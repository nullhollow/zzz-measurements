#!/usr/bin/env python3
"""Fetch official outfit (skin) portrait renders from the ZZZ Fandom wiki.

Outfit data comes from Category:Outfits. Each outfit page has an
{{Outfit Infobox}} with `agent`, `type` and a Portrait image. We keep every
non-Default outfit whose agent is in our roster (matched via
character_images/sources.json), and download the portrait to
character_images/skins/<char>_<outfit-slug>.png.

Writes character_images/skins.json:
  { "velina.png": { "name": "Velina", "items": [ {label,type,file,source} ] } }

Usage: python3 tools/fetch_skins.py [--force]
"""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from optimize_images import convert as convert_to_webp

API = 'https://zenless-zone-zero.fandom.com/api.php'
UA = {'User-Agent': 'zzz-analysis/1.0 (local research dashboard)'}
IMG_DIR = 'character_images'
SKIN_DIR = os.path.join(IMG_DIR, 'skins')
CATEGORY = 'Category:Outfits'
FORCE = '--force' in sys.argv

# Phoenix's outfit pages currently have in-game renders but no transparent
# portrait uploads. Keep the committed cut-outs instead of dropping the entries
# when this scraper is rerun.
EXTRA = {
    'phoenix.png': {'name': 'Phoenix', 'items': [
        {'label': 'The Illness Called Life', 'type': 'Paid',
         'file': 'skins/phoenix_the_illness_called_life.webp',
         'wiki_file': 'File:Agent Phoenix Reffaella The Illness Called Life In-Game.png'},
        {'label': 'Daydream Complex', 'type': 'Paid',
         'file': 'skins/phoenix_daydream_complex.webp',
         'wiki_file': 'File:Agent Phoenix Reffaella Daydream Complex In-Game.png'},
    ]},
}


def api(params):
    url = API + '?' + urllib.parse.urlencode({**params, 'format': 'json'})
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))


def api_post(params):
    data = urllib.parse.urlencode({**params, 'format': 'json'}).encode()
    req = urllib.request.Request(API, data=data, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=60))


def norm(pf):
    """'File:Agent Aria Human Portrait.png' -> 'Agent_Aria_Human'"""
    n = pf.replace('File:', '').replace(' ', '_')
    return n[:-len('_Portrait.png')] if n.endswith('_Portrait.png') else n


def slug(s):
    return re.sub(r'_+', '_', re.sub(r'[^a-z0-9]+', '_', s.lower())).strip('_')


def build_roster():
    src = json.load(open(os.path.join(IMG_DIR, 'sources.json')))
    roster = {}
    for s in src:
        wf = s['wiki_file'].replace(' ', '_')
        if wf.endswith('_Portrait.png'):
            roster[norm(s['wiki_file'])] = (s['csv_name'], s['file'])
    return roster


def match(key, roster):
    if key in roster:
        return roster[key]
    for k, v in roster.items():
        if k.startswith(key + '_') or key.startswith(k + '_'):
            return v
    return None


def discover(roster):
    members = api({'action': 'query', 'list': 'categorymembers', 'cmtitle': CATEGORY,
                   'cmlimit': '500'})['query']['categorymembers']
    pages = []
    for i in range(0, len(members), 40):
        chunk = [m['title'] for m in members[i:i + 40]]
        r = api({'action': 'query', 'prop': 'revisions', 'rvprop': 'content', 'rvslots': 'main',
                 'titles': '|'.join(chunk)})
        pages += r['query']['pages'].values()
        time.sleep(0.2)
    found = {}
    for pg in pages:
        txt = pg.get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('*', '')
        if not txt:
            continue
        def field(k):
            m = re.search(r'^\|\s*' + k + r'\s*=\s*(.*?)\s*$', txt, re.M)
            return m.group(1).strip() if m else ''
        agent, typ = field('agent'), field('type')
        if not agent or 'default' in typ.lower():
            continue
        imgs = re.findall(r'^([^\n|<>]+\.(?:png|jpg|jpeg|webp))\|([^\n]+)$', txt, re.M | re.I)
        portrait = next((fn for fn, lb in imgs if 'portrait' in lb.lower()), '')
        if not portrait:
            continue
        key = norm(portrait)
        tail = '_' + pg['title'].replace(' ', '_')
        if key.endswith(tail):
            key = key[:-len(tail)]
        hit = match(key, roster)
        if hit:
            found.setdefault(hit[1], {'name': hit[0], 'items': []})['items'].append(
                {'label': pg['title'], 'type': typ, 'wiki_file': 'File:' + portrait})
    return found


def file_url(title):
    r = api({'action': 'query', 'prop': 'imageinfo', 'iiprop': 'url|size',
             'titles': title})
    pg = list(r['query']['pages'].values())[0]
    ii = pg.get('imageinfo', [{}])[0]
    return ii.get('url'), ii.get('width'), ii.get('height')


def main():
    os.makedirs(SKIN_DIR, exist_ok=True)
    roster = build_roster()
    hits = discover(roster)
    for key, rec in EXTRA.items():
        hits.setdefault(key, rec)
    print('roster matches:', len(hits), '| outfits:', sum(len(v['items']) for v in hits.values()))
    out = {}
    for base, rec in sorted(hits.items()):
        items = []
        for it in rec['items']:
            fname = f"{base[:-4]}_{slug(it['label'])}.png"
            dest = os.path.join(SKIN_DIR, fname)
            if it.get('file') and os.path.exists(os.path.join(IMG_DIR, it['file'])) and not FORCE:
                items.append({'label': it['label'], 'type': it['type'].replace('; ', ';'),
                              'file': it['file'], 'wiki_file': it['wiki_file']})
                continue
            if FORCE or not os.path.exists(dest):
                url, w, h = file_url(it['wiki_file'])
                if url:
                    req = urllib.request.Request(url, headers=UA)
                    with urllib.request.urlopen(req, timeout=120) as r, open(dest, 'wb') as fh:
                        fh.write(r.read())
                try:
                    convert_to_webp(dest)
                except Exception as e:
                    print('  webp conversion failed:', e)
                print(f"  {rec['name']:14} {it['label']:24} -> {fname} ({w}x{h})")
                time.sleep(0.3)
            items.append({'label': it['label'], 'type': it['type'].replace('; ', ';'),
                          'file': f"skins/{fname}",
                          'wiki_file': it['wiki_file']})
        out[base] = {'name': rec['name'], 'items': items}
    json.dump(out, open(os.path.join(IMG_DIR, 'skins.json'), 'w'), indent=1)
    print('wrote', os.path.join(IMG_DIR, 'skins.json'))


if __name__ == '__main__':
    main()
