/* Catalyst Calendar — single page logic.
 * Reads the unified feed (data/catalyst_calendar.json) and renders into
 * the timeline + filters defined in catalysts.html.
 */
(function () {
  'use strict';

  const FEED_URL = 'data/catalyst_calendar.json?v=' + Date.now();

  // Friendly labels for type codes
  const TYPE_LABELS = {
    fda:      { label: '🧬 FDA',         color: 'bio' },
    trial:    { label: '🧪 Clinical',    color: 'bio' },
    faa:      { label: '✈️ FAA',         color: 'space' },
    nrc:      { label: '⚛️ NRC',         color: 'nuclear' },
    fcc:      { label: '📡 FCC',         color: 'space' },
    formd:    { label: '💵 Form D',      color: 'success' },
    sbir:     { label: '🎖 SBIR',        color: 'defense' },
    earnings: { label: '📈 Earnings',    color: 'info' },
    conf:     { label: '🎤 Conference',  color: 'neutral' },
    launch:   { label: '🚀 Launch',      color: 'space' },
    funding:  { label: '💰 Funding',     color: 'success' },
    factory:  { label: '🛰 Factory',     color: 'defense' },
    news:     { label: '📰 News',        color: 'neutral' },
    water:    { label: '💧 EPA',         color: 'energy' },
  };

  // State
  const state = {
    feed: null,
    activeTypes: new Set(),  // empty set = all types
    sector: '',
    window: '30',
    search: '',
  };

  // ── Data load ─────────────────────────────────────────────────────────
  async function loadFeed() {
    try {
      const r = await fetch(FEED_URL, { cache: 'no-store' });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (err) {
      console.error('Catalyst calendar feed load failed:', err);
      return null;
    }
  }

  // ── Filtering ─────────────────────────────────────────────────────────
  function filterEvents(events) {
    const now = state.window;
    return events.filter((e) => {
      // Type filter (chip set; empty = all)
      if (state.activeTypes.size > 0 && !state.activeTypes.has(e.type)) return false;
      // Sector
      if (state.sector && e.sector !== state.sector) return false;
      // Window
      if (now !== 'all') {
        const n = parseInt(now, 10);
        const d = e.daysOut == null ? -9999 : e.daysOut;
        if (n >= 0) {
          if (d < 0 || d > n) return false;
        } else {
          if (d > 0 || d < n) return false;
        }
      }
      // Search
      if (state.search) {
        const q = state.search.toLowerCase();
        const blob = (e.title + ' ' + (e.description || '') + ' ' + (e.companies || []).join(' ')).toLowerCase();
        if (!blob.includes(q)) return false;
      }
      return true;
    });
  }

  // ── Rendering ─────────────────────────────────────────────────────────
  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function dayLabel(daysOut) {
    if (daysOut == null) return '';
    if (daysOut === 0) return 'today';
    if (daysOut === 1) return 'tomorrow';
    if (daysOut === -1) return 'yesterday';
    if (daysOut > 0) return `in ${daysOut} days`;
    return `${Math.abs(daysOut)} days ago`;
  }

  function badgeForImportance(imp) {
    const map = {
      urgent:  '<span class="il-badge il-badge--danger">Urgent</span>',
      high:    '<span class="il-badge il-badge--accent">High</span>',
      medium:  '<span class="il-badge">Medium</span>',
      low:     '<span class="il-badge il-badge--neutral">Low</span>',
    };
    return map[imp] || map.low;
  }

  function badgeForType(type) {
    const meta = TYPE_LABELS[type] || { label: type, color: 'neutral' };
    const cls = {
      bio: 'il-badge', defense: 'il-badge il-badge--accent',
      space: 'il-badge il-badge--info', nuclear: 'il-badge il-badge--warning',
      energy: 'il-badge', quantum: 'il-badge', success: 'il-badge',
      info: 'il-badge il-badge--info', neutral: 'il-badge il-badge--neutral',
    }[meta.color] || 'il-badge il-badge--neutral';
    return `<span class="${cls}">${escapeHtml(meta.label)}</span>`;
  }

  function renderItem(e) {
    const dateStr = e.date + ' · ' + dayLabel(e.daysOut);
    const companies = (e.companies || []).filter(Boolean).slice(0, 3);
    const sectorChip = e.sector && e.sector !== 'other'
      ? `<span class="il-text-uppercase il-text-xs il-text-muted">${escapeHtml(e.sector)}</span>` : '';

    return `
      <article class="il-timeline-item" data-importance="${escapeHtml(e.importance)}">
        <div class="il-timeline-item__date">${escapeHtml(dateStr)}</div>
        <div class="il-timeline-item__title">${escapeHtml(e.title)}</div>
        <div class="il-timeline-item__meta">
          ${badgeForImportance(e.importance)}
          ${badgeForType(e.type)}
          ${companies.map((c) => `<span>${escapeHtml(c)}</span>`).join('<span>·</span>')}
          ${sectorChip}
          ${e.sourceUrl ? `<a href="${escapeHtml(e.sourceUrl)}" target="_blank" rel="noopener" style="margin-left:auto; color:var(--color-primary)">${escapeHtml(e.source)} ↗</a>` : ''}
        </div>
        ${e.description ? `<div class="il-timeline-item__body">${escapeHtml(e.description)}</div>` : ''}
      </article>
    `;
  }

  function render() {
    const feedEl = document.getElementById('cc-feed');
    const emptyEl = document.getElementById('cc-empty');
    const filtered = filterEvents(state.feed.events);

    if (!filtered.length) {
      feedEl.hidden = true;
      emptyEl.style.display = '';
      return;
    }

    emptyEl.style.display = 'none';
    feedEl.hidden = false;
    feedEl.innerHTML = filtered.map(renderItem).join('');
  }

  // ── Setup ─────────────────────────────────────────────────────────────
  function setupChips() {
    const wrap = document.getElementById('type-chips');
    const typeOrder = ['fda', 'trial', 'faa', 'nrc', 'fcc', 'formd', 'sbir', 'earnings', 'conf'];
    const chips = ['<button class="il-chip" aria-pressed="true" data-type="">All</button>']
      .concat(typeOrder.filter((t) => state.feed.byType?.[t]).map((t) => {
        const meta = TYPE_LABELS[t];
        return `<button class="il-chip" aria-pressed="false" data-type="${t}">${escapeHtml(meta?.label || t)}</button>`;
      }));
    wrap.innerHTML = chips.join('');

    wrap.addEventListener('click', (e) => {
      const btn = e.target.closest('.il-chip');
      if (!btn) return;
      const type = btn.dataset.type;
      // "All" chip toggles back to no filter
      if (type === '') {
        state.activeTypes.clear();
        wrap.querySelectorAll('.il-chip').forEach((c) =>
          c.setAttribute('aria-pressed', c.dataset.type === '' ? 'true' : 'false'));
      } else {
        // Toggle this type
        const willActivate = btn.getAttribute('aria-pressed') !== 'true';
        if (willActivate) state.activeTypes.add(type);
        else state.activeTypes.delete(type);
        btn.setAttribute('aria-pressed', willActivate ? 'true' : 'false');
        // Sync "All" chip
        const allChip = wrap.querySelector('.il-chip[data-type=""]');
        allChip.setAttribute('aria-pressed', state.activeTypes.size === 0 ? 'true' : 'false');
      }
      render();
    });
  }

  function setupFilters() {
    document.getElementById('filter-sector').addEventListener('change', (e) => {
      state.sector = e.target.value; render();
    });
    document.getElementById('filter-window').addEventListener('change', (e) => {
      state.window = e.target.value; render();
    });
    let searchTimer;
    document.getElementById('filter-search').addEventListener('input', (e) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => { state.search = e.target.value.trim(); render(); }, 150);
    });
  }

  function setupStats() {
    const ev = state.feed.events;
    const urgent = ev.filter((e) => e.importance === 'urgent').length;
    const high   = ev.filter((e) => e.importance === 'high').length;
    document.getElementById('stat-total').textContent = state.feed.totalEvents;
    document.getElementById('stat-urgent').textContent = urgent;
    document.getElementById('stat-high').textContent   = high;
    document.getElementById('stat-sources').textContent = Object.keys(state.feed.bySource || {}).length;

    document.getElementById('cc-generated-at').textContent =
      new Date(state.feed.generatedAt).toLocaleString();
    document.getElementById('cc-source-list').textContent =
      Object.entries(state.feed.bySource || {})
        .filter(([k, v]) => v > 0)
        .map(([k, v]) => `${k}(${v})`).join(' · ') || '(none)';
  }

  // ── Boot ──────────────────────────────────────────────────────────────
  async function boot() {
    state.feed = await loadFeed();
    if (!state.feed) {
      document.getElementById('cc-loading').innerHTML =
        '<div class="il-card il-card--danger"><div class="il-card__title">Could not load catalyst feed</div>' +
        '<div class="il-card__body">data/catalyst_calendar.json is missing or unreachable. ' +
        'Run <code>python scripts/build_unified_calendar.py</code> to generate it.</div></div>';
      return;
    }
    document.getElementById('cc-loading').remove();
    setupStats();
    setupChips();
    setupFilters();
    render();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
