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
        renderQueue(entries, btn.getAttribute('data-filter'));
      });
    });
  }

  function init() {
    if (!DATA) {
      renderEmpty('Queue data not yet loaded. Run scripts/fetch_interconnection_queue.py to populate.');
      return;
    }
    const entries = Array.isArray(DATA.entries) ? DATA.entries : [];
    renderStats(DATA.summary, DATA.source_status, DATA.generated_at);
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
