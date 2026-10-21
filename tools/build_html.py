"""Render index.html from tools/template.html + tools/data.json."""
import hashlib
import html as _html
import json
import os
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import card  # noqa: E402

DATA = json.loads((ROOT / 'tools/data.json').read_text())
META = json.loads((ROOT / 'tools/meta.json').read_text())
N = len(DATA)
MISSING = []

# ---- asset checks ----------------------------------------------------------
THUMBS = ('', '320/', 'avif/', 'avif/320/', 'avif/1024/')
for d in DATA:
    checks = {
        'sheet crop': ROOT / f"images/{d['img']}.webp",
        'official render': ROOT / f"character_images/{d['official']}.webp",
    }
    for prefix in THUMBS:
        ext = 'avif' if 'avif' in prefix else 'webp'
        checks[f'thumb {prefix or "640"}'] = ROOT / f"character_images/thumbs/{prefix}{d['official']}.{ext}"
    if d.get('skin'):
        checks['outfit render'] = ROOT / f"character_images/{d['skin']['official']}.webp"
    for label, path in checks.items():
        if not path.exists():
            MISSING.append(f"{d['display']}: {label} ({path.relative_to(ROOT)})")
    for it in d['outfits']:
        p = ROOT / 'character_images' / it['file']
        if not p.exists():
            MISSING.append(f"{d['display']}: outfit art ({p.relative_to(ROOT)})")
if MISSING:
    raise SystemExit('missing artwork (run tools/make_thumbs.py):\n  ' + '\n  '.join(MISSING))
print(f'artwork: all {N} entries and their responsive variants present')

# ---- exact intrinsic widths for srcset ------------------------------------
_WIDTH = {}
def intrinsic_width(rel):
    if rel not in _WIDTH:
        with Image.open(ROOT / rel) as im:
            _WIDTH[rel] = im.size[0]
    return _WIDTH[rel]

for d in DATA:
    o = d['official']
    d['w320'] = intrinsic_width(f'character_images/thumbs/320/{o}.webp')
    d['w640'] = intrinsic_width(f'character_images/thumbs/{o}.webp')
    d['w1024'] = intrinsic_width(f'character_images/thumbs/avif/1024/{o}.avif')
    d['wfull'] = intrinsic_width(f'character_images/{o}.webp')

DESC = (f"Measurements for all {N} female Zenless Zone Zero agents: height, bust, under-bust, waist, "
        "hips and thigh circumference in cm and inches, with waist-to-hip proportions, silhouette "
        "reads and UK, US and EU bra sizes.")
TITLE = f"ZZZ Female Measurements — all {N} agents, cm / inches"
PERMALINK = META['repo']

# ---- structured data -------------------------------------------------------
jsonld = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "WebSite",
            "@id": "__SITE_URL__#website",
            "url": "__SITE_URL__",
            "name": META['title'],
            "description": DESC,
            "inLanguage": "en",
            "publisher": {"@type": "Organization", "name": META['source']},
        },
        {
            "@type": "WebPage",
            "@id": "__SITE_URL__#page",
            "url": "__SITE_URL__",
            "name": TITLE,
            "isPartOf": {"@id": "__SITE_URL__#website"},
            "dateModified": META['data_updated'],
            "inLanguage": "en",
        },
        {
            "@type": "Dataset",
            "@id": "__SITE_URL__#measurements",
            "name": f"Zenless Zone Zero female character measurements ({N} agents)",
            "description": DESC,
            "url": "__SITE_URL__",
            "creator": {"@type": "Organization", "name": META['source']},
            "inLanguage": "en",
            "isAccessibleForFree": True,
            "dateModified": META['data_updated'],
            "keywords": ["Zenless Zone Zero", "female character measurements", "bust", "under-bust",
                         "waist", "hips", "thigh circumference", "height", "bra size", "UK US EU sizing"],
            "variableMeasured": [
                {"@type": "PropertyValue", "name": name, "unitText": "cm"}
                for name in META['measurement_fields']
            ],
            "measurementTechnique": ("Curves measured around the official 3D models; charted heights "
                                     "come from official listings and may include ears, footwear or accessories."),
            "size": {"@type": "QuantitativeValue", "value": N, "unitText": "characters"},
            "about": {"@type": "VideoGame", "name": "Zenless Zone Zero",
                      "publisher": {"@type": "Organization", "name": "HoYoverse"}},
            "isBasedOn": "https://modelmetrics.net",
            "citation": META['source'],
            "copyrightNotice": META['rights'],
            "distribution": [
                {"@type": "DataDownload", "encodingFormat": "application/json",
                 "contentUrl": "__SITE_URL__data/measurements.json"},
                {"@type": "DataDownload", "encodingFormat": "text/csv",
                 "contentUrl": "__SITE_URL__data/measurements.csv"},
            ],
        },
        {
            "@type": "ItemList",
            "@id": "__SITE_URL__#roster",
            "name": "Female agent roster",
            "numberOfItems": N,
            "itemListOrder": "https://schema.org/ItemListOrderAscending",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": d['display'],
                 "url": f"__SITE_URL__characters/{d['slug']}/",
                 "description": (d['desc_cm'] or '')[:180]}
                for i, d in enumerate(sorted(DATA, key=lambda x: x['display']))
            ],
        },
    ],
}
jsonld_txt = json.dumps(jsonld, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

# ---- no-JS / crawler fallback table ---------------------------------------
rows = []
for d in sorted(DATA, key=lambda x: x['display']):
    def v(k, dec=1):
        x = d.get(k)
        return '—' if x is None else f"{x:.{dec}f}"
    rows.append("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
        _html.escape(d['display']), d['ftin'] or '—', v('stature_cm', 0), v('bust_cm'), v('band_cm'),
        v('waist_cm'), v('hip_cm'), v('thigh_cm')))
noscript = f'''<div class="nsTable">
<h2>ZZZ female measurements: all {N} agents</h2>
<p>Zenless Zone Zero female character measurements in centimetres (1 cm = 0.394 in). The interactive chart on this page also shows imperial units, UK / US / EU bra sizing, proportions and silhouette reads for every agent. Enable JavaScript for filtering, sorting and the detail view.</p>
<table><thead><tr><th scope="col">Agent</th><th scope="col">Height (ft/in)</th><th scope="col">Stature (cm)</th><th scope="col">Bust (cm)</th><th scope="col">Under-bust (cm)</th><th scope="col">Waist (cm)</th><th scope="col">Hips (cm)</th><th scope="col">Thigh (cm)</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</div>'''

# bump the share-card URL whenever the image changes, so scrapers refetch it
og = ROOT / 'og.png'
ogv = hashlib.md5(og.read_bytes()).hexdigest()[:8] if og.exists() else '1'

# initial card order mirrors SORTS["bust-desc"] in template.html
initial = sorted(DATA, key=lambda d: (d['diff_cm'] if d['diff_cm'] is not None else -99), reverse=True)
cards_html = card.render_cards(initial)

tpl = (ROOT / 'tools/template.html').read_text()
card_tmpl_js = json.dumps(card.TEMPLATE, ensure_ascii=False).replace('</', '<\\/')
# the page only needs the fields the client renders; provenance and class
# internals stay in tools/data.json and the exported dataset
JS_SKIP = {'source_url', 'source_file', 'cm_eff', 'waist_level', 'hip_level', 'thigh_level',
           'confidence', 'confidence_note'}
def slim(d):
    out = {k: v for k, v in d.items() if k not in JS_SKIP}
    if out.get('skin'):
        out['skin'] = {k: v for k, v in out['skin'].items() if k not in JS_SKIP}
    return out
data_js = json.dumps([slim(d) for d in DATA], ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
html = (tpl
        .replace('/*__DATA__*/[]', data_js)
        .replace('/*__CARD_TMPL__*/""', card_tmpl_js)
        .replace('/*__JSONLD__*/', jsonld_txt)
        .replace('/*__NOSCRIPT__*/', noscript)
        .replace('/*__CARDS__*/', cards_html)
        .replace('/*__COUNT__*/', str(N))
        .replace('__DESC__', _html.escape(DESC, quote=True))
        .replace('__TITLE__', _html.escape(TITLE, quote=True))
        .replace('__DATA_UPDATED__', META['data_updated'])
        .replace('__SCHEMA_VERSION__', str(META['schema_version']))
        .replace('__REPO__', PERMALINK)
        .replace('__OGV__', ogv)
        .replace('__SITE_URL__', 'https://nullhollow.github.io/zzz-measurements/'))  # pack_site.py swaps in the real URL
(ROOT / 'index.html').write_text(html)
print('index.html written:', round(len(html) / 1024, 1), 'KB,', N, 'entries')
leftovers = [t for t in ('/*__DATA__*/', '/*__CARD_TMPL__*/', '/*__JSONLD__*/', '/*__NOSCRIPT__*/',
                         '/*__CARDS__*/', '/*__COUNT__*/', '__DESC__', '__TITLE__',
                         '__DATA_UPDATED__', '__SCHEMA_VERSION__', '__REPO__', '__OGV__')
             if t in html]
if leftovers:
    raise SystemExit('unreplaced tokens: ' + ', '.join(leftovers))
