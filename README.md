# ZZZ Female Measurements

A static, self-contained reference for the female *Zenless Zone Zero* roster: height,
bust, under-bust, waist, hips and thigh circumference in cm and inches, plus
proportions and UK/US/EU bra sizing.

Live site: <https://nullhollow.github.io/zzz-measurements/>

## What is in here

```
index.html                 generated roster page
tools.html                 generated comparison/exploration page
favourites.html            generated personal tier-ranking page and JPG export
measurements3.3.csv        source sheet (the only hand-edited data)
character_images/          54 official portraits + 26 outfit renders + thumbs/
images/                    49 sheet crops
fonts/                     ZZZ Hongmeng subset + Anton / Chakra / Inter / Noto fallbacks
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
3. `build_html.py` — `index.html`, `tools.html` and `favourites.html`, localized data and JSON-LD
4. `build_pages.py` — 50 character pages × 3 languages, 3 methodology/FAQ pages, dataset exports, offline page
5. crawler files, PWA manifest, service worker, link check

Optional asset steps (already committed):

```bash
python3 tools/refetch_images.py   # official renders at 1280 px tall (needs network)
python3 tools/make_thumbs.py      # 320/640/1024/1280 WebP + AVIF responsive set
python3 tools/make_favicon.py     # SVG, ICO, PWA + maskable icons
python3 tools/make_og.py          # social card (needs Chrome)
```

## Visual reference tools

Tools now includes a Height lineup and an illustrated Measurement guide. The lineup
uses effective-height bars, with ruler, 200 cm doorway and personal-height
references. Select up to eight agents and arrange them by height, faction or manual
order. Portraits identify agents and are deliberately not calibrated by their image
bounds. Selection, ordering and references travel in shared URL state.

The guide uses a schematic illustration and numbered controls, with text alternatives
on methodology pages. It explains measurement concepts rather than claiming to
reproduce the source's measuring process. The guide illustration was generated for
this site; character art remains attributed to HoYoverse.

Profiles include separately sourced agent facts and official profile links. Game
metadata lives in `tools/reference.json`; localized category names live in
`tools/reference_labels.json`. Missing gameplay fields are left unknown. Debut
versions are determined from the agent release date and cited version start dates.
These facts never enter measurement calculations or rankings.

The original artwork viewer works on profiles and inside the chart. It supports fit,
true 100% pixel view, zoom/pan, keyboard navigation, background choices and downloads.
`originals/` contains 76 unmodified source PNGs, approximately 112 MiB.
They load only when the viewer opens and are not part of the service-worker install
cache. SHA-256, dimensions, byte sizes and source URLs are recorded in the reference
manifest. Some source PNGs include backgrounds that are absent from curated previews.

To deliberately refresh the external references and originals, run
`python3 tools/fetch_reference.py`, review the changes, rebuild CJK font subsets if
needed, then pack and validate. The fetcher is never run by CI. It requests
`format=original`, verifies PNG format and source dimensions, and never resizes or
re-encodes the downloaded files. Original source quality varies; files are not
upscaled or reconstructed from the existing previews.

Owner-supplied originals retain their uploaded bytes and an `owner-upload` manifest
entry; the fetcher verifies their hashes and preserves them during a refresh.
Eldreda Sunbringer currently has official artwork only. Her `sheet_available: false`
record uses that optimized artwork even when Sheet mode is selected.

Shared implementation: `tools/visual_tools.js`, `tools/visual_tools.css`,
`tools/artwork.js` and `tools/reference.py`. Run `python3 tools/test_reference.py`
to verify original integrity, metadata coverage, static output and lineup behavior.

## Measurement settings

The Settings window groups cm/inches, UK/US/EU bra sizing, language and theme on
both interactive pages. It is also available from character and comparison dialogs. Preferences
are saved locally and included in shared URLs (`unit` and `cups`). The selected
cup system uses the corresponding source field without converting or inventing
sizes. Cards, tables, podium values, descriptions, comparisons, distributions and
the game follow that display preference. Rankings and UK cup filters keep their
original rules. Static profiles and exports retain all source sizing systems.

Theme defaults to **System**, following the browser's appearance and updating
when it changes. Saved **Light** or **Dark** choices override that default;
shared URLs preserve the preference as `th=system`, `th=light` or `th=dark`.
Profiles, methodology and fallback pages use the same palette and saved choice.
Without JavaScript, pages follow the browser through CSS. The shared palette and
early preference script live in `tools/theme.css` and `tools/theme.js`;
`tools/theme.py` inlines them during generation.

## Roster browsing

Search and filters appear before the collapsible Leaders section. Active filters
can be removed individually or cleared together. The roster table offers a column
picker, a pinned name column and one selected unit. Table sorting and columns are
shared as `ts=column:direction` and `cols=...`, and restore on reload and Back/Forward.
Missing values stay last in either direction. These controls live in `tools/roster.js`,
inlined by the HTML generator. Measurement help is available from
the toolbar and comparison row labels. Comparison dialogs can add or replace
characters directly, keeping the four-entry limit and existing winner rules.

## Compare

Every card has a labelled **Compare** pill inside its artwork. Pick 2–4 agents; the
tray explains the next step and enables **Compare** at two picks. The comparison
table uses larger values, shows direction arrows, and highlights the winner in
yellow for height, cup, waist (smaller), hips and thighs. Default sorting and the largest-cup podium use UK cup size. Confidence
badges are no longer shown; the raw field remains in the dataset exports.

The comparison dialog offers **Raw measurements** and **Height-adjusted** modes.
Height-adjusted mode shows bust, under-bust, waist, hips and thighs as
`circumference_cm / stature_cm × 100`, displayed as percentages to one decimal
place. Matching displayed values share the highlight, and missing measurements
stay unranked. Height, bra sizes and classes retain their values. This mode is
separate from roster rankings, filters, percentiles and podiums. The selected
mode is included in shared URLs as `basis=height`.

## Exploration tools

Comparisons show the selected unit only. The default rows focus on measurements
and ratios; source sizes, classes and profile commentary remain available under
**Rows and order**. Save up to 20 named comparison sets locally, including selected
rows/order, reference, raw/adjusted/scaled basis, target height, units and cup
system. The Saved comparisons window can reopen a group after navigation or reload,
and supports replacing a name, removal and undo. Local storage failures leave the
current comparison intact. CSV exports contain the visible canonical-character
rows and displayed reference differences, with English field names and explicit
units/basis. Temporary sandbox references and their reference differences are
omitted from exports. CSV text is quoted and protected against formula injection.

The comparison dialog also offers **Same height**: `circumference_cm / stature_cm × reference_height_cm`
(default 160 cm). This assumes uniform scaling and produces hypothetical equivalents,
not new measurements. Height itself retains its measured value. Choose visible rows,
reorder them, and select a reference character for signed differences. Adjusted
circumferences use percentage-point differences; raw and scaled differences use the
selected unit. Missing measurements stay unknown.

The separate **Tools** page (`tools.html`), linked from the page navigation, contains:

- **Distribution**: source cup-letter counts in the selected sizing system, using the
  existing UK order or grouped source-letter order for US/EU, and retaining
  full band-and-cup sizes in the value table. Equal cup letters do
  not imply equal volume. Numeric metrics use equal-width histograms and medians
  of the filtered roster. Comparison selections appear as markers; missing
  values and sandbox cup sizes are omitted. The Band × cup view counts supplied
  band-and-cup labels in a scrollable matrix. Select a bar or occupied matrix cell
  to view its characters and add them to comparison. Numeric bar selection uses
  the same histogram boundaries, including the maximum in the final bin.
- **Find similar figures**: raw or height-adjusted matching with per-metric weights
  from 0 to 100. Distances use the full canonical roster range for each metric,
  skip missing pairs, and renormalize the remaining weights. Default weights and
  static-profile matches retain the original rule. Zero shared weight gives no result.
  Type a name to select the reference. Expand a match to inspect each measured
  difference and its contribution to the total distance; this is not a probability.
- **Higher or Lower**: canonical character pairs with higher, lower and equal
  answers. Numeric rounds use displayed one-decimal values in the selected unit.
  Cup rounds use the existing UK letter-first, band-second score in every display
  system, including equal scores. After a guess, UK values appear as references
  when US/EU display labels are selected. Cup rounds are unaffected by length units
  or height adjustment. Scores stay in the page.
- **Figure sandbox**: fictional cm inputs that can join a comparison or serve as the
  matching reference. They never enter the roster, classes, percentiles, rankings,
  game rounds or exports. Optional blank circumferences stay unknown. Shared links
  include the fictional values and validated tool settings in the URL fragment.

`tools/analysis_math.py` and `tools/analysis.js` implement the same exploration math.
`tools/explorer.js`, `tools/settings.js` and `tools/explorer.css` are inlined by `build_html.py`; the shared
EN/JA/ZH copy in `tools/explorer_i18n.json` supplies both the interactive UI and static
methodology. The public measurement schema is unchanged. Old `#view=distribution`, `matches`,
`game` and `sandbox` links redirect to the Tools page with their state intact.
Tool section changes create browser-history entries; field edits replace the
current entry. A shared sticky container keeps tool navigation above its controls.
Navigation carries filters, comparison selections, units, theme and language between
pages. The packed site contains 50 entries, 150 profiles and 732 files (about 141.0 MB).

## Favourites

`favourites.html` ranks the current roster in ordered SSS, S, A, B, C, D and E
tiers. Tier labels and number badges share the same colours: amber-gold, gold,
purple, blue, silver, grey and dark grey. Numbers can run across the board or
restart within each tier. Drag agents to insert before another portrait or append
to a tier; tapping an agent and selecting its tier works on phones. Earlier/later
controls adjust its position. Empty tiers remain available while editing.

Drafts and named boards are saved on the current device. Undo restores board
changes and removed saved boards. Copy link includes the title, author, ordered
slugs and numbering mode; a shared board takes precedence over the local draft.
Personal rankings never change measurement data or comparison state.

Export image creates a 2160 px wide JPG (90% quality) with content-driven height, localized
names, the optional title/author, tier colours and artwork credit. Preview and
Save JPG use the same generated image. Empty tiers and unranked entries are
omitted. English names split within a word receive a hyphen. The canvas renders
at twice the layout resolution, using the existing optimized official
portraits and bundled fonts.

Sources: `tools/favourites.tmpl.html`, `tools/favourites.js`,
`tools/favourites.css` and `tools/favourites_i18n.json`. The HTML generator reuses
the site's head, navigation and hero. Run `python3 tools/test_favourites.py` for
state transitions, URL round trips, locale coverage and build integration.

Run the regression and Python/JavaScript parity suite with Node.js available:

```bash
python3 tools/test_analysis.py
python3 tools/test_roster.py
python3 tools/test_theme.py
```

## Live calculations

The derived numbers used by the interactive chart are computed in the browser
from the raw centimetre values on every load: bust difference, all proportions,
roster percentiles, cup/height/waist/hip/thigh classes, shape, the podium, the
highlights and the comparison winners. There are no handwritten podium picks or
rank tables to update when a character is added.

Static profile pages and the JSON/CSV exports are generated by the build so they
also work without JavaScript. Adding a character therefore means adding a row to
`measurements3.3.csv`, adding the artwork, and running the normal pack/validate
commands; the build and the live page both recalculate from that row.

## Languages

The language switch in Settings changes the interface, character names and the
figure-read/profile copy between English, Japanese and Simplified Chinese. Names are
the official localized names taken from the HoYoverse character pages (recorded in
`tools/localized_names.json`), not literal translations. The static profiles also
exist as crawlable pages at `/ja/characters/<slug>.html` and
`/zh/characters/<slug>.html`, with matching localized methodology pages and
`hreflang` alternates. The source/export fields stay in English.

## Typography

The primary UI face is a subset of **印品鸿蒙体 / inpin hongmengti**, the Chinese
face used by ZZZ's UI. It was subset from the site owner's installed `ZZZ.ttf`
to the characters on this site, so it covers the English labels, Chinese copy
and most Japanese kana/kanji in one family.

Two notes:

- 印品鸿蒙体 is a commercial typeface. The subset is included at the owner's
  direction; public web embedding/redistribution needs a licence from
  [inpin](https://inpin.cn/). See `fonts/LICENSE-ZZZ-Hongmeng.txt`.
- The available GB2312 cut does not contain 58 Japanese characters used by the
  profiles, including `見`, `長`, `開`, `時` and `・`. Those glyphs fall back to a
  weight-matched **Noto Sans JP 900** subset, with Noto Sans JP and Dela Gothic
  One as further fallbacks. Chinese display/body fallbacks use the Noto Sans SC
  variable and 900 subsets. This avoids tofu while keeping the ZZZ face wherever
  it has a glyph.

Rebuild the fallback font subsets with `tools/update_cjk_fonts.py` (requires
`fonttools[woff]` from `requirements.txt`). It subsets full OFL source files in memory
and preserves the existing font families and licences. Rebuild the
primary ZZZ subset from a licensed local source with:

```bash
python3 tools/pack_site.py
python3 tools/subset_zzz_font.py --font /path/to/ZZZ.ttf
python3 tools/pack_site.py
```

## Payload

Cards, the table and the podium use a `<picture>` set: AVIF 320/640/full-1024
with WebP fallbacks and per-card `sizes`. 1x desktop cards get the 640 set at
roughly 1:1; 2x desktop and phone cards pick the full 1024 render instead of
upscaling the 640 thumb. A 2x phone loads ~430 KB of artwork for the first screen
(podium plus visible cards), and the rest lazy-loads. Character-page heroes use a 1280 px AVIF/source set, the gallery uses 640 px
thumbs and the detail view uses the 1280 px source render. Outfit art with an
AVIF source serves AVIF first and WebP as the fallback. The HTML is ~84 KB
gzipped locally (GitHub Pages serves it compressed), and the page keeps its 50
static cards.

## Data model

One row per character in `measurements3.3.csv`. `tools/meta.json` documents every
derived field, carries the schema version and the data date.

Eldreda Sunbringer is a separate project estimate based on the owner's assumptions
and other sources, not modelmetrics.net. Her effective height is 180.37 cm;
193.37 cm includes horns. UK 23HH is the supplied source label. US ≈23L and EU
≈50L are estimates: the nonstandard UK band prevents an exact standard conversion,
and the EU estimate rounds the theoretical band upward. `record_sources` in
`tools/meta.json` supplies per-record provenance, source precision and missing-sheet
metadata. Exports preserve the labels and identify the estimated sizing systems.

* **Standard model is canonical**, except **Jane Doe**: her canonical entry uses the
  measured Nocturne of Light outfit. Other measured outfits are separate `skin`
  records; art-only outfits never touch a number.
* **`stature_cm`** is the comparison height shown in the UI as **Height**. It equals the charted height unless
  the chart counts an appendage (Miyabi's ears), where it uses head height.
  The 3.3 sheet dropped the optional effective-height column, so Miyabi's 152.1 cm
  head height is kept in `STATURE_OVERRIDE` in `tools/build_data.py`.
* **Shape** uses bust, waist and hips: Hourglass needs bust/waist and hip/waist ≥1.45
  with bust and hips within 15%; Straight is flare <1.30 or a bust–hip mismatch >25%;
  the rest is Balanced. The sharpest-hourglass score is flare × bust–hip balance.
* **Cup ranking** follows UK cup progression: D < DD < E < F < FF < G < GG < H < HH < J < JJ.
  Band breaks ties within the same cup. Shared Python/JavaScript scoring in
  `analysis_math.py` / `analysis.js` supplies the roster, podium, comparisons,
  distributions and game. Cup summaries use counts and the most common category;
  numerical averages and medians apply only to measurement values.
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
