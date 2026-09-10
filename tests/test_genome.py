import random
import unittest

from new_bloon.genome.layout import (
    Genome, LENGTH, REG_LEN, LOCUS_LEN, locus_of_position)
from new_bloon.genome.sequence import validate, SequenceError
from new_bloon.genome.mutation import mutate, MutationRates
from new_bloon.genome.recombination import crossover, METHODS
from new_bloon.genome.analysis import (
    gc_content, hamming_distance, genetic_distance, edit_distance)
from new_bloon.genome.factory import initial_genomes


class TestValidation(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate("ACGT"), "ACGT")

    def test_lowercase_normalized(self):
        self.assertEqual(validate("acgt"), "ACGT")

    def test_empty(self):
        with self.assertRaises(SequenceError):
            validate("")

    def test_invalid_character(self):
        for bad in ("ACGX", "ACGN", "ACG ", "ACG-"):
            with self.assertRaises(SequenceError):
                validate(bad)

    def test_wrong_length(self):
        with self.assertRaises(SequenceError):
            validate("ACGT", expected_length=10)

    def test_genome_length_enforced(self):
        with self.assertRaises(SequenceError):
            Genome("A" * (LENGTH - 1))
        with self.assertRaises(SequenceError):
            Genome("A" * (LENGTH + 1))
        Genome("A" * LENGTH)

    def test_position_boundaries(self):
        self.assertEqual(locus_of_position(0), "regulatory")
        self.assertEqual(locus_of_position(11), "regulatory")
        self.assertEqual(locus_of_position(12), "locus_01")
        self.assertEqual(locus_of_position(35), "locus_01")
        self.assertEqual(locus_of_position(36), "locus_02")
        self.assertEqual(locus_of_position(275), "locus_11")
        with self.assertRaises(SequenceError):
            locus_of_position(276)
        with self.assertRaises(SequenceError):
            locus_of_position(-1)

    def test_loci(self):
        g = Genome("A" * REG_LEN + "C" * (LENGTH - REG_LEN))
        self.assertEqual(g.regulatory_region(), "A" * REG_LEN)
        for i in range(11):
            self.assertEqual(g.locus(i), "C" * LOCUS_LEN)
        with self.assertRaises(SequenceError):
            g.locus(11)


class TestAnalysis(unittest.TestCase):
    def test_gc_content(self):
        self.assertEqual(gc_content("GGCC"), 1.0)
        self.assertEqual(gc_content("AATT"), 0.0)
        self.assertEqual(gc_content("AGCT"), 0.5)
        self.assertEqual(gc_content(""), 0.0)

    def test_hamming_and_genetic_distance(self):
        self.assertEqual(hamming_distance("ACGT", "ACGA"), 1)
        self.assertAlmostEqual(genetic_distance("ACGT", "TTTT"), 0.75)
        with self.assertRaises(ValueError):
            hamming_distance("ACG", "ACGT")

    def test_edit_distance(self):
        self.assertEqual(edit_distance("", "ABC"), 3)
        self.assertEqual(edit_distance("ACGT", "ACGT"), 0)
        self.assertEqual(edit_distance("ACGT", "AGT"), 1)
        self.assertEqual(edit_distance("ACGT", "ACGTT"), 1)
        self.assertEqual(edit_distance("KITTEN", "SITTING"), 3)


class TestMutation(unittest.TestCase):
    def setUp(self):
        self.seq = "ACGT" * (LENGTH // 4)
        self.rng = random.Random(7)

    def test_invalid_rates_rejected(self):
        for bad in (MutationRates(-0.1, 0.0, 0.0),
                    MutationRates(0.0, 1.5, 0.0),
                    MutationRates(0.0, 0.0, 2.0)):
            with self.assertRaises(SequenceError):
                mutate(self.seq, self.rng, bad, 1, "x")

    def test_substitution_traceable_and_real(self):
        rates = MutationRates(substitution_rate=1.0, insertion_rate=0.0,
                              deletion_rate=0.0)
        out, log = mutate(self.seq, self.rng, rates, 3, "offspring_02")
        self.assertEqual(len(out), LENGTH)
        self.assertTrue(log.events)
        for e in log.events:
            self.assertEqual(e.kind, "substitution")
            self.assertEqual(e.generation, 3)
            self.assertEqual(e.individual, "offspring_02")
            self.assertEqual(self.seq[e.position], e.before)
            self.assertEqual(out[e.position], e.after)
            self.assertNotEqual(e.before, e.after)
            self.assertEqual(e.locus, locus_of_position(e.position))
        rec = list(self.seq)
        for e in log.events:
            rec[e.position] = e.after
        self.assertEqual("".join(rec), out)

    def test_insertion_with_repair(self):
        rates = MutationRates(0.0, 1.0, 0.0)
        out, log = mutate(self.seq, self.rng, rates, 1, "o1")
        kinds = [e.kind for e in log.events]
        self.assertIn("insertion", kinds)
        self.assertIn("repair_truncate", kinds)
        self.assertEqual(len(out), LENGTH)

    def test_deletion_with_repair(self):
        rates = MutationRates(0.0, 0.0, 1.0)
        out, log = mutate(self.seq, self.rng, rates, 1, "o2")
        kinds = [e.kind for e in log.events]
        self.assertIn("deletion", kinds)
        self.assertIn("repair_pad", kinds)
        self.assertEqual(len(out), LENGTH)
        self.assertTrue(out.endswith("A"))

    def test_zero_rates_no_change(self):
        rates = MutationRates(0.0, 0.0, 0.0)
        out, log = mutate(self.seq, self.rng, rates, 1, "o3")
        self.assertEqual(out, self.seq)
        self.assertEqual(log.events, [])


class TestCrossover(unittest.TestCase):
    def test_single_point_exact(self):
        a, b = initial_genomes()
        rng = random.Random(1)
        c1, c2, cuts = crossover(a, b, "single_point", rng)
        k = cuts[0]
        self.assertTrue(1 <= k < LENGTH)
        self.assertEqual(c1, a[:k] + b[k:])
        self.assertEqual(c2, b[:k] + a[k:])
        self.assertEqual(len(c1), LENGTH)
        self.assertEqual(len(c2), LENGTH)

    def test_two_point_exact(self):
        a, b = initial_genomes()
        rng = random.Random(2)
        c1, c2, cuts = crossover(a, b, "two_point", rng)
        k1, k2 = cuts
        self.assertTrue(1 <= k1 < k2 < LENGTH)
        self.assertEqual(c1, a[:k1] + b[k1:k2] + a[k2:])
        self.assertEqual(c2, b[:k1] + a[k1:k2] + b[k2:])

    def test_block_cuts_on_locus_boundaries(self):
        a, b = initial_genomes()
        for seed in range(30):
            c1, c2, cuts = crossover(a, b, "block", random.Random(seed))
            self.assertEqual((cuts[0] - REG_LEN) % LOCUS_LEN, 0)
            self.assertEqual(c1, a[:cuts[0]] + b[cuts[0]:])
            self.assertEqual(c2, b[:cuts[0]] + a[cuts[0]:])
            self.assertEqual(len(c1), LENGTH)
            self.assertEqual(len(c2), LENGTH)

    def test_founders_distinct(self):
        a, b = initial_genomes()
        self.assertNotEqual(a, b)
        self.assertGreater(genetic_distance(a, b), 0.1)

    def test_all_methods_covered(self):
        self.assertEqual(set(METHODS),
                         {"single_point", "two_point", "block"})

    def test_unknown_method(self):
        a, b = initial_genomes()
        with self.assertRaises(ValueError):
            crossover(a, b, "magic", random.Random(0))


if __name__ == "__main__":
    unittest.main()
