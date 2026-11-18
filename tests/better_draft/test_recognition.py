# SPDX-License-Identifier: GPL-3.0-or-later
"""Unit tests for the pure recognition core. Runs with any Python 3.11+:

    python -I tests/better_draft/test_recognition.py
"""

import math
import os
import sys
import unittest

SRC = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
sys.path.insert(0, SRC)

from better_draft import geometry2d as g2  # noqa: E402
from better_draft import recognition as rc  # noqa: E402


def arc_points(cx, cy, r, a0, sweep, s, include_end=True):
    n = s + 1 if include_end else s
    return [
        (cx + r * math.cos(math.radians(a0 + sweep * k / s)), cy + r * math.sin(math.radians(a0 + sweep * k / s)))
        for k in range(n)
    ]


def rounded_rect(w, h, r, s):
    pts = []
    for cx, cy, a0 in ((w - r, h - r, 0), (r, h - r, 90), (r, r, 180), (w - r, r, 270)):
        pts += arc_points(cx, cy, r, a0, 90, s)
    return pts


def kinds(res):
    return [e.kind for e in res.entities]


class CircleFitTests(unittest.TestCase):
    def test_exact_circle(self):
        pts = arc_points(3.0, -2.0, 7.5, 10, 50, 5)
        fit = g2.fit_circle(pts)
        self.assertAlmostEqual(fit.cx, 3.0, places=9)
        self.assertAlmostEqual(fit.cy, -2.0, places=9)
        self.assertAlmostEqual(fit.radius, 7.5, places=9)
        self.assertLess(fit.max_dev, 1e-9)

    def test_collinear_returns_none(self):
        self.assertIsNone(g2.fit_circle([(0, 0), (1, 0), (2, 0), (3, 0)]))

    def test_far_from_origin(self):
        pts = [(1e6 + x, 2e5 + y) for x, y in arc_points(0, 0, 5, 0, 90, 8)]
        fit = g2.fit_circle(pts)
        self.assertAlmostEqual(fit.radius, 5.0, places=6)


class LoopTests(unittest.TestCase):
    def test_rounded_rect_by_segments(self):
        expected = {2: 0, 3: 0, 4: 4, 6: 4, 8: 4, 16: 4, 32: 4}
        for s, arcs in expected.items():
            res = rc.analyze_loop(rounded_rect(40, 20, 5, s))
            self.assertFalse(res.problems)
            self.assertEqual(kinds(res).count("ARC"), arcs, s)
            for e in res.entities:
                if e.kind == "ARC":
                    self.assertAlmostEqual(e.radius, 5.0, places=9)
                    self.assertAlmostEqual(e.sweep_deg, 90.0, places=6)
                    self.assertEqual(e.candidate.segments, s)

    def test_lines_join_arcs_exactly(self):
        res = rc.analyze_loop(rounded_rect(40, 20, 5, 8))
        ents = res.entities
        for k, e in enumerate(ents):
            nxt = ents[(k + 1) % len(ents)]
            self.assertEqual(e.end, nxt.start)
        self.assertTrue(all(t < 1e-6 for t in res.tangency_deg))

    def test_circle(self):
        for n in (8, 32, 64):
            res = rc.analyze_loop(arc_points(5, 5, 10, 0, 360, n, include_end=False))
            self.assertEqual(kinds(res), ["CIRCLE"], n)
            self.assertAlmostEqual(res.entities[0].radius, 10.0, places=9)

    def test_circle_min_segments(self):
        hexagon = arc_points(0, 0, 10, 0, 360, 6, include_end=False)
        res = rc.analyze_loop(hexagon)
        self.assertEqual(kinds(res), ["LINE"] * 6)
        self.assertEqual(res.candidates[0].reason, "below_circle_min_segments")
        res = rc.analyze_loop(hexagon, params=rc.Params(circle_min_segments=6))
        self.assertEqual(kinds(res), ["CIRCLE"])

    def test_circle_clockwise_input(self):
        pts = list(reversed(arc_points(0, 0, 4, 0, 360, 24, include_end=False)))
        self.assertEqual(kinds(rc.analyze_loop(pts)), ["CIRCLE"])

    def test_slot(self):
        pts = arc_points(20, 0, 4, -90, 180, 8) + arc_points(0, 0, 4, 90, 180, 8)
        res = rc.analyze_loop(pts)
        self.assertEqual(sorted(kinds(res)), ["ARC", "ARC", "LINE", "LINE"])
        self.assertTrue(all(t < 1e-6 for t in res.tangency_deg))

    def test_subdivided_line_is_one_line(self):
        pts = [(4.0 * k, 0.0) for k in range(10)] + [(40, 0), (40, 20), (0, 20)]
        res = rc.analyze_loop(pts)
        self.assertEqual(kinds(res), ["LINE"] * 4)
        bottom = [e for e in res.entities if abs(e.start[1]) < 1e-12 and abs(e.end[1]) < 1e-12]
        self.assertEqual(len(bottom), 1)
        self.assertEqual(len(bottom[0].orig_edges), 10)

    def test_mixed_arc_then_chamfer(self):
        pts = [(0, 0), (30, 0)] + arc_points(30, 5, 5, -90, 90, 8)[1:] + [(30, 15), (0, 15)]
        res = rc.analyze_loop(pts)
        arcs = [e for e in res.entities if e.kind == "ARC"]
        self.assertEqual(len(arcs), 1)
        self.assertEqual(arcs[0].candidate.segments, 8)

    def test_s_curve_inflection(self):
        a = arc_points(0, 10, 10, -90, 90, 4)
        b = arc_points(16, 10, 6, 180, -90, 4)[1:]
        pts = a + b + [(16, 30), (0, 30), (-10, 30), (-10, 0)]
        res = rc.analyze_loop(pts)
        arcs = [e for e in res.entities if e.kind == "ARC"]
        self.assertEqual(sorted(round(e.radius, 6) for e in arcs), [6.0, 10.0])
        self.assertEqual({a.ccw for a in arcs}, {True, False})
        self.assertTrue(all(e.candidate.segments == 4 for e in arcs))

    def test_dxf_angles_are_counter_clockwise(self):
        res = rc.analyze_loop(list(reversed(rounded_rect(40, 20, 5, 8))))
        for e in res.entities:
            if e.kind == "ARC":
                a0, a1 = e.dxf_angles
                self.assertAlmostEqual((a1 - a0) % 360.0, 90.0, places=6)

    def test_degenerate(self):
        res = rc.analyze_loop([(0, 0), (1, 0), (2, 0)])
        self.assertEqual([p.code for p in res.problems], ["DEGENERATE_LOOP"])


class ManualModeTests(unittest.TestCase):
    def setUp(self):
        self.pts = rounded_rect(40, 20, 5, 3)  # 3-segment corners, 16 edges
        self.n = len(self.pts)

    def modes(self, mapping):
        m = [rc.MODE_AUTO] * self.n
        for e, v in mapping.items():
            m[e] = v
        return m

    def test_facets_stay_lines_by_default(self):
        self.assertNotIn("ARC", kinds(rc.analyze_loop(self.pts)))

    def test_forced_arc(self):
        res = rc.analyze_loop(self.pts, self.modes({0: 1, 1: 1, 2: 1}))
        arcs = [e for e in res.entities if e.kind == "ARC"]
        self.assertEqual(len(arcs), 1)
        self.assertEqual(arcs[0].candidate.manual, "arc")
        self.assertAlmostEqual(arcs[0].radius, 5.0, places=9)

    def test_forced_arc_one_edge_marks_whole_candidate(self):
        res = rc.analyze_loop(self.pts, self.modes({1: 1}))
        arcs = [e for e in res.entities if e.kind == "ARC"]
        self.assertEqual(len(arcs), 1)
        self.assertEqual(arcs[0].candidate.segments, 3)

    def test_lines_beat_arc(self):
        res = rc.analyze_loop(self.pts, self.modes({0: 1, 1: 2, 2: 1}))
        # One "lines" edge turns the whole run into lines; its arc marks are ignored.
        self.assertNotIn("ARC", kinds(res))
        self.assertFalse(res.problems)
        self.assertIn("manual_lines", [c.reason for c in res.candidates])

    def test_forced_lines_on_auto_arc(self):
        pts = rounded_rect(40, 20, 5, 8)
        modes = [0] * len(pts)
        modes[3] = rc.MODE_LINES
        res = rc.analyze_loop(pts, modes)
        self.assertEqual(kinds(res).count("ARC"), 3)
        self.assertFalse(res.problems)

    def test_forced_arc_out_of_tolerance(self):
        # Mark a straight side plus a corner as arc: cannot fit one circle.
        modes = self.modes({e: 1 for e in range(0, 5)})
        res = rc.analyze_loop(self.pts, modes)
        self.assertEqual([p.code for p in res.problems], ["FORCED_ARC_OUT_OF_TOLERANCE"])
        self.assertEqual(res.entities, [])

    def test_forced_single_edge_on_line(self):
        pts = [(0, 0), (40, 0), (40, 20), (0, 20)]
        res = rc.analyze_loop(pts, [1, 0, 0, 0])
        self.assertEqual([p.code for p in res.problems], ["FORCED_ARC_SINGLE_EDGE"])


class RegionTests(unittest.TestCase):
    def test_outer_and_hole_roles(self):
        outer = [(0, 0), (60, 0), (60, 40), (0, 40)]
        hole = arc_points(30, 20, 8, 0, 360, 32, include_end=False)
        res = rc.analyze_region([outer, hole])
        self.assertFalse(res.problems)
        self.assertEqual(res.roles, ["OUTER", "INNER"])
        self.assertEqual(kinds(res.loops[1]), ["CIRCLE"])

    def test_self_intersection(self):
        bow = [(0, 0), (10, 10), (10, 0), (0, 10)]
        res = rc.analyze_region([bow])
        self.assertEqual([p.code for p in res.problems], ["LOOPS_INTERSECT"])

    def test_loops_crossing(self):
        a = [(0, 0), (10, 0), (10, 10), (0, 10)]
        b = [(5, 5), (15, 5), (15, 15), (5, 15)]
        self.assertEqual([p.code for p in rc.analyze_region([a, b]).problems], ["LOOPS_INTERSECT"])

    def test_two_islands_refused(self):
        a = [(0, 0), (10, 0), (10, 10), (0, 10)]
        b = [(20, 0), (30, 0), (30, 10), (20, 10)]
        self.assertEqual([p.code for p in rc.analyze_region([a, b]).problems], ["MULTIPLE_OUTER"])

    def test_island_in_hole_refused(self):
        a = [(0, 0), (30, 0), (30, 30), (0, 30)]
        b = [(5, 5), (25, 5), (25, 25), (5, 25)]
        c = [(10, 10), (20, 10), (20, 20), (10, 20)]
        self.assertEqual([p.code for p in rc.analyze_region([a, b, c]).problems], ["NESTED_ISLAND"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
