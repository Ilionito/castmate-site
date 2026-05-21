"""
One-shot surgery on the 7 .njk pages to strip the old Framer-based header
(.framer-7lsjpz-container + framer-mbHhH navs + cm-mobile-menu drawer + my
custom CSS/JS for them) and inject `{% include "site-header.njk" %}` instead.

Run from project root:
    python scripts/refactor-header.py
"""
from __future__ import annotations
import re
from pathlib import Path

PAGES = {
    "src/index.njk": {"forceSolid": False},
    "src/contact/index.njk": {"forceSolid": True},
    "src/demo/index.njk": {"forceSolid": True},
    "src/legal/conditions-utilisation/index.njk": {"forceSolid": True},
    "src/legal/engagements/index.njk": {"forceSolid": True},
    "src/legal/mentions-legales/index.njk": {"forceSolid": True},
    "src/legal/protection-donnees/index.njk": {"forceSolid": True},
}

ROOT = Path(__file__).resolve().parent.parent


def find_matching_div_end(html: str, start: int) -> int:
    """Given the index of '<div ...>' opening, walk forward tracking <div>
    nesting and return the index AFTER the matching '</div>'."""
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
    """Strip the entire `<div class="framer-7lsjpz-container">…</div>` block."""
    m = re.search(r'<div\s+class="framer-7lsjpz-container"[^>]*>', html)
    if not m:
        return html, False
    end = find_matching_div_end(html, m.start())
    if end < 0:
        return html, False
    return html[: m.start()] + html[end:], True


def strip_cm_mobile_menu(html: str) -> tuple[str, bool]:
    """Strip the `<nav class="cm-mobile-menu" …>…</nav>` block (single nav)."""
    m = re.search(r'<nav\s+class="cm-mobile-menu"[^>]*>.*?</nav>', html, re.DOTALL)
    if not m:
        return html, False
    return html[: m.start()] + html[m.end():], True


def strip_block(html: str, start_marker: str, end_marker_pattern: str) -> tuple[str, bool]:
    """Strip from `start_marker` literal to end of matched regex."""
    i = html.find(start_marker)
    if i < 0:
        return html, False
    m = re.search(end_marker_pattern, html[i:], re.DOTALL)
    if not m:
        return html, False
    return html[:i] + html[i + m.end():], True


def strip_custom_header_css(html: str) -> tuple[str, bool]:
    """Strip my old custom header CSS block.
    Marker start: `/* --- Site header: opaque navy at rest`
    End: closing brace of `.framer-1mehg92-container { … }` rule."""
    return strip_block(
        html,
        "/* --- Site header: opaque navy at rest",
        r"\.framer-1mehg92-container\s*\{[^}]*\}",
    )


def strip_mobile_drawer_css(html: str) -> tuple[str, bool]:
    """Strip the cm-mobile-menu CSS block."""
    return strip_block(
        html,
        "/* --- Mobile menu drawer (vanilla, no Framer runtime) --- */",
        r"\.cm-mobile-menu \.cm-mobile-menu__cta\s*\{[^}]*\}",
    )


def strip_burger_toggle_script(html: str) -> tuple[str, bool]:
    """Strip the inline `<script>` block that toggles the menu icon."""
    # The script is right before `<script data-castmate-header>` and contains
    # `data-cm-menu-open`. Match `<script>` (no attrs) up to its `</script>`
    # — but only if it contains the marker.
    pat = re.compile(r"<script>\s*\(function\s*\(\)\s*\{[^<]*?data-cm-menu-open.*?</script>", re.DOTALL)
    m = pat.search(html)
    if not m:
        return html, False
    return html[: m.start()] + html[m.end():], True


def strip_castmate_header_script(html: str) -> tuple[str, bool]:
    """Strip the `<script data-castmate-header>…</script>` block."""
    pat = re.compile(r"<script\s+data-castmate-header>.*?</script>", re.DOTALL)
    m = pat.search(html)
    if not m:
        return html, False
    return html[: m.start()] + html[m.end():], True


def inject_include(html: str, force_solid: bool) -> tuple[str, bool]:
    """Inject `{% include 'site-header.njk' %}` right after `<body>` (no attrs)
    or at the start of the first body content. We target the literal
    `<body>` tag — Eleventy keeps it intact."""
    marker = "<body>"
    i = html.find(marker)
    if i < 0:
        return html, False
    insertion = "\n"
    if force_solid:
        insertion += "{% set forceSolid = true %}"
    insertion += "{% include \"site-header.njk\" %}\n"
    after = i + len(marker)
    return html[:after] + insertion + html[after:], True


def process_file(path: Path, force_solid: bool) -> dict:
    original = path.read_text(encoding="utf-8")
    html = original
    report = {"path": str(path.relative_to(ROOT))}
    for name, fn in [
        ("framer_header_div", strip_framer_header_div),
        ("cm_mobile_menu", strip_cm_mobile_menu),
        ("custom_header_css", strip_custom_header_css),
        ("mobile_drawer_css", strip_mobile_drawer_css),
        ("burger_toggle_script", strip_burger_toggle_script),
        ("castmate_header_script", strip_castmate_header_script),
    ]:
        html, did = fn(html)
        report[name] = did
    html, did = inject_include(html, force_solid)
    report["inject_include"] = did
    if html != original:
        path.write_text(html, encoding="utf-8")
        report["bytes_before"] = len(original)
        report["bytes_after"] = len(html)
        report["delta"] = len(html) - len(original)
    else:
        report["delta"] = 0
    return report


def main():
    for rel, cfg in PAGES.items():
        p = ROOT / rel
        if not p.exists():
            print("[skip]", rel, "(not found)")
            continue
        r = process_file(p, cfg["forceSolid"])
        ok = all([
            r.get("framer_header_div"),
            r.get("cm_mobile_menu"),
            r.get("custom_header_css"),
            r.get("mobile_drawer_css"),
            r.get("burger_toggle_script"),
            r.get("castmate_header_script"),
            r.get("inject_include"),
        ])
        flag = "OK" if ok else "PARTIAL"
        print(f"[{flag}] {rel}  delta={r['delta']:+d} B  detail={ {k: r[k] for k in r if isinstance(r[k], bool)} }")


if __name__ == "__main__":
    main()
