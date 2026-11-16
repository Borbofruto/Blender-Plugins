"""Selective transform invalidation must retain dependency freshness and Undo.

Run as gui_sync through the compatibility runner. No timing thresholds: count
actual full inspections and compare every retained result with a fresh oracle.
"""
import sys
import json
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
import bpy
import addon_utils
from mathutils import Matrix, Vector

addon_utils.enable('better_item')
from better_item import distribution as d, transform_view as tv, native_refs, frames, placement

ctx = bpy.context
checks = []
calls = 0
original = d._inspect_spacing


def counted(*args):
    global calls
    calls += 1
    return original(*args)


d._inspect_spacing = counted
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
objects = []
for x in (3, 6, 10):
    bpy.ops.mesh.primitive_cube_add(location=(x, 0, 0))
    objects.append(ctx.object)
for obj in objects:
    obj.select_set(True)
ctx.view_layer.objects.active = objects[0]
other = bpy.data.objects.new('Unrelated transform', None)
ctx.scene.collection.objects.link(other)
s = ctx.scene.better_item
s.arrange_reference_mode = 'INDIVIDUAL'
s.arrange_origin = 'GLOBAL'
s.arrange_orientation = 'GLOBAL'
s.distribution_method = 'OFFSET'
s.distribution_mode = 'GEOMETRY'
s.axes = (True, False, False)
ctx.view_layer.update()


def read():
    result = d.inspect_spacing(ctx, objects)
    assert result == original(ctx, objects), (result, original(ctx, objects))
    return result


def changed(label, mutate):
    read()
    before = calls
    mutate()
    ctx.view_layer.update()
    read()
    assert calls > before, label
    checks.append(label)


try:
    for basis in ('ORIGINS', 'GEOMETRY', 'BOUNDS_CENTER', 'SURFACE', 'VOLUME'):
        s.distribution_mode = basis
        ctx.view_layer.update()
        read()
        before = calls
        for _ in range(3):
            other.location.y += 1
            ctx.view_layer.update()
            read()
        assert calls == before, (basis, 'unrelated transform caused a full inspection')
        changed('selected target transform / '+basis, lambda: setattr(objects[0].location, 'x', objects[0].location.x+1))
    changed('parent transform propagates to selected evaluated target',
            lambda: setattr(objects[0], 'parent', other))
    changed('unselected parent moves selected target', lambda: setattr(other.location, 'x', other.location.x+2))
    objects[0].parent = None
    # An unselected reference contributes placement geometry as well as origin.
    s.arrange_origin = 'OBJECT'
    s.arrange_origin_object = objects[2]
    selected = objects[:2]
    objects[2].select_set(False)
    objects, anchor = selected, objects[2]
    changed('unselected reference scale changes its placement', lambda: setattr(anchor.scale, 'x', 2))
    s.arrange_origin = 'GLOBAL'
    changed('mesh edits remain conservative', lambda: (setattr(objects[0].data.vertices[0].co, 'x', 5), objects[0].data.update()))
    s.distribution_method = 'ENDPOINT'
    s.distribution_end.mode = 'OBJECT'
    s.distribution_end.object = anchor
    anchor.location.x = 50
    changed('Endpoint object source', lambda: setattr(anchor.location, 'x', 60))
    frame = frames.create(ctx, 'Indirect cache source', Vector(), Matrix.Identity(3))
    frame.position_mode = 'OBJECT'
    frame.position_source = other
    s.arrange_origin = 'SAVED'
    s.arrange_origin_frame = frame.uid
    changed('indirect Frame source resolved in the key', lambda: setattr(other.location, 'z', 3))
    s.distribution_end.mode = 'CURSOR'
    changed('cursor changes without evaluated object update', lambda: setattr(ctx.scene.cursor.location, 'x', 75))
    # Application must still plan and verify independently of the display cache.
    s.distribution_method = 'OFFSET'
    s.distribution_mode = 'ORIGINS'
    s.arrange_origin = 'GLOBAL'
    d._inspect_spacing = lambda *_args: (_ for _ in ()).throw(AssertionError('Application used display cache'))
    d.apply(ctx, objects, basis='ORIGINS', method='OFFSET', axes=(True, False, False), spacing=5)
    d._inspect_spacing = counted
    assert sorted(round(obj.location.x, 5) for obj in objects) == [5, 10]
    checks.append('application never uses display-cache validation')

    # Isolate node-tree-only notifications, including when vertex caches are
    # empty but Placement/Live still depend on the geometry revision.
    tree = bpy.data.node_groups.new('Revision without vertex arrays', 'GeometryNodeTree')
    tree.nodes.new('GeometryNodeTransform')
    ctx.view_layer.update()
    tv._geometry_cache.clear()
    tv._dimension_cache.clear()
    revision = tv._geometry_revision
    graph = SimpleNamespace(updates=[SimpleNamespace(id=tree, is_updated_geometry=False)])
    tv.invalidate_geometry(ctx.scene, graph)
    assert tv._geometry_revision > revision
    checks.append('empty vertex caches still advance Placement/Live revision')
    shader = bpy.data.node_groups.new('Shader is not geometry', 'ShaderNodeTree')
    revision = tv._geometry_revision
    tv.invalidate_geometry(ctx.scene, SimpleNamespace(updates=[SimpleNamespace(id=shader, is_updated_geometry=False)]))
    assert tv._geometry_revision == revision
    checks.append('shader-only tree does not advance geometry revision')

    # Object Mode sync must keep native exports, while skipping normal searches.
    def forbidden(*_args):
        raise AssertionError('Object Mode scanned object reference sources')
    source_names = native_refs._source_names
    native_refs._source_names = forbidden
    try:
        frame.rotation_mode = 'MANUAL'
        native_refs.publish(ctx, frame)
        assert native_refs.sync() == .2
        assert frame.native_enabled and native_refs.named(ctx.scene, frame.native_name) is not None
        checks.append('Object Mode sync skips scans and preserves native Frame publication')
    finally:
        native_refs._source_names = source_names
    # Selection-normal refresh is still needed in Edit Mode (capture/export
    # remains supported; this does not add mesh-editing targets to the addon).
    ctx.view_layer.objects.active = objects[0]
    objects[0].better_item.orientation = 'NORMAL'
    bpy.ops.object.mode_set(mode='EDIT')
    import bmesh
    for obj in ctx.objects_in_mode_unique_data:
        mesh = bmesh.from_edit_mesh(obj.data)
        mesh.faces.ensure_lookup_table()
        for vert in mesh.verts:vert.select_set(False)
        mesh.faces[0].select_set(True)
        mesh.faces.active = mesh.faces[0]
        bmesh.update_edit_mesh(obj.data)
    scans = []
    def tracked_sources(scene):
        scans.append(scene.as_pointer())
        return source_names(scene)
    native_refs._source_names = tracked_sources
    try:
        assert native_refs.sync() == .2
        assert scans and ctx.scene.as_pointer() in native_refs._normal_cache
        checks.append('Edit Mode still refreshes native selection Normal')
    finally:
        native_refs._source_names = source_names
        bpy.ops.object.mode_set(mode='OBJECT')
    ctx.preferences.edit.use_global_undo = True
    bpy.ops.ed.undo_push(message='Before cache regression')
    read()
    bpy.ops.ed.undo()
    assert not d._inspection_cache
    checks.append('Undo clears entries and numeric dependencies')
    result = dict(passed=True, blender=bpy.app.version_string, checks=checks)
    Path(__file__).with_suffix('.results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('CACHE INVALIDATION PASSED', json.dumps(result))
finally:
    d._inspect_spacing = original
