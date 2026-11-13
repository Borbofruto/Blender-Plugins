import sys,time,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Euler
addon_utils.enable('better_item',default_set=True)
from better_item import transform_view
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
n=250000
co=np.random.default_rng(42).uniform(-1,1,(n,3)).astype(np.float32)
mesh=bpy.data.meshes.new('Dense')
mesh.vertices.add(n)
mesh.vertices.foreach_set('co',co.ravel())
mesh.update()
obj=bpy.data.objects.new('Dense',mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active=obj
bpy.context.view_layer.update()
axes=Euler((.3,.7,.2)).to_matrix()
flags=[]
def inspect(scene,graph):
    flags.extend((u.id.name,u.is_updated_geometry,u.is_updated_transform) for u in graph.updates)
bpy.app.handlers.depsgraph_update_post.append(inspect)
measure=[]
for value in (.1,.2,.3):
    obj.location.x=value
    bpy.context.view_layer.update()
    begin=time.perf_counter()
    result=transform_view.dimensions(obj,axes)
    measure.append((time.perf_counter()-begin)*1000)
bpy.app.handlers.depsgraph_update_post.remove(inspect)
scale_measure=[]
for value in (1.1,1.2,1.3):
    obj.scale.x=value
    bpy.context.view_layer.update()
    begin=time.perf_counter()
    transform_view.dimensions(obj,axes)
    scale_measure.append((time.perf_counter()-begin)*1000)
print(json.dumps({'vertices':n,'dimensions_ms':measure,'dimensions':result,'scale_projection_ms':scale_measure,'location_update_flags':flags}))
