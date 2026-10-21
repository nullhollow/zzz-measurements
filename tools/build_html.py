import hashlib, json, os, html as _html
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
data = json.load(open(ROOT/'tools/data.json'))

# verify the artwork the page asks for is on disk
missing = [d['img'] for d in data if not os.path.exists(f"{ROOT}/images/{d['img']}.webp")]
print('missing sheet crops:', missing if missing else 'none')
subs = [s for d in data for s in (d.get('std'), d.get('skin')) if s]
mi = [r['official'] for r in data + subs if not os.path.exists(f"{ROOT}/character_images/{r['official']}.webp")]
print('missing official portraits:', mi if mi else 'none')

DESC = ("Measurements for all 48 female Zenless Zone Zero agents: height, bust, under-bust, waist, "
        "hips and thigh circumference in cm and inches, with waist-to-hip proportions, silhouette "
        "reads and UK, US and EU bra sizes.")

# ---- structured data -------------------------------------------------------
jsonld = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "WebSite",
            "@id": "__SITE_URL__#website",
            "url": "__SITE_URL__",
            "name": "ZZZ Female Measurements",
            "description": DESC,
            "inLanguage": "en",
            "publisher": {"@type": "Organization", "name": "modelmetrics.net"},
        },
        {
            "@type": "Dataset",
            "@id": "__SITE_URL__#measurements",
            "name": "Zenless Zone Zero female character measurements",
            "description": DESC,
            "url": "__SITE_URL__",
            "creator": {"@type": "Organization", "name": "modelmetrics.net"},
            "inLanguage": "en",
            "isAccessibleForFree": True,
            "keywords": ["Zenless Zone Zero", "female character measurements", "bust", "under-bust",
                         "waist", "hips", "thigh circumference", "height", "bra size", "UK US EU sizing"],
            "variableMeasured": ["height", "bust", "under-bust", "waist", "hip", "thigh circumference"],
            "size": {"@type": "QuantitativeValue", "value": len(data), "unitText": "characters"},
            "about": {"@type": "VideoGame", "name": "Zenless Zone Zero",
                      "publisher": {"@type": "Organization", "name": "HoYoverse"}},
            "citation": "modelmetrics.net",
        },
        {
            "@type": "ItemList",
            "@id": "__SITE_URL__#roster",
            "name": "Female agent roster",
            "numberOfItems": len(data),
            "itemListOrder": "https://schema.org/ItemListOrderAscending",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": d['display'],
                 "description": (d['desc_cm'] or '')[:180]}
                for i, d in enumerate(sorted(data, key=lambda x: x['display']))
            ],
        },
    ],
}
jsonld_txt = json.dumps(jsonld, ensure_ascii=False, separators=(',', ':'))

# ---- no-JS / crawler fallback table ---------------------------------------
rows = []
for d in sorted(data, key=lambda x: x['display']):
    def v(k, dec=1):
        x = d.get(k)
        return '—' if x is None else f"{x:.{dec}f}"
    rows.append("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
        _html.escape(d['display']), d['ftin'] or '—', v('bust_cm'), v('band_cm'), v('waist_cm'),
        v('hip_cm'), v('thigh_cm')))
noscript = f'''<div class="nsTable">
<h2>ZZZ female measurements: all {len(data)} agents</h2>
<p>Zenless Zone Zero female character measurements in centimetres (1 cm = 0.394 in). The interactive chart on this page also shows imperial units, UK / US / EU bra sizing, proportions and silhouette reads for every agent. Enable JavaScript for filtering, sorting and the detail view.</p>
<table><thead><tr><th>Agent</th><th>Height (ft/in)</th><th>Bust (cm)</th><th>Under-bust (cm)</th><th>Waist (cm)</th><th>Hips (cm)</th><th>Thigh (cm)</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</div>'''

# bump the share-card URL whenever the image changes, so scrapers refetch it
og = ROOT/'og.png'
ogv = hashlib.md5(og.read_bytes()).hexdigest()[:8] if og.exists() else '1'

tpl = open(ROOT/'tools/template.html').read()
html = (tpl
        .replace('/*__DATA__*/[]', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
        .replace('/*__JSONLD__*/', jsonld_txt)
        .replace('/*__NOSCRIPT__*/', noscript)
        .replace('/*__COUNT__*/', str(len(data)))
        .replace('__OGV__', ogv)
        .replace('__SITE_URL__', 'https://nullhollow.github.io/zzz-measurements/'))   # pack_site.py swaps in the real URL
open(ROOT/'index.html', 'w').write(html)
print('index.html written:', round(len(html)/1024, 1), 'KB,', len(data), 'entries')
leftovers = [t for t in ('/*__DATA__*/', '/*__JSONLD__*/', '/*__NOSCRIPT__*/', '/*__COUNT__*/') if t in html]
print('unreplaced tokens:', leftovers if leftovers else 'none')
