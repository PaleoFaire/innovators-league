#!/usr/bin/env python3
"""
Compute investor intelligence: VC × thesis-cluster concentration, cluster
specialists, momentum (recent additions), and pedigree extraction from
founders.

Reads:
  data.js — COMPANIES (investors[], thesisCluster, founder, founded, addedDate)
            VC_FIRMS (canonical names + portfolioCompanies)

Writes:
  data/investor_intelligence.json
    {
      "generatedAt": ISO,
      "concentration": {
        "<VC name>": {
          "<cluster>": { "count": N, "companies": [...] }
        }
      },
      "specialists": {
        "<cluster>": [
          { "vc": "<name>", "count": N, "share": 0.30 }, ...
        ]
      },
      "momentum": [
        { "vc": "<name>", "recentCount": N, "totalCount": N, "score": 0.X },
        ...
      ],
      "pedigree": {
        "<founder origin company>": [
          { "founderName": "...", "foundedCo": "...", "foundedYear": 2024 }, ...
        ]
      }
    }

Usage:
  python scripts/compute_investor_intelligence.py
"""
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

sys.path.insert(0, str(ROOT / "scripts"))
from verify_company_facts import parse_companies
from verify_investor_facts import parse_vc_firms
from derive_investor_portfolios import canonical_name


# Pedigree-source companies (well-known origin points for founders).
# Detected in COMPANIES founder bios and descriptions.
PEDIGREE_SOURCES = [
    "SpaceX", "Tesla", "Apple", "Google", "Meta", "Facebook", "OpenAI",
    "Anthropic", "Palantir", "Stripe", "Uber", "Airbnb", "Netflix",
    "Amazon", "Microsoft", "DeepMind", "Google Brain", "FAIR",
    "Lockheed Martin", "Boeing", "Raytheon", "Northrop Grumman",
    "JPL", "NASA", "DARPA", "ARPA-E",
    "MIT", "Stanford", "Caltech", "CMU", "Berkeley",
    "Y Combinator", "Thiel Fellow",
]


def load_companies_full():
    """parse_companies doesn't return all fields — re-parse to get addedDate."""
    src = (ROOT / "data.js").read_text(encoding="utf-8")
    m = re.search(r'const COMPANIES\s*=\s*\[', src)
    start = m.end() - 1
    depth = 0; in_str = False; str_q = None
    for i in range(start, len(src)):
        c = src[i]
        if in_str:
            if c == "\\": continue
            if c == str_q: in_str = False
        else:
            if c in ('"', "'", "`"):
                in_str = True; str_q = c
            elif c == "[": depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    block = src[start:i+1]; break

    cos = []
    obj_depth = 0; obj_start = None; in_str = False; str_q = None
    for i, c in enumerate(block):
        if in_str:
            if c == "\\": continue
            if c == str_q: in_str = False
        else:
            if c in ('"', "'", "`"):
                in_str = True; str_q = c
            elif c == "{":
                if obj_depth == 0: obj_start = i
                obj_depth += 1
            elif c == "}":
                obj_depth -= 1
                if obj_depth == 0 and obj_start is not None:
                    obj = block[obj_start:i+1]
                    def grab(field):
                        mm = re.search(rf'\b{field}\s*:\s*"((?:[^"\\]|\\.)*)"', obj)
                        return mm.group(1) if mm else None
                    def grab_arr(field):
                        mm = re.search(rf'\b{field}\s*:\s*\[((?:[^\[\]"]*|"(?:[^"\\]|\\.)*")*)\]', obj)
                        return re.findall(r'"((?:[^"\\]|\\.)*)"', mm.group(1)) if mm else []
                    cos.append({
                        'name': grab('name'),
                        'sector': grab('sector'),
                        'description': grab('description') or '',
                        'founder': grab('founder') or '',
                        'thesisCluster': grab('thesisCluster'),
                        'addedDate': grab('addedDate'),
                        'investors': grab_arr('investors'),
                    })
                    obj_start = None
    return cos


def main():
    companies = load_companies_full()
    firms = parse_vc_firms()
    canonical_set = {f["name"] for f in firms if f.get("name")}
    short_to_canonical = {f["shortName"]: f["name"] for f in firms if f.get("shortName")}

    print(f"  Companies loaded: {len(companies)}")
    print(f"  VC firms loaded:  {len(firms)}")

    # ── 1. CONCENTRATION MATRIX ───────────────────────────────────────────
    # For each VC, count companies per thesis cluster.
    # Build via reverse-index from COMPANIES.investors[] using canonical_name.
    concentration = defaultdict(lambda: defaultdict(lambda: {"count": 0, "companies": []}))
    for co in companies:
        cluster = co.get("thesisCluster")
        if not cluster: continue
        for raw_inv in (co.get("investors") or []):
            canon = canonical_name(raw_inv, canonical_set)
            if not canon: continue
            cell = concentration[canon][cluster]
            cell["count"] += 1
            cell["companies"].append(co["name"])

    # ── 2. CLUSTER SPECIALISTS ────────────────────────────────────────────
    # For each thesis cluster, rank VCs by # investments.
    specialists = defaultdict(list)
    cluster_totals = defaultdict(int)
    for vc, clusters in concentration.items():
        for cluster, data in clusters.items():
            cluster_totals[cluster] += data["count"]
    for vc, clusters in concentration.items():
        for cluster, data in clusters.items():
            share = data["count"] / cluster_totals[cluster] if cluster_totals[cluster] else 0
            specialists[cluster].append({
                "vc": vc,
                "count": data["count"],
                "share": round(share, 4),
            })
    # Keep top 5 per cluster
    for cluster in specialists:
        specialists[cluster].sort(key=lambda x: -x["count"])
        specialists[cluster] = specialists[cluster][:5]

    # ── 3. MOMENTUM ───────────────────────────────────────────────────────
    # "Recent" = addedDate >= 2026-01.
    # Score = recent / total ratio, weighted by total to avoid one-hit wonders.
    now = datetime.now(timezone.utc)
    cutoff_date = "2026-01"
    momentum = []
    for vc, clusters in concentration.items():
        total_cos = sum(c["count"] for c in clusters.values())
        recent = 0
        recent_examples = []
        for cluster, data in clusters.items():
            for cname in data["companies"]:
                co = next((c for c in companies if c["name"] == cname), None)
                if co and co.get("addedDate") and co["addedDate"] >= cutoff_date:
                    recent += 1
                    recent_examples.append({"company": cname, "cluster": cluster, "addedDate": co["addedDate"]})
        # Score: recent count weighted by sqrt of total to prefer active firms with size
        import math
        score = (recent ** 0.6) * math.log(1 + total_cos) if total_cos > 0 else 0
        momentum.append({
            "vc": vc,
            "recentCount": recent,
            "totalCount": total_cos,
            "score": round(score, 3),
            "topCluster": max(clusters.items(), key=lambda kv: kv[1]["count"])[0] if clusters else None,
            "recentExamples": sorted(recent_examples, key=lambda x: x["addedDate"], reverse=True)[:5],
        })
    momentum.sort(key=lambda x: -x["score"])

    # ── 4. PEDIGREE EXTRACTION ───────────────────────────────────────────
    # Look for "ex-X" or "former X" or "X alumnus" patterns in company descriptions.
    pedigree = defaultdict(list)
    pedigree_patterns = []
    for source in PEDIGREE_SOURCES:
        # Match: "ex-X", "former X", "X alumnus", "from X", "previously at X"
        escaped = re.escape(source)
        pat = rf'\b(?:ex-|former|formerly\s+at\s+|previously\s+at\s+|from\s+|veteran\s+of\s+|alum(?:ni|nus)?\s+(?:of\s+)?){escaped}\b'
        pedigree_patterns.append((source, re.compile(pat, re.IGNORECASE)))

    for co in companies:
        co_name = co["name"]
        text = (co.get("description") or "") + " " + (co.get("founder") or "")
        for source, pat in pedigree_patterns:
            if pat.search(text):
                pedigree[source].append({
                    "company": co_name,
                    "cluster": co.get("thesisCluster"),
                    "founder": co.get("founder"),
                })

    # ── 5. CLUSTER STATS ─────────────────────────────────────────────────
    # Helpful summary: top clusters by total tracked-VC investment count
    cluster_rank = sorted(cluster_totals.items(), key=lambda x: -x[1])[:30]

    # Convert to plain dicts for JSON
    out = {
        "generatedAt": now.isoformat(timespec="seconds"),
        "stats": {
            "companies": len(companies),
            "vcFirms": len(firms),
            "uniqueClusters": len(cluster_totals),
            "totalInvestments": sum(cluster_totals.values()),
        },
        "concentration": {
            vc: {cluster: dict(data) for cluster, data in clusters.items()}
            for vc, clusters in concentration.items()
        },
        "specialists": dict(specialists),
        "momentum": momentum,
        "pedigree": {k: v for k, v in pedigree.items() if v},
        "topClusters": [{"cluster": c, "investmentCount": n} for c, n in cluster_rank],
    }

    out_path = DATA / "investor_intelligence.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n✅ Wrote {out_path.relative_to(ROOT)}")
    print(f"   VCs with portfolios: {len(concentration)}")
    print(f"   Unique clusters:     {len(cluster_totals)}")
    print(f"   Total investments:   {sum(cluster_totals.values())}")
    print(f"   Pedigree origins:    {len(out['pedigree'])}")
    print()
    print("  Top 5 momentum (most active recently):")
    for m in momentum[:5]:
        print(f"    {m['vc']:<35} score={m['score']:>5.2f}  recent={m['recentCount']:>3}  total={m['totalCount']:>3}  → {m['topCluster']}")
    print()
    print("  Top clusters by total tracked-VC investments:")
    for cluster_name, count in cluster_rank[:6]:
        leader = specialists.get(cluster_name, [{"vc": "?"}])[0]
        print(f"    {cluster_name:<35} {count:>4} investments  · leader: {leader['vc']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
