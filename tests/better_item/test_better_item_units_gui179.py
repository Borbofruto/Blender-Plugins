"""Render actual Better Item/native LENGTH fields under scene unit variants.

This is GUI rendering/RNA evidence, not an actual typing or mouse test.
"""
import json
import sys
import traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
import bpy
import better_item as addon

addon.frames.BETTERITEM_PT_frames.bl_options={'DEFAULT_CLOSED'}
addon.BETTERITEM_PT_alignment.bl_options={'DEFAULT_CLOSED'}
addon.BETTERITEM_PT_transform.bl_options=set()
draw_original=addon.BETTERITEM_PT_transform.draw
draw_errors=[]

def draw(self,context):
    try:
        unit=context.scene.unit_settings
        self.layout.label(text=unit.system+' / '+unit.length_unit)
        self.layout.label(text='Unit Scale: %.9g'%unit.scale_length)
        self.layout.label(text='RNA values compared; no keyboard simulation')
        box=self.layout.box();box.prop(context.active_object,'location',text='Native Location')
        draw_original(self,context)
    except Exception:
        draw_errors.append(traceback.format_exc());raise

addon.BETTERITEM_PT_transform.draw=draw
addon.register()
ctx=bpy.context;obj=ctx.object
ctx.preferences.view.show_splash=False
obj.better_item.transform_space='DEFAULT'
area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D')
area.spaces.active.show_region_ui=True
configs=[('METRIC',1.,'MILLIMETERS'),('METRIC',.001,'MILLIMETERS'),
         ('METRIC',.01,'CENTIMETERS'),('METRIC',1.,'METERS'),
         ('IMPERIAL',1.,'INCHES'),('NONE',1.,'ADAPTIVE')]
root=Path(__file__).parent;phase=0
result={'passed':False,'configurations':[],'draw_errors':draw_errors,'keyboard_input_tested':False,
        'visual_precision_certified':False,'scope':'GUI rendering and RNA equality; digit rounding is reviewed separately.'}

def run():
    global phase
    done=False
    try:
        with addon.native_refs.view_context(bpy.context):
            ctx=bpy.context
            index=phase//2
            if phase%2==0:
                next(r for r in area.regions if r.type=='UI').active_panel_category='Better Item'
                u=ctx.scene.unit_settings;u.system,u.scale_length,u.length_unit=configs[index]
                factor=1000.*float(u.scale_length)
                obj.location=(12.3456789/factor,1e-5/factor,1./factor)
                obj.scale=(.5/factor,)*3
                ctx.view_layer.update();area.tag_redraw()
            else:
                u=ctx.scene.unit_settings;factor=1000.*float(u.scale_length)
                raw=tuple(obj.location)
                addon_values=tuple(getattr(obj.better_item,'location_'+axis) for axis in 'xyz')
                assert raw==addon_values,(raw,addon_values)
                assert not draw_errors,draw_errors
                filename='units-gui-%02d-%s-%s.png'%(index,u.system,u.length_unit)
                bpy.ops.screen.screenshot(filepath=str(root/filename))
                result['configurations'].append({'system':u.system,'scale_length':u.scale_length,
                    'length_unit':u.length_unit,'raw_blender_units':raw,
                    'raw_mm_by_scene_scale':[v*factor for v in raw],
                    'native_and_addon_rna_equal':True,'screenshot':filename,
                    'addon_property_precision':obj.better_item.bl_rna.properties['location_x'].precision,
                    'native_property_precision':obj.bl_rna.properties['location'].precision,
                    'physical_units_declared':u.system!='NONE'})
                done=index==len(configs)-1
        phase+=1
        if done:result.update(passed=True,blender=bpy.app.version_string)
    except Exception:
        result['traceback']=traceback.format_exc();traceback.print_exc();done=True
    if done:
        addon.BETTERITEM_PT_transform.draw=draw_original
        Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('UNITS GUI',result['passed'],len(result['configurations']),flush=True)
        window=next(iter(bpy.context.window_manager.windows))
        with bpy.context.temp_override(window=window):bpy.ops.wm.quit_blender()
        return None
    return .6

bpy.app.timers.register(run,first_interval=2.)
