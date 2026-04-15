// ─── INVESTORS PAGE ───

const SIGNAL_CONFIG_VC = {
  established: { label: 'ESTABLISHED', icon: '✓', class: 'signal-established' },
  rising:      { label: 'RISING', icon: '⚡', class: 'signal-rising' },
  watch:       { label: 'WATCH', icon: '🔭', class: 'signal-watch' }
};

function parseAUM(aum) {
  if (!aum) return 0;
  const m = aum.match(/([\d.]+)\s*(B|M|T)?/i);
  if (!m) return 0;
  let val = parseFloat(m[1]);
  const unit = (m[2] || '').toUpperCase();
  if (unit === 'T') val *= 1000;
  else if (unit === 'M') val *= 0.001;
  return val; // in billions
}

// Pre-compute company -> firms map for efficient overlap detection
const _companyToFirms = new Map();
(typeof VC_FIRMS !== 'undefined' ? VC_FIRMS : []).forEach(firm => {
  (firm.portfolioCompanies || []).forEach(company => {
    if (!_companyToFirms.has(company)) _companyToFirms.set(company, []);
    _companyToFirms.get(company).push(firm.shortName);
  });
});

// For a given firm, find overlapping firms efficiently
function getPortfolioOverlaps(firm) {
  const overlaps = new Map();
  (firm.portfolioCompanies || []).forEach(company => {
    const firms = _companyToFirms.get(company) || [];
    firms.forEach(otherName => {
      if (otherName === firm.shortName) return;
      if (!overlaps.has(otherName)) overlaps.set(otherName, []);
      overlaps.get(otherName).push(company);
    });
  });
  return Array.from(overlaps.entries()).map(([firmName, companies]) => ({
    firm: firmName,
    companies: companies
  }));
}

// Get all pairwise overlaps efficiently (for matrix and graph views)
function getAllPairwiseOverlaps() {
  const pairMap = new Map();
  _companyToFirms.forEach((firms, company) => {
    for (let i = 0; i < firms.length; i++) {
      for (let j = i + 1; j < firms.length; j++) {
        const key = firms[i] < firms[j] ? `${firms[i]}|${firms[j]}` : `${firms[j]}|${firms[i]}`;
        if (!pairMap.has(key)) pairMap.set(key, { firm1: firms[i] < firms[j] ? firms[i] : firms[j], firm2: firms[i] < firms[j] ? firms[j] : firms[i], shared: [] });
        pairMap.get(key).shared.push(company);
      }
    }
  });
  return Array.from(pairMap.values()).map(o => ({ ...o, count: o.shared.length }));
}

document.addEventListener('DOMContentLoaded', () => {
  function initInvestorsPage() {
    // Always render all content first
    safeInit(initVCStats);
    safeInit(initVCFilters);
    safeInit(() => renderVCCards(VC_FIRMS), 'renderVCCards');
    safeInit(renderActiveDeployers);
    safeInit(renderCoInvestGraph);
    safeInit(renderOverlapMatrix);
    safeInit(renderFollowOnPatterns);
    safeInit(renderConvictionTracker);
    safeInit(renderSectorCapital);
    safeInit(renderPortfolioXRay);
    safeInit(initVCModal);
    safeInit(initVCMobileMenu);
    safeInit(initVCSearch);
    safeInit(initSectionObserver, 'initSectionObserver');

    // Auth gating disabled — all investor data open while site is pre-launch
  }

  function showInvestorAuthGate() {
    // Gate deeper sections — leave main VC grid visible as a teaser
    const gatedSections = document.querySelectorAll('#active-deployers, #co-invest, #follow-on, #conviction-tracker, #capital-flow');
    gatedSections.forEach(s => s.classList.add('section-gated'));

    // Add sign-in CTA between free content and gated content
    const vcSection = document.getElementById('vc-section');
    if (vcSection) {
      const cta = document.createElement('div');
      cta.className = 'investor-gate-banner';
      cta.innerHTML = `
        <div class="investor-gate-content">
          <span class="investor-gate-icon">🔒</span>
          <div>
            <strong>Sign in free to unlock full Investor Intelligence</strong>
            <p>Co-investment networks, follow-on patterns, capital flow analysis and more.</p>
          </div>
          <button class="gate-cta-btn" onclick="TILAuth.showAuthModal()">Sign In Free</button>
        </div>
      `;
      vcSection.insertAdjacentElement('afterend', cta);
    }
  }

  // Listen for auth changes to unlock content
  window.addEventListener('til-auth-change', (e) => {
    if (e.detail?.user) {
      document.querySelectorAll('.section-gated').forEach(s => s.classList.remove('section-gated'));
      document.querySelectorAll('.investor-gate-banner').forEach(c => c.remove());
    }
  });

  if (typeof TILAuth !== 'undefined' && TILAuth.onReady) {
    TILAuth.onReady(initInvestorsPage);
  } else {
    initInvestorsPage();
  }
});

// ─── STATS ───
function initVCStats() {
  const count = VC_FIRMS.length;
  animateCounter('vc-count', count);

  let totalAum = 0;
  VC_FIRMS.forEach(f => { totalAum += parseAUM(f.aum); });
  const aumEl = document.getElementById('total-aum');
  if (aumEl) {
    animateCounter('total-aum', Math.round(totalAum), { prefix: '$', suffix: 'B+' });
  }

  let portfolioLinks = 0;
  VC_FIRMS.forEach(f => { portfolioLinks += f.portfolioCompanies.length; });
  animateCounter('portfolio-count', portfolioLinks);
}

// ─── FILTERS ───
function initVCFilters() {
  // Sector filter — collect unique sector focuses
  const allSectors = new Set();
  VC_FIRMS.forEach(f => f.sectorFocus.forEach(s => allSectors.add(s)));
  const sectorFilter = document.getElementById('vc-sector-filter');
  [...allSectors].sort().forEach(s => {
    const opt = document.createElement('option');
    opt.value = s;
    opt.textContent = s;
    sectorFilter.appendChild(opt);
  });

  sectorFilter.addEventListener('change', applyVCFilters);
  document.getElementById('vc-sort').addEventListener('change', applyVCFilters);
}

function initVCSearch() {
  const input = document.getElementById('vc-search');
  let debounce;
  input.addEventListener('input', () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => applyVCFilters(), 200);
  });
}

function applyVCFilters() {
  const sector = document.getElementById('vc-sector-filter').value;
  const sortBy = document.getElementById('vc-sort').value;
  const searchTerm = document.getElementById('vc-search').value.toLowerCase();

  let filtered = [...VC_FIRMS];

  if (sector && sector !== 'all') {
    filtered = filtered.filter(f => f.sectorFocus.includes(sector));
  }

  if (searchTerm) {
    filtered = filtered.filter(f =>
      f.name.toLowerCase().includes(searchTerm) ||
      f.shortName.toLowerCase().includes(searchTerm) ||
      f.thesis.toLowerCase().includes(searchTerm) ||
      f.keyPartners.some(p => p.toLowerCase().includes(searchTerm)) ||
      f.portfolioCompanies.some(c => c.toLowerCase().includes(searchTerm)) ||
      f.hq.toLowerCase().includes(searchTerm)
    );
  }

  // Sort
  if (sortBy === 'aum') {
    filtered.sort((a, b) => parseAUM(b.aum) - parseAUM(a.aum));
  } else if (sortBy === 'name') {
    filtered.sort((a, b) => a.shortName.localeCompare(b.shortName));
  } else if (sortBy === 'founded') {
    filtered.sort((a, b) => a.founded - b.founded);
  } else if (sortBy === 'portfolio') {
    filtered.sort((a, b) => b.portfolioCompanies.length - a.portfolioCompanies.length);
  }

  renderVCCards(filtered);
}

// ─── RENDER VC CARDS ───
const VC_INITIAL_COUNT = 20;
const VC_STEP_SIZE = 20;
let vcShownCount = VC_INITIAL_COUNT;
let lastRenderedFirms = null;

function renderVCCards(firms) {
  const grid = document.getElementById('vc-grid');
  grid.innerHTML = '';

  if (lastRenderedFirms !== firms) {
    vcShownCount = VC_INITIAL_COUNT;
    lastRenderedFirms = firms;
  }

  const total = firms.length;
  const visibleFirms = firms.slice(0, vcShownCount);

  visibleFirms.forEach((firm, i) => {
    const card = document.createElement('div');
    card.className = 'vc-card';
    card.style.animationDelay = `${i * 0.03}s`;

    const signalInfo = SIGNAL_CONFIG_VC[firm.signal] || {};
    const signalBadge = firm.signal && signalInfo.label
      ? `<span class="signal-badge ${signalInfo.class}">${signalInfo.icon} ${signalInfo.label}</span>`
      : '';

    // Portfolio chips — link to main site if company exists in COMPANIES
    const portfolioChips = firm.portfolioCompanies.map(name => {
      const exists = typeof COMPANIES !== 'undefined' && COMPANIES.find(c => c.name === name);
      if (exists) {
        return `<a href="index.html?company=${encodeURIComponent(name)}" class="portfolio-chip linked" title="View ${name} profile">${name}</a>`;
      }
      return `<span class="portfolio-chip">${name}</span>`;
    }).join('');

    const sectorBadges = firm.sectorFocus.map(s => `<span class="vc-sector-tag">${s}</span>`).join('');

    card.innerHTML = `
      <div class="vc-card-header">
        <div>
          <h3 class="vc-card-name">${firm.shortName}</h3>
          <p class="vc-card-fullname">${firm.name}</p>
        </div>
        <div class="vc-card-aum">${firm.aum}</div>
      </div>
      <div class="vc-card-meta">
        <span class="vc-meta-item">📍 ${firm.hq}</span>
        <span class="vc-meta-item">📅 Est. ${firm.founded}</span>
        ${signalBadge}
      </div>
      <div class="vc-card-thesis">"${firm.thesis.substring(0, 180)}${firm.thesis.length > 180 ? '...' : ''}"</div>
      <div class="vc-card-section">
        <h4>Key Partners</h4>
        <p class="vc-partners">${firm.keyPartners.join(' · ')}</p>
      </div>
      <div class="vc-card-section">
        <h4>Sector Focus</h4>
        <div class="vc-sector-tags">${sectorBadges}</div>
      </div>
      <div class="vc-card-section">
        <h4>Portfolio Companies <span class="portfolio-count">${firm.portfolioCompanies.length}</span></h4>
        <div class="vc-portfolio-chips">${portfolioChips}</div>
      </div>
      <div class="vc-card-footer">
        <button class="vc-detail-btn" onclick="event.stopPropagation(); openVCModal('${firm.shortName.replace(/'/g, "\\'")}')">Full Profile →</button>
        <a href="${firm.website}" target="_blank" rel="noopener" class="vc-website-btn" onclick="event.stopPropagation()">Website ↗</a>
      </div>
    `;

    card.addEventListener('click', () => openVCModal(firm.shortName));
    card.style.cursor = 'pointer';
    grid.appendChild(card);
  });

  // Pagination controls
  if (total > VC_INITIAL_COUNT) {
    const remaining = total - vcShownCount;
    const actions = document.createElement('div');
    actions.className = 'paginated-list-actions';
    if (remaining > 0) {
      const nextBatch = Math.min(VC_STEP_SIZE, remaining);
      actions.innerHTML = `<button class="show-more-btn" type="button" data-vc-action="show-more">Show ${nextBatch} more firms <span class="show-more-count">(${remaining} remaining)</span></button>`;
    } else {
      actions.innerHTML = `<button class="show-more-btn show-less-btn" type="button" data-vc-action="show-less">Show less</button>`;
    }
    grid.appendChild(actions);
    const btn = actions.querySelector('[data-vc-action]');
    if (btn) {
      btn.addEventListener('click', () => {
        if (btn.getAttribute('data-vc-action') === 'show-more') {
          vcShownCount = Math.min(vcShownCount + VC_STEP_SIZE, total);
        } else {
          vcShownCount = VC_INITIAL_COUNT;
          grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        const cached = lastRenderedFirms;
        lastRenderedFirms = null;
        renderVCCards(cached);
        lastRenderedFirms = cached;
      });
    }
  }
}

// ─── VC MODAL ───
function initVCModal() {
  const overlay = document.getElementById('vc-modal-overlay');
  const closeBtn = document.getElementById('vc-modal-close');

  closeBtn.addEventListener('click', closeVCModal);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeVCModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeVCModal();
  });
}

function openVCModal(shortName) {
  const firm = VC_FIRMS.find(f => f.shortName === shortName);
  if (!firm) return;

  const body = document.getElementById('vc-modal-body');
  const signalInfo = SIGNAL_CONFIG_VC[firm.signal] || {};
  const signalBadge = firm.signal && signalInfo.label
    ? `<span class="signal-badge ${signalInfo.class}">${signalInfo.icon} ${signalInfo.label}</span>`
    : '';

  // Find overlap with other VCs (using pre-computed map)
  const overlaps = getPortfolioOverlaps(firm);

  const portfolioChips = firm.portfolioCompanies.map(name => {
    const exists = typeof COMPANIES !== 'undefined' && COMPANIES.find(c => c.name === name);
    if (exists) {
      return `<a href="index.html?company=${encodeURIComponent(name)}" class="portfolio-chip linked">${name}</a>`;
    }
    return `<span class="portfolio-chip">${name}</span>`;
  }).join('');

  body.innerHTML = `
    <div class="vc-modal-header">
      <div>
        <h2>${firm.name} ${signalBadge}</h2>
        <p class="vc-modal-meta">📍 ${firm.hq} · Est. ${firm.founded} · AUM: ${firm.aum}</p>
      </div>
    </div>

    <div class="vc-modal-stats">
      <div class="modal-stat">
        <span class="modal-stat-label">AUM</span>
        <span class="modal-stat-value">${firm.aum}</span>
      </div>
      <div class="modal-stat">
        <span class="modal-stat-label">Founded</span>
        <span class="modal-stat-value">${firm.founded}</span>
      </div>
      <div class="modal-stat">
        <span class="modal-stat-label">Flagship</span>
        <span class="modal-stat-value">${firm.flagshipFund}</span>
      </div>
      <div class="modal-stat">
        <span class="modal-stat-label">Portfolio</span>
        <span class="modal-stat-value">${firm.portfolioCompanies.length} companies</span>
      </div>
    </div>

    <div class="vc-modal-section">
      <h3>Investment Thesis</h3>
      <p class="vc-thesis-full">${firm.thesis}</p>
    </div>

    <div class="vc-modal-section">
      <h3>ROS Intelligence</h3>
      <div class="modal-insight">
        <div class="modal-insight-label">Analyst View</div>
        ${firm.insight}
      </div>
    </div>

    <div class="vc-modal-section">
      <h3>Key Partners</h3>
      <div class="vc-partners-grid">
        ${firm.keyPartners.map(p => `<div class="vc-partner-chip">${p}</div>`).join('')}
      </div>
    </div>

    <div class="vc-modal-section">
      <h3>Sector Focus</h3>
      <div class="vc-sector-tags">
        ${firm.sectorFocus.map(s => `<span class="vc-sector-tag">${s}</span>`).join('')}
      </div>
    </div>

    <div class="vc-modal-section">
      <h3>Portfolio Companies</h3>
      <div class="vc-portfolio-chips">${portfolioChips}</div>
    </div>

    ${overlaps.length > 0 ? `
      <div class="vc-modal-section">
        <h3>Co-Investment Network</h3>
        <div class="vc-overlaps">
          ${overlaps.map(o => `
            <div class="vc-overlap-item">
              <span class="overlap-firm">${o.firm}</span>
              <span class="overlap-shared">${o.companies.join(', ')}</span>
            </div>
          `).join('')}
        </div>
      </div>
    ` : ''}

    <div class="vc-modal-actions">
      <a href="${firm.website}" target="_blank" rel="noopener" class="modal-action-btn primary">
        Visit Website
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>
      </a>
    </div>
  `;

  document.getElementById('vc-modal-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeVCModal() {
  document.getElementById('vc-modal-overlay').classList.remove('active');
  document.body.style.overflow = '';
}

// ─── OVERLAP MATRIX ───
function renderOverlapMatrix() {
  const container = document.getElementById('overlap-matrix');
  if (!container) return;

  // Build overlap data (using pre-computed map)
  const overlaps = getAllPairwiseOverlaps();
  overlaps.sort((a, b) => b.count - a.count);

  if (overlaps.length === 0) {
    container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 40px;">No co-investment overlaps detected.</p>';
    return;
  }

  container.innerHTML = `
    <div class="overlap-cards">
      ${overlaps.slice(0, 20).map(o => `
        <div class="overlap-card">
          <div class="overlap-firms">
            <span class="overlap-firm-name">${o.firm1}</span>
            <span class="overlap-connector">×</span>
            <span class="overlap-firm-name">${o.firm2}</span>
          </div>
          <div class="overlap-count">${o.count} shared</div>
          <div class="overlap-companies">
            ${o.shared.map(c => `<span class="portfolio-chip small">${c}</span>`).join('')}
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

// ─── SECTOR CAPITAL ───
function renderSectorCapital() {
  const container = document.getElementById('sector-capital-grid');
  if (!container) return;

  // Count VC focus by sector
  const sectorCounts = {};
  VC_FIRMS.forEach(f => {
    f.sectorFocus.forEach(s => {
      if (!sectorCounts[s]) sectorCounts[s] = { count: 0, firms: [], totalAUM: 0 };
      sectorCounts[s].count++;
      sectorCounts[s].firms.push(f.shortName);
      sectorCounts[s].totalAUM += parseAUM(f.aum);
    });
  });

  const sorted = Object.entries(sectorCounts).sort((a, b) => b[1].totalAUM - a[1].totalAUM);

  container.innerHTML = sorted.map(([sector, data]) => {
    const maxAUM = sorted[0][1].totalAUM;
    const barWidth = Math.max(15, (data.totalAUM / maxAUM) * 100);

    return `
      <div class="sector-capital-card">
        <div class="sector-capital-header">
          <h4>${sector}</h4>
          <span class="sector-capital-aum">$${Math.round(data.totalAUM)}B+ combined</span>
        </div>
        <div class="sector-capital-bar-bg">
          <div class="sector-capital-bar" style="width: ${barWidth}%"></div>
        </div>
        <div class="sector-capital-firms">
          <span class="sector-capital-count">${data.count} firms:</span>
          ${data.firms.map(f => `<span class="sector-firm-tag">${f}</span>`).join('')}
        </div>
      </div>
    `;
  }).join('');
}

// ─── ACTIVE DEPLOYERS ───
function renderActiveDeployers() {
  const container = document.getElementById('active-deployers-grid');
  if (!container || typeof DEAL_TRACKER === 'undefined') return;

  // Group deals by investor and sort by date
  const investorDeals = {};
  DEAL_TRACKER.forEach(deal => {
    if (!investorDeals[deal.investor]) {
      investorDeals[deal.investor] = [];
    }
    investorDeals[deal.investor].push(deal);
  });

  // Sort each investor's deals by date (most recent first)
  Object.keys(investorDeals).forEach(investor => {
    investorDeals[investor].sort((a, b) => b.date.localeCompare(a.date));
  });

  // Rank investors by most recent activity + deal count
  const rankedInvestors = Object.entries(investorDeals)
    .map(([investor, deals]) => ({
      investor,
      deals,
      mostRecent: deals[0].date,
      totalDeals: deals.length
    }))
    .sort((a, b) => {
      // First by most recent date, then by deal count
      const dateCompare = b.mostRecent.localeCompare(a.mostRecent);
      if (dateCompare !== 0) return dateCompare;
      return b.totalDeals - a.totalDeals;
    })
    .slice(0, 8); // Top 8 most active

  container.innerHTML = rankedInvestors.map(({ investor, deals }) => {
    const recentDeals = deals.slice(0, 3);
    return `
      <div class="active-deployer-card">
        <div class="deployer-header">
          <span class="deployer-name">${investor}</span>
          <span class="deployer-count">${deals.length} deal${deals.length > 1 ? 's' : ''}</span>
        </div>
        <div class="deployer-deals">
          ${recentDeals.map(deal => `
            <div class="deployer-deal">
              <span class="deal-company">${deal.company}</span>
              <div class="deal-meta">
                <span class="deal-amount">${deal.amount}</span>
                <span class="deal-round">${deal.round}</span>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }).join('');
}

// ─── CO-INVESTMENT NETWORK GRAPH ───
function renderCoInvestGraph() {
  const container = document.getElementById('co-invest-graph');
  if (!container) return;

  // Build co-investment data (using pre-computed map)
  const pairOverlaps = getAllPairwiseOverlaps();
  const coInvestments = pairOverlaps.map(o => ({
    source: o.firm1,
    target: o.firm2,
    weight: o.count,
    companies: o.shared
  }));

  // Filter to firms with at least one co-investment
  const connectedFirms = new Set();
  coInvestments.forEach(c => {
    connectedFirms.add(c.source);
    connectedFirms.add(c.target);
  });

  if (connectedFirms.size === 0) {
    container.innerHTML = '<div class="graph-loading"><span>No co-investment connections found.</span></div>';
    return;
  }

  const nodes = [...connectedFirms].map(name => {
    const firm = VC_FIRMS.find(f => f.shortName === name);
    return {
      id: name,
      aum: firm ? parseAUM(firm.aum) : 0,
      portfolioSize: firm ? firm.portfolioCompanies.length : 0,
      hq: firm ? firm.hq : '',
      aumStr: firm ? firm.aum : ''
    };
  });

  const links = coInvestments.map(c => ({
    source: c.source,
    target: c.target,
    weight: c.weight,
    companies: c.companies
  }));

  if (typeof d3 === 'undefined') {
    container.innerHTML = '<div class="graph-loading"><span>D3 library failed to load. Refresh the page.</span></div>';
    return;
  }

  // Wait for container to be visible and have dimensions
  function tryCreateGraph() {
    const width = container.clientWidth;
    const height = container.clientHeight || 500;
    if (width < 100) {
      setTimeout(tryCreateGraph, 200);
      return;
    }
    container.innerHTML = '';
    createForceGraph(container, nodes, links, width, height);
  }

  // Use IntersectionObserver to only render when visible
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        tryCreateGraph();
        observer.disconnect();
      }
    }, { threshold: 0.1 });
    observer.observe(container);
  } else {
    tryCreateGraph();
  }
}

function createForceGraph(container, nodes, links, width, height) {
  // Accent color
  const accent = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#ff6b35';

  // Color scale for nodes by AUM
  const maxAUM = Math.max(...nodes.map(n => n.aum), 1);
  const colorScale = d3.scaleLinear()
    .domain([0, maxAUM * 0.3, maxAUM])
    .range(['#60a5fa', accent, '#ef4444']);

  // Create SVG
  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', [0, 0, width, height]);

  // Defs for glow filter
  const defs = svg.append('defs');
  const filter = defs.append('filter').attr('id', 'glow');
  filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
  const feMerge = filter.append('feMerge');
  feMerge.append('feMergeNode').attr('in', 'coloredBlur');
  feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

  // Add zoom behavior
  const g = svg.append('g');
  svg.call(d3.zoom()
    .scaleExtent([0.3, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform);
    }));

  // Create force simulation
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links)
      .id(d => d.id)
      .distance(d => Math.max(80, 180 - d.weight * 20))
      .strength(d => 0.15 + d.weight * 0.05))
    .force('charge', d3.forceManyBody().strength(-400))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => nodeRadius(d) + 15))
    .force('x', d3.forceX(width / 2).strength(0.05))
    .force('y', d3.forceY(height / 2).strength(0.05));

  function nodeRadius(d) {
    return Math.max(16, Math.min(38, 12 + d.portfolioSize * 1.8));
  }

  // Draw links
  const link = g.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('class', 'link')
    .attr('stroke-width', d => Math.max(1.5, Math.sqrt(d.weight) * 2.5));

  // Edge labels showing count
  const edgeLabel = g.append('g')
    .attr('class', 'edge-labels')
    .selectAll('text')
    .data(links)
    .join('text')
    .attr('class', 'edge-label')
    .text(d => d.weight > 1 ? d.weight : '');

  // Create node groups
  const node = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .attr('class', 'node')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended));

  // Add circles to nodes
  node.append('circle')
    .attr('r', d => nodeRadius(d))
    .attr('fill', d => colorScale(d.aum))
    .style('filter', 'url(#glow)');

  // AUM label inside node
  node.append('text')
    .text(d => d.aumStr ? d.aumStr.replace('+', '') : '')
    .attr('x', 0)
    .attr('y', 3)
    .attr('text-anchor', 'middle')
    .attr('fill', '#fff')
    .attr('font-size', d => nodeRadius(d) > 24 ? '8px' : '6px')
    .attr('font-weight', '700')
    .attr('font-family', "'Space Grotesk', sans-serif")
    .style('pointer-events', 'none');

  // Add name labels above nodes
  node.append('text')
    .text(d => d.id)
    .attr('x', 0)
    .attr('y', d => -nodeRadius(d) - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('font-weight', '600');

  // Selected node state
  let selectedNode = null;

  // Handle node click — show info panel
  node.on('click', function(event, d) {
    event.stopPropagation();

    // Toggle selection
    if (selectedNode === d.id) {
      resetHighlights();
      return;
    }
    selectedNode = d.id;

    // Highlight connected nodes and links
    const connected = new Set();
    connected.add(d.id);
    const connectedLinks = [];
    links.forEach(l => {
      const sId = typeof l.source === 'object' ? l.source.id : l.source;
      const tId = typeof l.target === 'object' ? l.target.id : l.target;
      if (sId === d.id) { connected.add(tId); connectedLinks.push(l); }
      if (tId === d.id) { connected.add(sId); connectedLinks.push(l); }
    });

    node.classed('dimmed', n => !connected.has(n.id));
    node.classed('selected', n => n.id === d.id);
    link.classed('dimmed', l => {
      const sId = typeof l.source === 'object' ? l.source.id : l.source;
      const tId = typeof l.target === 'object' ? l.target.id : l.target;
      return sId !== d.id && tId !== d.id;
    });
    link.classed('highlighted', l => {
      const sId = typeof l.source === 'object' ? l.source.id : l.source;
      const tId = typeof l.target === 'object' ? l.target.id : l.target;
      return sId === d.id || tId === d.id;
    });
    edgeLabel.classed('highlighted', l => {
      const sId = typeof l.source === 'object' ? l.source.id : l.source;
      const tId = typeof l.target === 'object' ? l.target.id : l.target;
      return sId === d.id || tId === d.id;
    });

    // Build info panel content
    const firm = VC_FIRMS.find(f => f.shortName === d.id);
    const sortedConns = connectedLinks
      .map(l => {
        const sId = typeof l.source === 'object' ? l.source.id : l.source;
        const tId = typeof l.target === 'object' ? l.target.id : l.target;
        return {
          partner: sId === d.id ? tId : sId,
          count: l.weight,
          companies: l.companies
        };
      })
      .sort((a, b) => b.count - a.count);

    const totalShared = sortedConns.reduce((sum, c) => sum + c.count, 0);

    let html = '<div class="info-panel-firm">' + d.id + '</div>';
    html += '<div class="info-panel-meta">' + (firm ? firm.aum + ' AUM · ' + firm.hq : '') + '</div>';
    html += '<div class="info-panel-section-title">Co-Investment Partners (' + sortedConns.length + ')</div>';

    sortedConns.forEach(conn => {
      html += '<div class="info-panel-connection">';
      html += '<div style="flex:1;min-width:0;">';
      html += '<div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">';
      html += '<span class="info-conn-name">' + conn.partner + '</span>';
      html += '<span class="info-conn-count">' + conn.count + ' shared</span>';
      html += '</div>';
      html += '<div class="info-conn-companies">' + conn.companies.join(', ') + '</div>';
      html += '</div>';
      html += '</div>';
    });

    html += '<div class="info-panel-total">' + totalShared + ' total co-investments across ' + sortedConns.length + ' firms</div>';

    const infoPanel = document.getElementById('co-invest-info');
    const infoContent = document.getElementById('co-invest-info-content');
    if (infoPanel && infoContent) {
      infoContent.innerHTML = html;
      infoPanel.style.display = 'block';
    }
  });

  function resetHighlights() {
    selectedNode = null;
    node.classed('dimmed', false);
    node.classed('selected', false);
    link.classed('dimmed', false);
    link.classed('highlighted', false);
    edgeLabel.classed('highlighted', false);
    const infoPanel = document.getElementById('co-invest-info');
    if (infoPanel) infoPanel.style.display = 'none';
  }

  // Click on background to reset
  svg.on('click', resetHighlights);

  // Close button on info panel
  const closeBtn = document.getElementById('info-panel-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      resetHighlights();
    });
  }

  // Update positions on tick
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

    edgeLabel
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2 - 4);

    node.attr('transform', d => `translate(${d.x},${d.y})`);
  });

  // Drag functions
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }
}

// ─── FOLLOW-ON PATTERNS ───
function renderFollowOnPatterns() {
  const container = document.getElementById('follow-on-grid');
  if (!container || typeof DEAL_TRACKER === 'undefined') return;

  // Build follow-on relationships: when X leads, who follows?
  const leadFollowMap = {};

  // Group deals by company and round
  const dealsByCompanyRound = {};
  DEAL_TRACKER.forEach(deal => {
    const key = `${deal.company}-${deal.round}`;
    if (!dealsByCompanyRound[key]) {
      dealsByCompanyRound[key] = { leads: [], participants: [], company: deal.company, round: deal.round };
    }
    if (deal.leadOrParticipant === 'lead') {
      dealsByCompanyRound[key].leads.push(deal.investor);
    } else {
      dealsByCompanyRound[key].participants.push(deal.investor);
    }
  });

  // For each deal with both leads and participants, track who follows whom
  Object.values(dealsByCompanyRound).forEach(deal => {
    deal.leads.forEach(lead => {
      if (!leadFollowMap[lead]) {
        leadFollowMap[lead] = { followedBy: {}, totalLeads: 0 };
      }
      leadFollowMap[lead].totalLeads++;

      deal.participants.forEach(participant => {
        if (!leadFollowMap[lead].followedBy[participant]) {
          leadFollowMap[lead].followedBy[participant] = { count: 0, companies: [] };
        }
        leadFollowMap[lead].followedBy[participant].count++;
        leadFollowMap[lead].followedBy[participant].companies.push(deal.company);
      });
    });
  });

  // Convert to sorted array and filter to VCs with followers
  const patterns = Object.entries(leadFollowMap)
    .filter(([_, data]) => Object.keys(data.followedBy).length > 0)
    .map(([lead, data]) => ({
      lead,
      totalLeads: data.totalLeads,
      followers: Object.entries(data.followedBy)
        .map(([follower, info]) => ({ follower, ...info }))
        .sort((a, b) => b.count - a.count)
    }))
    .sort((a, b) => {
      const aMax = a.followers.length > 0 ? a.followers[0].count : 0;
      const bMax = b.followers.length > 0 ? b.followers[0].count : 0;
      return bMax - aMax || b.totalLeads - a.totalLeads;
    })
    .slice(0, 6); // Top 6

  if (patterns.length === 0) {
    container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 40px;">Follow-on pattern data requires more deal history.</p>';
    return;
  }

  container.innerHTML = patterns.map(pattern => `
    <div class="follow-on-card">
      <div class="follow-on-header">
        <div>
          <span class="follow-on-lead">${pattern.lead}</span>
          <span class="follow-on-label"> leads → who follows?</span>
        </div>
        <span class="deployer-count">${pattern.totalLeads} lead deals</span>
      </div>
      <div class="follow-on-followers">
        ${pattern.followers.slice(0, 4).map(f => `
          <div class="follower-row">
            <div class="follower-info">
              <span class="follow-on-arrow">→</span>
              <span class="follower-name">${f.follower}</span>
              <span class="follower-count">${f.count}x</span>
            </div>
            <span class="follower-companies" title="${f.companies.join(', ')}">${f.companies.join(', ')}</span>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

// ─── CONVICTION TRACKER ───
function renderConvictionTracker() {
  var leaderboardEl = document.getElementById('ct-leaderboard');
  var validationEl = document.getElementById('ct-validation');
  if (!leaderboardEl || !validationEl) return;
  if (typeof DEAL_TRACKER === 'undefined' || typeof VC_FIRMS === 'undefined') return;

  // ── Name resolution: map DEAL_TRACKER investor → VC_FIRMS shortName ──
  var nameMap = {};
  VC_FIRMS.forEach(function(f) {
    nameMap[f.shortName] = f.shortName;
    nameMap[f.name] = f.shortName;
  });
  // Manual aliases for DEAL_TRACKER names
  var aliases = {
    'Lux Capital': 'Lux',
    'Eclipse Ventures': 'Eclipse',
    'Khosla Ventures': 'Khosla',
    'Sequoia Capital': 'Sequoia',
    'General Catalyst': 'GC',
    'Cantos Ventures': 'Cantos',
    'Riot Ventures': 'Riot',
    'Riot': 'Riot',
    'Prime Movers Lab': 'Prime Movers',
    'Prime Movers': 'Prime Movers',
    'Valor Equity Partners': 'Valor',
    'Valor Equity': 'Valor',
    'Valor': 'Valor',
    'Shield Capital': 'Shield Capital',
    'Shield Capital Partners': 'Shield Capital',
    'Harpoon Ventures': 'Harpoon',
    'Harpoon': 'Harpoon',
    'Bedrock Capital': 'Bedrock',
    'Bedrock': 'Bedrock',
    'Lowercarbon Capital': 'Lowercarbon',
    'Lowercarbon': 'Lowercarbon',
    'DCVC': 'DCVC',
    'Data Collective': 'DCVC',
    'Alumni Ventures': 'AV',
    'AlumniVentures': 'AV'
  };
  Object.keys(aliases).forEach(function(k) { nameMap[k] = aliases[k]; });

  function resolveVC(name) { return nameMap[name] || null; }

  // Build VC_FIRMS lookup by shortName
  var firmLookup = {};
  VC_FIRMS.forEach(function(f) { firmLookup[f.shortName] = f; });

  // ── Step 1: Group DEAL_TRACKER by resolved VC → company ──
  var vcCompanyDeals = {};
  DEAL_TRACKER.forEach(function(deal) {
    var vc = resolveVC(deal.investor);
    if (!vc) return;
    if (!vcCompanyDeals[vc]) vcCompanyDeals[vc] = {};
    if (!vcCompanyDeals[vc][deal.company]) vcCompanyDeals[vc][deal.company] = [];
    vcCompanyDeals[vc][deal.company].push(deal);
  });

  // ── Step 2: Compute conviction signals per VC-company pair ──
  var convictionSignals = [];

  Object.keys(vcCompanyDeals).forEach(function(vc) {
    var firm = firmLookup[vc];
    if (!firm) return;
    var companiesMap = vcCompanyDeals[vc];

    Object.keys(companiesMap).forEach(function(company) {
      var deals = companiesMap[company];
      var inPortfolio = firm.portfolioCompanies && firm.portfolioCompanies.indexOf(company) !== -1;
      var uniqueRounds = [];
      deals.forEach(function(d) { if (uniqueRounds.indexOf(d.round) === -1) uniqueRounds.push(d.round); });
      var roundCount = uniqueRounds.length;
      var isLead = deals.some(function(d) { return d.leadOrParticipant === 'lead'; });
      var sortedDeals = deals.slice().sort(function(a, b) { return b.date.localeCompare(a.date); });
      var latestDeal = sortedDeals[0];

      // Conviction score (1-10)
      var score = 2; // Base: has a tracked deal
      if (inPortfolio) score += 3;
      if (roundCount >= 2) score += 3;
      if (isLead) score += 1;
      if (latestDeal && latestDeal.date >= '2025-09') score += 1;
      if (score > 10) score = 10;

      convictionSignals.push({
        vc: vc,
        company: company,
        deals: sortedDeals,
        inPortfolio: inPortfolio,
        roundCount: roundCount,
        isLead: isLead,
        score: score,
        latestDate: latestDeal ? latestDeal.date : '',
        latestRound: latestDeal ? latestDeal.round : '',
        latestAmount: latestDeal ? latestDeal.amount : ''
      });
    });
  });

  // ── Step 3: VC Conviction Leaderboard ──
  var vcAgg = {};
  convictionSignals.forEach(function(s) {
    if (!vcAgg[s.vc]) vcAgg[s.vc] = { vc: s.vc, totalScore: 0, signals: [] };
    vcAgg[s.vc].totalScore += s.score;
    vcAgg[s.vc].signals.push(s);
  });

  var sortedVCs = Object.keys(vcAgg).map(function(k) { return vcAgg[k]; })
    .filter(function(v) { return v.signals.length >= 1; })
    .sort(function(a, b) { return b.totalScore - a.totalScore || b.signals.length - a.signals.length; })
    .slice(0, 8);

  var maxScore = sortedVCs.length > 0 ? sortedVCs[0].totalScore : 1;

  if (sortedVCs.length === 0) {
    leaderboardEl.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 40px;">Insufficient deal data to compute conviction signals.</p>';
  } else {
    leaderboardEl.innerHTML = '<div class="ct-leaderboard-grid">' + sortedVCs.map(function(vc) {
      var barWidth = Math.max(10, (vc.totalScore / maxScore) * 100);
      var signalsSorted = vc.signals.slice().sort(function(a, b) { return b.score - a.score; }).slice(0, 5);
      return '<div class="ct-vc-card">' +
        '<div class="ct-vc-header">' +
          '<span class="ct-vc-name">' + vc.vc + '</span>' +
          '<span class="ct-vc-score-badge">\uD83D\uDD25 ' + vc.totalScore + ' pts</span>' +
        '</div>' +
        '<div class="ct-vc-meta">' + vc.signals.length + ' conviction position' + (vc.signals.length > 1 ? 's' : '') + ' tracked</div>' +
        '<div class="ct-conviction-bar-bg">' +
          '<div class="ct-conviction-bar" style="width: ' + barWidth + '%;"></div>' +
        '</div>' +
        '<div class="ct-doubles">' +
          signalsSorted.map(function(s) {
            return '<div class="ct-double-row">' +
              '<div>' +
                '<span class="ct-double-company">' + s.company + '</span> ' +
                (s.inPortfolio ? '<span class="ct-portfolio-badge">Portfolio</span>' : '') +
              '</div>' +
              '<div class="ct-double-detail">' +
                '<span class="ct-double-round">' + s.latestRound + '</span>' +
                '<span class="ct-double-role ' + (s.isLead ? 'ct-lead' : 'ct-participant') + '">' + (s.isLead ? 'Lead' : 'Participant') + '</span>' +
              '</div>' +
            '</div>';
          }).join('') +
        '</div>' +
      '</div>';
    }).join('') + '</div>';
  }

  // ── Step 4: Company Validation Radar ──
  var companyAgg = {};
  convictionSignals.forEach(function(s) {
    if (!companyAgg[s.company]) companyAgg[s.company] = { company: s.company, vcs: [] };
    companyAgg[s.company].vcs.push(s);
  });

  var sortedCompanies = Object.keys(companyAgg).map(function(k) { return companyAgg[k]; })
    .filter(function(c) { return c.vcs.length >= 2; })
    .sort(function(a, b) {
      if (b.vcs.length !== a.vcs.length) return b.vcs.length - a.vcs.length;
      var aTotal = a.vcs.reduce(function(sum, v) { return sum + v.score; }, 0);
      var bTotal = b.vcs.reduce(function(sum, v) { return sum + v.score; }, 0);
      return bTotal - aTotal;
    })
    .slice(0, 10);

  if (sortedCompanies.length === 0) {
    validationEl.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 40px;">Insufficient cross-reference data for company validation.</p>';
  } else {
    validationEl.innerHTML = '<div class="ct-validation-grid">' + sortedCompanies.map(function(c) {
      var vcsSorted = c.vcs.slice().sort(function(a, b) { return b.score - a.score; });
      return '<div class="ct-company-card">' +
        '<div class="ct-company-header">' +
          '<span class="ct-company-name">' + c.company + '</span>' +
          '<span class="ct-company-count">' + c.vcs.length + ' committed VC' + (c.vcs.length > 1 ? 's' : '') + '</span>' +
        '</div>' +
        '<div class="ct-company-vcs">' +
          vcsSorted.map(function(v) {
            return '<div class="ct-company-vc-row">' +
              '<span class="ct-company-vc-name">' + v.vc + '</span>' +
              '<div class="ct-company-vc-signals">' +
                (v.inPortfolio ? '<span class="ct-portfolio-badge">Portfolio</span>' : '') +
                '<span class="ct-double-round">' + v.latestRound + '</span>' +
                '<span class="ct-double-role ' + (v.isLead ? 'ct-lead' : 'ct-participant') + '">' + (v.isLead ? 'Lead' : 'Participant') + '</span>' +
              '</div>' +
            '</div>';
          }).join('') +
        '</div>' +
      '</div>';
    }).join('') + '</div>';
  }

  // ── Tab switching ──
  document.querySelectorAll('.ct-tab').forEach(function(tab) {
    tab.addEventListener('click', function() {
      document.querySelectorAll('.ct-tab').forEach(function(t) { t.classList.remove('active'); });
      document.querySelectorAll('.ct-panel').forEach(function(p) { p.classList.remove('active'); });
      tab.classList.add('active');
      var targetId = 'ct-' + tab.getAttribute('data-ct-tab');
      var targetPanel = document.getElementById(targetId);
      if (targetPanel) targetPanel.classList.add('active');
    });
  });
}

// ─── PORTFOLIO X-RAY ───

function renderPortfolioXRay() {
  const grid = document.getElementById('xray-grid');
  if (!grid) return;
  if (typeof VC_FIRMS === 'undefined' || !VC_FIRMS.length) return;

  const COMPANIES = (typeof window.COMPANIES !== 'undefined') ? window.COMPANIES : [];
  const DEAL_TRACKER_DATA = (typeof DEAL_TRACKER !== 'undefined') ? DEAL_TRACKER : [];

  // Helper: parse AUM string to number
  function parseAUM(str) {
    if (!str) return 0;
    const match = str.match(/\$?([\d.]+)\s*([BMTKbmtk])/);
    if (!match) return 0;
    const num = parseFloat(match[1]);
    const unit = match[2].toUpperCase();
    if (unit === 'T') return num * 1e12;
    if (unit === 'B') return num * 1e9;
    if (unit === 'M') return num * 1e6;
    return num;
  }

  // Build per-VC analytics
  const xrayData = VC_FIRMS.map(vc => {
    const portfolioSize = vc.portfolioCompanies ? vc.portfolioCompanies.length : 0;

    // Sector concentration analysis
    const sectorMap = {};
    (vc.portfolioCompanies || []).forEach(compName => {
      const compData = COMPANIES.find(c => c.name === compName);
      if (compData && compData.sector) {
        sectorMap[compData.sector] = (sectorMap[compData.sector] || 0) + 1;
      }
    });
    const sectors = Object.entries(sectorMap)
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({ name, count, pct: Math.round((count / Math.max(portfolioSize, 1)) * 100) }));

    // Top sector concentration (Herfindahl-like)
    const sectorShares = sectors.map(s => s.pct / 100);
    const concentration = sectorShares.reduce((sum, s) => sum + (s * s), 0);
    const concentrationLabel = concentration > 0.5 ? 'Concentrated' : (concentration > 0.25 ? 'Focused' : 'Diversified');

    // Follow-on conviction — did they invest in the same company multiple rounds?
    // Use strict name matching to avoid false positives (e.g. "Light" matching "Lightspeed")
    const followOnMap = {};
    const vcMatchNames = [vc.name.toLowerCase(), vc.shortName.toLowerCase()];
    // Also add common variations (e.g. "Khosla Ventures" for shortName "Khosla")
    if (vc.shortName && vc.name && vc.shortName !== vc.name) {
      vcMatchNames.push(vc.shortName.toLowerCase() + ' ventures');
      vcMatchNames.push(vc.shortName.toLowerCase() + ' capital');
    }
    DEAL_TRACKER_DATA.forEach(deal => {
      if (!deal.investor) return;
      const investorLower = deal.investor.toLowerCase().trim();
      // Require exact match or that deal investor starts with VC name (not substring)
      if (vcMatchNames.some(n => investorLower === n || investorLower.startsWith(n + ' ') || n.startsWith(investorLower + ' ') || investorLower === n.split(' ')[0])) {
        followOnMap[deal.company] = (followOnMap[deal.company] || 0) + 1;
      }
    });
    const followOns = Object.entries(followOnMap)
      .filter(([_, count]) => count > 1)
      .sort((a, b) => b[1] - a[1])
      .map(([company, rounds]) => ({ company, rounds }));

    const followOnRate = portfolioSize > 0 ? Math.round((followOns.length / portfolioSize) * 100) : 0;

    // Stage distribution
    const stageMap = {};
    (vc.portfolioCompanies || []).forEach(compName => {
      const compData = COMPANIES.find(c => c.name === compName);
      if (compData && compData.fundingStage) {
        const stage = compData.fundingStage;
        stageMap[stage] = (stageMap[stage] || 0) + 1;
      }
    });
    const stages = Object.entries(stageMap)
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({ name, count }));

    // White space — sectors in VC_FIRMS sectorFocus but underrepresented in portfolio
    // Dynamically build sector list from ALL VC_FIRMS sectorFocus entries (not hard-coded)
    const allSectors = [...new Set(VC_FIRMS.flatMap(v => v.sectorFocus || []))];
    const whiteSpaces = allSectors.filter(sector => {
      const sectorLower = sector.toLowerCase();
      const inFocus = (vc.sectorFocus || []).some(s => s.toLowerCase() === sectorLower);
      const portfolioCount = sectorMap[sector] || 0;
      return inFocus && portfolioCount <= 1;
    });

    // Co-investment density (using pre-computed map)
    const coInvestCount = getPortfolioOverlaps(vc).length;

    return {
      ...vc,
      portfolioSize,
      sectors,
      concentration,
      concentrationLabel,
      followOns,
      followOnRate,
      stages,
      whiteSpaces,
      coInvestCount,
      aum: vc.aum,
      aumNum: parseAUM(vc.aum)
    };
  }).sort((a, b) => b.aumNum - a.aumNum);

  // Render X-Ray cards
  let html = '';
  xrayData.forEach(vc => {
    // Concentration color
    const concColor = vc.concentrationLabel === 'Concentrated' ? '#f59e0b' :
                      vc.concentrationLabel === 'Focused' ? '#3b82f6' : '#22c55e';

    // Top sectors bars
    let sectorBars = '';
    vc.sectors.slice(0, 3).forEach(s => {
      sectorBars += '<div class="xray-sector-row">' +
        '<span class="xray-sector-name">' + s.name + '</span>' +
        '<div class="xray-sector-bar-track"><div class="xray-sector-bar" style="width:' + s.pct + '%;"></div></div>' +
        '<span class="xray-sector-pct">' + s.pct + '%</span>' +
        '</div>';
    });

    // Follow-on chips
    let followOnHtml = '';
    if (vc.followOns.length > 0) {
      vc.followOns.slice(0, 3).forEach(fo => {
        followOnHtml += '<span class="xray-followon-chip">' + fo.company + ' <em>' + fo.rounds + 'x</em></span>';
      });
    } else {
      followOnHtml = '<span class="xray-no-data">No repeat investments detected</span>';
    }

    // White space chips
    let whiteSpaceHtml = '';
    if (vc.whiteSpaces.length > 0) {
      vc.whiteSpaces.forEach(ws => {
        whiteSpaceHtml += '<span class="xray-whitespace-chip">' + ws + '</span>';
      });
    } else {
      whiteSpaceHtml = '<span class="xray-no-data">Portfolio well-covered</span>';
    }

    // Stage distribution mini chart
    let stageHtml = '';
    vc.stages.slice(0, 4).forEach(s => {
      stageHtml += '<span class="xray-stage-chip">' + s.name + ' <em>(' + s.count + ')</em></span>';
    });

    html += '<div class="xray-card">';
    // Header
    html += '<div class="xray-header">';
    html += '<div class="xray-header-left">';
    html += '<h3 class="xray-vc-name">' + vc.shortName + '</h3>';
    html += '<span class="xray-aum">' + vc.aum + ' AUM</span>';
    html += '</div>';
    html += '<div class="xray-header-right">';
    html += '<span class="xray-portfolio-count">' + vc.portfolioSize + ' companies</span>';
    html += '</div>';
    html += '</div>';

    // Metrics row
    html += '<div class="xray-metrics">';
    html += '<div class="xray-metric"><span class="xray-metric-value" style="color:' + concColor + ';">' + vc.concentrationLabel + '</span><span class="xray-metric-label">Thesis Coherence</span></div>';
    html += '<div class="xray-metric"><span class="xray-metric-value">' + vc.followOnRate + '%</span><span class="xray-metric-label">Follow-On Rate</span></div>';
    html += '<div class="xray-metric"><span class="xray-metric-value">' + vc.coInvestCount + '</span><span class="xray-metric-label">Co-Invest Partners</span></div>';
    html += '</div>';

    // Sector concentration
    html += '<div class="xray-section">';
    html += '<div class="xray-section-title">Sector Concentration</div>';
    html += sectorBars;
    html += '</div>';

    // Follow-on conviction
    html += '<div class="xray-section">';
    html += '<div class="xray-section-title">Follow-On Conviction</div>';
    html += '<div class="xray-chips">' + followOnHtml + '</div>';
    html += '</div>';

    // White space
    html += '<div class="xray-section">';
    html += '<div class="xray-section-title">White Space (Underexposed)</div>';
    html += '<div class="xray-chips">' + whiteSpaceHtml + '</div>';
    html += '</div>';

    // Stage distribution
    if (stageHtml) {
      html += '<div class="xray-section">';
      html += '<div class="xray-section-title">Stage Distribution</div>';
      html += '<div class="xray-chips">' + stageHtml + '</div>';
      html += '</div>';
    }

    html += '</div>';
  });

  grid.innerHTML = html;
}

// ─── MOBILE MENU ───
function initVCMobileMenu() {
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
