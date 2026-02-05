// ─── COUNTRY MAPPING ───
// US state codes
const US_STATES = new Set([
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID',
  'IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS',
  'MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK',
  'OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC'
]);

// Unambiguous international codes (no US state conflict)
const INTL_CODES = {
  'UK': 'United Kingdom', 'GB': 'United Kingdom',
  'FR': 'France', 'SE': 'Sweden', 'FI': 'Finland',
  'CH': 'Switzerland', 'DK': 'Denmark', 'NO': 'Norway', 'NL': 'Netherlands',
  'ES': 'Spain', 'IT': 'Italy', 'EE': 'Estonia', 'PL': 'Poland',
  'JP': 'Japan', 'KR': 'South Korea',
  'AU': 'Australia', 'SG': 'Singapore',
  'NZ': 'New Zealand', 'ZA': 'South Africa', 'BR': 'Brazil',
  'IE': 'Ireland', 'CA-CAN': 'Canada',
  'PT': 'Portugal', 'CZ': 'Czech Republic'
};

// Countries found in location strings — used to disambiguate shared codes
const LOCATION_COUNTRIES = {
  'Germany': 'Germany', 'Israel': 'Israel', 'India': 'India',
  'Argentina': 'Argentina', 'Ireland': 'Ireland'
};

function getCountry(stateCode, location) {
  // Check unambiguous international codes first
  if (INTL_CODES[stateCode]) return INTL_CODES[stateCode];

  // For ambiguous codes (DE, IL, IN, AR, GA), use the location string
  if (location) {
    for (const [keyword, country] of Object.entries(LOCATION_COUNTRIES)) {
      if (location.includes(keyword)) return country;
    }
  }

  // Default: US state
  return 'United States';
}

// ─── SIGNAL HELPERS ───
const SIGNAL_CONFIG = {
  hot:         { label: 'HOT', icon: '🔥', class: 'signal-hot' },
  rising:      { label: 'RISING', icon: '⚡', class: 'signal-rising' },
  stealth:     { label: 'STEALTH', icon: '👀', class: 'signal-stealth' },
  watch:       { label: 'WATCH', icon: '🔭', class: 'signal-watch' },
  established: { label: 'EST.', icon: '✓', class: 'signal-established' }
};

const SIGNAL_PRIORITY = { hot: 0, rising: 1, stealth: 2, watch: 3, established: 4 };

function renderSignalBadge(signal) {
  if (!signal || !SIGNAL_CONFIG[signal]) return '';
  const s = SIGNAL_CONFIG[signal];
  return `<span class="signal-badge ${s.class}">${s.icon} ${s.label}</span>`;
}

// ─── INNOVATION SCORE ───
function getAverageScore(scores) {
  if (!scores) return 0;
  const vals = [scores.team, scores.traction, scores.techMoat, scores.market, scores.momentum].filter(v => v != null);
  return vals.length ? (vals.reduce((sum, v) => sum + v, 0) / vals.length) : 0;
}

function renderScoreBadge(scores) {
  if (!scores) return '';
  const avg = getAverageScore(scores);
  if (avg === 0) return '';
  const cls = avg >= 8 ? 'high' : avg >= 6 ? 'mid' : 'low';
  return `<span class="score-badge ${cls}">★ ${avg.toFixed(1)}</span>`;
}

// ─── INVESTMENT THESIS ───
function renderThesis(thesis) {
  if (!thesis) return '';
  return `
    <div class="thesis-section">
      <h4>Investment Thesis</h4>
      ${thesis.bull ? `
        <div class="thesis-item thesis-bull">
          <div class="thesis-label">Bull Case</div>
          ${thesis.bull}
        </div>
      ` : ''}
      ${thesis.bear ? `
        <div class="thesis-item thesis-bear">
          <div class="thesis-label">Bear Case</div>
          ${thesis.bear}
        </div>
      ` : ''}
      ${thesis.risks && thesis.risks.length > 0 ? `
        <div class="thesis-risks">
          <h5>Key Risks</h5>
          ${thesis.risks.map(r => `<div class="thesis-risk-item">${r}</div>`).join('')}
        </div>
      ` : ''}
    </div>
  `;
}

// ─── DUE DILIGENCE ONE-PAGER ───
function generateOnePager(companyName) {
  const company = COMPANIES.find(c => c.name === companyName);
  if (!company) return;

  const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };
  const country = getCountry(company.state, company.location);
  const avg = getAverageScore(company.scores);

  // Find VCs backing this company
  const backers = (typeof VC_FIRMS !== 'undefined' ? VC_FIRMS : [])
    .filter(f => f.portfolioCompanies.includes(company.name))
    .map(f => f.shortName);

  const competitors = (company.competitors || [])
    .map(name => COMPANIES.find(c => c.name === name))
    .filter(Boolean);

  const w = window.open('', '_blank');
  w.document.write(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>${company.name} — Due Diligence One-Pager | Innovators League</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, sans-serif; background: #000; color: #f0f0fa; padding: 40px; max-width: 900px; margin: 0 auto; line-height: 1.6; }
        .header { border-bottom: 2px solid #FF6B2C; padding-bottom: 20px; margin-bottom: 28px; }
        .header h1 { font-size: 28px; margin-bottom: 4px; }
        .header .subtitle { color: rgba(240,240,250,0.5); font-size: 13px; }
        .sector-tag { display: inline-block; background: rgba(255,107,44,0.12); color: #FF6B2C; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; margin-bottom: 12px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
        .stat-box { background: #0a0a0a; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 16px; }
        .stat-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: rgba(240,240,250,0.4); margin-bottom: 4px; }
        .stat-value { font-size: 18px; font-weight: 600; }
        .section { margin: 24px 0; }
        .section h3 { font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #FF6B2C; margin-bottom: 10px; }
        .section p { color: rgba(240,240,250,0.7); font-size: 14px; }
        .insight-box { background: #0a0a0a; border-left: 3px solid #FF6B2C; padding: 16px; border-radius: 0 8px 8px 0; margin: 12px 0; font-style: italic; color: rgba(240,240,250,0.7); font-size: 14px; }
        .tags { display: flex; flex-wrap: wrap; gap: 6px; }
        .tag { background: #111; border: 1px solid rgba(255,255,255,0.08); padding: 4px 10px; border-radius: 6px; font-size: 12px; color: rgba(240,240,250,0.6); }
        .bull { background: rgba(34,197,94,0.06); border-left: 3px solid #22C55E; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; font-size: 13px; color: rgba(240,240,250,0.7); }
        .bear { background: rgba(239,68,68,0.06); border-left: 3px solid #EF4444; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; font-size: 13px; color: rgba(240,240,250,0.7); }
        .bull-label { color: #22C55E; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }
        .bear-label { color: #EF4444; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }
        .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.08); text-align: center; color: rgba(240,240,250,0.3); font-size: 12px; }
        .score-row { display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }
        .score-item { background: #0a0a0a; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px 16px; text-align: center; }
        .score-num { font-size: 20px; font-weight: 700; color: #22C55E; }
        .score-lbl { font-size: 10px; text-transform: uppercase; letter-spacing: 0.3px; color: rgba(240,240,250,0.4); margin-top: 2px; }
        @media print {
          body { background: #fff; color: #000; padding: 20px; }
          .stat-box, .insight-box, .bull, .bear, .score-item { background: #f5f5f5; border-color: #ddd; }
          .section h3 { color: #333; }
          .stat-label, .section p, .insight-box, .bull, .bear { color: #333; }
          .header { border-color: #333; }
          .score-num { color: #22C55E; }
          .tag { background: #eee; border-color: #ccc; color: #333; }
        }
      </style>
    </head>
    <body>
      <div class="header">
        <div class="sector-tag">${sectorInfo.icon} ${company.sector}</div>
        <h1>${company.name}</h1>
        <div class="subtitle">Due Diligence One-Pager · Generated ${new Date().toLocaleDateString()} · Innovators League by ROS</div>
      </div>

      <div class="grid">
        <div class="stat-box"><div class="stat-label">Location</div><div class="stat-value">${company.location} · ${country}</div></div>
        <div class="stat-box"><div class="stat-label">Stage</div><div class="stat-value">${company.fundingStage || 'N/A'}</div></div>
        <div class="stat-box"><div class="stat-label">Total Raised</div><div class="stat-value">${company.totalRaised || 'N/A'}</div></div>
        <div class="stat-box"><div class="stat-label">Valuation</div><div class="stat-value">${company.valuation || 'N/A'}</div></div>
        ${company.founder ? `<div class="stat-box"><div class="stat-label">Founder(s)</div><div class="stat-value">${company.founder}</div></div>` : ''}
        ${avg > 0 ? `<div class="stat-box"><div class="stat-label">Innovation Score</div><div class="stat-value" style="color:#22C55E">${avg.toFixed(1)} / 10</div></div>` : ''}
      </div>

      ${company.scores ? `
        <div class="section">
          <h3>Intelligence Scores</h3>
          <div class="score-row">
            <div class="score-item"><div class="score-num">${company.scores.team}</div><div class="score-lbl">Team</div></div>
            <div class="score-item"><div class="score-num">${company.scores.traction}</div><div class="score-lbl">Traction</div></div>
            <div class="score-item"><div class="score-num">${company.scores.techMoat}</div><div class="score-lbl">Tech Moat</div></div>
            <div class="score-item"><div class="score-num">${company.scores.market}</div><div class="score-lbl">Market</div></div>
            <div class="score-item"><div class="score-num">${company.scores.momentum}</div><div class="score-lbl">Momentum</div></div>
          </div>
        </div>
      ` : ''}

      <div class="section">
        <h3>Overview</h3>
        <p>${company.description}</p>
      </div>

      ${company.insight ? `
        <div class="section">
          <h3>Analyst View</h3>
          <div class="insight-box">${company.insight}</div>
        </div>
      ` : ''}

      ${company.thesis ? `
        <div class="section">
          <h3>Investment Thesis</h3>
          ${company.thesis.bull ? `<div class="bull"><div class="bull-label">Bull Case</div>${company.thesis.bull}</div>` : ''}
          ${company.thesis.bear ? `<div class="bear"><div class="bear-label">Bear Case</div>${company.thesis.bear}</div>` : ''}
          ${company.thesis.risks ? `<div style="margin-top:12px"><div style="color:#F59E0B;font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:6px">Key Risks</div>${company.thesis.risks.map(r => `<div style="font-size:13px;color:rgba(240,240,250,0.6);padding:3px 0;">⚠ ${r}</div>`).join('')}</div>` : ''}
        </div>
      ` : ''}

      ${backers.length > 0 ? `
        <div class="section">
          <h3>VC Backers</h3>
          <div class="tags">${backers.map(b => `<span class="tag">${b}</span>`).join('')}</div>
        </div>
      ` : ''}

      ${competitors.length > 0 ? `
        <div class="section">
          <h3>Competitive Landscape</h3>
          <div class="tags">${competitors.map(c => `<span class="tag">${c.name}</span>`).join('')}</div>
        </div>
      ` : ''}

      <div class="section">
        <h3>Tags</h3>
        <div class="tags">${company.tags.map(t => `<span class="tag">${t}</span>`).join('')}</div>
      </div>

      <div class="footer">
        <p>The Innovators League by Rational Optimist Society · rationaloptimistsociety.com</p>
        <p style="margin-top:4px">This report is for informational purposes only and does not constitute investment advice.</p>
      </div>
    </body>
    </html>
  `);
  w.document.close();
}

// ─── RADAR CHART ───
function renderRadarChart(scores) {
  if (!scores) return '';
  const labels = ['Team', 'Traction', 'Tech Moat', 'Market', 'Momentum'];
  const keys = ['team', 'traction', 'techMoat', 'market', 'momentum'];
  const size = 280;
  const cx = size / 2;
  const cy = size / 2;
  const maxR = 100;
  const levels = [0.25, 0.5, 0.75, 1.0];

  function polarToCart(angle, radius) {
    const a = (angle - 90) * Math.PI / 180;
    return [cx + radius * Math.cos(a), cy + radius * Math.sin(a)];
  }

  const angleStep = 360 / 5;

  // Grid polygons
  let gridSvg = '';
  levels.forEach(level => {
    const points = [];
    for (let i = 0; i < 5; i++) {
      const [x, y] = polarToCart(i * angleStep, maxR * level);
      points.push(`${x},${y}`);
    }
    gridSvg += `<polygon points="${points.join(' ')}" class="radar-grid"/>`;
  });

  // Axis lines
  let axisSvg = '';
  for (let i = 0; i < 5; i++) {
    const [x, y] = polarToCart(i * angleStep, maxR);
    axisSvg += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" class="radar-axis"/>`;
  }

  // Data polygon
  const dataPoints = [];
  for (let i = 0; i < 5; i++) {
    const val = (scores[keys[i]] || 0) / 10;
    const [x, y] = polarToCart(i * angleStep, maxR * val);
    dataPoints.push(`${x},${y}`);
  }

  // Labels
  let labelsSvg = '';
  for (let i = 0; i < 5; i++) {
    const [x, y] = polarToCart(i * angleStep, maxR + 22);
    const val = scores[keys[i]] || 0;
    labelsSvg += `<text x="${x}" y="${y}" text-anchor="middle" dominant-baseline="middle" class="radar-label">${labels[i]}</text>`;
    const [sx, sy] = polarToCart(i * angleStep, maxR * (val / 10) + 12);
    labelsSvg += `<text x="${sx}" y="${sy}" text-anchor="middle" dominant-baseline="middle" class="radar-score">${val}</text>`;
  }

  return `
    <div class="radar-chart-container">
      <div>
        <h4>Intelligence Scores</h4>
        <div class="radar-chart">
          <svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
            ${gridSvg}
            ${axisSvg}
            <polygon points="${dataPoints.join(' ')}" class="radar-data"/>
            ${labelsSvg}
          </svg>
        </div>
      </div>
    </div>
  `;
}

// ─── BOOKMARKS ───
let bookmarks = JSON.parse(localStorage.getItem('til-bookmarks') || '[]');

function isBookmarked(name) {
  return bookmarks.includes(name);
}

function toggleBookmark(name) {
  if (isBookmarked(name)) {
    bookmarks = bookmarks.filter(b => b !== name);
  } else {
    bookmarks.push(name);
  }
  localStorage.setItem('til-bookmarks', JSON.stringify(bookmarks));
}

// ─── COMPARE ───
let compareList = [];
const MAX_COMPARE = 3;

function toggleCompare(name) {
  const idx = compareList.indexOf(name);
  if (idx > -1) {
    compareList.splice(idx, 1);
  } else if (compareList.length < MAX_COMPARE) {
    compareList.push(name);
  }
  updateCompareBar();
  // Re-render to update card states
  applyFilters();
}

function updateCompareBar() {
  const bar = document.getElementById('compare-bar');
  const items = document.getElementById('compare-items');

  if (compareList.length === 0) {
    bar.classList.remove('visible');
    return;
  }

  bar.classList.add('visible');
  items.innerHTML = compareList.map(name => {
    const c = COMPANIES.find(co => co.name === name);
    if (!c) return '';
    const sectorInfo = SECTORS[c.sector] || { color: '#6b7280', icon: '' };
    return `<div class="compare-item">
      <span style="color:${sectorInfo.color}">${sectorInfo.icon}</span> ${name}
      <button onclick="toggleCompare('${name.replace(/'/g, "\\'")}')" class="compare-remove">&times;</button>
    </div>`;
  }).join('');
}

function showComparison() {
  if (compareList.length < 2) return;

  const companies = compareList.map(name => COMPANIES.find(c => c.name === name)).filter(Boolean);
  const body = document.getElementById('modal-body');

  body.innerHTML = `
    <h2 style="margin-bottom: 24px; color: var(--accent);">Company Comparison</h2>
    <div style="display: grid; grid-template-columns: repeat(${companies.length}, 1fr); gap: 20px;">
      ${companies.map(c => {
        const si = SECTORS[c.sector] || { color: '#6b7280', icon: '' };
        return `<div style="padding: 20px; background: var(--bg-tertiary); border-radius: 12px; border: 1px solid var(--border);">
          <div style="font-size: 12px; color: ${si.color}; margin-bottom: 8px;">${si.icon} ${c.sector}</div>
          <h3 style="margin-bottom: 4px;">${c.name}</h3>
          ${c.founder ? `<p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 12px;">${c.founder}</p>` : ''}
          <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 16px;">${c.location}</p>
          <div class="modal-stats">
            ${c.fundingStage ? `<div class="modal-stat"><span class="modal-stat-label">Stage</span><span class="modal-stat-value">${c.fundingStage}</span></div>` : ''}
            ${c.totalRaised ? `<div class="modal-stat"><span class="modal-stat-label">Raised</span><span class="modal-stat-value">${c.totalRaised}</span></div>` : ''}
            ${c.valuation ? `<div class="modal-stat"><span class="modal-stat-label">Valuation</span><span class="modal-stat-value">${c.valuation}</span></div>` : ''}
          </div>
          <p style="color: var(--text-secondary); font-size: 13px; line-height: 1.6; margin-top: 12px;">${c.description.substring(0, 200)}${c.description.length > 200 ? '...' : ''}</p>
        </div>`;
      }).join('')}
    </div>
  `;

  openModal();
}

// ─── MODAL ───
function openModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.remove('active');
  document.body.style.overflow = '';
}

function openCompanyModal(companyName) {
  const company = COMPANIES.find(c => c.name === companyName);
  if (!company) return;

  const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };
  const saved = isBookmarked(company.name);
  const country = getCountry(company.state, company.location);

  // Related companies (same sector, different company)
  const related = COMPANIES
    .filter(c => c.sector === company.sector && c.name !== company.name)
    .sort(() => Math.random() - 0.5)
    .slice(0, 4);

  // Competitors from data
  const competitors = (company.competitors || [])
    .map(name => COMPANIES.find(c => c.name === name))
    .filter(Boolean);

  const body = document.getElementById('modal-body');
  body.innerHTML = `
    <div class="modal-sector-badge" style="background:${sectorInfo.color}15; color:${sectorInfo.color}; border: 1px solid ${sectorInfo.color}30;">
      ${sectorInfo.icon} ${company.sector}
    </div>
    <h2 class="modal-company-name">${company.name} ${renderSignalBadge(company.signal)}</h2>
    ${company.founder ? `<p class="modal-founder">${company.founder}</p>` : ''}
    <p class="modal-location">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
      ${company.location} &middot; ${country}
    </p>

    <div class="modal-stats">
      ${company.fundingStage ? `<div class="modal-stat"><span class="modal-stat-label">Stage</span><span class="modal-stat-value">${company.fundingStage}</span></div>` : ''}
      ${company.totalRaised ? `<div class="modal-stat"><span class="modal-stat-label">Raised</span><span class="modal-stat-value">${company.totalRaised}</span></div>` : ''}
      ${company.valuation ? `<div class="modal-stat"><span class="modal-stat-label">Valuation</span><span class="modal-stat-value">${company.valuation}</span></div>` : ''}
    </div>

    ${company.insight ? `
      <div class="modal-insight">
        <div class="modal-insight-label">ROS Intelligence</div>
        ${company.insight}
      </div>
    ` : ''}

    ${renderRadarChart(company.scores)}

    ${renderThesis(company.thesis)}

    <p class="modal-description">${company.description}</p>

    <div class="modal-tags">
      ${company.tags.map(t => `<span class="tag">${t}</span>`).join('')}
    </div>

    ${(() => {
      const backers = (typeof VC_FIRMS !== 'undefined' ? VC_FIRMS : [])
        .filter(f => f.portfolioCompanies.includes(company.name))
        .map(f => f.shortName);
      return backers.length > 0 ? `
        <div class="modal-competitors" style="margin-top:16px;">
          <h4>VC Backers</h4>
          <div class="competitors-grid">
            ${backers.map(b => `<a href="investors.html" class="competitor-chip">${b}</a>`).join('')}
          </div>
        </div>
      ` : '';
    })()}

    ${!company.scores && !company.insight ? '<p class="assessment-pending">⏳ Full intelligence assessment pending</p>' : ''}

    <div class="modal-actions">
      ${company.rosLink ? `<a href="${company.rosLink}" target="_blank" rel="noopener" class="modal-action-btn primary">
        Read Coverage
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>
      </a>` : ''}
      <button class="modal-action-btn ${saved ? 'saved' : ''}" onclick="toggleBookmark('${company.name.replace(/'/g, "\\'")}'); openCompanyModal('${company.name.replace(/'/g, "\\'")}');">
        ${saved ? '★ Saved' : '☆ Save'}
      </button>
      <button class="modal-action-btn" onclick="shareCompany('${company.name.replace(/'/g, "\\'")}')">
        ↗ Share
      </button>
      <button class="modal-action-btn" onclick="generateOnePager('${company.name.replace(/'/g, "\\'")}')">
        📋 One-Pager
      </button>
    </div>

    ${competitors.length > 0 ? `
      <div class="modal-competitors">
        <h4>Competitive Landscape</h4>
        <div class="competitors-grid">
          ${competitors.map(r => `
            <span class="competitor-chip" onclick="openCompanyModal('${r.name.replace(/'/g, "\\'")}')">
              ${r.name}
            </span>
          `).join('')}
        </div>
      </div>
    ` : ''}

    ${related.length > 0 ? `
      <div class="modal-related">
        <h4>Related Companies</h4>
        <div class="modal-related-grid">
          ${related.map(r => `
            <div class="modal-related-card" onclick="openCompanyModal('${r.name.replace(/'/g, "\\'")}')">
              <span class="modal-related-name">${r.name}</span>
              <span class="modal-related-loc">${r.location}</span>
            </div>
          `).join('')}
        </div>
      </div>
    ` : ''}
  `;

  // Update URL
  const url = new URL(window.location);
  url.searchParams.set('company', company.name);
  window.history.pushState({}, '', url);

  openModal();
}

function shareCompany(companyName, btnEl) {
  const url = new URL(window.location.origin + window.location.pathname);
  url.searchParams.set('company', companyName);
  const shareUrl = url.toString();

  if (navigator.clipboard) {
    navigator.clipboard.writeText(shareUrl).then(() => {
      // Find the share button specifically
      const btns = document.querySelectorAll('.modal-actions .modal-action-btn');
      let btn = null;
      btns.forEach(b => { if (b.textContent.includes('Share') || b.textContent.includes('Copied')) btn = b; });
      if (btn) {
        const original = btn.innerHTML;
        btn.innerHTML = '✓ Copied!';
        setTimeout(() => { btn.innerHTML = original; }, 1500);
      }
    });
  } else {
    // Fallback: select text via prompt
    prompt('Copy this link:', shareUrl);
  }
}

// ─── APP INITIALIZATION ───
document.addEventListener('DOMContentLoaded', () => {
  initStats();
  initMap();
  initFilters();
  renderCompanies(COMPANIES);
  renderSectors();
  initSearch();
  initScrollAnimations();
  initMobileMenu();
  initModal();
  initCompare();
  initKeyboard();
  initFeatured();
  initMovementTracker();
  initWeeklyDigest();
  initLeaderboard();
  initTRLDashboard();
  initDealTracker();
  initGrowthSignals();
  initMarketMap();
  initNewsTicker();
  initMarketPulse();
  initFundingTracker();
  initSectorMomentum();
  initIPOPipeline();
  initURLState();
  initSmoothScroll();
  updateResultsCount(COMPANIES.length);
});

// ─── STATS COUNTER ───
function initStats() {
  const companyCount = COMPANIES.length;
  const sectorCount = Object.keys(SECTORS).length;
  const countries = new Set(COMPANIES.map(c => getCountry(c.state, c.location)));
  const countryCount = countries.size;

  // Calculate total tracked funding
  let totalFunding = 0;
  COMPANIES.forEach(c => {
    if (c.totalRaised) {
      const match = c.totalRaised.match(/([\d.]+)\s*(B|M|K)?/i);
      if (match) {
        let val = parseFloat(match[1]);
        const unit = (match[2] || '').toUpperCase();
        if (unit === 'B') val *= 1000;
        else if (unit === 'K') val *= 0.001;
        // M is the base unit
        totalFunding += val;
      }
    }
  });

  animateCounter('company-count', companyCount);
  animateCounter('sector-count', sectorCount);
  animateCounter('country-count', countryCount);

  // Format funding as $XXB+
  const fundingEl = document.getElementById('funding-count');
  if (fundingEl) {
    const fundingB = (totalFunding / 1000).toFixed(0);
    animateCounterWithPrefix('funding-count', parseInt(fundingB), '$', 'B+');
  }

  // Last updated
  const updatedEl = document.getElementById('last-updated');
  if (updatedEl && typeof LAST_UPDATED !== 'undefined') {
    updatedEl.textContent = `Last updated: ${LAST_UPDATED}`;
  }
}

function animateCounter(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const duration = 1200;
  const step = target / (duration / 16);

  function tick() {
    current += step;
    if (current >= target) {
      el.textContent = target;
      return;
    }
    el.textContent = Math.floor(current);
    requestAnimationFrame(tick);
  }

  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      tick();
      observer.disconnect();
    }
  });
  observer.observe(el);
}

function animateCounterWithPrefix(id, target, prefix, suffix) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const duration = 1200;
  const step = target / (duration / 16);

  function tick() {
    current += step;
    if (current >= target) {
      el.textContent = prefix + target + suffix;
      return;
    }
    el.textContent = prefix + Math.floor(current) + suffix;
    requestAnimationFrame(tick);
  }

  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      tick();
      observer.disconnect();
    }
  });
  observer.observe(el);
}

// ─── MAP ───
function initMap() {
  const map = L.map('innovators-map', {
    center: [25, 0],
    zoom: 2,
    minZoom: 2,
    maxZoom: 12,
    scrollWheelZoom: true,
    zoomControl: true
  });

  // Dark tile layer
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 19
  }).addTo(map);

  COMPANIES.forEach(company => {
    if (!company.lat || !company.lng) return;

    const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };

    const markerHtml = `<div class="custom-marker" style="background:${sectorInfo.color};">
      <span class="marker-icon">${sectorInfo.icon}</span>
    </div>`;

    const icon = L.divIcon({
      html: markerHtml,
      className: 'marker-container',
      iconSize: [28, 28],
      iconAnchor: [14, 14]
    });

    const marker = L.marker([company.lat, company.lng], { icon });

    const popupContent = `
      <div class="map-popup">
        <div class="popup-sector" style="color:${sectorInfo.color}">${sectorInfo.icon} ${company.sector}</div>
        <h3>${company.name}</h3>
        ${company.founder ? `<p class="popup-founder">${company.founder}</p>` : ''}
        <p class="popup-location">${company.location}</p>
        <p class="popup-desc">${company.description.substring(0, 140)}...</p>
        <button class="popup-link" onclick="openCompanyModal('${company.name.replace(/'/g, "\\'")}')">View Details &rarr;</button>
      </div>
    `;

    marker.bindPopup(popupContent, { maxWidth: 300 });
    marker.addTo(map);
  });
}

// ─── FILTERS ───
function initFilters() {
  // Sector chips
  const chipContainer = document.getElementById('filter-chips');
  const sectors = Object.keys(SECTORS);

  sectors.forEach(sector => {
    const chip = document.createElement('button');
    chip.className = 'chip';
    chip.dataset.sector = sector;
    chip.textContent = sector;
    chipContainer.appendChild(chip);
  });

  chipContainer.addEventListener('click', (e) => {
    if (!e.target.classList.contains('chip')) return;

    chipContainer.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    e.target.classList.add('active');

    // Sync dropdown
    const sectorFilter = document.getElementById('sector-filter');
    sectorFilter.value = e.target.dataset.sector;

    applyFilters();
  });

  // Sector dropdown
  const sectorFilter = document.getElementById('sector-filter');
  sectors.forEach(sector => {
    const opt = document.createElement('option');
    opt.value = sector;
    opt.textContent = sector;
    sectorFilter.appendChild(opt);
  });

  sectorFilter.addEventListener('change', () => {
    // Sync chips
    const chipContainer = document.getElementById('filter-chips');
    chipContainer.querySelectorAll('.chip').forEach(c => {
      c.classList.toggle('active', c.dataset.sector === sectorFilter.value);
    });
    applyFilters();
  });

  // Country dropdown
  const countryFilter = document.getElementById('country-filter');
  const countriesSet = new Set(COMPANIES.map(c => getCountry(c.state, c.location)));
  const countriesSorted = [...countriesSet].sort();
  countriesSorted.forEach(country => {
    const opt = document.createElement('option');
    opt.value = country;
    opt.textContent = country;
    countryFilter.appendChild(opt);
  });
  countryFilter.addEventListener('change', applyFilters);

  // Stage dropdown
  const stageFilter = document.getElementById('stage-filter');
  const stages = [...new Set(COMPANIES.map(c => c.fundingStage).filter(Boolean))].sort();
  stages.forEach(stage => {
    const opt = document.createElement('option');
    opt.value = stage;
    opt.textContent = stage;
    stageFilter.appendChild(opt);
  });
  stageFilter.addEventListener('change', applyFilters);

  // Sort dropdown
  document.getElementById('sort-filter').addEventListener('change', applyFilters);
}

function applyFilters() {
  const sector = document.getElementById('sector-filter').value;
  const country = document.getElementById('country-filter').value;
  const stage = document.getElementById('stage-filter').value;
  const sortBy = document.getElementById('sort-filter').value;
  const searchTerm = document.getElementById('search-input').value.toLowerCase();

  let filtered = COMPANIES;

  if (sector && sector !== 'all') {
    filtered = filtered.filter(c => c.sector === sector);
  }

  if (country && country !== 'all') {
    filtered = filtered.filter(c => getCountry(c.state, c.location) === country);
  }

  if (stage && stage !== 'all') {
    filtered = filtered.filter(c => c.fundingStage === stage);
  }

  if (searchTerm) {
    filtered = filtered.filter(c =>
      c.name.toLowerCase().includes(searchTerm) ||
      c.description.toLowerCase().includes(searchTerm) ||
      (c.founder && c.founder.toLowerCase().includes(searchTerm)) ||
      c.location.toLowerCase().includes(searchTerm) ||
      c.sector.toLowerCase().includes(searchTerm) ||
      c.tags.some(t => t.toLowerCase().includes(searchTerm)) ||
      getCountry(c.state, c.location).toLowerCase().includes(searchTerm)
    );
  }

  // Sort
  filtered = [...filtered];
  if (sortBy === 'name') {
    filtered.sort((a, b) => a.name.localeCompare(b.name));
  } else if (sortBy === 'name-desc') {
    filtered.sort((a, b) => b.name.localeCompare(a.name));
  } else if (sortBy === 'sector') {
    filtered.sort((a, b) => a.sector.localeCompare(b.sector) || a.name.localeCompare(b.name));
  } else if (sortBy === 'saved') {
    filtered.sort((a, b) => {
      const aS = isBookmarked(a.name) ? 0 : 1;
      const bS = isBookmarked(b.name) ? 0 : 1;
      return aS - bS || a.name.localeCompare(b.name);
    });
  } else if (sortBy === 'signal') {
    filtered.sort((a, b) => {
      const aP = a.signal ? (SIGNAL_PRIORITY[a.signal] ?? 99) : 99;
      const bP = b.signal ? (SIGNAL_PRIORITY[b.signal] ?? 99) : 99;
      return aP - bP || a.name.localeCompare(b.name);
    });
  } else if (sortBy === 'score') {
    filtered.sort((a, b) => {
      const avg = s => {
        if (!s) return 0;
        const vals = [s.team, s.traction, s.techMoat, s.market, s.momentum].filter(v => v != null);
        return vals.length ? vals.reduce((sum, v) => sum + v, 0) / vals.length : 0;
      };
      return avg(b.scores) - avg(a.scores) || a.name.localeCompare(b.name);
    });
  } else if (sortBy === 'recent') {
    filtered.sort((a, b) => {
      const dA = a.recentEvent ? a.recentEvent.date : '0000-00';
      const dB = b.recentEvent ? b.recentEvent.date : '0000-00';
      return dB.localeCompare(dA) || a.name.localeCompare(b.name);
    });
  }

  renderCompanies(filtered);
  updateResultsCount(filtered.length);

  // Update URL with filter state
  const url = new URL(window.location);
  if (sector && sector !== 'all') url.searchParams.set('sector', sector);
  else url.searchParams.delete('sector');
  if (country && country !== 'all') url.searchParams.set('country', country);
  else url.searchParams.delete('country');
  if (searchTerm) url.searchParams.set('q', searchTerm);
  else url.searchParams.delete('q');
  url.searchParams.delete('company');
  window.history.replaceState({}, '', url);

  const noResults = document.getElementById('no-results');
  noResults.style.display = filtered.length === 0 ? 'block' : 'none';
}

function updateResultsCount(count) {
  const el = document.getElementById('results-count');
  if (el) {
    el.textContent = `Showing ${count} ${count === 1 ? 'company' : 'companies'}`;
  }
}

// ─── SEARCH ───
function initSearch() {
  const input = document.getElementById('search-input');
  let debounce;

  input.addEventListener('input', () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      applyFilters();
    }, 200);
  });
}

// ─── RENDER COMPANIES ───
function renderCompanies(companies) {
  const grid = document.getElementById('company-grid');
  grid.innerHTML = '';

  companies.forEach((company, i) => {
    const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };
    const saved = isBookmarked(company.name);
    const inCompare = compareList.includes(company.name);

    const card = document.createElement('div');
    card.className = 'company-card';
    card.style.animationDelay = `${i * 0.02}s`;

    const metaItems = [];
    if (company.fundingStage) metaItems.push(`<span class="meta-stage">${company.fundingStage}</span>`);
    if (company.totalRaised) metaItems.push(`<span class="meta-raised">${company.totalRaised}</span>`);
    if (company.valuation) metaItems.push(`<span class="meta-val">${company.valuation}</span>`);

    card.innerHTML = `
      <div class="card-header">
        <div class="card-sector-badge" style="background:${sectorInfo.color}12; color:${sectorInfo.color}; border: 1px solid ${sectorInfo.color}30;">
          ${sectorInfo.icon} ${company.sector}
        </div>
        <div class="card-actions-top">
          <button class="card-bookmark ${saved ? 'active' : ''}" onclick="event.stopPropagation(); toggleBookmark('${company.name.replace(/'/g, "\\'")}'); applyFilters();" title="Save">
            ${saved ? '★' : '☆'}
          </button>
          <button class="card-compare ${inCompare ? 'active' : ''}" onclick="event.stopPropagation(); toggleCompare('${company.name.replace(/'/g, "\\'")}');" title="Compare">
            ⇔
          </button>
        </div>
      </div>
      <h3 class="card-name">${company.name}</h3>
      ${(company.signal || company.scores) ? `<div class="card-badges">${renderSignalBadge(company.signal)}${renderScoreBadge(company.scores)}</div>` : ''}
      ${company.founder ? `<p class="card-founder">${company.founder}</p>` : ''}
      <p class="card-location">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        ${company.location}
      </p>
      ${metaItems.length ? `<div class="card-meta">${metaItems.join('')}</div>` : ''}
      <p class="card-description">${company.description}</p>
      <div class="card-tags">
        ${company.tags.slice(0, 3).map(t => `<span class="tag">${t}</span>`).join('')}
      </div>
      <div class="card-footer">
        ${company.rosLink ? `<a href="${company.rosLink}" target="_blank" rel="noopener" class="card-link" onclick="event.stopPropagation();">
          Read Coverage <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>
        </a>` : '<span class="card-link" style="color:var(--text-muted);">Coming Soon</span>'}
      </div>
    `;

    // Click card to open modal
    card.addEventListener('click', () => {
      openCompanyModal(company.name);
    });
    card.style.cursor = 'pointer';

    grid.appendChild(card);
  });
}

// ─── RENDER SECTORS ───
function renderSectors() {
  const grid = document.getElementById('sectors-grid');

  Object.entries(SECTORS).forEach(([name, info]) => {
    const count = COMPANIES.filter(c => c.sector === name).length;
    const card = document.createElement('div');
    card.className = 'sector-card';

    card.innerHTML = `
      <div class="sector-icon">${info.icon}</div>
      <h3>${name}</h3>
      <p>${info.description}</p>
      ${info.trend ? `<p style="font-size: 12px; color: var(--accent); margin-top: 8px; line-height: 1.5; font-style: italic;">${info.trend}</p>` : ''}
      <div class="sector-count">${count} ${count === 1 ? 'company' : 'companies'}</div>
    `;

    card.addEventListener('click', () => {
      document.getElementById('companies').scrollIntoView({ behavior: 'smooth' });
      setTimeout(() => {
        document.getElementById('sector-filter').value = name;
        const chips = document.querySelectorAll('.chip');
        chips.forEach(c => {
          c.classList.remove('active');
          if (c.dataset.sector === name) c.classList.add('active');
        });
        applyFilters();
      }, 400);
    });

    grid.appendChild(card);
  });
}

// ─── FEATURED INNOVATORS ───
function initFeatured() {
  const scroll = document.getElementById('featured-scroll');
  if (!scroll) return;

  // Pick highest-valued companies
  const featured = COMPANIES
    .filter(c => c.valuation)
    .sort((a, b) => {
      const parseVal = v => {
        const m = v.match(/([\d.]+)\s*(B|M|T)?/i);
        if (!m) return 0;
        let val = parseFloat(m[1]);
        const unit = (m[2] || '').toUpperCase();
        if (unit === 'T') val *= 1000;
        else if (unit === 'M') val *= 0.001;
        return val;
      };
      return parseVal(b.valuation) - parseVal(a.valuation);
    })
    .slice(0, 12);

  featured.forEach(company => {
    const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };

    const card = document.createElement('div');
    card.className = 'featured-card';

    card.innerHTML = `
      <div class="featured-card-accent" style="background: ${sectorInfo.color};"></div>
      <div class="featured-card-body">
        <span class="featured-sector" style="color: ${sectorInfo.color};">${sectorInfo.icon} ${company.sector}</span>
        <h3 class="featured-name">${company.name}</h3>
        ${company.valuation ? `<span class="featured-val">${company.valuation}</span>` : ''}
        <p class="featured-loc">${company.location}</p>
      </div>
    `;

    card.addEventListener('click', () => openCompanyModal(company.name));
    card.style.cursor = 'pointer';
    scroll.appendChild(card);
  });
}

// ─── MODAL INIT ───
function initModal() {
  const overlay = document.getElementById('modal-overlay');
  const closeBtn = document.getElementById('modal-close');

  closeBtn.addEventListener('click', () => {
    closeModal();
    // Remove company from URL
    const url = new URL(window.location);
    url.searchParams.delete('company');
    window.history.pushState({}, '', url);
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      closeModal();
      const url = new URL(window.location);
      url.searchParams.delete('company');
      window.history.pushState({}, '', url);
    }
  });
}

// ─── COMPARE INIT ───
function initCompare() {
  document.getElementById('compare-btn').addEventListener('click', openCompareView);
  document.getElementById('compare-clear').addEventListener('click', () => {
    compareList = [];
    updateCompareBar();
    applyFilters();
  });
}

// ─── KEYBOARD NAVIGATION ───
function initKeyboard() {
  document.addEventListener('keydown', (e) => {
    // / to focus search
    if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
      const active = document.activeElement;
      if (active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') {
        e.preventDefault();
        document.getElementById('search-input').focus();
      }
    }

    // Escape to close modal
    if (e.key === 'Escape') {
      const overlay = document.getElementById('modal-overlay');
      if (overlay.classList.contains('active')) {
        closeModal();
        const url = new URL(window.location);
        url.searchParams.delete('company');
        window.history.pushState({}, '', url);
      }
    }

    // b to bookmark in modal
    if (e.key === 'b' && !e.ctrlKey && !e.metaKey) {
      const active = document.activeElement;
      if (active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') {
        const overlay = document.getElementById('modal-overlay');
        if (overlay.classList.contains('active')) {
          const nameEl = document.querySelector('.modal-company-name');
          if (nameEl) {
            // Get only the direct text, not signal badge text
            const companyName = nameEl.childNodes[0].textContent.trim();
            toggleBookmark(companyName);
            openCompanyModal(companyName); // refresh modal
          }
        }
      }
    }
  });
}

// ─── URL STATE ───
function initURLState() {
  const params = new URLSearchParams(window.location.search);

  // Open company modal if ?company= present
  const companyParam = params.get('company');
  if (companyParam) {
    setTimeout(() => openCompanyModal(companyParam), 500);
  }

  // Apply filters from URL
  const sectorParam = params.get('sector');
  if (sectorParam) {
    document.getElementById('sector-filter').value = sectorParam;
    const chips = document.querySelectorAll('.chip');
    chips.forEach(c => {
      c.classList.remove('active');
      if (c.dataset.sector === sectorParam) c.classList.add('active');
    });
  }

  const countryParam = params.get('country');
  if (countryParam) {
    document.getElementById('country-filter').value = countryParam;
  }

  const qParam = params.get('q');
  if (qParam) {
    document.getElementById('search-input').value = qParam;
  }

  if (sectorParam || countryParam || qParam) {
    setTimeout(() => applyFilters(), 100);
  }
}

// ─── SCROLL ANIMATIONS ───
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.section-header, .sector-card, .featured-section').forEach(el => {
    observer.observe(el);
  });

  // Re-observe dynamically added sector cards
  const gridObserver = new MutationObserver(() => {
    document.querySelectorAll('.sector-card:not(.observed)').forEach(el => {
      el.classList.add('observed');
      observer.observe(el);
    });
  });

  const sectorsGrid = document.getElementById('sectors-grid');
  if (sectorsGrid) {
    gridObserver.observe(sectorsGrid, { childList: true });
  }
}

// ─── MOBILE MENU ───
function initMobileMenu() {
  const btn = document.querySelector('.mobile-menu-btn');
  const links = document.querySelector('.nav-links');

  btn.addEventListener('click', () => {
    links.classList.toggle('open');
    btn.classList.toggle('open');
  });

  links.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      links.classList.remove('open');
      btn.classList.remove('open');
    });
  });
}

// ─── MOVEMENT TRACKER ───
function initMovementTracker() {
  const grid = document.getElementById('movement-grid');
  if (!grid) return;

  const companiesWithEvents = COMPANIES
    .filter(c => c.recentEvent)
    .sort((a, b) => b.recentEvent.date.localeCompare(a.recentEvent.date));

  function renderMovements(type) {
    const filtered = type === 'all'
      ? companiesWithEvents
      : companiesWithEvents.filter(c => c.recentEvent.type === type);

    grid.innerHTML = filtered.slice(0, 15).map(c => {
      const evType = c.recentEvent.type;
      return `
        <div class="movement-item" onclick="openCompanyModal('${c.name.replace(/'/g, "\\'")}')">
          <span class="movement-type movement-type-${evType}">${evType}</span>
          <div class="movement-info">
            <div class="movement-company">${c.name} ${renderSignalBadge(c.signal)}</div>
            <div class="movement-text">${c.recentEvent.text}</div>
          </div>
          <span class="movement-date">${c.recentEvent.date}</span>
        </div>
      `;
    }).join('');

    if (filtered.length === 0) {
      grid.innerHTML = '<p style="color: var(--text-muted); padding: 20px;">No events in this category yet.</p>';
    }
  }

  renderMovements('all');

  // Tab handling
  document.querySelectorAll('.movement-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.movement-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      renderMovements(tab.dataset.type);
    });
  });
}

// ─── WEEKLY DIGEST ───
function initWeeklyDigest() {
  const scroll = document.getElementById('digest-scroll');
  if (!scroll || typeof WEEKLY_DIGEST === 'undefined') return;

  WEEKLY_DIGEST.forEach(item => {
    const card = document.createElement('div');
    card.className = 'digest-card';

    const catClass = `digest-category-${item.category}`;

    card.innerHTML = `
      <div>
        <span class="digest-date">${item.date}</span>
        <span class="digest-category ${catClass}">${item.category}</span>
      </div>
      <h3 class="digest-headline">${item.headline}</h3>
      <p class="digest-summary">${item.summary}</p>
      <div class="digest-companies">
        ${item.relatedCompanies.map(name => {
          const exists = COMPANIES.find(c => c.name === name);
          return exists
            ? `<span class="portfolio-chip linked small" onclick="openCompanyModal('${name.replace(/'/g, "\\'")}')">${name}</span>`
            : `<span class="portfolio-chip small">${name}</span>`;
        }).join('')}
      </div>
    `;

    scroll.appendChild(card);
  });
}

// ─── EXPORT WATCHLIST CSV ───
function exportWatchlistCSV() {
  const savedCompanies = COMPANIES.filter(c => isBookmarked(c.name));
  if (savedCompanies.length === 0) {
    alert('No companies saved to watchlist. Save companies first using the ☆ button.');
    return;
  }

  const headers = ['Name', 'Sector', 'Location', 'Country', 'Stage', 'Total Raised', 'Valuation', 'Founder', 'Signal', 'Score', 'Description'];
  const rows = savedCompanies.map(c => {
    const country = getCountry(c.state, c.location);
    const avg = getAverageScore(c.scores);
    return [
      c.name,
      c.sector,
      c.location,
      country,
      c.fundingStage || '',
      c.totalRaised || '',
      c.valuation || '',
      c.founder || '',
      c.signal || '',
      avg > 0 ? avg.toFixed(1) : '',
      `"${(c.description || '').replace(/"/g, '""')}"`
    ].join(',');
  });

  const csv = [headers.join(','), ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `innovators-league-watchlist-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ─── INNOVATION LEADERBOARD ───
function initLeaderboard() {
  const grid = document.getElementById('leaderboard-grid');
  if (!grid) return;

  // Get companies with scores, calculate average, sort by score
  const scored = COMPANIES
    .filter(c => c.scores)
    .map(c => ({
      ...c,
      avgScore: getAverageScore(c.scores)
    }))
    .sort((a, b) => b.avgScore - a.avgScore)
    .slice(0, 20);

  scored.forEach((c, i) => {
    const rank = i + 1;
    const rankClass = rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : 'normal';
    const rankSymbol = rank <= 3 ? ['🥇','🥈','🥉'][rank - 1] : `#${rank}`;
    const scoreClass = c.avgScore >= 8 ? 'high' : 'mid';
    const sectorInfo = SECTORS[c.sector] || { icon: '' };
    const signalBadge = c.signal ? renderSignalBadge(c.signal) : '';

    const row = document.createElement('div');
    row.className = 'leaderboard-row';
    row.innerHTML = `
      <div class="leaderboard-rank ${rankClass}">${rankSymbol}</div>
      <div class="leaderboard-company">
        <span class="leaderboard-name">${c.name} ${signalBadge}</span>
        <span class="leaderboard-sector">${sectorInfo.icon} ${c.sector}</span>
      </div>
      <div class="leaderboard-score ${scoreClass}">${c.avgScore.toFixed(1)}</div>
      <div class="leaderboard-bar">
        <div class="leaderboard-bar-fill" style="width: 0%"></div>
      </div>
      <div class="leaderboard-signal">${c.valuation || ''}</div>
      <div class="leaderboard-val">${c.fundingStage || ''}</div>
    `;

    row.addEventListener('click', () => openCompanyModal(c.name));
    grid.appendChild(row);

    // Animate bar
    setTimeout(() => {
      row.querySelector('.leaderboard-bar-fill').style.width = `${c.avgScore * 10}%`;
    }, 100 + i * 60);
  });
}

// ─── ENHANCED COMPARE VIEW ───
function openCompareView() {
  if (compareList.length < 2) return;

  const companies = compareList.map(name => COMPANIES.find(c => c.name === name)).filter(Boolean);
  if (companies.length < 2) return;

  const cols = companies.length + 1;
  const gridCols = `180px repeat(${companies.length}, 1fr)`;

  const metrics = [
    { label: 'Sector', key: c => c.sector },
    { label: 'Location', key: c => c.location },
    { label: 'Stage', key: c => c.fundingStage || 'N/A' },
    { label: 'Total Raised', key: c => c.totalRaised || 'N/A' },
    { label: 'Valuation', key: c => c.valuation || 'N/A' },
    { label: 'Signal', key: c => c.signal ? renderSignalBadge(c.signal) : 'None' },
    { label: 'Avg Score', key: c => c.scores ? getAverageScore(c.scores).toFixed(1) + '/10' : 'N/A', highlight: true },
    { label: 'Team', key: c => c.scores ? c.scores.team + '/10' : 'N/A' },
    { label: 'Traction', key: c => c.scores ? c.scores.traction + '/10' : 'N/A' },
    { label: 'Tech Moat', key: c => c.scores ? c.scores.techMoat + '/10' : 'N/A' },
    { label: 'Market', key: c => c.scores ? c.scores.market + '/10' : 'N/A' },
    { label: 'Momentum', key: c => c.scores ? c.scores.momentum + '/10' : 'N/A' },
    { label: 'Founder', key: c => c.founder || 'N/A' },
    { label: 'Latest Event', key: c => c.recentEvent ? c.recentEvent.text : 'N/A' }
  ];

  const body = document.getElementById('modal-body');
  body.innerHTML = `
    <div style="margin-bottom: 20px;">
      <span class="modal-sector-badge" style="background: var(--accent-dim); color: var(--accent);">COMPARISON</span>
      <h2 class="modal-company-name">Company Comparison</h2>
      <p style="color: var(--text-muted); font-size: 14px;">Side-by-side analysis of ${companies.length} companies</p>
    </div>

    <div class="compare-grid">
      <div class="compare-header-row" style="display: grid; grid-template-columns: ${gridCols};">
        <div class="compare-label">Metric</div>
        ${companies.map(c => {
          const sectorInfo = SECTORS[c.sector] || { color: '#6b7280' };
          return `<div style="text-align: center;">
            <div style="font-family: var(--font-display); font-weight: 700; font-size: 16px; color: var(--text-primary);">${c.name}</div>
            <div style="font-size: 11px; color: ${sectorInfo.color};">${c.sector}</div>
          </div>`;
        }).join('')}
      </div>
      ${metrics.map(m => `
        <div class="compare-data-row" style="display: grid; grid-template-columns: ${gridCols};">
          <div class="compare-label">${m.label}</div>
          ${companies.map(c => `<div class="compare-value ${m.highlight ? 'highlight' : ''}" style="text-align: center;">${m.key(c)}</div>`).join('')}
        </div>
      `).join('')}
    </div>
  `;

  document.getElementById('modal-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

// ─── SMOOTH SCROLL (runs after DOMContentLoaded via initSmoothScroll) ───
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(a.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

// ─── BREAKING NEWS TICKER ───
function initNewsTicker() {
  const scroll = document.getElementById('ticker-scroll');
  if (!scroll || typeof NEWS_TICKER === 'undefined') return;

  NEWS_TICKER.forEach((item, i) => {
    if (i > 0) {
      const divider = document.createElement('span');
      divider.className = 'ticker-divider';
      scroll.appendChild(divider);
    }

    const el = document.createElement('span');
    el.className = `ticker-item ticker-priority-${item.priority}`;
    el.innerHTML = `<span>${item.text}</span><span class="ticker-time">${item.time}</span>`;
    scroll.appendChild(el);
  });
}

// ─── MARKET PULSE ───
function initMarketPulse() {
  const grid = document.getElementById('market-pulse-grid');
  if (!grid || typeof MARKET_PULSE === 'undefined') return;

  MARKET_PULSE.forEach(stock => {
    const card = document.createElement('div');
    card.className = 'pulse-card';
    card.innerHTML = `
      <div class="pulse-ticker">${stock.ticker}</div>
      <div class="pulse-name">${stock.name}</div>
      <div>
        <span class="pulse-val">${stock.valuation}</span>
        <span class="pulse-change ${stock.trend}">${stock.change}</span>
      </div>
    `;
    card.addEventListener('click', () => openCompanyModal(stock.name));
    grid.appendChild(card);
  });
}

// ─── FUNDING TRACKER ───
function initFundingTracker() {
  const grid = document.getElementById('funding-tracker-grid');
  if (!grid || typeof FUNDING_TRACKER === 'undefined') return;

  // Header row
  const header = document.createElement('div');
  header.className = 'funding-row funding-row-header';
  header.innerHTML = `
    <span>Company</span>
    <span>Amount</span>
    <span>Stage</span>
    <span>Lead Investor</span>
    <span>Valuation</span>
    <span>Date</span>
  `;
  grid.appendChild(header);

  FUNDING_TRACKER.forEach(round => {
    const row = document.createElement('div');
    row.className = 'funding-row';
    row.innerHTML = `
      <span class="funding-company">${round.company}</span>
      <span class="funding-amount">${round.amount}</span>
      <span><span class="funding-stage-tag">${round.stage}</span></span>
      <span class="funding-lead">${round.lead}</span>
      <span class="funding-val">${round.valuation}</span>
      <span class="funding-date">${round.date}</span>
    `;
    row.addEventListener('click', () => openCompanyModal(round.company));
    grid.appendChild(row);
  });
}

// ─── SECTOR MOMENTUM INDEX ───
function initSectorMomentum() {
  const grid = document.getElementById('momentum-grid');
  if (!grid || typeof SECTOR_MOMENTUM === 'undefined') return;

  SECTOR_MOMENTUM.forEach((item, i) => {
    const sectorInfo = SECTORS[item.sector] || { icon: '📊' };
    const scoreClass = item.momentum >= 80 ? 'high' : item.momentum >= 60 ? 'mid' : 'low';
    const trendClass = `momentum-trend-${item.trend}`;

    const row = document.createElement('div');
    row.className = 'momentum-row';
    row.innerHTML = `
      <div class="momentum-sector-name">
        <span class="momentum-sector-icon">${sectorInfo.icon}</span>
        ${item.sector}
      </div>
      <div class="momentum-score ${scoreClass}">${item.momentum}</div>
      <div class="momentum-bar-bg">
        <div class="momentum-bar-fill ${scoreClass}" style="width: 0%"></div>
      </div>
      <div class="momentum-trend ${trendClass}">${item.trend}</div>
      <div class="momentum-funding">${item.fundingQ} Q1</div>
    `;

    grid.appendChild(row);

    // Animate bar
    setTimeout(() => {
      row.querySelector('.momentum-bar-fill').style.width = `${item.momentum}%`;
    }, 200 + i * 80);
  });
}

// ─── IPO & EXIT PIPELINE ───
function initIPOPipeline() {
  const grid = document.getElementById('ipo-grid');
  if (!grid || typeof IPO_PIPELINE === 'undefined') return;

  IPO_PIPELINE.forEach(item => {
    const card = document.createElement('div');
    card.className = 'ipo-card';

    const sectorInfo = SECTORS[item.sector] || { icon: '', color: '#6b7280' };

    card.innerHTML = `
      <div style="font-size: 11px; color: ${sectorInfo.color}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">${sectorInfo.icon} ${item.sector}</div>
      <div class="ipo-company">${item.company}</div>
      <div class="ipo-status ipo-status-${item.likelihood}">${item.status}</div>
      <div class="ipo-meta">
        <div class="ipo-meta-item">
          <div class="ipo-meta-label">Timeline</div>
          <div class="ipo-meta-value">${item.estimatedDate}</div>
        </div>
        <div class="ipo-meta-item">
          <div class="ipo-meta-label">Est. Valuation</div>
          <div class="ipo-meta-value" style="color: var(--accent);">${item.estimatedValuation}</div>
        </div>
      </div>
    `;

    card.addEventListener('click', () => openCompanyModal(item.company));
    grid.appendChild(card);
  });
}

// ─── TRL DASHBOARD ───
function initTRLDashboard() {
  const legend = document.getElementById('trl-legend');
  const grid = document.getElementById('trl-grid');
  if (!grid || typeof TRL_DEFINITIONS === 'undefined' || typeof TRL_RANKINGS === 'undefined') return;

  // Render legend
  if (legend) {
    legend.innerHTML = Object.entries(TRL_DEFINITIONS).map(([level, def]) =>
      `<div class="trl-legend-item">
        <div class="trl-level-badge" style="background:${def.color};">${level}</div>
        <div class="trl-legend-text">
          <div class="trl-legend-label">${def.label}</div>
        </div>
      </div>`
    ).join('');
  }

  // Group by TRL level (descending)
  const grouped = {};
  TRL_RANKINGS.forEach(item => {
    if (!grouped[item.trl]) grouped[item.trl] = [];
    grouped[item.trl].push(item);
  });

  Object.keys(grouped).sort((a, b) => b - a).forEach(trl => {
    const def = TRL_DEFINITIONS[trl];
    const section = document.createElement('div');
    section.className = 'trl-row';

    const companies = grouped[trl];
    section.innerHTML = `
      <div class="trl-row-header">
        <div class="trl-row-badge" style="background:${def.color};">TRL ${trl}</div>
        <div class="trl-row-info">
          <span class="trl-row-label">${def.label}</span>
          <span class="trl-row-count">${companies.length} companies</span>
        </div>
      </div>
      <div class="trl-row-companies">
        ${companies.map(c => {
          const comp = COMPANIES.find(x => x.name === c.company);
          const sectorInfo = comp ? (SECTORS[comp.sector] || { icon: '📦', color: '#6b7280' }) : { icon: '📦', color: '#6b7280' };
          return `<div class="trl-company-chip" onclick="openCompanyModal('${c.company}')" title="${c.note}">
            <span style="color:${sectorInfo.color}">${sectorInfo.icon}</span>
            <span class="trl-company-name">${c.company}</span>
            <span class="trl-company-note">${c.note.substring(0, 60)}${c.note.length > 60 ? '...' : ''}</span>
          </div>`;
        }).join('')}
      </div>
    `;

    grid.appendChild(section);
  });
}

// ─── DEAL TRACKER ───
function initDealTracker() {
  const grid = document.getElementById('deal-grid');
  if (!grid || typeof DEAL_TRACKER === 'undefined') return;

  function renderDeals(filter) {
    grid.innerHTML = '';
    const deals = filter === 'lead'
      ? DEAL_TRACKER.filter(d => d.leadOrParticipant === 'lead')
      : DEAL_TRACKER;

    // Sort by date descending
    deals.sort((a, b) => b.date.localeCompare(a.date));

    // Header
    const header = document.createElement('div');
    header.className = 'deal-row deal-header';
    header.innerHTML = `
      <div class="deal-cell deal-company-col">Company</div>
      <div class="deal-cell deal-investor-col">Investor</div>
      <div class="deal-cell deal-amount-col">Amount</div>
      <div class="deal-cell deal-round-col">Round</div>
      <div class="deal-cell deal-val-col">Valuation</div>
      <div class="deal-cell deal-date-col">Date</div>
      <div class="deal-cell deal-role-col">Role</div>
    `;
    grid.appendChild(header);

    deals.forEach((deal, i) => {
      const row = document.createElement('div');
      row.className = 'deal-row';
      row.style.animationDelay = `${i * 30}ms`;
      const isLead = deal.leadOrParticipant === 'lead';
      row.innerHTML = `
        <div class="deal-cell deal-company-col"><span class="deal-company-link" onclick="openCompanyModal('${deal.company}')">${deal.company}</span></div>
        <div class="deal-cell deal-investor-col">${deal.investor}</div>
        <div class="deal-cell deal-amount-col" style="color:var(--accent);font-weight:600;">${deal.amount}</div>
        <div class="deal-cell deal-round-col">${deal.round}</div>
        <div class="deal-cell deal-val-col">${deal.valuation || '—'}</div>
        <div class="deal-cell deal-date-col">${deal.date}</div>
        <div class="deal-cell deal-role-col"><span class="deal-role ${isLead ? 'deal-role-lead' : ''}">${isLead ? '★ Lead' : 'Participant'}</span></div>
      `;
      grid.appendChild(row);
    });
  }

  renderDeals('all');

  // Filter buttons
  document.querySelectorAll('.deal-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.deal-filter').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderDeals(btn.dataset.filter);
    });
  });
}

// ─── GROWTH SIGNALS ───
function initGrowthSignals() {
  const grid = document.getElementById('signals-grid');
  if (!grid || typeof GROWTH_SIGNALS === 'undefined' || typeof SIGNAL_TYPES === 'undefined') return;

  // Sort by strength (strong first) then date
  const sorted = [...GROWTH_SIGNALS].sort((a, b) => {
    const strengthOrder = { strong: 0, medium: 1, weak: 2 };
    if (strengthOrder[a.strength] !== strengthOrder[b.strength]) return strengthOrder[a.strength] - strengthOrder[b.strength];
    return b.date.localeCompare(a.date);
  });

  sorted.forEach((sig, i) => {
    const type = SIGNAL_TYPES[sig.signal] || { icon: '📊', label: sig.signal };
    const card = document.createElement('div');
    card.className = `signal-card signal-${sig.strength}`;
    card.style.animationDelay = `${i * 40}ms`;

    card.innerHTML = `
      <div class="signal-card-header">
        <span class="signal-type-icon">${type.icon}</span>
        <span class="signal-type-label">${type.label}</span>
        <span class="signal-strength signal-strength-${sig.strength}">${sig.strength}</span>
      </div>
      <div class="signal-company" onclick="openCompanyModal('${sig.company}')">${sig.company}</div>
      <div class="signal-detail">${sig.detail}</div>
      <div class="signal-date">${sig.date}</div>
    `;

    grid.appendChild(card);
  });
}

// ─── MARKET MAP ───
function initMarketMap() {
  const grid = document.getElementById('market-map-grid');
  if (!grid || typeof MARKET_MAP === 'undefined') return;

  Object.entries(MARKET_MAP).forEach(([category, data]) => {
    const card = document.createElement('div');
    card.className = 'market-map-card';

    const renderCompanyList = (companies, className) =>
      companies.map(c =>
        `<span class="market-company ${className}" onclick="openCompanyModal('${c}')">${c}</span>`
      ).join('');

    card.innerHTML = `
      <div class="market-map-header">
        <h3 class="market-map-title">${category}</h3>
        <span class="market-map-tam">${data.totalTAM} TAM</span>
      </div>
      <p class="market-map-desc">${data.description}</p>
      <div class="market-map-trend">${data.keyTrend}</div>
      <div class="market-map-tiers">
        <div class="market-tier">
          <div class="market-tier-label">🏆 Leaders</div>
          <div class="market-tier-companies">${renderCompanyList(data.leaders, 'market-leader')}</div>
        </div>
        <div class="market-tier">
          <div class="market-tier-label">⚡ Challengers</div>
          <div class="market-tier-companies">${renderCompanyList(data.challengers, 'market-challenger')}</div>
        </div>
        <div class="market-tier">
          <div class="market-tier-label">🌱 Emerging</div>
          <div class="market-tier-companies">${renderCompanyList(data.emerging, 'market-emerging')}</div>
        </div>
      </div>
    `;

    grid.appendChild(card);
  });
}
