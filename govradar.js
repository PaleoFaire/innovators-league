// ─── GOVERNMENT DEMAND RADAR ───

// ─── HELPERS ───

function formatCurrency(num) {
  if (typeof num === 'string') {
    // Already formatted strings like "$50M-$100M" or "~$3.4B"
    return num;
  }
  if (!num || isNaN(num)) return '$0';
  if (num >= 1e12) return '$' + (num / 1e12).toFixed(1) + 'T';
  if (num >= 1e9) return '$' + (num / 1e9).toFixed(1) + 'B';
  if (num >= 1e6) return '$' + (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return '$' + (num / 1e3).toFixed(0) + 'K';
  return '$' + num.toLocaleString();
}

function parseValueToNumber(valStr) {
  if (!valStr || typeof valStr !== 'string') return 0;
  // Handle ranges like "$50M-$100M" — take the midpoint
  const rangeMatch = valStr.match(/\$([\d.]+)\s*(B|M|K)?\s*-\s*\$([\d.]+)\s*(B|M|K)?/i);
  if (rangeMatch) {
    const lo = parseUnit(parseFloat(rangeMatch[1]), rangeMatch[2]);
    const hi = parseUnit(parseFloat(rangeMatch[3]), rangeMatch[4]);
    return (lo + hi) / 2;
  }
  // Handle single values like "$25M", "~$3.4B", "$3M Phase II"
  const singleMatch = valStr.match(/\$([\d.]+)\s*(B|M|K|T)?/i);
  if (singleMatch) {
    return parseUnit(parseFloat(singleMatch[1]), singleMatch[2]);
  }
  return 0;
}

function parseUnit(val, unit) {
  if (!unit) return val;
  switch (unit.toUpperCase()) {
    case 'T': return val * 1e12;
    case 'B': return val * 1e9;
    case 'M': return val * 1e6;
    case 'K': return val * 1e3;
    default: return val;
  }
}

function daysUntil(dateStr) {
  if (!dateStr) return Infinity;
  const target = new Date(dateStr + 'T00:00:00');
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return Math.ceil((target - now) / (1000 * 60 * 60 * 24));
}

function deadlineClass(days) {
  if (days < 0) return 'deadline-passed';
  if (days < 30) return 'deadline-urgent';
  if (days <= 90) return 'deadline-soon';
  return 'deadline-normal';
}

function deadlineText(days) {
  if (days < 0) return 'Closed';
  if (days === 0) return 'Today';
  if (days === 1) return '1 day';
  return days + ' days';
}

function priorityColor(priority) {
  if (!priority) return 'priority-low';
  switch (priority.toLowerCase()) {
    case 'critical': return 'priority-critical';
    case 'high': return 'priority-high';
    case 'medium': return 'priority-medium';
    default: return 'priority-low';
  }
}

function oppTypeBadgeClass(type) {
  if (!type) return 'opp-type-default';
  const t = type.toLowerCase();
  if (t.includes('other transaction') || t.includes('ot')) return 'opp-type-ot';
  if (t.includes('sbir') || t.includes('sttr')) return 'opp-type-sbir';
  if (t.includes('baa') || t.includes('broad agency')) return 'opp-type-baa';
  if (t.includes('rfi') || t.includes('request for information')) return 'opp-type-rfi';
  return 'opp-type-default';
}

function fedregTypeBadgeClass(type) {
  if (!type) return 'fedreg-type-notice';
  const t = type.toLowerCase();
  if (t === 'rule') return 'fedreg-type-rule';
  if (t.includes('proposed')) return 'fedreg-type-proposed';
  return 'fedreg-type-notice';
}

function readinessBarColor(score) {
  if (score >= 90) return '#22c55e';
  if (score >= 75) return '#3b82f6';
  if (score >= 60) return '#f59e0b';
  return '#ef4444';
}

function animateCounter(id, target) {
  var el = document.getElementById(id);
  if (!el) return;
  var current = 0;
  var duration = 1200;
  var step = target / (duration / 16);
  function tick() {
    current += step;
    if (current >= target) { el.textContent = target; return; }
    el.textContent = Math.floor(current);
    requestAnimationFrame(tick);
  }
  var observer = new IntersectionObserver(function(entries) {
    if (entries[0].isIntersecting) { tick(); observer.disconnect(); }
  });
  observer.observe(el);
}

function animateCounterWithPrefix(id, target, prefix, suffix) {
  var el = document.getElementById(id);
  if (!el) return;
  var current = 0;
  var duration = 1200;
  var step = target / (duration / 16);
  function tick() {
    current += step;
    if (current >= target) { el.textContent = prefix + target + suffix; return; }
    el.textContent = prefix + Math.floor(current) + suffix;
    requestAnimationFrame(tick);
  }
  var observer = new IntersectionObserver(function(entries) {
    if (entries[0].isIntersecting) { tick(); observer.disconnect(); }
  });
  observer.observe(el);
}

// Truncate text
function truncate(str, len) {
  if (!str) return '';
  return str.length > len ? str.slice(0, len) + '...' : str;
}

// ─── SAFE INIT ───

function safeInit(name, fn) {
  try {
    fn();
  } catch (e) {
    console.error('[GovRadar] ' + name + ' failed:', e);
  }
}

// ─── MERGED DATA HELPER ───

function getAllDemandSignals() {
  var curated = (typeof GOV_DEMAND_TRACKER !== 'undefined') ? GOV_DEMAND_TRACKER : [];
  var auto = (typeof GOV_DEMAND_SIGNALS_AUTO !== 'undefined') ? GOV_DEMAND_SIGNALS_AUTO : [];

  // Merge, with curated taking priority on duplicate IDs
  var seenIds = {};
  var merged = [];
  curated.forEach(function(s) { seenIds[s.id] = true; merged.push(s); });
  auto.forEach(function(s) { if (!seenIds[s.id]) { merged.push(s); } });
  return merged;
}

function getGovPullScores() {
  return (typeof GOV_PULL_SCORES_AUTO !== 'undefined') ? GOV_PULL_SCORES_AUTO : {};
}

// ─── MASTER INIT ───

function initGovRadar() {
  safeInit('heroStats', initHeroStats);
  safeInit('demandHeatmap', initDemandHeatmap);
  safeInit('demandRadar', initDemandRadar);
  safeInit('opportunities', initOpportunities);
  safeInit('valleyOfDeath', initValleyOfDeath);
  safeInit('vodTimeline', initVodTimeline);
  safeInit('vodViewToggle', initVodViewToggle);
  safeInit('liveAwardFeed', initLiveAwardFeed);
  safeInit('contractorReadiness', initContractorReadiness);
  safeInit('clearanceAdvantage', initClearanceAdvantage);
  safeInit('budgetSignals', initBudgetSignals);
  safeInit('fedRegister', initFedRegister);
  safeInit('agencySpending', initAgencySpending);
  safeInit('govFunding', initGovFunding);
  safeInit('companyMatch', initCompanyMatch);
  safeInit('congressIntel', initCongressIntel);
  safeInit('sbirTracker', initSbirTracker);
  safeInit('mobileMenu', initGovMobileMenu);
  safeInit('sectionObserver', initSectionObserver);
}

// ─── DOMContentLoaded + Auth ───

document.addEventListener('DOMContentLoaded', function() {
  if (typeof TILAuth !== 'undefined' && TILAuth.onReady) {
    TILAuth.onReady(initGovRadar);
  } else {
    initGovRadar();
  }
});

// ─── 1. HERO STATS ───

function initHeroStats() {
  var tracker = getAllDemandSignals();
  var arpaE = (typeof ARPA_E_PROJECTS_AUTO !== 'undefined') ? ARPA_E_PROJECTS_AUTO : [];
  var nih = (typeof NIH_GRANTS_AUTO !== 'undefined') ? NIH_GRANTS_AUTO : [];
  var sbir = (typeof SBIR_AWARDS_AUTO !== 'undefined') ? SBIR_AWARDS_AUTO : [];
  var contracts = (typeof GOV_CONTRACTS_AUTO !== 'undefined') ? GOV_CONTRACTS_AUTO : [];

  // Count opportunities — demand signals + R&D awards
  var oppCount = tracker.length + arpaE.length + nih.length + sbir.length;
  animateCounter('gov-opp-count', oppCount);

  // Pipeline value — demand signals + ARPA-E + NIH + USAspending
  var totalVal = 0;
  tracker.forEach(function(opp) { totalVal += parseValueToNumber(opp.value); });
  arpaE.forEach(function(p) { totalVal += (p.totalFunding || p.award || 0); });
  nih.forEach(function(g) { totalVal += (g.totalCost || g.awardAmount || 0); });
  contracts.forEach(function(c) { totalVal += parseValueToNumber(c.totalGovValue); });

  var pipelineEl = document.getElementById('gov-pipeline-value');
  if (pipelineEl) {
    if (totalVal >= 1e9) {
      animateCounterWithPrefix('gov-pipeline-value', Math.round(totalVal / 1e9 * 10) / 10, '$', 'B+');
    } else if (totalVal >= 1e6) {
      animateCounterWithPrefix('gov-pipeline-value', Math.round(totalVal / 1e6), '$', 'M+');
    } else {
      pipelineEl.textContent = formatCurrency(totalVal);
    }
  }

  // Unique agencies — include federal R&D sources
  var agencies = new Set();
  tracker.forEach(function(opp) { if (opp.agency) agencies.add(opp.agency); });
  if (arpaE.length > 0) agencies.add('ARPA-E');
  if (nih.length > 0) agencies.add('NIH');
  if (sbir.length > 0) agencies.add('SBIR/STTR');
  animateCounter('gov-agencies', agencies.size);
}

// ─── 2. DEMAND HEATMAP ───

function initDemandHeatmap() {
  var tracker = getAllDemandSignals();
  var container = document.getElementById('heatmap-container');
  if (!container || tracker.length === 0) return;

  // Extract unique tech areas and agencies
  var techSet = new Set();
  var agencySet = new Set();
  tracker.forEach(function(opp) {
    if (opp.techAreas) opp.techAreas.forEach(function(t) { techSet.add(t); });
    if (opp.agency) agencySet.add(opp.agency);
  });

  var techAreas = Array.from(techSet).sort();
  var agencies = Array.from(agencySet).sort();

  if (techAreas.length === 0 || agencies.length === 0) return;

  // Build count matrix
  var matrix = {};
  var maxCount = 0;
  techAreas.forEach(function(tech) {
    matrix[tech] = {};
    agencies.forEach(function(ag) {
      matrix[tech][ag] = 0;
    });
  });

  tracker.forEach(function(opp) {
    var ag = opp.agency;
    if (!ag || !opp.techAreas) return;
    opp.techAreas.forEach(function(tech) {
      if (matrix[tech] && matrix[tech][ag] !== undefined) {
        matrix[tech][ag]++;
        if (matrix[tech][ag] > maxCount) maxCount = matrix[tech][ag];
      }
    });
  });

  // Build grid
  var cols = agencies.length + 1; // +1 for row labels
  var html = '<div class="heatmap-grid" style="grid-template-columns: 140px repeat(' + agencies.length + ', 1fr);">';

  // Header row
  html += '<div class="heatmap-header"></div>'; // top-left blank
  agencies.forEach(function(ag) {
    // Shorten agency names for display
    var short = ag.replace(/\(.*?\)/g, '').trim();
    if (short.length > 18) short = short.slice(0, 16) + '...';
    html += '<div class="heatmap-header" title="' + escapeHtml(ag) + '">' + escapeHtml(short) + '</div>';
  });

  // Data rows
  techAreas.forEach(function(tech) {
    html += '<div class="heatmap-row-label" title="' + escapeHtml(tech) + '">' + escapeHtml(tech) + '</div>';
    agencies.forEach(function(ag) {
      var count = matrix[tech][ag];
      var intensity = maxCount > 0 ? count / maxCount : 0;
      var bg, textColor;
      if (count === 0) {
        bg = 'rgba(255,255,255,0.02)';
        textColor = 'rgba(255,255,255,0.1)';
      } else {
        var alpha = 0.15 + intensity * 0.7;
        bg = 'rgba(59,130,246,' + alpha.toFixed(2) + ')';
        textColor = intensity > 0.5 ? '#fff' : 'rgba(255,255,255,0.8)';
      }
      html += '<div class="heatmap-cell" style="background:' + bg + ';color:' + textColor + ';" title="' + escapeHtml(tech) + ' + ' + escapeHtml(ag) + ': ' + count + ' opportunities">' + (count > 0 ? count : '') + '</div>';
    });
  });

  html += '</div>';

  // Legend
  html += '<div class="heatmap-legend">';
  html += '<span>Intensity:</span>';
  html += '<span class="heatmap-legend-swatch" style="background:rgba(59,130,246,0.15);"></span><span>Low</span>';
  html += '<span class="heatmap-legend-swatch" style="background:rgba(59,130,246,0.45);"></span><span>Medium</span>';
  html += '<span class="heatmap-legend-swatch" style="background:rgba(59,130,246,0.85);"></span><span>High</span>';
  html += '</div>';

  container.innerHTML = html;
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ─── 3. OPPORTUNITIES BOARD ───

function initOpportunities() {
  var tracker = getAllDemandSignals();
  var filtersEl = document.getElementById('opp-filters');
  var gridEl = document.getElementById('opp-grid');
  if (!gridEl) return;

  if (tracker.length === 0) {
    gridEl.innerHTML = '<div class="empty-state">No opportunities data available.</div>';
    return;
  }

  // Extract filter options
  var agencySet = new Set();
  var techSet = new Set();
  var prioritySet = new Set();
  tracker.forEach(function(opp) {
    if (opp.agency) agencySet.add(opp.agency);
    if (opp.techAreas) opp.techAreas.forEach(function(t) { techSet.add(t); });
    if (opp.priority) prioritySet.add(opp.priority);
  });

  // Build filter dropdowns
  if (filtersEl) {
    var fhtml = '';
    fhtml += '<select class="opp-filter-select" id="opp-agency-filter"><option value="all">All Agencies</option>';
    Array.from(agencySet).sort().forEach(function(ag) {
      fhtml += '<option value="' + escapeHtml(ag) + '">' + escapeHtml(ag) + '</option>';
    });
    fhtml += '</select>';

    fhtml += '<select class="opp-filter-select" id="opp-tech-filter"><option value="all">All Tech Areas</option>';
    Array.from(techSet).sort().forEach(function(t) {
      fhtml += '<option value="' + escapeHtml(t) + '">' + escapeHtml(t) + '</option>';
    });
    fhtml += '</select>';

    fhtml += '<select class="opp-filter-select" id="opp-priority-filter"><option value="all">All Priorities</option>';
    ['Critical', 'High', 'Medium', 'Low'].forEach(function(p) {
      if (prioritySet.has(p)) {
        fhtml += '<option value="' + p + '">' + p + '</option>';
      }
    });
    fhtml += '</select>';

    filtersEl.innerHTML = fhtml;

    // Filter listeners
    document.getElementById('opp-agency-filter').addEventListener('change', renderOpportunities);
    document.getElementById('opp-tech-filter').addEventListener('change', renderOpportunities);
    document.getElementById('opp-priority-filter').addEventListener('change', renderOpportunities);
  }

  renderOpportunities();

  function renderOpportunities() {
    var agencyVal = document.getElementById('opp-agency-filter') ? document.getElementById('opp-agency-filter').value : 'all';
    var techVal = document.getElementById('opp-tech-filter') ? document.getElementById('opp-tech-filter').value : 'all';
    var priorityVal = document.getElementById('opp-priority-filter') ? document.getElementById('opp-priority-filter').value : 'all';

    var filtered = tracker.filter(function(opp) {
      if (agencyVal !== 'all' && opp.agency !== agencyVal) return false;
      if (techVal !== 'all' && (!opp.techAreas || opp.techAreas.indexOf(techVal) === -1)) return false;
      if (priorityVal !== 'all' && opp.priority !== priorityVal) return false;
      return true;
    });

    // Sort by deadline (soonest first), put null deadlines at end
    filtered.sort(function(a, b) {
      var da = daysUntil(a.deadline);
      var db = daysUntil(b.deadline);
      return da - db;
    });

    if (filtered.length === 0) {
      gridEl.innerHTML = '<div class="empty-state">No opportunities match the selected filters.</div>';
      return;
    }

    var html = '';
    filtered.forEach(function(opp) {
      var days = daysUntil(opp.deadline);
      var dlClass = deadlineClass(days);
      var dlText = deadlineText(days);
      var typeBadge = oppTypeBadgeClass(opp.type);
      var priClass = priorityColor(opp.priority);

      html += '<div class="opp-card">';
      html += '<div class="opp-card-header">';
      html += '<div>';
      html += '<div style="display:flex;gap:0.4rem;align-items:center;margin-bottom:0.4rem;flex-wrap:wrap;">';
      html += '<span class="opp-type-badge ' + typeBadge + '">' + escapeHtml(opp.type || 'Opportunity') + '</span>';
      html += '<span class="opp-priority-badge ' + priClass + '">' + escapeHtml(opp.priority || '') + '</span>';
      html += '</div>';
      html += '<div class="opp-title">' + escapeHtml(opp.title) + '</div>';
      html += '<div class="opp-agency">' + escapeHtml(opp.agency || '') + '</div>';
      html += '</div>';
      html += '</div>';
      if (opp.description) {
        html += '<div class="opp-desc">' + escapeHtml(opp.description) + '</div>';
      }
      html += '<div class="opp-meta">';
      if (opp.value) {
        html += '<span class="opp-value">' + escapeHtml(opp.value) + '</span>';
      }
      if (opp.deadline) {
        html += '<span class="opp-deadline ' + dlClass + '">' + dlText + '</span>';
      }
      html += '</div>';
      if (opp.techAreas && opp.techAreas.length > 0) {
        html += '<div class="opp-tags">';
        opp.techAreas.forEach(function(t) {
          html += '<span class="opp-tag">' + escapeHtml(t) + '</span>';
        });
        html += '</div>';
      }
      if (opp.relevantCompanies && opp.relevantCompanies.length > 0) {
        html += '<div class="opp-tags">';
        opp.relevantCompanies.forEach(function(c) {
          html += '<span class="opp-tag company-tag">' + escapeHtml(c) + '</span>';
        });
        html += '</div>';
      }
      html += '</div>';
    });

    gridEl.innerHTML = html;
  }
}

// ─── 4. CONTRACTOR READINESS ───

function initContractorReadiness() {
  var data = (typeof CONTRACTOR_READINESS !== 'undefined') ? CONTRACTOR_READINESS : [];
  var gridEl = document.getElementById('readiness-grid');
  if (!gridEl) return;

  if (data.length === 0) {
    gridEl.innerHTML = '<div class="empty-state">No contractor readiness data available.</div>';
    return;
  }

  // Sort by readiness score descending
  var sorted = data.slice().sort(function(a, b) { return (b.readinessScore || 0) - (a.readinessScore || 0); });

  var html = '';
  sorted.forEach(function(c) {
    var score = c.readinessScore || 0;
    var barColor = readinessBarColor(score);
    var scoreColor = barColor;

    html += '<div class="readiness-card">';
    html += '<div class="readiness-header">';
    html += '<span class="readiness-company">' + escapeHtml(c.company) + '</span>';
    html += '<span class="readiness-score-badge" style="color:' + scoreColor + ';">' + score + '</span>';
    html += '</div>';
    html += '<div class="readiness-bar-track"><div class="readiness-bar-fill" style="width:' + score + '%;background:' + barColor + ';"></div></div>';
    html += '<div class="readiness-meta">';
    html += '<div class="readiness-meta-item"><span class="readiness-meta-label">Clearance</span><span class="readiness-meta-value">' + escapeHtml(c.clearanceLevel || 'N/A') + '</span></div>';
    html += '<div class="readiness-meta-item"><span class="readiness-meta-label">TRL Level</span><span class="readiness-meta-value">' + (c.trlLevel || 'N/A') + '</span></div>';
    html += '<div class="readiness-meta-item"><span class="readiness-meta-label">CMMC Level</span><span class="readiness-meta-value">' + (c.cmmcLevel || 'N/A') + '</span></div>';
    html += '<div class="readiness-meta-item"><span class="readiness-meta-label">SBIR Phase</span><span class="readiness-meta-value">' + escapeHtml(c.sbirPhase || 'N/A') + '</span></div>';
    if (c.pastPerformance) {
      html += '<div class="readiness-meta-item"><span class="readiness-meta-label">Contracts Done</span><span class="readiness-meta-value">' + (c.pastPerformance.contractsCompleted || 0) + '</span></div>';
      html += '<div class="readiness-meta-item"><span class="readiness-meta-label">On-Time Rate</span><span class="readiness-meta-value">' + (c.pastPerformance.onTimeRate || 0) + '%</span></div>';
    }
    html += '</div>';
    if (c.readinessFactors && c.readinessFactors.length > 0) {
      html += '<div class="readiness-factors">';
      c.readinessFactors.forEach(function(f) {
        html += '<span class="readiness-factor">' + escapeHtml(f) + '</span>';
      });
      html += '</div>';
    }
    if (c.keyAgencies && c.keyAgencies.length > 0) {
      html += '<div class="readiness-factors" style="margin-top:0.4rem;">';
      c.keyAgencies.forEach(function(a) {
        html += '<span class="readiness-factor" style="background:rgba(59,130,246,0.1);color:rgba(59,130,246,0.8);">' + escapeHtml(a) + '</span>';
      });
      html += '</div>';
    }
    html += '</div>';
  });

  gridEl.innerHTML = html;
}

// ─── CLEARANCE ADVANTAGE DASHBOARD ───

function initClearanceAdvantage() {
  var readinessData = (typeof CONTRACTOR_READINESS !== 'undefined') ? CONTRACTOR_READINESS : [];
  var demandData = (typeof GOV_DEMAND_TRACKER !== 'undefined') ? GOV_DEMAND_TRACKER : [];
  var companies = (typeof COMPANIES !== 'undefined') ? COMPANIES : [];

  var statsEl = document.getElementById('clearance-stats');
  var breakdownEl = document.getElementById('clearance-breakdown');
  var gridEl = document.getElementById('clearance-advantage-grid');
  if (!gridEl) return;

  // Build clearance profiles from CONTRACTOR_READINESS + COMPANIES
  var clearanceProfiles = {};

  readinessData.forEach(function(c) {
    clearanceProfiles[c.company] = {
      company: c.company,
      clearanceLevel: c.clearanceLevel || 'None',
      facilityCleared: c.facilityCleared || false,
      cmmcLevel: c.cmmcLevel || 0,
      itarCompliant: c.itarCompliant || false,
      readinessScore: c.readinessScore || 0,
      keyAgencies: c.keyAgencies || [],
      sbirPhase: c.sbirPhase || 'N/A',
      pastPerformance: c.pastPerformance || {}
    };
  });

  // Also pull in companies with gov contracts from COMPANIES array
  companies.forEach(function(co) {
    if (!clearanceProfiles[co.name] && co.govContracts && co.govContracts.length > 0) {
      clearanceProfiles[co.name] = {
        company: co.name,
        clearanceLevel: 'Unknown',
        facilityCleared: false,
        cmmcLevel: 0,
        itarCompliant: false,
        readinessScore: 0,
        keyAgencies: [],
        sbirPhase: 'N/A',
        pastPerformance: {},
        hasGovContracts: true,
        sector: co.sector
      };
    }
  });

  var profiles = Object.values(clearanceProfiles);

  // Calculate stats
  var tsSCI = profiles.filter(function(p) { return p.clearanceLevel === 'TS/SCI'; }).length;
  var secret = profiles.filter(function(p) { return p.clearanceLevel === 'Secret'; }).length;
  var facilityCleared = profiles.filter(function(p) { return p.facilityCleared; }).length;
  var cmmcL3 = profiles.filter(function(p) { return p.cmmcLevel >= 3; }).length;
  var cmmcL2 = profiles.filter(function(p) { return p.cmmcLevel === 2; }).length;
  var itarCount = profiles.filter(function(p) { return p.itarCompliant; }).length;

  // Render stats row
  if (statsEl) {
    statsEl.innerHTML = ''
      + '<div class="clearance-stat-card">'
      + '  <div class="clearance-stat-number" style="color:#ef4444;">' + tsSCI + '</div>'
      + '  <div class="clearance-stat-label">TS/SCI Cleared</div>'
      + '  <div class="clearance-stat-sub">Highest clearance level</div>'
      + '</div>'
      + '<div class="clearance-stat-card">'
      + '  <div class="clearance-stat-number" style="color:#f59e0b;">' + secret + '</div>'
      + '  <div class="clearance-stat-label">Secret Cleared</div>'
      + '  <div class="clearance-stat-sub">Mid-level clearance</div>'
      + '</div>'
      + '<div class="clearance-stat-card">'
      + '  <div class="clearance-stat-number" style="color:#3b82f6;">' + facilityCleared + '</div>'
      + '  <div class="clearance-stat-label">Facility Clearances</div>'
      + '  <div class="clearance-stat-sub">Cleared workspaces</div>'
      + '</div>'
      + '<div class="clearance-stat-card">'
      + '  <div class="clearance-stat-number" style="color:#22c55e;">' + cmmcL3 + '</div>'
      + '  <div class="clearance-stat-label">CMMC Level 3</div>'
      + '  <div class="clearance-stat-sub">Top-tier cyber maturity</div>'
      + '</div>'
      + '<div class="clearance-stat-card">'
      + '  <div class="clearance-stat-number" style="color:#8b5cf6;">' + itarCount + '</div>'
      + '  <div class="clearance-stat-label">ITAR Compliant</div>'
      + '  <div class="clearance-stat-sub">Export-controlled capable</div>'
      + '</div>';
  }

  // Render clearance tier breakdown
  if (breakdownEl) {
    var clearanceTiers = [
      { level: 'TS/SCI', color: '#ef4444', icon: '🔴', companies: profiles.filter(function(p) { return p.clearanceLevel === 'TS/SCI'; }) },
      { level: 'Secret', color: '#f59e0b', icon: '🟡', companies: profiles.filter(function(p) { return p.clearanceLevel === 'Secret'; }) },
      { level: 'Uncleared / N/A', color: '#6b7280', icon: '⚪', companies: profiles.filter(function(p) { return p.clearanceLevel === 'N/A' || p.clearanceLevel === 'None' || p.clearanceLevel === 'Unknown'; }) }
    ];

    var breakdownHtml = '<div class="clearance-tier-breakdown">';
    clearanceTiers.forEach(function(tier) {
      if (tier.companies.length === 0) return;
      breakdownHtml += '<div class="clearance-tier-row">';
      breakdownHtml += '<div class="clearance-tier-header">';
      breakdownHtml += '<span class="clearance-tier-icon">' + tier.icon + '</span>';
      breakdownHtml += '<span class="clearance-tier-name" style="color:' + tier.color + ';">' + tier.level + '</span>';
      breakdownHtml += '<span class="clearance-tier-count">' + tier.companies.length + ' companies</span>';
      breakdownHtml += '</div>';
      breakdownHtml += '<div class="clearance-tier-companies">';
      tier.companies.sort(function(a, b) { return (b.readinessScore || 0) - (a.readinessScore || 0); });
      tier.companies.forEach(function(c) {
        var badges = [];
        if (c.facilityCleared) badges.push('🏢 Facility Cleared');
        if (c.cmmcLevel >= 2) badges.push('🛡️ CMMC L' + c.cmmcLevel);
        if (c.itarCompliant) badges.push('📋 ITAR');

        breakdownHtml += '<div class="clearance-company-chip" onclick="if(typeof openCompanyModal===\'function\')openCompanyModal(\'' + escapeHtml(c.company) + '\')">';
        breakdownHtml += '<span class="clearance-company-name">' + escapeHtml(c.company) + '</span>';
        if (c.readinessScore > 0) {
          breakdownHtml += '<span class="clearance-company-score" style="color:' + readinessBarColor(c.readinessScore) + ';">' + c.readinessScore + '</span>';
        }
        if (badges.length > 0) {
          breakdownHtml += '<span class="clearance-badges">' + badges.join(' ') + '</span>';
        }
        breakdownHtml += '</div>';
      });
      breakdownHtml += '</div></div>';
    });
    breakdownHtml += '</div>';
    breakdownEl.innerHTML = breakdownHtml;
  }

  // Render advantage match grid — cross-reference cleared companies with active solicitations
  if (gridEl) {
    var advantageHtml = '<h3 class="clearance-advantage-title">Clearance-Matched Opportunities</h3>';
    advantageHtml += '<p class="clearance-advantage-desc">Companies with existing security clearances mapped to solicitations where clearance creates competitive advantage.</p>';

    // Map solicitations to cleared companies
    var matches = [];
    var clearedCompanies = profiles.filter(function(p) { return p.clearanceLevel === 'TS/SCI' || p.clearanceLevel === 'Secret'; });

    // If we have demand tracker data, match on tech areas
    if (demandData.length > 0) {
      demandData.forEach(function(opp) {
        var matchedCompanies = [];
        clearedCompanies.forEach(function(c) {
          // Check if company's agencies overlap or tech areas match
          var agencyMatch = false;
          if (c.keyAgencies && opp.agency) {
            c.keyAgencies.forEach(function(a) {
              if (opp.agency.toLowerCase().indexOf(a.toLowerCase()) !== -1 || a.toLowerCase().indexOf(opp.agency.toLowerCase()) !== -1) {
                agencyMatch = true;
              }
            });
          }
          // Check relevant companies field
          var directMatch = false;
          if (opp.relevantCompanies) {
            opp.relevantCompanies.forEach(function(rc) {
              if (rc.toLowerCase() === c.company.toLowerCase()) directMatch = true;
            });
          }
          if (agencyMatch || directMatch) {
            matchedCompanies.push(c);
          }
        });
        if (matchedCompanies.length > 0) {
          matches.push({ opportunity: opp, companies: matchedCompanies });
        }
      });
    }

    if (matches.length > 0) {
      advantageHtml += '<div class="advantage-matches">';
      matches.slice(0, 8).forEach(function(m) {
        var opp = m.opportunity;
        var priorityColor = opp.priority === 'High' ? '#ef4444' : opp.priority === 'Medium' ? '#f59e0b' : '#22c55e';
        advantageHtml += '<div class="advantage-match-card">';
        advantageHtml += '<div class="advantage-match-header">';
        advantageHtml += '<span class="advantage-opp-agency" style="color:' + priorityColor + ';">' + escapeHtml(opp.agency || '') + '</span>';
        advantageHtml += '<span class="advantage-opp-value">' + escapeHtml(opp.value || '') + '</span>';
        advantageHtml += '</div>';
        advantageHtml += '<div class="advantage-opp-title">' + escapeHtml(opp.title || '') + '</div>';
        if (opp.deadline) {
          advantageHtml += '<div class="advantage-opp-deadline">Deadline: ' + escapeHtml(opp.deadline) + '</div>';
        }
        advantageHtml += '<div class="advantage-matched-companies">';
        advantageHtml += '<span class="advantage-match-label">Cleared Advantage:</span>';
        m.companies.forEach(function(c) {
          advantageHtml += '<span class="advantage-company-tag" style="border-color:' + (c.clearanceLevel === 'TS/SCI' ? '#ef4444' : '#f59e0b') + ';">';
          advantageHtml += escapeHtml(c.company);
          advantageHtml += ' <small>(' + c.clearanceLevel + ')</small>';
          advantageHtml += '</span>';
        });
        advantageHtml += '</div></div>';
      });
      advantageHtml += '</div>';
    } else {
      // Show cleared company capabilities even without solicitation matches
      advantageHtml += '<div class="advantage-capabilities">';
      clearedCompanies.sort(function(a, b) { return (b.readinessScore || 0) - (a.readinessScore || 0); });
      clearedCompanies.forEach(function(c) {
        advantageHtml += '<div class="advantage-capability-card">';
        advantageHtml += '<div class="advantage-cap-header">';
        advantageHtml += '<span class="advantage-cap-company">' + escapeHtml(c.company) + '</span>';
        advantageHtml += '<span class="advantage-cap-clearance" style="background:' + (c.clearanceLevel === 'TS/SCI' ? 'rgba(239,68,68,0.15);color:#ef4444' : 'rgba(245,158,11,0.15);color:#f59e0b') + ';">' + c.clearanceLevel + '</span>';
        advantageHtml += '</div>';
        var caps = [];
        if (c.facilityCleared) caps.push('Facility Cleared');
        if (c.cmmcLevel >= 2) caps.push('CMMC Level ' + c.cmmcLevel);
        if (c.itarCompliant) caps.push('ITAR Compliant');
        if (c.sbirPhase && c.sbirPhase !== 'N/A') caps.push('SBIR ' + c.sbirPhase);
        if (c.keyAgencies && c.keyAgencies.length > 0) caps.push('Agencies: ' + c.keyAgencies.join(', '));
        advantageHtml += '<div class="advantage-cap-details">' + caps.join(' · ') + '</div>';
        if (c.pastPerformance && c.pastPerformance.contractsCompleted > 0) {
          advantageHtml += '<div class="advantage-cap-perf">' + c.pastPerformance.contractsCompleted + ' contracts completed · ' + (c.pastPerformance.onTimeRate || 0) + '% on-time</div>';
        }
        advantageHtml += '</div>';
      });
      advantageHtml += '</div>';
    }

    gridEl.innerHTML = advantageHtml;
  }
}

// ─── 5. BUDGET SIGNALS ───

function initBudgetSignals() {
  var data = (typeof BUDGET_SIGNALS !== 'undefined') ? BUDGET_SIGNALS : [];
  var barsEl = document.getElementById('budget-bars');
  if (!barsEl) return;

  if (data.length === 0) {
    barsEl.innerHTML = '<div class="empty-state">No budget signals data available.</div>';
    return;
  }

  // Find max allocation for bar sizing
  var maxAlloc = 0;
  data.forEach(function(b) {
    var val = parseValueToNumber(b.allocation);
    if (val > maxAlloc) maxAlloc = val;
  });

  // Sort by allocation descending
  var sorted = data.slice().sort(function(a, b) {
    return parseValueToNumber(b.allocation) - parseValueToNumber(a.allocation);
  });

  var barColors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#22c55e', '#06b6d4', '#ef4444', '#14b8a6'];

  var html = '';
  sorted.forEach(function(b, idx) {
    var alloc = parseValueToNumber(b.allocation);
    var barWidth = maxAlloc > 0 ? Math.max((alloc / maxAlloc) * 100, 5) : 5;
    var changeNum = parseFloat((b.change || '0').replace(/[^-\d.]/g, ''));
    var changeClass = changeNum >= 0 ? 'budget-change-positive' : 'budget-change-negative';
    var color = barColors[idx % barColors.length];

    html += '<div class="budget-bar-item">';
    html += '<div class="budget-bar-top">';
    html += '<span class="budget-category">' + escapeHtml(b.category) + '</span>';
    html += '<div style="display:flex;align-items:center;gap:0.5rem;">';
    html += '<span class="budget-amount">' + escapeHtml(b.allocation || '') + '</span>';
    if (b.change) {
      html += '<span class="budget-change-badge ' + changeClass + '">' + escapeHtml(b.change) + '</span>';
    }
    html += '</div>';
    html += '</div>';
    html += '<div class="budget-bar-track"><div class="budget-bar-fill" style="width:' + barWidth.toFixed(1) + '%;background:' + color + ';"></div></div>';
    if (b.description) {
      html += '<div class="budget-bar-desc">' + escapeHtml(b.description) + '</div>';
    }
    if (b.beneficiaries && b.beneficiaries.length > 0) {
      html += '<div class="budget-beneficiaries">';
      b.beneficiaries.forEach(function(name) {
        html += '<span class="budget-beneficiary">' + escapeHtml(name) + '</span>';
      });
      html += '</div>';
    }
    html += '</div>';
  });

  barsEl.innerHTML = html;
}

// ─── 6. FEDERAL REGISTER FEED ───

function initFedRegister() {
  // The variable is FEDERAL_REGISTER (not FEDERAL_REGISTER_LIVE)
  var data = (typeof FEDERAL_REGISTER !== 'undefined') ? FEDERAL_REGISTER : [];
  var gridEl = document.getElementById('fedreg-grid');
  if (!gridEl) return;

  if (data.length === 0) {
    gridEl.innerHTML = '<div class="empty-state">No Federal Register data available.</div>';
    return;
  }

  // Sort by date descending, take latest 20
  var sorted = data.slice().sort(function(a, b) {
    return (b.date || '').localeCompare(a.date || '');
  });
  var latest = sorted.slice(0, 20);

  var html = '';
  latest.forEach(function(entry) {
    var typeClass = fedregTypeBadgeClass(entry.type);

    html += '<div class="fedreg-card">';
    html += '<div class="fedreg-header">';
    html += '<div class="fedreg-title" title="' + escapeHtml(entry.title) + '">' + escapeHtml(entry.title) + '</div>';
    html += '<span class="fedreg-type-badge ' + typeClass + '">' + escapeHtml(entry.type || 'Notice') + '</span>';
    html += '</div>';
    html += '<div class="fedreg-meta">';
    if (entry.date) {
      html += '<span class="fedreg-date">' + escapeHtml(entry.date) + '</span>';
    }
    if (entry.agencies) {
      html += '<span>' + escapeHtml(truncate(entry.agencies, 60)) + '</span>';
    }
    html += '</div>';
    if (entry.sectors && entry.sectors.trim()) {
      html += '<div class="opp-tags" style="margin-top:0.5rem;">';
      entry.sectors.split(',').forEach(function(s) {
        s = s.trim();
        if (s) html += '<span class="opp-tag">' + escapeHtml(s) + '</span>';
      });
      html += '</div>';
    }
    html += '</div>';
  });

  gridEl.innerHTML = html;
}

// ─── 7. AGENCY SPENDING DASHBOARD ───

function initAgencySpending() {
  var contracts = (typeof GOV_CONTRACTS_AUTO !== 'undefined') ? GOV_CONTRACTS_AUTO : [];
  var arpaE = (typeof ARPA_E_PROJECTS_AUTO !== 'undefined') ? ARPA_E_PROJECTS_AUTO : [];
  var nih = (typeof NIH_GRANTS_AUTO !== 'undefined') ? NIH_GRANTS_AUTO : [];
  var gridEl = document.getElementById('agency-grid');
  if (!gridEl) return;

  if (contracts.length === 0 && arpaE.length === 0 && nih.length === 0) {
    gridEl.innerHTML = '<div class="empty-state">No government contracts data available.</div>';
    return;
  }

  // Aggregate by agency
  var agencyMap = {};
  contracts.forEach(function(c) {
    if (!c.agencies) return;
    var val = parseValueToNumber(c.totalGovValue);
    c.agencies.forEach(function(ag) {
      if (!agencyMap[ag]) {
        agencyMap[ag] = { totalValue: 0, totalContracts: 0, companies: new Set() };
      }
      agencyMap[ag].totalValue += val;
      agencyMap[ag].totalContracts += (c.contractCount || 0);
      agencyMap[ag].companies.add(c.company);
    });
  });

  // Add ARPA-E as an agency
  if (arpaE.length > 0) {
    var arpaEKey = 'ARPA-E (Dept. of Energy)';
    if (!agencyMap[arpaEKey]) agencyMap[arpaEKey] = { totalValue: 0, totalContracts: 0, companies: new Set() };
    arpaE.forEach(function(p) {
      agencyMap[arpaEKey].totalValue += (p.totalFunding || p.award || 0);
      agencyMap[arpaEKey].totalContracts++;
      if (p.organization) agencyMap[arpaEKey].companies.add(p.organization);
    });
  }

  // Add NIH as an agency
  if (nih.length > 0) {
    var nihKey = 'NIH (Dept. of Health & Human Services)';
    if (!agencyMap[nihKey]) agencyMap[nihKey] = { totalValue: 0, totalContracts: 0, companies: new Set() };
    nih.forEach(function(g) {
      agencyMap[nihKey].totalValue += (g.totalCost || g.awardAmount || 0);
      agencyMap[nihKey].totalContracts++;
      if (g.organization) agencyMap[nihKey].companies.add(g.organization);
    });
  }

  // Sort by total value descending
  var agencyList = Object.keys(agencyMap).map(function(ag) {
    return {
      name: ag,
      totalValue: agencyMap[ag].totalValue,
      totalContracts: agencyMap[ag].totalContracts,
      companies: Array.from(agencyMap[ag].companies)
    };
  }).sort(function(a, b) { return b.totalValue - a.totalValue; });

  var html = '';
  agencyList.forEach(function(ag) {
    html += '<div class="agency-card">';
    html += '<div class="agency-name">' + escapeHtml(ag.name) + '</div>';
    html += '<div class="agency-stat">';
    html += '<span class="agency-stat-label">Total Contract Value</span>';
    html += '<span class="agency-stat-value">' + formatCurrency(ag.totalValue) + '</span>';
    html += '</div>';
    html += '<div class="agency-stat">';
    html += '<span class="agency-stat-label">Contracts Tracked</span>';
    html += '<span class="agency-stat-value" style="color:rgba(255,255,255,0.8);">' + ag.totalContracts + '</span>';
    html += '</div>';
    if (ag.companies.length > 0) {
      html += '<div class="agency-companies">';
      ag.companies.forEach(function(c) {
        html += '<span class="agency-company-tag">' + escapeHtml(c) + '</span>';
      });
      html += '</div>';
    }
    html += '</div>';
  });

  gridEl.innerHTML = html;
}

// ─── 8. COMPANY ↔ OPPORTUNITY MATCH ───

function initCompanyMatch() {
  var tracker = getAllDemandSignals();
  var pullScores = getGovPullScores();
  var gridEl = document.getElementById('match-grid');
  if (!gridEl) return;

  if (tracker.length === 0) {
    gridEl.innerHTML = '<div class="empty-state">No opportunity matching data available.</div>';
    return;
  }

  // Build reverse index: company -> [opportunities]
  var companyIndex = {};
  tracker.forEach(function(opp) {
    if (!opp.relevantCompanies) return;
    opp.relevantCompanies.forEach(function(co) {
      if (!companyIndex[co]) companyIndex[co] = [];
      companyIndex[co].push(opp);
    });
  });

  // Sort companies by number of matches descending
  var companyList = Object.keys(companyIndex).sort(function(a, b) {
    return companyIndex[b].length - companyIndex[a].length;
  });

  if (companyList.length === 0) {
    gridEl.innerHTML = '<div class="empty-state">No company matches found.</div>';
    return;
  }

  var html = '';
  companyList.forEach(function(co, idx) {
    var opps = companyIndex[co];
    var cardId = 'match-card-' + idx;

    var ps = pullScores[co];
    var pullBadge = '';
    if (ps && ps.govPullScore) {
      var pullClass = ps.govPullScore >= 60 ? 'gov-pull-high' : (ps.govPullScore >= 30 ? 'gov-pull-medium' : 'gov-pull-low');
      pullBadge = '<span class="gov-pull-badge ' + pullClass + '" title="Government Pull Score">' + ps.govPullScore + '</span>';
    }
    html += '<div class="match-card">';
    html += '<div style="display:flex;align-items:center;gap:0.5rem;">' + pullBadge + '<div class="match-company-name">' + escapeHtml(co) + '</div></div>';
    html += '<div class="match-count">' + opps.length + ' matching opportunit' + (opps.length === 1 ? 'y' : 'ies') + (ps ? ' &middot; Pull Score: ' + ps.govPullScore : '') + '</div>';
    html += '<button class="match-toggle" data-target="' + cardId + '" onclick="toggleMatchList(this)">Show Opportunities</button>';
    html += '<div class="match-opp-list" id="' + cardId + '">';
    opps.forEach(function(opp) {
      var days = daysUntil(opp.deadline);
      var dlClass = deadlineClass(days);
      var dlText = opp.deadline ? (deadlineText(days)) : '';
      html += '<div class="match-opp-item">';
      html += '<div class="match-opp-item-title">' + escapeHtml(opp.title) + '</div>';
      html += '<div class="match-opp-item-meta">';
      html += escapeHtml(opp.agency || '');
      if (opp.value) html += ' &middot; ' + escapeHtml(opp.value);
      if (dlText) html += ' &middot; <span class="' + dlClass + '" style="padding:1px 4px;border-radius:3px;font-weight:600;">' + dlText + '</span>';
      html += '</div>';
      html += '</div>';
    });
    html += '</div>';
    html += '</div>';
  });

  gridEl.innerHTML = html;
}

function toggleMatchList(btn) {
  var targetId = btn.getAttribute('data-target');
  var list = document.getElementById(targetId);
  if (!list) return;
  var isExpanded = list.classList.contains('expanded');
  list.classList.toggle('expanded');
  btn.textContent = isExpanded ? 'Show Opportunities' : 'Hide Opportunities';
}

// ─── 9. DEMAND SIGNAL RADAR ───

function initDemandRadar() {
  var signals = getAllDemandSignals();
  var pullScores = getGovPullScores();

  var controlsEl = document.getElementById('radar-controls');
  var statsEl = document.getElementById('radar-stats');
  var gridEl = document.getElementById('radar-grid');
  if (!gridEl) return;

  if (signals.length === 0) {
    gridEl.innerHTML = '<div class="empty-state">No demand signals available.</div>';
    return;
  }

  // Extract filter options
  var agencySet = new Set();
  var typeSet = new Set();
  signals.forEach(function(s) {
    if (s.agency) agencySet.add(s.agency);
    if (s.type) typeSet.add(s.type);
  });

  // Build controls
  if (controlsEl) {
    var chtml = '';
    chtml += '<div class="radar-search-box"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>';
    chtml += '<input type="text" id="radar-search" placeholder="Search signals, companies..."></div>';

    chtml += '<select class="radar-filter-select" id="radar-agency-filter"><option value="all">All Agencies</option>';
    Array.from(agencySet).sort().forEach(function(ag) {
      chtml += '<option value="' + escapeHtml(ag) + '">' + escapeHtml(ag.length > 40 ? ag.slice(0, 38) + '...' : ag) + '</option>';
    });
    chtml += '</select>';

    chtml += '<select class="radar-filter-select" id="radar-confidence-filter">';
    chtml += '<option value="0">All Confidence</option>';
    chtml += '<option value="30">Score &ge; 30</option>';
    chtml += '<option value="50">Score &ge; 50</option>';
    chtml += '<option value="70">Score &ge; 70</option>';
    chtml += '</select>';

    controlsEl.innerHTML = chtml;

    document.getElementById('radar-search').addEventListener('input', renderRadar);
    document.getElementById('radar-agency-filter').addEventListener('change', renderRadar);
    document.getElementById('radar-confidence-filter').addEventListener('change', renderRadar);
  }

  renderRadar();

  function renderRadar() {
    var searchVal = (document.getElementById('radar-search') ? document.getElementById('radar-search').value : '').toLowerCase();
    var agencyVal = document.getElementById('radar-agency-filter') ? document.getElementById('radar-agency-filter').value : 'all';
    var confidenceVal = parseInt(document.getElementById('radar-confidence-filter') ? document.getElementById('radar-confidence-filter').value : '0', 10);

    // Filter signals
    var filtered = signals.filter(function(s) {
      if (agencyVal !== 'all' && s.agency !== agencyVal) return false;

      // If confidence filter is set, only show signals that have at least one match above threshold
      if (confidenceVal > 0) {
        var hasMatch = (s.matchedCompanies || []).some(function(mc) { return mc.score >= confidenceVal; });
        if (!hasMatch && !(s.relevantCompanies && s.relevantCompanies.length > 0 && confidenceVal <= 30)) return false;
      }

      if (searchVal) {
        var searchText = (s.title + ' ' + s.agency + ' ' + s.description + ' ' + (s.relevantCompanies || []).join(' ')).toLowerCase();
        if (searchText.indexOf(searchVal) === -1) return false;
      }

      return true;
    });

    // Sort: Critical first, then by deadline
    var priorityOrder = { 'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3 };
    filtered.sort(function(a, b) {
      var pa = priorityOrder[a.priority] !== undefined ? priorityOrder[a.priority] : 4;
      var pb = priorityOrder[b.priority] !== undefined ? priorityOrder[b.priority] : 4;
      if (pa !== pb) return pa - pb;
      return daysUntil(a.deadline) - daysUntil(b.deadline);
    });

    // Stats
    if (statsEl) {
      var totalMatches = 0;
      var matchedCos = new Set();
      var avgScore = 0;
      var scoreCount = 0;
      filtered.forEach(function(s) {
        var mc = s.matchedCompanies || [];
        totalMatches += mc.length;
        mc.forEach(function(m) {
          matchedCos.add(m.name);
          avgScore += m.score;
          scoreCount++;
        });
        if (mc.length === 0 && s.relevantCompanies) {
          s.relevantCompanies.forEach(function(c) { matchedCos.add(c); });
        }
      });
      var avg = scoreCount > 0 ? Math.round(avgScore / scoreCount) : 0;

      statsEl.innerHTML = '<div class="radar-stat-item"><span class="radar-stat-number">' + filtered.length + '</span><span class="radar-stat-label">Demand Signals</span></div>' +
        '<div class="radar-stat-item"><span class="radar-stat-number">' + matchedCos.size + '</span><span class="radar-stat-label">Companies Matched</span></div>' +
        '<div class="radar-stat-item"><span class="radar-stat-number">' + totalMatches + '</span><span class="radar-stat-label">Total Matches</span></div>' +
        '<div class="radar-stat-item"><span class="radar-stat-number">' + avg + '%</span><span class="radar-stat-label">Avg Relevance</span></div>';
    }

    // Render cards
    if (filtered.length === 0) {
      gridEl.innerHTML = '<div class="empty-state">No demand signals match the selected filters.</div>';
      return;
    }

    var html = '';
    filtered.forEach(function(signal, idx) {
      var days = daysUntil(signal.deadline);
      var dlClass = deadlineClass(days);
      var dlText = deadlineText(days);
      var typeBadge = oppTypeBadgeClass(signal.type);
      var priClass = priorityColor(signal.priority);

      // Source badge
      var sourceApi = signal.sourceApi || 'seed';
      var srcClass = 'radar-source-' + (sourceApi === 'sbir.gov' ? 'sbir' : sourceApi === 'grants.gov' ? 'grants' : sourceApi === 'sam.gov' ? 'sam' : 'seed');
      var srcLabel = sourceApi === 'seed' ? 'Curated' : sourceApi;

      html += '<div class="radar-card">';

      // Header
      html += '<div class="radar-card-header"><div>';
      html += '<div class="radar-card-badges">';
      html += '<span class="opp-type-badge ' + typeBadge + '">' + escapeHtml(signal.type || 'Opportunity') + '</span>';
      html += '<span class="opp-priority-badge ' + priClass + '">' + escapeHtml(signal.priority || '') + '</span>';
      html += '<span class="radar-source-badge ' + srcClass + '">' + escapeHtml(srcLabel) + '</span>';
      html += '</div>';
      html += '<div class="radar-card-title">' + escapeHtml(signal.title) + '</div>';
      html += '<div class="radar-card-agency">' + escapeHtml(signal.agency || '') + '</div>';
      html += '</div></div>';

      // Description
      if (signal.description) {
        html += '<div class="radar-card-desc">' + escapeHtml(signal.description) + '</div>';
      }

      // Meta
      html += '<div class="radar-card-meta">';
      if (signal.value) html += '<span class="radar-card-value">' + escapeHtml(signal.value) + '</span>';
      if (signal.deadline) html += '<span class="opp-deadline ' + dlClass + '">' + dlText + '</span>';
      if (signal.techAreas && signal.techAreas.length > 0) {
        signal.techAreas.slice(0, 5).forEach(function(t) {
          html += '<span class="opp-tag">' + escapeHtml(t) + '</span>';
        });
      }
      html += '</div>';

      // Matched companies
      var mc = signal.matchedCompanies || [];
      var flatCompanies = signal.relevantCompanies || [];

      if (mc.length > 0) {
        html += '<div class="radar-matches-section">';
        html += '<div class="radar-matches-label">Matched Companies (' + mc.length + ')</div>';
        html += '<div class="radar-matches-list">';

        var showCount = Math.min(mc.length, 5);
        for (var i = 0; i < showCount; i++) {
          var m = mc[i];
          var scoreClass = m.score >= 70 ? 'score-high' : (m.score >= 40 ? 'score-medium' : 'score-low');
          var barClass = m.score >= 70 ? 'bar-high' : (m.score >= 40 ? 'bar-medium' : 'bar-low');
          var slug = m.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

          html += '<div class="radar-match-item">';
          html += '<a href="company.html?slug=' + slug + '" class="radar-match-name">' + escapeHtml(m.name) + '</a>';
          html += '<div class="radar-match-bar-track"><div class="radar-match-bar-fill ' + barClass + '" style="width:' + m.score + '%;"></div></div>';
          html += '<span class="radar-match-score ' + scoreClass + '">' + m.score + '%</span>';
          if (m.matchReasons && m.matchReasons.length > 0) {
            html += '<span class="radar-match-reasons">' + escapeHtml(m.matchReasons.slice(0, 2).join(', ')) + '</span>';
          }
          html += '</div>';
        }

        if (mc.length > 5) {
          var moreId = 'radar-more-' + idx;
          html += '<div id="' + moreId + '" style="display:none;">';
          for (var j = 5; j < mc.length; j++) {
            var m2 = mc[j];
            var sc2 = m2.score >= 70 ? 'score-high' : (m2.score >= 40 ? 'score-medium' : 'score-low');
            var bc2 = m2.score >= 70 ? 'bar-high' : (m2.score >= 40 ? 'bar-medium' : 'bar-low');
            var sl2 = m2.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

            html += '<div class="radar-match-item">';
            html += '<a href="company.html?slug=' + sl2 + '" class="radar-match-name">' + escapeHtml(m2.name) + '</a>';
            html += '<div class="radar-match-bar-track"><div class="radar-match-bar-fill ' + bc2 + '" style="width:' + m2.score + '%;"></div></div>';
            html += '<span class="radar-match-score ' + sc2 + '">' + m2.score + '%</span>';
            html += '</div>';
          }
          html += '</div>';
          html += '<button class="radar-show-more" onclick="toggleRadarMore(this, \'' + moreId + '\')">Show ' + (mc.length - 5) + ' more</button>';
        }

        html += '</div></div>';
      } else if (flatCompanies.length > 0) {
        // Fallback for curated signals without matchedCompanies
        html += '<div class="radar-matches-section">';
        html += '<div class="radar-matches-label">Relevant Companies</div>';
        html += '<div class="opp-tags">';
        flatCompanies.forEach(function(c) {
          html += '<span class="opp-tag company-tag">' + escapeHtml(c) + '</span>';
        });
        html += '</div></div>';
      }

      html += '</div>'; // radar-card
    });

    gridEl.innerHTML = html;
  }
}

function toggleRadarMore(btn, moreId) {
  var el = document.getElementById(moreId);
  if (!el) return;
  var hidden = el.style.display === 'none';
  el.style.display = hidden ? 'block' : 'none';
  btn.textContent = hidden ? 'Show less' : btn.textContent.replace('Show less', 'Show more');
}

// ─── 10. GOVERNMENT R&D FUNDING ───

function initGovFunding() {
  var arpaE = (typeof ARPA_E_PROJECTS_AUTO !== 'undefined') ? ARPA_E_PROJECTS_AUTO : [];
  var nih = (typeof NIH_GRANTS_AUTO !== 'undefined') ? NIH_GRANTS_AUTO : [];
  var sbir = (typeof SBIR_AWARDS_AUTO !== 'undefined') ? SBIR_AWARDS_AUTO : [];
  var nasa = (typeof NASA_PROJECTS !== 'undefined') ? NASA_PROJECTS : [];
  var nsf = (typeof NSF_AWARDS !== 'undefined') ? NSF_AWARDS : [];
  var sam = (typeof SAM_CONTRACTS_AUTO !== 'undefined') ? SAM_CONTRACTS_AUTO : [];

  var statsEl = document.getElementById('funding-stats');
  var filtersEl = document.getElementById('funding-filters');
  var gridEl = document.getElementById('funding-grid');
  if (!gridEl) return;

  // Normalize all sources into a common format
  var allFunding = [];

  arpaE.forEach(function(p) {
    allFunding.push({
      source: 'ARPA-E',
      sourceClass: 'source-arpa-e',
      title: p.title || '',
      organization: p.organization || '',
      amount: p.totalFunding || p.award || 0,
      status: p.status || '',
      techArea: p.techArea || p.program || '',
      matchedCompanies: p.matchedCompanies || [],
      state: p.state || ''
    });
  });

  nih.forEach(function(g) {
    allFunding.push({
      source: 'NIH',
      sourceClass: 'source-nih',
      title: g.title || '',
      organization: g.organization || '',
      amount: g.totalCost || g.awardAmount || 0,
      status: g.activity_code ? 'Active' : '',
      techArea: g.activity_code || '',
      matchedCompanies: g.matchedCompanies || [],
      state: g.orgState || ''
    });
  });

  sbir.forEach(function(a) {
    allFunding.push({
      source: 'SBIR/STTR',
      sourceClass: 'source-sbir',
      title: a.title || a.abstract || '',
      organization: a.company || a.firm || '',
      amount: a.amount || a.awardAmount || 0,
      status: a.phase || '',
      techArea: a.agency || '',
      matchedCompanies: a.matchedCompanies || [],
      state: a.state || ''
    });
  });

  nasa.forEach(function(p) {
    allFunding.push({
      source: 'NASA',
      sourceClass: 'source-nasa',
      title: p.title || '',
      organization: p.center || '',
      amount: 0,
      status: p.status || '',
      techArea: p.techArea || '',
      matchedCompanies: [],
      state: ''
    });
  });

  nsf.forEach(function(a) {
    allFunding.push({
      source: 'NSF',
      sourceClass: 'source-nsf',
      title: a.title || '',
      organization: a.awardee || '',
      amount: a.amount || 0,
      status: 'Active',
      techArea: a.sectors || '',
      matchedCompanies: [],
      state: a.state || ''
    });
  });

  sam.forEach(function(c) {
    allFunding.push({
      source: 'SAM.gov',
      sourceClass: 'source-sam',
      title: c.title || '',
      organization: c.department || c.agency || '',
      amount: parseValueToNumber(c.value || ''),
      status: c.type || '',
      techArea: '',
      matchedCompanies: c.relevantCompanies || [],
      state: ''
    });
  });

  if (allFunding.length === 0) {
    gridEl.innerHTML = '<div class="empty-state">No government R&D funding data available yet. Data pipelines are configured and will populate on next sync.</div>';
    return;
  }

  // Sort by amount descending
  allFunding.sort(function(a, b) { return (b.amount || 0) - (a.amount || 0); });

  // Stats
  if (statsEl) {
    var totalAmount = 0;
    var sourceCount = {};
    var withCompanyMatch = 0;
    allFunding.forEach(function(f) {
      totalAmount += (f.amount || 0);
      sourceCount[f.source] = (sourceCount[f.source] || 0) + 1;
      if (f.matchedCompanies && f.matchedCompanies.length > 0) withCompanyMatch++;
    });

    var totalStr = totalAmount >= 1e9 ? '$' + (totalAmount / 1e9).toFixed(1) + 'B' : totalAmount >= 1e6 ? '$' + (totalAmount / 1e6).toFixed(0) + 'M' : '$' + (totalAmount / 1e3).toFixed(0) + 'K';

    var shtml = '<div class="radar-stat-item"><span class="radar-stat-number">' + allFunding.length + '</span><span class="radar-stat-label">Total Awards</span></div>';
    shtml += '<div class="radar-stat-item"><span class="radar-stat-number">' + totalStr + '</span><span class="radar-stat-label">Total Funding</span></div>';
    shtml += '<div class="radar-stat-item"><span class="radar-stat-number">' + Object.keys(sourceCount).length + '</span><span class="radar-stat-label">Data Sources</span></div>';
    shtml += '<div class="radar-stat-item"><span class="radar-stat-number">' + withCompanyMatch + '</span><span class="radar-stat-label">Company Matches</span></div>';
    statsEl.innerHTML = shtml;
  }

  // Filters
  var sourceSet = new Set();
  allFunding.forEach(function(f) { sourceSet.add(f.source); });

  if (filtersEl) {
    var fhtml = '<select class="opp-filter-select" id="funding-source-filter"><option value="all">All Sources</option>';
    Array.from(sourceSet).sort().forEach(function(s) {
      fhtml += '<option value="' + escapeHtml(s) + '">' + escapeHtml(s) + ' (' + (allFunding.filter(function(f) { return f.source === s; }).length) + ')</option>';
    });
    fhtml += '</select>';
    fhtml += '<select class="opp-filter-select" id="funding-match-filter"><option value="all">All Awards</option><option value="matched">With Company Match</option><option value="top">Top Funded ($1M+)</option></select>';
    filtersEl.innerHTML = fhtml;

    document.getElementById('funding-source-filter').addEventListener('change', renderFunding);
    document.getElementById('funding-match-filter').addEventListener('change', renderFunding);
  }

  renderFunding();

  function renderFunding() {
    var sourceVal = document.getElementById('funding-source-filter') ? document.getElementById('funding-source-filter').value : 'all';
    var matchVal = document.getElementById('funding-match-filter') ? document.getElementById('funding-match-filter').value : 'all';

    var filtered = allFunding.filter(function(f) {
      if (sourceVal !== 'all' && f.source !== sourceVal) return false;
      if (matchVal === 'matched' && (!f.matchedCompanies || f.matchedCompanies.length === 0)) return false;
      if (matchVal === 'top' && (f.amount || 0) < 1000000) return false;
      return true;
    });

    // Limit display
    var displayCount = Math.min(filtered.length, 60);

    if (filtered.length === 0) {
      gridEl.innerHTML = '<div class="empty-state">No funding records match the selected filters.</div>';
      return;
    }

    var html = '';
    for (var i = 0; i < displayCount; i++) {
      var f = filtered[i];
      var amtStr = '';
      if (f.amount >= 1e9) amtStr = '$' + (f.amount / 1e9).toFixed(1) + 'B';
      else if (f.amount >= 1e6) amtStr = '$' + (f.amount / 1e6).toFixed(1) + 'M';
      else if (f.amount >= 1e3) amtStr = '$' + (f.amount / 1e3).toFixed(0) + 'K';
      else if (f.amount > 0) amtStr = '$' + f.amount.toLocaleString();

      var statusClass = (f.status || '').toLowerCase().indexOf('active') >= 0 || (f.status || '').toLowerCase().indexOf('phase') >= 0 ? 'status-active' : 'status-completed';

      html += '<div class="funding-card">';
      html += '<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;flex-wrap:wrap;">';
      html += '<span class="funding-card-source ' + f.sourceClass + '">' + escapeHtml(f.source) + '</span>';
      if (f.status) html += '<span class="funding-card-status ' + statusClass + '">' + escapeHtml(f.status) + '</span>';
      if (amtStr) html += '<span class="funding-card-amount">' + amtStr + '</span>';
      html += '</div>';
      html += '<div class="funding-card-title">' + escapeHtml(truncate(f.title, 120)) + '</div>';
      if (f.organization) html += '<div class="funding-card-org">' + escapeHtml(f.organization) + (f.state ? ' (' + escapeHtml(f.state) + ')' : '') + '</div>';
      if (f.techArea || (f.matchedCompanies && f.matchedCompanies.length > 0)) {
        html += '<div class="funding-card-tags">';
        if (f.techArea) {
          var areas = f.techArea.split(',');
          areas.forEach(function(a) {
            a = a.trim();
            if (a) html += '<span class="funding-tag">' + escapeHtml(truncate(a, 40)) + '</span>';
          });
        }
        if (f.matchedCompanies) {
          f.matchedCompanies.forEach(function(c) {
            var name = typeof c === 'string' ? c : (c.name || '');
            if (name) html += '<span class="funding-tag company-match">🏢 ' + escapeHtml(name) + '</span>';
          });
        }
        html += '</div>';
      }
      html += '</div>';
    }

    if (filtered.length > displayCount) {
      html += '<div class="empty-state" style="grid-column:1/-1;">Showing ' + displayCount + ' of ' + filtered.length + ' results. Use filters to narrow down.</div>';
    }

    gridEl.innerHTML = html;
  }
}

// ─── MOBILE MENU ───

// ─── VALLEY OF DEATH TRACKER ───

function initValleyOfDeath() {
  var data = (typeof VALLEY_OF_DEATH !== 'undefined') ? VALLEY_OF_DEATH : [];
  var stages = (typeof VALLEY_OF_DEATH_STAGES !== 'undefined') ? VALLEY_OF_DEATH_STAGES : [];
  var pipelineEl = document.getElementById('vod-pipeline');
  var detailEl = document.getElementById('vod-detail-grid');
  if (!pipelineEl || !detailEl) return;
  if (data.length === 0) {
    pipelineEl.innerHTML = '<div class="empty-state">No acquisition lifecycle data available.</div>';
    return;
  }

  // Count companies per stage
  var stageCounts = {};
  stages.forEach(function(s) { stageCounts[s.id] = []; });
  data.forEach(function(c) {
    if (stageCounts[c.stage]) stageCounts[c.stage].push(c);
  });

  var totalCompanies = data.length;

  // Render Sankey-style pipeline
  var pipelineHtml = '<div class="vod-stages">';
  stages.forEach(function(stage, idx) {
    var companies = stageCounts[stage.id] || [];
    var count = companies.length;
    var pct = Math.round((count / totalCompanies) * 100);
    var barWidth = Math.max(pct, 8);
    var isValley = (stage.id === 'sbir-phase-2' || stage.id === 'ota-prototype');

    pipelineHtml += '<div class="vod-stage' + (isValley ? ' vod-valley' : '') + '" data-stage="' + stage.id + '">';
    pipelineHtml += '<div class="vod-stage-header">';
    pipelineHtml += '<span class="vod-stage-label">' + stage.short + '</span>';
    pipelineHtml += '<span class="vod-stage-count" style="color:' + stage.color + ';">' + count + '</span>';
    pipelineHtml += '</div>';
    pipelineHtml += '<div class="vod-bar-track">';
    pipelineHtml += '<div class="vod-bar-fill" style="width:' + barWidth + '%;background:' + stage.color + ';"></div>';
    pipelineHtml += '</div>';
    pipelineHtml += '<div class="vod-stage-desc">' + stage.description + '</div>';
    if (isValley) {
      pipelineHtml += '<div class="vod-valley-label">⚠️ Valley of Death</div>';
    }
    // Company chips
    if (companies.length > 0) {
      pipelineHtml += '<div class="vod-companies">';
      companies.forEach(function(c) {
        pipelineHtml += '<span class="vod-company-chip" data-company="' + escapeHtml(c.company) + '" style="border-color:' + stage.color + ';">' + escapeHtml(c.company) + '</span>';
      });
      pipelineHtml += '</div>';
    }
    pipelineHtml += '</div>';

    // Arrow between stages
    if (idx < stages.length - 1) {
      pipelineHtml += '<div class="vod-arrow">→</div>';
    }
  });
  pipelineHtml += '</div>';

  // Summary stats
  var valleyCount = (stageCounts['sbir-phase-2'] || []).length + (stageCounts['ota-prototype'] || []).length;
  var productionCount = (stageCounts['production'] || []).length + (stageCounts['program-of-record'] || []).length;
  pipelineHtml += '<div class="vod-summary">';
  pipelineHtml += '<div class="vod-stat"><span class="vod-stat-num">' + totalCompanies + '</span><span class="vod-stat-label">Companies Tracked</span></div>';
  pipelineHtml += '<div class="vod-stat"><span class="vod-stat-num vod-danger">' + valleyCount + '</span><span class="vod-stat-label">In Valley of Death</span></div>';
  pipelineHtml += '<div class="vod-stat"><span class="vod-stat-num vod-success">' + productionCount + '</span><span class="vod-stat-label">Reached POR / Production</span></div>';
  pipelineHtml += '<div class="vod-stat"><span class="vod-stat-num">' + Math.round((productionCount / totalCompanies) * 100) + '%</span><span class="vod-stat-label">Survival Rate</span></div>';
  pipelineHtml += '</div>';

  pipelineEl.innerHTML = pipelineHtml;

  // Render detail grid
  var sorted = data.slice().sort(function(a, b) {
    var stageOrder = { 'production': 6, 'program-of-record': 5, 'ota-prototype': 4, 'sbir-phase-2': 3, 'sbir-phase-1': 2, 'rd-concept': 1 };
    return (stageOrder[b.stage] || 0) - (stageOrder[a.stage] || 0);
  });

  var detailHtml = '';
  sorted.forEach(function(c) {
    var stageInfo = stages.find(function(s) { return s.id === c.stage; }) || {};
    detailHtml += '<div class="vod-detail-card">';
    detailHtml += '<div class="vod-detail-header">';
    detailHtml += '<span class="vod-detail-company">' + escapeHtml(c.company) + '</span>';
    detailHtml += '<span class="vod-detail-stage" style="background:' + (stageInfo.color || '#666') + '20;color:' + (stageInfo.color || '#666') + ';">' + escapeHtml(c.label) + '</span>';
    detailHtml += '</div>';
    detailHtml += '<div class="vod-detail-meta">';
    detailHtml += '<span>TRL ' + c.trl + '</span>';
    detailHtml += '<span>' + c.contracts + ' contracts</span>';
    detailHtml += '</div>';
    detailHtml += '<p class="vod-detail-text">' + escapeHtml(c.detail) + '</p>';
    detailHtml += '</div>';
  });

  detailEl.innerHTML = detailHtml;
}

// ─── VOD TIMELINE PROGRESSION VIEW ───

function initVodTimeline() {
  var data = (typeof VALLEY_OF_DEATH !== 'undefined') ? VALLEY_OF_DEATH : [];
  var stages = (typeof VALLEY_OF_DEATH_STAGES !== 'undefined') ? VALLEY_OF_DEATH_STAGES : [];
  var timelineEl = document.getElementById('vod-timeline');
  if (!timelineEl || data.length === 0 || stages.length === 0) return;

  // Build stage index map
  var stageIndex = {};
  stages.forEach(function(s, i) { stageIndex[s.id] = i; });

  // Sort companies: production first, then by stage (descending), then by velocity
  var sorted = data.slice().sort(function(a, b) {
    var aIdx = stageIndex[a.stage] || 0;
    var bIdx = stageIndex[b.stage] || 0;
    if (bIdx !== aIdx) return bIdx - aIdx;
    // Within same stage, fast movers first
    var velOrder = { fast: 3, normal: 2, slow: 1 };
    return (velOrder[b.velocity] || 2) - (velOrder[a.velocity] || 2);
  });

  // Stage labels header
  var html = '<div class="vod-timeline-stage-labels">';
  stages.forEach(function(s) {
    html += '<div class="vod-timeline-stage-label" style="color:' + s.color + ';">' + s.short + '</div>';
  });
  html += '</div>';

  // Render each company as a timeline row
  sorted.forEach(function(c) {
    var currentIdx = stageIndex[c.stage] || 0;
    var progression = c.progression || [];
    var velocityColor = c.velocity === 'fast' ? '#22c55e' : c.velocity === 'slow' ? '#ef4444' : '#f59e0b';
    var velocityLabel = c.velocity === 'fast' ? '⚡ Fast Mover' : c.velocity === 'slow' ? '🐢 Slow' : '→ Normal';

    html += '<div class="vod-timeline-row" onclick="if(typeof openCompanyModal===\'function\')openCompanyModal(\'' + escapeHtml(c.company) + '\')">';

    // Company name + velocity
    html += '<div>';
    html += '<div class="vod-timeline-company">' + escapeHtml(c.company) + '</div>';
    html += '<div class="vod-timeline-company-velocity" style="color:' + velocityColor + ';">' + velocityLabel + '</div>';
    html += '</div>';

    // Timeline bar
    html += '<div class="vod-timeline-bar-container">';
    html += '<div class="vod-timeline-track"></div>';
    html += '<div class="vod-timeline-segments">';

    // Draw connector lines and dots for each progression step
    progression.forEach(function(step, idx) {
      var stepIdx = stageIndex[step.stage] || 0;
      var pct = (stepIdx / (stages.length - 1)) * 100;
      var stageData = stages[stepIdx];
      var color = stageData ? stageData.color : '#6b7280';
      var isCurrent = (step.stage === c.stage);

      // Connector from previous step
      if (idx > 0) {
        var prevStep = progression[idx - 1];
        var prevIdx = stageIndex[prevStep.stage] || 0;
        var prevPct = (prevIdx / (stages.length - 1)) * 100;
        html += '<div class="vod-timeline-connector" style="left:' + prevPct + '%;width:' + (pct - prevPct) + '%;background:' + color + ';opacity:0.5;"></div>';
      }

      // Dot
      html += '<div class="vod-timeline-dot' + (isCurrent ? ' current' : '') + '" style="left:' + pct + '%;background:' + color + ';border-color:' + color + ';color:' + color + ';" title="' + escapeHtml((stageData ? stageData.label : step.stage) + ' (' + step.entered + ')') + '"></div>';
    });

    // Draw predicted next stage (dashed)
    if (c.nextStage && stageIndex[c.nextStage] !== undefined) {
      var nextIdx = stageIndex[c.nextStage];
      var nextPct = (nextIdx / (stages.length - 1)) * 100;
      var currentPct = (currentIdx / (stages.length - 1)) * 100;
      html += '<div class="vod-timeline-connector" style="left:' + currentPct + '%;width:' + (nextPct - currentPct) + '%;background:rgba(255,255,255,0.15);border-top:2px dashed rgba(255,255,255,0.2);height:0;top:50%;"></div>';
      html += '<div class="vod-timeline-next" style="left:' + nextPct + '%;" title="Predicted: ' + escapeHtml(c.nextEstimate || 'TBD') + '"></div>';
    }

    html += '</div>'; // segments
    html += '</div>'; // bar container

    // Meta info (current stage + next estimate)
    html += '<div class="vod-timeline-meta">';
    var currentStageData = stages[currentIdx];
    html += '<div style="color:' + (currentStageData ? currentStageData.color : '#fff') + ';font-weight:700;">' + (currentStageData ? currentStageData.short : c.label) + '</div>';
    if (c.nextEstimate) {
      html += '<div class="vod-timeline-meta-next">→ ' + c.nextEstimate + '</div>';
    }
    html += '</div>';

    html += '</div>'; // row
  });

  timelineEl.innerHTML = html;
}

function initVodViewToggle() {
  var toggleBtns = document.querySelectorAll('.vod-view-btn');
  var pipeline = document.getElementById('vod-pipeline');
  var timeline = document.getElementById('vod-timeline');
  if (!toggleBtns.length || !pipeline || !timeline) return;

  toggleBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var view = btn.dataset.vodView;
      toggleBtns.forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');

      if (view === 'timeline') {
        pipeline.style.display = 'none';
        timeline.style.display = '';
        // Render timeline on first toggle
        if (!timeline.children.length) {
          initVodTimeline();
        }
      } else {
        pipeline.style.display = '';
        timeline.style.display = 'none';
      }
    });
  });
}

// ─── LIVE CONTRACT & AWARD FEED ───

function initLiveAwardFeed() {
  var data = (typeof LIVE_AWARD_FEED !== 'undefined') ? LIVE_AWARD_FEED : [];
  var feedEl = document.getElementById('award-feed');
  var filterEl = document.getElementById('award-feed-filters');
  if (!feedEl) return;
  if (data.length === 0) {
    feedEl.innerHTML = '<div class="empty-state">No recent awards to display.</div>';
    return;
  }

  var activeFilter = 'all';

  // Render filter buttons
  if (filterEl) {
    filterEl.innerHTML = '<div class="award-filter-row">' +
      '<button class="award-filter-btn active" data-filter="all">All Awards</button>' +
      '<button class="award-filter-btn" data-filter="contract">🏛️ Contracts</button>' +
      '<button class="award-filter-btn" data-filter="ota">⚡ OTA</button>' +
      '<button class="award-filter-btn" data-filter="sbir">🔬 SBIR</button>' +
      '</div>';

    filterEl.querySelectorAll('.award-filter-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        filterEl.querySelectorAll('.award-filter-btn').forEach(function(b) { b.classList.remove('active'); });
        btn.classList.add('active');
        activeFilter = btn.getAttribute('data-filter');
        renderFeed();
      });
    });
  }

  function renderFeed() {
    var filtered = data;
    if (activeFilter !== 'all') {
      filtered = data.filter(function(d) { return d.type === activeFilter; });
    }

    var typeConfig = {
      'contract': { label: 'CONTRACT', emoji: '🏛️', cls: 'award-contract' },
      'ota': { label: 'OTA', emoji: '⚡', cls: 'award-ota' },
      'sbir': { label: 'SBIR', emoji: '🔬', cls: 'award-sbir' }
    };

    var html = '';
    filtered.forEach(function(award) {
      var type = typeConfig[award.type] || { label: award.type, emoji: '📄', cls: '' };
      var dateStr = new Date(award.date + 'T00:00:00').toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric'
      });
      var daysAgo = Math.floor((Date.now() - new Date(award.date + 'T00:00:00').getTime()) / 86400000);
      var freshness = daysAgo <= 3 ? 'award-fresh' : (daysAgo <= 7 ? 'award-recent' : '');

      html += '<div class="award-card ' + freshness + '">';
      html += '<div class="award-card-left">';
      html += '<div class="award-date-col">';
      html += '<span class="award-date">' + dateStr + '</span>';
      if (daysAgo <= 3) html += '<span class="award-new-badge">NEW</span>';
      html += '</div>';
      html += '</div>';
      html += '<div class="award-card-center">';
      html += '<div class="award-top-row">';
      html += '<span class="award-type-badge ' + type.cls + '">' + type.emoji + ' ' + type.label + '</span>';
      html += '<span class="award-agency">' + escapeHtml(award.agency) + '</span>';
      html += '</div>';
      html += '<h4 class="award-title">' + escapeHtml(award.title) + '</h4>';
      html += '<p class="award-detail">' + escapeHtml(award.detail) + '</p>';
      html += '<span class="award-company-name">' + escapeHtml(award.company) + '</span>';
      html += '</div>';
      html += '<div class="award-card-right">';
      html += '<span class="award-value">' + escapeHtml(award.value) + '</span>';
      html += '</div>';
      html += '</div>';
    });

    feedEl.innerHTML = html;
  }

  renderFeed();
}

// ─── MOBILE MENU ───

function initGovMobileMenu() {
  var btn = document.querySelector('.mobile-menu-btn');
  var links = document.querySelector('.nav-links');
  if (!btn || !links) return;

  btn.addEventListener('click', function() {
    links.classList.toggle('open');
    btn.classList.toggle('open');
  });

  links.querySelectorAll('a').forEach(function(a) {
    a.addEventListener('click', function() {
      links.classList.remove('open');
      btn.classList.remove('open');
    });
  });
}

// ─── CONGRESSIONAL INTELLIGENCE ───

function initCongressIntel() {
  var grid = document.getElementById('congress-grid');
  var statsRow = document.getElementById('congress-stats');
  if (!grid) return;

  var bills = (typeof CONGRESS_BILLS_AUTO !== 'undefined') ? CONGRESS_BILLS_AUTO : [];
  if (!bills.length) {
    grid.innerHTML = '<p class="empty-state">No congressional data available.</p>';
    return;
  }

  // Stats
  if (statsRow) {
    var highRel = bills.filter(function(b) { return b.relevance === 'high'; }).length;
    var chambers = {};
    bills.forEach(function(b) { chambers[b.chamber] = true; });
    var sectorSet = {};
    bills.forEach(function(b) { (b.sectors || []).forEach(function(s) { sectorSet[s] = true; }); });

    statsRow.innerHTML =
      '<div class="radar-stat"><span class="radar-stat-value">' + bills.length + '</span><span class="radar-stat-label">Bills Tracked</span></div>' +
      '<div class="radar-stat"><span class="radar-stat-value">' + highRel + '</span><span class="radar-stat-label">High Relevance</span></div>' +
      '<div class="radar-stat"><span class="radar-stat-value">' + Object.keys(chambers).length + '</span><span class="radar-stat-label">Chambers</span></div>' +
      '<div class="radar-stat"><span class="radar-stat-value">' + Object.keys(sectorSet).length + '</span><span class="radar-stat-label">Sectors Affected</span></div>';
  }

  // Sort: high relevance first, then by latest action date
  var sorted = bills.slice().sort(function(a, b) {
    var relOrder = { high: 0, medium: 1, low: 2 };
    var relDiff = (relOrder[a.relevance] || 2) - (relOrder[b.relevance] || 2);
    if (relDiff !== 0) return relDiff;
    return (b.latestActionDate || '').localeCompare(a.latestActionDate || '');
  });

  var html = '';
  sorted.forEach(function(bill) {
    var relClass = bill.relevance === 'high' ? 'rel-high' : bill.relevance === 'medium' ? 'rel-medium' : 'rel-low';
    var chamberIcon = bill.chamber === 'Senate' ? '🏛️' : '🏢';
    var sectorTags = (bill.sectors || []).map(function(s) {
      return '<span class="congress-sector-tag">' + s + '</span>';
    }).join('');

    html += '<div class="congress-card ' + relClass + '">' +
      '<div class="congress-card-header">' +
        '<span class="congress-bill-number">' + chamberIcon + ' ' + bill.billNumber + '</span>' +
        '<span class="congress-relevance congress-relevance-' + bill.relevance + '">' + bill.relevance + '</span>' +
      '</div>' +
      '<div class="congress-title">' + bill.title + '</div>' +
      '<div class="congress-action">' +
        '<span class="congress-action-label">Latest:</span> ' + bill.latestAction +
        '<span class="congress-action-date"> (' + bill.latestActionDate + ')</span>' +
      '</div>' +
      '<div class="congress-impact">' + bill.impact + '</div>' +
      '<div class="congress-card-footer">' +
        '<div class="congress-sectors">' + sectorTags + '</div>' +
        (bill.url ? '<a href="' + bill.url + '" target="_blank" rel="noopener" class="congress-link">View Bill →</a>' : '') +
      '</div>' +
    '</div>';
  });

  grid.innerHTML = html;
}

// ─── SBIR/STTR TRACKER ───

function initSbirTracker() {
  var grid = document.getElementById('sbir-grid');
  if (!grid) return;

  var topics = (typeof SBIR_TOPICS_AUTO !== 'undefined') ? SBIR_TOPICS_AUTO : [];
  if (!topics.length) {
    grid.innerHTML = '<p class="empty-state">No SBIR/STTR data available.</p>';
    return;
  }

  // Sort by close date (soonest first)
  var sorted = topics.slice().sort(function(a, b) {
    return (a.closeDate || '').localeCompare(b.closeDate || '');
  });

  var html = '';
  sorted.forEach(function(topic) {
    var days = daysUntil(topic.closeDate);
    var dlClass = deadlineClass(days);
    var dlText = days < 0 ? 'Closed' : days === 0 ? 'Closes today' : days + 'd left';
    var typeClass = topic.type === 'STTR' ? 'sbir-type-sttr' : 'sbir-type-sbir';
    var phaseClass = topic.phase === 'Phase II' ? 'sbir-phase-ii' : 'sbir-phase-i';

    var companyTags = (topic.relevantCompanies || []).map(function(c) {
      return '<span class="sbir-company-tag" onclick="window.location.href=\'company.html?c=' + encodeURIComponent(c) + '\'">' + c + '</span>';
    }).join('');

    var sectorTags = (topic.sectors || []).map(function(s) {
      return '<span class="sbir-sector-tag">' + s + '</span>';
    }).join('');

    html += '<div class="sbir-card">' +
      '<div class="sbir-card-header">' +
        '<div class="sbir-badges">' +
          '<span class="sbir-type-badge ' + typeClass + '">' + topic.type + '</span>' +
          '<span class="sbir-phase-badge ' + phaseClass + '">' + topic.phase + '</span>' +
        '</div>' +
        '<span class="sbir-deadline ' + dlClass + '">' + dlText + '</span>' +
      '</div>' +
      '<div class="sbir-topic-title">' + topic.title + '</div>' +
      '<div class="sbir-topic-meta">' +
        '<span class="sbir-agency">' + topic.agency + '</span>' +
        '<span class="sbir-award">' + topic.award + '</span>' +
      '</div>' +
      '<div class="sbir-description">' + topic.description + '</div>' +
      '<div class="sbir-sectors">' + sectorTags + '</div>' +
      (companyTags ? '<div class="sbir-companies"><span class="sbir-companies-label">Matched Companies:</span>' + companyTags + '</div>' : '') +
    '</div>';
  });

  grid.innerHTML = html;
}

// ─── SECTION HEADER VISIBILITY OBSERVER ───
function initSectionObserver() {
  var headers = document.querySelectorAll('.section-header');
  if (!headers.length) return;
  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    headers.forEach(function(h) { observer.observe(h); });
  } else {
    headers.forEach(function(h) { h.classList.add('visible'); });
  }
}
