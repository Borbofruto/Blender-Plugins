import sys,itertools,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Euler,Vector
addon_utils.enable('better_item',default_set=True)
from better_item import engine,frames,arrange
context=bpy.context
settings=context.scene.better_item

def near(a,b,tol=3e-5):assert np.allclose(a,b,rtol=2e-6,atol=tol),(tuple(a),tuple(b))
def select(objects,active):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    context.view_layer.objects.active=active
    context.view_layer.update()
def empty(name):
    obj=bpy.data.objects.new(name,None)
    context.collection.objects.link(obj)
    return obj
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
objects=[empty('Cube.%03d'%i) for i in range(6)]
locations=[(.0137,-.0251,.0031),(-6.1234,3.7512,-2.1523),(4.8523,-1.5341,6.9871),
           (-1.4523,-7.8921,.8723),(8.5467,.1273,-4.1234),(-.8451,5.9862,1.6437)]
source=empty('Reference')
source.location=(2.1,-1.8,.005)
source.rotation_euler=(.21,.37,.59)
source.scale=(5,2,8)
parent=empty('Parent')
parent.location=(12,-20,.001)
parent.rotation_euler=(.2,.4,.6)
parent.scale=(2,.7,3)
context.view_layer.update()
frame=frames.create(context,'Reference Frame',source.matrix_world.translation,source.matrix_world.to_quaternion().to_matrix())
settings.arrange_object=source
settings.arrange_frame=frame.uid
settings.arrange_origin='MATCH'
settings.arrange_on_axis=False
count=0
for with_parent in (False,True):
    for orientation_mode in ('GLOBAL','REFERENCE','SAVED'):
        settings.arrange_orientation=orientation_mode
        for axes in itertools.product((False,True),repeat=3):
            if not any(axes):continue
            for reference in ('SELECTION','KEY','REFERENCE'):
                for action in ('MIN','CENTER','MAX','POS','NEG'):
                    for i,(obj,location) in enumerate(zip(objects,locations)):
                        obj.parent=parent if with_parent and i%2 else None
                        obj.matrix_parent_inverse=Matrix.Identity(4)
                        obj.location=location
                    select(objects,objects[0])
                    settings.reference=reference
                    settings.axes=axes
                    settings.spacing=1.39 if action=='POS' else -1.39
                    basis,origin,_=arrange.reference_frame(context)
                    before={obj.name:np.linalg.solve(basis,np.asarray(obj.matrix_world.translation)-origin) for obj in objects}
                    key=before[objects[0].name].copy()
                    expected={name:co.copy() for name,co in before.items()}
                    if action in ('MIN','CENTER','MAX'):
                        for axis,enabled in enumerate(axes):
                            if not enabled:continue
                            values=[co[axis] for co in before.values()]
                            destination=(min(values) if action=='MIN' else max(values) if action=='MAX' else (min(values)+max(values))/2)
                            if reference=='KEY':destination=key[axis]
                            if reference=='REFERENCE':destination=0
                            for co in expected.values():co[axis]=destination
                        status=bpy.ops.better_item.align(mode=action,reference=settings.reference,axes=tuple(settings.axes))
                    else:
                        step=float(settings.spacing)
                        for axis,enabled in enumerate(axes):
                            if not enabled:continue
                            if reference=='SELECTION':
                                order=sorted(before,key=lambda name:before[name][axis])
                                low,high=before[order[0]][axis],before[order[-1]][axis]
                                for rank,name in enumerate(order):expected[name][axis]=low+(high-low)*rank/(len(order)-1)
                            else:
                                anchor=key[axis] if reference=='KEY' else 0
                                names=[name for name in before if reference!='KEY' or name!=objects[0].name]
                                order=sorted(names,key=lambda name:(0 if (before[name][axis]-anchor)*step<0 else 1,abs(before[name][axis]-anchor),name))
                                for rank,name in enumerate(order,1):expected[name][axis]=anchor+rank*step
                        status=bpy.ops.better_item.distribute(reference=settings.reference,axes=tuple(settings.axes),spacing=settings.spacing,minimum_mm=settings.minimum_distance_mm)
                    assert status=={'FINISHED'},(with_parent,orientation_mode,axes,reference,action)
                    for obj in objects:
                        actual=np.linalg.solve(basis,np.asarray(obj.matrix_world.translation)-origin)
                        near(actual,expected[obj.name])
                    assert not arrange.error(context.scene)
                    count+=1
# Explicit failures are preflighted, with codes/names and no partial moves.
for obj,location in zip(objects,locations):
    obj.parent=None
    obj.location=location
select(objects,objects[0])
settings.arrange_orientation='GLOBAL'
settings.reference='KEY'
settings.axes=(True,False,False)
def rejects(code):
    before=[tuple(obj.location) for obj in objects]
    try:status=bpy.ops.better_item.distribute(reference=settings.reference,axes=tuple(settings.axes),spacing=settings.spacing,minimum_mm=settings.minimum_distance_mm)
    except RuntimeError:pass
    else:assert status=={'CANCELLED'},('Expected rejection',code,status)
    message=arrange.error(context.scene)
    assert code in message,message
    assert [tuple(obj.location) for obj in objects]==before
    return message
for spacing in (0,1e-12,-1e-12):
    settings.spacing=spacing
    rejects('BI-D001')
settings.spacing=.2
objects[1].location.x=objects[2].location.x
context.view_layer.update()
message=rejects('BI-D002')
assert objects[1].name in message and objects[2].name in message and 'X:' in message
# Same X is allowed when only Y is being distributed.
settings.axes=(False,True,False)
assert bpy.ops.better_item.distribute(reference=settings.reference,axes=tuple(settings.axes),spacing=settings.spacing,minimum_mm=settings.minimum_distance_mm)=={'FINISHED'}
settings.axes=(False,False,False)
rejects('BI-A001')
# Physical millimeter minimum is independent of Scene Unit Scale.
settings.axes=(True,False,False)
objects[1].location.x=-1
objects[2].location.x=1
context.view_layer.update()
context.scene.unit_settings.scale_length=.001
settings.spacing=1e-6
rejects('BI-D001')
context.scene.unit_settings.scale_length=1
# Place objects along the chosen rotated reference axis, without parenting.
for obj,location in zip(objects,locations):obj.location=location
select(objects,objects[0])
settings.reference='REFERENCE'
settings.arrange_orientation='REFERENCE'
settings.arrange_on_axis=True
settings.spacing=.3
basis,origin,_=arrange.reference_frame(context)
assert bpy.ops.better_item.distribute(reference=settings.reference,axes=tuple(settings.axes),spacing=settings.spacing,minimum_mm=settings.minimum_distance_mm)=={'FINISHED'}
for obj in objects:
    coordinates=np.linalg.solve(basis,np.asarray(obj.matrix_world.translation)-origin)
    near(coordinates[1:],(0,0),tol=1e-6)
    assert obj.parent is None and not obj.constraints
positions=[obj.matrix_world.copy() for obj in objects]
source.location.x+=1
source.rotation_euler.z+=.1
context.view_layer.update()
for obj,position in zip(objects,positions):near(obj.matrix_world.translation,position.translation)
# A frame still groups independent Location/Orientation components.
assert bpy.ops.better_item.new_frame(target='ALIGN_AXES',frame_name='Manual origin, linked axes')=={'FINISHED'}
mixed=context.scene.better_item.frames[-1]
mixed.position=(9,8,7)
mixed.rotation_mode='OBJECT'
mixed.rotation_source=source
near(frames.resolve(mixed)[0],(9,8,7))
assert mixed.rotation_source==source and not mixed.link_position and mixed.link_rotation
assert settings.arrange_frame==mixed.uid
assert bpy.ops.better_item.new_frame(target='ALIGN_ORIGIN',frame_name='Linked origin, manual axes')=={'FINISHED'}
other=context.scene.better_item.frames[-1]
other.rotation=(.1,.2,.3)
other.position_mode='OBJECT'
other.position_source=source
assert settings.arrange_origin_frame==other.uid and settings.arrange_frame==mixed.uid
assert other.link_position and not other.link_rotation
near(other.rotation,(.1,.2,.3))
# Main Transform origin and axes can also use those two different frames.
objects[0].better_item.orientation='SAVED'
objects[0].better_item.orientation_frame=mixed.uid
objects[0].better_item.pivot_mode='FRAME'
objects[0].better_item.pivot_frame=other.uid
source.location=(10,20,30)
context.view_layer.update()
near(frames.resolve(mixed)[0],(9,8,7))
near(frames.resolve(other)[0],(10,20,30))
# Native locked-axis rejection is still atomic.
select(objects,objects[0])
settings.reference='KEY'
settings.arrange_orientation='GLOBAL'
settings.arrange_on_axis=False
objects[1].lock_location[0]=True
settings.spacing=.25
rejects('BI-T003')
objects[1].lock_location[0]=False
assert type(bpy.types.BETTERITEM_PT_transform.bl_order)==int
assert bpy.types.BETTERITEM_PT_frames.bl_order < bpy.types.BETTERITEM_PT_transform.bl_order < bpy.types.BETTERITEM_PT_alignment.bl_order
print('ARRANGEMENT PASSED: %d combinations, all axis masks, signed steps, key/selection/reference origins, rotated/scaled parents, precision, errors, reference lines and mixed frames'%count)
# Arrangement references persist separately, including mixed frame components.
import tempfile
settings.arrange_orientation='SAVED'
settings.arrange_frame=mixed.uid
settings.arrange_origin='SAVED'
settings.arrange_origin_frame=other.uid
settings.reference='REFERENCE'
settings.arrange_on_axis=True
mixed_uid,other_uid=mixed.uid,other.uid
context.preferences.filepaths.file_preview_type='NONE'
with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
    path=str(Path(temp)/'arrangement.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.wm.open_mainfile(filepath=path)
    settings=bpy.context.scene.better_item
    assert settings.arrange_frame==mixed_uid and settings.arrange_origin_frame==other_uid
    assert settings.arrange_orientation=='SAVED' and settings.arrange_origin=='SAVED'
    assert settings.arrange_on_axis and settings.reference=='REFERENCE'
    mixed=frames.find(bpy.context.scene,mixed_uid)
    other=frames.find(bpy.context.scene,other_uid)
    near(frames.resolve(mixed)[0],(9,8,7))
    assert mixed.link_rotation and not mixed.link_position
    assert other.link_position and not other.link_rotation
    near(other.rotation,(.1,.2,.3))
    assert not arrange.error(bpy.context.scene)
print('ARRANGEMENT PERSISTENCE PASSED: axes/origin choices and independent mixed frame data')
# Additional orientation modes and a selected fixed reference source.
objects=[bpy.data.objects['Cube.%03d'%i] for i in range(6)]
source=bpy.data.objects['Reference']
settings=bpy.context.scene.better_item
for obj,location in zip(objects,locations):
    obj.parent=None
    obj.location=location
source.location=(2,-1,.3)
source.rotation_euler=(.2,.3,.4)
select(objects+[source],objects[0])
settings.reference='REFERENCE'
settings.arrange_orientation='REFERENCE'
settings.arrange_object=source
settings.arrange_origin='MATCH'
settings.axes=(True,False,False)
settings.arrange_on_axis=True
settings.spacing=.2
source_position=source.matrix_world.translation.copy()
assert bpy.ops.better_item.distribute(reference='REFERENCE',axes=tuple(settings.axes),spacing=.2)=={'FINISHED'}
near(source.matrix_world.translation,source_position,tol=1e-7)
for orientation_mode in ('LOCAL','VIEWPORT'):
    for obj,location in zip(objects,locations):obj.location=location
    select(objects,objects[0])
    settings.arrange_orientation=orientation_mode
    bpy.context.scene.transform_orientation_slots[0].type='GLOBAL'
    basis,origin,_=arrange.reference_frame(bpy.context)
    assert bpy.ops.better_item.distribute(reference='REFERENCE',axes=tuple(settings.axes),spacing=.2)=={'FINISHED'}
    for obj in objects:
        co=np.linalg.solve(basis,np.asarray(obj.matrix_world.translation)-origin)
        near(co[1:],(0,0))
# Coded driver/constraint errors preserve every object's native Location.
for obj,location in zip(objects,locations):obj.location=location
select(objects,objects[0])
settings.reference='KEY'
settings.arrange_orientation='GLOBAL'
settings.arrange_on_axis=False
curve=objects[1].driver_add('location',0)
curve.driver.expression='2'
bpy.context.view_layer.update()
rejects('BI-T002')
objects[1].driver_remove('location',0)
constraint=objects[1].constraints.new('COPY_LOCATION')
constraint.name='Driven placement'
constraint.target=source
bpy.context.view_layer.update()
assert 'Driven placement' in rejects('BI-T004')
objects[1].constraints.remove(constraint)
print('ARRANGEMENT EDGE CASES PASSED: selected reference, Local/Viewport axes, driver and named constraint diagnostics')
# Using only one frame component must not require its unused linked component.
source=bpy.data.objects['Reference']
objects=[bpy.data.objects['Cube.%03d'%i] for i in range(6)]
manual_axes=frames.create(bpy.context,'Axes only',Vector((1,2,3)),Euler((.1,.2,.3)).to_matrix(),source,
    follow_position=True,follow_rotation=False)
manual_axes.position_source=None
near(frames.frame_axes(manual_axes)[0],Euler((.1,.2,.3)).to_matrix()[0])
try:frames.frame_origin(manual_axes)
except Exception as exc:assert 'BI-F002' in str(exc) and 'Location' in str(exc) and exc.severity=='INFO'
else:raise AssertionError('The missing linked Location must still fail when requested')
manual_origin=frames.create(bpy.context,'Origin only',Vector((4,5,6)),Euler((.2,.3,.4)).to_matrix(),source,
    follow_position=False,follow_rotation=True)
manual_origin.rotation_source=None
near(frames.frame_origin(manual_origin),(4,5,6))
frames.apply_reference(manual_origin,'POSITION')
select(objects,objects[0])
settings=bpy.context.scene.better_item
settings.arrange_orientation='SAVED'
settings.arrange_frame=manual_axes.uid
settings.reference='SELECTION'
assert bpy.ops.better_item.align(reference='SELECTION',axes=(False,True,False),mode='MAX')=={'FINISHED'}
settings.arrange_orientation='GLOBAL'
settings.arrange_origin='SAVED'
settings.arrange_origin_frame=manual_origin.uid
settings.reference='REFERENCE'
assert bpy.ops.better_item.align(reference='REFERENCE',axes=(False,True,False),mode='CENTER')=={'FINISHED'}
for obj in objects:assert abs(obj.matrix_world.translation.y-5)<1e-5
objects[0].better_item.orientation='SAVED'
objects[0].better_item.orientation_frame=manual_axes.uid
objects[0].better_item.pivot_mode='FRAME'
objects[0].better_item.pivot_frame=manual_origin.uid
near(frames.object_origin(bpy.context,objects[0]),(4,5,6))
near(frames.object_axes(bpy.context,objects[0])[0],Euler((.1,.2,.3)).to_matrix()[0])
print('FRAME COMPONENT ISOLATION PASSED: axes-only/origin-only usage ignores unused missing source components')
# Tiny spacing can be mathematically valid but impossible in native float32.
precision_objects=[empty('Precision %d'%i) for i in range(3)]
for i,obj in enumerate(precision_objects):obj.location=(1+i,0,0)
select(precision_objects,precision_objects[0])
settings=bpy.context.scene.better_item
settings.arrange_orientation='GLOBAL'
settings.reference='KEY'
settings.axes=(True,False,False)
settings.minimum_distance_mm=.00001
original_positions=[tuple(obj.location) for obj in precision_objects]
try:status=bpy.ops.better_item.distribute(reference='KEY',axes=(True,False,False),spacing=1e-8)
except RuntimeError:pass
else:assert status=={'CANCELLED'},'Native precision must not silently collapse spacing'
assert 'BI-D003' in arrange.error(bpy.context.scene)
assert 'Precision 1' in arrange.error(bpy.context.scene)
assert [tuple(obj.location) for obj in precision_objects]==original_positions
assert bpy.ops.better_item.distribute(reference='KEY',axes=(True,False,False),spacing=1e-5)=={'FINISHED'}
assert not arrange.error(bpy.context.scene)
print('NATIVE PRECISION SPACING PASSED: collapsed spacing is rejected and atomically restored')

