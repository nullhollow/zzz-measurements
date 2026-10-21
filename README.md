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
2. `describe.py` — generated profile text in English, Japanese and Simplified Chinese (cm + inches)
3. `build_html.py` — `index.html` incl. static cards, localized data and JSON-LD
4. `build_pages.py` — 48 character pages × 3 languages, 3 methodology/FAQ pages, dataset exports, offline page
5. crawler files, PWA manifest, service worker, link check

Optional asset steps (already committed):

```bash
python3 tools/refetch_images.py   # official renders at 1280 px tall (needs network)
python3 tools/make_thumbs.py      # 320/640/1024/1280 WebP + AVIF responsive set
python3 tools/make_favicon.py     # SVG, ICO, PWA + maskable icons
python3 tools/make_og.py          # social card (needs Chrome)
```

## Compare

Every card has a labelled **Compare** pill inside its artwork. Pick 2–4 agents; the
tray explains the next step and enables **Compare** at two picks. The comparison
table uses larger values, shows direction arrows, and highlights the winner in
yellow for height, cup, waist (smaller), hips and thighs. Default sorting and the largest-cup podium use UK cup size. Confidence
badges are no longer shown; the raw field remains in the dataset exports.

## Languages

The language switch in the footer changes the interface, character names and the
figure-read/profile copy between English, Japanese and Simplified Chinese. Names are
the official localized names taken from the HoYoverse character pages (recorded in
`tools/localized_names.json`), not literal translations. The static profiles also
exist as crawlable pages at `/ja/characters/<slug>.html` and
`/zh/characters/<slug>.html`, with matching localized methodology pages and
`hreflang` alternates. The source/export fields stay in English.

## Payload

Cards, the table and the podium use a `<picture>` set: AVIF 320/640/full-1024
with WebP fallbacks and per-card `sizes`. 1x desktop cards get the 640 set at
roughly 1:1; 2x desktop and phone cards pick the full 1024 render instead of
upscaling the 640 thumb. A 2x phone loads ~430 KB of artwork for the first screen
(podium plus visible cards), and the rest lazy-loads. Character-page heroes use a 1280 px AVIF/source set, the gallery uses 640 px
thumbs and the detail view uses the 1280 px source render. The HTML is ~82 KB
gzipped locally (GitHub Pages serves it compressed), and the page keeps its 48
static cards.

## Data model

One row per character in `measurements.csv`. `tools/meta.json` documents every
derived field, carries the schema version and the data date.

* **Standard model is canonical**, except **Jane Doe**: her canonical entry uses the
  measured Nocturne of Light outfit. Other measured outfits are separate `skin`
  records; art-only outfits never touch a number.
* **`stature_cm`** is the comparison height shown in the UI as **Height**. It equals the charted height unless
  the chart counts an appendage (Miyabi's ears), where it uses head height.
* **Shape** uses bust, waist and hips: Hourglass needs bust/waist and hip/waist ≥1.45
  with bust and hips within 15%; Straight is flare <1.30 or a bust–hip mismatch >25%;
  the rest is Balanced. The sharpest-hourglass score is flare × bust–hip balance.
* **Cup ranking** follows the UK cup letter first (single letters outrank doubled forms,
  so G > GG) and then the band number.
* **Localized names and profiles** are stored as `name_ja`, `name_zh`, `desc_ja_cm`,
  `desc_ja_in`, `desc_zh_cm`, `desc_zh_in`, `read_ja`, `read_zh`, `tags_ja`, `tags_zh`
  and `notes_ja`/`notes_zh`. The names come from `tools/localized_names.json`, which
  records the official HoYoverse source for each character.
* **Confidence** values remain in the dataset exports as provenance; the UI no longer renders confidence badges.
* Percentiles are roster percentiles of the raw centimetre value; height uses `stature_cm`.

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
