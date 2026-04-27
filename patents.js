/* ─── Patent Velocity Page ─── */
/* Renders:
 *   1. Velocity leaderboard (sorted by QoQ change, from patent_velocity_auto.json)
 *   2. Per-company patent cards (clickable → expand, from PATENT_INTEL_AUTO)
 *   3. Sector breakdown (aggregate by sector)
 *   4. Top portfolios by total count
 *
 * Data sources:
 *   - PATENT_INTEL_AUTO         (loaded via <script> tag — rich per-company intel)
 *   - patent_velocity_auto.json (fetched — velocity-sorted view for leaderboard)
 */

(function () {
  'use strict';

  const esc = (typeof escapeHtml === 'function')
    ? escapeHtml
    : (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[c]));

  // Trend icon + color map
  const TREND_STYLES = {
    accelerating: { icon: '▲', color: '#22c55e', label: 'Accelerating' },
    steady:       { icon: '▪', color: '#60a5fa', label: 'Steady' },
    mature:       { icon: '●', color: '#a78bfa', label: 'Mature' },
    declining:    { icon: '▼', color: '#ef4444', label: 'Declining' },
  };

  const SECTOR_LABELS = {
    space:     { label: 'Space & Aerospace',       color: '#60a5fa' },
    defense:   { label: 'Defense & Dual-use',      color: '#f59e0b' },
    ai:        { label: 'AI & Compute',            color: '#a78bfa' },
    ev:        { label: 'Electric Vehicles',       color: '#22c55e' },
    autonomy:  { label: 'Autonomous Driving',      color: '#06b6d4' },
    evtol:     { label: 'Advanced Air Mobility',   color: '#ec4899' },
    nuclear:   { label: 'Nuclear Energy',          color: '#eab308' },
    fusion:    { label: 'Fusion Energy',           color: '#f97316' },
    quantum:   { label: 'Quantum Computing',       color: '#8b5cf6' },
    robotics:  { label: 'Robotics',                color: '#14b8a6' },
    biotech:   { label: 'Biotech & Health',        color: '#f472b6' },
  };

  function sectorStyle(s) {
    return SECTOR_LABELS[s] || { label: (s || '—'), color: '#FF6B2C' };
  }

  // Tiny SVG sparkline from an array of values
  function sparkline(values, opts) {
    opts = opts || {};
    const w = opts.width || 120;
    const h = opts.height || 32;
    const color = opts.color || '#FF6B2C';
    if (!values || values.length < 2) return '';
    const min = Math.min.apply(null, values);
    const max = Math.max.apply(null, values);
    const range = Math.max(1, max - min);
    const stepX = w / (values.length - 1);
    const pts = values.map((v, i) => {
      const x = i * stepX;
      const y = h - ((v - min) / range) * (h - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" style="display:block;">
      <polyline points="${pts.join(' ')}" fill="none" stroke="${color}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>
      <circle cx="${(pts[pts.length - 1].split(',')[0])}" cy="${(pts[pts.length - 1].split(',')[1])}" r="2.5" fill="${color}"/>
    </svg>`;
  }

  // ── Hold the velocity dataset globally for filters/compare ──────
  let _velocityData = [];
  const _filterState = { search: '', sector: '', trend: '' };

  // ── Acceleration Alerts: latest_Q vs trailing-4Q-avg ────────────
  // VC leading indicator: a company suddenly filing 2-3x its baseline
  // signals R&D acceleration before commercial inflection.
  function computeAccelerationCandidates(velocityData) {
    if (!velocityData || velocityData.length === 0) return [];
    const out = [];
    velocityData.forEach((r) => {
      const qs = r.quarters || [];
      if (qs.length < 5) return; // need at least latest + 4 prior
      const latest = qs[qs.length - 1].filings || 0;
      const prior4 = qs.slice(-5, -1).map(q => q.filings || 0);
      const prior4Avg = prior4.reduce((s, v) => s + v, 0) / prior4.length;
      if (prior4Avg < 1) return; // skip companies with no baseline (avoids div-by-zero noise)
      if (latest < 3) return;     // filter out tiny absolute counts (noise filter)
      const accelPct = ((latest - prior4Avg) / prior4Avg) * 100;
      if (accelPct < 50) return;  // only flag >=50% spikes
      out.push({
        company: r.company,
        sector: r.sector,
        latest,
        prior4Avg,
        accelPct,
        latestQuarter: qs[qs.length - 1].quarter,
        sourceUrl: r.sourceUrl,
        usptoUrl: r.usptoUrl,
      });
    });
    return out.sort((a, b) => b.accelPct - a.accelPct).slice(0, 12);
  }

  function renderAccelerationAlerts(velocityData) {
    const wrap = document.getElementById('patent-acceleration-grid');
    if (!wrap) return;
    const candidates = computeAccelerationCandidates(velocityData);
    if (candidates.length === 0) {
      wrap.innerHTML = '<div style="padding:32px; text-align:center; color:rgba(255,255,255,0.4); font-size:13px;">No companies are currently exhibiting >50% acceleration above baseline. Quiet quarter.</div>';
      return;
    }
    wrap.className = 'pat-accel-grid';
    wrap.innerHTML = candidates.map((c, i) => {
      const sector = sectorStyle(c.sector);
      const source = esc(c.sourceUrl || c.usptoUrl || 'https://patents.google.com/');
      return `<div class="pat-accel-card">
        <div class="pat-accel-rank">#${i + 1}</div>
        <div class="pat-accel-name">${esc(c.company)}</div>
        <div class="pat-accel-sector" style="color:${sector.color};">${esc(sector.label)}</div>
        <div class="pat-accel-metric">
          <div class="pat-accel-num">+${c.accelPct.toFixed(0)}%</div>
          <div class="pat-accel-lbl">vs trailing 4Q avg</div>
        </div>
        <div class="pat-accel-detail">
          Latest quarter (<strong>${esc(c.latestQuarter)}</strong>): <strong style="color:#fff;">${c.latest}</strong> filings<br>
          Trailing 4Q avg: <strong style="color:rgba(255,255,255,0.75);">${c.prior4Avg.toFixed(1)}</strong>
          <a href="${source}" target="_blank" rel="noopener" class="pat-accel-link">Verify on USPTO →</a>
        </div>
      </div>`;
    }).join('');
  }

  // ── Scanner filter pills + state ───────────────────────────────
  function renderScannerControls(velocityData) {
    const pillWrap = document.getElementById('pat-scanner-sector-pills');
    if (!pillWrap) return;
    const sectors = Array.from(new Set((velocityData || []).map(r => r.sector).filter(Boolean))).sort();
    pillWrap.innerHTML = sectors.map(s => {
      const lbl = sectorStyle(s).label;
      return `<button class="pat-scanner-sector-btn" data-sector="${esc(s)}">${esc(lbl)}</button>`;
    }).join('');

    pillWrap.addEventListener('click', (e) => {
      const btn = e.target.closest('.pat-scanner-sector-btn');
      if (!btn) return;
      const sector = btn.getAttribute('data-sector') || '';
      _filterState.sector = (_filterState.sector === sector) ? '' : sector;
      Array.from(pillWrap.querySelectorAll('.pat-scanner-sector-btn')).forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-sector') === _filterState.sector);
      });
      applyFilters();
    });

    const searchEl = document.getElementById('pat-scanner-search');
    if (searchEl) {
      searchEl.addEventListener('input', (e) => {
        _filterState.search = (e.target.value || '').toLowerCase().trim();
        applyFilters();
      });
    }
    const trendEl = document.getElementById('pat-scanner-trend');
    if (trendEl) {
      trendEl.addEventListener('change', (e) => {
        _filterState.trend = e.target.value || '';
        applyFilters();
      });
    }
  }

  function applyFilters() {
    const filtered = _velocityData.filter(r => {
      if (_filterState.sector && r.sector !== _filterState.sector) return false;
      if (_filterState.trend && r.trend !== _filterState.trend) return false;
      if (_filterState.search) {
        const name = (r.company || '').toLowerCase();
        if (!name.includes(_filterState.search)) return false;
      }
      return true;
    });
    renderVelocityLeaderboard(filtered, /*alreadyFiltered*/ true);
  }

  // ── Compare Mode: overlay 2-4 companies' 8Q sparklines ─────────
  const COMPARE_COLORS = ['#8b5cf6', '#22c55e', '#f59e0b', '#06b6d4'];

  function renderCompareControls(velocityData) {
    const sel = document.getElementById('pat-compare-select');
    const chart = document.getElementById('pat-compare-chart');
    if (!sel || !chart) return;
    const sorted = [...velocityData].sort((a, b) => (a.company || '').localeCompare(b.company || ''));
    sel.innerHTML = sorted.map(r => `<option value="${esc(r.company)}">${esc(r.company)}</option>`).join('');

    chart.className = 'pat-compare-chart';
    chart.innerHTML = '<div class="pat-compare-empty">Select 2&ndash;4 companies above to overlay their 8-quarter trajectories.</div>';

    sel.addEventListener('change', () => {
      const picked = Array.from(sel.selectedOptions).map(o => o.value).slice(0, 4);
      if (picked.length < 2) {
        chart.innerHTML = '<div class="pat-compare-empty">Select 2&ndash;4 companies above to overlay their 8-quarter trajectories.</div>';
        return;
      }
      const series = picked.map(name => velocityData.find(r => r.company === name)).filter(Boolean);
      renderCompareChart(series);
    });
  }

  function renderCompareChart(series) {
    const chart = document.getElementById('pat-compare-chart');
    if (!chart || series.length === 0) return;

    // Collect all quarters in order
    const allQs = Array.from(new Set(series.flatMap(s => (s.quarters || []).map(q => q.quarter)))).sort();
    if (allQs.length < 2) {
      chart.innerHTML = '<div class="pat-compare-empty">Not enough quarterly data to compare.</div>';
      return;
    }

    // Find max filings across all selected for y-axis
    let maxF = 0;
    series.forEach(s => (s.quarters || []).forEach(q => { if (q.filings > maxF) maxF = q.filings; }));
    if (maxF === 0) maxF = 1;

    const W = 600, H = 220, padL = 40, padR = 16, padT = 16, padB = 36;
    const innerW = W - padL - padR;
    const innerH = H - padT - padB;
    const stepX = innerW / (allQs.length - 1);

    // Build polylines per series
    const polylines = series.map((s, i) => {
      const color = COMPARE_COLORS[i % COMPARE_COLORS.length];
      const qMap = {};
      (s.quarters || []).forEach(q => { qMap[q.quarter] = q.filings; });
      const pts = allQs.map((q, idx) => {
        const v = qMap[q];
        if (v == null) return null;
        const x = padL + idx * stepX;
        const y = padT + innerH - (v / maxF) * innerH;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).filter(p => p !== null);
      const dots = allQs.map((q, idx) => {
        const v = qMap[q];
        if (v == null) return '';
        const x = padL + idx * stepX;
        const y = padT + innerH - (v / maxF) * innerH;
        return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="${color}"/>`;
      }).join('');
      return `<polyline points="${pts.join(' ')}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round"/>${dots}`;
    }).join('');

    // Y-axis ticks
    const yTicks = [0, Math.round(maxF / 2), maxF];
    const yLabels = yTicks.map(v => {
      const y = padT + innerH - (v / maxF) * innerH;
      return `<text x="${padL - 8}" y="${y + 3}" font-size="10" fill="rgba(255,255,255,0.4)" text-anchor="end" font-family="Space Grotesk, monospace">${v}</text>
              <line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="rgba(255,255,255,0.05)"/>`;
    }).join('');

    // X-axis quarter labels (show every 2nd if many)
    const xStep = allQs.length > 6 ? 2 : 1;
    const xLabels = allQs.map((q, idx) => {
      if (idx % xStep !== 0 && idx !== allQs.length - 1) return '';
      const x = padL + idx * stepX;
      return `<text x="${x}" y="${H - 16}" font-size="10" fill="rgba(255,255,255,0.5)" text-anchor="middle" font-family="Space Grotesk, monospace">${q}</text>`;
    }).join('');

    const legend = series.map((s, i) => {
      const color = COMPARE_COLORS[i % COMPARE_COLORS.length];
      return `<div class="pat-compare-legend-item">
        <div class="pat-compare-swatch" style="background:${color};"></div>
        <span style="color:#fff; font-weight:600;">${esc(s.company)}</span>
        <span style="color:rgba(255,255,255,0.5);">· ${s.qoqChange || 'flat'}</span>
      </div>`;
    }).join('');

    chart.innerHTML = `<div class="pat-compare-legend">${legend}</div>
      <svg width="100%" viewBox="0 0 ${W} ${H}" style="display:block; max-width:800px; margin:0 auto;">
        ${yLabels}
        ${polylines}
        ${xLabels}
        <text x="${padL - 28}" y="${padT - 4}" font-size="9" fill="rgba(255,255,255,0.4)" font-family="Space Grotesk, monospace">filings</text>
      </svg>
      <div style="text-align:center; margin-top:12px; font-size:11px; color:rgba(255,255,255,0.4);">8-quarter trajectory · USPTO PatentsView authoritative data</div>`;
  }

  // ── Velocity leaderboard (filtered or top 30) ─────────────────
  function renderVelocityLeaderboard(velocityData, alreadyFiltered) {
    const grid = document.getElementById('patent-velocity-grid');
    if (!grid) return;

    if (!velocityData || velocityData.length === 0) {
      grid.innerHTML = '<div style="padding:40px; text-align:center; color:rgba(255,255,255,0.4);">No companies match the current filters.</div>';
      return;
    }

    const top = alreadyFiltered ? velocityData : velocityData.slice(0, 30);

    const rowsHtml = top.map((r, i) => {
      const trend = TREND_STYLES[r.trend] || TREND_STYLES.steady;
      const sector = sectorStyle(r.sector);
      const filings = (r.quarters || []).map(q => q.filings);
      const spark = sparkline(filings, { color: trend.color, width: 110, height: 28 });
      const qoqColor = (r.qoqChangeNum || 0) >= 0 ? '#22c55e' : '#ef4444';
      const source = esc(r.sourceUrl || 'https://patents.google.com/');
      return `<tr data-company="${esc(r.company)}">
        <td style="font-weight:700; color:var(--accent); font-family:'Space Grotesk',monospace;">#${i + 1}</td>
        <td style="font-weight:600;">${esc(r.company)}</td>
        <td><span class="pat-sector-pill" style="background:${sector.color}1a; color:${sector.color}; border:1px solid ${sector.color}55;">${esc(sector.label)}</span></td>
        <td style="font-family:'Space Grotesk',monospace; text-align:right;">${esc(r.patentCount)}</td>
        <td style="text-align:right; font-family:'Space Grotesk',monospace; color:${qoqColor}; font-weight:600;">${r.qoqChange ? esc(r.qoqChange) : '<span style="color:rgba(255,255,255,0.3); font-weight:400;">flat</span>'}</td>
        <td>${spark}</td>
        <td style="font-size:11px; color:${trend.color};"><span style="display:inline-block; margin-right:6px;">${trend.icon}</span>${esc(trend.label)}</td>
        <td><a href="${source}" target="_blank" rel="noopener" style="color:var(--accent); text-decoration:none; font-size:11px;">Verify →</a></td>
      </tr>`;
    }).join('');

    grid.innerHTML = `<div class="pat-table-wrap">
      <table class="pat-leaderboard-table">
        <thead>
          <tr>
            <th style="width:44px;">#</th>
            <th>Company</th>
            <th>Sector</th>
            <th style="text-align:right;">Total</th>
            <th style="text-align:right;">QoQ Δ</th>
            <th>8Q Trend</th>
            <th>Signal</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    </div>`;
  }

  // ── Sector breakdown cards ─────────────────────────────────────
  function renderSectorBreakdown(intelData) {
    const wrap = document.getElementById('patent-sector-grid');
    if (!wrap) return;

    if (!intelData || intelData.length === 0) {
      wrap.innerHTML = '';
      return;
    }

    const bySector = {};
    intelData.forEach(r => {
      const s = r.sector || 'other';
      if (!bySector[s]) bySector[s] = { companies: [], total: 0 };
      bySector[s].companies.push(r);
      bySector[s].total += (r.patentCount || 0);
    });

    const sectors = Object.keys(bySector).map(s => ({
      sector: s,
      style: sectorStyle(s),
      total: bySector[s].total,
      companies: bySector[s].companies.sort((a, b) => (b.patentCount || 0) - (a.patentCount || 0)),
    })).sort((a, b) => b.total - a.total);

    wrap.innerHTML = sectors.map(s => {
      const topThree = s.companies.slice(0, 3);
      return `<div class="pat-sector-card" style="border-left: 3px solid ${s.style.color};">
        <div class="pat-sector-head">
          <div class="pat-sector-name" style="color:${s.style.color};">${esc(s.style.label)}</div>
          <div class="pat-sector-total">${esc(s.total.toLocaleString())}</div>
        </div>
        <div class="pat-sector-companies">${s.companies.length} companies</div>
        <ul class="pat-sector-leaders">
          ${topThree.map(c => `<li>
            <span class="pat-sector-leader-name">${esc(c.company)}</span>
            <span class="pat-sector-leader-count">${esc((c.patentCount || 0).toLocaleString())}</span>
          </li>`).join('')}
        </ul>
      </div>`;
    }).join('');
  }

  // ── Per-company expandable cards ───────────────────────────────
  function renderCompanyCards(intelData) {
    const grid = document.getElementById('patent-company-grid');
    if (!grid) return;

    if (!intelData || intelData.length === 0) {
      grid.innerHTML = '<div style="padding:40px; text-align:center; color:rgba(255,255,255,0.4);">No company data available.</div>';
      return;
    }

    const sorted = [...intelData].sort((a, b) => (b.patentCount || 0) - (a.patentCount || 0));

    grid.innerHTML = sorted.map((r) => {
      const trend = TREND_STYLES[r.trend] || TREND_STYLES.steady;
      const sector = sectorStyle(r.sector);
      const spark = sparkline((r.quarters || []).map(q => q.filings), { color: trend.color, width: 160, height: 36 });
      const qoqColor = (r.qoqChangeNum || 0) >= 0 ? '#22c55e' : '#ef4444';
      const keyPatents = r.keyPatents || [];
      const techAreas = (r.technologyAreas || []).slice(0, 4);

      return `<div class="pat-company-card" data-company="${esc(r.company)}">
        <div class="pat-company-head">
          <div>
            <div class="pat-company-name">${esc(r.company)}</div>
            <span class="pat-sector-pill" style="background:${sector.color}1a; color:${sector.color}; border:1px solid ${sector.color}55;">${esc(sector.label)}</span>
          </div>
          <div class="pat-company-count">
            <div class="pat-company-count-num">${esc((r.patentCount || 0).toLocaleString())}</div>
            <div class="pat-company-count-label">patents</div>
          </div>
        </div>

        <div class="pat-company-stats">
          <div class="pat-stat">
            <div class="pat-stat-label">QoQ Δ</div>
            <div class="pat-stat-val" style="color:${r.qoqChange ? qoqColor : 'rgba(255,255,255,0.4)'};">${r.qoqChange ? esc(r.qoqChange) : 'flat'}</div>
          </div>
          <div class="pat-stat">
            <div class="pat-stat-label">Trend</div>
            <div class="pat-stat-val" style="color:${trend.color};">${trend.icon} ${esc(trend.label)}</div>
          </div>
          <div class="pat-stat">
            <div class="pat-stat-label">Recent Filings</div>
            <div class="pat-stat-val">${esc((r.recentPatents || 0).toLocaleString())}</div>
          </div>
        </div>

        <div class="pat-company-spark">${spark}</div>

        <div class="pat-company-areas">
          ${techAreas.map(t => `<span class="pat-area-chip">${esc(t)}</span>`).join('')}
        </div>

        ${keyPatents.length ? `<details class="pat-company-details">
          <summary>Key patents (${keyPatents.length})</summary>
          <ul class="pat-keypatent-list">
            ${keyPatents.map(p => `<li>
              ${p.number ? `<span class="pat-kp-number">${esc(p.number)}</span>` : ''}
              ${p.title ? `<span class="pat-kp-title">${esc(p.title)}</span>` : ''}
              ${p.date ? `<span class="pat-kp-date">${esc(p.date)}</span>` : ''}
            </li>`).join('')}
          </ul>
        </details>` : ''}

        <div class="pat-company-links">
          <a href="${esc(r.sourceUrl || '#')}" target="_blank" rel="noopener" class="pat-link">Google Patents →</a>
          ${r.usptoUrl ? `<a href="${esc(r.usptoUrl)}" target="_blank" rel="noopener" class="pat-link">USPTO official →</a>` : ''}
        </div>
      </div>`;
    }).join('');
  }

  // ── Summary stats strip ────────────────────────────────────────
  function renderSummaryStats(intelData) {
    const el = document.getElementById('patent-summary-stats');
    if (!el) return;
    if (!intelData || intelData.length === 0) {
      el.innerHTML = '';
      return;
    }
    const total = intelData.reduce((s, r) => s + (r.patentCount || 0), 0);
    const accelerating = intelData.filter(r => r.trend === 'accelerating').length;
    const sectors = new Set(intelData.map(r => r.sector).filter(Boolean)).size;
    const recentTotal = intelData.reduce((s, r) => s + (r.recentPatents || 0), 0);

    el.innerHTML = `
      <div class="pat-stat-block"><div class="pat-stat-block-num">${total.toLocaleString()}</div><div class="pat-stat-block-lbl">Total patents tracked</div></div>
      <div class="pat-stat-block"><div class="pat-stat-block-num">${intelData.length}</div><div class="pat-stat-block-lbl">Companies</div></div>
      <div class="pat-stat-block"><div class="pat-stat-block-num">${sectors}</div><div class="pat-stat-block-lbl">Sectors covered</div></div>
      <div class="pat-stat-block"><div class="pat-stat-block-num" style="color:#22c55e;">${accelerating}</div><div class="pat-stat-block-lbl">Accelerating</div></div>
      <div class="pat-stat-block"><div class="pat-stat-block-num">${recentTotal.toLocaleString()}</div><div class="pat-stat-block-lbl">Last 4Q filings</div></div>
    `;
  }

  // ── Bootstrap ──────────────────────────────────────────────────
  function bootstrap() {
    const intel = (typeof PATENT_INTEL_AUTO !== 'undefined' && Array.isArray(PATENT_INTEL_AUTO))
      ? PATENT_INTEL_AUTO : [];

    // Hide the "in progress" placeholder if we have any data
    const note = document.getElementById('patent-velocity-note');
    if (note && intel.length > 0) note.style.display = 'none';

    renderSummaryStats(intel);
    renderSectorBreakdown(intel);
    renderCompanyCards(intel);

    // Velocity: try fetching live; fall back to PATENT_INTEL_AUTO sorted by qoq
    const velocityPath = 'data/patent_velocity_auto.json?v=' + (new Date().toISOString().slice(0, 10));
    fetch(velocityPath)
      .then(r => r.ok ? r.json() : Promise.reject('fetch failed'))
      .then(v => initVelocityViews(v))
      .catch(() => {
        // Fallback: derive velocity view from PATENT_INTEL_AUTO
        const derived = [...intel].sort((a, b) => (b.qoqChangeNum || 0) - (a.qoqChangeNum || 0));
        initVelocityViews(derived);
      });
  }

  // Boot all velocity-driven views once data is in hand
  function initVelocityViews(velocityData) {
    _velocityData = (velocityData || []).slice().sort((a, b) => (b.qoqChangeNum || 0) - (a.qoqChangeNum || 0));
    renderAccelerationAlerts(_velocityData);
    renderScannerControls(_velocityData);
    renderVelocityLeaderboard(_velocityData);
    renderCompareControls(_velocityData);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})();
