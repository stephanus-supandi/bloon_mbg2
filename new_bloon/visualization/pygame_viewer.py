"""Pygame procedural viewer - VISUALIZATION ONLY (telemetry consumer).

Pipeline:
    phenotype -> body model (pure geometry) -> pygame primitives

Modul ini TIDAK:
- meng-import genome / evolution / pbet (dijaga tests/test_import_graph.py)
- menerima genome, fitness, generation, atau target sebagai input gambar
- memakai aset gambar monkey/gorilla atau interpolasi apa pun

Pygame adalah dependency OPSIONAL. Core MBG2 berjalan penuh tanpa Pygame.
Geometry (phenotype_to_drawables) adalah pure function dan dapat diuji
tanpa pygame sama sekali.
"""
import argparse
import json
import os
import sys

from .morphology import morphology_from_phenotype
from .sprite import archetype_tag

CANVAS_W = 480
CANVAS_H = 640
GROUND_Y = 600

BG_COLOR = (24, 26, 32)
GROUND_COLOR = (70, 75, 60)
EYE_COLOR = (250, 250, 250)
TEXT_COLOR = (230, 230, 230)
FUR_LIGHT = (165, 135, 105)   # fur_density rendah
FUR_DARK = (60, 45, 35)       # fur_density tinggi


def _lerp(a, b, t):
    return a + (b - a) * t


def _fur_color(density):
    d = max(0.0, min(1.0, density))
    return tuple(int(_lerp(FUR_LIGHT[i], FUR_DARK[i], d)) for i in range(3))


def phenotype_to_drawables(p):
    """Pure function: phenotype dict -> list of primitive descriptors.

    Primitive: {"kind": "ellipse"|"line"|"circle", ...}
    Tidak membutuhkan pygame. Hanya 11 trait phenotype yang dibaca.
    """
    m = morphology_from_phenotype(p)
    d = []
    color = _fur_color(p["fur_density"])
    limb_w = max(3, int(4 + 10 * p["muscle_mass"]))

    cx = CANVAS_W / 2.0
    leg_len = 60.0 + 200.0 * p["leg_length"]
    hip_y = GROUND_Y - leg_len
    hip_x = cx
    lean = m["lean"] * 14.0  # posture rendah -> badan condong ke depan

    # legs
    spread = 18.0 + 14.0 * p["torso_width"]
    for s in (-1, 1):
        d.append({"kind": "line",
                  "start": (hip_x + s * spread * 0.4, hip_y),
                  "end": (hip_x + s * spread, GROUND_Y),
                  "color": color, "width": limb_w})

    # torso
    torso_w = m["torso_rx"] * 26.0
    torso_h = m["torso_ry"] * 24.0
    torso_cx = hip_x + lean * 0.35
    torso_cy = hip_y - torso_h / 2.0
    d.append({"kind": "ellipse",
              "rect": (torso_cx - torso_w / 2.0, torso_cy - torso_h / 2.0,
                       torso_w, torso_h),
              "color": color, "width": 0})

    # shoulders position
    shoulder_y = torso_cy - torso_h / 2.0 + 14.0
    shoulder_dx = torso_w / 2.0 + m["arm_rx"] * 6.0
    shoulder_x = torso_cx + lean * 0.15

    # arms: upper arm + forearm (proporsi = forearm_ratio)
    arm_total = m["arm_ry"] * 34.0
    fore = arm_total * p["forearm_ratio"]
    upper = arm_total - fore
    for s in (-1, 1):
        sx = shoulder_x + s * shoulder_dx
        elbow = (sx + s * 10.0, shoulder_y + upper)
        hand = (elbow[0] + s * 6.0, elbow[1] + fore)
        d.append({"kind": "line", "start": (sx, shoulder_y),
                  "end": elbow, "color": color, "width": limb_w})
        d.append({"kind": "line", "start": elbow, "end": hand,
                  "color": color, "width": max(2, limb_w - 2)})

    # shoulder mass
    sh_w = m["torso_rx"] * 30.0 * (0.6 + 0.4 * p["shoulder_width"])
    d.append({"kind": "ellipse",
              "rect": (shoulder_x - sh_w / 2.0, shoulder_y - 10.0,
                       sh_w, 20.0),
              "color": color, "width": 0})

    # head
    head_cx = shoulder_x + lean * 0.5
    head_cy = shoulder_y - m["head_ry"] * 20.0 - 6.0
    head_w = m["head_rx"] * 26.0
    head_h = m["head_ry"] * 26.0
    d.append({"kind": "ellipse",
              "rect": (head_cx - head_w / 2.0, head_cy - head_h / 2.0,
                       head_w, head_h),
              "color": color, "width": 0})

    # jaw / muzzle
    jaw_w = m["jaw_rx"] * 22.0
    jaw_h = max(6.0, jaw_w * 0.55)
    jaw_cx = head_cx + head_w * 0.28
    jaw_cy = head_cy + head_h * 0.22
    d.append({"kind": "ellipse",
              "rect": (jaw_cx - jaw_w / 2.0, jaw_cy - jaw_h / 2.0,
                       jaw_w, jaw_h),
              "color": color, "width": 0})

    # eyes
    for s in (-1, 1):
        d.append({"kind": "circle",
                  "center": (head_cx + s * head_w * 0.2,
                             head_cy - head_h * 0.1),
                  "radius": 3, "color": EYE_COLOR, "width": 0})

    # ground
    d.append({"kind": "line", "start": (0, GROUND_Y),
              "end": (CANVAS_W, GROUND_Y), "color": GROUND_COLOR, "width": 2})
    return d


def _require_pygame():
    try:
        import pygame
        return pygame
    except ImportError:
        return None


def draw_drawables(surface, drawables, offset_x=0, offset_y=0):
    pygame = _require_pygame()
    if pygame is None:
        raise RuntimeError("pygame tidak terpasang")
    for d in drawables:
        k = d["kind"]
        if k == "ellipse":
            x, y, w, h = d["rect"]
            pygame.draw.ellipse(
                surface, d["color"],
                (int(x + offset_x), int(y + offset_y),
                 max(1, int(w)), max(1, int(h))),
                d["width"])
        elif k == "circle":
            cx, cy = d["center"]
            pygame.draw.circle(
                surface, d["color"],
                (int(cx + offset_x), int(cy + offset_y)),
                max(1, int(d["radius"])), d["width"])
        elif k == "line":
            sx, sy = d["start"]
            ex, ey = d["end"]
            pygame.draw.line(
                surface, d["color"],
                (int(sx + offset_x), int(sy + offset_y)),
                (int(ex + offset_x), int(ey + offset_y)),
                max(1, d["width"]))


def load_records(path):
    """Baca generations.json (folder experiment atau file langsung)."""
    p = os.path.join(path, "generations.json") if os.path.isdir(path) else path
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError("generations.json kosong/invalid: " + p)
    return data


def run_viewer(records, fps=4, max_frames=None, dummy=False,
               title="MBG2 Pygame Viewer (visualization only)"):
    """Event loop:
    SPACE/RIGHT : generasi berikutnya   LEFT : sebelumnya
    A           : toggle autoplay (~1 generasi/detik)
    Q/ESC       : quit
    max_frames  : auto-advance lalu quit (smoke test)
    dummy       : SDL dummy video driver (headless)
    Return code: 0 ok, 2 records kosong, 3 pygame tidak terpasang.
    """
    pygame = _require_pygame()
    if pygame is None:
        print("ERROR: Pygame tidak terpasang.", file=sys.stderr)
        print("Install:  pip install pygame", file=sys.stderr)
        print("Core MBG2 tetap berjalan tanpa Pygame.", file=sys.stderr)
        return 3
    if not records:
        print("ERROR: records kosong", file=sys.stderr)
        return 2

    if dummy:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    pygame.init()
    win_w = CANVAS_W * 2
    win_h = CANVAS_H + 40
    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    idx = 0
    frames = 0
    auto = False
    tick_acc = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_RIGHT):
                    idx = min(idx + 1, len(records) - 1)
                elif event.key == pygame.K_LEFT:
                    idx = max(idx - 1, 0)
                elif event.key == pygame.K_a:
                    auto = not auto

        rec = records[idx]
        screen.fill(BG_COLOR)
        header = ("G{:03d} | best_fitness={} | auto={} | "
                  "SPACE/RIGHT: next  LEFT: prev  A: autoplay  Q/ESC: quit"
                  ).format(rec.get("generation", idx),
                           rec.get("best_fitness", "?"), auto)
        screen.blit(font.render(header, True, TEXT_COLOR), (10, 8))

        for slot, ind in enumerate(rec.get("population", [])[:2]):
            ph = ind.get("phenotype", {})
            drawables = phenotype_to_drawables(ph)
            draw_drawables(screen, drawables,
                           offset_x=slot * CANVAS_W, offset_y=40)
            label = "{}  fit={}  {}".format(
                ind.get("id", "?"), ind.get("fitness", "?"), archetype_tag(ph))
            screen.blit(font.render(label, True, TEXT_COLOR),
                        (slot * CANVAS_W + 10, win_h - 26))

        pygame.display.flip()
        clock.tick(fps)

        if auto:
            tick_acc += 1
            if tick_acc >= max(1, fps):
                tick_acc = 0
                idx = min(idx + 1, len(records) - 1)

        frames += 1
        if max_frames is not None:
            idx = min(idx + 1, len(records) - 1)
            if frames >= max_frames:
                running = False

    pygame.quit()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="MBG2 Pygame viewer (visualization only, no evolution)")
    ap.add_argument("--path", default="experiment",
                    help="folder experiment atau file generations.json")
    ap.add_argument("--fps", type=int, default=4)
    ap.add_argument("--frames", type=int, default=None,
                    help="auto-quit setelah N frame (smoke test)")
    ap.add_argument("--dummy", action="store_true",
                    help="SDL dummy video driver (headless)")
    args = ap.parse_args(argv)
    try:
        records = load_records(args.path)
    except (OSError, ValueError) as e:
        print("ERROR: {}".format(e), file=sys.stderr)
        return 2
    return run_viewer(records, fps=args.fps,
                      max_frames=args.frames, dummy=args.dummy)


if __name__ == "__main__":
    sys.exit(main())