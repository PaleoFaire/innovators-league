/*
 * Sector Landing Page — Shared Renderer
 *
 * Used by the SEO landing pages (defense.html, space.html, nuclear.html,
 * reindustrialize.html). Each landing sets a global `window.IL_SECTOR_CONFIG`
 * before loading this script:
 *
 *   window.IL_SECTOR_CONFIG = {
 *     slug:     "defense",
 *     title:    "Defense Tech Companies",
 *     // One of:
 *     sectors:  ["Defense & Security", "Drones & Autonomous"],
 *     // or, for the omnibus reindustrialize page, an inclusive whitelist of
 *     // every sector that counts as "rebuilding the industrial base":
 *     sectorWhitelist: [...]
 *   };
 *
 * Reads from the global COMPANIES array provided by data.js.
 */
(function () {
  'use strict';

  function escapeHTML(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function formatMoney(v) {
    if (typeof v === 'number') {
      if (v >= 1e9) return '$' + (v / 1e9).toFixed(1).replace(/\.0$/, '') + 'B';
      if (v >= 1e6) return '$' + (v / 1e6).toFixed(0) + 'M';
      return '$' + v.toLocaleString();
    }
    return v || '—';
  }

  function getFunding(c) {
    return c.totalFunding || c.funding || c.lastValuation || c.lastRound || null;
  }

  function getSectorColor(sector) {
    var map = {
      'Defense & Security':       '#ff6b2c',
      'Drones & Autonomous':      '#ff8147',
      'Space & Aerospace':        '#60a5fa',
      'Nuclear Energy':           '#facc15',
      'Climate & Energy':         '#4ade80',
      'Robotics & Manufacturing': '#a78bfa',
      'Chips & Semiconductors':   '#06b6d4',
      'AI & Software':            '#8b5cf6',
      'Biotech & Health':         '#ec4899',
      'Quantum Computing':        '#a855f7',
      'Supersonic & Hypersonic':  '#f43f5e',
      'Ocean & Maritime':         '#0ea5e9',
      'Housing & Construction':   '#84cc16',
      'Infrastructure & Logistics': '#f59e0b',
      'Transportation':           '#64748b',
    };
    return map[sector] || '#22c55e';
  }

  function getStageColor(stage) {
    if (!stage) return '#8b949e';
    var s = stage.toLowerCase();
    if (s.indexOf('public') !== -1 || s.indexOf('ipo') !== -1) return '#22c55e';
    if (s.indexOf('series d') !== -1 || s.indexOf('series e') !== -1 ||
        s.indexOf('series f') !== -1 || s.indexOf('series g') !== -1) return '#facc15';
    if (s.indexOf('series c') !== -1) return '#fbbf24';
    if (s.indexOf('series b') !== -1) return '#f59e0b';
    if (s.indexOf('series a') !== -1) return '#fb7185';
    if (s.indexOf('seed') !== -1)     return '#a78bfa';
    return '#8b949e';
  }

  function renderCard(c) {
    var sectorColor = getSectorColor(c.sector);
    var stage = c.stage || c.fundingStage || '';
    var stageColor = getStageColor(stage);
    var funding = formatMoney(getFunding(c));
    var location = c.location || c.headquarters || '';
    var desc = c.description || c.summary || '';
    if (desc.length > 180) desc = desc.slice(0, 178) + '…';

    var slug = (c.slug || c.id || c.ticker || c.name || '').toString();
    var detailHref = 'company.html?c=' + encodeURIComponent(c.name || c.id || c.slug || '');

    return ''
      + '<a class="sl-card" href="' + detailHref + '">'
      +   '<div class="sl-card-head">'
      +     '<div class="sl-card-name">' + escapeHTML(c.name) + '</div>'
      +     '<span class="sl-card-sector" style="background:' + sectorColor + '22;color:' + sectorColor + ';border-color:' + sectorColor + '44;">'
      +       escapeHTML(c.sector || '—')
      +     '</span>'
      +   '</div>'
      +   (desc ? '<p class="sl-card-desc">' + escapeHTML(desc) + '</p>' : '')
      +   '<div class="sl-card-meta">'
      +     (location ? '<span class="sl-card-loc">📍 ' + escapeHTML(location) + '</span>' : '')
      +     (stage ? '<span class="sl-card-stage" style="color:' + stageColor + ';">' + escapeHTML(stage) + '</span>' : '')
      +     (funding && funding !== '—' ? '<span class="sl-card-funding">' + escapeHTML(funding) + '</span>' : '')
      +   '</div>'
      + '</a>';
  }

  function filterCompanies(config) {
    if (typeof window.COMPANIES === 'undefined') return [];
    var matchSet = null;
    if (config.sectors) matchSet = new Set(config.sectors);
    else if (config.sectorWhitelist) matchSet = new Set(config.sectorWhitelist);

    var out = window.COMPANIES.filter(function (c) {
      if (!c || !c.name) return false;
      if (!matchSet) return true;
      return matchSet.has(c.sector);
    });

    // Sort: known funding (numerical) descending, then alphabetical
    out.sort(function (a, b) {
      var fa = getFunding(a), fb = getFunding(b);
      var na = (typeof fa === 'number') ? fa : 0;
      var nb = (typeof fb === 'number') ? fb : 0;
      if (na !== nb) return nb - na;
      return (a.name || '').localeCompare(b.name || '');
    });

    return out;
  }

  function renderStats(companies, container) {
    if (!container) return;
    var totalFunding = 0;
    var byStage = {};
    var byLocation = {};
    companies.forEach(function (c) {
      var f = getFunding(c);
      if (typeof f === 'number') totalFunding += f;
      var stage = (c.stage || c.fundingStage || 'Unknown').toLowerCase();
      var stageKey = stage.indexOf('public') !== -1 ? 'Public'
        : stage.indexOf('series') !== -1 ? 'Venture-backed'
        : stage.indexOf('seed') !== -1 ? 'Early'
        : 'Other';
      byStage[stageKey] = (byStage[stageKey] || 0) + 1;
      var loc = (c.location || c.headquarters || '').split(',')[0].trim() || 'Unknown';
      if (loc) byLocation[loc] = (byLocation[loc] || 0) + 1;
    });

    var topCities = Object.keys(byLocation)
      .filter(function (k) { return k && k !== 'Unknown'; })
      .sort(function (a, b) { return byLocation[b] - byLocation[a]; })
      .slice(0, 3);

    var html = ''
      + '<div class="sl-stat"><div class="sl-stat-n">' + companies.length + '</div><div class="sl-stat-l">Companies tracked</div></div>'
      + '<div class="sl-stat"><div class="sl-stat-n">' + formatMoney(totalFunding) + '</div><div class="sl-stat-l">Capital raised</div></div>'
      + '<div class="sl-stat"><div class="sl-stat-n">' + (byStage['Public'] || 0) + '</div><div class="sl-stat-l">Publicly traded</div></div>'
      + '<div class="sl-stat"><div class="sl-stat-n">' + topCities.join(' · ') + '</div><div class="sl-stat-l">Top hubs</div></div>';
    container.innerHTML = html;
  }

  function renderGrid(companies, container) {
    if (!container) return;
    if (!companies.length) {
      container.innerHTML = '<div class="sl-empty">No companies in this sector yet. Check back soon.</div>';
      return;
    }
    container.innerHTML = companies.map(renderCard).join('');
  }

  function init() {
    var config = window.IL_SECTOR_CONFIG || {};
    var companies = filterCompanies(config);

    renderStats(companies, document.getElementById('sl-stats'));
    renderGrid(companies, document.getElementById('sl-grid'));

    var countEl = document.getElementById('sl-count');
    if (countEl) countEl.textContent = String(companies.length);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
