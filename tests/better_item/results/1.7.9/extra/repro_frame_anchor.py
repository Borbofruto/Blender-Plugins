"""Hypothesis: the linked-edit anchor key ignores the reference orientation.

Drag linked X/Y to zero in Global, switch the object's orientation to a frame
rotated 90 deg about Z (same origin), then type X=1. Report what happens.
Run with cwd/sys.path pointing at a frozen better_item package.
"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
from mathutils import Matrix, Vector
import better_item
if not hasattr(bpy.types.Object, 'better_item'):
    better_item.register()
from better_item import transform_view as tv, frames
from better_item.math_core import BetterItemError

ctx = bpy.context
bpy.ops.wm.read_factory_settings(use_empty=True)
if not hasattr(bpy.types.Object, 'better_item'):
    better_item.register()
tv.clear_cache()
obj = bpy.data.objects.new('o', None)
ctx.scene.collection.objects.link(obj)
obj.location = (1, 2, 3)
ctx.view_layer.update()
ctx.view_layer.objects.active = obj
obj.select_set(True)
s = obj.better_item
s.transform_space = 'REFERENCE'
s.reference_mode = 'INDIVIDUAL'
s.pivot_mode = 'GLOBAL'
s.use_reference_pivot = False
s.orientation = 'GLOBAL'
s.link_location = (True, True, False)
print('version', better_item.__file__)
for value in (.5, 0.):
    tv.edit_component(ctx, obj, 'LOCATION', 0, value)
print('after drag in Global: world', tuple(obj.location), 'values', tuple(tv.values(ctx, obj, 'LOCATION')))
frame = frames.create(ctx, 'Rz90', Vector(), Matrix.Rotation(math.radians(90), 3, 'Z'))
s.orientation = 'SAVED'
s.orientation_frame = frame.uid
ctx.view_layer.update()
print('values in Rz90 frame', tuple(tv.values(ctx, obj, 'LOCATION')))
try:
    tv.edit_component(ctx, obj, 'LOCATION', 0, 1.)
    print('RESULT edit X=1 accepted: world', tuple(round(v, 6) for v in obj.location),
          'values', tuple(round(v, 6) for v in tv.values(ctx, obj, 'LOCATION')))
except BetterItemError as exc:
    print('RESULT edit X=1 refused:', exc)
