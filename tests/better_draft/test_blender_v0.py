# SPDX-License-Identifier: GPL-3.0-or-later
"""End-to-end tests of the installed better_draft extension inside Blender.

Install the ZIP into an isolated profile first, then:
    blender --offline-mode --background --factory-startup --python-exit-code 1 \
        --python test_blender_v0.py -- --out <dir>

DXF files are read back with ezdxf (the reader) and compared with the known
geometry. Every case also checks that the scene is unchanged.
"""

import hashlib
import json
import math
import os
import shutil
import sys
import traceback

import addon_utils
import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "calibration"))
import calibrate as shapes  # noqa: E402  (shape builders only)


def _reset(scale_length=1.0):
    # read_factory_settings would also reset preferences and disable the add-on.
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.context.scene.unit_settings.scale_length = scale_length


shapes.reset = _reset

MOD = "bl_ext.user_default.better_draft"
ATTR = "better_draft_arc_mode"
RESULTS = []


# ---------------------------------------------------------------------------
# Helpers


def snapshot():
    """Fingerprint of everything the addon must not change."""
    bpy.context.view_layer.update()  # settle matrix_world before comparing
    h = hashlib.sha256()
    for coll in ("objects", "meshes", "texts", "materials", "collections", "images", "node_groups"):
        h.update(("%s=%d;" % (coll, len(getattr(bpy.data, coll)))).encode())
    for obj in sorted(bpy.data.objects, key=lambda o: o.name):
        h.update(obj.name.encode())
        h.update(repr([tuple(r) for r in obj.matrix_world]).encode())
        h.update(repr((obj.select_get(), [m.name for m in obj.modifiers])).encode())
        if obj.type == "MESH":
            me = obj.data
            h.update(repr([tuple(v.co) for v in me.vertices]).encode())
            h.update(repr([tuple(e.vertices) for e in me.edges]).encode())
            h.update(repr([tuple(p.vertices) for p in me.polygons]).encode())
            for a in sorted(me.attributes, key=lambda a: a.name):
                vals = [d.value for d in a.data] if a.data_type in {"INT", "FLOAT", "BOOLEAN", "INT8"} else []
                h.update(repr((a.name, a.domain, a.data_type, vals)).encode())
    act = bpy.context.view_layer.objects.active
    h.update(repr((act.name if act else None, bpy.context.mode)).encode())
    return h.hexdigest()


def select_only(*objs):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def read(path):
    import ezdxf

    doc = ezdxf.readfile(path)
    ents = []
    for e in doc.modelspace():
        t = e.dxftype()
        d = {"type": t, "layer": e.dxf.layer}
        if t == "LINE":
            d["start"] = tuple(e.dxf.start)[:2]
            d["end"] = tuple(e.dxf.end)[:2]
        else:
            d["center"] = tuple(e.dxf.center)[:2]
            d["radius"] = e.dxf.radius
            if t == "ARC":
                d["angles"] = (e.dxf.start_angle, e.dxf.end_angle)
        ents.append(d)
    return {"insunits": doc.header.get("$INSUNITS"), "entities": ents}


def kinds(dxf, layer=None):
    out = {"LINE": 0, "ARC": 0, "CIRCLE": 0}
    for e in dxf["entities"]:
        if layer is None or e["layer"] == layer:
            out[e["type"]] += 1
    return out


def export(out_dir, name, expect_ok=True, **kw):
    path = os.path.join(out_dir, name + ".dxf")
    before = snapshot()
    files_before = set(os.listdir(out_dir))
    error = None
    try:
        res = bpy.ops.better_draft.export_dxf(filepath=path, **kw)
    except RuntimeError as exc:
        res = {"CANCELLED"}
        error = str(exc)
    after = snapshot()
    new_files = sorted(set(os.listdir(out_dir)) - files_before)
    assert before == after, "scene changed by export"
    if expect_ok:
        assert res == {"FINISHED"}, (res, error)
    else:
        assert res == {"CANCELLED"}, res
        assert not new_files, ("files written on refusal", new_files)
    return path, new_files, error


def case(fn):
    def run(out_dir):
        shapes.reset()
        try:
            detail = fn(out_dir) or {}
            RESULTS.append({"case": fn.__name__, "ok": True, **detail})
        except Exception:
            RESULTS.append({"case": fn.__name__, "ok": False, "error": traceback.format_exc()})

    run.__name__ = fn.__name__
    return run


def close(a, b, tol=1e-6):
    return abs(a - b) <= tol


# ---------------------------------------------------------------------------
# Cases


@case
def registration(out_dir):
    assert hasattr(bpy.ops.better_draft, "export_dxf")
    names = [f.__name__ for f in bpy.types.TOPBAR_MT_file_export._dyn_ui_initialize()]
    assert "menu_export" in names, names
    for menu in ("VIEW3D_MT_edit_mesh_context_menu", "VIEW3D_MT_edit_mesh_edges"):
        assert "menu_mark" in [f.__name__ for f in getattr(bpy.types, menu)._dyn_ui_initialize()], menu
    return {"menus": names.count("menu_export")}


@case
def rounded_rect_bevel_modifier(out_dir):
    obj, _ = shapes.case_bevel_modifier(8)
    select_only(obj)
    path, files, _ = export(out_dir, "rounded_rect")
    dxf = read(path)
    assert dxf["insunits"] == 4
    assert kinds(dxf) == {"LINE": 4, "ARC": 4, "CIRCLE": 0}, kinds(dxf)
    assert all(e["layer"] == "OUTER" for e in dxf["entities"])
    arcs = [e for e in dxf["entities"] if e["type"] == "ARC"]
    centres = sorted((round(e["center"][0], 4), round(e["center"][1], 4)) for e in arcs)
    assert centres == [(5.0, 5.0), (5.0, 15.0), (35.0, 5.0), (35.0, 15.0)], centres
    assert all(close(e["radius"], 5.0, 1e-4) for e in arcs)
    lines = sorted(round(math.dist(e["start"], e["end"]), 4) for e in dxf["entities"] if e["type"] == "LINE")
    assert lines == [10.0, 10.0, 30.0, 30.0], lines
    assert os.path.exists(path[:-4] + ".txt")
    return {"files": files, "max_radius_error": max(abs(e["radius"] - 5.0) for e in arcs)}


@case
def plate_with_circular_hole(out_dir):
    obj, _ = shapes.case_hole_bmesh(32)
    select_only(obj)
    path, _, _ = export(out_dir, "hole")
    dxf = read(path)
    assert kinds(dxf, "OUTER") == {"LINE": 4, "ARC": 0, "CIRCLE": 0}
    assert kinds(dxf, "INNER") == {"LINE": 0, "ARC": 0, "CIRCLE": 1}
    c = next(e for e in dxf["entities"] if e["type"] == "CIRCLE")
    assert close(c["radius"], 8.0, 1e-4) and close(c["center"][0], 30.0, 1e-4) and close(c["center"][1], 20.0, 1e-4)
    return {"radius": c["radius"]}


@case
def hexagon_hole_circle_minimum(out_dir):
    obj, _ = shapes.case_hole_bmesh(6)
    select_only(obj)
    path, _, _ = export(out_dir, "hex_default")
    assert kinds(read(path), "INNER") == {"LINE": 6, "ARC": 0, "CIRCLE": 0}
    path, _, _ = export(out_dir, "hex_min6", circle_min_segments=6)
    assert kinds(read(path), "INNER") == {"LINE": 0, "ARC": 0, "CIRCLE": 1}


@case
def scene_scale_and_transform(out_dir):
    obj, _ = shapes.case_scene_mm(8)  # 1 unit = 1 mm
    select_only(obj)
    path, _, _ = export(out_dir, "scene_mm")
    arcs = [e for e in read(path)["entities"] if e["type"] == "ARC"]
    assert len(arcs) == 4 and all(close(e["radius"], 5.0, 1e-4) for e in arcs)
    shapes.reset()
    obj, _ = shapes.case_transformed(8)  # scale 2.5, rotated, moved
    select_only(obj)
    path, _, _ = export(out_dir, "scaled_rotated")
    arcs = [e for e in read(path)["entities"] if e["type"] == "ARC"]
    assert len(arcs) == 4 and all(close(e["radius"], 12.5, 1e-3) for e in arcs), [e["radius"] for e in arcs]


@case
def flipped_normal_not_mirrored(out_dir):
    shape = [(0, 0), (40, 0), (40, 10), (10, 10), (10, 30), (0, 30)]  # L, asymmetric
    up = shapes.polygon_object("up", [shape])
    down = shapes.polygon_object("down", [list(reversed(shape))])
    assert up.data.polygons[0].normal.z > 0 > down.data.polygons[0].normal.z
    out = {}
    for obj in (up, down):
        select_only(obj)
        path, _, _ = export(out_dir, "normal_" + obj.name)
        out[obj.name] = sorted(
            tuple(round(c, 6) for c in e["start"] + e["end"]) if e["start"] < e["end"] else
            tuple(round(c, 6) for c in e["end"] + e["start"])
            for e in read(path)["entities"]
        )
    assert out["up"] == out["down"], out
    top_edge = [s for s in out["up"] if [round(c, 3) for c in s] == [0.0, 30.0, 10.0, 30.0]]
    assert top_edge, out["up"]  # the L's short top edge stays at y = 30 (not mirrored to y = -30)


@case
def thick_plate_largest_face(out_dir):
    obj, _ = shapes.case_solidified_bevel(8)
    select_only(obj)
    path, _, _ = export(out_dir, "thick")
    assert kinds(read(path)) == {"LINE": 4, "ARC": 4, "CIRCLE": 0}


@case
def mark_arc_operator_and_undo(out_dir):
    obj, _ = shapes.case_rounded_rect_bmesh(3)
    select_only(obj)
    path, _, _ = export(out_dir, "facets_auto")
    assert kinds(read(path))["ARC"] == 0
    bpy.context.preferences.edit.use_global_undo = True
    bpy.ops.ed.undo_push(message="before edit")
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    for e in bm.edges:
        a, b = sorted(v.index for v in e.verts)
        e.select_set((a, b) in {(0, 1), (1, 2), (2, 3)})
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.ed.undo_push(message="selected")
    assert bpy.ops.better_draft.mark_arc() == {"FINISHED"}
    bm = bmesh.from_edit_mesh(obj.data)
    layer = bm.edges.layers.int.get(ATTR)
    marked = sorted(tuple(sorted(v.index for v in e.verts)) for e in bm.edges if e[layer] == 1)
    assert marked == [(0, 1), (1, 2), (2, 3)], marked
    assert export_poll_in_edit_mode() is False
    coords = [tuple(v.co) for v in bmesh.from_edit_mesh(obj.data).verts]
    bpy.ops.ed.undo()
    # Background undo with Python-pushed steps does not mirror the UI stack
    # (one undo lands in Object Mode), so only the effect is checked here.
    undone = count_marks("rr") == 0
    after_undo = (bpy.data.objects["rr"].mode, count_selected("rr"))
    assert undone, "undo did not remove the marks"
    obj = bpy.data.objects["rr"]  # global undo may rebuild data-blocks
    assert [tuple(v.co) for v in obj.data.vertices] == coords or obj.mode == "EDIT"
    if obj.mode != "EDIT":
        select_only(obj)
        bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(obj.data)
    for e in bm.edges:
        a, b = sorted(v.index for v in e.verts)
        e.select_set((a, b) in {(0, 1), (1, 2), (2, 3)})
    bmesh.update_edit_mesh(obj.data)
    assert bpy.ops.better_draft.mark_arc() == {"FINISHED"}
    bpy.ops.object.mode_set(mode="OBJECT")
    assert [tuple(v.co) for v in obj.data.vertices] == coords, "marking changed vertices"
    redo_steps = None
    select_only(obj)
    path, _, _ = export(out_dir, "facets_marked")
    dxf = read(path)
    arcs = [e for e in dxf["entities"] if e["type"] == "ARC"]
    assert len(arcs) == 1 and close(arcs[0]["radius"], 5.0, 1e-4), arcs
    return {"undo": undone, "after_undo": after_undo, "redo_steps": redo_steps}


def count_marks(name):
    obj = bpy.data.objects[name]
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        layer = bm.edges.layers.int.get(ATTR)
        return 0 if layer is None else sum(1 for e in bm.edges if e[layer] == 1)
    attr = obj.data.attributes.get(ATTR)
    return 0 if attr is None else sum(1 for d in attr.data if d.value == 1)


def count_selected(name):
    obj = bpy.data.objects[name]
    if obj.mode == "EDIT":
        return sum(1 for e in bmesh.from_edit_mesh(obj.data).edges if e.select)
    return sum(1 for e in obj.data.edges if e.select)


def export_poll_in_edit_mode():
    return bpy.ops.better_draft.export_dxf.poll()


@case
def mark_auto_does_not_create_attribute(out_dir):
    obj, _ = shapes.case_rounded_rect_bmesh(8)
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    assert bpy.ops.better_draft.mark_auto() == {"FINISHED"}
    bpy.ops.object.mode_set(mode="OBJECT")
    assert ATTR not in obj.data.attributes


@case
def mark_lines_wins(out_dir):
    obj, _ = shapes.case_rounded_rect_bmesh(8)
    me = obj.data
    attr = me.attributes.new(ATTR, "INT", "EDGE")
    for e in me.edges:
        a, b = sorted(e.vertices)
        if (a, b) == (3, 4):
            attr.data[e.index].value = 2  # lines
        elif (a, b) in {(0, 1), (1, 2)}:
            attr.data[e.index].value = 1  # arc
    select_only(obj)
    path, _, _ = export(out_dir, "lines_win")
    assert kinds(read(path))["ARC"] == 3


@case
def forced_arc_out_of_tolerance_refused(out_dir):
    obj, _ = shapes.case_rounded_rect_bmesh(3)
    me = obj.data
    attr = me.attributes.new(ATTR, "INT", "EDGE")
    for e in me.edges:
        a, b = sorted(e.vertices)
        if b <= 5 and b - a == 1:
            attr.data[e.index].value = 1  # corner plus part of a side
    select_only(obj)
    _, _, error = export(out_dir, "forced_bad", expect_ok=False)
    assert "do not fit one circle" in error, error
    return {"message": error}


@case
def loose_parts(out_dir):
    a = shapes.polygon_object("parts", [[(0, 0), (40, 0), (40, 20), (0, 20)]])
    me = a.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for loop in ([(60, 0), (80, 0), (80, 20), (60, 20)], [(100, 0), (100.5, 0), (100.5, 0.5), (100, 0.5)]):
        bm.faces.new([bm.verts.new((x * 0.001, y * 0.001, 0)) for x, y in loop])
    bm.to_mesh(me)
    bm.free()
    select_only(a)
    _, _, error = export(out_dir, "parts_stop", expect_ok=False)
    assert "2 separate parts" in error and "1 below the minimum area" in error, error
    path, _, _ = export(out_dir, "parts_largest", loose_parts="LARGEST")
    assert kinds(read(path)) == {"LINE": 4, "ARC": 0, "CIRCLE": 0}
    path, _, _ = export(out_dir, "parts_all", loose_parts="ALL", spacing=5.0)
    dxf = read(path)
    xs = sorted({round(p[0], 4) for e in dxf["entities"] for p in (e["start"], e["end"])})
    assert kinds(dxf)["LINE"] == 8 and xs == [0.0, 40.0, 45.0, 65.0], xs
    return {"message": error}


@case
def identical_and_equal_area_parts(out_dir):
    tri = [(0, 0), (30, 0), (10, 20)]
    c, s = math.cos(math.radians(40)), math.sin(math.radians(40))
    rot = [(c * x - s * y + 80, s * x + c * y + 10) for x, y in tri]
    obj = shapes.polygon_object("twins", [tri])
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.new([bm.verts.new((x * 0.001, y * 0.001, 0)) for x, y in rot])
    bm.to_mesh(obj.data)
    bm.free()
    select_only(obj)
    path, _, _ = export(out_dir, "twins_largest", loose_parts="LARGEST")
    assert kinds(read(path))["LINE"] == 3
    shapes.reset()
    obj = shapes.polygon_object("equal", [[(0, 0), (40, 0), (40, 10), (0, 10)]])
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.new([bm.verts.new((x * 0.001, y * 0.001, 0)) for x, y in [(60, 0), (80, 0), (80, 20), (60, 20)]])
    bm.to_mesh(obj.data)
    bm.free()
    select_only(obj)
    _, _, error = export(out_dir, "equal_area", expect_ok=False, loose_parts="LARGEST")
    assert "same area but different shapes" in error, error


@case
def refusals(out_dir):
    messages = {}
    # Warped quad: not flat.
    obj = shapes.polygon_object("warped", [[(0, 0), (40, 0), (40, 20), (0, 20)]])
    obj.data.vertices[2].co.z = 0.002
    select_only(obj)
    messages["not_planar"] = export(out_dir, "warped", expect_ok=False)[2]
    assert "is not flat" in messages["not_planar"]
    # Bow-tie face: outline crosses itself.
    shapes.reset()
    obj = shapes.polygon_object("bowtie", [[(0, 0), (20, 20), (20, 0), (0, 10)]])
    select_only(obj)
    messages["cross"] = export(out_dir, "bowtie", expect_ok=False)[2]
    assert "cross" in messages["cross"]
    # Hole touching the outline at one vertex: 3 x 3 grid without the centre and one corner.
    shapes.reset()
    me = bpy.data.meshes.new("touch")
    bm = bmesh.new()
    grid = {(i, j): bm.verts.new((i * 0.01, j * 0.01, 0)) for i in range(4) for j in range(4)}
    for i in range(3):
        for j in range(3):
            if (i, j) in {(1, 1), (0, 0)}:
                continue
            bm.faces.new([grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]])
    bm.to_mesh(me)
    bm.free()
    obj = shapes.link(bpy.data.objects.new("touch", me))
    select_only(obj)
    messages["touch"] = export(out_dir, "touch", expect_ok=False)[2]
    assert "touch at one vertex" in messages["touch"], messages["touch"]
    # World XY on a rotated part.
    shapes.reset()
    obj, _ = shapes.case_transformed(8)
    select_only(obj)
    messages["world_xy"] = export(out_dir, "worldxy", expect_ok=False, plane="WORLD_XY")[2]
    assert "not parallel to the world XY" in messages["world_xy"]
    # No faces.
    shapes.reset()
    me = bpy.data.meshes.new("wire")
    me.from_pydata([(0, 0, 0), (0.01, 0, 0)], [(0, 1)], [])
    obj = shapes.link(bpy.data.objects.new("wire", me))
    select_only(obj)
    messages["no_faces"] = export(out_dir, "wire", expect_ok=False)[2]
    assert "has no faces" in messages["no_faces"]
    return {"messages": messages}


@case
def one_bad_object_blocks_all(out_dir):
    good, _ = shapes.case_bevel_modifier(8)
    bad = shapes.polygon_object("bad", [[(0, 0), (20, 20), (20, 0), (0, 20)]])
    select_only(good, bad)
    export(out_dir, "mixed_batch", expect_ok=False)


@case
def single_file_two_objects(out_dir):
    a, _ = shapes.case_bevel_modifier(8)
    b, _ = shapes.case_hole_bmesh(32)
    select_only(a, b)
    path, files, _ = export(out_dir, "single", output="SINGLE", spacing=10.0)
    assert [f for f in files if f.endswith(".dxf")] == ["single.dxf"], files
    dxf = read(path)
    assert kinds(dxf) == {"LINE": 8, "ARC": 4, "CIRCLE": 1}, kinds(dxf)
    circle = next(e for e in dxf["entities"] if e["type"] == "CIRCLE")
    # Objects sorted by name: "bevmod" (40 x 20) first, then "hole" at x = 40 + 10.
    assert close(circle["center"][0], 50.0 + 30.0, 1e-4), circle
    path, files, _ = export(out_dir, "per_object", output="PER_OBJECT")
    assert sorted(f for f in files if f.endswith(".dxf")) == ["per_object_bevmod.dxf", "per_object_hole.dxf"], files


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    out_root = argv[argv.index("--out") + 1]
    version = bpy.app.version_string.split()[0]
    out_dir = os.path.join(out_root, "e2e-" + version)
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    addon_utils.enable(MOD, default_set=True)
    for name in CASES:
        globals()[name](out_dir)
    summary = {"blender": bpy.app.version_string, "passed": sum(r["ok"] for r in RESULTS), "total": len(RESULTS),
               "results": RESULTS}
    with open(os.path.join(out_root, "e2e-%s.json" % version), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, default=str)
    for r in RESULTS:
        print("%s %s" % ("PASS" if r["ok"] else "FAIL", r["case"]))
        if not r["ok"]:
            print(r["error"])
    print("better_draft e2e: %d/%d passed on %s" % (summary["passed"], summary["total"], version))
    if summary["passed"] != summary["total"]:
        raise SystemExit(1)


CASES = [
    "registration",
    "rounded_rect_bevel_modifier",
    "plate_with_circular_hole",
    "hexagon_hole_circle_minimum",
    "scene_scale_and_transform",
    "flipped_normal_not_mirrored",
    "thick_plate_largest_face",
    "mark_arc_operator_and_undo",
    "mark_auto_does_not_create_attribute",
    "mark_lines_wins",
    "forced_arc_out_of_tolerance_refused",
    "loose_parts",
    "identical_and_equal_area_parts",
    "refusals",
    "one_bad_object_blocks_all",
    "single_file_two_objects",
]

main()
