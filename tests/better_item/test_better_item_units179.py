"""Physical-unit qualification of the frozen runtime, with independent mm oracles.

RNA/Python lengths are Blender units; explicit unit text is parsed by Blender
before a LENGTH setter is called. Display units do not rescale stored geometry.
This test does not simulate mouse/keyboard input into a numeric widget.
"""
import contextlib
import io
import json
import math
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
import bpy
import numpy as np
from mathutils import Matrix,Vector
import better_item as addon
from better_item import distribution as d,frames,transform_view as tv
from better_item.math_core import BetterItemError

if not hasattr(bpy.types.Object,'better_item'):addon.register()
ctx=bpy.context
eps=float(np.finfo(np.float32).eps)
rows=[];errors=[]
configs=[(system,scale,display)
    for system,scales,displays in (
        ('METRIC',(1.,.001,.01,1e-6,1000.),('ADAPTIVE','METERS','MILLIMETERS')),
        ('IMPERIAL',(1.,.3048,.0254,.001),('FEET','INCHES')),
        ('NONE',(1.,.001,1000.),('ADAPTIVE',)))
    for scale in scales for display in displays]


def reset(config):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    u=ctx.scene.unit_settings
    u.system,u.scale_length,u.length_unit=config
    assert math.isclose(u.scale_length,config[1],rel_tol=eps)
    tv.clear_cache();d.clear_inspection()
    s=ctx.scene.better_item
    s.arrange_reference_mode='INDIVIDUAL';s.arrange_origin='GLOBAL'
    s.arrange_orientation='GLOBAL';s.arrange_on_axis=False;s.axes=(True,False,False)
    s.distribution_method='OFFSET';s.distribution_mode='ORIGINS'
    return 1000.*float(u.scale_length)


def empty(name,location=(0,0,0)):
    obj=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(obj)
    obj.location=location
    return obj


def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    ctx.view_layer.objects.active=objects[0];ctx.view_layer.update()


def cube(name,width_bu):
    # Define vertices directly, rather than resizing by Blender's unit display.
    vertices=[tuple(sign*width_bu/2 for sign in corner) for corner in (
        (-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),
        (1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1))]
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],[face[::-1] for face in ((0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6))])
    mesh.update()
    obj=bpy.data.objects.new(name,mesh);ctx.scene.collection.objects.link(obj)
    return obj


def world_bounds(obj,axes=np.eye(3)):
    evaluated=obj.evaluated_get(ctx.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    try:
        points=np.asarray([tuple(v.co) for v in mesh.vertices],dtype=np.float64)
        matrix=np.asarray(evaluated.matrix_world,dtype=np.float64)
        projected=(points@matrix[:3,:3].T+matrix[:3,3])@axes
        return projected.min(axis=0),projected.max(axis=0)
    finally:evaluated.to_mesh_clear()


def poses(objects):return [tuple(float(v) for line in o.matrix_world for v in line) for o in objects]


def case(kind,config,fn,*args):
    row={'kind':kind,'system':config[0],'requested_scale_length':config[1],'length_unit':config[2]}
    try:
        factor=reset(config);row.update(mm_per_blender_unit=factor,**fn(factor,*args));row['passed']=True
    except Exception:
        row.update(passed=False,traceback=traceback.format_exc());errors.append(row['traceback'])
    rows.append(row)


def parser_and_rna(factor):
    obj=empty('Addon');native=empty('Native control');select([obj])
    obj.better_item.transform_space='DEFAULT'
    properties=obj.better_item.bl_rna.properties
    for name in ('location_x','dimensions_x'):assert properties[name].unit=='LENGTH'
    assert properties['scale_x'].unit=='NONE'
    assert ctx.scene.better_item.bl_rna.properties['minimum_distance_mm'].unit=='NONE'
    system=ctx.scene.unit_settings.system
    samples=[]
    if system=='NONE':
        # NONE deliberately has no SI parser. Do not mistake this native
        # behavior for an addon conversion failure or promise physical mm UI.
        with contextlib.redirect_stderr(io.StringIO()):
            try:bpy.utils.units.to_value('NONE','LENGTH','2.5 mm')
            except ValueError:pass
            else:raise AssertionError('Expected native NONE parser to reject SI suffix')
        return {'explicit_mm_text_supported':False,'physical_units_declared':False,'rna_length_metadata':True}
    for mm in (1e-8,1e-5,.001,2.5,123.456,1e6):
        metres=bpy.utils.units.to_value(system,'LENGTH',format(mm,'.12g')+' mm')
        bu=metres/ctx.scene.unit_settings.scale_length
        obj.better_item.location_x=bu;native.location.x=bu;ctx.view_layer.update()
        assert obj.location.x==native.location.x
        measured=float(obj.matrix_world.translation.x)*factor
        error=abs(measured-mm)
        assert error<=8*eps*abs(mm),(mm,measured,error)
        samples.append({'requested_mm':mm,'actual_mm':measured,'absolute_error_mm':error})
    inch=bpy.utils.units.to_value(system,'LENGTH','1 in')*1000
    assert abs(inch-25.4)<=4*eps*25.4
    return {'explicit_mm_text_supported':True,'rna_matches_native':True,'one_inch_mm':inch,'samples':samples}


def transform_and_frame(factor):
    parent=empty('Parent',tuple(np.array((250.,-125.,50.))/factor))
    parent.rotation_euler=(.2,-.1,.3);parent.scale=(1.5,.8,1.1)
    obj=cube('Physical piece',2./factor);obj.parent=parent
    obj.location=tuple(np.array((8.,12.,4.))/factor)
    select([obj]);settings=obj.better_item
    frame=frames.create(ctx,'Millimetre reference',Vector(tuple(np.array((250.,-125.,50.))/factor)),Matrix.Rotation(.3,3,'Z'))
    settings.transform_space='REFERENCE';settings.reference_mode='FRAME';settings.reference_frame=frame.uid
    # Independently build a Z basis from the stored source angle.
    z=float(frame.rotation.z);c,s=math.cos(z),math.sin(z)
    axes=np.array(((c,-s,0),(s,c,0),(0,0,1)),dtype=np.float64)
    origin=np.asarray(frame.position,dtype=np.float64)
    before=np.linalg.solve(axes,np.asarray(obj.matrix_world.translation)-origin)
    desired=before.copy();desired[0]=12.345/factor
    settings.location_x=desired[0];ctx.view_layer.update()
    assert not addon._field_errors,addon._field_errors
    expected=(origin+axes@desired)*factor
    actual=np.asarray(obj.matrix_world.translation,dtype=np.float64)*factor
    error=float(np.max(np.abs(actual-expected)))
    # Source angle and parent/world products are native float32. Report the
    # actual error in mm, with a magnitude-dependent independent bound.
    bound=32*eps*float(np.max(np.abs(origin*factor)+np.abs(axes)@np.abs(desired*factor)))
    assert error<=bound,(error,bound)
    low,high=world_bounds(obj,axes);wanted=(high-low)*factor;wanted[0]=12.345
    settings.dimensions_x=wanted[0]/factor;ctx.view_layer.update()
    assert not addon._field_errors,addon._field_errors
    low,high=world_bounds(obj,axes);got=(high-low)*factor
    relative=np.abs(got-wanted)/wanted
    assert np.max(relative)<=40*eps,(wanted,got,relative)
    obj.better_item.transform_space='DEFAULT'
    obj.better_item.scale_x=1.25
    assert obj.scale.x==1.25
    frame.position_x=251.125/factor
    assert abs(float(frame.position.x)*factor-251.125)<=4*eps*251.125
    return {'parented_reference_location_error_mm':error,'location_rounding_bound_mm':bound,
            'requested_dimensions_mm':wanted.tolist(),'actual_dimensions_mm':got.tolist(),
            'dimension_relative_error':relative.tolist(),'dimensionless_scale_preserved':True,
            'frame_position_mm':float(frame.position.x)*factor,'affine_modifier_count':len(obj.modifiers)}


def minimum_separation(factor):
    objects=[empty(str(i),((10+10*i)/factor,0,0)) for i in range(3)]
    select(objects);s=ctx.scene.better_item;s.minimum_distance_mm=.01
    literal=float(s.minimum_distance_mm)
    s.spacing=.009/factor;before=poses(objects)
    try:d.apply(ctx,objects)
    except BetterItemError as exc:assert 'BI-D001' in str(exc),exc
    else:raise AssertionError('Below-minimum Offset accepted')
    assert poses(objects)==before
    s.spacing=.011/factor;d.apply(ctx,objects)
    gap=float(s.spacing)*factor
    positions=np.asarray([o.matrix_world.translation.x for o in objects])*factor
    assert np.max(np.abs(np.diff(np.r_[0.,positions])-gap))<=68*eps*gap
    for i,o in enumerate(objects):o.location=((10+10*i)/factor,0,0)
    ctx.view_layer.update();s.distribution_method='ENDPOINT';s.distribution_start_override=True
    s.distribution_start.mode='MANUAL';s.distribution_start.position=(0,0,0)
    s.distribution_end.mode='MANUAL';s.distribution_end.position=(.009/factor,0,0)
    before=poses(objects)
    try:d.apply(ctx,objects)
    except BetterItemError as exc:assert 'BI-E001' in str(exc),exc
    else:raise AssertionError('Below-minimum Endpoint length accepted')
    assert poses(objects)==before
    s.distribution_end.position=(.011/factor,0,0);d.apply(ctx,objects)
    return {'minimum_mm_literal':literal,'below_minimum_atomic_rejections':2,'above_minimum_acceptances':2}


def display_changes(factor):
    obj=cube('Unit display',2./factor);obj.location=(12.345/factor,.00001/factor,0)
    select([obj]);obj.better_item.transform_space='DEFAULT'
    u=ctx.scene.unit_settings;before=poses([obj]);old_scale=tuple(obj.scale)
    old_read=float(obj.better_item.location_x)
    if u.system=='METRIC':u.length_unit='MILLIMETERS' if u.length_unit!='MILLIMETERS' else 'METERS'
    elif u.system=='IMPERIAL':u.length_unit='INCHES' if u.length_unit!='INCHES' else 'FEET'
    ctx.view_layer.update()
    assert poses([obj])==before and tuple(obj.scale)==old_scale
    assert float(obj.better_item.location_x)==old_read
    old_physical=old_read*factor
    u.scale_length=float(u.scale_length)*10
    ctx.view_layer.update();new_factor=1000*float(u.scale_length)
    assert poses([obj])==before and tuple(obj.scale)==old_scale
    new_physical=float(obj.better_item.location_x)*new_factor
    assert math.isclose(new_physical,old_physical*10,rel_tol=2*eps)
    return {'display_change_keeps_geometry':True,'unit_scale_change_keeps_raw_geometry':True,
            'old_location_mm':old_physical,'new_location_mm':new_physical,
            'note':'Changing Unit Scale reinterprets physical size; it does not resize stored geometry.'}


def endpoint_cache(factor):
    objects=[empty(str(i),((10+10*i)/factor,0,0)) for i in range(3)]
    select(objects);s=ctx.scene.better_item;s.distribution_method='ENDPOINT'
    s.minimum_distance_mm=.1;s.distribution_start_override=True
    s.distribution_start.mode='MANUAL';s.distribution_start.position=(0,0,0)
    s.distribution_end.mode='MANUAL';s.distribution_end.position=(1./factor,0,0)
    d.apply(ctx,objects);warm=d.inspect_spacing(ctx,objects)
    assert warm[0]=='UNIFORM',warm
    ctx.scene.unit_settings.scale_length=float(ctx.scene.unit_settings.scale_length)*.001
    observed=d.inspect_spacing(ctx,objects);d.clear_inspection();fresh=d.inspect_spacing(ctx,objects)
    assert observed==fresh and fresh[0]=='UNAVAILABLE',(warm,observed,fresh)
    return {'initial':list(warm),'after_unit_scale_change':list(observed),'fresh':list(fresh)}


def point_placements(factor,basis,method):
    objects=[cube(str(i),2./factor) for i in range(3)]
    for i,obj in enumerate(objects):
        for v in obj.data.vertices:v.co.x+=3./factor
        obj.data.update();obj.location=((10+10*i)/factor,0,0)
    select(objects)
    original=[tuple(tuple(v.co) for v in obj.data.vertices) for obj in objects]
    s=ctx.scene.better_item;s.distribution_method=method;s.distribution_mode=basis
    assert s.distribution_mode==basis
    s.spacing=2.5/factor;s.distribution_start_override=True
    s.distribution_start.mode='MANUAL';s.distribution_start.position=(0,0,0)
    s.distribution_end.mode='MANUAL';s.distribution_end.position=(10./factor,0,0)
    d.apply(ctx,objects)
    if basis=='ORIGINS':actual=np.array([obj.matrix_world.translation.x for obj in objects])*factor
    else:
        actual=np.array([(world_bounds(obj)[0][0]+world_bounds(obj)[1][0])/2 for obj in objects])*factor
    actual.sort()
    wanted=np.linspace(0,float(s.distribution_end.position.x)*factor,3) if method=='ENDPOINT' else np.arange(1,4)*float(s.spacing)*factor
    error=float(np.max(np.abs(actual-wanted)))
    assert error<=80*eps*float(np.max(np.abs(wanted))),(basis,method,actual,wanted,error)
    assert original==[tuple(tuple(v.co) for v in obj.data.vertices) for obj in objects]
    assert d.inspect_spacing(ctx,objects)[0]=='UNIFORM'
    return {'basis':basis,'method':method,'points_mm':actual.tolist(),'expected_points_mm':wanted.tolist(),'maximum_error_mm':error,'mesh_unchanged':True}


def precision_ladder(factor,offset_mm,gap_mm,geometry=False):
    s=ctx.scene.better_item;s.minimum_distance_mm=1e-8
    anchor=offset_mm/factor
    ulp=abs(float(np.spacing(np.float32(anchor))))*factor
    initial=max(10.,256*ulp)
    objects=[]
    for i in range(3):
        obj=cube(str(i),2./factor) if geometry else empty(str(i))
        obj.location=((offset_mm+(i+1)*initial)/factor,0,0);objects.append(obj)
    select(objects);s.arrange_origin='CURSOR';ctx.scene.cursor.location=(anchor,0,0)
    s.distribution_mode='GEOMETRY' if geometry else 'ORIGINS';s.spacing=gap_mm/factor
    requested=float(s.spacing)*factor;actual_anchor=float(ctx.scene.cursor.location.x)*factor
    before=poses(objects)
    row={'offset_mm':offset_mm,'input_gap_mm':gap_mm,'stored_requested_gap_mm':requested,'coordinate_ulp_mm':ulp,'geometry':geometry}
    try:d.apply(ctx,objects)
    except BetterItemError as exc:
        assert poses(objects)==before
        assert any(code in str(exc) for code in ('BI-E003','BI-G002','BI-D003','BI-D001')),exc
        assert offset_mm!=0 or geometry and gap_mm==1e-8,('Near-origin representable case refused',row,str(exc))
        row.update(accepted=False,atomic_rollback=True,error=str(exc))
        return row
    positions=np.asarray([o.matrix_world.translation.x for o in objects])*factor
    if geometry:
        intervals=sorted((world_bounds(o)[0][0]*factor,world_bounds(o)[1][0]*factor) for o in objects)
        measured=np.array([intervals[0][0]-actual_anchor]+[b[0]-a[1] for a,b in zip(intervals,intervals[1:])])
        assert np.all(measured>0),('Positive gap collapsed',row,measured)
        error=float(np.max(np.abs(measured-requested)))
        bound=16*max(ulp,abs(float(np.spacing(np.float32(float(positions.max())/factor))))*factor)+64*eps*(abs(requested)+2)
        assert error<=bound,(row,error,bound)
    else:
        measured=np.diff(np.r_[actual_anchor,positions])
        error=float(np.max(np.abs(measured-requested)))
        assert np.all(measured>0) and error<=68*eps*abs(requested),(row,measured,error)
    row.update(accepted=True,measured_gaps_mm=measured.tolist(),maximum_gap_error_mm=error)
    return row


for config in configs:
    for kind,fn in (('parser_rna',parser_and_rna),('reference_transform',transform_and_frame),
                    ('minimum_mm',minimum_separation),('unit_changes',display_changes),('endpoint_cache',endpoint_cache)):
        case(kind,config,fn)
    for basis in ('ORIGINS','BOUNDS_CENTER','SURFACE','VOLUME'):
        for method in ('OFFSET','ENDPOINT'):case('point_placement',config,point_placements,basis,method)
ladder_configs=[('METRIC',scale,'MILLIMETERS') for scale in (1.,.001,.01,1e-6,1000.)]+[('IMPERIAL',1.,'FEET'),('IMPERIAL',.3048,'INCHES')]
for config in ladder_configs:
    for offset in (0.,1000.,1e6,1e9):
        for gap in (1e-8,1e-5,.001,.01,1.):case('point_precision',config,precision_ladder,offset,gap,False)
        for gap in (1e-8,1e-5,.001,1.):case('geometry_precision',config,precision_ladder,offset,gap,True)
result={'passed':not errors,'blender':bpy.app.version_string,'cases':rows,'errors':errors,
        'configurations':len(configs),'case_count':len(rows),
        'accepted_precision_cases':sum(r.get('accepted',False) for r in rows),
        'atomic_precision_rejections':sum(r.get('atomic_rollback',False) for r in rows),
        'limits':'No universal absolute mm accuracy is asserted. Unit text is parsed through Blender API, not actual keyboard events.'}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('SCENE UNITS',json.dumps({k:v for k,v in result.items() if k not in {'cases','errors'}}),flush=True)
if errors:
    print('\n'.join(errors[:5]),flush=True)
    raise AssertionError(str(len(errors))+' unit qualification cases failed')
