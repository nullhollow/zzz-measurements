#!/usr/bin/env python3
"""Convert the dashboard's PNG artwork to WebP with cwebp.

Rules
  * height capped at 1024 px (never enlarged; wider than tall images keep their
    aspect, so a 2128x1332 render becomes 1636x1024)
  * quality 85 by default (override with --quality N)
  * -m 6 (slowest/best search), -sharp_yuv (keeps line-art edges crisp on the
    flat anime fills), -alpha_q 100 (alpha plane stays exact, verified 0 delta)

Usage
  python3 tools/optimize_images.py                 # convert what is missing
  python3 tools/optimize_images.py --quality 82    # try another setting
  python3 tools/optimize_images.py --force         # re-encode everything
  python3 tools/optimize_images.py --prune         # delete the source PNGs after
  python3 tools/optimize_images.py --report        # only print current saving
"""
import os, subprocess, sys
from PIL import Image

QUALITY = 85
MAX_H = 1024
FORCE = '--force' in sys.argv
PRUNE = '--prune' in sys.argv
REPORT = '--report' in sys.argv
if '--quality' in sys.argv:
    QUALITY = int(sys.argv[sys.argv.index('--quality') + 1])

DIRS = ['character_images', 'character_images/skins', 'images']


def convert(src, q=QUALITY, max_h=MAX_H):
    """png -> webp next to it; returns (dst, size_bytes) or (None, 0)."""
    dst = src[:-4] + '.webp'
    w, h = Image.open(src).size
    args = ['cwebp', '-quiet', '-q', str(q), '-m', '6', '-sharp_yuv', '-alpha_q', '100']
    if h > max_h:
        args += ['-resize', '0', str(max_h)]        # never upscales: only when taller
    args += [src, '-o', dst]
    subprocess.run(args, check=True)
    return dst, os.path.getsize(dst)


def main():
    pngs, done, skipped, before, after = [], 0, 0, 0, 0
    for d in DIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if not os.path.isfile(p):
                continue
            if f.lower().endswith('.png'):
                pngs.append(p)
            elif f.lower().endswith('.webp'):
                after += os.path.getsize(p)
    before = sum(os.path.getsize(p) for p in pngs)
    print(f'source PNGs: {len(pngs)} ({before/1048576:.1f} MB) | existing webp: {after/1048576:.1f} MB')
    if REPORT:
        return
    for p in pngs:
        dst = p[:-4] + '.webp'
        if not FORCE and os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(p):
            skipped += 1
            continue
        _, sz = convert(p)
        done += 1
        orig = os.path.getsize(p)
        im = Image.open(dst)
        print(f'  {os.path.relpath(p):52} {orig/1024:7.1f} kB -> {sz/1024:6.1f} kB  '
              f'{im.width}x{im.height}')
    out = 0
    for d in DIRS:
        for f in os.listdir(d) if os.path.isdir(d) else []:
            if f.lower().endswith('.webp'):
                out += os.path.getsize(os.path.join(d, f))
    print(f'converted {done}, skipped {skipped} | webp total {out/1048576:.1f} MB '
          f'({100*(1-out/before):.1f}% smaller than the PNGs)')
    if PRUNE:
        removed = kept = 0
        for p in pngs:
            w = p[:-4] + '.webp'
            if os.path.exists(w) and os.path.getsize(w) > 0:
                os.remove(p); removed += 1
            else:                       # never delete a PNG without its webp
                kept += 1
        print(f'pruned {removed} source PNGs' + (f' (kept {kept}: no webp)' if kept else ''))


if __name__ == '__main__':
    main()
