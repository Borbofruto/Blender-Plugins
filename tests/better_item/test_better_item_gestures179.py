"""Linked-edit gestures, instancer lookup and Normal selection fingerprint (1.7.9).

Each case was reproduced against 1.7.8 first:
- a 400-tick linked drag lost ~6e-6 of the ratio through float32 read-back;
- crossing zero collapsed every linked axis and every later tick raised BI-T008;
- Normal selection fingerprints walked every element on every 0.2 s tick.

Headless-safe: no Undo, no mouse. Counters and exact oracles, no timings.
"""
import sys
import math
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
import bpy
import bmesh

try:
    import addon_utils
    addon_utils.enable('better_item')
except Exception:
    pass
import better_item
if not hasattr(bpy.types.Object, 'better_item'):
    better_item.register()
from better_item import transform_view as tv, native_refs, engine, math_core
from better_item.math_core import BetterItemError

ctx = bpy.context
results = {}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if not hasattr(bpy.types.Object, 'better_item'):
        better_item.register()
    tv.clear_cache()


def empty(location=(1, 2, 3)):
    obj = bpy.data.objects.new('o', None)
    ctx.scene.collection.objects.link(obj)
    obj.location = location
    ctx.view_layer.update()
    ctx.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def edit(obj, group, axis, value):
    try:
        tv.edit_component(ctx, obj, group, axis, value)
        return None
    except BetterItemError as exc:
        return str(exc)


def current(obj, group):
    return tuple(tv.values(ctx, obj, group))


def linked(obj, group, space):
    obj.better_item.transform_space = space
    setattr(obj.better_item, engine.GROUP_LINK[group], (True, True, True))


def drag_ratio():
    for space in ('REFERENCE', 'DEFAULT'):
        reset()
        obj = empty()
        linked(obj, 'LOCATION', space)
        for k in range(1, 401):
            assert edit(obj, 'LOCATION', 0, 1 + 4 * k / 400) is None
        x, y, z = current(obj, 'LOCATION')
        assert abs(y / x - 2) < 1e-9 and abs(z / x - 3) < 1e-9, (space, x, y, z)
    reset()
    obj = empty()
    obj.scale = (1, 2, 3)
    linked(obj, 'SCALE', 'DEFAULT')
    for k in range(1, 401):
        assert edit(obj, 'SCALE', 0, 1 + 4 * k / 400) is None
    x, y, z = tuple(obj.scale)
    assert abs(y / x - 2) < 1e-9 and abs(z / x - 3) < 1e-9, (x, y, z)
    results['drag_ratio'] = 'Location (Reference and Default) and Scale keep exact ratios over a 400-tick drag'


def cross_zero():
    reset()
    obj = empty()
    linked(obj, 'LOCATION', 'REFERENCE')
    for value in (.5, .05, 0., -.05, -.5, -1.):
        assert edit(obj, 'LOCATION', 0, value) is None, value
    assert current(obj, 'LOCATION') == (-1., -2., -3.), current(obj, 'LOCATION')
    reset()
    obj = empty(location=(0, 0, 0))
    obj.rotation_euler = tuple(math.radians(v) for v in (10, 20, 30))
    ctx.view_layer.update()
    linked(obj, 'ROTATION', 'REFERENCE')
    for degrees in (5, 0, -2, -5):
        assert edit(obj, 'ROTATION', 0, math.radians(degrees)) is None, degrees
    got = tuple(round(math.degrees(v), 6) for v in current(obj, 'ROTATION'))
    assert got == (-5., -10., -15.), got
    reset()
    obj = empty()
    obj.scale = (1, 2, 3)
    linked(obj, 'SCALE', 'DEFAULT')
    for value in (.5, 0., -.5):
        assert edit(obj, 'SCALE', 0, value) is None, value
    assert tuple(obj.scale) == (-.5, -1., -1.5), tuple(obj.scale)
    results['cross_zero'] = 'Location, Rotation and Scale continue through zero with the original ratio'


def outside_changes_win():
    reset()
    obj = empty()
    linked(obj, 'LOCATION', 'DEFAULT')
    assert edit(obj, 'LOCATION', 0, 0.) is None
    assert tuple(obj.location) == (0., 0., 0.)
    obj.location = (0., 0., 7.)
    ctx.view_layer.update()
    message = edit(obj, 'LOCATION', 0, 2.)
    assert message and 'BI-T008' in message, message
    assert tuple(obj.location) == (0., 0., 7.), tuple(obj.location)
    reset()
    obj = empty()
    linked(obj, 'LOCATION', 'DEFAULT')
    assert edit(obj, 'LOCATION', 0, 2.) is None
    obj.location = (5., 5., 5.)
    ctx.view_layer.update()
    assert edit(obj, 'LOCATION', 0, 10.) is None
    assert tuple(obj.location) == (10., 10., 10.), tuple(obj.location)
    obj.better_item.link_location = (True, False, False)
    assert edit(obj, 'LOCATION', 0, 3.) is None
    assert tuple(obj.location) == (3., 10., 10.), tuple(obj.location)
    results['outside_changes_win'] = 'a value changed outside the gesture, or a link change, discards the remembered ratio'


def reference_switch():
    from mathutils import Matrix, Vector
    from better_item import frames
    reset()
    obj = empty()
    s = obj.better_item
    s.transform_space = 'REFERENCE'
    s.reference_mode = 'INDIVIDUAL'
    s.pivot_mode = 'GLOBAL'
    s.use_reference_pivot = False
    s.orientation = 'GLOBAL'
    s.link_location = (True, True, False)
    for value in (.5, 0.):
        assert edit(obj, 'LOCATION', 0, value) is None, value
    assert tuple(obj.location) == (0., 0., 3.), tuple(obj.location)
    frame = frames.create(ctx, 'Rz90', Vector(), Matrix.Rotation(math.radians(90), 3, 'Z'))
    s.orientation = 'SAVED'
    s.orientation_frame = frame.uid
    ctx.view_layer.update()
    assert current(obj, 'LOCATION') == (0., 0., 3.), current(obj, 'LOCATION')
    # The ratio was measured in Global; it must not be reused in another reference.
    message = edit(obj, 'LOCATION', 0, 1.)
    assert message and 'BI-T008' in message, message
    assert tuple(obj.location) == (0., 0., 3.), tuple(obj.location)
    # A fixed Frame reference keeps the gesture continuity through zero.
    # The stored Frame rotation is float32, so frame coordinates are inexact.
    obj.location = (-2., 1., 3.)
    ctx.view_layer.update()
    x0, y0, z0 = current(obj, 'LOCATION')
    assert abs(x0 - 1) < 1e-6 and abs(y0 - 2) < 1e-6, (x0, y0)
    for value in (.5, 0., -1.):
        assert edit(obj, 'LOCATION', 0, value) is None, value
    x, y, z = current(obj, 'LOCATION')
    assert abs(x + 1) < 1e-6 and abs(y / x - y0 / x0) < 1e-6 and abs(z - z0) < 1e-6, (x, y, z)
    results['reference_switch'] = 'a ratio remembered in one reference is not reused after switching orientation; a fixed Frame still crosses zero'


def default_rotation_order():
    reset()
    obj = empty(location=(0, 0, 0))
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler = (.1, .2, .3)
    linked(obj, 'ROTATION', 'DEFAULT')
    assert edit(obj, 'ROTATION', 0, 0.) is None
    obj.rotation_mode = 'ZYX'
    ctx.view_layer.update()
    assert edit(obj, 'ROTATION', 0, .05) is None
    got = tuple(obj.rotation_euler)
    assert abs(got[0] - .05) < 1e-8 and got[1:] == (0., 0.), got
    assert edit(obj, 'ROTATION', 0, 0.) is None
    obj.rotation_mode = 'XYZ'
    ctx.view_layer.update()
    assert edit(obj, 'ROTATION', 0, .05) is None
    got = tuple(obj.rotation_euler)
    assert abs(got[0] - .05) < 1e-8 and got[1:] == (0., 0.), got
    results['default_rotation_order'] = 'changing native Euler order, including returning to a previously used order, discards the old ratio at zero'


def links_toggle_back():
    for space in ('DEFAULT', 'REFERENCE'):
        reset()
        obj = empty()
        linked(obj, 'LOCATION', space)
        assert edit(obj, 'LOCATION', 0, 0.) is None
        obj.better_item.link_location = (False, False, False)
        obj.better_item.link_location = (True, True, True)
        message = edit(obj, 'LOCATION', 0, 1.)
        assert message and 'BI-T008' in message, (space, message)
        assert tuple(obj.location) == (0., 0., 0.), tuple(obj.location)
    results['links_toggle_back'] = 'off/on links discard the old ratio even without an edit between toggles'


def anchors_bounded():
    reset()
    objects = []
    for index in range(math_core._LINK_ANCHOR_ENTRIES + 6):
        obj = bpy.data.objects.new('a%d' % index, None)
        ctx.scene.collection.objects.link(obj)
        obj.location = (1, 2, 3)
        obj.better_item.transform_space = 'DEFAULT'
        obj.better_item.link_location = (True, True, True)
        objects.append(obj)
        ctx.view_layer.update()
        assert edit(obj, 'LOCATION', 0, 2.) is None
    assert len(math_core._link_anchors) <= math_core._LINK_ANCHOR_ENTRIES
    tv.clear_cache()
    assert not math_core._link_anchors
    results['anchors_bounded'] = 'anchor store is bounded and cleared with the transform caches'


def instancers():
    reset()
    mesh = bpy.data.meshes.new('m')
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=2)
    builder.to_mesh(mesh)
    builder.free()
    obj = bpy.data.objects.new('c', mesh)
    ctx.scene.collection.objects.link(obj)
    ctx.view_layer.update()
    plain = bpy.data.objects.new('p', mesh)
    ctx.scene.collection.objects.link(plain)
    group = bpy.data.node_groups.new('Unrealized', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    source = group.nodes.new('NodeGroupInput')
    sink = group.nodes.new('NodeGroupOutput')
    instance = group.nodes.new('GeometryNodeGeometryToInstance')
    group.links.new(source.outputs['Geometry'], instance.inputs['Geometry'])
    group.links.new(instance.outputs['Instances'], sink.inputs['Geometry'])
    ctx.view_layer.update()
    assert tv.dimensions(plain, ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    modifier = obj.modifiers.new('Instances', 'NODES')
    modifier.node_group = group
    ctx.view_layer.update()
    try:
        tv.values(ctx, obj, 'DIMENSIONS')
        raise AssertionError('instances were measured')
    except BetterItemError as exc:
        assert 'BI-M005' in str(exc), exc
    # The cached instancer set must follow the evaluated scene both ways.
    assert tv.dimensions(plain, ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    obj.modifiers.remove(modifier)
    ctx.view_layer.update()
    assert tv.values(ctx, obj, 'DIMENSIONS') and obj.name in ctx.scene.objects
    results['instancers'] = 'unrealized instances are refused and the lookup follows modifier add/remove'


def normal_fingerprint():
    reset()
    mesh = bpy.data.meshes.new('d')
    builder = bmesh.new()
    bmesh.ops.create_icosphere(builder, subdivisions=3, radius=1)
    builder.to_mesh(mesh)
    builder.free()
    obj = bpy.data.objects.new('d', mesh)
    ctx.scene.collection.objects.link(obj)
    ctx.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.mode_set(mode='EDIT')
    except RuntimeError:
        results['normal_fingerprint'] = 'skipped: Edit Mode unavailable'
        return
    walks = {'count': 0}
    original = native_refs._selection_states

    def counted(context):
        walks['count'] += 1
        return original(context)

    native_refs._selection_states = counted
    try:
        bpy.ops.mesh.select_all(action='DESELECT')
        ctx.view_layer.update()
        first = native_refs._normal_signature(ctx, fresh=False)
        base = walks['count']
        for _ in range(25):
            assert native_refs._normal_signature(ctx, fresh=False) == first
        assert walks['count'] == base, 'idle ticks walked every element'
        editing = bmesh.from_edit_mesh(mesh)
        editing.verts.ensure_lookup_table()
        editing.verts[0].select_set(True)
        editing.select_flush(True)
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        ctx.view_layer.update()
        second = native_refs._normal_signature(ctx, fresh=False)
        assert second != first and walks['count'] == base + 1
        # Same selected-element count, different element: still detected.
        editing.verts[0].select_set(False)
        editing.verts[5].select_set(True)
        editing.select_flush(True)
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        ctx.view_layer.update()
        third = native_refs._normal_signature(ctx, fresh=False)
        assert third != second
        # Safety net: an edit with no event is still found after the interval.
        editing.verts[5].select_set(False)
        editing.verts[7].select_set(True)
        editing.select_flush(True)
        native_refs._normal_dirty.clear()
        stamp = native_refs._normal_elements[ctx.scene.as_pointer()]
        native_refs._normal_elements[ctx.scene.as_pointer()] = (stamp[0], stamp[1], stamp[2] - 10.)
        fourth = native_refs._normal_signature(ctx, fresh=False)
        assert fourth != third
    finally:
        native_refs._selection_states = original
        bpy.ops.object.mode_set(mode='OBJECT')
    results['normal_fingerprint'] = 'idle ticks reuse the fingerprint; events, equal-count swaps and the safety interval are detected'


for case in (drag_ratio, cross_zero, outside_changes_win, reference_switch, default_rotation_order, links_toggle_back, anchors_bounded, instancers, normal_fingerprint):
    case()
for name, text in results.items():
    print('OK', name, '-', text)
print('BETTER_ITEM_GESTURES179_OK')
