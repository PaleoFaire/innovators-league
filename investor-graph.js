// ═══════════════════════════════════════════════════════════════════════════════
// INVESTOR GRAPH — runtime investor index built from COMPANIES.investors
//
// Builds INVESTOR_INDEX at page load: normalizes ~3,100 raw investor strings
// (strips "(lead)" / "(co-lead)" / descriptor parentheticals, merges obvious
// variants like a16z ↔ Andreessen Horowitz, NVentures (NVIDIA) ↔ NVentures,
// Data Collective ↔ DCVC) into canonical investors, each mapped to:
//   { companies, companySet, count, leadCount, leadSet, sectors, topSectors,
//     coInvestors (top-10 by overlap), notable }
//
// Consumed by:
//   • investors.html  — "All Investors" directory (table + detail panel)
//   • app.js (index.html) — "Backed by" screener filter (lazy-loads this file)
//
// Pure client-side, zero network calls beyond loading this script. No frameworks.
// ═══════════════════════════════════════════════════════════════════════════════

(function () {
  'use strict';

  // ─── NORMALIZATION ───

  // Explicit variant merges (keys are lowercase, post-parenthetical-strip).
  // Only "obvious" identities go here — everything else is handled by the
  // generic suffix-merge pass below.
  const ALIASES = {
    'a16z': 'andreessen horowitz',
    'a16z bio + health': 'andreessen horowitz',
    'yc': 'y combinator',
    'iqt': 'in-q-tel',
    'data collective': 'dcvc',
    'nea': 'new enterprise associates',
    'nvidia nventures': 'nventures',
    'google ventures': 'gv',                    // GV is the canonical brand; bare "Google" stays separate (strategic)
    'engine ventures': 'the engine',
    'the engine ventures': 'the engine',
    'usit': 'us innovative technology fund',
    'u.s. innovation technology fund': 'us innovative technology fund',
    'u.s. innovative technology fund': 'us innovative technology fund',
    "thomas tull's us innovative technology fund": 'us innovative technology fund',
    'eic': 'european innovation council',
    'eic fund': 'european innovation council',
    'eic accelerator': 'european innovation council',
    'european innovation council fund': 'european innovation council',
    'european innovation council accelerator': 'european innovation council',
    'european innovation council accelerator / eic fund': 'european innovation council'
  };

  // Generic trailing words stripped (iteratively) to find a variant "root":
  // "Lightspeed Venture Partners" → lightspeed, "Bond Capital" → bond.
  const SUFFIX_WORDS = new Set(['ventures', 'venture', 'capital', 'partners', 'vc', 'fund', 'holdings']);

  // Remove every parenthetical group: "Sequoia Capital (lead Series B)" →
  // "Sequoia Capital"; "European Innovation Council (EIC) Fund" →
  // "European Innovation Council Fund".
  function stripAnnotations(raw) {
    return String(raw || '')
      .replace(/\s*\([^)]*\)/g, ' ')
      .replace(/\s+/g, ' ')
      .replace(/[\s,.;]+$/, '')
      .trim();
  }

  // Lead flags live only inside parentheses: "(lead)", "(co-lead)",
  // "(lead, Series A)". Word-boundary so "Lead Edge Capital" never matches.
  function hasLeadAnnotation(raw) {
    const re = /\(([^)]*)\)/g;
    let m;
    const s = String(raw || '');
    while ((m = re.exec(s)) !== null) {
      if (/\b(?:co-)?lead\b/i.test(m[1])) return true;
    }
    return false;
  }

  // Raw string → preliminary canonical key (pre suffix-merge).
  function rawToKey(raw) {
    const stripped = stripAnnotations(raw);
    if (!stripped) return null;
    const key = stripped.toLowerCase();
    return ALIASES[key] || key;
  }

  function rootOf(key) {
    const words = key.split(' ');
    while (words.length > 1 && SUFFIX_WORDS.has(words[words.length - 1])) words.pop();
    const root = words.join(' ');
    return root.length >= 2 ? root : key;
  }

  function moneyNum(v) {
    const m = String(v || '').match(/\$?\s*([\d,.]+)\s*([TBMK])/i);
    if (!m) return 0;
    const n = parseFloat(m[1].replace(/,/g, ''));
    if (isNaN(n)) return 0;
    const mult = { T: 1e12, B: 1e9, M: 1e6, K: 1e3 }[m[2].toUpperCase()] || 1;
    return n * mult;
  }

  // ─── INDEX BUILDER ───

  function buildInvestorIndex(companies) {
    const list = Array.isArray(companies) ? companies : [];

    // Pass 1 — per-company preliminary keys + casing votes + lead flags
    const casings = new Map();     // key → Map(displayString → votes)
    const perCompany = [];         // [{ company, invMap: Map(key → {lead}) }]
    list.forEach(c => {
      if (!Array.isArray(c.investors) || c.investors.length === 0) return;
      const invMap = new Map();
      c.investors.forEach(raw => {
        const key = rawToKey(raw);
        if (!key) return;
        const display = stripAnnotations(raw);
        if (!casings.has(key)) casings.set(key, new Map());
        const cv = casings.get(key);
        cv.set(display, (cv.get(display) || 0) + 1);
        const lead = hasLeadAnnotation(raw);
        const prev = invMap.get(key);
        invMap.set(key, { lead: lead || (prev && prev.lead) || false });
      });
      if (invMap.size) perCompany.push({ company: c, invMap });
    });

    // Pass 2 — generic suffix merge. Group keys by root; merge a group only
    // when it is "variant-shaped": the bare root is itself a key, or one
    // member is a word-prefix of every other member (D1 Capital ↔ D1 Capital
    // Partners). Canonical = member with the biggest portfolio (tie → longer
    // name). Prevents unrelated firms that merely share a first word from
    // collapsing together.
    const counts = new Map(); // key → company count
    perCompany.forEach(({ invMap }) => invMap.forEach((_v, k) => counts.set(k, (counts.get(k) || 0) + 1)));

    const groups = new Map(); // root → [keys]
    counts.forEach((_n, key) => {
      const root = rootOf(key);
      if (!groups.has(root)) groups.set(root, []);
      groups.get(root).push(key);
    });

    const remap = new Map(); // key → canonical key
    groups.forEach((keys, root) => {
      if (keys.length < 2) return;
      const isPrefixOfAll = base => keys.every(k => k === base || k.startsWith(base + ' '));
      const variantShaped = keys.includes(root) || keys.some(isPrefixOfAll);
      if (!variantShaped) return;
      const target = keys.slice().sort((a, b) =>
        (counts.get(b) - counts.get(a)) || (b.length - a.length))[0];
      keys.forEach(k => { if (k !== target) remap.set(k, target); });
    });

    const finalKey = k => remap.get(k) || k;

    // Pass 3 — entries
    const index = new Map();
    const companyByName = new Map();
    perCompany.forEach(({ company, invMap }) => {
      companyByName.set(company.name, company);
      const merged = new Map(); // finalKey → {lead}
      invMap.forEach((v, k) => {
        const fk = finalKey(k);
        const prev = merged.get(fk);
        merged.set(fk, { lead: v.lead || (prev && prev.lead) || false });
      });
      merged.forEach((v, fk) => {
        if (!index.has(fk)) {
          index.set(fk, {
            key: fk, name: fk, companies: [], companySet: new Set(),
            count: 0, leadCount: 0, leadSet: new Set(),
            sectors: {}, topSectors: [], coInvestors: [], notable: []
          });
        }
        const e = index.get(fk);
        if (!e.companySet.has(company.name)) {
          e.companies.push(company.name);
          e.companySet.add(company.name);
          e.count++;
          const sector = company.sector || 'Other';
          e.sectors[sector] = (e.sectors[sector] || 0) + 1;
        }
        if (v.lead && !e.leadSet.has(company.name)) {
          e.leadSet.add(company.name);
          e.leadCount++;
        }
      });
      // store final key list for the co-investor pass
      company.__ilFinalKeys = [...merged.keys()];
    });

    // Display names — most-voted casing across all merged variants
    index.forEach(e => {
      const votes = new Map();
      // pool casing votes from every preliminary key that maps to this entry
      casings.forEach((cv, k) => {
        if (finalKey(k) !== e.key) return;
        cv.forEach((n, display) => votes.set(display, (votes.get(display) || 0) + n));
      });
      let best = e.key, bestN = -1;
      votes.forEach((n, display) => {
        if (n > bestN || (n === bestN && display.length > best.length)) { best = display; bestN = n; }
      });
      e.name = best;
      e.topSectors = Object.entries(e.sectors).sort((a, b) => b[1] - a[1]).slice(0, 3);
      e.notable = e.companies.slice().sort((a, b) => {
        const ca = companyByName.get(a) || {}, cb = companyByName.get(b) || {};
        return (moneyNum(cb.totalRaised) || moneyNum(cb.valuation)) -
               (moneyNum(ca.totalRaised) || moneyNum(ca.valuation));
      }).slice(0, 3);
    });

    // Pass 4 — co-investor overlaps (pairwise within each company)
    const pairCounts = new Map(); // "a|b" (a<b) → n
    perCompany.forEach(({ company }) => {
      const keys = company.__ilFinalKeys || [];
      for (let i = 0; i < keys.length; i++) {
        for (let j = i + 1; j < keys.length; j++) {
          const a = keys[i] < keys[j] ? keys[i] : keys[j];
          const b = keys[i] < keys[j] ? keys[j] : keys[i];
          const pk = a + '|' + b;
          pairCounts.set(pk, (pairCounts.get(pk) || 0) + 1);
        }
      }
      delete company.__ilFinalKeys;
    });
    const coMap = new Map(); // key → [{key, overlap}]
    pairCounts.forEach((n, pk) => {
      const [a, b] = pk.split('|');
      if (!coMap.has(a)) coMap.set(a, []);
      if (!coMap.has(b)) coMap.set(b, []);
      coMap.get(a).push({ key: b, overlap: n });
      coMap.get(b).push({ key: a, overlap: n });
    });
    index.forEach(e => {
      const co = (coMap.get(e.key) || [])
        .sort((a, b) => b.overlap - a.overlap || a.key.localeCompare(b.key))
        .slice(0, 10);
      e.coInvestors = co.map(x => ({ key: x.key, name: (index.get(x.key) || {}).name || x.key, overlap: x.overlap }));
    });

    return { index, companyByName };
  }

  // ─── DIRECTORY UI (investors.html — no-ops when the section is absent) ───

  const MIN_PORTFOLIO = 3; // directory shows investors with ≥ 3 portfolio companies

  let INDEX = null, COMPANY_BY_NAME = null, LIST = [];
  let uiState = { search: '', sortKey: 'count', sortDir: -1, openKey: null };

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function companyHref(name) { return 'company.html?c=' + encodeURIComponent(name); }

  function directoryRows() {
    let rows = LIST.filter(e => e.count >= MIN_PORTFOLIO);
    const q = uiState.search.trim().toLowerCase();
    if (q) {
      rows = rows.filter(e =>
        e.name.toLowerCase().includes(q) ||
        e.companies.some(n => n.toLowerCase().includes(q))
      );
    }
    const dir = uiState.sortDir, k = uiState.sortKey;
    rows = rows.slice().sort((a, b) => {
      let d = 0;
      if (k === 'name') d = a.name.localeCompare(b.name);
      else if (k === 'count') d = a.count - b.count;
      else if (k === 'leadCount') d = a.leadCount - b.leadCount;
      else if (k === 'sector') d = (a.topSectors[0] ? a.topSectors[0][0] : '').localeCompare(b.topSectors[0] ? b.topSectors[0][0] : '');
      return dir * d || a.name.localeCompare(b.name);
    });
    return rows;
  }

  function renderTable() {
    const tbody = document.getElementById('ai-tbody');
    const countEl = document.getElementById('ai-count-readout');
    if (!tbody) return;
    const rows = directoryRows();
    if (countEl) {
      const total = LIST.filter(e => e.count >= MIN_PORTFOLIO).length;
      countEl.textContent = 'Showing ' + rows.length + ' of ' + total + ' investors with ≥' + MIN_PORTFOLIO + ' portfolio companies';
    }
    tbody.innerHTML = rows.map(e => {
      const sectors = e.topSectors.map(([s, n]) =>
        '<span class="ai-sector" title="' + esc(s) + ' ×' + n + '">' + esc(s) + '</span>').join('');
      const notable = e.notable.map(n =>
        '<a class="ai-chip ai-chip-co" href="' + companyHref(n) + '" title="Open ' + esc(n) + '">' + esc(n) + '</a>').join('');
      const coinv = e.coInvestors.slice(0, 3).map(c =>
        '<button class="ai-chip ai-chip-inv" data-inv="' + esc(c.key) + '" title="' + esc(c.name) + ' — ' + c.overlap + ' shared companies">' + esc(c.name) + ' <span class="ai-x">×' + c.overlap + '</span></button>').join('');
      return '<tr class="ai-row' + (uiState.openKey === e.key ? ' ai-row-open' : '') + '" data-inv="' + esc(e.key) + '">' +
        '<td class="ai-td-name">' + esc(e.name) + '</td>' +
        '<td class="ai-td-num">' + e.count + '</td>' +
        '<td class="ai-td-num">' + (e.leadCount || '—') + '</td>' +
        '<td class="ai-td-sectors">' + sectors + '</td>' +
        '<td class="ai-td-chips">' + notable + '</td>' +
        '<td class="ai-td-chips">' + coinv + '</td>' +
        '</tr>';
    }).join('') || '<tr><td colspan="6" class="ai-empty">No investors match “' + esc(uiState.search) + '”.</td></tr>';

    // header sort indicators
    document.querySelectorAll('#ai-table th[data-sort]').forEach(th => {
      const active = th.dataset.sort === uiState.sortKey;
      th.classList.toggle('ai-th-active', active);
      th.querySelector('.ai-arrow').textContent = active ? (uiState.sortDir === -1 ? '▼' : '▲') : '';
    });
  }

  function renderDetail() {
    const panel = document.getElementById('ai-detail');
    if (!panel) return;
    const e = uiState.openKey && INDEX.get(uiState.openKey);
    if (!e) { panel.style.display = 'none'; panel.innerHTML = ''; return; }

    const sectors = e.topSectors.map(([s, n]) =>
      '<span class="ai-sector">' + esc(s) + ' ×' + n + '</span>').join('');
    const portfolio = e.companies.slice().sort().map(name => {
      const c = COMPANY_BY_NAME.get(name) || {};
      const led = e.leadSet.has(name);
      const meta = [c.sector, c.fundingStage, c.totalRaised].filter(Boolean).join(' · ');
      return '<a class="ai-port-card" href="' + companyHref(name) + '">' +
        '<span class="ai-port-name">' + esc(name) + (led ? ' <span class="ai-lead-badge">LEAD</span>' : '') + '</span>' +
        '<span class="ai-port-meta">' + esc(meta) + '</span></a>';
    }).join('');
    const coinv = e.coInvestors.map(c =>
      '<button class="ai-chip ai-chip-inv" data-inv="' + esc(c.key) + '">' + esc(c.name) + ' <span class="ai-x">×' + c.overlap + '</span></button>').join('') || '<span class="ai-empty">No co-investors on record.</span>';

    panel.innerHTML =
      '<div class="ai-detail-head">' +
        '<div>' +
          '<div class="ai-detail-name">' + esc(e.name) + '</div>' +
          '<div class="ai-detail-stats">' +
            '<span><strong>' + e.count + '</strong> portfolio companies</span>' +
            '<span><strong>' + e.leadCount + '</strong> as lead</span>' +
            sectors +
          '</div>' +
        '</div>' +
        '<button class="ai-detail-close" id="ai-detail-close" aria-label="Close detail panel">&times;</button>' +
      '</div>' +
      '<div class="ai-detail-label">PORTFOLIO</div>' +
      '<div class="ai-port-grid">' + portfolio + '</div>' +
      '<div class="ai-detail-label">TOP CO-INVESTORS</div>' +
      '<div class="ai-coinv-row">' + coinv + '</div>';
    panel.style.display = 'block';

    const close = document.getElementById('ai-detail-close');
    if (close) close.addEventListener('click', () => { uiState.openKey = null; renderDetail(); renderTable(); });
  }

  function openInvestor(key, viaChip) {
    if (!INDEX.has(key)) return;
    uiState.openKey = key;
    if (viaChip) {
      // "filter to" behavior: chip clicks narrow the table to that investor too
      const search = document.getElementById('ai-search');
      const e = INDEX.get(key);
      uiState.search = e.name;
      if (search) search.value = e.name;
    }
    renderTable();
    renderDetail();
    const panel = document.getElementById('ai-detail');
    if (panel && typeof panel.scrollIntoView === 'function') panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function initDirectory() {
    const section = document.getElementById('all-investors');
    if (!section) return;

    // hero stats for the section
    const totalEl = document.getElementById('ai-stat-total');
    const dirEl = document.getElementById('ai-stat-directory');
    const linksEl = document.getElementById('ai-stat-links');
    if (totalEl) totalEl.textContent = LIST.length.toLocaleString();
    if (dirEl) dirEl.textContent = LIST.filter(e => e.count >= MIN_PORTFOLIO).length.toLocaleString();
    if (linksEl) linksEl.textContent = LIST.reduce((s, e) => s + e.count, 0).toLocaleString();

    const search = document.getElementById('ai-search');
    if (search) search.addEventListener('input', () => { uiState.search = search.value; renderTable(); });

    document.querySelectorAll('#ai-table th[data-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const k = th.dataset.sort;
        if (uiState.sortKey === k) uiState.sortDir = -uiState.sortDir;
        else { uiState.sortKey = k; uiState.sortDir = (k === 'name' || k === 'sector') ? 1 : -1; }
        renderTable();
      });
    });

    // Delegated clicks: rows open the detail panel; co-investor chips jump +
    // filter; company chips are plain links (let them navigate).
    section.addEventListener('click', ev => {
      const chip = ev.target.closest('.ai-chip-inv');
      if (chip) { ev.stopPropagation(); openInvestor(chip.dataset.inv, true); return; }
      if (ev.target.closest('a')) return;
      const row = ev.target.closest('tr.ai-row');
      if (row) openInvestor(row.dataset.inv, false);
    });

    renderTable();

    // Deep link: investors.html#inv=<name or key>
    const m = (location.hash || '').match(/^#inv=(.+)$/);
    if (m) {
      const q = decodeURIComponent(m[1]).toLowerCase();
      const hit = LIST.find(e => e.key === q || e.name.toLowerCase() === q);
      if (hit) openInvestor(hit.key, false);
    }
  }

  // ─── BOOT ───

  function boot() {
    if (typeof COMPANIES === 'undefined') return;
    const { index, companyByName } = buildInvestorIndex(COMPANIES);
    INDEX = index;
    COMPANY_BY_NAME = companyByName;
    LIST = [...index.values()].sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
    window.INVESTOR_INDEX = INDEX;
    window.INVESTOR_LIST = LIST;
    initDirectory();
  }

  window.InvestorGraph = { buildInvestorIndex, stripAnnotations, hasLeadAnnotation, rawToKey };

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
    else boot();
  }
})();
