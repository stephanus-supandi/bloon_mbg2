"""Deterministic synthetic founder genomes.
These are SYNTHETIC computational sequences inspired by biological sequence
representation. They are NOT literal primate DNA.
Founder A biased ke {A,C} (trait score rendah); Founder B ke {G,T}.
Konstruksi founder fixed (seed internal 1001/1002), independen dari --seed;
--seed hanya mengontrol proses evolusioner stokastik.
"""
import random
from .layout import LENGTH

FOUNDER_A_SEED = 1001
FOUNDER_B_SEED = 1002


def initial_genomes():
    def build(seed, weights):
        rng = random.Random(seed)
        return "".join(rng.choices("ACGT", weights=weights, k=LENGTH))

    a = build(FOUNDER_A_SEED, [0.40, 0.30, 0.20, 0.10])
    b = build(FOUNDER_B_SEED, [0.10, 0.20, 0.30, 0.40])
    return a, b