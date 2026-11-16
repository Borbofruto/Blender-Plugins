"""Record public API capabilities used by Better Item, not just version strings."""
import sys,json,platform
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
import better_item as addon
from better_item import native_refs
root=Path(__file__).parent
result={'passed':False,'blender':bpy.app.version_string,'version':list(bpy.app.version),'build_hash':bpy.app.build_hash.decode(),'python':sys.version,'numpy':np.__version__,'platform':platform.platform()}
result['scene_orientation_attributes']=[n for n in dir(bpy.context.scene) if 'orient' in n]
slot=bpy.context.scene.transform_orientation_slots[0]
result['slot_type_enum']=[x.identifier for x in slot.bl_rna.properties['type'].enum_items]
result['slot_type_functions']=list(slot.bl_rna.functions.keys())
result['capabilities']={
 'NodesModifier.persistent_uid':'persistent_uid' in bpy.types.NodesModifier.bl_rna.properties,
 'NodeTree.interface':'interface' in bpy.types.NodeTree.bl_rna.properties,
 'Object.to_mesh':'to_mesh' in bpy.types.Object.bl_rna.functions,
 'Object.to_mesh_clear':'to_mesh_clear' in bpy.types.Object.bl_rna.functions,
 'UILayout.prop_search':'prop_search' in bpy.types.UILayout.bl_rna.functions,
 'UILayout.panel':'panel' in bpy.types.UILayout.bl_rna.functions,
 'Context.temp_override':hasattr(bpy.context,'temp_override'),
 'Scene.transform_orientations':hasattr(bpy.context.scene,'transform_orientations')}
addon.register()
result['registered']=all(hasattr(cls,'bl_rna') for cls in addon.classes)
result['custom_discovery_removed']=not hasattr(native_refs,'discover_names')
result['modifier_api']={}
group=bpy.data.node_groups.new('Compatibility probe','GeometryNodeTree')
group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
for kind in ('GeometryNodeInputPosition','ShaderNodeVectorMath','ShaderNodeCombineXYZ','GeometryNodeSetPosition','NodeGroupInput','NodeGroupOutput'):
 node=group.nodes.new(kind)
 result['modifier_api'][kind]={'inputs':[(s.name,s.identifier,s.bl_idname) for s in node.inputs],'outputs':[(s.name,s.identifier,s.bl_idname) for s in node.outputs]}
mod=bpy.context.object.modifiers.new('API probe','NODES');mod.node_group=group
result['modifier_input_properties']=hasattr(mod,'properties')
result['modifier_uid']=mod.persistent_uid if hasattr(mod,'persistent_uid') else None
result['timer_registered']=bpy.app.timers.is_registered(native_refs.sync)
addon.unregister()
result['unregistered']=not hasattr(bpy.types.Scene,'better_item')
result['passed']=result['registered'] and result['unregistered'] and all(v for k,v in result['capabilities'].items() if k!='Scene.transform_orientations')
(root/'api_probe.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert result['passed'],result
print('API PROBE PASSED',bpy.app.version_string)
