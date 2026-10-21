#!/usr/bin/env python3
"""Rebuild the bundled subset of the ZZZ UI face (印品鸿蒙体).

    python3 tools/pack_site.py
    python3 tools/subset_zzz_font.py --font /path/to/ZZZ.ttf
    python3 tools/pack_site.py

The source face is commercial (inpin font). Only run this if the site owner has
the necessary web-embedding rights. The script deliberately reads the source
from outside the repository; the original TTF is never committed.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--font', default='/Users/andi/Library/Fonts/ZZZ.ttf')
    args = ap.parse_args()
    src = Path(args.font)
    if not src.exists():
        raise SystemExit(f'source font not found: {src}')
    chars = set()
    for path in list((ROOT / 'docs').rglob('*.html')) + list((ROOT / 'docs/data').glob('*.json')):
        chars.update(path.read_text(errors='ignore'))
    chars.update(chr(c) for r in ((0x20, 0x7f), (0xa0, 0x100), (0x2000, 0x2070),
                                  (0x3000, 0x3100), (0xfe30, 0xfe50), (0xff00, 0xfff0))
                 for c in range(*r))
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.txt', delete=False) as fh:
        fh.write(''.join(sorted(chars)))
        text_file = fh.name
    out = ROOT / 'fonts/ZZZ-Hongmeng-web.woff2'
    cmd = ['pyftsubset', str(src), f'--text-file={text_file}', '--flavor=woff2',
           f'--output-file={out}', '--layout-features=*', '--glyph-names',
           '--symbol-cmap', '--legacy-cmap', '--notdef-glyph', '--notdef-outline',
           '--recommended-glyphs']
    subprocess.run(cmd, check=True)
    Path(text_file).unlink(missing_ok=True)
    print(f'{out}: {out.stat().st_size / 1024:.0f} kB')


if __name__ == '__main__':
    main()
