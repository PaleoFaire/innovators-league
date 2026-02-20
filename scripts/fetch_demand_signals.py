#!/usr/bin/env python3
"""
Demand Signal Radar — Unified Government Opportunity Fetcher & Matcher
For The Innovators League

Fetches government opportunities from:
  1. SBIR.gov API (free, no key)
  2. Grants.gov API (free, no key for search)
  3. SAM.gov API (optional, needs SAM_API_KEY env var)

Then algorithmically matches each opportunity against all 513 companies
using tags, thesisCluster, techApproach, and description overlap.

Computes a per-company "Government Pull Score" (0-100).

Falls back to curated seed data when APIs are unavailable.

Output:
  data/demand_signals_auto.js  — JS file with GOV_DEMAND_SIGNALS_AUTO, GOV_PULL_SCORES_AUTO, DEMAND_SIGNALS_STATS
  data/demand_signals_auto.json — Raw JSON backup
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("Warning: requests module not available. Using seed data only.")
    requests = None

# ─── PATHS ───
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
DATA_JS_PATH = ROOT_DIR / "data.js"

# ─── STOP WORDS for text matching ───
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need", "must",
    "that", "this", "these", "those", "it", "its", "as", "if", "not",
    "no", "nor", "so", "too", "very", "just", "about", "above", "after",
    "all", "also", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "than", "their", "them", "then", "there", "through",
    "into", "over", "under", "up", "out", "new", "first", "based", "using",
    "include", "including", "between", "during", "within", "without",
    "across", "along", "among", "around", "before", "beyond", "down",
    "further", "how", "what", "when", "where", "which", "while", "who",
    "whom", "why", "able", "well", "high", "low", "key", "next", "last",
    "per", "via", "use", "used", "development", "technology", "technologies",
    "system", "systems", "approach", "approaches", "program", "programs",
    "research", "develop", "developing", "developed", "enable", "enabling",
    "support", "supporting", "provide", "providing", "design", "designed",
}

# ─── THESIS CLUSTER → KEYWORDS mapping ───
# Maps each of the 76 thesis clusters to searchable keywords for matching
THESIS_CLUSTER_KEYWORDS = {
    # Defense / Autonomy
    "autonomy-drone-military": ["drone", "UAS", "unmanned aerial", "autonomous", "swarm", "military drone", "combat UAV", "loitering munition"],
    "autonomy-counter-drone": ["counter-UAS", "counter-drone", "C-UAS", "anti-drone", "directed energy", "electronic warfare", "CUAS"],
    "autonomy-maritime": ["autonomous vessel", "unmanned surface", "USV", "autonomous boat", "maritime autonomy", "undersea", "AUV", "naval"],
    "autonomy-ground": ["ground robot", "autonomous vehicle", "UGV", "unmanned ground", "military robot", "EOD"],
    "defense-software-platform": ["defense software", "C4ISR", "mission software", "command control", "battle management", "JADC2", "data fusion"],
    "defense-ew-rf-cyber": ["electronic warfare", "signals intelligence", "SIGINT", "radio frequency", "spectrum", "EW", "cyber warfare"],
    "defense-space-awareness": ["space domain awareness", "space situational", "SSA", "SDA", "orbital debris", "space surveillance"],
    "defense-munitions": ["precision munition", "guided weapon", "missile", "warhead", "cruise missile", "hypersonic weapon"],
    "defense-armor-protection": ["body armor", "protection system", "armor", "survivability", "ballistic"],
    "defense-biometric": ["biometric", "identity", "facial recognition", "person identification"],
    "defense-simulation": ["simulation", "training", "synthetic", "digital twin", "wargaming"],
    "defense-logistics": ["logistics", "supply chain", "sustainment", "MRO", "maintenance"],
    "defense-comms-mesh": ["mesh network", "tactical communications", "MANET", "tactical radio", "military comms"],
    "defense-intel-osint": ["intelligence", "OSINT", "open source intelligence", "geospatial", "GEOINT"],
    "ai-defense-intelligence": ["AI intelligence", "machine learning defense", "predictive intelligence", "AI analytics"],

    # Space
    "space-launch-reusable": ["launch vehicle", "rocket", "reusable launch", "orbital launch", "space launch"],
    "space-launch-small": ["small launch", "smallsat", "rideshare", "micro launch"],
    "space-satellite-constellation": ["satellite constellation", "LEO constellation", "satellite communications", "SATCOM"],
    "space-satellite-earth-obs": ["earth observation", "remote sensing", "satellite imaging", "SAR", "geospatial"],
    "space-station-habitat": ["space station", "orbital habitat", "microgravity", "space tourism"],
    "space-manufacturing": ["in-space manufacturing", "space manufacturing", "microgravity manufacturing", "orbital factory"],
    "space-debris-servicing": ["space debris", "orbital servicing", "debris removal", "satellite servicing"],
    "space-propulsion-advanced": ["electric propulsion", "ion thruster", "hall thruster", "space propulsion", "orbit transfer"],
    "space-nuclear-propulsion": ["nuclear thermal propulsion", "NTP", "nuclear electric", "space nuclear"],
    "space-lunar": ["lunar", "moon", "cislunar", "Artemis", "lunar landing"],
    "space-ground-segment": ["ground station", "ground segment", "satellite ground", "antenna network"],
    "space-optical-comms": ["laser communications", "optical comms", "free space optical", "lasercom"],

    # Nuclear / Fission
    "nuclear-smr": ["small modular reactor", "SMR", "nuclear reactor", "nuclear power plant"],
    "nuclear-smr-molten-salt": ["molten salt reactor", "MSR", "fluoride salt", "LFTR"],
    "nuclear-microreactor": ["microreactor", "portable reactor", "mobile nuclear", "transportable reactor"],
    "nuclear-htgr": ["high temperature gas", "HTGR", "TRISO", "pebble bed", "gas cooled reactor"],
    "nuclear-fuel": ["nuclear fuel", "HALEU", "uranium enrichment", "fuel fabrication", "fuel cycle"],
    "nuclear-services": ["nuclear services", "decommissioning", "nuclear waste", "spent fuel"],

    # Fusion
    "fusion-magnetic-confinement": ["fusion", "tokamak", "plasma confinement", "magnetic fusion", "stellarator"],
    "fusion-inertial": ["inertial fusion", "laser fusion", "inertial confinement", "ICF", "NIF"],
    "fusion-alternative": ["fusion energy", "field-reversed", "FRC", "aneutronic fusion", "compact fusion"],

    # AI
    "ai-foundation-models": ["large language model", "LLM", "foundation model", "generative AI", "artificial intelligence"],
    "ai-enterprise": ["enterprise AI", "AI platform", "machine learning operations", "MLOps"],
    "ai-data-labeling": ["data labeling", "training data", "data annotation", "AI data"],
    "ai-safety-alignment": ["AI safety", "alignment", "responsible AI", "AI governance"],
    "ai-robotics": ["robot AI", "embodied AI", "robot learning", "manipulation AI"],
    "ai-drug-discovery": ["AI drug discovery", "computational biology", "molecular design", "drug design AI"],
    "ai-vertical-legal": ["legal AI", "legal tech", "contract AI"],
    "ai-vertical-finance": ["financial AI", "fintech AI", "algorithmic trading"],

    # Quantum
    "quantum-trapped-ion": ["trapped ion", "ion trap", "quantum computing", "qubit", "quantum processor"],
    "quantum-superconducting": ["superconducting qubit", "quantum processor", "quantum computing"],
    "quantum-photonic": ["photonic quantum", "quantum optics", "photon qubit", "optical quantum"],
    "quantum-neutral-atom": ["neutral atom", "atom array", "Rydberg", "quantum simulator"],
    "quantum-networking": ["quantum network", "quantum internet", "quantum key distribution", "QKD", "quantum communication"],
    "quantum-sensing": ["quantum sensor", "quantum magnetometer", "quantum navigation", "atom interferometer"],
    "quantum-software": ["quantum software", "quantum algorithm", "quantum compiler", "quantum SDK"],
    "quantum-diamond-nv": ["diamond NV center", "nitrogen vacancy", "quantum diamond"],

    # Biotech
    "biotech-gene-editing": ["gene editing", "CRISPR", "gene therapy", "genetic engineering", "genome editing"],
    "biotech-synthetic-biology": ["synthetic biology", "biomanufacturing", "cell engineering", "metabolic engineering"],
    "biotech-longevity": ["longevity", "anti-aging", "senolytic", "cellular reprogramming", "lifespan"],
    "biotech-diagnostics": ["diagnostics", "biosensor", "point of care", "molecular diagnostics"],
    "biotech-protein-engineering": ["protein engineering", "protein design", "enzyme engineering", "directed evolution"],
    "biotech-neuroscience": ["brain-computer interface", "BCI", "neural", "neuroscience", "neurotech"],

    # Robotics
    "robotics-humanoid": ["humanoid robot", "bipedal", "general purpose robot", "android"],
    "robotics-industrial": ["industrial robot", "manufacturing robot", "warehouse robot", "cobot"],
    "robotics-surgical": ["surgical robot", "medical robot", "robotic surgery"],
    "robotics-agricultural": ["agricultural robot", "farming robot", "precision agriculture robot"],
    "robotics-inspection": ["inspection robot", "infrastructure inspection", "pipeline robot"],
    "robotics-delivery": ["delivery robot", "autonomous delivery", "last mile robot"],
    "robotics-construction": ["construction robot", "building robot", "3D printing construction"],

    # Chips / Semiconductors
    "chips-ai-accelerator": ["AI chip", "AI accelerator", "neural processor", "inference chip", "GPU", "TPU"],
    "chips-photonics": ["silicon photonics", "photonic chip", "optical computing", "photonic integrated"],
    "chips-manufacturing": ["semiconductor manufacturing", "chip fabrication", "foundry", "lithography", "EUV"],
    "chips-fpga-custom": ["FPGA", "custom silicon", "ASIC", "reconfigurable"],

    # Energy
    "energy-geothermal": ["geothermal", "enhanced geothermal", "EGS", "hot dry rock"],
    "energy-storage": ["energy storage", "battery", "grid storage", "flow battery", "iron-air"],
    "energy-hydrogen": ["hydrogen", "green hydrogen", "electrolysis", "fuel cell", "H2"],
    "energy-solar-advanced": ["perovskite", "tandem solar", "advanced solar", "space solar"],
    "energy-carbon-capture": ["carbon capture", "DAC", "direct air capture", "CCS", "CCUS", "carbon removal"],

    # Transport
    "transport-evtol": ["eVTOL", "air taxi", "urban air mobility", "electric vertical", "flying car"],
    "transport-supersonic": ["supersonic", "Mach", "faster than sound", "boom supersonic"],
    "transport-hypersonic": ["hypersonic", "scramjet", "Mach 5", "hypersonic vehicle", "thermal protection"],
    "transport-tunneling": ["tunneling", "boring", "underground", "tunnel boring machine"],
    "transport-ground-effect": ["ground effect", "ekranoplan", "wing-in-ground", "sea glider"],
    "transport-autonomous-marine": ["autonomous marine", "unmanned boat", "autonomous ship", "maritime autonomous"],

    # Other
    "housing-factory-built": ["modular housing", "factory built", "prefab", "modular construction", "3D printed house"],
    "ocean-exploration": ["ocean", "deep sea", "subsea", "marine exploration", "underwater"],
    "materials-advanced": ["advanced materials", "metamaterial", "composite", "nanomaterial", "additive manufacturing"],
    "scent-tech": ["scent", "olfactory", "digital scent", "fragrance tech"],
    "climate-monitoring": ["climate monitoring", "methane detection", "emissions monitoring", "environmental monitoring"],
    "infrastructure-grid": ["power grid", "grid modernization", "smart grid", "energy infrastructure"],
}

# ─── COMPANY NAME ALIASES (gov records often use different names) ───
COMPANY_ALIASES = {
    "Space Exploration Technologies": "SpaceX",
    "Space Exploration Technologies Corp": "SpaceX",
    "Rocket Lab USA": "Rocket Lab",
    "Palantir Technologies": "Palantir",
    "Scale AI Inc": "Scale AI",
    "Joby Aviation Inc": "Joby Aviation",
    "Archer Aviation Inc": "Archer Aviation",
    "Commonwealth Fusion Systems": "Commonwealth Fusion Systems",
    "CFS": "Commonwealth Fusion Systems",
    "Anduril Industries Inc": "Anduril Industries",
    "Shield AI Inc": "Shield AI",
    "Relativity Space Inc": "Relativity Space",
    "Figure AI Inc": "Figure AI",
    "Boston Dynamics Inc": "Boston Dynamics",
}


# ═══════════════════════════════════════════════════════════
#  COMPANY DATA EXTRACTION FROM data.js
# ═══════════════════════════════════════════════════════════

def extract_companies_for_matching():
    """Extract company matching data from data.js using regex."""
    if not DATA_JS_PATH.exists():
        print(f"Warning: {DATA_JS_PATH} not found")
        return []

    content = DATA_JS_PATH.read_text(encoding="utf-8")

    # Find COMPANIES array bounds
    start_match = re.search(r'const COMPANIES\s*=\s*\[', content)
    if not start_match:
        print("Warning: Could not find COMPANIES array in data.js")
        return []

    start = start_match.end()

    # Find the matching closing bracket
    depth = 1
    pos = start
    while pos < len(content) and depth > 0:
        if content[pos] == '[':
            depth += 1
        elif content[pos] == ']':
            depth -= 1
        pos += 1

    companies_text = content[start:pos - 1]

    # Extract individual company entries
    companies = []

    # Find each company block by matching name field
    name_pattern = re.compile(r'name:\s*"([^"]+)"')
    sector_pattern = re.compile(r'sector:\s*"([^"]+)"')
    desc_pattern = re.compile(r'description:\s*"([^"]*(?:\\.[^"]*)*)"')
    tags_pattern = re.compile(r'tags:\s*\[([^\]]*)\]')
    cluster_pattern = re.compile(r'thesisCluster:\s*"([^"]+)"')
    approach_pattern = re.compile(r'techApproach:\s*"([^"]*(?:\\.[^"]*)*)"')

    # Split into company blocks (each starts with { and name:)
    blocks = re.split(r'\n\s*\{', companies_text)

    for block in blocks:
        name_m = name_pattern.search(block)
        if not name_m:
            continue

        name = name_m.group(1)
        sector = ""
        description = ""
        tags = []
        cluster = ""
        approach = ""

        sector_m = sector_pattern.search(block)
        if sector_m:
            sector = sector_m.group(1)

        desc_m = desc_pattern.search(block)
        if desc_m:
            description = desc_m.group(1).replace('\\"', '"')

        tags_m = tags_pattern.search(block)
        if tags_m:
            tags_str = tags_m.group(1)
            tags = [t.strip().strip('"').strip("'") for t in tags_str.split(',') if t.strip().strip('"').strip("'")]

        cluster_m = cluster_pattern.search(block)
        if cluster_m:
            cluster = cluster_m.group(1)

        approach_m = approach_pattern.search(block)
        if approach_m:
            approach = approach_m.group(1).replace('\\"', '"')

        companies.append({
            "name": name,
            "sector": sector,
            "description": description[:500],  # Limit for memory
            "tags": tags,
            "thesisCluster": cluster,
            "techApproach": approach,
        })

    print(f"  Extracted {len(companies)} companies from data.js")
    return companies


# ═══════════════════════════════════════════════════════════
#  RELEVANCE SCORING ENGINE
# ═══════════════════════════════════════════════════════════

def extract_keywords(text):
    """Extract meaningful keywords from text, removing stop words."""
    words = re.findall(r'[a-zA-Z]{3,}', text.lower())
    return [w for w in words if w not in STOP_WORDS]


def compute_relevance_score(signal, company):
    """
    Score 0-100 for how well a company matches a demand signal.

    Scoring:
      - Direct name match: 40 pts
      - Tag overlap: 30 pts max (10 per matching tag, capped at 3)
      - Thesis cluster alignment: 20 pts max
      - techApproach text similarity: 10 pts max
    """
    score = 0
    match_reasons = []

    signal_text = f"{signal.get('title', '')} {signal.get('description', '')} {' '.join(signal.get('techAreas', []))}".lower()
    signal_keywords = set(extract_keywords(signal_text))

    # 1. Direct name match (40 points)
    company_name_lower = company["name"].lower()
    if company_name_lower in signal_text:
        score += 40
        match_reasons.append(f"name: {company['name']}")

    # 2. Tag overlap (30 points max)
    company_tags = [t.lower() for t in company.get("tags", [])]
    tag_hits = 0
    for tag in company_tags:
        tag_words = set(tag.split())
        # Check if the tag or significant words from the tag appear in signal text
        if tag in signal_text:
            tag_hits += 1
            match_reasons.append(f"tag: {tag}")
        elif len(tag_words) > 1 and len(tag_words & signal_keywords) >= len(tag_words) * 0.6:
            tag_hits += 1
            match_reasons.append(f"tag: {tag}")

    score += min(tag_hits * 10, 30)

    # 3. Thesis cluster alignment (20 points)
    cluster = company.get("thesisCluster", "")
    if cluster:
        cluster_kws = THESIS_CLUSTER_KEYWORDS.get(cluster, [])
        cluster_hits = 0
        for kw in cluster_kws:
            if kw.lower() in signal_text:
                cluster_hits += 1
        if cluster_hits > 0:
            cluster_score = min(cluster_hits * 5, 20)
            score += cluster_score
            if cluster_score >= 10:
                match_reasons.append(f"cluster: {cluster}")

    # 4. techApproach text similarity (10 points)
    tech_approach = company.get("techApproach", "").lower()
    if tech_approach:
        approach_words = set(extract_keywords(tech_approach))
        overlap = len(approach_words & signal_keywords)
        approach_score = min(overlap * 2, 10)
        score += approach_score
        if approach_score >= 4:
            match_reasons.append("techApproach overlap")

    return min(score, 100), match_reasons[:4]  # Cap at 4 reasons


def match_companies_to_signal(signal, companies):
    """Match all companies against a single demand signal. Return top 10 with score >= 15."""
    matches = []

    for company in companies:
        score, reasons = compute_relevance_score(signal, company)
        if score >= 15:
            matches.append({
                "name": company["name"],
                "score": score,
                "matchReasons": reasons
            })

    # Sort by score descending, keep top 10
    matches.sort(key=lambda x: -x["score"])
    return matches[:10]


def compute_gov_pull_scores(signals, companies):
    """Compute Government Pull Score (0-100) for each company."""
    company_matches = {}

    for signal in signals:
        for mc in signal.get("matchedCompanies", []):
            name = mc["name"]
            if name not in company_matches:
                company_matches[name] = []
            company_matches[name].append({
                "signal": signal,
                "relevanceScore": mc["score"]
            })

    scores = {}
    for name, matches in company_matches.items():
        # 1. Signal count (0-25)
        count_score = min(len(matches) * 3, 25)

        # 2. Average relevance (0-25)
        avg_rel = sum(m["relevanceScore"] for m in matches) / len(matches)
        relevance_score = avg_rel * 0.25

        # 3. Agency diversity (0-25)
        agencies = set(m["signal"].get("agency", "") for m in matches)
        diversity_score = min(len(agencies) * 5, 25)

        # 4. Value & urgency (0-25)
        value_urgency = 0
        for m in matches:
            val = parse_value_to_number(m["signal"].get("value", ""))
            if val > 50_000_000:
                value_urgency += 5
            elif val > 10_000_000:
                value_urgency += 3
            elif val > 1_000_000:
                value_urgency += 1
        value_urgency = min(value_urgency, 25)

        total = min(round(count_score + relevance_score + diversity_score + value_urgency), 100)

        scores[name] = {
            "name": name,
            "govPullScore": total,
            "matchCount": len(matches),
            "topAgencies": sorted(agencies)[:5],
            "avgRelevance": round(avg_rel),
            "topSignals": [
                m["signal"]["title"]
                for m in sorted(matches, key=lambda x: -x["relevanceScore"])[:3]
            ]
        }

    return scores


def parse_value_to_number(val_str):
    """Parse a dollar value string to a number."""
    if not val_str or not isinstance(val_str, str):
        return 0
    # Handle ranges like "$50M-$100M" — take midpoint
    range_match = re.search(r'\$([\d.]+)\s*(B|M|K)?\s*-\s*\$([\d.]+)\s*(B|M|K)?', val_str, re.I)
    if range_match:
        lo = float(range_match.group(1)) * _unit_multiplier(range_match.group(2))
        hi = float(range_match.group(3)) * _unit_multiplier(range_match.group(4))
        return (lo + hi) / 2
    # Handle single values
    single_match = re.search(r'\$([\d.]+)\s*(B|M|K|T)?', val_str, re.I)
    if single_match:
        return float(single_match.group(1)) * _unit_multiplier(single_match.group(2))
    return 0


def _unit_multiplier(unit):
    if not unit:
        return 1
    u = unit.upper()
    if u == 'T':
        return 1e12
    if u == 'B':
        return 1e9
    if u == 'M':
        return 1e6
    if u == 'K':
        return 1e3
    return 1


# ═══════════════════════════════════════════════════════════
#  API FETCHERS
# ═══════════════════════════════════════════════════════════

def fetch_sbir_topics():
    """Fetch active SBIR/STTR solicitations from SBIR.gov API."""
    if not requests:
        return []

    signals = []
    url = "https://www.sbir.gov/api/solicitations.json"

    try:
        print("  Fetching from SBIR.gov API...")
        params = {"keyword": "", "open": "1"}
        response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            print(f"  SBIR.gov returned status {response.status_code}")
            return []

        data = response.json()
        # Handle both possible response formats
        items = data if isinstance(data, list) else data.get("results", data.get("data", []))

        for item in items[:100]:
            title = item.get("solicitation_title", item.get("title", ""))
            agency = item.get("solicitation_agency", item.get("agency", ""))
            desc = item.get("abstract", item.get("description", ""))

            if not title:
                continue

            # Determine sectors for this topic
            full_text = f"{title} {agency} {desc}"
            tech_areas = _tag_sectors(full_text)
            if tech_areas == ["general"]:
                continue  # Skip non-frontier-tech topics

            sol_type = item.get("solicitation_type", item.get("type", "SBIR"))
            phase = item.get("phase", "")

            signals.append({
                "id": f"SBIR-{item.get('solicitation_id', item.get('id', ''))}",
                "title": title[:200],
                "agency": agency or "SBA",
                "type": f"{sol_type} {phase}".strip(),
                "deadline": item.get("close_date", item.get("closeDate", "Rolling")),
                "value": _sbir_phase_value(phase),
                "priority": "High" if "phase ii" in phase.lower() else "Medium",
                "description": (desc or "")[:500],
                "techAreas": tech_areas,
                "source": item.get("solicitation_url", item.get("url", "https://www.sbir.gov")),
                "sourceApi": "sbir.gov",
                "posted": item.get("open_date", item.get("openDate", datetime.now().strftime("%Y-%m-%d"))),
                "fetchDate": datetime.now().strftime("%Y-%m-%d"),
            })

        print(f"  Found {len(signals)} relevant SBIR topics")
        return signals

    except Exception as e:
        print(f"  Error fetching SBIR data: {e}")
        return []


def fetch_grants_gov():
    """Fetch relevant grant opportunities from Grants.gov API."""
    if not requests:
        return []

    signals = []
    base_url = "https://api.grants.gov/v1/api/search2"

    # Keywords to search for
    search_keywords = [
        "autonomous systems defense",
        "nuclear energy reactor",
        "quantum computing",
        "space technology satellite",
        "artificial intelligence",
        "biotechnology synthetic biology",
        "cybersecurity",
        "robotics manufacturing",
        "directed energy",
        "hypersonic",
    ]

    seen_ids = set()

    for keyword in search_keywords:
        try:
            print(f"  Grants.gov: searching '{keyword}'...")
            payload = {
                "keyword": keyword,
                "oppStatuses": "posted,forecasted",
                "sortBy": "openDate|desc",
                "rows": 10,
                "startRecordNum": 0,
            }

            response = requests.post(base_url, json=payload, timeout=30)
            if response.status_code != 200:
                print(f"    Grants.gov returned {response.status_code} for '{keyword}'")
                continue

            data = response.json()
            hits = data.get("oppHits", data.get("opportunities", []))

            for item in (hits if isinstance(hits, list) else []):
                opp_id = item.get("id", item.get("oppNumber", ""))
                if not opp_id or opp_id in seen_ids:
                    continue
                seen_ids.add(opp_id)

                title = item.get("title", item.get("oppTitle", ""))
                agency = item.get("agency", item.get("agencyName", ""))

                if not title:
                    continue

                tech_areas = _tag_sectors(f"{title} {keyword}")

                signals.append({
                    "id": f"GRANT-{opp_id}",
                    "title": title[:200],
                    "agency": agency or "Federal",
                    "type": "Grant",
                    "deadline": item.get("closeDate", item.get("archiveDate", "Rolling")),
                    "value": item.get("awardCeiling", item.get("estimatedFunding", "Varies")),
                    "priority": "Medium",
                    "description": item.get("synopsis", item.get("description", ""))[:500],
                    "techAreas": tech_areas,
                    "source": f"https://www.grants.gov/search-results-detail/{opp_id}",
                    "sourceApi": "grants.gov",
                    "posted": item.get("openDate", item.get("postedDate", datetime.now().strftime("%Y-%m-%d"))),
                    "fetchDate": datetime.now().strftime("%Y-%m-%d"),
                })

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"    Grants.gov error for '{keyword}': {e}")

    print(f"  Found {len(signals)} relevant Grants.gov opportunities")
    return signals


def fetch_sam_gov():
    """Fetch opportunities from SAM.gov (requires SAM_API_KEY)."""
    api_key = os.environ.get("SAM_API_KEY", "")
    if not api_key or not requests:
        print("  SAM.gov: No API key available, skipping")
        return []

    signals = []
    base_url = "https://api.sam.gov/opportunities/v2/search"

    # Use only 3-4 queries to stay within 10/day limit
    search_keywords = ["autonomous defense", "nuclear energy", "space launch", "quantum AI"]

    for keyword in search_keywords[:4]:
        try:
            print(f"  SAM.gov: searching '{keyword}'...")
            params = {
                "api_key": api_key,
                "keywords": keyword,
                "postedFrom": (datetime.now() - timedelta(days=90)).strftime("%m/%d/%Y"),
                "limit": 10,
                "offset": 0,
            }

            response = requests.get(base_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("opportunitiesData", []):
                    title = item.get("title", "")
                    if not title:
                        continue

                    tech_areas = _tag_sectors(f"{title} {keyword}")

                    signals.append({
                        "id": f"SAM-{item.get('noticeId', '')}",
                        "title": title[:200],
                        "agency": item.get("department", item.get("fullParentPathName", "Federal"))[:100],
                        "type": item.get("type", "RFP"),
                        "deadline": item.get("responseDeadLine", "TBD"),
                        "value": "Varies",
                        "priority": "Medium",
                        "description": item.get("description", "")[:500],
                        "techAreas": tech_areas,
                        "source": item.get("uiLink", "https://sam.gov"),
                        "sourceApi": "sam.gov",
                        "posted": item.get("postedDate", datetime.now().strftime("%Y-%m-%d")),
                        "fetchDate": datetime.now().strftime("%Y-%m-%d"),
                    })
            else:
                print(f"    SAM.gov returned {response.status_code}")

            time.sleep(1)  # Conservative rate limiting

        except Exception as e:
            print(f"    SAM.gov error for '{keyword}': {e}")

    print(f"  Found {len(signals)} SAM.gov opportunities")
    return signals


# ─── HELPERS ───

SECTOR_KEYWORDS = {
    "defense": ["defense", "military", "weapon", "munitions", "warfighter", "tactical", "C4ISR", "DoD", "army", "navy", "air force", "marine", "SOCOM"],
    "space": ["space", "satellite", "launch", "orbital", "payload", "LEO", "cislunar", "NASA", "lunar", "Artemis"],
    "nuclear": ["nuclear", "reactor", "fission", "fusion", "HALEU", "SMR", "isotope", "NRC", "DOE nuclear"],
    "ai": ["artificial intelligence", "machine learning", "deep learning", "neural network", "autonomy", "computer vision", "AI", "ML"],
    "quantum": ["quantum", "qubit", "entanglement", "quantum computing", "quantum sensing", "quantum network"],
    "biotech": ["biotech", "synthetic biology", "gene", "cell therapy", "biomanufacturing", "protein", "pharmaceutical", "BARDA"],
    "cyber": ["cybersecurity", "cyber", "encryption", "zero trust", "network security", "CISA"],
    "robotics": ["robot", "unmanned", "drone", "UAS", "autonomous vehicle", "manipulation", "humanoid"],
    "energy": ["energy storage", "battery", "solar", "hydrogen", "grid", "geothermal", "carbon capture"],
    "hypersonic": ["hypersonic", "scramjet", "Mach", "thermal protection", "supersonic"],
    "advanced_materials": ["materials", "composite", "metamaterial", "additive manufacturing", "3D printing"],
}


def _tag_sectors(text):
    """Tag text with relevant sectors."""
    text_lower = text.lower()
    tags = []
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            tags.append(sector)
    return tags or ["general"]


def _sbir_phase_value(phase):
    """Estimate SBIR value based on phase."""
    if not phase:
        return "$50K-$2M"
    pl = phase.lower()
    if "iii" in pl:
        return "$5M-$50M+"
    if "ii" in pl:
        return "$750K-$2M"
    if "i" in pl:
        return "$50K-$275K"
    return "$50K-$2M"


# ═══════════════════════════════════════════════════════════
#  CURATED SEED DATA (fallback when APIs unavailable)
# ═══════════════════════════════════════════════════════════

def generate_seed_data():
    """
    Curated seed data — 44 real/realistic government opportunities
    spanning all frontier tech sectors.
    """
    return [
        # ─── DEFENSE (10) ───
        {
            "id": "DIU-CSO-2026-001",
            "title": "Autonomous Counter-UAS Systems for Base Defense",
            "agency": "Defense Innovation Unit (DIU)",
            "type": "Commercial Solutions Opening (CSO)",
            "deadline": "2026-04-30",
            "value": "$50M-$100M",
            "priority": "Critical",
            "description": "Seeking autonomous systems capable of detecting, tracking, classifying, and neutralizing small UAS threats in GPS-denied and urban environments. Multi-domain sensor fusion, low cost-per-engagement, and scalability required.",
            "techAreas": ["counter-drone", "autonomous systems", "electronic warfare", "AI", "defense"],
            "source": "https://www.diu.mil/",
            "sourceApi": "seed",
            "posted": "2026-01-15",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DARPA-BAA-2026-001",
            "title": "AI-Enabled Autonomous Naval Surface Vessels",
            "agency": "DARPA",
            "type": "Broad Agency Announcement (BAA)",
            "deadline": "Rolling",
            "value": "Up to $75M",
            "priority": "Critical",
            "description": "Research into fully autonomous naval surface vessels with swarm coordination capabilities. Multi-domain awareness and edge AI processing for maritime operations.",
            "techAreas": ["maritime", "autonomous systems", "AI", "swarm", "naval", "defense"],
            "source": "https://www.darpa.mil/",
            "sourceApi": "seed",
            "posted": "2025-12-01",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "AFWERX-SBIR-2026-001",
            "title": "Next-Generation Hypersonic Propulsion Systems",
            "agency": "AFWERX / Air Force",
            "type": "SBIR Phase III",
            "deadline": "2026-05-01",
            "value": "$25M",
            "priority": "High",
            "description": "Innovative hypersonic air-breathing propulsion solutions including scramjet improvements, thermal management, and combined-cycle engines for Mach 5+ vehicles.",
            "techAreas": ["hypersonic", "propulsion", "aerospace", "defense"],
            "source": "https://afwerx.com/",
            "sourceApi": "seed",
            "posted": "2026-01-20",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "ARMY-SBIR-2026-001",
            "title": "Soldier-Portable Directed Energy for Counter-Drone",
            "agency": "U.S. Army",
            "type": "SBIR Phase II",
            "deadline": "2026-03-28",
            "value": "$2M",
            "priority": "High",
            "description": "Man-portable directed energy systems for counter-drone and counter-electronics missions. Weight under 20 lbs, battery-powered, effective to 1km range.",
            "techAreas": ["directed energy", "counter-drone", "portable systems", "defense"],
            "source": "https://www.sbir.gov/",
            "sourceApi": "seed",
            "posted": "2026-01-05",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "NAVY-BAA-2026-001",
            "title": "Undersea Autonomous Systems for ISR",
            "agency": "Office of Naval Research (ONR)",
            "type": "BAA",
            "deadline": "2026-06-30",
            "value": "$60M",
            "priority": "High",
            "description": "Advanced autonomous underwater vehicles for intelligence, surveillance, reconnaissance, mine countermeasures, and anti-submarine warfare. Extended endurance and deep-ocean capability.",
            "techAreas": ["AUV", "undersea warfare", "autonomous systems", "naval", "defense"],
            "source": "https://www.onr.navy.mil/",
            "sourceApi": "seed",
            "posted": "2025-11-15",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DHS-SBIR-2026-001",
            "title": "Autonomous Border Surveillance Platforms",
            "agency": "Department of Homeland Security (DHS)",
            "type": "SBIR Phase II",
            "deadline": "2026-04-10",
            "value": "$3M",
            "priority": "Medium",
            "description": "Long-endurance autonomous systems for border surveillance with sensor fusion, edge processing, and operation in communications-denied environments.",
            "techAreas": ["surveillance", "autonomous systems", "border security", "drones", "defense"],
            "source": "https://www.dhs.gov/science-and-technology/sbir",
            "sourceApi": "seed",
            "posted": "2026-01-18",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DIU-CSO-2026-002",
            "title": "General-Purpose Robotics for Military Logistics",
            "agency": "Defense Innovation Unit (DIU)",
            "type": "Commercial Solutions Opening (CSO)",
            "deadline": "2026-05-15",
            "value": "$30M",
            "priority": "High",
            "description": "General-purpose robotics for logistics, maintenance, and resupply in austere environments. Interest in humanoid form factors for human-designed environments.",
            "techAreas": ["robotics", "humanoid", "logistics", "defense"],
            "source": "https://www.diu.mil/",
            "sourceApi": "seed",
            "posted": "2026-02-01",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "SOCOM-BAA-2026-001",
            "title": "AI-Powered Intelligence Fusion Platform",
            "agency": "SOCOM",
            "type": "BAA",
            "deadline": "Rolling",
            "value": "$20M",
            "priority": "High",
            "description": "Next-generation intelligence platform combining SIGINT, GEOINT, HUMINT, and OSINT data sources with ML-driven analysis and anomaly detection for special operations.",
            "techAreas": ["AI", "intelligence", "data fusion", "defense", "OSINT"],
            "source": "https://www.socom.mil/",
            "sourceApi": "seed",
            "posted": "2026-01-10",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DOD-SBIR-2026-EW",
            "title": "Cognitive Electronic Warfare Systems",
            "agency": "Department of Defense",
            "type": "SBIR Phase I",
            "deadline": "2026-04-15",
            "value": "$250K",
            "priority": "Medium",
            "description": "AI/ML-driven electronic warfare systems for real-time signal classification, threat identification, and adaptive jamming in contested electromagnetic environments.",
            "techAreas": ["electronic warfare", "AI", "RF", "defense", "spectrum"],
            "source": "https://www.sbir.gov/",
            "sourceApi": "seed",
            "posted": "2025-11-01",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DARPA-JADC2-2026",
            "title": "Joint All-Domain Command and Control Integration",
            "agency": "DARPA",
            "type": "BAA",
            "deadline": "2026-07-31",
            "value": "$40M",
            "priority": "Critical",
            "description": "Software platforms enabling real-time decision-making across air, land, sea, space, and cyber domains. Focus on interoperability, data fusion, and human-machine teaming.",
            "techAreas": ["C4ISR", "AI", "data fusion", "command control", "defense"],
            "source": "https://www.darpa.mil/",
            "sourceApi": "seed",
            "posted": "2026-02-10",
            "fetchDate": "2026-02-20",
        },

        # ─── SPACE (6) ───
        {
            "id": "USSF-2026-SATCOM",
            "title": "Resilient Proliferated LEO Communications",
            "agency": "U.S. Space Force",
            "type": "Request for Prototype Proposal",
            "deadline": "2026-04-30",
            "value": "$100M+",
            "priority": "Critical",
            "description": "Proliferated LEO constellation for secure military communications. Anti-jam, rapid reconstitution, and ground segment integration required.",
            "techAreas": ["satellite", "LEO constellation", "space", "communications", "defense"],
            "source": "https://www.spaceforce.mil/",
            "sourceApi": "seed",
            "posted": "2026-01-25",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "NASA-ARTEMIS-POWER",
            "title": "Fission Power Systems for Lunar Surface Operations",
            "agency": "NASA",
            "type": "Announcement of Collaborative Opportunity",
            "deadline": "2026-06-15",
            "value": "$50M",
            "priority": "High",
            "description": "Fission power systems for sustained lunar surface operations. 40 kWe continuous output target. Flight demonstration pathway within 5 years.",
            "techAreas": ["space nuclear", "lunar", "nuclear", "power", "space"],
            "source": "https://www.nasa.gov/",
            "sourceApi": "seed",
            "posted": "2026-02-05",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "NASA-STTR-2026-PROP",
            "title": "Advanced In-Space Propulsion Technologies",
            "agency": "NASA",
            "type": "STTR Phase I",
            "deadline": "2026-05-01",
            "value": "$150K",
            "priority": "Medium",
            "description": "Novel propulsion concepts for cislunar operations and deep space missions. Electric, nuclear thermal, and advanced chemical approaches.",
            "techAreas": ["space propulsion", "electric propulsion", "nuclear thermal propulsion", "space"],
            "source": "https://www.nasa.gov/",
            "sourceApi": "seed",
            "posted": "2025-12-01",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "SDA-2026-TRACKING",
            "title": "Missile Tracking Layer Satellites",
            "agency": "Space Development Agency (SDA)",
            "type": "Other Transaction",
            "deadline": "2026-05-30",
            "value": "$500M",
            "priority": "Critical",
            "description": "Low-Earth orbit missile warning and tracking satellites for the National Defense Space Architecture. Infrared sensor integration and mesh networking.",
            "techAreas": ["satellite", "missile defense", "infrared", "space", "defense"],
            "source": "https://www.sda.mil/",
            "sourceApi": "seed",
            "posted": "2026-01-08",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "NASA-SBIR-2026-ISAM",
            "title": "In-Space Assembly and Manufacturing",
            "agency": "NASA",
            "type": "SBIR Phase II",
            "deadline": "2026-04-15",
            "value": "$1.5M",
            "priority": "Medium",
            "description": "Robotic assembly and manufacturing capabilities for in-space construction of large structures, habitats, and spacecraft components.",
            "techAreas": ["in-space manufacturing", "robotics", "space", "assembly"],
            "source": "https://www.nasa.gov/",
            "sourceApi": "seed",
            "posted": "2026-01-20",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "NRO-2026-EO",
            "title": "Next-Generation Earth Observation Capabilities",
            "agency": "National Reconnaissance Office (NRO)",
            "type": "BAA",
            "deadline": "Rolling",
            "value": "$200M+",
            "priority": "High",
            "description": "Commercial satellite imagery and SAR capabilities for national security. High-revisit, sub-meter resolution, all-weather persistent surveillance.",
            "techAreas": ["earth observation", "SAR", "satellite", "remote sensing", "space", "defense"],
            "source": "https://www.nro.gov/",
            "sourceApi": "seed",
            "posted": "2026-02-01",
            "fetchDate": "2026-02-20",
        },

        # ─── NUCLEAR / ENERGY (6) ───
        {
            "id": "DOE-FOA-2026-HALEU",
            "title": "Advanced HALEU Fuel Fabrication Capabilities",
            "agency": "Department of Energy (DOE)",
            "type": "Funding Opportunity Announcement (FOA)",
            "deadline": "2026-05-30",
            "value": "$40M",
            "priority": "High",
            "description": "Development of HALEU fuel fabrication capabilities for next-generation microreactors and advanced reactors. TRISO and metallic fuel forms.",
            "techAreas": ["nuclear fuel", "HALEU", "manufacturing", "nuclear", "energy"],
            "source": "https://www.energy.gov/ne",
            "sourceApi": "seed",
            "posted": "2026-01-10",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DOE-ARPA-E-2026-FUSION",
            "title": "Compact Fusion Pilot Plant Technologies",
            "agency": "ARPA-E",
            "type": "FOA",
            "deadline": "2026-06-30",
            "value": "$75M",
            "priority": "High",
            "description": "Component technologies for compact fusion pilot plants. High-temperature superconductors, plasma heating systems, tritium breeding blankets, and structural materials.",
            "techAreas": ["fusion", "plasma", "energy", "superconductor", "nuclear"],
            "source": "https://arpa-e.energy.gov/",
            "sourceApi": "seed",
            "posted": "2026-01-15",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DOE-SBIR-2026-SMR",
            "title": "Advanced Small Modular Reactor Components",
            "agency": "Department of Energy (DOE)",
            "type": "SBIR Phase II",
            "deadline": "2026-04-01",
            "value": "$1.5M",
            "priority": "Medium",
            "description": "Innovative components for small modular reactors including advanced instrumentation, passive safety systems, and digital twin modeling.",
            "techAreas": ["SMR", "nuclear", "reactor", "instrumentation", "energy"],
            "source": "https://www.energy.gov/ne",
            "sourceApi": "seed",
            "posted": "2025-10-15",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DOE-FOA-2026-GEOTHERMAL",
            "title": "Enhanced Geothermal Systems Demonstration",
            "agency": "Department of Energy (DOE)",
            "type": "FOA",
            "deadline": "2026-07-31",
            "value": "$100M",
            "priority": "High",
            "description": "Demonstration projects for enhanced geothermal systems. Drilling innovation, reservoir stimulation, and closed-loop approaches to unlock 100+ GW of geothermal potential.",
            "techAreas": ["geothermal", "energy", "drilling", "clean energy"],
            "source": "https://www.energy.gov/eere",
            "sourceApi": "seed",
            "posted": "2026-02-15",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DOE-FOA-2026-STORAGE",
            "title": "Long-Duration Energy Storage Technologies",
            "agency": "Department of Energy (DOE)",
            "type": "FOA",
            "deadline": "2026-06-15",
            "value": "$60M",
            "priority": "High",
            "description": "Grid-scale energy storage systems providing 10+ hours of discharge. Iron-air batteries, flow batteries, compressed air, and novel chemistries.",
            "techAreas": ["energy storage", "battery", "grid", "energy"],
            "source": "https://www.energy.gov/oe",
            "sourceApi": "seed",
            "posted": "2026-01-28",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DOE-FOA-2026-DAC",
            "title": "Direct Air Capture Hub Expansion",
            "agency": "Department of Energy (DOE)",
            "type": "FOA",
            "deadline": "2026-08-31",
            "value": "$500M",
            "priority": "Critical",
            "description": "Second round of Regional Direct Air Capture Hub funding. Large-scale facilities capturing 1M+ tonnes CO2 per year. Novel sorbents and process intensification.",
            "techAreas": ["carbon capture", "DAC", "climate", "energy"],
            "source": "https://www.energy.gov/oced",
            "sourceApi": "seed",
            "posted": "2026-02-10",
            "fetchDate": "2026-02-20",
        },

        # ─── AI (5) ───
        {
            "id": "NSF-SBIR-2026-AI",
            "title": "Trustworthy AI Systems for Critical Infrastructure",
            "agency": "National Science Foundation (NSF)",
            "type": "SBIR Phase I",
            "deadline": "2026-04-15",
            "value": "$275K",
            "priority": "Medium",
            "description": "AI/ML systems with verifiable safety guarantees for critical infrastructure. Explainable AI, formal verification, and robust performance under adversarial conditions.",
            "techAreas": ["AI", "safety", "critical infrastructure", "machine learning"],
            "source": "https://www.nsf.gov/",
            "sourceApi": "seed",
            "posted": "2026-01-05",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DARPA-AI-2026-AGENT",
            "title": "Autonomous AI Agents for Complex Decision Making",
            "agency": "DARPA",
            "type": "BAA",
            "deadline": "Rolling",
            "value": "$35M",
            "priority": "High",
            "description": "Development of AI agent architectures capable of autonomous planning, reasoning, and action in complex, partially-observable environments.",
            "techAreas": ["AI", "autonomous agents", "planning", "reasoning"],
            "source": "https://www.darpa.mil/",
            "sourceApi": "seed",
            "posted": "2026-02-01",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DHS-SBIR-2026-CYBER",
            "title": "AI-Powered Cybersecurity for Critical Infrastructure",
            "agency": "Department of Homeland Security (DHS)",
            "type": "SBIR Phase I",
            "deadline": "2026-04-30",
            "value": "$200K",
            "priority": "Medium",
            "description": "Machine learning for detecting and responding to cyber threats against energy, water, and transportation infrastructure. Zero-day detection and automated response.",
            "techAreas": ["cybersecurity", "AI", "critical infrastructure", "cyber"],
            "source": "https://www.dhs.gov/science-and-technology/sbir",
            "sourceApi": "seed",
            "posted": "2025-12-15",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "NSF-2026-AIINST",
            "title": "National AI Research Institutes — Frontier AI",
            "agency": "National Science Foundation (NSF)",
            "type": "Grant",
            "deadline": "2026-06-30",
            "value": "$20M per institute",
            "priority": "High",
            "description": "Funding for AI Research Institutes focused on frontier capabilities: large-scale reasoning, multimodal understanding, and human-AI collaboration.",
            "techAreas": ["AI", "research", "machine learning", "LLM"],
            "source": "https://www.nsf.gov/",
            "sourceApi": "seed",
            "posted": "2026-02-15",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DOD-CDAO-2026-DATA",
            "title": "Enterprise AI/ML Data Platform",
            "agency": "Chief Digital and AI Office (CDAO)",
            "type": "Other Transaction",
            "deadline": "2026-05-15",
            "value": "$50M",
            "priority": "High",
            "description": "Scalable data labeling, model training, and deployment infrastructure for DoD-wide AI/ML initiatives. Focus on classified environments and edge deployment.",
            "techAreas": ["AI", "data labeling", "ML infrastructure", "defense"],
            "source": "https://www.ai.mil/",
            "sourceApi": "seed",
            "posted": "2026-01-20",
            "fetchDate": "2026-02-20",
        },

        # ─── QUANTUM (4) ───
        {
            "id": "NSF-SBIR-2026-QUANTUM",
            "title": "Quantum Error Correction Hardware",
            "agency": "National Science Foundation (NSF)",
            "type": "SBIR Phase I",
            "deadline": "2026-04-30",
            "value": "$275K",
            "priority": "Medium",
            "description": "Hardware-level quantum error correction for fault-tolerant quantum computing. Novel qubit architectures, error syndrome extraction, and real-time decoding.",
            "techAreas": ["quantum computing", "qubit", "error correction", "quantum"],
            "source": "https://www.nsf.gov/",
            "sourceApi": "seed",
            "posted": "2025-11-15",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DOE-QIS-2026-NETWORK",
            "title": "Quantum Networking and Entanglement Distribution",
            "agency": "Department of Energy (DOE)",
            "type": "FOA",
            "deadline": "2026-07-15",
            "value": "$30M",
            "priority": "High",
            "description": "Long-distance quantum entanglement distribution and quantum repeater technologies. Building blocks for a national quantum internet infrastructure.",
            "techAreas": ["quantum network", "entanglement", "quantum", "QKD"],
            "source": "https://www.energy.gov/science",
            "sourceApi": "seed",
            "posted": "2026-01-30",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DARPA-2026-QSENSOR",
            "title": "Quantum Sensing for Position, Navigation, and Timing",
            "agency": "DARPA",
            "type": "BAA",
            "deadline": "Rolling",
            "value": "$25M",
            "priority": "High",
            "description": "Quantum sensors for GPS-denied navigation. Atom interferometers, NV-center magnetometers, and chip-scale quantum clocks for military applications.",
            "techAreas": ["quantum sensing", "navigation", "PNT", "quantum", "defense"],
            "source": "https://www.darpa.mil/",
            "sourceApi": "seed",
            "posted": "2026-02-05",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "NSA-2026-CRYPTO",
            "title": "Post-Quantum Cryptography Migration Tools",
            "agency": "NSA / CISA",
            "type": "Grant",
            "deadline": "2026-06-30",
            "value": "$15M",
            "priority": "Medium",
            "description": "Tools and frameworks for migrating government systems to post-quantum cryptographic standards. Automated cryptographic inventory and migration planning.",
            "techAreas": ["quantum", "cybersecurity", "cryptography", "post-quantum"],
            "source": "https://www.nsa.gov/",
            "sourceApi": "seed",
            "posted": "2026-01-15",
            "fetchDate": "2026-02-20",
        },

        # ─── BIOTECH (3) ───
        {
            "id": "BARDA-2026-BIOMANUF",
            "title": "Advanced Biomanufacturing for Pandemic Preparedness",
            "agency": "BARDA / HHS",
            "type": "BAA",
            "deadline": "Rolling",
            "value": "$100M",
            "priority": "High",
            "description": "Scalable biomanufacturing platforms for rapid vaccine and therapeutic production. Synthetic biology approaches to accelerate development timelines.",
            "techAreas": ["biomanufacturing", "synthetic biology", "vaccine", "biotech"],
            "source": "https://www.medicalcountermeasures.gov/",
            "sourceApi": "seed",
            "posted": "2026-01-10",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "NASA-SBIR-2026-BIO",
            "title": "Synthetic Biology for Space Life Support",
            "agency": "NASA",
            "type": "SBIR Phase I",
            "deadline": "2026-05-15",
            "value": "$150K",
            "priority": "Medium",
            "description": "Engineered biological systems for air revitalization and waste processing in long-duration space missions. Synthetic biology and metabolic engineering approaches.",
            "techAreas": ["synthetic biology", "biotech", "space", "life support"],
            "source": "https://www.nasa.gov/",
            "sourceApi": "seed",
            "posted": "2026-02-01",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "NIH-2026-GENETHERAPY",
            "title": "Next-Generation Gene Therapy Delivery",
            "agency": "National Institutes of Health (NIH)",
            "type": "Grant (R01)",
            "deadline": "2026-06-05",
            "value": "$3M",
            "priority": "Medium",
            "description": "Novel viral and non-viral gene therapy delivery vehicles with improved tissue specificity, reduced immunogenicity, and manufacturing scalability.",
            "techAreas": ["gene therapy", "gene editing", "biotech", "delivery"],
            "source": "https://www.nih.gov/",
            "sourceApi": "seed",
            "posted": "2026-01-25",
            "fetchDate": "2026-02-20",
        },

        # ─── CYBER (3) ───
        {
            "id": "CISA-2026-ZEROTRUST",
            "title": "Zero Trust Architecture Implementation Tools",
            "agency": "CISA / DHS",
            "type": "Grant",
            "deadline": "2026-05-31",
            "value": "$10M",
            "priority": "Medium",
            "description": "Tools and platforms for federal agencies to implement zero trust security architectures. Identity management, micro-segmentation, and continuous verification.",
            "techAreas": ["cybersecurity", "zero trust", "identity", "network security", "cyber"],
            "source": "https://www.cisa.gov/",
            "sourceApi": "seed",
            "posted": "2026-01-20",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "NSA-2026-AIDEFENSE",
            "title": "AI-Enabled Cyber Defense Operations",
            "agency": "NSA Cybersecurity Directorate",
            "type": "BAA",
            "deadline": "Rolling",
            "value": "$30M",
            "priority": "High",
            "description": "Machine learning for automated cyber threat hunting, adversary emulation, and network defense. Real-time behavioral analytics and threat intelligence fusion.",
            "techAreas": ["cybersecurity", "AI", "threat intelligence", "defense", "cyber"],
            "source": "https://www.nsa.gov/cybersecurity/",
            "sourceApi": "seed",
            "posted": "2026-02-01",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DOD-SBIR-2026-CRYPTO",
            "title": "Secure Communications for Contested Environments",
            "agency": "Department of Defense",
            "type": "SBIR Phase I",
            "deadline": "2026-04-15",
            "value": "$250K",
            "priority": "Medium",
            "description": "Encrypted communications systems resilient to jamming and interception in contested electromagnetic environments. Mesh networking and frequency hopping.",
            "techAreas": ["communications", "encryption", "mesh network", "defense", "cyber"],
            "source": "https://www.sbir.gov/",
            "sourceApi": "seed",
            "posted": "2026-01-08",
            "fetchDate": "2026-02-20",
        },

        # ─── ROBOTICS (3) ───
        {
            "id": "DARPA-2026-HUMANOID",
            "title": "Dexterous Manipulation for Unstructured Environments",
            "agency": "DARPA",
            "type": "BAA",
            "deadline": "2026-06-30",
            "value": "$45M",
            "priority": "High",
            "description": "Robotic manipulation systems capable of human-like dexterity in unstructured military and industrial environments. Adaptive grasping, tool use, and reactive planning.",
            "techAreas": ["robotics", "manipulation", "humanoid", "dexterity", "AI"],
            "source": "https://www.darpa.mil/",
            "sourceApi": "seed",
            "posted": "2026-02-10",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "ARMY-2026-LOGISTICS-ROBOT",
            "title": "Autonomous Logistics Resupply Vehicles",
            "agency": "U.S. Army",
            "type": "Other Transaction",
            "deadline": "2026-05-01",
            "value": "$20M",
            "priority": "Medium",
            "description": "Autonomous ground vehicles for last-mile logistics resupply in contested areas. Terrain navigation, load management, and convoy operations.",
            "techAreas": ["autonomous vehicle", "logistics", "robotics", "defense", "UGV"],
            "source": "https://www.army.mil/",
            "sourceApi": "seed",
            "posted": "2026-01-15",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "NSF-2026-AGROBOT",
            "title": "Intelligent Agricultural Robotics",
            "agency": "National Science Foundation (NSF)",
            "type": "Grant",
            "deadline": "2026-07-15",
            "value": "$5M",
            "priority": "Low",
            "description": "Autonomous robotic systems for precision agriculture including harvesting, weeding, and crop monitoring using computer vision and AI.",
            "techAreas": ["robotics", "agriculture", "AI", "computer vision"],
            "source": "https://www.nsf.gov/",
            "sourceApi": "seed",
            "posted": "2026-02-15",
            "fetchDate": "2026-02-20",
        },

        # ─── ADVANCED MATERIALS (2) ───
        {
            "id": "DOD-SBIR-2026-MATERIALS",
            "title": "Hypersonic Vehicle Thermal Protection Materials",
            "agency": "Department of Defense",
            "type": "SBIR Phase II",
            "deadline": "2026-03-15",
            "value": "$1.5M",
            "priority": "High",
            "description": "Advanced ceramic and composite materials for thermal protection systems on hypersonic flight vehicles operating at Mach 5+ speeds.",
            "techAreas": ["advanced materials", "hypersonic", "thermal protection", "defense"],
            "source": "https://www.sbir.gov/",
            "sourceApi": "seed",
            "posted": "2025-10-01",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DOE-2026-ADDITIVE",
            "title": "Additive Manufacturing for Energy Applications",
            "agency": "Department of Energy (DOE)",
            "type": "FOA",
            "deadline": "2026-06-30",
            "value": "$25M",
            "priority": "Medium",
            "description": "3D printing and additive manufacturing techniques for energy system components. Nuclear fuel elements, heat exchangers, and turbine components.",
            "techAreas": ["additive manufacturing", "3D printing", "nuclear", "energy"],
            "source": "https://www.energy.gov/",
            "sourceApi": "seed",
            "posted": "2026-02-05",
            "fetchDate": "2026-02-20",
        },

        # ─── CLIMATE (2) ───
        {
            "id": "EPA-2026-METHANE",
            "title": "Methane Emissions Monitoring and Reduction",
            "agency": "Environmental Protection Agency (EPA)",
            "type": "Grant",
            "deadline": "2026-05-31",
            "value": "$50M",
            "priority": "Medium",
            "description": "Satellite and ground-based methane detection and monitoring systems. Remote sensing, AI-driven leak detection, and emissions quantification.",
            "techAreas": ["emissions monitoring", "methane", "remote sensing", "climate"],
            "source": "https://www.epa.gov/",
            "sourceApi": "seed",
            "posted": "2026-01-30",
            "fetchDate": "2026-02-20",
        },
        {
            "id": "DOE-2026-HYDROGEN",
            "title": "Clean Hydrogen Hub Expansion",
            "agency": "Department of Energy (DOE)",
            "type": "FOA",
            "deadline": "2026-09-30",
            "value": "$1B",
            "priority": "Critical",
            "description": "Expansion of regional clean hydrogen hubs. Green hydrogen production via electrolysis, storage, transport, and end-use applications.",
            "techAreas": ["hydrogen", "electrolysis", "clean energy", "energy"],
            "source": "https://www.energy.gov/oced",
            "sourceApi": "seed",
            "posted": "2026-02-18",
            "fetchDate": "2026-02-20",
        },
    ]


# ═══════════════════════════════════════════════════════════
#  OUTPUT GENERATION
# ═══════════════════════════════════════════════════════════

def generate_js_output(signals, pull_scores):
    """Generate JavaScript output file."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Compute stats
    source_counts = {}
    agency_counts = {}
    companies_matched = set()

    for s in signals:
        src = s.get("sourceApi", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1

        agency = s.get("agency", "Unknown")
        agency_counts[agency] = agency_counts.get(agency, 0) + 1

        for mc in s.get("matchedCompanies", []):
            companies_matched.add(mc["name"])

    stats = {
        "totalSignals": len(signals),
        "bySource": source_counts,
        "byAgency": agency_counts,
        "companiesMatched": len(companies_matched),
        "lastUpdated": now,
    }

    # Clean signals for JSON output (remove any non-serializable data)
    clean_signals = []
    for s in signals:
        clean = {k: v for k, v in s.items() if v is not None}
        clean_signals.append(clean)

    js_content = f"""// Auto-generated demand signals data
// Last updated: {now}
// Total signals: {len(signals)} | Companies matched: {len(companies_matched)}

const GOV_DEMAND_SIGNALS_AUTO = {json.dumps(clean_signals, indent=2)};

const GOV_PULL_SCORES_AUTO = {json.dumps(pull_scores, indent=2)};

const DEMAND_SIGNALS_STATS = {json.dumps(stats, indent=2)};
"""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    js_path = DATA_DIR / "demand_signals_auto.js"
    with open(js_path, "w") as f:
        f.write(js_content)
    print(f"  Saved: {js_path} ({js_path.stat().st_size / 1024:.0f}KB)")

    json_path = DATA_DIR / "demand_signals_auto.json"
    with open(json_path, "w") as f:
        json.dump({"signals": clean_signals, "pullScores": pull_scores, "stats": stats}, f, indent=2)
    print(f"  Saved: {json_path}")

    return clean_signals


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("Demand Signal Radar — Unified Fetcher & Matcher")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Extract companies from data.js
    print("\n[1/5] Extracting company data from data.js...")
    companies = extract_companies_for_matching()
    if not companies:
        print("  ERROR: No companies extracted. Aborting.")
        sys.exit(1)

    # Step 2: Fetch from APIs
    print("\n[2/5] Fetching government opportunities from APIs...")
    all_signals = []

    sbir = fetch_sbir_topics()
    all_signals.extend(sbir)

    grants = fetch_grants_gov()
    all_signals.extend(grants)

    sam = fetch_sam_gov()
    all_signals.extend(sam)

    print(f"\n  API total: {len(all_signals)} signals")

    # Fallback to seed data if APIs returned very little
    if len(all_signals) < 10:
        print("\n  Insufficient API data — supplementing with curated seed data...")
        seed = generate_seed_data()
        # Merge: don't duplicate IDs from API results
        api_ids = {s["id"] for s in all_signals}
        for s in seed:
            if s["id"] not in api_ids:
                all_signals.append(s)
        print(f"  After seed data: {len(all_signals)} total signals")

    # Step 3: Deduplicate by ID
    seen_ids = set()
    unique_signals = []
    for s in all_signals:
        if s["id"] not in seen_ids:
            seen_ids.add(s["id"])
            unique_signals.append(s)
    print(f"\n  Unique signals after dedup: {len(unique_signals)}")

    # Step 4: Match companies to signals
    print("\n[3/5] Matching companies to signals...")
    for i, signal in enumerate(unique_signals):
        matches = match_companies_to_signal(signal, companies)
        signal["matchedCompanies"] = matches
        # Also set flat relevantCompanies for backward compatibility
        signal["relevantCompanies"] = [m["name"] for m in matches]

        if (i + 1) % 10 == 0:
            print(f"  Matched {i + 1}/{len(unique_signals)} signals...")

    # Stats
    total_matches = sum(len(s.get("matchedCompanies", [])) for s in unique_signals)
    matched_companies = set()
    for s in unique_signals:
        for mc in s.get("matchedCompanies", []):
            matched_companies.add(mc["name"])
    print(f"  Total company-signal matches: {total_matches}")
    print(f"  Unique companies matched: {len(matched_companies)}/{len(companies)}")

    # Step 5: Compute Government Pull Scores
    print("\n[4/5] Computing Government Pull Scores...")
    pull_scores = compute_gov_pull_scores(unique_signals, companies)
    print(f"  Companies with pull scores: {len(pull_scores)}")

    # Top 10 by pull score
    top_pull = sorted(pull_scores.values(), key=lambda x: -x["govPullScore"])[:10]
    if top_pull:
        print("\n  Top 10 Government Pull Scores:")
        for p in top_pull:
            print(f"    {p['govPullScore']:3d}  {p['name']} ({p['matchCount']} signals, {', '.join(p['topAgencies'][:2])})")

    # Step 6: Generate output
    print("\n[5/5] Generating output files...")
    generate_js_output(unique_signals, pull_scores)

    print(f"\n{'=' * 60}")
    print(f"COMPLETE: {len(unique_signals)} signals, {len(pull_scores)} companies scored")
    print("=" * 60)


if __name__ == "__main__":
    main()
