# SPDX-License-Identifier: GPL-3.0-or-later
"""Extract the planar region of an object's evaluated mesh as 2D loops in mm.

Reads only. The evaluated mesh is a temporary copy released before return;
the object's own mesh and the scene are never modified.
"""

import math

from .constants import ARC_MODE_ATTRIBUTE
from .recognition import Problem


class PartData:
    """One connected group of region faces."""

    __slots__ = ("loops", "modes", "edge_ids", "face_count")

    def __init__(self):
        self.loops = []  # list of [(x_mm, y_mm), ...]
        self.modes = []  # per loop, per edge: 0/1/2
        self.edge_ids = []  # per loop, per edge: evaluated mesh edge index
        self.face_count = 0


class RegionData:
    __slots__ = (
        "parts",
        "origin",
        "axis_u",
        "axis_v",
        "normal",
        "mm_per_unit",
        "flat",
        "reference",
        "face_count",
        "problems",
    )

    def __init__(self):
        self.parts = []
        self.origin = None
        self.axis_u = None
        self.axis_v = None
        self.normal = None
        self.mm_per_unit = 1000.0
        self.flat = True
        self.reference = None  # "all", "active" or "largest"
        self.face_count = 0
        self.problems = []

    # Convenience for single-part callers (calibration, tests).
    @property
    def loops(self):
        return [lp for p in self.parts for lp in p.loops]

    @property
    def modes(self):
        return [m for p in self.parts for m in p.modes]


def _matrix(m):
    return [[float(m[r][c]) for c in range(4)] for r in range(4)]


def _apply(m, co):
    x, y, z = float(co[0]), float(co[1]), float(co[2])
    return (
        m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3],
        m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3],
        m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3],
    )


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    return math.sqrt(_dot(a, a))


def _unit(a):
    n = _norm(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 0.0 else None


def _newell(points):
    nx = ny = nz = 0.0
    n = len(points)
    for i in range(n):
        x0, y0, z0 = points[i]
        x1, y1, z1 = points[(i + 1) % n]
        nx += (y0 - y1) * (z0 + z1)
        ny += (z0 - z1) * (x0 + x1)
        nz += (x0 - x1) * (y0 + y1)
    return (0.5 * nx, 0.5 * ny, 0.5 * nz)  # length = polygon area


def extract_region(obj, depsgraph, scene, tolerance_mm, world_xy=False):
    """Return ``RegionData`` for the object's evaluated mesh."""
    data = RegionData()
    data.mm_per_unit = float(scene.unit_settings.scale_length) * 1000.0
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    try:
        _extract(data, obj, eval_obj, mesh, tolerance_mm, world_xy)
    finally:
        eval_obj.to_mesh_clear()
    return data


def _extract(data, obj, eval_obj, mesh, tolerance_mm, world_xy):
    k = data.mm_per_unit
    tol_bu = tolerance_mm / k
    mw = _matrix(eval_obj.matrix_world)
    verts = [_apply(mw, v.co) for v in mesh.vertices]
    polys = [tuple(p.vertices) for p in mesh.polygons]
    if not polys:
        data.problems.append(Problem("NO_FACES"))
        return
    vec = [_newell([verts[i] for i in p]) for p in polys]
    areas = [_norm(v) for v in vec]

    ref = max(range(len(polys)), key=lambda i: areas[i])
    if areas[ref] == 0.0:
        data.problems.append(Problem("DEGENERATE_FACES"))
        return
    ref_n = _unit(vec[ref])
    aligned = [0.0, 0.0, 0.0]
    for v in vec:
        s = 1.0 if _dot(v, ref_n) >= 0.0 else -1.0
        for c in range(3):
            aligned[c] += s * v[c]
    flat_n = _unit(tuple(aligned)) or ref_n
    used = sorted({i for p in polys for i in p})
    centroid = tuple(sum(verts[i][c] for i in used) / len(used) for c in range(3))
    if all(abs(_dot(_sub(verts[i], centroid), flat_n)) <= tol_bu for i in used):
        data.flat = True
        data.reference = "all"
        region = list(range(len(polys)))
        normal = flat_n
        plane_point = centroid
    else:
        data.flat = False
        active = obj.data.polygons.active if obj.type == "MESH" else -1
        if 0 <= active < len(polys) and len(obj.data.polygons) == len(polys):
            ref = active
            data.reference = "active"
        else:
            data.reference = "largest"
        if areas[ref] == 0.0:
            data.problems.append(Problem("DEGENERATE_FACES"))
            return
        normal = _unit(vec[ref])
        p = polys[ref]
        plane_point = tuple(sum(verts[i][c] for i in p) / len(p) for c in range(3))
        if any(abs(_dot(_sub(verts[i], plane_point), normal)) > tol_bu for i in p):
            data.problems.append(Problem("NOT_PLANAR", None, reference=data.reference))
            return
        region = []
        for fi, poly in enumerate(polys):
            if areas[fi] == 0.0 or _dot(vec[fi], normal) <= 0.0:
                continue
            if all(abs(_dot(_sub(verts[i], plane_point), normal)) <= tol_bu for i in poly):
                region.append(fi)
    data.face_count = len(region)
    # Drawing side: look from the object's +Z (then +Y, +X for plates standing
    # on edge), so a face with a flipped normal is not exported mirrored.
    for col in (2, 1, 0):
        axis = _unit((mw[0][col], mw[1][col], mw[2][col]))
        if axis is not None and abs(_dot(axis, normal)) > 1e-6:
            if _dot(axis, normal) < 0.0:
                normal = (-normal[0], -normal[1], -normal[2])
            break
    data.normal = normal

    # Basis.
    if world_xy:
        if any(abs(verts[i][2] - plane_point[2]) > tol_bu for fi in region for i in polys[fi]):
            data.problems.append(Problem("NOT_PARALLEL_TO_XY"))
            return
        origin = (0.0, 0.0, 0.0)
        u = (1.0, 0.0, 0.0)
        v = (0.0, 1.0, 0.0)
    else:
        obj_origin = (mw[0][3], mw[1][3], mw[2][3])
        d = _dot(_sub(obj_origin, plane_point), normal)
        origin = tuple(obj_origin[c] - d * normal[c] for c in range(3))
        u = None
        for col in (0, 1):
            axis = _unit((mw[0][col], mw[1][col], mw[2][col]))
            if axis is None:
                continue
            proj = _sub(axis, tuple(_dot(axis, normal) * normal[c] for c in range(3)))
            if _norm(proj) > 1e-6:
                u = _unit(proj)
                break
        if u is None:
            u = _unit(_cross(normal, (0.0, 0.0, 1.0))) or (1.0, 0.0, 0.0)
        v = _cross(normal, u)
    data.origin, data.axis_u, data.axis_v = origin, u, v

    edge_index = {}
    for e in mesh.edges:
        a, b = e.vertices
        edge_index[(a, b) if a < b else (b, a)] = e.index
    attr = mesh.attributes.get(ARC_MODE_ATTRIBUTE)
    edge_mode = None
    if attr is not None and attr.domain == "EDGE" and attr.data_type in {"INT", "INT8"}:
        edge_mode = [int(d.value) for d in attr.data]

    # Connected components of region faces (shared edges).
    parent = {fi: fi for fi in region}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    edge_faces = {}
    for fi in region:
        p = polys[fi]
        n = len(p)
        for j in range(n):
            a, b = p[j], p[(j + 1) % n]
            edge_faces.setdefault((a, b) if a < b else (b, a), []).append(fi)
    if any(len(fs) > 2 for fs in edge_faces.values()):
        data.problems.append(Problem("NON_MANIFOLD"))
        return
    for fs in edge_faces.values():
        if len(fs) == 2:
            ra, rb = find(fs[0]), find(fs[1])
            if ra != rb:
                parent[ra] = rb
    groups = {}
    for fi in region:
        groups.setdefault(find(fi), []).append(fi)

    for faces in sorted(groups.values(), key=lambda fs: min(fs)):
        part = PartData()
        part.face_count = len(faces)
        fset = set(faces)
        boundary = [e for e, fs in edge_faces.items() if len(fs) == 1 and fs[0] in fset]
        adj = {}
        for a, b in boundary:
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
        if any(len(x) != 2 for x in adj.values()):
            data.problems.append(Problem("LOOPS_TOUCH"))
            return
        visited = set()
        for start in sorted(adj):
            if start in visited:
                continue
            loop_v = [start]
            visited.add(start)
            prev, cur = start, adj[start][0]
            while cur != start:
                loop_v.append(cur)
                visited.add(cur)
                a, b = adj[cur]
                prev, cur = cur, (b if a == prev else a)
            pts = []
            for i in loop_v:
                w = _sub(verts[i], origin)
                pts.append((_dot(w, u) * k, _dot(w, v) * k))
            ids = []
            modes = []
            n = len(loop_v)
            for j in range(n):
                a, b = loop_v[j], loop_v[(j + 1) % n]
                ei = edge_index.get((a, b) if a < b else (b, a), -1)
                ids.append(ei)
                modes.append(edge_mode[ei] if edge_mode is not None and ei >= 0 else 0)
            part.loops.append(pts)
            part.edge_ids.append(ids)
            part.modes.append(modes)
        data.parts.append(part)
