# SPDX-FileCopyrightText: 2026 Gabriel Webber do Nascimento
# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from bpy.app.handlers import persistent
from . import engine, frames, transform_view, arrange, native_refs, references, trace,diagnostics,geometry_arrange
from .math_core import BetterItemError

_field_errors={}
_groups=[('LOCATION','Location','Object Location'),
         ('ROTATION','Rotation','Object Euler angles'),
         ('SCALE','Scale','Native object Scale'),
         ('DIMENSIONS','Dimensions','Dimensions in the selected orientation')]
_references=[('SELECTION','Selection Bounds (Origins)','Minimum and maximum selected object origins in world space'),
             ('KEY','Key Object (Active)','Keep the selected active object fixed'),
             ('REFERENCE','Reference Origin','Use the selected reference origin as a fixed anchor')]


def _arrangement_failed(operator,context,error):
    """Domain diagnostics keep their severity; unknown API faults are critical."""
    message=diagnostics.Diagnostic(error)
    operation=operator.bl_idname.rsplit('_OT_',1)[-1].rsplit('.',1)[-1]
    message.operation={'distribute':'Distribution','align_orientation':'Orientation','align':'Alignment'}.get(operation)
    arrange.set_error(context.scene,message)
    diagnostics.report(operator,error)
    return {'CANCELLED'}


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
        except (BetterItemError,ValueError,RuntimeError,TypeError) as exc:
            _field_errors[obj.as_pointer()]=diagnostics.Diagnostic(exc)
        if bpy.context.area:
            bpy.context.area.tag_redraw()
    args=dict(name='XYZ'[axis],get=read_value,set=write_value,precision=3,options=set())
    if group in {'LOCATION','DIMENSIONS'}:
        args['unit']='LENGTH'
    elif group=='ROTATION':
        args.update(unit='ROTATION',subtype='ANGLE')
    if group=='DIMENSIONS':
        args['min']=0
        args['description']='Reference: physical projected width along the chosen unit direction. Default / Local: Blender Item Dimensions. Edits are centered on the object origin.'
    return bpy.props.FloatProperty(**args)


def _orientation_changed(self,context):
    # Switching reference changes the view, never the object's transform.
    _field_errors.pop(self.id_data.as_pointer(),None)
    if 'view_rotation_hint' in self:del self['view_rotation_hint']


def _origin_changed(self,context):
    _field_errors.pop(self.id_data.as_pointer(),None)


def _links_changed(self,context):
    _field_errors.pop(self.id_data.as_pointer(),None)


def _arrange_changed(self,context):
    arrange.clear_error()


_reference_modes=[('INDIVIDUAL','Individual','Choose Location and Orientation independently'),
    ('FRAME','Frame','Use both components of one saved frame')]


class BetterItemObjectSettings(bpy.types.PropertyGroup):
    show_diagnostic_details:bpy.props.BoolProperty(default=False,options=set())
    trace:bpy.props.PointerProperty(type=trace.BetterItemTrace)
    transform_space:bpy.props.EnumProperty(name='Coordinates',items=[('DEFAULT','Default / Local','Blender Item channels, excluding inherited transforms'),('REFERENCE','Reference','Measure and edit in the chosen reference')],default='REFERENCE',options=set(),update=_orientation_changed)
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
        ('SAVED','Saved Frame','Use a saved reference frame orientation')]+references.STORED_AXIS_EXTENSIONS,
        default='GLOBAL',options=set(),update=_orientation_changed)
    orientation_object:bpy.props.PointerProperty(name='Orientation Object',type=bpy.types.Object,update=_orientation_changed)
    orientation_frame:bpy.props.EnumProperty(name='Orientation Frame',items=frames.frame_items,options=set(),update=_orientation_changed)
    pivot_mode:bpy.props.EnumProperty(name='Origin',items=[
        ('GLOBAL','Global','World origin'),('VIEWPORT','Viewport Pivot','Current viewport pivot'),
        ('FRAME','Saved Frame','Saved reference frame origin'),('OBJECT','Object','Another object origin'),('CURSOR','3D Cursor','3D Cursor position'),('PIVOT','Pivot','Choose a native pivot'),('PARENT','Parent','Direct parent origin, or World')],default='GLOBAL',options=set(),update=_origin_changed)
    pivot_frame:bpy.props.EnumProperty(name='Origin Frame',items=frames.frame_items,options=set(),update=_origin_changed)
    use_reference_pivot:bpy.props.BoolProperty(name='Rotate Around Reference Location',
        description='Rotate around the selected Location reference; otherwise rotate around the object origin',options=set())
    origin_object:bpy.props.PointerProperty(name='Origin Object',type=bpy.types.Object,update=_origin_changed)
    view_rotation_order:bpy.props.EnumProperty(name='Rotation Mode',items=[
        (order,order+' Euler','Euler order for reference-space Rotation') for order in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX')],default='XYZ',options=set(),update=_orientation_changed)
    link_location:bpy.props.BoolVectorProperty(name='Link Location',size=3,default=(False,False,False),options=set(),update=_links_changed)
    link_rotation:bpy.props.BoolVectorProperty(name='Link Rotation',size=3,default=(False,False,False),options=set(),update=_links_changed)
    link_scale:bpy.props.BoolVectorProperty(name='Link Scale',size=3,default=(False,False,False),options=set(),update=_links_changed)
    link_dimensions:bpy.props.BoolVectorProperty(name='Link Dimensions',size=3,default=(False,False,False),options=set(),update=_links_changed)
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
    show_diagnostic_details:bpy.props.BoolProperty(default=False,options=set())
    show_solver:bpy.props.BoolProperty(name='Solver Settings',default=False,options=set())
    alignment_type:bpy.props.EnumProperty(name='Alignment',items=[('POSITION','Position','Align object origins'),('ORIENTATION','Orientation','Align selected object rotations, preserving positions')],options=set(),update=_arrange_changed)
    orientation_action:bpy.props.EnumProperty(name='Mode',items=[('MATCH','Match Reference','Match the full reference orientation'),('SET','Set Rotation','Set selected Euler components relative to the reference')],options=set(),update=_arrange_changed)
    orientation_axes:bpy.props.BoolVectorProperty(name='Rotation Components',size=3,default=(True,True,True),options=set(),update=_arrange_changed)
    orientation_angles:bpy.props.FloatVectorProperty(name='Rotation',size=3,subtype='EULER',unit='ROTATION',options=set(),update=_arrange_changed)
    orientation_order:bpy.props.EnumProperty(name='Euler Order',items=[(order,order+' Euler','Order used to read and set reference-space components') for order in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX')],options=set(),update=_arrange_changed)
    distribution_mode:bpy.props.EnumProperty(name='Distribute',items=[('ORIGINS','Origins','Signed origin intervals, preserving existing behavior'),('GEOMETRY','Geometry Bounds','Physical gaps between extreme evaluated vertices projected on reference axes')],options=set(),update=_arrange_changed)
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
        ('VIEWPORT','Viewport','Use the viewport transform orientation')]+references.STORED_AXIS_EXTENSIONS,default='GLOBAL',options=set(),update=_arrange_changed)
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
    minimum_distance_mm:bpy.props.FloatProperty(name='Minimum Separation (mm)',default=.00001,min=.00000001,
        precision=8,description='Minimum distinguishable starting origin separation. Also the minimum interval in Origins mode; Geometry Gap may be zero',options=set(),update=_arrange_changed)
    axes:bpy.props.BoolVectorProperty(name='Move Axes',description='Reference axes used by Position alignment and Distribution',size=3,default=(True,False,False),options=set(),update=_arrange_changed)
    spacing:bpy.props.FloatProperty(name='Spacing',unit='LENGTH',default=.1,precision=5,
        description='Sign selects direction on each move axis. Origins: coordinate interval. Geometry Bounds: physical gap between boundaries; zero packs touching bounds towards positive axes',options=set(),update=_arrange_changed)


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
        except (BetterItemError,RuntimeError,ValueError,TypeError) as exc:
            return _arrangement_failed(self,context,exc)
        arrange.clear_error()
        self.report({'INFO'},'%s object(s) aligned.' % count)
        return {'FINISHED'}


class BETTERITEM_OT_distribute(bpy.types.Operator):
    bl_idname='better_item.distribute'
    bl_label='Distribute Objects'
    bl_description='Distribute origins or evaluated projected geometry bounds using the selected reference'
    bl_options={'REGISTER','UNDO'}
    axes:bpy.props.BoolVectorProperty(name='Axes',size=3,default=(True,False,False))
    reference:bpy.props.EnumProperty(name='Operation',items=[('AUTO','Reference','Use the selected Location')]+_references,default='AUTO',options={'HIDDEN'})
    spacing:bpy.props.FloatProperty(name='Spacing',unit='LENGTH',default=.1)
    minimum_mm:bpy.props.FloatProperty(name='Minimum Distance (mm)',default=.00001,min=.00000001,precision=8)
    distribution_mode:bpy.props.EnumProperty(items=[('ORIGINS','Origins',''),('GEOMETRY','Geometry Bounds','')],default='ORIGINS')
    show_solver:bpy.props.BoolProperty(name='Solver Settings',default=False,options={'SKIP_SAVE'})
    @classmethod
    def poll(cls,context):return context.mode=='OBJECT' and len(context.selected_objects)>=1
    def invoke(self,context,event):
        settings=context.scene.better_item
        self.axes=settings.axes
        self.reference='AUTO'
        self.spacing=settings.spacing
        self.minimum_mm=settings.minimum_distance_mm
        self.distribution_mode=settings.distribution_mode
        return self.execute(context)
    def draw(self,context):
        layout=self.layout
        row=layout.row(align=True);row.label(text='Move')
        for i,axis in enumerate('XYZ'):row.prop(self,'axes',index=i,text=axis,toggle=True)
        layout.prop(self,'distribution_mode',expand=True)
        layout.prop(self,'spacing')
        layout.prop(self,'show_solver',emboss=False,icon='TRIA_DOWN' if self.show_solver else 'TRIA_RIGHT')
        if self.show_solver:layout.prop(self,'minimum_mm')
    def execute(self,context):
        try:
            objects,origins=engine.selection_origins(context)
            if self.distribution_mode=='GEOMETRY':
                targets,verify=geometry_arrange.plan(context,objects,origins,self.axes,self.reference,spacing=self.spacing,
                    minimum_mm=self.minimum_mm)
            else:
                targets=arrange.plan(context,objects,origins,self.axes,self.reference,spacing=self.spacing,minimum_mm=self.minimum_mm)
                verify=arrange.distribution_verifier(context,self.axes,self.reference,self.minimum_mm)
            count=engine.apply_world_positions(objects,targets,verify=verify)
        except (BetterItemError,RuntimeError,ValueError,TypeError) as exc:
            return _arrangement_failed(self,context,exc)
        arrange.clear_error()
        self.report({'INFO'},'%s object(s) distributed.' % count)
        return {'FINISHED'}


class BETTERITEM_OT_align_orientation(bpy.types.Operator):
    bl_idname='better_item.align_orientation'
    bl_label='Align Orientation'
    bl_description='Align selected rotations relative to the reference, preserving each world origin and native Scale'
    bl_options={'REGISTER','UNDO'}
    mode:bpy.props.EnumProperty(name='Mode',items=[('MATCH','Match Reference',''),('SET','Set Rotation','')],default='MATCH')
    axes:bpy.props.BoolVectorProperty(name='Components',size=3,default=(True,True,True))
    angles:bpy.props.FloatVectorProperty(name='Rotation',size=3,unit='ROTATION',subtype='EULER')
    order:bpy.props.EnumProperty(name='Euler Order',items=[(order,order+' Euler','') for order in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX')])
    @classmethod
    def poll(cls,context):return context.mode=='OBJECT' and bool(context.selected_objects)
    def invoke(self,context,event):
        settings=context.scene.better_item
        self.mode=settings.orientation_action;self.axes=settings.orientation_axes
        self.angles=settings.orientation_angles;self.order=settings.orientation_order
        return self.execute(context)
    def execute(self,context):
        settings=context.scene.better_item
        for field,source in (('mode','orientation_action'),('axes','orientation_axes'),('angles','orientation_angles'),('order','orientation_order')):
            if not self.properties.is_property_set(field):setattr(self,field,getattr(settings,source))
        try:
            count=arrange.align_orientations(context,list(context.selected_objects),mode=self.mode,
                axes=self.axes,angles=self.angles,order=self.order)
        except (BetterItemError,RuntimeError,ValueError,TypeError) as exc:
            return _arrangement_failed(self,context,exc)
        arrange.clear_error();self.report({'INFO'},'%s object(s) oriented.'%count);return {'FINISHED'}
    def draw(self,context):
        self.layout.prop(self,'mode')
        if self.mode=='SET':
            self.layout.prop(self,'order',text='')
            for i,axis in enumerate('XYZ'):
                row=self.layout.row(align=True);row.prop(self,'axes',index=i,text=axis,toggle=True)
                field=row.row();field.enabled=self.axes[i];field.prop(self,'angles',index=i,text='')


def _linked_rows(layout,obj,group,label,prefix,lock_name=None):
    settings=obj.better_item
    links=getattr(settings,engine.GROUP_LINK[group])
    row=layout.row(align=True)
    row.label(text=label+':')
    if group=='DIMENSIONS' and not transform_view.has_surface_geometry(obj):
        row.label(text='Unavailable')
        return
    try:transform_view.values(bpy.context,obj,group)
    except BetterItemError:
        row.label(text='Unavailable',icon='INFO')
        return
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
        layout.row(align=True).prop(settings,'transform_space',expand=True)
        if settings.transform_space=='REFERENCE':
            _draw_reference(layout,settings)
            layout.prop(settings,'use_reference_pivot')
        error=_field_errors.get(obj.as_pointer())
        configuration_error=False
        try:
            if settings.transform_space=='REFERENCE':
                frames.object_axes(context,obj)
                frames.object_origin(context,obj)
        except BetterItemError as exc:error=exc;configuration_error=True
        if error:
            diagnostics.draw(layout,error,settings,clear_operator='better_item.clear_error',configuration=configuration_error)
        _linked_rows(layout,obj,'LOCATION','Location','location','lock_location')
        if settings.transform_space=='DEFAULT' and obj.rotation_mode in {'QUATERNION','AXIS_ANGLE'}:
            layout.label(text='Rotation:')
            layout.prop(obj,'rotation_quaternion' if obj.rotation_mode=='QUATERNION' else 'rotation_axis_angle',text='')
        else:_linked_rows(layout,obj,'ROTATION','Rotation','rotation','lock_rotation')
        layout.prop(obj if settings.transform_space=='DEFAULT' else settings,'rotation_mode' if settings.transform_space=='DEFAULT' else 'view_rotation_order',text='')
        _linked_rows(layout,obj,'SCALE','Scale (Default)' if settings.transform_space=='REFERENCE' else 'Scale','scale','lock_scale')
        _linked_rows(layout,obj,'DIMENSIONS','Dimensions','dimensions')
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
        _draw_reference(layout,settings,arrangement=True)
        axes_error=origin_error=None
        resolved_axes=None
        try:resolved_axes=references.axes(context,settings,context.active_object,True)
        except BetterItemError as exc:axes_error=exc
        try:references.origin(context,settings,context.active_object,True)
        except BetterItemError as exc:origin_error=exc
        reference_error=axes_error or origin_error
        if reference_error:diagnostics.draw(layout,reference_error,settings,configuration=True)
        message=arrange.error(context.scene)
        if message:diagnostics.draw(layout,message,settings,clear_operator='better_item.clear_arrange_error')
        try:bounds=arrange.operation_reference(context)=='SELECTION'
        except BetterItemError:bounds=False
        row=layout.row(align=True)
        row.label(text='Move')
        for i,axis in enumerate('XYZ'):row.prop(settings,'axes',index=i,text=axis,toggle=True)
        if not any(settings.axes):layout.label(text='Choose axes for position operations.',icon='INFO')
        if not context.selected_objects:layout.label(text='Select objects to arrange.',icon='INFO')
        box=layout.box()
        box.label(text='Alignment')
        box.row(align=True).prop(settings,'alignment_type',expand=True)
        if settings.alignment_type=='ORIENTATION':
            if resolved_axes is not None:
                normalized=resolved_axes.normalized();gram=normalized.transposed()@normalized
                if normalized.determinant()<0 or max(abs(gram[i][j]-(1 if i==j else 0)) for i in range(3) for j in range(3))>1e-5:
                    box.label(text='Reflected reference axes.' if normalized.determinant()<0 else 'Non-orthogonal reference.',icon='INFO')
                    box.label(text='Uses its rotational component.')
            box.prop(settings,'orientation_action',text='Mode')
            if settings.orientation_action=='SET':
                box.prop(settings,'orientation_order',text='')
                for i,axis in enumerate('XYZ'):
                    row=box.row(align=True)
                    row.prop(settings,'orientation_axes',index=i,text=axis,toggle=True)
                    field=row.row(align=True);field.enabled=settings.orientation_axes[i]
                    field.prop(settings,'orientation_angles',index=i,text='')
            box.label(text='Selected positions stay fixed.')
            row=box.row();row.enabled=axes_error is None and bool(context.selected_objects)
            row.operator('better_item.align_orientation',text='Align Orientation' if settings.orientation_action=='MATCH' else 'Set Rotation')
        else:
            if bounds:box.label(text='Range: selected object origins')
            row=box.row(align=True);row.enabled=reference_error is None and any(settings.axes) and bool(context.selected_objects)
            if not bounds:row.operator('better_item.align',text='Align to Reference').mode='CENTER'
            else:
                for mode,label in (('MIN','Min'),('CENTER','Center'),('MAX','Max')):
                    row.operator('better_item.align',text=label).mode=mode
        box=layout.box()
        box.label(text='Distribution')
        box.row(align=True).prop(settings,'distribution_mode',expand=True)
        if settings.distribution_mode=='GEOMETRY':
            box.prop(settings,'spacing')
            box.label(text='Sign sets direction; zero is valid.')
            if bounds:box.label(text='Pack from selection boundary.')
        elif not bounds:
            box.prop(settings,'spacing')
            box.label(text='Spacing sign sets the direction.')
        else:
            box.label(text='Fixed extremes; equal intervals.')
        if not bounds:
            row=box.row()
            row.enabled=sum(settings.axes)==1
            row.prop(settings,'arrange_on_axis')
        row=box.row();row.enabled=reference_error is None and any(settings.axes) and bool(context.selected_objects)
        row.operator('better_item.distribute',text='Distribute')
        row=layout.row(align=True)
        row.prop(settings,'show_solver',text='Solver Settings',emboss=False,icon='TRIA_DOWN' if settings.show_solver else 'TRIA_RIGHT')
        if settings.show_solver:
            solver=layout.box();solver.prop(settings,'minimum_distance_mm',text='Minimum (mm)')
            solver.label(text='Used to distinguish starting order.')


@persistent
def _clear_runtime(_unused):
    _field_errors.clear()
    transform_view.clear_cache()
    arrange.clear_error()
    native_refs.clear_cache()
    frames.migrate()


classes=(frames.BetterItemFrame,trace.BetterItemTrace,BetterItemObjectSettings,BetterItemSceneSettings,BETTERITEM_OT_link_group,
         BETTERITEM_OT_clear_error,BETTERITEM_OT_clear_arrange_error,BETTERITEM_OT_align,BETTERITEM_OT_distribute,BETTERITEM_OT_align_orientation,
         BETTERITEM_PT_transform,BETTERITEM_PT_alignment)+frames.classes+(native_refs.BETTERITEM_OT_native_frame,)


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
        # Measurement invalidation only: never writes a transform or animation.
        # Frame changes can update indirect geometry without geometry flags in
        # depsgraph_update_post (e.g. an animated Object Info source in GN).
        if transform_view.clear_cache not in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.append(transform_view.clear_cache)
        frames.migrate()
        if not bpy.app.timers.is_registered(native_refs.sync):bpy.app.timers.register(native_refs.sync,first_interval=.2,persistent=True)
    except Exception:
        unregister()
        raise


def unregister():
    if transform_view.clear_cache in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(transform_view.clear_cache)
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
