/**
 * Power Grid Intelligence — UI controller
 *
 * Reads window.INTERCONNECTION_QUEUE_AUTO (populated by
 * data/interconnection_queue_auto.js) and renders:
 *   - Top-of-page stat tiles
 *   - Filterable queue table (All / SMR / AI / Matched)
 *   - Breakdown bars by RTO and by fuel type
 *
 * Gracefully handles: missing data file, empty queue, unknown fields.
 */

(function () {
  'use strict';

  const DATA = (typeof window.INTERCONNECTION_QUEUE_AUTO !== 'undefined')
    ? window.INTERCONNECTION_QUEUE_AUTO
    : null;

  // Utility: escape HTML to prevent XSS from any field contents.
  function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Utility: format MW value
  function fmtMw(n) {
    if (typeof n !== 'number') return '—';
    if (n >= 1000) return (n / 1000).toFixed(1) + ' GW';
    return n.toLocaleString() + ' MW';
  }

  // Utility: format a date-like string
  function fmtDate(s) {
    if (!s) return '—';
    const str = String(s);
    // YYYY-MM or YYYY-MM-DD → "Mon YYYY"
    const m = str.match(/^(\d{4})-(\d{2})/);
    if (m) {
      const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      return months[parseInt(m[2], 10) - 1] + ' ' + m[1];
    }
    return str;
  }

  function renderEmpty(msg) {
    const tbody = document.getElementById('pg-queue-body');
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="7" class="pg-empty">' + esc(msg) + '</td></tr>';
    }
  }

  function renderStats(summary, srcStatus, generatedAt) {
    const s = summary || {};
    const set = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    set('pg-stat-total', s.total_entries || 0);
    set('pg-stat-mw', (s.total_mw || 0).toLocaleString());
    set('pg-stat-ai', s.ai_buyer_entries || 0);
    set('pg-stat-smr', s.smr_entries || 0);
    set('pg-stat-matched', s.matched_to_tracked_company || 0);

    // Source + updated
    const sourceLbl = srcStatus === 'live' ? 'Interconnection.fyi (live)'
      : srcStatus === 'live_pending' ? 'Interconnection.fyi (live pipeline pending)'
      : 'Curated queue entries';
    set('pg-source-label', sourceLbl);

    if (generatedAt) {
      try {
        const d = new Date(generatedAt);
        set('pg-updated', d.toLocaleDateString('en-US', {
          month: 'short', day: 'numeric', year: 'numeric',
        }));
      } catch (_) {
        set('pg-updated', 'recently');
      }
    }
  }

  function priorityClass(e) {
    if (e.is_smr) return 'smr';
    if (e.is_ai_buyer) return 'ai';
    if ((e.mw_size || 0) >= 500) return 'large';
    return 'standard';
  }

  function rowClass(e) {
    if (e.is_smr) return 'smr';
    if (e.matched_company) return 'matched';
    return '';
  }

  function renderQueue(entries, filter) {
    const tbody = document.getElementById('pg-queue-body');
    if (!tbody) return;
    if (!entries || entries.length === 0) {
      renderEmpty('No queue entries in this view.');
      return;
    }

    const shown = entries.filter(e => {
      if (filter === 'smr') return e.is_smr;
      if (filter === 'ai') return e.is_ai_buyer;
      if (filter === 'matched') return !!e.matched_company;
      return true;
    });

    if (shown.length === 0) {
      renderEmpty('No entries match this filter.');
      return;
    }

    const html = shown.map(e => {
      const cls = rowClass(e);
      const prio = priorityClass(e);
      const prioLabel = esc(e.priority_label || 'Standard');
      const matchHtml = e.matched_company
        ? '<br><span class="pg-match-tag">✓ ' + esc(e.matched_company) + '</span>'
        : '';
      return (
        '<tr class="' + cls + '">' +
          '<td><span class="pg-customer">' + esc(e.customer || 'Unknown') + '</span>' +
             '<span class="pg-project">' + esc(e.project_name || '') + '</span>' +
             matchHtml +
          '</td>' +
          '<td><span class="pg-rto-pill">' + esc(e.rto || '—') + '</span></td>' +
          '<td><span class="pg-mw">' + fmtMw(e.mw_size) + '</span></td>' +
          '<td>' + esc(e.fuel_type || '—') + '</td>' +
          '<td>' + esc((e.county ? (e.county + ', ') : '') + (e.state || '—')) + '</td>' +
          '<td>' + esc(fmtDate(e.proposed_online_date)) + '</td>' +
          '<td><span class="pg-priority-pill ' + prio + '">' + prioLabel + '</span></td>' +
        '</tr>'
      );
    }).join('');

    tbody.innerHTML = html;
  }

  function renderBars(containerId, kv) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const items = Object.entries(kv || {})
      .sort((a, b) => b[1] - a[1]);
    if (items.length === 0) {
      container.innerHTML = '<p style="color:rgba(255,255,255,0.4); font-size:13px;">No data.</p>';
      return;
    }
    const max = items[0][1];
    const html = items.map(([k, v]) => {
      const pct = max > 0 ? (100 * v / max) : 0;
      return (
        '<div class="pg-bar-row">' +
          '<div class="pg-bar-lbl">' + esc(k) + '</div>' +
          '<div class="pg-bar-track"><div class="pg-bar-fill" style="width:' + pct.toFixed(1) + '%"></div></div>' +
          '<div class="pg-bar-val">' + fmtMw(v) + '</div>' +
        '</div>'
      );
    }).join('');
    container.innerHTML = html;
  }

  function wireFilters(entries) {
    document.querySelectorAll('.pg-filter-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.pg-filter-chip').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        window._pgStateFilter = null;
        document.getElementById('pg-state-filter-info').classList.remove('active');
        renderQueue(entries, btn.getAttribute('data-filter'));
      });
    });
  }

  // ── US MAP ────────────────────────────────────────────────────────────────

  // Pre-computed state center coordinates, projected into a 960×600 viewport
  // roughly matching Albers USA. Covers all 50 states + DC. AK/HI are
  // placed in the lower-left corner (inset) following D3 convention.
  const STATE_CENTERS = {
    AL: { x: 645, y: 435, name: 'Alabama' },
    AK: { x: 160, y: 525, name: 'Alaska' },
    AZ: { x: 230, y: 405, name: 'Arizona' },
    AR: { x: 540, y: 405, name: 'Arkansas' },
    CA: { x:  85, y: 305, name: 'California' },
    CO: { x: 335, y: 310, name: 'Colorado' },
    CT: { x: 825, y: 235, name: 'Connecticut' },
    DE: { x: 790, y: 290, name: 'Delaware' },
    DC: { x: 770, y: 300, name: 'D.C.' },
    FL: { x: 720, y: 500, name: 'Florida' },
    GA: { x: 690, y: 430, name: 'Georgia' },
    HI: { x: 260, y: 540, name: 'Hawaii' },
    ID: { x: 220, y: 190, name: 'Idaho' },
    IL: { x: 565, y: 275, name: 'Illinois' },
    IN: { x: 610, y: 285, name: 'Indiana' },
    IA: { x: 510, y: 245, name: 'Iowa' },
    KS: { x: 450, y: 320, name: 'Kansas' },
    KY: { x: 635, y: 330, name: 'Kentucky' },
    LA: { x: 560, y: 470, name: 'Louisiana' },
    ME: { x: 855, y: 145, name: 'Maine' },
    MD: { x: 760, y: 295, name: 'Maryland' },
    MA: { x: 830, y: 210, name: 'Massachusetts' },
    MI: { x: 620, y: 200, name: 'Michigan' },
    MN: { x: 490, y: 165, name: 'Minnesota' },
    MS: { x: 590, y: 430, name: 'Mississippi' },
    MO: { x: 530, y: 320, name: 'Missouri' },
    MT: { x: 295, y: 140, name: 'Montana' },
    NE: { x: 425, y: 250, name: 'Nebraska' },
    NV: { x: 170, y: 260, name: 'Nevada' },
    NH: { x: 830, y: 180, name: 'New Hampshire' },
    NJ: { x: 790, y: 260, name: 'New Jersey' },
    NM: { x: 310, y: 380, name: 'New Mexico' },
    NY: { x: 775, y: 195, name: 'New York' },
    NC: { x: 730, y: 355, name: 'North Carolina' },
    ND: { x: 395, y: 130, name: 'North Dakota' },
    OH: { x: 665, y: 265, name: 'Ohio' },
    OK: { x: 470, y: 385, name: 'Oklahoma' },
    OR: { x: 140, y: 175, name: 'Oregon' },
    PA: { x: 735, y: 245, name: 'Pennsylvania' },
    RI: { x: 833, y: 220, name: 'Rhode Island' },
    SC: { x: 720, y: 400, name: 'South Carolina' },
    SD: { x: 405, y: 195, name: 'South Dakota' },
    TN: { x: 630, y: 365, name: 'Tennessee' },
    TX: { x: 450, y: 460, name: 'Texas' },
    UT: { x: 240, y: 275, name: 'Utah' },
    VT: { x: 810, y: 175, name: 'Vermont' },
    VA: { x: 740, y: 315, name: 'Virginia' },
    WA: { x: 170, y: 100, name: 'Washington' },
    WV: { x: 700, y: 300, name: 'West Virginia' },
    WI: { x: 555, y: 190, name: 'Wisconsin' },
    WY: { x: 320, y: 215, name: 'Wyoming' },
  };

  // Dominant-priority color for a state based on its entries
  function stateColor(entries) {
    if (entries.some(e => e.is_smr)) return '#fbbf24';     // amber (SMR)
    if (entries.some(e => e.is_ai_buyer)) return '#60a5fa'; // blue (AI)
    if (entries.some(e => (e.mw_size || 0) >= 500)) return '#86efac'; // green
    return 'rgba(255,255,255,0.55)';
  }

  function aggregateByState(entries) {
    const agg = {};
    entries.forEach(e => {
      const st = (e.state || '').toUpperCase().trim();
      if (!st || !STATE_CENTERS[st]) return;
      if (!agg[st]) agg[st] = { entries: [], total_mw: 0 };
      agg[st].entries.push(e);
      agg[st].total_mw += e.mw_size || 0;
    });
    return agg;
  }

  // Radius scaling: log scale so a 2000 MW site isn't 40x bigger than a 75 MW SMR.
  function mwToRadius(mw) {
    if (mw <= 0) return 4;
    const r = 5 + Math.log10(mw / 10 + 1) * 9;
    return Math.max(5, Math.min(r, 38));
  }

  function renderMap(entries) {
    const bubblesG = document.getElementById('pg-map-bubbles');
    const labelsG = document.getElementById('pg-map-labels');
    const svgEl = document.getElementById('pg-map-svg');
    const tooltip = document.getElementById('pg-map-tooltip');
    if (!bubblesG || !labelsG || !svgEl) return;

    const agg = aggregateByState(entries);
    const states = Object.entries(agg)
      .map(([st, v]) => ({ state: st, ...v }))
      .sort((a, b) => b.total_mw - a.total_mw);

    const ns = 'http://www.w3.org/2000/svg';
    // Clear
    bubblesG.innerHTML = '';
    labelsG.innerHTML = '';

    states.forEach(s => {
      const c = STATE_CENTERS[s.state];
      const r = mwToRadius(s.total_mw);
      const col = stateColor(s.entries);

      // Outer halo circle (soft)
      const outer = document.createElementNS(ns, 'circle');
      outer.setAttribute('cx', c.x);
      outer.setAttribute('cy', c.y);
      outer.setAttribute('r', r + 6);
      outer.setAttribute('class', 'pg-map-bubble pg-map-bubble-outer');
      outer.setAttribute('fill', col);
      outer.setAttribute('stroke', col);
      bubblesG.appendChild(outer);

      // Inner solid circle
      const inner = document.createElementNS(ns, 'circle');
      inner.setAttribute('cx', c.x);
      inner.setAttribute('cy', c.y);
      inner.setAttribute('r', r);
      inner.setAttribute('class', 'pg-map-bubble pg-map-bubble-inner');
      inner.setAttribute('fill', col);
      inner.setAttribute('data-state', s.state);
      inner.style.cursor = 'pointer';
      inner.style.pointerEvents = 'auto';
      bubblesG.appendChild(inner);

      // State label
      const lbl = document.createElementNS(ns, 'text');
      lbl.setAttribute('x', c.x);
      lbl.setAttribute('y', c.y + 3);
      lbl.setAttribute('class', 'pg-map-label');
      lbl.textContent = s.state;
      labelsG.appendChild(lbl);

      // MW label below
      const mwLbl = document.createElementNS(ns, 'text');
      mwLbl.setAttribute('x', c.x);
      mwLbl.setAttribute('y', c.y + r + 14);
      mwLbl.setAttribute('class', 'pg-map-mw');
      mwLbl.textContent = fmtMw(s.total_mw);
      labelsG.appendChild(mwLbl);

      // Interaction handlers on inner
      inner.addEventListener('mouseenter', (evt) => {
        const rect = svgEl.getBoundingClientRect();
        const wrapRect = svgEl.parentElement.getBoundingClientRect();
        // Place tooltip near the bubble center, within the wrap
        const cx = rect.left + (c.x / 960) * rect.width - wrapRect.left + 20;
        const cy = rect.top + (c.y / 600) * rect.height - wrapRect.top - 10;
        tooltip.style.left = Math.max(10, Math.min(cx, wrapRect.width - 320)) + 'px';
        tooltip.style.top = Math.max(10, cy) + 'px';
        tooltip.innerHTML =
          '<div class="pg-tooltip-state">' + esc(c.name) + ' (' + esc(s.state) + ')</div>' +
          '<div class="pg-tooltip-stats">' + s.entries.length + ' project' + (s.entries.length !== 1 ? 's' : '') + ' · ' + esc(fmtMw(s.total_mw)) + '</div>' +
          s.entries.map(e =>
            '<div class="pg-tooltip-project"><strong>' + esc(e.customer) + '</strong><br><span style="color:rgba(255,255,255,0.55);">' + esc(e.project_name || '') + ' · ' + esc(fmtMw(e.mw_size)) + '</span></div>'
          ).join('');
        tooltip.classList.add('active');
      });
      inner.addEventListener('mouseleave', () => {
        tooltip.classList.remove('active');
      });
      inner.addEventListener('click', () => {
        applyStateFilter(s.state, c.name);
      });
    });
  }

  function applyStateFilter(stateCode, stateName) {
    const allEntries = (DATA && DATA.entries) || [];
    const filtered = allEntries.filter(e => (e.state || '').toUpperCase() === stateCode);
    window._pgStateFilter = stateCode;
    // Visual active filter chip: reset all chips
    document.querySelectorAll('.pg-filter-chip').forEach(b => b.classList.remove('active'));
    // Render filtered entries directly (by bypassing the filter function)
    const tbody = document.getElementById('pg-queue-body');
    if (!tbody) return;
    if (filtered.length === 0) {
      renderEmpty('No queue entries in ' + stateName + '.');
    } else {
      const html = filtered.map(e => {
        const cls = rowClass(e);
        const prio = priorityClass(e);
        const matchHtml = e.matched_company
          ? '<br><span class="pg-match-tag">✓ ' + esc(e.matched_company) + '</span>'
          : '';
        return (
          '<tr class="' + cls + '">' +
            '<td><span class="pg-customer">' + esc(e.customer || 'Unknown') + '</span>' +
               '<span class="pg-project">' + esc(e.project_name || '') + '</span>' +
               matchHtml +
            '</td>' +
            '<td><span class="pg-rto-pill">' + esc(e.rto || '—') + '</span></td>' +
            '<td><span class="pg-mw">' + fmtMw(e.mw_size) + '</span></td>' +
            '<td>' + esc(e.fuel_type || '—') + '</td>' +
            '<td>' + esc((e.county ? (e.county + ', ') : '') + (e.state || '—')) + '</td>' +
            '<td>' + esc(fmtDate(e.proposed_online_date)) + '</td>' +
            '<td><span class="pg-priority-pill ' + prio + '">' + esc(e.priority_label || 'Standard') + '</span></td>' +
          '</tr>'
        );
      }).join('');
      tbody.innerHTML = html;
    }
    // Filter info banner
    const info = document.getElementById('pg-state-filter-info');
    const nameSpan = document.getElementById('pg-state-filter-name');
    if (info && nameSpan) {
      nameSpan.textContent = stateName + ' (' + stateCode + ') — ' + filtered.length + ' project' + (filtered.length !== 1 ? 's' : '');
      info.classList.add('active');
    }
    // Scroll to table
    const tbl = document.querySelector('.pg-queue-wrap');
    if (tbl) tbl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  window.pgClearStateFilter = function () {
    window._pgStateFilter = null;
    document.getElementById('pg-state-filter-info').classList.remove('active');
    // Reset to "All"
    const allChip = document.querySelector('.pg-filter-chip[data-filter="all"]');
    if (allChip) {
      document.querySelectorAll('.pg-filter-chip').forEach(b => b.classList.remove('active'));
      allChip.classList.add('active');
    }
    renderQueue((DATA && DATA.entries) || [], 'all');
  };

  function init() {
    if (!DATA) {
      renderEmpty('Queue data not yet loaded. Run scripts/fetch_interconnection_queue.py to populate.');
      return;
    }
    const entries = Array.isArray(DATA.entries) ? DATA.entries : [];
    renderStats(DATA.summary, DATA.source_status, DATA.generated_at);
    renderMap(entries);
    renderQueue(entries, 'all');
    renderBars('pg-by-rto', (DATA.summary || {}).by_rto_mw || {});
    renderBars('pg-by-fuel', (DATA.summary || {}).by_fuel_mw || {});
    wireFilters(entries);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
