"""Distribution contracts and independent geometry checks in actual Blender."""
import sys,json,time,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector,Euler
addon_utils.enable('better_item')
from better_item import distribution as d,distribution_preview as live,placement,frames,arrange,engine,native_refs
from better_item.math_core import BetterItemError
ctx=bpy.context;result={}
def reset():
    live.forget()
    if ctx.object and ctx.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    s=ctx.scene.better_item;s.frames.clear();s.arrange_reference_mode='INDIVIDUAL';s.arrange_orientation='GLOBAL'
    s.arrange_origin='GLOBAL';s.arrange_on_axis=False;s.axes=(True,False,False)
    s.distribution_method='OFFSET';s.distribution_mode='ORIGINS';s.distribution_start_override=False;s.distribution_legacy_range=False
    s.distribution_end.mode='MANUAL';s.distribution_end.position=(10,0,0);s.minimum_distance_mm=.00001
    ctx.scene.unit_settings.scale_length=1;arrange.clear_error();return s
def cube(name,x=0,width=2):
    bpy.ops.mesh.primitive_cube_add(location=(x,0,0));o=ctx.object;o.name=name;o.scale.x=width/2;return o
def empty(name,position):
    o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);o.location=position;return o
def select(objects,active=None):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    ctx.view_layer.objects.active=active or objects[0];ctx.view_layer.update()
def near(a,b,tol=2e-5):assert np.allclose(a,b,atol=tol,rtol=2e-6),(a,b)
def failure(fn,code):
    try:fn()
    except BetterItemError as exc:assert code in str(exc),str(exc);return
    raise AssertionError('Expected '+code)
# Point placement and interval placement have intentionally different results.
s=reset();objects=[cube('Width'+str(i),10+i*400,width) for i,width in enumerate((100,200,300))]
select(objects);s.distribution_method='ENDPOINT';s.distribution_end.position=(1000,0,0)
d.apply(ctx,objects);near([o.location.x for o in objects],[0,500,1000])
for i,o in enumerate(objects):o.location.x=10+i*400
failure(lambda:d.endpoint_plan(ctx,objects,basis='GEOMETRY'),'BI-E002');result['point_endpoint_and_retired_interval_rejection']=True
# Segment uses two positions even with no valid shared Orientation.
cases=0
for basis in ('ORIGINS','BOUNDS_CENTER','SURFACE','VOLUME'):
    for vector in ((30,15,-9),(-30,6,12)):
        s=reset();objects=[cube('Segment'+str(i),i*5+1) for i in range(4)]
        for i,o in enumerate(objects):o.rotation_euler=(i*.1,i*.2,-i*.15);o.scale=(-1 if i%2 else 1,1+i*.1,1)
        s.distribution_method='ENDPOINT';s.distribution_mode=basis;s.arrange_orientation='REFERENCE';s.arrange_object=None
        s.distribution_end.position=vector;s.axes=(False,False,False);select(objects)
        originals={o.name:(tuple(o.rotation_euler),tuple(o.scale),o.data.as_pointer()) for o in objects}
        _,info=d.apply(ctx,objects);u=np.asarray(vector,dtype=float);length=np.linalg.norm(u);u/=length
        if basis!='GEOMETRY':
            for i,o in enumerate(objects):near(np.asarray(o.matrix_world.translation)+placement.offset(o,basis),u*length*i/3)
        else:
            intervals=[]
            for o in objects:
                evaluated=o.evaluated_get(ctx.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
                try:
                    world=np.asarray(o.matrix_world);coords=np.asarray([v.co[:] for v in mesh.vertices]);projected=(coords@world[:3,:3].T+world[:3,3])@u
                    intervals.append((projected.min(),projected.max()))
                finally:evaluated.to_mesh_clear()
            intervals.sort();near(intervals[0][0],0);near(intervals[-1][1],length)
            near([b[0]-a[1] for a,b in zip(intervals,intervals[1:])],[info['spacing']]*3)
        assert all(originals[o.name]==(tuple(o.rotation_euler),tuple(o.scale),o.data.as_pointer()) for o in objects);cases+=1
result['all_bases_oblique_reversed_segment']=cases
# Fixed selected objects occupy endpoint slots; cursor needs no endpoint object.
s=reset();a=cube('Start',0);b=cube('End',10);c=cube('Middle1',2);e=cube('Middle2',7);objects=[a,c,e,b]
s.arrange_origin='PIVOT';s.reference_pivot='ACTIVE_ELEMENT';s.distribution_end.mode='OBJECT';s.distribution_end.object=b
s.distribution_method='ENDPOINT';select(objects,a);d.apply(ctx,objects);near([o.location.x for o in objects],[0,10/3,20/3,10])
ctx.scene.cursor.location=(0,12,0);s.distribution_end.mode='CURSOR';select([a,c,e],a);d.apply(ctx,[a,c,e]);near(c.location,(0,6,0));near(e.location,(0,12,0));near(a.location,(0,0,0))
result['selected_anchors_and_cursor']=True
# Frame Location is independent from its missing Orientation. Override Start too.
s=reset();objects=[cube('Frame target'+str(i),2+i*4) for i in range(3)];select(objects)
frame=frames.create(ctx,'Only Location',Vector((5,5,5)),Matrix.Identity(3));frame.rotation_mode='OBJECT';frame.rotation_source=None
s.distribution_method='ENDPOINT';s.distribution_start_override=True;s.distribution_start.mode='MANUAL';s.distribution_start.position=(1,1,1)
s.distribution_end.mode='FRAME';s.distribution_end.frame=frame.uid;d.apply(ctx,objects)
near([tuple(o.location) for o in objects],[(1,1,1),(3,3,3),(5,5,5)]);result['independent_frame_components_and_override']=True
# Axis path projects End and preserves the selected source rotation.
s=reset();objects=[cube('Axis target'+str(i),2+i*4) for i in range(3)];select(objects)
source=empty('Axes',(0,0,0));source.rotation_euler.z=np.pi/2;s.arrange_orientation='REFERENCE';s.arrange_object=source
s.distribution_method='ENDPOINT';s.endpoint_path='AXIS';s.distribution_end.position=(10,8,3);d.apply(ctx,objects)
near([tuple(o.location) for o in objects],[(0,0,0),(0,4,0),(0,8,0)]);result['reference_axis_projection']=True
# Centroids: a closed tetrahedron; area criterion differs from volume, mirror safe.
s=reset();mesh=bpy.data.meshes.new('Tetra');mesh.from_pydata([(0,0,0),(4,0,0),(0,2,0),(0,0,1)],[],[(0,2,1),(0,1,3),(0,3,2),(1,2,3)]);mesh.update()
obj=bpy.data.objects.new('Tetra',mesh);ctx.scene.collection.objects.link(obj);obj.rotation_euler=(.2,.3,.4);obj.scale=(-2,3,.5);ctx.view_layer.update()
linear=np.asarray(obj.matrix_world.to_3x3());near(placement.offset(obj,'VOLUME'),linear@np.array((1,.5,.25)))
coords=np.asarray([v.co[:] for v in mesh.vertices])@linear.T;facecoords=coords[np.asarray([(0,2,1),(0,1,3),(0,3,2),(1,2,3)])]
areas=np.linalg.norm(np.cross(facecoords[:,1]-facecoords[:,0],facecoords[:,2]-facecoords[:,0]),axis=1)
near(placement.offset(obj,'SURFACE'),np.average(facecoords.mean(axis=1),axis=0,weights=areas))
mesh.polygons[0].flip();mesh.update();ctx.view_layer.update();failure(lambda:placement.offset(obj,'VOLUME'),'BI-P003')
result['surface_volume_oracle_and_open_volume_rejection']=True
# Insufficient space and dependent endpoints reject atomically.
s=reset();objects=[cube('Too wide'+str(i),4+i*4) for i in range(3)];select(objects);s.distribution_method='ENDPOINT';s.distribution_mode='ORIGINS';s.distribution_end.position=(3,0,0)
before={o:tuple(o.location) for o in objects};failure(lambda:d.endpoint_plan(ctx,objects,basis='GEOMETRY'),'BI-E002');assert before=={o:tuple(o.location) for o in objects}
s.distribution_mode='ORIGINS';source=empty('Dependent End',(20,0,0));source.parent=objects[0];s.distribution_end.mode='OBJECT';s.distribution_end.object=source;ctx.view_layer.update()
failure(lambda:d.apply(ctx,objects),'BI-G004');assert before=={o:tuple(o.location) for o in objects};result['retired_basis_and_dependency_rejections']=True
# Bounds Center Offset with displaced origins and an explicit geometric anchor.
s=reset();a=cube('Offset key',0);b=cube('Offset point',5)
for v in b.data.vertices:v.co.x+=3
b.data.update();s.arrange_origin='OBJECT';s.arrange_origin_object=a;s.distribution_mode='BOUNDS_CENTER';s.spacing=10
select([a,b],a);d.apply(ctx,[a,b]);near(b.location.x,7);near(np.asarray(b.matrix_world.translation)+placement.offset(b,'BOUNDS_CENTER'),(10,0,0))
status,value=d.inspect_spacing(ctx,[a,b]);assert status=='UNIFORM';near(value,10);result['offset_centers_and_measured_spacing']=True
# Selection is not required to be uniform; beginning preview does not move it.
s=reset();objects=[cube('Preview'+str(i),x) for i,x in enumerate((3,8,19))];select(objects)
assert d.inspect_spacing(ctx,objects)[0]=='MIXED';initial={o:tuple(o.location) for o in objects}
live.begin(ctx);assert initial=={o:tuple(o.location) for o in objects}
s.spacing=2;near([o.location.x for o in objects],[2,4,6]);s.spacing=3;near([o.location.x for o in objects],[3,6,9]);s.spacing=-3;near([o.location.x for o in objects],[-3,-6,-9])
live.finish(ctx,cancel=True);assert initial=={o:tuple(o.location) for o in objects}
live.begin(ctx);s.spacing=4;live.finish(ctx);near([o.location.x for o in objects],[4,8,12]);assert not live.active(ctx.scene)
result['preview_initial_order_cancel_confirm']=True
# Context sources in Frame creation are captures, not live selection pointers.
s=reset();a=cube('Capture A',0);b=cube('Capture B',10);select([a,b],a)
frame=frames.create(ctx,'Capture',Vector(),Matrix.Identity(3));frame.reference_location='MEDIAN_POINT'
assert frame.position_mode=='MANUAL';near(frame.position,(5,0,0));select([a]);a.location.x=4;ctx.view_layer.update();near(frames.frame_origin(frame),(5,0,0))
frame.reference_orientation='GIMBAL';assert frame.rotation_mode=='MANUAL'
result['frame_context_capture']=True
# Settings and endpoint sources persist as ordinary .blend data.
s.distribution_method='ENDPOINT';s.distribution_start_override=True;s.distribution_start.position=(1,2,3);s.distribution_end.mode='FRAME';s.distribution_end.frame=frame.uid
with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
    path=str(Path(td)/'distribution170.blend');bpy.ops.wm.save_as_mainfile(filepath=path);bpy.ops.wm.open_mainfile(filepath=path)
    s=bpy.context.scene.better_item;assert s.distribution_method=='ENDPOINT' and s.distribution_end.mode=='FRAME';near(s.distribution_start.position,(1,2,3));assert not live.active(bpy.context.scene)
result['persistence']=True
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('170 CONTRACTS PASSED',json.dumps(result))
