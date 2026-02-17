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

document.addEventListener('DOMContentLoaded', () => {
  function initInvestorsPage() {
    function safeInit(fn, name) {
      try { fn(); } catch (e) { console.error('[Investors] ' + (name || fn.name) + ' failed:', e); }
    }

    // Always render all content first
    safeInit(initVCStats);
    safeInit(initVCFilters);
    safeInit(() => renderVCCards(VC_FIRMS), 'renderVCCards');
    safeInit(renderActiveDeployers);
    safeInit(renderCoInvestGraph);
    safeInit(renderOverlapMatrix);
    safeInit(renderFollowOnPatterns);
    safeInit(renderSectorCapital);
    safeInit(initVCModal);
    safeInit(initVCMobileMenu);
    safeInit(initVCSearch);

    // Then apply visual gate if not logged in
    if (typeof TILAuth !== 'undefined' && !TILAuth.isLoggedIn()) {
      showInvestorAuthGate();
    }
  }

  function showInvestorAuthGate() {
    // Gate deeper sections — leave main VC grid visible as a teaser
    const gatedSections = document.querySelectorAll('#active-deployers, #co-invest, #follow-on, #capital-flow');
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
    animateCounterWithPrefix('total-aum', Math.round(totalAum), '$', 'B+');
  }

  let portfolioLinks = 0;
  VC_FIRMS.forEach(f => { portfolioLinks += f.portfolioCompanies.length; });
  animateCounter('portfolio-count', portfolioLinks);
}

function animateCounter(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const duration = 1200;
  const step = target / (duration / 16);
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

function animateCounterWithPrefix(id, target, prefix, suffix) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const duration = 1200;
  const step = target / (duration / 16);
  function tick() {
    current += step;
    if (current >= target) { el.textContent = prefix + target + suffix; return; }
    el.textContent = prefix + Math.floor(current) + suffix;
    requestAnimationFrame(tick);
  }
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) { tick(); observer.disconnect(); }
  });
  observer.observe(el);
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
function renderVCCards(firms) {
  const grid = document.getElementById('vc-grid');
  grid.innerHTML = '';

  firms.forEach((firm, i) => {
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

  // Find overlap with other VCs
  const overlaps = [];
  VC_FIRMS.forEach(other => {
    if (other.shortName === firm.shortName) return;
    const shared = firm.portfolioCompanies.filter(c => other.portfolioCompanies.includes(c));
    if (shared.length > 0) {
      overlaps.push({ firm: other.shortName, companies: shared });
    }
  });

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

  // Build overlap data
  const overlaps = [];
  for (let i = 0; i < VC_FIRMS.length; i++) {
    for (let j = i + 1; j < VC_FIRMS.length; j++) {
      const shared = VC_FIRMS[i].portfolioCompanies.filter(c =>
        VC_FIRMS[j].portfolioCompanies.includes(c)
      );
      if (shared.length > 0) {
        overlaps.push({
          firm1: VC_FIRMS[i].shortName,
          firm2: VC_FIRMS[j].shortName,
          shared: shared,
          count: shared.length
        });
      }
    }
  }

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

  // Build co-investment data
  const coInvestments = [];
  for (let i = 0; i < VC_FIRMS.length; i++) {
    for (let j = i + 1; j < VC_FIRMS.length; j++) {
      const shared = VC_FIRMS[i].portfolioCompanies.filter(c =>
        VC_FIRMS[j].portfolioCompanies.includes(c)
      );
      if (shared.length > 0) {
        coInvestments.push({
          source: VC_FIRMS[i].shortName,
          target: VC_FIRMS[j].shortName,
          weight: shared.length,
          companies: shared
        });
      }
    }
  }

  // Filter to firms with at least one co-investment
  const connectedFirms = new Set();
  coInvestments.forEach(c => {
    connectedFirms.add(c.source);
    connectedFirms.add(c.target);
  });

  const nodes = [...connectedFirms].map(name => {
    const firm = VC_FIRMS.find(f => f.shortName === name);
    return {
      id: name,
      aum: firm ? parseAUM(firm.aum) : 0,
      portfolioSize: firm ? firm.portfolioCompanies.length : 0
    };
  });

  const links = coInvestments.map(c => ({
    source: c.source,
    target: c.target,
    weight: c.weight,
    companies: c.companies
  }));

  // Set dimensions
  const width = container.clientWidth;
  const height = container.clientHeight || 500;

  // Clear previous content
  container.innerHTML = '';

  // Check if D3 is available
  if (typeof d3 === 'undefined') {
    // Load D3 dynamically
    const script = document.createElement('script');
    script.src = 'https://d3js.org/d3.v7.min.js';
    script.onload = () => createForceGraph(container, nodes, links, width, height);
    document.head.appendChild(script);
  } else {
    createForceGraph(container, nodes, links, width, height);
  }
}

function createForceGraph(container, nodes, links, width, height) {
  // Create SVG
  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', [0, 0, width, height]);

  // Add zoom behavior
  const g = svg.append('g');
  svg.call(d3.zoom()
    .scaleExtent([0.5, 3])
    .on('zoom', (event) => {
      g.attr('transform', event.transform);
    }));

  // Create force simulation
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links)
      .id(d => d.id)
      .distance(d => 150 - d.weight * 10)
      .strength(d => 0.1 + d.weight * 0.05))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(50));

  // Draw links
  const link = g.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('class', 'link')
    .attr('stroke-width', d => Math.sqrt(d.weight) * 2);

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
    .attr('r', d => Math.max(15, Math.min(35, 10 + d.portfolioSize * 2)))
    .attr('fill', getComputedStyle(document.documentElement).getPropertyValue('--accent') || '#ff6b35');

  // Add labels to nodes
  node.append('text')
    .text(d => d.id)
    .attr('x', 0)
    .attr('y', d => -Math.max(15, Math.min(35, 10 + d.portfolioSize * 2)) - 5)
    .attr('text-anchor', 'middle')
    .attr('fill', getComputedStyle(document.documentElement).getPropertyValue('--text-secondary') || '#888');

  // Add title for tooltips
  node.append('title')
    .text(d => {
      const firm = VC_FIRMS.find(f => f.shortName === d.id);
      const connections = links.filter(l => l.source.id === d.id || l.target.id === d.id);
      const coInvestors = connections.map(c => c.source.id === d.id ? c.target.id : c.source.id);
      return `${d.id}\n${firm ? firm.aum + ' AUM' : ''}\nCo-invests with: ${coInvestors.join(', ')}`;
    });

  // Handle node click to highlight connections
  node.on('click', function(event, d) {
    event.stopPropagation();
    const connected = new Set();
    connected.add(d.id);
    links.forEach(l => {
      if (l.source.id === d.id) connected.add(l.target.id);
      if (l.target.id === d.id) connected.add(l.source.id);
    });

    node.classed('dimmed', n => !connected.has(n.id));
    link.classed('dimmed', l => l.source.id !== d.id && l.target.id !== d.id);
    link.classed('highlighted', l => l.source.id === d.id || l.target.id === d.id);
  });

  // Click on background to reset
  svg.on('click', () => {
    node.classed('dimmed', false);
    link.classed('dimmed', false);
    link.classed('highlighted', false);
  });

  // Update positions on tick
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

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
