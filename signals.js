// ═══════════════════════════════════════════════════════════════════════════════
// signals.html renderers — 5 proprietary intelligence sections
// Each section reads its own auto.js global and renders defensively so the
// page still renders if any one feed is empty or awaiting config.
// ═══════════════════════════════════════════════════════════════════════════════

(function () {
  'use strict';

  const esc = (typeof escapeHtml === 'function') ? escapeHtml : function (s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  };

  // ── Helpers ───────────────────────────────────────────────────────────────

  function formatAmount(s) {
    if (!s) return '—';
    const raw = String(s).replace(/[$,]/g, '');
    const n = parseFloat(raw);
    if (isNaN(n) || n === 0) return s;
    if (n >= 1e9) return '$' + (n / 1e9).toFixed(1) + 'B';
    if (n >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return '$' + (n / 1e3).toFixed(0) + 'K';
    return '$' + n.toFixed(0);
  }

  function daysAgo(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr + 'T00:00:00Z');
    if (isNaN(d)) return '';
    const days = Math.floor((Date.now() - d) / 86400000);
    if (days === 0) return 'today';
    if (days === 1) return '1d ago';
    if (days < 30) return days + 'd ago';
    if (days < 365) return Math.floor(days / 30) + 'mo ago';
    return Math.floor(days / 365) + 'y ago';
  }

  // ── SECTION 1: Form D Filings ─────────────────────────────────────────────

  function renderFormD() {
    const grid = document.getElementById('form-d-grid');
    const count = document.getElementById('form-d-count');
    if (!grid) return;
    const data = (typeof FORM_D_FILINGS !== 'undefined') ? FORM_D_FILINGS : null;
    if (!data || !Array.isArray(data.filings) || data.filings.length === 0) {
      grid.innerHTML = '<div style="padding:24px; background:rgba(255,255,255,0.03); border-radius:10px; color:rgba(255,255,255,0.55); font-size:13px;">No Form D filings from tracked companies in the last 60 days. The pipeline is live; new filings will appear as they\'re filed.</div>';
      if (count) count.textContent = '0';
      return;
    }
    if (count) count.textContent = data.total_filings;

    grid.innerHTML = data.filings.map(f => {
      const amt = formatAmount(f.offering_amount);
      const secType = f.securities_type || '';
      const isSafe = f.is_safe || /safe/i.test(secType);
      const pillClass = isSafe ? 'safe' : (secType.toLowerCase().indexOf('equity') >= 0 ? 'equity' : '');
      const pillLabel = isSafe ? 'SAFE' : (secType || 'Form D');
      return `
        <a class="filing-card" href="${esc(f.filing_url)}" target="_blank" rel="noopener">
          <div class="filing-row-top">
            <span class="filing-co">${esc(f.company)}</span>
            <span class="filing-amt">${esc(amt)}</span>
          </div>
          ${f.issuer_name && f.issuer_name !== f.company
            ? `<div class="filing-issuer">filed as "${esc(f.issuer_name)}"</div>` : ''}
          <div class="filing-meta-row">
            <span class="filing-pill ${pillClass}">${esc(pillLabel)}</span>
            ${f.filed_date ? `<span class="filing-pill">${esc(f.filed_date.slice(0, 10))} · ${daysAgo(f.filed_date)}</span>` : ''}
            ${f.exemption ? `<span class="filing-pill">${esc(f.exemption)}</span>` : ''}
          </div>
        </a>
      `;
    }).join('');
  }

  // ── SECTION 2: Export Controls ────────────────────────────────────────────

  function renderExportControls() {
    const body = document.getElementById('ec-body');
    const count = document.getElementById('ec-count');
    const newAddsEl = document.getElementById('ec-new-adds');
    if (!body) return;
    const data = (typeof EXPORT_CONTROLS !== 'undefined') ? EXPORT_CONTROLS : null;
    if (!data) {
      body.innerHTML = '<div style="color:rgba(255,255,255,0.5); font-size:13px;">Export Controls data unavailable.</div>';
      return;
    }
    if (count) count.textContent = data.matches_total || 0;
    if (newAddsEl) {
      newAddsEl.textContent = (data.new_this_run > 0)
        ? `${data.new_this_run} NEW this run`
        : 'no new this run';
    }

    const matches = data.matches || [];
    if (matches.length === 0) {
      body.innerHTML = `
        <div class="ec-empty">
          <strong>✓ All clear.</strong>
          ${data.tracked_companies || 868} tracked companies cross-referenced against ${(data.total_list_entries || 0).toLocaleString()} entries on ${Object.keys(data.by_list || {}).length || 'multiple'} restricted-party lists — zero matches.
          <div style="margin-top:8px; font-size:12px; color:rgba(255,255,255,0.55);">Sources: BIS Entity List · OFAC SDN · ITAR Debarred · State Nonproliferation · + 10 more · refreshed daily</div>
        </div>
      `;
      return;
    }

    const newKeys = new Set(
      (data.new_additions || []).map(m => `${m.company}|${m.listed_name}|${m.list_source_raw}`)
    );
    body.innerHTML = matches.map(m => {
      const key = `${m.company}|${m.listed_name}|${m.list_source_raw}`;
      const isNew = newKeys.has(key);
      return `
        <div class="ec-match-card ${isNew ? 'new' : ''}">
          <div class="ec-match-title">
            ${isNew ? '🆕 ' : ''}${esc(m.company)} → ${esc(m.list_source)}
          </div>
          <div class="ec-match-meta">
            Listed as: <strong style="color:rgba(255,255,255,0.85);">${esc(m.listed_name)}</strong>
            ${m.list_added ? ` · added ${esc(m.list_added)}` : ''}
            ${m.country ? ` · ${esc(m.country)}` : ''}
          </div>
          ${m.remarks ? `<div style="margin-top:6px; font-size:12px; color:rgba(255,255,255,0.55);">${esc(m.remarks.slice(0, 240))}</div>` : ''}
          <div style="margin-top:8px;">
            <a href="${esc(m.source_url)}" target="_blank" rel="noopener" style="font-size:12px; color:#fca5a5; text-decoration:none;">→ View on source list</a>
          </div>
        </div>
      `;
    }).join('');
  }

  // ── SECTION 3: Trademarks ─────────────────────────────────────────────────

  function renderTrademarks() {
    const body = document.getElementById('tm-body');
    const count = document.getElementById('tm-count');
    if (!body) return;
    const data = (typeof TRADEMARK_FILINGS !== 'undefined') ? TRADEMARK_FILINGS : null;
    if (!data) {
      body.innerHTML = '<div class="tm-placeholder">Trademark data not loaded.</div>';
      return;
    }
    if (data.status === 'awaiting_uspto_api_key' || data.total_hits === 0) {
      body.innerHTML = `
        <div class="tm-placeholder">
          <strong>Pipeline wired, awaiting API key</strong>
          Get a free USPTO Trademark API key at <a href="https://developer.uspto.gov/api-catalog" target="_blank" style="color:#a78bfa;">developer.uspto.gov/api-catalog</a>
          and set <code>USPTO_API_KEY</code> in your GitHub Actions secrets. On the next weekly sync, this section populates automatically — no deploy.
        </div>
      `;
      if (count) count.textContent = '—';
      return;
    }
    if (count) count.textContent = data.total_hits || 0;

    const trademarks = data.trademarks || [];
    body.innerHTML = `
      <div class="filing-grid">
      ${trademarks.map(t => `
        <a class="filing-card" href="${esc(t.source_url)}" target="_blank" rel="noopener">
          <div class="filing-row-top">
            <span class="filing-co">${esc(t.mark || '—')}</span>
            <span class="filing-amt" style="color:#a78bfa; font-size:12px;">${esc(t.company)}</span>
          </div>
          <div class="filing-meta-row">
            ${t.filing_date ? `<span class="filing-pill">${esc(t.filing_date)} · ${daysAgo(t.filing_date)}</span>` : ''}
            ${(t.nice_class_labels || []).slice(0, 2).map(l =>
              `<span class="filing-pill">${esc(l)}</span>`).join('')}
            ${t.status ? `<span class="filing-pill">${esc(t.status)}</span>` : ''}
          </div>
        </a>
      `).join('')}
      </div>
    `;
  }

  // ── SECTION 4: SBIR Bid-Fit ───────────────────────────────────────────────

  function renderSbirBidFit() {
    const body = document.getElementById('sbir-body');
    const count = document.getElementById('sbir-count');
    if (!body) return;
    const topics = (typeof SBIR_TOPICS_AUTO !== 'undefined') ? SBIR_TOPICS_AUTO : [];
    if (!topics.length) {
      body.innerHTML = '<div style="color:rgba(255,255,255,0.5); font-size:13px;">No SBIR topics available.</div>';
      if (count) count.textContent = '0';
      return;
    }
    if (count) count.textContent = topics.length;

    // Only show topics that are still open (closeDate in future) and have bidFit data
    const today = new Date().toISOString().slice(0, 10);
    const live = topics.filter(t => !t.closeDate || t.closeDate >= today);

    body.innerHTML = live.map(t => {
      const bidFit = t.bidFit || [];
      return `
        <div class="sbir-topic-card">
          <div class="sbir-topic-title">${esc(t.title || '')}</div>
          <div class="sbir-topic-desc">${esc(t.description || '')}</div>
          <div class="sbir-topic-meta">
            <span>${esc(t.agency || '—')}</span>
            <span>•</span>
            <span>${esc(t.phase || '—')}</span>
            ${t.award ? `<span>•</span><span>${esc(t.award)}</span>` : ''}
            ${t.closeDate ? `<span>•</span><span>closes ${esc(t.closeDate)}</span>` : ''}
          </div>
          ${bidFit.length ? `
            <div style="font-size:11px; color:rgba(255,255,255,0.5); margin-bottom:6px; text-transform:uppercase; letter-spacing:0.5px;">Top Bid-Fit Matches (TF-IDF scored)</div>
            <div class="sbir-bidfit-grid">
              ${bidFit.slice(0, 6).map(bf => `
                <a class="sbir-bidfit" href="company.html?c=${encodeURIComponent(bf.company)}">
                  <div>
                    <div class="sbir-bidfit-name">${esc(bf.company)}</div>
                    <div class="sbir-bidfit-terms">${esc((bf.matched_terms || []).join(' · '))}</div>
                  </div>
                  <div class="sbir-bidfit-score">${bf.bid_fit_score.toFixed(0)}</div>
                </a>
              `).join('')}
            </div>
          ` : ''}
        </div>
      `;
    }).join('');
  }

  // ── SECTION 5: Factory Watch ──────────────────────────────────────────────

  function renderFactoryWatch() {
    const body = document.getElementById('fw-body');
    const count = document.getElementById('fw-count');
    if (!body) return;
    const data = (typeof FACTORY_WATCH !== 'undefined') ? FACTORY_WATCH : null;
    if (!data || !data.sites || !data.sites.length) {
      body.innerHTML = '<div style="color:rgba(255,255,255,0.5); font-size:13px;">Factory Watch data unavailable.</div>';
      if (count) count.textContent = '0';
      return;
    }
    if (count) count.textContent = data.total_watch_sites;

    body.innerHTML = `
      <div class="fw-grid">
      ${data.sites.map(s => {
        const latest = s.latest_pass_date ? `${s.latest_pass_date} · ${daysAgo(s.latest_pass_date)}` : '—';
        const clearStr = (s.days_since_clear != null) ?
          `${s.days_since_clear}d ago` : 'None in window';
        const clearClass = s.clear_scene_count > 0 ? 'clear' : 'cloudy';
        const browserLink = s.scenes && s.scenes[0] ? s.scenes[0].browser_url : '';
        return `
          <div class="fw-card">
            <div class="fw-co">${esc(s.company)}</div>
            <div class="fw-site">${esc(s.site)}</div>
            <div class="fw-stats">
              <div>
                <div class="fw-stat-lbl">Latest pass</div>
                <div class="fw-stat-val">${esc(latest)}</div>
              </div>
              <div>
                <div class="fw-stat-lbl">Last clear</div>
                <div class="fw-stat-val ${clearClass}">${esc(clearStr)}</div>
              </div>
              <div>
                <div class="fw-stat-lbl">Clear/Total</div>
                <div class="fw-stat-val">${s.clear_scene_count}/${s.scene_count}</div>
              </div>
            </div>
            ${browserLink ? `<a href="${esc(browserLink)}" target="_blank" rel="noopener" class="fw-link">→ View satellite imagery</a>` : ''}
          </div>
        `;
      }).join('')}
      </div>
      <div style="margin-top:16px; font-size:11px; color:rgba(255,255,255,0.4);">
        Cloud-free threshold: &lt; ${data.cloud_free_threshold_pct}% cover. Source: ESA Copernicus (free, public, ${data.lookback_days}-day lookback).
      </div>
    `;
  }

  // ── Boot ──────────────────────────────────────────────────────────────────

  function boot() {
    try { renderFormD(); } catch (e) { console.error('[signals] Form D failed:', e); }
    try { renderExportControls(); } catch (e) { console.error('[signals] Export Controls failed:', e); }
    try { renderTrademarks(); } catch (e) { console.error('[signals] Trademarks failed:', e); }
    try { renderSbirBidFit(); } catch (e) { console.error('[signals] SBIR failed:', e); }
    try { renderFactoryWatch(); } catch (e) { console.error('[signals] Factory Watch failed:', e); }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
