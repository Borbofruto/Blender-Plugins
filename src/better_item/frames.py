# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-owned reference frames; object pointers are sources, never constraints."""
import uuid
import bpy
from mathutils import Matrix, Vector, Euler
from .math_core import BetterItemError,vector3

_enum_cache = {}


def frame_items(self, context):
    scene = context.scene if context else None
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


def frame_origin(frame):
    if frame.link_position:
        if frame.source is None:raise BetterItemError('Frame "%s" has no Location source. Choose a source object.'%frame.name)
        return frame.source.matrix_world.translation.copy()
    return Vector(frame.position)


def frame_axes(frame):
    if frame.link_rotation:
        if frame.source is None:raise BetterItemError('Frame "%s" has no Orientation source. Choose a source object.'%frame.name)
        return frame.source.matrix_world.to_quaternion().normalized().to_matrix()
    return Euler(frame.rotation,'XYZ').to_matrix()


def resolve(frame):
    return frame_origin(frame),frame_axes(frame)


def viewport_axes(context, obj):
    slot = context.scene.transform_orientation_slots[0]
    kind = slot.type
    if slot.custom_orientation:
        return slot.custom_orientation.matrix.to_quaternion().normalized().to_matrix()
    if kind == 'GLOBAL':
        return Matrix.Identity(3)
    if kind in {'LOCAL', 'NORMAL'}:
        return obj.matrix_world.to_quaternion().normalized().to_matrix()
    if kind == 'PARENT':
        return obj.parent.matrix_world.to_quaternion().normalized().to_matrix() if obj.parent else Matrix.Identity(3)
    if kind == 'CURSOR':
        return context.scene.cursor.matrix.to_3x3()
    if kind == 'VIEW':
        region = context.region_data
        if region is None and context.space_data and context.space_data.type == 'VIEW_3D':
            region = context.space_data.region_3d
        if region:
            return region.view_rotation.to_matrix()
        raise BetterItemError('View orientation requires a 3D viewport.')
    raise BetterItemError('Cannot save %s as an orthogonal frame. Choose Global, Local, Cursor, View or a custom orientation.' % kind)


def object_axes(context, obj):
    from . import orientation
    settings = obj.better_item
    if settings.orientation == 'SAVED':
        return frame_axes(find(context.scene, settings.orientation_frame))
    if settings.orientation == 'VIEWPORT':
        return viewport_axes(context, obj)
    return orientation.basis(obj, settings.orientation, settings.orientation_object)


def viewport_origin(context,obj):
    mode=context.scene.tool_settings.transform_pivot_point
    if mode=='CURSOR':return context.scene.cursor.location.copy()
    if mode in {'ACTIVE_ELEMENT','INDIVIDUAL_ORIGINS'}:return obj.matrix_world.translation.copy()
    selected=list(context.selected_objects) or [obj]
    if mode=='MEDIAN_POINT':
        return sum((item.matrix_world.translation for item in selected),Vector())/len(selected)
    points=[]
    depsgraph=context.evaluated_depsgraph_get()
    for item in selected:
        evaluated=item.evaluated_get(depsgraph)
        if all(tuple(c)==(-1,-1,-1) for c in evaluated.bound_box):
            points.append(evaluated.matrix_world.translation.copy())
        else:points.extend(evaluated.matrix_world@Vector(c) for c in evaluated.bound_box)
    return Vector(tuple((min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)))


def object_origin(context, obj):
    settings = obj.better_item
    if settings.pivot_mode == 'GLOBAL':
        return Vector((0, 0, 0))
    if settings.pivot_mode == 'FRAME':
        return frame_origin(find(context.scene, settings.pivot_frame))
    if settings.pivot_mode == 'OBJECT':
        if settings.origin_object is None:raise BetterItemError('Choose an Origin Object.')
        return settings.origin_object.matrix_world.translation.copy()
    if settings.pivot_mode == 'CURSOR':return context.scene.cursor.location.copy()
    return viewport_origin(context, obj)


def relative_values(context, obj, kind):
    axes = object_axes(context, obj)
    if kind == 'POSITION':
        return tuple(axes.transposed() @ (obj.matrix_world.translation-object_origin(context, obj)))
    rotation = axes.transposed() @ obj.matrix_world.to_quaternion().normalized().to_matrix()
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


def set_position(context, obj, values):
    from . import engine
    context.view_layer.update()
    target=object_origin(context,obj)+object_axes(context,obj) @ Vector(values)
    return engine.apply_world_positions([obj],{obj.name:tuple(target)})


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
    frame.rotation = axes.to_euler('XYZ')
    frame.link_position = source is not None if follow_position is None else follow_position
    frame.link_rotation = source is not None if follow_rotation is None else follow_rotation
    frame.source = source
    settings.active_frame = len(settings.frames)-1
    return frame


def apply_reference(frame, component='ALL'):
    origin=axes=None
    if component=='ALL':origin,axes=resolve(frame)
    elif component=='POSITION':origin=frame_origin(frame)
    else:axes=frame_axes(frame)
    if component in {'ALL','POSITION'}:
        frame.position = origin
        frame.link_position = False
    if component in {'ALL','ROTATION'}:
        frame.rotation = axes.to_euler('XYZ')
        frame.link_rotation = False
    if not frame.link_position and not frame.link_rotation:
        frame.source = None


def _frame_component(kind, axis):
    attribute = 'position' if kind == 'POSITION' else 'rotation'
    def get(self):
        try:
            return frame_origin(self)[axis] if kind=='POSITION' else frame_axes(self).to_euler('XYZ')[axis]
        except BetterItemError:
            return getattr(self, attribute)[axis]
    def set_value(self, value):
        linked = self.link_position if kind == 'POSITION' else self.link_rotation
        if not linked:
            result = list(getattr(self, attribute))
            result[axis] = value
            setattr(self, attribute, result)
    args = dict(name='XYZ'[axis], get=get, set=set_value, options=set(), precision=5,
        unit='LENGTH' if kind == 'POSITION' else 'ROTATION')
    if kind == 'ROTATION': args['subtype'] = 'ANGLE'
    return bpy.props.FloatProperty(**args)


def _link_property(kind):
    key='follow_'+kind
    def get(self):return bool(self.get(key,False))
    def set_value(self,value):
        if self.get(key,False) and not value and self.source:
            if kind=='position':self.position=self.source.matrix_world.translation
            else:self.rotation=self.source.matrix_world.to_quaternion().to_euler('XYZ')
        self[key]=bool(value)
    return bpy.props.BoolProperty(name='Link '+('Location' if kind=='position' else 'Orientation'),
        get=get,set=set_value,options=set())


class BetterItemFrame(bpy.types.PropertyGroup):
    uid: bpy.props.StringProperty()
    number: bpy.props.IntProperty()
    position: bpy.props.FloatVectorProperty(size=3, subtype='TRANSLATION', unit='LENGTH', options=set())
    rotation: bpy.props.FloatVectorProperty(size=3, subtype='EULER', unit='ROTATION', options=set())
    source: bpy.props.PointerProperty(name='Source Object', type=bpy.types.Object)
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
    bl_description='Create a scene frame manually, copy an object, or follow an object'
    bl_options={'REGISTER','UNDO'}
    target:bpy.props.EnumProperty(items=[('NONE','Frame List',''),('AXES','Orientation',''),('ORIGIN','Origin',''),
        ('ALIGN_AXES','Arrangement Orientation',''),('ALIGN_ORIGIN','Arrangement Origin','')],
        default='NONE',options={'HIDDEN','SKIP_SAVE'})
    target_name:bpy.props.StringProperty(options={'HIDDEN','SKIP_SAVE'})
    frame_name:bpy.props.StringProperty(name='Name',default='Frame')
    creation_mode:bpy.props.EnumProperty(name='Type',items=[
        ('MANUAL','Manual','Enter world Location and Orientation'),
        ('OBJECT_STATIC','Object (Independent)','Copy the object transform without keeping a link'),
        ('OBJECT_LINKED','Object (Linked)','Follow the selected source object')],default='MANUAL')
    position:bpy.props.FloatVectorProperty(name='Location',size=3,unit='LENGTH',subtype='TRANSLATION')
    rotation:bpy.props.FloatVectorProperty(name='Rotation',size=3,unit='ROTATION',subtype='EULER')
    link_position:bpy.props.BoolProperty(name='Link Location',default=True)
    link_rotation:bpy.props.BoolProperty(name='Link Orientation',default=True)
    def invoke(self,context,event):
        self.target_name=context.active_object.name if context.active_object else ''
        context.scene.better_item.frame_create_source=context.active_object
        return context.window_manager.invoke_props_dialog(self,width=340)
    def draw(self,context):
        layout=self.layout
        layout.prop(self,'frame_name')
        layout.prop(self,'creation_mode')
        if self.creation_mode=='MANUAL':
            layout.column(align=True).prop(self,'position')
            layout.column(align=True).prop(self,'rotation')
        else:
            layout.prop(context.scene.better_item,'frame_create_source',text='Object')
            if self.creation_mode=='OBJECT_LINKED':
                layout.prop(self,'link_position')
                layout.prop(self,'link_rotation')
                if not self.link_position:layout.column(align=True).prop(self,'position')
                if not self.link_rotation:layout.column(align=True).prop(self,'rotation')
    def cancel(self,context):
        context.scene.better_item.frame_create_source=None
    def execute(self,context):
        settings=context.scene.better_item
        try:
            obj=context.scene.objects.get(self.target_name) if self.target_name else context.active_object
            if self.target in {'AXES','ORIGIN'} and (obj is None or not obj.is_editable):
                raise BetterItemError('Select an editable target object before creating a frame.')
            context.view_layer.update()
            source=None
            if self.creation_mode=='MANUAL':
                origin=Vector(vector3(self.position))
                axes=Euler(vector3(self.rotation),'XYZ').to_matrix()
            else:
                chosen=settings.frame_create_source
                if chosen is None:
                    raise BetterItemError('Choose an Object to create this frame.')
                origin=chosen.matrix_world.translation.copy()
                axes=chosen.matrix_world.to_quaternion().normalized().to_matrix()
                if self.creation_mode=='OBJECT_LINKED':
                    if not self.link_position:origin=Vector(vector3(self.position))
                    if not self.link_rotation:axes=Euler(vector3(self.rotation),'XYZ').to_matrix()
                if self.creation_mode=='OBJECT_LINKED' and (self.link_position or self.link_rotation):source=chosen
            frame=create(context,self.frame_name.strip() or 'Frame',origin,axes,source,
                follow_position=self.link_position if source is not None else False,
                follow_rotation=self.link_rotation if source is not None else False)
            if self.target=='AXES':
                obj.better_item.orientation='SAVED'
                obj.better_item.orientation_frame=frame.uid
            elif self.target=='ORIGIN':
                obj.better_item.pivot_mode='FRAME'
                obj.better_item.pivot_frame=frame.uid
            elif self.target=='ALIGN_AXES':
                settings.arrange_orientation='SAVED'
                settings.arrange_frame=frame.uid
            elif self.target=='ALIGN_ORIGIN':
                settings.arrange_origin='SAVED'
                settings.arrange_origin_frame=frame.uid
            settings.frame_create_source=None
        except BetterItemError as exc:
            settings.frame_create_source=None
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


class BETTERITEM_OT_frame(bpy.types.Operator):
    bl_idname = 'better_item.frame'
    bl_label = 'Better Item Reference Frame'
    bl_description = 'Create, apply or select a reference without parenting the target object'
    bl_options = {'REGISTER','UNDO'}
    action: bpy.props.EnumProperty(items=[(v,l,'') for v,l in (
        ('VIEWPORT','Create from Viewport'),('OBJECT','Create from Object (Applied)'),
        ('LINKED','Create Linked to Object'),('MANUAL','Create Manual'),
        ('APPLY','Apply Reference'),('APPLY_POSITION','Apply Location'),
        ('APPLY_ROTATION','Apply Orientation'),('REMOVE','Remove'),('USE','Use Orientation and Origin'))])
    def execute(self, context):
        settings = context.scene.better_item
        obj = context.active_object
        try:
            context.view_layer.update()
            if self.action in {'VIEWPORT','OBJECT','LINKED','MANUAL'}:
                if self.action != 'MANUAL' and obj is None:
                    raise BetterItemError('Select an object to capture a reference.')
                if self.action == 'MANUAL':
                    origin, axes, name = Vector(), Matrix.Identity(3), 'Reference'
                elif self.action == 'VIEWPORT':
                    origin, axes, name = viewport_origin(context,obj), viewport_axes(context,obj), 'Viewport Reference'
                else:
                    origin = obj.matrix_world.translation.copy()
                    axes = obj.matrix_world.to_quaternion().normalized().to_matrix()
                    name = obj.name + (' Linked' if self.action == 'LINKED' else ' Applied')
                create(context,name,origin,axes,obj if self.action == 'LINKED' else None)
                return {'FINISHED'}
            if not 0 <= settings.active_frame < len(settings.frames):
                raise BetterItemError('Select a saved reference frame.')
            frame = settings.frames[settings.active_frame]
            if self.action == 'REMOVE':
                settings.frames.remove(settings.active_frame)
                settings.active_frame = min(settings.active_frame,len(settings.frames)-1)
            elif self.action.startswith('APPLY'):
                apply_reference(frame,{'APPLY':'ALL','APPLY_POSITION':'POSITION','APPLY_ROTATION':'ROTATION'}[self.action])
            elif self.action == 'USE':
                if obj is None: raise BetterItemError('Select the target object.')
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
    bl_order=2
    def draw(self, context):
        layout=self.layout
        settings=context.scene.better_item
        layout.prop(settings,'show_frames')
        layout.operator('better_item.new_frame',text='New Frame',icon='ADD')
        layout.operator('better_item.frame',text='Create from Viewport').action='VIEWPORT'
        layout.template_list('BETTERITEM_UL_frames','',settings,'frames',settings,'active_frame',rows=3)
        if not 0 <= settings.active_frame < len(settings.frames): return
        frame=settings.frames[settings.active_frame]
        layout.prop(frame,'name',text='Name')
        layout.prop(frame,'source')
        try:
            resolve(frame)
        except BetterItemError:
            layout.label(text='Source missing: choose another object.',icon='ERROR')
        for kind,label,linked,action in (('position','Location','link_position','APPLY_POSITION'),
                ('rotation','Orientation','link_rotation','APPLY_ROTATION')):
            box=layout.box()
            box.label(text=label+' (World)')
            box.prop(frame,linked)
            column=box.column(align=True)
            column.enabled=not getattr(frame,linked)
            for axis in 'xyz':column.prop(frame,kind+'_'+axis,text=axis.upper())
            box.operator('better_item.frame',text='Apply '+label.lower()).action=action
        layout.operator('better_item.frame',text='Apply Reference').action='APPLY'
        layout.operator('better_item.frame',text='Use for Active Object').action='USE'
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
