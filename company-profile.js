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
    // Wait for auth to be ready before initializing
    if (typeof TILAuth !== 'undefined' && TILAuth.onReady) {
      TILAuth.onReady(function() {
        initCompanyProfile();
      });
    } else {
      // Fallback if auth not loaded
      initCompanyProfile();
    }
  });

  function initCompanyProfile() {
    // Get company from URL parameter — support slug, name, and company params
    const urlParams = new URLSearchParams(window.location.search);
    const slug = urlParams.get('slug');
    const companyName = urlParams.get('name') || urlParams.get('company');

    // Find company in database
    if (typeof COMPANIES === 'undefined') {
      console.error('COMPANIES data not loaded');
      showError();
      return;
    }

    // Resolve company from slug or name
    if (slug) {
      currentCompany = COMPANIES.find(c => profileSlug(c.name) === slug.toLowerCase());
    } else if (companyName) {
      currentCompany = COMPANIES.find(c =>
        c.name.toLowerCase() === companyName.toLowerCase() ||
        c.name.toLowerCase().replace(/\s+/g, '-') === companyName.toLowerCase()
      );
    }

    if (!currentCompany) {
      showError();
      return;
    }

    // Auth gating disabled — all company profiles open while site is pre-launch

    // Update page title and meta
    document.title = `${currentCompany.name} | The Innovators League`;
    updateMetaTags(currentCompany);

    // Render all sections
    renderHeroSection(currentCompany);
    renderTractionSection(currentCompany);
    renderCompetitiveSection(currentCompany);
    renderIntelligenceSection(currentCompany);
    renderMarketIntelSection(currentCompany);
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
    const innovatorScore = typeof INNOVATOR_SCORES !== 'undefined' ? INNOVATOR_SCORES.find(s => s.company === company.name) : null;
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
          <div class="company-logo-icon" style="width:72px; height:72px; border-radius:16px; background:${sectorInfo.color}20; border:2px solid ${sectorInfo.color}40; display:flex; align-items:center; justify-content:center; font-size:36px; margin:12px 0;">
            ${sectorInfo.icon}
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
        ${company.valuation ? `<div class="hero-stat"><div class="hero-stat-value">${company.valuation}</div><div class="hero-stat-label">Valuation</div></div>` : `<div class="hero-stat"><div class="hero-stat-value" style="font-size:14px; color:var(--text-muted);">Undisclosed</div><div class="hero-stat-label">Valuation</div></div>`}
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
      const card = document.getElementById('milestones-card');
      if (card) card.style.display = 'none';
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
              <a href="company.html?slug=${profileSlug(c.name)}" class="competitor-chip">
                ${c.name}
              </a>
            `).join('')}
          </div>
        `;
      } else {
        const card = document.getElementById('competitors-card');
        if (card) card.style.display = 'none';
      }
      return;
    }

    container.innerHTML = `
      <div class="competitor-grid">
        ${competitors.map(c => `
          <a href="company.html?slug=${profileSlug(c.name)}" class="competitor-chip">
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
      const card = document.getElementById('thesis-card');
      if (card) card.style.display = 'none';
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
    renderGitHubReleases(company);
    renderResearchPapers(company);
    renderClinicalTrials(company);
    renderFDAActions(company);
    renderHNBuzz(company);
    renderRegulatoryFeed(company);
    renderGovPrograms(company);
  }

  function renderPatentIntel(company) {
    const container = document.getElementById('patent-intel');

    // Check editorial data first, then fall back to live USPTO data
    const patent = typeof PATENT_INTEL !== 'undefined' ? PATENT_INTEL.find(p => p.company === company.name) : null;
    const livePatent = typeof PATENT_INTEL_AUTO !== 'undefined' ? PATENT_INTEL_AUTO.find(p => p.company === company.name) : null;

    if (!patent && !livePatent) {
      container.innerHTML = '<div class="no-data"><p>No patent data available</p></div>';
      return;
    }

    if (patent) {
      // Use editorial data (has IP moat score, tech areas, velocity)
      const moatClass = patent.ipMoatScore >= 7 ? 'high' : patent.ipMoatScore >= 5 ? 'mid' : 'low';
      const liveCount = livePatent ? livePatent.patentCount : null;

      container.innerHTML = `
        <div class="patent-stats">
          <div class="patent-stat">
            <div class="patent-stat-value">${liveCount || patent.totalPatents}</div>
            <div class="patent-stat-label">Patents${liveCount ? ' (USPTO)' : ''}</div>
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
    } else {
      // Live USPTO data only (no editorial score)
      const areas = (livePatent.technologyAreas || []).slice(0, 5);
      container.innerHTML = `
        <div class="patent-stats">
          <div class="patent-stat">
            <div class="patent-stat-value">${livePatent.patentCount}</div>
            <div class="patent-stat-label">Patents (USPTO)</div>
          </div>
          <div class="patent-stat">
            <div class="patent-stat-value">${areas.length}</div>
            <div class="patent-stat-label">Tech Areas</div>
          </div>
          <div class="patent-stat">
            <div class="patent-stat-value">${livePatent.latestPatentDate || 'N/A'}</div>
            <div class="patent-stat-label">Latest Filing</div>
          </div>
        </div>
        ${areas.length > 0 ? `
          <div class="patent-areas">
            ${areas.map(t => `<span class="patent-area-tag">${t}</span>`).join('')}
          </div>
        ` : ''}
        <p style="font-size:11px;color:var(--text-muted);margin-top:8px;">Source: USPTO PatentsView API</p>
      `;
    }
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

  // ── GitHub Releases (for open-source / dev-tools companies) ──
  function renderGitHubReleases(company) {
    const card = document.getElementById('github-releases-card');
    const container = document.getElementById('github-releases');
    if (!card || !container) return;

    const releases = typeof GITHUB_RELEASES !== 'undefined'
      ? GITHUB_RELEASES.filter(r => r.company === company.name).slice(0, 8)
      : [];

    if (releases.length === 0) return; // Keep card hidden

    card.style.display = '';
    container.innerHTML = `
      <div class="news-list">
        ${releases.map(r => `
          <div class="news-item" style="cursor:default;">
            <div class="news-date">${r.date || ''}</div>
            <div class="news-title" style="font-family:monospace;font-size:12px;">${r.tag}</div>
            <div class="news-source">${r.repo}</div>
          </div>
        `).join('')}
      </div>
      <p style="font-size:11px;color:var(--text-muted);margin-top:8px;">Source: GitHub API</p>
    `;
  }

  // ── Research Papers (arXiv — AI, robotics, quantum, etc.) ──
  function renderResearchPapers(company) {
    const card = document.getElementById('research-papers-card');
    const container = document.getElementById('research-papers');
    if (!card || !container) return;

    if (typeof ARXIV_PAPERS === 'undefined') return;

    const nameLower = company.name.toLowerCase();
    const papers = ARXIV_PAPERS.filter(p => {
      const text = `${p.title} ${p.authors || ''}`.toLowerCase();
      return text.includes(nameLower);
    }).slice(0, 6);

    // Also show sector-relevant papers if company has few direct matches
    const sectorPapers = papers.length < 3 && company.sector
      ? ARXIV_PAPERS.filter(p => (p.sectors || '').includes(company.sector.toLowerCase())).slice(0, 4)
      : [];

    const allPapers = papers.length > 0 ? papers : sectorPapers;
    if (allPapers.length === 0) return;

    card.style.display = '';
    const label = papers.length > 0 ? 'Company-related' : 'Sector research';
    container.innerHTML = `
      <p style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">${label} papers from arXiv</p>
      <div class="news-list">
        ${allPapers.map(p => `
          <a href="https://arxiv.org/abs/${p.id}" target="_blank" rel="noopener" class="news-item">
            <div class="news-date">${p.published || ''}</div>
            <div class="news-title" style="font-size:12px;">${(p.title || '').substring(0, 100)}</div>
            <div class="news-source">${p.category || ''}</div>
          </a>
        `).join('')}
      </div>
    `;
  }

  // ── Clinical Trials (biotech / medtech companies) ──
  function renderClinicalTrials(company) {
    const card = document.getElementById('clinical-trials-card');
    const container = document.getElementById('clinical-trials');
    if (!card || !container) return;

    if (typeof CLINICAL_TRIALS === 'undefined') return;

    const nameLower = company.name.toLowerCase();
    const trials = CLINICAL_TRIALS.filter(t => {
      const text = `${t.sponsor || ''} ${t.title || ''}`.toLowerCase();
      return text.includes(nameLower);
    }).slice(0, 6);

    if (trials.length === 0) return;

    const statusColors = { RECRUITING: '#22c55e', COMPLETED: '#3b82f6', NOT_YET_RECRUITING: '#f59e0b', ACTIVE_NOT_RECRUITING: '#6b7280' };

    card.style.display = '';
    container.innerHTML = `
      <div class="news-list">
        ${trials.map(t => {
          const color = statusColors[t.status] || '#6b7280';
          return `
            <a href="https://clinicaltrials.gov/study/${t.nctId}" target="_blank" rel="noopener" class="news-item">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <span style="font-size:10px;padding:2px 6px;border-radius:4px;background:${color}15;color:${color};font-weight:600;">${(t.status || '').replace(/_/g, ' ')}</span>
                ${t.phase && t.phase !== 'N/A' ? `<span style="font-size:10px;color:var(--text-muted);">${t.phase}</span>` : ''}
              </div>
              <div class="news-title" style="font-size:12px;">${(t.title || '').substring(0, 100)}</div>
              <div class="news-source">Enrollment: ${t.enrollment || 'N/A'} &middot; ${t.lastUpdated || ''}</div>
            </a>
          `;
        }).join('')}
      </div>
      <p style="font-size:11px;color:var(--text-muted);margin-top:8px;">Source: ClinicalTrials.gov</p>
    `;
  }

  // ── FDA Actions (biotech / medtech / pharma) ──
  function renderFDAActions(company) {
    const card = document.getElementById('fda-actions-card');
    const container = document.getElementById('fda-actions');
    if (!card || !container) return;

    if (typeof FDA_ACTIONS === 'undefined') return;

    const actions = FDA_ACTIONS.filter(a => a.company === company.name).slice(0, 8);
    if (actions.length === 0) return;

    card.style.display = '';
    container.innerHTML = `
      <div class="news-list">
        ${actions.map(a => `
          <div class="news-item" style="cursor:default;">
            <div class="news-date">${a.date || ''}</div>
            <div class="news-title" style="font-size:12px;">${a.product || ''}</div>
            <div class="news-source">${a.type === 'device_510k' ? '510(k) Clearance' : a.type || ''} &middot; ${a.status || ''}</div>
          </div>
        `).join('')}
      </div>
      <p style="font-size:11px;color:var(--text-muted);margin-top:8px;">Source: FDA openFDA</p>
    `;
  }

  // ── Hacker News Buzz ──
  function renderHNBuzz(company) {
    const card = document.getElementById('hn-buzz-card');
    const container = document.getElementById('hn-buzz');
    if (!card || !container) return;

    if (typeof HN_BUZZ === 'undefined') return;

    const nameLower = company.name.toLowerCase();
    const stories = HN_BUZZ.filter(h => {
      const companies = (h.companies || '').toLowerCase();
      return companies.includes(nameLower);
    }).slice(0, 6);

    if (stories.length === 0) return;

    card.style.display = '';
    container.innerHTML = `
      <div class="news-list">
        ${stories.map(h => `
          <a href="https://news.ycombinator.com/item?id=${h.id}" target="_blank" rel="noopener" class="news-item">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
              <span style="font-size:11px;font-weight:600;color:var(--accent);">${h.score} pts</span>
              <span style="font-size:11px;color:var(--text-muted);">${h.comments} comments</span>
            </div>
            <div class="news-title" style="font-size:12px;">${h.title}</div>
            <div class="news-source">${h.date || ''}</div>
          </a>
        `).join('')}
      </div>
      <p style="font-size:11px;color:var(--text-muted);margin-top:8px;">Source: Hacker News</p>
    `;
  }

  // ── Federal Register / Regulatory Activity ──
  function renderRegulatoryFeed(company) {
    const card = document.getElementById('regulatory-card');
    const container = document.getElementById('regulatory-feed');
    if (!card || !container) return;

    if (typeof FEDERAL_REGISTER === 'undefined') return;

    // Match by sector keywords
    const sectorLower = (company.sector || '').toLowerCase();
    const docs = FEDERAL_REGISTER.filter(d => {
      const sectors = (d.sectors || '').toLowerCase();
      return sectors.includes(sectorLower) || (d.significant === true);
    }).slice(0, 6);

    if (docs.length === 0) return;

    const typeColors = { Rule: '#22c55e', 'Proposed Rule': '#f59e0b', Notice: '#3b82f6' };

    card.style.display = '';
    container.innerHTML = `
      <p style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">Sector-relevant federal documents</p>
      <div class="news-list">
        ${docs.map(d => {
          const color = typeColors[d.type] || '#6b7280';
          return `
            <a href="https://www.federalregister.gov/documents/${d.docNum}" target="_blank" rel="noopener" class="news-item">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <span style="font-size:10px;padding:2px 6px;border-radius:4px;background:${color}15;color:${color};font-weight:600;">${d.type || ''}</span>
                <span style="font-size:10px;color:var(--text-muted);">${d.date || ''}</span>
              </div>
              <div class="news-title" style="font-size:12px;">${(d.title || '').substring(0, 100)}</div>
              <div class="news-source">${d.agencies || ''}</div>
            </a>
          `;
        }).join('')}
      </div>
    `;
  }

  // ── Government Programs (DOE, NASA — energy/space/defense) ──
  function renderGovPrograms(company) {
    const card = document.getElementById('gov-programs-card');
    const container = document.getElementById('gov-programs');
    if (!card || !container) return;

    const programs = [];

    // DOE programs
    if (typeof DOE_PROGRAMS !== 'undefined') {
      DOE_PROGRAMS.forEach(p => {
        if ((p.companies || '').toLowerCase().includes(company.name.toLowerCase())) {
          programs.push({ ...p, source: 'DOE' });
        }
      });
    }

    // NASA projects (may be empty)
    if (typeof NASA_PROJECTS !== 'undefined') {
      NASA_PROJECTS.forEach(p => {
        if ((p.companies || '').toLowerCase().includes(company.name.toLowerCase())) {
          programs.push({ ...p, source: 'NASA' });
        }
      });
    }

    if (programs.length === 0) return;

    card.style.display = '';
    container.innerHTML = `
      <div class="news-list">
        ${programs.map(p => `
          <div class="news-item" style="cursor:default;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
              <span style="font-size:10px;padding:2px 6px;border-radius:4px;background:#3b82f615;color:#3b82f6;font-weight:600;">${p.source}</span>
              <span style="font-size:10px;color:var(--text-muted);">${p.status || ''}</span>
            </div>
            <div class="news-title" style="font-size:12px;">${p.program || p.title || ''}</div>
            <div class="news-source">
              ${p.funding ? `Funding: ${p.funding}` : ''}
              ${p.agency ? ` &middot; ${p.agency}` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  // ═══════════════════════════════════════════════════════
  // SECTION E: MARKET & REGULATORY INTELLIGENCE
  // ═══════════════════════════════════════════════════════

  function renderMarketIntelSection(company) {
    const section = document.getElementById('profile-market-intel');
    if (!section) return;

    let hasData = false;

    hasData = renderStockPrice(company) || hasData;
    hasData = renderSECFilings(company) || hasData;
    hasData = renderInsiderTrading(company) || hasData;
    hasData = renderSectorMomentumContext(company) || hasData;
    hasData = renderGovDemandMatch(company) || hasData;

    if (hasData) {
      section.style.display = 'block';
      const ts = document.getElementById('market-intel-updated');
      if (ts) ts.textContent = 'Updated: ' + new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
  }

  function renderStockPrice(company) {
    const card = document.getElementById('stock-price-card');
    const container = document.getElementById('stock-price-content');
    if (!card || !container) return false;

    // Find stock data — check STOCK_PRICES object by matching company name
    if (typeof STOCK_PRICES === 'undefined') return false;

    let stockData = null;
    for (const [ticker, data] of Object.entries(STOCK_PRICES)) {
      if (data.company && company.name.toLowerCase().includes(data.company.toLowerCase())) {
        stockData = data;
        break;
      }
    }

    // Also try matching by ticker in company data
    if (!stockData && company.ticker) {
      stockData = STOCK_PRICES[company.ticker];
    }

    if (!stockData) return false;

    const isPositive = stockData.changePercent >= 0;
    const changeClass = isPositive ? 'positive' : 'negative';
    const changeIcon = isPositive ? '▲' : '▼';

    // Mini sparkline SVG
    let sparklineSVG = '';
    if (stockData.sparkline && stockData.sparkline.length > 1) {
      const min = Math.min(...stockData.sparkline);
      const max = Math.max(...stockData.sparkline);
      const range = max - min || 1;
      const w = 200, h = 50;
      const points = stockData.sparkline.map((v, i) => {
        const x = (i / (stockData.sparkline.length - 1)) * w;
        const y = h - ((v - min) / range) * h;
        return `${x},${y}`;
      }).join(' ');
      const color = isPositive ? '#22c55e' : '#ef4444';
      sparklineSVG = `
        <svg viewBox="0 0 ${w} ${h}" class="stock-sparkline" preserveAspectRatio="none">
          <polyline points="${points}" fill="none" stroke="${color}" stroke-width="2"/>
        </svg>
      `;
    }

    card.style.display = 'block';
    const ts = document.getElementById('stock-updated');
    if (ts) ts.textContent = stockData.lastUpdated ? stockData.lastUpdated.split(' ')[0] : '';

    container.innerHTML = `
      <div class="stock-summary">
        <div class="stock-ticker">${stockData.ticker} · ${stockData.exchange || 'NYSE'}</div>
        <div class="stock-price-large">$${stockData.price.toFixed(2)}</div>
        <div class="stock-change ${changeClass}">
          ${changeIcon} ${Math.abs(stockData.change).toFixed(2)} (${Math.abs(stockData.changePercent).toFixed(2)}%)
        </div>
        ${sparklineSVG}
        <div class="stock-details-grid">
          <div class="stock-detail">
            <span class="stock-detail-label">Day Range</span>
            <span class="stock-detail-value">$${stockData.dayLow?.toFixed(2) || '--'} — $${stockData.dayHigh?.toFixed(2) || '--'}</span>
          </div>
          <div class="stock-detail">
            <span class="stock-detail-label">52-Week Range</span>
            <span class="stock-detail-value">$${stockData.fiftyTwoWeekLow?.toFixed(2) || '--'} — $${stockData.fiftyTwoWeekHigh?.toFixed(2) || '--'}</span>
          </div>
          <div class="stock-detail">
            <span class="stock-detail-label">Volume</span>
            <span class="stock-detail-value">${stockData.volume ? stockData.volume.toLocaleString() : '--'}</span>
          </div>
          ${stockData.marketCap && stockData.marketCap !== 'N/A' ? `
            <div class="stock-detail">
              <span class="stock-detail-label">Market Cap</span>
              <span class="stock-detail-value">${stockData.marketCap}</span>
            </div>
          ` : ''}
        </div>
      </div>
    `;
    return true;
  }

  function renderSECFilings(company) {
    const card = document.getElementById('sec-filings-card');
    const container = document.getElementById('sec-filings-content');
    if (!card || !container) return false;

    // Check both local sec_filings_auto.js data and data.js SEC_FILINGS_LIVE
    let filings = [];
    if (typeof SEC_FILINGS_LIVE !== 'undefined') {
      filings = SEC_FILINGS_LIVE.filter(f =>
        f.company && company.name.toLowerCase().includes(f.company.toLowerCase().split(' ')[0])
      ).slice(0, 8);
    }

    if (filings.length === 0) return false;

    card.style.display = 'block';
    const ts = document.getElementById('sec-updated');
    if (ts && filings[0]?.date) ts.textContent = filings[0].date;

    container.innerHTML = `
      <div class="filings-list">
        ${filings.map(f => {
          const formClass = f.form === '10-K' || f.form === '10-Q' ? 'form-major' : f.form === '8-K' ? 'form-event' : 'form-insider';
          const formIcon = f.form === '10-K' ? '📊' : f.form === '10-Q' ? '📈' : f.form === '8-K' ? '📰' : f.form === '4' ? '👤' : '📄';
          return `
            <div class="filing-item">
              <span class="filing-form ${formClass}">${formIcon} ${f.form}</span>
              <span class="filing-company">${f.company}</span>
              <span class="filing-date">${formatDate(f.date)}</span>
              ${f.ticker ? `<a href="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=${f.ticker}&type=&dateb=&owner=include&count=10" target="_blank" rel="noopener" class="filing-link">EDGAR →</a>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
    return true;
  }

  function renderInsiderTrading(company) {
    const card = document.getElementById('insider-transactions-card');
    const container = document.getElementById('insider-transactions-content');
    if (!card || !container) return false;

    if (typeof INSIDER_TRANSACTIONS === 'undefined' || INSIDER_TRANSACTIONS.length === 0) return false;

    const transactions = INSIDER_TRANSACTIONS.filter(t =>
      t.company && company.name.toLowerCase().includes(t.company.toLowerCase().split(' ')[0])
    ).slice(0, 8);

    if (transactions.length === 0) return false;

    card.style.display = 'block';
    const ts = document.getElementById('insider-updated');
    if (ts && transactions[0]?.date) ts.textContent = transactions[0].date;

    container.innerHTML = `
      <div class="insider-list">
        ${transactions.map(t => {
          const isBuy = (t.type || '').toLowerCase().includes('buy') || (t.type || '').toLowerCase().includes('purchase');
          const typeClass = isBuy ? 'insider-buy' : 'insider-sell';
          const typeIcon = isBuy ? '🟢' : '🔴';
          return `
            <div class="insider-item ${typeClass}">
              <div class="insider-name">${t.insiderName || t.insider || 'Insider'}</div>
              <div class="insider-details">
                <span class="insider-type">${typeIcon} ${t.type || 'Transaction'}</span>
                ${t.shares ? `<span class="insider-shares">${parseInt(t.shares).toLocaleString()} shares</span>` : ''}
                ${t.price ? `<span class="insider-price">@ $${parseFloat(t.price).toFixed(2)}</span>` : ''}
              </div>
              <div class="insider-date">${formatDate(t.date)}</div>
            </div>
          `;
        }).join('')}
      </div>
    `;
    return true;
  }

  function renderSectorMomentumContext(company) {
    const card = document.getElementById('sector-momentum-card');
    const container = document.getElementById('sector-momentum-content');
    if (!card || !container) return false;

    if (typeof SECTOR_MOMENTUM === 'undefined') return false;

    const sectorData = SECTOR_MOMENTUM.find(s =>
      s.sector === company.sector || s.sector.toLowerCase().includes(company.sector?.toLowerCase().split(' ')[0] || '')
    );

    if (!sectorData) return false;

    card.style.display = 'block';

    const momentumClass = sectorData.momentum >= 85 ? 'momentum-high' : sectorData.momentum >= 70 ? 'momentum-mid' : 'momentum-low';
    const trendIcon = sectorData.trend === 'accelerating' ? '🚀' : sectorData.trend === 'steady' ? '→' : '↘️';

    container.innerHTML = `
      <div class="sector-momentum-display">
        <div class="momentum-score-container">
          <div class="momentum-score-ring ${momentumClass}">
            <span class="momentum-score-value">${sectorData.momentum}</span>
            <span class="momentum-score-max">/100</span>
          </div>
          <div class="momentum-meta">
            <span class="momentum-trend">${trendIcon} ${(sectorData.trend || 'unknown').charAt(0).toUpperCase() + (sectorData.trend || '').slice(1)}</span>
            ${sectorData.fundingQ ? `<span class="momentum-funding">${sectorData.fundingQ} this quarter</span>` : ''}
          </div>
        </div>
        ${sectorData.catalysts && sectorData.catalysts.length > 0 ? `
          <div class="momentum-catalysts">
            <span class="catalyst-label">Key Catalysts</span>
            <div class="catalyst-tags">
              ${sectorData.catalysts.map(c => `<span class="catalyst-tag">${c}</span>`).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;
    return true;
  }

  function renderGovDemandMatch(company) {
    const card = document.getElementById('gov-demand-card');
    const container = document.getElementById('gov-demand-content');
    if (!card || !container) return false;

    if (typeof GOV_DEMAND_TRACKER === 'undefined') return false;

    // Match by relevantCompanies or techAreas
    const demands = GOV_DEMAND_TRACKER.filter(d => {
      if (!d) return false;
      const companyMatch = (d.relevantCompanies || []).some(c => c.toLowerCase() === company.name.toLowerCase());
      const techMatch = (d.techAreas || []).some(t => {
        if (!company.sector) return false;
        const sectorKey = company.sector.toLowerCase();
        return sectorKey.includes(t.toLowerCase().split(' ')[0]) || t.toLowerCase().includes(sectorKey.split(' ')[0]);
      });
      return companyMatch || techMatch;
    }).slice(0, 5);

    if (demands.length === 0) return false;

    card.style.display = 'block';

    container.innerHTML = `
      <div class="demand-list">
        ${demands.map(d => {
          const priorityClass = (d.priority || '').toLowerCase() === 'critical' ? 'priority-critical' :
                                (d.priority || '').toLowerCase() === 'high' ? 'priority-high' : 'priority-medium';
          return `
            <div class="demand-item">
              <div class="demand-header">
                <span class="demand-agency">${d.agency || 'Government'}</span>
                <span class="demand-priority ${priorityClass}">${d.priority || 'Medium'}</span>
              </div>
              <div class="demand-tech">${d.title || d.techAreas?.join(', ') || 'Technology Area'}</div>
              ${d.value ? `<div class="demand-value">${d.value}</div>` : ''}
              ${d.deadline ? `<div class="demand-timeline">Deadline: ${d.deadline}</div>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
    return true;
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
      const score = typeof INNOVATOR_SCORES !== 'undefined' ? INNOVATOR_SCORES.find(s => s.company === c.name) : null;
      const scoreValue = score?.composite?.toFixed(0) || '--';

      return `
        <a href="company.html?slug=${profileSlug(c.name)}" class="related-card">
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

    // Update attribution
    const attrUpdated = document.getElementById('attribution-updated');
    if (attrUpdated && typeof DATA_SOURCES !== 'undefined') {
      attrUpdated.textContent = `Last updated: ${DATA_SOURCES.companies?.lastUpdated || 'Unknown'}`;
    }
  }

  // ═══════════════════════════════════════════════════════
  // UTILITY FUNCTIONS
  // ═══════════════════════════════════════════════════════

  function profileSlug(name) {
    if (typeof companyToSlug === 'function') return companyToSlug(name);
    return name.toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
  }

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
