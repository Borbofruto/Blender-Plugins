# SPDX-License-Identifier: GPL-3.0-or-later
"""Read Blender reference systems and manage scene-owned native orientations.

Native orientations have no public collection API. Access a named orientation
through a slot, always restoring that slot, and seed new entries with the native
operator in a real View3D context. No helper objects or target transforms.
"""
from contextlib import contextmanager
import math
import bpy
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


def clear_cache():
    _custom_cache.clear()
    _normal_cache.clear()


@contextmanager
def view_context(context):
    if context.area and context.area.type=='VIEW_3D':
        yield context
        return
    for window in context.window_manager.windows:
        if window.scene!=context.scene:continue
        for area in window.screen.areas:
            if area.type=='VIEW_3D':
                region=next(r for r in area.regions if r.type=='WINDOW')
                with context.temp_override(window=window,area=area,region=region):yield bpy.context
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


def sync():
    global _syncing
    if _syncing or not hasattr(bpy.types.Scene,'better_item'):return .2
    _syncing=True
    try:
        context=bpy.context
        from . import frames
        frames.migrate()
        live_scenes={scene.as_pointer() for scene in bpy.data.scenes}
        for key in list(_custom_cache):
            if key[0] not in live_scenes:del _custom_cache[key]
        live_names={(scene.as_pointer(),frame.native_source) for scene in bpy.data.scenes
            for frame in scene.better_item.frames if frame.rotation_mode=='NATIVE'}
        for key in list(_custom_cache):
            if key not in live_names:del _custom_cache[key]
        for key in list(_normal_cache):
            if key not in live_scenes:del _normal_cache[key]
        for window in context.window_manager.windows:
            with context.temp_override(window=window):
                scene=window.scene
                for frame in scene.better_item.frames:
                    if frame.rotation_mode!='NATIVE':continue
                    name=frame.native_source
                    if name not in BUILTINS:
                        custom=named(scene,name)
                        key=(scene.as_pointer(),name)
                        if custom is not None:_custom_cache[key]=custom.matrix.copy()
                        else:_custom_cache.pop(key,None)
                    elif name=='NORMAL' and context.mode!='OBJECT':
                        _normal_cache.pop(scene.as_pointer(),None)
                        try:
                            with view_context(context):
                                slot=scene.transform_orientation_slots[0]
                                previous=slot.type
                                try:
                                    result=bpy.ops.transform.create_orientation(name='Better Item Normal Probe',use=True)
                                    if 'FINISHED' in result and slot.custom_orientation:
                                        _normal_cache[scene.as_pointer()]=slot.custom_orientation.matrix.copy()
                                        bpy.ops.transform.delete_orientation()
                                finally:
                                    try:slot.type=previous
                                    except TypeError:slot.type='GLOBAL'
                        except (BetterItemError,RuntimeError):pass
                for frame in window.scene.better_item.frames:
                    if not frame.native_enabled:continue
                    try:publish(context,frame)
                    except (BetterItemError,RuntimeError,TypeError):
                        try:remove_native(context,frame)
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
