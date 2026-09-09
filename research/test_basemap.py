#!/usr/bin/env python3
"""test_basemap.py - the two bugs the base-map reader actually had, kept as tests.

Both were found on 2026-09-09 by looking at the derived file instead of trusting the run:
  1. Douglas-Peucker on a CLOSED ring collapsed every polygon to two points. The ring's first and
     last vertex are the same, so the base line has zero length and every vertex measures zero
     distance from it. The urban footprint of Belgrade came out as a two-point sliver.
  2. dBASE character fields are padded with NUL bytes, so the Danube arrived named
     'Danube\\x00\\x00\\x00…' and no name comparison could ever match it.
Neither reached the public site - but neither would have been noticed by a green test run either,
which is exactly why they are tests now.
"""
import pathlib
import struct
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import fetch_basemap as fb  # noqa: E402


class RingSimplification(unittest.TestCase):
    def test_closed_ring_survives_simplification(self):
        # a square, 4 corners + closing point, with midpoints that are collinear (removable)
        ring = [(0.0, 0.0), (0.5, 0.0), (1.0, 0.0), (1.0, 0.5), (1.0, 1.0),
                (0.5, 1.0), (0.0, 1.0), (0.0, 0.5), (0.0, 0.0)]
        out = fb._dp_ring(ring, 0.0004)
        self.assertGreaterEqual(len(out), 4, "a closed ring must not collapse to a sliver")
        for corner in [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]:
            self.assertIn(corner, out, f"corner {corner} was dropped")

    def test_polygon_geometry_keeps_its_area(self):
        ring = [(20.4, 44.8), (20.5, 44.8), (20.5, 44.9), (20.4, 44.9), (20.4, 44.8)]
        g = fb._simplify_geom({"type": "Polygon", "coordinates": [ring]}, 0.0004)
        self.assertGreaterEqual(len(g["coordinates"][0]), 4)

    def test_open_line_still_simplifies(self):
        line = [(0.0, 0.0), (0.5, 0.00001), (1.0, 0.0)]
        g = fb._simplify_geom({"type": "LineString", "coordinates": line}, 0.001)
        self.assertEqual(len(g["coordinates"]), 2, "a nearly straight line should reduce to its ends")


class DbfDecoding(unittest.TestCase):
    @staticmethod
    def _dbf(name_value: bytes) -> bytes:
        """Smallest valid dBASE III file with one 'name' field of 24 bytes and one record."""
        flen = 24
        hdr_len = 32 + 32 + 1
        rec_len = 1 + flen
        head = struct.pack("<BBBBIHH", 0x03, 126, 9, 9, 1, hdr_len, rec_len) + b"\x00" * 20
        field = b"name".ljust(11, b"\x00") + b"C" + b"\x00" * 4 + bytes([flen]) + b"\x00" * 15
        return head + field + b"\x0D" + b" " + name_value.ljust(flen, b"\x00")

    def test_nul_padding_is_stripped(self):
        rows = fb._dbf_records(self._dbf(b"Danube"))
        self.assertEqual(rows, [{"name": "Danube"}])

    def test_space_padding_is_stripped(self):
        rows = fb._dbf_records(self._dbf(b"Sava      "))
        self.assertEqual(rows[0]["name"], "Sava")


class Clipping(unittest.TestCase):
    def test_points_outside_the_window_are_dropped_not_moved(self):
        line = [(10.0, 40.0), (20.4, 44.8), (20.5, 44.85), (30.0, 50.0)]
        runs = fb._clip_runs(line)
        self.assertEqual(len(runs), 1)
        self.assertEqual(len(runs[0]), 2, "only the two points inside the window survive")
        for x, y in runs[0]:
            self.assertTrue(20.0 < x < 21.0 and 44.4 < y < 45.1)

    def test_no_vertex_is_invented(self):
        line = [(20.4, 44.8), (20.5, 44.85)]
        runs = fb._clip_runs(line)
        self.assertEqual([tuple(map(lambda v: round(v, 5), p)) for p in runs[0]], [(20.4, 44.8), (20.5, 44.85)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
