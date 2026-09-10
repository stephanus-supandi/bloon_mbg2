"""Evolutionary loop with lineage (A-16, A-20, A-21, A-22).
Imports genome/phenotype/pbet ONLY — never visualization. This module has no
knowledge of sprites, archetypes, or rendering. Elitism (default on): the
selection pool is parents + offspring; parents may SURVIVE — survival is not
automatically reproduction.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from ..genome.factory import initial_genomes
from ..genome.layout import Genome
from ..genome.mutation import MutationRates, mutate
from ..genome.recombination import crossover, METHODS
from ..genome.analysis import genetic_distance
from ..phenotype.development import express
from ..pbet.candidate import Candidate
from ..pbet.fitness import fitness_from_observation, FitnessWeights
from .population import Individual, Population
from .selection import select


@dataclass
class EngineConfig:
    seed: int = 12345
    generations: int = 100
    crossover_pairs_per_generation: int = 2   # 2 pairs -> 4 offspring; |P| stays 2
    crossover_methods: tuple = METHODS
    rates: MutationRates = field(default_factory=MutationRates)
    weights: FitnessWeights = field(default_factory=FitnessWeights)
    elitism: bool = True


class EvolutionEngine:
    def __init__(self, config: EngineConfig, sut) -> None:
        if config.generations < 0:
            raise ValueError(f"negative generations: {config.generations}")
        if config.crossover_pairs_per_generation < 1:
            raise ValueError("crossover_pairs_per_generation must be >= 1")
        for m in config.crossover_methods:
            if m not in METHODS:
                raise ValueError(f"invalid crossover method: {m!r}")
        config.rates.validate()
        if sut is None or not hasattr(sut, "execute"):
            raise ValueError("SUT must implement .execute(candidate)")
        self.cfg = config
        self.sut = sut
        self.rng = random.Random(config.seed)
        self._next_id = 0
        self.records = []
        self.lineage = []
        self.breeding_log = []
        self.mutation_log = []
        self.final_population = None

    def _new_id(self) -> str:
        i = f"I_{self._next_id:05d}"
        self._next_id += 1
        return i

    def _build(self, seq: str, generation: int, parents: list,
               apply_mutation: bool = False) -> Individual:
        ind_id = self._new_id()
        events = []
        if apply_mutation:
            seq, mlog = mutate(seq, self.rng, self.cfg.rates,
                               generation, ind_id)
            events = mlog.to_list()
            self.mutation_log.extend(events)
        genome = Genome(seq)
        phenotype = express(genome)                                  # F(genome)
        obs = self.sut.execute(Candidate(ind_id, phenotype))         # PBET
        fit = fitness_from_observation(obs, self.cfg.weights)        # H(obs)
        ind = Individual(id=ind_id, generation=generation,
                         parent_ids=parents,
                         genome=genome, phenotype=phenotype,
                         fitness=fit,
                         pbet={"distance": obs.distance,
                               "notes": obs.notes},
                         mutation_events=events)
        self.lineage.append({"id": ind_id, "generation": generation,
                             "parents": list(parents)})
        return ind

    def _record(self, generation, pop, offspring, breeding_events):
        pa, pb = pop[0], pop[1]
        self.records.append({
            "generation": generation,
            "population": [pa.to_dict(), pb.to_dict()],
            "offspring": [{"id": o.id, "fitness": round(o.fitness, 6),
                           "distance": round(o.pbet["distance"], 6)}
                          for o in offspring],
            "breeding_events": breeding_events,
            "best_fitness": round(max(pa.fitness, pb.fitness), 6),
            "mean_fitness": round((pa.fitness + pb.fitness) / 2.0, 6),
            "genetic_distance_A_B": round(
                genetic_distance(pa.genome.sequence,
                                 pb.genome.sequence), 6),
        })

    def run(self) -> dict:
        seq_a, seq_b = initial_genomes()
        pop = Population([self._build(seq_a, 0, []),
                          self._build(seq_b, 0, [])])
        self._record(0, pop, [], [])

        for t in range(1, self.cfg.generations + 1):
            pa, pb = pop[0], pop[1]
            offspring, breeding_events = [], []

            for _ in range(self.cfg.crossover_pairs_per_generation):
                method = self.rng.choice(list(self.cfg.crossover_methods))
                c1, c2, cuts = crossover(pa.genome.sequence,
                                         pb.genome.sequence,
                                         method, self.rng)
                o1 = self._build(c1, t, [pa.id, pb.id],
                                 apply_mutation=True)
                o2 = self._build(c2, t, [pa.id, pb.id],
                                 apply_mutation=True)
                offspring.extend([o1, o2])
                event = {"generation": t, "method": method,
                         "cut_points": cuts,
                         "parent_a": pa.id, "parent_b": pb.id,
                         "offspring": [o1.id, o2.id]}
                breeding_events.append(event)
                self.breeding_log.append(event)

            pool = (list(pop) if self.cfg.elitism else []) + offspring
            pop = Population(select(pool, k=Population.SIZE))
            self._record(t, pop, offspring, breeding_events)

        self.final_population = pop
        return {
            "records": self.records,
            "lineage": self.lineage,
            "breeding_log": self.breeding_log,
            "mutation_log": self.mutation_log,
            "final_population": [i.to_dict() for i in pop],
        }