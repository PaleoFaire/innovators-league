#!/usr/bin/env python3
"""
Headcount Estimator for The Innovators League
Estimates company headcount and growth trends from job posting data.
No API calls needed — pure computation from existing jobs data.

Methodology:
  - Base: open_positions / vacancy_rate = estimated_headcount
  - Vacancy rate calibrated per sector
  - Growth classification from job posting volume
  - Cross-reference with curated headcount estimates where available
"""

import json
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"

# Sector-specific vacancy rates (what % of workforce = open roles)
# Sources: BLS JOLTS, industry benchmarks
SECTOR_VACANCY_RATES = {
    "defense": 0.06,
    "space": 0.07,
    "nuclear": 0.05,
    "ai": 0.10,
    "robotics": 0.08,
    "biotech": 0.06,
    "climate": 0.07,
    "chips": 0.08,
    "energy": 0.06,
    "autonomous": 0.08,
    "transportation": 0.07,
    "manufacturing": 0.06,
    "sensors": 0.07,
    "semiconductor": 0.08,
    "quantum": 0.09,
}
DEFAULT_VACANCY_RATE = 0.07


def load_jobs_by_company():
    """Load job counts per company from jobs_stats.json."""
    stats_path = DATA_DIR / "jobs_stats.json"
    if stats_path.exists():
        with open(stats_path) as f:
            stats = json.load(f)
        return stats.get("byCompany", {})

    # Fallback: count from jobs_auto.js
    jobs_path = DATA_DIR / "jobs_auto.js"
    if not jobs_path.exists():
        return {}

    with open(jobs_path) as f:
        content = f.read()

    counts = defaultdict(int)
    for m in re.finditer(r'company:\s*"([^"]*)"', content):
        counts[m.group(1)] += 1
    return dict(counts)


def load_company_sectors():
    """Load company -> sector mapping from data.js."""
    if not DATA_JS_PATH.exists():
        return {}

    with open(DATA_JS_PATH) as f:
        content = f.read()

    sectors = {}
    # Match company entries in COMPANIES array
    for m in re.finditer(
        r'name:\s*"([^"]+)"[\s\S]*?sector:\s*"([^"]+)"',
        content
    ):
        sectors[m.group(1)] = m.group(2).lower()

    return sectors


def load_curated_headcounts():
    """Load any existing curated headcount data from data.js ALT_DATA_SIGNALS."""
    if not DATA_JS_PATH.exists():
        return {}

    with open(DATA_JS_PATH) as f:
        content = f.read()

    headcounts = {}
    # Try to find headcountEstimate fields in ALT_DATA_SIGNALS
    for m in re.finditer(
        r'company:\s*"([^"]+)"[\s\S]*?headcountEstimate:\s*"([^"]*)"',
        content
    ):
        company = m.group(1)
        estimate_str = m.group(2)
        # Parse "13,000+" -> 13000
        num = re.sub(r'[,+~]', '', estimate_str)
        try:
            headcounts[company] = int(num)
        except ValueError:
            pass

    return headcounts


def load_previous_estimates():
    """Load previous headcount estimates for trend calculation."""
    prev_path = DATA_DIR / "headcount_estimates_auto.json"
    if prev_path.exists():
        with open(prev_path) as f:
            data = json.load(f)
        return {item["company"]: item for item in data}
    return {}


def get_vacancy_rate(sector, curated_headcount=None, open_positions=None):
    """Get vacancy rate, calibrating against curated data if available."""
    if curated_headcount and open_positions and curated_headcount > 0:
        # Reverse-engineer vacancy rate from known headcount
        calibrated = open_positions / curated_headcount
        # Clamp to reasonable range
        return max(0.02, min(0.30, calibrated))

    # Use sector default
    return SECTOR_VACANCY_RATES.get(sector, DEFAULT_VACANCY_RATE)


def classify_hiring_velocity(open_positions):
    """Classify hiring velocity based on open positions."""
    if open_positions >= 200:
        return "surging"
    elif open_positions >= 50:
        return "rapid"
    elif open_positions >= 20:
        return "growing"
    elif open_positions >= 5:
        return "moderate"
    else:
        return "quiet"


def format_headcount(count):
    """Format headcount number for display."""
    if count >= 10000:
        return f"{count // 1000:,}K+"
    elif count >= 1000:
        return f"{count:,}+"
    elif count >= 100:
        # Round to nearest 50
        rounded = round(count / 50) * 50
        return f"{rounded}+"
    else:
        return f"{count}+"


def main():
    print("=" * 60)
    print("Headcount Estimator")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load all data sources
    job_counts = load_jobs_by_company()
    sectors = load_company_sectors()
    curated = load_curated_headcounts()
    previous = load_previous_estimates()

    print(f"Companies with job data: {len(job_counts)}")
    print(f"Companies with sector data: {len(sectors)}")
    print(f"Curated headcount anchors: {len(curated)}")
    print(f"Previous estimates: {len(previous)}")

    # Calculate estimates
    estimates = []
    for company, open_positions in sorted(job_counts.items(), key=lambda x: -x[1]):
        if open_positions < 1:
            continue

        sector = sectors.get(company, "unknown")
        curated_hc = curated.get(company)

        # Get calibrated vacancy rate
        vacancy_rate = get_vacancy_rate(sector, curated_hc, open_positions)

        # Estimate headcount
        estimated = round(open_positions / vacancy_rate)

        # Clamp: headcount should be at least open_positions * 2
        estimated = max(estimated, open_positions * 2)

        # If we have curated data, use it as primary (our estimate as secondary)
        display_headcount = curated_hc if curated_hc else estimated

        # Calculate growth trend vs previous
        growth_trend = ""
        prev = previous.get(company, {})
        if prev and prev.get("estimatedHeadcount", 0) > 0:
            prev_hc = prev["estimatedHeadcount"]
            delta = ((estimated - prev_hc) / prev_hc) * 100
            if abs(delta) >= 1:
                growth_trend = f"{delta:+.0f}%"

        hiring_velocity = classify_hiring_velocity(open_positions)

        estimates.append({
            "company": company,
            "openPositions": open_positions,
            "estimatedHeadcount": display_headcount,
            "headcountFormatted": format_headcount(display_headcount),
            "vacancyRate": round(vacancy_rate, 3),
            "hiringVelocity": hiring_velocity,
            "sector": sector,
            "growthTrend": growth_trend,
            "isCurated": bool(curated_hc),
            "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        })

    # Sort by estimated headcount descending
    estimates.sort(key=lambda x: x["estimatedHeadcount"], reverse=True)

    print(f"\nGenerated estimates for {len(estimates)} companies")

    # Save JSON
    json_path = DATA_DIR / "headcount_estimates_auto.json"
    with open(json_path, "w") as f:
        json.dump(estimates, f, indent=2)
    print(f"Saved JSON to {json_path}")

    # Generate JS snippet
    js_lines = [
        "// Auto-calculated headcount estimates from job posting data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "// Methodology: open_positions / sector_vacancy_rate, calibrated against known headcounts",
        "const HEADCOUNT_ESTIMATES_AUTO = [",
    ]

    for est in estimates:
        js_lines.append("  {")
        js_lines.append(f'    company: "{est["company"]}",')
        js_lines.append(f'    openPositions: {est["openPositions"]},')
        js_lines.append(f'    estimatedHeadcount: {est["estimatedHeadcount"]},')
        js_lines.append(f'    headcountFormatted: "{est["headcountFormatted"]}",')
        js_lines.append(f'    vacancyRate: {est["vacancyRate"]},')
        js_lines.append(f'    hiringVelocity: "{est["hiringVelocity"]}",')
        js_lines.append(f'    sector: "{est["sector"]}",')
        js_lines.append(f'    growthTrend: "{est["growthTrend"]}",')
        js_lines.append(f'    isCurated: {"true" if est["isCurated"] else "false"},')
        js_lines.append(f'    lastUpdated: "{est["lastUpdated"]}",')
        js_lines.append("  },")

    js_lines.append("];")

    js_path = DATA_DIR / "headcount_estimates_auto.js"
    with open(js_path, "w") as f:
        f.write("\n".join(js_lines))
    print(f"Saved JS to {js_path}")

    # Print top 15
    if estimates:
        print(f"\nTop 15 by Estimated Headcount:")
        print(f"  {'Company':35s} {'Open Jobs':>10s} {'Est. HC':>10s} {'Velocity':>10s}")
        print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*10}")
        for est in estimates[:15]:
            print(f"  {est['company']:35s} {est['openPositions']:>10,d} {est['headcountFormatted']:>10s} {est['hiringVelocity']:>10s}")

    print("=" * 60)


if __name__ == "__main__":
    main()
