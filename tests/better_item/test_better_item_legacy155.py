import sys,subprocess,tempfile,ast
from pathlib import Path
from types import SimpleNamespace
import bpy,addon_utils
root=Path(__file__).resolve().parents[2]/"src"
archived=root.parent/'archive/better_item-animation-1.5.1/src/better_item'
with tempfile.TemporaryDirectory(dir=root) as td:
 td=Path(td);writer=td/'writer.py';blend=td/'legacy-authoring.blend'
 writer.write_text(f'''import sys,bpy,importlib.util
spec=importlib.util.spec_from_file_location('better_item',{str(archived/'__init__.py')!r},submodule_search_locations=[{str(archived)!r}])
module=importlib.util.module_from_spec(spec);sys.modules['better_item']=module;spec.loader.exec_module(module);module.register()
from better_item import animation
obj=bpy.context.object
animation.start(bpy.context,obj);animation.keyframe(obj,'LOCATION',1)
obj.better_item.animation.location=(2,3,4);animation.keyframe(obj,'LOCATION',10)
obj.better_item.animation.dependencies_owned=True
curve=obj.driver_add('better_item.animation.dependency_stamp');curve.driver.expression='0'
obj['saved_location']=tuple(obj.location)
bpy.context.preferences.filepaths.file_preview_type='NONE'
bpy.ops.wm.save_as_mainfile(filepath={str(blend)!r})
''',encoding='utf-8')
 r=subprocess.run([bpy.app.binary_path,'--background','--factory-startup','--threads','2','--python-exit-code','1','--python',str(writer)],capture_output=True,text=True)
 assert r.returncode==0,r.stdout+r.stderr
 sys.path.insert(0,str(root));addon_utils.enable('better_item')
 import better_item as addon
 from better_item import native_refs,transform_view
 bpy.ops.wm.open_mainfile(filepath=str(blend));o=bpy.context.object
 retired=o.better_item.get('animation');assert retired and retired.get('enabled') and retired.get('dependencies_owned')
 curve=next(c for c in o.animation_data.drivers if c.data_path=='better_item.animation.dependency_stamp')
 action=o.animation_data.action;curve_pointer=curve.as_pointer()
 before=(retired.get('binding_uid'),tuple(retired.get('location')),tuple(o.location),tuple(o['saved_location']))
 addon._clear_runtime(None);native_refs.sync()
 assert o.animation_data.action==action
 assert any(c.as_pointer()==curve_pointer and c.data_path=='better_item.animation.dependency_stamp' for c in o.animation_data.drivers)
 assert before==(retired.get('binding_uid'),tuple(retired.get('location')),tuple(o.location),tuple(o['saved_location']))
 assert retired.get('dependencies_owned')
 assert not hasattr(addon,'_retire_animation_dependencies') and not hasattr(o.better_item,'animation')
 assert [h for h in bpy.app.handlers.frame_change_post if getattr(h,'__module__','').startswith('better_item')]==[transform_view.clear_cache]
 assert not hasattr(bpy.types,'BETTERITEM_OT_animation')
 # No active runtime calls write, remove, migrate or key animation data.
 for path in (root/'better_item').glob('*.py'):
  tree=ast.parse(path.read_text(encoding='utf-8'))
  forbidden=[node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr in {'driver_add','driver_remove','keyframe_insert','keyframe_delete','animation_data_clear','animation_data_create'}]
  assert not forbidden,(path.name,forbidden)
 labels=[]
 class Layout:
  def row(self,**kw):return self
  def column(self,**kw):return self
  def box(self):return self
  def prop(self,*args,**kw):pass
  def label(self,**kw):labels.append(kw.get('text',''))
  def operator(self,*args,**kw):return SimpleNamespace()
 addon.BETTERITEM_PT_transform.draw(SimpleNamespace(layout=Layout()),bpy.context)
 assert not any('animation' in label.lower() or 'bake' in label.lower() for label in labels)
 assert 'Scale (Default):' in labels
 print('155 LEGACY ISOLATION PASSED: archived file opens without deleting drivers/actions/data, no legacy runtime or UI handling, no animation-write calls; measurement-only callback retained')
