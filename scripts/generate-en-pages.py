"""Génère les versions anglaises des 7 pages dans src/en/ à partir des
pages FR. Chaque page EN reçoit :
  - un prélude {% set xxx = en.xxx %} qui override les variables globales
    (nav, hero, steps, features, ..., footer, meta, contact, demo)
  - une réécriture des liens internes (./contact → /en/contact, etc.)
  - <html lang="en"> pour SEO + accessibilité

Run from project root:
    python scripts/generate-en-pages.py
"""
from __future__ import annotations
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# Mapping FR -> EN. La racine src/index.njk devient src/en/index.njk.
PAGES = {
    "index.njk":                         "en/index.njk",
    "contact/index.njk":                 "en/contact/index.njk",
    "demo/index.njk":                    "en/demo/index.njk",
    "legal/conditions-utilisation/index.njk": "en/legal/conditions-utilisation/index.njk",
    "legal/engagements/index.njk":            "en/legal/engagements/index.njk",
    "legal/mentions-legales/index.njk":       "en/legal/mentions-legales/index.njk",
    "legal/protection-donnees/index.njk":     "en/legal/protection-donnees/index.njk",
}

# Préfixe à insérer juste après <body> (ou en début de page pour l'override
# des variables globales).
PRELUDE = """
{% set lang = "en" %}
{% set nav = en.nav %}
{% set hero = en.hero %}
{% set steps = en.steps %}
{% set features = en.features %}
{% set security = en.security %}
{% set clarity = en.clarity %}
{% set teamCta = en.teamCta %}
{% set testimonials = en.testimonials %}
{% set faq = en.faq %}
{% set footer = en.footer %}
{% set meta = en.meta %}
{% set contact = en.contact %}
{% set demo = en.demo %}
"""


def rewrite_internal_links(html: str) -> str:
    """Réécrit les href Framer relatifs/absolus vers le préfixe /en/."""
    # href="./"  -> href="/en/"
    html = re.sub(r'href="\./"', 'href="/en/"', html)
    # href="./contact" -> href="/en/contact"
    html = re.sub(r'href="\./contact"', 'href="/en/contact"', html)
    # href="./demo" -> href="/en/demo"
    html = re.sub(r'href="\./demo"', 'href="/en/demo"', html)
    # href="/contact" -> href="/en/contact"  (sauf déjà /en/)
    html = re.sub(r'href="/contact(?!.*/en/)"', 'href="/en/contact"', html)
    html = re.sub(r'href="/demo(?!.*/en/)"', 'href="/en/demo"', html)
    # href="/legal/..." -> href="/en/legal/..."
    html = re.sub(r'href="/legal/', 'href="/en/legal/', html)
    return html


def fix_html_lang(html: str) -> str:
    """Force <html lang="en">."""
    return re.sub(r'<html\b[^>]*>', '<html lang="en">', html, count=1)


def add_prelude(html: str) -> str:
    """Insère le prélude {% set %} juste après <body> (la première
    occurrence). Si déjà présent, no-op."""
    if '{% set lang = "en" %}' in html:
        return html
    return re.sub(r'(<body[^>]*>)', r'\1' + PRELUDE, html, count=1)


def process_page(src_rel: str, dst_rel: str) -> dict:
    src = SRC / src_rel
    dst = SRC / dst_rel
    if not src.exists():
        return {"src": src_rel, "missing": True}
    dst.parent.mkdir(parents=True, exist_ok=True)
    content = src.read_text(encoding="utf-8")
    new_content = fix_html_lang(content)
    new_content = rewrite_internal_links(new_content)
    new_content = add_prelude(new_content)
    dst.write_text(new_content, encoding="utf-8")
    return {"src": src_rel, "dst": dst_rel, "delta": len(new_content) - len(content)}


for src_rel, dst_rel in PAGES.items():
    r = process_page(src_rel, dst_rel)
    flag = "OK" if "delta" in r else "FAIL"
    print(f"[{flag}] {src_rel} -> {dst_rel}  {r}")
