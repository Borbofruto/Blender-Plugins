# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit, nonpersistent edit session for the sidebar distribution controls."""
import bpy
from . import distribution,engine,arrange
from .math_core import BetterItemError,ReferencePending

_session=None
_updating=False


def active(scene):
    if _session is not None and not any(s.as_pointer()==_session['scene'] for s in getattr(bpy.data,'scenes',())):forget()
    return scene is not None and _session is not None and _session['scene']==scene.as_pointer()


def forget():
    global _session
    _session=None


def contextual_start(context):
    s=context.scene.better_item
    if s.distribution_method=='ENDPOINT' and s.distribution_start_override:return False
    try:return distribution.references.location_kind(context,s,True) in {'MEDIAN_POINT','BOUNDING_BOX_CENTER'}
    except BetterItemError:return False


def begin(context):
    global _session
    if context.mode!='OBJECT':raise ReferencePending('[BI-A003] Switch to Object Mode before starting Live Preview.')
    active(context.scene)
    if _session is not None:raise ReferencePending('[BI-L001] Confirm or cancel the existing Live Preview first.')
    if context.scene.better_item.distribution_legacy_range:raise ReferencePending('[BI-L001] Switch Method to choose explicit distribution references before starting Live Preview on this legacy file.')
    if contextual_start(context):raise ReferencePending('[BI-L001] Capture this selection-dependent Location into a Frame, then use that Frame for Live Preview. One-shot distribution can still capture the selection at operation start.')
    objects=list(context.selected_objects)
    if not objects:raise ReferencePending('[BI-A003] Select objects before starting Live Preview.')
    context.view_layer.update()
    status,value=distribution.inspect_spacing(context,objects)
    if status=='UNIFORM' and value is not None and context.scene.better_item.distribution_method=='OFFSET':
        context.scene.better_item['spacing']=value
    _session={'scene':context.scene.as_pointer(),'objects':objects,'active':context.active_object,
        'initial':{obj:tuple(obj.location) for obj in objects},
        'latest':{obj:tuple(obj.location) for obj in objects},
        'linear':{obj:tuple(v for row in obj.matrix_world.to_3x3() for v in row) for obj in objects}}


def _objects(context):
    if not active(context.scene):raise ReferencePending('[BI-L001] Start Live Preview for this scene first.')
    try:
        if context.mode!='OBJECT' or set(context.selected_objects)!=set(_session['objects']) or context.active_object!=_session['active']:
            raise ReferencePending('[BI-L001] The selection changed. Confirm or cancel Live Preview before arranging another selection.')
        for obj in _session['objects']:
            if obj.name not in context.scene.objects:raise ReferencePending('[BI-L001] A preview object was removed. Confirm to close this session.')
            if tuple(obj.location)!=_session['latest'][obj] or tuple(v for row in obj.matrix_world.to_3x3() for v in row)!=_session['linear'][obj]:
                raise ReferencePending('[BI-L001] A preview transform changed outside the distribution controls. Confirm to keep it, or cancel to restore the initial locations.')
    except ReferenceError as exc:raise ReferencePending('[BI-L001] A preview object no longer exists. Confirm to close the session.') from exc
    return _session['objects']


def _restore(values,context):
    valid=[]
    for obj in values:
        try:
            if obj.name in context.scene.objects:valid.append(obj)
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
        context.view_layer.update();objects=_objects(context)
        previous={obj:tuple(obj.location) for obj in objects}
        _restore(_session['initial'],context)
        try:distribution.apply(context,objects)
        except Exception:
            _restore(previous,context)
            raise
        _session['latest']={obj:tuple(obj.location) for obj in objects}
        arrange.clear_error()
    except (BetterItemError,RuntimeError,ValueError,TypeError) as exc:
        arrange.set_error(context.scene,exc)
    finally:_updating=False


def finish(context,*,cancel=False):
    if not active(context.scene):raise ReferencePending('[BI-L001] There is no Live Preview in this scene.')
    if cancel:_restore(_session['initial'],context)
    forget();arrange.clear_error()


class BETTERITEM_OT_distribution_preview(bpy.types.Operator):
    bl_idname='better_item.distribution_preview'
    bl_label='Distribution Live Preview'
    bl_description='Edit this selection from a fixed initial state; confirm or restore the initial locations'
    bl_options={'REGISTER','UNDO'}
    action:bpy.props.EnumProperty(items=[('BEGIN','Live Preview','Capture the selection without moving it'),
        ('CONFIRM','Confirm','Keep current positions and end the session'),('CANCEL','Cancel','Restore initial locations and end the session')])
    def execute(self,context):
        try:
            if self.action=='BEGIN':begin(context)
            else:finish(context,cancel=self.action=='CANCEL')
        except BetterItemError as exc:
            from . import diagnostics
            diagnostics.report(self,exc);return {'CANCELLED'}
        return {'FINISHED'}
