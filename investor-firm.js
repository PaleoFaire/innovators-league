/**
 * Per-Investor Deep Page — investor-firm.html?firm=<URL-encoded-name>
 *
 * Renders a complete profile for one VC firm from the existing
 * VC_FIRMS global. Empty-UI rule: every section is gated on real data.
 * No "—" placeholders; if a field is missing, the section doesn't show.
 *
 * Sections:
 *   1. Hero — name, AUM, founded, HQ, website, signal status
 *   2. Thesis — the firm's investment thesis (rich text)
 *   3. ROS Insight — our editorial take on the firm
 *   4. Sector breakdown — bar chart of portfolio by sector
 *   5. Portfolio companies — grid of cards linking to company profiles
 *   6. Co-investors — top funds they syndicate with most often
 *   7. Recent deals — from DEAL_TRACKER if firm name appears
 *   8. Key partners — founder + named investors
 */

(function () {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // Bulletproof global reader (handles const X = ... and window.X = ...)
  function G(name) {
    if (typeof window[name] !== 'undefined') return window[name];
    try { return new Function('try { return typeof ' + name + ' !== "undefined" ? ' + name + ' : null; } catch (e) { return null; }')(); }
    catch (e) { return null; }
  }

  function getFirmFromQuery() {
    const params = new URLSearchParams(window.location.search);
    return (params.get('firm') || params.get('f') || '').trim();
  }

  function findFirm(name) {
    const firms = G('VC_FIRMS');
    if (!Array.isArray(firms) || !name) return null;
    const nameLc = name.toLowerCase();
    // Exact match first
    let f = firms.find(x => (x.name || '').toLowerCase() === nameLc);
    if (f) return f;
    // shortName match
    f = firms.find(x => (x.shortName || '').toLowerCase() === nameLc);
    if (f) return f;
    // Substring (for "a16z" → "a16z (Andreessen Horowitz)")
    f = firms.find(x =>
      (x.name || '').toLowerCase().indexOf(nameLc) >= 0 ||
      (x.shortName || '').toLowerCase().indexOf(nameLc) >= 0
    );
    return f || null;
  }

  function getCompanyByName(name) {
    const cos = G('COMPANIES');
    if (!Array.isArray(cos) || !name) return null;
    const nameLc = name.toLowerCase();
    return cos.find(c => (c.name || '').toLowerCase() === nameLc) || null;
  }

  // Render: hero
  function renderHero(firm) {
    let html = '<header class="if-hero"><div class="if-hero-inner">';
    html += '<a class="if-back" href="investors.html">← Investor directory</a>';
    html += '<h1 class="if-name">' + esc(firm.name) + '</h1>';
    if (firm.flagshipFund) {
      html += '<div style="font-size:13px; color:rgba(255,255,255,0.55); margin-top:4px;">' +
        'Flagship: <strong style="color:#86efac;">' + esc(firm.flagshipFund) + '</strong></div>';
    }
    const meta = [];
    if (firm.aum) meta.push({ lbl: 'AUM', val: firm.aum });
    if (firm.founded) meta.push({ lbl: 'Founded', val: String(firm.founded) });
    if (firm.hq) meta.push({ lbl: 'HQ', val: firm.hq });
    if (Array.isArray(firm.portfolioCompanies)) {
      meta.push({ lbl: 'Portfolio', val: firm.portfolioCompanies.length + ' tracked cos' });
    }
    if (meta.length) {
      html += '<div class="if-meta">' +
        meta.map(m =>
          '<div class="if-meta-item"><span class="if-meta-label">' + esc(m.lbl) + '</span>' +
          '<span class="if-meta-value">' + esc(m.val) + '</span></div>'
        ).join('') + '</div>';
    }
    if (firm.website) {
      html += '<a class="if-website" href="' + esc(firm.website) + '" target="_blank" rel="noopener">Visit firm site →</a>';
    }
    html += '</div></header>';
    return html;
  }

  // Render: container open + sections
  function renderSections(firm) {
    let html = '<main class="if-container">';

    // Thesis
    if (firm.thesis) {
      html += section('Investment Thesis', '<p class="if-thesis-text">' + esc(firm.thesis) + '</p>');
    }

    // ROS Insight
    if (firm.insight) {
      html += section('ROS Editorial Take', '<p class="if-insight-text">' + esc(firm.insight) + '</p>');
    }

    // Sector breakdown — derived from portfolio companies
    const sectors = computeSectorMix(firm);
    if (sectors.length) {
      const max = sectors[0].count;
      let bars = '<div class="if-sectors">';
      sectors.forEach(s => {
        const pct = (s.count / max) * 100;
        bars += '<div class="if-sector-bar">' +
          '<div class="if-sector-lbl">' + esc(s.sector) + '</div>' +
          '<div class="if-sector-track"><div class="if-sector-fill" style="width:' + pct.toFixed(1) + '%"></div></div>' +
          '<div class="if-sector-cnt">' + s.count + '</div>' +
          '</div>';
      });
      bars += '</div>';
      html += section('Portfolio by Sector', bars);
    }

    // Sector focus (declared)
    if (Array.isArray(firm.sectorFocus) && firm.sectorFocus.length) {
      html += section('Stated Sector Focus',
        '<div class="if-partners">' +
          firm.sectorFocus.map(s => '<span class="if-partner">' + esc(s) + '</span>').join('') +
        '</div>');
    }

    // Key partners
    if (Array.isArray(firm.keyPartners) && firm.keyPartners.length) {
      html += section('Key Partners',
        '<div class="if-partners">' +
          firm.keyPartners.map(p => '<span class="if-partner">' + esc(p) + '</span>').join('') +
        '</div>');
    }

    // Portfolio companies
    if (Array.isArray(firm.portfolioCompanies) && firm.portfolioCompanies.length) {
      let grid = '<div class="if-portfolio-grid">';
      firm.portfolioCompanies.forEach(pcName => {
        const co = getCompanyByName(pcName);
        const meta = co ? [
          co.sector ? '<span class="if-pc-sector">' + esc(co.sector) + '</span>' : '',
          co.fundingStage ? esc(co.fundingStage) : '',
        ].filter(Boolean).join(' · ') : '';
        grid += '<a class="if-portfolio-card" href="company.html?c=' + encodeURIComponent(pcName) + '">' +
          '<div class="if-pc-name">' + esc(pcName) + '</div>' +
          (meta ? '<div class="if-pc-meta">' + meta + '</div>' : '') +
        '</a>';
      });
      grid += '</div>';
      html += section('Portfolio Companies (' + firm.portfolioCompanies.length + ')', grid);
    }

    // Co-investors — funds with most overlap in portfolio
    const coinv = computeCoInvestors(firm);
    if (coinv.length) {
      let body = '<div class="if-coinvest-list">';
      coinv.slice(0, 10).forEach(c => {
        body += '<div class="if-coinvest-row">' +
          '<div>' +
            '<div class="if-coinvest-name"><a href="investor-firm.html?firm=' + encodeURIComponent(c.firm.name) + '">' + esc(c.firm.shortName || c.firm.name) + '</a></div>' +
            '<div class="if-coinvest-cos-detail">Shared: ' + esc(c.shared.slice(0, 3).join(' · ')) +
              (c.shared.length > 3 ? ' <span style="color:rgba(255,255,255,0.35);">+' + (c.shared.length - 3) + ' more</span>' : '') +
            '</div>' +
          '</div>' +
          '<div class="if-coinvest-cos">' + c.shared.length + ' co-invest</div>' +
        '</div>';
      });
      body += '</div>';
      html += section('Most Frequent Co-Investors', body);
    }

    // Recent deals from DEAL_TRACKER
    const recent = findRecentDealsByFirm(firm);
    if (recent.length) {
      let body = '<div class="if-deals-list">';
      recent.slice(0, 12).forEach(d => {
        body += '<div class="if-deal">' +
          '<div>' +
            '<div class="if-deal-co"><a href="company.html?c=' + encodeURIComponent(d.company) + '">' + esc(d.company) + '</a></div>' +
            '<div class="if-deal-meta">' + esc(d.round || 'Round') +
              (d.date ? ' · ' + esc(d.date) : '') +
              (d.leadOrParticipant ? ' · ' + esc(d.leadOrParticipant) : '') + '</div>' +
          '</div>' +
          (d.amount ? '<div class="if-deal-amt">' + esc(d.amount) + '</div>' : '') +
        '</div>';
      });
      body += '</div>';
      html += section('Recent Deals', body);
    }

    html += '</main>';
    return html;
  }

  function section(title, body) {
    return '<section class="if-section"><h2>' + esc(title) + '</h2>' + body + '</section>';
  }

  function computeSectorMix(firm) {
    if (!Array.isArray(firm.portfolioCompanies)) return [];
    const counts = {};
    firm.portfolioCompanies.forEach(pcName => {
      const co = getCompanyByName(pcName);
      if (co && co.sector) {
        counts[co.sector] = (counts[co.sector] || 0) + 1;
      }
    });
    return Object.entries(counts)
      .map(([sector, count]) => ({ sector, count }))
      .sort((a, b) => b.count - a.count);
  }

  function computeCoInvestors(firm) {
    const allFirms = G('VC_FIRMS');
    if (!Array.isArray(allFirms) || !Array.isArray(firm.portfolioCompanies)) return [];
    const myPortfolio = new Set(firm.portfolioCompanies.map(c => c.toLowerCase()));
    const others = [];
    allFirms.forEach(other => {
      if (other === firm || !Array.isArray(other.portfolioCompanies)) return;
      const shared = other.portfolioCompanies.filter(c => myPortfolio.has(c.toLowerCase()));
      if (shared.length > 0) {
        others.push({ firm: other, shared });
      }
    });
    return others.sort((a, b) => b.shared.length - a.shared.length);
  }

  function findRecentDealsByFirm(firm) {
    const tracker = G('DEAL_TRACKER');
    if (!Array.isArray(tracker)) return [];
    const candidates = [
      (firm.name || '').toLowerCase(),
      (firm.shortName || '').toLowerCase(),
    ].filter(Boolean);
    return tracker.filter(d => {
      if (!d.investor) return false;
      const inv = String(d.investor).toLowerCase();
      return candidates.some(c => inv.indexOf(c) >= 0 || c.indexOf(inv) >= 0);
    }).sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')));
  }

  function renderNotFound(name) {
    const root = document.getElementById('if-root');
    if (!root) return;
    root.innerHTML =
      '<div class="if-not-found">' +
        '<h2>Investor not found</h2>' +
        '<p>We couldn\'t find <strong>' + esc(name) + '</strong> in the VC_FIRMS database.</p>' +
        '<a href="investors.html">← Browse all investors</a>' +
      '</div>';
  }

  function init() {
    const name = getFirmFromQuery();
    if (!name) {
      renderNotFound('(no firm specified)');
      return;
    }
    const firm = findFirm(name);
    if (!firm) {
      renderNotFound(name);
      return;
    }
    document.title = firm.name + ' | The Innovators League';
    const root = document.getElementById('if-root');
    if (!root) return;
    root.innerHTML = renderHero(firm) + renderSections(firm);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
