import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Vector
addon_utils.enable('better_item',default_set=True)
from better_item import animation
ctx=bpy.context
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
source=bpy.data.objects.new('Controller',None);ctx.scene.collection.objects.link(source);source.hide_render=True
collection=bpy.data.collections.new('Excluded Controller');ctx.scene.collection.children.link(collection)
ctx.scene.collection.objects.unlink(source);collection.objects.link(source)
ctx.view_layer.layer_collection.children[collection.name].exclude=True
source.location=(10,0,0)
bpy.ops.mesh.primitive_cube_add(size=.5,location=(-.5,0,0));actor=ctx.object
s=actor.better_item;s.pivot_mode='OBJECT';s.origin_object=source;s.orientation='REFERENCE';s.orientation_object=source
ctx.view_layer.update();animation.start(ctx,actor)
source.location=(10,0,0);source.keyframe_insert(data_path='location',frame=1)
source.location=(11,0,0);source.keyframe_insert(data_path='location',frame=2)
camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));ctx.scene.collection.objects.link(camera)
camera.location=(0,0,5);camera.data.type='ORTHO';camera.data.ortho_scale=3
scene=ctx.scene;scene.camera=camera;scene.frame_start=1;scene.frame_end=2
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1
scene.render.resolution_x=32;scene.render.resolution_y=32;scene.render.resolution_percentage=100
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
material=bpy.data.materials.new('Emission');material.use_nodes=True
nodes=material.node_tree.nodes;nodes.clear()
out=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission')
material.node_tree.links.new(emission.outputs[0],out.inputs[0]);actor.data.materials.append(material)
with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
    scene.render.filepath=str(Path(temp)/'frame_')
    bpy.ops.render.render(animation=True)
    centers=[]
    for frame in (1,2):
        image=bpy.data.images.load(str(Path(temp)/('frame_%04d.png'%frame)))
        rgba=np.asarray(image.pixels[:]).reshape((32,32,4));alpha=rgba[:,:,3]
        assert alpha.sum()>1
        centers.append(float((alpha*np.arange(32)[None,:]).sum()/alpha.sum()))
        bpy.data.images.remove(image)
    assert centers[1]>centers[0]+5,centers
assert not s.animation.error,s.animation.error
print('RELATIVE RENDER PASSED: actual rendered pixel centroids follow the animated controller',centers)


