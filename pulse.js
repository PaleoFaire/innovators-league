// The Build-Out Pulse — page renderer. Reads PULSE_DATA from data/pulse_auto.js; no chart library.
(function () {
  if (typeof PULSE_DATA === 'undefined') return;
  const D = PULSE_DATA;
  const hist = D.history.filter(r => r.hiring_diffusion !== '' && r.hiring_diffusion !== null);
  const latest = D.latest;
  const $ = id => document.getElementById(id);
  const fmt = n => (n === '' || n === null || n === undefined) ? '—' : Number(n).toLocaleString('en-US', { maximumFractionDigits: 1 });
  const monthName = m => { const [y, mo] = m.split('-'); return new Date(+y, +mo - 1, 1).toLocaleString('en-US', { month: 'short', year: 'numeric' }); };
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  // ── headline ──
  $('pulse-month').textContent = monthName(latest.month) + (latest.is_nowcast ? ' (nowcast)' : '');
  const h = Number(latest.hiring_diffusion);
  const prevRow = hist.length > 1 ? hist[hist.length - 2] : null;
  const dir = prevRow ? (h > Number(prevRow.hiring_diffusion) ? 'up from ' : h < Number(prevRow.hiring_diffusion) ? 'down from ' : 'unchanged from ') + fmt(prevRow.hiring_diffusion) : '';
  $('pulse-headline').textContent = `The Pulse is ${fmt(h)} — ${h > 50 ? 'expansion' : h < 50 ? 'contraction' : 'neutral'}${dir ? ', ' + dir : ''}`;

  const tiles = [
    { k: 'Hiring diffusion', v: fmt(latest.hiring_diffusion), cls: h > 50 ? 'up' : 'down', s: `90% interval ${fmt(latest.hiring_ci_lo)}–${fmt(latest.hiring_ci_hi)} · panel ${latest.hiring_panel}` },
    { k: 'Breadth', v: `${fmt(latest.share_up_pct)}% up`, s: `${latest.hiring_up} up · ${latest.hiring_flat} flat · ${latest.hiring_down} down${latest.board_checks ? ' · ' + latest.board_checks + ' held for board check' : ''}` },
    { k: 'Open roles (panel)', v: fmt(latest.open_roles), s: `${latest.roles_mom_pct > 0 ? '+' : ''}${fmt(latest.roles_mom_pct)}% month on month` },
    { k: 'Atoms / bits', v: fmt(latest.atoms_bits_ratio), s: `${fmt(latest.manufacturing_roles)} manufacturing + ${fmt(latest.hardware_roles)} hardware-engineering roles vs ${fmt(latest.software_roles)} software` },
    { k: 'Capital breadth', v: fmt(latest.capital_diffusion_covered), s: `${latest.capital_events_3m} companies raised in 3 months · covered panel ${latest.capital_panel}` },
    { k: 'Contracts breadth', v: fmt(latest.contracts_diffusion_covered), s: `${latest.contracts_events_3m} new federal awards in 3 months · panel ${latest.contracts_panel}` },
    { k: 'Factory-coming flags', v: fmt(latest.factory_flags), s: 'senior manufacturing / plant / facilities roles posted this month' },
    { k: 'Universe', v: fmt(D.universe), s: `private, active, in-lane companies of ${fmt(D.companies_total)} tracked` },
    { k: 'Cohort mortality', v: (D.mortality && D.mortality.confirmed_rate_pct != null) ? fmt(D.mortality.confirmed_rate_pct) + '%' : '—', s: `${D.mortality ? D.mortality.liveness_confirmed_dead_or_acquired : '—'} confirmed dead or acquired of ${D.mortality ? D.mortality.liveness_checked : '—'} checked` },
  ];
  $('pulse-tiles').innerHTML = tiles.map(t => `<div class="pulse-tile"><div class="k">${esc(t.k)}</div><div class="v ${t.cls || ''}">${esc(t.v)}</div><div class="s">${esc(t.s)}</div></div>`).join('');

  // ── charts (inline SVG) ──
  function barChart(el, rows, key, opts) {
    const W = 880, H = 260, padL = 44, padR = 16, padT = 18, padB = 34;
    const vals = rows.map(r => Number(r[key]));
    const lo = opts.min ?? Math.min(...vals), hi = opts.max ?? Math.max(...vals);
    const y = v => padT + (H - padT - padB) * (1 - (v - lo) / (hi - lo || 1));
    const bw = (W - padL - padR) / rows.length;
    let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${esc(opts.label || '')}">`;
    s += '<g class="grid">';
    for (let i = 0; i <= 4; i++) { const v = lo + (hi - lo) * i / 4; s += `<line x1="${padL}" x2="${W - padR}" y1="${y(v)}" y2="${y(v)}"/><text class="axis" x="${padL - 6}" y="${y(v) + 4}" text-anchor="end" fill="rgba(255,255,255,0.55)" font-size="11">${fmt(v)}</text>`; }
    s += '</g>';
    if (opts.ref !== undefined) s += `<line x1="${padL}" x2="${W - padR}" y1="${y(opts.ref)}" y2="${y(opts.ref)}" stroke="#fbbf24" stroke-dasharray="4 4" stroke-width="1"/>`;
    rows.forEach((r, i) => {
      const v = Number(r[key]); const x = padL + i * bw + bw * 0.15; const w = bw * 0.7;
      const top = Math.min(y(v), y(opts.ref !== undefined ? opts.ref : lo)); const hgt = Math.abs(y(v) - y(opts.ref !== undefined ? opts.ref : lo));
      const col = opts.ref !== undefined ? (v >= opts.ref ? '#4ade80' : '#f87171') : '#60a5fa';
      s += `<rect x="${x}" y="${top}" width="${w}" height="${Math.max(hgt, 1)}" rx="3" fill="${col}" opacity="${r.is_nowcast ? 0.55 : 0.9}"/>`;
      if (opts.ci && r.hiring_ci_lo !== '' && r.hiring_ci_hi !== '') { const cx = x + w / 2; s += `<line x1="${cx}" x2="${cx}" y1="${y(Number(r.hiring_ci_lo))}" y2="${y(Number(r.hiring_ci_hi))}" stroke="rgba(255,255,255,0.55)" stroke-width="1.5"/><line x1="${cx - 5}" x2="${cx + 5}" y1="${y(Number(r.hiring_ci_lo))}" y2="${y(Number(r.hiring_ci_lo))}" stroke="rgba(255,255,255,0.55)"/><line x1="${cx - 5}" x2="${cx + 5}" y1="${y(Number(r.hiring_ci_hi))}" y2="${y(Number(r.hiring_ci_hi))}" stroke="rgba(255,255,255,0.55)"/>`; }
      s += `<text x="${x + w / 2}" y="${y(v) - 6}" text-anchor="middle" fill="#fff" font-size="12" font-weight="600">${fmt(v)}</text>`;
      s += `<text x="${x + w / 2}" y="${H - 12}" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="11">${monthName(r.month).replace(' 20', ' ’')}${r.is_nowcast ? '*' : ''}</text>`;
    });
    s += '</svg>';
    el.innerHTML = s;
  }
  function lineChart(el, rows, series, opts) {
    const W = 440, H = 220, padL = 46, padR = 12, padT = 16, padB = 30;
    const all = series.flatMap(sr => rows.map(r => Number(r[sr.key])));
    const lo = opts.min ?? Math.min(...all) * 0.95, hi = Math.max(...all) * 1.05;
    const y = v => padT + (H - padT - padB) * (1 - (v - lo) / (hi - lo || 1));
    const x = i => padL + (W - padL - padR) * (rows.length > 1 ? i / (rows.length - 1) : 0.5);
    let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg"><g class="grid">`;
    for (let i = 0; i <= 3; i++) { const v = lo + (hi - lo) * i / 3; s += `<line x1="${padL}" x2="${W - padR}" y1="${y(v)}" y2="${y(v)}"/><text x="${padL - 6}" y="${y(v) + 4}" text-anchor="end" fill="rgba(255,255,255,0.55)" font-size="10">${fmt(Math.round(v))}</text>`; }
    s += '</g>';
    series.forEach(sr => {
      const pts = rows.map((r, i) => `${x(i)},${y(Number(r[sr.key]))}`).join(' ');
      s += `<polyline points="${pts}" fill="none" stroke="${sr.color}" stroke-width="2.2"/>`;
      rows.forEach((r, i) => { s += `<circle cx="${x(i)}" cy="${y(Number(r[sr.key]))}" r="3" fill="${sr.color}"/>`; });
      const last = rows[rows.length - 1];
      s += `<text x="${x(rows.length - 1) - 4}" y="${y(Number(last[sr.key])) - 8}" text-anchor="end" fill="${sr.color}" font-size="11">${esc(sr.name)} ${fmt(last[sr.key])}</text>`;
    });
    rows.forEach((r, i) => { s += `<text x="${x(i)}" y="${H - 10}" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="10">${monthName(r.month).slice(0, 3)}</text>`; });
    s += '</svg>';
    el.innerHTML = s;
  }
  barChart($('pulse-chart-diffusion'), hist, 'hiring_diffusion', { min: 30, max: 80, ref: 50, ci: true, label: 'Hiring diffusion by month with 90% bootstrap intervals' });
  lineChart($('pulse-chart-roles'), hist, [{ key: 'open_roles', name: 'roles', color: '#60a5fa' }], {});
  lineChart($('pulse-chart-ab'), hist, [{ key: 'mfg_roles', name: 'atoms', color: '#f87171' }, { key: 'sw_roles', name: 'bits', color: '#a3a3a3' }], { min: 0 });

  // ── buckets ──
  const bk = D.latest_buckets.slice().sort((a, b) => b.open_roles - a.open_roles);
  $('pulse-bucket-table').innerHTML = `<table class="pulse-table"><thead><tr><th>Bucket</th><th>Panel</th><th>Up</th><th>Down</th><th>Diffusion</th><th>Open roles</th><th>Atoms / bits</th><th>Senior mfg roles</th><th>Status</th></tr></thead><tbody>` +
    bk.map(b => `<tr class="${b.sufficient ? '' : 'insufficient'}"><td>${esc(b.bucket)}</td><td class="num">${b.panel}</td><td class="num">${b.up}</td><td class="num">${b.down}</td><td class="num"><strong>${fmt(b.hiring_diffusion)}</strong></td><td class="num">${fmt(b.open_roles)}</td><td class="num">${b.atoms_bits !== '' && b.atoms_bits !== undefined ? fmt(b.atoms_bits) : '—'}</td><td class="num">${b.senior_roles}</td><td>${b.sufficient ? '<span class="pill ok">sufficient</span>' : '<span class="pill warn">insufficient · n &lt; 20</span>'}</td></tr>`).join('') + '</tbody></table>';

  // ── movers + flags ──
  const mv = D.movers || { up: [], factory_flags: [] };
  $('pulse-movers-up').innerHTML = `<h3>Fastest expansion</h3><table class="pulse-table"><thead><tr><th>Company</th><th>Bucket</th><th>Roles</th><th>Change</th></tr></thead><tbody>` +
    mv.up.map(m => `<tr><td>${esc(m.company)}</td><td>${esc(m.bucket)}</td><td class="num">${m.roles_prev} → ${m.roles_now}</td><td class="num" style="color:#4ade80">+${fmt(m.change_pct)}%</td></tr>`).join('') + '</tbody></table>';
  $('pulse-flags').innerHTML = `<h3>Factory coming — senior manufacturing hires this month</h3>` + (mv.factory_flags && mv.factory_flags.length ? `<ul class="flag-list">${mv.factory_flags.map(c => `<li>${esc(c)}<span>VP / director / plant / facilities role posted</span></li>`).join('')}</ul>` : '<p style="color:rgba(255,255,255,0.5)">None this month.</p>');

  // ── states ──
  const st = D.states || [];
  $('pulse-state-table').innerHTML = `<table class="pulse-table"><thead><tr><th>State</th><th>Open roles</th><th>Atoms (mfg + hardware)</th><th>Software</th><th>Atoms / bits</th></tr></thead><tbody>` +
    st.map(s => `<tr><td>${esc(s.state)}</td><td class="num">${fmt(s.roles)}</td><td class="num">${fmt(s.atoms ?? s.mfg)}</td><td class="num">${fmt(s.sw)}</td><td class="num">${s.sw ? ((s.atoms ?? s.mfg) / s.sw).toFixed(2) : '—'}</td></tr>`).join('') + '</tbody></table>';

  // ── scores ──
  const sc = D.scores || [];
  $('pulse-score-table').innerHTML = `<table class="pulse-table"><thead><tr><th>#</th><th>Company</th><th>Bucket</th><th>Score</th><th>Open roles</th><th>Last capital event</th><th>Last federal award</th></tr></thead><tbody>` +
    sc.map((r, i) => `<tr><td class="num">${i + 1}</td><td>${esc(r.company)}</td><td>${esc(r.bucket)}</td><td class="num"><strong>${fmt(r.score)}</strong></td><td class="num">${r.roles}</td><td>${r.last_capital || '—'}</td><td>${r.last_contract || '—'}</td></tr>`).join('') + '</tbody></table>';

  // ── method ──
  const t = D.thresholds || {}, w = D.weights || {};
  const comp = D.composition || {}; const rev = D.revisions || []; const checks = D.board_checks || [];
  const compRow = (title, obj) => obj ? `<p><strong>${title}:</strong> ${Object.entries(obj).map(([k, v]) => `${esc(k)} ${v}`).join(' · ')}</p>` : '';
  $('pulse-method-box').innerHTML = `
    <p><strong>Method v${esc(D.method_version || '1.1')} · taxonomy v${esc(D.taxonomy_version || '1.1')}.</strong> Changes are logged in <a href="data/pulse/CHANGELOG.md" style="color:var(--accent)">CHANGELOG.md</a>; the studies are pre-registered in <a href="data/pulse/PREREGISTRATION.md" style="color:var(--accent)">PREREGISTRATION.md</a>; data access is described in <a href="data/pulse/api/README.md" style="color:var(--accent)">api/README.md</a>.</p>
    <p><strong>Universe.</strong> ${fmt(D.universe)} private, active US hard-tech companies inside the build-out (nuclear, power and grid, defence, space and aerospace, chips and quantum, autonomy and robotics, manufacturing and materials) out of ${fmt(D.companies_total)} tracked. Public, dead and acquired companies leave the panel and stay in the history.</p>
    <p><strong>Hiring.</strong> Open roles from public job boards, month-end snapshots. Constant panel. Up = +${Math.round((t.up_pct || 0.1) * 100)}% or +${t.up_abs || 3} roles; down = the reverse. Diffusion = 50 + (share up − share down) × 50. Postings older than ${t.stale_days || 365} days are treated as ghosts. The atoms/bits ratio divides manufacturing, technician and production titles by software, data and product titles.</p>
    <p><strong>Capital and contracts.</strong> One dated event per company-month, merged from the deals feed, SEC Form D, VC portfolio first-funded dates and company announcements (${Object.entries(D.capital_sources || {}).map(([k, v]) => `${k} ${v}`).join(', ')}); federal awards from USAspending. On the covered panel: positive = an event in the trailing three months, negative = none in twelve.</p>
    <p><strong>Milestones and footprint.</strong> Confirmed Ladder rung changes and facility events only. Unconfirmed extractions sit in a review queue (${fmt(D.review_queue_size)} items today) and never count.</p>
    <p><strong>Composite.</strong> Weights hiring ${w.hiring}, capital ${w.capital}, contracts ${w.contracts}, milestones ${w.milestones}, footprint ${w.footprint}, renormalised over live components. Until milestones are logged, the headline is the hiring diffusion; the composite is shown for the shadow period only.</p>
    <p><strong>Board-change guard.</strong> A company whose count collapses from ≥${(t.collapse_from || 20)} roles to ≤${(t.collapse_to || 3)}, or jumps the reverse way, is held out of that month's panel until a human confirms it (${checks.length} held this month${checks.length ? ': ' + checks.map(c => esc(c.company)).join(', ') : ''}). A feed failure is never printed as a layoff.</p>
    <p><strong>Panel composition this month.</strong></p>${compRow('By funding stage', comp.by_stage)}${compRow('By founding year', comp.by_founded)}${compRow('By state', comp.by_state)}
    <p><strong>Revisions.</strong> The current month is a nowcast and is recomputed at month-end. First prints are kept beside revised values${rev.length ? ` — ${rev.length} logged: ` + rev.map(r => `${esc(r.month)} ${fmt(r.first_print)} → ${fmt(r.revised)} (${esc(r.reason)})`).join('; ') : ''}. Never included: stock prices, news-mention counts, anything a company paid for. Every founder's own benchmark is free at <a href="benchmark.html" style="color:var(--accent)">benchmark.html</a>.</p>
    <p style="margin:0;color:rgba(255,255,255,0.45)">Generated ${esc(D.generated)}. Coverage today: ${fmt(latest.hiring_panel)} companies on the hiring panel; ${fmt(D.discovered_boards_high)} additional job boards discovered and queued for the next sync.</p>`;
})();

// ── Intelligence layer (calc_pulse_intel.py) ──
(function () {
  if (typeof PULSE_DATA === 'undefined' || !PULSE_DATA.intel) return;
  const I = PULSE_DATA.intel;
  const $ = id => document.getElementById(id);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const fmt = n => (n === '' || n === null || n === undefined) ? '—' : Number(n).toLocaleString('en-US', { maximumFractionDigits: 1 });
  if ($('pulse-about-build')) $('pulse-about-build').innerHTML = `<h3>About to build — senior manufacturing hires + rising roles</h3><table class="pulse-table"><thead><tr><th>Company</th><th>Bucket</th><th>Senior mfg roles open</th><th>Roles</th><th>Last capital event</th></tr></thead><tbody>` +
    (I.about_to_build || []).slice(0, 12).map(x => `<tr><td>${esc(x.company)}</td><td>${esc(x.bucket)}</td><td class="num">${x.senior_roles_open}</td><td class="num">${x.roles_prev} → ${x.roles_now}</td><td>${x.last_capital_event || '<span class="pill warn">none on record</span>'}</td></tr>`).join('') + '</tbody></table>';
  if ($('pulse-about-raise')) $('pulse-about-raise').innerHTML = `<h3>About to raise — roles up ≥30% in three months, no round in 12</h3><table class="pulse-table"><thead><tr><th>Company</th><th>Bucket</th><th>Roles 3m ago → now</th><th>Growth</th><th>Last capital event</th></tr></thead><tbody>` +
    (I.about_to_raise || []).slice(0, 12).map(x => `<tr><td>${esc(x.company)}</td><td>${esc(x.bucket)}</td><td class="num">${x.roles_3m_ago} → ${x.roles_now}</td><td class="num" style="color:#4ade80">+${fmt(x.growth_pct)}%</td><td>${x.last_capital_event || '<span class="pill warn">none on record</span>'}</td></tr>`).join('') + `</tbody></table><p style="font-size:12px;color:rgba(255,255,255,0.5);margin-top:8px">Runway stress (roles down ≥30% in three months, no round in 18): <strong style="color:#f87171">${I.runway_stress_count}</strong> companies — names on request for paying tiers, never on the free page.</p>`;
  if ($('pulse-portfolio')) $('pulse-portfolio').innerHTML = `<h3>Portfolio Pulse — tracked VC portfolios run through the same diffusion</h3><p style="font-size:12px;color:rgba(255,255,255,0.5);margin:4px 0 8px">Funds with at least five in-lane portfolio companies on the hiring panel. Panels widen from October as discovered job boards land.</p><table class="pulse-table"><thead><tr><th>Fund</th><th>In-lane tracked</th><th>On panel</th><th>Diffusion</th><th>Roles</th><th>Atoms/bits</th><th>Raised in 3m</th><th>Factory flags</th></tr></thead><tbody>` +
    (I.portfolio_pulse || []).map(f => `<tr><td>${esc(f.fund)}</td><td class="num">${f.tracked_in_lane}</td><td class="num">${f.on_hiring_panel}</td><td class="num"><strong>${fmt(f.diffusion)}</strong></td><td class="num">${f.roles_prev} → ${f.roles_now}</td><td class="num">${fmt(f.atoms_bits)}</td><td class="num">${f.raised_last_3m}</td><td>${(f.factory_flags || []).map(esc).join(', ') || '—'}</td></tr>`).join('') + '</tbody></table>';
  const st = I.study_hiring_before_raise;
  if ($('pulse-study') && st) $('pulse-study').innerHTML = `<h3>Does hiring precede raising?</h3><p style="font-size:12px;color:rgba(255,255,255,0.5);margin:4px 0 8px">${esc(st.definition)} Window ${esc(st.window)}. Small n; re-run monthly, failures published.</p><table class="pulse-table"><thead><tr><th>Group</th><th>n</th><th>Median 3-month role growth</th><th>Share up ≥30%</th><th>Share down</th></tr></thead><tbody>` +
    ['raisers', 'others'].map(k => `<tr><td>${k}</td><td class="num">${st[k].n}</td><td class="num">${fmt(st[k].median_growth_pct)}%</td><td class="num">${fmt(st[k].share_up_30pct)}%</td><td class="num">${fmt(st[k].share_down)}%</td></tr>`).join('') + '</tbody></table>';
  if ($('pulse-exposure')) $('pulse-exposure').innerHTML = `<h3>Pulse-to-ticker (v0: bucket level)</h3><p style="font-size:12px;color:rgba(255,255,255,0.5);margin:4px 0 8px">Each bucket's private-cohort diffusion beside the listed names in that bucket of the Build-Out Index. v1 replaces buckets with the Supplier Map from the visits.</p><table class="pulse-table"><thead><tr><th>Bucket</th><th>Panel</th><th>Diffusion</th><th>Open roles</th><th>Listed names</th></tr></thead><tbody>` +
    (I.pulse_to_ticker_v0 || []).map(e => `<tr class="${e.sufficient ? '' : 'insufficient'}"><td>${esc(e.bucket)}</td><td class="num">${e.panel}</td><td class="num"><strong>${fmt(e.diffusion)}</strong></td><td class="num">${fmt(e.open_roles)}</td><td>${(e.listed_names_v0 || []).join(', ') || '—'}</td></tr>`).join('') + '</tbody></table>';
})();
