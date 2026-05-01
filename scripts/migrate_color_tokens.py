#!/usr/bin/env python3
"""
Migrate hardcoded hex color literals in *.css files to var() refs from
css/_tokens.css. The design tokens were explicitly defined to match the
existing palette, so this is a SAFE renaming — visual output identical,
but page CSS becomes themable + self-documenting.

Only literal hex codes are touched (#abcdef and #abc patterns). rgba()
and rgb() forms are left alone — they have different syntax. CSS
variable definitions (--xxx: #yyy;) are also skipped (they ARE the
source of truth and shouldn't reference vars).

Usage:
  python scripts/migrate_color_tokens.py [--dry-run] [--target FILE]
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Hex literal → token name. Only the most-used + clearly-semantic colors.
# Matches case-insensitively. The number after each is the audit count.
COLOR_MAP = {
    # Greens (primary)
    "#22c55e": "var(--color-primary)",        # 144 uses
    "#4ade80": "var(--color-primary-bright)", #  26
    "#16a34a": "var(--color-primary-deep)",   #  rare

    # Orange (accent / defense)
    "#ff6b2c": "var(--color-accent)",         # 121
    "#ff8147": "var(--color-accent-bright)",  #   8

    # Blue (info / fusion / space)
    "#60a5fa": "var(--color-fusion)",         #  76

    # Status
    "#f59e0b": "var(--color-warning)",        #  65
    "#ef4444": "var(--color-danger)",         #  64

    # Bio / AI / Quantum (purple shades)
    "#8b5cf6": "var(--color-bio)",            #  24
    "#a855f7": "var(--color-quantum)",        #  13

    # Nuclear / Gold
    "#facc15": "var(--color-nuclear)",        #  rare
    "#ffd700": "var(--color-gold)",           #  34
}

# Build case-insensitive regex covering all the keys
HEX_PATTERN = re.compile(
    r"#([0-9a-fA-F]{6})\b",
)

# Skip lines that DEFINE a variable (e.g. `--color-primary: #22c55e;`)
VAR_DEF_LINE = re.compile(r"^\s*--[a-z0-9_-]+\s*:")

# Files to never touch
SKIP_FILES = {
    "_tokens.css",         # source of truth
    "_components.css",     # already uses var()
}


def migrate_file(path, dry_run=False):
    src = path.read_text(encoding="utf-8")
    out_lines = []
    replacements = 0

    for line in src.split("\n"):
        # Don't replace inside variable definitions
        if VAR_DEF_LINE.match(line):
            out_lines.append(line)
            continue

        def replace(match):
            nonlocal replacements
            hex_lower = "#" + match.group(1).lower()
            if hex_lower in COLOR_MAP:
                replacements += 1
                return COLOR_MAP[hex_lower]
            return match.group(0)

        new_line = HEX_PATTERN.sub(replace, line)
        out_lines.append(new_line)

    new_src = "\n".join(out_lines)
    if replacements == 0:
        return ("noop", 0)

    if dry_run:
        return ("preview", replacements)

    path.write_text(new_src, encoding="utf-8")
    return ("ok", replacements)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--target", help="single file to migrate")
    args = ap.parse_args()

    print(f"Color-token migration — {'DRY RUN' if args.dry_run else 'APPLY'}")
    print("=" * 60)

    targets = [Path(args.target)] if args.target else sorted(ROOT.glob("*.css"))
    targets += sorted((ROOT / "css").glob("*.css")) if not args.target else []
    targets = [p for p in targets if p.name not in SKIP_FILES]

    summary = {"ok": 0, "noop": 0, "preview": 0}
    total_replacements = 0

    for p in targets:
        status, n = migrate_file(p, dry_run=args.dry_run)
        if n > 0:
            sym = {"ok": "✓", "preview": "→"}.get(status, "?")
            print(f"  {sym} {p.relative_to(ROOT).as_posix():<35} {n} replacements")
            total_replacements += n
        summary[status] = summary.get(status, 0) + 1

    print()
    print(f"Summary: {summary}  total replacements: {total_replacements}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
