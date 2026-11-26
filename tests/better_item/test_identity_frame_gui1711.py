"""Auxiliary real-dialog identity/redo check; requires --enable-event-simulate.

Run with -- --source PREPARED/source --output ISOLATED_OUTPUT. This uses native
simulated events, not physical typing or mouse interaction.
"""
import argparse,json,sys,time,traceback
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:]
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(args)
sys.dont_write_bytecode=True;sys.path.insert(0,str(a.source))
import bpy
import better_item as addon
a.output.mkdir(parents=True,exist_ok=True)
draws=[];original_draw=addon.frames.BETTERITEM_OT_new_frame.draw
def observed(self,context):
    original_draw(self,context);draws.append(dict(uid=self.target_uid,name=self.frame_name))
addon.frames.BETTERITEM_OT_new_frame.draw=observed;addon.register()
bpy.context.preferences.view.show_splash=False;bpy.context.preferences.edit.use_global_undo=True
phase=0;started=time.monotonic();uid=None;other_uid=None;last_draws=0;before=None
result=dict(passed=False,blender=bpy.app.version_string,source=addon.__file__,checks=[],events='native simulated Enter/Esc/F9; no physical interaction')
def object_by_uid(value):return next((o for o in bpy.context.scene.objects if str(o.session_uid)==value),None)
def view():
    window=bpy.context.window_manager.windows[0];area=next(a for a in window.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
    return bpy.context.temp_override(window=window,area=area,region=region)
def key(name):
    w=bpy.context.window_manager.windows[0]
    w.event_simulate(type=name,value='PRESS',x=w.width//2,y=w.height//2);w.event_simulate(type=name,value='RELEASE',x=w.width//2,y=w.height//2)
def select(obj):
    for o in bpy.context.scene.objects:o.select_set(o==obj)
    bpy.context.view_layer.objects.active=obj
def assigned():
    obj=object_by_uid(uid);s=bpy.context.scene.better_item
    assert obj is not None and len(s.frames)==1
    assert obj.better_item.reference_frame==s.frames[0].uid
    other=object_by_uid(other_uid);assert other is not None and other.better_item.reference_mode!='FRAME'
def save_and_exit():
    (a.output/'test_identity_frame_gui1711.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    with view():bpy.ops.wm.quit_blender()
def tick():
    global phase,uid,other_uid,last_draws,before
    try:
        assert time.monotonic()-started<70,'dialog phase timeout '+str(phase)
        with view():
            if phase==0:
                key('ESC');phase=1;return .8
            if phase==1:
                for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
                obj=bpy.data.objects.new('Captured',None);bpy.context.scene.collection.objects.link(obj);uid=str(obj.session_uid)
                other=bpy.data.objects.new('Other',None);bpy.context.scene.collection.objects.link(other);other_uid=str(other.session_uid);select(obj)
                bpy.ops.ed.undo_push(message='Identity Frame baseline')
                last_draws=len(draws)
                assert bpy.ops.better_item.new_frame('INVOKE_DEFAULT',True,target='BOTH',frame_name='Identity Frame')=={'RUNNING_MODAL'}
                phase=2;return .8
            if phase==2:
                if len(draws)<=last_draws:return .2
                assert draws[-1]['uid']==uid
                object_by_uid(uid).name='Renamed while dialog open';select(object_by_uid(other_uid))
                key('RET');phase=3;return .8
            if phase==3:
                assigned();result['checks'].append('real invoke captures object despite rename and active switch')
                last_draws=len(draws);key('F9');phase=4;return .8
            if phase==4:
                if len(draws)<=last_draws:return .2
                assert draws[-1]['uid']==uid
                key('ESC');phase=5;return .6
            if phase==5:
                assigned();assert bpy.ops.ed.undo_redo('EXEC_DEFAULT',True)=={'FINISHED'};phase=6;return .6
            if phase==6:
                assigned();result['checks'].append('F9 draw and native reexecute retain captured identity')
                bpy.ops.ed.undo();phase=7;return .6
            if phase==7:
                assert len(bpy.context.scene.better_item.frames)==0
                bpy.ops.ed.redo();phase=8;return .6
            if phase==8:
                assigned();result['checks'].append('one Undo removes Frame assignment and Redo restores it')
                select(object_by_uid(other_uid));before=(len(bpy.context.scene.better_item.frames),object_by_uid(other_uid).better_item.reference_mode)
                last_draws=len(draws);assert bpy.ops.better_item.new_frame('INVOKE_DEFAULT',True,target='BOTH',frame_name='Cancelled')=={'RUNNING_MODAL'}
                phase=9;return .6
            if phase==9:
                if len(draws)<=last_draws:return .2
                key('ESC');phase=10;return .6
            if phase==10:
                assert before==(len(bpy.context.scene.better_item.frames),object_by_uid(other_uid).better_item.reference_mode)
                result['checks'].append('Esc in real dialog leaves Frame list and target reference unchanged')
                result['passed']=True;save_and_exit();return None
    except Exception:
        result['error']=traceback.format_exc();print(result['error'],flush=True);save_and_exit();return None
    return .2
bpy.app.timers.register(tick,first_interval=.8)
