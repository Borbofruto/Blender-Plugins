import sys
from pathlib import Path
from types import SimpleNamespace
import bpy
import addon_utils

root=Path(__file__).resolve().parents[2]/"src"
sys.path.insert(0,str(root))
addon_utils.enable('better_item',default_set=True)
import better_item as addon
from better_item.math_core import BetterItemError
from better_item import engine

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=1)
cube=bpy.context.object
cube.name='UndoCube'
cube.dimensions=(.1,.2,.6)
cube.better_item.link_dimensions=(True,True,True)
bpy.context.view_layer.update()
bpy.context.preferences.edit.use_global_undo=True
assert bpy.ops.ed.undo_push(message='Before Better Item')=={'FINISHED'}
cube.better_item.dimensions_x=.3
assert abs(cube.dimensions.z-1.8)<1e-5
assert bpy.ops.ed.undo_push(message='After Better Item')=={'FINISHED'}
assert bpy.ops.ed.undo()=={'FINISHED'}
cube=bpy.data.objects['UndoCube']
assert abs(cube.dimensions.z-.6)<1e-5,tuple(cube.dimensions)
assert bpy.ops.ed.redo()=={'FINISHED'}
cube=bpy.data.objects['UndoCube']
assert abs(cube.dimensions.z-1.8)<1e-5,tuple(cube.dimensions)

# Validate all panel property references, operator IDs and icon enum names.
icons=bpy.types.UILayout.bl_rna.functions['prop'].parameters['icon'].enum_items.keys()
calls=[]
class Layout:
    def box(self):return self
    def row(self,**kwargs):return self
    def column(self,**kwargs):return self
    def template_list(self,listtype,listid,data,propname,active_data,active_propname,**kwargs):
        assert propname in data.bl_rna.properties
        assert active_propname in active_data.bl_rna.properties
    def prop(self,owner,name,**kwargs):
        assert name in owner.bl_rna.properties,(type(owner),name)
        if 'index' in kwargs:assert 0<=kwargs['index']<len(getattr(owner,name))
        if 'icon' in kwargs:assert kwargs['icon'] in icons,kwargs['icon']
        getattr(owner,name)
        calls.append(name)
    def prop_decorator(self,owner,name,**kwargs):
        assert name in owner.bl_rna.properties
        assert owner.bl_rna.properties[name].is_animatable
    def label(self,**kwargs):
        if 'icon' in kwargs:assert kwargs['icon'] in icons,kwargs['icon']
    def operator(self,name,**kwargs):
        namespace,method=name.split('.')
        getattr(getattr(bpy.ops,namespace),method).get_rna_type()
        if 'icon' in kwargs:assert kwargs['icon'] in icons,kwargs['icon']
        return SimpleNamespace()

context=SimpleNamespace(mode='OBJECT',active_object=cube,scene=bpy.context.scene,region=SimpleNamespace(width=320))
for mode in ('XYZ','ZYX','QUATERNION','AXIS_ANGLE'):
    cube.rotation_mode=mode
    addon.BETTERITEM_PT_transform.draw(SimpleNamespace(layout=Layout()),context)
for reference in ('SELECTION','KEY'):
    context.scene.better_item.reference=reference
    addon.BETTERITEM_PT_alignment.draw(SimpleNamespace(layout=Layout()),context)
assert 'dimensions_x' in calls and 'view_rotation_order' in calls and 'spacing' in calls

from better_item import frames
from mathutils import Matrix,Vector
reference=frames.create(bpy.context,'UI frame',Vector((1,2,3)),Matrix.Identity(3))
cube.better_item.orientation='SAVED'
cube.better_item.orientation_frame=reference.uid
cube.better_item.pivot_mode='FRAME'
cube.better_item.pivot_frame=reference.uid
addon.BETTERITEM_PT_transform.draw(SimpleNamespace(layout=Layout()),context)
frames.BETTERITEM_PT_frames.draw(SimpleNamespace(layout=Layout()),context)
assert 'orientation_frame' in calls and 'pivot_frame' in calls and 'position_x' in calls
scene_settings=bpy.context.scene.better_item
scene_settings.reference='REFERENCE'
scene_settings.arrange_orientation='SAVED'
scene_settings.arrange_frame=reference.uid
scene_settings.arrange_origin='SAVED'
scene_settings.arrange_origin_frame=reference.uid
addon.BETTERITEM_PT_alignment.draw(SimpleNamespace(layout=Layout()),context)
assert 'arrange_frame' in calls and 'arrange_origin_frame' in calls and 'minimum_distance_mm' in calls


# The reference-space Euler view can edit a quaternion-backed object.
cube.rotation_mode='QUATERNION'
cube.better_item.rotation_x=.2
assert abs(cube.better_item.rotation_x-.2)<1e-5

# Driven values are never silently replaced by panel edits.
cube.rotation_mode='XYZ'
curve=cube.driver_add('scale',0)
curve.driver.expression='2'
bpy.context.view_layer.update()
try:engine.edit_scale_component(cube,0,5)
except BetterItemError as exc:assert 'driver' in str(exc)
else:raise AssertionError('Must report a driven field')
cube.driver_remove('scale',0)
assert not hasattr(bpy.types,'BETTERITEM_PT_native')
assert not hasattr(bpy.types,'BETTERITEM_PT_incremental')
print('UI/UNDO PASSED: native-owner proportional edits undo/redo; panel references/icons, Euler/quaternion/axis-angle layouts, driven fields protected.')
# Reference creation and its enum identity participate in undo/redo.
bpy.context.preferences.edit.use_global_undo=True
count_before=len(bpy.context.scene.better_item.frames)
bpy.ops.ed.undo_push(message='Before saved reference')
undo_frame=frames.create(bpy.context,'Undo reference',Vector((4,5,6)),Matrix.Identity(3))
undo_uid=undo_frame.uid
bpy.ops.ed.undo_push(message='After saved reference')
bpy.ops.ed.undo()
assert len(bpy.context.scene.better_item.frames)==count_before
bpy.ops.ed.redo()
assert frames.find(bpy.context.scene,undo_uid).name=='Undo reference'
print('REFERENCE UNDO/REDO PASSED')

# 1.4.2: both panels expose the same coordinate system in every operation.
settings=bpy.context.scene.better_item
context=SimpleNamespace(mode='OBJECT',active_object=bpy.context.active_object,scene=bpy.context.scene,region=SimpleNamespace(width=320))
settings.arrange_reference_mode='INDIVIDUAL'
for mode in ('SELECTION','KEY','REFERENCE'):
    settings.reference=mode
    calls.clear()
    addon.BETTERITEM_PT_alignment.draw(SimpleNamespace(layout=Layout()),context)
    assert 'reference_location' in calls and 'reference_orientation' in calls,(mode,calls)
print('SHARED REFERENCE UI VISIBILITY PASSED')
