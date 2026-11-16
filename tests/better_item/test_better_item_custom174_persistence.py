import bpy,sys,json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import better_item as addon
from better_item import native_refs,references
addon.register()
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).parent/'custom174.blend'))
s=bpy.context.scene;o=s.objects['Cube'];name=o.better_item.reference_native
assert name.startswith('BI: ')
assert s.better_item.reference_native==name
assert not s.better_item_orientation_names,'Search index was not cleared on load'
previous=s.transform_orientation_slots[0].type
native_refs.refresh_names(s)
assert name in s.better_item_orientation_names
assert s.transform_orientation_slots[0].type==previous
assert native_refs.named(s,name) is not None
(Path(__file__).parent/'test_better_item_custom174_persistence.results.json').write_text(json.dumps({'passed':True,'saved_name':name,'search_index_cleared_on_load':True,'fresh_process_rebuild':True}),encoding='utf-8')
addon.unregister()
print('174 PERSISTENCE PASSED')
