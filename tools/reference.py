"""Cited game metadata and source-original gallery records, separate from measurements."""
import json
from pathlib import Path
TOOLS=Path(__file__).resolve().parent
REFERENCE=json.loads((TOOLS/'reference.json').read_text())
LABELS=json.loads((TOOLS/'reference_labels.json').read_text())
VIEWER_KEYS=['originalViewer','previousArt','nextArt','zoomArt','fitArt','backgroundArt','neutralArt','light','dark','close','loadingArt','failedArt','downloadOriginal','sourceOriginal','retryArt','artCredit']
def label(value,lang,unknown):return LABELS.get(value,{}).get(lang,value) if value else unknown

def artwork_items(d,prefix,p,lang='en'):
    choices=[(d['official']+'.webp',d.get('outfit') or p['official_portrait'])]
    if d.get('skin'):choices.append((d['skin']['official']+'.webp',d['skin']['outfit']))
    choices += [(o['file'],p['originalOutfit'] if o.get('original') else o['label']) for o in d['outfits']]
    return [dict(REFERENCE['art'][key],file=prefix+REFERENCE['art'][key]['file'],label=(d.get("name_"+lang) or d["display"])+" · "+name) for key,name in choices if key in REFERENCE['art']]
