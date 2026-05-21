"""Replace the entire Framer FAQ <section> (the one with class
framer-1y4a2ra) with `{% include "faq.njk" %}` in each page that has it.

Run from project root:
    python scripts/replace-faq.py
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = [
    "src/index.njk",
    "src/contact/index.njk",
    "src/demo/index.njk",
]


def find_matching_section_end(html: str, start: int) -> int:
    """Given an index pointing at '<section ...>', walk forward and return
    the index AFTER the matching '</section>'."""
    depth = 0
    pat = re.compile(r"<(/?)section\b[^>]*>", re.IGNORECASE)
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


def replace_faq(path: Path) -> dict:
    src = path.read_text(encoding="utf-8")
    # Locate the FAQ section by its signature class `framer-1y4a2ra`.
    sig = re.search(r'<section[^>]*framer-1y4a2ra[^>]*>', src)
    if not sig:
        return {"path": str(path.relative_to(ROOT)), "found": False}
    end = find_matching_section_end(src, sig.start())
    if end < 0:
        return {"path": str(path.relative_to(ROOT)), "found": True, "matched_end": False}
    new_src = src[: sig.start()] + '{% include "faq.njk" %}' + src[end:]
    path.write_text(new_src, encoding="utf-8")
    return {
        "path": str(path.relative_to(ROOT)),
        "found": True,
        "matched_end": True,
        "removed_bytes": end - sig.start(),
        "delta": len(new_src) - len(src),
    }


for rel in PAGES:
    p = ROOT / rel
    r = replace_faq(p)
    print(f"[{('OK' if r.get('matched_end') else 'FAIL')}] {rel}  detail={r}")
