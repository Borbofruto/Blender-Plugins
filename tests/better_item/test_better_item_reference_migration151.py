import sys,subprocess,tempfile
from pathlib import Path
import bpy,addon_utils
root=Path(__file__).resolve().parents[2]/"src"
legacy=root
with tempfile.TemporaryDirectory(dir=root) as td:
 td=Path(td);blend=td/'legacy.blend';writer=td/'writer.py'
 writer.write_text(f'''import sys,bpy,addon_utils
sys.path.insert(0,{str(legacy)!r})
addon_utils.enable('better_item')
o=bpy.context.object;o.rotation_euler=(.2,.4,.6)
o.better_item.orientation='LOCAL';o.better_item.pivot_mode='VIEWPORT'
if 'reference_ui_schema' in o.better_item:del o.better_item['reference_ui_schema']
if 'reference_ui_schema' in bpy.context.scene.better_item:del bpy.context.scene.better_item['reference_ui_schema']
bpy.context.scene.tool_settings.transform_pivot_point='MEDIAN_POINT'
bpy.context.scene.better_item.arrange_orientation='VIEWPORT'
bpy.context.scene.better_item.arrange_origin='VIEWPORT'
bpy.context.scene.better_item.reference='KEY'
bpy.context.scene.transform_orientation_slots[0].type='GLOBAL'
bpy.context.preferences.filepaths.file_preview_type='NONE'
bpy.ops.wm.save_as_mainfile(filepath={str(blend)!r})
''',encoding='utf-8')
 r=subprocess.run([bpy.app.binary_path,'--background','--factory-startup','--threads','2','--python-exit-code','1','--python',str(writer)],capture_output=True,text=True)
 assert r.returncode==0,r.stdout+r.stderr
 sys.path.insert(0,str(root));addon_utils.enable('better_item')
 from better_item import frames,orientation
 bpy.ops.wm.open_mainfile(filepath=str(blend))
 obj=bpy.context.object;s=obj.better_item;a=bpy.context.scene.better_item
 assert s.reference_orientation=='SAVED' and s.reference_location=='MEDIAN_POINT'
 assert a.reference_orientation=='SAVED' and a.reference_location=='MEDIAN_POINT'
 assert max(abs(v) for row in (frames.frame_axes(frames.find(bpy.context.scene,s.orientation_frame))-orientation.rotation(obj)) for v in row)<1e-4
 count=len(a.frames);frames.migrate();assert len(a.frames)==count
 bpy.ops.wm.save_as_mainfile(filepath=str(blend))
 bpy.ops.wm.open_mainfile(filepath=str(blend))
 assert len(bpy.context.scene.better_item.frames)==count
 print('REFERENCE UI MIGRATION PASSED: old Local/Viewport captured once, pivot converted, file save/reopen stable')

