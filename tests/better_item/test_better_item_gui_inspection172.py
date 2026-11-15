"""Real-sidebar redraw and native timer must reuse a stable inspection."""
import sys,json,traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy
import better_item as addon
addon.BETTERITEM_PT_transform.bl_options={'DEFAULT_CLOSED'};addon.frames.BETTERITEM_PT_frames.bl_options={'DEFAULT_CLOSED'};addon.register()
from better_item import distribution as d,native_refs
root=Path(__file__).parent;calls=0;phase=0;baseline=None;errors=[];original=d._inspect_spacing

def counted(*args):
 global calls
 calls+=1;return original(*args)
d._inspect_spacing=counted
ctx=bpy.context;ctx.preferences.view.show_splash=False
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add();template=ctx.object;template.select_set(False)
objects=[]
for i in range(600):
 o=bpy.data.objects.new('Panel%04d'%i,template.data);ctx.scene.collection.objects.link(o);o.location.x=3+3*i;o.select_set(True);objects.append(o)
ctx.view_layer.objects.active=objects[0];ctx.view_layer.update();s=ctx.scene.better_item;s.arrange_origin='GLOBAL';s.arrange_orientation='GLOBAL';s.distribution_mode='GEOMETRY';s.distribution_method='OFFSET'
area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');area.spaces.active.show_region_ui=True

def run():
 global phase,baseline
 try:
  with native_refs.view_context(bpy.context):
   next(r for r in area.regions if r.type=='UI').active_panel_category='Better Item'
   d.inspect_spacing(bpy.context,objects)
   if phase==0:baseline=calls
   else:assert calls==baseline,('redraw/timer recalculated unchanged inspection',phase,calls,baseline)
   area.tag_redraw()
  phase+=1
  if phase==6:
   (root/'test_better_item_gui_inspection172.results.json').write_text(json.dumps({'passed':True,'objects':600,'stable_timer_redraw_ticks':5,'full_inspections':calls},indent=2));bpy.ops.wm.quit_blender();return None
  return .5
 except Exception:
  (root/'test_better_item_gui_inspection172.results.json').write_text(json.dumps({'passed':False,'traceback':traceback.format_exc()},indent=2));traceback.print_exc();bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2.)
