"""1.6 Geometry Bounds, batch orientations, diagnostics and persistence."""
import sys,math,random,json,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector,Euler
from types import SimpleNamespace
addon_utils.enable('better_item')
import better_item as addon
from better_item import engine,arrange,geometry_arrange as geom,frames,orientation,transform_view as v,diagnostics
from better_item.math_core import BetterItemError,ReferencePending
ctx=bpy.context;rng=random.Random(160);results={}
def empty(name):
    o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);return o
def cube(name):
    bpy.ops.mesh.primitive_cube_add();ctx.object.name=name;return ctx.object
def select(objects,active):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    ctx.view_layer.objects.active=active
def reset():
    if ctx.object and ctx.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    ctx.scene.better_item.frames.clear();v.clear_cache();arrange.clear_error()
    s=ctx.scene.better_item;s.arrange_reference_mode='INDIVIDUAL';s.arrange_orientation='GLOBAL';s.arrange_origin='GLOBAL';s.arrange_on_axis=False
def near(a,b,tol=2e-5):assert np.allclose(a,b,atol=tol,rtol=2e-6),(a,b)
def fails(fn,code):
    try:fn()
    except BetterItemError as e:assert code in str(e),str(e);return e
    raise AssertionError('Expected '+code)
def distribute(objects,axes=(True,False,False),spacing=0,reference='AUTO'):
    ctx.view_layer.update();origins={o.name:tuple(o.matrix_world.translation) for o in objects}
    targets,verify=geom.plan(ctx,objects,origins,axes,reference,spacing=spacing)
    engine.apply_world_positions(objects,targets,verify=verify)
def bounds(obj,d):
    low,high=v.projected_bounds(obj,Matrix(d));c=np.asarray(d,dtype=np.float64);c/=np.linalg.norm(c,axis=0)
    p=c.T@np.asarray(obj.matrix_world.translation)
    return p+low,p+high
reset();key=cube('Key');b=cube('B');c=cube('C');s=ctx.scene.better_item
s.arrange_origin='OBJECT';s.arrange_origin_object=key
for spacing in (0,.05,-.05,-2.):
    direction=-1 if spacing<0 else 1;gap=abs(spacing)
    key.location=(0,0,0);key.scale=(1,1,1);b.location=(4,0,0);b.scale=(2,1,1);c.location=(10,0,0);c.scale=(3,1,1)
    select([key,b,c],key);before=key.matrix_world.copy();distribute([key,b,c],spacing=spacing)
    near(key.matrix_world,before);near((b.location.x,c.location.x),(direction*(3+gap),direction*(8+2*gap)))
results['key_geometry']=4
# Oriented/oblique axes, vertex offsets, signed scale, shared data and parents.
reset();ref=empty('Reference');parent=empty('Parent');parent.rotation_euler=(.2,-.3,.1);parent.scale=(1.2,.8,1.5)
objects=[cube('Part'+str(i)) for i in range(4)];s=ctx.scene.better_item
objects[-1].data=objects[0].data
for point in objects[0].data.vertices:point.co+=Vector((.1,.2,.3))
objects[0].data.update()
array=objects[1].modifiers.new('Evaluated Array','ARRAY');array.count=2
data_ids=[o.data.as_pointer() for o in objects];modifier_counts=[len(o.modifiers) for o in objects]
f=frames.create(ctx,'Geometry axes',Vector((1,2,3)),Matrix.Identity(3));s.arrange_reference_mode='FRAME';s.arrange_reference_frame=f.uid
cases=0
for basis in (Euler((.3,.2,.6)).to_matrix(),Matrix(((1,.3,0),(0,1,.2),(0,0,1)))):
    frames.store_axes(f,basis)
    for direction in (1,-1):
        for axes in ((True,False,False),(True,True,True)):
            for i,o in enumerate(objects):
                o.parent=parent if i%2 else None;o.location=(i*5+2,i*7+1,i*9+3)
                o.rotation_euler=(i*.2,i*.1,-i*.17);o.scale=(-1 if i%2 else 1,1+i*.1,1)
            ctx.view_layer.update();select(objects,objects[0]);before={o.name:(tuple(o.scale),tuple(o.rotation_euler),tuple(tuple(p.co) for p in o.data.vertices)) for o in objects}
            distribute(objects,axes=axes,spacing=.02*direction)
            unit=np.asarray(basis,dtype=np.float64);unit/=np.linalg.norm(unit,axis=0)
            for axis,enabled in enumerate(axes):
                if not enabled:continue
                intervals=sorted((bounds(o,basis)[0][axis],bounds(o,basis)[1][axis]) for o in objects)
                near([right[0]-left[1] for left,right in zip(intervals,intervals[1:])],[.02]*3)
            for o in objects:assert before[o.name]==(tuple(o.scale),tuple(o.rotation_euler),tuple(tuple(p.co) for p in o.data.vertices))
            assert [o.data.as_pointer() for o in objects]==data_ids and [len(o.modifiers) for o in objects]==modifier_counts
            cases+=1
# Offset origins must use min/max, not width/2.
reset();key=cube('Key');target=cube('Offset');target.location=(10,0,0)
for p in target.data.vertices:p.co.x+=3
target.data.update();s=ctx.scene.better_item;s.arrange_origin='OBJECT';s.arrange_origin_object=key
select([key,target],key);distribute([key,target]);near(target.location.x,-1);near(bounds(target,Matrix.Identity(3))[0][0],1)
# BBox mode packs from the outer selection edge, without a fixed far endpoint.
reset();objects=[cube('Packed'+str(i)) for i in range(3)]
for i,o in enumerate(objects):o.location=(i*5,0,0)
s=ctx.scene.better_item;s.arrange_origin='PIVOT';s.reference_pivot='BOUNDING_BOX_CENTER';select(objects,objects[0]);distribute(objects)
near([o.location.x for o in objects],[0,2,4]);results['projected_bounds']=cases+2
# A sub-precision positive gap and unrepresentable large-coordinate placement fail atomically.
reset();key=cube('Key');target=cube('Target');s=ctx.scene.better_item;s.arrange_origin='OBJECT';s.arrange_origin_object=key;select([key,target],key)
for x,gap in ((0,1e-10),(1e9,0)):
    key.location=(x,0,0);target.location=(x+128,0,0);ctx.view_layer.update();before=(tuple(key.location),tuple(target.location))
    fails(lambda:distribute([key,target],spacing=gap),'BI-G002');assert (tuple(key.location),tuple(target.location))==before
target.lock_location=(True,False,False);key.location=(0,0,0);target.location=(5,0,0);ctx.view_layer.update();before=tuple(target.location)
fails(lambda:distribute([key,target]),'BI-T003');assert tuple(target.location)==before;target.lock_location=(False,False,False)
results['geometry_rollback']=3
# Rotation alignment uses Scene references without writing per-object Transform settings.
reset();key=empty('Rotation Key');key.rotation_euler=(.3,-.2,.5)
objects=[cube('Rotated'+str(i)) for i in range(3)];parent=empty('Rotation Parent');parent.rotation_euler=(.1,.2,.3);parent.scale=(1.5,1.5,1.5)
s=ctx.scene.better_item;s.arrange_orientation='REFERENCE';s.arrange_object=key
for i,o in enumerate(objects):
    o.parent=parent if i%2 else None;o.location=(i+1,i+2,i+3);o.rotation_euler=(.1*i,.2*i,.3*i);o.scale=(-1 if i%2 else 1,1,1)
    o.better_item.orientation='SAVED';o.better_item.orientation_frame='NONE'
ctx.view_layer.update();select([key,*objects],key);positions={o.name:tuple(o.matrix_world.translation) for o in objects};keys={o.name:dict(o.better_item.items()) for o in objects};scales={o.name:tuple(o.scale) for o in objects}
arrange.align_orientations(ctx,[key,*objects])
for o in objects:
    near(orientation.rotation(o),orientation.rotation(key));near(o.matrix_world.translation,positions[o.name]);assert tuple(o.scale)==scales[o.name];assert dict(o.better_item.items())==keys[o.name]
# Partial angles are relative to one explicit reference and Euler order.
for order in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX'):
    for i,o in enumerate(objects):o.rotation_mode='QUATERNION' if i==1 else 'XYZ';o.rotation_euler=(.2,.3,.4)
    ctx.view_layer.update();reference=orientation.rotation(key);old={o.name:tuple((reference.transposed()@orientation.rotation(o)).to_euler(order)) for o in objects}
    arrange.align_orientations(ctx,[key,*objects],mode='SET',axes=(False,True,False),angles=(0,.25,0),order=order)
    for o in objects:
        expected=list(old[o.name]);expected[1]=.25
        near(orientation.rotation(o),reference@Euler(expected,order).to_matrix());near(o.matrix_world.translation,positions[o.name])
# Later-object failure restores the entire selection, including earlier successes.
objects[-1].lock_rotation=(True,True,True);snap={o.name:v._snapshot(o) for o in [key,*objects]}
fails(lambda:arrange.align_orientations(ctx,[key,*objects]),'BI-')
for o in [key,*objects]:assert v._snapshot(o)==snap[o.name]
objects[-1].lock_rotation=(False,False,False);results['orientation']=8
# Missing sources are typed pending and remain string-compatible for technical logs.
pending=ReferencePending('[BI-F002] Choose an object for Location.');message=diagnostics.Diagnostic(pending)
assert message.pending and message.severity=='INFO' and 'BI-F002' in message
assert diagnostics.Diagnostic(BetterItemError('[BI-T003] Unlock Local X.')).severity=='WARNING'
assert diagnostics.Diagnostic(RuntimeError('unexpected')).severity=='ERROR'
ctx.active_object.better_item.orientation='REFERENCE';ctx.active_object.better_item.orientation_object=None
error=fails(lambda:frames.object_axes(ctx,ctx.active_object),'BI-F002');assert isinstance(error,ReferencePending)
# Full Frame rotation works even when its independent Location is not configured.
f=frames.create(ctx,'Half configured',Vector(),Euler((.1,.2,.3)).to_matrix());f.position_mode='OBJECT';f.position_source=None
s.arrange_reference_mode='FRAME';s.arrange_reference_frame=f.uid
arrange.align_orientations(ctx,objects)
for o in objects:near(orientation.rotation(o),frames.frame_axes(f))
class Layout:
    def __init__(self,events=None):self.events=[] if events is None else events
    def __setattr__(self,key,value):
        if key=='alert' and value and hasattr(self,'events'):self.events.append(('red',True))
        object.__setattr__(self,key,value)
    def row(self,**kw):return Layout(self.events)
    def column(self,**kw):return Layout(self.events)
    def split(self,**kw):return Layout(self.events)
    def box(self):return Layout(self.events)
    def label(self,**kw):self.events.append(('label',kw.get('text','')))
    def prop(self,owner,name,**kw):self.events.append(('prop',name))
    def operator(self,*args,**kw):return SimpleNamespace()
    def template_list(self,*args,**kw):return None
s.alignment_type='ORIENTATION';s.distribution_mode='GEOMETRY';s.show_solver=False
layout=Layout();addon.BETTERITEM_PT_alignment.draw(SimpleNamespace(layout=layout),ctx)
assert ('red',True) not in layout.events;assert ('prop','minimum_distance_mm') not in layout.events
assert any(event==('label','Setup needed') for event in layout.events)
assert ('prop','spacing') in layout.events
assert not any(event[0]=='prop' and event[1] in {'geometry_direction','direction','geometry_gap','gap'} for event in layout.events)
s.show_solver=True;layout=Layout();addon.BETTERITEM_PT_alignment.draw(SimpleNamespace(layout=layout),ctx);assert ('prop','minimum_distance_mm') in layout.events
layout=Layout();frames.BETTERITEM_PT_frames.draw(SimpleNamespace(layout=layout),ctx)
assert ('prop','rotation_x') in layout.events and ('prop','position_x') not in layout.events
assert ('red',True) not in layout.events
results['ux']='INFO pending, WARNING domain failures, ERROR unexpected; no red pending; solver collapsed; independent frame components'
# New configuration persists, with signed Origins spacing left intact.
s.spacing=-.25;s.orientation_action='SET';s.orientation_angles=(.1,.2,.3)
with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
    p=str(Path(td)/'features.blend');bpy.ops.wm.save_as_mainfile(filepath=p);bpy.ops.wm.open_mainfile(filepath=p)
    s=bpy.context.scene.better_item;assert s.distribution_mode=='GEOMETRY' and s.spacing==-.25;near(s.orientation_angles,(.1,.2,.3))
results['persistence']=True
Path(__file__).with_suffix('.results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('160 FEATURES PASSED',json.dumps(results))
