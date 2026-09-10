#!/usr/bin/env python3
"""MBG2 final pre-GitHub cleanup.

Performs:
  1. Update pygame -> pygame-ce in requirements.txt
  2. Update pygame_viewer.py install message
  3. Rewrite .gitignore (tools/ NOT ignored)
  4. Remove experiment_* and exp_* artifact directories
  5. Remove __pycache__ and *.pyc from everywhere
  6. Verify no new_bloon_new_project remains

Does NOT touch source logic. Does NOT run tests.
Run: python tools/final_github_prep.py
"""
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "new_bloon"
LEGACY = ROOT / "new_bloon_new_project"

REQUIREMENTS = """# Core MBG2: Python >= 3.9, standard library only.
# Optional visualization dependencies:
Pillow>=9.0
pygame-ce>=2.3
"""

GITIGNORE = """# Python bytecode
__pycache__/
*.py[cod]
*$py.class
*.pyo

# Packaging / build
*.egg-info/
*.egg
dist/
build/
.eggs/
.pytest_cache/

# Experiment output (generated artifacts, NOT source)
experiment/
experiment_*/
exp_*/

# IDE / editor
.codeinsight/
.qodo/
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
"""

VIEWER_INSTALL_HINT = "Install:  pip install pygame"
VIEWER_INSTALL_NEW = "Install:  pip install pygame-ce  # community edition, supports Python 3.13+ (pip install pygame fails on 3.14)"


def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def handle_legacy():
    if LEGACY.exists():
        print(f"REMOVING legacy: {LEGACY}")
        shutil.rmtree(LEGACY)
        print("  removed.")
    else:
        print(f"legacy absent: {LEGACY.name} (OK)")


def update_requirements():
    path = ROOT / "requirements.txt"
    path.write_text(REQUIREMENTS, encoding="utf-8")
    print(f"wrote: {path.name}")


def update_gitignore():
    path = ROOT / ".gitignore"
    path.write_text(GITIGNORE, encoding="utf-8")
    print(f"wrote: {path.name}")
    # Verify tools/ is NOT ignored
    if re.search(r'^tools/?$', GITIGNORE, re.MULTILINE):
        print("  WARNING: tools/ is ignored - FIX .gitignore")
    else:
        print("  OK: tools/ is NOT ignored")


def update_pygame_viewer_message():
    path = PKG / "visualization" / "pygame_viewer.py"
    if not path.exists():
        print(f"SKIP: {path.name} not found")
        return
    content = path.read_text(encoding="utf-8")
    if "pygame-ce" in content and "pygame" in content:
        print(f"already updated: {path.name}")
        return
    # Replace the error message
    new = content.replace(VIEWER_INSTALL_HINT, VIEWER_INSTALL_NEW)
    if new == content:
        print(f"  WARNING: install hint not found in {path.name}")
        return
    path.write_text(new, encoding="utf-8")
    print(f"updated install hint in: {path.name}")


def clean_experiment_artifacts():
    removed = 0
    for name in os.listdir(ROOT):
        p = ROOT / name
        if p.is_dir() and (name == "experiment" or
                          name.startswith("experiment_") or
                          name.startswith("exp_")):
            try:
                shutil.rmtree(p)
                print(f"  removed: {name}/")
                removed += 1
            except OSError as e:
                print(f"  FAILED to remove {name}: {e}")
    print(f"total experiment artifacts removed: {removed}")


def clean_pycache():
    n_dirs = 0
    n_files = 0
    for root, dirs, files in os.walk(ROOT, topdown=False):
        # remove __pycache__ directories
        if os.path.basename(root) == "__pycache__":
            try:
                shutil.rmtree(root)
                n_dirs += 1
            except OSError:
                pass
        # remove .pyc files outside __pycache__
        for fn in files:
            if fn.endswith(".pyc") or fn.endswith(".pyo"):
                try:
                    os.remove(os.path.join(root, fn))
                    n_files += 1
                except OSError:
                    pass
    print(f"removed {n_dirs} __pycache__ directories")
    print(f"removed {n_files} stray .pyc/.pyo files")


def verify_no_legacy_imports():
    needle = "new_bloon_new_project"
    found = []
    search_roots = [PKG, ROOT / "tests", ROOT / "tools"] + [ROOT]
    for r in search_roots:
        if not r.exists():
            continue
        for p in r.rglob("*.py"):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                if needle in text:
                    found.append(p.relative_to(ROOT))
            except OSError:
                pass
    # Also check cli.py at root
    cli = ROOT / "cli.py"
    if cli.exists():
        text = cli.read_text(encoding="utf-8", errors="replace")
        if needle in text:
            found.append(Path("cli.py"))
    if found:
        print("FAIL: legacy import references still present:")
        for f in found:
            print(f"  {f}")
        return False
    print("OK: zero legacy import references")
    return True


def main():
    print("ROOT:", ROOT)
    section("1. LEGACY REMOVAL")
    handle_legacy()

    section("2. REQUIREMENTS.TXT (pygame -> pygame-ce)")
    update_requirements()

    section("3. .GITIGNORE (tools/ NOT ignored)")
    update_gitignore()

    section("4. PYGAME_VIEWER INSTALL MESSAGE")
    update_pygame_viewer_message()

    section("5. EXPERIMENT ARTIFACT CLEANUP")
    clean_experiment_artifacts()

    section("6. BYTECODE CLEANUP")
    clean_pycache()

    section("7. LEGACY IMPORT VERIFICATION")
    ok = verify_no_legacy_imports()

    section("DONE")
    if ok:
        print("Prep complete. Repository ready for GitHub commit check.")
        return 0
    else:
        print("Prep INCOMPLETE: legacy imports remain. Fix manually.")
        return 1


if __name__ == "__main__":
    sys.exit(main())