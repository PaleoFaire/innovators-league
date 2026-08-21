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

  // The canonical field in data.js is `totalRaised`, holding a display string
  // like "$175M", "$2.6B+" or "$17.5M". None of the four names this used to
  // look for (totalFunding / funding / lastValuation / lastRound) exists on a
  // single record, so every card showed no funding and the sector header read
  // "$0 CAPITAL RAISED" across 215 defence companies.
  //
  // Returns a NUMBER of dollars so the callers that sum and sort actually
  // work; they were summing a field that was always null.
  function getFunding(c) {
    var raw = c.totalRaised || c.totalFunding || c.funding || null;
    if (typeof raw === 'number') return raw;
    if (typeof raw !== 'string') return null;
    var m = raw.replace(/,/g, '').match(/\$?\s*([\d.]+)\s*([BMK])?/i);
    if (!m) return null;
    var n = parseFloat(m[1]);
    if (isNaN(n)) return null;
    var unit = (m[2] || '').toUpperCase();
    return n * (unit === 'B' ? 1e9 : unit === 'M' ? 1e6 : unit === 'K' ? 1e3 : 1);
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

  // data.js declares `const COMPANIES = [...]` at the top level of a classic
  // script. A top-level `const` lives in the script-global lexical scope and
  // is NOT a property of `window` — so `window.COMPANIES` is undefined even
  // though `COMPANIES` resolves fine. This function tested `window.COMPANIES`
  // and bailed, which is why defense, nuclear, space and reindustrialize all
  // rendered "0 COMPANIES TRACKED / $0 CAPITAL RAISED / No companies in this
  // sector yet" while the array sat right there with 1,181 records in it.
  function allCompanies() {
    if (typeof window.COMPANIES !== 'undefined' && window.COMPANIES) return window.COMPANIES;
    if (typeof COMPANIES !== 'undefined' && COMPANIES) return COMPANIES;
    return null;
  }

  function filterCompanies(config) {
    var all = allCompanies();
    if (!all) return [];
    var matchSet = null;
    if (config.sectors) matchSet = new Set(config.sectors);
    else if (config.sectorWhitelist) matchSet = new Set(config.sectorWhitelist);

    var out = all.filter(function (c) {
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
    // Group by subsector — the market-map view. Named shelves first (largest
    // first), the General residual last so the page leads with its verticals
    // ("Humanoids (24)", "Launch (28)") instead of an undifferentiated wall.
    var groups = {};
    companies.forEach(function (c) {
      var k = c.subsector || 'General';
      (groups[k] = groups[k] || []).push(c);
    });
    var keys = Object.keys(groups).sort(function (a, b) {
      if (a === 'General') return 1;
      if (b === 'General') return -1;
      return groups[b].length - groups[a].length;
    });
    if (keys.length < 2) {
      container.innerHTML = companies.map(renderCard).join('');
      return;
    }
    container.innerHTML = keys.map(function (k) {
      return '<div class="sl-subsector-head" style="grid-column:1/-1; margin:26px 0 2px; display:flex; align-items:center; gap:12px;">'
        + '<span style="font:700 13px/1 \'Space Grotesk\',sans-serif; letter-spacing:.12em; text-transform:uppercase; color:var(--text-primary);">'
        + escapeHTML(k) + '</span>'
        + '<span style="font:600 11px/1 Inter,sans-serif; color:var(--text-muted);">' + groups[k].length + '</span>'
        + '<span style="flex:1; height:1px; background:var(--border);"></span>'
        + '</div>'
        + groups[k].map(renderCard).join('');
    }).join('');
  }

  function injectItemListJsonLd(companies, name) {
    if (!companies.length) return;
    var top = companies.slice(0, 50);
    var data = {
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      'name': name || document.title,
      'numberOfItems': companies.length,
      'itemListElement': top.map(function (c, i) {
        return {
          '@type': 'ListItem',
          'position': i + 1,
          'name': c.name,
          'url': 'https://innovatorsleague.com/company.html?c=' + encodeURIComponent(c.name)
        };
      })
    };
    var s = document.createElement('script');
    s.type = 'application/ld+json';
    s.setAttribute('data-il-itemlist', '1');
    s.textContent = JSON.stringify(data);
    document.head.appendChild(s);
  }

  function init() {
    var config = window.IL_SECTOR_CONFIG || {};
    var companies = filterCompanies(config);

    renderStats(companies, document.getElementById('sl-stats'));
    renderGrid(companies, document.getElementById('sl-grid'));

    var countEl = document.getElementById('sl-count');
    if (countEl) countEl.textContent = String(companies.length);

    injectItemListJsonLd(companies, config.title);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
