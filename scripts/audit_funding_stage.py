#!/usr/bin/env python3
"""
Audit fundingStage vs totalRaised for self-inconsistency.

Rule: each funding stage has a typical totalRaised range. If the two
fields disagree by a wide margin, the entry is likely wrong (someone
tagged a Seed company "SPAC" or a $2B unicorn "Pre-Seed").

Sparked by Stephen catching Galvanick: tagged "SPAC" but raised $16M
(an obvious mismatch since SPACs IPO with $100M+).

Usage:
  python scripts/audit_funding_stage.py [--top N]
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Typical totalRaised ranges per stage (USD). Companies outside these
# ranges are flagged. Ranges are intentionally generous to avoid noise.
STAGE_RANGES = {
    # Stage          → (min_typical_$, max_typical_$, severity_below, severity_above)
    "pre-seed":      (0,        5_000_000,    "low",    "medium"),
    "seed":          (500_000,  20_000_000,   "low",    "medium"),
    "series a":      (5_000_000, 60_000_000,  "low",    "medium"),
    "series b":      (15_000_000, 150_000_000, "low",   "medium"),
    "series c":      (40_000_000, 400_000_000, "medium", "low"),
    "series d":      (80_000_000, 1_000_000_000, "medium", "low"),
    "series e":      (150_000_000, 3_000_000_000, "high", "low"),
    "series f":      (200_000_000, 5_000_000_000, "high", "low"),
    "series g":      (300_000_000, 10_000_000_000, "high", "low"),
    "late stage":    (50_000_000, None,       "medium", None),
    "growth":        (50_000_000, None,       "medium", None),
    "spac":          (50_000_000, None,       "high",   None),    # SPACs IPO with $100M+ typically
    "ipo":           (50_000_000, None,       "high",   None),
    "public":        (50_000_000, None,       "medium", None),
    "pre-ipo":       (100_000_000, None,      "high",   None),
    "acquired":      (None,     None,         None,     None),    # any range OK
}


def parse_money(s):
    """Convert '$2.5B+' / '$50M' / '$104,500' to int dollars; None if unparseable."""
    if not s: return None
    s = str(s).strip().lstrip("~$").rstrip("+").replace(",", "")
    # Strip "USD" / "EUR" / etc.
    s = re.sub(r"\s*(USD|EUR|GBP|CAD|JPY)\s*$", "", s, flags=re.IGNORECASE)
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([KMBT]?)", s, re.IGNORECASE)
    if not m: return None
    val = float(m.group(1))
    suf = (m.group(2) or "").upper()
    return int(val * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[suf])


def parse_companies():
    src = (ROOT / "data.js").read_text(encoding="utf-8")
    m = re.search(r"const COMPANIES\s*=\s*\[", src)
    start = m.end() - 1
    depth = 0; in_str = False; str_q = None
    for i in range(start, len(src)):
        c = src[i]
        if in_str:
            if c == "\\": continue
            if c == str_q: in_str = False
        else:
            if c in ('"', "'", "`"):
                in_str = True; str_q = c
            elif c == "[": depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0: block = src[start:i+1]; break

    out = []
    obj_depth = 0; obj_start = None; in_str = False; str_q = None
    for i, c in enumerate(block):
        if in_str:
            if c == "\\": continue
            if c == str_q: in_str = False
        else:
            if c in ('"', "'", "`"):
                in_str = True; str_q = c
            elif c == "{":
                if obj_depth == 0: obj_start = i
                obj_depth += 1
            elif c == "}":
                obj_depth -= 1
                if obj_depth == 0 and obj_start is not None:
                    obj = block[obj_start:i+1]
                    nm = re.search(r'name:\s*"([^"]+)"', obj)
                    fs = re.search(r'fundingStage:\s*"([^"]*)"', obj)
                    tr = re.search(r'totalRaised:\s*"([^"]*)"', obj)
                    if nm and fs:
                        out.append({
                            "name": nm.group(1),
                            "fundingStage": fs.group(1),
                            "totalRaised": tr.group(1) if tr else "",
                        })
                    obj_start = None
    return out


def fmt_money(n):
    if n is None: return "?"
    if n >= 1e9:  return f"${n/1e9:.1f}B"
    if n >= 1e6:  return f"${n/1e6:.0f}M"
    if n >= 1e3:  return f"${n/1e3:.0f}K"
    return f"${n}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=80)
    args = ap.parse_args()

    print("=" * 64)
    print("Funding-stage consistency audit (vs totalRaised)")
    print("=" * 64)

    cos = parse_companies()
    print(f"  Companies: {len(cos)}")

    flagged = []
    no_total_raised = []
    for c in cos:
        stage = (c["fundingStage"] or "").strip().lower()
        if not stage:
            continue
        rng = STAGE_RANGES.get(stage)
        if not rng:
            # Unknown stage label — flag if not already covered
            continue
        amt = parse_money(c["totalRaised"])
        if amt is None:
            if c["totalRaised"]:
                no_total_raised.append(c)
            continue
        min_t, max_t, sev_below, sev_above = rng
        problem = None
        severity = None
        if min_t is not None and amt < min_t:
            problem = f"too low for {stage}: raised {fmt_money(amt)}, expected ≥{fmt_money(min_t)}"
            severity = sev_below
        elif max_t is not None and amt > max_t:
            problem = f"too high for {stage}: raised {fmt_money(amt)}, expected ≤{fmt_money(max_t)}"
            severity = sev_above
        if problem:
            flagged.append({**c, "problem": problem, "severity": severity, "amt": amt})

    # Sort: high severity first, then by amount-mismatch ratio
    sev_rank = {"high": 0, "medium": 1, "low": 2, None: 3}
    flagged.sort(key=lambda f: (sev_rank[f["severity"]], -f["amt"]))

    print(f"\n  ⚠ Mismatches: {len(flagged)}")
    print(f"     · high severity:   {sum(1 for f in flagged if f['severity']=='high')}")
    print(f"     · medium severity: {sum(1 for f in flagged if f['severity']=='medium')}")
    print(f"     · low severity:    {sum(1 for f in flagged if f['severity']=='low')}")
    print()

    if flagged:
        print(f"  {'Company':<32}  {'Stage':<14}  {'Raised':>9}  {'Severity':<8}  Issue")
        print("  " + "-" * 110)
        for f in flagged[:args.top]:
            print(f"  {f['name'][:30]:<32}  {f['fundingStage'][:12]:<14}  {fmt_money(f['amt']):>9}  {f['severity']:<8}  {f['problem']}")
        if len(flagged) > args.top:
            print(f"  ... and {len(flagged) - args.top} more")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
