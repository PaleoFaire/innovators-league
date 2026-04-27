/* ─── Earnings Signals Page ───
 * Fetches data/earnings_signals_auto.json and renders:
 *   1. Summary stats strip
 *   2. Filter bar (search + 4 selects + reset)
 *   3. Signal card grid (sorted: high-sig first, then by date desc)
 *
 * Every signal quote is verbatim from an earnings transcript or IR release,
 * and every source_url is clickable.
 */

(function () {
  'use strict';

  const esc = (typeof escapeHtml === 'function')
    ? escapeHtml
    : (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[c]));

  // ─── Taxonomy maps ────────────────────────────────────────────────
  const VERTICAL_LABELS = {
    fusion:             { label: 'Fusion',             color: '#f97316' },
    quantum:            { label: 'Quantum',            color: '#8b5cf6' },
    hypersonics:        { label: 'Hypersonics',        color: '#ef4444' },
    autonomy:           { label: 'Autonomy',           color: '#06b6d4' },
    humanoid:           { label: 'Humanoid',           color: '#14b8a6' },
    space:              { label: 'Space',              color: '#60a5fa' },
    biotech:            { label: 'Biotech',            color: '#f472b6' },
    advanced_materials: { label: 'Adv. Materials',     color: '#c084fc' },
    nuclear:            { label: 'Nuclear',            color: '#eab308' },
    ai_compute:         { label: 'AI Compute',         color: '#a78bfa' },
    defense:            { label: 'Defense',            color: '#f59e0b' },
  };

  const TYPE_LABELS = {
    rd_investment:     { label: 'R&D Investment',     color: '#22c55e' },
    partnership:       { label: 'Partnership',        color: '#60a5fa' },
    competitive_threat:{ label: 'Competitive Threat', color: '#ef4444' },
    supply_chain:      { label: 'Supply Chain',       color: '#f59e0b' },
    capital_shift:     { label: 'Capital Shift',      color: '#8b5cf6' },
    forward_guidance:  { label: 'Forward Guidance',   color: '#06b6d4' },
  };

  const SIGNIFICANCE_LABELS = {
    high:   { label: 'High',   color: '#22c55e', bg: 'rgba(34,197,94,0.15)' },
    medium: { label: 'Medium', color: '#60a5fa', bg: 'rgba(96,165,250,0.15)' },
    low:    { label: 'Low',    color: 'rgba(255,255,255,0.5)', bg: 'rgba(255,255,255,0.05)' },
  };

  function verticalStyle(v) {
    return VERTICAL_LABELS[v] || { label: v || '—', color: 'rgba(255,255,255,0.5)' };
  }
  function typeStyle(t) {
    return TYPE_LABELS[t] || { label: t || '—', color: 'rgba(255,255,255,0.5)' };
  }
  function sigStyle(s) {
    return SIGNIFICANCE_LABELS[s] || SIGNIFICANCE_LABELS.low;
  }

  // ─── State ────────────────────────────────────────────────────────
  let ALL_SIGNALS = [];
  const filters = {
    q: '',
    vertical: '',
    type: '',
    significance: '',
    quarter: '',
  };

  // ─── Rendering ────────────────────────────────────────────────────
  function renderSummary(signals) {
    const el = document.getElementById('es-summary-stats');
    if (!el) return;

    const total = signals.length;
    const quarters = new Set(signals.map(s => s.quarter).filter(Boolean));
    const latest = [...quarters].sort().reverse()[0] || '';
    const thisQuarter = signals.filter(s => s.quarter === latest).length;
    const high = signals.filter(s => s.significance === 'high').length;
    const incumbents = new Set(signals.map(s => s.ticker).filter(Boolean)).size;

    el.innerHTML = `
      <div class="es-stat-block"><div class="es-stat-block-num">${total.toLocaleString()}</div><div class="es-stat-block-lbl">Total signals tracked</div></div>
      <div class="es-stat-block"><div class="es-stat-block-num">${thisQuarter.toLocaleString()}</div><div class="es-stat-block-lbl">Signals this quarter ${latest ? '(' + esc(latest) + ')' : ''}</div></div>
      <div class="es-stat-block"><div class="es-stat-block-num" style="color:#22c55e;">${high.toLocaleString()}</div><div class="es-stat-block-lbl">High-significance</div></div>
      <div class="es-stat-block"><div class="es-stat-block-num">${incumbents.toLocaleString()}</div><div class="es-stat-block-lbl">Incumbents covered</div></div>
    `;
  }

  function populateQuarterFilter(signals) {
    const sel = document.getElementById('es-filter-quarter');
    if (!sel) return;
    const quarters = [...new Set(signals.map(s => s.quarter).filter(Boolean))].sort().reverse();
    // Keep the default "All quarters" option, append
    quarters.forEach(q => {
      const opt = document.createElement('option');
      opt.value = q;
      opt.textContent = q;
      sel.appendChild(opt);
    });
  }

  function companyHref(name) {
    if (!name) return '#';
    return 'company.html?c=' + encodeURIComponent(name);
  }

  function formatDate(d) {
    if (!d) return '';
    // YYYY-MM-DD → Mon DD, YYYY
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(d);
    if (!m) return d;
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const y = m[1], mo = parseInt(m[2], 10), day = parseInt(m[3], 10);
    return `${months[mo - 1]} ${day}, ${y}`;
  }

  function renderCard(s) {
    const v = verticalStyle(s.target_vertical);
    const t = typeStyle(s.signal_type);
    const sg = sigStyle(s.significance);
    const sentimentClass = s.sentiment === 'bullish' ? 'es-sig-bullish'
                         : s.sentiment === 'bearish' ? 'es-sig-bearish'
                         : 'es-sig-neutral';
    const sentimentLabel = s.sentiment ? s.sentiment.charAt(0).toUpperCase() + s.sentiment.slice(1) : '—';

    const mentionsHtml = (s.frontier_companies_mentioned || []).length > 0
      ? `<div class="es-mentions">
           <span class="es-mentions-label">Mentions:</span>
           ${(s.frontier_companies_mentioned).map(n =>
              `<a class="es-mention-chip" href="${esc(companyHref(n))}">${esc(n)}</a>`
           ).join('')}
         </div>` : '';

    const implications = Array.isArray(s.implications) ? s.implications : [];
    const implHtml = implications.length
      ? `<div class="es-implications">
           <div class="es-implications-title">Implications</div>
           <ul class="es-impl-list">
             ${implications.map(i => `<li>${esc(i)}</li>`).join('')}
           </ul>
         </div>` : '';

    const sigClass = s.significance === 'high' ? 'sig-high'
                   : s.significance === 'medium' ? 'sig-medium' : 'sig-low';

    return `<article class="es-card ${sigClass}">
      <div class="es-card-head">
        <div class="es-incumbent">
          <h3 class="es-incumbent-name">${esc(s.incumbent || 'Unknown company')}</h3>
          ${s.ticker ? `<span class="es-ticker">${esc(s.ticker)}</span>` : ''}
        </div>
        <div class="es-quarter-date">
          ${s.quarter ? `<strong>${esc(s.quarter)}</strong>` : ''}
          ${s.date ? esc(formatDate(s.date)) : ''}
        </div>
      </div>

      <div class="es-badges">
        <span class="es-badge" style="color:${t.color}; background:${t.color}15; border:1px solid ${t.color}44;">${esc(t.label)}</span>
        <span class="es-badge" style="color:${v.color}; background:${v.color}15; border:1px solid ${v.color}44;">${esc(v.label)}</span>
        <span class="es-badge ${sentimentClass}">${esc(sentimentLabel)}</span>
      </div>

      <blockquote class="es-quote">${esc(s.quote || '')}</blockquote>

      ${implHtml}

      ${mentionsHtml}

      <div class="es-card-foot">
        <a class="es-transcript-link" href="${esc(s.source_url || '#')}" target="_blank" rel="noopener">Read transcript &rarr;</a>
        <span class="es-significance-chip" style="color:${sg.color}; background:${sg.bg};">${esc(sg.label)} significance</span>
      </div>
    </article>`;
  }

  function renderGrid(signals) {
    const grid = document.getElementById('es-signals-grid');
    const empty = document.getElementById('es-empty-state');
    const count = document.getElementById('es-result-count');
    const note  = document.getElementById('es-loading-note');
    if (!grid) return;

    if (note) note.style.display = 'none';

    if (!signals.length) {
      grid.innerHTML = '';
      if (empty) empty.style.display = 'block';
      if (count) count.textContent = '';
      return;
    }

    if (empty) empty.style.display = 'none';

    // Sort: high sig first, then by date desc
    const sigOrder = { high: 0, medium: 1, low: 2 };
    const sorted = [...signals].sort((a, b) => {
      const sa = sigOrder[a.significance] ?? 3;
      const sb = sigOrder[b.significance] ?? 3;
      if (sa !== sb) return sa - sb;
      return (b.date || '').localeCompare(a.date || '');
    });

    grid.innerHTML = sorted.map(renderCard).join('');

    if (count) {
      count.textContent = `Showing ${signals.length} of ${ALL_SIGNALS.length} signals`;
    }
  }

  // ─── Filtering ────────────────────────────────────────────────────
  function applyFilters() {
    const q = (filters.q || '').toLowerCase().trim();
    const filtered = ALL_SIGNALS.filter(s => {
      if (filters.vertical && s.target_vertical !== filters.vertical) return false;
      if (filters.type && s.signal_type !== filters.type) return false;
      if (filters.significance && s.significance !== filters.significance) return false;
      if (filters.quarter && s.quarter !== filters.quarter) return false;
      if (q) {
        const hay = [
          s.incumbent, s.ticker, s.quote,
          (s.implications || []).join(' '),
          (s.frontier_companies_mentioned || []).join(' '),
          s.target_vertical, s.signal_type,
        ].join(' ').toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    renderGrid(filtered);
  }

  function wireFilters() {
    const search = document.getElementById('es-search');
    const v = document.getElementById('es-filter-vertical');
    const t = document.getElementById('es-filter-type');
    const s = document.getElementById('es-filter-significance');
    const qq = document.getElementById('es-filter-quarter');
    const reset = document.getElementById('es-reset');

    if (search) search.addEventListener('input', (e) => { filters.q = e.target.value; applyFilters(); });
    if (v) v.addEventListener('change', (e) => { filters.vertical = e.target.value; applyFilters(); });
    if (t) t.addEventListener('change', (e) => { filters.type = e.target.value; applyFilters(); });
    if (s) s.addEventListener('change', (e) => { filters.significance = e.target.value; applyFilters(); });
    if (qq) qq.addEventListener('change', (e) => { filters.quarter = e.target.value; applyFilters(); });
    if (reset) {
      reset.addEventListener('click', () => {
        filters.q = filters.vertical = filters.type = filters.significance = filters.quarter = '';
        if (search) search.value = '';
        if (v) v.value = '';
        if (t) t.value = '';
        if (s) s.value = '';
        if (qq) qq.value = '';
        applyFilters();
      });
    }
  }

  // ─── Bootstrap ────────────────────────────────────────────────────
  function bootstrap() {
    const dataPath = 'data/earnings_signals_auto.json?v=' + (new Date().toISOString().slice(0, 10));
    fetch(dataPath)
      .then(r => r.ok ? r.json() : Promise.reject('fetch failed'))
      .then(payload => {
        const signals = Array.isArray(payload) ? payload
                      : (payload && Array.isArray(payload.signals)) ? payload.signals
                      : [];
        ALL_SIGNALS = signals;
        renderSummary(signals);
        populateQuarterFilter(signals);
        renderGrid(signals);
        wireFilters();
      })
      .catch((err) => {
        console.warn('[earnings-signals] fetch failed:', err);
        const note = document.getElementById('es-loading-note');
        if (note) {
          note.innerHTML = '<strong>Data pipeline in progress.</strong> Earnings signals will appear after the next sync cycle.';
        }
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }

  // Expose for reuse by company.html "Incumbent Signals" section
  window.ROS_EARNINGS_SIGNALS = {
    fetchSignals: async function () {
      try {
        const r = await fetch('data/earnings_signals_auto.json?v=' + (new Date().toISOString().slice(0, 10)));
        if (!r.ok) return [];
        const p = await r.json();
        return Array.isArray(p) ? p : (p && Array.isArray(p.signals)) ? p.signals : [];
      } catch (e) { return []; }
    },
    // Find signals where a given company name appears in frontier_companies_mentioned
    filterByMention: function (signals, companyName) {
      if (!companyName) return [];
      const target = String(companyName).toLowerCase().trim();
      return (signals || []).filter(s =>
        (s.frontier_companies_mentioned || [])
          .some(n => String(n).toLowerCase().includes(target) || target.includes(String(n).toLowerCase()))
      );
    },
    verticalStyle: verticalStyle,
    typeStyle: typeStyle,
    formatDate: formatDate,
  };
})();
