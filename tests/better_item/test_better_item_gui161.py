"""Real sidebar: self Normal refusal remains a warning; independent frame and Gimbal edits work."""
import sys,json,traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,numpy as np
import better_item as addon
addon.register()
from better_item import transform_view as view,frames,native_refs
ctx=bpy.context;obj=ctx.object;s=obj.better_item
ctx.preferences.view.show_splash=False
root=Path(__file__).parent;phase=0;result={'passed':False,'phases':[]}
area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');area.spaces.active.show_region_ui=True
s.transform_space='REFERENCE';s.reference_mode='INDIVIDUAL';s.orientation='NORMAL';s.pivot_mode='GLOBAL';s.use_reference_pivot=False
obj.rotation_euler=(.2,.3,.4);ctx.view_layer.update();before=view._snapshot(obj)
def run():
    global phase
    try:
        with native_refs.view_context(ctx):
            next(r for r in area.regions if r.type=='UI').active_panel_category='Better Item'
            if phase==0:
                s.rotation_x=.25
                assert view._snapshot(obj)==before
                diagnostic=addon._field_errors[obj.as_pointer()]
                assert diagnostic.severity=='WARNING' and 'BI-T009' in str(diagnostic)
            elif phase==1:
                bpy.ops.screen.screenshot(filepath=str(root/'ui161-normal-warning.png'))
                f=frames.create(ctx,'Applied Normal',obj.matrix_world.translation,native_refs.orientation(ctx,'NORMAL',obj))
                s.orientation='SAVED';s.orientation_frame=f.uid;s.rotation_x=.25
                assert np.allclose(view.values(ctx,obj,'ROTATION'),(.25,0,0),atol=2e-5)
            elif phase==2:
                bpy.ops.screen.screenshot(filepath=str(root/'ui161-independent-frame.png'))
                obj.rotation_mode='QUATERNION';s.orientation='GIMBAL';s.rotation_x=.4
                assert abs(view.values(ctx,obj,'ROTATION')[0]-.4)<2e-5
            else:
                bpy.ops.screen.screenshot(filepath=str(root/'ui161-quaternion-gimbal.png'))
                result['passed']=True;result['phases'].append(phase)
                result['checks']=['Normal fields allow an edit attempt; moving reference rejects as WARNING and rolls back','Manual frame snapshot accepts the requested relative angle','Quaternion Gimbal fields remain live and editable']
                (root/'ui161.results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
                print('161 REAL UI PASSED',flush=True);bpy.ops.wm.quit_blender();return None
        result['phases'].append(phase);phase+=1;return 1.
    except Exception:
        result['traceback']=traceback.format_exc();traceback.print_exc()
        (root/'ui161.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2.)
