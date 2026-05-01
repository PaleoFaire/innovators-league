/* Public-Market Baskets — page logic.
 * Reads BASKETS (data/baskets.js, loaded via <script> tag) and basket_prices_auto.json.
 */
(function () {
  'use strict';

  const PRICES_URL = 'data/basket_prices_auto.json?v=' + Date.now();

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function fmtPct(x) {
    if (x == null || isNaN(x)) return '—';
    const v = x * 100;
    const sign = v >= 0 ? '+' : '';
    return sign + v.toFixed(1) + '%';
  }
  function pctClass(x) {
    if (x == null || isNaN(x)) return '';
    return x >= 0 ? 'up' : 'down';
  }
  function fmtPrice(p, currency) {
    if (p == null) return '—';
    const sym = currency === 'EUR' ? '€' : currency === 'GBP' ? '£' : currency === 'CAD' ? 'C$' : '$';
    return sym + p.toFixed(2);
  }
  function fmtMcap(m) {
    if (m == null) return '—';
    if (m > 1e12) return '$' + (m / 1e12).toFixed(1) + 'T';
    if (m > 1e9)  return '$' + (m / 1e9).toFixed(1)  + 'B';
    if (m > 1e6)  return '$' + (m / 1e6).toFixed(0)  + 'M';
    return '$' + m.toFixed(0);
  }

  async function loadPrices() {
    try {
      const r = await fetch(PRICES_URL, { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return await r.json();
    } catch (e) {
      console.error('Could not load prices:', e);
      return null;
    }
  }

  // Aggregate weighted return for a basket (only counts active tickers w/ prices)
  function aggregateBasketReturn(basket, prices, period) {
    let totalWeight = 0;
    let weightedSum = 0;
    for (const t of basket.tickers) {
      if (t.status !== 'active') continue;
      const px = prices[t.ticker];
      if (!px || !px.ok || px[period] == null) continue;
      totalWeight += t.weight;
      weightedSum += t.weight * px[period];
    }
    if (totalWeight === 0) return null;
    return weightedSum / totalWeight;
  }

  function renderBasketCard(basket, prices) {
    const ytd = aggregateBasketReturn(basket, prices, 'ytdReturn');
    const y1  = aggregateBasketReturn(basket, prices, 'y1Return');
    const benchmarkPx = prices[basket.benchmark];
    const bYtd = benchmarkPx?.ytdReturn ?? null;
    const bY1  = benchmarkPx?.y1Return ?? null;

    // Sort tickers: active first by weight desc, then watch
    const sortedTickers = [...basket.tickers].sort((a, b) => {
      if (a.status !== b.status) return a.status === 'active' ? -1 : 1;
      return (b.weight || 0) - (a.weight || 0);
    });

    return `
      <details class="il-card basket-card" id="basket-${escapeHtml(basket.id)}">
        <summary>
          <div class="basket-card__header">
            <span class="basket-card__icon">${escapeHtml(basket.icon)}</span>
            <h2 class="basket-card__title">${escapeHtml(basket.name)}</h2>
            <span class="basket-card__cluster">${escapeHtml(basket.thesisCluster)}</span>
          </div>
          <div class="basket-card__methodology">${escapeHtml(basket.methodology)}</div>
          <div class="basket-card__stats">
            <div class="basket-stat">
              <div class="basket-stat__value ${pctClass(ytd)}">${fmtPct(ytd)}</div>
              <div class="basket-stat__label">Basket YTD</div>
            </div>
            <div class="basket-stat">
              <div class="basket-stat__value ${pctClass(bYtd)}">${fmtPct(bYtd)}</div>
              <div class="basket-stat__label">${escapeHtml(basket.benchmark)} YTD</div>
            </div>
            <div class="basket-stat">
              <div class="basket-stat__value ${pctClass(ytd != null && bYtd != null ? ytd - bYtd : null)}">${ytd != null && bYtd != null ? fmtPct(ytd - bYtd) : '—'}</div>
              <div class="basket-stat__label">vs benchmark</div>
            </div>
            <div class="basket-stat">
              <div class="basket-stat__value ${pctClass(y1)}">${fmtPct(y1)}</div>
              <div class="basket-stat__label">Basket 1y</div>
            </div>
            <div class="basket-stat">
              <div class="basket-stat__value">${basket.tickers.filter(t => t.status === 'active').length}</div>
              <div class="basket-stat__label">Holdings</div>
            </div>
            <div class="basket-stat">
              <div class="basket-stat__value">${basket.watchlist.length}</div>
              <div class="basket-stat__label">Watchlist</div>
            </div>
          </div>
        </summary>

        <table class="basket-table">
          <thead>
            <tr>
              <th>Ticker</th><th>Company</th><th class="num">Weight</th><th class="num">Price</th><th class="num">Mkt Cap</th><th class="num">YTD</th><th class="num">1y</th><th>Rationale</th>
            </tr>
          </thead>
          <tbody>
            ${sortedTickers.map(t => {
              const px = prices[t.ticker] || {};
              const cls = t.status === 'watch' ? 'watch' : '';
              return `
                <tr class="${cls}">
                  <td><strong>${escapeHtml(t.ticker)}</strong>${t.status === 'watch' ? ' <span class="il-badge il-badge--neutral">watch</span>' : ''}</td>
                  <td>${escapeHtml((px.name || '').replace(/\s{2,}.*$/, ''))}</td>
                  <td class="num">${(t.weight * 100).toFixed(0)}%</td>
                  <td class="num">${fmtPrice(px.price, px.currency)}</td>
                  <td class="num">${fmtMcap(px.marketCap)}</td>
                  <td class="num ${pctClass(px.ytdReturn)}">${fmtPct(px.ytdReturn)}</td>
                  <td class="num ${pctClass(px.y1Return)}">${fmtPct(px.y1Return)}</td>
                  <td style="color: var(--text-secondary)">${escapeHtml(t.rationale)}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>

        ${basket.watchlist.length ? `
          <div class="basket-watchlist">
            <h4 class="basket-watchlist__title">Pre-IPO watchlist (private companies in our DB that may join)</h4>
            ${basket.watchlist.map(w => `
              <div class="basket-watchlist__item">
                <a href="company.html?c=${encodeURIComponent(w.dbName)}" style="color: var(--text-primary); font-weight: var(--weight-medium); text-decoration: none; border-bottom: 1px dotted var(--border-default);">${escapeHtml(w.dbName)}</a>
                — ${escapeHtml(w.expectedIPO)} · ${escapeHtml(w.note || '')}
              </div>
            `).join('')}
          </div>
        ` : ''}

        ${basket.removed && basket.removed.length ? `
          <div class="basket-watchlist">
            <h4 class="basket-watchlist__title">Audit log — removed constituents</h4>
            ${basket.removed.map(r => `
              <div class="basket-watchlist__item">
                <strong>${escapeHtml(r.ticker)}</strong> removed ${escapeHtml(r.removedDate)}: ${escapeHtml(r.reason)}
              </div>
            `).join('')}
          </div>
        ` : ''}

        <div style="margin-top: var(--space-3); font-size: var(--text-xs); color: var(--text-muted)">
          Last reviewed: ${escapeHtml(basket.lastReviewed)} · Curated by: ${escapeHtml(basket.curator)} · Benchmark: ${escapeHtml(basket.benchmarkName)}
        </div>
      </details>
    `;
  }

  async function boot() {
    if (typeof BASKETS === 'undefined') {
      document.getElementById('bk-loading').innerHTML =
        '<div class="il-card il-card--danger"><div class="il-card__title">BASKETS not loaded</div>' +
        '<div class="il-card__body">data/baskets.js failed to load.</div></div>';
      return;
    }

    const priceData = await loadPrices();
    const prices = priceData?.prices || {};

    // Stats
    const totalTickers = new Set();
    let totalWatch = 0;
    BASKETS.forEach(b => {
      b.tickers.forEach(t => totalTickers.add(t.ticker));
      totalWatch += b.watchlist.length;
    });
    document.getElementById('stat-baskets').textContent  = BASKETS.length;
    document.getElementById('stat-tickers').textContent  = totalTickers.size;
    document.getElementById('stat-watchlist').textContent = totalWatch;
    document.getElementById('stat-fresh').textContent =
      priceData?.generatedAt
        ? new Date(priceData.generatedAt).toLocaleDateString()
        : '—';

    document.getElementById('bk-loading').remove();
    const feedEl = document.getElementById('bk-feed');
    feedEl.innerHTML = BASKETS.map(b => renderBasketCard(b, prices)).join('');
    feedEl.hidden = false;

    // Open the first basket by default
    const first = feedEl.querySelector('details');
    if (first) first.open = true;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
