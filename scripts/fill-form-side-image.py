"""Remplace le contenu interne du <div data-framer-name="Image Wrap"> (slot
prévu par Framer à côté de chaque formulaire contact/demo, actuellement
vide — juste un canvas WebGL placeholder) par une vraie <img>.

Cible : src/contact/index.njk et src/demo/index.njk.
Garde le wrapper externe intact (classes hidden-*, will-change/opacity
pour l'animation d'entrée via data-castmate-reveal).

Run from project root:
    python scripts/fill-form-side-image.py
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["src/contact/index.njk", "src/demo/index.njk"]
IMG_SRC = "/assets/uploads/castmate-form-side.png"
IMG_ALT = "CastMate"


def find_matching_div_end(html: str, start: int) -> int:
    depth = 0
    pat = re.compile(r"<(/?)div\b[^>]*>", re.IGNORECASE)
    i = start
    while i < len(html):
        m = pat.search(html, i)
        if not m:
            return -1
        if m.group(1) == "":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return m.end()
        i = m.end()
    return -1


def replace_in_page(path: Path) -> dict:
    src = path.read_text(encoding="utf-8")
    pat = re.compile(r'<div [^>]*data-framer-name="Image Wrap"[^>]*>')
    new_parts = []
    last_end = 0
    count = 0
    for m in pat.finditer(src):
        start = m.start()
        end = find_matching_div_end(src, start)
        if end < 0:
            continue
        open_tag = m.group(0)
        new_parts.append(src[last_end:start])
        new_parts.append(open_tag)
        new_parts.append(
            f'<img src="{IMG_SRC}" alt="{IMG_ALT}" '
            'style="width:100%;height:100%;object-fit:cover;display:block;border-radius:0">'
        )
        new_parts.append("</div>")
        last_end = end
        count += 1
    if count == 0:
        return {"path": str(path.relative_to(ROOT)), "replaced": 0}
    new_parts.append(src[last_end:])
    new_src = "".join(new_parts)
    path.write_text(new_src, encoding="utf-8")
    return {"path": str(path.relative_to(ROOT)), "replaced": count, "delta": len(new_src) - len(src)}


for rel in PAGES:
    p = ROOT / rel
    r = replace_in_page(p)
    print(f"[{'OK' if r.get('replaced') else 'FAIL'}] {rel}  {r}")
