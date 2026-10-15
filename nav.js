/* ═══════════════════════════════════════════════════════════════════════════
   ROS INNOVATORS LEAGUE — navigation v2 (intent-based, 15 Oct 2026)

   Six top-level intents: Companies · What's New · Sectors & Theses · Capital ·
   Calendar · Jobs. Each intent (except Jobs, a single page) opens a one-column
   landing panel on CLICK — never on hover — listing its tools with a one-line
   description and a live count.

   This file owns, on every page (scripts/unify_nav.py injects it after <nav>):
     1. Panel open / close (click, Escape, click-outside, keyboard).
     2. The mobile drawer (hamburger) under 1100px.
     3. Live counts: `[data-count="key"]` elements anywhere on the page are
        filled from in-page globals when the page has them (COMPANIES, WIRE,
        RADAR, JOBS_STATS, CHANGELOG_WEEKLY …) and otherwise from the tiny
        data/nav_counts.json built by scripts/build_nav_counts.js.
     4. Plausible custom events ("Nav Click", "Nav Open", "Tool Click",
        "Door Click") so the nav can be re-ordered by use after a month.
        They queue harmlessly until window.__TIL_PLAUSIBLE_DOMAIN is set in
        config.js AND the site exists in Plausible.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var nav = document.querySelector('.nav.nav-v2');
  if (!nav) return;

  var links  = nav.querySelector('.nav-links');
  var burger = nav.querySelector('.mobile-menu-btn');
  var groups = Array.prototype.slice.call(nav.querySelectorAll('.nav-group'));
  var MOBILE_MAX = 1100; // keep in sync with the "NAV v2" block in styles.css
  var page = (location.pathname.split('/').pop() || 'index.html').toLowerCase();

  function isMobile() { return window.innerWidth <= MOBILE_MAX; }

  /* ───────── analytics ───────── */
  function track(name, props) {
    try {
      if (typeof window.plausible === 'function') window.plausible(name, { props: props || {} });
    } catch (e) { /* analytics must never break navigation */ }
  }

  /* ───────── panels ───────── */
  function setOpen(group, open) {
    var btn = group.querySelector('.nav-group-btn');
    var panel = group.querySelector('.nav-panel');
    group.classList.toggle('open', open);
    if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (panel) panel.hidden = !open;
  }
  function closeAll(except) {
    groups.forEach(function (g) { if (g !== except) setOpen(g, false); });
  }

  groups.forEach(function (group) {
    var btn = group.querySelector('.nav-group-btn');
    if (!btn) return;
    setOpen(group, false);
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      var open = !group.classList.contains('open');
      closeAll(group);
      setOpen(group, open);
      if (open) track('Nav Open', { group: group.getAttribute('data-nav-group'), page: page });
    });
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' && group.classList.contains('open')) {
        e.preventDefault();
        var first = group.querySelector('.nav-panel-item');
        if (first) first.focus();
      }
    });
    group.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
      var items = Array.prototype.slice.call(group.querySelectorAll('.nav-panel-item, .nav-panel-foot a'));
      var i = items.indexOf(document.activeElement);
      if (i < 0) return;
      e.preventDefault();
      var next = items[i + (e.key === 'ArrowDown' ? 1 : -1)];
      if (next) next.focus(); else if (e.key === 'ArrowUp') btn.focus();
    });
  });

  document.addEventListener('click', function (e) {
    if (!nav.contains(e.target)) closeAll();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeAll();
      if (links && links.classList.contains('open')) toggleDrawer(false);
    }
  });
  nav.addEventListener('focusout', function (e) {
    if (isMobile()) return;
    if (e.relatedTarget && !nav.contains(e.relatedTarget)) closeAll();
  });

  /* ───────── mobile drawer ─────────
     The legacy initMobileMenu() in app.js / utils.js also binds this button
     (it toggles the same classes), which would open-then-close the drawer.
     A capture-phase listener on document runs first in every browser and
     stops the event before the button's own listeners see it. */
  function toggleDrawer(force) {
    if (!links || !burger) return;
    var open = typeof force === 'boolean' ? force : !links.classList.contains('open');
    links.classList.toggle('open', open);
    burger.classList.toggle('open', open);
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    document.body.classList.toggle('nav-drawer-open', open);
    if (!open) closeAll();
  }
  if (burger) {
    burger.setAttribute('aria-expanded', 'false');
    burger.setAttribute('aria-controls', links && links.id ? links.id : 'nav-links');
    document.addEventListener('click', function (e) {
      if (e.target === burger || burger.contains(e.target)) {
        e.stopPropagation();
        e.stopImmediatePropagation();
        toggleDrawer();
      }
    }, true);
  }
  if (links) {
    links.addEventListener('click', function (e) {
      var a = e.target.closest ? e.target.closest('a') : null;
      if (a && links.classList.contains('open')) toggleDrawer(false);
    });
  }
  window.addEventListener('resize', function () {
    if (!isMobile() && links && links.classList.contains('open')) toggleDrawer(false);
  });

  /* ───────── search button ─────────
     Pages with the global search (the homepage hero) focus it in place;
     every other page goes to the database search. */
  var searchBtn = nav.querySelector('.nav-search-btn');
  if (searchBtn) {
    searchBtn.addEventListener('click', function (e) {
      var field = document.getElementById('global-search');
      if (field) {
        e.preventDefault();
        if (links && links.classList.contains('open')) toggleDrawer(false);
        window.scrollTo({ top: 0, behavior: 'smooth' });
        field.focus();
      }
      track('Nav Click', { group: 'top', item: 'search', page: page });
    });
  }

  /* ───────── click tracking ───────── */
  document.addEventListener('click', function (e) {
    var el = e.target.closest ? e.target.closest('a, button') : null;
    if (!el) return;
    if (nav.contains(el) && (el.classList.contains('nav-panel-item') || el.classList.contains('nav-link') || el.closest('.nav-panel-foot'))) {
      var group = el.closest('.nav-group');
      track('Nav Click', {
        group: group ? group.getAttribute('data-nav-group') : 'top',
        item: el.getAttribute('data-nav-id') || (el.getAttribute('href') || '').replace(/\.html.*$/, '') || el.textContent.trim(),
        page: page
      });
      return;
    }
    var kind = el.getAttribute('data-track');
    if (kind === 'tool-card') track('Tool Click', { tool: el.getAttribute('data-tool') || '', page: page });
    else if (kind === 'door') track('Door Click', { door: el.getAttribute('data-door') || '', page: page });
  });

  /* ───────── live counts ───────── */
  function fmt(n) {
    n = Number(n);
    if (!isFinite(n)) return '';
    return n.toLocaleString('en-US');
  }
  function inPageCounts() {
    var c = {};
    try {
      if (typeof COMPANIES !== 'undefined' && COMPANIES.length) {
        c.companies = COMPANIES.length;
        var inv = {}, countries = {};
        COMPANIES.forEach(function (co) {
          (co.investors || []).forEach(function (i) { if (i) inv[i] = 1; });
          if (co.country) countries[co.country] = 1;
        });
        c.investors = Object.keys(inv).length;
        if (Object.keys(countries).length) c.countries = Object.keys(countries).length;
      }
      if (typeof SECTORS !== 'undefined') c.sectors = Object.keys(SECTORS).length;
      if (typeof INNOVATORS_LEAGUE_30 !== 'undefined') c.il30 = INNOVATORS_LEAGUE_30.length;
      if (typeof WIRE !== 'undefined' && WIRE.stats) {
        c.wire_events_week = WIRE.stats.events_this_week;
        c.wire_events = WIRE.stats.events;
        c.companies_moved = WIRE.stats.companies_moved;
        c.wire_generated_at = WIRE.generated_at;
      }
      if (typeof RADAR !== 'undefined' && RADAR.stats) c.radar_30d = RADAR.stats.filings_30d;
      if (typeof JOBS_STATS !== 'undefined') { c.jobs = JOBS_STATS.totalJobs; c.jobs_companies = JOBS_STATS.companiesHiring; }
      else if (typeof JOBS_DATA !== 'undefined') c.jobs = JOBS_DATA.length;
      if (typeof CHANGELOG_WEEKLY !== 'undefined' && CHANGELOG_WEEKLY) c.changelog_added = (CHANGELOG_WEEKLY.added || []).length;
      var ann = window.COMPANY_ANNOUNCEMENTS_AUTO;
      if (ann && ann.results) {
        var n = 0;
        ann.results.forEach(function (r) {
          (r.hits || []).forEach(function (h) { if (h && h.title && h.age_days != null && h.age_days <= 30) n++; });
        });
        c.rounds_30d = n;
      }
    } catch (e) { /* counts are decoration */ }
    Object.keys(c).forEach(function (k) { if (c[k] === undefined || c[k] === null) delete c[k]; });
    return c;
  }
  function apply(counts, root) {
    var scope = root || document;
    var els = scope.querySelectorAll('[data-count]');
    Array.prototype.forEach.call(els, function (el) {
      var key = el.getAttribute('data-count');
      var v = counts[key];
      if (v === undefined || v === null || v === '' || (typeof v === 'number' && !(v > 0) && !el.hasAttribute('data-count-zero'))) return;
      var label = el.getAttribute('data-count-label');
      var text = typeof v === 'number' ? fmt(v) : String(v);
      el.innerHTML = label ? text + ' <small>' + label + '</small>' : text;
      el.removeAttribute('data-count-pending');
    });
  }

  var fetched = null;
  function fetchCounts() {
    if (fetched) return fetched;
    if (typeof fetch !== 'function') { fetched = Promise.resolve({}); return fetched; }
    var day = new Date().toISOString().slice(0, 10);
    fetched = fetch('data/nav_counts.json?v=' + day, { cache: 'force-cache' })
      .then(function (r) { return r.ok ? r.json() : {}; })
      .catch(function () { return {}; });
    return fetched;
  }
  var merged = {};
  var ready = fetchCounts().then(function (json) {
    merged = Object.assign({}, json || {}, inPageCounts());
    apply(merged);
    return merged;
  });
  // In-page data loads in the body, after this deferred script — apply again
  // once everything has run so globals win over the JSON snapshot.
  window.addEventListener('load', function () { merged = Object.assign({}, merged, inPageCounts()); apply(merged); });

  window.TILNav = {
    counts: function () { return ready; },
    apply: function (root) { apply(merged, root); },
    track: track,
    closePanels: closeAll
  };
})();
