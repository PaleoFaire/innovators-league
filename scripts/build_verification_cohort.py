#!/usr/bin/env python3
"""
Build a cohort file for verification, selected by mode.

Modes:
  daily       - news-triggered: companies + investors mentioned in last 24h news
  weekly      - hot tier: signal=hot OR rising OR recent fundraise (last 30d)
  monthly     - full sweep: all entities (sliced by cohort batch)
  quarterly   - audit: companies/firms previously skipped (tier-1 doubt) + 128 unverifiable

Outputs JSON file: data/cohort_<entity>_<mode>.json
  Format: [{"name": "..."}, {"name": "..."}, ...]

Usage:
  python scripts/build_verification_cohort.py --mode daily --entity companies
  python scripts/build_verification_cohort.py --mode weekly --entity investors
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'

sys.path.insert(0, str(ROOT / 'scripts'))


def companies_news_triggered(since_hours=24):
    """Companies mentioned in news in the last N hours."""
    nr_path = DATA / 'news_raw.json'
    if not nr_path.exists(): return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    names = set()
    try:
        for n in json.load(open(nr_path)):
            # Try to parse pub date
            pub = n.get('pubDate') or n.get('isoDate') or n.get('publishedAt')
            if pub:
                try:
                    dt = datetime.fromisoformat(pub.replace('Z', '+00:00'))
                    if dt < cutoff: continue
                except Exception:
                    pass  # if we can't parse date, include conservatively
            for fld in ('matchedCompany', 'matchedCompanies'):
                v = n.get(fld)
                if isinstance(v, str) and v: names.add(v)
                elif isinstance(v, list): names.update(x for x in v if x)
    except Exception:
        return []
    return sorted(names)


def investors_news_triggered(since_hours=24):
    """Investors whose name appears in news in last N hours."""
    nr_path = DATA / 'news_raw.json'
    if not nr_path.exists(): return []
    from verify_investor_facts import parse_vc_firms
    firms = parse_vc_firms()
    firm_index = {}
    for f in firms:
        for variant in filter(None, [f.get('name'), f.get('shortName')]):
            firm_index[variant.lower()] = f['name']
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    matched = set()
    try:
        for n in json.load(open(nr_path)):
            pub = n.get('pubDate') or n.get('isoDate') or n.get('publishedAt')
            if pub:
                try:
                    dt = datetime.fromisoformat(pub.replace('Z', '+00:00'))
                    if dt < cutoff: continue
                except Exception:
                    pass
            blob = ((n.get('title') or '') + ' ' + (n.get('description') or '')).lower()
            for variant_lc, canonical in firm_index.items():
                if variant_lc in blob:
                    matched.add(canonical)
    except Exception:
        return []
    return sorted(matched)


def companies_hot_tier():
    """Companies with signal=hot/rising or recently funded."""
    from verify_company_facts import parse_companies
    cos = parse_companies()
    selected = set()
    # Currently parse_companies doesn't extract signal field — extend if needed
    # For now: include companies with addedDate in last 90 days as proxy
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).strftime('%Y-%m')
    for c in cos:
        # We don't have addedDate in the parsed dict — rely on raw data
        pass
    # Fallback: just return all signal=hot from raw scan
    src = (ROOT / 'data.js').read_text()
    # Find companies with signal: "hot" or "rising"
    for m in re.finditer(r'name:\s*"([^"]+)"[^}]*?signal:\s*"(hot|rising)"', src, re.DOTALL):
        if len(m.group(0)) < 5000:  # avoid greedy matches across cos
            selected.add(m.group(1))
    return sorted(selected)


def investors_hot_tier():
    """VC firms with signal=hot/rising."""
    from verify_investor_facts import parse_vc_firms
    firms = parse_vc_firms()
    return sorted(f['name'] for f in firms if f.get('signal') in ('hot', 'rising'))


def companies_full():
    """All companies."""
    from verify_company_facts import parse_companies
    return sorted(c['name'] for c in parse_companies() if c.get('name'))


def investors_full():
    """All VC firms."""
    from verify_investor_facts import parse_vc_firms
    return sorted(f['name'] for f in parse_vc_firms() if f.get('name'))


def companies_audit():
    """Companies previously tier-1 skipped or unverifiable across past batches."""
    names = set()
    for p in DATA.glob('company_facts_verification*.json'):
        try:
            d = json.load(open(p))
            for u in d.get('unverifiable', []):
                if u.get('name'): names.add(u['name'])
            # Also tier-1 skipped (company-wide doubt)
            for entry in d.get('changesProposed', []):
                notes = (entry.get('notes') or '').lower()
                if any(p in notes for p in ['different company', 'wrong company',
                                              'are two different', 'unrelated']):
                    if entry.get('name'): names.add(entry['name'])
        except Exception:
            continue
    return sorted(names)


def investors_audit():
    names = set()
    for p in DATA.glob('investor_facts_verification*.json'):
        try:
            d = json.load(open(p))
            for u in d.get('unverifiable', []):
                if u.get('name'): names.add(u['name'])
            for entry in d.get('changesProposed', []):
                notes = (entry.get('notes') or '').lower()
                if any(p in notes for p in ['different firm', 'wrong firm',
                                              'are two different', 'unrelated']):
                    if entry.get('name'): names.add(entry['name'])
        except Exception:
            continue
    return sorted(names)


SELECTORS = {
    ('daily', 'companies'):   companies_news_triggered,
    ('daily', 'investors'):   investors_news_triggered,
    ('weekly', 'companies'):  companies_hot_tier,
    ('weekly', 'investors'):  investors_hot_tier,
    ('monthly', 'companies'): companies_full,
    ('monthly', 'investors'): investors_full,
    ('quarterly', 'companies'): companies_audit,
    ('quarterly', 'investors'): investors_audit,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', required=True,
                    choices=['daily', 'weekly', 'monthly', 'quarterly'])
    ap.add_argument('--entity', required=True, choices=['companies', 'investors'])
    ap.add_argument('--limit', type=int, default=200)
    ap.add_argument('--output', help='Output path (default: data/cohort_<entity>_<mode>.json)')
    args = ap.parse_args()

    selector = SELECTORS.get((args.mode, args.entity))
    if not selector:
        print(f'ERROR: no selector for ({args.mode}, {args.entity})')
        return 1

    names = selector()
    names = names[:args.limit]
    out = [{'name': n} for n in names]

    if not args.output:
        args.output = str(DATA / f'cohort_{args.entity}_{args.mode}.json')
    with open(args.output, 'w') as f:
        json.dump(out, f, indent=2)

    print(f'Cohort built: {args.entity} / {args.mode}')
    print(f'  Count: {len(out)}')
    print(f'  Output: {args.output}')
    if names:
        print(f'  First 5: {names[:5]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
