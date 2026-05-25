// anchor-scroll.js
(function () {
  'use strict';

  const prefersReducedMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const DEFAULT_BEHAVIOR = prefersReducedMotion ? 'auto' : 'smooth';

  // Center an element in the viewport (with fallback)
  function centerElement(el, behavior = DEFAULT_BEHAVIOR) {
    if (!el) return;
    // Preferred API (modern browsers)
    try {
      if ('scrollIntoView' in el && typeof el.scrollIntoView === 'function') {
        el.scrollIntoView({ behavior, block: 'center', inline: 'nearest' });
        return;
      }
    } catch (err) {
      // some browsers throw on unknown options — fall through to manual calculation
    }

    // Manual fallback
    const rect = el.getBoundingClientRect();
    const top = window.pageYOffset + rect.top - (window.innerHeight / 2) + (rect.height / 2);
    window.scrollTo({ top: Math.max(0, Math.round(top)), behavior });
  }

  // Focus without triggering additional scroll
  function focusWithoutScroll(el) {
    if (!el) return;
    const hadTabIndex = el.hasAttribute('tabindex');
    const prevTabIndex = el.getAttribute('tabindex');

    if (!hadTabIndex) el.setAttribute('tabindex', '-1');
    try {
      el.focus({ preventScroll: true });
    } catch (err) {
      el.focus();
    }
    // cleanup: if we added tabindex, remove it on next frame so screen readers still see the focus
    if (!hadTabIndex) requestAnimationFrame(() => el.removeAttribute('tabindex'));
    else el.setAttribute('tabindex', prevTabIndex);
  }

  // Click handler (event delegation)
  function onDocumentClick(e) {
    const anchor = e.target.closest && e.target.closest('a[href*="#"]');
    if (!anchor) return;

    const href = anchor.getAttribute('href');
    if (!href) return;

    // build URL relative to current location so we can support absolute and relative same-page links
    let url;
    try {
      url = new URL(href, location.href);
    } catch (err) {
      // very old browsers without URL can fallback to naive hash parse
      const hashIndex = href.indexOf('#');
      if (hashIndex === -1) return;
      const id = href.slice(hashIndex + 1);
      if (!id) return;
      const el = document.getElementById(id) || document.getElementsByName(id)[0];
      if (!el) return;
      e.preventDefault();
      centerElement(el);
      history.pushState(null, '', '#' + id);
      focusWithoutScroll(el);
      return;
    }

    // only handle same-page (same origin + same path) links
    if (url.origin !== location.origin || url.pathname !== location.pathname) return;

    const id = url.hash.slice(1);
    if (!id) return;

    const el = document.getElementById(id) || document.getElementsByName(id)[0];
    if (!el) return;

    e.preventDefault();
    centerElement(el);
    // update the URL hash without causing another jump
    history.pushState(null, '', '#' + id);
    focusWithoutScroll(el);
  }

  // If page loaded with a hash — re-center (wait for load so layout/images/fonts settle)
  function handleInitialHash() {
    if (!location.hash) return;
    const id = location.hash.slice(1);
    if (!id) return;
    const el = document.getElementById(id) || document.getElementsByName(id)[0];
    if (!el) return;

    // run after load and allow browser initial jump/layout to settle
    window.addEventListener('load', function () {
      // double rAF to give the browser time to finish initial painting/scrolling
      requestAnimationFrame(() => requestAnimationFrame(() => {
        // on initial load it's nicer to avoid smooth animation — use 'auto' for immediate centering
        centerElement(el, 'auto');
        focusWithoutScroll(el);
      }));
    });
  }

  function init() {
    document.addEventListener('click', onDocumentClick, false);
    handleInitialHash();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // expose for manual re-init (if you dynamically inject anchors and need to re-run)
  window.__anchorScrollInit = init;
})();
