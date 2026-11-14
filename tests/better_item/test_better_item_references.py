"""Integration coverage for independently sourced scene frames and native axes."""
import sys,math,tempfile,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Matrix,Vector,Euler
addon_utils.enable('better_item',default_set=True)
import better_item as addon
from better_item import frames,native_refs,transform_view,arrange
from better_item.math_core import BetterItemError
ctx=bpy.context

def near(a,b,tol=2e-5):
    assert max(abs(x-y) for x,y in zip(a,b))<tol,(tuple(a),tuple(b))
def matrix_near(a,b):near(tuple(v for row in a for v in row),tuple(v for row in b for v in row))
def fails(fn,code):
    try:fn()
    except BetterItemError as exc:assert code in str(exc),str(exc)
    else:raise AssertionError('Expected '+code)

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=2)
a=ctx.object;a.name='Location source';a.location=(10,20,30)
bpy.ops.mesh.primitive_cube_add(size=2)
b=ctx.object;b.name='Orientation source';b.location=(-3,1,2);b.rotation_euler=(.2,.3,.4)
bpy.ops.mesh.primitive_cube_add(size=1)
target=ctx.object;target.name='Target';target.location=(4,5,6)
ctx.view_layer.update()
original=target.matrix_world.copy()
assert addon.frames.BETTERITEM_PT_frames.bl_order==0
assert addon.BETTERITEM_PT_transform.bl_order==1
assert addon.BETTERITEM_PT_alignment.bl_order==2
assert set(bpy.ops.better_item.new_frame.get_rna_type().properties.keys())=={'rna_type','target','target_name','frame_name'}
bpy.ops.better_item.new_frame(frame_name='Independent channels',target='BOTH')
f=ctx.scene.better_item.frames[-1]
assert f.position_mode==f.rotation_mode=='MANUAL'
f.position_mode='OBJECT';f.position_source=a
f.rotation_mode='OBJECT';f.rotation_source=b
near(frames.frame_origin(f),a.location)
matrix_near(frames.frame_axes(f),b.matrix_world.to_3x3())
assert target.better_item.reference_frame==f.uid
near(frames.object_origin(ctx,target),a.location)
matrix_near(frames.object_axes(ctx,target),b.matrix_world.to_3x3())
matrix_near(target.matrix_world,original)
# One selected frame drives live location and rotation, not object parenting.
target.better_item.location_x=8
near(frames.relative_values(ctx,target,'POSITION'),(8,*(frames.relative_values(ctx,target,'POSITION')[1:])))
before=target.matrix_world.copy()
a.location.x+=2;b.rotation_euler.z+=.1;ctx.view_layer.update()
matrix_near(target.matrix_world,before)
assert target.parent is None and not target.constraints
# Individual keeps independent components, Frame ignores the individual fields.
target.better_item.reference_mode='INDIVIDUAL'
target.better_item.pivot_mode='CURSOR';target.better_item.orientation='SAVED';target.better_item.orientation_frame=f.uid
near(frames.object_origin(ctx,target),ctx.scene.cursor.location)
target.better_item.reference_mode='FRAME'
assert not transform_view.scale_editable(target)
near(frames.object_origin(ctx,target),a.location)
# Native G/R use the exported axes, with no helper objects.
count=len(bpy.data.objects)
native_refs.publish(ctx,f,select=True)
assert len(bpy.data.objects)==count
assert ctx.scene.transform_orientation_slots[0].type==f.native_name
matrix_near(ctx.scene.transform_orientation_slots[0].custom_orientation.matrix,frames.frame_axes(f))
with native_refs.view_context(ctx):
    before=target.matrix_world.translation.copy()
    axes=frames.frame_axes(f)
    bpy.ops.transform.translate(value=(2,0,0),orient_type=f.native_name,constraint_axis=(True,False,False))
    ctx.view_layer.update()
    near(target.matrix_world.translation,before+axes.col[0]*2)
    before=target.matrix_world.to_quaternion().to_matrix()
    bpy.ops.transform.rotate(value=.2,orient_axis='Z',orient_type=f.native_name,constraint_axis=(False,False,True))
    ctx.view_layer.update()
    from mathutils import Quaternion
    matrix_near(target.matrix_world.to_quaternion().to_matrix(),Quaternion(axes.col[2],.2).to_matrix()@before)
# Another frame may reference the first through its native orientation.
bpy.ops.better_item.new_frame(frame_name='Native dependency')
g=ctx.scene.better_item.frames[-1];g.rotation_mode='NATIVE';g.native_source=f.native_name
matrix_near(frames.frame_axes(g),frames.frame_axes(f))
native_refs.publish(ctx,g)
f.rotation_mode='NATIVE';f.native_source=g.native_name
fails(lambda:frames.frame_axes(f),'BI-F001')
native_refs.sync()
assert native_refs.named(ctx.scene,f.native_name) is None
assert native_refs.named(ctx.scene,g.native_name) is None
f.rotation_mode='OBJECT';f.rotation_source=b
native_refs.sync()
assert native_refs.named(ctx.scene,f.native_name) is not None
matrix_near(frames.frame_axes(g),frames.frame_axes(f))
# Missing linked orientation is suspended, not left as a stale native entry.
f.rotation_source=None
native_refs.sync()
assert f.native_suspended and native_refs.named(ctx.scene,f.native_name) is None
f.rotation_source=b;native_refs.sync()
assert not f.native_suspended
# Direct component chains and cycles, independent unused-component validation.
g.position_mode='FRAME';g.position_frame=f.uid
near(frames.frame_origin(g),a.location)
f.position_mode='FRAME';f.position_frame=g.uid
fails(lambda:frames.frame_origin(f),'BI-F001')
matrix_near(frames.frame_axes(f),b.matrix_world.to_3x3())
f.position_mode='OBJECT'
# Pivot types (frame = one origin; Individual means active object's origin).
for obj in list(ctx.selected_objects):obj.select_set(False)
a.select_set(True);b.select_set(True);ctx.view_layer.objects.active=b
g.position_mode='PIVOT'
ctx.scene.cursor.location=(7,8,9)
for mode,expected in [('ACTIVE_ELEMENT',b.location),('INDIVIDUAL_ORIGINS',b.location),
    ('CURSOR',(7,8,9)),('MEDIAN_POINT',(a.location+b.location)/2)]:
    g.position_pivot=mode;near(frames.frame_origin(g),expected)
g.position_pivot='BOUNDING_BOX_CENTER'
points=[o.matrix_world@Vector(c) for o in (a,b) for c in o.bound_box]
near(frames.frame_origin(g),[(min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)])
for mode in native_refs.BUILTINS:
    g.rotation_mode='NATIVE';g.native_source=mode
    matrix=native_refs.orientation(ctx,mode)
    assert abs(matrix.determinant())>1e-6
    matrix_near(frames.frame_axes(g),matrix)
# Gimbal keeps its nonorthogonal axes, including an applied independent copy.
g.native_source='GIMBAL';basis=frames.frame_axes(g)
assert abs(basis.col[0].dot(basis.col[2]))>.01
frames.apply_reference(g,'ROTATION')
assert g.has_manual_basis
matrix_near(frames.frame_axes(g),basis)
# Oblique/Gimbal dimensions are projected extrema, including nonorthogonal axes.
target.better_item.reference_frame=g.uid
before=transform_view.dimensions(target,basis)
target.better_item.dimensions_x=before[0]*1.25
after=transform_view.dimensions(target,basis)
near(after,(before[0]*1.25,before[1],before[2]),tol=1e-4)
b.rotation_euler=(0,0,0);ctx.view_layer.update()
matrix_near(frames.frame_axes(g),basis)
# Native custom orientations not managed by this addon can be sources too.
with native_refs.view_context(ctx):
    bpy.ops.transform.create_orientation(name='External native',use_view=True,use=True)
custom=ctx.scene.transform_orientation_slots[0].custom_orientation
custom.matrix=Euler((.1,.2,.3)).to_matrix()
g.rotation_mode='NATIVE'
g.native_source=custom.name  # Explicit named source; no viewport capture action.
matrix_near(frames.frame_axes(g),custom.matrix)
ctx.scene.transform_orientation_slots[0].type='GLOBAL'
custom.matrix=Euler((.2,.4,.1)).to_matrix();native_refs.sync()
matrix_near(frames.frame_axes(g),custom.matrix)
# Consuming unified frame works for arrangement; separate old selectors ignored.
settings=ctx.scene.better_item
settings.arrange_reference_mode='FRAME';settings.arrange_reference_frame=f.uid;settings.reference='REFERENCE'
axes,origin,source=arrange.reference_frame(ctx)
matrix_near(axes,frames.frame_axes(f));near(origin,a.location);assert source==a
settings.arrange_reference_mode='INDIVIDUAL';settings.arrange_orientation='GLOBAL';settings.arrange_origin='CURSOR'
axes,origin,source=arrange.reference_frame(ctx)
matrix_near(axes,Matrix.Identity(3));near(origin,(7,8,9))
# Apply one channel never disconnects the other.
frames.apply_reference(f,'POSITION');assert f.rotation_source==b and f.rotation_mode=='OBJECT'
assert f.position_source is None and f.position_mode=='MANUAL'
# Old files migrate a single source into two independent pointers.
legacy=settings.frames.add();legacy.uid='legacy';legacy.name='Old frame';legacy.source=a
legacy['follow_position']=True;legacy['follow_rotation']=True
frames.migrate()
assert legacy.position_source==a and legacy.rotation_source==a and legacy.source is None
assert legacy.position_mode==legacy.rotation_mode=='OBJECT'
legacy.rotation_source=b
assert legacy.position_source==a
# Renaming an exported frame updates native dependencies, without moving targets.
g.native_source=f.native_name
old=f.native_name
f.name='Renamed Assembly'
native_refs.sync()
assert f.native_name!=old and g.native_source==f.native_name
matrix_near(frames.frame_axes(g),frames.frame_axes(f))
# Native creation and independent frame pointers participate in undo/redo.
ctx.preferences.edit.use_global_undo=True
bpy.ops.ed.undo_push(message='Before native frame')
bpy.ops.better_item.new_frame(frame_name='Undo Native')
undo_frame=settings.frames[-1];undo_uid=undo_frame.uid
native_refs.publish(ctx,undo_frame)
bpy.ops.ed.undo_push(message='After native frame')
bpy.ops.ed.undo()
assert not any(item.uid==undo_uid for item in ctx.scene.better_item.frames)
bpy.ops.ed.redo()
native_refs.sync()
assert native_refs.named(ctx.scene,frames.find(ctx.scene,undo_uid).native_name) is not None
# Undo replaces RNA wrappers: reacquire all persistent owners before continuing.
settings=ctx.scene.better_item
f=next(item for item in settings.frames if item.name=='Renamed Assembly')
g=next(item for item in settings.frames if item.name=='Native dependency')
target=bpy.data.objects['Target']
# Native entries, source pointers, frames and consumer modes survive fresh process.
settings.arrange_reference_mode='FRAME';settings.arrange_reference_frame=f.uid
target.better_item.reference_mode='FRAME';target.better_item.reference_frame=f.uid
root=Path(__file__).resolve().parents[2]/"src"
ctx.preferences.filepaths.file_preview_type='NONE'
with tempfile.TemporaryDirectory(dir=root) as temp:
    path=Path(temp)/'frames.blend';reader=Path(temp)/'reader.py'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    reader.write_text(f'''import sys
sys.path.insert(0,{str(root)!r})
import bpy,addon_utils
addon_utils.enable('better_item',default_set=True)
from better_item import frames,native_refs
bpy.ops.wm.open_mainfile(filepath={str(path)!r})
native_refs.sync()
f=frames.find(bpy.context.scene,{f.uid!r})
assert f.rotation_source.name=='Orientation source'
assert f.position_mode=='MANUAL'
assert native_refs.named(bpy.context.scene,f.native_name) is not None
assert bpy.data.objects['Target'].better_item.reference_frame==f.uid
assert bpy.context.scene.better_item.arrange_reference_frame==f.uid
legacy=frames.find(bpy.context.scene,'legacy')
assert legacy.position_source.name=='Location source'
assert legacy.rotation_source.name=='Orientation source'
print('FRESH FRAME SOURCES AND NATIVE ORIENTATIONS PASSED')
''',encoding='utf-8')
    result=subprocess.run([bpy.app.binary_path,'--background','--factory-startup','--python-exit-code','1','--python',str(reader)],capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
print('REFERENCE INTEGRATION PASSED: separate object channels, tabs, native G/R, native/frame cycles, missing sources, recovery, all builtin pivot/orientation types, Gimbal basis, external custom orientation, arrangement, migration and fresh-process persistence')
