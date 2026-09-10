"""fitness = H(PBET observation). Tidak pernah H(sprite), tidak pernah genome.
M2G v1 (terdokumentasi): fitness = 1 / (1 + distance).
Slot bobot tambahan adalah extension point terdokumentasi dan inert sampai
SUT nyata menyediakan observasi novelty/coverage/constraint.
"""
from dataclasses import dataclass
from .oracle import Observation


@dataclass(frozen=True)
class FitnessWeights:
    w_morphology: float = 1.0
    w_novelty: float = 0.0
    w_coverage: float = 0.0
    w_constraint: float = 0.0


def fitness_from_observation(obs, weights=None):
    if weights is None:
        weights = FitnessWeights()
    return weights.w_morphology * (1.0 / (1.0 + obs.distance))