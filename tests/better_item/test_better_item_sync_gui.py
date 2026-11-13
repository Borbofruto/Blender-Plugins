import sys,traceback,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Matrix,Vector
bpy.context.preferences.view.show_splash=False
addon_utils.enable('better_item',default_set=True)
from better_item import frames,native_refs
bpy.ops.object.empty_add();obj=bpy.context.object;obj.name='Live axes source'
obj.rotation_euler=(.1,.2,.3)
bpy.context.view_layer.update()
f=frames.create(bpy.context,'Live Timer',Vector(),Matrix.Identity(3))
f.rotation_mode='OBJECT';f.rotation_source=obj
phase=0
status=False

def check():
    global phase,status
    try:
        if phase==0:
            native_refs.publish(bpy.context,f,select=True)
            obj.rotation_euler.z+=.5
            bpy.context.view_layer.update()
        elif phase==1:
            # No explicit sync calls: these assertions depend on the timer.
            actual=native_refs.named(bpy.context.scene,f.native_name).matrix
            assert max(abs(a-b) for ra,rb in zip(actual,frames.frame_axes(f)) for a,b in zip(ra,rb))<1e-5
            f.rotation_source=None
        elif phase==2:
            assert native_refs.named(bpy.context.scene,f.native_name) is None
            assert f.native_suspended
            f.rotation_source=obj
        elif phase==3:
            assert native_refs.named(bpy.context.scene,f.native_name) is not None
            assert not f.native_suspended
            f.name='Renamed Timer'
        elif phase==4:
            assert f.native_name=='BI: Renamed Timer'
            for area in bpy.context.screen.areas:
                if area.type=='VIEW_3D':
                    with bpy.context.temp_override(area=area,region=next(r for r in area.regions if r.type=='WINDOW')):
                        bpy.ops.wm.call_panel(name='BETTERITEM_PT_transform',keep_open=True)
                    break
        else:
            bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'better141_empty_gui.png'))
            print('REAL UI TIMER PASSED: live orientation, invalid-source removal, recovery and rename; Empty panel captured',flush=True)
            status=True
            bpy.ops.wm.quit_blender()
            return None
        phase+=1
        return .8
    except Exception:
        traceback.print_exc()
        bpy.ops.wm.quit_blender()
        return None
bpy.app.timers.register(check,first_interval=2)
