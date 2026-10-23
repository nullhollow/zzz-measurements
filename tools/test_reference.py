"""Source-original integrity, metadata coverage and lineup regressions."""
import hashlib,json,subprocess,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
DATA=json.loads((ROOT/'tools/data.json').read_text())
REF=json.loads((ROOT/'tools/reference.json').read_text())
LABELS=json.loads((ROOT/'tools/reference_labels.json').read_text())
class ReferenceTests(unittest.TestCase):
    def test_original_files_are_unmodified_pngs(self):
        for art in REF['art'].values():
            with self.subTest(file=art['file']):
                path=ROOT/art['file'];content=path.read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(),art['sha256'])
                self.assertEqual(len(content),art['bytes'])
                with Image.open(path) as image:
                    self.assertEqual(image.format,'PNG');self.assertEqual(image.size,(art['width'],art['height']))
                self.assertEqual(content,(ROOT/'docs'/art['file']).read_bytes())
                self.assertIn('format=original',art['source'])
    def test_every_displayed_outfit_has_an_original(self):
        self.assertEqual(set(REF['agents']),{d['slug'] for d in DATA})
        for d in DATA:
            keys=[d['official']+'.webp']+([d['skin']['official']+'.webp'] if d.get('skin') else [])+[o['file'] for o in d['outfits']]
            for key in keys:self.assertIn(key,REF['art'],key)
            a=REF['agents'][d['slug']]
            for field in ['attribute','specialty','faction']:
                if a[field]:
                    for lang in ['en','ja','zh']:self.assertTrue(LABELS[a[field]].get(lang),(d['slug'],field,lang))
            self.assertTrue(a['source'].startswith('https://zenless-zone-zero.fandom.com/wiki/'))
    def test_lineup_uses_effective_height_and_preserves_order(self):
        source=(ROOT/'tools/visual_tools.js').read_text().replace('/*__REFERENCE__*/{}',json.dumps(REF)).replace('/*__REFERENCE_LABELS__*/{}',json.dumps(LABELS))
        script='const DATA='+json.dumps(DATA)+''';const bySlug=new Map(DATA.map(d=>[d.slug,d]));
const state={lang:'en',lineupSlugs:['astra_yao','miyabi','zhao'],lineupOrder:'custom'};const t=k=>k;
'''+source+'''
const assert=require('node:assert/strict');
assert.deepEqual(lineupRecords().map(d=>d.slug),state.lineupSlugs);
state.lineupOrder='short';assert.deepEqual(lineupRecords().map(d=>d.slug),['zhao','miyabi','astra_yao']);
assert.equal(lineupRecords()[1].stature_cm,152.1);
state.lineupOrder='tall';assert.equal(lineupRecords()[0].slug,'astra_yao');
state.lineupOrder='faction';assert.equal(lineupRecords().length,3);
assert.deepEqual(state.lineupSlugs,['astra_yao','miyabi','zhao']);
assert.equal(new Set(defaultLineup()).size,3);
'''
        subprocess.run(['node','-e',script],check=True)
    def test_static_profiles_and_guides(self):
        for lang in ['','ja/','zh/']:
            for d in DATA:
                html=(ROOT/'docs'/lang/'characters'/f'{d["slug"]}.html').read_text()
                self.assertIn('artworkConfig',html);self.assertIn('agent-facts',html)
                self.assertIn('data-art-index',html)
            self.assertIn('measurement-guide.webp',(ROOT/'docs'/lang/'methodology.html').read_text())
if __name__=='__main__':unittest.main()
