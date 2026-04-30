#!/usr/bin/env python3
"""
Auto-apply verified company-facts changes to data.js.

Conservative red-flag detection — automatically SKIPS:
  - Whole companies whose verifier `notes` contain doubt phrases
    ("different company", "wrong company", "could not verify", etc.)
  - The 3 companies in PERMANENT_SKIPS (Cover, etc. — Stephen-flagged)

Usage:
  python scripts/auto_apply_verified.py --suffix batch4
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / 'data.js'

# Stephen-approved permanent skips (apply across all batches)
PERMANENT_SKIP_COMPANIES = {'Cover'}
PERMANENT_SKIP_FIELDS_PER_COMPANY = {
    'SpaceX': {'fundingStage'},
    'OpenAI': {'founder'},
}

# Red-flag phrases in verifier `notes` that auto-skip the entire company
DOUBT_PHRASES = [
    'different company',
    'wrong company',
    'NOT a',
    'NOT the',
    'appear to be two different',
    'are two different companies',
    'cannot be verified',
    'could not be verified',
    'kitchen',  # the famous "Sift" / kitchen sieves false positive
    'unrelated',
]


def has_doubt(notes):
    if not notes: return False
    n = notes.lower()
    return any(phrase.lower() in n for phrase in DOUBT_PHRASES)


def find_object(src, name):
    """Locate a company entry in data.js. Returns (open_pos, close_pos) or None."""
    nm = re.escape(name)
    m = re.search(rf'name:\s*"{nm}"', src)
    if not m: return None
    open_pos = src.rfind('{', 0, m.start())
    depth = 0
    in_str = False
    str_q = None
    for i in range(open_pos, len(src)):
        ch = src[i]
        if in_str:
            if ch == '\\': continue
            if ch == str_q: in_str = False
        else:
            if ch in ('"', "'", '`'):
                in_str = True
                str_q = ch
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return (open_pos, i)
    return None


# Robust JS-literal regexes that handle escaped quotes / nested brackets
# in string values. Critical: the simpler "[^"]*" form fails on description
# strings with embedded \" sequences and would silently corrupt the file
# if such a value is ever inserted by a future verifier run.
_STRING_LIT = r'"(?:[^"\\]|\\.)*"'
_ARRAY_LIT  = r'\[(?:[^\[\]"]*|' + _STRING_LIT + r')*\]'


def apply_change_to_obj(obj, field, verified_val):
    """Apply a single field change to a JS object literal string.

    Returns (new_obj, changed, reason) where:
      - new_obj: the (possibly modified) JS object literal
      - changed: True iff new_obj != obj (i.e., bytes really changed)
      - reason:  'replaced' | 'inserted' | 'noop_same_value' | 'skipped:<why>'
    """
    if verified_val is None or verified_val == "":
        return obj, False, 'skipped:empty_verified'

    # Format new value as JS literal
    if field == 'investors':
        if not isinstance(verified_val, list):
            return obj, False, 'skipped:investors_not_list'
        items = verified_val[:10]
        items_str = ', '.join('"' + i.replace('"', '\\"') + '"' for i in items)
        new_value = f'[{items_str}]'
    elif field == 'founded':
        try:
            new_value = str(int(verified_val))
        except (ValueError, TypeError):
            return obj, False, 'skipped:founded_not_int'
    else:
        v_str = str(verified_val).replace('\\', '\\\\').replace('"', '\\"')
        new_value = f'"{v_str}"'

    existing_pattern = rf'\b{field}\s*:\s*({_STRING_LIT}|{_ARRAY_LIT}|-?\d+|null|true|false)'
    m = re.search(existing_pattern, obj)
    if m:
        candidate = obj[:m.start()] + f'{field}: {new_value}' + obj[m.end():]
        if candidate == obj:
            return obj, False, 'noop_same_value'
        return candidate, True, 'replaced'

    # Field doesn't exist — insert before closing brace
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--suffix', required=True, help='batch suffix (e.g. batch4)')
    ap.add_argument('--dry-run', action='store_true', help='Print what would change without writing data.js')
    args = ap.parse_args()

    in_path = ROOT / f'data/company_facts_verification_{args.suffix}.json'
    if not in_path.exists():
        # Per Stephen's "no silent failures" rule, this is an error condition
        # the caller (workflow) should be aware of. Exit non-zero.
        print(f'❌ {in_path} not found — verify step likely failed silently')
        return 2

    d = json.load(open(in_path))
    if d.get('skipped'):
        print(f"⚠ Verifier was skipped: {d.get('reason')}")
        return 0

    changes = d.get('changesProposed', [])
    print(f'Verification report: {len(changes)} companies w/ proposed changes')

    src_before = DATA_JS.read_text(encoding='utf-8')
    src = src_before
    applied_per_field = {}     # field → count of REAL byte-level changes
    noop_per_field = {}        # field → count of "matched but value identical" cases
    applied_per_company = []   # [(name, [fields_actually_changed]), ...]
    noop_per_company = []      # [(name, [fields_no_op]), ...]
    skipped = []

    for entry in changes:
        name = entry['name']
        notes = entry.get('notes') or ''

        # Auto-skip via red-flag detection
        if name in PERMANENT_SKIP_COMPANIES:
            skipped.append((name, 'permanent skip (Stephen-flagged)'))
            continue
        if has_doubt(notes):
            skipped.append((name, f'doubt phrase: "{(notes or "")[:80]}..."'))
            continue

        skip_fields = PERMANENT_SKIP_FIELDS_PER_COMPANY.get(name, set())

        loc = find_object(src, name)
        if not loc:
            skipped.append((name, 'NOT FOUND in data.js'))
            continue
        open_pos, close_pos = loc
        obj = src[open_pos:close_pos+1]
        new_obj = obj
        company_changes_real = []
        company_changes_noop = []

        for ch in entry.get('changes', []):
            field = ch['field']
            if field in skip_fields:
                continue
            verified_val = ch.get('verified')
            new_obj, changed, reason = apply_change_to_obj(new_obj, field, verified_val)
            if changed:
                company_changes_real.append(field)
                applied_per_field[field] = applied_per_field.get(field, 0) + 1
            elif reason == 'noop_same_value':
                company_changes_noop.append(field)
                noop_per_field[field] = noop_per_field.get(field, 0) + 1
            # other 'skipped:*' reasons are quietly counted as no-ops

        if company_changes_real:
            src = src[:open_pos] + new_obj + src[close_pos+1:]
            applied_per_company.append((name, company_changes_real))
        if company_changes_noop:
            noop_per_company.append((name, company_changes_noop))

    if args.dry_run:
        print('\n[DRY RUN] data.js NOT modified')
    else:
        if src != src_before:
            DATA_JS.write_text(src, encoding='utf-8')
            byte_delta = len(src) - len(src_before)
            print(f'\n✏️  data.js MODIFIED: {len(src_before):,} → {len(src):,} bytes ({byte_delta:+,})')
        else:
            print(f'\n📄 data.js UNCHANGED ({len(src):,} bytes) — all proposed changes were no-ops or skipped')

    real_total = sum(len(c) for _, c in applied_per_company)
    noop_total = sum(len(c) for _, c in noop_per_company)
    print(f'✅ Real changes:   {real_total} fields across {len(applied_per_company)} companies')
    print(f'➖ No-op matches:  {noop_total} fields across {len(noop_per_company)} companies (value already correct)')
    print(f'⏭  Skipped:        {len(skipped)} companies')
    if applied_per_field:
        print(f'\nField breakdown (real changes):')
        for f, n in sorted(applied_per_field.items(), key=lambda x: -x[1]):
            print(f'  {n:>3}  {f}')
    if skipped:
        print(f'\nSkipped (auto red-flag detection):')
        for nm, reason in skipped[:10]:
            print(f'  ⏭ {nm}: {reason}')
        if len(skipped) > 10:
            print(f'  ...and {len(skipped)-10} more')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
