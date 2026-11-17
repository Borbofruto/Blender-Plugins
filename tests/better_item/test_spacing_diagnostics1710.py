"""Inspection diagnostics stay fresh without changing tuple or solver contracts."""
import sys,json
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
import bpy
import better_item as addon
from better_item import distribution as d,distribution_preview as live
from better_item.math_core import BetterItemError
addon.register()
ctx=bpy.context;s=ctx.scene.better_item
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
objects=[]
for x in (3,8):
    bpy.ops.mesh.primitive_plane_add(location=(x,0,0));objects.append(ctx.object)
for obj in objects:obj.select_set(True)
ctx.view_layer.objects.active=objects[0]
s.arrange_reference_mode='INDIVIDUAL';s.arrange_origin='GLOBAL';s.arrange_orientation='GLOBAL'
s.distribution_method='OFFSET';s.distribution_mode='VOLUME';s.axes=(True,False,False)
ctx.view_layer.update()
checks=[]
before=[tuple(o.matrix_world.translation) for o in objects]
value=d.inspect_spacing(ctx,objects)
assert value==('UNAVAILABLE',None) and isinstance(value,tuple)
assert 'BI-P003' in str(value.diagnostic)
assert not isinstance(value.diagnostic,BaseException)
assert 'closed' in value.diagnostic.summary
assert d.inspect_spacing(ctx,objects) is value,'invalid geometry result should also be cached'
try:d.apply(ctx,objects)
except BetterItemError as exc:assert 'BI-P003' in str(exc)
else:raise AssertionError('Open volume accepted')
assert before==[tuple(o.matrix_world.translation) for o in objects]
checks.append('geometry cause preserved in cached tuple; invalid apply is atomic')

class Labels:
    def __init__(self):self.text=[]
    def box(self,**kwargs):return self
    def row(self,**kwargs):return self
    def column(self,**kwargs):return self
    def split(self,**kwargs):return self
    def label(self,**kwargs):self.text.append(kwargs.get('text',''))
    def prop(self,*args,**kwargs):pass
    def operator(self,*args,**kwargs):return SimpleNamespace()
layout=Labels();d.draw(layout,ctx)
assert 'Complete references to measure spacing.' not in layout.text
assert 'closed' in ' '.join(layout.text)
checks.append('panel describes invalid volume instead of requesting valid references')

s.arrange_origin='OBJECT';s.arrange_origin_object=None
missing=d.inspect_spacing(ctx,objects)
assert missing==('UNAVAILABLE',None) and missing.diagnostic.pending
assert 'BI-P003' not in str(missing.diagnostic)
checks.append('actually missing reference retains its own pending diagnostic')
s.arrange_origin='GLOBAL';s.axes=(False,False,False)
no_axes=d.inspect_spacing(ctx,objects)
assert no_axes==('UNAVAILABLE',None) and 'Move axis' in no_axes.diagnostic.summary
s.axes=(True,False,False)

# Repair mesh data on the same objects: no selection or reference identity change.
vertices=[(0,0,0),(1,0,0),(0,1,0),(0,0,1)]
faces=[(0,2,1),(0,1,3),(1,2,3),(2,0,3)]
ctx.preferences.edit.use_global_undo=True
bpy.ops.ed.undo_push(message='Before volume repair')
for obj in objects:
    obj.data.clear_geometry();obj.data.from_pydata(vertices,[],faces);obj.data.update()
ctx.view_layer.update()
repaired=d.inspect_spacing(ctx,objects)
assert repaired[0]!='UNAVAILABLE' and not getattr(repaired,'diagnostic',None)
bpy.ops.ed.undo_push(message='After volume repair')
checks.append('geometry repair invalidates the cached refusal')
bpy.ops.ed.undo();ctx.view_layer.update()
objects=list(ctx.selected_objects)
assert 'BI-P003' in str(d.inspect_spacing(ctx,objects).diagnostic)
bpy.ops.ed.redo();ctx.view_layer.update();objects=list(ctx.selected_objects)
assert d.inspect_spacing(ctx,objects)[0]!='UNAVAILABLE'
checks.append('Undo and Redo restore the current geometry diagnostic')

s=ctx.scene.better_item;s.distribution_mode='VOLUME';s.distribution_live=True
assert live.active(ctx.scene)
with live.reference_context(ctx) as captured:
    target=live.captured_objects(captured)[0]
    target.data.clear_geometry();target.data.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)]);target.data.update()
ctx.view_layer.update()
assert 'BI-P003' in str(d.inspect_spacing(ctx,[]).diagnostic)
s.distribution_live=False
checks.append('Live captured targets preserve the current geometry cause')
result={'passed':True,'blender':bpy.app.version_string,'checks':checks}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('SPACING DIAGNOSTICS 1710',json.dumps(result))
