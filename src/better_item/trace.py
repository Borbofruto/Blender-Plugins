# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only affine accounting; Euler angles are never added as offsets."""
import bpy
from mathutils import Vector
from . import engine,orientation
from .math_core import BetterItemError


def parent_label(obj):
    if obj is None or obj.parent is None:return 'No parent: using World / Global'
    return ('Nested hierarchy. Direct parent: ' if obj.parent.parent else 'Direct parent: ')+obj.parent.name


def draw_parent_label(layout,obj):
    import textwrap
    for line in textwrap.wrap(parent_label(obj),30):layout.label(text=line)


def values(obj):
    parent=engine._parent_matrix(obj)
    local=obj.matrix_basis.translation.copy()
    contribution=parent.to_3x3()@local
    origin=parent.translation.copy()
    world=obj.matrix_world.translation.copy()
    return dict(world=world,local=Vector(obj.location),delta=Vector(obj.delta_location),
        contribution=contribution,parent_origin=origin,residual=world-origin-contribution)


def _vector(key):
    def get(self):
        try:return tuple(values(self.id_data)[key])
        except BetterItemError:return (0,0,0)
    return bpy.props.FloatVectorProperty(size=3,unit='LENGTH',subtype='TRANSLATION',get=get,options=set(),precision=5)


def _world_rotation(self):
    try:return tuple(orientation.rotation(self.id_data).to_euler('XYZ'))
    except BetterItemError:return (0,0,0)


def _read_reference(context,obj,kind):
    from . import frames
    if obj.name not in context.scene.objects:
        raise BetterItemError('The object is not in the active scene.')
    return frames.object_origin(context,obj) if kind=='origin' else frames.relative_values(context,obj,'POSITION')


def _reference_vector(kind):
    def get(self):
        try:return tuple(_read_reference(bpy.context,self.id_data,kind))
        except (BetterItemError,AttributeError,RuntimeError):return (0,0,0)
    return bpy.props.FloatVectorProperty(size=3,unit='LENGTH',subtype='TRANSLATION',get=get,options=set(),precision=5)


def reference_paths(context,obj):
    from . import frames
    def object_path(source):
        if source is None:return 'Missing Object'
        names=[source.name];source=source.parent
        while source:names.append(source.name);source=source.parent
        return 'Object: '+' > '.join(names)
    def frame_path(frame,kind,seen=()):
        if frame.uid in seen:return 'Cycle: '+frame.name
        mode=frame.position_mode if kind=='Location' else frame.rotation_mode
        source=frame.position_source if kind=='Location' else frame.rotation_source
        prefix='Frame '+frame.name+' > '
        if mode=='FRAME':
            uid=frame.position_frame if kind=='Location' else frame.rotation_frame
            child=next((f for f in context.scene.better_item.frames if f.uid==uid),None)
            return prefix+(frame_path(child,kind,(*seen,frame.uid)) if child else 'Missing Frame')
        if mode=='OBJECT':return prefix+object_path(source)
        if mode=='PARENT':return prefix+object_path(source.parent) if source and source.parent else prefix+'World'
        if mode=='NATIVE':return prefix+'Native: '+frame.native_source
        if mode=='PIVOT':return prefix+'Pivot: '+frame.position_pivot
        return prefix+mode.title()
    s=obj.better_item;result=[]
    for kind in ('Location','Orientation'):
        if s.reference_mode=='FRAME':
            frame=next((f for f in context.scene.better_item.frames if f.uid==s.reference_frame),None)
            text=frame_path(frame,kind) if frame else 'Missing Frame'
        else:
            mode=s.pivot_mode if kind=='Location' else s.orientation
            uid=s.pivot_frame if kind=='Location' else s.orientation_frame
            if mode in {'FRAME','SAVED'}:
                frame=next((f for f in context.scene.better_item.frames if f.uid==uid),None)
                text=frame_path(frame,kind) if frame else 'Missing Frame'
            elif mode in {'OBJECT','REFERENCE'}:text=object_path(s.origin_object if kind=='Location' else s.orientation_object)
            elif mode=='PARENT':text=object_path(obj.parent) if obj.parent else 'World (no parent)'
            else:text=mode.title()
        result.append(kind+' reference: '+text)
    return result


class BetterItemTrace(bpy.types.PropertyGroup):
    expanded:bpy.props.BoolProperty(name='Transform Information',options=set())
    matrices:bpy.props.BoolProperty(name='Matrices',options=set())
    world:_vector('world')
    local:_vector('local')
    delta:_vector('delta')
    contribution:_vector('contribution')
    parent_origin:_vector('parent_origin')
    residual:_vector('residual')
    reference_origin:_reference_vector('origin')
    relative_location:_reference_vector('location')
    world_rotation:bpy.props.FloatVectorProperty(name='World Rotation',size=3,subtype='EULER',unit='ROTATION',
        get=_world_rotation,options=set())


def draw(layout,obj):
    settings=obj.better_item.trace
    box=layout.box()
    box.prop(settings,'expanded',text='Transform Information',icon='TRIA_DOWN' if settings.expanded else 'TRIA_RIGHT',emboss=False)
    if not settings.expanded:return
    draw_parent_label(box,obj)
    import textwrap
    for message in reference_paths(bpy.context,obj):
        for line in textwrap.wrap(message,30):box.label(text=line)
    try:values(obj)
    except BetterItemError as exc:
        box.label(text=str(exc),icon='ERROR');return
    for key,label in (('world','World Location'),('reference_origin','Reference Origin (World)'),('relative_location','Actual Reference Location'),('local','Default / Local Location'),('delta','Delta Location'),
            ('parent_origin','Parent / Inverse Origin (World)'),('contribution','Local + Delta Contribution (World)'),
            ('residual','Evaluation Residual (World)')):
        box.label(text=label)
        if key in {'reference_origin','relative_location'}:
            try:_read_reference(bpy.context,obj,'origin' if key=='reference_origin' else 'location')
            except (BetterItemError,AttributeError,RuntimeError) as exc:
                box.label(text='Unavailable',icon='INFO')
                for line in textwrap.wrap(str(exc),30):box.label(text=line)
                continue
        column=box.column(align=True);column.enabled=False;column.prop(settings,key,text='')
    box.label(text='World = parent/inverse origin')
    box.label(text='+ transformed local + residual')
    box.label(text='World Rotation (XYZ)')
    try:
        orientation.rotation(obj)
        column=box.column(align=True);column.enabled=False;column.prop(settings,'world_rotation',text='')
    except BetterItemError:box.label(text='Unavailable for this parent basis.')
    box.label(text='Default / Local Rotation')
    column=box.column(align=True);column.enabled=False
    column.prop(obj,{'QUATERNION':'rotation_quaternion','AXIS_ANGLE':'rotation_axis_angle'}.get(obj.rotation_mode,'rotation_euler'),text='')
    box.label(text='Parent Scale')
    if obj.parent:
        column=box.column(align=True);column.enabled=False;column.prop(obj.parent,'scale',text='')
    else:box.label(text='1, 1, 1')
    chain=[];parent=obj.parent
    while parent:chain.append(parent.name);parent=parent.parent
    if chain:box.label(text='Hierarchy: '+' > '.join(chain))
    box.prop(settings,'matrices',icon='TRIA_DOWN' if settings.matrices else 'TRIA_RIGHT',emboss=False)
    if settings.matrices:
        for name,matrix in (('World',obj.matrix_world),('Local Basis (incl. Delta)',obj.matrix_basis),
                ('Effective Parent',engine._parent_matrix(obj)),('Parent Inverse',obj.matrix_parent_inverse)):
            box.label(text=name)
            for row in matrix:box.label(text=' '.join('% .5g'%v for v in row))
