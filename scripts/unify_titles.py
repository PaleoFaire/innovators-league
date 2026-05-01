#!/usr/bin/env python3
"""
Unify <title> tags across all HTML pages to use the consistent
"<Page name> · The Innovators League" convention.

Removes the older "| ROS Startup Database | Rational Optimist Society"
suffix, keeping the page-specific name.

Usage:
  python scripts/unify_titles.py [--dry-run]
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Mapping: pattern → canonical title (just the page name).
# Anything not in the map gets a generic stripping pass.
EXPLICIT_TITLES = {
    "alerts.html":               "Deal Flow Alerts",
    "baskets.html":              "Public-Market Baskets",
    "brief.html":                "The Frontier Daily",
    "calendar.html":             "Industry Events Calendar",
    "captable.html":             "Cap Table Intelligence",
    "catalysts.html":            "Catalyst Calendar",
    "company.html":              "Company Profile",
    "compare.html":              "Company Comparison",
    "customers.html":            "Customer Intelligence",
    "discovery.html":            "Discovery Queue",
    "earnings-signals.html":     "Earnings Signals",
    "govradar.html":             "Government Demand Radar",
    "index.html":                "Companies Database",
    "investor-firm.html":        "Investor Profile",
    "investor-hub.html":         "Investor Hub",
    "investor-intelligence.html":"Investor Intelligence",
    "investors.html":            "Investors",
    "jobs.html":                 "Talent",
    "launches.html":             "Space Launch Manifest",
    "patents.html":              "Patent Velocity",
    "power-grid.html":           "Power Grid Intelligence",
    "regulatory.html":           "Regulatory Intelligence",
    "research.html":             "Deep Research",
    "sectors.html":              "Sector Explorer",
    "signals.html":              "Proprietary Signals",
    "terminal.html":             "Terminal",
    "transformation.html":       "Industry Transformation",
    "valuations.html":           "Valuation Intelligence",
    "visualizations.html":       "Insights & Data Viz",
}
SUFFIX = "The Innovators League"


def update(path, dry_run=False):
    src = path.read_text(encoding="utf-8")
    page_name = EXPLICIT_TITLES.get(path.name)
    if not page_name:
        return ("skip", "not in explicit map")

    new_title = f"<title>{page_name} · {SUFFIX}</title>"

    # Match the existing <title>...</title>
    new_src, n = re.subn(r"<title>[^<]*</title>", new_title, src, count=1)
    if n == 0:
        return ("skip", "no <title> tag")
    if new_src == src:
        return ("noop", "already correct")

    # Also update og:title to match (best-effort; only if pattern present)
    new_src = re.sub(
        r'<meta property="og:title" content="[^"]*"',
        f'<meta property="og:title" content="{page_name} · {SUFFIX}"',
        new_src,
        count=1,
    )

    if dry_run:
        return ("preview", f"would set: {page_name}")
    path.write_text(new_src, encoding="utf-8")
    return ("ok", f"set: {page_name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"Title unification — {'DRY RUN' if args.dry_run else 'APPLY'}")
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
