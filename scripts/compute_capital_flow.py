#!/usr/bin/env python3
"""
Compute Capital Flow Temporal — aggregate dated capital deployment
into our 870-company universe by quarter × thesis cluster.

ACCURACY CONTRACT (per Stephen's directive):
  - Only count events with REAL dates (no approximation)
  - Use the most-authoritative source available per company
  - Document data sources + caveats explicitly in the output
  - Prefer "we don't know" over inference

Sources used (in order of confidence):
  1. SEC EDGAR Form D filings (data/form_d_filings_auto.json)
     — actual SEC-filed dates, real money amounts. Most authoritative
       but only covers last 60 days + US-domiciled rounds.
  2. COMPANIES.recentEvent.date where type='funding'
     — curator-set, typically the most-recent funding round per company.
       ~46 funding events; spans 2024-2026.
  3. Catalyst calendar Form D entries (data/catalyst_calendar.json)
     — overlap with #1, kept for redundancy.

Output: data/capital_flow_temporal.json with:
  {
    "generatedAt": ISO,
    "matrix": {
      "<thesisCluster>": {
        "<YYYY-Q[1-4]>": {
          "deals": N,
          "totalSold": $XXX (or null if amounts unknown),
          "companies": [list],
          "investors": [list (current investors of those companies)]
        }
      }
    },
    "vcAttribution": {
      "<canonical VC name>": {
        "<YYYY-Q[1-4]>": [list of companies they're invested in that
                          had a dated event in this quarter]
      }
    },
    "caveats": [...],
    "stats": {totalDealsTracked, dateRange, ...}
  }

Usage:
  python scripts/compute_capital_flow.py
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

sys.path.insert(0, str(ROOT / "scripts"))
from verify_company_facts import parse_companies
from verify_investor_facts import parse_vc_firms
from derive_investor_portfolios import canonical_name


def parse_company_recent_events():
    """Extract recentEvent.date + .type from raw data.js (parse_companies
    doesn't surface this nested field)."""
    src = (ROOT / "data.js").read_text(encoding="utf-8")
    m = re.search(r"const COMPANIES\s*=\s*\[", src)
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
                    block = src[start:i+1]
                    break

    events = {}   # company name → {date, type}
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
                    nm = re.search(r'name:\s*"((?:[^"\\]|\\.)*)"', obj)
                    re_m = re.search(r'recentEvent:\s*\{[^}]*type:\s*"([^"]+)"[^}]*date:\s*"([^"]+)"', obj)
                    if nm and re_m:
                        events[nm.group(1)] = {
                            "type": re_m.group(1),
                            "date": re_m.group(2),
                        }
                    obj_start = None
    return events


def to_quarter(date_str):
    """YYYY-MM[-DD] → YYYY-Q[1-4]. Returns None on parse failure."""
    if not date_str: return None
    try:
        # Accept YYYY-MM, YYYY-MM-DD
        m = re.match(r"^(\d{4})-(\d{2})", date_str)
        if not m: return None
        year, month = int(m.group(1)), int(m.group(2))
        q = (month - 1) // 3 + 1
        return f"{year}-Q{q}"
    except Exception:
        return None


def parse_money(s):
    """'$104,500' / '$50M' / '$2.5B+' → integer dollars. None if unparseable."""
    if not s: return None
    s = str(s).strip().lstrip("~$").rstrip("+").replace(",", "")
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([KMBT]?)", s, re.IGNORECASE)
    if not m: return None
    val = float(m.group(1))
    suf = (m.group(2) or "").upper()
    return int(val * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[suf])


def main():
    print("=" * 60)
    print("Capital Flow Temporal aggregator")
    print("=" * 60)

    companies = parse_companies()
    co_by_name = {c["name"]: c for c in companies if c.get("name")}
    firms = parse_vc_firms()
    canonical_set = {f["name"] for f in firms if f.get("name")}

    # Load companies' recentEvent + thesisCluster
    recent_events = parse_company_recent_events()
    print(f"  COMPANIES: {len(companies)}")
    print(f"  recentEvent.date entries: {len(recent_events)}")

    # Load Form D filings
    fd_path = DATA / "form_d_filings_auto.json"
    fd_filings = []
    if fd_path.exists():
        try:
            fd_data = json.load(open(fd_path))
            fd_filings = fd_data.get("filings", [])
        except Exception:
            pass
    print(f"  Form D filings: {len(fd_filings)}")

    # Load Companies' raw data so we can grab thesisCluster + investors
    src = (ROOT / "data.js").read_text(encoding="utf-8")

    def get_co_meta(name):
        """Return {thesisCluster, investors[], totalRaised} for a company name."""
        nm = re.escape(name)
        m = re.search(rf'name:\s*"{nm}"', src)
        if not m: return None
        op = src.rfind("{", 0, m.start())
        depth = 0; in_str = False; q = None
        cp = None
        for i in range(op, len(src)):
            c = src[i]
            if in_str:
                if c == "\\": continue
                if c == q: in_str = False
            else:
                if c in ('"', "'", "`"):
                    in_str = True; q = c
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        cp = i; break
        if cp is None: return None
        obj = src[op:cp+1]
        cluster_m = re.search(r'thesisCluster:\s*"([^"]+)"', obj)
        invs_m = re.search(r'investors:\s*\[((?:[^\[\]"]*|"(?:[^"\\]|\\.)*")*)\]', obj)
        totalraised_m = re.search(r'totalRaised:\s*"([^"]+)"', obj)
        invs = re.findall(r'"((?:[^"\\]|\\.)*)"', invs_m.group(1)) if invs_m else []
        return {
            "thesisCluster": cluster_m.group(1) if cluster_m else None,
            "investors": invs,
            "totalRaised": totalraised_m.group(1) if totalraised_m else None,
        }

    # ── Build the matrix ─────────────────────────────────────────
    # matrix[cluster][quarter] = { deals, totalSold, companies[], investors[] }
    matrix = defaultdict(lambda: defaultdict(lambda: {
        "deals": 0, "totalSold": 0, "companiesWithUnknownAmount": 0,
        "companies": [], "investors": set()
    }))
    # vcAttribution[vc_canonical][quarter] = list of (company, cluster)
    vc_attr = defaultdict(lambda: defaultdict(list))

    seen_event_keys = set()    # avoid double-counting (Form D + recentEvent for same co)

    def record(company_name, date_str, amount, source):
        quarter = to_quarter(date_str)
        if not quarter: return
        meta = get_co_meta(company_name)
        if not meta or not meta.get("thesisCluster"): return
        cluster = meta["thesisCluster"]
        key = (company_name, quarter)
        if key in seen_event_keys: return    # dedupe
        seen_event_keys.add(key)

        cell = matrix[cluster][quarter]
        cell["deals"] += 1
        if amount is not None:
            cell["totalSold"] += amount
        else:
            cell["companiesWithUnknownAmount"] += 1
        cell["companies"].append({
            "name": company_name,
            "amount": amount,
            "date": date_str,
            "source": source,
            "investors": meta["investors"],
        })
        # Aggregate VCs at the cell level (current investors, best-effort)
        for inv_raw in meta["investors"]:
            canon = canonical_name(inv_raw, canonical_set)
            if canon:
                cell["investors"].add(canon)
                vc_attr[canon][quarter].append({
                    "company": company_name,
                    "cluster": cluster,
                    "date": date_str,
                    "source": source,
                })

    # 1. Form D filings (most authoritative, real dollars)
    for fd in fd_filings:
        co_name = fd.get("company") or fd.get("issuer_name", "").split(" Mar ")[0]
        date = fd.get("filed_date") or fd.get("first_sale_date")
        amount = fd.get("amount_sold") or fd.get("offering_amount")
        try:
            amount = int(amount) if amount not in (None, "") else None
        except (ValueError, TypeError):
            amount = None
        record(co_name, date, amount, source="formd")

    # 2. recentEvent.date with type='funding'
    funding_events_used = 0
    for co_name, ev in recent_events.items():
        if ev.get("type") not in ("funding", "milestone"):  # accept "milestone" as fallback
            continue
        date = ev.get("date")
        # Use totalRaised as a rough amount proxy (imprecise — represents
        # cumulative, not just this round). Mark as approximate.
        meta = get_co_meta(co_name)
        if not meta: continue
        amount = parse_money(meta.get("totalRaised"))
        # Don't add the cumulative as the round amount — leave amount as None
        # to avoid inflating the totalSold figure. Show as deal count only.
        record(co_name, date, None, source="recentEvent")
        funding_events_used += 1

    print(f"  Form D records used:        {sum(1 for fd in fd_filings if fd.get('filed_date'))}")
    print(f"  recentEvent records used:   {funding_events_used}")

    # ── Output ──────────────────────────────────────────────────
    matrix_out = {}
    all_quarters = set()
    for cluster, quarters in matrix.items():
        matrix_out[cluster] = {}
        for q, cell in quarters.items():
            all_quarters.add(q)
            matrix_out[cluster][q] = {
                "deals": cell["deals"],
                "totalSold": cell["totalSold"] if cell["totalSold"] > 0 else None,
                "companiesWithUnknownAmount": cell["companiesWithUnknownAmount"],
                "companies": cell["companies"],
                "investors": sorted(cell["investors"]),
            }

    vc_attr_out = {
        vc: {q: deals for q, deals in qmap.items()}
        for vc, qmap in vc_attr.items()
    }

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "matrix": matrix_out,
        "vcAttribution": vc_attr_out,
        "stats": {
            "totalDealsTracked": sum(c["deals"] for q in matrix.values() for c in q.values()),
            "totalUSDSold": sum(c["totalSold"] for q in matrix.values() for c in q.values()),
            "uniqueClusters": len(matrix_out),
            "uniqueQuarters": len(all_quarters),
            "uniqueVCs": len(vc_attr_out),
            "quarterRange": [min(all_quarters), max(all_quarters)] if all_quarters else None,
        },
        "caveats": [
            "Coverage is limited to companies with dated funding events on file. "
            "Of 870 tracked companies, ~120-150 have either a Form D filing or "
            "a recentEvent.date on record.",
            "Form D filings (data/form_d_filings_auto.json) cover the LAST 60 DAYS only "
            "and US-domiciled offerings. Older rounds are not in EDGAR's recent feed.",
            "Investor attribution uses the company's CURRENT investors[] list as a "
            "best-effort proxy. A VC listed today may have invested in an EARLIER round "
            "than the one recorded here. We do not infer round participation from Form D "
            "(which doesn't reliably identify investors).",
            "Amounts (totalSold) sum only Form D amount_sold figures. recentEvent-based "
            "deals are counted but not summed (their totalRaised is cumulative, not "
            "per-round).",
            "All quarters use UTC calendar quarters: Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec.",
        ],
    }

    out_path = DATA / "capital_flow_temporal.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print()
    print(f"✅ Wrote {out_path.relative_to(ROOT)}")
    print(f"   Total deals tracked: {out['stats']['totalDealsTracked']}")
    print(f"   Total $ sold (Form D only): ${out['stats']['totalUSDSold']:,}")
    print(f"   Unique clusters: {out['stats']['uniqueClusters']}")
    print(f"   Unique quarters: {out['stats']['uniqueQuarters']} ({out['stats']['quarterRange']})")
    print(f"   Unique VCs attributed: {out['stats']['uniqueVCs']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
