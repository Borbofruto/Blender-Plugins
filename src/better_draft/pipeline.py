# SPDX-License-Identifier: GPL-3.0-or-later
"""From extracted parts to placed pieces. No Blender imports.

Nothing here writes files; ``dxf_writer`` does that only after every object
has been analysed without problems.
"""

import math

from . import parts as pt
from . import recognition as rc

OUTPUT_PER_OBJECT = "PER_OBJECT"
OUTPUT_SINGLE = "SINGLE"


class Piece:
    __slots__ = ("object_name", "part_index", "region", "edge_ids", "bbox")

    def __init__(self, object_name, part_index, region, edge_ids):
        self.object_name = object_name
        self.part_index = part_index
        self.region = region  # recognition.RegionResult
        self.edge_ids = edge_ids
        self.bbox = entities_bbox(region)


class ObjectResult:
    __slots__ = ("name", "pieces", "problems", "notes", "selection")

    def __init__(self, name):
        self.name = name
        self.pieces = []
        self.problems = []  # (object name, Problem, point_mm or None)
        self.notes = []  # informational strings for the report
        self.selection = None


def _loop_point(loop, edges):
    """Midpoint (mm) of the listed loop edges, for messages."""
    if not edges:
        return None
    n = len(loop)
    xs = []
    ys = []
    for e in edges:
        a = loop[e % n]
        b = loop[(e + 1) % n]
        xs.append(0.5 * (a[0] + b[0]))
        ys.append(0.5 * (a[1] + b[1]))
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def problem_point(problem, loops):
    li = problem.loop
    d = problem.details
    if li is None or li >= len(loops):
        return None
    if "edges" in d:
        return _loop_point(loops[li], d["edges"])
    if "edge" in d:
        return _loop_point(loops[li], [d["edge"]])
    if "vertex" in d:
        return loops[li][d["vertex"] % len(loops[li])]
    return None


def analyze_object(name, region_data, params, loose_mode, min_area_fraction):
    """Analyse one object's ``RegionData``. Returns ``ObjectResult``."""
    out = ObjectResult(name)
    for p in region_data.problems:
        out.problems.append((name, p, None))
    if out.problems:
        return out
    loops_by_part = [p.loops for p in region_data.parts]
    sel = pt.select_parts(loops_by_part, loose_mode, min_area_fraction, params.fit_tolerance_mm)
    out.selection = sel
    if sel.problem is not None:
        out.problems.append((name, sel.problem, None))
        return out
    for i in sel.ignored_small:
        out.notes.append("part %d ignored: area %.4f mm2 is below the minimum" % (i + 1, sel.areas[i]))
    for i in sel.duplicates:
        out.notes.append("part %d skipped: identical to the exported part" % (i + 1))
    for i in sel.selected:
        part = region_data.parts[i]
        res = rc.analyze_region(part.loops, part.modes, params)
        if res.problems:
            for p in res.problems:
                out.problems.append((name, p, problem_point(p, part.loops)))
            continue
        out.pieces.append(Piece(name, i, res, part.edge_ids))
    return out


# ---------------------------------------------------------------------------
# Bounding boxes and layout


def _arc_extremes(arc):
    pts = [arc.start, arc.end]
    a0, a1 = arc.dxf_angles
    sweep = (a1 - a0) % 360.0 or 360.0
    for k in range(4):
        ang = 90.0 * k
        if (ang - a0) % 360.0 <= sweep:
            r = math.radians(ang)
            pts.append((arc.center[0] + arc.radius * math.cos(r), arc.center[1] + arc.radius * math.sin(r)))
    return pts


def entities_bbox(region):
    xs = []
    ys = []
    for lr in region.loops:
        for e in lr.entities:
            if e.kind == "LINE":
                pts = [e.start, e.end]
            elif e.kind == "ARC":
                pts = _arc_extremes(e)
            else:
                cx, cy = e.center
                pts = [(cx - e.radius, cy - e.radius), (cx + e.radius, cy + e.radius)]
            for x, y in pts:
                xs.append(x)
                ys.append(y)
    if not xs:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), min(ys), max(xs), max(ys))


def layout(pieces, output, spacing_mm):
    """Return [(group_key, [(piece, (dx, dy)), ...]), ...].

    One group per object (PER_OBJECT) or a single group (SINGLE). A group with
    one piece keeps its coordinates; several pieces go side by side along +X,
    bottoms aligned to the first piece, ``spacing_mm`` apart.
    """
    if output == OUTPUT_SINGLE:
        groups = [(None, list(pieces))]
    else:
        groups = []
        for p in pieces:
            if groups and groups[-1][0] == p.object_name:
                groups[-1][1].append(p)
            else:
                groups.append((p.object_name, [p]))
    placed = []
    for key, items in groups:
        if len(items) == 1:
            placed.append((key, [(items[0], (0.0, 0.0))]))
            continue
        first = items[0].bbox
        cursor = first[2] + spacing_mm
        row = [(items[0], (0.0, 0.0))]
        for p in items[1:]:
            x0, y0, x1, _ = p.bbox
            dx = cursor - x0
            dy = first[1] - y0
            row.append((p, (dx, dy)))
            cursor += (x1 - x0) + spacing_mm
        placed.append((key, row))
    return placed


def check_no_overlap(row):
    """True if placed bounding boxes are disjoint (used by tests)."""
    boxes = []
    for piece, (dx, dy) in row:
        x0, y0, x1, y1 = piece.bbox
        boxes.append((x0 + dx, y0 + dy, x1 + dx, y1 + dy))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                return False
    return True


def counts(pieces):
    c = {"LINE": 0, "ARC": 0, "CIRCLE": 0}
    for p in pieces:
        for lr in p.region.loops:
            for e in lr.entities:
                c[e.kind] += 1
    return c

