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


def apply_change_to_obj(obj, field, verified_val):
    """Apply a single field change to a JS object literal string."""
    if not verified_val:
        return obj, False

    if field == 'investors':
        if not isinstance(verified_val, list):
            return obj, False
        items = verified_val[:10]
        items_str = ', '.join('"' + i.replace('"', '\\"') + '"' for i in items)
        new_value = f'[{items_str}]'
    elif field == 'founded':
        try:
            new_value = str(int(verified_val))
        except (ValueError, TypeError):
            return obj, False
    else:
        v_str = str(verified_val).replace('"', '\\"')
        new_value = f'"{v_str}"'

    existing_pattern = rf'\b{field}\s*:\s*("[^"]*"|\[[^\]]*\]|\d+|null|true|false)'
    m = re.search(existing_pattern, obj)
    if m:
        return obj[:m.start()] + f'{field}: {new_value}' + obj[m.end():], True

    # Insert new field before closing brace
    indent_match = re.search(r'\n(\s+)\w+\s*:', obj)
    indent = indent_match.group(1) if indent_match else '    '
    close_idx = obj.rfind('}')
    prev = close_idx - 1
    while prev > 0 and obj[prev] in ' \n\t':
        prev -= 1
    if obj[prev] == ',':
        return obj[:prev+1] + f'\n{indent}{field}: {new_value}\n{indent[:-2]}' + obj[close_idx:], True
    elif obj[prev] != '{':
        return obj[:prev+1] + f',\n{indent}{field}: {new_value}\n{indent[:-2]}' + obj[close_idx:], True
    return obj, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--suffix', required=True, help='batch suffix (e.g. batch4)')
    args = ap.parse_args()

    in_path = ROOT / f'data/company_facts_verification_{args.suffix}.json'
    if not in_path.exists():
        print(f'⚠ {in_path} not found — nothing to apply')
        return 0

    d = json.load(open(in_path))
    changes = d.get('changesProposed', [])
    print(f'Verification report: {len(changes)} companies w/ proposed changes')

    src = DATA_JS.read_text(encoding='utf-8')
    applied_per_field = {}
    applied_per_company = []
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
        company_changes = []

        for ch in entry.get('changes', []):
            field = ch['field']
            if field in skip_fields:
                continue
            verified_val = ch.get('verified')
            new_obj, ok = apply_change_to_obj(new_obj, field, verified_val)
            if ok:
                company_changes.append(field)
                applied_per_field[field] = applied_per_field.get(field, 0) + 1

        if company_changes:
            src = src[:open_pos] + new_obj + src[close_pos+1:]
            applied_per_company.append((name, len(company_changes)))

    DATA_JS.write_text(src, encoding='utf-8')

    total = sum(n for _, n in applied_per_company)
    print(f'\n✅ Applied {total} changes across {len(applied_per_company)} companies')
    print(f'⏭  Skipped {len(skipped)} companies')
    print(f'\nField breakdown:')
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
