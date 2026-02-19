// ═══════════════════════════════════════════════════════════════════════════════
// ROS FUND INTELLIGENCE — Deal Flow Engine
// Private page: proprietary deal sourcing, thesis matching, pipeline management
// ═══════════════════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  // ─── CONSTANTS ───
  const KANBAN_COLUMNS = [
    { id: 'sourced', title: 'Sourced' },
    { id: 'meeting', title: 'Meeting' },
    { id: 'dd', title: 'Due Diligence' },
    { id: 'termsheet', title: 'Term Sheet' },
    { id: 'closed', title: 'Closed' }
  ];

  const FRONTIER_SECTORS = [
    'Defense & Security', 'Space & Aerospace', 'AI & Software',
    'Nuclear Energy', 'Quantum Computing', 'Robotics & Manufacturing',
    'Supersonic & Hypersonic', 'Drones & Autonomous'
  ];

  const THESIS_LEGEND = [
    { label: 'Stage Fit', cls: 'lb-bar-stage', color: '#8b5cf6' },
    { label: 'Sector Fit', cls: 'lb-bar-sector', color: '#60a5fa' },
    { label: 'Innovator', cls: 'lb-bar-innovator', color: '#22c55e' },
    { label: 'Gov Traction', cls: 'lb-bar-gov', color: '#f59e0b' },
    { label: 'Founder', cls: 'lb-bar-founder', color: '#ec4899' },
    { label: 'Growth', cls: 'lb-bar-growth', color: '#14b8a6' }
  ];

  // ─── SAFE INIT ───
  function safeInit(name, fn) {
    try {
      fn();
    } catch (e) {
      console.error('[DealFlow] ' + name + ' failed:', e);
    }
  }

  // ─── DATA HELPERS ───
  function getCompanies() {
    return typeof COMPANIES !== 'undefined' ? COMPANIES : [];
  }

  function getInnovatorScore(companyName) {
    if (typeof INNOVATOR_SCORES === 'undefined') return null;
    return INNOVATOR_SCORES.find(s => s.company === companyName) || null;
  }

  function getMosaicScore(companyName) {
    if (typeof MOSAIC_SCORES === 'undefined') return null;
    return MOSAIC_SCORES[companyName] || null;
  }

  function getRevenueIntel(companyName) {
    if (typeof REVENUE_INTEL === 'undefined') return null;
    return REVENUE_INTEL.find(r => r.company === companyName) || null;
  }

  function getPredictiveIPO(companyName) {
    if (typeof PREDICTIVE_SCORES === 'undefined') return null;
    return (PREDICTIVE_SCORES.ipoReadiness && PREDICTIVE_SCORES.ipoReadiness.companies)
      ? PREDICTIVE_SCORES.ipoReadiness.companies[companyName] || null
      : null;
  }

  function getPredictiveMA(companyName) {
    if (typeof PREDICTIVE_SCORES === 'undefined') return null;
    return (PREDICTIVE_SCORES.maTarget && PREDICTIVE_SCORES.maTarget.companies)
      ? PREDICTIVE_SCORES.maTarget.companies[companyName] || null
      : null;
  }

  function getPredictiveFailure(companyName) {
    if (typeof PREDICTIVE_SCORES === 'undefined') return null;
    return (PREDICTIVE_SCORES.failureRisk && PREDICTIVE_SCORES.failureRisk.companies)
      ? PREDICTIVE_SCORES.failureRisk.companies[companyName] || null
      : null;
  }

  function getPredictiveNextRound(companyName) {
    if (typeof PREDICTIVE_SCORES === 'undefined') return null;
    return (PREDICTIVE_SCORES.nextRound && PREDICTIVE_SCORES.nextRound.predictions)
      ? PREDICTIVE_SCORES.nextRound.predictions[companyName] || null
      : null;
  }

  function getDealFlowSignal(companyName) {
    if (typeof DEAL_FLOW_SIGNALS === 'undefined') return null;
    return DEAL_FLOW_SIGNALS.find(d => d.company === companyName) || null;
  }

  function getFounderConnection(companyName) {
    if (typeof FOUNDER_CONNECTIONS === 'undefined') return null;
    return FOUNDER_CONNECTIONS[companyName] || null;
  }

  function getContractorReadiness(companyName) {
    if (typeof CONTRACTOR_READINESS === 'undefined') return null;
    return CONTRACTOR_READINESS.find(c => c.company === companyName) || null;
  }

  function getAltData(companyName) {
    if (typeof ALT_DATA_SIGNALS === 'undefined') return null;
    return ALT_DATA_SIGNALS.find(a => a.company === companyName) || null;
  }

  function getSectorColor(sectorName) {
    if (typeof SECTORS !== 'undefined' && SECTORS[sectorName]) {
      return SECTORS[sectorName].color;
    }
    return '#8b5cf6';
  }

  function normalizeFundingStage(stage) {
    if (!stage) return '';
    return stage.replace(/\+/g, '').trim();
  }

  function stageIsSeedOrA(stage) {
    if (!stage) return false;
    const s = stage.toLowerCase();
    return s.includes('seed') || s.includes('series a') || s === 'pre-seed' || s === 'angel';
  }

  function stageIsB(stage) {
    if (!stage) return false;
    return stage.toLowerCase().includes('series b');
  }

  // ─── THESIS SCORE CALCULATION ───
  function calcThesisScore(company) {
    let stage = 0, sector = 0, innovator = 0, gov = 0, founder = 0, growth = 0;

    // Stage fit (30 pts): Seed/Series A = 30, Series B = 20, Later = 10
    if (stageIsSeedOrA(company.fundingStage)) {
      stage = 30;
    } else if (stageIsB(company.fundingStage)) {
      stage = 20;
    } else if (company.fundingStage) {
      stage = 10;
    }

    // Sector fit (20 pts): Frontier sectors = 20, Others = 10
    if (FRONTIER_SECTORS.includes(company.sector)) {
      sector = 20;
    } else if (company.sector) {
      sector = 10;
    }

    // Innovator Score (20 pts): composite/100 * 20
    var innScore = getInnovatorScore(company.name);
    if (innScore && innScore.composite) {
      innovator = Math.round((innScore.composite / 100) * 20);
    } else {
      // Fall back to MOSAIC_SCORES
      var mosaic = getMosaicScore(company.name);
      if (mosaic && mosaic.total) {
        innovator = Math.round((mosaic.total / 1000) * 20);
      }
    }

    // Gov traction (15 pts)
    var contractor = getContractorReadiness(company.name);
    var hasGovTags = company.tags && company.tags.some(t =>
      t.toLowerCase().includes('defense') || t.toLowerCase().includes('government') ||
      t.toLowerCase().includes('military') || t.toLowerCase().includes('dod')
    );
    if (contractor || hasGovTags) {
      gov = 15;
    }
    // Also check GOV_DEMAND_TRACKER for matching companies
    if (gov === 0 && typeof GOV_DEMAND_TRACKER !== 'undefined') {
      var hasGovDemand = GOV_DEMAND_TRACKER.some(g =>
        g.relatedCompanies && g.relatedCompanies.includes(company.name)
      );
      if (hasGovDemand) gov = 15;
    }

    // Founder quality (10 pts)
    var fc = getFounderConnection(company.name);
    if (fc && (fc.metFounder || fc.exclusiveQuote)) {
      founder = 10;
    } else if (company.founder && company.founder.split(',').length >= 2) {
      // Multiple founders is a positive signal
      founder = 5;
    }

    // Revenue growth (5 pts)
    var rev = getRevenueIntel(company.name);
    if (rev && rev.growth && rev.growth !== 'N/A' && !rev.growth.includes('-')) {
      growth = 5;
    }
    // Alt data signal
    if (growth === 0) {
      var alt = getAltData(company.name);
      if (alt && (alt.hiringVelocity === 'surging' || alt.webTraffic === 'up')) {
        growth = 3;
      }
    }

    var total = stage + sector + innovator + gov + founder + growth;
    return {
      total: total,
      breakdown: { stage: stage, sector: sector, innovator: innovator, gov: gov, founder: founder, growth: growth }
    };
  }

  // ─── LOCAL STORAGE HELPERS ───
  function loadPipeline() {
    try {
      var raw = localStorage.getItem('ros-pipeline');
      if (raw) {
        var parsed = JSON.parse(raw);
        // Ensure all columns exist
        KANBAN_COLUMNS.forEach(function(col) {
          if (!Array.isArray(parsed[col.id])) parsed[col.id] = [];
        });
        return parsed;
      }
    } catch (e) { /* ignore */ }
    var empty = {};
    KANBAN_COLUMNS.forEach(function(col) { empty[col.id] = []; });
    return empty;
  }

  function savePipeline(pipeline) {
    try { localStorage.setItem('ros-pipeline', JSON.stringify(pipeline)); } catch (e) { /* ignore */ }
  }

  function loadNotes() {
    try {
      var raw = localStorage.getItem('ros-notes');
      return raw ? JSON.parse(raw) : {};
    } catch (e) { return {}; }
  }

  function saveNotes(notes) {
    try { localStorage.setItem('ros-notes', JSON.stringify(notes)); } catch (e) { /* ignore */ }
  }

  // ═══════════════════════════════════════════
  // HERO STATS
  // ═══════════════════════════════════════════
  function initHeroStats() {
    var pipeline = loadPipeline();
    var pipelineCount = 0;
    KANBAN_COLUMNS.forEach(function(col) {
      pipelineCount += (pipeline[col.id] || []).length;
    });

    // Thesis matches: companies with score > 70
    var companies = getCompanies();
    var thesisMatches = 0;
    companies.forEach(function(c) {
      var ts = calcThesisScore(c);
      if (ts.total > 70) thesisMatches++;
    });

    // Upcoming rounds count
    var upcomingCount = 0;
    if (typeof DEAL_FLOW_SIGNALS !== 'undefined') upcomingCount += DEAL_FLOW_SIGNALS.length;
    if (typeof PREDICTIVE_SCORES !== 'undefined' && PREDICTIVE_SCORES.nextRound && PREDICTIVE_SCORES.nextRound.predictions) {
      upcomingCount += Object.keys(PREDICTIVE_SCORES.nextRound.predictions).length;
    }
    // Deduplicate
    var allNames = new Set();
    if (typeof DEAL_FLOW_SIGNALS !== 'undefined') {
      DEAL_FLOW_SIGNALS.forEach(function(d) { allNames.add(d.company); });
    }
    if (typeof PREDICTIVE_SCORES !== 'undefined' && PREDICTIVE_SCORES.nextRound && PREDICTIVE_SCORES.nextRound.predictions) {
      Object.keys(PREDICTIVE_SCORES.nextRound.predictions).forEach(function(k) { allNames.add(k); });
    }

    animateCounter('df-pipeline-count', pipelineCount);
    animateCounter('df-thesis-matches', thesisMatches);
    animateCounter('df-upcoming', allNames.size);
  }

  function animateCounter(id, target) {
    var el = document.getElementById(id);
    if (!el) return;
    if (target === 0) { el.textContent = '0'; return; }
    var start = 0;
    var duration = 800;
    var startTime = performance.now();
    function step(ts) {
      var elapsed = ts - startTime;
      var progress = Math.min(elapsed / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // ═══════════════════════════════════════════
  // THESIS SCREENER
  // ═══════════════════════════════════════════
  var screenerState = {
    sector: '',
    stage: '',
    minScore: 70,
    signal: '',
    location: '',
    valuation: ''
  };

  function initThesisScreener() {
    var container = document.getElementById('screener-filters');
    if (!container) return;

    var sectors = typeof SCREENER_FILTERS !== 'undefined' ? SCREENER_FILTERS.sectors : Object.keys(typeof SECTORS !== 'undefined' ? SECTORS : {});
    var stages = typeof SCREENER_FILTERS !== 'undefined' ? SCREENER_FILTERS.stages : [];
    var valuations = typeof SCREENER_FILTERS !== 'undefined' ? SCREENER_FILTERS.valuationRanges : [];
    var signals = typeof SCREENER_FILTERS !== 'undefined' ? SCREENER_FILTERS.signals : [];
    var locations = typeof SCREENER_FILTERS !== 'undefined' ? SCREENER_FILTERS.locations : [];

    container.innerHTML =
      buildFilterSelect('sector', 'Sector', [{ v: '', l: 'All Sectors' }].concat(sectors.map(function(s) { return { v: s, l: s }; }))) +
      buildFilterSelect('stage', 'Stage', [{ v: '', l: 'All Stages' }, { v: 'seed-a', l: 'Seed / Series A' }].concat(stages.map(function(s) { return { v: s, l: s }; }))) +
      buildFilterSelect('signal', 'Signal', [{ v: '', l: 'All Signals' }].concat(signals.map(function(s) { return { v: s.toLowerCase(), l: s }; }))) +
      buildFilterSelect('valuation', 'Valuation', [{ v: '', l: 'All Valuations' }].concat(valuations.map(function(v) { return { v: v, l: v }; }))) +
      buildFilterSelect('location', 'Location', [{ v: '', l: 'All Locations' }].concat(locations.map(function(l) { return { v: l, l: l }; }))) +
      '<div class="screener-filter-group"><label>Min Thesis Score</label>' +
      '<input type="number" id="filter-minScore" min="0" max="100" value="70" style="width:100px;"></div>';

    // Bind events
    ['sector', 'stage', 'signal', 'valuation', 'location'].forEach(function(key) {
      var sel = document.getElementById('filter-' + key);
      if (sel) sel.addEventListener('change', function() {
        screenerState[key] = this.value;
        renderScreenerResults();
      });
    });

    var minInput = document.getElementById('filter-minScore');
    if (minInput) minInput.addEventListener('input', function() {
      screenerState.minScore = parseInt(this.value) || 0;
      renderScreenerResults();
    });

    // Set defaults for frontier Seed/A
    var stageSelect = document.getElementById('filter-stage');
    if (stageSelect) stageSelect.value = 'seed-a';
    screenerState.stage = 'seed-a';

    renderScreenerResults();
  }

  function buildFilterSelect(id, label, options) {
    var html = '<div class="screener-filter-group"><label>' + label + '</label><select id="filter-' + id + '">';
    options.forEach(function(o) {
      html += '<option value="' + escapeHTML(o.v) + '">' + escapeHTML(o.l) + '</option>';
    });
    html += '</select></div>';
    return html;
  }

  function renderScreenerResults() {
    var container = document.getElementById('screener-results');
    var countEl = document.getElementById('screener-count');
    if (!container) return;

    var companies = getCompanies();
    var results = [];

    companies.forEach(function(c) {
      var ts = calcThesisScore(c);
      if (ts.total < screenerState.minScore) return;

      // Stage filter
      if (screenerState.stage === 'seed-a') {
        if (!stageIsSeedOrA(c.fundingStage)) return;
      } else if (screenerState.stage) {
        if (normalizeFundingStage(c.fundingStage).toLowerCase() !== screenerState.stage.toLowerCase()) return;
      }

      // Sector filter
      if (screenerState.sector && c.sector !== screenerState.sector) return;

      // Signal filter
      if (screenerState.signal && (!c.signal || c.signal.toLowerCase() !== screenerState.signal)) return;

      // Location filter
      if (screenerState.location) {
        if (screenerState.location === 'International') {
          if (c.location && !c.location.includes(',')) return; // crude check
        } else {
          if (!c.location || !c.location.includes(screenerState.location.substring(0, 4))) {
            // Also check state
            if (!c.state) return;
            var stateMatch = false;
            var locStates = { 'California': 'CA', 'Texas': 'TX', 'New York': 'NY', 'Washington': 'WA', 'Massachusetts': 'MA', 'Colorado': 'CO' };
            if (locStates[screenerState.location] && c.state === locStates[screenerState.location]) {
              stateMatch = true;
            }
            if (!stateMatch) return;
          }
        }
      }

      results.push({ company: c, score: ts });
    });

    // Sort by thesis score desc
    results.sort(function(a, b) { return b.score.total - a.score.total; });

    if (countEl) countEl.textContent = results.length + ' companies match';

    if (results.length === 0) {
      container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">No companies match the current filters. Try broadening your criteria.</div>';
      return;
    }

    var html = '';
    results.slice(0, 60).forEach(function(r) {
      var c = r.company;
      var ts = r.score;
      var sectorColor = getSectorColor(c.sector);
      html += '<div class="screener-card" onclick="window._dfDeepDive(\'' + escapeAttr(c.name) + '\')">' +
        '<div class="screener-card-header">' +
          '<div class="screener-card-name">' + escapeHTML(c.name) + '</div>' +
          '<div class="screener-card-score">' + ts.total + '</div>' +
        '</div>' +
        '<div class="screener-card-meta">' +
          '<span class="screener-badge sector" style="color:' + sectorColor + ';background:' + sectorColor + '1a;">' + escapeHTML(c.sector || '') + '</span>' +
          '<span class="screener-badge">' + escapeHTML(c.fundingStage || 'Unknown') + '</span>' +
          (c.signal ? '<span class="screener-badge" style="color:#f59e0b;">' + escapeHTML(c.signal) + '</span>' : '') +
        '</div>' +
        '<div class="screener-card-row"><span>Valuation</span><span>' + escapeHTML(c.valuation || 'Undisclosed') + '</span></div>' +
        '<div class="screener-card-row"><span>Total Raised</span><span>' + escapeHTML(c.totalRaised || 'Undisclosed') + '</span></div>' +
        '<div class="screener-card-row"><span>Location</span><span>' + escapeHTML(c.location || 'N/A') + '</span></div>' +
      '</div>';
    });

    container.innerHTML = html;
  }

  // ═══════════════════════════════════════════
  // THESIS LEADERBOARD
  // ═══════════════════════════════════════════
  function initThesisLeaderboard() {
    var body = document.getElementById('leaderboard-body');
    var legendEl = document.getElementById('leaderboard-legend');
    if (!body) return;

    var companies = getCompanies();
    var scored = [];
    companies.forEach(function(c) {
      var ts = calcThesisScore(c);
      scored.push({ company: c, score: ts });
    });

    scored.sort(function(a, b) { return b.score.total - a.score.total; });

    var html = '';
    scored.slice(0, 50).forEach(function(item, i) {
      var c = item.company;
      var ts = item.score;
      var rank = i + 1;
      var sectorColor = getSectorColor(c.sector);
      html += '<tr onclick="window._dfDeepDive(\'' + escapeAttr(c.name) + '\')">' +
        '<td class="lb-rank' + (rank <= 3 ? ' top-3' : '') + '">' + rank + '</td>' +
        '<td class="lb-name">' + escapeHTML(c.name) + '</td>' +
        '<td><span class="screener-badge sector" style="color:' + sectorColor + ';background:' + sectorColor + '1a;font-size:11px;">' + escapeHTML(c.sector || '') + '</span></td>' +
        '<td style="font-size:12px;color:var(--text-secondary);">' + escapeHTML(c.fundingStage || '') + '</td>' +
        '<td class="lb-total">' + ts.total + '</td>' +
        '<td class="lb-bar-cell"><div class="lb-bar-stack">' +
          '<div class="lb-bar-seg lb-bar-stage" style="width:' + ts.breakdown.stage + '%;"></div>' +
          '<div class="lb-bar-seg lb-bar-sector" style="width:' + ts.breakdown.sector + '%;"></div>' +
          '<div class="lb-bar-seg lb-bar-innovator" style="width:' + ts.breakdown.innovator + '%;"></div>' +
          '<div class="lb-bar-seg lb-bar-gov" style="width:' + ts.breakdown.gov + '%;"></div>' +
          '<div class="lb-bar-seg lb-bar-founder" style="width:' + ts.breakdown.founder + '%;"></div>' +
          '<div class="lb-bar-seg lb-bar-growth" style="width:' + ts.breakdown.growth + '%;"></div>' +
        '</div></td>' +
      '</tr>';
    });
    body.innerHTML = html;

    // Legend
    if (legendEl) {
      legendEl.innerHTML = THESIS_LEGEND.map(function(l) {
        return '<div class="legend-item"><div class="legend-dot" style="background:' + l.color + ';"></div>' + l.label + '</div>';
      }).join('');
    }
  }

  // ═══════════════════════════════════════════
  // KANBAN BOARD
  // ═══════════════════════════════════════════
  var pipeline = loadPipeline();

  function initKanban() {
    var board = document.getElementById('kanban-board');
    if (!board) return;

    var html = '';
    KANBAN_COLUMNS.forEach(function(col) {
      var items = pipeline[col.id] || [];
      html += '<div class="kanban-column" data-col="' + col.id + '">' +
        '<div class="kanban-column-header">' +
          '<span class="kanban-column-title">' + col.title + '</span>' +
          '<span class="kanban-column-count">' + items.length + '</span>' +
        '</div>' +
        '<div class="kanban-column-body" data-col="' + col.id + '" id="kanban-col-' + col.id + '">';
      items.forEach(function(name) {
        html += buildKanbanCard(name);
      });
      html += '</div></div>';
    });
    board.innerHTML = html;

    initKanbanDragDrop();
    initKanbanAddCompany();
  }

  function buildKanbanCard(companyName) {
    var companies = getCompanies();
    var c = companies.find(function(co) { return co.name === companyName; });
    var ts = c ? calcThesisScore(c) : { total: 0 };
    var sector = c ? c.sector : '';
    var stage = c ? c.fundingStage : '';
    var valuation = c ? c.valuation : '';
    var sectorColor = getSectorColor(sector);

    return '<div class="kanban-card" draggable="true" data-company="' + escapeAttr(companyName) + '">' +
      '<button class="kanban-card-remove" title="Remove from pipeline" onclick="event.stopPropagation();window._dfRemoveFromPipeline(this);">&times;</button>' +
      '<div class="kanban-card-name" onclick="window._dfDeepDive(\'' + escapeAttr(companyName) + '\')">' + escapeHTML(companyName) + '</div>' +
      '<div class="kanban-card-meta">' +
        (sector ? '<span class="kanban-card-badge" style="color:' + sectorColor + ';background:' + sectorColor + '1a;">' + escapeHTML(sector) + '</span>' : '') +
        (stage ? '<span class="kanban-card-badge">' + escapeHTML(stage) + '</span>' : '') +
      '</div>' +
      '<div style="display:flex;justify-content:space-between;align-items:center;">' +
        '<span class="kanban-card-score">Score: ' + ts.total + '</span>' +
        '<span class="kanban-card-valuation">' + escapeHTML(valuation || '') + '</span>' +
      '</div>' +
    '</div>';
  }

  function initKanbanDragDrop() {
    var board = document.getElementById('kanban-board');
    if (!board) return;

    // Drag start
    board.addEventListener('dragstart', function(e) {
      var card = e.target.closest('.kanban-card');
      if (!card) return;
      card.classList.add('dragging');
      e.dataTransfer.setData('text/plain', card.dataset.company);
      e.dataTransfer.effectAllowed = 'move';
    });

    // Drag end
    board.addEventListener('dragend', function(e) {
      var card = e.target.closest('.kanban-card');
      if (card) card.classList.remove('dragging');
      // Remove all drag-over states
      document.querySelectorAll('.kanban-column-body.drag-over').forEach(function(el) {
        el.classList.remove('drag-over');
      });
    });

    // Drag over columns
    var columns = board.querySelectorAll('.kanban-column-body');
    columns.forEach(function(col) {
      col.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        col.classList.add('drag-over');
      });

      col.addEventListener('dragleave', function(e) {
        // Only remove if actually leaving the column
        if (!col.contains(e.relatedTarget)) {
          col.classList.remove('drag-over');
        }
      });

      col.addEventListener('drop', function(e) {
        e.preventDefault();
        col.classList.remove('drag-over');
        var companyName = e.dataTransfer.getData('text/plain');
        var targetCol = col.dataset.col;

        if (!companyName || !targetCol) return;

        // Remove from all columns
        KANBAN_COLUMNS.forEach(function(c) {
          pipeline[c.id] = (pipeline[c.id] || []).filter(function(n) { return n !== companyName; });
        });

        // Add to target
        pipeline[targetCol].push(companyName);
        savePipeline(pipeline);
        initKanban();
        initHeroStats();
      });
    });
  }

  function initKanbanAddCompany() {
    var btn = document.getElementById('kanban-add-btn');
    var dropdown = document.getElementById('add-company-dropdown');
    var searchInput = document.getElementById('add-company-search');
    var listEl = document.getElementById('add-company-list');
    if (!btn || !dropdown) return;

    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      dropdown.classList.toggle('active');
      if (dropdown.classList.contains('active') && searchInput) {
        searchInput.value = '';
        searchInput.focus();
        renderAddCompanyList('');
      }
    });

    document.addEventListener('click', function(e) {
      if (!dropdown.contains(e.target) && e.target !== btn) {
        dropdown.classList.remove('active');
      }
    });

    if (searchInput) {
      searchInput.addEventListener('input', function() {
        renderAddCompanyList(this.value);
      });
    }

    function renderAddCompanyList(query) {
      if (!listEl) return;
      var companies = getCompanies();
      var q = (query || '').toLowerCase();

      // Get all companies already in the pipeline
      var pipelined = new Set();
      KANBAN_COLUMNS.forEach(function(col) {
        (pipeline[col.id] || []).forEach(function(n) { pipelined.add(n); });
      });

      var filtered = companies.filter(function(c) {
        if (pipelined.has(c.name)) return false;
        if (!q) return true;
        return c.name.toLowerCase().includes(q) || (c.sector && c.sector.toLowerCase().includes(q));
      });

      var html = '';
      filtered.slice(0, 30).forEach(function(c) {
        html += '<div class="add-company-item" onclick="window._dfAddToPipeline(\'' + escapeAttr(c.name) + '\')">' +
          '<div><div class="add-company-item-name">' + escapeHTML(c.name) + '</div>' +
          '<div class="add-company-item-sector">' + escapeHTML(c.sector || '') + ' &middot; ' + escapeHTML(c.fundingStage || '') + '</div></div>' +
        '</div>';
      });

      if (filtered.length === 0) {
        html = '<div style="padding:16px;text-align:center;color:var(--text-muted);font-size:13px;">No matching companies</div>';
      }
      listEl.innerHTML = html;
    }
  }

  window._dfAddToPipeline = function(companyName) {
    // Add to "sourced" column
    if (!pipeline.sourced) pipeline.sourced = [];
    if (!pipeline.sourced.includes(companyName)) {
      pipeline.sourced.push(companyName);
      savePipeline(pipeline);
      initKanban();
      initHeroStats();
    }
    var dropdown = document.getElementById('add-company-dropdown');
    if (dropdown) dropdown.classList.remove('active');
  };

  window._dfRemoveFromPipeline = function(btn) {
    var card = btn.closest('.kanban-card');
    if (!card) return;
    var name = card.dataset.company;
    KANBAN_COLUMNS.forEach(function(col) {
      pipeline[col.id] = (pipeline[col.id] || []).filter(function(n) { return n !== name; });
    });
    savePipeline(pipeline);
    initKanban();
    initHeroStats();
  };

  // ═══════════════════════════════════════════
  // DEEP DIVE MODAL
  // ═══════════════════════════════════════════
  function initDeepDive(companyName) {
    var overlay = document.getElementById('dd-overlay');
    var content = document.getElementById('dd-content');
    if (!overlay || !content) return;

    var companies = getCompanies();
    var c = companies.find(function(co) { return co.name === companyName; });
    if (!c) {
      content.innerHTML = '<p style="color:var(--text-muted);">Company not found in database.</p>';
      overlay.classList.add('active');
      return;
    }

    var ts = calcThesisScore(c);
    var innScore = getInnovatorScore(c.name);
    var mosaic = getMosaicScore(c.name);
    var rev = getRevenueIntel(c.name);
    var ipo = getPredictiveIPO(c.name);
    var ma = getPredictiveMA(c.name);
    var failure = getPredictiveFailure(c.name);
    var nextRound = getPredictiveNextRound(c.name);
    var fc = getFounderConnection(c.name);
    var alt = getAltData(c.name);
    var contractor = getContractorReadiness(c.name);
    var notes = loadNotes();
    var userNote = notes[c.name] || { text: '', date: '' };

    var html = '';

    // Header
    html += '<div class="dd-header">' +
      '<div>' +
        '<div class="dd-company-name">' + escapeHTML(c.name) + '</div>' +
        '<div style="display:flex;gap:8px;margin-top:6px;flex-wrap:wrap;">' +
          '<span class="screener-badge sector" style="color:' + getSectorColor(c.sector) + ';background:' + getSectorColor(c.sector) + '1a;">' + escapeHTML(c.sector || '') + '</span>' +
          '<span class="screener-badge">' + escapeHTML(c.fundingStage || '') + '</span>' +
          '<span class="screener-badge">' + escapeHTML(c.location || '') + '</span>' +
        '</div>' +
      '</div>' +
      '<div style="text-align:center;">' +
        '<div class="dd-thesis-total">' + ts.total + '</div>' +
        '<div class="dd-thesis-label">Thesis Score</div>' +
      '</div>' +
    '</div>';

    html += '<div class="dd-grid">';

    // Innovator Score Breakdown (Radar-like)
    html += '<div class="dd-card">' +
      '<div class="dd-card-title">Innovator Score Breakdown</div>';
    if (innScore) {
      var axes = [
        { label: 'Tech Moat', value: innScore.techMoat },
        { label: 'Momentum', value: innScore.momentum },
        { label: 'Team', value: innScore.teamPedigree },
        { label: 'Market', value: innScore.marketGravity },
        { label: 'Capital Eff.', value: innScore.capitalEfficiency },
        { label: 'Gov Traction', value: innScore.govTraction }
      ];
      html += '<div class="dd-radar">';
      axes.forEach(function(ax) {
        html += '<div class="dd-radar-axis">' +
          '<div class="dd-radar-value">' + (ax.value || 0) + '/10</div>' +
          '<div class="dd-radar-bar"><div class="dd-radar-fill" style="width:' + ((ax.value || 0) * 10) + '%;"></div></div>' +
          '<div class="dd-radar-label">' + ax.label + '</div>' +
        '</div>';
      });
      html += '</div>';
      html += '<div style="text-align:center;margin-top:12px;"><span style="font-size:13px;color:var(--text-muted);">Composite:</span> <span style="font-weight:800;color:var(--df-accent);font-size:18px;">' + innScore.composite + '</span></div>';
      if (innScore.tier) {
        html += '<div style="text-align:center;margin-top:4px;"><span class="screener-badge" style="text-transform:uppercase;">' + escapeHTML(innScore.tier) + '</span></div>';
      }
    } else if (mosaic) {
      var mAxes = [
        { label: 'Momentum', value: mosaic.momentum },
        { label: 'Market', value: mosaic.market },
        { label: 'Technology', value: mosaic.technology },
        { label: 'Team', value: mosaic.team }
      ];
      html += '<div class="dd-radar" style="grid-template-columns:repeat(2,1fr);">';
      mAxes.forEach(function(ax) {
        html += '<div class="dd-radar-axis">' +
          '<div class="dd-radar-value">' + (ax.value || 0) + '</div>' +
          '<div class="dd-radar-bar"><div class="dd-radar-fill" style="width:' + (ax.value || 0) + '%;"></div></div>' +
          '<div class="dd-radar-label">' + ax.label + '</div>' +
        '</div>';
      });
      html += '</div>';
      html += '<div style="text-align:center;margin-top:12px;"><span style="font-size:13px;color:var(--text-muted);">Mosaic:</span> <span style="font-weight:800;color:var(--df-accent);font-size:18px;">' + mosaic.total + '/1000</span></div>';
    } else {
      html += '<div style="color:var(--text-muted);font-size:13px;">No innovator score data available.</div>';
    }
    html += '</div>';

    // Thesis Score Breakdown
    html += '<div class="dd-card">' +
      '<div class="dd-card-title">Thesis Score Breakdown</div>';
    var bk = ts.breakdown;
    var scoreRows = [
      { label: 'Stage Fit', value: bk.stage, max: 30, color: '#8b5cf6' },
      { label: 'Sector Fit', value: bk.sector, max: 20, color: '#60a5fa' },
      { label: 'Innovator', value: bk.innovator, max: 20, color: '#22c55e' },
      { label: 'Gov Traction', value: bk.gov, max: 15, color: '#f59e0b' },
      { label: 'Founder', value: bk.founder, max: 10, color: '#ec4899' },
      { label: 'Growth', value: bk.growth, max: 5, color: '#14b8a6' }
    ];
    scoreRows.forEach(function(row) {
      var pct = (row.value / row.max) * 100;
      html += '<div class="dd-score-row">' +
        '<span class="dd-score-label">' + row.label + '</span>' +
        '<div class="dd-score-bar-bg"><div class="dd-score-bar-fill" style="width:' + pct + '%;background:' + row.color + ';"></div></div>' +
        '<span class="dd-score-val">' + row.value + '/' + row.max + '</span>' +
      '</div>';
    });
    html += '</div>';

    // Valuation & Revenue
    html += '<div class="dd-card">' +
      '<div class="dd-card-title">Financials</div>' +
      '<div class="dd-info-row"><span>Valuation</span><span>' + escapeHTML(c.valuation || 'Undisclosed') + '</span></div>' +
      '<div class="dd-info-row"><span>Total Raised</span><span>' + escapeHTML(c.totalRaised || 'Undisclosed') + '</span></div>' +
      '<div class="dd-info-row"><span>Funding Stage</span><span>' + escapeHTML(c.fundingStage || 'N/A') + '</span></div>';
    if (rev) {
      html += '<div class="dd-info-row"><span>Revenue</span><span>' + escapeHTML(rev.revenue) + ' (' + escapeHTML(rev.period) + ')</span></div>' +
        '<div class="dd-info-row"><span>Growth</span><span style="color:' + (rev.growth && rev.growth.includes('+') ? 'var(--df-green)' : 'var(--text-primary)') + ';">' + escapeHTML(rev.growth || 'N/A') + '</span></div>';
    }
    if (alt) {
      html += '<div class="dd-info-row"><span>Hiring</span><span>' + escapeHTML(alt.hiringVelocity || '') + ' (' + escapeHTML(alt.headcountEstimate || '') + ')</span></div>';
    }
    if (contractor) {
      html += '<div class="dd-info-row"><span>Gov Readiness</span><span>' + contractor.readinessScore + '/100</span></div>';
    }
    html += '</div>';

    // Predictive Scores
    html += '<div class="dd-card">' +
      '<div class="dd-card-title">Predictive Scores</div>' +
      '<div class="dd-predictive-grid">';
    if (ipo) {
      html += '<div class="dd-pred-card"><div class="dd-pred-value" style="color:' + predColor(ipo.score) + ';">' + ipo.score + '</div><div class="dd-pred-label">IPO Readiness</div></div>';
    } else {
      html += '<div class="dd-pred-card"><div class="dd-pred-value" style="color:var(--text-muted);">--</div><div class="dd-pred-label">IPO Readiness</div></div>';
    }
    if (ma) {
      html += '<div class="dd-pred-card"><div class="dd-pred-value" style="color:' + predColor(ma.score) + ';">' + ma.score + '</div><div class="dd-pred-label">M&A Target</div></div>';
    } else {
      html += '<div class="dd-pred-card"><div class="dd-pred-value" style="color:var(--text-muted);">--</div><div class="dd-pred-label">M&A Target</div></div>';
    }
    if (failure) {
      html += '<div class="dd-pred-card"><div class="dd-pred-value" style="color:' + riskColor(failure.score) + ';">' + failure.score + '</div><div class="dd-pred-label">Failure Risk</div></div>';
    } else {
      html += '<div class="dd-pred-card"><div class="dd-pred-value" style="color:var(--text-muted);">--</div><div class="dd-pred-label">Failure Risk</div></div>';
    }
    html += '</div>';
    // Next round prediction
    if (nextRound) {
      html += '<div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border);">' +
        '<div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">Next Round Prediction</div>' +
        '<div class="dd-info-row"><span>Timing</span><span>' + escapeHTML(nextRound.predictedTiming) + '</span></div>' +
        '<div class="dd-info-row"><span>Size</span><span>' + escapeHTML(nextRound.predictedSize) + '</span></div>' +
        '<div class="dd-info-row"><span>Valuation</span><span>' + escapeHTML(nextRound.predictedValuation) + '</span></div>' +
        '<div class="dd-info-row"><span>Confidence</span><span>' + nextRound.confidence + '%</span></div>' +
      '</div>';
    }
    html += '</div>';

    html += '</div>'; // close dd-grid

    // Founder Connection
    if (fc) {
      html += '<div class="dd-card" style="margin-bottom:20px;">' +
        '<div class="dd-card-title">Founder Connection</div>';
      if (fc.metFounder) {
        html += '<div style="margin-bottom:8px;"><span class="note-card-founder-badge">Met Founder</span></div>';
      }
      if (fc.exclusiveQuote) {
        html += '<div class="note-quote">"' + escapeHTML(fc.exclusiveQuote) + '"</div>';
      }
      if (fc.tripNotes) {
        html += '<div class="note-trip">' + escapeHTML(fc.tripNotes) + '</div>';
      }
      if (fc.founderInsight) {
        html += '<div class="note-insight">' + escapeHTML(fc.founderInsight) + '</div>';
      }
      if (fc.lastConversation) {
        html += '<div class="note-date">Last conversation: ' + escapeHTML(fc.lastConversation) + '</div>';
      }
      html += '</div>';
    }

    // Personal notes
    html += '<div class="dd-card">' +
      '<div class="dd-card-title">Your Notes</div>' +
      '<textarea class="dd-notes-textarea" id="dd-notes-input" placeholder="Add your notes about ' + escapeAttr(c.name) + '...">' + escapeHTML(userNote.text || '') + '</textarea>' +
      '<div style="display:flex;justify-content:space-between;align-items:center;">' +
        '<button class="dd-notes-save" onclick="window._dfSaveNote(\'' + escapeAttr(c.name) + '\')">Save Note</button>' +
        (userNote.date ? '<span class="note-date">Last saved: ' + escapeHTML(userNote.date) + '</span>' : '') +
      '</div>' +
    '</div>';

    content.innerHTML = html;
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function predColor(score) {
    if (score >= 70) return '#22c55e';
    if (score >= 40) return '#f59e0b';
    return '#ef4444';
  }

  function riskColor(score) {
    if (score <= 20) return '#22c55e';
    if (score <= 50) return '#f59e0b';
    return '#ef4444';
  }

  // Deep dive modal close
  function initDeepDiveModal() {
    var overlay = document.getElementById('dd-overlay');
    var closeBtn = document.getElementById('dd-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function() {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
      });
    }
    if (overlay) {
      overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
          overlay.classList.remove('active');
          document.body.style.overflow = '';
        }
      });
    }
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && overlay && overlay.classList.contains('active')) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  }

  window._dfDeepDive = function(companyName) {
    initDeepDive(companyName);
  };

  window._dfSaveNote = function(companyName) {
    var textarea = document.getElementById('dd-notes-input');
    if (!textarea) return;
    var notes = loadNotes();
    notes[companyName] = {
      text: textarea.value,
      date: new Date().toISOString().split('T')[0]
    };
    saveNotes(notes);
    // Refresh the deep dive to show updated date
    initDeepDive(companyName);
    // Refresh notes section
    safeInit('initPersonalNotes', initPersonalNotes);
  };

  // ═══════════════════════════════════════════
  // UPCOMING ROUNDS
  // ═══════════════════════════════════════════
  function initUpcomingRounds() {
    var grid = document.getElementById('rounds-grid');
    if (!grid) return;

    // Merge DEAL_FLOW_SIGNALS + PREDICTIVE_SCORES.nextRound
    var rounds = {};

    if (typeof DEAL_FLOW_SIGNALS !== 'undefined') {
      DEAL_FLOW_SIGNALS.forEach(function(d) {
        rounds[d.company] = {
          company: d.company,
          probability: d.probability,
          expectedRound: d.expectedRound,
          expectedAmount: d.expectedAmount,
          expectedTiming: d.expectedTiming,
          signals: d.signals || [],
          potentialLeads: d.potentialLeads || [],
          source: 'dealflow'
        };
      });
    }

    if (typeof PREDICTIVE_SCORES !== 'undefined' && PREDICTIVE_SCORES.nextRound && PREDICTIVE_SCORES.nextRound.predictions) {
      var preds = PREDICTIVE_SCORES.nextRound.predictions;
      Object.keys(preds).forEach(function(name) {
        var p = preds[name];
        if (rounds[name]) {
          // Merge data
          if (!rounds[name].predictedValuation) rounds[name].predictedValuation = p.predictedValuation;
          if (!rounds[name].likelyInvestors) rounds[name].likelyInvestors = p.likelyInvestors;
          if (p.confidence > rounds[name].probability) rounds[name].probability = p.confidence;
          rounds[name].catalyst = p.catalyst;
        } else {
          rounds[name] = {
            company: name,
            probability: p.confidence,
            expectedRound: '',
            expectedAmount: p.predictedSize,
            expectedTiming: p.predictedTiming,
            predictedValuation: p.predictedValuation,
            signals: [],
            potentialLeads: p.likelyInvestors || [],
            catalyst: p.catalyst,
            source: 'predictive'
          };
        }
      });
    }

    // Sort by probability desc
    var roundList = Object.values(rounds);
    roundList.sort(function(a, b) { return b.probability - a.probability; });

    var html = '';
    roundList.forEach(function(r) {
      var probClass = r.probability >= 75 ? 'high' : (r.probability >= 50 ? 'medium' : 'low');
      html += '<div class="round-card" onclick="window._dfDeepDive(\'' + escapeAttr(r.company) + '\')">' +
        '<div class="round-card-header">' +
          '<div class="round-card-name">' + escapeHTML(r.company) + '</div>' +
          '<div class="round-card-prob ' + probClass + '">' + r.probability + '%</div>' +
        '</div>' +
        (r.expectedRound ? '<div class="round-info"><strong>' + escapeHTML(r.expectedRound) + '</strong></div>' : '') +
        '<div class="round-info">Amount: <strong>' + escapeHTML(r.expectedAmount || 'TBD') + '</strong></div>' +
        '<div class="round-info">Timing: <strong>' + escapeHTML(r.expectedTiming || 'TBD') + '</strong></div>' +
        (r.predictedValuation ? '<div class="round-info">Expected Val: <strong>' + escapeHTML(r.predictedValuation) + '</strong></div>' : '') +
        (r.catalyst ? '<div class="round-info" style="color:var(--df-accent);font-size:12px;margin-top:4px;">Catalyst: ' + escapeHTML(r.catalyst) + '</div>' : '');

      if (r.signals && r.signals.length > 0) {
        html += '<div class="round-signals">';
        r.signals.forEach(function(s) {
          html += '<div class="round-signal-item"><div class="round-signal-dot"></div>' + escapeHTML(s.description) + '</div>';
        });
        html += '</div>';
      }

      if (r.potentialLeads && r.potentialLeads.length > 0) {
        html += '<div class="round-leads">';
        r.potentialLeads.forEach(function(l) {
          html += '<span class="round-lead-tag">' + escapeHTML(l) + '</span>';
        });
        html += '</div>';
      }

      html += '</div>';
    });

    grid.innerHTML = html;
  }

  // ═══════════════════════════════════════════
  // RISK DASHBOARD
  // ═══════════════════════════════════════════
  function initRiskDashboard() {
    var grid = document.getElementById('risk-grid');
    if (!grid) return;

    if (typeof PREDICTIVE_SCORES === 'undefined' || !PREDICTIVE_SCORES.failureRisk || !PREDICTIVE_SCORES.failureRisk.companies) {
      grid.innerHTML = '<div style="color:var(--text-muted);padding:20px;">No failure risk data available.</div>';
      return;
    }

    var companies = PREDICTIVE_SCORES.failureRisk.companies;
    var entries = Object.keys(companies).map(function(name) {
      return { name: name, data: companies[name] };
    });

    // Sort: highest risk first
    entries.sort(function(a, b) { return b.data.score - a.data.score; });

    var html = '';
    entries.forEach(function(entry) {
      var d = entry.data;
      var riskClass, barColor;
      if (d.score <= 20) {
        riskClass = 'low';
        barColor = '#22c55e';
      } else if (d.score <= 50) {
        riskClass = 'medium';
        barColor = '#f59e0b';
      } else {
        riskClass = 'high';
        barColor = '#ef4444';
      }

      html += '<div class="risk-card" onclick="window._dfDeepDive(\'' + escapeAttr(entry.name) + '\')">' +
        '<div class="risk-card-header">' +
          '<div class="risk-card-name">' + escapeHTML(entry.name) + '</div>' +
          '<div class="risk-score ' + riskClass + '">' + d.score + '</div>' +
        '</div>' +
        '<div class="risk-bar-bg"><div class="risk-bar-fill" style="width:' + d.score + '%;background:' + barColor + ';"></div></div>' +
        '<div class="risk-analysis">' + escapeHTML(d.analysis || '') + '</div>' +
        (d.runway ? '<div class="risk-runway">Runway: <strong>' + escapeHTML(d.runway) + '</strong></div>' : '') +
        (d.trend ? '<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Trend: ' + escapeHTML(d.trend) + '</div>' : '') +
      '</div>';
    });

    grid.innerHTML = html;
  }

  // ═══════════════════════════════════════════
  // PERSONAL NOTES & CONNECTIONS
  // ═══════════════════════════════════════════
  function initPersonalNotes() {
    var grid = document.getElementById('notes-grid');
    var selectEl = document.getElementById('note-company-select');
    if (!grid) return;

    var notes = loadNotes();
    var html = '';

    // Founder connections first
    if (typeof FOUNDER_CONNECTIONS !== 'undefined') {
      Object.keys(FOUNDER_CONNECTIONS).forEach(function(name) {
        var fc = FOUNDER_CONNECTIONS[name];
        var userNote = notes[name] || null;

        html += '<div class="note-card">' +
          '<div class="note-card-header">' +
            '<div class="note-card-company">' + escapeHTML(name) + '</div>' +
            (fc.metFounder ? '<span class="note-card-founder-badge">Met Founder</span>' : '') +
          '</div>';

        if (fc.exclusiveQuote) {
          html += '<div class="note-quote">"' + escapeHTML(fc.exclusiveQuote) + '"</div>';
        }
        if (fc.tripNotes) {
          html += '<div class="note-trip">' + escapeHTML(fc.tripNotes) + '</div>';
        }
        if (fc.founderInsight) {
          html += '<div class="note-insight">' + escapeHTML(fc.founderInsight) + '</div>';
        }
        if (fc.lastConversation) {
          html += '<div class="note-date">Last conversation: ' + escapeHTML(fc.lastConversation) + '</div>';
        }

        // User notes
        if (userNote && userNote.text) {
          html += '<div class="note-custom">' +
            '<div class="note-custom-header"><span class="note-custom-title">Your Notes</span>' +
            '<button class="note-edit-btn" onclick="window._dfDeepDive(\'' + escapeAttr(name) + '\')">Edit</button></div>' +
            '<div style="font-size:13px;color:var(--text-secondary);white-space:pre-wrap;">' + escapeHTML(userNote.text) + '</div>' +
            '<div class="note-date">Saved: ' + escapeHTML(userNote.date) + '</div>' +
          '</div>';
        }

        html += '</div>';
      });
    }

    // Additional user notes for companies not in FOUNDER_CONNECTIONS
    var fcNames = typeof FOUNDER_CONNECTIONS !== 'undefined' ? Object.keys(FOUNDER_CONNECTIONS) : [];
    Object.keys(notes).forEach(function(name) {
      if (fcNames.includes(name)) return;
      if (!notes[name].text) return;

      html += '<div class="note-card">' +
        '<div class="note-card-header">' +
          '<div class="note-card-company">' + escapeHTML(name) + '</div>' +
        '</div>' +
        '<div class="note-custom">' +
          '<div class="note-custom-header"><span class="note-custom-title">Your Notes</span>' +
          '<button class="note-edit-btn" onclick="window._dfDeepDive(\'' + escapeAttr(name) + '\')">Edit</button></div>' +
          '<div style="font-size:13px;color:var(--text-secondary);white-space:pre-wrap;">' + escapeHTML(notes[name].text) + '</div>' +
          '<div class="note-date">Saved: ' + escapeHTML(notes[name].date) + '</div>' +
        '</div>' +
      '</div>';
    });

    if (!html) {
      html = '<div style="color:var(--text-muted);padding:20px;text-align:center;">No founder connections or notes yet. Add companies to your pipeline and start taking notes.</div>';
    }

    grid.innerHTML = html;

    // Populate company select
    if (selectEl) {
      var companies = getCompanies();
      var optHtml = '<option value="">Select company...</option>';
      companies.forEach(function(c) {
        optHtml += '<option value="' + escapeAttr(c.name) + '">' + escapeHTML(c.name) + '</option>';
      });
      selectEl.innerHTML = optHtml;
    }

    // Save note button
    var saveBtn = document.getElementById('note-save-btn');
    if (saveBtn) {
      saveBtn.onclick = function() {
        var sel = document.getElementById('note-company-select');
        var txt = document.getElementById('note-text-input');
        if (!sel || !txt || !sel.value || !txt.value.trim()) return;
        var allNotes = loadNotes();
        allNotes[sel.value] = {
          text: txt.value.trim(),
          date: new Date().toISOString().split('T')[0]
        };
        saveNotes(allNotes);
        txt.value = '';
        sel.value = '';
        initPersonalNotes();
      };
    }
  }

  // ═══════════════════════════════════════════
  // HTML ESCAPING
  // ═══════════════════════════════════════════
  function escapeHTML(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function escapeAttr(str) {
    if (!str) return '';
    return String(str)
      .replace(/\\/g, '\\\\')
      .replace(/'/g, "\\'")
      .replace(/"/g, '&quot;');
  }

  // ═══════════════════════════════════════════
  // MASTER INIT
  // ═══════════════════════════════════════════
  function initDealFlow() {
    safeInit('initHeroStats', initHeroStats);
    safeInit('initThesisScreener', initThesisScreener);
    safeInit('initThesisLeaderboard', initThesisLeaderboard);
    safeInit('initKanban', initKanban);
    safeInit('initDeepDiveModal', initDeepDiveModal);
    safeInit('initUpcomingRounds', initUpcomingRounds);
    safeInit('initRiskDashboard', initRiskDashboard);
    safeInit('initPersonalNotes', initPersonalNotes);
  }

  // ═══════════════════════════════════════════
  // BOOTSTRAP
  // ═══════════════════════════════════════════
  document.addEventListener('DOMContentLoaded', function() {
    if (typeof TILAuth !== 'undefined' && TILAuth.onReady) {
      TILAuth.onReady(function() {
        safeInit('initDealFlow', initDealFlow);
      });
    } else {
      safeInit('initDealFlow', initDealFlow);
    }
  });

})();
