// ═══════════════════════════════════════════════════════════════════════════════
// THE INNOVATORS LEAGUE — Authentication & Access Gating Module
// Powered by Supabase. All pages include this file before app.js.
// ═══════════════════════════════════════════════════════════════════════════════

const TILAuth = (function() {
  'use strict';

  // ── Supabase Configuration ──
  // Replace these with your Supabase project credentials
  const SUPABASE_URL = 'https://imxrdesbozbxmlffewyr.supabase.co';
  const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlteHJkZXNib3pieG1sZmZld3lyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE0NTM2MDQsImV4cCI6MjA4NzAyOTYwNH0.ULUcvwaU2d-gyL_k6lcRziIEsndnDLGtMkV61Q9Knq0';

  let supabaseClient = null;
  let currentUser = null;
  let currentProfile = null;
  let isReady = false;
  let authReadyCallbacks = [];

  // ── Premium section IDs to gate on index.html ──
  const GATED_SECTION_IDS = [
    'innovator-scores',
    'gov-contracts',
    'patent-intel',
    'predictive-scores',
    'portfolio-builder',
    'network-graph',
    'pro-watchlist',
    'historical-tracking'
  ];

  // ═══ INITIALIZATION ═══

  function init() {
    if (typeof supabase === 'undefined') {
      console.warn('[TILAuth] Supabase SDK not loaded — running in demo mode');
      setReady(null);
      return;
    }

    if (SUPABASE_URL === 'YOUR_SUPABASE_URL') {
      console.warn('[TILAuth] Supabase not configured — running in demo mode');
      setReady(null);
      return;
    }

    try {
      supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

      supabaseClient.auth.onAuthStateChange((event, session) => {
        currentUser = session?.user || null;

        if (currentUser) {
          loadProfile(currentUser.id);
        } else {
          currentProfile = null;
        }

        updateNavAuthState();
        updateGating();

        if (!isReady) {
          setReady(currentUser);
        }

        // Trigger custom event for other scripts
        window.dispatchEvent(new CustomEvent('til-auth-change', {
          detail: { user: currentUser, event: event }
        }));
      });

      // Check for auth redirect (e.g., ?auth=required)
      const params = new URLSearchParams(window.location.search);
      if (params.get('auth') === 'required') {
        setTimeout(() => showAuthModal(), 500);
        // Clean URL
        params.delete('auth');
        params.delete('redirect');
        const clean = params.toString();
        const url = window.location.pathname + (clean ? '?' + clean : '');
        window.history.replaceState({}, '', url);
      }

    } catch (e) {
      console.error('[TILAuth] Init error:', e);
      setReady(null);
    }
  }

  function setReady(user) {
    isReady = true;
    authReadyCallbacks.forEach(cb => {
      try { cb(user); } catch(e) { console.error('[TILAuth] Ready callback error:', e); }
    });
    authReadyCallbacks = [];
  }

  // ═══ AUTH METHODS ═══

  async function signIn(email, password) {
    if (!supabaseClient) return { error: { message: 'Supabase not configured. Contact support.' } };
    const { data, error } = await supabaseClient.auth.signInWithPassword({ email, password });
    if (error) return { error };
    return { data };
  }

  async function signUp(email, password) {
    if (!supabaseClient) return { error: { message: 'Supabase not configured. Contact support.' } };
    const { data, error } = await supabaseClient.auth.signUp({ email, password });
    if (error) return { error };
    return { data };
  }

  async function signInWithGoogle() {
    if (!supabaseClient) return { error: { message: 'Supabase not configured.' } };
    const { data, error } = await supabaseClient.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin + window.location.pathname }
    });
    return { data, error };
  }

  async function signOut() {
    if (!supabaseClient) return;
    await supabaseClient.auth.signOut();
    currentUser = null;
    currentProfile = null;
    updateNavAuthState();
    updateGating();
    // Re-render company grid if on main page
    if (typeof renderCompanyGrid === 'function') renderCompanyGrid();
  }

  async function resetPassword(email) {
    if (!supabaseClient) return { error: { message: 'Supabase not configured.' } };
    const { data, error } = await supabaseClient.auth.resetPasswordForEmail(email, {
      redirectTo: window.location.origin + '/index.html'
    });
    return { data, error };
  }

  // ═══ PROFILE ═══

  async function loadProfile(userId) {
    if (!supabaseClient) return;
    try {
      const { data, error } = await supabaseClient
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .single();
      if (!error && data) {
        currentProfile = data;
        // Update last login
        supabaseClient.from('profiles').update({ last_login: new Date().toISOString() }).eq('id', userId);
      }
    } catch (e) {
      console.warn('[TILAuth] Profile load error:', e);
    }
  }

  // ═══ STATE HELPERS ═══

  function isLoggedIn() {
    return !!currentUser;
  }

  function getUser() {
    return currentUser;
  }

  function getProfile() {
    return currentProfile;
  }

  function getClient() {
    return supabaseClient;
  }

  function onReady(callback) {
    if (isReady) {
      callback(currentUser);
    } else {
      authReadyCallbacks.push(callback);
    }
  }

  // ═══ NAV AUTH STATE ═══

  function updateNavAuthState() {
    const signInArea = document.getElementById('nav-auth');
    const userArea = document.getElementById('nav-user');
    const userEmail = document.getElementById('nav-user-email');

    if (!signInArea || !userArea) return;

    if (currentUser) {
      signInArea.style.display = 'none';
      userArea.style.display = 'flex';
      if (userEmail) {
        const displayName = currentProfile?.display_name || currentUser.email?.split('@')[0] || 'Member';
        userEmail.textContent = displayName;
      }
    } else {
      signInArea.style.display = 'flex';
      userArea.style.display = 'none';
    }
  }

  // ═══ SECTION GATING ═══

  function updateGating() {
    GATED_SECTION_IDS.forEach(id => {
      const section = document.getElementById(id);
      if (!section) return;

      if (currentUser) {
        section.classList.remove('section-gated');
        // Remove gate CTA if it exists
        const cta = section.querySelector('.section-gate-cta');
        if (cta) cta.remove();
      } else {
        if (!section.classList.contains('section-gated')) {
          section.classList.add('section-gated');
          // Add gate CTA overlay if not already present
          if (!section.querySelector('.section-gate-cta')) {
            const ctaDiv = document.createElement('div');
            ctaDiv.className = 'section-gate-cta';
            ctaDiv.innerHTML = `
              <div class="gate-cta-content">
                <span class="gate-lock-icon">&#128274;</span>
                <h3>Sign in to access this intelligence</h3>
                <p>Create a free account to unlock the full Innovators League database.</p>
                <button class="gate-cta-btn" onclick="TILAuth.showAuthModal()">Sign In Free</button>
              </div>
            `;
            section.appendChild(ctaDiv);
          }
        }
      }
    });

    // Also re-render company grid if function exists and we're on main page
    if (typeof renderCompanyGrid === 'function' && document.getElementById('companies-grid')) {
      renderCompanyGrid();
    }

    // Load saved searches if logged in
    if (currentUser && typeof loadSavedSearches === 'function') {
      loadSavedSearches();
    }
    if (currentUser && typeof loadAlertPreferences === 'function') {
      loadAlertPreferences();
    }
  }

  // ═══ AUTH MODAL ═══

  function showAuthModal() {
    const overlay = document.getElementById('auth-modal-overlay');
    if (overlay) {
      overlay.style.display = 'flex';
      document.body.style.overflow = 'hidden';
      // Focus email input
      setTimeout(() => {
        const emailInput = document.getElementById('auth-email');
        if (emailInput) emailInput.focus();
      }, 100);
    } else {
      // Auth modal not on this page — redirect to main page with auth prompt
      window.location.href = 'index.html?auth=required';
    }
  }

  function hideAuthModal() {
    const overlay = document.getElementById('auth-modal-overlay');
    if (overlay) {
      overlay.style.display = 'none';
      document.body.style.overflow = '';
      clearAuthError();
    }
  }

  function showAuthError(msg) {
    const errorEl = document.getElementById('auth-error');
    if (errorEl) {
      errorEl.textContent = msg;
      errorEl.style.display = 'block';
    }
  }

  function clearAuthError() {
    const errorEl = document.getElementById('auth-error');
    if (errorEl) {
      errorEl.textContent = '';
      errorEl.style.display = 'none';
    }
  }

  function showAuthSuccess(msg) {
    const errorEl = document.getElementById('auth-error');
    if (errorEl) {
      errorEl.textContent = msg;
      errorEl.style.display = 'block';
      errorEl.style.color = '#22c55e';
      errorEl.style.borderColor = 'rgba(34,197,94,0.3)';
    }
  }

  // ═══ AUTH MODAL EVENT HANDLERS ═══

  function initAuthModal() {
    // Close button
    const closeBtn = document.getElementById('auth-modal-close');
    if (closeBtn) closeBtn.addEventListener('click', hideAuthModal);

    // Overlay click to close
    const overlay = document.getElementById('auth-modal-overlay');
    if (overlay) {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) hideAuthModal();
      });
    }

    // Tab switching
    document.querySelectorAll('.auth-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const tabName = tab.dataset.tab;
        document.getElementById('auth-login-panel').style.display = tabName === 'login' ? 'block' : 'none';
        document.getElementById('auth-signup-panel').style.display = tabName === 'signup' ? 'block' : 'none';
        clearAuthError();
      });
    });

    // Login form
    const loginForm = document.getElementById('auth-login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAuthError();
        const email = document.getElementById('auth-email').value.trim();
        const password = document.getElementById('auth-password').value;
        if (!email || !password) { showAuthError('Please enter email and password.'); return; }

        const btn = loginForm.querySelector('.auth-submit-btn');
        btn.textContent = 'Signing in...';
        btn.disabled = true;

        const { error } = await signIn(email, password);
        btn.textContent = 'Sign In';
        btn.disabled = false;

        if (error) {
          showAuthError(error.message || 'Sign in failed. Check your credentials.');
        } else {
          hideAuthModal();
        }
      });
    }

    // Signup form
    const signupForm = document.getElementById('auth-signup-form');
    if (signupForm) {
      signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAuthError();
        const email = document.getElementById('auth-signup-email').value.trim();
        const password = document.getElementById('auth-signup-password').value;
        const confirmPw = document.getElementById('auth-signup-confirm').value;

        if (!email || !password) { showAuthError('Please enter email and password.'); return; }
        if (password.length < 6) { showAuthError('Password must be at least 6 characters.'); return; }
        if (password !== confirmPw) { showAuthError('Passwords do not match.'); return; }

        const btn = signupForm.querySelector('.auth-submit-btn');
        btn.textContent = 'Creating account...';
        btn.disabled = true;

        const { data, error } = await signUp(email, password);
        btn.textContent = 'Create Account';
        btn.disabled = false;

        if (error) {
          showAuthError(error.message || 'Sign up failed. Try a different email.');
        } else {
          // Check if email confirmation is required
          if (data?.user?.identities?.length === 0) {
            showAuthError('An account with this email already exists.');
          } else {
            showAuthSuccess('Account created! Check your email to confirm, then sign in.');
            // Switch to login tab after brief delay
            setTimeout(() => {
              document.querySelector('.auth-tab[data-tab="login"]')?.click();
            }, 3000);
          }
        }
      });
    }

    // Google OAuth button
    const googleBtn = document.getElementById('auth-google-btn');
    if (googleBtn) {
      googleBtn.addEventListener('click', async () => {
        clearAuthError();
        const { error } = await signInWithGoogle();
        if (error) showAuthError(error.message || 'Google sign-in failed.');
      });
    }

    // Forgot password link
    const forgotLink = document.getElementById('auth-forgot-password');
    if (forgotLink) {
      forgotLink.addEventListener('click', async (e) => {
        e.preventDefault();
        clearAuthError();
        const email = document.getElementById('auth-email').value.trim();
        if (!email) { showAuthError('Enter your email above, then click Forgot Password.'); return; }
        const { error } = await resetPassword(email);
        if (error) {
          showAuthError(error.message);
        } else {
          showAuthSuccess('Password reset email sent! Check your inbox.');
        }
      });
    }

    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const overlay = document.getElementById('auth-modal-overlay');
        if (overlay && overlay.style.display === 'flex') hideAuthModal();
      }
    });
  }

  // ═══ BOOTSTRAP ═══

  // Auto-init when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      init();
      initAuthModal();
    });
  } else {
    init();
    initAuthModal();
  }

  // ═══ PUBLIC API ═══

  return {
    init,
    signIn,
    signUp,
    signInWithGoogle,
    signOut,
    resetPassword,
    isLoggedIn,
    getUser,
    getProfile,
    getClient,
    onReady,
    showAuthModal,
    hideAuthModal,
    updateGating,
    updateNavAuthState
  };

})();
