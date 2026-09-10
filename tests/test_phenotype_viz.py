"""Test suite untuk phenotype expression dan visualization layer."""
import unittest

from new_bloon.genome.layout import Genome, LENGTH, REG_LEN, LOCUS_LEN
from new_bloon.phenotype.development import express
from new_bloon.phenotype.traits import TRAIT_NAMES, GORILLA_TARGET
from new_bloon.visualization.morphology import morphology_from_phenotype
from new_bloon.visualization.sprite import (
    render_sprite, archetype_tag, ROWS, COLS)


def _make_genome(base="A"):
    return Genome(base * LENGTH)


def _make_phenotype(val=0.5):
    return {t: val for t in TRAIT_NAMES}


class TestPhenotypeExpression(unittest.TestCase):
    def test_same_genome_same_phenotype(self):
        g = _make_genome("C")
        p1 = express(g)
        p2 = express(g)
        self.assertEqual(p1, p2)

    def test_phenotype_bounded_01(self):
        for base in ("A", "C", "G", "T"):
            g = _make_genome(base)
            p = express(g)
            for trait, val in p.items():
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 1.0)

    def test_all_traits_present(self):
        g = _make_genome("G")
        p = express(g)
        self.assertEqual(set(p.keys()), set(TRAIT_NAMES))

    def test_locus_change_changes_trait(self):
        seq_a = "A" * LENGTH
        seq_b = seq_a[:REG_LEN] + "T" * LOCUS_LEN + seq_a[REG_LEN + LOCUS_LEN:]
        g_a = Genome(seq_a)
        g_b = Genome(seq_b)
        p_a = express(g_a)
        p_b = express(g_b)
        self.assertNotAlmostEqual(p_a["body_size"], p_b["body_size"])

    def test_regulatory_modulation(self):
        seq_low = "A" * REG_LEN + "T" * (LENGTH - REG_LEN)
        seq_high = "G" * REG_LEN + "T" * (LENGTH - REG_LEN)
        p_low = express(Genome(seq_low))
        p_high = express(Genome(seq_high))
        for t in TRAIT_NAMES:
            self.assertGreaterEqual(p_high[t], p_low[t])

    def test_genome_from_sequence_classmethod(self):
        g = Genome.from_sequence("ACGT" * (LENGTH // 4))
        self.assertEqual(len(g.sequence), LENGTH)


class TestMorphology(unittest.TestCase):
    def test_returns_expected_keys(self):
        p = _make_phenotype(0.5)
        m = morphology_from_phenotype(p)
        expected_keys = {"torso_rx", "torso_ry", "head_rx", "head_ry",
                         "jaw_rx", "arm_ry", "arm_rx", "leg_ry", "leg_rx",
                         "lean"}
        self.assertEqual(set(m.keys()), expected_keys)

    def test_positive_dimensions(self):
        p = _make_phenotype(0.5)
        m = morphology_from_phenotype(p)
        for k, v in m.items():
            if k != "lean":
                self.assertGreater(v, 0.0)

    def test_larger_phenotype_larger_morphology(self):
        p_small = _make_phenotype(0.1)
        p_large = _make_phenotype(0.9)
        m_small = morphology_from_phenotype(p_small)
        m_large = morphology_from_phenotype(p_large)
        self.assertGreater(m_large["torso_rx"], m_small["torso_rx"])
        self.assertGreater(m_large["torso_ry"], m_small["torso_ry"])
        self.assertGreater(m_large["arm_ry"], m_small["arm_ry"])

    def test_posture_affects_lean(self):
        p_upright = _make_phenotype(0.5)
        p_upright["posture"] = 1.0
        p_hunched = _make_phenotype(0.5)
        p_hunched["posture"] = 0.0
        m_up = morphology_from_phenotype(p_upright)
        m_hunch = morphology_from_phenotype(p_hunched)
        self.assertLess(m_up["lean"], m_hunch["lean"])


class TestSprite(unittest.TestCase):
    def test_returns_string(self):
        p = _make_phenotype(0.5)
        s = render_sprite(p)
        self.assertIsInstance(s, str)

    def test_row_count(self):
        p = _make_phenotype(0.5)
        s = render_sprite(p)
        lines = s.split("\n")
        self.assertEqual(len(lines), ROWS)

    def test_max_col_width(self):
        p = _make_phenotype(0.5)
        s = render_sprite(p)
        for line in s.split("\n"):
            self.assertLessEqual(len(line), COLS)

    def test_contains_body_characters(self):
        p = _make_phenotype(0.7)
        s = render_sprite(p)
        self.assertIn("o", s)
        self.assertTrue(any(c in s for c in ".:#"))

    def test_different_phenotype_different_sprite(self):
        p1 = _make_phenotype(0.2)
        p2 = _make_phenotype(0.9)
        s1 = render_sprite(p1)
        s2 = render_sprite(p2)
        self.assertNotEqual(s1, s2)

    def test_renderer_receives_only_phenotype_dict(self):
        plain = {
            "body_size": 0.5,
            "torso_width": 0.5,
            "arm_length": 0.5,
            "forearm_ratio": 0.5,
            "leg_length": 0.5,
            "shoulder_width": 0.5,
            "muscle_mass": 0.5,
            "jaw_size": 0.5,
            "skull_ratio": 0.5,
            "posture": 0.5,
            "fur_density": 0.5,
        }
        s = render_sprite(plain)
        self.assertIsInstance(s, str)


class TestArchetypeTag(unittest.TestCase):
    def test_valid_tags(self):
        valid = {"GORILLA-like", "GREAT-APE-like", "MACAQUE-like", "MONKEY-like"}
        for val in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
            p = _make_phenotype(val)
            tag = archetype_tag(p)
            self.assertIn(tag, valid)

    def test_extreme_low_is_monkey(self):
        p = _make_phenotype(0.0)
        self.assertEqual(archetype_tag(p), "MONKEY-like")

    def test_extreme_high_is_gorilla(self):
        p = {t: 1.0 for t in TRAIT_NAMES}
        p["leg_length"] = 0.0
        p["posture"] = 0.0
        tag = archetype_tag(p)
        self.assertEqual(tag, "GORILLA-like")

    def test_gorilla_target_tag(self):
        tag = archetype_tag(dict(GORILLA_TARGET))
        self.assertIn(tag, ("GORILLA-like", "GREAT-APE-like"))

    def test_telemetry_tag_is_string(self):
        p = _make_phenotype(0.5)
        self.assertIsInstance(archetype_tag(p), str)


if __name__ == "__main__":
    unittest.main()
