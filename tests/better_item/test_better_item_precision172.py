"""Long geometric chains and translated endpoints; independent evaluated bounds oracle."""
import sys,json,random,time
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
addon_utils.enable('better_item')
from better_item import distribution as d,arrange
from better_item.math_core import BetterItemError
ctx=bpy.context;s=ctx.scene.better_item
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add();mesh=ctx.object.data;template=ctx.object
baseline='--baseline' in sys.argv;out=[]
def setup(count,offset,seed):
 rng=random.Random(seed);objects=[]
 for i in range(count):
  obj=bpy.data.objects.new('Piece%04d'%i,mesh);ctx.scene.collection.objects.link(obj)
  obj.location=(offset+i*3,10+rng.uniform(-5,5),20+rng.uniform(-5,5));objects.append(obj)
 template.select_set(False)
 for obj in objects:obj.select_set(True)
 ctx.view_layer.objects.active=objects[0];ctx.view_layer.update()
 return objects
def bounds(obj,axis):
 # Independent oracle uses float64 multiplication to avoid injecting another float32 matrix-vector rounding.
 points=np.array([tuple(v.co) for v in obj.data.vertices])@np.array(obj.matrix_world.to_3x3()).T+np.array(obj.matrix_world.translation)
 p=points@axis;return float(p.min()),float(p.max())
for method,count,offset,spacing,seed in [('OFFSET',200,100,g,k) for g in (.05,.2,1.) for k in range(3)]+[('ENDPOINT',n,o,.2,k) for n,o in ((12,300),(12,1000),(4,5000)) for k in range(4)]:
 objects=setup(count,offset,seed);before=[tuple(o.location) for o in objects]
 s.arrange_origin='CURSOR';ctx.scene.cursor.location=(offset,12,20);s.arrange_orientation='GLOBAL';s.axes=(True,False,False)
 s.distribution_method=method;s.distribution_mode='GEOMETRY' if method=='OFFSET' else 'ORIGINS';s.spacing=spacing
 if method=='ENDPOINT':
  s.distribution_end.mode='MANUAL';s.distribution_end.position=(offset+100,35,38)
  start=np.array(ctx.scene.cursor.location);end=np.array(s.distribution_end.position);axis=(end-start)/np.linalg.norm(end-start)
 else:axis=np.array((1.,0.,0.))
 row=dict(method=method,basis='GEOMETRY' if method=='OFFSET' else 'ORIGINS',count=count,offset=offset,spacing=spacing,seed=seed)
 try:
  _,info=d.apply(ctx,objects)
  intervals=sorted(bounds(o,axis) for o in objects);actual=np.array([b[0]-a[1] for a,b in zip(intervals,intervals[1:])]);wanted=spacing if method=='OFFSET' else info['spacing']-2*np.abs(axis).sum()
  row['inspection_state']=d.inspect_spacing(ctx,objects)[0]
  if not baseline:assert row['inspection_state']=='UNIFORM',row
  row.update(accepted=True,max_gap_error=float(np.max(np.abs(actual-wanted))),expected_gap=float(wanted))
  assert np.all(actual>0),row
  assert row['max_gap_error']<.004,row
 except BetterItemError as exc:
  row.update(accepted=False,error=str(exc));assert before==[tuple(o.location) for o in objects]
  if not baseline:raise AssertionError(row) from exc
 out.append(row)
 for obj in objects:bpy.data.objects.remove(obj,do_unlink=True)
result=dict(passed=not baseline,cases=out,accepted=sum(r['accepted'] for r in out),rejected=sum(not r['accepted'] for r in out))
path=Path(__file__).with_suffix('.baseline.json' if baseline else '.results.json');path.write_text(json.dumps(result,indent=2));print('172 PRECISION',result['accepted'],result['rejected'])
