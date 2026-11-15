"""Native undo and preview lifecycle, selection guards and source captures."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector
addon_utils.enable('better_item')
from better_item import distribution as d,distribution_preview as live,arrange,frames,placement
ctx=bpy.context;s=ctx.scene.better_item
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
objects=[]
for i,x in enumerate((3,8,19)):
    bpy.ops.mesh.primitive_cube_add(location=(x,0,0));ctx.object.name='Preview'+str(i);objects.append(ctx.object)
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
ctx.view_layer.objects.active=objects[0];ctx.view_layer.update()
s.arrange_origin='GLOBAL';s.distribution_method='OFFSET';s.axes=(True,False,False)
before={o.name:tuple(o.location) for o in objects}
ctx.preferences.edit.use_global_undo=True;bpy.ops.ed.undo_push(message='Before Live Preview')
assert bpy.ops.better_item.distribution_preview('EXEC_DEFAULT',True,action='BEGIN')=={'FINISHED'}
s.spacing=2;s.spacing=4
assert [o.location.x for o in objects]==[4,8,12]
assert bpy.ops.better_item.distribution_preview('EXEC_DEFAULT',True,action='CONFIRM')=={'FINISHED'}
after={o.name:tuple(o.location) for o in objects}
bpy.ops.ed.undo()
actual={name:tuple(bpy.data.objects[name].location) for name in before}
assert actual==before,('Undo did not restore initial positions',actual,before)
bpy.ops.ed.redo();assert {name:tuple(bpy.data.objects[name].location) for name in after}==after
ctx=bpy.context;s=ctx.scene.better_item;objects=[bpy.data.objects[name] for name in before]
# No normalization occurs on Begin. Invalid edits retain the last valid preview.
assert bpy.ops.better_item.distribution_preview(action='BEGIN')=={'FINISHED'}
s.spacing=3;latest={o:tuple(o.location) for o in objects};s.spacing=0
assert latest=={o:tuple(o.location) for o in objects} and 'BI-D001' in arrange.error(ctx.scene)
objects[-1].select_set(False);s.spacing=5
assert [o.location.x for o in objects]==[5,10,15];assert not arrange.error(ctx.scene)
assert bpy.ops.better_item.distribution_preview(action='CANCEL')=={'FINISHED'}
assert {o.name:tuple(o.location) for o in objects}==after
# Selection captures in Transform produce a stable saved Frame, not a moving pivot.
for o in objects:o.select_set(True)
ctx.view_layer.objects.active=objects[0]
settings=objects[0].better_item;settings.reference_location='MEDIAN_POINT';assert settings.pivot_mode=='FRAME'
f=frames.find(ctx.scene,settings.pivot_frame);position=tuple(f.position)
objects[0].location.x+=10;ctx.view_layer.update();assert tuple(frames.frame_origin(f))==position
# Empty anchors are valid; only actual pieces need geometry for geometric placement.
key=bpy.data.objects.new('Empty anchor',None);ctx.scene.collection.objects.link(key)
for o in objects:o.parent=None;o.location=(10+objects.index(o)*5,0,0)
bpy.ops.object.select_all(action='DESELECT')
for o in [key,*objects]:o.select_set(True)
ctx.view_layer.objects.active=key;s.arrange_origin='OBJECT';s.arrange_origin_object=key
empty_cases=0
for basis in ('ORIGINS','BOUNDS_CENTER','SURFACE','VOLUME','GEOMETRY'):
    for i,o in enumerate(objects):o.location=(10+i*5,0,0)
    s.distribution_method='OFFSET';s.distribution_mode=basis;s.spacing=.5
    d.apply(ctx,[key,*objects]);assert tuple(key.location)==(0,0,0)
    assert d.inspect_spacing(ctx,[key,*objects])[0]=='UNIFORM'
    for i,o in enumerate(objects):o.location=(10+i*5,0,0)
    if basis=='GEOMETRY':continue
    s.distribution_method='ENDPOINT';s.distribution_mode=basis;s.distribution_end.mode='MANUAL';s.distribution_end.position=(20,0,0)
    d.apply(ctx,[key,*objects]);assert tuple(key.location)==(0,0,0);empty_cases+=1
result={'native_preview_undo_redo':True,'invalid_preview_retains_last_valid':True,'selection_changes_keep_capture':True,'cancel_restores_session_start':True,'transform_selection_capture':True,'empty_anchor_bases':empty_cases}
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('170 PREVIEW PASSED',json.dumps(result))
