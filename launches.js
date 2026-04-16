/* ─── Space Launch Manifest Page ─── */
/* Loads upcoming launches from data/launch_manifest_auto.json when available */

(function () {
  'use strict';

  const esc = (typeof escapeHtml === 'function') ? escapeHtml : (s) => String(s || '');

  function renderPlaceholder() {
    // The "in progress" note in the HTML already explains the state — nothing to do.
  }

  function renderLaunches(launches) {
    const grid = document.getElementById('launch-manifest-grid');
    const note = document.getElementById('launch-manifest-note');
    if (!grid) return;

    if (!Array.isArray(launches) || launches.length === 0) return;

    // Build a set of tracked company names for payload highlighting
    const trackedNames = new Set();
    if (typeof COMPANIES !== 'undefined' && Array.isArray(COMPANIES)) {
      COMPANIES.forEach(c => { if (c && c.name) trackedNames.add(c.name.toLowerCase()); });
    }

    const sorted = [...launches].sort((a, b) =>
      String(a.date || '9').localeCompare(String(b.date || '9'))
    );

    const html = '<div class="leaderboard-table-wrap"><table class="leaderboard-table">' +
      '<thead><tr><th>Date</th><th>Vehicle</th><th>Payload</th><th>Pad</th><th>Source</th></tr></thead>' +
      '<tbody>' +
      sorted.slice(0, 100).map(l => {
        const payloadLower = (l.payload || '').toLowerCase();
        const matched = [...trackedNames].find(n => payloadLower.includes(n));
        const highlighted = matched ? 'style="background:rgba(255,107,44,0.06);"' : '';
        return `<tr ${highlighted}>
          <td style="font-family:'Space Grotesk', monospace; font-weight:600;">${esc(l.date || 'TBD')}</td>
          <td>${esc(l.vehicle || '—')}</td>
          <td style="font-weight:600;">${esc(l.payload || '—')}${matched ? ' <span style="background:rgba(255,107,44,0.15); color:var(--accent); padding:1px 6px; border-radius:8px; font-size:10px; font-weight:700; margin-left:6px;">TRACKED</span>' : ''}</td>
          <td style="font-size:12px; color:rgba(255,255,255,0.55);">${esc(l.pad || '—')}</td>
          <td>${l.url ? `<a href="${esc(l.url)}" target="_blank" rel="noopener" style="color:var(--accent); text-decoration:none; font-size:11px;">${esc(l.provider || 'source')} →</a>` : esc(l.provider || '—')}</td>
        </tr>`;
      }).join('') +
      '</tbody></table></div>';

    grid.innerHTML = html;
    if (note) note.style.display = 'none';
  }

  function init() {
    fetch('data/launch_manifest_auto.json', { cache: 'no-cache' })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) renderLaunches(data);
        else renderPlaceholder();
      })
      .catch(() => renderPlaceholder());
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
