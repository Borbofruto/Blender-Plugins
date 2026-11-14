"""Regression: explicit relative zeros and unsafe proportional denominators."""
import sys, random, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy, addon_utils, numpy as np
from mathutils import Matrix
addon_utils.enable('better_item')
from better_item import frames, transform_view as view, engine, math_core
from better_item.math_core import BetterItemError
ctx=bpy.context
def empty(name):
    obj=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(obj);return obj
obj,ref,parent=empty('Target'),empty('Reference'),empty('Parent')
s=obj.better_item;s.transform_space='REFERENCE';s.orientation='REFERENCE';s.orientation_object=ref
s.pivot_mode='OBJECT';s.origin_object=ref
rng=random.Random(156)
checks=0
for scale_length in (1.,.001):
    ctx.scene.unit_settings.scale_length=scale_length
    for use_parent in (False,True):
        obj.parent=parent if use_parent else None
        for case in range(50):
            parent.location=tuple(rng.uniform(-20,20) for _ in range(3))
            parent.rotation_euler=tuple(rng.uniform(-2,2) for _ in range(3))
            parent.scale=tuple(rng.uniform(.3,3) for _ in range(3))
            obj.matrix_parent_inverse=Matrix.Translation(tuple(rng.uniform(-4,4) for _ in range(3)))
            obj.delta_location=tuple(rng.uniform(-1,1) for _ in range(3))
            ref.location=tuple(rng.uniform(-5,5) for _ in range(3))
            ref.rotation_euler=tuple(rng.uniform(-2,2) for _ in range(3))
            ctx.view_layer.update()
            s.link_location=(False,False,False)
            frames.set_position(ctx,obj,(.2,-.4,-.86))
            view.edit_component(ctx,obj,'LOCATION',0,0.)
            assert view.values(ctx,obj,'LOCATION')[0]==0.,view.values(ctx,obj,'LOCATION')
            view.edit_component(ctx,obj,'LOCATION',1,0.)
            read=view.values(ctx,obj,'LOCATION')
            assert read[:2]==(0.,0.),read
            assert abs(read[2]+.86)<1e-4,read
            raw,budget,_=frames._position_sample(ctx,obj)
            assert np.all(np.abs(raw[:2])<=budget[:2])
            # A displayed zero must not secretly supply a huge finite ratio.
            s.link_location=(True,True,True);before=tuple(obj.location)
            try:view.edit_component(ctx,obj,'LOCATION',0,1.)
            except BetterItemError as exc:assert '= 0' in str(exc),str(exc)
            else:raise AssertionError('Zero denominator accepted')
            assert tuple(obj.location)==before
            # Remove only the UI hint, emulating an external native transform.
            del s['view_location_zero_signature']
            raw,budget,_=frames._position_sample(ctx,obj)
            if raw[0]!=0 and abs(raw[0])<=budget[0]:
                try:view.edit_component(ctx,obj,'LOCATION',0,1.)
                except BetterItemError as exc:assert 'BI-T008' in str(exc),str(exc)
                else:raise AssertionError('Uncertain denominator accepted')
                assert tuple(obj.location)==before
            checks+=1
# Hints are not a persistent freeze: changing a resolved reference invalidates them.
obj.parent=None;obj.delta_location=(0,0,0);ref.location=(3.21,-2.13,1.7);ref.rotation_euler=(.37,-.26,.61)
s.link_location=(False,False,False);ctx.view_layer.update();frames.set_position(ctx,obj,(0,0,-.86))
assert view.values(ctx,obj,'LOCATION')[:2]==(0.,0.)
ref.location.x+=.25;ctx.view_layer.update()
assert abs(view.values(ctx,obj,'LOCATION')[0])>.1
# Preserve real tiny coordinates; no fixed millimeter threshold or generic snap.
s.orientation='GLOBAL';s.pivot_mode='GLOBAL';obj.location=(0,0,0);ctx.view_layer.update()
frames.set_position(ctx,obj,(1e-13,2e-13,3e-13))
read=view.values(ctx,obj,'LOCATION');assert all(v!=0 for v in read),read
s.link_location=(True,True,True);view.edit_component(ctx,obj,'LOCATION',0,3e-13)
assert np.allclose(view.values(ctx,obj,'LOCATION'),(3e-13,6e-13,9e-13),rtol=1e-6,atol=0)
# Ordinary nonzero ratios and zeroing one member of a linked vector still work.
frames.set_position(ctx,obj,(100,200,600));view.edit_component(ctx,obj,'LOCATION',0,300)
assert view.values(ctx,obj,'LOCATION')==(300.,600.,1800.)
view.edit_component(ctx,obj,'LOCATION',1,0.)
assert view.values(ctx,obj,'LOCATION')==(0.,0.,0.)
# Hints survive a .blend round trip, then invalidate after a native movement.
s.link_location=(False,False,False)
s.orientation='REFERENCE';s.pivot_mode='OBJECT'
ctx.view_layer.update();frames.set_position(ctx,obj,(0.,0.,-.86))
with tempfile.TemporaryDirectory(prefix='better_item_zero_',dir=Path(__file__).resolve().parent) as directory:
    path=str(Path(directory)/'zero.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.wm.open_mainfile(filepath=path)
    obj=bpy.data.objects['Target'];ctx=bpy.context
    assert view.values(ctx,obj,'LOCATION')[:2]==(0.,0.),view.values(ctx,obj,'LOCATION')
    obj.location.x+=.1;ctx.view_layer.update()
    assert abs(view.values(ctx,obj,'LOCATION')[0])>.01
print('PASS: 200 rotated reference/parent/unit cases; exact requested zeros, raw uncertainty guard, reference invalidation, tiny genuine values, ordinary links.')
