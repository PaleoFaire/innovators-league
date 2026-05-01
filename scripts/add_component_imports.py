#!/usr/bin/env python3
"""
Add <link> imports for css/_tokens.css + css/_components.css to every
HTML page that doesn't already have them. Pure additive — no visual
change unless a page already has elements using .il-* classes.

Idempotent (skips pages already importing the lib).

Usage:
  python scripts/add_component_imports.py [--dry-run]
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "20260501"

IMPORTS = (
    f'    <link rel="stylesheet" href="css/_tokens.css?v={VERSION}" />\n'
    f'    <link rel="stylesheet" href="css/_components.css?v={VERSION}" />\n'
)


def update(path, dry_run=False):
    src = path.read_text(encoding="utf-8")
    if "_tokens.css" in src and "_components.css" in src:
        return ("noop", "already imports lib")

    head_end = src.find("</head>")
    if head_end < 0:
        return ("skip", "no </head> tag")

    new_src = src[:head_end] + IMPORTS + src[head_end:]
    if dry_run:
        return ("preview", f"would add {len(IMPORTS)}B before </head>")
    path.write_text(new_src, encoding="utf-8")
    return ("ok", f"added {len(IMPORTS)}B")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"Component lib import migration — {'DRY RUN' if args.dry_run else 'APPLY'}")
    print("=" * 60)

    summary = {"ok": 0, "noop": 0, "skip": 0, "preview": 0}
    for p in sorted(ROOT.glob("*.html")):
        status, msg = update(p, dry_run=args.dry_run)
        sym = {"ok": "✓", "noop": "·", "skip": "⏭", "preview": "→"}.get(status, "?")
        print(f"  {sym} {p.name:<35} {msg}")
        summary[status] = summary.get(status, 0) + 1
    print()
    print(f"Summary: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
