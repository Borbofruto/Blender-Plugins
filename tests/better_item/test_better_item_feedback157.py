"""Targeted execution of defects raised in the three 1.5.5 audits."""
import sys, math, json, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy, addon_utils, numpy as np
from mathutils import Matrix,Vector,Euler
addon_utils.enable('better_item')
import better_item as addon
from better_item import frames,engine,native_refs,transform_view as v,math_core
from better_item.math_core import BetterItemError
ctx=bpy.context
results={}
def reset():
    if ctx.object and ctx.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    ctx.scene.better_item.frames.clear();ctx.scene.better_item.active_frame=-1
    v.clear_cache()
def cube(name='Target'):
    bpy.ops.mesh.primitive_cube_add(size=2);ctx.object.name=name;return ctx.object
def empty(name):
    o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);return o
def fail(call,code):
    try:call()
    except BetterItemError as e:assert code in str(e),(code,str(e));return str(e)
    raise AssertionError('Expected '+code)
def state(o):
    return (v._snapshot(o),tuple((m.persistent_uid,m.name,m.node_group.as_pointer() if m.type=='NODES' and m.node_group else None) for m in o.modifiers),
        tuple(tuple(p.co) for p in o.data.vertices) if o.type=='MESH' else (),len(bpy.data.node_groups))
def precision():
    reset();o=cube();axes=Euler((.2,.4,.6)).to_matrix()
    for vertex in o.data.vertices:vertex.co+=Vector((1e5,1e5,1e5))
    o.data.update();ctx.view_layer.update()
    xyz=np.array([tuple(p.co) for p in o.data.vertices],dtype=np.float64)
    directions=np.asarray(axes,dtype=np.float64);directions/=np.linalg.norm(directions,axis=0)
    truth=np.ptp(xyz@directions,axis=0);actual=v.dimensions(o,axes)
    assert np.allclose(actual,truth,rtol=0,atol=1e-9),(actual,truth)
    for actual,desired in ((4e-8,1e-8),(1e-9,1e-8),(0,9e-8)):
        assert not v._dimensions_match((actual,1,1),(desired,1,1))
    assert not engine._native_matches((0,1,1),(1e-9,1,1))
    o.location=(0,0,0);ctx.view_layer.update()
    assert not engine._position_matches(o,(1e-9,0,0))
    reset();o=cube()
    for size in (1e-12,1e-8,1e-4,1,1e4):
        o.scale=(size,size,size);ctx.view_layer.update();before=v.values(ctx,o,'DIMENSIONS')
        desired=tuple(x*f for x,f in zip(before,(1.2,.8,1.1)))
        v.set_dimensions(ctx,o,desired);assert v._dimensions_match(v.values(ctx,o,'DIMENSIONS'),desired)
    for space in ('DEFAULT','REFERENCE'):
        o.better_item.transform_space=space;o.scale=(1,1,1);ctx.view_layer.update();old=state(o)
        fail(lambda:v.edit_component(ctx,o,'DIMENSIONS',0,0),'BI-T010');assert state(o)==old
    # Different uniform units do not make an invertible basis singular.
    for scalar in (1e-9,.001,1,1e9):native_refs.checked(Matrix.Diagonal((scalar,scalar,100*scalar)))
    fail(lambda:native_refs.checked(Matrix(((1,1,0),(0,1e-9,0),(0,0,1)))),'BI-F005')
    results['precision']='large local coordinates, tiny/large Dimensions, zero guard, channel retention and scale-invariant conditioning passed'
def gimbal():
    reset();o=cube();s=o.better_item;s.orientation='GIMBAL';accepted=rejected=0
    for order in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX'):
        for axis in range(3):
            o.rotation_mode=order;o.rotation_euler=(.4,.3,.5);ctx.view_layer.update()
            request=list(v.values(ctx,o,'ROTATION'));request[axis]+=.3;before=state(o)
            try:v.set_rotation(ctx,o,request)
            except BetterItemError as e:
                assert 'BI-T009' in str(e),str(e);assert state(o)==before;rejected+=1
            else:
                a=Euler(v.values(ctx,o,'ROTATION'),s.view_rotation_order).to_matrix()
                b=Euler(request,s.view_rotation_order).to_matrix()
                assert np.allclose(a,b,atol=2e-4);accepted+=1
    assert rejected>0 and accepted>0
    results['moving_gimbal']={'accepted_with_roundtrip':accepted,'rejected_atomically':rejected}
def modifier_integrity():
    reset();o=cube();ref=empty('Ref');ref.rotation_euler.z=.7
    o.better_item.orientation='REFERENCE';o.better_item.orientation_object=ref;ctx.view_layer.update()
    v.set_dimensions(ctx,o,tuple(x*f for x,f in zip(v.values(ctx,o,'DIMENSIONS'),(1.2,.8,1))))
    modifier=o.modifiers[-1];group=modifier.node_group
    def reject_mutation(change,undo):
        change();ctx.view_layer.update();before=state(o)
        fail(lambda:v.set_dimensions(ctx,o,tuple(x*1.01 for x in v.values(ctx,o,'DIMENSIONS'))),'BI-M003')
        assert state(o)==before;undo();ctx.view_layer.update()
    reject_mutation(lambda:group.pop('better_item_affine'),lambda:group.__setitem__('better_item_affine',1))
    link=next(l for l in group.links if l.to_node.bl_idname=='GeometryNodeSetPosition' and l.to_socket.name=='Position')
    src,dst=link.from_socket,link.to_socket
    reject_mutation(lambda:group.links.remove(link),lambda:group.links.new(src,dst))
    row=group.nodes['Better Item Row 0'];reject_mutation(lambda:setattr(row,'operation','ADD'),lambda:setattr(row,'operation','DOT_PRODUCT'))
    setpos=next(n for n in group.nodes if n.bl_idname=='GeometryNodeSetPosition')
    reject_mutation(lambda:setattr(setpos.inputs['Selection'],'default_value',False),lambda:setattr(setpos.inputs['Selection'],'default_value',True))
    reject_mutation(lambda:modifier.__setattr__('node_group',None),lambda:modifier.__setattr__('node_group',group))
    # A shared group must be restored and the temporary copy freed on failure.
    other=cube('Shared');other_mod=other.modifiers.new('Shared','NODES');other_mod.node_group=group
    before=state(o);original=v._write_affine
    def broken(g,m):
        original(g,m);raise BetterItemError('injected write failure')
    v._write_affine=broken
    try:
        # Pick a nonuniform projected edit that requires the affine path.
        request=tuple(x*f for x,f in zip(v.values(ctx,o,'DIMENSIONS'),(.9,1.1,1)))
        fail(lambda:v.set_dimensions(ctx,o,request),'injected');assert state(o)==before
    finally:v._write_affine=original
    # Renames and .blend reload preserve the independent modifier identity.
    modifier.name='Renamed stage';uid=modifier.persistent_uid
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
        p=str(Path(td)/'modifier.blend');bpy.ops.wm.save_as_mainfile(filepath=p);bpy.ops.wm.open_mainfile(filepath=p)
        o=bpy.data.objects['Target'];m=v._dimensions_modifier(o);assert m.persistent_uid==uid
        assert o.better_item['dimensions_modifier_uid']==uid
    results['modifier_integrity']='missing marker/link/source, changed operation/selection, shared-copy rollback, rename and reload passed'
def channel_drivers():
    reset();o=cube();o.scale=(1,2,3);driver=o.driver_add('scale',2);driver.driver.expression='3'
    ctx.view_layer.update();engine.edit_scale_component(o,0,1.5);assert tuple(o.scale)==(1.5,2,3)
    before=state(o);fail(lambda:engine.edit_scale_component(o,2,4),'BI-T002');assert state(o)==before
    # Rotating around the object origin need not block a constant Scale driver.
    v.set_rotation(ctx,o,(.1,.2,.3));assert tuple(o.scale)==(1.5,2,3)
    addon._field_errors[o.as_pointer()]='old error';o.better_item.link_scale=(True,False,False)
    assert o.as_pointer() not in addon._field_errors
    before=state(o);o.lock_location[0]=True
    fail(lambda:v._edit_default(o,'LOCATION',0,1e-13),'BI-');assert state(o)==before
    o.location=(0,0,0);ctx.view_layer.update();before=state(o)
    fail(lambda:frames.set_position(ctx,o,(1e-13,0,0)),'BI-T003');assert state(o)==before
    results['channels']='unrelated Scale driver allowed, affected driver blocked, rotation preserves driven Scale, link error reset and tiny locked edits passed'
def rotation_position():
    reset();o=cube();o.location=(2,3,4);o.delta_location=(.2,.5,-.3);o.better_item.use_reference_pivot=True
    ctx.view_layer.update();before=state(o);original=engine._target_location
    engine._target_location=lambda obj,target:original(obj,Vector(target)+Vector((.01,0,0)))
    try:
        fail(lambda:v.set_rotation(ctx,o,(.1,.2,.3)),'BI-T006');assert state(o)==before
    finally:engine._target_location=original
    results['rotation_position']='fault-injected final position mismatch rejected; full Rotation/Location/Scale rollback passed'
def instances():
    reset();o=cube();g=bpy.data.node_groups.new('Unrealized','GeometryNodeTree')
    g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    inp=g.nodes.new('NodeGroupInput');out=g.nodes.new('NodeGroupOutput');instance=g.nodes.new('GeometryNodeGeometryToInstance')
    g.links.new(inp.outputs['Geometry'],instance.inputs['Geometry']);g.links.new(instance.outputs['Instances'],out.inputs['Geometry'])
    m=o.modifiers.new('Instances','NODES');m.node_group=g;ctx.view_layer.update()
    fail(lambda:v.values(ctx,o,'DIMENSIONS'),'BI-M005')
    realize=g.nodes.new('GeometryNodeRealizeInstances');g.links.new(instance.outputs['Instances'],realize.inputs['Geometry']);g.links.new(realize.outputs['Geometry'],out.inputs['Geometry']);ctx.view_layer.update()
    assert np.allclose(v.values(ctx,o,'DIMENSIONS'),(2,2,2))
    results['instances']='unrealized instances rejected; Realize Instances restores valid measurement'
errors={}
for test in (precision,gimbal,modifier_integrity,channel_drivers,rotation_position,instances):
    try:test();print('PASS',test.__name__,flush=True)
    except Exception as e:
        import traceback;traceback.print_exc();errors[test.__name__]=str(e)
Path(__file__).with_suffix('.results.json').write_text(json.dumps({'results':results,'errors':errors},indent=2),encoding='utf-8')
assert not errors,errors
print('157 TARGETED AUDIT PASSED',json.dumps(results))
