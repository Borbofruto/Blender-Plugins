"""Real event-loop/timer and panel smoke test in a separate factory-startup UI."""
import sys,json,traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Matrix,Vector
addon_utils.enable('better_item')
from better_item import native_refs,frames,transform_view as v
ctx=bpy.context;ctx.preferences.view.show_splash=False
root=Path(__file__).parent;phase=0
o=ctx.object;ref=bpy.data.objects.new('Reference',None);ctx.scene.collection.objects.link(ref)
ref.location=(3.21,-2.13,1.7);ref.rotation_euler=(.37,-.26,.61)
s=o.better_item;s.orientation='REFERENCE';s.orientation_object=ref;s.pivot_mode='OBJECT';s.origin_object=ref
ctx.view_layer.update();frames.set_position(ctx,o,(0,0,-.86))
f=frames.create(ctx,'Timer Frame',Vector(),Matrix.Identity(3));f.rotation_mode='OBJECT';f.rotation_source=ref
result={'passed':False,'phases':[]}
def run():
    global phase
    try:
        with native_refs.view_context(ctx):
            if phase==0:
                assert s.location_x==0 and s.location_y==0
                bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
                native_refs.publish(ctx,f,select=True);ref.rotation_euler.z+=.4;ctx.view_layer.update()
            elif phase==1:
                actual=native_refs.named(ctx.scene,f.native_name).matrix
                assert max(abs(a-b) for ra,rb in zip(actual,frames.frame_axes(f)) for a,b in zip(ra,rb))<1e-5
                bpy.ops.screen.screenshot(filepath=str(root/'ui157-transform.png'))
                ctx.scene.transform_orientation_slots[0].type=f.native_name;bpy.ops.transform.delete_orientation()
            elif phase==2:
                assert not f.native_enabled and f.native_name==''
                bpy.ops.wm.call_panel(name='BETTERITEM_PT_alignment',keep_open=True)
            elif phase==3:
                bpy.ops.wm.call_panel(name='BETTERITEM_PT_frames',keep_open=True)
            elif phase==4:
                bpy.ops.screen.screenshot(filepath=str(root/'ui157-frames.png'))
                # Draw the actual New Frame dialog; configuration remains in the editor.
                assert bpy.ops.better_item.new_frame('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
            else:
                bpy.ops.screen.screenshot(filepath=str(root/'ui157-new-frame.png'))
                result['passed']=True;result['phases'].append(phase)
                (root/'ui157.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
                print('157 REAL UI PASSED: fields, panel draws, New Frame dialog, live export timer and external native deletion',flush=True)
                bpy.ops.wm.quit_blender();return None
        result['phases'].append(phase);phase+=1;return 1.
    except Exception:
        traceback.print_exc();result['traceback']=traceback.format_exc()
        (root/'ui157.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2.)
