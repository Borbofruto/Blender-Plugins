"""Prepare a 1.7.2 Geometry Endpoint file, then check it in a fresh 1.7.3 process."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parent
source=sys.argv[sys.argv.index('--source')+1] if '--source' in sys.argv else str(root.parents[1]/"src")
sys.path.insert(0,source)
import bpy,addon_utils
addon_utils.enable('better_item')
path=root/'migration173.legacy.blend'
if '--prepare' in sys.argv:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for i in range(5):bpy.ops.mesh.primitive_cube_add(location=(3+3*i,0,0))
 bpy.ops.object.select_all(action='SELECT');s=bpy.context.scene.better_item;s.distribution_method='ENDPOINT';s.distribution_mode='GEOMETRY';s.distribution_end.position=(.5,0,0);s.arrange_origin='GLOBAL';s.arrange_orientation='GLOBAL'
 bpy.ops.wm.save_as_mainfile(filepath=str(path));print('173 LEGACY PREPARED')
else:
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene.better_item
 assert s.distribution_mode=='ORIGINS' and s.get('placement_migration_notice')
 from better_item import distribution
 objs=list(bpy.context.selected_objects);distribution.apply(bpy.context,objs)
 assert sorted(round(o.location.x,4) for o in objs)==[0,.125,.25,.375,.5]
 s.distribution_method='OFFSET';assert s.distribution_mode=='GEOMETRY';s.distribution_method='ENDPOINT';s.distribution_mode='SURFACE'
 assert not s.get('placement_migration_notice')
 result={'passed':True,'fresh_process_172_migration':True,'notice_and_offset_choice_preserved':True,'short_point_segment_without_resize':True}
 Path(__file__).with_suffix('.results.json').write_text(json.dumps(result,indent=2));print('173 MIGRATION PASSED',result)
