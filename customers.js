// ─── Customer Intelligence ───
// Aggregates government contract data per company and surfaces top customers.
// Data sources: COMPANIES, GOV_CONTRACTS, GOV_CONTRACTS_AUTO, SECTORS (from data.js)

document.addEventListener('DOMContentLoaded', function() {
  initMobileMenu();
  populateSectorFilter();
  wireFilters();
  renderCustomerIntel();
});

// Current filter state
var CUSTOMER_FILTERS = {
  type: 'all',
  sector: 'all',
  sort: 'value'
};

function populateSectorFilter() {
  var sel = document.getElementById('sector-filter');
  if (!sel || typeof COMPANIES === 'undefined') return;
  var sectors = {};
  COMPANIES.forEach(function(c) {
    if (c.sector) sectors[c.sector] = true;
  });
  Object.keys(sectors).sort().forEach(function(s) {
    var opt = document.createElement('option');
    opt.value = s;
    opt.textContent = s;
    sel.appendChild(opt);
  });
}

function wireFilters() {
  // Filter pills
  var pills = document.querySelectorAll('.customers-filter');
  pills.forEach(function(p) {
    p.addEventListener('click', function() {
      pills.forEach(function(x) { x.classList.remove('active'); });
      p.classList.add('active');
      CUSTOMER_FILTERS.type = p.getAttribute('data-type') || 'all';
      renderCustomerIntel();
    });
  });

  var sectorSel = document.getElementById('sector-filter');
  if (sectorSel) {
    sectorSel.addEventListener('change', function() {
      CUSTOMER_FILTERS.sector = sectorSel.value;
      renderCustomerIntel();
    });
  }

  var sortSel = document.getElementById('sort-filter');
  if (sortSel) {
    sortSel.addEventListener('change', function() {
      CUSTOMER_FILTERS.sort = sortSel.value;
      renderCustomerIntel();
    });
  }
}

function isDoDAgency(name) {
  if (!name) return false;
  var n = name.toLowerCase();
  return /\b(dod|defense|navy|army|air force|marine|space force|darpa|afrl|afwerx|diu|office of naval|missile defense|special operations|socom)\b/.test(n);
}

function renderCustomerIntel() {
  var container = document.getElementById('customers-content');
  if (!container || typeof COMPANIES === 'undefined') {
    if (container) container.innerHTML = '<p class="empty-state">Data loading&hellip;</p>';
    return;
  }

  // Aggregate customer data from GOV_CONTRACTS
  var companyCustomers = {};

  if (typeof GOV_CONTRACTS !== 'undefined' && Array.isArray(GOV_CONTRACTS)) {
    GOV_CONTRACTS.forEach(function(c) {
      var name = c.company;
      if (!name) return;
      if (!companyCustomers[name]) {
        companyCustomers[name] = { gov: {}, total: 0, totalValue: 0, count: 0 };
      }
      var agency = c.agency || c.awardingAgency || 'Unknown';
      if (!companyCustomers[name].gov[agency]) {
        companyCustomers[name].gov[agency] = { count: 0, value: 0 };
      }
      companyCustomers[name].gov[agency].count++;
      var val = parseFloat((c.value || c.amount || '0').toString().replace(/[^0-9.]/g, '')) || 0;
      companyCustomers[name].gov[agency].value += val;
      companyCustomers[name].total++;
      companyCustomers[name].count++;
      companyCustomers[name].totalValue += val;
    });
  }

  // Also aggregate from GOV_CONTRACTS_AUTO if exists
  if (typeof GOV_CONTRACTS_AUTO !== 'undefined' && Array.isArray(GOV_CONTRACTS_AUTO)) {
    GOV_CONTRACTS_AUTO.forEach(function(c) {
      var name = c.company || c.recipient;
      if (!name) return;
      if (!companyCustomers[name]) {
        companyCustomers[name] = { gov: {}, total: 0, totalValue: 0, count: 0 };
      }
      var agency = c.agency || c.awardingAgency || 'Unknown';
      if (!companyCustomers[name].gov[agency]) {
        companyCustomers[name].gov[agency] = { count: 0, value: 0 };
      }
      companyCustomers[name].gov[agency].count++;
      var val = parseFloat((c.value || c.amount || '0').toString().replace(/[^0-9.]/g, '')) || 0;
      companyCustomers[name].gov[agency].value += val;
      companyCustomers[name].total++;
      companyCustomers[name].totalValue += val;
    });
  }

  // Build list of companies with customer data
  var companiesWithData = Object.keys(companyCustomers).map(function(name) {
    var data = companyCustomers[name];
    var agencies = Object.keys(data.gov).map(function(a) {
      return {
        name: a,
        count: data.gov[a].count,
        value: data.gov[a].value,
        isDoD: isDoDAgency(a)
      };
    }).sort(function(a, b) { return b.value - a.value || b.count - a.count; });

    var dodCount = agencies.filter(function(a) { return a.isDoD; }).length;
    return {
      company: name,
      agencies: agencies,
      total: data.count,
      totalValue: data.totalValue,
      hasDoD: dodCount > 0,
      hasCivilian: agencies.length - dodCount > 0
    };
  });

  // Apply filters
  var filtered = companiesWithData.filter(function(d) {
    // Type filter
    if (CUSTOMER_FILTERS.type === 'dod' && !d.hasDoD) return false;
    if (CUSTOMER_FILTERS.type === 'civilian' && !d.hasCivilian) return false;
    if (CUSTOMER_FILTERS.type === 'gov' && d.total === 0) return false;

    // Sector filter
    if (CUSTOMER_FILTERS.sector !== 'all') {
      var company = COMPANIES.find(function(c) { return c.name === d.company; });
      if (!company || company.sector !== CUSTOMER_FILTERS.sector) return false;
    }
    return true;
  });

  // Sort
  filtered.sort(function(a, b) {
    if (CUSTOMER_FILTERS.sort === 'count') {
      return b.total - a.total || b.totalValue - a.totalValue;
    }
    if (CUSTOMER_FILTERS.sort === 'name') {
      return (a.company || '').localeCompare(b.company || '');
    }
    // Default: value
    return b.totalValue - a.totalValue || b.total - a.total;
  });

  // Compute aggregate stats
  var totalCompanies = filtered.length;
  var totalContracts = filtered.reduce(function(s, c) { return s + c.total; }, 0);
  var totalValue = filtered.reduce(function(s, c) { return s + c.totalValue; }, 0);
  var dodCompanies = filtered.filter(function(c) { return c.hasDoD; }).length;

  // Render
  var html = '<div class="customers-stats-bar">';
  html += '<div class="customers-stat"><span class="customers-stat-value">' + totalCompanies + '</span><span class="customers-stat-label">Companies Tracked</span></div>';
  html += '<div class="customers-stat"><span class="customers-stat-value">' + totalContracts.toLocaleString() + '</span><span class="customers-stat-label">Total Contracts</span></div>';
  html += '<div class="customers-stat"><span class="customers-stat-value">' + formatValue(totalValue) + '</span><span class="customers-stat-label">Total Contract Value</span></div>';
  html += '<div class="customers-stat"><span class="customers-stat-value">' + dodCompanies + '</span><span class="customers-stat-label">DoD Customers</span></div>';
  html += '</div>';

  if (filtered.length === 0) {
    html += '<div class="customer-empty"><div class="customer-empty-icon">&#128202;</div><h3>No Customer Data Yet</h3><p>Customer intelligence is built from GOV_CONTRACTS data. Try changing filters or check back once data has loaded.</p></div>';
    container.innerHTML = html;
    return;
  }

  html += '<div class="customers-grid">';
  filtered.slice(0, 60).forEach(function(d) {
    var company = COMPANIES.find(function(c) { return c.name === d.company; });
    var sector = company ? company.sector : '';
    var sectorInfo = (typeof SECTORS !== 'undefined' && sector && SECTORS[sector]) || { icon: '&#128230;', color: '#6b7280' };

    html += '<div class="customer-card" data-sector="' + escapeHtml(sector) + '">';
    html += '<div class="customer-card-header">';
    html += '<div class="customer-card-title">';
    html += '<h3><a href="company.html?c=' + encodeURIComponent(d.company) + '">' + escapeHtml(d.company) + '</a></h3>';
    if (sector) {
      html += '<span class="customer-sector" style="color:' + sectorInfo.color + ';border-color:' + sectorInfo.color + '33;background:' + sectorInfo.color + '10;">' + sectorInfo.icon + ' ' + escapeHtml(sector) + '</span>';
    }
    html += '</div>';
    html += '<div class="customer-badges">';
    html += '<div class="customer-badge">' + d.total + ' contracts</div>';
    if (d.totalValue > 0) {
      html += '<div class="customer-badge customer-badge-value">' + formatValue(d.totalValue) + '</div>';
    }
    html += '</div>';
    html += '</div>';
    html += '<div class="customer-agencies">';
    html += '<div class="agencies-label">TOP GOVERNMENT CUSTOMERS</div>';
    d.agencies.slice(0, 5).forEach(function(a) {
      var pct = d.total > 0 ? Math.round((a.count / d.total) * 100) : 0;
      var icon = a.isDoD ? '&#128737;' : '&#127963;';
      html += '<div class="agency-row">';
      html += '<span class="agency-name">' + icon + ' ' + escapeHtml(a.name) + (a.isDoD ? ' <span class="agency-dod-tag">DoD</span>' : '') + '</span>';
      html += '<div class="agency-meta">';
      html += '<span class="agency-count">' + a.count + (a.count === 1 ? ' contract' : ' contracts') + '</span>';
      html += '<span class="agency-pct">' + pct + '%</span>';
      html += '</div>';
      html += '<div class="agency-bar"><div class="agency-bar-fill" style="width:' + pct + '%;"></div></div>';
      html += '</div>';
    });
    if (d.agencies.length > 5) {
      html += '<div class="agency-more">+ ' + (d.agencies.length - 5) + ' more agencies</div>';
    }
    html += '</div>';
    html += '</div>';
  });
  html += '</div>';

  container.innerHTML = html;
}

// Format dollar value for display
function formatValue(val) {
  if (!val || isNaN(val)) return '$0';
  var num = Number(val);
  if (num >= 1e9) return '$' + (num / 1e9).toFixed(1) + 'B';
  if (num >= 1e6) return '$' + (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return '$' + (num / 1e3).toFixed(1) + 'K';
  return '$' + num.toFixed(0);
}

// Helper: simple HTML escape (in case utils.js not loaded)
if (typeof escapeHtml === 'undefined') {
  window.escapeHtml = function(str) {
    if (str == null) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  };
}

if (typeof initMobileMenu === 'undefined') {
  window.initMobileMenu = function() {
    var btn = document.querySelector('.mobile-menu-btn');
    var links = document.querySelector('.nav-links');
    if (btn && links) {
      btn.addEventListener('click', function() {
        links.classList.toggle('open');
        btn.classList.toggle('open');
      });
    }
  };
}
