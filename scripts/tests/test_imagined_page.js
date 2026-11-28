#!/usr/bin/env node
/*
 * Tests for the pure helpers in imagined.js (Who's Building It).
 *
 *     node scripts/tests/test_imagined_page.js
 *
 * No browser: imagined.js exports its helpers when loaded under Node. The last block loads
 * the real data/imagined_auto.js and checks the page can draw every theme from it.
 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..', '..');
const WB = require(path.join(ROOT, 'imagined.js'));

let passed = 0;
function test(name, fn) {
  try { fn(); passed++; } catch (e) { console.error('FAIL ' + name + '\n  ' + e.message); process.exitCode = 1; }
}

const T = (id, year, status, extra) => Object.assign({
  id, title: id.replace(/-/g, ' '), imagined: 'An idea.', status, status_label: status,
  fiction: { idea_id: 'r1', entry: 'Entry', work: 'Work ' + id, author: 'Author ' + id, year, url: 'https://notboring.com/sci-fi-idea-bank?idea=r1' },
  also: [], evidence: { date: '2025-01-01', publisher: 'Pub', url: 'https://example.org', fact: 'A fact.' },
  gap: 'A gap.', count: 0, companies: [], sectors: {}
}, extra || {});

const themes = [
  T('fusion-power', 1956, 'demonstrated', { count: 3, sectors: { 'Nuclear Energy': 3 }, companies: [{ n: 'Helion', s: 'helion' }] }),
  T('space-stations', 1869, 'built', { count: 2, sectors: { 'Space & Aerospace': 2 } }),
  T('stopping-aging', 1954, 'still_fiction', { count: 5, sectors: { 'Biotech & Health': 5 }, fiction: { idea_id: 'r1741', entry: 'Anti-Gerasone', work: 'Tomorrow and Tomorrow and Tomorrow', author: 'Kurt Vonnegut, Jr.', year: 1954, url: 'x' } }),
  T('air-taxis', 1911, 'demonstrated', { count: 3, sectors: { 'Drones & Autonomous': 3 } }),
  T('moon-bases', 1903, 'in_development', { count: 1, sectors: { 'Space & Aerospace': 1 }, gap: 'No one has stood on the Moon since 1972.' })
];

test('filter by status', () => {
  assert.deepStrictEqual(WB.filterThemes(themes, { status: 'demonstrated' }).map(t => t.id), ['fusion-power', 'air-taxis']);
});

test('filter by sector uses the companies in each theme', () => {
  assert.deepStrictEqual(WB.filterThemes(themes, { sector: 'Space & Aerospace' }).map(t => t.id), ['space-stations', 'moon-bases']);
});

test('search needs every word, ignores case and accents, and reads authors, companies and gaps', () => {
  assert.deepStrictEqual(WB.filterThemes(themes, { q: 'VONNEGUT' }).map(t => t.id), ['stopping-aging']);
  assert.deepStrictEqual(WB.filterThemes(themes, { q: 'hélion' }).map(t => t.id), ['fusion-power']);
  assert.deepStrictEqual(WB.filterThemes(themes, { q: 'moon 1972' }).map(t => t.id), ['moon-bases']);
  assert.deepStrictEqual(WB.filterThemes(themes, { q: 'moon 1999' }), []);
});

test('filters combine', () => {
  assert.deepStrictEqual(WB.filterThemes(themes, { status: 'demonstrated', sector: 'Nuclear Energy' }).map(t => t.id), ['fusion-power']);
});

test('sort modes', () => {
  assert.deepStrictEqual(WB.sortThemes(themes, 'oldest').map(t => t.fiction.year), [1869, 1903, 1911, 1954, 1956]);
  assert.deepStrictEqual(WB.sortThemes(themes, 'newest').map(t => t.fiction.year), [1956, 1954, 1911, 1903, 1869]);
  assert.deepStrictEqual(WB.sortThemes(themes, 'companies').map(t => t.id), ['stopping-aging', 'air-taxis', 'fusion-power', 'space-stations', 'moon-bases']);
  assert.deepStrictEqual(WB.sortThemes(themes, 'status').map(t => t.status), ['built', 'demonstrated', 'demonstrated', 'in_development', 'still_fiction']);
  assert.deepStrictEqual(WB.sortThemes(themes, 'nonsense').map(t => t.fiction.year), [1869, 1903, 1911, 1954, 1956]);
});

test('sorting does not change the input', () => {
  const before = themes.map(t => t.id).join();
  WB.sortThemes(themes, 'az');
  assert.strictEqual(themes.map(t => t.id).join(), before);
});

test('dates', () => {
  assert.strictEqual(WB.formatDate('2025-04-07'), '7 Apr 2025');
  assert.strictEqual(WB.formatDate('2016-10'), 'Oct 2016');
  assert.strictEqual(WB.formatDate('2001'), '2001');
  assert.strictEqual(WB.formatDate(''), '');
  assert.strictEqual(WB.yearsAgo(1869, 2026), 157);
  assert.strictEqual(WB.yearsAgo(2030, 2026), 0);
});

test('source labels say when a page is undated', () => {
  assert.strictEqual(WB.sourceLabel({ publisher: 'NASA', date: '2023-09-24' }), 'NASA, 24 Sep 2023');
  assert.strictEqual(WB.sourceLabel({ publisher: 'FANUC', date: 'undated', accessed: '2026-11-25' }), 'FANUC, undated page, read 25 Nov 2026');
});

test('URL state round-trips and drops unknown values', () => {
  const s = WB.parseState('?status=built&sector=Space+%26+Aerospace&q=moon&sort=companies');
  assert.deepStrictEqual(s, { status: 'built', sector: 'Space & Aerospace', q: 'moon', sort: 'companies' });
  assert.deepStrictEqual(WB.parseState(WB.stateToSearch(s)), s);
  assert.deepStrictEqual(WB.parseState('?status=soon&sort=random'), { status: '', sector: '', q: '', sort: 'oldest' });
  assert.strictEqual(WB.stateToSearch({ status: '', sector: '', q: '', sort: 'oldest' }), '');
});

test('sector options count themes, most first', () => {
  assert.deepStrictEqual(WB.sectorOptions(themes)[0], { sector: 'Space & Aerospace', themes: 2 });
});

// ─── the real data file ───────────────────────────────────────────────
test('the real data file draws', () => {
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(ROOT, 'data', 'imagined_auto.js'), 'utf8') + ';globalThis.D = IMAGINED;', ctx);
  const D = ctx.D;
  assert.ok(D.themes.length >= 20, 'expected at least 20 themes');
  const known = Array.from(D.statuses, s => s.key);      // a plain array in this realm, not the vm's
  assert.deepStrictEqual(known, WB.STATUS_ORDER);
  for (const t of D.themes) {
    assert.ok(known.includes(t.status), t.id);
    assert.ok(/^https:\/\/notboring\.com\/sci-fi-idea-bank\?idea=[rt]\d+$/.test(t.fiction.url), t.id);
    assert.ok(t.evidence.url.startsWith('https://') && !t.evidence.url.includes('notboring'), t.id);
    assert.strictEqual(t.count, t.companies.length, t.id);
    assert.ok(t.count > 0, t.id + ' has no companies');
    for (const c of t.companies) assert.ok(c.n && c.s, t.id);
  }
  assert.strictEqual(WB.filterThemes(D.themes, {}).length, D.themes.length);
  assert.strictEqual(D.meta.themes, D.themes.length);
  const built = D.themes.filter(t => t.status === 'built').length;
  assert.strictEqual(D.meta.by_status.built, built);
});

console.log((process.exitCode ? 'FAILED' : 'ok') + ': ' + passed + ' passed');
