import sys,math,time
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Euler
addon_utils.enable('better_item',default_set=True)
from better_item import transform_view as view,frames
context=bpy.context

def near(a,b):assert np.allclose(a,b,rtol=2e-6,atol=2e-6),(a,b)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
mesh=bpy.data.meshes.new('Cached')
co=np.random.default_rng(123).uniform(-2,2,(1000,3)).astype(np.float32)
mesh.vertices.add(len(co))
mesh.vertices.foreach_set('co',co.ravel())
mesh.update()
obj=bpy.data.objects.new('Cached',mesh)
context.collection.objects.link(obj)
obj.rotation_euler=(.3,.5,.7)
obj.scale=(-2,.7,3)
context.view_layer.update()
axes=Euler((.2,.8,.1)).to_matrix()
linear=axes.transposed()@obj.matrix_world.to_3x3()
points=np.asarray([tuple(linear@v.co) for v in mesh.vertices])
expected=np.ptp(points,axis=0)
near(view.dimensions(obj,axes),expected)
key=view._geometry_key(obj,context.evaluated_depsgraph_get())
coordinates=view._geometry_cache[key]
result=view.dimensions(obj,axes)
# Translation and unrelated scene edits do not discard target geometry/results.
obj.location.x+=50
context.view_layer.update()
assert view.dimensions(obj,axes) is result
assert view._geometry_cache[key] is coordinates
bpy.ops.mesh.primitive_cube_add(size=1)
other=context.object
other.data.vertices[0].co.x-=1
other.data.update()
context.view_layer.update()
near(view.dimensions(obj,axes),expected)
assert view._geometry_cache[key] is coordinates
# Rotation invalidates the projection by key, not the local vertex coordinates.
obj.rotation_euler.y+=.3
context.view_layer.update()
view.dimensions(obj,axes)
assert view._geometry_cache[key] is coordinates
# Shared mesh changes invalidate every cached user of that mesh.
shared=bpy.data.objects.new('Shared',mesh)
context.collection.objects.link(shared)
context.view_layer.update()
view.dimensions(shared,Matrix.Identity(3))
mesh.vertices[0].co.x=100
mesh.update()
context.view_layer.update()
assert key not in view._geometry_cache
assert view.dimensions(shared,Matrix.Identity(3))[0]>100
linear=axes.transposed()@obj.matrix_world.to_3x3()
points=np.asarray([tuple(linear@v.co) for v in mesh.vertices])
near(view.dimensions(obj,axes),np.ptp(points,axis=0))
# Evaluated geometry invalidation includes a modifier's external dependencies.
bpy.ops.mesh.primitive_cube_add(size=1)
modified=context.object
bpy.ops.object.empty_add(location=(2,0,0))
source=context.object
mirror=modified.modifiers.new('Dependency','MIRROR')
mirror.mirror_object=source
mirror.use_mirror_merge=False
context.view_layer.update()
near(view.dimensions(modified,Matrix.Identity(3)),(5,1,1))
source.location.x=3
context.view_layer.update()
near(view.dimensions(modified,Matrix.Identity(3)),(7,1,1))
# Geometry cache entries and bytes are bounded; oversized reads remain correct.
old_count,old_bytes=view._GEOMETRY_CACHE_ENTRIES,view._GEOMETRY_CACHE_BYTES
view.clear_cache()
view._GEOMETRY_CACHE_ENTRIES=2
view._GEOMETRY_CACHE_BYTES=200
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(size=1)
    near(view.dimensions(context.object,Matrix.Identity(3)),(1,1,1))
    assert len(view._geometry_cache)<=2
    assert sum(array.nbytes for array in view._geometry_cache.values())<=200
view.dimensions(shared,Matrix.Identity(3)) # larger than the temporary byte budget
assert sum(array.nbytes for array in view._geometry_cache.values())<=200
view._GEOMETRY_CACHE_ENTRIES,view._GEOMETRY_CACHE_BYTES=old_count,old_bytes
view.clear_cache()
# Current item lists are retained once per existing scene, not once per rename.
frame=frames.create(context,'Original',source.location,Matrix.Identity(3))
context.object.better_item.orientation='SAVED'
context.object.better_item.orientation_frame=frame.uid
for i in range(2000):
    frame.name='Renamed %d'%i
    items=frames.frame_items(None,context)
    assert items[1][1]==frame.name
assert len(frames._enum_cache)==1
assert context.object.better_item.orientation_frame==frame.uid
second=bpy.data.scenes.new('Second')
frames.frame_items(None,SimpleNamespace(scene=second))
assert len(frames._enum_cache)==2
bpy.data.scenes.remove(second)
frames.frame_items(None,context)
assert len(frames._enum_cache)==1
print('CACHE TESTS PASSED: vectorized extrema, transform reuse, unrelated edits, shared meshes, modifier dependencies, bounded memory and 2000 frame renames')
