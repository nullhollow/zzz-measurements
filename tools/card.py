"""Shared card renderer.

The card markup lives in tools/card.tmpl.html and is used twice:
  * build_html.py renders the 48 cards into the initial HTML (works without JS,
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
    if d['stature_basis'] == 'head':
        return f"{fmt(d['cm'], 0)} cm chart · {fmt(d['stature_cm'], 0)} cm head"
    return (f"{fmt(d['cm'], 0)} cm · {d['ftin']}" if unit == 'cm'
            else f"{d['ftin']} · {fmt(d['cm'], 0)} cm")


def thumb(d):
    return f"character_images/thumbs/{d['official']}.webp"


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
    stick = f'<span class="stick">{esc(d["outfit"] or "variant")}</span>' if d['variant_of'] else ''
    dx = ''
    if d.get('dx') is not None:
        dx = f' style="--dx:{d["dx"]}%"'
    suffix = '' if unit == 'cm' else '_in'
    val = lambda k: fmt(d[k + suffix])  # noqa: E731
    return {
        'name': esc(d['name']),
        'cmpAria': esc(f"Add {d['display']} to comparison"),
        'href': f"characters/{d['slug']}.html",
        'thumb': thumb(d),
        'dx': dx,
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
        'uk': esc(d['uk']),
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
    return out


def render_cards(data, unit='cm'):
    return '\n'.join(render_card(d, unit) for d in data)
