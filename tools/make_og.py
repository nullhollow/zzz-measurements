#!/usr/bin/env python3
"""Render the social share card (1200x630) from tools/og.html using headless Chrome.

The card is built from the same palette, bundled fonts and character renders as the
site, so it never drifts from the design. Writes og.png at the project root.

Usage: python3 tools/make_og.py
"""
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
W, H = 1200, 630
OUT = ROOT / 'og.png'
STRIP_PAD, GAP, TALL, LEAD = 34, 6, 242, 258


def preflight():
    """Cells size to their art, so make sure the natural widths still fit the strip."""
    html = (ROOT / 'tools/og.html').read_text()
    picks = re.findall(r"\['(\w+)',\s*'([^']+)',\s*'(\d)',\s*'([^']+)'\]", html)
    if not picks:
        sys.exit('could not read PICKS from tools/og.html')
    avail = W - 2 * STRIP_PAD
    total = 0.0
    for slug, label, place, _ in picks:
        im = Image.open(ROOT / 'character_images' / f'{slug}.webp')
        h = LEAD if place == '1' else TALL
        w = h * im.width / im.height
        total += w
        print(f'  {label:11} {w:6.1f} px wide at {h} px tall')
    need = total + GAP * (len(picks) - 1)
    print(f'  {"total":11} {need:6.1f} px  / {avail} px available  ({avail - need:.0f} px spare)')
    if need > avail:
        sys.exit(f'strip overflows by {need - avail:.0f} px: drop a character or lower the heights')


def main():
    if not Path(CHROME).exists():
        sys.exit(f'Chrome not found at {CHROME}')
    preflight()
    tmp = '/tmp/_og_render.png'
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                    '--force-device-scale-factor=1', f'--window-size={W},{H}',
                    '--virtual-time-budget=9000', f'--screenshot={tmp}',
                    (ROOT / 'tools/og.html').as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    im = Image.open(tmp).convert('RGB')
    if im.size != (W, H):
        sys.exit(f'unexpected render size {im.size}')
    im.save(OUT, optimize=True)
    print(f'og.png {W}x{H}  {OUT.stat().st_size/1024:.0f} kB')
    if OUT.stat().st_size > 400_000:
        print('  note: over 400 kB, consider JPEG for the meta tags')


if __name__ == '__main__':
    main()
