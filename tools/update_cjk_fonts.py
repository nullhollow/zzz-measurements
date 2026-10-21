#!/usr/bin/env python3
"""Regenerate the bundled Japanese/Chinese WOFF2 subsets.

The site is deliberately self-hosted, so the CJK fonts are subset to the
characters that actually appear in the built pages. Run this after changing any
Japanese or Chinese copy, then run pack_site again:

    python3 tools/pack_site.py
    python3 tools/update_cjk_fonts.py
    python3 tools/pack_site.py

Requires network access to fonts.googleapis.com / fonts.gstatic.com. The four
OFL licence files are kept in fonts/ alongside the binaries.
"""
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36')


def used_chars(lang):
    chars = set()
    paths = list((ROOT / 'docs' / lang).rglob('*.html'))
    if lang in ('ja', 'zh'):
        paths.append(ROOT / 'docs' / 'index.html')
    for path in paths:
        for ch in path.read_text(errors='ignore'):
            o = ord(ch)
            if (0x3000 <= o <= 0x30ff or 0x3400 <= o <= 0x4dbf or
                    0x4e00 <= o <= 0x9fff or 0xff00 <= o <= 0xffef or
                    0xfe30 <= o <= 0xfe4f):
                chars.add(ch)
    return ''.join(sorted(chars))


def fetch(family, text, out):
    query = urllib.parse.quote(text)
    css_url = f'https://fonts.googleapis.com/css2?family={family}&display=swap&text={query}'
    req = urllib.request.Request(css_url, headers={'User-Agent': UA})
    css = urllib.request.urlopen(req, timeout=60).read().decode()
    match = re.search(r'url\((https://[^)]+)\)', css)
    if not match:
        raise RuntimeError(f'no font URL for {family}')
    req = urllib.request.Request(match.group(1), headers={'User-Agent': UA})
    data = urllib.request.urlopen(req, timeout=120).read()
    dest = ROOT / 'fonts' / out
    dest.write_bytes(data)
    print(f'{out}: {len(data) / 1024:.0f} kB ({len(text)} source characters)')


if __name__ == '__main__':
    ja = used_chars('ja')
    zh = used_chars('zh')
    if not ja or not zh:
        raise SystemExit('build docs/ first; no localized pages found')
    fetch('Noto+Sans+JP:wght@400..900', ja, 'NotoSansJP-var-jp.woff2')
    fetch('Noto+Sans+JP:wght@900', ja, 'NotoSansJP-900-jp.woff2')
    fetch('Dela+Gothic+One', ja, 'DelaGothicOne-jp.woff2')
    fetch('Noto+Sans+SC:wght@400..900', zh, 'NotoSansSC-var-zh.woff2')
    fetch('Noto+Sans+SC:wght@900', zh, 'NotoSansSC-900-zh.woff2')
