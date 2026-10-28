"""Favourites state transitions and generated-page integration."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent


class FavouriteTests(unittest.TestCase):
    def test_export_name_wrapping(self):
        subprocess.run(['node', '-e', r'''
const assert=require('node:assert/strict');
const {wrapText}=require('./tools/favourites.js');
const measure=s=>Array.from(s).length*10;
assert.deepEqual(wrapText('Eldreda Sunbringer',measure,110,3,true),['Eldreda Su-','nbringer']);
assert.deepEqual(wrapText('Jane Doe',measure,80,3,true),['Jane Doe']);
assert.deepEqual(wrapText('Astra Yao',measure,60,3,true),['Astra','Yao']);
assert.deepEqual(wrapText('Aria (Construct)',measure,100,3,true),['Aria (Con-','struct)']);
assert.deepEqual(wrapText('エルダ・サンブリンガー',measure,60,3),['エルダ・サン','ブリンガー']);
assert.deepEqual(wrapText('Long title text',measure,60,1),['Long…']);
for(const d of require('./tools/data.json')){
  const lines=wrapText(d.display,measure,110,3,true);
  assert(lines.every(line=>measure(line)<=110));
  assert.equal(lines.join('').replaceAll('-','').replaceAll(' ',''),d.display.replaceAll('-','').replaceAll(' ',''));
}
'''], cwd=ROOT, check=True)

    def test_real_board_operations(self):
        subprocess.run(['node', '-e', r'''
const assert=require('node:assert/strict');
const B=require('./tools/favourites.js');
const roster=require('./tools/data.json').map(d=>d.slug);
assert.deepEqual(B.tiers,['SSS','S','A','B','C','D','E']);
assert.deepEqual(B.colours,['#F2A621','#FFD500','#AC61F2','#3686F5','#C4C8CE','#92969E','#50545C']);
let board=B.empty();
for(const slug of roster)board=B.move(board,slug,1);
assert.equal(new Set(board.tiers.flat()).size,roster.length);
assert.equal(B.ranks(board)[1].at(-1).rank,roster.length);
const original=JSON.stringify(board);
let next=B.move(board,roster[4],0);
assert.equal(JSON.stringify(board),original);
assert.equal(next.tiers[0][0],roster[4]);
assert.equal(next.tiers.flat().filter(s=>s===roster[4]).length,1);
next=B.move(next,roster[0],1,roster[2]);
assert.equal(next.tiers[1].indexOf(roster[0])+1,next.tiers[1].indexOf(roster[2]));
next=B.move(next,roster[0],-1);
assert(!next.tiers.flat().includes(roster[0]));
assert.equal(B.ranks(next)[1][0].rank,2);
next.numbering='tier';assert.equal(B.ranks(next)[1][0].rank,1);
assert.deepEqual(B.parse(JSON.parse(JSON.stringify(next)),roster),next);
assert.equal(B.parse({v:1,tiers:[[]]},roster),null);
assert.equal(B.parse({v:2,tiers:B.empty().tiers},roster),null);
assert.equal(B.parse({...B.empty(),tiers:[null,[],[],[],[],[],[]]},roster),null);
const messy={...B.empty(),title:'x'.repeat(100),tiers:[[roster[0],'missing',roster[0]],[],[roster[0]],[],[],[],[]]};
const cleaned=B.parse(messy,roster);assert.equal(cleaned.title.length,80);assert.deepEqual(cleaned.tiers.flat(),[roster[0]]);
const url=new URL('https://example.org/favourites.html');url.hash=new URLSearchParams({board:JSON.stringify(next)});
assert.deepEqual(B.parse(JSON.parse(new URLSearchParams(url.hash.slice(1)).get('board')),roster),next);
'''], cwd=ROOT, check=True)

    def test_page_and_locale_coverage(self):
        copy = json.loads((ROOT / 'tools/favourites_i18n.json').read_text())
        self.assertEqual(set(copy), {'en', 'ja', 'zh'})
        for lang in copy:
            self.assertEqual(set(copy[lang]), set(copy['en']))
            self.assertTrue(all(copy[lang].values()))
        page = (ROOT / 'docs/favourites.html').read_text()
        for marker in ('data-page="favourites"', 'id="favBoard"', 'id="favDownload"',
                       'id="favPreview"', 'const siteTheme', "'image/jpeg',0.9", 'download="zzz-favourites.jpg"', 'const FAVOURITES_DATA'):
            self.assertIn(marker, page)
        for path in ('index.html', 'tools.html'):
            self.assertIn('id="favouritesLink"', (ROOT / 'docs' / path).read_text())
        for path in ('sw.js', 'sitemap.xml', 'manifest.webmanifest'):
            self.assertIn('favourites.html', (ROOT / 'docs' / path).read_text())


if __name__ == '__main__':
    unittest.main()
