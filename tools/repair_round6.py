#!/usr/bin/env python3
"""
MBG2 Round 7 — Final cleanup, validation, and report generation.
Run: python round7_finalize.py
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"E:\bloon_mbg2")
PKG = ROOT / "new_bloon"
TESTS = ROOT / "tests"
TOOLS = ROOT / "tools"

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def run_cmd(cmd, desc):
    print(f"\n--- {desc} ---")
    print(f"CMD: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=str(ROOT), timeout=300
        )
        if result.stdout:
            print(result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
        print(f"EXIT CODE: {result.returncode}")
        return result
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def main():
    section("ROUND 7 — PHASE 1: CLEANUP")

    # 1. Move maintenance scripts to tools/
    TOOLS.mkdir(exist_ok=True)
    for script in ["repair_round6.py", "patch_utf8.py"]:
        src = ROOT / script
        if src.exists():
            shutil.move(str(src), str(TOOLS / script))
            print(f"moved: {script} -> tools/{script}")

    # 2. Clean __pycache__
    count = 0
    for p in list(ROOT.rglob("__pycache__")):
        try:
            shutil.rmtree(p)
            count += 1
        except Exception:
            pass
    print(f"removed {count} __pycache__ directories")

    # 3. Verify new_bloon_new_project is gone
    legacy = ROOT / "new_bloon_new_project"
    if legacy.exists():
        print("WARNING: new_bloon_new_project still exists!")
        print("Contents:", list(legacy.iterdir())[:10])
        # Do NOT auto-delete - require manual confirmation
    else:
        print("OK: new_bloon_new_project does not exist")

    # 4. Search for remaining references
    print("\nSearching for 'new_bloon_new_project' in .py files...")
    found = []
    for py in list(PKG.rglob("*.py")) + list(TESTS.rglob("*.py")) + [ROOT / "cli.py"]:
        if py.exists():
            try:
                content = py.read_text(encoding="utf-8", errors="replace")
                if "new_bloon_new_project" in content:
                    found.append(str(py))
            except Exception:
                pass
    if found:
        print(f"FOUND in {len(found)} files: {found}")
    else:
        print("OK: zero occurrences in source/tests")

    # 5. Update .gitignore
    gitignore_content = """__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/
experiment/
experiment_*/
exp_*/
.codeinsight/
.qodo/
tools/
round7_finalize.py
"""
    (ROOT / ".gitignore").write_text(gitignore_content, encoding="utf-8")
    print("updated: .gitignore")

    # 6. Verify package structure
    section("ROUND 7 — PHASE 2: STRUCTURE VERIFICATION")
    required_inits = [
        PKG / "__init__.py",
        PKG / "genome" / "__init__.py",
        PKG / "phenotype" / "__init__.py",
        PKG / "pbet" / "__init__.py",
        PKG / "evolution" / "__init__.py",
        PKG / "visualization" / "__init__.py",
    ]
    for init in required_inits:
        status = "OK" if init.exists() else "MISSING"
        print(f"  {status}: {init.relative_to(ROOT)}")

    config_path = PKG / "experiments" / "configs" / "default.json"
    print(f"  {'OK' if config_path.exists() else 'MISSING'}: {config_path.relative_to(ROOT)}")

    # 7. Verify UTF-8 encoding in animation.py
    anim = PKG / "visualization" / "animation.py"
    if anim.exists():
        content = anim.read_text(encoding="utf-8")
        if 'encoding="utf-8"' in content:
            print("  OK: animation.py has explicit UTF-8 encoding")
        else:
            print("  WARNING: animation.py missing explicit UTF-8")

    section("ROUND 7 — PHASE 3: COMPILE")
    r = run_cmd("python -m compileall new_bloon tests cli.py", "compileall (python)")

    section("ROUND 7 — PHASE 4: UNIT TESTS")
    r = run_cmd("python -m unittest discover -s tests -v", "unittest")

    section("ROUND 7 — PHASE 5: CLI HELP")
    r = run_cmd("python cli.py --help", "CLI help")

    section("ROUND 7 — PHASE 6: SMOKE RUN (10 gen)")
    # Clean previous
    smoke_dir = ROOT / "experiment_smoke"
    if smoke_dir.exists():
        shutil.rmtree(smoke_dir)
    r = run_cmd("python cli.py --seed 12345 --generations 10 --out experiment_smoke", "Smoke run")

    section("ROUND 7 — PHASE 7: FULL RUN (100 gen)")
    exp_dir = ROOT / "experiment"
    if exp_dir.exists():
        shutil.rmtree(exp_dir)
    r = run_cmd("python cli.py --seed 12345 --generations 100 --out experiment", "100-gen run")

    section("ROUND 7 — PHASE 8: REPRODUCIBILITY")
    for d in ["experiment_a", "experiment_b"]:
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p)
    run_cmd("python cli.py --seed 12345 --generations 100 --out experiment_a", "Repro A")
    run_cmd("python cli.py --seed 12345 --generations 100 --out experiment_b", "Repro B")

    # Compare
    compare_files = [
        "config.json", "seed.txt", "generations.json",
        "lineage.json", "fitness.csv", "phenotype.csv",
        os.path.join("animation", "timeline.txt"),
        os.path.join("animation", "timeline_tags.txt"),
    ]
    print("\n--- Same-seed comparison ---")
    all_match = True
    for f in compare_files:
        fa = ROOT / "experiment_a" / f
        fb = ROOT / "experiment_b" / f
        if fa.exists() and fb.exists():
            match = fa.read_bytes() == fb.read_bytes()
            print(f"  {f:40s} {'IDENTICAL' if match else 'DIFFERENT'}")
            if not match:
                all_match = False
        else:
            print(f"  {f:40s} MISSING")
            all_match = False
    print(f"\n  Reproducibility: {'PASS' if all_match else 'FAIL'}")

    section("ROUND 7 — PHASE 9: DIFFERENT SEEDS")
    for s in [1, 2, 3]:
        d = ROOT / f"experiment_s{s}"
        if d.exists():
            shutil.rmtree(d)
        run_cmd(f"python cli.py --seed {s} --generations 100 --out experiment_s{s}", f"Seed {s}")

    # Compare trajectories
    print("\n--- Different-seed comparison ---")
    for s in [1, 2, 3]:
        gen_file = ROOT / f"experiment_s{s}" / "generations.json"
        if gen_file.exists():
            data = json.loads(gen_file.read_text(encoding="utf-8"))
            last = data[-1]
            print(f"  Seed {s}: final_best={last['best_fitness']}, "
                  f"genetic_dist={last['genetic_distance_A_B']}")

    section("ROUND 7 — PHASE 10: NO-ELITISM RUN")
    ne_dir = ROOT / "experiment_no_elitism"
    if ne_dir.exists():
        shutil.rmtree(ne_dir)
    r = run_cmd("python cli.py --seed 12345 --generations 100 --out experiment_no_elitism --no-elitism", "No-elitism")

    section("ROUND 7 — PHASE 11: ARTIFACT INSPECTION")
    # Check sprite files exist
    sprites_dir = ROOT / "experiment" / "sprites"
    if sprites_dir.exists():
        sprite_files = sorted(sprites_dir.glob("*.txt"))
        print(f"  Sprite files: {len(sprite_files)}")
        if sprite_files:
            # Show first sprite
            print(f"\n  Sample sprite ({sprite_files[0].name}):")
            content = sprite_files[0].read_text(encoding="utf-8")
            for line in content.split("\n")[:12]:
                print(f"    {line}")
    else:
        print("  WARNING: sprites directory missing")

    # Check animation
    anim_dir = ROOT / "experiment" / "animation"
    if anim_dir.exists():
        tags_file = anim_dir / "timeline_tags.txt"
        if tags_file.exists():
            lines = tags_file.read_text(encoding="utf-8").strip().split("\n")
            print(f"\n  Timeline tags ({len(lines)} lines):")
            for line in lines[:5]:
                print(f"    {line}")
            print(f"    ...")
            for line in lines[-3:]:
                print(f"    {line}")

    section("ROUND 7 — PHASE 12: EVOLUTION STATISTICS")
    # Parse from experiment run
    gen_file = ROOT / "experiment" / "generations.json"
    if gen_file.exists():
        data = json.loads(gen_file.read_text(encoding="utf-8"))
        first = data[0]
        last = data[-1]
        best_gen = max(data, key=lambda r: r["best_fitness"])
        print(f"  seed                    = 12345")
        print(f"  generations             = {len(data) - 1}")
        print(f"  initial_best_fitness    = {first['best_fitness']}")
        print(f"  final_best_fitness      = {last['best_fitness']}")
        print(f"  initial_mean_fitness    = {first['mean_fitness']}")
        print(f"  final_mean_fitness      = {last['mean_fitness']}")
        print(f"  initial_genetic_dist    = {first['genetic_distance_A_B']}")
        print(f"  final_genetic_dist      = {last['genetic_distance_A_B']}")
        print(f"  best_fitness_generation = G{best_gen['generation']:03d}")

        # Check population invariant
        pop_ok = all(len(r["population"]) == 2 for r in data)
        print(f"  population_invariant    = {'OK' if pop_ok else 'VIOLATED'}")

        # Diversity check
        final_dist = last["genetic_distance_A_B"]
        if final_dist < 0.01:
            print(f"  diversity_status        = CONVERGED (dist={final_dist})")
        else:
            print(f"  diversity_status        = DIVERSE (dist={final_dist})")

    section("ROUND 7 — DONE")
    print("\nAll phases complete. Review output above for final report.")
    return 0

if __name__ == "__main__":
    sys.exit(main())