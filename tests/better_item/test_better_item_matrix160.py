"""Deterministic feature matrix for 1.6.0, independent from the 1.5 regression grid."""
import sys,itertools,random,json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector,Euler
addon_utils.enable('better_item')
from better_item import frames,arrange,geometry_arrange as geom,engine,orientation,transform_view as v
ctx=bpy.context;rng=random.Random(1600)
def cube(name):bpy.ops.mesh.primitive_cube_add();ctx.object.name=name;return ctx.object
def empty(name):o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);return o
def select(objects,active):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    ctx.view_layer.objects.active=active
def near(a,b,tol=2e-5):assert np.allclose(a,b,atol=tol,rtol=2e-6),(a,b)
key=cube('Geometry key');objects=[cube('Matrix'+str(i)) for i in range(4)];objects[3].data=objects[0].data
for point in objects[0].data.vertices:point.co+=Vector((.3,-.2,.4))
objects[0].data.update();parent=empty('Position parent');parent.rotation_euler=(.3,.1,-.2);parent.scale=(1.4,.8,1.2)
frame=frames.create(ctx,'Matrix axes',Vector((1,-2,3)),Matrix.Identity(3));s=ctx.scene.better_item;s.arrange_reference_mode='FRAME';s.arrange_reference_frame=frame.uid
masks=[tuple(bool(mask&(1<<i)) for i in range(3)) for mask in range(1,8)]
bases=(Euler((.3,.2,.4)).to_matrix(),Matrix(((1,.3,0),(0,1,.2),(0,0,1))))
geometric=0
for use_key,basis,mask,scale,direction,gap_mm in itertools.product((False,True),bases,masks,(1.,.001),(1,-1),(0.,.5)):
    if gap_mm==0 and direction<0:continue  # zero always uses the positive side
    ctx.scene.unit_settings.scale_length=scale;frames.store_axes(frame,basis)
    frame.position_mode='OBJECT' if use_key else 'MANUAL';frame.position_source=key if use_key else None
    key.location=(1,-2,3);key.rotation_euler=(.2,.1,.3);key.scale=(1.2,.7,1)
    for i,o in enumerate(objects):
        o.parent=parent if i%2 else None;o.location=tuple(rng.uniform(2,12)+i*3 for _ in range(3))
        o.rotation_euler=tuple(rng.uniform(-.7,.7) for _ in range(3));o.scale=(-1 if i%2 else 1,rng.uniform(.6,1.4),rng.uniform(.6,1.4))
    ctx.view_layer.update();moving=[key,*objects] if use_key else objects;select(moving,key if use_key else objects[0])
    orig={o.name:tuple(o.matrix_world.translation) for o in moving};original={o.name:(tuple(o.rotation_euler),tuple(o.scale),o.data.as_pointer()) for o in objects}
    gap=gap_mm/(1000*scale)
    targets,verify=geom.plan(ctx,moving,orig,mask,spacing=gap*direction)
    engine.apply_world_positions(moving,targets,verify=verify)
    d=np.asarray(basis,dtype=np.float64);d/=np.linalg.norm(d,axis=0)
    for axis,enabled in enumerate(mask):
        if not enabled:continue
        intervals=[]
        for obj in moving:
            lo,hi=v.projected_bounds(obj,basis);center=d.T@np.asarray(obj.matrix_world.translation)
            intervals.append((center[axis]+lo[axis],center[axis]+hi[axis]))
        intervals.sort();actual=[b[0]-a[1] for a,b in zip(intervals,intervals[1:])]
        near(actual,[gap]*len(actual))
    for o in objects:assert original[o.name]==(tuple(o.rotation_euler),tuple(o.scale),o.data.as_pointer())
    geometric+=1
# Return to ordinary units and independent sources for the orientation matrix.
ctx.scene.unit_settings.scale_length=1;parent.scale=(1.5,1.5,1.5)
orders=('XYZ','XZY','YXZ','YZX','ZXY','ZYX');rotation_cases=0
for order,use_object,mode,mask in itertools.product(orders,(False,True),('MATCH','SET'),((True,False,False),(False,True,True),(True,True,True))):
    key.rotation_euler=(.2,-.3,.4);key.scale=(-1,1,1)
    s.arrange_reference_mode='INDIVIDUAL' if use_object else 'FRAME';s.arrange_object=key;s.arrange_orientation='REFERENCE'
    frame.rotation_mode='MANUAL';frames.store_axes(frame,Euler((.2,-.3,.4)).to_matrix())
    for i,o in enumerate(objects):
        o.rotation_mode=('XYZ','QUATERNION','AXIS_ANGLE','ZYX')[i];q=Euler(tuple(rng.uniform(-.7,.7) for _ in range(3))).to_quaternion()
        if o.rotation_mode=='QUATERNION':o.rotation_quaternion=q
        elif o.rotation_mode=='AXIS_ANGLE':axis,angle=q.to_axis_angle();o.rotation_axis_angle=(angle,*axis)
        else:o.rotation_euler=q.to_euler(o.rotation_mode)
        o.location=(i+1,i+2,i+3)
    ctx.view_layer.update();select(objects,objects[0]);ref=orientation.rotation(key) if use_object else frames.frame_axes(frame)
    angles=(.15,-.25,.35);expected={};positions={}
    for obj in objects:
        old=tuple((ref.transposed()@orientation.rotation(obj)).to_euler(order));goal=(0,0,0) if mode=='MATCH' else tuple(angles[i] if mask[i] else old[i] for i in range(3))
        expected[obj.name]=ref@Euler(goal,order).to_matrix();positions[obj.name]=tuple(obj.matrix_world.translation)
    arrange.align_orientations(ctx,objects,mode=mode,axes=mask,angles=angles,order=order)
    for obj in objects:near(orientation.rotation(obj),expected[obj.name]);near(obj.matrix_world.translation,positions[obj.name])
    rotation_cases+=1
result={'geometry_combinations':geometric,'rotation_batches':rotation_cases,'rotation_targets_checked':rotation_cases*len(objects),'geometry_axes_masks':7,'unit_scales':[1,.001],'zero_and_positive_gaps':True,'oblique_and_rotated_references':True,'shared_meshes_and_parented_targets':True}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('160 FEATURE MATRIX PASSED',json.dumps(result))
