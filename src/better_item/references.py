# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared reference choices, readers and UI for Transform and Arrange.

The field map preserves .blend/RNA compatibility with earlier releases. Both
consumers use the same choices and resolution rules; operation anchors remain
the responsibility of the arrangement planner.
"""
import bpy
from mathutils import Matrix,Vector
from . import native_refs,orientation
from .math_core import BetterItemError

ORIENTATIONS=[('GLOBAL','Global','World axes'),('LOCAL','Local','Active object axes'),
    ('REFERENCE','Object','Chosen object axes'),('VIEWPORT','Viewport','Current viewport orientation'),
    ('SAVED','Saved Frame','Orientation component of a scene frame'),
    ('NORMAL','Normal','Native selection normal'),('GIMBAL','Gimbal','Native Gimbal axes'),
    ('VIEW','View','Current view axes'),('CURSOR','Cursor','3D Cursor axes'),
    ('PARENT','Parent','Active object parent axes'),('NATIVE','Native Orientation','Link to a named native custom orientation')]
LOCATIONS=[('GLOBAL','Global','World origin'),('VIEWPORT','Viewport Pivot','Current native pivot choice'),
    ('FRAME','Saved Frame','Location component of a scene frame'),('OBJECT','Object','Chosen object origin'),
    ('CURSOR','3D Cursor','3D Cursor position'),('PIVOT','Pivot','Choose any native pivot type')]
_FIELDS={False:dict(mode='reference_mode',frame='reference_frame',axes='orientation',axes_object='orientation_object',
    axes_frame='orientation_frame',origin='pivot_mode',origin_object='origin_object',origin_frame='pivot_frame'),
    True:dict(mode='arrange_reference_mode',frame='arrange_reference_frame',axes='arrange_orientation',
    axes_object='arrange_object',axes_frame='arrange_frame',origin='arrange_origin',
    origin_object='arrange_origin_object',origin_frame='arrange_origin_frame')}


def _location_mode(settings,arrangement):
    f=_FIELDS[arrangement]
    mode=getattr(settings,f['origin'])
    if mode=='SAVED':return 'FRAME'
    if mode!='MATCH':return mode
    axes=getattr(settings,f['axes'])
    return {'SAVED':'FRAME','REFERENCE':'OBJECT','LOCAL':'ACTIVE','VIEWPORT':'VIEWPORT'}.get(axes,'GLOBAL')


def choice_property(kind,arrangement):
    items=ORIENTATIONS if kind=='axes' else LOCATIONS
    names=[item[0] for item in items]
    def get(self):
        mode=getattr(self,_FIELDS[arrangement]['axes']) if kind=='axes' else _location_mode(self,arrangement)
        if mode=='ACTIVE':mode='PIVOT'
        return names.index(mode)
    def set_value(self,value):
        mode=names[value]
        if kind=='origin' and arrangement and mode=='FRAME':mode='SAVED'
        setattr(self,_FIELDS[arrangement][kind],mode)
    return bpy.props.EnumProperty(name='Orientation' if kind=='axes' else 'Location',items=items,get=get,set=set_value,options=set())


def axes(context,settings,active,arrangement=False):
    from . import frames
    f=_FIELDS[arrangement]
    if getattr(settings,f['mode'])=='FRAME':return frames.frame_axes(frames.find(context.scene,getattr(settings,f['frame'])),context)
    mode=getattr(settings,f['axes'])
    if mode=='SAVED':return frames.frame_axes(frames.find(context.scene,getattr(settings,f['axes_frame'])),context)
    if mode=='VIEWPORT':return frames.viewport_axes(context,active)
    if mode=='NATIVE':return native_refs.orientation(context,settings.reference_native,active)
    if mode in native_refs.BUILTINS and mode not in {'GLOBAL','LOCAL'}:return native_refs.orientation(context,mode,active)
    return orientation.basis(active,mode,getattr(settings,f['axes_object']))


def origin(context,settings,active,arrangement=False):
    from . import frames
    f=_FIELDS[arrangement]
    if getattr(settings,f['mode'])=='FRAME':
        frame=frames.find(context.scene,getattr(settings,f['frame']))
        return frames.frame_origin(frame,context),frames.position_reference_object(frame,context.scene)
    mode=_location_mode(settings,arrangement)
    if mode=='GLOBAL':return Vector(),None
    if mode=='FRAME':
        name=f['axes_frame'] if arrangement and settings.arrange_origin=='MATCH' else f['origin_frame']
        frame=frames.find(context.scene,getattr(settings,name))
        return frames.frame_origin(frame,context),frames.position_reference_object(frame,context.scene)
    if mode in {'OBJECT','ACTIVE'}:
        if mode=='ACTIVE':source=active
        else:
            name=f['axes_object'] if arrangement and settings.arrange_origin=='MATCH' else f['origin_object']
            source=getattr(settings,name)
        if source is None:raise BetterItemError('[BI-F002] Choose a Location Object.')
        return source.matrix_world.translation.copy(),source
    if mode=='CURSOR':return context.scene.cursor.location.copy(),None
    pivot=settings.reference_pivot if mode=='PIVOT' else context.scene.tool_settings.transform_pivot_point
    return native_refs.pivot(context,pivot,active),None


def draw(layout,settings,arrangement=False):
    f=_FIELDS[arrangement]
    box=layout.box()
    box.label(text='Reference')
    box.row(align=True).prop(settings,f['mode'],expand=True)
    if getattr(settings,f['mode'])=='FRAME':
        row=box.row(align=True)
        row.prop(settings,f['frame'],text='')
        row.operator('better_item.new_frame',text='',icon='ADD').target='ALIGN_BOTH' if arrangement else 'BOTH'
        return
    box.prop(settings,'reference_orientation',text='Orientation')
    mode=getattr(settings,f['axes'])
    if mode=='REFERENCE':box.prop(settings,f['axes_object'],text='Object')
    elif mode=='SAVED':
        row=box.row(align=True)
        row.prop(settings,f['axes_frame'],text='Frame')
        row.operator('better_item.new_frame',text='',icon='ADD').target='ALIGN_AXES' if arrangement else 'AXES'
    elif mode=='NATIVE':
        box.label(text='Source: '+settings.reference_native)
        box.prop(bpy.context.scene.transform_orientation_slots[0],'type',text='Viewport')
        box.operator('better_item.reference_native',text='Use Viewport Choice').arrangement=arrangement
    box.prop(settings,'reference_location',text='Location')
    mode=_location_mode(settings,arrangement)
    if mode=='OBJECT':
        name=f['axes_object'] if arrangement and settings.arrange_origin=='MATCH' else f['origin_object']
        box.prop(settings,name,text='Object')
    elif mode=='FRAME':
        row=box.row(align=True)
        name=f['axes_frame'] if arrangement and settings.arrange_origin=='MATCH' else f['origin_frame']
        row.prop(settings,name,text='Frame')
        row.operator('better_item.new_frame',text='',icon='ADD').target='ALIGN_ORIGIN' if arrangement else 'ORIGIN'
    elif mode in {'PIVOT','ACTIVE'}:box.prop(settings,'reference_pivot',text='Pivot')


def migrate(scene):
    settings=scene.better_item
    if settings.get('reference_schema',0)>=2:return
    # Before 1.4.2, an absent arrangement origin meant Match Axes. Resolve it
    # once, keeping the stored axes and origin independent from then onward.
    if settings.get('arrange_origin',0)==0:
        mode=_location_mode(settings,True) if settings.get('arrange_origin') is not None else {
            'REFERENCE':'OBJECT','SAVED':'FRAME','LOCAL':'ACTIVE','VIEWPORT':'VIEWPORT'}.get(settings.arrange_orientation,'GLOBAL')
        if mode=='FRAME':
            settings['arrange_origin_frame']=settings.get('arrange_frame',0)
            settings.arrange_origin='SAVED'
        elif mode=='OBJECT':
            settings.arrange_origin_object=settings.arrange_object
            settings.arrange_origin='OBJECT'
        elif mode=='ACTIVE':
            settings.arrange_origin='PIVOT'
            settings.reference_pivot='ACTIVE_ELEMENT'
        else:settings.arrange_origin=mode
    settings['reference_schema']=2


class BETTERITEM_OT_reference_native(bpy.types.Operator):
    bl_idname='better_item.reference_native'
    bl_label='Use Viewport Orientation'
    bl_options={'REGISTER','UNDO'}
    arrangement:bpy.props.BoolProperty(default=False,options={'SKIP_SAVE'})
    def execute(self,context):
        if not self.arrangement and context.active_object is None:return {'CANCELLED'}
        settings=context.scene.better_item if self.arrangement else context.active_object.better_item
        name=context.scene.transform_orientation_slots[0].type
        try:native_refs.orientation(context,name)
        except BetterItemError as exc:
            self.report({'ERROR'},str(exc));return {'CANCELLED'}
        custom=context.scene.transform_orientation_slots[0].custom_orientation
        if custom:native_refs._custom_cache[(context.scene.as_pointer(),name)]=custom.matrix.copy()
        settings.reference_native=name
        return {'FINISHED'}
