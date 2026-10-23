#!/usr/bin/env python3
"""Refresh cited agent facts and archive unmodified source originals. Never run in CI."""
import datetime
import concurrent.futures, hashlib, io, json, re, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
UA={'User-Agent':'zzz-analysis/1.0 (reference archive)'}
API='https://zenless-zone-zero.fandom.com/api.php'
def api(**params):
    url=API+'?'+urllib.parse.urlencode(dict(params,format='json'))
    with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=90) as r:return json.load(r)
def pages(titles):
    result={}
    for i in range(0,len(titles),15):
        r=api(action='query',prop='revisions',rvprop='content',rvslots='main',titles='|'.join(titles[i:i+15]),redirects=1)
        for p in r['query']['pages'].values():result[p['title']]=p.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
    return result

def main():
    data=json.loads((ROOT/'tools/data.json').read_text());sources=json.loads((ROOT/'character_images/sources.json').read_text());skins=json.loads((ROOT/'character_images/skins.json').read_text());names=json.loads((ROOT/'tools/localized_names.json').read_text())
    source_by={s['file'].replace('.png',''):s for s in sources}
    aliases={'aria_construct':'Aria','jane_doe':'Jane Doe','yi_xuan':'Yixuan'}
    titles={d['slug']:aliases.get(d['slug'],source_by.get(d['official'],{}).get('wiki_page',d['display'])) for d in data}
    # Some source records use an explicit art URL instead of a page title.
    for d in data:
        if titles[d['slug']].startswith('('):titles[d['slug']]=d['display']
    raw=pages(sorted(set(titles.values())|{d['display'] for d in data}))
    fields={title:{k:v.strip() for k,v in re.findall(r'^\|\s*(name|brief_name|baseFaction|faction|releaseDate|type)\s*=\s*(.*?)\s*$',txt,re.M)} for title,txt in raw.items() if txt}
    agents={}
    for d in data:
        title=titles[d['slug']]
        if title not in fields:
            hits=[n for n,f in fields.items() if d['display'] in (f.get('name'),f.get('brief_name')) or n.startswith(title+' ')]
            if len(hits)!=1:raise ValueError(f'Unresolved agent: {d["slug"]}: {hits}')
            title=hits[0]
        f=fields[title];values=[]
        if f.get('type')=='Playable':
            text='|'.join('{{Get|'+title+'|'+key+'}}' for key in ['rank','attribute','specialty'])
            values=api(action='expandtemplates',text=text,prop='wikitext')['expandtemplates']['wikitext'].split('|')
            if len(values)!=3 or any('<' in v or '{' in v for v in values):raise ValueError((title,values))
        loc=names.get(d['slug'],{})
        agents[d['slug']]={'faction':f.get('baseFaction') or f.get('faction') or None,'rank':values[0] if values else None,'attribute':values[1] if values else None,'specialty':values[2] if values else None,'release':f.get('releaseDate','')[:10] or None,'source':'https://zenless-zone-zero.fandom.com/wiki/'+urllib.parse.quote(title.replace(' ','_')),'official':{lang:loc.get('source_'+lang) for lang in ['ja','zh']},'checked':datetime.datetime.now(datetime.timezone.utc).date().isoformat()}
        if loc.get('source_ja'):agents[d['slug']]['official']['en']=loc['source_ja'].replace('/ja-jp/','/en-us/')
        print('Agent:',d['slug'],flush=True)
    version_text=api(action='expandtemplates',text='{{Versions|1}}{{Versions|2}}{{Versions|3}}',prop='wikitext')['expandtemplates']['wikitext']
    versions=[]
    for block in version_text.split('|-'):
        match=re.search(r'^\s*\|([123]\.\d+)\n',block)
        date=re.search(r'\|data-sort-value="[^"]+"\|([^\n]+)',block)
        if match and date:versions.append((datetime.datetime.strptime(date[1],'%B %d, %Y').date().isoformat(),match[1]))
    versions.sort()
    for agent in agents.values():
        choices=[v for date,v in versions if agent['release'] and date<=agent['release']]
        agent['version']=choices[-1] if choices else None
        agent['version_source']='https://zenless-zone-zero.fandom.com/wiki/Version/'+agent['version'] if agent['version'] else None
    factions=pages(sorted({a['faction'] for a in agents.values() if a['faction']}))
    vocabulary=pages(sorted({a[k] for a in agents.values() for k in ['attribute','specialty'] if a[k]}))
    labels={}
    for title,txt in (factions|vocabulary).items():
        groups={}
        for number,lang,value in re.findall(r'^\|\s*(?:(\d+)_)?(en|ja|zhs)\s*=\s*(.*?)\s*$',txt,re.M):
            groups.setdefault(number,{})[lang]=value.strip()
        for group in groups.values():
            key=group.get('en',title)
            if 'ja' in group and 'zhs' in group:
                labels[key]={'en':key,'ja':group['ja'],'zh':group['zhs'],'source':'https://zenless-zone-zero.fandom.com/wiki/'+urllib.parse.quote(title.replace(' ','_'))}
    (ROOT/'tools/reference_labels.json').write_text(json.dumps(labels,ensure_ascii=False,indent=2)+'\n')
    requested={s['file'].replace('.png','.webp'):s['wiki_file'] for s in sources}
    for rec in skins.values():
        for item in rec['items']:requested[item['file'].replace('.png','.webp')]=item['wiki_file']
    used=set()
    for record in data:
        used.add(record['official']+'.webp')
        if record.get('skin'):used.add(record['skin']['official']+'.webp')
        used.update(o['file'] for o in record['outfits'])
    requested={key:title for key,title in requested.items() if key in used}
    info={}
    all_titles=sorted(set(v.replace('_',' ') for v in requested.values()))
    for i in range(0,len(all_titles),15):
        r=api(action='query',prop='imageinfo',iiprop='url|size|mime',titles='|'.join(all_titles[i:i+15]))
        for p in r['query']['pages'].values():
            ii=p.get('imageinfo',[None])[0]
            if ii:info[p['title'].replace('_',' ')]=ii
    (ROOT/'originals').mkdir(exist_ok=True)
    def archive(pair):
        key,title=pair;ii=info.get(title.replace('_',' '))
        if not ii:raise ValueError('Missing original '+title)
        if urllib.parse.urlparse(ii['url']).hostname!='static.wikia.nocookie.net':raise ValueError('Unexpected original host')
        ii=dict(ii);ii['url']+=('&' if '?' in ii['url'] else '?')+'format=original'
        filename=re.sub(r'[^a-zA-Z0-9_-]','_',key.removesuffix('.webp'))+'.png'
        target=ROOT/'originals'/filename
        with urllib.request.urlopen(urllib.request.Request(ii['url'],headers=UA),timeout=90) as r:content=r.read()
        image=Image.open(io.BytesIO(content))
        if image.format!='PNG' or image.size!=(ii['width'],ii['height']):raise ValueError(('Original mismatch',key,image.format,image.size,len(content),ii))
        target.write_bytes(content)
        return key,{'file':'originals/'+filename,'width':image.width,'height':image.height,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'source':ii['url'],'page':ii['descriptionurl'],'format':'PNG'}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:art=dict(pool.map(archive,requested.items()))
    (ROOT/'tools/reference.json').write_text(json.dumps({'agents':agents,'art':art},ensure_ascii=False,indent=2)+'\n')
    print('Originals:',len(art),sum(a['bytes'] for a in art.values())/1e6,'MB')
if __name__=='__main__':main()
