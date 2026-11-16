"""Representative upward .blend migration, including affine GN and references."""
import sys,json,argparse
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parent
for candidate in (root/'source',root.parent/'source',root.parents[2]/'src'):
 if (candidate/'better_item/__init__.py').exists():
  sys.path.insert(0,str(candidate));break
import bpy,numpy as np
from mathutils import Vector,Euler
import better_item as addon
from better_item import frames,transform_view as view
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--fixture',type=Path,required=True);a=p.parse_args(args);addon.register()

def snapshot():
 obj=bpy.data.objects['Migrating Piece'];frame=bpy.context.scene.better_item.frames[0];view._dimensions_modifier(obj)
 return {'world':[v for row in obj.matrix_world for v in row],'scale':list(obj.scale),'location':list(frames.relative_values(bpy.context,obj,'POSITION')),'dimensions':list(view.values(bpy.context,obj,'DIMENSIONS')),'frame_uid':frame.uid,'frame_source':frame.position_source.name,'selected_frame':obj.better_item.reference_frame,'distribution_mode':bpy.context.scene.better_item.distribution_mode,'spacing':bpy.context.scene.better_item.spacing,'modifier_count':len(obj.modifiers)}

if a.write:
 obj=bpy.context.object;obj.name='Migrating Piece'
 source=bpy.data.objects.new('Linked Reference',None);bpy.context.scene.collection.objects.link(source);source.location=(7,-2,1);source.rotation_euler.z=.7
 bpy.context.view_layer.update();frame=frames.create(bpy.context,'Persisted Frame',Vector(),Euler((0,0,.7)).to_matrix());frame.position_mode='OBJECT';frame.position_source=source;frame.rotation_mode='OBJECT';frame.rotation_source=source
 obj.better_item.transform_space='REFERENCE';obj.better_item.reference_mode='FRAME';obj.better_item.reference_frame=frame.uid
 bpy.context.scene.better_item.arrange_reference_mode='FRAME';bpy.context.scene.better_item.arrange_reference_frame=frame.uid;bpy.context.scene.better_item.distribution_mode='GEOMETRY';bpy.context.scene.better_item.spacing=-.5
 bpy.context.view_layer.update();before=view.values(bpy.context,obj,'DIMENSIONS');view.set_dimensions(bpy.context,obj,tuple(x*f for x,f in zip(before,(1.2,.8,1))));assert len(obj.modifiers)==1
 expected=snapshot();a.fixture.parent.mkdir(exist_ok=True);a.fixture.with_suffix('.json').write_text(json.dumps(expected,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(a.fixture));print('WROTE CROSS VERSION FIXTURE',bpy.app.version_string)
else:
 bpy.ops.wm.open_mainfile(filepath=str(a.fixture));bpy.context.view_layer.update();expected=json.loads(a.fixture.with_suffix('.json').read_text(encoding='utf-8'));actual=snapshot()
 for key in expected:
  if isinstance(expected[key],list):assert np.allclose(actual[key],expected[key],atol=2e-5,rtol=1e-6),(key,expected[key],actual[key])
  else:assert actual[key]==expected[key],(key,expected[key],actual[key])
 result={'passed':True,'reader':bpy.app.version_string,'writer':'4.2.0','world_native_scale_relative_location_dimensions_frame_and_affine_modifier_preserved':True};(root/'cross-version.results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
addon.unregister()
