#!/usr/bin/env node
/*
 * Tests for the pure helpers at the top of jobs.js (window.JobsFamilyLib on the page):
 * place names, distances, ZIP decoding, place lookup, the address-bar state and the
 * plain role-type matching.
 *
 *   node scripts/tests/test_jobs_family.js
 *
 * No dependencies. jobs_family_cases.json is shared with test_jobs_family.py, so the
 * page and the pipeline give the same answers.
 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const L = require(path.join(ROOT, 'jobs.js'));
const CASES = JSON.parse(fs.readFileSync(path.join(__dirname, 'jobs_family_cases.json'), 'utf8'));
const GEO = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'geo', 'us_places.json'), 'utf8'));

let passed = 0, failed = 0;
function test(name, fn) {
  try { fn(); passed++; } catch (e) { failed++; console.error('FAIL ' + name + '\n  ' + e.message); }
}
const close = (a, b, tol) => Math.abs(a - b) <= (tol === undefined ? 1e-9 : tol);

test('normPlace gives the pipeline keys', () => {
  CASES.normPlace.forEach(([raw, want]) => assert.strictEqual(L.normPlace(raw), want, raw));
});
test('stateCode', () => {
  CASES.stateCode.forEach(([raw, want]) => assert.strictEqual(L.stateCode(raw), want, raw));
});
test('haversineMiles', () => {
  CASES.distanceMiles.forEach((c) => assert.ok(close(L.haversineMiles(c.from[0], c.from[1], c.to[0], c.to[1]), c.miles, 0.001), c.why));
});
test('unpackZip reads what build_geo_places.py packs', () => {
  CASES.zips.lookups.forEach(([code, want]) => {
    const got = L.unpackZip(CASES.zips.packed, code);
    if (want === null) assert.strictEqual(got, null, code);
    else assert.ok(got && close(got[0], want[0]) && close(got[1], want[1]), code + ' -> ' + JSON.stringify(got));
  });
});

const idx = L.geoIndex(GEO);
test('geoIndex reads the committed places file', () => {
  assert.ok(idx.ok);
  assert.strictEqual(idx.places.filter(Boolean).length, GEO.counts.places);
  assert.strictEqual(idx.hubs.length, GEO.counts.hubs);
  assert.strictEqual(idx.hasZips, GEO.counts.zips > 0);
  assert.strictEqual(L.geoIndex(null).ok, false);
  assert.strictEqual(L.geoIndex({ places: 'nope' }).ok, false);
});
test('resolveNear: towns and areas in the committed file', () => {
  const r = (t) => L.resolveNear(t, idx);
  assert.strictEqual(r('Hawthorne, CA').label, 'Hawthorne, CA');
  assert.strictEqual(r('hawthorne, california').label, 'Hawthorne, CA');
  assert.strictEqual(r('Austin TX').label, 'Austin, TX');
  assert.strictEqual(r('austin tx').label, 'Austin, TX');
  assert.strictEqual(r('Washington, DC').label, 'Washington, DC');
  assert.strictEqual(r('NYC').label, 'New York, NY');
  assert.strictEqual(r('Saint Louis, Missouri').label, 'St. Louis, MO');
  assert.strictEqual(r('Starbase').label, 'Starbase, TX');
  assert.strictEqual(r('SF Bay Area').value, 'hub:sf');
  assert.strictEqual(r('Austin / Texas (whole area)').value, 'hub:tx');
  assert.strictEqual(r('hub:den').label, 'Denver / Colorado');
  assert.strictEqual(r('hub:xx').ok, false);
  assert.deepStrictEqual(r('   '), { ok: false, reason: 'empty' });
  assert.strictEqual(r('Atlantis, CA').reason, 'unknown');
  assert.strictEqual(r('Gotham').reason, 'unknown');
  if (!idx.hasZips) assert.strictEqual(r('90250').reason, 'no-zips');
});

const SYN = L.geoIndex({
  schema: 1, source: 'census', states: ['ME', 'OR', 'TX'],
  places: [['Portland', 0, 43.66, -70.26], ['Portland', 1, 45.52, -122.68], ['Austin', 2, 30.27, -97.74], ['Lake Placid', 2, 31.0, -95.0]],
  aliases: {}, hubs: [['tx', 'Austin / Texas', 30.27, -97.74, 0]], zips: CASES.zips.packed
});
test('resolveNear: ZIP codes and look-alike names', () => {
  const r = (t) => L.resolveNear(t, SYN);
  const z = r('92626');
  assert.strictEqual(z.kind, 'zip'); assert.ok(close(z.lat, 33.68) && close(z.lng, -117.91));
  assert.strictEqual(r('9262').reason, 'zip-short');
  assert.strictEqual(r('92628').reason, 'zip-unknown');
  const amb = r('Portland');
  assert.strictEqual(amb.reason, 'ambiguous');
  assert.deepStrictEqual(amb.options, ['Portland, ME', 'Portland, OR']);
  assert.strictEqual(r('Portland OR').label, 'Portland, OR');
  assert.strictEqual(r('portland, oregon').label, 'Portland, OR');
  assert.strictEqual(r('Lake Placid').label, 'Lake Placid, TX');
  assert.strictEqual(r('Austin').kind, 'place', 'a town beats the hub that shares its name');
  assert.strictEqual(r('Austin Texas').label, 'Austin, TX');
});
test('suggestPlaces', () => {
  const vals = (t, ix) => L.suggestPlaces(t, ix || idx).map((o) => o.value);
  assert.ok(vals('haw').includes('Hawthorne, CA'));
  assert.strictEqual(vals('san f')[0], 'San Francisco, CA');
  const hub = L.suggestPlaces('bay', idx).find((o) => o.kind === 'hub');
  assert.ok(hub, 'a hub is offered');
  assert.strictEqual(L.resolveNear(hub.value, idx).value, 'hub:sf', 'picking the hub resolves to it');
  assert.deepStrictEqual(vals('a'), []);
  assert.deepStrictEqual(vals('92626', SYN), ['92626']);
  assert.deepStrictEqual(vals('92628', SYN), []);
  assert.deepStrictEqual(vals('portland, o', SYN), ['Portland, OR']);
  if (!idx.hasZips) assert.deepStrictEqual(vals('90250'), []);
});

test('address-bar state round trip', () => {
  const s = Object.assign(L.defaultState(), {
    type: ['hands', 'early'], near: 'Austin, TX', within: 25, plusremote: true, nodegree: true, entry: true,
    salary: true, citizen: 'hide', clearance: 'only', q: 'welder', sort: 'new', metro: ['tx'], hardtech: false
  });
  const back = L.parseQuery('?' + L.buildQuery(s));
  ['type', 'near', 'within', 'plusremote', 'nodegree', 'entry', 'salary', 'citizen', 'clearance', 'q', 'sort', 'metro', 'hardtech']
    .forEach((k) => assert.deepStrictEqual(back[k], s[k], k));
  assert.strictEqual(L.buildQuery(L.defaultState()), '', 'defaults leave the address bar clean');
  const anyDist = Object.assign(L.defaultState(), { near: 'Austin, TX', within: 0 });
  assert.ok(L.buildQuery(anyDist).includes('within=any'));
  assert.strictEqual(L.parseQuery('?' + L.buildQuery(anyDist)).within, 0);
  assert.ok(!L.buildQuery(Object.assign(L.defaultState(), { near: 'Austin, TX' })).includes('within'), '50 miles is the default');
});
test('the browser location never goes into a link', () => {
  const me = Object.assign(L.defaultState(), { near: 'me', within: 25, plusremote: true });
  assert.strictEqual(L.buildQuery(me), '');
  assert.strictEqual(L.parseQuery('?near=me').near, '');
});
test('old links and bad values', () => {
  const old = L.parseQuery('?clearance=1&salary=1&remote=1');
  assert.strictEqual(old.clearance, 'only');
  assert.strictEqual(old.salary, true);
  assert.strictEqual(old.remote, true);
  const bad = L.parseQuery('?within=7&sort=bogus&citizen=maybe');
  assert.strictEqual(bad.within, L.WITHIN_DEFAULT);
  assert.strictEqual(bad.sort, '');
  assert.strictEqual(bad.citizen, '');
  assert.ok(L.buildQuery(Object.assign(L.defaultState(), { job: 'gh-acme-1' })).startsWith('job=gh-acme-1'));
});

test('plain role types: kinds of work add up, first jobs narrow', () => {
  const RT = [['hands', '', '', 1, 0], ['engineering', '', '', 2, 0], ['software', '', '', 4, 0], ['business', '', '', 8, 0], ['early', '', '', 16, 1]];
  const both = L.typeMasks(['hands', 'early'], RT);
  assert.deepStrictEqual(both, { work: 1, across: 16 });
  assert.ok(L.typeMatches(1 | 16, both));
  assert.ok(!L.typeMatches(1, both));
  assert.ok(!L.typeMatches(2 | 16, both));
  const either = L.typeMasks(['hands', 'engineering'], RT);
  assert.ok(L.typeMatches(1, either) && L.typeMatches(2, either) && !L.typeMatches(4, either));
  const early = L.typeMasks(['early'], RT);
  assert.ok(L.typeMatches(4 | 16, early) && !L.typeMatches(4, early));
  assert.ok(L.typeMatches(0, L.typeMasks([], RT)));
});
test('plain words for miles and dates', () => {
  assert.strictEqual(L.milesText(0.4), 'under 1 mile');
  assert.strictEqual(L.milesText(1.2), '1 mile');
  assert.strictEqual(L.milesText(12.6), '13 miles');
  assert.strictEqual(L.milesText(1234), '1,234 miles');
  assert.strictEqual(L.milesText(Infinity), '');
  assert.strictEqual(L.milesText(NaN), '');
  assert.strictEqual(L.plainDate('2026-05'), 'May 2026');
  assert.strictEqual(L.plainDate('2026-11-16'), '16 Nov 2026');
  assert.strictEqual(L.plainDate(''), '');
  assert.strictEqual(L.plainDate('soon'), 'soon');
});

console.log(passed + ' passed, ' + failed + ' failed');
process.exit(failed ? 1 : 0);
