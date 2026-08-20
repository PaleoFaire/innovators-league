/**
 * Exit Watch — The Innovators League
 *
 * Renders the pre-company dealflow queue from EXIT_WATCH (data/exit_watch_auto.js).
 *
 * Every row is a lead, not a claim. The UI is deliberately built so that the
 * evidence and the caveat are as visible as the headline — a name match is a
 * hypothesis, and the page says so on every row that rests on one.
 */

(function () {
  'use strict';

  var rows = (typeof EXIT_WATCH !== 'undefined' && Array.isArray(EXIT_WATCH)) ? EXIT_WATCH : [];
  var meta = (typeof EXIT_WATCH_META !== 'undefined') ? EXIT_WATCH_META : {};

  var TIERS = [
    { id: 'all',           label: 'All' },
    { id: 'Strong lead',   label: 'Strong leads' },
    { id: 'Lead',          label: 'Leads' },
    { id: 'New formation', label: 'New formations' }
  ];

  var state = { tier: 'all', q: '', sort: 'score' };

  // ── helpers ────────────────────────────────────────────────────────────
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function money(n) {
    if (!n && n !== 0) return '—';
    if (n >= 1e9) return '$' + (n / 1e9).toFixed(1) + 'B';
    if (n >= 1e6) return '$' + (n / 1e6).toFixed(n >= 1e7 ? 0 : 1) + 'M';
    if (n >= 1e3) return '$' + Math.round(n / 1e3) + 'K';
    return '$' + n;
  }

  function daysAgo(iso) {
    if (!iso) return '';
    var d = new Date(iso);
    if (isNaN(d)) return '';
    var n = Math.floor((Date.now() - d.getTime()) / 86400000);
    if (n <= 0) return 'today';
    if (n === 1) return 'yesterday';
    if (n < 31) return n + ' days ago';
    return Math.floor(n / 30) + (Math.floor(n / 30) === 1 ? ' month ago' : ' months ago');
  }

  function tierClass(t) {
    if (t === 'Strong lead') return 'ew-tier-strong';
    if (t === 'Lead') return 'ew-tier-lead';
    return 'ew-tier-new';
  }

  // ── render ─────────────────────────────────────────────────────────────
  function renderStats() {
    var el = document.getElementById('ew-stats');
    if (!el) return;
    var strong = rows.filter(function (r) { return r.confidence === 'Strong lead'; }).length;
    var lead   = rows.filter(function (r) { return r.confidence === 'Lead'; }).length;
    var capital = rows.reduce(function (a, r) { return a + (r.amountSold || 0); }, 0);

    var items = [
      { v: rows.length, l: 'entities in the queue' },
      { v: strong + lead, l: 'with a name matched to a founder we track' },
      { v: money(capital), l: 'capital disclosed across the queue' },
      { v: (meta.filings_scanned || 0).toLocaleString(), l: 'Form D filings swept' }
    ];
    el.innerHTML = items.map(function (i) {
      return '<div class="ew-stat"><div class="ew-stat-v">' + esc(i.v) +
             '</div><div class="ew-stat-l">' + esc(i.l) + '</div></div>';
    }).join('');
  }

  function renderFilters() {
    var el = document.getElementById('ew-tier-filters');
    if (!el) return;
    el.innerHTML = TIERS.map(function (t) {
      var n = t.id === 'all' ? rows.length
            : rows.filter(function (r) { return r.confidence === t.id; }).length;
      if (n === 0 && t.id !== 'all') return '';
      return '<button class="ew-chip' + (state.tier === t.id ? ' active' : '') +
             '" data-tier="' + esc(t.id) + '">' + esc(t.label) +
             '<span class="ew-chip-n">' + n + '</span></button>';
    }).join('');
    Array.prototype.forEach.call(el.querySelectorAll('.ew-chip'), function (b) {
      b.addEventListener('click', function () {
        state.tier = b.getAttribute('data-tier');
        renderFilters(); renderRows();
      });
    });
  }

  function matchesQuery(r, q) {
    if (!q) return true;
    var hay = [r.entity, r.industry, r.state,
               (r.people || []).map(function (p) { return p.name; }).join(' '),
               (r.matches || []).map(function (m) {
                 return m.person + ' ' + (m.known_for || []).join(' ') + ' ' +
                        (m.employers || []).join(' ');
               }).join(' ')].join(' ').toLowerCase();
    return hay.indexOf(q) !== -1;
  }

  function visible() {
    var q = state.q.trim().toLowerCase();
    var out = rows.filter(function (r) {
      return (state.tier === 'all' || r.confidence === state.tier) && matchesQuery(r, q);
    });
    if (state.sort === 'recent') {
      out.sort(function (a, b) { return (b.firstSale || '').localeCompare(a.firstSale || ''); });
    } else if (state.sort === 'amount') {
      out.sort(function (a, b) { return (b.amountSold || 0) - (a.amountSold || 0); });
    } else {
      out.sort(function (a, b) { return (b.score || 0) - (a.score || 0); });
    }
    return out;
  }

  function rowHtml(r) {
    var people = (r.people || []).map(function (p) {
      var matched = (r.matches || []).some(function (m) { return m.person === p.name; });
      return '<span class="ew-person' + (matched ? ' matched' : '') + '">' +
             esc(p.name) +
             (p.roles && p.roles.length ? '<em>' + esc(p.roles.join(', ')) + '</em>' : '') +
             '</span>';
    }).join('');

    var evidence = '';
    if (r.matches && r.matches.length) {
      evidence = '<div class="ew-evidence">' + r.matches.map(function (m) {
        var known = (m.known_for || []).join(', ');
        var emp = (m.employers || []).length
          ? ' <span class="ew-emp">' + esc(m.employers.join(' · ')) + '</span>' : '';
        return '<div class="ew-ev-row' + (m.name_ambiguous ? ' ambiguous' : '') + '">' +
               '<strong>' + esc(m.person) + '</strong> matches our record for ' +
               '<strong>' + esc(known) + '</strong>' + emp +
               (m.name_ambiguous
                 ? '<div class="ew-warn">That name is common or ambiguous in our data — ' +
                   'this may be a different person. Verify before acting.</div>'
                 : '') +
               '</div>';
      }).join('') + '</div>';
    }

    var reasons = (r.reasons || []).length
      ? '<ul class="ew-reasons">' + r.reasons.map(function (x) {
          return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>'
      : '';

    return '' +
      '<article class="ew-row ' + tierClass(r.confidence) + '">' +
        '<div class="ew-row-head">' +
          '<div class="ew-row-title">' +
            '<h3>' + esc(r.entity) + '</h3>' +
            '<div class="ew-meta">' +
              '<span class="ew-badge ' + tierClass(r.confidence) + '">' + esc(r.confidence) + '</span>' +
              (r.industry ? '<span>' + esc(r.industry) + '</span>' : '') +
              (r.state ? '<span>' + esc(r.state) + '</span>' : '') +
              (r.yearInc ? '<span>inc. ' + esc(r.yearInc) + '</span>' : '') +
              (r.firstSale ? '<span>' + esc(daysAgo(r.firstSale)) + '</span>' : '') +
            '</div>' +
          '</div>' +
          '<div class="ew-row-num">' +
            '<div class="ew-amount">' + esc(money(r.amountSold)) + '</div>' +
            '<div class="ew-score" title="Lead strength, 0-100">' + esc(r.score) + '</div>' +
          '</div>' +
        '</div>' +
        (people ? '<div class="ew-people">' + people + '</div>' : '') +
        evidence + reasons +
        '<div class="ew-links">' +
          '<a href="' + esc(r.url) + '" target="_blank" rel="noopener">Read the filing →</a>' +
          '<a href="' + esc(r.filingUrl) + '" target="_blank" rel="noopener">All EDGAR filings →</a>' +
        '</div>' +
      '</article>';
  }

  function renderRows() {
    var host = document.getElementById('ew-rows');
    var empty = document.getElementById('ew-empty');
    var line = document.getElementById('ew-result-line');
    if (!host) return;

    var list = visible();
    host.innerHTML = list.map(rowHtml).join('');
    if (empty) empty.hidden = list.length !== 0;
    if (line) {
      line.innerHTML = 'Showing <b>' + list.length + '</b> of ' + rows.length +
        ' entities' + (meta.window_days ? ' · last ' + meta.window_days + ' days of filings' : '');
    }
  }

  function bind() {
    var s = document.getElementById('ew-search');
    if (s) {
      s.addEventListener('input', function () { state.q = s.value; renderRows(); });
    }
    var sel = document.getElementById('ew-sort');
    if (sel) {
      sel.addEventListener('change', function () { state.sort = sel.value; renderRows(); });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    renderStats();
    renderFilters();
    renderRows();
    bind();
  });
})();
