import sys,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Vector,Matrix
addon_utils.enable('better_item',default_set=True)
import better_item as addon
from better_item import references,frames,native_refs,arrange,engine
ctx=bpy.context
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def empty(name,location):
 o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);o.location=location;return o
def near(a,b):assert np.allclose(a,b,rtol=0,atol=3e-5),(a,b)
parent=empty('Parent',(10,20,30));parent.rotation_euler=(.2,.4,.6)
target=empty('Target',(1,2,3));target.parent=parent
controller=empty('Controller',(-3,7,2));controller.rotation_euler=(.1,.3,-.2)
ctx.view_layer.objects.active=target;target.select_set(True);ctx.view_layer.update()
userframe=frames.create(ctx,'Source Frame',Vector((4,5,6)),Matrix.Identity(3));uid=userframe.uid
frame=frames.create(ctx,'Edited Frame',Vector(),Matrix.Identity(3));edited=frame.uid
s=target.better_item;a=ctx.scene.better_item
for owner in (s,a):
 fields=references._FIELDS[owner==a]
 setattr(owner,fields['axes_object'],controller);setattr(owner,fields['origin_object'],controller)
 setattr(owner,fields['axes_frame'],uid);setattr(owner,fields['origin_frame'],uid)
frame.position_source=frame.rotation_source=target
frame.position_frame=frame.rotation_frame=uid
# All ordinary native/added choices have one selector in all three contexts.
locs=[c[0] for c in references._LOCATION_CHOICES]
rots=[c[0] for c in references._ORIENTATION_CHOICES if c[0]!='NATIVE']
assert locs==['GLOBAL','FRAME','OBJECT','BOUNDING_BOX_CENTER','CURSOR','INDIVIDUAL_ORIGINS','MEDIAN_POINT','ACTIVE_ELEMENT']
assert not {'LOCAL','VIEWPORT','PIVOT'}&set(locs+rots)
for kind,choices in [('origin',locs),('axes',rots)]:
 prop='reference_location' if kind=='origin' else 'reference_orientation'
 for value in choices:
  for owner in (s,a,frame):
   setattr(owner,prop,value);assert getattr(owner,prop)==value,(prop,value,getattr(owner,prop))
  # Object in frame needs the same chosen source; Parent frame uses explicit child.
  if value in {'OBJECT','REFERENCE'}:frame.position_source=frame.rotation_source=controller
  elif value=='PARENT':frame.position_source=frame.rotation_source=target
  left=references.origin(ctx,s,target)[0] if kind=='origin' else references.axes(ctx,s,target)
  middle=references.origin(ctx,a,target,True)[0] if kind=='origin' else references.axes(ctx,a,target,True)
  right=frames.frame_origin(frame,ctx) if kind=='origin' else frames.frame_axes(frame,ctx)
  near(left,middle);near(left,right)
# The same renderer calls/properties/icons, no extra Pivot dropdown or mode tabs.
from types import SimpleNamespace
class Layout:
 def __init__(self,calls):self.calls=calls
 def __getattr__(self,name):
  if name in {'row','box','column'}:return lambda *a,**kw:self
  if name=='prop':return lambda owner,prop,**kw:self.calls.append(('prop',prop,kw))
  if name=='label':return lambda **kw:self.calls.append(('label',kw))
  if name=='operator':return lambda *a,**kw:SimpleNamespace()
  if name=='template_list':return lambda *a,**kw:None
  raise AttributeError(name)
for owner in (s,a,frame):owner.reference_location='BOUNDING_BOX_CENTER';owner.reference_orientation='GIMBAL'
logs=[]
for owner,isarr,isframe in [(s,False,False),(a,True,False),(frame,False,True)]:
 calls=[];references.draw_component(Layout(calls),owner,'axes',isarr,isframe);references.draw_component(Layout(calls),owner,'origin',isarr,isframe);logs.append(calls)
assert logs[0]==logs[1]==logs[2],logs
for owner in (s,a,frame):
 for prop in ('reference_location','reference_orientation'):
  items=owner.bl_rna.properties[prop].enum_items
  for item in items:
   if item.identifier:assert item.icon!='NONE',(prop,item.identifier)
calls=[];addon.BETTERITEM_PT_alignment.draw(SimpleNamespace(layout=Layout(calls)),ctx)
assert not any(c[0]=='prop' and c[1] in {'reference','reference_pivot','arrange_origin','arrange_orientation'} for c in calls)
# AUTO uses the single reference; explicit old operator modes stay script-compatible.
for o in list(ctx.selected_objects):o.select_set(False)
objects=[empty('Arrange '+str(i),(x,i,0)) for i,x in enumerate((-5,1,9))]
for o in objects:o.select_set(True)
ctx.view_layer.objects.active=objects[1];ctx.view_layer.update();a.reference_orientation='GLOBAL'
a.reference_location='GLOBAL'
origins={o.name:tuple(o.matrix_world.translation) for o in objects}
result=arrange.plan(ctx,objects,origins,(True,False,False),'AUTO')
for v in result.values():near(v[0],0)
a.reference_location='OBJECT';a.arrange_origin_object=controller
result=arrange.plan(ctx,objects,origins,(True,False,False),'AUTO',spacing=2)
assert sorted(round(v[0],5) for v in result.values())==[-1,1,3]
a.reference_location='ACTIVE_ELEMENT'
result=arrange.plan(ctx,objects,origins,(True,False,False),'AUTO',spacing=2)
near(result[objects[1].name],origins[objects[1].name])
a.reference_location='BOUNDING_BOX_CENTER'
result=arrange.plan(ctx,objects,origins,(True,False,False),'AUTO',spacing=2)
assert sorted(round(v[0],5) for v in result.values())==[-5,2,9]
# Frame mode inherits the same operation from its Location component.
frame=frames.find(ctx.scene,edited);frame.reference_location='BOUNDING_BOX_CENTER'
a.arrange_reference_mode='FRAME';a.arrange_reference_frame=edited
assert arrange.operation_reference(ctx)=='SELECTION'
frame.reference_location='GLOBAL';assert arrange.operation_reference(ctx)=='REFERENCE'
frame.reference_location='MANUAL';frame.position=(8,9,10)
near(frames.frame_origin(frame,ctx),(8,9,10))
print('UNIFIED REFERENCE UI PASSED: flat icon choices, shared frame/consumer rendering, source parity, AUTO point/bounds arrangements and fixed active origin')
