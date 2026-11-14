import sys,math,inspect,numpy as np,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Vector,Matrix
addon_utils.enable('better_item')
import better_item as addon
from better_item import transform_view as view,frames,native_refs,references
from better_item.math_core import BetterItemError
ctx=bpy.context;o=ctx.object
source=bpy.data.objects.new('Reference',None);ctx.scene.collection.objects.link(source);source.rotation_euler.z=math.pi/4
s=o.better_item;s.orientation='REFERENCE';s.orientation_object=source;ctx.view_layer.update()
owned=lambda:[m for m in o.modifiers if m.type=='NODES' and m.node_group and m.node_group.get('better_item_affine')==1]
def state():
 return (view._snapshot(o),[(m.as_pointer(),m.name,m.node_group.as_pointer() if m.type=='NODES' and m.node_group else None) for m in o.modifiers],
 [(m.node_group.as_pointer(),tuple(tuple(m.node_group.nodes['Better Item Row %d'%i].inputs[1].default_value) for i in range(3))) for m in owned()],
 [tuple(v.co) for v in o.data.vertices])
def reject(code,target):
 before=state()
 try:view.set_dimensions(ctx,o,target)
 except BetterItemError as exc:assert code in str(exc),str(exc)
 else:raise AssertionError('Invalid stack must reject')
 assert state()==before
# Normal path still creates and reuses one affine stage, independent of its name.
view.edit_component(ctx,o,'DIMENSIONS',0,1.6);assert len(owned())==1
mod=owned()[0];mod.name='Renamed by user';pointer=mod.as_pointer()
view.edit_component(ctx,o,'DIMENSIONS',0,1.8);assert len(owned())==1 and owned()[0].as_pointer()==pointer
# A downstream modifier forbids both affine and native-compatible edits.
tri=o.modifiers.new('User Triangulate','TRIANGULATE');ctx.view_layer.update()
before=view.values(ctx,o,'DIMENSIONS');reject('BI-M002',(before[0]*1.1,before[1],before[2]));reject('BI-M002',tuple(v*1.1 for v in before))
assert len(owned())==1
# Reading remains valid even when the stack cannot be edited.
assert all(v>0 for v in view.values(ctx,o,'DIMENSIONS'))
o.modifiers.remove(tri);view.edit_component(ctx,o,'DIMENSIONS',0,1.9);assert len(owned())==1
# Pre-existing duplicates are reported, not silently selected/deleted/applied.
duplicate=o.modifiers.new('Existing duplicate','NODES');duplicate.node_group=mod.node_group;ctx.view_layer.update()
reject('BI-M001',tuple(v*1.1 for v in view.values(ctx,o,'DIMENSIONS')));assert len(owned())==2
o.modifiers.remove(duplicate);mod.show_viewport=False;ctx.view_layer.update()
reject('Enable',tuple(v*1.1 for v in view.values(ctx,o,'DIMENSIONS')))
mod.show_viewport=True;ctx.view_layer.update()
# No animation schema, migration or fallback surface remains in the active addon.
assert not hasattr(addon,'_retire_animation_dependencies')
assert not hasattr(view,'_animated_tree')
assert set(inspect.signature(frames.apply_reference).parameters)=={'frame','component'}
assert not hasattr(s,'animation')
# Resolving Apply Reference is atomic when one component is unavailable.
f=frames.create(ctx,'Partial',Vector((7,8,9)),Matrix.Identity(3));uid=f.uid
f.position_mode='OBJECT';f.position_source=source;f.rotation_mode='OBJECT';f.rotation_source=None
before=(tuple(f.position),tuple(f.rotation),f.position_mode,f.rotation_mode,f.position_source)
try:frames.apply_reference(f)
except BetterItemError:pass
else:raise AssertionError('Missing component cannot be silently applied')
assert before==(tuple(f.position),tuple(f.rotation),f.position_mode,f.rotation_mode,f.position_source)
frames.apply_reference(f,'POSITION');assert f.position_mode=='MANUAL' and f.rotation_mode=='OBJECT'
# Compatibility enum serials remain unchanged despite removing the table slice.
for typ,expected in [(addon.BetterItemObjectSettings,['GLOBAL','LOCAL','REFERENCE','VIEWPORT','SAVED','NORMAL','GIMBAL','VIEW','CURSOR','PARENT','NATIVE']),
                     (addon.BetterItemSceneSettings,['GLOBAL','LOCAL','REFERENCE','SAVED','VIEWPORT','NORMAL','GIMBAL','VIEW','CURSOR','PARENT','NATIVE'])]:
 prop='orientation' if typ==addon.BetterItemObjectSettings else 'arrange_orientation'
 items=typ.bl_rna.properties[prop].enum_items
 assert [(i.identifier,i.value) for i in items]==list(zip(expected,range(len(expected))))
# Leftover authoring data and drivers are not managed, even when marked owned.
s['animation']={'enabled':True,'dependencies_owned':True,'user_data':17}
s['retired_stamp']=0.
curve=o.driver_add('better_item["retired_stamp"]');curve.driver.expression='0';curve.data_path='better_item.animation.dependency_stamp'
raw_before=s['animation'].to_dict();pointer=curve.as_pointer()
addon._clear_runtime(None);native_refs.sync()
assert s['animation'].to_dict()==raw_before
assert o.animation_data.drivers[0].as_pointer()==pointer
assert bpy.app.handlers.frame_change_post.count(view.clear_cache)==1
print('155 CLEANUP PASSED: one renamed final modifier reused; downstream/duplicate/disabled stacks reject atomically; reads remain valid; animation runtime/fallback removed; Apply atomicity and enum serials retained; leftover data untouched')
