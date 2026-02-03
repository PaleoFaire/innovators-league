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
  updateResultsCount(COMPANIES.length);
});

// ─── STATS COUNTER ───
function initStats() {
  const companyCount = COMPANIES.length;
  const sectorCount = Object.keys(SECTORS).length;
  const states = new Set(COMPANIES.map(c => c.state));
  const stateCount = states.size;

  animateCounter('company-count', companyCount);
  animateCounter('sector-count', sectorCount);
  animateCounter('state-count', stateCount);
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

// ─── MAP ───
function initMap() {
  const map = L.map('innovators-map', {
    center: [39.0, -98.0],
    zoom: 4,
    minZoom: 3,
    maxZoom: 12,
    scrollWheelZoom: true,
    zoomControl: true
  });

  // Light tile layer (matches Buildlist clean aesthetic)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
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
        <a href="${company.rosLink}" target="_blank" rel="noopener" class="popup-link">Read Coverage &rarr;</a>
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
  const stage = document.getElementById('stage-filter').value;
  const sortBy = document.getElementById('sort-filter').value;
  const searchTerm = document.getElementById('search-input').value.toLowerCase();

  let filtered = COMPANIES;

  if (sector && sector !== 'all') {
    filtered = filtered.filter(c => c.sector === sector);
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
      c.tags.some(t => t.toLowerCase().includes(searchTerm))
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
  }

  renderCompanies(filtered);
  updateResultsCount(filtered.length);

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
      </div>
      <h3 class="card-name">${company.name}</h3>
      ${company.founder ? `<p class="card-founder">${company.founder}</p>` : ''}
      <p class="card-location">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        ${company.location}
      </p>
      ${metaItems.length ? `<div class="card-meta">${metaItems.join('')}</div>` : ''}
      <p class="card-description">${company.description}</p>
      <div class="card-tags">
        ${company.tags.slice(0, 3).map(t => `<span class="tag">${t}</span>`).join('')}
      </div>
      <a href="${company.rosLink}" target="_blank" rel="noopener" class="card-link">
        Read Coverage <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>
      </a>
    `;

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
        // Set sector filter
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

// ─── SCROLL ANIMATIONS ───
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.section-header, .sector-card').forEach(el => {
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
