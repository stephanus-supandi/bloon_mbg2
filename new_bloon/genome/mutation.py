"""Traceable mutation: substitution / insertion / deletion + synthetic repair.
Semantik parameter (tidak ambigu, bukan operator weighting):
    substitution_rate : probabilitas PER BASE per replikasi.
    insertion_rate    : probabilitas MAKSIMAL SATU insertion event per genome.
    deletion_rate     : probabilitas MAKSIMAL SATU deletion event per genome.
Keputusan fixed-length (Option A): genome tetap 276 nt. Indel diperbaiki
secara sintetis di ujung 3' (truncate overflow / pad dengan 'A').
This is a computational simplification, not a realistic model of biological
indel behavior. Setiap event dan setiap repair dicatat di log.
"""
import random
from dataclasses import dataclass, field, asdict
from .layout import LENGTH, locus_of_position
from .sequence import validate, SequenceError

BASES = "ACGT"


@dataclass(frozen=True)
class MutationRates:
    substitution_rate: float = 0.005
    insertion_rate: float = 0.10
    deletion_rate: float = 0.10

    def validate(self):
        for name in ("substitution_rate", "insertion_rate", "deletion_rate"):
            v = getattr(self, name)
            if not (0.0 <= v <= 1.0):
                raise SequenceError(
                    "invalid {}: {} (must be in [0,1])".format(name, v))


@dataclass(frozen=True)
class MutationEvent:
    generation: int
    individual: str
    kind: str        # substitution|insertion|deletion|repair_truncate|repair_pad
    position: int
    before: str
    after: str
    locus: str

    def to_dict(self):
        return asdict(self)


@dataclass
class MutationLog:
    events: list = field(default_factory=list)

    def add(self, generation, individual, kind, position, before, after, locus):
        self.events.append(MutationEvent(
            generation, individual, kind, position, before, after, locus))

    def to_list(self):
        return [e.to_dict() for e in self.events]


def mutate(seq, rng, rates, generation, individual_id):
    """Return (mutated_seq_of_fixed_LENGTH, MutationLog). Fully traceable."""
    rates.validate()
    log = MutationLog()
    seq = validate(seq)
    out = list(seq)

    for pos in range(len(out)):
        if rng.random() < rates.substitution_rate:
            old = out[pos]
            new = rng.choice([b for b in BASES if b != old])
            out[pos] = new
            log.add(generation, individual_id, "substitution", pos,
                    old, new, locus_of_position(pos))

    seq = "".join(out)

    if rng.random() < rates.insertion_rate:
        pos = rng.randrange(len(seq))
        base = rng.choice(BASES)
        seq = seq[:pos] + base + seq[pos:]
        log.add(generation, individual_id, "insertion", pos, "-", base,
                locus_of_position(min(pos, LENGTH - 1)))

    if rng.random() < rates.deletion_rate:
        pos = rng.randrange(len(seq))
        base = seq[pos]
        seq = seq[:pos] + seq[pos + 1:]
        log.add(generation, individual_id, "deletion", pos, base, "-",
                locus_of_position(min(pos, LENGTH - 1)))

    if len(seq) > LENGTH:
        removed = seq[LENGTH:]
        seq = seq[:LENGTH]
        log.add(generation, individual_id, "repair_truncate", LENGTH,
                removed, "-", "3_prime_end")
    elif len(seq) < LENGTH:
        pad_len = LENGTH - len(seq)
        pad = "A" * pad_len
        seq = seq + pad
        log.add(generation, individual_id, "repair_pad", LENGTH - pad_len,
                "-", pad, "3_prime_end")

    return validate(seq, LENGTH), log