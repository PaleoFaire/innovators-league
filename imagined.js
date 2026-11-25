/* Who's Building It (imagined.html)
 *
 * Reads window IMAGINED (data/imagined_auto.js, built by scripts/build_imagined.py) and draws:
 * the featured pairing, the counters, the filters and one card per idea. The page holds no
 * data of its own: every word on a card comes from data/imagined/themes.json.
 *
 * The pure helpers (filter, sort, dates, URL state) are exported for
 * scripts/tests/test_imagined_page.js, which runs them under Node without a browser.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  } else {
    root.WhoIsBuilding = api;
    if (typeof document !== 'undefined' && typeof IMAGINED !== 'undefined') {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { api.start(IMAGINED); });
      } else {
        api.start(IMAGINED);
      }
    }
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var STATUS_ORDER = ['built', 'demonstrated', 'in_development', 'still_fiction'];
  var SORTS = ['oldest', 'newest', 'companies', 'status', 'az'];
  var CHIP_LIMIT = 8;
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  // ─── pure helpers ──────────────────────────────────────────────────────

  function norm(s) {
    return String(s == null ? '' : s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }

  function themeText(t) {
    var also = (t.also || []).map(function (a) { return a.work + ' ' + a.author + ' ' + a.entry; }).join(' ');
    var cos = (t.companies || []).map(function (c) { return c.n; }).join(' ');
    return norm([t.title, t.imagined, t.fiction.entry, t.fiction.work, t.fiction.author, String(t.fiction.year),
      also, t.evidence.fact, t.evidence.publisher, t.gap, t.status_label, cos].join(' '));
  }

  /** Themes matching every filter: status, sector (any company in it) and all search words. */
  function filterThemes(themes, f) {
    f = f || {};
    var words = norm(f.q || '').trim().split(/\s+/).filter(Boolean);
    return themes.filter(function (t) {
      if (f.status && t.status !== f.status) return false;
      if (f.sector && !(t.sectors && t.sectors[f.sector])) return false;
      if (words.length) {
        var text = themeText(t);
        for (var i = 0; i < words.length; i++) if (text.indexOf(words[i]) === -1) return false;
      }
      return true;
    });
  }

  function byTitle(a, b) { return a.title.localeCompare(b.title, 'en'); }
  function byYear(a, b) { return a.fiction.year - b.fiction.year; }
  function byStatus(a, b) { return STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status); }

  /** A sorted copy. Unknown modes sort oldest first. Ties always fall back to the title. */
  function sortThemes(themes, mode) {
    var cmp = {
      oldest: function (a, b) { return byYear(a, b) || byTitle(a, b); },
      newest: function (a, b) { return byYear(b, a) || byTitle(a, b); },
      companies: function (a, b) { return (b.count - a.count) || byYear(a, b) || byTitle(a, b); },
      status: function (a, b) { return byStatus(a, b) || byYear(a, b) || byTitle(a, b); },
      az: byTitle
    }[mode] || function (a, b) { return byYear(a, b) || byTitle(a, b); };
    return themes.slice().sort(cmp);
  }

  function yearsAgo(year, nowYear) { return Math.max(0, nowYear - year); }

  /** '2025-04-07' -> '7 Apr 2025', '2025-04' -> 'Apr 2025', '2025' -> '2025'. */
  function formatDate(raw) {
    var p = String(raw || '').split('-').map(Number);
    if (p.length === 3 && p[1] >= 1 && p[1] <= 12) return p[2] + ' ' + MONTHS[p[1] - 1] + ' ' + p[0];
    if (p.length === 2 && p[1] >= 1 && p[1] <= 12) return MONTHS[p[1] - 1] + ' ' + p[0];
    return p[0] ? String(p[0]) : '';
  }

  function countBy(themes, key) {
    var out = {};
    themes.forEach(function (t) { out[t[key]] = (out[t[key]] || 0) + 1; });
    return out;
  }

  /** Sectors across all themes: [{sector, themes}] most themes first, then A to Z. */
  function sectorOptions(themes) {
    var n = {};
    themes.forEach(function (t) { Object.keys(t.sectors || {}).forEach(function (s) { n[s] = (n[s] || 0) + 1; }); });
    return Object.keys(n).map(function (s) { return { sector: s, themes: n[s] }; })
      .sort(function (a, b) { return (b.themes - a.themes) || a.sector.localeCompare(b.sector, 'en'); });
  }

  function parseState(search, knownStatuses) {
    var u = new URLSearchParams(search || '');
    var status = u.get('status') || '';
    var sort = u.get('sort') || 'oldest';
    return {
      status: (knownStatuses || STATUS_ORDER).indexOf(status) >= 0 ? status : '',
      sector: u.get('sector') || '',
      q: u.get('q') || '',
      sort: SORTS.indexOf(sort) >= 0 ? sort : 'oldest'
    };
  }

  function stateToSearch(s) {
    var u = new URLSearchParams();
    if (s.status) u.set('status', s.status);
    if (s.sector) u.set('sector', s.sector);
    if (s.q) u.set('q', s.q);
    if (s.sort && s.sort !== 'oldest') u.set('sort', s.sort);
    var str = u.toString();
    return str ? '?' + str : '';
  }

  // ─── the page ──────────────────────────────────────────────────────────

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch];
    });
  }

  /** Copy text: the Clipboard API where allowed, else a hidden textarea. done(true|false). */
  function copyText(text, done) {
    function fallback() {
      var ok = false;
      try {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        ok = document.execCommand('copy');
        document.body.removeChild(ta);
      } catch (err) { ok = false; }
      done(ok);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
    } else {
      fallback();
    }
  }

  function track(action) {
    try { if (typeof window.plausible === 'function') window.plausible('Who Is Building It', { props: { action: action } }); } catch (e) { /* analytics is optional */ }
  }

  function statusTag(t) {
    return '<span class="wb-status wb-status--' + esc(t.status) + '">' + esc(t.status_label) + '</span>';
  }

  function storyLine(fic) {
    return '<a class="wb-story" href="' + esc(fic.url) + '" target="_blank" rel="noopener" title="' +
      esc(fic.entry) + ' in Not Boring’s Sci-Fi Idea Bank"><span class="wb-year">' + esc(fic.year) +
      '</span> <cite>' + esc(fic.work) + '</cite> <span class="wb-author">' + esc(fic.author) + '</span></a>';
  }

  /** 'NASA, 24 Sep 2023', or for a page that prints no date: 'FANUC, undated page, read 25 Nov 2026'. */
  function sourceLabel(ev) {
    if (ev.date === 'undated') return ev.publisher + ', undated page, read ' + formatDate(ev.accessed);
    return ev.publisher + ', ' + formatDate(ev.date);
  }

  function evidenceLink(ev) {
    return '<a class="wb-source" href="' + esc(ev.url) + '" target="_blank" rel="noopener">' + esc(sourceLabel(ev)) + '</a>';
  }

  function companyChip(c) {
    var title = [c.sec, c.st, c.r].filter(Boolean).join(' · ');
    return '<li><a class="wb-co" href="company.html?slug=' + encodeURIComponent(c.s) + '" title="' + esc(title) + '">' + esc(c.n) + '</a></li>';
  }

  function builders(t, limit) {
    if (!t.count) return '<p class="wb-none">No company in the database is working on this yet.</p>';
    var shown = t.companies.slice(0, limit);
    var more = t.count - shown.length;
    return '<ul class="wb-chiplist" data-theme="' + esc(t.id) + '">' + shown.map(companyChip).join('') + '</ul>' +
      (more > 0 ? '<button type="button" class="wb-more" data-theme="' + esc(t.id) + '">Show all ' + t.count + '</button>' : '');
  }

  function card(t, nowYear) {
    var also = (t.also || []).length
      ? '<p class="wb-also">Also in ' + t.also.map(function (a) {
          return '<a href="' + esc(a.url) + '" target="_blank" rel="noopener"><cite>' + esc(a.work) + '</cite> (' + esc(a.author) + ', ' + esc(a.year) + ')</a>';
        }).join(' and ') + '</p>'
      : '';
    return '<article class="wb-card" id="' + esc(t.id) + '" data-status="' + esc(t.status) + '">' +
      '<div class="wb-card__top">' + storyLine(t.fiction) + statusTag(t) + '</div>' +
      '<h3 class="wb-card__title"><a href="#' + esc(t.id) + '">' + esc(t.title) + '</a></h3>' +
      '<p class="wb-line"><span class="wb-k">The idea</span>' + esc(t.imagined) + '</p>' +
      '<p class="wb-line"><span class="wb-k">Today</span>' + esc(t.evidence.fact) + ' ' + evidenceLink(t.evidence) + '</p>' +
      '<p class="wb-line wb-line--gap"><span class="wb-k">Still missing</span>' + esc(t.gap) + '</p>' +
      '<div class="wb-builders"><p class="wb-k wb-k--block">Who’s building it <span class="wb-n">' + t.count + '</span></p>' + builders(t, CHIP_LIMIT) + '</div>' +
      also +
      '<div class="wb-card__foot"><span>Imagined ' + yearsAgo(t.fiction.year, nowYear) + ' years ago</span>' +
      '<button type="button" class="wb-copy" data-theme="' + esc(t.id) + '">Copy link</button></div>' +
      '</article>';
  }

  function feature(t, nowYear) {
    return '<div class="wb-feature__year" aria-hidden="true">' + esc(t.fiction.year) + '</div>' +
      '<div class="wb-feature__body">' +
      '<p class="wb-feature__eyebrow">Imagined ' + yearsAgo(t.fiction.year, nowYear) + ' years ago ' + statusTag(t) + '</p>' +
      '<h2 class="wb-feature__title"><a href="#' + esc(t.id) + '">' + esc(t.title) + '</a></h2>' +
      '<p class="wb-feature__story">In ' + esc(t.fiction.year) + ', ' + esc(t.fiction.author) + ' wrote <a href="' + esc(t.fiction.url) +
      '" target="_blank" rel="noopener"><cite>' + esc(t.fiction.work) + '</cite></a>. ' + esc(t.imagined) + '</p>' +
      '<p class="wb-feature__today"><span class="wb-k">Today</span>' + esc(t.evidence.fact) + ' ' + evidenceLink(t.evidence) + '</p>' +
      '<p class="wb-feature__today"><span class="wb-k">Still missing</span>' + esc(t.gap) + '</p>' +
      '<div class="wb-builders"><p class="wb-k wb-k--block">Who’s building it <span class="wb-n">' + t.count + '</span></p>' + builders(t, CHIP_LIMIT) + '</div>' +
      '</div>';
  }

  function start(data) {
    var themes = data.themes || [];
    var byId = {};
    themes.forEach(function (t) { byId[t.id] = t; });
    var nowYear = new Date().getFullYear();
    var known = (data.statuses || []).map(function (s) { return s.key; });
    var state = parseState(window.location.search, known);
    var $ = function (id) { return document.getElementById(id); };

    // header lines and counters
    var meta = data.meta || {};
    $('wb-asof').textContent = 'Statuses checked ' + formatDate(meta.checked) + ' · Companies from the database of ' + formatDate(meta.data_updated);
    $('wb-c-ideas').textContent = meta.themes;
    $('wb-c-built').textContent = (meta.by_status && meta.by_status.built || 0) + ' of ' + meta.themes;
    $('wb-c-companies').textContent = Number(meta.companies).toLocaleString('en-US');
    $('wb-c-oldest').textContent = meta.oldest_year;
    $('wb-dates').textContent = 'Statuses last checked ' + formatDate(meta.checked) + '. Company lists rebuilt from the database of ' + formatDate(meta.data_updated) + '.';
    $('wb-defs').innerHTML = (data.statuses || []).map(function (s) {
      return '<dt><span class="wb-status wb-status--' + esc(s.key) + '">' + esc(s.label) + '</span></dt><dd>' + esc(s.definition) + '</dd>';
    }).join('');

    // featured pairing
    var featured = themes.filter(function (t) { return t.featured; })[0];
    if (featured) {
      $('wb-feature').innerHTML = feature(featured, nowYear);
      $('wb-feature').hidden = false;
    }

    // controls
    var counts = countBy(themes, 'status');
    var chips = [{ key: '', label: 'All', n: themes.length }].concat((data.statuses || []).map(function (s) {
      return { key: s.key, label: s.label, n: counts[s.key] || 0 };
    }));
    $('wb-status-chips').innerHTML = chips.map(function (c) {
      return '<button type="button" class="il-chip wb-chip" data-status="' + esc(c.key) + '" aria-pressed="false">' +
        esc(c.label) + ' <span class="wb-chip__n">' + c.n + '</span></button>';
    }).join('');
    var sectorSel = $('wb-sector');
    sectorOptions(themes).forEach(function (o) {
      var opt = document.createElement('option');
      opt.value = o.sector;
      opt.textContent = o.sector + ' (' + o.themes + ')';
      sectorSel.appendChild(opt);
    });
    if (state.sector && !sectorOptions(themes).some(function (o) { return o.sector === state.sector; })) state.sector = '';
    $('wb-q').value = state.q;
    sectorSel.value = state.sector;
    $('wb-sort').value = state.sort;

    var visible = [];
    function render(push) {
      visible = sortThemes(filterThemes(themes, state), state.sort);
      $('wb-list').innerHTML = visible.map(function (t) { return card(t, nowYear); }).join('');
      $('wb-empty').hidden = visible.length > 0;
      $('wb-count').textContent = visible.length === themes.length
        ? 'Showing all ' + themes.length + ' ideas'
        : 'Showing ' + visible.length + ' of ' + themes.length + ' ideas';
      Array.prototype.forEach.call(document.querySelectorAll('.wb-chip'), function (b) {
        b.setAttribute('aria-pressed', String(b.getAttribute('data-status') === state.status));
      });
      if (push) {
        var url = window.location.pathname + stateToSearch(state) + window.location.hash;
        window.history.replaceState(null, '', url);
      }
    }

    function focusTheme(id, smooth) {
      var el = document.getElementById(id);
      if (!el || !byId[id]) return false;
      el.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'start' });
      el.classList.remove('wb-card--flash');
      void el.offsetWidth;            // restart the highlight animation
      el.classList.add('wb-card--flash');
      return true;
    }

    function showTheme(id, smooth) {
      if (!byId[id]) return;
      if (!document.getElementById(id) || !document.querySelector('#wb-list #' + CSS.escape(id))) {
        state = { status: '', sector: '', q: '', sort: state.sort };
        $('wb-q').value = '';
        sectorSel.value = '';
        render(true);
      }
      if (window.location.hash !== '#' + id) window.history.replaceState(null, '', window.location.pathname + stateToSearch(state) + '#' + id);
      focusTheme(id, smooth);
    }

    $('wb-status-chips').addEventListener('click', function (e) {
      var b = e.target.closest('.wb-chip');
      if (!b) return;
      state.status = b.getAttribute('data-status') || '';
      render(true);
    });
    var qTimer = null;
    $('wb-q').addEventListener('input', function () {
      clearTimeout(qTimer);
      qTimer = setTimeout(function () { state.q = $('wb-q').value.trim(); render(true); }, 150);
    });
    sectorSel.addEventListener('change', function () { state.sector = sectorSel.value; render(true); });
    $('wb-sort').addEventListener('change', function () { state.sort = $('wb-sort').value; render(true); });
    $('wb-clear').addEventListener('click', function () {
      state = { status: '', sector: '', q: '', sort: 'oldest' };
      $('wb-q').value = '';
      sectorSel.value = '';
      $('wb-sort').value = 'oldest';
      render(true);
    });
    $('wb-random').addEventListener('click', function () {
      var pool = visible.length ? visible : themes;
      var pick = pool[Math.floor(Math.random() * pool.length)];
      if (pick) { showTheme(pick.id, true); track('random'); }
    });

    // card buttons (delegated, so they survive re-renders)
    document.addEventListener('click', function (e) {
      var more = e.target.closest('.wb-more');
      if (more) {
        var t = byId[more.getAttribute('data-theme')];
        var list = more.previousElementSibling;
        if (t && list) { list.innerHTML = t.companies.map(companyChip).join(''); more.remove(); }
        return;
      }
      var copy = e.target.closest('.wb-copy');
      if (copy) {
        var id = copy.getAttribute('data-theme');
        var link = window.location.origin + window.location.pathname + '#' + id;
        copyText(link, function (ok) {
          copy.textContent = ok ? 'Link copied' : 'Press Ctrl+C or Cmd+C to copy';
          setTimeout(function () { copy.textContent = 'Copy link'; }, ok ? 1800 : 4000);
        });
        if (window.location.hash !== '#' + id) window.history.replaceState(null, '', window.location.pathname + stateToSearch(state) + '#' + id);
        track('copy-link');
      }
    });

    window.addEventListener('hashchange', function () {
      var id = decodeURIComponent(window.location.hash.slice(1));
      if (byId[id]) showTheme(id, true);
    });

    render(false);
    var first = decodeURIComponent(window.location.hash.slice(1));
    if (byId[first]) setTimeout(function () { showTheme(first, false); }, 0);
  }

  return {
    STATUS_ORDER: STATUS_ORDER,
    norm: norm,
    filterThemes: filterThemes,
    sortThemes: sortThemes,
    yearsAgo: yearsAgo,
    formatDate: formatDate,
    sourceLabel: sourceLabel,
    sectorOptions: sectorOptions,
    parseState: parseState,
    stateToSearch: stateToSearch,
    start: start
  };
});
