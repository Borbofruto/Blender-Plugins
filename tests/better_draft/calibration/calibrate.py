# SPDX-License-Identifier: GPL-3.0-or-later
"""Calibration run (section 6 of the v0 specification).

Run inside Blender (background, factory startup):
    blender --background --factory-startup --python-exit-code 1 \
        --python calibrate.py -- --out <dir>

Builds shapes with known geometry (bmesh with analytic vertices, the Bevel
modifier, the bmesh bevel operator, mesh primitives, Solidify), extracts the
planar region with ``better_draft.region`` and runs the recognition core for
several fit tolerances. Writes one JSON row per candidate plus per-case
summaries to ``<out>/calibration-<blender version>.json``.
"""

import argparse
import json
import math
import os
import random
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "..", "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from better_draft import recognition as rc  # noqa: E402
from better_draft import region as rg  # noqa: E402
from better_draft.constants import ARC_MODE_ATTRIBUTE  # noqa: E402

TOLERANCES_MM = [0.0005, 0.001, 0.002, 0.005, 0.01, 0.05]
STRAIGHT_DEG = [0.05, 0.1, 0.25, 0.5, 1.0]
STRAIGHT_SWEEP_FIT_MM = 0.01
MM = 0.001  # metres per millimetre (default scene: 1 unit = 1 m)


# ---------------------------------------------------------------------------
# Scene helpers


def reset(scale_length=1.0):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.scale_length = scale_length


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj


def polygon_object(name, loops, unit=MM, offset=(0.0, 0.0, 0.0)):
    """One loop -> one n-gon; more loops -> triangle_fill with holes."""
    bm = bmesh.new()
    edges = []
    for loop in loops:
        vs = [bm.verts.new((x * unit + offset[0], y * unit + offset[1], offset[2])) for x, y in loop]
        if len(loops) == 1:
            bm.faces.new(vs)
        else:
            for i in range(len(vs)):
                edges.append(bm.edges.new((vs[i], vs[(i + 1) % len(vs)])))
    if len(loops) > 1:
        bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=True, edges=edges)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me))


def arc_points(cx, cy, r, a0_deg, sweep_deg, s, include_end=True):
    n = s + 1 if include_end else s
    return [
        (cx + r * math.cos(math.radians(a0_deg + sweep_deg * k / s)), cy + r * math.sin(math.radians(a0_deg + sweep_deg * k / s)))
        for k in range(n)
    ]


def rounded_rect(w, h, r, s):
    pts = []
    for cx, cy, a0 in ((w - r, h - r, 0), (r, h - r, 90), (r, r, 180), (w - r, r, 270)):
        pts += arc_points(cx, cy, r, a0, 90, s)
    return pts, [((w - r, h - r), r), ((r, h - r), r), ((r, r), r), ((w - r, r), r)]


def circle_loop(cx, cy, r, n, start_deg=0.0):
    return arc_points(cx, cy, r, start_deg, 360.0, n, include_end=False)


# ---------------------------------------------------------------------------
# Case builders. Each returns (obj, expected) where expected is a list of
# ((cx_mm, cy_mm), r_mm, kind) in the object's local plane (mm), and kind is
# "arc" or "circle". An empty list means "no arc expected" (negative case).


def case_rounded_rect_bmesh(s, size=1.0):
    pts, arcs = rounded_rect(40 * size, 20 * size, 5 * size, s)
    obj = polygon_object("rr", [pts])
    return obj, [((c[0], c[1]), r, "arc") for c, r in arcs]


def case_hole_bmesh(n):
    outer = [(0, 0), (60, 0), (60, 40), (0, 40)]
    hole = list(reversed(circle_loop(30, 20, 8, n)))
    obj = polygon_object("hole", [outer, hole])
    return obj, [((30.0, 20.0), 8.0, "circle")]


def case_slot_bmesh(s):
    pts = arc_points(20, 0, 4, -90, 180, s) + arc_points(0, 0, 4, 90, 180, s)
    obj = polygon_object("slot", [pts])
    return obj, [((20.0, 0.0), 4.0, "arc"), ((0.0, 0.0), 4.0, "arc")]


def case_subdivided_line(offset_m=0.0):
    pts = [(4.0 * k, 0.0) for k in range(10)] + [(40, 0), (40, 20), (0, 20)]
    return polygon_object("subdiv", [pts], offset=(offset_m, 0.0, 0.0)), []


def case_s_curve(s):
    # Two tangent arcs of opposite direction and different radii, closed by lines.
    a = arc_points(0, 10, 10, -90, 90, s)  # R10, centre (0, 10), ccw
    b = arc_points(16, 10, 6, 180, -90, s)[1:]  # R6, centre (16, 10), cw
    pts = a + b + [(16, 30), (0, 30), (-10, 30), (-10, 0)]
    return polygon_object("scurve", [pts]), [((0.0, 10.0), 10.0, "arc"), ((16.0, 10.0), 6.0, "arc")]


def case_mixed():
    # Line, 90 degree arc (8 segments), chamfer of one segment, lines.
    pts = [(0, 0), (30, 0)] + arc_points(30, 5, 5, -90, 90, 8)[1:] + [(30, 15), (0, 15)]
    return polygon_object("mixed", [pts]), [((30.0, 5.0), 5.0, "arc")]


def case_polygon(n):
    return polygon_object("poly", [circle_loop(0, 0, 10, n, 90.0)]), []


def case_noisy_circle(sigma_mm, seed=1):
    rnd = random.Random(seed)
    pts = []
    for k in range(32):
        a = 2 * math.pi * k / 32
        r = 10 + rnd.gauss(0, sigma_mm)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return polygon_object("noisy", [pts]), [((0.0, 0.0), 10.0, "circle")]


def case_hand_facets(n, seed):
    rnd = random.Random(seed)
    angles = sorted(2 * math.pi * (k + rnd.uniform(-0.15, 0.15)) / n for k in range(n))
    pts = [((10 + rnd.uniform(-0.5, 0.5)) * math.cos(a), (10 + rnd.uniform(-0.5, 0.5)) * math.sin(a)) for a in angles]
    return polygon_object("hand", [pts]), []


def case_ellipse(ratio):
    pts = [(10 * math.cos(2 * math.pi * k / 32), 10 / ratio * math.sin(2 * math.pi * k / 32)) for k in range(32)]
    return polygon_object("ellipse", [pts]), []


def _plane(name, w, h, unit=MM):
    return polygon_object(name, [[(0, 0), (w, 0), (w, h), (0, h)]], unit=unit)


def case_bevel_modifier(s, profile=0.5, width_mm=5.0, unit=MM, w=40, h=20):
    obj = _plane("bevmod", w, h, unit)
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.affect = "VERTICES"
    mod.width = width_mm * unit
    mod.segments = s
    mod.profile = profile
    mod.limit_method = "NONE"
    r = width_mm
    exp = [((w - r, h - r), r, "arc"), ((r, h - r), r, "arc"), ((r, r), r, "arc"), ((w - r, r), r, "arc")]
    return obj, (exp if abs(profile - 0.5) < 1e-9 else [])


def case_bevel_operator(s):
    bm = bmesh.new()
    vs = [bm.verts.new((x * MM, y * MM, 0.0)) for x, y in [(0, 0), (40, 0), (40, 20), (0, 20)]]
    bm.faces.new(vs)
    bmesh.ops.bevel(
        bm,
        geom=vs,
        offset=5 * MM,
        offset_type="OFFSET",
        segments=s,
        profile=0.5,
        affect="VERTICES",
    )
    me = bpy.data.meshes.new("bevop")
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new("bevop", me))
    _, arcs = rounded_rect(40, 20, 5, s)
    return obj, [((c[0], c[1]), r, "arc") for c, r in arcs]


def case_bevel_angles(s):
    # Trapezoid with 60 and 120 degree corners; vertex bevel, width 4 mm.
    h = 20.0
    dx = h / math.tan(math.radians(60))
    pts = [(0, 0), (50, 0), (50 - dx, h), (dx, h)]
    obj = polygon_object("bevang", [pts])
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.affect = "VERTICES"
    mod.width = 4 * MM
    mod.segments = s
    mod.limit_method = "NONE"
    # Expected circle for offset d along both edges at interior angle a:
    # radius d * tan(a / 2), centre on the bisector.
    exp = []
    corners = pts
    for i, p in enumerate(corners):
        a = corners[i - 1]
        b = corners[(i + 1) % 4]
        u = _unit2((a[0] - p[0], a[1] - p[1]))
        v = _unit2((b[0] - p[0], b[1] - p[1]))
        ang = math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1])))
        r = 4.0 * math.tan(ang / 2)
        bis = _unit2((u[0] + v[0], u[1] + v[1]))
        dist = 4.0 / math.cos(ang / 2)
        exp.append(((p[0] + bis[0] * dist, p[1] + bis[1] * dist), r, "arc"))
    return obj, exp


def _unit2(v):
    n = math.hypot(v[0], v[1])
    return (v[0] / n, v[1] / n)


def case_solidified_bevel(s):
    obj, exp = case_bevel_modifier(s)
    sol = obj.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 3 * MM
    return obj, exp


def case_circle_primitive(n):
    bpy.ops.mesh.primitive_circle_add(vertices=n, radius=10 * MM, fill_type="NGON")
    return bpy.context.active_object, [((0.0, 0.0), 10.0, "circle")]


def case_cylinder_primitive(n):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=10 * MM, depth=3 * MM)
    return bpy.context.active_object, [((0.0, 0.0), 10.0, "circle")]


def case_scene_mm(s):
    reset(scale_length=0.001)
    return case_bevel_modifier(s, unit=1.0)


def case_transformed(s):
    obj, exp = case_bevel_modifier(s)
    obj.scale = (2.5, 2.5, 2.5)
    obj.rotation_euler = (math.radians(30), math.radians(20), math.radians(10))
    obj.location = (1.0, 2.0, 3.0)
    return obj, [((c[0] * 2.5, c[1] * 2.5), r * 2.5, k) for c, r, k in exp]


def case_far_object(s, metres):
    obj, exp = case_bevel_modifier(s)
    obj.location = (metres, 0.0, 0.0)
    return obj, exp


def case_far_mesh(s, metres):
    pts, arcs = rounded_rect(40, 20, 5, s)
    obj = polygon_object("farmesh", [pts], offset=(metres, 0.0, 0.0))
    # Object origin stays at the world origin, so the local plane origin is
    # (0, 0): expected centres are shifted by the offset in mm.
    return obj, [((c[0] + metres / MM, c[1]), r, "arc") for c, r in arcs]


def case_marked_facets():
    pts, arcs = rounded_rect(40, 20, 5, 3)
    obj = polygon_object("marked", [pts])
    me = obj.data
    attr = me.attributes.new(ARC_MODE_ATTRIBUTE, "INT", "EDGE")
    # Mark the first corner's three edges (vertices 0..3) as arc.
    for e in me.edges:
        a, b = sorted(e.vertices)
        if (a, b) in {(0, 1), (1, 2), (2, 3)}:
            attr.data[e.index].value = 1
    return obj, [((arcs[0][0][0], arcs[0][0][1]), 5.0, "arc")]


def build_cases():
    cases = []
    for s in (64, 128):
        cases.append(("rounded_rect", "bevel_modifier", s, lambda s=s: case_bevel_modifier(s)))
    for s in (2, 3, 4, 6, 8, 16, 32):
        cases.append(("rounded_rect", "bmesh", s, lambda s=s: case_rounded_rect_bmesh(s)))
        cases.append(("rounded_rect", "bevel_modifier", s, lambda s=s: case_bevel_modifier(s)))
        cases.append(("rounded_rect", "bevel_operator", s, lambda s=s: case_bevel_operator(s)))
    for n in (6, 8, 10, 12, 16, 24, 32, 48, 64):
        cases.append(("hole", "bmesh", n, lambda n=n: case_hole_bmesh(n)))
    for n in (6, 8, 12, 16, 32, 64):
        cases.append(("circle", "primitive_circle", n, lambda n=n: case_circle_primitive(n)))
        cases.append(("circle", "primitive_cylinder", n, lambda n=n: case_cylinder_primitive(n)))
    for s in (4, 8, 16):
        cases.append(("slot", "bmesh", s, lambda s=s: case_slot_bmesh(s)))
    cases.append(("subdivided_line", "bmesh", 10, case_subdivided_line))
    cases.append(("subdivided_line_far_mesh_100m", "bmesh", 10, lambda: case_subdivided_line(100.0)))
    for s in (4, 8, 16):
        cases.append(("s_curve_R10_R6", "bmesh", s, lambda s=s: case_s_curve(s)))
    cases.append(("mixed_arc_chamfer", "bmesh", 8, case_mixed))
    cases.append(("marked_facets", "bmesh+attribute", 3, case_marked_facets))
    for n in (5, 6, 8, 12):
        cases.append(("regular_polygon", "bmesh", n, lambda n=n: case_polygon(n)))
    for sigma in (0.0002, 0.001, 0.003, 0.01, 0.03):
        cases.append(("noisy_circle_sigma_%gmm" % sigma, "bmesh", 32, lambda sg=sigma: case_noisy_circle(sg)))
    for n in (5, 6, 8, 10):
        for seed in (1, 2, 3):
            cases.append(("hand_facets_seed%d" % seed, "bmesh", n, lambda n=n, sd=seed: case_hand_facets(n, sd)))
    for ratio in (1.001, 1.01, 1.1):
        cases.append(("ellipse_%g" % ratio, "bmesh", 32, lambda r=ratio: case_ellipse(r)))
    for p in (0.3, 0.7, 1.0):
        cases.append(("bevel_profile_%g" % p, "bevel_modifier", 8, lambda p=p: case_bevel_modifier(8, profile=p)))
    for s in (4, 8, 16):
        cases.append(("corners_60_120", "bevel_modifier", s, lambda s=s: case_bevel_angles(s)))
        cases.append(("solidify_thickness", "bevel_modifier+solidify", s, lambda s=s: case_solidified_bevel(s)))
    for size in (0.1, 10.0, 100.0):
        cases.append(("rounded_rect_x%g" % size, "bmesh", 8, lambda z=size: case_rounded_rect_bmesh(8, z)))
    cases.append(("scene_scale_0.001", "bevel_modifier", 8, lambda: case_scene_mm(8)))
    cases.append(("scaled_rotated", "bevel_modifier", 8, lambda: case_transformed(8)))
    for metres in (100.0, 1000.0):
        cases.append(("far_object_%gm" % metres, "bevel_modifier", 8, lambda m=metres: case_far_object(8, m)))
        cases.append(("far_mesh_%gm" % metres, "bmesh", 8, lambda m=metres: case_far_mesh(8, m)))
    return cases


# ---------------------------------------------------------------------------
# Evaluation


def nearest_expected(center, expected):
    best = None
    for (cx, cy), r, kind in expected:
        d = math.hypot(center[0] - cx, center[1] - cy)
        if best is None or d < best[0]:
            best = (d, (cx, cy), r, kind)
    return best


def evaluate(obj, expected, params):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    data = rg.extract_region(obj, depsgraph, bpy.context.scene, params.fit_tolerance_mm)
    out = {
        "region_problems": [p.code for p in data.problems],
        "reference": data.reference,
        "flat": data.flat,
        "loops": len(data.loops),
    }
    if data.problems:
        out["candidates"] = []
        out["entities"] = {}
        return out
    res = rc.analyze_region(data.loops, data.modes, params)
    out["problems"] = [p.code for p in res.problems]
    cands = []
    counts = {"LINE": 0, "ARC": 0, "CIRCLE": 0}
    max_gap = 0.0
    tangency = []
    for lr in res.loops:
        max_gap = max(max_gap, lr.max_gap)
        tangency += lr.tangency_deg
        for ent in lr.entities:
            counts[ent.kind] += 1
        for c in lr.candidates:
            row = {
                "segments": c.segments,
                "edges": c.edge_count,
                "is_circle": c.is_circle,
                "confidence": c.confidence,
                "components": c.components,
                "max_dev_mm": c.fit.max_dev,
                "rms_dev_mm": c.fit.rms_dev,
                "radius_mm": c.fit.radius,
                "center_mm": [c.fit.cx, c.fit.cy],
                "decision": c.decision,
                "reason": c.reason,
                "manual": c.manual,
            }
            near = nearest_expected(c.fit.center, expected) if expected else None
            if near is not None and near[0] < 0.5 * near[2]:
                row["expected_radius_mm"] = near[2]
                row["center_error_mm"] = near[0]
                row["radius_error_mm"] = c.fit.radius - near[2]
                row["label"] = "true_" + near[3]
            else:
                row["label"] = "no_arc_expected"
            cands.append(row)
    out["candidates"] = cands
    out["entities"] = counts
    out["max_gap_mm"] = max_gap
    out["max_tangency_deg"] = max(tangency) if tangency else None
    found = 0
    for (cx, cy), r, kind in expected:
        for lr in res.loops:
            for ent in lr.entities:
                if ent.kind in ("ARC", "CIRCLE") and math.hypot(ent.center[0] - cx, ent.center[1] - cy) < 0.5 * r:
                    found += 1
                    break
            else:
                continue
            break
    out["expected_arcs"] = len(expected)
    out["recognized_expected"] = found
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    version = ".".join(str(x) for x in bpy.app.version)
    results = []
    straight_default = rc.Params().straight_tolerance_deg
    for name, source, n, build in build_cases():
        for tol in TOLERANCES_MM:
            reset()
            obj, expected = build()
            params = rc.Params(fit_tolerance_mm=tol)
            row = {"case": name, "source": source, "n": n, "tolerance_mm": tol, "straight_deg": straight_default}
            row.update(evaluate(obj, expected, params))
            results.append(row)
        if name.startswith("subdivided") or (name == "rounded_rect" and source == "bevel_modifier"):
            for straight in STRAIGHT_DEG:
                reset()
                obj, expected = build()
                params = rc.Params(fit_tolerance_mm=STRAIGHT_SWEEP_FIT_MM, straight_tolerance_deg=straight)
                row = {"case": name, "source": source, "n": n, "tolerance_mm": STRAIGHT_SWEEP_FIT_MM, "straight_deg": straight, "sweep": "straight"}
                row.update(evaluate(obj, expected, params))
                results.append(row)
    path = os.path.join(args.out, "calibration-%s.json" % version)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"blender": version, "build": bpy.app.build_hash.decode(), "params": rc.Params().as_dict(), "rows": results}, f, indent=1)
    print("wrote", path, len(results))


if __name__ == "__main__":
    main()
