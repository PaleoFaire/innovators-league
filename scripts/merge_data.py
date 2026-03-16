#!/usr/bin/env python3
"""
Data Merger for The Innovators League
Merges auto-generated data from various sources into data.js
"""

import json
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"

def load_json(filename):
    """Load JSON data from the data directory."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return []

def format_js_array(name, data, indent=2):
    """Format Python data as a JavaScript array."""
    lines = [f"const {name} = ["]

    for item in data:
        item_lines = []
        item_lines.append("  {")

        for key, value in item.items():
            if isinstance(value, str):
                # Escape quotes and newlines
                escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
                item_lines.append(f'    {key}: "{escaped}",')
            elif isinstance(value, bool):
                item_lines.append(f'    {key}: {"true" if value else "false"},')
            elif isinstance(value, (int, float)):
                item_lines.append(f'    {key}: {value},')
            elif isinstance(value, list):
                item_lines.append(f'    {key}: {json.dumps(value)},')
            elif value is None:
                item_lines.append(f'    {key}: null,')

        item_lines.append("  },")
        lines.extend(item_lines)

    lines.append("];")
    return "\n".join(lines)

def update_sec_filings(data_js_content):
    """Update SEC_FILINGS_LIVE in data.js."""
    filings = load_json("sec_filings_recent.json")
    if not filings:
        print("No SEC filings data found, skipping...")
        return data_js_content

    print(f"Merging {len(filings)} SEC filings...")

    # Generate new SEC_FILINGS_LIVE block
    js_array = "// Auto-updated SEC filings from EDGAR\n"
    js_array += f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n"
    js_array += "const SEC_FILINGS_LIVE = [\n"

    for f in filings[:40]:
        desc = f.get("description", f.get("form", "")).replace('"', "'")
        js_array += f'  {{ company: "{f["company"]}", form: "{f["form"]}", date: "{f["date"]}", '
        js_array += f'description: "{desc}", isIPO: {"true" if f.get("isIPO") else "false"}, '
        js_array += f'ticker: "{f.get("ticker", "")}" }},\n'

    js_array += "];"

    # Replace existing SEC_FILINGS_LIVE
    pattern = r'const SEC_FILINGS_LIVE = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print("  Updated SEC_FILINGS_LIVE")
    else:
        print("  SEC_FILINGS_LIVE not found in data.js")

    return data_js_content

def update_company_signals(data_js_content):
    """Update COMPANY_SIGNALS in data.js with fresh news."""
    signals = load_json("news_raw.json")
    if not signals:
        print("No news signals data found, skipping...")
        return data_js_content

    print(f"Merging {len(signals)} news signals...")

    # Convert to COMPANY_SIGNALS format
    formatted_signals = []
    for i, s in enumerate(signals[:15]):
        formatted_signals.append({
            "id": i + 1,
            "type": s.get("type", "news"),
            "company": s.get("matchedCompany", ""),
            "headline": s.get("title", "")[:120].replace('"', "'"),
            "source": s.get("source", ""),
            "time": s.get("time", ""),
            "impact": s.get("impact", "medium"),
            "unread": i < 5
        })

    # Generate JS block
    js_array = "// Auto-generated real-time signals\n"
    js_array += f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n"
    js_array += "const COMPANY_SIGNALS = [\n"

    for s in formatted_signals:
        js_array += f'  {{ id: {s["id"]}, type: "{s["type"]}", company: "{s["company"]}", '
        js_array += f'headline: "{s["headline"]}", source: "{s["source"]}", '
        js_array += f'time: "{s["time"]}", impact: "{s["impact"]}", '
        js_array += f'unread: {"true" if s["unread"] else "false"} }},\n'

    js_array += "];"

    # Replace existing COMPANY_SIGNALS
    pattern = r'const COMPANY_SIGNALS = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print("  Updated COMPANY_SIGNALS")
    else:
        print("  COMPANY_SIGNALS not found in data.js")

    return data_js_content

def update_gov_contracts(data_js_content):
    """Update GOV_CONTRACTS in data.js with fresh USAspending data."""
    contracts = load_json("gov_contracts_aggregated.json")
    if not contracts:
        print("No gov contracts data found, skipping...")
        return data_js_content

    print(f"Merging {len(contracts)} gov contract records...")

    today = datetime.now().strftime("%Y-%m-%d")
    js_array = "// Auto-updated government contracts from USAspending\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "const GOV_CONTRACTS = [\n"

    for c in contracts:
        company = c.get("company", "").replace('"', "'")
        total_val = c.get("totalGovValue", "$0").replace('"', "'")
        count = c.get("contractCount", 0)
        agencies = json.dumps(c.get("agencies", []))
        last_updated = c.get("lastUpdated", today)
        js_array += f'  {{ company: "{company}", totalGovValue: "{total_val}", '
        js_array += f'contractCount: {count}, agencies: {agencies}, '
        js_array += f'lastUpdated: "{last_updated}" }},\n'

    js_array += "];"

    # Replace existing GOV_CONTRACTS (but not GOV_CONTRACTS_AUTO)
    pattern = r'const GOV_CONTRACTS = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print("  Updated GOV_CONTRACTS")
    else:
        print("  GOV_CONTRACTS not found in data.js")

    return data_js_content


def update_deal_tracker(data_js_content):
    """Update DEAL_TRACKER in data.js with fresh deal data."""
    deals = load_json("deals_auto.json")
    if not deals:
        print("No deals data found, skipping...")
        return data_js_content

    print(f"Merging {len(deals)} deal records...")

    today = datetime.now().strftime("%Y-%m-%d")
    js_array = "// Auto-updated deal flow from RSS + Crunchbase\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "const DEAL_TRACKER = [\n"

    for d in deals:
        company = d.get("company", "").replace('"', "'")
        investor = d.get("investor", "").replace('"', "'")
        amount = d.get("amount", "").replace('"', "'")
        rnd = d.get("round", "").replace('"', "'")
        date = d.get("date", "")
        valuation = d.get("valuation", "").replace('"', "'")
        role = d.get("leadOrParticipant", "lead")
        js_array += f'  {{ company: "{company}", investor: "{investor}", amount: "{amount}", '
        js_array += f'round: "{rnd}", date: "{date}", valuation: "{valuation}", '
        js_array += f'leadOrParticipant: "{role}" }},\n'

    js_array += "];"

    pattern = r'const DEAL_TRACKER = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print("  Updated DEAL_TRACKER")
    else:
        print("  DEAL_TRACKER not found in data.js")

    return data_js_content


def update_sector_momentum(data_js_content):
    """Update SECTOR_MOMENTUM in data.js with calculated scores."""
    momentum = load_json("sector_momentum_auto.json")
    if not momentum:
        print("No sector momentum data found, skipping...")
        return data_js_content

    print(f"Merging {len(momentum)} sector momentum scores...")

    today = datetime.now().strftime("%Y-%m-%d")
    js_array = "// Auto-calculated sector momentum scores\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "// Methodology: Funding velocity (35%) + News frequency (25%) + Hiring velocity (20%) + Market sentiment (20%)\n"
    js_array += "const SECTOR_MOMENTUM = [\n"

    for s in momentum:
        sector = s.get("sector", "").replace('"', "'")
        score = s.get("momentum", 50)
        trend = s.get("trend", "steady")
        catalysts = json.dumps(s.get("catalysts", []))
        funding_q = s.get("fundingQ", "$0M").replace('"', "'")
        js_array += f'  {{ sector: "{sector}", momentum: {score}, trend: "{trend}", '
        js_array += f'catalysts: {catalysts}, fundingQ: "{funding_q}" }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const SECTOR_MOMENTUM = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print("  Updated SECTOR_MOMENTUM")
    else:
        print("  SECTOR_MOMENTUM not found in data.js")

    return data_js_content


def update_ipo_pipeline(data_js_content):
    """Update IPO_PIPELINE in data.js."""
    pipeline = load_json("ipo_pipeline_auto.json")
    if not pipeline:
        print("No IPO pipeline data found, skipping...")
        return data_js_content

    print(f"Merging {len(pipeline)} IPO pipeline entries...")
    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-updated IPO pipeline — Last updated: {today}\n"
    js_array += "const IPO_PIPELINE = [\n"

    for e in pipeline:
        company = e.get("company", "").replace('"', "'")
        status = e.get("status", "").replace('"', "'")
        likelihood = e.get("likelihood", "medium")
        est_date = e.get("estimatedDate", "").replace('"', "'")
        est_val = e.get("estimatedValuation", "").replace('"', "'")
        sector = e.get("sector", "").replace('"', "'")
        js_array += f'  {{ company: "{company}", status: "{status}", likelihood: "{likelihood}", '
        js_array += f'estimatedDate: "{est_date}", estimatedValuation: "{est_val}", sector: "{sector}" }},\n'

    js_array += "];"

    pattern = r'const IPO_PIPELINE = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print("  Updated IPO_PIPELINE")
    else:
        print("  IPO_PIPELINE not found in data.js")

    return data_js_content


def update_revenue_intel(data_js_content):
    """Update REVENUE_INTEL in data.js."""
    revenue = load_json("revenue_intel_auto.json")
    if not revenue:
        print("No revenue intel data found, skipping...")
        return data_js_content

    print(f"Merging {len(revenue)} revenue entries...")
    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-updated revenue intelligence — Last updated: {today}\n"
    js_array += "const REVENUE_INTEL = [\n"

    for r in revenue:
        company = r.get("company", "").replace('"', "'")
        rev = r.get("revenue", "").replace('"', "'")
        period = r.get("period", "").replace('"', "'")
        growth = r.get("growth", "").replace('"', "'")
        source = r.get("source", "").replace('"', "'")
        js_array += f'  {{ company: "{company}", revenue: "{rev}", '
        js_array += f'period: "{period}", growth: "{growth}", source: "{source}" }},\n'

    js_array += "];"

    pattern = r'const REVENUE_INTEL = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print("  Updated REVENUE_INTEL")
    else:
        print("  REVENUE_INTEL not found in data.js")

    return data_js_content


def update_growth_signals(data_js_content):
    """Update GROWTH_SIGNALS in data.js."""
    signals = load_json("growth_signals_auto.json")
    if not signals:
        print("No growth signals data found, skipping...")
        return data_js_content

    print(f"Merging {len(signals)} growth signals...")
    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-calculated growth signals — Last updated: {today}\n"
    js_array += "const GROWTH_SIGNALS = [\n"

    for s in signals[:100]:  # Cap at 100
        company = s.get("company", "").replace('"', "'")
        sig_type = s.get("type", "").replace('"', "'")
        detail = s.get("detail", "").replace('"', "'")
        strength = s.get("strength", 0)
        date = s.get("date", today)
        js_array += f'  {{ company: "{company}", type: "{sig_type}", '
        js_array += f'detail: "{detail}", strength: {strength}, date: "{date}" }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const GROWTH_SIGNALS = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print("  Updated GROWTH_SIGNALS")
    else:
        print("  GROWTH_SIGNALS not found in data.js")

    return data_js_content


def update_funding_tracker(data_js_content):
    """Update FUNDING_TRACKER in data.js."""
    tracker = load_json("funding_tracker_auto.json")
    if not tracker:
        print("No funding tracker data found, skipping...")
        return data_js_content

    print(f"Merging {len(tracker)} funding tracker entries...")
    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-calculated funding tracker — Last updated: {today}\n"
    js_array += "const FUNDING_TRACKER = [\n"

    for t in tracker:
        company = t.get("company", "").replace('"', "'")
        total = t.get("totalRaised", "").replace('"', "'")
        last_round = t.get("lastRound", "").replace('"', "'")
        last_amount = t.get("lastRoundAmount", "").replace('"', "'")
        last_date = t.get("lastRoundDate", "")
        valuation = t.get("valuation", "").replace('"', "'")
        investors = json.dumps(t.get("leadInvestors", []))
        js_array += f'  {{ company: "{company}", totalRaised: "{total}", '
        js_array += f'lastRound: "{last_round}", lastRoundAmount: "{last_amount}", '
        js_array += f'lastRoundDate: "{last_date}", valuation: "{valuation}", '
        js_array += f'leadInvestors: {investors} }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const FUNDING_TRACKER = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print("  Updated FUNDING_TRACKER")
    else:
        print("  FUNDING_TRACKER not found in data.js")

    return data_js_content


def update_valuation_benchmarks(data_js_content):
    """Update VALUATION_BENCHMARKS in data.js."""
    benchmarks = load_json("valuation_benchmarks_auto.json")
    if not benchmarks:
        print("No valuation benchmarks data found, skipping...")
        return data_js_content

    print(f"Merging {len(benchmarks)} valuation benchmarks...")
    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-calculated valuation benchmarks — Last updated: {today}\n"
    js_array += "const VALUATION_BENCHMARKS = [\n"

    for b in benchmarks:
        company = b.get("company", "").replace('"', "'")
        val = b.get("valuation", "N/A").replace('"', "'")
        val_raw = b.get("valuationRaw", 0)
        source = b.get("source", "").replace('"', "'")
        ticker = b.get("ticker") or ""
        day_change = b.get("dayChange") or ""
        rev_mult = b.get("revenueMultiple", "")
        revenue = b.get("revenue", "").replace('"', "'")
        js_array += f'  {{ company: "{company}", valuation: "{val}", valuationRaw: {val_raw}, '
        js_array += f'source: "{source}", ticker: "{ticker}", dayChange: "{day_change}", '
        js_array += f'revenueMultiple: "{rev_mult}", revenue: "{revenue}" }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const VALUATION_BENCHMARKS = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print("  Updated VALUATION_BENCHMARKS")
    else:
        print("  VALUATION_BENCHMARKS not found in data.js")

    return data_js_content


def update_innovator_scores(data_js_content):
    """Update INNOVATOR_SCORES in data.js with auto-calculated scores."""
    scores = load_json("innovator_scores_auto.json")
    if not scores:
        print("No innovator scores data found, skipping...")
        return data_js_content

    print(f"Merging {len(scores)} innovator scores...")
    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Frontier Index™ scores — Last updated: {today}\n"
    js_array += "const INNOVATOR_SCORES = [\n"

    for s in scores:
        company = s.get("company", "").replace('"', '\\"')
        note = s.get("note", "").replace('"', '\\"')
        js_array += f'  {{ company: "{company}", '
        js_array += f'techMoat: {s.get("techMoat", 5)}, '
        js_array += f'momentum: {s.get("momentum", 5)}, '
        js_array += f'teamPedigree: {s.get("teamPedigree", 5)}, '
        js_array += f'marketGravity: {s.get("marketGravity", 5)}, '
        js_array += f'capitalEfficiency: {s.get("capitalEfficiency", 5)}, '
        js_array += f'govTraction: {s.get("govTraction", 2)}, '
        js_array += f'composite: {s.get("composite", 50.0)}, '
        js_array += f'tier: "{s.get("tier", "early")}", '
        js_array += f'note: "{note}" }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const INNOVATOR_SCORES = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print(f"  Updated INNOVATOR_SCORES ({len(scores)} companies)")
    else:
        print("  INNOVATOR_SCORES not found in data.js")

    return data_js_content


def update_predictive_scores(data_js_content):
    """Update PREDICTIVE_SCORES in data.js with auto-calculated predictions."""
    scores = load_json("predictive_scores_auto.json")
    if not scores:
        print("No predictive scores data found, skipping...")
        return data_js_content

    # Read existing curated PREDICTIVE_SCORES to preserve methodology and curated entries
    ps_match = re.search(r'const PREDICTIVE_SCORES = \{([\s\S]*?)\n\};', data_js_content)
    if not ps_match:
        print("  PREDICTIVE_SCORES not found in data.js, skipping...")
        return data_js_content

    today = datetime.now().strftime("%Y-%m-%d")

    # Helper to format a companies dict as JS
    def format_companies(companies_dict):
        if not companies_dict:
            return ""
        lines = []
        for name, data in companies_dict.items():
            name_escaped = name.replace('"', '\\"')
            score = data.get("score", 50)
            trend = data.get("trend", "stable")
            analysis = data.get("analysis", "").replace('"', '\\"')
            last_updated = data.get("lastUpdated", today)

            if "factors" in data:
                factors_parts = []
                for fk, fv in data["factors"].items():
                    factors_parts.append(f"{fk}: {fv}")
                factors_str = "{ " + ", ".join(factors_parts) + " }"
                lines.append(f'      "{name_escaped}": {{ score: {score}, trend: "{trend}", '
                           f'factors: {factors_str}, '
                           f'analysis: "{analysis}", lastUpdated: "{last_updated}" }},')
            elif "runway" in data:
                runway = data.get("runway", "Unknown")
                lines.append(f'      "{name_escaped}": {{ score: {score}, trend: "{trend}", '
                           f'runway: "{runway}", '
                           f'analysis: "{analysis}", lastUpdated: "{last_updated}" }},')
            elif "predictedTiming" in data:
                timing = data.get("predictedTiming", "TBD")
                confidence = data.get("confidence", 50)
                size = data.get("predictedSize", "TBD").replace('"', '\\"')
                val = data.get("predictedValuation", "TBD").replace('"', '\\"')
                catalyst = data.get("catalyst", "").replace('"', '\\"')
                lines.append(f'      "{name_escaped}": {{ predictedTiming: "{timing}", '
                           f'confidence: {confidence}, predictedSize: "{size}", '
                           f'predictedValuation: "{val}", likelyInvestors: [], '
                           f'catalyst: "{catalyst}", lastUpdated: "{last_updated}" }},')
            else:
                lines.append(f'      "{name_escaped}": {{ score: {score}, trend: "{trend}", '
                           f'analysis: "{analysis}", lastUpdated: "{last_updated}" }},')
        return "\n".join(lines)

    # Merge auto scores with curated (curated already excluded from auto output)
    # We need to inject auto companies into each category's companies block
    categories = ["ipoReadiness", "maTarget", "failureRisk", "nextRound"]

    for category in categories:
        auto_companies = scores.get(category, {})
        if not auto_companies:
            continue

        auto_js = format_companies(auto_companies)
        if not auto_js:
            continue

        # Find the companies: { ... } block for this category and append auto entries
        cat_pattern = rf'({category}:\s*\{{[\s\S]*?companies:\s*\{{)([\s\S]*?)(\n\s*\}}\s*\}})'
        cat_match = re.search(cat_pattern, data_js_content)
        if cat_match:
            existing = cat_match.group(2).rstrip().rstrip(",")
            combined = existing + ",\n" + auto_js if existing.strip() else auto_js
            replacement = cat_match.group(1) + "\n" + combined + cat_match.group(3)
            data_js_content = data_js_content[:cat_match.start()] + replacement + data_js_content[cat_match.end():]
            print(f"  Updated {category}: +{len(auto_companies)} auto entries")

    return data_js_content


def update_headcount_estimates(data_js_content):
    """Update HEADCOUNT_ESTIMATES in data.js with estimated headcount from job data."""
    estimates = load_json("headcount_estimates_auto.json")
    if not estimates:
        print("No headcount estimates data found, skipping...")
        return data_js_content

    print(f"Merging {len(estimates)} headcount estimates...")
    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-calculated headcount estimates from job posting data\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "const HEADCOUNT_ESTIMATES = [\n"

    for est in estimates:
        company = est.get("company", "").replace('"', "'")
        js_array += f'  {{ company: "{company}", '
        js_array += f'openPositions: {est.get("openPositions", 0)}, '
        js_array += f'estimatedHeadcount: {est.get("estimatedHeadcount", 0)}, '
        js_array += f'headcountFormatted: "{est.get("headcountFormatted", "")}", '
        js_array += f'vacancyRate: {est.get("vacancyRate", 0.07)}, '
        js_array += f'hiringVelocity: "{est.get("hiringVelocity", "quiet")}", '
        js_array += f'sector: "{est.get("sector", "")}", '
        js_array += f'growthTrend: "{est.get("growthTrend", "")}", '
        js_array += f'isCurated: {"true" if est.get("isCurated") else "false"}, '
        js_array += f'lastUpdated: "{est.get("lastUpdated", today)}" }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const HEADCOUNT_ESTIMATES = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print(f"  Updated HEADCOUNT_ESTIMATES ({len(estimates)} companies)")
    else:
        # Append after GROWTH_SIGNALS if HEADCOUNT_ESTIMATES doesn't exist yet
        growth_pattern = r'(const GROWTH_SIGNALS = \[[\s\S]*?\];)'
        growth_match = re.search(growth_pattern, data_js_content)
        if growth_match:
            data_js_content = data_js_content[:growth_match.end()] + "\n\n" + js_array + data_js_content[growth_match.end():]
            print(f"  Inserted HEADCOUNT_ESTIMATES ({len(estimates)} companies)")
        else:
            print("  Could not find insertion point for HEADCOUNT_ESTIMATES")

    return data_js_content


def update_sam_contracts(data_js_content):
    """Update SAM_CONTRACTS in data.js with SAM.gov opportunity data."""
    contracts = load_json("sam_contracts_aggregated.json")
    if not contracts:
        print("No SAM contracts data found, skipping...")
        return data_js_content

    print(f"Merging {len(contracts)} SAM contract records...")
    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-updated SAM.gov contract opportunities\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "const SAM_CONTRACTS = [\n"

    for c in contracts:
        company = c.get("company", "").replace('"', "'")
        agencies = json.dumps(c.get("agencies", [])[:5])
        types = json.dumps(c.get("types", []))
        recent = json.dumps(c.get("recentOpportunities", [])[:3])
        js_array += f'  {{ company: "{company}", '
        js_array += f'opportunityCount: {c.get("opportunityCount", 0)}, '
        js_array += f'agencies: {agencies}, '
        js_array += f'types: {types}, '
        js_array += f'recentOpportunities: {recent}, '
        js_array += f'lastUpdated: "{c.get("lastUpdated", today)}" }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const SAM_CONTRACTS = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print(f"  Updated SAM_CONTRACTS ({len(contracts)} companies)")
    else:
        # Append after GOV_CONTRACTS if SAM_CONTRACTS doesn't exist yet
        gov_pattern = r'(const GOV_CONTRACTS = \[[\s\S]*?\];)'
        gov_match = re.search(gov_pattern, data_js_content)
        if gov_match:
            data_js_content = data_js_content[:gov_match.end()] + "\n\n" + js_array + data_js_content[gov_match.end():]
            print(f"  Inserted SAM_CONTRACTS ({len(contracts)} companies)")
        else:
            print("  Could not find insertion point for SAM_CONTRACTS")

    return data_js_content


def update_trade_data(data_js_content):
    """Update TRADE_DATA in data.js with Census Bureau trade trends."""
    trade = load_json("trade_data_raw.json")
    if not trade:
        print("No trade data found, skipping...")
        return data_js_content

    print(f"Merging {len(trade)} trade data entries...")
    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-updated Census Bureau trade data\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "const TRADE_DATA = [\n"

    for entry in trade:
        category = entry.get("category", "").replace('"', "'")
        companies = json.dumps(entry.get("relevantCompanies", []))
        js_array += f'  {{ hsCode: "{entry.get("hsCode", "")}", '
        js_array += f'category: "{category}", '
        js_array += f'tradeType: "{entry.get("tradeType", "")}", '
        js_array += f'latestMonthValue: {entry.get("latestMonthValue", 0)}, '
        js_array += f'latestMonthFormatted: "{entry.get("latestMonthFormatted", "$0")}", '
        js_array += f'yoyChange: "{entry.get("yoyChange", "")}", '
        js_array += f'momChange: "{entry.get("momChange", "")}", '
        js_array += f'trend: "{entry.get("trend", "unknown")}", '
        js_array += f'relevantCompanies: {companies}, '
        js_array += f'relevantSector: "{entry.get("relevantSector", "")}", '
        js_array += f'period: "{entry.get("period", "")}", '
        js_array += f'lastUpdated: "{entry.get("lastUpdated", today)}" }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const TRADE_DATA = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print(f"  Updated TRADE_DATA ({len(trade)} entries)")
    else:
        # Append after SECTOR_MOMENTUM if TRADE_DATA doesn't exist yet
        momentum_pattern = r'(const SECTOR_MOMENTUM = \[[\s\S]*?\];)'
        momentum_match = re.search(momentum_pattern, data_js_content)
        if momentum_match:
            data_js_content = data_js_content[:momentum_match.end()] + "\n\n" + js_array + data_js_content[momentum_match.end():]
            print(f"  Inserted TRADE_DATA ({len(trade)} entries)")
        else:
            print("  Could not find insertion point for TRADE_DATA")

    return data_js_content


def update_product_launches(data_js_content):
    """Update PRODUCT_LAUNCHES in data.js with Product Hunt launch data."""
    launches = load_json("product_launches_raw.json")
    if not launches:
        print("No product launches data found, skipping...")
        return data_js_content

    print(f"Merging {len(launches)} product launches...")
    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-updated Product Hunt launches\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "const PRODUCT_LAUNCHES = [\n"

    for launch in launches[:30]:
        company = launch.get("company", "").replace('"', "'")
        product = launch.get("product", "").replace('"', "'")
        tagline = launch.get("tagline", "").replace('"', "'").replace('\n', ' ')
        topics = json.dumps(launch.get("topics", []))
        makers = json.dumps(launch.get("makers", []))
        js_array += f'  {{ company: "{company}", '
        js_array += f'product: "{product}", '
        js_array += f'tagline: "{tagline}", '
        js_array += f'votes: {launch.get("votes", 0)}, '
        js_array += f'comments: {launch.get("comments", 0)}, '
        js_array += f'launchDate: "{launch.get("launchDate", "")}", '
        js_array += f'url: "{launch.get("url", "")}", '
        js_array += f'topics: {topics}, '
        js_array += f'makers: {makers}, '
        js_array += f'source: "producthunt" }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const PRODUCT_LAUNCHES = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print(f"  Updated PRODUCT_LAUNCHES ({len(launches)} entries)")
    else:
        # Append after DEAL_TRACKER if PRODUCT_LAUNCHES doesn't exist yet
        deal_pattern = r'(const DEAL_TRACKER = \[[\s\S]*?\];)'
        deal_match = re.search(deal_pattern, data_js_content)
        if deal_match:
            data_js_content = data_js_content[:deal_match.end()] + "\n\n" + js_array + data_js_content[deal_match.end():]
            print(f"  Inserted PRODUCT_LAUNCHES ({len(launches)} entries)")
        else:
            print("  Could not find insertion point for PRODUCT_LAUNCHES")

    return data_js_content


def update_last_updated(data_js_content):
    """Update the LAST_UPDATED timestamp."""
    today = datetime.now().strftime("%Y-%m-%d")
    pattern = r'const LAST_UPDATED = "[^"]+";'
    replacement = f'const LAST_UPDATED = "{today}";'

    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: replacement, data_js_content)
        print(f"  Updated LAST_UPDATED to {today}")

    return data_js_content


def update_company_funding(data_js_content):
    """Update COMPANIES funding fields from recent deals."""
    deals = load_json("deals_auto.json")
    if not deals:
        print("No deals data found, skipping company funding updates...")
        return data_js_content

    # Group deals by company, keep most recent
    latest_deals = {}
    for deal in deals:
        company = deal.get("company", "")
        date = deal.get("date", "")
        if company and (company not in latest_deals or date > latest_deals[company].get("date", "")):
            latest_deals[company] = deal

    print(f"Updating company funding from {len(latest_deals)} companies with deals...")

    # Valid funding stages for auto-update
    valid_stages = {
        "Pre-Seed", "Seed", "Series A", "Series B", "Series C", "Series D",
        "Series E", "Series F", "Series G", "Series H", "IPO", "SPAC",
    }

    updated = 0
    for company, deal in latest_deals.items():
        deal_date = deal.get("date", "")
        deal_round = deal.get("round", "")
        deal_amount = deal.get("amount", "")
        deal_valuation = deal.get("valuation", "")

        # Find this company's entry in COMPANIES array
        name_pattern = re.escape(company)
        name_match = re.search(rf'name:\s*"{name_pattern}"', data_js_content)
        if not name_match:
            continue

        # Find the boundary of this company entry
        entry_start = name_match.start()
        next_name = re.search(r'name:\s*"', data_js_content[entry_start + 10:])
        if next_name:
            entry_end = entry_start + 10 + next_name.start()
        else:
            entry_end = len(data_js_content)

        entry_block = data_js_content[entry_start:entry_end]

        # Check existing recentEvent date — only update if deal is newer
        existing_date_match = re.search(r'recentEvent:.*?date:\s*"([^"]*)"', entry_block, re.DOTALL)
        if existing_date_match:
            existing_date = existing_date_match.group(1)
            if deal_date <= existing_date:
                continue  # Deal is older than existing event, skip

        changes_made = False

        # Update fundingStage if deal round is a recognized stage
        if deal_round in valid_stages:
            stage_match = re.search(r'(fundingStage:\s*")[^"]*(")', entry_block)
            if stage_match:
                new_block = entry_block[:stage_match.start()] + \
                    f'{stage_match.group(1)}{deal_round}{stage_match.group(2)}' + \
                    entry_block[stage_match.end():]
                entry_block = new_block
                changes_made = True

        # Update valuation if deal has one
        if deal_valuation:
            val_match = re.search(r'(valuation:\s*")[^"]*(")', entry_block)
            if val_match:
                new_block = entry_block[:val_match.start()] + \
                    f'{val_match.group(1)}{deal_valuation}{val_match.group(2)}' + \
                    entry_block[val_match.end():]
                entry_block = new_block
                changes_made = True

        # Update recentEvent
        if deal_amount and deal_round:
            event_text = f"Raised {deal_amount} {deal_round}"
            re_match = re.search(
                r'recentEvent:\s*\{[^}]*\}',
                entry_block
            )
            if re_match:
                new_event = f'recentEvent: {{ type: "funding", text: "{event_text}", date: "{deal_date}" }}'
                new_block = entry_block[:re_match.start()] + new_event + entry_block[re_match.end():]
                entry_block = new_block
                changes_made = True

        if changes_made:
            data_js_content = data_js_content[:entry_start] + entry_block + data_js_content[entry_end:]
            updated += 1
            print(f"  {company}: {deal_amount} {deal_round} ({deal_date})")

    print(f"  Updated {updated} company funding records from deals")
    return data_js_content


def update_vc_portfolios(data_js_content):
    """Update VC_FIRMS portfolioCompanies from deal data + portfolio page scraping."""
    deals = load_json("deals_auto.json")
    portfolio_changes = load_json("vc_portfolio_changes.json")

    # Map deal investor names to VC_FIRMS shortNames
    INVESTOR_TO_VC = {
        "a16z": "a16z",
        "8VC": "8VC",
        "Founders Fund": "Founders Fund",
        "Khosla Ventures": "Khosla",
        "Sequoia Capital": "Sequoia",
        "Sequoia": "Sequoia",
        "Eclipse Ventures": "Eclipse",
        "General Catalyst": "GC",
        "Lux Capital": "Lux",
        "Cantos Ventures": "Cantos",
    }

    # Build investor → companies map from deals
    vc_investments = {}
    for deal in (deals or []):
        investor = deal.get("investor", "")
        company = deal.get("company", "")
        if not investor or not company:
            continue
        vc_short = INVESTOR_TO_VC.get(investor)
        if vc_short:
            vc_investments.setdefault(vc_short, set()).add(company)

    # Also incorporate portfolio page scrape results
    for change in (portfolio_changes or []):
        vc_short = change.get("vc", "")
        company = change.get("company", "")
        if vc_short and company:
            vc_investments.setdefault(vc_short, set()).add(company)

    if not vc_investments:
        print("No VC portfolio updates needed")
        return data_js_content

    print(f"Checking portfolio updates for {len(vc_investments)} VCs...")

    # Get set of all tracked company names for validation
    tracked_companies = set(re.findall(r'name:\s*"([^"]+)"', data_js_content[:500000]))

    updated = 0
    for vc_short, deal_companies in vc_investments.items():
        # Find this VC's entry
        vc_match = re.search(rf'shortName:\s*"{re.escape(vc_short)}"', data_js_content)
        if not vc_match:
            continue

        # Find the portfolioCompanies array within this VC entry
        entry_start = vc_match.start()
        # Look ahead for the portfolio array
        after_vc = data_js_content[entry_start:entry_start + 2000]
        portfolio_match = re.search(
            r'(portfolioCompanies:\s*\[)([^\]]*?)(\])',
            after_vc
        )
        if not portfolio_match:
            continue

        # Parse existing portfolio
        existing_str = portfolio_match.group(2)
        existing_companies = set(re.findall(r'"([^"]+)"', existing_str))

        # Find new companies to add (must be tracked and not already in portfolio)
        new_additions = []
        for company in deal_companies:
            if company in tracked_companies and company not in existing_companies:
                new_additions.append(company)

        if not new_additions:
            continue

        # Build updated portfolio string
        all_companies = list(existing_companies) + new_additions
        new_portfolio_str = ", ".join(f'"{c}"' for c in all_companies)

        # Replace in content
        abs_start = entry_start + portfolio_match.start()
        abs_end = entry_start + portfolio_match.end()
        replacement = f'{portfolio_match.group(1)}{new_portfolio_str}{portfolio_match.group(3)}'
        data_js_content = data_js_content[:abs_start] + replacement + data_js_content[abs_end:]

        updated += 1
        print(f"  {vc_short}: +{len(new_additions)} ({', '.join(new_additions)})")

    print(f"  Updated {updated} VC portfolio lists")
    return data_js_content


def update_sbir_awards(data_js_content):
    """Update SBIR_AWARDS in data.js with SBIR/STTR government grant data."""
    awards = load_json("sbir_awards_raw.json")
    if not awards:
        print("No SBIR awards data found, skipping...")
        return data_js_content

    print(f"Merging {len(awards)} SBIR awards...")
    today = datetime.now().strftime("%Y-%m-%d")
    known_awards = [a for a in awards if a.get("isKnownCompany")]
    js_array = f"// Auto-updated SBIR/STTR government grant awards\n"
    js_array += f"// Last updated: {today}\n"
    js_array += f"// Total awards: {len(awards)} | Known companies: {len(known_awards)}\n"
    js_array += "const SBIR_AWARDS = [\n"

    for award in awards[:500]:
        firm = award.get("firm", "").replace('"', "'")
        title = award.get("title", "")[:100].replace('"', "'")
        abstract = award.get("abstract", "")[:150].replace('"', "'").replace("\n", " ")
        js_array += f'  {{ firm: "{firm}", '
        js_array += f'title: "{title}", '
        js_array += f'agency: "{award.get("agency", "")}", '
        js_array += f'phase: "{award.get("phase", "")}", '
        js_array += f'program: "{award.get("program", "")}", '
        js_array += f'awardYear: {award.get("awardYear", 0) or 0}, '
        js_array += f'awardAmount: {award.get("awardAmount", 0) or 0}, '
        js_array += f'state: "{award.get("state", "")}", '
        js_array += f'abstract: "{abstract}", '
        js_array += f'isKnownCompany: {"true" if award.get("isKnownCompany") else "false"} }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const SBIR_AWARDS = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print(f"  Updated SBIR_AWARDS ({len(awards)} entries)")
    else:
        # Append after SAM_CONTRACTS
        sam_pattern = r'(const SAM_CONTRACTS = \[[\s\S]*?\];)'
        sam_match = re.search(sam_pattern, data_js_content)
        if sam_match:
            data_js_content = data_js_content[:sam_match.end()] + "\n\n" + js_array + data_js_content[sam_match.end():]
            print(f"  Inserted SBIR_AWARDS ({len(awards)} entries)")
        else:
            # Fallback: append after GOV_CONTRACTS
            gov_pattern = r'(const GOV_CONTRACTS = \[[\s\S]*?\];)'
            gov_match = re.search(gov_pattern, data_js_content)
            if gov_match:
                data_js_content = data_js_content[:gov_match.end()] + "\n\n" + js_array + data_js_content[gov_match.end():]
                print(f"  Inserted SBIR_AWARDS after GOV_CONTRACTS ({len(awards)} entries)")
            else:
                print("  Could not find insertion point for SBIR_AWARDS")

    return data_js_content


def update_nih_grants(data_js_content):
    """Update NIH_GRANTS in data.js with NIH Reporter grant data."""
    grants = load_json("nih_grants_raw.json")
    if not grants:
        print("No NIH grants data found, skipping...")
        return data_js_content

    print(f"Merging {len(grants)} NIH grants...")
    today = datetime.now().strftime("%Y-%m-%d")
    known_grants = [g for g in grants if g.get("isKnownCompany")]
    js_array = f"// Auto-updated NIH Reporter grant data\n"
    js_array += f"// Last updated: {today}\n"
    js_array += f"// Total grants: {len(grants)} | Known companies: {len(known_grants)}\n"
    js_array += "const NIH_GRANTS = [\n"

    for grant in grants[:500]:
        org = grant.get("orgName", "").replace('"', "'")
        title = grant.get("title", "")[:100].replace('"', "'")
        terms = json.dumps(grant.get("terms", [])[:5])
        js_array += f'  {{ orgName: "{org}", '
        js_array += f'title: "{title}", '
        js_array += f'agency: "{grant.get("agency", "")}", '
        js_array += f'fiscalYear: {grant.get("fiscalYear", 0)}, '
        js_array += f'totalCost: {grant.get("totalCost", 0)}, '
        js_array += f'totalCostFormatted: "{grant.get("totalCostFormatted", "$0")}", '
        js_array += f'activityCode: "{grant.get("activityCode", "")}", '
        js_array += f'isSbir: {"true" if grant.get("isSbir") else "false"}, '
        js_array += f'terms: {terms}, '
        js_array += f'isKnownCompany: {"true" if grant.get("isKnownCompany") else "false"} }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const NIH_GRANTS = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print(f"  Updated NIH_GRANTS ({len(grants)} entries)")
    else:
        # Append after SBIR_AWARDS if exists, else after GOV_CONTRACTS
        for anchor in ["SBIR_AWARDS", "SAM_CONTRACTS", "GOV_CONTRACTS"]:
            anchor_pattern = rf'(const {anchor} = \[[\s\S]*?\];)'
            anchor_match = re.search(anchor_pattern, data_js_content)
            if anchor_match:
                data_js_content = data_js_content[:anchor_match.end()] + "\n\n" + js_array + data_js_content[anchor_match.end():]
                print(f"  Inserted NIH_GRANTS after {anchor} ({len(grants)} entries)")
                break
        else:
            print("  Could not find insertion point for NIH_GRANTS")

    return data_js_content


def update_arpa_e_projects(data_js_content):
    """Update ARPA_E_PROJECTS in data.js with ARPA-E project data."""
    projects = load_json("arpa_e_projects_raw.json")
    if not projects:
        print("No ARPA-E projects data found, skipping...")
        return data_js_content

    print(f"Merging {len(projects)} ARPA-E projects...")
    today = datetime.now().strftime("%Y-%m-%d")
    private_projects = [p for p in projects if p.get("isPrivateCompany")]
    js_array = f"// Auto-updated ARPA-E project data\n"
    js_array += f"// Last updated: {today}\n"
    js_array += f"// Total projects: {len(projects)} | Private companies: {len(private_projects)}\n"
    js_array += "const ARPA_E_PROJECTS = [\n"

    for proj in projects[:500]:
        title = proj.get("title", "")[:120].replace('"', '\\"').replace("\n", " ")
        org = proj.get("organization", "").replace('"', '\\"')
        techs = json.dumps(proj.get("technologyAreas", [])[:5])
        js_array += f'  {{ title: "{title}", '
        js_array += f'organization: "{org}", '
        js_array += f'orgType: "{proj.get("orgType", "")}", '
        js_array += f'status: "{proj.get("status", "")}", '
        js_array += f'state: "{proj.get("state", "")}", '
        js_array += f'awardAmount: {proj.get("awardAmount", 0)}, '
        js_array += f'awardFormatted: "{proj.get("awardFormatted", "")}", '
        js_array += f'programAcronym: "{proj.get("programAcronym", "")}", '
        js_array += f'technologyAreas: {techs}, '
        js_array += f'isKnownCompany: {"true" if proj.get("isKnownCompany") else "false"}, '
        js_array += f'isPrivateCompany: {"true" if proj.get("isPrivateCompany") else "false"} }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const ARPA_E_PROJECTS = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print(f"  Updated ARPA_E_PROJECTS ({len(projects)} entries)")
    else:
        for anchor in ["NIH_GRANTS", "SBIR_AWARDS", "SAM_CONTRACTS", "GOV_CONTRACTS"]:
            anchor_pattern = rf'(const {anchor} = \[[\s\S]*?\];)'
            anchor_match = re.search(anchor_pattern, data_js_content)
            if anchor_match:
                data_js_content = data_js_content[:anchor_match.end()] + "\n\n" + js_array + data_js_content[anchor_match.end():]
                print(f"  Inserted ARPA_E_PROJECTS after {anchor} ({len(projects)} entries)")
                break
        else:
            print("  Could not find insertion point for ARPA_E_PROJECTS")

    return data_js_content


def update_diffbot_enrichment(data_js_content):
    """Update DIFFBOT_ENRICHMENT in data.js with Diffbot company enrichment data."""
    enrichment = load_json("diffbot_enrichment_raw.json")
    if not enrichment:
        print("No Diffbot enrichment data found, skipping...")
        return data_js_content

    # Only include enriched companies
    enriched = [e for e in enrichment if e.get("enriched")]
    if not enriched:
        print("No enriched companies in Diffbot data, skipping...")
        return data_js_content

    print(f"Merging {len(enriched)} Diffbot enrichments...")
    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-updated Diffbot company enrichment\n"
    js_array += f"// Last updated: {today}\n"
    js_array += f"// Enriched: {len(enriched)} companies\n"
    js_array += "const DIFFBOT_ENRICHMENT = [\n"

    for entry in enriched:
        name = entry.get("name", "").replace('"', '\\"')
        summary = entry.get("summary", "").replace('"', '\\"').replace("\n", " ")[:150]
        hq = entry.get("headquarters", "").replace('"', '\\"')
        industries = json.dumps(entry.get("industries", [])[:3])
        social = json.dumps(entry.get("socialLinks", {}))

        js_array += f'  {{ name: "{name}", '
        js_array += f'summary: "{summary}", '
        if entry.get("employeeCount"):
            js_array += f'employeeCount: {entry["employeeCount"]}, '
        if entry.get("employeeRange"):
            js_array += f'employeeRange: "{entry["employeeRange"]}", '
        if entry.get("foundedYear"):
            js_array += f'foundedYear: "{entry["foundedYear"]}", '
        if hq:
            js_array += f'headquarters: "{hq}", '
        if entry.get("industries"):
            js_array += f'industries: {industries}, '
        if entry.get("socialLinks"):
            js_array += f'socialLinks: {social}, '
        if entry.get("isPublic"):
            js_array += f'isPublic: true, '
            if entry.get("ticker"):
                js_array += f'ticker: "{entry["ticker"]}", '
        if entry.get("revenueFormatted"):
            js_array += f'estimatedRevenue: "{entry["revenueFormatted"]}", '
        js_array += f'lastEnriched: "{entry.get("lastEnriched", "")}" }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const DIFFBOT_ENRICHMENT = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print(f"  Updated DIFFBOT_ENRICHMENT ({len(enriched)} entries)")
    else:
        # Append after HEADCOUNT_ESTIMATES or GROWTH_SIGNALS
        for anchor in ["HEADCOUNT_ESTIMATES", "GROWTH_SIGNALS", "REVENUE_INTEL"]:
            anchor_pattern = rf'(const {anchor} = \[[\s\S]*?\];)'
            anchor_match = re.search(anchor_pattern, data_js_content)
            if anchor_match:
                data_js_content = data_js_content[:anchor_match.end()] + "\n\n" + js_array + data_js_content[anchor_match.end():]
                print(f"  Inserted DIFFBOT_ENRICHMENT after {anchor} ({len(enriched)} entries)")
                break
        else:
            print("  Could not find insertion point for DIFFBOT_ENRICHMENT")

    return data_js_content


def validate_js_syntax(content):
    """Basic validation: check for missing commas between objects in arrays."""
    issues = list(re.finditer(r'\}\s*\n\s*\{', content))
    if issues:
        for i in issues:
            line = content[:i.start()].count('\n') + 1
            print(f"  WARNING: Possible missing comma at line ~{line}")
        return False
    return True


def main():
    print("=" * 60)
    print("Data Merger for The Innovators League")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Read current data.js
    if not DATA_JS_PATH.exists():
        print("ERROR: data.js not found!")
        return

    with open(DATA_JS_PATH, 'r') as f:
        data_js_content = f.read()

    original_length = len(data_js_content)

    # Apply updates — each function is safe to skip if data file doesn't exist
    data_js_content = update_sec_filings(data_js_content)
    data_js_content = update_company_signals(data_js_content)
    data_js_content = update_gov_contracts(data_js_content)
    data_js_content = update_deal_tracker(data_js_content)
    data_js_content = update_sector_momentum(data_js_content)
    data_js_content = update_ipo_pipeline(data_js_content)
    data_js_content = update_revenue_intel(data_js_content)
    data_js_content = update_growth_signals(data_js_content)
    data_js_content = update_funding_tracker(data_js_content)
    data_js_content = update_valuation_benchmarks(data_js_content)
    data_js_content = update_innovator_scores(data_js_content)
    data_js_content = update_predictive_scores(data_js_content)
    data_js_content = update_headcount_estimates(data_js_content)
    data_js_content = update_sam_contracts(data_js_content)
    data_js_content = update_trade_data(data_js_content)
    data_js_content = update_product_launches(data_js_content)
    data_js_content = update_sbir_awards(data_js_content)
    data_js_content = update_nih_grants(data_js_content)
    data_js_content = update_arpa_e_projects(data_js_content)
    data_js_content = update_diffbot_enrichment(data_js_content)
    data_js_content = update_company_funding(data_js_content)
    data_js_content = update_vc_portfolios(data_js_content)
    data_js_content = update_last_updated(data_js_content)

    # Validate before writing
    print("\nValidating JS syntax...")
    if validate_js_syntax(data_js_content):
        print("  No syntax issues detected")
    else:
        print("  WARNING: Potential syntax issues found — review data.js manually")

    # Write updated data.js
    with open(DATA_JS_PATH, 'w') as f:
        f.write(data_js_content)

    print("\n" + "=" * 60)
    print(f"data.js updated ({original_length} -> {len(data_js_content)} bytes)")
    print("=" * 60)

if __name__ == "__main__":
    main()
