"""Favourites state transitions and generated-page integration."""
import json
import re
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent


class FavouriteTests(unittest.TestCase):
    def test_top_ten_summary(self):
        subprocess.run(['node', '-e', r'''
const assert=require('node:assert/strict');
const B=require('./tools/favourites.js'),roster=require('./tools/data.json');
const top=['remielle','eldreda_sunbringer','yi_xuan','velina','astra_yao','evelyn','yanagi','jane_doe','sigrid','yidhari'];
let board=B.empty();board.tiers[0]=top.slice(0,2);board.tiers[1]=top.slice(2);board.tiers[6]=['koleda'];
const before=JSON.stringify(roster),result=B.summary(board,roster);
assert.equal(result.count,10);assert.equal(result.bust.median,74.85);assert.equal(result.rosterBust.median,64.05);
assert.deepEqual(result.findings.map(f=>[f.field,f.tag]),[['hips','Wide'],['height','Tall'],['thighs','Thick']]);
assert.equal(result.thighPins,6);
const cups=result.groups.find(g=>g.field==='bust');
assert.deepEqual(cups.categories.filter(c=>c.count).map(c=>[c.tag,c.count]),[['DD-E',2],['F-G',5],['GG+',3]]);
const build=result.groups.find(g=>g.field==='balance');assert.equal(build.categories.find(c=>c.tag==='Balanced').count,9);
assert(!result.findings.some(f=>f.field==='balance'));
board.numbering='tier';assert.deepEqual(B.summary(board,roster),result);
board.tiers[0].reverse();assert.deepEqual(B.summary(board,roster),result);
board=B.move(board,'koleda',0,board.tiers[0][0]);const changed=B.summary(board,roster);
assert.equal(changed.groups.find(g=>g.field==='thighs').count,9);
assert.equal(changed.groups.find(g=>g.field==='thighs').rosterCount,49);
assert.notEqual(changed.bust.median,result.bust.median);
const small=B.empty();small.tiers[0]=top.slice(0,4);assert.equal(B.summary(small,roster).findings.length,0);
small.tiers[0].push('koleda');assert(!B.summary(small,roster).findings.some(f=>f.field==='thighs'));
assert.equal(B.summary(B.empty(),roster).bust.median,null);
const onlyKoleda=B.empty();onlyKoleda.tiers[0]=['koleda'];assert.equal(B.summary(onlyKoleda,roster).groups.find(g=>g.field==='thighs').count,0);
const tied=B.empty();tied.tiers[0]=['miyabi','vivian','belle','anby','burnice',...top.slice(0,5)];
const tieResult=B.summary(tied,roster),heights=tieResult.groups.find(g=>g.field==='height');
assert.equal(heights.categories.find(c=>c.tag==='Mid').count,5);assert.equal(heights.categories.find(c=>c.tag==='Tall').count,5);
assert(!tieResult.findings.some(f=>f.field==='height'));
const missing=structuredClone(roster);missing.find(d=>d.slug==='miyabi').bust_cm=null;
assert.equal(B.summary(tied,missing).bust.count,9);
board.includeSummary=true;assert.equal(B.parse(JSON.parse(JSON.stringify(board)),roster.map(d=>d.slug)).includeSummary,true);
assert.equal(B.parse({v:1,title:'old',tiers:B.empty().tiers},roster.map(d=>d.slug)).includeSummary,false);
assert.equal(JSON.stringify(roster),before);
'''], cwd=ROOT, check=True)

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
assert.deepEqual(wrapText('Bust measurement',measure,110,3,false,true),['Bust','measurement']);
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
            for record in json.loads((ROOT / 'tools/data.json').read_text()):
                for field, tag in record['tags'].items():
                    if tag not in ('n/a', '?'):
                        self.assertIn(f'favTrait_{field}_{tag}', copy[lang])
        page = (ROOT / 'docs/favourites.html').read_text()
        for marker in ('data-page="favourites"', 'id="favBoard"', 'id="favDownload"',
                       'id="favPreview"', 'const siteTheme', "'image/jpeg',0.9", 'download="zzz-favourites.jpg"', 'const FAVOURITES_DATA'):
            self.assertIn(marker, page)
        payload = json.loads(re.search(r'const FAVOURITES_DATA = (.*?);\n', page)[1])
        source = {d['slug']: d for d in json.loads((ROOT / 'tools/data.json').read_text())}
        self.assertEqual(set(d['slug'] for d in payload), set(source))
        for record in payload:
            for field in ('tags', 'tags_ja', 'tags_zh', 'bust_cm', 'thigh_pin'):
                self.assertEqual(record[field], source[record['slug']][field])
        for path in ('index.html', 'tools.html'):
            self.assertIn('id="favouritesLink"', (ROOT / 'docs' / path).read_text())
        for path in ('sw.js', 'sitemap.xml', 'manifest.webmanifest'):
            self.assertIn('favourites.html', (ROOT / 'docs' / path).read_text())


if __name__ == '__main__':
    unittest.main()
