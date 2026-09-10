import json
import unittest

from new_bloon.evolution.engine import EvolutionEngine, EngineConfig
from new_bloon.evolution.population import Population, Individual
from new_bloon.evolution.selection import select
from new_bloon.genome.layout import Genome, LENGTH
from new_bloon.genome.mutation import MutationRates
from new_bloon.pbet.oracle import GorillaMorphologyOracle


def make_engine(seed=12345, generations=5, elitism=True):
    cfg = EngineConfig(seed=seed, generations=generations, elitism=elitism,
                       rates=MutationRates(0.01, 0.2, 0.2))
    return EvolutionEngine(cfg, GorillaMorphologyOracle())


def _ind(ident, fitness):
    return Individual(id=ident, generation=0, parent_ids=[],
                      genome=Genome("A" * LENGTH), fitness=fitness)


class TestPopulationInvariant(unittest.TestCase):
    def test_size_two(self):
        pop = Population([_ind("a", 0.1), _ind("b", 0.2)])
        self.assertEqual(len(pop), 2)
        self.assertEqual(pop[0].id, "a")
        self.assertEqual([m.id for m in pop], ["a", "b"])

    def test_size_violations_raise(self):
        for n in (0, 1, 3, 10, 100):
            with self.assertRaises(ValueError):
                Population([_ind("x" + str(i), 0.1) for i in range(n)])

    def test_duplicates_raise(self):
        with self.assertRaises(ValueError):
            Population([_ind("a", 0.1), _ind("a", 0.2)])

    def test_selection_returns_exactly_two(self):
        pool = [_ind("i" + str(k), k * 0.1) for k in range(6)]
        self.assertEqual(len(select(pool, 2)), 2)

    def test_selection_deterministic_rank(self):
        winners = select([_ind("b", 0.5), _ind("a", 0.9), _ind("c", 0.5)], 2)
        self.assertEqual([w.id for w in winners], ["a", "b"])


class TestEngine(unittest.TestCase):
    def test_invalid_config_rejected(self):
        with self.assertRaises(ValueError):
            EvolutionEngine(EngineConfig(generations=-1),
                            GorillaMorphologyOracle())
        with self.assertRaises(ValueError):
            EvolutionEngine(EngineConfig(crossover_methods=("magic",)),
                            GorillaMorphologyOracle())
        with self.assertRaises(ValueError):
            EvolutionEngine(EngineConfig(rates=MutationRates(-1.0, 0.0, 0.0)),
                            GorillaMorphologyOracle())
        with self.assertRaises(ValueError):
            EvolutionEngine(EngineConfig(), None)

    def test_population_two_every_generation(self):
        res = make_engine(generations=10).run()
        self.assertEqual(len(res["records"]), 11)
        for rec in res["records"]:
            self.assertEqual(len(rec["population"]), 2)

    def test_lineage(self):
        res = make_engine(generations=10).run()
        by_id = {e["id"]: e for e in res["lineage"]}
        founders = 0
        for entry in res["lineage"]:
            if entry["generation"] == 0:
                self.assertEqual(entry["parents"], [])
                founders += 1
            else:
                self.assertEqual(len(entry["parents"]), 2)
                for p in entry["parents"]:
                    self.assertIn(p, by_id)
                    self.assertLess(by_id[p]["generation"],
                                    entry["generation"])
        self.assertEqual(founders, 2)

    def test_deterministic_seed(self):
        r1 = json.dumps(make_engine(seed=999, generations=15).run()["records"])
        r2 = json.dumps(make_engine(seed=999, generations=15).run()["records"])
        self.assertEqual(r1, r2)

    def test_seed_changes_trajectory(self):
        r1 = json.dumps(make_engine(seed=1, generations=15).run()["records"])
        r2 = json.dumps(make_engine(seed=2, generations=15).run()["records"])
        self.assertNotEqual(r1, r2)

    def test_breeding_events_logged(self):
        res = make_engine(seed=5, generations=3).run()
        self.assertEqual(len(res["breeding_log"]), 6)
        for ev in res["breeding_log"]:
            self.assertIn(ev["method"],
                          ("single_point", "two_point", "block"))
            self.assertEqual(len(ev["offspring"]), 2)
            self.assertTrue(ev["cut_points"])

    def test_offspring_genomes_index_semantics(self):
        """
        Mutation off + elitism off.

        offspring[0] harus child1, offspring[1] harus child2.
        Bukan set membership.
        """
        cfg = EngineConfig(seed=11, generations=2,
                           rates=MutationRates(0.0, 0.0, 0.0),
                           elitism=False)
        res = EvolutionEngine(cfg, GorillaMorphologyOracle()).run()

        genomes = {}
        for rec in res["records"]:
            for ind in rec["population"]:
                genomes[ind["id"]] = ind["genome"]

        checked = 0
        for ev in res["breeding_log"]:
            a = genomes.get(ev["parent_a"])
            b = genomes.get(ev["parent_b"])
            if a is None or b is None:
                continue

            cuts = ev["cut_points"]
            child_ids = ev["offspring"]

            if ev["method"] in ("single_point", "block"):
                k = cuts[0]
                expected = [a[:k] + b[k:], b[:k] + a[k:]]
            else:
                k1, k2 = cuts
                expected = [a[:k1] + b[k1:k2] + a[k2:],
                            b[:k1] + a[k1:k2] + b[k2:]]

            for idx, oid in enumerate(child_ids):
                if oid in genomes:
                    self.assertEqual(
                        genomes[oid], expected[idx],
                        "offspring[{}] != expected child for method={} cuts={}".format(
                            idx, ev["method"], cuts))
                    checked += 1

        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
