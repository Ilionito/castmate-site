"""Find every `<div class="ssr-variant ...">` whose content contains either
the {% include "faq.njk" %} placeholder OR a residual Framer FAQ section
(class `framer-1y4a2ra`), remove them all, and insert ONE standalone
`{% include "faq.njk" %}` where the first one was.

Works for any SSR breakpoint hash combination (home uses
hidden-oi1h3g/hidden-1wco97h, subpages use hidden-190d003/hidden-5vamp1).

Run from project root:
    python scripts/fix-faq-ssr.py
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
INCLUDE_LINE = '{% include "faq.njk" %}'
FAQ_SECTION_SIG = "framer-1y4a2ra"


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


def fix(path: Path) -> dict:
    src = path.read_text(encoding="utf-8")
    # Collect spans (start, end) of every ssr-variant <div> whose CONTENT
    # contains either the include placeholder or the FAQ section signature.
    spans = []
    for m in re.finditer(r'<div\s+class="ssr-variant[^"]*"\s*>', src):
        start = m.start()
        end = find_matching_div_end(src, start)
        if end < 0:
            continue
        body = src[start:end]
        if INCLUDE_LINE in body or FAQ_SECTION_SIG in body:
            spans.append((start, end))
    if not spans:
        return {"path": str(path.relative_to(ROOT)), "no_matching_wrapper": True}
    # Merge overlapping/nested spans (defensive — Framer SSR variants are
    # siblings, but better safe).
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    # Replace from start of first wrapper to end of last wrapper with one
    # standalone include. Anything BETWEEN wrappers (whitespace/comments)
    # is dropped.
    first_start = merged[0][0]
    last_end = merged[-1][1]
    new_src = src[:first_start] + INCLUDE_LINE + src[last_end:]
    path.write_text(new_src, encoding="utf-8")
    return {
        "path": str(path.relative_to(ROOT)),
        "wrappers_collapsed": len(merged),
        "removed_bytes": last_end - first_start,
        "delta": len(new_src) - len(src),
    }


for rel in PAGES:
    p = ROOT / rel
    r = fix(p)
    ok = "delta" in r
    print(f"[{'OK' if ok else 'FAIL'}] {rel}  {r}")
