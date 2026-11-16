import bpy,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import better_item as addon
from better_item import references,frames,native_refs
from better_item.math_core import ReferencePending
addon.register();root=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(root/'retired175.blend'))
ctx=bpy.context;obj=bpy.data.objects['Cube'];f=ctx.scene.better_item.frames[0]
for owner in (obj.better_item,ctx.scene.better_item,f):assert owner.reference_orientation=='NATIVE'
for call in (lambda:references.axes(ctx,obj.better_item,obj),lambda:references.axes(ctx,ctx.scene.better_item,obj,True),lambda:frames.frame_axes(f,ctx)):
 try:call()
 except ReferencePending as exc:assert 'removed' in str(exc)
 else:raise AssertionError('Old reference silently accepted')
assert not hasattr(native_refs,'discover_names')
(root/'test_retired_custom175_persistence.results.json').write_text(json.dumps({'passed':True,'retired_sources_preserved_and_reported':True}),encoding='utf-8');addon.unregister()
