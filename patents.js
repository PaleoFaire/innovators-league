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

  // ── Velocity leaderboard (top 30 by QoQ change) ─────────────────
  function renderVelocityLeaderboard(velocityData) {
    const grid = document.getElementById('patent-velocity-grid');
    if (!grid) return;

    if (!velocityData || velocityData.length === 0) {
      grid.innerHTML = '<div style="padding:40px; text-align:center; color:rgba(255,255,255,0.4);">No velocity data available.</div>';
      return;
    }

    const top = velocityData.slice(0, 30);

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
      .then(v => renderVelocityLeaderboard(v))
      .catch(() => {
        // Fallback: derive velocity view from PATENT_INTEL_AUTO
        const derived = [...intel].sort((a, b) => (b.qoqChangeNum || 0) - (a.qoqChangeNum || 0));
        renderVelocityLeaderboard(derived);
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})();
