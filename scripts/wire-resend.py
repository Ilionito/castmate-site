"""Patch les 2 forms (contact + demo) :
- retire action="..." + method="POST" du <form>
- ajoute classes "js-resend-form" et data-form="contact"|"demo"
- retire les hidden _next (résidu Formspree)
- retire tous les hidden _hp_* (anciens honeypots Formspree)
- ajoute un seul hidden honeypot _gotcha juste après le <form>
- normalise la textarea "Message" (capital M) → "message" sur demo
- inclut {% include "cm-popup.njk" %} juste avant </body>
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "src/contact/index.njk": {"slug": "contact", "form_class": "framer-1gy4yt8"},
    "src/demo/index.njk": {"slug": "demo", "form_class": "framer-1dcuvpj"},
}

GOTCHA = (
    '<input type="text" name="_gotcha" tabindex="-1" autocomplete="off" '
    'aria-hidden="true" style="position:absolute;left:-9999px">'
)


def patch(path: Path, slug: str, form_class: str) -> dict:
    src = path.read_text(encoding="utf-8")
    report = {"path": str(path.relative_to(ROOT)), "slug": slug}

    # 1. Replace <form ...> opening tag
    new_open = (
        f'<form class="{form_class} js-resend-form" '
        f'data-form="{slug}" data-border="true">'
    )
    form_open_pat = re.compile(
        r'<form\s+action="\{\{\s*' + slug + r'\.form\.endpoint\s*\}\}"\s+method="POST"\s+class="'
        + re.escape(form_class)
        + r'"\s+data-border="true">'
    )
    new_src, n = form_open_pat.subn(new_open + GOTCHA, src)
    report["form_open_patched"] = n

    # 2. Remove <input ... name="_next" ...>
    new_src, n = re.subn(r'<input[^>]*\bname="_next"[^>]*>', '', new_src)
    report["next_removed"] = n

    # 3. Remove all <input ... name="_hp_*" ...>
    new_src, n = re.subn(r'<input[^>]*\bname="_hp_[^"]*"[^>]*>', '', new_src)
    report["hp_removed"] = n

    # 4. Normalize <textarea ... name="Message" ...> to name="message" (demo only,
    #    but safe to run on both).
    new_src, n = re.subn(r'(<textarea[^>]*\bname=")Message(")', r'\1message\2', new_src)
    report["textarea_renamed"] = n

    # 5. Add {% include "cm-popup.njk" %} just before </body>.
    if '{% include "cm-popup.njk" %}' not in new_src:
        new_src, n = re.subn(r'</body>', '{% include "cm-popup.njk" %}</body>', new_src, count=1)
        report["popup_included"] = n
    else:
        report["popup_included"] = 0  # already there

    path.write_text(new_src, encoding="utf-8")
    report["delta"] = len(new_src) - len(src)
    return report


for rel, cfg in CONFIG.items():
    r = patch(ROOT / rel, cfg["slug"], cfg["form_class"])
    print(f"[OK] {rel}  {r}")
