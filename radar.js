/* Pre-Announcement Radar — SEC Form D filings matched to tracked companies.
   Reads const RADAR from data/wire_auto.js (built by scripts/build_wire.py).
   Trust rule inherited from the pipeline: only CIK- or founder-confirmed
   matches reach this payload; name-only guesses stay in the review queue. */
(function () {
  'use strict';

  var list = document.getElementById('radar-list');
  if (typeof RADAR === 'undefined' || !RADAR.filings) {
    list.innerHTML = '<p class="radar-empty">Radar data not loaded — data/wire_auto.js missing.</p>';
    return;
  }

  var esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };

  function fmtDate(iso) {
    try {
      return new Date(iso + 'T00:00:00Z').toLocaleDateString('en-US',
        { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
    } catch (e) { return iso; }
  }

  function renderStats() {
    var s = RADAR.stats;
    document.getElementById('radar-stats').innerHTML =
      '<div class="radar-stat"><b>' + s.filings_30d + '</b><span>filings · 30d</span></div>' +
      '<div class="radar-stat"><b>' + esc(s.offered_30d_fmt) + '</b><span>offered · 30d</span></div>' +
      '<div class="radar-stat"><b>' + s.fully_subscribed_30d + '</b><span>fully subscribed · 30d</span></div>' +
      '<div class="radar-stat"><b>' + s.total_tracked + '</b><span>tracked filings</span></div>';
  }

  function card(r) {
    var amounts = '';
    if (r.offering || r.sold) {
      var bits = [];
      if (r.offering_fmt) bits.push('<b>' + esc(r.offering_fmt) + '</b> offered');
      if (r.sold_fmt) bits.push('<b>' + esc(r.sold_fmt) + '</b> sold' +
        (r.pct_subscribed != null ? ' <span style="color:var(--text-muted)">(' + r.pct_subscribed + '%)</span>' : ''));
      amounts = '<div class="radar-amounts"><div class="radar-amount-row">' + bits.join('<span style="color:var(--text-muted)">·</span>') + '</div>' +
        (r.pct_subscribed != null
          ? '<div class="radar-bar"><div class="radar-bar-fill" style="width:' + Math.min(100, r.pct_subscribed) + '%"></div></div>'
          : '') +
        '</div>';
    } else {
      amounts = '<div class="radar-amounts"><div class="radar-amount-row">Amount not disclosed in the filing</div></div>';
    }

    var chips = '';
    if (r.securities_type) chips += '<span class="radar-chip">' + esc(r.securities_type.toUpperCase()) + '</span>';
    if (r.is_safe) chips += '<span class="radar-chip">SAFE</span>';
    if (r.exemption) chips += '<span class="radar-chip">REG D 5' + esc(String(r.exemption).replace(/^0/, '')) + '</span>';

    return '<article class="radar-card' + (r.fully_subscribed ? ' full' : '') + '">' +
      '<div class="radar-co">' +
        '<a href="company.html?c=' + encodeURIComponent(r.company) + '">' + esc(r.company) + '</a>' +
        (r.sector ? '<span class="radar-sector">' + esc(r.sector) + '</span>' : '') +
      '</div>' +
      (r.fully_subscribed
        ? '<span class="radar-flag">FULLY SUBSCRIBED — ROUND CLOSED</span>'
        : '<span class="radar-date">Filed ' + esc(fmtDate(r.filed_date)) + '</span>') +
      amounts +
      (r.vs_last_round ? '<div class="radar-vs">' + esc(r.vs_last_round) + '</div>' : '') +
      '<div class="radar-links">' +
        (r.fully_subscribed ? 'Filed ' + esc(fmtDate(r.filed_date)) + ' · ' : '') +
        (r.filing_url ? '<a href="' + esc(r.filing_url) + '" target="_blank" rel="noopener">View the filing on SEC EDGAR ↗</a> · ' : '') +
        '<a href="company.html?c=' + encodeURIComponent(r.company) + '">Company profile</a>' +
        chips +
      '</div>' +
    '</article>';
  }

  renderStats();
  list.innerHTML = RADAR.filings.length
    ? RADAR.filings.map(card).join('')
    : '<p class="radar-empty">No matched filings in the window — the sweep runs daily.</p>';
})();
