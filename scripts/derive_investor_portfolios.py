#!/usr/bin/env python3
"""
Derive VC_FIRMS.portfolioCompanies from COMPANIES.investors[] reverse index.

Why: the investor verifier shouldn't try to extract portfolio from sources —
we have it more accurately by reverse-indexing what each company says.

Handles fragmented investor names: "a16z" / "Andreessen Horowitz" / "Andreessen
Horowitz Growth" all resolve to the same VC_FIRMS entry via canonical-name map.

Usage:
  python scripts/derive_investor_portfolios.py [--dry-run]
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / 'data.js'

sys.path.insert(0, str(ROOT / 'scripts'))
from verify_company_facts import parse_companies
from verify_investor_facts import parse_vc_firms
from auto_apply_investors import find_firm_object, get_vc_firms_bounds, format_value


# Canonical-name map: maps every alias seen in COMPANIES.investors[] to the
# canonical VC_FIRMS name. Built from observed fragmentation. Easy to extend.
NAME_ALIASES = {
    # a16z
    'a16z': 'a16z (Andreessen Horowitz)',
    'andreessen horowitz': 'a16z (Andreessen Horowitz)',
    'andreessen horowitz growth': 'a16z (Andreessen Horowitz)',
    'a16z growth': 'a16z (Andreessen Horowitz)',
    'a16z american dynamism': 'a16z (Andreessen Horowitz)',

    # Founders Fund
    'founders fund': 'Founders Fund',
    'founders fund growth': 'Founders Fund',

    # 8VC
    '8vc': '8VC',

    # Khosla
    'khosla ventures': 'Khosla Ventures',
    'khosla': 'Khosla Ventures',

    # Sequoia
    'sequoia capital': 'Sequoia Capital',
    'sequoia': 'Sequoia Capital',

    # DCVC
    'dcvc': 'DCVC (Data Collective)',
    'data collective': 'DCVC (Data Collective)',
    'data collective dcvc': 'DCVC (Data Collective)',

    # Lux
    'lux capital': 'Lux Capital',
    'lux': 'Lux Capital',

    # Lowercarbon
    'lowercarbon capital': 'Lowercarbon Capital',
    'lowercarbon': 'Lowercarbon Capital',

    # Breakthrough Energy Ventures
    'breakthrough energy ventures': 'Breakthrough Energy Ventures',
    'breakthrough energy': 'Breakthrough Energy Ventures',

    # General Catalyst
    'general catalyst': 'General Catalyst',
    'general catalyst partners': 'General Catalyst',

    # Y Combinator
    'y combinator': 'Y Combinator',
    'yc': 'Y Combinator',
    'ycombinator': 'Y Combinator',

    # Playground Global
    'playground global': 'Playground Global',
    'playground': 'Playground Global',

    # Bessemer
    'bessemer venture partners': 'Bessemer Venture Partners',
    'bessemer': 'Bessemer Venture Partners',
    'bessemer ventures': 'Bessemer Venture Partners',

    # Accel
    'accel': 'Accel',
    'accel partners': 'Accel',

    # GV
    'gv': 'GV (Google Ventures)',
    'google ventures': 'GV (Google Ventures)',
    'gv (google ventures)': 'GV (Google Ventures)',

    # Index
    'index ventures': 'Index Ventures',

    # In-Q-Tel
    'in-q-tel': 'In-Q-Tel',
    'iqt': 'In-Q-Tel',

    # Insight Partners
    'insight partners': 'Insight Partners',

    # Tiger Global
    'tiger global': 'Tiger Global',
    'tiger global management': 'Tiger Global',

    # Coatue
    'coatue': 'Coatue',
    'coatue management': 'Coatue',

    # Thrive Capital
    'thrive capital': 'Thrive Capital',
    'thrive': 'Thrive Capital',

    # Greylock
    'greylock partners': 'Greylock Partners',
    'greylock': 'Greylock Partners',

    # Kleiner Perkins
    'kleiner perkins': 'Kleiner Perkins',
    'kpcb': 'Kleiner Perkins',

    # NEA
    'nea': 'NEA (New Enterprise Associates)',
    'new enterprise associates': 'NEA (New Enterprise Associates)',

    # Benchmark
    'benchmark': 'Benchmark',
    'benchmark capital': 'Benchmark',
}


def canonical_name(raw_name, vc_firms_canonical_set):
    """Resolve a raw investor string from COMPANIES.investors[] to a VC_FIRMS canonical name.
    Returns None if no match."""
    if not raw_name: return None
    norm = raw_name.lower().strip()

    # Direct alias hit?
    if norm in NAME_ALIASES:
        canonical = NAME_ALIASES[norm]
        if canonical in vc_firms_canonical_set:
            return canonical
        return None

    # Direct match against canonical set (case-insensitive)?
    for canon in vc_firms_canonical_set:
        if canon.lower() == norm:
            return canon
        # Also try shortName match: canonical is "a16z (Andreessen Horowitz)" → check "a16z"
        m = re.match(r'^(\S+(?:\s+\S+)?)\s*\(', canon)
        if m and m.group(1).lower() == norm:
            return canon
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    print('=' * 60)
    print('Derive Investor Portfolios from COMPANIES.investors[]')
    print('=' * 60)

    companies = parse_companies()
    firms = parse_vc_firms()
    canonical_set = {f['name'] for f in firms if f.get('name')}
    print(f'  Companies: {len(companies)}')
    print(f'  VC firms: {len(firms)}')
    print()

    # Build reverse index: canonical_firm_name → set of company names
    portfolio_index = {f['name']: set() for f in firms}

    unmatched_aliases = {}  # raw_name → count
    matched_count = 0
    total_mentions = 0

    for c in companies:
        co_name = c.get('name')
        for inv_raw in (c.get('investors') or []):
            total_mentions += 1
            canon = canonical_name(inv_raw, canonical_set)
            if canon:
                portfolio_index[canon].add(co_name)
                matched_count += 1
            else:
                unmatched_aliases[inv_raw] = unmatched_aliases.get(inv_raw, 0) + 1

    print(f'Investor mentions matched: {matched_count} / {total_mentions} ({100*matched_count/total_mentions:.1f}%)')
    print(f'Unmatched raw names: {len(unmatched_aliases)} unique')
    print()
    print('Portfolio counts per VC (current vs derived):')
    print()
    print(f'  {"FIRM":<35} {"CURRENT":>9} {"DERIVED":>9} {"DELTA":>9}')
    print('  ' + '-' * 65)

    deltas = []
    for f in firms:
        nm = f['name']
        current = set(f.get('portfolioCompanies') or [])
        derived = portfolio_index.get(nm, set())
        delta = len(derived) - len(current)
        deltas.append((nm, current, derived, delta))
        marker = '⬆' if delta > 0 else ('⬇' if delta < 0 else ' ')
        print(f'  {nm[:33]:<35} {len(current):>9} {len(derived):>9} {marker}{delta:>+8}')

    # Show top unmatched aliases (so Stephen can extend NAME_ALIASES if needed)
    print()
    print('Top 15 unmatched investor aliases (extend NAME_ALIASES if any are real VCs we should track):')
    for raw, n in sorted(unmatched_aliases.items(), key=lambda x: -x[1])[:15]:
        print(f'  {n:>3}  {raw}')

    if args.dry_run:
        print('\n[DRY RUN] data.js NOT modified')
        return 0

    # Apply: write derived portfolioCompanies into VC_FIRMS
    src = DATA_JS.read_text(encoding='utf-8')
    vc_bounds = get_vc_firms_bounds(src)
    real_writes = 0

    for nm, current, derived, delta in deltas:
        if not derived: continue
        # Use union: don't remove existing entries (curator-set may include
        # historical), but add newly-discovered ones.
        merged = sorted(current | derived)
        if list(merged) == sorted(current): continue   # no change

        loc = find_firm_object(src, nm, vc_bounds)
        if not loc: continue
        open_pos, close_pos = loc
        obj = src[open_pos:close_pos+1]
        new_value = format_value('portfolioCompanies', merged)
        if not new_value: continue
        # Replace existing portfolioCompanies array
        from auto_apply_investors import _STRING_LIT, _ARRAY_LIT
        pat = rf'\bportfolioCompanies\s*:\s*({_STRING_LIT}|{_ARRAY_LIT}|-?\d+|null|true|false)'
        m = re.search(pat, obj)
        if m:
            new_obj = obj[:m.start()] + f'portfolioCompanies: {new_value}' + obj[m.end():]
            if new_obj != obj:
                src = src[:open_pos] + new_obj + src[close_pos+1:]
                vc_bounds = get_vc_firms_bounds(src)
                real_writes += 1

    if real_writes > 0:
        DATA_JS.write_text(src, encoding='utf-8')
        print(f'\n✏️  data.js MODIFIED: {real_writes} firms got updated portfolios')
    else:
        print('\n📄 data.js unchanged (no firms had portfolio additions)')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
