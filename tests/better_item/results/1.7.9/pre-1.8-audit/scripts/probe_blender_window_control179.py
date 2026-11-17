"""Control: closing a real secondary window without importing the addon."""
import json,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
result={'passed':False,'blender':bpy.app.version_string,'addon_imported':False,'steps':[]}
phase=0
def checkpoint(text):
    result['steps'].append(text)
    Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('CONTROL',text,flush=True)
def run():
    global phase,primary,secondary
    try:
        if phase==0:
            primary=bpy.context.window_manager.windows[0]
            with bpy.context.temp_override(window=primary):
                bpy.ops.wm.window_new()
                secondary=next(w for w in bpy.context.window_manager.windows if w!=primary)
            checkpoint('secondary window created; primary override exited')
            phase=1
            return .3
        if phase==1:
            with bpy.context.temp_override(window=secondary):bpy.ops.wm.window_close()
            checkpoint('secondary close returned; override exited')
            phase=2
            return .5
        with bpy.context.temp_override(window=primary):
            checkpoint('primary override valid after close')
        result['passed']=True
    except Exception:result['probe_error']=traceback.format_exc()
    checkpoint('finished')
    window=bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=window):bpy.ops.wm.quit_blender()
    return None
bpy.app.timers.register(run,first_interval=.5)
