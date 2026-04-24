#!/usr/bin/env python3
"""
Pipeline Watchdog — scans every auto.js / auto.json in data/ and flags:
  • DEAD pipelines (< 500 bytes, or empty const/list/dict)
  • STALE pipelines (last-updated > N days)
  • FRESH pipelines (OK)

Writes data/pipeline_health.json. Intended to run from every major
workflow so downstream jobs (and a footer badge on the site) always
have an up-to-the-minute picture of data freshness.

Usage:
  python scripts/pipeline_watchdog.py
  python scripts/pipeline_watchdog.py --fail-on-dead    # exit 1 if any dead
  python scripts/pipeline_watchdog.py --fail-on-stale   # exit 1 if any stale

Design:
  • Every pipeline has an expected refresh cadence (in PIPELINE_CADENCE
    below). If an output file is older than 2 × the cadence it's STALE.
  • Outputs < MIN_SIZE_BYTES are DEAD regardless of age.
  • Exits with code 0 by default (advisory) — flip the flags above to
    make CI actually fail on degradations, e.g. in a pre-deploy gate.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_PATH = DATA_DIR / "pipeline_health.json"
MIN_SIZE_BYTES = 500

# Expected max days between refreshes. 2 × this = staleness threshold.
# Pipelines missing from this map use a default of 14 days.
PIPELINE_CADENCE = {
    # ── Hourly / near-real-time ──
    "news_signals_auto.js":              1,
    "stocks_auto.js":                    1,
    "daily_digest.json":                 1,

    # ── Daily ──
    "sec_filings_auto.js":               2,
    "gov_contracts_auto.js":             2,
    "jobs_auto.js":                      1,
    "diffbot_enrichment_auto.js":        7,

    # ── Several times per week ──
    "arxiv_papers_auto.js":              3,
    "press_releases_auto.js":            2,
    "patent_intel_auto.js":              7,
    "federal_register_auto.js":          2,
    "nrc_licensing_auto.js":             3,
    "clinical_trials_auto.js":           3,
    "faa_certification_auto.js":         7,
    "congress_bills_auto.js":            3,
    "demand_signals_auto.js":            3,
    "sbir_topics_auto.js":               3,
    "sam_contracts_auto.js":             2,

    # ── Weekly ──
    "insider_transactions_auto.js":      7,
    "fda_actions_auto.js":               7,
    "github_releases_auto.js":           7,
    "product_launches_auto.js":          7,
    "headcount_estimates_auto.js":       7,
    "linkedin_headcount_auto.json":      7,
    "nasa_projects_auto.js":             7,
    "sbir_awards_auto.js":               7,
    "nih_grants_auto.js":                7,
    "arpa_e_projects_auto.js":           14,
    "nsf_awards_auto.js":                7,
    "doe_programs_auto.js":              14,
    "trade_data_auto.js":                7,
    "hackernews_buzz_auto.js":           3,
    "twitter_signals_auto.json":         3,

    # ── Round 7l outputs (weekly calcs) ──
    "field_notes_auto.js":               7,
    "budget_signals_auto.js":            7,
    "fund_intelligence_auto.js":         7,
    "ma_comps_auto.js":                  14,
    "founder_mafias_auto.js":            14,
    "network_graph_auto.js":             14,
    "contractor_readiness_auto.js":      7,
    "gov_demand_summary_auto.js":        7,
    "expert_takes_auto.js":              3,

    # ── Round 8: Crown-Jewel Intelligence Pipelines ──
    "interconnection_queue_auto.js":      7,  # FERC/ISO power queue
    "website_changes_auto.js":            7,  # Wayback CDX
    "youtube_mentions_auto.js":           7,  # YouTube captions
    "fcc_licenses_auto.js":               7,  # FCC ULS+ELS
    "h1b_lca_auto.js":                   30,  # DOL OFLC quarterly source
    "dsca_fms_auto.js":                   7,  # DSCA FMS notifications
    "lobbying_auto.js":                  30,  # Senate LDA quarterly

    # ── Round 9: Supply chain + regulatory depth + hedge fund skill ──
    "bill_of_lading_auto.js":             7,  # ImportYeti / CBP ACE
    "state_puct_dockets_auto.js":         7,  # State PUC filings
    "water_permits_auto.js":              7,  # EPA NPDES + state water
    "deception_scores_auto.js":           7,  # Earnings deception (skill)
}

# Human-readable labels for the site footer / admin dashboard
PIPELINE_LABEL = {
    "news_signals_auto.js":         "News Feed",
    "stocks_auto.js":               "Stock Prices",
    "daily_digest.json":            "Frontier Daily",
    "sec_filings_auto.js":          "SEC Filings",
    "gov_contracts_auto.js":        "Gov Contracts",
    "jobs_auto.js":                 "Jobs Feed",
    "arxiv_papers_auto.js":         "arXiv Papers",
    "press_releases_auto.js":       "Press Releases",
    "patent_intel_auto.js":         "Patent Intel",
    "federal_register_auto.js":     "Federal Register",
    "nrc_licensing_auto.js":        "NRC Licensing",
    "clinical_trials_auto.js":      "Clinical Trials",
    "faa_certification_auto.js":    "FAA Type Certs",
    "congress_bills_auto.js":       "Congress Bills",
    "demand_signals_auto.js":       "Demand Signals",
    "insider_transactions_auto.js": "Insider Trades",
    "fda_actions_auto.js":          "FDA Actions",
    "github_releases_auto.js":      "GitHub Releases",
    "product_launches_auto.js":     "Product Launches",
    "nasa_projects_auto.js":        "NASA Projects",
    "sbir_awards_auto.js":          "SBIR Awards",
    "sbir_topics_auto.js":          "SBIR Topics",
    "sam_contracts_auto.js":        "SAM.gov",
    "nih_grants_auto.js":           "NIH Grants",
    "arpa_e_projects_auto.js":      "ARPA-E",
    "nsf_awards_auto.js":           "NSF Awards",
    "doe_programs_auto.js":         "DOE Programs",
    "trade_data_auto.js":           "Trade Data",
    "hackernews_buzz_auto.js":      "HN Buzz",
    "twitter_signals_auto.json":    "X / Twitter Signals",
    "linkedin_headcount_auto.json": "LinkedIn Headcount",
    "diffbot_enrichment_auto.js":   "Diffbot Enrichment",
    "field_notes_auto.js":          "Field Notes",
    "budget_signals_auto.js":       "Budget Signals",
    "fund_intelligence_auto.js":    "Fund Intelligence",
    "ma_comps_auto.js":             "M&A Comps",
    "founder_mafias_auto.js":       "Founder Mafias",
    "network_graph_auto.js":        "Network Graph",
    "contractor_readiness_auto.js": "Contractor Readiness",
    "gov_demand_summary_auto.js":   "Gov Demand Summary",
    "expert_takes_auto.js":         "Expert Takes",

    # ── Round 8 crown-jewel pipelines ──
    "interconnection_queue_auto.js": "Power Grid (FERC/ISO)",
    "website_changes_auto.js":       "Website Changes (Wayback)",
    "youtube_mentions_auto.js":      "Corporate Mentions (YouTube)",
    "fcc_licenses_auto.js":          "FCC Licenses (ULS/ELS)",
    "h1b_lca_auto.js":               "H-1B LCA Hiring",
    "dsca_fms_auto.js":              "DSCA Arms Sales",
    "lobbying_auto.js":              "Senate Lobbying",

    # ── Round 9 pipelines ──
    "bill_of_lading_auto.js":        "Bill of Lading (Supply Chain)",
    "state_puct_dockets_auto.js":    "State PUC Dockets",
    "water_permits_auto.js":         "Water Permits",
    "deception_scores_auto.js":      "Deception Detector (Skill)",
}


def parse_last_updated(path):
    """Pull the Last-Updated timestamp from the header of an auto.js file
    (or `generated_at`/`_meta.generated_at` from a JSON file). Returns a
    tz-aware UTC datetime or None if we can't find one."""
    try:
        head = path.read_text(errors="ignore")[:2048]
    except Exception:
        return None

    # JS header comment: "// Last updated: 2026-04-23 08:00:00 UTC"
    m = re.search(r"Last updated:\s*(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}:\d{2}))?",
                  head)
    if m:
        date_part = m.group(1)
        time_part = m.group(2) or "00:00:00"
        try:
            return datetime.strptime(f"{date_part} {time_part}",
                                     "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    # JSON: try `generated_at` or `_meta.generated_at`
    if path.suffix == ".json":
        try:
            data = json.loads(path.read_text())
            ts = None
            if isinstance(data, dict):
                ts = data.get("generated_at")
                if not ts and isinstance(data.get("_meta"), dict):
                    ts = data["_meta"].get("generated_at")
            if ts:
                ts_norm = ts.rstrip("Z").split("+")[0].split(".")[0]
                try:
                    return datetime.strptime(ts_norm, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
                try:
                    return datetime.strptime(ts_norm, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
        except Exception:
            pass

    # Fallback: filesystem mtime
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except Exception:
        return None


def classify(path, min_size=MIN_SIZE_BYTES):
    """Return ('fresh'|'stale'|'dead', metadata dict)."""
    size = path.stat().st_size if path.exists() else 0
    name = path.name
    # Title-case a clean label when we don't have a hand-curated one in
    # PIPELINE_LABEL. Strip file extension and the "_auto" suffix, then
    # replace underscores with spaces.
    stem = name
    for ext in (".auto.js", ".auto.json", "_auto.js", "_auto.json", ".json", ".js"):
        if stem.endswith(ext):
            stem = stem[: -len(ext)]
            break
    label = PIPELINE_LABEL.get(name, stem.replace("_", " ").title())
    cadence_days = PIPELINE_CADENCE.get(name, 14)

    last_updated = parse_last_updated(path)
    now = datetime.now(tz=timezone.utc)
    age_hours = None
    if last_updated:
        age_hours = (now - last_updated).total_seconds() / 3600.0

    # DEAD: file smaller than threshold — script ran but produced no data
    if size < min_size:
        status = "dead"
    # STALE: > 2× cadence old
    elif age_hours is not None and age_hours > cadence_days * 2 * 24:
        status = "stale"
    else:
        status = "fresh"

    return status, {
        "file": name,
        "label": label,
        "status": status,
        "size_bytes": size,
        "cadence_days": cadence_days,
        "last_updated": last_updated.isoformat() if last_updated else None,
        "age_hours": round(age_hours, 1) if age_hours is not None else None,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fail-on-dead", action="store_true",
                    help="Exit non-zero if any pipeline is dead")
    ap.add_argument("--fail-on-stale", action="store_true",
                    help="Exit non-zero if any pipeline is stale (or dead)")
    args = ap.parse_args()

    if not DATA_DIR.exists():
        print(f"data/ not found at {DATA_DIR}", file=sys.stderr)
        sys.exit(2)

    fresh, stale, dead = [], [], []
    for path in sorted(DATA_DIR.iterdir()):
        if not (path.name.endswith("_auto.js") or path.name.endswith("_auto.json")
                or path.name == "daily_digest.json"):
            continue
        status, meta = classify(path)
        if status == "dead":
            dead.append(meta)
        elif status == "stale":
            stale.append(meta)
        else:
            fresh.append(meta)

    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "total": len(fresh) + len(stale) + len(dead),
        "fresh_count": len(fresh),
        "stale_count": len(stale),
        "dead_count": len(dead),
        "health_score": round(100 * len(fresh) / max(1, len(fresh) + len(stale) + len(dead)), 1),
        "fresh": fresh,
        "stale": stale,
        "dead": dead,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2))

    print(f"Pipeline Health — {payload['health_score']}%  "
          f"(fresh {payload['fresh_count']} / stale {payload['stale_count']} / dead {payload['dead_count']})")
    if stale:
        print("\nSTALE:")
        for p in stale:
            print(f"  {p['label']:28s}  {p['age_hours']:>6.0f}h old  (cadence {p['cadence_days']}d)")
    if dead:
        print("\nDEAD:")
        for p in dead:
            print(f"  {p['label']:28s}  {p['size_bytes']:>6d}b")
    print(f"\n→ wrote {OUT_PATH.name}")

    if args.fail_on_dead and dead:
        sys.exit(1)
    if args.fail_on_stale and (stale or dead):
        sys.exit(1)


if __name__ == "__main__":
    main()
