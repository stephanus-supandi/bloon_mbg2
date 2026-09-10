"""Generation timeline artifacts. GIF opsional via Pillow; tidak pernah wajib.
Tidak ada timestamp yang ditulis ke artifact deterministik.
"""
import os
from .sprite import render_sprite, archetype_tag, TAG_EMOJI


def _side_by_side(s1, s2, gap="   |   "):
    r1 = s1.split("\n")
    r2 = s2.split("\n")
    w1 = max(len(x) for x in r1)
    return "\n".join(a.ljust(w1) + gap + b for a, b in zip(r1, r2))


def write_animation(records, out_dir):
    sprite_dir = os.path.join(out_dir, "sprites")
    anim_dir = os.path.join(out_dir, "animation")
    os.makedirs(sprite_dir, exist_ok=True)
    os.makedirs(anim_dir, exist_ok=True)

    timeline = []
    tagline = []

    for rec in records:
        g = rec["generation"]
        parts = []
        tags = []
        for ind in rec["population"]:
            sprite = render_sprite(ind["phenotype"])
            tag = archetype_tag(ind["phenotype"])
            tags.append(TAG_EMOJI[tag])
            fname = "G{:03d}_{}.txt".format(g, ind["id"])
            with open(os.path.join(sprite_dir, fname), "w", encoding="utf-8") as f:
                f.write("# generation={} id={} archetype={} fitness={}\n".format(
                    g, ind["id"], tag, ind["fitness"]))
                f.write(sprite)
                f.write("\n")
            parts.append(sprite)

        header = "=== G{:03d} | {} ({}) vs {} ({}) | best_fitness={} ===".format(
            g, rec["population"][0]["id"], tags[0],
            rec["population"][1]["id"], tags[1], rec["best_fitness"])
        timeline.append(header + "\n" + _side_by_side(parts[0], parts[1]))
        tagline.append("G{:03d}  {} {}".format(g, tags[0], tags[1]))

    with open(os.path.join(anim_dir, "timeline.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(timeline))
        f.write("\n")

    with open(os.path.join(anim_dir, "timeline_tags.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(tagline))
        f.write("\n")

    try:
        _write_gif(records, anim_dir)
    except ImportError:
        pass  # Pillow tidak ada: GIF opsional


def _write_gif(records, anim_dir):
    from PIL import Image, ImageDraw
    frames = []
    for rec in records:
        img = Image.new("RGB", (640, 420), "white")
        d = ImageDraw.Draw(img)
        for k, ind in enumerate(rec["population"]):
            d.text((20 + 320 * k, 10),
                   "G{:03d} {} {}".format(rec["generation"], ind["id"],
                                          archetype_tag(ind["phenotype"])),
                   fill="black")
            d.text((20 + 320 * k, 40),
                   render_sprite(ind["phenotype"]), fill="black")
        frames.append(img)
    frames[0].save(os.path.join(anim_dir, "animation.gif"),
                   save_all=True, append_images=frames[1:],
                   duration=200, loop=0)