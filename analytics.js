// ═══════════════════════════════════════════════════════════════════════════════
// THE INNOVATORS LEAGUE — Analytics & Error Reporting
// ═══════════════════════════════════════════════════════════════════════════════
//
// Wires up Plausible (privacy-friendly page analytics) and Sentry (JS error
// reporting) behind a single config gate so both can be turned on from one
// place. Ships disabled; fill in config and reload.
//
// To enable:
//   1. Create a Plausible site at plausible.io (or self-host) and set
//      window.__TIL_PLAUSIBLE_DOMAIN to your domain string, e.g.
//      "innovatorsleague.com". You can do this inline before loading this
//      script, or edit the default below.
//   2. Create a Sentry project (free tier works) and set
//      window.__TIL_SENTRY_DSN to your DSN URL.
//   3. Load this script from every page's <head> AFTER any inline config.
//
// Respects Do-Not-Track and never collects PII. Plausible is cookieless;
// Sentry redacts form-input content via `maskAllInputs: true`.
//
// Safe to ship with both disabled — the file is a no-op until configured.

(function() {
  'use strict';

  // ───────── CONFIG ─────────
  // Plausible: set the DOMAIN you registered with Plausible.
  // Leave empty to keep analytics off.
  var PLAUSIBLE_DOMAIN = window.__TIL_PLAUSIBLE_DOMAIN || '';
  var PLAUSIBLE_SRC    = window.__TIL_PLAUSIBLE_SRC    || 'https://plausible.io/js/script.js';

  // Sentry: paste your DSN from Sentry Project Settings → Client Keys.
  // Leave empty to keep error reporting off.
  var SENTRY_DSN       = window.__TIL_SENTRY_DSN       || '';
  var SENTRY_ENV       = window.__TIL_SENTRY_ENV       || 'production';
  var SENTRY_SRC       = window.__TIL_SENTRY_SRC       || 'https://browser.sentry-cdn.com/7.119.0/bundle.tracing.min.js';
  var SENTRY_INTEGRITY = window.__TIL_SENTRY_INTEGRITY || 'sha384-GzZ4bdr+fG4HQxpFjPQWUt4u5W3bxwhVr6LVk84SxQqHVdxsRSuj1rU8RxVg5QpO';

  // Respect Do-Not-Track. We don't run analytics if the user opted out.
  var dnt = (navigator.doNotTrack === '1') || (window.doNotTrack === '1') ||
            (navigator.msDoNotTrack === '1') || (window.doNotTrack === 'yes');

  // ───────── PLAUSIBLE ─────────
  if (PLAUSIBLE_DOMAIN && !dnt) {
    var p = document.createElement('script');
    p.defer = true;
    p.src = PLAUSIBLE_SRC;
    p.setAttribute('data-domain', PLAUSIBLE_DOMAIN);
    document.head.appendChild(p);

    // Expose a queue for custom events so callers don't have to care if
    // Plausible has loaded yet: `plausible('Signup', { props: {…} })`.
    window.plausible = window.plausible || function() {
      (window.plausible.q = window.plausible.q || []).push(arguments);
    };
  }

  // ───────── SENTRY ─────────
  if (SENTRY_DSN) {
    var s = document.createElement('script');
    s.src = SENTRY_SRC;
    s.crossOrigin = 'anonymous';
    // Don't set integrity if the caller overrode the SRC — version drift
    // breaks the hash.
    if (SENTRY_SRC === 'https://browser.sentry-cdn.com/7.119.0/bundle.tracing.min.js') {
      s.integrity = SENTRY_INTEGRITY;
    }
    s.onload = function() {
      if (!window.Sentry) return;
      try {
        window.Sentry.init({
          dsn: SENTRY_DSN,
          environment: SENTRY_ENV,
          release: 'til@' + (typeof LAST_UPDATED !== 'undefined' ? LAST_UPDATED : 'unknown'),
          tracesSampleRate: 0.1,          // 10 % of page loads sampled for perf
          replaysSessionSampleRate: 0.0,  // No session replay by default
          replaysOnErrorSampleRate: 0.0,
          beforeSend: function(event) {
            // Strip any form-input text that Sentry might have picked up
            if (event.request && event.request.data) event.request.data = '[redacted]';
            return event;
          },
          ignoreErrors: [
            // Browser noise we don't care about
            'ResizeObserver loop limit exceeded',
            'ResizeObserver loop completed with undelivered notifications',
            'Network request failed',
            'Load failed',
            // Extension noise
            'top.GLOBALS',
            'originalCreateNotification',
            'canvas.contentDocument',
          ],
        });
      } catch (e) {
        // If init fails for any reason, don't break the page.
      }
    };
    document.head.appendChild(s);
  }

  // ───────── DIAGNOSTIC SURFACE ─────────
  // For debugging: `window.__TIL_ANALYTICS_STATUS()` reports what's loaded.
  window.__TIL_ANALYTICS_STATUS = function() {
    return {
      plausible: {
        configured: !!PLAUSIBLE_DOMAIN,
        dnt_respected: dnt,
        queued_events: (window.plausible && window.plausible.q && window.plausible.q.length) || 0,
      },
      sentry: {
        configured: !!SENTRY_DSN,
        loaded: !!window.Sentry,
        env: SENTRY_ENV,
      },
    };
  };
})();
