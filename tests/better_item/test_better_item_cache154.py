import sys,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Matrix
addon_utils.enable('better_item')
from better_item import transform_view as view
ctx=bpy.context;o=ctx.object;s=o.better_item
ctx.preferences.edit.use_global_undo=True
# External-source geometry invalidation with a nested Geometry Nodes group.
s.reference_mode='INDIVIDUAL';s.orientation='GLOBAL';s.pivot_mode='GLOBAL';o.location=(0,0,0);ctx.view_layer.update()
source=bpy.data.objects.new('External Geometry Controller',None);ctx.scene.collection.objects.link(source)
inner=bpy.data.node_groups.new('Indirect Offset','GeometryNodeTree')
inner.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');inner.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
n=inner.nodes;links=inner.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');setpos=n.new('GeometryNodeSetPosition');position=n.new('GeometryNodeInputPosition');mult=n.new('ShaderNodeVectorMath');mult.operation='MULTIPLY';info=n.new('GeometryNodeObjectInfo');info.inputs['Object'].default_value=source
links.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);links.new(position.outputs['Position'],mult.inputs[0]);links.new(info.outputs['Location'],mult.inputs[1]);links.new(mult.outputs['Vector'],setpos.inputs['Offset']);links.new(setpos.outputs['Geometry'],out.inputs['Geometry'])
outer=bpy.data.node_groups.new('Nested Indirect','GeometryNodeTree')
outer.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');outer.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
ni=outer.nodes.new('NodeGroupInput');no=outer.nodes.new('NodeGroupOutput');nested=outer.nodes.new('GeometryNodeGroup');nested.node_tree=inner;outer.links.new(ni.outputs['Geometry'],nested.inputs['Geometry']);outer.links.new(nested.outputs['Geometry'],no.inputs['Geometry'])
mod=o.modifiers.new('Indirect GN','NODES');mod.node_group=outer
for x in (0,1,3,0):
 source.location=(x,0,0);ctx.view_layer.update();measured=view.dimensions(o,Matrix.Identity(3));expected=(2*(1+x),2,2)
 assert np.allclose(measured,expected,atol=1e-5),(measured,expected)
 print('NESTED EXTERNAL CACHE:',x,measured)

pose=tuple(v for row in o.matrix_world for v in row)
# The previous bug retained the disabled-modifier dimensions across frame_set.
mod.show_viewport=False;ctx.view_layer.update();assert np.allclose(view.dimensions(o,Matrix.Identity(3)),(2,2,2))
mod.show_viewport=True
source.location.x=2;source.keyframe_insert('location',index=0,frame=1)
source.location.x=4;source.keyframe_insert('location',index=0,frame=2)
for frame,expect in ((1,6),(2,10),(1,6),(2,10)):
 ctx.scene.frame_set(frame)
 assert abs(view.dimensions(o,Matrix.Identity(3))[0]-expect)<1e-5
 assert pose==tuple(v for row in o.matrix_world for v in row)
# Native animated drivers on an external GN source, including subframes.
source.animation_data_clear()
control=bpy.data.objects.new('Driver controller',None);ctx.scene.collection.objects.link(control)
for frame,value in ((1,1.),(2,3.)):
 control['stretch']=value;control.keyframe_insert(data_path='["stretch"]',frame=frame)
for layer in control.animation_data.action.layers:
 for strip in layer.strips:
  if strip.type=='KEYFRAME':
   bag=strip.channelbag(control.animation_data.action_slot)
   for curve in bag.fcurves:
    for key in curve.keyframe_points:key.interpolation='LINEAR'
curve=source.driver_add('location',0);variable=curve.driver.variables.new();variable.name='stretch';variable.type='SINGLE_PROP';variable.targets[0].id=control;variable.targets[0].data_path='["stretch"]';curve.driver.expression='stretch'
for frame,subframe,expect in ((1,0,4),(1,.5,6),(2,0,8),(1,0,4)):
 ctx.scene.frame_set(frame,subframe=subframe)
 assert abs(view.dimensions(o,Matrix.Identity(3))[0]-expect)<1e-5
# Key edits while another frame was cached must not resurrect an old result.
ctx.scene.frame_set(2);control['stretch']=5.;control.keyframe_insert(data_path='["stretch"]',frame=2)
ctx.scene.frame_set(1);view.dimensions(o,Matrix.Identity(3));ctx.scene.frame_set(2)
assert abs(view.dimensions(o,Matrix.Identity(3))[0]-12)<1e-5
# Native shape key animation does not live in a modifier node tree.
bpy.ops.mesh.primitive_cube_add();shaped=ctx.object
shaped.shape_key_add(name='Basis');wide=shaped.shape_key_add(name='Wide')
for point in wide.data:point.co.x*=2
wide.value=0;wide.keyframe_insert('value',frame=1);wide.value=1;wide.keyframe_insert('value',frame=2)
for frame,expect in ((1,2),(2,4),(1,2)):
 ctx.scene.frame_set(frame);assert abs(view.dimensions(shaped,Matrix.Identity(3))[0]-expect)<1e-5
# Same-frame translation still reuses geometry; frame changes invalidate it.
ctx.scene.frame_set(1);view.dimensions(shaped,Matrix.Identity(3));key=view._geometry_key(shaped,ctx.evaluated_depsgraph_get());coords=view._geometry_cache[key]
shaped.location.x+=1;ctx.view_layer.update();view.dimensions(shaped,Matrix.Identity(3));assert view._geometry_cache[key] is coords
ctx.scene.frame_set(2);assert not view._geometry_cache and not view._dimension_cache
# Modifier toggles plus undo/redo retain the fresh evaluated result.
ctx.scene.frame_set(2);mod.show_viewport=True;ctx.view_layer.update();assert abs(view.dimensions(o,Matrix.Identity(3))[0]-12)<1e-5
bpy.ops.ed.undo_push(message='Visible indirect modifier')
mod.show_viewport=False;ctx.view_layer.update();assert abs(view.dimensions(o,Matrix.Identity(3))[0]-2)<1e-5
bpy.ops.ed.undo_push(message='Hidden indirect modifier')
bpy.ops.ed.undo();o=bpy.data.objects['Cube'];assert abs(view.dimensions(o,Matrix.Identity(3))[0]-12)<1e-5
bpy.ops.ed.redo();o=bpy.data.objects['Cube'];assert abs(view.dimensions(o,Matrix.Identity(3))[0]-2)<1e-5
print('154 CACHE PASSED: nested GN external dependencies, modifier toggles, native external keyframes/drivers, shape keys, frame/subframe changes, backward seeks, key edits, translation cache reuse, undo/redo and no target pose writes')
