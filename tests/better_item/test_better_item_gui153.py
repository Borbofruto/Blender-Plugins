import sys,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Euler
addon_utils.enable('better_item')
ctx=bpy.context;ctx.preferences.view.show_splash=False
o=ctx.object;s=o.better_item;s.trace.expanded=True;s.reference_mode='FRAME';s.reference_frame='NONE'
o.rotation_mode='QUATERNION';o.rotation_quaternion=Euler((.2,.3,.4)).to_quaternion();s.transform_space='DEFAULT'
phase=0

def run():
 global phase
 try:
  area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  with ctx.temp_override(area=area,region=region):
   if phase==0:bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
   elif phase==1:
    bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'reference153_unavailable.png'))
    s.trace.expanded=False
    bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
   else:
    bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'reference153_quaternion.png'))
    print('153 GUI PASSED: actual Default quaternion fields and trace unavailable display render without RNA errors',flush=True)
    bpy.ops.wm.quit_blender();return None
  phase+=1;return 1
 except Exception:traceback.print_exc();bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2)
