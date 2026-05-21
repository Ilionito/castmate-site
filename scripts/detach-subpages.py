"""Strip Framer runtime + inject reveal/menu drawer/styles on subpages."""
import re
from pathlib import Path

REVEAL_SCRIPT = """<script data-castmate-reveal>
(function () {
  function init() {
    var els = document.querySelectorAll('[style*="will-change:transform"]');
    var targets = [];
    for (var i = 0; i < els.length; i++) {
      var s = els[i].style;
      if (s.opacity !== "" && parseFloat(s.opacity) < 1) {
        targets.push(els[i]);
        s.transition = "opacity 0.6s cubic-bezier(0.22, 1, 0.36, 1), transform 0.6s cubic-bezier(0.22, 1, 0.36, 1)";
      }
    }
    if (!targets.length) return;
    if (typeof IntersectionObserver === "undefined") {
      targets.forEach(function (el) { el.style.opacity = "1"; el.style.transform = "none"; });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var el = entry.target;
          el.style.opacity = "1"; el.style.transform = "none"; el.style.filter = "none"; el.style.webkitFilter = "none";
          io.unobserve(el);
        }
      });
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.05 });
    targets.forEach(function (el) { io.observe(el); });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
</script>"""

DRAWER = """<nav class="cm-mobile-menu" data-cm-mobile-menu>{% for link in nav.links %}<a href="{{ link.url }}">{{ link.label }}</a>{% endfor %}<a class="cm-mobile-menu__cta" href="{{ nav.ctaUrl }}">{{ nav.ctaLabel }}</a></nav>"""

TOGGLE_JS = """<script>
(function () {
  function onReady(fn) { if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn); else fn(); }
  onReady(function () {
    var icon = document.querySelector('[data-framer-name="Menu Icon"]');
    if (!icon) return;
    icon.setAttribute("role", "button");
    icon.setAttribute("aria-label", "Ouvrir le menu");
    icon.setAttribute("aria-expanded", "false");
    function toggle() {
      var open = document.body.hasAttribute("data-cm-menu-open");
      if (open) { document.body.removeAttribute("data-cm-menu-open"); icon.setAttribute("aria-expanded", "false"); icon.setAttribute("aria-label", "Ouvrir le menu"); }
      else { document.body.setAttribute("data-cm-menu-open", ""); icon.setAttribute("aria-expanded", "true"); icon.setAttribute("aria-label", "Fermer le menu"); }
    }
    icon.addEventListener("click", toggle);
    icon.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
    document.querySelectorAll(".cm-mobile-menu a").forEach(function (a) { a.addEventListener("click", function () { document.body.removeAttribute("data-cm-menu-open"); }); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && document.body.hasAttribute("data-cm-menu-open")) toggle(); });
  });
})();
</script>"""

STYLE_BLOCK = """<style data-castmate-base>
/* CTA hover */
a:hover .framer-1r36vle, [data-highlight="true"]:hover .framer-1r36vle { opacity: 0; transform: scale(0.8); filter: blur(5px); -webkit-filter: blur(5px); transition: opacity 0.22s ease, transform 0.22s ease, filter 0.22s ease; }
a:hover .framer-1y6kmu5, [data-highlight="true"]:hover .framer-1y6kmu5 { opacity: 1; transform: none; filter: none; -webkit-filter: none; transition: opacity 0.22s ease, transform 0.22s ease, filter 0.22s ease; }
.framer-1r36vle, .framer-1y6kmu5 { transition: opacity 0.22s ease, transform 0.22s ease, filter 0.22s ease; }
/* Mobile menu */
.cm-mobile-menu { position: fixed; top: 70px; left: 0; right: 0; bottom: 0; background: rgb(13, 18, 49); padding: 24px 32px 32px; z-index: 1000; display: flex; flex-direction: column; gap: 20px; transform: translateY(-100%); transition: transform 0.28s cubic-bezier(0.4,0,0.2,1); pointer-events: none; }
[data-cm-menu-open] .cm-mobile-menu { transform: translateY(0); pointer-events: auto; }
[data-cm-menu-open] { overflow: hidden; }
.cm-mobile-menu a { color: rgb(255, 255, 255); font-family: 'Archivo', system-ui, sans-serif; font-size: 22px; font-weight: 500; text-decoration: none; padding: 12px 0; }
.cm-mobile-menu .cm-mobile-menu__cta { background: rgb(80, 18, 2); color: rgb(255, 255, 255); border-radius: 12px; padding: 16px 24px; text-align: center; font-size: 18px; margin-top: 16px; box-shadow: inset 0 0.5px 0 0 rgba(255,255,255,0.2); }
</style>"""


def transform(html: str) -> str:
    # 1. Strip Framer <script>...</script> blocks (drop ALL on subpages)
    out, i = "", 0
    while True:
        m = html.find("<script", i)
        if m == -1:
            out += html[i:]
            break
        end = html.find("</script>", m) + len("</script>")
        out += html[i:m]
        i = end
    html = out
    # 2. Strip Framer modulepreload links
    html = re.sub(r'<link rel="modulepreload"[^>]*\.mjs"[^>]*>', "", html)
    # 3. Inject our CSS + reveal + drawer + toggle
    if "data-castmate-base" not in html:
        html = html.replace("</head>", STYLE_BLOCK + "</head>", 1)
    if "data-castmate-reveal" not in html:
        html = html.replace("<body>", "<body>" + REVEAL_SCRIPT + DRAWER, 1)
    if "data-cm-menu-open" not in html:
        html = html.replace("</body>", TOGGLE_JS + "</body>", 1)
    return html


SRC = Path("src")
SUBPAGES = [
    SRC / "contact" / "index.html",
    SRC / "demo" / "index.html",
    SRC / "legal" / "conditions-utilisation" / "index.html",
    SRC / "legal" / "engagements" / "index.html",
    SRC / "legal" / "mentions-legales" / "index.html",
    SRC / "legal" / "protection-donnees" / "index.html",
]

for p in SUBPAGES:
    if not p.exists():
        print(f"MISSING: {p}")
        continue
    html = p.read_text(encoding="utf-8")
    before = len(html)
    html = transform(html)
    new_path = p.with_suffix(".njk")
    new_path.write_text(html, encoding="utf-8")
    p.unlink()
    print(f"{p.relative_to(SRC)} -> {new_path.name}: {before} -> {len(html)}")

print("Done.")
