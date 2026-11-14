import sys,traceback,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Vector
bpy.context.preferences.view.show_splash=False
addon_utils.enable('better_item',default_set=True)
from better_item import animation,frames
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
outer=bpy.data.objects.new('Outer Reference Parent',None);bpy.context.scene.collection.objects.link(outer)
source=bpy.data.objects.new('Animation Controller',None);bpy.context.scene.collection.objects.link(source);source.parent=outer
bpy.ops.mesh.primitive_cube_add(size=.5,location=(1,0,0));obj=bpy.context.object;obj.name='Relative Actor'
s=obj.better_item;s.pivot_mode='OBJECT';s.origin_object=source;s.orientation='REFERENCE';s.orientation_object=source
bpy.context.view_layer.update();animation.start(bpy.context,obj);a=s.animation
bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=11
bpy.context.scene.frame_set(1);animation.keyframe(obj,'LOCATION',1)
bpy.context.scene.frame_set(11);a.location=(3,0,0);animation.keyframe(obj,'LOCATION',11)
for curve in animation.object_curves(obj):
    for key in curve.keyframe_points:key.interpolation='LINEAR'
a.expanded=True
phase=0

def run():
    global phase
    try:
        area=next(area for area in bpy.context.screen.areas if area.type=='VIEW_3D')
        region=next(region for region in area.regions if region.type=='WINDOW')
        with bpy.context.temp_override(area=area,region=region):
            if phase==0:
                bpy.context.scene.frame_set(1);bpy.ops.screen.animation_play()
            elif phase==1:
                assert bpy.context.screen.is_animation_playing
                assert not a.error,a.error
                assert (obj.matrix_world.translation-source.matrix_world.translation-Vector(a.location)).length<1e-4
                bpy.ops.screen.animation_cancel(restore_frame=False)
                outer.location.x=10;bpy.context.view_layer.update()
            elif phase==2:
                # Actual depsgraph+timer update without changing timeline frame.
                assert not a.error,a.error
                assert abs(obj.matrix_world.translation.x-10-a.location.x)<1e-4
                bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
            elif phase==3:
                bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'better150_animation_gui.png'))
                bpy.data.objects.remove(source,do_unlink=True);bpy.context.view_layer.update()
            elif phase==4:
                assert not a.error,a.error
                assert a.warning
                f=frames.find(bpy.context.scene,a.binding_uid)
                assert f.position_mode==f.rotation_mode=='MANUAL'
                s.trace.expanded=True
                bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
            else:
                bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'better150_trace_gui.png'))
                print('REAL ANIMATION UI PASSED: actual playback, same-frame reference changes, source deletion fallback, relative RNA fields and trace panel',flush=True)
                bpy.ops.wm.quit_blender();return None
        phase+=1
        return 1.
    except Exception:
        traceback.print_exc();bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2)
