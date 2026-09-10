#!/usr/bin/env python3
"""Forensic breeding tracer - membaca mapping EKSPLISIT dari lineage.json.

TIDAK ADA inferensi set/heuristik. Semua berasal dari log:
    breeding_log : generation, method, cut_points, parent_a, parent_b,
                   offspring = [child1_id, child2_id]  (index = urutan crossover)
    lineage      : id -> generation, parents
    mutation_log : event per individu

Usage:
    python tools/trace_breeding.py experiment
    python tools/trace_breeding.py experiment --generation 3
    python tools/trace_breeding.py experiment --id I_00042
"""
import argparse
import json
import os
import sys


def load_lineage(path):
    p = os.path.join(path, "lineage.json") if os.path.isdir(path) else path
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    by_id = {e["id"]: e for e in data["lineage"]}
    return data, by_id


def ancestry(by_id, individual_id):
    """Chain of custody eksplisit: child -> parents -> ... -> founders."""
    chain = []
    stack = [(individual_id, 0)]
    seen = set()
    while stack:
        cur, depth = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        entry = by_id.get(cur)
        if entry is None:
            chain.append((depth, cur, "UNKNOWN-ID"))
            continue
        chain.append((depth, cur, entry))
        for p in entry.get("parents", []):
            stack.append((p, depth + 1))
    return chain


def format_ancestry(chain):
    lines = []
    for depth, iid, entry in sorted(chain, key=lambda x: (x[0], x[1])):
        indent = "  " * depth
        if isinstance(entry, dict):
            g = entry.get("generation")
            parents = entry.get("parents", [])
            if parents:
                lines.append("{}{} (G{:03d}) <- parents {}".format(
                    indent, iid, g, ", ".join(parents)))
            else:
                lines.append("{}{} (G{:03d}) <- FOUNDER".format(indent, iid, g))
        else:
            lines.append("{}{} <- {}".format(indent, iid, entry))
    return lines


def events_for(data, individual_id):
    breeding = [e for e in data.get("breeding_log", [])
                if individual_id in e.get("offspring", [])]
    mutations = [m for m in data.get("mutation_log", [])
                 if m.get("individual") == individual_id]
    return breeding, mutations


def format_generation(data, by_id, gen):
    lines = ["Generation {:03d}".format(gen)]
    events = [e for e in data.get("breeding_log", [])
              if e.get("generation") == gen]
    for e in events:
        for idx, child in enumerate(e.get("offspring", [])):
            lines.append("")
            lines.append("  child {} ({})".format(idx, child))
            lines.append("    parent_a   = {}".format(e.get("parent_a")))
            lines.append("    parent_b   = {}".format(e.get("parent_b")))
            lines.append("    crossover  = {} cuts={}".format(
                e.get("method"), e.get("cut_points")))
            muts = [m for m in data.get("mutation_log", [])
                    if m.get("individual") == child]
            if muts:
                for m in muts:
                    lines.append(
                        "    mutation   = {} pos={} {}->{} locus={}".format(
                            m.get("kind"), m.get("position"),
                            m.get("before"), m.get("after"), m.get("locus")))
            else:
                lines.append("    mutation   = (none)")
    if not events:
        lines.append("  (tidak ada breeding event pada generasi ini)")
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="MBG2 forensic breeding tracer")
    ap.add_argument("experiment", help="folder experiment atau lineage.json")
    ap.add_argument("--generation", type=int, default=None)
    ap.add_argument("--id", default=None)
    args = ap.parse_args(argv)
    try:
        data, by_id = load_lineage(args.experiment)
    except (OSError, ValueError, KeyError) as e:
        print("ERROR: {}".format(e), file=sys.stderr)
        return 2

    if args.id:
        if args.id not in by_id:
            print("ERROR: id {} tidak ditemukan".format(args.id),
                  file=sys.stderr)
            return 2
        b, m = events_for(data, args.id)
        print("=== chain of custody: {} ===".format(args.id))
        for line in format_ancestry(ancestry(by_id, args.id)):
            print(line)
        if b:
            print("")
            print("breeding event yang menghasilkan individu ini:")
            for e in b:
                idx = e["offspring"].index(args.id)
                print("  G{:03d} {} cuts={} parents=({}, {}) "
                      "offspring={} (child index {})".format(
                          e["generation"], e["method"], e["cut_points"],
                          e["parent_a"], e["parent_b"], e["offspring"], idx))
        print("mutation events: {}".format(len(m)))
        return 0

    gen = args.generation
    if gen is None:
        all_gens = sorted({e["generation"]
                           for e in data.get("breeding_log", [])})
        gen = all_gens[0] if all_gens else 1
    for line in format_generation(data, by_id, gen):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())