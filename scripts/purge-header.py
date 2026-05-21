"""Pure deletion pass: strip the OLD Framer header (markup + CSS + JS)
from all 7 .njk pages. Does NOT inject any replacement — that's a
separate step.

Removes:
  Markup:
    - <div class="framer-7lsjpz-container">…</div>  (fixed header wrapper +
      3 SSR nav.framer-mbHhH variants inside the giant body line)
    - <nav class="cm-mobile-menu" …>…</nav>          (mobile drawer)
  CSS in <style> blocks:
    - /* --- Header transparent at top, solid on scroll --- */ block
      (nav.framer-mbHhH + body.cm-scrolled nav.framer-mbHhH)
    - /* --- Mobile menu drawer (vanilla, no Framer runtime) --- */ block
      (home variant)
    - /* Mobile menu */ block (subpage variant)
  CSS in Framer minified blob:
    - rules whose every selector targets .framer-mbHhH* /
      .framer-zexGJ .framer-7lsjpz-container / .framer-vmxz5 /
      .framer-lq0369 / .framer-hec128 / .framer-ceqaw  (~27 rules per page)
  JS:
    - <script>…</script> (no attrs) that contains data-cm-menu-open
      (burger toggle)
    - <script data-castmate-header>…</script>          (scroll-state toggle)

Leaves nav.json untouched.

Run from project root:
    python scripts/purge-header.py
"""
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


def find_matching_div_end(html: str, start: int) -> int:
    depth = 0
    i = start
    pat = re.compile(r"<(/?)div\b[^>]*>", re.IGNORECASE)
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


def strip_framer_header_div(html: str) -> tuple[str, bool]:
    m = re.search(r'<div\s+class="framer-7lsjpz-container"[^>]*>', html)
    if not m:
        return html, False
    end = find_matching_div_end(html, m.start())
    if end < 0:
        return html, False
    return html[: m.start()] + html[end:], True


def strip_cm_mobile_menu(html: str) -> tuple[str, bool]:
    m = re.search(r'<nav\s+class="cm-mobile-menu"[^>]*>.*?</nav>', html, re.DOTALL)
    if not m:
        return html, False
    return html[: m.start()] + html[m.end():], True


def strip_block(html: str, start_marker: str, end_pattern: str) -> tuple[str, bool]:
    i = html.find(start_marker)
    if i < 0:
        return html, False
    m = re.search(end_pattern, html[i:], re.DOTALL)
    if not m:
        return html, False
    return html[:i] + html[i + m.end():], True


def strip_header_css_v1(html: str) -> tuple[str, bool]:
    """Strip `/* --- Header transparent at top, solid on scroll --- */ … }`."""
    return strip_block(
        html,
        "/* --- Header transparent at top, solid on scroll --- */",
        r"body\.cm-scrolled\s+nav\.framer-mbHhH\s*\{[^}]*\}",
    )


def strip_drawer_css_home(html: str) -> tuple[str, bool]:
    """Strip `/* --- Mobile menu drawer (vanilla, no Framer runtime) --- */`."""
    return strip_block(
        html,
        "/* --- Mobile menu drawer (vanilla, no Framer runtime) --- */",
        r"\.cm-mobile-menu \.cm-mobile-menu__cta\s*\{[^}]*\}",
    )


def strip_drawer_css_subpage(html: str) -> tuple[str, bool]:
    """Strip `/* Mobile menu */` block (subpage variant)."""
    return strip_block(
        html,
        "/* Mobile menu */",
        r"\.cm-mobile-menu \.cm-mobile-menu__cta\s*\{[^}]*\}",
    )


def strip_burger_toggle_script(html: str) -> tuple[str, bool]:
    """Strip the unnamed <script>…</script> that contains data-cm-menu-open."""
    pat = re.compile(r"<script>\s*\(function\s*\(\)\s*\{[^<]*?data-cm-menu-open.*?</script>", re.DOTALL)
    m = pat.search(html)
    if not m:
        return html, False
    return html[: m.start()] + html[m.end():], True


def strip_castmate_header_script(html: str) -> tuple[str, bool]:
    pat = re.compile(r"<script\s+data-castmate-header>.*?</script>", re.DOTALL)
    m = pat.search(html)
    if not m:
        return html, False
    return html[: m.start()] + html[m.end():], True


def selector_is_header_only(selector: str) -> bool:
    s = selector.strip()
    return any(s.startswith(p) for p in HEADER_PREFIXES)


def find_balanced_block(text: str, start: int) -> int:
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


def strip_framer_dead_rules(css: str) -> tuple[str, int]:
    out, i, removed = [], 0, 0
    while i < len(css):
        if css[i] == "@":
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
        brace = css.find("{", i)
        if brace < 0:
            out.append(css[i:])
            break
        end = find_balanced_block(css, brace)
        if end < 0:
            out.append(css[i:])
            break
        selectors = css[i:brace]
        parts = [p.strip() for p in selectors.split(",") if p.strip()]
        if parts and all(selector_is_header_only(p) for p in parts):
            removed += 1
        else:
            out.append(css[i:end])
        i = end
    return "".join(out), removed


def process(path: Path) -> dict:
    src = path.read_text(encoding="utf-8")
    html = src
    report = {"path": str(path.relative_to(ROOT))}
    steps = [
        ("framer_header_div", strip_framer_header_div),
        ("cm_mobile_menu", strip_cm_mobile_menu),
        ("header_css", strip_header_css_v1),
        ("drawer_css_home", strip_drawer_css_home),
        ("drawer_css_subpage", strip_drawer_css_subpage),
        ("burger_toggle_script", strip_burger_toggle_script),
        ("castmate_header_script", strip_castmate_header_script),
    ]
    for name, fn in steps:
        html, did = fn(html)
        report[name] = did
    html, removed = strip_framer_dead_rules(html)
    report["framer_dead_rules_removed"] = removed
    if html != src:
        path.write_text(html, encoding="utf-8")
        report["delta"] = len(html) - len(src)
    else:
        report["delta"] = 0
    return report


def main():
    for rel in PAGES:
        p = ROOT / rel
        if not p.exists():
            print(f"[SKIP] {rel} (not found)")
            continue
        r = process(p)
        bool_steps = {k: v for k, v in r.items() if isinstance(v, bool)}
        flag = "OK" if r["delta"] != 0 else "NOOP"
        print(f"[{flag}] {rel}  delta={r['delta']:+d} B  rules_removed={r['framer_dead_rules_removed']}  steps={bool_steps}")


if __name__ == "__main__":
    main()
