# SPDX-License-Identifier: GPL-3.0-or-later
"""Import each DXF in FreeCAD (headless, C++ importer) and compare its edges
with the entities read by the independent raw parser.

    FreeCADCmd.exe freecad_check.py   (arguments through env vars)
    BD_DXF_DIR=<dir with .dxf>  BD_OUT=<json path>
"""

import json
import math
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dxf_raw  # noqa: E402

import FreeCAD  # noqa: E402
import Import  # noqa: E402
import Part  # noqa: E402


_RR = [("ARC", (5, 5), 5), ("ARC", (5, 15), 5), ("ARC", (35, 5), 5), ("ARC", (35, 15), 5)]
# Known geometry (mm) of the end-to-end cases: arcs/circles and line count.
KNOWN = {
    "rounded_rect.dxf": (_RR, 4),
    "per_object_bevmod.dxf": (_RR, 4),
    "thick.dxf": (_RR, 4),
    "scene_mm.dxf": (_RR, 4),
    "scaled_rotated.dxf": ([("ARC", (x * 2.5, y * 2.5), 12.5) for _, (x, y), _ in _RR], 4),
    "hole.dxf": ([("CIRCLE", (30, 20), 8)], 4),
    "per_object_hole.dxf": ([("CIRCLE", (30, 20), 8)], 4),
    "hex_min6.dxf": ([("CIRCLE", (30, 20), 8)], 4),
    "hex_default.dxf": ([], 10),
    "facets_auto.dxf": ([], 16),
    "facets_marked.dxf": ([("ARC", (35, 15), 5)], 13),
    "single.dxf": (_RR + [("CIRCLE", (80, 20), 8)], 8),
    "parts_largest.dxf": ([], 4),
    "parts_all.dxf": ([], 8),
    "normal_up.dxf": ([], 6),
    "normal_down.dxf": ([], 6),
    "twins_largest.dxf": ([], 3),
    "lines_win.dxf": ([("ARC", (5, 15), 5), ("ARC", (5, 5), 5), ("ARC", (35, 5), 5)], 4 + 8),
}


def known_check(name, got, tol=1e-3):
    if name not in KNOWN:
        return None
    curves, n_lines = KNOWN[name]
    problems = []
    lines = sum(1 for e in got if e["type"] == "LINE")
    if lines != n_lines:
        problems.append("lines %d != %d" % (lines, n_lines))
    found = [e for e in got if e["type"] in ("ARC", "CIRCLE")]
    if len(found) != len(curves):
        problems.append("curves %d != %d" % (len(found), len(curves)))
    for t, (cx, cy), r in curves:
        if not any(e["type"] == t and abs(e["radius"] - r) <= tol and math.hypot(e["center"][0] - cx, e["center"][1] - cy) <= tol
                   for e in found):
            problems.append("missing %s R%g at (%g, %g)" % (t, r, cx, cy))
    return problems


def edges_to_entities(doc):
    ents = []
    for obj in doc.Objects:
        shape = getattr(obj, "Shape", None)
        if shape is None or shape.isNull():
            continue
        if obj.InList:  # skip children already counted through a compound parent
            continue
        for edge in shape.Edges:
            c = edge.Curve
            if isinstance(c, (Part.Line, Part.LineSegment)):
                p0 = edge.Vertexes[0].Point
                p1 = edge.Vertexes[-1].Point
                ents.append({"type": "LINE", "start": (p0.x, p0.y), "end": (p1.x, p1.y)})
            elif isinstance(c, Part.Circle):
                closed = edge.isClosed() or abs((edge.LastParameter - edge.FirstParameter) - 2 * math.pi) < 1e-9
                d = {"center": (c.Center.x, c.Center.y), "radius": c.Radius}
                if closed:
                    d["type"] = "CIRCLE"
                else:
                    d["type"] = "ARC"
                    p0 = edge.valueAt(edge.FirstParameter)
                    p1 = edge.valueAt(edge.LastParameter)
                    a0 = math.degrees(math.atan2(p0.y - c.Center.y, p0.x - c.Center.x)) % 360.0
                    a1 = math.degrees(math.atan2(p1.y - c.Center.y, p1.x - c.Center.x)) % 360.0
                    if c.Axis.z < 0:  # clockwise parametrisation: swap to CCW
                        a0, a1 = a1, a0
                    d["angles"] = (a0, a1)
                ents.append(d)
            else:
                ents.append({"type": "OTHER:" + type(c).__name__})
    return ents


def main():
    dxf_dir = os.environ["BD_DXF_DIR"]
    out_path = os.environ["BD_OUT"]
    rows = []
    for name in sorted(os.listdir(dxf_dir)):
        if not name.lower().endswith(".dxf"):
            continue
        path = os.path.join(dxf_dir, name)
        row = {"file": name}
        try:
            raw = dxf_raw.parse_raw(path)
            doc = FreeCAD.newDocument("check")
            Import.readDXF(path, doc.Name, True)
            doc.recompute()
            got = edges_to_entities(doc)
            FreeCAD.closeDocument(doc.Name)
            counts = {}
            for e in got:
                counts[e["type"]] = counts.get(e["type"], 0) + 1
            exp_counts = {}
            for e in raw["entities"]:
                exp_counts[e["type"]] = exp_counts.get(e["type"], 0) + 1
            problems = dxf_raw.compare(raw["entities"], got, tol=1e-4)
            known = known_check(name, got)
            row.update({"freecad_counts": counts, "raw_counts": exp_counts, "problems": problems[:10],
                        "known_geometry_problems": known,
                        "ok": not problems and counts == exp_counts and not known})
        except Exception:  # noqa: BLE001
            row.update({"ok": False, "error": traceback.format_exc()})
        rows.append(row)
    data = {"freecad": FreeCAD.Version()[:4], "rows": rows, "passed": all(r["ok"] for r in rows)}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print("freecad check:", sum(r["ok"] for r in rows), "/", len(rows))


main()
