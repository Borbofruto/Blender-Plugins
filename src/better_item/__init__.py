# SPDX-FileCopyrightText: 2026 Gabriel Webber do Nascimento
# SPDX-License-Identifier: GPL-3.0-or-later
import textwrap
import bpy
from bpy.app.handlers import persistent
from . import engine, frames, transform_view
from .math_core import BetterItemError,align_positions,distribute_positions

_field_errors={}
_groups=[('LOCATION','Location','Object Location'),
         ('ROTATION','Rotation','Object Euler angles'),
         ('SCALE','Scale','Native object Scale'),
         ('DIMENSIONS','Dimensions','Dimensions in the selected orientation')]
_references=[('SELECTION','Selection Bounds (Origins)','Minimum and maximum selected object origins in world space'),
             ('KEY','Key Object (Active)','Keep the selected active object fixed')]


def _active(context):
    return context.active_object if context.mode=='OBJECT' else None


def _component(group,axis):
    def read_value(self):
        try:return transform_view.values(bpy.context,self.id_data,group)[axis]
        except BetterItemError:return 0.
    def write_value(self,value):
        obj=self.id_data
        try:
            transform_view.edit_component(bpy.context,obj,group,axis,value)
            _field_errors.pop(obj.as_pointer(),None)
        except (BetterItemError,ValueError,RuntimeError) as exc:
            _field_errors[obj.as_pointer()]=str(exc)
        if bpy.context.area:
            bpy.context.area.tag_redraw()
    args=dict(name='XYZ'[axis],get=read_value,set=write_value,precision=3,options=set())
    if group in {'LOCATION','DIMENSIONS'}:
        args['unit']='LENGTH'
    elif group=='ROTATION':
        args.update(unit='ROTATION',subtype='ANGLE')
    if group=='DIMENSIONS':
        args['min']=0
    return bpy.props.FloatProperty(**args)


def _orientation_changed(self,context):
    # Switching reference changes the view, never the object's transform.
    _field_errors.pop(self.id_data.as_pointer(),None)
    if 'view_rotation_hint' in self:del self['view_rotation_hint']


def _origin_changed(self,context):
    _field_errors.pop(self.id_data.as_pointer(),None)


class BetterItemObjectSettings(bpy.types.PropertyGroup):
    orientation:bpy.props.EnumProperty(name='Orientation',items=[
        ('GLOBAL','Global','World axes'),
        ('LOCAL','Local','Object local axes'),
        ('REFERENCE','Object','Use another object orientation only; ignore its position and scale'),
        ('VIEWPORT','Viewport','Current viewport transform orientation'),
        ('SAVED','Saved Frame','Use a saved reference frame orientation')],
        default='GLOBAL',options=set(),update=_orientation_changed)
    orientation_object:bpy.props.PointerProperty(name='Orientation Object',type=bpy.types.Object,update=_orientation_changed)
    orientation_frame:bpy.props.EnumProperty(name='Orientation Frame',items=frames.frame_items,options=set(),update=_orientation_changed)
    pivot_mode:bpy.props.EnumProperty(name='Origin',items=[
        ('GLOBAL','Global','World origin'),('VIEWPORT','Viewport Pivot','Current viewport pivot'),
        ('FRAME','Saved Frame','Saved reference frame origin'),('OBJECT','Object','Another object origin'),('CURSOR','3D Cursor','3D Cursor position')],default='GLOBAL',options=set(),update=_origin_changed)
    pivot_frame:bpy.props.EnumProperty(name='Origin Frame',items=frames.frame_items,options=set(),update=_origin_changed)
    use_reference_pivot:bpy.props.BoolProperty(name='Use Reference Pivot',
        description='Rotate around the selected origin instead of the object origin',options=set())
    origin_object:bpy.props.PointerProperty(name='Origin Object',type=bpy.types.Object,update=_origin_changed)
    view_rotation_order:bpy.props.EnumProperty(name='Rotation Mode',items=[
        (order,order+' Euler','Euler order for reference-space Rotation') for order in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX')],default='XYZ',options=set())
    link_location:bpy.props.BoolVectorProperty(name='Link Location',size=3,default=(False,False,False),options=set())
    link_rotation:bpy.props.BoolVectorProperty(name='Link Rotation',size=3,default=(False,False,False),options=set())
    link_scale:bpy.props.BoolVectorProperty(name='Link Scale',size=3,default=(False,False,False),options=set())
    link_dimensions:bpy.props.BoolVectorProperty(name='Link Dimensions',size=3,default=(False,False,False),options=set())
    location_x:_component('LOCATION',0)
    location_y:_component('LOCATION',1)
    location_z:_component('LOCATION',2)
    rotation_x:_component('ROTATION',0)
    rotation_y:_component('ROTATION',1)
    rotation_z:_component('ROTATION',2)
    scale_x:_component('SCALE',0)
    scale_y:_component('SCALE',1)
    scale_z:_component('SCALE',2)
    dimensions_x:_component('DIMENSIONS',0)
    dimensions_y:_component('DIMENSIONS',1)
    dimensions_z:_component('DIMENSIONS',2)


class BetterItemSceneSettings(bpy.types.PropertyGroup):
    frames:bpy.props.CollectionProperty(type=frames.BetterItemFrame)
    frame_create_source:bpy.props.PointerProperty(name='Object',type=bpy.types.Object,
        poll=lambda self,obj: obj.name in self.id_data.objects)
    frame_serial:bpy.props.IntProperty(default=0)
    active_frame:bpy.props.IntProperty(default=-1,min=-1)
    show_frames:bpy.props.BoolProperty(name='Show Reference Frames',default=True,options=set())
    reference:bpy.props.EnumProperty(name='Align To',items=_references,default='SELECTION',options=set())
    axes:bpy.props.BoolVectorProperty(name='Global Axes',size=3,default=(True,False,False),options=set())
    spacing:bpy.props.FloatProperty(name='Spacing',unit='LENGTH',default=.1,precision=5,
        description='Signed spacing from the fixed key object; opposite-side objects first, ordered by distance',options=set())


class BETTERITEM_OT_link_group(bpy.types.Operator):
    bl_idname='better_item.link_group'
    bl_label='Link XYZ'
    bl_description='Link all XYZ components or unlink them'
    bl_options={'REGISTER','UNDO'}
    group:bpy.props.EnumProperty(items=_groups)
    @classmethod
    def poll(cls,context):return _active(context) is not None and context.active_object.is_editable
    def execute(self,context):
        settings=context.active_object.better_item
        name=engine.GROUP_LINK[self.group]
        value=not all(getattr(settings,name))
        setattr(settings,name,(value,value,value))
        return {'FINISHED'}


class BETTERITEM_OT_clear_error(bpy.types.Operator):
    bl_idname='better_item.clear_error'
    bl_label='Dismiss Message'
    def execute(self,context):
        if context.active_object:
            _field_errors.pop(context.active_object.as_pointer(),None)
        return {'FINISHED'}


class BETTERITEM_OT_align(bpy.types.Operator):
    bl_idname='better_item.align'
    bl_label='Align Origins'
    bl_description='Align object origins along selected global axes'
    bl_options={'REGISTER','UNDO'}
    axes:bpy.props.BoolVectorProperty(name='Global Axes',size=3,default=(True,False,False))
    reference:bpy.props.EnumProperty(name='Align To',items=_references,default='SELECTION')
    mode:bpy.props.EnumProperty(name='Alignment',items=[('MIN','Min','Lowest coordinate'),
        ('CENTER','Center','Center between extreme coordinates'),('MAX','Max','Highest coordinate')])
    @classmethod
    def poll(cls,context):return context.mode=='OBJECT' and len(context.selected_objects)>=2
    def invoke(self,context,event):
        self.axes=context.scene.better_item.axes
        self.reference=context.scene.better_item.reference
        return self.execute(context)
    def execute(self,context):
        try:
            objects,origins=engine.selection_origins(context)
            key=context.active_object.name if context.active_object else None
            targets=align_positions(origins,self.axes,self.reference,self.mode,key)
            count=engine.apply_world_positions(objects,targets)
        except BetterItemError as exc:
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}
        self.report({'INFO'},'%s object(s) aligned.' % count)
        return {'FINISHED'}


class BETTERITEM_OT_distribute(bpy.types.Operator):
    bl_idname='better_item.distribute'
    bl_label='Distribute Origins'
    bl_description='Distribute origins between bounds or at signed intervals from the key object'
    bl_options={'REGISTER','UNDO'}
    axes:bpy.props.BoolVectorProperty(name='Global Axes',size=3,default=(True,False,False))
    reference:bpy.props.EnumProperty(name='Align To',items=_references,default='SELECTION')
    spacing:bpy.props.FloatProperty(name='Spacing',unit='LENGTH',default=.1)
    @classmethod
    def poll(cls,context):return context.mode=='OBJECT' and len(context.selected_objects)>=2
    def invoke(self,context,event):
        settings=context.scene.better_item
        self.axes=settings.axes
        self.reference=settings.reference
        self.spacing=settings.spacing
        return self.execute(context)
    def execute(self,context):
        try:
            objects,origins=engine.selection_origins(context)
            key=context.active_object.name if context.active_object else None
            targets=distribute_positions(origins,self.axes,self.reference,self.spacing,key)
            count=engine.apply_world_positions(objects,targets)
        except BetterItemError as exc:
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}
        self.report({'INFO'},'%s object(s) distributed.' % count)
        return {'FINISHED'}


def _linked_rows(layout,obj,group,label,prefix,lock_name=None):
    settings=obj.better_item
    links=getattr(settings,engine.GROUP_LINK[group])
    row=layout.row(align=True)
    row.label(text=label+':')
    readonly=group=='SCALE' and not transform_view.scale_editable(obj)
    if not readonly:
        row.operator('better_item.link_group',text='',icon='LINKED' if all(links) else 'UNLINKED').group=group
    column=layout.column(align=True)
    if readonly:
        row=column.row(align=True)
        values=row.column(align=True)
        values.enabled=False
        values.prop(obj,'scale',text='')
        locks=row.column(align=True)
        for i in range(3):
            locks.prop(obj,'lock_scale',index=i,text='',emboss=False,icon='LOCKED' if obj.lock_scale[i] else 'UNLOCKED')
        return
    for i,axis in enumerate('xyz'):
        row=column.row(align=True)
        row.enabled=obj.is_editable
        row.prop(settings,prefix+'_'+axis,text=axis.upper())
        row.prop(settings,engine.GROUP_LINK[group],index=i,text='',toggle=True,icon='LINKED' if links[i] else 'UNLINKED')
        if lock_name:
            locked=getattr(obj,lock_name)[i]
            row.prop(obj,lock_name,index=i,text='',emboss=False,icon='LOCKED' if locked else 'UNLOCKED')


class BETTERITEM_PT_transform(bpy.types.Panel):
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Better Item'
    bl_label='Transform'
    def draw(self,context):
        layout=self.layout
        layout.use_property_decorate=False
        obj=_active(context)
        if obj is None:
            layout.label(text='Select an object in Object Mode.')
            return
        settings=obj.better_item
        layout.prop(settings,'orientation',text='Axes')
        if settings.orientation=='REFERENCE':layout.prop(settings,'orientation_object',text='Object')
        if settings.orientation=='SAVED':
            row=layout.row(align=True)
            row.prop(settings,'orientation_frame',text='Frame')
            row.operator('better_item.new_frame',text='',icon='ADD').target='AXES'
        layout.prop(settings,'pivot_mode')
        if settings.pivot_mode=='FRAME':
            row=layout.row(align=True)
            row.prop(settings,'pivot_frame',text='Frame')
            row.operator('better_item.new_frame',text='',icon='ADD').target='ORIGIN'
        if settings.pivot_mode=='OBJECT':layout.prop(settings,'origin_object',text='Object')
        layout.prop(settings,'use_reference_pivot')
        error=_field_errors.get(obj.as_pointer())
        try:
            frames.object_axes(context,obj)
            frames.object_origin(context,obj)
        except BetterItemError as exc:error=str(exc)
        if error:
            row=layout.row(align=True)
            row.alert=True
            row.label(text='Transform unavailable',icon='ERROR')
            row.operator('better_item.clear_error',text='',icon='X')
            width=max(22,int((context.region.width-40)/7))
            for line in textwrap.wrap(error,width):layout.label(text=line)
        _linked_rows(layout,obj,'LOCATION','Location','location','lock_location')
        _linked_rows(layout,obj,'ROTATION','Rotation','rotation','lock_rotation')
        layout.prop(settings,'view_rotation_order',text='')
        _linked_rows(layout,obj,'SCALE','Scale','scale','lock_scale')
        _linked_rows(layout,obj,'DIMENSIONS','Dimensions','dimensions')


class BETTERITEM_PT_alignment(bpy.types.Panel):
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Better Item'
    bl_label='Align and Distribute'
    bl_order=4
    def draw(self,context):
        layout=self.layout
        settings=context.scene.better_item
        layout.label(text='Use object origins.')
        layout.prop(settings,'reference')
        if settings.reference=='KEY':
            key=context.active_object
            layout.label(text='Key: '+(key.name if key and key.select_get() else 'Select an active object'),icon='OBJECT_DATA')
        row=layout.row(align=True)
        row.label(text='Global Axes')
        for i,axis in enumerate('XYZ'):row.prop(settings,'axes',index=i,text=axis,toggle=True)
        box=layout.box()
        box.label(text='Alignment')
        row=box.row(align=True)
        if settings.reference=='KEY':
            row.operator('better_item.align',text='Align to Key').mode='CENTER'
        else:
            for mode,label in (('MIN','Min'),('CENTER','Center'),('MAX','Max')):
                row.operator('better_item.align',text=label).mode=mode
        box=layout.box()
        box.label(text='Distribution')
        if settings.reference=='KEY':
            box.prop(settings,'spacing')
            box.label(text='Spacing sign sets the direction.')
        else:
            box.label(text='Fixed extremes; equal intervals.')
        box.operator('better_item.distribute',text='Distribute')


@persistent
def _clear_runtime(_unused):
    _field_errors.clear()
    transform_view.clear_cache()


classes=(frames.BetterItemFrame,BetterItemObjectSettings,BetterItemSceneSettings,BETTERITEM_OT_link_group,
         BETTERITEM_OT_clear_error,BETTERITEM_OT_align,BETTERITEM_OT_distribute,
         BETTERITEM_PT_transform,BETTERITEM_PT_alignment)+frames.classes


def register():
    try:
        for cls in classes:
            if not getattr(cls,'is_registered','bl_rna' in cls.__dict__):bpy.utils.register_class(cls)
        if not hasattr(bpy.types.Object,'better_item'):
            bpy.types.Object.better_item=bpy.props.PointerProperty(type=BetterItemObjectSettings)
        if not hasattr(bpy.types.Scene,'better_item'):
            bpy.types.Scene.better_item=bpy.props.PointerProperty(type=BetterItemSceneSettings)
        for handlers in (bpy.app.handlers.load_post,bpy.app.handlers.undo_post,bpy.app.handlers.redo_post):
            if _clear_runtime not in handlers:handlers.append(_clear_runtime)
        if transform_view.invalidate_geometry not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(transform_view.invalidate_geometry)
    except Exception:
        unregister()
        raise


def unregister():
    for handlers in (bpy.app.handlers.load_post,bpy.app.handlers.undo_post,bpy.app.handlers.redo_post):
        if _clear_runtime in handlers:handlers.remove(_clear_runtime)
    _field_errors.clear()
    if transform_view.invalidate_geometry in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(transform_view.invalidate_geometry)
    transform_view.clear_cache()
    for owner in (bpy.types.Scene,bpy.types.Object):
        if hasattr(owner,'better_item'):del owner.better_item
    for cls in reversed(classes):
        if getattr(cls,'is_registered','bl_rna' in cls.__dict__):bpy.utils.unregister_class(cls)
    frames._enum_cache.clear()
