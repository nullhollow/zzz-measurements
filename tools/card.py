"""Shared card renderer.

The card markup lives in tools/card.tmpl.html and is used twice:
  * build_html.py renders the roster cards into the initial HTML (works without JS,
    paints before the script runs, keeps the roster in the crawlable document)
  * template.html embeds the same template and re-renders on filter/sort/unit
    changes

Both sides fill the same {{placeholders}}, so the markup cannot drift.
"""
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / 'tools/card.tmpl.html').read_text()
PLACEHOLDERS = set(__import__('re').findall(r'\{\{(\w+)\}\}', TEMPLATE))


def esc(value):
    return html.escape('' if value is None else str(value), quote=True)


def fmt(v, dec=1):
    if v is None:
        return '—'
    s = f'{v:.{dec}f}'
    return s[:-2] if s.endswith('.0') else s


def pct(p):
    return 0 if p is None else round(p * 100)


def height_line(d, unit='cm'):
    head = (f" · {fmt(d['cm'], 2)} cm including horns" if d.get('height_appendage') == 'horns' else f" · {fmt(d['cm'], 0)} charted") if d['stature_basis'] == 'head' else ''
    if unit == 'cm':
        return f"{fmt(d['stature_cm'], d.get('precision_cm',1))} cm · {d['ftin_stature']}{head}"
    return f"{d['ftin_stature']} · {fmt(d['stature_cm'], d.get('precision_cm',1))} cm{head}"


def thumb(d, size=None):
    base = f"character_images/thumbs/{size + '/' if size else ''}{d['official']}.webp"
    return base


def card_sizes(d):
    """CSS width of the art before the imgbox crops it.

    Desktop art is height-driven (height:100%, width:auto), so a wide character
    can render much wider than the 260 px card. Telling the browser the real
    width makes it pick the full 1024 variant on 2x screens instead of upscaling
    the 640 thumb. Phones use a 132x377 box with object-fit:cover.
    """
    ar = d.get('ar') or 0.6
    mobile = max(132, round(ar * 377))
    desktop = max(1, round(ar * 497))
    return f'(max-width:560px) {mobile}px, {desktop}px'


def media(d, sizes, art='official', lazy=True, priority=None):
    """AVIF + WebP <picture> for official art; a plain crop for sheet mode."""
    if art == 'sheet' and d.get('sheet_available',True):
        return (f'<img loading="lazy" decoding="async" src="images/{d["img"]}.webp" '
                f'data-fallback="character_images/{d["official"]}.webp" '
                f'onerror="this.onerror=null;this.src=this.dataset.fallback" alt="">')
    load = ' loading="lazy"' if lazy else ''
    prio = f' fetchpriority="{priority}"' if priority else ''
    slug = d['official']
    base = 'character_images/thumbs'
    dx = f' style="--dx:{d["dx"]}%"' if d.get('dx') is not None else ''
    w320, w640 = d.get('w320', 320), d.get('w640', 640)
    w1024, wfull = d.get('w1024', 1024), d.get('wfull', 1024)
    avif = (f'{base}/avif/320/{slug}.avif {w320}w, '
            f'{base}/avif/{slug}.avif {w640}w, '
            f'{base}/avif/1024/{slug}.avif {w1024}w')
    webp = (f'{base}/320/{slug}.webp {w320}w, '
            f'{base}/{slug}.webp {w640}w, '
            f'character_images/{slug}.webp {wfull}w')
    return (f'<picture>'
            f'<source type="image/avif" srcset="{avif}" sizes="{sizes}">'
            f'<img{load}{prio} decoding="async" src="{base}/{slug}.webp" '
            f'srcset="{webp}" sizes="{sizes}" alt=""{dx}>'
            f'</picture>')


def chips_html(d):
    chips = [
        f'<span class="chip height">{esc(d["tags"]["height"])}</span>',
        f'<span class="chip bust">UK {esc(d["uk"])}</span>',
        f'<span class="chip waist">waist {esc(d["tags"]["waist"])}</span>',
        f'<span class="chip hips">hips {esc(d["tags"]["hips"])}</span>',
    ]
    if d['thigh_cm'] is not None:
        chips.append(f'<span class="chip thighs">thighs {esc(d["tags"]["thighs"])}</span>')
    chips.append(f'<span class="chip shape">{esc(d["tags"]["shape"])}</span>')
    chips.append(f'<span class="chip">{esc(d["tags"]["balance"])}</span>')
    return ''.join(chips)


def values(d, unit='cm', lang='en'):
    """Placeholder values, mirroring cardValues() in template.html."""
    words = {
        'en': ('bust', 'waist', 'hips', 'uk', 'bust', 'waist', 'hip'),
        'ja': ('バスト', 'ウエスト', 'ヒップ', 'UK', 'バスト', 'ウエスト', 'ヒップ'),
        'zh': ('胸围', '腰围', '臀围', 'UK', '胸围', '腰围', '臀围'),
    }[lang]
    unit_suffix = 'cm' if unit == 'cm' else 'in'
    note = f'<div class="note">{esc(d["notes"])}</div>' if d['notes'] else ''
    stick = f'<span class="stick">{esc(d["outfit"] or "variant")}</span>' if d.get('outfit') or d['variant_of'] else ''
    suffix = '_cm' if unit == 'cm' else '_in'
    val = lambda k: fmt(d[k + suffix], d.get('precision_cm',1) if unit=='cm' else 1)  # noqa: E731
    return {
        'name': esc(d['name']),
        'cmpAria': esc(f"Add {d['display']} to comparison"),
        'cmpIco': '+',
        'cmpLbl': 'Compare',
        'href': f"characters/{d['slug']}.html",
        'media': media(d, card_sizes(d)),
        'stick': stick,
        'display': esc(d['display']),
        'heightLine': esc(height_line(d, unit)),
        'pctTitle': esc('Roster percentile of the raw centimetre measurement. 0 = smallest in the cast, 100 = largest.'),
        'bustWord': words[0], 'waistWord': words[1], 'hipWord': words[2],
        'pBust': pct(d['p_bust_cm']), 'pWaist': pct(d['p_waist_cm']), 'pHip': pct(d['p_hip_cm']),
        'bust': val('bust'), 'waist': val('waist'), 'hip': val('hip'),
        'bustLabel': f'{words[4]} {unit_suffix}',
        'waistLabel': f'{words[5]} {unit_suffix}',
        'hipLabel': f'{words[6]} {unit_suffix}',
        'cupValue': esc(d['uk']), 'cupLabel': 'UK',
        'chips': chips_html(d),
        'desc': esc(d['desc_cm'] if unit == 'cm' else d['desc_in']),
        'note': note,
    }


def render_card(d, unit='cm', lang='en'):
    vals = values(d, unit, lang)
    missing = PLACEHOLDERS - set(vals)
    if missing:
        raise SystemExit(f'card.tmpl.html uses unknown placeholders: {sorted(missing)}')
    out = TEMPLATE
    for key, value in vals.items():
        out = out.replace('{{' + key + '}}', str(value))
    return '\n'.join(line.rstrip() for line in out.splitlines())


def render_cards(data, unit='cm'):
    return '\n'.join(render_card(d, unit) for d in data)
