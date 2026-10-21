#!/usr/bin/env python3
"""Generate the site favicon: the acid tile with a chunky black Z.

Writes favicon.svg (any-modern-browser icon, crisp at every size) and
favicon.ico (16/32/48/64 px fallback for Safari and legacy engines) from one
shared geometry definition, so both stay in sync.

Usage: python3 tools/make_favicon.py
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACID = (216, 250, 0, 255)      # #D8FA00
INK = (11, 11, 12, 255)        # #0B0B0C
SIGNAL = (255, 94, 65, 255)    # #FF5E41
U = 64.0                       # design space
RADIUS = 14.0
Z = [(14, 14), (50, 14), (50, 25), (27, 39), (50, 39), (50, 50),
     (14, 50), (14, 39), (37, 25), (14, 25)]          # chunky Z
NOTCH = [(45, 0), (64, 0), (64, 19)]                   # signal-red corner

SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="ZZZ Measurements">
  <defs>
    <clipPath id="tile"><rect width="64" height="64" rx="14"/></clipPath>
  </defs>
  <rect width="64" height="64" rx="14" fill="#D8FA00"/>
  <g clip-path="url(#tile)">
    <path d="M45 0h19v19z" fill="#FF5E41"/>
  </g>
  <path d="M14 14H50V25L27 39H50V50H14V39L37 25H14Z" fill="#0B0B0C"/>
</svg>
'''


def render(size, ss=8):
    """Draw the tile at size*ss then downscale (smooth edges, rounded corners)."""
    S = size * ss
    k = S / U
    tile = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=RADIUS * k, fill=ACID)
    # red notch, clipped to the tile's rounded silhouette
    layer = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(layer).polygon([(x * k, y * k) for x, y in NOTCH], fill=SIGNAL)
    clipped = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    clipped.paste(layer, (0, 0), tile.split()[3])
    tile = Image.alpha_composite(tile, clipped)
    ImageDraw.Draw(tile).polygon([(x * k, y * k) for x, y in Z], fill=INK)
    return tile.resize((size, size), Image.LANCZOS)


def main():
    open(os.path.join(ROOT, 'favicon.svg'), 'w').write(SVG)
    base = render(256)
    base.save(os.path.join(ROOT, 'favicon.ico'),
              sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    render(512).save(os.path.join(ROOT, 'icon-512.png'))          # manifest / apple-touch icon
    render(192).save(os.path.join(ROOT, 'icon-192.png'))
    print('wrote favicon.svg, favicon.ico, icon-192.png, icon-512.png',
          f"({os.path.getsize(os.path.join(ROOT, 'favicon.svg'))} B / "
          f"{os.path.getsize(os.path.join(ROOT, 'favicon.ico'))} B / "
          f"{os.path.getsize(os.path.join(ROOT, 'icon-512.png'))} B)")


if __name__ == '__main__':
    main()
