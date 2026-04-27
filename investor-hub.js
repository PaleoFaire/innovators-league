/**
 * Investor Hub — investor-hub.html
 *
 * Renders four investor-grade tools on one page:
 *   1. Active Raise Calendar (Form D filings, last 60 days)
 *   2. Unified Funding Pulse (Form D + news + press releases, chronological)
 *   3. Co-Investor Network Graph (D3-style force layout, no D3 dependency)
 *   4. Investor Directory (cards linking to per-firm deep pages)
 *
 * Empty-UI rule: every section either renders real data OR shows an
 * explicit "no data this week" empty state. No placeholder dashes.
 *
 * Data sources (every datapoint links to its primary source):
 *   - FORM_D_FILINGS  — SEC EDGAR
 *   - COMPANY_SIGNALS_AUTO — funding-relevant news
 *   - PRESS_RELEASES_AUTO — original publisher links
 *   - VC_FIRMS — curated, links to firm websites
 */

(function () {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function G(name) {
    if (typeof window[name] !== 'undefined') return window[name];
    try { return new Function('try { return typeof ' + name + ' !== "undefined" ? ' + name + ' : null; } catch (e) { return null; }')(); }
    catch (e) { return null; }
  }

  function fmtAmount(s) {
    if (!s) return '';
    const n = parseFloat(String(s).replace(/[^0-9.]/g, ''));
    if (!n || isNaN(n)) return s;
    if (n >= 1e9) return '$' + (n / 1e9).toFixed(2) + 'B';
    if (n >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return '$' + (n / 1e3).toFixed(0) + 'K';
    return '$' + n.toFixed(0);
  }

  function daysAgo(s) {
    if (!s) return '';
    const d = new Date(String(s).slice(0, 10) + 'T00:00:00Z');
    if (isNaN(d)) return '';
    const days = Math.floor((Date.now() - d) / 86400000);
    if (days < 0) return 'upcoming';
    if (days === 0) return 'today';
    if (days === 1) return '1d ago';
    if (days < 30) return days + 'd ago';
    if (days < 365) return Math.floor(days / 30) + 'mo ago';
    return Math.floor(days / 365) + 'y ago';
  }

  // Determine ROS Fund check-size fit: green = $100K-$250K, amber = stretch, red = too big
  function checkFit(offering) {
    if (!offering) return { class: 'gray', label: 'Size unknown' };
    const n = parseFloat(String(offering).replace(/[^0-9.]/g, ''));
    if (!n || isNaN(n)) return { class: 'gray', label: 'Size unknown' };
    // Heuristic: round size correlates roughly with check needed
    // Most rounds, our $100-250K is meaningful at < $5M total raise
    if (n < 5e6) return { class: 'green', label: 'Direct fit' };
    if (n < 25e6) return { class: 'amber', label: 'SPV / stretch' };
    if (n < 100e6) return { class: 'red', label: 'Too big · LP play' };
    return { class: 'gray', label: 'Late stage' };
  }

  // ═══ SECTION 1: Active Raise Calendar ═══
  function renderActiveRaises() {
    const body = document.getElementById('ih-raise-body');
    const meta = document.getElementById('ih-raise-meta');
    const stat = document.getElementById('ih-stat-raises');
    if (!body) return;
    const data = G('FORM_D_FILINGS');
    const filings = (data && Array.isArray(data.filings)) ? data.filings : [];
    if (stat) stat.textContent = filings.length || '0';
    if (meta) meta.textContent = filings.length + ' filings · last ' + (data?.lookback_days || 60) + ' days';
    if (filings.length === 0) {
      body.innerHTML = '<div class="ih-empty">No active Form D filings in the last 60 days from tracked companies. The pipeline is live; new filings will appear as the SEC publishes them.</div>';
      return;
    }
    // Sort newest first
    const sorted = [...filings].sort((a, b) =>
      String(b.filed_date || '').localeCompare(String(a.filed_date || ''))
    );

    const rows = sorted.map(f => {
      const fit = checkFit(f.offering_amount);
      const isSafe = f.is_safe || /safe/i.test(f.securities_type || '');
      return '<tr>' +
        '<td class="ih-raise-co">' +
          '<a href="company.html?c=' + encodeURIComponent(f.company) + '">' + esc(f.company) + '</a>' +
          (f.issuer_name && f.issuer_name !== f.company ?
            '<div style="font-size:11px; color:rgba(255,255,255,0.4); font-style:italic;">' + esc(f.issuer_name) + '</div>'
            : '') +
        '</td>' +
        '<td><span class="ih-raise-amt">' + esc(fmtAmount(f.offering_amount) || '—') + '</span>' +
          (isSafe ? '<div style="font-size:10px; color:#fbbf24; margin-top:2px;">SAFE</div>' : '') +
        '</td>' +
        '<td>' + esc(f.filed_date || '') +
          '<div style="font-size:11px; color:rgba(255,255,255,0.5);">' + esc(daysAgo(f.filed_date)) + '</div>' +
        '</td>' +
        '<td><span class="ih-raise-fit ' + fit.class + '">' + esc(fit.label) + '</span></td>' +
        '<td>' + (f.filing_url
          ? '<a class="ih-source-link" href="' + esc(f.filing_url) + '" target="_blank" rel="noopener">SEC EDGAR →</a>'
          : '') + '</td>' +
      '</tr>';
    }).join('');

    body.innerHTML =
      '<table class="ih-raise-table">' +
        '<thead><tr>' +
          '<th>Company</th><th>Offering</th><th>Filed</th><th>ROS Fund Fit</th><th>Source</th>' +
        '</tr></thead>' +
        '<tbody>' + rows + '</tbody>' +
      '</table>';
  }

  // ═══ SECTION 2: Unified Funding Pulse ═══
  function buildPulseFeed() {
    const items = [];
    // Form D
    const fdData = G('FORM_D_FILINGS');
    if (fdData && Array.isArray(fdData.filings)) {
      fdData.filings.forEach(f => {
        items.push({
          type: 'formd',
          tag: 'FORM D',
          company: f.company,
          headline: 'Form D filed · ' + (fmtAmount(f.offering_amount) || 'undisclosed amount') +
            (f.is_safe ? ' (SAFE)' : ''),
          date: f.filed_date,
          url: f.filing_url,
        });
      });
    }
    // News signals (filtered to funding-relevant types)
    const news = G('COMPANY_SIGNALS_AUTO');
    if (Array.isArray(news)) {
      news.forEach(n => {
        const fundingRelated = n.type === 'funding' ||
          /raise|raises|raised|funding|series|seed|round|valuation|invest/i.test(n.headline || '');
        if (!fundingRelated) return;
        items.push({
          type: 'news',
          tag: 'NEWS',
          company: n.company,
          headline: n.headline,
          dateText: n.time,
          source: n.source,
          url: n.link,
        });
      });
    }
    // Press releases (filtered to funding signals)
    const press = G('PRESS_RELEASES_AUTO');
    if (Array.isArray(press)) {
      press.slice(0, 80).forEach(p => {
        const ttl = (p.title || p.headline || '').toLowerCase();
        if (!/raise|funding|series|seed|invest|million|billion/.test(ttl)) return;
        items.push({
          type: 'press',
          tag: 'PRESS',
          company: p.company || p.source,
          headline: p.title || p.headline,
          date: p.date || p.published,
          source: p.source,
          url: p.link || p.url,
        });
      });
    }
    return items;
  }

  function renderPulseFeed(filter) {
    const body = document.getElementById('ih-pulse-body');
    const meta = document.getElementById('ih-pulse-meta');
    const stat = document.getElementById('ih-stat-pulse');
    if (!body) return;
    const allItems = buildPulseFeed();
    if (stat) stat.textContent = allItems.length;
    const items = (!filter || filter === 'all') ? allItems
      : allItems.filter(i => i.type === filter);
    if (meta) meta.textContent = items.length + ' items' + (filter && filter !== 'all' ? ' · ' + filter : '');
    if (items.length === 0) {
      body.innerHTML = '<div class="ih-empty">No funding-relevant items in this filter.</div>';
      return;
    }
    // Sort: items with date first (newest), then items with dateText
    items.sort((a, b) => {
      if (a.date && b.date) return String(b.date).localeCompare(String(a.date));
      if (a.date) return -1;
      if (b.date) return 1;
      return 0;
    });

    body.innerHTML = '<div class="ih-pulse-list">' +
      items.slice(0, 60).map(i => {
        const dateLabel = i.date ? (i.date.slice(0, 10) + ' · ' + daysAgo(i.date))
          : (i.dateText || '');
        return '<div class="ih-pulse-item ' + i.type + '">' +
          '<div class="ih-pulse-tag ' + i.type + '">' + esc(i.tag) + '</div>' +
          '<div>' +
            (i.company ?
              '<div class="ih-pulse-co"><a href="company.html?c=' + encodeURIComponent(i.company) + '">' + esc(i.company) + '</a></div>'
              : '') +
            '<div class="ih-pulse-headline">' +
              (i.url ? '<a href="' + esc(i.url) + '" target="_blank" rel="noopener">' + esc(i.headline) + '</a>'
                : esc(i.headline)) +
              (i.source ? ' <span style="color:rgba(255,255,255,0.35); font-size:10px;">— ' + esc(i.source) + '</span>' : '') +
            '</div>' +
          '</div>' +
          '<div class="ih-pulse-time">' + esc(dateLabel) + '</div>' +
        '</div>';
      }).join('') + '</div>';
  }

  function wirePulseFilters() {
    document.querySelectorAll('#ih-pulse-filters .ih-filter-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#ih-pulse-filters .ih-filter-chip').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderPulseFeed(btn.getAttribute('data-filter'));
      });
    });
  }

  // ═══ SECTION 3: Co-Investor Network Graph ═══
  function renderCoInvestorGraph() {
    const svg = document.getElementById('ih-graph-svg');
    const info = document.getElementById('ih-graph-info');
    const meta = document.getElementById('ih-graph-meta');
    const statEdges = document.getElementById('ih-stat-edges');
    if (!svg) return;

    const firms = G('VC_FIRMS');
    if (!Array.isArray(firms) || firms.length === 0) {
      if (info) info.innerHTML = '<em>VC_FIRMS data unavailable.</em>';
      return;
    }

    // Compute edges: for every pair, count shared portfolio companies
    const nodes = firms.filter(f => Array.isArray(f.portfolioCompanies) && f.portfolioCompanies.length > 0)
      .map((f, i) => ({
        id: i,
        firm: f,
        portfolio: new Set(f.portfolioCompanies.map(c => c.toLowerCase())),
        size: f.portfolioCompanies.length,
        x: 0, y: 0, vx: 0, vy: 0,
      }));

    const edges = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const shared = [...nodes[i].portfolio].filter(c => nodes[j].portfolio.has(c));
        if (shared.length > 0) {
          edges.push({ source: nodes[i], target: nodes[j], weight: shared.length, shared });
        }
      }
    }
    if (statEdges) statEdges.textContent = edges.length;
    if (meta) meta.textContent = nodes.length + ' firms · ' + edges.length + ' edges';

    // Initialize positions in a circle
    const W = 1200, H = 600, cx = W / 2, cy = H / 2;
    nodes.forEach((n, i) => {
      const angle = (i / nodes.length) * Math.PI * 2;
      n.x = cx + Math.cos(angle) * 200;
      n.y = cy + Math.sin(angle) * 180;
    });

    // Run a simple force simulation (no D3 dependency)
    runForceSimulation(nodes, edges, W, H);

    // Render edges
    const edgesG = document.getElementById('ih-graph-edges');
    const nodesG = document.getElementById('ih-graph-nodes');
    if (!edgesG || !nodesG) return;
    edgesG.innerHTML = '';
    nodesG.innerHTML = '';

    const ns = 'http://www.w3.org/2000/svg';
    edges.forEach((e, idx) => {
      const line = document.createElementNS(ns, 'line');
      line.setAttribute('x1', e.source.x);
      line.setAttribute('y1', e.source.y);
      line.setAttribute('x2', e.target.x);
      line.setAttribute('y2', e.target.y);
      line.setAttribute('stroke-width', Math.min(4, 0.5 + e.weight * 0.4));
      line.setAttribute('class', 'ih-edge');
      line.setAttribute('data-edge-idx', idx);
      edgesG.appendChild(line);
    });

    nodes.forEach(n => {
      const g = document.createElementNS(ns, 'g');
      g.setAttribute('class', 'ih-node');
      g.setAttribute('data-firm', n.firm.name);
      g.setAttribute('transform', 'translate(' + n.x + ',' + n.y + ')');
      const r = Math.max(8, Math.min(28, 6 + Math.sqrt(n.size) * 3));
      const circle = document.createElementNS(ns, 'circle');
      circle.setAttribute('r', r);
      g.appendChild(circle);
      const text = document.createElementNS(ns, 'text');
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('y', r + 12);
      text.textContent = n.firm.shortName || n.firm.name;
      g.appendChild(text);
      nodesG.appendChild(g);

      // Hover + click
      g.addEventListener('mouseenter', () => highlightFirm(n, edges));
      g.addEventListener('mouseleave', () => unhighlight());
      g.addEventListener('click', () => {
        // Show co-investors panel
        const partners = edges
          .filter(e => e.source === n || e.target === n)
          .map(e => ({ other: e.source === n ? e.target : e.source, weight: e.weight, shared: e.shared }))
          .sort((a, b) => b.weight - a.weight);

        if (info) {
          let html = '<strong>' + esc(n.firm.name) + '</strong> · ' + n.size + ' tracked companies in portfolio.<br>';
          if (partners.length) {
            html += 'Top co-investors: ';
            html += partners.slice(0, 5).map(p =>
              '<a href="investor-firm.html?firm=' + encodeURIComponent(p.other.firm.name) + '" style="color:#86efac; text-decoration:none;">' +
              esc(p.other.firm.shortName || p.other.firm.name) + ' (' + p.weight + ')' + '</a>'
            ).join(' · ');
            html += ' · <a href="investor-firm.html?firm=' + encodeURIComponent(n.firm.name) + '" style="color:#86efac;">Open ' + esc(n.firm.shortName || n.firm.name) + ' deep page →</a>';
          } else {
            html += 'No co-investors detected (no portfolio overlap with other tracked firms).';
          }
          info.innerHTML = html;
        }
      });
    });
  }

  function highlightFirm(node, edges) {
    document.querySelectorAll('.ih-node').forEach(g => g.classList.add('dimmed'));
    document.querySelectorAll('.ih-edge').forEach(e => e.classList.remove('highlighted'));
    const connected = new Set([node.id]);
    edges.forEach((e, idx) => {
      if (e.source === node || e.target === node) {
        const line = document.querySelector('[data-edge-idx="' + idx + '"]');
        if (line) line.classList.add('highlighted');
        connected.add(e.source.id);
        connected.add(e.target.id);
      }
    });
    document.querySelectorAll('.ih-node').forEach(g => {
      const firmName = g.getAttribute('data-firm');
      const node = [...document.querySelectorAll('.ih-node')].find(n => n.getAttribute('data-firm') === firmName);
      // Determine if this node is connected
      const idMatch = [...document.querySelectorAll('.ih-node')].indexOf(node);
      if (connected.has(idMatch)) g.classList.remove('dimmed');
    });
  }

  function unhighlight() {
    document.querySelectorAll('.ih-node').forEach(g => g.classList.remove('dimmed'));
    document.querySelectorAll('.ih-edge').forEach(e => e.classList.remove('highlighted'));
  }

  // Tiny custom force simulation (avoids the D3 dependency for initial paint)
  function runForceSimulation(nodes, edges, W, H) {
    const iterations = 200;
    const k = 50; // ideal edge length
    const repulsion = 8000;
    const damping = 0.85;
    const cx = W / 2, cy = H / 2;
    for (let it = 0; it < iterations; it++) {
      // Repulsion between all node pairs
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
          const force = repulsion / (dist * dist);
          nodes[i].vx -= (dx / dist) * force;
          nodes[i].vy -= (dy / dist) * force;
          nodes[j].vx += (dx / dist) * force;
          nodes[j].vy += (dy / dist) * force;
        }
      }
      // Spring along edges
      edges.forEach(e => {
        const dx = e.target.x - e.source.x;
        const dy = e.target.y - e.source.y;
        const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        const idealLen = k + (1 / Math.sqrt(e.weight)) * 30;
        const force = (dist - idealLen) * 0.05 * Math.log(1 + e.weight);
        e.source.vx += (dx / dist) * force;
        e.source.vy += (dy / dist) * force;
        e.target.vx -= (dx / dist) * force;
        e.target.vy -= (dy / dist) * force;
      });
      // Center pull
      nodes.forEach(n => {
        n.vx += (cx - n.x) * 0.001;
        n.vy += (cy - n.y) * 0.001;
      });
      // Update positions with damping
      nodes.forEach(n => {
        n.vx *= damping; n.vy *= damping;
        n.x += n.vx; n.y += n.vy;
        // Clamp to viewport
        n.x = Math.max(40, Math.min(W - 40, n.x));
        n.y = Math.max(40, Math.min(H - 40, n.y));
      });
    }
  }

  // ═══ SECTION 4: Investor Directory ═══
  function renderInvestorDirectory() {
    const body = document.getElementById('ih-firms-body');
    const meta = document.getElementById('ih-firms-meta');
    const stat = document.getElementById('ih-stat-firms');
    if (!body) return;
    const firms = G('VC_FIRMS');
    if (stat) stat.textContent = (firms || []).length;
    if (!Array.isArray(firms) || firms.length === 0) {
      body.innerHTML = '<div class="ih-empty">VC_FIRMS data unavailable.</div>';
      return;
    }
    if (meta) meta.textContent = firms.length + ' firms · click for deep page';
    // Sort by AUM descending where parseable
    const aumNum = s => {
      if (!s) return 0;
      const m = String(s).match(/[\d.]+/);
      if (!m) return 0;
      const n = parseFloat(m[0]);
      if (/B|billion/i.test(s)) return n * 1000;
      return n;
    };
    const sorted = [...firms].sort((a, b) => aumNum(b.aum) - aumNum(a.aum));

    body.innerHTML = '<div class="ih-firm-grid">' +
      sorted.map(f => {
        const portfolioCnt = Array.isArray(f.portfolioCompanies) ? f.portfolioCompanies.length : 0;
        return '<a class="ih-firm-card" href="investor-firm.html?firm=' + encodeURIComponent(f.name) + '">' +
          '<div class="ih-firm-name">' + esc(f.shortName || f.name) + '</div>' +
          (f.aum ? '<div class="ih-firm-aum">' + esc(f.aum) + (f.founded ? ' · est. ' + f.founded : '') + '</div>' : '') +
          (f.thesis ? '<div class="ih-firm-thesis">' + esc(f.thesis) + '</div>' : '') +
          (portfolioCnt ? '<div class="ih-firm-portfolio-cnt">' + portfolioCnt + ' tracked portfolio companies</div>' : '') +
        '</a>';
      }).join('') +
    '</div>';
  }

  function init() {
    try { renderActiveRaises(); } catch (e) { console.error('[hub] Active Raises:', e); }
    try { renderPulseFeed('all'); wirePulseFilters(); } catch (e) { console.error('[hub] Pulse:', e); }
    try { renderCoInvestorGraph(); } catch (e) { console.error('[hub] Graph:', e); }
    try { renderInvestorDirectory(); } catch (e) { console.error('[hub] Directory:', e); }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
