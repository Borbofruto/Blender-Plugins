# SPDX-License-Identifier: GPL-3.0-or-later
"""Loose-part selection: area filter, largest part and congruence. No Blender imports.

A part is a list of loops (lists of (x, y) mm points), as produced by
``region.extract_region`` for one connected group of faces.
"""

import math

from . import geometry2d as g2
from .recognition import Problem

MODE_REFUSE = "REFUSE"
MODE_LARGEST = "LARGEST"
MODE_ALL = "ALL"


def part_area(loops):
    """Area enclosed by the part: outer area minus holes (by nesting)."""
    areas = [abs(g2.signed_area(lp)) for lp in loops]
    if not areas:
        return 0.0
    outer = max(range(len(loops)), key=lambda i: areas[i])
    return areas[outer] - sum(a for i, a in enumerate(areas) if i != outer)


def perimeter(loop):
    n = len(loop)
    return sum(g2.distance(loop[i], loop[(i + 1) % n]) for i in range(n))


def _outer_index(loops):
    return max(range(len(loops)), key=lambda i: abs(g2.signed_area(loops[i])))


def _ccw(loop):
    return list(loop) if g2.signed_area(loop) >= 0.0 else list(reversed(loop))


def _rigid(a, b):
    """Best rotation+translation taking points ``a`` onto ``b`` (no mirror)."""
    n = len(a)
    ax = sum(p[0] for p in a) / n
    ay = sum(p[1] for p in a) / n
    bx = sum(p[0] for p in b) / n
    by = sum(p[1] for p in b) / n
    s_dot = s_cross = 0.0
    for (x0, y0), (x1, y1) in zip(a, b):
        u0, v0 = x0 - ax, y0 - ay
        u1, v1 = x1 - bx, y1 - by
        s_dot += u0 * u1 + v0 * v1
        s_cross += u0 * v1 - v0 * u1
    ang = math.atan2(s_cross, s_dot)
    c, s = math.cos(ang), math.sin(ang)

    def apply(p):
        u, v = p[0] - ax, p[1] - ay
        return (c * u - s * v + bx, s * u + c * v + by)

    return apply


def congruent(part_a, part_b, tol):
    """True if part_a moved and rotated matches part_b within ``tol`` mm."""
    if len(part_a) != len(part_b):
        return False
    oa = _ccw(part_a[_outer_index(part_a)])
    ob = _ccw(part_b[_outer_index(part_b)])
    n = len(oa)
    if n != len(ob):
        return False
    if abs(perimeter(oa) - perimeter(ob)) > 2.0 * n * tol:
        return False
    holes_a = [h for i, h in enumerate(part_a) if i != _outer_index(part_a)]
    holes_b = [h for i, h in enumerate(part_b) if i != _outer_index(part_b)]
    for k in range(n):
        shifted = [ob[(i + k) % n] for i in range(n)]
        # Cheap rejection on a few correspondences before the full fit.
        probe = sorted({0, n // 3, (2 * n) // 3})
        if any(
            abs(g2.distance(oa[i], oa[j]) - g2.distance(shifted[i], shifted[j])) > 2.0 * tol
            for i in probe
            for j in probe
            if i < j
        ):
            continue
        apply = _rigid(oa, shifted)
        if all(g2.distance(apply(p), q) <= tol for p, q in zip(oa, shifted)):
            if _holes_match(holes_a, holes_b, apply, tol):
                return True
    return False


def _holes_match(holes_a, holes_b, apply, tol):
    free = list(range(len(holes_b)))
    for ha in holes_a:
        moved = [apply(p) for p in ha]
        match = None
        for j in free:
            hb = holes_b[j]
            if len(hb) != len(moved):
                continue
            if all(min(g2.distance(p, q) for q in hb) <= tol for p in moved):
                match = j
                break
        if match is None:
            return False
        free.remove(match)
    return True


class Selection:
    __slots__ = ("selected", "ignored_small", "duplicates", "areas", "problem")

    def __init__(self):
        self.selected = []  # part indices to export
        self.ignored_small = []  # below the area threshold
        self.duplicates = []  # identical copies of the exported largest part
        self.areas = []
        self.problem = None


def select_parts(parts, mode, min_area_fraction, tol):
    """Choose which parts to export. ``parts`` is a list of loop lists."""
    sel = Selection()
    sel.areas = [part_area(p) for p in parts]
    if not parts:
        sel.problem = Problem("NO_FACES")
        return sel
    largest = max(sel.areas)
    significant = []
    for i, a in enumerate(sel.areas):
        if a < min_area_fraction * largest:
            sel.ignored_small.append(i)
        else:
            significant.append(i)
    if len(significant) == 1:
        sel.selected = significant
        return sel
    if mode == MODE_ALL:
        sel.selected = significant
        return sel
    if mode != MODE_LARGEST:
        sel.problem = Problem("LOOSE_PARTS", None, count=len(significant), ignored=len(sel.ignored_small))
        return sel
    order = sorted(significant, key=lambda i: -sel.areas[i])
    top = order[0]
    eps = tol * max(perimeter(lp) for i in significant for lp in parts[i])
    tied = [i for i in order if sel.areas[top] - sel.areas[i] <= eps]
    if len(tied) == 1:
        sel.selected = [top]
        return sel
    if all(congruent(parts[i], parts[top], tol) for i in tied[1:]):
        sel.selected = [top]
        sel.duplicates = tied[1:]
        return sel
    sel.problem = Problem("EQUAL_AREA_PARTS", None, count=len(tied))
    return sel
