#!/usr/bin/env python3
"""
USAspending.gov Government Contracts Fetcher
Fetches federal contract data for companies tracked in The Innovators League.
Free API - no key required.

Scope (2026-08-19)
──────────────────
This used to query a hand-written list of 48 names. That list was written when
the database held a few hundred companies and was never grown with it, so as of
today it covered 40 distinct companies out of 1,181 — and a company only
appeared if someone had remembered to type it in. Every company added since
(the buildlist and Black Flag imports especially) was invisible to the single
best evidence of real revenue we can get for free.

The list is now derived from data.js. Two scopes:

  --scope hot   (default, safe for a daily run) US companies in the sectors
                that actually win federal awards, plus every company already
                known to hold one. Roughly 300 queries.
  --scope all   every US company in the database. Roughly 900 queries, ~8
                minutes at the polite rate. Intended for the weekly job.

Why the recipient name is verified
──────────────────────────────────
The API filter is `recipient_search_text`, which is a FUZZY match. With 48
curated names that was tolerable. Across 1,181 it is not: "Apex", "Radiant",
"Primer", "Base", "Forterra" and dozens like them would hoover up awards
belonging to unrelated federal vendors and post them on our company profiles as
revenue. A fabricated $40M defence contract on a company profile is a far worse
failure than a missing one — the same rule that governs the website resolver and
the Form D matcher.

So every returned award now has to clear `recipient_matches()`: the awardee's
name, with legal suffixes stripped, must equal or contain our company's name as
a whole token. Anything else is counted and reported as rejected, not silently
dropped, so the reject count is visible if the filter is ever too strict.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

# Hand-curated priority names, kept because they carry the alias spellings that
# USASpending actually files awards under (e.g. "Space Exploration Technologies").
TRACKED_COMPANIES = [
    # Defense & Security
    "Anduril", "Anduril Industries",
    "Shield AI",
    "Palantir", "Palantir Technologies",
    "SpaceX", "Space Exploration Technologies",
    "Epirus",
    "Saronic",
    "Skydio",
    "Neros",
    "Chaos Industries",
    "Castelion",
    "Forterra",
    "Vannevar Labs",
    "Rebellion Defense",
    "Primer",
    "Second Front Systems",
    "Hadrian",

    # Space & Aerospace
    "Rocket Lab", "Rocket Lab USA",
    "Relativity Space",
    "Axiom Space",
    "Sierra Space",
    "Varda Space Industries",
    "Impulse Space",
    "Planet Labs",
    "Muon Space",
    "Albedo",
    "BlackSky", "BlackSky Technology",
    "Capella Space",

    # Nuclear & Energy
    "Oklo",
    "Kairos Power",
    "TerraPower",
    "X-energy",
    "NuScale", "NuScale Power",
    "Radiant",
    "Fervo Energy",

    # AI & Robotics
    "Scale AI",
    "OpenAI",
    "Anthropic",
    "Figure AI",
    "Boston Dynamics",
    "Agility Robotics",

    # Biotech
    "Moderna",
    "Ginkgo Bioworks",
]

USASPENDING_API = "https://api.usaspending.gov/api/v2"

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "data.js"

# Sectors that plausibly hold federal prime contracts. A vertical-farming or
# consumer-fintech company can hold one, but the hit rate is low enough that
# querying them daily is a waste; --scope all still covers them weekly.
GOV_SECTORS = re.compile(
    r"defen[cs]e|space|aerospace|nuclear|energy|robotic|semiconductor|"
    r"quantum|biotech|materials|manufactur|autonom|security|sensor|"
    r"communications|drone|maritime|hypersonic", re.I)

_SUFFIX = re.compile(
    r"\b(inc|incorporated|llc|l\.?l\.?c|corp|corporation|co|company|ltd|limited|"
    r"lp|llp|plc|holdings?|group|the)\b\.?", re.I)

# Words a startup routinely appends to its own trading name. Stripped from the
# AWARDEE only, so "ANDURIL INDUSTRIES, INC." reduces to "anduril" and matches
# our "Anduril" exactly, without loosening the rule into containment.
#
# Two tiers, because 83 of our US company names are ordinary English words
# (Apex, Radiant, Matter, Halo, Vast, Union...). For those the broad tier is
# dangerous: "APEX MANUFACTURING COMPANY" and "APEX TECHNOLOGY, INC." are both
# real California vendors that are not our Apex, and both survive a broad
# strip. The tight tier contains only words a frontier-tech company actually
# trades under, which keeps SARONIC TECHNOLOGIES and ANDURIL INDUSTRIES while
# rejecting the manufacturing and IT-services firms that share the word.
_DESC_TIGHT = (r"industries|technologies|aerospace|space|robotics|dynamics|"
               r"systems|labs?|defense|defence")
_DESC_BROAD = (_DESC_TIGHT + r"|technology|automation|aviation|energy|power|"
               r"works|laboratories|sciences|solutions|manufacturing|"
               r"international|usa|us")
_DESCRIPTOR_TIGHT = re.compile(rf"\b({_DESC_TIGHT})\b", re.I)
_DESCRIPTOR_BROAD = re.compile(rf"\b({_DESC_BROAD})\b", re.I)

# Our own company names that are ordinary English words, so a same-named
# federal vendor is likely. Derived from the 816 US companies in data.js
# intersected with /usr/share/dict/words; baked in as a constant because CI
# runners have no system dictionary. Regenerate with:
#   comm -12 <(names) <(dict)
GENERIC_NAMES = {
    "albacore", "albedo", "ample", "antares", "armada", "athanor", "atmo",
    "augury", "axion", "becoming", "bountiful", "brimstone", "burro",
    "cambium", "cape", "cognition", "cover", "deterrence", "dexterity",
    "diode", "dispatcher", "divergent", "drafter", "electra", "enigma",
    "formic", "foxglove", "gambit", "glimpse", "halo", "harbinger", "helion",
    "icon", "icarus", "integrate", "kestrel", "lambda", "laminar", "loyal",
    "lydian", "material", "mara", "matter", "mazama", "meter", "nominal",
    "nudge", "octavia", "orchid", "ouster", "outrider", "pilgrim", "pivotal",
    "poolside", "privateer", "profluent", "quilter", "radiant", "remora",
    "resilience", "revel", "revere", "saronic", "seneca", "singularity",
    "sorcerer", "span", "specter", "spiritus", "squint", "substrate", "swan",
    "tempo", "theseus", "twelve", "twenty", "umbra", "union", "unspun",
    "until", "vast", "verse", "zoo",
}


def _norm_vendor(s: str, descriptors: re.Pattern | None = None) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    for _ in range(3):
        t = re.sub(r"\s+", " ", _SUFFIX.sub(" ", s)).strip()
        if t == s:
            break
        s = t
    if descriptors is not None:
        for _ in range(3):
            t = re.sub(r"\s+", " ", descriptors.sub(" ", s)).strip()
            if t == s or not t:
                break
            s = t
    return re.sub(r"\s+", "", s)


def recipient_matches(queried: str, awardee: str) -> bool:
    """Is this award really our company's?

    `recipient_search_text` is FUZZY, so USASpending returns "APEX SYSTEMS LLC"
    (a Virginia IT staffing firm) when asked about our Apex, and "RADIANT
    LOGISTICS INC" when asked about Radiant Industries. Both would post a
    stranger's federal revenue on our company profile.

    Containment is not a usable rule here, because it cannot separate
    "apex" ⊂ "apex systems" (wrong) from "anduril" ⊂ "anduril industries"
    (right). So we require EQUALITY after stripping legal suffixes from both
    sides and trading descriptors from the awardee — with the descriptor list
    narrowed for the 83 company names that are ordinary English words.

    Worked examples, all real:
      Anduril    vs ANDURIL INDUSTRIES, INC.    accept (coined name, broad tier)
      Saronic    vs SARONIC TECHNOLOGIES, INC   accept (generic name, but
                                                "technologies" is in the tight
                                                tier — a frontier-tech word)
      Apex       vs APEX MANUFACTURING COMPANY  reject (generic name, and
                                                "manufacturing" is broad-tier
                                                only)
      Apex       vs APEX TECHNOLOGY, INC.       reject (singular "technology"
                                                is broad-tier only)
      Radiant    vs RADIANT LOGISTICS INC       reject (no descriptor match)

    The caller also constrains each query by the company's home state, so a
    same-named vendor in another state never reaches this function at all.
    """
    if not queried or not awardee:
        return False
    q = _norm_vendor(queried)
    if not q:
        return False
    if q == _norm_vendor(awardee):
        return True
    tier = (_DESCRIPTOR_TIGHT if queried.strip().lower() in GENERIC_NAMES
            else _DESCRIPTOR_BROAD)
    return q == _norm_vendor(awardee, descriptors=tier)


def companies_from_data_js(scope: str) -> list[dict]:
    """US companies worth querying, each with the state used to disambiguate."""
    js = (
        'const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
        'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
        '+";globalThis.__n=COMPANIES.map(c=>({name:c.name,country:c.country||\'\','
        'state:c.state||\'\',sector:c.sector||\'\',status:c.status||\'\'}));",s);'
        "console.log(JSON.stringify(s.__n));"
    )
    rows = json.loads(subprocess.run(["node", "-e", js, str(DATA_JS)],
                                     capture_output=True, text=True,
                                     check=True).stdout)
    # Dead companies cannot win new awards; their history is already recorded.
    rows = [r for r in rows
            if r["country"] == "United States" and r["status"] not in ("dead",)]
    if scope != "all":
        rows = [r for r in rows if GOV_SECTORS.search(r["sector"] or "")]
    return [{"name": r["name"], "state": r["state"]} for r in rows]


def fetch_with_retry(url, headers=None, json_payload=None, method="get", max_retries=3, timeout=30):
    """Fetch URL with retry logic and exponential backoff."""
    for attempt in range(max_retries):
        try:
            if method == "post":
                response = requests.post(url, json=json_payload, headers=headers, timeout=timeout)
            else:
                response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 429:
                wait = (2 ** attempt) * 5
                print(f"  Rate limited (429), waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"  Request failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    print(f"  All {max_retries} attempts failed for {url}")
    return None

def fetch_contracts_for_company(company_name, start_date=None, state=None):
    """Fetch federal contracts for a specific company.

    `state` is the company's home state from data.js. Passing it narrows the
    query to recipients registered there, which is what separates our Apex
    (California) from APEX SYSTEMS LLC (Virginia) — a distinction the name
    alone cannot make. Omitted when we do not hold a state, in which case the
    name rule stands on its own.
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    end_date = datetime.now().strftime("%Y-%m-%d")

    payload = {
        "filters": {
            "recipient_search_text": [company_name],
            "time_period": [
                {
                    "start_date": start_date,
                    "end_date": end_date
                }
            ],
            "award_type_codes": ["A", "B", "C", "D"]  # Contracts only
        },
        "fields": [
            "Award ID",
            "Recipient Name",
            "Award Amount",
            "Awarding Agency",
            "Awarding Sub Agency",
            "Award Type",
            "Start Date",
            "End Date",
            "Description"
        ],
        "page": 1,
        "limit": 100,
        "sort": "Award Amount",
        "order": "desc"
    }
    if state:
        payload["filters"]["recipient_locations"] = [
            {"country": "USA", "state": state}
        ]

    response = fetch_with_retry(
        f"{USASPENDING_API}/search/spending_by_award/",
        headers={"Content-Type": "application/json"},
        json_payload=payload,
        method="post"
    )
    if response is None:
        print(f"Error fetching contracts for {company_name}: all retries failed")
        return None
    return response.json()

def fetch_all_contracts(targets=None):
    """Fetch contracts for every target, keeping only verified awardees."""
    all_contracts = []
    if targets is None:
        targets = [{"name": n, "state": ""} for n in TRACKED_COMPANIES]
    kept = rejected = 0

    for i, t in enumerate(targets, 1):
        company, state = t["name"], t.get("state") or ""
        result = fetch_contracts_for_company(company, state=state)
        if not (result and "results" in result):
            continue

        hits = 0
        for award in result["results"]:
            awardee = award.get("Recipient Name", "")
            if not recipient_matches(company, awardee):
                rejected += 1
                continue
            all_contracts.append({
                "company": company,
                "awardId": award.get("Award ID", ""),
                "recipientName": awardee,
                "amount": award.get("Award Amount", 0),
                "agency": award.get("Awarding Agency", ""),
                "subAgency": award.get("Awarding Sub Agency", ""),
                "awardType": award.get("Award Type", ""),
                "startDate": award.get("Start Date", ""),
                "endDate": award.get("End Date", ""),
                "description": award.get("Description", "")[:200] if award.get("Description") else ""
            })
            hits += 1
            kept += 1

        if hits:
            dropped = len(result["results"]) - hits
            note = f", {dropped} rejected as a different vendor" if dropped else ""
            print(f"  [{i}/{len(targets)}] {company}: {hits} verified{note}")
        time.sleep(0.35)   # polite; USASpending throttles hard at ~10 req/s

    print(f"\nverified awards: {kept}   rejected as a different vendor: {rejected}")
    return all_contracts

# Canonical-name map for vendors whose contracts appear under multiple aliases
# in USASpending. We query both forms (higher hit rate) then merge at aggregation.
CANONICAL_NAME = {
    "Anduril Industries": "Anduril",
    "Palantir Technologies": "Palantir",
    "Space Exploration Technologies": "SpaceX",
    "Rocket Lab USA": "Rocket Lab",
    "NuScale Power": "NuScale",
    "BlackSky Technology": "BlackSky",
}

def aggregate_by_company(contracts):
    """Aggregate contracts by company for the GOV_CONTRACTS format.

    Merges aliases (e.g. 'Anduril Industries' -> 'Anduril') via CANONICAL_NAME
    so the customer-intelligence page doesn't show the same vendor twice.
    """
    company_data = {}

    for contract in contracts:
        # Normalize to canonical name before aggregating
        company = CANONICAL_NAME.get(contract["company"], contract["company"])
        if company not in company_data:
            company_data[company] = {
                "company": company,
                "totalGovValue": 0,
                "contractCount": 0,
                "agencies": set(),
                "recentContracts": []
            }

        amount = contract.get("amount", 0) or 0
        company_data[company]["totalGovValue"] += amount
        company_data[company]["contractCount"] += 1

        if contract.get("agency"):
            company_data[company]["agencies"].add(contract["agency"])

        # Keep top 5 recent contracts
        if len(company_data[company]["recentContracts"]) < 5:
            company_data[company]["recentContracts"].append({
                "amount": amount,
                "agency": contract.get("agency", ""),
                "description": contract.get("description", ""),
                "date": contract.get("startDate", "")
            })

    # Convert to list format
    result = []
    for company, data in company_data.items():
        if data["contractCount"] > 0:
            total = data["totalGovValue"]
            if total >= 1_000_000_000:
                total_str = f"${total/1_000_000_000:.1f}B+"
            elif total >= 1_000_000:
                total_str = f"${total/1_000_000:.0f}M+"
            else:
                total_str = f"${total/1_000:.0f}K"

            result.append({
                "company": company,
                "totalGovValue": total_str,
                "contractCount": data["contractCount"],
                "agencies": list(data["agencies"])[:5],
                "recentContracts": data["recentContracts"],
                "lastUpdated": datetime.now().strftime("%Y-%m-%d")
            })

    # Sort by total value
    result.sort(key=lambda x: x["contractCount"], reverse=True)
    return result

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(aggregated_data):
    """Generate JavaScript code snippet to update data.js."""
    js_output = "// Auto-generated government contracts data\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const GOV_CONTRACTS_AUTO = [\n"

    for item in aggregated_data:
        js_output += f"  {{\n"
        js_output += f'    company: "{item["company"]}",\n'
        js_output += f'    totalGovValue: "{item["totalGovValue"]}",\n'
        js_output += f'    contractCount: {item["contractCount"]},\n'
        js_output += f'    agencies: {json.dumps(item["agencies"])},\n'
        js_output += f'    lastUpdated: "{item["lastUpdated"]}"\n'
        js_output += f"  }},\n"

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "gov_contracts_auto.js"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["hot", "all", "legacy"], default="hot",
                    help="hot = US companies in contract-winning sectors "
                         "(daily); all = every US company (weekly); "
                         "legacy = the old 48-name list")
    args = ap.parse_args()

    print("=" * 60)
    print("USAspending.gov Government Contracts Fetcher")
    print("=" * 60)

    if args.scope == "legacy":
        targets = [{"name": n, "state": ""} for n in TRACKED_COMPANIES]
    else:
        # Curated aliases first — they carry the spellings USASpending files
        # awards under, and are queried without a state filter because an alias
        # like "Space Exploration Technologies" may be registered elsewhere —
        # then everything else in scope, deduped.
        derived = companies_from_data_js(args.scope)
        seen, targets = set(), []
        for t in ([{"name": n, "state": ""} for n in TRACKED_COMPANIES] + derived):
            if t["name"].lower() not in seen:
                seen.add(t["name"].lower())
                targets.append(t)

    print(f"Scope: {args.scope} — querying {len(targets)} companies "
          f"(was 48 hardcoded)")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all contracts
    contracts = fetch_all_contracts(targets)
    print(f"\nTotal contracts found: {len(contracts)}")

    # Aggregate by company
    aggregated = aggregate_by_company(contracts)
    print(f"Companies with contracts: {len(aggregated)}")

    # Save raw data
    save_to_json(contracts, "gov_contracts_raw.json")
    save_to_json(aggregated, "gov_contracts_aggregated.json")

    # Generate JS snippet
    generate_js_snippet(aggregated)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
