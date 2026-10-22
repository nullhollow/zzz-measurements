"""Inline the shared palette and pre-paint preference on every generated page."""
import re
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
THEME_JS = (TOOLS / 'theme.js').read_text()
PALETTE = (TOOLS / 'theme.css').read_text()


def adaptive_css(css):
    """No-JavaScript pages also follow the browser unless a theme is explicit."""
    css = PALETTE + css
    light = re.findall(r'html\[data-theme="light"\][^{}]*\{[^{}]*\}', css)
    fallback = '\n'.join(rule.replace('html[data-theme="light"]', 'html:not([data-theme])')
                         for rule in light)
    return css + '\n@media(prefers-color-scheme:light){\n' + fallback + '\n}'
