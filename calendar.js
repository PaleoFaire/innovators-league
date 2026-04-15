// ─── FRONTIER TECH CALENDAR ──────────────────────────────────────────────────
// Curated list of frontier-tech industry events — conferences, ROS events,
// site visits, and summits — plus the rendering + filtering logic for
// calendar.html. Event data is hardcoded here for now; can be moved to
// data.js or a dedicated data file later.

var FRONTIER_EVENTS = [
  {
    title: "Space Symposium 2026",
    date: "2026-04-07",
    endDate: "2026-04-10",
    location: "Colorado Springs, CO",
    type: "conference",
    description: "World's premier gathering of global space leaders. Defense, commercial space, policy.",
    url: "https://www.spacesymposium.org",
    stephenRecommends: true,
    keyAttendees: ["SpaceX", "Lockheed Martin", "Boeing", "Varda"]
  },
  {
    title: "AUVSI XPONENTIAL 2026",
    date: "2026-04-20",
    endDate: "2026-04-23",
    location: "Los Angeles, CA",
    type: "conference",
    description: "The world's largest unmanned systems conference. Defense, robotics, autonomous systems.",
    url: "https://www.xponential.org",
    stephenRecommends: true,
    keyAttendees: ["Shield AI", "Anduril", "Skydio", "Saildrone"]
  },
  {
    title: "Hypersonic Weapon Systems Summit",
    date: "2026-05-12",
    endDate: "2026-05-14",
    location: "Washington, DC",
    type: "summit",
    description: "Government and industry gathering on hypersonic capabilities.",
    url: "#",
    stephenRecommends: true,
    keyAttendees: ["Hermeus", "Castelion", "Dynamo Air"]
  },
  {
    title: "American Nuclear Society Annual Meeting",
    date: "2026-06-14",
    endDate: "2026-06-17",
    location: "Anaheim, CA",
    type: "conference",
    description: "Premier gathering for nuclear energy industry — SMRs, microreactors, fusion.",
    url: "https://www.ans.org",
    stephenRecommends: false,
    keyAttendees: ["Aalo Atomics", "Valar Atomics", "Oklo"]
  },
  {
    title: "Defense Week 2026",
    date: "2026-05-06",
    endDate: "2026-05-10",
    location: "Washington, DC",
    type: "conference",
    description: "Annual Pentagon/industry gathering. NDIA and major primes.",
    url: "#",
    stephenRecommends: true,
    keyAttendees: ["All defense primes", "Top startups"]
  },
  {
    title: "RE+ 2026 (Solar & Storage Conference)",
    date: "2026-09-08",
    endDate: "2026-09-11",
    location: "Las Vegas, NV",
    type: "conference",
    description: "Largest clean energy event in North America.",
    url: "https://www.re-plus.com",
    stephenRecommends: false,
    keyAttendees: ["Base Power", "Form Energy"]
  },
  {
    title: "ROS x Inner Circle: Abu Dhabi Summit",
    date: "2026-11-15",
    endDate: "2026-11-17",
    location: "Abu Dhabi, UAE",
    type: "ros-event",
    description: "Flagship ROS gathering bringing top frontier tech founders to Abu Dhabi for meetings with sovereign wealth and family offices.",
    url: "https://rationaloptimistsociety.substack.com/",
    stephenRecommends: true,
    keyAttendees: ["Handpicked IL30 founders", "UAE investors"]
  },
  {
    title: "DefenseTalk Tech Summit",
    date: "2026-06-03",
    endDate: "2026-06-05",
    location: "San Diego, CA",
    type: "summit",
    description: "Emerging defense tech summit with startup pitch day.",
    url: "#",
    stephenRecommends: true,
    keyAttendees: ["Saronic", "Shield AI", "Skydio"]
  },
  {
    title: "AIAA SciTech Forum 2027",
    date: "2027-01-04",
    endDate: "2027-01-08",
    location: "Orlando, FL",
    type: "conference",
    description: "American Institute of Aeronautics & Astronautics — largest aerospace tech event.",
    url: "https://www.aiaa.org/scitech",
    stephenRecommends: false,
    keyAttendees: ["All major aerospace"]
  },
  {
    title: "SpaceCom 2027",
    date: "2027-01-26",
    endDate: "2027-01-28",
    location: "Orlando, FL",
    type: "conference",
    description: "Commercial space industry convention.",
    url: "https://www.spacecomexpo.com",
    stephenRecommends: false,
    keyAttendees: ["SpaceX", "Blue Origin", "Relativity"]
  }
];

// ─── LOCAL HELPERS ───────────────────────────────────────────────────────────
function calEscapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function calSanitizeUrl(url) {
  if (!url) return '#';
  var trimmed = String(url).trim();
  if (trimmed === '#' || trimmed === '') return '#';
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  if (/^mailto:/i.test(trimmed)) return trimmed;
  return '#';
}

function calInitMobileMenu() {
  var btn = document.querySelector('.mobile-menu-btn');
  var links = document.querySelector('.nav-links');
  if (btn && links) {
    btn.addEventListener('click', function() {
      links.classList.toggle('open');
      btn.classList.toggle('open');
    });
  }
}

function formatEventDateRange(start, end) {
  if (!start) return '';
  var s = new Date(start);
  if (isNaN(s.getTime())) return String(start);
  var options = { month: 'short', day: 'numeric' };
  var startStr = s.toLocaleDateString('en-US', options);
  if (!end || end === start) {
    return startStr + ', ' + s.getFullYear();
  }
  var e = new Date(end);
  if (isNaN(e.getTime())) return startStr;
  // If same month and year, show "Apr 7 – 10, 2026"
  if (s.getMonth() === e.getMonth() && s.getFullYear() === e.getFullYear()) {
    return s.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' – ' + e.getDate() + ', ' + e.getFullYear();
  }
  return startStr + ' – ' + e.toLocaleDateString('en-US', options) + ', ' + e.getFullYear();
}

function formatDaysUntil(dateStr) {
  if (!dateStr) return '';
  var date = new Date(dateStr);
  if (isNaN(date.getTime())) return '';
  var now = new Date();
  now.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  var diffDays = Math.round((date - now) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return 'Passed';
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Tomorrow';
  if (diffDays < 7) return 'In ' + diffDays + ' days';
  if (diffDays < 30) return 'In ' + Math.round(diffDays / 7) + ' weeks';
  if (diffDays < 365) return 'In ' + Math.round(diffDays / 30) + ' months';
  return 'In ' + Math.round(diffDays / 365) + ' years';
}

// ─── RENDERING ───────────────────────────────────────────────────────────────
var CAL_STATE = {
  events: [],
  filters: { type: 'all', month: 'all', recommended: false }
};

var TYPE_ICONS = {
  'conference': '&#127908;',      // 🎤
  'ros-event': '&#128992;',       // 🔶
  'site-visit': '&#127981;',      // 🏭
  'summit': '&#127963;'            // 🏛️
};

var TYPE_LABELS = {
  'conference': 'Conference',
  'ros-event': 'ROS Event',
  'site-visit': 'Site Visit',
  'summit': 'Summit'
};

var CAL_INITIAL_COUNT = 15;
var CAL_STEP_SIZE = 15;
var calShownCount = CAL_INITIAL_COUNT;

function calendarEventHTML(event) {
  var icon = TYPE_ICONS[event.type] || '&#128197;';
  var typeLabel = TYPE_LABELS[event.type] || 'Event';
  var startDate = new Date(event.date);
  var month = startDate.toLocaleDateString('en-US', { month: 'short' }).toUpperCase();
  var day = startDate.getDate();
  var countdown = formatDaysUntil(event.date);
  var recommend = event.stephenRecommends
    ? '<span class="stephen-recommends">&#9733; Stephen Recommends</span>'
    : '';

  var cardClass = 'calendar-event';
  if (event.stephenRecommends) cardClass += ' recommended';

  var monthKey = startDate.getFullYear() + '-' + String(startDate.getMonth() + 1).padStart(2, '0');

  var html = '<div class="' + cardClass
    + '" data-type="' + calEscapeHtml(event.type || '')
    + '" data-month="' + calEscapeHtml(monthKey)
    + '" data-recommended="' + (event.stephenRecommends ? 'true' : 'false') + '">';

  // Date block
  html += '<div class="event-date-block">';
  html += '<div class="event-month">' + calEscapeHtml(month) + '</div>';
  html += '<div class="event-day">' + day + '</div>';
  html += '<div class="event-countdown">' + calEscapeHtml(countdown) + '</div>';
  html += '</div>';

  // Body
  html += '<div class="event-body">';
  html += '<div class="event-type-badge">' + icon + ' ' + calEscapeHtml(typeLabel.toUpperCase()) + '</div>';
  html += '<h3 class="event-title">' + calEscapeHtml(event.title) + '</h3>';
  html += '<div class="event-meta">';
  html += '<span class="event-location">&#128205; ' + calEscapeHtml(event.location || 'TBD') + '</span>';
  html += '<span class="event-dot">&middot;</span>';
  html += '<span class="event-dates">' + calEscapeHtml(formatEventDateRange(event.date, event.endDate)) + '</span>';
  html += '</div>';
  html += '<p class="event-description">' + calEscapeHtml(event.description || '') + '</p>';

  if (event.keyAttendees && event.keyAttendees.length) {
    html += '<div class="event-attendees">';
    html += '<span class="event-attendees-label">Key Companies:</span> ';
    html += event.keyAttendees.map(calEscapeHtml).join(', ');
    html += '</div>';
  }

  html += '<div class="event-footer">';
  html += recommend;
  if (event.url && event.url !== '#') {
    html += '<a href="' + calSanitizeUrl(event.url) + '" target="_blank" rel="noopener" class="event-link">Visit Event &rarr;</a>';
  }
  html += '</div>';
  html += '</div>'; // .event-body
  html += '</div>'; // .calendar-event
  return html;
}

function renderCalendar() {
  var container = document.getElementById('calendar-content');
  if (!container) return;

  var now = new Date();
  now.setHours(0, 0, 0, 0);

  var upcoming = CAL_STATE.events.filter(function(e) {
    var d = new Date(e.date);
    return !isNaN(d.getTime()) && d >= now;
  });

  upcoming.sort(function(a, b) {
    return new Date(a.date) - new Date(b.date);
  });

  if (!upcoming.length) {
    container.innerHTML = '<div class="calendar-empty">'
      + '<div class="calendar-empty-icon">&#128197;</div>'
      + '<h3>No upcoming events</h3>'
      + '<p>We\'re curating the next batch of frontier tech gatherings. Check back soon.</p>'
      + '</div>';
    return;
  }

  var total = upcoming.length;
  var visible = upcoming.slice(0, calShownCount);

  var html = '<div class="calendar-list">';
  visible.forEach(function(event) { html += calendarEventHTML(event); });
  html += '</div>';

  if (total > CAL_INITIAL_COUNT) {
    var remaining = total - calShownCount;
    if (remaining > 0) {
      var nextBatch = Math.min(CAL_STEP_SIZE, remaining);
      html += '<div class="paginated-list-actions"><button class="show-more-btn" type="button" data-cal-action="show-more">Show ' + nextBatch + ' more events <span class="show-more-count">(' + remaining + ' remaining)</span></button></div>';
    } else {
      html += '<div class="paginated-list-actions"><button class="show-more-btn show-less-btn" type="button" data-cal-action="show-less">Show less</button></div>';
    }
  }

  container.innerHTML = html;

  var btn = container.querySelector('[data-cal-action]');
  if (btn) {
    btn.addEventListener('click', function() {
      if (btn.getAttribute('data-cal-action') === 'show-more') {
        calShownCount = Math.min(calShownCount + CAL_STEP_SIZE, total);
      } else {
        calShownCount = CAL_INITIAL_COUNT;
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      renderCalendar();
      // Re-apply filters after re-render so filter state is preserved
      if (typeof applyCalendarFilters === 'function') applyCalendarFilters();
    });
  }
}

function populateMonthFilter() {
  var sel = document.getElementById('month-filter');
  if (!sel) return;
  var now = new Date();
  now.setHours(0, 0, 0, 0);

  var seen = {};
  var months = [];
  CAL_STATE.events.forEach(function(e) {
    var d = new Date(e.date);
    if (isNaN(d.getTime()) || d < now) return;
    var key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
    if (!seen[key]) {
      seen[key] = true;
      months.push({
        key: key,
        label: d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
        sortValue: d.getFullYear() * 100 + d.getMonth()
      });
    }
  });
  months.sort(function(a, b) { return a.sortValue - b.sortValue; });
  months.forEach(function(m) {
    var opt = document.createElement('option');
    opt.value = m.key;
    opt.textContent = m.label;
    sel.appendChild(opt);
  });
}

// ─── FILTERING ───────────────────────────────────────────────────────────────
function applyCalendarFilters() {
  var f = CAL_STATE.filters;
  var cards = document.querySelectorAll('.calendar-event');
  cards.forEach(function(card) {
    var matchType = f.type === 'all' || card.dataset.type === f.type;
    var matchMonth = f.month === 'all' || card.dataset.month === f.month;
    var matchRecommended = !f.recommended || card.dataset.recommended === 'true';
    card.style.display = (matchType && matchMonth && matchRecommended) ? '' : 'none';
  });
}

function initCalendarFilters() {
  var typeBtns = document.querySelectorAll('.calendar-filter[data-filter="type"]');
  typeBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      typeBtns.forEach(function(b) { b.classList.remove('active'); });
      this.classList.add('active');
      CAL_STATE.filters.type = this.dataset.type || 'all';
      applyCalendarFilters();
    });
  });

  var recommendBtn = document.querySelector('.calendar-filter[data-filter="recommended"]');
  if (recommendBtn) {
    recommendBtn.addEventListener('click', function() {
      CAL_STATE.filters.recommended = !CAL_STATE.filters.recommended;
      this.classList.toggle('active', CAL_STATE.filters.recommended);
      applyCalendarFilters();
    });
  }

  var monthSel = document.getElementById('month-filter');
  if (monthSel) {
    monthSel.addEventListener('change', function() {
      CAL_STATE.filters.month = this.value || 'all';
      applyCalendarFilters();
    });
  }
}

// ─── BOOT ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  calInitMobileMenu();
  try {
    CAL_STATE.events = FRONTIER_EVENTS.slice();
    populateMonthFilter();
    renderCalendar();
    initCalendarFilters();
  } catch (e) {
    console.error('[calendar] failed to render:', e);
    var container = document.getElementById('calendar-content');
    if (container) {
      container.innerHTML = '<div class="calendar-empty"><h3>Unable to load calendar</h3><p>' + calEscapeHtml(e.message || 'Unknown error') + '</p></div>';
    }
  }
});
