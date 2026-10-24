"""Owner-supplied Eldreda record, estimates and portrait-only rendering."""
import json,re,subprocess,unittest
from pathlib import Path
from analysis_math import size_parts,cup_size,cup_distribution,cup_matrix
ROOT=Path(__file__).resolve().parent.parent
class EldredaTests(unittest.TestCase):
 def test_supplied_values_and_provenance(self):
  data=json.loads((ROOT/'tools/data.json').read_text());e=next(d for d in data if d['slug']=='eldreda_sunbringer')
  for key,value in {'cm':193.37,'stature_cm':180.37,'bust_cm':86.52,'band_cm':57,'waist_cm':54.14,'hip_cm':92.5,'thigh_cm':56.82,'uk':'23HH','us':'≈23L','eu':'≈50L'}.items():self.assertEqual(e[key],value,key)
  self.assertFalse(e['sheet_available']);self.assertEqual(e['measurement_source'],'project_estimate');self.assertEqual(e['confidence'],'estimated')
  self.assertEqual(e['estimated_cup_systems'],['us','eu']);self.assertEqual(e['height_appendage'],'horns')
  for lang in ['','ja/','zh/']:
   html=(ROOT/'docs'/lang/'characters/eldreda_sunbringer.html').read_text()
   for value in ['180.37','193.37','86.52','54.14','56.82','≈23L','≈50L','modelmetrics.net']:self.assertIn(value,html)
   self.assertNotIn('/images/eldreda_sunbringer.webp',html)
   self.assertIn(lang+'characters/eldreda_sunbringer.html',(ROOT/'docs/sitemap.xml').read_text())
 def test_estimates_group_without_changing_uk_rank(self):
  self.assertEqual(size_parts('≈50L'),{'band':50,'cup':'L'});self.assertIsNone(cup_size('≈23HH'))
  self.assertGreater(cup_size('22H')['score'],cup_size('23HH')['score'])
  records=[{'slug':'estimate','uk':'23HH','us':'≈23L','eu':'≈50L'}]
  for system in ['uk','us','eu']:
   self.assertEqual(cup_distribution(records,system)['count'],1)
   self.assertEqual(cup_matrix(records,system)['cells'][0]['slugs'],['estimate'])
 def test_display_switch_preserves_source_note(self):
  data=json.loads((ROOT/'tools/data.json').read_text());e=next(d for d in data if d['slug']=='eldreda_sunbringer')
  source=(ROOT/'tools/template.html').read_text()
  fn=re.search(r'function descFor\(d\)\{.*?\n\}',source,re.S).group()
  script='const d='+json.dumps(e)+';let state={unit:"cm",lang:"en"};function cupText(d){return "EU "+d.eu};'+fn+';for(const lang of ["en","ja","zh"]){state.lang=lang;const out=descFor(d);if(!out.includes("EU ≈50L")||!out.includes("UK 23HH"))throw Error(lang+" source size lost");}'
  subprocess.run(['node'],input=script,text=True,check=True)
if __name__=='__main__':unittest.main()
