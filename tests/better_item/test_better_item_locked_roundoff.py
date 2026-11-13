import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector
addon_utils.enable('better_item',default_set=True)
from better_item import engine
from better_item.math_core import BetterItemError
ctx=bpy.context
def empty(name):
    obj=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(obj);return obj
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parent=empty('Parent');obj=empty('Locked child');obj.parent=parent
obj.lock_location=(False,True,True)
rng=np.random.default_rng(142)
count=0
for i in range(1500):
    parent.location=tuple(rng.uniform(-50,50,3));parent.rotation_euler=tuple(rng.uniform(-math.pi,math.pi,3))
    parent.scale=tuple(rng.uniform(.2,4,3));obj.location=tuple(rng.uniform(-20,20,3))
    obj.delta_location=tuple(rng.uniform(-1,1,3));ctx.view_layer.update()
    locked=tuple(obj.location)[1:]
    planned=Vector((float(rng.uniform(-20,20)),obj.location.y+obj.delta_location.y,obj.location.z+obj.delta_location.z))
    target=parent.matrix_world@planned
    engine.apply_world_positions([obj],{obj.name:tuple(target)})
    assert tuple(obj.location)[1:]==locked
    count+=1
# A real locked displacement is rejected even with the extra numerical budget.
before=obj.location.copy()
target=parent.matrix_world@Vector((obj.location.x,obj.location.y+.01,obj.location.z))
try:engine.apply_world_positions([obj],{obj.name:tuple(target)})
except BetterItemError as exc:assert 'BI-T003' in str(exc)
else:raise AssertionError('Real locked displacement accepted')
assert obj.location==before
# Unexpected world error still fails BI-T006 and rolls back: the accepted
# noise budget is recorded only for axes actually snapped by this operation.
obj.lock_location=(False,False,False);original=engine._target_location
def corrupt(item,target):return original(item,target)+Vector((.02,0,0))
engine._target_location=corrupt
try:
    target=obj.matrix_world.translation+Vector((1,0,0))
    try:engine.apply_world_positions([obj],{obj.name:tuple(target)})
    except BetterItemError as exc:assert 'BI-T006' in str(exc)
    else:raise AssertionError('Unexpected positioning error accepted')
    assert obj.location==before
finally:engine._target_location=original
print('LOCKED ROUNDING PASSED: %d rotated/scaled parents, exact locked channels, real lock rejection and BI-T006 rollback'%count)
