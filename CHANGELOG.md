# Changelog

## Unreleased — audit implementation

### Version 3.3 — Phoenix

- Added **Phoenix** (156 cm, UK 21C) from `measurements3.3.csv`: 59.4 cm bust,
  51.9 cm under-bust, 40.6 cm waist, 78.8 cm hips and 44.9 cm thigh.
- Added the official HoYoverse portrait plus both paid outfit renders,
  **The Illness Called Life** and **Daydream Complex**, as art-only outfit views.
- Added the official Japanese and Chinese names from the HoYoverse character
  page, and regenerated all 49 EN/JA/ZH profile pages and dataset exports.
- Re-imported the 3.3 contact sheet (`zzz3.3.webp`); all 49 sheet crops were
  rebuilt, including the new Phoenix crop.
- Moved the interactive rankings onto a live derivation pass: proportions,
  percentiles, cup/height/waist/hip/thigh classes, shape, podium, highlights and
  comparison winners are recalculated from raw centimetres in the browser.
- Removed the build-time 48-character warning and updated counts, docs and the
  service-worker payload for 49 entries.

### Typography
- Added a subset of **印品鸿蒙体 / inpin hongmengti**, the ZZZ Chinese UI face,
  for the Latin, Chinese and Japanese interface and profiles.
- Added OFL fallbacks for glyphs missing from the GB2312 cut: a weight-matched
  Noto Sans JP 900 for missing Japanese glyphs, Noto Sans JP / Noto Sans SC for
  body text, Dela Gothic One as a secondary Japanese display fallback and Noto
  Sans SC 900 for Chinese display. Japanese punctuation such as `・` and 58
  Japanese characters fall back instead of showing tofu.
- Added reproducible subset scripts and the inpin licence/attribution note.

### Multilingual profiles and names
- The EN / 日本語 / 中文 switch now localizes character names, generated profile
  copy in cm and inches, figure-read lines, class labels, filters, table headers,
  comparison rows and profile captions.
- Character names use the official HoYoverse localized names, recorded with source
  links in `tools/localized_names.json`; nothing is machine-translated from the
  English display name.
- Added 48 Japanese and 48 Simplified Chinese crawlable profile pages under
  `ja/characters/` and `zh/characters/`, localized methodology pages, `hreflang`
  alternates, and localized dataset profile links. English pages remain at the root.
- Profile wording was written per language rather than translated line by line;
  the Japanese and Chinese versions use natural, conversational phrasing.

### Data
- Standard model is now the canonical basis; measured outfits are stored separately
  instead of taking the larger value of two records per measurement.
- Added `stature_cm` / `stature_basis`; stature comparisons, sorting, filters, the
  tallest podium and height percentiles use it. Charted height stays visible.
- Added URL slugs, search aliases, portrait provenance, confidence flags and a
  schema version + data date (`tools/meta.json`).
- Bust diff is recomputed from bust minus under-bust; stale whole-number diff columns
  are no longer exported.
- Removed unused composite thigh z-scores; the documented raw-tercile + hand-pinned
  method is now the only implementation.
- Profile copy: waist wording no longer implies a height-relative class.

### Site
- 48 pre-rendered cards, so the roster paints before JavaScript and is crawlable.
- Shared card markup (`tools/card.tmpl.html`) between Python and JS, so the two
  renderers cannot drift.
- Accessibility: skip link, main landmark, keyboard cards/rows/plot points, focus
  trap + restore in the modal, `aria-modal`, `aria-pressed`, `aria-expanded`,
  `aria-sort`, live result counts, reduced-motion, high-contrast and forced-colors
  support, `prefers-color-scheme`-independent light theme.
- URL state for search, filters, sort, view, unit, artwork, language, theme,
  comparison set and the open character; Back closes the modal; Share uses the Web
  Share API with a clipboard fallback.
- Compare tray (up to 4) and a filter-aware scatter plot with selectable Y metric.
- Similar figures in the detail view, full-profile link, pre-filled error report.
- Mobile filter sheet, inert background, capped modal art, responsive table columns.
- Debounced search and rAF-batched range filters; delegated click handling.
- English / Japanese / Chinese UI labels; roster commentary stays English.
- Service worker with versioned cache, offline fallback and image runtime caching.
- Light theme, print stylesheet and a maskable PWA icon.

### Pages, data and crawlers
- 48 static character pages with canonical URLs, Open Graph, `ProfilePage` /
  `Person` JSON-LD, breadcrumbs, outfit gallery, provenance and prev/next links.
- Methodology + FAQ page with `FAQPage` JSON-LD.
- Versioned dataset exports: `data/measurements.json`, `.csv` and JSON Schema.
- Sitemap now lists every page; 404 resolves assets correctly from nested URLs.
- Dataset JSON-LD gains `dateModified`, `distribution`, `measurementTechnique` and
  rights metadata.

### Build & CI
- Pipeline is working-directory independent, fails on missing artwork, escapes
  injected data, and no longer packs `.DS_Store` or wiki manifests.
- Thumbnails cut the first-load artwork weight roughly in half.
- Font preloads and a single high-priority podium image instead of twelve.
- `tools/validate.py` + GitHub Actions: build, validate, reproducibility diff.
- Fixed `fetch_images.py` missing imports and `optimize_images.py` division by zero.

### Art resolution and sheet fix (follow-up)
- Official portraits were refetched at **1280 px tall** (+25% linear). Character-page
  heroes use the 1280 AVIF set, the gallery uses 640 px thumbs, and the detail view uses
  the 1280 px source WebP.
- Fixed the missing `imgSrc()` helper that broke the sheet toggle in the detail modal;
  sheet images now also fall back to the official portrait if a crop is unavailable.

### Data and ranking corrections (follow-up)
- Jane Doe now uses the Nocturne of Light measurements as her canonical record; the
  standard-model values are discarded for that entry.
- Miyabi's head height is corrected to **152.1 cm** (charted 170 cm still shown as a note).
- The default sort, table UK sort, podium and highlight now rank by **UK cup size**:
  single-letter cups outrank doubled forms (G > GG), then the band number decides
  (22E > 19E, 23GG > 21GG). Bust diff is kept as a measurement, not a ranking metric.
- Cup groups and the filter now follow the UK cup letter (A-B, C-D, DD-E, F-G, GG+).
- Shape now uses bust, waist and hips: Hourglass requires bust/waist and hip/waist ≥1.45
  plus bust–hip balance within 15%; Straight is flare <1.30 or mismatch >25%; the rest is
  Balanced. The sharpest-hourglass ranking uses flare × bust–hip balance.

### Height terminology (follow-up)
- The UI now uses a single **Height** value (`stature_cm`) instead of separate Height/Stature
  rows, columns and labels. Miyabi still shows her 170 cm charted figure as a note, while
  comparisons use the 152.1 cm head height.
- Removed the explanatory yellow-highlight sentence from the comparison table.

### Comparison UX (follow-up)
- Each card has a labelled **Compare** pill inside the artwork; selected cards get an acid
  border and the pill switches to **Added**.
- The compare tray says how many are picked, explains the next step, and disables
  **Compare** until two agents are selected.
- The comparison table uses 16 px values / 19 px headers on desktop (13 px on phones,
  all picks visible without horizontal scroll). Yellow marks the winner for height,
  cup, waist (smaller), hips and thighs; arrows show direction.
- Removed the confidence badges, table column, detail row and methodology section from
  the UI; confidence remains in the dataset exports as provenance.

### Payload and phones (follow-up)
- Responsive `<picture>` set: AVIF 320/640 with WebP 320/640 fallbacks and `sizes`.
  Measured first-screen artwork drops from ~556 KB to ~120 KB on a 390 px phone.
- Character pages load the 320/640/1280 hero set instead of the old 1024 px render.
- Cards gained a full 1024 px AVIF candidate and exact per-image `srcset` widths;
  2x desktop and phone cards now pick the full render instead of upscaling the
  640 thumb (1x desktop stays on the lighter 640 set).
- The embedded client dataset drops provenance-only fields; static cards are reused
  on first paint instead of being rebuilt.
- Phones get one horizontal card per row (art left, data right), a swipeable podium
  strip, a compact three-row control bar with the count moved into the filter sheet,
  and a four-column table (name, bust, waist, hip) with no horizontal scroll and a
  sticky name column; tapping a row opens the full record.
- The filter sheet is taller, applies from a sticky footer, and carries Reset/Share.
- Compare, filter and modal tap targets were enlarged; the modal art is capped at
  34vh so measurements are reachable without a long scroll.
