# SPDX-FileCopyrightText: 2026 Gabriel Webber do Nascimento
# SPDX-License-Identifier: GPL-3.0-or-later
import textwrap
import bpy
from bpy.app.handlers import persistent
from . import engine, frames, transform_view, arrange, native_refs, references, trace, animation
from .math_core import BetterItemError

frames.BetterItemFrame.__annotations__['reference_location']=references.choice_property('origin',frame=True)
frames.BetterItemFrame.__annotations__['reference_orientation']=references.choice_property('axes',frame=True)

_field_errors={}
_groups=[('LOCATION','Location','Object Location'),
         ('ROTATION','Rotation','Object Euler angles'),
         ('SCALE','Scale','Native object Scale'),
         ('DIMENSIONS','Dimensions','Dimensions in the selected orientation')]
_references=[('SELECTION','Selection Bounds (Origins)','Minimum and maximum selected object origins in world space'),
             ('KEY','Key Object (Active)','Keep the selected active object fixed'),
             ('REFERENCE','Reference Origin','Use the selected reference origin as a fixed anchor')]


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


def _arrange_changed(self,context):
    arrange.clear_error()


_reference_modes=[('INDIVIDUAL','Individual','Choose Location and Orientation independently'),
    ('FRAME','Frame','Use both components of one saved frame')]


class BetterItemObjectSettings(bpy.types.PropertyGroup):
    trace:bpy.props.PointerProperty(type=trace.BetterItemTrace)
    animation:bpy.props.PointerProperty(type=animation.BetterItemAnimation)
    reference_mode:bpy.props.EnumProperty(name='Reference',items=_reference_modes,options=set(),update=_orientation_changed)
    reference_frame:bpy.props.EnumProperty(name='Frame',items=frames.frame_items,options=set(),update=_orientation_changed)
    reference_orientation:references.choice_property('axes',False)
    reference_location:references.choice_property('origin',False)
    reference_pivot:bpy.props.EnumProperty(name='Pivot',items=native_refs.PIVOTS,options=set(),update=_origin_changed)
    reference_native:bpy.props.StringProperty(name='Native Orientation',default='GLOBAL',update=_orientation_changed)
    orientation:bpy.props.EnumProperty(name='Orientation',items=[
        ('GLOBAL','Global','World axes'),
        ('LOCAL','Local','Object local axes'),
        ('REFERENCE','Object','Use another object orientation only; ignore its position and scale'),
        ('VIEWPORT','Viewport','Current viewport transform orientation'),
        ('SAVED','Saved Frame','Use a saved reference frame orientation')]+references.ORIENTATIONS[5:],
        default='GLOBAL',options=set(),update=_orientation_changed)
    orientation_object:bpy.props.PointerProperty(name='Orientation Object',type=bpy.types.Object,update=_orientation_changed)
    orientation_frame:bpy.props.EnumProperty(name='Orientation Frame',items=frames.frame_items,options=set(),update=_orientation_changed)
    pivot_mode:bpy.props.EnumProperty(name='Origin',items=[
        ('GLOBAL','Global','World origin'),('VIEWPORT','Viewport Pivot','Current viewport pivot'),
        ('FRAME','Saved Frame','Saved reference frame origin'),('OBJECT','Object','Another object origin'),('CURSOR','3D Cursor','3D Cursor position'),('PIVOT','Pivot','Choose a native pivot'),('PARENT','Parent','Direct parent origin, or World')],default='GLOBAL',options=set(),update=_origin_changed)
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
    arrange_reference_mode:bpy.props.EnumProperty(name='Reference',items=_reference_modes,options=set(),update=_arrange_changed)
    arrange_reference_frame:bpy.props.EnumProperty(name='Frame',items=frames.frame_items,options=set(),update=_arrange_changed)
    frame_serial:bpy.props.IntProperty(default=0)
    active_frame:bpy.props.IntProperty(default=-1,min=-1)
    show_frames:bpy.props.BoolProperty(name='Show Reference Frames',default=True,options=set())
    reference:bpy.props.EnumProperty(name='Legacy Anchor',items=_references,default='SELECTION',options={'HIDDEN'},update=_arrange_changed)
    reference_orientation:references.choice_property('axes',True)
    reference_location:references.choice_property('origin',True)
    reference_pivot:bpy.props.EnumProperty(name='Pivot',items=native_refs.PIVOTS,options=set(),update=_arrange_changed)
    reference_native:bpy.props.StringProperty(name='Native Orientation',default='GLOBAL',update=_arrange_changed)
    arrange_orientation:bpy.props.EnumProperty(name='Axes',items=[
        ('GLOBAL','Global','World axes'),('LOCAL','Active Local','Active object local axes'),
        ('REFERENCE','Object','Use a chosen object orientation'),('SAVED','Saved Frame','Use a saved frame orientation'),
        ('VIEWPORT','Viewport','Use the viewport transform orientation')]+references.ORIENTATIONS[5:],default='GLOBAL',options=set(),update=_arrange_changed)
    arrange_object:bpy.props.PointerProperty(name='Orientation Object',type=bpy.types.Object,update=_arrange_changed)
    arrange_frame:bpy.props.EnumProperty(name='Orientation Frame',items=frames.frame_items,options=set(),update=_arrange_changed)
    arrange_origin:bpy.props.EnumProperty(name='Origin',items=[
        ('MATCH','Match Axes','Use the origin of the orientation object/frame, or the world origin for Global'),
        ('GLOBAL','Global','World origin'),('CURSOR','3D Cursor','3D Cursor position'),
        ('OBJECT','Object','Choose an origin object'),('SAVED','Saved Frame','Choose a saved frame origin'),
        ('VIEWPORT','Viewport Pivot','Current viewport pivot'),('PIVOT','Pivot','Choose a native pivot'),('PARENT','Parent','Direct parent origin, or World')],default='GLOBAL',options=set(),update=_arrange_changed)
    arrange_origin_object:bpy.props.PointerProperty(name='Origin Object',type=bpy.types.Object,update=_arrange_changed)
    arrange_origin_frame:bpy.props.EnumProperty(name='Origin Frame',items=frames.frame_items,options=set(),update=_arrange_changed)
    arrange_on_axis:bpy.props.BoolProperty(name='On Reference Axis',
        description='For single-axis Reference Origin distribution, place all origins on that reference line',options=set())
    minimum_distance_mm:bpy.props.FloatProperty(name='Minimum Distance (mm)',default=.00001,min=.00000001,
        precision=8,description='Minimum spacing and coordinate separation, in physical millimeters',options=set(),update=_arrange_changed)
    axes:bpy.props.BoolVectorProperty(name='Axes',size=3,default=(True,False,False),options=set(),update=_arrange_changed)
    spacing:bpy.props.FloatProperty(name='Spacing',unit='LENGTH',default=.1,precision=5,
        description='Signed spacing from the fixed key object or reference origin',options=set(),update=_arrange_changed)


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


class BETTERITEM_OT_clear_arrange_error(bpy.types.Operator):
    bl_idname='better_item.clear_arrange_error'
    bl_label='Dismiss Arrangement Error'
    def execute(self,context):
        arrange.clear_error()
        return {'FINISHED'}


class BETTERITEM_OT_align(bpy.types.Operator):
    bl_idname='better_item.align'
    bl_label='Align Origins'
    bl_description='Align object origins along the selected reference axes'
    bl_options={'REGISTER','UNDO'}
    axes:bpy.props.BoolVectorProperty(name='Axes',size=3,default=(True,False,False))
    reference:bpy.props.EnumProperty(name='Operation',items=[('AUTO','Reference','Use the selected Location')]+_references,default='AUTO',options={'HIDDEN'})
    mode:bpy.props.EnumProperty(name='Alignment',items=[('MIN','Min','Lowest coordinate'),
        ('CENTER','Center','Center between extreme coordinates'),('MAX','Max','Highest coordinate')])
    @classmethod
    def poll(cls,context):return context.mode=='OBJECT' and len(context.selected_objects)>=1
    def invoke(self,context,event):
        self.axes=context.scene.better_item.axes
        self.reference='AUTO'
        return self.execute(context)
    def execute(self,context):
        try:
            objects,origins=engine.selection_origins(context)
            targets=arrange.plan(context,objects,origins,self.axes,self.reference,mode=self.mode)
            count=engine.apply_world_positions(objects,targets)
        except BetterItemError as exc:
            arrange.set_error(context.scene,str(exc))
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}
        arrange.clear_error()
        self.report({'INFO'},'%s object(s) aligned.' % count)
        return {'FINISHED'}


class BETTERITEM_OT_distribute(bpy.types.Operator):
    bl_idname='better_item.distribute'
    bl_label='Distribute Origins'
    bl_description='Distribute origins between bounds or at signed intervals from the key object'
    bl_options={'REGISTER','UNDO'}
    axes:bpy.props.BoolVectorProperty(name='Axes',size=3,default=(True,False,False))
    reference:bpy.props.EnumProperty(name='Operation',items=[('AUTO','Reference','Use the selected Location')]+_references,default='AUTO',options={'HIDDEN'})
    spacing:bpy.props.FloatProperty(name='Spacing',unit='LENGTH',default=.1)
    minimum_mm:bpy.props.FloatProperty(name='Minimum Distance (mm)',default=.00001,min=.00000001,precision=8)
    @classmethod
    def poll(cls,context):return context.mode=='OBJECT' and len(context.selected_objects)>=1
    def invoke(self,context,event):
        settings=context.scene.better_item
        self.axes=settings.axes
        self.reference='AUTO'
        self.spacing=settings.spacing
        self.minimum_mm=settings.minimum_distance_mm
        return self.execute(context)
    def execute(self,context):
        try:
            objects,origins=engine.selection_origins(context)
            targets=arrange.plan(context,objects,origins,self.axes,self.reference,spacing=self.spacing,minimum_mm=self.minimum_mm)
            verify=arrange.distribution_verifier(context,self.axes,self.reference,self.minimum_mm)
            count=engine.apply_world_positions(objects,targets,verify=verify)
        except BetterItemError as exc:
            arrange.set_error(context.scene,str(exc))
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}
        arrange.clear_error()
        self.report({'INFO'},'%s object(s) distributed.' % count)
        return {'FINISHED'}


def _linked_rows(layout,obj,group,label,prefix,lock_name=None):
    settings=obj.better_item
    links=getattr(settings,engine.GROUP_LINK[group])
    row=layout.row(align=True)
    row.label(text=label+':')
    if group=='DIMENSIONS' and not transform_view.has_surface_geometry(obj):
        row.label(text='Unavailable')
        return
    if obj.is_editable:
        row.operator('better_item.keyframe',text='',icon='KEYFRAME_HLT' if animation.has_key(obj,group,bpy.context.scene.frame_current+bpy.context.scene.frame_subframe) else 'KEYFRAME').group=group
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
        live=settings.animation.enabled and group in {'LOCATION','ROTATION'} and getattr(settings.animation,'drive_'+group.lower())
        if live:row.prop(settings.animation,group.lower(),index=i,text=axis.upper())
        else:row.prop(settings,prefix+'_'+axis,text=axis.upper())
        row.prop(settings,engine.GROUP_LINK[group],index=i,text='',toggle=True,icon='LINKED' if links[i] else 'UNLINKED')
        if lock_name:
            locked=getattr(obj,lock_name)[i]
            row.prop(obj,lock_name,index=i,text='',emboss=False,icon='LOCKED' if locked else 'UNLOCKED')


def _draw_reference(layout,settings,arrangement=False):
    references.draw(layout,settings,arrangement)


class BETTERITEM_PT_transform(bpy.types.Panel):
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Better Item'
    bl_label='Transform'
    bl_order=1
    def draw(self,context):
        layout=self.layout
        layout.use_property_decorate=False
        obj=_active(context)
        if obj is None:
            layout.label(text='Select an object in Object Mode.')
            return
        settings=obj.better_item
        reference_layout=layout.column()
        reference_layout.enabled=not settings.animation.enabled
        _draw_reference(reference_layout,settings)
        pivot_layout=layout.column()
        pivot_layout.enabled=not settings.animation.enabled
        pivot_layout.prop(settings,'use_reference_pivot')
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
        order_layout=layout.row()
        order_layout.enabled=not settings.animation.enabled
        order_layout.prop(settings,'view_rotation_order',text='')
        _linked_rows(layout,obj,'SCALE','Scale','scale','lock_scale')
        _linked_rows(layout,obj,'DIMENSIONS','Dimensions','dimensions')
        animation.draw(layout,obj)
        trace.draw(layout,obj)


class BETTERITEM_PT_alignment(bpy.types.Panel):
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Better Item'
    bl_label='Align and Distribute'
    bl_order=2
    def draw(self,context):
        layout=self.layout
        settings=context.scene.better_item
        layout.label(text='Use object origins.')
        _draw_reference(layout,settings,arrangement=True)
        try:bounds=arrange.operation_reference(context)=='SELECTION'
        except BetterItemError:bounds=False
        row=layout.row(align=True)
        row.label(text='Axes')
        for i,axis in enumerate('XYZ'):row.prop(settings,'axes',index=i,text=axis,toggle=True)
        box=layout.box()
        box.label(text='Alignment')
        row=box.row(align=True)
        if not bounds:
            row.operator('better_item.align',text='Align to Reference').mode='CENTER'
        else:
            for mode,label in (('MIN','Min'),('CENTER','Center'),('MAX','Max')):
                row.operator('better_item.align',text=label).mode=mode
        box=layout.box()
        box.label(text='Distribution')
        if not bounds:
            box.prop(settings,'spacing')
            box.label(text='Spacing sign sets the direction.')
        else:
            box.label(text='Fixed extremes; equal intervals.')
        if not bounds:
            row=box.row()
            row.enabled=sum(settings.axes)==1
            row.prop(settings,'arrange_on_axis')
        box.prop(settings,'minimum_distance_mm')
        box.operator('better_item.distribute',text='Distribute')
        message=arrange.error(context.scene)
        if message:
            box=layout.box()
            box.alert=True
            row=box.row(align=True)
            row.label(text='Arrangement Error',icon='ERROR')
            row.operator('better_item.clear_arrange_error',text='',icon='X')
            width=min(30,max(24,int((context.region.width-40)/7)))
            for paragraph in message.splitlines():
                for line in textwrap.wrap(paragraph,width):box.label(text=line)


@persistent
def _clear_runtime(_unused):
    _field_errors.clear()
    transform_view.clear_cache()
    arrange.clear_error()
    native_refs.clear_cache()
    animation.clear_runtime()
    frames.migrate()


classes=(frames.BetterItemFrame,trace.BetterItemTrace,animation.BetterItemAnimation,BetterItemObjectSettings,BetterItemSceneSettings,BETTERITEM_OT_link_group,
         BETTERITEM_OT_clear_error,BETTERITEM_OT_clear_arrange_error,BETTERITEM_OT_align,BETTERITEM_OT_distribute,
         BETTERITEM_PT_transform,BETTERITEM_PT_alignment)+frames.classes+(native_refs.BETTERITEM_OT_native_frame,references.BETTERITEM_OT_reference_native,animation.BETTERITEM_OT_animation,animation.BETTERITEM_OT_keyframe,)


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
        if native_refs.invalidate_normal not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(native_refs.invalidate_normal)
        frames.migrate()
        if animation.frame_changed not in bpy.app.handlers.frame_change_post:bpy.app.handlers.frame_change_post.append(animation.frame_changed)
        if animation.frame_prepare not in bpy.app.handlers.frame_change_pre:bpy.app.handlers.frame_change_pre.append(animation.frame_prepare)
        if not bpy.app.timers.is_registered(animation.sync):bpy.app.timers.register(animation.sync,first_interval=.05,persistent=True)
        if not bpy.app.timers.is_registered(native_refs.sync):bpy.app.timers.register(native_refs.sync,first_interval=.2,persistent=True)
    except Exception:
        unregister()
        raise


def unregister():
    if animation.frame_prepare in bpy.app.handlers.frame_change_pre:bpy.app.handlers.frame_change_pre.remove(animation.frame_prepare)
    if bpy.app.timers.is_registered(animation.sync):bpy.app.timers.unregister(animation.sync)
    if animation.frame_changed in bpy.app.handlers.frame_change_post:bpy.app.handlers.frame_change_post.remove(animation.frame_changed)
    if hasattr(bpy.types.Object,'better_item') and hasattr(bpy.data,'objects'):
        for obj in bpy.data.objects:
            if obj.is_editable and obj.better_item.animation.dependencies_owned:
                obj.driver_remove(animation._DEPENDENCY_PATH)
                obj.better_item.animation.dependencies_owned=False
    animation.clear_runtime()
    if bpy.app.timers.is_registered(native_refs.sync):bpy.app.timers.unregister(native_refs.sync)
    for handlers in (bpy.app.handlers.load_post,bpy.app.handlers.undo_post,bpy.app.handlers.redo_post):
        if _clear_runtime in handlers:handlers.remove(_clear_runtime)
    _field_errors.clear()
    native_refs.clear_cache()
    arrange.clear_error()
    if transform_view.invalidate_geometry in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(transform_view.invalidate_geometry)
    transform_view.clear_cache()
    if native_refs.invalidate_normal in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(native_refs.invalidate_normal)
    for owner in (bpy.types.Scene,bpy.types.Object):
        if hasattr(owner,'better_item'):del owner.better_item
    for cls in reversed(classes):
        if getattr(cls,'is_registered','bl_rna' in cls.__dict__):bpy.utils.unregister_class(cls)
    frames._enum_cache.clear()
