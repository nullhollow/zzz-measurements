#!/usr/bin/env python3
"""
Extract per-character portrait tiles from zzz3.2b.webp.

Fixes the "broken hair" bug: the name-label bounding box previously extended
from the text down into the character's hair (light gray hair passes the
"bright, low saturation" text test), and the eraser then overwrote hair pixels.

Now:
  * only the FIRST vertical run of text rows is used as the label (multi-line
    labels are merged only when the line gap is <= 20 px),
  * the eraser mask is a plain color test (bright gray / dark shadow),
  * tiles are centred on the character's own content inside its 250 px cell.
"""
from pathlib import Path
from PIL import Image
import numpy as np, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from optimize_images import convert as convert_to_webp
import json

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / 'zzz3.2b.webp'
OUT = ROOT / 'images'

NAMES = ["Zhao","Ju Fufu","Soukaku","Sunna","Roxy","Aria","Aria (construct)","Norma",
"Koleda","Lucy","Nangong Yu","Dialyn","Piper","Corin","Nekomata","Qingyi","Seed","Yuzuha",
"Miyabi","Vivian","Belle","Anby","Soldier 11","Lucia","Promeia","Claret","Ellen Joe","Alice",
"Ye Shunguang","Orphie","Burnice","Cissia","Nicole","Trigger","Jane Doe","Zhu Yuan","Sigrid",
"Astra Yao","Evelyn","Remielle","Pulchra","Yi Xuan","Yanagi","Grace","Velina","Caesar","Yidhari","Rina"]

def slug(n):
    return n.lower().replace(' ', '_').replace('(', '').replace(')', '')

im = Image.open(SHEET).convert('RGB')
a = np.asarray(im).astype(int).copy()
H, W = a.shape[:2]

# ---------- 1. locate name labels ----------
band = a[180:420]
band_mx = band.max(axis=2); band_mn = band.min(axis=2)
text_px = (band_mn > 115) & ((band_mx - band_mn) < 45)
colsum = text_px.sum(axis=0)
cs = np.convolve(colsum, np.ones(11) / 11, 'same')
clusters = []; in_c = False
for x in range(len(cs)):
    if cs[x] > 0.5 and not in_c: start = x; in_c = True
    elif cs[x] <= 0.5 and in_c: clusters.append((start, x)); in_c = False
merged = []
for x0, x1 in clusters:
    if merged and x0 - merged[-1][1] < 45: merged[-1][1] = x1
    else: merged.append([x0, x1])
labels = []
for x0, x1 in merged:
    if x1 - x0 < 20: continue
    rowsum = text_px[:, x0:x1].sum(axis=1)
    ys = np.where(rowsum > 1)[0]
    if not len(ys): continue
    # first contiguous run only (gap > 20 px starts a new object, e.g. hair)
    runs = []; s = ys[0]; p = ys[0]
    for y in ys[1:]:
        if y - p > 20: runs.append((s, p)); s = y
        p = y
    runs.append((s, p))
    ty0, ty1 = runs[0]
    labels.append((x0, x1, 180 + ty0, 180 + ty1))
assert len(labels) == len(NAMES), f'found {len(labels)} labels, expected {len(NAMES)}'

# ---------- 2. erase the label text (text only, never hair) ----------
sat = a.max(axis=2) - a.min(axis=2)
mn_all = a.min(axis=2)
gray_bg = (mn_all > 52) & (mn_all < 100) & (sat < 16)
PAD = 6
patched = 0
for x0, x1, y0, y1 in labels:
    rx0, rx1 = max(0, x0 - PAD), min(W, x1 + PAD)
    ry0, ry1 = max(0, y0 - PAD), min(H, y1 + PAD)
    rmn = mn_all[ry0:ry1, rx0:rx1]; rsat = sat[ry0:ry1, rx0:rx1]
    # bright glyphs + their dark outline only
    m = ((rmn > 88) | (rmn < 63)) & (rsat < 30)
    if not m.any(): continue
    best = None
    for s in [25, -25, 50, -50, 75, -75, 100, -100, 125, -125, 150, -150, 175, -175, 200, -200]:
        sx0, sx1 = rx0 + s, rx1 + s
        if sx0 < 0 or sx1 > W: continue
        d = ((~gray_bg[ry0:ry1, sx0:sx1]) & m).sum()
        if best is None or d < best[1]: best = (s, d)
    s = best[0]
    src = a[ry0:ry1, rx0 + s:rx1 + s].copy()
    dirty = (~gray_bg[ry0:ry1, rx0 + s:rx1 + s]) & m
    src[dirty] = [68, 68, 68]
    reg = a[ry0:ry1, rx0:rx1]
    reg[m] = src[m]
    patched += int(m.sum())
print(f'text pixels erased: {patched}')

# ---------- 3. crop tiles ----------
mx2 = a.max(axis=2); mn2 = a.min(axis=2)
objmask = ((mx2 - mn2) > 25) | (mx2 > 105) | (mx2 < 45)
Y0, Y1, TW = 245, 742, 260
OUT.mkdir(exist_ok=True)
tiles = {}
for n, (x0, x1, y0, y1) in zip(NAMES, labels):
    c = (x0 + x1) // 2
    # content centroid limited to this character's own 250 px cell
    cx0, cx1 = max(0, c - 125), min(W, c + 125)
    sub = objmask[Y0:Y1, cx0:cx1]
    xs = np.where(sub.sum(axis=0) > 3)[0]
    bcx = cx0 + (xs.min() + xs.max()) // 2 if len(xs) else c
    center = c + max(-15, min(15, bcx - c))
    left = max(0, min(center - TW // 2, W - TW))
    tile = OUT / f'{slug(n)}.png'
    Image.fromarray(a.astype(np.uint8)).crop((left, Y0, left + TW, Y1)).save(tile)
    try: convert_to_webp(str(tile))
    except Exception as e: print('  webp conversion failed:', e)
    tiles[slug(n)] = {"name": n, "left": int(left), "y0": Y0, "y1": Y1, "w": TW,
                      "label": [int(x0), int(x1), int(y0), int(y1)]}
json.dump(tiles, open(ROOT / 'tools/tiles.json', 'w'), indent=1)
print(f'saved {len(NAMES)} tiles -> {OUT}')
