"""Regression and Python/JavaScript parity tests for the exploration tools."""
import json
import math
import ast
import csv
import io
import re
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import unittest

from fontTools.ttLib import TTFont
from analysis_math import (FIELDS, WEIGHTS, bin_index, cup_distribution, cup_matrix, cup_size, difference, displayed, distribution,
                           game_outcome, matches, metric_value, outcome, percentage, size_parts)

ROOT = Path(__file__).resolve().parent.parent
ROSTER = json.loads((ROOT / 'tools/data.json').read_text())


class AnalysisTests(unittest.TestCase):
    def test_cup_categories_preserve_band_context_and_order(self):
        self.assertGreater(cup_size('19G')['score'], cup_size('24GG')['score'])
        self.assertGreater(cup_size('22E')['score'], cup_size('19E')['score'])
        self.assertEqual(cup_size('22E')['cup'], cup_size('19E')['cup'])
        self.assertNotEqual(cup_size('22E')['band'], cup_size('19E')['band'])
        self.assertEqual(cup_distribution(ROSTER)['count'], len(ROSTER))
        self.assertEqual(cup_distribution(ROSTER)['modes'], ['C'])

    def test_cup_distribution_missing_values_and_modes(self):
        data = [{'uk': '23G'}, {'uk': '19GG'}, {'uk': '20DD'}, {'uk': '21D'}, {'uk': ''}, {}]
        result = cup_distribution(data)
        self.assertEqual([b['cup'] for b in result['bins']], ['DD', 'D', 'GG', 'G'])
        self.assertEqual(result['count'], 4)
        self.assertEqual(result['modes'], ['DD', 'D', 'GG', 'G'])
        self.assertEqual(cup_distribution([]), {'count': 0, 'bins': [], 'modes': []})
        for value in (None, '', '??', '32I', 'E', '32'):
            self.assertIsNone(cup_size(value))

    def test_display_systems_use_source_values_without_conversion(self):
        self.assertEqual(size_parts('23DDDD'), {'band': 23, 'cup': 'DDDD'})
        self.assertEqual(size_parts('47I'), {'band': 47, 'cup': 'I'})
        records = [{'uk': '19E', 'eu': '37G'}, {'uk': '21E', 'eu': '42F', 'us': '21DDD'}]
        self.assertEqual(cup_distribution(records, 'us')['count'], 1)
        self.assertEqual(cup_distribution(records, 'eu')['bins'], [{'cup': 'F', 'count': 1}, {'cup': 'G', 'count': 1}])
        for system in ('uk', 'us', 'eu'):
            self.assertEqual(cup_distribution(ROSTER, system)['count'], len(ROSTER))
        self.assertEqual([b['cup'] for b in cup_distribution(ROSTER, 'us')['bins']],
                         ['A', 'B', 'C', 'D', 'DD', 'DDD', 'DDDD', 'H', 'I', 'J', 'K'])

    def test_cup_game_uses_uk_letter_then_band(self):
        for unit in ('cm', 'in'):
            for basis in ('raw', 'height', 'scaled'):
                self.assertEqual(game_outcome({'uk': '24GG'}, {'uk': '19G'}, 'cup', basis, unit), 'higher')
                self.assertEqual(game_outcome({'uk': '19E'}, {'uk': '22E'}, 'cup', basis, unit), 'higher')
                self.assertEqual(game_outcome({'uk': '22E'}, {'uk': '19E'}, 'cup', basis, unit), 'lower')
                self.assertEqual(game_outcome({'uk': '19E'}, {'uk': '19E'}, 'cup', basis, unit), 'equal')
        # Equal EU labels can represent distinct source UK ranks.
        left, right = {'uk': '21DD', 'eu': '42F'}, {'uk': '21E', 'eu': '42F'}
        self.assertEqual(game_outcome(left, right, 'cup'), 'higher')
        self.assertIsNone(game_outcome({}, right, 'cup'))

    def test_numeric_game_uses_selected_unit_precision(self):
        self.assertEqual(game_outcome({'waist_cm': 50}, {'waist_cm': 50.1}, 'waist', 'raw', 'cm'), 'higher')
        self.assertEqual(game_outcome({'waist_cm': 50}, {'waist_cm': 50.1}, 'waist', 'raw', 'in'), 'equal')

    def test_effective_height_and_scaling(self):
        miyabi = next(d for d in ROSTER if d['slug'] == 'miyabi')
        self.assertEqual(miyabi['stature_cm'], 152.1)
        self.assertEqual(metric_value(miyabi, 'height', 'scaled', 160), 152.1)
        self.assertAlmostEqual(metric_value(miyabi, 'waist', 'height'), miyabi['waist_cm'] / 152.1 * 100)
        scaled = {k: v * 2 if k in FIELDS.values() and v is not None else v for k, v in miyabi.items()}
        for key in FIELDS:
            if key == 'height':
                continue
            self.assertAlmostEqual(metric_value(miyabi, key, 'height'), metric_value(scaled, key, 'height'))
            self.assertAlmostEqual(metric_value(miyabi, key, 'scaled', 160), metric_value(scaled, key, 'scaled', 160))

    def test_missing_values_and_zero_height(self):
        koleda = next(d for d in ROSTER if d['slug'] == 'koleda')
        self.assertIsNone(metric_value(koleda, 'thigh', 'scaled'))
        self.assertIsNone(percentage(None, 160))
        self.assertIsNone(percentage(50, 0))
        self.assertIsNone(difference(None, 1))
        self.assertIsNone(difference(1, None))
        self.assertAlmostEqual(difference(31.3, 30), 1.3)

    def test_similarity_preserves_default_order(self):
        # Original rule, retained as a regression oracle for the default settings.
        keys = [('bust_cm', .25), ('waist_cm', .2), ('hip_cm', .2), ('thigh_cm', .15), ('stature_cm', .2)]
        spans = {key: max(d[key] for d in ROSTER if d[key] is not None) - min(d[key] for d in ROSTER if d[key] is not None) or 1 for key, _ in keys}
        for source in ROSTER:
            scores = []
            for d in ROSTER:
                if d['slug'] == source['slug']:
                    continue
                pairs = [(key, weight) for key, weight in keys if d[key] is not None and source[key] is not None]
                score = sum(weight * abs(d[key] - source[key]) / spans[key] for key, weight in pairs) / sum(weight for _, weight in pairs)
                scores.append((score, d['slug']))
            expected = [slug for _, slug in sorted(scores, key=lambda x: x[0])]
            self.assertEqual([x['d']['slug'] for x in matches(ROSTER, source)], expected)

    def test_similarity_missing_and_zero_weights(self):
        koleda = next(d for d in ROSTER if d['slug'] == 'koleda')
        self.assertEqual(matches(ROSTER, koleda, {'thigh': 1}), [])
        self.assertEqual(matches(ROSTER, ROSTER[0], {}), [])
        self.assertEqual(matches(ROSTER, ROSTER[0], {'waist': float('nan')}), [])
        source = {'slug': '~sandbox', 'stature_cm': 160, 'waist_cm': 40}
        self.assertEqual(len(matches(ROSTER, source, {'waist': 1}, 'height')), len(ROSTER))
        self.assertNotIn('~sandbox', [x['d']['slug'] for x in matches(ROSTER, source)])

    def test_histogram_edges_and_equal_values(self):
        result = distribution([None, *range(11)])
        self.assertEqual(result['count'], 11)
        self.assertEqual(result['median'], 5)
        self.assertEqual([b['count'] for b in result['bins']], [1] * 9 + [2])
        self.assertEqual(distribution([7, 7])['bins'], [{'lo': 7, 'hi': 7, 'count': 2}])
        self.assertEqual(distribution([None])['count'], 0)

    def test_game_displayed_ties(self):
        self.assertEqual(outcome(31.32, 31.34), 'equal')
        self.assertEqual(outcome(31.32, 31.36), 'higher')
        self.assertEqual(outcome(31.32, 31.24), 'lower')
        self.assertIsNone(outcome(None, 31))
        self.assertEqual(displayed(2.55), 2.5)

    def test_javascript_parity(self):
        fixtures = [*ROSTER, *(d['skin'] for d in ROSTER if d.get('skin')),
                    {'slug': '~sandbox', 'stature_cm': 160, 'bust_cm': 80, 'waist_cm': 50, 'hip_cm': 85, 'band_cm': None, 'thigh_cm': None}]
        payload = {'roster': ROSTER, 'fixtures': fixtures}
        js = r'''
const fs=require('fs'),vm=require('vm');
const context=vm.createContext({});
vm.runInContext(fs.readFileSync('tools/analysis.js','utf8')+';globalThis.math=Analysis;',context);
const a=context.math,p=JSON.parse(fs.readFileSync(0,'utf8'));
const values=p.fixtures.map(d=>Object.keys(a.fields).map(k=>['raw','height','scaled'].map(b=>a.value(d,k,b,172.3))));
const match=p.fixtures.map(d=>['raw','height'].map(b=>a.matches(p.roster,d,a.weights,b).map(x=>[x.d.slug,x.score])));
const dist=Object.keys(a.fields).map(k=>['raw','height','scaled'].map(b=>a.distribution(p.roster.map(d=>a.value(d,k,b,172.3)))));
const binIndices=Object.keys(a.fields).map((k,i)=>['raw','height','scaled'].map((b,j)=>p.roster.map(d=>a.binIndex(a.value(d,k,b,172.3),dist[i][j].bins))));
const rounds=[[31.32,31.34],[31.32,31.36],[31.32,31.24],[null,1],[2.55,2.56]].map(v=>a.outcome(...v));
const cups=p.fixtures.map(d=>a.cupSize(d.uk)),cupDist=['uk','us','eu'].map(s=>a.cupDistribution(p.roster,s));
const matrices=['uk','us','eu'].map(s=>a.cupMatrix(p.roster,s));
const components=p.fixtures.map(d=>['raw','height'].map(b=>a.matches(p.roster,d,a.weights,b).map(x=>x.components)));
const game=p.roster.map(left=>p.roster.map(right=>['cm','in'].map(u=>a.gameOutcome(left,right,'cup','raw',u))));
const numeric=p.fixtures.map((d,i)=>Object.keys(a.fields).map(k=>['raw','height'].map(b=>['cm','in'].map(u=>a.gameOutcome(d,p.fixtures[(i+1)%p.fixtures.length],k,b,u)))));
process.stdout.write(JSON.stringify({values,match,dist,binIndices,rounds,cups,cupDist,matrices,components,game,numeric}));
'''
        result = subprocess.run(['node', '-e', js], input=json.dumps(payload), text=True, cwd=ROOT, check=True, capture_output=True)
        expected = {
            'values': [[[metric_value(d, k, b, 172.3) for b in ('raw', 'height', 'scaled')] for k in FIELDS] for d in fixtures],
            'match': [[[[x['d']['slug'], x['score']] for x in matches(ROSTER, d, WEIGHTS, b)] for b in ('raw', 'height')] for d in fixtures],
            'dist': [[distribution([metric_value(d, k, b, 172.3) for d in ROSTER]) for b in ('raw', 'height', 'scaled')] for k in FIELDS],
            'binIndices': [[[bin_index(metric_value(d, key, basis, 172.3), distribution([metric_value(r, key, basis, 172.3) for r in ROSTER])['bins']) for d in ROSTER] for basis in ('raw', 'height', 'scaled')] for key in FIELDS],
            'rounds': [outcome(*v) for v in [(31.32, 31.34), (31.32, 31.36), (31.32, 31.24), (None, 1), (2.55, 2.56)]],
            'cups': [cup_size(d.get('uk')) for d in fixtures],
            'cupDist': [cup_distribution(ROSTER, system) for system in ('uk', 'us', 'eu')],
            'matrices': [cup_matrix(ROSTER, system) for system in ('uk', 'us', 'eu')],
            'components': [[[x['components'] for x in matches(ROSTER, d, WEIGHTS, b)] for b in ('raw', 'height')] for d in fixtures],
            'game': [[[game_outcome(left, right, 'cup', 'raw', unit) for unit in ('cm', 'in')] for right in ROSTER] for left in ROSTER],
            'numeric': [[[[game_outcome(d, fixtures[(i + 1) % len(fixtures)], key, basis, unit) for unit in ('cm', 'in')]
                          for basis in ('raw', 'height')] for key in FIELDS] for i, d in enumerate(fixtures)],
        }
        def compare(a, b):
            if isinstance(a, dict):
                self.assertEqual(a.keys(), b.keys())
                for key in a:
                    compare(a[key], b[key])
            elif isinstance(a, list):
                self.assertEqual(len(a), len(b))
                for x, y in zip(a, b):
                    compare(x, y)
            elif isinstance(a, (int, float)):
                self.assertTrue(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12), (a, b))
            else:
                self.assertEqual(a, b)
        compare(expected, json.loads(result.stdout))

    def test_similarity_components_sum_to_unchanged_distance(self):
        for basis in ('raw', 'height'):
            for source in ROSTER:
                for result in matches(ROSTER, source, basis=basis):
                    components = result['components']
                    self.assertAlmostEqual(sum(c['contribution'] for c in components), result['score'])
                    self.assertAlmostEqual(sum(c['weight'] for c in components), 1)
                    self.assertNotIn('underbust', [c['key'] for c in components])
                    self.assertTrue(all(c['difference'] >= 0 for c in components))
        koleda = next(d for d in ROSTER if d['slug'] == 'koleda')
        self.assertTrue(all('thigh' not in [c['key'] for c in r['components']] for r in matches(ROSTER, koleda)))

    def test_matrix_totals_and_source_sizes(self):
        for system in ('uk', 'us', 'eu'):
            matrix = cup_matrix(ROSTER, system)
            self.assertEqual(matrix['bands'], sorted(matrix['bands']))
            self.assertEqual(matrix['cups'], [b['cup'] for b in cup_distribution(ROSTER, system)['bins']])
            slugs = [slug for cell in matrix['cells'] for slug in cell['slugs']]
            self.assertCountEqual(slugs, [d['slug'] for d in ROSTER])
            for cell in matrix['cells']:
                for slug in cell['slugs']:
                    d = next(d for d in ROSTER if d['slug'] == slug)
                    self.assertEqual(size_parts(d[system]), {'cup': cell['cup'], 'band': cell['band']})
        self.assertEqual(cup_matrix([{'slug': '~sandbox'}]), {'bands': [], 'cups': [], 'cells': []})

    def test_chart_drilldown_uses_histogram_boundaries(self):
        for key in FIELDS:
            for basis in ('raw', 'height', 'scaled'):
                values = [metric_value(d, key, basis) for d in ROSTER]
                bins = distribution(values)['bins']
                counts = [0] * len(bins)
                for value in values:
                    index = bin_index(value, bins)
                    if value is not None:
                        counts[index] += 1
                    else:
                        self.assertEqual(index, -1)
                self.assertEqual(counts, [b['count'] for b in bins])
        self.assertEqual(bin_index(7, distribution([7, 7])['bins']), 0)
        self.assertEqual(bin_index(8, distribution([7, 7])['bins']), -1)

    def test_saved_comparison_validation_and_csv_safety(self):
        js = r'''
const fs=require('fs'),vm=require('vm'),source=fs.readFileSync('tools/explorer.js','utf8');
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const context=vm.createContext({bySlug:new Map(p.roster.map(d=>[d.slug,d])),CIRCUMFERENCES:{bust:'bust_cm',underbust:'band_cm',waist:'waist_cm',hip:'hip_cm',thigh:'thigh_cm'}});
vm.runInContext(source.slice(0,source.indexOf('let gameRound'))+
source.slice(source.indexOf('function validSandbox('),source.indexOf('function sandboxRecord('))+
source.slice(source.indexOf('function validSavedComparison('),source.indexOf('function savedComparisons('))+
source.slice(source.indexOf('function csvText('),source.indexOf('function exportComparison('))+
';this.results={groups:'+JSON.stringify(p.groups)+'.map(validSavedComparison),csv:csvText('+JSON.stringify(p.rows)+')};',context);
process.stdout.write(JSON.stringify(context.results));
'''
        group = {'name': 'Test', 'compare': ['miyabi', 'seed', 'missing', 'miyabi'],
                 'compareRows': ['waist', 'unknown', 'waist'], 'compareBase': 'missing',
                 'compareMode': 'height', 'compareHeight': 172.3, 'unit': 'in', 'cupSystem': 'eu'}
        sandbox = {'stature_cm': 160, 'name': '<script>test</script>', 'waist_cm': None}
        groups = [group, {**group, 'name': ''}, {**group, 'compare': ['miyabi']},
                  {**group, 'compare': ['miyabi', '~sandbox'], 'sandbox': sandbox},
                  {**group, 'compare': ['miyabi', '~sandbox'], 'sandbox': {'stature_cm': 0}},
                  {**group, 'compareHeight': 999, 'unit': 'invalid', 'cupSystem': 'invalid'}]
        rows = [['character', 'value'], ['=HYPERLINK("bad")', -2.5], ['中文, "quoted"', 'line1\nline2'], ['  +formula', None]]
        payload = {'roster': ROSTER, 'groups': groups, 'rows': rows}
        result = subprocess.run(['node', '-e', js], input=json.dumps(payload), text=True, cwd=ROOT, check=True, capture_output=True)
        actual = json.loads(result.stdout)
        good = actual['groups'][0]
        self.assertEqual(good['compare'], ['miyabi', 'seed'])
        self.assertEqual(good['compareRows'], ['waist'])
        self.assertEqual(good['compareBase'], '')
        self.assertEqual((good['unit'], good['cupSystem'], good['compareMode']), ('in', 'eu', 'height'))
        self.assertIsNone(actual['groups'][1])
        self.assertIsNone(actual['groups'][2])
        self.assertEqual(actual['groups'][3]['sandbox']['name'], sandbox['name'])
        self.assertIsNone(actual['groups'][4])
        self.assertEqual(actual['groups'][5]['compareHeight'], 160)
        self.assertEqual(actual['groups'][5]['unit'], 'cm')
        self.assertEqual(actual['groups'][5]['cupSystem'], 'uk')
        parsed = list(csv.reader(io.StringIO(actual['csv'].lstrip('\ufeff'))))
        self.assertEqual(parsed[1], ["'=HYPERLINK(\"bad\")", '-2.5'])
        self.assertEqual(parsed[2], rows[2])
        self.assertEqual(parsed[3], ["'  +formula", ''])

    def test_locale_key_parity(self):
        strings = json.loads((ROOT / 'tools/explorer_i18n.json').read_text())
        self.assertEqual(set(strings), {'en', 'ja', 'zh'})
        for language in ('ja', 'zh'):
            self.assertEqual(strings['en'].keys(), strings[language].keys())
            self.assertTrue(all(strings[language].values()))
        source = (ROOT / 'tools/template.html').read_text()
        blocks = re.split(r'\n  (?:en|ja|zh): \{', re.search(r'const I18N = \{(.*?)\n\};', source, re.S)[1])[1:]
        for lang, block in zip(('en', 'ja', 'zh'), blocks):
            existing = set(re.findall(r'\b(\w+):\s*[\'\"]', block))
            self.assertFalse(existing & strings[lang].keys())
        module = ast.parse((ROOT / 'tools/build_pages.py').read_text())
        page = next(ast.literal_eval(node.value) for node in module.body if isinstance(node, ast.Assign) and
                    any(isinstance(target, ast.Name) and target.id == 'PAGE' for target in node.targets))
        for lang in strings:
            self.assertFalse(page[lang].keys() & strings[lang].keys())

    def test_localized_font_coverage(self):
        class Text(HTMLParser):
            def __init__(self):
                super().__init__()
                self.hidden = False
                self.parts = []

            def handle_starttag(self, tag, attrs):
                if tag in ('script', 'style'):
                    self.hidden = True

            def handle_endtag(self, tag):
                if tag in ('script', 'style'):
                    self.hidden = False

            def handle_data(self, text):
                if not self.hidden:
                    self.parts.append(text)

        strings = json.loads((ROOT / 'tools/explorer_i18n.json').read_text())
        primary = set(TTFont(ROOT / 'fonts/ZZZ-Hongmeng-web.woff2').getBestCmap())
        for lang, face in (('ja', 'NotoSansJP'), ('zh', 'NotoSansSC')):
            content = ''.join(strings[lang].values())
            for path in (ROOT / 'docs' / lang).rglob('*.html'):
                parser = Text()
                parser.feed(path.read_text())
                content += ''.join(parser.parts)
            wanted = {ord(ch) for ch in content if 0x3000 <= ord(ch) <= 0x30ff or
                      0x3400 <= ord(ch) <= 0x9fff or 0xff00 <= ord(ch) <= 0xffef}
            if lang == 'ja':
                wanted.update(map(ord, '・見長開時'))
            for weight in ('var', '900'):
                fallback = set(TTFont(ROOT / f'fonts/{face}-{weight}-{lang if lang == "zh" else "jp"}.woff2').getBestCmap())
                self.assertFalse(wanted - (primary | fallback), ''.join(map(chr, sorted(wanted - (primary | fallback)))))


if __name__ == '__main__':
    unittest.main()
