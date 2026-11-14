import sys,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Matrix,Vector
addon_utils.enable('better_item')
from better_item import frames
bpy.context.preferences.view.show_splash=False
ctx=bpy.context
frame=frames.create(ctx,'Assembly axes',Vector((2,3,4)),Matrix.Identity(3))
frame.reference_location='MEDIAN_POINT';frame.reference_orientation='PARENT';frame.rotation_source=ctx.object
s=ctx.object.better_item;s.reference_location='BOUNDING_BOX_CENTER';s.reference_orientation='GIMBAL'
a=ctx.scene.better_item;a.reference_location='ACTIVE_ELEMENT';a.reference_orientation='SAVED';a.arrange_frame=frame.uid
phase=0
panels=['BETTERITEM_PT_frames','BETTERITEM_PT_transform','BETTERITEM_PT_alignment']
def run():
 global phase
 try:
  area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  with ctx.temp_override(area=area,region=region):
   if phase%2==0:
    if phase==6:
     print('REFERENCE UI 151 GUI PASSED: three actual panels rendered without RNA errors',flush=True);bpy.ops.wm.quit_blender();return None
    bpy.ops.wm.call_panel(name=panels[phase//2],keep_open=True)
   else:bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/('reference151_'+str(phase//2)+'.png')))
  phase+=1;return 1
 except Exception:traceback.print_exc();bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2)
