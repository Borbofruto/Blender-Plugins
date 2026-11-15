"""Method-specific placement and transient reference-driven Live editing."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector
addon_utils.enable('better_item')
from better_item import distribution as d,distribution_preview as live,placement,frames,arrange
from better_item.math_core import BetterItemError
ctx=bpy.context;checks=[]

def reset(n=5):
 live.forget();bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 s=ctx.scene.better_item;s.arrange_reference_mode='INDIVIDUAL';s.arrange_origin='GLOBAL';s.arrange_orientation='GLOBAL'
 s.distribution_method='OFFSET';s.distribution_mode='ORIGINS';s.distribution_start_override=False;s.distribution_end.mode='MANUAL';s.distribution_end.position=(10,0,0);s.axes=(True,False,False)
 objs=[]
 for i in range(n):
  bpy.ops.mesh.primitive_cube_add(location=(3+5*i,2+i,0));objs.append(ctx.object)
 select(objs,objs[0]);return s,objs

def select(objs,active=None):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 ctx.view_layer.objects.active=active or (objs[0] if objs else None);ctx.view_layer.update()

def empty(name,pos):
 o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);o.location=pos;ctx.view_layer.update();return o

def tick():ctx.view_layer.update();live.poll()
def positions(objs):return [tuple(o.location) for o in objs]
def line(objs,start,end):
 # Endpoint order is first solved from the initial scene, then kept while sources move.
 for i,o in enumerate(objs):assert np.allclose(o.matrix_world.translation,np.array(start)+(np.array(end)-start)*i/(len(objs)-1),rtol=2e-6,atol=2e-6),(o.name,tuple(o.location),start,end)

s,objs=reset();s.distribution_mode='GEOMETRY';s.distribution_method='ENDPOINT'
assert s.distribution_mode=='ORIGINS' and 'GEOMETRY' not in [i[0] for i in placement.items(s,ctx)]
s.distribution_mode='SURFACE';s.distribution_method='OFFSET';assert s.distribution_mode=='GEOMETRY'
s.distribution_method='ENDPOINT';assert s.distribution_mode=='SURFACE'
assert dict((i[0],i[1]) for i in placement.BASES)['VOLUME']=='Center of Mass (Volume)'
checks.append('separate saved placements and native labels')
# No interval-fit condition: two-unit cubes may overlap inside a half-unit segment.
s.distribution_end.position=(.5,0,0);s.distribution_mode='ORIGINS';before=[(tuple(o.scale),tuple(o.rotation_euler),o.data.as_pointer()) for o in objs]
d.apply(ctx,objs);line(objs,(0,0,0),(.5,0,0));assert before==[(tuple(o.scale),tuple(o.rotation_euler),o.data.as_pointer()) for o in objs]
try:d.endpoint_plan(ctx,objs,basis='GEOMETRY')
except BetterItemError as exc:assert 'BI-E002' in str(exc)
else:raise AssertionError('Retired interval placement remained callable')
checks.append('short Endpoint permits overlap without resizing')
# Legacy Endpoint/Geometry choices migrate visibly, preserving the Offset choice.
for key in ('placement_schema','offset_placement_value','endpoint_placement_value'):
 if key in s:del s[key]
s['distribution_mode']=1;placement.migrate(s)
assert s.distribution_mode=='ORIGINS' and s['placement_migration_notice']
s.distribution_method='OFFSET';assert s.distribution_mode=='GEOMETRY'
checks.append('legacy Geometry Endpoint migration notice')
# Unselected object sources can be manipulated by changing the selection.
s,objs=reset(3);a=empty('Start',(0,0,0));b=empty('End',(10,0,0))
s.distribution_method='ENDPOINT';s.distribution_start_override=True;s.distribution_start.mode='OBJECT';s.distribution_start.object=a;s.distribution_end.mode='OBJECT';s.distribution_end.object=b
select(objs);before=positions(objs);s.distribution_live=True;assert before==positions(objs)
select([b],b);b.location=(9,6,3);tick();assert not arrange.error(ctx.scene),str(arrange.error(ctx.scene));line(objs,(0,0,0),(9,6,3))
a.location=(-4,3,1);tick();line(objs,(-4,3,1),(9,6,3))
assert not objs[0].select_get() and ctx.active_object==b
assert d.inspect_spacing(ctx,[])[0]=='UNIFORM';assert len(live.captured_objects(ctx))==3
# Captured order survives moving Start past the previous targets.
a.location=(30,0,0);tick();line(objs,(30,0,0),(9,6,3))
s.distribution_live=False;after=positions(objs);b.location.x=20;tick();assert positions(objs)==after and not bpy.app.timers.is_registered(live.poll)
checks.append('object sources, changed selection, stable order and stop')
# Active source identity is captured. Selected endpoint moves are never restored by Live.
s,objs=reset(4);key=objs[0];key.location=(0,0,0);s.distribution_method='ENDPOINT';s.arrange_origin='PIVOT';s.reference_pivot='ACTIVE_ELEMENT';s.distribution_end.mode='CURSOR';ctx.scene.cursor.location=(12,0,0)
select(objs,key);s.distribution_live=True
other=empty('New active',(100,100,100));select([other],other);ctx.scene.cursor.location=(15,6,0);tick();line(objs,(0,0,0),(15,6,0))
key.location=(-3,2,0);tick();line(objs,(-3,2,0),(15,6,0));assert tuple(key.location)==(-3,2,0)
s.distribution_live=False;checks.append('cursor and captured Active identity; selected anchor editable')
# Manual fields and independently linked frame location are also live inputs.
s,objs=reset(3);a=empty('Linked frame source',(0,0,0));f=frames.create(ctx,'Only Location',Vector(),Matrix.Identity(3));f.position_mode='OBJECT';f.position_source=a;f.rotation_mode='OBJECT';f.rotation_source=None
s.distribution_method='ENDPOINT';s.arrange_origin='SAVED';s.arrange_origin_frame=f.uid;s.distribution_end.position=(20,0,0)
s.distribution_live=True;a.location=(2,3,4);tick();line(objs,(2,3,4),(20,0,0))
s.distribution_end.position=(9,8,7);line(objs,(2,3,4),(9,8,7));assert not arrange.error(ctx.scene),str(arrange.error(ctx.scene))
# Invalid references preserve the last result, and fixing the reference resumes editing.
last=positions(objs);s.distribution_end.position=(2,3,4);assert positions(objs)==last and 'BI-E001' in str(arrange.error(ctx.scene))
s.distribution_end.position=(15,8,7);assert not arrange.error(ctx.scene),str(arrange.error(ctx.scene));line(objs,(2,3,4),(15,8,7))
# Direct target edits are not silently overwritten.
objs[1].location.y+=3;manual=positions(objs);tick();assert positions(objs)==manual and 'BI-L001' in str(arrange.error(ctx.scene))
s.distribution_live=False;checks.append('Frame/manual inputs, recovery and target edit guard')
# Offset also observes reference changes and preserves unselected coordinates.
s,objs=reset(3);a=empty('Offset source',(0,0,0));s.arrange_origin='OBJECT';s.arrange_origin_object=a;s.distribution_mode='GEOMETRY';s.spacing=.3;s.distribution_live=True
before=positions(objs)
bpy.ops.mesh.primitive_cube_add(location=(100,100,100));tick();assert positions(objs)==before
a.location=(8,50,60);tick();assert all(o.location.x>8 for o in objs)
assert [tuple(o.location)[1:] for o in objs]==[v[1:] for v in before]
s.distribution_live=False;checks.append('Offset reference observer preserves transverse axes')
# Playback/seek/render do not establish a distribution runtime.
select(objs);s.distribution_live=True;ctx.scene.frame_set(15);assert not s.distribution_live and not bpy.app.timers.is_registered(live.poll)
s.distribution_live=True;live.stop_on_render(ctx.scene);assert not s.distribution_live
checks.append('frame change and render end Live')
# Per-method choices persist, transient editing does not.
s.distribution_method='OFFSET';s.distribution_mode='GEOMETRY';s.distribution_method='ENDPOINT';s.distribution_mode='VOLUME'
path=Path(__file__).with_suffix('.blend');bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
s=bpy.context.scene.better_item;assert s.distribution_mode=='VOLUME' and not s.distribution_live
s.distribution_method='OFFSET';assert s.distribution_mode=='GEOMETRY'
checks.append('per-method choices persist across reopen')
# Disabling the extension ends observation without rolling back committed live edits.
current=list(ctx.selected_objects);s.distribution_live=True;s.spacing=.6
poses=positions(current)
import better_item
better_item.unregister()
assert positions(current)==poses and not bpy.app.timers.is_registered(live.poll)
assert live.stop_on_frame_change not in bpy.app.handlers.frame_change_pre
better_item.register();assert not ctx.scene.better_item.distribution_live
checks.append('unregister keeps poses and removes observer/guards')
result={'passed':True,'checks':checks};Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2));print('173 PASSED',json.dumps(result))
