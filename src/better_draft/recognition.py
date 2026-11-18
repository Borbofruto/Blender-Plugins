# SPDX-License-Identifier: GPL-3.0-or-later
"""Arc and circle recognition on closed 2D loops (millimetres, float64).

Pure Python: no Blender imports, so it can be tested outside Blender and
reused by a later review window. Input loops are lists of (x, y) points; edge
``i`` goes from point ``i`` to point ``i + 1`` (cyclic). Optional per-edge
modes use the values of the ``better_draft_arc_mode`` attribute.
"""

import math

from . import geometry2d as g2

MODE_AUTO = 0
MODE_ARC = 1
MODE_LINES = 2

DUPLICATE_EPS_MM = 1e-7


class Params:
    """Recognition parameters. Defaults are provisional until calibrated."""

    __slots__ = (
        "confidence_threshold",
        "min_segments",
        "straight_tolerance_deg",
        "fit_tolerance_mm",
        "corner_limit_deg",
        "count_scale",
        "regularity_span",
        "chord_ratio_limit",
    )

    def __init__(
        self,
        confidence_threshold=0.7,
        min_segments=4,
        straight_tolerance_deg=0.1,
        fit_tolerance_mm=0.01,
        corner_limit_deg=65.0,
        count_scale=1.5,
        regularity_span=0.5,
        chord_ratio_limit=2.0,
    ):
        self.confidence_threshold = float(confidence_threshold)
        self.min_segments = int(min_segments)
        self.straight_tolerance_deg = float(straight_tolerance_deg)
        self.fit_tolerance_mm = float(fit_tolerance_mm)
        self.corner_limit_deg = float(corner_limit_deg)
        self.count_scale = float(count_scale)
        self.regularity_span = float(regularity_span)
        self.chord_ratio_limit = float(chord_ratio_limit)

    def as_dict(self):
        return {name: getattr(self, name) for name in self.__slots__}


class Problem:
    """A refusal reason. ``code`` is stable; ``details`` feeds UI messages."""

    __slots__ = ("code", "loop", "details")

    def __init__(self, code, loop=None, **details):
        self.code = code
        self.loop = loop
        self.details = details

    def __repr__(self):
        return "Problem(%r, loop=%r, %r)" % (self.code, self.loop, self.details)


class Candidate:
    """A run of segments that fits one circle within the fit tolerance."""

    __slots__ = (
        "start",
        "edge_count",
        "is_circle",
        "segments",
        "fit",
        "confidence",
        "components",
        "manual",
        "decision",
        "reason",
        "orig_edges",
        "ccw",
    )

    def __init__(self, start, edge_count, is_circle):
        self.start = start  # cleaned vertex index where the run starts
        self.edge_count = edge_count  # cleaned edges covered
        self.is_circle = is_circle
        self.segments = 0  # chords after straight merging
        self.fit = None
        self.confidence = 0.0
        self.components = {}
        self.manual = None  # None, "arc" or "lines"
        self.decision = None  # "arc", "circle" or "lines"
        self.reason = ""
        self.orig_edges = []
        self.ccw = True


class Line:
    __slots__ = ("start", "end", "orig_edges")
    kind = "LINE"

    def __init__(self, start, end, orig_edges):
        self.start = start
        self.end = end
        self.orig_edges = orig_edges


class Arc:
    __slots__ = ("center", "radius", "start", "end", "ccw", "candidate")
    kind = "ARC"

    def __init__(self, center, radius, start, end, ccw, candidate):
        self.center = center
        self.radius = radius
        self.start = start  # traversal start point (on the circle)
        self.end = end
        self.ccw = ccw
        self.candidate = candidate

    def _angle(self, p):
        return math.degrees(math.atan2(p[1] - self.center[1], p[0] - self.center[0])) % 360.0

    @property
    def dxf_angles(self):
        """(start, end) in degrees, counter-clockwise, as DXF ARC expects."""
        if self.ccw:
            return self._angle(self.start), self._angle(self.end)
        return self._angle(self.end), self._angle(self.start)

    @property
    def sweep_deg(self):
        a0, a1 = self.dxf_angles
        sweep = (a1 - a0) % 360.0
        return 360.0 if sweep == 0.0 else sweep


class Circle:
    __slots__ = ("center", "radius", "candidate")
    kind = "CIRCLE"

    def __init__(self, center, radius, candidate):
        self.center = center
        self.radius = radius
        self.candidate = candidate


class LoopResult:
    __slots__ = (
        "entities",
        "candidates",
        "problems",
        "max_gap",
        "tangency_deg",
        "vertex_count",
        "reduced_count",
    )

    def __init__(self):
        self.entities = []
        self.candidates = []
        self.problems = []
        self.max_gap = 0.0
        self.tangency_deg = []  # (vertex index, angle) at line/arc joins
        self.vertex_count = 0
        self.reduced_count = 0


# ---------------------------------------------------------------------------
# Confidence


def _cv(values):
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    if mean == 0.0:
        return float("inf")
    var = sum((v - mean) ** 2 for v in values) / n
    return math.sqrt(var) / abs(mean)


def _clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def confidence_components(segments, chord_lengths, interior_turns, max_dev, params):
    """Return (confidence, components). See docs for the calibrated formula."""
    span = params.regularity_span
    c_count = 1.0 - math.exp(-(segments - 1) / params.count_scale) if segments > 1 else 0.0
    cv_turn = _cv([abs(t) for t in interior_turns]) if len(interior_turns) >= 2 else 0.0
    cv_len = _cv(chord_lengths)
    c_turn = _clamp01(1.0 - cv_turn / span)
    c_len = _clamp01(1.0 - cv_len / span)
    tol = params.fit_tolerance_mm
    c_dev = _clamp01(1.0 - (max_dev / tol) ** 2) if tol > 0.0 else (1.0 if max_dev == 0.0 else 0.0)
    conf = c_count * c_turn * c_len * c_dev
    return conf, {
        "count": c_count,
        "turn": c_turn,
        "length": c_len,
        "deviation": c_dev,
        "cv_turn": cv_turn,
        "cv_length": cv_len,
    }


# ---------------------------------------------------------------------------
# Loop preparation


def _clean(points, modes):
    """Drop repeated points. Returns (pts, groups, cmodes, orig_index).

    ``groups[j]`` lists the original edge indices merged into cleaned edge j.
    """
    n = len(points)
    keep = []
    for i in range(n):
        if keep and g2.distance(points[i], points[keep[-1]]) <= DUPLICATE_EPS_MM:
            continue
        keep.append(i)
    while len(keep) > 1 and g2.distance(points[keep[-1]], points[keep[0]]) <= DUPLICATE_EPS_MM:
        keep.pop()
    m = len(keep)
    pts = [points[i] for i in keep]
    groups = []
    for j in range(m):
        a = keep[j]
        b = keep[j + 1] if j + 1 < m else keep[0] + n
        groups.append([k % n for k in range(a, b)])
    cmodes = []
    for grp in groups:
        values = [modes[k] for k in grp] if modes is not None else [MODE_AUTO]
        if MODE_LINES in values:
            cmodes.append(MODE_LINES)
        elif MODE_ARC in values:
            cmodes.append(MODE_ARC)
        else:
            cmodes.append(MODE_AUTO)
    return pts, groups, cmodes, keep


def _turns(pts):
    m = len(pts)
    return [g2.turn_angle(pts[i - 1], pts[i], pts[(i + 1) % m]) for i in range(m)]


def _merge_straight(pts, turns, params):
    """Indices of vertices kept after absorbing subdivision vertices."""
    m = len(pts)
    straight = math.radians(params.straight_tolerance_deg)
    tol = params.fit_tolerance_mm
    start = max(range(m), key=lambda i: abs(turns[i]))
    kept = [start]
    k = start
    steps = 0
    while True:
        j = (k + 1) % m
        while j != start and abs(turns[j]) < straight:
            nxt = (j + 1) % m
            before = turns[(j - 1) % m]
            after = turns[nxt]
            if abs(before) >= straight and abs(after) >= straight and before * after < 0.0:
                # Inflection between two opposite arcs: keep it as a junction.
                break
            a = pts[k]
            b = pts[nxt]
            t = (k + 1) % m
            ok = True
            while True:
                if g2.point_line_distance(pts[t], a, b) > tol:
                    ok = False
                    break
                if t == j:
                    break
                t = (t + 1) % m
            if not ok:
                break
            j = nxt
        if j == start:
            break
        kept.append(j)
        k = j
        steps += 1
        if steps > m:
            break
    return kept


# ---------------------------------------------------------------------------
# Candidate detection


def _detect(pts, kept, params):
    """Return candidate spans as (start_kept_pos, end_kept_pos, is_circle).

    Positions are unrolled indices into ``kept`` (end may exceed len(kept)).
    """
    M = len(kept)
    P = [pts[i] for i in kept]
    if M < 3:
        return []
    T = _turns(P)
    corner = math.radians(params.corner_limit_deg)
    tol = params.fit_tolerance_mm
    sign = [1 if t > 0 else -1 for t in T]
    chord = [g2.distance(P[q], P[(q + 1) % M]) for q in range(M)]
    ratio = params.chord_ratio_limit

    def even(*lengths):
        return max(lengths) <= ratio * min(lengths)

    # A vertex can sit inside an arc if its turn is below the corner limit and
    # its two chords have comparable length (bevel and circle chords are even).
    smooth = [0.0 < abs(T[q]) <= corner and even(chord[q - 1], chord[q]) for q in range(M)]

    def compat(q):
        q0 = q % M
        q1 = (q + 1) % M
        if not (smooth[q0] and smooth[q1] and sign[q0] == sign[q1]):
            return False
        if M < 4:
            return False
        if not even(chord[(q - 1) % M], chord[q0], chord[q1]):
            return False
        quad = [P[(q - 1) % M], P[q0], P[q1], P[(q + 2) % M]]
        fit = g2.fit_circle(quad)
        return fit is not None and fit.max_dev <= tol

    comp = [compat(q) for q in range(M)]

    def fits(span_pos):
        fit = g2.fit_circle([P[p % M] for p in span_pos])
        return fit is not None and fit.max_dev <= tol

    if all(comp):
        whole = list(range(M))
        if fits(whole):
            return [(0, M, True)]
        start_q = 0
        runs = [list(range(M))]
    else:
        start_q = next(q for q in range(M) if not comp[(q - 1) % M])
        runs = []
        q = start_q
        end_q = start_q + M
        while q < end_q:
            if not smooth[q % M]:
                q += 1
                continue
            run = [q]
            while comp[q % M] and q + 1 < end_q:
                q += 1
                run.append(q)
            runs.append(run)
            q += 1

    spans = []
    for run in runs:
        a = run[0] - 1
        b = run[-1] + 1
        if all(comp) and len(run) == M:
            a, b = 0, M  # closed run that failed the global fit: split it
        verts = list(range(a, b + 1))
        if fits(verts):
            spans.append((a, b))
            continue
        i = 0
        while i <= len(verts) - 3:
            j = i + 2
            while j + 1 < len(verts) and fits(verts[i : j + 2]):
                j += 1
            spans.append((verts[i], verts[j]))
            i = j
    # Resolve overlaps: longer spans win; a shorter span keeps its longest
    # non-overlapping piece if that piece still has two or more chords.
    taken = set()
    result = []
    for a, b in sorted(spans, key=lambda s: (-(s[1] - s[0]), s[0])):
        free = [p for p in range(a, b) if p % M not in taken]
        best = None
        run_start = None
        prev = None
        for p in free + [None]:
            if p is not None and prev is not None and p == prev + 1:
                prev = p
                continue
            if run_start is not None:
                piece = (run_start, prev + 1)
                if best is None or piece[1] - piece[0] > best[1] - best[0]:
                    best = piece
            run_start = p
            prev = p
        if best is not None and best[1] - best[0] >= 2:
            result.append(best)
            taken.update(p % M for p in range(best[0], best[1]))
    result.sort()
    return [(a, b, False) for a, b in result]


def _span_points(pts, start, count):
    m = len(pts)
    return [pts[(start + k) % m] for k in range(count + 1)]


def _make_candidate(pts, kept, turns_c, groups, a, b, is_circle, params):
    m = len(pts)
    M = len(kept)
    start = kept[a % M]
    if is_circle:
        count = m
        chords_pos = list(range(M))
        P_pts = [pts[kept[q]] for q in range(M)]
        interior = [g2.turn_angle(P_pts[q - 1], P_pts[q], P_pts[(q + 1) % M]) for q in range(M)]
        lengths = [g2.distance(P_pts[q], P_pts[(q + 1) % M]) for q in range(M)]
        fit_pts = [pts[i] for i in range(m)]
        segments = M
    else:
        end = kept[b % M]
        count = (end - start) % m
        if count == 0:
            count = m
        P_pts = [pts[kept[q % M]] for q in range(a, b + 1)]
        lengths = [g2.distance(P_pts[i], P_pts[i + 1]) for i in range(len(P_pts) - 1)]
        interior = [
            g2.turn_angle(P_pts[i - 1], P_pts[i], P_pts[i + 1]) for i in range(1, len(P_pts) - 1)
        ]
        fit_pts = _span_points(pts, start, count)
        segments = b - a
    cand = Candidate(start, count, is_circle)
    cand.segments = segments
    cand.fit = g2.fit_circle(fit_pts)
    max_dev = cand.fit.max_dev if cand.fit else float("inf")
    # Span endpoints are the tangent points (half turn); ``interior`` holds
    # only the vertices strictly between them.
    cand.confidence, cand.components = confidence_components(
        segments, lengths, interior, max_dev, params
    )
    cand.ccw = sum(interior) > 0.0
    cand.orig_edges = [e for k in range(count) for e in groups[(start + k) % m]]
    return cand


def _edges_of(start, count, m):
    return [(start + k) % m for k in range(count)]


# ---------------------------------------------------------------------------
# Public API


def analyze_loop(points, modes=None, params=None, loop_index=None):
    """Recognise arcs/circles in one closed loop. Returns ``LoopResult``."""
    params = params or Params()
    res = LoopResult()
    pts, groups, cmodes, keep = _clean([tuple(map(float, p)) for p in points], modes)
    m = len(pts)
    res.vertex_count = m
    if m < 3 or abs(g2.signed_area(pts)) <= DUPLICATE_EPS_MM:
        res.problems.append(Problem("DEGENERATE_LOOP", loop_index, vertices=m))
        return res
    turns_c = _turns(pts)
    for i, t in enumerate(turns_c):
        if abs(abs(t) - math.pi) <= 1e-9:
            res.problems.append(Problem("SELF_OVERLAP", loop_index, vertex=keep[i]))
            return res
    kept = _merge_straight(pts, turns_c, params)
    res.reduced_count = len(kept)
    tol = params.fit_tolerance_mm

    spans = _detect(pts, kept, params)
    cands = [_make_candidate(pts, kept, turns_c, groups, a, b, c, params) for a, b, c in spans]
    cands = [c for c in cands if c.fit is not None and (c.confidence > 0.0 or _has_mode(c, cmodes, m))]

    # Manual modes per candidate: "lines" beats "arc" beats automatic.
    edge_owner = {}
    for idx, c in enumerate(cands):
        edges = _edges_of(c.start, c.edge_count, m)
        values = {cmodes[e] for e in edges}
        if MODE_LINES in values:
            c.manual = "lines"
        elif MODE_ARC in values:
            c.manual = "arc"
        for e in edges:
            edge_owner[e] = idx

    # Forced-arc extents: maximal MODE_ARC runs, merged with overlapping
    # candidates that are not marked "lines".
    arc_edges = [e for e in range(m) if cmodes[e] == MODE_ARC]
    forced = []
    if arc_edges:
        covered = set()
        for e0 in arc_edges:
            if e0 in covered:
                continue
            ext = {e0}
            frontier = [e0]
            while frontier:
                e = frontier.pop()
                for nb in ((e - 1) % m, (e + 1) % m):
                    if nb in ext:
                        continue
                    if cmodes[nb] == MODE_ARC:
                        ext.add(nb)
                        frontier.append(nb)
                if e in edge_owner:
                    c = cands[edge_owner[e]]
                    if c.manual != "lines":
                        for ce in _edges_of(c.start, c.edge_count, m):
                            if ce not in ext:
                                ext.add(ce)
                                frontier.append(ce)
            # Only keep MODE_ARC edges that are not inside a "lines" candidate.
            ext = {e for e in ext if not (e in edge_owner and cands[edge_owner[e]].manual == "lines")}
            covered |= ext
            if ext:
                forced.append(ext)

    final = []  # (start, count, candidate, is_circle)
    used = set()
    for ext in forced:
        orig = sorted({o for e in ext for o in groups[e]})
        if len(ext) == m:
            start, count, is_circle = 0, m, True
        else:
            start = next(e for e in ext if (e - 1) % m not in ext)
            count = len(ext)
            is_circle = False
            # The extent must be contiguous.
            if any((start + k) % m not in ext for k in range(count)):
                res.problems.append(Problem("FORCED_ARC_SPLIT", loop_index, edges=orig))
                continue
        if count < 2:
            res.problems.append(Problem("FORCED_ARC_SINGLE_EDGE", loop_index, edges=orig))
            continue
        fit_pts = [pts[i] for i in range(m)] if is_circle else _span_points(pts, start, count)
        fit = g2.fit_circle(fit_pts)
        inner = [turns_c[(start + k) % m] for k in range(1, count)] if not is_circle else turns_c
        same_sign = inner and (all(t >= 0 for t in inner) or all(t <= 0 for t in inner))
        if fit is None or fit.max_dev > tol or not same_sign:
            res.problems.append(
                Problem(
                    "FORCED_ARC_OUT_OF_TOLERANCE",
                    loop_index,
                    edges=orig,
                    deviation_mm=(fit.max_dev if fit else None),
                    tolerance_mm=tol,
                )
            )
            continue
        # Reuse a covering candidate's statistics when it matches exactly.
        cand = None
        for c in cands:
            if c.start == start and c.edge_count == count:
                cand = c
        if cand is None:
            cand = Candidate(start, count, is_circle)
            if is_circle:
                lengths = [g2.distance(pts[i], pts[(i + 1) % m]) for i in range(m)]
            else:
                lengths = [g2.distance(fit_pts[i], fit_pts[i + 1]) for i in range(count)]
            cand.segments = count
            cand.fit = fit
            cand.confidence, cand.components = confidence_components(
                count, lengths, list(inner), fit.max_dev, params
            )
            cand.ccw = sum(inner) > 0.0
            cand.orig_edges = orig
            cands.append(cand)
        cand.manual = "arc"
        cand.decision = "circle" if is_circle else "arc"
        cand.reason = "manual_arc"
        final.append((start, count, cand, is_circle))
        used.update(_edges_of(start, count, m))

    for c in cands:
        if c.decision is not None:
            continue
        edges = _edges_of(c.start, c.edge_count, m)
        if c.manual == "lines":
            c.decision = "lines"
            c.reason = "manual_lines"
        elif any(e in used for e in edges):
            c.decision = "lines"
            c.reason = "superseded"
        elif c.manual == "arc":
            # Marked edges inside this candidate were consumed by an extent
            # that failed; already reported as a problem.
            c.decision = "lines"
            c.reason = "manual_arc_failed"
        elif c.segments < params.min_segments:
            c.decision = "lines"
            c.reason = "below_min_segments"
        elif c.confidence < params.confidence_threshold:
            c.decision = "lines"
            c.reason = "low_confidence"
        else:
            c.decision = "circle" if c.is_circle else "arc"
            c.reason = "auto"
            final.append((c.start, c.edge_count, c, c.is_circle))
            used.update(edges)
    res.candidates = [c for c in cands if c.reason != "superseded" or c.manual]
    if res.problems:
        return res
    _assemble(res, pts, groups, kept, final, m)
    return res


def _has_mode(c, cmodes, m):
    return any(cmodes[e] != MODE_AUTO for e in _edges_of(c.start, c.edge_count, m))


def _project(fit, p):
    dx = p[0] - fit.cx
    dy = p[1] - fit.cy
    d = math.hypot(dx, dy)
    return (fit.cx + fit.radius * dx / d, fit.cy + fit.radius * dy / d)


def _assemble(res, pts, groups, kept, final, m):
    for start, count, cand, is_circle in final:
        if is_circle:
            res.entities.append(Circle(cand.fit.center, cand.fit.radius, cand))
            return
    arc_at = {start: (start, count, cand) for start, count, cand, _ in final}
    arc_edges = set()
    for start, count, _ in arc_at.values():
        arc_edges.update(_edges_of(start, count, m))
    breaks = set(kept)
    for start, count, _ in arc_at.values():
        breaks.add(start)
        breaks.add((start + count) % m)
    # Begin the walk at a break vertex.
    first = min(breaks)
    items = []  # ("arc", start, count, cand) or ("line", a, b)
    i = first
    walked = 0
    while walked < m:
        if i in arc_at:
            start, count, cand = arc_at[i]
            items.append(("arc", start, count, cand))
            i = (i + count) % m
            walked += count
            continue
        j = (i + 1) % m
        steps = 1
        while j not in breaks and steps < m:
            j = (j + 1) % m
            steps += 1
        items.append(("line", i, j))
        i = j
        walked += steps
    # Junction points.
    n_items = len(items)
    ends = []
    for it in items:
        if it[0] == "arc":
            _, start, count, cand = it
            s = _project(cand.fit, pts[start])
            e = _project(cand.fit, pts[(start + count) % m])
            ends.append([s, e])
        else:
            ends.append([pts[it[1]], pts[it[2]]])
    for k in range(n_items):
        cur = items[k]
        nxt = items[(k + 1) % n_items]
        if cur[0] == "arc" and nxt[0] == "line":
            ends[(k + 1) % n_items][0] = ends[k][1]
        elif cur[0] == "line" and nxt[0] == "arc":
            ends[k][1] = ends[(k + 1) % n_items][0]
        elif cur[0] == "arc" and nxt[0] == "arc":
            res.max_gap = max(res.max_gap, g2.distance(ends[k][1], ends[(k + 1) % n_items][0]))
    for k, it in enumerate(items):
        s, e = ends[k]
        if it[0] == "arc":
            _, start, count, cand = it
            res.entities.append(Arc(cand.fit.center, cand.fit.radius, s, e, cand.ccw, cand))
        else:
            _, a, b = it
            count = (b - a) % m or m
            orig = [o for q in range(count) for o in groups[(a + q) % m]]
            res.entities.append(Line(s, e, orig))
    # Tangency report at line/arc joins.
    for k in range(n_items):
        cur = res.entities[k]
        nxt = res.entities[(k + 1) % n_items]
        if isinstance(cur, Line) and isinstance(nxt, Arc):
            res.tangency_deg.append(_tangency(cur, nxt, at_start=True))
        elif isinstance(cur, Arc) and isinstance(nxt, Line):
            res.tangency_deg.append(_tangency(nxt, cur, at_start=False))


def _tangency(line, arc, at_start):
    p = arc.start if at_start else arc.end
    rx = p[0] - arc.center[0]
    ry = p[1] - arc.center[1]
    tangent = (-ry, rx) if arc.ccw else (ry, -rx)
    d = g2.sub(line.end, line.start)
    ang = math.degrees(math.atan2(abs(g2.cross(d, tangent)), g2.dot(d, tangent)))
    return min(ang, 180.0 - ang)


# ---------------------------------------------------------------------------
# Region (outer loop + holes)


class RegionResult:
    __slots__ = ("loops", "roles", "problems")

    def __init__(self):
        self.loops = []  # LoopResult per input loop
        self.roles = []  # "OUTER" or "INNER"
        self.problems = []


def _all_segments(loops):
    segs = []
    for li, loop in enumerate(loops):
        n = len(loop)
        for i in range(n):
            segs.append((li, i, n, loop[i], loop[(i + 1) % n]))
    return segs


def find_intersections(loops, eps=1e-9, limit=1):
    """Return up to ``limit`` intersecting edge pairs (loop, edge, loop, edge)."""
    segs = _all_segments(loops)
    scale = 1.0
    for _, _, _, a, b in segs:
        scale = max(scale, abs(a[0]), abs(a[1]))
    eps_abs = eps * scale
    order = sorted(range(len(segs)), key=lambda k: min(segs[k][3][0], segs[k][4][0]))
    active = []
    found = []
    for k in order:
        li, i, n, a, b = segs[k]
        xmin = min(a[0], b[0])
        active = [q for q in active if max(segs[q][3][0], segs[q][4][0]) >= xmin - eps_abs]
        ymin = min(a[1], b[1])
        ymax = max(a[1], b[1])
        for q in active:
            lj, j, nj, c, d = segs[q]
            if max(c[1], d[1]) < ymin - eps_abs or min(c[1], d[1]) > ymax + eps_abs:
                continue
            if li == lj and (j == (i + 1) % n or i == (j + 1) % n):
                continue
            if g2.segments_intersect(a, b, c, d, eps_abs):
                found.append((li, i, lj, j))
                if len(found) >= limit:
                    return found
        active.append(k)
    return found


def analyze_region(loops, modes=None, params=None):
    """Validate nesting and intersections, then recognise every loop."""
    params = params or Params()
    out = RegionResult()
    loops = [[tuple(map(float, p)) for p in loop] for loop in loops]
    if not loops:
        out.problems.append(Problem("NO_LOOP"))
        return out
    hits = find_intersections(loops)
    if hits:
        li, i, lj, j = hits[0]
        out.problems.append(Problem("LOOPS_INTERSECT", li, edge=i, other_loop=lj, other_edge=j))
        return out
    depth = []
    for li, loop in enumerate(loops):
        probe = loop[0]
        depth.append(sum(1 for lj, other in enumerate(loops) if lj != li and g2.point_in_polygon(probe, other)))
    outers = [li for li, d in enumerate(depth) if d == 0]
    if len(outers) != 1:
        out.problems.append(Problem("MULTIPLE_OUTER", None, count=len(outers)))
        return out
    if any(d > 1 for d in depth):
        out.problems.append(Problem("NESTED_ISLAND", None))
        return out
    for li, loop in enumerate(loops):
        lm = modes[li] if modes is not None else None
        lr = analyze_loop(loop, lm, params, loop_index=li)
        out.loops.append(lr)
        out.roles.append("OUTER" if depth[li] == 0 else "INNER")
        out.problems.extend(lr.problems)
    return out
