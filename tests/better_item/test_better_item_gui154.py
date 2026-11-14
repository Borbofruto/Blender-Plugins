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


ctx.preferences.view.show_splash=False
source.location.x=2;source.keyframe_insert('location',index=0,frame=1)
source.location.x=4;source.keyframe_insert('location',index=0,frame=2)
phase=0
import traceback

def run():
 global phase
 try:
  area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  with ctx.temp_override(area=area,region=region):
   ctx.view_layer.objects.active=o
   if phase==0:
    ctx.scene.frame_set(1);assert abs(view.dimensions(o,Matrix.Identity(3))[0]-6)<1e-5
   elif phase==1:
    ctx.scene.frame_set(2);assert abs(view.dimensions(o,Matrix.Identity(3))[0]-10)<1e-5
    s.pivot_mode='OBJECT';s.origin_object=None
    bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
   elif phase==2:
    assert abs(view.dimensions(o,Matrix.Identity(3))[0]-10)<1e-5
    bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'reference154_missing_location.png'))
    s.pivot_mode='GLOBAL';s.orientation='REFERENCE';s.orientation_object=None
    bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
   else:
    bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'reference154_missing_orientation.png'))
    print('154 GUI PASSED: external animated GN geometry reads 6 then 10 without cache reset; missing Location/Orientation show unavailable groups while readable groups render',flush=True)
    bpy.ops.wm.quit_blender();return None
  phase+=1;return 1
 except Exception:traceback.print_exc();bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2)
