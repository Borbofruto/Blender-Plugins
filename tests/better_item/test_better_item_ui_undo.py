import sys
from pathlib import Path
from types import SimpleNamespace
import bpy
import addon_utils

root=Path(__file__).resolve().parents[2]/"addons"
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
assert 'dimensions_x' in calls and 'rotation_mode' in calls and 'spacing' in calls

# No false claim of proportional Euler linkage for quaternion components.
cube.rotation_mode='QUATERNION'
before=tuple(cube.rotation_quaternion)
try:engine.edit_component(cube,'ROTATION',0,.2)
except BetterItemError as exc:assert 'Euler' in str(exc)
else:raise AssertionError('Quaternion component ratios are not Euler-angle ratios')
assert tuple(cube.rotation_quaternion)==before

# Driven values are never silently replaced by panel edits.
cube.rotation_mode='XYZ'
curve=cube.driver_add('location',0)
curve.driver.expression='2'
bpy.context.view_layer.update()
try:engine.edit_component(cube,'LOCATION',0,5)
except BetterItemError as exc:assert 'driver' in str(exc)
else:raise AssertionError('Must report a driven field')
cube.driver_remove('location',0)
print('UI/UNDO PASSED: native-owner proportional edits undo/redo; panel references/icons, Euler/quaternion/axis-angle layouts, driven fields protected.')
