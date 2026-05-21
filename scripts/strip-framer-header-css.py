"""Strip dead Framer CSS rules tied to the OLD header (now removed).
Targets rules whose every comma-separated selector starts with one of:
  - .framer-mbHhH              (nav root)
  - .framer-zexGJ .framer-7lsjpz-container  (fixed wrapper)
  - .framer-vmxz5 / .framer-lq0369 / .framer-hec128 / .framer-ceqaw (menu icon)

If a rule mixes header selectors with non-header ones, it's left alone.
Run from project root."""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = [
    "src/index.njk",
    "src/contact/index.njk",
    "src/demo/index.njk",
    "src/legal/conditions-utilisation/index.njk",
    "src/legal/engagements/index.njk",
    "src/legal/mentions-legales/index.njk",
    "src/legal/protection-donnees/index.njk",
]

HEADER_PREFIXES = (
    ".framer-mbHhH",
    ".framer-zexGJ .framer-7lsjpz-container",
    ".framer-vmxz5",
    ".framer-lq0369",
    ".framer-hec128",
    ".framer-ceqaw",
)


def selector_is_header_only(selector: str) -> bool:
    s = selector.strip()
    return any(s.startswith(prefix) for prefix in HEADER_PREFIXES)


def find_balanced_block(text: str, start: int) -> int:
    """Return index AFTER matching '}' for a CSS block starting at '{' index `start`."""
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def strip_dead_rules(css: str) -> tuple[str, int]:
    """Scan `css` and remove rules whose every selector is header-only."""
    out = []
    i = 0
    removed = 0
    while i < len(css):
        # Skip @media / @supports / @keyframes blocks by treating them as units
        # — but we don't recurse into them (they may legitimately contain
        # framer-mbHhH rules; we leave those alone for safety).
        if css[i] == "@":
            # Find brace start of this at-rule
            brace = css.find("{", i)
            if brace < 0:
                out.append(css[i:])
                break
            end = find_balanced_block(css, brace)
            if end < 0:
                out.append(css[i:])
                break
            out.append(css[i:end])
            i = end
            continue
        # Find the next '{' which marks the end of a selector list
        brace = css.find("{", i)
        if brace < 0:
            out.append(css[i:])
            break
        end = find_balanced_block(css, brace)
        if end < 0:
            out.append(css[i:])
            break
        selectors = css[i:brace]
        # Split selectors by top-level commas (no commas inside parens here in
        # minified Framer CSS practice — selectors are flat lists).
        parts = [p.strip() for p in selectors.split(",") if p.strip()]
        if parts and all(selector_is_header_only(p) for p in parts):
            removed += 1
        else:
            out.append(css[i:end])
        i = end
    return "".join(out), removed


def process(path: Path) -> dict:
    src = path.read_text(encoding="utf-8")
    # Operate on the giant minified Framer CSS blob first (a single line in
    # the <head>). We don't want to scan our own well-formatted style blocks
    # — but in practice, the same logic applies safely (well-formatted rules
    # like `nav.framer-mbHhH` don't exist anymore in the source).
    out, removed = strip_dead_rules(src)
    if out != src:
        path.write_text(out, encoding="utf-8")
    return {"removed_rules": removed, "delta": len(out) - len(src)}


for rel in PAGES:
    p = ROOT / rel
    r = process(p)
    print(f"[OK] {rel}  removed_rules={r['removed_rules']}  delta={r['delta']:+d} B")
