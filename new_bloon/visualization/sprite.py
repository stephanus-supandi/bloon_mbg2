"""Procedural ASCII sprite rasterizer: sprite = G(phenotype).
Renderer menerima PHENOTYPE ONLY. Tidak pernah menerima genome, fitness,
generation, atau gorilla target; tidak ada lookup target, tidak ada
branching berdasarkan generation atau fitness. Tidak ada interpolasi
monkey.png / gorilla.png di mana pun.
Archetype tag: TELEMETRY ONLY, dihitung dari phenotype vector lewat
weighted-sum heuristic terdokumentasi atas 8 trait. Tidak pernah
mempengaruhi fitness, selection, mutation, atau recombination (dijaga oleh
import graph: tidak ada modul genome/pbet/evolution yang meng-import modul
ini — dicek oleh tests/test_import_graph.py).
"""
import math
from .morphology import morphology_from_phenotype

ROWS = 21
COLS = 31


def fur_char(density):
    if density < 0.33:
        return "."
    if density < 0.66:
        return ":"
    return "#"


def _fill(cv, cx, cy, rx, ry, ch):
    rx = max(rx, 0.4)
    ry = max(ry, 0.4)
    y0 = max(0, int(math.floor(cy - ry)))
    y1 = min(ROWS, int(math.ceil(cy + ry)) + 1)
    x0 = max(0, int(math.floor(cx - rx)))
    x1 = min(COLS, int(math.ceil(cx + rx)) + 1)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                cv[y][x] = ch


def _put(cv, x, y, ch):
    xi = int(round(x))
    yi = int(round(y))
    if 0 <= yi < ROWS and 0 <= xi < COLS:
        cv[yi][xi] = ch


def render_sprite(phenotype):
    m = morphology_from_phenotype(phenotype)
    ch = fur_char(phenotype["fur_density"])
    cv = [[" "] * COLS for _ in range(ROWS)]
    cx = COLS // 2
    base = ROWS - 2

    leg_ry = m["leg_ry"]
    _fill(cv, cx - 2, base - leg_ry, m["leg_rx"], leg_ry, ch)
    _fill(cv, cx + 2, base - leg_ry, m["leg_rx"], leg_ry, ch)

    torso_cy = base - 2 * leg_ry - m["torso_ry"]
    _fill(cv, cx, torso_cy, m["torso_rx"], m["torso_ry"], ch)

    sh_y = torso_cy - m["torso_ry"] + 1.5
    for s in (-1, 1):
        ax = cx + s * (m["torso_rx"] + m["arm_rx"])
        _fill(cv, ax, sh_y + m["arm_ry"], m["arm_rx"], m["arm_ry"], ch)

    hx = cx + m["lean"]
    hy = torso_cy - m["torso_ry"] - m["head_ry"] + 1.5
    _fill(cv, hx, hy, m["head_rx"], m["head_ry"], ch)
    _fill(cv, hx + m["head_rx"] * 0.9, hy + m["head_ry"] * 0.5,
          m["jaw_rx"], max(m["jaw_rx"] * 0.6, 0.5), ch)
    _put(cv, hx - 1, hy - 0.5, "o")
    _put(cv, hx + 1, hy - 0.5, "o")

    return "\n".join("".join(row).rstrip() for row in cv)


def archetype_tag(p):
    """Phenotype-only telemetry heuristic (lihat docstring modul)."""
    s = (p["body_size"] + p["torso_width"] + p["shoulder_width"]
         + p["muscle_mass"] + p["jaw_size"] + p["arm_length"]
         + (1.0 - p["leg_length"]) + (1.0 - p["posture"])) / 8.0
    if s >= 0.78:
        return "GORILLA-like"
    if s >= 0.62:
        return "GREAT-APE-like"
    if s >= 0.45:
        return "MACAQUE-like"
    return "MONKEY-like"


TAG_EMOJI = {
    "GORILLA-like": "\U0001F98D",
    "GREAT-APE-like": "\U0001F9A7",
    "MACAQUE-like": "\U0001F435",
    "MONKEY-like": "\U0001F412",
}