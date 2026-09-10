"""Individual record dan Population dengan invariant keras |P| == 2.
Python >= 3.9 compatible: plain class, keyword-only construction, TANPA
dataclasses kw_only (3.10+). Field identifier adalah `id`; semua call site
memakai keyword.
"""


class Individual:
    __slots__ = ("id", "generation", "parent_ids", "genome",
                 "phenotype", "fitness", "pbet", "mutation_events")

    def __init__(self, *, id, generation, parent_ids, genome,
                 phenotype=None, fitness=float("nan"), pbet=None,
                 mutation_events=None):
        self.id = id
        self.generation = generation
        self.parent_ids = list(parent_ids)
        self.genome = genome
        self.phenotype = dict(phenotype) if phenotype else {}
        self.fitness = fitness
        self.pbet = dict(pbet) if pbet else {}
        self.mutation_events = list(mutation_events) if mutation_events else []

    def to_dict(self):
        return {
            "id": self.id,
            "generation": self.generation,
            "parents": list(self.parent_ids),
            "genome": self.genome.sequence,
            "phenotype": {k: round(v, 6) for k, v in self.phenotype.items()},
            "fitness": round(self.fitness, 6),
            "pbet": {
                "distance": round(self.pbet.get("distance", float("nan")), 6),
                "notes": self.pbet.get("notes", ""),
            },
            "mutation_events": self.mutation_events,
        }


class Population:
    """Tepat dua individu. Tidak ada zoo. Raise jika invariant dilanggar."""
    SIZE = 2

    def __init__(self, members):
        if len(members) != self.SIZE:
            raise ValueError(
                "population invariant violated: {} != {}".format(
                    len(members), self.SIZE))
        ids = [m.id for m in members]
        if len(set(ids)) != self.SIZE:
            raise ValueError(
                "duplicate individuals in population: " + repr(ids))
        self.members = list(members)

    def __len__(self):
        return len(self.members)

    def __iter__(self):
        return iter(self.members)

    def __getitem__(self, i):
        return self.members[i]