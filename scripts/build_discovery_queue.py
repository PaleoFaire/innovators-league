#!/usr/bin/env python3
"""
Discovery Queue Aggregator.

Combines three signal sources to surface candidate frontier-tech companies
that should be added to the ROS database:

  1. SEC Form D filings    (data/form_d_filings_auto.json)
       — Filed within 15 days of any private fundraise. Strong signal.
       — Filter: company NOT in COMPANIES, optionally with frontier-tech
         investor lead.

  2. VC portfolio diffs    (data/vc_portfolio_changes.json)
       — Weekly diff of 16 elite VC portfolio pages (a16z, Founders Fund,
         Lux, Sequoia, etc.). New entries = high-conviction signal.

  3. Newsletter mentions   (data/newsletter_signals_auto.json)
       — RSS pull from 8 elite frontier-tech newsletters with NER-lite
         company name extraction. Lower precision; corroborating signal only.

Scoring:
  - VC portfolio additions: +30 (most reliable — VC has skin in game)
  - Form D filing >$5M:     +25 (real fundraise, real company)
  - Newsletter mention:     +5 per mention, +10 if multi-source
  - Multi-source bonus:     +20 if 2+ sources agree on same company

Output: data/discovery_queue_auto.json
        data/discovery_queue_auto.js (script-tag loadable for the review UI)
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"

OUT_JSON = DATA_DIR / "discovery_queue_auto.json"
OUT_JS = DATA_DIR / "discovery_queue_auto.js"

# Frontier-tech VC firms whose Form D filings as lead = high signal.
# Extracted from VC_FIRMS const + augmented.
FRONTIER_TECH_VCS = {
    "a16z", "andreessen horowitz", "andreessen", "horowitz",
    "founders fund", "founders fnd", "founders f.",
    "lux capital", "lux",
    "khosla", "khosla ventures",
    "8vc", "eight vc",
    "shield capital",
    "dcvc", "data collective",
    "eclipse ventures", "eclipse",
    "general catalyst", "gc",
    "av", "anduril ventures",
    "lower carbon",
    "cantos", "cantos ventures",
    "harpoon",
    "bedrock",
    "founders fund", "founders fnd",
    "sequoia", "sequoia capital",
    "kleiner perkins",
    "bessemer", "bessemer venture",
    "first round",
    "thrive capital",
    "spark capital",
    "greylock",
    "index ventures",
    "lightspeed",
    "y combinator", "yc",
    "social capital",
    "playground global",
    "atomic", "atomic vc",
    "trousdale",
    "fusion fund",
    "riot ventures", "riot",
    "alumni ventures",
    "pillar vc", "pillar",
    "in-q-tel", "iqt",
    "decisive point",
    "razor's edge",
    "8090",
    "pritzker military",
}


def load_existing_companies():
    """Set of normalized name keys from data.js. Includes hyphen-stripped
    and space-stripped variants so 'X-Energy' matches 'X Energy' and
    'XEnergy'."""
    if not DATA_JS.exists():
        return set()
    src = DATA_JS.read_text(encoding="utf-8", errors="replace")
    names = set()
    for m in re.finditer(r'name:\s*"([^"]+)"', src):
        raw = m.group(1).strip()
        for v in name_variants(raw):
            names.add(v)
    return names


def is_known(candidate, known_set):
    """True if any variant of candidate is in known_set."""
    for v in name_variants(candidate):
        if v in known_set:
            return True
    return False


def normalize_name(s):
    """Lower-case, strip incorporated/inc/llc/corp suffixes, normalize
    hyphens/dots/spaces. So 'X-Energy', 'X Energy', 'X.Energy' all match
    the same key."""
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r'[,.]?\s+(inc|llc|ltd|limited|corp|corporation|incorporated|gmbh|co)\.?$', '', s)
    # Collapse all separators to single space
    s = re.sub(r'[\s\-_\.]+', ' ', s)
    return s.strip()


def name_variants(s):
    """Return all sensible match-keys for a candidate name to catch
    variations in the existing roster (Anduril vs Anduril Industries)."""
    norm = normalize_name(s)
    if not norm:
        return set()
    out = {norm}
    # Also try without spaces/separators
    out.add(re.sub(r'\s+', '', norm))
    return out


def parse_dollar(amount_str):
    """Convert '$2.5M', '500000' etc. to USD."""
    if not amount_str:
        return 0
    s = str(amount_str)
    if s.replace('.', '').replace(',', '').isdigit():
        return float(s.replace(',', ''))
    m = re.match(r'\$?\s*([\d,.]+)\s*([KMBT])?', s, re.I)
    if not m:
        return 0
    try:
        n = float(m.group(1).replace(',', ''))
    except ValueError:
        return 0
    u = (m.group(2) or '').upper()
    return n * {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}.get(u, 1)


def collect_form_d_signals(known):
    """Form D filings → candidate dicts."""
    fp = DATA_DIR / "form_d_filings_auto.json"
    if not fp.exists():
        return []
    raw = json.load(open(fp))
    filings = raw.get("filings", []) if isinstance(raw, dict) else raw
    out = []
    for f in filings:
        company = (f.get("company") or "").strip()
        if not company:
            continue
        if is_known(company, known):
            continue
        amt = parse_dollar(f.get("amount_sold") or f.get("offering_amount"))
        if amt < 1e6:
            continue
        out.append({
            "name": company,
            "source": "Form D filing",
            "sourceWeight": 25,
            "amount": amt,
            "amountFmt": fmt_amount(amt),
            "date": f.get("filed_date"),
            "verifyUrl": f.get("filing_url"),
            "issuerName": f.get("issuer_name"),
            "context": f"Form D filed {f.get('filed_date','?')}: {fmt_amount(amt)} raise (issuer: {f.get('issuer_name','?')})",
        })
    return out


def collect_vc_portfolio_signals(known):
    """VC portfolio diffs → candidate dicts."""
    fp = DATA_DIR / "vc_portfolio_changes.json"
    if not fp.exists():
        return []
    changes = json.load(open(fp))
    out = []
    for c in changes:
        company = (c.get("company") or "").strip()
        vc = (c.get("vc") or "").strip()
        if not company or not vc:
            continue
        if is_known(company, known):
            continue
        # Higher weight if added to a frontier-tech VC's portfolio
        weight = 35 if vc.lower() in FRONTIER_TECH_VCS else 18
        out.append({
            "name": company,
            "source": f"VC portfolio: {vc}",
            "sourceWeight": weight,
            "vc": vc,
            "date": c.get("detected_date"),
            "verifyUrl": c.get("source"),
            "context": f"Newly listed in {vc} portfolio on {c.get('detected_date','?')}",
        })
    return out


def collect_newsletter_signals(known):
    """Newsletter mentions → candidate dicts."""
    fp = DATA_DIR / "newsletter_signals_auto.json"
    if not fp.exists():
        return []
    raw = json.load(open(fp))
    candidates = raw.get("candidates", [])
    out = []
    for c in candidates:
        if is_known(c["name"], known):
            continue
        for sig in c.get("signals", []):
            out.append({
                "name": c["name"],
                "source": f"Newsletter: {sig.get('source','?')}",
                "sourceWeight": min(15, sig.get("score", 0)),
                "context": (sig.get("context") or "")[:200],
                "date": sig.get("articleDate"),
                "verifyUrl": sig.get("articleUrl"),
                "articleTitle": sig.get("articleTitle"),
            })
    return out


def fmt_amount(n):
    if not n:
        return "?"
    if n >= 1e9: return f"${n/1e9:.1f}B"
    if n >= 1e6: return f"${n/1e6:.1f}M"
    if n >= 1e3: return f"${n/1e3:.0f}K"
    return f"${n:,.0f}"


def main():
    print("=" * 64)
    print("Discovery Queue Aggregator · ROS Frontier-Tech Pipeline")
    print("=" * 64)

    known = load_existing_companies()
    print(f"  Loaded {len(known)} known company names from data.js")

    form_d = collect_form_d_signals(known)
    vc = collect_vc_portfolio_signals(known)
    news = collect_newsletter_signals(known)

    print(f"  Form D candidates:      {len(form_d)}")
    print(f"  VC portfolio additions: {len(vc)}")
    print(f"  Newsletter mentions:    {len(news)}")
    print()

    # Aggregate by normalized company name
    by_name = {}
    for sig in form_d + vc + news:
        key = normalize_name(sig["name"])
        if not key:
            continue
        if key not in by_name:
            by_name[key] = {
                "name": sig["name"],
                "score": 0,
                "signals": [],
                "sources": set(),
            }
        by_name[key]["signals"].append(sig)
        by_name[key]["sources"].add(sig["source"].split(":")[0])
        by_name[key]["score"] += sig["sourceWeight"]
        # Keep the longest variant of the name (e.g. "Anduril Industries" not "Anduril")
        if len(sig["name"]) > len(by_name[key]["name"]):
            by_name[key]["name"] = sig["name"]

    # Multi-source bonus + confidence label
    for entry in by_name.values():
        if len(entry["sources"]) >= 2:
            entry["score"] += 20
            entry["multiSource"] = True
        else:
            entry["multiSource"] = False
        entry["sources"] = sorted(entry["sources"])

        # Confidence labelling — drives UI sorting + filtering
        sources_set = set(entry["sources"])
        if entry["multiSource"]:
            entry["confidence"] = "high"
        elif "Form D filing" in sources_set or any(s.startswith("VC portfolio") for s in sources_set):
            entry["confidence"] = "high"
        elif entry["score"] >= 10:
            entry["confidence"] = "medium"
        else:
            entry["confidence"] = "low"

    # Sort by score
    candidates = sorted(by_name.values(), key=lambda x: -x["score"])

    # Suggest sector based on context (lightweight keyword classifier)
    SECTOR_HINTS = [
        ("Defense & Security", ["defense", "weapon", "military", "drone", "uas",
                                "tactical", "missile", "munition", "soldier",
                                "battlefield", "swarm", "counter-drone"]),
        ("Space & Aerospace", ["space", "satellite", "launch", "rocket", "orbit",
                              "spacecraft", "lunar", "mars", "aerospace"]),
        ("Nuclear Energy", ["nuclear", "smr", "reactor", "fission", "uranium"]),
        ("Fusion Energy", ["fusion", "tokamak", "stellarator", "plasma"]),
        ("AI & Compute", ["ai", "llm", "foundation model", "embodied", "agent",
                         "inference", "training", "neural"]),
        ("Robotics & Manufacturing", ["robot", "humanoid", "manipulator",
                                     "factory", "manufacturing", "additive",
                                     "3d printing"]),
        ("Quantum Computing", ["quantum", "qubit", "photonic", "neutral atom"]),
        ("Biotech & Health", ["biotech", "biology", "gene", "crispr", "mrna",
                             "therapy", "drug", "pharma", "clinical"]),
        ("Climate & Energy", ["geothermal", "carbon capture", "dac", "solar",
                             "battery", "lithium", "green steel", "hydrogen"]),
        ("Chips & Semiconductors", ["semiconductor", "asic", "fabless", "chip",
                                   "wafer", "photonic"]),
    ]
    for c in candidates:
        ctx = " ".join(s.get("context", "") for s in c["signals"]).lower()
        sector_scores = []
        for sector, kws in SECTOR_HINTS:
            score = sum(1 for kw in kws if kw in ctx)
            if score > 0:
                sector_scores.append((sector, score))
        sector_scores.sort(key=lambda x: -x[1])
        c["suggestedSector"] = sector_scores[0][0] if sector_scores else None

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "knownCompaniesCount": len(known),
        "summary": {
            "totalCandidates": len(candidates),
            "fromFormD": len(form_d),
            "fromVcPortfolios": len(vc),
            "fromNewsletters": len(news),
            "multiSource": sum(1 for c in candidates if c["multiSource"]),
        },
        "candidates": candidates,
    }

    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    js_payload = (
        f"// Auto-generated from {OUT_JSON.name}\n"
        f"// Last updated: {out['generatedAt']}\n"
        f"const DISCOVERY_QUEUE_AUTO = {json.dumps(out, indent=2, default=str)};\n"
        f"if (typeof window !== 'undefined') window.DISCOVERY_QUEUE_AUTO = DISCOVERY_QUEUE_AUTO;\n"
    )
    OUT_JS.write_text(js_payload)
    print(f"✅ Wrote {OUT_JSON.relative_to(ROOT)} ({len(candidates)} candidates)")
    print(f"✅ Wrote {OUT_JS.relative_to(ROOT)}")
    print()
    print("Top 15 discovery candidates (multi-source first):")
    multi = [c for c in candidates if c["multiSource"]]
    single = [c for c in candidates if not c["multiSource"]]
    for c in (multi + single)[:15]:
        marker = "🌟" if c["multiSource"] else "  "
        sector = f"  [{c['suggestedSector']}]" if c.get("suggestedSector") else ""
        sigs = "/".join(c["sources"])
        print(f"  {marker} [{c['score']:>5.0f}] {c['name']:<40} ({sigs}){sector}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
