#!/usr/bin/env python3
"""Bandingkan dua directory experiment untuk reproducibility.

Usage:
    python tools/check_reproducibility.py experiment_a experiment_b

Byte-level compare (SHA-256) untuk SEMUA file.
animation.gif diperlakukan SOFT: jika berbeda -> WARNING bukan FAIL
(encoder GIF dapat menyisipkan metadata nondeterministik).
Seluruh artifact teks/JSON/CSV/sprite WAJIB byte-identical.

Exit code: 0 = PASS, 1 = FAIL, 2 = usage error.
"""
import hashlib
import os
import sys

SOFT_BASENAMES = {"animation.gif"}


def _collect(root):
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            files[rel] = full
    return files


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compare_dirs(dir_a, dir_b):
    fa, fb = _collect(dir_a), _collect(dir_b)
    only_a = sorted(set(fa) - set(fb))
    only_b = sorted(set(fb) - set(fa))
    hard_diff, soft_diff, identical = [], [], 0
    for rel in sorted(set(fa) & set(fb)):
        if _sha256(fa[rel]) == _sha256(fb[rel]):
            identical += 1
        elif os.path.basename(rel) in SOFT_BASENAMES:
            soft_diff.append(rel)
        else:
            hard_diff.append(rel)
    ok = not only_a and not only_b and not hard_diff
    return {"status": "PASS" if ok else "FAIL",
            "identical": identical,
            "hard_diff": hard_diff,
            "soft_diff": soft_diff,
            "only_a": only_a,
            "only_b": only_b}


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    if not os.path.isdir(argv[1]) or not os.path.isdir(argv[2]):
        print("ERROR: kedua argumen harus directory experiment")
        return 2
    res = compare_dirs(argv[1], argv[2])
    print("compare: {} vs {}".format(argv[1], argv[2]))
    print("identical files : {}".format(res["identical"]))
    if res["soft_diff"]:
        print("SOFT (warning)  : {}".format(res["soft_diff"]))
    if res["hard_diff"]:
        print("HARD DIFF       : {}".format(res["hard_diff"]))
    if res["only_a"]:
        print("only in A       : {}".format(res["only_a"]))
    if res["only_b"]:
        print("only in B       : {}".format(res["only_b"]))
    print(res["status"])
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))