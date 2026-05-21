"""Wire contact + demo forms to Formspree, templatize their meta + placeholders."""
import re
from pathlib import Path


def transform(path: Path, scope: str):
    """scope is 'contact' or 'demo' — picks the right _data key."""
    t = path.read_text(encoding="utf-8")

    # 1. Templatize <title>
    t = re.sub(
        r"<title>[^<]+</title>",
        f"<title>{{{{ {scope}.meta.title }}}}</title>",
        t,
        count=1,
    )

    # 2. Templatize <meta name="description" content="..."> + og + twitter
    t = re.sub(
        r'(<meta name="description" content=")[^"]*(")',
        rf"\1{{{{ {scope}.meta.description }}}}\2",
        t,
    )
    t = re.sub(
        r'(<meta property="og:title" content=")[^"]*(")',
        rf"\1{{{{ {scope}.meta.title }}}}\2",
        t,
    )
    t = re.sub(
        r'(<meta property="og:description" content=")[^"]*(")',
        rf"\1{{{{ {scope}.meta.description }}}}\2",
        t,
    )
    t = re.sub(
        r'(<meta name="twitter:title" content=")[^"]*(")',
        rf"\1{{{{ {scope}.meta.title }}}}\2",
        t,
    )
    t = re.sub(
        r'(<meta name="twitter:description" content=")[^"]*(")',
        rf"\1{{{{ {scope}.meta.description }}}}\2",
        t,
    )

    # 3. Form opening — add action + method, keep Framer classes
    t = re.sub(
        r"<form ",
        f'<form action="{{{{ {scope}.form.endpoint }}}}" method="POST" ',
        t,
        count=1,
    )

    # 4. Rename visible field names + templatize placeholders
    # Name field
    t = t.replace(
        'name="Name" placeholder="Nom Prénom"',
        f'name="name" placeholder="{{{{ {scope}.form.namePlaceholder }}}}" required',
    )
    # Email field (originally named "Enter")
    t = t.replace(
        'name="Enter" placeholder="Entrez votre mail"',
        f'name="email" placeholder="{{{{ {scope}.form.emailPlaceholder }}}}" required',
    )
    # Phone field (name has space "Phone number")
    t = t.replace(
        'name="Phone number" placeholder="Entrez votre téléphone"',
        f'name="phone" placeholder="{{{{ {scope}.form.phonePlaceholder }}}}"',
    )
    # Consent checkbox
    t = re.sub(
        r'name="J\'accepte les conditions d\'utilisation"',
        'name="consent" value="yes" required',
        t,
    )
    # Message textarea
    t = t.replace(
        'name="Message" placeholder="Ecrivez votre message ici"',
        f'name="message" placeholder="{{{{ {scope}.form.messagePlaceholder }}}}" required',
    )

    path.write_text(t, encoding="utf-8")
    return path


transform(Path("src/contact/index.njk"), "contact")
transform(Path("src/demo/index.njk"), "demo")
print("Forms wired + meta templatized for contact + demo.")
