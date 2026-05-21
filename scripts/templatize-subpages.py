"""Templatize visible content on contact + demo pages."""
import re
from pathlib import Path


def transform(path: Path, scope: str, hero_subtitle_pattern, hero_subtitle_replace):
    """scope is 'contact' or 'demo'."""
    t = path.read_text(encoding="utf-8")

    # 1. Hero title: <h1 ...>{old}</h1>. Use a regex that matches inside <h1>.
    hero_old_title = "Nous contacter" if scope == "contact" else "Demander une démo"
    t = re.sub(
        r"(<h1[^>]*>)" + re.escape(hero_old_title) + r"(</h1>)",
        rf"\1{{{{ {scope}.hero.title }}}}\2",
        t,
    )

    # 2. Hero subtitle: depends on the page
    t = re.sub(hero_subtitle_pattern, hero_subtitle_replace, t)

    # 3. Form labels — anchor on `<p ...>X</p>` followed by the form-input
    #    container so we don't catch unrelated occurrences.
    for old, varname in [
        ("Nom Prénom",          "nameLabel"),
        ("Adresse mail",        "emailLabel"),
        ("Numéro de téléphone", "phoneLabel"),
        ("Message",             "messageLabel"),
    ]:
        # Each label is a unique <p>X</p> structure preceding a framer-form-text-input wrapper
        t = re.sub(
            r'(<p class="framer-text[^"]*"[^>]*>)' + re.escape(old) + r'(</p>\s*</div>\s*<div class="framer-form-text-input)',
            rf'\1{{{{ {scope}.form.{varname} }}}}\2',
            t,
        )

    # 4. Consent prefix
    t = re.sub(
        r'(<p class="framer-text[^"]*"[^>]*>)J\'accepte les(</p>)',
        rf"\1{{{{ {scope}.form.consentPrefix }}}}\2",
        t,
    )
    # 5. Consent link label + URL — both on the <a> wrapping "conditions d'utilisation"
    t = re.sub(
        r'(<a class="framer-text[^"]*" )(?:href="[^"]*")(\s+target="_blank">)conditions d\'utilisation(</a>)',
        rf'\1href="{{{{ {scope}.form.consentLinkUrl }}}}"\2{{{{ {scope}.form.consentLinkLabel }}}}\3',
        t,
    )

    # 6. Submit label "Envoyer" (visible + hover clone)
    t = re.sub(
        r'(<p class="framer-text[^"]*"[^>]*>)Envoyer\s*(</p>)',
        rf"\1{{{{ {scope}.form.submitLabel }}}}\2",
        t,
    )

    path.write_text(t, encoding="utf-8")


# Contact: 2-paragraph subtitle collapsed into 1 <p> with <br/><br/>
CONTACT_SUBTITLE_RE = re.compile(
    r'(<p class="framer-text framer-styles-preset-8wefef"[^>]*>)Une question sur CastMate \?</p>'
    r'<p class="framer-text framer-styles-preset-8wefef"[^>]*>Écrivez-nous, nous vous répondrons rapidement\.</p>'
)
CONTACT_SUBTITLE_NEW = r"\1{{ contact.hero.subtitle | safe }}</p>"

# Demo: single <p>, no fragmentation
DEMO_SUBTITLE_RE = re.compile(
    r'(<p class="framer-text framer-styles-preset-8wefef"[^>]*>)Réservez une démonstration avec notre équipe\. Nous vous montrons la plateforme sur un cas concret\.(</p>)'
)
DEMO_SUBTITLE_NEW = r"\1{{ demo.hero.subtitle }}\2"

transform(Path("src/contact/index.njk"), "contact", CONTACT_SUBTITLE_RE, CONTACT_SUBTITLE_NEW)
transform(Path("src/demo/index.njk"), "demo", DEMO_SUBTITLE_RE, DEMO_SUBTITLE_NEW)

# Sanity scan: report remaining literal occurrences
for fn, scope in [("src/contact/index.njk", "contact"), ("src/demo/index.njk", "demo")]:
    t = Path(fn).read_text(encoding="utf-8")
    expected_old = {
        "contact": ["Nous contacter", "Une question sur CastMate", "Écrivez-nous", "Adresse mail", "Numéro de téléphone", "Envoyer", "J'accepte les", "conditions d'utilisation", "Nom Prénom"],
        "demo":    ["Demander une démo", "Réservez une démonstration", "Adresse mail", "Numéro de téléphone", "Envoyer", "J'accepte les", "conditions d'utilisation", "Nom Prénom"],
    }[scope]
    print(f"\n=== {fn} — remaining literal counts ===")
    for s in expected_old:
        n = t.count(s)
        print(f"  '{s}': {n}")
