/* ─── The War Room — Daily Frontier Tech Digest ─── */
/* Reads data/daily_digest.json (generated every hour by generate_daily_digest.py) */

(function () {
  'use strict';

  var esc = (typeof escapeHtml === 'function') ? escapeHtml : function (s) { return String(s || ''); };

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  /* ── Section renderers ── */

  function renderDeals(deals) {
    if (!deals || deals.length === 0) return '<p class="brief-empty">No major deals in the last 7 days.</p>';
    return '<div class="brief-table-wrap"><table class="brief-table">' +
      '<thead><tr><th>Company</th><th>Amount</th><th>Round</th><th>Date</th></tr></thead><tbody>' +
      deals.map(function (d) {
        var linkedCompany = esc(d.company);
        if (d.url) {
          linkedCompany = '<a href="' + esc(d.url) + '" target="_blank" rel="noopener">' + esc(d.company) + '</a>';
        }
        return '<tr>' +
          '<td class="brief-company-name">' + linkedCompany + '</td>' +
          '<td class="brief-amount">' + esc(d.amount) + '</td>' +
          '<td><span class="brief-badge brief-badge-round">' + esc(d.round || '—') + '</span></td>' +
          '<td class="brief-date">' + esc(d.date) + '</td>' +
          '</tr>';
      }).join('') +
      '</tbody></table></div>';
  }

  function renderNews(news) {
    if (!news || news.length === 0) return '<p class="brief-empty">No fresh news signals.</p>';
    return '<div class="brief-list">' + news.map(function (n) {
      var headline = n.url
        ? '<a href="' + esc(n.url) + '" target="_blank" rel="noopener">' + esc(n.headline) + '</a>'
        : esc(n.headline);
      return '<div class="brief-list-item">' +
        '<div class="brief-list-meta">' +
          '<span class="brief-company-pill">' + esc(n.company || '—') + '</span>' +
          (n.source ? '<span class="brief-source">· ' + esc(n.source) + '</span>' : '') +
          (n.time ? '<span class="brief-time">· ' + esc(n.time) + '</span>' : '') +
        '</div>' +
        '<div class="brief-list-headline">' + headline + '</div>' +
      '</div>';
    }).join('') + '</div>';
  }

  function renderGovContracts(gov) {
    if (!gov || gov.length === 0) return '<p class="brief-empty">No major government contract awards in the last 14 days.</p>';
    return '<div class="brief-table-wrap"><table class="brief-table">' +
      '<thead><tr><th>Company</th><th>Amount</th><th>Agency</th><th>Description</th></tr></thead><tbody>' +
      gov.map(function (g) {
        return '<tr>' +
          '<td class="brief-company-name">' + esc(g.company) + '</td>' +
          '<td class="brief-amount">' + esc(g.amount) + '</td>' +
          '<td>' + esc(g.agency) + '</td>' +
          '<td class="brief-desc">' + esc((g.description || '').slice(0, 120)) + '</td>' +
        '</tr>';
      }).join('') +
      '</tbody></table></div>';
  }

  function renderMovers(movers) {
    if (!movers || movers.length === 0) return '<p class="brief-empty">Markets are quiet today.</p>';
    return '<div class="brief-mover-grid">' + movers.map(function (m) {
      var dir = m.changePercent >= 0 ? 'up' : 'down';
      var sign = m.changePercent >= 0 ? '+' : '';
      return '<div class="brief-mover-card mover-' + dir + '">' +
        '<div class="mover-ticker">' + esc(m.ticker) + '</div>' +
        '<div class="mover-company">' + esc(m.company) + '</div>' +
        '<div class="mover-price">$' + Number(m.price || 0).toFixed(2) + '</div>' +
        '<div class="mover-change">' + sign + Number(m.changePercent).toFixed(1) + '%</div>' +
      '</div>';
    }).join('') + '</div>';
  }

  function renderRegulatory(items) {
    if (!items || items.length === 0) return '<p class="brief-empty">No new regulatory action in the last 14 days.</p>';
    return '<div class="brief-list">' + items.map(function (i) {
      var title = i.url
        ? '<a href="' + esc(i.url) + '" target="_blank" rel="noopener">' + esc(i.title) + '</a>'
        : esc(i.title);
      return '<div class="brief-list-item">' +
        '<div class="brief-list-meta">' +
          '<span class="brief-badge">' + esc(i.kind) + '</span>' +
          (i.company ? '<span class="brief-company-pill">' + esc(i.company) + '</span>' : '') +
          (i.date ? '<span class="brief-time">· ' + esc(i.date) + '</span>' : '') +
        '</div>' +
        '<div class="brief-list-headline">' + title + '</div>' +
      '</div>';
    }).join('') + '</div>';
  }

  function renderPatents(items) {
    if (!items || items.length === 0) return '<p class="brief-empty">No new patent grants in the last 30 days.</p>';
    return '<div class="brief-list">' + items.map(function (i) {
      var title = i.url
        ? '<a href="' + esc(i.url) + '" target="_blank" rel="noopener">' + esc(i.title) + '</a>'
        : esc(i.title);
      return '<div class="brief-list-item">' +
        '<div class="brief-list-meta">' +
          '<span class="brief-company-pill">' + esc(i.company) + '</span>' +
          (i.date ? '<span class="brief-time">· ' + esc(i.date) + '</span>' : '') +
        '</div>' +
        '<div class="brief-list-headline">' + title + '</div>' +
      '</div>';
    }).join('') + '</div>';
  }

  function section(title, badge, bodyHtml) {
    return '<section class="brief-section">' +
      '<div class="brief-section-header">' +
        '<h2 class="brief-section-title">' + esc(title) + '</h2>' +
        (badge ? '<span class="brief-section-badge">' + esc(badge) + '</span>' : '') +
      '</div>' +
      bodyHtml +
    '</section>';
  }

  /* ── Main renderer ── */

  function renderDigest(digest) {
    if (!digest || !digest.sections) {
      document.getElementById('brief-error').style.display = 'block';
      document.getElementById('brief-skeleton').style.display = 'none';
      return;
    }

    // Hero stats
    setText('brief-date', digest.dateDisplay ? digest.dateDisplay.split(',')[0] : digest.date);
    setText('brief-deal-count', (digest.stats || {}).dealCount || 0);
    setText('brief-contract-count', (digest.stats || {}).contractCount || 0);
    setText('brief-top-mover', (digest.stats || {}).topMover || '—');

    var s = digest.sections;

    var html = '';
    html += section('💰 Biggest Deals', 'Last 7 days', renderDeals(s.biggestDeals));
    html += section('📰 Top News', 'Live', renderNews(s.topNews));
    html += section('🏛️ Government Activity', 'SAM.gov', renderGovContracts(s.govActivity));
    html += section('📈 Market Movers', 'Today', renderMovers(s.marketMovers));
    html += section('⚖️ Regulatory Highlights', 'FDA · Fed Reg', renderRegulatory(s.regulatory));
    html += section('🔬 Recent Patent Grants', 'USPTO', renderPatents(s.patents));

    html += '<div class="brief-footer-note">' +
      '<p style="color:rgba(255,255,255,0.45); font-size:12px; text-align:center; margin-top:32px;">Generated ' + esc(digest.generatedAt || '') + ' · Auto-refreshed hourly from ROS data pipeline</p>' +
    '</div>';

    var content = document.getElementById('brief-content');
    content.innerHTML = html;
    content.style.display = 'block';
    document.getElementById('brief-skeleton').style.display = 'none';
  }

  /* ── Bootstrap ── */

  function loadBrief() {
    document.getElementById('brief-skeleton').style.display = 'block';
    document.getElementById('brief-content').style.display = 'none';
    document.getElementById('brief-error').style.display = 'none';

    fetch('data/daily_digest.json', { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status)); })
      .then(renderDigest)
      .catch(function (e) {
        console.error('[WarRoom] Failed to load digest:', e);
        document.getElementById('brief-error').style.display = 'block';
        document.getElementById('brief-skeleton').style.display = 'none';
      });
  }

  window.loadBrief = loadBrief;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadBrief);
  } else {
    loadBrief();
  }
})();
