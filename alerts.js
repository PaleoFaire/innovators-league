// ─── DEAL FLOW ALERTS PAGE ───────────────────────────────────────────────────
// Aggregates real-time deal signals (funding, contracts, filings, news, IPO)
// from the project's existing data sources and renders them as a chronological
// feed with type/sector/time-range filters.

// ─── LOCAL HELPERS ───────────────────────────────────────────────────────────
// This project does not have a shared utils.js, so we inline minimal versions
// of the helpers alerts.js needs. Kept here (not global) to avoid colliding
// with per-page definitions in other files.

function alertsEscapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function alertsSanitizeUrl(url) {
  if (!url) return '#';
  var trimmed = String(url).trim();
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  if (/^mailto:/i.test(trimmed)) return trimmed;
  return '#';
}

function alertsFormatDateRelative(dateStr) {
  if (!dateStr) return '';
  var date = new Date(dateStr);
  if (isNaN(date.getTime())) return String(dateStr);
  var now = new Date();
  var diffMs = now - date;
  var diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  var diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffHours < 1) return 'Just now';
  if (diffHours < 24) return diffHours + 'h ago';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return diffDays + 'd ago';
  if (diffDays < 30) return Math.floor(diffDays / 7) + 'w ago';
  if (diffDays < 365) return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

function alertsInitMobileMenu() {
  var btn = document.querySelector('.mobile-menu-btn');
  var links = document.querySelector('.nav-links');
  if (btn && links) {
    btn.addEventListener('click', function() {
      links.classList.toggle('open');
      btn.classList.toggle('open');
    });
  }
}

// ─── COMPANY LOOKUP (for sector tagging and deep-link slugs) ─────────────────
function alertsFindCompany(name) {
  if (!name || typeof COMPANIES === 'undefined') return null;
  var needle = String(name).toLowerCase().trim();
  if (!needle) return null;
  // Try exact match first, then suffix-stripped, then substring
  var exact = COMPANIES.find(function(c) {
    return (c.name || '').toLowerCase() === needle;
  });
  if (exact) return exact;
  var bare = needle.replace(/\s*(inc\.?|industries|corp\.?|corporation|llc|ltd\.?|co\.?|technologies)\s*$/i, '').trim();
  return COMPANIES.find(function(c) {
    var cName = (c.name || '').toLowerCase();
    var cBare = cName.replace(/\s*(inc\.?|industries|corp\.?|corporation|llc|ltd\.?|co\.?|technologies)\s*$/i, '').trim();
    return cBare === bare || cName.indexOf(needle) !== -1 || needle.indexOf(cBare) !== -1;
  }) || null;
}

function alertsCompanyHref(name) {
  if (!name) return '#';
  // Prefer a slug if COMPANIES has the match, otherwise use the ?c= fallback
  var match = alertsFindCompany(name);
  if (match && match.name) {
    var slug = match.name.toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
    return 'company.html?c=' + encodeURIComponent(slug);
  }
  return 'company.html?c=' + encodeURIComponent(name);
}

// ─── SIGNAL AGGREGATION ──────────────────────────────────────────────────────
function aggregateDealSignals() {
  var signals = [];

  // 1. Funding signals from DEAL_FLOW_SIGNALS
  // Real shape: { company, probability, expectedRound, expectedAmount, expectedTiming, signals: [...], potentialLeads }
  if (typeof DEAL_FLOW_SIGNALS !== 'undefined' && Array.isArray(DEAL_FLOW_SIGNALS)) {
    DEAL_FLOW_SIGNALS.forEach(function(d) {
      if (!d || !d.company) return;
      var latestSignal = (d.signals && d.signals.length) ? d.signals[d.signals.length - 1] : null;
      var titleBase = d.expectedRound && d.expectedRound !== 'Unknown'
        ? d.expectedRound + ' Round Forecast'
        : 'Funding Signal';
      var descr = latestSignal && latestSignal.description
        ? latestSignal.description
        : (d.signal || d.headline || titleBase);
      var probStr = typeof d.probability === 'number' ? ' — ' + d.probability + '% probability' : '';
      signals.push({
        type: 'funding',
        company: d.company,
        title: descr + probStr,
        date: d.date || d.lastUpdated || null,
        source: d.source || 'ROS Intelligence',
        url: d.url,
        icon: '💰',
        color: '#22c55e',
        priority: d.priority || (d.probability >= 90 ? 'high' : 'medium'),
        sector: (alertsFindCompany(d.company) || {}).sector || null
      });
    });
  }

  // 2. SEC filings
  var secFilings = null;
  if (typeof SEC_FILINGS_LIVE !== 'undefined') secFilings = SEC_FILINGS_LIVE;
  else if (typeof SEC_FILINGS_AUTO !== 'undefined') secFilings = SEC_FILINGS_AUTO;
  if (Array.isArray(secFilings)) {
    secFilings.slice(0, 60).forEach(function(f) {
      if (!f) return;
      var companyName = f.company || f.companyName || f.ticker || 'Unknown';
      var form = f.form || f.type || 'Filing';
      signals.push({
        type: 'sec',
        company: companyName,
        title: 'SEC Filing: ' + form + (f.description ? ' (' + f.description + ')' : ''),
        date: f.date || f.filingDate,
        source: 'SEC EDGAR',
        url: f.url,
        icon: '📄',
        color: '#f59e0b',
        sector: (alertsFindCompany(companyName) || {}).sector || null
      });
    });
  }

  // 3. Government contracts
  var govContracts = null;
  if (typeof GOV_CONTRACTS_LIVE !== 'undefined') govContracts = GOV_CONTRACTS_LIVE;
  else if (typeof GOV_CONTRACTS_AUTO !== 'undefined') govContracts = GOV_CONTRACTS_AUTO;
  if (Array.isArray(govContracts)) {
    govContracts.slice(0, 60).forEach(function(c) {
      if (!c || !c.company) return;
      var agency = c.agency || (c.agencies && c.agencies[0]) || 'Government';
      var value = c.value || c.totalGovValue || 'Undisclosed';
      var count = c.contractCount ? ' (' + c.contractCount + ' contracts)' : '';
      signals.push({
        type: 'contract',
        company: c.company,
        title: agency + ' Contract: ' + value + count,
        date: c.date || c.lastUpdated,
        source: c.source || 'USAspending / SAM.gov',
        url: c.url,
        icon: '🏛️',
        color: '#3b82f6',
        sector: (alertsFindCompany(c.company) || {}).sector || null
      });
    });
  }

  // 4. News signals (handles both curated items and auto-detected)
  if (typeof NEWS_FEED !== 'undefined' && Array.isArray(NEWS_FEED)) {
    NEWS_FEED.slice(0, 80).forEach(function(n) {
      if (!n) return;
      var companyName = n.company
        || (Array.isArray(n.companies) && n.companies[0])
        || 'Multiple';
      var cat = (n.category || '').toLowerCase();
      // Classify news into our filter buckets when possible
      var bucket = 'news';
      if (cat === 'funding') bucket = 'funding';
      else if (cat === 'contract') bucket = 'contract';
      else if (cat === 'ipo') bucket = 'ipo';
      else if (cat === 'mna' || cat === 'm&a' || cat === 'acquisition') bucket = 'mna';
      signals.push({
        type: bucket,
        company: companyName,
        title: n.headline || n.title || 'News update',
        date: n.date,
        source: n.source,
        url: n.url,
        icon: bucket === 'funding' ? '💰' : (bucket === 'contract' ? '🏛️' : (bucket === 'ipo' ? '🚀' : (bucket === 'mna' ? '🤝' : '📰'))),
        color: bucket === 'funding' ? '#22c55e' : (bucket === 'contract' ? '#3b82f6' : (bucket === 'ipo' ? '#ec4899' : (bucket === 'mna' ? '#eab308' : '#a855f7'))),
        priority: n.impact || null,
        sector: n.sector || (alertsFindCompany(companyName) || {}).sector || null
      });
    });
  }

  // 5. IPO pipeline signals
  if (typeof IPO_PIPELINE !== 'undefined' && Array.isArray(IPO_PIPELINE)) {
    IPO_PIPELINE.forEach(function(ipo) {
      if (!ipo || !ipo.company) return;
      var detail = ipo.status || ipo.stage || 'Pipeline update';
      var valuation = ipo.estimatedValuation ? ' @ ' + ipo.estimatedValuation : '';
      signals.push({
        type: 'ipo',
        company: ipo.company,
        title: 'IPO Pipeline: ' + detail + valuation,
        date: ipo.lastUpdate || ipo.date || ipo.estimatedDate || null,
        source: 'SEC / Media',
        url: ipo.url,
        icon: '🚀',
        color: '#ec4899',
        priority: ipo.likelihood || null,
        sector: ipo.sector || (alertsFindCompany(ipo.company) || {}).sector || null
      });
    });
  }

  // Sort by date, newest first; undated items sink
  signals.sort(function(a, b) {
    var da = a.date ? new Date(a.date).getTime() : 0;
    var db = b.date ? new Date(b.date).getTime() : 0;
    return db - da;
  });

  return signals;
}

// ─── RENDERING ───────────────────────────────────────────────────────────────
var ALERTS_STATE = {
  all: [],
  filters: { type: 'all', sector: 'all', time: 'all' }
};

var ALERTS_FEED_INITIAL = 25;
var ALERTS_FEED_STEP = 25;
var alertsFeedShownCount = ALERTS_FEED_INITIAL;
var lastRenderedAlertSignals = null;

function renderAlertsFeed(signals) {
  var container = document.getElementById('alerts-feed');
  if (!container) return;

  if (!signals || !signals.length) {
    container.innerHTML = '<div class="alerts-empty">'
      + '<div class="alerts-empty-icon">📡</div>'
      + '<h3>No alerts to display</h3>'
      + '<p>Data sources may be loading, or your current filters don\'t match any signals yet. Try widening the time range or resetting the type filter.</p>'
      + '</div>';
    return;
  }

  // Cap raw signals at 150 (original hard cap)
  var capped = signals.slice(0, 150);

  if (lastRenderedAlertSignals !== signals) {
    alertsFeedShownCount = ALERTS_FEED_INITIAL;
    lastRenderedAlertSignals = signals;
  }

  function alertItemHTML(s) {
    var dateStr = s.date ? alertsFormatDateRelative(s.date) : 'Recent';
    var companyLink = s.company
      ? '<a href="' + alertsSanitizeUrl(alertsCompanyHref(s.company)) + '" class="alert-company">' + alertsEscapeHtml(s.company) + '</a>'
      : '';
    var sourceLink = s.url
      ? '<a href="' + alertsSanitizeUrl(s.url) + '" target="_blank" rel="noopener" class="alert-source-link">' + alertsEscapeHtml(s.source || 'Source') + ' &rarr;</a>'
      : '<span class="alert-source">' + alertsEscapeHtml(s.source || '') + '</span>';
    var sectorTag = s.sector
      ? '<span class="alert-sector">' + alertsEscapeHtml(s.sector) + '</span>'
      : '';
    var priorityTag = '';
    if (s.priority === 'high' || s.priority === 'critical') {
      priorityTag = '<span class="alert-priority high">High Impact</span>';
    }

    var html = '<div class="alert-item" data-type="' + alertsEscapeHtml(s.type) + '" data-sector="' + alertsEscapeHtml(s.sector || '') + '" data-date="' + alertsEscapeHtml(s.date || '') + '">';
    html += '<div class="alert-icon" style="background:' + s.color + '15;color:' + s.color + ';border:1px solid ' + s.color + '30;">' + s.icon + '</div>';
    html += '<div class="alert-body">';
    html += '<div class="alert-meta">' + companyLink + '<span class="alert-date">' + alertsEscapeHtml(dateStr) + '</span></div>';
    html += '<div class="alert-title">' + alertsEscapeHtml(s.title) + '</div>';
    html += '<div class="alert-footer">' + sourceLink + sectorTag + priorityTag + '</div>';
    html += '</div>';
    html += '</div>';
    return html;
  }

  var total = capped.length;
  var visible = capped.slice(0, alertsFeedShownCount);

  var html = '<div class="alerts-list">';
  visible.forEach(function(s) { html += alertItemHTML(s); });
  html += '</div>';

  if (total > ALERTS_FEED_INITIAL) {
    var remaining = total - alertsFeedShownCount;
    if (remaining > 0) {
      var nextBatch = Math.min(ALERTS_FEED_STEP, remaining);
      html += '<div class="paginated-list-actions"><button class="show-more-btn" type="button" data-alerts-feed-action="show-more">Show ' + nextBatch + ' more alerts <span class="show-more-count">(' + remaining + ' remaining)</span></button></div>';
    } else {
      html += '<div class="paginated-list-actions"><button class="show-more-btn show-less-btn" type="button" data-alerts-feed-action="show-less">Show less</button></div>';
    }
  }

  container.innerHTML = html;

  var btn = container.querySelector('[data-alerts-feed-action]');
  if (btn) {
    btn.addEventListener('click', function() {
      if (btn.getAttribute('data-alerts-feed-action') === 'show-more') {
        alertsFeedShownCount = Math.min(alertsFeedShownCount + ALERTS_FEED_STEP, total);
      } else {
        alertsFeedShownCount = ALERTS_FEED_INITIAL;
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      var cached = lastRenderedAlertSignals;
      lastRenderedAlertSignals = null;
      renderAlertsFeed(cached);
      lastRenderedAlertSignals = cached;
    });
  }
}

function renderAlertsSummary(signals) {
  var el = document.getElementById('alerts-summary');
  if (!el) return;
  var counts = { funding: 0, contract: 0, sec: 0, news: 0, ipo: 0, mna: 0 };
  signals.forEach(function(s) {
    if (counts.hasOwnProperty(s.type)) counts[s.type]++;
  });
  el.innerHTML = ''
    + '<div class="alerts-stat"><span class="alerts-stat-num">' + signals.length + '</span><span class="alerts-stat-label">Total Signals</span></div>'
    + '<div class="alerts-stat"><span class="alerts-stat-num">' + counts.funding + '</span><span class="alerts-stat-label">Funding</span></div>'
    + '<div class="alerts-stat"><span class="alerts-stat-num">' + counts.contract + '</span><span class="alerts-stat-label">Contracts</span></div>'
    + '<div class="alerts-stat"><span class="alerts-stat-num">' + counts.news + '</span><span class="alerts-stat-label">News</span></div>'
    + '<div class="alerts-stat"><span class="alerts-stat-num">' + counts.sec + '</span><span class="alerts-stat-label">SEC</span></div>'
    + '<div class="alerts-stat"><span class="alerts-stat-num">' + counts.ipo + '</span><span class="alerts-stat-label">IPO</span></div>';
}

function populateSectorFilter(signals) {
  var sel = document.getElementById('sector-filter');
  if (!sel) return;
  var seen = {};
  signals.forEach(function(s) {
    if (s.sector && !seen[s.sector]) seen[s.sector] = true;
  });
  var sectors = Object.keys(seen).sort();
  sectors.forEach(function(sector) {
    var opt = document.createElement('option');
    opt.value = sector;
    opt.textContent = sector;
    sel.appendChild(opt);
  });
}

// ─── FILTERING ───────────────────────────────────────────────────────────────
function applyAllFilters() {
  var f = ALERTS_STATE.filters;
  var now = Date.now();
  var timeMs = { '24h': 24 * 3600 * 1000, '7d': 7 * 86400 * 1000, '30d': 30 * 86400 * 1000 };
  var items = document.querySelectorAll('.alert-item');
  items.forEach(function(item) {
    var matchType = f.type === 'all' || item.dataset.type === f.type;
    var matchSector = f.sector === 'all' || item.dataset.sector === f.sector;
    var matchTime = true;
    if (f.time !== 'all' && timeMs[f.time]) {
      var d = item.dataset.date;
      if (!d) {
        matchTime = false;
      } else {
        var ts = new Date(d).getTime();
        matchTime = !isNaN(ts) && (now - ts) <= timeMs[f.time];
      }
    }
    item.style.display = (matchType && matchSector && matchTime) ? '' : 'none';
  });
}

function initFilters() {
  // Type tabs
  var filterBtns = document.querySelectorAll('.alert-filter[data-filter="type"]');
  filterBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      filterBtns.forEach(function(b) { b.classList.remove('active'); });
      this.classList.add('active');
      ALERTS_STATE.filters.type = this.dataset.type || 'all';
      applyAllFilters();
    });
  });

  // Sector select
  var sectorSel = document.getElementById('sector-filter');
  if (sectorSel) {
    sectorSel.addEventListener('change', function() {
      ALERTS_STATE.filters.sector = this.value || 'all';
      applyAllFilters();
    });
  }

  // Time range
  var timeSel = document.getElementById('time-filter');
  if (timeSel) {
    timeSel.addEventListener('change', function() {
      ALERTS_STATE.filters.time = this.value || 'all';
      applyAllFilters();
    });
  }

  // Create Alert CTA (placeholder link to settings)
  var cta = document.getElementById('create-alert-btn');
  if (cta) {
    cta.addEventListener('click', function() {
      alert('Alert preferences are coming soon. For now, all signals for tracked companies appear in this feed.');
    });
  }
}

// ─── BOOT ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  alertsInitMobileMenu();
  try {
    var signals = aggregateDealSignals();
    ALERTS_STATE.all = signals;
    populateSectorFilter(signals);
    renderAlertsSummary(signals);
    renderAlertsFeed(signals);
    initFilters();
  } catch (e) {
    console.error('[alerts] failed to render feed:', e);
    var container = document.getElementById('alerts-feed');
    if (container) {
      container.innerHTML = '<div class="alerts-empty"><h3>Unable to load alerts</h3><p>' + alertsEscapeHtml(e.message || 'Unknown error') + '</p></div>';
    }
  }
});
