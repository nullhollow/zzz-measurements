# AGENTS.md

Operational guide for this repository. `README.md` explains the architecture;
`DEPLOY.md` covers hosting and account details. This file is the working
contract for changing the site.

The project is a hand-curated dataset with a generated site. Treat
`measurements3.3.csv` as the input, the Python pipeline as the only writer, and
`docs/` as an artifact.

## House style

- Avoid unnecessary secondary labels and descriptions. Let the layout do the
  explaining.
- Prefer one clear label and a value over a label, a helper line and a caption.
- Reuse existing sections, CSS variables and components. Do not add a panel for
  a single number or a new badge for a value the layout already communicates.
- Keep English, Japanese and Chinese copy equally finished. No placeholders or
  literal translations.
- Do not add confidence badges. `confidence` stays in the exports/provenance.
- Bust difference is display/export data. Do not use it for ranking, filtering
  or comparison.

## Source of truth

| Path | Role |
| --- | --- |
| `measurements3.3.csv` | The only hand-edited measurement source. |
| `tools/build_data.py` | CSV → `tools/data.json`; classes, percentiles, outfits, provenance. |
| `tools/describe.py` | Generated English/Japanese/Chinese profile prose. |
| `tools/build_html.py` | Builds the interactive `index.html` from `tools/template.html`. |
| `tools/template.html` | Interactive UI, styles, client-side live calculations and modal. |
| `tools/card.tmpl.html` | Shared card markup used by the static cards and the live re-render. |
| `tools/build_pages.py` | Static profiles, methodology pages, exports, offline page. |
| `tools/pack_site.py` | Full pipeline, asset copy, service worker, sitemap, link check → `docs/`. |
| `tools/validate.py` | Data and packed-site validation. |
| `tools/meta.json` | Schema version, data date, rights and field documentation. |
| `tools/localized_names.json` | Official Japanese/Chinese names and HoYoverse source URLs. |
| `character_images/` | Portraits, outfit art and generated responsive thumbs. |
| `images/` | Sheet crops used by profiles and comparison views. |
| `fonts/` | Bundled ZZZ subset and fallback fonts. |
| `docs/` | Deployed output. Never hand-edit. |
| `measurements.csv` | Legacy sheet. Not read by the build; leave it alone. |
| `zzz3.3.webp` | Source contact sheet. Not shipped. |

`tools/data.json`, `index.html`, `character_images/thumbs/`, `docs/sw.js`,
`docs/sitemap.xml` and everything else in `docs/` are generated. Do not edit
them directly; fix the generator and rebuild. The only hand-maintained files
allowed inside `docs/` are search-console verification files
(`google*.html`, `BingSiteAuth.xml`, `yandex_*.html`), which `pack_site.py`
preserves.

Raw uploads can live at the repository root. Files under `images/`,
`character_images/` and `fonts/` are copied into `docs/`, so do not put PSDs,
source PNGs or other large working files there unless they should ship.

## Build and validate

```bash
pip install -r requirements.txt

python3 tools/pack_site.py --site-url https://nullhollow.github.io/zzz-measurements/
python3 tools/validate.py  --site-url https://nullhollow.github.io/zzz-measurements/
```

`pack_site.py` runs, in order:

1. `build_data.py` — CSV → `tools/data.json`
2. `describe.py` — adds generated prose to `tools/data.json`
3. `build_html.py` — writes `index.html`
4. `build_pages.py` — writes static pages and exports into `docs/`
5. copies assets, writes the service worker/sitemap/manifest/404 and checks
   every local reference

Useful flags: `--no-rebuild` packs the current `index.html` without rerunning
the data/build steps; `--out DIR` writes somewhere else. Do not use
`--no-rebuild` after changing the CSV, generator or template.

Serve the packed site locally:

```bash
cd docs
python3 -m http.server 8765
```

At the time of writing the baseline is **49 displayed entries, 147 localized
profile pages, 643 packed files, 25.0 MB and 0 broken local references**. Treat
these as regression checks, not constants. The validator recalculates the
expected roster count; update the manual counts in `README.md` and `DEPLOY.md`
when the roster or shipped file total changes.

## Edit map

| Change | Edit here |
| --- | --- |
| Add or correct measurements | `measurements3.3.csv` |
| Change shape/percentile/class rules | `tools/build_data.py` **and** the live copy in `tools/template.html` |
| Change cup ranking | `tools/build_data.py`, `tools/build_html.py` (initial order) **and** `tools/template.html` |
| Change generated profile wording | `tools/describe.py` |
| Change interactive markup, styles or behavior | `tools/template.html` |
| Change card layout or markup | `tools/card.tmpl.html` (shared by static cards and the live re-render) |
| Change static profile markup | `tools/build_pages.py` |
| Change metadata, source text or data date | `tools/meta.json` |
| Add official localized names | `tools/localized_names.json` |
| Add portraits/outfit art | `character_images/`; update `sources.json` or `skins.json` |
| Regenerate card/hero crops | `character_images/thumbs/` via `tools/make_thumbs.py` |
| Add a shipped root asset | `ASSET_FILES` in `tools/pack_site.py` |
| Add a shipped asset directory | `ASSET_DIRS` in `tools/pack_site.py` |

## Data invariants

- Each CSV row is one measurement record; four measured-outfit rows merge into
  their owning character. Lucy (swimsuit), Vivian (swimsuit) and Belle (summer)
  become nested `skin` records; Jane Doe (skin) replaces her canonical record.
- The standard model is canonical. Art-only outfits never change any number.
  Measured outfits are separate `skin` records and are not part of roster
  percentiles.
- `stature_cm` is the value shown as **Height** and used for every comparison.
  It normally equals the charted `cm`. Where the chart counts an appendage, it
  uses head height instead. Miyabi is the standing example: charted 170 cm
  including ears, effective stature 152.1 cm, with the ear note preserved.
  The 3.3 sheet has no effective-height column; Miyabi's value lives in
  `STATURE_OVERRIDE` in `tools/build_data.py`. Do not drop the 170 cm note.
- Jane Doe's canonical entry uses **Nocturne of Light**. Do not revert her to
  the standard model or treat her outfit as an optional art-only extra.
- Bust difference is recomputed from raw bust minus under-bust to one decimal
  place. The rounded diff columns in the sheet are not used. It is display and
  export data only.
- Cup ranking uses the **UK cup letter first**, then the band. Single-letter
  cups outrank their doubled forms (G > GG); the band decides within a letter.
- Percentiles are roster percentiles of raw centimetres across displayed
  entries, not skin records. Height uses `stature_cm`. Values are 0–1 in the
  data, rendered as 0–100.
- Shape is computed from bust, waist and hips:
  - `flare = min(bust/waist, hip/waist)`
  - `balance = min(bust, hip) / max(bust, hip)`
  - Hourglass: `flare >= 1.45` and `balance >= 0.85`
  - Straight: `flare < 1.30` or `balance < 0.75`
  - Otherwise: Balanced
  - `hourglass_score = flare × balance`
- Waist, hip and thigh classes are roster terciles of the raw centimetre
  circumference. The curators' `THIGH_PIN` set overrides the raw thigh tercile
  for visual reads and is labelled “hand-pinned” in the UI. Do not add or
  remove pins without an explicit editorial decision.
- Height groups: Petite below 150 cm, Mid 150–165 cm, Tall above 165 cm.
- The podium, highlights, rankings, percentiles, classes, filters, comparison
  winners and detail values are derived. Never hardcode a placement or a rank
  table. A new character needs a CSV row and art, not ranking edits.
- `confidence` remains in `tools/data.json` and the exports as provenance, but
  the UI does not render confidence badges. Do not reintroduce them.
- Default sort and the largest-cup podium use UK cup size. Bust difference is
  not in the comparison table.

## Adding or changing a character

1. Append one row to `measurements3.3.csv` in the existing 23-column order.
   Keep the header intact. Use `??` for an unreadable/missing thigh (as the
   sheet does); do not invent a number. Put caveats in `Notes`.
2. If the source name differs from the display name, or the image slug differs,
   add the mapping in `build_data.py` (`DISPLAY`, `IMG`, `VARIANT_OF`,
   `OUTFIT`). Do not rename an existing `Character` or display name casually:
   `slug` is the public URL (`/characters/<slug>.html`) and changing it breaks
   links and indexed pages.
3. Add `character_images/<official>.webp` — a transparent portrait, 1280 px
   tall maximum. Add a `character_images/sources.json` record with the source
   URL, wiki page/file and licence note. The `file` field in `sources.json` is
   `<official>.png` even though the shipped portrait is `.webp`; follow the
   existing records. The build reads the portrait's aspect ratio, so it must
   exist before building.
4. Add the sheet crop `images/<img>.webp` (or regenerate crops with
   `tools/extract_portraits.py`), then regenerate responsive thumbs with
   `python3 tools/make_thumbs.py --force`.
5. Add the official localized name and source URLs to
   `tools/localized_names.json`, keyed by the **slug** (for example
   `"phoenix"`), with `ja`, `zh`, `source_ja` and `source_zh`.
6. Add outfits if applicable (below).
7. Set `tools/meta.json` `data_updated` to the current ISO date. Change
   `schema_version` only for a breaking export change.
8. Run the full pack and validator. Check all three profile URLs, the card, the
   modal, thumbnails and the dataset exports. No ranking edits should be
   needed.
9. Update the manual counts in `README.md` / `DEPLOY.md` if the roster or
   shipped file total changed, and add a `CHANGELOG.md` entry.

## Outfits

**Measured outfit** (has its own numbers):

- Add a CSV row using the existing `Character (outfit)` convention, then add
  the display/variant/outfit mappings in `build_data.py`. Follow the existing
  `Lucy (swimsuit)`, `Vivian (swimsuit)` and `Belle (summer)` patterns.
- Add its portrait to `character_images/` and its provenance to
  `character_images/sources.json`.
- The build nests it as `skin` on the standard model, excludes it from the
  roster cards and shows the standard/outfit toggle. It does not change the
  base rankings.
- `build_data.py` uses matching `wiki_file` values in `sources.json` to keep
  measured outfits out of the art-only list. Keep those values consistent or
  the outfit will be duplicated or misclassified.

**Art-only outfit** (no measurement data):

- Add an item to `character_images/skins.json`. The top-level key is
  `<official>.png` (legacy), while the items carry `label`, `type` (for
  example `Paid`), `file` (the served `.webp`), optional `avif`, and
  `wiki_file`. A `.png` value in `file` is normalized to `.webp` by the build.
- Do not add a CSV row and do not assign numbers. Art-only outfits never touch
  rankings or comparisons.
- The static gallery and detail modal automatically render a `<picture>` with
  AVIF first and WebP fallback when `avif` is present.
- The current Phoenix skin art is 870 × 1280: WebP quality 90 with alpha,
  AVIF quality 65. Follow that pattern for new skin art and add the `avif`
  field. If only a WebP exists, the UI still works, but the AVIF path should be
  provided for new art.
- `tools/fetch_skins.py` can refresh wiki art, but it can overwrite curated
  uploads. Phoenix's high-resolution art is protected by the `EXTRA` entries
  only while the files exist; do not run `--force` unless you intend to reset
  that art.

## Localization

The three locales are English at `/characters/`, Japanese at
`/ja/characters/` and Simplified Chinese at `/zh/characters/`. Method pages
mirror the same paths. Generated `hreflang` alternates and the sitemap must
stay in sync.

- Use the official HoYoverse names, not literal translations and not Fandom
  romanizations. Record both source URLs in `tools/localized_names.json`.
- `build_data.py` attaches `name_ja`/`name_zh`; `describe.py` generates
  `desc_ja_cm`, `desc_ja_in`, `desc_zh_cm`, `desc_zh_in`, `read_ja`, `read_zh`,
  `tags_ja`, `tags_zh`, `notes_ja` and `notes_zh`. Do not hand-edit generated
  pages to fix copy — change the generators.
- Japanese and Chinese copy should read natively, not like translated English.
  Keep units localized consistently (`cm` / `インチ`, `厘米` / `英寸`).
- When adding a new chart note, add its Japanese and Chinese mapping to
  `NOTE_JA` / `NOTE_ZH` in `describe.py`. An unmapped note falls back to
  English and is a bug.
- Interactive UI strings live in the `I18N` object in `tools/template.html`;
  static-page strings live in `PAGE` in `tools/build_pages.py`. Add every new
  string to all three languages in both places.
- Dataset/export fields stay English. Localized copy uses the official names
  and natural phrasing.

## Front end and live calculations

The interactive page recalculates derived values from raw centimetres in the
browser; the static pages and exports use the Python pipeline. The rules are
implemented twice:

- `tools/build_data.py` for `tools/data.json`, static pages and exports
- `tools/template.html` (`computeDerived()`, `cupScore()`, podium/highlight
  code) for the live page

If you change a formula, ranking rule or class threshold, change both and
verify they agree. `validate.py` checks the Python-side data, not the JS
calculation. The live page must never contain handwritten podium picks or rank
tables; any initial values are generated fallbacks, and `computeDerived()`
recalculates them on load.

Preserve:

- shareable URL state: query, filters, sort, view, unit, language, comparison
  and open character
- the pre-rendered cards and `<noscript>` table
- the comparison tray (2–4 agents) and its winner highlighting
- `<picture>` artwork with AVIF first and WebP fallback; lazy-load below the
  fold, priority for the first podium image
- keyboard focus, the skip link, `main`, modal `aria-modal`, the polite live
  region and reduced-motion behavior
- the existing ZZZ visual language: dark/light palettes, acid-lime accent,
  hazard yellow, signal orange, holo blue, metric colours and tabular numerals

No confidence badges. No bust-diff comparison column. No extra explanatory
labels where the section heading and values already say it.

## Art, assets and fonts

- Portraits are transparent WebPs, 1280 px tall maximum, stored at
  `character_images/<official>.webp`. Their aspect ratio drives card and hero
  layout. Refresh official portraits with `tools/refetch_images.py` (network),
  then regenerate thumbs.
- Responsive thumbs are generated, never hand-edited:
  `python3 tools/make_thumbs.py --force` writes 320/640 WebP and
  320/640/1024/1280 AVIF. AVIF requires Pillow with AVIF support; if
  `PIL.features.check('avif')` is false, the thumb generator skips AVIF and
  the validator will fail on missing assets.
- The sheet crops in `images/` come from `zzz3.3.webp` via
  `tools/extract_portraits.py`. If the sheet or roster order changes, update
  its `NAMES` list and regenerate.
- `pack_site.py` copies all files in `images/`, `character_images/` and
  `fonts/` except `sources.json`, `skins.json` and editor junk. Keep raw
  source files outside those directories.
- The primary UI face is a subset of **印品鸿蒙体 / inpin hongmengti**, a
  commercial typeface used at the owner's direction. Do not add or redistribute
  fonts without a licence. The GB2312 subset lacks 58 Japanese glyphs; the
  fallback chain to Noto Sans JP 900 is intentional. Test Japanese punctuation
  (`・`, `見`, `長`, `開`, `時`) when touching fonts. Rebuild subsets with
  `tools/update_cjk_fonts.py` or `tools/subset_zzz_font.py`, then repack.
- Character art is © HoYoverse, shown as fair use; measurements are compiled
  from modelmetrics.net. Keep the footer, methodology and source attribution
  intact. Do not relicense artwork or fonts.

## QA checklist

Run the pack and validator before calling a change done:

```bash
python3 tools/pack_site.py --site-url https://nullhollow.github.io/zzz-measurements/
python3 tools/validate.py  --site-url https://nullhollow.github.io/zzz-measurements/
python3 -m py_compile tools/*.py
git diff --check
```

Then inspect the packed site locally:

- all three language versions of a changed profile, plus the methodology page
- card, table, filters, unit toggle, language switch, comparison tray and modal
- outfit modal/gallery: AVIF is selected in a supporting browser; WebP remains
  the fallback
- 390 px and 1440 px layouts, no horizontal scroll, no console errors
- service worker/cache behavior after a rebuild; unregister or use a fresh
  profile if old copy appears
- `docs/` contains the regenerated output and the local link check reports zero
  broken references

`validate.py` checks arithmetic, conversions, classes/percentiles, assets
(including outfit AVIF), all three profile pages, names, JSON-LD, canonical
URLs, the sitemap, the service worker, `docs/` hygiene and local links. It does
not check visual layout, translation quality, JS/Python parity or dynamic
image paths; verify those manually.

## Deploy

GitHub Pages serves `main` / `docs`. Keep the remote on HTTPS; this machine has
no SSH key and `gh` is authenticated for HTTPS Git. See `DEPLOY.md` for the
account setup and repository creation details.

1. Build and validate with the exact production `--site-url`.
2. Commit the source change together with regenerated `index.html`,
   `tools/data.json`, `docs/` and any new art/thumbs. Do not commit
   `__pycache__`, temporary screenshots or working PNGs under shipped asset
   directories.
3. Push to `main`. CI runs the same build, validator and a reproducibility diff
   against `docs/`, `index.html` and `tools/data.json`.
4. Watch the build and Pages runs:

   ```bash
   gh run list --limit 3
   gh run watch <run-id> --exit-status
   ```

5. Verify the live URL and changed assets return 200. GitHub Pages can cache
   for about ten minutes; hard-refresh before assuming a deploy failed.

If the Pages URL changes, update the `--site-url` in
`.github/workflows/ci.yml`, `PLACEHOLDER` in `tools/pack_site.py`, the default
`SITE` constants in `tools/build_html.py` / `tools/build_pages.py` and
`DEPLOY.md`, then rebuild and commit the regenerated `docs/`. If CI reports a
reproducibility diff, rerun `pack_site.py` with the same URL and commit the
result.

## Common failures

| Symptom | Fix |
| --- | --- |
| `docs/` or `index.html` changes keep disappearing | You edited generated output; edit the generator/template and repack. |
| `missing artwork` from `build_html.py` / validator | Add the portrait or run `make_thumbs.py --force`. |
| Broken local reference | Fix the source path or pack list, not `docs/` by hand. |
| CI reproducibility diff | Rebuild with the exact CI URL and commit `docs/`, `index.html`, `tools/data.json`. |
| Old copy on the live site | Pages cache or service-worker cache; hard-refresh/clear and check the Pages run. |
| Missing AVIF/WebP outfit file | Generate both; if `avif` is set in `skins.json`, both paths must exist. |
| Japanese glyphs render as tofu | Rebuild the CJK fallback subsets; do not remove the Noto Sans JP fallback. |
| Custom Phoenix outfit art disappeared | `fetch_skins.py --force` overwrote it; restore the high-resolution sources. |
| A renamed character 404s | Slugs are public URLs; keep the old slug or add a redirect/migration. |
| Raw PNGs inflate `docs/` | Move source files out of `images/`, `character_images/` or `fonts/`. |
| `--no-rebuild` shows stale data | It reuses `index.html`; run the full pack after source changes. |
| New locale string shows English | Add it to all three locales in both `I18N` and `PAGE`. |
| New note is English in JA/ZH | Add the mapping to `NOTE_JA` / `NOTE_ZH`. |
| Wrong package/site URL in canonical tags | Rebuild with the production `--site-url`; do not patch generated HTML. |

## Definition of done

- `pack_site.py` and `validate.py` pass with zero broken references.
- The changed data appears correctly in English, Japanese and Chinese, on both
  the interactive page and the static profiles.
- Derived values come from raw data; no ranking, podium or percentile was
  hand-edited.
- Generated `docs/`, `index.html`, `tools/data.json` and new assets are
  committed with the source change.
- Mobile and desktop layouts, the modal, comparison and language/unit controls
  were checked.
- CI is green and the live page/assets were verified after deployment.
- The working tree is clean.

Update this file when the pipeline, commands or data invariants change.
