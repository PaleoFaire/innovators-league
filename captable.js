// ─── Cap Table Intelligence ───
// Estimates ownership, dilution, and investor stakes from funding data
// Data sources: COMPANIES, FUNDING_TRACKER (from data.js)

document.addEventListener('DOMContentLoaded', function() {
  initMobileMenu();

  var params = new URLSearchParams(window.location.search);
  var preselected = params.get('company');

  if (typeof COMPANIES === 'undefined') {
    var content = document.getElementById('captable-content');
    if (content) content.innerHTML = '<div class="captable-empty"><h3>Data loading failed.</h3><p>Unable to load company database.</p></div>';
    return;
  }

  initCompanySelector(preselected);

  if (preselected) {
    var company = COMPANIES.find(function(c) { return c.name === preselected; });
    if (company) renderCapTable(company);
  }
});

function initMobileMenu() {
  var btn = document.querySelector('.mobile-menu-btn');
  var links = document.querySelector('.nav-links');
  if (btn && links) {
    btn.addEventListener('click', function() {
      links.classList.toggle('open');
      btn.classList.toggle('open');
    });
  }
}

function debounce(fn, wait) {
  var t;
  return function() {
    var ctx = this, args = arguments;
    clearTimeout(t);
    t = setTimeout(function() { fn.apply(ctx, args); }, wait);
  };
}

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatDateAbsolute(dateStr) {
  if (!dateStr) return '—';
  // Handle YYYY-MM or YYYY-MM-DD formats
  var parts = String(dateStr).split('-');
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  if (parts.length >= 2) {
    var m = parseInt(parts[1], 10);
    if (m >= 1 && m <= 12) {
      return months[m-1] + ' ' + parts[0];
    }
  }
  return dateStr;
}

function initCompanySelector(initial) {
  var input = document.getElementById('captable-company-input');
  if (!input) return;

  var dropdown = null;

  function removeDropdown() {
    if (dropdown) {
      dropdown.remove();
      dropdown = null;
    }
  }

  input.addEventListener('input', debounce(function() {
    var query = input.value.trim().toLowerCase();
    removeDropdown();
    if (query.length < 2) return;

    var matches = COMPANIES.filter(function(c) {
      return c.name && c.name.toLowerCase().indexOf(query) !== -1;
    }).slice(0, 10);

    if (!matches.length) return;

    dropdown = document.createElement('div');
    dropdown.className = 'captable-dropdown';
    matches.forEach(function(c) {
      var opt = document.createElement('div');
      opt.className = 'captable-option';
      var sector = c.sector ? '<span class="captable-option-sector">' + escapeHtml(c.sector) + '</span>' : '';
      opt.innerHTML = '<span class="captable-option-name">' + escapeHtml(c.name) + '</span>' + sector;
      opt.addEventListener('click', function() {
        input.value = c.name;
        removeDropdown();
        renderCapTable(c);
        history.replaceState(null, '', 'captable.html?company=' + encodeURIComponent(c.name));
      });
      dropdown.appendChild(opt);
    });
    input.parentNode.appendChild(dropdown);
  }, 180));

  // Dismiss dropdown on outside click
  document.addEventListener('click', function(e) {
    if (dropdown && !input.parentNode.contains(e.target)) {
      removeDropdown();
    }
  });

  if (initial) input.value = initial;
}

function renderCapTable(company) {
  var container = document.getElementById('captable-content');
  if (!container) return;

  // Pull funding data from FUNDING_TRACKER if present
  var tracker = null;
  if (typeof FUNDING_TRACKER !== 'undefined') {
    tracker = FUNDING_TRACKER.find(function(f) {
      return f.company === company.name;
    });
  }

  // Synthesize "rounds" from the latest round + inferred prior rounds for the timeline
  var rounds = buildRoundsTimeline(company, tracker);

  var totalRaisedDisplay = (tracker && tracker.totalRaised) || company.totalRaised || 'Undisclosed';
  var valuationDisplay = (tracker && tracker.valuation) || company.valuation || 'Undisclosed';

  var html = '';

  // Header with key stats
  html += '<div class="captable-header-card">';
  html += '<div class="captable-header-top">';
  html += '<div>';
  html += '<h2 class="captable-company-name">' + escapeHtml(company.name) + '</h2>';
  if (company.sector) html += '<div class="captable-sector-tag">' + escapeHtml(company.sector) + '</div>';
  html += '</div>';
  html += '<a class="captable-profile-link" href="company.html?c=' + encodeURIComponent(company.name) + '">View Full Profile &rarr;</a>';
  html += '</div>';

  // Stat tiles — only render tiles that have real values (no "—" placeholders).
  // Empty-UI rule: never ship a stat card with no data.
  html += '<div class="captable-stats">';
  if (totalRaisedDisplay && totalRaisedDisplay !== 'Undisclosed' && totalRaisedDisplay !== '—') {
    html += statCard('Total Raised', totalRaisedDisplay);
  }
  if (company.fundingStage) {
    html += statCard('Stage', company.fundingStage);
  }
  if (valuationDisplay && valuationDisplay !== 'Undisclosed' && valuationDisplay !== '—') {
    html += statCard('Valuation', valuationDisplay);
  }
  if (rounds.length) {
    html += statCard('Rounds', String(rounds.length));
  }
  html += '</div>';
  html += '</div>';

  // Rounds timeline
  html += '<div class="captable-section">';
  html += '<h3 class="captable-section-title">Funding Rounds</h3>';
  if (rounds.length) {
    html += '<div class="rounds-timeline">';
    rounds.forEach(function(r, idx) {
      html += '<div class="round-item' + (r.latest ? ' round-item-latest' : '') + '">';
      html += '<div class="round-index">' + (idx + 1) + '</div>';
      html += '<div class="round-body">';
      html += '<div class="round-stage">' + escapeHtml(r.stage || 'Round') + (r.latest ? ' <span class="round-latest-tag">LATEST</span>' : '') + '</div>';
      html += '<div class="round-meta">';
      html += '<span class="round-amount">' + escapeHtml(r.amount || '—') + '</span>';
      html += '<span class="round-date">' + (r.date ? formatDateAbsolute(r.date) : '—') + '</span>';
      html += '</div>';
      if (r.investors && r.investors.length) {
        html += '<div class="round-investors">';
        r.investors.forEach(function(inv) {
          html += '<span class="investor-chip">' + escapeHtml(inv) + '</span>';
        });
        html += '</div>';
      }
      if (!r.confirmed) {
        html += '<div class="round-inferred">Inferred from stage progression</div>';
      }
      html += '</div>';
      html += '</div>';
    });
    html += '</div>';
  } else {
    html += '<p class="captable-empty-state">No detailed round data available. Check SEC filings for Form D and D/A filings, or the company\'s investor relations page.</p>';
  }
  html += '</div>';

  // Estimated ownership model
  html += '<div class="captable-section">';
  html += '<h3 class="captable-section-title">Estimated Ownership Model</h3>';
  html += '<p class="model-note"><span class="warn-icon">&#9888;</span> This is a <strong>MODEL</strong> based on typical frontier tech cap tables at this stage. Actual ownership requires SEC Form D or direct company disclosure.</p>';

  var estimates = estimateCapTable(company, rounds);
  html += '<div class="ownership-chart">';
  estimates.forEach(function(e) {
    html += '<div class="ownership-row">';
    html += '<div class="ownership-label">' + escapeHtml(e.category) + '</div>';
    html += '<div class="ownership-bar-container">';
    html += '<div class="ownership-bar" style="width:' + e.percent + '%;background:' + e.color + ';"></div>';
    html += '</div>';
    html += '<div class="ownership-percent">' + e.percent + '%</div>';
    html += '</div>';
  });
  html += '</div>';

  // Dilution over time
  html += '<h4 class="captable-subtitle">Founder Dilution Curve</h4>';
  html += '<div class="dilution-chart">';
  var dilutionStages = buildDilutionCurve(company);
  dilutionStages.forEach(function(d) {
    html += '<div class="dilution-point' + (d.current ? ' dilution-current' : '') + '">';
    html += '<div class="dilution-bar" style="height:' + (d.founders * 0.9) + 'px;"></div>';
    html += '<div class="dilution-stage">' + escapeHtml(d.stage) + '</div>';
    html += '<div class="dilution-pct">' + d.founders + '%</div>';
    html += '</div>';
  });
  html += '</div>';
  html += '</div>';

  // Known investors from database
  var knownInvestors = [];
  if (company.investors && company.investors.length) {
    knownInvestors = company.investors.slice();
  }
  if (tracker && tracker.leadInvestors) {
    tracker.leadInvestors.forEach(function(inv) {
      if (inv && inv !== 'Undisclosed' && knownInvestors.indexOf(inv) === -1) {
        knownInvestors.push(inv);
      }
    });
  }

  if (knownInvestors.length) {
    html += '<div class="captable-section">';
    html += '<h3 class="captable-section-title">Known Investors</h3>';
    html += '<div class="investors-tags">';
    knownInvestors.forEach(function(inv) {
      html += '<span class="investor-tag">' + escapeHtml(inv) + '</span>';
    });
    html += '</div>';
    html += '</div>';
  }

  // Disclosure
  html += '<div class="captable-disclosure">';
  html += '<strong>Methodology.</strong> Cap table estimates use typical dilution patterns for frontier tech companies at each funding stage. Founder ownership assumes a standard 10&ndash;13% option pool refresh per round and typical investor dilution of 18&ndash;22% per priced round. Results are directional &mdash; consult Form D filings or direct disclosures for precise figures.';
  html += '</div>';

  container.innerHTML = html;
}

function statCard(label, value) {
  return '<div class="captable-stat">' +
    '<span class="stat-label">' + escapeHtml(label) + '</span>' +
    '<span class="stat-value">' + escapeHtml(value) + '</span>' +
    '</div>';
}

// Build a funding-rounds timeline from real data sources only.
// Previously this synthesized empty rows for every stage Pre-Seed →
// current, then labeled them "Inferred from stage progression" — which
// looked unprofessional (8 rows of "—  —"). New rule: only return rounds
// with REAL confirmed data. If the company has no per-round detail,
// return an empty list so the caller can render the helpful empty state.
function buildRoundsTimeline(company, tracker) {
  var rounds = [];
  if (!tracker) return rounds;

  // Latest round — always emit if we have ANY data point on it
  if (tracker.lastRoundAmount || tracker.lastRoundDate || (tracker.leadInvestors && tracker.leadInvestors.length)) {
    rounds.push({
      stage: tracker.lastRound || company.fundingStage || 'Round',
      amount: tracker.lastRoundAmount || '',
      date: tracker.lastRoundDate || '',
      investors: (tracker.leadInvestors || []).filter(function(i) { return i && i !== 'Undisclosed'; }),
      latest: true,
      confirmed: true
    });
  }

  // Historical rounds — only if tracker has explicit `priorRounds` array.
  // (Future enhancement: populate priorRounds from a manual + Crunchbase
  // scrape for the IL30. For now this gracefully handles companies that
  // already have per-round data.)
  if (tracker.priorRounds && tracker.priorRounds.length) {
    tracker.priorRounds.forEach(function(r) {
      if (r.amount || r.date || (r.investors && r.investors.length)) {
        rounds.unshift({
          stage: r.stage || 'Round',
          amount: r.amount || '',
          date: r.date || '',
          investors: r.investors || [],
          latest: false,
          confirmed: true
        });
      }
    });
  }

  return rounds;
}

function parseRaised(str) {
  if (!str) return 0;
  var match = String(str).match(/\$?([0-9.]+)\s*(M|B|million|billion|K|thousand)?/i);
  if (!match) return 0;
  var num = parseFloat(match[1]);
  var unit = (match[2] || '').toLowerCase();
  if (unit.charAt(0) === 'b') return num * 1000;
  if (unit.charAt(0) === 'k') return num / 1000;
  return num; // default M
}

function estimateCapTable(company, rounds) {
  var stage = (company.fundingStage || '').toLowerCase().trim();

  // Typical ownership breakdown by stage (frontier tech averages)
  var defaults = {
    'pre-seed': { founders: 82, investors: 10, esop: 8 },
    'seed':     { founders: 70, investors: 20, esop: 10 },
    'series a': { founders: 55, investors: 32, esop: 13 },
    'series b': { founders: 42, investors: 45, esop: 13 },
    'series c': { founders: 32, investors: 55, esop: 13 },
    'series d': { founders: 25, investors: 62, esop: 13 },
    'series e': { founders: 20, investors: 67, esop: 13 },
    'series f': { founders: 17, investors: 70, esop: 13 },
    'series g': { founders: 15, investors: 72, esop: 13 }
  };

  var profile = defaults[stage] || defaults['series b'];

  return [
    { category: 'Founders & Early Team', percent: profile.founders, color: '#FF6B2C' },
    { category: 'Investors (Aggregate)', percent: profile.investors, color: '#60a5fa' },
    { category: 'Employee Stock Option Pool', percent: profile.esop, color: '#22c55e' }
  ];
}

function buildDilutionCurve(company) {
  var stages = ['Seed', 'Series A', 'Series B', 'Series C', 'Series D', 'Series E', 'Series F', 'Series G'];
  var founderPct = [70, 55, 42, 32, 25, 20, 17, 15];
  var currentStage = (company.fundingStage || '').toLowerCase().trim();

  var currentIdx = 2; // default to Series B
  for (var i = 0; i < stages.length; i++) {
    if (stages[i].toLowerCase() === currentStage) {
      currentIdx = i;
      break;
    }
  }

  // Show from seed through current stage (or just current if very early)
  var out = [];
  for (var j = 0; j <= currentIdx; j++) {
    out.push({
      stage: stages[j],
      founders: founderPct[j],
      current: (j === currentIdx)
    });
  }
  return out;
}
