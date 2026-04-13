document.addEventListener('DOMContentLoaded', function() {
  initMobileMenu();

  // Parse URL params for pre-selected companies
  var params = new URLSearchParams(window.location.search);
  var preselected = (params.get('companies') || '').split(',').filter(Boolean);
  var selectedCompanies = [];

  if (typeof COMPANIES === 'undefined') {
    document.getElementById('compare-content').innerHTML = '<p>Data loading failed.</p>';
    return;
  }

  // Resolve pre-selected slugs to company objects
  preselected.forEach(function(slug) {
    var name = slugToCompanyName(slug);
    if (name) {
      var company = COMPANIES.find(function(c) { return c.name === name; });
      if (company && selectedCompanies.length < 4) selectedCompanies.push(company);
    }
  });

  renderSelector();
  if (selectedCompanies.length >= 2) renderComparison();

  function renderSelector() {
    var container = document.getElementById('company-selector');
    var html = '<div class="selector-row">';

    for (var i = 0; i < 4; i++) {
      var company = selectedCompanies[i];
      html += '<div class="selector-slot">';
      if (company) {
        var sectorInfo = (typeof SECTORS !== 'undefined' && SECTORS[company.sector]) || { icon: '&#x1f52c;', color: '#6b7280' };
        html += '<div class="selector-company">' +
          '<span class="selector-icon">' + sectorInfo.icon + '</span>' +
          '<span class="selector-name">' + escapeHtml(company.name) + '</span>' +
          '<button class="selector-remove" data-index="' + i + '">&times;</button>' +
        '</div>';
      } else {
        html += '<input type="text" class="selector-input" placeholder="Search company..." data-slot="' + i + '">';
      }
      html += '</div>';
    }

    html += '</div>';
    if (selectedCompanies.length >= 2) {
      html += '<button class="compare-go-btn" id="compare-go">Compare ' + selectedCompanies.length + ' Companies</button>';
    } else {
      html += '<p class="selector-hint">Select at least 2 companies to compare</p>';
    }
    container.innerHTML = html;

    // Bind events
    container.querySelectorAll('.selector-remove').forEach(function(btn) {
      btn.addEventListener('click', function() {
        selectedCompanies.splice(parseInt(this.dataset.index), 1);
        renderSelector();
        if (selectedCompanies.length >= 2) renderComparison();
        else document.getElementById('compare-content').innerHTML = '';
        updateUrl();
      });
    });

    container.querySelectorAll('.selector-input').forEach(function(input) {
      var dropdown = null;
      input.addEventListener('input', debounce(function() {
        var query = input.value.trim().toLowerCase();
        if (query.length < 2) { if (dropdown) dropdown.remove(); return; }
        var matches = COMPANIES.filter(function(c) {
          return c.name.toLowerCase().includes(query) && !selectedCompanies.find(function(s) { return s.name === c.name; });
        }).slice(0, 8);

        if (dropdown) dropdown.remove();
        if (!matches.length) return;

        dropdown = document.createElement('div');
        dropdown.className = 'selector-dropdown';
        matches.forEach(function(c) {
          var opt = document.createElement('div');
          opt.className = 'selector-option';
          opt.textContent = c.name;
          opt.addEventListener('click', function() {
            selectedCompanies.push(c);
            if (dropdown) dropdown.remove();
            renderSelector();
            if (selectedCompanies.length >= 2) renderComparison();
            updateUrl();
          });
          dropdown.appendChild(opt);
        });
        input.parentNode.appendChild(dropdown);
      }, 200));
    });

    var goBtn = document.getElementById('compare-go');
    if (goBtn) {
      goBtn.addEventListener('click', function() { renderComparison(); });
    }
  }

  function updateUrl() {
    var slugs = selectedCompanies.map(function(c) { return companyToSlug(c.name); }).join(',');
    history.replaceState(null, '', 'compare.html' + (slugs ? '?companies=' + slugs : ''));
  }

  function renderComparison() {
    var container = document.getElementById('compare-content');
    if (selectedCompanies.length < 2) { container.innerHTML = ''; return; }

    var html = '';

    // 1. Overview comparison
    html += '<div class="compare-section"><h3>Overview</h3><div class="compare-table-wrap"><table class="compare-table"><thead><tr><th></th>';
    selectedCompanies.forEach(function(c) { html += '<th>' + escapeHtml(c.name) + '</th>'; });
    html += '</tr></thead><tbody>';

    var fields = [
      { label: 'Sector', key: 'sector' },
      { label: 'Location', key: 'location' },
      { label: 'Founded', key: 'founded' },
      { label: 'Stage', key: 'fundingStage' },
      { label: 'Total Raised', key: 'totalRaised' },
      { label: 'Valuation', key: 'valuation' },
      { label: 'Employees', key: 'employees' },
      { label: 'Founder', key: 'founder' },
      { label: 'Signal', key: 'signal' }
    ];

    fields.forEach(function(f) {
      html += '<tr><td class="compare-label">' + f.label + '</td>';
      selectedCompanies.forEach(function(c) {
        html += '<td>' + escapeHtml(c[f.key] || '\u2014') + '</td>';
      });
      html += '</tr>';
    });
    html += '</tbody></table></div></div>';

    // 2. Score comparison
    if (typeof INNOVATOR_SCORES !== 'undefined') {
      html += '<div class="compare-section"><h3>Frontier Index Scores</h3><div class="compare-table-wrap"><table class="compare-table"><thead><tr><th></th>';
      selectedCompanies.forEach(function(c) { html += '<th>' + escapeHtml(c.name) + '</th>'; });
      html += '</tr></thead><tbody>';

      var scoreDims = ['composite', 'techMoat', 'momentum', 'teamPedigree', 'marketGravity', 'govTraction'];
      var scoreLabels = { composite: 'Composite', techMoat: 'Tech Moat', momentum: 'Momentum', teamPedigree: 'Team', marketGravity: 'Market', govTraction: "Gov't" };

      scoreDims.forEach(function(dim) {
        html += '<tr><td class="compare-label">' + (scoreLabels[dim] || dim) + '</td>';
        selectedCompanies.forEach(function(c) {
          var score = INNOVATOR_SCORES.find(function(s) { return s.company === c.name; });
          var val = score ? (score[dim] || 0) : '\u2014';
          if (typeof val === 'number') val = val.toFixed(1);
          html += '<td>' + val + '</td>';
        });
        html += '</tr>';
      });
      html += '</tbody></table></div></div>';
    }

    // 3. Hiring comparison
    if (typeof ALT_DATA_SIGNALS !== 'undefined') {
      html += '<div class="compare-section"><h3>Hiring & Signals</h3><div class="compare-table-wrap"><table class="compare-table"><thead><tr><th></th>';
      selectedCompanies.forEach(function(c) { html += '<th>' + escapeHtml(c.name) + '</th>'; });
      html += '</tr></thead><tbody>';

      var altFields = [
        { label: 'Headcount', key: 'headcountEstimate' },
        { label: 'Hiring Velocity', key: 'hiringVelocity' },
        { label: 'Web Traffic', key: 'webTraffic' },
        { label: 'Signal Strength', key: 'signalStrength' }
      ];

      altFields.forEach(function(f) {
        html += '<tr><td class="compare-label">' + f.label + '</td>';
        selectedCompanies.forEach(function(c) {
          var alt = ALT_DATA_SIGNALS.find(function(a) { return a.company === c.name; });
          html += '<td>' + escapeHtml(alt ? String(alt[f.key] || '\u2014') : '\u2014') + '</td>';
        });
        html += '</tr>';
      });
      html += '</tbody></table></div></div>';
    }

    // 4. Radar chart for score comparison
    if (typeof Chart !== 'undefined' && typeof INNOVATOR_SCORES !== 'undefined') {
      var radarData = selectedCompanies.map(function(c) {
        var score = INNOVATOR_SCORES.find(function(s) { return s.company === c.name; });
        return score || null;
      }).filter(Boolean);

      if (radarData.length >= 2) {
        html += '<div class="compare-section"><h3>Score Radar</h3>';
        html += '<div style="max-width:500px; margin:0 auto;"><canvas id="compare-radar"></canvas></div></div>';
      }
    }

    // 5. Export button
    html += '<div class="compare-actions">' +
      '<button class="compare-export-btn" id="export-comparison">Export CSV</button>' +
      '<button class="compare-share-btn" id="share-comparison">Copy Link</button>' +
    '</div>';

    container.innerHTML = html;

    // Render radar chart after innerHTML is set
    if (typeof Chart !== 'undefined' && typeof INNOVATOR_SCORES !== 'undefined') {
      var radarDataPost = selectedCompanies.map(function(c) {
        var score = INNOVATOR_SCORES.find(function(s) { return s.company === c.name; });
        return score || null;
      }).filter(Boolean);

      if (radarDataPost.length >= 2) {
        setTimeout(function() {
          var ctx = document.getElementById('compare-radar');
          if (!ctx) return;
          var colors = ['#FF6B2C', '#60a5fa', '#22c55e', '#f59e0b'];
          try {
            new Chart(ctx, {
              type: 'radar',
              data: {
                labels: ['Tech Moat', 'Momentum', 'Team', 'Market', "Gov't"],
                datasets: radarDataPost.map(function(s, i) {
                  return {
                    label: s.company,
                    data: [s.techMoat || 0, s.momentum || 0, s.teamPedigree || 0, s.marketGravity || 0, s.govTraction || 0],
                    borderColor: colors[i % colors.length],
                    backgroundColor: colors[i % colors.length] + '20',
                    borderWidth: 2,
                    pointRadius: 3
                  };
                })
              },
              options: {
                responsive: true,
                scales: {
                  r: {
                    beginAtZero: true,
                    max: 10,
                    grid: { color: 'rgba(255,255,255,0.06)' },
                    angleLines: { color: 'rgba(255,255,255,0.06)' },
                    pointLabels: { color: 'rgba(255,255,255,0.6)', font: { size: 11 } },
                    ticks: { display: false }
                  }
                },
                plugins: {
                  legend: { labels: { color: 'rgba(255,255,255,0.7)', font: { size: 11 } } }
                }
              }
            });
          } catch(e) { console.error('[TIL] Radar chart failed:', e); }
        }, 100);
      }
    }

    // Export handler
    document.getElementById('export-comparison').addEventListener('click', function() {
      var data = selectedCompanies.map(function(c) {
        var score = (typeof INNOVATOR_SCORES !== 'undefined') ? INNOVATOR_SCORES.find(function(s) { return s.company === c.name; }) : null;
        return {
          Company: c.name,
          Sector: c.sector || '',
          Location: c.location || '',
          Stage: c.fundingStage || '',
          'Total Raised': c.totalRaised || '',
          Valuation: c.valuation || '',
          Employees: c.employees || '',
          'Composite Score': score ? score.composite : '',
          'Tech Moat': score ? score.techMoat : '',
          'Momentum': score ? score.momentum : ''
        };
      });
      exportToCSV(data, 'company-comparison.csv');
    });

    // Share handler
    document.getElementById('share-comparison').addEventListener('click', function() {
      navigator.clipboard.writeText(window.location.href).then(function() {
        var btn = document.getElementById('share-comparison');
        btn.textContent = 'Copied!';
        setTimeout(function() { btn.textContent = 'Copy Link'; }, 2000);
      });
    });
  }
});
