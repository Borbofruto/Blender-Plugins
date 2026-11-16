"""Edit Mode Normal polling cost on a dense mesh (1.7.9 study).

Run through the compatibility runner in gui_sync mode (real window, real
View3D override). Calls native_refs.sync() explicitly, as the 0.2 s timer would.
Not a frame-rate or latency acceptance test: timings have no pass/fail limit.
Correctness is checked: a swap to a different vertex with the same selected
count must produce a different native Normal sample.
"""
import json
import statistics
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
import bpy
import bmesh
import addon_utils

addon_utils.enable('better_item')
from better_item import native_refs

ctx = bpy.context
walks = {'count': 0}
walker_name = '_selection_states' if hasattr(native_refs, '_selection_states') else '_normal_signature'
original_walker = getattr(native_refs, walker_name)


def counted(*args, **kwargs):
    walks['count'] += 1
    return original_walker(*args, **kwargs)


def ticks(count):
    samples = []
    before = walks['count']
    for _ in range(count):
        start = time.perf_counter()
        assert native_refs.sync() == .2
        samples.append(time.perf_counter() - start)
    return dict(iterations=count, median_ms=statistics.median(samples) * 1e3,
                max_ms=max(samples) * 1e3, walks=walks['count'] - before)


def select_only(mesh, index):
    editing = bmesh.from_edit_mesh(mesh)
    for vert in editing.verts:
        vert.select_set(False)
    editing.select_flush(False)
    editing.verts.ensure_lookup_table()
    editing.verts[index].select_set(True)
    editing.select_history.clear()
    editing.select_history.add(editing.verts[index])
    editing.select_flush(True)
    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
    ctx.view_layer.update()


setattr(native_refs, walker_name, counted)
try:
    if ctx.object and ctx.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=512, ring_count=256, radius=1)
    obj = ctx.object
    vertices = len(obj.data.vertices)
    assert vertices >= 100000, vertices
    obj.better_item.orientation = 'NORMAL'
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    key = ctx.scene.as_pointer()
    # Two vertices on different rings: different normals, same selected count.
    first_index, second_index = 1000, vertices // 3
    select_only(obj.data, first_index)
    start = time.perf_counter()
    native_refs.sync()
    first_sample_ms = (time.perf_counter() - start) * 1e3
    first_matrix = native_refs._normal_cache.get(key)
    assert first_matrix is not None, 'no Normal sample after first sync'
    first_matrix = first_matrix.copy()
    idle = ticks(30)
    select_only(obj.data, second_index)
    start = time.perf_counter()
    native_refs.sync()
    swap_ms = (time.perf_counter() - start) * 1e3
    second_matrix = native_refs._normal_cache.get(key)
    assert second_matrix is not None and second_matrix != first_matrix, 'equal-count swap not detected'
    idle_after_swap = ticks(30)
    time.sleep(native_refs.__dict__.get('_NORMAL_RECHECK_SECONDS', 0.) + .1)
    safety = ticks(1)
    result = dict(passed=True, blender=bpy.app.version_string,
                  module=__import__('better_item').__file__, walker=walker_name,
                  vertices=vertices, first_sample_ms=first_sample_ms, idle=idle,
                  swap_same_count_ms=swap_ms, idle_after_swap=idle_after_swap,
                  after_safety_interval=safety)
    Path(__file__).with_suffix('.results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('EDITMODE NORMAL BENCHMARK', json.dumps(result))
finally:
    setattr(native_refs, walker_name, original_walker)
    if ctx.object and ctx.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
