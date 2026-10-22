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

PAGE = {
    'en': {
        'home': '← ZZZ Measurements', 'top': 'Zenless Zone Zero · <b>{n}</b> agents',
        'eyebrow': 'Zenless Zone Zero · measurements', 'open': 'Open in the chart',
        'dataset': 'Dataset', 'report': 'Report an error', 'measurements': 'Measurements',
        'caption': 'Centimetres and inches; bra sizing as supplied by the source.',
        'proportions': 'Proportions', 'percentiles': 'Roster percentiles',
        'pct_note': 'Percentiles of the raw centimetre measurement across the {n} displayed entries; height uses head height. 0 = smallest, 100 = largest.',
        'figure_read': 'Figure read', 'classes': 'Classes', 'outfits': 'Outfits',
        'provenance': 'Provenance', 'portrait_source': 'Portrait source', 'updated': 'Data updated',
        'similar': 'Similar figures', 'previous': 'Previous', 'next': 'Next',
        'height': 'Height', 'bust': 'Bust', 'underbust': 'Under-bust', 'waist': 'Waist',
        'hip': 'Hip', 'thigh': 'Thigh', 'bust_diff': 'Bust diff', 'bra': 'Bra size',
        'no_thigh': 'no reliable measurement', 'charted': 'charted',
        'waist_hip': 'Waist / hip', 'waist_height': 'Waist / height', 'waist_thigh': 'Waist / thigh',
        'thigh_height': 'Thigh / height', 'thigh_hip': 'Thigh / hip',
        'bust_height': 'Bust / height', 'hip_height': 'Hip / height',
        'official_portrait': 'Official portrait', 'measured_outfit': 'Measured outfit · has its own numbers',
        'outfit_portrait': 'outfit portrait', 'art_only': 'art only',
        'stature_note': 'Height uses the ~{st} cm head height; the charted {cm} cm includes her ears.',
        'measured_note': 'This agent has a measured outfit ({outfit}). The numbers on this page are the <b>standard model</b>; the outfit record is kept separate in the dataset.',
        'chart_note': 'Chart note', 'source': 'Source', 'rights': 'Official art via HoYoverse and the ZZZ Fandom wiki, © HoYoverse (fair use). Auto-generated commentary is not in-game canon.',
        'methodology': 'Methodology &amp; FAQ', 'data_updated': 'Data updated', 'back': 'Back to the chart',
        'shape': 'Shape', 'build_word': 'build', 'hand_pinned': 'hand-pinned', 'language': 'Language', 'roster_nav': 'Roster navigation',
    },
    'ja': {
        'home': '← ZZZ 寸法', 'top': 'ゼンレスゾーンゼロ · <b>{n}</b> 名',
        'eyebrow': 'ゼンレスゾーンゼロ · 寸法', 'open': 'チャートで開く',
        'dataset': 'データセット', 'report': '誤りを報告', 'measurements': '寸法',
        'caption': 'センチとインチ。ブラサイズは出典の表記のまま。',
        'proportions': '比率', 'percentiles': '名簿内パーセンタイル',
        'pct_note': '{n}名の実寸cm値のパーセンタイル。身長は頭頂ベース。0＝最小、100＝最大。',
        'figure_read': '体型の読み', 'classes': '分類', 'outfits': '衣装',
        'provenance': '出典', 'portrait_source': '画像出典', 'updated': 'データ更新',
        'similar': '似た体型', 'previous': '前', 'next': '次',
        'height': '身長', 'bust': 'バスト', 'underbust': 'アンダー', 'waist': 'ウエスト',
        'hip': 'ヒップ', 'thigh': '太もも', 'bust_diff': 'バスト差', 'bra': 'ブラサイズ',
        'no_thigh': '信頼できる計測なし', 'charted': '公式',
        'waist_hip': 'ウエスト / ヒップ', 'waist_height': 'ウエスト / 身長', 'waist_thigh': 'ウエスト / 太もも',
        'thigh_height': '太もも / 身長', 'thigh_hip': '太もも / ヒップ',
        'bust_height': 'バスト / 身長', 'hip_height': 'ヒップ / 身長',
        'official_portrait': '公式ポートレート', 'measured_outfit': '計測済み衣装・独自の数値あり',
        'outfit_portrait': '衣装ポートレート', 'art_only': '画像のみ',
        'stature_note': '身長は頭頂ベースの約{st}cm。公式の{cm}cmは耳を含みます。',
        'measured_note': 'このエージェントには計測済み衣装（{outfit}）があります。このページの数値は<b>標準モデル</b>で、衣装の記録はデータセット内に別途保存しています。',
        'chart_note': 'チャート注記', 'source': '出典', 'rights': '公式画像はHoYoverse公式サイトおよびZZZ Fandom wiki経由、© HoYoverse（フェアユース）。自動生成の解説はゲーム内設定ではありません。',
        'methodology': '算出方法とFAQ', 'data_updated': 'データ更新', 'back': 'チャートに戻る',
        'shape': 'シルエット', 'build_word': '体型', 'hand_pinned': '手動分類', 'language': '言語', 'roster_nav': '名簿ナビゲーション',
    },
    'zh': {
        'home': '← ZZZ 测量', 'top': '绝区零 · <b>{n}</b> 位角色',
        'eyebrow': '绝区零 · 三围', 'open': '在图表中打开',
        'dataset': '数据集', 'report': '报告错误', 'measurements': '测量',
        'caption': '厘米和英寸；内衣尺码沿用来源写法。',
        'proportions': '比例', 'percentiles': '名单百分位',
        'pct_note': '{n} 位角色原始厘米数据的百分位；身高按头顶高度计算。0 = 最小，100 = 最大。',
        'figure_read': '体型解读', 'classes': '分类', 'outfits': '服装',
        'provenance': '来源', 'portrait_source': '立绘来源', 'updated': '数据更新',
        'similar': '相似体型', 'previous': '上一位', 'next': '下一位',
        'height': '身高', 'bust': '胸围', 'underbust': '下胸围', 'waist': '腰围',
        'hip': '臀围', 'thigh': '大腿', 'bust_diff': '胸围差', 'bra': '内衣尺码',
        'no_thigh': '没有可靠数据', 'charted': '官方',
        'waist_hip': '腰围 / 臀围', 'waist_height': '腰围 / 身高', 'waist_thigh': '腰围 / 大腿',
        'thigh_height': '大腿 / 身高', 'thigh_hip': '大腿 / 臀围',
        'bust_height': '胸围 / 身高', 'hip_height': '臀围 / 身高',
        'official_portrait': '官方立绘', 'measured_outfit': '已测量服装 · 有独立数据',
        'outfit_portrait': '服装立绘', 'art_only': '仅立绘',
        'stature_note': '身高采用约 {st} 厘米的头顶高度；官方 {cm} 厘米包含耳朵。',
        'measured_note': '这位角色有一套已测量服装（{outfit}）。本页数值是<b>标准模型</b>；服装数据单独保存在数据集中。',
        'chart_note': '榜单注记', 'source': '来源', 'rights': '官方立绘来自 HoYoverse 官网和 ZZZ Fandom wiki，© HoYoverse（合理使用）。自动生成的解读并非游戏内设定。',
        'methodology': '方法与常见问题', 'data_updated': '数据更新', 'back': '返回图表',
        'shape': '轮廓', 'build_word': '体型', 'hand_pinned': '人工分类', 'language': '语言', 'roster_nav': '名单导航',
    },
}


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
  --thighs:#FFDE00;--tan:#D3BC8E;--disp:'ZZZ Hongmeng','Anton','Noto Sans JP 900','Dela Gothic One','Arial Narrow',Impact,sans-serif;
  --body:'ZZZ Hongmeng',Inter,'Noto Sans JP 900','Noto Sans JP',system-ui,-apple-system,sans-serif;
  --num:'Chakra Petch','ZZZ Hongmeng','Noto Sans JP 900','Noto Sans JP',ui-monospace,Menlo,monospace}
html[lang^="zh"]{--disp:'ZZZ Hongmeng','Anton','Noto Sans SC Display','Arial Narrow',Impact,sans-serif;
  --body:'ZZZ Hongmeng',Inter,'Noto Sans SC Display','Noto Sans SC',system-ui,-apple-system,sans-serif;
  --num:'Chakra Petch','ZZZ Hongmeng','Noto Sans SC Display','Noto Sans SC',ui-monospace,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--ink);color:#fff;font:14px/1.6 var(--body);
  -webkit-font-smoothing:antialiased}
a{color:var(--acid)}
:focus-visible{outline:2px solid var(--acid);outline-offset:2px}
.top{max-width:1100px;margin:0 auto;padding:18px 20px;display:flex;justify-content:space-between;
  align-items:center;gap:12px;border-bottom:1px solid var(--line);font-size:11px;letter-spacing:.14em;
  text-transform:uppercase}
.top a{text-decoration:none;color:var(--dim)}
.top a:hover{color:var(--acid)}
.top b{font-family:var(--num);color:var(--acid)}
.langnav{display:flex;gap:10px;margin-left:auto}.langnav a{text-decoration:none}.langnav a[data-lang]{opacity:.55}.langnav a:hover{color:var(--acid);opacity:1}.langnav a.on{color:var(--acid);opacity:1}
main{max-width:1100px;margin:0 auto;padding:22px 20px 60px}
.hero{display:grid;grid-template-columns:min(340px,38vw) 1fr;gap:26px;align-items:center;
  border-bottom:1px solid var(--line);padding-bottom:24px}
.hero img{width:100%;height:auto;border-radius:16px;border:1px solid var(--line);background:#101014}
.hero picture{display:block}
.eyebrow{margin:0 0 6px;font-family:var(--num);font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:var(--dim)}
h1{margin:0 0 10px;font-family:var(--disp);font-weight:400;font-size:clamp(36px,6vw,64px);line-height:.96;
  text-transform:uppercase;word-break:keep-all;line-break:strict}
html[lang="ja"] h1{font-size:clamp(30px,5vw,54px);line-height:1.04;letter-spacing:.01em}
@media(max-width:560px){.top{flex-wrap:nowrap;padding:14px 16px;gap:10px;font-size:10px;letter-spacing:.1em}.top>span{display:none}.top a{white-space:nowrap}.langnav{gap:8px;margin-left:auto}}
.lead{margin:0 0 14px;color:#cfd0d6;font-size:13px}
.altname{margin:-6px 0 10px;color:var(--dim);font-family:var(--num);font-size:11px;letter-spacing:.08em}
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


def head(title, desc, canonical, og_image, extra_ld='', prefix='../', lang='en', alts=None, home=None, path=''):
    p = PAGE[lang]
    home = home if home is not None else prefix
    alt = ''
    if alts:
        alt = ''.join(f'<link rel="alternate" hreflang="{esc(h)}" href="{esc(url)}">\n' for h, url in alts)
    return f'''<!DOCTYPE html>
<html lang="{ 'zh-Hans' if lang=='zh' else lang }">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
{alt}<meta property="og:type" content="article">
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
<header class="top">
  <a href="{home}">{p['home']}</a>
  <nav class="langnav" aria-label="{p['language']}">
    <a href="{prefix}{path}" data-lang="en" class="{ 'on' if lang=='en' else ''}" onclick="try{{localStorage.setItem('zzz-lang','en')}}catch(e){{}}">EN</a>
    <a href="{prefix}ja/{path}" data-lang="ja" class="{ 'on' if lang=='ja' else ''}" onclick="try{{localStorage.setItem('zzz-lang','ja')}}catch(e){{}}">日本語</a>
    <a href="{prefix}zh/{path}" data-lang="zh" class="{ 'on' if lang=='zh' else ''}" onclick="try{{localStorage.setItem('zzz-lang','zh')}}catch(e){{}}">中文</a>
  </nav>
  <span>{p['top'].format(n=N)}</span>
</header>
'''


def footer(updated, prefix='../', lang='en', methodology=None):
    p = PAGE[lang]
    methodology = methodology or (prefix + ('methodology.html' if lang == 'en' else f'{lang}/methodology.html'))
    return f'''<footer><div class="rule">
<b>{p['source']}:</b> modelmetrics.net · <i>Zenless Zone Zero · Female Character Measurements</i>. {p['data_updated']} <time datetime="{updated}">{updated}</time>.<br>
{p['rights']}<br>
<a href="{methodology}">{p['methodology']}</a> · <a href="{prefix}data/measurements.json" download>{esc(p["dataset"])} (JSON)</a> ·
<a href="{prefix}data/measurements.csv" download>CSV</a> · <a href="{META['repo']}" rel="noopener">Source</a>
</div></footer>
</body>
</html>'''


def pct_bars(r, lang='en'):
    labels = PAGE[lang]
    rows = [
        (labels['bust'], r['p_bust_cm'], 'var(--bust)'),
        (labels['waist'], r['p_waist_cm'], 'var(--waist)'),
        (labels['hip'], r['p_hip_cm'], 'var(--hips)'),
        (labels['thigh'], r['p_thigh_cm'], 'var(--thighs)'),
        (labels['height'], r['p_stature_cm'], 'var(--tan)'),
    ]
    return ''.join(
        f'<div class="prow"><span>{label}</span><div class="pbar"><i style="width:{pct(p)}%;background:{col}"></i></div><b>{pct(p) if p is not None else "—"}</b></div>'
        for label, p, col in rows)


def hero_picture(d, prefix='../', name=None, alt_word='official portrait'):
    s = d['official']
    name = name or d['display']
    sizes = '(max-width:760px) 360px, 340px'
    height = round(440 / d['ar']) if d.get('ar') else 700
    w320 = intrinsic_width(f'character_images/thumbs/320/{s}.webp')
    w640 = intrinsic_width(f'character_images/thumbs/{s}.webp')
    w1024 = intrinsic_width(f'character_images/thumbs/avif/1024/{s}.avif')
    w1280 = intrinsic_width(f'character_images/thumbs/avif/1280/{s}.avif')
    wfull = intrinsic_width(f'character_images/{s}.webp')
    avif = (f'{prefix}character_images/thumbs/avif/320/{s}.avif {w320}w, '
            f'{prefix}character_images/thumbs/avif/{s}.avif {w640}w, '
            f'{prefix}character_images/thumbs/avif/1024/{s}.avif {w1024}w, '
            f'{prefix}character_images/thumbs/avif/1280/{s}.avif {w1280}w')
    webp = (f'{prefix}character_images/thumbs/320/{s}.webp {w320}w, '
            f'{prefix}character_images/thumbs/{s}.webp {w640}w, '
            f'{prefix}character_images/{s}.webp {wfull}w')
    return (f'<picture>'
            f'<source type="image/avif" srcset="{avif}" sizes="{sizes}">'
            f'<img src="{prefix}character_images/thumbs/{s}.webp" srcset="{webp}" '
            f'sizes="{sizes}" width="440" height="{height}" alt="{esc(name)} {esc(alt_word)}">'
            f'</picture>')


def character_page(d, prev_d, next_d, lang='en'):
    p = PAGE[lang]
    nm = d.get(f'name_{lang}') or d['display']
    read = d.get(f'read_{lang}') or d['read']
    tags = d.get(f'tags_{lang}') or d['tags']
    note = d.get(f'notes_{lang}') if lang != 'en' else d.get('notes')
    if lang == 'en':
        profile_cm, profile_in = d['desc_cm'], d['desc_in']
    else:
        profile_cm = d.get(f'desc_{lang}_cm') or d['desc_cm']
        profile_in = d.get(f'desc_{lang}_in') or d['desc_in']
    sub = '' if lang == 'en' else f'<p class="altname" lang="en">{esc(d["display"])}</p>'
    prefix = '../' if lang == 'en' else '../../'
    page_path = f"characters/{d['slug']}.html"
    base = SITE + (f'{lang}/' if lang != 'en' else '')
    canonical = base + page_path
    alts = [
        ('en', SITE + f"characters/{d['slug']}.html"),
        ('ja', SITE + f"ja/characters/{d['slug']}.html"),
        ('zh-Hans', SITE + f"zh/characters/{d['slug']}.html"),
        ('x-default', SITE + f"characters/{d['slug']}.html"),
    ]
    if lang == 'en':
        title = f"{d['display']} measurements — height, bust, waist, hips | ZZZ"
    elif lang == 'ja':
        title = f"{nm}の寸法 — 身長・バスト・ウエスト・ヒップ | ZZZ"
    else:
        title = f"{nm}的三围 — 身高、胸围、腰围、臀围 | ZZZ"
    desc = (profile_cm or '')[:150].rstrip() + ('…' if len(profile_cm or '') > 150 else '')
    desc = f"{nm}: {desc}"
    og = f"{SITE}character_images/{d['official']}.webp"
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "ProfilePage", "@id": canonical + "#page", "url": canonical,
             "name": title, "description": desc, "dateModified": META['data_updated'],
             "inLanguage": lang,
             "isPartOf": {"@id": f"{SITE}#website"},
             "mainEntity": {"@id": canonical + "#person"},
             "about": {"@type": "VideoGame", "name": "Zenless Zone Zero"}},
            {"@type": "Person", "@id": canonical + "#person", "name": nm,
             "alternateName": [d['display'], d.get('name_ja'), d.get('name_zh')],
             "description": profile_cm, "image": og,
             "additionalProperty": [
                 {"@type": "PropertyValue", "name": label, "value": value, "unitText": "cm"}
                 for label, value in (
                     (p['height'], d['stature_cm']),
                     (p['bust'], d['bust_cm']),
                     (p['underbust'], d['band_cm']),
                     (p['waist'], d['waist_cm']),
                     (p['hip'], d['hip_cm']),
                     (p['thigh'], d['thigh_cm']),
                 ) if value is not None
             ] + [{"@type": "PropertyValue", "name": p['bra'] + " (UK)", "value": d['uk']}]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "ZZZ Measurements", "item": SITE},
                {"@type": "ListItem", "position": 2, "name": nm, "item": canonical},
            ]},
        ],
    }
    ld_tag = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>'

    charted = f" · {fmt(d['cm'], 0)} cm {p['charted']}" if d['stature_basis'] == 'head' else ''
    rows = [
        (p['height'], f"{fmt(d['stature_cm'], 1)} cm · {d['ftin_stature']}" + charted),
        (p['bust'], f"{fmt(d['bust_cm'])} cm · {fmt(d['bust_in'])} in"),
        (p['underbust'], f"{fmt(d['band_cm'])} cm · {fmt(d['band_in'])} in"),
        (p['waist'], f"{fmt(d['waist_cm'])} cm · {fmt(d['waist_in'])} in"),
        (p['hip'], f"{fmt(d['hip_cm'])} cm · {fmt(d['hip_in'])} in"),
        (p['thigh'], f"{fmt(d['thigh_cm'])} cm · {fmt(d['thigh_in'])} in" if d['thigh_cm'] is not None else p['no_thigh']),
        (p['bust_diff'], f"{fmt(d['diff_cm'])} cm · {fmt(d['diff_in'])} in" if d['diff_cm'] is not None else '—'),
        (p['bra'], f"UK {d['uk']} · US {d['us']} · EU {d['eu']}"),
    ]
    rows_html = ''.join(f'<tr><th scope="row">{esc(k)}</th><td>{esc(v)}</td></tr>' for k, v in rows)

    props = [
        (p['waist_hip'], d['whr']), (p['waist_height'], d['whtr']), (p['waist_thigh'], d['wtr']),
        (p['thigh_height'], d['thr']), (p['thigh_hip'], d['thh']), (p['bust_height'], d['bhr']),
        (p['hip_height'], d['hhr']),
    ]
    props_html = ''.join(f'<tr><th scope="row">{esc(k)}</th><td>{fmt(v, 3)}</td></tr>' for k, v in props)

    gallery = []
    gallery.append((f"{prefix}character_images/thumbs/{d['official']}.webp",
                    f"{nm} — {p['official_portrait']}", p['official_portrait']))
    if d.get('skin'):
        skin = d['skin']
        gallery.append((f"{prefix}character_images/{skin['official']}.webp",
                        f"{skin['outfit']} — {p['measured_outfit']}",
                        p['measured_outfit']))
    for it in d['outfits']:
        gallery.append((f"{prefix}character_images/{it['file']}",
                        f"{it['label']} — {p['outfit_portrait']}",
                        f"{it['type']} · {p['art_only']}"))
    gallery_html = ''.join(
        f'<figure><img loading="lazy" decoding="async" src="{esc(src)}" alt="{esc(alt)}">'
        f'<figcaption><b>{esc(alt.split(" — ")[0])}</b>{esc(cap)}</figcaption></figure>'
        for src, alt, cap in gallery)

    sim = similar(d)
    sim_html = ' · '.join(
        f'<a href="{esc(x["slug"])}.html">{esc(x.get(f"name_{lang}") or x["display"])}</a>'
        for x in sim)
    report = (f"{META['repo']}/issues/new?title=" + quote(f"[data] {nm}") +
              "&body=" + quote(f"Character: {nm}\nField: \nCurrent value: \nSource: \n\nWhat looks wrong?\n"))
    src_link = (f"<a href=\"https://zenless-zone-zero.fandom.com/wiki/{quote(d['source_page'].replace(' ', '_'))}\" rel=\"noopener\">"
                f"{esc(d['source_page'])}</a>" if d.get('source_page') else '—')
    measured_note = (f"<p class=\"note\">{p['measured_note'].format(outfit=esc(d['skin']['outfit']))}</p>" if d.get('skin') else '')
    stature_note = (f"<p class=\"note\">{p['stature_note'].format(st=fmt(d['stature_cm'], 1), cm=fmt(d['cm'], 0))}</p>"
                    if d['stature_basis'] == 'head' else '')
    chart_note = ''
    if note and not (d['stature_basis'] == 'head' and d['notes'].lower().startswith('height includes ears')):
        chart_note = f'<p class="note">{esc(p["chart_note"])}: {esc(note)}</p>'
    chart_link = f"{prefix}#p={quote(d['slug'])}&amp;lang={lang}"

    return head(title, desc, canonical, og, ld_tag, prefix=prefix, lang=lang, alts=alts,
                home=prefix, path=page_path) + f'''
<main>
  <section class="hero">
    {hero_picture(d, prefix=prefix, name=nm, alt_word=p['official_portrait'])}
    <div>
      <p class="eyebrow">{esc(p['eyebrow'])}</p>
      <h1>{esc(nm)}</h1>
      {sub}
      <p class="lead">{esc(read)}</p>
      <ul class="chips">
        <li class="chip height">{esc(tags['height'])}</li>
        <li class="chip bust">UK {esc(d['uk'])}</li>
        <li class="chip waist">{esc(p['waist'])} {esc(tags['waist'])}</li>
        <li class="chip hips">{esc(p['hip'])} {esc(tags['hips'])}</li>
        <li class="chip thighs">{esc(p['thigh'])} {esc(tags['thighs'])}</li>
      </ul>
      <p class="meta">{esc(p['height'])} {fmt(d['stature_cm'], 1)} cm{charted} · UK {esc(d['uk'])} / US {esc(d['us'])} / EU {esc(d['eu'])}</p>
      <div class="btns">
        <a class="btn primary" href="{chart_link}">{esc(p['open'])}</a>
        <a class="btn" href="{prefix}data/measurements.json" download>{esc(p['dataset'])}</a>
        <a class="btn" href="{report}" rel="noopener">{esc(p['report'])}</a>
      </div>
    </div>
  </section>

  {stature_note}{measured_note}

  <h2>{esc(p['measurements'])}</h2>
  <table><caption class="small" style="text-align:left;padding-bottom:6px">{esc(p['caption'])}</caption>
    <tbody>{rows_html}</tbody></table>

  <div class="grid2">
    <div><h2>{esc(p['proportions'])}</h2><table><tbody>{props_html}</tbody></table></div>
    <div><h2>{esc(p['percentiles'])}</h2><div class="bars">{pct_bars(d, lang)}</div>
      <p class="small" style="margin-top:10px">{p['pct_note'].format(n=N)}</p></div>
  </div>

  <h2>{esc(p['figure_read'])}</h2>
  <div class="card"><p>{esc(profile_cm)}</p>
    <p class="small" style="margin-top:10px">{esc(p['classes'])}: {esc(p['waist'])} {esc(tags['waist'])} · {esc(p['hip'])} {esc(tags['hips'])} · {esc(p['thigh'])} {esc(tags['thighs'])}{(' · ' + p['hand_pinned']) if d['thigh_pin'] else ''} · {esc(p['shape'])} {esc(tags['shape'])} · {esc(p['build_word'])} {esc(tags['balance'])}{'。' if lang != 'en' else '.'}</p>
    {chart_note}
  </div>

  <h2>{esc(p['outfits'])}</h2>
  <div class="gallery">{gallery_html}</div>

  <h2>{esc(p['provenance'])}</h2>
  <table><tbody>
    <tr><th scope="row">{esc(p['portrait_source'])}</th><td>{src_link}</td></tr>
    <tr><th scope="row">{esc(p['updated'])}</th><td>{META['data_updated']}</td></tr>
    <tr><th scope="row">{esc(p['similar'])}</th><td>{sim_html}</td></tr>
  </tbody></table>

  <nav class="nav" aria-label="{esc(p['roster_nav'])}">
    <div><span>{esc(p['previous'])}</span><br><a href="{esc(prev_d['slug'])}.html">← {esc(prev_d.get(f'name_{lang}') or prev_d['display'])}</a></div>
    <div style="text-align:right"><span>{esc(p['next'])}</span><br><a href="{esc(next_d['slug'])}.html">{esc(next_d.get(f'name_{lang}') or next_d['display'])} →</a></div>
  </nav>
</main>
''' + footer(META['data_updated'], prefix=prefix, lang=lang,
              methodology=(prefix + ('methodology.html' if lang == 'en' else f'{lang}/methodology.html')))

METHOD = {
 'en': {
  'title': 'Methodology, classes and FAQ — ZZZ Female Measurements',
  'desc': 'How the Zenless Zone Zero measurements were taken, how height normalises charted ears, and what the silhouette classes and percentiles mean.',
  'intro': 'A short, honest account of what the chart measures, what it estimates, and how every class and percentile is calculated.',
  'sections': [
   ('Height', 'Charted height comes from official listings and may include ears, footwear or accessories. The UI uses head height where the chart notes an appendage (Miyabi: 170 cm charted, 152.1 cm used). The charted value stays visible as a note; <code>stature_cm</code> remains the comparison field in the exports.'),
   ('Circumferences', 'Bust, under-bust, waist, hip and thigh come from curves wrapped around the official 3D models. Clothing, armour and removed geometry make some readings approximate; the source notes are preserved verbatim.'),
   ('Standard model vs outfit', 'The standard model is canonical, with one exception: Jane Doe\'s canonical entry uses the measured Nocturne of Light outfit. Other measured outfits are separate records with their own numbers and deltas; art-only outfits are never measured and never affect a figure, filter or ranking.'),
   ('Bra sizing', 'The cup group follows the source\'s UK cup letter (A-B, C-D, DD-E, F-G, GG+). UK / US / EU letters are reproduced from the source for comparison, not as a fit recommendation.'),
   ('Classes', 'Waist, hip and thigh classes are roster terciles of the raw circumference in cm. Build compares raw bust and hip percentiles. Shape uses all three circumferences: Hourglass needs bust/waist and hip/waist ≥1.45 with bust and hips within 15%; Straight is flare below 1.30 or bust–hip mismatch over 25%; everything else is Balanced. Thirteen agents are hand-pinned to Thick by curator read and labelled as such.'),
   ('Percentiles', 'Bars show the roster percentile of the raw centimetre measurement, with height using head height. 0 is the smallest value in the set, 50 the midpoint and 100 the largest.'),
   ('Corrections', 'Every character page has a pre-filled “Report an error” link. Corrections are recorded in the changelog, and the dataset carries a schema version and an update date.'),
  ],
  'data_heading': 'Data &amp; exports',
  'data_lead': 'The same numbers power the interactive chart and the static pages. Downloads are versioned by schema v{schema} and dated {date}.',
  'json': 'JSON dataset', 'csv': 'CSV export', 'schema': 'JSON Schema', 'back': 'Back to the chart',
  'faq': [
   ('Where do the numbers come from?', 'Heights come from official listings where available. The remaining circumferences come from curves measured around the official 3D models, so treat every value as an estimate rather than an in-game stat.'),
   ('Why does Miyabi show 170 cm and 152.1 cm?', 'Her charted 170 cm includes her ears. The UI uses the ~152.1 cm head height as Height, while the charted number stays visible as a note and in the exports.'),
   ('Why is the card value the standard model?', 'The standard model is the canonical figure, except Jane Doe, where the measured Nocturne of Light outfit is the only record used. Other measured outfits are stored separately with their own numbers and deltas, so no card or ranking mixes two outfits into one body.'),
   ('What do the silhouette classes mean?', 'Shape uses bust, waist and hips: Hourglass requires both bust/waist and hip/waist ≥1.45 plus a bust–hip balance within 15%; Straight is a flare below 1.30 or a bust–hip mismatch over 25%; the rest is Balanced. Build compares the raw bust and hip percentiles. Waist, hip and thigh classes are roster terciles of their raw circumference.'),
   ('What does hand-pinned mean?', 'A few agents read as visibly thicker or slimmer than a single circumference suggests. Thirteen are marked thick by curator read and labelled hand-pinned in their detail view.'),
   ('How is the cup group calculated?', 'The cup group follows the source\'s UK cup letter (A-B, C-D, DD-E, F-G, GG+). The letter is not a fit recommendation; it is the source\'s sizing label.'),
   ('Can I reuse the data?', 'The measurements are compiled from modelmetrics.net and the character art is © HoYoverse, shown via the ZZZ Fandom wiki as fair use. Link back to the source and respect those rights.'),
  ],
 },
 'ja': {
  'title': '算出方法・分類・FAQ — ZZZ 女性キャラ寸法',
  'desc': 'ゼンレスゾーンゼロの寸法の測り方、耳を含む公式身長の扱い、シルエット分類とパーセンタイルの意味をまとめています。',
  'intro': 'このチャートが何を測っていて、どこが推定なのか。各分類とパーセンタイルの出し方を、できるだけ正直に説明します。',
  'sections': [
   ('身長', '公式身長は公式の表記によるもので、耳・靴・アクセサリーを含むことがあります。耳などの注記がある場合は頭頂ベースを「身長」に使い、公式値は注記として残します（星見雅：公式170cm／表示152.1cm）。書き出しでは <code>stature_cm</code> が比較用の値です。'),
   ('周囲', 'バスト、アンダー、ウエスト、ヒップ、太ももは公式3Dモデルに沿って測った値です。服や鎧、欠けたジオメトリで概算になることがあり、出典の注記はそのまま残しています。'),
   ('標準モデルと衣装', '標準モデルが基本です。例外はジェーン・ドゥで、計測済みの「Nocturne of Light」を正式値にしています。ほかの計測済み衣装は独立した数値と差分を持つ別記録。画像だけの衣装は数値・フィルター・ランキングに影響しません。'),
   ('ブラサイズ', 'カップ区分は出典のUKカップ表記（A-B、C-D、DD-E、F-G、GG+）に沿っています。フィッティングの提案ではなく、出典のサイズ表記です。'),
   ('分類', 'ウエスト、ヒップ、太ももの区分は実寸cmのロスター三分位。体型（Build）はバストとヒップの百分位を比較します。シルエットは3周を使い、砂時計型はバスト/ウエストとヒップ/ウエストが1.45以上、バストとヒップの差が15%以内。直線型はフレア1.30未満またはバストとヒップの差が25%超。それ以外はバランス型です。13名は目視で太めとして手動分類しています。'),
   ('パーセンタイル', 'バーは実寸cmのロスター内パーセンタイル。身長は頭頂ベースです。0が最小、50が中央、100が最大。'),
   ('修正', '各キャラクターページに記入済みの「誤りを報告」リンクがあります。修正は変更履歴に残し、データセットにはスキーマ版と更新日があります。'),
  ],
  'data_heading': 'データと書き出し',
  'data_lead': 'チャートと静的ページは同じ数値を使っています。ダウンロードはスキーマv{schema}、更新日{date}。',
  'json': 'JSONデータ', 'csv': 'CSV書き出し', 'schema': 'JSONスキーマ', 'back': 'チャートに戻る',
  'faq': [
   ('数値の出典は？', '身長は公式の表記がある場合に採用。それ以外の周囲は公式3Dモデルに沿って測った値なので、ゲーム内ステータスではなく推定値として見てください。'),
   ('星見雅が170cmと152.1cmなのはなぜ？', '公式の170cmは耳を含みます。UIでは頭頂ベースの約152.1cmを身長に使い、公式値は注記と書き出しに残しています。'),
   ('カードの数値は標準モデル？', '標準モデルが基本で、ジェーン・ドゥだけは計測済みの「Nocturne of Light」を正式値にしています。ほかの衣装は独立した数値と差分を持ち、カードやランキングでは混ぜません。'),
   ('シルエット分類の意味は？', 'バスト・ウエスト・ヒップの3周を使います。砂時計型はバスト/ウエストとヒップ/ウエストが1.45以上、バストとヒップの差が15%以内。直線型はフレア1.30未満またはバストとヒップの差が25%超。それ以外はバランス型。体型（Build）はバストとヒップの百分位を比べます。'),
   ('手動分類とは？', '数字だけでは厚みが伝わりにくい一部のキャラを、目視で太めに分類しています。13名が該当し、詳細で「手動分類」と表示しています。'),
   ('カップ区分の計算は？', '出典のUKカップ表記（A-B、C-D、DD-E、F-G、GG+）に沿った区分です。フィッティングの提案ではありません。'),
   ('データは再利用できますか？', '計測値はmodelmetrics.net、キャラクター画像は©HoYoverse。ZZZ Fandom wiki経由でフェアユースとして掲載しています。出典へのリンクと権利表示を守ってください。'),
  ],
 },
 'zh': {
  'title': '方法与常见问题 — ZZZ 女性角色测量',
  'desc': '绝区零角色测量数据的来源、官方身高包含耳朵时的处理方式，以及轮廓分类和百分位的含义。',
  'intro': '这份图表量了什么、哪些是估算、每个分类和百分位怎么算——尽量坦白地说清楚。',
  'sections': [
   ('身高', '官方身高来自官方资料，可能包含耳朵、鞋子或配饰。如果图表有相关注记，界面会用头顶高度作为“身高”，官方数字仍保留为注释（星见雅：官方 170cm／显示 152.1cm）。导出数据里的 <code>stature_cm</code> 是对比用字段。'),
   ('围度', '胸围、下胸围、腰围、臀围和大腿围是沿官方 3D 模型量出的曲线。服装、铠甲和缺失的几何体会让部分读数变成估算，来源注记按原文保留。'),
   ('标准模型与服装', '标准模型是默认版本，唯一的例外是简·杜：她的正式记录采用已测量的「Nocturne of Light」服装。其他已测量服装是独立记录，带有自己的数值和差值；仅立绘服装从不参与数值、筛选或排名。'),
   ('内衣尺码', '罩杯分组沿用来源的 UK 罩杯字母（A-B、C-D、DD-E、F-G、GG+）。这不是合身建议，只是来源的尺码标注。'),
   ('分类', '腰围、臀围和大腿分类按厘米实围把全榜三等分。体型（Build）比较胸围和臀围的百分位。轮廓使用三围：沙漏型要求胸围/腰围和臀围/腰围都≥1.45，且胸围与臀围差距在15%以内；直线型是外扩低于1.30，或胸胯差距超过25%；其余为匀称型。有13位角色按视觉判断人工归为“丰满”，并标注为人工分类。'),
   ('百分位', '进度条显示厘米实围在全榜中的百分位，身高按头顶高度计算。0是最小值，50是中位，100是最大值。'),
   ('修正', '每个角色页都有预填好的“报告错误”链接。修正记录在更新日志里，数据集带有 schema 版本和更新日期。'),
  ],
  'data_heading': '数据与导出',
  'data_lead': '交互图表和静态页面使用同一套数据。下载文件的 schema 版本为 v{schema}，更新日期为 {date}。',
  'json': 'JSON 数据集', 'csv': 'CSV 导出', 'schema': 'JSON Schema', 'back': '返回图表',
  'faq': [
   ('这些数字从哪来？', '有官方身高资料时优先采用官方值。其余围度是沿官方 3D 模型量出来的，所以请把它们当作估算，不要当成游戏内数值。'),
   ('为什么星见雅同时显示 170cm 和 152.1cm？', '官方 170cm 包含耳朵。界面把约 152.1cm 的头顶高度作为“身高”，官方数字仍保留在注释和导出数据里。'),
   ('卡片用的是标准模型吗？', '默认是标准模型，只有简·杜例外：她的正式记录采用已测量的「Nocturne of Light」服装。其他已测量服装独立保存，卡片和排名不会把两套服装混在一起。'),
   ('轮廓分类是什么意思？', '用胸围、腰围和臀围三项。沙漏型要求胸围/腰围和臀围/腰围都≥1.45，且胸围与臀围差距在15%以内；直线型是外扩低于1.30，或胸胯差距超过25%；其余为匀称型。体型（Build）比较胸围和臀围的原始百分位。'),
   ('“人工分类”是什么？', '有些角色单看围度数字不够直观，编辑会按视觉判断归为“丰满”。共有13位，详情页会标注“人工分类”。'),
   ('罩杯分组怎么算？', '沿用来源的 UK 罩杯字母（A-B、C-D、DD-E、F-G、GG+）。这不是合身建议，只是来源的尺码标注。'),
   ('数据可以复用吗？', '测量数据整理自 modelmetrics.net，角色立绘©HoYoverse，经由 ZZZ Fandom wiki 以合理使用方式展示。请链接回来源并遵守相关权利。'),
  ],
 },
}


FAQ = [
    ("Where do the numbers come from?",
     "Heights come from official listings where available. The remaining circumferences come from curves measured around the official 3D models, so treat every value as an estimate rather than an in-game stat."),
    ("Why does Miyabi show 170 cm and 152.1 cm?",
     "Her charted 170 cm includes her ears. The UI uses the ~152.1 cm head height as Height, while the charted number stays visible as a note and in the exports."),
    ("Why is the card value the standard model?",
     "The standard model is the canonical figure, except Jane Doe, where the measured Nocturne of Light outfit is the only record used. Other measured outfits are stored separately with their own numbers and deltas, so no card or ranking mixes two outfits into one body."),
    ("What do the silhouette classes mean?",
     "Shape uses bust, waist and hips: Hourglass requires both bust/waist and hip/waist ≥1.45 plus a bust–hip balance within 15%; Straight is a flare below 1.30 or a bust–hip mismatch over 25%; the rest is Balanced. Build compares the raw bust and hip percentiles. Waist, hip and thigh classes are roster terciles of their raw circumference."),
    ("What does hand-pinned mean?",
     "A few agents read as visibly thicker or slimmer than a single circumference suggests. Thirteen are marked thick by curator read and labelled hand-pinned in their detail view."),
    ("How is the cup group calculated?",
     "The cup group follows the source's UK cup letter (A-B, C-D, DD-E, F-G, GG+). The letter is not a fit recommendation; it is the source's sizing label."),
    ("Can I reuse the data?",
     "The measurements are compiled from modelmetrics.net and the character art is © HoYoverse, shown via the ZZZ Fandom wiki as fair use. Link back to the source and respect those rights."),
]


def methodology_page(lang='en'):
    p = PAGE[lang]
    m = METHOD[lang]
    prefix = '' if lang == 'en' else '../'
    path = 'methodology.html'
    canonical = SITE + (f'{lang}/' if lang != 'en' else '') + path
    alts = [
        ('en', SITE + 'methodology.html'),
        ('ja', SITE + 'ja/methodology.html'),
        ('zh-Hans', SITE + 'zh/methodology.html'),
        ('x-default', SITE + 'methodology.html'),
    ]
    faq_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "FAQPage", "@id": canonical + "#faq", "inLanguage": lang,
             "mainEntity": [{"@type": "Question", "name": q,
                             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in m['faq']]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "ZZZ Measurements", "item": SITE},
                {"@type": "ListItem", "position": 2, "name": p['methodology'], "item": canonical},
            ]},
        ],
    }
    ld_tag = '<script type="application/ld+json">' + json.dumps(faq_ld, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>'
    sections = ''.join(f'<section class="card"><h3>{esc(h)}</h3><p>{body}</p></section>' for h, body in m['sections'])
    faq_html = ''.join(f'<dt>{esc(q)}</dt><dd>{esc(a)}</dd>' for q, a in m['faq'])
    home = './' if lang == 'en' else '../'
    methodology = prefix + ('methodology.html' if lang == 'en' else f'{lang}/methodology.html')
    return head(m['title'], m['desc'], canonical, SITE + 'og.png', ld_tag, prefix=prefix,
                lang=lang, alts=alts, home=home, path=path) + f'''
<main>
  <p class="eyebrow">{esc(p['methodology'])}</p>
  <h1>{esc(p['methodology'])}</h1>
  <p class="lead">{esc(m['intro'])}</p>

  <div class="grid2">{sections}</div>

  <h2>{m['data_heading']}</h2>
  <p class="lead">{m['data_lead'].format(schema=META['schema_version'], date=META['data_updated'])}</p>
  <div class="btns">
    <a class="btn primary" href="{prefix}data/measurements.json" download>{esc(m['json'])}</a>
    <a class="btn" href="{prefix}data/measurements.csv" download>{esc(m['csv'])}</a>
    <a class="btn" href="{prefix}data/schema.json" download>{esc(m['schema'])}</a>
  </div>
  <p class="small">{esc(p['rights'])}</p>

  <h2>FAQ</h2>
  <dl class="faq">{faq_html}</dl>

  <div class="btns"><a class="btn primary" href="{home}">{esc(m['back'])}</a></div>
</main>
''' + footer(META['data_updated'], prefix=prefix, lang=lang, methodology=methodology)

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
            "display_ja": d.get('name_ja'), "display_zh": d.get('name_zh'),
            "profile": SITE + f"characters/{d['slug']}.html",
            "profile_ja": SITE + f"ja/characters/{d['slug']}.html",
            "profile_zh": SITE + f"zh/characters/{d['slug']}.html",
            "profile_text": {
                "en": {"cm": d['desc_cm'], "in": d['desc_in'], "read": d['read']},
                "ja": {"cm": d.get('desc_ja_cm'), "in": d.get('desc_ja_in'), "read": d.get('read_ja')},
                "zh": {"cm": d.get('desc_zh_cm'), "in": d.get('desc_zh_in'), "read": d.get('read_zh')},
            },
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
        w = csv.writer(f, lineterminator='\n')
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
                        "display_ja": {"type": ["string", "null"]}, "display_zh": {"type": ["string", "null"]},
                        "profile": {"type": "string", "format": "uri"},
                        "profile_ja": {"type": "string", "format": "uri"},
                        "profile_zh": {"type": "string", "format": "uri"},
                        "profile_text": {"type": "object"},
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
    for lang in ('en', 'ja', 'zh'):
        page_dir = out / 'characters' if lang == 'en' else out / lang / 'characters'
        page_dir.mkdir(parents=True, exist_ok=True)
        (out / 'data').mkdir(parents=True, exist_ok=True)
        for i, d in enumerate(DISPLAY_SORTED):
            prev_d = DISPLAY_SORTED[(i - 1) % N]
            next_d = DISPLAY_SORTED[(i + 1) % N]
            page_html = character_page(d, prev_d, next_d, lang)
            page_html = '\n'.join(line.rstrip() for line in page_html.splitlines()) + '\n'
            (page_dir / f"{d['slug']}.html").write_text(page_html)
        methodology_dir = out if lang == 'en' else out / lang
        method_html = methodology_page(lang)
        method_html = '\n'.join(line.rstrip() for line in method_html.splitlines()) + '\n'
        (methodology_dir / 'methodology.html').write_text(method_html)
    (out / 'offline.html').write_text(OFFLINE)
    (out / 'data' / 'measurements.json').write_text(
        json.dumps(export_json(), indent=1, ensure_ascii=False) + '\n')
    export_csv(out / 'data' / 'measurements.csv')
    (out / 'data' / 'schema.json').write_text(
        json.dumps(schema_doc(), indent=1, ensure_ascii=False) + '\n')
    print(f'pages: {N * 3} character pages + 3 methodology + offline + 3 data files -> {out}')


if __name__ == '__main__':
    main()
