#!/usr/bin/env python3
"""Validate the data and the packed site.

    python3 tools/validate.py                      # checks docs/
    python3 tools/validate.py --site-url https://.../ --out docs

Exits non-zero on the first category with problems, printing every finding.
Designed for CI after tools/pack_site.py.
"""
import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from pack_site import link_check  # noqa: E402

DATA = json.loads((ROOT / 'tools/data.json').read_text())
META = json.loads((ROOT / 'tools/meta.json').read_text())
N = len(DATA)
errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def close(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


# ---------------------------------------------------------------- data model
def check_data(out):
    names, slugs = set(), set()
    for d in DATA:
        for key in ('name', 'display', 'slug', 'aliases', 'cm', 'stature_cm', 'stature_basis',
                    'bust_cm', 'band_cm', 'waist_cm', 'hip_cm', 'uk', 'us', 'eu',
                    'confidence', 'tags', 'desc_cm', 'desc_in', 'read'):
            if key not in d:
                err(f'{d.get("display", "?")}: missing field {key}')
        if d.get('name') in names:
            err(f'duplicate name {d.get("name")}')
        if d.get('slug') in slugs:
            err(f'duplicate slug {d.get("slug")}')
        names.add(d.get('name'))
        slugs.add(d.get('slug'))
        if not re.fullmatch(r'[a-z0-9_]+', d.get('slug', '')):
            err(f'{d.get("display")}: slug is not url-safe: {d.get("slug")}')
        if d.get('stature_basis') == 'head':
            if d.get('stature_cm') != d.get('cm_eff'):
                err(f'{d["display"]}: head stature must equal cm_eff')
        elif d.get('stature_cm') != d.get('cm'):
            err(f'{d["display"]}: stature should equal charted height')
        if d.get('confidence') not in ('charted', 'estimated', 'partial'):
            err(f'{d["display"]}: bad confidence {d.get("confidence")}')
        if d.get('stature_cm') and not (100 <= d['stature_cm'] <= 220):
            err(f'{d["display"]}: implausible stature {d["stature_cm"]}')
        # arithmetic
        if d.get('bust_cm') is not None and d.get('band_cm') is not None:
            if not close(d['diff_cm'], d['bust_cm'] - d['band_cm'], 0.051):
                err(f'{d["display"]}: bust diff {d["diff_cm"]} != {d["bust_cm"] - d["band_cm"]:.2f}')
        for cm_key, in_key in (('bust_cm', 'bust_in'), ('band_cm', 'band_in'), ('waist_cm', 'waist_in'),
                               ('hip_cm', 'hip_in'), ('thigh_cm', 'thigh_in')):
            if d.get(cm_key) is not None and d.get(in_key) is not None:
                if not close(d[in_key], d[cm_key] / 2.54, 0.06):
                    err(f'{d["display"]}: {in_key} {d[in_key]} != {d[cm_key] / 2.54:.2f}')
        ratios = {
            'whr': d['waist_cm'] / d['hip_cm'] if d['waist_cm'] and d['hip_cm'] else None,
            'whtr': d['waist_cm'] / d['stature_cm'] if d['waist_cm'] and d['stature_cm'] else None,
            'thr': d['thigh_cm'] / d['stature_cm'] if d['thigh_cm'] and d['stature_cm'] else None,
            'thh': d['thigh_cm'] / d['hip_cm'] if d['thigh_cm'] and d['hip_cm'] else None,
        }
        for k, v in ratios.items():
            if v is not None and not close(d.get(k), v, 0.0015):
                err(f'{d["display"]}: {k} {d.get(k)} != {v:.4f}')
        expected_hg = 'Petite' if d['stature_cm'] < 150 else ('Mid' if d['stature_cm'] <= 165 else 'Tall')
        if d.get('height_group') != expected_hg:
            err(f'{d["display"]}: height_group {d.get("height_group")} != {expected_hg}')
        for pk in ('p_bust_cm', 'p_waist_cm', 'p_hip_cm', 'p_whr', 'p_stature_cm'):
            if d.get(pk) is not None and not (0 <= d[pk] <= 1):
                err(f'{d["display"]}: {pk} out of range')
        # tags mirror the computed classes
        if d.get('tags', {}).get('height') != expected_hg:
            err(f'{d["display"]}: tags.height mismatch')
        if d.get('tags', {}).get('shape') != d.get('shape'):
            err(f'{d["display"]}: tags.shape mismatch')
        if d.get('notes') and ('<' in d['notes'] or '>' in d['notes']):
            warn(f'{d["display"]}: note contains angle brackets')
        for it in d.get('outfits', []):
            if not it.get('label') or not it.get('file'):
                err(f'{d["display"]}: malformed art-only outfit')
        if d.get('skin'):
            s = d['skin']
            if s.get('outfit') is None:
                err(f'{d["display"]}: measured outfit has no name')
            if s.get('bust_cm') is None or s.get('waist_cm') is None:
                err(f'{d["display"]}: measured outfit is missing numbers')
        for a in d.get('aliases', []):
            if not isinstance(a, str) or not a.strip():
                err(f'{d["display"]}: empty alias')

    if N != 48:
        warn(f'roster count is {N} (was 48 when the copy was written)')
    if META.get('schema_version') != 2:
        err('meta.schema_version must be 2')
    try:
        date.fromisoformat(META.get('data_updated', ''))
    except ValueError:
        err('meta.data_updated must be YYYY-MM-DD')
    # export count agrees with the roster
    exp = out / 'data/measurements.json'
    if exp.exists():
        try:
            blob = json.loads(exp.read_text())
            if len(blob.get('characters', [])) != N:
                err(f'export count {len(blob.get("characters", []))} != roster {N}')
            if blob.get('meta', {}).get('schema_version') != META['schema_version']:
                err('export schema version mismatch')
        except json.JSONDecodeError as e:
            err(f'measurements.json is not valid JSON: {e}')
    # CSV rows
    csvp = out / 'data/measurements.csv'
    if csvp.exists():
        with csvp.open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        if len(rows) != N:
            err(f'CSV has {len(rows)} rows, expected {N}')
        missing = [r['slug'] for r in rows if not r.get('profile')]
        if missing:
            err(f'CSV rows without profile URL: {missing[:3]}')


# ---------------------------------------------------------------- assets
def check_assets(out):
    for d in DATA:
        for rel in (f"images/{d['img']}.webp", f"character_images/{d['official']}.webp",
                    f"character_images/thumbs/{d['official']}.webp",
                    f"character_images/thumbs/320/{d['official']}.webp",
                    f"character_images/thumbs/avif/{d['official']}.avif",
                    f"character_images/thumbs/avif/320/{d['official']}.avif",
                    f"character_images/thumbs/avif/1024/{d['official']}.avif"):
            if not (ROOT / rel).exists():
                err(f'missing source asset {rel}')
        if d.get('skin'):
            if not (ROOT / f"character_images/{d['skin']['official']}.webp").exists():
                err(f'{d["display"]}: missing measured outfit art')
        for it in d['outfits']:
            if not (ROOT / 'character_images' / it['file']).exists():
                err(f'{d["display"]}: missing outfit art {it["file"]}')
        page = out / 'characters' / f"{d['slug']}.html"
        if not page.exists():
            err(f'missing character page {page.relative_to(out)}')
            continue
        html = page.read_text()
        if d['display'] not in html:
            err(f'{d["slug"]}: page does not name the character')
        if 'application/ld+json' not in html:
            err(f'{d["slug"]}: page has no JSON-LD')
        if 'rel="canonical"' not in html:
            err(f'{d["slug"]}: page has no canonical URL')
    # exports & crawler files
    for rel in ('index.html', 'methodology.html', 'offline.html', 'sw.js', '404.html',
                'robots.txt', 'sitemap.xml', 'manifest.webmanifest', '.nojekyll',
                'data/measurements.json', 'data/measurements.csv', 'data/schema.json'):
        if not (out / rel).exists():
            err(f'missing packed file {rel}')
    junk = [str(p.relative_to(out)) for p in out.rglob('*')
            if p.name in ('.DS_Store', 'sources.json', 'skins.json')]
    if junk:
        err(f'dev files leaked into the pack: {junk[:5]}')
    if (out / 'data/measurements.json').exists():
        try:
            json.loads((out / 'data/measurements.json').read_text())
        except json.JSONDecodeError as e:
            err(f'dataset JSON invalid: {e}')
    for rel in ('data/schema.json', 'manifest.webmanifest'):
        if (out / rel).exists():
            try:
                json.loads((out / rel).read_text())
            except json.JSONDecodeError as e:
                err(f'{rel} invalid: {e}')


# ---------------------------------------------------------------- HTML
def check_html(out, site):
    pages = sorted(out.rglob('*.html'))
    if not pages:
        err('no HTML files found')
        return
    for page in pages:
        text = page.read_text()
        rel = page.relative_to(out)
        if re.match(r'^(google|BingSiteAuth|yandex_)', page.name):
            continue        # hand-uploaded search-console verification file
        for token in ('__SITE_URL__', '__DESC__', '__TITLE__', '__OGV__', '__REPO__',
                      '__DATA_UPDATED__', '__SCHEMA_VERSION__', '/*__'):
            if token in text:
                err(f'{rel}: unreplaced token {token}')
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            try:
                json.loads(block)
            except json.JSONDecodeError as e:
                err(f'{rel}: invalid JSON-LD: {e}')
        if '<html lang="en">' not in text and '<html lang=' not in text:
            err(f'{rel}: missing lang attribute')
    idx = (out / 'index.html').read_text()
    for needle, label in (('class="skip"', 'skip link'), ('id="main"', 'main landmark'),
                          ('aria-modal="true"', 'modal aria-modal'), ('aria-live="polite"', 'live region'),
                          ('rel="manifest"', 'manifest link'), ('sw.js', 'service worker registration')):
        if needle not in idx:
            err(f'index.html: missing {label}')
    if idx.count('class="card"') < N:
        err(f'index.html: only {idx.count("class=\"card\"")} static cards, expected {N}')
    checked, broken = link_check(out, site)
    if broken:
        for b in broken[:20]:
            err(f'broken local reference {b}')
    if checked < 50:
        err(f'link check only resolved {checked} references')
    sm = (out / 'sitemap.xml').read_text()
    for d in DATA:
        if f"characters/{d['slug']}.html" not in sm:
            err(f'sitemap missing {d["slug"]}')
    notfound = (out / '404.html').read_text()
    if '<base href=' not in notfound:
        err('404.html needs a <base href> so nested URLs resolve assets')
    sw = (out / 'sw.js').read_text()
    for needle in ('offline.html', 'cache', 'fetch'):
        if needle not in sw:
            err(f'sw.js missing {needle}')
    # generated copy must agree with the roster size
    if f'all {N} female' not in idx:
        err(f'index.html copy does not mention all {N} agents')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(ROOT / 'docs'))
    ap.add_argument('--site-url', default='https://nullhollow.github.io/zzz-measurements/')
    a = ap.parse_args()
    site = a.site_url if a.site_url.endswith('/') else a.site_url + '/'
    out = Path(a.out)
    if not out.exists():
        sys.exit(f'packed site not found at {out}')

    check_data(out)
    check_assets(out)
    check_html(out, site)

    if warnings:
        print('warnings:')
        for w in warnings:
            print('  -', w)
    if errors:
        print(f'\nFAILED: {len(errors)} problem(s)')
        for e in errors:
            print('  -', e)
        sys.exit(1)
    print(f'OK: {N} entries · {len(list((out / "characters").glob("*.html")))} character pages · '
          f'{sum(1 for p in out.rglob("*") if p.is_file())} files validated')


if __name__ == '__main__':
    main()
