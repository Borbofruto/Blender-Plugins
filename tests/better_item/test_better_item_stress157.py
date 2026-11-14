"""Eleven execution groups corresponding to Feedback 1's test suggestions.

Coverage is explicit and finite, not a claim of exhaustively testing every
possible Blender scene. Uses only factory-startup objects and native test data.
"""
import sys, math, random, itertools, json, tempfile, traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector,Euler
addon_utils.enable('better_item')
from better_item import engine,frames,transform_view as v,native_refs,arrange,math_core
from better_item.math_core import BetterItemError
ctx=bpy.context;rng=random.Random(157);report={};errors={}
orders=('XYZ','XZY','YXZ','YZX','ZXY','ZYX')
def reset():
    if ctx.object and ctx.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    ctx.scene.better_item.frames.clear();ctx.scene.better_item.active_frame=-1
    ctx.scene.unit_settings.scale_length=1;v.clear_cache()
def empty(name):
    o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);return o
def cube(name='Target'):
    bpy.ops.mesh.primitive_cube_add(size=2);ctx.object.name=name;return ctx.object
def select(objects,active):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    ctx.view_layer.objects.active=active
def rejected(call,code=None):
    try:call()
    except BetterItemError as e:
        assert str(e).startswith('[BI-'),str(e)
        if code:assert code in str(e),(code,str(e))
        return
    raise AssertionError('Expected rejection')
def near(a,b,tol=2e-4):assert np.allclose(a,b,rtol=2e-5,atol=tol),(a,b)
def group1():
    reset();o=cube();p=empty('Parent');ref=empty('Ref');ref.rotation_euler=(.2,-.4,.6);ref.location=(.3,-.6,.9)
    f=frames.create(ctx,'Stable',Vector((.1,-.2,.3)),Euler((.3,.2,-.1)).to_matrix())
    ctx.scene.cursor.rotation_euler=(.3,-.2,.1)
    with native_refs.view_context(ctx):
        bpy.ops.transform.create_orientation(name='Audit Fixed',use=True)
        ctx.scene.transform_orientation_slots[0].custom_orientation.matrix=Euler((.1,.2,.3)).to_matrix()
    s=o.better_item;success=rejections=0;reasons={}
    for mode,parent_case,storage,mirror,pivot,kind in itertools.product(
            ('GLOBAL','REFERENCE','SAVED','GIMBAL','NORMAL','CURSOR','VIEW','NATIVE'),range(3),(*orders,'QUATERNION','AXIS_ANGLE'),(False,True),
            ('GLOBAL','OBJECT','FRAME','CURSOR','BOUNDING_BOX_CENTER','MEDIAN_POINT','ACTIVE_ELEMENT','INDIVIDUAL_ORIGINS'),('LOCATION','ROTATION','DIMENSIONS')):
        for modifier in list(o.modifiers):
            group=modifier.node_group if modifier.type=='NODES' else None
            o.modifiers.remove(modifier)
            if group and group.users==0:bpy.data.node_groups.remove(group)
        o.parent=p if parent_case else None;p.rotation_euler=(.2,-.1,.4);p.scale=(2,2,2) if parent_case==1 else (1,.7,1.3)
        o.matrix_parent_inverse=Matrix.Identity(4);o.delta_location=(.03,-.02,.01);o.location=(.2,-.3,.4)
        o.rotation_mode=storage
        q=Euler((.2,.3,.4)).to_quaternion()
        if storage=='QUATERNION':o.rotation_quaternion=q
        elif storage=='AXIS_ANGLE':axis,angle=q.to_axis_angle();o.rotation_axis_angle=(angle,*axis)
        else:o.rotation_euler=(.2,.3,.4)
        o.scale=(-1 if mirror else 1,1,1)
        s.reference_mode='INDIVIDUAL';s.orientation=mode;s.orientation_object=ref;s.orientation_frame=f.uid;s.reference_native='Audit Fixed'
        s.view_rotation_order=storage if storage in orders else 'XYZ'
        s.pivot_mode=pivot if pivot in {'GLOBAL','OBJECT','FRAME','CURSOR'} else 'PIVOT';s.origin_object=ref;s.pivot_frame=f.uid
        if pivot not in {'GLOBAL','OBJECT','FRAME','CURSOR'}:s.reference_pivot=pivot
        s.use_reference_pivot=parent_case==1;ctx.view_layer.update()
        before=v._snapshot(o);count=len(o.modifiers);values=list(v.values(ctx,o,kind))
        if kind=='LOCATION':values[0]+=.07
        elif kind=='ROTATION':values[1]+=.07
        else:values=[x*f for x,f in zip(values,(1.03,.98,1.01))]
        try:
            if kind=='LOCATION':frames.set_position(ctx,o,values)
            elif kind=='ROTATION':v.set_rotation(ctx,o,values)
            else:v.set_dimensions(ctx,o,values)
        except BetterItemError as e:
            assert str(e).startswith('[BI-');assert v._snapshot(o)==before,(mode,kind,str(e));assert len(o.modifiers)==count
            code=str(e).split(']',1)[0]+']'
            assert code in {'[BI-T009]','[BI-T012]','[BI-V001]'},(mode,kind,str(e))
            if code=='[BI-V001]':assert 'parent' in str(e).lower() or 'rigid' in str(e).lower(),str(e)
            reasons[code]=reasons.get(code,0)+1
            rejections+=1
        else:
            read=v.values(ctx,o,kind)
            if kind=='ROTATION':near(Euler(read,s.view_rotation_order).to_matrix(),Euler(values,s.view_rotation_order).to_matrix())
            else:near(read,values)
            success+=1
    assert success>0 and rejections>0
    return {'cases':success+rejections,'accepted':success,'coded_atomic_rejections':rejections,'rejection_codes':reasons}
def group2():
    reset();p=empty('Parent');ref=empty('Reference');ref.rotation_euler=(.3,-.2,.4)
    a=cube('Numeric');b=cube('Native');count=0
    with native_refs.view_context(ctx):
        bpy.ops.transform.create_orientation(name='Audit Reference',use=True)
        for custom,has_parent,mirror,storage,edited_axis in itertools.product((False,True),(False,True),(False,True),(*orders,'QUATERNION','AXIS_ANGLE'),range(3)):
            p.rotation_euler=(.2,.1,.3);p.scale=(1.5,1.5,1.5)
            for o in (a,b):
                o.parent=p if has_parent else None;o.matrix_parent_inverse=Matrix.Identity(4)
                o.location=(1,2,3);o.rotation_mode=storage;o.scale=(-1 if mirror else 1,1,1)
                q=Euler((.2,.3,.4)).to_quaternion()
                if storage=='QUATERNION':o.rotation_quaternion=q
                elif storage=='AXIS_ANGLE':axis,angle=q.to_axis_angle();o.rotation_axis_angle=(angle,*axis)
                else:o.rotation_euler=(.2,.3,.4)
            a.better_item.orientation='REFERENCE' if custom else 'GLOBAL';a.better_item.orientation_object=ref
            a.better_item.view_rotation_order=storage if storage in orders else 'XYZ'
            a.better_item.use_reference_pivot=True;a.better_item.pivot_mode='GLOBAL'
            ctx.view_layer.update();basis=frames.object_axes(ctx,a)
            desired=list(v.values(ctx,a,'ROTATION'));desired[edited_axis]+=.08 if edited_axis%2 else -.12
            # Independently construct a world axis-angle for the equivalent
            # native operator. Signed scale and uniform parent scale are known.
            world_rotation=b.matrix_world.to_3x3() @ Matrix.Diagonal(tuple(1/(scale*(1.5 if has_parent else 1)) for scale in b.scale))
            desired_world=basis @ Euler(desired,a.better_item.view_rotation_order).to_matrix()
            delta=desired_world @ world_rotation.transposed();axis,angle=delta.to_quaternion().to_axis_angle()
            z=axis.normalized();x=z.orthogonal().normalized();y=z.cross(x)
            slot=ctx.scene.transform_orientation_slots[0];slot.type='Audit Reference';slot.custom_orientation.matrix=Matrix((x,y,z)).transposed()
            v.set_rotation(ctx,a,desired)
            select([b],b)
            bpy.ops.transform.rotate(value=angle,orient_axis='Z',orient_type='Audit Reference',constraint_axis=(False,False,True),center_override=(0,0,0))
            ctx.view_layer.update();near(a.matrix_world,b.matrix_world);count+=1
        # Single-axis Euler configurations questioned in Feedback 2.
        directions=0
        for order,seed_axis,axis in itertools.product(orders,range(3),range(3)):
            b.parent=None;b.rotation_mode=order;b.rotation_euler=(0,0,0);b.rotation_euler[seed_axis]=.3;b.location=(0,0,0)
            select([b],b);ctx.view_layer.update();basis=native_refs.orientation(ctx,'GIMBAL',b)
            before=b.matrix_world.translation.copy();value=[0,0,0];value[axis]=1
            bpy.ops.transform.translate(value=value,orient_type='GIMBAL',constraint_axis=tuple(i==axis for i in range(3)))
            ctx.view_layer.update();near(b.matrix_world.translation-before,basis.col[axis]);directions+=1
    return {'actual_native_rotation_comparisons':count,'single_axis_gimbal_direction_comparisons':directions}
def group3():
    reset();arm_data=bpy.data.armatures.new('Rig');arm=bpy.data.objects.new('Rig',arm_data);ctx.scene.collection.objects.link(arm)
    select([arm],arm);bpy.ops.object.mode_set(mode='EDIT');bone=arm.data.edit_bones.new('Bone');bone.head=(0,0,0);bone.tail=(0,0,1);bpy.ops.object.mode_set(mode='OBJECT')
    mesh=cube('VertexParent');o=empty('Child');count=0
    for parent_type in ('OBJECT','BONE','VERTEX','VERTEX_3'):
        o.parent=arm if parent_type=='BONE' else mesh;o.parent_type=parent_type
        if parent_type=='BONE':o.parent_bone='Bone'
        if parent_type in ('VERTEX','VERTEX_3'):o.parent_vertices=(0,1,2)
        o.location=(.2,.3,.4);o.scale=(1,1,1);o.delta_location=(.1,-.1,.2)
        ctx.view_layer.update();target=o.matrix_world.translation+Vector((.1,.2,-.1));engine.apply_world_positions([o],{o.name:tuple(target)});near(o.matrix_world.translation,target);count+=1
        if parent_type!='OBJECT':
            o.scale=(0,1,1);ctx.view_layer.update();before=v._snapshot(o)
            rejected(lambda:engine.apply_world_positions([o],{o.name:tuple(target+Vector((1,0,0)))}),'BI-T005');assert v._snapshot(o)==before
    # Deep mirrored parents, delta rotation and Parent Inverse: accepted rigid
    # cases must round-trip; shear cases may reject atomically.
    o.parent=None;parents=[empty('Chain'+str(i)) for i in range(5)]
    for i,p in enumerate(parents):
        p.parent=parents[i-1] if i else None;p.rotation_euler=(.05,.1,-.08);p.scale=(-1,1,1) if i%2 else (1.1,1.1,1.1)
    o.parent=parents[-1];o.scale=(-1,1,1);o.matrix_parent_inverse=Matrix.Translation((3,-2,1));o.delta_rotation_euler=(.1,.2,.3);o.delta_location=(.3,-.1,.2);ctx.view_layer.update()
    frames.set_position(ctx,o,(1,2,3));near(v.values(ctx,o,'LOCATION'),(1,2,3))
    before=v._snapshot(o)
    try:v.set_rotation(ctx,o,(.2,.3,.4))
    except BetterItemError:assert v._snapshot(o)==before
    else:near(v.values(ctx,o,'ROTATION'),(.2,.3,.4))
    return {'parent_types':count,'collapsed_child_cases':3,'deep_signed_delta_chain':True}
def group4():
    reset();o=cube();cases=0
    for magnitude,signs in itertools.product((1e-4,1e4),itertools.product((-1,1),repeat=3)):
        o.scale=tuple(magnitude*s for s in signs);ctx.view_layer.update()
        request=tuple(x*1.1 for x in v.values(ctx,o,'DIMENSIONS'));v.set_dimensions(ctx,o,request);assert v._dimensions_match(v.values(ctx,o,'DIMENSIONS'),request);cases+=1
    return {'extreme_signed_scale_cases':cases}
def group5():
    reset();o=cube();axes=Euler((.3,.5,.8)).to_matrix();cases=0
    for offset in (0,1e5,1e7):
        for i,vertex in enumerate(o.data.vertices):vertex.co=Vector((offset+(1 if i&1 else -1),offset+(2 if i&2 else -2),offset+(3 if i&4 else -3)))
        o.data.update();ctx.view_layer.update();xyz=np.array([tuple(p.co) for p in o.data.vertices],dtype=np.float64)
        d=np.asarray(axes,dtype=np.float64);d/=np.linalg.norm(d,axis=0)
        near(v.dimensions(o,axes),np.ptp(xyz@d,axis=0),tol=1e-8);cases+=1
    return {'float64_truth_from_stored_vertices':cases}
def group6():
    reset();o=empty('Linked');o.better_item.link_location=(True,True,True)
    frames.set_position(ctx,o,(.1,.2,.6));worst=0
    for iteration in range(1000):
        axis=iteration%3;before=v.values(ctx,o,'LOCATION');request=before[axis]*(1.001 if iteration%2 else 1/1.001)
        v.edit_component(ctx,o,'LOCATION',axis,request);after=v.values(ctx,o,'LOCATION')
        worst=max(worst,max(abs(after[i]/after[0]-expected) for i,expected in enumerate((1,2,6))))
    assert worst<1e-4,worst
    o.lock_location=(False,True,False);before=v._snapshot(o);rejected(lambda:v.edit_component(ctx,o,'LOCATION',0,1),'BI-T003');assert v._snapshot(o)==before
    return {'chained_edits':1000,'max_ratio_drift':worst,'linked_lock_rollback':True}
def group7():
    reset();o=empty('Angles');s=o.better_item;s.link_rotation=(True,True,True);cases=0
    for start,end in ((0,math.pi/2),(math.pi/2,0),(math.pi, -math.pi),(-math.pi,math.pi),(math.pi/2,-math.pi/2)):
        o.rotation_euler=(0,0,start);ctx.view_layer.update();v.edit_component(ctx,o,'ROTATION',2,end)
        near(o.rotation_euler,(0,0,end));cases+=1
    o.rotation_euler=(0,math.pi/2,0);s.orientation='GIMBAL';ctx.view_layer.update();rejected(lambda:v.values(ctx,o,'LOCATION'),'BI-F005')
    return {'angle_zero_turn_crossing_cases':cases,'gimbal_lock_rejected':True}
def group8():
    reset();source=empty('Source');source.location=(1,2,3);source.rotation_euler=(.1,.2,.3);ctx.view_layer.update();checks=0
    for length in (2,20,100):
        ctx.scene.better_item.frames.clear();chain=[]
        for i in range(length):
            f=frames.create(ctx,'Frame'+str(i),Vector(),Matrix.Identity(3));uid=f.uid
            if i:
                f.position_mode='FRAME';f.position_frame=chain[-1];f.rotation_mode='FRAME';f.rotation_frame=chain[-1]
            else:f.position_mode='OBJECT';f.position_source=source;f.rotation_mode='OBJECT';f.rotation_source=source
            chain.append(uid)
        last=frames.find(ctx.scene,chain[-1]);near(frames.frame_origin(last),(1,2,3));near(frames.frame_axes(last),source.rotation_euler.to_matrix())
        last.name='Renamed';near(frames.frame_origin(last),(1,2,3))
        first=frames.find(ctx.scene,chain[0]);first.rotation_mode='FRAME';first.rotation_frame=last.uid
        rejected(lambda:frames.frame_axes(last),'BI-F001');first.rotation_mode='OBJECT'
        if length>2:
            removed=chain[length//2];number=frames.find(ctx.scene,removed).number;frames.clear_missing_choices(ctx.scene,number)
            index=next(i for i,f in enumerate(ctx.scene.better_item.frames) if f.uid==removed);ctx.scene.better_item.frames.remove(index)
            rejected(lambda:frames.frame_origin(frames.find(ctx.scene,chain[-1])),'BI-F002')
        checks+=1
    return {'chain_lengths':[2,20,100],'cycle_rename_removal_cases':checks}
def group9():
    reset();objects=[empty('Item'+str(i)) for i in range(5)];p=empty('Parent');objects[1].parent=p
    cases=0;rejections=0
    for magnitude,units in itertools.product((1e-6,1,1e6,1e9),(1,.001)):
        ctx.scene.unit_settings.scale_length=units
        for i,o in enumerate(objects):o.location=(magnitude+i*max(1,magnitude*1e-5),i*3,0)
        p.rotation_euler=(.1,.2,.3);ctx.view_layer.update();select(objects,objects[0]);_,origins=engine.selection_origins(ctx)
        before={o.name:tuple(o.location) for o in objects}
        try:
            targets=arrange.plan(ctx,objects,origins,(True,False,False),'KEY',spacing=max(1,magnitude*1e-5))
            engine.apply_world_positions(objects,targets,verify=arrange.distribution_verifier(ctx,(True,False,False),'KEY',.00001))
        except BetterItemError:
            assert all(tuple(o.location)==before[o.name] for o in objects);rejections+=1
        else:
            expected=sorted(value[0] for value in targets.values());near(sorted(o.matrix_world.translation.x for o in objects),expected,tol=max(2e-4,magnitude*3e-7))
        cases+=1
    # Coincident initial coordinates must name ambiguity, not silently sort it.
    for o in objects:o.parent=None;o.location=(1,0,0)
    ctx.view_layer.update();_,origins=engine.selection_origins(ctx)
    rejected(lambda:arrange.plan(ctx,objects,origins,(True,False,False),'KEY',spacing=1),'BI-D002')
    # Tiny steps at very large coordinates must reject collapsed output spacing.
    for i,o in enumerate(objects):o.location=(1e9+i*128,0,0)
    ctx.view_layer.update();_,origins=engine.selection_origins(ctx);before={o.name:tuple(o.location) for o in objects}
    targets=arrange.plan(ctx,objects,origins,(True,False,False),'KEY',spacing=.01)
    rejected(lambda:engine.apply_world_positions(objects,targets,verify=arrange.distribution_verifier(ctx,(True,False,False),'KEY',.00001)),'BI-D003')
    assert all(tuple(o.location)==before[o.name] for o in objects)
    # Selected parent and selected child must receive their own world targets.
    parent,child,free=objects[:3]
    for action in ('ALIGN','DISTRIBUTE'):
        parent.location=(2,0,0);child.parent=parent;child.location=(3,0,0);free.location=(10,0,0)
        select([parent,child,free],free);ctx.view_layer.update();selected,origins=engine.selection_origins(ctx)
        targets=arrange.plan(ctx,selected,origins,(True,False,False),'KEY',spacing=1 if action=='DISTRIBUTE' else None)
        engine.apply_world_positions(selected,targets)
        for item in selected:near(item.matrix_world.translation,targets[item.name])
    return {'coordinate_unit_cases':cases,'expected_precision_rejections':rejections,'ambiguity_and_collapse':True,'selected_parent_child_operations':2}
def group10():
    reset();o=cube();checks=0
    for kind in ('ARRAY','MIRROR','SHAPEKEY'):
        for m in list(o.modifiers):o.modifiers.remove(m)
        if o.data.shape_keys:o.shape_key_clear()
        if kind=='ARRAY':m=o.modifiers.new('Array','ARRAY');m.count=3
        elif kind=='MIRROR':m=o.modifiers.new('Mirror','MIRROR');o.data.vertices[0].co.x=-2;o.data.update()
        else:
            o.shape_key_add(name='Basis');key=o.shape_key_add(name='Wide')
            for vertex in key.data:vertex.co.x*=1.2
            key.value=.5
        ctx.view_layer.update();size=v.values(ctx,o,'DIMENSIONS');v.set_dimensions(ctx,o,tuple(x*1.05 for x in size));assert v._dimensions_match(v.values(ctx,o,'DIMENSIONS'),tuple(x*1.05 for x in size));checks+=1
    return {'array_mirror_shape_key_cases':checks}
def group11():
    reset();ctx.preferences.edit.use_global_undo=True;o=cube();ref=empty('Reference');ref.rotation_euler.z=.7;o.better_item.orientation='REFERENCE';o.better_item.orientation_object=ref;ctx.view_layer.update()
    before=v.values(ctx,o,'DIMENSIONS');bpy.ops.ed.undo_push(message='Before oblique edit')
    target=tuple(x*f for x,f in zip(before,(1.2,.8,1)));v.set_dimensions(ctx,o,target);bpy.ops.ed.undo_push(message='After oblique edit')
    bpy.ops.ed.undo();o=bpy.data.objects['Target'];assert not o.modifiers;near(v.values(ctx,o,'DIMENSIONS'),before)
    bpy.ops.ed.redo();o=bpy.data.objects['Target'];assert len(o.modifiers)==1;near(v.values(ctx,o,'DIMENSIONS'),target)
    shared=cube('Shared');shared.modifiers.new('Shared','NODES').node_group=o.modifiers[0].node_group
    select([o],o);second=tuple(x*f for x,f in zip(target,(.95,1.05,1)));v.set_dimensions(ctx,o,second)
    assert o.modifiers[0].node_group!=shared.modifiers[0].node_group
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
        p=str(Path(td)/'roundtrip.blend');bpy.ops.wm.save_as_mainfile(filepath=p);bpy.ops.wm.open_mainfile(filepath=p)
        o=bpy.data.objects['Target'];near(v.values(ctx,o,'DIMENSIONS'),second);v._dimensions_modifier(o)
    return {'undo_redo_creation':True,'copy_on_write':True,'blend_roundtrip':True}
for number in range(1,12):
    name='group'+str(number)
    try:report[name]=globals()[name]();print('PASS',name,report[name],flush=True)
    except Exception as e:traceback.print_exc();errors[name]=str(e)
Path(__file__).with_suffix('.results.json').write_text(json.dumps({'groups':report,'errors':errors},indent=2),encoding='utf-8')
assert not errors,errors
print('157 ELEVEN-GROUP STRESS PASSED')
