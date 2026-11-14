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

# Storage extension order is historical: both object/scene enum tables append
# these at IDs 5..10. Retired entries remain readable for .blend migration;
# they are not offered by the current selectors below.
STORED_AXIS_EXTENSIONS=[('NORMAL','Normal','Native selection normal'),
    ('GIMBAL','Gimbal','Native Gimbal axes'),('VIEW','View','Current view axes'),
    ('CURSOR','Cursor','3D Cursor axes'),('PARENT','Parent','Direct parent axes'),
    ('NATIVE','Native Orientation','Link to a named native custom orientation')]
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


# Visible choices are shared by both consumers and the frame editor. Legacy
# storage fields keep their numeric IDs so existing .blend files remain readable.
_LOCATION_CHOICES=[
    ('GLOBAL','Global','World origin','WORLD'),
    ('FRAME','Frame','Location component of a saved frame','EMPTY_AXIS'),
    ('OBJECT','Object','Chosen object origin','OBJECT_DATA'),
    ('BOUNDING_BOX_CENTER','Bounding Box Center','Center of selected geometry bounds','PIVOT_BOUNDBOX'),
    ('CURSOR','3D Cursor','3D Cursor position','PIVOT_CURSOR'),
    ('INDIVIDUAL_ORIGINS','Individual Origins','Active object origin for a single reference point','PIVOT_INDIVIDUAL'),
    ('MEDIAN_POINT','Median Point','Median of the selection','PIVOT_MEDIAN'),
    ('ACTIVE_ELEMENT','Active Element','Active selection element','PIVOT_ACTIVE')]
_ORIENTATION_CHOICES=[
    ('GLOBAL','Global','World axes','ORIENTATION_GLOBAL'),
    ('SAVED','Frame','Orientation component of a saved frame','EMPTY_AXIS'),
    ('REFERENCE','Object','Chosen object axes, ignoring scale','OBJECT_DATA'),
    ('NORMAL','Normal','Native selection normal','ORIENTATION_NORMAL'),
    ('GIMBAL','Gimbal','Native Gimbal axes','ORIENTATION_GIMBAL'),
    ('VIEW','View','Current view axes','ORIENTATION_VIEW'),
    ('CURSOR','3D Cursor','3D Cursor axes','ORIENTATION_CURSOR'),
    ('NATIVE','Custom Orientation...','Choose a named custom transform orientation','EMPTY_AXIS')]


def _choices(kind,frame=False):
    values=_ORIENTATION_CHOICES if kind=='axes' else _LOCATION_CHOICES
    if frame:values=[('MANUAL','Manual','Independent values stored in this frame','EDITMODE_HLT')]+values
    return values


def _visible(settings,kind,arrangement=False,frame=False):
    if frame:
        mode=settings.rotation_mode if kind=='axes' else settings.position_mode
        if kind=='axes':
            if mode=='OBJECT':return 'REFERENCE'
            if mode=='FRAME':return 'SAVED'
            if mode=='NATIVE':return settings.native_source if settings.native_source in {'GLOBAL','NORMAL','GIMBAL','VIEW','CURSOR'} else 'NATIVE'
        elif mode=='PIVOT':return settings.position_pivot
        return mode
    f=_FIELDS[arrangement]
    mode=getattr(settings,f['axes']) if kind=='axes' else _location_mode(settings,arrangement)
    if kind=='origin':
        if mode=='PIVOT':return settings.reference_pivot
        if mode=='ACTIVE':return 'ACTIVE_ELEMENT'
    return mode


def choice_property(kind,arrangement=False,frame=False):
    choices=_choices(kind,frame)
    names=[item[0] for item in choices]
    items=[]
    custom={'MANUAL','FRAME','SAVED','OBJECT','REFERENCE','NATIVE'}
    for title,is_custom in (('Better Item',True),('Default',False)):
        items.append(('',title,''))
        items.extend((*item,i) for i,item in enumerate(choices) if (item[0] in custom)==is_custom)
    def get(self):
        mode=_visible(self,kind,arrangement,frame)
        return names.index(mode) if mode in names else 0
    def set_value(self,value):
        mode=names[value]
        if frame:
            if kind=='origin':
                if mode in {item[0] for item in native_refs.PIVOTS}:
                    self.position_pivot=mode;self.position_mode='PIVOT'
                else:self.position_mode=mode
            else:
                if mode=='REFERENCE':self.rotation_mode='OBJECT'
                elif mode=='SAVED':self.rotation_mode='FRAME'
                elif mode=='MANUAL':self.rotation_mode='MANUAL'
                elif mode=='PARENT':self.rotation_mode='PARENT'
                else:
                    if mode!='NATIVE':self.native_source=mode
                    elif self.native_source in native_refs.BUILTINS:self.native_source=''
                    self.rotation_mode='NATIVE'
        else:
            f=_FIELDS[arrangement]
            if kind=='origin' and mode in {item[0] for item in native_refs.PIVOTS}:
                # Keep the dedicated legacy cursor ID, retained for old file compatibility.
                self.reference_pivot=mode
                setattr(self,f['origin'],'CURSOR' if mode=='CURSOR' else 'PIVOT')
            else:
                if kind=='origin' and arrangement and mode=='FRAME':mode='SAVED'
                if kind=='axes' and mode=='NATIVE' and self.reference_native in native_refs.BUILTINS:self.reference_native=''
                setattr(self,f[kind],mode)
    return bpy.props.EnumProperty(name='Orientation' if kind=='axes' else 'Location',items=items,get=get,set=set_value,options=set())


def axes(context,settings,active,arrangement=False):
    from . import frames
    f=_FIELDS[arrangement]
    if getattr(settings,f['mode'])=='FRAME':return frames.frame_axes(frames.find(context.scene,getattr(settings,f['frame'])),context)
    mode=getattr(settings,f['axes'])
    if mode=='PARENT':return orientation.rotation(active.parent) if active and active.parent else Matrix.Identity(3)
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
    if mode=='PARENT':return (active.parent.matrix_world.translation.copy(),active.parent) if active and active.parent else (Vector(),None)
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


def location_kind(context,settings,arrangement=False):
    """Concrete point source, following frame pointers without evaluating it."""
    from . import frames
    f=_FIELDS[arrangement]
    if getattr(settings,f['mode'])=='FRAME':
        frame=frames.find(context.scene,getattr(settings,f['frame']))
    elif _location_mode(settings,arrangement)=='FRAME':
        frame=frames.find(context.scene,getattr(settings,f['axes_frame'] if arrangement and settings.arrange_origin=='MATCH' else f['origin_frame']))
    else:return _visible(settings,'origin',arrangement)
    seen=set()
    while frame.position_mode=='FRAME':
        if frame.uid in seen:raise BetterItemError('[BI-F001] Circular Location reference.')
        seen.add(frame.uid);frame=frames.find(context.scene,frame.position_frame)
    return frame.position_pivot if frame.position_mode=='PIVOT' else frame.position_mode


def draw_component(layout,settings,kind,arrangement=False,frame=False):
    from . import frames
    f=_FIELDS[arrangement]
    prop=('reference_orientation' if kind=='axes' else 'reference_location')
    layout.prop(settings,prop,text='Orientation' if kind=='axes' else 'Location')
    mode=_visible(settings,kind,arrangement,frame)
    if mode in {'OBJECT','REFERENCE','PARENT'}:
        if frame:
            layout.prop(settings,'rotation_source' if kind=='axes' else 'position_source',text='Child Object' if mode=='PARENT' else 'Object')
        elif mode!='PARENT':layout.prop(settings,f['axes_object' if kind=='axes' else 'origin_object'],text='Object')
        if mode=='PARENT':
            from .trace import draw_parent_label
            source=getattr(settings,'rotation_source' if kind=='axes' else 'position_source') if frame else bpy.context.active_object
            draw_parent_label(layout,source)
    elif mode in {'SAVED','FRAME'}:
        row=layout.row(align=True)
        name=('rotation_frame' if kind=='axes' else 'position_frame') if frame else f['axes_frame' if kind=='axes' else 'origin_frame']
        row.prop(settings,name,text='Frame')
        if not frame:row.operator('better_item.new_frame',text='',icon='ADD').target=('ALIGN_' if arrangement else '')+('AXES' if kind=='axes' else 'ORIGIN')
    elif mode=='NATIVE':
        layout.prop(settings,'native_source' if frame else 'reference_native',text='Name')


    if mode=='INDIVIDUAL_ORIGINS':layout.label(text='Single reference: active origin.')


def draw(layout,settings,arrangement=False):
    f=_FIELDS[arrangement]
    box=layout.box();box.label(text='Reference')
    box.row(align=True).prop(settings,f['mode'],expand=True)
    if getattr(settings,f['mode'])=='FRAME':
        row=box.row(align=True);row.prop(settings,f['frame'],text='')
        row.operator('better_item.new_frame',text='',icon='ADD').target='ALIGN_BOTH' if arrangement else 'BOTH'
        return
    draw_component(box,settings,'axes',arrangement)
    draw_component(box,settings,'origin',arrangement)


def migrate(scene):
    settings=scene.better_item
    if settings.get('reference_schema',0)>=2:
        _migrate_visible(scene)
        return
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
    _migrate_visible(scene)


def _migrate_visible(scene):
    """Resolve retired shortcuts once; keep actual axes/pivots in old files."""
    from . import frames
    owners=[(scene.better_item,True,None)]+[(o.better_item,False,o) for o in scene.objects]
    for settings,arrangement,obj in owners:
        if settings.get('parent_shortcut_schema',0)<1:
            active=obj or bpy.context.active_object
            parent=active.parent if active else None
            f=_FIELDS[arrangement]
            if getattr(settings,f['axes'])=='PARENT':
                setattr(settings,f['axes_object'],parent);setattr(settings,f['axes'],'REFERENCE' if parent else 'GLOBAL')
            if _location_mode(settings,arrangement)=='PARENT':
                setattr(settings,f['origin_object'],parent);setattr(settings,f['origin'],'OBJECT' if parent else 'GLOBAL')
            settings['parent_shortcut_schema']=1
        if settings.get('reference_ui_schema',0)>=1:continue
        f=_FIELDS[arrangement]
        with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0]):
            bpy.context.view_layer.update()
            active=obj or bpy.context.active_object
            mode=getattr(settings,f['axes'])
            if mode in {'LOCAL','VIEWPORT'}:
                try:matrix=orientation.rotation(active) if mode=='LOCAL' else frames.viewport_axes(bpy.context,active)
                except (BetterItemError,AttributeError,RuntimeError):matrix=Matrix.Identity(3)
                frame=frames.create(bpy.context,'Imported Orientation - '+(obj.name if obj else scene.name),Vector(),matrix)
                settings_frame=frame.uid
                setattr(settings,f['axes_frame'],settings_frame)
                setattr(settings,f['axes'],'SAVED')
            if _location_mode(settings,arrangement)=='VIEWPORT':
                settings.reference_pivot=scene.tool_settings.transform_pivot_point
                setattr(settings,f['origin'],'PIVOT')
        settings['reference_ui_schema']=1
    for frame in scene.better_item.frames:
        for kind in ('position','rotation'):
            if getattr(frame,kind+'_mode')=='PARENT':
                source=getattr(frame,kind+'_source')
                if source is None:continue
                parent=source.parent
                setattr(frame,kind+'_source',parent)
                setattr(frame,kind+'_mode','OBJECT' if parent else ('GLOBAL' if kind=='position' else 'NATIVE'))
                if not parent and kind=='rotation':frame.native_source='GLOBAL'
        if frame.rotation_mode=='NATIVE' and frame.native_source=='LOCAL':
            with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0]):
                try:frames.apply_reference(frame,'ROTATION')
                except BetterItemError:pass

