/* ═══════════════════════════════════════════════════════════════════════════
   ROS INNOVATORS LEAGUE — homepage v2 (15 Oct 2026)

   The homepage is six sections: hero (search first), Today strip, three doors,
   the Innovators League 30, the tools grid, podcast + newsletter. app.js still
   runs here for the global search, the hero counter, the IL30 showcase, the
   signals ticker (#news-ticker), this week's movers (#weekly-movers) and the
   podcast list. This file only fills what is new: the Today strip's "what
   changed" rows and its "updated X hours ago" line, plus the live stats that
   come from data files app.js does not read.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function slug(name) {
    return (typeof companyToSlug === 'function') ? companyToSlug(name)
      : String(name || '').toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
  }
  function ago(iso) {
    var d = new Date(iso);
    if (isNaN(d)) return '';
    var mins = Math.max(0, Math.round((Date.now() - d.getTime()) / 60000));
    if (mins < 60) return mins + ' min ago';
    var hours = Math.round(mins / 60);
    if (hours < 48) return hours + (hours === 1 ? ' hour ago' : ' hours ago');
    var days = Math.round(hours / 24);
    return days + ' days ago';
  }
  function shortDate(iso) {
    var d = new Date(String(iso || '').slice(0, 10) + 'T00:00:00Z');
    if (isNaN(d)) return '';
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
  }

  /* ───────── Today strip ───────── */
  function renderToday() {
    var wireEl = document.getElementById('today-wire');
    var updatedEl = document.getElementById('today-updated');
    var footEl = document.getElementById('today-foot');
    var hasWire = (typeof WIRE !== 'undefined' && WIRE && WIRE.top && WIRE.top.length);

    if (wireEl && hasWire) {
      var COLORS = { form_d: '#4ade80', funding: '#4ade80', contract: '#fbbf24', grant: '#fbbf24',
                     regulatory: '#60a5fa', exec: '#a78bfa', launch: '#22d3ee' };
      wireEl.innerHTML = WIRE.top.slice(0, 5).map(function (e) {
        var c = COLORS[e.kind] || '#9ca3af';
        var href = e.company ? 'company.html?slug=' + slug(e.company) : 'wire.html';
        return '<a class="today-row" href="' + href + '">' +
          '<span class="today-tag" style="color:' + c + ';border-color:' + c + '55;background:' + c + '12;">' + esc(e.label) + '</span>' +
          '<span class="today-text"><b>' + esc(e.company) + '</b> <span>' + esc(e.headline) +
            (e.detail && e.detail !== 'Funding Round' ? ' · ' + esc(e.detail) : '') + '</span></span>' +
          '<span class="today-date">' + esc(shortDate(e.date)) + '</span>' +
        '</a>';
      }).join('');
    } else if (wireEl) {
      wireEl.innerHTML = '<p class="today-empty">The Wire has not been generated yet. <a href="wire.html">Open The Wire &rarr;</a></p>';
    }

    if (updatedEl && hasWire && WIRE.generated_at) {
      var when = ago(WIRE.generated_at);
      updatedEl.textContent = when ? 'Updated ' + when : '';
      updatedEl.setAttribute('title', 'Wire rebuilt ' + WIRE.generated_at);
    }

    if (footEl) {
      var bits = [];
      if (hasWire && WIRE.stats) {
        if (WIRE.stats.events_this_week != null) bits.push('<b>' + WIRE.stats.events_this_week + '</b> changes this week');
        if (WIRE.stats.companies_moved != null) bits.push('<b>' + WIRE.stats.companies_moved + '</b> companies moved in ' + (WIRE.window_days || 30) + ' days');
      }
      if (typeof CHANGELOG_WEEKLY !== 'undefined' && CHANGELOG_WEEKLY) {
        var added = (CHANGELOG_WEEKLY.added || []).length;
        bits.push('<a href="changes.html"><b>' + added + '</b> ' + (added === 1 ? 'company' : 'companies') + ' added this week</a>');
      }
      if (typeof LAST_UPDATED !== 'undefined') bits.push('database as of <b>' + esc(LAST_UPDATED) + '</b>');
      footEl.innerHTML = bits.map(function (b) { return '<span>' + b + '</span>'; }).join('');
    }
  }

  /* ───────── hero stat: changes this week (from the wire) ───────── */
  function renderHeroStats() {
    var el = document.getElementById('stat-events-week');
    if (el && typeof WIRE !== 'undefined' && WIRE && WIRE.stats && WIRE.stats.events_this_week != null) {
      el.textContent = Number(WIRE.stats.events_this_week).toLocaleString('en-US');
    }
  }

  /* ───────── keyboard: "/" focuses the hero search ───────── */
  function initSlashShortcut() {
    var field = document.getElementById('global-search');
    if (!field) return;
    document.addEventListener('keydown', function (e) {
      if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return;
      var t = e.target;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
      e.preventDefault();
      field.focus();
    });
  }

  function init() {
    try { renderToday(); } catch (e) { console.error('[TIL home] today strip failed', e); }
    try { renderHeroStats(); } catch (e) { /* decoration */ }
    try { initSlashShortcut(); } catch (e) { /* decoration */ }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
