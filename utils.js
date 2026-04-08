// ─── SHARED UTILITIES ───
// Canonical implementations of functions used across multiple pages.
// Load this script before any page-specific JS.

// ─── SECURITY ───

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escapeAttr(str) {
  return (str || '')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function sanitizeUrl(url) {
  if (!url) return '#';
  const trimmed = String(url).trim();
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  if (/^mailto:/i.test(trimmed)) return trimmed;
  return '#';
}

// ─── FORMATTING ───

function formatCurrency(num) {
  if (typeof num === 'string') return num;
  if (!num || isNaN(num)) return '$0';
  if (num >= 1e12) return '$' + (num / 1e12).toFixed(1) + 'T';
  if (num >= 1e9) return '$' + (num / 1e9).toFixed(1) + 'B';
  if (num >= 1e6) return '$' + (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return '$' + (num / 1e3).toFixed(0) + 'K';
  return '$' + num.toLocaleString();
}

function formatValuation(num) {
  if (!num || num === 0) return '';
  var abs = Math.abs(num);
  if (abs >= 1e12) return '$' + (num / 1e12).toFixed(1) + 'T';
  if (abs >= 1e9) return '$' + (num / 1e9).toFixed(1) + 'B';
  if (abs >= 1e6) return '$' + (num / 1e6).toFixed(0) + 'M';
  if (abs >= 1e3) return '$' + (num / 1e3).toFixed(0) + 'K';
  return '$' + num.toFixed(0);
}

function formatDateRelative(dateStr) {
  if (!dateStr) return '';
  var date = new Date(dateStr);
  if (isNaN(date.getTime())) return dateStr;
  var now = new Date();
  var diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return diffDays + ' days ago';
  if (diffDays < 30) return Math.floor(diffDays / 7) + ' weeks ago';
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatDateAbsolute(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    var d = new Date(/^\d{4}-\d{2}-\d{2}$/.test(dateStr) ? dateStr + 'T00:00:00' : dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch (e) {
    return dateStr;
  }
}

function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max) + '...' : str;
}

// ─── ANIMATION ───

function animateCounter(idOrEl, target, opts) {
  var el = typeof idOrEl === 'string' ? document.getElementById(idOrEl) : idOrEl;
  if (!el) return;
  if (!target || target <= 0) { el.textContent = '0'; return; }

  var o = opts || {};
  var prefix = o.prefix || '';
  var suffix = o.suffix || '';
  var duration = o.duration || 1500;
  var useObserver = o.observe !== false;
  var format = o.format || function(n) { return n >= 1000 ? n.toLocaleString() : String(n); };

  function easeOutQuart(t) { return 1 - Math.pow(1 - t, 4); }

  function run() {
    var start = null;
    function tick(now) {
      if (!start) start = now;
      var t = Math.min((now - start) / duration, 1);
      var val = Math.round(target * easeOutQuart(t));
      el.textContent = prefix + format(val) + suffix;
      if (t < 1) requestAnimationFrame(tick);
      else el.textContent = prefix + format(target) + suffix;
    }
    requestAnimationFrame(tick);
  }

  if (useObserver && typeof IntersectionObserver !== 'undefined') {
    var observer = new IntersectionObserver(function(entries) {
      if (entries[0].isIntersecting) { run(); observer.disconnect(); }
    });
    observer.observe(el);
  } else {
    run();
  }
}

// ─── SLUG HELPERS ───

function companyToSlug(name) {
  if (!name) return '';
  return name.toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function slugToCompanyName(slug) {
  if (!slug || typeof COMPANIES === 'undefined') return null;
  var match = COMPANIES.find(function(c) { return companyToSlug(c.name) === slug; });
  return match ? match.name : null;
}

// ─── COMPANY NAME NORMALIZATION ───

var _companyAliases = null;
function _buildAliasMap() {
  if (_companyAliases) return _companyAliases;
  _companyAliases = {};
  if (typeof COMPANIES !== 'undefined') {
    COMPANIES.forEach(function(c) {
      var key = c.name.toLowerCase().trim();
      _companyAliases[key] = c.name;
      // Common short forms
      var short = key.replace(/\s*(inc\.?|industries|corp\.?|corporation|llc|ltd\.?|co\.?)\s*$/i, '').trim();
      if (short !== key) _companyAliases[short] = c.name;
    });
  }
  return _companyAliases;
}

function normalizeCompanyName(name) {
  if (!name) return name;
  var aliases = _buildAliasMap();
  var key = name.toLowerCase().trim();
  if (aliases[key]) return aliases[key];
  // Try without suffix
  var short = key.replace(/\s*(inc\.?|industries|corp\.?|corporation|llc|ltd\.?|co\.?)\s*$/i, '').trim();
  if (aliases[short]) return aliases[short];
  return name;
}

function findCompanyData(name, dataset) {
  if (!name || !dataset || !Array.isArray(dataset)) return [];
  var canonical = normalizeCompanyName(name);
  var nameLower = name.toLowerCase();
  var canonicalLower = canonical.toLowerCase();
  return dataset.filter(function(item) {
    var itemName = (item.company || item.name || '').toLowerCase();
    return itemName === canonicalLower ||
           itemName === nameLower ||
           canonicalLower.includes(itemName) ||
           itemName.includes(canonicalLower);
  });
}

// ─── SAFE INIT ───

function safeInit(nameOrFn, fnOrUndef) {
  var name, fn;
  if (typeof nameOrFn === 'function') {
    fn = nameOrFn; name = fnOrUndef || fn.name || 'unknown';
  } else {
    name = nameOrFn; fn = fnOrUndef;
  }
  try { fn(); } catch (e) { console.error('[TIL] ' + name + ' failed:', e); }
}

// ─── LOCAL STORAGE ───

function safeLocalStorageGet(key, fallback) {
  try {
    var val = localStorage.getItem(key);
    return val !== null ? JSON.parse(val) : fallback;
  } catch (e) {
    return fallback;
  }
}

function safeLocalStorageSet(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (e) {
    console.warn('[TIL] localStorage write failed for "' + key + '":', e.message);
    return false;
  }
}

// ─── DEBOUNCE ───

function debounce(func, wait) {
  var timeout;
  return function() {
    var args = arguments;
    var context = this;
    clearTimeout(timeout);
    timeout = setTimeout(function() { func.apply(context, args); }, wait);
  };
}

// ─── MOBILE MENU ───

function initMobileMenu() {
  var btn = document.querySelector('.mobile-menu-btn');
  var links = document.querySelector('.nav-links');
  if (btn && links) {
    btn.addEventListener('click', function() {
      links.classList.toggle('open');
      btn.classList.toggle('open');
    });
    links.querySelectorAll('a').forEach(function(a) {
      a.addEventListener('click', function() {
        links.classList.remove('open');
        btn.classList.remove('open');
      });
    });
  }
}

// ─── EXPORT ───

function exportToCSV(data, filename) {
  if (!data || !data.length) return;
  var headers = Object.keys(data[0]);
  var csvRows = [headers.join(',')];
  data.forEach(function(row) {
    var values = headers.map(function(h) {
      var val = row[h] == null ? '' : String(row[h]);
      return '"' + val.replace(/"/g, '""') + '"';
    });
    csvRows.push(values.join(','));
  });
  var blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = filename || 'export.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
