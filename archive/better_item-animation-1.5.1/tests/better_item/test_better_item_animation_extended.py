import sys,math,itertools,tempfile,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Vector,Euler
addon_utils.enable('better_item',default_set=True)
from better_item import animation,frames,trace,references
from better_item.math_core import BetterItemError
ctx=bpy.context
def near(a,b,tol=5e-5):assert np.allclose(a,b,rtol=0,atol=tol),(a,b)
def empty(name):
    o=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(o);return o
def linear(obj):
    for c in animation.object_curves(obj):
        for k in c.keyframe_points:k.interpolation='LINEAR'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parent=empty('Parent');grand=empty('Grandparent');parent.parent=grand
grand.location=(2,3,4);grand.rotation_euler=(.1,.2,.3)
parent.location=(10,20,30);parent.rotation_euler=(.2,.3,.4);parent.scale=(2,2,2)
source=empty('Source');source.location=(4,5,6);source.rotation_euler=(.1,.2,.3)
count=0
for mode,mirror in itertools.product(('XYZ','ZYX','QUATERNION','AXIS_ANGLE'),(False,True)):
    obj=empty('Actor '+mode+str(mirror));obj.parent=parent;obj.location=(1,2,3);obj.delta_location=(.5,-.25,1)
    obj.scale=(-1,1,1) if mirror else (1,1,1);obj.rotation_mode=mode
    s=obj.better_item;s.orientation='REFERENCE';s.orientation_object=source;s.pivot_mode='OBJECT';s.origin_object=source
    ctx.view_layer.objects.active=obj;obj.select_set(True);ctx.view_layer.update()
    animation.start(ctx,obj);a=s.animation
    ctx.scene.frame_set(1);animation.keyframe(obj,'LOCATION',1);animation.keyframe(obj,'ROTATION',1)
    ctx.scene.frame_set(9);a.location=(2,3,4);a.rotation=(.3,.2,.1)
    animation.keyframe(obj,'LOCATION',9);animation.keyframe(obj,'ROTATION',9);linear(obj)
    for frame in (1,5,9,2,8):
        ctx.scene.frame_set(frame);assert not a.error,a.error
        origin,axes=animation.basis(ctx,obj)
        near(obj.matrix_world.translation,origin+axes@Vector(a.location))
        expected=axes@Euler(a.rotation,a.order).to_matrix()
        from better_item.orientation import rotation
        near(rotation(obj),expected)
        assert tuple(obj.scale)==((-1,1,1) if mirror else (1,1,1))
    animation.pause(obj);count+=1
# Exact affine accounting with rotation, scale, inverse and deltas.
obj=empty('Trace target');obj.parent=parent;obj.location=(1,2,3);obj.delta_location=(.2,.4,.6)
obj.matrix_parent_inverse=Matrix.Translation((-.5,1,2));ctx.view_layer.update()
v=trace.values(obj);near(v['world'],v['parent_origin']+v['contribution']+v['residual'])
near(v['local'],obj.location);near(v['delta'],obj.delta_location);near(v['residual'],(0,0,0))
assert 'Nested hierarchy' in trace.parent_label(obj)
obj.better_item.reference_location='PARENT';obj.better_item.reference_orientation='PARENT'
near(frames.object_origin(ctx,obj),parent.matrix_world.translation)
near(frames.object_axes(ctx,obj),parent.matrix_world.to_3x3().normalized())
f=frames.create(ctx,'Parent frame',Vector(),Matrix.Identity(3))
f.position_mode=f.rotation_mode='PARENT';f.position_source=f.rotation_source=obj
near(frames.frame_origin(f),parent.matrix_world.translation)
assert 'Direct parent' in trace.parent_label(parent)
obj.parent=None;ctx.view_layer.update()
near(frames.object_origin(ctx,obj),(0,0,0));near(frames.object_axes(ctx,obj),Matrix.Identity(3))
assert trace.parent_label(obj).startswith('No parent')
# Linked zero-ratio rejection remains atomic for actual animated vectors.
actor=empty('Persisted Actor');actor.location=(11,0,0)
controller=empty('Animated Controller');controller.location=(10,0,0)
ctx.view_layer.objects.active=actor;ctx.view_layer.update()
s=actor.better_item;s.orientation='REFERENCE';s.orientation_object=controller;s.pivot_mode='OBJECT';s.origin_object=controller
animation.start(ctx,actor);a=s.animation
a.location=(0,2,3);s.link_location=(True,True,True);before=tuple(a.location)
a.location.x=1
assert tuple(a.location)==before and a.error
s.link_location=(False,False,False)
ctx.scene.frame_set(1);a.location=(1,0,0);animation.keyframe(actor,'LOCATION',1)
controller.location=(10,0,0);controller.keyframe_insert(data_path='location',frame=1)
ctx.scene.frame_set(11);a.location=(3,0,0);animation.keyframe(actor,'LOCATION',11)
controller.location=(20,0,0);controller.keyframe_insert(data_path='location',frame=11)
linear(actor);linear(controller);ctx.scene.frame_set(6)
assert not a.error,a.error;near(actor.matrix_world.translation,(17,0,0))
# Another live actor can provide the reference: explicit dependency order wins.
child=empty('Dependent Actor');child.location=(18,0,0);cs=child.better_item
cs.orientation='REFERENCE';cs.orientation_object=actor;cs.pivot_mode='OBJECT';cs.origin_object=actor
ctx.view_layer.objects.active=child;ctx.view_layer.update();animation.start(ctx,child)
ctx.scene.frame_set(7);near(child.matrix_world.translation,actor.matrix_world.translation+Vector((1,0,0)))
assert not child.better_item.animation.error
# Fresh-process loading restores curves, bindings, cache and handlers.
root=Path(__file__).resolve().parents[2]/"src";ctx.preferences.filepaths.file_preview_type='NONE'
with tempfile.TemporaryDirectory(dir=root) as temp:
    path=Path(temp)/'animated.blend';reader=Path(temp)/'reader.py'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    reader.write_text(f'''import sys
sys.path.insert(0,{str(root)!r})
import bpy,addon_utils
addon_utils.enable('better_item',default_set=True)
from better_item import animation
bpy.ops.wm.open_mainfile(filepath={str(path)!r})
bpy.context.scene.frame_set(6)
a=bpy.data.objects['Persisted Actor']
assert not a.better_item.animation.error,a.better_item.animation.error
assert abs(a.matrix_world.translation.x-17)<5e-5,tuple(a.matrix_world.translation)
bpy.data.objects.remove(bpy.data.objects['Animated Controller'],do_unlink=True)
bpy.context.scene.frame_set(7)
assert not a.better_item.animation.error,a.better_item.animation.error
assert abs(a.matrix_world.translation.x-17.2)<5e-5,tuple(a.matrix_world.translation)
''',encoding='utf-8')
    result=subprocess.run([bpy.app.binary_path,'--background','--factory-startup','--python-exit-code','1','--python',str(reader)],capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
print('EXTENDED ANIMATION PASSED: %d parent/mirror/storage setups, exact affine trace, Parent scope/labels, atomic linked rejection, animated controller, actor dependency order and fresh-process fallback'%count)
