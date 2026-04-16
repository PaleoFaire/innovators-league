// ═══════════════════════════════════════════════════════════════════════════════
// SECTOR EXPLORER — sectors.js
// The Innovators League | Rational Optimist Society
// ═══════════════════════════════════════════════════════════════════════════════
// Top-level: grid of sector cards (one per SECTORS entry).
// Drilldown (via ?sector=slug): hero + sub-segments + market map + companies
//                               grid + top investors + gov activity + trend.
// ═══════════════════════════════════════════════════════════════════════════════

// ─── State ───────────────────────────────────────────────────────────────────

var SX_STATE = {
  samContracts: null,   // JSON array from sam_contracts_aggregated.json
  sbirAwards: null,     // JSON array from sbir_awards_auto.json
  currentSector: null,  // null in index view; string name in drilldown
  companySearch: '',
  companySort: 'score'
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function sxEsc(s) {
  return (typeof escapeHtml === 'function') ? escapeHtml(String(s == null ? '' : s)) : String(s == null ? '' : s);
}

function sxFormat(num) {
  if (!num || !isFinite(num) || num <= 0) return '$0';
  var abs = Math.abs(num);
  if (abs >= 1e12) return '$' + (num / 1e12).toFixed(1) + 'T';
  if (abs >= 1e9) return '$' + (num / 1e9).toFixed(1) + 'B';
  if (abs >= 1e6) return '$' + (num / 1e6).toFixed(0) + 'M';
  if (abs >= 1e3) return '$' + (num / 1e3).toFixed(0) + 'K';
  return '$' + num.toFixed(0);
}

function sxParseMoney(str) {
  if (!str) return 0;
  if (typeof str === 'number') return str;
  var m = String(str).match(/\$?\s*([\d,.]+)\s*([BMTKbmtk])?/);
  if (!m) return 0;
  var n = parseFloat(m[1].replace(/,/g, ''));
  if (!isFinite(n)) return 0;
  var u = (m[2] || '').toUpperCase();
  if (u === 'T') return n * 1e12;
  if (u === 'B') return n * 1e9;
  if (u === 'M') return n * 1e6;
  if (u === 'K') return n * 1e3;
  return n;
}

function sxSlug(name) {
  if (!name) return '';
  return String(name).toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function sxSectorFromSlug(slug) {
  if (!slug || typeof SECTORS === 'undefined') return null;
  var keys = Object.keys(SECTORS);
  for (var i = 0; i < keys.length; i++) {
    if (sxSlug(keys[i]) === slug) return keys[i];
  }
  return null;
}

// Map a raw company.sector string (which may be mis-cased or legacy) to a
// canonical SECTORS key. Returns null if no match is found.
var _sxSectorAliasCache = null;
function sxResolveSectorKey(raw) {
  if (!raw || typeof SECTORS === 'undefined') return null;
  if (!_sxSectorAliasCache) {
    _sxSectorAliasCache = {};
    Object.keys(SECTORS).forEach(function(k) {
      _sxSectorAliasCache[k.toLowerCase()] = k;
      _sxSectorAliasCache[sxSlug(k)] = k;
    });
    // Hand-curated aliases for legacy / variant sector strings
    var aliases = {
      'energy & climate':       'Climate & Energy',
      'climate and energy':     'Climate & Energy',
      'ai & autonomy':          'AI & Software',
      'advanced manufacturing': 'Robotics & Manufacturing',
      'robotics & automation':  'Robotics & Manufacturing',
      'biotech & medical':      'Biotech & Health',
      'construction & housing': 'Housing & Construction',
      'semiconductors':         'Chips & Semiconductors'
    };
    Object.keys(aliases).forEach(function(k) {
      _sxSectorAliasCache[k] = aliases[k];
      _sxSectorAliasCache[sxSlug(k)] = aliases[k];
    });
  }
  var key = String(raw).toLowerCase().trim();
  if (_sxSectorAliasCache[key]) return _sxSectorAliasCache[key];
  var sluggy = sxSlug(raw);
  if (_sxSectorAliasCache[sluggy]) return _sxSectorAliasCache[sluggy];
  return null;
}

// Return all companies whose sector matches this canonical SECTORS key,
// tolerating case / alias differences.
function sxCompaniesForSector(sectorName) {
  if (!sectorName) return [];
  return COMPANIES.filter(function(c) {
    if (!c || !c.sector) return false;
    if (c.sector === sectorName) return true;
    return sxResolveSectorKey(c.sector) === sectorName;
  });
}

function sxGetFrontierIndex(companyName) {
  if (typeof INNOVATOR_SCORES === 'undefined' || !companyName) return null;
  var row = INNOVATOR_SCORES.find(function(s) { return s.company === companyName; });
  return row && typeof row.composite === 'number' ? row.composite : null;
}

function sxGetTotalRaisedValue(company) {
  // Prefer FUNDING_TRACKER if it has a larger/more recent value
  var fromCompany = sxParseMoney(company.totalRaised);
  if (typeof FUNDING_TRACKER !== 'undefined') {
    var row = FUNDING_TRACKER.find(function(r) { return r.company === company.name; });
    if (row) {
      var tr = sxParseMoney(row.totalRaised);
      if (tr > fromCompany) return tr;
    }
  }
  return fromCompany;
}

function sxGetStageRank(stage) {
  if (!stage) return 0;
  var s = String(stage).toLowerCase();
  if (s.indexOf('pre-seed') >= 0) return 1;
  if (s.indexOf('seed') >= 0) return 2;
  if (s.indexOf('series a') >= 0) return 3;
  if (s.indexOf('series b') >= 0) return 4;
  if (s.indexOf('series c') >= 0) return 5;
  if (s.indexOf('series d') >= 0) return 6;
  if (s.indexOf('series e') >= 0) return 7;
  if (s.indexOf('series f') >= 0) return 8;
  if (s.indexOf('series g') >= 0) return 9;
  if (s.indexOf('series h') >= 0 || s.indexOf('series i') >= 0 || s.indexOf('series j') >= 0) return 10;
  if (s.indexOf('late stage') >= 0 || s.indexOf('growth') >= 0 || s.indexOf('mega') >= 0) return 10;
  if (s.indexOf('ipo') >= 0 || s.indexOf('public') >= 0 || s.indexOf('spac') >= 0) return 11;
  return 0;
}

function sxBucket(company) {
  // Leaders / Challengers / Emerging — based on FI and stage
  var fi = sxGetFrontierIndex(company.name);
  var stageRank = sxGetStageRank(company.fundingStage);
  if ((fi != null && fi >= 80) || stageRank >= 5) return 'leaders';
  if ((fi != null && fi >= 60) || stageRank >= 3) return 'challengers';
  return 'emerging';
}

// ─── Boot ────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
  // Mobile menu
  var btn = document.querySelector('.mobile-menu-btn');
  var links = document.querySelector('.nav-links');
  if (btn && links) {
    btn.addEventListener('click', function() {
      links.classList.toggle('open');
      btn.classList.toggle('open');
    });
  }

  if (typeof TILAuth !== 'undefined' && TILAuth.onReady) {
    TILAuth.onReady(function() { initSectors(); });
  } else {
    initSectors();
  }
});

function initSectors() {
  if (typeof SECTORS === 'undefined' || typeof COMPANIES === 'undefined') {
    console.warn('[Sectors] Required globals (SECTORS, COMPANIES) not loaded.');
    return;
  }

  // Preload JSON resources (best-effort, non-blocking renders still work)
  var samP = fetch('data/sam_contracts_aggregated.json', { cache: 'default' })
    .then(function(r) { return r.ok ? r.json() : []; })
    .catch(function() { return []; });
  var sbirP = fetch('data/sbir_awards_auto.json', { cache: 'default' })
    .then(function(r) { return r.ok ? r.json() : []; })
    .catch(function() { return []; });

  Promise.all([samP, sbirP]).then(function(vals) {
    SX_STATE.samContracts = Array.isArray(vals[0]) ? vals[0] : [];
    SX_STATE.sbirAwards = Array.isArray(vals[1]) ? vals[1] : [];
    // Re-render drilldown gov panel if we're already on one
    if (SX_STATE.currentSector) {
      safeInit('sxRenderGov', function() { sxRenderGov(SX_STATE.currentSector); });
    }
  });

  // Decide view based on URL
  var params = new URLSearchParams(window.location.search);
  var slug = params.get('sector');
  var sectorName = slug ? sxSectorFromSlug(slug) : null;

  if (sectorName) {
    sxShowDrilldown(sectorName);
  } else {
    sxShowIndex();
  }

  // Handle back-link — keep SPA feel without hash churn
  var backLink = document.getElementById('sx-back-link');
  if (backLink) {
    backLink.addEventListener('click', function(e) {
      e.preventDefault();
      history.pushState({}, '', 'sectors.html');
      sxShowIndex();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // Browser back/forward
  window.addEventListener('popstate', function() {
    var p = new URLSearchParams(window.location.search);
    var sl = p.get('sector');
    var nm = sl ? sxSectorFromSlug(sl) : null;
    if (nm) sxShowDrilldown(nm);
    else sxShowIndex();
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// INDEX VIEW — grid of sector cards
// ═══════════════════════════════════════════════════════════════════════════════

function sxShowIndex() {
  SX_STATE.currentSector = null;

  var idxView = document.getElementById('sectors-index-view');
  var ddView = document.getElementById('sectors-drilldown-view');
  var idxHero = document.getElementById('sectors-index-hero');
  var ddHero = document.getElementById('sectors-drilldown-hero');
  if (idxView) idxView.style.display = '';
  if (ddView) ddView.style.display = 'none';
  if (idxHero) idxHero.style.display = '';
  if (ddHero) ddHero.style.display = 'none';

  var crumb = document.getElementById('breadcrumb-current');
  if (crumb) crumb.textContent = 'Sector Explorer';

  document.title = 'Sector Explorer | ROS Startup Database';

  safeInit('sxRenderIndexStats', sxRenderIndexStats);
  safeInit('sxRenderGrid', sxRenderGrid);
}

function sxRenderIndexStats() {
  var sectorNames = Object.keys(SECTORS);
  var sectorCount = sectorNames.length;
  var companyCount = COMPANIES.length;
  var totalFunding = 0;
  COMPANIES.forEach(function(c) { totalFunding += sxGetTotalRaisedValue(c); });

  var sEl = document.getElementById('sx-sector-count');
  if (sEl) sEl.textContent = sectorCount;
  var cEl = document.getElementById('sx-company-count');
  if (cEl) cEl.textContent = companyCount;
  var fEl = document.getElementById('sx-total-funding');
  if (fEl) fEl.textContent = sxFormat(totalFunding);
}

function sxRenderGrid() {
  var grid = document.getElementById('sx-grid');
  if (!grid) return;

  // Build sector summary data, sorted by company count desc
  var sectorNames = Object.keys(SECTORS);
  var summaries = sectorNames.map(function(name) {
    var info = SECTORS[name];
    var companies = sxCompaniesForSector(name);
    var totalFunding = 0;
    companies.forEach(function(c) { totalFunding += sxGetTotalRaisedValue(c); });

    // Top 3 by Frontier Index; fall back to valuation, then total raised
    var ranked = companies.slice().sort(function(a, b) {
      var sa = sxGetFrontierIndex(a.name) || 0;
      var sb = sxGetFrontierIndex(b.name) || 0;
      if (sb !== sa) return sb - sa;
      var va = sxParseMoney(a.valuation);
      var vb = sxParseMoney(b.valuation);
      if (vb !== va) return vb - va;
      return sxGetTotalRaisedValue(b) - sxGetTotalRaisedValue(a);
    });
    var top3 = ranked.slice(0, 3);

    return {
      name: name,
      info: info,
      companies: companies,
      totalFunding: totalFunding,
      top3: top3
    };
  }).sort(function(a, b) { return b.companies.length - a.companies.length; });

  grid.innerHTML = summaries.map(function(s) {
    var slug = sxSlug(s.name);
    var color = s.info.color || '#6b7280';
    var icon = s.info.icon || '';
    var topList = s.top3.length
      ? s.top3.map(function(c) {
          var fi = sxGetFrontierIndex(c.name);
          var fiBadge = fi != null ? '<span class="sx-card-fi" style="color:' + color + ';">' + fi.toFixed(0) + '</span>' : '';
          return '<li><span class="sx-card-top-name">' + sxEsc(c.name) + '</span>' + fiBadge + '</li>';
        }).join('')
      : '<li class="sx-card-empty">No companies tracked yet.</li>';

    return (
      '<a class="sx-card" href="sectors.html?sector=' + sxEsc(slug) + '" ' +
         'style="--sx-accent:' + color + ';">' +
        '<div class="sx-card-head">' +
          '<div class="sx-card-icon" style="background:' + color + '18; color:' + color + ';">' + sxEsc(icon) + '</div>' +
          '<div class="sx-card-title">' + sxEsc(s.name) + '</div>' +
        '</div>' +
        '<div class="sx-card-stats">' +
          '<div class="sx-card-stat"><div class="sx-card-stat-num">' + s.companies.length + '</div><div class="sx-card-stat-lbl">Companies</div></div>' +
          '<div class="sx-card-stat"><div class="sx-card-stat-num" style="color:' + color + ';">' + sxEsc(sxFormat(s.totalFunding)) + '</div><div class="sx-card-stat-lbl">Capital Raised</div></div>' +
        '</div>' +
        '<div class="sx-card-top-title">Top Players</div>' +
        '<ul class="sx-card-top">' + topList + '</ul>' +
        '<div class="sx-card-cta">Explore &rarr;</div>' +
      '</a>'
    );
  }).join('');
}

// ═══════════════════════════════════════════════════════════════════════════════
// DRILLDOWN VIEW
// ═══════════════════════════════════════════════════════════════════════════════

function sxShowDrilldown(sectorName) {
  if (!sectorName || !SECTORS[sectorName]) {
    // Unknown sector — fall back to index
    sxShowIndex();
    return;
  }
  SX_STATE.currentSector = sectorName;

  var idxView = document.getElementById('sectors-index-view');
  var ddView = document.getElementById('sectors-drilldown-view');
  var idxHero = document.getElementById('sectors-index-hero');
  var ddHero = document.getElementById('sectors-drilldown-hero');
  if (idxView) idxView.style.display = 'none';
  if (ddView) ddView.style.display = '';
  if (idxHero) idxHero.style.display = 'none';
  if (ddHero) ddHero.style.display = '';

  var crumb = document.getElementById('breadcrumb-current');
  if (crumb) crumb.textContent = sectorName;

  document.title = sectorName + ' | Sector Explorer | ROS';

  safeInit('sxRenderDrilldownHero', function() { sxRenderDrilldownHero(sectorName); });
  safeInit('sxRenderSegments',       function() { sxRenderSegments(sectorName); });
  safeInit('sxRenderMarketMap',      function() { sxRenderMarketMap(sectorName); });
  safeInit('sxRenderCompanies',      function() { sxRenderCompanies(sectorName); });
  safeInit('sxRenderInvestors',      function() { sxRenderInvestors(sectorName); });
  safeInit('sxRenderCrossLinks',     function() { sxRenderCrossLinks(sectorName); });
  safeInit('sxRenderGov',            function() { sxRenderGov(sectorName); });
  safeInit('sxRenderTrend',          function() { sxRenderTrend(sectorName); });
}

function sxRenderDrilldownHero(sectorName) {
  var info = SECTORS[sectorName];
  var color = info.color || '#FF6B2C';
  var companies = sxCompaniesForSector(sectorName);

  var totalFunding = 0;
  companies.forEach(function(c) { totalFunding += sxGetTotalRaisedValue(c); });

  // Median Frontier Index
  var scores = companies.map(function(c) { return sxGetFrontierIndex(c.name); }).filter(function(s) { return typeof s === 'number'; });
  scores.sort(function(a, b) { return a - b; });
  var medianFI = scores.length ? scores[Math.floor(scores.length / 2)] : 0;

  var hero = document.getElementById('sectors-drilldown-hero');
  if (hero) {
    hero.style.background = 'linear-gradient(135deg, ' + color + '22 0%, #0a0a0a 55%, ' + color + '10 100%)';
  }

  var iconEl = document.getElementById('sx-dd-icon');
  if (iconEl) {
    iconEl.textContent = info.icon || '';
    iconEl.style.background = color + '22';
    iconEl.style.color = color;
    iconEl.style.borderColor = color + '55';
  }

  var titleEl = document.getElementById('sx-dd-title');
  if (titleEl) titleEl.textContent = sectorName;

  var eyebrowEl = document.getElementById('sx-dd-eyebrow');
  if (eyebrowEl) eyebrowEl.style.color = color;

  var descEl = document.getElementById('sx-dd-description');
  if (descEl) descEl.textContent = info.description || '';

  var cEl = document.getElementById('sx-dd-companies');
  if (cEl) cEl.textContent = companies.length;
  var fEl = document.getElementById('sx-dd-funding');
  if (fEl) { fEl.textContent = sxFormat(totalFunding); fEl.style.color = color; }
  var fiEl = document.getElementById('sx-dd-fi');
  if (fiEl) fiEl.textContent = medianFI ? medianFI.toFixed(0) : '—';

  var trendEl = document.getElementById('sx-dd-trend');
  if (trendEl) {
    if (info.trend) {
      trendEl.innerHTML = '<span class="sx-trend-tag" style="background:' + color + '22; color:' + color + ';">WHY IT MATTERS</span> ' + sxEsc(info.trend);
      trendEl.style.display = '';
    } else {
      trendEl.style.display = 'none';
    }
  }

  // Link to transformation page if one exists for this sector
  var trLinkEl = document.getElementById('sx-dd-transformation-link');
  if (trLinkEl) {
    // Map sector -> transformation slug. Keys match COMPANIES[].sector values.
    var sectorToTransformation = {
      'Defense & Security': 'defense',
      'Drones & Autonomous': 'defense',
      'Ocean & Maritime': 'defense',
      'Supersonic & Hypersonic': 'defense',
      'Nuclear Energy': 'energy',
      'Climate & Energy': 'energy',
      'Energy & Climate': 'energy',
      'Space & Aerospace': 'space',
      'Transportation': 'automotive',
      'Biotech & Health': 'pharma',
      'Biotech & Medical': 'pharma',
      'Advanced Manufacturing': 'materials',
      'Robotics & Manufacturing': 'materials',
      'Robotics & Automation': 'materials'
    };
    var slug = sectorToTransformation[sectorName];
    if (slug) {
      trLinkEl.href = 'transformation/' + slug + '.html';
      var titleEl2 = document.getElementById('sx-dd-transformation-title');
      if (titleEl2) titleEl2.textContent = 'View full ' + sectorName + ' transformation analysis';
      trLinkEl.style.display = '';
    } else {
      trLinkEl.style.display = 'none';
    }
  }
}

function sxRenderSegments(sectorName) {
  var wrap = document.getElementById('sx-segments-wrap');
  if (!wrap) return;
  var companies = sxCompaniesForSector(sectorName);
  var color = (SECTORS[sectorName] && SECTORS[sectorName].color) || '#FF6B2C';

  // Group by thesisCluster first; fall back to first tag; else "Other"
  var groups = {};
  companies.forEach(function(c) {
    var key = null;
    if (c.thesisCluster) {
      key = String(c.thesisCluster);
    } else if (c.tags && c.tags.length) {
      key = String(c.tags[0]);
    } else {
      key = 'Other';
    }
    if (!groups[key]) groups[key] = [];
    groups[key].push(c);
  });

  var groupArr = Object.keys(groups).map(function(k) {
    return { key: k, companies: groups[k] };
  }).sort(function(a, b) { return b.companies.length - a.companies.length; });

  if (groupArr.length === 0) {
    wrap.innerHTML = '<div class="sx-empty">No companies tracked in this sector yet.</div>';
    return;
  }

  function prettyKey(k) {
    if (!k) return 'Other';
    return String(k).replace(/-/g, ' ').replace(/\b\w/g, function(l) { return l.toUpperCase(); });
  }

  wrap.innerHTML = groupArr.map(function(g) {
    var preview = g.companies.slice(0, 6).map(function(c) {
      var fi = sxGetFrontierIndex(c.name);
      var fiBadge = fi != null ? '<span class="sx-seg-fi">' + fi.toFixed(0) + '</span>' : '';
      return '<a class="sx-seg-chip" href="company.html?slug=' + encodeURIComponent(sxSlug(c.name)) + '">' + sxEsc(c.name) + fiBadge + '</a>';
    }).join('');
    var more = g.companies.length > 6 ? '<span class="sx-seg-more">+' + (g.companies.length - 6) + ' more</span>' : '';
    return (
      '<div class="sx-seg-card" style="--sx-accent:' + color + ';">' +
        '<div class="sx-seg-head">' +
          '<div class="sx-seg-title">' + sxEsc(prettyKey(g.key)) + '</div>' +
          '<div class="sx-seg-count">' + g.companies.length + ' companies</div>' +
        '</div>' +
        '<div class="sx-seg-chips">' + preview + more + '</div>' +
      '</div>'
    );
  }).join('');
}

function sxRenderMarketMap(sectorName) {
  var wrap = document.getElementById('sx-marketmap');
  if (!wrap) return;
  var companies = sxCompaniesForSector(sectorName);

  var buckets = { leaders: [], challengers: [], emerging: [] };
  companies.forEach(function(c) { buckets[sxBucket(c)].push(c); });

  // Sort each bucket by FI desc, then total raised desc
  Object.keys(buckets).forEach(function(k) {
    buckets[k].sort(function(a, b) {
      var sa = sxGetFrontierIndex(a.name) || 0;
      var sb = sxGetFrontierIndex(b.name) || 0;
      if (sb !== sa) return sb - sa;
      return sxGetTotalRaisedValue(b) - sxGetTotalRaisedValue(a);
    });
  });

  var defs = [
    { key: 'leaders',     label: 'Leaders',     color: '#22c55e', sub: 'Series C+ or Frontier Index > 80' },
    { key: 'challengers', label: 'Challengers', color: '#3b82f6', sub: 'Series A/B + Frontier Index 60-80' },
    { key: 'emerging',    label: 'Emerging',    color: '#f59e0b', sub: 'Seed / Pre-seed or FI < 60' }
  ];

  wrap.innerHTML = defs.map(function(d) {
    var items = buckets[d.key];
    var body = items.length
      ? items.map(function(c) {
          var fi = sxGetFrontierIndex(c.name);
          var fiTxt = fi != null ? '<span class="sx-mm-fi" style="color:' + d.color + ';">FI ' + fi.toFixed(0) + '</span>' : '';
          var stg = c.fundingStage ? '<span class="sx-mm-stage">' + sxEsc(c.fundingStage) + '</span>' : '';
          return (
            '<a class="sx-mm-row" href="company.html?slug=' + encodeURIComponent(sxSlug(c.name)) + '">' +
              '<span class="sx-mm-name">' + sxEsc(c.name) + '</span>' +
              '<span class="sx-mm-meta">' + stg + fiTxt + '</span>' +
            '</a>'
          );
        }).join('')
      : '<div class="sx-mm-empty">No companies in this tier yet.</div>';

    return (
      '<div class="sx-mm-col sx-mm-' + d.key + '" style="--sx-mm-color:' + d.color + ';">' +
        '<div class="sx-mm-head">' +
          '<div class="sx-mm-label">' + sxEsc(d.label) + '</div>' +
          '<div class="sx-mm-count">' + items.length + '</div>' +
        '</div>' +
        '<div class="sx-mm-sub">' + sxEsc(d.sub) + '</div>' +
        '<div class="sx-mm-list">' + body + '</div>' +
      '</div>'
    );
  }).join('');
}

function sxRenderCompanies(sectorName) {
  var grid = document.getElementById('sx-companies-grid');
  var heading = document.getElementById('sx-companies-heading');
  if (!grid) return;

  var all = sxCompaniesForSector(sectorName);
  if (heading) heading.textContent = 'Companies in ' + sectorName + ' (' + all.length + ')';

  var searchEl = document.getElementById('sx-company-search');
  var sortEl = document.getElementById('sx-company-sort');

  function renderList() {
    var q = (SX_STATE.companySearch || '').trim().toLowerCase();
    var sortKey = SX_STATE.companySort || 'score';
    var rows = all.slice();
    if (q) {
      rows = rows.filter(function(c) {
        return String(c.name || '').toLowerCase().indexOf(q) >= 0 ||
               String(c.description || '').toLowerCase().indexOf(q) >= 0 ||
               String(c.founder || '').toLowerCase().indexOf(q) >= 0;
      });
    }

    rows.sort(function(a, b) {
      if (sortKey === 'name') return String(a.name).localeCompare(String(b.name));
      if (sortKey === 'stage') return sxGetStageRank(b.fundingStage) - sxGetStageRank(a.fundingStage);
      if (sortKey === 'funding') return sxGetTotalRaisedValue(b) - sxGetTotalRaisedValue(a);
      // default: score desc
      var sa = sxGetFrontierIndex(a.name) || 0;
      var sb = sxGetFrontierIndex(b.name) || 0;
      return sb - sa;
    });

    if (rows.length === 0) {
      grid.innerHTML = '<div class="sx-empty">No companies match your filters.</div>';
      return;
    }

    grid.innerHTML = rows.map(sxRenderCompanyCard).join('');
  }

  if (searchEl && !searchEl.dataset.bound) {
    searchEl.addEventListener('input', function() {
      SX_STATE.companySearch = searchEl.value;
      renderList();
    });
    searchEl.dataset.bound = '1';
  }
  if (sortEl && !sortEl.dataset.bound) {
    sortEl.addEventListener('change', function() {
      SX_STATE.companySort = sortEl.value;
      renderList();
    });
    sortEl.dataset.bound = '1';
  }

  renderList();
}

function sxRenderCompanyCard(c) {
  var info = SECTORS[c.sector] || { icon: '', color: '#6b7280' };
  var color = info.color || '#6b7280';
  var fi = sxGetFrontierIndex(c.name);
  var fiBadge = fi != null
    ? '<span class="sx-cc-fi" style="color:' + color + ';">FI ' + fi.toFixed(0) + '</span>'
    : '';
  var stage = c.fundingStage ? '<span class="sx-cc-stage">' + sxEsc(c.fundingStage) + '</span>' : '';
  var raised = c.totalRaised ? '<span class="sx-cc-raised">' + sxEsc(c.totalRaised) + '</span>' : '';
  var desc = c.description ? String(c.description).slice(0, 120) + (c.description.length > 120 ? '…' : '') : '';
  var loc = c.location ? sxEsc(c.location) : '';

  var slug = sxSlug(c.name);

  return (
    '<a class="sx-cc" href="company.html?slug=' + encodeURIComponent(slug) + '" style="--sx-accent:' + color + ';">' +
      '<div class="sx-cc-head">' +
        '<span class="sx-cc-sector" style="background:' + color + '1a; color:' + color + ';">' + sxEsc(info.icon) + ' ' + sxEsc(c.sector) + '</span>' +
        fiBadge +
      '</div>' +
      '<div class="sx-cc-name">' + sxEsc(c.name) + '</div>' +
      (c.founder ? '<div class="sx-cc-founder">' + sxEsc(c.founder) + '</div>' : '') +
      '<div class="sx-cc-desc">' + sxEsc(desc) + '</div>' +
      '<div class="sx-cc-foot">' +
        (loc ? '<span class="sx-cc-loc">' + loc + '</span>' : '') +
        stage +
        raised +
      '</div>' +
    '</a>'
  );
}

function sxRenderInvestors(sectorName) {
  var grid = document.getElementById('sx-investors-grid');
  if (!grid) return;
  var color = (SECTORS[sectorName] && SECTORS[sectorName].color) || '#8b5cf6';

  // Build company name set for this sector
  var companies = sxCompaniesForSector(sectorName);
  var companyNames = new Set(companies.map(function(c) { return c.name; }));

  // From VC_FIRMS: portfolio overlap
  var overlap = [];
  if (typeof VC_FIRMS !== 'undefined') {
    VC_FIRMS.forEach(function(v) {
      var pcs = v.portfolioCompanies || [];
      var matches = pcs.filter(function(n) { return companyNames.has(n); });
      var focusMatch = (v.sectorFocus || []).some(function(f) { return f === sectorName; });
      if (matches.length === 0 && !focusMatch) return;
      overlap.push({
        name: v.name,
        shortName: v.shortName || v.name,
        aum: v.aum,
        hq: v.hq,
        thesis: v.thesis,
        website: v.website,
        matches: matches,
        focusMatch: focusMatch
      });
    });
  }

  // Also count lead-investor appearances from FUNDING_TRACKER
  var leadCounts = {};
  if (typeof FUNDING_TRACKER !== 'undefined') {
    FUNDING_TRACKER.forEach(function(r) {
      if (!companyNames.has(r.company)) return;
      (r.leadInvestors || []).forEach(function(inv) {
        if (!inv || inv === 'Undisclosed') return;
        leadCounts[inv] = (leadCounts[inv] || 0) + 1;
      });
    });
  }

  // Attach lead counts to known firms (fuzzy: short-name or name substring)
  overlap.forEach(function(o) {
    var c = 0;
    Object.keys(leadCounts).forEach(function(lead) {
      var ll = lead.toLowerCase();
      if (ll === String(o.name).toLowerCase() ||
          ll === String(o.shortName).toLowerCase() ||
          String(o.name).toLowerCase().indexOf(ll) >= 0 ||
          ll.indexOf(String(o.shortName).toLowerCase()) >= 0) {
        c += leadCounts[lead];
      }
    });
    o.leadCount = c;
  });

  // Sort: portfolio overlap desc, then leadCount desc, then focusMatch
  overlap.sort(function(a, b) {
    if (b.matches.length !== a.matches.length) return b.matches.length - a.matches.length;
    if ((b.leadCount || 0) !== (a.leadCount || 0)) return (b.leadCount || 0) - (a.leadCount || 0);
    return (b.focusMatch ? 1 : 0) - (a.focusMatch ? 1 : 0);
  });

  var top = overlap.slice(0, 12);
  if (top.length === 0) {
    grid.innerHTML = '<div class="sx-empty">No tracked investors overlap with this sector yet.</div>';
    return;
  }

  grid.innerHTML = top.map(function(o) {
    var sampleNames = o.matches.slice(0, 4).map(sxEsc).join(', ');
    var moreCount = o.matches.length > 4 ? ' +' + (o.matches.length - 4) + ' more' : '';
    return (
      '<div class="sx-inv-card" style="--sx-accent:' + color + ';">' +
        '<div class="sx-inv-head">' +
          '<div class="sx-inv-name">' + sxEsc(o.shortName || o.name) + '</div>' +
          '<div class="sx-inv-aum">' + sxEsc(o.aum || '') + '</div>' +
        '</div>' +
        (o.hq ? '<div class="sx-inv-hq">' + sxEsc(o.hq) + '</div>' : '') +
        '<div class="sx-inv-stats">' +
          '<span class="sx-inv-stat"><strong>' + o.matches.length + '</strong> portfolio cos</span>' +
          (o.leadCount ? '<span class="sx-inv-stat"><strong>' + o.leadCount + '</strong> leads tracked</span>' : '') +
          (o.focusMatch ? '<span class="sx-inv-chip" style="background:' + color + '22; color:' + color + ';">Focus Sector</span>' : '') +
        '</div>' +
        (sampleNames ? '<div class="sx-inv-samples">' + sampleNames + sxEsc(moreCount) + '</div>' : '') +
        '<a href="investors.html" class="sx-inv-cta">View Investor &rarr;</a>' +
      '</div>'
    );
  }).join('');
}

function sxRenderCrossLinks(sectorName) {
  var card = document.getElementById('sx-regulatory-card');
  if (card) {
    // Map to closest reg tab — just land on the page; users can filter there
    card.href = 'regulatory.html?sector=' + encodeURIComponent(sxSlug(sectorName));
    var desc = document.getElementById('sx-regulatory-desc');
    if (desc) desc.textContent = 'Open the regulatory feed — timelines, pathways, and FDA/NRC/FAA/DOE filings tagged to ' + sectorName + '.';
  }
}

function sxRenderGov(sectorName) {
  var contractsUl = document.getElementById('sx-gov-contracts');
  var sbirUl = document.getElementById('sx-gov-sbir');

  var companyNames = sxCompaniesForSector(sectorName).map(function(c) { return c.name; });
  var lowerNames = companyNames.map(function(n) { return n.toLowerCase(); });

  function nameMatches(input) {
    if (!input) return false;
    var lower = String(input).toLowerCase();
    for (var i = 0; i < lowerNames.length; i++) {
      var n = lowerNames[i];
      // Match if either direction contains the other (handles "Anduril" vs "Anduril Industries")
      if (n === lower || n.indexOf(lower) >= 0 || lower.indexOf(n) >= 0) return true;
    }
    return false;
  }

  // Contracts
  if (contractsUl) {
    if (Array.isArray(SX_STATE.samContracts) && SX_STATE.samContracts.length) {
      var contracts = SX_STATE.samContracts
        .filter(function(c) { return nameMatches(c.company); })
        .sort(function(a, b) { return (b.opportunityCount || 0) - (a.opportunityCount || 0); })
        .slice(0, 6);
      if (contracts.length) {
        contractsUl.innerHTML = contracts.map(function(c) {
          return '<li><span class="sx-gov-name">' + sxEsc(c.company) + '</span>' +
                 '<span class="sx-gov-meta">' + (c.opportunityCount || 0) + ' opps · ' + sxEsc((c.agencies || [])[0] || '—') + '</span></li>';
        }).join('');
      } else {
        contractsUl.innerHTML = '<li class="sx-gov-empty">No federal contract activity detected yet.</li>';
      }
    } else if (SX_STATE.samContracts == null) {
      contractsUl.innerHTML = '<li class="sx-gov-loading">Loading contract data…</li>';
    } else {
      contractsUl.innerHTML = '<li class="sx-gov-empty">No contract data available.</li>';
    }
  }

  // SBIR
  if (sbirUl) {
    if (Array.isArray(SX_STATE.sbirAwards) && SX_STATE.sbirAwards.length) {
      var sbir = SX_STATE.sbirAwards
        .filter(function(a) { return nameMatches(a.company || a.firm); })
        .sort(function(a, b) { return (b.year || 0) - (a.year || 0); })
        .slice(0, 6);
      if (sbir.length) {
        sbirUl.innerHTML = sbir.map(function(a) {
          return '<li><span class="sx-gov-name">' + sxEsc(a.company || a.firm || '—') + '</span>' +
                 '<span class="sx-gov-meta">' + sxEsc(a.amount || '') + ' · ' + sxEsc(a.agency || '') + (a.year ? ' · ' + a.year : '') + '</span></li>';
        }).join('');
      } else {
        sbirUl.innerHTML = '<li class="sx-gov-empty">No SBIR awards detected yet.</li>';
      }
    } else if (SX_STATE.sbirAwards == null) {
      sbirUl.innerHTML = '<li class="sx-gov-loading">Loading SBIR data…</li>';
    } else {
      sbirUl.innerHTML = '<li class="sx-gov-empty">No SBIR data available.</li>';
    }
  }
}

function sxRenderTrend(sectorName) {
  var chart = document.getElementById('sx-trend-chart');
  var statsEl = document.getElementById('sx-trend-stats');
  if (!chart) return;
  var color = (SECTORS[sectorName] && SECTORS[sectorName].color) || '#3b82f6';

  var companyNames = new Set(sxCompaniesForSector(sectorName).map(function(c) { return c.name; }));

  // Build last 8 quarters from today (inclusive)
  function quarterKey(d) {
    return d.getFullYear() + '-Q' + (Math.floor(d.getMonth() / 3) + 1);
  }
  function quarterLabel(d) {
    return 'Q' + (Math.floor(d.getMonth() / 3) + 1) + ' ' + String(d.getFullYear()).slice(2);
  }
  function parseYMD(s) {
    if (!s) return null;
    // Accept "YYYY-MM" or "YYYY-MM-DD"
    var m = String(s).match(/^(\d{4})-(\d{1,2})(?:-(\d{1,2}))?/);
    if (!m) return null;
    return new Date(parseInt(m[1], 10), parseInt(m[2], 10) - 1, 1);
  }

  var now = new Date();
  var quarters = [];
  var curMonth = Math.floor(now.getMonth() / 3) * 3;
  var cur = new Date(now.getFullYear(), curMonth, 1);
  for (var i = 7; i >= 0; i--) {
    var d = new Date(cur.getFullYear(), cur.getMonth() - 3 * i, 1);
    quarters.push({ key: quarterKey(d), label: quarterLabel(d), deals: 0, dollars: 0 });
  }
  var keyIndex = {};
  quarters.forEach(function(q, idx) { keyIndex[q.key] = idx; });

  var totalDeals = 0, totalDollars = 0;
  if (typeof FUNDING_TRACKER !== 'undefined') {
    FUNDING_TRACKER.forEach(function(r) {
      if (!companyNames.has(r.company)) return;
      var d = parseYMD(r.lastRoundDate);
      if (!d) return;
      var k = quarterKey(d);
      if (keyIndex[k] == null) return;
      var slot = quarters[keyIndex[k]];
      slot.deals += 1;
      slot.dollars += sxParseMoney(r.lastRoundAmount);
      totalDeals += 1;
      totalDollars += sxParseMoney(r.lastRoundAmount);
    });
  }

  var maxDeals = quarters.reduce(function(m, q) { return Math.max(m, q.deals); }, 0);
  if (maxDeals === 0) {
    chart.innerHTML = '<div class="sx-empty">No tracked funding rounds in the last 8 quarters.</div>';
    if (statsEl) statsEl.innerHTML = '';
    return;
  }

  chart.innerHTML = quarters.map(function(q) {
    var h = Math.round((q.deals / maxDeals) * 100);
    return (
      '<div class="sx-bar-col">' +
        '<div class="sx-bar-val">' + q.deals + '</div>' +
        '<div class="sx-bar-track">' +
          '<div class="sx-bar-fill" style="height:' + h + '%; background:' + color + ';"></div>' +
        '</div>' +
        '<div class="sx-bar-label">' + sxEsc(q.label) + '</div>' +
      '</div>'
    );
  }).join('');

  if (statsEl) {
    statsEl.innerHTML =
      '<div class="sx-trend-stat"><div class="sx-trend-stat-num" style="color:' + color + ';">' + totalDeals + '</div><div class="sx-trend-stat-lbl">Deals (8 quarters)</div></div>' +
      '<div class="sx-trend-stat"><div class="sx-trend-stat-num" style="color:' + color + ';">' + sxFormat(totalDollars) + '</div><div class="sx-trend-stat-lbl">Capital deployed</div></div>';
  }
}
