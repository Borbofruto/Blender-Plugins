# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit relative-pose animation, native keying and portable pose baking.

Only opted-in objects are driven. Stored RNA vectors are animation channels;
the ordinary transform proxies deliberately remain non-animatable. Owned scene
frames isolate fallback from user frames shared by other consumers.
"""
import math
import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix,Vector,Euler
from . import frames,native_refs,orientation,engine,transform_view
from .math_core import BetterItemError,linked_values
import numpy as np
from collections import OrderedDict

_busy=False
_pose_signatures=OrderedDict()
_DEPENDENCY_PATH='better_item.animation.dependency_stamp'


def curves(action,slot):
    if action is None or slot is None:return
    for layer in action.layers:
        for strip in layer.strips:
            if strip.type=='KEYFRAME':
                bag=strip.channelbag(slot)
                if bag:
                    yield from bag.fcurves


def object_curves(obj):
    data=obj.animation_data
    if data:yield from curves(data.action,data.action_slot)


def _rotation_path(obj):return {'QUATERNION':'rotation_quaternion','AXIS_ANGLE':'rotation_axis_angle'}.get(obj.rotation_mode,'rotation_euler')


def guard(obj):
    engine.editable(obj)
    a=obj.better_item.animation
    if len(obj.users_scene)>1:raise BetterItemError('[BI-AN007] Relative Animation needs a scene-specific object. Make a separate object for each scene.')
    if _dependency_curve(obj) and not a.dependencies_owned:raise BetterItemError('[BI-AN001] The reserved animation dependency channel is already driven.')
    paths=set()
    if a.drive_location:paths.add('location')
    if a.drive_rotation:paths.update(('rotation_euler','rotation_quaternion','rotation_axis_angle'))
    engine._driver_guard(obj,paths|{'better_item.animation.location','better_item.animation.rotation'})
    if any(not c.mute and c.influence for c in obj.constraints):raise BetterItemError('[BI-AN001] Disable target constraints before Relative Animation.')
    if a.drive_location and any(obj.lock_location):raise BetterItemError('[BI-AN001] Unlock Location before Relative Animation owns it.')
    if a.drive_rotation and (any(obj.lock_rotation) or obj.lock_rotation_w):raise BetterItemError('[BI-AN001] Unlock Rotation before Relative Animation owns it.')
    conflicts=sorted({c.data_path for c in object_curves(obj) if not c.mute and c.data_path in paths})
    if conflicts:raise BetterItemError('[BI-AN001] Native animation already controls %s. Remove those curves or use native keying.'%', '.join(conflicts))
    data=obj.animation_data
    if data and (data.use_tweak_mode or any(not t.mute and t.strips for t in data.nla_tracks)):
        raise BetterItemError('[BI-AN001] Exit NLA tweak mode and mute target NLA tracks before Relative Animation.')
    if data and data.action and (data.action_blend_type!='REPLACE' or abs(data.action_influence-1)>1e-6):
        raise BetterItemError('[BI-AN001] Use a full-influence Replace action for Relative Animation.')


def _matrix(values):return Matrix(tuple(tuple(values[i*3+j] for j in range(3)) for i in range(3)))


def _assign(owner,name,value):
    old=getattr(owner,name)
    if isinstance(value,(tuple,list,Vector)):
        if tuple(old)==tuple(value):return
    elif old==value:return
    setattr(owner,name,value)


def _frame(scene,uid):
    return next((f for f in scene.better_item.frames if f.uid==uid),None)


def _missing(scene,frame,kind,seen=(),probe=False):
    if frame is None:return True
    if frame.uid in seen:return False  # Cycles are diagnosed, not frozen.
    mode=frame.position_mode if kind=='POSITION' else frame.rotation_mode
    source=frame.position_source if kind=='POSITION' else frame.rotation_source
    if mode in {'OBJECT','PARENT'}:return source is None
    if mode=='FRAME':return _missing(scene,_frame(scene,frame.position_frame if kind=='POSITION' else frame.rotation_frame),kind,(*seen,frame.uid),probe)
    if kind=='ROTATION' and mode=='NATIVE' and frame.native_source not in native_refs.BUILTINS:
        if probe and native_refs.named(scene,frame.native_source) is None:return True
        owner=next((f for f in scene.better_item.frames if f.native_enabled and f.native_name==frame.native_source),None)
        return _missing(scene,owner,kind,(*seen,frame.uid),probe) if owner else False
    return False


def _evaluated_component(context,frame,kind,graph,seen=(),probe=False):
    if frame.uid in seen:raise BetterItemError('[BI-AN003] Circular animation frame reference.')
    mode=frame.position_mode if kind=='POSITION' else frame.rotation_mode
    source=frame.position_source if kind=='POSITION' else frame.rotation_source
    if mode=='FRAME':
        child=_frame(frame.id_data,frame.position_frame if kind=='POSITION' else frame.rotation_frame)
        if child is None:raise BetterItemError('[BI-AN002] Animation frame source was removed.')
        return _evaluated_component(context,child,kind,graph,(*seen,frame.uid),probe)
    if mode in {'OBJECT','PARENT'}:
        if source is None:raise BetterItemError('[BI-AN002] Animation object source was removed.')
        if mode=='PARENT':source=source.parent
        if source is None:return Vector() if kind=='POSITION' else Matrix.Identity(3)
        source=source.evaluated_get(graph)
        return source.matrix_world.translation.copy() if kind=='POSITION' else orientation.rotation(source)
    # Blender's cursor is not an animatable RNA transform. Its original scene
    # value is authoritative for manual/pre-handler edits at the current frame.
    if kind=='POSITION' and mode=='PIVOT' and frame.position_pivot=='CURSOR':return context.scene.cursor.location.copy()
    if kind=='ROTATION' and mode=='NATIVE' and frame.native_source=='CURSOR':return context.scene.cursor.matrix.to_3x3()
    if kind=='ROTATION' and mode=='NATIVE' and frame.native_source not in native_refs.BUILTINS:
        owner=next((f for f in frame.id_data.better_item.frames if f.native_enabled and f.native_name==frame.native_source),None)
        if owner:return _evaluated_component(context,owner,kind,graph,(*seen,frame.uid),probe)
        if probe:
            native=native_refs.named(frame.id_data,frame.native_source)
            if native is None:raise BetterItemError('[BI-AN002] Native orientation source was removed.')
            matrix=native.matrix.copy();native_refs._custom_cache[(frame.id_data.as_pointer(),frame.native_source)]=matrix
            return matrix
    if not _stable(frame.id_data,frame,kind):raise BetterItemError('[BI-AN002] Viewport-dependent source changed. Pause and restart to capture its base.')
    return frames.frame_origin(frame,context) if kind=='POSITION' else frames.frame_axes(frame,context)


def basis(context,obj,depsgraph=None,*,update=False):
    a=obj.better_item.animation;scene=a.scene
    if scene is None:raise BetterItemError('[BI-AN002] Relative Animation has no source scene.')
    if context.scene!=scene:raise BetterItemError('[BI-AN007] Evaluate Relative Animation in its binding scene.')
    if depsgraph is None and hasattr(context,'evaluated_depsgraph_get'):depsgraph=context.evaluated_depsgraph_get()
    frame=_frame(scene,a.binding_uid)
    if frame is None:
        if not a.cache_valid:raise BetterItemError('[BI-AN002] Animation reference was removed before a valid basis was saved.')
        if update:_assign(a,'warning','Reference frame removed: using the saved manual base.')
        return Vector(a.cached_origin),_matrix(a.cached_axes)
    changed=False
    missing_position=_missing(scene,frame,'POSITION',probe=update) and a.drive_location
    missing_rotation=_missing(scene,frame,'ROTATION',probe=update)
    if missing_position:
        if not a.cache_valid:raise BetterItemError('[BI-AN002] Location reference is missing and no valid cache exists.')
        if update:
            frames.apply_reference(frame,'POSITION',fallback_origin=Vector(a.cached_origin),force_cached=True)
            changed=True
            _assign(a,'warning','Location source removed: last valid Location applied to the animation frame.')
    if missing_rotation:
        if not a.cache_valid:raise BetterItemError('[BI-AN002] Orientation reference is missing and no valid cache exists.')
        if update:
            frames.apply_reference(frame,'ROTATION',fallback_axes=_matrix(a.cached_axes),force_cached=True)
            changed=True
            _assign(a,'warning','Orientation source removed: last valid Orientation applied to the animation frame.')
    if depsgraph is not None:
        if changed:depsgraph.update()
        origin=_evaluated_component(context,frame,'POSITION',depsgraph,probe=update) if a.drive_location and not missing_position else Vector(a.cached_origin)
        axes=_evaluated_component(context,frame,'ROTATION',depsgraph,probe=update) if not missing_rotation else _matrix(a.cached_axes)
    else:
        origin=frames.frame_origin(frame,context) if a.drive_location and not missing_position else Vector(a.cached_origin)
        axes=frames.frame_axes(frame,context) if not missing_rotation else _matrix(a.cached_axes)
    if update:
        _assign(a,'cached_origin',tuple(origin));_assign(a,'cached_axes',tuple(v for row in axes for v in row))
        _assign(a,'cache_valid',True)
    return origin,axes


def _stable(scene,frame,kind,seen=()):
    if frame is None:raise BetterItemError('[BI-AN002] Choose a valid frame before starting animation.')
    if frame.uid in seen:raise BetterItemError('[BI-AN003] Circular frame reference.')
    mode=frame.position_mode if kind=='POSITION' else frame.rotation_mode
    if mode=='FRAME':return _stable(scene,_frame(scene,frame.position_frame if kind=='POSITION' else frame.rotation_frame),kind,(*seen,frame.uid))
    if mode in {'MANUAL','GLOBAL','OBJECT','PARENT'}:return True
    if mode=='PIVOT':return frame.position_pivot=='CURSOR'
    if mode=='NATIVE':
        if frame.native_source in {'GLOBAL','CURSOR'}:return True
        if frame.native_source not in native_refs.BUILTINS:
            owner=next((f for f in scene.better_item.frames if f.native_enabled and f.native_name==frame.native_source),None)
            return _stable(scene,owner,'ROTATION',(*seen,frame.uid)) if owner else True
        return False
    return False


def _binding(context,obj):
    s=obj.better_item;scene=context.scene
    origin=frames.object_origin(context,obj) if s.animation.drive_location else obj.matrix_world.translation.copy()
    axes=frames.object_axes(context,obj)
    f=frames.create(context,'Animation Reference - '+obj.name,origin,axes);uid=f.uid;f.visible=False
    if s.reference_mode=='FRAME':
        source=_frame(scene,s.reference_frame)
        if s.animation.drive_location and _stable(scene,source,'POSITION'):f.position_mode='FRAME';f.position_frame=source.uid
        if _stable(scene,source,'ROTATION'):f.rotation_mode='FRAME';f.rotation_frame=source.uid
    else:
        mode=s.pivot_mode
        if mode=='OBJECT':f.position_mode='OBJECT';f.position_source=s.origin_object
        elif mode=='PARENT':
            f.position_mode='OBJECT' if obj.parent else 'GLOBAL';f.position_source=obj.parent
        elif mode=='FRAME':
            source=_frame(scene,s.pivot_frame)
            if _stable(scene,source,'POSITION'):f.position_mode='FRAME';f.position_frame=source.uid
        elif mode=='CURSOR' or mode=='PIVOT' and s.reference_pivot=='CURSOR':f.position_mode='PIVOT';f.position_pivot='CURSOR'
        elif mode=='GLOBAL':f.position_mode='GLOBAL'
        mode=s.orientation
        if mode=='REFERENCE':f.rotation_mode='OBJECT';f.rotation_source=s.orientation_object
        elif mode=='PARENT' and obj.parent:f.rotation_mode='OBJECT';f.rotation_source=obj.parent
        elif mode=='SAVED':
            source=_frame(scene,s.orientation_frame)
            if _stable(scene,source,'ROTATION'):f.rotation_mode='FRAME';f.rotation_frame=source.uid
        elif mode=='CURSOR':f.rotation_mode='NATIVE';f.native_source='CURSOR'
        elif mode=='NATIVE':
            f.rotation_mode='NATIVE';f.native_source=s.reference_native
            if not _stable(scene,f,'ROTATION'):f.rotation_mode='MANUAL'
    if not s.animation.drive_location:f.position_mode='MANUAL'
    return uid,origin,axes


def _native_dependencies(obj):
    result=set()
    if obj.parent:result.add(obj.parent)
    for c in obj.constraints:
        if not c.mute and getattr(c,'target',None):result.add(c.target)
    data=obj.animation_data
    if data:
        for driver in data.drivers:
            if driver.mute:continue
            if driver.data_path==_DEPENDENCY_PATH and obj.better_item.animation.dependencies_owned:continue
            for variable in driver.driver.variables:
                for target in variable.targets:
                    if isinstance(target.id,bpy.types.Object):result.add(target.id)
    return result


def _sources(scene,frame,seen=(),component=None):
    if frame is None or frame.uid in seen:return set()
    result=set();seen=(*seen,frame.uid)
    for kind in ((component,) if component else ('position','rotation')):
        mode=getattr(frame,kind+'_mode');source=getattr(frame,kind+'_source')
        if mode=='OBJECT' and source:result.add(source)
        elif mode=='PARENT' and source and source.parent:result.add(source.parent)
        elif mode=='FRAME':result|=_sources(scene,_frame(scene,getattr(frame,kind+'_frame')),seen,kind)
        elif kind=='rotation' and mode=='NATIVE' and frame.native_source not in native_refs.BUILTINS:
            owner=next((f for f in scene.better_item.frames if f.native_enabled and f.native_name==frame.native_source),None)
            result|=_sources(scene,owner,seen,'rotation')
        elif mode=='PIVOT' and frame.position_pivot=='CURSOR' or mode=='NATIVE' and frame.native_source=='CURSOR':
            if scene.animation_data:
                for curve in scene.animation_data.drivers:
                    if curve.mute or not curve.data_path.startswith('cursor.'):continue
                    for variable in curve.driver.variables:
                        for target in variable.targets:
                            if isinstance(target.id,bpy.types.Object):result.add(target.id)
    return result


def _uses_cursor(scene,frame,seen=(),component=None):
    if frame is None or frame.uid in seen:return False
    for kind in ((component,) if component else ('position','rotation')):
        mode=getattr(frame,kind+'_mode')
        if kind=='position' and mode=='PIVOT' and frame.position_pivot=='CURSOR' or kind=='rotation' and mode=='NATIVE' and frame.native_source=='CURSOR':return True
        if mode=='FRAME' and _uses_cursor(scene,_frame(scene,getattr(frame,kind+'_frame')),(*seen,frame.uid),kind):return True
        if kind=='rotation' and mode=='NATIVE' and frame.native_source not in native_refs.BUILTINS:
            owner=next((f for f in scene.better_item.frames if f.native_enabled and f.native_name==frame.native_source),None)
            if _uses_cursor(scene,owner,(*seen,frame.uid),'rotation'):return True
    return False


def _dependency_curve(obj):
    return next((c for c in obj.animation_data.drivers if c.data_path==_DEPENDENCY_PATH),None) if obj.animation_data else None


def _ensure_dependencies(scene):
    try:actors=ordered(scene)
    except BetterItemError:
        # A newly introduced logical cycle must not leave our bookkeeping
        # drivers creating a native dependency-graph cycle as well.
        for obj in scene.objects:
            a=obj.better_item.animation
            if a.dependencies_owned and obj.is_editable and a.scene==scene:
                obj.driver_remove(_DEPENDENCY_PATH);a.dependencies_owned=False
        return
    for obj in actors:
        a=obj.better_item.animation;frame=_frame(scene,a.binding_uid)
        sources=sorted(_sources(scene,frame),key=lambda source:source.name)
        specs=[('TRANSFORMS',source,'LOC_X') for source in sources]
        if _uses_cursor(scene,frame):specs.extend(('SINGLE_PROP',scene,path) for path in ('cursor.location[0]','cursor.rotation_euler[0]'))
        curve=_dependency_curve(obj)
        if curve and not a.dependencies_owned:
            raise BetterItemError('[BI-AN001] The reserved animation dependency channel is already driven.')
        if not specs:
            if curve:obj.driver_remove(_DEPENDENCY_PATH)
            a.dependencies_owned=False
            continue
        current=[]
        if curve:
            for variable in curve.driver.variables:
                target=variable.targets[0]
                current.append((variable.type,target.id,target.transform_type if variable.type=='TRANSFORMS' else target.data_path))
        expression='+'.join('0*ref%d'%i for i in range(len(specs)))
        if curve and curve.mute:curve.mute=False
        if current==specs and [v.name for v in curve.driver.variables]==['ref%d'%i for i in range(len(specs))] and curve.driver.type=='SCRIPTED' and curve.driver.expression==expression:continue
        if curve is None:curve=obj.driver_add(_DEPENDENCY_PATH)
        driver=curve.driver
        while driver.variables:driver.variables.remove(driver.variables[0])
        for i,(kind,source,path) in enumerate(specs):
            variable=driver.variables.new();variable.name='ref%d'%i;variable.type=kind
            target=variable.targets[0]
            if kind=='SINGLE_PROP':target.id_type='SCENE';target.id=source;target.data_path=path
            else:target.id=source;target.transform_type=path;target.transform_space='WORLD_SPACE'
        driver.type='SCRIPTED';driver.expression=expression
        a.dependencies_owned=True


@persistent
def frame_prepare(scene):
    # Relations must exist before evaluation, including for hidden controllers
    # that the render dependency graph would otherwise omit.
    _ensure_dependencies(scene)


def ordered(scene):
    actors={o for o in scene.objects if o.better_item.animation.enabled and o.better_item.animation.scene==scene}
    output=[];visiting=set();visited=set()
    def visit(obj):
        if obj in visiting:raise BetterItemError('[BI-AN003] Cyclic animation/reference dependency involving "%s".'%obj.name)
        if obj in visited:return
        if obj.better_item.animation.enabled and obj.better_item.animation.scene!=scene:
            raise BetterItemError('[BI-AN007] A reference actor belongs to another animation scene.')
        visiting.add(obj)
        dependencies=_native_dependencies(obj)
        if obj in actors:
            sources=_sources(scene,_frame(scene,obj.better_item.animation.binding_uid))
            if any(source.name not in scene.objects for source in sources):raise BetterItemError('[BI-AN002] Link animation reference objects into the binding scene.')
            dependencies|=sources
        for source in sorted(dependencies,key=lambda o:o.name):visit(source)
        visiting.remove(obj);visited.add(obj)
        if obj in actors:output.append(obj)
    for obj in sorted(actors,key=lambda o:o.name):visit(obj)
    return output


def apply_object(context,obj,depsgraph=None):
    a=obj.better_item.animation
    guard(obj)
    if obj.better_item.view_rotation_order!=a.order:raise BetterItemError('[BI-AN001] Restore the recorded Rotation Mode (%s), or bake before changing it.'%a.order)
    graph=depsgraph or context.evaluated_depsgraph_get()
    origin,axes=basis(context,obj,graph,update=True)
    evaluated=obj.evaluated_get(graph)
    inputs=evaluated.better_item.animation
    location=tuple(inputs.location);rotation=tuple(inputs.rotation)
    parent=engine._parent_matrix(evaluated)
    signature=(tuple(origin),tuple(v for row in axes for v in row),location,rotation,
        tuple(v for row in parent for v in row),tuple(evaluated.scale),tuple(evaluated.delta_scale),
        tuple(evaluated.delta_location),tuple(evaluated.delta_rotation_euler),tuple(evaluated.delta_rotation_quaternion),
        obj.rotation_mode,a.order,a.drive_location,a.drive_rotation)
    cache_key=(context.scene.as_pointer(),obj.as_pointer(),graph.as_pointer())
    native_before=(tuple(obj.location),tuple(getattr(obj,_rotation_path(obj))))
    if _pose_signatures.get(cache_key)==(signature,native_before):
        _pose_signatures.move_to_end(cache_key)
        _assign(a,'error','')
        return location,rotation
    desired_rotation=native_refs.rotation_basis(axes)@Euler(rotation,a.order).to_matrix()
    native_location=None;native_rotation=None
    if a.drive_location:
        target=origin+axes@Vector(location)
        try:local=np.linalg.solve(np.asarray(parent.to_3x3(),dtype=np.float64),np.asarray(target)-np.asarray(parent.translation))
        except np.linalg.LinAlgError as exc:raise BetterItemError('[BI-T005] Animation parent transform is singular.') from exc
        native_location=tuple(local-np.asarray(evaluated.delta_location))
    if a.drive_rotation:
        total=(orientation.inherited_rotation(evaluated).inverted()@desired_rotation).to_quaternion()
        requested=orientation.delta_rotation(evaluated).inverted()@total
        new_local=total.to_matrix();old_local=orientation.local_rotation(evaluated).to_matrix()
        try:delta=parent.to_3x3()@new_local@old_local.transposed()@parent.to_3x3().inverted()
        except ValueError as exc:raise BetterItemError('[BI-T005] Animation parent transform is singular.') from exc
        gram=delta.transposed()@delta
        if max(abs(gram[i][j]-(1 if i==j else 0)) for i in range(3) for j in range(3))>2e-5:
            raise BetterItemError('[BI-AN001] Nonuniform parenting prevents this rigid world rotation.')
        if obj.rotation_mode=='QUATERNION':native_rotation=tuple(requested)
        elif obj.rotation_mode=='AXIS_ANGLE':
            axis,angle=requested.to_axis_angle();native_rotation=(angle,*axis)
        else:native_rotation=tuple(requested.to_euler(obj.rotation_mode,evaluated.rotation_euler))
    previous=transform_view._snapshot(obj)
    try:
        if native_rotation is not None:setattr(obj,_rotation_path(obj),native_rotation)
        if native_location is not None:obj.location=native_location
        graph.update()
        result=obj.evaluated_get(graph)
        if a.drive_location and not engine._position_matches(result,target):raise BetterItemError('[BI-AN006] Evaluated animation position did not retain its target.')
        if a.drive_rotation:
            error=orientation.rotation(result).to_quaternion().rotation_difference(desired_rotation.to_quaternion()).angle
            if min(abs(error),abs(math.tau-error))>2e-4:raise BetterItemError('[BI-AN006] Evaluated animation rotation did not retain its target.')
        _assign(a,'error','')
        _pose_signatures[cache_key]=(signature,(tuple(obj.location),tuple(getattr(obj,_rotation_path(obj)))))
        while len(_pose_signatures)>2048:_pose_signatures.popitem(last=False)
        return location,rotation
    except Exception:
        for name,value in previous.items():setattr(obj,name,value)
        graph.update()
        raise


def evaluate(scene,depsgraph=None):
    global _busy
    if _busy:return
    _busy=True
    try:
        with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0]):
            try:actors=ordered(scene)
            except BetterItemError as exc:
                for obj in scene.objects:
                    if obj.is_editable and obj.better_item.animation.enabled and obj.better_item.animation.scene==scene:_assign(obj.better_item.animation,'error',str(exc))
                return
            for obj in actors:
                a=obj.better_item.animation
                try:
                    location,rotation=apply_object(bpy.context,obj,depsgraph)
                    if tuple(a.get('input_location',()))!=location:a['input_location']=location
                    if tuple(a.get('input_rotation',()))!=rotation:a['input_rotation']=rotation
                except (BetterItemError,RuntimeError,ValueError) as exc:
                    if obj.is_editable:_assign(a,'error',str(exc))
    finally:_busy=False


@persistent
def frame_changed(scene,_depsgraph=None):evaluate(scene,_depsgraph)


def sync():
    if bpy.app.is_job_running('RENDER'):return .05
    for scene in bpy.data.scenes:
        active=any(o.better_item.animation.enabled and o.better_item.animation.scene==scene for o in scene.objects)
        if not active:continue
        _ensure_dependencies(scene)
        evaluate(scene)
    return .05


def clear_runtime():
    _pose_signatures.clear()


def _input_changed(kind):
    def update(self,context):
        global _busy
        if _busy or not self.enabled:return
        _busy=True
        try:
            obj=self.id_data
            values=tuple(getattr(self,kind));previous=tuple(self.get('input_'+kind,values))
            changed=[i for i in range(3) if values[i]!=previous[i]]
            if len(changed)==1:
                axis=changed[0]
                values=linked_values(previous,axis,values[axis],getattr(obj.better_item,'link_'+kind),zero_angle_as_turn=kind=='rotation')
                setattr(self,kind,values)
            self['input_'+kind]=values
            apply_object(context,obj)
        except (BetterItemError,RuntimeError,ValueError) as exc:
            setattr(self,kind,previous)
            self['input_'+kind]=previous
            self.error=str(exc)
        finally:_busy=False
    return update


class BetterItemAnimation(bpy.types.PropertyGroup):
    enabled:bpy.props.BoolProperty(default=False,options=set())
    scene:bpy.props.PointerProperty(type=bpy.types.Scene)
    binding_uid:bpy.props.StringProperty()
    drive_location:bpy.props.BoolProperty(name='Location',default=True,options=set())
    drive_rotation:bpy.props.BoolProperty(name='Rotation',default=True,options=set())
    location:bpy.props.FloatVectorProperty(name='Location',size=3,unit='LENGTH',subtype='TRANSLATION',update=_input_changed('location'))
    rotation:bpy.props.FloatVectorProperty(name='Rotation',size=3,unit='ROTATION',subtype='EULER',update=_input_changed('rotation'))
    cached_origin:bpy.props.FloatVectorProperty(size=3,options=set())
    cached_axes:bpy.props.FloatVectorProperty(size=9,default=(1,0,0,0,1,0,0,0,1),options=set())
    cache_valid:bpy.props.BoolProperty(default=False,options=set())
    order:bpy.props.StringProperty(default='XYZ')
    error:bpy.props.StringProperty()
    warning:bpy.props.StringProperty()
    expanded:bpy.props.BoolProperty(name='Animation',default=False,options=set())
    start:bpy.props.IntProperty(name='Start',default=1,options=set())
    end:bpy.props.IntProperty(name='End',default=250,options=set())
    step:bpy.props.IntProperty(name='Step',default=1,min=1,options=set())
    previous_pivot:bpy.props.BoolProperty(default=False)
    dependencies_owned:bpy.props.BoolProperty(default=False,options=set())
    dependency_stamp:bpy.props.FloatProperty(default=0)


def start(context,obj):
    global _busy
    a=obj.better_item.animation
    if a.enabled:return
    if not a.drive_location and not a.drive_rotation:raise BetterItemError('[BI-AN001] Enable Location or Rotation.')
    guard(obj)
    if any(c.data_path=='better_item.animation.rotation' for c in object_curves(obj)) and a.order!=obj.better_item.view_rotation_order:
        raise BetterItemError('[BI-AN001] Existing relative Rotation keys use %s. Restore that Rotation Mode or use a new action.'%a.order)
    # Remove an earlier unused owned binding only by explicit user action; no
    # animation/keyframe data is deleted when starting a new recording.
    uid='';created=False
    previous_ref=(obj.better_item.reference_mode,obj.better_item.reference_frame,obj.better_item.use_reference_pivot)
    world_before=obj.matrix_world.translation.copy();rotation_before=orientation.rotation(obj).copy()
    _busy=True
    try:
        existing=_frame(context.scene,a.binding_uid)
        if existing and obj.better_item.reference_mode=='FRAME' and obj.better_item.reference_frame==existing.uid:
            uid=existing.uid;origin=frames.object_origin(context,obj);axes=frames.object_axes(context,obj)
        else:uid,origin,axes=_binding(context,obj);created=True
        a.scene=context.scene;a.binding_uid=uid;a.cache_valid=True
        a.cached_origin=origin;a.cached_axes=tuple(v for row in axes for v in row)
        a.location=axes.inverted()@(obj.matrix_world.translation-origin)
        a.order=obj.better_item.view_rotation_order
        a.rotation=(native_refs.rotation_basis(axes).transposed()@orientation.rotation(obj)).to_euler(a.order)
        a['input_location']=tuple(a.location);a['input_rotation']=tuple(a.rotation)
        a.previous_pivot=obj.better_item.use_reference_pivot
        obj.better_item.use_reference_pivot=False
        obj.better_item.reference_mode='FRAME';obj.better_item.reference_frame=uid
        a.error='';a.warning='';a.start=context.scene.frame_start;a.end=context.scene.frame_end
        a.enabled=True
        ordered(context.scene)
        _unique_action(obj)
        _ensure_dependencies(context.scene)
        context.view_layer.update()
        origin,axes=basis(context,obj,context.evaluated_depsgraph_get(),update=True)
        a.location=axes.inverted()@(world_before-origin)
        a.rotation=(native_refs.rotation_basis(axes).transposed()@rotation_before).to_euler(a.order)
        a['input_location']=tuple(a.location);a['input_rotation']=tuple(a.rotation)
        context.scene.render.use_lock_interface=True
    except Exception:
        a.enabled=False
        if a.dependencies_owned:
            obj.driver_remove(_DEPENDENCY_PATH);a.dependencies_owned=False
        obj.better_item.reference_mode,old_frame,obj.better_item.use_reference_pivot=previous_ref
        obj.better_item.reference_frame=old_frame
        if uid and created:
            index=next((i for i,f in enumerate(context.scene.better_item.frames) if f.uid==uid),None)
            if index is not None:
                frames.clear_missing_choices(context.scene,context.scene.better_item.frames[index].number)
                context.scene.better_item.frames.remove(index)
        raise
    finally:_busy=False


def pause(obj):
    a=obj.better_item.animation;a.enabled=False
    if a.dependencies_owned:
        obj.driver_remove(_DEPENDENCY_PATH);a.dependencies_owned=False
    obj.better_item.use_reference_pivot=a.previous_pivot
    if a.scene is None or _frame(a.scene,a.binding_uid) is None:
        obj.better_item.reference_mode='INDIVIDUAL';obj.better_item.orientation='GLOBAL';obj.better_item.pivot_mode='GLOBAL'


def _paths(obj,group):
    a=obj.better_item.animation
    if a.enabled and group in {'LOCATION','ROTATION'} and getattr(a,'drive_'+group.lower()):return ['better_item.animation.'+group.lower()]
    if group=='LOCATION':return ['location']
    if group=='ROTATION':return [_rotation_path(obj)]+(['location'] if obj.better_item.use_reference_pivot else [])
    return ['scale']


def _unique_action(owner):
    data=owner.animation_data
    if data and data.action and data.action.users>1:
        name=data.action_slot.identifier if data.action_slot else None
        data.action=data.action.copy()
        if name:data.action_slot=next(s for s in data.action.slots if s.identifier==name)


def keyframe(obj,group,frame,delete=False):
    if obj.better_item.animation.enabled and group in {'LOCATION','ROTATION'} and not delete:_unique_action(obj)
    for path in _paths(obj,group):
        method=obj.keyframe_delete if delete else obj.keyframe_insert
        try:
            if not delete and not method(data_path=path,frame=frame,group='Better Item Relative' if path.startswith('better_item.') else 'Object Transforms'):
                raise BetterItemError('[BI-AN005] Blender could not key "%s".'%path)
            if delete:method(data_path=path,frame=frame)
        except RuntimeError:
            if not delete:raise
    if group=='DIMENSIONS':
        for modifier in obj.modifiers:
            if modifier.type=='NODES' and modifier.node_group and modifier.node_group.get('better_item_affine')==1:
                if not delete and modifier.node_group.users>1:modifier.node_group=modifier.node_group.copy()
                if not delete:_unique_action(modifier.node_group)
                for i in range(3):
                    socket=modifier.node_group.nodes['Better Item Row %d'%i].inputs[1]
                    try:
                        if delete:socket.keyframe_delete(data_path='default_value',frame=frame)
                        else:socket.keyframe_insert(data_path='default_value',frame=frame,group='Better Item Dimensions')
                    except RuntimeError:
                        if not delete:raise


def has_key(obj,group,frame):
    paths=set(_paths(obj,group))
    return any(c.data_path in paths and any(abs(k.co.x-frame)<1e-5 for k in c.keyframe_points) for c in object_curves(obj))


def bake(context,obj):
    a=obj.better_item.animation
    if bpy.app.is_job_running('RENDER'):raise BetterItemError('[BI-AN004] Finish rendering before baking animation.')
    if not a.enabled:raise BetterItemError('[BI-AN004] Start Relative Animation before baking.')
    if a.scene!=context.scene:raise BetterItemError('[BI-AN007] Bake in the scene that owns this animation binding.')
    if a.start>a.end:raise BetterItemError('[BI-AN004] Start must not exceed End.')
    scene=context.scene;old_frame=scene.frame_current;subframe=scene.frame_subframe
    records=[];old_action=obj.animation_data.action if obj.animation_data else None
    old_slot=obj.animation_data.action_slot if obj.animation_data else None
    slot_name=old_slot.identifier if old_slot else None
    new_action=None
    try:
        samples=list(range(a.start,a.end+1,a.step))
        if samples[-1]!=a.end:samples.append(a.end)
        previous_quat=None
        for frame in samples:
            scene.frame_set(frame)
            if a.error:raise BetterItemError(a.error)
            rotation=tuple(getattr(obj,_rotation_path(obj)))
            if obj.rotation_mode=='QUATERNION':
                q=obj.rotation_quaternion.copy()
                if previous_quat:q.make_compatible(previous_quat)
                previous_quat=q.copy();rotation=tuple(q)
            records.append((frame,tuple(obj.location),rotation))
        if old_action:
            new_action=old_action.copy();new_action.name=obj.name+' - Baked Better Item'
            obj.animation_data.action=new_action
            if slot_name:obj.animation_data.action_slot=next(s for s in new_action.slots if s.identifier==slot_name)
            old_action.use_fake_user=True
            for layer in new_action.layers:
                for strip in layer.strips:
                    if strip.type!='KEYFRAME':continue
                    bag=strip.channelbag(obj.animation_data.action_slot)
                    if bag:
                        for curve in list(bag.fcurves):
                            if curve.data_path.startswith('better_item.animation.'):bag.fcurves.remove(curve)
        pause(obj)
        owned={'location'} if a.drive_location else set()
        if a.drive_rotation:owned.add(_rotation_path(obj))
        for curve in object_curves(obj):
            if curve.data_path in owned:curve.mute=False;curve.lock=False
        for frame,location,rotation in records:
            if a.drive_location:obj.location=location;obj.keyframe_insert(data_path='location',frame=frame,group='Baked Better Item')
            if a.drive_rotation:setattr(obj,_rotation_path(obj),rotation);obj.keyframe_insert(data_path=_rotation_path(obj),frame=frame,group='Baked Better Item')
        a.scene=None  # A portable baked object must not retain its entire source scene as an ID dependency.
    except Exception:
        a.enabled=True
        if obj.animation_data:
            obj.animation_data.action=old_action
            if old_slot:obj.animation_data.action_slot=old_slot
        if new_action and new_action.users==0:bpy.data.actions.remove(new_action)
        raise
    finally:scene.frame_set(old_frame,subframe=subframe)


class BETTERITEM_OT_animation(bpy.types.Operator):
    bl_idname='better_item.animation'
    bl_label='Better Item Animation'
    bl_options={'REGISTER','UNDO'}
    action:bpy.props.EnumProperty(items=[(v,v.title(),'') for v in ('START','PAUSE','BAKE')])
    @classmethod
    def poll(cls,context):return context.mode=='OBJECT' and context.active_object is not None
    def execute(self,context):
        try:
            if self.action=='START':start(context,context.active_object)
            elif self.action=='PAUSE':pause(context.active_object)
            else:bake(context,context.active_object)
        except (BetterItemError,ValueError,RuntimeError) as exc:
            self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}


class BETTERITEM_OT_keyframe(bpy.types.Operator):
    bl_idname='better_item.keyframe'
    bl_label='Insert Keyframe'
    bl_description='Insert or update group keys; Alt-click deletes. Relative pose keys while Relative Animation is active, native keys otherwise'
    bl_options={'REGISTER','UNDO'}
    group:bpy.props.EnumProperty(items=[(v,v.title(),'') for v in ('LOCATION','ROTATION','SCALE','DIMENSIONS')])
    delete:bpy.props.BoolProperty(default=False,options={'SKIP_SAVE'})
    @classmethod
    def poll(cls,context):return context.mode=='OBJECT' and context.active_object is not None
    def invoke(self,context,event):
        if not self.properties.is_property_set('delete'):self.delete=event.alt
        return self.execute(context)
    def execute(self,context):
        try:keyframe(context.active_object,self.group,context.scene.frame_current+self.frame_fraction(context),self.delete)
        except (BetterItemError,RuntimeError,ValueError) as exc:
            self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
    def frame_fraction(self,context):return context.scene.frame_subframe


def draw(layout,obj):
    a=obj.better_item.animation
    box=layout.box();box.prop(a,'expanded',text='Animation',icon='TRIA_DOWN' if a.expanded else 'TRIA_RIGHT',emboss=False)
    if not a.expanded:return
    if not a.enabled:
        row=box.row(align=True);row.prop(a,'drive_location');row.prop(a,'drive_rotation')
        box.operator('better_item.animation',text='Start Relative Animation',icon='PLAY').action='START'
        box.label(text='Diamonds key native transforms.')
        box.label(text='Start Relative to animate in a frame.')
    else:
        box.label(text='Relative animation active')
        box.label(text='Viewport / selection sources')
        box.label(text='captured when started.')
        box.operator('better_item.animation',text='Pause Relative Animation',icon='PAUSE').action='PAUSE'
        row=box.row(align=True);row.prop(a,'start');row.prop(a,'end')
        box.prop(a,'step')
        box.operator('better_item.animation',text='Bake to Native Keyframes',icon='KEYFRAME_HLT').action='BAKE'
        box.label(text='Bake for export or playback')
        box.label(text='without Better Item.')
    for message in (a.warning,a.error):
        if message:
            import textwrap
            for line in textwrap.wrap(message,30):box.label(text=line,icon='ERROR' if message==a.error else 'INFO')
