import sys,traceback,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Matrix,Vector,Euler
addon_utils.enable('better_item')
from better_item import frames,native_refs
ctx=bpy.context;ctx.preferences.view.show_splash=False
obj=ctx.object;parent=bpy.data.objects.new('Technical Assembly',None);ctx.scene.collection.objects.link(parent);obj.parent=parent;parent.location=(4,0,0);ctx.view_layer.update()
f=frames.create(ctx,'Assembly axes',Vector((.33122,3.2745,2.048)),Euler((math.pi/4,math.pi/4,0)).to_matrix());uid=f.uid
s=obj.better_item;s.reference_mode='FRAME';s.reference_frame=uid;s.use_reference_pivot=True
native_refs.publish(ctx,f,select=True)
redraw=[];original_redraw=native_refs._redraw_scene
def recorded(scene,windows):redraw.append(scene.as_pointer());original_redraw(scene,windows)
native_refs._redraw_scene=recorded
phase=0
def run():
 global phase
 try:
  area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  with ctx.temp_override(area=area,region=region):
   f=frames.find(ctx.scene,uid)
   if phase==0:
    bpy.ops.transform.delete_orientation()
   elif phase==1:
    assert not f.native_enabled and not f.native_name
    assert redraw,'External deletion did not request redraw'
    bpy.ops.wm.call_panel(name='BETTERITEM_PT_frames',keep_open=True)
   elif phase==2:
    bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'reference152_export_removed.png'))
    s.transform_space='DEFAULT';bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
   elif phase==3:
    bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'reference152_default.png'))
    s.transform_space='REFERENCE';bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
   elif phase==4:
    bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'reference152_reference.png'))
    print('152 GUI PASSED: native-menu deletion detected by real timer, redraw requested without panel interaction, Default/Local and Reference panels with no keyframe UI',flush=True)
    bpy.ops.wm.quit_blender();return None
  phase+=1;return 1
 except Exception:traceback.print_exc();bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2)
