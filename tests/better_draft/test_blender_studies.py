# SPDX-License-Identifier: GPL-3.0-or-later
"""Studies with the installed better_draft extension (background).

    blender --offline-mode --background --factory-startup --python-exit-code 1 \
        --python test_blender_studies.py -- --out <dir> --study modifiers|performance

modifiers:   arc marks under Subdivision, Bevel, Array, Mirror and Solidify.
performance: export time of a large plate and of 20 objects in one file.
Writes <out>/study-<name>-<version>.json. Observations, not pass/fail, except
that every export must leave the scene unchanged.
"""

import json
import math
import os
import shutil
import statistics
import sys
import time

import addon_utils
import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "calibration"))
import calibrate as shapes  # noqa: E402

MOD = "bl_ext.user_default.better_draft"
ATTR = "better_draft_arc_mode"
MM = 0.001


def reset(scale_length=1.0):
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.context.scene.unit_settings.scale_length = scale_length


shapes.reset = reset


def select_only(*objs):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def export(path, **kw):
    try:
        res = bpy.ops.better_draft.export_dxf(filepath=path, **kw)
        return res, None
    except RuntimeError as exc:
        return {"CANCELLED"}, str(exc).strip()


def read_counts(path):
    import ezdxf

    doc = ezdxf.readfile(path)
    out = {"LINE": 0, "ARC": 0, "CIRCLE": 0}
    radii = []
    for e in doc.modelspace():
        out[e.dxftype()] += 1
        if e.dxftype() in ("ARC", "CIRCLE"):
            radii.append(round(e.dxf.radius, 4))
    return out, sorted(radii)


def eval_marks(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        attr = me.attributes.get(ATTR)
        if attr is None:
            return {"attribute": False, "edges": len(me.edges)}
        hist = {}
        for d in attr.data:
            hist[str(d.value)] = hist.get(str(d.value), 0) + 1
        return {"attribute": True, "domain": attr.domain, "type": attr.data_type, "values": hist, "edges": len(me.edges)}
    finally:
        ev.to_mesh_clear()


# ---------------------------------------------------------------------------


def marked_facets():
    """Rounded rectangle with 3-segment corners; first corner marked as arc."""
    obj, _ = shapes.case_rounded_rect_bmesh(3)
    me = obj.data
    attr = me.attributes.new(ATTR, "INT", "EDGE")
    for e in me.edges:
        a, b = sorted(e.vertices)
        if (a, b) in {(0, 1), (1, 2), (2, 3)}:
            attr.data[e.index].value = 1
    return obj


MODIFIERS = {
    "none": lambda o: None,
    "subdivision_catmull_1": lambda o: setattr(o.modifiers.new("Sub", "SUBSURF"), "levels", 1),
    "subdivision_simple_1": lambda o: _subsimple(o),
    "bevel_vertices_2seg": lambda o: _bevel(o),
    "array_2_x": lambda o: _array(o),
    "mirror_x": lambda o: _mirror(o),
    "solidify_3mm": lambda o: setattr(o.modifiers.new("Sol", "SOLIDIFY"), "thickness", 3 * MM),
}


def _subsimple(o):
    m = o.modifiers.new("Sub", "SUBSURF")
    m.subdivision_type = "SIMPLE"
    m.levels = 1


def _bevel(o):
    m = o.modifiers.new("Bev", "BEVEL")
    m.affect = "VERTICES"
    m.width = 1 * MM
    m.segments = 2
    m.limit_method = "NONE"


def _array(o):
    m = o.modifiers.new("Arr", "ARRAY")
    m.count = 2
    m.relative_offset_displace = (1.25, 0, 0)


def _mirror(o):
    m = o.modifiers.new("Mir", "MIRROR")
    m.use_axis[0] = True


def study_modifiers(out_dir):
    rows = []
    for name, apply in MODIFIERS.items():
        for marked in (True, False):
            reset()
            if marked:
                obj = marked_facets()
            else:
                obj, _ = shapes.case_rounded_rect_bmesh(3)
            apply(obj)
            select_only(obj)
            row = {"modifier": name, "marked": marked, "marks_in_evaluated_mesh": eval_marks(obj)}
            path = os.path.join(out_dir, "mod_%s_%s.dxf" % (name, "marked" if marked else "plain"))
            res, err = export(path, loose_parts="ALL")
            row["result"] = sorted(res)
            row["message"] = err
            if res == {"FINISHED"}:
                row["entities"], row["radii"] = read_counts(path)
            rows.append(row)
    return rows


def plate_with_holes():
    w, h = 400.0, 300.0
    outer, _ = shapes.rounded_rect(w, h, 10.0, 256)
    holes = []
    for i in range(10):
        for j in range(5):
            cx = 30.0 + i * 37.0
            cy = 40.0 + j * 55.0
            holes.append(list(reversed(shapes.circle_loop(cx, cy, 4.0, 64))))
    return shapes.polygon_object("plate", [outer] + holes)


def timed(path, repeats, **kw):
    times = []
    for _ in range(repeats):
        t = time.perf_counter()
        res, err = export(path, **kw)
        times.append(time.perf_counter() - t)
        assert res == {"FINISHED"}, err
    return times


def study_performance(out_dir):
    rows = []
    reset()
    plate = plate_with_holes()
    select_only(plate)
    n_verts = len(plate.data.vertices)
    times = timed(os.path.join(out_dir, "perf_plate.dxf"), 3)
    counts, radii = read_counts(os.path.join(out_dir, "perf_plate.dxf"))
    rows.append({"case": "plate 400x300, 4 corners x 256 seg, 50 holes x 64 seg", "vertices": n_verts,
                 "seconds": times, "median": statistics.median(times), "entities": counts,
                 "distinct_radii": sorted(set(radii))})
    reset()
    objs = []
    for k in range(10):
        obj, _ = shapes.case_hole_bmesh(32)
        obj.name = "part_%02d" % k
        obj.location.x = k * 0.1
        objs.append(obj)
        bev, _ = shapes.case_bevel_modifier(16)
        bev.name = "bev_%02d" % k
        bev.location.y = 0.1 + k * 0.05
        objs.append(bev)
    select_only(*objs)
    times = timed(os.path.join(out_dir, "perf_20_objects.dxf"), 3, output="SINGLE")
    counts, _ = read_counts(os.path.join(out_dir, "perf_20_objects.dxf"))
    rows.append({"case": "20 objects (10 plates with 32-seg hole, 10 bevelled 16-seg rectangles), single file",
                 "seconds": times, "median": statistics.median(times), "entities": counts})
    return rows


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :]
    out_root = argv[argv.index("--out") + 1]
    study = argv[argv.index("--study") + 1]
    version = bpy.app.version_string.split()[0]
    out_dir = os.path.join(out_root, "study-%s-%s" % (study, version))
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    addon_utils.enable(MOD, default_set=True)
    rows = study_modifiers(out_dir) if study == "modifiers" else study_performance(out_dir)
    data = {"blender": bpy.app.version_string, "study": study, "rows": rows}
    with open(os.path.join(out_root, "study-%s-%s.json" % (study, version)), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print(json.dumps(data, indent=1))


main()
