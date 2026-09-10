"""Separation A-18, dicek mesin: engine/PBET tidak boleh import visualization;
visualization tidak boleh import genome/evolution/pbet."""
import ast
import os
import unittest

ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "new_bloon",
)

FORBIDDEN = {
    "evolution": {"visualization"},
    "pbet": {"visualization", "evolution"},
    "genome": {"visualization", "evolution", "pbet", "phenotype"},
    "phenotype": {"visualization", "evolution", "pbet"},
    "visualization": {"genome", "evolution", "pbet"},
}


class TestImportGraph(unittest.TestCase):
    def test_no_forbidden_imports(self):
        for pkg, forbidden in FORBIDDEN.items():
            pkg_dir = os.path.join(ROOT, pkg)
            self.assertTrue(
                os.path.isdir(pkg_dir),
                "package directory missing: {}".format(pkg_dir))

            for fn in sorted(os.listdir(pkg_dir)):
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(pkg_dir, fn)
                with open(path, encoding="utf-8", errors="replace") as f:
                    tree = ast.parse(f.read(), filename=path)

                for node in ast.walk(tree):
                    mods = []
                    if isinstance(node, ast.Import):
                        mods = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        mods = [node.module]

                    for m in mods:
                        parts = m.split(".")
                        for bad in forbidden:
                            self.assertNotIn(
                                bad, parts,
                                "{} imports {} (forbidden: {})".format(
                                    os.path.join(pkg, fn), m, bad))


if __name__ == "__main__":
    unittest.main()
