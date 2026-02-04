// ─── COUNTRY MAPPING ───
// US state codes
const US_STATES = new Set([
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID',
  'IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS',
  'MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK',
  'OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC'
]);

// Unambiguous international codes (no US state conflict)
const INTL_CODES = {
  'UK': 'United Kingdom', 'GB': 'United Kingdom',
  'FR': 'France', 'SE': 'Sweden', 'FI': 'Finland',
  'CH': 'Switzerland', 'DK': 'Denmark', 'NO': 'Norway', 'NL': 'Netherlands',
  'ES': 'Spain', 'IT': 'Italy', 'EE': 'Estonia', 'PL': 'Poland',
  'JP': 'Japan', 'KR': 'South Korea',
  'AU': 'Australia', 'SG': 'Singapore',
  'NZ': 'New Zealand', 'ZA': 'South Africa', 'BR': 'Brazil',
  'IE': 'Ireland', 'CA-CAN': 'Canada'
};

// Countries found in location strings — used to disambiguate shared codes
const LOCATION_COUNTRIES = {
  'Germany': 'Germany', 'Israel': 'Israel', 'India': 'India',
  'Argentina': 'Argentina', 'Ireland': 'Ireland'
};

function getCountry(stateCode, location) {
  // Check unambiguous international codes first
  if (INTL_CODES[stateCode]) return INTL_CODES[stateCode];

  // For ambiguous codes (DE, IL, IN, AR, GA), use the location string
  if (location) {
    for (const [keyword, country] of Object.entries(LOCATION_COUNTRIES)) {
      if (location.includes(keyword)) return country;
    }
  }

  // Default: US state
  return 'United States';
}

// ─── BOOKMARKS ───
let bookmarks = JSON.parse(localStorage.getItem('til-bookmarks') || '[]');

function isBookmarked(name) {
  return bookmarks.includes(name);
}

function toggleBookmark(name) {
  if (isBookmarked(name)) {
    bookmarks = bookmarks.filter(b => b !== name);
  } else {
    bookmarks.push(name);
  }
  localStorage.setItem('til-bookmarks', JSON.stringify(bookmarks));
}

// ─── COMPARE ───
let compareList = [];
const MAX_COMPARE = 3;

function toggleCompare(name) {
  const idx = compareList.indexOf(name);
  if (idx > -1) {
    compareList.splice(idx, 1);
  } else if (compareList.length < MAX_COMPARE) {
    compareList.push(name);
  }
  updateCompareBar();
  // Re-render to update card states
  applyFilters();
}

function updateCompareBar() {
  const bar = document.getElementById('compare-bar');
  const items = document.getElementById('compare-items');

  if (compareList.length === 0) {
    bar.classList.remove('visible');
    return;
  }

  bar.classList.add('visible');
  items.innerHTML = compareList.map(name => {
    const c = COMPANIES.find(co => co.name === name);
    const sectorInfo = SECTORS[c.sector] || { color: '#6b7280', icon: '' };
    return `<div class="compare-item">
      <span style="color:${sectorInfo.color}">${sectorInfo.icon}</span> ${name}
      <button onclick="toggleCompare('${name.replace(/'/g, "\\'")}')" class="compare-remove">&times;</button>
    </div>`;
  }).join('');
}

function showComparison() {
  if (compareList.length < 2) return;

  const companies = compareList.map(name => COMPANIES.find(c => c.name === name)).filter(Boolean);
  const body = document.getElementById('modal-body');

  body.innerHTML = `
    <h2 style="margin-bottom: 24px; color: var(--accent);">Company Comparison</h2>
    <div style="display: grid; grid-template-columns: repeat(${companies.length}, 1fr); gap: 20px;">
      ${companies.map(c => {
        const si = SECTORS[c.sector] || { color: '#6b7280', icon: '' };
        return `<div style="padding: 20px; background: var(--bg-tertiary); border-radius: 12px; border: 1px solid var(--border);">
          <div style="font-size: 12px; color: ${si.color}; margin-bottom: 8px;">${si.icon} ${c.sector}</div>
          <h3 style="margin-bottom: 4px;">${c.name}</h3>
          ${c.founder ? `<p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 12px;">${c.founder}</p>` : ''}
          <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 16px;">${c.location}</p>
          <div class="modal-stats">
            ${c.fundingStage ? `<div class="modal-stat"><span class="modal-stat-label">Stage</span><span class="modal-stat-value">${c.fundingStage}</span></div>` : ''}
            ${c.totalRaised ? `<div class="modal-stat"><span class="modal-stat-label">Raised</span><span class="modal-stat-value">${c.totalRaised}</span></div>` : ''}
            ${c.valuation ? `<div class="modal-stat"><span class="modal-stat-label">Valuation</span><span class="modal-stat-value">${c.valuation}</span></div>` : ''}
          </div>
          <p style="color: var(--text-secondary); font-size: 13px; line-height: 1.6; margin-top: 12px;">${c.description.substring(0, 200)}${c.description.length > 200 ? '...' : ''}</p>
        </div>`;
      }).join('')}
    </div>
  `;

  openModal();
}

// ─── MODAL ───
function openModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.remove('active');
  document.body.style.overflow = '';
}

function openCompanyModal(companyName) {
  const company = COMPANIES.find(c => c.name === companyName);
  if (!company) return;

  const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };
  const saved = isBookmarked(company.name);
  const country = getCountry(company.state, company.location);

  // Related companies (same sector, different company)
  const related = COMPANIES
    .filter(c => c.sector === company.sector && c.name !== company.name)
    .sort(() => Math.random() - 0.5)
    .slice(0, 4);

  const body = document.getElementById('modal-body');
  body.innerHTML = `
    <div class="modal-sector-badge" style="background:${sectorInfo.color}15; color:${sectorInfo.color}; border: 1px solid ${sectorInfo.color}30;">
      ${sectorInfo.icon} ${company.sector}
    </div>
    <h2 class="modal-company-name">${company.name}</h2>
    ${company.founder ? `<p class="modal-founder">${company.founder}</p>` : ''}
    <p class="modal-location">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
      ${company.location} &middot; ${country}
    </p>

    <div class="modal-stats">
      ${company.fundingStage ? `<div class="modal-stat"><span class="modal-stat-label">Stage</span><span class="modal-stat-value">${company.fundingStage}</span></div>` : ''}
      ${company.totalRaised ? `<div class="modal-stat"><span class="modal-stat-label">Raised</span><span class="modal-stat-value">${company.totalRaised}</span></div>` : ''}
      ${company.valuation ? `<div class="modal-stat"><span class="modal-stat-label">Valuation</span><span class="modal-stat-value">${company.valuation}</span></div>` : ''}
    </div>

    <p class="modal-description">${company.description}</p>

    <div class="modal-tags">
      ${company.tags.map(t => `<span class="tag">${t}</span>`).join('')}
    </div>

    <div class="modal-actions">
      <a href="${company.rosLink}" target="_blank" rel="noopener" class="modal-action-btn primary">
        Read Coverage
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>
      </a>
      <button class="modal-action-btn ${saved ? 'saved' : ''}" onclick="toggleBookmark('${company.name.replace(/'/g, "\\'")}'); openCompanyModal('${company.name.replace(/'/g, "\\'")}');">
        ${saved ? '★ Saved' : '☆ Save'}
      </button>
      <button class="modal-action-btn" onclick="shareCompany('${company.name.replace(/'/g, "\\'")}')">
        ↗ Share
      </button>
    </div>

    ${related.length > 0 ? `
      <div class="modal-related">
        <h4>Related Companies</h4>
        <div class="modal-related-grid">
          ${related.map(r => `
            <div class="modal-related-card" onclick="openCompanyModal('${r.name.replace(/'/g, "\\'")}')">
              <span class="modal-related-name">${r.name}</span>
              <span class="modal-related-loc">${r.location}</span>
            </div>
          `).join('')}
        </div>
      </div>
    ` : ''}
  `;

  // Update URL
  const url = new URL(window.location);
  url.searchParams.set('company', company.name);
  window.history.pushState({}, '', url);

  openModal();
}

function shareCompany(companyName) {
  const url = new URL(window.location.origin + window.location.pathname);
  url.searchParams.set('company', companyName);
  const shareUrl = url.toString();

  if (navigator.clipboard) {
    navigator.clipboard.writeText(shareUrl).then(() => {
      const btn = document.querySelector('.modal-action-btn:last-child');
      if (btn) {
        const original = btn.innerHTML;
        btn.innerHTML = '✓ Copied!';
        setTimeout(() => { btn.innerHTML = original; }, 1500);
      }
    });
  }
}

// ─── APP INITIALIZATION ───
document.addEventListener('DOMContentLoaded', () => {
  initStats();
  initMap();
  initFilters();
  renderCompanies(COMPANIES);
  renderSectors();
  initSearch();
  initScrollAnimations();
  initMobileMenu();
  initModal();
  initCompare();
  initKeyboard();
  initFeatured();
  initURLState();
  updateResultsCount(COMPANIES.length);
});

// ─── STATS COUNTER ───
function initStats() {
  const companyCount = COMPANIES.length;
  const sectorCount = Object.keys(SECTORS).length;
  const countries = new Set(COMPANIES.map(c => getCountry(c.state, c.location)));
  const countryCount = countries.size;

  // Calculate total tracked funding
  let totalFunding = 0;
  COMPANIES.forEach(c => {
    if (c.totalRaised) {
      const match = c.totalRaised.match(/([\d.]+)\s*(B|M|K)?/i);
      if (match) {
        let val = parseFloat(match[1]);
        const unit = (match[2] || '').toUpperCase();
        if (unit === 'B') val *= 1000;
        else if (unit === 'K') val *= 0.001;
        // M is the base unit
        totalFunding += val;
      }
    }
  });

  animateCounter('company-count', companyCount);
  animateCounter('sector-count', sectorCount);
  animateCounter('country-count', countryCount);

  // Format funding as $XXB+
  const fundingEl = document.getElementById('funding-count');
  if (fundingEl) {
    const fundingB = (totalFunding / 1000).toFixed(0);
    animateCounterWithPrefix('funding-count', parseInt(fundingB), '$', 'B+');
  }
}

function animateCounter(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const duration = 1200;
  const step = target / (duration / 16);

  function tick() {
    current += step;
    if (current >= target) {
      el.textContent = target;
      return;
    }
    el.textContent = Math.floor(current);
    requestAnimationFrame(tick);
  }

  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      tick();
      observer.disconnect();
    }
  });
  observer.observe(el);
}

function animateCounterWithPrefix(id, target, prefix, suffix) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const duration = 1200;
  const step = target / (duration / 16);

  function tick() {
    current += step;
    if (current >= target) {
      el.textContent = prefix + target + suffix;
      return;
    }
    el.textContent = prefix + Math.floor(current) + suffix;
    requestAnimationFrame(tick);
  }

  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      tick();
      observer.disconnect();
    }
  });
  observer.observe(el);
}

// ─── MAP ───
function initMap() {
  const map = L.map('innovators-map', {
    center: [25, 0],
    zoom: 2,
    minZoom: 2,
    maxZoom: 12,
    scrollWheelZoom: true,
    zoomControl: true
  });

  // Dark tile layer
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 19
  }).addTo(map);

  COMPANIES.forEach(company => {
    if (!company.lat || !company.lng) return;

    const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };

    const markerHtml = `<div class="custom-marker" style="background:${sectorInfo.color};">
      <span class="marker-icon">${sectorInfo.icon}</span>
    </div>`;

    const icon = L.divIcon({
      html: markerHtml,
      className: 'marker-container',
      iconSize: [28, 28],
      iconAnchor: [14, 14]
    });

    const marker = L.marker([company.lat, company.lng], { icon });

    const popupContent = `
      <div class="map-popup">
        <div class="popup-sector" style="color:${sectorInfo.color}">${sectorInfo.icon} ${company.sector}</div>
        <h3>${company.name}</h3>
        ${company.founder ? `<p class="popup-founder">${company.founder}</p>` : ''}
        <p class="popup-location">${company.location}</p>
        <p class="popup-desc">${company.description.substring(0, 140)}...</p>
        <button class="popup-link" onclick="openCompanyModal('${company.name.replace(/'/g, "\\'")}')">View Details &rarr;</button>
      </div>
    `;

    marker.bindPopup(popupContent, { maxWidth: 300 });
    marker.addTo(map);
  });
}

// ─── FILTERS ───
function initFilters() {
  // Sector chips
  const chipContainer = document.getElementById('filter-chips');
  const sectors = Object.keys(SECTORS);

  sectors.forEach(sector => {
    const chip = document.createElement('button');
    chip.className = 'chip';
    chip.dataset.sector = sector;
    chip.textContent = sector;
    chipContainer.appendChild(chip);
  });

  chipContainer.addEventListener('click', (e) => {
    if (!e.target.classList.contains('chip')) return;

    chipContainer.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    e.target.classList.add('active');

    // Sync dropdown
    const sectorFilter = document.getElementById('sector-filter');
    sectorFilter.value = e.target.dataset.sector;

    applyFilters();
  });

  // Sector dropdown
  const sectorFilter = document.getElementById('sector-filter');
  sectors.forEach(sector => {
    const opt = document.createElement('option');
    opt.value = sector;
    opt.textContent = sector;
    sectorFilter.appendChild(opt);
  });

  sectorFilter.addEventListener('change', () => {
    // Sync chips
    const chipContainer = document.getElementById('filter-chips');
    chipContainer.querySelectorAll('.chip').forEach(c => {
      c.classList.toggle('active', c.dataset.sector === sectorFilter.value);
    });
    applyFilters();
  });

  // Country dropdown
  const countryFilter = document.getElementById('country-filter');
  const countriesSet = new Set(COMPANIES.map(c => getCountry(c.state, c.location)));
  const countriesSorted = [...countriesSet].sort();
  countriesSorted.forEach(country => {
    const opt = document.createElement('option');
    opt.value = country;
    opt.textContent = country;
    countryFilter.appendChild(opt);
  });
  countryFilter.addEventListener('change', applyFilters);

  // Stage dropdown
  const stageFilter = document.getElementById('stage-filter');
  const stages = [...new Set(COMPANIES.map(c => c.fundingStage).filter(Boolean))].sort();
  stages.forEach(stage => {
    const opt = document.createElement('option');
    opt.value = stage;
    opt.textContent = stage;
    stageFilter.appendChild(opt);
  });
  stageFilter.addEventListener('change', applyFilters);

  // Sort dropdown
  document.getElementById('sort-filter').addEventListener('change', applyFilters);
}

function applyFilters() {
  const sector = document.getElementById('sector-filter').value;
  const country = document.getElementById('country-filter').value;
  const stage = document.getElementById('stage-filter').value;
  const sortBy = document.getElementById('sort-filter').value;
  const searchTerm = document.getElementById('search-input').value.toLowerCase();

  let filtered = COMPANIES;

  if (sector && sector !== 'all') {
    filtered = filtered.filter(c => c.sector === sector);
  }

  if (country && country !== 'all') {
    filtered = filtered.filter(c => getCountry(c.state, c.location) === country);
  }

  if (stage && stage !== 'all') {
    filtered = filtered.filter(c => c.fundingStage === stage);
  }

  if (searchTerm) {
    filtered = filtered.filter(c =>
      c.name.toLowerCase().includes(searchTerm) ||
      c.description.toLowerCase().includes(searchTerm) ||
      (c.founder && c.founder.toLowerCase().includes(searchTerm)) ||
      c.location.toLowerCase().includes(searchTerm) ||
      c.sector.toLowerCase().includes(searchTerm) ||
      c.tags.some(t => t.toLowerCase().includes(searchTerm)) ||
      getCountry(c.state, c.location).toLowerCase().includes(searchTerm)
    );
  }

  // Sort
  filtered = [...filtered];
  if (sortBy === 'name') {
    filtered.sort((a, b) => a.name.localeCompare(b.name));
  } else if (sortBy === 'name-desc') {
    filtered.sort((a, b) => b.name.localeCompare(a.name));
  } else if (sortBy === 'sector') {
    filtered.sort((a, b) => a.sector.localeCompare(b.sector) || a.name.localeCompare(b.name));
  } else if (sortBy === 'saved') {
    filtered.sort((a, b) => {
      const aS = isBookmarked(a.name) ? 0 : 1;
      const bS = isBookmarked(b.name) ? 0 : 1;
      return aS - bS || a.name.localeCompare(b.name);
    });
  }

  renderCompanies(filtered);
  updateResultsCount(filtered.length);

  // Update URL with filter state
  const url = new URL(window.location);
  if (sector && sector !== 'all') url.searchParams.set('sector', sector);
  else url.searchParams.delete('sector');
  if (country && country !== 'all') url.searchParams.set('country', country);
  else url.searchParams.delete('country');
  if (searchTerm) url.searchParams.set('q', searchTerm);
  else url.searchParams.delete('q');
  url.searchParams.delete('company');
  window.history.replaceState({}, '', url);

  const noResults = document.getElementById('no-results');
  noResults.style.display = filtered.length === 0 ? 'block' : 'none';
}

function updateResultsCount(count) {
  const el = document.getElementById('results-count');
  if (el) {
    el.textContent = `Showing ${count} ${count === 1 ? 'company' : 'companies'}`;
  }
}

// ─── SEARCH ───
function initSearch() {
  const input = document.getElementById('search-input');
  let debounce;

  input.addEventListener('input', () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      applyFilters();
    }, 200);
  });
}

// ─── RENDER COMPANIES ───
function renderCompanies(companies) {
  const grid = document.getElementById('company-grid');
  grid.innerHTML = '';

  companies.forEach((company, i) => {
    const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };
    const saved = isBookmarked(company.name);
    const inCompare = compareList.includes(company.name);

    const card = document.createElement('div');
    card.className = 'company-card';
    card.style.animationDelay = `${i * 0.02}s`;

    const metaItems = [];
    if (company.fundingStage) metaItems.push(`<span class="meta-stage">${company.fundingStage}</span>`);
    if (company.totalRaised) metaItems.push(`<span class="meta-raised">${company.totalRaised}</span>`);
    if (company.valuation) metaItems.push(`<span class="meta-val">${company.valuation}</span>`);

    card.innerHTML = `
      <div class="card-header">
        <div class="card-sector-badge" style="background:${sectorInfo.color}12; color:${sectorInfo.color}; border: 1px solid ${sectorInfo.color}30;">
          ${sectorInfo.icon} ${company.sector}
        </div>
        <div class="card-actions-top">
          <button class="card-bookmark ${saved ? 'active' : ''}" onclick="event.stopPropagation(); toggleBookmark('${company.name.replace(/'/g, "\\'")}'); applyFilters();" title="Save">
            ${saved ? '★' : '☆'}
          </button>
          <button class="card-compare ${inCompare ? 'active' : ''}" onclick="event.stopPropagation(); toggleCompare('${company.name.replace(/'/g, "\\'")}');" title="Compare">
            ⇔
          </button>
        </div>
      </div>
      <h3 class="card-name">${company.name}</h3>
      ${company.founder ? `<p class="card-founder">${company.founder}</p>` : ''}
      <p class="card-location">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        ${company.location}
      </p>
      ${metaItems.length ? `<div class="card-meta">${metaItems.join('')}</div>` : ''}
      <p class="card-description">${company.description}</p>
      <div class="card-tags">
        ${company.tags.slice(0, 3).map(t => `<span class="tag">${t}</span>`).join('')}
      </div>
      <div class="card-footer">
        <a href="${company.rosLink}" target="_blank" rel="noopener" class="card-link" onclick="event.stopPropagation();">
          Read Coverage <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>
        </a>
      </div>
    `;

    // Click card to open modal
    card.addEventListener('click', () => {
      openCompanyModal(company.name);
    });
    card.style.cursor = 'pointer';

    grid.appendChild(card);
  });
}

// ─── RENDER SECTORS ───
function renderSectors() {
  const grid = document.getElementById('sectors-grid');

  Object.entries(SECTORS).forEach(([name, info]) => {
    const count = COMPANIES.filter(c => c.sector === name).length;
    const card = document.createElement('div');
    card.className = 'sector-card';

    card.innerHTML = `
      <div class="sector-icon">${info.icon}</div>
      <h3>${name}</h3>
      <p>${info.description}</p>
      <div class="sector-count">${count} ${count === 1 ? 'company' : 'companies'}</div>
    `;

    card.addEventListener('click', () => {
      document.getElementById('companies').scrollIntoView({ behavior: 'smooth' });
      setTimeout(() => {
        document.getElementById('sector-filter').value = name;
        const chips = document.querySelectorAll('.chip');
        chips.forEach(c => {
          c.classList.remove('active');
          if (c.dataset.sector === name) c.classList.add('active');
        });
        applyFilters();
      }, 400);
    });

    grid.appendChild(card);
  });
}

// ─── FEATURED INNOVATORS ───
function initFeatured() {
  const scroll = document.getElementById('featured-scroll');
  if (!scroll) return;

  // Pick highest-valued companies
  const featured = COMPANIES
    .filter(c => c.valuation)
    .sort((a, b) => {
      const parseVal = v => {
        const m = v.match(/([\d.]+)\s*(B|M|T)?/i);
        if (!m) return 0;
        let val = parseFloat(m[1]);
        const unit = (m[2] || '').toUpperCase();
        if (unit === 'T') val *= 1000;
        else if (unit === 'M') val *= 0.001;
        return val;
      };
      return parseVal(b.valuation) - parseVal(a.valuation);
    })
    .slice(0, 12);

  featured.forEach(company => {
    const sectorInfo = SECTORS[company.sector] || { color: '#6b7280', icon: '' };

    const card = document.createElement('div');
    card.className = 'featured-card';

    card.innerHTML = `
      <div class="featured-card-accent" style="background: ${sectorInfo.color};"></div>
      <div class="featured-card-body">
        <span class="featured-sector" style="color: ${sectorInfo.color};">${sectorInfo.icon} ${company.sector}</span>
        <h3 class="featured-name">${company.name}</h3>
        ${company.valuation ? `<span class="featured-val">${company.valuation}</span>` : ''}
        <p class="featured-loc">${company.location}</p>
      </div>
    `;

    card.addEventListener('click', () => openCompanyModal(company.name));
    card.style.cursor = 'pointer';
    scroll.appendChild(card);
  });
}

// ─── MODAL INIT ───
function initModal() {
  const overlay = document.getElementById('modal-overlay');
  const closeBtn = document.getElementById('modal-close');

  closeBtn.addEventListener('click', () => {
    closeModal();
    // Remove company from URL
    const url = new URL(window.location);
    url.searchParams.delete('company');
    window.history.pushState({}, '', url);
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      closeModal();
      const url = new URL(window.location);
      url.searchParams.delete('company');
      window.history.pushState({}, '', url);
    }
  });
}

// ─── COMPARE INIT ───
function initCompare() {
  document.getElementById('compare-btn').addEventListener('click', showComparison);
  document.getElementById('compare-clear').addEventListener('click', () => {
    compareList = [];
    updateCompareBar();
    applyFilters();
  });
}

// ─── KEYBOARD NAVIGATION ───
function initKeyboard() {
  document.addEventListener('keydown', (e) => {
    // / to focus search
    if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
      const active = document.activeElement;
      if (active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') {
        e.preventDefault();
        document.getElementById('search-input').focus();
      }
    }

    // Escape to close modal
    if (e.key === 'Escape') {
      const overlay = document.getElementById('modal-overlay');
      if (overlay.classList.contains('active')) {
        closeModal();
        const url = new URL(window.location);
        url.searchParams.delete('company');
        window.history.pushState({}, '', url);
      }
    }

    // b to bookmark in modal
    if (e.key === 'b' && !e.ctrlKey && !e.metaKey) {
      const active = document.activeElement;
      if (active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') {
        const overlay = document.getElementById('modal-overlay');
        if (overlay.classList.contains('active')) {
          const nameEl = document.querySelector('.modal-company-name');
          if (nameEl) {
            toggleBookmark(nameEl.textContent);
            openCompanyModal(nameEl.textContent); // refresh modal
          }
        }
      }
    }
  });
}

// ─── URL STATE ───
function initURLState() {
  const params = new URLSearchParams(window.location.search);

  // Open company modal if ?company= present
  const companyParam = params.get('company');
  if (companyParam) {
    setTimeout(() => openCompanyModal(companyParam), 500);
  }

  // Apply filters from URL
  const sectorParam = params.get('sector');
  if (sectorParam) {
    document.getElementById('sector-filter').value = sectorParam;
    const chips = document.querySelectorAll('.chip');
    chips.forEach(c => {
      c.classList.remove('active');
      if (c.dataset.sector === sectorParam) c.classList.add('active');
    });
  }

  const countryParam = params.get('country');
  if (countryParam) {
    document.getElementById('country-filter').value = countryParam;
  }

  const qParam = params.get('q');
  if (qParam) {
    document.getElementById('search-input').value = qParam;
  }

  if (sectorParam || countryParam || qParam) {
    setTimeout(() => applyFilters(), 100);
  }
}

// ─── SCROLL ANIMATIONS ───
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.section-header, .sector-card, .featured-section').forEach(el => {
    observer.observe(el);
  });

  // Re-observe dynamically added sector cards
  const gridObserver = new MutationObserver(() => {
    document.querySelectorAll('.sector-card:not(.observed)').forEach(el => {
      el.classList.add('observed');
      observer.observe(el);
    });
  });

  const sectorsGrid = document.getElementById('sectors-grid');
  if (sectorsGrid) {
    gridObserver.observe(sectorsGrid, { childList: true });
  }
}

// ─── MOBILE MENU ───
function initMobileMenu() {
  const btn = document.querySelector('.mobile-menu-btn');
  const links = document.querySelector('.nav-links');

  btn.addEventListener('click', () => {
    links.classList.toggle('open');
    btn.classList.toggle('open');
  });

  links.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      links.classList.remove('open');
      btn.classList.remove('open');
    });
  });
}

// ─── SMOOTH SCROLL ───
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', (e) => {
    e.preventDefault();
    const target = document.querySelector(a.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});
