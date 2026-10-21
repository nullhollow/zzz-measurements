# Deploying ZZZ Female Measurements

The whole site is packed into **`docs/`** — a self-contained folder with the page, the WebP
artwork, the bundled fonts, icons, the social card and the crawler files. Nothing else in this
repository is needed to host it.

```
docs/
  index.html              the site (203 kB, includes all 48 entries inline)
  og.png                 1200×630 social share card
  favicon.svg .ico       tab icon (SVG + multi-size ICO)
  icon-192.png 512.png   manifest / home-screen icons
  manifest.webmanifest   PWA metadata
  robots.txt  sitemap.xml  .nojekyll    crawler + Pages files
  404.html               styled not-found page
  fonts/                 16 woff2 + fonts.css (Anton, Chakra Petch, Inter)
  images/                48 sheet crops (WebP)
  character_images/      52 official renders + 24 outfit renders (WebP)
```

Total ≈ **7.6 MB**, 153 files. No CDN calls: every font and image is local.

## 1. Set your URL (once)

`canonical`, `og:url`, `og:image`, `robots.txt` and `sitemap.xml` need the final address.
Re-pack with your real Pages URL:

```bash
python3 tools/pack_site.py            # uses https://nullhollow.github.io/zzz-measurements/ by default
```

Different repo name? `python3 tools/pack_site.py --site-url https://nullhollow.github.io/<repo>/` and re-commit `docs/`.

## 2. Publish on GitHub Pages

**Auth on this machine:** there is no SSH key, so `git@github.com:...` remotes are refused. The
`gh` CLI is installed and authenticated (currently as **`yangandi114`**, token scopes include
`repo`), and `gh auth setup-git` has wired that token into git for HTTPS. Keep the remote on
HTTPS:

```bash
git remote set-url origin https://github.com/<account>/zzz-measurements.git
```

Create the repo and push in one step (uses the account `gh` is logged into):

```bash
gh repo create zzz-measurements --public --source=. --push
```

If the site should live under a **different account** than the one `gh` is logged into
(for example `nullhollow`), either switch accounts first:

```bash
gh auth login                    # choose the account that owns the site
gh repo create zzz-measurements --public --source=. --push
```

or create the empty repo on github.com with that account, add `yangandi114` under
**Settings → Collaborators → Add people** with *Write* access, then:

```bash
git remote set-url origin https://github.com/<account>/zzz-measurements.git
git push -u origin main
```

Then on GitHub: **Settings → Pages → Build and deployment → Deploy from a branch →
`main` / `docs`**. The site appears at `https://nullhollow.github.io/zzz-measurements/` (or the
account you used) within a minute.

## 3. Re-packing after a data or design change

```bash
python3 tools/pack_site.py            # uses https://nullhollow.github.io/zzz-measurements/ by default
```

That runs the full pipeline (`build_data.py` → `describe.py` → `build_html.py`), refreshes
`index.html`, and re-copies every asset into `docs/`. Add `--no-rebuild` to pack the existing
`index.html` as-is.

Rebuild the icons or the social card after a palette change:

```bash
python3 tools/make_favicon.py     # favicon.svg, favicon.ico, icon-192/512.png
python3 tools/make_og.py          # og.png from tools/og.html
```

## What ships and what does not

| shipped | left out (dev only) |
|---|---|
| `index.html`, all WebP artwork, fonts, icons, OG card | `tools/` (build scripts, data.json, template), `measurements.csv` |
| `robots.txt`, `sitemap.xml`, `manifest.webmanifest`, `404.html`, `.nojekyll` | `zzz3.2b.webp` (4.3 MB source contact sheet), `bug/` screenshots |
| | `visual-center-demo.html` + `visual-masks.js` (the alignment lab), `ui-proposal.html` (style tile) |

To publish the alignment lab alongside the site as well, copy it in and re-pack:

```bash
cp visual-center-demo.html visual-masks.js docs/
```

## SEO in the page

* `<title>ZZZ Female Measurements</title>`, meta description, keywords, author, robots
* canonical URL, Open Graph (`og:image` 1200×630) and Twitter `summary_large_image`
* JSON-LD: `WebSite` + `Dataset` (48 characters, variableMeasured list) + `ItemList` of the roster
* an `<h2>` naming "48 female agents" and a `<noscript>` fallback that renders the whole roster
  as a plain table, so crawlers and no-JS visitors still get every measurement
* local fonts, WebP artwork capped at 1024 px, lazy loading for the grid, `fetchpriority="high"`
  on the podium renders
