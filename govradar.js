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

// ─── MASTER INIT ───

function initGovRadar() {
  safeInit('heroStats', initHeroStats);
  safeInit('demandHeatmap', initDemandHeatmap);
  safeInit('opportunities', initOpportunities);
  safeInit('contractorReadiness', initContractorReadiness);
  safeInit('budgetSignals', initBudgetSignals);
  safeInit('fedRegister', initFedRegister);
  safeInit('agencySpending', initAgencySpending);
  safeInit('companyMatch', initCompanyMatch);
  safeInit('mobileMenu', initGovMobileMenu);
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
  var tracker = (typeof GOV_DEMAND_TRACKER !== 'undefined') ? GOV_DEMAND_TRACKER : [];

  // Count opportunities
  var oppCount = tracker.length;
  animateCounter('gov-opp-count', oppCount);

  // Pipeline value
  var totalVal = 0;
  tracker.forEach(function(opp) {
    totalVal += parseValueToNumber(opp.value);
  });
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

  // Unique agencies
  var agencies = new Set();
  tracker.forEach(function(opp) {
    if (opp.agency) agencies.add(opp.agency);
  });
  animateCounter('gov-agencies', agencies.size);
}

// ─── 2. DEMAND HEATMAP ───

function initDemandHeatmap() {
  var tracker = (typeof GOV_DEMAND_TRACKER !== 'undefined') ? GOV_DEMAND_TRACKER : [];
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
  var tracker = (typeof GOV_DEMAND_TRACKER !== 'undefined') ? GOV_DEMAND_TRACKER : [];
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
  var gridEl = document.getElementById('agency-grid');
  if (!gridEl) return;

  if (contracts.length === 0) {
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
  var tracker = (typeof GOV_DEMAND_TRACKER !== 'undefined') ? GOV_DEMAND_TRACKER : [];
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

    html += '<div class="match-card">';
    html += '<div class="match-company-name">' + escapeHtml(co) + '</div>';
    html += '<div class="match-count">' + opps.length + ' matching opportunit' + (opps.length === 1 ? 'y' : 'ies') + '</div>';
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
