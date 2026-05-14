/*
 * Cookie Consent Banner - The Innovators League
 *
 * Reusable consent banner injected on every page.
 *
 * Storage: localStorage key `il_cookie_consent`
 *   "accepted" | "rejected" | "" (unset)
 *
 * Behavior:
 *   - Injects banner DOM and styles on DOMContentLoaded if no prior choice.
 *   - User clicks Accept/Reject → records choice, hides banner.
 *   - Other scripts (analytics.js, posthog, etc.) can check
 *     window.TIL_CookieConsent.hasConsented() before firing.
 *
 * Re-open later: window.TIL_CookieConsent.show()
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'il_cookie_consent';
  var VERSION = '1';
  var VERSION_KEY = 'il_cookie_consent_version';

  function read() {
    try { return localStorage.getItem(STORAGE_KEY) || ''; } catch (e) { return ''; }
  }
  function write(v) {
    try {
      localStorage.setItem(STORAGE_KEY, v);
      localStorage.setItem(VERSION_KEY, VERSION);
    } catch (e) {}
  }
  function needsConsent() {
    var v = read();
    return !v || v === '';
  }

  function injectStyles() {
    if (document.getElementById('il-cookie-consent-styles')) return;
    var style = document.createElement('style');
    style.id = 'il-cookie-consent-styles';
    style.textContent = '\
      .il-cookie-consent {\
        position: fixed; bottom: 16px; left: 16px; right: 16px;\
        max-width: 720px; margin: 0 auto;\
        background: rgba(13, 17, 23, 0.97);\
        backdrop-filter: blur(8px);\
        -webkit-backdrop-filter: blur(8px);\
        border: 1px solid rgba(34, 197, 94, 0.35);\
        border-radius: 12px;\
        padding: 16px 20px;\
        font-family: "Inter", system-ui, -apple-system, sans-serif;\
        color: #e6edf3;\
        z-index: 99999;\
        box-shadow: 0 10px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04) inset;\
        display: flex; flex-direction: column; gap: 12px;\
        animation: ilCookieIn 280ms ease-out;\
      }\
      @keyframes ilCookieIn {\
        from { opacity: 0; transform: translateY(20px); }\
        to   { opacity: 1; transform: translateY(0); }\
      }\
      .il-cookie-consent__body {\
        font-size: 13px; line-height: 1.5; color: #c9d1d9;\
      }\
      .il-cookie-consent__body strong { color: #22c55e; font-weight: 600; }\
      .il-cookie-consent__body a { color: #4ade80; text-decoration: underline; text-decoration-color: rgba(74,222,128,0.4); }\
      .il-cookie-consent__body a:hover { text-decoration-color: #4ade80; }\
      .il-cookie-consent__actions {\
        display: flex; gap: 8px; flex-wrap: wrap; align-items: center;\
      }\
      .il-cookie-consent__btn {\
        font-family: "Inter", system-ui, sans-serif;\
        font-size: 12px; font-weight: 600;\
        padding: 8px 16px;\
        border-radius: 6px;\
        border: 1px solid transparent;\
        cursor: pointer;\
        transition: all 140ms ease;\
        letter-spacing: 0.02em;\
      }\
      .il-cookie-consent__btn--accept {\
        background: #22c55e; color: #0d1117;\
      }\
      .il-cookie-consent__btn--accept:hover {\
        background: #4ade80; transform: translateY(-1px);\
      }\
      .il-cookie-consent__btn--reject {\
        background: transparent; color: #c9d1d9;\
        border-color: rgba(255,255,255,0.15);\
      }\
      .il-cookie-consent__btn--reject:hover {\
        background: rgba(255,255,255,0.06); color: #e6edf3;\
      }\
      .il-cookie-consent__close {\
        position: absolute; top: 8px; right: 12px;\
        background: none; border: none; color: #8b949e;\
        cursor: pointer; font-size: 18px; line-height: 1;\
        padding: 4px 8px;\
      }\
      .il-cookie-consent__close:hover { color: #e6edf3; }\
      @media (min-width: 640px) {\
        .il-cookie-consent { flex-direction: row; align-items: center; }\
        .il-cookie-consent__body { flex: 1; }\
        .il-cookie-consent__actions { flex-shrink: 0; }\
      }\
      @media (max-width: 480px) {\
        .il-cookie-consent { left: 8px; right: 8px; bottom: 8px; padding: 14px 16px; }\
        .il-cookie-consent__btn { flex: 1; text-align: center; }\
      }\
    ';
    document.head.appendChild(style);
  }

  function buildBanner() {
    var wrap = document.createElement('div');
    wrap.className = 'il-cookie-consent';
    wrap.setAttribute('role', 'dialog');
    wrap.setAttribute('aria-label', 'Cookie consent');
    wrap.id = 'il-cookie-consent-banner';

    var body = document.createElement('div');
    body.className = 'il-cookie-consent__body';
    body.innerHTML =
      '<strong>Cookies &amp; analytics.</strong> ' +
      'We use essential cookies for sign-in plus privacy-friendly analytics to understand which pages our readers find useful. ' +
      'No third-party tracking or ads. See our <a href="privacy.html">Privacy Policy</a>.';

    var actions = document.createElement('div');
    actions.className = 'il-cookie-consent__actions';

    var reject = document.createElement('button');
    reject.className = 'il-cookie-consent__btn il-cookie-consent__btn--reject';
    reject.type = 'button';
    reject.textContent = 'Essential only';

    var accept = document.createElement('button');
    accept.className = 'il-cookie-consent__btn il-cookie-consent__btn--accept';
    accept.type = 'button';
    accept.textContent = 'Accept all';

    reject.addEventListener('click', function () {
      write('rejected');
      dismiss();
      try { window.dispatchEvent(new CustomEvent('il:cookie-consent', { detail: { choice: 'rejected' } })); } catch (e) {}
    });

    accept.addEventListener('click', function () {
      write('accepted');
      dismiss();
      try { window.dispatchEvent(new CustomEvent('il:cookie-consent', { detail: { choice: 'accepted' } })); } catch (e) {}
    });

    actions.appendChild(reject);
    actions.appendChild(accept);
    wrap.appendChild(body);
    wrap.appendChild(actions);

    return wrap;
  }

  function dismiss() {
    var existing = document.getElementById('il-cookie-consent-banner');
    if (!existing) return;
    existing.style.transition = 'opacity 200ms ease, transform 200ms ease';
    existing.style.opacity = '0';
    existing.style.transform = 'translateY(20px)';
    setTimeout(function () { if (existing.parentNode) existing.parentNode.removeChild(existing); }, 220);
  }

  function show(force) {
    injectStyles();
    if (document.getElementById('il-cookie-consent-banner')) return;
    if (!force && !needsConsent()) return;
    var banner = buildBanner();
    document.body.appendChild(banner);
  }

  function init() {
    if (needsConsent()) show(false);
  }

  // Public API for analytics scripts + footer "manage cookies" link
  window.TIL_CookieConsent = {
    hasConsented: function () { return read() === 'accepted'; },
    hasRejected:  function () { return read() === 'rejected'; },
    choice:       function () { return read(); },
    show:         function () { show(true); },
    reset:        function () {
      try { localStorage.removeItem(STORAGE_KEY); localStorage.removeItem(VERSION_KEY); } catch (e) {}
      show(true);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
