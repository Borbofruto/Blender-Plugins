"""Identity boundaries outside the original differential regression."""
import json,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
import better_item as addon
from better_item import engine,arrange
addon.register();ctx=bpy.context
checks=[]
def empty(name,point=(0,0,0)):
    obj=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(obj);obj.location=point;return obj
def reset():
    for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
    for lib in list(bpy.data.libraries):bpy.data.libraries.remove(lib)
    ctx.scene.better_item.frames.clear();arrange.clear_error()
def select(objects,active):
    for obj in ctx.scene.objects:obj.select_set(obj in objects)
    ctx.view_layer.objects.active=active;ctx.view_layer.update()
def refusal(call):
    # Public operators report WARNING domain errors and return CANCELLED.
    return call()=={'CANCELLED'}
with tempfile.TemporaryDirectory(prefix='better_item_identity_frame_') as temporary:
    reset();source=empty('Cube',(0,20,30));lib=Path(temporary)/'library.blend';bpy.data.libraries.write(str(lib),{source});bpy.data.objects.remove(source,do_unlink=True)
    local=empty('Cube',(5,0,0))
    with bpy.data.libraries.load(str(lib),link=True) as (data_from,data_to):data_to.objects=['Cube']
    linked=data_to.objects[0];ctx.scene.collection.objects.link(linked);select([linked],linked)
    # This is exactly the name copied by invoke; it must not select its local homonym.
    status=bpy.ops.better_item.new_frame(target='BOTH',target_name=linked.name,frame_name='Wrong target guard')
    assert status=={'CANCELLED'} and not len(ctx.scene.better_item.frames),'Captured linked name redirected the Frame assignment to a local homonym'
    checks.append('legacy captured name cannot redirect New Frame to a homonym')
    before=tuple(local.location)
    try:engine.apply_world_positions([local,linked],{'Cube':(1,2,3)})
    except addon.BetterItemError as exc:assert '[BI-A004]' in str(exc)
    else:raise AssertionError('ambiguous legacy target map accepted')
    assert tuple(local.location)==before and tuple(linked.location)==(0,20,30)
    checks.append('ambiguous legacy position map refused before writes')
    # Selection membership is object identity, even if another scene has the object.
    second=bpy.data.scenes.new('Other scene');second.collection.objects.link(local)
    ctx.scene.collection.objects.unlink(local)
    assert not engine.contains_object(ctx.scene,local)
    ctx.scene.collection.objects.link(local)
    assert engine.contains_object(ctx.scene,local)
    bpy.data.scenes.remove(second)
    checks.append('membership distinguishes objects across scenes')
    select([local],local);uid=str(local.session_uid);local.name='Renamed'
    other=empty('Cube');select([other],other)
    assert bpy.ops.better_item.new_frame(target='BOTH',target_uid=uid,target_name='Cube',frame_name='Captured identity')=={'FINISHED'}
    frame=ctx.scene.better_item.frames[-1]
    assert local.better_item.reference_frame==frame.uid and other.better_item.reference_mode!='FRAME'
    checks.append('renamed captured object wins over active object and stale name')
    deleted=empty('Removed');deleted_uid=str(deleted.session_uid);bpy.data.objects.remove(deleted,do_unlink=True);replacement=empty('Removed');select([replacement],replacement)
    count=len(ctx.scene.better_item.frames)
    assert refusal(lambda:bpy.ops.better_item.new_frame(target='BOTH',target_uid=deleted_uid,target_name='Removed',frame_name='Stale identity'))
    assert len(ctx.scene.better_item.frames)==count and replacement.better_item.reference_mode!='FRAME'
    checks.append('deleted identity never retargets a same-name replacement')
    for basis in ['ORIGINS','GEOMETRY']:
        select([local,linked],local);local.location=(0,0,0);ctx.view_layer.update()
        s=ctx.scene.better_item;s.arrange_reference_mode='INDIVIDUAL';s.arrange_origin='GLOBAL';s.arrange_orientation='GLOBAL';s.distribution_legacy_range=False
        assert bpy.ops.better_item.distribute(modern=True,distribution_mode=basis,method='OFFSET',spacing=1,axes=(True,False,False))=={'CANCELLED'}
        assert '[BI-D002]' in str(arrange.error(ctx.scene))
    checks.append('homonym ties remain BI-D002, never an RNA comparison TypeError')
    reset()
result=dict(passed=True,blender=bpy.app.version_string,checks=checks,limits='EXEC_DEFAULT captures and identity guards; no physical dialog/keyboard interaction certified.')
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('IDENTITY FRAME 1711',json.dumps(result))
