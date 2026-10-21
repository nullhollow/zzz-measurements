#!/usr/bin/env python3
"""Re-download the official portraits at a higher working resolution.

The original PNGs on the Fandom wiki are mostly 1300-1800 px tall. The site
previously capped them at 1024 px; this refetch caps at 1280 px (+25% linear
resolution) and writes the WebP renders used by character pages and the detail
view. Responsive thumbs are regenerated separately with tools/make_thumbs.py.

Usage:
    python3 tools/refetch_images.py [--height 1280] [--force]
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'character_images'
SOURCES = json.loads((OUT / 'sources.json').read_text())
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) zzz-fan-dashboard/1.0 (local archive)'}
ap = argparse.ArgumentParser()
ap.add_argument('--height', type=int, default=1280)
ap.add_argument('--force', action='store_true')
ap.add_argument('--quality', type=int, default=85)
args = ap.parse_args()


def download(url, dst):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r, open(dst, 'wb') as f:
        f.write(r.read())


def encode(src, dst, quality):
    w, h = Image.open(src).size
    cwebp = subprocess.run(['which', 'cwebp'], capture_output=True, text=True).stdout.strip()
    if cwebp:
        cmd = [cwebp, '-quiet', '-q', str(quality), '-m', '6', '-sharp_yuv', '-alpha_q', '100']
        if h > args.height:
            cmd += ['-resize', '0', str(args.height)]
        subprocess.run(cmd + [src, '-o', dst], check=True)
    else:
        im = Image.open(src)
        if h > args.height:
            im = im.resize((round(w * args.height / h), args.height), Image.LANCZOS)
        im.save(dst, 'WEBP', quality=quality, method=6)


def main():
    height = args.height
    made = kept = 0
    for s in SOURCES:
        dst = OUT / s['file'].replace('.png', '.webp')
        if not args.force and dst.exists():
            with Image.open(dst) as im:
                if im.height >= height:
                    kept += 1
                    continue
        with tempfile.TemporaryDirectory() as td:
            png = Path(td) / (Path(s['file']).stem + '.png')
            try:
                download(s['source'], png)
                encode(png, dst, args.quality)
                with Image.open(dst) as im:
                    print(f"{dst.name:24} {s['width']}x{s['height']} -> {im.width}x{im.height}")
                made += 1
            except Exception as e:
                print(f'ERROR {s["file"]}: {e}', file=sys.stderr)
    print(f'official portraits: {made} fetched, {kept} already >= {height}px tall')


if __name__ == '__main__':
    main()
