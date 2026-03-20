document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const toggle = document.getElementById('theme-toggle');
  if (!toggle) return;

  const applyTheme = (mode) => {
    body.classList.remove('theme-dark', 'theme-light');
    body.classList.add(mode === 'light' ? 'theme-light' : 'theme-dark');
    toggle.textContent = mode === 'light' ? 'Light' : 'Dark';
  };

  const stored = window.localStorage.getItem('gigshield-theme');
  applyTheme(stored === 'light' ? 'light' : 'dark');

  toggle.addEventListener('click', () => {
    const next = body.classList.contains('theme-light') ? 'dark' : 'light';
    applyTheme(next);
    window.localStorage.setItem('gigshield-theme', next);
  });
});