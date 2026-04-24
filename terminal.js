/**
 * The Terminal — integrated Bloomberg-style workspace
 *
 * Aggregates the most actionable signals across all pipelines into one
 * screen: "What do I do today" panel + daily feed + skills sidebar +
 * alerts + watchlist.
 *
 * Reads from multiple _auto.js globals with defensive fallbacks — any
 * missing feed degrades gracefully without breaking the page.
 */

(function () {
  'use strict';

  const esc = s => String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

  function daysAgo(ds) {
    if (!ds) return '';
    const d = new Date(String(ds).replace(' ', 'T'));
    if (isNaN(d)) return '';
    const days = Math.floor((Date.now() - d) / 86400000);
    if (days < 0) return 'upcoming';
    if (days === 0) return 'today';
    if (days === 1) return '1d ago';
    if (days < 30) return days + 'd ago';
    return Math.floor(days / 30) + 'mo ago';
  }

  function greet() {
    const h = new Date().getHours();
    const name = (window.TILAuth && TILAuth.currentUser && TILAuth.currentUser.email)
      ? TILAuth.currentUser.email.split('@')[0]
      : null;
    const salutation =
      h < 12 ? 'Good morning' :
      h < 17 ? 'Good afternoon' :
      'Good evening';
    const h1 = document.getElementById('term-greeting-h1');
    if (h1) h1.textContent = salutation + (name ? ', ' + name : '') + '.';
    const dateEl = document.getElementById('term-date');
    if (dateEl) {
      dateEl.textContent = new Date().toLocaleDateString('en-US', {
        weekday: 'long', month: 'long', day: 'numeric',
      });
    }
  }

  // ── Top-bar quick stats ───────────────────────────────────────────────────

  function renderQuickStats() {
    // Signals today: count of items in last 72h across a few feeds
    let signals = 0;
    const newsFeed = window.NEWS_SIGNALS && window.NEWS_SIGNALS.items;
    if (Array.isArray(newsFeed)) {
      signals += newsFeed.filter(n => {
        const d = new Date(n.date || n.publishedAt || 0);
        return !isNaN(d) && (Date.now() - d) < 3 * 86400000;
      }).length;
    }
    // Fall back to counting form D filings if news is sparse
    const fd = window.FORM_D_FILINGS && window.FORM_D_FILINGS.filings;
    if (Array.isArray(fd)) signals += fd.length;
    const signalsEl = document.getElementById('term-qs-signals');
    if (signalsEl) signalsEl.textContent = signals || '—';

    // Actively raising: Form D count
    const raising = (window.FORM_D_FILINGS && window.FORM_D_FILINGS.total_filings) || 0;
    const rEl = document.getElementById('term-qs-raising');
    if (rEl) rEl.textContent = raising;

    // Queue MW
    const mw = (window.INTERCONNECTION_QUEUE_AUTO && window.INTERCONNECTION_QUEUE_AUTO.summary && window.INTERCONNECTION_QUEUE_AUTO.summary.total_mw) || 0;
    const mwEl = document.getElementById('term-qs-mw');
    if (mwEl) mwEl.textContent = mw >= 1000 ? (mw / 1000).toFixed(1) + 'GW' : mw + 'MW';

    // Watchlist from localStorage
    const wl = getWatchlist();
    const wlEl = document.getElementById('term-qs-watch');
    if (wlEl) wlEl.textContent = wl.length;
  }

  // ── Watchlist (left column) ──────────────────────────────────────────────

  function getWatchlist() {
    try {
      return JSON.parse(localStorage.getItem('til_watchlist') || '[]');
    } catch (e) {
      return [];
    }
  }

  function renderWatchlist() {
    const ul = document.getElementById('term-watchlist-ul');
    if (!ul) return;
    const wl = getWatchlist();
    if (wl.length === 0) return; // keep the empty state
    ul.innerHTML = wl.map(co => {
      // Check for recent signals on this company
      const hotTag = companyHasRecentSignal(co)
        ? '<span class="term-watch-sig hot">● HOT</span>'
        : '<span class="term-watch-sig">—</span>';
      return '<li class="term-watch-item">' +
        '<a href="company.html?c=' + encodeURIComponent(co) + '" class="term-watch-co">' + esc(co) + '</a>' +
        hotTag +
      '</li>';
    }).join('');
  }

  function companyHasRecentSignal(name) {
    const fd = window.FORM_D_FILINGS && window.FORM_D_FILINGS.filings;
    if (Array.isArray(fd) && fd.some(f => f.company === name)) return true;
    const dep = window.DECEPTION_SCORES_AUTO && window.DECEPTION_SCORES_AUTO.scored_calls;
    if (Array.isArray(dep) && dep.some(d => d.company === name && d.composite_score >= 60)) return true;
    const wc = window.WEBSITE_CHANGES_AUTO && window.WEBSITE_CHANGES_AUTO.changes;
    if (Array.isArray(wc) && wc.some(c => c.company === name)) return true;
    return false;
  }

  // ── Today's actions (center column, top) ─────────────────────────────────

  function renderTodayActions() {
    const body = document.getElementById('term-today-body');
    if (!body) return;
    const actions = buildTodayActions();
    if (actions.length === 0) {
      body.innerHTML = '<p style="color:rgba(255,255,255,0.4); font-size:13px;">No specific actions surfaced today. Check back later.</p>';
      return;
    }
    body.innerHTML = actions.map(a => {
      return '<div class="term-action ' + esc(a.kind || '') + '">' +
        '<div class="term-action-head">' +
          '<span class="term-action-type">' + esc(a.type) + '</span>' +
          '<span class="term-action-time">' + esc(a.time) + '</span>' +
        '</div>' +
        '<div class="term-action-headline">' + esc(a.headline) + '</div>' +
        '<div class="term-action-cta">' + a.cta + '</div>' +
        (a.href ? '<a href="' + esc(a.href) + '" class="term-action-btn">' + esc(a.btn || 'Open →') + '</a>' : '') +
      '</div>';
    }).join('');
  }

  function buildTodayActions() {
    const out = [];
    // 1. Top-flagged earnings-call deception score
    const dep = window.DECEPTION_SCORES_AUTO && window.DECEPTION_SCORES_AUTO.scored_calls;
    if (Array.isArray(dep) && dep.length > 0 && dep[0].composite_score >= 60) {
      const top = dep[0];
      out.push({
        kind: top.composite_score >= 75 ? 'risk' : 'urgent',
        type: 'Earnings deception alert',
        time: top.date,
        headline: top.company + ' (' + top.ticker + ') scored ' + top.composite_score + ' on the deception detector',
        cta: '<strong>Why it matters:</strong> ' + top.company + "'s " + top.quarter + ' call shows elevated hedge density, self-avoidance, and topic-avoidance. Flagged as <strong>' + (top.flag_level === 'high_alert' ? 'HIGH ALERT' : 'suspicious') + '</strong>.',
        href: 'earnings-signals.html#deception-detector-section',
        btn: 'View full score →',
      });
    }
    // 2. Active Form D raisers
    const fd = (window.FORM_D_FILINGS && window.FORM_D_FILINGS.filings) || [];
    if (fd.length > 0) {
      const top = fd.slice(0, 3);
      out.push({
        kind: 'urgent',
        type: 'Active raisers',
        time: 'last 60d',
        headline: top.length + ' companies filed Form D in the last 60 days',
        cta: '<strong>Who:</strong> ' + top.map(f => f.company).join(' · ') + '. Cold email templates ready in the Playbook.',
        href: 'signals.html#form-d',
        btn: 'See all filings →',
      });
    }
    // 3. DSCA FMS deal this week with tracked company named
    const dsca = (window.DSCA_FMS_AUTO && window.DSCA_FMS_AUTO.notifications) || [];
    const dscaWithMatch = dsca.filter(n => (n.matched_companies || []).length > 0);
    if (dscaWithMatch.length > 0) {
      const top = dscaWithMatch[0];
      out.push({
        kind: '',
        type: 'Defense export signal',
        time: top.notification_date,
        headline: top.country + ' · ' + top.article + ' (' + (top.value_usd_m >= 1000 ? '$' + (top.value_usd_m / 1000).toFixed(1) + 'B' : '$' + top.value_usd_m + 'M') + ')',
        cta: '<strong>Named subs in package:</strong> ' + top.matched_companies.map(c => c).join(' · ') + '.',
        href: 'govradar.html#dsca-fms-section',
        btn: 'Read notification →',
      });
    }
    // 4. Lobbying spend acceleration
    const lob = (window.LOBBYING_AUTO && window.LOBBYING_AUTO.by_company) || [];
    const accel = lob.filter(r => r.qoq_pct > 25).slice(0, 1);
    if (accel.length > 0) {
      const r = accel[0];
      out.push({
        kind: 'urgent',
        type: 'Policy pipeline',
        time: 'this quarter',
        headline: r.company + ' lobbying spend +' + r.qoq_pct.toFixed(0) + '% QoQ ($' + ((r.total_spend || 0) / 1000).toFixed(0) + 'K total)',
        cta: '<strong>Issues:</strong> ' + (r.issues || []).slice(0, 4).join(' · ') + '. Usually precedes a regulatory or contract win.',
        href: 'govradar.html#lobbying-section',
        btn: 'See all →',
      });
    }
    // 5. Website change detected
    const wc = (window.WEBSITE_CHANGES_AUTO && window.WEBSITE_CHANGES_AUTO.changes) || [];
    if (wc.length > 0) {
      const first = wc.slice(0, 3);
      out.push({
        kind: '',
        type: 'Website drift',
        time: 'last 90d',
        headline: wc.length + ' tracked companies changed their website recently',
        cta: '<strong>First three:</strong> ' + first.map(c => c.company).join(' · ') + '. Compare with Wayback to find exec moves, pivots, customer wins.',
        href: 'signals.html#website-changes',
        btn: 'View diffs →',
      });
    }
    return out.slice(0, 4); // cap to 4 cards
  }

  // ── The daily feed (center column) ───────────────────────────────────────

  function renderFeed() {
    const body = document.getElementById('term-feed-body');
    if (!body) return;
    const items = buildFeedItems();
    if (items.length === 0) {
      body.innerHTML = '<p style="color:rgba(255,255,255,0.4); font-size:13px;">No feed items.</p>';
      return;
    }
    body.innerHTML = items.map(it => {
      return '<div class="term-feed-item">' +
        '<div class="term-feed-icon" style="background:' + it.iconBg + ';">' + it.icon + '</div>' +
        '<div class="term-feed-body">' +
          '<div class="term-feed-title"><a href="' + esc(it.href) + '">' + esc(it.title) + '</a></div>' +
          '<div class="term-feed-meta">' + esc(it.meta) + '</div>' +
        '</div>' +
      '</div>';
    }).join('');
  }

  function buildFeedItems() {
    const items = [];
    const fd = (window.FORM_D_FILINGS && window.FORM_D_FILINGS.filings) || [];
    fd.slice(0, 4).forEach(f => {
      items.push({
        icon: '$',
        iconBg: 'rgba(34,197,94,0.2)',
        title: f.company + ' filed Form D for ' + (f.offering_amount || 'undisclosed'),
        meta: 'Form D · ' + (f.filed_date ? f.filed_date.slice(0, 10) + ' · ' + daysAgo(f.filed_date) : ''),
        href: 'signals.html#form-d',
      });
    });
    const dsca = (window.DSCA_FMS_AUTO && window.DSCA_FMS_AUTO.notifications) || [];
    dsca.slice(0, 3).forEach(d => {
      items.push({
        icon: '🎖',
        iconBg: 'rgba(239,68,68,0.18)',
        title: d.country + ' · ' + d.article,
        meta: 'DSCA FMS · $' + (d.value_usd_m >= 1000 ? (d.value_usd_m / 1000).toFixed(1) + 'B' : d.value_usd_m + 'M') + ' · ' + d.notification_date,
        href: 'govradar.html#dsca-fms-section',
      });
    });
    const wc = (window.WEBSITE_CHANGES_AUTO && window.WEBSITE_CHANGES_AUTO.changes) || [];
    wc.slice(0, 2).forEach(c => {
      items.push({
        icon: '🕵',
        iconBg: 'rgba(59,130,246,0.18)',
        title: c.company + ' website updated',
        meta: 'Wayback diff · ' + c.url,
        href: 'signals.html#website-changes',
      });
    });
    const queue = (window.INTERCONNECTION_QUEUE_AUTO && window.INTERCONNECTION_QUEUE_AUTO.entries) || [];
    queue.slice(0, 2).forEach(q => {
      items.push({
        icon: '⚡',
        iconBg: 'rgba(134,239,172,0.22)',
        title: q.customer + ' · ' + (q.mw_size >= 1000 ? (q.mw_size / 1000).toFixed(1) + ' GW' : q.mw_size + ' MW') + ' queue filing',
        meta: q.rto + ' · ' + (q.county ? (q.county + ', ') : '') + q.state + ' · ' + q.queue_date,
        href: 'power-grid.html',
      });
    });
    return items;
  }

  // ── Deception flags (center column, bottom) ─────────────────────────────

  function renderDeception() {
    const body = document.getElementById('term-deception-body');
    if (!body) return;
    const scored = (window.DECEPTION_SCORES_AUTO && window.DECEPTION_SCORES_AUTO.scored_calls) || [];
    const flagged = scored.filter(s => s.flag_level === 'high_alert' || s.flag_level === 'suspicious');
    if (flagged.length === 0) {
      body.innerHTML = '<p style="color:rgba(255,255,255,0.4); font-size:12px;">All recent earnings calls scoring clean.</p>';
      return;
    }
    body.innerHTML = flagged.slice(0, 4).map(s => {
      const col = s.flag_level === 'high_alert' ? '#fca5a5' : '#fbbf24';
      return '<div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.04);">' +
        '<div style="font-size:12px;"><a href="earnings-signals.html#deception-detector-section" style="color:#fff; text-decoration:none; font-weight:600;">' + esc(s.company) + '</a> <span style="color:rgba(255,255,255,0.4); font-family:monospace; font-size:10px;">' + esc(s.ticker) + ' · ' + esc(s.quarter) + '</span></div>' +
        '<div style="display:flex; align-items:center; gap:8px;"><span style="color:' + col + '; font-family:\'Space Grotesk\',monospace; font-weight:700;">' + s.composite_score + '</span>' +
        '<span style="color:' + col + '; font-size:9px; text-transform:uppercase; font-weight:700; letter-spacing:0.5px; padding:2px 6px; border:1px solid ' + col + '40; border-radius:4px;">' + s.flag_level.replace('_', ' ') + '</span></div>' +
      '</div>';
    }).join('');
  }

  // ── Alerts stream (right column) ─────────────────────────────────────────

  function renderAlerts() {
    const body = document.getElementById('term-alerts-body');
    if (!body) return;
    const alerts = buildSyntheticAlerts();
    if (alerts.length === 0) return; // keep default empty state
    body.innerHTML = alerts.map(a =>
      '<div class="term-alert">' +
        '<span class="term-alert-ts">' + esc(a.time) + '</span>' +
        esc(a.text) +
      '</div>'
    ).join('');
  }

  function buildSyntheticAlerts() {
    // Until real user alerts exist, synthesize from the feed
    const out = [];
    const fd = (window.FORM_D_FILINGS && window.FORM_D_FILINGS.filings) || [];
    if (fd.length > 0) {
      out.push({
        time: daysAgo(fd[0].filed_date),
        text: '🟢 ' + fd[0].company + ' filed Form D — round opening.',
      });
    }
    const scored = (window.DECEPTION_SCORES_AUTO && window.DECEPTION_SCORES_AUTO.scored_calls) || [];
    if (scored.length > 0 && scored[0].composite_score >= 60) {
      out.push({
        time: scored[0].date,
        text: '🔴 ' + scored[0].company + ' · earnings-call deception score ' + scored[0].composite_score + '.',
      });
    }
    const lob = (window.LOBBYING_AUTO && window.LOBBYING_AUTO.by_company) || [];
    const accel = lob.filter(r => r.qoq_pct > 30)[0];
    if (accel) {
      out.push({
        time: 'Q1 2026',
        text: '🟡 ' + accel.company + ' lobbying +' + accel.qoq_pct.toFixed(0) + '% QoQ.',
      });
    }
    return out;
  }

  // ── Export CSV ────────────────────────────────────────────────────────────

  window.termExport = function () {
    const items = buildFeedItems();
    const rows = [['icon', 'title', 'meta', 'href']];
    items.forEach(it => rows.push([it.icon, it.title, it.meta, it.href]));
    const csv = rows.map(r => r.map(v => '"' + String(v || '').replace(/"/g, '""') + '"').join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ros-terminal-feed-' + new Date().toISOString().slice(0, 10) + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  function init() {
    greet();
    try { renderQuickStats(); } catch (e) { console.error('[terminal] quickstats:', e); }
    try { renderWatchlist(); } catch (e) { console.error('[terminal] watchlist:', e); }
    try { renderTodayActions(); } catch (e) { console.error('[terminal] today:', e); }
    try { renderFeed(); } catch (e) { console.error('[terminal] feed:', e); }
    try { renderDeception(); } catch (e) { console.error('[terminal] deception:', e); }
    try { renderAlerts(); } catch (e) { console.error('[terminal] alerts:', e); }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
