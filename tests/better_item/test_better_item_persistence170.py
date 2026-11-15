"""Run --prepare, --legacy [--source OLD_ADDON_PARENT], then --check in fresh processes."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parent
sys.path.insert(0,sys.argv[sys.argv.index('--source')+1] if '--source' in sys.argv else str(root.parents[1]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector
addon_utils.enable('better_item')
from better_item import frames
ctx=bpy.context
directory=root/'persistence170-fixtures';directory.mkdir(exist_ok=True)
if '--check' not in sys.argv:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    objects=[]
    for i,x in enumerate((0,3,10)):
        bpy.ops.mesh.primitive_cube_add(location=(x,0,0));ctx.object.name='Piece'+str(i);objects.append(ctx.object)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    ctx.view_layer.objects.active=objects[0]
    s=ctx.scene.better_item;s.arrange_reference_mode='INDIVIDUAL';s.axes=(True,False,False)
    if '--legacy' in sys.argv:
        s.arrange_origin='PIVOT';s.reference_pivot='BOUNDING_BOX_CENTER';s.distribution_mode='ORIGINS'
        if 'distribution_schema' in s:del s['distribution_schema']
        bpy.ops.wm.save_as_mainfile(filepath=str(directory/'legacy.blend'))
        print('LEGACY FIXTURE PREPARED')
    else:
        from better_item import distribution as d
        a=frames.create(ctx,'Start Frame',Vector(),Matrix.Identity(3),objects[0],follow_position=True,follow_rotation=False)
        b=frames.create(ctx,'End Frame',Vector(),Matrix.Identity(3),objects[-1],follow_position=True,follow_rotation=False)
        a.rotation_mode='OBJECT';a.rotation_source=None;b.rotation_mode='OBJECT';b.rotation_source=None
        s.distribution_method='ENDPOINT';s.distribution_mode='SURFACE';s.arrange_reference_mode='FRAME';s.arrange_reference_frame=a.uid
        s.distribution_end.mode='FRAME';s.distribution_end.frame=b.uid
        d.apply(ctx,objects)
        expected={obj.name:tuple(obj.location) for obj in objects}
        (directory/'expected.json').write_text(json.dumps(expected),encoding='utf-8')
        bpy.ops.wm.save_as_mainfile(filepath=str(directory/'current.blend'));print('170 FIXTURE PREPARED')
else:
    from better_item import distribution as d,distribution_preview as live
    bpy.ops.wm.open_mainfile(filepath=str(directory/'current.blend'));ctx=bpy.context;s=ctx.scene.better_item
    assert s.distribution_method=='ENDPOINT' and s.distribution_mode=='SURFACE' and s.distribution_end.mode=='FRAME'
    expected=json.loads((directory/'expected.json').read_text());assert {name:tuple(bpy.data.objects[name].location) for name in expected}=={name:tuple(value) for name,value in expected.items()}
    assert not live.active(ctx.scene);d.apply(ctx,list(ctx.selected_objects))
    bpy.ops.wm.open_mainfile(filepath=str(directory/'legacy.blend'));ctx=bpy.context;s=ctx.scene.better_item
    assert s.distribution_legacy_range and s.get('distribution_schema')==1
    assert bpy.ops.better_item.distribute('INVOKE_DEFAULT')=={'FINISHED'}
    assert np.allclose([bpy.data.objects['Piece'+str(i)].location.x for i in range(3)],[0,5,10])
    s.distribution_method='ENDPOINT';assert not s.distribution_legacy_range
    result={'fresh_process_endpoint_sources_and_poses':True,'missing_unused_frame_orientation':True,'saved_legacy_selection_range':True,'explicit_method_exits_legacy':True}
    (root/'test_better_item_persistence170.results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('170 FRESH PROCESS PASSED',json.dumps(result))
