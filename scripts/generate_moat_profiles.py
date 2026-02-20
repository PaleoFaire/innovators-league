#!/usr/bin/env python3
"""
Technical Moat Breakdown Generator for The Innovators League
Cross-references INNOVATOR_SCORES, PATENT_INTEL, GOV_CONTRACTS,
ALT_DATA_SIGNALS, TRL_RANKINGS, and COMPANIES to produce
dimensional moat profiles for the top 60 companies.

Output: data/moat_profiles.js
"""

import json
import re
from datetime import datetime
from pathlib import Path

DATA_JS = Path(__file__).parent.parent / "data.js"
OUTPUT_JS = Path(__file__).parent.parent / "data" / "moat_profiles.js"

# ── Dimension weight for moatDepth composite ──
WEIGHTS = {
    "regulatoryMoat": 0.20,
    "switchingCosts": 0.25,
    "manufacturingReadiness": 0.15,
    "dataAdvantage": 0.15,
    "supplyChainControl": 0.10,
    "talentDensity": 0.15,
}

# ── Keyword maps for heuristic scoring ──
REGULATORY_KEYWORDS = {
    "itar": 3, "classified": 3, "ts/sci": 3, "secret": 2,
    "nrc": 3, "nuclear": 2, "faa": 2, "fda": 2,
    "fedramp": 2, "cmmc": 1, "clearance": 2,
    "export control": 2, "munitions": 2, "dod": 1,
    "darpa": 1, "license": 1,
}

SWITCHING_COST_KEYWORDS = {
    "platform": 3, "operating system": 3, "os ": 2, "ecosystem": 3,
    "integration": 2, "integrated": 2, "foundry": 2, "ontology": 3,
    "api": 1, "sdk": 1, "data lake": 2, "pipeline": 1,
    "command and control": 2, "c2": 2, "backbone": 2,
    "workflow": 1, "enterprise": 1,
}

SUPPLY_CHAIN_KEYWORDS = {
    "vertical": 3, "vertically integrated": 4, "in-house": 2,
    "manufacturing": 2, "factory": 2, "foundry": 2,
    "proprietary": 2, "custom": 1, "supply chain": 2,
    "rare earth": 3, "critical mineral": 3, "haleu": 3,
    "fuel": 2, "acquisition": 1,
}

DATA_ADVANTAGE_KEYWORDS = {
    "data": 2, "dataset": 3, "training data": 3,
    "sensor fusion": 3, "telemetry": 2, "proprietary data": 3,
    "flight data": 2, "operational data": 2, "labeled": 2,
    "annotation": 2, "imagery": 2, "geospatial": 2,
    "model": 1, "foundation model": 2, "ai": 1, "ml": 1,
}

# ── Sector-based regulatory inference ──
SECTOR_REGULATORY_BASE = {
    "Defense & Security": 7,
    "Space & Aerospace": 5,
    "Nuclear Energy": 7,
    "Energy & Climate": 4,
    "Biotech & Health": 5,
    "AI & Software": 3,
    "Robotics & Manufacturing": 3,
    "Quantum Computing": 4,
    "Advanced Materials": 3,
    "Transportation & Logistics": 3,
}

# ── Primary moat type classification rules ──
# (dimension_key, min_score) pairs — first match wins
MOAT_TYPE_RULES = [
    # If both regulatory and switching costs are high → regulatory-platform
    (lambda d: d.get("regulatoryMoat", {}).get("score", 0) >= 7 and
               d.get("switchingCosts", {}).get("score", 0) >= 7, "regulatory-platform"),
    (lambda d: d.get("regulatoryMoat", {}).get("score", 0) >= 7, "regulatory"),
    (lambda d: d.get("switchingCosts", {}).get("score", 0) >= 8, "platform"),
    (lambda d: d.get("dataAdvantage", {}).get("score", 0) >= 7 and
               d.get("switchingCosts", {}).get("score", 0) >= 5, "ip-data"),
    (lambda d: d.get("manufacturingReadiness", {}).get("score", 0) >= 8, "manufacturing"),
    (lambda d: d.get("talentDensity", {}).get("score", 0) >= 8, "talent"),
    (lambda d: True, "platform"),  # default
]

# ── Moat dimension labels by score range ──
REGULATORY_LABELS = {
    (9, 10): "ITAR + Classified",
    (7, 8): "Licensed & Regulated",
    (5, 6): "Moderately Regulated",
    (3, 4): "Light Regulation",
    (0, 2): "Minimal Barriers",
}

SWITCHING_LABELS = {
    (9, 10): "Deep Integration",
    (7, 8): "Platform Lock-in",
    (5, 6): "Moderate Stickiness",
    (3, 4): "Some Switching Costs",
    (0, 2): "Easy to Switch",
}

MFG_LABELS = {
    (9, 10): "Production at Scale",
    (7, 8): "Scaling Up",
    (5, 6): "Pilot Production",
    (3, 4): "Prototype Stage",
    (0, 2): "Lab / Pre-Production",
}

DATA_LABELS = {
    (9, 10): "Proprietary Data Flywheel",
    (7, 8): "Strong Data Moat",
    (5, 6): "Growing Dataset",
    (3, 4): "Early Data Collection",
    (0, 2): "Limited Data",
}

SUPPLY_LABELS = {
    (9, 10): "Full Vertical Integration",
    (7, 8): "Vertical Stack",
    (5, 6): "Partial Integration",
    (3, 4): "Standard Supply Chain",
    (0, 2): "Outsourced",
}

TALENT_LABELS = {
    (9, 10): "Elite Pipeline",
    (7, 8): "Strong Talent Draw",
    (5, 6): "Competitive Hiring",
    (3, 4): "Standard Talent",
    (0, 2): "Talent Challenged",
}

LABEL_MAPS = {
    "regulatoryMoat": REGULATORY_LABELS,
    "switchingCosts": SWITCHING_LABELS,
    "manufacturingReadiness": MFG_LABELS,
    "dataAdvantage": DATA_LABELS,
    "supplyChainControl": SUPPLY_LABELS,
    "talentDensity": TALENT_LABELS,
}


def get_label(dimension, score):
    """Get the label for a dimension score."""
    label_map = LABEL_MAPS.get(dimension, {})
    for (low, high), label in label_map.items():
        if low <= score <= high:
            return label
    return "Unknown"


def keyword_score(text, keyword_map, base=0, cap=10):
    """Score text against a keyword map. Returns 0-10."""
    text_lower = text.lower()
    total = base
    for kw, pts in keyword_map.items():
        if kw.lower() in text_lower:
            total += pts
    return min(total, cap)


def extract_array(content, name):
    """Extract a JS array from data.js content."""
    # Match const NAME = [ ... ];
    pattern = rf'const {name}\s*=\s*\[(.*?)\];'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return []

    array_content = match.group(1)
    # Extract company names
    companies = re.findall(r'company:\s*"([^"]+)"', array_content)
    return companies


def extract_companies_data(content):
    """Extract full company data from COMPANIES array."""
    companies = {}

    # Find COMPANIES array
    match = re.search(r'const COMPANIES\s*=\s*\[(.*?)\n\];', content, re.DOTALL)
    if not match:
        return companies

    text = match.group(1)

    # Split into individual company blocks
    blocks = re.split(r'\n  \{', text)

    for block in blocks:
        name_m = re.search(r'name:\s*"([^"]+)"', block)
        if not name_m:
            continue
        name = name_m.group(1)

        c = {"name": name}

        # Extract fields
        sector_m = re.search(r'sector:\s*"([^"]+)"', block)
        c["sector"] = sector_m.group(1) if sector_m else ""

        desc_m = re.search(r'description:\s*"([^"]*)"', block)
        c["description"] = desc_m.group(1) if desc_m else ""

        ta_m = re.search(r'techApproach:\s*"([^"]*)"', block)
        c["techApproach"] = ta_m.group(1) if ta_m else ""

        tc_m = re.search(r'thesisCluster:\s*"([^"]*)"', block)
        c["thesisCluster"] = tc_m.group(1) if tc_m else ""

        # Tags
        tags_m = re.search(r'tags:\s*\[(.*?)\]', block, re.DOTALL)
        if tags_m:
            c["tags"] = re.findall(r'"([^"]+)"', tags_m.group(1))
        else:
            c["tags"] = []

        # Insight
        insight_m = re.search(r'insight:\s*"([^"]*)"', block)
        c["insight"] = insight_m.group(1) if insight_m else ""

        # Thesis bull/bear
        bull_m = re.search(r'bull:\s*"([^"]*)"', block)
        c["bull"] = bull_m.group(1) if bull_m else ""

        bear_m = re.search(r'bear:\s*"([^"]*)"', block)
        c["bear"] = bear_m.group(1) if bear_m else ""

        # Risks
        risks_m = re.search(r'risks:\s*\[(.*?)\]', block, re.DOTALL)
        if risks_m:
            c["risks"] = re.findall(r'"([^"]+)"', risks_m.group(1))
        else:
            c["risks"] = []

        # Recent event
        event_m = re.search(r'recentEvent:\s*\{[^}]*text:\s*"([^"]*)"', block)
        c["recentEvent"] = event_m.group(1) if event_m else ""

        # Signal
        signal_m = re.search(r'signal:\s*"([^"]*)"', block)
        c["signal"] = signal_m.group(1) if signal_m else ""

        companies[name] = c

    return companies


def extract_innovator_scores(content):
    """Extract INNOVATOR_SCORES data."""
    scores = {}
    match = re.search(r'const INNOVATOR_SCORES\s*=\s*\[(.*?)\];', content, re.DOTALL)
    if not match:
        return scores

    text = match.group(1)
    blocks = re.split(r'\{', text)

    for block in blocks:
        name_m = re.search(r'company:\s*"([^"]+)"', block)
        if not name_m:
            continue
        name = name_m.group(1)

        s = {}
        for field in ["techMoat", "momentum", "teamPedigree", "marketGravity",
                       "capitalEfficiency", "govTraction", "composite"]:
            fm = re.search(rf'{field}:\s*([\d.]+)', block)
            s[field] = float(fm.group(1)) if fm else 0

        tier_m = re.search(r'tier:\s*"([^"]+)"', block)
        s["tier"] = tier_m.group(1) if tier_m else ""

        note_m = re.search(r'note:\s*"([^"]*)"', block)
        s["note"] = note_m.group(1) if note_m else ""

        scores[name] = s

    return scores


def extract_gov_contracts(content):
    """Extract GOV_CONTRACTS data."""
    contracts = {}
    match = re.search(r'const GOV_CONTRACTS\s*=\s*\[(.*?)\];', content, re.DOTALL)
    if not match:
        return contracts

    text = match.group(1)
    blocks = re.split(r'\n  \{', text)

    for block in blocks:
        name_m = re.search(r'company:\s*"([^"]+)"', block)
        if not name_m:
            continue
        name = name_m.group(1)

        c = {}
        cl_m = re.search(r'clearanceLevel:\s*"([^"]*)"', block)
        c["clearanceLevel"] = cl_m.group(1) if cl_m else ""

        tv_m = re.search(r'totalGovValue:\s*"([^"]*)"', block)
        c["totalGovValue"] = tv_m.group(1) if tv_m else ""

        sbir_m = re.search(r'sbirStatus:\s*"([^"]*)"', block)
        c["sbirStatus"] = sbir_m.group(1) if sbir_m else ""

        mix_m = re.search(r'contractMix:\s*"([^"]*)"', block)
        c["contractMix"] = mix_m.group(1) if mix_m else ""

        rev_m = re.search(r'govRevenuePercent:\s*"([^"]*)"', block)
        c["govRevenuePercent"] = rev_m.group(1) if rev_m else ""

        notes_m = re.search(r'notes:\s*"([^"]*)"', block)
        c["notes"] = notes_m.group(1) if notes_m else ""

        # Agencies
        agencies_m = re.search(r'agencies:\s*\[(.*?)\]', block, re.DOTALL)
        if agencies_m:
            c["agencies"] = re.findall(r'"([^"]+)"', agencies_m.group(1))
        else:
            c["agencies"] = []

        contracts[name] = c

    return contracts


def extract_patent_intel(content):
    """Extract PATENT_INTEL data."""
    patents = {}
    match = re.search(r'const PATENT_INTEL\s*=\s*\[(.*?)\];', content, re.DOTALL)
    if not match:
        return patents

    text = match.group(1)
    blocks = re.split(r'\n  \{', text)

    for block in blocks:
        name_m = re.search(r'company:\s*"([^"]+)"', block)
        if not name_m:
            continue
        name = name_m.group(1)

        p = {}
        tp_m = re.search(r'totalPatents:\s*(\d+)', block)
        p["totalPatents"] = int(tp_m.group(1)) if tp_m else 0

        ip_m = re.search(r'ipMoatScore:\s*(\d+)', block)
        p["ipMoatScore"] = int(ip_m.group(1)) if ip_m else 0

        vt_m = re.search(r'velocityTrend:\s*"([^"]*)"', block)
        p["velocityTrend"] = vt_m.group(1) if vt_m else ""

        note_m = re.search(r'note:\s*"([^"]*)"', block)
        p["note"] = note_m.group(1) if note_m else ""

        patents[name] = p

    return patents


def extract_alt_data(content):
    """Extract ALT_DATA_SIGNALS data."""
    signals = {}
    match = re.search(r'const ALT_DATA_SIGNALS\s*=\s*\[(.*?)\];', content, re.DOTALL)
    if not match:
        return signals

    text = match.group(1)
    blocks = re.split(r'\n  \{', text)

    for block in blocks:
        name_m = re.search(r'company:\s*"([^"]+)"', block)
        if not name_m:
            continue
        name = name_m.group(1)

        s = {}
        hv_m = re.search(r'hiringVelocity:\s*"([^"]*)"', block)
        s["hiringVelocity"] = hv_m.group(1) if hv_m else ""

        hc_m = re.search(r'headcountEstimate:\s*"([^"]*)"', block)
        s["headcountEstimate"] = hc_m.group(1) if hc_m else ""

        ss_m = re.search(r'signalStrength:\s*(\d+)', block)
        s["signalStrength"] = int(ss_m.group(1)) if ss_m else 0

        ks_m = re.search(r'keySignal:\s*"([^"]*)"', block)
        s["keySignal"] = ks_m.group(1) if ks_m else ""

        signals[name] = s

    return signals


def extract_trl_rankings(content):
    """Extract TRL_RANKINGS data."""
    rankings = {}
    match = re.search(r'const TRL_RANKINGS\s*=\s*\[(.*?)\];', content, re.DOTALL)
    if not match:
        return rankings

    text = match.group(1)
    # Find each entry: { company: "...", trl: N, note: "..." }
    entries = re.findall(
        r'\{\s*company:\s*"([^"]+)",\s*trl:\s*(\d+),\s*note:\s*"([^"]*)"',
        text
    )
    for name, trl, note in entries:
        rankings[name] = {"trl": int(trl), "note": note}

    return rankings


def compute_regulatory_moat(company, gov_contract, sector):
    """Compute regulatory moat score (0-10)."""
    base = SECTOR_REGULATORY_BASE.get(sector, 3)

    # Boost from clearance level
    if gov_contract:
        cl = gov_contract.get("clearanceLevel", "").lower()
        if "ts/sci" in cl:
            base = max(base, 8)
        elif "secret" in cl:
            base = max(base, 6)
        elif "confidential" in cl:
            base = max(base, 5)

    # Keyword boost from techApproach and tags
    search_text = " ".join([
        company.get("techApproach", ""),
        " ".join(company.get("tags", [])),
        company.get("description", ""),
    ])
    kw_boost = keyword_score(search_text, REGULATORY_KEYWORDS, base=0, cap=4)
    base = min(base + kw_boost // 2, 10)

    return base


def compute_switching_costs(company, iscore):
    """Compute switching costs score (0-10)."""
    search_text = " ".join([
        company.get("techApproach", ""),
        company.get("description", ""),
        company.get("insight", ""),
        company.get("bull", ""),
    ])

    base = keyword_score(search_text, SWITCHING_COST_KEYWORDS, base=0, cap=10)

    # Calibrate against editorial techMoat
    if iscore:
        tech_moat = iscore.get("techMoat", 5)
        # Blend: 60% keyword-based, 40% editorial calibration
        base = round(base * 0.6 + tech_moat * 0.4)

    return min(max(base, 1), 10)


def compute_manufacturing_readiness(company, trl_data, sector):
    """Compute manufacturing readiness (0-10). Distinct from TRL."""
    # TRL measures "does the tech work?" — manufacturing readiness measures
    # "can you produce it at scale?"
    if trl_data:
        trl = trl_data.get("trl", 5)
        # Manufacturing readiness typically lags TRL by 1-2 levels
        # but for production companies (TRL 8-9), they're close
        if trl >= 9:
            base = 8  # Proven production
        elif trl >= 8:
            base = 7  # Qualified production
        elif trl >= 7:
            base = 6  # Scaling
        elif trl >= 6:
            base = 5  # Pilot production
        elif trl >= 5:
            base = 4  # Pre-production
        else:
            base = max(trl - 1, 1)  # Lab stage
    else:
        base = 4  # Default if no TRL data

    # Software companies get a boost (no physical manufacturing needed)
    if sector in ["AI & Software"]:
        base = min(base + 2, 10)

    return base


def compute_data_advantage(company, patent, iscore, alt_data):
    """Compute data advantage score (0-10)."""
    search_text = " ".join([
        company.get("techApproach", ""),
        company.get("description", ""),
        company.get("insight", ""),
        " ".join(company.get("tags", [])),
    ])

    base = keyword_score(search_text, DATA_ADVANTAGE_KEYWORDS, base=0, cap=8)

    # IP boost
    if patent:
        ip_score = patent.get("ipMoatScore", 0)
        if ip_score >= 8:
            base = max(base, 7)
        elif ip_score >= 6:
            base = max(base, 5)

    # Patent velocity boost
    if patent and patent.get("velocityTrend") == "accelerating":
        base = min(base + 1, 10)

    return min(max(base, 1), 10)


def compute_supply_chain(company, sector):
    """Compute supply chain control score (0-10)."""
    search_text = " ".join([
        company.get("techApproach", ""),
        company.get("description", ""),
        company.get("insight", ""),
        company.get("bull", ""),
    ])

    base = keyword_score(search_text, SUPPLY_CHAIN_KEYWORDS, base=0, cap=10)

    # Sector adjustments
    if sector in ["Defense & Security", "Space & Aerospace", "Nuclear Energy"]:
        base = max(base, 4)  # Strategic sectors have inherent supply chain importance

    return min(max(base, 1), 10)


def compute_talent_density(company, alt_data, iscore):
    """Compute talent density score (0-10)."""
    base = 4  # default

    if alt_data:
        hv = alt_data.get("hiringVelocity", "")
        ss = alt_data.get("signalStrength", 0)

        if hv == "surging":
            base = 9
        elif hv == "growing":
            base = 7
        elif hv == "stable":
            base = 5
        elif hv == "slowing":
            base = 3

        # Headcount as modifier
        hc = alt_data.get("headcountEstimate", "")
        try:
            hc_num = int(re.sub(r'[^\d]', '', hc.split('+')[0].replace(',', '')))
            if hc_num >= 5000:
                base = min(base + 1, 10)
        except (ValueError, IndexError):
            pass

    # Calibrate with team pedigree from INNOVATOR_SCORES
    if iscore:
        tp = iscore.get("teamPedigree", 5)
        base = round(base * 0.6 + tp * 0.4)

    return min(max(base, 1), 10)


def compute_moat_depth(dimensions):
    """Compute overall moat depth (0-100) from dimension scores."""
    total = 0
    for dim, weight in WEIGHTS.items():
        score = dimensions.get(dim, {}).get("score", 0)
        total += score * weight
    # Scale from 0-10 to 0-100
    return round(total * (100 / 10))


def classify_moat_type(dimensions):
    """Classify the primary moat type."""
    for check_fn, moat_type in MOAT_TYPE_RULES:
        if check_fn(dimensions):
            return moat_type
    return "platform"


def infer_moat_trend(company, iscore, alt_data, patent):
    """Infer whether the moat is strengthening, stable, or weakening."""
    strengthening_signals = 0
    weakening_signals = 0

    # Check momentum
    if iscore:
        momentum = iscore.get("momentum", 5)
        if momentum >= 8:
            strengthening_signals += 2
        elif momentum >= 6:
            strengthening_signals += 1
        elif momentum <= 3:
            weakening_signals += 2

    # Check signal
    signal = company.get("signal", "")
    if signal == "hot":
        strengthening_signals += 1
    elif signal == "declining":
        weakening_signals += 2

    # Check hiring velocity
    if alt_data:
        hv = alt_data.get("hiringVelocity", "")
        if hv == "surging":
            strengthening_signals += 1
        elif hv == "slowing":
            weakening_signals += 1

    # Check patent velocity
    if patent:
        vt = patent.get("velocityTrend", "")
        if vt == "accelerating":
            strengthening_signals += 1
        elif vt == "declining":
            weakening_signals += 1

    if strengthening_signals >= 3:
        return "strengthening"
    elif weakening_signals >= 2:
        return "weakening"
    else:
        return "stable"


def generate_evidence(dimension, company, gov_contract, patent, alt_data, trl_data):
    """Generate human-readable evidence string for a dimension."""
    name = company["name"]
    sector = company.get("sector", "")
    ta = company.get("techApproach", "")
    tags = company.get("tags", [])
    insight = company.get("insight", "")

    if dimension == "regulatoryMoat":
        parts = []
        if gov_contract:
            cl = gov_contract.get("clearanceLevel", "")
            if cl:
                parts.append(f"{cl} clearance programs")
            agencies = gov_contract.get("agencies", [])
            if agencies:
                top = agencies[:3]
                parts.append(f"contracts with {', '.join(top)}")
        if sector == "Nuclear Energy":
            parts.append("NRC regulatory framework")
        if sector == "Space & Aerospace":
            parts.append("FAA/ITAR export controls")
        if any(t.lower() in ["itar", "classified", "defense"] for t in tags):
            if "ITAR-controlled" not in " ".join(parts):
                parts.append("ITAR-controlled technology")
        if not parts:
            parts.append(f"{sector} regulatory environment")
        return "; ".join(parts[:3])

    elif dimension == "switchingCosts":
        parts = []
        ta_lower = ta.lower()
        if "platform" in ta_lower or "os" in ta_lower:
            parts.append("Platform deeply embedded in customer workflows")
        if "integration" in ta_lower or "integrated" in ta_lower:
            parts.append("Integrated stack increases migration costs")
        if "ecosystem" in ta_lower:
            parts.append("Ecosystem lock-in with third-party integrations")
        if gov_contract:
            parts.append("Recertification costs for gov customers prohibitive")
        if not parts:
            if insight:
                # Extract first clause from insight
                first_clause = insight.split(".")[0][:80]
                parts.append(first_clause)
            else:
                parts.append("Technical differentiation creates switching barriers")
        return "; ".join(parts[:2])

    elif dimension == "manufacturingReadiness":
        parts = []
        if trl_data:
            trl = trl_data["trl"]
            if trl >= 9:
                parts.append("Full production at commercial scale")
            elif trl >= 8:
                parts.append("Qualified production systems")
            elif trl >= 7:
                parts.append("Production prototypes in operational testing")
            elif trl >= 6:
                parts.append("Pilot production demonstrated")
            else:
                parts.append(f"TRL {trl} - pre-production development")
        ta_lower = ta.lower()
        if "factory" in ta_lower or "manufacturing" in ta_lower:
            parts.append("Dedicated manufacturing facilities")
        if "3d print" in ta_lower or "additive" in ta_lower:
            parts.append("Additive manufacturing capability")
        if not parts:
            parts.append("Manufacturing readiness developing")
        return "; ".join(parts[:2])

    elif dimension == "dataAdvantage":
        parts = []
        ta_lower = ta.lower()
        if "data" in ta_lower or "ai" in ta_lower or "ml" in ta_lower:
            parts.append("AI/ML systems generating proprietary training data")
        if "sensor" in ta_lower:
            parts.append("Deployed sensors accumulating operational data")
        if patent:
            if patent.get("totalPatents", 0) > 100:
                parts.append(f"{patent['totalPatents']}+ patents protecting IP")
        if "model" in ta_lower or "foundation" in ta_lower:
            parts.append("Proprietary model weights and training pipeline")
        if not parts:
            parts.append("Building proprietary technical knowledge base")
        return "; ".join(parts[:2])

    elif dimension == "supplyChainControl":
        parts = []
        ta_lower = ta.lower()
        if "vertical" in ta_lower:
            parts.append("Vertically integrated design and production")
        if "in-house" in ta_lower or "proprietary" in ta_lower:
            parts.append("In-house component development")
        if sector == "Nuclear Energy":
            parts.append("Critical nuclear fuel supply position")
        if sector == "Space & Aerospace":
            parts.append("Launch vehicle manufacturing control")
        if not parts:
            parts.append("Developing supply chain capabilities")
        return "; ".join(parts[:2])

    elif dimension == "talentDensity":
        parts = []
        if alt_data:
            hv = alt_data.get("hiringVelocity", "")
            hc = alt_data.get("headcountEstimate", "")
            if hv == "surging":
                parts.append(f"Aggressively hiring ({hc} employees)")
            elif hv == "growing":
                parts.append(f"Growing team ({hc} employees)")
            elif hc:
                parts.append(f"Team of {hc}")
        ta_lower = ta.lower()
        founder = company.get("description", "")
        if "phd" in founder.lower() or "mit" in founder.lower() or "stanford" in founder.lower():
            parts.append("Elite academic pedigree")
        if not parts:
            parts.append("Building specialized technical team")
        return "; ".join(parts[:2])

    return "Evidence pending"


def generate_narrative(company, iscore, dimensions, moat_type):
    """Generate a moat narrative from existing data."""
    name = company["name"]
    insight = company.get("insight", "")
    bull = company.get("bull", "")
    note = iscore.get("note", "") if iscore else ""

    # Build narrative from available text sources
    if insight:
        # Use first 1-2 sentences of insight
        sentences = insight.split(".")
        core = ". ".join(s.strip() for s in sentences[:2] if s.strip()) + "."
    elif note:
        core = note
    elif bull:
        sentences = bull.split(".")
        core = ". ".join(s.strip() for s in sentences[:2] if s.strip()) + "."
    else:
        core = f"{name} is building technical differentiation in its sector."

    # Add moat type context
    type_context = {
        "regulatory-platform": "This creates a dual moat: regulatory barriers prevent new entrants while platform lock-in retains existing customers.",
        "regulatory": "Regulatory barriers create significant entry costs for potential competitors.",
        "platform": "Platform effects create increasing switching costs as adoption deepens.",
        "ip-data": "IP protection and proprietary data create compounding advantages over time.",
        "manufacturing": "Manufacturing scale and know-how create cost advantages difficult to replicate.",
        "network": "Network effects strengthen the moat as the user base grows.",
        "talent": "Concentrated domain expertise creates a knowledge moat competitors struggle to match.",
    }

    suffix = type_context.get(moat_type, "")

    # Don't let narrative exceed ~300 chars
    if len(core) > 250:
        core = core[:247] + "..."

    return f"{core} {suffix}".strip()


def generate_milestone(company, trl_data):
    """Generate key milestone from recent events or TRL data."""
    event = company.get("recentEvent", "")
    if event:
        return event[:150]

    if trl_data:
        trl = trl_data["trl"]
        note = trl_data.get("note", "")
        if trl <= 6:
            return f"Advancing from TRL {trl} to TRL {trl + 1}: {note}"
        elif trl <= 8:
            return f"Scaling production: {note}"
        else:
            return f"Operational at scale: {note}"

    return None


def generate_scale_path(company, iscore):
    """Generate scale path from thesis bull case."""
    bull = company.get("bull", "")
    if bull:
        # Take first sentence of bull case
        first = bull.split(".")[0].strip()
        if len(first) > 150:
            first = first[:147] + "..."
        return first

    note = iscore.get("note", "") if iscore else ""
    if note:
        return note[:150]

    return None


def main():
    print("=" * 60)
    print("Technical Moat Breakdown Generator")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Read data.js
    print(f"\nReading {DATA_JS}...")
    content = DATA_JS.read_text()
    print(f"  File size: {len(content):,} bytes")

    # Extract all data arrays
    print("\nExtracting data arrays...")
    companies = extract_companies_data(content)
    print(f"  COMPANIES: {len(companies)} entries")

    iscores = extract_innovator_scores(content)
    print(f"  INNOVATOR_SCORES: {len(iscores)} entries")

    gov_contracts = extract_gov_contracts(content)
    print(f"  GOV_CONTRACTS: {len(gov_contracts)} entries")

    patents = extract_patent_intel(content)
    print(f"  PATENT_INTEL: {len(patents)} entries")

    alt_data = extract_alt_data(content)
    print(f"  ALT_DATA_SIGNALS: {len(alt_data)} entries")

    trl = extract_trl_rankings(content)
    print(f"  TRL_RANKINGS: {len(trl)} entries")

    # Generate moat profiles for INNOVATOR_SCORES companies
    print(f"\nGenerating moat profiles for {len(iscores)} companies...")
    profiles = []

    for company_name, iscore in iscores.items():
        company = companies.get(company_name, {"name": company_name})
        sector = company.get("sector", "")
        gc = gov_contracts.get(company_name)
        pat = patents.get(company_name)
        ad = alt_data.get(company_name)
        trl_data = trl.get(company_name)

        # Compute each dimension
        reg_score = compute_regulatory_moat(company, gc, sector)
        sw_score = compute_switching_costs(company, iscore)
        mfg_score = compute_manufacturing_readiness(company, trl_data, sector)
        data_score = compute_data_advantage(company, pat, iscore, ad)
        sc_score = compute_supply_chain(company, sector)
        talent_score = compute_talent_density(company, ad, iscore)

        dimensions = {
            "regulatoryMoat": {
                "score": reg_score,
                "label": get_label("regulatoryMoat", reg_score),
                "evidence": generate_evidence("regulatoryMoat", company, gc, pat, ad, trl_data),
            },
            "switchingCosts": {
                "score": sw_score,
                "label": get_label("switchingCosts", sw_score),
                "evidence": generate_evidence("switchingCosts", company, gc, pat, ad, trl_data),
            },
            "manufacturingReadiness": {
                "score": mfg_score,
                "label": get_label("manufacturingReadiness", mfg_score),
                "evidence": generate_evidence("manufacturingReadiness", company, gc, pat, ad, trl_data),
            },
            "dataAdvantage": {
                "score": data_score,
                "label": get_label("dataAdvantage", data_score),
                "evidence": generate_evidence("dataAdvantage", company, gc, pat, ad, trl_data),
            },
            "supplyChainControl": {
                "score": sc_score,
                "label": get_label("supplyChainControl", sc_score),
                "evidence": generate_evidence("supplyChainControl", company, gc, pat, ad, trl_data),
            },
            "talentDensity": {
                "score": talent_score,
                "label": get_label("talentDensity", talent_score),
                "evidence": generate_evidence("talentDensity", company, gc, pat, ad, trl_data),
            },
        }

        moat_depth = compute_moat_depth(dimensions)
        primary_type = classify_moat_type(dimensions)
        trend = infer_moat_trend(company, iscore, ad, pat)
        narrative = generate_narrative(company, iscore, dimensions, primary_type)
        milestone = generate_milestone(company, trl_data)
        scale_path = generate_scale_path(company, iscore)

        profile = {
            "company": company_name,
            "moatDepth": moat_depth,
            "primaryMoatType": primary_type,
            "moatTrend": trend,
            "dimensions": dimensions,
            "moatNarrative": narrative,
        }

        if milestone:
            profile["keyMilestone"] = milestone
        if scale_path:
            profile["scalePath"] = scale_path

        profiles.append(profile)

    # Sort by moatDepth descending
    profiles.sort(key=lambda p: p["moatDepth"], reverse=True)

    # Generate output
    print(f"\nGenerating output...")
    OUTPUT_JS.parent.mkdir(parents=True, exist_ok=True)

    js_content = f"// Technical Moat Breakdown — Auto-generated {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    js_content += f"// {len(profiles)} company moat profiles\n"
    js_content += f"// Cross-referenced from INNOVATOR_SCORES, PATENT_INTEL, GOV_CONTRACTS, ALT_DATA_SIGNALS, TRL_RANKINGS\n\n"
    js_content += f"const MOAT_PROFILES = {json.dumps(profiles, indent=2)};\n"

    with open(OUTPUT_JS, "w") as f:
        f.write(js_content)

    print(f"  Saved {len(profiles)} profiles to {OUTPUT_JS}")
    print(f"  File size: {OUTPUT_JS.stat().st_size:,} bytes")

    # Validate
    bracket_open = js_content.count("[")
    bracket_close = js_content.count("]")
    brace_open = js_content.count("{")
    brace_close = js_content.count("}")
    print(f"\n  Brackets: [ {bracket_open} / ] {bracket_close}")
    print(f"  Braces:   {{ {brace_open} / }} {brace_close}")
    assert bracket_open == bracket_close, "Bracket mismatch!"
    assert brace_open == brace_close, "Brace mismatch!"

    # Summary
    print(f"\nTop 10 by Moat Depth:")
    for p in profiles[:10]:
        print(f"  {p['moatDepth']:3d} | {p['primaryMoatType']:<20s} | {p['moatTrend']:<13s} | {p['company']}")

    print(f"\nMoat Type Distribution:")
    type_counts = {}
    for p in profiles:
        t = p["primaryMoatType"]
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    print(f"\nTrend Distribution:")
    trend_counts = {}
    for p in profiles:
        t = p["moatTrend"]
        trend_counts[t] = trend_counts.get(t, 0) + 1
    for t, c in sorted(trend_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()
