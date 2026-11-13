# SPDX-License-Identifier: GPL-3.0-or-later
"""Read Blender reference systems and manage scene-owned native orientations.

Native orientations have no public collection API. Access a named orientation
through a slot, always restoring that slot, and seed new entries with the native
operator in a real View3D context. No helper objects or target transforms.
"""
from contextlib import contextmanager
import math
import uuid
import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix, Vector, Euler, Quaternion
from .math_core import BetterItemError

BUILTINS=('GLOBAL','LOCAL','NORMAL','GIMBAL','VIEW','CURSOR','PARENT')
PIVOTS=[('BOUNDING_BOX_CENTER','Bounding Box Center','Center of selected bounds'),
    ('CURSOR','3D Cursor','3D Cursor location'),
    ('INDIVIDUAL_ORIGINS','Individual Origins','Active object origin for a single frame'),
    ('MEDIAN_POINT','Median Point','Median pivot of the current selection'),
    ('ACTIVE_ELEMENT','Active Element','Active element of the current selection')]
_syncing=False
_custom_cache={}
_normal_cache={}
_needs_migration=True
_normal_signatures={}
_normal_revisions={}


def clear_cache():
    global _needs_migration
    _needs_migration=True
    _custom_cache.clear()
    _normal_cache.clear()
    _normal_signatures.clear()
    _normal_revisions.clear()


@persistent
def invalidate_normal(scene,depsgraph):
    if any(update.is_updated_geometry for update in depsgraph.updates):
        key=scene.as_pointer()
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
    if not all(math.isfinite(v) for row in matrix for v in row) or abs(matrix.determinant())<1e-6:
        raise BetterItemError('[BI-F005] Reference axes are singular (for example, Gimbal lock). Change the source rotation.')
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
    for frame in context.scene.better_item.frames:
        if frame.native_enabled and frame.native_name==name:
            return frames.frame_axes(frame,context,stack)
    if name not in BUILTINS:
        slot=context.scene.transform_orientation_slots[0]
        matrix=slot.custom_orientation.matrix if slot.type==name and slot.custom_orientation else _custom_cache.get((context.scene.as_pointer(),name))
        if matrix is None:raise BetterItemError('[BI-F003] Native orientation "%s" is missing or awaiting refresh.'%name)
        return checked(matrix)
    if name=='GLOBAL':return Matrix.Identity(3)
    if name=='CURSOR':return checked(context.scene.cursor.matrix.to_3x3())
    if name=='VIEW':
        with view_context(context) as ctx:return ctx.space_data.region_3d.view_rotation.to_matrix()
    obj=obj or context.active_object
    if obj is None:raise BetterItemError('[BI-F002] %s orientation needs an active object.'%name.title())
    if name=='PARENT':return checked(obj.parent.matrix_world.to_3x3().normalized()) if obj.parent else Matrix.Identity(3)
    if name=='GIMBAL':return _gimbal(obj)
    if name=='NORMAL' and context.mode!='OBJECT':
        matrix=_normal_cache.get(context.scene.as_pointer())
        if matrix is None:raise BetterItemError('[BI-F002] Select elements for Normal orientation and wait for refresh.')
        return checked(matrix)
    return checked(obj.matrix_world.to_3x3().normalized())


def pivot(context,mode,obj=None):
    if mode=='CURSOR':return context.scene.cursor.location.copy()
    obj=obj or context.active_object
    if obj is None:raise BetterItemError('[BI-F002] This pivot needs an active object or selection.')
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
        if mode=='MEDIAN_POINT':points=[item.matrix_world.translation.copy() for item in selected]
        else:
            graph=context.evaluated_depsgraph_get()
            for item in selected:
                evaluated=item.evaluated_get(graph)
                if all(tuple(c)==(-1,-1,-1) for c in evaluated.bound_box):points.append(evaluated.matrix_world.translation.copy())
                else:points.extend(evaluated.matrix_world@Vector(c) for c in evaluated.bound_box)
    if not points:raise BetterItemError('[BI-F002] Select elements to define this pivot.')
    if mode=='MEDIAN_POINT':return sum(points,Vector())/len(points)
    return Vector(tuple((min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)))


def remove_native(context,frame):
    if not frame.native_name:return
    _custom_cache.pop((context.scene.as_pointer(),frame.native_name),None)
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


def _source_names(scene):
    names={frame.native_source for frame in scene.better_item.frames if frame.rotation_mode=='NATIVE'}
    settings=[(scene.better_item,'arrange_orientation')]
    settings.extend((obj.better_item,'orientation') for obj in scene.objects)
    for owner,field in settings:
        mode=getattr(owner,field)
        if mode=='NATIVE':names.add(owner.reference_native)
        elif mode in BUILTINS:names.add(mode)
        elif mode=='VIEWPORT':names.add(scene.transform_orientation_slots[0].type)
    return names


def _normal_signature(context):
    selected=[]
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
        selected.append((obj.as_pointer(),tuple(v for row in obj.matrix_world for v in row),state))
    return (context.mode,context.active_object.as_pointer() if context.active_object else 0,
        tuple(sorted(selected)),_normal_revisions.get(context.scene.as_pointer(),0),tuple(context.tool_settings.mesh_select_mode))


def _refresh_normal(context):
    key=context.scene.as_pointer()
    signature=_normal_signature(context)
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


def sync():
    global _syncing,_needs_migration
    if _syncing or not hasattr(bpy.types.Scene,'better_item'):return .2
    _syncing=True
    try:
        context=bpy.context
        from . import frames
        if _needs_migration:
            frames.migrate()
            _needs_migration=False
        live_scenes={scene.as_pointer() for scene in bpy.data.scenes}
        live_names={(scene.as_pointer(),name) for scene in bpy.data.scenes for name in _source_names(scene)}
        for key in list(_custom_cache):
            if key not in live_names:del _custom_cache[key]
        for cache in (_normal_cache,_normal_signatures,_normal_revisions):
            for key in list(cache):
                if key not in live_scenes:del cache[key]
        windows=list(context.window_manager.windows)
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
            with context.temp_override(window=window,screen=window.screen,area=area,region=region):
                ctx=bpy.context
                # Absence while valid is an external deletion, not a request
                # to recreate. Suspended entries were removed by us instead.
                for frame in scene.better_item.frames:
                    if frame.native_enabled and not frame.native_suspended and frame.native_name and named(scene,frame.native_name) is None:
                        _custom_cache.pop((scene.as_pointer(),frame.native_name),None)
                        frame.native_enabled=False
                        frame.native_name=''
                names=_source_names(scene)
                for name in names:
                    if name not in BUILTINS:
                        custom=named(scene,name)
                        key=(scene.as_pointer(),name)
                        if custom is not None:_custom_cache[key]=custom.matrix.copy()
                        else:_custom_cache.pop(key,None)
                if 'NORMAL' in names and ctx.mode!='OBJECT':_refresh_normal(ctx)
                for frame in scene.better_item.frames:
                    if not frame.native_enabled:continue
                    try:publish(ctx,frame)
                    except (BetterItemError,RuntimeError,TypeError):
                        try:remove_native(ctx,frame)
                        except (BetterItemError,RuntimeError):pass
                        if not frame.native_suspended:frame.native_suspended=True
    finally:_syncing=False
    return .2


class BETTERITEM_OT_native_frame(bpy.types.Operator):
    bl_idname='better_item.native_frame'
    bl_label='Frame Orientation'
    bl_options={'REGISTER','UNDO'}
    action:bpy.props.EnumProperty(items=[('PUBLISH','Use in Viewport','Create or update a native orientation'),
        ('SOURCE','Use Viewport Choice','Link to the currently selected native orientation'),
        ('REMOVE','Remove Native Orientation','Stop synchronizing this native orientation')])
    def execute(self,context):
        settings=context.scene.better_item
        try:
            if not 0<=settings.active_frame<len(settings.frames):raise BetterItemError('Choose a frame.')
            frame=settings.frames[settings.active_frame]
            if self.action=='SOURCE':
                previous=frame.native_source
                frame.native_source=context.scene.transform_orientation_slots[0].type
                custom=context.scene.transform_orientation_slots[0].custom_orientation
                if custom:_custom_cache[(context.scene.as_pointer(),custom.name)]=custom.matrix.copy()
                try:
                    from . import frames
                    frames.frame_axes(frame,context)
                except BetterItemError:
                    frame.native_source=previous
                    raise
            elif self.action=='REMOVE':
                remove_native(context,frame)
                frame.native_enabled=False
                frame.native_name=''
            else:publish(context,frame,select=True)
        except (BetterItemError,RuntimeError) as exc:
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}
