import sys,subprocess,tempfile
from pathlib import Path
import bpy,addon_utils
root=Path(__file__).resolve().parents[2]/"src"
archived=root.parent/'archive/better_item-animation-1.5.1/src/better_item'
with tempfile.TemporaryDirectory(dir=root) as td:
 td=Path(td);writer=td/'writer.py';blend=td/'relative.blend'
 # The archived package must be imported under its original module name.
 writer.write_text(f'''import sys,bpy,addon_utils
sys.path.insert(0,{str(archived.parent)!r})
import importlib.util
spec=importlib.util.spec_from_file_location('better_item',{str(archived/'__init__.py')!r},submodule_search_locations=[{str(archived)!r}])
module=importlib.util.module_from_spec(spec);sys.modules['better_item']=module;spec.loader.exec_module(module);module.register()
from better_item import animation
obj=bpy.context.object
animation.start(bpy.context,obj);animation.keyframe(obj,'LOCATION',1)
obj.better_item.animation.location=(2,3,4);animation.keyframe(obj,'LOCATION',10)
obj.better_item.animation.dependencies_owned=True
curve=obj.driver_add('better_item.animation.dependency_stamp');curve.driver.expression='0'
bpy.context.preferences.filepaths.file_preview_type='NONE'
bpy.ops.wm.save_as_mainfile(filepath={str(blend)!r})
''',encoding='utf-8')
 r=subprocess.run([bpy.app.binary_path,'--background','--factory-startup','--threads','2','--python-exit-code','1','--python',str(writer)],capture_output=True,text=True)
 assert r.returncode==0,r.stdout+r.stderr
 sys.path.insert(0,str(root));addon_utils.enable('better_item')
 bpy.ops.wm.open_mainfile(filepath=str(blend));o=bpy.context.object
 retired=o.better_item.get('animation');assert retired and retired.get('enabled')
 assert not retired.get('dependencies_owned')
 assert not any(c.data_path=='better_item.animation.dependency_stamp' for c in o.animation_data.drivers)
 from better_item import _retire_animation_dependencies
 _retire_animation_dependencies()
 assert o.animation_data.action,'Authoring action must not be deleted'
 assert not hasattr(o.better_item,'animation')
 assert not any(getattr(h,'__module__','').startswith('better_item') for h in bpy.app.handlers.frame_change_post)
 print('152 ARCHIVE COMPATIBILITY PASSED: old authoring data retained, owned stamp removed, no relative playback or schema registered')
