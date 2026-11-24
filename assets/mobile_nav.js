// Native dialog supplies focus trapping, Escape handling, and inert background.
(() => {
  const toggle = document.querySelector('.mobile-menu-toggle');
  const drawer = document.getElementById('mobile-menu');
  if (!toggle || !drawer || toggle.dataset.bound) return;
  toggle.dataset.bound = 'true';
  const main = document.querySelector('[data-testid="stMain"]');
  let overflow = '';
  toggle.addEventListener('click', () => {
    overflow = main.style.overflow;
    main.style.overflow = 'hidden';
    drawer.showModal();
    toggle.setAttribute('aria-expanded', 'true');
  });
  drawer.addEventListener('close', () => {
    main.style.overflow = overflow;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.focus({preventScroll: true});
  });
  drawer.querySelector('.drawer-close').addEventListener('click', () => drawer.close());
  drawer.addEventListener('click', event => {
    const bounds = drawer.getBoundingClientRect();
    if (event.target === drawer && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) drawer.close();
    const link = event.target.closest('a');
    if (!link) return;
    drawer.close();
    if (link.hash && link.pathname === location.pathname) {
      event.preventDefault();
      history.replaceState(null, '', link.hash);
      document.getElementById(link.hash.slice(1))?.scrollIntoView();
    }
  });
  matchMedia('(min-width: 901px)').addEventListener('change', event => {
    if (event.matches && drawer.open) drawer.close();
  });
})();
