import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

data = json.load(open(ROOT/'tools/data.json'))
by_key = {d['name']: d for d in data}
# stature baseline for the profile text, using head height where the chart counts an appendage
ROSTER_AVG = sum(d['stature_cm'] for d in data) / len(data)
# rank by stature (1 = tallest) so the "tallest" claim matches the actual chart position;
# tied statures share the better rank, hence the "among the tallest" wording for the top group
_HEIGHTS = [d['stature_cm'] for d in data]
H_TOTAL = len(data)
H_RANK = {d['name']: 1 + sum(1 for x in _HEIGHTS if x > d['stature_cm']) for d in data}


def ordinal(n):
    if 10 <= n % 100 <= 20: suf = 'th'
    else: suf = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suf}"

def rel_bust(p):
    if p is None: return "hard to place"
    if p >= 0.85: return "among the largest bust measurements on the chart"
    if p >= 0.66: return "clearly above the roster average"
    if p >= 0.34: return "close to the roster average"
    if p >= 0.15: return "on the modest side for the chart"
    return "among the smallest bust measurements here"

CUP_PHRASE = {
  'A-B':  "a modest A–B tier",
  'C-D':  "a middle-of-the-road C–D tier",
  'DD-E': "a full DD–E tier",
  'F-G':  "a heavy F–G tier",
  'GG+':  "one of the chart's heaviest GG+ tiers",
}
WAIST_PHRASE = {
  'low': "one of the trimmer midsections in the set",
  'avg': "a middling midsection by this set's standards",
  'high': "a fuller midsection than most of the roster",
}
HIP_WORD   = {'low':"compact",'avg':"average-width",'high':"wide"}
THIGH_WORD = {'low':"slim",'avg':"average",'high':"thick"}

def rankword(p):
    if p is None: return "unranked"
    if p >= 0.85: return f"top {max(1, round((1-p)*100))}% of the roster"
    if p <= 0.15: return f"bottom {max(1, round(p*100))}% of the roster"
    return "mid-pack for the roster"

def describe(d, unit, compare=None):
    cmu = (unit == 'cm')
    word = 'cm' if cmu else 'in'

    def v(in_key, cm_key, dec=1):
        raw = d[cm_key] if cmu else d[in_key]
        if raw is None: return '—'
        s = f"{raw:.{dec}f}".rstrip('0').rstrip('.')
        return f"{s} {word}"

    n = d['display']; cmv = d['cm']; ft = d.get('ftin')
    hg = d['height_group']
    if d['stature_basis'] == 'head':
        gap = d['stature_cm'] - ROSTER_AVG
        where = 'just under' if gap < -2 else ('above' if gap > 2 else 'right around')
        frame = (f"{n} is charted at {cmv:g} cm ({ft}), but that figure counts her ears: at head height "
                 f"she stands about {d['stature_cm']:g} cm ({d['ftin_stature']}), {where} the roster average.")
    elif hg == 'Tall':
        r = H_RANK.get(d.get('variant_of') or d['name'], H_TOTAL)
        if r <= 3:
            frame = f"{n} is among the tallest figures on the chart at {cmv:g} cm ({ft})."
        elif r <= 8:
            frame = (f"{n} is one of the taller figures here, {ordinal(r)} tallest of {H_TOTAL}, "
                     f"at {cmv:g} cm ({ft}).")
        else:
            frame = (f"{n} measures {cmv:g} cm ({ft}), above the roster average at "
                     f"{ordinal(r)} tallest of {H_TOTAL}.")
    else:
        frame = {
            'Petite': f"{n} measures just {cmv:g} cm ({ft}), one of the most compact frames on the chart.",
            'Mid':    f"{n} measures {cmv:g} cm ({ft}), right around the roster average.",
        }[hg]
    bust = f"Her {v('bust_in','bust_cm')} bust (UK {d['uk']}) is {rel_bust(d['p_bust_cm'])}."
    waist = (f"The waist comes in at {v('waist_in','waist_cm')} (waist-to-height {d['whtr']:.2f}), "
             f"{WAIST_PHRASE[d['waist_level']]}.")
    if d['thigh_cm'] is not None:
        hips = (f"Below that, {HIP_WORD[d['hip_level']]} hips ({v('hip_in','hip_cm')}) pair with "
                f"{THIGH_WORD[d['thigh_level']]} {v('thigh_in','thigh_cm')} thighs "
                f"({rankword(d['p_thigh_cm'])} by thigh circumference).")
    else:
        hips = (f"Below that, hips read {HIP_WORD[d['hip_level']]} at {v('hip_in','hip_cm')}; "
                f"no reliable thigh measurement exists for her.")
    b, h = d['bust_cm'], d['hip_cm']
    balance_text = ("The chest carries noticeably more visual weight than the hips" if b > h * 1.10
                    else "The hips carry more visual weight than the chest" if h > b * 1.10
                    else "Chest and hips are fairly evenly matched")
    bw = b / d['waist_cm'] if b and d['waist_cm'] else 0
    hw = h / d['waist_cm'] if h and d['waist_cm'] else 0
    bhi = min(b, h) / max(b, h)
    shape = (f"The result is a {d['shape'].lower()} silhouette "
             f"(bust/waist {bw:.2f}, hip/waist {hw:.2f}, bust–hip balance {bhi*100:.0f}%): {balance_text}.")
    parts = [frame, bust, waist, hips, shape]
    if compare is None and d.get('variant_of'):
        compare = by_key.get(d['variant_of'])
    if compare is not None:
        b = compare
        if cmu:
            dB = (d['bust_cm'] or 0) - (b['bust_cm'] or 0)
            dW = (d['waist_cm'] or 0) - (b['waist_cm'] or 0)
            dH = (d['hip_cm'] or 0) - (b['hip_cm'] or 0)
            u = 'cm'
        else:
            dB = d['bust_in'] - b['bust_in']
            dW = d['waist_in'] - b['waist_in']
            dH = d['hip_in'] - b['hip_in']
            u = 'in'
        if max(abs(dB), abs(dW), abs(dH)) >= (1.2 if cmu else 0.5):
            parts.append(f"Versus her standard model this outfit reads {dB:+.1f} {u} bust, "
                         f"{dW:+.1f} {u} waist, {dH:+.1f} {u} hips.")
    notes = d['notes']
    if d['stature_basis'] == 'head' and notes.lower().startswith('height includes ears'):
        notes = ''          # already spelled out in the first sentence
    if notes:
        parts.append(f"Chart note: {notes}.")
    return ' '.join(parts)

BALANCE_WORD = {'top': "top-heavy", 'bottom': "bottom-heavy", 'even': "balanced"}


def read_line(d):
    """One short, symbol-friendly sentence: the same commentary the prose carries, compressed."""
    frame = {'Petite': "compact", 'Mid': "mid-height", 'Tall': "tall"}[d['height_group']]
    bits = []
    if d['p_bust_cm'] is not None:
        if d['p_bust_cm'] >= 0.7: bits.append("full bust")
        elif d['p_bust_cm'] <= 0.3: bits.append("modest bust")
    if d['p_waist_cm'] is not None:
        if d['p_waist_cm'] >= 0.7: bits.append("full waist")
        elif d['p_waist_cm'] <= 0.3: bits.append("trim waist")
    if d['p_hip_cm'] is not None:
        if d['p_hip_cm'] >= 0.7: bits.append("wide hips")
        elif d['p_hip_cm'] <= 0.3: bits.append("narrow hips")
    if d['thigh_cm'] is not None:
        if d['p_thigh_cm'] is not None and d['p_thigh_cm'] >= 0.66: bits.append("thick thighs")
        elif d['p_thigh_cm'] is not None and d['p_thigh_cm'] <= 0.33: bits.append("slim thighs")
    line = f"{frame} frame"
    if bits:
        line += " with " + ", ".join(bits)
    line += f". {d['shape']} silhouette, {BALANCE_WORD[d['balance']]} build."
    return line


def build_tags(d):
    return {
        'height': d['height_group'],
        'bust': d['cup_group'],
        'waist': {'low':'Cinched','avg':'Average','high':'Fuller'}[d['waist_level']],
        'hips': HIP_WORD[d['hip_level']].capitalize(),
        'thighs': (THIGH_WORD[d['thigh_level']].capitalize() if d['thigh_cm'] is not None else 'n/a'),
        'shape': d['shape'],
        'balance': {'top':'Top-heavy','bottom':'Bottom-heavy','even':'Balanced'}[d['balance']],
    }

for d in data:
    d['desc_cm'] = describe(d, 'cm')
    d['desc_in'] = describe(d, 'in')
    d.pop('desc', None)
    d['tags'] = build_tags(d)
    d['read'] = read_line(d)
    # an outfit variant keeps its own text and tags; it is always compared
    # against the standard model that owns it
    s = d.get('skin')
    if s:
        s['desc_cm'] = describe(s, 'cm', compare=d)
        s['desc_in'] = describe(s, 'in', compare=d)
        s.pop('desc', None)
        s['tags'] = build_tags(s)
        s['read'] = read_line(s)

json.dump(data, open(ROOT/'tools/data.json','w'), indent=1, ensure_ascii=False)
print('descriptions written (cm + in)\n')
samples = data[:2] + [by_key['Rina']]
for d in data:
    if d.get('skin'):
        samples.append(d['skin'])
        break
for d in samples:
    print('*', d['display'], '· CM:')
    print(' ', d['desc_cm'])
    print(' · IN:')
    print(' ', d['desc_in'])
    print()
