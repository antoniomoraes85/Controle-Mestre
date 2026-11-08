/* Independent of API/app startup: a missing module leaves the dashboard usable. */
const key = 'cm:intro:v071:seen';
const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
function startIntro() {
  // When storage is unavailable, prefer no intro over repeated interruptions.
  try {
    if (sessionStorage.getItem(key)) return;
    sessionStorage.setItem(key, '1');
  } catch { return; }
  if (motion.matches) return;
  const template = document.querySelector('#intro-template');
  if (!template) return;
  const intro = template.content.firstElementChild.cloneNode(true);
  let timer;
  const finish = () => {
    const focused = intro.contains(document.activeElement);
    intro.remove();
    window.dispatchEvent(new Event('cm:intro:finished'));
    clearTimeout(timer);
    document.removeEventListener('keydown', onKey);
    document.removeEventListener('focusin', onFocus);
    window.removeEventListener('pagehide', finish);
    motion.removeEventListener('change', finish);
    if (focused) document.querySelector('#content')?.focus({preventScroll: true});
  };
  const onKey = e => { if (e.key === 'Escape') finish(); };
  const onFocus = e => { if (!intro.contains(e.target)) finish(); };
  // Install the watchdog before displaying anything, independently of CSS/assets.
  timer = setTimeout(finish, 2600);
  try {
    intro.querySelector('button').addEventListener('click', finish);
    intro.addEventListener('animationend', e => {
      if (e.target === intro && e.animationName === 'intro-exit') finish();
    });
    intro.querySelector('img').addEventListener('error', finish);
    document.addEventListener('keydown', onKey);
    document.addEventListener('focusin', onFocus);
    window.addEventListener('pagehide', finish);
    motion.addEventListener('change', finish);
    document.body.prepend(intro);
    // CSS missing/blocked: never show an unstyled fullscreen experience.
    if (getComputedStyle(intro).position !== 'fixed') finish();
  } catch { finish(); }
}
startIntro();
