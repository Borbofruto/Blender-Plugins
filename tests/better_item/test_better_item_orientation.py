import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Vector,Matrix
addon_utils.enable('better_item',default_set=True)
from better_item import orientation,engine
from better_item.math_core import BetterItemError

def near(a,b,tol=1e-5):assert all(abs(x-y)<tol for x,y in zip(a,b)),(tuple(a),tuple(b))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=1)
obj=bpy.context.object
obj.name='Target'
bpy.ops.object.empty_add()
ref=bpy.context.object
ref.name='Axes'
ref.location=(100,-200,500)
ref.rotation_euler.z=math.pi/2
ref.scale=(2,3,5)
bpy.context.view_layer.objects.active=obj
obj.select_set(True)
bpy.context.view_layer.update()
context=bpy.context
orientation.apply(context,obj,'MOVE',(2,0,0),'REFERENCE',ref)
near(obj.location,(0,2,0))
near(ref.location,(100,-200,500))
ref.location=(-1000,1200,-500)
context.view_layer.update()
orientation.apply(context,obj,'MOVE',(2,0,0),'REFERENCE',ref)
near(obj.location,(0,4,0))
obj.rotation_euler.z=math.pi/2
context.view_layer.update()
orientation.apply(context,obj,'MOVE',(2,0,0),'LOCAL')
near(obj.location,(0,6,0))
orientation.apply(context,obj,'MOVE',(2,0,0),'GLOBAL')
near(obj.location,(2,6,0))
obj.rotation_euler=(0,0,0)
context.view_layer.update()
orientation.apply(context,obj,'ROTATE',(math.pi/2,0,0),'REFERENCE',ref)
print('rotation result',obj.rotation_euler[:])
near(obj.matrix_world.to_3x3()@Vector((0,0,1)),(1,0,0))
near(obj.location,(2,6,0))
obj.rotation_euler=(0,0,0)
obj.scale=(1,1,1)
context.view_layer.update()
orientation.apply(context,obj,'SCALE',(2,1,1),'REFERENCE',ref)
print('scale result',obj.scale[:])
near(obj.dimensions,(1,2,1))
obj.scale=(1,1,1)
context.view_layer.update()
axes=orientation.basis(obj,'REFERENCE',ref)
print('before dimensions',orientation.dimensions(obj,axes))
orientation.apply(context,obj,'SCALE',(3,2,1),'REFERENCE',ref)
print('after dimensions',orientation.dimensions(obj,axes),obj.dimensions[:])
obj.scale=(1,1,1)
context.view_layer.update()
orientation.apply(context,obj,'DIMENSIONS',(3,2,1),'REFERENCE',ref)
near(orientation.dimensions(obj,orientation.basis(obj,'REFERENCE',ref)),(3,2,1))
near(obj.dimensions,(2,3,1))
settings=obj.better_item
settings.orientation='REFERENCE'
settings.orientation_object=ref
settings.link_scale=(True,True,False)
settings.factor_x=3
near((settings.factor_x,settings.factor_y,settings.factor_z),(3,3,1))
settings.link_rotation=(True,True,True)
settings.turn_x=math.pi/4
near((settings.turn_x,settings.turn_y,settings.turn_z),(math.pi/4,)*3)
settings.link_location=(False,False,False)
settings.move_x=1
before=obj.location.copy()
assert bpy.ops.better_item.oriented(kind='MOVE')=={'FINISHED'}
near(obj.location,before+Vector((0,1,0)))
near((settings.move_x,settings.move_y,settings.move_z),(0,0,0))
assert obj.select_get() and ref.select_get()
print('ORIENTATION TESTS PASSED')
# Reference is optional in other modes and required only in REFERENCE.
try:orientation.apply(context,obj,'MOVE',(1,0,0),'REFERENCE')
except BetterItemError:pass
else:raise AssertionError('Missing reference must fail')
# Locks reject the operation, preserving both selection and transforms.
obj.lock_scale[1]=True
snapshot=obj.matrix_world.copy()
try:orientation.apply(context,obj,'SCALE',(2,1,1),'REFERENCE',ref)
except BetterItemError:pass
else:raise AssertionError('Must reject locked scale')
near(obj.matrix_world.translation,snapshot.translation)
obj.lock_scale[1]=False
obj.lock_location[1]=True
before=obj.location.copy()
try:orientation.apply(context,obj,'MOVE',(1,0,0),'REFERENCE',ref)
except BetterItemError:pass
else:raise AssertionError('Must reject locked world movement')
near(obj.location,before)
obj.lock_location[1]=False
# Cursor pivot remains independent of the external orientation's position.
context.scene.tool_settings.transform_pivot_point='CURSOR'
context.scene.cursor.location=(0,0,0)
obj.location=(1,0,0)
obj.rotation_euler=(0,0,0)
obj.scale=(1,1,1)
context.view_layer.update()
orientation.apply(context,obj,'ROTATE',(0,0,math.pi/2),'REFERENCE',ref)
near(obj.location,(0,1,0))
assert context.scene.tool_settings.transform_pivot_point=='CURSOR'
context.scene.tool_settings.transform_pivot_point='MEDIAN_POINT'
# Non-uniform scaling in the object's own axes behaves like native S X X.
obj.rotation_euler=(.3,.5,.7)
obj.scale=(1,2,3)
context.view_layer.update()
orientation.apply(context,obj,'SCALE',(2,1,1),'LOCAL')
near(obj.scale,(2,2,3))
# Geometrically incompatible target dimensions fail without partial changes.
obj.rotation_euler=(0,0,math.pi/4)
obj.scale=(1,1,1)
context.view_layer.update()
old_scale=tuple(obj.scale)
try:orientation.apply(context,obj,'DIMENSIONS',(3,1,1),'GLOBAL')
except BetterItemError:near(obj.scale,old_scale)
else:raise AssertionError('Incompatible projected extents must not silently succeed')
# Parent transforms are handled by Blender's native operation.
bpy.ops.object.empty_add()
parent=context.object
parent.rotation_euler.z=.3
parent.scale=(2,2,2)
obj.parent=parent
obj.rotation_euler=(0,0,0)
obj.scale=(1,1,1)
context.view_layer.update()
old_location=obj.matrix_world.translation.copy()
orientation.apply(context,obj,'MOVE',(1,0,0),'REFERENCE',ref)
near(obj.matrix_world.translation,old_location+Vector((0,1,0)))
assert obj.parent==parent
# Axis sources and neutral delta inputs persist in blend files.
import tempfile
context.view_layer.objects.active=obj
obj.better_item.orientation='REFERENCE'
obj.better_item.orientation_object=ref
with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
    filepath=str(Path(tmp)/'oriented.blend')
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
    bpy.ops.wm.open_mainfile(filepath=filepath)
    restored=bpy.data.objects['Target']
    assert restored.better_item.orientation=='REFERENCE'
    assert restored.better_item.orientation_object.name=='Axes'
print('EXTENDED ORIENTATION PASSED: pivots, locks, native local scaling, dimension rollback, parents and persistence')

