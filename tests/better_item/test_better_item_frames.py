import sys, math, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy, addon_utils
from mathutils import Vector, Euler, Matrix
addon_utils.enable('better_item',default_set=True)
import better_item as addon
from better_item import frames, orientation
from better_item.math_core import BetterItemError
context=bpy.context

def near(a,b,tol=1e-5):assert all(abs(x-y)<tol for x,y in zip(a,b)),(tuple(a),tuple(b))
def rotation_near(a,b):
    error=a.to_quaternion().rotation_difference(b.to_quaternion()).angle
    assert min(abs(error),abs(math.tau-error))<2e-4,error
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.object.empty_add()
source=context.object
source.name='Source'
source.location=(10,20,30)
source.rotation_euler=(0,0,math.pi/2)
source.scale=(2,3,4)
context.view_layer.update()
fixed=frames.create(context,'Fixed',source.matrix_world.translation,source.matrix_world.to_3x3().to_quaternion().to_matrix())
uid=fixed.uid
follow=frames.create(context,'Follow',source.matrix_world.translation,source.matrix_world.to_quaternion().to_matrix(),source)
fuid=follow.uid
source.location=(100,200,300)
source.rotation_euler=(0,0,math.pi/4)
context.view_layer.update()
near(frames.resolve(fixed)[0],(10,20,30))
near(frames.resolve(follow)[0],(100,200,300))
rotation_near(frames.resolve(follow)[1],source.matrix_world.to_quaternion().to_matrix())
frames.apply_reference(follow,'POSITION')
source.location=(500,600,700)
source.rotation_euler=(.2,.3,.4)
context.view_layer.update()
near(frames.resolve(follow)[0],(100,200,300))
rotation_near(frames.resolve(follow)[1],source.matrix_world.to_quaternion().to_matrix())
frames.apply_reference(follow)
assert follow.source is None and not follow.link_position and not follow.link_rotation
follow.rotation_x=.7
assert abs(follow.rotation[0]-.7)<1e-5
# Source-only frame relationship never changes the target's transforms.
bpy.ops.mesh.primitive_cube_add(size=1)
obj=context.object
obj.name='Target'
obj.location=(10,22,30)
obj.rotation_euler=(0,0,math.pi/2)
context.view_layer.update()
settings=obj.better_item
settings.orientation='SAVED'
settings.orientation_frame=uid
settings.pivot_mode='FRAME'
settings.pivot_frame=uid
near(frames.relative_values(context,obj,'POSITION'),(2,0,0))
near(frames.relative_values(context,obj,'ROTATION'),(0,0,0))
settings.location_x=4
near(obj.location,(10,24,30)) # live setter: no Apply button

near(obj.location,(10,24,30))
old_position=obj.location.copy()
settings.rotation_x=math.pi/2

near(obj.location,old_position)
rotation_near(obj.matrix_world.to_3x3(),frames.resolve(fixed)[1]@Euler((math.pi/2,0,0)).to_matrix())
# Rotation around explicitly selected saved origin.
obj.rotation_euler=(0,0,math.pi/2)
obj.location=(10,22,30)
settings.use_reference_pivot=True
context.view_layer.update()
settings.rotation_z=math.pi/2

near(obj.location,(8,20,30))
# A live frame changes the reading, never the already-transformed target.
live=frames.create(context,'Live',source.matrix_world.translation,source.matrix_world.to_quaternion().to_matrix(),source)
luid=live.uid
settings.orientation_frame=luid
settings.pivot_frame=luid
before=obj.matrix_world.copy()
reading=frames.relative_values(context,obj,'POSITION')
source.location.x+=50
source.rotation_euler.z+=.3
context.view_layer.update()
near(obj.matrix_world.translation,before.translation)
rotation_near(obj.matrix_world.to_3x3(),before.to_3x3())
assert tuple(frames.relative_values(context,obj,'POSITION'))!=reading
assert obj.parent is None and len(obj.constraints)==0
# Apply and delete source; static reference remains usable.
frames.apply_reference(live)
origin,axes=frames.resolve(live)
bpy.data.objects.remove(source,do_unlink=True)
context.view_layer.update()
near(frames.resolve(live)[0],origin)
rotation_near(frames.resolve(live)[1],axes)
# Names can change without breaking a UID selection.
live.name='Renamed'
assert frames.find(context.scene,settings.orientation_frame).name=='Renamed'
# Capture viewport orientation + pivot as a static reference.
context.scene.transform_orientation_slots[0].type='LOCAL'
context.scene.tool_settings.transform_pivot_point='CURSOR'
context.scene.cursor.location=(7,8,9)
assert bpy.ops.better_item.frame(action='VIEWPORT')=={'FINISHED'}
captured=context.scene.better_item.frames[-1]
near(frames.resolve(captured)[0],(7,8,9))
rotation_near(frames.resolve(captured)[1],obj.matrix_world.to_quaternion().to_matrix())
# Global defaults match actual world transforms, not parent-local fields.
settings.orientation='GLOBAL'
settings.pivot_mode='GLOBAL'
near(frames.relative_values(context,obj,'POSITION'),obj.matrix_world.translation)
# Pending edits are invalidated on changing the coordinate system.
settings.location_x=123
near(frames.relative_values(context,obj,'POSITION')[0:1],(123,))
settings.orientation='LOCAL'
assert obj.location.x==123
# Blocked edits cancel without touching geometry, parenting or selection.
settings.orientation='GLOBAL'
obj.lock_location[0]=True
old=obj.location.copy()
settings.location_x=999
assert obj.as_pointer() in addon._field_errors
near(obj.location,old)
obj.lock_location[0]=False
addon._field_errors.clear()
# Blend-file persistence retains frame IDs, source mode and enum choices.
settings.orientation='SAVED'
settings.orientation_frame=luid
settings.pivot_mode='FRAME'
settings.pivot_frame=uid
context.preferences.filepaths.file_preview_type='NONE'
with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
    path=str(Path(tmp)/'frames.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.wm.open_mainfile(filepath=path)
    restored=bpy.data.objects['Target'].better_item
    assert restored.orientation_frame==luid
    assert restored.pivot_frame==uid
    assert len(context.scene.better_item.frames)==4
    assert frames.find(context.scene,luid).name=='Renamed'
print('FRAMES PASSED: independent links, apply, manual values, deletion, live relative readings, absolute edits, separate pivot, UID rename and persistence')
# Multi-selection viewport pivot capture uses all selected origins.
obj=bpy.data.objects['Target']
bpy.context.view_layer.objects.active=obj
bpy.ops.object.select_all(action='DESELECT')
obj.location=(2,0,0)
obj.select_set(True)
bpy.ops.object.empty_add(location=(8,0,0))
other=bpy.context.object
obj.select_set(True)
bpy.context.view_layer.objects.active=obj
bpy.context.scene.tool_settings.transform_pivot_point='MEDIAN_POINT'
bpy.context.view_layer.update()
near(frames.viewport_origin(bpy.context,obj),(5,0,0))
# Missing live source fails visibly; unrelated static components survive.
missing=frames.create(bpy.context,'Missing',Vector(),Matrix.Identity(3),other)
bpy.data.objects.remove(other,do_unlink=True)
bpy.context.view_layer.update()
try:frames.resolve(missing)
except BetterItemError:pass
else:raise AssertionError('Missing live source must not silently use a stale pose')
# Applying an already-manual component never copies an unlinked source.
manual=frames.create(bpy.context,'Manual',Vector((3,4,5)),Matrix.Identity(3))
manual.source=obj
frames.apply_reference(manual,'POSITION')
near(manual.position,(3,4,5))
print('FRAME EDGE CASES PASSED: selection pivot, missing source, unlinked source isolation')
# Disabling/re-enabling the add-on preserves scene-owned frame data.
ids=[frame.uid for frame in bpy.context.scene.better_item.frames]
addon.unregister()
addon.register()
assert [frame.uid for frame in bpy.context.scene.better_item.frames]==ids
print('FRAME RE-REGISTRATION PASSED')

