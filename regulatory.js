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
  safeInit('FAATracker', initFAACertTracker);
  safeInit('NRCTracker', initNRCLicenseTracker);
  safeInit('RegRisk', initRegRisk);
  safeInit('FedRegisterMonitor', initFedRegisterMonitor);
  safeInit('ClinicalTrialsRadar', initClinicalTrialsRadar);
  safeInit('PDUFACalendar', initPDUFACalendar);
  safeInit('MobileMenu', initRegMobileMenu);
  safeInit('SectionObserver', initSectionObserver);
}

// ─── Clinical Trials Radar — data from data/clinical_trials_active.json (NIH) ───
function initClinicalTrialsRadar() {
  var tbody = document.getElementById('ctr-body');
  var countEl = document.getElementById('ctr-count');
  var searchEl = document.getElementById('ctr-search');
  var phaseEl = document.getElementById('ctr-phase');
  var statusEl = document.getElementById('ctr-status');
  if (!tbody) return;

  var esc = (typeof escapeHtml === 'function') ? escapeHtml : function(s) { return String(s || ''); };

  // Build a set of tracked company names (lowercased) for sponsor matching
  var trackedNames = new Set();
  if (typeof COMPANIES !== 'undefined' && Array.isArray(COMPANIES)) {
    COMPANIES.forEach(function(c) {
      if (c && c.name) trackedNames.add(c.name.toLowerCase());
    });
  }

  function matchSponsorToCompany(sponsor) {
    if (!sponsor) return null;
    var low = sponsor.toLowerCase();
    // Try exact + substring match against tracked companies
    var bestMatch = null;
    trackedNames.forEach(function(name) {
      if (low.indexOf(name) !== -1 && name.length > 3) {
        if (!bestMatch || name.length > bestMatch.length) bestMatch = name;
      }
    });
    return bestMatch;
  }

  function phaseLabel(p) {
    if (!p) return '—';
    return String(p).replace('PHASE', 'Phase ').replace(/,\s*PHASE/g, '/Ph ').replace(/_/g, ' ');
  }

  function statusLabel(s) {
    if (!s) return '—';
    return String(s).replace(/_/g, ' ').toLowerCase().replace(/(^|\s)\w/g, function(c) { return c.toUpperCase(); });
  }

  fetch('data/clinical_trials_active.json', { cache: 'no-cache' })
    .then(function(r) { return r.ok ? r.json() : []; })
    .then(function(data) {
      if (!Array.isArray(data) || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:40px; color:rgba(255,255,255,0.4);">No clinical trial data available.</td></tr>';
        return;
      }

      // Enrich each trial with a matched company name (when sponsor matches)
      var trials = data.map(function(t) {
        var match = matchSponsorToCompany(t.sponsor || '');
        return {
          company: match ? (COMPANIES.find(function(c) { return c.name.toLowerCase() === match; }) || {}).name || t.sponsor : t.sponsor,
          hasMatch: !!match,
          nctId: t.nctId || '',
          title: t.title || '',
          phase: t.phase || '',
          status: t.status || '',
          completion: t.completionDate || '',
          enrollment: t.enrollment || 0,
          sponsor: t.sponsor || ''
        };
      });

      // Prefer matches to tracked companies — show those first
      trials.sort(function(a, b) {
        if (a.hasMatch !== b.hasMatch) return a.hasMatch ? -1 : 1;
        return String(a.completion || 'z').localeCompare(String(b.completion || 'z'));
      });

      function render() {
        var q = (searchEl && searchEl.value || '').trim().toLowerCase();
        var phase = phaseEl && phaseEl.value || 'all';
        var status = statusEl && statusEl.value || 'all';
        var filtered = trials;
        if (q) filtered = filtered.filter(function(t) {
          return (t.company + ' ' + t.title).toLowerCase().indexOf(q) !== -1;
        });
        if (phase !== 'all') filtered = filtered.filter(function(t) { return String(t.phase).indexOf(phase) !== -1; });
        if (status !== 'all') filtered = filtered.filter(function(t) { return t.status === status; });

        if (countEl) {
          var matchedCos = filtered.filter(function(t) { return t.hasMatch; }).length;
          countEl.textContent = 'Showing ' + filtered.length + ' of ' + trials.length + ' trials · ' + matchedCos + ' match tracked companies';
        }

        var dim = '<span style="color:rgba(255,255,255,0.3); font-size:11px; font-style:italic;">—</span>';
        tbody.innerHTML = filtered.slice(0, 500).map(function(t) {
          var nctLink = t.nctId ? '<a href="https://clinicaltrials.gov/study/' + esc(t.nctId) + '" target="_blank" rel="noopener" style="color:var(--accent); text-decoration:none;">' + esc(t.nctId) + '</a>' : dim;
          return '<tr style="' + (t.hasMatch ? '' : 'opacity:0.6;') + '">' +
            '<td style="font-weight:600;">' + esc(t.company) + '</td>' +
            '<td style="font-size:12px;">' + esc((t.title || '').slice(0, 100)) + '</td>' +
            '<td><span class="val-src-badge" style="background:rgba(139,92,246,0.15); color:#a78bfa; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">' + esc(phaseLabel(t.phase)) + '</span></td>' +
            '<td style="font-size:12px;">' + esc(statusLabel(t.status)) + '</td>' +
            '<td>' + (t.enrollment ? esc(t.enrollment) : dim) + '</td>' +
            '<td style="font-family: Space Grotesk, monospace;">' + (t.completion ? esc(t.completion) : dim) + '</td>' +
            '<td>' + nctLink + '</td>' +
          '</tr>';
        }).join('');
      }

      render();
      if (searchEl) searchEl.addEventListener('input', render);
      if (phaseEl) phaseEl.addEventListener('change', render);
      if (statusEl) statusEl.addEventListener('change', render);
    })
    .catch(function(e) {
      console.warn('[ClinicalTrialsRadar] Failed:', e);
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:40px; color:rgba(255,255,255,0.4);">Could not load clinical trial data.</td></tr>';
    });
}

// ─── openFDA PDUFA Calendar — data from data/fda_actions_raw.json ───
function initPDUFACalendar() {
  var tbody = document.getElementById('pdufa-body');
  var countEl = document.getElementById('pdufa-count');
  if (!tbody) return;

  var esc = (typeof escapeHtml === 'function') ? escapeHtml : function(s) { return String(s || ''); };

  fetch('data/fda_actions_raw.json', { cache: 'no-cache' })
    .then(function(r) { return r.ok ? r.json() : []; })
    .then(function(data) {
      if (!Array.isArray(data) || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:40px; color:rgba(255,255,255,0.4);">No FDA action data available.</td></tr>';
        return;
      }

      // Sort by date descending (most recent first)
      var sorted = [...data].sort(function(a, b) {
        return String(b.date || b.decision_date || '').localeCompare(String(a.date || a.decision_date || ''));
      });

      if (countEl) countEl.textContent = 'Showing ' + Math.min(sorted.length, 200) + ' of ' + sorted.length + ' FDA actions';

      var dim = '<span style="color:rgba(255,255,255,0.3); font-size:11px; font-style:italic;">—</span>';
      // Empty-UI rule: only show actions where we have a company name
      var usable = sorted.filter(function(a) { return a.company || a.applicant; });
      tbody.innerHTML = usable.slice(0, 200).map(function(a) {
        var date = a.decision_date || a.date;
        var k = a.k_number || '';
        var kLink = k ? '<a href="https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=' + esc(k) + '" target="_blank" rel="noopener" style="color:var(--accent); text-decoration:none;">' + esc(k) + '</a>' : dim;
        var action = a.clearance_type || a.action || a.decision_code || 'Clearance';
        return '<tr>' +
          '<td style="font-weight:600;">' + esc(a.company || a.applicant) + '</td>' +
          '<td style="font-size:12px;">' + esc((a.device_name || a.product || a.title || '').slice(0, 100)) + '</td>' +
          '<td><span class="val-src-badge" style="background:rgba(34,197,94,0.15); color:#22c55e; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600;">' + esc(action) + '</span></td>' +
          '<td style="font-family: Space Grotesk, monospace;">' + (date ? esc(date) : dim) + '</td>' +
          '<td>' + kLink + '</td>' +
        '</tr>';
      }).join('');
    })
    .catch(function(e) {
      console.warn('[PDUFACalendar] Failed:', e);
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:40px; color:rgba(255,255,255,0.4);">Could not load FDA action data.</td></tr>';
    });
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
      (typeof d.companies === 'string' ? d.companies.split(',') : Array.isArray(d.companies) ? d.companies : []).forEach(c => companySet.add(c.trim()));
    }
  });
  regAnimateCounter('reg-companies', companySet.size);

  // Unique agencies
  const agencySet = new Set();
  fedReg.forEach(r => {
    if (r.agencies) {
      (typeof r.agencies === 'string' ? r.agencies.split(',') : Array.isArray(r.agencies) ? r.agencies : []).forEach(a => agencySet.add(a.trim()));
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
  const dateStr = e.date ? formatDateAbsolute(e.date) : 'No date';
  const companyHtml = e.company ? `<div class="reg-timeline-company">${escapeHtml(e.company)}</div>` : '';
  const descHtml = e.desc ? `<div class="reg-timeline-desc">${escapeHtml(truncate(e.desc, 150))}</div>` : '';

  return `
    <div class="reg-timeline-entry">
      <div class="reg-timeline-dot-col">
        <div class="reg-timeline-dot" style="background: ${e.dotColor}"></div>
        <div class="reg-timeline-line"></div>
      </div>
      <div class="reg-timeline-body">
        <div class="reg-timeline-meta">
          <span class="reg-timeline-date">${dateStr}</span>
          <span class="reg-timeline-badge ${e.badgeClass}">${escapeHtml(e.badgeLabel)}</span>
          <span class="reg-timeline-agency">${escapeHtml(truncate(e.agency, 60))}</span>
        </div>
        <div class="reg-timeline-title">${escapeHtml(truncate(e.title, 120))}</div>
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
        <div class="fda-company-name">${escapeHtml(co)}</div>
        <div class="fda-company-count">${actions.length} FDA action${actions.length !== 1 ? 's' : ''}</div>
        ${renderFDAPipeline(stageIndex)}
        <div class="fda-products-list">
          ${actions.slice(0, 5).map(a => `
            <div class="fda-product-item">
              <span class="fda-product-date">${a.date || 'N/A'}</span>
              <span class="fda-product-name" title="${escapeHtml(a.product || '')}">${escapeHtml(truncate(a.product || 'N/A', 70))}</span>
              <span class="fda-product-status ${getStatusClass(a.status)}">${escapeHtml(a.status || 'N/A')}</span>
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
        ${ag.companies.map(c => `<span class="agency-company-tag">${escapeHtml(c)}</span>`).join('')}
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

// ─── 4b. FAA CERTIFICATION TRACKER ───
function getFAACertData() {
  return (typeof FAA_CERTIFICATION_AUTO !== 'undefined' && Array.isArray(FAA_CERTIFICATION_AUTO)) ? FAA_CERTIFICATION_AUTO : [];
}

function initFAACertTracker() {
  const grid = document.getElementById('faa-grid');
  if (!grid) return;

  const data = getFAACertData();
  if (data.length === 0) {
    grid.innerHTML = '<div class="reg-empty-state">No FAA certification data available.</div>';
    return;
  }

  grid.classList.add('faa-grid');
  grid.innerHTML = data.map(function(entry) {
    var statusBadgeClass = getCertStatusBadgeClass(entry.status);
    var milestonesHtml = (entry.milestones || []).map(function(m) {
      var statusClass = (m.status || 'pending').replace('_', '-');
      var icon = m.status === 'completed' ? '&#x2705;' : m.status === 'in_progress' ? '&#x1F504;' : '&#x23F3;';
      return '<div class="cert-milestone ' + escapeAttr(statusClass) + '">' +
        '<span class="cert-milestone-icon">' + icon + '</span>' +
        '<span class="cert-milestone-date">' + escapeHtml(m.date || '') + '</span>' +
        '<span class="cert-milestone-event">' + escapeHtml(m.event || '') + '</span>' +
      '</div>';
    }).join('');

    var pct = entry.progressPercent || 0;
    var currentMilestone = entry.currentMilestone || 'N/A';
    var subtitle = [entry.certType, entry.category, entry.aircraft].filter(Boolean).join(' &middot; ');

    return '<div class="cert-card">' +
      '<div class="cert-card-header">' +
        '<span class="cert-company-name">' + escapeHtml(entry.company || 'Unknown') + '</span>' +
        '<span class="cert-status-badge ' + statusBadgeClass + '">' + escapeHtml(truncate(entry.status || 'N/A', 32)) + '</span>' +
      '</div>' +
      '<div class="cert-card-subtitle">' + subtitle + '</div>' +
      '<div class="cert-progress"><div class="cert-progress-fill faa-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="cert-progress-label"><span class="cert-progress-pct">' + pct + '%</span><span>Progress</span></div>' +
      '<div class="cert-current-milestone"><strong>Current:</strong> ' + escapeHtml(currentMilestone) + '</div>' +
      '<div class="cert-milestone-timeline">' + milestonesHtml + '</div>' +
      '<div class="cert-meta">' +
        '<span>Updated: ' + formatDateAbsolute(entry.lastUpdated) + '</span>' +
        (entry.note ? '<span>' + escapeHtml(truncate(entry.note, 60)) + '</span>' : '') +
      '</div>' +
    '</div>';
  }).join('');
}

// ─── 4c. NRC LICENSING TRACKER ───
function getNRCLicenseData() {
  return (typeof NRC_LICENSING_AUTO !== 'undefined' && Array.isArray(NRC_LICENSING_AUTO)) ? NRC_LICENSING_AUTO : [];
}

function initNRCLicenseTracker() {
  var grid = document.getElementById('nrc-grid');
  if (!grid) return;

  // Try the new auto-generated file first (from fetch_nrc_licensing.py)
  fetch('data/nrc_licensing_auto.json', { cache: 'no-cache' })
    .then(function(r) { return r.ok ? r.json() : null; })
    .then(function(autoData) {
      if (Array.isArray(autoData) && autoData.length > 0) {
        renderNRCAuto(grid, autoData);
        return;
      }
      renderNRCLegacy(grid);
    })
    .catch(function() { renderNRCLegacy(grid); });
}

function renderNRCAuto(grid, data) {
  var esc = (typeof escapeHtml === 'function') ? escapeHtml : function(s) { return String(s || ''); };
  // Order by stage advancement (most advanced first)
  var stagePriority = {
    'Approved': 6, 'Operating License': 5, 'Construction Permit': 4,
    'Combined License Application': 3, 'Design Certification Application': 2,
    'Pre-application': 1
  };
  data.sort(function(a, b) { return (stagePriority[b.stage] || 0) - (stagePriority[a.stage] || 0); });

  grid.innerHTML = '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:16px;">' +
    data.map(function(entry) {
      var color = (stagePriority[entry.stage] || 0) >= 4 ? '#22c55e' :
                  (stagePriority[entry.stage] || 0) >= 2 ? '#60a5fa' : 'rgba(255,255,255,0.55)';
      return '<div style="padding:18px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:12px;">' +
        '<div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px;">' +
          '<h3 style="color:#fff; font-size:16px; font-weight:700; margin:0;">' + esc(entry.company) + '</h3>' +
          (entry.docketId ? '<span style="color:rgba(255,255,255,0.35); font-size:11px; font-family:Space Grotesk, monospace;">' + esc(entry.docketId) + '</span>' : '') +
        '</div>' +
        '<div style="color:rgba(255,255,255,0.6); font-size:12px; margin-bottom:8px;">' + esc(entry.design || '—') + '</div>' +
        '<div style="padding:6px 10px; border-radius:8px; background:' + color + '22; color:' + color + '; font-size:11px; font-weight:600; display:inline-block; margin-bottom:10px;">' + esc(entry.stage || 'Pre-application') + '</div>' +
        '<div style="font-size:12px; color:rgba(255,255,255,0.7); margin-bottom:6px;"><strong>Status:</strong> ' + esc(entry.status || '—') + '</div>' +
        (entry.nextMilestone ? '<div style="font-size:12px; color:rgba(255,255,255,0.55);"><strong>Next:</strong> ' + esc(entry.nextMilestone) + '</div>' : '') +
        (entry.url ? '<a href="' + esc(entry.url) + '" target="_blank" rel="noopener" style="display:inline-block; margin-top:10px; color:var(--accent); font-size:11px; text-decoration:none;">NRC docket →</a>' : '') +
      '</div>';
    }).join('') +
  '</div>';
}

function renderNRCLegacy(grid) {
  var data = (typeof getNRCLicenseData === 'function') ? getNRCLicenseData() : [];
  if (data.length === 0) {
    grid.innerHTML = '<div class="reg-empty-state">No NRC licensing data available.</div>';
    return;
  }

  grid.classList.add('nrc-grid');
  grid.innerHTML = data.map(function(entry) {
    var statusBadgeClass = getCertStatusBadgeClass(entry.status);
    var milestonesHtml = (entry.milestones || []).map(function(m) {
      var statusClass = (m.status || 'pending').replace('_', '-');
      var icon = m.status === 'completed' ? '&#x2705;' : m.status === 'in_progress' ? '&#x1F504;' : '&#x23F3;';
      return '<div class="cert-milestone ' + escapeAttr(statusClass) + '">' +
        '<span class="cert-milestone-icon">' + icon + '</span>' +
        '<span class="cert-milestone-date">' + escapeHtml(m.date || '') + '</span>' +
        '<span class="cert-milestone-event">' + escapeHtml(m.event || '') + '</span>' +
      '</div>';
    }).join('');

    var pct = entry.progressPercent || 0;
    var subtitle = [entry.reactorType, entry.docketNumber !== 'N/A' ? 'Docket: ' + entry.docketNumber : ''].filter(Boolean).join(' &middot; ');

    return '<div class="cert-card">' +
      '<div class="cert-card-header">' +
        '<span class="cert-company-name">' + escapeHtml(entry.company || 'Unknown') + '</span>' +
        '<span class="cert-status-badge ' + statusBadgeClass + '">' + escapeHtml(truncate(entry.status || 'N/A', 36)) + '</span>' +
      '</div>' +
      '<div class="cert-card-subtitle">' + subtitle + '</div>' +
      '<div class="cert-progress"><div class="cert-progress-fill nrc-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="cert-progress-label"><span class="cert-progress-pct">' + pct + '%</span><span>Progress</span></div>' +
      '<div class="cert-milestone-timeline">' + milestonesHtml + '</div>' +
      '<div class="cert-meta">' +
        (entry.docketNumber && entry.docketNumber !== 'N/A' ? '<span class="cert-docket">Docket #' + escapeHtml(entry.docketNumber) + '</span>' : '<span></span>') +
        '<span>Updated: ' + formatDateAbsolute(entry.lastUpdated) + '</span>' +
      '</div>' +
      (entry.note ? '<div style="font-size:0.75rem;color:rgba(255,255,255,0.35);margin-top:8px;font-style:italic;">' + escapeHtml(truncate(entry.note, 120)) + '</div>' : '') +
    '</div>';
  }).join('');
}

// ─── CERT STATUS BADGE HELPER ───
function getCertStatusBadgeClass(status) {
  if (!status) return 'status-pending';
  var s = status.toLowerCase();
  if (s.includes('approved') || s.includes('active') || s.includes('issued') || s.includes('granted') || s.includes('operating') || s.includes('commercial')) return 'status-approved';
  if (s.includes('review') || s.includes('testing') || s.includes('certification') || s.includes('construction') || s.includes('iterating') || s.includes('resumed') || s.includes('progress') || s.includes('scale')) return 'status-review';
  return 'status-pending';
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
          <div class="risk-sector-name">${escapeHtml(name)}</div>
          <span class="risk-level-badge ${levelClass}">${levelLabel}</span>
          <div class="risk-reason">${escapeHtml(risk.reason)}</div>
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
        ${[...agenciesSet].sort().map(a => `<option value="${escapeAttr(a)}">${escapeHtml(truncate(a, 60))}</option>`).join('')}
      </select>
      <select class="fed-filter-select" id="fed-type-filter">
        <option value="all">All Types</option>
        ${[...typesSet].sort().map(t => `<option value="${escapeAttr(t)}">${escapeHtml(t)}</option>`).join('')}
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
          <span class="fed-reg-type-badge ${typeClass}">${escapeHtml(r.type || 'N/A')}</span>
          <span class="fed-reg-date">${formatDateAbsolute(r.date)}</span>
        </div>
        <div class="fed-reg-title">${escapeHtml(truncate(r.title || 'Untitled', 100))}</div>
        <div class="fed-reg-agency">${escapeHtml(truncate(r.agencies || 'Unknown Agency', 80))}</div>
        ${sectors.length > 0 ? `
          <div class="fed-reg-sectors">
            ${sectors.map(s => `<span class="fed-reg-sector-tag">${escapeHtml(s)}</span>`).join('')}
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

  function sponsorCardHTML(sponsor, idx) {
    const sponsorTrials = bySponsor[sponsor];
    // Group by phase
    const byPhase = {};
    sponsorTrials.forEach(t => {
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
            <span class="ct-company-name">${escapeHtml(truncate(sponsor, 60))}</span>
            <span class="ct-trial-count">${sponsorTrials.length} trial${sponsorTrials.length !== 1 ? 's' : ''}</span>
          </div>
          <div style="display:flex;align-items:center;gap:8px;">
            <div class="ct-phase-badges">
              ${phases.map(p => `<span class="ct-phase-badge ${getPhaseClass(p)}">${escapeHtml(p)}</span>`).join('')}
            </div>
            <span class="ct-expand-icon">▼</span>
          </div>
        </div>
        <div class="ct-trials-body">
          ${phases.map(phase => `
            <div class="ct-phase-group">
              <div class="ct-phase-group-title">${escapeHtml(phase)} (${byPhase[phase].length})</div>
              ${byPhase[phase].map(t => renderTrialItem(t)).join('')}
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  const CT_INITIAL_COUNT = 20;
  const CT_STEP_SIZE = 20;
  let ctShownCount = CT_INITIAL_COUNT;

  function renderCT() {
    const total = sponsors.length;
    const visible = sponsors.slice(0, ctShownCount);
    let html = visible.map((sp, i) => sponsorCardHTML(sp, i)).join('');

    if (total > CT_INITIAL_COUNT) {
      const remaining = total - ctShownCount;
      if (remaining > 0) {
        const nextBatch = Math.min(CT_STEP_SIZE, remaining);
        html += `<div class="paginated-list-actions"><button class="show-more-btn" type="button" data-ct-action="show-more">Show ${nextBatch} more sponsors <span class="show-more-count">(${remaining} remaining)</span></button></div>`;
      } else {
        html += `<div class="paginated-list-actions"><button class="show-more-btn show-less-btn" type="button" data-ct-action="show-less">Show less</button></div>`;
      }
    }

    grid.innerHTML = html;

    const btn = grid.querySelector('[data-ct-action]');
    if (btn) {
      btn.addEventListener('click', () => {
        if (btn.getAttribute('data-ct-action') === 'show-more') {
          ctShownCount = Math.min(ctShownCount + CT_STEP_SIZE, total);
        } else {
          ctShownCount = CT_INITIAL_COUNT;
          grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        renderCT();
      });
    }
  }

  renderCT();
}

function renderTrialItem(t) {
  const statusClass = getTrialStatusClass(t.status);
  const statusLabel = formatTrialStatus(t.status);

  return `
    <div class="ct-trial-item">
      <div class="ct-trial-title">${escapeHtml(truncate(t.title || 'Untitled Trial', 120))}</div>
      <div class="ct-trial-meta">
        <span class="ct-trial-status ${statusClass}">${escapeHtml(statusLabel)}</span>
        <span class="ct-trial-date">${formatDateAbsolute(t.lastUpdated)}</span>
        <span class="ct-trial-nct">${escapeHtml(t.nctId || '')}</span>
        ${t.enrollment ? `<span class="ct-trial-enrollment">n=${t.enrollment}</span>` : ''}
      </div>
      ${t.conditions ? `<div class="ct-trial-conditions">${escapeHtml(truncate(t.conditions, 100))}</div>` : ''}
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
