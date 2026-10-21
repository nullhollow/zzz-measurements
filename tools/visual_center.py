"""Visual-centre toolbox: packs compact alpha masks and computes a reference alignment.

Run:  python3 tools/visual_center.py
Out:  visual-masks.js   window.MASKS      — 4-bit packed alpha per image (works offline, no canvas reads)
      visual-centers.js window.PRECOMPUTED — result of the default parameters per image

Every centring parameter lives in DEFAULTS below and can also be tuned live in
visual-center-demo.html (the JS there implements the same pipeline).
"""
import base64, json, math
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MASK_DIM = 220          # longest side of the stored mask

DEFAULTS = dict(
    # mask & bounds
    alphaSil=24, alphaCore=160, bboxTrim=0.0, bboxMode="silhouette", sparseCols=0.0,
    # torso band & row runs
    bandTop=0.22, bandBottom=0.55, gapFrac=0.012, window=0.76, minRun=0.02, maxRun=1.0,
    pick="widest",
    # weighting / aggregation
    rowWeight="uniform", rowCenter=0.38, rowSigma=0.12, trim=0.08, agg="median",
    # symmetry
    symRadius=0.08, symProfile="mass", symVert="weights", symWidth=0.5, symStep=0.5, symSubpixel=True,
    # gaussian-density ("densest part") method
    denSigma=12.0, denSource="alpha", denRows="all", denMode="column", denPow=6.0, denBlend=0.0,
    # final
    method="torso", blend=0.0, bias=0.0, biasScale=1.0, clamp=40.0,
)


# ---------------------------------------------------------------- mask packing
def pack_mask(im):
    w, h = im.size
    s = MASK_DIM / max(w, h)
    if s < 1:
        im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    a = np.asarray(im.convert('RGBA'))[:, :, 3]
    lvl = (a // 16).astype(np.uint8).reshape(-1)          # 0..15
    if len(lvl) % 2:
        lvl = np.append(lvl, np.uint8(0))
    packed = ((lvl[0::2] << 4) | lvl[1::2]).astype(np.uint8)
    return dict(w=int(im.width), h=int(im.height), data=base64.b64encode(packed.tobytes()).decode('ascii'))


def unpack(mask):
    raw = np.frombuffer(base64.b64decode(mask['data']), dtype=np.uint8)
    px = np.empty(raw.size * 2, dtype=np.uint8)
    px[0::2] = raw >> 4
    px[1::2] = raw & 15
    return (px[: mask['w'] * mask['h']] * 17).reshape(mask['h'], mask['w'])


# ---------------------------------------------------------------- the pipeline
def runs_with_gap(row, gap):
    idx = np.flatnonzero(row)
    if idx.size == 0:
        return []
    out, start, prev = [], idx[0], idx[0]
    for x in idx[1:]:
        if x - prev <= gap:
            prev = x
            continue
        out.append((int(start), int(prev)))
        start = prev = x
    out.append((int(start), int(prev)))
    return out


def _box1d(a, r, axis):
    """O(n) box filter with edge padding (one of the three Gaussian-approximating passes)."""
    if r < 1:
        return a
    n = a.shape[axis]
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r, r)
    cs = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis)
    zeros = list(cs.shape)
    zeros[axis] = 1
    cs = np.concatenate([np.zeros(zeros, cs.dtype), cs], axis=axis)
    lo = np.take(cs, np.arange(0, n), axis=axis)
    hi = np.take(cs, np.arange(2 * r + 1, n + 2 * r + 1), axis=axis)
    return (hi - lo) / (2 * r + 1)


def blur_gaussian(src, sigma):
    """3 box passes per axis ~ Gaussian of the requested sigma."""
    r = max(1, int(round(sigma - 0.5)))
    b = src
    for _ in range(3):
        b = _box1d(b, r, 1)
        b = _box1d(b, r, 0)
    return b


def density_axis(px, P, rows=None, roww=None):
    """Blur the figure into a density field and read the densest column (the 'visual centre')."""
    src = (px > P['alphaCore']).astype(np.float32) if P['denSource'] == 'core' else px.astype(np.float32) / 255.0
    B = blur_gaussian(src, max(0.5, P['denSigma']))
    band = B[rows[0]:rows[1] + 1] if rows else B
    if roww is not None:
        band = band * roww[:, None]
    prof = band.sum(axis=0)
    if prof.sum() <= 0:
        return px.shape[1] / 2
    if P['denMode'] == 'point':
        _, xp = np.unravel_index(np.argmax(band), band.shape)
        base = float(xp)
    elif P['denMode'] == 'centroid':
        w = prof
        return float((np.arange(len(prof)) * w).sum() / w.sum())
    elif P['denMode'] == 'weighted':
        w = prof ** max(0.2, P['denPow'])
        return float((np.arange(len(prof)) * w).sum() / w.sum())
    else:                                    # 'column' — peak of the column profile
        base = float(np.argmax(prof))
    i = int(round(base))
    if 0 < i < len(prof) - 1:
        a, b2, c = prof[i - 1], prof[i], prof[i + 1]
        den = a - 2 * b2 + c
        if den:
            base += 0.5 * (a - c) / den
    return float(base)


def analyse(px, P=None):
    """px: HxW array of alpha (0..255). Returns centres + dx for the chosen method."""
    P = {**DEFAULTS, **(P or {})}
    H, W = px.shape
    sil, core = px > P['alphaSil'], px > P['alphaCore']

    ys, xs = np.nonzero(sil)
    if xs.size == 0:
        return dict(w=W, h=H, bbox_cx=W / 2, torso_cx=W / 2, sym_cx=W / 2,
                    dx={'geometric': 0.0, 'bbox': 0.0, 'torso': 0.0, 'sym': 0.0}, rows=0, band=[0, 0])
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    figH = y1 - y0 + 1

    # ---- bbox centre
    ref = core if P['bboxMode'] == 'core' else sil
    if P['sparseCols'] > 0:
        colmass = ref.sum(axis=0)
        keep = colmass >= P['sparseCols'] * max(1, colmass.max())
        if keep.any():
            kx = np.flatnonzero(keep)
            bx0, bx1 = int(kx.min()), int(kx.max())
        else:
            bx0, bx1 = x0, x1
    else:
        bx0, bx1 = x0, x1
    trim = P['bboxTrim'] * (bx1 - bx0)
    bbox_cx = (bx0 + trim + bx1 - trim) / 2

    # ---- torso band rows
    gap = max(1, int(round(P['gapFrac'] * W)))
    lo, hi = x0 + (1 - P['window']) / 2 * (x1 - x0), x1 - (1 - P['window']) / 2 * (x1 - x0)
    by0 = int(round(y0 + P['bandTop'] * figH))
    by1 = int(round(y0 + P['bandBottom'] * figH))
    yc = y0 + P['rowCenter'] * figH

    centres, weights = [], []
    prev_c = None
    for y in range(by0, by1 + 1):
        cand = [r for r in runs_with_gap(core[y], gap)
                if r[0] >= lo and r[1] <= hi
                and (r[1] - r[0]) >= P['minRun'] * W
                and (r[1] - r[0]) <= P['maxRun'] * W]
        if not cand:
            continue
        if P['pick'] == 'nearest' and prev_c is not None:
            run = min(cand, key=lambda r: abs((r[0] + r[1]) / 2 - prev_c))
        else:
            run = max(cand, key=lambda r: r[1] - r[0])
        c = (run[0] + run[1]) / 2
        prev_c = c
        centres.append(c)
        if P['rowWeight'] == 'width':
            weights.append(run[1] - run[0])
        elif P['rowWeight'] == 'mass':
            weights.append(int(core[y, run[0]:run[1] + 1].sum()))
        elif P['rowWeight'] == 'gaussian':
            weights.append(math.exp(-((y - yc) / max(1e-6, P['rowSigma'] * figH)) ** 2))
        else:
            weights.append(1.0)

    def aggregate(cs, ws):
        cs, ws = np.asarray(cs, float), np.asarray(ws, float)
        if cs.size == 0:
            return bbox_cx
        if P['agg'] == 'mean':
            return float((cs * ws).sum() / ws.sum())
        o = np.argsort(cs)
        cs, ws = cs[o], ws[o]
        cum = np.cumsum(ws) / ws.sum()
        return float(cs[np.searchsorted(cum, 0.5)])

    torso_cx = aggregate(centres, weights)
    if P['trim'] > 0 and len(centres) >= 5:
        keep = [(c, w) for c, w in zip(centres, weights) if abs(c - torso_cx) <= P['trim'] * W]
        if len(keep) >= 5:
            torso_cx = aggregate([k[0] for k in keep], [k[1] for k in keep])

    # ---- symmetry
    prof = np.zeros(W, float)
    band = core[max(0, by0):by1 + 1]
    for i, y in enumerate(range(by0, by1 + 1)):
        w = weights[0] if not weights else 1.0
        if P['symVert'] == 'weights' and centres:
            w = math.exp(-((y - yc) / max(1e-6, P['rowSigma'] * figH)) ** 2) if P['rowWeight'] == 'gaussian' else 1.0
        prof += band[i] * w
    if P['symProfile'] == 'uniform':
        prof = (prof > 0).astype(float)
    xr = np.arange(W)
    mass = prof.sum() or 1.0
    best, best_s = torso_cx, -1.0
    steps = np.arange(torso_cx - P['symRadius'] * W, torso_cx + P['symRadius'] * W + 1e-9, P['symStep'])
    scores = []
    for c in steps:
        mirror = np.rint(2 * c).astype(int) - xr
        ok = (mirror >= 0) & (mirror < W) & (np.abs(xr - c) <= P['symWidth'] * W)
        s = float(np.minimum(prof[ok], prof[mirror[ok]]).sum() / mass)
        scores.append(s)
        if s > best_s:
            best_s, best = s, c
    if P['symSubpixel'] and len(scores) >= 3:
        i = int(np.argmax(scores))
        if 0 < i < len(scores) - 1:
            y0s, y1s, y2s = scores[i - 1], scores[i], scores[i + 1]
            den = (y0s - 2 * y1s + y2s)
            if den != 0:
                best = float(steps[i] + 0.5 * (y0s - y2s) / den * P['symStep'])
    sym_cx = best

    # ---- gaussian-density centre ("densest part")
    sg = max(1e-6, P['rowSigma'] / 100 * figH)
    den_rows, den_roww = None, None
    if P['denRows'] == 'band':
        den_rows = (by0, by1)
    elif P['denRows'] == 'gaussian':
        den_rows = (y0, y1)
        den_roww = np.exp(-(((np.arange(y0, y1 + 1) - yc) / sg) ** 2))
    den_cx = density_axis(px, P, den_rows, den_roww)

    pct = lambda c: (W / 2 - c) / W * 100
    d = {'geometric': 0.0, 'bbox': pct(bbox_cx), 'torso': pct(torso_cx), 'sym': pct(sym_cx),
         'density': pct(den_cx)}
    base = d[P['method']] if P['method'] in d else d['torso']
    if P['method'] == 'blend':
        base = d['torso'] + P['blend'] * (d['sym'] - d['torso'])
    if P['denBlend']:
        base = base * (1 - P['denBlend']) + d['density'] * P['denBlend']
    dx = max(-P['clamp'], min(P['clamp'], base * P['biasScale'] + P['bias']))
    return dict(w=W, h=H, box=[x0, x1, y0, y1], band=[by0, by1], rows=len(centres),
                bbox_cx=round(bbox_cx, 2), torso_cx=round(torso_cx, 2), sym_cx=round(sym_cx, 2),
                den_cx=round(den_cx, 2),
                dx={k: round(v, 2) for k, v in d.items()}, dx_final=round(dx, 2),
                dx_bbox=round(d['bbox'], 2), dx_torso=round(d['torso'], 2), dx_sym=round(d['sym'], 2),
                dx_density=round(d['density'], 2))


def bake(params_file=None):
    """Apply a settings JSON (as copied from visual-center-demo.html) and store the
    resulting dx per image in tools/visual-centers.json + tools/data.json."""
    P, MANUAL = dict(DEFAULTS), {}
    if params_file:
        j = json.load(open(params_file))
        P.update({k: v for k, v in (j.get('params') or {}).items() if k in DEFAULTS})
        MANUAL = j.get('manual') or {}
    data = json.load(open(ROOT / 'tools/data.json'))
    subs = [s for d in data for s in (d.get('std'), d.get('skin')) if s]
    seen, out = set(), {}
    for rec in data + subs:
        slug = rec['official']
        if slug in seen:
            continue
        seen.add(slug)
        m = pack_mask(Image.open(ROOT / 'character_images' / f'{slug}.png'))
        r = analyse(unpack(m), P)
        r['manual'] = round(MANUAL.get(slug, 0), 2)
        r['dx_final'] = round(max(-P['clamp'], min(P['clamp'], r['dx_final'] + r['manual'])), 2)
        out[slug] = r
    json.dump(out, open(ROOT / 'tools/visual-centers.json', 'w'), indent=1)
    for rec in data:
        for r in [rec] + ([rec['skin']] if rec.get('skin') else []):
            r['dx'] = out[r['official']]['dx_final']
    json.dump(data, open(ROOT / 'tools/data.json', 'w'), indent=1)
    print(f"baked {len(out)} offsets with method={P['method']} -> tools/visual-centers.json, tools/data.json")
    for slug, r in sorted(out.items(), key=lambda kv: -abs(kv[1]['dx_final']))[:10]:
        print(f"  {slug:22s} dx {r['dx_final']:+7.2f}%")
    return out


def main():
    data = json.load(open(ROOT / 'tools/data.json'))
    subs = [d['skin'] for d in data if d.get('skin')]
    seen, masks, ref = set(), {}, {}
    for rec in data + subs:
        slug = rec['official']
        if slug in seen:
            continue
        seen.add(slug)
        m = pack_mask(Image.open(ROOT / 'character_images' / f'{slug}.png'))
        masks[slug] = m
        r = analyse(unpack(m))
        r['display'] = rec['display']
        ref[slug] = r

    (ROOT / 'visual-masks.js').write_text('window.MASKS = ' + json.dumps(masks) + ';\n')
    (ROOT / 'visual-centers.js').write_text('window.PRECOMPUTED = ' + json.dumps(ref) + ';\n')
    kb = (ROOT / 'visual-masks.js').stat().st_size / 1024
    print(f'packed {len(masks)} masks -> visual-masks.js ({kb:.0f} KB), reference -> visual-centers.js\n')
    print(f"{'image':22s} {'mask':>9s} {'bbox':>7s} {'torso':>7s} {'sym':>7s} {'dx torso':>9s} {'dx sym':>8s}")
    for slug, r in sorted(ref.items(), key=lambda kv: -abs(kv[1]['dx_torso']))[:16]:
        print(f"{slug:22s} {r['w']:4d}×{r['h']:<4d} {r['bbox_cx']:7.1f} {r['torso_cx']:7.1f} {r['sym_cx']:7.1f}"
              f" {r['dx_torso']:+9.2f} {r['dx_sym']:+8.2f}")


if __name__ == '__main__':
    import sys
    if '--bake' in sys.argv:
        i = sys.argv.index('--bake')
        bake(sys.argv[i + 1] if len(sys.argv) > i + 1 else None)
    else:
        main()
