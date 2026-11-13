import sys,itertools,math,tempfile,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils,numpy as np
from mathutils import Matrix,Euler,Vector
addon_utils.enable('better_item',default_set=True)
from better_item import references,frames,native_refs,arrange,engine
from better_item.math_core import BetterItemError
ctx=bpy.context
def near(a,b):assert np.allclose(a,b,rtol=1e-6,atol=3e-5),(a,b)
def empty(name):
    obj=bpy.data.objects.new(name,None);ctx.scene.collection.objects.link(obj);return obj
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
obj=empty('Target');obj.location=(4,5,6);obj.rotation_euler=(.1,.2,.3)
source=empty('Source');source.location=(7,8,9);source.rotation_euler=(.3,.2,.1)
obj.select_set(True);source.select_set(True);ctx.view_layer.objects.active=obj
ctx.view_layer.update()
f=frames.create(ctx,'Axes and origin',Vector((1,2,3)),Euler((.2,.3,.4)).to_matrix())
o=obj.better_item;s=ctx.scene.better_item
s['reference_schema']=2
o.orientation_object=s.arrange_object=source
o.origin_object=s.arrange_origin_object=source
o.orientation_frame=s.arrange_frame=f.uid
o.pivot_frame=s.arrange_origin_frame=f.uid
o.reference_frame=s.arrange_reference_frame=f.uid
ctx.scene.cursor.location=(10,20,30);ctx.scene.cursor.rotation_euler=(.4,.1,.2)
with native_refs.view_context(ctx):
    bpy.ops.transform.create_orientation(name='External parity',use_view=True,use=True)
    ctx.scene.transform_orientation_slots[0].custom_orientation.matrix=Euler((.2,.4,.6)).to_matrix()
o.reference_native=s.reference_native='External parity'
native_refs.sync()
checks=0
for axes,loc in itertools.product(references.ORIENTATIONS,references.LOCATIONS):
    o.reference_orientation=s.reference_orientation=axes[0]
    o.reference_location=s.reference_location=loc[0]
    o.reference_pivot=s.reference_pivot='BOUNDING_BOX_CENTER'
    near(frames.object_axes(ctx,obj),arrange.reference_frame(ctx,'REFERENCE')[0])
    near(frames.object_origin(ctx,obj),arrange.reference_frame(ctx,'REFERENCE')[1])
    checks+=1
for pivot in native_refs.PIVOTS:
    o.reference_location=s.reference_location='PIVOT'
    o.reference_pivot=s.reference_pivot=pivot[0]
    near(frames.object_origin(ctx,obj),arrange.reference_frame(ctx,'REFERENCE')[1])
o.reference_mode=s.arrange_reference_mode='FRAME'
near(frames.object_axes(ctx,obj),arrange.reference_frame(ctx,'REFERENCE')[0])
near(frames.object_origin(ctx,obj),arrange.reference_frame(ctx,'REFERENCE')[1])
# World origin is a first-class independent frame Location source.
f.position=(123,456,789);f.position_mode='GLOBAL'
near(frames.frame_origin(f),(0,0,0))
near(frames.object_origin(ctx,obj),(0,0,0))
# Removing an intermediate frame preserves later serials and enum selections.
middle=frames.create(ctx,'Remove middle',Vector(),Matrix.Identity(3))
last=frames.create(ctx,'Survivor',Vector(),Matrix.Identity(3))
uid=last.uid;number=last.number
o.reference_frame=s.arrange_reference_frame=uid
assert o.get('reference_frame')==s.get('arrange_reference_frame')==number
s.active_frame=next(i for i,frame in enumerate(s.frames) if frame.uid==middle.uid)
bpy.ops.better_item.frame(action='REMOVE')
assert o.reference_frame==s.arrange_reference_frame==uid
assert o.get('reference_frame')==number
# Collection removal invalidates cached RNA wrappers; reacquire by stable UID.
last=frames.find(ctx.scene,uid)
# Native menu deletion disables only the export, never deletes the scene frame.
s.active_frame=next(i for i,frame in enumerate(s.frames) if frame.uid==uid)
native_refs.publish(ctx,last,select=True);name=last.native_name;count=len(s.frames)
with native_refs.view_context(ctx):bpy.ops.transform.delete_orientation()
native_refs.sync()
assert not last.native_enabled and not last.native_name
assert native_refs.named(ctx.scene,name) is None and len(s.frames)==count
native_refs.sync();assert native_refs.named(ctx.scene,name) is None
native_refs.publish(ctx,last);assert last.native_enabled
# Native Normal is sampled once per unchanged selection; changed selection
# resamples and does not overwrite any preexisting custom orientation.
bpy.ops.mesh.primitive_cube_add()
cube=ctx.object;cube.better_item.orientation='NORMAL'
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT')
import bmesh
mesh=bmesh.from_edit_mesh(cube.data);mesh.faces.ensure_lookup_table();mesh.faces[0].select_set(True);bmesh.update_edit_mesh(cube.data)
old_uuid=native_refs.uuid.uuid4;calls=[]
def counted_uuid():calls.append(1);return old_uuid()
native_refs.uuid.uuid4=counted_uuid
try:
    native_refs.sync();first=len(calls)
    assert first==1,first
    for _ in range(5):native_refs.sync()
    assert len(calls)==first,(len(calls),first)
    mesh.faces[0].select_set(False);mesh.faces[1].select_set(True);bmesh.update_edit_mesh(cube.data)
    native_refs.sync();assert len(calls)==first+1
finally:native_refs.uuid.uuid4=old_uuid
bpy.ops.object.mode_set(mode='OBJECT')
# Owner-scene lookups and legacy Match Axes migration must not depend on the
# currently displayed scene. Dynamic enum raw storage remains an integer.
legacy_scene=bpy.data.scenes.new('Legacy inactive scene')
with ctx.temp_override(scene=legacy_scene):
    legacy_frame=frames.create(ctx,'Legacy source',Vector((3,4,5)),Matrix.Identity(3))
    legacy_uid=legacy_frame.uid
    dependent=frames.create(ctx,'Legacy child',Vector(),Matrix.Identity(3))
    dependent.position_mode='FRAME';dependent.position_frame=legacy_uid
legacy=legacy_scene.better_item
legacy.arrange_orientation='SAVED';legacy.arrange_frame=legacy_uid
legacy['arrange_origin']=0
references.migrate(legacy_scene)
assert legacy.arrange_origin=='SAVED' and legacy.arrange_origin_frame==legacy_uid
near(frames.frame_origin(dependent),(3,4,5))
# New pivot/native choices, and World origins in scene frames, survive a new
# Blender process without existing enum/native caches.
o.reference_mode=s.arrange_reference_mode='INDIVIDUAL'
o.reference_orientation='NATIVE';o.reference_native='External parity'
o.reference_location='PIVOT';o.reference_pivot='BOUNDING_BOX_CENTER'
s.reference_orientation='CURSOR';s.reference_location='FRAME'
s.arrange_origin_frame=next(frame.uid for frame in s.frames if frame.name=='Axes and origin')
root=Path(__file__).resolve().parents[2]/"src"
ctx.preferences.filepaths.file_preview_type='NONE'
with tempfile.TemporaryDirectory(dir=root) as temp:
    path=Path(temp)/'references.blend';reader=Path(temp)/'read.py'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    reader.write_text(f'''import sys
sys.path.insert(0,{str(root)!r})
import bpy,addon_utils
addon_utils.enable('better_item',default_set=True)
from better_item import frames,native_refs
bpy.ops.wm.open_mainfile(filepath={str(path)!r})
native_refs.sync()
o=bpy.data.objects['Target'].better_item
s=bpy.context.scene.better_item
assert o.reference_orientation=='NATIVE' and o.reference_native=='External parity'
assert o.reference_location=='PIVOT' and o.reference_pivot=='BOUNDING_BOX_CENTER'
assert s.reference_orientation=='CURSOR' and s.reference_location=='FRAME'
f=frames.find(bpy.context.scene,s.arrange_origin_frame)
assert f.position_mode=='GLOBAL' and tuple(frames.frame_origin(f))==(0,0,0)
''',encoding='utf-8')
    result=subprocess.run([bpy.app.binary_path,'--background','--factory-startup','--python-exit-code','1','--python',str(reader)],capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
print('REFERENCE PARITY PASSED: %d identical Individual combinations, all pivots, full frame, World origin, stable enum gap, external native deletion and Normal sample invalidation'%checks)




