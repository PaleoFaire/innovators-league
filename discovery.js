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

  function renderScoutTopPicks() {
    const container = document.getElementById('scout-top-picks');
    const weekEl = document.getElementById('scout-week-of');
    if (!container) return;
    if (typeof SCOUT_BRIEFING_AUTO === 'undefined') {
      container.innerHTML = '<div class="scout-empty">Scout briefing not yet generated. Run <code>scripts/scout_top_picks.py</code> or wait for the weekly workflow.</div>';
      return;
    }
    const briefing = SCOUT_BRIEFING_AUTO;
    if (weekEl && briefing.weekOf) {
      weekEl.textContent = 'Week of ' + briefing.weekOf;
    }
    const picks = briefing.topPicks || [];
    if (picks.length === 0) {
      container.innerHTML = '<div class="scout-empty">No high-conviction picks this week. The scout screened ' +
        (briefing.summary?.candidatesScreened || 0) + ' candidates from ' +
        (briefing.summary?.rosterSize || 0) + ' tracked companies.</div>';
      return;
    }
    container.innerHTML = picks.map((p, i) => {
      const d = p.dimensions || {};
      const dimsHtml = [
        ['Capital', d.capital_quality],
        ['Magnitude', d.magnitude],
        ['Tech Depth', d.tech_depth],
        ['Frontier Fit', d.frontier_fit],
        ['Stealth', d.stealth_signal],
        ['Excitement', d.excitement],
      ].map(([k, v]) => `<span class="scout-dim">${k}: <strong>${(v ?? 0).toFixed ? v.toFixed(0) : v}</strong></span>`).join('');

      const briefingMd = (p.briefing || '')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '<br><br>');

      // First verifyUrl from any signal
      const sig = (p.signals || []).find(s => s.verifyUrl) || {};
      const verifyHref = sig.verifyUrl || '#';

      return `<div class="scout-pick">
        <div class="scout-pick-rank">#${i + 1} · ${p.score?.toFixed ? p.score.toFixed(0) : p.score}/70</div>
        <div class="scout-pick-name">${esc(p.name)}</div>
        <div class="scout-pick-sector">${esc(p.suggestedSector || 'Frontier Tech')}</div>
        <div class="scout-pick-dimensions">${dimsHtml}</div>
        <div class="scout-pick-brief">${briefingMd}</div>
        <div class="scout-pick-actions">
          <button class="scout-pick-btn" onclick="window._scoutAdd('${esc(p.name)}')">✓ Add to ROS DB</button>
          <a class="scout-pick-btn scout-pick-btn-research" href="${esc(verifyHref)}" target="_blank" rel="noopener">🔍 Research source →</a>
          <button class="scout-pick-btn scout-pick-btn-skip" onclick="window._scoutSkip('${esc(p.name)}')">Skip this week</button>
        </div>
      </div>`;
    }).join('');

    // Runner-up summary
    const runners = briefing.runnersUp || [];
    if (runners.length) {
      const runnerHtml = runners.slice(0, 8).map(r =>
        `<div class="scout-runner"><span class="scout-runner-name">${esc(r.name)}</span> <span class="scout-runner-meta">${(r.sources || []).join(' · ')} · score ${r.score?.toFixed ? r.score.toFixed(0) : r.score}/70</span></div>`
      ).join('');
      container.innerHTML += `<div style="margin-top:24px;">
        <p style="font-size:11px; color:rgba(255,255,255,0.45); text-transform:uppercase; letter-spacing:0.6px; margin-bottom:8px;">Runners-up (${runners.length})</p>
        ${runnerHtml}
      </div>`;
    }
  }

  // Action helpers exposed globally so the scout-pick buttons can call them
  window._scoutAdd = function(name) {
    setAction(name, 'add');
    alert('Added "' + name + '" to your add-to-DB queue. Click the floating tray to copy as markdown for the ROS team.');
  };
  window._scoutSkip = function(name) {
    setAction(name, 'reject');
  };

  function init() {
    if (typeof DISCOVERY_QUEUE_AUTO === 'undefined') {
      const grid = document.getElementById('dq-grid');
      if (grid) grid.innerHTML = '<div class="dq-empty">Discovery queue data not loaded.</div>';
    }
    loadActions();
    renderScoutTopPicks();  // hero briefing first
    if (typeof DISCOVERY_QUEUE_AUTO !== 'undefined') {
      renderStats(DISCOVERY_QUEUE_AUTO);
      bindFilters();
      render();
    }
    bindTray();
    renderTray();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
