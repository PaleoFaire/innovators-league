/*
 * Substack Email Capture — The Innovators League
 *
 * Renders a custom-branded email capture form that posts directly to the
 * Substack subscription page with the email pre-filled. Validates locally
 * and fires a Plausible 'Subscribe Submitted' event when analytics is on.
 *
 * Usage in HTML:
 *   <div class="til-capture"
 *        data-headline="Get the Frontier Weekly"
 *        data-subhead="..."
 *        data-cta="Subscribe Free"></div>
 *
 * Add the script before </body>:
 *   <script src="substack-capture.js?v=20260501"></script>
 */
(function () {
  'use strict';

  var SUBSTACK_BASE = 'https://rationaloptimistsociety.substack.com/subscribe';
  // Track which slots have been rendered so we can hot-reload safely
  var rendered = new WeakSet();

  function injectStyles() {
    if (document.getElementById('til-capture-styles')) return;
    var style = document.createElement('style');
    style.id = 'til-capture-styles';
    style.textContent = '\
      .til-capture {\
        background: linear-gradient(135deg, rgba(34,197,94,0.06), rgba(34,197,94,0.01));\
        border: 1px solid rgba(34,197,94,0.18);\
        border-radius: 14px;\
        padding: 28px 28px 26px;\
        margin: 40px auto;\
        max-width: 720px;\
        text-align: center;\
        font-family: "Inter", system-ui, -apple-system, sans-serif;\
      }\
      .til-capture-eyebrow {\
        display: inline-block;\
        font-size: 11px;\
        letter-spacing: 0.16em;\
        text-transform: uppercase;\
        color: #4ade80;\
        font-weight: 700;\
        margin-bottom: 12px;\
      }\
      .til-capture-headline {\
        font-size: clamp(22px, 3vw, 28px);\
        font-weight: 800;\
        margin: 0 0 8px;\
        color: #e6edf3;\
        letter-spacing: -0.01em;\
      }\
      .til-capture-sub {\
        font-size: 14px;\
        line-height: 1.55;\
        color: #8b949e;\
        margin: 0 auto 22px;\
        max-width: 480px;\
      }\
      .til-capture-form {\
        display: flex;\
        gap: 8px;\
        max-width: 480px;\
        margin: 0 auto;\
      }\
      .til-capture-input {\
        flex: 1;\
        padding: 12px 16px;\
        background: rgba(255,255,255,0.04);\
        border: 1px solid rgba(255,255,255,0.12);\
        border-radius: 8px;\
        color: #e6edf3;\
        font-size: 14px;\
        font-family: inherit;\
        outline: none;\
        transition: border-color 140ms ease;\
      }\
      .til-capture-input:focus { border-color: #22c55e; }\
      .til-capture-input::placeholder { color: #6e7681; }\
      .til-capture-btn {\
        padding: 12px 22px;\
        background: #22c55e;\
        color: #0d1117;\
        font-weight: 700;\
        font-size: 13px;\
        letter-spacing: 0.02em;\
        border: none;\
        border-radius: 8px;\
        cursor: pointer;\
        font-family: inherit;\
        transition: all 140ms ease;\
        white-space: nowrap;\
      }\
      .til-capture-btn:hover { background: #4ade80; transform: translateY(-1px); }\
      .til-capture-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }\
      .til-capture-note {\
        font-size: 11px;\
        color: #6e7681;\
        margin-top: 14px;\
      }\
      .til-capture-error {\
        color: #ef4444;\
        font-size: 12px;\
        margin-top: 10px;\
      }\
      .til-capture-success {\
        color: #4ade80;\
        font-size: 14px;\
        font-weight: 600;\
        margin-top: 16px;\
        animation: tilFadeIn 240ms ease;\
      }\
      @keyframes tilFadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }\
      @media (max-width: 540px) {\
        .til-capture { padding: 22px 18px; margin: 28px auto; }\
        .til-capture-form { flex-direction: column; }\
        .til-capture-btn { width: 100%; }\
      }\
    ';
    document.head.appendChild(style);
  }

  function isValidEmail(v) {
    return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v);
  }

  function track(eventName, props) {
    try {
      if (typeof window.plausible === 'function') {
        window.plausible(eventName, props ? { props: props } : undefined);
      }
    } catch (e) {}
  }

  function render(el) {
    if (rendered.has(el)) return;
    rendered.add(el);

    var headline = el.getAttribute('data-headline') || 'Get the Frontier Weekly';
    var subhead  = el.getAttribute('data-subhead') ||
      'Factory visits, founder calls, and deal signals that aren’t in any LLM. Free, every Sunday.';
    var eyebrow  = el.getAttribute('data-eyebrow') || 'STEPHEN’S WEEKLY';
    var cta      = el.getAttribute('data-cta') || 'Subscribe Free';
    var note     = el.getAttribute('data-note') || 'Join 50,000+ investors and founders. No spam — unsubscribe anytime.';

    el.innerHTML =
      '<div class="til-capture-eyebrow">' + eyebrow + '</div>' +
      '<h3 class="til-capture-headline">' + headline + '</h3>' +
      '<p class="til-capture-sub">' + subhead + '</p>' +
      '<form class="til-capture-form" novalidate>' +
        '<input type="email" class="til-capture-input" placeholder="you@company.com" required autocomplete="email" aria-label="Email address">' +
        '<button type="submit" class="til-capture-btn">' + cta + '</button>' +
      '</form>' +
      '<div class="til-capture-note">' + note + '</div>';

    var form  = el.querySelector('form');
    var input = el.querySelector('input');
    var btn   = el.querySelector('button');

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var v = (input.value || '').trim();

      // Clear any prior error
      var prevErr = el.querySelector('.til-capture-error');
      if (prevErr) prevErr.remove();

      if (!isValidEmail(v)) {
        var err = document.createElement('div');
        err.className = 'til-capture-error';
        err.textContent = 'Please enter a valid email.';
        el.appendChild(err);
        input.focus();
        return;
      }

      // Track + redirect to Substack with email pre-filled
      track('Subscribe Submitted', { source: location.pathname || '/' });

      btn.disabled = true;
      btn.textContent = 'Redirecting…';

      // Show success message briefly before redirect (so the user knows it worked)
      var msg = document.createElement('div');
      msg.className = 'til-capture-success';
      msg.textContent = '✓ Sending you to Substack to confirm…';
      el.appendChild(msg);

      var url = SUBSTACK_BASE + '?email=' + encodeURIComponent(v);
      // Open in same tab — Substack flow expects the user to confirm
      setTimeout(function () { window.location.href = url; }, 600);
    });
  }

  function initAll() {
    injectStyles();
    var slots = document.querySelectorAll('.til-capture');
    for (var i = 0; i < slots.length; i++) render(slots[i]);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  // Expose so dynamically-added slots can be rendered
  window.TILSubstackCapture = { render: render, initAll: initAll };
})();
