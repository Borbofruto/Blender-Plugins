"""Additional 1.6 audit tests: external geometry dependency, units, 240 objects."""
import sys,json,time,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix
addon_utils.enable('better_item')
from better_item import geometry_arrange as geom,engine,transform_view as view,arrange
from better_item.math_core import BetterItemError
ctx=bpy.context;result={}
def reset():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    s=ctx.scene.better_item;s.arrange_reference_mode='INDIVIDUAL';s.arrange_orientation='GLOBAL'
    s.arrange_origin='GLOBAL';s.arrange_on_axis=False
    view.clear_cache();return s
def cube(name,x):
    bpy.ops.mesh.primitive_cube_add(location=(x,0,0));obj=ctx.object;obj.name=name;return obj
def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    ctx.view_layer.objects.active=objects[0];ctx.view_layer.update()
def distribute(objects,gap):
    ctx.view_layer.update();origins={o.name:tuple(o.matrix_world.translation) for o in objects}
    targets,verify=geom.plan(ctx,objects,origins,(True,False,False),spacing=gap)
    engine.apply_world_positions(objects,targets,verify=verify)
def interval(obj):
    world=np.asarray(obj.matrix_world,dtype=np.float64)
    points=np.asarray([v.co[:] for v in obj.data.vertices],dtype=np.float64)
    x=points@world[0,:3]+world[0,3]
    return float(x.min()),float(x.max())
def assert_gaps(objects,gap):
    intervals=sorted(interval(o) for o in objects)
    errors=[abs(b[0]-a[1]-gap) for a,b in zip(intervals,intervals[1:])]
    assert max(errors,default=0)<2e-5*max(1,abs(gap)),max(errors)
    return max(errors,default=0)
# Object Info relative coordinates change the evaluated offset as the target moves.
s=reset();target=cube('Object Info dependent target',8)
source=bpy.data.objects.new('Independent Object Info source',None);ctx.scene.collection.objects.link(source);source.location=(20,0,0)
group=bpy.data.node_groups.new('Relative Object Info audit','GeometryNodeTree')
group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
inp=group.nodes.new('NodeGroupInput');out=group.nodes.new('NodeGroupOutput')
info=group.nodes.new('GeometryNodeObjectInfo');info.inputs['Object'].default_value=source;info.transform_space='RELATIVE'
move=group.nodes.new('GeometryNodeSetPosition');factor=group.nodes.new('ShaderNodeVectorMath');factor.operation='SCALE';factor.inputs['Scale'].default_value=.1
group.links.new(inp.outputs['Geometry'],move.inputs['Geometry']);group.links.new(info.outputs['Location'],factor.inputs[0])
group.links.new(factor.outputs['Vector'],move.inputs['Offset']);group.links.new(move.outputs['Geometry'],out.inputs['Geometry'])
target.modifiers.new('Object Info offset','NODES').node_group=group;select([target]);before=view._snapshot(target)
try:distribute([target],.1)
except BetterItemError as exc:assert 'BI-G003' in str(exc),str(exc)
else:raise AssertionError('Location-dependent Object Info geometry must reject')
assert view._snapshot(target)==before
result['object_info_relative_geometry_atomic_rejection']=True
# Imperial is a display convention; physical conversion follows Scene Unit Scale.
unit_cases=[]
for system,scale in (('METRIC',1.),('METRIC',.001),('IMPERIAL',1.),('IMPERIAL',.3048)):
    s=reset();ctx.scene.unit_settings.system=system;ctx.scene.unit_settings.scale_length=scale
    objects=[cube('Unit'+str(i),4+6*i) for i in range(3)];select(objects)
    spacing=bpy.utils.units.to_value(system,'LENGTH','30 mm')/scale
    assert abs(spacing*scale-.03)<3e-9  # Blender's unit parser uses float32 factors.
    distribute(objects,spacing);assert_gaps(objects,spacing)
    unit_cases.append({'system':system,'scale_length':scale,'gap_mm':30})
result['units']=unit_cases
# Measure a reproducible finite scene, without claiming a whole-viewport benchmark.
s=reset();ctx.scene.unit_settings.system='METRIC';ctx.scene.unit_settings.scale_length=1.
objects=[cube('Batch%03d'%i,8+8*i) for i in range(240)]
for i,o in enumerate(objects):o.scale=(.5+.25*(i%3),1,1)
select(objects);before={o.name:(tuple(o.rotation_euler),tuple(o.scale),o.data.as_pointer()) for o in objects}
start=time.perf_counter();distribute(objects,.25);elapsed=time.perf_counter()-start
error=assert_gaps(objects,.25)
assert all(before[o.name]==(tuple(o.rotation_euler),tuple(o.scale),o.data.as_pointer()) for o in objects)
result['batch240']={'seconds_plan_apply_verify':elapsed,'maximum_gap_error_blender_units':error}
# Distribution undo, redo and .blend reopen preserve the result and references.
bpy.context.preferences.edit.use_global_undo=True
original={o.name:tuple(o.location) for o in objects}
bpy.ops.ed.undo_push(message='Before negative spacing')
assert bpy.ops.better_item.distribute('EXEC_DEFAULT',axes=(True,False,False),distribution_mode='GEOMETRY',spacing=-.25)=={'FINISHED'}
after={o.name:tuple(o.location) for o in objects};assert after!=original
bpy.ops.ed.undo_push(message='After negative spacing');bpy.ops.ed.undo()
assert {n:tuple(bpy.data.objects[n].location) for n in original}==original
bpy.ops.ed.redo();assert {n:tuple(bpy.data.objects[n].location) for n in after}==after
ctx.scene.better_item.distribution_mode='GEOMETRY';ctx.scene.better_item.spacing=-.25
with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
    p=str(Path(td)/'distribution.blend');bpy.ops.wm.save_as_mainfile(filepath=p);bpy.ops.wm.open_mainfile(filepath=p)
    assert {n:tuple(bpy.data.objects[n].location) for n in after}==after
    assert bpy.context.scene.better_item.spacing==-.25
result['distribution_undo_redo_reopen']=True
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('161 ARRANGEMENT AUDIT PASSED',json.dumps(result))
