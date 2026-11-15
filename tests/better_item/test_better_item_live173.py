"""Live observer grid: independent placement points, source motion and stable order."""
import sys,json,itertools
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Vector
addon_utils.enable('better_item')
from better_item import distribution_preview as live,engine,arrange
ctx=bpy.context;s=ctx.scene.better_item
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
objs=[]
for i in range(4):
 bpy.ops.mesh.primitive_cube_add();o=ctx.object;o.name='Piece'+str(i)
 for v in o.data.vertices:v.co+=Vector((.2*i,-.1*i,.15*i))
 o.data.update();objs.append(o)

def empty(name):
 o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);return o
a=empty('Start');b=empty('End');axes=empty('Axes');parent=empty('Parent');parent.rotation_euler=(.2,.1,.3);parent.scale=(1.3,.8,1.1)

def point(o,basis):
 p=np.array(o.matrix_world.translation,dtype=float)
 if o in objs and basis!='ORIGINS':p+=np.array(o.matrix_world.to_3x3())@np.array((.2*objs.index(o),-.1*objs.index(o),.15*objs.index(o)))
 return p

cases=0;updates=0
for basis,path,mode,parented,sign in itertools.product(('ORIGINS','BOUNDS_CENTER','SURFACE','VOLUME'),('SEGMENT','AXIS'),('NONE','START','BOTH'),(False,True),(1,-1)):
 live.forget();arrange.clear_error()
 s.distribution_method='ENDPOINT';s.distribution_mode=basis;s.endpoint_path=path;s.distribution_start_override=True;s.distribution_start.mode='OBJECT';s.distribution_end.mode='OBJECT';s.arrange_orientation='REFERENCE';s.arrange_object=axes;s.axes=(True,False,False)
 axes.rotation_euler=(.2,.3,.4);a.location=(-2,1,3);b.location=(20*sign,8,7)
 for i,o in enumerate(objs):o.parent=parent if parented and i%2 else None;o.rotation_euler=(.11*i,.07*i,-.13*i);o.scale=(-1 if i%2 else 1,1,1);o.location=(6+7*i,2+i,1+i)
 ctx.view_layer.update()
 start=objs[0] if mode!='NONE' else a;end=objs[-1] if mode=='BOTH' else b
 engine.apply_world_positions([start,end],{start.name:(-2,1,3),end.name:(20*sign,8,7)})
 s.distribution_start.object=start;s.distribution_end.object=end
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 ctx.view_layer.objects.active=objs[0];ctx.view_layer.update()
 native={o:(tuple(o.rotation_euler),tuple(o.scale),o.data.as_pointer()) for o in objs}
 live.begin(ctx)
 # Change selection to a reference proxy, as in an ordinary viewport workflow.
 bpy.ops.object.select_all(action='DESELECT');end.select_set(True);ctx.view_layer.objects.active=end
 last_order=None
 for step in range(2):
  end.location.x+=sign*2;start.location.y+=.4
  if step:axes.rotation_euler.z+=.1
  ctx.view_layer.update();live.poll();assert not arrange.error(ctx.scene),(basis,path,mode,parented,sign,str(arrange.error(ctx.scene)))
  pa=point(start,basis);pb=point(end,basis)
  if path=='AXIS':
   u=np.array(axes.matrix_world.to_3x3().col[0]);u/=np.linalg.norm(u);pb=pa+u*np.dot(pb-pa,u)
  u=pb-pa;length=np.linalg.norm(u);u/=length
  moving=[o for o in objs if o not in (start,end)];ordered=sorted(moving,key=lambda o:np.dot(point(o,basis)-pa,u))
  if last_order is not None:assert ordered==last_order,(basis,path,mode,'order changed')
  last_order=ordered
  slots=range(0 if mode=='NONE' else 1,3 if mode=='BOTH' else 4)
  for o,index in zip(ordered,slots):assert np.allclose(point(o,basis),pa+(pb-pa)*index/3,atol=3e-5,rtol=3e-6),(basis,path,mode,index,point(o,basis),pa,pb)
  assert all(native[o]==(tuple(o.rotation_euler),tuple(o.scale),o.data.as_pointer()) for o in objs)
  updates+=1
 live.finish(ctx);cases+=1
result={'passed':True,'live_batches':cases,'reference_updates':updates,'point_bases':4,'paths':2,'anchor_modes':3,'parented_and_mirrored':True,'stable_order':True,'independent_cube_center_oracle':True}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2));print('173 LIVE MATRIX PASSED',json.dumps(result))
