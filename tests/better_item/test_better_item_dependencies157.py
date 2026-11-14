"""Same-frame indirect geometry changes, near-singular edits and fault rollback."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector
addon_utils.enable('better_item')
from better_item import frames,transform_view as v
from better_item.math_core import BetterItemError
ctx=bpy.context;o=ctx.object
control=bpy.data.objects.new('Controller',None);ctx.scene.collection.objects.link(control);control['amount']=0.
o.shape_key_add(name='Basis');wide=o.shape_key_add(name='Wide')
for point in wide.data:point.co.x*=2
fc=wide.driver_add('value');var=fc.driver.variables.new();var.name='amount';var.type='SINGLE_PROP';var.targets[0].id=control;var.targets[0].data_path='["amount"]';fc.driver.expression='amount'
for value in (0,.2,.8,.1,1):
    control['amount']=value;control.update_tag();ctx.view_layer.update()
    assert abs(v.values(ctx,o,'DIMENSIONS')[0]-2*(1+value))<1e-6
# A same-frame driven transform controls a GN consumer, through Object Info.
bpy.ops.mesh.primitive_cube_add();consumer=ctx.object
source=bpy.data.objects.new('Driven GN source',None);ctx.scene.collection.objects.link(source)
fc=source.driver_add('location',0);var=fc.driver.variables.new();var.name='amount';var.type='SINGLE_PROP';var.targets[0].id=control;var.targets[0].data_path='["amount"]';fc.driver.expression='amount'
g=bpy.data.node_groups.new('Driven indirect geometry','GeometryNodeTree')
g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
inp=g.nodes.new('NodeGroupInput');out=g.nodes.new('NodeGroupOutput');position=g.nodes.new('GeometryNodeInputPosition');info=g.nodes.new('GeometryNodeObjectInfo');info.inputs['Object'].default_value=source
mult=g.nodes.new('ShaderNodeVectorMath');mult.operation='MULTIPLY';setpos=g.nodes.new('GeometryNodeSetPosition')
for a,b in ((inp.outputs['Geometry'],setpos.inputs['Geometry']),(position.outputs['Position'],mult.inputs[0]),(info.outputs['Location'],mult.inputs[1]),(mult.outputs['Vector'],setpos.inputs['Offset']),(setpos.outputs['Geometry'],out.inputs['Geometry'])):g.links.new(a,b)
consumer.modifiers.new('GN consumer','NODES').node_group=g
for value in (0,.5,1,2,.1):
    control['amount']=value;control.update_tag();ctx.view_layer.update()
    assert abs(v.values(ctx,consumer,'DIMENSIONS')[0]-2*(1+value))<1e-6
# No broad invalidation is necessary for the suspected cache case on 5.2.3.
bpy.ops.mesh.primitive_cube_add();obj=ctx.object
accepted=rejected=0
for epsilon in (1e-2,1e-3,1e-4,1e-5,1e-7):
    for mod in list(obj.modifiers):obj.modifiers.remove(mod)
    basis=Matrix(((1,1,0),(0,epsilon,0),(0,0,1)))
    try:f=frames.create(ctx,'Almost parallel',Vector(),basis)
    except BetterItemError:rejected+=1;continue
    obj.better_item.reference_mode='FRAME';obj.better_item.reference_frame=f.uid;ctx.view_layer.update()
    snapshot=v._snapshot(obj);count=len(obj.modifiers)
    try:
        size=v.values(ctx,obj,'DIMENSIONS');target=tuple(a*b for a,b in zip(size,(1.1,.9,1)));v.set_dimensions(ctx,obj,target)
    except BetterItemError:
        assert v._snapshot(obj)==snapshot and len(obj.modifiers)==count;rejected+=1
    else:assert v._dimensions_match(v.values(ctx,obj,'DIMENSIONS'),target);accepted+=1
# Failing group initialization must not leak an orphan Node Group.
obj.better_item.reference_mode='INDIVIDUAL';obj.better_item.orientation='GLOBAL'
original=v._initialize_affine_group;count=len(bpy.data.node_groups)
def broken(group):original(group);raise RuntimeError('injected graph initialization failure')
v._initialize_affine_group=broken
try:
    try:v._new_affine_group()
    except RuntimeError:pass
    else:raise AssertionError('Expected injected failure')
    assert len(bpy.data.node_groups)==count
finally:v._initialize_affine_group=original
result={'same_frame_driver_shape_key_values':5,'same_frame_driven_gn_values':5,'near_singular_cases':{'accepted':accepted,'rejected_atomically':rejected},'group_initialization_rollback':True}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('157 DEPENDENCIES PASSED',json.dumps(result))
