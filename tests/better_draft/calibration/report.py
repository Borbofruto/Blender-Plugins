# SPDX-License-Identifier: GPL-3.0-or-later
"""Build Markdown calibration tables from calibrate.py JSON output.

Usage: python report.py <calibration.json> <fit_tol_mm> > tables.md
"""

import json
import sys
from collections import defaultdict

NEGATIVE_PREFIXES = (
    "regular_polygon",
    "hand_facets",
    "ellipse",
    "bevel_profile",
    "subdivided_line",
)


def fmt(x, spec=".2e"):
    if x is None:
        return "-"
    return format(x, spec)


def is_negative(row):
    return row["case"].startswith(NEGATIVE_PREFIXES)


def main():
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    tol = float(sys.argv[2])
    rows = [r for r in data["rows"] if r.get("sweep") is None]
    main_rows = [r for r in rows if r["tolerance_mm"] == tol]
    p = data["params"]
    out = []
    w = out.append
    w("Blender %s (%s). Fit tolerance %g mm; straight tolerance %g deg; corner limit %g deg; "
      "chord ratio limit %g; confidence threshold %g; minimum segments %d."
      % (data["blender"], data["build"], tol, p["straight_tolerance_deg"], p["corner_limit_deg"],
         p["chord_ratio_limit"], p["confidence_threshold"], p["min_segments"]))
    w("")
    w("### Per case (fit tolerance %g mm)" % tol)
    w("")
    w("| Case | Source | n | Entities L/A/C | Recognised | Segments | Confidence | Max dev (mm) | max abs dR (mm) | max abs dC (mm) | Decisions |")
    w("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in main_rows:
        ent = r.get("entities") or {}
        cands = r["candidates"]
        rel = [c for c in cands if c["label"].startswith("true")] if not is_negative(r) else cands
        rel = rel or cands
        segs = sorted({c["segments"] for c in rel})
        confs = [c["confidence"] for c in rel]
        devs = [c["max_dev_mm"] for c in rel]
        drs = [abs(c["radius_error_mm"]) for c in rel if "radius_error_mm" in c]
        dcs = [c["center_error_mm"] for c in rel if "center_error_mm" in c]
        dec = defaultdict(int)
        for c in rel:
            dec["%s/%s" % (c["decision"], c["reason"])] += 1
        probs = r.get("region_problems", []) + r.get("problems", [])
        w("| %s | %s | %s | %s/%s/%s | %s/%s | %s | %s | %s | %s | %s | %s |" % (
            r["case"], r["source"], r["n"],
            ent.get("LINE", "-"), ent.get("ARC", "-"), ent.get("CIRCLE", "-"),
            r.get("recognized_expected", "-"), r.get("expected_arcs", "-"),
            ",".join(str(s) for s in segs) or "-",
            ("%.3f-%.3f" % (min(confs), max(confs))) if confs else "-",
            fmt(max(devs)) if devs else "-",
            fmt(max(drs)) if drs else "-",
            fmt(max(dcs)) if dcs else "-",
            "; ".join("%s x%d" % kv for kv in sorted(dec.items())) + (" " + ",".join(probs) if probs else ""),
        ))
    w("")
    w("### Confidence x segments x deviation (true arcs/circles, fit tolerance %g mm)" % tol)
    w("")
    w("| Segments | Candidates | Confidence min | Confidence max | Max dev (mm) | Became ARC/CIRCLE |")
    w("| --- | --- | --- | --- | --- | --- |")
    by_seg = defaultdict(list)
    neg_seg = defaultdict(list)
    for r in main_rows:
        for c in r["candidates"]:
            if is_negative(r) or not c["label"].startswith("true"):
                neg_seg[c["segments"]].append((c, r))
            else:
                by_seg[c["segments"]].append((c, r))
    for s in sorted(by_seg):
        items = by_seg[s]
        confs = [c["confidence"] for c, _ in items]
        w("| %d | %d | %.3f | %.3f | %s | %d |" % (
            s, len(items), min(confs), max(confs), fmt(max(c["max_dev_mm"] for c, _ in items)),
            sum(1 for c, _ in items if c["decision"] in ("arc", "circle"))))
    w("")
    w("### Candidates without an expected arc (negatives and spurious runs, fit tolerance %g mm)" % tol)
    w("")
    w("| Case | n | Segments | Confidence | Max dev (mm) | cv turn | cv length | Decision |")
    w("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for s in sorted(neg_seg):
        for c, r in neg_seg[s]:
            w("| %s | %s | %d | %.3f | %s | %.3f | %.3f | %s/%s |" % (
                r["case"], r["n"], s, c["confidence"], fmt(c["max_dev_mm"]),
                c["components"]["cv_turn"], c["components"]["cv_length"], c["decision"], c["reason"]))
    w("")
    w("### Fit tolerance sweep")
    w("")
    w("Positive arcs counted only when the run has at least the minimum segments. "
      "False arcs: ARC/CIRCLE entities in cases where no arc is expected.")
    w("")
    w("| Fit tol (mm) | Expected arcs recognised | Missed (case/source/n) | False ARC/CIRCLE (case/n) |")
    w("| --- | --- | --- | --- |")
    tols = sorted({r["tolerance_mm"] for r in rows})
    for t in tols:
        rec = exp = 0
        missed = []
        false = []
        for r in rows:
            if r["tolerance_mm"] != t:
                continue
            if is_negative(r) or r.get("expected_arcs", 0) == 0:
                ent = r.get("entities") or {}
                k = ent.get("ARC", 0) + ent.get("CIRCLE", 0)
                if k:
                    false.append("%s/%s(%d)" % (r["case"], r["n"], k))
                continue
            if r["n"] < p["min_segments"] or r["case"].startswith("marked"):
                continue
            exp += r["expected_arcs"]
            rec += r.get("recognized_expected", 0)
            if r.get("recognized_expected", 0) < r["expected_arcs"]:
                missed.append("%s/%s/%s" % (r["case"], r["source"], r["n"]))
        w("| %g | %d/%d | %s | %s |" % (t, rec, exp, ", ".join(missed) or "-", ", ".join(false) or "-"))
    sweep = [r for r in data["rows"] if r.get("sweep") == "straight"]
    if sweep:
        w("")
        w("### Straight tolerance sweep (fit tolerance %g mm)" % sweep[0]["tolerance_mm"])
        w("")
        w("| Case | Source | n | Straight (deg) | Entities L/A/C | Recognised | Arc segments |")
        w("| --- | --- | --- | --- | --- | --- | --- |")
        for r in sweep:
            ent = r.get("entities") or {}
            segs = sorted({c["segments"] for c in r["candidates"] if c["decision"] in ("arc", "circle")})
            w("| %s | %s | %s | %g | %s/%s/%s | %s/%s | %s |" % (
                r["case"], r["source"], r["n"], r["straight_deg"],
                ent.get("LINE", "-"), ent.get("ARC", "-"), ent.get("CIRCLE", "-"),
                r.get("recognized_expected", "-"), r.get("expected_arcs", "-"),
                ",".join(str(s) for s in segs) or "-"))
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
