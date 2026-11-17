import sys,time
sys.dont_write_bytecode=True
sys.path.insert(0,'D:/Codex-BetterItem-179-Consolidated/source')
"""Real timer observes cursor and Empty changes after target deselection."""
import sys,json,traceback,time
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,numpy as np
import better_item as addon
addon.BETTERITEM_PT_transform.bl_options={'DEFAULT_CLOSED'};addon.frames.BETTERITEM_PT_frames.bl_options={'DEFAULT_CLOSED'}
errors=[];draw=addon.BETTERITEM_PT_alignment.draw

def checked(self,ctx):
 try:draw(self,ctx)
 except Exception:errors.append(traceback.format_exc());raise
addon.BETTERITEM_PT_alignment.draw=checked;addon.register()
from better_item import native_refs,distribution_preview as live,placement
ctx=bpy.context;root=Path(__file__).parent;phase=0;phase_started=time.monotonic();result={'passed':False,'phases':[],'waits':{}}
ctx.preferences.view.show_splash=False;ctx.preferences.edit.use_global_undo=True
key=ctx.object;key.name='Captured Start';objects=[key]
for i,x in enumerate((5,12,20)):
 bpy.ops.mesh.primitive_cube_add(location=(x,1+i,0));ctx.object.name='Piece '+str(i+1);objects.append(ctx.object)
source=bpy.data.objects.new('Editable End',None);ctx.scene.collection.objects.link(source);source.location=(12,8,0)

def select(items,active):
 bpy.ops.object.select_all(action='DESELECT')
 for o in items:o.select_set(True)
 ctx.view_layer.objects.active=active;ctx.view_layer.update()
select(objects,key)
s=ctx.scene.better_item;s.arrange_origin='PIVOT';s.reference_pivot='ACTIVE_ELEMENT';s.arrange_orientation='GLOBAL';s.distribution_method='ENDPOINT';s.distribution_end.mode='CURSOR'
area=next(a for a in ctx.screen.areas if a.type=='VIEW_3D');area.spaces.active.show_region_ui=True;area.spaces.active.region_3d.view_distance=30

def line(end):
 for i,o in enumerate(objects):assert np.allclose(o.matrix_world.translation,np.array(end)*i/3,atol=3e-5),(o.name,tuple(o.location),end)

def run():
 global phase,phase_started,ctx,s,key,objects,source
 try:
  with native_refs.view_context(bpy.context):
   ctx=bpy.context;s=ctx.scene.better_item
   next(r for r in area.regions if r.type=='UI').active_panel_category='Better Item'
   # Test and Live timers can both be overdue after a blocked UI tick. The
   # test callback was registered first and may run before Live in that tick.
   # Wait for the observable result, bounded, without invoking poll ourselves.
   expected={1:(15,6,0),2:(12,8,0),3:(18,-3,6)}.get(phase)
   ready=all(np.allclose(o.matrix_world.translation,np.array(expected)*i/3,atol=3e-5) for i,o in enumerate(objects)) if expected else True
   if phase==4:ready=all(o.location.x<0 for o in objects[1:])
   if not ready and time.monotonic()-phase_started<10.:
    error=addon.arrange.error(ctx.scene)
    assert not error,str(error)
    result['waits'][str(phase)]=result['waits'].get(str(phase),0)+1
    return .1
   if phase==0:
    initial=[tuple(o.location) for o in objects];s.distribution_live=True;assert [tuple(o.location) for o in objects]==initial
    ctx.scene.cursor.location=(15,6,0)
    def block_once():
     time.sleep(1.2)
     return None
    bpy.app.timers.register(block_once,first_interval=.05)
   elif phase==1:
    line((15,6,0));assert not addon.arrange.error(ctx.scene),str(addon.arrange.error(ctx.scene))
    bpy.ops.screen.screenshot(filepath=str(root/'ui173-cursor-live.png'))
    select([source],source);s.distribution_end.mode='OBJECT';s.distribution_end.object=source
   elif phase==2:
    line((12,8,0));assert bpy.ops.transform.translate(value=(6,-11,6),orient_type='GLOBAL')=={'FINISHED'};ctx.view_layer.update()
   elif phase==3:
    line((18,-3,6));assert ctx.active_object==source and not key.select_get()
    bpy.ops.screen.screenshot(filepath=str(root/'ui173-object-live.png'))
    s.distribution_method='OFFSET';s.distribution_mode='GEOMETRY';s.spacing=-.5;s.spacing=0
   elif phase==4:
    assert all(o.location.x<0 for o in objects[1:])
    s.distribution_method='ENDPOINT';assert s.distribution_mode=='ORIGINS'
    assert 'GEOMETRY' not in [i[0] for i in placement.items(s,ctx)]
    line((18,-3,6));s.distribution_live=False
    result['before']={o.name:tuple(o.location) for o in objects};source.location=(21,9,0);ctx.view_layer.update()
   elif phase==5:
    assert result['before']=={o.name:tuple(o.location) for o in objects}
    select(objects,key);bpy.ops.ed.undo_push(message='Before one-shot distribution')
    assert bpy.ops.better_item.distribute('INVOKE_DEFAULT',True)=={'FINISHED'}
    line((21,9,0));result['after']={o.name:tuple(o.location) for o in objects}
    op=ctx.window_manager.operators[-1];assert op.bl_idname=='BETTER_ITEM_OT_distribute'
    op.method='OFFSET';op.distribution_mode='GEOMETRY';op.method='ENDPOINT';assert op.distribution_mode=='ORIGINS';op.method='OFFSET';assert op.distribution_mode=='GEOMETRY';op.method='ENDPOINT'
    bpy.ops.ed.undo();assert result['before']=={name:tuple(bpy.data.objects[name].location) for name in result['before']}
    bpy.ops.ed.redo();assert result['after']=={name:tuple(bpy.data.objects[name].location) for name in result['after']}
    assert not live.active(bpy.context.scene) and not bpy.app.timers.is_registered(live.poll)
    assert not errors,errors
    result.update(passed=True,draw_errors=errors,checks=['actual timer follows cursor','actual timer follows Empty with targets deselected','captured Active identity stable','zero retains negative Offset direction','Endpoint restores point basis','disable stops following','native invoke and F9 placements','native Undo/Redo'])
    (root/'test_better_item_gui173.results.json').write_text(json.dumps(result,indent=2));print('173 REAL UI PASSED',flush=True);bpy.ops.wm.quit_blender();return None
  result['phases'].append(phase);phase+=1;phase_started=time.monotonic();return .8
 except Exception:
  result['traceback']=traceback.format_exc();traceback.print_exc();(root/'test_better_item_gui173.results.json').write_text(json.dumps(result,indent=2));bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(run,first_interval=2.)
