import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix
addon_utils.enable('better_item',default_set=True)
from better_item import animation,transform_view
ctx=bpy.context
def near(a,b):assert np.allclose(a,b,rtol=0,atol=5e-5),(a,b)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=1);obj=ctx.object
assert not obj.better_item.bl_rna.properties['location_x'].is_animatable
assert obj.better_item.animation.bl_rna.properties['location'].is_animatable
obj.location=(1,2,3);animation.keyframe(obj,'LOCATION',1)
obj.location=(3,4,5);animation.keyframe(obj,'LOCATION',11)
for c in animation.object_curves(obj):
    for k in c.keyframe_points:k.interpolation='LINEAR'
ctx.scene.frame_set(6);near(obj.location,(2,3,4))
assert animation.has_key(obj,'LOCATION',1)
animation.keyframe(obj,'LOCATION',1,delete=True)
assert not animation.has_key(obj,'LOCATION',1)
# Dimensions keys animate the actual native Scale / affine sockets, not a
# custom UI getter that Blender cannot evaluate into geometry.
ref=bpy.data.objects.new('Oblique axes',None);ctx.scene.collection.objects.link(ref);ref.rotation_euler.z=.4
obj.better_item.orientation='REFERENCE';obj.better_item.orientation_object=ref
ctx.view_layer.update();ctx.scene.frame_set(1)
before=transform_view.values(ctx,obj,'DIMENSIONS');wanted=(before[0]*1.4,before[1],before[2])
transform_view.set_dimensions(ctx,obj,wanted);animation.keyframe(obj,'DIMENSIONS',1)
first=transform_view.values(ctx,obj,'DIMENSIONS')
ctx.scene.frame_set(11)
transform_view.set_dimensions(ctx,obj,(first[0]*1.3,first[1],first[2]));animation.keyframe(obj,'DIMENSIONS',11)
last=transform_view.values(ctx,obj,'DIMENSIONS')
ctx.scene.frame_set(1);near(transform_view.values(ctx,obj,'DIMENSIONS'),first)
ctx.scene.frame_set(11);near(transform_view.values(ctx,obj,'DIMENSIONS'),last)
# Bake a separate relative actor and prove native playback survives unregister.
bpy.ops.object.empty_add();actor=ctx.object;actor.location=(10,0,0)
animation.start(ctx,actor);a=actor.better_item.animation
ctx.scene.frame_set(1);a.location=(1,2,3);animation.keyframe(actor,'LOCATION',1)
ctx.scene.frame_set(3);a.location=(3,4,5);animation.keyframe(actor,'LOCATION',3)
a.start=1;a.end=3;animation.bake(ctx,actor)
expected=[]
for frame in (1,2,3):ctx.scene.frame_set(frame);expected.append(tuple(actor.location))
assert not any(c.data_path.startswith('better_item.') for c in animation.object_curves(actor))
addon_utils.disable('better_item',default_set=True)
for frame,pose in zip((1,2,3),expected):ctx.scene.frame_set(frame);near(actor.location,pose)
print('NATIVE KEYS PASSED: native insertion/deletion, protected proxies, keyable affine Dimensions and baked playback with addon disabled')


