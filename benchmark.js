// Founder benchmark page — renders one company's Pulse signals against its bucket. Free, no login.
(function () {
  if (typeof PULSE_COMPANIES === 'undefined') return;
  const P = PULSE_COMPANIES;
  const $ = id => document.getElementById(id);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const fmt = n => (n === '' || n === null || n === undefined) ? '—' : Number(n).toLocaleString('en-US', { maximumFractionDigits: 1 });
  const monthLabel = m => { const [y, mo] = m.split('-'); return new Date(+y, +mo - 1, 1).toLocaleString('en-US', { month: 'short' }); };
  const names = Object.keys(P.companies).sort((a, b) => a.localeCompare(b));

  // search box
  const dl = $('bench-list');
  dl.innerHTML = names.map(n => `<option value="${esc(n)}"></option>`).join('');
  const params = new URLSearchParams(window.location.search);
  let q = params.get('company') || params.get('name') || '';
  if (params.get('slug')) { const s = params.get('slug').toLowerCase(); q = names.find(n => n.toLowerCase().replace(/[^a-z0-9]+/g, '-') === s) || q; }
  $('bench-search').value = q;
  $('bench-search').addEventListener('change', () => { const v = $('bench-search').value; if (P.companies[v]) { history.replaceState(null, '', '?company=' + encodeURIComponent(v)); render(v); } });
  $('bench-form').addEventListener('submit', e => { e.preventDefault(); $('bench-search').dispatchEvent(new Event('change')); });

  function spark(r, medianRoles) {
    const W = 520, H = 150, padL = 36, padR = 12, padT = 14, padB = 26;
    const vals = r.map(v => v === null ? null : Number(v));
    const nums = vals.filter(v => v !== null);
    if (!nums.length) return '';
    const lo = 0, hi = Math.max(...nums, medianRoles || 0) * 1.15 || 1;
    const y = v => padT + (H - padT - padB) * (1 - (v - lo) / (hi - lo));
    const x = i => padL + (W - padL - padR) * (r.length > 1 ? i / (r.length - 1) : 0.5);
    let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">`;
    for (let i = 0; i <= 2; i++) { const v = lo + (hi - lo) * i / 2; s += `<line x1="${padL}" x2="${W - padR}" y1="${y(v)}" y2="${y(v)}" stroke="rgba(255,255,255,0.08)"/><text x="${padL - 6}" y="${y(v) + 4}" text-anchor="end" fill="rgba(255,255,255,0.5)" font-size="10">${Math.round(v)}</text>`; }
    if (medianRoles) s += `<line x1="${padL}" x2="${W - padR}" y1="${y(medianRoles)}" y2="${y(medianRoles)}" stroke="#fbbf24" stroke-dasharray="4 4"/><text x="${W - padR}" y="${y(medianRoles) - 5}" text-anchor="end" fill="#fbbf24" font-size="10">bucket median ${Math.round(medianRoles)}</text>`;
    const pts = vals.map((v, i) => v === null ? null : `${x(i)},${y(v)}`).filter(Boolean).join(' ');
    s += `<polyline points="${pts}" fill="none" stroke="#4ade80" stroke-width="2.4"/>`;
    vals.forEach((v, i) => { if (v !== null) s += `<circle cx="${x(i)}" cy="${y(v)}" r="3.5" fill="#4ade80"/><text x="${x(i)}" y="${y(v) - 8}" text-anchor="middle" fill="#fff" font-size="10">${v}</text>`; });
    P.months.forEach((m, i) => { s += `<text x="${x(i)}" y="${H - 8}" text-anchor="middle" fill="rgba(255,255,255,0.55)" font-size="10">${monthLabel(m)}</text>`; });
    return s + '</svg>';
  }

  function render(name) {
    const c = P.companies[name];
    const el = $('bench-card');
    if (!c) { el.innerHTML = `<p style="color:rgba(255,255,255,0.6)">No company called “${esc(name)}” in the cohort. Try the search above, or <a href="mailto:contact@rationaloptimistsociety.com?subject=Add%20us%20to%20the%20Innovators%20League" style="color:var(--accent)">ask to be added</a>.</p>`; return; }
    const med = P.medians[c.b] || {};
    const r = c.r, now = r[r.length - 1], back = r.length >= 4 ? r[r.length - 4] : r[0];
    const growth = (now !== null && back) ? (now - back) / back * 100 : null;
    const ab = (c.m[c.m.length - 1] !== null && c.s[c.s.length - 1]) ? c.m[c.m.length - 1] / c.s[c.s.length - 1] : null;
    const rungNames = ['', 'Prototype', 'First unit / criticality', 'First paying customer', 'First factory / power to a load', 'At rate / commercial operation', 'Proven reliability'];
    const vs = (v, m, higherGood = true) => (v === null || m === null || m === undefined) ? '' : (v > m ? `<span class="pill ok">above bucket median ${fmt(m)}</span>` : v < m ? `<span class="pill warn">below bucket median ${fmt(m)}</span>` : `<span class="pill">at bucket median</span>`);
    const tiles = [
      { k: 'Open roles', v: now === null ? '—' : fmt(now), s: c.board ? `${growth === null ? '' : (growth >= 0 ? '+' : '') + fmt(growth) + '% over three months '}${vs(now, med.roles)}` : 'no public job board found' },
      { k: 'Atoms / bits', v: ab === null ? '—' : ab.toFixed(2), s: ab === null ? 'manufacturing vs software titles' : vs(ab, med.atoms_bits) },
      { k: 'Rank in bucket', v: c.rk ? `#${c.rk}` : '—', s: c.rk ? `of ${c.n} ${esc(c.b)} companies with a board, by three-month hiring growth` : `${esc(c.b)} — not ranked without a job board` },
      { k: 'Pulse score', v: c.sc !== null && c.sc !== undefined ? fmt(c.sc) : '—', s: '0–100: hiring momentum, capital recency, awards, milestones' },
      { k: 'Last capital event', v: c.cap || 'none on record', s: 'deals feed · Form D · VC portfolio pages' },
      { k: 'Last federal award', v: c.con || 'none on record', s: 'USAspending' },
      { k: 'Ladder rung', v: c.rung ? `${c.rung}` : '—', s: c.rung ? rungNames[c.rung] || '' : 'not yet placed — send us the evidence' },
      { k: 'Signals', v: [c.ff ? 'factory-coming' : null, c.atr ? 'about to raise' : null, c.atb ? 'about to build' : null].filter(Boolean).join(' · ') || 'none this month', s: 'derived from postings and events; a signal, not a verdict' },
    ];
    el.innerHTML = `
      <div class="bench-head"><div><p class="section-eyebrow">FOUNDER BENCHMARK · ${esc(P.months[P.months.length - 1])}</p><h2>${esc(name)}</h2><p>${esc(c.b)}${c.st ? ' · ' + esc(c.st) : ''} · <a href="company.html?name=${encodeURIComponent(name)}" style="color:var(--accent)">company profile →</a></p></div></div>
      <div class="pulse-tiles">${tiles.map(t => `<div class="pulse-tile"><div class="k">${esc(t.k)}</div><div class="v" style="font-size:22px">${t.v}</div><div class="s">${t.s}</div></div>`).join('')}</div>
      <h3 style="margin-top:26px">Open roles, month by month — against the ${esc(c.b)} median</h3>
      <div class="pulse-chart small">${spark(r, med.roles)}</div>
      <div class="bench-note"><strong>This is what investors, journalists and your peers see.</strong> It comes from your public job board and public filings, month-end snapshots, the same method for every company. Nobody can pay to change it. If something here is wrong or missing — a board we haven't found, a raise we missed, a milestone you've hit — tell us and we'll fix the record: <a href="mailto:contact@rationaloptimistsociety.com?subject=${encodeURIComponent('Pulse benchmark correction: ' + name)}" style="color:var(--accent)">correct this page</a>.</div>`;
    $('bench-poll-company').value = name;
  }

  if (q && P.companies[q]) render(q); else if (q) render(q);
  else $('bench-card').innerHTML = `<p style="color:rgba(255,255,255,0.6)">Type a company name above. ${fmt(names.length)} private hard-tech companies are in the cohort; ${fmt(Object.values(P.companies).filter(c => c.board).length)} have a public job board we track this month.</p>`;

  // Founder Poll — mailto form
  $('bench-poll').addEventListener('submit', e => {
    e.preventDefault();
    const f = e.target; const co = f.company.value || 'Unknown company';
    const lines = [
      `Company: ${co}`,
      `1. Months of runway today: ${f.q1.value}`,
      `2. Will you raise in the next 12 months? ${f.q2.value}`,
      `3. Headcount in 12 months vs today (%): ${f.q3.value}`,
      `4. Longest-lead-time input and its quoted lead time (weeks): ${f.q4.value}`,
      `5. The listed supplier you'll pay the most in the next 12 months: ${f.q5.value}`,
      `6. Date you expect your next Ladder rung: ${f.q6.value}`,
      `7. Biggest constraint on the next 12 months: ${f.q7.value}`,
      `Contact: ${f.email.value}`,
    ];
    window.location.href = 'mailto:contact@rationaloptimistsociety.com?subject=' + encodeURIComponent('Founder Poll: ' + co) + '&body=' + encodeURIComponent(lines.join('\n'));
  });
})();
