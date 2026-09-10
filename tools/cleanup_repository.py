#!/usr/bin/env python3
"""MBG2 final cleanup: legacy removal, pycache, garbage, root hygiene.
Legacy new_bloon_new_project HANYA dihapus jika setiap file punya
counterpart di new_bloon. Kalau tidak, abort dan laporkan.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEGACY = ROOT / "new_bloon_new_project"
CANON = ROOT / "new_bloon"

GARBAGE_FILES = [
    ROOT / "tests" / "traits.py",
    ROOT / "tests" / "import unittest.py",
]


def clean_pycache():
    n = 0
    for p in list(ROOT.rglob("__pycache__")):
        try:
            shutil.rmtree(p)
            n += 1
        except OSError as e:
            print("WARN pycache:", p, e)
    for p in list(ROOT.rglob("*.pyc")):
        try:
            p.unlink()
        except OSError:
            pass
    print("pycache dirs removed:", n)


def clean_garbage():
    for g in GARBAGE_FILES:
        if g.exists():
            g.unlink()
            print("deleted garbage:", g)
    for js in list(ROOT.rglob("*.electron-builder.js")):
        js.unlink()
        print("deleted foreign artifact:", js)


def handle_legacy():
    if not LEGACY.exists():
        print("legacy: absent (OK)")
        return True
    if not CANON.exists():
        LEGACY.rename(CANON)
        print("legacy renamed -> new_bloon (satu-satunya source)")
        return True
    missing, differ = [], []
    for f in LEGACY.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(LEGACY)
        if "__pycache__" in rel.parts or rel.suffix == ".pyc":
            continue
        c = CANON / rel
        if not c.exists():
            missing.append(str(rel))
        elif f.read_bytes() != c.read_bytes():
            differ.append(str(rel))
    if missing:
        print("ABORT: legacy punya file tanpa counterpart di new_bloon:")
        for m in missing:
            print("   ", m)
        return False
    if differ:
        print("note: {} file legacy berbeda isi (canonical new_bloon yang menang):".format(len(differ)))
        for d in differ[:20]:
            print("   ", d)
    shutil.rmtree(LEGACY)
    print("legacy new_bloon_new_project REMOVED (canonical lengkap)")
    return True


def root_hygiene():
    tools = ROOT / "tools"
    tools.mkdir(exist_ok=True)
    for name in ["repair_round6.py", "patch_utf8.py",
                 "round7_finalize.py", "finalize_mbg2.py"]:
        src = ROOT / name
        if src.exists():
            dst = tools / name
            if dst.exists():
                dst.unlink()
            shutil.move(str(src), str(dst))
            print("moved to tools/:", name)


def main():
    print("ROOT:", ROOT)
    ok = handle_legacy()
    clean_garbage()
    clean_pycache()
    root_hygiene()
    print("CLEANUP:", "OK" if ok else "INCOMPLETE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())