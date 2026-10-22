#!/usr/bin/env python3
"""Pack the site into a single folder ready for GitHub Pages.

    python3 tools/pack_site.py                                   # -> docs/
    python3 tools/pack_site.py --site-url https://me.github.io/zzz/   # sets canonical/OG/sitemap URLs
    python3 tools/pack_site.py --no-rebuild                      # reuse the existing index.html

The folder contains only what the site needs to run: the page, the static
character pages, the WebP artwork, the bundled fonts, icons, the data exports,
the service worker and the crawler files. Dev assets stay out.

Everything is deterministic: data date comes from tools/meta.json, the sitemap
lastmod uses it, and the service-worker version is a hash of the built page, so
a rebuild on CI produces byte-identical output.
"""
import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = 'https://nullhollow.github.io/zzz-measurements/'   # override with --site-url
META = json.loads((ROOT / 'tools/meta.json').read_text())
DATA = json.loads((ROOT / 'tools/data.json').read_text())

ASSET_DIRS = ['images', 'character_images', 'fonts']
ASSET_FILES = ['favicon.svg', 'favicon.ico', 'icon-192.png', 'icon-512.png',
               'icon-maskable-512.png', 'og.png']
IGNORE_NAMES = {'.DS_Store', 'sources.json', 'skins.json'}
KEEP_GLOBS = ('google*.html', 'BingSiteAuth.xml', 'yandex_*.html')

MANIFEST = {
    'id': './',
    'name': 'ZZZ Female Measurements',
    'short_name': 'ZZZ Measurements',
    'description': 'Measurements, proportions and silhouette reads for all female Zenless Zone Zero agents.',
    'start_url': './',
    'scope': './',
    'display': 'standalone',
    'background_color': '#0B0B0C',
    'theme_color': '#0B0B0C',
    'lang': 'en',
    'dir': 'ltr',
    'categories': ['reference', 'entertainment'],
    'icons': [
        {'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
        {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
        {'src': 'icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        {'src': 'favicon.svg', 'sizes': 'any', 'type': 'image/svg+xml'},
    ],
    'shortcuts': [
        {'name': 'Measurements table', 'short_name': 'Table', 'url': './#view=table'},
        {'name': 'Comparison tools', 'short_name': 'Tools', 'url': './tools.html'},
        {'name': 'Methodology', 'short_name': 'Method', 'url': './methodology.html'},
    ],
}

NOT_FOUND = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<base href="__SITE__">
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
  <a href="__SITE__">Back to the measurements</a>
</main></body></html>
'''


def rebuild():
    for script in ('build_data.py', 'describe.py', 'build_html.py'):
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / script)],
                           capture_output=True, text=True, cwd=ROOT)
        if r.returncode:
            sys.exit(f'{script} failed:\n{r.stdout}\n{r.stderr}')
        tail = [l for l in r.stdout.strip().splitlines() if l][-1:]
        print(f'  {script}: {tail[0] if tail else "ok"}')


def copy_tree(src, dst):
    n = 0
    for dirpath, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in IGNORE_NAMES]
        for f in files:
            if f in IGNORE_NAMES or f.endswith(('.pyc', '.swp')):
                continue
            s = Path(dirpath) / f
            d = dst / s.relative_to(src)
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
            n += 1
    return n


def service_worker(html, site, tools_html=''):
    version = hashlib.sha256((html + tools_html).encode()).hexdigest()[:10]
    fonts = sorted(p.name for p in (ROOT / 'fonts').glob('*.woff2'))
    shell = ['./', 'index.html', 'tools.html', 'methodology.html', 'offline.html', 'manifest.webmanifest',
             'favicon.svg', 'favicon.ico', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png',
             'fonts/fonts.css', 'data/measurements.json'] + [f'fonts/{f}' for f in fonts]
    shell_js = json.dumps(shell, indent=1)
    return f'''/* Generated by tools/pack_site.py — cache v{version} */
const VERSION = 'zzz-{version}';
const SHELL = {shell_js};

self.addEventListener('install', event => {{
  event.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
}});

self.addEventListener('activate', event => {{
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
}});

self.addEventListener('fetch', event => {{
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  if (req.mode === 'navigate') {{
    event.respondWith(
      fetch(req).then(res => {{
        const copy = res.clone();
        caches.open(VERSION).then(c => c.put(req, copy));
        return res;
      }}).catch(() => caches.match(req).then(hit => hit || caches.match('offline.html')))
    );
    return;
  }}

  if (req.destination === 'image') {{
    event.respondWith(
      caches.match(req).then(hit => hit || fetch(req).then(res => {{
        const copy = res.clone();
        caches.open(VERSION).then(c => c.put(req, copy));
        return res;
      }}).catch(() => hit))
    );
    return;
  }}

  event.respondWith(
    caches.match(req).then(hit => {{
      const network = fetch(req).then(res => {{
        const copy = res.clone();
        caches.open(VERSION).then(c => c.put(req, copy));
        return res;
      }}).catch(() => hit);
      return hit || network;
    }})
  );
}});
'''


def sitemap(site):
    pages = ['', 'tools.html', 'methodology.html'] + [f"characters/{d['slug']}.html" for d in DATA]
    for lang in ('ja', 'zh'):
        pages += [f'{lang}/methodology.html'] + [f"{lang}/characters/{d['slug']}.html" for d in DATA]
    items = '\n'.join(
        f'  <url><loc>{site}{p}</loc><lastmod>{META["data_updated"]}</lastmod>'
        f'<changefreq>monthly</changefreq><priority>{"1.0" if p == "" else "0.7"}</priority></url>'
        for p in pages)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'{items}\n</urlset>\n')


def local_target(ref, base_dir, out, site):
    """Resolve a href/src to a file inside out, or None when it is external."""
    if not ref or ref.startswith(('data:', 'mailto:', 'tel:', 'javascript:')):
        return None
    if ref.startswith('#') or '${' in ref:
        return None
    parsed = urlparse(ref)
    base = base_dir
    if parsed.scheme in ('http', 'https'):
        if not ref.startswith(site):
            return None
        path = ref[len(site):]
        base = ''                 # absolute site URLs are always root-relative
    else:
        path = ref
    path = path.split('#')[0].split('?')[0]
    if not path:
        path = './'
    if path.startswith('/'):
        # absolute in-site path, e.g. /zzz-measurements/foo
        path = path.lstrip('/')
        base = ''
    target = posixpath.normpath(posixpath.join(base, path))
    if target.startswith('..'):
        return None
    candidate = out / target
    if candidate.is_dir() or path.endswith('/') or target in ('.', ''):
        candidate = candidate / 'index.html'
    return candidate


def link_check(out, site):
    broken, checked = [], 0
    for page in sorted(out.rglob('*.html')):
        rel = page.relative_to(out)
        text = page.read_text()
        refs = re.findall(r'(?:src|href)="([^"]+)"', text)
        for srcset in re.findall(r'srcset="([^"]+)"', text):
            refs += [part.strip().split()[0] for part in srcset.split(',') if part.strip()]
        for attr in refs:
            target = local_target(attr, str(rel.parent).replace('\\', '/'), out, site)
            if target is None:
                continue
            checked += 1
            if not target.exists():
                broken.append(f'{rel}: {attr} -> {target.relative_to(out)}')
    return checked, broken


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site-url', default=PLACEHOLDER,
                    help='absolute URL of the deployed site (trailing slash)')
    ap.add_argument('--out', default=str(ROOT / 'docs'), help='output folder')
    ap.add_argument('--no-rebuild', action='store_true',
                    help='skip build_data/describe/build_html')
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
    tools_html = (ROOT / 'tools.html').read_text().replace('__SITE_URL__', site).replace(PLACEHOLDER, site)
    (out / 'tools.html').write_text(tools_html)
    files = 2
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

    # static pages + exports
    pages = subprocess.run([sys.executable, str(ROOT / 'tools/build_pages.py'),
                            '--out', str(out), '--site-url', site],
                           capture_output=True, text=True, cwd=ROOT)
    if pages.returncode:
        sys.exit(f'build_pages.py failed:\n{pages.stdout}\n{pages.stderr}')
    print('  ' + [l for l in pages.stdout.strip().splitlines() if l][-1])
    files += sum(1 for _ in (out / 'characters').glob('*.html')) + sum(1 for _ in (out / 'ja' / 'characters').glob('*.html')) + sum(1 for _ in (out / 'zh' / 'characters').glob('*.html')) + 8

    # service worker + crawler files
    (out / 'sw.js').write_text(service_worker(html, site, tools_html))
    (out / 'robots.txt').write_text(
        'User-agent: *\nAllow: /\n\nSitemap: ' + site + 'sitemap.xml\n')
    (out / 'sitemap.xml').write_text(sitemap(site))
    (out / 'manifest.webmanifest').write_text(json.dumps(MANIFEST, indent=1) + '\n')
    (out / '404.html').write_text(NOT_FOUND.replace('__SITE__', site))
    (out / '.nojekyll').write_text('')
    files += 5

    # leftovers + broken links
    tokens = []
    for page in out.rglob('*.html'):
        text = page.read_text()
        for token in ('__SITE_URL__', '__DESC__', '__TITLE__', '__OGV__', '__REPO__',
                      '__DATA_UPDATED__', '__SCHEMA_VERSION__', '/*__'):
            if token in text:
                tokens.append(f'{page.relative_to(out)}: {token}')
    print('unreplaced tokens:', tokens if tokens else 'none')
    if tokens:
        sys.exit(1)
    checked, broken = link_check(out, site)
    print(f'local references checked: {checked} · broken: {len(broken)}')
    for b in broken:
        print('  BROKEN', b)
    if broken:
        sys.exit(1)

    total = sum(f.stat().st_size for f in out.rglob('*') if f.is_file())
    print(f'\npacked {files} files into {out.relative_to(ROOT)}/  ({total/1048576:.1f} MB)')
    for d in sorted(out.iterdir(), key=lambda p: p.name):
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
