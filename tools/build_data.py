"""Turn measurements.csv + the wiki manifests into tools/data.json.

Design rules
  * the standard model is the canonical figure; measured outfits live under
    ``skin`` and never change the base record
  * ``stature_cm`` is the value used for every stature comparison. It equals the
    charted height unless the chart explicitly counts an appendage (Miyabi's
    ears), in which case it falls back to the effective head height
  * every path is resolved from the repository root, so the script runs from
    any working directory
  * schema version and data date come from tools/meta.json
"""
import copy
import csv
import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
META = json.loads((ROOT / 'tools/meta.json').read_text())
CSV_PATH = ROOT / 'measurements.csv'

# column contract — order matters because Bust/Band/Waist/Hip/Thigh repeat in
# inches; the header is still verified so a reshuffled sheet fails loudly
COLUMNS = [
    'Character', 'cm', 'ft',
    'Bust', 'Band', 'Waist', 'Hip', 'Thigh',           # cm
    'Bust', 'Band', 'Waist', 'Hip', 'Thigh',           # in
    'diff (in)', 'diff (cm)', 'UK', 'US', 'EU',
    'Waist-Hip Ratio', 'Waist-height ratio', 'Waist-thigh ratio', 'Thigh-height ratio',
    'Notes', 'Effective height (cm)',
]
REQUIRED = len(COLUMNS) - 2          # notes + effective height are optional


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def ftin(cm):
    """Imperial height rounded to the nearest 0.4 inch (= 1 cm)."""
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
MERGE = list(VARIANT_OF)

# ---------------------------------------------------------------- read sheet
with CSV_PATH.open(newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    try:
        header = next(reader)
    except StopIteration:
        raise SystemExit('measurements.csv is empty')
    if header[:len(COLUMNS)] != COLUMNS:
        raise SystemExit(
            'measurements.csv header changed.\n  expected: ' + ','.join(COLUMNS) +
            '\n  found:    ' + ','.join(header[:len(COLUMNS)]))
    rows = [r for r in reader if r and r[0].strip()]
    for i, row in enumerate(rows, start=2):
        if len(row) < REQUIRED:
            raise SystemExit(f'measurements.csv line {i} ({row[0]}): {len(row)} columns, need {REQUIRED}')

recs = []
for row in rows:
    name = row[0].strip()
    d = dict(
        name=name, display=DISPLAY.get(name, name),
        slug=slug(DISPLAY.get(name, name)),
        img=IMG.get(name, slug(name)),
        official=slug(DISPLAY.get(name, name)),
        variant_of=VARIANT_OF.get(name),
        outfit=OUTFIT.get(name),
        cm=num(row[1]),
        bust_cm=num(row[3]), band_cm=num(row[4]), waist_cm=num(row[5]), hip_cm=num(row[6]),
        thigh_cm=num(row[7]),
        bust_in=num(row[8]), band_in=num(row[9]), waist_in=num(row[10]), hip_in=num(row[11]),
        thigh_in=num(row[12]),
        uk=row[15].strip(), us=row[16].strip(), eu=row[17].strip(),
        notes=row[22].strip() if len(row) > 22 else '',
        # stature that excludes an appendage (Miyabi's ears) when the chart value counts it;
        # every stature comparison uses this, the chart number is never overwritten
        cm_eff=num(row[23]) if len(row) > 23 and row[23].strip() else None,
    )
    d['ftin'] = ftin(d['cm'])
    d['stature_cm'] = d['cm_eff'] if d['cm_eff'] is not None else d['cm']
    d['stature_basis'] = 'head' if d['cm_eff'] is not None else 'charted'
    d['ftin_stature'] = ftin(d['stature_cm'])
    # recompute bust diff from bust - under-bust so it keeps 1 dp (the sheet's
    # own diff columns are whole-number rounded)
    if d['bust_cm'] is not None and d['band_cm'] is not None:
        d['diff_cm'] = round(d['bust_cm'] - d['band_cm'], 1)
        d['diff_in'] = round(d['diff_cm'] / 2.54, 2)
    else:
        d['diff_cm'] = d['diff_in'] = None
    recs.append(d)

by_name = {d['name']: d for d in recs}

# ---------------------------------------------------------------- outfits
# The base record keeps the standard model's numbers. A measured outfit is
# attached as a sub-record with its own values, so nothing on the page mixes
# two outfits into one figure.
for vname in MERGE:
    v, base = by_name[vname], by_name[VARIANT_OF[vname]]
    base['skin'] = copy.deepcopy(v)
    base['merged'] = True

# Art-only outfit renders (no measured data), fetched by tools/fetch_skins.py
SKINS = json.loads((ROOT / 'character_images/skins.json').read_text()) \
    if (ROOT / 'character_images/skins.json').exists() else {}
SOURCES = json.loads((ROOT / 'character_images/sources.json').read_text()) \
    if (ROOT / 'character_images/sources.json').exists() else []
SRC_BY_FILE = {s['file']: s for s in SOURCES}

for d in recs:
    rec = SKINS.get(d['official'] + '.png')
    items = []
    if rec:
        measured = {SRC_BY_FILE.get(d['official'] + '.png', {}).get('wiki_file')}
        if d.get('skin'):
            measured.add(SRC_BY_FILE.get(d['skin']['official'] + '.png', {}).get('wiki_file'))
        for it in rec['items']:
            if it['wiki_file'] in measured:
                continue            # measured outfit lives in the standard / outfit toggle
            items.append({'label': it['label'], 'type': it['type'],
                          'file': it['file'].replace('.png', '.webp')})
    d['outfits'] = items

# ---------------------------------------------------------------- provenance
for d in recs:
    src = SRC_BY_FILE.get(d['official'] + '.png')
    d['source_page'] = src['wiki_page'] if src else None
    d['source_file'] = src['wiki_file'] if src else None
    d['source_url'] = src['source'] if src else None
    if d.get('skin'):
        ssrc = SRC_BY_FILE.get(d['skin']['official'] + '.png')
        d['skin']['source_page'] = ssrc['wiki_page'] if ssrc else None
        d['skin']['source_file'] = ssrc['wiki_file'] if ssrc else None
        d['skin']['source_url'] = ssrc['source'] if ssrc else None

# Jane Doe: the measured Nocturne of Light outfit is the canonical record.
# The standard-model numbers are discarded for this entry, and the nested
# outfit copy is removed so nothing can fall back to the standard body.
jane = by_name.get('Jane Doe')
if jane and jane.get('skin'):
    skin = jane['skin']
    for key in (
        'cm', 'cm_eff', 'stature_cm', 'stature_basis', 'ftin', 'ftin_stature',
        'bust_cm', 'band_cm', 'waist_cm', 'hip_cm', 'thigh_cm',
        'bust_in', 'band_in', 'waist_in', 'hip_in', 'thigh_in',
        'diff_cm', 'diff_in', 'uk', 'us', 'eu',
        'source_page', 'source_file', 'source_url',
    ):
        if key in skin:
            jane[key] = skin[key]
    jane['outfit'] = skin.get('outfit')
    jane['notes'] = ('Measurements use the Nocturne of Light outfit; '
                     'standard-model values are not used.').strip()
    jane.pop('skin', None)
    jane.pop('merged', None)

# Official localized agent names. These are the names used by the official
# HoYoverse character pages, not literal translations of the English display.
LOCALIZED_NAMES = json.loads((ROOT / 'tools/localized_names.json').read_text())
for d in recs:
    loc = LOCALIZED_NAMES.get(d['slug'])
    if loc:
        d['name_ja'] = loc['ja']
        d['name_zh'] = loc['zh']
        if d.get('skin'):
            d['skin']['name_ja'] = loc['ja']
            d['skin']['name_zh'] = loc['zh']

# search aliases: roster key, wiki page title, display name and outfit labels
for d in recs:
    alias = {d['name'], d['display'], d['slug'].replace('_', ' ')}
    if d['source_page']:
        alias.add(d['source_page'])
    if d.get('skin') and d['skin'].get('outfit'):
        alias.add(d['skin']['outfit'])
    if d.get('outfit'):
        alias.add(d['outfit'])
    for it in d['outfits']:
        alias.add(it['label'])
    d['aliases'] = sorted(a for a in alias if a and a.lower() != d['display'].lower())

# confidence: derived from the sheet's own caveats, never invented
for d in recs:
    note = d['notes'].lower()
    missing = d['thigh_cm'] is None
    if 'impossible' in note or missing:
        d['confidence'] = 'partial'
        d['confidence_note'] = 'At least one measurement is missing or unreadable.'
    elif 'approximat' in note or 'tbc' in note:
        d['confidence'] = 'estimated'
        d['confidence_note'] = 'The sheet marks at least one value as approximated or pending.'
    else:
        d['confidence'] = 'charted'
        d['confidence_note'] = 'No approximation is flagged in the source note.'

# ---------------------------------------------------------------- ratios
for d in recs:
    w, h = Image.open(ROOT / 'character_images' / (d['official'] + '.webp')).size
    d['ar'] = round(w / h, 3)

roster = [d for d in recs if d['name'] not in MERGE]          # 48 displayed cards
subs = [d['skin'] for d in roster if d.get('skin')]
allrecs = roster + subs


def add_ratios(d):
    d['whr'] = round(d['waist_cm'] / d['hip_cm'], 3) if d['waist_cm'] and d['hip_cm'] else None
    d['whtr'] = round(d['waist_cm'] / d['stature_cm'], 3) if d['waist_cm'] and d['stature_cm'] else None
    d['wtr'] = round(d['waist_cm'] / d['thigh_cm'], 3) if d['waist_cm'] and d['thigh_cm'] else None
    d['thr'] = round(d['thigh_cm'] / d['stature_cm'], 3) if d['thigh_cm'] and d['stature_cm'] else None
    d['thh'] = round(d['thigh_cm'] / d['hip_cm'], 3) if d['thigh_cm'] and d['hip_cm'] else None
    d['bhr'] = round(d['bust_cm'] / d['stature_cm'], 3) if d['bust_cm'] and d['stature_cm'] else None
    d['hhr'] = round(d['hip_cm'] / d['stature_cm'], 3) if d['hip_cm'] and d['stature_cm'] else None


for d in allrecs:
    add_ratios(d)


def pct_rank(values, v):
    vals = sorted(x for x in values if x is not None)
    n = len(vals)
    below = sum(1 for x in vals if x < v)
    return (below + 0.5 * sum(1 for x in vals if x == v)) / n


PCT_KEYS = ['bust_cm', 'waist_cm', 'hip_cm', 'thigh_cm', 'whr', 'bhr', 'hhr', 'stature_cm']
lists = {k: [d[k] for d in roster] for k in PCT_KEYS}   # reference = the 48 displayed entries
for d in allrecs:
    for k in PCT_KEYS:
        d['p_' + k] = round(pct_rank(lists[k], d[k]), 3) if d[k] is not None else None


def cup_group(uk):
    """Group by the UK cup letter, the same ordering used for ranking."""
    letter = re.sub(r'^\d+', '', (uk or '')).upper()
    if letter in ('AA', 'A', 'B'):
        return 'A-B'
    if letter in ('C', 'D'):
        return 'C-D'
    if letter in ('DD', 'E'):
        return 'DD-E'
    if letter in ('F', 'FF', 'G'):
        return 'F-G'
    if letter:
        return 'GG+'
    return '?'


def height_group(cm):
    if cm < 150:
        return 'Petite'
    if cm <= 165:
        return 'Mid'
    return 'Tall'


def level(p, lo=0.33, hi=0.66):
    if p is None:
        return 'avg'
    if p < lo:
        return 'low'
    if p > hi:
        return 'high'
    return 'avg'


def add_groups(d):
    d['cup_group'] = cup_group(d['uk'])
    d['height_group'] = height_group(d['stature_cm'])
    d['waist_level'] = level(d['p_waist_cm'])     # raw waist cm terciles
    d['hip_level'] = level(d['p_hip_cm'])         # raw hip cm terciles
    bp, hp = d['p_bust_cm'], d['p_hip_cm']
    bal = (bp - hp) if (bp is not None and hp is not None) else 0
    d['balance'] = 'top' if bal > 0.18 else ('bottom' if bal < -0.18 else 'even')
    # Shape uses all three circumferences, not WHR alone.
    #   flare  = min(bust/waist, hip/waist): both curves must clear the waist
    #   balance= min(bust,hip)/max(bust,hip): bust and hips must be comparable
    # Hourglass needs a strong flare on both sides and a balanced bust/hip pair.
    # Straight is a weak flare or a strongly top/bottom-heavy pair; the rest is
    # Balanced. hourglass_score ranks the continuous version of the same idea.
    b, w, h = d['bust_cm'], d['waist_cm'], d['hip_cm']
    if b and w and h:
        flare = min(b / w, h / w)
        balance = min(b, h) / max(b, h)
        d['hourglass_score'] = round(flare * balance, 3)
        if flare >= 1.45 and balance >= 0.85:
            d['shape'] = 'Hourglass'
        elif flare < 1.30 or balance < 0.75:
            d['shape'] = 'Straight'
        else:
            d['shape'] = 'Balanced'
    else:
        d['hourglass_score'] = None
        d['shape'] = 'Balanced'


for d in allrecs:
    add_groups(d)

# thigh class: raw-circumference tercile plus curator pins. The pins exist
# because a single circumference cannot express a visual read, and the site
# labels every pinned entry in its detail view.
THIGH_PIN = {'Rina', 'Yidhari', 'Caesar', 'Velina', 'Yanagi', 'Pulchra', 'Astra Yao',
             'Sigrid', 'Jane Doe', 'Trigger', 'Cissia', 'Burnice', 'Orphie'}
for d in allrecs:
    d['thigh_pin'] = bool(d['name'] in THIGH_PIN or d.get('variant_of') in THIGH_PIN)
    if d['thigh_cm'] is not None:
        d['thigh_level'] = 'high' if d['thigh_pin'] else level(d['p_thigh_cm'])
    else:
        d['thigh_level'] = 'avg'

# ---------------------------------------------------------------- visual centres
# Optional values produced by tools/visual_center.py --bake
centres = ROOT / 'tools/visual-centers.json'
if centres.exists():
    C = json.loads(centres.read_text())
    for d in roster:
        for r in [d] + ([d['skin']] if d.get('skin') else []):
            if r['official'] in C:
                r['dx'] = C[r['official']]['dx_final']
    print('injected visual-centre dx for', len(C), 'images')

# ---------------------------------------------------------------- output
out = ROOT / 'tools/data.json'
out.write_text(json.dumps(roster, indent=1, ensure_ascii=False) + '\n')
print(f'wrote data.json (schema {META["schema_version"]}): {len(roster)} entries')
print(f'  canonical basis: standard model; Jane Doe uses her measured outfit · '
      f'other measured outfits kept separately: '
      f'{", ".join(d["display"] for d in roster if d.get("merged"))}')
print(f'  stature overrides: '
      f'{", ".join(f"{d["display"]} {d["cm"]:g}→{d["stature_cm"]:g}" for d in roster if d["stature_basis"] == "head") or "none"}')
_nsk = sum(1 for d in roster if d['outfits'])
_nimg = sum(len(d['outfits']) for d in roster)
print(f'  outfit art without measured data: {_nimg} renders across {_nsk} characters')
print(f'  confidence: ' + ', '.join(f'{k}={sum(1 for d in roster if d["confidence"] == k)}'
                                  for k in ('charted', 'estimated', 'partial')))
print('  hand-pinned thick: ' + ', '.join(sorted(d['display'] for d in roster if d['thigh_pin'])))
