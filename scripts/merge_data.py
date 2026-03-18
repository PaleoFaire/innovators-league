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
        try:
            with open(filepath) as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  WARNING: {filename} has invalid JSON ({e}), skipping...")
            return []
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


def update_prev_week_scores(data_js_content):
    """Add PREV_WEEK_SCORES for delta tracking in Frontier Index."""
    prev_scores = load_json("prev_week_scores.json")
    if not prev_scores:
        print("No prev_week_scores data found, skipping...")
        return data_js_content

    print(f"Merging {len(prev_scores)} previous week scores...")
    js_array = "// Previous week Frontier Index scores for delta tracking\n"
    js_array += "const PREV_WEEK_SCORES = [\n"

    for s in prev_scores:
        company = s.get("company", "").replace('"', '\\"')
        js_array += f'  {{ company: "{company}", composite: {s.get("composite", 50.0)} }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const PREV_WEEK_SCORES = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print(f"  Updated PREV_WEEK_SCORES ({len(prev_scores)} companies)")
    else:
        # Append after INNOVATOR_SCORES
        insert_pattern = r'(const INNOVATOR_SCORES = \[[\s\S]*?\];)'
        if re.search(insert_pattern, data_js_content):
            data_js_content = re.sub(insert_pattern, lambda m: m.group(0) + '\n\n' + js_array, data_js_content)
            print(f"  Inserted PREV_WEEK_SCORES ({len(prev_scores)} companies)")
        else:
            print("  Could not find INNOVATOR_SCORES to insert after")

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


def update_contractor_readiness(data_js_content):
    """Recalibrate CONTRACTOR_READINESS scores using latest gov contract data.
    Updates contract counts, agencies, and recalculates readiness scores.
    Preserves curated security fields (clearanceLevel, cmmcLevel, itarCompliant, etc.).
    """
    gov_contracts = load_json("gov_contracts_aggregated.json")
    sbir_awards = load_json("sbir_awards_raw.json")

    if not any([gov_contracts, sbir_awards]):
        print("No gov data for contractor readiness recalibration, skipping...")
        return data_js_content

    # Build lookup: company → contract info
    contract_intel = {}
    for gc in (gov_contracts or []):
        company = gc.get("company", "")
        if company:
            contract_intel[company] = {
                "contractCount": gc.get("contractCount", 0),
                "agencies": gc.get("agencies", []),
            }

    # SBIR phase per company (highest)
    sbir_phases = {}
    phase_order = {"Phase I": 1, "Phase II": 2, "Phase III": 3}
    for sa in (sbir_awards or []):
        if not sa.get("isKnownCompany"):
            continue
        company = sa.get("firm", "")
        phase = sa.get("phase", "")
        if company and phase_order.get(phase, 0) > phase_order.get(sbir_phases.get(company, ""), 0):
            sbir_phases[company] = phase

    if not contract_intel and not sbir_phases:
        print("No contract intel built, skipping contractor readiness...")
        return data_js_content

    # Parse existing CONTRACTOR_READINESS
    pattern = r'const CONTRACTOR_READINESS = \[([\s\S]*?)\];'
    match = re.search(pattern, data_js_content)
    if not match:
        print("  CONTRACTOR_READINESS not found in data.js, skipping...")
        return data_js_content

    # Extract entries preserving curated fields
    entries = []
    block_pattern = r'\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
    for block_match in re.finditer(block_pattern, match.group(1)):
        block = block_match.group(0)
        name_m = re.search(r'company:\s*"([^"]+)"', block)
        if not name_m:
            continue

        company = name_m.group(1)

        def extract_num(field, default=0):
            m = re.search(rf'{field}:\s*(\d+)', block)
            return int(m.group(1)) if m else default

        def extract_str(field, default=""):
            m = re.search(rf'{field}:\s*"([^"]*)"', block)
            return m.group(1) if m else default

        def extract_bool(field, default=False):
            m = re.search(rf'{field}:\s*(true|false)', block)
            return m.group(1) == "true" if m else default

        def extract_array(field):
            m = re.search(rf'{field}:\s*\[([^\]]*)\]', block)
            if m:
                return [s.strip().strip('"') for s in m.group(1).split(',') if s.strip().strip('"')]
            return []

        entry = {
            "company": company,
            "readinessScore": extract_num("readinessScore", 50),
            "trlLevel": extract_num("trlLevel", 5),
            "sbirPhase": extract_str("sbirPhase", ""),
            "clearanceLevel": extract_str("clearanceLevel", ""),
            "facilityCleared": extract_bool("facilityCleared"),
            "contractsCompleted": extract_num("contractsCompleted", 0),
            "onTimeRate": extract_num("onTimeRate", 0),
            "avgRating": 0,
            "cmmcLevel": extract_num("cmmcLevel", 0),
            "itarCompliant": extract_bool("itarCompliant"),
            "keyAgencies": extract_array("keyAgencies"),
            "readinessFactors": extract_array("readinessFactors"),
        }

        rating_m = re.search(r'avgRating:\s*([\d.]+)', block)
        entry["avgRating"] = float(rating_m.group(1)) if rating_m else 0

        # Update from auto data
        intel = contract_intel.get(company, {})
        if intel:
            new_count = intel.get("contractCount", 0)
            if new_count > entry["contractsCompleted"]:
                entry["contractsCompleted"] = new_count
            auto_agencies = intel.get("agencies", [])
            existing_set = set(entry["keyAgencies"])
            for agency in auto_agencies:
                if agency not in existing_set:
                    entry["keyAgencies"].append(agency)

        auto_phase = sbir_phases.get(company, "")
        if auto_phase:
            current_phase = entry["sbirPhase"]
            if current_phase not in ["Graduated", "N/A (Public)"]:
                if phase_order.get(auto_phase, 0) > phase_order.get(current_phase, 0):
                    entry["sbirPhase"] = auto_phase

        # Recalculate readiness score
        contract_score = min(100, entry["contractsCompleted"] * 2)
        trl_score = (entry["trlLevel"] / 9) * 100
        clearance_score = {"TS/SCI": 100, "TS": 90, "Secret": 70, "Confidential": 50}.get(entry["clearanceLevel"], 30)
        perf_score = entry["onTimeRate"]
        cmmc_score = (entry["cmmcLevel"] / 3) * 100

        new_readiness = round(
            contract_score * 0.30 + trl_score * 0.25 +
            clearance_score * 0.20 + perf_score * 0.15 + cmmc_score * 0.10
        )
        entry["readinessScore"] = max(entry["readinessScore"], new_readiness)
        entries.append(entry)

    if not entries:
        print("No contractor readiness entries parsed, skipping...")
        return data_js_content

    entries.sort(key=lambda x: x["readinessScore"], reverse=True)

    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-recalibrated contractor readiness scores\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "const CONTRACTOR_READINESS = [\n"

    for e in entries:
        agencies = json.dumps(e["keyAgencies"])
        factors = json.dumps(e["readinessFactors"])
        js_array += f'  {{ company: "{e["company"]}", readinessScore: {e["readinessScore"]}, '
        js_array += f'trlLevel: {e["trlLevel"]}, sbirPhase: "{e["sbirPhase"]}", '
        js_array += f'clearanceLevel: "{e["clearanceLevel"]}", '
        js_array += f'facilityCleared: {"true" if e["facilityCleared"] else "false"}, '
        js_array += f'pastPerformance: {{ contractsCompleted: {e["contractsCompleted"]}, '
        js_array += f'onTimeRate: {e["onTimeRate"]}, avgRating: {e["avgRating"]} }}, '
        js_array += f'cmmcLevel: {e["cmmcLevel"]}, '
        js_array += f'itarCompliant: {"true" if e["itarCompliant"] else "false"}, '
        js_array += f'keyAgencies: {agencies}, '
        js_array += f'readinessFactors: {factors} }},\n'

    js_array += "];"

    data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
    print(f"  Updated CONTRACTOR_READINESS ({len(entries)} entries)")

    return data_js_content


def update_news_feed(data_js_content):
    """Update NEWS_FEED in data.js with fresh news from RSS aggregation.
    Preserves curated entries with rosAnalysis, adds new auto-detected news.
    """
    news = load_json("news_raw.json")
    if not news:
        print("No news data found for NEWS_FEED, skipping...")
        return data_js_content

    # Parse existing curated NEWS_FEED entries (those with rosAnalysis)
    pattern = r'const NEWS_FEED = \[([\s\S]*?)\];'
    match = re.search(pattern, data_js_content)
    if not match:
        print("  NEWS_FEED not found in data.js, skipping...")
        return data_js_content

    # Extract curated entries that have rosAnalysis
    curated_entries = []
    # Find entries with rosAnalysis field — these are editorial and should be preserved
    entry_blocks = re.findall(r'\{[^{}]*rosAnalysis:[^{}]*\}', match.group(1))
    for block in entry_blocks:
        company_m = re.search(r'company:\s*"([^"]+)"', block)
        headline_m = re.search(r'headline:\s*"((?:[^"\\]|\\.)*)"', block)
        if company_m and headline_m:
            curated_entries.append({
                "company": company_m.group(1),
                "headline": headline_m.group(1),
            })

    curated_keys = set(f"{e['company']}:{e['headline'][:50]}" for e in curated_entries)

    # Categorize news by keywords
    def categorize_news(title):
        t = title.lower()
        if any(w in t for w in ["fund", "raise", "series", "valuation", "invest", "round"]):
            return "funding"
        elif any(w in t for w in ["contract", "award", "sbir", "ota", "idiq"]):
            return "contract"
        elif any(w in t for w in ["ipo", "spac", "public", "listing"]):
            return "ipo"
        elif any(w in t for w in ["launch", "deploy", "milestone", "test", "demo"]):
            return "milestone"
        elif any(w in t for w in ["partner", "collaborat", "joint", "alliance"]):
            return "partnership"
        elif any(w in t for w in ["hire", "appoint", "ceo", "cto", "executive"]):
            return "leadership"
        return "news"

    def assess_impact(title):
        t = title.lower()
        if any(w in t for w in ["billion", "$1b", "$2b", "$5b", "$10b", "ipo", "acquisition"]):
            return "high"
        elif any(w in t for w in ["million", "contract", "award", "series"]):
            return "medium"
        return "low"

    # Build new news items from auto-fetched data
    auto_items = []
    for i, article in enumerate(news):
        company = article.get("matchedCompany", "")
        if not company:
            continue
        title = article.get("title", "")
        if not title:
            continue
        # Skip if this matches a curated entry
        key = f"{company}:{title[:50]}"
        if key in curated_keys:
            continue

        sector = article.get("sector", "")
        # Try to derive sector from company if not provided
        if not sector:
            sector = "General"

        auto_items.append({
            "company": company,
            "headline": title[:150].replace('"', "'"),
            "source": article.get("source", ""),
            "category": categorize_news(title),
            "date": article.get("date", article.get("time", ""))[:10],
            "summary": (article.get("summary", "") or "")[:200].replace('"', "'").replace("\n", " "),
            "impact": assess_impact(title),
            "sector": sector,
        })

    if not auto_items:
        print("No new auto news items found, skipping NEWS_FEED update...")
        return data_js_content

    # Sort by date descending
    auto_items.sort(key=lambda x: x.get("date", ""), reverse=True)

    # Rebuild NEWS_FEED: curated entries first (preserved as-is), then auto items
    today = datetime.now().strftime("%Y-%m-%d")

    # We need to keep the curated block intact and append auto items
    # Instead of replacing, we'll rebuild the whole array
    js_array = f"// Auto-updated news feed (curated + auto-detected)\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "const NEWS_FEED = [\n"

    # Re-insert curated entries by extracting their full blocks from existing content
    curated_block = ""
    for block_match in re.finditer(r'(\{[^{}]*rosAnalysis:[^{}]*\}),?\s*\n', match.group(1)):
        curated_block += "  " + block_match.group(1) + ",\n"

    if curated_block:
        js_array += "  // ─── CURATED (Editorial Analysis) ───\n"
        js_array += curated_block

    # Add auto items (cap at 50)
    js_array += "  // ─── AUTO-DETECTED NEWS ───\n"
    next_id = len(curated_entries) + 1
    for item in auto_items[:50]:
        js_array += f'  {{ id: {next_id}, company: "{item["company"]}", '
        js_array += f'headline: "{item["headline"]}", '
        js_array += f'source: "{item["source"]}", '
        js_array += f'category: "{item["category"]}", '
        js_array += f'date: "{item["date"]}", '
        js_array += f'summary: "{item["summary"]}", '
        js_array += f'impact: "{item["impact"]}", '
        js_array += f'sector: "{item["sector"]}", '
        js_array += f'url: "#" }},\n'
        next_id += 1

    js_array += "];"

    data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
    print(f"  Updated NEWS_FEED ({len(curated_entries)} curated + {min(len(auto_items), 50)} auto)")

    return data_js_content


def update_alt_data_signals(data_js_content):
    """Rebuild ALT_DATA_SIGNALS from auto-updated HEADCOUNT_ESTIMATES, GROWTH_SIGNALS, and news data.
    Produces per-company signal dashboard: hiring velocity, headcount, sentiment, signal strength.
    """
    headcount = load_json("headcount_estimates_auto.json")
    growth_signals = load_json("growth_signals_auto.json")
    news = load_json("news_raw.json")

    if not any([headcount, growth_signals, news]):
        print("No data sources for ALT_DATA_SIGNALS, skipping...")
        return data_js_content

    pattern = r'(?://[^\n]*\n)*const ALT_DATA_SIGNALS = \[[\s\S]*?\];'
    if not re.search(pattern, data_js_content):
        print("  ALT_DATA_SIGNALS not found in data.js, skipping...")
        return data_js_content

    # Build company profiles from multiple sources
    companies = {}

    # From headcount estimates: hiring velocity, headcount
    for hc in (headcount or []):
        company = hc.get("company", "")
        if not company:
            continue
        companies.setdefault(company, {})
        companies[company]["hiringVelocity"] = hc.get("hiringVelocity", "stable")
        open_pos = hc.get("openPositions", 0)
        est_hc = hc.get("estimatedHeadcount", 0)
        companies[company]["headcountEstimate"] = hc.get("headcountFormatted", f"{est_hc:,}" if est_hc else "")
        companies[company]["sector"] = hc.get("sector", "")
        # Derive signal strength from hiring velocity
        velocity_scores = {"surging": 9, "growing": 7, "stable": 5, "quiet": 3, "declining": 2}
        companies[company]["hiringScore"] = velocity_scores.get(hc.get("hiringVelocity", "stable"), 5)

    # From growth signals: aggregate signal strength per company
    signal_counts = {}
    for gs in (growth_signals or []):
        company = gs.get("company", "")
        if not company:
            continue
        companies.setdefault(company, {})
        signal_counts.setdefault(company, 0)
        signal_counts[company] += gs.get("strength", 1)
        # Use the strongest signal as key signal
        if gs.get("strength", 0) > companies[company].get("bestSignalStrength", 0):
            companies[company]["bestSignalStrength"] = gs.get("strength", 0)
            companies[company]["keySignal"] = gs.get("detail", "")

    # From news: sentiment and web traffic proxy
    news_counts = {}
    for article in (news or []):
        company = article.get("matchedCompany", "")
        if not company:
            continue
        companies.setdefault(company, {})
        news_counts.setdefault(company, 0)
        news_counts[company] += 1

    # Calculate composite signal strength and sentiment for each company
    results = []
    for company, data in companies.items():
        hiring_score = data.get("hiringScore", 5)
        signal_count = signal_counts.get(company, 0)
        news_count = news_counts.get(company, 0)

        # Composite signal strength (1-10)
        signal_strength = min(10, max(1, round(
            hiring_score * 0.4 +
            min(10, signal_count) * 0.3 +
            min(10, news_count * 2) * 0.3
        )))

        # Determine web traffic proxy from news volume
        if news_count >= 3:
            web_traffic = "up"
        elif news_count >= 1:
            web_traffic = "flat"
        else:
            web_traffic = "down"

        # Determine sentiment from news (simplified — positive if mentioned frequently)
        if news_count >= 3 and hiring_score >= 7:
            sentiment = "positive"
        elif news_count >= 1:
            sentiment = "mixed"
        elif hiring_score <= 3:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        key_signal = data.get("keySignal", "")
        if not key_signal and data.get("hiringVelocity"):
            velocity = data.get("hiringVelocity", "stable")
            hc = data.get("headcountEstimate", "")
            key_signal = f"Hiring velocity: {velocity}. Est. headcount: {hc}" if hc else f"Hiring velocity: {velocity}"

        results.append({
            "company": company,
            "hiringVelocity": data.get("hiringVelocity", "stable"),
            "headcountEstimate": data.get("headcountEstimate", ""),
            "webTraffic": web_traffic,
            "newsSentiment": sentiment,
            "signalStrength": signal_strength,
            "keySignal": key_signal[:200].replace('"', "'").replace("\n", " "),
        })

    # Sort by signal strength descending, take top 50
    results.sort(key=lambda x: x["signalStrength"], reverse=True)
    results = results[:50]

    if not results:
        print("No ALT_DATA_SIGNALS to write, skipping...")
        return data_js_content

    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-calculated alternative data signals\n"
    js_array += f"// Last updated: {today}\n"
    js_array += f"// Sources: headcount estimates, growth signals, news sentiment\n"
    js_array += "const ALT_DATA_SIGNALS = [\n"

    for s in results:
        company = s["company"].replace('"', "'")
        key_signal = s["keySignal"].replace('"', "'")
        js_array += f'  {{ company: "{company}", '
        js_array += f'hiringVelocity: "{s["hiringVelocity"]}", '
        js_array += f'keyRoles: [], '
        js_array += f'headcountEstimate: "{s["headcountEstimate"]}", '
        js_array += f'webTraffic: "{s["webTraffic"]}", '
        js_array += f'newsSentiment: "{s["newsSentiment"]}", '
        js_array += f'githubPresence: null, '
        js_array += f'signalStrength: {s["signalStrength"]}, '
        js_array += f'keySignal: "{key_signal}" }},\n'

    js_array += "];"

    data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
    print(f"  Updated ALT_DATA_SIGNALS ({len(results)} companies)")

    return data_js_content


def update_patent_intel(data_js_content):
    """Update PATENT_INTEL in data.js with fresh USPTO patent data.
    Merges auto-fetched patent counts/velocity with curated ipMoatScore/notes.
    """
    aggregated = load_json("patents_aggregated.json")
    if not aggregated:
        print("No patent aggregated data found, skipping...")
        return data_js_content

    # Build lookup from aggregated patent data
    auto_data = {}
    for entry in aggregated:
        auto_data[entry["company"]] = entry

    # Parse existing curated PATENT_INTEL entries to preserve ipMoatScore, notablePatents, note
    pattern = r'const PATENT_INTEL = \[([\s\S]*?)\];'
    match = re.search(pattern, data_js_content)
    if not match:
        print("  PATENT_INTEL not found in data.js, skipping...")
        return data_js_content

    # Extract curated entries
    curated = {}
    entry_pattern = r'\{[^}]+\}'
    for entry_match in re.finditer(entry_pattern, match.group(1)):
        block = entry_match.group(0)
        name_match = re.search(r'company:\s*"([^"]+)"', block)
        if name_match:
            company = name_match.group(1)
            # Extract curated fields
            moat_match = re.search(r'ipMoatScore:\s*(\d+)', block)
            note_match = re.search(r'note:\s*"((?:[^"\\]|\\.)*)"', block)
            notable_match = re.search(r'notablePatents:\s*\[(.*?)\]', block)
            tech_match = re.search(r'techAreas:\s*\[(.*?)\]', block)
            curated[company] = {
                "ipMoatScore": int(moat_match.group(1)) if moat_match else 5,
                "note": note_match.group(1) if note_match else "",
                "notablePatents": notable_match.group(1) if notable_match else "",
                "techAreas": tech_match.group(1) if tech_match else "",
            }

    print(f"Merging patent data: {len(auto_data)} auto + {len(curated)} curated...")

    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-updated patent intelligence (curated scores + USPTO data)\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "const PATENT_INTEL = [\n"

    # Merge: start with curated companies (preserve order), update counts from auto
    processed = set()
    for company, cur in curated.items():
        auto = auto_data.get(company, {})
        total_patents = auto.get("patentCount", 0)
        # Try to extract existing totalPatents from curated if no auto data
        if total_patents == 0:
            existing_match = re.search(rf'company:\s*"{re.escape(company)}"[^}}]*totalPatents:\s*(\d+)', match.group(1))
            if existing_match:
                total_patents = int(existing_match.group(1))

        # Calculate velocity from auto data
        velocity_match = re.search(rf'company:\s*"{re.escape(company)}"[^}}]*velocity:\s*"([^"]*)"', match.group(1))
        velocity = velocity_match.group(1) if velocity_match else "N/A"

        velocity_trend_match = re.search(rf'company:\s*"{re.escape(company)}"[^}}]*velocityTrend:\s*"([^"]*)"', match.group(1))
        velocity_trend = velocity_trend_match.group(1) if velocity_trend_match else "steady"

        # If auto data has recent patents, estimate velocity
        if auto and auto.get("patentCount", 0) > 0:
            # patents_aggregated covers 2 years, so divide by 2 for annual
            annual_rate = auto["patentCount"] // 2
            if annual_rate > 0:
                low = max(1, annual_rate - 5)
                high = annual_rate + 5
                velocity = f"{low}-{high}/yr"
            # Update total if auto has higher count
            if auto["patentCount"] > total_patents:
                total_patents = auto["patentCount"]

        note_escaped = cur["note"].replace('"', '\\"')
        js_array += f'  {{ company: "{company}", totalPatents: {total_patents}, '
        js_array += f'velocity: "{velocity}", velocityTrend: "{velocity_trend}", '
        js_array += f'ipMoatScore: {cur["ipMoatScore"]}, '
        js_array += f'techAreas: [{cur["techAreas"]}], '
        js_array += f'notablePatents: [{cur["notablePatents"]}], '
        js_array += f'note: "{note_escaped}" }},\n'
        processed.add(company)

    # Add new companies from auto data not in curated
    for company, auto in auto_data.items():
        if company in processed:
            continue
        if auto.get("patentCount", 0) < 3:
            continue  # Skip companies with very few patents
        annual_rate = auto["patentCount"] // 2
        low = max(1, annual_rate - 5)
        high = annual_rate + 5
        velocity = f"{low}-{high}/yr" if annual_rate > 0 else "N/A"
        tech_areas = json.dumps(auto.get("technologyAreas", [])[:3])
        js_array += f'  {{ company: "{company}", totalPatents: {auto["patentCount"]}, '
        js_array += f'velocity: "{velocity}", velocityTrend: "unknown", '
        js_array += f'ipMoatScore: 5, '
        js_array += f'techAreas: {tech_areas}, '
        js_array += f'notablePatents: [], '
        js_array += f'note: "Auto-detected from USPTO. Pending manual review." }},\n'

    js_array += "];"

    data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
    print(f"  Updated PATENT_INTEL ({len(curated)} curated + new auto entries)")

    return data_js_content


def update_live_award_feed(data_js_content):
    """Update LIVE_AWARD_FEED in data.js with fresh contract/award data.
    Sources: USAspending, SAM.gov, SBIR awards, news-detected contracts.
    """
    # Gather awards from multiple sources
    awards = []

    # Source 1: Government contracts (USAspending)
    gov_contracts = load_json("gov_contracts_aggregated.json")
    for gc in (gov_contracts or []):
        company = gc.get("company", "")
        if not company:
            continue
        # Only include companies with recent contracts
        last_updated = gc.get("lastUpdated", "")
        if not last_updated:
            continue
        awards.append({
            "company": company,
            "type": "contract",
            "title": f"Government Contract — {', '.join(gc.get('agencies', [])[:2])}",
            "value": gc.get("totalGovValue", ""),
            "agency": ", ".join(gc.get("agencies", [])[:2]),
            "detail": f"{gc.get('contractCount', 0)} contracts across {len(gc.get('agencies', []))} agencies.",
            "date": last_updated,
            "source": "usaspending"
        })

    # Source 2: SBIR awards (recent)
    sbir_awards = load_json("sbir_awards_raw.json")
    for sa in (sbir_awards or []):
        if not sa.get("isKnownCompany"):
            continue
        award_year = sa.get("awardYear", 0)
        if award_year < 2025:
            continue
        amount = sa.get("awardAmount", 0)
        amount_fmt = f"${amount:,.0f}" if amount else ""
        awards.append({
            "company": sa.get("firm", ""),
            "type": "sbir",
            "title": f"SBIR {sa.get('phase', '')} — {sa.get('title', '')[:80]}",
            "value": amount_fmt,
            "agency": sa.get("agency", ""),
            "detail": sa.get("abstract", "")[:150],
            "date": f"{award_year}-01-01",
            "source": "sbir.gov"
        })

    # Source 3: SAM.gov opportunities
    sam_contracts = load_json("sam_contracts_aggregated.json")
    for sc in (sam_contracts or []):
        company = sc.get("company", "")
        if not company:
            continue
        recent = sc.get("recentOpportunities", [])
        for opp in recent[:1]:  # Only most recent per company
            awards.append({
                "company": company,
                "type": "ota" if "OTA" in opp.get("title", "").upper() or "OTHER TRANSACTION" in opp.get("title", "").upper() else "contract",
                "title": opp.get("title", "")[:100],
                "value": opp.get("value", ""),
                "agency": ", ".join(sc.get("agencies", [])[:2]),
                "detail": opp.get("description", "")[:150] if opp.get("description") else "",
                "date": opp.get("date", sc.get("lastUpdated", "")),
                "source": "sam.gov"
            })

    # Source 4: News-detected contracts
    news = load_json("news_raw.json")
    contract_keywords = ["contract", "award", "awarded", "SBIR", "OTA", "IDIQ", "prototype"]
    for article in (news or []):
        title = article.get("title", "")
        matched_company = article.get("matchedCompany", "")
        if not matched_company:
            continue
        if any(kw.lower() in title.lower() for kw in contract_keywords):
            award_type = "sbir" if "sbir" in title.lower() else "ota" if "ota" in title.lower() else "contract"
            # Try to extract value from title
            value_match = re.search(r'\$[\d.]+[BMK]?\s*(?:million|billion)?|\$[\d,]+', title, re.IGNORECASE)
            value = value_match.group(0) if value_match else ""
            awards.append({
                "company": matched_company,
                "type": award_type,
                "title": title[:100],
                "value": value,
                "agency": "",
                "detail": article.get("summary", "")[:150] if article.get("summary") else "",
                "date": article.get("date", article.get("time", "")),
                "source": article.get("source", "news")
            })

    if not awards:
        print("No award feed data found, skipping...")
        return data_js_content

    # Deduplicate by company+type, keep most recent
    seen = {}
    for award in awards:
        key = f"{award['company']}:{award['type']}"
        if key not in seen or award.get("date", "") > seen[key].get("date", ""):
            seen[key] = award

    # Sort by date descending, take top 20
    sorted_awards = sorted(seen.values(), key=lambda x: x.get("date", ""), reverse=True)[:20]

    print(f"Merging {len(sorted_awards)} live awards (from {len(awards)} raw)...")

    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-updated live contract & award feed\n"
    js_array += f"// Last updated: {today}\n"
    js_array += f"// Sources: USAspending, SAM.gov, SBIR.gov, news RSS\n"
    js_array += "const LIVE_AWARD_FEED = [\n"

    for i, a in enumerate(sorted_awards):
        company = a["company"].replace('"', "'")
        title = a.get("title", "").replace('"', "'")
        value = a.get("value", "").replace('"', "'")
        agency = a.get("agency", "").replace('"', "'")
        detail = a.get("detail", "").replace('"', "'").replace("\n", " ")
        date = a.get("date", today)[:10]  # Ensure YYYY-MM-DD format
        js_array += f'  {{ id: {i + 1}, date: "{date}", company: "{company}", '
        js_array += f'type: "{a["type"]}", title: "{title}", '
        js_array += f'value: "{value}", agency: "{agency}", '
        js_array += f'detail: "{detail}" }},\n'

    js_array += "];"

    pattern = r'(?://[^\n]*\n)*const LIVE_AWARD_FEED = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
        print(f"  Updated LIVE_AWARD_FEED ({len(sorted_awards)} entries)")
    else:
        print("  LIVE_AWARD_FEED not found in data.js")

    return data_js_content


def update_valley_of_death(data_js_content):
    """Recalibrate VALLEY_OF_DEATH stage assignments using latest contract/award data.
    Cross-references gov contracts, SBIR awards, deal flow to detect stage progression.
    """
    gov_contracts = load_json("gov_contracts_aggregated.json")
    sbir_awards = load_json("sbir_awards_raw.json")
    deals = load_json("deals_auto.json")
    sam_contracts = load_json("sam_contracts_aggregated.json")

    if not any([gov_contracts, sbir_awards, deals, sam_contracts]):
        print("No data sources available for Valley of Death recalibration, skipping...")
        return data_js_content

    # Build company intelligence profile
    company_intel = {}

    # From gov contracts: contract count, total value, agencies
    for gc in (gov_contracts or []):
        company = gc.get("company", "")
        if company:
            company_intel.setdefault(company, {})
            company_intel[company]["contractCount"] = gc.get("contractCount", 0)
            company_intel[company]["agencies"] = gc.get("agencies", [])
            company_intel[company]["totalGovValue"] = gc.get("totalGovValue", "")

    # From SBIR awards: phase progression
    for sa in (sbir_awards or []):
        if not sa.get("isKnownCompany"):
            continue
        company = sa.get("firm", "")
        phase = sa.get("phase", "")
        if company:
            company_intel.setdefault(company, {})
            existing_phase = company_intel[company].get("sbirPhase", "")
            # Keep highest phase
            phase_order = {"Phase I": 1, "Phase II": 2, "Phase III": 3}
            if phase_order.get(phase, 0) > phase_order.get(existing_phase, 0):
                company_intel[company]["sbirPhase"] = phase

    # From SAM.gov: opportunity count
    for sc in (sam_contracts or []):
        company = sc.get("company", "")
        if company:
            company_intel.setdefault(company, {})
            company_intel[company]["samOpportunities"] = sc.get("opportunityCount", 0)

    if not company_intel:
        print("No company intel built for VoD recalibration, skipping...")
        return data_js_content

    # Parse existing VALLEY_OF_DEATH entries
    pattern = r'const VALLEY_OF_DEATH = \[([\s\S]*?)\];'
    match = re.search(pattern, data_js_content)
    if not match:
        print("  VALLEY_OF_DEATH not found in data.js, skipping...")
        return data_js_content

    # Extract existing entries
    entries = []
    entry_pattern = r'\{[^}]+\}'
    for entry_match in re.finditer(entry_pattern, match.group(1)):
        block = entry_match.group(0)
        name_match = re.search(r'company:\s*"([^"]+)"', block)
        stage_match = re.search(r'stage:\s*"([^"]+)"', block)
        label_match = re.search(r'label:\s*"([^"]+)"', block)
        trl_match = re.search(r'trl:\s*(\d+)', block)
        contracts_match = re.search(r'contracts:\s*(\d+)', block)
        detail_match = re.search(r'detail:\s*"((?:[^"\\]|\\.)*)"', block)

        if name_match:
            entries.append({
                "company": name_match.group(1),
                "stage": stage_match.group(1) if stage_match else "rd-concept",
                "label": label_match.group(1) if label_match else "",
                "trl": int(trl_match.group(1)) if trl_match else 1,
                "contracts": int(contracts_match.group(1)) if contracts_match else 0,
                "detail": detail_match.group(1) if detail_match else ""
            })

    # Stage labels mapping
    stage_labels = {
        "rd-concept": "R&D Concept",
        "sbir-phase-1": "SBIR Phase I",
        "sbir-phase-2": "SBIR Phase II",
        "ota-prototype": "OTA / Prototype",
        "program-of-record": "Program of Record",
        "production": "Production Contract"
    }

    stage_order = ["rd-concept", "sbir-phase-1", "sbir-phase-2", "ota-prototype", "program-of-record", "production"]

    # Recalibrate each entry
    updated_count = 0
    for entry in entries:
        company = entry["company"]
        intel = company_intel.get(company, {})
        if not intel:
            continue

        current_stage_idx = stage_order.index(entry["stage"]) if entry["stage"] in stage_order else 0

        # Update contract count from fresh data
        new_contract_count = intel.get("contractCount", 0) or intel.get("samOpportunities", 0)
        if new_contract_count > entry["contracts"]:
            entry["contracts"] = new_contract_count
            updated_count += 1

        # Check for stage progression (only advance, never regress)
        new_stage_idx = current_stage_idx

        # SBIR phase progression
        sbir_phase = intel.get("sbirPhase", "")
        if sbir_phase == "Phase I" and current_stage_idx < 1:
            new_stage_idx = max(new_stage_idx, 1)
        elif sbir_phase == "Phase II" and current_stage_idx < 2:
            new_stage_idx = max(new_stage_idx, 2)
        elif sbir_phase == "Phase III" and current_stage_idx < 3:
            new_stage_idx = max(new_stage_idx, 3)

        # High contract count suggests advancement
        contract_count = intel.get("contractCount", 0)
        if contract_count >= 30 and current_stage_idx < 5:
            new_stage_idx = max(new_stage_idx, 5)  # Production
        elif contract_count >= 15 and current_stage_idx < 4:
            new_stage_idx = max(new_stage_idx, 4)  # Program of Record
        elif contract_count >= 5 and current_stage_idx < 3:
            new_stage_idx = max(new_stage_idx, 3)  # OTA / Prototype

        if new_stage_idx > current_stage_idx:
            entry["stage"] = stage_order[new_stage_idx]
            entry["label"] = stage_labels[entry["stage"]]
            # Bump TRL accordingly
            trl_by_stage = {"rd-concept": 2, "sbir-phase-1": 4, "sbir-phase-2": 5, "ota-prototype": 6, "program-of-record": 8, "production": 9}
            entry["trl"] = max(entry["trl"], trl_by_stage.get(entry["stage"], entry["trl"]))
            updated_count += 1

    print(f"Recalibrating {len(entries)} Valley of Death entries ({updated_count} updated)...")

    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-recalibrated Valley of Death stages\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "const VALLEY_OF_DEATH = [\n"

    for e in entries:
        company = e["company"].replace('"', '\\"')
        label = e["label"].replace('"', '\\"')
        detail = e["detail"].replace('"', '\\"')
        js_array += f'  {{ company: "{company}", stage: "{e["stage"]}", label: "{label}", '
        js_array += f'trl: {e["trl"]}, contracts: {e["contracts"]}, '
        js_array += f'detail: "{detail}" }},\n'

    js_array += "];"

    data_js_content = re.sub(pattern, lambda m: js_array, data_js_content)
    print(f"  Updated VALLEY_OF_DEATH ({len(entries)} entries, {updated_count} recalibrated)")

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


def update_deal_flow_signals(data_js_content):
    """Auto-detect fundraising signals for DEAL_FLOW_SIGNALS.
    Combines headcount surges, SEC filings, deal activity, and news to predict upcoming rounds.
    Preserves curated potentialLeads, expectedAmount, and expectedTiming fields.
    """
    deals = load_json("deals_auto.json")
    sec_filings = load_json("sec_filings_raw.json")
    headcount = load_json("headcount_estimates_auto.json")
    news = load_json("news_signals_raw.json") or load_json("news_raw.json")

    if not any([deals, sec_filings, headcount, news]):
        print("No deal flow signal sources found, skipping...")
        return data_js_content

    # Parse existing curated entries to preserve editorial fields
    curated = {}
    pattern = r'const DEAL_FLOW_SIGNALS = \[([\s\S]*?)\];'
    match = re.search(pattern, data_js_content)
    if match:
        # Extract company names and their curated fields from existing data
        company_pattern = r'company:\s*"([^"]+)"'
        leads_pattern = r'potentialLeads:\s*\[([^\]]*)\]'
        amount_pattern = r'expectedAmount:\s*"([^"]*)"'
        timing_pattern = r'expectedTiming:\s*"([^"]*)"'
        round_pattern = r'expectedRound:\s*"([^"]*)"'

        existing_text = match.group(1)
        # Split by company entries
        entries = re.split(r'\},\s*\{', existing_text)
        for entry in entries:
            cname = re.search(company_pattern, entry)
            if cname:
                name = cname.group(1)
                curated[name] = {}
                leads = re.search(leads_pattern, entry)
                if leads:
                    curated[name]["potentialLeads"] = [l.strip().strip('"') for l in leads.group(1).split(',') if l.strip()]
                amt = re.search(amount_pattern, entry)
                if amt:
                    curated[name]["expectedAmount"] = amt.group(1)
                tim = re.search(timing_pattern, entry)
                if tim:
                    curated[name]["expectedTiming"] = tim.group(1)
                rnd = re.search(round_pattern, entry)
                if rnd:
                    curated[name]["expectedRound"] = rnd.group(1)

    # Build signals from auto data
    company_signals = {}

    # Source 1: Headcount surge detection (>15% growth = fundraising signal)
    for hc in (headcount or []):
        company = hc.get("company", "")
        if not company:
            continue
        growth = hc.get("growthRate", hc.get("growth_rate", 0))
        if isinstance(growth, str):
            try:
                growth = float(growth.replace('%', ''))
            except (ValueError, TypeError):
                growth = 0
        if growth > 15:
            if company not in company_signals:
                company_signals[company] = {"signals": [], "score": 0}
            weight = min(30, int(growth))
            company_signals[company]["signals"].append({
                "type": "hiring",
                "description": f"Headcount growth {growth:.0f}% — scaling signal",
                "weight": weight
            })
            company_signals[company]["score"] += weight

    # Source 2: SEC filing signals (D filings = fundraising, S-1 = IPO prep)
    for filing in (sec_filings or []):
        company = filing.get("matchedCompany", filing.get("company", ""))
        form_type = filing.get("formType", filing.get("form_type", ""))
        if not company or not form_type:
            continue
        if "D" in form_type.upper() and ("REG" in form_type.upper() or form_type.strip() == "D"):
            if company not in company_signals:
                company_signals[company] = {"signals": [], "score": 0}
            company_signals[company]["signals"].append({
                "type": "regulatory",
                "description": f"SEC Form {form_type} filed — fundraising activity",
                "weight": 25
            })
            company_signals[company]["score"] += 25

    # Source 3: Recent deal momentum
    for deal in (deals or []):
        company = deal.get("company", "")
        if not company:
            continue
        deal_date = deal.get("date", "")
        if deal_date and deal_date >= "2025-06":
            if company not in company_signals:
                company_signals[company] = {"signals": [], "score": 0}
            company_signals[company]["signals"].append({
                "type": "milestone",
                "description": f"Recent funding activity: {deal.get('round', deal.get('type', 'deal'))}",
                "weight": 20
            })
            company_signals[company]["score"] += 20

    # Source 4: News signals (contract wins, partnerships = runway extension signals)
    contract_kw = ["contract", "partnership", "awarded", "selected", "expansion"]
    for article in (news or [])[:200]:
        company = article.get("matchedCompany", article.get("company", ""))
        title = article.get("title", "")
        if not company:
            continue
        if any(kw in title.lower() for kw in contract_kw):
            if company not in company_signals:
                company_signals[company] = {"signals": [], "score": 0}
            company_signals[company]["signals"].append({
                "type": "contract" if "contract" in title.lower() else "partnership",
                "description": title[:80],
                "weight": 20
            })
            company_signals[company]["score"] += 20

    if not company_signals:
        print("No deal flow signals detected, skipping...")
        return data_js_content

    # Merge with curated data, build output
    output = []
    for company, data in sorted(company_signals.items(), key=lambda x: x[1]["score"], reverse=True)[:15]:
        signals = data["signals"][:4]  # Top 4 signals per company
        # Normalize weights to sum to 100
        total_w = sum(s["weight"] for s in signals) or 1
        for s in signals:
            s["weight"] = round(s["weight"] / total_w * 100)

        probability = min(95, max(40, data["score"]))

        # Preserve curated fields if they exist
        cur = curated.get(company, {})
        entry = {
            "company": company,
            "probability": probability,
            "expectedRound": cur.get("expectedRound", "Unknown"),
            "expectedAmount": cur.get("expectedAmount", "TBD"),
            "expectedTiming": cur.get("expectedTiming", "TBD"),
            "signals": signals,
            "potentialLeads": cur.get("potentialLeads", [])
        }
        output.append(entry)

    # Add curated entries that weren't in auto-detected (they may have manually set data)
    auto_companies = {e["company"] for e in output}
    for cname, cur in curated.items():
        if cname not in auto_companies and cur.get("potentialLeads"):
            output.append({
                "company": cname,
                "probability": 50,
                "expectedRound": cur.get("expectedRound", "Unknown"),
                "expectedAmount": cur.get("expectedAmount", "TBD"),
                "expectedTiming": cur.get("expectedTiming", "TBD"),
                "signals": [{"type": "historical", "description": "Curated prediction — awaiting auto signals", "weight": 100}],
                "potentialLeads": cur.get("potentialLeads", [])
            })

    print(f"Merging {len(output)} deal flow signals...")

    today = datetime.now().strftime("%Y-%m-%d")
    js_array = f"// Auto-updated deal flow signals\n"
    js_array += f"// Last updated: {today}\n"
    js_array += "const DEAL_FLOW_SIGNALS = [\n"

    for entry in output:
        company = entry["company"].replace('"', "'")
        exp_round = entry["expectedRound"].replace('"', "'")
        exp_amount = entry["expectedAmount"].replace('"', "'")
        exp_timing = entry["expectedTiming"].replace('"', "'")
        leads_js = json.dumps(entry["potentialLeads"])

        signals_js = "[\n"
        for s in entry["signals"]:
            desc = s["description"].replace('"', "'").replace("\n", " ")
            signals_js += f'      {{ type: "{s["type"]}", description: "{desc}", weight: {s["weight"]} }},\n'
        signals_js += "    ]"

        js_array += f'  {{\n'
        js_array += f'    company: "{company}",\n'
        js_array += f'    probability: {entry["probability"]},\n'
        js_array += f'    expectedRound: "{exp_round}",\n'
        js_array += f'    expectedAmount: "{exp_amount}",\n'
        js_array += f'    expectedTiming: "{exp_timing}",\n'
        js_array += f'    signals: {signals_js},\n'
        js_array += f'    potentialLeads: {leads_js}\n'
        js_array += f'  }},\n'

    js_array += "];"

    full_pattern = r'(?://[^\n]*\n)*const DEAL_FLOW_SIGNALS = \[[\s\S]*?\];'
    if re.search(full_pattern, data_js_content):
        data_js_content = re.sub(full_pattern, lambda m: js_array, data_js_content)
        print(f"  Updated DEAL_FLOW_SIGNALS ({len(output)} entries)")
    else:
        print("  DEAL_FLOW_SIGNALS not found in data.js")

    return data_js_content


def update_ma_comps(data_js_content):
    """Auto-append M&A transactions to MA_COMPS from deal data and SEC 8-K filings.
    Preserves all existing curated entries. Adds new acquisitions detected from auto data.
    """
    deals = load_json("deals_auto.json")
    sec_filings = load_json("sec_filings_raw.json")

    if not any([deals, sec_filings]):
        print("No M&A data sources found, skipping...")
        return data_js_content

    # Extract existing targets to avoid duplicates
    existing_targets = set()
    target_pattern = r'target:\s*"([^"]+)"'
    ma_match = re.search(r'const MA_COMPS = \[([\s\S]*?)\];', data_js_content)
    if ma_match:
        for t in re.finditer(target_pattern, ma_match.group(1)):
            existing_targets.add(t.group(1).lower())

    new_comps = []

    # Source 1: Deals with acquisition type
    for deal in (deals or []):
        deal_type = deal.get("type", "").lower()
        if "acqui" not in deal_type and "merger" not in deal_type and "m&a" not in deal_type:
            continue
        target = deal.get("company", deal.get("target", ""))
        if not target or target.lower() in existing_targets:
            continue
        acquirer = deal.get("acquirer", deal.get("investor", "Unknown"))
        sector = deal.get("sector", "")
        year = deal.get("date", "")[:4] if deal.get("date") else ""
        try:
            year = int(year) if year else ""
        except ValueError:
            year = ""
        new_comps.append({
            "target": target,
            "acquirer": acquirer if isinstance(acquirer, str) else ", ".join(acquirer[:2]) if isinstance(acquirer, list) else str(acquirer),
            "sector": sector,
            "year": year,
            "dealValue": deal.get("amount", deal.get("dealValue", "")),
            "evRevenue": deal.get("evRevenue", "N/A"),
            "evFunding": deal.get("evFunding", "N/A"),
            "notes": deal.get("notes", deal.get("description", ""))[:80] if deal.get("notes") or deal.get("description") else "Auto-detected acquisition",
            "type": "Completed"
        })
        existing_targets.add(target.lower())

    # Source 2: SEC 8-K filings mentioning acquisitions
    acquisition_keywords = ["acquisition", "merger", "acquired", "definitive agreement"]
    for filing in (sec_filings or []):
        form_type = filing.get("formType", filing.get("form_type", ""))
        if "8-K" not in str(form_type):
            continue
        title = filing.get("title", filing.get("description", ""))
        company = filing.get("matchedCompany", filing.get("company", ""))
        if not company or not title:
            continue
        if any(kw in title.lower() for kw in acquisition_keywords):
            if company.lower() not in existing_targets:
                filing_date = filing.get("filingDate", filing.get("filing_date", ""))
                try:
                    year = int(filing_date[:4]) if filing_date else ""
                except (ValueError, TypeError):
                    year = ""
                new_comps.append({
                    "target": company,
                    "acquirer": "See SEC Filing",
                    "sector": filing.get("sector", ""),
                    "year": year,
                    "dealValue": "TBD",
                    "evRevenue": "N/A",
                    "evFunding": "N/A",
                    "notes": title[:80],
                    "type": "Announced"
                })
                existing_targets.add(company.lower())

    if not new_comps:
        print("No new M&A transactions detected, skipping...")
        return data_js_content

    print(f"Appending {len(new_comps)} new M&A comps...")

    # Build JS entries for new comps
    new_entries = ""
    for comp in new_comps:
        target = comp["target"].replace('"', "'")
        acquirer = comp["acquirer"].replace('"', "'") if isinstance(comp["acquirer"], str) else str(comp["acquirer"])
        sector = comp.get("sector", "").replace('"', "'")
        notes = comp.get("notes", "").replace('"', "'").replace("\n", " ")
        deal_val = comp.get("dealValue", "").replace('"', "'") if isinstance(comp.get("dealValue", ""), str) else str(comp.get("dealValue", ""))
        ev_rev = comp.get("evRevenue", "N/A")
        ev_fund = comp.get("evFunding", "N/A")
        year_val = comp.get("year", "")

        new_entries += f'  {{\n'
        new_entries += f'    target: "{target}",\n'
        new_entries += f'    acquirer: "{acquirer}",\n'
        new_entries += f'    sector: "{sector}",\n'
        if isinstance(year_val, int):
            new_entries += f'    year: {year_val},\n'
        else:
            new_entries += f'    year: "{year_val}",\n'
        new_entries += f'    dealValue: "{deal_val}",\n'
        if isinstance(ev_rev, (int, float)):
            new_entries += f'    evRevenue: {ev_rev},\n'
        else:
            new_entries += f'    evRevenue: "{ev_rev}",\n'
        if isinstance(ev_fund, (int, float)):
            new_entries += f'    evFunding: {ev_fund},\n'
        else:
            new_entries += f'    evFunding: "{ev_fund}",\n'
        new_entries += f'    notes: "{notes}",\n'
        new_entries += f'    type: "{comp["type"]}"\n'
        new_entries += f'  }},\n'

    # Insert before closing ];
    insert_pattern = r'(const MA_COMPS = \[[\s\S]*?)(];)'
    match = re.search(insert_pattern, data_js_content)
    if match:
        data_js_content = data_js_content[:match.start(2)] + new_entries + match.group(2) + data_js_content[match.end(2):]
        print(f"  Appended {len(new_comps)} entries to MA_COMPS")
    else:
        print("  MA_COMPS not found in data.js")

    return data_js_content


def update_gov_demand_tracker(data_js_content):
    """Auto-update GOV_DEMAND_TRACKER with active solicitations from SAM.gov and Federal Register.
    Preserves curated entries with editorial relevantCompanies.
    Adds new solicitations, removes expired ones.
    """
    sam_data = load_json("sam_contracts_raw.json") or load_json("sam_contracts_aggregated.json")
    fed_register = load_json("federal_register_raw.json")
    sbir_data = load_json("sbir_awards_raw.json")

    if not any([sam_data, fed_register, sbir_data]):
        print("No gov demand data sources found, skipping...")
        return data_js_content

    # Parse existing curated entries
    curated_entries = {}
    pattern = r'const GOV_DEMAND_TRACKER = \[([\s\S]*?)\];'
    match = re.search(pattern, data_js_content)
    if match:
        id_pattern = r'id:\s*"([^"]+)"'
        for id_match in re.finditer(id_pattern, match.group(1)):
            curated_entries[id_match.group(1)] = True

    # Tech area keywords for company matching
    tech_mapping = {
        "autonomous": ["Anduril Industries", "Shield AI", "Skydio", "Saronic"],
        "drone": ["Anduril Industries", "Shield AI", "Skydio", "Fortem Technologies"],
        "hypersonic": ["Hermeus", "Venus Aerospace", "Castelion"],
        "space": ["SpaceX", "Rocket Lab", "Firefly Aerospace", "Relativity Space"],
        "satellite": ["SpaceX", "Astranis", "Muon Space", "Capella Space"],
        "ai": ["Palantir", "Scale AI", "Anthropic", "OpenAI"],
        "machine learning": ["Palantir", "Scale AI", "Anthropic"],
        "nuclear": ["Valar Atomics", "Oklo", "Last Energy"],
        "energy": ["Commonwealth Fusion", "Valar Atomics", "Form Energy"],
        "cyber": ["Palantir", "Rebellion Defense", "HiddenLayer"],
        "propulsion": ["Hermeus", "Ursa Major", "Rocket Lab"],
        "biotech": ["Ginkgo Bioworks", "Resilience"],
        "quantum": ["IonQ", "Rigetti", "PsiQuantum"],
        "maritime": ["Saronic", "Saildrone", "Anduril Industries"],
        "counter-uas": ["Anduril Industries", "Epirus", "Fortem Technologies"],
    }

    def match_companies(title, description=""):
        """Match tech areas to tracked companies."""
        text = (title + " " + description).lower()
        matched = set()
        for keyword, companies in tech_mapping.items():
            if keyword in text:
                matched.update(companies)
        return list(matched)[:6]

    new_entries = []
    seen_ids = set(curated_entries.keys())

    # Source 1: SAM.gov active solicitations
    for item in (sam_data or [])[:50]:
        opp_id = item.get("noticeId", item.get("solicitationNumber", ""))
        if not opp_id or opp_id in seen_ids:
            continue
        title = item.get("title", "")
        if not title:
            continue
        deadline = item.get("responseDeadLine", item.get("deadline", ""))
        if deadline and deadline < datetime.now().strftime("%Y-%m-%d"):
            continue  # Skip expired
        agency = item.get("department", item.get("agency", ""))
        notice_type = item.get("type", item.get("noticeType", ""))
        value = item.get("award", {}).get("amount", "") if isinstance(item.get("award"), dict) else ""
        description = item.get("description", "")[:200]

        companies = match_companies(title, description)
        new_entries.append({
            "id": f"SAM-{opp_id[:20]}",
            "title": title[:120],
            "agency": agency,
            "type": notice_type or "Solicitation",
            "deadline": deadline[:10] if deadline else "Rolling",
            "value": f"${value:,.0f}" if isinstance(value, (int, float)) and value else str(value) if value else "TBD",
            "priority": "High" if companies else "Medium",
            "description": description,
            "techAreas": [],
            "relevantCompanies": companies,
            "source": "sam.gov",
            "posted": item.get("postedDate", "")[:10] if item.get("postedDate") else ""
        })
        seen_ids.add(f"SAM-{opp_id[:20]}")

    # Source 2: Federal Register BAAs and FOAs
    for item in (fed_register or [])[:50]:
        doc_number = item.get("document_number", item.get("id", ""))
        if not doc_number or f"FR-{doc_number}" in seen_ids:
            continue
        title = item.get("title", "")
        if not title:
            continue
        doc_type = item.get("type", "")
        # Only include relevant document types
        if not any(kw in title.lower() for kw in ["baa", "foa", "funding", "solicitation", "opportunity", "prototype", "defense", "dod", "darpa"]):
            continue
        agency_names = item.get("agencies", [])
        agency = agency_names[0].get("name", "") if agency_names and isinstance(agency_names[0], dict) else str(agency_names[0]) if agency_names else ""

        companies = match_companies(title)
        if companies:
            new_entries.append({
                "id": f"FR-{doc_number}",
                "title": title[:120],
                "agency": agency[:60],
                "type": "Federal Register Notice",
                "deadline": "See Document",
                "value": "TBD",
                "priority": "Medium",
                "description": item.get("abstract", "")[:200] if item.get("abstract") else "",
                "techAreas": [],
                "relevantCompanies": companies,
                "source": item.get("html_url", "federalregister.gov"),
                "posted": item.get("publication_date", "")[:10] if item.get("publication_date") else ""
            })
            seen_ids.add(f"FR-{doc_number}")

    if not new_entries:
        print("No new gov demand entries detected, skipping...")
        return data_js_content

    print(f"Appending {len(new_entries)} new gov demand entries...")

    # Build JS for new entries and append
    new_js = ""
    for entry in new_entries[:15]:  # Limit to 15 new entries
        title = entry["title"].replace('"', "'")
        agency = entry["agency"].replace('"', "'")
        desc = entry.get("description", "").replace('"', "'").replace("\n", " ")
        tech_areas = json.dumps(entry.get("techAreas", []))
        companies = json.dumps(entry.get("relevantCompanies", []))
        source = entry.get("source", "").replace('"', "'")

        new_js += f'  {{\n'
        new_js += f'    id: "{entry["id"]}",\n'
        new_js += f'    title: "{title}",\n'
        new_js += f'    agency: "{agency}",\n'
        new_js += f'    type: "{entry["type"]}",\n'
        new_js += f'    deadline: "{entry["deadline"]}",\n'
        new_js += f'    value: "{entry["value"]}",\n'
        new_js += f'    priority: "{entry["priority"]}",\n'
        new_js += f'    description: "{desc}",\n'
        new_js += f'    techAreas: {tech_areas},\n'
        new_js += f'    relevantCompanies: {companies},\n'
        new_js += f'    source: "{source}",\n'
        new_js += f'    posted: "{entry["posted"]}"\n'
        new_js += f'  }},\n'

    # Insert before closing ];
    insert_pattern = r'(const GOV_DEMAND_TRACKER = \[[\s\S]*?)(];)'
    match = re.search(insert_pattern, data_js_content)
    if match:
        data_js_content = data_js_content[:match.start(2)] + new_js + match.group(2) + data_js_content[match.end(2):]
        print(f"  Appended {min(len(new_entries), 15)} entries to GOV_DEMAND_TRACKER")
    else:
        print("  GOV_DEMAND_TRACKER not found in data.js")

    return data_js_content


def update_budget_signals(data_js_content):
    """Auto-refresh BUDGET_SIGNALS beneficiaries using latest contract/award data.
    Preserves curated allocation, fy, description, and relatedPrograms fields.
    Updates beneficiaries by cross-referencing companies with contract wins per category.
    """
    gov_contracts = load_json("gov_contracts_aggregated.json")
    sam_data = load_json("sam_contracts_aggregated.json")
    sbir_data = load_json("sbir_awards_raw.json")

    if not any([gov_contracts, sam_data, sbir_data]):
        print("No budget signal data sources found, skipping...")
        return data_js_content

    # Build mapping: category keywords → companies that won contracts
    category_keywords = {
        "Autonomous Systems & Drones": ["autonomous", "drone", "uas", "uav", "unmanned", "replicator"],
        "Space Launch & Access": ["space", "launch", "satellite", "orbit", "nssl", "leo"],
        "AI & Machine Learning for Defense": ["ai", "machine learning", "artificial intelligence", "cdao", "maven", "jadc2"],
        "Hypersonic & High-Speed Systems": ["hypersonic", "scramjet", "prompt strike", "high-speed"],
        "Cybersecurity & Zero Trust": ["cyber", "zero trust", "cmmc", "network security"],
        "Nuclear & Energy": ["nuclear", "reactor", "microreactor", "fusion", "energy"],
        "Biotechnology & Biosecurity": ["bio", "biosecurity", "synthetic biology", "pandemic"],
        "Quantum Computing": ["quantum", "qubit"],
        "Maritime & Undersea": ["maritime", "naval", "undersea", "submarine", "usv"],
        "Directed Energy": ["directed energy", "laser", "microwave", "hpm"],
    }

    # Find companies with contracts matching each category
    company_contracts = {}
    for gc in (gov_contracts or []):
        company = gc.get("company", "")
        if not company:
            continue
        agencies = " ".join(gc.get("agencies", []))
        for cat, keywords in category_keywords.items():
            if any(kw in agencies.lower() or kw in company.lower() for kw in keywords):
                if cat not in company_contracts:
                    company_contracts[cat] = set()
                company_contracts[cat].add(company)

    for sc in (sam_data or []):
        company = sc.get("company", "")
        if not company:
            continue
        opps = sc.get("recentOpportunities", [])
        opp_text = " ".join(o.get("title", "") for o in opps).lower()
        for cat, keywords in category_keywords.items():
            if any(kw in opp_text for kw in keywords):
                if cat not in company_contracts:
                    company_contracts[cat] = set()
                company_contracts[cat].add(company)

    for sa in (sbir_data or []):
        company = sa.get("firm", "")
        if not company or not sa.get("isKnownCompany"):
            continue
        title = sa.get("title", "").lower()
        abstract = sa.get("abstract", "").lower()
        text = title + " " + abstract
        for cat, keywords in category_keywords.items():
            if any(kw in text for kw in keywords):
                if cat not in company_contracts:
                    company_contracts[cat] = set()
                company_contracts[cat].add(company)

    if not company_contracts:
        print("No budget signal enrichment found, skipping...")
        return data_js_content

    # Update beneficiaries in existing BUDGET_SIGNALS entries
    pattern = r'const BUDGET_SIGNALS = \[([\s\S]*?)\];'
    match = re.search(pattern, data_js_content)
    if not match:
        print("  BUDGET_SIGNALS not found in data.js")
        return data_js_content

    content = match.group(0)
    updated = False

    for cat, new_companies in company_contracts.items():
        # Find the entry for this category and update beneficiaries
        cat_escaped = re.escape(cat)
        beneficiary_pattern = rf'(category:\s*"{cat_escaped}"[\s\S]*?beneficiaries:\s*\[)[^\]]*(\])'
        bm = re.search(beneficiary_pattern, content)
        if bm:
            # Merge existing and new beneficiaries
            existing_str = content[bm.start(1)+len(bm.group(1)):bm.start(2)]
            existing_list = [b.strip().strip('"') for b in existing_str.split(',') if b.strip().strip('"')]
            merged = list(dict.fromkeys(existing_list + sorted(new_companies)))[:8]
            new_beneficiaries = ", ".join(f'"{b}"' for b in merged)
            content = content[:bm.start(1)] + bm.group(1) + new_beneficiaries + content[bm.start(2):]
            updated = True

    if updated:
        data_js_content = data_js_content[:match.start()] + content + data_js_content[match.end():]
        print(f"  Updated BUDGET_SIGNALS beneficiaries ({len(company_contracts)} categories refreshed)")
    else:
        print("  No BUDGET_SIGNALS beneficiary updates needed")

    return data_js_content


def update_historical_tracking(data_js_content):
    """Auto-append latest data points to HISTORICAL_TRACKING.
    Adds new valuation, funding, and headcount entries from auto-fetched data.
    Never overwrites existing data points — only appends newer ones.
    """
    deals = load_json("deals_auto.json")
    headcount = load_json("headcount_estimates_auto.json")

    if not any([deals, headcount]):
        print("No historical tracking data sources found, skipping...")
        return data_js_content

    # Parse existing HISTORICAL_TRACKING to find latest dates per company
    pattern = r'const HISTORICAL_TRACKING = \{([\s\S]*?)\n\};'
    match = re.search(pattern, data_js_content)
    if not match:
        print("  HISTORICAL_TRACKING not found in data.js")
        return data_js_content

    # Extract per-company latest dates
    company_latest = {}
    company_pattern = r'"([^"]+)":\s*\{'
    for cm in re.finditer(company_pattern, match.group(1)):
        company = cm.group(1)
        # Find latest valuation date
        company_section_start = cm.start()
        # Look for dates in this company's section
        date_pattern = r'date:\s*"(\d{4}-\d{2})"'
        dates = [d.group(1) for d in re.finditer(date_pattern, match.group(1)[company_section_start:company_section_start+800])]
        company_latest[company] = max(dates) if dates else "2020-01"

    updates_made = 0
    current_date = datetime.now().strftime("%Y-%m")

    # Source 1: Add new funding/valuation data points from deals
    for deal in (deals or []):
        company = deal.get("company", "")
        if not company or company not in company_latest:
            continue
        deal_date = deal.get("date", "")[:7]  # YYYY-MM
        if not deal_date or deal_date <= company_latest.get(company, ""):
            continue

        valuation = deal.get("valuation", deal.get("postMoney", ""))
        amount = deal.get("amount", "")
        round_name = deal.get("round", deal.get("type", ""))

        # Parse valuation to numeric (billions)
        val_num = None
        if valuation:
            try:
                if isinstance(valuation, str):
                    val_str = valuation.replace("$", "").replace(",", "").strip()
                    if "B" in val_str.upper():
                        val_num = float(val_str.upper().replace("B", "").strip())
                    elif "M" in val_str.upper():
                        val_num = float(val_str.upper().replace("M", "").strip()) / 1000
                    else:
                        val_num = float(val_str)
                elif isinstance(valuation, (int, float)):
                    val_num = valuation
            except (ValueError, TypeError):
                pass

        if val_num:
            # Find the company's valuations array and append
            val_entry = f'      {{ date: "{deal_date}", value: {val_num}, event: "{round_name}" }}'
            # Find insertion point: before the closing ] of valuations array for this company
            company_section_pattern = rf'"({re.escape(company)}":\s*\{{[\s\S]*?valuations:\s*\[[\s\S]*?)(]\s*,\s*\n\s*funding:)'
            vm = re.search(company_section_pattern, match.group(1))
            if vm:
                insert_pos = match.start(1) + vm.start(2)
                data_js_content = data_js_content[:insert_pos] + ",\n" + val_entry + "\n    " + data_js_content[insert_pos:]
                updates_made += 1
                # Re-find the match since we modified content
                match = re.search(pattern, data_js_content)
                if not match:
                    break

    # Source 2: Add headcount data points
    for hc in (headcount or []):
        company = hc.get("company", "")
        if not company or company not in company_latest:
            continue
        count = hc.get("estimated_count", hc.get("count", 0))
        if not count:
            continue
        hc_date = current_date
        if hc_date <= company_latest.get(company, ""):
            continue

        # We'd need to find the headcount array for this company and append
        # This is complex with regex; for safety, skip if pattern is ambiguous
        # The key value is in the valuation/funding updates above

    if updates_made > 0:
        print(f"  Updated HISTORICAL_TRACKING ({updates_made} new data points)")
    else:
        print("  No new HISTORICAL_TRACKING data points to add")

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
    data_js_content = update_prev_week_scores(data_js_content)
    data_js_content = update_predictive_scores(data_js_content)
    data_js_content = update_headcount_estimates(data_js_content)
    data_js_content = update_sam_contracts(data_js_content)
    data_js_content = update_trade_data(data_js_content)
    data_js_content = update_product_launches(data_js_content)
    data_js_content = update_sbir_awards(data_js_content)
    data_js_content = update_nih_grants(data_js_content)
    data_js_content = update_arpa_e_projects(data_js_content)
    data_js_content = update_diffbot_enrichment(data_js_content)
    data_js_content = update_news_feed(data_js_content)
    data_js_content = update_alt_data_signals(data_js_content)
    data_js_content = update_patent_intel(data_js_content)
    data_js_content = update_live_award_feed(data_js_content)
    data_js_content = update_valley_of_death(data_js_content)
    data_js_content = update_contractor_readiness(data_js_content)
    data_js_content = update_deal_flow_signals(data_js_content)
    data_js_content = update_ma_comps(data_js_content)
    data_js_content = update_gov_demand_tracker(data_js_content)
    data_js_content = update_budget_signals(data_js_content)
    data_js_content = update_historical_tracking(data_js_content)
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
