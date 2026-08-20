/* The Wire — chronological change feed across the database.
   Reads const WIRE from data/wire_auto.js (built by scripts/build_wire.py).
   Member-facing by design: no relationship weighting, every line primary-source. */
(function () {
  'use strict';

  if (typeof WIRE === 'undefined' || !WIRE.events) {
    document.getElementById('wire-feed').innerHTML =
      '<p class="wire-empty">Wire data not loaded — data/wire_auto.js missing.</p>';
    return;
  }

  var esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };

  var BADGE = {
    form_d:      { color: '#4ade80' },
    funding:     { color: '#4ade80' },
    contract:    { color: '#fbbf24' },
    grant:       { color: '#fbbf24' },
    regulatory:  { color: '#60a5fa' },
    exec:        { color: '#a78bfa' },
    launch:      { color: '#22d3ee' },
    announcement:{ color: '#9ca3af' },
    patent:      { color: '#f472b6' }
  };

  var FILTERS = [
    { key: 'all',        label: 'All',        kinds: null },
    { key: 'capital',    label: '💰 Capital',  kinds: ['form_d', 'funding'] },
    { key: 'government', label: '🎖 Government', kinds: ['contract', 'grant'] },
    { key: 'regulatory', label: '📋 Regulatory', kinds: ['regulatory'] },
    { key: 'people',     label: '👥 People',   kinds: ['exec'] },
    { key: 'launches',   label: '🛰 Launches',  kinds: ['launch'] },
    { key: 'news',       label: '📰 Company News', kinds: ['announcement', 'patent'] }
  ];

  function dayLabel(iso) {
    try {
      var d = new Date(iso + 'T00:00:00Z');
      var today = new Date(); today.setUTCHours(0, 0, 0, 0);
      var diff = Math.round((today - d) / 86400000);
      if (diff === 0) return 'Today';
      if (diff === 1) return 'Yesterday';
      return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', timeZone: 'UTC' });
    } catch (e) { return iso; }
  }

  function renderStats() {
    var s = WIRE.stats;
    document.getElementById('wire-stats').innerHTML =
      '<div class="wire-stat"><b>' + s.events_this_week + '</b><span>events this week</span></div>' +
      '<div class="wire-stat"><b>' + esc(s.capital_this_week_fmt) + '</b><span>capital moved · 7d</span></div>' +
      '<div class="wire-stat"><b>' + s.companies_moved + '</b><span>companies moved · ' + WIRE.window_days + 'd</span></div>' +
      '<div class="wire-stat"><b>' + s.events + '</b><span>events · ' + WIRE.window_days + 'd</span></div>';
  }

  function eventRow(e) {
    var b = BADGE[e.kind] || BADGE.announcement;
    var name = '<a href="company.html?c=' + encodeURIComponent(e.company) + '">' + esc(e.company) + '</a>';
    var src = e.url
      ? '<a href="' + esc(e.url) + '" target="_blank" rel="noopener">' + esc(e.source || 'source') + ' ↗</a>'
      : esc(e.source || '');
    return '<div class="wire-event" data-kind="' + esc(e.kind) + '">' +
      '<span class="wire-badge" style="color:' + b.color + ';border-color:' + b.color + '55;background:' + b.color + '12">' + esc(e.label) + '</span>' +
      '<div class="wire-main">' +
        '<div class="wire-head">' + name + ' ' + esc(e.headline) + '</div>' +
        (e.detail ? '<div class="wire-detail">' + esc(e.detail) + '</div>' : '') +
        (e.context ? '<div class="wire-context">' + esc(e.context) + '</div>' : '') +
        '<div class="wire-meta">' + src + (e.sector ? ' · ' + esc(e.sector) : '') + '</div>' +
      '</div>' +
    '</div>';
  }

  function renderFeed(kinds) {
    var feed = document.getElementById('wire-feed');
    var events = WIRE.events.filter(function (e) {
      return !kinds || kinds.indexOf(e.kind) !== -1;
    });
    if (!events.length) {
      feed.innerHTML = '<p class="wire-empty">Nothing in this window — check back tomorrow.</p>';
      return;
    }
    var html = [], lastDay = null;
    events.forEach(function (e) {
      if (e.date !== lastDay) {
        if (lastDay !== null) html.push('</div>');
        html.push('<section class="wire-day"><div class="wire-day-head">' + esc(dayLabel(e.date)) + '</div>');
        lastDay = e.date;
      }
      html.push(eventRow(e));
    });
    html.push('</section>');
    feed.innerHTML = html.join('');
  }

  function renderFilters() {
    var box = document.getElementById('wire-filters');
    box.innerHTML = FILTERS.map(function (f, i) {
      return '<button class="wire-filter' + (i === 0 ? ' active' : '') + '" data-key="' + f.key + '">' + f.label + '</button>';
    }).join('');
    box.addEventListener('click', function (ev) {
      var btn = ev.target.closest('.wire-filter');
      if (!btn) return;
      box.querySelectorAll('.wire-filter').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      var f = FILTERS.filter(function (x) { return x.key === btn.dataset.key; })[0];
      renderFeed(f ? f.kinds : null);
    });
  }

  renderStats();
  renderFilters();
  renderFeed(null);
})();
