# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-owned reference frames; object pointers are sources, never constraints."""
import uuid
import bpy
import numpy as np
from mathutils import Matrix, Vector, Euler
from .math_core import BetterItemError
from . import native_refs,references

_enum_cache = {}


def frame_items(self, context):
    owner=getattr(self,'id_data',None)
    scene=owner if isinstance(owner,bpy.types.Scene) else getattr(context,'scene',None)
    fallback=[('NONE', 'Choose a Frame', '', 0)]
    if scene is None or not hasattr(scene, 'better_item'):
        return fallback
    live_scenes={item.as_pointer() for item in bpy.data.scenes}
    for pointer in list(_enum_cache):
        if pointer not in live_scenes:del _enum_cache[pointer]
    pointer=scene.as_pointer()
    signature=tuple((frame.uid,frame.name,frame.number) for frame in scene.better_item.frames)
    cached=_enum_cache.get(pointer)
    if cached is None or cached[0]!=signature:
        items=fallback+[(frame.uid,frame.name,'Saved reference frame',frame.number) for frame in scene.better_item.frames]
        _enum_cache[pointer]=(signature,items)
    # Keep the current callback strings alive, with one generation per scene.
    return _enum_cache[pointer][1]


def find(scene, uid):
    for frame in scene.better_item.frames:
        if frame.uid == uid:
            return frame
    raise BetterItemError('Choose a reference frame that exists in this scene.')


def _enter(frame,component,stack):
    key=(frame.uid,component)
    if key in stack:
        raise BetterItemError('[BI-F001] Circular %s reference involving frame "%s".'%(component,frame.name))
    return (*stack,key)


def frame_origin(frame,context=None,stack=()):
    from . import native_refs
    context=context or bpy.context
    stack=_enter(frame,'Location',stack)
    mode=frame.position_mode
    if mode=='GLOBAL':return Vector()
    if mode=='PARENT':
        if frame.position_source is None:raise BetterItemError('[BI-F002] Choose a child object for the parent Location source.')
        return frame.position_source.parent.matrix_world.translation.copy() if frame.position_source.parent else Vector()
    if mode=='OBJECT':
        source=frame.position_source
        if source is None:raise BetterItemError('[BI-F002] Frame "%s": choose a Location Object.'%frame.name)
        return source.matrix_world.translation.copy()
    if mode=='PIVOT':
        if getattr(context,'scene',None)!=frame.id_data:raise BetterItemError('[BI-F004] Activate the frame scene to read its viewport pivot.')
        return native_refs.pivot(context,frame.position_pivot)
    if mode=='FRAME':return frame_origin(find(frame.id_data,frame.position_frame),context,stack)
    return Vector(frame.position)


def frame_axes(frame,context=None,stack=()):
    from . import native_refs
    context=context or bpy.context
    stack=_enter(frame,'Orientation',stack)
    mode=frame.rotation_mode
    if mode=='PARENT':
        if frame.rotation_source is None:raise BetterItemError('[BI-F002] Choose a child object for the parent Orientation source.')
        from .orientation import rotation
        return rotation(frame.rotation_source.parent) if frame.rotation_source.parent else Matrix.Identity(3)
    if mode=='OBJECT':
        source=frame.rotation_source
        if source is None:raise BetterItemError('[BI-F002] Frame "%s": choose an Orientation Object.'%frame.name)
        from .orientation import rotation
        return rotation(source)
    if mode=='NATIVE':
        if getattr(context,'scene',None)!=frame.id_data:raise BetterItemError('[BI-F004] Activate the frame scene to read its native orientation.')
        return native_refs.orientation(context,frame.native_source,stack=stack)
    if mode=='FRAME':return frame_axes(find(frame.id_data,frame.rotation_frame),context,stack)
    result=Euler(frame.rotation,'XYZ').to_matrix()
    if frame.has_manual_basis:
        result=result@Matrix(tuple(tuple(frame.manual_basis[i*3+j] for j in range(3)) for i in range(3)))
    return native_refs.checked(result)


def position_reference_object(frame,scene,seen=()):
    if frame.uid in seen:return None
    if frame.position_mode=='PARENT':return frame.position_source.parent if frame.position_source else None
    if frame.position_mode=='OBJECT':return frame.position_source
    if frame.position_mode=='FRAME':return position_reference_object(find(scene,frame.position_frame),scene,(*seen,frame.uid))
    return None


def resolve(frame,context=None):
    return frame_origin(frame,context),frame_axes(frame,context)


def viewport_axes(context,obj):
    from . import native_refs
    return native_refs.orientation(context,context.scene.transform_orientation_slots[0].type,obj)


def object_axes(context,obj):
    return references.axes(context,obj.better_item,obj)



def object_origin(context,obj):
    return references.origin(context,obj.better_item,obj)[0]


def relative_values(context, obj, kind):
    if kind == 'POSITION':
        return position_values(context,obj)[0]
    axes = object_axes(context, obj)
    from .native_refs import rotation_basis
    from .orientation import rotation as object_rotation
    rotation = rotation_basis(axes).transposed() @ object_rotation(obj)
    order=obj.better_item.view_rotation_order
    if obj.parent is None and obj.rotation_mode==order and all(abs(v)<1e-12 for v in obj.delta_rotation_euler):
        if max(abs(axes[i][j]-(1 if i==j else 0)) for i in range(3) for j in range(3))<1e-8:
            return tuple(obj.rotation_euler)
    hint=obj.better_item.get('view_rotation_hint')
    if hint is not None and obj.better_item.get('view_rotation_hint_order')==order:
        compatible=Euler(hint,order)
        expected=compatible.to_matrix()
        if max(abs(rotation[i][j]-expected[i][j]) for i in range(3) for j in range(3))<5e-7:
            return tuple(hint)
        return tuple(0. if abs(v)<1e-7 else v for v in rotation.to_euler(order,compatible))
    return tuple(0. if abs(v)<1e-7 else v for v in rotation.to_euler(order))


def _position_sample(context,obj):
    """Resolve coordinates in float64, retaining Blender's stored float32 inputs.

    The error budget bounds world evaluation and subtraction near a remote
    origin. It is not a fixed snap distance, nor a user-selected unit threshold.
    """
    from . import engine
    axes=np.asarray(object_axes(context,obj),dtype=np.float64)
    origin=np.asarray(object_origin(context,obj),dtype=np.float64)
    world=np.asarray(obj.matrix_world,dtype=np.float64)
    try:inverse=np.linalg.inv(axes)
    except np.linalg.LinAlgError as exc:
        raise BetterItemError('[BI-F005] Reference axes are singular.') from exc
    values=inverse @ (world[:3,3]-origin)
    origin_ulp=np.abs(np.spacing(origin.astype(np.float32))).astype(np.float64)/2
    world_error=engine._world_roundoff(obj,world[:3,3])+origin_ulp
    arithmetic=8*np.finfo(np.float64).eps*(np.abs(world[:3,3])+np.abs(origin)+np.abs(axes) @ np.abs(values))
    uncertainty=np.abs(inverse) @ (world_error+arithmetic)
    signature=tuple(world.ravel())+tuple(axes.ravel())+tuple(origin)+tuple(obj.location)+tuple(obj.delta_location)
    return values,uncertainty,signature


def position_values(context,obj):
    values,uncertainty,signature=_position_sample(context,obj)
    settings=obj.better_item
    # Only an explicitly requested and verified zero gets an exact zero readout.
    # Moving either the target or its resolved reference invalidates this hint.
    if tuple(settings.get('view_location_zero_signature',()))==signature:
        mask=settings.get('view_location_zero_mask',())
        for axis,zero in enumerate(mask):
            if axis<3 and zero and abs(values[axis])<=uncertainty[axis]:values[axis]=0.
    return tuple(values),tuple(uncertainty)


def set_position(context, obj, values):
    from . import engine
    context.view_layer.update()
    # Avoid rounding the reference-to-world conversion before the native solve.
    target=np.asarray(object_origin(context,obj),dtype=np.float64)+np.asarray(object_axes(context,obj),dtype=np.float64) @ np.asarray(values,dtype=np.float64)
    sample=[]
    result=engine.apply_world_positions([obj],{obj.name:tuple(target)},
        verify=lambda objects:sample.append(_position_sample(context,obj)))
    actual,uncertainty,signature=sample[0]
    obj.better_item['view_location_zero_signature']=signature
    obj.better_item['view_location_zero_mask']=[int(value==0 and abs(actual[i])<=uncertainty[i]) for i,value in enumerate(values)]
    return result


def create(context, name, origin, axes, source=None, *, follow_position=None,follow_rotation=None):
    settings = context.scene.better_item
    frame = settings.frames.add()
    frame.uid = uuid.uuid4().hex
    settings.frame_serial += 1
    frame.number = settings.frame_serial
    existing = {f.name for f in settings.frames if f.uid != frame.uid}
    candidate = name
    suffix = 1
    while candidate in existing:
        candidate = '%s.%03d' % (name, suffix)
        suffix += 1
    frame.name = candidate
    frame.position = origin
    store_axes(frame,axes)
    frame.link_position = source is not None if follow_position is None else follow_position
    frame.link_rotation = source is not None if follow_rotation is None else follow_rotation
    frame.position_source = source if frame.link_position else None
    frame.rotation_source = source if frame.link_rotation else None
    frame['source_schema']=2
    settings.active_frame = len(settings.frames)-1
    return frame


def store_axes(frame,axes):
    from .native_refs import rotation_basis
    orthogonal=rotation_basis(axes)
    frame.has_manual_basis=max(abs(axes[i][j]-orthogonal[i][j]) for i in range(3) for j in range(3))>1e-6
    if frame.has_manual_basis:
        frame.manual_basis=tuple(v for row in axes for v in row)
        frame.rotation=(0,0,0)
    else:frame.rotation=axes.to_euler('XYZ')


def apply_reference(frame,component='ALL'):
    """Apply only live frame components; never recover a missing source silently."""
    if component not in {'ALL','POSITION','ROTATION'}:
        raise BetterItemError('Choose a valid frame component to apply.')
    # Resolve both before writing either, so a missing source leaves it intact.
    origin=frame_origin(frame) if component in {'ALL','POSITION'} else None
    axes=frame_axes(frame) if component in {'ALL','ROTATION'} else None
    if origin is not None:
        frame.position=origin
        frame.position_mode='MANUAL'
        frame.position_source=None
    if axes is not None:
        store_axes(frame,axes)
        frame.rotation_mode='MANUAL'
        frame.rotation_source=None
    frame.source=None


def migrate():
    if not hasattr(bpy.data,'scenes'):return
    for scene in bpy.data.scenes:
        if not hasattr(scene,'better_item'):continue
        for frame in scene.better_item.frames:
            if frame.get('source_schema',0)>=2:continue
            if frame.get('follow_position',False):
                frame.position_source=frame.source
                frame.position_mode='OBJECT'
            if frame.get('follow_rotation',False):
                frame.rotation_source=frame.source
                frame.rotation_mode='OBJECT'
            frame.source=None
            frame['source_schema']=2
        clear_missing_choices(scene)
        references.migrate(scene)


def clear_missing_choices(scene,removed=None):
    """Reset RNA enum numbers without reading their invalid enum identifiers."""
    valid={0}|{frame.number for frame in scene.better_item.frames if frame.number!=removed}
    owners=[(scene.better_item,('arrange_reference_frame','arrange_frame','arrange_origin_frame'))]
    owners.extend((obj.better_item,('reference_frame','orientation_frame','pivot_frame')) for obj in scene.objects)
    owners.extend((frame,('position_frame','rotation_frame')) for frame in scene.better_item.frames)
    for owner,fields in owners:
        for field in fields:
            number=owner.get(field,0)
            if number not in valid:owner[field]=0


def _frame_component(kind, axis):
    attribute = 'position' if kind == 'POSITION' else 'rotation'
    def get(self):
        try:
            return frame_origin(self)[axis] if kind=='POSITION' else (self.rotation[axis] if self.rotation_mode=='MANUAL' else frame_axes(self).to_euler('XYZ')[axis])
        except (BetterItemError,AttributeError,RuntimeError):
            return getattr(self, attribute)[axis]
    def set_value(self, value):
        manual=getattr(self,'position_mode' if kind=='POSITION' else 'rotation_mode')=='MANUAL'
        if manual:
            result = list(getattr(self, attribute))
            result[axis] = value
            setattr(self, attribute, result)
    args = dict(name='XYZ'[axis], get=get, set=set_value, options=set(), precision=5,
        unit='LENGTH' if kind == 'POSITION' else 'ROTATION')
    if kind == 'ROTATION': args['subtype'] = 'ANGLE'
    return bpy.props.FloatProperty(**args)


def _link_property(kind):
    # Legacy scripting API; new files use independent source modes.
    field='position_mode' if kind=='position' else 'rotation_mode'
    def get(self):return getattr(self,field)=='OBJECT'
    def set_value(self,value):
        if not value and getattr(self,field)=='OBJECT':
            try:apply_reference(self,'POSITION' if kind=='position' else 'ROTATION')
            except BetterItemError:pass
        setattr(self,field,'OBJECT' if value else 'MANUAL')
    return bpy.props.BoolProperty(get=get,set=set_value,options=set())


class BetterItemFrame(bpy.types.PropertyGroup):
    uid: bpy.props.StringProperty()
    number: bpy.props.IntProperty()
    position: bpy.props.FloatVectorProperty(size=3, subtype='TRANSLATION', unit='LENGTH', options=set())
    rotation: bpy.props.FloatVectorProperty(size=3, subtype='EULER', unit='ROTATION', options=set())
    # Keep the old pointer solely to migrate existing .blend files.
    source: bpy.props.PointerProperty(type=bpy.types.Object)
    position_mode:bpy.props.EnumProperty(name='Source',items=[('MANUAL','Manual',''),('OBJECT','Object',''),('PIVOT','Pivot',''),('FRAME','Frame',''),('GLOBAL','World',''),('PARENT','Parent','')],options=set())
    rotation_mode:bpy.props.EnumProperty(name='Source',items=[('MANUAL','Manual',''),('OBJECT','Object',''),('NATIVE','Native',''),('FRAME','Frame',''),('PARENT','Parent','')],options=set())
    position_source:bpy.props.PointerProperty(name='Location Object',type=bpy.types.Object)
    rotation_source:bpy.props.PointerProperty(name='Orientation Object',type=bpy.types.Object)
    position_pivot:bpy.props.EnumProperty(name='Pivot',items=native_refs.PIVOTS,options=set())
    position_frame:bpy.props.EnumProperty(name='Location Frame',items=frame_items,options=set())
    rotation_frame:bpy.props.EnumProperty(name='Orientation Frame',items=frame_items,options=set())
    native_source:bpy.props.StringProperty(name='Native Orientation',default='GLOBAL')
    native_enabled:bpy.props.BoolProperty(default=False)
    native_name:bpy.props.StringProperty()
    native_suspended:bpy.props.BoolProperty(default=False)
    has_manual_basis:bpy.props.BoolProperty(default=False)
    manual_basis:bpy.props.FloatVectorProperty(size=9,default=(1,0,0,0,1,0,0,0,1))
    reference_location:references.choice_property('origin',frame=True)
    reference_orientation:references.choice_property('axes',frame=True)
    link_position: _link_property('position')
    link_rotation: _link_property('rotation')
    visible: bpy.props.BoolProperty(name='Show Axes', default=True, options=set())
    position_x: _frame_component('POSITION',0)
    position_y: _frame_component('POSITION',1)
    position_z: _frame_component('POSITION',2)
    rotation_x: _frame_component('ROTATION',0)
    rotation_y: _frame_component('ROTATION',1)
    rotation_z: _frame_component('ROTATION',2)


class BETTERITEM_OT_new_frame(bpy.types.Operator):
    bl_idname='better_item.new_frame'
    bl_label='New Frame'
    bl_description='Create a named frame; configure its independent sources in Reference Frames'
    bl_options={'REGISTER','UNDO'}
    target:bpy.props.EnumProperty(items=[('NONE','Frame List',''),('BOTH','Transform Frame',''),('ALIGN_BOTH','Arrangement Frame',''),('AXES','Orientation',''),('ORIGIN','Origin',''),
        ('ALIGN_AXES','Arrangement Orientation',''),('ALIGN_ORIGIN','Arrangement Origin','')],
        default='NONE',options={'HIDDEN','SKIP_SAVE'})
    target_name:bpy.props.StringProperty(options={'HIDDEN','SKIP_SAVE'})
    frame_name:bpy.props.StringProperty(name='Name',default='Frame')
    def invoke(self,context,event):
        self.target_name=context.active_object.name if context.active_object else ''
        if not self.properties.is_property_set('frame_name'):self.frame_name='Frame'
        return context.window_manager.invoke_props_dialog(self,width=300)
    def draw(self,context):self.layout.prop(self,'frame_name')
    def execute(self,context):
        settings=context.scene.better_item
        obj=context.scene.objects.get(self.target_name) if self.target_name else context.active_object
        if self.target in {'AXES','ORIGIN','BOTH'} and (obj is None or not obj.is_editable):
            self.report({'ERROR'},'Select an editable target object.')
            return {'CANCELLED'}
        frame=create(context,self.frame_name.strip() or 'Frame',Vector(),Matrix.Identity(3))
        if self.target=='AXES':
            obj.better_item.orientation='SAVED'
            obj.better_item.orientation_frame=frame.uid
        elif self.target=='ORIGIN':
            obj.better_item.pivot_mode='FRAME'
            obj.better_item.pivot_frame=frame.uid
        elif self.target=='BOTH':
            obj.better_item.reference_mode='FRAME'
            obj.better_item.reference_frame=frame.uid
        elif self.target=='ALIGN_AXES':
            settings.arrange_orientation='SAVED'
            settings.arrange_frame=frame.uid
        elif self.target=='ALIGN_ORIGIN':
            settings.arrange_origin='SAVED'
            settings.arrange_origin_frame=frame.uid
        elif self.target=='ALIGN_BOTH':
            settings.arrange_reference_mode='FRAME'
            settings.arrange_reference_frame=frame.uid
        return {'FINISHED'}


class BETTERITEM_OT_frame(bpy.types.Operator):
    bl_idname = 'better_item.frame'
    bl_label = 'Better Item Reference Frame'
    bl_description = 'Create, apply or select a reference without parenting the target object'
    bl_options = {'REGISTER','UNDO'}
    action: bpy.props.EnumProperty(items=[(v,l,'') for v,l in (
('OBJECT','Create from Object (Applied)'),
        ('LINKED','Create Linked to Object'),('MANUAL','Create Manual'),
        ('APPLY','Apply Reference'),('APPLY_POSITION','Apply Location'),
        ('APPLY_ROTATION','Apply Orientation'),('REMOVE','Remove'),('USE','Use Orientation and Origin'))])
    def execute(self, context):
        settings = context.scene.better_item
        obj = context.active_object
        try:
            context.view_layer.update()
            if self.action in {'OBJECT','LINKED','MANUAL'}:
                if self.action != 'MANUAL' and obj is None:
                    raise BetterItemError('Select an object to capture a reference.')
                if self.action == 'MANUAL':
                    origin, axes, name = Vector(), Matrix.Identity(3), 'Reference'
                else:
                    origin = obj.matrix_world.translation.copy()
                    from .orientation import rotation
                    axes = rotation(obj)
                    name = obj.name + (' Linked' if self.action == 'LINKED' else ' Applied')
                create(context,name,origin,axes,obj if self.action == 'LINKED' else None)
                return {'FINISHED'}
            if not 0 <= settings.active_frame < len(settings.frames):
                raise BetterItemError('Select a saved reference frame.')
            frame = settings.frames[settings.active_frame]
            if self.action == 'REMOVE':
                from .native_refs import remove_native
                remove_native(context,frame)
                clear_missing_choices(context.scene,frame.number)
                settings.frames.remove(settings.active_frame)
                settings.active_frame = min(settings.active_frame,len(settings.frames)-1)
            elif self.action.startswith('APPLY'):
                apply_reference(frame,{'APPLY':'ALL','APPLY_POSITION':'POSITION','APPLY_ROTATION':'ROTATION'}[self.action])
            elif self.action == 'USE':
                if obj is None: raise BetterItemError('Select the target object.')
                obj.better_item.reference_mode='FRAME'
                obj.better_item.reference_frame=frame.uid
                obj.better_item.orientation = 'SAVED'
                obj.better_item.orientation_frame = frame.uid
                obj.better_item.pivot_mode = 'FRAME'
                obj.better_item.pivot_frame = frame.uid
                obj.better_item.use_reference_pivot = True
        except BetterItemError as exc:
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


class BETTERITEM_UL_frames(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item,'name',text='',emboss=False,icon='EMPTY_AXIS')
        row.prop(item,'visible',text='',emboss=False,icon='HIDE_OFF' if item.visible else 'HIDE_ON')


class BETTERITEM_PT_frames(bpy.types.Panel):
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Better Item'
    bl_label='Reference Frames'
    bl_order=0
    def draw(self, context):
        layout=self.layout
        settings=context.scene.better_item
        layout.prop(settings,'show_frames')
        layout.operator('better_item.new_frame',text='New Frame',icon='ADD')
        layout.template_list('BETTERITEM_UL_frames','',settings,'frames',settings,'active_frame',rows=3)
        if not 0 <= settings.active_frame < len(settings.frames): return
        frame=settings.frames[settings.active_frame]
        layout.prop(frame,'name',text='Name')
        for kind,label,action in (('rotation','Orientation','APPLY_ROTATION'),('position','Location','APPLY_POSITION')):
            box=layout.box()
            box.label(text=label+' (World)')
            references.draw_component(box,frame,'origin' if kind=='position' else 'axes',frame=True)
            mode=getattr(frame,kind+'_mode')
            try:
                frame_origin(frame,context) if kind=='position' else frame_axes(frame,context)
            except BetterItemError as exc:
                import textwrap
                for line in textwrap.wrap(str(exc),34):box.label(text=line,icon='ERROR' if line.startswith('[BI-') else 'NONE')
            column=box.column(align=True)
            column.enabled=mode=='MANUAL'
            if kind=='rotation' and frame.has_manual_basis and mode=='MANUAL':box.label(text='Rotation offset on applied axes')
            for axis in 'xyz':column.prop(frame,kind+'_'+axis,text=axis.upper())
            if mode!='MANUAL':box.operator('better_item.frame',text='Apply '+label).action=action
        layout.operator('better_item.native_frame',text='Use Orientation in Viewport',icon='ORIENTATION_GLOBAL').action='PUBLISH'
        if frame.native_enabled:
            layout.label(text='Exported: '+frame.native_name)
            if frame.native_suspended:layout.label(text='Invalid source: orientation suspended.',icon='ERROR')
            layout.operator('better_item.native_frame',text='Remove Exported Orientation').action='REMOVE'
        layout.operator('better_item.frame',text='Use Frame for Active Object').action='USE'
        layout.operator('better_item.frame',text='Remove Frame',icon='X').action='REMOVE'


class BETTERITEM_GGT_frames(bpy.types.GizmoGroup):
    bl_idname='BETTERITEM_GGT_frames'
    bl_label='Better Item Reference Frames'
    bl_space_type='VIEW_3D'
    bl_region_type='WINDOW'
    bl_options={'3D','PERSISTENT'}
    @classmethod
    def poll(cls,context):
        return hasattr(context.scene,'better_item') and context.scene.better_item.show_frames
    def setup(self,context):
        self._arrows={}
    def draw_prepare(self,context):
        settings=context.scene.better_item
        uids={frame.uid for frame in settings.frames}
        for uid in list(self._arrows):
            if uid not in uids:
                for arrow in self._arrows.pop(uid):self.gizmos.remove(arrow)
        for index,frame in enumerate(settings.frames):
            if frame.uid not in self._arrows:
                arrows=[]
                for color in ((1,.15,.12),(.2,1,.2),(.2,.4,1)):
                    arrow=self.gizmos.new('GIZMO_GT_arrow_3d')
                    arrow.color=color
                    arrow.alpha=.8
                    arrow.hide_select=True
                    arrow.line_width=2
                    arrows.append(arrow)
                self._arrows[frame.uid]=arrows
            try:
                origin,axes=resolve(frame)
                valid=True
            except BetterItemError:
                valid=False
            for i,arrow in enumerate(self._arrows[frame.uid]):
                arrow.hide=not frame.visible or not valid
                if arrow.hide:continue
                arrow.scale_basis=.8 if index==settings.active_frame else .5
                matrix=(axes @ Vector((0,0,1)).rotation_difference(Vector(tuple(1 if j==i else 0 for j in range(3)))).to_matrix()).to_4x4()
                matrix.translation=origin
                arrow.matrix_basis=matrix


classes=(BETTERITEM_OT_new_frame,BETTERITEM_OT_frame,BETTERITEM_UL_frames,BETTERITEM_PT_frames,BETTERITEM_GGT_frames)
