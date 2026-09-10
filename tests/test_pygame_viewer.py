"""Tests untuk pygame_viewer: pure geometry (tanpa pygame) + smoke headless."""
import json
import os
import shutil
import tempfile
import unittest

from new_bloon.phenotype.traits import TRAIT_NAMES
from new_bloon.visualization import pygame_viewer as pv

try:
    import pygame  # noqa: F401
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


def _pheno(val=0.5, **over):
    p = {t: val for t in TRAIT_NAMES}
    p.update(over)
    return p


def _smoke_records(n=3):
    recs = []
    for g in range(n):
        pop = []
        for k in range(2):
            ph = {t: 0.2 + 0.1 * g + 0.05 * k for t in TRAIT_NAMES}
            pop.append({"id": "I_{:05d}".format(g * 2 + k),
                        "phenotype": ph, "fitness": 0.5,
                        "pbet": {"distance": 0.5, "notes": ""}})
        recs.append({"generation": g, "population": pop,
                     "best_fitness": 0.5, "mean_fitness": 0.5,
                     "genetic_distance_A_B": 0.1,
                     "offspring": [], "breeding_events": []})
    return recs


class TestGeometry(unittest.TestCase):
    """phenotype_to_drawables = pure function, tidak butuh pygame."""

    def test_drawables_structure(self):
        d = pv.phenotype_to_drawables(_pheno(0.5))
        self.assertIsInstance(d, list)
        self.assertGreaterEqual(len(d), 8)
        self.assertTrue({x["kind"] for x in d} <= {"ellipse", "line", "circle"})

    def test_geometry_within_canvas(self):
        for val in (0.0, 0.5, 1.0):
            for posture in (0.0, 1.0):
                d = pv.phenotype_to_drawables(_pheno(val, posture=posture))
                for item in d:
                    pts = []
                    if item["kind"] == "ellipse":
                        x, y, w, h = item["rect"]
                        pts = [(x, y), (x + w, y + h)]
                    elif item["kind"] == "line":
                        pts = [item["start"], item["end"]]
                    elif item["kind"] == "circle":
                        r = item["radius"]
                        cx, cy = item["center"]
                        pts = [(cx - r, cy - r), (cx + r, cy + r)]
                    for x, y in pts:
                        self.assertGreaterEqual(x, -5)
                        self.assertLessEqual(x, pv.CANVAS_W + 5)
                        self.assertGreaterEqual(y, -5)
                        self.assertLessEqual(y, pv.CANVAS_H + 5)

    def test_posture_changes_head_lean(self):
        up = [e for e in pv.phenotype_to_drawables(_pheno(0.5, posture=1.0))
              if e["kind"] == "ellipse"]
        hunch = [e for e in pv.phenotype_to_drawables(_pheno(0.5, posture=0.0))
                 if e["kind"] == "ellipse"]
        # ellipse order: torso, shoulders, head, jaw
        self.assertGreater(hunch[2]["rect"][0], up[2]["rect"][0])

    def test_body_size_changes_torso_height(self):
        small = [e for e in pv.phenotype_to_drawables(_pheno(0.2))
                 if e["kind"] == "ellipse"][0]
        large = [e for e in pv.phenotype_to_drawables(_pheno(0.9))
                 if e["kind"] == "ellipse"][0]
        self.assertGreater(large["rect"][3], small["rect"][3])

    def test_leg_length_changes_hip_height(self):
        short = pv.phenotype_to_drawables(_pheno(0.5, leg_length=0.1))
        long_ = pv.phenotype_to_drawables(_pheno(0.5, leg_length=0.9))
        self.assertLess(long_[0]["start"][1], short[0]["start"][1])

    def test_fur_density_changes_color(self):
        light = pv.phenotype_to_drawables(_pheno(0.5, fur_density=0.0))[0]
        dark = pv.phenotype_to_drawables(_pheno(0.5, fur_density=1.0))[0]
        self.assertNotEqual(light["color"], dark["color"])

    def test_renderer_needs_only_phenotype_dict(self):
        plain = {t: 0.5 for t in TRAIT_NAMES}
        d = pv.phenotype_to_drawables(plain)
        self.assertTrue(d)


class TestLoadRecords(unittest.TestCase):
    def test_load_from_dir_and_file(self):
        tmp = tempfile.mkdtemp()
        try:
            recs = [{"generation": 0, "population": []}]
            p = os.path.join(tmp, "generations.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(recs, f)
            self.assertEqual(pv.load_records(tmp), recs)
            self.assertEqual(pv.load_records(p), recs)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_empty_raises(self):
        tmp = tempfile.mkdtemp()
        try:
            p = os.path.join(tmp, "generations.json")
            with open(p, "w", encoding="utf-8") as f:
                f.write("[]")
            with self.assertRaises(ValueError):
                pv.load_records(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_missing_raises(self):
        missing = os.path.join(tempfile.gettempdir(),
                               "mbg2_definitely_missing_xyz")
        with self.assertRaises(OSError):
            pv.load_records(missing)


class TestViewerBehaviour(unittest.TestCase):
    def test_graceful_without_pygame(self):
        orig = pv._require_pygame
        pv._require_pygame = lambda: None
        try:
            rc = pv.run_viewer(_smoke_records(1))
            self.assertEqual(rc, 3)
        finally:
            pv._require_pygame = orig

    @unittest.skipUnless(HAS_PYGAME, "pygame not installed")
    def test_headless_smoke(self):
        rc = pv.run_viewer(_smoke_records(3), fps=60,
                           max_frames=4, dummy=True)
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main() 