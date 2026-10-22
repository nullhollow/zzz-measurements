"""Download official character portraits from the ZZZ Fandom wiki into character_images/.

Source: https://zenless-zone-zero.fandom.com (images are fair-use, (c) HoYoverse).
One WebP per roster entry, named after the character (slug of display name).
"""
import json, sys, os, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from optimize_images import convert as _c
def convert_to_webp(p):
    try: return _c(p)[0]
    except Exception as e: print('  webp conversion failed:', e); return None
from io import BytesIO
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'character_images'
OUT.mkdir(parents=True, exist_ok=True)

WIKI = 'https://zenless-zone-zero.fandom.com'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) zzz-fan-dashboard/1.0 (local archive)'}

# explicit file targets where page-image resolution is wrong or a skin is wanted
FILE_OVERRIDE = {
    'Aria bot':           'File:Agent Aria Robot Portrait.png',            # construct form
    'Aria':               'File:Agent Aria Human Portrait.png',
    'Soldier11':          'File:Agent Soldier 11 Portrait.png',
    # outfit variants (official skins the sheet's variant rows were measured from)
    'Lucy (swimsuit)':    'File:Agent Luciana de Montefio Princess on Holiday Portrait.png',
    'Vivian (swimsuit)':  'File:Agent Vivian Banshee Iris of the Shore Portrait.png',
    'Belle (summer)':     'File:Agent Belle Summer Skies Portrait.png',
    'Jane Doe (skin)':    'File:Agent Jane Doe Nocturne of Light Portrait.png',
}
PAGE_OVERRIDE = {'Soldier11': 'Soldier 11'}   # page title differs from csv name
# The wiki's Phoenix portrait carries a white-barcode upload artefact; use the
# clean transparent render from the official character page instead.
URL_OVERRIDE = {
    'Phoenix': 'https://fastcdn.hoyoverse.com/content-v2/nap/166075/'
               '93913c7d1fa97b87c146ad1467ce1d16_8934185391506393783.png',
}


def api(params):
    params.update({'format': 'json', 'redirects': 1})
    req = urllib.request.Request(WIKI + '/api.php?' + urllib.parse.urlencode(params), headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def slugify(display):
    return display.lower().replace(' (', '_').replace(')', '').replace(' ', '_')


def resolve_files(data):
    """map csv name -> (wiki file title, page title)"""
    out, cache = {}, {}
    for d in data:
        name = d['name']
        if name in FILE_OVERRIDE:
            out[name] = (FILE_OVERRIDE[name], '(explicit)')
            continue
        title = PAGE_OVERRIDE.get(name, name)
        if title in cache:
            out[name] = cache[title]
            continue
        j = api({'action': 'query', 'prop': 'pageimages', 'piprop': 'original', 'titles': title})
        page = list(j['query']['pages'].values())[0]
        src = page.get('original', {}).get('source', '')
        if not src:                       # fall back to search
            s = api({'action': 'query', 'list': 'search', 'srsearch': name, 'srlimit': 1})
            hits = s.get('query', {}).get('search', [])
            if not hits:
                raise SystemExit(f'no wiki page for {name!r}')
            j = api({'action': 'query', 'prop': 'pageimages', 'piprop': 'original', 'titles': hits[0]['title']})
            page = list(j['query']['pages'].values())[0]
            src = page.get('original', {}).get('source', '')
        fname = urllib.parse.unquote(src.split('/revision/')[0].rsplit('/', 1)[-1])
        if not fname.lower().startswith('file:'):
            fname = 'File:' + fname
        cache[title] = (fname, page['title'])
        out[name] = cache[title]
        time.sleep(0.25)
    return out


def file_url(file_title):
    j = api({'action': 'query', 'prop': 'imageinfo', 'iiprop': 'url|size|mime', 'titles': file_title})
    page = list(j['query']['pages'].values())[0]
    if 'missing' in page or not page.get('imageinfo'):
        return None, None
    return page['imageinfo'][0]['url'], page['imageinfo'][0]


def main():
    data = json.load(open(ROOT / 'tools/data.json'))
    files = resolve_files(data)
    manifest, problems = [], []
    for d in data:
        name, disp = d['name'], d['display']
        file_title, page_title = files[name]
        url, info = file_url(file_title)
        url = URL_OVERRIDE.get(name, url)
        if not url:
            problems.append(f'{disp}: file page missing ({file_title})')
            continue
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            blob = r.read()
        im = Image.open(BytesIO(blob))
        if getattr(im, 'is_animated', False):
            im.seek(0)
        im = im.convert('RGBA')
        dst = OUT / (slugify(disp) + '.png')
        im.save(dst)
        webp = convert_to_webp(str(dst))   # optimised copy for the dashboard
        manifest.append({
            'file': dst.name, 'character': disp, 'csv_name': name,
            'wiki_page': page_title, 'wiki_file': file_title,
            'source': url, 'width': im.width, 'height': im.height, 'license': 'Fair use / (c) HoYoverse (Fandom wiki)',
        })
        print(f"{disp:20s} {im.width}x{im.height}  {dst.stat().st_size/1024:7.0f} KB  <- {file_title}")
        time.sleep(0.25)
    json.dump(manifest, open(OUT / 'sources.json', 'w'), indent=1)
    total = sum(f.stat().st_size for f in OUT.glob('*.png'))
    web = sum(f.stat().st_size for f in OUT.glob('*.webp'))
    print(f"\n{len(manifest)}/{len(data)} images saved to {OUT}  (png {total/1024/1024:.1f} MB, webp {web/1024/1024:.1f} MB)")
    if problems:
        print('PROBLEMS:'); [print('  -', p) for p in problems]


if __name__ == '__main__':
    main()
