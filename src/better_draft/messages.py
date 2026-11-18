# SPDX-License-Identifier: GPL-3.0-or-later
"""User-facing refusal messages: what went wrong and what to do. No Blender imports."""

_TEXT = {
    "NO_FACES": "has no faces. Export reads the faces of a flat mesh",
    "DEGENERATE_FACES": "has only zero-area faces. Remove them with Mesh > Clean Up > Delete Loose / Degenerate Dissolve",
    "NOT_PLANAR": "the reference face ({reference}) is not flat within {tol} mm. "
    "In Edit Mode make a flat face active, or raise Fit Tolerance",
    "NON_MANIFOLD": "an edge of the flat region is shared by more than two faces. "
    "Fix it (Select > Select All by Trait > Non Manifold)",
    "LOOPS_TOUCH": "two outline loops touch at one vertex. Move or split that vertex so each outline vertex has two outline edges",
    "NOT_PARALLEL_TO_XY": "the flat region is not parallel to the world XY plane. Use Plane: Local Part, or rotate the object",
    "LOOSE_PARTS": "has {count} separate parts{ignored_text}. Set Loose Parts to Largest or All in the export options, "
    "or separate them (Mesh > Separate > By Loose Parts)",
    "EQUAL_AREA_PARTS": "the {count} largest parts have the same area but different shapes, so the largest cannot be chosen. "
    "Set Loose Parts to All, or separate them (Mesh > Separate > By Loose Parts)",
    "LOOPS_INTERSECT": "outline edges cross or overlap{at}. Fix the crossing edges",
    "MULTIPLE_OUTER": "a part has more than one outer outline. Separate the pieces",
    "NESTED_ISLAND": "a piece sits inside a hole of another piece. Separate the pieces",
    "NO_LOOP": "the flat region has no outline",
    "DEGENERATE_LOOP": "an outline loop has zero area{at}. Remove the collapsed faces",
    "SELF_OVERLAP": "an outline folds back on itself{at}. Fix the overlapping edges",
    "FORCED_ARC_OUT_OF_TOLERANCE": "{n} edges marked as arc{at} do not fit one circle within {tol} mm{dev_text}. "
    "Mark them Automatic or Lines, raise Fit Tolerance, or correct the vertices",
    "FORCED_ARC_SINGLE_EDGE": "a single edge marked as arc{at} cannot define an arc. Mark the whole run (two or more edges)",
    "FORCED_ARC_SPLIT": "edges marked as arc{at} are not one continuous run. Mark one run at a time",
}


def format_problem(object_name, problem, point=None, tol=None):
    d = dict(problem.details)
    d.setdefault("tol", "%g" % tol if tol is not None else "?")
    d["at"] = " near (%.3f, %.3f) mm" % point if point is not None else ""
    edges = d.get("edges") or []
    d["n"] = len(edges)
    dev = d.get("deviation_mm")
    d["dev_text"] = " (deviation %.4f mm)" % dev if dev is not None else ""
    ign = d.get("ignored", 0)
    d["ignored_text"] = " (plus %d below the minimum area)" % ign if ign else ""
    if "tolerance_mm" in d:
        d["tol"] = "%g" % d["tolerance_mm"]
    template = _TEXT.get(problem.code, problem.code)
    try:
        body = template.format(**d)
    except (KeyError, IndexError):
        body = template
    return "%s: %s." % (object_name, body)
