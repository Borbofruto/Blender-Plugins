# SPDX-License-Identifier: GPL-3.0-or-later
"""Transient distribution editing of captured targets and live spatial sources."""
from contextlib import contextmanager
import bpy
from bpy.app.handlers import persistent
from . import distribution,engine,arrange,transform_view,placement
from .math_core import BetterItemError,ReferencePending

_session=None
_updating=False
_polling=False
_context_depth=0
_INTERVAL=.1


def active(scene):
    if _session is not None and not any(s.as_pointer()==_session['scene'] for s in getattr(bpy.data,'scenes',())):forget()
    return scene is not None and _session is not None and _session['scene']==scene.as_pointer()


def in_context():return _context_depth>0


def forget():
    global _session
    _session=None
    if not _polling and bpy.app.timers.is_registered(poll):bpy.app.timers.unregister(poll)


@persistent
def stop_on_frame_change(scene,*_unused):
    if active(scene):
        forget()
        arrange.set_error(scene,ReferencePending('[BI-L001] Live ended after a frame change. Enable it again to edit this frame.'))


@persistent
def stop_on_render(scene,*_unused):
    if active(scene):forget()


def contextual_start(context):
    s=context.scene.better_item
    if s.distribution_method=='ENDPOINT' and s.distribution_start_override:return False
    try:return distribution.references.location_kind(context,s,True) in {'MEDIAN_POINT','BOUNDING_BOX_CENTER'}
    except BetterItemError:return False


def captured_objects(context):
    if not active(context.scene):raise ReferencePending('[BI-L001] Enable Live for this scene first.')
    try:
        for obj in _session['objects']:
            if not engine.contains_object(context.scene,obj):raise ReferencePending('[BI-L001] A captured target was removed. Disable Live, then capture the new targets.')
        return list(_session['objects'])
    except ReferenceError as exc:raise ReferencePending('[BI-L001] A captured target no longer exists. Disable Live, then capture the new targets.') from exc


@contextmanager
def reference_context(context):
    """Selection changes must not change the captured Active Object reference."""
    global _context_depth
    objects=captured_objects(context)
    try:
        obj=_session['active']
        if obj is not None and not engine.contains_object(context.scene,obj):raise ReferenceError('Captured active object was removed')
    except ReferenceError as exc:raise ReferencePending('[BI-L001] The captured active object was removed. Disable Live and select new targets.') from exc
    with context.temp_override(active_object=obj,object=obj,selected_objects=objects,selected_editable_objects=objects):
        _context_depth+=1
        try:yield bpy.context
        finally:_context_depth-=1


def _anchors(context):
    s=context.scene.better_item
    if s.distribution_method=='ENDPOINT':
        _,start=distribution._start(context);_,end=distribution.point(context,s.distribution_end)
        return {obj for obj in (start,end) if obj is not None}
    _,_,source=arrange.reference_frame(context,'REFERENCE')
    return {source} if source is not None else set()


def _signature(context):
    s=context.scene.better_item;objects=captured_objects(context)
    if s.distribution_method=='ENDPOINT':
        start,a=distribution._start(context);end,b=distribution.point(context,s.distribution_end)
        points=(tuple(start),a.as_pointer() if a else 0,tuple(end),b.as_pointer() if b else 0)
        axes=tuple(v for row in distribution.references.axes(context,s,context.active_object,True) for v in row) if s.endpoint_path=='AXIS' else ()
        geometry_objects=objects
    else:
        matrix,origin,source=arrange.reference_frame(context,'REFERENCE')
        points=(tuple(origin),source.as_pointer() if source else 0);axes=tuple(float(v) for v in matrix.flat)
        geometry_objects=objects+([source] if source is not None and source not in objects else [])
    poses=tuple((obj.as_pointer(),obj.name,tuple(obj.location),tuple(v for row in obj.matrix_world.to_3x3() for v in row)) for obj in objects)
    geometry=()
    if s.distribution_mode!='ORIGINS':
        key=(s.distribution_mode,axes,transform_view._geometry_revision,
            tuple((o.as_pointer(),tuple(v for row in o.matrix_world.to_3x3() for v in row)) for o in geometry_objects))
        if _session.get('geometry_key')!=key:
            values=[]
            for obj in geometry_objects:
                if not transform_view.has_surface_geometry(obj):values.append((obj.as_pointer(),()));continue
                if s.distribution_mode=='GEOMETRY':
                    from mathutils import Matrix
                    left,right=placement.intervals(obj,Matrix(matrix))
                    value=tuple(left)+tuple(right)
                else:value=tuple(placement.offset(obj,s.distribution_mode))
                values.append((obj.as_pointer(),value))
            _session['geometry_key']=key;_session['geometry_value']=tuple(values)
        geometry=_session['geometry_value']
    return (s.distribution_method,s.distribution_mode,s.endpoint_path,tuple(s.axes),s.spacing,s.distribution_last_sign,
        s.minimum_distance_mm,points,axes,poses,geometry)


def begin(context):
    global _session
    if context.mode!='OBJECT':raise ReferencePending('[BI-A003] Switch to Object Mode before enabling Live.')
    active(context.scene)
    if _session is not None:raise ReferencePending('[BI-L001] Disable Live in the existing scene before enabling it here.')
    if context.scene.better_item.distribution_legacy_range:raise ReferencePending('[BI-L001] Switch Method to choose explicit distribution references before enabling Live on this legacy file.')
    if contextual_start(context):raise ReferencePending('[BI-L001] Capture this selection-dependent Location into a Frame, then use that Frame for Live. One-shot distribution can still capture the selection at operation start.')
    objects=list(context.selected_objects)
    if not objects:raise ReferencePending('[BI-A003] Select objects before enabling Live.')
    context.view_layer.update()
    _session={'scene':context.scene.as_pointer(),'view_layer':context.view_layer,
        'objects':objects,'active':context.active_object,'orders':{},'sources':set(),'signature':None,
        'initial':{obj:tuple(obj.location) for obj in objects},'latest':{obj:tuple(obj.location) for obj in objects},
        'linear':{obj:tuple(v for row in obj.matrix_world.to_3x3() for v in row) for obj in objects}}
    # Incomplete sources remain a normal setup state. Enabling never applies.
    try:
        with reference_context(context) as ctx:_session['signature']=_signature(ctx)
    except BetterItemError:pass
    if not bpy.app.timers.is_registered(poll):bpy.app.timers.register(poll,first_interval=_INTERVAL)


def _objects(context,anchors):
    if context.mode!='OBJECT':raise ReferencePending('[BI-A003] Return to Object Mode to continue Live editing.')
    objects=captured_objects(context)
    for obj in objects:
        if obj in anchors:continue
        if tuple(obj.location)!=_session['latest'][obj] or tuple(v for row in obj.matrix_world.to_3x3() for v in row)!=_session['linear'][obj]:
            raise ReferencePending('[BI-L001] Captured target "%s" was transformed outside Live. Disable Live, then enable it again to capture the changed targets.'%obj.name)
    return objects


def _restore(values,context):
    valid=[]
    for obj in values:
        try:
            if engine.contains_object(context.scene,obj):valid.append(obj)
        except ReferenceError:continue
    for obj in sorted(valid,key=engine._depth):
        try:
            if tuple(obj.location)!=values[obj]:obj.location=values[obj]
        except ReferenceError:continue
    context.view_layer.update()


def update(context):
    global _updating
    if _updating or context is None or not active(getattr(context,'scene',None)):return
    _updating=True
    try:
        if context.mode!='OBJECT':raise ReferencePending('[BI-A003] Return to Object Mode to continue Live editing.')
        context.view_layer.update()
        with reference_context(context) as ctx:
            anchors=_anchors(ctx);objects=_objects(ctx,anchors);_session['sources'].update(anchors)
            previous={obj:tuple(obj.location) for obj in objects}
            _restore({obj:value for obj,value in _session['initial'].items() if obj not in anchors},ctx)
            s=ctx.scene.better_item;key=(s.distribution_method,s.distribution_mode,s.endpoint_path,tuple(s.axes))
            kwargs={}
            if s.distribution_method=='ENDPOINT' and key in _session['orders']:
                kwargs['order_override']=[obj for obj in _session['orders'][key] if obj not in anchors]
            try:_,info=distribution.apply(ctx,objects,**kwargs)
            except Exception:
                _restore(previous,ctx)
                raise
            if s.distribution_method=='ENDPOINT':
                _session['orders'][key]=list(info['order'])
            _session['latest']={obj:tuple(obj.location) for obj in objects}
            _session['linear']={obj:tuple(v for row in obj.matrix_world.to_3x3() for v in row) for obj in objects}
            _session.pop('unexpected_failure',None)
            arrange.clear_error()
    except (BetterItemError,RuntimeError,ValueError,TypeError,ReferenceError) as exc:
        arrange.set_error(context.scene,exc)
    finally:
        if active(context.scene):
            try:
                with reference_context(context) as ctx:_session['signature']=_signature(ctx)
            except (BetterItemError,RuntimeError,ReferenceError):_session['signature']=None
        _updating=False
    for area in getattr(context.screen,'areas',()):
        if area.type=='VIEW_3D':area.tag_redraw()


def poll():
    """Only an enabled editing session observes source changes; never playback."""
    global _polling
    if _session is None:return None
    if _session.get('unexpected_failure'):return _INTERVAL
    _polling=True
    try:
        ctx=bpy.context
        if not active(getattr(ctx,'scene',None)) or ctx.view_layer!=_session['view_layer']:return _INTERVAL
        if ctx.mode!='OBJECT':return _INTERVAL
        with reference_context(ctx) as captured:signature=_signature(captured)
        if signature!=_session['signature']:update(ctx)
    except (BetterItemError,RuntimeError,ValueError,TypeError,ReferenceError) as exc:
        if _session is not None and getattr(bpy.context,'scene',None):arrange.set_error(bpy.context.scene,exc)
    except Exception as exc:
        # Keep the timer registered but suspend a broken session until disabled.
        if _session is not None:
            arrange.set_error(bpy.context.scene,BetterItemError('[BI-V002] Live update failed unexpectedly: %s. Disable Live before continuing.'%exc,severity='ERROR'))
            _session['unexpected_failure']=True
    finally:_polling=False
    return _INTERVAL if _session is not None else None


def status(scene):
    if not active(scene):return ''
    try:return 'Live: %d captured objects'%len(_session['objects'])
    except ReferenceError:return 'Live paused: a captured object was removed.'


def active_name(scene):
    if not active(scene):return ''
    try:return _session['active'].name if _session['active'] else ''
    except ReferenceError:return ''


def finish(context,*,cancel=False):
    if not active(context.scene):raise ReferencePending('[BI-L001] There is no Live session in this scene.')
    if cancel:_restore({obj:value for obj,value in _session['initial'].items() if obj not in _session['sources']},context)
    forget();arrange.clear_error()


class BETTERITEM_OT_distribution_preview(bpy.types.Operator):
    bl_idname='better_item.distribution_preview'
    bl_label='Distribution Live Preview'
    bl_description='Capture targets for live spatial editing; keep or restore target locations'
    bl_options={'REGISTER','UNDO'}
    action:bpy.props.EnumProperty(items=[('BEGIN','Live','Capture targets without moving them'),
        ('CONFIRM','Confirm','Keep current positions and end the session'),('CANCEL','Cancel','Restore initial target locations and end the session')])
    def execute(self,context):
        try:
            if self.action=='BEGIN':begin(context)
            else:finish(context,cancel=self.action=='CANCEL')
        except BetterItemError as exc:
            from . import diagnostics
            diagnostics.report(self,exc);return {'CANCELLED'}
        return {'FINISHED'}
