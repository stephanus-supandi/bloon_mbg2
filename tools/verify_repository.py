#!/usr/bin/env python3
"""MBG2 repository sanity verifier - SEMUA check dari filesystem/eksekusi nyata.

Checks:
  1. canonical package new_bloon + semua __init__.py
  2. legacy new_bloon_new_project absent
  3. __pycache__/*.pyc absent (sebelum compile)
  4. garbage files absent
  5. default.json valid, population_size == 2
  6. dunder-corruption scan pada source canonical
  7. python -m compileall  (eksekusi nyata)
  8. python -m unittest    (eksekusi nyata)
  9. cli.py --help         (eksekusi nyata)

Usage:  python tools/verify_repository.py [--fast]
Exit:   0 semua PASS, 1 ada FAIL.
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "new_bloon")

REQUIRED_INITS = [
    os.path.join(PKG, "__init__.py"),
    os.path.join(PKG, "genome", "__init__.py"),
    os.path.join(PKG, "phenotype", "__init__.py"),
    os.path.join(PKG, "pbet", "__init__.py"),
    os.path.join(PKG, "evolution", "__init__.py"),
    os.path.join(PKG, "visualization", "__init__.py"),
]

GARBAGE = [
    os.path.join(ROOT, "new_bloon_new_project"),
    os.path.join(ROOT, "tests", "traits.py"),
    os.path.join(ROOT, "tests", "import unittest.py"),
]

DUNDER_PATTERNS = [
    "def init(", "def len(", "def iter(", "def getitem(",
    "def str(", "def repr(", "from future import", "if name ==",
]

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print("[{}] {}{}".format("PASS" if ok else "FAIL", name,
                             (" - " + str(detail)) if detail and not ok else ""))
    return ok


def scan_dunder_corruption():
    bad = []
    files = [os.path.join(ROOT, "cli.py")]
    for r in (PKG, os.path.join(ROOT, "tests")):
        for dirpath, dirnames, filenames in os.walk(r):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if fn.endswith(".py"):
                    files.append(os.path.join(dirpath, fn))
    for path in files:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        for pat in DUNDER_PATTERNS:
            if pat in text:
                bad.append((os.path.relpath(path, ROOT), pat))
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description="MBG2 repository verifier")
    ap.add_argument("--fast", action="store_true",
                    help="skip subprocess (compileall/unittest/cli)")
    args = ap.parse_args(argv)

    check("canonical package new_bloon exists", os.path.isdir(PKG))
    missing = [os.path.relpath(p, ROOT) for p in REQUIRED_INITS
               if not os.path.isfile(p)]
    check("all __init__.py present", not missing, missing)
    check("legacy new_bloon_new_project absent",
          not os.path.exists(os.path.join(ROOT, "new_bloon_new_project")))

    caches = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if "__pycache__" in dirnames:
            caches.append(os.path.relpath(
                os.path.join(dirpath, "__pycache__"), ROOT))
            dirnames.remove("__pycache__")
    check("no stale __pycache__ (pre-compile)", not caches, caches[:5])

    garb = [os.path.relpath(g, ROOT) for g in GARBAGE if os.path.exists(g)]
    check("garbage absent", not garb, garb)

    js = []
    for dirpath, dirnames, filenames in os.walk(PKG):
        for fn in filenames:
            if fn.endswith(".electron-builder.js"):
                js.append(fn)
    check("no foreign js artifacts in package", not js, js)

    cfg_path = os.path.join(PKG, "experiments", "configs", "default.json")
    ok, detail = True, ""
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
        if cfg.get("population_size") != 2:
            ok, detail = False, "population_size != 2"
    except (OSError, ValueError) as e:
        ok, detail = False, repr(e)
    check("default.json valid (population_size=2)", ok, detail)

    bad = scan_dunder_corruption()
    check("dunder corruption scan clean", not bad, bad[:5])

    if not args.fast:
        exe = sys.executable
        r = subprocess.run(
            [exe, "-m", "compileall", "-q", "new_bloon", "tests", "tools",
             "cli.py"],
            cwd=ROOT, capture_output=True, text=True)
        check("compileall (real execution)", r.returncode == 0,
              (r.stdout + r.stderr)[-500:])

        r = subprocess.run(
            [exe, "-m", "unittest", "discover", "-s", "tests"],
            cwd=ROOT, capture_output=True, text=True)
        tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
        check("unittest (real execution)", r.returncode == 0, " | ".join(tail))

        r = subprocess.run([exe, "cli.py", "--help"],
                           cwd=ROOT, capture_output=True, text=True)
        check("cli.py --help (real execution)", r.returncode == 0,
              r.stderr[-300:])

    fails = [n for n, ok in results if not ok]
    print("")
    print("SUMMARY: {} checks, {} FAIL".format(len(results), len(fails)))
    for n in fails:
        print("  FAIL:", n)
    print("VERDICT:", "PASS" if not fails else "FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())