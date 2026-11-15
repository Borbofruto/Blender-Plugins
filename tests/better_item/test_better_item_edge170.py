"""Dependency, cache, source lifecycle and large-selection checks for 1.7."""
import sys,json,time
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector
addon_utils.enable('better_item')
from better_item import distribution as d,distribution_preview as live,placement,frames,native_refs,arrange
from better_item.math_core import BetterItemError
ctx=bpy.context;result={}
def reset():
    live.forget();bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    s=ctx.scene.better_item;s.frames.clear();s.arrange_reference_mode='INDIVIDUAL';s.arrange_orientation='GLOBAL';s.arrange_origin='GLOBAL'
    s.distribution_start_override=False;s.distribution_method='ENDPOINT';s.endpoint_path='SEGMENT';s.distribution_end.mode='MANUAL';s.distribution_end.position=(20,0,0)
    s.distribution_mode='ORIGINS';s.axes=(True,False,False);s.arrange_on_axis=False;s.distribution_legacy_range=False;return s
def cube(name,x):bpy.ops.mesh.primitive_cube_add(location=(x,0,0));ctx.object.name=name;return ctx.object
def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    ctx.view_layer.objects.active=objects[0];ctx.view_layer.update()
def fails(fn,code):
    try:fn()
    except BetterItemError as exc:assert code in str(exc),str(exc);return
    raise AssertionError('Expected '+code)
s=reset();a=cube('Position dependent',5);b=cube('Static',10);select([a,b])
group=bpy.data.node_groups.new('Object Info dependency','GeometryNodeTree');group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
inp=group.nodes.new('NodeGroupInput');out=group.nodes.new('NodeGroupOutput');info=group.nodes.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE'
source=bpy.data.objects.new('External Info source',None);ctx.scene.collection.objects.link(source);source.location.x=30;info.inputs['Object'].default_value=source
move=group.nodes.new('GeometryNodeSetPosition');factor=group.nodes.new('ShaderNodeVectorMath');factor.operation='SCALE';factor.inputs['Scale'].default_value=.1
group.links.new(inp.outputs['Geometry'],move.inputs['Geometry']);group.links.new(info.outputs['Location'],factor.inputs[0]);group.links.new(factor.outputs['Vector'],move.inputs['Offset']);group.links.new(move.outputs['Geometry'],out.inputs['Geometry'])
a.modifiers.new('Dependent evaluated geometry','NODES').node_group=group
before={o:tuple(o.location) for o in (a,b)}
for basis in ('BOUNDS_CENTER','SURFACE','VOLUME','GEOMETRY'):
    s.distribution_mode=basis;ctx.view_layer.update();fails(lambda:d.apply(ctx,[a,b]),'BI-G003');assert before=={o:tuple(o.location) for o in (a,b)}
result['object_info_dependency_bases']=4
# Cache tracks evaluated geometry edits, shape keys and same-frame modifier state.
s=reset();obj=cube('Cached centroid',0);obj.shape_key_add(name='Basis');shape=obj.shape_key_add(name='Asymmetric')
for i,p in enumerate(shape.data):
    if p.co.x>0:p.co.z+=.2+i*.1
checks=0
for value in (0,.5,1,.2,0):
    shape.value=value;ctx.view_layer.update()
    for basis in ('BOUNDS_CENTER','SURFACE','VOLUME'):
        actual=placement.offset(obj,basis);expected=placement._offset(obj,basis);assert np.allclose(actual,expected,rtol=2e-7,atol=1e-9);checks+=1
array=obj.modifiers.new('Array','ARRAY');array.count=3;ctx.view_layer.update()
for show in (True,False,True):
    array.show_viewport=show;ctx.view_layer.update()
    for basis in ('BOUNDS_CENTER','SURFACE','VOLUME'):
        assert np.allclose(placement.offset(obj,basis),placement._offset(obj,basis),rtol=2e-7,atol=1e-9);checks+=1
result['centroid_cache_checks']=checks
# Missing/new/deleted sources remain normal input states, without invalid enum IDs.
s=reset();a=cube('A',2);b=cube('B',8);select([a,b]);f=frames.create(ctx,'Endpoint',Vector((20,0,0)),Matrix.Identity(3))
s.distribution_end.mode='FRAME';s.distribution_end.frame=f.uid;s.distribution_start.frame=f.uid
assert bpy.ops.better_item.frame(action='REMOVE')=={'FINISHED'}
assert s.distribution_end.frame=='NONE' and s.distribution_start.frame=='NONE';before={o:tuple(o.location) for o in (a,b)}
fails(lambda:d.apply(ctx,[a,b]),'BI-F002');assert before=={o:tuple(o.location) for o in (a,b)}
result['deleted_frame_choices_reset']=True
# Native Bounding Box Center uses origins; geometry displacement does not move it.
for v in b.data.vertices:v.co.x+=100
b.data.update();ctx.view_layer.update();assert np.allclose(native_refs.pivot(ctx,'BOUNDING_BOX_CENTER'),(5,0,0))
assert np.allclose(native_refs.pivot(ctx,'MEDIAN_POINT'),(5,0,0));result['native_bbox_semantics']=True
# Invalid context capture leaves the existing frame intact and provides a diagnostic.
f=frames.create(ctx,'Capture fails',Vector((3,4,5)),Matrix.Identity(3));a.rotation_euler=(0,np.pi/2,0);ctx.view_layer.update()
previous=tuple(f.rotation);f.reference_orientation='GIMBAL'
assert tuple(f.rotation)==previous and 'BI-F005' in f['reference_capture_error'];assert f.rotation_mode=='MANUAL'
f.reference_orientation='GLOBAL';assert not f.get('reference_capture_error');result['invalid_capture_is_non_destructive']=True
# An operation may fit each rounded point but still lose its small interval.
s=reset();s.distribution_method='OFFSET';s.spacing=100
anchor=bpy.data.objects.new('Large anchor',None);ctx.scene.collection.objects.link(anchor);anchor.location.x=1e9
a=cube('Unresolved interval A',1e9+1024);b=cube('Unresolved interval B',1e9+2048);select([a,b]);s.arrange_origin='OBJECT';s.arrange_origin_object=anchor
before={o:tuple(o.location) for o in (a,b)};fails(lambda:d.apply(ctx,[a,b]),'BI-E003');assert before=={o:tuple(o.location) for o in (a,b)}
result['point_spacing_precision_rollback']=True
# A live inspection session needs a stable start rather than a moving mean.
s=reset();a=cube('Context A',1);b=cube('Context B',6);select([a,b]);s.arrange_origin='PIVOT';s.reference_pivot='MEDIAN_POINT'
fails(lambda:live.begin(ctx),'BI-L001');assert not live.active(ctx.scene)
result['contextual_start_preview_guard']=True
# A timed scene with different shapes; verify gaps independently from the planner.
s=reset();s.distribution_mode='GEOMETRY';s.distribution_end.position=(1000,0,0)
objects=[cube('Batch%03d'%i,4+i*4) for i in range(200)]
for i,o in enumerate(objects):o.scale.x=.5+.25*(i%3)
select(objects);start=time.perf_counter();_,info=d.apply(ctx,objects);elapsed=time.perf_counter()-start
intervals=[]
for o in objects:
    matrix=np.asarray(o.matrix_world);coords=np.asarray([v.co[:] for v in o.data.vertices]);x=coords@matrix[0,:3]+matrix[0,3];intervals.append((x.min(),x.max()))
intervals.sort();errors=[abs(right[0]-left[1]-info['spacing']) for left,right in zip(intervals,intervals[1:])]
assert max(errors)<1e-4,max(errors)
assert len(placement._point_cache)<=64
result['geometry_endpoint_200']={'seconds_plan_apply_verify':elapsed,'maximum_gap_error_blender_units':max(errors)}
# Removing a target during preview can still be cancelled; no dangling session.
live.begin(ctx);s.distribution_end.position=(1200,0,0)
deleted=objects[-1];bpy.data.objects.remove(deleted,do_unlink=True);live.finish(ctx,cancel=True);assert not live.active(ctx.scene)
result['preview_deleted_target_cancel']=True
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('170 EDGE PASSED',json.dumps(result))
