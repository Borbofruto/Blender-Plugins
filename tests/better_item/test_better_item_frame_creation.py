import sys,math,tempfile,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
import bpy,addon_utils
from mathutils import Vector,Euler
addon_utils.enable('better_item',default_set=True)
from better_item import frames
context=bpy.context

def near(a,b):assert all(abs(x-y)<1e-5 for x,y in zip(a,b)),(tuple(a),tuple(b))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=1)
target=context.object
target.name='Target'
original=target.matrix_world.copy()
bpy.ops.object.empty_add()
source=context.object
source.name='Source'
source.location=(10,20,30)
source.rotation_euler=(.2,.3,.4)
source.scale=(2,3,4)
context.view_layer.objects.active=target
context.view_layer.update()
# A manual frame is created and immediately selected for the requested field.
assert bpy.ops.better_item.new_frame(target='AXES',target_name='Target',frame_name='Manual')=={'FINISHED'}
manual=context.scene.better_item.frames[-1]
manual_uid=manual.uid
manual.position=(1,2,3)
manual.rotation=(.1,.2,.3)
near(manual.position,(1,2,3))
assert target.better_item.orientation=='SAVED' and target.better_item.orientation_frame==manual_uid
assert target.better_item.pivot_mode=='GLOBAL'
# An independent object copy does not keep a source pointer.
assert bpy.ops.better_item.new_frame(target='ORIGIN',target_name='Target',frame_name='Independent')=={'FINISHED'}
independent=context.scene.better_item.frames[-1]
independent_uid=independent.uid
independent.position_mode=independent.rotation_mode='OBJECT'
independent.position_source=independent.rotation_source=source
frames.apply_reference(independent)
assert independent.source is None
assert not independent.link_position and not independent.link_rotation
near(independent.position,(10,20,30))
assert target.better_item.pivot_frame==independent_uid
assert target.better_item.orientation_frame==manual_uid
assert not hasattr(context.scene.better_item,'frame_create_source')
# A linked source remains separate from the selected target.
assert bpy.ops.better_item.new_frame(target='AXES',target_name='Target',frame_name='Linked')=={'FINISHED'}
linked=context.scene.better_item.frames[-1]
linked_uid=linked.uid
linked.position_mode=linked.rotation_mode='OBJECT'
linked.position_source=linked.rotation_source=source
assert linked.position_source==source and linked.rotation_source==source and linked.link_position and linked.link_rotation
assert target.better_item.orientation_frame==linked_uid
source.location=(40,50,60)
source.rotation_euler=(.5,.6,.7)
context.view_layer.update()
near(frames.resolve(linked)[0],(40,50,60))
near(frames.resolve(independent)[0],(10,20,30))
near(target.matrix_world.translation,original.translation)
assert target.parent is None and not target.constraints
# A failed creation cannot leave a partially created frame.
count=len(context.scene.better_item.frames)
try:bpy.ops.better_item.new_frame(target='AXES',target_name='Missing target')
except RuntimeError:pass
assert len(context.scene.better_item.frames)==count
# Save and reopen in a NEW Blender process: no existing Python enum cache.
context.preferences.filepaths.file_preview_type='NONE'
root=Path(__file__).resolve().parents[2]/"src"
with tempfile.TemporaryDirectory(dir=root) as temp:
    filepath=Path(temp)/'saved_frames.blend'
    reader=Path(temp)/'read_frames.py'
    bpy.ops.wm.save_as_mainfile(filepath=str(filepath))
    reader.write_text('''import sys
from pathlib import Path
sys.path.insert(0,ROOT)
import bpy,addon_utils
addon_utils.enable('better_item',default_set=True)
from better_item import frames
bpy.ops.wm.open_mainfile(filepath=FILEPATH)
scene=bpy.context.scene
target=bpy.data.objects['Target']
source=bpy.data.objects['Source']
assert len(scene.better_item.frames)==3
assert target.better_item.orientation_frame==LINKED_UID
assert target.better_item.pivot_frame==INDEPENDENT_UID
items=frames.frame_items(None,bpy.context)
assert {item[1] for item in items}=={'Choose a Frame','Manual','Independent','Linked'}
manual=frames.find(scene,MANUAL_UID)
independent=frames.find(scene,INDEPENDENT_UID)
linked=frames.find(scene,LINKED_UID)
assert tuple(manual.position)==(1,2,3)
assert tuple(independent.position)==(10,20,30)
assert linked.position_source==source and linked.rotation_source==source and linked.link_position and linked.link_rotation
assert not hasattr(scene.better_item,'frame_create_source')
source.location=(70,80,90)
bpy.context.view_layer.update()
assert tuple(frames.resolve(linked)[0])==(70,80,90)
assert tuple(frames.resolve(independent)[0])==(10,20,30)
assert tuple(target.matrix_world.translation)==(0,0,0)
bpy.data.objects.remove(source,do_unlink=True)
bpy.context.view_layer.update()
assert tuple(frames.resolve(independent)[0])==(10,20,30)
assert independent.source is None
print('FRESH PROCESS SCENE PERSISTENCE PASSED')
'''.replace('ROOT',repr(str(root))).replace('FILEPATH',repr(str(filepath)))
        .replace('LINKED_UID',repr(linked_uid)).replace('INDEPENDENT_UID',repr(independent_uid)).replace('MANUAL_UID',repr(manual_uid)),encoding='utf-8')
    result=subprocess.run([bpy.app.binary_path,'--background','--factory-startup','--disable-autoexec',
        '--python-exit-code','1','--python',str(reader)],capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    assert 'FRESH PROCESS SCENE PERSISTENCE PASSED' in result.stdout,result.stdout
print('INLINE FRAME CREATION PASSED: name-only dialog, independent component sources, apply and auto-selection and .blend persistence in a fresh process')

