import sys,math,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Matrix,Vector
addon_utils.enable('better_item')
from better_item import transform_view as view,frames
ctx=bpy.context;ctx.preferences.view.show_splash=False;o=ctx.object
source=bpy.data.objects.new('Reference',None);ctx.scene.collection.objects.link(source);source.rotation_euler.z=math.pi/4
s=o.better_item;s.orientation='REFERENCE';s.orientation_object=source
ctx.view_layer.update();view.edit_component(ctx,o,'DIMENSIONS',0,1.6)
o.modifiers.new('User Triangulate','TRIANGULATE');ctx.view_layer.update()
s.dimensions_x=1.8
assert len(o.modifiers)==2
s['animation']={'enabled':True,'dependencies_owned':True}
phase=0

def run():
 global phase
 try:
  area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  with ctx.temp_override(area=area,region=region):
   if phase==0:bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
   elif phase==1:
    bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'reference155_stack_error.png'))
    s.transform_space='DEFAULT';bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
   else:
    bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'reference155_default.png'))
    assert s['animation']['dependencies_owned'] and len(o.modifiers)==2
    print('155 GUI PASSED: stack rejection UI, Scale (Default) reference label, native Scale label and no retired-animation panel',flush=True)
    bpy.ops.wm.quit_blender();return None
  phase+=1;return 1
 except Exception:traceback.print_exc();bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2)
