"""Blender UI regression: scene custom orientations and shared source picker."""
import sys,json,traceback
from pathlib import Path
from mathutils import Matrix,Vector
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,numpy as np
import better_item as addon
from better_item import native_refs,references,frames
from better_item.math_core import ReferencePending
root=Path(__file__).parent;result={'passed':False,'checks':[]};errors=[];phase=0
for panel in (addon.BETTERITEM_PT_transform,addon.BETTERITEM_PT_alignment,frames.BETTERITEM_PT_frames):
 def wrap(original):
  def checked(self,ctx):
   try:original(self,ctx)
   except Exception:errors.append(traceback.format_exc());raise
  return checked
 panel.draw=wrap(panel.draw)
addon.register()
ctx=bpy.context;ctx.preferences.view.show_splash=False;scene=ctx.scene;obj=ctx.object
obj.better_item.transform_space='REFERENCE';obj.better_item.reference_orientation='NATIVE'
scene.better_item.reference_orientation='NATIVE'
f=frames.create(ctx,'Custom Source',Vector(),Matrix.Identity(3));f.reference_orientation='NATIVE'
area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');area.spaces.active.show_region_ui=True
names=('A "quoted" orient',"B 'apostrophe' \\ path",'C: rotação 漢字')

def expect_pending(owner,arrange=False,frame=False):
 try:
  if frame:frames.frame_axes(owner,bpy.context)
  else:references.axes(bpy.context,owner,obj,arrange)
 except ReferencePending as exc:assert exc.severity=='INFO';return str(exc)
 raise AssertionError('Missing source accepted')

def run():
 global phase
 try:
  with native_refs.view_context(bpy.context):
   ctx=bpy.context;next(r for r in area.regions if r.type=='UI').active_panel_category='Better Item'
   if phase==0:
    assert native_refs.discovery_status(scene)==((),False)
    for owner,a,fr in ((obj.better_item,False,False),(scene.better_item,True,False),(f,False,True)):expect_pending(owner,a,fr)
    result['checks'].append('Empty scene: INFO setup state, all three consumers')
    for i,name in enumerate(names):
     obj.rotation_euler=(.1*i,.2*i,.3*i);ctx.view_layer.update()
     assert bpy.ops.transform.create_orientation(name=name,use=True)=={'FINISHED'}
    scene.transform_orientation_slots[0].type='LOCAL'
    try:scene.transform_orientation_slots[0].type=''
    except TypeError as exc:result['raw_enum']=str(exc)
   elif phase==1:
    assert tuple(x.name for x in scene.better_item_orientation_names)==names,(tuple(x.name for x in scene.better_item_orientation_names),names)
    assert scene.transform_orientation_slots[0].type=='LOCAL'
    other=bpy.data.scenes.new('Other Scene');assert native_refs.discover_names(other)==()
    native_refs.refresh_names(other);assert not other.better_item_orientation_names
    for owner,field in ((obj.better_item,'reference_native'),(scene.better_item,'reference_native'),(f,'native_source')):setattr(owner,field,names[1])
    result['checks'].append('Native creation discovered by real timer, Unicode/quotes, scene isolation, active slot preserved')
   elif phase==2:
    expected=native_refs.named(scene,names[1]).matrix.copy()
    for matrix in (references.axes(ctx,obj.better_item,obj),references.axes(ctx,scene.better_item,obj,True),frames.frame_axes(f,ctx)):assert np.allclose(matrix,expected)
    assert scene.transform_orientation_slots[0].type=='LOCAL'
    custom=native_refs.named(scene,names[1]);custom.name='Renamed orientation'
    result['checks'].append('Object / Scene / Frame sources resolve same matrix without changing viewport choice')
   elif phase==3:
    assert 'Renamed orientation' in scene.better_item_orientation_names and names[1] not in scene.better_item_orientation_names
    for owner,a,fr in ((obj.better_item,False,False),(scene.better_item,True,False),(f,False,True)):expect_pending(owner,a,fr)
    for name in native_refs.discover_names(scene):
     scene.transform_orientation_slots[0].type=name;bpy.ops.transform.delete_orientation()
    result['checks'].append('External rename removes old option; saved missing name gets setup guidance, no silent reassignment')
   elif phase==4:
    assert not scene.better_item_orientation_names
    for owner,a,fr in ((obj.better_item,False,False),(scene.better_item,True,False),(f,False,True)):expect_pending(owner,a,fr)
    bpy.ops.screen.screenshot(filepath=str(root/'ui174-empty.png'))
    # Export path stays available and appears in discovery too.
    f.rotation_mode='MANUAL';f.rotation=(.1,.2,.3)
    native_refs.publish(ctx,f,select=True)
   elif phase==5:
    assert f.native_name in scene.better_item_orientation_names
    obj.better_item.reference_native=f.native_name;scene.better_item.reference_native=f.native_name
    assert np.allclose(references.axes(ctx,obj.better_item,obj),frames.frame_axes(f,ctx))
    bpy.ops.screen.screenshot(filepath=str(root/'ui174-source.png'))
    result['checks'].append('External deletion clears scene list; published Better Item Frame discoverable')
    bpy.ops.wm.save_as_mainfile(filepath=str(root/'custom174.blend'))
   elif phase==6:
    assert not errors,errors
    original=native_refs.discover_names
    try:
     native_refs.discover_names=lambda scene:None
     native_refs.refresh_names(scene)
     assert native_refs.discovery_status(scene)[1]
     assert obj.better_item.reference_native==f.native_name
    finally:native_refs.discover_names=original
    native_refs.refresh_names(scene)
    result['checks'].append('Discovery adapter failure preserves saved source and exposes manual fallback')
    # Repeated lifecycle must remove the transient search collection cleanly.
    addon.unregister();assert not hasattr(bpy.types.Scene,'better_item_orientation_names')
    addon.register();native_refs.sync();assert scene.better_item_orientation_names
    result['checks'].append('Register/unregister lifecycle and rebuild')
    result['passed']=True;finish();return None
   phase+=1
 except Exception:result['error']=traceback.format_exc();finish();return None
 return .7

def finish():
 result['draw_errors']=errors
 (root/'test_better_item_custom174.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 bpy.ops.wm.quit_blender()
bpy.app.timers.register(run,first_interval=1)


