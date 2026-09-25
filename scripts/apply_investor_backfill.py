#!/usr/bin/env python3
"""
Apply the VC Portfolio Watcher's investor back-fill to data.js.

The watcher (scripts/fetch_vc_portfolio_watcher.py) writes
data/vc_portfolio_investor_backfill.json: companies we track that a fund lists
on its own portfolio page but whose `investors` field does not name that fund.
This script appends the fund's canonical name to each such record.

Only matches made by website domain or exact name are applied. Stem matches
("Vantage" -> "Vantage Robotics") are printed for a human and skipped unless
--include-stem is passed.

Usage
─────
  python3 scripts/apply_investor_backfill.py            # dry run: show what would change
  python3 scripts/apply_investor_backfill.py --apply    # write data.js
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "data.js"
BACKFILL = ROOT / "data" / "vc_portfolio_investor_backfill.json"

sys.path.insert(0, str(ROOT / "scripts"))
from fetch_vc_portfolio_watcher import FUNDS  # noqa: E402


def scan_block(src: str, start: int, open_ch: str, close_ch: str) -> int:
    """Index just past the bracket that closes the one at `start`, string-aware."""
    depth, i, n = 0, start, len(src)
    while i < n:
        ch = src[i]
        if ch in "\"'`":
            q = ch
            i += 1
            while i < n and src[i] != q:
                i += 2 if src[i] == "\\" else 1
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced")


def record_span(src: str, lo: int, hi: int, name: str) -> tuple[int, int] | None:
    """(start, end) of the COMPANIES object whose name is `name`, or None."""
    needle = f'name: "{name}"'
    pos = src.find(needle, lo, hi)
    if pos < 0:
        needle = f"name: '{name}'"
        pos = src.find(needle, lo, hi)
        if pos < 0:
            return None
    start = src.rfind("{", lo, pos)
    end = scan_block(src, start, "{", "}")
    return start, end


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write data.js (default is a dry run)")
    ap.add_argument("--include-stem", action="store_true", help="also apply stem-only name matches")
    args = ap.parse_args()

    items = json.loads(BACKFILL.read_text()).get("items", [])
    src = DATA_JS.read_text()
    m = re.search(r"const COMPANIES\s*=\s*\[", src)
    lo = m.end() - 1
    hi = scan_block(src, lo, "[", "]")

    ok_kinds = {"domain", "exact-name"} | ({"stem"} if args.include_stem else set())
    applied, skipped, missing, no_field = [], [], [], []
    # apply from the end of the file backwards so earlier offsets stay valid
    plan = []
    for it in items:
        if it["matched_by"] not in ok_kinds:
            skipped.append(it)
            continue
        span = record_span(src, lo, hi, it["company"])
        if not span:
            missing.append(it)
            continue
        plan.append((span, it))
    plan.sort(key=lambda t: -t[0][0])

    for (start, end), it in plan:
        rec = src[start:end]
        im = re.search(r"investors:\s*\[", rec)
        if not im:
            no_field.append(it)
            continue
        arr_start = start + im.end() - 1
        arr_end = scan_block(src, arr_start, "[", "]")
        inner = src[arr_start + 1:arr_end - 1]
        have = " | ".join(re.findall(r'"((?:[^"\\]|\\.)*)"', inner)).lower()
        alias = FUNDS[it["fund"]]["alias"]
        if re.search(alias, have):
            continue                                    # already there under another spelling
        new = f'"{it["add"]}"'
        if not inner.strip():
            new_inner = new
        elif "\n" not in inner:
            new_inner = inner.rstrip() + ", " + new
        else:
            last_q = inner.rfind('"')
            indent = re.search(r"\n([ \t]*)\S", inner[:last_q][::-1] and inner) or None
            ind = re.findall(r"\n([ \t]*)\"", inner)
            pad = ind[-1] if ind else "      "
            new_inner = inner[:last_q + 1] + ",\n" + pad + new + inner[last_q + 1:]
        src = src[:arr_start + 1] + new_inner + src[arr_end - 1:]
        applied.append(it)

    print(f"{len(applied)} to apply · {len(skipped)} stem-only skipped · {len(missing)} records not found"
          f" · {len(no_field)} without an investors field")
    for it in applied:
        print(f"  + {it['company']:<34} {it['add']:<26} ({it['matched_by']}, {it['fund']})")
    if skipped:
        print("\nskipped (stem match, check by hand):")
        for it in skipped:
            print(f"  ? {it['company']:<34} {it['add']:<26} via {it['evidence']}")
    if args.apply and applied:
        DATA_JS.write_text(src)
        print(f"\nwrote {DATA_JS.name}")
    elif applied:
        print("\ndry run — pass --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
