/**
 * Jobs Board JavaScript
 * The Innovators League
 */

// State
let allJobs = [];
let filteredJobs = [];
let currentPage = 1;
const JOBS_PER_PAGE = 25;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initJobs();
    setupEventListeners();
});

function initJobs() {
    // Load jobs data
    if (typeof JOBS_DATA !== 'undefined' && JOBS_DATA.length > 0) {
        allJobs = JOBS_DATA;
        filteredJobs = [...allJobs];

        // Update hero stats
        updateHeroStats();

        // Populate company filter
        populateCompanyFilter();

        // Render sector stats
        renderSectorStats();

        // Render Hiring Intelligence Dashboard
        renderHiringIntelligence();

        // Render initial jobs
        renderJobs();
    } else {
        document.getElementById('jobs-grid').innerHTML = `
            <div class="no-jobs">
                <h3>Loading Jobs...</h3>
                <p>Jobs data is being loaded. If this persists, the data may need to be refreshed.</p>
            </div>
        `;
    }
}

function updateHeroStats() {
    const stats = typeof JOBS_STATS !== 'undefined' ? JOBS_STATS : {
        totalJobs: allJobs.length,
        byCompany: {},
        remoteJobs: allJobs.filter(j => j.remote).length
    };

    // Animate counters
    animateNumber('total-jobs', stats.totalJobs);
    animateNumber('total-companies', Object.keys(stats.byCompany).length);
    animateNumber('remote-jobs', stats.remoteJobs);
}

function animateNumber(elementId, target) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const duration = 1000;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(start + (target - start) * easeOutCubic(progress));
        element.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function easeOutCubic(x) {
    return 1 - Math.pow(1 - x, 3);
}

function populateCompanyFilter() {
    const companyFilter = document.getElementById('company-filter');
    if (!companyFilter) return;

    const companies = [...new Set(allJobs.map(j => j.company))].sort();

    companies.forEach(company => {
        const option = document.createElement('option');
        option.value = company;
        option.textContent = company;
        companyFilter.appendChild(option);
    });
}

function renderSectorStats() {
    const container = document.getElementById('sector-stats');
    if (!container) return;

    const stats = typeof JOBS_STATS !== 'undefined' ? JOBS_STATS : { bySector: {} };

    // Get top sectors by job count
    const sectors = Object.entries(stats.bySector)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6);

    const sectorNames = {
        'ai': 'AI & ML',
        'defense': 'Defense',
        'space': 'Space',
        'climate': 'Climate',
        'robotics': 'Robotics',
        'nuclear': 'Nuclear',
        'autonomous': 'Autonomous',
        'quantum': 'Quantum',
        'biotech': 'Biotech',
        'chips': 'Chips'
    };

    container.innerHTML = sectors.map(([sector, count]) => `
        <div class="jobs-stat-card" onclick="filterBySector('${sector}')">
            <div class="jobs-stat-number">${count}</div>
            <div class="jobs-stat-label">${sectorNames[sector] || sector} Jobs</div>
        </div>
    `).join('');
}

function renderHiringIntelligence() {
    const stats = typeof JOBS_STATS !== 'undefined' ? JOBS_STATS : { byCompany: {}, bySector: {} };

    // Top Hiring Leaders
    const leadersContainer = document.getElementById('hiring-leaders');
    if (leadersContainer) {
        const topCompanies = Object.entries(stats.byCompany)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 6);

        const avgJobsPerCompany = Math.round(
            Object.values(stats.byCompany).reduce((a, b) => a + b, 0) /
            Object.keys(stats.byCompany).length
        );

        leadersContainer.innerHTML = topCompanies.map(([company, count], idx) => {
            const isAboveAvg = count > avgJobsPerCompany * 2;
            const growthLabel = isAboveAvg ? '🔥 Hypergrowth' : count > avgJobsPerCompany ? '📈 Growing' : '➡️ Stable';
            const badges = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣'];

            return `
                <div style="background:linear-gradient(135deg,rgba(255,255,255,0.03) 0%,rgba(255,255,255,0.01) 100%);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1.25rem;cursor:pointer;transition:all 0.2s;" onclick="filterByCompany('${company}')">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">
                        <span style="font-size:1.5rem;">${badges[idx]}</span>
                        <span style="font-size:0.7rem;padding:4px 8px;background:${isAboveAvg ? 'rgba(34,197,94,0.15)' : 'rgba(255,140,0,0.1)'};color:${isAboveAvg ? '#22c55e' : 'var(--accent-orange)'};border-radius:4px;font-weight:600;">${growthLabel}</span>
                    </div>
                    <div style="font-size:1rem;font-weight:700;color:var(--text-primary);margin-bottom:0.25rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${company}</div>
                    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.75rem;font-weight:800;color:var(--accent-orange);">${count}</div>
                    <div style="font-size:0.75rem;color:var(--text-secondary);">open positions</div>
                </div>
            `;
        }).join('');
    }

    // Sector Hiring Bars
    const sectorBarsContainer = document.getElementById('sector-hiring-bars');
    if (sectorBarsContainer) {
        const sectorData = Object.entries(stats.bySector)
            .filter(([sector]) => !['tech'].includes(sector.toLowerCase()))
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8);

        const maxJobs = sectorData[0]?.[1] || 1;

        sectorBarsContainer.innerHTML = sectorData.map(([sector, count]) => {
            const percentage = Math.round((count / maxJobs) * 100);
            const sectorColors = {
                'Space & Aerospace': '#3b82f6',
                'Defense & Security': '#ef4444',
                'AI & Software': '#8b5cf6',
                'Nuclear Energy': '#22c55e',
                'Robotics & Manufacturing': '#f59e0b',
                'Chips & Semiconductors': '#06b6d4',
                'Climate & Energy': '#10b981',
                'Drones & Autonomous': '#f97316',
                'Biotech & Health': '#ec4899',
                'Quantum Computing': '#6366f1'
            };
            const color = sectorColors[sector] || '#6b7280';

            return `
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="width:160px;font-size:0.85rem;color:var(--text-secondary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${sector}</div>
                    <div style="flex:1;height:24px;background:rgba(255,255,255,0.05);border-radius:4px;overflow:hidden;">
                        <div style="width:${percentage}%;height:100%;background:${color};border-radius:4px;transition:width 0.5s ease;"></div>
                    </div>
                    <div style="width:60px;text-align:right;font-weight:700;color:var(--text-primary);">${count.toLocaleString()}</div>
                </div>
            `;
        }).join('');
    }

    // Hiring Insights
    const insightsContainer = document.getElementById('hiring-insights');
    if (insightsContainer) {
        const totalJobs = Object.values(stats.byCompany).reduce((a, b) => a + b, 0);
        const companiesHiring = Object.keys(stats.byCompany).length;
        const avgPerCompany = Math.round(totalJobs / companiesHiring);
        const remoteJobs = stats.remoteJobs || allJobs.filter(j => j.remote).length;
        const remotePercent = Math.round((remoteJobs / totalJobs) * 100);

        // Find fastest growing sector (highest job count)
        const topSector = Object.entries(stats.bySector)
            .filter(([s]) => s !== 'tech')
            .sort((a, b) => b[1] - a[1])[0];

        insightsContainer.innerHTML = `
            <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1.25rem;text-align:center;">
                <div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Avg Jobs per Company</div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:2rem;font-weight:800;color:var(--text-primary);">${avgPerCompany}</div>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1.25rem;text-align:center;">
                <div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Remote Positions</div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:2rem;font-weight:800;color:#22c55e;">${remotePercent}%</div>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1.25rem;text-align:center;">
                <div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Hottest Sector</div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:700;color:var(--accent-orange);line-height:1.3;">${topSector ? topSector[0] : 'N/A'}</div>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1.25rem;text-align:center;">
                <div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Companies Hiring</div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:2rem;font-weight:800;color:#3b82f6;">${companiesHiring}</div>
            </div>
        `;
    }
}

function filterByCompany(company) {
    const companyFilter = document.getElementById('company-filter');
    if (companyFilter) {
        companyFilter.value = company;
        currentPage = 1;
        applyFilters();
        scrollToJobs();
    }
}

function setupEventListeners() {
    // Search
    const searchInput = document.getElementById('job-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => {
            currentPage = 1;
            applyFilters();
        }, 300));
    }

    // Filters
    ['sector-filter', 'location-filter', 'company-filter', 'sort-filter'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', () => {
                currentPage = 1;
                applyFilters();
            });
        }
    });

    // Quick filter tags
    document.querySelectorAll('.filter-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            tag.classList.toggle('active');
            currentPage = 1;
            applyFilters();
        });
    });

    // Pagination
    document.getElementById('prev-page')?.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderJobs();
            scrollToJobs();
        }
    });

    document.getElementById('next-page')?.addEventListener('click', () => {
        const totalPages = Math.ceil(filteredJobs.length / JOBS_PER_PAGE);
        if (currentPage < totalPages) {
            currentPage++;
            renderJobs();
            scrollToJobs();
        }
    });
}

function applyFilters() {
    const searchQuery = document.getElementById('job-search')?.value.toLowerCase() || '';
    const sectorFilter = document.getElementById('sector-filter')?.value || 'all';
    const locationFilter = document.getElementById('location-filter')?.value || 'all';
    const companyFilter = document.getElementById('company-filter')?.value || 'all';
    const sortFilter = document.getElementById('sort-filter')?.value || 'recent';

    // Get active quick filters
    const activeQuickFilters = Array.from(document.querySelectorAll('.filter-tag.active'))
        .map(tag => tag.dataset.filter.toLowerCase());

    filteredJobs = allJobs.filter(job => {
        // Search
        if (searchQuery) {
            const searchText = `${job.title} ${job.company} ${job.location} ${job.department}`.toLowerCase();
            if (!searchText.includes(searchQuery)) return false;
        }

        // Sector
        if (sectorFilter !== 'all' && job.sector !== sectorFilter) return false;

        // Location
        if (locationFilter !== 'all') {
            if (locationFilter === 'remote' && !job.remote) return false;
            if (locationFilter === 'sf' && !job.location.toLowerCase().includes('san francisco') &&
                !job.location.toLowerCase().includes('bay area') &&
                !job.location.toLowerCase().includes('palo alto') &&
                !job.location.toLowerCase().includes('mountain view')) return false;
            if (locationFilter === 'la' && !job.location.toLowerCase().includes('los angeles') &&
                !job.location.toLowerCase().includes('costa mesa') &&
                !job.location.toLowerCase().includes('el segundo')) return false;
            if (locationFilter === 'nyc' && !job.location.toLowerCase().includes('new york')) return false;
            if (locationFilter === 'seattle' && !job.location.toLowerCase().includes('seattle')) return false;
            if (locationFilter === 'austin' && !job.location.toLowerCase().includes('austin')) return false;
            if (locationFilter === 'boston' && !job.location.toLowerCase().includes('boston')) return false;
        }

        // Company
        if (companyFilter !== 'all' && job.company !== companyFilter) return false;

        // Quick filters (department/title keywords)
        if (activeQuickFilters.length > 0) {
            const jobText = `${job.title} ${job.department}`.toLowerCase();
            if (!activeQuickFilters.some(filter => jobText.includes(filter))) return false;
        }

        return true;
    });

    // Sort
    switch (sortFilter) {
        case 'recent':
            filteredJobs.sort((a, b) => (b.posted || '').localeCompare(a.posted || ''));
            break;
        case 'company':
            filteredJobs.sort((a, b) => a.company.localeCompare(b.company));
            break;
        case 'title':
            filteredJobs.sort((a, b) => a.title.localeCompare(b.title));
            break;
    }

    renderJobs();
}

function renderJobs() {
    const container = document.getElementById('jobs-grid');
    if (!container) return;

    const totalPages = Math.ceil(filteredJobs.length / JOBS_PER_PAGE);
    const startIndex = (currentPage - 1) * JOBS_PER_PAGE;
    const endIndex = startIndex + JOBS_PER_PAGE;
    const pageJobs = filteredJobs.slice(startIndex, endIndex);

    if (pageJobs.length === 0) {
        container.innerHTML = `
            <div class="no-jobs">
                <h3>No jobs found</h3>
                <p>Try adjusting your filters or search query.</p>
            </div>
        `;
        updatePagination(0, 0);
        return;
    }

    container.innerHTML = pageJobs.map(job => `
        <div class="job-card" onclick="window.open('${job.url}', '_blank')">
            <div class="job-main">
                <div class="job-title">${escapeHtml(job.title)}</div>
                <div class="job-company">${escapeHtml(job.company)}</div>
                <div class="job-meta">
                    <span>📍 ${escapeHtml(job.location)}</span>
                    <span>🏢 ${escapeHtml(job.department)}</span>
                    ${job.posted ? `<span>📅 ${formatDate(job.posted)}</span>` : ''}
                </div>
            </div>
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem;">
                <div class="job-badges">
                    ${job.remote ? '<span class="job-badge remote">Remote</span>' : ''}
                    <span class="job-badge sector">${job.sector}</span>
                </div>
                <a href="${job.url}" target="_blank" rel="noopener" class="job-apply" onclick="event.stopPropagation();">
                    Apply Now
                </a>
            </div>
        </div>
    `).join('');

    updatePagination(currentPage, totalPages);
}

function updatePagination(current, total) {
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const info = document.getElementById('pagination-info');

    if (prevBtn) prevBtn.disabled = current <= 1;
    if (nextBtn) nextBtn.disabled = current >= total;
    if (info) {
        info.textContent = total > 0
            ? `Page ${current} of ${total} (${filteredJobs.length} jobs)`
            : 'No results';
    }
}

function filterBySector(sector) {
    const sectorFilter = document.getElementById('sector-filter');
    if (sectorFilter) {
        sectorFilter.value = sector;
        currentPage = 1;
        applyFilters();
        scrollToJobs();
    }
}

function scrollToJobs() {
    document.getElementById('jobs-section')?.scrollIntoView({ behavior: 'smooth' });
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Mobile menu
document.querySelector('.mobile-menu-btn')?.addEventListener('click', function() {
    document.querySelector('.nav-links')?.classList.toggle('open');
    this.classList.toggle('open');
});
