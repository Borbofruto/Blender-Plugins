"""Real-window reentrant closure and migration-fault regression (controlled)."""
import json
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
import bpy
import better_item as addon
from better_item import native_refs as nr,frames,distribution as d,references
from better_item.math_core import BetterItemError

addon.register()
if bpy.app.timers.is_registered(nr.sync):bpy.app.timers.unregister(nr.sync)
result={'passed':False,'purpose':'diagnostic reproduction; failures expected on current stable',
        'blender':bpy.app.version_string,'source':addon.__file__}
original_migrate=frames.migrate
phase=0

class Labels:
    def __init__(self):self.text=[]
    def box(self,**kwargs):return self
    def row(self,**kwargs):return self
    def column(self,**kwargs):return self
    def split(self,**kwargs):return self
    def label(self,**kwargs):self.text.append(kwargs.get('text',''))
    def prop(self,*args,**kwargs):pass
    def operator(self,*args,**kwargs):return SimpleNamespace()

def migration_with_close():
    if not result.get('close_operator_returned'):
        with bpy.context.temp_override(window=secondary):
            bpy.ops.wm.window_close()
    result['close_operator_returned']=True
    result['window_removed']=secondary not in list(bpy.context.window_manager.windows)
    print('CLOSE CHECKPOINT: removed from current windows',result['window_removed'],flush=True)
    raise RuntimeError('Controlled migration fault after closing secondary real window')

def run():
    global phase,primary,secondary
    done=False
    try:
        if phase==0:
            primary=bpy.context.window_manager.windows[0]
            with bpy.context.temp_override(window=primary):
                bpy.ops.object.select_all(action='SELECT')
                bpy.ops.object.delete(use_global=False)
                objects=[]
                for x in (3,8):
                    bpy.ops.mesh.primitive_plane_add(location=(x,0,0))
                    objects.append(bpy.context.object)
                for obj in objects:obj.select_set(True)
                s=bpy.context.scene.better_item
                s.arrange_reference_mode='INDIVIDUAL'
                s.arrange_origin='GLOBAL';s.arrange_orientation='GLOBAL'
                s.distribution_method='OFFSET';s.distribution_mode='VOLUME'
                s.axes=(True,False,False)
                bpy.context.view_layer.update()
                references.axes(bpy.context,s,bpy.context.active_object,True)
                references.origin(bpy.context,s,bpy.context.active_object,True)
                before=[tuple(obj.location) for obj in objects]
                cause=None
                try:d.plan(bpy.context,objects)
                except BetterItemError as exc:cause=str(exc)
                labels=Labels();d.draw(labels,bpy.context)
                result['volume']={'references_valid':True,'cause':cause,'labels':labels.text,
                    'unchanged_targets':before==[tuple(obj.location) for obj in objects],
                    'drawing':'Python label capture, not screenshot or mouse'}
                bpy.ops.wm.window_new()
                secondary=next(w for w in bpy.context.window_manager.windows if w!=primary)
            frames.migrate=migration_with_close
            nr._needs_migration=True
            nr._sync_errors.clear()
            bpy.app.timers.register(nr.sync,first_interval=.1,persistent=True)
            result['timer_registered_before']=bpy.app.timers.is_registered(nr.sync)
            phase=1
            return 1.5
        result['timer_registered_after']=bpy.app.timers.is_registered(nr.sync)
        result['observer_issue']=dict(nr._sync_errors.get((0,''),{}))
        result['syncing_after']=nr._syncing
        result['window_failure_reproduced']=bool(result.get('window_removed') and not result['timer_registered_after'])
        result['volume_guidance_reproduced']=bool('BI-P003' in str(result['volume']['cause']) and
            'Complete references to measure spacing.' in result['volume']['labels'])
        result['passed']=bool(result.get('close_operator_returned') and result.get('window_removed') and result['timer_registered_before'] and result['timer_registered_after'] and not result['syncing_after'] and not result['volume_guidance_reproduced'])
        done=True
    except Exception:
        result['probe_error']=traceback.format_exc();done=True
    if done:
        frames.migrate=original_migrate
        Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('PATCH READINESS DIAGNOSIS',json.dumps(result),flush=True)
        window=next(iter(bpy.context.window_manager.windows))
        with bpy.context.temp_override(window=window):bpy.ops.wm.quit_blender()
        return None
    return .5

bpy.app.timers.register(run,first_interval=1.,persistent=True)
