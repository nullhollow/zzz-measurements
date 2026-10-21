#!/usr/bin/env python3
"""Build small WebP thumbs for cards, the table, the podium and character pages.

Full portraits stay in character_images/ for the detail view (1024 px), while
everything that paints on first load uses a 900 px longest-side copy. Sizes are
kept in character_images/thumbs/ so pack_site.py ships them automatically.

Usage: python3 tools/make_thumbs.py [--force]
"""
import os
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'character_images'
OUT = SRC / 'thumbs'
MAX_DIM = 640
QUALITY = 78
FORCE = '--force' in sys.argv


def main():
    OUT.mkdir(exist_ok=True)
    files = sorted(p for p in SRC.glob('*.webp') if p.is_file())
    if not files:
        sys.exit('no source portraits found')
    total_in = total_out = 0
    made = kept = 0
    for src in files:
        dst = OUT / src.name
        total_in += src.stat().st_size
        if not FORCE and dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            total_out += dst.stat().st_size
            kept += 1
            continue
        im = Image.open(src)
        im.load()
        w, h = im.size
        scale = min(1.0, MAX_DIM / max(w, h))
        if scale < 1.0:
            im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        if im.mode not in ('RGB', 'RGBA'):
            im = im.convert('RGBA')
        im.save(dst, 'WEBP', quality=QUALITY, method=6)
        total_out += dst.stat().st_size
        made += 1
    print(f'thumbs: {made} written, {kept} current · '
          f'{total_in/1048576:.1f} MB -> {total_out/1048576:.1f} MB '
          f'({100*(1-total_out/max(1,total_in)):.0f}% smaller)')


if __name__ == '__main__':
    main()
