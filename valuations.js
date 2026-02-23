// ═══════════════════════════════════════════════════════════════════════════════
// VALUATION INTELLIGENCE ENGINE — valuations.js
// The Innovators League | Rational Optimist Society
// ═══════════════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  // Mobile menu
  const btn = document.querySelector('.mobile-menu-btn');
  const links = document.querySelector('.nav-links');
  if (btn && links) {
    btn.addEventListener('click', () => {
      links.classList.toggle('open');
      btn.classList.toggle('open');
    });
  }

  if (typeof TILAuth !== 'undefined' && TILAuth.onReady) {
    TILAuth.onReady(() => { initValuations(); });
  } else {
    initValuations();
  }
});

// ─── Master Init ─────────────────────────────────────────────────────────────
function initValuations() {
  function safeInit(name, fn) {
    try { fn(); } catch (e) { console.error('[Valuations] ' + name + ' failed:', e); }
  }

  safeInit('initHeroStats', initHeroStats);
  safeInit('initSectorValMap', initSectorValMap);
  safeInit('initRevenueLeaderboard', initRevenueLeaderboard);
  safeInit('initOverUnder', initOverUnder);
  safeInit('initIPOTracker', initIPOTracker);
  safeInit('initMAComps', initMAComps);
  safeInit('initDealSignals', initDealSignals);
  safeInit('initCapitalHeatmap', initCapitalHeatmap);
  safeInit('initSectionObserver', initSectionObserver);
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Parse "$2.5B" / "$500M" / "$14B+" to raw number */
function parseValuation(str) {
  if (!str || typeof str !== 'string') return 0;
  const cleaned = str.replace(/[^0-9.\-BMKTbmkt+]/g, '').replace(/\+$/, '');
  const num = parseFloat(cleaned);
  if (isNaN(num)) return 0;
  const upper = str.toUpperCase();
  if (upper.includes('T')) return num * 1e12;
  if (upper.includes('B')) return num * 1e9;
  if (upper.includes('M')) return num * 1e6;
  if (upper.includes('K')) return num * 1e3;
  return num;
}

/** Format raw number to "$2.5B" */
function formatValue(num) {
  if (!num || num === 0) return 'N/A';
  const abs = Math.abs(num);
  if (abs >= 1e12) return '$' + (num / 1e12).toFixed(1) + 'T';
  if (abs >= 1e9) return '$' + (num / 1e9).toFixed(1) + 'B';
  if (abs >= 1e6) return '$' + (num / 1e6).toFixed(0) + 'M';
  if (abs >= 1e3) return '$' + (num / 1e3).toFixed(0) + 'K';
  return '$' + num.toFixed(0);
}

/** Format to "12.5x" */
function formatMultiple(num) {
  if (!num || !isFinite(num) || num <= 0) return 'N/A';
  if (num >= 1000) return num.toFixed(0) + 'x';
  if (num >= 100) return num.toFixed(1) + 'x';
  return num.toFixed(1) + 'x';
}

/** Parse revenue string — handles "$4.5B", "$106M-$110M" (takes first number), "Pre-Revenue" */
function parseRevenue(str) {
  if (!str || typeof str !== 'string') return 0;
  if (str.toLowerCase().includes('pre-revenue') || str.toLowerCase().includes('early revenue')) return 0;
  // Take first monetary value found
  const match = str.match(/\$?([\d.]+)\s*(T|B|M|K)?/i);
  if (!match) return 0;
  const num = parseFloat(match[1]);
  if (isNaN(num)) return 0;
  const unit = (match[2] || '').toUpperCase();
  if (unit === 'T') return num * 1e12;
  if (unit === 'B') return num * 1e9;
  if (unit === 'M') return num * 1e6;
  if (unit === 'K') return num * 1e3;
  return num;
}

/** Get sector icon from SECTORS object */
function getSectorIcon(sectorName) {
  if (typeof SECTORS !== 'undefined' && SECTORS[sectorName]) {
    return SECTORS[sectorName].icon || '';
  }
  // Fallback icons
  const fallback = {
    'Defense & Security': '\u{1F6E1}\u{FE0F}',
    'Nuclear Energy': '\u269B\u{FE0F}',
    'Space & Aerospace': '\u{1F680}',
    'AI & Software': '\u{1F916}',
    'Robotics & Manufacturing': '\u{1F3ED}',
    'Climate & Energy': '\u{1F30D}',
    'Biotech & Health': '\u{1F9EC}',
    'Chips & Semiconductors': '\u{1F48E}'
  };
  return fallback[sectorName] || '';
}

/** Get sector color from SECTORS object */
function getSectorColor(sectorName) {
  if (typeof SECTORS !== 'undefined' && SECTORS[sectorName]) {
    return SECTORS[sectorName].color || '#FF6B2C';
  }
  return '#FF6B2C';
}

// ─── 1. Hero Stats ───────────────────────────────────────────────────────────
function initHeroStats() {
  // Count companies with valuations
  let companyCount = 0;
  if (typeof COMPANIES !== 'undefined' && Array.isArray(COMPANIES)) {
    companyCount = COMPANIES.filter(c => c.valuation && parseValuation(c.valuation) > 0).length;
  }
  const countEl = document.getElementById('val-company-count');
  if (countEl) countEl.textContent = companyCount.toLocaleString();

  // Calculate median revenue multiple from REVENUE_INTEL + COMPANIES
  const multiples = computeRevenueMultiples();
  const validMultiples = multiples.filter(m => m.multiple > 0 && isFinite(m.multiple)).map(m => m.multiple).sort((a, b) => a - b);
  let medianMultiple = 0;
  if (validMultiples.length > 0) {
    const mid = Math.floor(validMultiples.length / 2);
    medianMultiple = validMultiples.length % 2 !== 0
      ? validMultiples[mid]
      : (validMultiples[mid - 1] + validMultiples[mid]) / 2;
  }
  const medianEl = document.getElementById('val-median-multiple');
  if (medianEl) medianEl.textContent = medianMultiple > 0 ? formatMultiple(medianMultiple) : 'N/A';

  // Sum valuations from COMPANIES (private valuations + public where valuation field exists)
  let totalVal = 0;
  let publicMcap = 0;
  if (typeof STOCK_PRICES !== 'undefined' && STOCK_PRICES) {
    Object.values(STOCK_PRICES).forEach(s => {
      if (s.marketCapRaw && s.marketCapRaw > 0) publicMcap += s.marketCapRaw;
    });
  }
  if (typeof COMPANIES !== 'undefined' && Array.isArray(COMPANIES)) {
    COMPANIES.forEach(c => {
      const val = parseValuation(c.valuation);
      if (val > 0) totalVal += val;
    });
  }
  // Use public market cap where available, otherwise use private valuations
  const displayTotal = publicMcap > 0 ? publicMcap + totalVal : totalVal;
  const mcapEl = document.getElementById('val-total-mcap');
  if (mcapEl) mcapEl.textContent = formatValue(displayTotal);
}

// ─── 2. Sector Valuation Map ─────────────────────────────────────────────────
function initSectorValMap() {
  const grid = document.getElementById('sector-val-grid');
  if (!grid) return;
  if (typeof VALUATION_BENCHMARKS === 'undefined' || !VALUATION_BENCHMARKS) {
    grid.innerHTML = '<div class="val-empty">Sector valuation data unavailable.</div>';
    return;
  }

  const stages = ['seed', 'seriesA', 'seriesB', 'seriesC', 'growth'];
  const stageLabels = { seed: 'Seed', seriesA: 'Series A', seriesB: 'Series B', seriesC: 'Series C', growth: 'Growth' };

  let html = '';
  for (const [sector, data] of Object.entries(VALUATION_BENCHMARKS)) {
    const icon = getSectorIcon(sector);
    html += `
      <div class="sector-val-card">
        <div class="sector-val-header">
          <span class="sector-val-icon">${icon}</span>
          <span class="sector-val-name">${sector}</span>
        </div>
        <table class="stage-table">
          <thead>
            <tr>
              <th>Stage</th>
              <th>Median</th>
              <th>Range</th>
              <th>Deals</th>
            </tr>
          </thead>
          <tbody>`;
    stages.forEach(stage => {
      const s = data[stage];
      if (s) {
        html += `
            <tr>
              <td>${stageLabels[stage]}</td>
              <td class="median-val">${s.median}</td>
              <td>${s.range}</td>
              <td class="deals-count">${s.deals}</td>
            </tr>`;
      }
    });
    html += `
          </tbody>
        </table>`;
    if (data.note) {
      html += `<div class="sector-val-note">${data.note}</div>`;
    }
    html += `</div>`;
  }
  grid.innerHTML = html;
}

// ─── 3. Revenue Multiple Leaderboard ─────────────────────────────────────────

/** Compute revenue multiples by joining REVENUE_INTEL with COMPANIES */
function computeRevenueMultiples() {
  if (typeof REVENUE_INTEL === 'undefined' || !Array.isArray(REVENUE_INTEL)) return [];
  if (typeof COMPANIES === 'undefined' || !Array.isArray(COMPANIES)) return [];

  const companyMap = {};
  COMPANIES.forEach(c => { companyMap[c.name] = c; });

  const results = [];
  REVENUE_INTEL.forEach(ri => {
    const rev = parseRevenue(ri.revenue);
    if (rev <= 0) return; // skip pre-revenue

    const company = companyMap[ri.company];
    let valuation = 0;
    let sector = '';

    if (company) {
      valuation = parseValuation(company.valuation);
      sector = company.sector || '';
    }

    // Also check STOCK_PRICES for public companies with market cap
    if (typeof STOCK_PRICES !== 'undefined' && STOCK_PRICES && company && company.ticker) {
      const stock = STOCK_PRICES[company.ticker];
      if (stock && stock.marketCapRaw && stock.marketCapRaw > 0) {
        valuation = stock.marketCapRaw;
      }
    }

    if (valuation <= 0) return;

    const multiple = valuation / rev;
    results.push({
      company: ri.company,
      revenue: rev,
      revenueStr: ri.revenue,
      valuation: valuation,
      valuationStr: formatValue(valuation),
      multiple: multiple,
      sector: sector,
      growth: ri.growth || 'N/A'
    });
  });

  return results;
}

/** Compute sector median multiples */
function computeSectorMedians(multiples) {
  const bySector = {};
  multiples.forEach(m => {
    if (!m.sector) return;
    if (!bySector[m.sector]) bySector[m.sector] = [];
    bySector[m.sector].push(m.multiple);
  });
  const medians = {};
  Object.entries(bySector).forEach(([sector, vals]) => {
    vals.sort((a, b) => a - b);
    const mid = Math.floor(vals.length / 2);
    medians[sector] = vals.length % 2 !== 0 ? vals[mid] : (vals[mid - 1] + vals[mid]) / 2;
  });
  return medians;
}

function initRevenueLeaderboard() {
  const tbody = document.getElementById('lb-body');
  const table = document.getElementById('lb-table');
  const searchInput = document.getElementById('lb-search');
  if (!tbody || !table) return;

  const multiples = computeRevenueMultiples();
  if (multiples.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="val-empty">Revenue data unavailable.</td></tr>';
    return;
  }

  const sectorMedians = computeSectorMedians(multiples);

  // Add vsMedian to each entry
  multiples.forEach(m => {
    const med = sectorMedians[m.sector];
    if (med && med > 0) {
      m.vsMedianRatio = m.multiple / med;
      const pct = ((m.vsMedianRatio - 1) * 100);
      m.vsMedianPct = pct;
      m.vsMedianStr = (pct >= 0 ? '+' : '') + pct.toFixed(0) + '%';
      if (m.vsMedianRatio > 1.5) m.vsMedianClass = 'premium';
      else if (m.vsMedianRatio >= 0.5) m.vsMedianClass = 'fair';
      else m.vsMedianClass = 'discount';
    } else {
      m.vsMedianRatio = 1;
      m.vsMedianPct = 0;
      m.vsMedianStr = 'N/A';
      m.vsMedianClass = 'fair';
    }
  });

  // State
  let sortKey = 'multiple';
  let sortDir = 'desc';
  let searchTerm = '';

  function renderTable() {
    let filtered = multiples;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      filtered = multiples.filter(m => m.company.toLowerCase().includes(q));
    }

    // Sort
    filtered.sort((a, b) => {
      let av, bv;
      switch (sortKey) {
        case 'company': av = a.company.toLowerCase(); bv = b.company.toLowerCase(); return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
        case 'revenue': av = a.revenue; bv = b.revenue; break;
        case 'valuation': av = a.valuation; bv = b.valuation; break;
        case 'multiple': av = a.multiple; bv = b.multiple; break;
        case 'vsMedian': av = a.vsMedianPct; bv = b.vsMedianPct; break;
        case 'growth':
          av = parseGrowth(a.growth); bv = parseGrowth(b.growth); break;
        default: av = a.multiple; bv = b.multiple;
      }
      return sortDir === 'asc' ? av - bv : bv - av;
    });

    tbody.innerHTML = filtered.map(m => `
      <tr>
        <td>${m.company}</td>
        <td>${m.revenueStr}</td>
        <td>${m.valuationStr}</td>
        <td><span class="lb-multiple">${formatMultiple(m.multiple)}</span></td>
        <td><span class="lb-vs-median ${m.vsMedianClass}">${m.vsMedianStr}</span></td>
        <td>${m.growth}</td>
      </tr>
    `).join('');
  }

  // Sort click handlers
  table.querySelectorAll('thead th').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      if (!key) return;
      if (sortKey === key) {
        sortDir = sortDir === 'asc' ? 'desc' : 'asc';
      } else {
        sortKey = key;
        sortDir = 'desc';
      }
      // Update header classes
      table.querySelectorAll('thead th').forEach(h => h.classList.remove('sorted-asc', 'sorted-desc'));
      th.classList.add(sortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');
      renderTable();
    });
  });

  // Search
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      searchTerm = searchInput.value.trim();
      renderTable();
    });
  }

  // Initial render sorted by multiple desc
  const multipleHeader = table.querySelector('th[data-sort="multiple"]');
  if (multipleHeader) multipleHeader.classList.add('sorted-desc');
  renderTable();
}

/** Parse growth string to numeric for sorting ("+56% YoY" => 56) */
function parseGrowth(str) {
  if (!str || str === 'N/A') return -Infinity;
  const match = str.match(/([\+\-]?[\d,]+(?:\.\d+)?)/);
  if (!match) return -Infinity;
  return parseFloat(match[1].replace(/,/g, ''));
}

// ─── 4. Over/Under Score ─────────────────────────────────────────────────────
function initOverUnder() {
  const grid = document.getElementById('ou-grid');
  if (!grid) return;

  const multiples = computeRevenueMultiples();
  if (multiples.length === 0) {
    grid.innerHTML = '<div class="val-empty">Revenue multiple data unavailable.</div>';
    return;
  }

  const sectorMedians = computeSectorMedians(multiples);

  // Enrich with vsMedian data
  const enriched = multiples.map(m => {
    const med = sectorMedians[m.sector];
    let ratio = 1;
    let cls = 'fair';
    let label = 'Fair Value';
    if (med && med > 0) {
      ratio = m.multiple / med;
      if (ratio > 1.5) { cls = 'premium'; label = 'Premium'; }
      else if (ratio < 0.5) { cls = 'discount'; label = 'Discount'; }
      else { cls = 'fair'; label = 'Fair Value'; }
    }
    return { ...m, ratio, cls, label };
  });

  // Sort: premiums first, then fair, then discounts (and within each, by ratio desc)
  const order = { premium: 0, fair: 1, discount: 2 };
  enriched.sort((a, b) => {
    if (order[a.cls] !== order[b.cls]) return order[a.cls] - order[b.cls];
    return b.ratio - a.ratio;
  });

  grid.innerHTML = enriched.map(m => `
    <div class="ou-card ${m.cls}">
      <div class="ou-company">${m.company}</div>
      <div class="ou-sector">${m.sector}</div>
      <div class="ou-stats">
        <div class="ou-stat-item"><strong>${formatMultiple(m.multiple)}</strong> multiple</div>
        <div class="ou-stat-item"><strong>${m.ratio.toFixed(1)}x</strong> vs sector</div>
        <span class="ou-badge ${m.cls}">${m.label}</span>
      </div>
    </div>
  `).join('');
}

// ─── 5. IPO Readiness Tracker ────────────────────────────────────────────────
function initIPOTracker() {
  const grid = document.getElementById('ipo-grid');
  if (!grid) return;
  if (typeof IPO_PIPELINE === 'undefined' || !Array.isArray(IPO_PIPELINE) || IPO_PIPELINE.length === 0) {
    grid.innerHTML = '<div class="val-empty">IPO pipeline data unavailable.</div>';
    return;
  }

  // Map likelihood to a numeric probability for progress bar
  const likelihoodPct = { high: 85, medium: 55, low: 25 };

  grid.innerHTML = IPO_PIPELINE.map(ipo => {
    const pct = likelihoodPct[ipo.likelihood] || 50;
    const lClass = ipo.likelihood || 'medium';
    return `
      <div class="ipo-card">
        <div class="ipo-card-header">
          <div class="ipo-company">${ipo.company}</div>
          <span class="ipo-likelihood ${lClass}">${(ipo.likelihood || 'unknown').toUpperCase()}</span>
        </div>
        <div class="ipo-status">${ipo.status || ''}</div>
        <div class="ipo-meta">
          <div>Target: <strong>${ipo.estimatedDate || 'TBD'}</strong></div>
          <div>Est. Valuation: <strong>${ipo.estimatedValuation || 'N/A'}</strong></div>
        </div>
        <div class="ipo-meta">
          <div>Sector: <strong>${ipo.sector || 'N/A'}</strong></div>
        </div>
        <div class="ipo-progress-wrap">
          <div class="ipo-progress-label">
            <span>IPO Likelihood</span>
            <span>${pct}%</span>
          </div>
          <div class="ipo-progress-bar">
            <div class="ipo-progress-fill ${lClass}" style="width: ${pct}%;"></div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ─── 6. M&A Comps Table ──────────────────────────────────────────────────────
function initMAComps() {
  const tbody = document.getElementById('ma-body');
  if (!tbody) return;
  if (typeof MA_COMPS === 'undefined' || !Array.isArray(MA_COMPS) || MA_COMPS.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="val-empty">M&A data unavailable.</td></tr>';
    return;
  }

  tbody.innerHTML = MA_COMPS.map(ma => {
    const typeClass = (ma.type || '').toLowerCase().replace(/\s/g, '');
    const evRevStr = (typeof ma.evRevenue === 'number') ? ma.evRevenue.toFixed(1) + 'x' : (ma.evRevenue || 'N/A');
    return `
      <tr>
        <td style="font-weight:600; color:var(--text-primary);">${ma.target || 'N/A'}</td>
        <td>${ma.acquirer || 'N/A'}</td>
        <td>${ma.dealValue || 'N/A'}</td>
        <td style="font-family:'Space Grotesk',sans-serif; font-weight:600; color:#FF6B2C;">${evRevStr}</td>
        <td>${ma.year || 'N/A'}</td>
        <td>${ma.sector || 'N/A'}</td>
        <td><span class="ma-type-badge ${typeClass}">${ma.type || 'N/A'}</span></td>
      </tr>
    `;
  }).join('');
}

// ─── 7. Deal Flow Signals ────────────────────────────────────────────────────
function initDealSignals() {
  const grid = document.getElementById('deal-signals-grid');
  if (!grid) return;
  if (typeof DEAL_FLOW_SIGNALS === 'undefined' || !Array.isArray(DEAL_FLOW_SIGNALS) || DEAL_FLOW_SIGNALS.length === 0) {
    grid.innerHTML = '<div class="val-empty">Deal flow signal data unavailable.</div>';
    return;
  }

  // Sort by probability desc
  const sorted = [...DEAL_FLOW_SIGNALS].sort((a, b) => (b.probability || 0) - (a.probability || 0));

  grid.innerHTML = sorted.map(ds => {
    const prob = ds.probability || 0;
    const signalsHtml = (ds.signals || []).map(s => `
      <div class="ds-signal-row">
        <span class="ds-signal-type">${s.type || ''}</span>
        <span class="ds-signal-desc">${s.description || ''}</span>
        <span class="ds-signal-weight">${s.weight || 0}%</span>
      </div>
    `).join('');

    const leadsHtml = (ds.potentialLeads && ds.potentialLeads.length > 0)
      ? `<div class="ds-leads"><strong>Potential Leads:</strong> ${ds.potentialLeads.join(', ')}</div>`
      : '';

    return `
      <div class="deal-signal-card">
        <div class="ds-header">
          <div class="ds-company">${ds.company}</div>
          <div class="ds-probability">${prob}%</div>
        </div>
        <div class="ds-progress-bar">
          <div class="ds-progress-fill" style="width: ${prob}%;"></div>
        </div>
        <div class="ds-meta">
          <div class="ds-meta-item">
            <span>Round</span>
            ${ds.expectedRound || 'N/A'}
          </div>
          <div class="ds-meta-item">
            <span>Amount</span>
            ${ds.expectedAmount || 'N/A'}
          </div>
          <div class="ds-meta-item">
            <span>Timeline</span>
            ${ds.expectedTiming || 'N/A'}
          </div>
        </div>
        <div class="ds-signals">
          ${signalsHtml}
        </div>
        ${leadsHtml}
      </div>
    `;
  }).join('');
}

// ─── 8. Capital Flow Heatmap ──────────────────────────────────────────────────

/** Normalize sector strings to canonical SECTORS keys */
function normalizeSector(sector) {
  if (!sector) return 'Other';
  const s = sector.trim();
  // Direct match
  if (typeof SECTORS !== 'undefined' && SECTORS[s]) return s;
  // Known variants → canonical
  const map = {
    'BioTech & Health': 'Biotech & Health',
    'Climate Tech': 'Climate & Energy',
    'Energy & Climate': 'Climate & Energy',
    'Construction Tech': 'Housing & Construction',
    'Quantum & Computing': 'Quantum Computing',
    'Robotics & AI': 'Robotics & Manufacturing',
    'Semiconductors': 'Chips & Semiconductors',
    'Space Systems': 'Space & Aerospace',
    'Autonomous Systems': 'Drones & Autonomous',
    'Advanced Materials': 'Climate & Energy',
    'Medical Devices': 'Biotech & Health'
  };
  return map[s] || s;
}

/** Normalize funding stage strings to 7 column buckets */
function normalizeFundingStage(stage) {
  if (!stage) return 'Other';
  const s = stage.trim().toLowerCase();
  if (s === 'pre-seed' || s === 'seed') return 'Seed';
  if (s === 'series a' || s === 'early stage') return 'Series A';
  if (s.startsWith('series b')) return 'Series B';
  if (s === 'series c') return 'Series C';
  if (s === 'series d' || s === 'series e' || s === 'series f' || s === 'series g') return 'Series D+';
  if (s === 'growth' || s === 'late stage' || s === 'pre-ipo' || s === 'private' || s === 'profitable' || s === 'bootstrapped' || s === 'fund') return 'Late / Growth';
  if (s === 'public' || s.startsWith('public') || s.startsWith('acquired') || s.includes('subsidiary') || s.startsWith('government')) return 'Public / Other';
  return 'Other';
}

function initCapitalHeatmap() {
  const statsEl = document.getElementById('cap-heatmap-stats');
  const wrapperEl = document.getElementById('cap-heatmap-wrapper');
  const velocityEl = document.getElementById('cap-velocity-grid');
  if (!wrapperEl) return;
  if (typeof COMPANIES === 'undefined' || !Array.isArray(COMPANIES)) return;

  // ── Stage columns (ordered)
  const stageCols = ['Seed', 'Series A', 'Series B', 'Series C', 'Series D+', 'Late / Growth', 'Public / Other'];

  // ── Aggregate capital into matrix[sector][stage]
  var matrix = {};       // sector → { stage → { total, count, companies[] } }
  var sectorTotals = {}; // sector → total capital
  var grandTotal = 0;
  var totalCompanies = 0;

  COMPANIES.forEach(function(c) {
    var raised = parseValuation(c.totalRaised);
    if (raised <= 0) return; // skip — only use actual capital raised, never valuation

    var sector = normalizeSector(c.sector);
    var stage = normalizeFundingStage(c.fundingStage);

    // Merge 'Other' stage into 'Public / Other'
    if (stage === 'Other') stage = 'Public / Other';

    if (!matrix[sector]) matrix[sector] = {};
    if (!matrix[sector][stage]) matrix[sector][stage] = { total: 0, count: 0, companies: [] };

    matrix[sector][stage].total += raised;
    matrix[sector][stage].count += 1;
    if (matrix[sector][stage].companies.length < 5) {
      matrix[sector][stage].companies.push({ name: c.name, raised: raised });
    }

    sectorTotals[sector] = (sectorTotals[sector] || 0) + raised;
    grandTotal += raised;
    totalCompanies++;
  });

  // ── Sort sectors by total capital descending
  var sortedSectors = Object.keys(sectorTotals).sort(function(a, b) {
    return sectorTotals[b] - sectorTotals[a];
  });

  // ── Find max cell value for heat scaling
  var maxCellTotal = 0;
  sortedSectors.forEach(function(sector) {
    stageCols.forEach(function(stage) {
      var cell = matrix[sector] && matrix[sector][stage];
      if (cell && cell.total > maxCellTotal) maxCellTotal = cell.total;
    });
  });

  // ── Render summary stats banner
  if (statsEl) {
    var hotSector = sortedSectors[0] || 'N/A';
    var hotIcon = getSectorIcon(hotSector);
    statsEl.innerHTML =
      '<div class="cap-stat-card">' +
        '<div class="cap-stat-value">' + formatValue(grandTotal) + '</div>' +
        '<div class="cap-stat-label">Total Capital Raised</div>' +
      '</div>' +
      '<div class="cap-stat-card">' +
        '<div class="cap-stat-value">' + totalCompanies + '</div>' +
        '<div class="cap-stat-label">Companies with Data</div>' +
      '</div>' +
      '<div class="cap-stat-card">' +
        '<div class="cap-stat-value">' + sortedSectors.length + '</div>' +
        '<div class="cap-stat-label">Sectors</div>' +
      '</div>' +
      '<div class="cap-stat-card">' +
        '<div class="cap-stat-value">' + hotIcon + ' ' + hotSector + '</div>' +
        '<div class="cap-stat-label">Highest Concentration</div>' +
      '</div>';
  }

  // ── Render CSS grid heatmap
  var gridHtml = '';

  // Header row: empty corner + stage labels
  gridHtml += '<div class="cap-hm-corner"></div>';
  stageCols.forEach(function(stage) {
    gridHtml += '<div class="cap-hm-col-header">' + stage + '</div>';
  });

  // Data rows
  sortedSectors.forEach(function(sector) {
    var icon = getSectorIcon(sector);
    var color = getSectorColor(sector);
    gridHtml += '<div class="cap-hm-row-label" style="border-left: 3px solid ' + color + ';">' +
      '<span class="cap-hm-row-icon">' + icon + '</span>' +
      '<span class="cap-hm-row-name">' + sector + '</span>' +
    '</div>';

    stageCols.forEach(function(stage) {
      var cell = matrix[sector] && matrix[sector][stage];
      if (cell && cell.total > 0) {
        var intensity = 0.08 + (cell.total / maxCellTotal) * 0.77;
        var bgColor = 'rgba(255,107,44,' + intensity.toFixed(2) + ')';
        var textColor = intensity > 0.5 ? '#fff' : 'var(--text-primary)';
        // Tooltip: top companies in this cell
        var tipCompanies = cell.companies.sort(function(a, b) { return b.raised - a.raised; })
          .map(function(co) { return co.name + ' (' + formatValue(co.raised) + ')'; }).join(', ');
        var tooltip = sector + ' · ' + stage + ': ' + formatValue(cell.total) + ' across ' + cell.count + ' companies. Top: ' + tipCompanies;

        gridHtml += '<div class="cap-hm-cell" style="background:' + bgColor + '; color:' + textColor + ';" title="' + tooltip.replace(/"/g, '&quot;') + '">' +
          '<div class="cap-hm-cell-amount">' + formatValue(cell.total) + '</div>' +
          '<div class="cap-hm-cell-count">' + cell.count + ' co' + (cell.count !== 1 ? 's' : '') + '</div>' +
        '</div>';
      } else {
        gridHtml += '<div class="cap-hm-cell cap-hm-empty">—</div>';
      }
    });
  });

  wrapperEl.innerHTML =
    '<div class="cap-heatmap-grid" style="grid-template-columns: 160px repeat(' + stageCols.length + ', 1fr); grid-template-rows: auto repeat(' + sortedSectors.length + ', auto);">' +
      gridHtml +
    '</div>' +
    '<div class="cap-heatmap-legend">' +
      '<span class="cap-legend-label">Low</span>' +
      '<div class="cap-legend-bar"></div>' +
      '<span class="cap-legend-label">High</span>' +
    '</div>';

  // ── Render velocity cards (one per sector)
  if (velocityEl) {
    var velocityHtml = '';
    sortedSectors.forEach(function(sector) {
      var icon = getSectorIcon(sector);
      var color = getSectorColor(sector);
      var total = sectorTotals[sector];
      var count = 0;
      var largestCo = { name: 'N/A', raised: 0 };

      // Aggregate per-sector stats
      stageCols.forEach(function(stage) {
        var cell = matrix[sector] && matrix[sector][stage];
        if (cell) {
          count += cell.count;
          cell.companies.forEach(function(co) {
            if (co.raised > largestCo.raised) largestCo = co;
          });
        }
      });

      var avgRaised = count > 0 ? total / count : 0;

      // Find dominant thesis cluster for this sector
      var thesisCounts = {};
      COMPANIES.forEach(function(c) {
        if (normalizeSector(c.sector) === sector && c.thesisCluster) {
          thesisCounts[c.thesisCluster] = (thesisCounts[c.thesisCluster] || 0) + 1;
        }
      });
      var dominantThesis = 'N/A';
      var maxThesisCount = 0;
      Object.keys(thesisCounts).forEach(function(t) {
        if (thesisCounts[t] > maxThesisCount) {
          maxThesisCount = thesisCounts[t];
          dominantThesis = t;
        }
      });

      // Pct of grand total
      var pctOfTotal = grandTotal > 0 ? ((total / grandTotal) * 100).toFixed(1) : '0';

      velocityHtml +=
        '<div class="cap-velocity-card">' +
          '<div class="cap-vel-header" style="border-left: 4px solid ' + color + ';">' +
            '<span class="cap-vel-icon">' + icon + '</span>' +
            '<span class="cap-vel-name">' + sector + '</span>' +
            '<span class="cap-vel-pct">' + pctOfTotal + '%</span>' +
          '</div>' +
          '<div class="cap-vel-total">' + formatValue(total) + '</div>' +
          '<div class="cap-vel-stats">' +
            '<div class="cap-vel-stat"><strong>' + count + '</strong> companies</div>' +
            '<div class="cap-vel-stat"><strong>' + formatValue(avgRaised) + '</strong> avg raised</div>' +
            '<div class="cap-vel-stat"><strong>' + largestCo.name + '</strong> largest (' + formatValue(largestCo.raised) + ')</div>' +
          '</div>' +
          '<div class="cap-vel-thesis">Dominant Thesis: <strong>' + dominantThesis + '</strong></div>' +
        '</div>';
    });

    velocityEl.innerHTML = velocityHtml;
  }
}

// ─── SECTION HEADER VISIBILITY OBSERVER ───
function initSectionObserver() {
  const headers = document.querySelectorAll('.section-header');
  if (!headers.length) return;
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    headers.forEach(h => observer.observe(h));
  } else {
    headers.forEach(h => h.classList.add('visible'));
  }
}
