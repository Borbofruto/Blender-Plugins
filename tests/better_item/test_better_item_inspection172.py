"""Inspection reuse and invalidation; timings include the real spacing getter."""
import sys,json,time
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Vector,Matrix
addon_utils.enable('better_item')
from better_item import distribution as d,frames,distribution_preview as live
ctx=bpy.context;s=ctx.scene.better_item
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add();template=ctx.object;template.select_set(False);objects=[]
for i in range(1500):
 o=bpy.data.objects.new('Cache%04d'%i,template.data);ctx.scene.collection.objects.link(o);o.location=(3+3*i,0,0);o.select_set(True);objects.append(o)
ctx.view_layer.objects.active=objects[0];ctx.view_layer.update();s.arrange_origin='GLOBAL';s.arrange_orientation='GLOBAL';s.distribution_method='OFFSET';s.axes=(True,False,False)
original=d._inspect_spacing;calls=0

def counted(*args):
 global calls
 calls+=1;return original(*args)
d._inspect_spacing=counted
rows=[]
for count in (600,1500):
 for basis in ('ORIGINS','GEOMETRY','VOLUME'):
  chosen=objects[:count];s.distribution_mode=basis;d.clear_inspection();ctx.view_layer.update()
  n=calls;t=time.perf_counter();expected=d.inspect_spacing(ctx,chosen);cold=time.perf_counter()-t
  t=time.perf_counter()
  for repeat in range(5):assert d.inspect_spacing(ctx,chosen)==expected
  warm=(time.perf_counter()-t)/5
  assert calls==n+1,(count,basis,calls,n)
  assert warm<max(.03,cold*.25),(count,basis,cold,warm)
  rows.append(dict(count=count,basis=basis,cold_seconds=cold,cached_seconds=warm))
# Getter and draw share one result; no second full pass.
s.distribution_mode='GEOMETRY';s.distribution_live=True;d.clear_inspection();ctx.view_layer.update()
n=calls;d.inspect_spacing(ctx,list(ctx.selected_objects));s.spacing_view
assert calls==n+1;assert len(d._inspection_cache)<=4;s.distribution_live=False
# Use a small selection for exhaustive invalidation comparisons.
for o in objects[3:]:o.select_set(False)
objects=objects[:3];obj=objects[0]
checks=[]
def fresh(label):
 n=calls;cached=d.inspect_spacing(ctx,objects);direct=original(ctx,objects)
 assert cached==direct,(label,cached,direct)
 assert calls>n,(label,'result was not invalidated')
 checks.append(label)
d.inspect_spacing(ctx,objects);obj.location.y+=4;ctx.view_layer.update();fresh('target Location')
obj.rotation_euler.z=.2;ctx.view_layer.update();fresh('target Rotation')
obj.scale.x=1.3;ctx.view_layer.update();fresh('target Scale')
s.spacing=-.3;fresh('spacing sign')
s.axes=(False,True,False);fresh('axis mask')
s.distribution_mode='BOUNDS_CENTER';fresh('placement basis')
obj.data=obj.data.copy();obj.shape_key_add(name='Basis');shape=obj.shape_key_add(name='Shape');shape.data[0].co.x+=4;shape.value=.4;ctx.view_layer.update();fresh('shape key')
array=obj.modifiers.new('Array','ARRAY');array.count=3;ctx.view_layer.update();fresh('modifier creation')
array.show_viewport=False;ctx.view_layer.update();fresh('modifier viewport state')
obj.data.vertices[0].co.z+=2;obj.data.update();ctx.view_layer.update();fresh('mesh data')
ctx.scene.frame_set(12);fresh('frame evaluation')
f=frames.create(ctx,'Inspection source',Vector((0,0,0)),Matrix.Identity(3));s.arrange_origin='SAVED';s.arrange_origin_frame=f.uid;fresh('saved Location Frame')
f.position=(10,20,30);fresh('manual Frame value without depsgraph update')
s.distribution_method='ENDPOINT';s.distribution_end.mode='MANUAL';s.distribution_end.position=(50,0,0);fresh('Endpoint method and source')
s.distribution_end.position=(60,10,5);fresh('manual Endpoint value')
s.distribution_end.mode='CURSOR';ctx.scene.cursor.location=(70,5,3);fresh('cursor Endpoint')
ctx.view_layer.objects.active=objects[-1];fresh('active object')
# Indirect evaluated geometry changes also invalidate the scalar inspection.
s.distribution_method='OFFSET';s.distribution_mode='GEOMETRY';s.arrange_origin='GLOBAL';s.axes=(True,False,False)
group=bpy.data.node_groups.new('Inspection dependency','GeometryNodeTree');group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
inp=group.nodes.new('NodeGroupInput');out=group.nodes.new('NodeGroupOutput');info=group.nodes.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE'
source=bpy.data.objects.new('External source',None);ctx.scene.collection.objects.link(source);info.inputs['Object'].default_value=source
move=group.nodes.new('GeometryNodeSetPosition');group.links.new(inp.outputs['Geometry'],move.inputs['Geometry']);group.links.new(info.outputs['Location'],move.inputs['Offset']);group.links.new(move.outputs['Geometry'],out.inputs['Geometry'])
obj.modifiers.new('External GN','NODES').node_group=group;ctx.view_layer.update();d.inspect_spacing(ctx,objects)
source.location.x=25;ctx.view_layer.update();fresh('external Geometry Nodes dependency')
s.arrange_origin='OBJECT';s.arrange_origin_object=template;ctx.view_layer.update();d.inspect_spacing(ctx,objects)
template.scale.x=2;ctx.view_layer.update();fresh('unselected reference geometry')

# The cache is bounded under changing reference snapshots, including manual edits without evaluation.
s.arrange_origin='SAVED';s.arrange_origin_frame=f.uid
for i in range(20):f.position.x=i;d.inspect_spacing(ctx,objects)
assert len(d._inspection_cache)<=4
# One registration lifecycle must not leave dangling callbacks/cache state.
import better_item
better_item.unregister();assert not d._inspection_cache and d.invalidate_inspection not in bpy.app.handlers.depsgraph_update_post
better_item.register()
ctx.preferences.edit.use_global_undo=True
bpy.ops.ed.undo_push(message='Inspection before edit')
obj.location.x+=2;ctx.view_layer.update();bpy.ops.ed.undo_push(message='Inspection after edit')
d.inspect_spacing(ctx,list(ctx.selected_objects));assert d._inspection_cache
bpy.ops.ed.undo();assert not d._inspection_cache
bpy.ops.ed.redo();assert not d._inspection_cache
checks.append('Undo/Redo clears inspection')
result={'passed':True,'timings':rows,'shared_draw_getter_measurement':True,'invalidation_checks':checks,'bounded_cache_and_unregister':True}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2));print('172 CACHE PASSED',json.dumps(result))
