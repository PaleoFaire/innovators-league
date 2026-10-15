/**
 * Jobs Board v2 — The ROS Innovators League
 *
 * Reads window.JOBS_V2 (data/jobs_enriched.js, built by scripts/enrich_jobs.py)
 * and renders: six curated shelves, a synonym-aware search box, four primary
 * chip rows (what I do / where / which kind of company / level) with live
 * counts, a secondary filter rail, and a newest-first list with a per-company
 * cap and a group-by-company view.
 *
 * Also exposes JOBS_DATA / JOBS_STATS (expanded from the compact rows) so the
 * untouched Talent Intelligence tab (talent.js) keeps working.
 */
(function () {
  'use strict';

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
  var F = { REMOTE: 1, STALE: 2, CLEARANCE: 4, USPERSON: 8, TRADES: 16, SUMMER27: 32, GENERAL: 64 };
  var CF = { IL30: 1, HARDTECH: 2, INDB: 4 };
  var STALE_DAYS = D.staleAfterDays || 90;
  var PAGE = 50;
  var GROUP_PAGE = 12;
  var COMPANY_CAP = 20;
  var MS_DAY = 86400000;

  var FAMILIES = D.families, LEVELS = D.levels, METROS = D.metros, STAGES = D.stages, SECTORS = D.sectors;
  var famLabel = {}, lvlLabel = {}, metroLabel = {}, stageLabel = {};
  FAMILIES.forEach(function (f) { famLabel[f[0]] = f[1]; });
  LEVELS.forEach(function (l) { lvlLabel[l[0]] = l[1]; });
  METROS.forEach(function (m) { metroLabel[m[0]] = m[1]; });
  STAGES.forEach(function (s) { stageLabel[s[0]] = s[1]; });

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
    'london': ['london', 'uk'], 'uk': ['uk', 'london', 'united kingdom', 'england'], 'germany': ['germany', 'munich', 'berlin'], 'europe': ['europe', 'germany', 'uk', 'france', 'international'],
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
      il30: !!(r[3] & CF.IL30), hardTech: !!(r[3] & CF.HARDTECH), inDb: !!(r[3] & CF.INDB),
      raisedAmount: r[4] || '', raisedRound: r[5] || '', raisedMonth: r[6] || '', fundingStage: r[7] || '', jobs: r[8] || 0,
      canonical: r[9] || r[0]
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

  function daysSince(posted, fallback) {
    if (!posted) return fallback >= 0 ? fallback : -1;
    var p = posted.split('-');
    var t = Date.UTC(+p[0], +p[1] - 1, +p[2]);
    return Math.max(0, Math.round((todayUTC - t) / MS_DAY));
  }

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
      days: days, updDays: updDays, stale: !!(flags & F.STALE) || updDays > STALE_DAYS,
      remote: !!(flags & F.REMOTE), clearance: !!(flags & F.CLEARANCE), usPerson: !!(flags & F.USPERSON),
      trades: !!(flags & F.TRADES), summer27: !!(flags & F.SUMMER27), general: !!(flags & F.GENERAL),
      hay: (r[2] + ' ' + c.name + ' ' + r[3] + ' ' + (famLabel[fam] || '') + ' ' + (lvlLabel[lvl] || '') + ' ' + c.sector + ' ' + metros.map(function (m) { return metroLabel[m] || ''; }).join(' ')).toLowerCase()
    };
  });

  // Talent tab compatibility (talent.js reads JOBS_DATA / JOBS_STATS)
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
  var state = defaultState();
  var shown = PAGE;
  var shownGroups = GROUP_PAGE;

  function defaultState() {
    return { q: '', family: [], metro: [], sector: [], level: [], stage: [], company: '', remote: false, salary: false, clearance: false, intern: false, il30: false, hardtech: true, posted: 0, stale: false, view: 'list', shelf: '' };
  }

  var SHELVES = [
    { key: 'trades', icon: '🔧', title: 'Hard-tech trades', blurb: 'Technicians, welders, machinists, electricians', test: function (j) { return j.trades && j.c.hardTech; }, apply: function (s) { s.hardtech = true; } },
    { key: 'interns', icon: '🎓', title: 'Summer 2027 internships', blurb: 'Posted for next summer, newest first', test: function (j) { return j.summer27; }, apply: function (s) { s.intern = true; } },
    { key: 'raised', icon: '💵', title: 'Raised this quarter', blurb: 'Companies that closed a round in the last ' + (D.raisedWindowDays || 90) + ' days', test: function (j) { return !!j.c.raisedMonth; }, apply: function (s) {} },
    { key: 'il30', icon: '🏆', title: 'IL30 hiring now', blurb: 'Open roles at the Innovators League 30', test: function (j) { return j.c.il30; }, apply: function (s) { s.il30 = true; } },
    { key: 'remote', icon: '🌐', title: 'Remote hard-tech', blurb: 'Remote-friendly roles at hardware companies', test: function (j) { return j.remote && j.c.hardTech; }, apply: function (s) { s.remote = true; s.hardtech = true; } },
    { key: 'cleared', icon: '🛡️', title: 'Cleared roles', blurb: 'Postings that call for a security clearance', test: function (j) { return j.clearance; }, apply: function (s) { s.clearance = true; } }
  ];
  var shelfByKey = {};
  SHELVES.forEach(function (s) { shelfByKey[s.key] = s; });

  // ─── URL sync ─────────────────────────────────────────────────────────────
  function readUrl() {
    var p = new URLSearchParams(location.search);
    var s = defaultState();
    var list = function (k) { var v = p.get(k); return v ? v.split(',').filter(Boolean) : []; };
    s.q = p.get('q') || '';
    s.family = list('family'); s.metro = list('metro'); s.sector = list('sector'); s.level = list('level'); s.stage = list('stage');
    s.company = p.get('company') || '';
    s.remote = p.get('remote') === '1'; s.salary = p.get('salary') === '1'; s.clearance = p.get('clearance') === '1';
    s.intern = p.get('intern') === '1'; s.il30 = p.get('il30') === '1'; s.hardtech = p.get('hardtech') !== '0';
    s.posted = parseInt(p.get('posted') || '0', 10) || 0; s.stale = p.get('stale') === '1';
    s.view = p.get('view') === 'company' ? 'company' : 'list';
    s.shelf = p.get('shelf') || '';
    if (s.shelf && shelfByKey[s.shelf]) shelfByKey[s.shelf].apply(s);
    return s;
  }
  function writeUrl() {
    var p = new URLSearchParams();
    if (state.q) p.set('q', state.q);
    ['family', 'metro', 'sector', 'level', 'stage'].forEach(function (k) { if (state[k].length) p.set(k, state[k].join(',')); });
    if (state.company) p.set('company', state.company);
    if (state.remote) p.set('remote', '1'); if (state.salary) p.set('salary', '1'); if (state.clearance) p.set('clearance', '1');
    if (state.intern) p.set('intern', '1'); if (state.il30) p.set('il30', '1'); if (!state.hardtech) p.set('hardtech', '0');
    if (state.posted) p.set('posted', String(state.posted)); if (state.stale) p.set('stale', '1');
    if (state.view === 'company') p.set('view', 'company');
    if (state.shelf) p.set('shelf', state.shelf);
    var qs = p.toString();
    var url = location.pathname + (qs ? '?' + qs : '') + location.hash;
    try { history.replaceState(null, '', url); } catch (e) { /* ignore */ }
  }

  // ─── Filtering ────────────────────────────────────────────────────────────
  function queryTerms(q) {
    q = (q || '').trim().toLowerCase();
    if (!q) return [];
    if (SYN[q]) return [SYN[q]];
    return q.split(/\s+/).map(function (w) { return SYN[w] || [w]; });
  }

  // skip: facet key whose own selection is ignored (for counts)
  function matches(j, s, terms, skip) {
    if (skip !== 'family' && s.family.length && s.family.indexOf(j.fam) < 0) return false;
    if (skip !== 'metro' && s.metro.length && !j.metros.some(function (m) { return s.metro.indexOf(m) >= 0; })) return false;
    if (skip !== 'sector' && s.sector.length && s.sector.indexOf(j.c.sector) < 0) return false;
    if (skip !== 'level' && s.level.length && s.level.indexOf(j.lvl) < 0) return false;
    if (skip !== 'stage' && s.stage.length && s.stage.indexOf(j.c.stage) < 0) return false;
    if (s.company && j.c.name !== s.company) return false;
    if (s.hardtech && !j.c.hardTech) return false;
    if (s.remote && !j.remote) return false;
    if (s.salary && !(j.salMin || j.salMax)) return false;
    if (s.clearance && !j.clearance) return false;
    if (s.intern && j.lvl !== 'intern') return false;
    if (s.il30 && !j.c.il30) return false;
    if (s.posted && (j.days < 0 || j.days > s.posted)) return false;
    if (!s.stale && j.stale) return false;
    if (s.shelf && shelfByKey[s.shelf] && !shelfByKey[s.shelf].test(j)) return false;
    if (terms.length) {
      for (var t = 0; t < terms.length; t++) {
        var alts = terms[t], ok = false;
        for (var a = 0; a < alts.length; a++) { if (j.hay.indexOf(alts[a]) >= 0) { ok = true; break; } }
        if (!ok) return false;
      }
    }
    return true;
  }

  function run() {
    var terms = queryTerms(state.q);
    var out = [];
    for (var i = 0; i < jobs.length; i++) if (matches(jobs[i], state, terms, null)) out.push(jobs[i]);
    // newest first; undated last; then company A–Z, title
    out.sort(function (a, b) {
      if (a.posted !== b.posted) { if (!a.posted) return 1; if (!b.posted) return -1; return a.posted < b.posted ? 1 : -1; }
      var ca = a.c.name.toLowerCase(), cb = b.c.name.toLowerCase();
      if (ca !== cb) return ca < cb ? -1 : 1;
      return a.title.toLowerCase() < b.title.toLowerCase() ? -1 : 1;
    });
    return out;
  }

  function facetCounts(key, terms) {
    var counts = {};
    for (var i = 0; i < jobs.length; i++) {
      var j = jobs[i];
      if (!matches(j, state, terms, key)) continue;
      if (key === 'metro') { for (var m = 0; m < j.metros.length; m++) counts[j.metros[m]] = (counts[j.metros[m]] || 0) + 1; }
      else if (key === 'family') counts[j.fam] = (counts[j.fam] || 0) + 1;
      else if (key === 'sector') counts[j.c.sector] = (counts[j.c.sector] || 0) + 1;
      else if (key === 'level') counts[j.lvl] = (counts[j.lvl] || 0) + 1;
      else if (key === 'stage') counts[j.c.stage] = (counts[j.c.stage] || 0) + 1;
    }
    return counts;
  }

  // Cap: no company shows more than COMPANY_CAP rows unless the reader asked for that company
  function capByCompany(list) {
    if (state.company || state.q) return { rows: list, capped: {} };
    var seen = {}, rows = [], capped = {};
    for (var i = 0; i < list.length; i++) {
      var j = list[i], n = seen[j.c.i] || 0;
      if (n < COMPANY_CAP) { rows.push(j); seen[j.c.i] = n + 1; }
      else { capped[j.c.i] = (capped[j.c.i] || 0) + 1; }
    }
    return { rows: rows, capped: capped };
  }

  // ─── Formatting ───────────────────────────────────────────────────────────
  function money(v) {
    if (v >= 1000000) return '$' + (v / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
    if (v >= 1000) return '$' + Math.round(v / 1000) + 'K';
    return '$' + v;
  }
  function salary(j) {
    if (!j.salMin && !j.salMax) return '';
    var cur = j.cur && j.cur !== 'USD' ? ' ' + j.cur : '';
    if (j.salMin && j.salMax) return money(j.salMin) + '–' + money(j.salMax) + cur;
    if (j.salMin) return money(j.salMin) + '+' + cur;
    return 'Up to ' + money(j.salMax) + cur;
  }
  function age(j) {
    if (j.days < 0) return '';
    if (j.days === 0) return 'Today';
    if (j.days === 1) return '1d';
    if (j.days < 14) return j.days + 'd';
    if (j.days < 60) return Math.round(j.days / 7) + 'w';
    return Math.round(j.days / 30) + 'mo';
  }
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function raisedTag(c, long) {
    if (!c.raisedMonth) return '';
    var m = c.raisedMonth.split('-');
    var month = MONTHS[(+m[1] || 1) - 1] || '';
    var amt = c.raisedAmount ? 'raised ' + esc(c.raisedAmount) : 'raised';
    return '<span class="jb-tag jb-tag-raised" title="' + esc(c.raisedRound || 'Funding round') + ' ' + esc(c.raisedMonth) + '">💵 ' + amt + ' in ' + month + (long && c.raisedRound ? ' · ' + esc(c.raisedRound) : '') + '</span>';
  }
  function companyLink(c, cls) {
    if (!c.inDb) return '<span class="' + cls + '">' + esc(c.name) + '</span>';
    return '<a class="' + cls + '" href="company.html?name=' + encodeURIComponent(c.canonical) + '">' + esc(c.name) + '</a>';
  }
  function levelText(j) { return j.lvl === 'mid' ? '' : (lvlLabel[j.lvl] || ''); }

  // ─── Rendering ────────────────────────────────────────────────────────────
  function rowHtml(j, compact) {
    var c = j.c;
    var meta2 = [];
    if (j.location) meta2.push('<span class="jb-loc">📍 ' + esc(j.location) + '</span>');
    var lt = levelText(j); if (lt) meta2.push('<span class="jb-lvl">' + esc(lt) + '</span>');
    var sal = salary(j); if (sal) meta2.push('<span class="jb-sal">💰 ' + esc(sal) + '</span>');
    if (j.remote) meta2.push('<span class="jb-pill jb-pill-remote">Remote</span>');
    if (j.clearance) meta2.push('<span class="jb-pill jb-pill-clear">Clearance</span>');
    if (j.stale) meta2.push('<span class="jb-pill jb-pill-stale" title="No activity on the ATS for more than ' + STALE_DAYS + ' days">Older</span>');
    var head = compact ? '' :
      '<div class="jb-meta">' + companyLink(c, 'jb-company') +
      '<span class="jb-sector">' + (SECTOR_ICON[c.sector] || '') + ' ' + esc(c.sector) + '</span>' +
      (c.il30 ? '<span class="jb-tag jb-tag-il30" title="Innovators League 30">🏆 IL30</span>' : '') +
      raisedTag(c) + '</div>';
    return '<article class="jb-row' + (compact ? ' jb-row-compact' : '') + '">' +
      '<div class="jb-row-main">' +
        '<a class="jb-title" href="' + esc(j.url) + '" target="_blank" rel="noopener">' + esc(j.title) + '</a>' +
        head +
        '<div class="jb-meta2">' + meta2.join('') + '</div>' +
      '</div>' +
      '<div class="jb-row-side">' +
        '<span class="jb-age" title="' + esc(j.posted || 'Date not provided by the ATS') + '">' + esc(age(j)) + '</span>' +
        '<a class="jb-apply" href="' + esc(j.url) + '" target="_blank" rel="noopener">Apply ↗</a>' +
      '</div>' +
    '</article>';
  }

  function capNote(c, hidden) {
    return '<div class="jb-capnote">' + esc(c.name) + ' has ' + fmtN(c.jobs) + ' open roles · showing the ' + COMPANY_CAP + ' newest that match · ' +
      '<button type="button" class="jb-link" data-company="' + esc(c.name) + '">See all at ' + esc(c.name) + ' →</button></div>';
  }

  function renderList(list) {
    var capped = capByCompany(list);
    var rows = capped.rows;
    var el = $('jb-list');
    if (!rows.length) {
      el.innerHTML = '<div class="jb-empty"><h3>No roles match</h3><p>Try fewer filters, a broader search, or switch on <em>Include older postings</em>.</p><button type="button" class="jb-btn" id="jb-empty-reset">Clear all filters</button></div>';
      $('jb-more').style.display = 'none';
      return;
    }
    var html = [], seen = {};
    var limit = Math.min(shown, rows.length);
    for (var i = 0; i < limit; i++) {
      var j = rows[i];
      html.push(rowHtml(j, false));
      seen[j.c.i] = (seen[j.c.i] || 0) + 1;
      if (seen[j.c.i] === COMPANY_CAP && capped.capped[j.c.i]) html.push(capNote(j.c, capped.capped[j.c.i]));
    }
    el.innerHTML = html.join('');
    var more = $('jb-more');
    if (rows.length > limit) { more.style.display = ''; more.textContent = 'Show ' + Math.min(PAGE, rows.length - limit) + ' more (' + fmtN(rows.length - limit) + ' left)'; }
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
    groups.sort(function (a, b) { return a.newest === b.newest ? a.c.name.localeCompare(b.c.name) : (a.newest < b.newest ? 1 : -1); });
    var el = $('jb-list');
    if (!groups.length) { renderList(list); return; }
    var html = [];
    var limit = Math.min(shownGroups, groups.length);
    for (var g = 0; g < limit; g++) {
      var grp = groups[g], c = grp.c, hidden = capped.capped[c.i] || 0;
      html.push('<section class="jb-group">' +
        '<header class="jb-group-head">' +
          '<div class="jb-group-title">' + companyLink(c, 'jb-group-company') +
            '<span class="jb-sector">' + (SECTOR_ICON[c.sector] || '') + ' ' + esc(c.sector) + '</span>' +
            (c.il30 ? '<span class="jb-tag jb-tag-il30">🏆 IL30</span>' : '') +
            (c.fundingStage ? '<span class="jb-tag jb-tag-stage">' + esc(c.fundingStage) + '</span>' : '') +
            raisedTag(c, true) + '</div>' +
          '<div class="jb-group-count">' + (hidden ? 'showing ' + grp.rows.length + ' of ' + fmtN(grp.rows.length + hidden) + ' · <button type="button" class="jb-link" data-company="' + esc(c.name) + '">see all →</button>' : fmtN(grp.rows.length) + (grp.rows.length === 1 ? ' role' : ' roles')) + '</div>' +
        '</header>' +
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

  function renderChips(terms) {
    var fc = facetCounts('family', terms);
    var famOrder = FAMILIES.map(function (f) { return f[0]; }).filter(function (k) { return k !== 'other' && k !== 'general'; })
      .sort(function (a, b) { return (fc[b] || 0) - (fc[a] || 0); });
    ['general', 'other'].forEach(function (k) { if (fc[k]) famOrder.push(k); });
    $('chips-family').innerHTML = famOrder.map(function (k) { return chipHtml('family', k, famLabel[k], fc[k] || 0, state.family.indexOf(k) >= 0, FAMILY_ICON[k]); }).join('');

    var mc = facetCounts('metro', terms);
    $('chips-metro').innerHTML = METROS.map(function (m) { return chipHtml('metro', m[0], m[1], mc[m[0]] || 0, state.metro.indexOf(m[0]) >= 0, ''); }).join('');

    var sc = facetCounts('sector', terms);
    var secOrder = SECTORS.slice().sort(function (a, b) { return (sc[b] || 0) - (sc[a] || 0); });
    $('chips-sector').innerHTML = secOrder.map(function (k) { return chipHtml('sector', k, k, sc[k] || 0, state.sector.indexOf(k) >= 0, SECTOR_ICON[k] || ''); }).join('');

    var lc = facetCounts('level', terms);
    $('chips-level').innerHTML = LEVELS.map(function (l) { return chipHtml('level', l[0], l[1], lc[l[0]] || 0, state.level.indexOf(l[0]) >= 0, ''); }).join('');

    var stc = facetCounts('stage', terms);
    $('chips-stage').innerHTML = STAGES.map(function (s) { return chipHtml('stage', s[0], s[1], stc[s[0]] || 0, state.stage.indexOf(s[0]) >= 0, ''); }).join('');
  }

  function renderShelves() {
    // counts under the board defaults (stale hidden, hard-tech on where the shelf says so)
    var base = defaultState();
    var el = $('jb-shelves');
    el.innerHTML = SHELVES.map(function (s) {
      var st = defaultState(); s.apply(st); st.shelf = s.key;
      var n = 0;
      for (var i = 0; i < jobs.length; i++) if (matches(jobs[i], st, [], null)) n++;
      var active = state.shelf === s.key;
      return '<button type="button" class="jb-shelf" data-shelf="' + s.key + '" aria-pressed="' + (active ? 'true' : 'false') + '">' +
        '<span class="jb-shelf-ico">' + s.icon + '</span>' +
        '<span class="jb-shelf-body"><span class="jb-shelf-title">' + esc(s.title) + '</span><span class="jb-shelf-blurb">' + esc(s.blurb) + '</span></span>' +
        '<span class="jb-shelf-n">' + fmtN(n) + '</span></button>';
    }).join('');
    void base;
  }

  function renderActive(total) {
    var pills = [];
    var pill = function (label, k, v) { pills.push('<button type="button" class="jb-active-pill" data-k="' + k + '" data-v="' + esc(v || '') + '">' + esc(label) + ' <span>×</span></button>'); };
    if (state.shelf && shelfByKey[state.shelf]) pill(shelfByKey[state.shelf].icon + ' ' + shelfByKey[state.shelf].title, 'shelf');
    if (state.q) pill('“' + state.q + '”', 'q');
    state.family.forEach(function (v) { pill(famLabel[v] || v, 'family', v); });
    state.metro.forEach(function (v) { pill(metroLabel[v] || v, 'metro', v); });
    state.sector.forEach(function (v) { pill(v, 'sector', v); });
    state.level.forEach(function (v) { pill(lvlLabel[v] || v, 'level', v); });
    state.stage.forEach(function (v) { pill(stageLabel[v] || v, 'stage', v); });
    if (state.company) pill(state.company, 'company');
    if (state.remote) pill('Remote', 'remote');
    if (state.salary) pill('Salary shown', 'salary');
    if (state.clearance) pill('Clearance', 'clearance');
    if (state.intern) pill('Internships', 'intern');
    if (state.il30) pill('IL30 only', 'il30');
    if (!state.hardtech) pill('Including software companies', 'hardtech');
    if (state.posted) pill('Posted ≤ ' + state.posted + ' days', 'posted');
    if (state.stale) pill('Including older postings', 'stale');
    var el = $('jb-active');
    el.innerHTML = pills.length ? pills.join('') + '<button type="button" class="jb-link jb-clear-all">Clear all</button>' : '';
    var count = $('jb-count');
    count.innerHTML = '<strong>' + fmtN(total) + '</strong> ' + (total === 1 ? 'role' : 'roles') + (state.view === 'company' ? ' · grouped by company' : ' · newest first') +
      (!state.stale && D.totals && D.totals.stale ? ' <span class="jb-count-note">(' + fmtN(D.totals.stale) + ' older than ' + STALE_DAYS + ' days hidden)</span>' : '');
  }

  function syncRail() {
    $('rail-company').value = state.company;
    $('rail-remote').checked = state.remote;
    $('rail-salary').checked = state.salary;
    $('rail-clearance').checked = state.clearance;
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

  function render(resetPaging) {
    if (resetPaging) { shown = PAGE; shownGroups = GROUP_PAGE; }
    var terms = queryTerms(state.q);
    var list = run();
    renderChips(terms);
    renderShelves();
    renderActive(list.length);
    syncRail();
    if (state.view === 'company') renderGroups(list); else renderList(list);
    writeUrl();
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
    animateNumber('total-jobs', t.jobs || jobs.length);
    animateNumber('total-companies', t.companies || companies.length);
    animateNumber('remote-jobs', t.remote || 0);
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

  function wire() {
    document.addEventListener('click', function (e) {
      var chip = e.target.closest('.jb-chip');
      if (chip) { toggleIn(state[chip.getAttribute('data-facet')], chip.getAttribute('data-value')); render(true); return; }
      var shelf = e.target.closest('.jb-shelf');
      if (shelf) {
        var key = shelf.getAttribute('data-shelf');
        var next = defaultState();
        if (state.shelf !== key && shelfByKey[key]) { next.shelf = key; shelfByKey[key].apply(next); }
        state = next; render(true); scrollToResults(); return;
      }
      var pill = e.target.closest('.jb-active-pill');
      if (pill) {
        var k = pill.getAttribute('data-k'), v = pill.getAttribute('data-v');
        if (Array.isArray(state[k])) toggleIn(state[k], v);
        else if (k === 'hardtech') state.hardtech = true;
        else if (k === 'posted') state.posted = 0;
        else if (typeof state[k] === 'boolean') state[k] = false;
        else state[k] = '';
        render(true); return;
      }
      if (e.target.closest('.jb-clear-all') || e.target.id === 'jb-empty-reset' || e.target.id === 'rail-reset') { state = defaultState(); render(true); return; }
      var link = e.target.closest('.jb-link[data-company]');
      if (link) { state.company = link.getAttribute('data-company'); render(true); scrollToResults(); return; }
      if (e.target.id === 'jb-more') {
        if (state.view === 'company') shownGroups += GROUP_PAGE; else shown += PAGE;
        render(false); return;
      }
      if (e.target.id === 'jb-view-list') { state.view = 'list'; render(true); return; }
      if (e.target.id === 'jb-view-company') { state.view = 'company'; render(true); return; }
      var seg = e.target.closest('#rail-posted button');
      if (seg) { var d = parseInt(seg.getAttribute('data-days'), 10) || 0; state.posted = state.posted === d ? 0 : d; render(true); return; }
      if (e.target.id === 'jb-search-clear') { state.q = ''; render(true); $('jb-search').focus(); return; }
    });

    var onSearch = debounce(function () { state.q = $('jb-search').value; render(true); }, 220);
    $('jb-search').addEventListener('input', onSearch);
    $('jb-search').addEventListener('keydown', function (e) { if (e.key === 'Enter') { state.q = this.value; render(true); } });

    var toggles = { 'rail-remote': 'remote', 'rail-salary': 'salary', 'rail-clearance': 'clearance', 'rail-intern': 'intern', 'rail-il30': 'il30', 'rail-hardtech': 'hardtech', 'rail-stale': 'stale' };
    Object.keys(toggles).forEach(function (id) {
      $(id).addEventListener('change', function () { state[toggles[id]] = this.checked; render(true); });
    });

    // company typeahead (datalist) — commit on exact match or on change
    var dl = $('rail-company-list');
    dl.innerHTML = companies.slice().sort(function (a, b) { return b.jobs - a.jobs; }).map(function (c) { return '<option value="' + esc(c.name) + '">' + fmtN(c.jobs) + ' roles</option>'; }).join('');
    var companyNames = {};
    companies.forEach(function (c) { companyNames[c.name.toLowerCase()] = c.name; });
    var onCompany = function () {
      var v = this.value.trim();
      var hit = companyNames[v.toLowerCase()];
      if (!v) { if (state.company) { state.company = ''; render(true); } return; }
      if (hit && hit !== state.company) { state.company = hit; render(true); }
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
    wire();
    railLayout();
    var rail = $('jb-rail');
    if (rail) rail.addEventListener('toggle', function () { if (!railProgrammatic && window.innerWidth < 1024) rail.setAttribute('data-user-toggled', '1'); });
    window.addEventListener('resize', debounce(railLayout, 150));
    render(true);
  });

  // Mobile menu (shared nav)
  var mb = document.querySelector('.mobile-menu-btn');
  if (mb) mb.addEventListener('click', function () { var n = document.querySelector('.nav-links'); if (n) n.classList.toggle('open'); this.classList.toggle('open'); });
})();
