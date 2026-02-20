// ─── FRONTIER TECH TALENT GRAPH ───

(function() {
  function initTalentPageInner() {
    function safeInit(name, fn) {
      try { fn(); } catch (e) { console.error('[Talent] ' + name + ' failed:', e); }
    }

    safeInit('initHeroStats', initHeroStats);
    safeInit('initTalentFlow', initTalentFlow);
    safeInit('initMafiaExplorer', initMafiaExplorer);
    safeInit('initFounderDNA', initFounderDNA);
    safeInit('initTalentMagnets', initTalentMagnets);
    safeInit('initSectorHiring', initSectorHiring);
    safeInit('initTalentGeo', initTalentGeo);
    safeInit('initMobileMenu', initMobileMenu);
    safeInit('initSectionObserver', initSectionObserver);
  }

  // ── Hero Stats ──
  function initHeroStats() {
    const jobs = getJobsData();
    const jobsCountEl = document.getElementById('talent-jobs-count');
    const companiesEl = document.getElementById('talent-companies-hiring');
    const networksEl = document.getElementById('talent-networks');

    if (jobsCountEl) {
      animateCounter(jobsCountEl, jobs.length);
    }

    if (companiesEl) {
      const uniqueCompanies = new Set(jobs.map(j => j.company)).size;
      animateCounter(companiesEl, uniqueCompanies);
    }

    if (networksEl) {
      const mafias = getMafiaData();
      networksEl.textContent = Object.keys(mafias).length || 7;
    }
  }

  // ── Animate a counter from 0 to target ──
  function animateCounter(el, target) {
    if (!el || target <= 0) { if (el) el.textContent = '0'; return; }
    const duration = 1200;
    const start = performance.now();
    const format = (n) => n >= 1000 ? n.toLocaleString() : String(n);

    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = format(Math.round(eased * target));
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // ── Talent Flow Diagram ──
  function initTalentFlow() {
    const container = document.getElementById('flow-container');
    if (!container) return;

    const mafias = getMafiaData();
    if (!mafias || Object.keys(mafias).length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);text-align:center;">Talent flow data loading...</p>';
      return;
    }

    let html = '';
    for (const [name, data] of Object.entries(mafias)) {
      const color = data.color || '#FF6B2C';
      const sourceLabel = name.replace(' Mafia', '').replace(' Alumni', '').replace(' Deep Tech', '');
      const companies = data.companies || [];

      html += `
        <div class="flow-row">
          <div class="flow-source" style="border-color: ${color}20;">
            <span class="flow-source-dot" style="background: ${color};"></span>
            <span>${data.icon || ''} ${sourceLabel}</span>
          </div>
          <div class="flow-connector">
            <div class="flow-line" style="background: ${color}40;"><span style="position:absolute;right:-4px;top:-3px;width:0;height:0;border-left:6px solid ${color}60;border-top:4px solid transparent;border-bottom:4px solid transparent;"></span></div>
          </div>
          <div class="flow-targets">
            ${companies.map(c => `<span class="flow-target" style="border-color: ${color}30;">${c.company}</span>`).join('')}
          </div>
        </div>
      `;
    }

    container.innerHTML = html;
  }

  // ── Mafia Explorer ──
  function initMafiaExplorer() {
    const grid = document.getElementById('mafia-grid');
    if (!grid) return;

    const mafias = getMafiaData();
    if (!mafias || Object.keys(mafias).length === 0) {
      grid.innerHTML = '<p style="color:var(--text-muted);text-align:center;">Network data loading...</p>';
      return;
    }

    let html = '';
    for (const [name, data] of Object.entries(mafias)) {
      const color = data.color || '#FF6B2C';
      const companies = data.companies || [];

      html += `
        <div class="mafia-card" data-mafia="${escapeHtml(name)}">
          <div class="mafia-card-header" onclick="this.parentElement.classList.toggle('expanded')">
            <div class="mafia-header-left">
              <div class="mafia-icon" style="background: ${color}15;">${data.icon || ''}</div>
              <div>
                <div class="mafia-name">${escapeHtml(name)}</div>
                <div class="mafia-count">${companies.length} spinoff${companies.length !== 1 ? 's' : ''}</div>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <span class="mafia-badge" style="background: ${color};">${companies.length}</span>
              <div class="mafia-toggle">&#9660;</div>
            </div>
          </div>
          <div class="mafia-card-body">
            <div class="mafia-description">${escapeHtml(data.description || '')}</div>
            <div class="mafia-alumni-list">
              ${companies.map(c => `
                <div class="mafia-alumni-item" style="border-left-color: ${color};">
                  <div>
                    <div class="mafia-alumni-company">${escapeHtml(c.company)}</div>
                    <div class="mafia-alumni-founders">${escapeHtml(c.founders || '')}</div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      `;
    }

    grid.innerHTML = html;
  }

  // ── Talent Magnets Leaderboard ──
  function initTalentMagnets() {
    const list = document.getElementById('magnets-list');
    if (!list) return;

    const jobs = getJobsData();
    if (jobs.length === 0) {
      list.innerHTML = '<p style="color:var(--text-muted);text-align:center;">Job data loading...</p>';
      return;
    }

    // Group jobs by company
    const companyCounts = {};
    jobs.forEach(j => {
      const co = j.company || 'Unknown';
      if (!companyCounts[co]) companyCounts[co] = { count: 0, sector: j.sector || '' };
      companyCounts[co].count++;
      if (!companyCounts[co].sector && j.sector) companyCounts[co].sector = j.sector;
    });

    // If no sector from jobs, try COMPANIES
    const companiesData = getCompaniesData();
    const companyMap = {};
    companiesData.forEach(c => { companyMap[c.name] = c; });

    // Sort by count
    const sorted = Object.entries(companyCounts)
      .sort((a, b) => b[1].count - a[1].count)
      .slice(0, 30);

    const maxCount = sorted.length > 0 ? sorted[0][1].count : 1;

    let html = '';
    sorted.forEach(([company, data], i) => {
      const rank = i + 1;
      const sector = data.sector || (companyMap[company] ? companyMap[company].sector : '');
      const sectorInfo = getSectorInfo(sector);
      const pct = Math.round((data.count / maxCount) * 100);

      html += `
        <div class="magnet-row" style="animation-delay: ${i * 30}ms;">
          <div class="magnet-rank ${rank <= 3 ? 'top3' : ''}">${rank}</div>
          <div class="magnet-info">
            <div class="magnet-company">${escapeHtml(company)}</div>
            <div class="magnet-sector">${sectorInfo.icon} ${escapeHtml(sector)}</div>
          </div>
          <div class="magnet-bar-wrapper">
            <div class="magnet-bar-track">
              <div class="magnet-bar-fill" style="width: ${pct}%; background: linear-gradient(90deg, ${sectorInfo.color || 'var(--accent)'} 0%, ${sectorInfo.color || 'var(--accent-hover)'}88 100%);"></div>
            </div>
            <div class="magnet-count">${data.count.toLocaleString()}</div>
          </div>
        </div>
      `;
    });

    list.innerHTML = html;
  }

  // ── Sector Hiring Trends ──
  function initSectorHiring() {
    const container = document.getElementById('sector-bars');
    if (!container) return;

    const jobs = getJobsData();
    if (jobs.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);text-align:center;">Job data loading...</p>';
      return;
    }

    // Group by sector. Jobs already have a sector field.
    // For jobs without a sector, try to look up via COMPANIES.
    const companiesData = getCompaniesData();
    const companyToSector = {};
    companiesData.forEach(c => { companyToSector[c.name] = c.sector; });

    const sectorCounts = {};
    jobs.forEach(j => {
      let sector = j.sector || companyToSector[j.company] || 'Other';
      if (!sectorCounts[sector]) sectorCounts[sector] = 0;
      sectorCounts[sector]++;
    });

    const sorted = Object.entries(sectorCounts)
      .filter(([s]) => s !== 'Other')
      .sort((a, b) => b[1] - a[1]);

    const maxCount = sorted.length > 0 ? sorted[0][1] : 1;

    let html = '';
    sorted.forEach(([sector, count]) => {
      const info = getSectorInfo(sector);
      const pct = Math.round((count / maxCount) * 100);

      html += `
        <div class="sector-bar-row">
          <div class="sector-bar-label">
            <span class="sector-bar-icon">${info.icon}</span>
            <span>${escapeHtml(sector)}</span>
          </div>
          <div class="sector-bar-track">
            <div class="sector-bar-fill" style="width: ${pct}%; background: ${info.color || 'var(--accent)'};">
              <span class="sector-bar-value">${count.toLocaleString()} jobs</span>
            </div>
          </div>
          <div class="sector-bar-count-outside">${count.toLocaleString()}</div>
        </div>
      `;
    });

    // Add "Other" at the end if exists
    if (sectorCounts['Other']) {
      const count = sectorCounts['Other'];
      const pct = Math.round((count / maxCount) * 100);
      html += `
        <div class="sector-bar-row">
          <div class="sector-bar-label">
            <span class="sector-bar-icon">📋</span>
            <span>Other</span>
          </div>
          <div class="sector-bar-track">
            <div class="sector-bar-fill" style="width: ${pct}%; background: var(--text-muted);">
              <span class="sector-bar-value">${count.toLocaleString()} jobs</span>
            </div>
          </div>
          <div class="sector-bar-count-outside">${count.toLocaleString()}</div>
        </div>
      `;
    }

    container.innerHTML = html;
  }

  // ── Geographic Talent Clusters ──
  function initTalentGeo() {
    const grid = document.getElementById('geo-grid');
    if (!grid) return;

    const jobs = getJobsData();
    if (jobs.length === 0) {
      grid.innerHTML = '<p style="color:var(--text-muted);text-align:center;">Job data loading...</p>';
      return;
    }

    // Normalize locations to metro areas
    const locationCounts = {};
    const locationCompanies = {};

    jobs.forEach(j => {
      const loc = normalizeLocation(j.location || '');
      if (!loc || loc === 'Remote' || loc === 'Unknown') return;

      if (!locationCounts[loc]) {
        locationCounts[loc] = 0;
        locationCompanies[loc] = new Set();
      }
      locationCounts[loc]++;
      if (j.company) locationCompanies[loc].add(j.company);
    });

    const sorted = Object.entries(locationCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 15);

    let html = '';
    sorted.forEach(([location, count], i) => {
      const rank = i + 1;
      const companyCount = locationCompanies[location] ? locationCompanies[location].size : 0;
      const parts = location.split(', ');
      const city = parts[0];
      const state = parts.length > 1 ? parts.slice(1).join(', ') : '';

      html += `
        <div class="geo-card" style="animation: fadeInUp 0.4s ease ${i * 60}ms both;">
          <div class="geo-rank">${rank}</div>
          <div class="geo-city">${escapeHtml(city)}</div>
          <div class="geo-state">${escapeHtml(state)}</div>
          <div class="geo-stats">
            <div class="geo-stat-item">
              <span class="geo-stat-value">${count.toLocaleString()}</span>
              <span class="geo-stat-label">Jobs</span>
            </div>
            <div class="geo-stat-item">
              <span class="geo-stat-value">${companyCount}</span>
              <span class="geo-stat-label">Companies</span>
            </div>
          </div>
        </div>
      `;
    });

    grid.innerHTML = html;
  }

  // ── Location normalization ──
  function normalizeLocation(loc) {
    if (!loc) return '';
    loc = loc.trim();

    // Skip fully remote
    if (/^remote$/i.test(loc)) return 'Remote';

    // Handle "City, ST" and "City, ST, US" etc.
    // Strip country suffixes
    loc = loc.replace(/,\s*(US|USA|United States|UK|United Kingdom|CA|Canada|AU|Australia|DE|Germany|FR|France|JP|Japan|IL|Israel|NZ|New Zealand|IN|India|KR|South Korea|SG|Singapore)$/i, '');

    // Normalize common metro names
    const metroMap = {
      'San Francisco': 'San Francisco, CA',
      'SF': 'San Francisco, CA',
      'South San Francisco': 'San Francisco, CA',
      'Mountain View': 'Mountain View, CA',
      'Palo Alto': 'Palo Alto, CA',
      'Sunnyvale': 'Sunnyvale, CA',
      'Menlo Park': 'Menlo Park, CA',
      'San Jose': 'San Jose, CA',
      'Redwood City': 'Redwood City, CA',
      'Santa Clara': 'Santa Clara, CA',
      'Cupertino': 'Cupertino, CA',
      'Los Angeles': 'Los Angeles, CA',
      'El Segundo': 'Los Angeles, CA',
      'Hawthorne': 'Los Angeles, CA',
      'Irvine': 'Irvine, CA',
      'Costa Mesa': 'Costa Mesa, CA',
      'New York': 'New York, NY',
      'NYC': 'New York, NY',
      'Manhattan': 'New York, NY',
      'Brooklyn': 'New York, NY',
      'Seattle': 'Seattle, WA',
      'Bellevue': 'Seattle, WA',
      'Redmond': 'Seattle, WA',
      'Washington': 'Washington, DC',
      'Washington DC': 'Washington, DC',
      'Arlington': 'Arlington, VA',
      'Reston': 'Reston, VA',
      'Boston': 'Boston, MA',
      'Cambridge': 'Cambridge, MA',
      'Denver': 'Denver, CO',
      'Boulder': 'Boulder, CO',
      'Austin': 'Austin, TX',
      'Houston': 'Houston, TX',
      'Dallas': 'Dallas, TX',
      'San Diego': 'San Diego, CA',
      'Pittsburgh': 'Pittsburgh, PA',
      'Detroit': 'Detroit, MI',
      'Chicago': 'Chicago, IL',
      'Atlanta': 'Atlanta, GA',
      'Phoenix': 'Phoenix, AZ',
      'Tucson': 'Tucson, AZ',
      'Portland': 'Portland, OR',
      'Salt Lake City': 'Salt Lake City, UT',
      'Miami': 'Miami, FL',
      'Tampa': 'Tampa, FL',
      'Orlando': 'Orlando, FL'
    };

    // Try direct mapping on the full loc string
    const cityPart = loc.split(',')[0].trim();
    if (metroMap[cityPart]) return metroMap[cityPart];

    // If it already has a comma (City, State format) keep it
    if (loc.includes(',')) {
      return loc;
    }

    return loc;
  }

  // ── Data access helpers (with safety checks) ──
  function getJobsData() {
    if (typeof JOBS_DATA !== 'undefined' && Array.isArray(JOBS_DATA)) return JOBS_DATA;
    return [];
  }

  function getMafiaData() {
    if (typeof FOUNDER_MAFIAS !== 'undefined' && FOUNDER_MAFIAS && typeof FOUNDER_MAFIAS === 'object') return FOUNDER_MAFIAS;
    return {};
  }

  function getCompaniesData() {
    if (typeof COMPANIES !== 'undefined' && Array.isArray(COMPANIES)) return COMPANIES;
    return [];
  }

  function getSectorsData() {
    if (typeof SECTORS !== 'undefined' && SECTORS && typeof SECTORS === 'object') return SECTORS;
    return {};
  }

  function getSectorInfo(sectorName) {
    const sectors = getSectorsData();
    if (sectors[sectorName]) {
      return { icon: sectors[sectorName].icon || '', color: sectors[sectorName].color || '#FF6B2C' };
    }
    return { icon: '', color: '#FF6B2C' };
  }

  // ── Escape HTML ──
  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // ── Mobile Menu ──
  function initMobileMenu() {
    const btn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    if (!btn || !navLinks) return;

    btn.addEventListener('click', () => {
      btn.classList.toggle('open');
      navLinks.classList.toggle('open');
    });

    // Close menu on link click
    navLinks.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        btn.classList.remove('open');
        navLinks.classList.remove('open');
      });
    });
  }

  // ── Section header fade-in observer ──
  function initSectionObserver() {
    const headers = document.querySelectorAll('.section-header');
    if (!headers.length) return;

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15 });

      headers.forEach(h => observer.observe(h));
    } else {
      // Fallback: show all
      headers.forEach(h => h.classList.add('visible'));
    }
  }

  // ── Expose global initTalentPage ──
  window.initTalentPage = function() {
    if (typeof TILAuth !== 'undefined' && TILAuth.onReady) {
      TILAuth.onReady(initTalentPageInner);
    } else {
      initTalentPageInner();
    }
  };

  // ── Founder DNA Index ──
  function initFounderDNA() {
    var statsEl = document.getElementById('fd-stats-row');
    var serialEl = document.getElementById('fd-serial-section');
    var sectorEl = document.getElementById('fd-sector-grid');
    var lbEl = document.getElementById('fd-leaderboard');
    var structEl = document.getElementById('fd-structure-chart');
    if (!statsEl) return;

    var dna = (typeof FOUNDER_DNA !== 'undefined' && Array.isArray(FOUNDER_DNA)) ? FOUNDER_DNA : [];
    var sectors = (typeof FOUNDER_DNA_SECTORS !== 'undefined' && Array.isArray(FOUNDER_DNA_SECTORS)) ? FOUNDER_DNA_SECTORS : [];
    var serials = (typeof FOUNDER_SERIAL_MAP !== 'undefined' && Array.isArray(FOUNDER_SERIAL_MAP)) ? FOUNDER_SERIAL_MAP : [];
    if (dna.length === 0) return;

    // Helper: format millions
    function fmtM(val) {
      if (!val || val <= 0) return 'N/A';
      if (val >= 1000) return '$' + (val / 1000).toFixed(1) + 'B';
      return '$' + Math.round(val) + 'M';
    }

    // ── 1. Summary Stats ──
    var totalFounders = dna.reduce(function(s, d) { return s + d.founderCount; }, 0);
    var mafiaConnected = dna.filter(function(d) { return d.mafiaCount > 0; }).length;
    var mafiaPercent = Math.round((mafiaConnected / dna.length) * 100);
    var avgDna = Math.round(dna.reduce(function(s, d) { return s + d.dnaScore; }, 0) / dna.length);

    statsEl.innerHTML =
      '<div class="fd-stat-card"><div class="fd-stat-number">' + totalFounders.toLocaleString() + '</div><div class="fd-stat-label">Founders Profiled</div></div>' +
      '<div class="fd-stat-card"><div class="fd-stat-number">' + dna.length + '</div><div class="fd-stat-label">Companies</div></div>' +
      '<div class="fd-stat-card"><div class="fd-stat-number">' + mafiaPercent + '%</div><div class="fd-stat-label">Mafia Connected</div></div>' +
      '<div class="fd-stat-card"><div class="fd-stat-number">' + serials.length + '</div><div class="fd-stat-label">Serial Founders</div></div>' +
      '<div class="fd-stat-card"><div class="fd-stat-number">' + avgDna + '</div><div class="fd-stat-label">Avg DNA Score</div></div>';

    // ── 2. Serial Founders Spotlight ──
    if (serialEl && serials.length > 0) {
      var serialHtml = '<h3 class="fd-sub-header">\uD83D\uDD04 Serial Founders</h3><div class="fd-serial-grid">';
      serials.slice(0, 10).forEach(function(sf) {
        var pills = sf.companies.map(function(c) { return '<span class="fd-serial-pill">' + c + '</span>'; }).join('');
        serialHtml +=
          '<div class="fd-serial-card">' +
            '<div class="fd-serial-name">' + sf.founder + '</div>' +
            '<div class="fd-serial-companies">' + sf.companies.length + ' companies across ' + sf.sectors.length + ' sector' + (sf.sectors.length > 1 ? 's' : '') + '</div>' +
            '<div class="fd-serial-pills">' + pills + '</div>' +
            '<div class="fd-serial-badge">' + fmtM(sf.totalCapitalRaisedM) + ' total capital</div>' +
          '</div>';
      });
      serialHtml += '</div>';
      serialEl.innerHTML = serialHtml;
    }

    // ── 3. Sector DNA Patterns ──
    if (sectorEl && sectors.length > 0) {
      var sectorIcons = {};
      if (typeof SECTORS !== 'undefined') {
        Object.keys(SECTORS).forEach(function(k) { sectorIcons[k] = SECTORS[k].icon || ''; });
      }

      var sectorHtml = '<h3 class="fd-sub-header">\uD83E\uDDEC Sector DNA Patterns</h3>';
      // Show top 10 sectors by DNA score
      sectors.slice(0, 10).forEach(function(sec) {
        var icon = sectorIcons[sec.sector] || '';
        sectorHtml +=
          '<div class="fd-sector-card">' +
            '<div class="fd-sector-name">' + icon + ' ' + sec.sector + '</div>' +
            '<div class="fd-sector-stats">' +
              '<div class="fd-sector-stat"><div class="fd-sector-stat-val">' + sec.avgDnaScore + '</div><div class="fd-sector-stat-lbl">Avg DNA</div></div>' +
              '<div class="fd-sector-stat"><div class="fd-sector-stat-val">' + sec.avgFounderCount + '</div><div class="fd-sector-stat-lbl">Avg Founders</div></div>' +
              '<div class="fd-sector-stat"><div class="fd-sector-stat-val">' + sec.pctMafiaConnected + '%</div><div class="fd-sector-stat-lbl">Mafia %</div></div>' +
            '</div>' +
            '<div class="fd-sector-top">Top: ' + sec.topDnaCompanies.join(', ') + '</div>' +
          '</div>';
      });
      sectorEl.innerHTML = sectorHtml;
    }

    // ── 4. DNA Leaderboard (Top 25) ──
    if (lbEl) {
      var maxDna = dna.length > 0 ? dna[0].dnaScore : 1;
      var lbHtml = '<h3 class="fd-sub-header">\uD83C\uDFC6 Top 25 by Founder DNA Score</h3>';
      dna.slice(0, 25).forEach(function(d, idx) {
        var rank = idx + 1;
        var barWidth = Math.max(5, (d.dnaScore / maxDna) * 100);
        var mafiaTags = d.mafiaConnections.map(function(m) {
          var short = m.replace(' Mafia', '').replace(' Alumni', '').replace(' Deep Tech', '');
          return '<span class="fd-mafia-tag">' + short + '</span>';
        }).join(' ');
        var serialBadge = d.hasSerialFounder ? ' <span class="fd-serial-badge">Serial</span>' : '';
        var structIcon = { solo: '\u{1F464}', duo: '\u{1F465}', trio: '\u{1F465}', squad: '\u{1F46A}', large: '\u{1F3E2}' };
        var sIcon = structIcon[d.teamStructure] || '';

        lbHtml +=
          '<div class="fd-lb-row">' +
            '<div class="fd-lb-rank' + (rank <= 3 ? ' top3' : '') + '">' + rank + '</div>' +
            '<div class="fd-lb-info">' +
              '<div class="fd-lb-company">' + d.company + serialBadge + '</div>' +
              '<div class="fd-lb-meta">' +
                '<span>' + sIcon + ' ' + d.teamStructure + ' (' + d.founderCount + ')</span>' +
                '<span>' + d.sector + '</span>' +
                (mafiaTags ? '<span>' + mafiaTags + '</span>' : '') +
              '</div>' +
            '</div>' +
            '<div class="fd-lb-bar-wrapper"><div class="fd-lb-bar-track"><div class="fd-lb-bar-fill" style="width:' + barWidth + '%;"></div></div></div>' +
            '<div class="fd-lb-score" style="color:' + (d.dnaScore >= 60 ? 'var(--accent)' : d.dnaScore >= 45 ? 'var(--text-primary)' : 'var(--text-muted)') + ';">' + d.dnaScore + '</div>' +
          '</div>';
      });
      lbEl.innerHTML = lbHtml;
    }

    // ── 5. Team Structure Distribution ──
    if (structEl) {
      var structCounts = { solo: 0, duo: 0, trio: 0, squad: 0, large: 0 };
      dna.forEach(function(d) { structCounts[d.teamStructure] = (structCounts[d.teamStructure] || 0) + 1; });
      var total = dna.length;
      var structDefs = [
        { key: 'solo', label: 'Solo Founder', icon: '\u{1F464}', desc: '1 founder' },
        { key: 'duo', label: 'Duo', icon: '\u{1F465}', desc: '2 founders' },
        { key: 'trio', label: 'Trio', icon: '\u{1F46B}', desc: '3 founders' },
        { key: 'squad', label: 'Squad', icon: '\u{1F46A}', desc: '4-5 founders' },
        { key: 'large', label: 'Large Team', icon: '\u{1F3E2}', desc: '6+ founders' }
      ];

      var structHtml = '<h3 class="fd-sub-header">\u{1F4CA} Team Structure Distribution</h3><div class="fd-structure-chart">';
      structDefs.forEach(function(sd) {
        var count = structCounts[sd.key] || 0;
        var pct = total > 0 ? Math.round((count / total) * 100) : 0;
        structHtml +=
          '<div class="fd-structure-item">' +
            '<div class="fd-structure-icon">' + sd.icon + '</div>' +
            '<div class="fd-structure-count">' + count + '</div>' +
            '<div class="fd-structure-label">' + sd.label + '</div>' +
            '<div class="fd-structure-pct">' + pct + '% · ' + sd.desc + '</div>' +
          '</div>';
      });
      structHtml += '</div>';
      structEl.innerHTML = structHtml;
    }
  }

  // ── Boot ──
  // If on merged page (tab-talent exists), don't auto-init — wait for tab click.
  // If standalone page (no tab-talent), init normally on DOMContentLoaded.
  document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('tab-talent')) {
      window.initTalentPage();
    }
  });
})();
