// ═══════════════════════════════════════════════════════
// COMPANY PROFILE PAGE — WORLD-CLASS IMPLEMENTATION
// The single most important page for due diligence
// ═══════════════════════════════════════════════════════

(function() {
  'use strict';

  // Current company data
  let currentCompany = null;
  let hiringChart = null;

  // ─── INITIALIZATION ───
  document.addEventListener('DOMContentLoaded', function() {
    initCompanyProfile();
    initAIAssistant();
  });

  function initCompanyProfile() {
    // Get company from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const companyName = urlParams.get('name') || urlParams.get('company');

    if (!companyName) {
      showError();
      return;
    }

    // Find company in database
    if (typeof COMPANIES === 'undefined') {
      console.error('COMPANIES data not loaded');
      showError();
      return;
    }

    currentCompany = COMPANIES.find(c =>
      c.name.toLowerCase() === companyName.toLowerCase() ||
      c.name.toLowerCase().replace(/\s+/g, '-') === companyName.toLowerCase()
    );

    if (!currentCompany) {
      showError();
      return;
    }

    // Update page title and meta
    document.title = `${currentCompany.name} | The Innovators League`;
    updateMetaTags(currentCompany);

    // Render all sections
    renderHeroSection(currentCompany);
    renderTractionSection(currentCompany);
    renderCompetitiveSection(currentCompany);
    renderIntelligenceSection(currentCompany);
    renderRelatedSection(currentCompany);
    initActionButtons(currentCompany);

    // Show content
    document.getElementById('profile-loading').style.display = 'none';
    document.getElementById('profile-content').style.display = 'block';
  }

  function showError() {
    document.getElementById('profile-loading').style.display = 'none';
    document.getElementById('profile-error').style.display = 'block';
  }

  function updateMetaTags(company) {
    // Update Open Graph tags
    const ogTitle = document.querySelector('meta[property="og:title"]');
    const ogDesc = document.querySelector('meta[property="og:description"]');
    const twitterTitle = document.querySelector('meta[name="twitter:title"]');
    const metaDesc = document.querySelector('meta[name="description"]');

    if (ogTitle) ogTitle.content = `${company.name} | The Innovators League`;
    if (ogDesc) ogDesc.content = company.description?.substring(0, 160) || '';
    if (twitterTitle) twitterTitle.content = `${company.name} | The Innovators League`;
    if (metaDesc) metaDesc.content = company.description?.substring(0, 160) || '';
  }

  // ═══════════════════════════════════════════════════════
  // SECTION A: EXECUTIVE SUMMARY
  // ═══════════════════════════════════════════════════════

  function renderHeroSection(company) {
    const container = document.getElementById('profile-hero');
    const sectorInfo = typeof SECTORS !== 'undefined' ? SECTORS[company.sector] : { icon: '🏢', color: '#6b7280' };
    const innovatorScore = typeof INNOVATOR_SCORES !== 'undefined' ? INNOVATOR_SCORES[company.name] : null;
    const country = getCountryFromLocation(company);

    // Get score tier info
    let scoreClass = 'promising';
    let scoreTier = 'UNRATED';
    let scoreValue = '--';

    if (innovatorScore) {
      scoreValue = innovatorScore.composite?.toFixed(0) || innovatorScore.total || '--';
      const numScore = parseFloat(scoreValue);
      if (numScore >= 90) { scoreClass = 'elite'; scoreTier = 'ELITE'; }
      else if (numScore >= 80) { scoreClass = 'exceptional'; scoreTier = 'EXCEPTIONAL'; }
      else if (numScore >= 70) { scoreClass = 'strong'; scoreTier = 'STRONG'; }
      else { scoreClass = 'promising'; scoreTier = 'PROMISING'; }
    }

    // Generate one-liner (first sentence of description)
    const oneLiner = company.description?.split('.')[0] + '.' || 'Frontier technology company.';

    container.innerHTML = `
      <div class="hero-top-row">
        <div class="hero-main">
          <div class="hero-badges">
            <span class="sector-badge" style="background:${sectorInfo.color}15; color:${sectorInfo.color}; border: 1px solid ${sectorInfo.color}30;">
              ${sectorInfo.icon} ${company.sector}
            </span>
            ${company.signal ? `<span class="signal-badge-large ${company.signal}">${getSignalIcon(company.signal)} ${company.signal.toUpperCase()}</span>` : ''}
            ${company.tbpnMentioned ? '<span class="signal-badge-large" style="background:#22c55e15; color:#22c55e; border:1px solid #22c55e40;">✓ TBPN Featured</span>' : ''}
          </div>
          <h1 class="company-name-large">${company.name}</h1>
          <p class="company-oneliner">${oneLiner}</p>
          <div class="hero-meta">
            <span class="meta-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              ${company.location || 'Location TBD'}
            </span>
            <span class="meta-divider"></span>
            <span class="meta-item">🌍 ${country}</span>
            ${company.founder ? `<span class="meta-divider"></span><span class="meta-item">👤 ${company.founder}</span>` : ''}
            ${company.founded ? `<span class="meta-divider"></span><span class="meta-item">📅 Est. ${company.founded}</span>` : ''}
          </div>
        </div>
        <div class="hero-score-card">
          <div class="score-card-label">Frontier Index™</div>
          <div class="score-card-value ${scoreClass}">${scoreValue}</div>
          <span class="score-card-tier ${scoreClass}">${scoreTier}</span>
        </div>
      </div>

      <div class="hero-stats-grid">
        ${company.fundingStage ? `<div class="hero-stat"><div class="hero-stat-value">${company.fundingStage}</div><div class="hero-stat-label">Stage</div></div>` : ''}
        ${company.totalRaised ? `<div class="hero-stat"><div class="hero-stat-value">${company.totalRaised}</div><div class="hero-stat-label">Total Raised</div></div>` : ''}
        ${company.valuation ? `<div class="hero-stat"><div class="hero-stat-value">${company.valuation}</div><div class="hero-stat-label">Valuation</div></div>` : ''}
        ${company.employees ? `<div class="hero-stat"><div class="hero-stat-value">${company.employees}</div><div class="hero-stat-label">Employees</div></div>` : ''}
        ${getTRL(company) ? `<div class="hero-stat"><div class="hero-stat-value">TRL ${getTRL(company)}</div><div class="hero-stat-label">Tech Readiness</div></div>` : ''}
      </div>

      ${company.insight ? `
        <div class="ros-take">
          <div class="ros-take-header">
            <span class="ros-take-badge">ROS TAKE</span>
            <span style="color:var(--text-muted); font-size:12px;">Our differentiated analysis</span>
          </div>
          <div class="ros-take-content">${company.insight}</div>
        </div>
      ` : ''}

      ${innovatorScore ? renderScoreBreakdownMini(innovatorScore) : ''}
    `;
  }

  function renderScoreBreakdownMini(score) {
    const dims = [
      { key: 'techMoat', label: 'Tech', color: '#3b82f6', value: score.techMoat || 0 },
      { key: 'momentum', label: 'Momentum', color: '#f59e0b', value: score.momentum || 0 },
      { key: 'teamPedigree', label: 'Team', color: '#8b5cf6', value: score.teamPedigree || 0 },
      { key: 'marketGravity', label: 'Market', color: '#22c55e', value: score.marketGravity || 0 },
      { key: 'govTraction', label: "Gov't", color: '#dc2626', value: score.govTraction || 0 }
    ];

    return `
      <div class="score-breakdown-mini">
        ${dims.map(d => `
          <div class="score-dim-mini">
            <div class="score-dim-mini-bar">
              <div class="score-dim-mini-fill" style="width:${d.value * 10}%; background:${d.color};"></div>
            </div>
            <span class="score-dim-mini-label">${d.label}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  // ═══════════════════════════════════════════════════════
  // SECTION B: EVIDENCE-BACKED TRACTION
  // ═══════════════════════════════════════════════════════

  function renderTractionSection(company) {
    renderFundingHistory(company);
    renderContracts(company);
    renderHiringTrend(company);
    renderMilestones(company);
    renderRevenueIntel(company);
  }

  function renderFundingHistory(company) {
    const container = document.getElementById('funding-history');

    // Get funding rounds from FUNDING_TRACKER
    const rounds = typeof FUNDING_TRACKER !== 'undefined'
      ? FUNDING_TRACKER.filter(f => f.company === company.name).sort((a, b) => new Date(b.date) - new Date(a.date))
      : [];

    if (rounds.length === 0) {
      container.innerHTML = `
        <div class="no-data">
          <p>No funding history available</p>
          ${company.totalRaised ? `<p style="margin-top:8px; color:var(--text);">Total raised: <strong>${company.totalRaised}</strong></p>` : ''}
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="funding-timeline">
        ${rounds.map(round => `
          <div class="funding-round">
            <div class="funding-round-date">${formatDate(round.date)}</div>
            <div class="funding-round-details">
              <div class="funding-round-amount">${round.amount}</div>
              <div class="funding-round-stage">${round.stage || round.type || 'Funding Round'}</div>
              ${round.investor ? `<div class="funding-round-investors">Lead: ${round.investor}</div>` : ''}
              <div class="funding-source">
                <a href="https://www.google.com/search?q=${encodeURIComponent(company.name + ' ' + round.amount + ' funding')}" target="_blank" rel="noopener">Verify →</a>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  function renderContracts(company) {
    const container = document.getElementById('contracts-list');

    // Get contracts from GOV_CONTRACTS
    const contracts = typeof GOV_CONTRACTS !== 'undefined'
      ? GOV_CONTRACTS.filter(c => c.company === company.name).slice(0, 5)
      : [];

    // Also check GOV_CONTRACT_INTEL
    const contractIntel = typeof GOV_CONTRACT_INTEL !== 'undefined'
      ? GOV_CONTRACT_INTEL.find(c => c.company === company.name)
      : null;

    if (contracts.length === 0 && !contractIntel) {
      container.innerHTML = '<div class="no-data"><p>No government contracts on record</p></div>';
      return;
    }

    let html = '';

    if (contractIntel) {
      html += `
        <div class="contract-summary" style="margin-bottom:16px; padding:12px; background:var(--bg); border-radius:8px;">
          <div style="display:flex; gap:16px; flex-wrap:wrap;">
            ${contractIntel.totalContracts ? `<div><strong>${contractIntel.totalContracts}</strong> <span style="color:var(--text-muted); font-size:12px;">Contracts</span></div>` : ''}
            ${contractIntel.agencies ? `<div><strong>${contractIntel.agencies.length}</strong> <span style="color:var(--text-muted); font-size:12px;">Agencies</span></div>` : ''}
            ${contractIntel.clearanceLevel ? `<div><strong>${contractIntel.clearanceLevel}</strong> <span style="color:var(--text-muted); font-size:12px;">Clearance</span></div>` : ''}
          </div>
        </div>
      `;
    }

    if (contracts.length > 0) {
      html += contracts.map(contract => `
        <div class="contract-item">
          <div class="contract-header">
            <span class="contract-agency">${contract.agency || 'Government'}</span>
            <span class="contract-value">${contract.value || 'Undisclosed'}</span>
          </div>
          <div class="contract-description">${contract.description || contract.program || 'Contract details'}</div>
          ${contract.samUrl ? `<a href="${contract.samUrl}" target="_blank" rel="noopener" class="contract-link">View on SAM.gov →</a>` : ''}
        </div>
      `).join('');
    }

    container.innerHTML = html;
  }

  function renderHiringTrend(company) {
    const container = document.getElementById('hiring-details');
    const chartContainer = document.getElementById('hiring-chart-container');

    // Get alt data for hiring info
    const altData = typeof ALT_DATA_SIGNALS !== 'undefined'
      ? ALT_DATA_SIGNALS.find(a => a.company === company.name)
      : null;

    if (!altData) {
      chartContainer.style.display = 'none';
      container.innerHTML = '<div class="no-data"><p>No hiring data available</p></div>';
      return;
    }

    // Render hiring details
    const trendClass = altData.hiringVelocity === 'surging' ? 'hiring-trend-up' :
                       altData.hiringVelocity === 'declining' ? 'hiring-trend-down' : 'hiring-trend-stable';

    container.innerHTML = `
      <div class="hiring-details">
        <span class="hiring-stat">
          <strong>${altData.headcountEstimate || '?'}</strong> employees
        </span>
        <span class="hiring-stat ${trendClass}">
          ${getHiringIcon(altData.hiringVelocity)} ${(altData.hiringVelocity || 'unknown').toUpperCase()}
        </span>
      </div>
      ${altData.keySignal ? `<p style="margin-top:12px; font-size:13px; color:var(--text-muted);">${altData.keySignal}</p>` : ''}
    `;

    // Create mock hiring chart (in production, this would use real data)
    renderHiringChart(company, altData);
  }

  function renderHiringChart(company, altData) {
    const ctx = document.getElementById('hiring-chart');
    if (!ctx) return;

    // Generate mock trend data based on hiring velocity
    const months = ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan'];
    const baseCount = parseInt(altData.headcountEstimate) || 100;
    let data;

    if (altData.hiringVelocity === 'surging') {
      data = months.map((_, i) => Math.round(baseCount * (0.7 + i * 0.06)));
    } else if (altData.hiringVelocity === 'growing') {
      data = months.map((_, i) => Math.round(baseCount * (0.85 + i * 0.03)));
    } else if (altData.hiringVelocity === 'declining') {
      data = months.map((_, i) => Math.round(baseCount * (1.1 - i * 0.03)));
    } else {
      data = months.map(() => Math.round(baseCount * (0.95 + Math.random() * 0.1)));
    }

    if (hiringChart) hiringChart.destroy();

    hiringChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: months,
        datasets: [{
          label: 'Headcount',
          data: data,
          borderColor: '#ff6b2c',
          backgroundColor: 'rgba(255, 107, 44, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointBackgroundColor: '#ff6b2c'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: 'rgba(255,255,255,0.5)', font: { size: 10 } }
          },
          y: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: 'rgba(255,255,255,0.5)', font: { size: 10 } }
          }
        }
      }
    });
  }

  function renderMilestones(company) {
    const container = document.getElementById('milestones-timeline');

    // Get recent event and any milestones
    const milestones = [];

    if (company.recentEvent) {
      milestones.push({
        date: company.recentEvent.date,
        title: company.recentEvent.type?.charAt(0).toUpperCase() + company.recentEvent.type?.slice(1),
        description: company.recentEvent.text
      });
    }

    // Check news for milestones
    if (typeof NEWS_FEED !== 'undefined') {
      const companyNews = NEWS_FEED
        .filter(n => n.companies?.includes(company.name))
        .slice(0, 3)
        .map(n => ({
          date: n.date,
          title: 'News',
          description: n.headline
        }));
      milestones.push(...companyNews);
    }

    if (milestones.length === 0) {
      container.innerHTML = '<div class="no-data"><p>No milestones recorded</p></div>';
      return;
    }

    container.innerHTML = milestones.slice(0, 5).map(m => `
      <div class="milestone-item">
        <span class="milestone-date">${formatDate(m.date)}</span>
        <div class="milestone-content">
          <div class="milestone-title">${m.title}</div>
          <div class="milestone-desc">${m.description}</div>
        </div>
      </div>
    `).join('');
  }

  function renderRevenueIntel(company) {
    const container = document.getElementById('revenue-intel');

    const revenue = typeof REVENUE_INTEL !== 'undefined'
      ? REVENUE_INTEL.find(r => r.company === company.name)
      : null;

    if (!revenue) {
      container.innerHTML = '<div class="no-data"><p>Revenue data not available</p><p style="font-size:12px; color:var(--text-muted); margin-top:4px;">Most private companies don\'t disclose</p></div>';
      return;
    }

    const confidenceLevel = revenue.confidence || 'medium';
    const confidenceWidth = confidenceLevel === 'high' ? 90 : confidenceLevel === 'medium' ? 60 : 30;

    container.innerHTML = `
      <div class="revenue-display">
        <div class="revenue-value">${revenue.revenue}</div>
        <div class="revenue-period">${revenue.period}</div>
        ${revenue.growth ? `<div class="revenue-growth positive">${revenue.growth} growth</div>` : ''}
        <div class="revenue-confidence">
          <div class="confidence-label">Confidence Level</div>
          <div class="confidence-bar">
            <div class="confidence-fill ${confidenceLevel}" style="width:${confidenceWidth}%;"></div>
          </div>
          <p style="font-size:11px; color:var(--text-muted); margin-top:8px;">Source: ${revenue.source || 'Industry estimates'}</p>
        </div>
      </div>
    `;
  }

  // ═══════════════════════════════════════════════════════
  // SECTION C: COMPETITIVE CONTEXT
  // ═══════════════════════════════════════════════════════

  function renderCompetitiveSection(company) {
    renderCompetitors(company);
    renderThesis(company);
    renderMoatEvidence(company);
  }

  function renderCompetitors(company) {
    const container = document.getElementById('competitors-list');

    const competitors = (company.competitors || [])
      .map(name => COMPANIES.find(c => c.name === name))
      .filter(Boolean);

    if (competitors.length === 0) {
      // Find companies in same sector
      const sectorPeers = COMPANIES
        .filter(c => c.sector === company.sector && c.name !== company.name)
        .slice(0, 5);

      if (sectorPeers.length > 0) {
        container.innerHTML = `
          <p style="font-size:13px; color:var(--text-muted); margin-bottom:12px;">Sector peers:</p>
          <div class="competitor-grid">
            ${sectorPeers.map(c => `
              <a href="company.html?name=${encodeURIComponent(c.name)}" class="competitor-chip">
                ${c.name}
              </a>
            `).join('')}
          </div>
        `;
      } else {
        container.innerHTML = '<div class="no-data"><p>No competitors identified</p></div>';
      }
      return;
    }

    container.innerHTML = `
      <div class="competitor-grid">
        ${competitors.map(c => `
          <a href="company.html?name=${encodeURIComponent(c.name)}" class="competitor-chip">
            ${c.name}
            ${c.valuation ? `<span style="color:var(--text-muted); font-size:11px;">${c.valuation}</span>` : ''}
          </a>
        `).join('')}
      </div>
    `;
  }

  function renderThesis(company) {
    const container = document.getElementById('thesis-content');

    if (!company.thesis) {
      container.innerHTML = '<div class="no-data"><p>Investment thesis pending</p></div>';
      return;
    }

    container.innerHTML = `
      ${company.thesis.bull ? `
        <div class="thesis-section">
          <div class="thesis-label bull">🐂 Bull Case</div>
          <p class="thesis-text">${company.thesis.bull}</p>
        </div>
      ` : ''}

      ${company.thesis.bear ? `
        <div class="thesis-section">
          <div class="thesis-label bear">🐻 Bear Case</div>
          <p class="thesis-text">${company.thesis.bear}</p>
        </div>
      ` : ''}

      ${company.thesis.risks && company.thesis.risks.length > 0 ? `
        <div class="thesis-section">
          <div class="thesis-label" style="color:var(--text-muted);">⚠️ Key Risks</div>
          <ul class="risks-list">
            ${company.thesis.risks.map(r => `<li><span class="risk-icon">•</span> ${r}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
    `;
  }

  function renderMoatEvidence(company) {
    const container = document.getElementById('moat-content');

    // Gather moat evidence from various sources
    const patent = typeof PATENT_INTEL !== 'undefined' ? PATENT_INTEL.find(p => p.company === company.name) : null;
    const govContract = typeof GOV_CONTRACT_INTEL !== 'undefined' ? GOV_CONTRACT_INTEL.find(g => g.company === company.name) : null;
    const altData = typeof ALT_DATA_SIGNALS !== 'undefined' ? ALT_DATA_SIGNALS.find(a => a.company === company.name) : null;

    const ipMoat = patent ? { value: `${patent.ipMoatScore}/10`, strength: patent.ipMoatScore >= 7 ? 'strong' : patent.ipMoatScore >= 5 ? 'medium' : 'weak' } : { value: '?', strength: 'weak' };
    const govMoat = govContract ? { value: govContract.totalContracts ? `${govContract.totalContracts} contracts` : 'Active', strength: 'strong' } : { value: 'None', strength: 'weak' };
    const talentMoat = altData?.hiringVelocity === 'surging' ? { value: 'Surging', strength: 'strong' } : altData?.hiringVelocity === 'growing' ? { value: 'Growing', strength: 'medium' } : { value: 'Unknown', strength: 'weak' };

    // Check for supply chain moat (based on sector)
    const supplyMoat = ['Defense & Security', 'Space & Aerospace', 'Nuclear Energy'].includes(company.sector)
      ? { value: 'Strategic', strength: 'strong' }
      : { value: 'Standard', strength: 'medium' };

    container.innerHTML = `
      <div class="moat-grid">
        <div class="moat-item">
          <div class="moat-icon">📜</div>
          <div class="moat-label">IP / Patents</div>
          <div class="moat-value ${ipMoat.strength}">${ipMoat.value}</div>
        </div>
        <div class="moat-item">
          <div class="moat-icon">🏛️</div>
          <div class="moat-label">Gov Contracts</div>
          <div class="moat-value ${govMoat.strength}">${govMoat.value}</div>
        </div>
        <div class="moat-item">
          <div class="moat-icon">🔗</div>
          <div class="moat-label">Supply Chain</div>
          <div class="moat-value ${supplyMoat.strength}">${supplyMoat.value}</div>
        </div>
        <div class="moat-item">
          <div class="moat-icon">👥</div>
          <div class="moat-label">Talent</div>
          <div class="moat-value ${talentMoat.strength}">${talentMoat.value}</div>
        </div>
      </div>
    `;
  }

  // ═══════════════════════════════════════════════════════
  // SECTION D: DEEP INTELLIGENCE
  // ═══════════════════════════════════════════════════════

  function renderIntelligenceSection(company) {
    renderPatentIntel(company);
    renderAltData(company);
    renderFounderNetwork(company);
    renderNewsFeed(company);
  }

  function renderPatentIntel(company) {
    const container = document.getElementById('patent-intel');

    const patent = typeof PATENT_INTEL !== 'undefined' ? PATENT_INTEL.find(p => p.company === company.name) : null;

    if (!patent) {
      container.innerHTML = '<div class="no-data"><p>No patent data available</p></div>';
      return;
    }

    const moatClass = patent.ipMoatScore >= 7 ? 'high' : patent.ipMoatScore >= 5 ? 'mid' : 'low';

    container.innerHTML = `
      <div class="patent-stats">
        <div class="patent-stat">
          <div class="patent-stat-value">${patent.totalPatents}</div>
          <div class="patent-stat-label">Patents</div>
        </div>
        <div class="patent-stat">
          <div class="patent-stat-value">${patent.velocity}</div>
          <div class="patent-stat-label">Filing Rate</div>
        </div>
        <div class="patent-stat">
          <div class="patent-stat-value" style="color:${moatClass === 'high' ? '#22c55e' : moatClass === 'mid' ? '#f59e0b' : '#6b7280'};">${patent.trend || '→'}</div>
          <div class="patent-stat-label">Trend</div>
        </div>
      </div>
      <div class="ip-moat-score">
        <span class="ip-moat-label">IP Moat Score</span>
        <span class="ip-moat-value ${moatClass}">${patent.ipMoatScore}/10</span>
      </div>
      ${patent.techAreas && patent.techAreas.length > 0 ? `
        <div class="patent-areas">
          ${patent.techAreas.map(t => `<span class="patent-area-tag">${t}</span>`).join('')}
        </div>
      ` : ''}
    `;
  }

  function renderAltData(company) {
    const container = document.getElementById('alt-data');

    const altData = typeof ALT_DATA_SIGNALS !== 'undefined' ? ALT_DATA_SIGNALS.find(a => a.company === company.name) : null;

    if (!altData) {
      container.innerHTML = '<div class="no-data"><p>No alternative data signals</p></div>';
      return;
    }

    container.innerHTML = `
      <div class="alt-data-grid">
        <div class="alt-data-item">
          <div class="alt-data-label">Hiring Velocity</div>
          <div class="alt-data-value ${altData.hiringVelocity}">${(altData.hiringVelocity || 'Unknown').toUpperCase()}</div>
        </div>
        <div class="alt-data-item">
          <div class="alt-data-label">Web Traffic</div>
          <div class="alt-data-value ${altData.webTraffic}">${(altData.webTraffic || 'Unknown').toUpperCase()}</div>
        </div>
        <div class="alt-data-item">
          <div class="alt-data-label">News Sentiment</div>
          <div class="alt-data-value">${(altData.newsSentiment || 'Neutral').toUpperCase()}</div>
        </div>
        <div class="alt-data-item">
          <div class="alt-data-label">Signal Strength</div>
          <div class="alt-data-value" style="color:var(--accent);">${altData.signalStrength}/10</div>
        </div>
      </div>
      ${altData.keySignal ? `<p style="margin-top:12px; font-size:13px; color:var(--text-muted); padding:12px; background:var(--bg); border-radius:8px;">${altData.keySignal}</p>` : ''}
    `;
  }

  function renderFounderNetwork(company) {
    const container = document.getElementById('founder-network');

    // Get mafia connections
    const mafias = typeof getCompanyMafias === 'function' ? getCompanyMafias(company.name) : [];

    // Get founder connection info
    const founderConnection = typeof FOUNDER_CONNECTIONS !== 'undefined' ? FOUNDER_CONNECTIONS[company.name] : null;

    if (mafias.length === 0 && !founderConnection) {
      container.innerHTML = '<div class="no-data"><p>No founder network data</p></div>';
      return;
    }

    let html = '';

    if (founderConnection && founderConnection.metFounder) {
      html += `
        <div style="padding:12px; background:linear-gradient(135deg, #ff6b2c10 0%, #ff6b2c05 100%); border:1px solid #ff6b2c30; border-radius:8px; margin-bottom:12px;">
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <span style="background:var(--accent); color:#000; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700;">ROS CONNECTED</span>
          </div>
          ${founderConnection.exclusiveQuote ? `<p style="font-style:italic; font-size:14px;">"${founderConnection.exclusiveQuote}"</p>` : ''}
        </div>
      `;
    }

    if (mafias.length > 0) {
      html += `
        <div class="mafia-list">
          ${mafias.map(m => `
            <div class="mafia-badge-large" style="border-left:3px solid ${m.color};">
              <span class="mafia-icon-large">${m.icon}</span>
              <div class="mafia-info">
                <div class="mafia-name-large">${m.mafia}</div>
                <div class="mafia-detail-large">${m.detail}</div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    container.innerHTML = html;
  }

  function renderNewsFeed(company) {
    const container = document.getElementById('news-feed');

    const news = typeof NEWS_FEED !== 'undefined'
      ? NEWS_FEED.filter(n => n.companies?.includes(company.name) || n.headline?.includes(company.name)).slice(0, 5)
      : [];

    if (news.length === 0) {
      container.innerHTML = '<div class="no-data"><p>No recent news</p></div>';
      return;
    }

    container.innerHTML = `
      <div class="news-list">
        ${news.map(n => `
          <a href="${n.url || '#'}" target="_blank" rel="noopener" class="news-item">
            <div class="news-date">${formatDate(n.date)}</div>
            <div class="news-title">${n.headline}</div>
            ${n.source ? `<div class="news-source">${n.source}</div>` : ''}
          </a>
        `).join('')}
      </div>
    `;
  }

  // ═══════════════════════════════════════════════════════
  // RELATED COMPANIES
  // ═══════════════════════════════════════════════════════

  function renderRelatedSection(company) {
    const container = document.getElementById('related-grid');

    // Get related companies (same sector, excluding current)
    const related = COMPANIES
      .filter(c => c.sector === company.sector && c.name !== company.name)
      .sort(() => Math.random() - 0.5)
      .slice(0, 6);

    if (related.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);">No related companies found</p>';
      return;
    }

    container.innerHTML = related.map(c => {
      const score = typeof INNOVATOR_SCORES !== 'undefined' ? INNOVATOR_SCORES[c.name] : null;
      const scoreValue = score?.composite?.toFixed(0) || score?.total || '--';

      return `
        <a href="company.html?name=${encodeURIComponent(c.name)}" class="related-card">
          <div class="related-card-header">
            <span class="related-card-name">${c.name}</span>
            <span class="related-card-score">${scoreValue}</span>
          </div>
          <p class="related-card-desc">${c.description?.substring(0, 100)}...</p>
        </a>
      `;
    }).join('');
  }

  // ═══════════════════════════════════════════════════════
  // ACTION BUTTONS
  // ═══════════════════════════════════════════════════════

  function initActionButtons(company) {
    // Save button
    const saveBtn = document.getElementById('btn-save');
    if (saveBtn) {
      const isSaved = typeof isBookmarked === 'function' && isBookmarked(company.name);
      if (isSaved) {
        saveBtn.classList.add('saved');
        saveBtn.innerHTML = '<span class="btn-icon">★</span> Saved';
      }
      saveBtn.addEventListener('click', () => {
        if (typeof toggleBookmark === 'function') {
          toggleBookmark(company.name);
          const nowSaved = isBookmarked(company.name);
          saveBtn.classList.toggle('saved', nowSaved);
          saveBtn.innerHTML = nowSaved ? '<span class="btn-icon">★</span> Saved' : '<span class="btn-icon">☆</span> Save to Watchlist';
        }
      });
    }

    // Share button
    const shareBtn = document.getElementById('btn-share');
    if (shareBtn) {
      shareBtn.addEventListener('click', () => {
        const url = window.location.href;
        if (navigator.clipboard) {
          navigator.clipboard.writeText(url).then(() => {
            shareBtn.innerHTML = '<span class="btn-icon">✓</span> Copied!';
            setTimeout(() => {
              shareBtn.innerHTML = '<span class="btn-icon">↗</span> Share Profile';
            }, 2000);
          });
        }
      });
    }

    // Website button
    const websiteBtn = document.getElementById('btn-website');
    if (websiteBtn) {
      const website = typeof getCompanyWebsite === 'function' ? getCompanyWebsite(company.name) : '';
      if (website) {
        websiteBtn.href = website;
      } else {
        websiteBtn.style.display = 'none';
      }
    }

    // Compare button
    const compareBtn = document.getElementById('btn-compare');
    if (compareBtn) {
      compareBtn.addEventListener('click', () => {
        if (typeof toggleCompare === 'function') {
          toggleCompare(company.name);
        }
      });
    }

    // Export button
    const exportBtn = document.getElementById('btn-export');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        if (typeof generateOnePager === 'function') {
          generateOnePager(company.name);
        } else {
          alert('PDF export coming soon!');
        }
      });
    }

    // Update attribution
    const attrUpdated = document.getElementById('attribution-updated');
    if (attrUpdated && typeof DATA_SOURCES !== 'undefined') {
      attrUpdated.textContent = `Last updated: ${DATA_SOURCES.companies?.lastUpdated || 'Unknown'}`;
    }
  }

  // ═══════════════════════════════════════════════════════
  // AI RESEARCH ASSISTANT
  // ═══════════════════════════════════════════════════════

  function initAIAssistant() {
    const fab = document.getElementById('ai-assistant-fab');
    const panel = document.getElementById('ai-assistant-panel');
    const closeBtn = document.getElementById('ai-panel-close');
    const input = document.getElementById('ai-input');
    const sendBtn = document.getElementById('ai-send-btn');
    const chatContainer = document.getElementById('ai-chat');
    const suggestionBtns = document.querySelectorAll('.ai-suggestion-btn');

    if (!fab || !panel) return;

    // Toggle panel
    fab.addEventListener('click', () => {
      panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
      fab.style.display = panel.style.display === 'none' ? 'flex' : 'none';
      if (panel.style.display !== 'none') {
        input.focus();
      }
    });

    closeBtn.addEventListener('click', () => {
      panel.style.display = 'none';
      fab.style.display = 'flex';
    });

    // Suggestion buttons
    suggestionBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const query = btn.dataset.query;
        handleAIQuery(query, chatContainer);
      });
    });

    // Send button
    sendBtn.addEventListener('click', () => {
      const query = input.value.trim();
      if (query) {
        handleAIQuery(query, chatContainer);
        input.value = '';
      }
    });

    // Enter key
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const query = input.value.trim();
        if (query) {
          handleAIQuery(query, chatContainer);
          input.value = '';
        }
      }
    });
  }

  function handleAIQuery(query, chatContainer) {
    if (!currentCompany) return;

    // Add user message
    const userMsg = document.createElement('div');
    userMsg.className = 'ai-message user';
    userMsg.textContent = getQueryDisplayText(query);
    chatContainer.appendChild(userMsg);

    // Add loading message
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'ai-message assistant loading';
    loadingMsg.innerHTML = '<div class="ai-typing-indicator"><span></span><span></span><span></span></div>';
    chatContainer.appendChild(loadingMsg);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Generate response (using local data - in production would call Claude API)
    setTimeout(() => {
      loadingMsg.remove();
      const response = generateAIResponse(query, currentCompany);
      const assistantMsg = document.createElement('div');
      assistantMsg.className = 'ai-message assistant';
      assistantMsg.innerHTML = response;
      chatContainer.appendChild(assistantMsg);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 1000);
  }

  function getQueryDisplayText(query) {
    const queryMap = {
      'summarize': 'Summarize this company',
      'bull-case': "What's the bull case?",
      'bear-case': "What's the bear case?",
      'competitors': 'How do they compare to competitors?',
      'risks': 'What are the key risks?'
    };
    return queryMap[query] || query;
  }

  function generateAIResponse(query, company) {
    // In production, this would call the Claude API
    // For now, generate intelligent responses from available data

    const score = typeof INNOVATOR_SCORES !== 'undefined' ? INNOVATOR_SCORES[company.name] : null;
    const patent = typeof PATENT_INTEL !== 'undefined' ? PATENT_INTEL.find(p => p.company === company.name) : null;
    const altData = typeof ALT_DATA_SIGNALS !== 'undefined' ? ALT_DATA_SIGNALS.find(a => a.company === company.name) : null;

    switch (query) {
      case 'summarize':
        return `<strong>${company.name}</strong> is a ${company.sector} company ${company.location ? `based in ${company.location}` : ''}. ${company.description?.split('.').slice(0, 2).join('.')}.<br><br>` +
          `${company.valuation ? `<strong>Valuation:</strong> ${company.valuation}<br>` : ''}` +
          `${company.totalRaised ? `<strong>Total Raised:</strong> ${company.totalRaised}<br>` : ''}` +
          `${score ? `<strong>Frontier Index:</strong> ${score.composite?.toFixed(0) || score.total}/100` : ''}`;

      case 'bull-case':
        return company.thesis?.bull || `The bull case for ${company.name} centers on their position in the ${company.sector} sector. ${company.insight || 'Further analysis pending.'}`;

      case 'bear-case':
        return company.thesis?.bear || `Key concerns for ${company.name} include market competition and execution risk. ${company.thesis?.risks ? 'Specific risks: ' + company.thesis.risks.join(', ') : ''}`;

      case 'competitors':
        const competitors = company.competitors || [];
        if (competitors.length > 0) {
          return `${company.name} competes with: <strong>${competitors.join(', ')}</strong>.<br><br>` +
            `${company.insight || 'Competitive positioning analysis pending.'}`;
        }
        return `No direct competitors identified in our database. ${company.name} operates in the ${company.sector} sector.`;

      case 'risks':
        if (company.thesis?.risks && company.thesis.risks.length > 0) {
          return `<strong>Key risks for ${company.name}:</strong><br><br>` +
            company.thesis.risks.map(r => `• ${r}`).join('<br>');
        }
        return `Risk assessment for ${company.name} is pending. General sector risks in ${company.sector} include regulatory changes, market competition, and execution risk.`;

      default:
        return `I can help you analyze ${company.name}. Try asking about:<br>` +
          `• Company summary<br>` +
          `• Bull/bear case<br>` +
          `• Competitive landscape<br>` +
          `• Key risks<br><br>` +
          `<em>Note: For more detailed AI analysis, configure your API key in settings.</em>`;
    }
  }

  // ═══════════════════════════════════════════════════════
  // UTILITY FUNCTIONS
  // ═══════════════════════════════════════════════════════

  function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  }

  function getSignalIcon(signal) {
    const icons = { hot: '🔥', rising: '⚡', stealth: '👀', watch: '🔭', established: '✓' };
    return icons[signal] || '';
  }

  function getHiringIcon(velocity) {
    const icons = { surging: '📈', growing: '↗', stable: '→', declining: '↘' };
    return icons[velocity] || '→';
  }

  function getCountryFromLocation(company) {
    if (!company.state && !company.location) return 'Unknown';

    // Use the getCountry function if available
    if (typeof getCountry === 'function') {
      return getCountry(company.state, company.location);
    }

    // Fallback
    const usStates = ['CA', 'TX', 'NY', 'WA', 'MA', 'CO', 'FL', 'VA', 'DC', 'AZ', 'OR'];
    if (usStates.includes(company.state)) return 'United States';

    return company.state || 'Unknown';
  }

  function getTRL(company) {
    // Check TRL data if available
    if (typeof TRL_RANKINGS !== 'undefined') {
      for (const [level, data] of Object.entries(TRL_RANKINGS)) {
        if (data.companies?.includes(company.name)) {
          return level.replace('trl', '');
        }
      }
    }
    return null;
  }

})();
