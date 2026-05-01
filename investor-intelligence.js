/* Investor Intelligence — page logic. */
(function () {
  'use strict';

  const FEED_URL = 'data/investor_intelligence.json?v=' + Date.now();

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  async function loadIntel() {
    try {
      const r = await fetch(FEED_URL, { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return await r.json();
    } catch (e) {
      console.error('Could not load intel:', e);
      return null;
    }
  }

  function renderMomentum(momentum) {
    const top = momentum.slice(0, 15);
    const maxScore = Math.max(...top.map((m) => m.score), 1);
    return top.map((m, i) => {
      const barW = (m.score / maxScore) * 100;
      const examples = (m.recentExamples || []).slice(0, 3).map((e) =>
        `<span style="margin-right: 6px"><strong style="color: var(--text-primary)">${escapeHtml(e.company)}</strong> <span class="il-text-muted">(${escapeHtml(e.cluster)})</span></span>`
      ).join('');
      return `
        <div class="momentum-row">
          <div class="momentum-row__rank">${i + 1}</div>
          <div>
            <div class="momentum-row__vc">${escapeHtml(m.vc)}</div>
            <div class="momentum-row__bar"><div class="momentum-row__bar-fill" style="width: ${barW}%"></div></div>
            <div class="il-text-xs il-text-muted" style="margin-top: 4px">
              ${examples || '(no recent examples)'}
            </div>
          </div>
          <div class="momentum-row__cluster">→ ${escapeHtml(m.topCluster || '—')}</div>
          <div class="momentum-row__metrics">
            <strong>${m.recentCount}</strong> recent · ${m.totalCount} total
          </div>
          <div class="momentum-row__metrics" style="text-align: right; font-size: var(--text-md)">
            ${m.score.toFixed(2)}
          </div>
        </div>
      `;
    }).join('');
  }

  function renderSpecialists(specialists, topClusters) {
    // Show top clusters w/ their leader VCs
    return topClusters.slice(0, 12).map((c) => {
      const leaders = specialists[c.cluster] || [];
      const leaderHtml = leaders.slice(0, 4).map((l) => `
        <div class="specialist-leader">
          <strong>${escapeHtml(l.vc)}</strong>
          <span class="specialist-leader__count">${l.count}</span>
          <span class="specialist-leader__share">${(l.share * 100).toFixed(0)}%</span>
        </div>
      `).join('');
      return `
        <div class="il-card specialist-card">
          <div class="specialist-card__cluster">${escapeHtml(c.cluster)}</div>
          <div class="specialist-card__leaders">${leaderHtml || '<span class="il-text-muted il-text-xs">No tracked-VC investments yet</span>'}</div>
          <div class="il-text-xs il-text-muted" style="margin-top: var(--space-2)">
            ${c.investmentCount} total tracked-VC investments in this cluster
          </div>
        </div>
      `;
    }).join('');
  }

  function renderPedigree(pedigree) {
    const sorted = Object.entries(pedigree)
      .sort(([, a], [, b]) => b.length - a.length);
    if (!sorted.length) {
      return `<div class="il-empty-state">
        <div class="il-empty-state__icon">🧬</div>
        <div class="il-empty-state__title">No pedigree matches found</div>
        <div class="il-empty-state__body">Founder bios in our DB don't yet mention common origin patterns. As bios get richer, this section will fill in.</div>
      </div>`;
    }
    return sorted.map(([source, kids]) => `
      <div class="pedigree-source">
        <div class="pedigree-source__name">${escapeHtml(source)} <span class="pedigree-source__count">— ${kids.length} ${kids.length === 1 ? 'company' : 'companies'}</span></div>
        <div class="pedigree-children">
          ${kids.slice(0, 30).map((k) => `
            <span class="pedigree-child" title="${escapeHtml(k.founder || '')}">
              <strong>${escapeHtml(k.company)}</strong>
              ${k.cluster ? `<span class="il-text-muted"> · ${escapeHtml(k.cluster.replace(/-/g, ' '))}</span>` : ''}
            </span>
          `).join('')}
          ${kids.length > 30 ? `<span class="il-text-muted il-text-xs">+ ${kids.length - 30} more</span>` : ''}
        </div>
      </div>
    `).join('');
  }

  async function boot() {
    const data = await loadIntel();
    if (!data) {
      document.getElementById('momentum-list').innerHTML =
        '<div class="il-empty-state"><div class="il-empty-state__title">Could not load intelligence feed</div>' +
        '<div class="il-empty-state__body">data/investor_intelligence.json is missing. Run <code>python scripts/compute_investor_intelligence.py</code>.</div></div>';
      return;
    }

    // Stats
    document.getElementById('stat-vcs').textContent         = data.stats.vcFirms;
    document.getElementById('stat-cos').textContent         = data.stats.companies;
    document.getElementById('stat-clusters').textContent    = data.stats.uniqueClusters;
    document.getElementById('stat-investments').textContent = data.stats.totalInvestments;
    document.getElementById('ii-fresh').textContent         = new Date(data.generatedAt).toLocaleString();

    // Momentum
    document.getElementById('momentum-list').innerHTML = renderMomentum(data.momentum);

    // Specialists
    document.getElementById('specialists-list').innerHTML = renderSpecialists(data.specialists, data.topClusters);

    // Pedigree
    document.getElementById('pedigree-list').innerHTML = renderPedigree(data.pedigree);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
