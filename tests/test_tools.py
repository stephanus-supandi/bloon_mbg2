"""Behavioural tests untuk forensic tools (bukan sekadar import test)."""
import importlib.util
import json
import os
import shutil
import tempfile
import unittest

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "tools")


def _load_tool(filename, alias):
    path = os.path.join(_TOOLS, filename)
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


check_repro = _load_tool("check_reproducibility.py", "mbg2_check_repro")
trace = _load_tool("trace_breeding.py", "mbg2_trace_breeding")


class TestCheckReproducibility(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.a = os.path.join(self.tmp, "a")
        self.b = os.path.join(self.tmp, "b")
        os.makedirs(self.a)
        os.makedirs(self.b)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, root, rel, content):
        p = os.path.join(root, rel)
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

    def test_identical_pass(self):
        for root in (self.a, self.b):
            self._write(root, "config.json", '{"seed": 1}')
            self._write(root, os.path.join("animation", "timeline.txt"),
                        "G000 x")
        res = check_repro.compare_dirs(self.a, self.b)
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["identical"], 2)
        self.assertEqual(res["hard_diff"], [])

    def test_content_diff_fail(self):
        self._write(self.a, "seed.txt", "1")
        self._write(self.b, "seed.txt", "2")
        res = check_repro.compare_dirs(self.a, self.b)
        self.assertEqual(res["status"], "FAIL")
        self.assertIn("seed.txt", res["hard_diff"])

    def test_missing_file_fail(self):
        self._write(self.a, "lineage.json", "{}")
        res = check_repro.compare_dirs(self.a, self.b)
        self.assertEqual(res["status"], "FAIL")
        self.assertIn("lineage.json", res["only_a"])

    def test_gif_diff_is_soft_not_fail(self):
        self._write(self.a, os.path.join("animation", "animation.gif"), "AAA")
        self._write(self.b, os.path.join("animation", "animation.gif"), "BBB")
        res = check_repro.compare_dirs(self.a, self.b)
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["soft_diff"], ["animation/animation.gif"])


LINEAGE_FIXTURE = {
    "lineage": [
        {"id": "I_00000", "generation": 0, "parents": []},
        {"id": "I_00001", "generation": 0, "parents": []},
        {"id": "I_00002", "generation": 1,
         "parents": ["I_00000", "I_00001"]},
    ],
    "breeding_log": [
        {"generation": 1, "method": "single_point", "cut_points": [100],
         "parent_a": "I_00000", "parent_b": "I_00001",
         "offspring": ["I_00002", "I_00003"]},
    ],
    "mutation_log": [
        {"generation": 1, "individual": "I_00002", "kind": "substitution",
         "position": 40, "before": "A", "after": "G", "locus": "locus_02"},
    ],
}


class TestTraceBreeding(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        with open(os.path.join(self.tmp, "lineage.json"), "w",
                  encoding="utf-8") as f:
            json.dump(LINEAGE_FIXTURE, f)
        self.data, self.by_id = trace.load_lineage(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_ancestry_chain_explicit(self):
        chain = trace.ancestry(self.by_id, "I_00002")
        ids = {c[1] for c in chain}
        self.assertEqual(ids, {"I_00002", "I_00000", "I_00001"})
        text = "\n".join(trace.format_ancestry(chain))
        self.assertIn("FOUNDER", text)
        self.assertIn("parents I_00000, I_00001", text)

    def test_events_for_child(self):
        breeding, muts = trace.events_for(self.data, "I_00002")
        self.assertEqual(len(breeding), 1)
        self.assertEqual(breeding[0]["parent_a"], "I_00000")
        self.assertEqual(breeding[0]["offspring"][0], "I_00002")
        self.assertEqual(len(muts), 1)
        self.assertEqual(muts[0]["kind"], "substitution")

    def test_format_generation_explicit_mapping(self):
        text = "\n".join(trace.format_generation(self.data, self.by_id, 1))
        self.assertIn("parent_a   = I_00000", text)
        self.assertIn("parent_b   = I_00001", text)
        self.assertIn("single_point", text)
        self.assertIn("substitution", text)
        self.assertIn("child 0 (I_00002)", text)
        self.assertIn("child 1 (I_00003)", text)

    def test_format_generation_empty(self):
        text = "\n".join(trace.format_generation(self.data, self.by_id, 99))
        self.assertIn("tidak ada breeding event", text)


if __name__ == "__main__":
    unittest.main()