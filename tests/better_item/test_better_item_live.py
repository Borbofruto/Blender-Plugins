import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Vector,Euler,Matrix
addon_utils.enable('better_item',default_set=True)
import better_item as addon
from better_item import frames,transform_view
context=bpy.context

def near(a,b,tol=3e-5):assert all(abs(x-y)<tol for x,y in zip(a,b)),(tuple(a),tuple(b))
def fields(settings,prefix):return tuple(getattr(settings,prefix+'_'+axis) for axis in 'xyz')
def check(obj):assert obj.as_pointer() not in addon._field_errors,addon._field_errors.get(obj.as_pointer())
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=1)
obj=context.object
obj.name='Target'
s=obj.better_item
obj.dimensions=(.1,.2,.6)
context.view_layer.update()
s.link_dimensions=(True,True,True)
s.dimensions_x=.3
check(obj)
near(obj.dimensions,(.3,.6,1.8))
s.link_dimensions=(False,False,False)
bpy.ops.object.empty_add()
source=context.object
source.location=(10,20,30)
source.rotation_euler.z=math.pi/2
source.scale=(2,3,4)
context.view_layer.objects.active=obj
context.view_layer.update()
s.orientation='REFERENCE'
s.orientation_object=source
s.pivot_mode='OBJECT'
s.origin_object=source
obj.location=(10,22,30)
context.view_layer.update()
near(fields(s,'location'),(2,0,0))
for value in (3,4,5):
    s.location_x=value
    check(obj)
    near(obj.location,(10,20+value,30))
    near(fields(s,'location'),(value,0,0))
old_scale=tuple(obj.scale)
s.scale_x=999
assert tuple(obj.scale)==old_scale
assert 'read-only' in addon._field_errors[obj.as_pointer()]
obj.rotation_euler=source.rotation_euler
context.view_layer.update()
for degrees in (10,20,30):
    s.rotation_x=math.radians(degrees)
    check(obj)
    near(fields(s,'rotation'),(math.radians(degrees),0,0))
# Changing origin changes Location only; changing axes changes Rotation/Dimensions.
old_world=obj.matrix_world.copy()
old_rotation=fields(s,'rotation')
s.pivot_mode='GLOBAL'
near(fields(s,'rotation'),old_rotation)
near(obj.matrix_world.translation,old_world.translation)
s.orientation='GLOBAL'
near(obj.matrix_world.translation,old_world.translation)
# Readings follow the reference, but the target has no persistent relationship.
s.orientation='REFERENCE'
s.pivot_mode='OBJECT'
read_before=fields(s,'location')
source.location.x+=10
context.view_layer.update()
assert fields(s,'location')!=read_before
near(obj.matrix_world.translation,old_world.translation)
assert obj.parent is None and not obj.constraints
# Dimensions are extrema of evaluated vertices, not a projected local bbox.
mesh=bpy.data.meshes.new('Triangle')
mesh.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)])
triangle=bpy.data.objects.new('Triangle',mesh)
context.collection.objects.link(triangle)
source.rotation_euler=(0,0,math.pi/4)
triangle.better_item.orientation='REFERENCE'
triangle.better_item.orientation_object=source
context.view_layer.update()
near(fields(triangle.better_item,'dimensions'),(math.sqrt(.5),math.sqrt(2),0))
# Arbitrary oriented dimensions remain live and non-destructive.
obj.rotation_euler=(0,0,0)
obj.scale=(1,1,1)
s.pivot_mode='GLOBAL'
context.view_layer.update()
base_vertices=[tuple(v.co) for v in obj.data.vertices]
shared=bpy.data.objects.new('Shared mesh',obj.data)
context.collection.objects.link(shared)
before_dims=fields(s,'dimensions')
for width in (1.6,1.8,2.0):
    s.dimensions_x=width
    check(obj)
    near(fields(s,'dimensions'),(width,before_dims[1],before_dims[2]))
assert len(obj.modifiers)==1
assert obj.modifiers[0].type=='NODES'
assert [tuple(v.co) for v in obj.data.vertices]==base_vertices
near(shared.dimensions,(1,1,1))
# Changing the source after editing does not add a driver or move vertices again.
old_evaluated=transform_view.dimensions(obj,Matrix.Identity(3))
source.rotation_euler.z=.1
source.location=(0,0,0)
context.view_layer.update()
near(transform_view.dimensions(obj,Matrix.Identity(3)),old_evaluated)
assert not obj.animation_data and obj.parent is None and not obj.constraints
# Duplicated node groups are made single-user before further edits.
duplicate=obj.copy()
context.collection.objects.link(duplicate)
context.view_layer.update()
duplicate_before=transform_view.dimensions(duplicate,Matrix.Identity(3))
s.dimensions_x=2.2
check(obj)
near(transform_view.dimensions(duplicate,Matrix.Identity(3)),duplicate_before)
assert duplicate.modifiers[0].node_group!=obj.modifiers[0].node_group
# Global native Scale remains editable and updates the same Dimensions view.
s.orientation='GLOBAL'
s.pivot_mode='GLOBAL'
old_native=tuple(obj.scale)
s.scale_x=old_native[0]*1.2
check(obj)
assert abs(obj.scale.x-old_native[0]*1.2)<1e-5
# All Euler display orders represent the same reference-space orientation.
for order in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX'):
    s.view_rotation_order=order
    s.rotation_x=.2
    check(obj)
    assert abs(s.rotation_x-.2)<1e-4
# Zero angles keep the requested 360-degree ratio convention.
obj.rotation_euler=(0,0,0)
context.view_layer.update()
s.view_rotation_order='XYZ'
s.link_rotation=(True,True,True)
s.rotation_x=math.pi/2
check(obj)
near(fields(s,'rotation'),(math.pi/2,math.pi/2,math.pi/2),tol=2e-4)
print('LIVE TRANSFORM PASSED: immediate fields, reference switching, native Scale, true vertex extrema, non-destructive oblique Dimensions, shared data and all Euler orders')
# Real undo snapshots restore both modifier creation and shape-key data.
bpy.ops.mesh.primitive_cube_add(size=1)
undo_obj=context.object
undo_obj.name='LiveUndo'
undo_obj.shape_key_add(name='Basis')
undo_obj.shape_key_add(name='Shape')
u=undo_obj.better_item
u.orientation='REFERENCE'
u.orientation_object=source
context.view_layer.update()
undo_before=fields(u,'dimensions')
context.preferences.edit.use_global_undo=True
bpy.ops.ed.undo_push(message='Before live dimension drag')
u.dimensions_x=2
check(undo_obj)
assert len(undo_obj.modifiers)==1
assert len(undo_obj.data.shape_keys.key_blocks)==2
bpy.ops.ed.undo_push(message='After live dimension drag')
bpy.ops.ed.undo()
undo_obj=bpy.data.objects['LiveUndo']
assert len(undo_obj.modifiers)==0
near(fields(undo_obj.better_item,'dimensions'),undo_before)
bpy.ops.ed.redo()
undo_obj=bpy.data.objects['LiveUndo']
assert len(undo_obj.modifiers)==1
assert len(undo_obj.data.shape_keys.key_blocks)==2
assert abs(undo_obj.better_item.dimensions_x-2)<1e-4
print('LIVE DIMENSIONS UNDO/REDO AND SHAPE KEYS PASSED')
