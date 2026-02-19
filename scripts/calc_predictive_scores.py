#!/usr/bin/env python3
"""
Predictive Scores Calculator for The Innovators League
Auto-generates IPO Readiness, M&A Target, Failure Risk, and Next Round predictions
for all companies using available data sources.

Preserves manually curated predictions for companies that already have them.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"


def load_json(filename):
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath) as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_company_data():
    """Extract company names, sectors, stages, funding info from data.js."""
    with open(DATA_JS_PATH) as f:
        content = f.read()

    # Find all company names first, then extract fields per company
    # Split COMPANIES array into individual entries using name: as delimiter
    companies = []
    name_positions = [(m.start(), m.group(1)) for m in re.finditer(r'name:\s*"([^"]+)"', content)]

    for i, (pos, name) in enumerate(name_positions):
        # Get text from this name to the next name (or 2000 chars)
        end = name_positions[i + 1][0] if i + 1 < len(name_positions) else pos + 2000
        block = content[pos:end]

        # Extract fields from this block (looking within a reasonable window)
        sector_m = re.search(r'sector:\s*"([^"]*)"', block)
        stage_m = re.search(r'fundingStage:\s*"([^"]*)"', block)
        raised_m = re.search(r'totalRaised:\s*"([^"]*)"', block)
        val_m = re.search(r'valuation:\s*"([^"]*)"', block)

        companies.append({
            "name": name,
            "sector": sector_m.group(1) if sector_m else "",
            "stage": stage_m.group(1) if stage_m else "",
            "totalRaised": raised_m.group(1) if raised_m else "",
            "valuation": val_m.group(1) if val_m else "",
        })

    # Deduplicate
    seen = set()
    unique = []
    for c in companies:
        if c["name"] not in seen:
            seen.add(c["name"])
            unique.append(c)
    return unique


def parse_money(val_str):
    """Parse strings like '$2.5B+', '$500M', '$150K' into numbers."""
    if not val_str or not isinstance(val_str, str):
        return 0
    val_str = val_str.replace("+", "").replace("~", "").replace(",", "").strip()
    match = re.search(r'\$?([\d.]+)\s*(T|B|M|K)?', val_str, re.IGNORECASE)
    if not match:
        return 0
    num = float(match.group(1))
    unit = (match.group(2) or "").upper()
    if unit == "T":
        return num * 1e12
    elif unit == "B":
        return num * 1e9
    elif unit == "M":
        return num * 1e6
    elif unit == "K":
        return num * 1e3
    return num


def count_by_company(data, key="company"):
    counts = defaultdict(int)
    for item in data:
        if isinstance(item, dict) and key in item:
            counts[item[key]] += 1
    return counts


def count_jobs(filename="jobs_auto.js"):
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return {}
    with open(filepath) as f:
        content = f.read()
    counts = defaultdict(int)
    for match in re.finditer(r'company:\s*"([^"]+)"', content):
        counts[match.group(1)] += 1
    return counts


def get_sector_momentum():
    data = load_json("sector_momentum_auto.json")
    return {d["sector"]: d.get("momentum", 50) for d in data if isinstance(d, dict) and "sector" in d}


def get_curated_predictions():
    """Extract existing curated PREDICTIVE_SCORES companies from data.js."""
    curated = {"ipoReadiness": {}, "maTarget": {}, "failureRisk": {}, "nextRound": {}}
    with open(DATA_JS_PATH) as f:
        content = f.read()

    # Find PREDICTIVE_SCORES block
    ps_match = re.search(r'const PREDICTIVE_SCORES\s*=\s*\{([\s\S]*?)\n\};', content)
    if not ps_match:
        return curated

    block = ps_match.group(1)

    # For each category, find company entries
    for category in curated.keys():
        cat_match = re.search(rf'{category}:\s*\{{[\s\S]*?companies:\s*\{{([\s\S]*?)\n\s*\}}\s*\}}', block)
        if cat_match:
            companies_block = cat_match.group(1)
            for company_match in re.finditer(r'"([^"]+)":\s*\{[^}]+\}', companies_block):
                curated[category][company_match.group(1)] = True  # Mark as curated

    return curated


def clamp(val, lo=0, hi=100):
    return max(lo, min(hi, round(val)))


def calc_ipo_readiness(company, stage, raised, valuation, job_count, sector_mom, patent_count, news_count):
    """IPO Readiness Score (0-100). Only for private late-stage companies."""
    is_public = any(s in stage.lower() for s in ["public", "ipo"])
    if is_public:
        return None  # Skip public companies

    # Only meaningful for Series C+
    late_stages = ["series c", "series d", "series e", "series f", "series g", "late", "pre-ipo"]
    is_late = any(s in stage.lower() for s in late_stages)
    if not is_late and raised < 100e6:
        return None  # Too early

    # Revenue scale proxy (20%) - use job count as proxy
    if job_count >= 500:
        revenue_score = 85
    elif job_count >= 200:
        revenue_score = 70
    elif job_count >= 50:
        revenue_score = 55
    elif job_count >= 20:
        revenue_score = 40
    else:
        revenue_score = 25

    # Revenue growth proxy (15%) - news activity as proxy
    growth_score = min(80, 30 + news_count * 5)

    # Profitability path (15%)
    if raised > 0 and valuation > 0:
        prof_score = min(80, (valuation / max(raised, 1)) * 10)
    else:
        prof_score = 40

    # Governance readiness (10%) - stage-based
    stage_gov = {"series g": 80, "series f": 75, "series e": 70, "series d": 60, "series c": 50, "pre-ipo": 85}
    gov_score = 50
    for s, v in stage_gov.items():
        if s in stage.lower():
            gov_score = v
            break

    # Market conditions (15%) - sector momentum
    market_score = sector_mom * 0.8

    # Investor pressure (10%) - later stage = more pressure
    pressure_map = {"series g": 80, "series f": 70, "series e": 60, "series d": 50, "pre-ipo": 90}
    pressure_score = 40
    for s, v in pressure_map.items():
        if s in stage.lower():
            pressure_score = v
            break

    # Competitive position (10%) - patents + news
    comp_score = min(80, 30 + patent_count * 2 + news_count * 3)

    # Regulatory clearance (5%)
    reg_score = 70  # Default neutral

    composite = (revenue_score * 0.20 + growth_score * 0.15 + prof_score * 0.15 +
                 gov_score * 0.10 + market_score * 0.15 + pressure_score * 0.10 +
                 comp_score * 0.10 + reg_score * 0.05)

    return {
        "score": clamp(composite),
        "trend": "up" if news_count >= 3 else "stable",
        "factors": {
            "revenueScale": clamp(revenue_score),
            "revenueGrowth": clamp(growth_score),
            "profitability": clamp(prof_score),
            "governance": clamp(gov_score),
            "marketConditions": clamp(market_score),
            "investorPressure": clamp(pressure_score),
            "competitivePosition": clamp(comp_score),
            "regulatory": clamp(reg_score),
        },
        "analysis": f"Auto-scored based on {stage} stage, {job_count} jobs, {patent_count} patents, sector momentum {sector_mom:.0f}/100.",
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
    }


def calc_ma_target(company, stage, raised, valuation, patent_count, sector, gov_count):
    """M&A Target Score (0-100)."""
    is_public = any(s in stage.lower() for s in ["public", "ipo"])

    # Strategic value (25%) - patents + unique tech
    strategic = min(90, 30 + patent_count * 3)

    # Acquirer landscape (20%) - sector-based
    active_ma_sectors = {"AI & Software": 75, "Biotech & Health": 70, "Robotics & Manufacturing": 65,
                         "Defense & Security": 50, "Space & Aerospace": 45}
    acquirer_score = 50
    for s, v in active_ma_sectors.items():
        if s.lower() in sector.lower() or sector.lower() in s.lower():
            acquirer_score = v
            break

    # Valuation attractiveness (15%) - lower = more attractive target
    if valuation > 0:
        if valuation < 500e6:
            val_score = 80
        elif valuation < 2e9:
            val_score = 65
        elif valuation < 10e9:
            val_score = 50
        else:
            val_score = 30  # Too expensive for most acquirers
    else:
        val_score = 60

    # Founder intent (15%) - early stage founders less likely to sell
    early_stages = ["seed", "pre-seed", "series a"]
    if any(s in stage.lower() for s in early_stages):
        intent_score = 30
    elif is_public:
        intent_score = 55
    else:
        intent_score = 60

    # Competitive pressure (10%)
    comp_score = 50  # neutral default

    # Integration complexity (10%)
    if is_public:
        integration = 40  # Public M&A is complex
    elif raised > 1e9:
        integration = 45
    else:
        integration = 65

    # Regulatory risk (5%)
    reg_risk = 60 if gov_count == 0 else 40  # Gov contractors face CFIUS review

    composite = (strategic * 0.25 + acquirer_score * 0.20 + val_score * 0.15 +
                 intent_score * 0.15 + comp_score * 0.10 + integration * 0.10 + reg_risk * 0.05)

    return {
        "score": clamp(composite),
        "trend": "stable",
        "potentialAcquirers": [],
        "analysis": f"Auto-scored: {sector}, {stage}, {patent_count} patents.",
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
    }


def calc_failure_risk(company, stage, raised, job_count, news_count, sector_mom, gov_count):
    """Failure Risk Score (0-100, higher = more risk)."""
    is_public = any(s in stage.lower() for s in ["public", "ipo"])
    if is_public:
        return None  # Public companies rarely "fail" in the startup sense

    # Runway proxy (25%) - stage + funding
    if raised >= 1e9:
        runway_risk = 10
    elif raised >= 500e6:
        runway_risk = 20
    elif raised >= 100e6:
        runway_risk = 30
    elif raised >= 50e6:
        runway_risk = 45
    elif raised >= 10e6:
        runway_risk = 60
    else:
        runway_risk = 75

    # Burn multiple proxy (20%) - jobs vs funding
    if raised > 0 and job_count > 0:
        burn_ratio = job_count / (raised / 1e6)  # jobs per $M raised
        if burn_ratio > 5:
            burn_risk = 70  # hiring aggressively relative to funding
        elif burn_ratio > 2:
            burn_risk = 50
        elif burn_ratio > 0.5:
            burn_risk = 30
        else:
            burn_risk = 20
    else:
        burn_risk = 50  # neutral

    # Revenue trajectory (15%)
    if news_count >= 5:
        rev_risk = 25  # lots of press = likely traction
    elif news_count >= 2:
        rev_risk = 40
    else:
        rev_risk = 60

    # Market position (15%)
    market_risk = max(10, 100 - sector_mom)

    # Funding environment (10%)
    funding_risk = max(10, 80 - sector_mom * 0.6)

    # Customer concentration (10%)
    if gov_count >= 5:
        concentration_risk = 30  # diversified gov customer base
    elif gov_count >= 1:
        concentration_risk = 45
    else:
        concentration_risk = 55

    # Team stability (5%)
    team_risk = 40  # neutral default

    composite = (runway_risk * 0.25 + burn_risk * 0.20 + rev_risk * 0.15 +
                 market_risk * 0.15 + funding_risk * 0.10 + concentration_risk * 0.10 + team_risk * 0.05)

    # Determine runway label
    if raised >= 1e9:
        runway = "36+ months"
    elif raised >= 500e6:
        runway = "24-36 months"
    elif raised >= 100e6:
        runway = "18-24 months"
    elif raised >= 50e6:
        runway = "12-18 months"
    else:
        runway = "6-12 months"

    return {
        "score": clamp(composite),
        "trend": "down" if news_count >= 3 else "stable",
        "runway": runway,
        "analysis": f"Auto-scored: ${raised/1e6:.0f}M raised, {job_count} jobs, {stage}.",
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
    }


def calc_next_round(company, stage, raised, valuation, job_count, sector):
    """Next Round Prediction. For private companies."""
    is_public = any(s in stage.lower() for s in ["public", "ipo"])
    if is_public:
        return None

    # Determine next round name and typical size
    round_progression = {
        "pre-seed": ("Seed", "$2-5M", "$15-30M"),
        "seed": ("Series A", "$10-20M", "$50-100M"),
        "series a": ("Series B", "$30-60M", "$150-300M"),
        "series b": ("Series C", "$50-150M", "$500M-1B"),
        "series c": ("Series D", "$100-300M", "$1-3B"),
        "series d": ("Series E", "$200-500M", "$3-8B"),
        "series e": ("Series F", "$300-700M", "$5-15B"),
        "series f": ("Series G", "$500M-1B", "$10-30B"),
        "series g": ("Pre-IPO/IPO", "$500M-2B", "$20-50B"),
    }

    next_round = "Unknown"
    predicted_size = "$TBD"
    predicted_val = "$TBD"

    for s, (nr, size, val) in round_progression.items():
        if s in stage.lower():
            next_round = nr
            predicted_size = size
            predicted_val = val
            break

    # Confidence based on data availability
    confidence = 30
    if job_count >= 10:
        confidence += 15
    if raised > 0:
        confidence += 15
    if valuation > 0:
        confidence += 10

    return {
        "predictedTiming": "H2 2026",
        "confidence": min(85, confidence),
        "predictedSize": predicted_size,
        "predictedValuation": predicted_val,
        "likelyInvestors": [],
        "catalyst": f"Growth trajectory and {stage} stage momentum",
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
    }


def main():
    print("=" * 60)
    print("PREDICTIVE SCORES CALCULATOR")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load data
    companies = get_company_data()
    print(f"Companies found: {len(companies)}")

    curated = get_curated_predictions()
    print(f"Curated entries: IPO={len(curated['ipoReadiness'])}, "
          f"M&A={len(curated['maTarget'])}, Risk={len(curated['failureRisk'])}, "
          f"Round={len(curated['nextRound'])}")

    # Load data sources
    patent_data = []
    patent_path = DATA_DIR / "patent_intel_auto.js"
    if patent_path.exists():
        with open(patent_path) as f:
            for m in re.finditer(r'company:\s*"([^"]+)"[^}]*?(?:patentCount|recentPatents):\s*(\d+)', f.read()):
                patent_data.append((m.group(1), int(m.group(2))))
    patent_counts = dict(patent_data)

    news_data = load_json("news_raw.json")
    news_counts = count_by_company(news_data, "matchedCompany")

    job_counts = count_jobs()

    sector_momentum = get_sector_momentum()

    gov_data_raw = []
    gov_path = DATA_DIR / "gov_contracts_auto.js"
    if gov_path.exists():
        with open(gov_path) as f:
            for m in re.finditer(r'company:\s*"([^"]+)"', f.read()):
                gov_data_raw.append({"company": m.group(1)})
    gov_counts = count_by_company(gov_data_raw)

    # Calculate scores
    ipo_results = {}
    ma_results = {}
    risk_results = {}
    round_results = {}

    for c in companies:
        name = c["name"]
        stage = c["stage"]
        raised = parse_money(c["totalRaised"])
        valuation = parse_money(c["valuation"])
        jobs = job_counts.get(name, 0)
        news = news_counts.get(name, 0)
        patents = patent_counts.get(name, 0)
        sector = c["sector"]
        sector_mom = sector_momentum.get(sector, 50)
        gov = gov_counts.get(name, 0)

        # IPO Readiness
        if name not in curated["ipoReadiness"]:
            ipo = calc_ipo_readiness(name, stage, raised, valuation, jobs, sector_mom, patents, news)
            if ipo:
                ipo_results[name] = ipo
        
        # M&A Target
        if name not in curated["maTarget"]:
            ma = calc_ma_target(name, stage, raised, valuation, patents, sector, gov)
            if ma:
                ma_results[name] = ma

        # Failure Risk
        if name not in curated["failureRisk"]:
            risk = calc_failure_risk(name, stage, raised, jobs, news, sector_mom, gov)
            if risk:
                risk_results[name] = risk

        # Next Round
        if name not in curated["nextRound"]:
            nr = calc_next_round(name, stage, raised, valuation, jobs, sector)
            if nr:
                round_results[name] = nr

    # Save output
    output = {
        "ipoReadiness": ipo_results,
        "maTarget": ma_results,
        "failureRisk": risk_results,
        "nextRound": round_results,
    }

    output_path = DATA_DIR / "predictive_scores_auto.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"RESULTS:")
    print(f"  IPO Readiness: {len(ipo_results)} companies")
    print(f"  M&A Target: {len(ma_results)} companies")
    print(f"  Failure Risk: {len(risk_results)} companies")
    print(f"  Next Round: {len(round_results)} companies")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
