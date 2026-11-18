# SPDX-License-Identifier: GPL-3.0-or-later
"""Minimal DXF reader independent of ezdxf: LINE, ARC and CIRCLE from ENTITIES.

Works on ASCII DXF of any release (reads group-code pairs only).
"""

import math


def parse_raw(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        tokens = [ln.strip() for ln in f.read().splitlines()]
    pairs = list(zip(tokens[0::2], tokens[1::2]))
    header = {}
    out = []
    section = None
    cur = None
    var = None
    for code, value in pairs:
        if code == "0" and value == "SECTION":
            section = "?"
            continue
        if section == "?" and code == "2":
            section = value
            continue
        if code == "0" and value == "ENDSEC":
            if cur is not None:
                out.append(cur)
                cur = None
            section = None
            continue
        if section == "HEADER":
            if code == "9":
                var = value
            elif var is not None and var not in header:
                header[var] = value
            continue
        if section != "ENTITIES":
            continue
        if code == "0":
            if cur is not None:
                out.append(cur)
            cur = {"type": value, "g": {}}
            continue
        if cur is not None and code not in cur["g"]:
            cur["g"][code] = value
    entities = []
    other = {}
    for c in out:
        g = c["g"]
        t = c["type"]
        if t not in ("LINE", "ARC", "CIRCLE"):
            other[t] = other.get(t, 0) + 1
            continue
        d = {"type": t, "layer": g.get("8")}
        if t == "LINE":
            d["start"] = (float(g["10"]), float(g["20"]))
            d["end"] = (float(g["11"]), float(g["21"]))
        else:
            d["center"] = (float(g["10"]), float(g["20"]))
            d["radius"] = float(g["40"])
            if t == "ARC":
                d["angles"] = (float(g.get("50", 0)) % 360.0, float(g.get("51", 0)) % 360.0)
        entities.append(d)
    return {"header": header, "entities": entities, "other_entities": other}


def _key(e, nd=4):
    if e["type"] == "LINE":
        a = tuple(round(c, nd) + 0.0 for c in e["start"])
        b = tuple(round(c, nd) + 0.0 for c in e["end"])
        return ("LINE",) + (a + b if a <= b else b + a)
    if e["type"] == "CIRCLE":
        return ("CIRCLE",) + tuple(round(c, nd) + 0.0 for c in e["center"]) + (round(e["radius"], nd) + 0.0,)
    a0, a1 = e["angles"]
    cx, cy = e["center"]
    r = e["radius"]
    p0 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
    p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
    return (
        ("ARC",)
        + tuple(round(c, nd) + 0.0 for c in e["center"])
        + (round(r, nd) + 0.0,)
        + tuple(round(c, nd) + 0.0 for c in p0)
        + tuple(round(c, nd) + 0.0 for c in p1)
    )


def compare(expected, actual, tol=1e-4):
    """Match entity lists (order-free) within ``tol``. Returns list of problems."""
    problems = []
    left = list(actual)
    for e in expected:
        best = None
        for i, a in enumerate(left):
            if a["type"] != e["type"]:
                continue
            ke, ka = _key(e, 9), _key(a, 9)
            if all(abs(x - y) <= tol for x, y in zip(ke[1:], ka[1:])):
                best = i
                break
            if e["type"] == "LINE":  # reversed direction
                ka2 = ("LINE",) + ka[3:5] + ka[1:3]
                if all(abs(x - y) <= tol for x, y in zip(ke[1:], ka2[1:])):
                    best = i
                    break
        if best is None:
            problems.append({"missing": e})
        else:
            left.pop(best)
    for a in left:
        problems.append({"unexpected": a})
    return problems
