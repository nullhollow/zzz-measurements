"""Favourites state transitions and generated-page integration."""
import json
import re
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent


class FavouriteTests(unittest.TestCase):
    def test_top_ten_summary(self):
        subprocess.run(['node', '-e', r"""
const assert=require('node:assert/strict');
const B=require('./tools/favourites.js'),A=require('./tools/analysis.js'),roster=require('./tools/data.json');
const top=['remielle','eldreda_sunbringer','yi_xuan','velina','astra_yao','evelyn','yanagi','jane_doe','sigrid','yidhari'];
let board=B.empty();board.tiers[0]=top.slice(0,2);board.tiers[3]=top.slice(2);board.tiers[6]=['koleda'];
const before=JSON.stringify(roster),result=B.summary(board,roster);
assert.equal(result.count,10);assert(!Object.hasOwn(result,'pass'));assert(!Object.hasOwn(result,'fail'));
assert.equal(result.metrics.length,5);assert.equal(result.metrics[0].median,74.85);
assert.equal(result.cups.meanIndex,8.7);assert.equal(result.cups.meanLabel,'G');assert.deepEqual(result.cups.modes,['G']);assert.equal(result.cups.modeCount,3);
assert.equal(B.summary(board,roster,'us').cups.meanLabel,'I');
const eu=B.summary(board,roster,'eu');assert.equal(eu.cups.meanLabel,'J');assert.deepEqual(eu.cups.modes,['G','H','J','M']);assert.equal(eu.cups.estimatedCount,1);
assert.equal(result.thighPins,6);
board.numbering='tier';board.tiers[0].reverse();assert.deepEqual(B.summary(board,roster),result);
board=B.move(board,'vivian',6);assert.deepEqual(B.summary(board,roster),result);
board=B.move(board,'koleda',0,board.tiers[0][0]);const changed=B.summary(board,roster);
assert.equal(changed.count,10);assert.equal(changed.metrics.find(m=>m.field==='thighs').count,9);assert.notEqual(changed.metrics[0].median,result.metrics[0].median);
const small=B.empty();small.tiers[6]=['koleda','eldreda_sunbringer','miyabi','jane_doe'];
assert.equal(B.summary(small,roster).count,4);assert.equal(B.summary(small,roster).metrics.find(m=>m.field==='thighs').count,3);
const onlyKoleda=B.empty();onlyKoleda.tiers[0]=['koleda'];assert.equal(B.summary(onlyKoleda,roster).metrics.find(m=>m.field==='thighs').count,0);
assert.equal(B.summary(B.empty(),roster).cups.meanLabel,null);
assert.equal(A.cupLabelSummary([{uk:'28D'},{uk:'40DD'}]).meanLabel,'DD');
assert.equal(A.cupLabelSummary([{uk:'28AA'},{uk:'28A'}]).meanLabel,'A');
assert.equal(A.cupLabelSummary([{uk:'28H'},{uk:'28HH'}]).meanLabel,'HH');
assert.equal(A.cupLabelSummary([{eu:'60D'},{eu:'60E'}],'eu').meanLabel,'E');
const aliases=A.cupLabelSummary(['30E','30DD','30F','30DDD','30G','30DDDD','30BB'].map(us=>({us})),'us');
assert.equal(aliases.count,6);assert.equal(aliases.meanLabel,'DDD');assert.deepEqual(aliases.modes,['DD','DDD','DDDD']);
const estimated=A.cupLabelSummary([{us:'≈23L'}],'us');assert.equal(estimated.count,1);assert.equal(estimated.estimatedCount,1);assert(estimated.bins[0].estimated);
assert.equal(A.cupLabelSummary([{uk:'23BB'},{}]).count,0);
assert.deepEqual(A.numericSummary([1,2,3,4,null]),{count:4,median:2.5,q1:1.75,q3:3.25});
board.includeSummary=true;assert.equal(B.parse(JSON.parse(JSON.stringify(board)),roster.map(d=>d.slug)).includeSummary,true);
assert.equal(B.parse({v:1,title:'old',tiers:B.empty().tiers},roster.map(d=>d.slug)).includeSummary,false);
assert.equal(JSON.stringify(roster),before);
"""], cwd=ROOT, check=True)

    def test_cup_and_numeric_python_javascript_parity(self):
        from analysis_math import cup_label_summary, numeric_summary
        roster = json.loads((ROOT / 'tools/data.json').read_text())
        cases = [roster, roster[:10], [], [
            {'uk': '23HH', 'us': '≈23L', 'eu': '≈50L'},
            {'uk': '30D', 'us': '30E', 'eu': '65D'},
            {'uk': '30DD', 'us': '30G', 'eu': '65E'},
            {'uk': '30BB', 'us': '30BB', 'eu': '65DD'}, {},
        ]]
        numbers = [[], [None], [2], [1, 2, 3, 4, None], [d['bust_cm'] for d in roster]]
        payload = {'cases': cases, 'numbers': numbers}
        output = subprocess.check_output(['node', '-e', r"""
const A=require('./tools/analysis.js'),p=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
console.log(JSON.stringify({cups:p.cases.map(rows=>['uk','us','eu'].map(s=>A.cupLabelSummary(rows,s))),numbers:p.numbers.map(A.numericSummary)}));
"""], cwd=ROOT, input=json.dumps(payload), text=True)
        actual = json.loads(output)
        self.assertEqual(actual['cups'], [[cup_label_summary(rows, system) for system in ('uk', 'us', 'eu')] for rows in cases])
        self.assertEqual(actual['numbers'], [numeric_summary(values) for values in numbers])

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
            for field in ('bust', 'waist', 'hips', 'thighs', 'height'):
                self.assertIn(f'favMeasure_{field}', copy[lang])
        page = (ROOT / 'docs/favourites.html').read_text()
        for marker in ('data-page="favourites"', 'id="favBoard"', 'id="favDownload"',
                       'id="favPreview"', 'const siteTheme', "'image/jpeg',0.9", 'download="zzz-favourites.jpg"', 'const FAVOURITES_DATA'):
            self.assertIn(marker, page)
        payload = json.loads(re.search(r'const FAVOURITES_DATA = (.*?);\n', page)[1])
        source = {d['slug']: d for d in json.loads((ROOT / 'tools/data.json').read_text())}
        self.assertEqual(set(d['slug'] for d in payload), set(source))
        for record in payload:
            for field in ('tags', 'tags_ja', 'tags_zh', 'bust_cm', 'waist_cm', 'hip_cm', 'thigh_cm', 'stature_cm', 'uk', 'us', 'eu', 'thigh_pin'):
                self.assertEqual(record[field], source[record['slug']][field])
        for path in ('index.html', 'tools.html'):
            self.assertIn('id="favouritesLink"', (ROOT / 'docs' / path).read_text())
        for path in ('sw.js', 'sitemap.xml', 'manifest.webmanifest'):
            self.assertIn('favourites.html', (ROOT / 'docs' / path).read_text())


if __name__ == '__main__':
    unittest.main()
