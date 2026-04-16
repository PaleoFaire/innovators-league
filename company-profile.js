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
    renderConvictionSection(currentCompany);
    renderTractionSection(currentCompany);
    renderCompanyTimeline(currentCompany);
    renderCompetitiveSection(currentCompany);
    renderIntelligenceSection(currentCompany);
    renderMarketIntelSection(currentCompany);
    renderRelatedSection(currentCompany);
    renderFounderSocialSignal(currentCompany);
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
    const oneLiner = company.description ? company.description.split('.')[0] + '.' : 'Frontier technology company.';

    container.innerHTML = `
      <div class="hero-top-row">
        <div class="hero-main">
          <div class="hero-badges">
            <span class="sector-badge" style="background:${sectorInfo.color}15; color:${sectorInfo.color}; border: 1px solid ${sectorInfo.color}30;">
              ${sectorInfo.icon} ${escapeHtml(company.sector)}
            </span>
            ${company.signal ? `<span class="signal-badge-large ${company.signal}">${getSignalIcon(company.signal)} ${company.signal.toUpperCase()}</span>` : ''}
            ${company.tbpnMentioned ? '<span class="signal-badge-large" style="background:#22c55e15; color:#22c55e; border:1px solid #22c55e40;">✓ TBPN Featured</span>' : ''}
          </div>
          <div class="company-logo-icon" style="width:72px; height:72px; border-radius:16px; background:${sectorInfo.color}20; border:2px solid ${sectorInfo.color}40; display:flex; align-items:center; justify-content:center; font-size:36px; margin:12px 0;">
            ${sectorInfo.icon}
          </div>
          <h1 class="company-name-large">${escapeHtml(company.name)}</h1>
          <p class="company-oneliner">${escapeHtml(oneLiner)}</p>
          <div class="hero-meta">
            <span class="meta-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              ${escapeHtml(company.location || 'Location TBD')}
            </span>
            <span class="meta-divider"></span>
            <span class="meta-item">🌍 ${escapeHtml(country)}</span>
            ${company.founder ? `<span class="meta-divider"></span><span class="meta-item">👤 ${escapeHtml(company.founder)}</span>` : ''}
            ${company.founded ? `<span class="meta-divider"></span><span class="meta-item">📅 Est. ${escapeHtml(company.founded)}</span>` : ''}
          </div>
        </div>
        <div class="hero-score-card">
          <div class="score-card-label">Frontier Index™</div>
          <div class="score-card-value ${scoreClass}">${scoreValue}</div>
          <span class="score-card-tier ${scoreClass}">${scoreTier}</span>
        </div>
      </div>

      <div class="hero-stats-grid">
        ${company.fundingStage ? `<div class="hero-stat"><div class="hero-stat-value">${escapeHtml(company.fundingStage)}</div><div class="hero-stat-label">Stage</div></div>` : ''}
        ${company.totalRaised ? `<div class="hero-stat"><div class="hero-stat-value">${escapeHtml(company.totalRaised)}</div><div class="hero-stat-label">Total Raised</div></div>` : ''}
        ${company.valuation ? `<div class="hero-stat"><div class="hero-stat-value">${escapeHtml(company.valuation)}</div><div class="hero-stat-label">Valuation</div></div>` : `<div class="hero-stat"><div class="hero-stat-value" style="font-size:14px; color:var(--text-muted);">Undisclosed</div><div class="hero-stat-label">Valuation</div></div>`}
        ${company.employees ? `<div class="hero-stat"><div class="hero-stat-value">${escapeHtml(company.employees)}</div><div class="hero-stat-label">Employees</div></div>` : ''}
        ${getTRL(company) ? `<div class="hero-stat"><div class="hero-stat-value">TRL ${getTRL(company)}</div><div class="hero-stat-label">Tech Readiness</div></div>` : ''}
      </div>

      ${company.insight ? `
        <div class="ros-take">
          <div class="ros-take-header">
            <span class="ros-take-badge">ROS TAKE</span>
            <span style="color:var(--text-muted); font-size:12px;">Our differentiated analysis</span>
          </div>
          <div class="ros-take-content">${escapeHtml(company.insight)}</div>
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
  // STEPHEN'S TAKE — CONVICTION SECTION
  // ═══════════════════════════════════════════════════════

  function renderConvictionSection(company) {
    var heroContainer = document.getElementById('profile-hero');
    if (!heroContainer) return;

    var existing = document.getElementById('conviction-section');
    if (existing) existing.remove();

    var section = document.createElement('div');
    section.id = 'conviction-section';
    section.className = 'conviction-section';

    // Gather data
    var fieldNote = (typeof FIELD_NOTES !== 'undefined') ? FIELD_NOTES.find(function(n) { return n.company === company.name; }) : null;
    var connection = (typeof FOUNDER_CONNECTIONS !== 'undefined') ? FOUNDER_CONNECTIONS[company.name] : null;
    var conviction = fieldNote ? fieldNote.conviction : null;
    var insight = fieldNote ? fieldNote.insight : (company.insight || null);
    var quote = connection ? connection.exclusiveQuote : (fieldNote ? fieldNote.pullQuote : null);
    var tripNotes = connection ? connection.tripNotes : null;
    var metFounder = connection ? connection.metFounder : false;
    var lastConversation = connection ? connection.lastConversation : null;
    var isInterviewed = connection ? connection.interviewConducted : false;
    var isSiteVisit = fieldNote ? fieldNote.type === 'site-visit' : false;
    var isPodcast = fieldNote ? (fieldNote.type === 'podcast' || fieldNote.type === 'interview') : false;

    // If nothing at all, show minimal placeholder
    if (!insight && !quote && !tripNotes && !conviction && !metFounder) {
      section.innerHTML = '<div class="conviction-empty"><span class="conviction-empty-label">STEPHEN\'S TAKE</span><p>No conviction note yet. This company is being tracked but has not been assessed.</p></div>';
      heroContainer.parentNode.insertBefore(section, heroContainer.nextSibling);
      return;
    }

    // Build conviction badge
    var convictionBadges = {
      'strong-buy': { label: 'STRONG BUY', cls: 'conviction-lg-strong-buy', icon: '🟢' },
      'buy': { label: 'BUY', cls: 'conviction-lg-buy', icon: '🔵' },
      'watch': { label: 'WATCH', cls: 'conviction-lg-watch', icon: '🟡' },
      'caution': { label: 'CAUTION', cls: 'conviction-lg-caution', icon: '🔴' }
    };
    var cb = conviction ? convictionBadges[conviction] : null;

    var html = '<div class="conviction-header"><span class="conviction-label">STEPHEN\'S TAKE</span>';
    if (cb) html += '<span class="conviction-lg-badge ' + cb.cls + '">' + cb.icon + ' ' + cb.label + '</span>';
    html += '</div>';

    // Check for podcast episodes across all FIELD_NOTES (not just the first match)
    if (!isPodcast && typeof FIELD_NOTES !== 'undefined') {
      var podEpisodes = FIELD_NOTES.filter(function(n) {
        return n.company === company.name && (n.type === 'podcast' || n.type === 'interview');
      });
      if (podEpisodes.length > 0) isPodcast = true;
    }

    // Connection badges
    var badges = [];
    if (metFounder) badges.push('<span class="connection-badge">🤝 Met Founder</span>');
    if (isPodcast) badges.push('<span class="connection-badge">🎙️ Podcast Guest</span>');
    if (isSiteVisit) badges.push('<span class="connection-badge">🏭 Site Visit</span>');
    if (isInterviewed) badges.push('<span class="connection-badge">🎤 Interviewed</span>');
    if (badges.length > 0) html += '<div class="connection-badges">' + badges.join('') + '</div>';

    // Insight/thesis
    if (insight) html += '<div class="conviction-thesis"><p>' + escapeHtml(insight) + '</p></div>';

    // Founder quote
    if (quote) {
      html += '<div class="conviction-quote"><div class="conviction-quote-mark">"</div><blockquote>' + escapeHtml(quote) + '</blockquote>';
      if (connection && connection.metFounder && company.founder) {
        html += '<div class="conviction-quote-attr">— ' + escapeHtml(company.founder) + ', ' + escapeHtml(company.name) + '</div>';
      }
      html += '</div>';
    }

    // Trip notes
    if (tripNotes) html += '<div class="conviction-trip"><span class="conviction-trip-label">📍 Field Notes</span><p>' + escapeHtml(tripNotes) + '</p></div>';

    // Last conversation
    if (lastConversation) html += '<div class="conviction-last-updated">Last conversation: ' + escapeHtml(lastConversation) + '</div>';

    section.innerHTML = html;
    heroContainer.parentNode.insertBefore(section, heroContainer.nextSibling);
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
          ${company.totalRaised ? `<p style="margin-top:8px; color:var(--text);">Total raised: <strong>${escapeHtml(company.totalRaised)}</strong></p>` : ''}
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
              <div class="funding-round-amount">${escapeHtml(round.amount)}</div>
              <div class="funding-round-stage">${escapeHtml(round.stage || round.type || 'Funding Round')}</div>
              ${round.investor ? `<div class="funding-round-investors">Lead: ${escapeHtml(round.investor)}</div>` : ''}
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

    // Also check GOV_CONTRACTS for intel
    const contractIntel = typeof GOV_CONTRACTS !== 'undefined'
      ? GOV_CONTRACTS.find(c => c.company === company.name)
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
            ${contractIntel.totalContracts ? `<div><strong>${escapeHtml(String(contractIntel.totalContracts))}</strong> <span style="color:var(--text-muted); font-size:12px;">Contracts</span></div>` : ''}
            ${contractIntel.agencies ? `<div><strong>${contractIntel.agencies.length}</strong> <span style="color:var(--text-muted); font-size:12px;">Agencies</span></div>` : ''}
            ${contractIntel.clearanceLevel ? `<div><strong>${escapeHtml(contractIntel.clearanceLevel)}</strong> <span style="color:var(--text-muted); font-size:12px;">Clearance</span></div>` : ''}
          </div>
        </div>
      `;
    }

    if (contracts.length > 0) {
      html += contracts.map(contract => `
        <div class="contract-item">
          <div class="contract-header">
            <span class="contract-agency">${escapeHtml(contract.agency || 'Government')}</span>
            <span class="contract-value">${escapeHtml(contract.value || 'Undisclosed')}</span>
          </div>
          <div class="contract-description">${escapeHtml(contract.description || contract.program || 'Contract details')}</div>
          ${contract.samUrl ? `<a href="${sanitizeUrl(contract.samUrl)}" target="_blank" rel="noopener" class="contract-link">View on SAM.gov →</a>` : ''}
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
      ${altData.keySignal ? `<p style="margin-top:12px; font-size:13px; color:var(--text-muted);">${escapeHtml(altData.keySignal)}</p>` : ''}
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

    try {
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
    } catch (e) {
      console.error('[TIL] Hiring chart failed:', e);
    }
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
          <div class="milestone-title">${escapeHtml(m.title)}</div>
          <div class="milestone-desc">${escapeHtml(m.description)}</div>
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
        <div class="revenue-value">${escapeHtml(revenue.revenue)}</div>
        <div class="revenue-period">${escapeHtml(revenue.period)}</div>
        ${revenue.growth ? `<div class="revenue-growth positive">${escapeHtml(revenue.growth)} growth</div>` : ''}
        <div class="revenue-confidence">
          <div class="confidence-label">Confidence Level</div>
          <div class="confidence-bar">
            <div class="confidence-fill ${confidenceLevel}" style="width:${confidenceWidth}%;"></div>
          </div>
          <p style="font-size:11px; color:var(--text-muted); margin-top:8px;">Source: ${escapeHtml(revenue.source || 'Industry estimates')}</p>
        </div>
      </div>
    `;
  }

  // ═══════════════════════════════════════════════════════
  // SECTION C: COMPETITIVE CONTEXT
  // ═══════════════════════════════════════════════════════

  function renderCompetitiveSection(company) {
    renderCompetitors(company);
    renderThesisNeighbors(company);
    renderTransformationFeature(company);
    renderThesis(company);
    renderMoatEvidence(company);
  }

  function renderTransformationFeature(company) {
    const card = document.getElementById('transformation-feature-card');
    const descEl = document.getElementById('transformation-feature-desc');
    const linkEl = document.getElementById('transformation-feature-link');
    if (!card || !company || !company.sector) return;

    // Map sector to transformation page slug
    const sectorToTransformation = {
      'Defense & Security': { slug: 'defense', label: 'Defense' },
      'Drones & Autonomous': { slug: 'defense', label: 'Defense' },
      'Ocean & Maritime': { slug: 'defense', label: 'Defense' },
      'Supersonic & Hypersonic': { slug: 'defense', label: 'Defense' },
      'Nuclear Energy': { slug: 'energy', label: 'Energy' },
      'Climate & Energy': { slug: 'energy', label: 'Energy' },
      'Energy & Climate': { slug: 'energy', label: 'Energy' },
      'Space & Aerospace': { slug: 'space', label: 'Space' },
      'Transportation': { slug: 'automotive', label: 'Automotive' },
      'Biotech & Health': { slug: 'pharma', label: 'Pharma' },
      'Biotech & Medical': { slug: 'pharma', label: 'Pharma' },
      'Advanced Manufacturing': { slug: 'materials', label: 'Materials' },
      'Robotics & Manufacturing': { slug: 'materials', label: 'Materials' },
      'Robotics & Automation': { slug: 'materials', label: 'Materials' }
    };
    const match = sectorToTransformation[company.sector];
    if (!match) { card.style.display = 'none'; return; }

    if (descEl) descEl.textContent = `${escapeHtml(company.name)} is featured in the ${match.label} transformation report — the full stack breakdown, verified contract wins, capital flow, and earnings signals.`;
    if (linkEl) linkEl.href = `transformation/${match.slug}.html`;
    card.style.display = '';
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
                ${escapeHtml(c.name)}
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
            ${escapeHtml(c.name)}
            ${c.valuation ? `<span style="color:var(--text-muted); font-size:11px;">${escapeHtml(c.valuation)}</span>` : ''}
          </a>
        `).join('')}
      </div>
    `;
  }

  function renderThesisNeighbors(company) {
    const container = document.getElementById('thesis-neighbors-list');
    const card = document.getElementById('thesis-neighbors-card');
    if (!container || !company.thesisCluster) {
      if (card) card.style.display = 'none';
      return;
    }

    // Find all companies in the same thesis cluster
    const neighbors = COMPANIES
      .filter(c => c.thesisCluster === company.thesisCluster && c.name !== company.name)
      .sort((a, b) => {
        const signalOrder = { 'hot': 0, 'rising': 1, 'established': 2, 'early': 3, 'stealth': 4 };
        return (signalOrder[a.signal] || 5) - (signalOrder[b.signal] || 5);
      });

    if (neighbors.length === 0) {
      if (card) card.style.display = 'none';
      return;
    }

    const clusterLabel = company.thesisCluster.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    const signalEmoji = { hot: '🔥', rising: '📈', established: '💚', early: '🌱', stealth: '👻' };

    container.innerHTML = `
      <div style="margin-bottom: 10px; padding: 6px 12px; background: #1a1a1a; border-radius: 6px; font-size: 12px; color: #FF6B2C;">
        Cluster: ${escapeHtml(clusterLabel)} (${neighbors.length + 1} companies)
      </div>
      ${company.techApproach ? `<div style="margin-bottom: 12px; font-size: 12px; color: #aaa; border-left: 2px solid #FF6B2C; padding-left: 10px; line-height: 1.5;">
        <strong style="color: #ddd;">This company:</strong> ${escapeHtml(company.techApproach)}
      </div>` : ''}
      <div class="competitor-grid">
        ${neighbors.slice(0, 12).map(c => `
          <a href="company.html?slug=${profileSlug(c.name)}" class="competitor-chip" style="flex-direction: column; align-items: flex-start; gap: 2px;">
            <span>${signalEmoji[c.signal] || ''} ${escapeHtml(c.name)}</span>
            ${c.techApproach ? `<span style="font-size: 10px; color: var(--text-muted); line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${escapeHtml(c.techApproach)}</span>` : ''}
          </a>
        `).join('')}
      </div>
      ${neighbors.length > 12 ? `<p style="font-size: 11px; color: var(--text-muted); margin-top: 8px;">+${neighbors.length - 12} more in this cluster</p>` : ''}
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
          <p class="thesis-text">${escapeHtml(company.thesis.bull)}</p>
        </div>
      ` : ''}

      ${company.thesis.bear ? `
        <div class="thesis-section">
          <div class="thesis-label bear">🐻 Bear Case</div>
          <p class="thesis-text">${escapeHtml(company.thesis.bear)}</p>
        </div>
      ` : ''}

      ${company.thesis.risks && company.thesis.risks.length > 0 ? `
        <div class="thesis-section">
          <div class="thesis-label" style="color:var(--text-muted);">⚠️ Key Risks</div>
          <ul class="risks-list">
            ${company.thesis.risks.map(r => `<li><span class="risk-icon">•</span> ${escapeHtml(r)}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
    `;
  }

  function renderMoatEvidence(company) {
    var container = document.getElementById('moat-content');
    if (!container) return;

    // Check for rich moat profile
    var moatProfile = (typeof MOAT_PROFILES !== 'undefined')
      ? MOAT_PROFILES.find(function(m) { return m.company === company.name; })
      : null;

    if (moatProfile) {
      renderRichMoatBreakdown(container, company, moatProfile);
    } else {
      renderBasicMoatEvidence(container, company);
    }
  }

  function renderRichMoatBreakdown(container, company, profile) {
    // Update card title
    var cardTitle = document.querySelector('#moat-card h3');
    if (cardTitle) cardTitle.textContent = 'Technical Moat Breakdown';

    // Cross-reference data
    var patent = (typeof PATENT_INTEL !== 'undefined') ? PATENT_INTEL.find(function(p) { return p.company === company.name; }) : null;
    var govContract = (typeof GOV_CONTRACTS !== 'undefined') ? GOV_CONTRACTS.find(function(g) { return g.company === company.name; }) : null;
    var trlEntry = (typeof TRL_RANKINGS !== 'undefined') ? TRL_RANKINGS.find(function(t) { return t.company === company.name; }) : null;
    var trlVal = trlEntry ? trlEntry.trl : null;

    // Dimension definitions
    var dimDefs = [
      { key: 'regulatoryMoat', icon: '\u{1F3DB}\uFE0F', name: 'Regulatory' },
      { key: 'switchingCosts', icon: '\u{1F512}', name: 'Switching Costs' },
      { key: 'manufacturingReadiness', icon: '\u{1F3ED}', name: 'Mfg Readiness' },
      { key: 'dataAdvantage', icon: '\u{1F4CA}', name: 'Data Advantage' },
      { key: 'supplyChainControl', icon: '\u26D3\uFE0F', name: 'Supply Chain' },
      { key: 'talentDensity', icon: '\u{1F9E0}', name: 'Talent Density' }
    ];

    // Moat type labels
    var typeLabels = {
      'regulatory': 'Regulatory Moat',
      'platform': 'Platform Moat',
      'regulatory-platform': 'Regulatory + Platform',
      'ip-data': 'IP & Data Moat',
      'manufacturing': 'Manufacturing Moat',
      'network': 'Network Effects',
      'talent': 'Talent Moat'
    };

    // Trend display
    var trendMap = {
      'strengthening': { icon: '\u2191', label: 'Strengthening', cls: 'strong' },
      'stable': { icon: '\u2192', label: 'Stable', cls: 'medium' },
      'weakening': { icon: '\u2193', label: 'Weakening', cls: 'weak' }
    };
    var trend = trendMap[profile.moatTrend] || trendMap['stable'];

    // Moat depth color
    var depthColor = profile.moatDepth >= 70 ? '#22c55e' : profile.moatDepth >= 50 ? '#3b82f6' : profile.moatDepth >= 35 ? '#f59e0b' : '#6b7280';

    // Build dimensions HTML
    var dimsHtml = '';
    dimDefs.forEach(function(d) {
      var dim = profile.dimensions[d.key];
      if (!dim) return;
      var strength = dim.score >= 8 ? 'strong' : dim.score >= 5 ? 'medium' : 'weak';
      var barWidth = (dim.score / 10) * 100;
      dimsHtml += '<div class="moat-dimension">' +
        '<div class="moat-dim-header">' +
          '<span class="moat-dim-icon">' + d.icon + '</span>' +
          '<span class="moat-dim-name">' + d.name + '</span>' +
          '<span class="moat-dim-score ' + strength + '">' + dim.score + '/10</span>' +
        '</div>' +
        '<div class="moat-dim-bar"><div class="moat-dim-fill ' + strength + '" style="width:' + barWidth + '%"></div></div>' +
        '<div class="moat-dim-label">' + escapeHtml(dim.label) + '</div>' +
        '<div class="moat-dim-evidence">' + escapeHtml(dim.evidence) + '</div>' +
      '</div>';
    });

    // Build milestones HTML
    var milestonesHtml = '';
    if (profile.keyMilestone) {
      milestonesHtml += '<div class="moat-milestone-item">' +
        '<span class="moat-milestone-icon">\u2B50</span>' +
        '<div><div class="moat-milestone-label">Key Milestone</div>' +
        '<div class="moat-milestone-text">' + escapeHtml(profile.keyMilestone) + '</div></div></div>';
    }
    if (profile.scalePath) {
      milestonesHtml += '<div class="moat-milestone-item">' +
        '<span class="moat-milestone-icon">\u{1F680}</span>' +
        '<div><div class="moat-milestone-label">Scale Path</div>' +
        '<div class="moat-milestone-text">' + escapeHtml(profile.scalePath) + '</div></div></div>';
    }

    // Build cross-references HTML
    var crossrefsHtml = '';
    if (patent) {
      var ipStrength = patent.ipMoatScore >= 7 ? 'strong' : patent.ipMoatScore >= 5 ? 'medium' : 'weak';
      crossrefsHtml += '<div class="moat-crossref">\u{1F4DC} IP Moat: <span class="moat-value ' + ipStrength + '">' + patent.ipMoatScore + '/10</span> \u2014 <a href="#patent-intel-card" class="moat-crossref-link">See Patent Intelligence</a></div>';
    }
    if (govContract) {
      crossrefsHtml += '<div class="moat-crossref">\u{1F3DB}\uFE0F Gov Contracts: <span class="moat-value strong">' + (govContract.totalGovValue || 'Active') + '</span> \u2014 <a href="#contracts-card" class="moat-crossref-link">See Contracts</a></div>';
    }
    if (trlVal) {
      crossrefsHtml += '<div class="moat-crossref">\u{1F52C} Tech Readiness: <span class="moat-value medium">TRL ' + trlVal + '</span> \u2014 Shown in Hero Stats</div>';
    }

    container.innerHTML =
      '<div class="moat-header">' +
        '<div class="moat-depth-score">' +
          '<div class="moat-depth-value" style="background:linear-gradient(135deg,' + depthColor + ',' + depthColor + '99);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">' + profile.moatDepth + '</div>' +
          '<div class="moat-depth-label">Moat Depth</div>' +
        '</div>' +
        '<div class="moat-meta">' +
          '<span class="moat-type-badge">' + (typeLabels[profile.primaryMoatType] || profile.primaryMoatType) + '</span>' +
          '<span class="moat-trend ' + trend.cls + '">' + trend.icon + ' ' + trend.label + '</span>' +
        '</div>' +
      '</div>' +
      '<div class="moat-dimensions-grid">' + dimsHtml + '</div>' +
      (profile.moatNarrative ?
        '<div class="moat-narrative">' +
          '<div class="moat-narrative-label">Moat Analysis</div>' +
          '<p>' + escapeHtml(profile.moatNarrative) + '</p>' +
        '</div>' : '') +
      (milestonesHtml ? '<div class="moat-milestones">' + milestonesHtml + '</div>' : '') +
      (crossrefsHtml ? '<div class="moat-crossrefs">' + crossrefsHtml + '</div>' : '');
  }

  function renderBasicMoatEvidence(container, company) {
    // Fallback: original 4-tile display for companies without MOAT_PROFILES entry
    var patent = (typeof PATENT_INTEL !== 'undefined') ? PATENT_INTEL.find(function(p) { return p.company === company.name; }) : null;
    var govContract = (typeof GOV_CONTRACTS !== 'undefined') ? GOV_CONTRACTS.find(function(g) { return g.company === company.name; }) : null;
    var altData = (typeof ALT_DATA_SIGNALS !== 'undefined') ? ALT_DATA_SIGNALS.find(function(a) { return a.company === company.name; }) : null;

    var ipMoat = patent ? { value: patent.ipMoatScore + '/10', strength: patent.ipMoatScore >= 7 ? 'strong' : patent.ipMoatScore >= 5 ? 'medium' : 'weak' } : { value: '?', strength: 'weak' };
    var govMoat = govContract ? { value: govContract.totalContracts ? govContract.totalContracts + ' contracts' : 'Active', strength: 'strong' } : { value: 'None', strength: 'weak' };
    var talentMoat = altData && altData.hiringVelocity === 'surging' ? { value: 'Surging', strength: 'strong' } : altData && altData.hiringVelocity === 'growing' ? { value: 'Growing', strength: 'medium' } : { value: 'Unknown', strength: 'weak' };

    var supplyMoat = ['Defense & Security', 'Space & Aerospace', 'Nuclear Energy'].indexOf(company.sector) >= 0
      ? { value: 'Strategic', strength: 'strong' }
      : { value: 'Standard', strength: 'medium' };

    container.innerHTML =
      '<div class="moat-grid">' +
        '<div class="moat-item"><div class="moat-icon">\u{1F4DC}</div><div class="moat-label">IP / Patents</div><div class="moat-value ' + ipMoat.strength + '">' + ipMoat.value + '</div></div>' +
        '<div class="moat-item"><div class="moat-icon">\u{1F3DB}\uFE0F</div><div class="moat-label">Gov Contracts</div><div class="moat-value ' + govMoat.strength + '">' + govMoat.value + '</div></div>' +
        '<div class="moat-item"><div class="moat-icon">\u{1F517}</div><div class="moat-label">Supply Chain</div><div class="moat-value ' + supplyMoat.strength + '">' + supplyMoat.value + '</div></div>' +
        '<div class="moat-item"><div class="moat-icon">\u{1F465}</div><div class="moat-label">Talent</div><div class="moat-value ' + talentMoat.strength + '">' + talentMoat.value + '</div></div>' +
      '</div>';
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
            <div class="patent-stat-value">${escapeHtml(String(liveCount || patent.totalPatents))}</div>
            <div class="patent-stat-label">Patents${liveCount ? ' (USPTO)' : ''}</div>
          </div>
          <div class="patent-stat">
            <div class="patent-stat-value">${escapeHtml(patent.velocity)}</div>
            <div class="patent-stat-label">Filing Rate</div>
          </div>
          <div class="patent-stat">
            <div class="patent-stat-value" style="color:${moatClass === 'high' ? '#22c55e' : moatClass === 'mid' ? '#f59e0b' : '#6b7280'};">${escapeHtml(patent.trend || '→')}</div>
            <div class="patent-stat-label">Trend</div>
          </div>
        </div>
        <div class="ip-moat-score">
          <span class="ip-moat-label">IP Moat Score</span>
          <span class="ip-moat-value ${moatClass}">${escapeHtml(patent.ipMoatScore)}/10</span>
        </div>
        ${patent.techAreas && patent.techAreas.length > 0 ? `
          <div class="patent-areas">
            ${patent.techAreas.map(t => `<span class="patent-area-tag">${escapeHtml(t)}</span>`).join('')}
          </div>
        ` : ''}
      `;
    } else {
      // Live USPTO data only (no editorial score)
      const areas = (livePatent.technologyAreas || []).slice(0, 5);
      container.innerHTML = `
        <div class="patent-stats">
          <div class="patent-stat">
            <div class="patent-stat-value">${escapeHtml(String(livePatent.patentCount))}</div>
            <div class="patent-stat-label">Patents (USPTO)</div>
          </div>
          <div class="patent-stat">
            <div class="patent-stat-value">${areas.length}</div>
            <div class="patent-stat-label">Tech Areas</div>
          </div>
          <div class="patent-stat">
            <div class="patent-stat-value">${escapeHtml(livePatent.latestPatentDate || 'N/A')}</div>
            <div class="patent-stat-label">Latest Filing</div>
          </div>
        </div>
        ${areas.length > 0 ? `
          <div class="patent-areas">
            ${areas.map(t => `<span class="patent-area-tag">${escapeHtml(t)}</span>`).join('')}
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
          <div class="alt-data-value ${altData.hiringVelocity}">${escapeHtml((altData.hiringVelocity || 'Unknown').toUpperCase())}</div>
        </div>
        <div class="alt-data-item">
          <div class="alt-data-label">Web Traffic</div>
          <div class="alt-data-value ${altData.webTraffic}">${escapeHtml((altData.webTraffic || 'Unknown').toUpperCase())}</div>
        </div>
        <div class="alt-data-item">
          <div class="alt-data-label">News Sentiment</div>
          <div class="alt-data-value">${escapeHtml((altData.newsSentiment || 'Neutral').toUpperCase())}</div>
        </div>
        <div class="alt-data-item">
          <div class="alt-data-label">Signal Strength</div>
          <div class="alt-data-value" style="color:var(--accent);">${escapeHtml(altData.signalStrength)}/10</div>
        </div>
      </div>
      ${altData.keySignal ? `<p style="margin-top:12px; font-size:13px; color:var(--text-muted); padding:12px; background:var(--bg); border-radius:8px;">${escapeHtml(altData.keySignal)}</p>` : ''}
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
          ${founderConnection.exclusiveQuote ? `<p style="font-style:italic; font-size:14px;">"${escapeHtml(founderConnection.exclusiveQuote)}"</p>` : ''}
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
                <div class="mafia-name-large">${escapeHtml(m.mafia)}</div>
                <div class="mafia-detail-large">${escapeHtml(m.detail)}</div>
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
          <a href="${sanitizeUrl(n.url)}" target="_blank" rel="noopener" class="news-item">
            <div class="news-date">${formatDate(n.date)}</div>
            <div class="news-title">${escapeHtml(n.headline)}</div>
            ${n.source ? `<div class="news-source">${escapeHtml(n.source)}</div>` : ''}
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
            <div class="news-date">${escapeHtml(r.date || '')}</div>
            <div class="news-title" style="font-family:monospace;font-size:12px;">${escapeHtml(r.tag)}</div>
            <div class="news-source">${escapeHtml(r.repo)}</div>
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
          <a href="https://arxiv.org/abs/${encodeURIComponent(p.id)}" target="_blank" rel="noopener" class="news-item">
            <div class="news-date">${escapeHtml(p.published || '')}</div>
            <div class="news-title" style="font-size:12px;">${escapeHtml((p.title || '').substring(0, 100))}</div>
            <div class="news-source">${escapeHtml(p.category || '')}</div>
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
            <a href="https://clinicaltrials.gov/study/${encodeURIComponent(t.nctId)}" target="_blank" rel="noopener" class="news-item">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <span style="font-size:10px;padding:2px 6px;border-radius:4px;background:${color}15;color:${color};font-weight:600;">${escapeHtml((t.status || '').replace(/_/g, ' '))}</span>
                ${t.phase && t.phase !== 'N/A' ? `<span style="font-size:10px;color:var(--text-muted);">${escapeHtml(t.phase)}</span>` : ''}
              </div>
              <div class="news-title" style="font-size:12px;">${escapeHtml((t.title || '').substring(0, 100))}</div>
              <div class="news-source">Enrollment: ${escapeHtml(t.enrollment || 'N/A')} &middot; ${escapeHtml(t.lastUpdated || '')}</div>
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
            <div class="news-date">${escapeHtml(a.date || '')}</div>
            <div class="news-title" style="font-size:12px;">${escapeHtml(a.product || '')}</div>
            <div class="news-source">${escapeHtml(a.type === 'device_510k' ? '510(k) Clearance' : a.type || '')} &middot; ${escapeHtml(a.status || '')}</div>
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
            <div class="news-title" style="font-size:12px;">${escapeHtml(h.title)}</div>
            <div class="news-source">${escapeHtml(h.date || '')}</div>
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
            <a href="https://www.federalregister.gov/documents/${encodeURIComponent(d.docNum)}" target="_blank" rel="noopener" class="news-item">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <span style="font-size:10px;padding:2px 6px;border-radius:4px;background:${color}15;color:${color};font-weight:600;">${escapeHtml(d.type || '')}</span>
                <span style="font-size:10px;color:var(--text-muted);">${escapeHtml(d.date || '')}</span>
              </div>
              <div class="news-title" style="font-size:12px;">${escapeHtml((d.title || '').substring(0, 100))}</div>
              <div class="news-source">${escapeHtml(d.agencies || '')}</div>
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
              <span style="font-size:10px;padding:2px 6px;border-radius:4px;background:#3b82f615;color:#3b82f6;font-weight:600;">${escapeHtml(p.source)}</span>
              <span style="font-size:10px;color:var(--text-muted);">${escapeHtml(p.status || '')}</span>
            </div>
            <div class="news-title" style="font-size:12px;">${escapeHtml(p.program || p.title || '')}</div>
            <div class="news-source">
              ${p.funding ? `Funding: ${escapeHtml(p.funding)}` : ''}
              ${p.agency ? ` &middot; ${escapeHtml(p.agency)}` : ''}
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
        <div class="stock-ticker">${escapeHtml(stockData.ticker)} · ${escapeHtml(stockData.exchange || 'NYSE')}</div>
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
              <span class="stock-detail-value">${escapeHtml(stockData.marketCap)}</span>
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
              <span class="filing-form ${formClass}">${formIcon} ${escapeHtml(f.form)}</span>
              <span class="filing-company">${escapeHtml(f.company)}</span>
              <span class="filing-date">${formatDate(f.date)}</span>
              ${f.ticker ? `<a href="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=${encodeURIComponent(f.ticker)}&type=&dateb=&owner=include&count=10" target="_blank" rel="noopener" class="filing-link">EDGAR →</a>` : ''}
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
              <div class="insider-name">${escapeHtml(t.insiderName || t.insider || 'Insider')}</div>
              <div class="insider-details">
                <span class="insider-type">${typeIcon} ${escapeHtml(t.type || 'Transaction')}</span>
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
            ${sectorData.fundingQ ? `<span class="momentum-funding">${escapeHtml(sectorData.fundingQ)} this quarter</span>` : ''}
          </div>
        </div>
        ${sectorData.catalysts && sectorData.catalysts.length > 0 ? `
          <div class="momentum-catalysts">
            <span class="catalyst-label">Key Catalysts</span>
            <div class="catalyst-tags">
              ${sectorData.catalysts.map(c => `<span class="catalyst-tag">${escapeHtml(c)}</span>`).join('')}
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

    // Merge curated + auto signals
    const curated = (typeof GOV_DEMAND_TRACKER !== 'undefined') ? GOV_DEMAND_TRACKER : [];
    const auto = (typeof GOV_DEMAND_SIGNALS_AUTO !== 'undefined') ? GOV_DEMAND_SIGNALS_AUTO : [];
    const seenIds = {};
    const allSignals = [];
    curated.forEach(s => { seenIds[s.id] = true; allSignals.push(s); });
    auto.forEach(s => { if (!seenIds[s.id]) allSignals.push(s); });

    if (allSignals.length === 0) return false;

    // Get Government Pull Score
    const pullScores = (typeof GOV_PULL_SCORES_AUTO !== 'undefined') ? GOV_PULL_SCORES_AUTO : {};
    const pullScore = pullScores[company.name];

    // Find matches using multiple strategies
    const matches = [];
    const companyNameLower = company.name.toLowerCase();

    allSignals.forEach(d => {
      if (!d) return;

      // Strategy 1: Pre-computed matchedCompanies (from auto-generated data)
      const autoMatch = (d.matchedCompanies || []).find(mc => mc.name.toLowerCase() === companyNameLower);
      if (autoMatch) {
        matches.push({ signal: d, score: autoMatch.score, reasons: autoMatch.matchReasons || [] });
        return;
      }

      // Strategy 2: Hardcoded relevantCompanies (from curated data)
      if ((d.relevantCompanies || []).some(c => c.toLowerCase() === companyNameLower)) {
        matches.push({ signal: d, score: 90, reasons: ['Curated match'] });
        return;
      }

      // Strategy 3: Client-side fallback tag matching
      const signalText = `${d.title || ''} ${d.description || ''} ${(d.techAreas || []).join(' ')}`.toLowerCase();
      const tagHits = (company.tags || []).filter(tag => signalText.includes(tag.toLowerCase()));
      if (tagHits.length >= 2) {
        matches.push({ signal: d, score: Math.min(tagHits.length * 15, 60), reasons: tagHits.map(t => 'tag: ' + t) });
      }
    });

    // Sort by score descending, take top 8
    matches.sort((a, b) => b.score - a.score);
    const topMatches = matches.slice(0, 8);

    if (topMatches.length === 0 && !pullScore) return false;

    card.style.display = 'block';

    let html = '';

    // Government Pull Score summary
    if (pullScore) {
      const pullClass = pullScore.govPullScore >= 60 ? 'gov-pull-high' : (pullScore.govPullScore >= 30 ? 'gov-pull-medium' : 'gov-pull-low');
      const pullColor = pullScore.govPullScore >= 60 ? '#22c55e' : (pullScore.govPullScore >= 30 ? '#3b82f6' : '#f59e0b');
      html += `<div style="display:flex;align-items:center;gap:12px;padding:10px 12px;background:var(--bg);border-radius:8px;margin-bottom:12px;">
        <div style="width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:800;color:${pullColor};border:2px solid ${pullColor}30;background:${pullColor}15;">${pullScore.govPullScore}</div>
        <div>
          <div style="font-size:12px;font-weight:600;color:var(--text-primary);">Government Pull Score</div>
          <div style="font-size:11px;color:var(--text-muted);">${pullScore.matchCount} matching signal${pullScore.matchCount !== 1 ? 's' : ''} across ${pullScore.topAgencies.length} agenc${pullScore.topAgencies.length !== 1 ? 'ies' : 'y'}</div>
        </div>
      </div>`;
    }

    // Matched signals with score bars
    if (topMatches.length > 0) {
      html += '<div class="demand-list">';
      topMatches.forEach(m => {
        const priorityClass = (m.signal.priority || '').toLowerCase() === 'critical' ? 'priority-critical' :
                              (m.signal.priority || '').toLowerCase() === 'high' ? 'priority-high' : 'priority-medium';
        const scoreColor = m.score >= 70 ? '#22c55e' : (m.score >= 40 ? '#3b82f6' : '#f59e0b');
        const barColor = m.score >= 70 ? '#22c55e' : (m.score >= 40 ? '#3b82f6' : '#f59e0b');

        html += `<div class="demand-item">
          <div class="demand-header">
            <span class="demand-agency">${escapeHtml(m.signal.agency || 'Government')}</span>
            <div style="display:flex;align-items:center;gap:6px;">
              <div style="width:40px;height:4px;background:rgba(255,255,255,0.1);border-radius:2px;overflow:hidden;"><div style="width:${m.score}%;height:100%;background:${barColor};border-radius:2px;"></div></div>
              <span style="font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;color:${scoreColor};">${m.score}%</span>
            </div>
          </div>
          <div class="demand-tech">${escapeHtml(m.signal.title || 'Technology Area')}</div>
          ${m.signal.value ? `<div class="demand-value">${escapeHtml(m.signal.value)}</div>` : ''}
          ${m.signal.deadline && m.signal.deadline !== 'Rolling' ? `<div class="demand-timeline">Deadline: ${escapeHtml(m.signal.deadline)}</div>` : ''}
          ${m.reasons.length > 0 ? `<div style="font-size:10px;color:var(--text-muted);margin-top:2px;">${m.reasons.slice(0, 3).map(r => escapeHtml(r)).join(' + ')}</div>` : ''}
        </div>`;
      });
      html += '</div>';
    }

    container.innerHTML = html;
    return true;
  }

  // ═══════════════════════════════════════════════════════
  // RELATED COMPANIES
  // ═══════════════════════════════════════════════════════

  // ═══════════════════════════════════════════════════════
  // SIMILARITY SCORING
  // ═══════════════════════════════════════════════════════
  // Given a target company, score every OTHER company on shared attributes
  // and return the top N most similar. This replaces the old "random same
  // sector" logic with a genuine recommender signal.
  function _valuationBucket(val) {
    if (!val || typeof val !== 'string') return null;
    const s = val.toUpperCase().replace(/[$,+]/g, '').trim();
    const num = parseFloat(s);
    if (isNaN(num)) return null;
    const multiplier = s.includes('T') ? 1000 : s.includes('B') ? 1 : s.includes('M') ? 0.001 : 0;
    const billions = num * multiplier;
    if (billions >= 50) return 'mega';
    if (billions >= 10) return 'decacorn';
    if (billions >= 1) return 'unicorn';
    if (billions >= 0.1) return 'soonicorn';
    return 'early';
  }

  function _stageBucket(stage) {
    if (!stage || typeof stage !== 'string') return null;
    const s = stage.toLowerCase();
    if (/(public|ipo|listed|nasdaq|nyse)/.test(s)) return 'public';
    if (/(pre-ipo|late|growth|series [ef-j])/.test(s)) return 'late';
    if (/(series [cd])/.test(s)) return 'growth';
    if (/(series [ab])/.test(s)) return 'early';
    if (/(seed|angel|pre-seed)/.test(s)) return 'seed';
    return null;
  }

  function _regionOf(location) {
    if (!location || typeof location !== 'string') return null;
    const l = location.toLowerCase();
    if (/(uk|london|england|scotland|wales|britain|united kingdom)/.test(l)) return 'uk';
    if (/(germany|berlin|munich|france|paris|netherlands|amsterdam|sweden|stockholm|finland|denmark|norway|spain|italy|switzerland|zurich|europe)/.test(l)) return 'europe';
    if (/(china|beijing|shanghai|shenzhen|hong kong)/.test(l)) return 'china';
    if (/(japan|tokyo|korea|seoul|singapore|india|bangalore|taiwan)/.test(l)) return 'asia';
    if (/(canada|toronto|vancouver|montreal)/.test(l)) return 'canada';
    if (/(israel|tel aviv|uae|abu dhabi|dubai|saudi)/.test(l)) return 'mena';
    if (/(australia|sydney|melbourne)/.test(l)) return 'anz';
    return 'americas'; // default, most US
  }

  function computeSimilarity(target, candidate) {
    if (target.name === candidate.name) return 0;
    let score = 0;

    // 1. Same sector — the strongest signal
    if (candidate.sector && candidate.sector === target.sector) score += 40;

    // 2. Overlapping tags — topic/tech alignment
    const tTags = new Set((target.tags || []).map(t => (t || '').toLowerCase()));
    const cTags = (candidate.tags || []).map(t => (t || '').toLowerCase());
    const overlap = cTags.filter(t => tTags.has(t)).length;
    score += Math.min(overlap * 6, 24); // cap at 24

    // 3. Funding stage proximity
    const ts = _stageBucket(target.fundingStage);
    const cs = _stageBucket(candidate.fundingStage);
    if (ts && cs) {
      if (ts === cs) score += 12;
      else if ((ts === 'early' && cs === 'growth') || (ts === 'growth' && cs === 'early')
             || (ts === 'growth' && cs === 'late') || (ts === 'late' && cs === 'growth')
             || (ts === 'late' && cs === 'public') || (ts === 'public' && cs === 'late')) {
        score += 6;
      }
    }

    // 4. Valuation bucket
    const tv = _valuationBucket(target.valuation);
    const cv = _valuationBucket(candidate.valuation);
    if (tv && cv && tv === cv) score += 8;

    // 5. Geographic region
    const tr = _regionOf(target.location);
    const cr = _regionOf(candidate.location);
    if (tr && cr && tr === cr) score += 6;

    // 6. Both featured (IL30 or shortlist)
    if (target.featured && candidate.featured) score += 4;

    return score;
  }

  function renderRelatedSection(company) {
    const container = document.getElementById('related-grid');
    if (!container) return;

    // Compute a similarity score for every other company; pick top 6.
    const scored = COMPANIES
      .filter(c => c && c.name && c.name !== company.name)
      .map(c => ({ company: c, score: computeSimilarity(company, c) }))
      .filter(x => x.score > 0)
      .sort((a, b) => b.score - a.score);

    const related = scored.slice(0, 6).map(x => x.company);

    if (related.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);">No related companies found</p>';
      return;
    }

    container.innerHTML = related.map((c, i) => {
      const score = typeof INNOVATOR_SCORES !== 'undefined' ? INNOVATOR_SCORES.find(s => s.company === c.name) : null;
      const scoreValue = score?.composite?.toFixed(0) || '--';
      const sim = scored[i] ? scored[i].score : 0;
      // Why-tag: surface the strongest reason
      const tTags = new Set((company.tags || []).map(t => (t || '').toLowerCase()));
      const sharedTags = (c.tags || []).filter(t => tTags.has((t || '').toLowerCase())).slice(0, 2);
      let reason = '';
      if (c.sector === company.sector && sharedTags.length) {
        reason = `${escapeHtml(c.sector)} · ${sharedTags.map(escapeHtml).join(', ')}`;
      } else if (c.sector === company.sector) {
        reason = escapeHtml(c.sector);
      } else if (sharedTags.length) {
        reason = sharedTags.map(escapeHtml).join(', ');
      } else if (c.fundingStage === company.fundingStage) {
        reason = escapeHtml(c.fundingStage || 'Similar stage');
      } else {
        reason = _regionOf(c.location) === _regionOf(company.location) ? 'Same region' : 'Adjacent tech';
      }

      return `
        <a href="company.html?slug=${profileSlug(c.name)}" class="related-card" title="Similarity score: ${sim}">
          <div class="related-card-header">
            <span class="related-card-name">${escapeHtml(c.name)}</span>
            <span class="related-card-score">${escapeHtml(scoreValue)}</span>
          </div>
          <div class="related-card-reason">${reason}</div>
          <p class="related-card-desc">${escapeHtml((c.description || '').substring(0, 100))}${c.description && c.description.length > 100 ? '…' : ''}</p>
        </a>
      `;
    }).join('');
  }

  // ═══════════════════════════════════════════════════════
  // FOUNDER SOCIAL SIGNAL (X / Twitter)
  // Renders founder X presence from data/twitter_signals_auto.json.
  // Hides itself if no record exists for this company.
  // ═══════════════════════════════════════════════════════
  function renderFounderSocialSignal(company) {
    const section = document.getElementById('profile-social');
    const grid = document.getElementById('social-grid');
    if (!section || !grid) return;

    // Fetch twitter signals once and cache on window. Works whether loaded
    // from data.js (for bundled signals) or fetched from data/*.json.
    const dataUrl = 'data/twitter_signals_auto.json';
    const showRecords = (records) => {
      if (!Array.isArray(records) || records.length === 0) return;
      // Match by company name (case-insensitive, trimmed)
      const target = (company.name || '').trim().toLowerCase();
      const matches = records.filter(r =>
        (r.company || '').trim().toLowerCase() === target
      );
      if (matches.length === 0) return;

      const formatFollowers = (n) => {
        if (n == null || isNaN(n)) return null;
        if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
        if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
        return String(n);
      };

      grid.innerHTML = matches.map(m => {
        const handle = m.handle || (m.candidate_handles && m.candidate_handles[0]) || '';
        const cleanHandle = String(handle).replace(/^@/, '');
        const followerLabel = formatFollowers(m.followers);
        const isPlaceholder = m.placeholder === true || !m.followers;
        const topicsHtml = (Array.isArray(m.topics) && m.topics.length > 0)
          ? `<div class="social-topics">${m.topics.slice(0, 4).map(t => `<span class="social-topic">#${escapeHtml(String(t))}</span>`).join('')}</div>`
          : '';
        const followersHtml = followerLabel
          ? `<div class="social-followers">${escapeHtml(followerLabel)} followers · ${escapeHtml(String(m.recent_posts || 0))} recent posts</div>`
          : '';
        const placeholderHtml = isPlaceholder
          ? `<div class="social-placeholder-note">Handle inferred — live follower data pending</div>`
          : '';
        const xUrl = cleanHandle ? `https://x.com/${encodeURIComponent(cleanHandle)}` : '#';

        return `
          <div class="social-card">
            <div class="social-founder">${escapeHtml(m.founder || '—')}</div>
            ${cleanHandle ? `<a class="social-handle" href="${xUrl}" target="_blank" rel="noopener">𝕏 @${escapeHtml(cleanHandle)}</a>` : ''}
            ${followersHtml}
            ${topicsHtml}
            ${placeholderHtml}
          </div>
        `;
      }).join('');
      section.style.display = 'block';
    };

    // Prefer a preloaded array on window.TWITTER_SIGNALS if something else loaded it
    if (window.TWITTER_SIGNALS && Array.isArray(window.TWITTER_SIGNALS)) {
      showRecords(window.TWITTER_SIGNALS);
      return;
    }

    // Otherwise lazy-fetch. Silently fail if file missing (e.g. in local dev).
    fetch(dataUrl, { cache: 'no-cache' })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          window.TWITTER_SIGNALS = data;
          showRecords(data);
        }
      })
      .catch(() => {});
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

    // Share on X button
    const shareXBtn = document.getElementById('btn-share-x');
    if (shareXBtn) {
      var shareText = 'Check out ' + company.name + ' on The Innovators League — the Bloomberg Terminal for frontier tech.';
      var shareUrl = window.location.href;
      var twitterUrl = 'https://twitter.com/intent/tweet?text=' + encodeURIComponent(shareText) + '&url=' + encodeURIComponent(shareUrl);
      shareXBtn.href = twitterUrl;
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

    // Tear Sheet button — populate the hidden tear-sheet-view and trigger native print
    const tearSheetBtn = document.getElementById('btn-tear-sheet');
    if (tearSheetBtn) {
      tearSheetBtn.addEventListener('click', () => {
        try {
          renderTearSheetView(company);
        } catch (e) {
          console.error('[TIL] renderTearSheetView failed:', e);
        }
        // Give the browser one paint tick to apply the populated DOM before print
        setTimeout(() => {
          try { window.print(); } catch (e) { console.error('[TIL] window.print failed:', e); }
        }, 50);
      });
    }

    // Update attribution
    const attrUpdated = document.getElementById('attribution-updated');
    if (attrUpdated && typeof DATA_SOURCES !== 'undefined') {
      attrUpdated.textContent = `Last updated: ${DATA_SOURCES.companies?.lastUpdated || 'Unknown'}`;
    }
  }

  // ═══════════════════════════════════════════════════════
  // TEAR SHEET — banker-grade one-page PDF export view
  // Populated from live company data; shown only via @media print
  // ═══════════════════════════════════════════════════════

  function renderTearSheetView(company) {
    if (!company) return;

    // ─── Gather data from all available sources ───
    var scores = company.scores || {};
    var innovatorScore = (typeof INNOVATOR_SCORES !== 'undefined')
      ? INNOVATOR_SCORES.find(function(s) { return s.company === company.name; }) : null;

    var fundingRounds = (typeof FUNDING_TRACKER !== 'undefined')
      ? FUNDING_TRACKER.filter(function(f) { return f.company === company.name; }) : [];
    var dealEntries = (typeof DEAL_TRACKER !== 'undefined')
      ? DEAL_TRACKER.filter(function(d) { return d.company === company.name; }) : [];

    var govContracts = (typeof GOV_CONTRACTS !== 'undefined')
      ? GOV_CONTRACTS.filter(function(g) { return g.company === company.name; }) : [];
    var sbirAwards = (typeof SBIR_AWARDS !== 'undefined')
      ? SBIR_AWARDS.filter(function(s) { return s.company === company.name; }) : [];
    var patents = (typeof PATENT_INTEL !== 'undefined')
      ? PATENT_INTEL.find(function(p) { return p.company === company.name; }) : null;
    var headcount = (typeof HEADCOUNT_ESTIMATES !== 'undefined')
      ? HEADCOUNT_ESTIMATES.find(function(h) { return h.company === company.name; }) : null;
    var moat = (typeof MOAT_PROFILES !== 'undefined')
      ? MOAT_PROFILES.find(function(m) { return m.company === company.name; }) : null;
    var founderDna = (typeof FOUNDER_DNA !== 'undefined')
      ? FOUNDER_DNA.find(function(f) { return f.company === company.name; }) : null;
    var clinicalTrials = (typeof CLINICAL_TRIALS !== 'undefined')
      ? CLINICAL_TRIALS.filter(function(t) {
          var hay = ((t.sponsor || '') + ' ' + (t.title || '')).toLowerCase();
          return hay.includes(company.name.toLowerCase());
        }) : [];
    var trl = getTRL(company);

    var today = new Date();
    var dateStr = today.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    var genStamp = today.toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' });

    // ─── Header date ───
    setText('ts-date', dateStr);
    setText('ts-footer-generated', 'Generated ' + genStamp);

    // ─── Document title / page title ───
    document.title = 'Tear Sheet · ' + company.name + ' | The Innovators League';

    // ─── Title row ───
    setText('ts-company-name', company.name || '—');

    // Meta line: sector · stage · HQ · website · ticker
    var website = (typeof getCompanyWebsite === 'function') ? getCompanyWebsite(company.name) : '';
    if (!website && company.website) website = company.website;
    var websiteDisplay = '';
    if (website) {
      try {
        websiteDisplay = String(website).replace(/^https?:\/\//, '').replace(/\/$/, '');
      } catch (e) { websiteDisplay = website; }
    }
    var metaParts = [];
    if (company.sector) metaParts.push(escapeHtml(company.sector));
    if (company.fundingStage) metaParts.push(escapeHtml(company.fundingStage));
    if (company.location) metaParts.push(escapeHtml(company.location));
    if (websiteDisplay) metaParts.push(escapeHtml(websiteDisplay));
    if (company.ticker) metaParts.push('NYSE/NASDAQ: ' + escapeHtml(company.ticker));
    setHtml('ts-company-meta', metaParts.join('<span class="ts-sep">·</span>'));

    // Description (limit to ~3 sentences / ~380 chars)
    var desc = company.description || '';
    if (desc.length > 420) {
      // Truncate at last period before 420 chars to preserve sentence boundary
      var cut = desc.slice(0, 420);
      var lastPeriod = cut.lastIndexOf('.');
      if (lastPeriod > 200) cut = cut.slice(0, lastPeriod + 1);
      desc = cut + (desc.length > cut.length ? '…' : '');
    }
    setText('ts-company-desc', desc || 'No description available.');

    // ─── Score block ───
    var scoreValue = '—';
    var scoreTier = 'UNRATED';
    if (innovatorScore) {
      var composite = innovatorScore.composite != null ? innovatorScore.composite : (innovatorScore.total != null ? innovatorScore.total : null);
      if (composite != null) {
        scoreValue = parseFloat(composite).toFixed(0);
        var ns = parseFloat(scoreValue);
        if (ns >= 90) scoreTier = 'ELITE';
        else if (ns >= 80) scoreTier = 'EXCEPTIONAL';
        else if (ns >= 70) scoreTier = 'STRONG';
        else scoreTier = 'PROMISING';
      }
    } else if (scores.composite != null) {
      scoreValue = String(scores.composite);
    }
    setText('ts-score-value', scoreValue);
    setText('ts-score-tier', scoreTier);

    // ─── Key stats grid ───
    var keyStats = [];
    keyStats.push({ label: 'Founded', value: company.founded || company.yearFounded || '—' });
    keyStats.push({ label: 'Total Raised', value: company.totalRaised || '—' });
    keyStats.push({ label: 'Valuation', value: company.valuation || 'Undisclosed' });
    keyStats.push({ label: 'HQ', value: company.location || '—' });
    var empVal = company.employees || (headcount && headcount.current ? String(headcount.current) : '—');
    keyStats.push({ label: 'Employees', value: empVal });
    if (company.ticker) {
      keyStats.push({ label: 'Ticker', value: company.ticker });
    } else if (trl) {
      keyStats.push({ label: 'TRL', value: 'TRL ' + trl + '/9' });
    } else {
      keyStats.push({ label: 'Stage', value: company.fundingStage || '—' });
    }
    var keyStatsHtml = keyStats.map(function(s) {
      return '<div class="ts-keystat">' +
        '<div class="ts-keystat-label">' + escapeHtml(s.label) + '</div>' +
        '<div class="ts-keystat-value">' + escapeHtml(s.value) + '</div>' +
      '</div>';
    }).join('');
    setHtml('ts-keystats-grid', keyStatsHtml);

    // ─── Founders / Leadership ───
    var foundersHtml = '';
    if (company.founder) {
      var names = String(company.founder).split(/,|\band\b|;/).map(function(n) { return n.trim(); }).filter(Boolean);
      foundersHtml += names.map(function(n, i) {
        var role = (i === 0) ? 'Founder &amp; CEO' : 'Co-founder';
        return '<div class="ts-founder-row">' +
          '<span class="ts-founder-name">' + escapeHtml(n) + '</span>' +
          '<span class="ts-founder-role">' + role + '</span>' +
        '</div>';
      }).join('');
      if (founderDna) {
        var dnaBits = [];
        if (founderDna.serialFounder) dnaBits.push('Serial founder');
        if (founderDna.dnaScore != null) dnaBits.push('DNA score: ' + founderDna.dnaScore);
        if (founderDna.mafias && founderDna.mafias.length) dnaBits.push('Mafia: ' + founderDna.mafias.join(', '));
        if (dnaBits.length) {
          foundersHtml += '<p style="margin-top:4px;font-size:8.5pt;color:#555;">' + escapeHtml(dnaBits.join(' · ')) + '</p>';
        }
      }
    } else {
      foundersHtml = '<span class="ts-empty">Leadership data unavailable.</span>';
    }
    setHtml('ts-founders', foundersHtml);

    // ─── Funding History table ───
    var fundingHtml = '';
    // Prefer DEAL_TRACKER entries (richer) if they exist, otherwise FUNDING_TRACKER summary
    var rows = [];
    if (dealEntries.length > 0) {
      rows = dealEntries.slice().sort(function(a, b) {
        return new Date(b.date || 0) - new Date(a.date || 0);
      }).map(function(d) {
        return {
          date: d.date || '',
          stage: d.round || d.type || '—',
          amount: d.amount || '—',
          lead: d.lead || d.investor || '—'
        };
      });
    } else if (fundingRounds.length > 0) {
      rows = fundingRounds.map(function(f) {
        return {
          date: f.lastRoundDate || '',
          stage: f.lastRound || '—',
          amount: f.lastRoundAmount || f.totalRaised || '—',
          lead: (f.leadInvestors && f.leadInvestors.length) ? f.leadInvestors.join(', ') : '—'
        };
      });
    }
    if (rows.length > 0) {
      // cap to top 6 to preserve one-page layout
      var maxRows = rows.slice(0, 6);
      fundingHtml = '<table class="ts-table"><thead><tr>' +
          '<th>Date</th><th>Stage</th><th class="ts-num">Amount</th><th>Lead Investor</th>' +
        '</tr></thead><tbody>' +
        maxRows.map(function(r) {
          return '<tr>' +
            '<td>' + escapeHtml(formatRoundDate(r.date)) + '</td>' +
            '<td>' + escapeHtml(r.stage) + '</td>' +
            '<td class="ts-num">' + escapeHtml(r.amount) + '</td>' +
            '<td>' + escapeHtml(truncate(r.lead, 40)) + '</td>' +
          '</tr>';
        }).join('') +
        '</tbody></table>' +
        '<p style="margin-top:3pt;font-size:7pt;color:#888;font-style:italic;">Source: Crunchbase · PitchBook · press releases</p>';
    } else if (company.totalRaised) {
      fundingHtml = '<p>Total raised: <strong>' + escapeHtml(company.totalRaised) + '</strong>';
      if (company.valuation) fundingHtml += ' · Last valuation: <strong>' + escapeHtml(company.valuation) + '</strong>';
      fundingHtml += '</p>';
    } else {
      fundingHtml = '<span class="ts-empty">No funding rounds tracked.</span>';
    }
    setHtml('ts-funding', fundingHtml);

    // ─── Traction signals ───
    var tractionItems = [];
    tractionItems.push({
      label: 'Gov contracts',
      value: govContracts.length > 0 ? String(govContracts.length) + ' on record' : '—',
      src: govContracts.length ? 'SAM.gov' : null
    });
    if (sbirAwards.length > 0) {
      tractionItems.push({ label: 'SBIR/STTR', value: String(sbirAwards.length) + ' awards', src: 'SBIR.gov' });
    }
    if (patents) {
      if (patents.totalPatents != null) {
        tractionItems.push({ label: 'Patents', value: String(patents.totalPatents), src: 'USPTO' });
      } else if (patents.patentCount != null) {
        tractionItems.push({ label: 'Patents', value: String(patents.patentCount), src: 'USPTO' });
      }
      if (patents.ipMoatScore != null) {
        tractionItems.push({ label: 'IP moat', value: String(patents.ipMoatScore) + '/10', src: null });
      }
    }
    if (headcount) {
      if (headcount.current != null) {
        tractionItems.push({ label: 'Headcount', value: String(headcount.current), src: 'LinkedIn est.' });
      }
      if (headcount.growth != null) {
        var g = String(headcount.growth);
        if (!g.startsWith('+') && !g.startsWith('-') && /^\d/.test(g)) g = '+' + g;
        tractionItems.push({ label: '12-mo trend', value: g, src: null });
      }
    }
    if (clinicalTrials.length > 0) {
      tractionItems.push({ label: 'Clinical trials', value: String(clinicalTrials.length), src: 'ClinicalTrials.gov' });
    }
    if (trl != null) {
      tractionItems.push({ label: 'Tech readiness', value: 'TRL ' + trl + '/9', src: null });
    }
    if (company.signal) {
      tractionItems.push({ label: 'Signal', value: String(company.signal).toUpperCase(), src: null });
    }
    if (company.recentEvent && company.recentEvent.text) {
      tractionItems.push({ label: 'Latest event', value: truncate(company.recentEvent.text, 36), src: null });
    }

    var tractionHtml = '';
    if (tractionItems.length > 0) {
      tractionHtml = '<div class="ts-traction-grid">' +
        tractionItems.slice(0, 10).map(function(t) {
          var src = t.src ? ' <span class="ts-source-tag">[' + escapeHtml(t.src) + ']</span>' : '';
          return '<div class="ts-traction-item">' +
            '<span class="ts-traction-label">' + escapeHtml(t.label) + src + '</span>' +
            '<span class="ts-traction-value">' + escapeHtml(t.value) + '</span>' +
          '</div>';
        }).join('') +
      '</div>';
    } else {
      tractionHtml = '<span class="ts-empty">No traction signals available.</span>';
    }
    setHtml('ts-traction', tractionHtml);

    // ─── Investment thesis (bull/bear/insight) ───
    var thesisHtml = '';
    if (company.thesis && company.thesis.bull) {
      thesisHtml += '<div class="ts-thesis-label">Bull</div>' +
        '<p>' + escapeHtml(company.thesis.bull) + '</p>';
    }
    if (company.thesis && company.thesis.bear) {
      thesisHtml += '<div class="ts-thesis-label">Bear</div>' +
        '<p>' + escapeHtml(company.thesis.bear) + '</p>';
    }
    if (!thesisHtml && company.insight) {
      thesisHtml = '<div class="ts-thesis-label">ROS Take</div>' +
        '<p>' + escapeHtml(company.insight) + '</p>';
    }
    if (!thesisHtml) {
      thesisHtml = '<span class="ts-empty">No published thesis.</span>';
    }
    setHtml('ts-thesis', thesisHtml);

    // ─── Competitive context ───
    var compHtml = '';
    var comps = Array.isArray(company.competitors) ? company.competitors.slice(0, 5) : [];
    if (comps.length > 0) {
      compHtml = '<div class="ts-competitor-list">' +
        comps.map(function(n) {
          return '<span class="ts-competitor-chip">' + escapeHtml(n) + '</span>';
        }).join('') +
      '</div>';
      // Quick comps: if any competitor is in COMPANIES, show a one-liner
      if (typeof COMPANIES !== 'undefined') {
        var compRows = comps.map(function(n) {
          var c = COMPANIES.find(function(x) { return x.name === n; });
          if (!c) return null;
          var bits = [];
          if (c.fundingStage) bits.push(c.fundingStage);
          if (c.totalRaised) bits.push(c.totalRaised);
          if (c.location) bits.push(c.location);
          return { name: n, detail: bits.join(' · ') };
        }).filter(Boolean);
        if (compRows.length > 0) {
          compHtml += '<ul style="margin-top:4pt;">' +
            compRows.map(function(r) {
              return '<li><strong>' + escapeHtml(r.name) + '</strong>' +
                (r.detail ? ' <span style="color:#666;">— ' + escapeHtml(r.detail) + '</span>' : '') + '</li>';
            }).join('') +
          '</ul>';
        }
      }
    } else {
      compHtml = '<span class="ts-empty">No direct competitors catalogued.</span>';
    }
    if (company.thesisCluster) {
      compHtml += '<p style="margin-top:4pt;font-size:8pt;color:#555;"><em>Thesis cluster: ' + escapeHtml(company.thesisCluster) + '</em></p>';
    }
    setHtml('ts-competitive', compHtml);

    // ─── Risks & Moats ───
    var rmHtml = '';
    // Moats
    var moatBullets = [];
    if (moat && Array.isArray(moat.moats)) {
      moat.moats.slice(0, 4).forEach(function(m) {
        if (typeof m === 'string') moatBullets.push(m);
        else if (m && m.title) moatBullets.push(m.title + (m.detail ? ' — ' + m.detail : ''));
      });
    }
    if (!moatBullets.length && company.techApproach) {
      moatBullets.push('Technical approach: ' + company.techApproach);
    }
    if (patents && patents.keyAreas && patents.keyAreas.length) {
      moatBullets.push('IP in: ' + patents.keyAreas.slice(0, 3).join(', '));
    }

    if (moatBullets.length > 0) {
      rmHtml += '<div class="ts-thesis-label">Moats</div><ul>' +
        moatBullets.map(function(b) { return '<li>' + escapeHtml(truncate(b, 180)) + '</li>'; }).join('') +
      '</ul>';
    }

    // Risks
    var riskBullets = [];
    if (company.thesis && Array.isArray(company.thesis.risks)) {
      riskBullets = company.thesis.risks.slice(0, 5);
    } else if (Array.isArray(company.risks)) {
      riskBullets = company.risks.slice(0, 5);
    }
    if (riskBullets.length > 0) {
      rmHtml += '<div class="ts-thesis-label">Risks</div><ul>' +
        riskBullets.map(function(r) { return '<li>' + escapeHtml(truncate(r, 180)) + '</li>'; }).join('') +
      '</ul>';
    }
    if (!rmHtml) {
      rmHtml = '<span class="ts-empty">No risks or moats catalogued.</span>';
    }
    setHtml('ts-risks-moats', rmHtml);

    // ─── Sources footer line — adapt based on what's actually used ───
    var sources = ['ROS research'];
    if (govContracts.length || sbirAwards.length) sources.unshift('SAM.gov');
    if (patents) sources.unshift('USPTO');
    if (company.ticker) sources.unshift('SEC EDGAR', 'Yahoo Finance');
    if (dealEntries.length || fundingRounds.length) sources.push('Crunchbase');
    if (clinicalTrials.length) sources.push('ClinicalTrials.gov');
    // Deduplicate while preserving order
    var seen = {};
    var dedup = sources.filter(function(s) { if (seen[s]) return false; seen[s] = true; return true; });
    var lastRefreshed = (typeof LAST_UPDATED !== 'undefined') ? LAST_UPDATED : (typeof DATA_SOURCES !== 'undefined' && DATA_SOURCES.companies ? DATA_SOURCES.companies.lastUpdated : '');
    var sourceLine = 'Sources: ' + dedup.join(' · ');
    if (lastRefreshed) sourceLine += ' · Last refreshed ' + lastRefreshed;
    setText('ts-sources', sourceLine);
  }

  // ─── Tear-sheet helpers ───
  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = (value == null || value === '') ? '—' : String(value);
  }
  function setHtml(id, html) {
    var el = document.getElementById(id);
    if (el) el.innerHTML = html || '—';
  }
  function formatRoundDate(dateStr) {
    if (!dateStr) return '—';
    try {
      var d = new Date(/^\d{4}-\d{2}$/.test(dateStr) ? dateStr + '-01' : dateStr);
      if (isNaN(d.getTime())) return String(dateStr);
      return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    } catch (e) { return String(dateStr); }
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
    if (typeof TRL_RANKINGS !== 'undefined' && Array.isArray(TRL_RANKINGS)) {
      var entry = TRL_RANKINGS.find(function(t) { return t.company === company.name; });
      if (entry) return entry.trl;
    }
    return null;
  }

  // ─── INTELLIGENCE BRIEF GENERATOR ───
  // Exposed globally for onclick handler
  window.generateIntelBrief = function() {
    if (!currentCompany) return;
    var c = currentCompany;
    var today = new Date().toISOString().split('T')[0];

    // Gather data from all sources
    var scores = c.scores || {};
    var trl = getTRL(c);

    // Funding history
    var fundingEntries = [];
    if (typeof DEAL_TRACKER !== 'undefined') {
      fundingEntries = DEAL_TRACKER.filter(function(d) { return d.company === c.name; });
    }

    // Gov contracts
    var govContracts = [];
    if (typeof GOV_CONTRACTS !== 'undefined') {
      govContracts = GOV_CONTRACTS.filter(function(g) { return g.company === c.name; });
    }

    // SBIR awards
    var sbirAwards = [];
    if (typeof SBIR_AWARDS !== 'undefined') {
      sbirAwards = SBIR_AWARDS.filter(function(s) { return s.company === c.name; });
    }

    // Patent intel
    var patents = null;
    if (typeof PATENT_INTEL !== 'undefined') {
      patents = PATENT_INTEL.find(function(p) { return p.company === c.name; });
    }

    // Headcount
    var headcount = null;
    if (typeof HEADCOUNT_ESTIMATES !== 'undefined') {
      headcount = HEADCOUNT_ESTIMATES.find(function(h) { return h.company === c.name; });
    }

    // Founder DNA
    var founderDna = null;
    if (typeof FOUNDER_DNA !== 'undefined') {
      founderDna = FOUNDER_DNA.find(function(f) { return f.company === c.name; });
    }

    // Moat profile
    var moat = null;
    if (typeof MOAT_PROFILES !== 'undefined') {
      moat = MOAT_PROFILES.find(function(m) { return m.company === c.name; });
    }

    // Predictive scores
    var predictive = null;
    if (typeof PREDICTIVE_SCORES !== 'undefined') {
      predictive = PREDICTIVE_SCORES.find(function(p) { return p.company === c.name; });
    }

    // Contractor readiness
    var contractor = null;
    if (typeof CONTRACTOR_READINESS !== 'undefined') {
      contractor = CONTRACTOR_READINESS.find(function(cr) { return cr.company === c.name; });
    }

    // News signals
    var newsItems = [];
    if (typeof NEWS_SIGNALS !== 'undefined') {
      newsItems = NEWS_SIGNALS.filter(function(n) { return n.company === c.name; }).slice(0, 5);
    }

    // SEC filings
    var secFilings = [];
    if (typeof SEC_FILINGS_LIVE !== 'undefined') {
      secFilings = SEC_FILINGS_LIVE.filter(function(s) { return s.company === c.name; }).slice(0, 5);
    }

    // Build brief HTML
    var briefHTML = '<!DOCTYPE html><html><head><meta charset="UTF-8">' +
      '<title>Intel Brief: ' + c.name + '</title>' +
      '<style>' +
      'body{font-family:"Inter",sans-serif;max-width:800px;margin:0 auto;padding:40px;color:#1a1a2e;line-height:1.6;background:#fff;}' +
      'h1{font-family:"Space Grotesk",sans-serif;font-size:28px;border-bottom:3px solid #FF6B2C;padding-bottom:12px;margin-bottom:4px;}' +
      '.brief-meta{color:#666;font-size:13px;margin-bottom:32px;border-bottom:1px solid #ddd;padding-bottom:16px;}' +
      'h2{font-family:"Space Grotesk",sans-serif;font-size:18px;color:#FF6B2C;text-transform:uppercase;letter-spacing:2px;margin-top:32px;margin-bottom:12px;border-bottom:1px solid #eee;padding-bottom:8px;}' +
      'h3{font-size:14px;font-weight:600;margin:16px 0 8px;}' +
      '.stat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin:16px 0;}' +
      '.stat-box{background:#f8f9fa;border:1px solid #e5e7eb;border-radius:8px;padding:12px;text-align:center;}' +
      '.stat-box .label{font-size:11px;color:#666;text-transform:uppercase;letter-spacing:1px;}' +
      '.stat-box .value{font-size:20px;font-weight:700;color:#1a1a2e;margin-top:4px;}' +
      '.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;margin:2px;}' +
      '.badge-orange{background:#FFF3ED;color:#FF6B2C;}' +
      '.badge-green{background:#ECFDF5;color:#059669;}' +
      '.badge-blue{background:#EFF6FF;color:#2563EB;}' +
      '.badge-red{background:#FEF2F2;color:#DC2626;}' +
      'table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px;}' +
      'th{background:#f8f9fa;text-align:left;padding:8px;border-bottom:2px solid #ddd;font-weight:600;}' +
      'td{padding:8px;border-bottom:1px solid #eee;}' +
      '.section-note{font-size:12px;color:#999;font-style:italic;margin-top:4px;}' +
      '.thesis-box{background:#FFF8F5;border-left:3px solid #FF6B2C;padding:16px;margin:12px 0;border-radius:0 8px 8px 0;}' +
      '.risk-box{background:#FEF2F2;border-left:3px solid #DC2626;padding:16px;margin:12px 0;border-radius:0 8px 8px 0;}' +
      '@media print{body{padding:20px;font-size:11px;}h1{font-size:22px;}h2{font-size:15px;margin-top:24px;}' +
      '.stat-grid{grid-template-columns:repeat(4,1fr);}.no-print{display:none!important;}}' +
      '</style></head><body>';

    // Header
    briefHTML += '<h1>INTELLIGENCE BRIEF: ' + c.name.toUpperCase() + '</h1>';
    briefHTML += '<div class="brief-meta">';
    briefHTML += '<strong>Classification:</strong> UNCLASSIFIED // TIL<br>';
    briefHTML += '<strong>Date:</strong> ' + today + '<br>';
    briefHTML += '<strong>Analyst:</strong> Rational Optimist Society — The Innovators League<br>';
    briefHTML += '<strong>Sector:</strong> ' + (c.sector || 'N/A') + ' | <strong>Stage:</strong> ' + (c.fundingStage || 'N/A') + ' | <strong>Location:</strong> ' + (c.location || 'N/A');
    briefHTML += '</div>';

    // SECTION 1: Executive Summary
    briefHTML += '<h2>1. Executive Summary</h2>';
    briefHTML += '<p>' + (c.description || 'No description available.') + '</p>';
    briefHTML += '<div class="stat-grid">';
    briefHTML += '<div class="stat-box"><div class="label">Frontier Score</div><div class="value">' + (scores.composite || 'N/A') + '</div></div>';
    briefHTML += '<div class="stat-box"><div class="label">Founded</div><div class="value">' + (c.yearFounded || 'N/A') + '</div></div>';
    briefHTML += '<div class="stat-box"><div class="label">Total Raised</div><div class="value">' + (c.totalRaised || 'N/A') + '</div></div>';
    briefHTML += '<div class="stat-box"><div class="label">Valuation</div><div class="value">' + (c.valuation || 'N/A') + '</div></div>';
    if (trl) briefHTML += '<div class="stat-box"><div class="label">TRL Level</div><div class="value">' + trl + '/9</div></div>';
    if (c.signal) briefHTML += '<div class="stat-box"><div class="label">Signal</div><div class="value">' + c.signal + '</div></div>';
    briefHTML += '</div>';

    // Score dimensions
    if (scores.dimensions) {
      briefHTML += '<h3>Score Dimensions</h3>';
      briefHTML += '<div class="stat-grid">';
      var dims = scores.dimensions;
      if (dims.innovation != null) briefHTML += '<div class="stat-box"><div class="label">Innovation</div><div class="value">' + dims.innovation + '</div></div>';
      if (dims.execution != null) briefHTML += '<div class="stat-box"><div class="label">Execution</div><div class="value">' + dims.execution + '</div></div>';
      if (dims.market != null) briefHTML += '<div class="stat-box"><div class="label">Market</div><div class="value">' + dims.market + '</div></div>';
      if (dims.team != null) briefHTML += '<div class="stat-box"><div class="label">Team</div><div class="value">' + dims.team + '</div></div>';
      if (dims.defensibility != null) briefHTML += '<div class="stat-box"><div class="label">Defensibility</div><div class="value">' + dims.defensibility + '</div></div>';
      if (dims.momentum != null) briefHTML += '<div class="stat-box"><div class="label">Momentum</div><div class="value">' + dims.momentum + '</div></div>';
      briefHTML += '</div>';
    }

    // SECTION 2: Financial Intelligence
    briefHTML += '<h2>2. Financial Intelligence</h2>';
    if (fundingEntries.length > 0) {
      briefHTML += '<table><tr><th>Date</th><th>Round</th><th>Amount</th><th>Valuation</th><th>Lead</th></tr>';
      fundingEntries.forEach(function(d) {
        briefHTML += '<tr><td>' + (d.date || 'N/A') + '</td><td>' + (d.round || d.type || 'N/A') + '</td><td>' + (d.amount || 'N/A') + '</td><td>' + (d.valuation || '-') + '</td><td>' + (d.lead || '-') + '</td></tr>';
      });
      briefHTML += '</table>';
    } else {
      briefHTML += '<p class="section-note">No funding events tracked.</p>';
    }

    if (c.investors && c.investors.length > 0) {
      briefHTML += '<h3>Key Investors</h3><p>';
      briefHTML += c.investors.join(', ');
      briefHTML += '</p>';
    }

    // SECTION 3: Government Traction
    briefHTML += '<h2>3. Government Traction</h2>';
    if (contractor) {
      briefHTML += '<div class="stat-grid">';
      briefHTML += '<div class="stat-box"><div class="label">Readiness Score</div><div class="value">' + (contractor.score || 'N/A') + '</div></div>';
      if (contractor.clearance) briefHTML += '<div class="stat-box"><div class="label">Clearance</div><div class="value">' + contractor.clearance + '</div></div>';
      if (contractor.cmmc) briefHTML += '<div class="stat-box"><div class="label">CMMC Level</div><div class="value">' + contractor.cmmc + '</div></div>';
      briefHTML += '</div>';
    }

    if (govContracts.length > 0) {
      briefHTML += '<h3>Government Contracts (' + govContracts.length + ')</h3>';
      briefHTML += '<table><tr><th>Agency</th><th>Description</th><th>Value</th><th>Date</th></tr>';
      govContracts.forEach(function(g) {
        briefHTML += '<tr><td>' + (g.agency || 'N/A') + '</td><td>' + (g.description || g.title || '-').substring(0, 80) + '</td><td>' + (g.value || g.amount || '-') + '</td><td>' + (g.date || '-') + '</td></tr>';
      });
      briefHTML += '</table>';
    }

    if (sbirAwards.length > 0) {
      briefHTML += '<h3>SBIR/STTR Awards (' + sbirAwards.length + ')</h3>';
      briefHTML += '<table><tr><th>Agency</th><th>Phase</th><th>Topic</th><th>Amount</th></tr>';
      sbirAwards.forEach(function(s) {
        briefHTML += '<tr><td>' + (s.agency || 'N/A') + '</td><td>' + (s.phase || '-') + '</td><td>' + (s.topic || s.title || '-').substring(0, 60) + '</td><td>' + (s.amount || '-') + '</td></tr>';
      });
      briefHTML += '</table>';
    }

    if (!govContracts.length && !sbirAwards.length && !contractor) {
      briefHTML += '<p class="section-note">No government traction data available.</p>';
    }

    // SECTION 4: Technology Assessment
    briefHTML += '<h2>4. Technology Assessment</h2>';
    if (trl) {
      briefHTML += '<p><strong>Technology Readiness Level:</strong> TRL ' + trl + '/9</p>';
    }
    if (patents) {
      briefHTML += '<div class="stat-grid">';
      if (patents.totalPatents != null) briefHTML += '<div class="stat-box"><div class="label">Total Patents</div><div class="value">' + patents.totalPatents + '</div></div>';
      if (patents.pendingPatents != null) briefHTML += '<div class="stat-box"><div class="label">Pending</div><div class="value">' + patents.pendingPatents + '</div></div>';
      if (patents.ipMoatScore != null) briefHTML += '<div class="stat-box"><div class="label">IP Moat Score</div><div class="value">' + patents.ipMoatScore + '</div></div>';
      if (patents.patentVelocity != null) briefHTML += '<div class="stat-box"><div class="label">Patent Velocity</div><div class="value">' + patents.patentVelocity + '/yr</div></div>';
      briefHTML += '</div>';
      if (patents.keyAreas && patents.keyAreas.length > 0) {
        briefHTML += '<h3>Key Patent Areas</h3><p>' + patents.keyAreas.join(', ') + '</p>';
      }
    }

    if (c.thesisCluster) {
      briefHTML += '<h3>Thesis Cluster</h3><p>' + c.thesisCluster + '</p>';
    }

    // SECTION 5: Competitive Landscape
    briefHTML += '<h2>5. Competitive Landscape</h2>';
    if (c.competitors && c.competitors.length > 0) {
      briefHTML += '<h3>Direct Competitors</h3><p>' + c.competitors.join(', ') + '</p>';
    }
    if (predictive) {
      briefHTML += '<div class="stat-grid">';
      if (predictive.maTarget != null) briefHTML += '<div class="stat-box"><div class="label">M&A Target Prob.</div><div class="value">' + predictive.maTarget + '%</div></div>';
      if (predictive.ipoReadiness != null) briefHTML += '<div class="stat-box"><div class="label">IPO Readiness</div><div class="value">' + predictive.ipoReadiness + '</div></div>';
      if (predictive.failureRisk != null) briefHTML += '<div class="stat-box"><div class="label">Failure Risk</div><div class="value">' + predictive.failureRisk + '%</div></div>';
      briefHTML += '</div>';
    }

    // SECTION 6: Team & Network
    briefHTML += '<h2>6. Team & Network</h2>';
    if (c.founder) briefHTML += '<p><strong>Founder(s):</strong> ' + c.founder + '</p>';

    if (founderDna) {
      briefHTML += '<div class="stat-grid">';
      if (founderDna.dnaScore != null) briefHTML += '<div class="stat-box"><div class="label">Founder DNA Score</div><div class="value">' + founderDna.dnaScore + '</div></div>';
      if (founderDna.serialFounder) briefHTML += '<div class="stat-box"><div class="label">Serial Founder</div><div class="value">Yes</div></div>';
      if (founderDna.mafias && founderDna.mafias.length > 0) briefHTML += '<div class="stat-box"><div class="label">Mafia Network</div><div class="value">' + founderDna.mafias.join(', ') + '</div></div>';
      briefHTML += '</div>';
    }

    if (headcount) {
      briefHTML += '<h3>Headcount</h3>';
      briefHTML += '<div class="stat-grid">';
      if (headcount.current != null) briefHTML += '<div class="stat-box"><div class="label">Current</div><div class="value">' + headcount.current + '</div></div>';
      if (headcount.growth != null) briefHTML += '<div class="stat-box"><div class="label">Growth</div><div class="value">' + headcount.growth + '</div></div>';
      briefHTML += '</div>';
    }

    // SECTION 7: Risk Assessment
    briefHTML += '<h2>7. Risk Assessment</h2>';
    if (c.thesis && c.thesis.bear) {
      briefHTML += '<div class="risk-box"><strong>Bear Case:</strong> ' + c.thesis.bear + '</div>';
    }
    if (c.risks && c.risks.length > 0) {
      briefHTML += '<h3>Key Risks</h3><ul>';
      c.risks.forEach(function(r) { briefHTML += '<li>' + r + '</li>'; });
      briefHTML += '</ul>';
    }
    if (predictive && predictive.failureRisk != null) {
      briefHTML += '<p><strong>Quantified Failure Risk:</strong> ' + predictive.failureRisk + '%</p>';
    }

    // SECTION 8: ROS Editorial Take
    briefHTML += '<h2>8. ROS Editorial Take</h2>';
    if (c.thesis) {
      if (c.thesis.bull) {
        briefHTML += '<div class="thesis-box"><strong>Bull Case:</strong> ' + c.thesis.bull + '</div>';
      }
      if (c.thesis.insight) {
        briefHTML += '<p><strong>Key Insight:</strong> ' + c.thesis.insight + '</p>';
      }
    }
    if (c.rosCoverage) {
      briefHTML += '<h3>ROS Coverage</h3><p>' + c.rosCoverage + '</p>';
    }
    if (c.conviction) {
      briefHTML += '<p><strong>Conviction Level:</strong> <span class="badge badge-orange">' + c.conviction + '</span></p>';
    }

    // Footer
    briefHTML += '<hr style="margin-top:40px;border:none;border-top:1px solid #ddd;">';
    briefHTML += '<p style="font-size:11px;color:#999;text-align:center;margin-top:16px;">Generated by The Innovators League — Rational Optimist Society | ' + today + '</p>';
    briefHTML += '<p class="no-print" style="text-align:center;margin-top:16px;"><button onclick="window.print()" style="background:#FF6B2C;color:#fff;border:none;padding:12px 24px;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600;">Print / Export PDF</button></p>';
    briefHTML += '</body></html>';

    // Open in new window
    var briefWindow = window.open('', '_blank');
    if (briefWindow) {
      briefWindow.document.write(briefHTML);
      briefWindow.document.close();
    }
  };

  // ─── COMPANY TIMELINE ───
  function renderCompanyTimeline(company) {
    var card = document.getElementById('timeline-card');
    var container = document.getElementById('company-timeline');
    var filtersContainer = document.getElementById('timeline-filters');
    if (!card || !container) return;

    var events = [];
    var nameLower = company.name.toLowerCase();

    // Gather events from all data sources
    // 1. Funding rounds
    if (typeof FUNDING_TRACKER !== 'undefined') {
      FUNDING_TRACKER.filter(function(f) { return f.company === company.name; }).forEach(function(f) {
        events.push({
          date: f.date,
          type: 'funding',
          icon: '\uD83D\uDCB0',
          title: escapeHtml((f.stage || f.type || 'Funding') + ' \u2014 ' + (f.amount || 'Undisclosed')),
          detail: f.investor ? 'Lead: ' + escapeHtml(f.investor) : '',
          color: '#22c55e'
        });
      });
    }

    // 2. Government contracts
    if (typeof GOV_CONTRACTS !== 'undefined') {
      GOV_CONTRACTS.filter(function(c) {
        var cn = (c.company || '').toLowerCase();
        return cn === nameLower || nameLower.includes(cn) || cn.includes(nameLower);
      }).forEach(function(c) {
        events.push({
          date: c.date || c.awardDate,
          type: 'contract',
          icon: '\uD83C\uDFDB\uFE0F',
          title: escapeHtml((c.agency || 'Government') + ' Contract'),
          detail: escapeHtml(c.value || c.description || ''),
          color: '#3b82f6'
        });
      });
    }

    // 3. SEC filings
    if (typeof SEC_FILINGS_LIVE !== 'undefined') {
      SEC_FILINGS_LIVE.filter(function(f) { return (f.company || '').toLowerCase().includes(nameLower); }).forEach(function(f) {
        events.push({
          date: f.date || f.filingDate,
          type: 'sec',
          icon: '\uD83D\uDCC4',
          title: escapeHtml('SEC Filing: ' + (f.form || f.type || 'Filing')),
          detail: f.description ? escapeHtml(truncate(f.description, 80)) : '',
          color: '#f59e0b'
        });
      });
    }

    // 4. News
    if (typeof NEWS_FEED !== 'undefined') {
      NEWS_FEED.filter(function(n) { return (n.companies || []).includes(company.name) || (n.headline || '').includes(company.name); }).slice(0, 10).forEach(function(n) {
        events.push({
          date: n.date,
          type: 'news',
          icon: '\uD83D\uDCF0',
          title: escapeHtml(n.headline || 'News'),
          detail: n.source ? escapeHtml(n.source) : '',
          color: '#a855f7',
          url: n.url
        });
      });
    }

    // 5. Patent filings
    if (typeof PATENT_INTEL_AUTO !== 'undefined') {
      PATENT_INTEL_AUTO.filter(function(p) { return p.company === company.name; }).forEach(function(p) {
        if (p.latestPatentDate) {
          events.push({
            date: p.latestPatentDate,
            type: 'patent',
            icon: '\uD83D\uDCDC',
            title: escapeHtml('Patent Activity \u2014 ' + (p.patentCount || '') + ' patents'),
            detail: (p.technologyAreas || []).slice(0, 3).map(function(t) { return escapeHtml(t); }).join(', '),
            color: '#06b6d4'
          });
        }
      });
    }

    // 6. Product launches
    if (typeof PRODUCT_LAUNCHES !== 'undefined') {
      PRODUCT_LAUNCHES.filter(function(p) { return (p.company || '').toLowerCase().includes(nameLower); }).forEach(function(p) {
        events.push({
          date: p.date,
          type: 'product',
          icon: '\uD83D\uDE80',
          title: escapeHtml(p.title || 'Product Launch'),
          detail: p.description ? escapeHtml(truncate(p.description, 80)) : '',
          color: '#ec4899'
        });
      });
    }

    // 7. Clinical trials
    if (typeof CLINICAL_TRIALS !== 'undefined') {
      CLINICAL_TRIALS.filter(function(t) {
        var text = ((t.sponsor || '') + ' ' + (t.title || '')).toLowerCase();
        return text.includes(nameLower);
      }).slice(0, 5).forEach(function(t) {
        events.push({
          date: t.lastUpdated || t.startDate,
          type: 'trial',
          icon: '\uD83E\uDDEC',
          title: escapeHtml(truncate(t.title || 'Clinical Trial', 80)),
          detail: escapeHtml((t.status || '').replace(/_/g, ' ') + (t.phase ? ' \u2014 ' + t.phase : '')),
          color: '#14b8a6'
        });
      });
    }

    // 8. Recent events from company data
    if (company.recentEvent) {
      events.push({
        date: company.recentEvent.date,
        type: 'event',
        icon: '\u26A1',
        title: escapeHtml(company.recentEvent.type || 'Event'),
        detail: escapeHtml(company.recentEvent.text || ''),
        color: '#FF6B2C'
      });
    }

    if (events.length === 0) return;

    // Sort by date (newest first)
    events.sort(function(a, b) {
      var da = a.date ? new Date(a.date) : new Date(0);
      var db = b.date ? new Date(b.date) : new Date(0);
      return db - da;
    });

    card.style.display = '';

    // Get unique event types for filters
    var types = [];
    var seenTypes = {};
    events.forEach(function(e) {
      if (!seenTypes[e.type]) {
        seenTypes[e.type] = true;
        types.push(e.type);
      }
    });
    var activeFilters = new Set(types);

    // Render filter chips
    var typeLabels = { funding: 'Funding', contract: 'Contracts', sec: 'SEC Filings', news: 'News', patent: 'Patents', product: 'Products', trial: 'Trials', event: 'Events' };
    filtersContainer.innerHTML = types.map(function(t) {
      return '<button class="timeline-filter-chip active" data-type="' + t + '">' + (typeLabels[t] || t) + '</button>';
    }).join('');

    function renderTimeline() {
      var filtered = events.filter(function(e) { return activeFilters.has(e.type); });
      container.innerHTML = '<div class="timeline-line">' +
        filtered.map(function(e) {
          var dateStr = e.date ? formatDateAbsolute(e.date) : '';
          var linkOpen = e.url ? '<a href="' + sanitizeUrl(e.url) + '" target="_blank" rel="noopener" class="timeline-event-link">' : '<div class="timeline-event-content">';
          var linkClose = e.url ? '</a>' : '</div>';
          return '<div class="timeline-event" data-type="' + e.type + '">' +
            '<div class="timeline-dot" style="background:' + e.color + ';">' + e.icon + '</div>' +
            '<div class="timeline-event-body">' +
              '<div class="timeline-date">' + dateStr + '</div>' +
              linkOpen +
                '<div class="timeline-title">' + e.title + '</div>' +
                (e.detail ? '<div class="timeline-detail">' + e.detail + '</div>' : '') +
              linkClose +
            '</div>' +
          '</div>';
        }).join('') +
      '</div>';
    }

    renderTimeline();

    // Filter click handlers
    filtersContainer.querySelectorAll('.timeline-filter-chip').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var type = this.dataset.type;
        if (activeFilters.has(type)) {
          activeFilters.delete(type);
          this.classList.remove('active');
        } else {
          activeFilters.add(type);
          this.classList.add('active');
        }
        renderTimeline();
      });
    });
  }

})();
