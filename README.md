# ZZZ Female Measurements

A static, self-contained reference for the female *Zenless Zone Zero* roster: height,
bust, under-bust, waist, hips and thigh circumference in cm and inches, plus
proportions, silhouette reads and UK/US/EU bra sizing.

Live site: <https://nullhollow.github.io/zzz-measurements/>

## What is in here

```
index.html                 dev build of the interactive page
measurements.csv           source sheet (the only hand-edited data)
character_images/          52 official portraits + 24 outfit renders + thumbs/
images/                    48 sheet crops
fonts/                     bundled Anton / Chakra Petch / Inter woff2
tools/                     build pipeline, scrapers and the alignment lab
docs/                      the packed site (served by GitHub Pages)
```

The site ships from **`docs/`** only. Nothing in `docs/` is hand-edited except
search-console verification files, which `pack_site.py` preserves.

## Build

```bash
pip install -r requirements.txt
python3 tools/pack_site.py --site-url https://<user>.github.io/<repo>/
python3 tools/validate.py  --site-url https://<user>.github.io/<repo>/
```

`pack_site.py` runs the pipeline and writes a complete `docs/`:

1. `build_data.py` — CSV → `tools/data.json` (ratios, classes, percentiles, provenance)
2. `describe.py` — generated profile text in cm and inches
3. `build_html.py` — `index.html` incl. static cards and JSON-LD
4. `build_pages.py` — 48 character pages, methodology/FAQ, dataset exports, offline page
5. crawler files, PWA manifest, service worker, link check

Optional asset steps (already committed):

```bash
python3 tools/make_thumbs.py      # 320/640 px WebP + AVIF responsive set
python3 tools/make_favicon.py     # SVG, ICO, PWA + maskable icons
python3 tools/make_og.py          # social card (needs Chrome)
```

## Payload

Cards, the table and the podium use a `<picture>` set: AVIF 320/640 with WebP
fallbacks and `sizes`, so a phone downloads ~120 KB of artwork for the first screen
instead of ~0.5 MB. Full 1024 px renders are only fetched when a detail view opens.
The HTML is ~61 KB gzipped locally (GitHub Pages serves it compressed), and the
page keeps its 48 static cards.

## Data model

One row per character in `measurements.csv`. `tools/meta.json` documents every
derived field, carries the schema version and the data date.

* **Standard model is canonical.** Measured outfits are separate `skin` records;
  art-only outfits never touch a number.
* **`stature_cm`** is the comparison height. It equals the charted height unless
  the chart counts an appendage (Miyabi's ears), where it uses head height.
* **Confidence** is derived from the sheet's own notes: `charted`, `estimated`, `partial`.
* Percentiles are roster percentiles of the raw centimetre value; stature uses `stature_cm`.

## Validation

`tools/validate.py` checks arithmetic and conversions, class/percentile consistency,
every referenced asset, character pages, JSON-LD, the sitemap, the service worker,
`docs/` hygiene and every local `href`/`src`. CI runs the build, the validator and a
reproducibility diff on each push.

## Deploy

GitHub Pages serves `main` / `docs`. Full instructions and the URL switch are in
[DEPLOY.md](DEPLOY.md).

## Rights

Measurements compiled from [modelmetrics.net](https://modelmetrics.net). Character
artwork is © HoYoverse, shown via the ZZZ Fandom wiki as fair use. See the footer and
methodology page for the exact wording. Do not relicense the artwork.
