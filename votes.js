// ═══════════════════════════════════════════════════════════════════════════════
// THE INNOVATORS LEAGUE — Community Upvotes
// ═══════════════════════════════════════════════════════════════════════════════
//
// Lets logged-in users upvote any company in the database. Vote counts drive
// a "Community Picks" sort and a live badge on every company card.
//
// Backend: Supabase table `company_votes` + view `company_vote_counts`.
//          See supabase/migrations/20260422_company_votes.sql. Before that
//          migration runs, every call in here fails silently and the
//          upvote UI simply doesn't render — zero risk to ship ahead of it.
//
// Architecture:
//   • One in-memory cache of the full counts map, refreshed every 60s or
//     when the user casts a vote (optimistic update).
//   • One in-memory set of the current user's own voted companies.
//   • Graceful no-op when Supabase/auth isn't wired on a page.
//
// Public API (window.TILVotes):
//   getCount(name)            → integer
//   hasVoted(name)            → boolean
//   getTopVoted(limit=20)     → [{name, count}, ...]
//   toggle(name)              → Promise<{count, voted}>
//   refresh()                 → Promise<void>  (forces a reload)
//   onChange(cb)              → subscribe to count-map updates
//   isReady()                 → bool, true once first fetch completed

(function() {
  'use strict';

  var countsByCompany = {};     // { "Anduril Industries": 42, ... }
  var myVotes = new Set();      // Set<string> — the current user's voted company names
  var ready = false;
  var lastFetch = 0;
  var REFRESH_MS = 60 * 1000;   // 60 s cache TTL
  var listeners = [];
  var inFlightFetch = null;

  function getClient() {
    if (typeof TILAuth === 'undefined' || !TILAuth.getClient) return null;
    return TILAuth.getClient();
  }

  // ─── INTERNAL ─────────────────────────────────────────────────────────────

  async function fetchCounts() {
    var client = getClient();
    if (!client) return;
    try {
      var { data, error } = await client
        .from('company_vote_counts')
        .select('company_name, vote_count');
      if (error) {
        // Most common failure mode: the migration hasn't been run yet.
        // Log once in the console for dev visibility but don't blow up.
        if (!fetchCounts._warned) {
          console.warn('[TILVotes] Count fetch failed — has the SQL migration run?', error.message);
          fetchCounts._warned = true;
        }
        return;
      }
      var map = {};
      (data || []).forEach(function(row) {
        map[row.company_name] = row.vote_count;
      });
      countsByCompany = map;
      lastFetch = Date.now();
      ready = true;
      notify();
    } catch (e) {
      // Network or schema issue; keep counts at whatever we had.
    }
  }

  async function fetchMyVotes() {
    var client = getClient();
    if (!client || typeof TILAuth === 'undefined' || !TILAuth.isLoggedIn()) {
      myVotes = new Set();
      return;
    }
    var user = TILAuth.getUser();
    if (!user) { myVotes = new Set(); return; }
    try {
      var { data, error } = await client
        .from('company_votes')
        .select('company_name')
        .eq('user_id', user.id);
      if (error) return;
      myVotes = new Set((data || []).map(function(r) { return r.company_name; }));
      notify();
    } catch (e) { /* silent */ }
  }

  async function loadAll() {
    if (inFlightFetch) return inFlightFetch;
    inFlightFetch = Promise.all([fetchCounts(), fetchMyVotes()])
      .finally(function() { inFlightFetch = null; });
    return inFlightFetch;
  }

  function notify() {
    listeners.forEach(function(cb) {
      try { cb({ counts: countsByCompany, myVotes: myVotes }); } catch (e) {}
    });
  }

  // Refresh on tab refocus (handles "user voted on another tab" case)
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible' && Date.now() - lastFetch > REFRESH_MS) {
      loadAll();
    }
  });

  // ─── PUBLIC API ───────────────────────────────────────────────────────────

  function getCount(name) {
    return (countsByCompany && countsByCompany[name]) || 0;
  }

  function hasVoted(name) {
    return myVotes.has(name);
  }

  function getTopVoted(limit) {
    limit = limit || 20;
    return Object.keys(countsByCompany)
      .map(function(name) { return { name: name, count: countsByCompany[name] }; })
      .filter(function(r) { return r.count > 0; })
      .sort(function(a, b) { return b.count - a.count; })
      .slice(0, limit);
  }

  async function toggle(name) {
    if (!name) return { count: 0, voted: false, error: 'No company name' };
    var client = getClient();
    if (!client) return { count: getCount(name), voted: false, error: 'Auth not ready' };
    if (typeof TILAuth === 'undefined' || !TILAuth.isLoggedIn()) {
      // Prompt sign-in
      if (TILAuth && TILAuth.showAuthModal) TILAuth.showAuthModal();
      return { count: getCount(name), voted: false, error: 'Not logged in' };
    }
    var user = TILAuth.getUser();
    if (!user) return { count: getCount(name), voted: false, error: 'No user session' };

    var wasVoted = myVotes.has(name);
    // Optimistic update — flip the UI before the network returns
    if (wasVoted) {
      myVotes.delete(name);
      countsByCompany[name] = Math.max(0, (countsByCompany[name] || 1) - 1);
    } else {
      myVotes.add(name);
      countsByCompany[name] = (countsByCompany[name] || 0) + 1;
    }
    notify();

    try {
      if (wasVoted) {
        var { error } = await client
          .from('company_votes')
          .delete()
          .eq('user_id', user.id)
          .eq('company_name', name);
        if (error) throw error;
      } else {
        var { error: insertError } = await client
          .from('company_votes')
          .insert({ user_id: user.id, company_name: name });
        // 23505 = unique_violation (user already voted). Treat as success.
        if (insertError && insertError.code !== '23505') throw insertError;
      }
      return { count: countsByCompany[name] || 0, voted: !wasVoted };
    } catch (e) {
      // Roll back optimistic update
      if (wasVoted) {
        myVotes.add(name);
        countsByCompany[name] = (countsByCompany[name] || 0) + 1;
      } else {
        myVotes.delete(name);
        countsByCompany[name] = Math.max(0, (countsByCompany[name] || 1) - 1);
      }
      notify();
      return { count: countsByCompany[name] || 0, voted: wasVoted, error: e.message || 'Vote failed' };
    }
  }

  function onChange(cb) {
    if (typeof cb !== 'function') return function(){};
    listeners.push(cb);
    return function unsubscribe() {
      listeners = listeners.filter(function(f) { return f !== cb; });
    };
  }

  function isReady() { return ready; }

  async function refresh() { return loadAll(); }

  // ─── INIT ─────────────────────────────────────────────────────────────────

  function init() {
    if (typeof TILAuth === 'undefined') return; // no auth on this page
    if (TILAuth.onReady) {
      TILAuth.onReady(function() { loadAll(); });
    } else {
      loadAll();
    }
    // Also refresh when the auth state changes (sign-in / sign-out)
    var client = getClient();
    if (client && client.auth && client.auth.onAuthStateChange) {
      client.auth.onAuthStateChange(function() { loadAll(); });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.TILVotes = {
    getCount: getCount,
    hasVoted: hasVoted,
    getTopVoted: getTopVoted,
    toggle: toggle,
    refresh: refresh,
    onChange: onChange,
    isReady: isReady
  };
})();
