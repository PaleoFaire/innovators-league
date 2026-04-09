/* ─── Weekly Intelligence Brief ─── */

(function () {
  'use strict';

  // Use globals from utils.js: escapeHtml, formatDateAbsolute
  var escapeHTML = escapeHtml;
  var formatDate = formatDateAbsolute;

  /* ── Section Renderers ── */

  function renderFundingRounds(items) {
    if (!items || !items.length) return '<p class="brief-empty">No funding rounds this week.</p>';
    return '<div class="brief-table-wrap"><table class="brief-table">' +
      '<thead><tr><th>Company</th><th>Amount</th><th>Round</th><th>Investor</th><th>Date</th></tr></thead><tbody>' +
      items.map(function (item) {
        return '<tr>' +
          '<td class="brief-company-name">' + escapeHTML(item.company) + '</td>' +
          '<td class="brief-amount">' + escapeHTML(item.amount) + '</td>' +
          '<td><span class="brief-badge brief-badge-round">' + escapeHTML(item.round) + '</span></td>' +
          '<td>' + escapeHTML(item.investor || 'Undisclosed') + '</td>' +
          '<td class="brief-date-cell">' + escapeHTML(item.date) + '</td>' +
          '</tr>';
      }).join('') +
      '</tbody></table></div>';
  }

  function renderSECActivity(items) {
    if (!items || !items.length) return '<p class="brief-empty">No SEC activity this week.</p>';
    var displayed = items.slice(0, 20);
    var html = '<div class="brief-grid brief-grid-sec">' +
      displayed.map(function (item) {
        var ipoTag = item.isIPO ? '<span class="brief-badge brief-badge-ipo">IPO</span>' : '';
        return '<div class="brief-item-card">' +
          '<div class="brief-item-header">' +
            '<span class="brief-form-badge">' + escapeHTML(item.form) + '</span>' +
            ipoTag +
          '</div>' +
          '<div class="brief-item-company">' + escapeHTML(item.company) + '</div>' +
          '<div class="brief-item-date">' + formatDate(item.date) + '</div>' +
          '</div>';
      }).join('') +
      '</div>';
    if (items.length > 20) {
      html += '<p class="brief-more-note">Showing 20 of ' + items.length + ' filings</p>';
    }
    return html;
  }

  function renderFederalRegister(items) {
    if (!items || !items.length) return '<p class="brief-empty">No federal register entries this week.</p>';
    var displayed = items.slice(0, 15);
    var html = '<div class="brief-list">' +
      displayed.map(function (item) {
        var agencies = (item.agencies || []).join(', ');
        var sigBadge = item.significant ? '<span class="brief-badge brief-badge-sig">Significant</span>' : '';
        return '<div class="brief-list-item">' +
          '<div class="brief-list-item-top">' +
            '<span class="brief-badge brief-badge-type">' + escapeHTML(item.type) + '</span>' +
            sigBadge +
            '<span class="brief-item-date">' + formatDate(item.date) + '</span>' +
          '</div>' +
          '<div class="brief-list-item-title">' + escapeHTML(item.title) + '</div>' +
          '<div class="brief-list-item-meta">' + escapeHTML(agencies) + '</div>' +
          '</div>';
      }).join('') +
      '</div>';
    if (items.length > 15) {
      html += '<p class="brief-more-note">Showing 15 of ' + items.length + ' entries</p>';
    }
    return html;
  }

  function renderMarketSignals(items) {
    if (!items || !items.length) return '<p class="brief-empty">No market signals this week.</p>';
    var displayed = items.slice(0, 15);
    var html = '<div class="brief-list">' +
      displayed.map(function (item) {
        var impactClass = item.impact === 'high' ? 'brief-badge-high' : 'brief-badge-med';
        var typeLabel = (item.type || '').toUpperCase();
        return '<div class="brief-list-item brief-list-item-signal">' +
          '<div class="brief-list-item-top">' +
            '<span class="brief-badge ' + impactClass + '">' + escapeHTML(item.impact || 'medium') + '</span>' +
            '<span class="brief-badge brief-badge-type">' + escapeHTML(typeLabel) + '</span>' +
          '</div>' +
          '<div class="brief-list-item-title">' + escapeHTML(item.title) + '</div>' +
          '<div class="brief-list-item-meta">' +
            '<span class="brief-signal-source">' + escapeHTML(item.source) + '</span>' +
            (item.company ? ' &middot; <span class="brief-signal-company">' + escapeHTML(item.company) + '</span>' : '') +
          '</div>' +
          '</div>';
      }).join('') +
      '</div>';
    if (items.length > 15) {
      html += '<p class="brief-more-note">Showing 15 of ' + items.length + ' signals</p>';
    }
    return html;
  }

  function renderHackerNews(items) {
    if (!items || !items.length) return '<p class="brief-empty">No Hacker News items this week.</p>';
    var displayed = items.slice(0, 12);
    var html = '<div class="brief-grid brief-grid-hn">' +
      displayed.map(function (item) {
        var companies = (item.companies || []).join(', ');
        return '<div class="brief-item-card brief-hn-card">' +
          '<div class="brief-hn-score">' + (item.score || 0) + ' pts</div>' +
          '<a href="' + escapeHTML(item.url || '#') + '" target="_blank" rel="noopener" class="brief-hn-title">' +
            escapeHTML(item.title) +
          '</a>' +
          '<div class="brief-hn-meta">' +
            '<span>' + (item.comments || 0) + ' comments</span>' +
            (companies ? '<span class="brief-hn-companies">' + escapeHTML(companies) + '</span>' : '') +
          '</div>' +
          '</div>';
      }).join('') +
      '</div>';
    if (items.length > 12) {
      html += '<p class="brief-more-note">Showing 12 of ' + items.length + ' stories</p>';
    }
    return html;
  }

  function renderPressReleases(items) {
    if (!items || !items.length) return '<p class="brief-empty">No press releases this week.</p>';
    var displayed = items.slice(0, 12);
    var html = '<div class="brief-list">' +
      displayed.map(function (item) {
        var companies = (item.companies || []).filter(function (c) { return c; }).join(', ');
        return '<div class="brief-list-item">' +
          '<div class="brief-list-item-top">' +
            '<span class="brief-badge brief-badge-type">' + escapeHTML(item.source || 'Press') + '</span>' +
          '</div>' +
          '<div class="brief-list-item-title">' + escapeHTML(item.title) + '</div>' +
          (companies ? '<div class="brief-list-item-meta">Related: ' + escapeHTML(companies) + '</div>' : '') +
          '</div>';
      }).join('') +
      '</div>';
    if (items.length > 12) {
      html += '<p class="brief-more-note">Showing 12 of ' + items.length + ' releases</p>';
    }
    return html;
  }

  function renderGenericSection(items) {
    if (!items || !items.length) return '<p class="brief-empty">No items this week.</p>';
    return '<div class="brief-list">' +
      items.slice(0, 15).map(function (item) {
        var title = item.title || item.company || 'Untitled';
        var desc = item.description || item.source || '';
        return '<div class="brief-list-item">' +
          '<div class="brief-list-item-title">' + escapeHTML(title) + '</div>' +
          (desc ? '<div class="brief-list-item-meta">' + escapeHTML(desc) + '</div>' : '') +
          '</div>';
      }).join('') +
      '</div>';
  }

  /* ── Section Router ── */
  function renderSectionItems(sectionTitle, items) {
    var t = sectionTitle.toLowerCase();
    if (t.indexOf('funding') !== -1) return renderFundingRounds(items);
    if (t.indexOf('sec') !== -1) return renderSECActivity(items);
    if (t.indexOf('federal') !== -1) return renderFederalRegister(items);
    if (t.indexOf('market') !== -1) return renderMarketSignals(items);
    if (t.indexOf('hacker') !== -1) return renderHackerNews(items);
    if (t.indexOf('press') !== -1) return renderPressReleases(items);
    return renderGenericSection(items);
  }

  /* ── What Stephen Is Watching ── */
  function renderWatchList() {
    if (typeof FIELD_NOTES === 'undefined' || !FIELD_NOTES.length) return '';
    var latest = FIELD_NOTES.slice(0, 3);
    var badgeMap = {
      'strong-buy': { label: 'STRONG BUY', color: '#22c55e' },
      'buy': { label: 'BUY', color: '#3b82f6' },
      'watch': { label: 'WATCH', color: '#f59e0b' },
      'caution': { label: 'CAUTION', color: '#ef4444' }
    };
    var html = '<section class="brief-section brief-watchlist">' +
      '<div class="brief-section-header">' +
        '<div class="brief-section-icon">&#128065;</div>' +
        '<div class="brief-section-title-group">' +
          '<h2 class="brief-section-title">What Stephen Is Watching</h2>' +
          '<span class="brief-section-count">Latest field notes</span>' +
        '</div>' +
      '</div>' +
      '<div class="brief-section-body">' +
        '<div class="brief-watchlist-grid">';
    latest.forEach(function(note) {
      var b = badgeMap[note.conviction] || badgeMap['watch'];
      html += '<a href="company.html?slug=' + companyToSlug(note.company) + '" class="brief-watchlist-item">' +
        '<div class="brief-watchlist-item-header">' +
          '<span class="brief-watchlist-company">' + escapeHTML(note.company) + '</span>' +
          '<span class="brief-watchlist-badge" style="color:' + b.color + '; border-color:' + b.color + ';">' + b.label + '</span>' +
        '</div>' +
        '<p class="brief-watchlist-insight">' + escapeHTML(note.insight ? (note.insight.length > 140 ? note.insight.substring(0, 140) + '...' : note.insight) : '') + '</p>' +
      '</a>';
    });
    html += '</div></div></section>';
    return html;
  }

  /* ── Main Render ── */
  function renderBrief(data) {
    var container = document.getElementById('brief-content');
    if (!container) return;

    // Update hero stats
    var dateEl = document.getElementById('brief-date');
    var totalEl = document.getElementById('brief-total-items');
    var secCountEl = document.getElementById('brief-section-count');
    if (dateEl) dateEl.textContent = data.display_date || formatDate(data.date) || '---';
    if (totalEl) totalEl.textContent = data.total_items || 0;
    if (secCountEl) secCountEl.textContent = data.section_count || 0;

    var html = '<div class="brief-sections">';

    // Watch list at the top
    html += renderWatchList();

    // Table of contents
    html += '<nav class="brief-toc">';
    html += '<h3 class="brief-toc-title">In This Brief</h3>';
    html += '<div class="brief-toc-items">';
    (data.sections || []).forEach(function (section, i) {
      html += '<a href="#brief-section-' + i + '" class="brief-toc-item">' +
        '<span class="brief-toc-icon">' + (section.icon || '') + '</span>' +
        '<span class="brief-toc-label">' + escapeHTML(section.title) + '</span>' +
        '<span class="brief-toc-count">' + (section.count || 0) + '</span>' +
        '</a>';
    });
    html += '</div></nav>';

    // Sections
    (data.sections || []).forEach(function (section, i) {
      html += '<section class="brief-section" id="brief-section-' + i + '">' +
        '<div class="brief-section-header">' +
          '<div class="brief-section-icon">' + (section.icon || '') + '</div>' +
          '<div class="brief-section-title-group">' +
            '<h2 class="brief-section-title">' + escapeHTML(section.title) + '</h2>' +
            '<span class="brief-section-count">' + (section.count || 0) + ' items</span>' +
          '</div>' +
        '</div>' +
        '<div class="brief-section-body">' +
          renderSectionItems(section.title, section.items) +
        '</div>' +
        '</section>';
    });

    html += '</div>';

    // Brief footer with metadata
    html += '<div class="brief-meta">' +
      '<p>Brief ID: <code>' + escapeHTML(data.brief_id || '') + '</code></p>' +
      '<p>Generated: ' + escapeHTML(data.generated_at ? new Date(data.generated_at).toLocaleString() : '') + '</p>' +
      '<p>Data cutoff: ' + escapeHTML(data.cutoff ? new Date(data.cutoff).toLocaleString() : '') + '</p>' +
      '</div>';

    container.innerHTML = html;
  }

  /* ── Fetch & Init ── */
  window.loadBrief = function loadBrief() {
    var skeleton = document.getElementById('brief-skeleton');
    var content = document.getElementById('brief-content');
    var errorEl = document.getElementById('brief-error');

    if (skeleton) skeleton.style.display = '';
    if (content) content.style.display = 'none';
    if (errorEl) errorEl.style.display = 'none';

    fetch('data/weekly_brief.json')
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function (data) {
        renderBrief(data);
        if (skeleton) skeleton.style.display = 'none';
        if (content) content.style.display = '';
      })
      .catch(function (err) {
        console.error('Failed to load weekly brief:', err);
        if (skeleton) skeleton.style.display = 'none';
        if (errorEl) errorEl.style.display = '';
      });
  };

  document.addEventListener('DOMContentLoaded', function () {
    if (typeof initMobileMenu === 'function') initMobileMenu();
    window.loadBrief();
  });
})();
