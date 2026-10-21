#!/usr/bin/env python3
"""Build the static pages and data exports that ship next to index.html.

    python3 tools/build_pages.py --out docs --site-url https://example.github.io/repo/

Outputs
    <out>/characters/<slug>.html    one crawlable page per agent
    <out>/methodology.html          method, classes, FAQ (FAQPage JSON-LD)
    <out>/data/measurements.json    versioned public dataset
    <out>/data/measurements.csv     flat export
    <out>/data/schema.json          JSON Schema for the export
    <out>/offline.html              service-worker fallback

The pages are plain HTML with inline CSS, so they work with JavaScript disabled
and give every character its own URL, title, description and structured data.
"""
import argparse
import csv
import html
import json
from pathlib import Path
from urllib.parse import quote
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
_WIDTH = {}


def intrinsic_width(rel):
    if rel not in _WIDTH:
        with Image.open(ROOT / rel) as im:
            _WIDTH[rel] = im.size[0]
    return _WIDTH[rel]


DATA = json.loads((ROOT / 'tools/data.json').read_text())
META = json.loads((ROOT / 'tools/meta.json').read_text())
SITE = 'https://nullhollow.github.io/zzz-measurements/'
N = len(DATA)
DISPLAY_SORTED = sorted(DATA, key=lambda d: d['display'].lower())


def esc(v):
    return html.escape('' if v is None else str(v), quote=True)


def fmt(v, dec=1):
    if v is None:
        return '—'
    s = f'{v:.{dec}f}'
    return s[:-2] if s.endswith('.0') else s


def pct(p):
    return 0 if p is None else round(p * 100)


def similar(d, key='slug'):
    keys = [('bust_cm', .25), ('waist_cm', .2), ('hip_cm', .2), ('thigh_cm', .15), ('stature_cm', .2)]
    spans = {}
    for k, _ in keys:
        vals = [x[k] for x in DATA if x[k] is not None]
        spans[k] = max(vals) - min(vals) or 1
    scored = []
    for x in DATA:
        if x['slug'] == d['slug']:
            continue
        total = weight = 0.0
        for k, w in keys:
            if d[k] is None or x[k] is None:
                continue
            total += w * abs(d[k] - x[k]) / spans[k]
            weight += w
        scored.append((total / weight if weight else 9, x))
    scored.sort(key=lambda kv: kv[0])
    return [x for _, x in scored[:3]]


CSS = '''
:root{--acid:#D8FA00;--hazard:#FFDE00;--signal:#FF5E41;--ink:#0B0B0C;--panel:#17171C;
  --line:#ffffff22;--dim:#A6A6AE;--dim2:#8A8A94;--bust:#FF5E41;--waist:#29D4FF;--hips:#D8FA00;
  --thighs:#FFDE00;--tan:#D3BC8E;--disp:'Anton','Arial Narrow',Impact,sans-serif;
  --num:'Chakra Petch',ui-monospace,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--ink);color:#fff;font:14px/1.6 Inter,system-ui,-apple-system,sans-serif;
  -webkit-font-smoothing:antialiased}
a{color:var(--acid)}
:focus-visible{outline:2px solid var(--acid);outline-offset:2px}
.top{max-width:1100px;margin:0 auto;padding:18px 20px;display:flex;justify-content:space-between;
  align-items:center;gap:12px;border-bottom:1px solid var(--line);font-size:11px;letter-spacing:.14em;
  text-transform:uppercase}
.top a{text-decoration:none;color:var(--dim)}
.top a:hover{color:var(--acid)}
.top b{font-family:var(--num);color:var(--acid)}
main{max-width:1100px;margin:0 auto;padding:22px 20px 60px}
.hero{display:grid;grid-template-columns:min(340px,38vw) 1fr;gap:26px;align-items:center;
  border-bottom:1px solid var(--line);padding-bottom:24px}
.hero img{width:100%;height:auto;border-radius:16px;border:1px solid var(--line);background:#101014}
.hero picture{display:block}
.eyebrow{margin:0 0 6px;font-family:var(--num);font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:var(--dim)}
h1{margin:0 0 10px;font-family:var(--disp);font-weight:400;font-size:clamp(36px,6vw,64px);line-height:.96;
  text-transform:uppercase}
.lead{margin:0 0 14px;color:#cfd0d6;font-size:13px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 14px;padding:0;list-style:none}
.chip{border:1px solid var(--line);border-radius:999px;padding:4px 10px;font-size:9.5px;
  letter-spacing:.13em;text-transform:uppercase;color:#e8e8ee}
.chip.bust{border-color:var(--bust);color:var(--bust)}.chip.waist{border-color:var(--waist);color:var(--waist)}
.chip.hips{border-color:var(--hips);color:var(--hips)}.chip.thighs{border-color:var(--thighs);color:var(--thighs)}
.chip.height{border-color:var(--tan);color:var(--tan)}
.meta{font-family:var(--num);font-size:12px;color:var(--dim);letter-spacing:.03em}
h2{margin:30px 0 10px;font-family:var(--disp);font-weight:400;font-size:22px;text-transform:uppercase}
h3{margin:18px 0 6px;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--acid)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
thead th{font-family:var(--num);font-size:10px;letter-spacing:.13em;text-transform:uppercase;color:var(--dim)}
tbody th{font-weight:500;color:var(--dim)}
td{font-family:var(--num);font-weight:600}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.card{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:14px}
.card p{margin:0;color:#cfd0d6;font-size:12.5px}
.bars{display:grid;gap:7px}
.prow{display:grid;grid-template-columns:64px 1fr 36px;gap:8px;align-items:center;font-size:10px;
  letter-spacing:.12em;text-transform:uppercase;color:var(--dim)}
.pbar{height:6px;background:#ffffff1a;border-radius:99px;overflow:hidden}
.pbar i{display:block;height:100%}
.prow b{font-family:var(--num);text-align:right;color:#e8e8ee;font-size:11px}
.note{border-left:2px solid var(--hazard);padding-left:10px;color:var(--dim);font-size:12px;margin-top:12px}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px}
.gallery figure{margin:0;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#101014}
.gallery img{width:100%;height:auto;display:block;background:#0c0c10}
.gallery figcaption{padding:8px 10px;font-size:10.5px;color:var(--dim)}
.gallery b{display:block;color:#fff;font-size:12px}
.nav{display:flex;justify-content:space-between;gap:12px;margin-top:34px;border-top:1px solid var(--line);padding-top:16px}
.nav a{text-decoration:none;font-family:var(--num);font-size:11px;letter-spacing:.1em;text-transform:uppercase}
.nav span{color:var(--dim)}
footer{max-width:1100px;margin:0 auto;padding:0 20px 60px;color:var(--dim2);font-size:11px;line-height:1.7}
footer a{color:var(--dim)}
footer .rule{border-top:1px solid var(--line);padding-top:14px}
.btn{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:8px 14px;
  font-family:var(--num);font-size:10px;letter-spacing:.13em;text-transform:uppercase;text-decoration:none;color:#fff}
.btn:hover{border-color:var(--acid);color:var(--acid)}
.btn.primary{background:var(--acid);border-color:var(--acid);color:#0b0b0c;font-weight:800}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.faq dt{font-weight:700;margin-top:14px;color:#fff}
.faq dd{margin:4px 0 0;color:#cfd0d6}
.small{font-size:11px;color:var(--dim2)}
@media(max-width:760px){.hero{grid-template-columns:1fr}.hero img{max-width:320px}
  .grid2{grid-template-columns:1fr}}
@media print{body{background:#fff;color:#000}.top,footer,.nav,.btns{display:none}
  .hero img{max-height:300px;width:auto}.card{background:#fff}.lead,.card p{color:#333}
  a{color:#000}}
'''


def head(title, desc, canonical, og_image, extra_ld='', prefix='../'):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="ZZZ Female Measurements">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og_image)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{esc(og_image)}">
<meta name="theme-color" content="#0B0B0C">
<link rel="icon" type="image/svg+xml" href="{prefix}favicon.svg">
<link rel="stylesheet" href="{prefix}fonts/fonts.css">
<style>{CSS}</style>
{extra_ld}
</head>
<body>
<header class="top"><a href="{prefix}">← ZZZ Measurements</a><span>Zenless Zone Zero · <b>{N}</b> agents</span></header>
'''


def footer(updated, prefix='../'):
    return f'''<footer><div class="rule">
<b>Source:</b> modelmetrics.net · <i>Zenless Zone Zero · Female Character Measurements</i>. Data updated <time datetime="{updated}">{updated}</time>.<br>
Official art via the ZZZ Fandom wiki, © HoYoverse (fair use). Auto-generated commentary is not in-game canon.<br>
<a href="{prefix}methodology.html">Methodology &amp; FAQ</a> · <a href="{prefix}data/measurements.json" download>Dataset (JSON)</a> ·
<a href="{prefix}data/measurements.csv" download>CSV</a> · <a href="{META['repo']}" rel="noopener">Source</a>
</div></footer>
</body>
</html>'''


def pct_bars(r):
    rows = [
        ('bust', r['p_bust_cm'], 'var(--bust)'),
        ('waist', r['p_waist_cm'], 'var(--waist)'),
        ('hips', r['p_hip_cm'], 'var(--hips)'),
        ('thigh', r['p_thigh_cm'], 'var(--thighs)'),
        ('stature', r['p_stature_cm'], 'var(--tan)'),
    ]
    return ''.join(
        f'<div class="prow"><span>{label}</span><div class="pbar"><i style="width:{pct(p)}%;background:{col}"></i></div><b>{pct(p) if p is not None else "—"}</b></div>'
        for label, p, col in rows)


def hero_picture(d):
    s = d['official']
    sizes = '(max-width:760px) 360px, 340px'
    height = round(440 / d['ar']) if d.get('ar') else 700
    w320 = intrinsic_width(f'character_images/thumbs/320/{s}.webp')
    w640 = intrinsic_width(f'character_images/thumbs/{s}.webp')
    w1024 = intrinsic_width(f'character_images/thumbs/avif/1024/{s}.avif')
    wfull = intrinsic_width(f'character_images/{s}.webp')
    avif = (f'../character_images/thumbs/avif/320/{s}.avif {w320}w, '
            f'../character_images/thumbs/avif/{s}.avif {w640}w, '
            f'../character_images/thumbs/avif/1024/{s}.avif {w1024}w')
    webp = (f'../character_images/thumbs/320/{s}.webp {w320}w, '
            f'../character_images/thumbs/{s}.webp {w640}w, '
            f'../character_images/{s}.webp {wfull}w')
    return (f'<picture>'
            f'<source type="image/avif" srcset="{avif}" sizes="{sizes}">'
            f'<img src="../character_images/thumbs/{s}.webp" srcset="{webp}" '
            f'sizes="{sizes}" width="440" height="{height}" alt="{esc(d["display"])} official portrait">'
            f'</picture>')


def character_page(d, prev_d, next_d):
    canonical = f"{SITE}characters/{d['slug']}.html"
    title = f"{d['display']} measurements — height, bust, waist, hips | ZZZ"
    desc = (d['desc_cm'] or '')[:150].rstrip() + ('…' if len(d['desc_cm'] or '') > 150 else '')
    desc = f"{d['display']}: {desc}"
    og = f"{SITE}character_images/{d['official']}.webp"
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "ProfilePage", "@id": canonical + "#page", "url": canonical,
             "name": title, "description": desc, "dateModified": META['data_updated'],
             "isPartOf": {"@id": f"{SITE}#website"},
             "mainEntity": {"@id": canonical + "#person"},
             "about": {"@type": "VideoGame", "name": "Zenless Zone Zero"}},
            {"@type": "Person", "@id": canonical + "#person", "name": d['display'],
             "description": d['desc_cm'], "image": og,
             "additionalProperty": [
                 {"@type": "PropertyValue", "name": name, "value": value, "unitText": "cm"}
                 for name, value in (
                     ("height (charted)", d['cm']),
                     ("stature", d['stature_cm']),
                     ("bust", d['bust_cm']),
                     ("under-bust", d['band_cm']),
                     ("waist", d['waist_cm']),
                     ("hip", d['hip_cm']),
                     ("thigh", d['thigh_cm']),
                 ) if value is not None
             ] + [{"@type": "PropertyValue", "name": "bra size (UK)", "value": d['uk']}]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "ZZZ Measurements", "item": SITE},
                {"@type": "ListItem", "position": 2, "name": d['display'], "item": canonical},
            ]},
        ],
    }
    ld_tag = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>'

    rows = [
        ('Height (charted)', f"{fmt(d['cm'], 0)} cm · {d['ftin']}"),
        ('Stature used', f"{fmt(d['stature_cm'], 0)} cm · {d['ftin_stature']}" + (' (head height)' if d['stature_basis'] == 'head' else '')),
        ('Bust', f"{fmt(d['bust_cm'])} cm · {fmt(d['bust_in'])} in"),
        ('Under-bust', f"{fmt(d['band_cm'])} cm · {fmt(d['band_in'])} in"),
        ('Waist', f"{fmt(d['waist_cm'])} cm · {fmt(d['waist_in'])} in"),
        ('Hip', f"{fmt(d['hip_cm'])} cm · {fmt(d['hip_in'])} in"),
        ('Thigh', (f"{fmt(d['thigh_cm'])} cm · {fmt(d['thigh_in'])} in" if d['thigh_cm'] is not None else 'no reliable measurement')),
        ('Bust diff', (f"{fmt(d['diff_cm'])} cm · {fmt(d['diff_in'])} in" if d['diff_cm'] is not None else '—')),
        ('Bra size', f"UK {d['uk']} · US {d['us']} · EU {d['eu']}"),
    ]
    rows_html = ''.join(f'<tr><th scope="row">{esc(k)}</th><td>{esc(v)}</td></tr>' for k, v in rows)

    props = [
        ('Waist / hip', d['whr']), ('Waist / stature', d['whtr']), ('Waist / thigh', d['wtr']),
        ('Thigh / stature', d['thr']), ('Thigh / hip', d['thh']), ('Bust / stature', d['bhr']),
        ('Hip / stature', d['hhr']),
    ]
    props_html = ''.join(f'<tr><th scope="row">{esc(k)}</th><td>{fmt(v, 3)}</td></tr>' for k, v in props)

    gallery = []
    gallery.append((f"character_images/thumbs/320/{d['official']}.webp", f"{d['display']} — official portrait", 'Standard model'))
    if d.get('skin'):
        s = d['skin']
        gallery.append((f"character_images/{s['official']}.webp", f"{s['outfit']} — measured outfit", 'Measured outfit · has its own numbers'))
    for it in d['outfits']:
        gallery.append((f"character_images/{it['file']}", f"{it['label']} — outfit portrait", f"{it['type']} · art only"))
    gallery_html = ''.join(
        f'<figure><img loading="lazy" decoding="async" src="../{esc(src)}" alt="{esc(alt)}">'
        f'<figcaption><b>{esc(alt.split(" — ")[0])}</b>{esc(cap)}</figcaption></figure>'
        for src, alt, cap in gallery)

    sim = similar(d)
    sim_html = ' · '.join(f'<a href="{esc(x["slug"])}.html">{esc(x["display"])}</a>' for x in sim)
    report = (f"{META['repo']}/issues/new?title=" + quote(f"[data] {d['display']}") +
              "&body=" + quote(f"Character: {d['display']}\nField: \nCurrent value: \nSource: \n\nWhat looks wrong?\n"))
    src_link = (f"<a href=\"https://zenless-zone-zero.fandom.com/wiki/{quote(d['source_page'].replace(' ', '_'))}\" rel=\"noopener\">"
                f"{esc(d['source_page'])}</a>" if d.get('source_page') else '—')
    measured_note = (f"<p class=\"note\">This agent has a measured outfit ({esc(d['skin']['outfit'])}). The numbers on this page "
                     f"are the <b>standard model</b>; the outfit record is kept separate in the dataset.</p>" if d.get('skin') else '')
    stature_note = ("<p class=\"note\">Charted height counts her ears. Stature comparisons use the ~"
                    f"{fmt(d['stature_cm'], 0)} cm head height.</p>" if d['stature_basis'] == 'head' else '')

    return head(title, desc, canonical, og, ld_tag) + f'''
<main>
  <section class="hero">
    {hero_picture(d)}
    <div>
      <p class="eyebrow">Zenless Zone Zero · measurements</p>
      <h1>{esc(d['display'])}</h1>
      <p class="lead">{esc(d['read'])}</p>
      <ul class="chips">
        <li class="chip height">{esc(d['tags']['height'])}</li>
        <li class="chip bust">UK {esc(d['uk'])}</li>
        <li class="chip waist">waist {esc(d['tags']['waist'])}</li>
        <li class="chip hips">hips {esc(d['tags']['hips'])}</li>
        <li class="chip thighs">thighs {esc(d['tags']['thighs'])}</li>
      </ul>
      <p class="meta">{fmt(d['cm'], 0)} cm charted · {fmt(d['stature_cm'], 0)} cm stature · UK {esc(d['uk'])} / US {esc(d['us'])} / EU {esc(d['eu'])}</p>
      <div class="btns">
        <a class="btn primary" href="../#p={esc(d['slug'])}">Open in the chart</a>
        <a class="btn" href="../data/measurements.json" download>Dataset</a>
        <a class="btn" href="{report}" rel="noopener">Report an error</a>
      </div>
    </div>
  </section>

  {stature_note}{measured_note}

  <h2>Measurements</h2>
  <table><caption class="small" style="text-align:left;padding-bottom:6px">Centimetres and inches; bra sizing as supplied by the source.</caption>
    <tbody>{rows_html}</tbody></table>

  <div class="grid2">
    <div><h2>Proportions</h2><table><tbody>{props_html}</tbody></table></div>
    <div><h2>Roster percentiles</h2><div class="bars">{pct_bars(d)}</div>
      <p class="small" style="margin-top:10px">Percentiles of the raw centimetre measurement across the {N} displayed entries; stature uses head height. 0 = smallest, 100 = largest.</p></div>
  </div>

  <h2>Figure read</h2>
  <div class="card"><p>{esc(d['desc_cm'])}</p>
    <p class="small" style="margin-top:10px">Classes: waist {esc(d['tags']['waist'])} · hips {esc(d['tags']['hips'])} · thighs {esc(d['tags']['thighs'])}{' (hand-pinned)' if d['thigh_pin'] else ''} · shape {esc(d['shape'])} · build {esc(d['tags']['balance'])}.</p>
    {f'<p class="note">Chart note: {esc(d["notes"])}</p>' if d['notes'] and not (d['stature_basis'] == 'head' and d['notes'].lower().startswith('height includes ears')) else ''}
  </div>

  <h2>Outfits</h2>
  <div class="gallery">{gallery_html}</div>

  <h2>Provenance</h2>
  <table><tbody>
    <tr><th scope="row">Portrait source</th><td>{src_link}</td></tr>
    <tr><th scope="row">Data updated</th><td>{META['data_updated']}</td></tr>
    <tr><th scope="row">Similar figures</th><td>{sim_html}</td></tr>
  </tbody></table>

  <nav class="nav" aria-label="Roster navigation">
    <div><span>Previous</span><br><a href="{esc(prev_d['slug'])}.html">← {esc(prev_d['display'])}</a></div>
    <div style="text-align:right"><span>Next</span><br><a href="{esc(next_d['slug'])}.html">{esc(next_d['display'])} →</a></div>
  </nav>
</main>
''' + footer(META['data_updated'])


FAQ = [
    ("Where do the numbers come from?",
     "Heights come from official listings where available. The remaining circumferences come from curves measured around the official 3D models, so treat every value as an estimate rather than an in-game stat."),
    ("Why does Miyabi show 170 cm and 155 cm?",
     "Her charted 170 cm includes her ears. Stature comparisons use the ~155 cm head height, while the charted number stays visible in the table, the card and the exports."),
    ("Why is the card value the standard model?",
     "The standard model is the canonical figure. A measured outfit is stored as its own record with its own numbers and deltas, so no card or ranking mixes two outfits into one body."),
    ("What do the silhouette classes mean?",
     "Shape (Hourglass / Balanced / Straight) is the waist ÷ hip percentile. Build compares the raw bust and hip percentiles. Waist, hip and thigh classes are roster terciles of their raw circumference."),
    ("What does hand-pinned mean?",
     "A few agents read as visibly thicker or slimmer than a single circumference suggests. Thirteen are marked thick by curator read and labelled hand-pinned in their detail view."),
    ("How is the bust tier calculated?",
     "Bust minus under-bust, recomputed to one decimal rather than using the sheet's rounded diff column. The letter is the source's UK sizing, not a fit recommendation."),
    ("Can I reuse the data?",
     "The measurements are compiled from modelmetrics.net and the character art is © HoYoverse, shown via the ZZZ Fandom wiki as fair use. Link back to the source and respect those rights."),
]


def methodology_page():
    canonical = SITE + 'methodology.html'
    title = "Methodology, classes and FAQ — ZZZ Female Measurements"
    desc = ("How the Zenless Zone Zero measurements were taken, why stature and charted height differ, "
            "and what the silhouette classes and percentiles mean.")
    faq_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "FAQPage", "@id": canonical + "#faq",
             "mainEntity": [{"@type": "Question", "name": q,
                             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "ZZZ Measurements", "item": SITE},
                {"@type": "ListItem", "position": 2, "name": "Methodology", "item": canonical},
            ]},
        ],
    }
    ld_tag = '<script type="application/ld+json">' + json.dumps(faq_ld, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>'
    faq_html = ''.join(f'<dt>{esc(q)}</dt><dd>{esc(a)}</dd>' for q, a in FAQ)
    return head(title, desc, canonical, SITE + 'og.png', ld_tag, prefix='') + f'''
<main>
  <p class="eyebrow">Reference</p>
  <h1>Methodology &amp; FAQ</h1>
  <p class="lead">A short, honest account of what the chart measures, what it estimates, and how every class and percentile is calculated.</p>

  <div class="grid2">
    <section class="card">
      <h3>Height</h3>
      <p>Charted height comes from official listings and may include ears, footwear or accessories. Stature comparisons use head height where the chart notes an appendage. Both values appear in the table and in the exports; <code>stature_cm</code> is the comparison value.</p>
    </section>
    <section class="card">
      <h3>Circumferences</h3>
      <p>Bust, under-bust, waist, hip and thigh come from curves wrapped around the official 3D models. Clothing, armour and removed geometry make some readings approximate; the source notes are preserved verbatim.</p>
    </section>
    <section class="card">
      <h3>Standard model vs outfit</h3>
      <p>The standard model is canonical. A measured outfit is a separate record with its own numbers and deltas; art-only outfits are never measured and never affect a figure, filter or ranking.</p>
    </section>
    <section class="card">
      <h3>Bra sizing</h3>
      <p>The bust tier uses bust minus under-bust, recomputed to one decimal. UK / US / EU letters are reproduced from the source for comparison, not as a fit recommendation.</p>
    </section>
    <section class="card">
      <h3>Classes</h3>
      <p>Waist, hip and thigh classes are roster terciles of the raw circumference in cm. Build compares raw bust and hip percentiles. Shape is waist ÷ hip. Thirteen agents are hand-pinned to Thick by curator read and labelled as such.</p>
    </section>
    <section class="card">
      <h3>Percentiles</h3>
      <p>Bars show the roster percentile of the raw centimetre measurement, with stature using head height. 0 is the smallest value in the set, 50 the midpoint and 100 the largest.</p>
    </section>
    <section class="card">
      <h3>Corrections</h3>
      <p>Every character page has a pre-filled “Report an error” link. Corrections are recorded in the changelog, and the dataset carries a schema version and an update date.</p>
    </section>
  </div>

  <h2>Data &amp; exports</h2>
  <p class="lead">The same numbers power the interactive chart and the static pages. Downloads are versioned by schema v{META['schema_version']} and dated {META['data_updated']}.</p>
  <div class="btns">
    <a class="btn primary" href="data/measurements.json" download>JSON dataset</a>
    <a class="btn" href="data/measurements.csv" download>CSV export</a>
    <a class="btn" href="data/schema.json" download>JSON Schema</a>
  </div>
  <p class="small">Rights: {esc(META['rights'])}</p>

  <h2>FAQ</h2>
  <dl class="faq">{faq_html}</dl>

  <div class="btns"><a class="btn primary" href="./">Back to the chart</a></div>
</main>
''' + footer(META['data_updated'], prefix='')


def export_json():
    out = {"meta": {
        "schema_version": META['schema_version'],
        "data_updated": META['data_updated'],
        "source": META['source'],
        "rights": META['rights'],
        "count": N,
        "fields": META['fields'],
        "urls": {"site": SITE, "json": SITE + "data/measurements.json",
                 "csv": SITE + "data/measurements.csv", "schema": SITE + "data/schema.json"},
    }, "characters": []}
    for d in DATA:
        rec = {
            "slug": d['slug'], "name": d['name'], "display": d['display'],
            "aliases": d['aliases'],
            "height_cm": d['cm'], "stature_cm": d['stature_cm'], "stature_basis": d['stature_basis'],
            "bust_cm": d['bust_cm'], "underbust_cm": d['band_cm'], "waist_cm": d['waist_cm'],
            "hip_cm": d['hip_cm'], "thigh_cm": d['thigh_cm'],
            "bust_in": d['bust_in'], "underbust_in": d['band_in'], "waist_in": d['waist_in'],
            "hip_in": d['hip_in'], "thigh_in": d['thigh_in'],
            "bust_diff_cm": d['diff_cm'], "bust_diff_in": d['diff_in'],
            "uk": d['uk'], "us": d['us'], "eu": d['eu'],
            "ratios": {"waist_hip": d['whr'], "waist_stature": d['whtr'], "waist_thigh": d['wtr'],
                       "thigh_stature": d['thr'], "thigh_hip": d['thh'],
                       "bust_stature": d['bhr'], "hip_stature": d['hhr']},
            "percentiles": {"bust": d['p_bust_cm'], "waist": d['p_waist_cm'], "hip": d['p_hip_cm'],
                            "thigh": d['p_thigh_cm'], "stature": d['p_stature_cm']},
            "classes": {"height": d['height_group'], "cup": d['cup_group'], "waist": d['waist_level'],
                        "hip": d['hip_level'], "thigh": d['thigh_level'], "thigh_hand_pinned": d['thigh_pin'],
                        "shape": d['shape'], "build": d['balance']},
            "confidence": d['confidence'], "confidence_note": d['confidence_note'],
            "notes": d['notes'], "source_page": d['source_page'],
            "profile": SITE + f"characters/{d['slug']}.html",
            "measured_outfit": None,
            "art_only_outfits": [{"label": o['label'], "type": o['type']} for o in d['outfits']],
        }
        if d.get('skin'):
            s = d['skin']
            rec['measured_outfit'] = {
                "outfit": s['outfit'], "bust_cm": s['bust_cm'], "underbust_cm": s['band_cm'],
                "waist_cm": s['waist_cm'], "hip_cm": s['hip_cm'], "thigh_cm": s['thigh_cm'],
                "bust_diff_cm": s['diff_cm'], "uk": s['uk'], "us": s['us'], "eu": s['eu'],
                "ratios": {"waist_hip": s['whr'], "waist_stature": s['whtr']},
            }
        out['characters'].append(rec)
    return out


def export_csv(path):
    cols = ['slug', 'name', 'display', 'height_cm', 'stature_cm', 'stature_basis', 'bust_cm',
            'underbust_cm', 'waist_cm', 'hip_cm', 'thigh_cm', 'bust_diff_cm', 'uk', 'us', 'eu',
            'waist_hip_ratio', 'waist_stature_ratio', 'thigh_stature_ratio', 'thigh_hip_ratio',
            'height_class', 'cup_class', 'waist_class', 'hip_class', 'thigh_class', 'thigh_hand_pinned',
            'shape', 'build', 'confidence', 'notes', 'source_page', 'profile']
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for d in DATA:
            w.writerow([d['slug'], d['name'], d['display'], d['cm'], d['stature_cm'], d['stature_basis'],
                        d['bust_cm'], d['band_cm'], d['waist_cm'], d['hip_cm'], d['thigh_cm'], d['diff_cm'],
                        d['uk'], d['us'], d['eu'], d['whr'], d['whtr'], d['thr'], d['thh'],
                        d['height_group'], d['cup_group'], d['waist_level'], d['hip_level'], d['thigh_level'],
                        d['thigh_pin'], d['shape'], d['balance'], d['confidence'], d['notes'], d['source_page'],
                        SITE + f"characters/{d['slug']}.html"])


def schema_doc():
    num = {"type": ["number", "null"]}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SITE + "data/schema.json",
        "title": "ZZZ Female Measurements dataset",
        "description": "Measurements, proportions and classification for the female Zenless Zone Zero roster.",
        "type": "object",
        "required": ["meta", "characters"],
        "properties": {
            "meta": {
                "type": "object",
                "required": ["schema_version", "data_updated", "count"],
                "properties": {
                    "schema_version": {"type": "integer"},
                    "data_updated": {"type": "string", "format": "date"},
                    "count": {"type": "integer", "minimum": 1},
                    "source": {"type": "string"}, "rights": {"type": "string"},
                    "fields": {"type": "object"},
                },
            },
            "characters": {
                "type": "array", "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["slug", "display", "height_cm", "stature_cm", "bust_cm", "waist_cm", "hip_cm", "confidence"],
                    "properties": {
                        "slug": {"type": "string", "pattern": "^[a-z0-9_]+$"},
                        "name": {"type": "string"}, "display": {"type": "string"},
                        "aliases": {"type": "array", "items": {"type": "string"}},
                        "height_cm": num, "stature_cm": num,
                        "stature_basis": {"enum": ["charted", "head"]},
                        "bust_cm": num, "underbust_cm": num, "waist_cm": num, "hip_cm": num, "thigh_cm": num,
                        "bust_in": num, "underbust_in": num, "waist_in": num, "hip_in": num, "thigh_in": num,
                        "bust_diff_cm": num, "bust_diff_in": num,
                        "uk": {"type": "string"}, "us": {"type": "string"}, "eu": {"type": "string"},
                        "ratios": {"type": "object", "additionalProperties": num},
                        "percentiles": {"type": "object", "additionalProperties": num},
                        "classes": {
                            "type": "object",
                            "properties": {
                                "height": {"enum": ["Petite", "Mid", "Tall"]},
                                "shape": {"enum": ["Hourglass", "Balanced", "Straight"]},
                                "build": {"enum": ["top", "bottom", "even"]},
                                "thigh_hand_pinned": {"type": "boolean"},
                            },
                        },
                        "confidence": {"enum": ["charted", "estimated", "partial"]},
                        "confidence_note": {"type": "string"},
                        "notes": {"type": "string"},
                        "source_page": {"type": ["string", "null"]},
                        "profile": {"type": "string", "format": "uri"},
                        "measured_outfit": {"type": ["object", "null"]},
                        "art_only_outfits": {"type": "array"},
                    },
                },
            },
        },
    }


OFFLINE = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Offline · ZZZ Female Measurements</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="stylesheet" href="fonts/fonts.css">
<style>
  body{{margin:0;background:#0B0B0C;color:#fff;font-family:Inter,system-ui,sans-serif;
    display:grid;place-items:center;min-height:100vh;text-align:center}}
  h1{{font-family:'Anton',Impact,sans-serif;font-weight:400;font-size:clamp(36px,9vw,80px);
    text-transform:uppercase;margin:0 0 10px}} h1 span{{color:#D8FA00}}
  p{{color:#9A9AA3;margin:0 0 22px}} a{{display:inline-block;background:#D8FA00;color:#0b0b0c;
    text-decoration:none;font-weight:800;padding:12px 22px;border-radius:999px;font-size:13px;
    letter-spacing:.08em;text-transform:uppercase}}
</style></head>
<body><main><h1>Offline <span>mode</span></h1>
<p>The roster you already visited is cached. Reconnect for the latest data.</p>
<a href="./">Retry the chart</a></main></body></html>
'''


def main():
    global SITE
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(ROOT / 'docs'))
    ap.add_argument('--site-url', default=SITE)
    a = ap.parse_args()
    SITE = a.site_url if a.site_url.endswith('/') else a.site_url + '/'
    out = Path(a.out)
    (out / 'characters').mkdir(parents=True, exist_ok=True)
    (out / 'data').mkdir(parents=True, exist_ok=True)

    for i, d in enumerate(DISPLAY_SORTED):
        prev_d = DISPLAY_SORTED[(i - 1) % N]
        next_d = DISPLAY_SORTED[(i + 1) % N]
        (out / 'characters' / f"{d['slug']}.html").write_text(character_page(d, prev_d, next_d))
    (out / 'methodology.html').write_text(methodology_page())
    (out / 'offline.html').write_text(OFFLINE)
    (out / 'data' / 'measurements.json').write_text(
        json.dumps(export_json(), indent=1, ensure_ascii=False) + '\n')
    export_csv(out / 'data' / 'measurements.csv')
    (out / 'data' / 'schema.json').write_text(
        json.dumps(schema_doc(), indent=1, ensure_ascii=False) + '\n')
    print(f'pages: {N} character pages + methodology + offline + 3 data files -> {out}')


if __name__ == '__main__':
    main()
