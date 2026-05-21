# CastMate — Intégration Sveltia CMS (brief pour Claude Code)

Objectif : permettre au client d'éditer **textes, images, vidéos et liens** de la
landing CastMate, sans toucher au code, depuis une page `/admin`.

Approche retenue : **build-time avec Eleventy (11ty)**. Le HTML Framer devient un
template qui lit le contenu depuis `src/_data/*.json`. Le site livré reste du HTML
statique pur (zéro JS framework, zéro JS client ajouté) — seul un build s'intercale.
Sveltia CMS commit les fichiers JSON dans GitHub → Vercel rebuild automatiquement.

## Contenu de ce bundle

```
src/admin/index.html      # loader Sveltia CMS (sert /admin)
src/admin/config.yml       # config Sveltia : 1 collection "files", 1 fichier par section
src/_data/*.json           # tout le contenu actuel de la page, déjà extrait et rempli
```

## Étapes d'intégration (Claude Code)

1. **Initialiser 11ty** sur le projet (`@11ty/eleventy`), `input: "src"`, `output: "_site"`.
   - Passthrough copy de `src/assets/` et de `src/admin/` (servir `/admin` tel quel).
   - Aucune autre dépendance npm n'est requise.

2. **Transformer l'export Framer en template** (`src/index.html` ou `.njk`) :
   remplacer chaque chaîne/asset codé en dur par la variable 11ty correspondante.
   Les données globales `_data/hero.json` sont accessibles via `{{ hero.title }}`,
   `{{ features.items }}` (boucle), etc. Conserver **exactement** le markup, les
   classes Framer et les query params responsive des images (`?width=...&height=...`).
   Exemple : `src="/assets/.../Xsw6...png?width=1440&height=1024"` →
   `src="{{ hero.image }}?width=1440&height=1024"`.

3. **Repérage** : chaque clé JSON correspond à un bloc réel de la page
   (hero, steps = section « Créez votre casting », features = « Conçu pour les équipes »,
   security, clarity = « Pilotez avec plus de clarté » + vidéo, teamCta, testimonials,
   faq, footer, nav, meta). Mapper 1:1.

4. **Médias** : `media_folder: src/assets/uploads`, `public_folder: /assets/uploads`.
   Les images/vidéos uploadées par le client via l'admin atterrissent là.
   Les valeurs initiales pointent vers les assets Framer existants (rien ne casse).

## Authentification (à faire manuellement, une fois)

Sveltia sur Vercel (hors Netlify) a besoin d'un client OAuth :

1. Déployer le Worker **sveltia-cms-auth** sur Cloudflare Workers (gratuit) :
   https://github.com/sveltia/sveltia-cms-auth
2. Créer une **OAuth App GitHub** (Settings > Developer settings > OAuth Apps) avec
   l'URL du Worker en callback ; renseigner client_id / client_secret dans le Worker.
3. Dans `config.yml`, renseigner `backend.repo` (owner/repo) et `backend.base_url`
   (= URL du Worker). C'est tout.

Alternative tout-Vercel : un handler OAuth serverless équivalent peut être hébergé
sur Vercel plutôt que Cloudflare (même principe, même `base_url`).

## À compléter côté contenu

- **FAQ** : seule la 1re réponse était visible sur le site. Les 7 autres `answer`
  sont vides dans `faq.json` → à remplir (par toi, ou par le client via l'admin).
- 1 coquille corrigée dans le témoignage de Clément (« maintenan » → « maintenant »).

## Rappel important

NoCodeXport est un export **one-shot**. À partir d'ici, **GitHub est la source de
vérité**, plus Framer. Une réextraction depuis Framer écraserait le templating : toute
évolution future passe par le code (structure) ou par Sveltia (contenu).
