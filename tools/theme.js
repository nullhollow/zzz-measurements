/* Run before styles paint. An explicit URL or saved choice overrides the browser. */
const siteTheme = (() => {
  const valid = value => ['system', 'light', 'dark'].includes(value);
  const media = window.matchMedia('(prefers-color-scheme: light)');
  let preference = 'system';
  try {
    const saved = localStorage.getItem('zzz-theme');
    if (valid(saved)) preference = saved;
  } catch (_) {}
  const shared = new URLSearchParams(location.hash.slice(1)).get('th');
  if (valid(shared)) preference = shared;
  function paint() {
    const resolved = preference === 'system' ? (media.matches ? 'light' : 'dark') : preference;
    document.documentElement.dataset.theme = resolved;
    document.documentElement.dataset.themePreference = preference;
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = resolved === 'light' ? '#F2F4F6' : '#0B0B0C';
  }
  media.addEventListener('change', () => { if (preference === 'system') paint(); });
  paint();
  return {
    get preference() { return preference; },
    set(value) {
      preference = valid(value) ? value : 'system';
      try { localStorage.setItem('zzz-theme', preference); } catch (_) {}
      paint();
    }
  };
})();
