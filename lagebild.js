/* The Build-Out, Live: page renderer.
   Reads const LAGEBILD from data/lagebild_auto.js (built by scripts/build_lagebild.py).

   Every number on the page is computed here from that file. "Today" is the file's as_of
   date, never the visitor's clock, so the page shows the same thing to everyone until the
   next build. Lines arrive finished and checked; this script never writes or edits one. */
(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };
  var D = (typeof LAGEBILD !== 'undefined' && LAGEBILD && Array.isArray(LAGEBILD.events)) ? LAGEBILD : null;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  if (!D) {
    $('lb-feed').innerHTML = '';
    showEmpty('The event file is missing.',
      'This page reads data/lagebild_auto.js, which the daily build writes. Check back after the next build.', []);
    $('lb-map').className = 'lb-map lb-map--off';
    $('lb-map').textContent = 'No events to map.';
    return;
  }

  // ── constants that are about display only ───────────────────────────────
  var GROUP = {
    round: 'capital', debt: 'capital', form_d: 'capital', ipo_filing: 'capital',
    contract: 'awards', grant: 'awards',
    new_location: 'jobs', first_mfg_role: 'jobs', senior_mfg_role: 'jobs', production_turn: 'jobs', hiring_surge: 'jobs'
  };
  var GROUP_COLOR = { capital: '#4ade80', awards: '#f59e0b', jobs: '#60a5fa', other: '#9ca3af' };
  var SITE_TYPES = ['new_location', 'first_mfg_role'];
  var BASIS = { hq: 'HQ town', source: 'named in the source' };
  var STATES = {
    AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut',
    DE: 'Delaware', DC: 'District of Columbia', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois',
    IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland',
    MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana',
    NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York',
    NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania',
    RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah',
    VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming'
  };
  var PAGE_SIZE = 100;                       // rows drawn before "Show more"
  var US_VIEW = [[24.5, -125], [49.5, -66.9]];
  // Same basemap and key as the company map in app.js (initDiscoveryMap).
  var TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=cb1_3sea_1_eae8aeaaadc19f9306a0da40';

  // ── dates and money ─────────────────────────────────────────────────────
  function dayNumber(iso) {
    var p = String(iso).split('-');
    return Math.round(Date.UTC(+p[0], +p[1] - 1, +p[2]) / 86400000);
  }
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function fmtDate(iso) {                      // "9 Nov 2026", the same in every browser
    var p = String(iso).split('-');
    return (+p[2]) + ' ' + MONTHS[+p[1] - 1] + ' ' + p[0];
  }
  function fmtUsd(n) {
    var units = [[1e12, 'T'], [1e9, 'B'], [1e6, 'M'], [1e3, 'K']];
    for (var i = 0; i < units.length; i++) {
      if (n >= units[i][0]) {
        var q = n / units[i][0];
        var places = q >= 100 ? 0 : q >= 10 ? 1 : 2;
        var rounded = Number(q.toFixed(places));
        if (rounded >= 1000 && units[i][1] !== 'T') return fmtUsd(rounded * units[i][0]);
        return '$' + String(rounded) + units[i][1];
      }
    }
    return '$' + Math.round(n);
  }
  function plural(n, one, many) { return n + ' ' + (n === 1 ? one : many); }
  function safeUrl(u) { return /^https:\/\//.test(String(u || '')) ? String(u) : ''; }
  function typeLabel(t) { return (D.types[t] && D.types[t].label) || t; }

  var asOf = dayNumber(D.as_of);
  var events = D.events.map(function (e) {
    var copy = Object.assign({}, e);
    copy.age = asOf - dayNumber(e.date);
    return copy;
  }).filter(function (e) { return e.age >= 0; });
  var held = D.held_types || [];
  var windows = (D.windows || [7, 30, 90]).slice().sort(function (a, b) { return a - b; });
  var counterDays = windows[0];
  var maxDays = windows[windows.length - 1];

  // ── state, kept in the page address ─────────────────────────────────────
  var DEFAULTS = { w: windows.indexOf(30) !== -1 ? 30 : maxDays, type: '', sector: '', state: '', sort: 'score' };
  var state = Object.assign({}, DEFAULTS);
  var shown = PAGE_SIZE;

  function distinct(key) {
    var seen = {};
    events.forEach(function (e) { if (e[key]) seen[e[key]] = true; });
    return Object.keys(seen);
  }
  var typeOptions = Object.keys(D.types).filter(function (t) { return distinct('type').indexOf(t) !== -1; });
  var sectorOptions = distinct('sector').sort();
  var stateOptions = distinct('state').sort();

  function readState() {
    var q = new URLSearchParams(window.location.search);
    var next = Object.assign({}, DEFAULTS);
    var w = parseInt(q.get('w'), 10);
    if (windows.indexOf(w) !== -1) next.w = w;
    if (typeOptions.indexOf(q.get('type')) !== -1) next.type = q.get('type');
    if (sectorOptions.indexOf(q.get('sector')) !== -1) next.sector = q.get('sector');
    if (stateOptions.indexOf(q.get('state')) !== -1) next.state = q.get('state');
    if (q.get('sort') === 'new') next.sort = 'new';
    state = next;
  }
  function writeState() {
    var q = new URLSearchParams(window.location.search);      // other parameters are left alone
    var own = {
      w: state.w !== DEFAULTS.w ? String(state.w) : '',
      type: state.type, sector: state.sector, state: state.state,
      sort: state.sort !== DEFAULTS.sort ? state.sort : ''
    };
    Object.keys(own).forEach(function (k) { if (own[k]) q.set(k, own[k]); else q.delete(k); });
    var text = q.toString();
    try {
      window.history.replaceState(null, '', window.location.pathname + (text ? '?' + text : '') + window.location.hash);
    } catch (err) { /* file:// pages may refuse; the page still works */ }
  }
  function filtersActive() { return !!(state.type || state.sector || state.state); }

  // ── selection ───────────────────────────────────────────────────────────
  function matches(e, skip) {
    return (skip === 'type' || !state.type || e.type === state.type) &&
           (skip === 'sector' || !state.sector || e.sector === state.sector) &&
           (skip === 'state' || !state.state || e.state === state.state);
  }
  function selected(days, skip) {
    return events.filter(function (e) { return e.age <= days && matches(e, skip); });
  }
  function byDateThenId(a, b) {
    return a.date < b.date ? -1 : a.date > b.date ? 1 : a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
  }
  // Follow-ups sit under the earliest event of their thread that is in the current view.
  function toThreads(list) {
    var groups = {}, order = [];
    list.forEach(function (e) {
      if (!groups[e.thread]) { groups[e.thread] = []; order.push(e.thread); }
      groups[e.thread].push(e);
    });
    return order.map(function (k) {
      var members = groups[k].slice().sort(byDateThenId);
      return { head: members[0], rest: members.slice(1) };
    });
  }
  function ranked(threads) {
    var name = function (t) { return t.head.company.toLowerCase(); };
    return threads.sort(function (a, b) {
      var byScore = b.head.score - a.head.score;
      var byDate = a.head.date < b.head.date ? 1 : a.head.date > b.head.date ? -1 : 0;
      var first = state.sort === 'new' ? byDate : byScore;
      var second = state.sort === 'new' ? byScore : byDate;
      return first || second || (name(a) < name(b) ? -1 : name(a) > name(b) ? 1 : 0) || (a.head.id < b.head.id ? -1 : 1);
    });
  }

  // ── counters: always the shortest window ────────────────────────────────
  function renderCounters() {
    var list = events.filter(function (e) { return e.age <= counterDays && matches(e, 'type'); });
    var rounds = toThreads(list.filter(function (e) { return e.type === 'round'; }));
    var raised = 0, withAmount = 0;
    rounds.forEach(function (t) {
      var amounts = [t.head].concat(t.rest).map(function (e) { return e.amount; }).filter(function (a) { return typeof a === 'number'; });
      if (amounts.length) { raised += Math.max.apply(null, amounts); withAmount += 1; }
    });
    var contracts = list.filter(function (e) { return e.type === 'contract'; }).length;
    var sites = list.filter(function (e) { return SITE_TYPES.indexOf(e.type) !== -1; }).length;
    var sitesHeld = SITE_TYPES.every(function (t) { return held.indexOf(t) !== -1; });

    $('lb-counters-title').textContent = 'The last ' + counterDays + ' days';
    $('lb-counter-scope').textContent = 'to ' + fmtDate(D.as_of) + ' · ' + (state.sector || 'all sectors') + ' · ' +
      (state.state ? (STATES[state.state] || state.state) : 'all states');
    $('lb-c-rounds').textContent = String(rounds.length);
    $('lb-c-raised').textContent = fmtUsd(raised);
    $('lb-c-raised-note').textContent = rounds.length && withAmount < rounds.length
      ? plural(rounds.length - withAmount, 'round states', 'rounds state') + ' no dollar amount' : '';
    $('lb-c-contracts').textContent = String(contracts);
    var waiting = (D.awaiting_link && D.awaiting_link.contract && D.awaiting_link.contract[String(counterDays)]) || 0;
    $('lb-c-contracts-note').textContent = (waiting && !state.sector && !state.state)
      ? plural(waiting, 'more award has', 'more awards have') + ' no source link yet' : '';
    var siteBox = $('lb-c-sites').parentNode;
    if (sitesHeld) {
      $('lb-c-sites').textContent = '—';
      $('lb-c-sites-note').textContent = 'Job-board signals are not switched on yet';
      siteBox.classList.add('lb-metric--held');
    } else {
      $('lb-c-sites').textContent = String(sites);
      $('lb-c-sites-note').textContent = '';
      siteBox.classList.remove('lb-metric--held');
    }
  }

  // ── filter controls ─────────────────────────────────────────────────────
  function chip(label, pressed, attrs) {
    return '<button type="button" class="il-chip" aria-pressed="' + (pressed ? 'true' : 'false') + '" ' + attrs + '>' + esc(label) + '</button>';
  }
  function fillSelect(id, options, current, allLabel, dim, labelOf) {
    var pool = selected(state.w, dim);
    var html = '<option value="">' + esc(allLabel) + ' (' + pool.length + ')</option>';
    options.forEach(function (value) {
      var n = pool.filter(function (e) { return e[dim] === value; }).length;
      html += '<option value="' + esc(value) + '"' + (value === current ? ' selected' : '') + '>' + esc(labelOf(value)) + ' (' + n + ')</option>';
    });
    $(id).innerHTML = html;
  }
  function renderControls() {
    $('lb-window').innerHTML = windows.map(function (w) {
      return chip(w + ' days', state.w === w, 'data-w="' + w + '"');
    }).join('');
    $('lb-sort').innerHTML = chip('By score', state.sort === 'score', 'data-sort="score"') + chip('Newest first', state.sort === 'new', 'data-sort="new"');
    fillSelect('lb-type', typeOptions, state.type, 'All types', 'type', typeLabel);
    fillSelect('lb-sector', sectorOptions, state.sector, 'All sectors', 'sector', function (v) { return v; });
    fillSelect('lb-state', stateOptions, state.state, 'All states', 'state', function (v) { return STATES[v] ? STATES[v] + ' (' + v + ')' : v; });
    $('lb-clear').hidden = !filtersActive();
  }

  // ── the feed ────────────────────────────────────────────────────────────
  function companyLink(e) {
    return '<a href="company.html?c=' + encodeURIComponent(e.company) + '">' + esc(e.company) + '</a>';
  }
  function lineHtml(e) {
    if (e.line.indexOf(e.company + ' ') === 0) return companyLink(e) + esc(e.line.slice(e.company.length));
    return esc(e.line) + ' ' + companyLink(e);
  }
  function sourceHtml(e) {
    var url = safeUrl(e.url);
    var html = url ? '<a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + esc(e.source || 'Source') + ' ↗</a>' : esc(e.source || '');
    (e.also || []).forEach(function (u, i) {
      if (safeUrl(u)) html += ' <a href="' + esc(u) + '" target="_blank" rel="noopener noreferrer">link ' + (i + 2) + ' ↗</a>';
    });
    return html;
  }
  function pointKey(e) { return (typeof e.lat === 'number' && typeof e.lng === 'number') ? e.lat + ',' + e.lng : ''; }
  function placeHtml(e) {
    if (!e.place) return '';
    var key = pointKey(e);
    var basis = key ? (BASIS[e.basis] || '') : 'not mapped';
    var name = key
      ? '<button type="button" class="lb-place" data-point="' + esc(key) + '" title="Show on the map">' + esc(e.place) + '</button>'
      : '<span>' + esc(e.place) + '</span>';
    return '<span>' + name + (basis ? ' <span class="lb-basis">· ' + esc(basis) + '</span>' : '') + '</span>';
  }
  function badges(e) {
    var group = GROUP[e.type] || 'other';
    var cls = group === 'awards' ? ' lb-badge--awards' : group === 'jobs' ? ' lb-badge--jobs' : group === 'other' ? ' lb-badge--plain' : '';
    var html = '<span class="il-badge' + cls + '">' + esc(typeLabel(e.type)) + '</span>';
    if (e.first) html += '<span class="il-badge lb-badge--plain" title="The earliest event of this type for the company in this site\'s record">First on record</span>';
    return html;
  }
  function scoreHtml(e) {
    var p = e.parts || [0, 0, 0];
    var title = 'Type points ' + p[0] + ' + dollar points ' + p[1] + ' + first-of-kind points ' + p[2];
    return '<div class="lb-score" title="' + esc(title) + '"><b>' + esc(e.score) + '</b><span>' + esc(p[0] + ' + ' + p[1] + ' + ' + p[2]) + '</span></div>';
  }
  function rowHtml(t, rank) {
    var e = t.head;
    var html = '<li class="lb-row" data-id="' + esc(e.id) + '" data-points="' +
      esc([e].concat(t.rest).map(pointKey).filter(Boolean).join(' ')) + '">' +
      '<div class="lb-rank" aria-hidden="true">' + rank + '</div><div class="lb-body">' +
      '<div class="lb-tags">' + badges(e) + '</div>' +
      '<p class="lb-line">' + lineHtml(e) + '</p>' +
      '<div class="lb-meta"><span>' + esc(fmtDate(e.date)) + '</span>' + placeHtml(e) + '<span>' + sourceHtml(e) + '</span></div>';
    if (e.follows) {
      var rootUrl = safeUrl(e.follows.url);
      html += '<div class="lb-follows">Follow-up to an event on ' + esc(fmtDate(e.follows.date)) + ': ' +
        (rootUrl ? '<a href="' + esc(rootUrl) + '" target="_blank" rel="noopener noreferrer">' + esc(e.follows.line) + '</a>' : esc(e.follows.line)) + '</div>';
    }
    if (t.rest.length) {
      html += '<details class="lb-more"><summary>' + plural(t.rest.length, 'follow-up', 'follow-ups') + '</summary><ul>' +
        t.rest.map(function (f) {
          return '<li>' + esc(fmtDate(f.date)) + ' · ' + lineHtml(f) + ' ' + sourceHtml(f) + '</li>';
        }).join('') + '</ul></details>';
    }
    return html + '</div>' + scoreHtml(e) + '</li>';
  }
  function showEmpty(title, body, actions) {
    $('lb-empty-title').textContent = title;
    $('lb-empty-body').textContent = body;
    $('lb-empty-actions').innerHTML = (actions || []).join('');
    $('lb-empty').hidden = false;
  }
  function renderFeed(list) {
    var feed = $('lb-feed');
    var threads = ranked(toThreads(list));
    $('lb-feed-title').textContent = state.sort === 'new' ? 'Events, newest first' : 'Events, ranked by score';
    $('lb-feed-count').textContent = plural(list.length, 'event', 'events') + ' · last ' + state.w + ' days' +
      (threads.length !== list.length ? ' · ' + plural(threads.length, 'thread', 'threads') : '');
    if (!threads.length) {
      feed.innerHTML = '';
      var actions = [];
      if (filtersActive()) actions.push(chip('Clear filters', false, 'data-clear="1"'));
      windows.forEach(function (w) {
        var n = selected(w).length;
        if (w > state.w && n) actions.push(chip('Show ' + w + ' days (' + n + ')', false, 'data-w="' + w + '"'));
      });
      if (!events.length) {
        showEmpty('No sourced events in the last ' + maxDays + ' days.',
          'An event appears here only when the data holds a link to its primary source.', []);
      } else if (filtersActive()) {
        showEmpty('No events match these filters in the last ' + state.w + ' days.',
          'Clear a filter or choose a longer window.', actions);
      } else {
        showEmpty('No sourced events in the last ' + state.w + ' days.',
          actions.length ? 'A longer window has some.' : 'An event appears here only when the data holds a link to its primary source.', actions);
      }
      return;
    }
    $('lb-empty').hidden = true;
    var html = threads.slice(0, shown).map(function (t, i) { return rowHtml(t, i + 1); }).join('');
    if (threads.length > shown) {
      html += '<li class="lb-loading"><button type="button" class="il-chip" data-more="1">Show ' +
        Math.min(PAGE_SIZE, threads.length - shown) + ' more of ' + threads.length + '</button></li>';
    }
    feed.innerHTML = html;
  }

  // ── the map: one circle per rounded town point ──────────────────────────
  var map = null, layer = null, markers = {}, fitted = '';
  function initMap() {
    var el = $('lb-map');
    if (typeof L === 'undefined') {
      el.className = 'lb-map lb-map--off';
      el.textContent = 'The map could not load. The list is complete without it.';
      return;
    }
    map = L.map(el, {
      minZoom: 3,
      maxZoom: Math.min(12, 5 + 3 * (D.coord_decimals || 1)),     // never closer than the rounding allows
      scrollWheelZoom: false,
      worldCopyJump: true
    });
    L.tileLayer(TILE_URL, { attribution: '&copy; OpenStreetMap &copy; CARTO', maxZoom: 19 }).addTo(map);
    map.fitBounds(US_VIEW);
    fitted = 'us';
    layer = L.layerGroup().addTo(map);
    map.on('popupopen', function (ev) { markRows(ev.popup && ev.popup.options ? ev.popup.options.lbPoint : ''); });
    map.on('popupclose', function () { markRows(''); });
  }
  function markRows(key) {
    Array.prototype.forEach.call(document.querySelectorAll('.lb-row'), function (row) {
      var points = (row.getAttribute('data-points') || '').split(' ');
      row.classList.toggle('is-active', !!key && points.indexOf(key) !== -1);
    });
  }
  function popupHtml(list) {
    var places = [];
    list.forEach(function (e) {
      var label = e.place + (e.basis === 'hq' ? ' · HQ town' : '');
      if (places.indexOf(label) === -1) places.push(label);
    });
    var top = list.slice().sort(function (a, b) { return b.score - a.score || byDateThenId(b, a); });
    var html = '<div class="lb-pop"><div class="lb-pop-place">' + esc(places.join(' / ')) + '</div><ul>' +
      top.slice(0, 5).map(function (e) {
        var url = safeUrl(e.url);
        return '<li>' + esc(e.line) + ' <span>' + esc(fmtDate(e.date)) + '</span>' +
          (url ? ' <a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">source ↗</a>' : '') + '</li>';
      }).join('') + '</ul>';
    if (top.length > 5) html += '<div class="lb-pop-more">and ' + (top.length - 5) + ' more in the list</div>';
    return html + '</div>';
  }
  function renderMap(list) {
    var mapped = list.filter(pointKey);
    var km = Math.round(111 / Math.pow(10, D.coord_decimals || 1));
    var note = list.length
      ? mapped.length + ' of ' + plural(list.length, 'event', 'events') + ' on the map. '
      : '';
    $('lb-map-note').textContent = note + 'A point marks a town, rounded to about ' + km + ' km, never a building. ' +
      '"HQ town" means the source names no place, so the event sits at the company\'s headquarters town.';
    if (!map) return;
    layer.clearLayers();
    markers = {};
    var groups = {};
    mapped.forEach(function (e) { (groups[pointKey(e)] = groups[pointKey(e)] || []).push(e); });
    var bounds = [];
    Object.keys(groups).forEach(function (key) {
      var members = groups[key];
      var best = members.slice().sort(function (a, b) { return b.score - a.score; })[0];
      var color = GROUP_COLOR[GROUP[best.type] || 'other'];
      var latlng = [members[0].lat, members[0].lng];
      var marker = L.circleMarker(latlng, {
        radius: Math.min(22, 5 + 3 * Math.sqrt(members.length)),
        color: color, weight: 1.5, fillColor: color, fillOpacity: 0.45
      });
      marker.bindPopup(popupHtml(members), { maxWidth: 300, lbPoint: key });
      marker.addTo(layer);
      markers[key] = marker;
      bounds.push(latlng);
    });
    // Follow the state filter; otherwise keep the whole-country view steady.
    var want = state.state && bounds.length ? 'state:' + state.state : 'us';
    if (want !== fitted) {
      if (want === 'us') map.fitBounds(US_VIEW);
      else map.fitBounds(L.latLngBounds(bounds).pad(0.6), { maxZoom: 7 });
      fitted = want;
    }
  }
  function showPoint(key) {
    if (!map || !markers[key]) return;
    var marker = markers[key];
    map.setView(marker.getLatLng(), Math.max(map.getZoom(), 6));
    marker.openPopup();
    var box = $('lb-map').getBoundingClientRect();
    if (box.top < 60 || box.bottom > window.innerHeight) $('lb-map').scrollIntoView({ block: 'center' });
  }

  // ── "How this is ranked", written from the numbers in the data file ─────
  function renderMethod() {
    var s = D.scoring || {};
    var floor = s.dollar_floor_usd, per = s.points_per_tenfold, cap = s.dollar_cap_points;
    var steps = [];
    for (var amount = floor, pts = 0; pts <= cap; amount *= 10, pts += per) steps.push(fmtUsd(amount) + ' = ' + pts);
    var rows = Object.keys(D.types).map(function (k) { return { key: k, t: D.types[k] }; })
      .sort(function (a, b) { return b.t.points - a.t.points || (a.t.label < b.t.label ? -1 : 1); });
    var noFirst = rows.filter(function (r) { return !r.t.first; }).map(function (r) { return '"' + r.t.label + '"'; });
    var html = '<p class="lb-formula">score = type points + dollar points + first-of-kind points</p>' +
      '<p>The score is built only from an event\'s fields. The formula is the same for every event and is never tuned for one.</p>' +
      '<h3>Type points</h3><div class="lb-table-wrap"><table class="lb-table"><thead><tr><th>Event type</th><th class="lb-num">Points</th><th>On this page</th></tr></thead><tbody>' +
      rows.map(function (r) {
        var n = events.filter(function (e) { return e.type === r.key; }).length;
        var status = held.indexOf(r.key) !== -1 ? 'not switched on yet' : plural(n, 'event', 'events') + ' in ' + maxDays + ' days';
        return '<tr><td>' + esc(r.t.label) + '</td><td class="lb-num">' + r.t.points + '</td><td>' + esc(status) + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<p>Types that carry a dollar figure start lower and earn most of their score from the dollars. Types that never carry one start higher.</p>' +
      '<h3>Dollar points</h3><p>' + per + ' points for every tenfold step above ' + fmtUsd(floor) + ', up to ' + cap + ': ' + esc(steps.join(', ')) +
      '. In between, the points follow the logarithm of the amount. An event with no dollar figure gets 0.</p>' +
      '<h3>First-of-kind points</h3><p>' + s.first_points + ' points when the event is the earliest of its type for that company in this site\'s record, ' +
      'and only where the record of that type goes back at least ' + s.first_record_days + ' days before the event. ' +
      (noFirst.length ? 'Not given to the types ' + esc(noFirst.join(', ').replace(/, ([^,]*)$/, ' or $1')) + ', because this site\'s record of those is incomplete. ' : '') +
      'Such an event is marked "First on record".</p>' +
      '<h3>Order and threads</h3><p>Higher score first. Ties go to the newer event, then to the company name. A follow-up, meaning the same company and the same event type within ' +
      D.thread_days + ' days of the first event, sits under the first event instead of taking its own row.</p>' +
      '<h3>The counters</h3><p>The four counters cover the last ' + counterDays + ' days up to ' + esc(fmtDate(D.as_of)) +
      ' and follow the sector and state filters. "Raised" adds up funding rounds only, taking the largest amount stated in each thread. ' +
      'Debt financings and Form D filings are listed but not added, because a filing or a second post can repeat an announced round.</p>' +
      '<h3>What is not here</h3><ul>' +
      '<li>Anything without a link to a primary source: a filing, an award record, the company\'s own announcement or its job board.</li>' +
      '<li>Forecasts, estimates and schedules. A filing is an event; a likelihood is not.</li>' +
      '<li>Negative signals about a named company, and investor names.</li>';
    Object.keys(D.awaiting_link || {}).forEach(function (k) {
      var n = D.awaiting_link[k][String(maxDays)] || 0;
      if (n) {
        html += '<li>' + plural(n, 'event', 'events') + ' of the type "' + esc(typeLabel(k)) + '" from the last ' + maxDays +
          ' days that passed every other check. The data holds no link for them yet, and nothing is published without one.</li>';
      }
    });
    if (held.length) html += '<li>Job-board signals. They are built but not switched on yet.</li>';
    html += '</ul><p>The full method is in <a href="data/lagebild/README-METHOD.md">README-METHOD.md</a>. Every published event, with where each field came from, is in ' +
      '<a href="data/lagebild/events.json">events.json</a>. What was rejected, and why, is counted in <a href="data/lagebild/rejected.json">rejected.json</a>. ' +
      'This page covers US-headquartered companies among the ' + Number(D.companies_tracked).toLocaleString('en-US') + ' in the database.</p>';
    $('lb-method-body').innerHTML = html;
  }

  // ── draw everything ─────────────────────────────────────────────────────
  function render() {
    var list = selected(state.w);
    renderControls();
    renderCounters();
    renderFeed(list);
    renderMap(list);
  }
  function update(change) {
    Object.keys(change).forEach(function (k) { state[k] = change[k]; });
    shown = PAGE_SIZE;
    writeState();
    render();
  }

  // ── wiring ──────────────────────────────────────────────────────────────
  $('lb-asof').textContent = 'As of ' + fmtDate(D.as_of) + ' · every line links to its source';
  $('lb-type').addEventListener('change', function () { update({ type: this.value }); });
  $('lb-sector').addEventListener('change', function () { update({ sector: this.value }); });
  $('lb-state').addEventListener('change', function () { update({ state: this.value }); });
  $('lb-clear').addEventListener('click', function () { update({ type: '', sector: '', state: '' }); });
  $('lb-main').addEventListener('click', function (ev) {
    var target = ev.target.closest ? ev.target.closest('[data-w], [data-sort], [data-clear], [data-more], [data-point]') : null;
    if (!target) return;
    if (target.hasAttribute('data-w')) update({ w: parseInt(target.getAttribute('data-w'), 10) });
    else if (target.hasAttribute('data-sort')) update({ sort: target.getAttribute('data-sort') });
    else if (target.hasAttribute('data-clear')) update({ type: '', sector: '', state: '' });
    else if (target.hasAttribute('data-more')) { shown += PAGE_SIZE; renderFeed(selected(state.w)); }
    else if (target.hasAttribute('data-point')) showPoint(target.getAttribute('data-point'));
  });
  window.addEventListener('popstate', function () { readState(); shown = PAGE_SIZE; render(); });

  readState();
  initMap();
  renderMethod();
  render();
})();
