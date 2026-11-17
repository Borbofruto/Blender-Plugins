# SPDX-License-Identifier: GPL-3.0-or-later
"""Read Blender reference systems and manage scene-owned native orientations.

Native orientations have no public collection API. Access a named orientation
through a slot, always restoring that slot, and seed new entries with the native
operator in a real View3D context. No helper objects or target transforms.
"""
from contextlib import contextmanager
import math
import time
import uuid
import bpy
import numpy as np
from bpy.app.handlers import persistent
from mathutils import Matrix, Vector, Quaternion
from .math_core import BetterItemError,ReferencePending

BUILTINS=('GLOBAL','LOCAL','NORMAL','GIMBAL','VIEW','CURSOR','PARENT')
PIVOTS=[('BOUNDING_BOX_CENTER','Bounding Box Center','Center of selected bounds'),
    ('CURSOR','3D Cursor','3D Cursor location'),
    ('INDIVIDUAL_ORIGINS','Individual Origins','Active object origin for a single frame'),
    ('MEDIAN_POINT','Median Point','Median pivot of the current selection'),
    ('ACTIVE_ELEMENT','Active Element','Active element of the current selection')]
_syncing=False
_normal_cache={}
_needs_migration=True
_normal_signatures={}
_normal_revisions={}
_sync_errors={}
_RETRY_MIN=1.0
_RETRY_MAX=8.0
_normal_elements={}
_normal_dirty=set()
# Safety net if a script edits a selection without any depsgraph event.
_NORMAL_RECHECK_SECONDS=2.


def clear_cache():
    global _needs_migration
    _needs_migration=True
    _normal_cache.clear()
    _normal_signatures.clear()
    _normal_revisions.clear()
    _sync_errors.clear()
    _normal_elements.clear()
    _normal_dirty.clear()


@persistent
def invalidate_normal(scene,depsgraph):
    if not len(depsgraph.updates):return
    key=scene.as_pointer()
    # Element selection changes arrive as updates without a geometry flag.
    _normal_dirty.add(key)
    if any(update.is_updated_geometry for update in depsgraph.updates):
        _normal_revisions[key]=_normal_revisions.get(key,0)+1


@contextmanager
def view_context(context):
    if context.area and context.area.type=='VIEW_3D' and context.window and context.area in context.window.screen.areas[:]:
        yield context
        return
    for window in context.window_manager.windows:
        if window.scene!=context.scene:continue
        for area in window.screen.areas:
            if area.type=='VIEW_3D':
                region=next(r for r in area.regions if r.type=='WINDOW')
                with context.temp_override(window=window,screen=window.screen,area=area,region=region):yield bpy.context
                return
    raise BetterItemError('[BI-F004] Open a 3D Viewport for this reference operation.')


def named(scene,name):
    slot=scene.transform_orientation_slots[0]
    previous=slot.type
    try:
        try:
            if previous!=name:slot.type=name
        except TypeError:return None
        # These RNA values are freed without invalidating Python wrappers when
        # a native orientation is deleted. Never retain wrappers across calls.
        return slot.custom_orientation
    finally:
        try:
            if slot.type!=previous:slot.type=previous
        except TypeError:slot.type='GLOBAL'


def checked(matrix):
    # Singular values are invariant to uniform unit rescaling, unlike det(B).
    array=np.asarray(matrix,dtype=np.float64)
    singular=np.linalg.svd(array,compute_uv=False) if np.isfinite(array).all() else (0.,0.,0.)
    if singular[0]==0 or singular[-1]<=8*np.finfo(np.float32).eps*singular[0]:
        raise BetterItemError('[BI-F005] Reference axes are singular or too ill-conditioned for float32 source data (for example, Gimbal lock). Apply a stable reference or change the source rotation.')
    return matrix.copy()


def rotation_basis(matrix):
    """Euler pose uses the rotational component; directions retain all axes."""
    return matrix.to_quaternion().normalized().to_matrix()


def _gimbal(obj):
    if obj.rotation_mode in {'QUATERNION','AXIS_ANGLE'}:
        # Blender has no quaternion Euler gimbals: it uses the parent basis.
        if obj.rotation_mode=='QUATERNION':return checked(obj.parent.matrix_world.to_3x3().normalized()) if obj.parent else Matrix.Identity(3)
        angle,*axis=obj.rotation_axis_angle
        z=Vector(axis).normalized()
        seed=Vector((z.y,z.z,z.x))
        x=seed.cross(z)
        if x.length<1e-8:x=z.orthogonal()
        x=Quaternion(z,angle)@x.normalized()
        y=Quaternion(z,math.pi/2)@x
        basis=Matrix((x,y,z)).transposed()
    else:
        angles=obj.rotation_euler.copy()
        first,second,last=('XYZ'.index(c) for c in obj.rotation_mode)
        basis=Matrix.Identity(3)
        basis.col[first]=angles.to_matrix().col[first]
        angles[first]=0
        basis.col[second]=angles.to_matrix().col[second]
    if obj.parent:basis=obj.parent.matrix_world.to_3x3().normalized()@basis
    return checked(basis)


def orientation(context,name,obj=None,stack=()):
    from . import frames
    if name not in BUILTINS:
        raise ReferencePending('[BI-F003] Custom Orientation references were removed. Choose Object or Frame for Orientation; your object was not changed.')
    if name=='GLOBAL':return Matrix.Identity(3)
    if name=='CURSOR':return checked(context.scene.cursor.matrix.to_3x3())
    if name=='VIEW':
        with view_context(context) as ctx:return ctx.space_data.region_3d.view_rotation.to_matrix()
    obj=obj or context.active_object
    if obj is None:raise ReferencePending('[BI-F002] Select an active object for %s orientation.'%name.title())
    if name=='PARENT':return checked(obj.parent.matrix_world.to_3x3().normalized()) if obj.parent else Matrix.Identity(3)
    if name=='GIMBAL':return _gimbal(obj)
    if name=='NORMAL' and context.mode!='OBJECT':
        matrix=_normal_cache.get(context.scene.as_pointer())
        if matrix is None:raise ReferencePending('[BI-F002] Select mesh elements for Normal orientation and wait for refresh.')
        return checked(matrix)
    return checked(obj.matrix_world.to_3x3().normalized())


def pivot(context,mode,obj=None):
    if mode=='CURSOR':return context.scene.cursor.location.copy()
    obj=obj or context.active_object
    if obj is None:raise ReferencePending('[BI-F002] Select an active object or mesh elements for this Location reference.')
    if mode=='INDIVIDUAL_ORIGINS':return obj.matrix_world.translation.copy()
    points=[]
    if context.mode=='EDIT_MESH':
        import bmesh
        for item in context.objects_in_mode_unique_data:
            mesh=bmesh.from_edit_mesh(item.data)
            if mode=='ACTIVE_ELEMENT' and item==obj:
                active=mesh.select_history.active
                if active:
                    local=active.co if isinstance(active,bmesh.types.BMVert) else (active.calc_center_median() if isinstance(active,bmesh.types.BMFace) else (active.verts[0].co+active.verts[1].co)/2)
                    return item.matrix_world@local
            points.extend(item.matrix_world@v.co for v in mesh.verts if v.select)
    else:
        if mode=='ACTIVE_ELEMENT':return obj.matrix_world.translation.copy()
        selected=list(context.selected_objects) or [obj]
        # Native Object Mode pivots use selected origins, not mesh bounds.
        points=[item.matrix_world.translation.copy() for item in selected]
    if not points:raise ReferencePending('[BI-F002] Select mesh elements to define this Location reference.')
    if mode=='MEDIAN_POINT':return sum(points,Vector())/len(points)
    return Vector(tuple((min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)))


def remove_native(context,frame):
    if not frame.native_name:return
    custom=named(context.scene,frame.native_name)
    if custom is None:return
    with view_context(context):
        slot=context.scene.transform_orientation_slots[0]
        previous=slot.type
        slot.type=frame.native_name
        bpy.ops.transform.delete_orientation()
        try:slot.type=previous
        except TypeError:slot.type='GLOBAL'


def publish(context,frame,select=False):
    from . import frames
    matrix=frames.frame_axes(frame,context)
    with view_context(context):
        slot=context.scene.transform_orientation_slots[0]
        previous=slot.type
        custom=named(context.scene,frame.native_name) if frame.native_name else None
        if custom is None:
            result=bpy.ops.transform.create_orientation(name='BI: '+frame.name,use_view=True,use=True)
            if 'FINISHED' not in result:raise BetterItemError('[BI-F004] Cannot create a native orientation in this context.')
            custom=slot.custom_orientation
            frame.native_name=custom.name
        if custom.name!='BI: '+frame.name:
            old=custom.name
            custom.name='BI: '+frame.name
            frame.native_name=custom.name
            for other in context.scene.better_item.frames:
                if other.native_source==old:other.native_source=custom.name
            if previous==old:previous=custom.name
        if max(abs(custom.matrix[i][j]-matrix[i][j]) for i in range(3) for j in range(3))>1e-7:custom.matrix=matrix
        if not frame.native_enabled:frame.native_enabled=True
        if frame.native_suspended:frame.native_suspended=False
        desired=custom.name if select else previous
        if slot.type!=desired:slot.type=desired
        _sync_errors.pop((context.scene.as_pointer(),frame.uid),None)


def _source_names(scene):
    names={frame.native_source for frame in scene.better_item.frames if frame.rotation_mode=='NATIVE' and frame.native_source}
    settings=[(scene.better_item,'arrange_orientation')]
    settings.extend((obj.better_item,'orientation') for obj in scene.objects)
    for owner,field in settings:
        mode=getattr(owner,field)
        if mode=='NATIVE' and owner.reference_native:names.add(owner.reference_native)
        elif mode in BUILTINS:names.add(mode)
        elif mode=='VIEWPORT':names.add(scene.transform_orientation_slots[0].type)
    return names


def _selection_states(context):
    """Per-element selection of every object in the current edit session."""
    states=[]
    for obj in context.objects_in_mode_unique_data:
        state=()
        if obj.type=='MESH':
            import bmesh
            mesh=bmesh.from_edit_mesh(obj.data)
            for elements in (mesh.verts,mesh.edges,mesh.faces):elements.index_update()
            state=tuple(tuple(item.index for item in elements if item.select) for elements in (mesh.verts,mesh.edges,mesh.faces))
            state+=(tuple((type(item).__name__,item.index) for item in mesh.select_history),
                mesh.faces.active.index if mesh.faces.active else -1)
        elif obj.type in {'CURVE','SURFACE'}:
            state=tuple(tuple((p.select_control_point,p.select_left_handle,p.select_right_handle) for p in spline.bezier_points)
                +tuple(p.select for p in spline.points) for spline in obj.data.splines)
        states.append((obj.as_pointer(),state))
    return tuple(sorted(states))


def _normal_signature(context,fresh=True):
    """Selection fingerprint. Walking every element is O(vertices) in Python, so
    an unchanged fingerprint is reused until a depsgraph event arrives (or a
    short safety interval passes) unless `fresh` forces an exact walk."""
    key=context.scene.as_pointer()
    pointers=tuple(sorted(obj.as_pointer() for obj in context.objects_in_mode_unique_data))
    cached=_normal_elements.get(key)
    if (fresh or cached is None or key in _normal_dirty or cached[0]!=pointers
            or time.monotonic()-cached[2]>_NORMAL_RECHECK_SECONDS):
        elements=_selection_states(context)
        _normal_elements[key]=(pointers,elements,time.monotonic())
        _normal_dirty.discard(key)
    else:elements=cached[1]
    matrices=tuple(sorted((obj.as_pointer(),tuple(v for row in obj.matrix_world for v in row)) for obj in context.objects_in_mode_unique_data))
    return (context.mode,context.active_object.as_pointer() if context.active_object else 0,
        matrices,elements,_normal_revisions.get(key,0),tuple(context.tool_settings.mesh_select_mode))


def _refresh_normal(context):
    key=context.scene.as_pointer()
    signature=_normal_signature(context,fresh=False)
    if _normal_signatures.get(key)==signature:return
    _normal_signatures[key]=signature
    _normal_cache.pop(key,None)
    slot=context.scene.transform_orientation_slots[0]
    previous=slot.type
    try:
        # One exact native sample per changed selection, never per frame/tick.
        result=bpy.ops.transform.create_orientation(name='BI Normal '+uuid.uuid4().hex,use=True)
        if 'FINISHED' in result and slot.custom_orientation:
            _normal_cache[key]=slot.custom_orientation.matrix.copy()
            bpy.ops.transform.delete_orientation()
    except RuntimeError:pass
    finally:
        try:slot.type=previous
        except TypeError:slot.type='GLOBAL'
        _normal_signatures[key]=_normal_signature(context)


def _redraw_scene(scene,windows):
    for window in windows:
        try:
            screen=window.screen
            if window.scene==scene and screen:
                for area in screen.areas:
                    if area.type=='VIEW_3D':area.tag_redraw()
        except (ReferenceError,RuntimeError):
            # A closed window must not make error reporting fail as well.
            continue


def _redraw_all(windows):
    """Redraw each window's scene. An invalid window must not stop recovery reporting."""
    for window in windows:
        try:scene=window.scene
        except (ReferenceError,RuntimeError):continue
        if scene is not None:_redraw_scene(scene,windows)


def sync_error(scene,frame=None):
    """Transient health, separate from export intent and source suspension."""
    pointer=scene.as_pointer()
    keys=[(pointer,frame.uid)] if frame is not None else []
    keys.extend(((pointer,''),(0,'')))
    issue=next((_sync_errors[key] for key in keys if key in _sync_errors),None)
    if issue is None:return None
    error=BetterItemError('[BI-F006] '+issue['message'])
    if frame is not None:error.subject=frame.name
    return error


def _retry_ready(key):
    issue=_sync_errors.get(key)
    return issue is None or time.monotonic()>=issue['retry_at']


def _sync_failed(key,error):
    # Keep copies of text/numbers only: no exception, Object or orientation RNA
    # wrappers may survive Undo, reload or deletion through this health record.
    message='%s: %s'%(type(error).__name__,error)
    previous=_sync_errors.get(key)
    attempts=previous['attempts']+1 if previous and previous['message']==message else 1
    delay=min(_RETRY_MAX,_RETRY_MIN*2**min(attempts-1,3))
    _sync_errors[key]={'message':message,'attempts':attempts,'retry_at':time.monotonic()+delay}
    if previous is None or previous['message']!=message:
        print('Better Item native sync paused [%s]: %s; automatic retry pending.'%(key,message))
        return True
    return False


def _sync_frame(context,frame):
    scene=context.scene
    # An unknown read failure must not be mistaken for native deletion. Let
    # the caller pause/retry this Frame without changing its export intent.
    if not frame.native_suspended and frame.native_name and named(scene,frame.native_name) is None:
        frame.native_enabled=False
        frame.native_name=''
        return
    try:publish(context,frame)
    except BetterItemError:
        # Preserve the existing policy for an invalid source: remove our
        # export, then recreate it only when the source becomes valid again.
        remove_native(context,frame)
        if not frame.native_suspended:frame.native_suspended=True


def _sync_scene(context,scene,windows):
    pointer=scene.as_pointer()
    before=tuple((f.uid,f.native_enabled,f.native_suspended,f.native_name) for f in scene.better_item.frames)
    valid={f.uid for f in scene.better_item.frames}
    for key in list(_sync_errors):
        if key[0]==pointer and key[1] and key[1] not in valid:del _sync_errors[key]
    # Object Mode never consumes a selection-normal sample.
    if context.mode!='OBJECT' and 'NORMAL' in _source_names(scene):_refresh_normal(context)
    health_changed=False
    for frame in scene.better_item.frames:
        key=(pointer,frame.uid)
        if not frame.native_enabled:
            health_changed=bool(_sync_errors.pop(key,None)) or health_changed
            continue
        if not _retry_ready(key):continue
        had_error=key in _sync_errors
        try:
            _sync_frame(context,frame)
            _sync_errors.pop(key,None)
            health_changed=had_error or health_changed
        except Exception as exc:
            # An unexpected failure of one Frame must not stop the other
            # exports or unregister the Blender timer.
            health_changed=_sync_failed(key,exc) or health_changed
    after=tuple((f.uid,f.native_enabled,f.native_suspended,f.native_name) for f in scene.better_item.frames)
    if before!=after or health_changed:_redraw_scene(scene,windows)


def sync():
    global _syncing,_needs_migration
    if _syncing or not hasattr(bpy.types.Scene,'better_item'):return .2
    if not _retry_ready((0,'')):return .2
    _syncing=True
    windows=[]
    try:
        context=bpy.context
        windows=list(context.window_manager.windows)
        from . import frames
        if _needs_migration:
            frames.migrate()
            from . import distribution
            distribution.migrate()
            _needs_migration=False
        live_scenes={scene.as_pointer() for scene in bpy.data.scenes}
        for cache in (_normal_cache,_normal_signatures,_normal_revisions,_normal_elements):
            for key in list(cache):
                if key not in live_scenes:del cache[key]
        for key in list(_sync_errors):
            if key[0] and key[0] not in live_scenes:del _sync_errors[key]
        _normal_dirty.intersection_update(live_scenes)
        if context.window in windows:windows.remove(context.window);windows.insert(0,context.window)
        visited=set()
        for window in windows:
            scene=window.scene
            if scene.as_pointer() in visited:continue
            area=next((a for a in window.screen.areas if a.type=='VIEW_3D'),None)
            if area is None:continue
            region=next((r for r in area.regions if r.type=='WINDOW'),None)
            if region is None:continue
            visited.add(scene.as_pointer())
            key=(scene.as_pointer(),'')
            if not _retry_ready(key):continue
            had_error=key in _sync_errors
            try:
                with context.temp_override(window=window,screen=window.screen,area=area,region=region):
                    _sync_scene(bpy.context,scene,windows)
                _sync_errors.pop(key,None)
                if had_error:_redraw_scene(scene,windows)
            except Exception as exc:
                if _sync_failed(key,exc):_redraw_scene(scene,windows)
        recovered=bool(_sync_errors.pop((0,''),None))
        if recovered:
            _redraw_all(windows)
    except Exception as exc:
        # Registration/migration/window enumeration can fail before a Frame is
        # available. Keep a visible observer-level diagnostic and bounded retry.
        if _sync_failed((0,''),exc):
            _redraw_all(windows)
    finally:_syncing=False
    return .2


class BETTERITEM_OT_native_frame(bpy.types.Operator):
    bl_idname='better_item.native_frame'
    bl_label='Frame Orientation'
    bl_options={'REGISTER','UNDO'}
    action:bpy.props.EnumProperty(items=[('PUBLISH','Use in Viewport','Create or update a native orientation'),
        ('REMOVE','Remove Native Orientation','Stop synchronizing this native orientation')])
    def execute(self,context):
        settings=context.scene.better_item
        try:
            if not 0<=settings.active_frame<len(settings.frames):raise BetterItemError('Choose a frame.')
            frame=settings.frames[settings.active_frame]
            if self.action=='REMOVE':
                remove_native(context,frame)
                frame.native_enabled=False
                frame.native_name=''
                _sync_errors.pop((context.scene.as_pointer(),frame.uid),None)
            else:publish(context,frame,select=True)
        except (BetterItemError,RuntimeError) as exc:
            from . import diagnostics
            diagnostics.report(self,exc)
            return {'CANCELLED'}
        return {'FINISHED'}
