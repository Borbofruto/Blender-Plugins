"""Public operator kwargs, real repeat-last/Undo and method-specific Placement.

Run in a real GUI through compatibility/run_matrix.py (gui_sync). The tetrahedron
has analytically different bounds, surface and volume centers, all off-origin.
"""
import sys
import json
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
import bpy
import addon_utils
import numpy as np

addon_utils.enable('better_item')
from better_item import placement

ctx = bpy.context
checks = []
cases = []
POINTS = {
    'ORIGINS': np.zeros(3),
    'BOUNDS_CENTER': np.array((2., 1., 3.)),
    'SURFACE': np.array((10/9, 4/9, 16/9)),
    'VOLUME': np.array((1., .5, 1.5)),
}
IDS = {'ORIGINS': 0, 'GEOMETRY': 1, 'BOUNDS_CENTER': 2, 'SURFACE': 3, 'VOLUME': 4}


def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    s = ctx.scene.better_item
    s.arrange_reference_mode = 'INDIVIDUAL'
    s.arrange_origin = 'GLOBAL'
    s.arrange_orientation = 'GLOBAL'
    s.distribution_start_override = False
    s.distribution_end.mode = 'MANUAL'
    s.distribution_end.position = (30, 0, 0)
    s.distribution_legacy_range = False
    objects = []
    shifts = []
    for i in range(3):
        shift = np.array((1 + i, 2 + i, -1 - i), dtype=float)
        vertices = np.array(((0, 0, 0), (4, 0, 0), (0, 2, 0), (0, 0, 6))) + shift
        mesh = bpy.data.meshes.new('Operator tetrahedron')
        mesh.from_pydata(vertices.tolist(), [], [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)])
        obj = bpy.data.objects.new('Operator piece ' + str(i), mesh)
        ctx.scene.collection.objects.link(obj)
        obj.location = (3 + 8*i, 2 + i, 1)
        objects.append(obj)
        shifts.append(shift)
    for obj in objects:
        obj.select_set(True)
    ctx.view_layer.objects.active = objects[0]
    ctx.view_layer.update()
    return s, objects, shifts


def positions(objects):
    ctx.view_layer.update()
    return np.array([tuple(obj.matrix_world.translation) for obj in objects])


def invariant(objects):
    return [(obj.data.as_pointer(), tuple(tuple(v.co) for v in obj.data.vertices),
             tuple(obj.scale), tuple(obj.rotation_euler), tuple(obj.delta_location),
             tuple(obj.delta_scale), obj.select_get()) for obj in objects]


def assert_endpoint(objects, shifts, basis):
    offsets = np.zeros((3, 3)) if basis == 'ORIGINS' else np.array(shifts) + POINTS[basis]
    expected = np.array(((0, 0, 0), (15, 0, 0), (30, 0, 0))) - offsets
    assert np.allclose(positions(objects), expected, rtol=0, atol=8e-6), (basis, positions(objects), expected)


# Keyword order must not affect the public Python API. Exercise both paths.
for path in ('SEGMENT', 'AXIS'):
    for basis in POINTS:
        for method_first in (True, False):
            s, objects, shifts = reset()
            before = invariant(objects)
            scene_choices = (s.distribution_method, s.distribution_mode)
            kwargs = dict(method='ENDPOINT', distribution_mode=basis) if method_first else dict(distribution_mode=basis, method='ENDPOINT')
            status = bpy.ops.better_item.distribute(**kwargs, path=path, axes=(True, False, False))
            assert status == {'FINISHED'}, (basis, status)
            assert_endpoint(objects, shifts, basis)
            assert invariant(objects) == before
            assert ctx.active_object == objects[0]
            assert scene_choices == (s.distribution_method, s.distribution_mode)
            cases.append(dict(method='ENDPOINT', path=path, basis=basis, method_first=method_first))
checks.append('16 direct Endpoint calls: independent analytic centers, both keyword orders and paths')

# GEOMETRY must be rejected at argument conversion, without executing/moving.
for method_first in (True, False):
    s, objects, shifts = reset()
    before = positions(objects).copy(), invariant(objects)
    kwargs = dict(method='ENDPOINT', distribution_mode='GEOMETRY') if method_first else dict(distribution_mode='GEOMETRY', method='ENDPOINT')
    try:
        bpy.ops.better_item.distribute(**kwargs)
    except TypeError as exc:
        assert 'GEOMETRY' in str(exc)
    else:
        raise AssertionError('Endpoint accepted Geometry Bounds')
    assert np.array_equal(positions(objects), before[0]) and invariant(objects) == before[1]
checks.append('invalid Endpoint Geometry rejects both keyword orders atomically')

# Offset keeps its five valid choices and preserves transverse coordinates.
for basis in (*POINTS, 'GEOMETRY'):
    for method_first in (True, False):
        s, objects, shifts = reset()
        before, data = positions(objects).copy(), invariant(objects)
        kwargs = dict(method='OFFSET', distribution_mode=basis) if method_first else dict(distribution_mode=basis, method='OFFSET')
        assert bpy.ops.better_item.distribute(**kwargs, modern=True, spacing=10, axes=(True, False, False)) == {'FINISHED'}
        actual = positions(objects)
        assert np.array_equal(actual[:, 1:], before[:, 1:])
        if basis == 'GEOMETRY':
            # Each translated tetrahedron occupies [shift.x, shift.x+4].
            expected_x = np.arange(1, 4)*10 + np.arange(3)*4 - np.array(shifts)[:, 0]
        else:
            offsets_x = np.zeros(3) if basis == 'ORIGINS' else np.array(shifts)[:, 0] + POINTS[basis][0]
            expected_x = np.arange(1, 4)*10 - offsets_x
        assert np.allclose(actual[:, 0], expected_x, rtol=0, atol=8e-6), (basis, actual, expected_x)
        assert invariant(objects) == data
        cases.append(dict(method='OFFSET', basis=basis, method_first=method_first))
checks.append('10 direct Offset calls including Geometry; transverse axes and native data preserved')

# Stable numeric enum IDs and legacy Scene migration remain unchanged.
assert {item[0]: item[-1] for item in placement.OFFSET_ITEMS} == IDS
s, objects, shifts = reset()
for key in ('placement_schema', 'offset_placement_value', 'endpoint_placement_value'):
    if key in s:
        del s[key]
s.distribution_method = 'ENDPOINT'
s['distribution_mode'] = 1
placement.migrate(s)
assert s.distribution_mode == 'ORIGINS' and s['placement_migration_notice']
s.distribution_method = 'OFFSET'
assert s.distribution_mode == 'GEOMETRY'
checks.append('saved numeric IDs and legacy Geometry migration/notice preserved')

# Native invoke copies Scene choices; repeat-last is Blender's EXEC redo path.
ctx.preferences.edit.use_global_undo = True
s.distribution_method = 'ENDPOINT'
s.distribution_mode = 'VOLUME'
bpy.ops.ed.undo_push(message='Before Endpoint operator regression')
initial = positions(objects).copy()
assert bpy.ops.better_item.distribute('INVOKE_DEFAULT', True) == {'FINISHED'}
assert_endpoint(objects, shifts, 'VOLUME')
after_invoke = positions(objects).copy()
assert bpy.ops.ed.undo() == {'FINISHED'}
objects = [bpy.data.objects['Operator piece ' + str(i)] for i in range(3)]
assert np.allclose(positions(objects), initial)
assert bpy.ops.ed.redo() == {'FINISHED'}
objects = [bpy.data.objects['Operator piece ' + str(i)] for i in range(3)]
assert np.allclose(positions(objects), after_invoke)
# Undo/Redo can clear window_manager.operators in a scripted GUI context.
# Start a fresh registered invoke before checking the editable redo properties.
assert bpy.ops.better_item.distribute('INVOKE_DEFAULT', True) == {'FINISHED'}
assert_endpoint(objects, shifts, 'VOLUME')
op = ctx.window_manager.operators[-1]
assert op.bl_idname == 'BETTER_ITEM_OT_distribute'
assert op.endpoint_placement == 4 and op.offset_placement == 1
op.method = 'OFFSET'
assert op.distribution_mode == 'GEOMETRY'
op.distribution_mode = 'BOUNDS_CENTER'
op.method = 'ENDPOINT'
assert op.distribution_mode == 'VOLUME'
op.distribution_mode = 'SURFACE'
op.method = 'OFFSET'
assert op.distribution_mode == 'BOUNDS_CENTER'
op.method = 'ENDPOINT'
# This screen wrapper deliberately returns CANCELLED after repeating the inner
# operator. Its return status is not the distribution's acceptance oracle.
bpy.ops.screen.repeat_last()
objects = [bpy.data.objects['Operator piece ' + str(i)] for i in range(3)]
assert_endpoint(objects, shifts, 'SURFACE')
checks.append('native invoke and real Undo/Redo; F9 property memory; repeat-last applies Surface')

result = dict(passed=True, blender=bpy.app.version_string, module=__import__('better_item').__file__,
              cases=cases, checks=checks)
Path(__file__).with_suffix('.results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print('177 OPERATOR PASSED', json.dumps(result))
