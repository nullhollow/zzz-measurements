# Changelog

## Unreleased — audit implementation

### Favourites page (2026-10-28)

- Increase PNG exports to 2160 px wide with vector text rendered at double
  resolution. Hyphenate English names when a word continues onto the next line.

- Add ordered SSS/S/A/B/C/D/E tiers with matching number badges, stronger purple
  for A and blue for B, using the site's existing ZZZ artwork, typography and hero.
- Support dragging, tap placement, earlier/later ordering, undo, device-local
  drafts and named boards, shared links and overall/per-tier numbering.
- Export a 1080 px wide PNG with localized names, title, optional author and art
  credit. Reuse the exact PNG in preview and download; omit unranked/empty tiers.
- Add EN/JA/ZH copy, responsive picker placement, cache/sitemap/PWA integration
  and regression coverage. Keep personal rankings separate from measurements.

### UK cup-order correction (2026-10-25)

- Correct UK progression to D < DD < E < F < FF < G < GG < H < HH < J < JJ,
  with band deciding only within the same cup. Eldreda's 23HH now outranks 22H.
- Use shared Python/JavaScript scoring for initial/live sorting, table order,
  podiums, comparison winners, cup charts and Higher or Lower. Update EN/JA/ZH
  guidance and regression tests, including full-roster game parity.
- Keep supplied sizes, raw measurements, filters and category counts intact.
  Cup summaries remain categorical; numeric measurement summaries are unchanged.

### Eldreda Sunbringer (2026-10-25)

- Add the supplied measurements, using 180.37 cm excluding horns for comparisons
  and preserving 193.37 cm including horns. Existing calculation and ranking rules
  are unchanged; roster-derived values now include 50 entries.
- Preserve UK 23HH and label US ≈23L / EU ≈50L as estimates. Explain the
  nonstandard band and independent project provenance in EN/JA/ZH and exports.
- Add optimized official artwork and the unchanged original PNG, with an official
  portrait fallback until a sheet crop is available. Preserve uploaded originals
  during reference refreshes and include new profiles in the first-build sitemap.

### Visual reference features (2026-10-23)

- Add an effective-height lineup with ruler, doorway and personal-height references,
  short/tall/faction/custom ordering and shareable selections.
- Add a schematic measurement guide with numbered controls and static text alternatives.
- Add source-linked agent faction, Attribute, Specialty, rank, release date and debut
  version to profiles, with separate metadata and EN/JA/ZH category names.
- Add a full-window original-art viewer on static and interactive profiles, using
  75 genuine source PNGs without resizing/re-encoding. Include native-pixel zoom,
  fit, pan, keyboard controls, background choices and original downloads.
- Use a compact mobile tool selector, maintain accessible focus and error states,
  and regenerate existing CJK subsets. Measurement exports and rankings are unchanged.

### Jane Doe original outfit (2026-10-23)

- Restore the original outfit artwork to Jane's gallery and interactive outfit
  selector, with AVIF/WebP and EN/JA/ZH labels. Nocturne of Light remains her
  canonical portrait and measurement record; the original outfit is art-only.

### Roster browsing and comparison editing (2026-10-23)

- Keep unknown table values last and retain table sorting/columns in shared URLs
  and navigation history. Show one unit and allow column selection on mobile.
- Move roster controls before collapsible Leaders, remove repeated highlights,
  and add removable active filters and empty-result recovery.
- Add character replacement/addition inside comparisons and contextual measurement
  help, with EN/JA/ZH copy, keyboard support and regenerated existing font subsets.

### Colour contrast and browser theme (2026-10-23)

- Fixed Compare/filter count badges, the skip link and outfit ribbons in light mode.
- Separated accent fills from text colours, strengthened input boundaries, and
  improved chart marks, focus, disabled states and light-mode shadows.
- Added System / Light / Dark preferences with browser appearance updates,
  shared URL support and early theme application. Static and offline pages use
  the same palette, including a browser-based fallback without JavaScript.
- Preserved measurement data, calculations and ranking rules.

### Tools usability and saved comparisons (2026-10-22)

- Fixed low-contrast table headings, overlapping tool navigation/controls and Back
  navigation between tools before adding features.
- Compacted the game layout, moved language/theme into Settings and made empty
  comparison actions link to the roster. Character/reference pickers accept names.
- Simplified comparison defaults and used the selected unit; additional source
  sizing, classes and commentary remain optional rows.
- Added named local comparison sets with restore, replacement, removal and undo,
  plus CSV exports of visible canonical values and reference differences.
- Added per-metric similarity contributions, source band-by-cup distributions and
  accessible chart/cell drill-down with character comparison actions.
- Refined light mode with neutral surfaces, stronger text/borders and restrained
  lime accents. Removed “silhouette reads” promotion and shortened browser titles
  to “ZZZ Measurements”. Completed EN/JA/ZH copy and regenerated the CJK subsets.
- Preserved all measurements, existing rankings, cup rules and dataset exports.

### Measurement settings and cup game rounds (2026-10-22)

- Added cup-size Higher or Lower rounds using the existing UK letter-first,
  band-second ranking, including equal answers and UK references after a guess.
- Grouped cm/inches and a global UK/US/EU display choice in a keyboard-accessible
  Settings dialog on both pages, with saved preferences and shared URL state.
- Applied the supplied sizing labels to interactive cards, table, podium values,
  detail/comparison views, distributions and game values. US/EU display choices
  preserve UK ranking, filtering and game answers; no conversion is inferred.
- Added mirrored math/regression checks, finished EN/JA/ZH copy and regenerated
  the existing CJK subsets for the new settings and methodology text.

### Cup distributions and dedicated tools page (2026-10-22)

- Added source UK cup-letter distributions with selected-character markers,
  categorical counts and full band-and-cup sizes in the value table. Cup size
  is the default distribution; existing cup order and rankings are preserved.
- Moved exploration to `tools.html`, with its own header and tool navigation.
  Removed the selector from the roster toolbar and preserved state across page
  navigation and older shared tool links.
- Added the page to the sitemap, offline cache, PWA shortcut and build checks,
  with finished EN/JA/ZH copy and regenerated fallback font subsets.

### Comparison and exploration tools (2026-10-22)

- Added comparison row selection/order, reference differences and same-height
  circumference equivalents at a chosen height, preserving measured height.
- Added weighted raw/height-adjusted similarity matching and a filtered-roster
  distribution explorer with comparison markers and an accessible value table.
- Added Higher or Lower rounds with displayed-value ties and a fictional figure
  sandbox for temporary comparisons and matching references.
- Kept sandbox records outside official data, classes, percentiles, rankings,
  games and exports. Shared URLs preserve validated tool settings and inputs.
- Finished controls and methodology in EN/JA/ZH, with shared Python/JS math,
  regression/parity tests and regenerated CJK font subsets.

### Height-adjusted comparison (2026-10-22)

- Added a comparison-only switch between raw measurements and circumferences
  expressed as a percentage of effective height in English, Japanese and Chinese.
- The adjusted mode uses `circumference_cm / stature_cm × 100`, with missing
  measurements left unranked and displayed ties sharing the highlight.
- Preserved the selected mode in shared URLs. Existing roster rankings, sorting,
  filters, percentiles, classes, podiums and cup rules are unchanged.
- Added mobile name wrapping and regenerated the existing CJK font subsets for
  the new controls and methodology copy.

### Correctness and localization (2026-10-22)

- Fixed all roster JSON-LD profile links and replaced truncated search descriptions
  with complete summaries in English, Japanese and Simplified Chinese.
- Aligned profile prose with the existing percentile-based Build class, corrected
  Japanese sentence endings and normalized chart-note punctuation.
- Restored Jane Doe's Nocturne of Light portrait and outfit name on the cards,
  static profiles and detail view without changing her canonical measurements.
- Localized footer links, controls and source metadata; corrected the under-bust
  table label and removed misleading US/EU text sorting. UK sorting is unchanged.
- Regenerated the existing CJK fallback subsets to cover the new localized copy.
- Added validation for structured-data links, Build/prose agreement, generated
  grammar, search descriptions, footer translations and canonical outfit art.

### Version 3.3 — Phoenix

- Added **Phoenix** (156 cm, UK 21C) from `measurements3.3.csv`: 59.4 cm bust,
  51.9 cm under-bust, 40.6 cm waist, 78.8 cm hips and 44.9 cm thigh.
- Added the official HoYoverse portrait plus both paid outfit renders,
  **The Illness Called Life** and **Daydream Complex**, as art-only outfit views.
- Replaced the Phoenix outfit art with the new high-resolution painted renders;
  the gallery and detail view serve AVIF with WebP fallback.
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
- The default sort, table UK sort, podium and highlight now rank by **UK cup size**.
  The original single/doubled-letter rule was corrected in the UK cup-order update
  above. Band decides within a cup (22E > 19E, 23GG > 21GG). Bust diff remains a
  measurement, not a ranking metric.
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
