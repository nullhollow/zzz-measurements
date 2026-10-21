#!/usr/bin/env python3
"""Pack the site into a single folder ready for GitHub Pages.

    python3 tools/pack_site.py                                   # -> docs/
    python3 tools/pack_site.py --site-url https://me.github.io/zzz/   # sets canonical/OG/sitemap URLs
    python3 tools/pack_site.py --no-rebuild                      # pack the existing index.html

The folder contains only what the site needs to run: the page, the WebP artwork,
the bundled fonts, icons, the OG card and the crawler files. Dev assets (tools/,
the CSV, the source contact sheet, the lab) stay out.

Deploy: commit the docs/ folder and point GitHub Pages at "main /docs"
(Settings -> Pages -> Build and deployment -> Deploy from a branch).
"""
import argparse, json, os, re, shutil, subprocess, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = 'https://nullhollow.github.io/zzz-measurements/'   # nullhollow's GitHub Pages URL (override with --site-url)

ASSET_DIRS = ['images', 'character_images', 'fonts']
ASSET_FILES = ['favicon.svg', 'favicon.ico', 'icon-192.png', 'icon-512.png', 'og.png']
# files uploaded by hand into docs/ (search-console / site verification) that a rebuild
# must not delete: they live in git, not in the pipeline
KEEP_GLOBS = ('google*.html', 'BingSiteAuth.xml', 'yandex_*.html')
MANIFEST = {
    'name': 'ZZZ Female Measurements',
    'short_name': 'ZZZ Measurements',
    'description': 'Measurements, proportions and silhouette reads for all female Zenless Zone Zero agents.',
    'start_url': './',
    'scope': './',
    'display': 'standalone',
    'background_color': '#0B0B0C',
    'theme_color': '#0B0B0C',
    'icons': [
        {'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
        {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
        {'src': 'favicon.svg', 'sizes': 'any', 'type': 'image/svg+xml'},
    ],
}
NOT_FOUND = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Page not found · ZZZ Female Measurements</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="stylesheet" href="fonts/fonts.css">
<style>
  body{margin:0; background:#0B0B0C; color:#fff; font-family:'Inter',system-ui,sans-serif;
    display:grid; place-items:center; min-height:100vh; text-align:center}
  h1{font-family:'Anton','Arial Narrow',Impact,sans-serif; font-weight:400; font-size:clamp(40px,9vw,90px);
    line-height:1; margin:0 0 10px; text-transform:uppercase}
  h1 span{color:#D8FA00}
  p{color:#9A9AA3; margin:0 0 22px}
  a{display:inline-block; background:#D8FA00; color:#0b0b0c; text-decoration:none; font-weight:800;
    padding:12px 22px; border-radius:999px; font-size:13px; letter-spacing:.08em; text-transform:uppercase}
</style></head>
<body><main>
  <h1>404 <span>nothing here</span></h1>
  <p>The page you asked for is not part of this chart.</p>
  <a href="./">Back to the measurements</a>
</main></body></html>
'''


def rebuild():
    for script in ('build_data.py', 'describe.py', 'build_html.py'):
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / script)], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f'{script} failed:\n{r.stdout}\n{r.stderr}')
        tail = [l for l in r.stdout.strip().splitlines() if l][-1:]
        print(f'  {script}: {tail[0] if tail else "ok"}')


def copy_tree(src, dst):
    n = 0
    for dirpath, _dirs, files in os.walk(src):
        for f in files:
            s = Path(dirpath) / f
            d = dst / s.relative_to(src)
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site-url', default=PLACEHOLDER, help='absolute URL of the deployed site (trailing slash)')
    ap.add_argument('--out', default=str(ROOT / 'docs'), help='output folder')
    ap.add_argument('--no-rebuild', action='store_true', help='skip build_data/describe/build_html')
    a = ap.parse_args()
    site = a.site_url if a.site_url.endswith('/') else a.site_url + '/'
    out = Path(a.out)
    if not a.no_rebuild:
        print('rebuilding:')
        rebuild()

    kept = {}
    if out.exists():
        for pat in KEEP_GLOBS:
            for f in out.glob(pat):
                if f.is_file():
                    kept[f.relative_to(out)] = f.read_bytes()
        shutil.rmtree(out)
    out.mkdir(parents=True)

    # page + assets
    html = (ROOT / 'index.html').read_text()
    html = html.replace('__SITE_URL__', site).replace(PLACEHOLDER, site)
    (out / 'index.html').write_text(html)
    files = 1
    for f in ASSET_FILES:
        shutil.copy2(ROOT / f, out / f)
        files += 1
    for d in ASSET_DIRS:
        src = ROOT / d
        if not src.is_dir():
            sys.exit(f'missing asset folder: {d}')
        files += copy_tree(src, out / d)
    for rel, blob in kept.items():
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_bytes(blob)
        files += 1
        print(f'  kept hand-uploaded file: {rel}')

    # the wiki manifests are build metadata, not site assets
    for junk in ('sources.json', 'skins.json'):
        (out / 'character_images' / junk).unlink(missing_ok=True)
        files -= 1

    # crawler + PWA files
    (out / 'robots.txt').write_text(
        'User-agent: *\nAllow: /\n\nSitemap: ' + site + 'sitemap.xml\n')
    (out / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>{site}</loc><lastmod>{date.today().isoformat()}</lastmod>'
        '<changefreq>monthly</changefreq><priority>1.0</priority></url>\n'
        '</urlset>\n')
    (out / 'manifest.webmanifest').write_text(json.dumps(MANIFEST, indent=1) + '\n')
    (out / '404.html').write_text(NOT_FOUND)
    (out / '.nojekyll').write_text('')
    files += 5

    # every local reference in the page must exist inside the packed folder
    missing = []
    for ref in set(re.findall(r'(?:src|href)="([^"#:]+?)"', html)):
        if ref.startswith(('data:', 'http', 'mailto:', '//')) or '${' in ref:
            continue        # skip absolute URLs and runtime template literals
        if not (out / ref).exists():
            missing.append(ref)
    print('broken local references:', missing if missing else 'none')

    total = sum(f.stat().st_size for f in out.rglob('*') if f.is_file())
    print(f'\npacked {files} files into {out.relative_to(ROOT)}/  ({total/1048576:.1f} MB)')
    for d in sorted([p for p in out.iterdir()], key=lambda p: p.name):
        if d.is_dir():
            n = sum(1 for _ in d.rglob('*') if _.is_file())
            sz = sum(f.stat().st_size for f in d.rglob('*') if f.is_file())
            print(f'   {d.name + "/":22} {n:3} files  {sz/1048576:5.1f} MB')
        else:
            print(f'   {d.name:22} {"":10} {d.stat().st_size/1024:5.1f} kB')
    if site == PLACEHOLDER:
        print(f'\nURLs point at {site}')
        print('      (different repo name? re-run: python3 tools/pack_site.py --site-url https://nullhollow.github.io/<repo>/)')


if __name__ == '__main__':
    main()
