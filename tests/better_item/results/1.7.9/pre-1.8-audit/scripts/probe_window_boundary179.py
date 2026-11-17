"""Synthetic invalid Window wrapper isolates Python error-handler boundary."""
import json,sys,traceback
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
import bpy
import better_item as addon
from better_item import native_refs as nr,frames
addon.register()
if bpy.app.timers.is_registered(nr.sync):bpy.app.timers.unregister(nr.sync)
result={'passed':False,'blender':bpy.app.version_string,'kind':'synthetic Window.scene ReferenceError plus controlled migration fault; no real window close'}
class InvalidWindow:
    @property
    def scene(self):raise ReferenceError('Controlled invalid Window RNA wrapper')
def broken_migration():raise RuntimeError('Controlled migration failure')
def run():
    original_bpy=nr.bpy;original_migrate=frames.migrate
    try:
        nr.bpy=SimpleNamespace(types=bpy.types,context=SimpleNamespace(window_manager=SimpleNamespace(windows=[InvalidWindow()])))
        frames.migrate=broken_migration
        nr._needs_migration=True;nr._sync_errors.clear()
        try:
            result['return_value']=nr.sync()
        except Exception as exc:
            result['escaped_exception']=type(exc).__name__+': '+str(exc)
            result['traceback']=traceback.format_exc()
        result['syncing_after']=nr._syncing
        result['observer_issue']=dict(nr._sync_errors.get((0,''),{}))
        result['passed']=not bool(result.get('escaped_exception'))
    finally:
        nr.bpy=original_bpy;frames.migrate=original_migrate
    Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('WINDOW BOUNDARY DIAGNOSIS',json.dumps(result),flush=True)
    window=bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=window):bpy.ops.wm.quit_blender()
    return None
bpy.app.timers.register(run,first_interval=.5)
