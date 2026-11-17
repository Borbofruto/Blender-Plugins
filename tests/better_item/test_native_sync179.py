"""Real timer survives faults, isolates Frames and respects native deletion."""
import sys,json,traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
import bpy
import better_item as addon
from mathutils import Vector,Matrix
from better_item import native_refs as nr,frames

addon.register()
if bpy.app.timers.is_registered(nr.sync):bpy.app.timers.unregister(nr.sync)
nr.sync()
root=Path(__file__).resolve().parent
result={'passed':False,'checks':[],'draw_errors':[]}
phase=0;calls=0;fault='once'
original_named=nr.named
original_draw=frames.BETTERITEM_PT_frames.draw
def checked_draw(self,context):
    try:original_draw(self,context)
    except Exception:
        result['draw_errors'].append(traceback.format_exc());raise
frames.BETTERITEM_PT_frames.draw=checked_draw
area=next(area for area in bpy.context.screen.areas if area.type=='VIEW_3D')
area.spaces.active.show_region_ui=True

def create(name):
    obj=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(obj)
    frame=frames.create(bpy.context,name,Vector(),Matrix.Identity(3))
    frame.rotation_mode='OBJECT';frame.rotation_source=obj
    nr.publish(bpy.context,frame)
    return obj,frame

def matches(frame):
    actual=original_named(bpy.context.scene,frame.native_name).matrix.copy()
    expected=frames.frame_axes(frame,bpy.context)
    return max(abs(actual[i][j]-expected[i][j]) for i in range(3) for j in range(3))<2e-6

def faulty_named(scene,name):
    global calls
    if name==bad.native_name:
        calls+=1
        if fault=='persistent' or fault=='once' and calls==1:
            raise RuntimeError('Injected native read failure')
    return original_named(scene,name)

def run():
    global phase,source,bad,other,good,fault,calls,ctx
    done=False;delay=.3
    try:
        with nr.view_context(bpy.context):
            ctx=bpy.context
            if phase==0:
                source,bad=create('Faulted Frame')
                other,good=create('Healthy Frame')
                ctx.scene.better_item.active_frame=0
                ctx.area.spaces.active.show_region_ui=True
                next(r for r in ctx.area.regions if r.type=='UI').active_panel_category='Better Item'
                source.rotation_euler.z=.5;other.rotation_euler.z=.7;ctx.view_layer.update()
                nr.named=faulty_named
                bpy.app.timers.register(nr.sync,first_interval=.05,persistent=True)
            elif phase==1:
                assert bpy.app.timers.is_registered(nr.sync) and not nr._syncing
                assert calls==1 and nr.sync_error(ctx.scene,bad) is not None
                assert 'BI-F006' in str(nr.sync_error(ctx.scene,bad))
                assert bad.native_enabled and not bad.native_suspended
                assert matches(good) and not matches(bad)
                bpy.ops.screen.screenshot(filepath=str(root/'native-sync179-paused.png'))
                result['checks'].append('one Frame pauses visibly while healthy export updates')
                delay=1.2
            elif phase==2:
                assert nr.sync_error(ctx.scene,bad) is None and matches(bad)
                result['checks'].append('real timer retries one-shot read failure and recovers')
                fault='persistent';calls=0
                source.rotation_euler.z=.9;other.rotation_euler.z=1.1;ctx.view_layer.update()
            elif phase==3:
                assert calls==1 and nr.sync_error(ctx.scene,bad) is not None
                for _ in range(20):nr.sync()
                assert calls==1,'retry ignored backoff'
                assert matches(good)
                result['checks'].append('persistent fault keeps timer and other Frames alive; backoff prevents busy retry')
                delay=1.2
            elif phase==4:
                assert calls==2
                issue=nr._sync_errors[(ctx.scene.as_pointer(),bad.uid)]
                assert issue['attempts']==2 and issue['retry_at']>nr.time.monotonic()
                fault=None
                delay=2.2
            elif phase==5:
                assert matches(bad) and nr.sync_error(ctx.scene,bad) is None
                result['checks'].append('persistent failure recovers without resetting export intent')
                fault='once';calls=0;nr.sync()
                assert nr.sync_error(ctx.scene,bad) is not None
                slot=ctx.scene.transform_orientation_slots[0]
                slot.type=bad.native_name
                bpy.ops.transform.delete_orientation()
                slot.type='GLOBAL'
                delay=1.2
            elif phase==6:
                assert not bad.native_enabled and bad.native_name==''
                assert nr.sync_error(ctx.scene,bad) is None
                result['checks'].append('external deletion during backoff is respected; export is not recreated')
                nr.named=original_named
                source2,domain=create('Source validity')
                domain.rotation_source=None;nr.sync()
                assert domain.native_suspended and domain.native_enabled
                assert nr.sync_error(ctx.scene,domain) is None
                domain.rotation_source=source2;nr.sync()
                assert matches(domain) and not domain.native_suspended
                result['checks'].append('invalid source retains existing remove/suspend/recover policy')
                first_scene=ctx.scene
                second=bpy.data.scenes.new('Native sync context')
                ctx.window.scene=second
                source_b,frame_b=create('Second Scene Frame')
                source_b.rotation_euler.x=.4;ctx.view_layer.update();nr.sync()
                assert matches(frame_b) and frame_b.id_data==second
                ctx.window.scene=first_scene
                nr.sync();assert matches(good)
                second_pointer=second.as_pointer()
                nr._sync_failed((second_pointer,''),RuntimeError('Injected health for removed scene'))
                bpy.data.scenes.remove(second)
                nr.sync()
                assert all(key[0]!=second_pointer for key in nr._sync_errors)
                result['checks'].append('scene switching uses current context; removed-scene health is pruned')
                original_migrate=frames.migrate
                def broken_migration():raise RuntimeError('Injected migration failure')
                frames.migrate=broken_migration;nr._needs_migration=True
                try:nr.sync()
                finally:frames.migrate=original_migrate
                assert nr.sync_error(ctx.scene) is not None and bpy.app.timers.is_registered(nr.sync)
                nr._sync_errors[(0,'')]['retry_at']=0
                nr.sync()
                assert nr.sync_error(ctx.scene) is None and not nr._needs_migration
                result['checks'].append('observer-level migration fault is visible and recoverable')
                ctx.preferences.edit.use_global_undo=True
                bpy.ops.ed.undo_push(message='Before native sync health')
                nr._sync_failed((ctx.scene.as_pointer(),''),RuntimeError('Injected health for Undo'))
                bpy.ops.ed.undo()
                assert not nr._sync_errors
                result['checks'].append('Undo clears transient sync health')
                path=root/'native-sync179.blend'
                bpy.ops.wm.save_as_mainfile(filepath=str(path))
                nr._sync_failed((0,''),RuntimeError('Injected health for load'))
                bpy.ops.wm.open_mainfile(filepath=str(path))
                assert not nr._sync_errors and bpy.app.timers.is_registered(nr.sync)
                result['checks'].append('load clears health and retains persistent observer')
                assert not result['draw_errors']
                addon.unregister()
                assert not nr._sync_errors and not bpy.app.timers.is_registered(nr.sync)
                result['checks'].append('unregister removes observer and health')
                result['passed']=True;done=True
        phase+=1
    except Exception:
        result['traceback']=traceback.format_exc();traceback.print_exc();done=True
    if done:
        nr.named=original_named
        frames.BETTERITEM_PT_frames.draw=original_draw
        result['blender']=bpy.app.version_string
        Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('NATIVE SYNC 179',json.dumps(result),flush=True)
        window=next(iter(bpy.context.window_manager.windows))
        with bpy.context.temp_override(window=window):bpy.ops.wm.quit_blender()
        return None
    return delay
bpy.app.timers.register(run,first_interval=1.,persistent=True)
