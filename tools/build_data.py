import csv, json, math, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def num(x):
    try: return float(x)
    except: return None

rows = []
with open(ROOT/'measurements.csv', newline='', encoding='utf-8') as f:
    r = csv.reader(f); next(r)
    for row in r:
        if not row or not row[0].strip(): continue
        rows.append(row)

def ftin(cm):
    """Imperial height rounded to the nearest 0.4 inch (= 1 cm), e.g. 173 cm -> 5'8"."""
    if cm is None:
        return None
    ti = round(cm / 2.54 / 0.4) * 0.4
    ft = int(ti // 12)
    inch = ti - ft * 12
    if abs(inch - 12) < 0.05:
        ft, inch = ft + 1, 0.0
    txt = f"{inch:.1f}".rstrip("0").rstrip(".")
    return f"{ft}\'{txt or 0}\""


def slug(n):
    return n.lower().replace(' ', '_').replace('(', '').replace(')', '')

IMG = {                       # sheet-crop slug (images/)
    'Soldier11': 'soldier_11',
    'Aria bot': 'aria_construct',
    'Lucy (swimsuit)': 'lucy',
    'Vivian (swimsuit)': 'vivian',
    'Belle (summer)': 'belle',
    'Jane Doe (skin)': 'jane_doe',
}
DISPLAY = {
    'Soldier11': 'Soldier 11',
    'Aria bot': 'Aria (Construct)',
    'Lucy (swimsuit)': 'Lucy (Swimsuit)',
    'Vivian (swimsuit)': 'Vivian (Swimsuit)',
    'Belle (summer)': 'Belle (Summer)',
    'Jane Doe (skin)': 'Jane Doe (Skin)',
}
VARIANT_OF = {
    'Lucy (swimsuit)': 'Lucy',
    'Vivian (swimsuit)': 'Vivian',
    'Belle (summer)': 'Belle',
    'Jane Doe (skin)': 'Jane Doe',
}
OUTFIT = {                    # official skin names (matches character_images/ files)
    'Lucy (swimsuit)': 'Princess on Holiday',
    'Vivian (swimsuit)': 'Iris of the Shore',
    'Belle (summer)': 'Summer Skies',
    'Jane Doe (skin)': 'Nocturne of Light',
}
# outfit rows folded into their base entry (one card, outfit toggle in the detail view)
MERGE = ['Lucy (swimsuit)', 'Vivian (swimsuit)', 'Belle (summer)', 'Jane Doe (skin)']
MEAS_KEYS = ['cm','bust_cm','band_cm','waist_cm','hip_cm','thigh_cm',
             'bust_in','band_in','waist_in','hip_in','thigh_in','diff_in','diff_cm']

recs = []
for row in rows:
    name = row[0].strip()
    d = dict(
        name=name, display=DISPLAY.get(name, name),
        img=IMG.get(name, slug(name)),
        official=slug(DISPLAY.get(name, name)),
        variant_of=VARIANT_OF.get(name),
        outfit=OUTFIT.get(name),
        cm=num(row[1]), ft=row[2],
        bust_cm=num(row[3]), band_cm=num(row[4]), waist_cm=num(row[5]), hip_cm=num(row[6]),
        thigh_cm=num(row[7]),
        bust_in=num(row[8]), band_in=num(row[9]), waist_in=num(row[10]), hip_in=num(row[11]),
        thigh_in=num(row[12]),
        diff_in=num(row[13]), diff_cm=num(row[14]),   # diff_in kept below: exact conversion from cm
        uk=row[15], us=row[16], eu=row[17],
        notes=row[22].strip() if len(row) > 22 else '',
        # stature that excludes an appendage (Miyabi's ears) when the chart value counts it;
        # drives the profile text and the height class, never the measurement columns
        cm_eff=num(row[23]) if len(row) > 23 and row[23].strip() else None,
    )
    d['ftin'] = ftin(d['cm'])
    d['ftin_eff'] = ftin(d['cm_eff'])
    # the sheet's own diff columns are whole-number rounded (Velina 26 cm vs 25.5 real);
    # recompute from bust - under-bust so the value keeps its 1 dp precision
    d['diff_in_csv'], d['diff_cm_csv'] = d['diff_in'], d['diff_cm']
    if d['bust_cm'] is not None and d['band_cm'] is not None:
        d['diff_cm'] = round(d['bust_cm'] - d['band_cm'], 1)
        d['diff_in'] = round(d['diff_cm'] / 2.54, 2)
    recs.append(d)

# ---- merge outfit variants into their base entry ----
# One card per character. The card/table/filter/sort profile uses the LARGER value
# of standard vs outfit for every measurement; the detail view keeps both sets and
# lets you toggle between them.
by_name = {d['name']: d for d in recs}
for vname in MERGE:
    v, base = by_name[vname], by_name[VARIANT_OF[vname]]
    base['std'] = dict(base)          # standard model, untouched copy
    base['skin'] = v                  # outfit variant record
    base['merged'] = True
    for k in MEAS_KEYS:
        if v[k] is not None and (base[k] is None or v[k] > base[k]):
            base[k] = v[k]
    if (v['diff_in'] is not None and (base['std']['diff_in'] is None or v['diff_in'] > base['std']['diff_in'])):
        base['uk'], base['us'], base['eu'] = v['uk'], v['us'], v['eu']

# ---- official outfit renders with no measured data (art-only skins) ----
# Fetched from Category:Outfits on the Fandom wiki by tools/fetch_skins.py. These
# never touch the numbers: they only show up as extra art in the detail view.
SKINS = json.load(open('character_images/skins.json')) if os.path.exists('character_images/skins.json') else {}
SRC_WIKI = {s['file']: s['wiki_file'] for s in json.load(open('character_images/sources.json'))}
for d in recs:
    rec = SKINS.get(d['official'] + '.png')
    items = []
    if rec:
        measured = {SRC_WIKI.get(d[k]['official'] + '.png') for k in ('std', 'skin') if k in d}
        measured.add(SRC_WIKI.get(d['official'] + '.png'))
        for it in rec['items']:
            if it['wiki_file'] in measured:
                continue            # measured outfit: lives in the standard / outfit data toggle
            items.append({'label': it['label'], 'type': it['type'],
                           'file': it['file'].replace('.png', '.webp')})
    d['outfits'] = items

# ---- render aspect ratios (lets the podium scale its art to fill the card) ----
from PIL import Image as _Image
for d in recs:
    _p = ROOT / 'character_images' / (d['official'] + '.webp')
    if _p.exists():
        _w, _h = _Image.open(_p).size
        d['ar'] = round(_w / _h, 3)

roster = [d for d in recs if d['name'] not in MERGE]          # 51 chart entries
subs = [s for d in roster for s in (d.get('std'), d.get('skin')) if s]
allrecs = roster + subs

def add_ratios(d):
    d['whr']  = round(d['waist_cm']/d['hip_cm'], 3) if d['waist_cm'] and d['hip_cm'] else None
    d['whtr'] = round(d['waist_cm']/d['cm'], 3) if d['waist_cm'] and d['cm'] else None
    d['wtr']  = round(d['waist_cm']/d['thigh_cm'], 3) if d['waist_cm'] and d['thigh_cm'] else None
    d['thr']  = round(d['thigh_cm']/d['cm'], 3) if d['thigh_cm'] and d['cm'] else None
    d['thh']  = round(d['thigh_cm']/d['hip_cm'], 3) if d['thigh_cm'] and d['hip_cm'] else None
    d['bhr']  = round(d['bust_cm']/d['cm'], 3) if d['bust_cm'] and d['cm'] else None
    d['hhr']  = round(d['hip_cm']/d['cm'], 3) if d['hip_cm'] and d['cm'] else None
for d in allrecs: add_ratios(d)

def pct_rank(values, v):
    vals = sorted(x for x in values if x is not None)
    n = len(vals)
    below = sum(1 for x in vals if x < v)
    return (below + 0.5*sum(1 for x in vals if x == v)) / n

PCT_KEYS = ['bhr','hhr','whtr','thr','thh','whr','cm','diff_in','bust_cm','hip_cm','waist_cm','thigh_cm']
lists = {k: [d[k] for d in roster] for k in PCT_KEYS}   # reference = the 51 displayed entries
for d in allrecs:
    for k in PCT_KEYS:
        d['p_'+k] = round(pct_rank(lists[k], d[k]), 3) if d[k] is not None else None

def cup_group(diff):
    if diff is None: return '?'
    if diff <= 2: return 'A-B'
    if diff <= 4: return 'C-D'
    if diff <= 6: return 'DD-E'
    if diff <= 8: return 'F-G'
    return 'GG+'

def height_group(cm):
    if cm < 150: return 'Petite'
    if cm <= 165: return 'Mid'
    return 'Tall'

def level(p, lo=0.33, hi=0.66):
    if p is None: return 'avg'
    if p < lo: return 'low'
    if p > hi: return 'high'
    return 'avg'

def add_groups(d):
    d['cup_group'] = cup_group(d['diff_in'])
    d['height_group'] = height_group(d['cm_eff'] or d['cm'])
    d['bust_level'] = level(d['p_bust_cm'])       # raw bust cm terciles
    d['waist_level'] = level(d['p_waist_cm'])     # raw waist cm terciles
    d['hip_level'] = level(d['p_hip_cm'])         # raw hip cm terciles
    d['whr_level'] = level(d['p_whr'])
    bp, hp = d['p_bust_cm'], d['p_hip_cm']
    bal = (bp - hp) if (bp is not None and hp is not None) else 0
    d['balance'] = 'top' if bal > 0.18 else ('bottom' if bal < -0.18 else 'even')
    d['shape'] = ('Hourglass' if d['whr'] is not None and d['p_whr'] < 0.33
                  else 'Straight' if d['whr'] is not None and d['p_whr'] > 0.66
                  else 'Balanced')
for d in allrecs: add_groups(d)

# ---- thigh thickness class: composite of two normalised indices ----
# Hand-pinned entries: characters the curator reads as thick even though the
# normalised ratios land mid-pack (no single score reproduces this list).
# Applied by base name; variants of a pinned character inherit the class.
THIGH_PIN = {'Rina','Yidhari','Caesar','Velina','Yanagi','Pulchra','Astra Yao',
             'Sigrid','Jane Doe','Trigger','Cissia','Burnice','Orphie'}
# Absolute thigh girth is height-confounded (r≈0.71 here), so it is normalised twice:
#   frame  = thigh / height  -> stature-relative girth
#   pelvis = thigh / hip     -> silhouette-relative girth
# Both are converted to z-scores over the roster, averaged, and the composite is
# re-standardised to unit spread; Slim / Thick sit beyond ±0.5 SD of the roster mean.
def _ms(vals):
    m = sum(vals)/len(vals)
    return m, math.sqrt(sum((x-m)**2 for x in vals)/(len(vals)-1))

tmp = [d for d in roster if d['thr'] is not None and d['thh'] is not None]
m1, s1 = _ms([d['thr'] for d in tmp])
m2, s2 = _ms([d['thh'] for d in tmp])
raw = {d['name']: (((d['thr']-m1)/s1) + ((d['thh']-m2)/s2))/2 for d in tmp}
mz, sz = _ms(list(raw.values()))
for d in allrecs:
    d['thigh_pin'] = bool(d['name'] in THIGH_PIN or (d.get('variant_of') in THIGH_PIN))
    if d['thr'] is not None and d['thh'] is not None:
        d['thigh_z1'] = round((d['thr']-m1)/s1, 2)   # frame z
        d['thigh_z2'] = round((d['thh']-m2)/s2, 2)   # pelvis z
        z = ((((d['thr']-m1)/s1) + ((d['thh']-m2)/s2))/2 - mz)/sz
        d['thigh_z'] = round(z, 2)                    # composite z
        d['thigh_level'] = level(d['p_thigh_cm'])     # raw thigh circumference terciles
        if d['thigh_pin']:
            d['thigh_level'] = 'high'
    else:
        d['thigh_z1'] = d['thigh_z2'] = d['thigh_z'] = None
        d['thigh_level'] = 'avg'
tz = [d['thigh_z'] for d in roster]
for d in allrecs:
    d['p_thigh'] = round(pct_rank(tz, d['thigh_z']), 3) if d['thigh_z'] is not None else None

# ---- visual-centre offsets (optional: produced by tools/visual_center.py --bake) ----
centres = ROOT/'tools/visual-centers.json'
if centres.exists():
    C = json.load(open(centres))
    for d in roster:
        for r in [d] + [d[k] for k in ('std','skin') if k in d]:
            if r['official'] in C:
                r['dx'] = C[r['official']]['dx_final']
    print('injected visual-centre dx for', len(C), 'images')

json.dump(roster, open(ROOT/'tools/data.json','w'), indent=1)
print(f'wrote data.json: {len(roster)} entries (merged: {", ".join(MERGE)})')
_nsk = sum(1 for d in roster if d['outfits']); _nimg = sum(len(d['outfits']) for d in roster)
print(f'  outfit art, no measured data: {_nimg} renders across {_nsk} characters')
print('thigh reference (n=%d): thigh/height %.4f±%.4f · thigh/hip %.4f±%.4f' % (len(tmp), m1, s1, m2, s2))
print('hand-pinned thick: ' + ', '.join(sorted(d['display'] for d in roster if d['thigh_pin'])))
for vname in MERGE:
    b = by_name[VARIANT_OF[vname]]
    print(f"merged {b['display']:16s} {b['bust_cm']:5.1f}/{b['waist_cm']:5.1f}/{b['hip_cm']:5.1f} cm"
          f"  (std {b['std']['bust_cm']:5.1f}/{b['std']['waist_cm']:5.1f}/{b['std']['hip_cm']:5.1f}"
          f" · {b['skin']['outfit']} {b['skin']['bust_cm']:5.1f}/{b['skin']['waist_cm']:5.1f}/{b['skin']['hip_cm']:5.1f})")
