/*
 * The Innovators League — runtime config
 *
 * Loaded BEFORE analytics.js on every page. Sets the globals that analytics.js
 * checks before activating Plausible (page analytics) and Sentry (error
 * reporting).
 *
 * --- WHEN YOU'RE READY TO ENABLE EITHER ONE ---
 *   1. Plausible:
 *        Sign up at https://plausible.io and add the site
 *        "innovatorsleague.com" (or whatever your final domain is).
 *        Then uncomment the PLAUSIBLE_DOMAIN line below and set it to that
 *        exact domain string.
 *
 *   2. Sentry:
 *        Create a project at https://sentry.io, copy the DSN from
 *        Project Settings → Client Keys (DSN), and paste it below.
 *
 * Both are OFF by default. Leaving the constants empty is safe — no scripts
 * load, no analytics fire, no errors are reported.
 *
 * SECURITY NOTE: Both DSN and Plausible domain are public values intended
 * to live in client-side JS. They are not secrets.
 */
(function () {
  'use strict';

  // ─── Plausible (page analytics) ─────────────────────────────────────────
  // Uncomment + set when ready.
  // window.__TIL_PLAUSIBLE_DOMAIN = 'innovatorsleague.com';

  // ─── Sentry (error reporting) ───────────────────────────────────────────
  // Uncomment + set when ready.
  // window.__TIL_SENTRY_DSN = 'https://YOUR_KEY@oXXXXXX.ingest.sentry.io/XXXXXXX';
  // window.__TIL_SENTRY_ENV = 'production';

  // ─── Self-diagnostic ────────────────────────────────────────────────────
  // For debugging in the console: `__TIL_CONFIG()`
  window.__TIL_CONFIG = function () {
    return {
      plausible_domain: window.__TIL_PLAUSIBLE_DOMAIN || '(unset)',
      sentry_dsn:       window.__TIL_SENTRY_DSN ? '(set)' : '(unset)',
      sentry_env:       window.__TIL_SENTRY_ENV || '(default: production)',
      built:            '2026-05-14'
    };
  };
})();
