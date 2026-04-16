/* ─── Patent Velocity Page ─── */
/* Renders patent filings by company from PATENT_INTEL_AUTO or placeholder */

(function () {
  'use strict';

  const esc = (typeof escapeHtml === 'function') ? escapeHtml : (s) => String(s || '');

  function initPatentVelocity() {
    const grid = document.getElementById('patent-velocity-grid');
    const note = document.getElementById('patent-velocity-note');
    if (!grid) return;

    const patents = (typeof PATENT_INTEL_AUTO !== 'undefined' && Array.isArray(PATENT_INTEL_AUTO))
      ? PATENT_INTEL_AUTO : [];

    if (patents.length === 0) {
      // Placeholder — the note already explains why, don't duplicate
      return;
    }

    // Build a velocity view: sort by recent patent count descending
    const sorted = [...patents]
      .filter(p => p && p.company)
      .sort((a, b) => (b.patentCount || 0) - (a.patentCount || 0))
      .slice(0, 50);

    const html = '<div class="leaderboard-table-wrap"><table class="leaderboard-table">' +
      '<thead><tr><th>Rank</th><th>Company</th><th>Total Patents</th><th>Recent Filings</th><th>USPTO Link</th></tr></thead>' +
      '<tbody>' +
      sorted.map((p, i) => {
        const uspto = `https://patft.uspto.gov/netacgi/nph-Parser?patentsearch-bool.html&TERM1=${encodeURIComponent(p.company)}`;
        return `<tr>
          <td style="font-weight:700; color:var(--accent);">#${i + 1}</td>
          <td style="font-weight:600;">${esc(p.company)}</td>
          <td style="font-family:'Space Grotesk', monospace;">${esc(p.patentCount || 0)}</td>
          <td style="font-family:'Space Grotesk', monospace;">${esc(p.recentPatents || 0)}</td>
          <td><a href="${uspto}" target="_blank" rel="noopener" style="color:var(--accent); text-decoration:none; font-size:11px;">USPTO search →</a></td>
        </tr>`;
      }).join('') +
      '</tbody></table></div>';

    grid.innerHTML = html;
    // Hide the "in progress" note since we have data
    if (note) note.style.display = 'none';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPatentVelocity);
  } else {
    initPatentVelocity();
  }
})();
