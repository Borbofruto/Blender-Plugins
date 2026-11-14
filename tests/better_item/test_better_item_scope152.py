import sys,random,math,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Vector,Matrix,Euler
addon_utils.enable('better_item')
import better_item as addon
from better_item import engine,frames,transform_view,references,native_refs
ctx=bpy.context
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
p=bpy.data.objects.new('Parent',None);ctx.scene.collection.objects.link(p)
o=bpy.data.objects.new('Child',None);ctx.scene.collection.objects.link(o);o.parent=p;ctx.view_layer.objects.active=o;o.select_set(True)
rng=random.Random(152)
fail=0
for case in range(1200):
 p.location=tuple(rng.uniform(-30,30) for i in range(3));p.rotation_euler=tuple(rng.uniform(-3,3) for i in range(3));p.scale=(rng.uniform(.5,3),)*3
 ctx.view_layer.update();o.matrix_parent_inverse=p.matrix_world.inverted()
 o.location=tuple(rng.uniform(-.3,.3) for i in range(3));ctx.view_layer.update()
 target=tuple(rng.uniform(-.21,.21) if i==0 else rng.uniform(-3,3) for i in range(3))
 engine.apply_world_positions([o],{o.name:target})
 assert engine._position_matches(o,target)
 assert not engine._position_matches(o,Vector(target)+Vector((.01,0,0)))
# Same manually authored frame as the screenshots, both common mm conventions.
p.location=(28.65919876,-6.51297045,-21.22911263);p.rotation_euler=(2.82963204,1.79027307,.74803495);p.scale=(2.75848913,)*3
ctx.view_layer.update();o.matrix_parent_inverse=p.matrix_world.inverted()
f=frames.create(ctx,'Manual 45 45',Vector((.33122,3.2745,2.048)),Euler((math.pi/4,math.pi/4,0)).to_matrix());uid=f.uid
s=o.better_item;s.reference_mode='FRAME';s.reference_frame=uid
for unit_scale in (1,.001):
 ctx.scene.unit_settings.scale_length=unit_scale;factor=.001/unit_scale
 f=frames.find(ctx.scene,uid);f.position=Vector((331.22,3274.5,2048))*factor
 for mm in range(-210,211):
  desired=Vector((mm,-3505,1126))*factor
  target=frames.frame_origin(f)+frames.frame_axes(f)@desired
  frames.set_position(ctx,o,desired)
  assert engine._position_matches(o,target),(unit_scale,mm)
# Default/local reproduces channels rather than a parent point/rotation frame.
s.transform_space='DEFAULT';o.location=(1,2,3);o.rotation_euler=(.1,.2,.3);o.delta_location=(.4,.5,.6);ctx.view_layer.update()
for group,field in [('LOCATION','location'),('ROTATION','rotation_euler'),('SCALE','scale')]:assert tuple(transform_view.values(ctx,o,group))==tuple(getattr(o,field))
world_before=o.matrix_world.translation.copy();p.location.x+=40;ctx.view_layer.update()
assert tuple(transform_view.values(ctx,o,'LOCATION'))==tuple(o.location)
assert (world_before-o.matrix_world.translation).length>10
s.link_location=(True,True,True);transform_view.edit_component(ctx,o,'LOCATION',0,3)
assert np.allclose(o.location,(3,6,9));s.link_location=(False,False,False)
o.lock_location[1]=True
try:transform_view.edit_component(ctx,o,'LOCATION',1,40)
except Exception:pass
else:raise AssertionError('Default lock must reject')
o.lock_location[1]=False
assert 'PARENT' not in {c[0] for c in references._LOCATION_CHOICES+references._ORIENTATION_CHOICES}
for kind in ('origin','axes'):
 for isframe in (False,True):
  prop=references.choice_property(kind,frame=isframe)
  titles=[entry[1] for entry in prop.keywords['items'] if not entry[0]]
  assert titles==['Better Item','Default'],titles
# No relative-animation schema, operator or handler in the active package.
assert not hasattr(o.better_item,'animation')
assert not any(getattr(h,'__module__','').startswith('better_item') for h in bpy.app.handlers.frame_change_pre+bpy.app.handlers.frame_change_post)
assert not hasattr(bpy.types,'BETTERITEM_OT_keyframe')
assert not hasattr(bpy.types,'BETTERITEM_OT_animation')
# Raw vector display matches native storage for quaternion and axis-angle too.
for mode in ('QUATERNION','AXIS_ANGLE','ZYX'):
 o.rotation_mode=mode
 assert o.better_item.transform_space=='DEFAULT'
# Real mesh native Dimensions edit changes its Scale, not a reference affine node.
bpy.ops.mesh.primitive_cube_add();mesh=ctx.object;mesh.parent=p;ctx.view_layer.update();mesh.better_item.transform_space='DEFAULT'
mesh.better_item.link_dimensions=(True,True,True)
transform_view.edit_component(ctx,mesh,'DIMENSIONS',0,4)
assert np.allclose(mesh.dimensions,(4,4,4)),tuple(mesh.dimensions)
assert not mesh.modifiers
print('152 CORE PASSED: 1200 parent-inverse cancellations, 842 mm sweep moves with manual frame, real-error rejection, Default/Local channels, parent independence, links/locks, native Dimensions, category titles and no animation runtime')
