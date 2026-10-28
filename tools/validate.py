#!/usr/bin/env python3
"""Validate the data and the packed site.

    python3 tools/validate.py                      # checks docs/
    python3 tools/validate.py --site-url https://.../ --out docs

Exits non-zero on the first category with problems, printing every finding.
Designed for CI after tools/pack_site.py.
"""
import argparse
import csv
import html as htmllib
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit

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
        if d.get('slug') == 'jane_doe' and (d.get('official') != 'jane_doe_skin' or
                d.get('outfit') != 'Nocturne of Light' or d.get('skin')):
            err('Jane Doe must use her canonical Nocturne of Light record and portrait')
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
        for rec in [d] + ([d['skin']] if d.get('skin') else []):
            for key, field in (('bust', 'bust_cm'), ('underbust', 'band_cm'), ('waist', 'waist_cm'),
                               ('hip', 'hip_cm'), ('thigh', 'thigh_cm')):
                expected = rec[field] / rec['stature_cm'] * 100 if rec[field] is not None and rec['stature_cm'] > 0 else None
                actual = rec.get('height_adjusted', {}).get(key)
                if (key not in rec.get('height_adjusted', {}) or
                        (expected is None and actual is not None) or
                        (expected is not None and not close(actual, expected, 1e-10))):
                    err(f'{rec["display"]}: height_adjusted.{key} must use raw cm / stature_cm × 100')
            bp, hp = rec.get('p_bust_cm'), rec.get('p_hip_cm')
            delta = bp - hp if bp is not None and hp is not None else 0
            balance = 'top' if delta > .18 else 'bottom' if delta < -.18 else 'even'
            if rec.get('balance') != balance:
                err(f'{rec["display"]}: Build disagrees with bust/hip percentiles')
            # Check the actual generated prose, including both unit variants.
            phrases = {
                'top': ('the bust ranks higher', 'バストがヒップより上位', '胸围在全榜中的排名高于臀围'),
                'bottom': ('the hips rank higher', 'ヒップがバストより上位', '臀围在全榜中的排名高于胸围'),
                'even': ('bust and hip percentile ranks are close', '順位は近い位置', '胸围与臀围在全榜中的排名接近'),
            }[balance]
            for lang, phrase in zip(('en', 'ja', 'zh'), phrases):
                for unit in ('cm', 'in'):
                    key = f'desc_{unit}' if lang == 'en' else f'desc_{lang}_{unit}'
                    prose = rec.get(key, '')
                    if phrase not in prose:
                        err(f'{rec["display"]}: {key} disagrees with Build')
                    if re.search(r'ありますです|ですです|\.\.|。。', prose):
                        err(f'{rec["display"]}: malformed punctuation/grammar in {key}')
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
                    f"character_images/thumbs/avif/1024/{d['official']}.avif",
                    f"character_images/thumbs/avif/1280/{d['official']}.avif"):
            if rel.startswith('images/') and d.get('sheet_available') is False:continue
            if not (ROOT / rel).exists():
                err(f'missing source asset {rel}')
        if d.get('skin'):
            if not (ROOT / f"character_images/{d['skin']['official']}.webp").exists():
                err(f'{d["display"]}: missing measured outfit art')
        for it in d['outfits']:
            if not (ROOT / 'character_images' / it['file']).exists():
                err(f'{d["display"]}: missing outfit art {it["file"]}')
            if it.get('avif') and not (ROOT / 'character_images' / it['avif']).exists():
                err(f'{d["display"]}: missing outfit AVIF {it["avif"]}')
        for lang in ('en', 'ja', 'zh'):
            page = (out / 'characters' if lang == 'en' else out / lang / 'characters') / f"{d['slug']}.html"
            if not page.exists():
                err(f'missing {lang} character page {page.relative_to(out)}')
                continue
            html = page.read_text()
            expected = d['display'] if lang == 'en' else d.get(f'name_{lang}')
            if expected and htmllib.escape(expected) not in html:
                err(f'{d["slug"]} ({lang}): page does not name the character')
            if 'application/ld+json' not in html:
                err(f'{d["slug"]} ({lang}): page has no JSON-LD')
            if 'rel="canonical"' not in html:
                err(f'{d["slug"]} ({lang}): page has no canonical URL')
            meta = re.search(r'<meta name="description" content="([^"]*)"', html)
            desc = htmllib.unescape(meta[1]) if meta else ''
            if not desc or not expected or desc.count(expected) != 1 or desc.endswith(('…', '...')) or not desc.endswith(('.', '。')):
                err(f'{d["slug"]} ({lang}): missing, repeated or incomplete meta description')
            footer = html.split('<footer>', 1)[-1]
            if lang != 'en' and re.search(r'>Source(?: repository)?</a>', footer):
                err(f'{d["slug"]} ({lang}): untranslated source link')
            if d.get('outfit'):
                hero = html.split('<section class="hero">', 1)[-1].split('</section>', 1)[0]
                gallery = html.split('<div class="gallery">', 1)[-1].split('</div>', 1)[0]
                for label, section in (('hero', hero), ('gallery', gallery)):
                    if f"/{d['official']}.webp" not in section or d['outfit'] not in section:
                        err(f'{d["slug"]} ({lang}): canonical outfit missing from {label}')
    # exports & crawler files
    for rel in ('index.html', 'tools.html', 'favourites.html', 'methodology.html', 'offline.html', 'sw.js', '404.html',
                'robots.txt', 'sitemap.xml', 'manifest.webmanifest', '.nojekyll',
                'ja/methodology.html', 'zh/methodology.html',
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
    def check_jsonld(value, rel):
        if isinstance(value, list):
            for item in value:
                check_jsonld(item, rel)
        elif isinstance(value, dict):
            if value.get('@type') == 'ItemList':
                items = value.get('itemListElement', [])
                expected_urls = {f"{site}characters/{d['slug']}.html" for d in DATA}
                if {item.get('url') for item in items} != expected_urls or len(items) != N:
                    err(f'{rel}: ItemList does not link to all {N} character pages')
                for item in items:
                    desc = item.get('description', '')
                    if not desc.endswith('.') or desc.endswith(('…', '...')):
                        err(f'{rel}: incomplete ItemList description for {item.get("name")}')
            for key, item in value.items():
                if key in ('url', '@id', 'contentUrl', 'image', 'item') and isinstance(item, str) and item.startswith(site):
                    path = unquote(urlsplit(item[len(site):]).path)
                    target = out / (path + 'index.html' if not path or path.endswith('/') else path)
                    if not target.is_file():
                        err(f'{rel}: broken local JSON-LD reference {item}')
                check_jsonld(item, rel)

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
                check_jsonld(json.loads(block), rel)
            except json.JSONDecodeError as e:
                err(f'{rel}: invalid JSON-LD: {e}')
        if '<html lang="en">' not in text and '<html lang=' not in text:
            err(f'{rel}: missing lang attribute')
    idx = (out / 'index.html').read_text()
    tools = (out / 'tools.html').read_text()
    favourites = (out / 'favourites.html').read_text()
    for needle in ('data-page="favourites"', 'id="favBoard"', 'id="favDownload"',
                   f'rel="canonical" href="{site}favourites.html"'):
        if needle not in favourites:
            err(f'favourites.html: missing {needle}')
    for rel, page in (('index.html', idx), ('tools.html', tools)):
        settings = re.search(r'<dialog\b[^>]*id="settingsDialog".*?</dialog>', page, re.S)
        if not settings or 'id="unitToggle"' not in settings[0] or 'id="cupSystemToggle"' not in settings[0]:
            err(f'{rel}: measurement settings must group length and cup systems in a dialog')
        if page.count('id="settingsBtn"') != 1 or page.count('id="unitToggle"') != 1:
            err(f'{rel}: duplicated or missing measurement settings controls')
        if settings:
            for system in ('uk', 'us', 'eu'):
                if f'data-cup-system="{system}"' not in settings[0]:
                    err(f'{rel}: missing {system} display setting')
    if 'id="toolSelect"' in idx:
        err('index.html: tools selector belongs on the dedicated tools page')
    for needle in ('id="toolsLink"', 'href="tools.html"'):
        if needle not in idx:
            err(f'index.html: missing tools navigation {needle}')
    for needle in ('data-page="tools"', 'id="toolsNav"', 'id="toolsView"',
                   f'rel="canonical" href="{site}tools.html"'):
        if needle not in tools:
            err(f'tools.html: missing {needle}')
    for key in ('distribution', 'matches', 'game', 'sandbox'):
        if f'data-tool-link="{key}"' not in tools:
            err(f'tools.html: missing navigation for {key}')
    for needle, label in (('class="skip"', 'skip link'), ('id="main"', 'main landmark'),
                          ('aria-modal="true"', 'modal aria-modal'), ('aria-live="polite"', 'live region'),
                          ('rel="manifest"', 'manifest link'), ('sw.js', 'service worker registration')):
        if needle not in idx:
            err(f'index.html: missing {label}')
    if idx.count('class="card"') < N:
        err(f'index.html: only {idx.count("class=\"card\"")} static cards, expected {N}')
    for d in DATA:
        if d.get('outfit'):
            card = re.search(r'<article class="card" data-name="' + re.escape(htmllib.escape(d['name'], quote=True)) + r'">(.*?)</article>', idx, re.S)
            if not card or f"/{d['official']}.webp" not in card[1] or d['outfit'] not in card[1]:
                err(f'index.html: canonical outfit missing from {d["display"]} card')
    # All marked strings, including footer controls, need all three translations.
    i18n = re.search(r'const I18N = \{(.*?)\n\};', idx, re.S)
    if i18n:
        blocks = re.split(r'\n  (?:en|ja|zh): \{', i18n[1])[1:]
        if len(blocks) != 3:
            err('index.html: expected three I18N language blocks')
        keys = set(re.findall(r'data-i18n="([^"]+)"', idx + tools))
        for lang, block in zip(('en', 'ja', 'zh'), blocks):
            present = set(re.findall(r'\b(\w+):\s*[\'\"]', block))
            if keys - present:
                err(f'index.html ({lang}): missing translations {sorted(keys - present)}')
    else:
        err('index.html: missing I18N translations')
    footer = idx.split('<footer>', 1)[-1].split('</footer>', 1)[0]
    for key in ('changelog', 'sourceRepository', 'mainSource', 'sourceTitle', 'schema', 'updated'):
        if f'data-i18n="{key}"' not in footer:
            err(f'index.html: footer {key} is not localizable')
    for filename, content in (('index.html', idx), ('tools.html', tools)):
        settings = content.split('<dialog class="settings-dialog" id="settingsDialog"', 1)[-1].split('</dialog>', 1)[0]
        for key in ('language', 'theme', 'dark', 'light', 'lengthUnit', 'cupSystem'):
            if f'data-i18n="{key}"' not in settings:
                err(f'{filename}: settings {key} is not localizable')
        if '<title>ZZZ Measurements</title>' not in content:
            err(f'{filename}: unexpected browser title')
    checked, broken = link_check(out, site)
    if broken:
        for b in broken[:20]:
            err(f'broken local reference {b}')
    if checked < 50:
        err(f'link check only resolved {checked} references')
    sm = (out / 'sitemap.xml').read_text()
    if f'{site}tools.html' not in sm:
        err('sitemap missing tools.html')
    if f'{site}favourites.html' not in sm:
        err('sitemap missing favourites.html')
    for d in DATA:
        if f"characters/{d['slug']}.html" not in sm:
            err(f'sitemap missing {d["slug"]}')
    notfound = (out / '404.html').read_text()
    if '<base href=' not in notfound:
        err('404.html needs a <base href> so nested URLs resolve assets')
    sw = (out / 'sw.js').read_text()
    for needle in ('offline.html', 'tools.html', 'favourites.html', 'cache', 'fetch'):
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
