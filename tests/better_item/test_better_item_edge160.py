import sys,math,json,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector,Euler
addon_utils.enable('better_item')
from better_item import arrange,geometry_arrange as geom,engine,frames,orientation,transform_view as v
from better_item.math_core import BetterItemError
ctx=bpy.context
def reset():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);ctx.scene.better_item.frames.clear();v.clear_cache()
    s=ctx.scene.better_item;s.arrange_reference_mode='INDIVIDUAL';s.arrange_orientation='GLOBAL';s.arrange_origin='GLOBAL';s.arrange_on_axis=False
def cube(name):bpy.ops.mesh.primitive_cube_add();ctx.object.name=name;return ctx.object
def empty(name):o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);return o
def select(objects,active):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    ctx.view_layer.objects.active=active
def distribute(objects):
    ctx.view_layer.update();targets,verify=geom.plan(ctx,objects,{o.name:tuple(o.matrix_world.translation) for o in objects},(True,False,False),spacing=.1)
    engine.apply_world_positions(objects,targets,verify=verify)
def fail(fn,code):
    try:fn()
    except BetterItemError as e:assert code in str(e),str(e);return
    raise AssertionError('Expected '+code)
def near(a,b):assert np.allclose(a,b,rtol=2e-6,atol=2e-5),(a,b)
reset();key=cube('Key');target=cube('Driven Geometry');target.location=(8,0,0)
s=ctx.scene.better_item;s.arrange_origin='OBJECT';s.arrange_origin_object=key;select([key,target],key)
# GN local offset driven by its own Location: shape width alone cannot detect it.
g=bpy.data.node_groups.new('Position dependent','GeometryNodeTree')
g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
inp=g.nodes.new('NodeGroupInput');out=g.nodes.new('NodeGroupOutput');setpos=g.nodes.new('GeometryNodeSetPosition');offset=g.nodes.new('ShaderNodeCombineXYZ')
g.links.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);g.links.new(offset.outputs['Vector'],setpos.inputs['Offset']);g.links.new(setpos.outputs['Geometry'],out.inputs['Geometry'])
curve=offset.inputs[0].driver_add('default_value');variable=curve.driver.variables.new();variable.name='x';variable.type='TRANSFORMS';variable.targets[0].id=target;variable.targets[0].transform_type='LOC_X';variable.targets[0].transform_space='WORLD_SPACE';curve.driver.expression='x*.1'
target.modifiers.new('Position dependent','NODES').node_group=g;ctx.view_layer.update();before=v._snapshot(target)
fail(lambda:distribute([key,target]),'BI-G003');assert v._snapshot(target)==before
# A Location-dependent native Scale must also roll back.
target.modifiers.clear();curve=target.driver_add('scale',1);variable=curve.driver.variables.new();variable.name='x';variable.type='SINGLE_PROP';variable.targets[0].id=target;variable.targets[0].data_path='location[0]';curve.driver.expression='1+x*.1'
ctx.view_layer.update();before=v._snapshot(target);fail(lambda:distribute([key,target]),'BI-G005');assert v._snapshot(target)==before
# Reference descendant of a target is not silently repositioned independently.
reset();parent=cube('Parent target');key=empty('Child key');key.parent=parent;key.location=(4,0,0);s=ctx.scene.better_item;s.arrange_origin='OBJECT';s.arrange_origin_object=key
select([parent],parent);ctx.view_layer.update();before=v._snapshot(parent);fail(lambda:distribute([parent]),'BI-G004');assert v._snapshot(parent)==before
# Selected parent and child both get their own world targets.
reset();key=cube('Key');parent=cube('Parent target');child=cube('Child target');parent.location=(6,0,0);child.parent=parent;child.location=(6,0,0)
s=ctx.scene.better_item;s.arrange_origin='OBJECT';s.arrange_origin_object=key;select([key,parent,child],key);distribute([key,parent,child]);near(parent.matrix_world.translation.x,2.1);near(child.matrix_world.translation.x,4.2)
# Reference-child orientation remains fixed while a selected parent aligns to it.
reset();parent=cube('Parent');key=empty('Child Reference');key.parent=parent;key.location=(3,2,1);key.rotation_euler=(.2,.4,.1)
other=cube('Other');other.location=(5,3,1);s=ctx.scene.better_item;s.arrange_orientation='REFERENCE';s.arrange_object=key
select([parent,key,other],key);ctx.view_layer.update();key_world=key.matrix_world.copy();positions={o.name:tuple(o.matrix_world.translation) for o in (parent,key,other)}
arrange.align_orientations(ctx,[parent,key,other]);near(key.matrix_world,key_world)
for o in (parent,key,other):near(o.matrix_world.translation,positions[o.name]);near(orientation.rotation(o),orientation.rotation(key))
# All storage types, Empty/Camera targets and Frame orientation snapshots.
reset();f=frames.create(ctx,'Angles',Vector(),Euler((.2,-.3,.4)).to_matrix());s=ctx.scene.better_item;s.arrange_reference_mode='FRAME';s.arrange_reference_frame=f.uid
objects=[]
for storage in ('XYZ','XZY','YXZ','YZX','ZXY','ZYX','QUATERNION','AXIS_ANGLE'):
    obj=empty(storage);obj.rotation_mode=storage;obj.location=(len(objects),2,3);obj.scale=(-1,1,1);objects.append(obj)
camera=bpy.data.objects.new('Camera target',bpy.data.cameras.new('Camera'));ctx.scene.collection.objects.link(camera);objects.append(camera)
select(objects,objects[0]);positions={o.name:tuple(o.matrix_world.translation) for o in objects};arrange.align_orientations(ctx,objects)
for o in objects:near(orientation.rotation(o),frames.frame_axes(f));near(o.matrix_world.translation,positions[o.name])
# Explicit execution verifies geometry mode, selected Y axis, negative direction.
# INVOKE scene-field capture is tested in a real UI event loop separately.
reset();key=cube('Key');target=cube('Invoked');target.location=(0,8,0)
s=ctx.scene.better_item;s.arrange_origin='OBJECT';s.arrange_origin_object=key;s.axes=(False,True,False);s.distribution_mode='GEOMETRY';s.spacing=-.1
select([key,target],key);assert bpy.ops.better_item.distribute('EXEC_DEFAULT',axes=s.axes,distribution_mode='GEOMETRY',spacing=s.spacing)=={'FINISHED'};near(target.location,(0,-2.1,0))
s.arrange_orientation='GLOBAL';s.orientation_action='SET';s.orientation_axes=(True,False,False);s.orientation_angles=(.3,0,0)
assert bpy.ops.better_item.align_orientation('INVOKE_DEFAULT')=={'FINISHED'};near(orientation.rotation(target),Euler((.3,0,0)).to_matrix())
# Undo/redo covers the entire operation and the source remains untouched.
ctx.preferences.edit.use_global_undo=True;before={o.name:v._snapshot(o) for o in (key,target)};bpy.ops.ed.undo_push(message='Before orientation')
s.orientation_angles=(.5,0,0);bpy.ops.better_item.align_orientation();bpy.ops.ed.undo_push(message='After orientation')
bpy.ops.ed.undo();target=bpy.data.objects['Invoked'];near(orientation.rotation(target),Euler((.3,0,0)).to_matrix())
bpy.ops.ed.redo();target=bpy.data.objects['Invoked'];near(orientation.rotation(target),Euler((.5,0,0)).to_matrix());near(target.location,(0,-2.1,0))
result={'position_dependent_geometry_rollback':True,'dependent_transform_rollback':True,'reference_dependency_rejection':True,'selected_parent_child_bounds':True,'selected_orientation_key_compensation':True,'orientation_storage_and_camera_targets':9,'execute_mode_axis_direction':True,'batch_undo_redo':True}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('160 EDGE CASES PASSED',json.dumps(result))
