import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

data = json.load(open(ROOT/'tools/data.json'))
by_key = {d['name']: d for d in data}

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
  'high': "a fuller midsection relative to height",
}
HIP_WORD   = {'low':"compact",'avg':"average-width",'high':"wide"}
THIGH_WORD = {'low':"slim",'avg':"average",'high':"thick"}

def rankword(p):
    if p is None: return "unranked"
    if p >= 0.85: return f"top {max(1, round((1-p)*100))}% of the roster"
    if p <= 0.15: return f"bottom {max(1, round(p*100))}% of the roster"
    return "mid-pack for the roster"

def thigh_word(z):
    if z is None: return "average"
    if z >= 0.75: return "full"
    if z >= 0.25: return "slightly full"
    if z <= -0.75: return "slim"
    if z <= -0.25: return "slightly slim"
    return "average"

def describe(d, unit, compare=None):
    cmu = (unit == 'cm')
    word = 'cm' if cmu else 'in'

    def v(in_key, cm_key, dec=1):
        raw = d[cm_key] if cmu else d[in_key]
        if raw is None: return '—'
        s = f"{raw:.{dec}f}".rstrip('0').rstrip('.')
        return f"{s} {word}"

    n = d['display']; cmv = d['cm']; ft = d.get('ftin') or d['ft']
    hg = d['height_group']
    frame = {
        'Petite': f"{n} measures just {cmv:g} cm ({ft}), one of the most compact frames on the chart.",
        'Tall':   f"{n} is one of the tallest figures on the chart at {cmv:g} cm ({ft}).",
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
    bal = {'top': "The chest carries noticeably more visual weight than the hips",
           'bottom': "The hips carry more visual weight than the chest",
           'even': "Chest and hips are fairly evenly matched"}[d['balance']]
    shape = (f"The result is a {d['shape'].lower()} silhouette (waist-to-hip {d['whr']:.2f}): {bal}.")
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
    if d['notes']:
        parts.append(f"Chart note: {d['notes']}.")
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
    # merged outfit entries keep two sub-records (standard model + skin), each
    # with its own text/tags for the detail-view toggle
    for key, cmp_ in (('std', None), ('skin', d.get('std'))):
        s = d.get(key)
        if not s: continue
        s['desc_cm'] = describe(s, 'cm', compare=cmp_)
        s['desc_in'] = describe(s, 'in', compare=cmp_)
        s.pop('desc', None)
        s['tags'] = build_tags(s)
        s['read'] = read_line(s)

json.dump(data, open(ROOT/'tools/data.json','w'), indent=1)
print('descriptions written (cm + in)\n')
for d in data[:2] + [by_key['Rina'], by_key['Jane Doe']['skin']]:
    print('*', d['display'], '· CM:')
    print(' ', d['desc_cm'])
    print(' · IN:')
    print(' ', d['desc_in'])
    print()
