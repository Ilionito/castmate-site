"""Templatize nav, footer (and FAQ where present) across the 6 subpages.

Strategy: per-page text substitution. We never share markup between pages
because Framer-generated class names differ from page to page — collapsing
to a single partial would silently break the CSS on some pages. Instead,
each page keeps its own markup, and we only replace text + href values
with {{ nav.* }} / {{ footer.* }} / {{ faq.* }}.

Ambiguous strings ("Demander une démo", "Conditions d'utilisation"…) appear
in multiple sections. We resolve them by scoping substitutions to the
<nav>...</nav> and <footer>...</footer> spans on each page.
"""
import re
from pathlib import Path


SUBPAGES = [
    Path("src/contact/index.njk"),
    Path("src/demo/index.njk"),
    Path("src/legal/conditions-utilisation/index.njk"),
    Path("src/legal/engagements/index.njk"),
    Path("src/legal/mentions-legales/index.njk"),
    Path("src/legal/protection-donnees/index.njk"),
]


def find_all_spans(text: str, open_tag: str, close_tag: str):
    """All [start, end_inclusive) ranges from each open_tag through the matching close_tag."""
    spans = []
    i = 0
    while True:
        s = text.find(open_tag, i)
        if s == -1:
            break
        e = text.find(close_tag, s)
        if e == -1:
            break
        e += len(close_tag)
        spans.append((s, e))
        i = e
    return spans


def replace_in_spans(text: str, spans, pairs):
    """Apply pairs (list of (old, new) substrings) inside each span. Walk
    spans last-to-first so offsets stay valid."""
    counts = {old: 0 for old, _ in pairs}
    for s, e in reversed(spans):
        slice_ = text[s:e]
        for old, new in pairs:
            if old in slice_:
                counts[old] += slice_.count(old)
                slice_ = slice_.replace(old, new)
        text = text[:s] + slice_ + text[e:]
    return text, counts


# ---- nav substitutions (scoped to <nav>...</nav>) ----
# nav.links[0]: Accueil → /
# nav.links[1]: Contact → /contact
# nav.ctaLabel: Demander une démo
# nav.ctaUrl: /demo
NAV_PAIRS = [
    # Order matters: do label replacements first, URL replacements after.
    ("Accueil", "{{ nav.links[0].label }}"),
    (">Contact<", ">{{ nav.links[1].label }}<"),
    ("Demander une démo", "{{ nav.ctaLabel }}"),
    # URLs — relative form Framer used inside nav of subpages.
    # Each subpage's nav uses ./demo and ./ relative to the page directory.
    # Both work after templating because the absolute paths in JSON
    # (/, /demo, /contact) will be served verbatim.
    ('"./demo"', '"{{ nav.ctaUrl }}"'),
    ('"./"', '"{{ nav.links[0].url }}"'),
    ('"./contact"', '"{{ nav.links[1].url }}"'),
]

# ---- footer substitutions (scoped to <footer>...</footer>) ----
FOOTER_PAIRS = [
    # Tagline + CTA
    ("La plateforme tout-en-un pour vos castings.", "{{ footer.tagline }}"),
    ("Demander une démo", "{{ footer.ctaLabel }}"),
    # Legal links — labels (avoid replacing the page's own H1 by scoping to footer)
    ("Mentions légales",                       "{{ footer.legalLinks[0].label }}"),
    ("Nos engagements",                        "{{ footer.legalLinks[1].label }}"),
    ("Politique de protection des données",    "{{ footer.legalLinks[2].label }}"),
    ("Conditions d'utilisation",               "{{ footer.legalLinks[3].label }}"),
    # Legal links — URLs (Framer used relative forms; replace with templated absolutes)
    ('"./legal/mentions-legales"',     '"{{ footer.legalLinks[0].url }}"'),
    ('"./legal/engagements"',          '"{{ footer.legalLinks[1].url }}"'),
    ('"./legal/protection-donnees"',   '"{{ footer.legalLinks[2].url }}"'),
    ('"./legal/conditions-utilisation"', '"{{ footer.legalLinks[3].url }}"'),
    # Also the relative form used inside legal pages
    ('"./mentions-legales"',     '"{{ footer.legalLinks[0].url }}"'),
    ('"./engagements"',          '"{{ footer.legalLinks[1].url }}"'),
    ('"./protection-donnees"',   '"{{ footer.legalLinks[2].url }}"'),
    ('"./conditions-utilisation"', '"{{ footer.legalLinks[3].url }}"'),
    # And the up-level form
    ('"../mentions-legales"',     '"{{ footer.legalLinks[0].url }}"'),
    ('"../engagements"',          '"{{ footer.legalLinks[1].url }}"'),
    ('"../protection-donnees"',   '"{{ footer.legalLinks[2].url }}"'),
    ('"../conditions-utilisation"', '"{{ footer.legalLinks[3].url }}"'),
    # CTA URL — relative
    ('"./demo"', '"{{ footer.ctaUrl }}"'),
    ('"../demo"', '"{{ footer.ctaUrl }}"'),
    # Other footer fields
    ("CastMate - BV TECH SAS", "{{ footer.companyName }}"),
    ("contact@castmate.fr", "{{ footer.email }}"),
    ("contact@bvtech.fr", "{{ footer.altEmail }}"),
    # rcs MUST be replaced before siren, because rcs contains siren as a substring.
    ("Versailles B 901 938 787", "{{ footer.rcs }}"),
    ("901 938 787", "{{ footer.siren }}"),
    # Copyright — has a <br> mid-string in some variants. Handle both.
    ('© 2025 {{ footer.companyName }}.<br class="framer-text">Tous droits réservés.',
     "{{ footer.copyright }}"),
    ('© 2025 {{ footer.companyName }}. Tous droits réservés.',
     "{{ footer.copyright }}"),
    # LinkedIn URL — usually inside a footer <a href="https://linkedin…"
    ('"https://linkedin.com"', '"{{ footer.linkedinUrl }}"'),
]


# ---- FAQ accordion replacement ----
# Same replacement we did on the home: drop the framer-yolmln-container's
# Framer accordion mount + replace with our <details> loop. Only contact +
# demo have a FAQ section.
FAQ_ACCORDION = (
    '<div class="castmate-faq">{% for item in faq.items %}'
    '<details class="castmate-faq__item">'
    '<summary class="castmate-faq__summary">'
    '<span class="castmate-faq__question">{{ item.question }}</span>'
    '<span class="castmate-faq__icon" aria-hidden="true"></span>'
    "</summary>"
    "{% if item.answer %}"
    '<div class="castmate-faq__answer">{{ item.answer }}</div>'
    "{% endif %}"
    "</details>{% endfor %}</div>"
)


def find_close_div(text: str, start: int) -> int:
    depth = 1
    i = start
    while depth > 0 and i < len(text):
        no = text.find("<div", i)
        nc = text.find("</div>", i)
        if nc == -1:
            return -1
        if no != -1 and no < nc:
            depth += 1
            i = no + 4
        else:
            depth -= 1
            i = nc + 6
    return i


def replace_faq_mounts(text: str):
    """Same logic as the home: replace each <div class="framer-yolmln-container">…</div>
    with the standalone <details> accordion."""
    mounts = []
    for m in re.finditer(r'<div class="framer-yolmln-container">', text):
        i = m.start()
        end = find_close_div(text, m.end())
        mounts.append((i, end))
    for s, e in reversed(mounts):
        text = text[:s] + FAQ_ACCORDION + text[e:]
    return text, len(mounts)


# ---- Patch the FAQ section's adjacent labels/CTA too ----
# The FAQ section's title/intro/CTA in the section header are still hardcoded
# on subpages. Same substitutions as the home, applied across the whole file
# (these strings are unique enough not to collide elsewhere).
FAQ_SECTION_PAIRS = [
    ("Des questions ?", "{{ faq.title }}"),
    ("Tout ce qu’il faut savoir sur CastMate, son fonctionnement et la gestion de vos castings.",
     "{{ faq.intro }}"),
    # The FAQ section also has a "Nous contacter" CTA in subpages — but
    # "Nous contacter" is the contact page's hero.title too. We anchor it
    # via the FAQ CTA's href: a[href="…contact"] within the FAQ section.
    # For simplicity we handle this only inside the FAQ section's narrow
    # scope above (the framer-yolmln-container area), which we have
    # already nuked. So no extra pass needed.
]


def process_page(path: Path):
    text = path.read_text(encoding="utf-8")
    report = {"path": str(path), "nav": {}, "footer": {}, "faq_mounts": 0}

    # --- nav: scope to each <nav>...</nav> span -----------------------
    nav_spans = find_all_spans(text, "<nav", "</nav>")
    text, nav_counts = replace_in_spans(text, nav_spans, NAV_PAIRS)
    report["nav"] = nav_counts
    report["nav_spans"] = len(nav_spans)

    # --- footer: scope to each <footer>...</footer> span --------------
    footer_spans = find_all_spans(text, "<footer", "</footer>")
    text, footer_counts = replace_in_spans(text, footer_spans, FOOTER_PAIRS)
    report["footer"] = footer_counts
    report["footer_spans"] = len(footer_spans)

    # --- FAQ section adjacent strings (title, intro) — file-wide ------
    for old, new in FAQ_SECTION_PAIRS:
        text = text.replace(old, new)

    # --- FAQ mount replacement ----------------------------------------
    text, n_mounts = replace_faq_mounts(text)
    report["faq_mounts"] = n_mounts

    path.write_text(text, encoding="utf-8")
    return report


for p in SUBPAGES:
    r = process_page(p)
    nav_total = sum(v for v in r["nav"].values())
    footer_total = sum(v for v in r["footer"].values())
    print(f"{p}")
    print(f"  nav spans={r['nav_spans']} substitutions={nav_total}")
    print(f"  footer spans={r['footer_spans']} substitutions={footer_total}")
    print(f"  FAQ mounts replaced: {r['faq_mounts']}")
