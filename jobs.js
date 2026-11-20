/**
 * Jobs Board v2 — The ROS Innovators League
 *
 * Reads window.JOBS_V2 (data/jobs_enriched.js, built by scripts/enrich_jobs.py)
 * and renders: nine curated shelves, a synonym-aware search box, four primary
 * chip rows (what I do / where / which kind of company / level) with live
 * counts, a secondary filter rail, and a newest-first list with a per-company
 * cap and a group-by-company view.
 *
 * On top of that sits the family layer, for readers who do not know the trade
 * names: plain role types, "search near home" (a city or ZIP code and a
 * distance, or the browser's own location), the filters families ask about,
 * an employer-facts card, a link to copy for a search or a single job, and a
 * one-page printout. Every rule behind those (which title is hands-on work,
 * which town a posting is in) lives in the pipeline; this file only reads the
 * columns the pipeline wrote, and hides a control when its column is missing.
 *
 * Nothing a reader types, and nothing their browser says about where they
 * are, leaves the browser: places are looked up in data/geo/us_places.json
 * and distances are worked out here. A location from the browser is kept in
 * memory only. It is never written to the address bar, to storage or to a link.
 *
 * Postings that are per-location clones of one role (same company, same
 * normalised title) arrive pre-grouped: the primary row carries the others
 * and expands to the individual postings. Chips, shelves and the results
 * count all count roles (grouped rows); the hero keeps the raw postings count.
 *
 * Also exposes JOBS_DATA / JOBS_STATS (one record per posting, expanded from
 * the compact rows) so the untouched Talent Intelligence tab (talent.js)
 * keeps working.
 */

// ─────────────────────────────────────────────────────────────────────────────
// Pure helpers: no DOM, no globals. Loaded in Node by scripts/tests/test_jobs_family.js.
// normPlace, stateCode, haversineMiles and unpackZip mirror scripts/enrich_jobs.py and
// scripts/build_geo_places.py; scripts/tests/jobs_family_cases.json holds both to the same answers.
// ─────────────────────────────────────────────────────────────────────────────
(function (root) {
  'use strict';

  var EARTH_RADIUS_MILES = 3958.8;
  var WITHIN_CHOICES = [25, 50, 100];   // miles; 0 = "Open to moving" (no distance limit)
  var WITHIN_DEFAULT = 50;

  var STATE_NAMES = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA', 'colorado': 'CO',
    'connecticut': 'CT', 'delaware': 'DE', 'district of columbia': 'DC', 'florida': 'FL', 'georgia': 'GA',
    'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS', 'kentucky': 'KY',
    'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD', 'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN',
    'mississippi': 'MS', 'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH',
    'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND',
    'ohio': 'OH', 'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'puerto rico': 'PR', 'rhode island': 'RI',
    'south carolina': 'SC', 'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
    'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'
  };
  var STATE_CODES = {};
  Object.keys(STATE_NAMES).forEach(function (k) { STATE_CODES[STATE_NAMES[k]] = true; });

  /** Town name -> lookup key: lower case, no accents or punctuation, "Saint" and "St." alike. */
  function normPlace(name) {
    var s = String(name == null ? '' : name);
    if (s.normalize) s = s.normalize('NFKD');
    s = s.replace(/[̀-ͯ]/g, '').replace(/[^\x00-\x7f]/g, '').toLowerCase();
    s = s.replace(/[.']/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
    return s.replace(/^saint /, 'st ').replace(/^mount /, 'mt ').replace(/^fort /, 'ft ');
  }

  /** 'CA', 'California', 'D.C.' -> 'CA' / 'CA' / 'DC'; anything else -> ''. */
  function stateCode(token) {
    var t = String(token == null ? '' : token).trim().replace(/\./g, '');
    var code = t.toUpperCase();
    if (STATE_CODES[code]) return code;
    return STATE_NAMES[t.toLowerCase().replace(/\s+/g, ' ')] || '';
  }

  /** Great-circle distance in miles. */
  function haversineMiles(lat1, lng1, lat2, lng2) {
    var rad = Math.PI / 180;
    var p1 = lat1 * rad, p2 = lat2 * rad;
    var a = Math.pow(Math.sin((p2 - p1) / 2), 2) + Math.cos(p1) * Math.cos(p2) * Math.pow(Math.sin((lng2 - lng1) * rad / 2), 2);
    return 2 * EARTH_RADIUS_MILES * Math.asin(Math.min(1, Math.sqrt(a)));
  }

  /** One ZIP code out of the packed table (see build_geo_places.py) -> [lat, lng] or null. */
  function unpackZip(packed, code) {
    var row = (packed && packed[String(code).slice(0, 3)]) || '';
    var tail = String(code).slice(3);
    for (var i = 0; i + 8 <= row.length; i += 8) {
      if (row.substr(i, 2) === tail) {
        return [Math.round(parseInt(row.substr(i + 2, 3), 36) - 9000) / 100, Math.round(parseInt(row.substr(i + 5, 3), 36) - 18000) / 100];
      }
    }
    return null;
  }

  /** data/geo/us_places.json -> lookups. An empty index (ok: false) when the file is missing or malformed. */
  function geoIndex(G) {
    var idx = { ok: false, source: '', places: [], byKey: {}, byName: {}, aliases: {}, hubs: [], zips: {}, hasZips: false };
    if (!G || !Array.isArray(G.places) || !Array.isArray(G.states)) return idx;
    for (var i = 0; i < G.places.length; i++) {
      var r = G.places[i], st = G.states[r[1]];
      if (!r || typeof r[0] !== 'string' || !st || typeof r[2] !== 'number' || typeof r[3] !== 'number') continue;
      var p = { name: r[0], state: st, lat: r[2], lng: r[3], key: normPlace(r[0]), label: r[0] + ', ' + st };
      idx.places[i] = p;
      if (!idx.byKey[p.key + '|' + st]) idx.byKey[p.key + '|' + st] = p;
      (idx.byName[p.key] = idx.byName[p.key] || []).push(p);
    }
    var al = G.aliases || {};
    Object.keys(al).forEach(function (k) { if (idx.places[al[k]]) idx.aliases[k] = idx.places[al[k]]; });
    (G.hubs || []).forEach(function (h) {
      if (h && typeof h[0] === 'string') idx.hubs.push({ code: h[0], label: h[1], lat: h[2], lng: h[3], approx: !!h[4], key: normPlace(h[1]) });
    });
    idx.zips = G.zips && typeof G.zips === 'object' ? G.zips : {};
    idx.hasZips = Object.keys(idx.zips).length > 0;
    idx.source = G.source || '';
    idx.ok = true;
    return idx;
  }

  function placeResult(p) { return { ok: true, kind: 'place', value: p.label, label: p.label, lat: p.lat, lng: p.lng }; }

  /** "Austin, TX" / "Austin Texas" -> ['Austin', 'TX']; state '' when the text gives none. */
  function splitTown(text) {
    var parts = String(text || '').split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    if (!parts.length) return ['', ''];
    if (parts.length >= 2) {
      var st = stateCode(parts[1]);
      if (st) return [parts[0], st];
    }
    var words = parts[0].split(/\s+/);
    for (var n = 3; n >= 1; n--) {                      // "Charleston South Carolina", "Austin TX", "washington dc"
      if (words.length > n) {
        var code = stateCode(words.slice(-n).join(' '));
        if (code) return [words.slice(0, -n).join(' '), code];
      }
    }
    return [parts[0], ''];
  }

  /**
   * What the reader typed -> a point, a hub, or a plain reason why not.
   *   { ok: true, kind: 'place' | 'zip', value, label, lat, lng }
   *   { ok: true, kind: 'hub', value: 'hub:sf', code, label }
   *   { ok: false, reason: 'empty' | 'no-zips' | 'zip-short' | 'zip-unknown' | 'ambiguous' | 'unknown', options? }
   */
  function resolveNear(text, idx) {
    var t = String(text == null ? '' : text).trim();
    if (!t) return { ok: false, reason: 'empty' };
    var m = /^hub:([a-z]+)$/.exec(t);
    if (m) return hubFor(m[1], idx) || { ok: false, reason: 'unknown' };
    if (/^\d+$/.test(t)) {
      if (!idx.hasZips) return { ok: false, reason: 'no-zips' };
      if (t.length !== 5) return { ok: false, reason: 'zip-short' };
      var z = unpackZip(idx.zips, t);
      return z ? { ok: true, kind: 'zip', value: t, label: 'ZIP code ' + t, lat: z[0], lng: z[1] } : { ok: false, reason: 'zip-unknown' };
    }
    var area = /^(.*?)\s*\(whole area\)$/i.exec(t);       // a hub picked from the list
    if (area) return hubFor(normPlace(area[1]), idx) || { ok: false, reason: 'unknown' };
    var res = townFor(t, idx);
    return res.ok || res.reason === 'ambiguous' ? res : (hubFor(normPlace(t), idx) || res);   // "SF Bay Area"
  }

  function hubFor(key, idx) {
    for (var i = 0; i < idx.hubs.length; i++) {
      var h = idx.hubs[i];
      if (h.key === key || h.code === key) return { ok: true, kind: 'hub', value: 'hub:' + h.code, code: h.code, label: h.label };
    }
    return null;
  }

  function townFor(t, idx) {
    var town = splitTown(t), st = town[1];
    if (st) {
      var key = normPlace(town[0]);
      var hit = key && (idx.byKey[key + '|' + st] || idx.aliases[key + '|' + st]);
      if (hit) return placeResult(hit);
      if (t.indexOf(',') >= 0) return { ok: false, reason: 'unknown' };   // "Town, ST" that is not on the list
    }
    var bare = st ? normPlace(t) : normPlace(town[0]);   // "Lake Placid": not "Lake" in a state called Placid
    if (!bare) return { ok: false, reason: 'unknown' };
    if (idx.aliases[bare + '|']) return placeResult(idx.aliases[bare + '|']);
    var list = idx.byName[bare] || [];
    if (list.length === 1) return placeResult(list[0]);
    if (list.length > 1) return { ok: false, reason: 'ambiguous', options: list.map(function (p) { return p.label; }) };
    return { ok: false, reason: 'unknown' };
  }

  /** Suggestions for what has been typed so far: [{ value, label, kind }], towns first, then areas. */
  function suggestPlaces(text, idx, limit) {
    var t = String(text == null ? '' : text).trim();
    limit = limit || 8;
    if (!idx || !idx.ok || t.length < 2) return [];
    if (/^\d+$/.test(t)) {
      return idx.hasZips && t.length === 5 && unpackZip(idx.zips, t) ? [{ value: t, label: 'ZIP code ' + t, kind: 'zip' }] : [];
    }
    var comma = t.indexOf(',');
    var key = normPlace(comma >= 0 ? t.slice(0, comma) : t);
    var stText = comma >= 0 ? t.slice(comma + 1).trim() : '';
    var stFull = stateCode(stText), stPrefix = stText.toUpperCase();
    if (!key) return [];
    var out = [], seen = {};
    var add = function (p, exact) {
      if (seen[p.label]) return;
      if (stText && !(p.state === stFull || (!stFull && p.state.indexOf(stPrefix) === 0))) return;
      seen[p.label] = 1;
      out.push({ value: p.label, label: p.label, kind: 'place', exact: exact ? 0 : 1, name: p.key, state: p.state });
    };
    if (comma < 0) {                                    // "Austin TX" typed without the comma
      var town = splitTown(t);
      if (town[1] && idx.byKey[normPlace(town[0]) + '|' + town[1]]) add(idx.byKey[normPlace(town[0]) + '|' + town[1]], true);
    }
    Object.keys(idx.aliases).forEach(function (k) { if (k.split('|')[0] === key) add(idx.aliases[k], true); });
    for (var i = 0; i < idx.places.length; i++) {
      var p = idx.places[i];
      if (p && p.key.indexOf(key) === 0) add(p, p.key === key);
    }
    out.sort(function (a, b) { return a.exact - b.exact || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0) || (a.state < b.state ? -1 : 1); });
    out = out.slice(0, limit);
    if (!stText) {
      idx.hubs.forEach(function (h) {
        if (h.key.indexOf(key) >= 0 || h.code === key) out.push({ value: h.label + ' (whole area)', label: 'Every job in the ' + h.label + ' area', kind: 'hub' });
      });
    }
    return out.map(function (o) { return { value: o.value, label: o.label, kind: o.kind }; });
  }

  // ─── Search state and the address bar ─────────────────────────────────────
  function defaultState() {
    return {
      q: '', family: [], metro: [], sector: [], level: [], stage: [], company: '',
      remote: false, salary: false, clearance: '', intern: false, il30: false, hardtech: true, posted: 0, stale: false,
      view: 'list', shelf: '',
      // family layer
      type: [],            // plain role types
      near: '',            // 'Austin, TX' | '78701' | 'hub:tx' | 'me' (the browser's location, held in memory only)
      within: WITHIN_DEFAULT, // 25 | 50 | 100 miles, or 0 for "Open to moving"
      plusremote: false,   // with a distance: also list remote jobs
      nodegree: false, entry: false,
      citizen: '',         // '' | 'only' | 'hide', as clearance
      sort: '',            // '' (nearest first on a distance search, else newest) | 'new' | 'near'
      job: ''              // a single shared posting, by id
    };
  }

  var LIST_KEYS = ['family', 'metro', 'sector', 'level', 'stage', 'type'];
  var FLAG_KEYS = ['remote', 'salary', 'intern', 'il30', 'stale', 'plusremote', 'nodegree', 'entry'];
  var TRI_KEYS = ['clearance', 'citizen'];             // 1 = only these, 0 = leave these out

  /** "?type=hands&near=Austin%2C+TX" -> state. Unknown or malformed values fall back to the defaults. */
  function parseQuery(search) {
    var p = new URLSearchParams(search || '');
    var s = defaultState();
    s.q = p.get('q') || '';
    LIST_KEYS.forEach(function (k) { var v = p.get(k); s[k] = v ? v.split(',').filter(Boolean) : []; });
    s.company = p.get('company') || '';
    FLAG_KEYS.forEach(function (k) { s[k] = p.get(k) === '1'; });
    TRI_KEYS.forEach(function (k) { var v = p.get(k); s[k] = v === '1' ? 'only' : v === '0' ? 'hide' : ''; });
    s.hardtech = p.get('hardtech') !== '0';
    s.posted = parseInt(p.get('posted') || '0', 10) || 0;
    s.view = p.get('view') === 'company' ? 'company' : 'list';
    s.shelf = p.get('shelf') || '';
    s.near = (p.get('near') || '').trim().slice(0, 80);
    if (s.near === 'me') s.near = '';                    // a location from the browser never travels in a link
    var w = p.get('within');
    s.within = w === 'any' || w === '0' ? 0 : (WITHIN_CHOICES.indexOf(parseInt(w, 10)) >= 0 ? parseInt(w, 10) : WITHIN_DEFAULT);
    var so = p.get('sort');
    s.sort = so === 'new' || so === 'near' ? so : '';
    s.job = (p.get('job') || '').slice(0, 200);
    return s;
  }

  /** state -> "type=hands&near=Austin%2C+TX" (no leading "?"); defaults are left out. */
  function buildQuery(state) {
    var p = new URLSearchParams();
    if (state.job) p.set('job', state.job);
    if (state.q) p.set('q', state.q);
    if (state.type && state.type.length) p.set('type', state.type.join(','));
    if (state.near && state.near !== 'me') {
      p.set('near', state.near);
      if (state.within !== WITHIN_DEFAULT) p.set('within', state.within ? String(state.within) : 'any');
      if (state.plusremote) p.set('plusremote', '1');
    }
    ['family', 'metro', 'sector', 'level', 'stage'].forEach(function (k) { if (state[k] && state[k].length) p.set(k, state[k].join(',')); });
    if (state.company) p.set('company', state.company);
    ['nodegree', 'entry', 'salary', 'remote', 'intern', 'il30'].forEach(function (k) { if (state[k]) p.set(k, '1'); });
    TRI_KEYS.forEach(function (k) { if (state[k]) p.set(k, state[k] === 'only' ? '1' : '0'); });
    if (!state.hardtech) p.set('hardtech', '0');
    if (state.posted) p.set('posted', String(state.posted));
    if (state.stale) p.set('stale', '1');
    if (state.view === 'company') p.set('view', 'company');
    if (state.sort) p.set('sort', state.sort);
    if (state.shelf) p.set('shelf', state.shelf);
    return p.toString();
  }

  /**
   * Does a role's type mask fit the chosen plain types? The kinds of work add up (hands-on OR
   * engineering); a type marked "across" narrows them (AND): hands-on + first jobs = hands-on first jobs.
   * roleTypes rows are [code, label, about, bit, across] as the pipeline wrote them.
   */
  function typeMasks(selected, roleTypes) {
    var work = 0, across = 0;
    (roleTypes || []).forEach(function (r) {
      if ((selected || []).indexOf(r[0]) >= 0) { if (r[4]) across |= r[3]; else work |= r[3]; }
    });
    return { work: work, across: across };
  }
  function typeMatches(mask, masks) {
    return (!masks.work || (mask & masks.work) !== 0) && (mask & masks.across) === masks.across;
  }

  /** Whole miles in words a grandmother would use. */
  function milesText(miles) {
    if (!(miles >= 0) || !isFinite(miles)) return '';
    if (miles < 1) return 'under 1 mile';
    var n = Math.round(miles);
    return n.toLocaleString('en-US') + (n === 1 ? ' mile' : ' miles');
  }

  var MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  /** '2026-05' -> 'May 2026'; '2026-11-16' -> '16 Nov 2026'; anything else comes back unchanged. */
  function plainDate(iso) {
    var m = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(iso || '');
    if (!m || +m[2] < 1 || +m[2] > 12) return iso || '';
    return m[3] ? (+m[3]) + ' ' + MONTHS_SHORT[+m[2] - 1] + ' ' + m[1] : MONTHS_LONG[+m[2] - 1] + ' ' + m[1];
  }

  var lib = {
    WITHIN_CHOICES: WITHIN_CHOICES, WITHIN_DEFAULT: WITHIN_DEFAULT,
    normPlace: normPlace, stateCode: stateCode, haversineMiles: haversineMiles, unpackZip: unpackZip,
    geoIndex: geoIndex, splitTown: splitTown, resolveNear: resolveNear, suggestPlaces: suggestPlaces,
    defaultState: defaultState, parseQuery: parseQuery, buildQuery: buildQuery,
    typeMasks: typeMasks, typeMatches: typeMatches, milesText: milesText, plainDate: plainDate
  };
  if (typeof module === 'object' && module && module.exports) module.exports = lib;
  else root.JobsFamilyLib = lib;
})(typeof window !== 'undefined' ? window : this);

// ─────────────────────────────────────────────────────────────────────────────
// The board
// ─────────────────────────────────────────────────────────────────────────────
(function () {
  'use strict';
  if (typeof window === 'undefined' || typeof document === 'undefined') return;   // Node: helpers only

  var L = window.JobsFamilyLib;
  var D = window.JOBS_V2;
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  };
  var fmtN = function (n) { return Number(n || 0).toLocaleString(); };

  if (!D || !D.jobs) {
    var grid = $('jb-list');
    if (grid) grid.innerHTML = '<div class="jb-empty"><h3>Jobs data is not loaded</h3><p>data/jobs_enriched.js is missing. Run <code>python3 scripts/enrich_jobs.py</code>.</p></div>';
    return;
  }

  // ─── Constants ────────────────────────────────────────────────────────────
  var F = { REMOTE: 1, STALE: 2, CLEARANCE: 4, USPERSON: 8, TRADES: 16, SUMMER27: 32, GENERAL: 64, SALTEXT: 128, SALHOURLY: 256, LVLDESC: 512, NODEGREE: 1024 };
  var CF = { IL30: 1, HARDTECH: 2, INDB: 4, SURGE: 8 };
  var STALE_DAYS = D.staleAfterDays || 90;
  var NEW_DAYS = D.newDays || 7;
  var CLOSING_DAYS = D.closingDays || 14;
  var SURGE_DAYS = D.surgeWindowDays || 14;
  var HOURS_PER_YEAR = 2080;
  var PAGE = 50;
  var GROUP_PAGE = 12;
  var COMPANY_CAP = 20;
  var PRINT_ROWS = 25;                 // what fits on one printed page, one line a job
  var MS_DAY = 86400000;
  var GEO_URL = 'data/geo/us_places.json';
  var NEAREST_TOWN_MILES = 40;         // "the nearest town we know" is only named when it is this close
  var HUB_HINT_MILES = 60;             // offer "every role in the area" when home is this close to a hub's main town

  var FAMILIES = D.families, LEVELS = D.levels, METROS = D.metros, STAGES = D.stages, SECTORS = D.sectors;
  var famLabel = {}, lvlLabel = {}, metroLabel = {}, stageLabel = {};
  FAMILIES.forEach(function (f) { famLabel[f[0]] = f[1]; });
  LEVELS.forEach(function (l) { lvlLabel[l[0]] = l[1]; });
  METROS.forEach(function (m) { metroLabel[m[0]] = m[1]; });
  STAGES.forEach(function (s) { stageLabel[s[0]] = s[1]; });

  // The family layer reads columns the pipeline appends. Data written before a column existed
  // (the scheduled job regenerates it a few hours after a deploy) simply lacks the control.
  var JOB_FIELDS = D.jobFields || [], COMPANY_FIELDS = D.companyFields || [];
  var COL_PLACES = JOB_FIELDS.indexOf('places'), COL_TYPES = JOB_FIELDS.indexOf('roleTypes'), COL_CARD = COMPANY_FIELDS.indexOf('card');
  var ROLE_TYPES = Array.isArray(D.roleTypes) ? D.roleTypes : [];          // [code, label, about, bit, across]
  var PLACES = Array.isArray(D.places) ? D.places : [];                    // [name, state, lat, lng, approximate]
  var ENTRY_BIT = D.entryLevelBit || 0;
  var US_METROS = {};
  (D.usMetros || []).forEach(function (m) { US_METROS[m] = true; });
  var HAS = {
    types: COL_TYPES >= 0 && ROLE_TYPES.length > 0,
    places: COL_PLACES >= 0 && PLACES.length > 0,
    card: COL_CARD >= 0,
    entry: COL_TYPES >= 0 && ENTRY_BIT > 0,
    nodegree: !!(D.totals && D.totals.noDegree > 0)          // hidden until the pipeline has read real posting text
  };
  var typeLabel = {};
  ROLE_TYPES.forEach(function (r) { typeLabel[r[0]] = r[1]; });

  var SECTOR_ICON = {
    'Space & Aerospace': '🚀', 'Defense & Security': '🛡️', 'Nuclear Energy': '⚛️', 'AI & Software': '🤖',
    'Robotics & Manufacturing': '🦾', 'Chips & Semiconductors': '💾', 'Climate & Energy': '⚡', 'Drones & Autonomous': '🛸',
    'Biotech & Health': '🧬', 'Quantum Computing': '🔮', 'Transportation': '🚄', 'Housing & Construction': '🏗️',
    'Ocean & Maritime': '🌊', 'Consumer Tech': '📱', 'Supersonic & Hypersonic': '✈️', 'Infrastructure & Logistics': '🚚'
  };
  var FAMILY_ICON = {
    manufacturing: '🔧', software: '💻', ml: '🧠', mechanical: '⚙️', electrical: '🔌', firmware: '📟', propulsion: '🚀',
    systems: '🧩', controls: '🎛️', test: '🧪', science: '🔬', supply: '📦', program: '🗂️', operations: '🏭', fde: '🧭',
    it: '🖥️', product: '🎨', data: '📊', sales: '🤝', gna: '📋', leadership: '🏛️', general: '📬', other: '•'
  };
  var TYPE_ICON = { hands: '🔧', engineering: '📐', software: '💻', business: '📋', early: '🎓' };

  // Search synonyms: query token -> alternatives (any match counts)
  var SYN = {
    'ml': ['machine learning', 'ml'], 'machine learning': ['machine learning', 'ml'], 'ai': ['ai', 'machine learning', ' ml'],
    'swe': ['software engineer', 'software'], 'software': ['software', 'swe'], 'dev': ['developer', 'software'],
    'mech': ['mechanical'], 'mechanical': ['mechanical', 'mech'], 'me': ['mechanical'],
    'ee': ['electrical'], 'electrical': ['electrical', 'ee'],
    'gnc': ['gnc', 'guidance', 'navigation'], 'guidance': ['guidance', 'gnc'],
    'pm': ['product manager', 'program manager', 'project manager'], 'tpm': ['technical program manager', 'tpm'],
    'welder': ['weld'], 'welding': ['weld'], 'weld': ['weld'],
    'machinist': ['machinist', 'machining', 'cnc'], 'cnc': ['cnc', 'machinist', 'machining'],
    'technician': ['technician', 'tech'], 'tech': ['tech'],
    'bd': ['business development', 'bd'], 'sales': ['sales', 'account executive', 'account manager'],
    'recruiter': ['recruit', 'talent'], 'recruiting': ['recruit', 'talent'], 'hr': ['people', 'human resources', 'hr'],
    'ops': ['operations', 'ops'], 'operations': ['operations', 'ops'],
    'qa': ['quality', 'qa'], 'quality': ['quality', 'qa'],
    'sre': ['site reliability', 'sre'], 'devops': ['devops', 'infrastructure', 'platform'],
    'intern': ['intern', 'co-op', 'internship'], 'internship': ['intern', 'co-op'], 'interns': ['intern', 'co-op'],
    'new grad': ['new grad', 'graduate', 'entry level', 'entry-level'], 'graduate': ['graduate', 'new grad'],
    'junior': ['junior', 'new grad', 'entry level', 'new grad / junior'], 'entry level': ['entry level', 'entry-level', 'new grad', 'junior'],
    'embedded': ['embedded', 'firmware'], 'firmware': ['firmware', 'embedded'], 'avionics': ['avionics'], 'fpga': ['fpga'],
    'controls': ['controls', 'control systems', 'plc', 'automation'], 'plc': ['plc', 'controls'],
    'robotics': ['robot'], 'robot': ['robot'], 'humanoid': ['humanoid'],
    'autonomy': ['autonomy', 'autonomous', 'perception'], 'autonomous': ['autonomous', 'autonomy'],
    'perception': ['perception', 'computer vision'], 'cv': ['computer vision', 'perception'],
    'manufacturing': ['manufactur', 'production'], 'production': ['production', 'manufactur'],
    'supply chain': ['supply chain', 'procurement', 'sourcing', 'buyer', 'supply'], 'procurement': ['procurement', 'sourcing', 'buyer', 'supply chain'], 'sourcing': ['sourcing', 'procurement', 'buyer'],
    'finance': ['finance', 'financ', 'accounting', 'fp&a'], 'accounting': ['accounting', 'accountant'], 'legal': ['legal', 'counsel', 'attorney'],
    'clearance': ['clearance', 'cleared', 'ts/sci', 'top secret', 'secret'], 'cleared': ['cleared', 'clearance'], 'ts/sci': ['ts/sci', 'clearance', 'top secret'], 'secret': ['secret', 'clearance'],
    'rf': ['rf', 'radio frequency', 'antenna', 'microwave'], 'antenna': ['antenna', 'rf'],
    'asic': ['asic', 'silicon', 'rtl'], 'silicon': ['silicon', 'asic', 'chip'], 'chip': ['chip', 'silicon', 'asic'],
    'thermal': ['thermal', 'heat'], 'structures': ['structur'], 'structural': ['structur'],
    'propulsion': ['propulsion', 'engine', 'rocket'], 'rocket': ['rocket', 'propulsion', 'launch'], 'engine': ['engine'],
    'test': ['test'], 'safety': ['safety', 'ehs'], 'ehs': ['ehs', 'safety', 'environmental health'],
    'data': ['data', 'analytics'], 'analyst': ['analyst', 'analytics'], 'remote': ['remote'],
    'nuclear': ['nuclear', 'reactor'], 'reactor': ['reactor', 'nuclear'], 'fusion': ['fusion', 'plasma'], 'quantum': ['quantum'],
    'bio': ['bio'], 'satellite': ['satellite', 'spacecraft'], 'spacecraft': ['spacecraft', 'satellite'], 'space': ['space'],
    'drone': ['drone', 'uav', 'uas'], 'uav': ['uav', 'drone', 'uas'], 'battery': ['battery', 'cell'], 'solar': ['solar', 'photovoltaic', 'pv'],
    'security': ['security'], 'it': ['it ', 'help desk', 'sysadmin', 'it &'], 'network': ['network'],
    'director': ['director', 'head of'], 'vp': ['vp', 'vice president'], 'chief': ['chief'], 'founding': ['founding'],
    'fde': ['forward deployed', 'fde'], 'forward deployed': ['forward deployed', 'fde'], 'field': ['field'],
    'program': ['program'], 'project': ['project'], 'product': ['product'], 'design': ['design'], 'designer': ['designer', 'design'],
    'marketing': ['marketing', 'growth'], 'customer': ['customer'], 'support': ['support'], 'success': ['success'],
    'electrician': ['electrician', 'electrical technician'], 'hvac': ['hvac'], 'composite': ['composite'], 'additive': ['additive', '3d print'],
    'optical': ['optical', 'photonic', 'laser'], 'photonics': ['photonic', 'optical'], 'laser': ['laser', 'optical'],
    'simulation': ['simulation', 'sim'], 'materials': ['material'], 'chemist': ['chem'], 'chemistry': ['chem'], 'physicist': ['physic'], 'physics': ['physic'],
    'scientist': ['scientist', 'research'], 'research': ['research', 'scientist'], 'phd': ['phd', 'postdoc', 'research'],
    'starlink': ['starlink'], 'starship': ['starship'], 'spacex': ['spacex'], 'anduril': ['anduril'],
    'london': ['london'], 'uk': ['uk', 'london', 'united kingdom', 'england'], 'germany': ['germany', 'munich', 'berlin', 'bavaria'], 'munich': ['munich', 'bavaria'],
    'paris': ['paris'], 'france': ['france', 'paris'], 'toronto': ['toronto'], 'canada': ['canada', 'toronto'], 'tel aviv': ['tel aviv', 'israel'], 'israel': ['israel', 'tel aviv'],
    'europe': ['europe', 'germany', 'uk', 'france', 'international', 'london', 'munich', 'paris'], 'international': ['international', 'london', 'munich', 'paris', 'toronto', 'tel aviv'],
    'sf': ['sf bay', 'san francisco'], 'bay area': ['sf bay', 'bay area', 'san francisco'], 'la': ['los angeles'], 'nyc': ['new york'], 'dc': ['washington dc', 'washington, dc'], 'texas': ['texas', 'austin'], 'austin': ['austin', 'texas'], 'seattle': ['seattle'], 'boston': ['boston'], 'denver': ['denver', 'colorado'], 'colorado': ['colorado', 'denver']
  };

  // ─── Expand compact rows ──────────────────────────────────────────────────
  var now = new Date();
  var todayUTC = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  var generatedUTC = (function () { var p = (D.generated || '').split('-'); return p.length === 3 ? Date.UTC(+p[0], +p[1] - 1, +p[2]) : todayUTC; })();
  var drift = Math.max(0, Math.round((todayUTC - generatedUTC) / MS_DAY)); // days since the data was generated

  var companies = D.companies.map(function (r, i) {
    return {
      i: i, name: r[0], sector: SECTORS[r[1]] || 'Other', stage: STAGES[r[2]] ? STAGES[r[2]][0] : 'other',
      il30: !!(r[3] & CF.IL30), hardTech: !!(r[3] & CF.HARDTECH), inDb: !!(r[3] & CF.INDB), surge: !!(r[3] & CF.SURGE),
      raisedAmount: r[4] || '', raisedRound: r[5] || '', raisedMonth: r[6] || '', fundingStage: r[7] || '', jobs: r[8] || 0,
      canonical: r[9] || r[0], recent14: r[10] || 0, prior14: r[11] || 0, roles: r[12] || r[8] || 0,
      card: HAS.card ? (r[COL_CARD] || 0) : null          // null: no card column in this data; 0: company not in the database
    };
  });

  function atsUrl(id, url) {
    if (url) return url;
    if (id.indexOf('gh-') === 0) {
      var k = id.lastIndexOf('-');
      return 'https://job-boards.greenhouse.io/' + id.slice(3, k) + '/jobs/' + id.slice(k + 1);
    }
    if (id.indexOf('ab-') === 0) return 'https://jobs.ashbyhq.com/' + id.slice(3, -37) + '/' + id.slice(-36);
    if (id.indexOf('lv-') === 0) return 'https://jobs.lever.co/' + id.slice(3, -37) + '/' + id.slice(-36);
    return '';
  }

  function utcOf(iso) { var p = iso.split('-'); return Date.UTC(+p[0], +p[1] - 1, +p[2]); }
  function daysSince(posted, fallback) {
    if (!posted) return fallback >= 0 ? fallback : -1;
    return Math.max(0, Math.round((todayUTC - utcOf(posted)) / MS_DAY));
  }
  function daysUntil(iso) { return iso ? Math.round((utcOf(iso) - todayUTC) / MS_DAY) : null; }
  function placeList(v) {                               // -1 | 12 | [12, 40] -> [] | [12] | [12, 40]
    if (typeof v === 'number') return v >= 0 && PLACES[v] ? [v] : [];
    return Array.isArray(v) ? v.filter(function (p) { return !!PLACES[p]; }) : [];
  }

  // one record per posting
  var jobs = D.jobs.map(function (r, i) {
    var c = companies[r[1]];
    var fam = FAMILIES[r[6]] ? FAMILIES[r[6]][0] : 'other';
    var lvl = LEVELS[r[7]] ? LEVELS[r[7]][0] : 'mid';
    var metros = r[8] ? r[8].split(',') : [];
    var days = daysSince(r[4], r[13]);
    var updDays = r[14] >= 0 ? r[14] + drift : -1;
    var flags = r[12];
    return {
      i: i, id: r[0], c: c, title: r[2], location: r[3], posted: r[4], url: atsUrl(r[0], r[5]),
      fam: fam, lvl: lvl, metros: metros, salMin: r[9], salMax: r[10], cur: D.currencies[r[11]] || 'USD',
      salText: !!(flags & F.SALTEXT), salHourly: !!(flags & F.SALHOURLY), lvlDesc: !!(flags & F.LVLDESC),
      days: days, updDays: updDays, stale: !!(flags & F.STALE) || updDays > STALE_DAYS,
      remote: !!(flags & F.REMOTE), clearance: !!(flags & F.CLEARANCE), usPerson: !!(flags & F.USPERSON),
      trades: !!(flags & F.TRADES), summer27: !!(flags & F.SUMMER27), general: !!(flags & F.GENERAL),
      noDegree: !!(flags & F.NODEGREE),
      mask: HAS.types ? (r[COL_TYPES] || 0) : 0,
      places: HAS.places ? placeList(r[COL_PLACES]) : [],
      group: typeof r[15] === 'number' ? r[15] : -1, deadline: r[16] || '', deadlineDays: daysUntil(r[16] || '')
    };
  });
  var jobById = {};
  jobs.forEach(function (j) { jobById[j.id] = j; });

  // Fold per-location clones into their primary row. The primary is the newest posting of the
  // role; it keeps every member so the row can expand, filters on the union of their metros, and
  // only counts as stale when every posting is.
  function uniq(arr) { var seen = {}, out = []; arr.forEach(function (v) { if (v !== '' && v != null && !seen[v]) { seen[v] = 1; out.push(v); } }); return out; }
  var rows = [];
  jobs.forEach(function (j) { if (j.group < 0) { j.members = [j]; rows.push(j); } });
  jobs.forEach(function (j) {
    if (j.group >= 0) {
      var p = jobs[j.group];
      if (p && p.members) { p.members.push(j); j.primary = p; }
      else { j.members = [j]; rows.push(j); }
    }
  });
  rows.forEach(function (r) {
    var ms = r.members;
    r.n = ms.length;
    r.locations = uniq(ms.map(function (m) { return m.location; }));
    r.allMetros = uniq([].concat.apply([], ms.map(function (m) { return m.metros; })));
    r.allPlaces = uniq([].concat.apply([], ms.map(function (m) { return m.places.map(function (p) { return 'p' + p; }); }))).map(function (k) { return +k.slice(1); });
    r.firstDays = -1;
    ms.forEach(function (m) { if (m.days > r.firstDays) r.firstDays = m.days; });
    r.anyStale = r.stale; r.stale = ms.every(function (m) { return m.stale; });
    r.remote = ms.some(function (m) { return m.remote; });
    r.clearance = ms.some(function (m) { return m.clearance; });
    r.usPerson = ms.some(function (m) { return m.usPerson; });
    r.noDegree = ms.some(function (m) { return m.noDegree; });
    // a US reader can take a remote role unless every place it names is abroad
    r.inUS = r.allMetros.some(function (m) { return US_METROS[m]; });
    r.remoteUS = r.remote && (r.inUS || r.allMetros.every(function (m) { return m === 'remote'; }));
    r.dist = Infinity; r.distApprox = false; r.distPlace = -1;       // filled in when the reader gives a home
    if (!(r.salMin || r.salMax)) {
      var w = null; ms.forEach(function (m) { if (!w && (m.salMin || m.salMax)) w = m; });
      if (w) { r.salMin = w.salMin; r.salMax = w.salMax; r.cur = w.cur; r.salText = w.salText; r.salHourly = w.salHourly; }
    }
    var dd = null, dIso = '';
    ms.forEach(function (m) { if (m.deadlineDays !== null && m.deadlineDays >= 0 && (dd === null || m.deadlineDays < dd)) { dd = m.deadlineDays; dIso = m.deadline; } });
    r.deadlineDays = dd; r.deadline = dIso;
    r.isNew = r.firstDays >= 0 && r.firstDays <= NEW_DAYS;
    r.closing = dd !== null && dd <= CLOSING_DAYS;
    r.hay = (r.title + ' ' + r.c.name + ' ' + r.locations.join(' ') + ' ' + (famLabel[r.fam] || '') + ' ' + (lvlLabel[r.lvl] || '') + ' ' + r.c.sector + ' ' +
      r.allMetros.map(function (m) { return metroLabel[m] || ''; }).join(' ')).toLowerCase();
  });

  // Talent tab compatibility (talent.js reads JOBS_DATA / JOBS_STATS): one record per posting
  (function exposeLegacy() {
    var byCompany = {}, bySector = {}, remote = 0;
    window.JOBS_DATA = jobs.map(function (j) {
      byCompany[j.c.name] = (byCompany[j.c.name] || 0) + 1;
      bySector[j.c.sector] = (bySector[j.c.sector] || 0) + 1;
      if (j.remote) remote++;
      return { id: j.id, company: j.c.name, title: j.title, location: j.location, department: famLabel[j.fam] || '', type: '', posted: j.posted, url: j.url, remote: j.remote, sector: j.c.sector, source: j.id.slice(0, 2), salaryMin: j.salMin || null, salaryMax: j.salMax || null, salaryCurrency: j.salMin || j.salMax ? j.cur : null };
    });
    window.JOBS_STATS = { totalJobs: jobs.length, companiesHiring: companies.length, byCompany: byCompany, bySector: bySector, remoteJobs: remote, lastUpdated: (D.totals && D.totals.lastUpdated) || '' };
  })();

  // ─── State ────────────────────────────────────────────────────────────────
  var defaultState = L.defaultState;
  var state = defaultState();
  var shown = PAGE;
  var shownGroups = GROUP_PAGE;
  var expanded = {};   // row index -> true while its postings list is open
  var openCards = {};  // 'r<row index>' or 'c<company index>' -> true while its employer facts are open

  var SHELVES = [
    { key: 'new', icon: '🆕', title: 'New this week', blurb: 'Roles first posted in the last ' + NEW_DAYS + ' days (a new location on an old role does not count)', test: function (j) { return j.isNew; }, apply: function (s) {} },
    { key: 'surge', icon: '📈', title: 'Hiring surge', blurb: 'Companies that posted 50%+ more roles in the last ' + SURGE_DAYS + ' days than in the ' + SURGE_DAYS + ' before', test: function (j) { return j.c.surge; }, apply: function (s) {} },
    { key: 'trades', icon: '🔧', title: 'Hard-tech trades', blurb: 'Technicians, welders, machinists, electricians', test: function (j) { return j.trades && j.c.hardTech; }, apply: function (s) { s.hardtech = true; } },
    { key: 'interns', icon: '🎓', title: 'Summer 2027 internships', blurb: 'Posted for next summer, newest first', test: function (j) { return j.summer27; }, apply: function (s) { s.intern = true; } },
    { key: 'raised', icon: '💵', title: 'Raised this quarter', blurb: 'Companies that closed a round in the last ' + (D.raisedWindowDays || 90) + ' days', test: function (j) { return !!j.c.raisedMonth; }, apply: function (s) {} },
    { key: 'il30', icon: '🏆', title: 'IL30 hiring now', blurb: 'Open roles at the Innovators League 30', test: function (j) { return j.c.il30; }, apply: function (s) { s.il30 = true; } },
    { key: 'remote', icon: '🌐', title: 'Remote hard-tech', blurb: 'Remote-friendly roles at hardware companies', test: function (j) { return j.remote && j.c.hardTech; }, apply: function (s) { s.remote = true; s.hardtech = true; } },
    { key: 'cleared', icon: '🛡️', title: 'Cleared roles', blurb: 'Postings that call for a security clearance', test: function (j) { return j.clearance; }, apply: function (s) { s.clearance = 'only'; } },
    { key: 'closing', icon: '⏳', title: 'Closing soon', blurb: 'Postings that state an application deadline within ' + CLOSING_DAYS + ' days (all sectors)', test: function (j) { return j.closing; }, apply: function (s) { s.hardtech = false; } }
  ];
  var shelfByKey = {};
  SHELVES.forEach(function (s) { shelfByKey[s.key] = s; });

  // ─── URL sync ─────────────────────────────────────────────────────────────
  function readUrl() {
    var s = L.parseQuery(location.search);
    s.type = s.type.filter(function (t) { return !!typeLabel[t]; });
    if (!HAS.places && s.near.indexOf('hub:') !== 0) s.near = '';   // no places in this data: only a hub can be searched
    if (s.shelf && shelfByKey[s.shelf]) shelfByKey[s.shelf].apply(s);
    return s;
  }
  function writeUrl() {
    var qs = L.buildQuery(state);
    var url = location.pathname + (qs ? '?' + qs : '') + location.hash;
    try { history.replaceState(null, '', url); } catch (e) { /* ignore */ }
  }
  // The address of this board with a search on it, for links people copy and for the printout.
  function boardUrl(query) {
    return location.href.split('#')[0].split('?')[0] + (query ? '?' + query : '');
  }
  function searchQuery() {                                // the current search, without the shared job
    var s = {}, k;
    for (k in state) if (Object.prototype.hasOwnProperty.call(state, k)) s[k] = state[k];
    s.job = '';
    return L.buildQuery(s);
  }

  // ─── Home: where the reader is searching from ─────────────────────────────
  // origin is what state.near resolved to. A point ({ kind: 'place' | 'zip' | 'me' }) is measured
  // against; a hub ({ kind: 'hub' }) means "anywhere in that area" and uses the hub the pipeline
  // already gave each role. myPoint is the browser's own location: memory only, never stored,
  // never put in the address bar (state.near says 'me', nothing more).
  var geo = { idx: null, loading: false, failed: false, waiting: [] };
  var origin = null;
  var myPoint = null;
  var nearNote = { text: '', bad: false };               // one-off message for the status line (errors)
  var settledFor = null;                                 // the state.near value origin was last worked out for
  var ME_LABEL = 'My location';

  function loadGeo(cb) {
    if (geo.idx || geo.failed) { if (cb) cb(); return; }
    if (cb) geo.waiting.push(cb);
    if (geo.loading) return;
    geo.loading = true;
    var done = function (payload) {
      geo.loading = false;
      geo.idx = L.geoIndex(payload);
      if (!geo.idx.ok) { geo.idx = null; geo.failed = true; }
      var w = geo.waiting; geo.waiting = [];
      w.forEach(function (f) { f(); });
    };
    if (!window.fetch) { done(null); return; }
    fetch(GEO_URL, { credentials: 'omit' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(done, function () { done(null); });
  }

  function hubOrigin(code) {
    return metroLabel[code] ? { kind: 'hub', code: code, label: metroLabel[code], value: 'hub:' + code } : null;
  }

  // Work out origin from state.near. A town needs the places file; while it loads, nothing is
  // filtered and the status line says so, and the board renders again when it arrives.
  function settleOrigin() {
    var near = state.near, was = origin;
    origin = null;
    settledFor = near;
    if (near === 'me') {
      if (myPoint) origin = { kind: 'me', label: 'your location', value: 'me', lat: myPoint.lat, lng: myPoint.lng };
      else state.near = settledFor = '';
    } else if (near.indexOf('hub:') === 0) {
      origin = hubOrigin(near.slice(4));
      if (!origin) state.near = settledFor = '';
    } else if (near) {
      if (geo.idx) {
        var res = L.resolveNear(near, geo.idx);
        if (res.ok) origin = res.kind === 'hub' ? hubOrigin(res.code) : res;
        if (origin) state.near = settledFor = origin.value;          // the plain spelling goes in the link
        else { nearNote = { text: nearProblem(res, near), bad: true }; state.near = settledFor = ''; }
      } else if (!geo.failed) {
        loadGeo(function () { if (state.near === near) { settledFor = null; render(true); } });
      } else {
        nearNote = { text: 'The list of places could not be loaded, so “' + near + '” cannot be looked up. “Use my location” still works.', bad: true };
        state.near = settledFor = '';
      }
    }
    measure(was);
  }

  // Distance from the origin to every town the postings name, then the nearest for each role.
  function measure(was) {
    var o = origin && origin.kind !== 'hub' ? origin : null;
    if (was && o && was.kind !== 'hub' && was.lat === o.lat && was.lng === o.lng) return;
    var d = null, i;
    if (o) {
      d = new Array(PLACES.length);
      for (i = 0; i < PLACES.length; i++) d[i] = L.haversineMiles(o.lat, o.lng, PLACES[i][2], PLACES[i][3]);
    }
    for (i = 0; i < rows.length; i++) {
      var r = rows[i], best = Infinity, at = -1;
      if (d) for (var k = 0; k < r.allPlaces.length; k++) { var p = r.allPlaces[k]; if (d[p] < best) { best = d[p]; at = p; } }
      r.dist = best; r.distPlace = at; r.distApprox = at >= 0 && !!PLACES[at][4];
    }
  }

  function nearProblem(res, typed) {
    var known = geo.idx ? fmtN(geo.idx.places.filter(Boolean).length) : '';
    switch (res.reason) {
      case 'no-zips': return 'ZIP codes are not loaded on this site yet. Type a city and pick it from the list, or choose “Use my location”.';
      case 'zip-short': return 'A ZIP code has five digits. “' + typed + '” has ' + typed.length + '.';
      case 'zip-unknown': return 'We do not have ZIP code ' + typed + '. Try the name of the town.';
      case 'ambiguous': return 'There is more than one ' + L.splitTown(typed)[0] + '. Pick one: ' + res.options.join('; ') + '.';
      default: return 'We do not have “' + typed + '” on our list of ' + known + ' places. Check the spelling, add the state (for example “Austin, TX”), or choose “Use my location”.';
    }
  }

  function sortMode() {
    var point = origin && origin.kind !== 'hub';
    if (state.sort === 'near') return point ? 'near' : 'new';
    if (state.sort === 'new') return 'new';
    return point ? 'near' : 'new';
  }

  // ─── Filtering (over grouped rows) ────────────────────────────────────────
  function queryTerms(q) {
    q = (q || '').trim().toLowerCase();
    if (!q) return [];
    if (SYN[q]) return [SYN[q]];
    return q.split(/\s+/).map(function (w) { return SYN[w] || [w]; });
  }

  function isCompany(c, name) { return c.name === name || c.canonical === name; }

  var maskCache = { key: null };
  function masksOf(s) {                                   // the chosen plain types as bit masks; with each half left out, for counts
    var key = s.type.join(',');
    if (maskCache.key !== key) {
      var m = L.typeMasks(s.type, ROLE_TYPES);
      maskCache = { key: key, all: m, noWork: { work: 0, across: m.across }, noAcross: { work: m.work, across: 0 } };
    }
    return maskCache;
  }

  // The filters families ask about. `except` leaves one out, to count what switching it on would give.
  var TOGGLES = [
    { key: 'nodegree', test: function (j) { return j.noDegree; } },
    { key: 'entry', test: function (j) { return (j.mask & ENTRY_BIT) !== 0; } },
    { key: 'salary', test: function (j) { return !!(j.salMin || j.salMax); } },
    { key: 'citizen', tri: true, test: function (j) { return j.usPerson; } },
    { key: 'clearance', tri: true, test: function (j) { return j.clearance; } }
  ];
  function togglesOk(j, s, except) {
    for (var i = 0; i < TOGGLES.length; i++) {
      var t = TOGGLES[i], v = s[t.key];
      if (!v || t.key === except) continue;
      if (t.test(j) !== (v !== 'hide')) return false;     // true / 'only': must have it; 'hide': must not
    }
    return true;
  }

  // Home. Only the search on screen has one (shelf counts are taken on default states, without).
  function nearOk(j, s) {
    if (!s.near || !origin) return true;
    if (origin.kind === 'hub') return j.allMetros.indexOf(origin.code) >= 0 || (s.plusremote && j.remoteUS);
    if (!(s.within > 0)) return true;                     // "Open to moving": no distance limit
    return j.dist <= s.within || (s.plusremote && j.remoteUS);
  }

  // skip: the part of the search to ignore, so a control can count what it would add
  function matches(j, s, terms, skip) {
    if (skip !== 'family' && s.family.length && s.family.indexOf(j.fam) < 0) return false;
    if (skip !== 'metro' && s.metro.length && !j.allMetros.some(function (m) { return s.metro.indexOf(m) >= 0; })) return false;
    if (skip !== 'sector' && s.sector.length && s.sector.indexOf(j.c.sector) < 0) return false;
    if (skip !== 'level' && s.level.length && s.level.indexOf(j.lvl) < 0) return false;
    if (skip !== 'stage' && s.stage.length && s.stage.indexOf(j.c.stage) < 0) return false;
    if (s.company && !isCompany(j.c, s.company)) return false;
    if (s.hardtech && !s.company && !j.c.hardTech) return false; // asking for one company shows it whatever its sector
    if (s.remote && !j.remote) return false;
    if (s.intern && j.lvl !== 'intern') return false;
    if (s.il30 && !j.c.il30) return false;
    if (s.posted && (j.days < 0 || j.days > s.posted)) return false;
    if (!s.stale && j.stale) return false;
    if (s.shelf && shelfByKey[s.shelf] && !shelfByKey[s.shelf].test(j)) return false;
    if (s.type.length) {
      var tm = masksOf(s);
      if (!L.typeMatches(j.mask, skip === 'type-work' ? tm.noWork : skip === 'type-across' ? tm.noAcross : tm.all)) return false;
    }
    if (skip !== 'toggles' && !togglesOk(j, s, null)) return false;
    if (skip !== 'near' && !nearOk(j, s)) return false;
    if (terms.length) {
      for (var t = 0; t < terms.length; t++) {
        var alts = terms[t], ok = false;
        for (var a = 0; a < alts.length; a++) { if (j.hay.indexOf(alts[a]) >= 0) { ok = true; break; } }
        if (!ok) return false;
      }
    }
    return true;
  }

  function byNewest(a, b) {
    if (a.posted !== b.posted) { if (!a.posted) return 1; if (!b.posted) return -1; return a.posted < b.posted ? 1 : -1; }
    var ca = a.c.name.toLowerCase(), cb = b.c.name.toLowerCase();
    if (ca !== cb) return ca < cb ? -1 : 1;
    return a.title.toLowerCase() < b.title.toLowerCase() ? -1 : 1;
  }

  function run() {
    if (state.job) {                                      // a link to one job: show that role, whatever else is set
      var jj = jobById[state.job], row = jj ? (jj.primary || jj) : null;
      return row && row.members ? [row] : [];
    }
    var terms = queryTerms(state.q);
    var out = [];
    for (var i = 0; i < rows.length; i++) if (matches(rows[i], state, terms, null)) out.push(rows[i]);
    // newest first; undated last; then company A–Z, title. On a distance search: nearest first.
    if (sortMode() === 'near') out.sort(function (a, b) { return a.dist !== b.dist ? (a.dist < b.dist ? -1 : 1) : byNewest(a, b); });
    else out.sort(byNewest);
    return out;
  }

  function facetCounts(key, terms) {
    var counts = {};
    for (var i = 0; i < rows.length; i++) {
      var j = rows[i];
      if (!matches(j, state, terms, key)) continue;
      if (key === 'metro') { for (var m = 0; m < j.allMetros.length; m++) counts[j.allMetros[m]] = (counts[j.allMetros[m]] || 0) + 1; }
      else if (key === 'family') counts[j.fam] = (counts[j.fam] || 0) + 1;
      else if (key === 'sector') counts[j.c.sector] = (counts[j.c.sector] || 0) + 1;
      else if (key === 'level') counts[j.lvl] = (counts[j.lvl] || 0) + 1;
      else if (key === 'stage') counts[j.c.stage] = (counts[j.c.stage] || 0) + 1;
    }
    return counts;
  }

  // Roles each plain type would show, given everything else that is set.
  function typeCounts(terms) {
    var counts = {}, i, k;
    ROLE_TYPES.forEach(function (r) { counts[r[0]] = 0; });
    for (i = 0; i < rows.length; i++) {
      var j = rows[i];
      if (matches(j, state, terms, 'type-work')) for (k = 0; k < ROLE_TYPES.length; k++) if (!ROLE_TYPES[k][4] && (j.mask & ROLE_TYPES[k][3])) counts[ROLE_TYPES[k][0]]++;
      if (matches(j, state, terms, 'type-across')) for (k = 0; k < ROLE_TYPES.length; k++) if (ROLE_TYPES[k][4] && (j.mask & ROLE_TYPES[k][3])) counts[ROLE_TYPES[k][0]]++;
    }
    return counts;
  }

  // Roles each family filter would leave if it were switched on (to "only these", for the two-way ones).
  function toggleCounts(terms) {
    var counts = {}, i, k;
    TOGGLES.forEach(function (t) { counts[t.key] = 0; });
    for (i = 0; i < rows.length; i++) {
      var j = rows[i];
      if (!matches(j, state, terms, 'toggles')) continue;
      for (k = 0; k < TOGGLES.length; k++) if (TOGGLES[k].test(j) && togglesOk(j, state, TOGGLES[k].key)) counts[TOGGLES[k].key]++;
    }
    return counts;
  }

  // What a distance search leaves out, said plainly: roles in US towns the places file cannot put
  // on a map, remote jobs, and the hub the reader's home sits in.
  function nearSideCounts(terms) {
    var out = { unplaced: 0, remote: 0, hub: null, hubUnplaced: 0 };
    if (!state.near || !origin || origin.kind === 'hub' || !(state.within > 0)) return out;
    if (geo.idx) {
      var best = HUB_HINT_MILES;
      geo.idx.hubs.forEach(function (h) {
        var d = L.haversineMiles(origin.lat, origin.lng, h.lat, h.lng);
        if (d <= best && metroLabel[h.code]) { best = d; out.hub = h; }
      });
    }
    for (var i = 0; i < rows.length; i++) {
      var j = rows[i];
      if (!matches(j, state, terms, 'near')) continue;
      if (j.remoteUS && !(j.dist <= state.within)) out.remote++;
      if (j.inUS && !j.allPlaces.length) {
        out.unplaced++;
        if (out.hub && j.allMetros.indexOf(out.hub.code) >= 0) out.hubUnplaced++;
      }
    }
    return out;
  }

  // Cap: no company shows more than COMPANY_CAP rows unless the reader asked for that company
  function capByCompany(list) {
    if (state.company || state.q) return { rows: list, capped: {} };
    var seen = {}, out = [], capped = {};
    for (var i = 0; i < list.length; i++) {
      var j = list[i], n = seen[j.c.i] || 0;
      if (n < COMPANY_CAP) { out.push(j); seen[j.c.i] = n + 1; }
      else { capped[j.c.i] = (capped[j.c.i] || 0) + 1; }
    }
    return { rows: out, capped: capped };
  }

  // ─── Formatting ───────────────────────────────────────────────────────────
  var CUR_SYMBOL = { USD: '$', GBP: '£', EUR: '€', CAD: 'C$', AUD: 'A$', SGD: 'S$', NZD: 'NZ$', INR: '₹', ILS: '₪', CHF: 'CHF ', PLN: 'zł', BRL: 'R$' };
  function money(v, cur) {
    var sym = CUR_SYMBOL[cur] || (cur ? cur + ' ' : '$');
    if (v >= 1000000) return sym + (v / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
    if (v >= 1000) return sym + Math.round(v / 1000) + 'K';
    return sym + v;
  }
  function hourly(v, cur) {
    var sym = CUR_SYMBOL[cur] || '$';
    var h = v / HOURS_PER_YEAR;
    return sym + (h < 100 ? h.toFixed(h % 1 ? 2 : 0).replace(/\.00$/, '') : Math.round(h));
  }
  function salaryText(j) {
    if (!j.salMin && !j.salMax) return '';
    if (j.salMin && j.salMax && j.salMin !== j.salMax) return money(j.salMin, j.cur) + '–' + money(j.salMax, j.cur);
    if (j.salMin && j.salMax) return money(j.salMin, j.cur);
    if (j.salMin) return money(j.salMin, j.cur) + '+';
    return 'Up to ' + money(j.salMax, j.cur);
  }
  function salaryHtml(j) {
    var s = salaryText(j);
    if (!s) return '';
    var hint = '', title = 'Salary range provided by the ATS';
    if (j.salHourly) {
      var lo = j.salMin || j.salMax, hi = j.salMax || j.salMin;
      hint = '≈ ' + hourly(lo, j.cur) + (hi !== lo ? '–' + hourly(hi, j.cur) : '') + '/hr';
      title = 'Hourly rate annualised at ' + fmtN(HOURS_PER_YEAR) + ' hours' + (j.salText ? ', read from the posting text' : '');
    } else if (j.salText) {
      hint = 'from posting'; title = 'Range read from the posting text, not from a structured ATS field';
    }
    return '<span class="jb-sal" title="' + esc(title) + '">💰 ' + esc(s) + (hint ? ' <span class="jb-hint">' + esc(hint) + '</span>' : '') + '</span>';
  }
  function age(days) {
    if (days < 0) return '';
    if (days === 0) return 'Today';
    if (days === 1) return '1d';
    if (days < 14) return days + 'd';
    if (days < 60) return Math.round(days / 7) + 'w';
    return Math.round(days / 30) + 'mo';
  }
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function shortDate(iso) { if (!iso) return ''; var p = iso.split('-'); return MONTHS[(+p[1] || 1) - 1] + ' ' + (+p[2]); }
  function raisedTag(c, long) {
    if (!c.raisedMonth) return '';
    var m = c.raisedMonth.split('-');
    var month = MONTHS[(+m[1] || 1) - 1] || '';
    var amt = c.raisedAmount ? 'raised ' + esc(c.raisedAmount) : 'raised';
    return '<span class="jb-tag jb-tag-raised" title="' + esc(c.raisedRound || 'Funding round') + ' ' + esc(c.raisedMonth) + '">💵 ' + amt + ' in ' + month + (long && c.raisedRound ? ' · ' + esc(c.raisedRound) : '') + '</span>';
  }
  function surgeTag(c) {
    if (!c.surge) return '';
    return '<span class="jb-tag jb-tag-surge" title="' + fmtN(c.recent14) + ' roles posted in the last ' + SURGE_DAYS + ' days vs ' + fmtN(c.prior14) + ' in the ' + SURGE_DAYS + ' before">📈 hiring surge · ' + fmtN(c.recent14) + ' in ' + SURGE_DAYS + 'd</span>';
  }
  function companyLink(c, cls) {
    if (!c.inDb) return '<span class="' + cls + '">' + esc(c.name) + '</span>';
    return '<a class="' + cls + '" href="company.html?name=' + encodeURIComponent(c.canonical) + '">' + esc(c.name) + '</a>';
  }
  function levelHtml(j) {
    if (j.lvl === 'mid' && !j.lvlDesc) return '';
    var label = lvlLabel[j.lvl] || '';
    if (!label) return '';
    if (j.lvlDesc) return '<span class="jb-lvl jb-lvl-desc" title="Level read from the years of experience the posting asks for; the title carries no level word">' + esc(label) + '</span>';
    return '<span class="jb-lvl">' + esc(label) + '</span>';
  }
  function locationHtml(j) {
    if (!j.locations.length) return '';
    var first = j.locations[0];
    var extra = j.locations.length - 1;
    var html = '<span class="jb-loc">📍 ' + esc(first);
    if (extra > 0) html += ' <button type="button" class="jb-expand" data-row="' + j.i + '" aria-expanded="' + (expanded[j.i] ? 'true' : 'false') + '">+' + extra + ' location' + (extra === 1 ? '' : 's') + '</button>';
    else if (j.n > 1) html += ' <button type="button" class="jb-expand" data-row="' + j.i + '" aria-expanded="' + (expanded[j.i] ? 'true' : 'false') + '">' + j.n + ' postings</button>';
    return html + '</span>';
  }
  function clonesHtml(j) {
    if (j.n < 2) return '';
    var items = j.members.slice().sort(function (a, b) { return a.posted === b.posted ? (a.location < b.location ? -1 : 1) : (a.posted < b.posted ? 1 : -1); }).map(function (m) {
      return '<li><span class="jb-clone-loc">📍 ' + esc(m.location || 'Location not given') + '</span>' +
        (m.stale ? '<span class="jb-pill jb-pill-stale">Older</span>' : '') +
        '<span class="jb-clone-age" title="' + esc(m.posted || 'Date not provided by the ATS') + '">' + esc(age(m.days)) + '</span>' +
        '<a class="jb-clone-apply" href="' + esc(m.url) + '" target="_blank" rel="noopener">Apply ↗</a></li>';
    });
    return '<ul class="jb-clones" id="jb-clones-' + j.i + '"' + (expanded[j.i] ? '' : ' hidden') + '>' + items.join('') + '</ul>';
  }
  function plural(n, one, many) { return n === 1 ? one : many; }

  // ─── Distance and employer facts ──────────────────────────────────────────
  function placeName(p) { var r = PLACES[p]; return r ? r[0] + ', ' + r[1] : ''; }
  function distanceHtml(j) {
    if (!origin || origin.kind === 'hub' || !isFinite(j.dist)) return '';
    var title = 'Straight-line distance from ' + (origin.kind === 'me' ? 'your location' : origin.label) + ' to ' + placeName(j.distPlace) +
      (j.distApprox ? '. The posting names an area, so this is measured to its main town.' : '');
    var text = (j.distApprox ? 'About ' : '') + L.milesText(j.dist) + (origin.kind === 'me' ? ' from you' : ' away');
    return '<span class="jb-dist" title="' + esc(title) + '">📏 ' + esc(text) + '</span>';
  }
  function whereText(j) {
    var t = j.locations[0] || (j.remote ? 'Remote' : '');
    if (j.locations.length > 1) t += ' (+' + (j.locations.length - 1) + ' more)';
    if (origin && origin.kind !== 'hub' && isFinite(j.dist)) t += ' · ' + (j.distApprox ? 'about ' : '') + L.milesText(j.dist);
    return t;
  }

  var CARD_AT = {};
  (D.cardFields || []).forEach(function (f, i) { CARD_AT[f] = i; });
  function cf(k, name) { return k && CARD_AT[name] !== undefined ? k[CARD_AT[name]] : undefined; }

  // postings: [now, nowDate, then, thenDate, boardChanged]; then is -1 (and thenDate the first count) when there is no earlier count
  function trendText(p) {
    if (!p) return 'No count of its job postings over time on record.';
    if (p[2] < 0) return fmtN(p[0]) + ' open job postings on ' + L.plainDate(p[1]) + '. First counted on ' + L.plainDate(p[3]) + ', so there is no count from about 90 days earlier yet.';
    if (p[4]) return fmtN(p[2]) + ' open job postings on ' + L.plainDate(p[3]) + ' and ' + fmtN(p[0]) + ' on ' + L.plainDate(p[1]) + '. The count changed too sharply to compare (usually a change of job board), so no direction is shown.';
    var d = p[0] - p[2];
    return (d > 0 ? 'Up by ' + fmtN(d) : d < 0 ? 'Down by ' + fmtN(-d) : 'No change') + ': ' + fmtN(p[2]) + ' open job postings on ' + L.plainDate(p[3]) + ', ' + fmtN(p[0]) + ' on ' + L.plainDate(p[1]) + '.';
  }

  // Facts only, each from the repo's own records; a missing fact is said to be missing.
  function cardHtml(c, key) {
    var k = c.card, items = [], body;
    var add = function (label, text) { items.push('<div class="jb-card-row"><dt>' + esc(label) + '</dt><dd>' + esc(text) + '</dd></div>'); };
    if (!k) {
      body = '<p>' + esc(c.name) + ' is not in our company database, so we have no facts about it to show. We list its jobs because its job board is public.</p>';
    } else {
      var round = cf(k, 'lastRound'), backers = cf(k, 'backers') || [], total = cf(k, 'backersTotal') || backers.length, field = cf(k, 'field');
      add('What it builds', cf(k, 'about') || 'No description on record.');
      if (field && field !== 'General') add('Field', field);
      if (cf(k, 'founded')) add('Founded', String(cf(k, 'founded')));
      if (cf(k, 'home')) add('Based in', cf(k, 'home'));
      if (cf(k, 'ticker')) add('Stock market', 'Listed as ' + cf(k, 'ticker'));
      add('Last funding round', round ? [round[0] || 'Funding round', round[1] || 'amount not disclosed', L.plainDate(round[2])].join(', ') : 'No public funding round on record.');
      add('Backed by', backers.length ? backers.join(', ') + (total > backers.length ? ' and ' + fmtN(total - backers.length) + ' more' : '') : 'No investors on record.');
      add('Open jobs over about 90 days', trendText(cf(k, 'postings')));
      body = '<dl>' + items.join('') + '</dl>';
    }
    return '<div class="jb-card" id="jb-card-' + key + '"><h4>Facts about ' + esc(c.name) + '</h4>' + body +
      '<p class="jb-card-note">From our company database, funding records and monthly counts of each company’s job board. We do not rate employers.' +
      (c.inDb ? ' <a href="company.html?name=' + encodeURIComponent(c.canonical) + '">Full company profile</a>' : '') + '</p></div>';
  }
  function cardButton(key, c) {
    var open = !!openCards[key];
    return '<button type="button" class="jb-act jb-card-btn" data-card="' + key + '" aria-expanded="' + open + '"' + (open ? ' aria-controls="jb-card-' + key + '"' : '') + '>' +
      (open ? 'Hide company facts' : 'Company facts') + '<span class="jb-sr"> about ' + esc(c.name) + '</span></button>';
  }
  function actionsHtml(j, compact) {
    var key = 'r' + j.i, b = [];
    if (HAS.card && !compact) b.push(cardButton(key, j.c));
    b.push('<button type="button" class="jb-act jb-copy" data-job="' + esc(j.id) + '"><span class="jb-copy-txt">Copy link</span><span class="jb-sr"> to this job: ' + esc(j.title) + ' at ' + esc(j.c.name) + '</span></button>');
    return '<div class="jb-actions">' + b.join('') + '</div>' + (HAS.card && !compact && openCards[key] ? cardHtml(j.c, key) : '');
  }

  // ─── Rendering ────────────────────────────────────────────────────────────
  function rowHtml(j, compact) {
    var c = j.c;
    var meta2 = [];
    var dist = distanceHtml(j); if (dist) meta2.push(dist);
    var loc = locationHtml(j); if (loc) meta2.push(loc);
    var lt = levelHtml(j); if (lt) meta2.push(lt);
    var sal = salaryHtml(j); if (sal) meta2.push(sal);
    if (j.isNew) meta2.push('<span class="jb-pill jb-pill-new" title="First posted ' + esc(age(j.firstDays) || 'this week') + ' ago">New</span>');
    if (j.remote) meta2.push('<span class="jb-pill jb-pill-remote">Remote</span>');
    if (HAS.nodegree && j.noDegree) meta2.push('<span class="jb-pill jb-pill-plain jb-pill-deg" title="The posting text says a college degree is not needed, or asks for a high-school diploma or GED">No degree required (likely)</span>');
    if (j.clearance) meta2.push('<span class="jb-pill jb-pill-plain jb-pill-clear" title="Read from the posting text">Clearance likely</span>');
    if (j.usPerson) meta2.push('<span class="jb-pill jb-pill-plain jb-pill-us" title="The posting text mentions US citizenship, permanent residence (green card) or US export rules">Citizen or green card likely</span>');
    if (j.deadlineDays !== null && j.deadlineDays >= 0 && j.deadlineDays <= 60) meta2.push('<span class="jb-pill jb-pill-close' + (j.closing ? ' jb-pill-urgent' : '') + '" title="Application deadline stated in the posting">Closes ' + esc(shortDate(j.deadline)) + '</span>');
    if (j.stale) meta2.push('<span class="jb-pill jb-pill-stale" title="No activity on the ATS for more than ' + STALE_DAYS + ' days">Older</span>');
    var head = compact ? '' :
      '<div class="jb-meta">' + companyLink(c, 'jb-company') +
      '<span class="jb-sector">' + (SECTOR_ICON[c.sector] || '') + ' ' + esc(c.sector) + '</span>' +
      (c.il30 ? '<span class="jb-tag jb-tag-il30" title="Innovators League 30">🏆 IL30</span>' : '') +
      raisedTag(c) + surgeTag(c) + '</div>';
    var ageTitle = (j.posted || 'Date not provided by the ATS') + (j.n > 1 && j.firstDays > j.days ? ' · first posted ' + age(j.firstDays) + ' ago' : '');
    return '<article class="jb-row' + (compact ? ' jb-row-compact' : '') + (j.n > 1 ? ' jb-row-grouped' : '') + '" data-row="' + j.i + '">' +
      '<div class="jb-row-main">' +
        '<a class="jb-title" href="' + esc(j.url) + '" target="_blank" rel="noopener">' + esc(j.title) + '</a>' +
        head +
        '<div class="jb-meta2">' + meta2.join('') + '</div>' +
        clonesHtml(j) + actionsHtml(j, compact) +
      '</div>' +
      '<div class="jb-row-side">' +
        '<span class="jb-age" title="' + esc(ageTitle) + '">' + esc(age(j.days)) + '</span>' +
        '<a class="jb-apply" href="' + esc(j.url) + '" target="_blank" rel="noopener">Apply ↗</a>' +
      '</div>' +
    '</article>';
  }

  function capNote(c) {
    var postings = c.jobs > c.roles ? ' (' + fmtN(c.jobs) + ' postings)' : '';
    return '<div class="jb-capnote">' + esc(c.name) + ' has ' + fmtN(c.roles) + ' open roles' + postings + ' · showing the ' + COMPANY_CAP + ' newest that match · ' +
      '<button type="button" class="jb-link" data-company="' + esc(c.name) + '">See all at ' + esc(c.name) + ' →</button></div>';
  }

  function emptyHtml() {
    if (state.job) return '<div class="jb-empty"><h3>This job is no longer listed</h3><p>The company may have filled it or taken the posting down.</p><button type="button" class="jb-btn" id="jb-empty-reset">See all jobs</button></div>';
    var tips = 'Try fewer filters or a broader search';
    if (origin && origin.kind !== 'hub' && state.within > 0) tips += ', a larger distance, or “Open to moving”';
    return '<div class="jb-empty"><h3>No jobs match</h3><p>' + tips + '. Postings with no activity for ' + STALE_DAYS + ' days are hidden unless you switch on “Include postings idle for 90+ days”.</p><button type="button" class="jb-btn" id="jb-empty-reset">Clear all filters</button></div>';
  }

  function renderList(list) {
    var capped = capByCompany(list);
    var out = capped.rows;
    var el = $('jb-list');
    if (!out.length) { el.innerHTML = emptyHtml(); $('jb-more').style.display = 'none'; return; }
    var html = [], seen = {};
    var limit = Math.min(shown, out.length);
    for (var i = 0; i < limit; i++) {
      var j = out[i];
      html.push(rowHtml(j, false));
      seen[j.c.i] = (seen[j.c.i] || 0) + 1;
      if (seen[j.c.i] === COMPANY_CAP && capped.capped[j.c.i]) html.push(capNote(j.c));
    }
    el.innerHTML = html.join('');
    var more = $('jb-more');
    if (out.length > limit) { more.style.display = ''; more.textContent = 'Show ' + Math.min(PAGE, out.length - limit) + ' more (' + fmtN(out.length - limit) + ' left)'; }
    else more.style.display = 'none';
  }

  function renderGroups(list) {
    var capped = capByCompany(list);
    var groups = [], byC = {};
    capped.rows.forEach(function (j) {
      var g = byC[j.c.i];
      if (!g) { g = byC[j.c.i] = { c: j.c, rows: [], newest: j.posted || '' }; groups.push(g); }
      g.rows.push(j);
    });
    if (sortMode() !== 'near') groups.sort(function (a, b) { return a.newest === b.newest ? a.c.name.localeCompare(b.c.name) : (a.newest < b.newest ? 1 : -1); });
    var el = $('jb-list');
    if (!groups.length) { renderList(list); return; }
    var html = [];
    var limit = Math.min(shownGroups, groups.length);
    for (var g = 0; g < limit; g++) {
      var grp = groups[g], c = grp.c, hidden = capped.capped[c.i] || 0, key = 'c' + c.i;
      html.push('<section class="jb-group">' +
        '<header class="jb-group-head">' +
          '<div class="jb-group-title">' + companyLink(c, 'jb-group-company') +
            '<span class="jb-sector">' + (SECTOR_ICON[c.sector] || '') + ' ' + esc(c.sector) + '</span>' +
            (c.il30 ? '<span class="jb-tag jb-tag-il30">🏆 IL30</span>' : '') +
            (c.fundingStage ? '<span class="jb-tag jb-tag-stage">' + esc(c.fundingStage) + '</span>' : '') +
            raisedTag(c, true) + surgeTag(c) + (HAS.card ? cardButton(key, c) : '') + '</div>' +
          '<div class="jb-group-count">' + (hidden ? 'showing ' + grp.rows.length + ' of ' + fmtN(grp.rows.length + hidden) + ' · <button type="button" class="jb-link" data-company="' + esc(c.name) + '">see all →</button>' : fmtN(grp.rows.length) + (grp.rows.length === 1 ? ' role' : ' roles')) + '</div>' +
        '</header>' +
        (HAS.card && openCards[key] ? '<div class="jb-group-card">' + cardHtml(c, key) + '</div>' : '') +
        grp.rows.map(function (j) { return rowHtml(j, true); }).join('') +
      '</section>');
    }
    el.innerHTML = html.join('');
    var more = $('jb-more');
    if (groups.length > limit) { more.style.display = ''; more.textContent = 'Show more companies (' + fmtN(groups.length - limit) + ' left)'; }
    else more.style.display = 'none';
  }

  function chipHtml(facet, value, label, count, active, icon) {
    return '<button type="button" class="jb-chip" data-facet="' + facet + '" data-value="' + esc(value) + '" aria-pressed="' + (active ? 'true' : 'false') + '"' + (count === 0 && !active ? ' disabled' : '') + '>' +
      (icon ? '<span class="jb-chip-ico">' + icon + '</span>' : '') + '<span class="jb-chip-label">' + esc(label) + '</span><span class="jb-chip-n">' + fmtN(count) + '</span></button>';
  }
  // Rebuild a row of buttons without losing the keyboard focus that was on one of them.
  function keepFocus(el, html) {
    var a = document.activeElement, v = a && el.contains(a) ? a.getAttribute('data-value') : null;
    el.innerHTML = html;
    if (v === null) return;
    for (var i = 0; i < el.children.length; i++) if (el.children[i].getAttribute('data-value') === v) { el.children[i].focus(); break; }
  }

  function renderChips(terms) {
    var fc = facetCounts('family', terms);
    var famOrder = FAMILIES.map(function (f) { return f[0]; }).filter(function (k) { return k !== 'other' && k !== 'general'; })
      .sort(function (a, b) { return (fc[b] || 0) - (fc[a] || 0); });
    ['general', 'other'].forEach(function (k) { if (fc[k]) famOrder.push(k); });
    keepFocus($('chips-family'), famOrder.map(function (k) { return chipHtml('family', k, famLabel[k], fc[k] || 0, state.family.indexOf(k) >= 0, FAMILY_ICON[k]); }).join(''));
    var mc = facetCounts('metro', terms);
    keepFocus($('chips-metro'), METROS.map(function (m) { return chipHtml('metro', m[0], m[1], mc[m[0]] || 0, state.metro.indexOf(m[0]) >= 0, ''); }).join(''));
    var sc = facetCounts('sector', terms);
    var secOrder = SECTORS.slice().sort(function (a, b) { return (sc[b] || 0) - (sc[a] || 0); });
    keepFocus($('chips-sector'), secOrder.map(function (k) { return chipHtml('sector', k, k, sc[k] || 0, state.sector.indexOf(k) >= 0, SECTOR_ICON[k] || ''); }).join(''));
    var lc = facetCounts('level', terms);
    keepFocus($('chips-level'), LEVELS.map(function (l) { return chipHtml('level', l[0], l[1], lc[l[0]] || 0, state.level.indexOf(l[0]) >= 0, ''); }).join(''));
    var stc = facetCounts('stage', terms);
    keepFocus($('chips-stage'), STAGES.map(function (s) { return chipHtml('stage', s[0], s[1], stc[s[0]] || 0, state.stage.indexOf(s[0]) >= 0, ''); }).join(''));
  }

  function renderShelves() {
    // counts under the board defaults (stale hidden, hard-tech on where the shelf says so); roles, not postings
    var el = $('jb-shelves');
    el.innerHTML = SHELVES.map(function (s) {
      var st = defaultState(); s.apply(st); st.shelf = s.key;
      var n = 0;
      for (var i = 0; i < rows.length; i++) if (matches(rows[i], st, [], null)) n++;
      var active = state.shelf === s.key;
      return '<button type="button" class="jb-shelf" data-shelf="' + s.key + '" aria-pressed="' + (active ? 'true' : 'false') + '"' + (n === 0 && !active ? ' data-empty="1"' : '') + ' title="' + esc(s.blurb) + '">' +
        '<span class="jb-shelf-ico">' + s.icon + '</span>' +
        '<span class="jb-shelf-body"><span class="jb-shelf-title">' + esc(s.title) + '</span><span class="jb-shelf-blurb">' + esc(s.blurb) + '</span></span>' +
        '<span class="jb-shelf-n">' + fmtN(n) + '</span></button>';
    }).join('');
  }

  // ─── The family panel: role types, near home, filters ─────────────────────
  var FILTER_TEXT = {
    nodegree: ['No degree required (likely)', 'The posting says a college degree is not needed, or asks for a high-school diploma or GED.'],
    entry: ['Entry level', 'Jobs for people starting out: new-graduate and junior jobs. Internships are under “Internships and first jobs”.'],
    salary: ['Pay shown', 'The posting gives the pay or a pay range.'],
    citizen: ['US citizenship or green card likely required', 'The posting mentions US citizenship, permanent residence (a green card) or US export rules. We read this from the posting text, so it says “likely”.'],
    clearance: ['Security clearance likely required', 'The posting asks for a government security clearance. We read this from the posting text, so it says “likely”.']
  };
  var FILTER_SHOWN = { nodegree: HAS.nodegree, entry: HAS.entry };

  function initFamily() {
    var tEl = $('jb-types');
    if (tEl && HAS.types) {
      tEl.innerHTML = ROLE_TYPES.map(function (r) {
        return '<button type="button" class="jb-type" data-type="' + esc(r[0]) + '" aria-pressed="false">' +
          '<span class="jb-type-top"><span class="jb-type-ico" aria-hidden="true">' + (TYPE_ICON[r[0]] || '') + '</span><span class="jb-type-label">' + esc(r[1]) + '</span></span>' +
          '<span class="jb-type-about">' + esc(r[2]) + '</span><span class="jb-type-n"></span></button>';
      }).join('');
    }
    var fEl = $('jb-ffilters');
    if (fEl) {
      fEl.innerHTML = TOGGLES.map(function (t) {
        var id = 'jb-f-' + t.key, txt = FILTER_TEXT[t.key];
        var hide = FILTER_SHOWN[t.key] === false ? ' hidden' : '';
        var count = '<span class="jb-ff-n" id="' + id + '-n"></span>';
        var about = '<p class="jb-ff-about" id="' + id + '-help">' + esc(txt[1]) + '</p>';
        if (!t.tri) return '<div class="jb-ff"' + hide + '><label class="jb-ff-label" for="' + id + '"><input type="checkbox" id="' + id + '" aria-describedby="' + id + '-help"><span>' + esc(txt[0]) + '</span>' + count + '</label>' + about + '</div>';
        return '<div class="jb-ff"' + hide + '><label class="jb-ff-label" for="' + id + '"><span>' + esc(txt[0]) + '</span>' + count + '</label>' +
          '<select id="' + id + '" aria-describedby="' + id + '-help"><option value="">Show all jobs</option><option value="only">Only these jobs</option><option value="hide">Hide these jobs</option></select>' + about + '</div>';
      }).join('');
    }
  }

  function renderFamily(terms) {
    var tw = $('jb-types-wrap');
    if (tw) {
      tw.hidden = !HAS.types;
      if (HAS.types) {
        var tc = typeCounts(terms), btns = $('jb-types').querySelectorAll('.jb-type');
        for (var i = 0; i < btns.length; i++) {
          var code = btns[i].getAttribute('data-type'), on = state.type.indexOf(code) >= 0, n = tc[code] || 0;
          btns[i].setAttribute('aria-pressed', String(on));
          btns[i].classList.toggle('is-empty', n === 0 && !on);
          var nEl = btns[i].querySelector('.jb-type-n');
          if (nEl) nEl.textContent = fmtN(n) + plural(n, ' job', ' jobs');
        }
      }
    }
    var fc = toggleCounts(terms);
    TOGGLES.forEach(function (t) {
      var input = $('jb-f-' + t.key), nEl = $('jb-f-' + t.key + '-n');
      if (!input) return;
      if (t.tri) input.value = state[t.key] || ''; else input.checked = !!state[t.key];
      if (nEl) nEl.textContent = fmtN(fc[t.key]) + plural(fc[t.key], ' job', ' jobs');
    });
    renderNear(terms);
  }

  function nearInputText() {
    if (!state.near) return '';
    if (state.near === 'me') return ME_LABEL;
    if (state.near.indexOf('hub:') === 0) { var l = metroLabel[state.near.slice(4)]; return l ? l + ' (whole area)' : ''; }
    if (origin && origin.kind === 'zip') return origin.value;
    return origin && origin.label ? origin.label : state.near;
  }
  function nearPillText() {
    if (!origin) return 'Near ' + state.near;
    if (origin.kind === 'hub') return 'In the ' + origin.label + ' area';
    var who = origin.kind === 'me' ? 'you' : origin.label;
    return state.within > 0 ? 'Within ' + state.within + ' miles of ' + who : 'Any distance from ' + who;
  }

  function renderNear(terms) {
    var on = $('jb-near-on'), off = $('jb-near-off');
    if (!on) return;
    if (!HAS.places) { on.hidden = true; if (off) off.hidden = false; return; }   // data written before places existed
    on.hidden = false; if (off) off.hidden = true;
    var input = $('jb-near');
    var zips = geo.idx ? geo.idx.hasZips : !!(D.geo && D.geo.zips > 0);
    var towns = geo.idx ? geo.idx.places.filter(Boolean).length : (D.geo && D.geo.towns) || 0;
    $('jb-near-label').textContent = zips ? 'City or ZIP code' : 'Town or city';
    input.setAttribute('placeholder', zips ? 'For example: Hawthorne, CA or 90250' : 'For example: Hawthorne, CA');
    $('jb-near-help').textContent = zips ? 'Type a town or a five-digit ZIP code, then choose how far you would travel.' :
      'ZIP codes are not loaded on this site yet. Start typing a town and pick it from the list' + (towns ? ' (' + fmtN(towns) + ' towns where these companies hire, plus the main hiring areas)' : '') + ', or use your location.';
    if (document.activeElement !== input) input.value = nearInputText();
    var radios = document.querySelectorAll('input[name="jb-within"]');
    for (var i = 0; i < radios.length; i++) radios[i].checked = (parseInt(radios[i].value, 10) || 0) === state.within;
    $('jb-plusremote').checked = state.plusremote;
    $('jb-near-me').hidden = !navigator.geolocation;
    $('jb-near-clear').hidden = !state.near;

    var parts = [];
    if (nearNote.text) parts.push('<span class="jb-near-err">' + esc(nearNote.text) + '</span>');
    else if (state.near && !origin) parts.push('Looking up “' + esc(state.near) + '”…');
    else if (origin && origin.kind === 'hub') parts.push('Showing every job in the ' + esc(origin.label) + ' area.' + (state.plusremote ? ' Remote jobs in the US are included.' : ''));
    else if (origin) {
      var where = origin.kind === 'me' ? 'your location' : origin.label;
      var order = sortMode() === 'near' ? ', nearest first.' : ', newest first.';
      parts.push((state.within > 0 ? 'Showing jobs within ' + state.within + ' miles of ' : 'Open to moving: jobs at any distance from ') + esc(where) + order);
      var side = nearSideCounts(terms);
      if (side.remote && !state.plusremote) parts.push(fmtN(side.remote) + ' remote ' + plural(side.remote, 'job is', 'jobs are') + ' not included. <button type="button" class="jb-link" data-near-act="plusremote">Include remote jobs</button>');
      if (side.hub && side.hubUnplaced) parts.push(fmtN(side.hubUnplaced) + ' ' + plural(side.hubUnplaced, 'job', 'jobs') + ' in the ' + esc(side.hub.label) + ' area name no town we can find on a map, so ' + plural(side.hubUnplaced, 'it is', 'they are') + ' not included. <button type="button" class="jb-link" data-near-act="hub:' + esc(side.hub.code) + '">Show every job in the ' + esc(side.hub.label) + ' area</button>');
      else if (side.unplaced) parts.push('Jobs whose posting names no town we can find on a map are not included (' + fmtN(side.unplaced) + ' across the US).');
      if (origin.kind === 'me') parts.push('Your location stays in this browser. It is not saved and never put in a link.');
    }
    $('jb-near-status').innerHTML = parts.join(' ');
  }

  var activeLabels = [];
  function renderActive(list) {
    var total = list.length, postings = 0;
    for (var i = 0; i < list.length; i++) postings += list[i].n;
    var pills = [];
    activeLabels = [];
    var pill = function (label, k, v) {
      activeLabels.push(label);
      pills.push('<button type="button" class="jb-active-pill" data-k="' + k + '" data-v="' + esc(v || '') + '" aria-label="Remove: ' + esc(label) + '">' + esc(label) + ' <span aria-hidden="true">×</span></button>');
    };
    if (state.shelf && shelfByKey[state.shelf]) pill(shelfByKey[state.shelf].icon + ' ' + shelfByKey[state.shelf].title, 'shelf');
    if (state.q) pill('“' + state.q + '”', 'q');
    state.type.forEach(function (v) { pill(typeLabel[v] || v, 'type', v); });
    if (state.near) pill(nearPillText(), 'near');
    if (state.near && state.plusremote) pill('Plus remote jobs in the US', 'plusremote');
    if (state.nodegree) pill('No degree required (likely)', 'nodegree');
    if (state.entry) pill('Entry level', 'entry');
    if (state.salary) pill('Pay shown', 'salary');
    if (state.citizen) pill((state.citizen === 'only' ? 'Only' : 'Hiding') + ': citizenship or green card likely required', 'citizen');
    if (state.clearance) pill((state.clearance === 'only' ? 'Only' : 'Hiding') + ': clearance likely required', 'clearance');
    state.family.forEach(function (v) { pill(famLabel[v] || v, 'family', v); });
    state.metro.forEach(function (v) { pill(metroLabel[v] || v, 'metro', v); });
    state.sector.forEach(function (v) { pill(v, 'sector', v); });
    state.level.forEach(function (v) { pill(lvlLabel[v] || v, 'level', v); });
    state.stage.forEach(function (v) { pill(stageLabel[v] || v, 'stage', v); });
    if (state.company) pill(state.company, 'company');
    if (state.remote) pill('Remote', 'remote');
    if (state.intern) pill('Internships', 'intern');
    if (state.il30) pill('IL30 only', 'il30');
    if (!state.hardtech) pill('Including software companies', 'hardtech');
    if (state.posted) pill('Posted ≤ ' + state.posted + ' days', 'posted');
    if (state.stale) pill('Including older postings', 'stale');
    var el = $('jb-active'), count = $('jb-count');
    if (state.job) {
      el.innerHTML = '';
      count.innerHTML = list.length ? '<strong>One job</strong> someone shared with you. <button type="button" class="jb-link" id="jb-job-exit">See all jobs</button>' : '';
      return;
    }
    el.innerHTML = pills.length ? pills.join('') + '<button type="button" class="jb-link jb-clear-all">Clear all</button>' : '';
    count.innerHTML = '<strong>' + fmtN(total) + '</strong> ' + (total === 1 ? 'job' : 'jobs') +
      (postings > total ? ' <span class="jb-count-note">(' + fmtN(postings) + ' postings)</span>' : '') +
      (sortMode() === 'near' ? ' · nearest first' : state.view === 'company' ? ' · grouped by company' : ' · newest first') +
      (!state.stale && D.totals && D.totals.stale ? ' <span class="jb-count-note">(' + fmtN(D.totals.stale) + ' older than ' + STALE_DAYS + ' days hidden)</span>' : '');
  }

  function syncRail() {
    $('rail-company').value = state.company;
    $('rail-remote').checked = state.remote;
    $('rail-intern').checked = state.intern;
    $('rail-il30').checked = state.il30;
    $('rail-hardtech').checked = state.hardtech;
    $('rail-stale').checked = state.stale;
    var seg = document.querySelectorAll('#rail-posted button');
    for (var i = 0; i < seg.length; i++) seg[i].setAttribute('aria-pressed', String(parseInt(seg[i].getAttribute('data-days'), 10) === state.posted));
    $('jb-view-list').setAttribute('aria-pressed', String(state.view === 'list'));
    $('jb-view-company').setAttribute('aria-pressed', String(state.view === 'company'));
    var si = $('jb-search'); if (si.value !== state.q) si.value = state.q;
    $('jb-search-clear').style.display = state.q ? '' : 'none';
  }

  function renderSort() {
    var el = $('jb-sort'); if (!el) return;
    el.hidden = !(origin && origin.kind !== 'hub') || !!state.job;
    var mode = sortMode(), b = el.querySelectorAll('button');
    for (var i = 0; i < b.length; i++) b[i].setAttribute('aria-pressed', String(b[i].getAttribute('data-sort') === mode));
  }

  // The plain sentence at the top, from the board's default view: how many jobs, and how few are software.
  function renderLead() {
    var el = $('jb-family-lead'); if (!el) return;
    var st = defaultState(), n = 0, sw = 0, cos = {}, swBit = 0;
    ROLE_TYPES.forEach(function (r) { if (r[0] === 'software') swBit = r[3]; });
    for (var i = 0; i < rows.length; i++) {
      var j = rows[i];
      if (!matches(j, st, [], null)) continue;
      n++; cos[j.c.i] = 1;
      if (j.mask & swBit) sw++;
    }
    var text = fmtN(n) + ' open jobs at ' + fmtN(Object.keys(cos).length) + ' companies that make physical things: rockets, reactors, robots, chips, medicines and more.';
    if (HAS.types && sw > 0 && n / sw >= 2) text += ' About 1 in ' + Math.round(n / sw) + ' is a software job. Most of the rest are engineering, business and hands-on jobs, from technician to welder.';
    el.textContent = text;
  }

  var lastList = [];
  function render(resetPaging) {
    if (resetPaging) { shown = PAGE; shownGroups = GROUP_PAGE; expanded = {}; openCards = {}; }
    if (state.near !== settledFor) settleOrigin();
    var terms = queryTerms(state.q);
    var list = run();
    lastList = list;
    renderChips(terms);
    renderShelves();
    renderFamily(terms);
    renderActive(list);
    syncRail();
    renderSort();
    if (state.view === 'company' && !state.job) renderGroups(list); else renderList(list);
    writeUrl();
  }
  function changed() { state.job = ''; render(true); }      // any new choice leaves a shared single job

  // ─── Near home: typing, picking, the browser's location ───────────────────
  var sugg = { items: [], active: -1 };
  function openSuggest() {
    var input = $('jb-near'), list = $('jb-near-list');
    if (!input || !list) return;
    if (!geo.idx) { loadGeo(function () { if (geo.idx && document.activeElement === input) openSuggest(); }); return; }
    var items = L.suggestPlaces(input.value, geo.idx, 8);
    sugg.items = items; sugg.active = -1;
    if (!items.length) { closeSuggest(); return; }
    list.innerHTML = items.map(function (it, k) { return '<li role="option" class="jb-near-opt" id="jb-near-opt-' + k + '" data-k="' + k + '" aria-selected="false">' + esc(it.label) + '</li>'; }).join('');
    list.hidden = false;
    input.setAttribute('aria-expanded', 'true');
    input.removeAttribute('aria-activedescendant');
  }
  function closeSuggest() {
    var input = $('jb-near'), list = $('jb-near-list');
    if (!input || !list) return;
    list.hidden = true; list.innerHTML = '';
    sugg.items = []; sugg.active = -1;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
  }
  function moveSuggest(step) {
    if (!sugg.items.length) { openSuggest(); return; }
    sugg.active = (sugg.active + step + sugg.items.length) % sugg.items.length;
    var opts = $('jb-near-list').children;
    for (var i = 0; i < opts.length; i++) opts[i].setAttribute('aria-selected', String(i === sugg.active));
    $('jb-near').setAttribute('aria-activedescendant', 'jb-near-opt-' + sugg.active);
  }
  function pickSuggest(k) { var it = sugg.items[k]; if (!it) return; $('jb-near').value = it.value; applyNear(it.value); }
  function applyNear(text) {
    text = String(text || '').trim();
    nearNote = { text: '', bad: false };
    if (text === ME_LABEL && myPoint) text = 'me';
    state.near = text;
    closeSuggest();
    changed();
  }
  function useMyLocation() {
    if (!navigator.geolocation) return;
    nearNote = { text: '', bad: false };
    $('jb-near-status').textContent = 'Asking your browser for your location…';
    navigator.geolocation.getCurrentPosition(function (pos) {
      myPoint = { lat: pos.coords.latitude, lng: pos.coords.longitude };   // memory only
      state.near = 'me'; settledFor = null;
      changed();
      loadGeo(function () { render(false); });          // the hub hint needs the places file
    }, function (err) {
      nearNote = { text: err && err.code === 1 ? 'Your browser did not share your location. You can type a town instead.' : 'Your location could not be found. You can type a town instead.', bad: true };
      renderNear(queryTerms(state.q));
    }, { enableHighAccuracy: false, timeout: 15000, maximumAge: 600000 });
  }

  // ─── Copy a link, print ───────────────────────────────────────────────────
  function copyText(text, done) {
    var fallback = function () {
      var ta = document.createElement('textarea'), ok = false;
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      done(ok);
    };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
    else fallback();
  }
  function announce(msg) {
    var el = $('jb-live'); if (!el) return;
    el.textContent = '';
    setTimeout(function () { el.textContent = msg; }, 50);
  }
  function copySearch() {
    var url = boardUrl(searchQuery()), out = $('jb-copy-status');
    copyText(url, function (ok) {
      if (!out) return;
      if (ok) {
        out.textContent = 'Link copied. Paste it into a message or an email.' + (state.near === 'me' ? ' Your location is not in the link: the person who opens it can type their own town.' : '');
        return;
      }
      out.innerHTML = 'Copy this link: <input class="jb-copy-fallback" type="text" readonly aria-label="Link to this search" value="' + esc(url) + '">';
      var f = out.querySelector('input'); if (f) { f.focus(); f.select(); }
    });
  }
  function copyJob(btn) {
    var url = boardUrl('job=' + encodeURIComponent(btn.getAttribute('data-job')));
    copyText(url, function (ok) {
      if (!ok) { window.prompt('Copy this link to the job:', url); return; }
      var txt = btn.querySelector('.jb-copy-txt');
      if (txt) { txt.textContent = 'Link copied'; setTimeout(function () { txt.textContent = 'Copy link'; }, 2500); }
      announce('Link to this job copied. Paste it into a message or an email.');
    });
  }
  // One printed page: the first PRINT_ROWS results, one line each, with the address that brings the list back.
  function fillPrintSheet() {
    var sheet = $('jb-print-sheet'); if (!sheet) return;
    var list = lastList, take = list.slice(0, PRINT_ROWS), n = list.length;
    var url = boardUrl(searchQuery());
    var when = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    var search = state.job ? 'One job someone shared.' : 'Search: ' + (activeLabels.length ? activeLabels.join(' · ') : 'all jobs') + '.' +
      (state.hardtech && !state.company ? ' Hard-tech companies only.' : '') + (sortMode() === 'near' ? ' Nearest first.' : ' Newest first.');
    sheet.innerHTML = '<h2>Jobs from the Innovators League jobs board</h2>' +
      '<p>' + esc(search) + '</p>' +
      '<p class="jb-ps-url">Page address: <strong>' + esc(url) + '</strong>' + (state.near === 'me' ? ' (your location is not part of it)' : '') + '</p>' +
      '<table><thead><tr><th>Job</th><th>Company</th><th>Where</th><th>Pay</th></tr></thead><tbody>' +
      take.map(function (j) { return '<tr><td>' + esc(j.title) + '</td><td>' + esc(j.c.name) + '</td><td>' + esc(whereText(j)) + '</td><td>' + esc(salaryText(j) || '—') + '</td></tr>'; }).join('') +
      '</tbody></table>' +
      '<p>' + (n > take.length ? 'The first ' + take.length + ' of ' + fmtN(n) + ' jobs. The page address shows them all.' : fmtN(n) + plural(n, ' job.', ' jobs.')) +
      ' Printed ' + esc(when) + '. To apply, open the page address and follow the link to the company’s own job posting. We never collect applications.</p>';
  }

  // ─── Hero stats ───────────────────────────────────────────────────────────
  function animateNumber(id, target) {
    var el = $(id); if (!el) return;
    var start = performance.now(), dur = 900;
    (function tick(t) {
      var p = Math.min((t - start) / dur, 1);
      el.textContent = Math.floor(target * (1 - Math.pow(1 - p, 3))).toLocaleString();
      if (p < 1) requestAnimationFrame(tick);
    })(start);
  }
  function heroStats() {
    var t = D.totals || {};
    animateNumber('total-jobs', t.jobs || jobs.length);          // raw postings, as before
    animateNumber('total-companies', t.companies || companies.length);
    animateNumber('remote-jobs', t.remote || 0);
    var roles = $('total-roles');
    if (roles) roles.textContent = fmtN(t.roles || rows.length) + ' distinct roles';
    var el = $('jobs-last-updated');
    if (el && t.lastUpdated) {
      var last = new Date(t.lastUpdated.replace(' UTC', 'Z').replace(' ', 'T'));
      if (!isNaN(last)) {
        var hours = (Date.now() - last.getTime()) / 3600000;
        var when = last.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) + ' · ' + last.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
        el.innerHTML = hours > 48 ? '<span style="color:#ff9a6e;">⚠ Data is ' + Math.floor(hours / 24) + ' days old</span> — last refresh ' + when : 'Last refreshed: ' + when;
      }
    }
  }

  // ─── Events ───────────────────────────────────────────────────────────────
  function toggleIn(arr, v) { var i = arr.indexOf(v); if (i >= 0) arr.splice(i, 1); else arr.push(v); }
  function scrollToResults() {
    var el = $('jb-results-head');
    if (el && window.innerWidth < 1024) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  function debounce(fn, ms) { var t; return function () { clearTimeout(t); var a = arguments, c = this; t = setTimeout(function () { fn.apply(c, a); }, ms); }; }
  function refocus(sel, attr, val) {
    var all = document.querySelectorAll(sel);
    for (var i = 0; i < all.length; i++) if (all[i].getAttribute(attr) === val) { all[i].focus(); break; }
  }

  function wire() {
    document.addEventListener('click', function (e) {
      var t = e.target;
      if (!t || !t.closest) return;
      var exp = t.closest('.jb-expand');
      if (exp) {
        var ri = parseInt(exp.getAttribute('data-row'), 10);
        var cl = $('jb-clones-' + ri);
        var open = !expanded[ri];
        expanded[ri] = open;
        if (cl) { if (open) cl.removeAttribute('hidden'); else cl.setAttribute('hidden', ''); }
        exp.setAttribute('aria-expanded', String(open));
        return;
      }
      var tb = t.closest('.jb-type');
      if (tb) { toggleIn(state.type, tb.getAttribute('data-type')); changed(); return; }
      var cb = t.closest('.jb-card-btn');
      if (cb) { var key = cb.getAttribute('data-card'); openCards[key] = !openCards[key]; render(false); refocus('.jb-card-btn', 'data-card', key); return; }
      var cp = t.closest('.jb-copy');
      if (cp) { copyJob(cp); return; }
      var na = t.closest('[data-near-act]');
      if (na) {
        var act = na.getAttribute('data-near-act');
        if (act === 'plusremote') state.plusremote = true; else { state.near = act; nearNote = { text: '', bad: false }; }
        changed(); return;
      }
      var so = t.closest('#jb-sort button');
      if (so) { state.sort = so.getAttribute('data-sort'); render(true); return; }
      var chip = t.closest('.jb-chip');
      if (chip) { toggleIn(state[chip.getAttribute('data-facet')], chip.getAttribute('data-value')); changed(); return; }
      var shelf = t.closest('.jb-shelf');
      if (shelf) {
        var skey = shelf.getAttribute('data-shelf');
        var next = defaultState();
        if (state.shelf !== skey && shelfByKey[skey]) { next.shelf = skey; shelfByKey[skey].apply(next); }
        state = next; render(true); scrollToResults(); return;
      }
      var pill = t.closest('.jb-active-pill');
      if (pill) {
        var k = pill.getAttribute('data-k'), v = pill.getAttribute('data-v');
        if (Array.isArray(state[k])) toggleIn(state[k], v);
        else if (k === 'hardtech') state.hardtech = true;
        else if (k === 'posted') state.posted = 0;
        else if (typeof state[k] === 'boolean') state[k] = false;
        else state[k] = '';
        if (k === 'near') nearNote = { text: '', bad: false };
        changed(); return;
      }
      if (t.closest('.jb-clear-all') || t.id === 'jb-empty-reset' || t.id === 'rail-reset') { state = defaultState(); nearNote = { text: '', bad: false }; render(true); return; }
      var link = t.closest('.jb-link[data-company]');
      if (link) { state.company = link.getAttribute('data-company'); changed(); scrollToResults(); return; }
      if (t.id === 'jb-more') {
        if (state.view === 'company') shownGroups += GROUP_PAGE; else shown += PAGE;
        render(false); return;
      }
      if (t.id === 'jb-view-list') { state.view = 'list'; changed(); return; }
      if (t.id === 'jb-view-company') { state.view = 'company'; changed(); return; }
      var seg = t.closest('#rail-posted button');
      if (seg) { var d = parseInt(seg.getAttribute('data-days'), 10) || 0; state.posted = state.posted === d ? 0 : d; changed(); return; }
      if (t.id === 'jb-search-clear') { state.q = ''; changed(); $('jb-search').focus(); return; }
      if (t.id === 'jb-near-go') { applyNear($('jb-near').value); return; }
      if (t.id === 'jb-near-me') { useMyLocation(); return; }
      if (t.id === 'jb-near-clear') { $('jb-near').value = ''; applyNear(''); $('jb-near').focus(); return; }
      if (t.id === 'jb-copy-search') { copySearch(); return; }
      if (t.id === 'jb-print') { fillPrintSheet(); window.print(); return; }
      if (t.id === 'jb-job-exit') { state.job = ''; render(true); return; }
    });

    document.addEventListener('change', function (e) {
      var t = e.target;
      if (!t) return;
      if (t.name === 'jb-within') { state.within = parseInt(t.value, 10) || 0; changed(); return; }
      if (t.id === 'jb-plusremote') { state.plusremote = t.checked; changed(); return; }
      if (t.id && t.id.indexOf('jb-f-') === 0 && FILTER_TEXT[t.id.slice(5)]) { state[t.id.slice(5)] = t.type === 'checkbox' ? t.checked : t.value; changed(); }
    });

    var onSearch = debounce(function () { state.q = $('jb-search').value; changed(); }, 220);
    $('jb-search').addEventListener('input', onSearch);
    $('jb-search').addEventListener('keydown', function (e) { if (e.key === 'Enter') { state.q = this.value; changed(); } });

    var toggles = { 'rail-remote': 'remote', 'rail-intern': 'intern', 'rail-il30': 'il30', 'rail-hardtech': 'hardtech', 'rail-stale': 'stale' };
    Object.keys(toggles).forEach(function (id) {
      $(id).addEventListener('change', function () { state[toggles[id]] = this.checked; changed(); });
    });

    var ni = $('jb-near');
    if (ni) {
      ni.addEventListener('focus', function () { loadGeo(function () { renderNear(queryTerms(state.q)); }); });
      ni.addEventListener('input', debounce(openSuggest, 120));
      ni.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown') { e.preventDefault(); moveSuggest(1); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); moveSuggest(-1); }
        else if (e.key === 'Enter') { e.preventDefault(); if (sugg.active >= 0) pickSuggest(sugg.active); else applyNear(ni.value); }
        else if (e.key === 'Escape') closeSuggest();
      });
      ni.addEventListener('blur', function () { setTimeout(closeSuggest, 150); });
      $('jb-near-list').addEventListener('mousedown', function (e) {
        var li = e.target.closest && e.target.closest('.jb-near-opt');
        if (li) { e.preventDefault(); pickSuggest(parseInt(li.getAttribute('data-k'), 10)); }
      });
    }
    window.addEventListener('beforeprint', fillPrintSheet);

    // company typeahead (datalist) — commit on exact match or on change
    var dl = $('rail-company-list');
    dl.innerHTML = companies.slice().sort(function (a, b) { return b.roles - a.roles; }).map(function (c) { return '<option value="' + esc(c.name) + '">' + fmtN(c.roles) + ' roles</option>'; }).join('');
    var companyNames = {};
    companies.forEach(function (c) { companyNames[c.name.toLowerCase()] = c.name; companyNames[c.canonical.toLowerCase()] = c.name; });
    var onCompany = function () {
      var v = this.value.trim();
      var hit = companyNames[v.toLowerCase()];
      if (!v) { if (state.company) { state.company = ''; changed(); } return; }
      if (hit && hit !== state.company) { state.company = hit; changed(); }
    };
    $('rail-company').addEventListener('change', onCompany);
    $('rail-company').addEventListener('input', debounce(onCompany, 300));
  }

  // The secondary rail collapses to a "More filters" disclosure on narrow screens
  var railProgrammatic = false;
  function railLayout() {
    var rail = $('jb-rail'); if (!rail) return;
    var narrow = window.innerWidth < 1024;
    railProgrammatic = true;
    if (!narrow) rail.setAttribute('open', '');
    else if (!rail.hasAttribute('data-user-toggled')) rail.removeAttribute('open');
    setTimeout(function () { railProgrammatic = false; }, 0);
  }

  // ─── Boot ─────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    heroStats();
    state = readUrl();
    if (!HAS.entry) state.entry = false;
    if (!HAS.nodegree) state.nodegree = false;
    initFamily();
    wire();
    railLayout();
    var rail = $('jb-rail');
    if (rail) rail.addEventListener('toggle', function () { if (!railProgrammatic && window.innerWidth < 1024) rail.setAttribute('data-user-toggled', '1'); });
    window.addEventListener('resize', debounce(railLayout, 150));
    renderLead();
    render(true);
  });

  // Mobile menu (shared nav)
  var mb = document.querySelector('.mobile-menu-btn');
  if (mb) mb.addEventListener('click', function () { var n = document.querySelector('.nav-links'); if (n) n.classList.toggle('open'); this.classList.toggle('open'); });
})();
