import unittest

from new_bloon.pbet.candidate import Candidate
from new_bloon.pbet.oracle import SUT, Observation, GorillaMorphologyOracle
from new_bloon.pbet.fitness import fitness_from_observation, FitnessWeights
from new_bloon.phenotype.traits import GORILLA_TARGET, TRAIT_NAMES


class ZeroOracle(SUT):
    """Test double: membuktikan interface SUT replaceable."""

    def execute(self, candidate):
        return Observation(candidate.individual_id, 0.0, "stub")


class TestPBET(unittest.TestCase):
    def setUp(self):
        self.sut = GorillaMorphologyOracle()

    def test_candidate_generation(self):
        c = Candidate("I_00001", dict(GORILLA_TARGET))
        self.assertEqual(c.to_dict()["individual_id"], "I_00001")

    def test_sut_zero_distance_at_target(self):
        obs = self.sut.execute(Candidate("x", dict(GORILLA_TARGET)))
        self.assertAlmostEqual(obs.distance, 0.0)

    def test_fitness_formula(self):
        obs = self.sut.execute(Candidate("x", dict(GORILLA_TARGET)))
        self.assertAlmostEqual(fitness_from_observation(obs), 1.0)
        obs2 = Observation("y", 1.0)
        self.assertAlmostEqual(fitness_from_observation(obs2), 0.5)

    def test_closer_is_fitter(self):
        near = dict((t, GORILLA_TARGET[t] - 0.05) for t in TRAIT_NAMES)
        far = dict((t, 0.0) for t in TRAIT_NAMES)
        f_near = fitness_from_observation(
            self.sut.execute(Candidate("n", near)))
        f_far = fitness_from_observation(
            self.sut.execute(Candidate("f", far)))
        self.assertGreater(f_near, f_far)

    def test_sut_replaceable(self):
        obs = ZeroOracle().execute(Candidate("y", {}))
        self.assertEqual(obs.notes, "stub")
        self.assertEqual(fitness_from_observation(obs), 1.0)

    def test_base_sut_abstract(self):
        with self.assertRaises(NotImplementedError):
            SUT().execute(Candidate("z", {}))

    def test_weights_default_morphology_only(self):
        w = FitnessWeights()
        self.assertEqual(
            (w.w_morphology, w.w_novelty, w.w_coverage, w.w_constraint),
            (1.0, 0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
