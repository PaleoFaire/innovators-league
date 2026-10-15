#!/usr/bin/env node
/* Build data/nav_counts.json — the live numbers shown in the navigation panels
   and on the homepage tool cards.

   Why a separate file: the nav is on every page, but most pages do not load
   data.js (4 MB) or the other data bundles. nav.js fetches this 400-byte JSON
   instead and lets in-page globals override it when a page has fresher data.

   Run after the daily sync (it is wired into daily-data-sync.yml):
     node scripts/build_nav_counts.js
*/
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'data', 'nav_counts.json');

function loadGlobals(file, names) {
  const ctx = { window: {}, console: { log() {}, warn() {}, error() {} } };
  vm.createContext(ctx);
  const src = fs.readFileSync(path.join(ROOT, file), 'utf8');
  const tail = names.map(n =>
    `globalThis.__out_${n} = (typeof ${n} !== 'undefined') ? ${n} : window.${n};`).join('\n');
  try {
    vm.runInContext(src + '\n;' + tail, ctx, { timeout: 30000, filename: file });
  } catch (e) {
    console.warn(`[nav_counts] ${file}: ${e.message}`);
    return {};
  }
  const out = {};
  names.forEach(n => { out[n] = ctx['__out_' + n]; });
  return out;
}

const counts = { generated_at: new Date().toISOString() };

// ── data.js: companies, countries, sectors, IL30, investors ──
try {
  const d = loadGlobals('data.js', ['COMPANIES', 'SECTORS', 'INNOVATORS_LEAGUE_30', 'LAST_UPDATED']);
  if (Array.isArray(d.COMPANIES)) {
    counts.companies = d.COMPANIES.length;
    counts.countries = new Set(d.COMPANIES.map(c => c.country).filter(Boolean)).size;
    counts.investors = new Set(d.COMPANIES.flatMap(c => c.investors || []).filter(Boolean)).size;
  }
  if (d.SECTORS) counts.sectors = Object.keys(d.SECTORS).length;
  if (Array.isArray(d.INNOVATORS_LEAGUE_30)) counts.il30 = d.INNOVATORS_LEAGUE_30.length;
  if (d.LAST_UPDATED) counts.database_updated = d.LAST_UPDATED;
} catch (e) { console.warn('[nav_counts] data.js skipped: ' + e.message); }

// ── data/wire_auto.js: The Wire + Radar ──
try {
  const w = loadGlobals('data/wire_auto.js', ['WIRE', 'RADAR']);
  if (w.WIRE && w.WIRE.stats) {
    counts.wire_events_week = w.WIRE.stats.events_this_week;
    counts.wire_events = w.WIRE.stats.events;
    counts.companies_moved = w.WIRE.stats.companies_moved;
    counts.wire_generated_at = w.WIRE.generated_at;
  }
  if (w.RADAR && w.RADAR.stats) {
    counts.radar_30d = w.RADAR.stats.filings_30d;
    counts.radar_offered_30d_fmt = w.RADAR.stats.offered_30d_fmt;
  }
} catch (e) { console.warn('[nav_counts] wire skipped: ' + e.message); }

// ── data/jobs_auto.js: open roles ──
try {
  const j = loadGlobals('data/jobs_auto.js', ['JOBS_STATS', 'JOBS_DATA']);
  if (j.JOBS_STATS && j.JOBS_STATS.totalJobs) {
    counts.jobs = j.JOBS_STATS.totalJobs;
    counts.jobs_companies = j.JOBS_STATS.companiesHiring;
    counts.jobs_updated = j.JOBS_STATS.lastUpdated;
  } else if (Array.isArray(j.JOBS_DATA)) {
    counts.jobs = j.JOBS_DATA.length;
  }
} catch (e) { console.warn('[nav_counts] jobs skipped: ' + e.message); }

// ── data/company_announcements_auto.js: Raised (announcements in the last 30 days) ──
try {
  const a = loadGlobals('data/company_announcements_auto.js', ['COMPANY_ANNOUNCEMENTS_AUTO']);
  const A = a.COMPANY_ANNOUNCEMENTS_AUTO;
  if (A && Array.isArray(A.results)) {
    let n = 0;
    A.results.forEach(r => (r.hits || []).forEach(h => {
      if (h && h.title && h.age_days != null && h.age_days <= 30) n++;
    }));
    counts.rounds_30d = n;
    counts.rounds_generated_at = A.generated_at;
  }
} catch (e) { console.warn('[nav_counts] announcements skipped: ' + e.message); }

// ── data/catalyst_calendar.json: dated catalysts ahead ──
try {
  const cal = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'catalyst_calendar.json'), 'utf8'));
  const today = new Date().toISOString().slice(0, 10);
  const events = Array.isArray(cal.events) ? cal.events : [];
  counts.catalysts_upcoming = events.filter(e => {
    const d = e.date || e.eventDate || e.expectedDate || '';
    return typeof d === 'string' && d.slice(0, 10) >= today;
  }).length;
  counts.catalysts_total = events.length;
} catch (e) { console.warn('[nav_counts] catalysts skipped: ' + e.message); }

// ── data/changelog_auto.js: this week's additions ──
try {
  const c = loadGlobals('data/changelog_auto.js', ['CHANGELOG_WEEKLY']);
  if (c.CHANGELOG_WEEKLY) {
    counts.changelog_added = (c.CHANGELOG_WEEKLY.added || []).length;
    counts.changelog_generated = c.CHANGELOG_WEEKLY.generated;
  }
} catch (e) { console.warn('[nav_counts] changelog skipped: ' + e.message); }

fs.writeFileSync(OUT, JSON.stringify(counts, null, 2) + '\n');
console.log('[nav_counts] wrote ' + path.relative(ROOT, OUT));
console.log(JSON.stringify(counts));
