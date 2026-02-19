#!/usr/bin/env python3
"""
Innovator Scores Calculator for The Innovators League
Auto-generates Frontier Index scores for ALL companies using available data:
  - Patent data (techMoat)
  - News/Jobs/Stocks/Deals (momentum)
  - Founder connections (teamPedigree)
  - Sector momentum (marketGravity)
  - Funding/Revenue data (capitalEfficiency)
  - Gov contracts/SBIR (govTraction)

Preserves manually curated scores for the original 60 companies.
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


def load_js_array(filename, const_name):
    """Extract a JS const array from a .js file."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return []
    with open(filepath) as f:
        content = f.read()
    # Try to extract the array using regex
    pattern = rf'(?:const|var|let)\s+{const_name}\s*=\s*(\[[\s\S]*?\]);'
    match = re.search(pattern, content)
    if not match:
        return []
    try:
        # Clean JS syntax for JSON parsing
        js_str = match.group(1)
        # Remove trailing commas before } or ]
        js_str = re.sub(r',\s*([}\]])', r'\1', js_str)
        # Remove single-line comments
        js_str = re.sub(r'//[^\n]*', '', js_str)
        # Handle unquoted keys
        js_str = re.sub(r'(\{|,)\s*(\w+)\s*:', r'\1"\2":', js_str)
        return json.loads(js_str)
    except json.JSONDecodeError:
        return []


def load_js_object(filename, const_name):
    """Extract a JS const object from a .js file."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        # Try main data.js
        filepath = DATA_JS_PATH
    if not filepath.exists():
        return {}
    with open(filepath) as f:
        content = f.read()
    pattern = rf'(?:const|var|let)\s+{const_name}\s*=\s*(\{{[\s\S]*?\}});'
    match = re.search(pattern, content)
    if not match:
        return {}
    try:
        js_str = match.group(1)
        js_str = re.sub(r',\s*([}\]])', r'\1', js_str)
        js_str = re.sub(r'//[^\n]*', '', js_str)
        js_str = re.sub(r'(\{|,)\s*(\w+)\s*:', r'\1"\2":', js_str)
        return json.loads(js_str)
    except json.JSONDecodeError:
        return {}


def get_company_names():
    """Extract all company names from data.js COMPANIES array."""
    companies = []
    with open(DATA_JS_PATH) as f:
        content = f.read()
    # Find all name: "..." in COMPANIES
    for match in re.finditer(r'name:\s*"([^"]+)"', content):
        name = match.group(1)
        if name and len(name) > 1:
            companies.append(name)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in companies:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


def get_company_sectors():
    """Map company name -> sector from data.js."""
    sectors = {}
    with open(DATA_JS_PATH) as f:
        content = f.read()
    # Use position-based extraction (name→sector within same entry)
    name_positions = [(m.start(), m.group(1)) for m in re.finditer(r'name:\s*"([^"]+)"', content)]
    for i, (pos, name) in enumerate(name_positions):
        end = name_positions[i + 1][0] if i + 1 < len(name_positions) else pos + 2000
        block = content[pos:end]
        sector_m = re.search(r'sector:\s*"([^"]+)"', block)
        if sector_m:
            sectors[name] = sector_m.group(1)
    return sectors


def get_company_stages():
    """Map company name -> funding stage."""
    stages = {}
    with open(DATA_JS_PATH) as f:
        content = f.read()
    name_positions = [(m.start(), m.group(1)) for m in re.finditer(r'name:\s*"([^"]+)"', content)]
    for i, (pos, name) in enumerate(name_positions):
        end = name_positions[i + 1][0] if i + 1 < len(name_positions) else pos + 2000
        block = content[pos:end]
        stage_m = re.search(r'fundingStage:\s*"([^"]+)"', block)
        if stage_m:
            stages[name] = stage_m.group(1)
    return stages


def count_by_company(data, key="company"):
    """Count occurrences per company in a list of dicts."""
    counts = defaultdict(int)
    for item in data:
        if isinstance(item, dict) and key in item:
            counts[item[key]] += 1
    return counts


def count_jobs_by_company(jobs_file):
    """Count open jobs per company from jobs_auto.js."""
    filepath = DATA_DIR / jobs_file
    if not filepath.exists():
        return {}
    with open(filepath) as f:
        content = f.read()
    counts = defaultdict(int)
    for match in re.finditer(r'company:\s*"([^"]+)"', content):
        counts[match.group(1)] += 1
    return counts


def get_stock_changes():
    """Get stock price changes from stocks_auto.js."""
    filepath = DATA_DIR / "stocks_auto.js"
    if not filepath.exists():
        return {}
    with open(filepath) as f:
        content = f.read()
    changes = {}
    # Match patterns like: "PLTR": { ... changePercent: 2.5, ...
    for match in re.finditer(r'"(\w+)":\s*\{[^}]*?name:\s*"([^"]+)"[^}]*?changePercent:\s*([-\d.]+)', content):
        changes[match.group(2)] = float(match.group(3))
    return changes


def get_curated_scores():
    """Load existing curated INNOVATOR_SCORES from data.js."""
    with open(DATA_JS_PATH) as f:
        content = f.read()
    curated = {}
    # Extract each entry from INNOVATOR_SCORES array
    pattern = r'const INNOVATOR_SCORES\s*=\s*\[([\s\S]*?)\];'
    match = re.search(pattern, content)
    if not match:
        return curated
    block = match.group(1)
    # Find each company entry
    for entry in re.finditer(
        r'company:\s*"([^"]+)"[^}]*?techMoat:\s*(\d+)[^}]*?momentum:\s*(\d+)[^}]*?'
        r'teamPedigree:\s*(\d+)[^}]*?marketGravity:\s*(\d+)[^}]*?capitalEfficiency:\s*(\d+)[^}]*?'
        r'govTraction:\s*(\d+)[^}]*?composite:\s*([\d.]+)[^}]*?tier:\s*"([^"]+)"[^}]*?note:\s*"([^"]*)"',
        block
    ):
        curated[entry.group(1)] = {
            "company": entry.group(1),
            "techMoat": int(entry.group(2)),
            "momentum": int(entry.group(3)),
            "teamPedigree": int(entry.group(4)),
            "marketGravity": int(entry.group(5)),
            "capitalEfficiency": int(entry.group(6)),
            "govTraction": int(entry.group(7)),
            "composite": float(entry.group(8)),
            "tier": entry.group(9),
            "note": entry.group(10),
        }
    return curated


def clamp(val, lo=0, hi=10):
    return max(lo, min(hi, round(val)))


def calc_tech_moat(company, patent_counts, arxiv_counts, github_counts):
    """Calculate techMoat score (0-10)."""
    patents = patent_counts.get(company, 0)
    papers = arxiv_counts.get(company, 0)
    github = github_counts.get(company, 0)

    if patents >= 50:
        score = 9
    elif patents >= 20:
        score = 7.5
    elif patents >= 5:
        score = 6
    elif patents >= 1:
        score = 4.5
    else:
        score = 3

    if papers >= 5:
        score += 0.5
    elif papers >= 1:
        score += 0.25
    if github >= 3:
        score += 0.5
    elif github >= 1:
        score += 0.25

    return clamp(score)


def calc_momentum(company, news_counts, job_counts, stock_changes, deal_counts):
    """Calculate momentum score (0-10)."""
    news = news_counts.get(company, 0)
    jobs = job_counts.get(company, 0)
    stock = stock_changes.get(company, 0)
    deals = deal_counts.get(company, 0)

    # News component (0-10)
    if news >= 10:
        news_score = 9
    elif news >= 5:
        news_score = 7
    elif news >= 2:
        news_score = 5
    elif news >= 1:
        news_score = 3.5
    else:
        news_score = 2

    # Jobs component (0-10)
    if jobs >= 100:
        jobs_score = 9
    elif jobs >= 50:
        jobs_score = 7.5
    elif jobs >= 20:
        jobs_score = 6
    elif jobs >= 5:
        jobs_score = 4.5
    elif jobs >= 1:
        jobs_score = 3.5
    else:
        jobs_score = 2

    # Stock component (0-10)
    if stock > 20:
        stock_score = 9
    elif stock > 10:
        stock_score = 7.5
    elif stock > 5:
        stock_score = 6
    elif stock > 0:
        stock_score = 5
    elif stock == 0:
        stock_score = 5  # neutral for private companies
    else:
        stock_score = max(2, 5 + stock / 5)

    # Deals component (0-10)
    if deals >= 3:
        deal_score = 9
    elif deals >= 2:
        deal_score = 7
    elif deals >= 1:
        deal_score = 5.5
    else:
        deal_score = 3

    return clamp(news_score * 0.25 + jobs_score * 0.25 + stock_score * 0.25 + deal_score * 0.25)


def calc_team_pedigree(company, founder_connections, mafia_companies):
    """Calculate teamPedigree score (0-10)."""
    connections = founder_connections.get(company, 0)
    in_mafia = company in mafia_companies

    if connections >= 10:
        score = 9
    elif connections >= 5:
        score = 7.5
    elif connections >= 2:
        score = 6
    elif connections >= 1:
        score = 5
    else:
        score = 5  # neutral default

    if in_mafia:
        score = min(10, score + 1)

    return clamp(score)


def calc_market_gravity(company, sector, sector_momentum):
    """Calculate marketGravity score (0-10)."""
    momentum = sector_momentum.get(sector, 50)  # default 50/100
    return clamp(momentum / 10)  # Map 0-100 to 0-10


def calc_capital_efficiency(company, stage, total_raised_map, revenue_map):
    """Calculate capitalEfficiency score (0-10)."""
    revenue = revenue_map.get(company, 0)
    raised = total_raised_map.get(company, 0)

    if revenue > 0 and raised > 0:
        ratio = revenue / raised
        if ratio >= 2:
            return 9
        elif ratio >= 1:
            return 8
        elif ratio >= 0.5:
            return 7
        elif ratio >= 0.2:
            return 6
        else:
            return 5
    else:
        # Estimate from stage
        stage_scores = {
            "Public": 7, "Pre-IPO": 7, "Late Stage": 6, "Series G": 6,
            "Series F": 6, "Series E": 6, "Series D": 5.5, "Series C": 5,
            "Series B": 4.5, "Series A": 4, "Seed": 3.5, "Pre-Seed": 3,
        }
        for key, val in stage_scores.items():
            if key.lower() in str(stage).lower():
                return val
        return 5  # neutral default


def calc_gov_traction(company, gov_counts, gov_values, sbir_companies, fda_companies, nrc_companies):
    """Calculate govTraction score (0-10)."""
    contracts = gov_counts.get(company, 0)
    value = gov_values.get(company, 0)
    has_sbir = company in sbir_companies
    has_fda = company in fda_companies
    has_nrc = company in nrc_companies

    if contracts >= 10 or value >= 1e9:
        score = 9
    elif contracts >= 5 or value >= 100e6:
        score = 7.5
    elif contracts >= 2 or value >= 10e6:
        score = 6
    elif contracts >= 1:
        score = 4.5
    else:
        score = 2

    if has_sbir:
        score = max(score, 4)
        score += 0.5
    if has_fda:
        score += 0.5
    if has_nrc:
        score += 0.5

    return clamp(score)


def generate_note(company, scores):
    """Generate an auto-summary note based on strongest dimensions."""
    dims = [
        ("techMoat", "Strong technology moat"),
        ("momentum", "High momentum"),
        ("teamPedigree", "Notable team pedigree"),
        ("marketGravity", "Large addressable market"),
        ("capitalEfficiency", "Capital efficient"),
        ("govTraction", "Strong government traction"),
    ]
    # Sort by score descending
    sorted_dims = sorted(dims, key=lambda d: scores.get(d[0], 0), reverse=True)
    top = [d[1] for d in sorted_dims[:2] if scores.get(d[0], 0) >= 6]
    if not top:
        top = [sorted_dims[0][1]]
    return "; ".join(top) + f". Composite: {scores['composite']:.0f}/100."


def main():
    print("=" * 60)
    print("INNOVATOR SCORES CALCULATOR")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Load all company names and metadata
    companies = get_company_names()
    sectors = get_company_sectors()
    stages = get_company_stages()
    print(f"Companies found: {len(companies)}")

    # 2. Load curated scores (preserve these)
    curated = get_curated_scores()
    print(f"Curated scores (preserved): {len(curated)}")

    # 3. Load data sources
    patent_data = load_js_array("patent_intel_auto.js", "PATENT_INTEL_AUTO")
    patent_counts = {}
    for p in patent_data:
        if isinstance(p, dict) and "company" in p:
            patent_counts[p["company"]] = p.get("patentCount", p.get("recentPatents", 0))

    arxiv_data = load_json("arxiv_papers_filtered.json")
    if not arxiv_data:
        arxiv_data = load_json("arxiv_papers_aggregated.json")
    arxiv_counts = count_by_company(arxiv_data, "matchedCompany")

    github_data = load_js_array("github_releases_auto.js", "GITHUB_RELEASES")
    github_counts = count_by_company(github_data, "company")

    news_data = load_json("news_raw.json")
    news_counts = count_by_company(news_data, "matchedCompany")

    job_counts = count_jobs_by_company("jobs_auto.js")

    stock_changes = get_stock_changes()

    deal_data = load_json("deals_auto.json")
    deal_counts = count_by_company(deal_data, "company")

    # Sector momentum
    sector_momentum_data = load_json("sector_momentum_auto.json")
    sector_momentum = {}
    for sm in sector_momentum_data:
        if isinstance(sm, dict) and "sector" in sm:
            sector_momentum[sm["sector"]] = sm.get("momentum", 50)

    # Founder connections
    founder_conn_counts = defaultdict(int)
    with open(DATA_JS_PATH) as f:
        content = f.read()
    # Count FOUNDER_CONNECTIONS entries per company
    for match in re.finditer(r'"([^"]+)":\s*\{[^}]*?connections:\s*\[', content):
        founder_conn_counts[match.group(1)] = len(re.findall(r'"[^"]+"', content[match.start():match.start()+500]))

    # Mafia companies
    mafia_companies = set()
    for match in re.finditer(r'company:\s*"([^"]+)"', content[content.find("FOUNDER_MAFIAS"):content.find("FOUNDER_MAFIAS")+5000] if "FOUNDER_MAFIAS" in content else ""):
        mafia_companies.add(match.group(1))

    # Gov contracts
    gov_data = load_js_array("gov_contracts_auto.js", "GOV_CONTRACTS_AUTO")
    gov_counts = count_by_company(gov_data, "company")
    gov_values = defaultdict(float)
    for g in gov_data:
        if isinstance(g, dict) and "company" in g:
            val = g.get("totalObligations", g.get("amount", 0))
            if isinstance(val, (int, float)):
                gov_values[g["company"]] += val

    # SBIR companies
    sbir_data = load_js_array("sbir_topics_auto.js", "SBIR_TOPICS")
    sbir_companies = set()
    for s in sbir_data:
        if isinstance(s, dict):
            for c in s.get("matchedCompanies", []):
                sbir_companies.add(c)

    # FDA companies
    fda_data = load_js_array("fda_actions_auto.js", "FDA_ACTIONS")
    fda_companies = {f.get("company", "") for f in fda_data if isinstance(f, dict)}

    # NRC companies
    nrc_data = load_js_array("nrc_licensing_auto.js", "NRC_LICENSING")
    nrc_companies = {n.get("company", "") for n in nrc_data if isinstance(n, dict)}

    # Total raised / revenue
    funding_data = load_json("funding_tracker_auto.json")
    total_raised_map = {}
    for f_item in funding_data:
        if isinstance(f_item, dict) and "company" in f_item:
            raw = f_item.get("totalRaisedRaw", 0)
            if isinstance(raw, (int, float)):
                total_raised_map[f_item["company"]] = raw * 1e6  # stored in millions

    revenue_data = load_json("revenue_intel_auto.json")
    revenue_map = {}
    for r in revenue_data:
        if isinstance(r, dict) and "company" in r:
            rev = r.get("revenueRaw", r.get("revenue", 0))
            if isinstance(rev, (int, float)):
                revenue_map[r["company"]] = rev

    print(f"\nData sources loaded:")
    print(f"  Patents: {len(patent_counts)} companies")
    print(f"  arXiv papers: {len(arxiv_counts)} companies")
    print(f"  GitHub releases: {len(github_counts)} companies")
    print(f"  News mentions: {len(news_counts)} companies")
    print(f"  Job listings: {len(job_counts)} companies")
    print(f"  Stock prices: {len(stock_changes)} companies")
    print(f"  Deal flow: {len(deal_counts)} companies")
    print(f"  Gov contracts: {len(gov_counts)} companies")
    print(f"  SBIR: {len(sbir_companies)} companies")
    print(f"  FDA actions: {len(fda_companies)} companies")
    print(f"  NRC licensing: {len(nrc_companies)} companies")
    print(f"  Funding tracker: {len(total_raised_map)} companies")
    print(f"  Revenue intel: {len(revenue_map)} companies")

    # 4. Calculate scores for all companies
    results = []
    for company in companies:
        # Use curated score if available
        if company in curated:
            results.append(curated[company])
            continue

        sector = sectors.get(company, "")
        stage = stages.get(company, "")

        tech_moat = calc_tech_moat(company, patent_counts, arxiv_counts, github_counts)
        momentum = calc_momentum(company, news_counts, job_counts, stock_changes, deal_counts)
        team_pedigree = calc_team_pedigree(company, founder_conn_counts, mafia_companies)
        market_gravity = calc_market_gravity(company, sector, sector_momentum)
        capital_eff = calc_capital_efficiency(company, stage, total_raised_map, revenue_map)
        gov_traction = calc_gov_traction(company, gov_counts, gov_values, sbir_companies, fda_companies, nrc_companies)

        # Composite (matches app.js formula)
        composite = (tech_moat * 2.5 + momentum * 2.5 + team_pedigree * 1.5 +
                     market_gravity * 1.5 + capital_eff * 1.0 + gov_traction * 1.0)

        # Tier
        if composite >= 90:
            tier = "elite"
        elif composite >= 75:
            tier = "strong"
        elif composite >= 60:
            tier = "promising"
        else:
            tier = "early"

        entry = {
            "company": company,
            "techMoat": tech_moat,
            "momentum": momentum,
            "teamPedigree": team_pedigree,
            "marketGravity": market_gravity,
            "capitalEfficiency": capital_eff,
            "govTraction": gov_traction,
            "composite": round(composite, 1),
            "tier": tier,
        }
        entry["note"] = generate_note(company, entry)
        results.append(entry)

    # Sort by composite descending
    results.sort(key=lambda x: x.get("composite", 0), reverse=True)

    # 5. Save output
    output_path = DATA_DIR / "innovator_scores_auto.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    # Stats
    curated_count = sum(1 for r in results if r["company"] in curated)
    auto_count = len(results) - curated_count
    tiers = defaultdict(int)
    for r in results:
        tiers[r["tier"]] += 1

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {len(results)} companies scored")
    print(f"  Curated (preserved): {curated_count}")
    print(f"  Auto-generated: {auto_count}")
    print(f"  Elite: {tiers['elite']}, Strong: {tiers['strong']}, "
          f"Promising: {tiers['promising']}, Early: {tiers['early']}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
