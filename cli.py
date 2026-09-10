"""MBG2 / M2G v1 - Evolutionary PBET CLI (population = 2).

Usage:
    python cli.py --help
    python cli.py --seed 12345 --generations 10
    python cli.py --seed 12345 --generations 100 --out experiment
    python cli.py --seed 12345 --generations 100 --out experiment --pygame
    python cli.py --replay experiment --pygame

Exit codes:
    0 = sukses
    2 = config invalid / generations negatif / mutation param di luar [0,1] /
        crossover method tidak dikenal / replay path invalid
    3 = pygame diminta tetapi tidak terpasang
Tidak ada timestamp di artifact deterministik.
"""
import argparse
import csv
import json
import os
import sys

from new_bloon.evolution.engine import EvolutionEngine, EngineConfig
from new_bloon.genome.mutation import MutationRates
from new_bloon.genome.layout import LOCUS_ANNOTATION
from new_bloon.genome.recombination import METHODS
from new_bloon.pbet.fitness import FitnessWeights
from new_bloon.pbet.oracle import GorillaMorphologyOracle
from new_bloon.visualization.animation import write_animation
from new_bloon.visualization.sprite import archetype_tag

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(
    _REPO_ROOT, "new_bloon", "experiments", "configs", "default.json"
)

_MUT_KEYS = ("substitution_rate", "insertion_rate", "deletion_rate")


class ConfigError(Exception):
    pass


def load_config(path, seed=None, generations=None):
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except OSError as e:
        raise ConfigError("invalid config {!r}: {}".format(path, e))
    except json.JSONDecodeError as e:
        raise ConfigError("invalid config JSON {!r}: {}".format(path, e))

    if seed is not None:
        cfg["seed"] = seed
    if generations is not None:
        cfg["generations"] = generations

    if cfg.get("population_size") != 2:
        raise ConfigError("population_size must be exactly 2, got {!r}".format(
            cfg.get("population_size")))

    gens = cfg.get("generations")
    if not isinstance(gens, int) or isinstance(gens, bool) or gens < 0:
        raise ConfigError(
            "generations must be a non-negative int, got {!r}".format(gens))

    for m in cfg.get("crossover_methods", []):
        if m not in METHODS:
            raise ConfigError("invalid crossover method: {!r} (valid: {})".format(
                m, list(METHODS)))

    mut = cfg.get("mutation", {})
    for k, v in mut.items():
        if k not in _MUT_KEYS:
            raise ConfigError("unknown mutation parameter: {!r}".format(k))
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ConfigError(
                "invalid mutation {}: {!r} (must be a number)".format(k, v))
        if not (0.0 <= float(v) <= 1.0):
            raise ConfigError(
                "invalid mutation {}: {!r} (must be in [0,1])".format(k, v))

    return cfg


def summarize(cfg, result):
    """Statistik dihitung HANYA dari record run yang nyata."""
    recs = result["records"]
    first = recs[0]
    last = recs[-1]
    best = max(recs, key=lambda r: r["best_fitness"])
    worst_reg = min(
        (b["best_fitness"] - a["best_fitness"]
         for a, b in zip(recs, recs[1:])),
        default=0.0)
    regressions = sum(1 for a, b in zip(recs, recs[1:])
                      if b["best_fitness"] < a["best_fitness"])
    stagnant = 0
    cur = 0
    for a, b in zip(recs, recs[1:]):
        if b["best_fitness"] <= a["best_fitness"]:
            cur += 1
            if cur > stagnant:
                stagnant = cur
        else:
            cur = 0

    mut_kinds = {}
    for e in result["mutation_log"]:
        mut_kinds[e["kind"]] = mut_kinds.get(e["kind"], 0) + 1

    final_arch = [archetype_tag(i["phenotype"]) for i in last["population"]]

    lines = [
        "seed                       = {}".format(cfg["seed"]),
        "generations                = {}".format(cfg["generations"]),
        "elitism                    = {}".format(cfg.get("elitism", True)),
        "individuals_created        = {}".format(len(result["lineage"])),
        "offspring_created          = {}".format(len(result["lineage"]) - 2),
        "crossover_events           = {}".format(len(result["breeding_log"])),
        "mutation_events            = {} {}".format(
            len(result["mutation_log"]), mut_kinds),
        "initial_best_fitness       = {}".format(first["best_fitness"]),
        "final_best_fitness         = {}".format(last["best_fitness"]),
        "initial_mean_fitness       = {}".format(first["mean_fitness"]),
        "final_mean_fitness         = {}".format(last["mean_fitness"]),
        "initial_genetic_distance   = {}".format(first["genetic_distance_A_B"]),
        "final_genetic_distance     = {}".format(last["genetic_distance_A_B"]),
        "best_fitness_generation    = G{:03d} ({})".format(
            best["generation"], best["best_fitness"]),
        "worst_generation_regression= {}".format(round(worst_reg, 6)),
        "generation_regressions     = {}".format(regressions),
        "longest_no_improvement     = {} generations".format(stagnant),
        "final_archetypes           = {}".format(" ".join(final_arch)),
    ]
    return "\n".join(lines)


def _launch_pygame(args, records):
    from new_bloon.visualization.pygame_viewer import run_viewer
    return run_viewer(records, fps=args.pygame_fps,
                      max_frames=args.pygame_frames,
                      dummy=args.pygame_dummy)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="MBG2 / M2G v1 - Evolutionary PBET (population=2)",
        epilog="Pygame = optional interactive viewer (visualization only); "
               "tidak mempengaruhi evolution/fitness. Core jalan tanpa pygame.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--generations", type=int, default=None)
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--out", default="experiment")
    ap.add_argument("--no-elitism", action="store_true",
                    help="exclude parents from the selection pool")
    ap.add_argument("--replay", default=None, metavar="DIR",
                    help="load generations dari artifact experiment (tanpa run)")
    ap.add_argument("--pygame", action="store_true",
                    help="buka interactive pygame viewer setelah run/replay")
    ap.add_argument("--pygame-fps", type=int, default=4)
    ap.add_argument("--pygame-frames", type=int, default=None,
                    help="auto-quit setelah N frame (smoke test)")
    ap.add_argument("--pygame-dummy", action="store_true",
                    help="headless SDL dummy driver (smoke test)")
    args = ap.parse_args(argv)

    if args.replay:
        from new_bloon.visualization.pygame_viewer import load_records
        try:
            records = load_records(args.replay)
        except (OSError, ValueError) as e:
            print("replay error: {}".format(e), file=sys.stderr)
            return 2
        print("replay: {} generations loaded from {}".format(
            len(records) - 1, args.replay))
        if args.pygame:
            return _launch_pygame(args, records)
        return 0

    if args.generations is not None and args.generations < 0:
        print("config error: negative generations", file=sys.stderr)
        return 2

    try:
        cfg = load_config(args.config, args.seed, args.generations)
    except ConfigError as e:
        print("config error: {}".format(e), file=sys.stderr)
        return 2

    engine_cfg = EngineConfig(
        seed=cfg["seed"],
        generations=cfg["generations"],
        crossover_pairs_per_generation=cfg["crossover_pairs_per_generation"],
        crossover_methods=tuple(cfg["crossover_methods"]),
        rates=MutationRates(**cfg["mutation"]),
        weights=FitnessWeights(**cfg["fitness_weights"]),
        elitism=bool(cfg.get("elitism", True)) and not args.no_elitism,
    )

    try:
        sut = GorillaMorphologyOracle(cfg.get("gorilla_target"))
        engine = EvolutionEngine(engine_cfg, sut)
        result = engine.run()
    except ValueError as e:
        print("engine error: {}".format(e), file=sys.stderr)
        return 2

    records = result["records"]
    out = args.out
    os.makedirs(out, exist_ok=True)

    def write_json(name, obj):
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
            f.write("\n")

    write_json("config.json", cfg)

    with open(os.path.join(out, "seed.txt"), "w", encoding="utf-8") as f:
        f.write("{}\n".format(cfg["seed"]))

    write_json("generations.json", records)
    write_json("lineage.json", {
        "lineage": result["lineage"],
        "breeding_log": result["breeding_log"],
        "mutation_log": result["mutation_log"],
    })

    with open(os.path.join(out, "fitness.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["generation", "id", "fitness", "pbet_distance"])
        for rec in records:
            for ind in rec["population"]:
                w.writerow([rec["generation"], ind["id"],
                            ind["fitness"], ind["pbet"]["distance"]])

    with open(os.path.join(out, "phenotype.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["generation", "id"] + LOCUS_ANNOTATION)
        for rec in records:
            for ind in rec["population"]:
                w.writerow([rec["generation"], ind["id"]]
                           + [round(ind["phenotype"][t], 6)
                              for t in LOCUS_ANNOTATION])

    write_animation(records, out)

    print(summarize(cfg, result))
    print("artifacts written to: {}".format(os.path.abspath(out)))

    if args.pygame:
        return _launch_pygame(args, records)
    return 0


if __name__ == "__main__":
    sys.exit(main())