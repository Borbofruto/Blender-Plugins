"""Storage budget does not permit collapsed positive gaps or occupied slots."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
addon_utils.enable('better_item')
from better_item import distribution as d
from better_item.math_core import BetterItemError
ctx=bpy.context;s=ctx.scene.better_item
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
objects=[]
for x in (1e9+1024,1e9+2048,1e9+3072,1e9+4096):
 bpy.ops.mesh.primitive_cube_add(location=(x,0,0));objects.append(ctx.object)
for o in objects:o.select_set(True)
ctx.view_layer.objects.active=objects[0];ctx.view_layer.update()
s.arrange_origin='CURSOR';ctx.scene.cursor.location=(1e9,0,0);s.arrange_orientation='GLOBAL';s.axes=(True,False,False);s.distribution_mode='GEOMETRY'
checked=[]
for method,gap,span in (('OFFSET',.2,0),('OFFSET',0,0),('ENDPOINT',0,128),('ENDPOINT',0,4)):
 s.distribution_method=method;s.spacing=gap;s.distribution_end.mode='MANUAL';s.distribution_end.position=(1e9+span,0,0)
 before=[tuple(o.location) for o in objects]
 try:d.apply(ctx,objects)
 except BetterItemError as e:
  assert 'BI-G002' in str(e) or 'BI-E003' in str(e) or 'BI-E001' in str(e),str(e)
  assert before==[tuple(o.location) for o in objects];checked.append((method,gap,span,str(e).split(']')[0]+']'))
 else:raise AssertionError(('Collapsed geometry accepted',method,gap,span))
# Wider coordinate tolerances must not hide symmetric shape changes.
for i,o in enumerate(objects):o.location=(10+10*i,0,0)
obj=objects[0];obj.data=obj.data.copy();obj.shape_key_add(name='Basis');shape=obj.shape_key_add(name='Symmetric expansion')
for v in shape.data:v.co*=2
curve=shape.driver_add('value');driver=curve.driver;var=driver.variables.new();var.name='x';var.type='TRANSFORMS';var.targets[0].id=obj;var.targets[0].transform_type='LOC_X';var.targets[0].transform_space='WORLD_SPACE';driver.expression='abs(x)/100'
s.distribution_method='OFFSET';s.distribution_mode='GEOMETRY';ctx.scene.cursor.location=(0,0,0);s.distribution_end.position=(100,0,0);ctx.view_layer.update()
before=[tuple(o.location) for o in objects]
try:d.apply(ctx,objects)
except BetterItemError as exc:assert 'BI-G003' in str(exc),str(exc)
else:raise AssertionError('Position-dependent symmetric bounds change accepted')
assert before==[tuple(o.location) for o in objects]
result={'passed':True,'symmetric_geometry_dependency_rejected':True,'atomic_rejections':checked};Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2));print('172 COLLAPSE PASSED',result)

