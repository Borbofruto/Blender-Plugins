# SPDX-License-Identifier: GPL-3.0-or-later
"""Unit tests for loose-part selection and layout (no Blender needed)."""

import math
import os
import sys
import unittest

SRC = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
sys.path.insert(0, SRC)

from better_draft import parts as pt  # noqa: E402
from better_draft import pipeline as pl  # noqa: E402
from better_draft import recognition as rc  # noqa: E402

TOL = 0.01


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def moved(loop, dx, dy, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(c * px - s * py + dx, s * px + c * py + dy) for px, py in loop]


class SelectionTests(unittest.TestCase):
    def test_single_part(self):
        sel = pt.select_parts([[rect(0, 0, 10, 5)]], pt.MODE_REFUSE, 0.01, TOL)
        self.assertEqual(sel.selected, [0])
        self.assertIsNone(sel.problem)

    def test_small_parts_ignored(self):
        parts = [[rect(0, 0, 100, 50)], [rect(200, 0, 1, 1)]]  # 1 mm2 < 1% of 5000
        sel = pt.select_parts(parts, pt.MODE_REFUSE, 0.01, TOL)
        self.assertEqual(sel.selected, [0])
        self.assertEqual(sel.ignored_small, [1])

    def test_refuse_by_default(self):
        parts = [[rect(0, 0, 100, 50)], [rect(200, 0, 50, 50)]]
        sel = pt.select_parts(parts, pt.MODE_REFUSE, 0.01, TOL)
        self.assertEqual(sel.problem.code, "LOOSE_PARTS")
        self.assertEqual(sel.problem.details["count"], 2)

    def test_largest(self):
        parts = [[rect(0, 0, 50, 50)], [rect(200, 0, 100, 50)]]
        sel = pt.select_parts(parts, pt.MODE_LARGEST, 0.01, TOL)
        self.assertEqual(sel.selected, [1])

    def test_largest_identical_exports_one(self):
        base = [(0, 0), (40, 0), (40, 10), (20, 25), (0, 10)]
        parts = [[base], [moved(base, 100, 30, 37)]]
        sel = pt.select_parts(parts, pt.MODE_LARGEST, 0.01, TOL)
        self.assertEqual(sel.selected, [0])
        self.assertEqual(sel.duplicates, [1])

    def test_mirrored_is_different(self):
        base = [(0, 0), (40, 0), (40, 10), (10, 25), (0, 10)]
        mirror = [(-x + 100, y) for x, y in reversed(base)]
        self.assertFalse(pt.congruent([base], [mirror], TOL))

    def test_equal_area_different_shape_refused(self):
        parts = [[rect(0, 0, 40, 10)], [rect(100, 0, 20, 20)]]
        sel = pt.select_parts(parts, pt.MODE_LARGEST, 0.01, TOL)
        self.assertEqual(sel.problem.code, "EQUAL_AREA_PARTS")

    def test_all(self):
        parts = [[rect(0, 0, 40, 10)], [rect(100, 0, 20, 20)], [rect(0, 100, 0.5, 0.5)]]
        sel = pt.select_parts(parts, pt.MODE_ALL, 0.01, TOL)
        self.assertEqual(sel.selected, [0, 1])
        self.assertEqual(sel.ignored_small, [2])

    def test_holes_must_match(self):
        outer = rect(0, 0, 40, 40)
        a = [outer, list(reversed(rect(5, 5, 10, 10)))]
        b = [outer, list(reversed(rect(20, 20, 10, 10)))]
        self.assertTrue(pt.congruent(a, [moved(lp, 3, 4, 90) for lp in a], TOL))
        self.assertFalse(pt.congruent(a, b, TOL))

    def test_area_with_hole(self):
        self.assertAlmostEqual(pt.part_area([rect(0, 0, 10, 10), rect(2, 2, 2, 2)]), 96.0)


class LayoutTests(unittest.TestCase):
    def piece(self, name, loop):
        return pl.Piece(name, 0, rc.analyze_region([loop]), [[]])

    def test_single_file_side_by_side(self):
        a = self.piece("A", rect(0, 0, 40, 20))
        b = self.piece("B", rect(-5, -5, 30, 30))
        groups = pl.layout([a, b], pl.OUTPUT_SINGLE, 10.0)
        self.assertEqual(len(groups), 1)
        row = groups[0][1]
        self.assertEqual(row[0][1], (0.0, 0.0))
        self.assertEqual(row[1][1], (55.0, 5.0))
        self.assertTrue(pl.check_no_overlap(row))

    def test_per_object_keeps_coordinates(self):
        a = self.piece("A", rect(0, 0, 40, 20))
        b = self.piece("B", rect(0, 0, 30, 30))
        groups = pl.layout([a, b], pl.OUTPUT_PER_OBJECT, 10.0)
        self.assertEqual([g[0] for g in groups], ["A", "B"])
        self.assertTrue(all(row[0][1] == (0.0, 0.0) for _, row in groups))

    def test_bbox_includes_arc_bulge(self):
        res = rc.analyze_region([[(10 * math.cos(2 * math.pi * k / 16), 10 * math.sin(2 * math.pi * k / 16)) for k in range(16)]])
        self.assertEqual(pl.entities_bbox(res), (-10.0, -10.0, 10.0, 10.0))


if __name__ == "__main__":
    unittest.main(verbosity=1)
