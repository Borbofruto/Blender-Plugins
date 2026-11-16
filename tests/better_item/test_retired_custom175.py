"""Real UI: retired custom references and retained native Frame export."""
import bpy,sys,json,traceback
from pathlib import Path
from mathutils import Vector,Matrix,Euler
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import better_item as addon
from better_item import references,frames,native_refs
from better_item.math_core import ReferencePending
root=Path(__file__).parent;result={'passed':False,'checks':[]};errors=[];phase=0
for panel in (addon.BETTERITEM_PT_transform,addon.BETTERITEM_PT_alignment,frames.BETTERITEM_PT_frames):
 def wrap(draw):
  def checked(self,ctx):
   try:draw(self,ctx)
   except Exception:errors.append(traceback.format_exc());raise
  return checked
 panel.draw=wrap(panel.draw)
addon.register();ctx=bpy.context;ctx.preferences.view.show_splash=False;obj=ctx.object;scene=ctx.scene
f=frames.create(ctx,'Export still supported',Vector(),Euler((.2,.3,.4)).to_matrix())
obj.better_item.transform_space='REFERENCE'
area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');area.spaces.active.show_region_ui=True

def pending(call):
 try:call()
 except ReferencePending as exc:assert exc.severity=='INFO' and 'removed' in str(exc);return
 raise AssertionError('Retired source was accepted or silently replaced')

def run():
 global phase
 try:
  with native_refs.view_context(bpy.context):
   ctx=bpy.context;next(r for r in area.regions if r.type=='UI').active_panel_category='Better Item'
   if phase==0:
    assert not hasattr(native_refs,'discover_names') and not hasattr(native_refs,'_custom_cache')
    assert not hasattr(bpy.types.Scene,'better_item_orientation_names')
    for frame in (False,True):
     for arrangement in (False,True):assert 'NATIVE' not in [item[0] for item in references._choices('axes',frame,arrangement)]
    bpy.ops.transform.create_orientation(name='External native source',use=True)
    before=tuple(obj.matrix_world[i][j] for i in range(4) for j in range(4))
    obj.better_item.orientation='NATIVE';obj.better_item.reference_native='External native source'
    scene.better_item.arrange_orientation='NATIVE';scene.better_item.reference_native='External native source'
    f.rotation_mode='NATIVE';f.native_source='External native source'
    assert obj.better_item.reference_orientation=='NATIVE' and f.reference_orientation=='NATIVE'
    for call in (lambda:references.axes(ctx,obj.better_item,obj),lambda:references.axes(ctx,scene.better_item,obj,True),lambda:frames.frame_axes(f,ctx)):pending(call)
    assert before==tuple(obj.matrix_world[i][j] for i in range(4) for j in range(4))
    result['checks'].append('No discovery/cache/search registration; no custom source in new choices; old files explicitly unavailable without pose changes')
   elif phase==1:
    bpy.ops.screen.screenshot(filepath=str(root/'ui175-retired.png'))
    f.reference_orientation='MANUAL';f.rotation=(.2,.3,.4)
    obj.better_item.reference_orientation='SAVED';obj.better_item.orientation_frame=f.uid
    scene.better_item.reference_orientation='SAVED';scene.better_item.arrange_frame=f.uid
    native_refs.publish(ctx,f,select=True)
    assert f.native_enabled;native_name=f.native_name;before=obj.matrix_world.translation.copy()
    bpy.ops.transform.translate(value=(1,0,0),orient_type=native_name)
    ctx.view_layer.update();expected=frames.frame_axes(f,ctx).col[0]
    assert (obj.matrix_world.translation-before-expected).length<1e-5
    bpy.ops.transform.delete_orientation()
    result['checks'].append('Native Frame export and G operation in exported axes remain functional')
   elif phase==2:
    assert not f.native_enabled and not f.native_name
    result['checks'].append('Deletion through native Blender UI is observed without recreating orientation')
    # Persist old sources intentionally, so a new process checks honest labels.
    obj.better_item.orientation='NATIVE';obj.better_item.reference_native='External native source'
    scene.better_item.arrange_orientation='NATIVE';scene.better_item.reference_native='External native source'
    f.rotation_mode='NATIVE';f.native_source='External native source'
    bpy.ops.wm.save_as_mainfile(filepath=str(root/'retired175.blend'))
   elif phase==3:
    assert not errors,errors
    addon.unregister();addon.register();native_refs.sync();addon.unregister()
    result['checks'].append('Repeated registration lifecycle without orphan handlers')
    result['passed']=True;finish();return None
   phase+=1
 except Exception:result['error']=traceback.format_exc();finish();return None
 return .6

def finish():
 result['draw_errors']=errors;(root/'test_retired_custom175.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');bpy.ops.wm.quit_blender()
bpy.app.timers.register(run,first_interval=1)
