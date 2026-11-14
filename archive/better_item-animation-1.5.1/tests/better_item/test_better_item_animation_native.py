import sys,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Matrix,Euler
addon_utils.enable('better_item',default_set=True)
from better_item import animation,frames,native_refs,orientation
ctx=bpy.context
def empty(name):
    o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);return o
def near(a,b):assert np.allclose(a,b,rtol=0,atol=3e-5),(a,b)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
source=empty('Native Controller');obj=empty('Native Actor')
ctx.view_layer.objects.active=obj;obj.select_set(True);ctx.view_layer.update()
owner=frames.create(ctx,'Native owner',obj.matrix_world.translation,Matrix.Identity(3),source)
# Its unused position points at the target: only Orientation is consumed.
owner.position_source=obj
native_refs.publish(ctx,owner);name=owner.native_name
obj.better_item.orientation='NATIVE';obj.better_item.reference_native=name
obj.better_item.animation.drive_location=False
animation.start(ctx,obj)
source.rotation_euler=(.2,.3,.4);ctx.view_layer.update();animation.sync()
a=obj.better_item.animation
assert not a.error,a.error
near(orientation.rotation(obj),orientation.rotation(source))
assert animation._sources(ctx.scene,frames.find(ctx.scene,a.binding_uid))=={source}
previous=orientation.rotation(obj).copy()
with native_refs.view_context(ctx):
    ctx.scene.transform_orientation_slots[0].type=name;bpy.ops.transform.delete_orientation()
animation.sync()
assert not a.error,a.error
assert frames.find(ctx.scene,a.binding_uid).rotation_mode=='MANUAL'
near(orientation.rotation(obj),previous)
animation.pause(obj)
# External native orientation matrices stay live, then freeze on native deletion.
with native_refs.view_context(ctx):
    bpy.ops.transform.create_orientation(name='External animation axes',use_view=True,use=True)
    custom=ctx.scene.transform_orientation_slots[0].custom_orientation
    custom.matrix=Matrix.Identity(3)
obj.better_item.reference_mode='INDIVIDUAL';obj.better_item.orientation='NATIVE'
obj.better_item.reference_native=custom.name
animation.start(ctx,obj);relative=Euler(tuple(a.rotation),a.order).to_matrix()
custom.matrix=Euler((.4,.2,-.3)).to_matrix();expected=custom.matrix@relative
animation.sync();assert not a.error,a.error;near(orientation.rotation(obj),expected)
with native_refs.view_context(ctx):bpy.ops.transform.delete_orientation()
animation.sync();assert not a.error,a.error
near(orientation.rotation(obj),expected)
print('ANIMATED NATIVE REFERENCES PASSED: live managed/external orientation, independent component dependencies and native-menu deletion fallback')
