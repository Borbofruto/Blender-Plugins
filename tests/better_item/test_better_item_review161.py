"""Check audit claims against real Blender; no blanket self-reference lockout."""
import sys,json,math
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Euler,Vector
addon_utils.enable('better_item')
from better_item import transform_view as view,frames,orientation,native_refs
from better_item.math_core import BetterItemError,align_positions,distribute_positions
from better_item.diagnostics import Diagnostic
ctx=bpy.context;obj=ctx.object;s=obj.better_item
results={}
def reset(storage='XYZ'):
    obj.rotation_mode=storage;obj.rotation_euler=(0,0,0);obj.rotation_quaternion=(1,0,0,0)
    obj.location=(0,0,0);obj.scale=(1,1,1);s.transform_space='REFERENCE';s.reference_mode='INDIVIDUAL'
    s.pivot_mode='GLOBAL';s.use_reference_pivot=False;s.view_rotation_order='XYZ'
    ctx.view_layer.update()
def same_rotation(angles):
    assert orientation.rotation(obj).to_quaternion().rotation_difference(Euler(angles).to_quaternion()).angle<2e-4
# An unparented quaternion target has a stationary identity Gimbal basis.
reset('QUATERNION');s.orientation='GIMBAL';view.set_rotation(ctx,obj,(.2,.1,.3));same_rotation((.2,.1,.3))
results['quaternion_gimbal_rotation_remains_supported']=True
# Test all Euler orders/components; accepted values must read back, refusals restore.
accepted=rejected=0
for order in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX'):
    for axis in range(3):
        reset(order);s.orientation='GIMBAL';obj.rotation_euler=(.2,.3,.4);ctx.view_layer.update()
        before=view._snapshot(obj);requested=list(view.values(ctx,obj,'ROTATION'));requested[axis]+=.35
        try:view.set_rotation(ctx,obj,requested)
        except BetterItemError as exc:
            assert 'BI-T009' in str(exc),str(exc)
            assert view._snapshot(obj)==before
            rejected+=1
        else:
            actual=Euler(view.values(ctx,obj,'ROTATION')).to_quaternion()
            assert actual.rotation_difference(Euler(requested).to_quaternion()).angle<2e-4
            accepted+=1
assert accepted>0 and rejected>0,(accepted,rejected)
results['euler_gimbal_edits']={'accepted':accepted,'atomic_rejections':rejected}
# Object-mode Normal follows the object. Applying its frame gives an independent basis.
reset();s.orientation='NORMAL';obj.rotation_euler=(.2,.3,.4);ctx.view_layer.update()
before=view._snapshot(obj)
try:view.set_rotation(ctx,obj,(.25,0,0))
except BetterItemError as exc:
    assert 'BI-T009' in str(exc),str(exc)
    assert view._snapshot(obj)==before
else:raise AssertionError('Self-following Normal must not silently accept different readback')
frame=frames.create(ctx,'Independent Normal',Vector(),native_refs.orientation(ctx,'NORMAL',obj))
s.orientation='SAVED';s.orientation_frame=frame.uid
view.set_rotation(ctx,obj,(.25,0,0))
assert np.allclose(view.values(ctx,obj,'ROTATION'),(.25,0,0),atol=2e-5)
results['normal_frame_snapshot_allows_rotation']=True
# Signed spacing uses opposite-half-space priority, then distance, per axis.
origins={'Key':(-600,0,0),'A':(-800,0,0),'B':(-500,0,0),'C':(-1000,0,0)}
positive=distribute_positions(origins,(1,0,0),'KEY',30,'Key')
negative=distribute_positions(origins,(1,0,0),'KEY',-30,'Key')
assert [positive[n][0] for n in ('A','C','B')]==[-570,-540,-510]
assert [negative[n][0] for n in ('B','A','C')]==[-630,-660,-690]
results['opposite_halfspace_order_both_signs']=True
# Every domain failure already has a code through the common constructor.
error=BetterItemError('Example fallback')
assert str(error).startswith('[BI-V001]') and '[BI-' not in Diagnostic(error).summary
results['central_code_fallback_and_hidden_ui_code']=True
for operation,code in (
    (lambda:align_positions({},(1,0,0),'SELECTION'),'BI-A003'),
    (lambda:align_positions({'A':(0,0,0),'B':(1,0,0)},(0,0,0),'SELECTION'),'BI-A001'),
    (lambda:align_positions({'A':(0,0,0),'B':(1,0,0)},(1,0,0),'SELECTION','INVALID'),'BI-A004'),
    (lambda:distribute_positions({'A':(0,0,0)},(1,0,0),'KEY',1,'A'),'BI-A003'),
    (lambda:distribute_positions({'A':(0,0,0),'B':(1,0,0)},(1,0,0),'KEY',float('inf'),'A'),'BI-D001')):
    try:operation()
    except BetterItemError as exc:assert str(exc).startswith('['+code+']'),str(exc)
    else:raise AssertionError('Invalid arrangement input accepted')
results['specific_input_codes']=5
# Object extracts a rotation; native Gimbal can retain inherited obliquity.
reset();grand=bpy.data.objects.new('Nonuniform ancestor',None);ctx.scene.collection.objects.link(grand)
parent=bpy.data.objects.new('Rotated parent',None);ctx.scene.collection.objects.link(parent)
grand.scale=(2,1,1);parent.parent=grand;parent.rotation_euler.z=.5;obj.parent=parent
ctx.view_layer.update()
object_basis=np.asarray(orientation.rotation(obj));gimbal_basis=np.asarray(native_refs.orientation(ctx,'GIMBAL',obj))
assert np.max(np.abs(object_basis.T@object_basis-np.eye(3)))<2e-6
assert np.max(np.abs(gimbal_basis.T@gimbal_basis-np.eye(3)))>.05
results['object_orthogonal_gimbal_oblique_under_shear']=True
print('161 REVIEW PASSED',json.dumps(results))
Path(__file__).with_suffix('.results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
