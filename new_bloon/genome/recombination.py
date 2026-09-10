"""Crossover operators. Formula eksak:
    single_point(k):   c1 = A[:k] + B[k:]                c2 = B[:k] + A[k:]
    two_point(k1,k2):  c1 = A[:k1] + B[k1:k2] + A[k2:]   c2 = B[:k1] + A[k1:k2] + B[k2:]
    block(k):          sama dengan single_point, k dibatasi {12 + 24j}
Setiap breeding event dicatat engine: method, cut_points, parent IDs,
offspring IDs, generation.
"""
import random
from .layout import REG_LEN, LOCUS_LEN, N_LOCI, LENGTH
from .sequence import validate

METHODS = ("single_point", "two_point", "block")


def single_point(a, b, rng):
    k = rng.randrange(1, LENGTH)
    return a[:k] + b[k:], b[:k] + a[k:], [k]


def two_point(a, b, rng):
    k1, k2 = sorted(rng.sample(range(1, LENGTH), 2))
    c1 = a[:k1] + b[k1:k2] + a[k2:]
    c2 = b[:k1] + a[k1:k2] + b[k2:]
    return c1, c2, [k1, k2]


def block(a, b, rng):
    boundaries = [REG_LEN + j * LOCUS_LEN for j in range(1, N_LOCI + 1)]
    k = rng.choice(boundaries[:-1])
    return a[:k] + b[k:], b[:k] + a[k:], [k]


_OPS = {
    "single_point": single_point,
    "two_point": two_point,
    "block": block,
}


def crossover(a, b, method, rng):
    """Return (child1_seq, child2_seq, cut_points); keduanya tervalidasi 276 nt."""
    validate(a, LENGTH)
    validate(b, LENGTH)
    if method not in _OPS:
        raise ValueError("unknown crossover method: " + repr(method))
    op = _OPS[method]
    c1, c2, cuts = op(a, b, rng)
    return validate(c1, LENGTH), validate(c2, LENGTH), cuts