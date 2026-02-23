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
    """Update VC_FIRMS portfolioCompanies from deal data."""
    deals = load_json("deals_auto.json")
    if not deals:
        print("No deals data found, skipping VC portfolio updates...")
        return data_js_content

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
    for deal in deals:
        investor = deal.get("investor", "")
        company = deal.get("company", "")
        if not investor or not company:
            continue
        vc_short = INVESTOR_TO_VC.get(investor)
        if vc_short:
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
