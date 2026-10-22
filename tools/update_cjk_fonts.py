#!/usr/bin/env python3
"""Subset the existing OFL CJK faces from Google Fonts' full source files.

Run after building changed copy, then repack. Full sources avoid the CSS API's
split unicode-range responses, which can silently yield an incomplete subset.
Requires fonttools[woff]. Sources stay in memory and are never shipped.
"""
from io import BytesIO
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    'jp': 'https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf',
    'zh': 'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf',
    'dela': 'https://raw.githubusercontent.com/google/fonts/main/ofl/delagothicone/DelaGothicOne-Regular.ttf',
}


def used_chars(lang):
    chars = set()
    paths = [*(ROOT / 'docs' / lang).rglob('*.html'), ROOT / 'docs/index.html']
    for path in paths:
        for ch in path.read_text(errors='ignore'):
            o = ord(ch)
            if (0x3000 <= o <= 0x30ff or 0x3400 <= o <= 0x4dbf or
                    0x4e00 <= o <= 0x9fff or 0xff00 <= o <= 0xffef or
                    0xfe30 <= o <= 0xfe4f):
                chars.add(ch)
    return ''.join(sorted(chars))


def write_subset(source, text, out, weight=None):
    font = TTFont(BytesIO(source))
    if weight is not None:
        instantiateVariableFont(font, {'wght': weight}, inplace=True)
    wanted = {ord(ch) for ch in text} & font.getBestCmap().keys()
    options = subset.Options()
    options.flavor = 'woff2'
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=wanted)
    sub.subset(font)
    font.flavor = 'woff2'
    result = BytesIO()
    font.save(result)
    data = result.getvalue()
    actual = TTFont(BytesIO(data)).getBestCmap()
    if not wanted <= actual.keys():
        raise RuntimeError(f'{out}: glyphs lost while subsetting')
    (ROOT / 'fonts' / out).write_bytes(data)
    print(f'{out}: {len(data) / 1024:.0f} kB ({len(wanted)} glyphs)')


if __name__ == '__main__':
    ja, zh = used_chars('ja'), used_chars('zh')
    if not ja or not zh:
        raise SystemExit('build docs/ first; no localized pages found')
    sources = {}
    for key, url in SOURCES.items():
        with urllib.request.urlopen(url, timeout=60) as response:
            sources[key] = response.read()
    write_subset(sources['jp'], ja, 'NotoSansJP-var-jp.woff2', (400, 900))
    write_subset(sources['jp'], ja, 'NotoSansJP-900-jp.woff2', 900)
    write_subset(sources['dela'], ja, 'DelaGothicOne-jp.woff2')
    write_subset(sources['zh'], zh, 'NotoSansSC-var-zh.woff2', (400, 900))
    write_subset(sources['zh'], zh, 'NotoSansSC-900-zh.woff2', 900)
