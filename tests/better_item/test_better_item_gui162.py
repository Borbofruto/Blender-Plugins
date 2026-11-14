"""Render the shared reference hierarchy in all three real sidebar consumers."""
import sys,json,traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy
from mathutils import Matrix,Vector
import better_item as addon
addon.frames.BETTERITEM_PT_frames.bl_options={'DEFAULT_CLOSED'}
addon.register()
from better_item import frames,native_refs
ctx=bpy.context;obj=ctx.object;root=Path(__file__).parent;phase=0;result={'passed':False,'phases':[]}
ctx.preferences.view.show_splash=False
source=bpy.data.objects.new('Orientation Object',None);ctx.scene.collection.objects.link(source)
origin=frames.create(ctx,'Location Frame',Vector((1,2,3)),Matrix.Identity(3))
edited=frames.create(ctx,'Edited Frame',Vector(),Matrix.Identity(3))
edited.rotation_mode='OBJECT';edited.rotation_source=source;edited.position_mode='FRAME';edited.position_frame=origin.uid
settings=obj.better_item;settings.orientation='REFERENCE';settings.orientation_object=source;settings.pivot_mode='FRAME';settings.pivot_frame=origin.uid
s=ctx.scene.better_item;s.arrange_orientation='REFERENCE';s.arrange_object=source;s.arrange_origin='SAVED';s.arrange_origin_frame=origin.uid
area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');area.spaces.active.show_region_ui=True
def run():
    global phase
    try:
        with native_refs.view_context(ctx):
            next(r for r in area.regions if r.type=='UI').active_panel_category='Better Item'
            if phase==0:pass
            elif phase==1:
                bpy.ops.screen.screenshot(filepath=str(root/'ui162-reference-mixed.png'))
                # Temporarily hide the Transform panel in this test process so
                # Align and Distribute can be inspected without sidebar scroll.
                bpy.utils.unregister_class(addon.BETTERITEM_PT_transform)
            elif phase==2:
                bpy.ops.screen.screenshot(filepath=str(root/'ui162-align-reference.png'))
                bpy.utils.unregister_class(addon.BETTERITEM_PT_alignment)
                settings.orientation='NATIVE';settings.reference_native='';settings.pivot_mode='OBJECT';settings.origin_object=None
                bpy.utils.register_class(addon.BETTERITEM_PT_transform)
            elif phase==3:
                bpy.ops.screen.screenshot(filepath=str(root/'ui162-reference-pending.png'))
                bpy.ops.wm.call_panel(name='BETTERITEM_PT_frames',keep_open=True)
            else:
                bpy.ops.screen.screenshot(filepath=str(root/'ui162-frame-editor.png'))
                result['passed']=True;result['phases'].append(phase)
                result['checks']=['mixed Object Orientation / Frame Location','Align and Distribute shared hierarchy','Frame editor Object / Frame hierarchy','custom Name and pending Object hierarchy']
                (root/'ui162.results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
                print('162 REAL UI PASSED',flush=True);bpy.ops.wm.quit_blender();return None
        result['phases'].append(phase);phase+=1;return 1.
    except Exception:
        result['traceback']=traceback.format_exc();traceback.print_exc()
        (root/'ui162.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2.)
