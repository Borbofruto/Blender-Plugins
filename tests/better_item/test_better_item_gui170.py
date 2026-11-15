"""Real sidebar, actual invoke/undo and live point/interval adjustments."""
import sys,json,traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,numpy as np
from mathutils import Matrix,Vector
import better_item as addon
addon.BETTERITEM_PT_transform.bl_options={'DEFAULT_CLOSED'};addon.frames.BETTERITEM_PT_frames.bl_options={'DEFAULT_CLOSED'}
_draw_errors=[]
_original_draw=addon.BETTERITEM_PT_alignment.draw
def checked_draw(self,context):
    try:_original_draw(self,context)
    except Exception:
        _draw_errors.append(traceback.format_exc());raise
addon.BETTERITEM_PT_alignment.draw=checked_draw
addon.register()
from better_item import distribution as d,distribution_preview as live,native_refs,frames
ctx=bpy.context;root=Path(__file__).parent;phase=0;result={'passed':False,'phases':[]}
ctx.preferences.view.show_splash=False;ctx.preferences.edit.use_global_undo=True
key=ctx.object;key.name='Start Anchor';objects=[key]
for i,x in enumerate((5,12,20)):
    bpy.ops.mesh.primitive_cube_add(location=(x,1+i,0));o=ctx.object;o.name='Part '+str(i+1);o.scale.x=1+i*.25;objects.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
ctx.view_layer.objects.active=key
s=ctx.scene.better_item;s.arrange_origin='PIVOT';s.reference_pivot='ACTIVE_ELEMENT';s.arrange_orientation='GLOBAL'
s.distribution_method='ENDPOINT';s.distribution_end.mode='CURSOR';ctx.scene.cursor.location=(12,6,3)
area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');area.spaces.active.show_region_ui=True;area.spaces.active.region_3d.view_distance=24
def shot(name):bpy.ops.screen.screenshot(filepath=str(root/name))
def run():
    global phase,ctx,s,key,objects
    try:
        with native_refs.view_context(bpy.context):
            ctx=bpy.context;s=ctx.scene.better_item
            next(r for r in area.regions if r.type=='UI').active_panel_category='Better Item'
            if phase==0:
                assert bpy.ops.better_item.distribute('INVOKE_DEFAULT',True)=={'FINISHED'}
                for i,o in enumerate(objects):assert np.allclose(o.matrix_world.translation,np.array((12,6,3))*i/3,atol=2e-5)
            elif phase==1:
                shot('ui170-endpoint.png');s.distribution_method='OFFSET';s.distribution_mode='GEOMETRY'
                s.axes=(True,False,False)
                for i,o in enumerate(objects[1:]):o.location=(5+7*i,0,0)
                ctx.view_layer.update();assert d.inspect_spacing(ctx,objects)[0]=='MIXED'
            elif phase==2:
                shot('ui170-mixed.png')
                initial={o.name:tuple(o.location) for o in objects}
                result['initial']=initial
                assert bpy.ops.better_item.distribution_preview('INVOKE_DEFAULT',True,action='BEGIN')=={'FINISHED'}
                assert initial=={o.name:tuple(o.location) for o in objects}
                s.spacing=.5;assert d.inspect_spacing(ctx,objects)[0]=='UNIFORM'
            elif phase==3:
                shot('ui170-live.png');s.spacing=1.25
                status,value=d.inspect_spacing(ctx,objects);assert status=='UNIFORM' and abs(value-1.25)<1e-5
                assert bpy.ops.better_item.distribution_preview('INVOKE_DEFAULT',True,action='CONFIRM')=={'FINISHED'}
                result['confirmed']={o.name:tuple(o.location) for o in objects}
                bpy.ops.ed.undo()
                assert {name:tuple(bpy.data.objects[name].location) for name in result['initial']}==result['initial']
                bpy.ops.ed.redo();assert {name:tuple(bpy.data.objects[name].location) for name in result['confirmed']}==result['confirmed']
                objects=[bpy.data.objects[name] for name in result['initial']];key=objects[0]
            elif phase==4:
                s=bpy.context.scene.better_item
                s.distribution_method='ENDPOINT';s.distribution_start_override=True;s.distribution_start.mode='OBJECT';s.distribution_start.object=key
                s.distribution_end.mode='MANUAL';s.distribution_end.position=(20,4,2);s.distribution_mode='BOUNDS_CENTER'
                assert bpy.ops.better_item.distribution_preview('INVOKE_DEFAULT',True,action='BEGIN')=={'FINISHED'}
                s.distribution_end.position=(18,8,4)
                assert not addon.arrange.error(ctx.scene),str(addon.arrange.error(ctx.scene))
            elif phase==5:
                shot('ui170-endpoint-live.png')
                assert bpy.ops.better_item.distribution_preview('INVOKE_DEFAULT',True,action='CANCEL')=={'FINISHED'}
                assert {name:tuple(bpy.data.objects[name].location) for name in result['confirmed']}==result['confirmed']
                assert not _draw_errors,_draw_errors
                result['passed']=True;result['phases'].append(phase);result['draw_errors']=_draw_errors
                result['checks']=['native Endpoint invoke using active object and cursor','Mixed is not a fabricated zero','Live Begin leaves selection unchanged','live Geometry Bounds updates','native Confirm Undo Redo','live Endpoint source coordinates','Cancel restores initial selection']
                (root/'ui170.results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
                print('170 REAL UI PASSED',flush=True);bpy.ops.wm.quit_blender();return None
        result['phases'].append(phase);phase+=1;return 1.
    except Exception:
        result['traceback']=traceback.format_exc();traceback.print_exc();(root/'ui170.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2.)
