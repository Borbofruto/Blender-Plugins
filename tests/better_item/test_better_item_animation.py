import sys,math,tempfile,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Vector,Matrix,Euler
addon_utils.enable('better_item',default_set=True)
from better_item import animation,frames
from better_item.math_core import BetterItemError
ctx=bpy.context
def near(a,b,tol=3e-5):assert np.allclose(a,b,atol=tol,rtol=0),(tuple(a),tuple(b))
def empty(name):
    o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);return o
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
source=empty('Source');target=empty('Actor');ctx.view_layer.objects.active=target;target.select_set(True)
source.location=(10,0,0);target.location=(11,0,0);ctx.view_layer.update()
s=target.better_item;s.orientation='REFERENCE';s.orientation_object=source;s.pivot_mode='OBJECT';s.origin_object=source
animation.start(ctx,target);a=s.animation
assert a.enabled and target.parent is None and not target.constraints
near(a.location,(1,0,0));ctx.scene.frame_set(1)
animation.keyframe(target,'LOCATION',1);animation.keyframe(target,'ROTATION',1)
ctx.scene.frame_set(11)
a.location=(3,0,0);a.rotation=(0,0,math.pi/2)
animation.keyframe(target,'LOCATION',11);animation.keyframe(target,'ROTATION',11)
for c in animation.object_curves(target):
    for k in c.keyframe_points:k.interpolation='LINEAR'
ctx.scene.frame_set(6)
assert not a.error,a.error
near(target.matrix_world.translation,(12,0,0))
near(target.matrix_world.to_quaternion().to_euler(),(0,0,math.pi/4))
# Reference movement affects the live trajectory, with no parenting.
source.location=(20,5,0);source.rotation_euler.z=math.pi/2;ctx.view_layer.update();ctx.scene.frame_set(6)
assert not a.error,a.error
near(target.matrix_world.translation,(20,7,0))
near(target.matrix_world.to_quaternion().to_euler(),(0,0,3*math.pi/4))
# A deleted source applies the last cached basis to the OWNED frame only.
uid=a.binding_uid
bpy.data.objects.remove(source,do_unlink=True);ctx.view_layer.update();ctx.scene.frame_set(7)
assert not a.error,a.error
f=frames.find(ctx.scene,uid)
assert f.position_mode==f.rotation_mode=='MANUAL'
near(frames.frame_origin(f),(20,5,0))
near(target.matrix_world.translation,(20,7.2,0))
assert a.warning
# Backward jumps use actual animated RNA channels, not previous-frame deltas.
ctx.scene.frame_set(1);near(target.matrix_world.translation,(20,6,0))
ctx.scene.frame_set(11);near(target.matrix_world.translation,(20,8,0))
# Portable native bake produces the same sampled trajectory with handler off.
a.start=1;a.end=11;a.step=1
expected=[]
for frame in range(1,12):ctx.scene.frame_set(frame);expected.append(target.matrix_world.copy())
animation.bake(ctx,target);assert not a.enabled
for frame,matrix in enumerate(expected,1):
    ctx.scene.frame_set(frame);near(target.matrix_world.translation,matrix.translation)
    assert target.matrix_world.to_quaternion().rotation_difference(matrix.to_quaternion()).angle<3e-4
assert all(c.data_path!='better_item.location_x' for c in animation.object_curves(target))
# Target native pose animation is not silently overwritten on restart.
try:animation.start(ctx,target)
except BetterItemError as exc:assert 'BI-AN001' in str(exc)
else:raise AssertionError('Native animation conflict not rejected')
# Cyclic native/reference dependencies cannot start.
cycle=empty('Cycle');ctx.view_layer.objects.active=cycle;cycle.select_set(True)
cycle.better_item.orientation='REFERENCE';cycle.better_item.orientation_object=cycle
try:animation.start(ctx,cycle)
except BetterItemError as exc:assert 'BI-AN003' in str(exc)
else:raise AssertionError('Self-reference animation allowed')
assert not cycle.better_item.animation.enabled
print('ANIMATION PASSED: actual channel playback, interpolation, moving/deleted source, last-basis fallback, backward seeks, native bake, ownership conflicts and cycles')
