#!/usr/bin/env python3
"""
Apply verified corrections to company data in data.js.
Reads corrections from /tmp/corrections_merged.json and safely applies them.

Correction format:
[
  {"name": "Company Name", "field": "founder", "old": "Wrong", "new": "Correct"},
  {"name": "Company Name", "field": "location", "old": "Wrong City", "new": "Correct City"},
  {"name": "Company Name", "field": "state", "old": "XX", "new": "YY"},
  {"name": "Company Name", "field": "lat", "old": "30.0", "new": "37.0"},
  {"name": "Company Name", "field": "lng", "old": "-97.0", "new": "-122.0"},
]
"""

import json
import re
import sys
from pathlib import Path

DATA_JS_PATH = Path(__file__).parent.parent / "data.js"
CORRECTIONS_PATH = Path("/tmp/corrections_merged.json")


def apply_corrections(data_js_content, corrections):
    """Apply corrections to data.js content."""
    applied = 0
    failed = []

    for correction in corrections:
        name = correction["name"]
        field = correction["field"]
        old_val = correction["old"]
        new_val = correction["new"]

        # Find the company entry by name
        name_pattern = re.escape(name)
        name_match = re.search(rf'name:\s*"{name_pattern}"', data_js_content)

        if not name_match:
            failed.append(f"Company not found: {name}")
            continue

        # Find the end of this company's entry (next company or end of array)
        entry_start = name_match.start()
        # Look for the closing } of this entry
        # Find the next 'name:' or end of COMPANIES array
        next_name = re.search(r'name:\s*"', data_js_content[entry_start + 10:])
        if next_name:
            entry_end = entry_start + 10 + next_name.start()
        else:
            entry_end = len(data_js_content)

        entry_block = data_js_content[entry_start:entry_end]

        # Handle different field types
        if field in ("lat", "lng"):
            # Numeric fields
            old_escaped = re.escape(str(old_val))
            field_pattern = rf'({field}:\s*){old_escaped}'
            field_match = re.search(field_pattern, entry_block)
            if field_match:
                replacement = f'{field_match.group(1)}{new_val}'
                new_block = entry_block[:field_match.start()] + replacement + entry_block[field_match.end():]
                data_js_content = data_js_content[:entry_start] + new_block + data_js_content[entry_end:]
                applied += 1
                print(f"  ✅ {name}.{field}: {old_val} → {new_val}")
            else:
                # Try finding field with any value
                field_any = re.search(rf'{field}:\s*[-\d.]+', entry_block)
                if field_any:
                    replacement = f'{field}: {new_val}'
                    new_block = entry_block[:field_any.start()] + replacement + entry_block[field_any.end():]
                    data_js_content = data_js_content[:entry_start] + new_block + data_js_content[entry_end:]
                    applied += 1
                    print(f"  ✅ {name}.{field}: (any) → {new_val}")
                else:
                    failed.append(f"Field not found: {name}.{field}")
        else:
            # String fields (founder, location, state)
            old_escaped = re.escape(old_val)
            field_pattern = rf'({field}:\s*"){old_escaped}(")'
            field_match = re.search(field_pattern, entry_block)
            if field_match:
                # Escape any special chars in new_val for the replacement
                new_val_escaped = new_val.replace('\\', '\\\\').replace('"', '\\"')
                replacement = f'{field_match.group(1)}{new_val_escaped}{field_match.group(2)}'
                new_block = entry_block[:field_match.start()] + replacement + entry_block[field_match.end():]
                data_js_content = data_js_content[:entry_start] + new_block + data_js_content[entry_end:]
                applied += 1
                print(f"  ✅ {name}.{field}: \"{old_val}\" → \"{new_val}\"")
            else:
                # Try to find field with any value
                field_any = re.search(rf'{field}:\s*"[^"]*"', entry_block)
                if field_any:
                    new_val_escaped = new_val.replace('\\', '\\\\').replace('"', '\\"')
                    replacement = f'{field}: "{new_val_escaped}"'
                    new_block = entry_block[:field_any.start()] + replacement + entry_block[field_any.end():]
                    data_js_content = data_js_content[:entry_start] + new_block + data_js_content[entry_end:]
                    applied += 1
                    print(f"  ✅ {name}.{field}: (any) → \"{new_val}\"")
                else:
                    failed.append(f"Field not found: {name}.{field}")

    return data_js_content, applied, failed


def validate_brackets(content):
    """Check bracket balance."""
    counts = {"(": 0, "[": 0, "{": 0}
    close_map = {")": "(", "]": "[", "}": "{"}
    for ch in content:
        if ch in counts:
            counts[ch] += 1
        elif ch in close_map:
            counts[close_map[ch]] -= 1

    balanced = all(v == 0 for v in counts.values())
    return balanced, counts


def main():
    print("=" * 60)
    print("APPLY CORRECTIONS TO data.js")
    print("=" * 60)

    if not CORRECTIONS_PATH.exists():
        print(f"ERROR: {CORRECTIONS_PATH} not found!")
        sys.exit(1)

    with open(CORRECTIONS_PATH) as f:
        corrections = json.load(f)

    print(f"Corrections to apply: {len(corrections)}")

    if not corrections:
        print("No corrections to apply.")
        return

    with open(DATA_JS_PATH) as f:
        content = f.read()

    original_len = len(content)

    # Validate before
    balanced, counts = validate_brackets(content)
    print(f"\nBefore: {original_len:,} bytes, brackets balanced: {balanced}")

    # Apply corrections
    print("\nApplying corrections:")
    content, applied, failed = apply_corrections(content, corrections)

    # Validate after
    balanced, counts = validate_brackets(content)
    print(f"\nAfter: {len(content):,} bytes, brackets balanced: {balanced}")
    if not balanced:
        print(f"  WARNING: Bracket imbalance: {counts}")
        print("  NOT writing file!")
        sys.exit(1)

    # Check for missing commas
    missing_commas = list(re.finditer(r'}\s*\n\s*{', content))
    if missing_commas:
        print(f"  WARNING: {len(missing_commas)} possible missing commas")

    # Write
    with open(DATA_JS_PATH, 'w') as f:
        f.write(content)

    print(f"\n{'=' * 60}")
    print(f"RESULTS:")
    print(f"  Applied: {applied}")
    print(f"  Failed: {len(failed)}")
    if failed:
        for f_msg in failed:
            print(f"    ❌ {f_msg}")
    print(f"  File: {original_len:,} → {len(content):,} bytes")
    print("=" * 60)


if __name__ == "__main__":
    main()
