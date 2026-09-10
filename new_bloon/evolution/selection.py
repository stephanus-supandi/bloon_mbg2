"""Deterministic rank selection: (fitness desc, id asc), ambil top k."""


def select(candidates, k=2):
    ordered = sorted(candidates, key=lambda ind: (-ind.fitness, ind.id))
    return ordered[:k]