"""Finite regression grid for placement bases, references, units and anchors."""
import sys,json,itertools,random
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Euler,Vector
addon_utils.enable('better_item')
from better_item import distribution as d,placement,frames,distribution_preview as live,engine,arrange
ctx=bpy.context;rng=random.Random(170);s=ctx.scene.better_item
def cube(name):bpy.ops.mesh.primitive_cube_add();ctx.object.name=name;return ctx.object
def select(objects,active):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    ctx.view_layer.objects.active=active;ctx.view_layer.update()
def near(a,b,tol=2e-5):assert np.allclose(a,b,rtol=3e-6,atol=tol),(a,b)
objects=[cube('Piece%d'%i) for i in range(4)]
for i,obj in enumerate(objects):
    for vertex in obj.data.vertices:vertex.co+=Vector((.2*i,-.1*i,.15*i))
    obj.data.update()
parent=bpy.data.objects.new('Parent',None);ctx.scene.collection.objects.link(parent);parent.rotation_euler=(.2,.1,.3);parent.scale=(1.3,.8,1.1)
axis_source=bpy.data.objects.new('Axes',None);ctx.scene.collection.objects.link(axis_source);axis_source.rotation_euler=(.3,-.2,.4)
start_source=bpy.data.objects.new('Start proxy',None);ctx.scene.collection.objects.link(start_source)
s.arrange_reference_mode='INDIVIDUAL';s.arrange_origin='GLOBAL';s.arrange_on_axis=False
bases=[item[0] for item in placement.BASES];endpoint=offset=0
for basis,path,anchor_mode,unit,sign,parented in itertools.product([b for b in bases if b!='GEOMETRY'],('SEGMENT','AXIS'),('NONE','START','END','BOTH'),(1.,.001),(1,-1),(False,True)):
    scale=1/(1000*unit);ctx.scene.unit_settings.scale_length=unit
    s.distribution_method='ENDPOINT';s.distribution_mode=basis;s.endpoint_path=path;s.axes=(True,False,False)
    s.arrange_orientation='REFERENCE';s.arrange_object=axis_source
    start=np.array((2,3,4))*scale
    vector=np.array((45,25,-12),dtype=float)*scale*sign
    if path=='AXIS':vector=np.asarray(axis_source.rotation_euler.to_matrix().col[0])*50*scale*sign
    end=start+vector
    for i,obj in enumerate(objects):
        obj.parent=parent if parented and i%2 else None
        obj.rotation_euler=(i*.11,-i*.07,i*.13);obj.scale=tuple(np.array((-1 if i%2 else 1,.8+i*.1,1.1))*scale)
    ctx.view_layer.update()
    # Use evaluated translations after the parent transform, not unflushed assignments.
    for i,obj in enumerate(objects):obj.location=(i*8+5,2+i,3+i)
    ctx.view_layer.update()
    engine.apply_world_positions(objects,{obj.name:tuple(start+np.array((5+9*i,1+i,2+i))*scale) for i,obj in enumerate(objects)})
    s.distribution_start_override=True;s.distribution_start.mode='MANUAL';s.distribution_start.position=start
    s.distribution_end.mode='MANUAL';s.distribution_end.position=end
    if anchor_mode in {'START','BOTH'}:
        engine.apply_world_positions([objects[0]],{objects[0].name:tuple(start)})
        s.distribution_start.mode='OBJECT';s.distribution_start.object=objects[0]
    if anchor_mode in {'END','BOTH'}:
        engine.apply_world_positions([objects[-1]],{objects[-1].name:tuple(end)})
        s.distribution_end.mode='OBJECT';s.distribution_end.object=objects[-1]
    select(objects,objects[0]);fixed={o.name:tuple(o.matrix_world.translation) for o in objects if o in ((objects[0],) if anchor_mode=='START' else (objects[-1],) if anchor_mode=='END' else (objects[0],objects[-1]) if anchor_mode=='BOTH' else ())}
    state={o.name:(tuple(o.rotation_euler),tuple(o.scale),o.data.as_pointer()) for o in objects}
    try:_,info=d.apply(ctx,objects)
    except Exception:
        print('FAILED CASE',basis,path,anchor_mode,unit,sign,parented,flush=True);raise
    a=np.asarray(info['start']);b=np.asarray(info['end']);u=b-a;u/=np.linalg.norm(u)
    ordered=[bpy.data.objects[name] for name in info['order']]
    if basis=='GEOMETRY':
        intervals=[]
        for obj in ordered:
            world=np.asarray(obj.matrix_world,dtype=np.float64);coords=np.asarray([v.co[:] for v in obj.data.vertices])
            projection=(coords@world[:3,:3].T+world[:3,3]-a)@u;intervals.append((projection.min(),projection.max()))
        near([right[0]-left[1] for left,right in zip(intervals,intervals[1:])],[info['spacing']]*3,tol=1e-5*scale)
    else:
        points=[np.asarray(o.matrix_world.translation)+placement.offset(o,basis) for o in ordered]
        near([(point-a)@u for point in points],np.linspace((points[0]-a)@u,(points[-1]-a)@u,4))
    for o in objects:
        assert state[o.name]==(tuple(o.rotation_euler),tuple(o.scale),o.data.as_pointer())
        if o.name in fixed:near(o.matrix_world.translation,fixed[o.name])
    endpoint+=1
# Offset: signed intervals for points, physical gaps for geometry, no implicit BBox range.
s.distribution_start_override=False;s.arrange_origin='GLOBAL';s.distribution_method='OFFSET';s.arrange_on_axis=False
for basis,mask,sign,axis_kind in itertools.product(bases,range(1,8),(1,-1),('GLOBAL','REFERENCE')):
    ctx.scene.unit_settings.scale_length=1;s.distribution_mode=basis;s.arrange_orientation=axis_kind;s.arrange_object=axis_source
    s.axes=tuple(bool(mask&(1<<i)) for i in range(3));s.spacing=2.5*sign
    for i,obj in enumerate(objects):obj.parent=None;obj.location=(5+8*i,6+9*i,7+10*i);obj.scale=(-1 if i%2 else 1,1,1)
    select(objects,objects[0]);d.apply(ctx,objects)
    status,value=d.inspect_spacing(ctx,objects);assert status=='UNIFORM',(basis,mask,sign,axis_kind,status)
    near(value,2.5*sign);offset+=1
result={'endpoint_batches':endpoint,'offset_batches':offset,'bases':bases,'endpoint_paths':2,'anchor_patterns':4,'units':[1,.001],'parented_and_mirrored':True,'axis_masks':7}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('170 MATRIX PASSED',json.dumps(result))
