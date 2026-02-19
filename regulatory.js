// ─── REGULATORY INTELLIGENCE PAGE ───

// ─── MAIN INIT ───
document.addEventListener('DOMContentLoaded', function() {
  initRegulatory();
});

function initRegulatory() {
  safeInit('HeroStats', initHeroStats);
  safeInit('RegTimeline', initRegTimeline);
  safeInit('FDATracker', initFDATracker);
  safeInit('AgencyOverview', initAgencyOverview);
  safeInit('RegRisk', initRegRisk);
  safeInit('FedRegisterMonitor', initFedRegisterMonitor);
  safeInit('ClinicalTrials', initClinicalTrials);
  safeInit('MobileMenu', initRegMobileMenu);
  safeInit('SectionObserver', initSectionObserver);
}

function safeInit(name, fn) {
  try {
    fn();
  } catch (e) {
    console.error('[Regulatory] ' + name + ' failed:', e);
  }
}

// ─── DATA HELPERS ───
// Note: const declarations don't attach to window, so use typeof checks directly
function getFDAActions() {
  return (typeof FDA_ACTIONS !== 'undefined' && Array.isArray(FDA_ACTIONS)) ? FDA_ACTIONS : [];
}
function getFedRegister() {
  return (typeof FEDERAL_REGISTER !== 'undefined' && Array.isArray(FEDERAL_REGISTER)) ? FEDERAL_REGISTER : [];
}
function getClinicalTrials() {
  return (typeof CLINICAL_TRIALS !== 'undefined' && Array.isArray(CLINICAL_TRIALS)) ? CLINICAL_TRIALS : [];
}
function getDOEPrograms() {
  return (typeof DOE_PROGRAMS !== 'undefined' && Array.isArray(DOE_PROGRAMS)) ? DOE_PROGRAMS : [];
}

function getCompanies() {
  if (typeof COMPANIES !== 'undefined' && Array.isArray(COMPANIES)) return COMPANIES;
  return [];
}

function getSectors() {
  if (typeof SECTORS !== 'undefined' && typeof SECTORS === 'object') return SECTORS;
  return {};
}

// ─── COUNTER ANIMATION ───
function regAnimateCounter(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const duration = 1200;
  const step = Math.max(target / (duration / 16), 0.5);
  function tick() {
    current += step;
    if (current >= target) { el.textContent = target; return; }
    el.textContent = Math.floor(current);
    requestAnimationFrame(tick);
  }
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) { tick(); observer.disconnect(); }
  });
  observer.observe(el);
}

// ─── 1. HERO STATS ───
function initHeroStats() {
  const fda = getFDAActions();
  const fedReg = getFedRegister();
  const trials = getClinicalTrials();
  const doe = getDOEPrograms();

  // Total regulatory actions
  const totalActions = fda.length + fedReg.length + trials.length + doe.length;
  regAnimateCounter('reg-actions-count', totalActions);

  // Unique companies monitored
  const companySet = new Set();
  fda.forEach(a => { if (a.company) companySet.add(a.company); });
  trials.forEach(t => {
    if (t.sponsor) companySet.add(t.sponsor);
  });
  doe.forEach(d => {
    if (d.companies) {
      d.companies.split(',').forEach(c => companySet.add(c.trim()));
    }
  });
  regAnimateCounter('reg-companies', companySet.size);

  // Unique agencies
  const agencySet = new Set();
  fedReg.forEach(r => {
    if (r.agencies) {
      r.agencies.split(',').forEach(a => agencySet.add(a.trim()));
    }
  });
  doe.forEach(d => { if (d.agency) agencySet.add(d.agency); });
  // Always include FDA as we have FDA_ACTIONS
  if (fda.length > 0) agencySet.add('FDA');
  regAnimateCounter('reg-agencies', agencySet.size);
}

// ─── 2. REGULATORY TIMELINE ───
let regTimelineData = [];
let regTimelineShown = 0;
const REG_TIMELINE_PAGE_SIZE = 30;

function initRegTimeline() {
  const fda = getFDAActions();
  const fedReg = getFedRegister();
  const trials = getClinicalTrials();
  const doe = getDOEPrograms();
  const entries = [];

  // FDA entries
  fda.forEach(a => {
    entries.push({
      date: a.date || '',
      type: 'fda',
      badgeClass: 'badge-fda',
      badgeLabel: 'FDA',
      agency: 'FDA',
      title: a.product || 'FDA Action',
      company: a.company || '',
      desc: 'Device 510(k) — Status: ' + (a.status || 'N/A'),
      dotColor: '#3b82f6'
    });
  });

  // Federal Register entries
  fedReg.forEach(r => {
    let agency = 'Federal Register';
    let badgeClass = 'badge-fedreg';
    let badgeLabel = 'FedReg';
    let dotColor = '#9ca3af';
    const agStr = (r.agencies || '').toLowerCase();

    if (agStr.includes('nuclear regulatory')) {
      agency = 'NRC'; badgeClass = 'badge-nrc'; badgeLabel = 'NRC'; dotColor = '#22c55e';
    } else if (agStr.includes('aviation') || agStr.includes('faa')) {
      agency = 'FAA'; badgeClass = 'badge-faa'; badgeLabel = 'FAA'; dotColor = '#f97316';
    } else if (agStr.includes('energy department') || agStr.includes('doe')) {
      agency = 'DOE'; badgeClass = 'badge-doe'; badgeLabel = 'DOE'; dotColor = '#a855f7';
    } else if (agStr.includes('food and drug') || agStr.includes('fda')) {
      agency = 'FDA'; badgeClass = 'badge-fda'; badgeLabel = 'FDA'; dotColor = '#3b82f6';
    }

    entries.push({
      date: r.date || '',
      type: 'fedreg',
      badgeClass: badgeClass,
      badgeLabel: badgeLabel,
      agency: r.agencies || agency,
      title: r.title || 'Federal Register Entry',
      company: '',
      desc: (r.type || '') + (r.sectors ? ' — Sectors: ' + r.sectors : ''),
      dotColor: dotColor
    });
  });

  // Clinical trial entries
  trials.forEach(t => {
    entries.push({
      date: t.lastUpdated || '',
      type: 'trial',
      badgeClass: 'badge-trial',
      badgeLabel: t.phase && t.phase !== 'N/A' && t.phase !== 'NA' ? t.phase.replace('PHASE', 'Ph') : 'Trial',
      agency: 'ClinicalTrials.gov',
      title: t.title || 'Clinical Trial',
      company: t.sponsor || '',
      desc: (t.conditions || '') + (t.enrollment ? ' — Enrollment: ' + t.enrollment : ''),
      dotColor: '#ec4899'
    });
  });

  // DOE program entries
  doe.forEach(d => {
    entries.push({
      date: d.lastUpdate || '',
      type: 'doe',
      badgeClass: 'badge-doe',
      badgeLabel: 'DOE',
      agency: d.agency || 'DOE',
      title: d.program || 'DOE Program',
      company: d.companies || '',
      desc: (d.status || '') + ' — Funding: $' + (d.funding || 'N/A'),
      dotColor: '#a855f7'
    });
  });

  // Sort by date, newest first
  entries.sort((a, b) => {
    if (!a.date && !b.date) return 0;
    if (!a.date) return 1;
    if (!b.date) return -1;
    return b.date.localeCompare(a.date);
  });

  regTimelineData = entries;
  regTimelineShown = 0;
  renderTimelineBatch();

  // Load more button
  const btn = document.getElementById('btn-load-more-timeline');
  if (btn) {
    btn.addEventListener('click', renderTimelineBatch);
  }
}

function renderTimelineBatch() {
  const container = document.getElementById('reg-timeline-list');
  const moreBtn = document.getElementById('reg-timeline-more');
  if (!container) return;

  if (regTimelineData.length === 0) {
    container.innerHTML = '<div class="reg-empty-state">No regulatory data available.</div>';
    return;
  }

  const end = Math.min(regTimelineShown + REG_TIMELINE_PAGE_SIZE, regTimelineData.length);
  let html = '';
  for (let i = regTimelineShown; i < end; i++) {
    const e = regTimelineData[i];
    html += renderTimelineEntry(e);
  }

  if (regTimelineShown === 0) {
    container.innerHTML = html;
  } else {
    container.insertAdjacentHTML('beforeend', html);
  }

  regTimelineShown = end;

  if (moreBtn) {
    moreBtn.style.display = regTimelineShown < regTimelineData.length ? 'block' : 'none';
  }
}

function renderTimelineEntry(e) {
  const dateStr = e.date ? formatDate(e.date) : 'No date';
  const companyHtml = e.company ? `<div class="reg-timeline-company">${escHtml(e.company)}</div>` : '';
  const descHtml = e.desc ? `<div class="reg-timeline-desc">${escHtml(truncate(e.desc, 150))}</div>` : '';

  return `
    <div class="reg-timeline-entry">
      <div class="reg-timeline-dot-col">
        <div class="reg-timeline-dot" style="background: ${e.dotColor}"></div>
        <div class="reg-timeline-line"></div>
      </div>
      <div class="reg-timeline-body">
        <div class="reg-timeline-meta">
          <span class="reg-timeline-date">${dateStr}</span>
          <span class="reg-timeline-badge ${e.badgeClass}">${escHtml(e.badgeLabel)}</span>
          <span class="reg-timeline-agency">${escHtml(truncate(e.agency, 60))}</span>
        </div>
        <div class="reg-timeline-title">${escHtml(truncate(e.title, 120))}</div>
        ${companyHtml}
        ${descHtml}
      </div>
    </div>
  `;
}

// ─── 3. FDA PATHWAY TRACKER ───
const FDA_STAGES = ['Preclinical', 'Phase 1', 'Phase 2', 'Phase 3', 'Approved'];
const FDA_STAGE_SHORT = ['Pre', 'P1', 'P2', 'P3', '✓'];

function initFDATracker() {
  const fda = getFDAActions();
  const grid = document.getElementById('fda-tracker-grid');
  if (!grid) return;

  if (fda.length === 0) {
    grid.innerHTML = '<div class="reg-empty-state">No FDA data available.</div>';
    return;
  }

  // Group by company
  const byCompany = {};
  fda.forEach(a => {
    const co = a.company || 'Unknown';
    if (!byCompany[co]) byCompany[co] = [];
    byCompany[co].push(a);
  });

  // Sort companies by number of actions (most first)
  const companies = Object.keys(byCompany).sort((a, b) => byCompany[b].length - byCompany[a].length);

  let html = '';
  companies.forEach(co => {
    const actions = byCompany[co];
    // Sort actions by date newest first
    actions.sort((a, b) => (b.date || '').localeCompare(a.date || ''));

    // Determine furthest stage - for 510k cleared devices, they're effectively "Approved"
    // Since all data is device_510k with SESE (substantially equivalent), treat as Approved
    const hasApproved = actions.some(a => a.status === 'SESE' || a.status === 'SESU');
    const stageIndex = hasApproved ? 4 : 0; // All 510k cleared = Approved

    html += `
      <div class="fda-company-card">
        <div class="fda-company-name">${escHtml(co)}</div>
        <div class="fda-company-count">${actions.length} FDA action${actions.length !== 1 ? 's' : ''}</div>
        ${renderFDAPipeline(stageIndex)}
        <div class="fda-products-list">
          ${actions.slice(0, 5).map(a => `
            <div class="fda-product-item">
              <span class="fda-product-date">${a.date || 'N/A'}</span>
              <span class="fda-product-name" title="${escHtml(a.product || '')}">${escHtml(truncate(a.product || 'N/A', 70))}</span>
              <span class="fda-product-status ${getStatusClass(a.status)}">${escHtml(a.status || 'N/A')}</span>
            </div>
          `).join('')}
          ${actions.length > 5 ? `<div style="color: rgba(255,255,255,0.35); font-size: 0.78rem; padding: 4px 10px;">+ ${actions.length - 5} more actions</div>` : ''}
        </div>
      </div>
    `;
  });

  grid.innerHTML = html;
}

function renderFDAPipeline(activeIndex) {
  let html = '<div class="fda-pipeline">';
  for (let i = 0; i < FDA_STAGES.length; i++) {
    if (i > 0) {
      const connClass = i <= activeIndex ? 'completed' : '';
      html += `<div class="fda-pipeline-connector ${connClass}"></div>`;
    }
    const isActive = i === activeIndex;
    const isCompleted = i < activeIndex;
    const circleClass = isActive ? 'active' : isCompleted ? 'completed' : '';
    const labelClass = isActive ? 'active' : isCompleted ? 'completed' : '';
    html += `
      <div class="fda-stage">
        <div class="fda-stage-circle ${circleClass}">${FDA_STAGE_SHORT[i]}</div>
        <div class="fda-stage-label ${labelClass}">${FDA_STAGES[i]}</div>
      </div>
    `;
  }
  html += '</div>';
  return html;
}

function getStatusClass(status) {
  switch ((status || '').toUpperCase()) {
    case 'SESE': return 'fda-status-sese';
    case 'DENG': return 'fda-status-deng';
    case 'SESU': return 'fda-status-sesu';
    default: return '';
  }
}

// ─── 4. AGENCY OVERVIEW ───
function initAgencyOverview() {
  const grid = document.getElementById('agency-overview-grid');
  if (!grid) return;

  const fda = getFDAActions();
  const fedReg = getFedRegister();
  const trials = getClinicalTrials();
  const doe = getDOEPrograms();

  // Count NRC actions in Federal Register
  const nrcActions = fedReg.filter(r => (r.agencies || '').toLowerCase().includes('nuclear regulatory'));
  const nrcCompanies = new Set();
  nrcActions.forEach(r => {
    if (r.sectors && r.sectors.includes('nuclear')) {
      // Match with known nuclear companies
      const nuclearCos = ['TerraPower', 'X-energy', 'Kairos Power', 'Oklo', 'Westinghouse', 'NuScale', 'Constellation Energy', 'Radiant', 'Commonwealth Fusion Systems'];
      nuclearCos.forEach(c => nrcCompanies.add(c));
    }
  });
  doe.forEach(d => {
    if (d.companies) d.companies.split(',').forEach(c => nrcCompanies.add(c.trim()));
  });

  // Count FAA actions
  const faaActions = fedReg.filter(r => {
    const ag = (r.agencies || '').toLowerCase();
    return ag.includes('aviation') || ag.includes('faa');
  });
  const faaSectors = ['Space & Aerospace', 'Supersonic & Hypersonic', 'Drones & Autonomous'];

  // FDA companies
  const fdaCompanies = new Set();
  fda.forEach(a => { if (a.company) fdaCompanies.add(a.company); });
  trials.forEach(t => { if (t.sponsor) fdaCompanies.add(t.sponsor); });

  // DOE companies
  const doeCompanies = new Set();
  doe.forEach(d => {
    if (d.companies) d.companies.split(',').forEach(c => doeCompanies.add(c.trim()));
  });

  const agencies = [
    {
      name: 'FDA',
      icon: '💊',
      iconBg: 'rgba(59,130,246,0.15)',
      focus: 'Food and Drug Administration — regulates medical devices, drugs, biologics, and diagnostics. Key pathway for biotech and health tech companies.',
      actionsCount: fda.length + trials.length,
      companiesCount: fdaCompanies.size,
      companies: [...fdaCompanies].slice(0, 8)
    },
    {
      name: 'NRC',
      icon: '⚛️',
      iconBg: 'rgba(34,197,94,0.15)',
      focus: 'Nuclear Regulatory Commission — licenses and regulates nuclear reactors, materials, and waste. Critical for advanced reactor and fusion companies.',
      actionsCount: nrcActions.length,
      companiesCount: nrcCompanies.size,
      companies: [...nrcCompanies].slice(0, 8)
    },
    {
      name: 'FAA',
      icon: '✈️',
      iconBg: 'rgba(249,115,22,0.15)',
      focus: 'Federal Aviation Administration — certifies aircraft, manages airspace, regulates drones and commercial space launches. Gatekeeper for aerospace innovation.',
      actionsCount: faaActions.length,
      companiesCount: faaSectors.length,
      companies: getCompaniesForSectors(faaSectors).slice(0, 8)
    },
    {
      name: 'DOE',
      icon: '⚡',
      iconBg: 'rgba(168,85,247,0.15)',
      focus: 'Department of Energy — funds advanced reactor demos, fusion research, and clean energy programs. Major source of grants and loan guarantees.',
      actionsCount: doe.length,
      companiesCount: doeCompanies.size,
      companies: [...doeCompanies].slice(0, 8)
    }
  ];

  grid.innerHTML = agencies.map(ag => `
    <div class="agency-card">
      <div class="agency-card-header">
        <div class="agency-icon" style="background: ${ag.iconBg}">${ag.icon}</div>
        <div class="agency-card-title">${ag.name}</div>
      </div>
      <div class="agency-card-focus">${ag.focus}</div>
      <div class="agency-card-stats">
        <div class="agency-stat">
          <div class="agency-stat-num">${ag.actionsCount}</div>
          <div class="agency-stat-label">Actions</div>
        </div>
        <div class="agency-stat">
          <div class="agency-stat-num">${ag.companiesCount}</div>
          <div class="agency-stat-label">Companies</div>
        </div>
      </div>
      <div class="agency-companies">
        ${ag.companies.map(c => `<span class="agency-company-tag">${escHtml(c)}</span>`).join('')}
      </div>
    </div>
  `).join('');
}

function getCompaniesForSectors(sectorNames) {
  const companies = getCompanies();
  const result = new Set();
  companies.forEach(c => {
    if (sectorNames.includes(c.sector)) {
      result.add(c.name);
    }
  });
  return [...result];
}

// ─── 5. REGULATORY RISK HEATMAP ───
function initRegRisk() {
  const grid = document.getElementById('reg-risk-grid');
  if (!grid) return;

  const sectors = getSectors();
  const sectorNames = Object.keys(sectors);

  if (sectorNames.length === 0) {
    grid.innerHTML = '<div class="reg-empty-state">No sector data available.</div>';
    return;
  }

  // Assign risk levels based on regulatory exposure
  const riskMap = {
    'Biotech & Health': { level: 'high', reason: 'FDA device/drug approval, clinical trials, HIPAA compliance' },
    'Nuclear Energy': { level: 'high', reason: 'NRC licensing, safety reviews, fuel handling regulations' },
    'Space & Aerospace': { level: 'high', reason: 'FAA certification, ITAR export controls, launch licensing' },
    'Supersonic & Hypersonic': { level: 'high', reason: 'FAA special conditions, sonic boom regulations, military compliance' },
    'Defense & Security': { level: 'high', reason: 'ITAR/EAR export controls, CFIUS review, classified programs' },
    'Drones & Autonomous': { level: 'high', reason: 'FAA Part 107, BVLOS waivers, airspace integration' },
    'Climate & Energy': { level: 'medium', reason: 'DOE programs, EPA standards, grid interconnection rules' },
    'Chips & Semiconductors': { level: 'medium', reason: 'CHIPS Act compliance, export controls, CFIUS review' },
    'AI & Software': { level: 'medium', reason: 'Emerging AI regulations, data privacy laws, algorithmic accountability' },
    'Quantum Computing': { level: 'medium', reason: 'Export controls, national security classification, encryption regulations' },
    'Transportation': { level: 'medium', reason: 'NHTSA standards, DOT regulations, autonomous vehicle permitting' },
    'Robotics & Manufacturing': { level: 'medium', reason: 'OSHA safety standards, import/export controls, industry certifications' },
    'Ocean & Maritime': { level: 'medium', reason: 'Coast Guard regulations, NOAA permits, international maritime law' },
    'Infrastructure & Logistics': { level: 'low', reason: 'Standard permitting, FERC oversight, local zoning compliance' },
    'Housing & Construction': { level: 'low', reason: 'Building codes, local permits, HUD standards' },
    'Consumer Tech': { level: 'low', reason: 'FCC compliance, consumer protection laws, standard product safety' }
  };

  let html = '';
  sectorNames.forEach(name => {
    const s = sectors[name];
    const risk = riskMap[name] || { level: 'low', reason: 'Standard regulatory environment' };
    const levelClass = 'risk-' + risk.level;
    const levelLabel = risk.level.charAt(0).toUpperCase() + risk.level.slice(1);

    html += `
      <div class="risk-card">
        <div class="risk-icon">${s.icon || '📋'}</div>
        <div class="risk-body">
          <div class="risk-sector-name">${escHtml(name)}</div>
          <span class="risk-level-badge ${levelClass}">${levelLabel}</span>
          <div class="risk-reason">${escHtml(risk.reason)}</div>
        </div>
      </div>
    `;
  });

  grid.innerHTML = html;
}

// ─── 6. FEDERAL REGISTER MONITOR ───
let fedRegAllEntries = [];
let fedRegFiltered = [];

function initFedRegisterMonitor() {
  const filtersEl = document.getElementById('fed-register-filters');
  const grid = document.getElementById('fed-register-grid');
  if (!grid) return;

  fedRegAllEntries = getFedRegister();

  if (fedRegAllEntries.length === 0) {
    grid.innerHTML = '<div class="reg-empty-state">No Federal Register data available.</div>';
    return;
  }

  // Collect unique agencies and types
  const agenciesSet = new Set();
  const typesSet = new Set();
  fedRegAllEntries.forEach(r => {
    if (r.agencies) agenciesSet.add(r.agencies);
    if (r.type) typesSet.add(r.type);
  });

  // Render filters
  if (filtersEl) {
    filtersEl.innerHTML = `
      <select class="fed-filter-select" id="fed-agency-filter">
        <option value="all">All Agencies</option>
        ${[...agenciesSet].sort().map(a => `<option value="${escAttr(a)}">${escHtml(truncate(a, 60))}</option>`).join('')}
      </select>
      <select class="fed-filter-select" id="fed-type-filter">
        <option value="all">All Types</option>
        ${[...typesSet].sort().map(t => `<option value="${escAttr(t)}">${escHtml(t)}</option>`).join('')}
      </select>
    `;

    document.getElementById('fed-agency-filter').addEventListener('change', applyFedRegFilters);
    document.getElementById('fed-type-filter').addEventListener('change', applyFedRegFilters);
  }

  applyFedRegFilters();
}

function applyFedRegFilters() {
  const agencyVal = (document.getElementById('fed-agency-filter') || {}).value || 'all';
  const typeVal = (document.getElementById('fed-type-filter') || {}).value || 'all';

  fedRegFiltered = fedRegAllEntries.filter(r => {
    if (agencyVal !== 'all' && r.agencies !== agencyVal) return false;
    if (typeVal !== 'all' && r.type !== typeVal) return false;
    return true;
  });

  // Sort by date newest first
  fedRegFiltered.sort((a, b) => (b.date || '').localeCompare(a.date || ''));

  renderFedRegCards(fedRegFiltered.slice(0, 20));
}

function renderFedRegCards(entries) {
  const grid = document.getElementById('fed-register-grid');
  if (!grid) return;

  if (entries.length === 0) {
    grid.innerHTML = '<div class="reg-empty-state">No entries match the current filters.</div>';
    return;
  }

  grid.innerHTML = entries.map(r => {
    const typeClass = getTypeClass(r.type);
    const sectors = (r.sectors || '').split(',').map(s => s.trim()).filter(Boolean);

    return `
      <div class="fed-register-card">
        <div class="fed-reg-card-header">
          <span class="fed-reg-type-badge ${typeClass}">${escHtml(r.type || 'N/A')}</span>
          <span class="fed-reg-date">${formatDate(r.date)}</span>
        </div>
        <div class="fed-reg-title">${escHtml(truncate(r.title || 'Untitled', 100))}</div>
        <div class="fed-reg-agency">${escHtml(truncate(r.agencies || 'Unknown Agency', 80))}</div>
        ${sectors.length > 0 ? `
          <div class="fed-reg-sectors">
            ${sectors.map(s => `<span class="fed-reg-sector-tag">${escHtml(s)}</span>`).join('')}
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

function getTypeClass(type) {
  switch ((type || '').toLowerCase()) {
    case 'rule': return 'type-rule';
    case 'proposed rule': return 'type-proposed-rule';
    case 'notice': return 'type-notice';
    default: return 'type-notice';
  }
}

// ─── 7. CLINICAL TRIALS DASHBOARD ───
function initClinicalTrials() {
  const grid = document.getElementById('clinical-trials-grid');
  if (!grid) return;

  const trials = getClinicalTrials();

  if (trials.length === 0) {
    grid.innerHTML = '<div class="reg-empty-state">No clinical trials data available.</div>';
    return;
  }

  // Group by sponsor (company)
  const bySponsor = {};
  trials.forEach(t => {
    const sponsor = t.sponsor || 'Unknown';
    if (!bySponsor[sponsor]) bySponsor[sponsor] = [];
    bySponsor[sponsor].push(t);
  });

  // Sort sponsors by number of trials
  const sponsors = Object.keys(bySponsor).sort((a, b) => bySponsor[b].length - bySponsor[a].length);

  grid.innerHTML = sponsors.map((sponsor, idx) => {
    const trials = bySponsor[sponsor];
    // Group by phase
    const byPhase = {};
    trials.forEach(t => {
      const phase = normalizePhase(t.phase);
      if (!byPhase[phase]) byPhase[phase] = [];
      byPhase[phase].push(t);
    });

    // Collect unique phase badges
    const phases = Object.keys(byPhase).sort(phaseSort);

    return `
      <div class="ct-company-card" id="ct-card-${idx}">
        <div class="ct-company-header" onclick="toggleCTCard(${idx})">
          <div class="ct-company-info">
            <span class="ct-company-name">${escHtml(truncate(sponsor, 60))}</span>
            <span class="ct-trial-count">${trials.length} trial${trials.length !== 1 ? 's' : ''}</span>
          </div>
          <div style="display:flex;align-items:center;gap:8px;">
            <div class="ct-phase-badges">
              ${phases.map(p => `<span class="ct-phase-badge ${getPhaseClass(p)}">${escHtml(p)}</span>`).join('')}
            </div>
            <span class="ct-expand-icon">▼</span>
          </div>
        </div>
        <div class="ct-trials-body">
          ${phases.map(phase => `
            <div class="ct-phase-group">
              <div class="ct-phase-group-title">${escHtml(phase)} (${byPhase[phase].length})</div>
              ${byPhase[phase].map(t => renderTrialItem(t)).join('')}
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }).join('');
}

function renderTrialItem(t) {
  const statusClass = getTrialStatusClass(t.status);
  const statusLabel = formatTrialStatus(t.status);

  return `
    <div class="ct-trial-item">
      <div class="ct-trial-title">${escHtml(truncate(t.title || 'Untitled Trial', 120))}</div>
      <div class="ct-trial-meta">
        <span class="ct-trial-status ${statusClass}">${escHtml(statusLabel)}</span>
        <span class="ct-trial-date">${formatDate(t.lastUpdated)}</span>
        <span class="ct-trial-nct">${escHtml(t.nctId || '')}</span>
        ${t.enrollment ? `<span class="ct-trial-enrollment">n=${t.enrollment}</span>` : ''}
      </div>
      ${t.conditions ? `<div class="ct-trial-conditions">${escHtml(truncate(t.conditions, 100))}</div>` : ''}
    </div>
  `;
}

function normalizePhase(phase) {
  if (!phase || phase === 'N/A' || phase === 'NA') return 'N/A';
  // Handle combined phases like "PHASE1, PHASE2"
  return phase
    .replace(/PHASE/gi, 'Phase ')
    .replace(/\s+/g, ' ')
    .replace(/, /g, '/')
    .trim();
}

function phaseSort(a, b) {
  const order = { 'Phase 1': 1, 'Phase 1/Phase 2': 1.5, 'Phase 2': 2, 'Phase 2/Phase 3': 2.5, 'Phase 3': 3, 'N/A': 4 };
  return (order[a] || 5) - (order[b] || 5);
}

function getPhaseClass(phase) {
  if (phase.includes('3')) return 'phase-3';
  if (phase.includes('2')) return 'phase-2';
  if (phase.includes('1')) return 'phase-1';
  return 'phase-na';
}

function getTrialStatusClass(status) {
  switch ((status || '').toUpperCase()) {
    case 'RECRUITING': return 'status-recruiting';
    case 'ACTIVE_NOT_RECRUITING':
    case 'ENROLLING_BY_INVITATION': return 'status-active';
    case 'COMPLETED': return 'status-completed';
    case 'NOT_YET_RECRUITING': return 'status-not-recruiting';
    default: return '';
  }
}

function formatTrialStatus(status) {
  switch ((status || '').toUpperCase()) {
    case 'RECRUITING': return 'Recruiting';
    case 'ACTIVE_NOT_RECRUITING': return 'Active';
    case 'ENROLLING_BY_INVITATION': return 'By Invitation';
    case 'COMPLETED': return 'Completed';
    case 'NOT_YET_RECRUITING': return 'Not Yet Recruiting';
    default: return status || 'Unknown';
  }
}

// Toggle clinical trial card expansion
window.toggleCTCard = function(idx) {
  const card = document.getElementById('ct-card-' + idx);
  if (card) card.classList.toggle('expanded');
};

// ─── MOBILE MENU ───
function initRegMobileMenu() {
  const btn = document.querySelector('.mobile-menu-btn');
  const links = document.querySelector('.nav-links');
  if (!btn || !links) return;

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

// ─── UTILITY FUNCTIONS ───
function escHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

function escAttr(str) {
  return (str || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.substring(0, max) + '...' : str;
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch (e) {
    return dateStr;
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
