/*
 * Structured Data (JSON-LD) — The Innovators League
 *
 * Injects schema.org metadata into the document head so search engines can
 * render rich results. Three layers:
 *
 *   1. Organization — site owner (ROS). Same on every page.
 *   2. WebSite — site itself with a search action. Same on every page.
 *   3. WebPage / CollectionPage — page-specific. Reads:
 *        document.querySelector('link[rel="canonical"]').href
 *        document.title
 *        meta[name="description"]
 *      plus an optional `window.IL_STRUCTURED_DATA` extension block that a
 *      page can set BEFORE loading this script:
 *
 *        window.IL_STRUCTURED_DATA = {
 *          type: 'CollectionPage',
 *          itemListName: 'Defense Tech Companies',
 *          // optional: an array of {name, url} that becomes ItemList items
 *          itemList: [...]
 *        };
 */
(function () {
  'use strict';

  function $meta(name) {
    var el = document.querySelector('meta[name="' + name + '"]') ||
             document.querySelector('meta[property="' + name + '"]');
    return el ? el.getAttribute('content') : '';
  }
  function $canonical() {
    var el = document.querySelector('link[rel="canonical"]');
    return el ? el.href : (location.origin + location.pathname);
  }

  function inject(obj) {
    var s = document.createElement('script');
    s.type = 'application/ld+json';
    s.textContent = JSON.stringify(obj);
    document.head.appendChild(s);
  }

  var BASE = 'https://innovatorsleague.com';

  // ─── Organization ────────────────────────────────────────────────────────
  inject({
    '@context': 'https://schema.org',
    '@type': 'Organization',
    'name': 'The Innovators League',
    'legalName': 'Rational Optimist Society',
    'alternateName': ['ROS', 'Innovators League'],
    'url': BASE + '/',
    'logo': BASE + '/og-default.png',
    'description': 'The deal engine for frontier technology. Intelligence, access, and deal flow on the companies rebuilding the American industrial base.',
    'sameAs': [
      'https://twitter.com/rationalopt',
      'https://rationaloptimistsociety.substack.com',
      'https://www.rationaloptimistsociety.com'
    ],
    'founder': {
      '@type': 'Person',
      'name': 'Stephen McBride',
      'sameAs': 'https://twitter.com/stephenmcb'
    }
  });

  // ─── WebSite ─────────────────────────────────────────────────────────────
  inject({
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    'name': 'The Innovators League',
    'url': BASE + '/',
    'description': 'Frontier-tech intelligence platform tracking defense, space, nuclear, semiconductors, and advanced-manufacturing companies.',
    'publisher': { '@type': 'Organization', 'name': 'Rational Optimist Society' },
    'potentialAction': {
      '@type': 'SearchAction',
      'target': BASE + '/?q={search_term_string}',
      'query-input': 'required name=search_term_string'
    }
  });

  // ─── Per-page WebPage / CollectionPage ───────────────────────────────────
  var ext = window.IL_STRUCTURED_DATA || {};
  var pageType = ext.type || 'WebPage';
  var pageObj = {
    '@context': 'https://schema.org',
    '@type': pageType,
    'name': document.title || 'The Innovators League',
    'url': $canonical(),
    'description': $meta('description') || '',
    'isPartOf': { '@type': 'WebSite', 'url': BASE + '/' }
  };

  if (pageType === 'CollectionPage' && Array.isArray(ext.itemList)) {
    pageObj.mainEntity = {
      '@type': 'ItemList',
      'name': ext.itemListName || document.title,
      'numberOfItems': ext.itemList.length,
      'itemListElement': ext.itemList.slice(0, 50).map(function (item, i) {
        return {
          '@type': 'ListItem',
          'position': i + 1,
          'name': item.name,
          'url': item.url || (BASE + '/company.html?c=' + encodeURIComponent(item.name))
        };
      })
    };
  }
  inject(pageObj);

  // ─── BreadcrumbList (if breadcrumb element present) ──────────────────────
  var crumb = document.querySelector('.breadcrumb');
  if (crumb) {
    var items = [];
    var links = crumb.querySelectorAll('a');
    var current = crumb.querySelector('[aria-current="page"]');
    var pos = 1;
    links.forEach(function (a) {
      var href = a.getAttribute('href') || '';
      if (href === '#' || href === '') return;
      var url = href.indexOf('http') === 0 ? href : (BASE + '/' + href.replace(/^\/+/, ''));
      items.push({
        '@type': 'ListItem',
        'position': pos++,
        'name': (a.textContent || '').trim(),
        'item': url
      });
    });
    if (current && current.textContent.trim()) {
      items.push({
        '@type': 'ListItem',
        'position': pos,
        'name': current.textContent.trim()
      });
    }
    if (items.length > 1) {
      inject({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': items
      });
    }
  }
})();
