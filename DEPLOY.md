# Deploying ZZZ Female Measurements

Everything the site needs lives in **`docs/`** — the roster and tools pages, 147 static
character pages (49 agents × English/Japanese/Simplified Chinese), three
methodology/FAQ pages, the dataset exports, WebP artwork, bundled fonts, icons, the
service worker and the crawler files. Nothing else in the repository is served.

```
docs/
  index.html               interactive chart (49 cards pre-rendered)
  tools.html               cup distributions, matching, game and sandbox
  methodology.html         method, classes, FAQ
  characters/*.html        49 English profiles
  ja/, zh/                 localized profiles + methodology
  data/                    measurements.json · measurements.csv · schema.json
  offline.html             service-worker fallback
  sw.js                    versioned cache
  manifest.webmanifest     PWA metadata (incl. maskable icon)
  404.html                 absolute-base not-found page
  robots.txt sitemap.xml .nojekyll
  og.png favicon.* icon-*.png
  fonts/                   22 woff2 + fonts.css + OFL/licence notes (local)
  images/                  49 sheet crops
  character_images/        53 portraits + 26 outfit renders + responsive thumbs/
```

≈ **644 files / 26.0 MB** (the responsive thumb set adds storage but cuts transfer).

## 1. Set the URL

`canonical`, Open Graph, the sitemap and the service worker all use the deployed
address. Re-pack with the real one (the default is the current Pages URL):

```bash
python3 tools/pack_site.py --site-url https://<account>.github.io/<repo>/
```

## 2. Publish on GitHub Pages

**Auth on this machine:** there is no SSH key, so `git@github.com:...` remotes are
refused. The `gh` CLI is installed and authenticated (currently as **`yangandi114`**,
token scopes include `repo`), and `gh auth setup-git` has wired that token into git
for HTTPS. Keep the remote on HTTPS:

```bash
git remote set-url origin https://github.com/<account>/zzz-measurements.git
```

Create the repo and push in one step:

```bash
gh repo create zzz-measurements --public --source=. --push
```

If the site should live under a **different account** than the one `gh` is logged
into (for example `nullhollow`), either switch accounts first:

```bash
gh auth login
gh repo create zzz-measurements --public --source=. --push
```

or create the empty repo on github.com with that account, add `yangandi114` under
**Settings → Collaborators → Add people** with *Write* access, then:

```bash
git remote set-url origin https://github.com/<account>/zzz-measurements.git
git push -u origin main
```

Then on GitHub: **Settings → Pages → Build and deployment → Deploy from a branch →
`main` / `docs`**. The site appears within a minute.

## 3. Rebuild and validate

```bash
python3 tools/pack_site.py            # full pipeline + docs/
python3 tools/validate.py             # data, assets, links, JSON-LD, crawler files
```

`pack_site.py` runs, in order:

1. `build_data.py` — `measurements3.3.csv` → `tools/data.json`
2. `describe.py` — generated profile text (cm + in)
3. `build_html.py` — `index.html` with static cards and JSON-LD
4. `build_pages.py` — character pages, methodology, exports, offline page
5. copies assets, writes `sw.js` / sitemap / manifest / 404, checks every local link

Useful flags: `--no-rebuild` packs the current `index.html`; `--out DIR` writes
somewhere else.

Asset-only steps (outputs are committed):

```bash
python3 tools/refetch_images.py   # official portraits at 1280 px tall (network)
python3 tools/make_thumbs.py      # 320/640/1024/1280 WebP + AVIF (needs Pillow AVIF)
python3 tools/make_favicon.py     # SVG, ICO, PWA + maskable icons
python3 tools/make_og.py          # 1200×630 social card (needs Chrome)
```

## 4. CI

`.github/workflows/ci.yml` runs on every push/PR:

* installs `requirements.txt`
* builds and packs the site
* runs `tools/validate.py`
* fails if the rebuild differs from the committed `docs/`, `index.html` or
  `tools/data.json` (reproducibility check)
* uploads `docs/` as an artifact

So: build locally, commit `docs/`, push. If CI reports a diff, run the same
`pack_site.py --site-url ...` command and commit the result.

## What ships and what does not

| shipped | left out (dev only) |
|---|---|
| `index.html`, character pages, methodology, data exports, service worker | `tools/` (pipeline, data.json, templates) |
| all WebP artwork + thumbs, fonts, icons, OG card | `measurements3.3.csv` (source sheet) |
| `robots.txt`, `sitemap.xml`, `manifest.webmanifest`, `404.html`, `offline.html`, `.nojekyll` | `zzz3.3.webp` (3.8 MB source contact sheet), `bug/` |
| | `visual-center-demo.html` + `visual-masks.js` (alignment lab), `ui-proposal.html` |

`pack_site.py` deletes everything else in `docs/` on purpose, but preserves
search-console verification files (`google*.html`, `BingSiteAuth.xml`, `yandex_*.html`).

## SEO & sharing

* per-character `<title>`, description, canonical and Open Graph tags
* JSON-LD: `WebSite`, `WebPage`, `Dataset` (with `dateModified`, `distribution`,
  `measurementTechnique`, rights), `ItemList`, `ProfilePage` + `Person`,
  `BreadcrumbList`, `FAQPage`
* 147 static profile pages (EN/JA/ZH) plus three methodology pages in the sitemap
* a `<noscript>` table and 49 pre-rendered cards, so crawlers and no-JS visitors get
  every measurement
* local fonts, responsive `srcset` artwork (AVIF first, WebP fallback, 320/640 px),
  full 1280 px art in character-page heroes and the detail view, one
  `fetchpriority="high"` podium image, lazy loading below the fold
* shareable URL state (filters, sort, view, unit, language, comparison, open character)
* official localized character names from the HoYoverse pages, stored in
  `tools/localized_names.json`

## Troubleshooting

| symptom | cause / fix |
|---|---|
| `missing artwork` from `build_html.py` | run `python3 tools/make_thumbs.py`; check `character_images/` |
| `broken local reference` | a page links to a file the pack does not copy; fix the source, not `docs/` |
| CI reproducibility diff | `docs/` was not rebuilt after a data/template change |
| 404 assets break on nested URLs | `404.html` must keep its `<base href="...">` |
| pages show old copy | GitHub Pages caches for ~10 min; hard-refresh or check the Actions run |
