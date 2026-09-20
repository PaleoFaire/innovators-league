/* Raised — first-party funding announcements.
   Reads window.COMPANY_ANNOUNCEMENTS_AUTO from
   data/company_announcements_auto.js (built by
   scripts/fetch_company_announcements.py).

   The watcher reads company newsrooms directly rather than waiting for the
   trade press, so a round can appear here before anyone writes it up. That
   also means every row is the company's own words, which is why each one
   links straight to the announcement.
*/
(function () {
  var D = window.COMPANY_ANNOUNCEMENTS_AUTO;
  var feed = document.getElementById('rounds-feed');

  if (!D || !D.results) {
    feed.innerHTML = '<p class="rounds-empty">Announcement data has not been generated yet.</p>';
    return;
  }

  /* ---------- flatten to hits ---------- */
  var hits = [];
  D.results.forEach(function (r) {
    (r.hits || []).forEach(function (h) {
      if (!h.title || !String(h.title).trim()) return;
      hits.push({
        company: r.company,
        website: r.website,
        title: decodeEntities(h.title),
        link: h.link,
        date: h.date || '',
        ts: parseDate(h.date),
        age: h.age_days,
        round: h.round || '',
        amount: h.amount || '',
        valuation: h.valuation || '',
        knownStage: h.known_stage || '',
        knownRaised: h.known_raised || '',
        isNew: !!h.looks_new
      });
    });
  });

  /* One announcement is often syndicated across a company's own feed and a
     press page. Same company + same round + same amount is one event. */
  var seen = {};
  hits = hits.filter(function (h) {
    var k = (h.company + '|' + h.round + '|' + h.amount).toLowerCase();
    if (seen[k]) return false;
    seen[k] = 1;
    return true;
  });

  hits.sort(function (a, b) {
    if (a.isNew !== b.isNew) return a.isNew ? -1 : 1;
    return (b.ts || 0) - (a.ts || 0);
  });

  /* ---------- helpers ---------- */
  function decodeEntities(s) {
    var t = document.createElement('textarea');
    t.innerHTML = String(s);
    return t.value;
  }
  function parseDate(s) {
    if (!s) return 0;
    var d = new Date(s);
    return isNaN(d.getTime()) ? 0 : d.getTime();
  }
  function fmtDate(h) {
    if (!h.ts) return h.date ? esc(h.date.slice(0, 16)) : '—';
    var d = new Date(h.ts);
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  }
  function ageLabel(h) {
    if (h.age == null) return '';
    if (h.age <= 31) return '<span class="rounds-fresh">' + Math.max(0, Math.round(h.age)) + 'd ago</span>';
    if (h.age <= 400) return Math.round(h.age / 30) + ' months ago';
    return '<span class="rounds-stale">' + (h.age / 365).toFixed(1) + ' years old</span>';
  }
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function companyHref(name) {
    return 'company.html?c=' + encodeURIComponent(name);
  }

  /* ---------- stats ---------- */
  var fresh = hits.filter(function (h) { return h.age != null && h.age <= 31; }).length;
  document.getElementById('rounds-stats').innerHTML =
    stat(hits.length, 'announcements found') +
    stat(fresh, 'in the last 30 days') +
    stat(D.with_feed, 'newsrooms readable') +
    stat(D.companies_checked, 'companies checked');

  function stat(n, label) {
    return '<div class="rounds-stat"><b>' + (n == null ? '—' : n) + '</b><span>' + label + '</span></div>';
  }

  /* ---------- render ---------- */
  function card(h) {
    var flag = h.isNew
      ? '<span class="rounds-badge rounds-badge-new">AHEAD OF OUR RECORD</span>'
      : '<span class="rounds-badge rounds-badge-known">MATCHES OUR RECORD</span>';

    var money = [];
    if (h.round) money.push('<b>' + esc(h.round) + '</b>');
    if (h.amount) money.push(esc(h.amount));
    if (h.valuation) money.push('at ' + esc(h.valuation));

    var known = [];
    if (h.knownStage) known.push(esc(h.knownStage));
    if (h.knownRaised) known.push(esc(h.knownRaised) + ' on file');

    return '' +
      '<article class="rounds-row">' +
        '<div class="rounds-left">' +
          flag +
          '<div class="rounds-date">' + fmtDate(h) + '</div>' +
          '<div class="rounds-age">' + ageLabel(h) + '</div>' +
        '</div>' +
        '<div class="rounds-main">' +
          '<div class="rounds-co"><a href="' + companyHref(h.company) + '">' + esc(h.company) + '</a>' +
            (money.length ? ' <span class="rounds-money">' + money.join(' · ') + '</span>' : '') +
          '</div>' +
          '<div class="rounds-title">' +
            (h.link ? '<a href="' + esc(h.link) + '" target="_blank" rel="noopener">' + esc(h.title) + '</a>'
                    : esc(h.title)) +
          '</div>' +
          (known.length ? '<div class="rounds-known">We hold: ' + known.join(' · ') + '</div>' : '') +
        '</div>' +
      '</article>';
  }

  function render(filter) {
    var rows = hits.filter(function (h) {
      if (filter === 'new') return h.isNew;
      if (filter === 'recent') return h.age != null && h.age <= 90;
      return true;
    });
    if (!rows.length) {
      feed.innerHTML = '<p class="rounds-empty">' +
        (filter === 'new'
          ? 'Nothing ahead of our record right now. Every announcement the watcher found matches what the database already holds — which is the outcome you want most days.'
          : 'No announcements in this window.') +
        '</p>';
      return;
    }
    feed.innerHTML = rows.map(card).join('');
  }

  /* ---------- filters ---------- */
  var FILTERS = [
    ['all', 'Everything'],
    ['recent', 'Last 90 days'],
    ['new', 'Ahead of our record']
  ];
  var box = document.getElementById('rounds-filters');
  box.innerHTML = FILTERS.map(function (f, i) {
    return '<button class="rounds-filter' + (i === 0 ? ' active' : '') +
           '" data-f="' + f[0] + '">' + f[1] + '</button>';
  }).join('');
  box.addEventListener('click', function (e) {
    var b = e.target.closest('.rounds-filter');
    if (!b) return;
    box.querySelectorAll('.rounds-filter').forEach(function (x) { x.classList.remove('active'); });
    b.classList.add('active');
    render(b.getAttribute('data-f'));
  });

  var gen = D.generated_at ? new Date(D.generated_at) : null;
  if (gen) {
    document.getElementById('rounds-updated').textContent =
      'Last swept ' + gen.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
  }

  render('all');
})();
