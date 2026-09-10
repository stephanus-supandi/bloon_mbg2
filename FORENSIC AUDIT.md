# MBG2 — FORENSIC AUDIT

## Status

**FINAL REVIEW — execution evidence recorded from actual Windows runs.**

MBG2 v1 is a deterministic, testable evolutionary optimization benchmark with:
- population fixed at 2
- synthetic 276-nt genome
- phenotype-based evaluation (PBET)
- explicit lineage/breeding custody
- ASCII, Pillow, and optional Pygame visualization
- forensic verification tools

This audit distinguishes **source repairs**, **repository checks**, and **execution evidence**.
No metric below is presented as a theoretical result; recorded numbers come from the execution log.

## Defect history

| ID | Area | Problem | Severity | Repair | Status |
|---|---|---|---|---|---|
| R3-1 | `evolution/population.py` | `def init(...)` instead of constructor dunder | Critical | Retyped as `def __init__(...)` | FIXED |
| R3-2 | `tests/test_phenotype_viz.py` | Test file truncated | Critical | Rewritten as complete visualization tests | FIXED |
| R3-3 | `evolution/population.py` | `slots`, `def len`, `def iter`, `def getitem` corruption | Critical | Restored `__slots__`, `__len__`, `__iter__`, `__getitem__` | FIXED |
| R3-4 | `tools/trace_offspring.py` | Corrupted/truncated content | Critical | Removed; superseded by explicit breeding log | REMOVED |
| R3-5 | `tools/trace_sprite.py` | Corrupted escape handling | Critical | Removed; deferred | REMOVED |
| R3-6 | `tests/import unittest.py` | Invalid filename and duplicate test | Critical | Deleted | REMOVED |
| R3-7 | package structure | `init.py` instead of `__init__.py` | Critical | Restored all package dunders | FIXED |
| R3-8 | lineage tracing | Child identity inferred from sets | Medium | Breeding log now stores explicit offspring order | FIXED |
| R3-9 | tests | Tests previously claimed unchanged without full source evidence | Medium | Test suite rewritten/attached in full during repair rounds | FIXED |
| R5-1 | package name | `new_bloon_new_project` conflicted with canonical package | Critical | Canonical package changed to `new_bloon` | FIXED |
| R5-2 | `cli.py` | Config path depended on working directory | Critical | Default config path anchored to `cli.py` location | FIXED |
| R5-3 | tests | Mixed package imports | Critical | All imports normalized to `new_bloon` | FIXED |
| R5-4 | `tests/test_import_graph.py` | Incorrect package root | Critical | Root corrected to canonical package | FIXED |
| R5-5 | PBET tests | Wrong import namespace | Critical | Imports normalized to `new_bloon.pbet...` | FIXED |
| R5-6 | visualization tests | Duplicate evolution coverage | Critical | Rewritten as visualization-focused tests | FIXED |
| R5-7 | repository | Garbage/foreign artifacts | Critical | Removed | REMOVED |
| R6-1 | `visualization/animation.py` | Windows CP1252 Unicode failure | Critical | Explicit UTF-8 file writes | FIXED |
| R7-1 | `cli.py` | Stale `new_bloon_new_project` imports | Critical | All normalized to `new_bloon` | FIXED |
| R7-2 | tests | Stale legacy imports | Critical | All normalized to `new_bloon` | FIXED |
| R7-3 | Pygame dependency | Standard `pygame` package failed to install on Python 3.14 in the observed environment | Medium | Switched optional dependency to `pygame-ce` | FIXED |
| R7-4 | `.gitignore` | `tools/` accidentally ignored | Medium | Forensic tools kept trackable | FIXED |
| R7-5 | repository | Legacy duplicate package remained during repair | Critical | Removed after canonical equivalence check | REMOVED |
| R7-6 | working tree | Generated experiment directories polluted repository | Low | Excluded/removed before publication | FIXED |
| R7-7 | documentation | README/audit contained stale or contradictory architecture text | Medium | Rewritten for final publication | FIXED |

## Architecture integrity

The enforced dependency boundary is:

```text
genome
   ↓
phenotype
   ↓
pbet
   ↓
evolution

visualization ← phenotype only

cli = orchestrator
```

The import-graph test explicitly rejects forbidden imports between these layers.

Core evaluation remains:

```text
Genome → Phenotype → PBET Candidate → SUT/Oracle → Observation → Fitness
```

Visualization is downstream-only and does not feed back into fitness or selection.

## Repository checks

The repository verifier checks:

1. canonical `new_bloon` package exists
2. required `__init__.py` files exist
3. legacy `new_bloon_new_project` is absent
4. stale `__pycache__` / `.pyc` are absent before compilation
5. known garbage files are absent
6. `default.json` is valid and `population_size == 2`
7. source contains no known dunder-corruption patterns
8. `compileall` succeeds
9. the unittest suite succeeds
10. `cli.py --help` succeeds

Final publication should be made only after the verifier reports:

```text
VERDICT: PASS
```

## Execution evidence — actual runs

### Static compilation

The canonical package and test/tool trees compiled successfully after cleanup, including:

```text
new_bloon/
  evolution/
  genome/
  pbet/
  phenotype/
  visualization/
tests/
tools/
cli.py
```

### Unit tests

Recorded final test run:

```text
Ran 83 tests in 0.694s

OK
```

Pygame was available during this run as:

```text
pygame-ce 2.5.8
SDL 2.32.10
Python 3.14.0
```

### CLI

`python cli.py --help` exposes:

```text
--seed
--generations
--config
--out
--no-elitism
--replay
--pygame
--pygame-fps
--pygame-frames
--pygame-dummy
```

The CLI describes Pygame as an optional visualization-only layer.

### 10-generation smoke run

Recorded with `seed=12345`:

```text
generations                = 10
individuals_created        = 42
offspring_created          = 40
crossover_events           = 20
mutation_events            = 84

initial_best_fitness       = 0.802132
final_best_fitness         = 0.838506
initial_mean_fitness       = 0.748318
final_mean_fitness         = 0.837693

initial_genetic_distance   = 0.807971
final_genetic_distance     = 0.221014

best_fitness_generation    = G010
generation_regressions     = 0
```

### 100-generation seeded run

Recorded with `seed=12345` and elitism enabled:

```text
individuals_created        = 402
offspring_created           = 400
crossover_events            = 200
mutation_events             = 724

initial_best_fitness        = 0.802132
final_best_fitness          = 0.939974
initial_mean_fitness        = 0.748318
final_mean_fitness          = 0.939960

initial_genetic_distance    = 0.807971
final_genetic_distance      = 0.003623

best_fitness_generation     = G098
worst_generation_regression = 0.0
generation_regressions      = 0
longest_no_improvement      = 7
```

The recorded mutation breakdown was:

```text
substitution     = 580
insertion        = 39
repair_truncate  = 38
deletion         = 34
repair_pad       = 33
```

### Same-seed reproducibility

Two independent runs with `seed=12345` produced matching deterministic artifacts for:

```text
config.json
seed.txt
generations.json
lineage.json
fitness.csv
phenotype.csv
animation/timeline.txt
animation/timeline_tags.txt
```

The reproducibility tooling treats GIF byte differences as a soft comparison case when necessary.

### Different seeds

Independent 100-generation runs were recorded for seeds:

```text
1
2
3
```

The trajectories were not identical and produced different terminal results, demonstrating that
the evolutionary process is seed-sensitive while remaining deterministic for a fixed seed.

### No-elitism

Recorded with:

```text
seed=12345
generations=100
elitism=False
```

Observed:

```text
final_best_fitness          = 0.897095
final_mean_fitness          = 0.897015
final_genetic_distance      = 0.007246
best_fitness_generation     = G090
worst_generation_regression = -0.005672
generation_regressions      = 32
longest_no_improvement      = 3
```

This run exhibits fitness regressions, which is expected because parents are excluded from the
selection pool.

## Forensic lineage evidence

The breeding tracer reports explicit custody from `lineage.json` and `breeding_log`.

Example recorded trace:

```text
=== chain of custody: I_00042 ===
I_00042 (G011) <- parents I_00040, I_00034
...
breeding event yang menghasilkan individu ini:
G011 single_point cuts=[44]
parents=(I_00040, I_00034)
offspring=['I_00042', 'I_00043']
(child index 0)
mutation events: 3
```

The child index is obtained directly from the ordered `offspring` list rather than inferred from
set differences.

## Pygame evidence

The interactive viewer was launched from replay:

```text
python cli.py --replay experiment --pygame
```

Recorded runtime:

```text
replay: 100 generations loaded from experiment
pygame-ce 2.5.8 (SDL 2.32.10, Python 3.14.0)
```

The viewer is explicitly visualization-only. Its geometry pipeline is:

```text
phenotype
   ↓
procedural morphology
   ↓
Pygame primitives
```

No monkey/gorilla image assets are used to determine phenotype.

A headless smoke-test mode is also available:

```text
--pygame-dummy
--pygame-frames N
```

## Publication checklist

Before the GitHub commit:

```text
[ ] python -m compileall new_bloon tests tools cli.py
[ ] python -m unittest discover -s tests -v
[ ] python cli.py --help
[ ] python cli.py --seed 12345 --generations 100 --out <clean-output>
[ ] same-seed reproducibility check
[ ] seeds 1 / 2 / 3
[ ] no-elitism run
[ ] Pygame interactive replay
[ ] Pygame headless smoke test
[ ] python tools/verify_repository.py
[ ] git status --short
[ ] final tree contains no generated experiment outputs
[ ] no __pycache__ / *.pyc committed
```

## Final interpretation

MBG2 v1 should be presented as a **computational evolutionary optimization benchmark**, not as
a claim of biological realism.

Its strongest reproducible properties are:

```text
small fixed population
synthetic genome
deterministic phenotype mapping
replaceable PBET SUT
explicit breeding custody
reproducible seeded execution
phenotype-only visualization
machine-checked dependency boundaries
```

The repository is publication-ready **only when the final verifier and final Git status pass on
the machine being used for the GitHub commit**.
