"""Genome layout: [regulatory 12][locus 01..11 x 24] = 276 nt, annotated."""
from dataclasses import dataclass
from .sequence import validate, SequenceError

REG_LEN = 12
LOCUS_LEN = 24
N_LOCI = 11
LENGTH = REG_LEN + N_LOCI * LOCUS_LEN  # 276

LOCUS_ANNOTATION = [
    "body_size", "torso_width", "arm_length", "forearm_ratio", "leg_length",
    "shoulder_width", "muscle_mass", "jaw_size", "skull_ratio", "posture",
    "fur_density",
]


def locus_of_position(pos):
    """0..11 -> regulatory; 12..35 -> locus_01; ...; 252..275 -> locus_11."""
    if not isinstance(pos, int) or not (0 <= pos < LENGTH):
        raise SequenceError("position out of genome: " + repr(pos))
    if pos < REG_LEN:
        return "regulatory"
    return "locus_{:02d}".format((pos - REG_LEN) // LOCUS_LEN + 1)


@dataclass(frozen=True)
class Genome:
    sequence: str

    def __post_init__(self):
        validate(self.sequence, LENGTH)

    @classmethod
    def from_sequence(cls, seq):
        return cls(validate(seq, LENGTH))

    def regulatory_region(self):
        return self.sequence[:REG_LEN]

    def locus(self, i):
        if not isinstance(i, int) or not (0 <= i < N_LOCI):
            raise SequenceError("malformed locus index: " + repr(i))
        start = REG_LEN + i * LOCUS_LEN
        return self.sequence[start:start + LOCUS_LEN]