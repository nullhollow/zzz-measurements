#!/usr/bin/env python3
"""Build the responsive artwork set used by cards, the table and the podium.

For every portrait in character_images/ this writes five files under thumbs/:

    <slug>.webp                 640 px longest side, WebP q78
    320/<slug>.webp             320 px longest side, WebP q76
    avif/<slug>.avif            640 px longest side, AVIF q60
    avif/320/<slug>.avif        320 px longest side, AVIF q60
    avif/1024/<slug>.avif       1024 px longest side, AVIF q60
    avif/1280/<slug>.avif       full 1280 px source, AVIF q60

AVIF is used first (roughly 35% smaller); WebP is the fallback. The 1024 set is
what 2x desktop cards and character-page heroes pick, so they stay sharp instead
of upscaling a 640 px thumb. The original 1024 px WebP stays in character_images/
as the largest WebP fallback and for the detail view.

Usage: python3 tools/make_thumbs.py [--force]
"""
import os
import sys
from pathlib import Path
from PIL import Image, features

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'character_images'
OUT = SRC / 'thumbs'
WEBP640 = OUT
WEBP320 = OUT / '320'
AVIF640 = OUT / 'avif'
AVIF320 = AVIF640 / '320'
AVIF1024 = AVIF640 / '1024'
AVIF1280 = AVIF640 / '1280'
FORCE = '--force' in sys.argv
AVIF = features.check('avif')


def resize(im, longest):
    w, h = im.size
    scale = min(1.0, longest / max(w, h))
    if scale >= 1.0:
        return im.copy()
    return im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)


def encode(im, dst, fmt, quality):
    if fmt == 'WEBP':
        im.save(dst, 'WEBP', quality=quality, method=6)
    else:
        im.save(dst, 'AVIF', quality=quality, speed=6)


def make(src, targets):
    if not FORCE and all(p.exists() and p.stat().st_mtime >= src.stat().st_mtime for p in targets):
        return False
    im = Image.open(src)
    im.load()
    if im.mode not in ('RGB', 'RGBA'):
        im = im.convert('RGBA')
    avif = src.stem + '.avif'
    targets = [
        (WEBP640 / src.name, 640, 'WEBP', 78),
        (WEBP320 / src.name, 320, 'WEBP', 76),
    ]
    if AVIF:
        targets += [(AVIF640 / avif, 640, 'AVIF', 60), (AVIF320 / avif, 320, 'AVIF', 60),
                    (AVIF1024 / avif, 1024, 'AVIF', 60),
                    (AVIF1280 / avif, 1280, 'AVIF', 60)]
    for path, longest, fmt, q in targets:
        encode(resize(im, longest), path, fmt, q)
    return True


def main():
    for d in (WEBP320, AVIF640, AVIF320, AVIF1024, AVIF1280):
        d.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in SRC.glob('*.webp') if p.is_file())
    if not files:
        sys.exit('no source portraits found')
    made = kept = 0
    for src in files:
        avif = src.stem + '.avif'
        targets = [WEBP640 / src.name, WEBP320 / src.name]
        if AVIF:
            targets += [AVIF640 / avif, AVIF320 / avif, AVIF1024 / avif, AVIF1280 / avif]
        if make(src, targets):
            made += 1
        else:
            kept += 1
    if not AVIF:
        print('warning: Pillow has no AVIF support; avif/ files were not written')
    total = sum(p.stat().st_size for p in OUT.rglob('*.webp')) + \
        sum(p.stat().st_size for p in OUT.rglob('*.avif'))
    src_total = sum(p.stat().st_size for p in files)
    print(f'thumbs: {made} written, {kept} current · '
          f'{src_total/1048576:.1f} MB sources -> {total/1048576:.1f} MB responsive set')


if __name__ == '__main__':
    main()
