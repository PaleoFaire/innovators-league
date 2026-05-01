#!/usr/bin/env python3
"""
Auto-apply verified investor-facts changes to data.js (VC_FIRMS array).

Mirrors auto_apply_verified.py but scoped to VC_FIRMS — never modifies
COMPANIES entries by accident.

Conservative red-flag detection — automatically SKIPS:
  - Whole firms whose verifier `notes` contain TIER-1 doubt phrases
  - Per-field tier-2 doubts (skip just the suspect field, apply rest)
  - Firms in PERMANENT_SKIP_FIRMS

Usage:
  python scripts/auto_apply_investors.py --suffix [batchN] [--dry-run]
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / 'data.js'

# Reuse doubt logic from auto_apply_verified.py
sys.path.insert(0, str(ROOT / 'scripts'))
from auto_apply_verified import (
    is_tier1_doubt, field_has_doubt,
    _STRING_LIT, _ARRAY_LIT,
)

# Stephen-approved permanent skips (none yet for investors)
PERMANENT_SKIP_FIRMS = set()
PERMANENT_SKIP_FIELDS_PER_FIRM = {
    # Example for future use:
    # 'a16z (Andreessen Horowitz)': {'thesis'},  # if Stephen wants curator-only
}

# Field synonyms specific to investor entities (extends company synonyms)
INVESTOR_FIELD_SYNONYMS = {
    'aum':           ['aum', 'assets under management', 'fund size', 'capital under management'],
    'flagshipFund':  ['flagship fund', 'main fund', 'current fund'],
    'founded':       ['founded', 'founding year', 'established', 'started'],
    'hq':            ['hq', 'headquarters', 'based in', 'based out of'],
    'keyPartners':   ['partners', 'managing partners', 'general partners', 'gp', 'principals'],
    'sectorFocus':   ['sector', 'sector focus', 'thesis', 'investment thesis', 'focus areas'],
    'thesis':        ['thesis', 'investment thesis', 'strategy', 'philosophy'],
    'website':       ['website', 'url', 'domain'],
}


# ────────────────────────────────────────────────────────────────────────
# VC_FIRMS-SCOPED OBJECT LOCATION


def get_vc_firms_bounds(src):
    """Return (start_pos, end_pos) of the VC_FIRMS = [ ... ] block."""
    m = re.search(r'const VC_FIRMS\s*=\s*\[', src)
    if not m: return None
    start = m.end() - 1
    depth = 0
    in_str = False
    str_q = None
    for i in range(start, len(src)):
        c = src[i]
        if in_str:
            if c == '\\': continue
            if c == str_q: in_str = False
        else:
            if c in ('"', "'", '`'):
                in_str = True; str_q = c
            elif c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return (start, i)
    return None


def find_firm_object(src, name, vc_bounds=None):
    """Locate a VC firm entry inside VC_FIRMS only.
    Returns (open_pos, close_pos) absolute in src, or None.
    Matches `name: "X"` field exactly (not shortName)."""
    if vc_bounds is None:
        vc_bounds = get_vc_firms_bounds(src)
    if not vc_bounds: return None
    arr_start, arr_end = vc_bounds
    block = src[arr_start:arr_end+1]

    nm = re.escape(name)
    m = re.search(rf'name:\s*"{nm}"', block)
    if not m: return None

    open_pos_local = block.rfind('{', 0, m.start())
    if open_pos_local < 0: return None

    depth = 0
    in_str = False
    str_q = None
    for i in range(open_pos_local, len(block)):
        c = block[i]
        if in_str:
            if c == '\\': continue
            if c == str_q: in_str = False
        else:
            if c in ('"', "'", '`'):
                in_str = True; str_q = c
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return (arr_start + open_pos_local, arr_start + i)
    return None


# ────────────────────────────────────────────────────────────────────────
# APPLY CHANGE


def format_value(field, verified_val):
    """Format a verified value as a JS literal. Returns None if not formattable."""
    if verified_val is None or verified_val == "" or verified_val == []:
        return None

    # Array fields
    if field in ('keyPartners', 'sectorFocus', 'portfolioCompanies'):
        if not isinstance(verified_val, list):
            return None
        items = verified_val[:25]  # cap
        items_str = ', '.join('"' + str(i).replace('\\', '\\\\').replace('"', '\\"') + '"'
                              for i in items)
        return f'[{items_str}]'

    # Int field
    if field == 'founded':
        try:
            return str(int(verified_val))
        except (ValueError, TypeError):
            return None

    # String field
    v_str = str(verified_val).replace('\\', '\\\\').replace('"', '\\"')
    return f'"{v_str}"'


def apply_change_to_obj(obj, field, verified_val):
    """Apply a single field change. Returns (new_obj, changed_bool, reason_str)."""
    new_value = format_value(field, verified_val)
    if new_value is None:
        return obj, False, 'skipped:invalid_value'

    existing_pattern = rf'\b{field}\s*:\s*({_STRING_LIT}|{_ARRAY_LIT}|-?\d+|null|true|false)'
    m = re.search(existing_pattern, obj)
    if m:
        candidate = obj[:m.start()] + f'{field}: {new_value}' + obj[m.end():]
        if candidate == obj:
            return obj, False, 'noop_same_value'
        return candidate, True, 'replaced'

    # Insert as new field before closing brace
    indent_match = re.search(r'\n(\s+)\w+\s*:', obj)
    indent = indent_match.group(1) if indent_match else '    '
    close_idx = obj.rfind('}')
    prev = close_idx - 1
    while prev > 0 and obj[prev] in ' \n\t':
        prev -= 1
    if obj[prev] == ',':
        candidate = obj[:prev+1] + f'\n{indent}{field}: {new_value}\n{indent[:-2]}' + obj[close_idx:]
    elif obj[prev] != '{':
        candidate = obj[:prev+1] + f',\n{indent}{field}: {new_value}\n{indent[:-2]}' + obj[close_idx:]
    else:
        return obj, False, 'skipped:cant_locate_insertion_point'
    if candidate == obj:
        return obj, False, 'noop_same_value'
    return candidate, True, 'inserted'


def field_has_investor_doubt(notes, field):
    """Per-field doubt check using investor-specific synonyms."""
    if not notes: return False
    nl = notes.lower()
    # Reuse company-side detector but with investor synonyms
    synonyms = list(INVESTOR_FIELD_SYNONYMS.get(field, [])) + [field.lower()]

    # Same proximity logic as company side
    TIER2 = [
        'cannot be verified', 'could not be verified', 'not be verified',
        'no clear evidence', 'unable to verify', 'cannot verify',
        'could not verify', 'not explicitly', 'no information about', 'no source for',
    ]
    doubt_spans = []
    for d in TIER2:
        for m in re.finditer(re.escape(d), nl):
            doubt_spans.append((m.start(), m.end()))
    if not doubt_spans:
        return False
    for syn in synonyms:
        for sm in re.finditer(re.escape(syn.lower()), nl):
            for ds, de in doubt_spans:
                if abs(sm.start() - ds) < 80 or abs(sm.start() - de) < 80:
                    return True
    return False


# ────────────────────────────────────────────────────────────────────────
# MAIN


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--suffix', default='', help='batch suffix (empty for default file)')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    suf = f"_{args.suffix}" if args.suffix else ""
    in_path = ROOT / f'data/investor_facts_verification{suf}.json'
    if not in_path.exists():
        print(f'❌ {in_path} not found')
        return 2

    d = json.load(open(in_path))
    if d.get('skipped'):
        print(f"⚠ Verifier was skipped: {d.get('reason')}")
        return 0

    changes = d.get('changesProposed', [])
    print(f'Investor verification: {len(changes)} firms w/ proposed changes')

    src_before = DATA_JS.read_text(encoding='utf-8')
    src = src_before
    vc_bounds = get_vc_firms_bounds(src)
    if not vc_bounds:
        print('❌ Cannot locate VC_FIRMS array in data.js')
        return 2

    applied_per_field = {}
    applied_per_firm = []
    field_skipped_doubt = []
    skipped = []

    for entry in changes:
        name = entry['name']
        notes = entry.get('notes') or ''

        if name in PERMANENT_SKIP_FIRMS:
            skipped.append((name, 'permanent skip'))
            continue
        if is_tier1_doubt(notes):
            skipped.append((name, f'tier-1 doubt: "{notes[:80]}..."'))
            continue

        skip_fields = PERMANENT_SKIP_FIELDS_PER_FIRM.get(name, set())

        loc = find_firm_object(src, name, vc_bounds)
        if not loc:
            skipped.append((name, 'NOT FOUND in VC_FIRMS'))
            continue
        open_pos, close_pos = loc
        obj = src[open_pos:close_pos+1]
        new_obj = obj
        firm_changes_real = []

        for ch in entry.get('changes', []):
            field = ch['field']
            if field in skip_fields:
                continue
            if field_has_investor_doubt(notes, field):
                field_skipped_doubt.append((name, field))
                continue
            verified_val = ch.get('verified')
            new_obj, changed, reason = apply_change_to_obj(new_obj, field, verified_val)
            if changed:
                firm_changes_real.append(field)
                applied_per_field[field] = applied_per_field.get(field, 0) + 1

        if firm_changes_real:
            src = src[:open_pos] + new_obj + src[close_pos+1:]
            applied_per_firm.append((name, firm_changes_real))
            # Recompute bounds — they shifted
            vc_bounds = get_vc_firms_bounds(src)

    if args.dry_run:
        print('\n[DRY RUN] data.js NOT modified')
    else:
        if src != src_before:
            DATA_JS.write_text(src, encoding='utf-8')
            print(f'\n✏️  data.js MODIFIED: {len(src_before):,} → {len(src):,} bytes')
        else:
            print(f'\n📄 data.js UNCHANGED — all proposed investor changes were no-ops or skipped')

    real_total = sum(len(c) for _, c in applied_per_firm)
    print(f'✅ Real changes:        {real_total} fields across {len(applied_per_firm)} firms')
    print(f'⏭  Whole-firm skipped:  {len(skipped)}')
    print(f'⏭  Per-field skipped:   {len(field_skipped_doubt)}')

    if applied_per_field:
        print(f'\nField breakdown (real changes):')
        for f, n in sorted(applied_per_field.items(), key=lambda x: -x[1]):
            print(f'  {n:>3}  {f}')

    if skipped:
        print(f'\nFirms skipped:')
        for nm, reason in skipped[:10]:
            print(f'  ⏭ {nm}: {reason}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
