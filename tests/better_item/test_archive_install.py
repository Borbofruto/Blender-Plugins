"""Install the actual extension archive into an isolated local repository."""
import bpy,json,sys,traceback,zipfile,tomllib
from pathlib import Path
root=Path(__file__).resolve().parent
archive=root.parents[1]/'source/better_item.zip'
repo_dir=root/'profile/installed';repo_dir.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as package:minimum=tuple(map(int,tomllib.loads(package.read('blender_manifest.toml').decode())['blender_version_min'].split('.')))
result={'blender':bpy.app.version_string,'passed':False,'archive_install':False,'declared_minimum':list(minimum)}
try:
 before={repo.module for repo in bpy.context.preferences.extensions.repos}
 status=bpy.ops.preferences.extension_repo_add(name='Better Item Compatibility',type='LOCAL',use_custom_directory=True,custom_directory=str(repo_dir))
 assert status=={'FINISHED'},status
 repo=next(repo for repo in bpy.context.preferences.extensions.repos if repo.module not in before)
 result['repository']=repo.module
 status=bpy.ops.extensions.package_install_files(filepath=str(archive),repo=repo.module,enable_on_install=True,overwrite=True)
 result['operator_result']=sorted(status)
 module='bl_ext.'+repo.module+'.better_item'
 result['module_loaded']=module in sys.modules
 result['archive_install']=status=={'FINISHED'} and result['module_loaded'] and hasattr(bpy.types.Object,'better_item')
 if bpy.app.version>=minimum:
  assert result['archive_install'],result
  obj=bpy.context.object;obj.better_item.transform_space='REFERENCE';obj.better_item.location_x=3
  bpy.context.view_layer.update();assert abs(obj.matrix_world.translation.x-3)<1e-6
  sys.modules[module].unregister();result['passed']=True
 else:
  result['expected_manifest_rejection']=not result['archive_install'];result['passed']=result['expected_manifest_rejection']
except Exception:
 result['exception']=traceback.format_exc()
 if bpy.app.version<minimum and not result['archive_install'] and '.'.join(map(str,minimum)) in result['exception'] and 'blender' in result['exception'].lower():
  result['expected_manifest_rejection']=True;result['passed']=True
(root/'test_archive_install.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
assert result['passed']
