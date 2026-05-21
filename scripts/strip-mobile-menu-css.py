"""Strip the residual `.cm-mobile-menu` CSS block left in subpages.
The block starts with the `/* Mobile menu */` comment (subpages) or
`/* --- Mobile menu drawer (vanilla, no Framer runtime) --- */` (home).
Ends at the closing brace of `.cm-mobile-menu .cm-mobile-menu__cta { … }`."""
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

START_MARKERS = [
    "/* --- Mobile menu drawer (vanilla, no Framer runtime) --- */",
    "/* Mobile menu */",
]
END_PATTERN = re.compile(r"\.cm-mobile-menu \.cm-mobile-menu__cta\s*\{[^}]*\}", re.DOTALL)


def strip(html: str) -> tuple[str, bool]:
    for marker in START_MARKERS:
        i = html.find(marker)
        if i >= 0:
            m = END_PATTERN.search(html[i:])
            if m:
                return html[:i] + html[i + m.end():], True
    return html, False


for rel in PAGES:
    p = ROOT / rel
    src = p.read_text(encoding="utf-8")
    out, did = strip(src)
    if did:
        p.write_text(out, encoding="utf-8")
        print(f"[OK] {rel}  delta={len(out) - len(src)} B")
    else:
        print(f"[SKIP] {rel}")
