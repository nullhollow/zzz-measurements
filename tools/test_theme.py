"""Theme preference, no-JavaScript fallback and palette contrast regressions."""
from pathlib import Path
import re
import subprocess
import unittest

from theme import PALETTE, adaptive_css

ROOT = Path(__file__).resolve().parent.parent


def contrast(first, second):
    def luminance(colour):
        channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
        return sum(c * weight for c, weight in zip(linear, (.2126, .7152, .0722)))
    a, b = sorted((luminance(first), luminance(second)))
    return (b + .05) / (a + .05)


class ThemeTests(unittest.TestCase):
    def test_preference_precedence_and_browser_changes(self):
        script = r'''
const {runInNewContext} = require('node:vm');
const assert = require('node:assert/strict');
const source = require('node:fs').readFileSync('tools/theme.js', 'utf8');
function boot({saved=null,hash='',light=false,blocked=false}={}) {
  const root={dataset:{}},meta={},store=new Map([['zzz-theme',saved]]);
  let listener;
  const media={matches:light,addEventListener(type,fn){assert.equal(type,'change');listener=fn;}};
  const ctx={window:{matchMedia:()=>media},document:{documentElement:root,querySelector:()=>meta},
    location:{hash},URLSearchParams,localStorage:{getItem:k=>{if(blocked)throw Error();return store.get(k);},
      setItem:(k,v)=>{if(blocked)throw Error();store.set(k,v);}}};
  runInNewContext(source+';this.theme=siteTheme',ctx);
  return {root,meta,store,theme:ctx.theme,change(light){media.matches=light;listener();}};
}
for (const light of [true,false]) {
  const a=boot({light});assert.equal(a.theme.preference,'system');
  assert.equal(a.root.dataset.theme,light?'light':'dark');
  a.change(!light);assert.equal(a.root.dataset.theme,light?'dark':'light');
  assert.equal(a.meta.content,light?'#0B0B0C':'#F2F4F6');
}
for (const saved of ['light','dark']) {
  const a=boot({saved,light:saved==='dark'});assert.equal(a.root.dataset.theme,saved);
  a.change(true);a.change(false);assert.equal(a.root.dataset.theme,saved);
  a.theme.set('system');assert.equal(a.store.get('zzz-theme'),'system');
  a.change(true);assert.equal(a.root.dataset.theme,'light');
  a.theme.set('dark');assert.equal(a.root.dataset.theme,'dark');assert.equal(a.store.get('zzz-theme'),'dark');
}
assert.equal(boot({saved:'dark',hash:'#th=light'}).theme.preference,'light');
assert.equal(boot({saved:'light',hash:'#th=system'}).theme.preference,'system');
assert.equal(boot({saved:'dark',hash:'#th=invalid'}).theme.preference,'dark');
assert.equal(boot({saved:'invalid',light:true}).root.dataset.theme,'light');
const a=boot({blocked:true,light:true});a.theme.set('dark');a.theme.set('system');
assert.equal(a.root.dataset.theme,'light');
'''
        subprocess.run(['node', '-e', script], cwd=ROOT, check=True)

    def test_palette_pairs(self):
        blocks = re.findall(r'\{([^{}]+)\}', PALETTE)
        dark = dict(re.findall(r'(--[\w-]+):\s*(#[\da-fA-F]+)', blocks[0]))
        light = dark | dict(re.findall(r'(--[\w-]+):\s*(#[\da-fA-F]+)', blocks[1]))
        for name, palette in [('dark', dark), ('light', light)]:
            for foreground in ('concrete', 'dim', 'dimmer', 'acid', 'hazard', 'signal', 'blue',
                               'brass', 'tan', 'bust', 'waist', 'hips', 'thighs'):
                for surface in ('ink', 'panel', 'panel2', 'coal'):
                    with self.subTest(theme=name, text=foreground, surface=surface):
                        self.assertGreaterEqual(contrast(palette['--' + foreground], palette['--' + surface]), 4.5)
            self.assertGreaterEqual(contrast(palette['--accent-fill'], palette['--on-accent']), 4.5)
            for surface in ('ink', 'panel', 'panel2'):
                self.assertGreaterEqual(contrast(palette['--control-line'], palette['--' + surface]), 3)

    def test_no_javascript_and_all_page_templates(self):
        css = adaptive_css('html[data-theme="light"] .label{color:#000}')
        self.assertIn('@media(prefers-color-scheme:light)', css)
        self.assertIn('html:not([data-theme]) .label{color:#000}', css)
        for path in ('index.html', 'tools.html', 'characters/jane_doe.html', 'ja/characters/miyabi.html',
                     'zh/methodology.html', 'offline.html', '404.html'):
            text = (ROOT / 'docs' / path).read_text()
            with self.subTest(path=path):
                self.assertLess(text.index('const siteTheme'), text.index('<style>'))
                self.assertIn('@media(prefers-color-scheme:light)', text)
        for path in ('index.html', 'tools.html'):
            text = (ROOT / 'docs' / path).read_text()
            self.assertIn("p.set('th',siteTheme.preference)", text)
            for label in ('System', '端末に合わせる', '跟随系统'):
                self.assertIn(label, text)


if __name__ == '__main__':
    unittest.main()
