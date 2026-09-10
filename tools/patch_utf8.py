import re
from pathlib import Path

ROOT = Path(r"E:\bloon_mbg2")

def patch(path):
    text = path.read_text(encoding="utf-8")
    orig = text
    # Tambahkan encoding="utf-8" pada open(..., "w")
    text = re.sub(r'open\((.*?),\s*"w"\)', r'open(\1, "w", encoding="utf-8")', text)
    # Tambahkan encoding="utf-8" pada open(..., "w", newline="")
    text = re.sub(r'open\((.*?),\s*"w",\s*newline=""\)', r'open(\1, "w", encoding="utf-8", newline="")', text)
    
    if text != orig:
        path.write_text(text, encoding="utf-8")
        print("patched:", path)
    else:
        print("no changes:", path)

patch(ROOT / "new_bloon" / "visualization" / "animation.py")
patch(ROOT / "cli.py")