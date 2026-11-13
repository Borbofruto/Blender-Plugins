import sys,traceback,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Matrix,Vector
bpy.context.preferences.view.show_splash=False
addon_utils.enable('better_item',default_set=True)
from better_item import frames,native_refs,references
state={};phase=0

class BETTERITEM_PT_reference_preview142(bpy.types.Panel):
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_label='Better Item References'
    def draw(self,context):
        self.layout.label(text='Transform')
        references.draw(self.layout,context.active_object.better_item)
        self.layout.separator()
        self.layout.label(text='Align and Distribute')
        references.draw(self.layout,context.scene.better_item,True)
bpy.utils.register_class(BETTERITEM_PT_reference_preview142)

def setup(window,name,rotation):
    area=next(a for a in window.screen.areas if a.type=='VIEW_3D')
    region=next(r for r in area.regions if r.type=='WINDOW')
    with bpy.context.temp_override(window=window,screen=window.screen,area=area,region=region):
        ctx=bpy.context
        obj=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(obj)
        obj.rotation_euler=rotation
        ctx.view_layer.objects.active=obj;obj.select_set(True);ctx.view_layer.update()
        frame=frames.create(ctx,name,Vector(),Matrix.Identity(3));frame.rotation_mode='OBJECT';frame.rotation_source=obj
        native_refs.publish(ctx,frame,select=True)
        return dict(window=window,scene=ctx.scene,object=obj,uid=frame.uid,name=frame.native_name,area=area,region=region)

def verify(data):
    frame=frames.find(data['scene'],data['uid'])
    actual=native_refs.named(data['scene'],frame.native_name)
    assert actual is not None
    expected=frames.frame_axes(frame)
    error=max(abs(a-b) for ra,rb in zip(actual.matrix,expected) for a,b in zip(ra,rb))
    assert error<1e-5,(phase,data['scene'].name,frame.native_name,error,tuple(tuple(r) for r in actual.matrix),tuple(tuple(r) for r in expected))

def run():
    global phase
    try:
        if phase==0:
            wa=bpy.context.window
            state['A']=setup(wa,'Window A',(.1,.2,.3))
            bpy.ops.wm.window_new_main()
            wb=next(w for w in bpy.context.window_manager.windows if w!=wa)
            wb.scene=bpy.data.scenes.new('Reference Scene B')
            state['B']=setup(wb,'Window B',(.3,.2,.1))
        elif phase==1:
            for data in state.values():
                verify(data)
                data['object'].rotation_euler.z+=.25
                data['scene'].view_layers[0].update()
        elif phase==2:
            for data in state.values():verify(data)
            d=state['A']
            with bpy.context.temp_override(window=d['window'],screen=d['window'].screen,area=d['area'],region=d['region']):
                d['scene'].transform_orientation_slots[0].type=d['name']
                bpy.ops.transform.delete_orientation()
        elif phase==3:
            d=state['A'];frame=frames.find(d['scene'],d['uid'])
            assert not frame.native_enabled and frame.native_name==''
            assert native_refs.named(d['scene'],d['name']) is None
            verify(state['B'])
            with bpy.context.temp_override(window=d['window'],screen=d['window'].screen,area=d['area'],region=d['region']):
                o=d['object'].better_item;s=d['scene'].better_item
                o.reference_mode=s.arrange_reference_mode='INDIVIDUAL'
                o.reference_orientation=s.reference_orientation='GIMBAL'
                o.reference_location=s.reference_location='PIVOT'
                o.reference_pivot=s.reference_pivot='BOUNDING_BOX_CENTER'
                bpy.ops.wm.call_panel(name='BETTERITEM_PT_reference_preview142',keep_open=True)
        elif phase==4:
            d=state['A']
            with bpy.context.temp_override(window=d['window']):
                bpy.ops.screen.screenshot(filepath=str(Path(__file__).parent/'better142_reference_gui.png'))
            print('REAL MULTIWINDOW GUI PASSED: independent scene exports, timer updates, external deletion and identical reference controls',flush=True)
            bpy.ops.wm.quit_blender()
            return None
        phase+=1
        return 1.
    except Exception:
        traceback.print_exc();bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2)



