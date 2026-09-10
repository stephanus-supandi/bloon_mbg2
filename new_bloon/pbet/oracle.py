"""SUT interface + default gorilla-morphology oracle.
SUT replaceable: engine hanya bergantung pada
`SUT.execute(candidate) -> Observation`. Oracle menerima phenotype SAJA —
tidak pernah genome, sprite, generation, atau fitness.
"""
import math
from dataclasses import dataclass
from ..phenotype.traits import TRAIT_NAMES, GORILLA_TARGET
from .candidate import Candidate


@dataclass(frozen=True)
class Observation:
    individual_id: str
    distance: float
    notes: str = ""


class SUT:
    def execute(self, candidate):
        raise NotImplementedError


class GorillaMorphologyOracle(SUT):
    """o = d(p, G) = RMS phenotype distance ke benchmark target G yang tetap."""

    def __init__(self, target=None):
        self.target = dict(target if target is not None else GORILLA_TARGET)

    def execute(self, candidate):
        p = candidate.phenotype
        sq = sum((p[t] - self.target[t]) ** 2 for t in TRAIT_NAMES)
        d = math.sqrt(sq / len(TRAIT_NAMES))
        return Observation(candidate.individual_id, d,
                           "rms_phenotype_distance")