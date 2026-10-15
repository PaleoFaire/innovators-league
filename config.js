/*
 * The ROS Innovators League — runtime config
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
  // Set on 15 Oct 2026 with the homepage/nav redesign so tool-card and
  // nav-item clicks can be counted (nav.js fires "Nav Click", "Nav Open",
  // "Tool Click" and "Door Click" custom events; substack-capture.js fires
  // "Subscribe Submitted").
  //
  // NOTHING IS RECORDED UNTIL STEPHEN CREATES THE SITE IN PLAUSIBLE:
  // plausible.io → Sites → "+ Add a website" → domain exactly
  // "paleofaire.github.io" (the host visitors actually hit; GitHub Pages
  // serves the site at paleofaire.github.io/innovators-league). Then, under
  // the site's Goals, add the four custom events above so they show up as
  // goals. Until the site exists the Plausible script loads and its event
  // calls are rejected silently — no error, no data. Analytics.js also skips
  // everything for visitors with Do-Not-Track on. Change this string if the
  // site moves to innovatorsleague.com.
  window.__TIL_PLAUSIBLE_DOMAIN = 'paleofaire.github.io';

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
