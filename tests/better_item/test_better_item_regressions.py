import sys,math,itertools
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Euler,Vector
addon_utils.enable('better_item',default_set=True)
from better_item import engine,frames,orientation,transform_view,math_core
from better_item.math_core import BetterItemError
ctx=bpy.context
def near(a,b,tol=3e-5):assert np.allclose(a,b,rtol=0,atol=tol),(a,b)
def select(objects,active):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    ctx.view_layer.objects.active=active
def empty(name):
    obj=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(obj);return obj
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
obj=empty('Linked rotation')
select([obj],obj)
obj.better_item.link_rotation=(True,True,True)
for end in (10,20,80,-20,0):
    obj.rotation_euler=(0,0,math.radians(40));ctx.view_layer.update()
    obj.better_item.rotation_z=math.radians(end)
    near(obj.rotation_euler,(0,0,math.radians(end)))
near(math_core.linked_values((0,math.pi,4*math.pi),0,math.pi/2,(True,True,True),True),(math.pi/2,math.pi/4,math.pi))
near(math_core.linked_values((1,2,3),0,0,(True,True,True),True),(0,0,0))
# All mirrored sign combinations, each parent/reference arrangement and storage.
parent=empty('Parent');parent.rotation_euler=(.1,.2,.3);parent.scale=(2,2,2)
ref=empty('Reference');ref.rotation_euler=(.2,.1,-.3)
cases=0
for has_parent,has_ref,storage,signs in itertools.product((False,True),(False,True),('XYZ','ZYX','QUATERNION','AXIS_ANGLE'),list(itertools.product((-1,1),repeat=3))):
    obj.parent=parent if has_parent else None;obj.matrix_parent_inverse=Matrix.Identity(4)
    obj.rotation_mode=storage;obj.scale=signs;obj.delta_scale=(1,1,1)
    obj.delta_rotation_euler=(0,0,0);obj.delta_rotation_quaternion=(1,0,0,0)
    initial=Euler((.2,.3,.4),'XYZ').to_quaternion()
    if storage=='QUATERNION':obj.rotation_quaternion=initial
    elif storage=='AXIS_ANGLE':
        axis,angle=initial.to_axis_angle();obj.rotation_axis_angle=(angle,*axis)
    else:obj.rotation_euler=initial.to_euler(storage)
    obj.location=(1,2,3);obj.delta_location=(.2,5,-.1)
    s=obj.better_item;s.link_rotation=(False,False,False);s.orientation='REFERENCE' if has_ref else 'GLOBAL';s.orientation_object=ref
    s.view_rotation_order='XYZ';s.pivot_mode='GLOBAL';s.reference_mode='INDIVIDUAL';s.use_reference_pivot=False
    ctx.view_layer.update();position=obj.matrix_world.translation.copy()
    before=frames.relative_values(ctx,obj,'ROTATION')
    expected=list(before);expected[2]+=.15
    transform_view.set_rotation(ctx,obj,expected)
    assert tuple(obj.scale)==signs,(cases,tuple(obj.scale),signs)
    near(frames.relative_values(ctx,obj,'ROTATION'),expected)
    near(obj.matrix_world.translation,position)
    cases+=1
# Parent inverse from Keep Transform (including a mirrored parent) must work.
for parent_scale in ((2,2,2),(-2,2,2),(2,3,4)):
    parent.scale=parent_scale;ctx.view_layer.update()
    obj.parent=parent;obj.matrix_parent_inverse=parent.matrix_world.inverted()
    obj.scale=(-1,1,1);obj.rotation_mode='XYZ';obj.rotation_euler=(.2,.3,.4)
    s.orientation='GLOBAL';ctx.view_layer.update()
    before=frames.relative_values(ctx,obj,'ROTATION')
    expected=(before[0],before[1],before[2]+.1)
    transform_view.set_rotation(ctx,obj,expected)
    near(frames.relative_values(ctx,obj,'ROTATION'),expected)
    assert tuple(obj.scale)==(-1,1,1)
parent.scale=(2,2,2);ctx.view_layer.update()
# A mirror alone is not a half-turn, through any Object/frame path.
obj.parent=empty('Identity parent');obj.rotation_mode='XYZ';obj.rotation_euler=(math.radians(20),0,0);obj.scale=(-1,1,1)
ctx.view_layer.update();s.orientation='GLOBAL';s.orientation_object=None
near(frames.relative_values(ctx,obj,'ROTATION'),obj.rotation_euler)
obj.rotation_euler=tuple(math.radians(v) for v in (10,20,30));ctx.view_layer.update()
expected=obj.rotation_euler.to_matrix()
near(orientation.basis(obj,'LOCAL'),expected)
near(orientation.basis(ref,'REFERENCE',obj),expected)
frame=frames.create(ctx,'Mirrored source',Vector(),Matrix.Identity(3),obj)
near(frames.frame_axes(frame),expected)
select([obj],obj)
assert bpy.ops.better_item.frame(action='OBJECT')=={'FINISHED'}
near(frames.frame_axes(ctx.scene.better_item.frames[-1]),expected)
assert orientation.basis(obj,'LOCAL').determinant()>.999
# Delta rotations and native storage stay intact, including all delta modes.
obj.parent=parent;obj.scale=(-1,1,1);obj.delta_scale=(2,.5,3)
obj.matrix_parent_inverse=Matrix.Identity(4)
for mode in ('XYZ','ZYX','QUATERNION','AXIS_ANGLE'):
    obj.rotation_mode=mode
    obj.delta_rotation_euler=(.2,.1,-.3)
    obj.delta_rotation_quaternion=Euler((-.1,.2,.3)).to_quaternion()
    ctx.view_layer.update()
    before=frames.relative_values(ctx,obj,'ROTATION');expected=(before[0]+.05,*before[1:])
    transform_view.set_rotation(ctx,obj,expected)
    near(frames.relative_values(ctx,obj,'ROTATION'),expected)
    assert tuple(obj.scale)==(-1,1,1)
    assert tuple(obj.delta_scale)==(2,.5,3)
# Rotated parent roundoff must not trip locked Y, or mutate it.
parent.rotation_euler=(0,0,math.radians(30));parent.scale=(2,2,2)
a=empty('A');b=empty('B')
a.parent=b.parent=parent;a.location=(1,2,3);b.location=(4,2,3);b.lock_location[1]=True
ctx.view_layer.update();start=b.location.y
target=parent.matrix_world@Vector((1,2,3))
engine.apply_world_positions([b],{b.name:tuple(target)})
assert b.location.y==start
near(b.matrix_world.translation,target)
before=b.location.copy()
try:engine.apply_world_positions([b],{b.name:tuple(parent.matrix_world@Vector((1,2.1,3)))})
except BetterItemError as exc:assert 'BI-T003' in str(exc)
else:raise AssertionError('A real locked-axis change must fail')
near(b.location,before)
# Unsupported Dimensions is a domain error and scalar getters never traceback.
types=[('Empty',None),('Camera',bpy.data.cameras.new('Camera')),('Light',bpy.data.lights.new('Light','POINT')),
    ('Armature',bpy.data.armatures.new('Armature')),('Lattice',bpy.data.lattices.new('Lattice')),
    ('Grease',bpy.data.grease_pencils.new('Grease'))]
for name,data in types:
    item=bpy.data.objects.new(name,data);ctx.scene.collection.objects.link(item)
    assert not transform_view.has_surface_geometry(item)
    for field in ('dimensions_x','dimensions_y','dimensions_z'):assert getattr(item.better_item,field)==0
    try:transform_view.dimensions(item,Matrix.Identity(3))
    except BetterItemError:pass
    else:raise AssertionError('Expected no-geometry domain error')
# Removing a frame clears every dependent enum number before the enum shrinks.
f=frames.create(ctx,'Remove me',Vector(),Matrix.Identity(3))
other=frames.create(ctx,'Dependent',Vector(),Matrix.Identity(3))
select([a],a);settings=ctx.scene.better_item
for name in ('reference_frame','orientation_frame','pivot_frame'):setattr(a.better_item,name,f.uid)
for name in ('arrange_reference_frame','arrange_frame','arrange_origin_frame'):setattr(settings,name,f.uid)
other.position_frame=other.rotation_frame=f.uid
settings.active_frame=next(i for i,item in enumerate(settings.frames) if item.uid==f.uid)
bpy.ops.better_item.frame(action='REMOVE')
for name in ('reference_frame','orientation_frame','pivot_frame'):assert getattr(a.better_item,name)=='NONE'
for name in ('arrange_reference_frame','arrange_frame','arrange_origin_frame'):assert getattr(settings,name)=='NONE'
assert other.position_frame==other.rotation_frame=='NONE'
# A collapsed own Scale does not prevent a native rotation.
a.parent=None;a.scale=(0,1,1);ctx.view_layer.update()
transform_view.set_rotation(ctx,a,(.2,.3,.4))
near(a.rotation_euler,(.2,.3,.4));assert tuple(a.scale)==(0,1,1)
print('REPORTED REGRESSIONS PASSED: linked zero/crossing, %d signed-scale rotations, source consistency, delta transforms, parent locks, unsupported geometry and removed enums'%cases)



