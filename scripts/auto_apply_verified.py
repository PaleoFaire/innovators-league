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

# Tier-1 doubt phrases: indicate the verifier got the WRONG company entirely.
# When any of these appear in notes → skip the whole company, no fields applied.
TIER1_DOUBT_PHRASES = [
    'different company',
    'wrong company',
    'are two different companies',
    'appear to be two different',
    'unrelated company',
    'kitchen',                # famous Sift / kitchen-sieves false positive
]
# Tier-1 negative patterns matched CASE-SENSITIVELY in raw notes (rarer + specific):
TIER1_NEGATIVE_PATTERNS = [
    r'\bNOT a (company|startup|firm|business)\b',
    r'\bNOT the same (company|firm)\b',
    r'\bis NOT (a|an|the)\b',
]

# Tier-2 doubt phrases: indicate uncertainty about a SPECIFIC field, not the
# whole company. We only skip the field whose name (or synonym) appears
# nearby in the notes — other verified fields still get applied.
# This implements Stephen's per-field-doubt-filter rule:
# "update what information you can verify and leave the rest blank."
TIER2_DOUBT_PHRASES = [
    'cannot be verified',
    'could not be verified',
    'not be verified',
    'no clear evidence',
    'unable to verify',
    'cannot verify',
    'could not verify',
    'not explicitly',
    'no information about',
    'no source for',
]

# Map each verified field → text we'd look for in notes to associate doubts.
FIELD_SYNONYMS = {
    'totalRaised':  ['total raised', 'total_raised', 'total funding', 'capital raised',
                     'amount raised', 'fundraising', 'funding amount'],
    'founded':      ['founded year', 'founding year', 'founded_year', 'year founded',
                     'established', 'founded in', 'founded:'],
    'fundingStage': ['funding stage', 'current_stage', 'current stage', 'series',
                     'funding round', 'stage'],
    'founder':      ['founder', 'founders', 'co-founder', 'co-founders', 'cofounder',
                     'founding team'],
    'location':     ['location', 'headquarters', 'hq ', 'based in', 'based out',
                     'headquartered'],
    'investors':    ['investor', 'investors', 'backed by', 'lead investor', 'capital partners'],
    'website':      ['website', 'url', 'domain'],
    'description':  ['description', 'business description'],
}

# Window (chars) around a tier-2 doubt phrase in which a field synonym
# counts as "this doubt refers to that field".
DOUBT_PROXIMITY_WINDOW = 80


def is_tier1_doubt(notes):
    """Whole company is unsalvageable (wrong-company source confusion)."""
    if not notes: return False
    nl = notes.lower()
    for p in TIER1_DOUBT_PHRASES:
        if p.lower() in nl: return True
    for pat in TIER1_NEGATIVE_PATTERNS:
        if re.search(pat, notes): return True   # case-sensitive
    return False


def field_has_doubt(notes, field):
    """True iff a tier-2 doubt phrase appears within DOUBT_PROXIMITY_WINDOW
    chars of any synonym of `field` in `notes`. Skips just that field."""
    if not notes: return False
    nl = notes.lower()
    synonyms = list(FIELD_SYNONYMS.get(field, [])) + [field.lower()]
    # Pre-compute tier-2 phrase positions
    doubt_spans = []
    for d in TIER2_DOUBT_PHRASES:
        for m in re.finditer(re.escape(d.lower()), nl):
            doubt_spans.append((m.start(), m.end()))
    if not doubt_spans:
        return False
    for syn in synonyms:
        for sm in re.finditer(re.escape(syn.lower()), nl):
            for ds, de in doubt_spans:
                # synonym overlap window with the doubt phrase?
                if abs(sm.start() - ds) < DOUBT_PROXIMITY_WINDOW or \
                   abs(sm.start() - de) < DOUBT_PROXIMITY_WINDOW:
                    return True
    return False


# Backwards-compat alias (old call sites used this for "skip whole company")
def has_doubt(notes):
    """Conservative whole-company skip — kept for legacy callers."""
    return is_tier1_doubt(notes)


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
    skipped = []                  # whole-company skips
    field_skipped_doubt = []      # per-field doubt skips: (name, field)

    for entry in changes:
        name = entry['name']
        notes = entry.get('notes') or ''

        # Whole-company skips: permanent + tier-1 (wrong-company source confusion)
        if name in PERMANENT_SKIP_COMPANIES:
            skipped.append((name, 'permanent skip (Stephen-flagged)'))
            continue
        if is_tier1_doubt(notes):
            skipped.append((name, f'tier-1 doubt: "{(notes or "")[:80]}..."'))
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
            # Per-field tier-2 doubt: skip just this field if verifier expressed
            # uncertainty about it specifically, but apply other verified fields.
            if field_has_doubt(notes, field):
                field_skipped_doubt.append((name, field))
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
    print(f'✅ Real changes:        {real_total} fields across {len(applied_per_company)} companies')
    print(f'➖ No-op matches:       {noop_total} fields across {len(noop_per_company)} companies (value already correct)')
    print(f'⏭  Whole-co skipped:    {len(skipped)} companies (tier-1 doubt or permanent)')
    print(f'⏭  Per-field skipped:   {len(field_skipped_doubt)} field-changes (tier-2 field-specific doubt)')
    if applied_per_field:
        print(f'\nField breakdown (real changes):')
        for f, n in sorted(applied_per_field.items(), key=lambda x: -x[1]):
            print(f'  {n:>3}  {f}')
    if skipped:
        print(f'\nWhole-company skips (first 10):')
        for nm, reason in skipped[:10]:
            print(f'  ⏭ {nm}: {reason}')
        if len(skipped) > 10:
            print(f'  ...and {len(skipped)-10} more')
    if field_skipped_doubt:
        # Field-level skips, grouped by field
        from collections import Counter
        c = Counter(f for _, f in field_skipped_doubt)
        print(f'\nPer-field doubt skips by field:')
        for f, n in c.most_common():
            print(f'  {n:>3}  {f}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
