import sys
import math
import tempfile
from pathlib import Path
import bpy
import addon_utils
from mathutils import Matrix,Vector

root=Path(__file__).resolve().parents[2]/"src"
sys.path.insert(0,str(root))
addon_utils.enable('better_item',default_set=True)
import better_item as addon
from better_item import engine
from better_item.math_core import BetterItemError,linked_values,align_positions,distribute_positions

def near(actual,expected):
    assert all(abs(a-b)<1e-5 for a,b in zip(actual,expected)),(tuple(actual),expected)

def fails(function,fragment=None):
    try:function()
    except BetterItemError as exc:
        if fragment:assert fragment in str(exc),str(exc)
    else:raise AssertionError('Expected rejection')

near(linked_values((100,200,600),0,300,(1,1,1)),(300,600,1800))
near(linked_values((100,200,600),0,300,(1,1,0)),(300,600,600))
near(linked_values((100,200,600),2,300,(1,1,0)),(100,200,300))
fails(lambda:linked_values((0,2,6),0,3,(1,1,1)),'= 0')
near(linked_values((-1,2,6),0,3,(1,1,1)),(3,-6,-18))
origins={'key':(-600,0,0),'opposite_far':(-800,20,3),'opposite_near':(-650,30,2),
         'forward_near':(-590,-10,1),'forward_far':(-500,-20,4)}
positive=distribute_positions(origins,(1,0,0),'KEY',30,'key')
assert positive['key'][0]==-600
assert [positive[n][0] for n in ('opposite_near','opposite_far','forward_near','forward_far')]==[-570,-540,-510,-480]
negative=distribute_positions(origins,(1,0,0),'KEY',-30,'key')
assert [negative[n][0] for n in ('forward_near','forward_far','opposite_near','opposite_far')]==[-630,-660,-690,-720]
multiple=distribute_positions(origins,(1,1,0),'KEY',30,'key')
assert [multiple[n][1] for n in ('forward_near','forward_far','opposite_far','opposite_near')]==[30,60,90,120]
for name in origins:assert multiple[name][2]==origins[name][2]
even=distribute_positions({'a':(-8,1,9),'b':(-5,6,3),'c':(1,2,4),'d':(7,9,0)},(1,1,0),'SELECTION')
assert [even[n][0] for n in ('a','b','c','d')]==[-8,-3,2,7]
near(align_positions(origins,(1,0,0),'SELECTION','MIN')['key'],(-800,0,0))
near(align_positions(origins,(1,0,0),'SELECTION','CENTER')['key'],(-650,0,0))
near(align_positions(origins,(1,0,0),'SELECTION','MAX')['key'],(-500,0,0))
fails(lambda:distribute_positions(origins,(0,0,0),'KEY',30,'key'),'Select')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1
bpy.context.scene.unit_settings.length_unit='MILLIMETERS'
bpy.ops.mesh.primitive_cube_add(size=1)
cube=bpy.context.object
cube.name='Dimensions'
cube.dimensions=(.1,.2,.6)
bpy.context.view_layer.update()
cube.better_item.link_dimensions=(True,True,True)
cube.better_item.dimensions_x=.3
near(cube.dimensions,(.3,.6,1.8))
assert cube.as_pointer() not in addon._field_errors
cube.better_item.link_scale=(True,True,False)
cube.better_item.scale_y=1.2
near(cube.scale,(.6,1.2,1.8))
cube.location=(1,2,6)
cube.better_item.link_location=(True,True,True)
cube.better_item.location_x=3
near(cube.location,(3,6,18))
cube.rotation_euler=(.1,.2,.6)
cube.better_item.link_rotation=(True,True,True)
cube.better_item.rotation_x=.3
near(cube.rotation_euler,(.3,.6,1.8))

# A zero Euler angle uses a full turn in proportional calculations only.
def degrees(values):return tuple(math.radians(v) for v in values)
cube.rotation_euler=(0,0,0)
cube.better_item.rotation_x=math.radians(90)
near(cube.rotation_euler,degrees((90,0,0)))
cube.better_item.rotation_x=0
near(cube.rotation_euler,degrees((0,0,0)))
cube.better_item.rotation_x=math.radians(-90)
near(cube.rotation_euler,degrees((-90,0,0)))
cube.better_item.rotation_x=0
near(cube.rotation_euler,degrees((0,0,0)))
cube.better_item.rotation_x=math.radians(90)
near(cube.rotation_euler,degrees((90,0,0)))
cube.rotation_euler=degrees((0,180,720))
cube.better_item.rotation_x=math.radians(90)
near(cube.rotation_euler,degrees((90,45,180)))
cube.rotation_euler=degrees((0,180,720))
cube.better_item.link_rotation=(True,True,False)
cube.better_item.rotation_x=math.radians(90)
near(cube.rotation_euler,degrees((90,45,720)))
cube.rotation_euler=(0,0,0)
cube.lock_rotation[1]=True
cube.better_item.rotation_x=math.radians(90)
near(cube.rotation_euler,(0,0,0))
assert cube.as_pointer() in addon._field_errors
cube.lock_rotation[1]=False
cube.better_item.rotation_x=math.radians(90)
assert cube.as_pointer() not in addon._field_errors

# Atomic rejection if a linked peer is locked.
cube.lock_location[1]=True
old=cube.location.copy()
cube.better_item.location_x=6
near(cube.location,old)
assert 'locked' in addon._field_errors[cube.as_pointer()]
cube.lock_location[1]=False
cube.location.x=0
cube.better_item.location_x=1
near(cube.location,(0,6,18))
assert '= 0' in addon._field_errors[cube.as_pointer()]
cube.better_item.link_location=(False,False,False)
cube.better_item.location_x=1
near(cube.location,(1,6,18))
assert cube.as_pointer() not in addon._field_errors

def empty(name,location):
    ob=bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(ob)
    ob.location=location
    return ob

def selected(objects,key):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=key
    bpy.context.view_layer.update()

key=empty('Key',(-.6,0,0))
opposite=empty('Opposite',(-.8,.2,0))
forward=empty('Forward',(-.59,-.1,0))
selected([key,opposite,forward],key)
assert bpy.ops.better_item.distribute(reference='KEY',axes=(True,False,False),spacing=.03)=={'FINISHED'}
near(key.matrix_world.translation,(-.6,0,0))
near(opposite.matrix_world.translation,(-.57,.2,0))
near(forward.matrix_world.translation,(-.54,-.1,0))
assert bpy.ops.better_item.align(reference='SELECTION',axes=(False,True,False),mode='MAX')=={'FINISHED'}
for ob in (key,opposite,forward):near(ob.matrix_world.translation.yyx,(.2,.2,ob.matrix_world.translation.x))

# Parent movement must not move the key away from its captured world origin.
parent=empty('Parent',(2,3,4))
child=empty('Child',(1,2,3))
child.parent=parent
child.matrix_parent_inverse=Matrix.Identity(4)
selected([parent,child],child)
anchor=child.matrix_world.translation.copy()
original_rotation=parent.rotation_euler.copy()
assert bpy.ops.better_item.align(reference='KEY',axes=(True,True,True),mode='CENTER')=={'FINISHED'}
near(parent.matrix_world.translation,anchor)
near(child.matrix_world.translation,anchor)
near(parent.rotation_euler,original_rotation)

# World X changes can require a local Y change under a rotated parent.
parent.rotation_euler.z=math.pi/2
parent.scale=(2,3,1)
bpy.context.view_layer.update()
before_world=child.matrix_world.translation.copy()
engine.apply_world_positions([child],{child.name:tuple(before_world+Vector((.5,0,0)))})
near(child.matrix_world.translation,before_world+Vector((.5,0,0)))
child.lock_location[1]=True
old_child=child.location.copy()
old_forward=forward.location.copy()
try:
    engine.apply_world_positions([forward,child],{
        forward.name:tuple(forward.matrix_world.translation+Vector((.4,0,0))),
        child.name:tuple(child.matrix_world.translation+Vector((.5,0,0)))})
except BetterItemError:pass
else:raise AssertionError('Local lock must cancel the entire transaction')
near(child.location,old_child)
near(forward.location,old_forward)
child.lock_location[1]=False

# Native dimension edits must keep mirror signs and reflect external changes.
selected([cube],cube)
cube.rotation_euler=(0,0,0)
cube.scale=(-.1,.2,.6)
bpy.context.view_layer.update()
cube.better_item.link_dimensions=(True,True,True)
cube.better_item.dimensions_x=.3
near(cube.dimensions,(.3,.6,1.8))
assert cube.scale.x<0
cube.location=(4,5,6)
bpy.context.view_layer.update()
near((cube.better_item.location_x,cube.better_item.location_y,cube.better_item.location_z),(4,5,6))

# Registration is reversible and leaves no handlers/classes behind.
for i in range(2):
    addon.unregister()
    assert not hasattr(bpy.types.Object,'better_item')
    assert not hasattr(bpy.types.Scene,'better_item')
    assert addon._clear_runtime not in bpy.app.handlers.load_post
    addon.register()
    addon.register()
    assert all(getattr(cls,'is_registered','bl_rna' in cls.__dict__) for cls in addon.classes)
    assert bpy.app.handlers.load_post.count(addon._clear_runtime)==1

# Scene and per-object settings survive a .blend round-trip.
cube.better_item.link_dimensions=(True,False,True)
bpy.context.scene.better_item.reference='KEY'
bpy.context.scene.better_item.spacing=-.03
bpy.context.scene.better_item.axes=(True,False,True)
folder=Path(tempfile.mkdtemp(prefix='better_item_',dir=root))
bpy.context.preferences.filepaths.file_preview_type='NONE'
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'settings.blend'),check_existing=False)
bpy.ops.wm.open_mainfile(filepath=str(folder/'settings.blend'))
assert tuple(bpy.data.objects['Dimensions'].better_item.link_dimensions)==(True,False,True)
assert bpy.context.scene.better_item.reference=='KEY'
assert abs(bpy.context.scene.better_item.spacing+.03)<1e-6
assert tuple(bpy.context.scene.better_item.axes)==(True,False,True)
print('BETTER ITEM PASSED: proportional transforms, partial links, zeros, locks, world alignment, signed key ordering, independent axes, parents, rollback, mirror scale, registration and persistence.')


