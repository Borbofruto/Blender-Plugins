"""One-shot fault injection: observe the real timer, not a direct sync call."""
import sys
import json
import traceback
from pathlib import Path

sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'Blender-Plugins/src'))
import bpy
import better_item as addon
from mathutils import Vector, Matrix
from better_item import native_refs as nr, frames

addon.register()
if bpy.app.timers.is_registered(nr.sync):bpy.app.timers.unregister(nr.sync)
nr.sync()
source=bpy.data.objects.new('Timer failure source',None)
bpy.context.scene.collection.objects.link(source)
frame=frames.create(bpy.context,'Timer fault probe',Vector(),Matrix.Identity(3))
frame.rotation_mode='OBJECT'
frame.rotation_source=source
with nr.view_context(bpy.context) as ctx:nr.publish(ctx,frame)
original_named=nr.named
calls=0
phase=0
result=dict(blender=bpy.app.version_string,kind='one-shot synthetic RuntimeError; not a spontaneous production crash',
            initial_timer_registered=True,initial_export_enabled=frame.native_enabled)
def faulty_named(scene,name):
    global calls
    calls+=1
    if calls==1:raise RuntimeError('Injected one-shot native orientation read failure')
    return original_named(scene,name)
nr.named=faulty_named
bpy.app.timers.register(nr.sync,first_interval=.1,persistent=True)

def observe():
    global phase
    done=False
    try:
        if phase==0:
            result['timer_registered_after_fault']=bpy.app.timers.is_registered(nr.sync)
            result['sync_reentry_flag']=nr._syncing
            result['fault_calls']=calls
            nr.named=original_named
            source.rotation_euler.z=.5
            bpy.context.view_layer.update()
            phase=1
            return .5
        actual=original_named(bpy.context.scene,frame.native_name).matrix.copy()
        expected=frames.frame_axes(frame)
        result['export_error_after_source_change']=max(abs(actual[i][j]-expected[i][j]) for i in range(3) for j in range(3))
        result['export_still_enabled']=frame.native_enabled
        result['reproduced']=(not result['timer_registered_after_fault'] and result['fault_calls']==1
                               and result['export_still_enabled'] and result['export_error_after_source_change']>.1)
        done=True
    except Exception:
        result['probe_error']=traceback.format_exc()
        done=True
    finally:
        if done:
            nr.named=original_named
            path=root/'ui-assessment'/('native-timer-failure-'+bpy.app.version_string.replace(' ','-')+'.json')
            path.write_text(json.dumps(result,indent=2),encoding='utf-8')
            print('NATIVE TIMER FAULT OBSERVATION',json.dumps(result),flush=True)
            addon.unregister()
            window=next(iter(bpy.context.window_manager.windows))
            with bpy.context.temp_override(window=window):bpy.ops.wm.quit_blender()
    return None
bpy.app.timers.register(observe,first_interval=1.)
