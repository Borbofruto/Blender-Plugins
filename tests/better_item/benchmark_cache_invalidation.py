"""Measure real evaluation updates, inspection misses and Object Mode polling.

Use the compatibility runner in gui_sync mode. This is a benchmark, not a
latency acceptance test: correctness is checked, timings have no fixed limit.
"""
import json
import sys
import time
import statistics
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
import bpy
import addon_utils

addon_utils.enable('better_item')
from better_item import distribution as d, native_refs, transform_view as tv

ctx = bpy.context
rows = []
full_calls = 0
source_calls = 0
tree_calls = 0
original_inspect = d._inspect_spacing
original_sources = native_refs._source_names
original_tree = tv._tree_matches


def counted_inspect(*args):
    global full_calls
    full_calls += 1
    return original_inspect(*args)


def counted_sources(*args):
    global source_calls
    source_calls += 1
    return original_sources(*args)


def counted_tree(*args):
    global tree_calls
    tree_calls += 1
    return original_tree(*args)


d._inspect_spacing = counted_inspect
native_refs._source_names = counted_sources
tv._tree_matches = counted_tree
updates = {}


def capture(_scene, graph):
    for update in graph.updates:
        item = update.id.original
        key = (type(item).__name__, update.is_updated_geometry,
               update.is_updated_transform, update.is_updated_shading)
        if key not in updates:
            updates[key] = dict(type=key[0], geometry=key[1], transform=key[2],
                                shading=key[3], count=0, examples=[])
        row = updates[key]
        row['count'] += 1
        if len(row['examples']) < 3 and item.name not in row['examples']:
            row['examples'].append(item.name)


bpy.app.handlers.depsgraph_update_post.append(capture)
try:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add()
    template = ctx.object
    template.select_set(False)
    objects = []
    for i in range(1500):
        obj = bpy.data.objects.new('Benchmark %04d' % i, template.data)
        ctx.scene.collection.objects.link(obj)
        obj.location = (3 + 3*i, 2, 0)
        objects.append(obj)
    other = bpy.data.objects.new('Unrelated Empty', None)
    ctx.scene.collection.objects.link(other)
    material = bpy.data.materials.new('Unrelated shader')
    material.use_nodes = True
    template.data.materials.append(material)
    shader = material.node_tree.nodes.get('Principled BSDF')
    # A GN object exists to measure unnecessary tree traversal on shader edits.
    group = bpy.data.node_groups.new('Unrelated Geometry', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = group.nodes.new('NodeGroupInput')
    out = group.nodes.new('NodeGroupOutput')
    group.links.new(inp.outputs['Geometry'], out.inputs['Geometry'])
    template.modifiers.new('Benchmark GN', 'NODES').node_group = group
    s = ctx.scene.better_item
    s.arrange_reference_mode = 'INDIVIDUAL'
    s.arrange_origin = 'GLOBAL'
    s.arrange_orientation = 'GLOBAL'
    s.distribution_method = 'OFFSET'
    s.axes = (True, False, False)
    ctx.view_layer.objects.active = objects[0]
    ctx.view_layer.update()
    for count in (600, 1500):
        chosen = objects[:count]
        for obj in objects:
            obj.select_set(obj in chosen)
        ctx.view_layer.update()
        for basis in ('ORIGINS', 'GEOMETRY', 'VOLUME'):
            s.distribution_mode = basis
            ctx.view_layer.update()
            d.clear_inspection()
            start = time.perf_counter()
            expected = d.inspect_spacing(ctx, chosen)
            cold = time.perf_counter() - start
            for event in ('unchanged', 'unrelated_transform', 'shader'):
                samples = []
                n = full_calls
                trees = tree_calls
                updates.clear()
                for repeat in range(3):
                    start = time.perf_counter()
                    if event == 'unrelated_transform':
                        other.location.x += 1
                        ctx.view_layer.update()
                    elif event == 'shader':
                        shader.inputs['Roughness'].default_value = .2 + .1*repeat
                        ctx.view_layer.update()
                    assert d.inspect_spacing(ctx, chosen) == expected
                    samples.append(time.perf_counter() - start)
                rows.append(dict(count=count, basis=basis, event=event,
                                 cold_seconds=cold, median_seconds=statistics.median(samples),
                                 full_inspections=full_calls-n, tree_visits=tree_calls-trees,
                                 updates=list(updates.values())))
    # Isolate sync itself; do not turn these timings into UI frame-rate claims.
    n = source_calls
    samples = []
    for repeat in range(30):
        start = time.perf_counter()
        assert native_refs.sync() == .2
        samples.append(time.perf_counter() - start)
    polling = dict(scene_objects=len(ctx.scene.objects), iterations=30,
                   source_scans=source_calls-n, median_seconds=statistics.median(samples))
    result = dict(passed=True, blender=bpy.app.version_string,
                  module=__import__('better_item').__file__, rows=rows, polling=polling)
    Path(__file__).with_suffix('.results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('CACHE BENCHMARK', json.dumps(dict(rows=[{k:v for k,v in row.items() if k != 'updates'} for row in rows], polling=polling)))
finally:
    bpy.app.handlers.depsgraph_update_post.remove(capture)
    d._inspect_spacing = original_inspect
    native_refs._source_names = original_sources
    tv._tree_matches = original_tree
