"""Render index.html from tools/template.html + tools/data.json."""
import hashlib
import html as _html
import json
import os
import re
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import card  # noqa: E402
from theme import THEME_JS, adaptive_css
from profile_text import profile_summary  # noqa: E402

DATA = json.loads((ROOT / 'tools/data.json').read_text())
META = json.loads((ROOT / 'tools/meta.json').read_text())
N = len(DATA)
MISSING = []

# ---- asset checks ----------------------------------------------------------
THUMBS = ('', '320/', 'avif/', 'avif/320/', 'avif/1024/', 'avif/1280/')
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
        if it.get('avif') and not (ROOT / 'character_images' / it['avif']).exists():
            MISSING.append(f"{d['display']}: outfit AVIF ({it['avif']})")
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
        "hips and thigh circumference in cm and inches, with waist-to-hip proportions "
        "and UK, US and EU bra sizes.")
TITLE = "ZZZ Measurements"
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
                 "url": f"__SITE_URL__characters/{d['slug']}.html",
                 "description": profile_summary(d)}
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
    height = f"{v('stature_cm', 1)} cm · {d['ftin_stature']}"
    if d['stature_basis'] == 'head':
        height += f" ({v('cm', 0)} charted)"
    rows.append("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
        _html.escape(d['display']), _html.escape(height), v('bust_cm'), v('band_cm'),
        v('waist_cm'), v('hip_cm'), v('thigh_cm')))
noscript = f'''<div class="nsTable">
<h2>ZZZ female measurements: all {N} agents</h2>
<p>Zenless Zone Zero female character measurements in centimetres (1 cm = 0.394 in). The interactive chart on this page also shows imperial units, UK / US / EU bra sizing and proportions for every agent. Enable JavaScript for filtering, sorting and the detail view.</p>
<table><thead><tr><th scope="col">Agent</th><th scope="col">Height</th><th scope="col">Bust (cm)</th><th scope="col">Under-bust (cm)</th><th scope="col">Waist (cm)</th><th scope="col">Hips (cm)</th><th scope="col">Thigh (cm)</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</div>'''

# bump the share-card URL whenever the image changes, so scrapers refetch it
og = ROOT / 'og.png'
ogv = hashlib.md5(og.read_bytes()).hexdigest()[:8] if og.exists() else '1'

# initial card order mirrors SORTS["cup-desc"] in template.html
CUP_BASE = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
            'J': 9, 'K': 10, 'L': 11, 'M': 12, 'N': 13}
def cup_score(d):
    m = re.match(r'^(\d+)\s*([A-Za-z]+)$', d.get('uk') or '')
    if not m:
        return -1
    cup = m.group(2).upper()
    base = CUP_BASE.get(cup[0], 0)
    if not base:
        return -1
    single = 1 if len(cup) == 1 else 0
    return base * 10000 + single * 1000 + int(m.group(1))
initial = sorted(DATA, key=cup_score, reverse=True)
cards_html = card.render_cards(initial)

tpl = (ROOT / 'tools/template.html').read_text()
card_tmpl_js = json.dumps(card.TEMPLATE, ensure_ascii=False).replace('</', '<\\/')
# the page only needs the fields the client renders; provenance and class
# internals stay in tools/data.json and the exported dataset
JS_SKIP = {'source_url', 'source_file', 'cm_eff', 'waist_level', 'hip_level', 'thigh_level',
           'confidence', 'confidence_note', 'height_adjusted'}
def slim(d):
    out = {k: v for k, v in d.items() if k not in JS_SKIP}
    if out.get('skin'):
        out['skin'] = {k: v for k, v in out['skin'].items() if k not in JS_SKIP}
    return out
data_js = json.dumps([slim(d) for d in DATA], ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
explorer_i18n = json.loads((ROOT / 'tools/explorer_i18n.json').read_text())
for lang, strings in explorer_i18n.items():
    copy = ',\n    '.join(f'{key}: {json.dumps(value, ensure_ascii=False)}' for key, value in strings.items()) + ','
    tpl = tpl.replace(f'/*__EXPLORER_I18N_{lang.upper()}__*/', copy)
for token, source in (('ANALYSIS_JS', 'analysis.js'), ('EXPLORER_JS', 'explorer.js'), ('SETTINGS_JS', 'settings.js'), ('ROSTER_JS', 'roster.js'), ('VISUAL_JS','visual_tools.js'), ('ARTWORK_JS','artwork.js'), ('VISUAL_CSS','visual_tools.css'), ('EXPLORER_CSS', 'explorer.css')):
    tpl = tpl.replace(f'/*__{token}__*/', (ROOT / 'tools' / source).read_text())
tpl=tpl.replace('/*__REFERENCE__*/{}',json.dumps(json.loads((ROOT/'tools/reference.json').read_text()),ensure_ascii=False).replace('</','<\\/')).replace('/*__REFERENCE_LABELS__*/{}',json.dumps(json.loads((ROOT/'tools/reference_labels.json').read_text()),ensure_ascii=False).replace('</','<\\/'))
tpl = tpl.replace('/*__THEME_JS__*/', THEME_JS)
tpl = re.sub(r'<style>(.*?)</style>', lambda m: '<style>' + adaptive_css(m[1]) + '</style>', tpl, flags=re.S)

def render_interactive(tools=False):
    page = tpl
    title = TITLE
    description = explorer_i18n['en']['toolsDescription'] if tools else DESC
    structured = jsonld_txt
    nav = ''
    settings_button = '<button class="btn" id="settingsBtn" data-open-settings data-i18n="settingsButton">Settings</button>'
    if tools:
        structured = json.dumps({'@context': 'https://schema.org', '@type': 'WebPage',
                                 'url': '__SITE_URL__tools.html', 'name': title,
                                 'description': description, 'inLanguage': ['en', 'ja', 'zh'],
                                 'isPartOf': {'@id': '__SITE_URL__#website'}}, ensure_ascii=False)
        page = re.sub(r'<header class="hero">.*?<div class="film".*?</div>',
                      '<header class="toolsheader"><h1 data-i18n="toolsTitle">Comparison tools</h1></header>', page, flags=re.S)
        page = page.replace('data-i18n="skip">Skip to the roster', 'data-i18n="skipTools">Skip to the tools')
        nav = '<div class="tools-shell"><nav class="tooltabs" id="toolsNav" aria-label="Tools">' + ''.join(
            f'<a href="tools.html#view={key}" data-tool-link="{key}" data-i18n="{key}">{_html.escape(explorer_i18n["en"][key])}</a>'
            for key in ('distribution', 'matches', 'game', 'sandbox', 'lineup', 'guide')) + settings_button + '</nav>'
        picker='<select id="toolSelect" class="tool-picker" aria-label="Tools">'+''.join(f'<option value="{key}" data-i18n="{key}">{_html.escape(explorer_i18n["en"][key])}</option>' for key in ('distribution','matches','game','sandbox','lineup','guide'))+'</select>'
        nav=nav.replace('aria-label="Tools">','aria-label="Tools">'+picker,1)
        page = page.replace('  <div class="wrap">', '</div>\n  <div class="wrap">', 1)
    fallback = ('<p data-i18n="toolsNoScript">' + _html.escape(explorer_i18n['en']['toolsNoScript']) +
                '</p><a href="index.html">Measurements</a>') if tools else noscript
    result = (page
        .replace('/*__DATA__*/[]', data_js)
        .replace('/*__CARD_TMPL__*/""', card_tmpl_js)
        .replace('/*__JSONLD__*/', structured)
        .replace('/*__NOSCRIPT__*/', fallback)
        .replace('/*__CARDS__*/', '' if tools else cards_html)
        .replace('/*__COUNT__*/', str(N))
        .replace('/*__TOOLS_NAV__*/', nav)
        .replace('/*__SETTINGS_BUTTON__*/', '' if tools else settings_button)
        .replace('/*__ROSTER_CURRENT__*/', '' if tools else 'aria-current="page"')
        .replace('/*__TOOLS_CURRENT__*/', 'aria-current="page"' if tools else '')
        .replace('__PAGE__', 'tools' if tools else 'roster')
        .replace('__PAGE_URL__', '__SITE_URL__tools.html' if tools else '__SITE_URL__')
        .replace('__DESC__', _html.escape(description, quote=True))
        .replace('__TITLE__', _html.escape(title, quote=True))
        .replace('__DATA_UPDATED__', META['data_updated'])
        .replace('__SCHEMA_VERSION__', str(META['schema_version']))
        .replace('__REPO__', PERMALINK)
        .replace('__OGV__', ogv)
        .replace('__SITE_URL__', 'https://nullhollow.github.io/zzz-measurements/'))
    if tools:
        for tag in ('property="og:title"', 'name="twitter:title"'):
            result = result.replace(tag + ' content="ZZZ Female Measurements"', tag + ' content="Comparison tools · ZZZ Measurements"')
    leftovers = re.findall(r'/\*__[A-Z_]+__\*/|__[A-Z_]+__', result)
    if leftovers:
        raise SystemExit('unreplaced tokens: ' + ', '.join(sorted(set(leftovers))))
    return result


for filename, is_tools in (('index.html', False), ('tools.html', True)):
    html = render_interactive(is_tools)
    (ROOT / filename).write_text(html)
    print(filename + ' written:', round(len(html) / 1024, 1), 'KB,', N, 'entries')
