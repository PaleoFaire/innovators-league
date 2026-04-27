/* ─── Discovery Queue Review UI ───
 *
 * Reads window.DISCOVERY_QUEUE_AUTO (loaded from data/discovery_queue_auto.js)
 * and renders a card-based triage interface. Stephen's weekly workflow:
 *
 *   1. Open discovery.html
 *   2. See multi-source candidates first (auto-sorted by score)
 *   3. Filter by confidence + source
 *   4. Per-card: click "Add to DB" / "Research" / "Reject"
 *   5. Click "Copy to clipboard" → paste into a triage doc / send to ROS team
 *
 * Decisions persist in localStorage so Stephen can come back next session
 * and see what he's already triaged. Action tray surfaces pending decisions.
 */

(function () {
  'use strict';

  const esc = (typeof escapeHtml === 'function')
    ? escapeHtml
    : (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[c]));

  const STORAGE_KEY = 'ros_discovery_actions_v1';
  const _state = {
    confidenceFilter: { high: true, medium: true, low: false },
    sourceFilter: 'all',
    actions: {},  // { companyName: 'add'|'reject'|'research' }
  };

  function loadActions() {
    try {
      _state.actions = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch (e) {
      _state.actions = {};
    }
  }

  function saveActions() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(_state.actions));
  }

  function setAction(name, action) {
    if (action === 'clear') {
      delete _state.actions[name];
    } else {
      _state.actions[name] = { action, timestamp: new Date().toISOString() };
    }
    saveActions();
    renderTray();
    render();
  }

  function renderStats(d) {
    const wrap = document.getElementById('dq-stats');
    if (!wrap) return;
    const s = d.summary || {};
    wrap.innerHTML =
      `<div class="dq-stat"><div class="dq-stat-num">${d.candidates.length}</div><div class="dq-stat-lbl">Candidates</div></div>` +
      `<div class="dq-stat"><div class="dq-stat-num" style="color:#22c55e;">${s.multiSource || 0}</div><div class="dq-stat-lbl">Multi-Source</div></div>` +
      `<div class="dq-stat"><div class="dq-stat-num">${s.fromVcPortfolios || 0}</div><div class="dq-stat-lbl">VC Portfolio Diffs</div></div>` +
      `<div class="dq-stat"><div class="dq-stat-num">${s.fromFormD || 0}</div><div class="dq-stat-lbl">Form D Filings</div></div>` +
      `<div class="dq-stat"><div class="dq-stat-num">${s.fromNewsletters || 0}</div><div class="dq-stat-lbl">Newsletter Hits</div></div>`;
  }

  function renderCard(c) {
    const conf = c.confidence || 'low';
    const sourceChips = (c.sources || []).map(s => {
      const cls = c.multiSource ? 'is-multi' : '';
      return `<span class="dq-source-chip ${cls}">${esc(s)}</span>`;
    }).join('');

    // Aggregate signals: dedupe by source+url, keep top-rated
    const signalSummary = (c.signals || []).slice(0, 3).map(sig => {
      const url = sig.verifyUrl ? `<a href="${esc(sig.verifyUrl)}" target="_blank" rel="noopener" style="color:#93c5fd; text-decoration:none;">[verify →]</a>` : '';
      const article = sig.articleTitle ? `<span class="dq-signal-context">"${esc(sig.articleTitle.substring(0, 70))}${sig.articleTitle.length > 70 ? '…' : ''}"</span>` : '';
      const ctx = sig.context ? `<span class="dq-signal-context">${esc((sig.context || '').substring(0, 100))}…</span>` : '';
      return `<div class="dq-signal-item">
        <span class="dq-signal-source">${esc(sig.source || 'unknown')}</span>
        ${sig.amountFmt ? '<span style="color:#22c55e; font-weight:600;"> · ' + esc(sig.amountFmt) + '</span>' : ''}
        ${sig.date ? '<span style="color:rgba(255,255,255,0.4); font-size:11px;"> · ' + esc(sig.date) + '</span>' : ''}
        ${url}
        <br>${article || ctx || ''}
      </div>`;
    }).join('');

    const sectorBadge = c.suggestedSector
      ? `<span class="dq-suggested-sector">${esc(c.suggestedSector)}</span>`
      : '';

    const action = (_state.actions[c.name] || {}).action;
    const actionMarker = action ? `<span style="position:absolute; top:8px; right:8px; font-size:10px; padding:2px 7px; border-radius:8px; background:${action === 'add' ? 'rgba(34,197,94,0.18)' : action === 'reject' ? 'rgba(239,68,68,0.15)' : 'rgba(96,165,250,0.18)'}; color:${action === 'add' ? '#22c55e' : action === 'reject' ? '#ef4444' : '#93c5fd'}; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">${action}</span>` : '';

    return `<div class="dq-card dq-confidence-${conf}" data-name="${esc(c.name)}">
      ${actionMarker}
      <div class="dq-card-head">
        <div>
          <div class="dq-card-name">${esc(c.name)}${sectorBadge}</div>
          <div class="dq-card-meta">Score: <strong style="color:#f59e0b;">${c.score}</strong> · ${(c.signals || []).length} signal${(c.signals || []).length !== 1 ? 's' : ''}</div>
        </div>
        <span class="dq-confidence-badge dq-confidence-${conf}">${conf}</span>
      </div>
      <div class="dq-sources-row">${sourceChips}</div>
      <div class="dq-signals-detail">${signalSummary}</div>
      <div class="dq-card-actions">
        <button class="dq-action-btn dq-action-add" data-action="add" data-name="${esc(c.name)}">✓ Add to DB</button>
        <button class="dq-action-btn dq-action-research" data-action="research" data-name="${esc(c.name)}">🔍 Research</button>
        <button class="dq-action-btn dq-action-reject" data-action="reject" data-name="${esc(c.name)}">✗ Reject</button>
      </div>
    </div>`;
  }

  function applyFilters(candidates) {
    return candidates.filter(c => {
      // Confidence filter
      const conf = c.confidence || 'low';
      if (!_state.confidenceFilter[conf]) return false;
      // Source filter
      if (_state.sourceFilter !== 'all') {
        const matchSource = (c.sources || []).some(s => s.startsWith(_state.sourceFilter));
        if (!matchSource) return false;
      }
      return true;
    });
  }

  function render() {
    const data = window.DISCOVERY_QUEUE_AUTO;
    if (!data) return;
    const grid = document.getElementById('dq-grid');
    if (!grid) return;
    const filtered = applyFilters(data.candidates || []);
    if (filtered.length === 0) {
      grid.innerHTML = '<div class="dq-empty">No candidates match the current filters.</div>';
      return;
    }
    grid.innerHTML = filtered.map(renderCard).join('');
    bindCardActions();
  }

  function bindCardActions() {
    document.querySelectorAll('.dq-action-btn[data-action]').forEach(btn => {
      btn.addEventListener('click', () => {
        const name = btn.getAttribute('data-name');
        const action = btn.getAttribute('data-action');
        if (action === 'research') {
          // Open the highest-confidence verifyUrl in a new tab
          const c = (window.DISCOVERY_QUEUE_AUTO.candidates || []).find(x => x.name === name);
          if (c && c.signals) {
            const topUrl = (c.signals.find(s => s.verifyUrl) || {}).verifyUrl;
            if (topUrl) window.open(topUrl, '_blank');
          }
          // Mark as researched too
          setAction(name, 'research');
        } else {
          setAction(name, action);
        }
      });
    });
  }

  function bindFilters() {
    document.querySelectorAll('.dq-filter-btn[data-filter]').forEach(btn => {
      btn.addEventListener('click', () => {
        const filter = btn.getAttribute('data-filter');
        _state.confidenceFilter[filter] = !_state.confidenceFilter[filter];
        btn.classList.toggle('active');
        render();
      });
    });
    document.querySelectorAll('.dq-filter-btn[data-source]').forEach(btn => {
      btn.addEventListener('click', () => {
        const src = btn.getAttribute('data-source');
        document.querySelectorAll('.dq-filter-btn[data-source]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        _state.sourceFilter = src;
        render();
      });
    });
  }

  function renderTray() {
    const tray = document.getElementById('dq-action-tray');
    const list = document.getElementById('dq-action-tray-list');
    const title = document.getElementById('dq-action-tray-title');
    if (!tray || !list || !title) return;
    const entries = Object.entries(_state.actions || {});
    if (entries.length === 0) {
      tray.classList.remove('show');
      return;
    }
    tray.classList.add('show');
    const adds = entries.filter(([_, v]) => v.action === 'add').map(([k, _]) => k);
    const rejs = entries.filter(([_, v]) => v.action === 'reject').map(([k, _]) => k);
    const res = entries.filter(([_, v]) => v.action === 'research').map(([k, _]) => k);
    title.innerHTML = `${adds.length} adds · ${rejs.length} rejects · ${res.length} researched`;
    list.innerHTML = (adds.length ? `<strong style="color:#22c55e;">Add to DB (${adds.length}):</strong> ${adds.map(esc).join(', ')}<br>` : '') +
                     (rejs.length ? `<strong style="color:#ef4444;">Rejected (${rejs.length}):</strong> ${rejs.map(esc).join(', ')}<br>` : '') +
                     (res.length ? `<strong style="color:#93c5fd;">Researched (${res.length}):</strong> ${res.map(esc).join(', ')}` : '');
  }

  function bindTray() {
    document.getElementById('dq-tray-export').addEventListener('click', () => {
      const entries = Object.entries(_state.actions || {});
      const adds = entries.filter(([_, v]) => v.action === 'add').map(([k, _]) => k);
      const rejs = entries.filter(([_, v]) => v.action === 'reject').map(([k, _]) => k);
      const text =
        `# ROS Discovery Queue Triage — ${new Date().toISOString().split('T')[0]}\n\n` +
        `## Add to database (${adds.length})\n` + adds.map(n => `- [ ] ${n}`).join('\n') +
        `\n\n## Rejected (${rejs.length})\n` + rejs.map(n => `- ${n}`).join('\n');
      navigator.clipboard.writeText(text).then(() => {
        document.getElementById('dq-tray-export').textContent = '✓ Copied!';
        setTimeout(() => { document.getElementById('dq-tray-export').textContent = 'Copy to clipboard'; }, 1500);
      });
    });
    document.getElementById('dq-tray-clear').addEventListener('click', () => {
      if (confirm('Clear all triage actions? This will reset your review state.')) {
        _state.actions = {};
        saveActions();
        renderTray();
        render();
      }
    });
  }

  function init() {
    if (typeof DISCOVERY_QUEUE_AUTO === 'undefined') {
      const grid = document.getElementById('dq-grid');
      if (grid) grid.innerHTML = '<div class="dq-empty">Discovery queue data not loaded.</div>';
      return;
    }
    loadActions();
    renderStats(DISCOVERY_QUEUE_AUTO);
    bindFilters();
    bindTray();
    render();
    renderTray();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
