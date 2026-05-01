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

    // Capital flow heatmap (separate fetch — data lives in its own file)
    loadAndRenderCapitalFlow();
  }

  // ── Capital Flow Heatmap ──────────────────────────────────────────────
  async function loadAndRenderCapitalFlow() {
    try {
      const r = await fetch('data/capital_flow_temporal.json?v=' + Date.now(), { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const cf = await r.json();
      renderCapitalFlow(cf);
      // Wire control
      const limitSel = document.getElementById('cf-cluster-limit');
      if (limitSel) limitSel.addEventListener('change', () => renderCapitalFlow(cf));
    } catch (e) {
      const el = document.getElementById('capital-flow-heatmap');
      if (el) el.innerHTML =
        '<div class="il-empty-state"><div class="il-empty-state__icon">📊</div>' +
        '<div class="il-empty-state__title">Capital flow data not available</div>' +
        '<div class="il-empty-state__body">Run <code>python scripts/compute_capital_flow.py</code> to generate.</div></div>';
    }
  }

  function renderCapitalFlow(cf) {
    const heatmap = document.getElementById('capital-flow-heatmap');
    if (!heatmap || !cf || !cf.matrix) return;

    // Sort quarters chronologically
    const allQuarters = new Set();
    Object.values(cf.matrix).forEach((q) => Object.keys(q).forEach((k) => allQuarters.add(k)));
    const quarters = [...allQuarters].sort();

    // Sort clusters by total deal count, take top N per the dropdown
    const limitVal = parseInt(document.getElementById('cf-cluster-limit')?.value || '20', 10) || 0;
    const clusterTotals = Object.entries(cf.matrix)
      .map(([cluster, q]) => ({
        cluster,
        total: Object.values(q).reduce((sum, c) => sum + c.deals, 0),
      }))
      .sort((a, b) => b.total - a.total);
    const clusters = (limitVal > 0 ? clusterTotals.slice(0, limitVal) : clusterTotals).map((x) => x.cluster);

    // Find max deal count for color scaling
    let maxDeals = 1;
    clusters.forEach((cl) => {
      const q = cf.matrix[cl] || {};
      Object.values(q).forEach((cell) => {
        if (cell.deals > maxDeals) maxDeals = cell.deals;
      });
    });

    function intensityColor(deals) {
      if (!deals) return 'transparent';
      const t = Math.min(1, deals / maxDeals);
      // Green at high intensity, dimmer at low
      const alpha = 0.10 + 0.50 * t;
      return `rgba(34, 197, 94, ${alpha.toFixed(2)})`;
    }

    let html = '<table style="width:100%; border-collapse:collapse; font-size: var(--text-xs);">';
    // Header row
    html += '<thead><tr><th style="text-align:left; padding:8px; color: var(--text-muted); font-weight: var(--weight-medium); position: sticky; left: 0; background: var(--bg-card);">Thesis Cluster</th>';
    quarters.forEach((q) => {
      html += `<th style="padding: 6px 8px; color: var(--text-muted); font-weight: var(--weight-medium); font-family: var(--font-mono); text-align: center; min-width: 70px;">${escapeHtml(q)}</th>`;
    });
    html += '<th style="padding: 6px 8px; color: var(--text-muted); text-align: right;">Total</th>';
    html += '</tr></thead><tbody>';

    clusters.forEach((cluster) => {
      const row = cf.matrix[cluster] || {};
      let rowTotal = 0;
      html += `<tr><td style="padding: 6px 8px; color: var(--text-secondary); position: sticky; left: 0; background: var(--bg-card); border-right: 1px solid var(--border-subtle); font-family: var(--font-mono); font-size: var(--text-xs);">${escapeHtml(cluster)}</td>`;
      quarters.forEach((q) => {
        const cell = row[q];
        if (cell) {
          rowTotal += cell.deals;
          const dollars = cell.totalSold ? '$' + (cell.totalSold / 1e6).toFixed(1) + 'M' : '';
          html += `<td class="cf-cell" data-cluster="${escapeHtml(cluster)}" data-quarter="${escapeHtml(q)}" style="text-align:center; padding: 6px 4px; background: ${intensityColor(cell.deals)}; cursor: pointer; border-right: 1px solid var(--bg-page);" title="${cell.deals} deals · ${dollars || 'amounts not summed'}">
            <div style="color: var(--text-primary); font-weight: var(--weight-semi); font-family: var(--font-mono);">${cell.deals}</div>
            ${dollars ? `<div style="color: var(--text-muted); font-size: 9px;">${dollars}</div>` : ''}
          </td>`;
        } else {
          html += '<td style="padding: 6px 4px; border-right: 1px solid var(--bg-page);"></td>';
        }
      });
      html += `<td style="padding: 6px 8px; text-align: right; color: var(--color-primary-bright); font-family: var(--font-mono); font-weight: var(--weight-semi);">${rowTotal}</td></tr>`;
    });

    html += '</tbody></table>';
    heatmap.innerHTML = html;

    // Wire cell drilldown
    heatmap.querySelectorAll('.cf-cell').forEach((td) => {
      td.addEventListener('click', () => {
        const cluster = td.dataset.cluster;
        const quarter = td.dataset.quarter;
        const cell = cf.matrix[cluster]?.[quarter];
        if (!cell) return;
        renderDrilldown(cluster, quarter, cell);
      });
    });
  }

  function renderDrilldown(cluster, quarter, cell) {
    const drill = document.getElementById('cf-drilldown');
    if (!drill) return;
    const dollars = cell.totalSold ? '$' + (cell.totalSold / 1e6).toFixed(1) + 'M Form-D-attested' : '(amounts not summed for this view)';
    drill.style.display = '';
    drill.innerHTML = `
      <div class="il-row il-row--between" style="margin-bottom: var(--space-3);">
        <div>
          <div class="il-text-uppercase il-text-xs il-text-muted">${escapeHtml(quarter)} · ${escapeHtml(cluster)}</div>
          <div style="font-size: var(--text-md); font-weight: var(--weight-semi); margin-top: 4px;">${cell.deals} dated event${cell.deals !== 1 ? 's' : ''}</div>
          <div class="il-text-xs il-text-muted">${dollars}</div>
        </div>
        <button onclick="document.getElementById('cf-drilldown').style.display='none';" style="background: none; border: 1px solid var(--border-default); border-radius: var(--radius-sm); color: var(--text-secondary); padding: 4px 12px; cursor: pointer;">Close</button>
      </div>
      <div style="margin-bottom: var(--space-3);">
        <div class="il-text-uppercase il-text-xs il-text-muted" style="margin-bottom: var(--space-2);">Companies</div>
        ${cell.companies.map((c) => `
          <div style="padding: 6px 0; border-bottom: 1px solid var(--border-subtle);">
            <a href="company.html?c=${encodeURIComponent(c.name)}" style="color: var(--color-primary-bright); text-decoration: none; font-weight: var(--weight-medium);">${escapeHtml(c.name)}</a>
            <span class="il-text-xs il-text-muted"> · ${escapeHtml(c.date)} · source: ${escapeHtml(c.source)}${c.amount ? ` · $${(c.amount / 1e6).toFixed(2)}M` : ''}</span>
          </div>
        `).join('')}
      </div>
      ${cell.investors.length ? `
        <div>
          <div class="il-text-uppercase il-text-xs il-text-muted" style="margin-bottom: var(--space-2);">Tracked-VC investors w/ exposure (current state, not necessarily this round)</div>
          <div class="il-row il-row--gap-2 il-row--wrap">
            ${cell.investors.map((vc) => `<span class="il-badge il-badge--neutral">${escapeHtml(vc)}</span>`).join('')}
          </div>
        </div>
      ` : ''}
    `;
    drill.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
