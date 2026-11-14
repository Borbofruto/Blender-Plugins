import sys,numpy as np
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Euler,Matrix,Vector
addon_utils.enable('better_item')
from better_item import transform_view as view,trace,frames
from better_item.math_core import BetterItemError
ctx=bpy.context;o=ctx.object;o.better_item.transform_space='DEFAULT'
for mode,field in [('QUATERNION','rotation_quaternion'),('AXIS_ANGLE','rotation_axis_angle')]:
 o.rotation_mode=mode;q=Euler((.3,.4,.5)).to_quaternion()
 if mode=='QUATERNION':o.rotation_quaternion=q
 else:
  axis,angle=q.to_axis_angle();o.rotation_axis_angle=(angle,*axis)
 ctx.view_layer.update();before=view._snapshot(o);world=o.matrix_world.copy()
 for call in (lambda:view.values(ctx,o,'ROTATION'),lambda:view.edit_component(ctx,o,'ROTATION',0,1.2),lambda:view._edit_default(o,'ROTATION',0,1.2)):
  try:call()
  except BetterItemError as exc:assert mode in str(exc) and field in str(exc),str(exc)
  else:raise AssertionError('Unsupported Euler API must reject '+mode)
  assert before==view._snapshot(o)
  assert np.allclose(world,o.matrix_world,rtol=0,atol=0)
 # The native widgets used by the UI still operate their actual storage.
 if mode=='QUATERNION':o.rotation_quaternion=Euler((.7,.2,.1)).to_quaternion()
 else:
  axis,angle=Euler((.7,.2,.1)).to_quaternion().to_axis_angle();o.rotation_axis_angle=(angle,*axis)
 ctx.view_layer.update();assert not np.allclose(world,o.matrix_world,rtol=0,atol=1e-5)
o.rotation_mode='ZYX';o.rotation_euler=(.1,.2,.3)
view.edit_component(ctx,o,'ROTATION',1,.8);assert abs(view.values(ctx,o,'ROTATION')[1]-.8)<1e-6
for kind,data in [('EMPTY',None),('CAMERA',bpy.data.cameras.new('Guard Camera')),('LIGHT',bpy.data.lights.new('Guard Light','POINT'))]:
 unsupported=bpy.data.objects.new('Guard '+kind,data);ctx.scene.collection.objects.link(unsupported);unsupported.better_item.transform_space='DEFAULT'
 snapshot=view._snapshot(unsupported)
 for call in (lambda:view.values(ctx,unsupported,'DIMENSIONS'),lambda:view.edit_component(ctx,unsupported,'DIMENSIONS',0,1)):
  try:call()
  except BetterItemError as exc:assert kind in str(exc) and 'unavailable' in str(exc).lower() and 'zero' not in str(exc).lower()
  else:raise AssertionError('Unsupported geometry must reject '+kind)
  assert snapshot==view._snapshot(unsupported)
# Keep the separate supported-geometry zero-dimension diagnostic.
o.scale=(0,1,1);ctx.view_layer.update()
try:view.edit_component(ctx,o,'DIMENSIONS',0,1)
except BetterItemError as exc:assert 'zero Dimension' in str(exc),str(exc)
else:raise AssertionError('A zero scale dimension needs its existing diagnostic')
o.scale=(1,1,1);o.better_item.trace.expanded=True
class Layout:
 def __init__(self):self.events=[]
 def box(self):return self
 def column(self,**kwargs):return self
 def label(self,**kwargs):self.events.append(('label',kwargs.get('text','')))
 def prop(self,owner,key,**kwargs):self.events.append(('prop',key))
def drawn():
 layout=Layout();trace.draw(layout,o);return layout.events
# Valid zero is a real vector; invalid reference is a label, not fake zeros.
s=o.better_item;s.reference_mode='INDIVIDUAL';s.pivot_mode='GLOBAL';s.orientation='GLOBAL'
events=drawn();assert ('prop','reference_origin') in events and ('prop','relative_location') in events
assert ('label','Unavailable') not in events
s.reference_mode='FRAME';s.reference_frame='NONE';events=drawn()
assert events.count(('label','Unavailable'))==2
assert ('prop','reference_origin') not in events and ('prop','relative_location') not in events
assert ('prop','world') in events and ('prop','local') in events
# Location can still resolve when only the Orientation source is missing.
s.reference_mode='INDIVIDUAL';s.orientation='REFERENCE';s.orientation_object=None;events=drawn()
assert ('prop','reference_origin') in events and ('prop','relative_location') not in events
assert events.count(('label','Unavailable'))==1
# Active-scene mismatch is explicitly unavailable as well.
other=bpy.data.scenes.new('Other context')
try:trace._read_reference(SimpleNamespace(scene=other),o,'origin')
except BetterItemError as exc:assert 'active scene' in str(exc)
else:raise AssertionError('Wrong scene must not produce a valid zero')
# No enum IDs, defaults or terminology changes in this patch.
assert any(c[0]=='BOUNDING_BOX_CENTER' and c[1]=='Bounding Box Center' for c in __import__('better_item.references',fromlist=['_LOCATION_CHOICES'])._LOCATION_CHOICES)
print('153 REGRESSIONS PASSED: quaternion/axis-angle read+write guards without mutation, native storage still editable, Euler supported, geometry diagnostics, valid-zero vs unavailable trace, independent components and wrong-scene detection')
