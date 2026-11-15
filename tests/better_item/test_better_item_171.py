import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Euler
addon_utils.enable('better_item')
from better_item import distribution as d,distribution_preview as live
ctx=bpy.context;s=ctx.scene.better_item
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
objects=[]
for i in range(5):
 bpy.ops.mesh.primitive_cube_add(location=(3+i*4,2*i,-i));objects.append(ctx.object)
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
ctx.view_layer.objects.active=objects[0]
s.arrange_origin='GLOBAL';s.arrange_orientation='GLOBAL';s.distribution_method='OFFSET';s.arrange_on_axis=True
initial=[tuple(o.location) for o in objects];cases=0
for basis in ('ORIGINS','BOUNDS_CENTER','SURFACE','VOLUME','GEOMETRY'):
 for axis in range(3):
  for rotated in (False,True):
   if rotated:
    key=bpy.data.objects.get('Axes')
    if key is None:key=bpy.data.objects.new('Axes',None);ctx.scene.collection.objects.link(key)
    key.rotation_euler=(.2,.4,.7);s.arrange_orientation='REFERENCE';s.arrange_object=key
    matrix=np.array(Euler((.2,.4,.7)).to_matrix(),dtype=float)
   else:s.arrange_orientation='GLOBAL';matrix=np.eye(3)
   for i,o in enumerate(objects):o.location=matrix@np.array((3+i*4,4+i*3,5+i*2))
   ctx.view_layer.update();before=[np.linalg.solve(matrix,np.array(o.matrix_world.translation)) for o in objects]
   s.axes=tuple(j==axis for j in range(3));s.distribution_mode=basis;s.spacing=.5
   d.apply(ctx,objects);ctx.view_layer.update()
   for o,old in zip(objects,before):
    value=np.linalg.solve(matrix,np.array(o.matrix_world.translation));assert np.allclose(np.delete(value,axis),np.delete(old,axis),rtol=2e-6,atol=2e-6),(basis,axis,rotated,old,value)
   cases+=1
s.arrange_orientation='GLOBAL';s.axes=(True,False,False);s.distribution_mode='GEOMETRY'
for sign in (-1,1,-1):
 for i,o in enumerate(objects):o.location=initial[i]
 ctx.view_layer.update();s.spacing=sign*.5;d.apply(ctx,objects);s.spacing=0;d.apply(ctx,objects)
 assert all(sign*o.location.x>0 for o in objects)
 assert d.inspect_spacing(ctx,objects)[0]=='UNIFORM'
# Checkbox neither seeds requested Spacing nor moves on activation.
for i,o in enumerate(objects):o.location=initial[i]
ctx.view_layer.update();s.spacing=-.75;before=[tuple(o.location) for o in objects]
s.distribution_live=True
assert s.distribution_live and before==[tuple(o.location) for o in objects] and s.spacing==-.75
s.spacing=-.25;assert all(o.location.x<0 for o in objects)
s.spacing=0;assert all(o.location.x<0 for o in objects)
after=[tuple(o.location) for o in objects];s.distribution_live=False
assert not live.active(ctx.scene) and after==[tuple(o.location) for o in objects]
s.spacing=2;assert after==[tuple(o.location) for o in objects]
# Last nonzero direction survives saving, not just the preview lifetime.
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_suffix('.blend')))
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).with_suffix('.blend')))
s=bpy.context.scene.better_item;s.spacing=-3;s.spacing=0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_suffix('.blend')))
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).with_suffix('.blend')))
assert bpy.context.scene.better_item.distribution_last_sign==-1 and not bpy.context.scene.better_item.distribution_live
result={'passed':True,'transverse_cases':cases,'zero_direction_sequences':3,'checkbox_no_initial_mutation':True,'checkbox_disable_keeps_result':True,'direction_persistence':True}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2));print('171 PASSED',result)
