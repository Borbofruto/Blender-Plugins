# SPDX-License-Identifier: GPL-3.0-or-later
"""Plain-text export report, one per DXF file. No Blender imports."""

import math

from .constants import ADDON_NAME


def _fmt_pt(p):
    return "(%.4f, %.4f)" % (p[0], p[1])


def build(placed, params, notes_by_object, header):
    lines = ["%s export report" % ADDON_NAME, header, ""]
    p = params
    lines.append(
        "Parameters: fit tolerance %g mm, straight tolerance %g deg, min segments %d, "
        "circle min segments %d, confidence threshold %g"
        % (p.fit_tolerance_mm, p.straight_tolerance_deg, p.min_segments, p.circle_min_segments, p.confidence_threshold)
    )
    lines.append("Units: millimetres, scale 1:1. Coordinates below are before placement offsets.")
    seen = set()
    for piece, (dx, dy) in placed:
        lines.append("")
        lines.append(
            "Object %s, part %d, offset (%.4f, %.4f) mm" % (piece.object_name, piece.part_index + 1, dx, dy)
        )
        if piece.object_name not in seen:
            for note in notes_by_object.get(piece.object_name, []):
                lines.append("  note: %s" % note)
            seen.add(piece.object_name)
        for li, (lr, role) in enumerate(zip(piece.region.loops, piece.region.roles)):
            lines.append("  Loop %d (%s): %d vertices" % (li + 1, role, lr.vertex_count))
            for k, e in enumerate(lr.entities):
                if e.kind == "LINE":
                    lines.append(
                        "    %3d LINE   %s -> %s  length %.4f  edges %d"
                        % (k + 1, _fmt_pt(e.start), _fmt_pt(e.end), math.dist(e.start, e.end), len(e.orig_edges))
                    )
                else:
                    c = e.candidate
                    manual = "manual" if c.manual == "arc" else "auto"
                    extra = ""
                    if e.kind == "ARC":
                        a0, a1 = e.dxf_angles
                        extra = "  angles %.4f -> %.4f" % (a0, a1)
                    lines.append(
                        "    %3d %-6s R %.4f  centre %s%s  segments %d  max dev %.2e  confidence %.3f  %s"
                        % (k + 1, e.kind, e.radius, _fmt_pt(e.center), extra, c.segments, c.fit.max_dev,
                           c.confidence, manual)
                    )
            rejected = [c for c in lr.candidates if c.decision == "lines" and c.reason != "superseded"]
            for c in rejected:
                lines.append(
                    "        candidate kept as lines: R %.4f, segments %d, max dev %.2e, confidence %.3f, reason %s"
                    % (c.fit.radius, c.segments, c.fit.max_dev, c.confidence, c.reason)
                )
            if lr.max_gap:
                lines.append("        largest gap between consecutive arcs: %.2e mm" % lr.max_gap)
    return "\n".join(lines) + "\n"
