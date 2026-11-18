# SPDX-License-Identifier: GPL-3.0-or-later
"""Plane geometry helpers in float64. No Blender imports."""

import math


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def length(a):
    return math.hypot(a[0], a[1])


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def turn_angle(p_prev, p, p_next):
    """Signed turning angle (radians) at ``p``; positive turns left."""
    d0 = sub(p, p_prev)
    d1 = sub(p_next, p)
    return math.atan2(cross(d0, d1), dot(d0, d1))


def signed_area(points):
    area = 0.0
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return 0.5 * area


def point_line_distance(p, a, b):
    d = sub(b, a)
    lng = length(d)
    if lng == 0.0:
        return distance(p, a)
    return abs(cross(d, sub(p, a))) / lng


def _solve3(m, v):
    """Gaussian elimination with partial pivoting. Returns None if singular."""
    a = [list(m[0]) + [v[0]], list(m[1]) + [v[1]], list(m[2]) + [v[2]]]
    scale = max(abs(x) for row in m for x in row) or 1.0
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(a[r][col]))
        if abs(a[piv][col]) <= 1e-14 * scale:
            return None
        a[col], a[piv] = a[piv], a[col]
        for r in range(3):
            if r != col:
                f = a[r][col] / a[col][col]
                for c in range(col, 4):
                    a[r][c] -= f * a[col][c]
    return [a[i][3] / a[i][i] for i in range(3)]


class CircleFit:
    __slots__ = ("cx", "cy", "radius", "max_dev", "rms_dev", "iterations")

    def __init__(self, cx, cy, radius, max_dev, rms_dev, iterations):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.max_dev = max_dev
        self.rms_dev = rms_dev
        self.iterations = iterations

    @property
    def center(self):
        return (self.cx, self.cy)


def _residuals(points, cx, cy, r):
    res = [math.hypot(x - cx, y - cy) - r for x, y in points]
    max_dev = max(abs(e) for e in res)
    rms = math.sqrt(sum(e * e for e in res) / len(res))
    return max_dev, rms


def fit_circle(points, max_iterations=50):
    """Algebraic (Kasa) fit on centred data, refined by Gauss-Newton.

    Returns ``CircleFit`` or ``None`` when the points are (nearly) collinear.
    """
    n = len(points)
    if n < 3:
        return None
    mx = sum(p[0] for p in points) / n
    my = sum(p[1] for p in points) / n
    pts = [(x - mx, y - my) for x, y in points]
    suu = svv = suv = suuu = svvv = suvv = svuu = 0.0
    for u, v in pts:
        uu = u * u
        vv = v * v
        suu += uu
        svv += vv
        suv += u * v
        suuu += uu * u
        svvv += vv * v
        suvv += u * vv
        svuu += v * uu
    # Kasa: minimise sum (u^2 + v^2 + D u + E v + F)^2 ; centred so Su = Sv = 0.
    sol = _solve3(
        [[suu, suv, 0.0], [suv, svv, 0.0], [0.0, 0.0, float(n)]],
        [-(suuu + suvv), -(svuu + svvv), -(suu + svv)],
    )
    if sol is None:
        return None
    d, e, f = sol
    a = -0.5 * d
    b = -0.5 * e
    r2 = a * a + b * b - f
    if r2 <= 0.0:
        return None
    r = math.sqrt(r2)
    spread = math.sqrt((suu + svv) / n)
    if spread == 0.0 or r > 1e7 * spread:
        return None
    it = 0
    for it in range(1, max_iterations + 1):
        jtj = [[0.0] * 3 for _ in range(3)]
        jtr = [0.0, 0.0, 0.0]
        for u, v in pts:
            du = u - a
            dv = v - b
            di = math.hypot(du, dv)
            if di == 0.0:
                continue
            res = di - r
            j = (-du / di, -dv / di, -1.0)
            for p in range(3):
                jtr[p] += j[p] * res
                for q in range(3):
                    jtj[p][q] += j[p] * j[q]
        step = _solve3(jtj, [-x for x in jtr])
        if step is None:
            break
        a += step[0]
        b += step[1]
        r += step[2]
        if max(abs(s) for s in step) <= 1e-15 * max(r, spread):
            break
    if r <= 0.0:
        return None
    max_dev, rms = _residuals(pts, a, b, r)
    return CircleFit(a + mx, b + my, r, max_dev, rms, it)


def segments_intersect(p1, p2, p3, p4, eps):
    """True if closed segments p1p2 and p3p4 intersect (touching counts)."""
    d1 = sub(p2, p1)
    d2 = sub(p4, p3)
    denom = cross(d1, d2)
    w = sub(p3, p1)
    l1 = length(d1)
    l2 = length(d2)
    if abs(denom) <= eps * max(l1 * l2, 1e-300):
        # Parallel: intersect only if collinear and overlapping.
        if point_line_distance(p3, p1, p2) > eps:
            return False
        if l1 == 0.0:
            return False
        t3 = dot(sub(p3, p1), d1) / (l1 * l1)
        t4 = dot(sub(p4, p1), d1) / (l1 * l1)
        lo, hi = min(t3, t4), max(t3, t4)
        tol = eps / l1
        return hi >= -tol and lo <= 1.0 + tol
    t = cross(w, d2) / denom
    u = cross(w, d1) / denom
    tol1 = eps / l1 if l1 else 0.0
    tol2 = eps / l2 if l2 else 0.0
    return -tol1 <= t <= 1.0 + tol1 and -tol2 <= u <= 1.0 + tol2


def point_in_polygon(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xc = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if xc > x:
                inside = not inside
    return inside
