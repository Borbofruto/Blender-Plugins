"""Cold GUI comparison fixture; copied into the unmerged proposal's tests.

BI_UI_UNIT_SCALE selects 1 or .001, recorded in the result. Each run uses a
fresh runner output/profile, so a previous unit configuration cannot leak in.
"""
import hashlib
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import better_item as addon
from better_item import diagnostics
from better_item.math_core import BetterItemError,ReferencePending

addon.register()
ctx=bpy.context;root=Path(__file__).parent
scale=float(os.environ.get('BI_UI_UNIT_SCALE','1'))
expectation=os.environ.get('BI_UI_EXPECTATION','proposal')
assert scale in (1.,.001) and expectation in ('baseline','proposal')
u=ctx.scene.unit_settings;u.system='METRIC';u.scale_length=scale;u.length_unit='MILLIMETERS'
factor=1000*float(u.scale_length)
obj=ctx.object
for v in obj.data.vertices:v.co/=factor
obj.data.update();obj.location=(12.3456789/factor,1e-5/factor,1./factor)
obj.rotation_euler=(math.radians(12.3456789),0,0)
obj.scale=(1.23456789,.98765432,1.11111223)
obj.better_item.transform_space='DEFAULT'
ctx.view_layer.update()
groups={'LOCATION':('location','location_x'),'ROTATION':('rotation_euler','rotation_x'),
        'SCALE':('scale','scale_x'),'DIMENSIONS':('dimensions','dimensions_x')}
native={g:obj.bl_rna.properties[n].precision for g,(n,_) in groups.items()}
actual={g:obj.better_item.bl_rna.properties[a].precision for g,(_,a) in groups.items()}
expected=native if expectation=='proposal' else {g:3 for g in groups}
assert actual==expected,(expectation,native,actual)
before=tuple(v for row in obj.matrix_world for v in row)
draw_errors=[];draw_count=0
error=BetterItemError('[BI-F006] Controlled display-only sync fault')
assert callable(diagnostics.Diagnostic(error).title),'Diagnostic must preserve str.title()'

class TraceLayout:
    def __init__(self,labels):self.labels=labels
    def box(self):return self
    def row(self,**kwargs):return self
    def column(self,**kwargs):return self
    def label(self,*,text,**kwargs):self.labels.append(text)
    def prop(self,*args,**kwargs):pass

def title_of(error,configuration):
    labels=[];diagnostics.draw(TraceLayout(labels),error,ctx.scene.better_item,configuration=configuration)
    return labels[0]

title=title_of(error,True)
assert title==('Orientation sync paused' if expectation=='proposal' else 'Reference unavailable'),title
assert title_of(BetterItemError('[BI-F005] Bad axes'),True)=='Reference unavailable'
assert title_of(ReferencePending('[BI-F002] Choose source'),True)=='Setup needed'
assert title_of(RuntimeError('Controlled failure'),True)=='Operation failed'

class BETTERITEM_PT_precision_test(bpy.types.Panel):
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Precision Test';bl_label='Cold precision comparison'
    def draw(self,context):
        global draw_count
        try:
            layout=self.layout
            layout.label(text='Blender '+bpy.app.version_string+' / '+expectation)
            layout.label(text='Unit Scale: %.9g'%context.scene.unit_settings.scale_length)
            layout.label(text='Native (left) / Add-on (right)')
            for g,(name,field) in groups.items():
                layout.label(text=g.title()+' — precision %d / %d'%(native[g],actual[g]))
                row=layout.split(factor=.5,align=True)
                row.prop(obj,name,index=0,text='')
                row.prop(obj.better_item,field,text='')
            layout.separator()
            diagnostics.draw(layout,error,context.scene.better_item,configuration=True)
            draw_count+=1
        except Exception:
            draw_errors.append(traceback.format_exc());raise

bpy.utils.register_class(BETTERITEM_PT_precision_test)
area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');area.spaces.active.show_region_ui=True
started=time.monotonic();phase=0;original_draw_count=0
original_transform_draw=addon.BETTERITEM_PT_transform.draw
def counted_original(self,context):
    global original_draw_count
    original_transform_draw(self,context);original_draw_count+=1
addon.BETTERITEM_PT_transform.draw=counted_original
result={'passed':False,'blender':bpy.app.version_string,'expectation':expectation,
    'scale_length':float(u.scale_length),'native_precision':native,'addon_precision':actual,
    'sync_title':title,'draw_errors':draw_errors,'cold_process':True,'keyboard_input_tested':False}

def run():
    global phase
    done=False
    try:
        if phase==0:
            next(r for r in area.regions if r.type=='UI').active_panel_category='Precision Test'
            phase=1;area.tag_redraw();return .6
        assert time.monotonic()-started<30,'No complete GUI draw'
        if phase==1 and draw_count<2:area.tag_redraw();return .2
        assert not draw_errors,draw_errors
        assert before==tuple(v for row in obj.matrix_world for v in row),'Draw changed transform'
        for g,(name,field) in groups.items():
            assert float(getattr(obj,name)[0])==float(getattr(obj.better_item,field)),g
        if phase==1:
            screenshot=root/'precision-cold.png';bpy.ops.screen.screenshot(filepath=str(screenshot))
            next(r for r in area.regions if r.type=='UI').active_panel_category='Better Item'
            phase=2;area.tag_redraw();return .6
        if original_draw_count<2:area.tag_redraw();return .2
        bpy.ops.screen.screenshot(filepath=str(root/'original-panel.png'))
        h=hashlib.sha256()
        for p in sorted(Path(addon.__file__).parent.glob('*.py')):h.update(p.name.encode());h.update(b'\0');h.update(p.read_bytes())
        result.update(passed=True,draw_count=draw_count,original_panel_draws=original_draw_count,
            runtime_python_sha256=h.hexdigest(),screenshot='precision-cold.png',original_panel_screenshot='original-panel.png',
            physical_location_mm=float(obj.location.x)*factor,dimensionless_scale=float(obj.scale.x))
        done=True
    except Exception:
        result['traceback']=traceback.format_exc();traceback.print_exc();done=True
    if done:
        Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('COLD UI PRECISION',json.dumps(result),flush=True)
        window=next(iter(bpy.context.window_manager.windows))
        with bpy.context.temp_override(window=window):bpy.ops.wm.quit_blender()
        return None
    return .2
bpy.app.timers.register(run,first_interval=2.)
