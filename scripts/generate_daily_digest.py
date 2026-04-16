#!/usr/bin/env python3
"""
Daily Frontier Tech Digest Generator

Produces data/daily_digest.json — a curated snapshot of today's most
important activity across frontier tech. Runs every hour via
hourly-news-sync.yml; front-end (brief.js) renders from the JSON.

Draws from:
  - deals_auto.json       → Biggest Deals
  - news_signals_auto.js  → Top News
  - sam_contracts_aggregated.json → Government Activity
  - stocks_auto.js        → Biggest Market Movers
  - patents_aggregated.json → New Patents
  - federal_register_auto.js → Regulatory Highlights
  - fda_actions_raw.json  → FDA Activity
"""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_json_safe(filename):
    p = DATA_DIR / filename
    if not p.exists():
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except Exception as e:
        print(f"  ! Failed to load {filename}: {e}")
        return None


def load_js_const(filename, const_name):
    """Extract a JS const array/object from a .js file."""
    p = DATA_DIR / filename
    if not p.exists():
        return None
    content = p.read_text()
    m = re.search(rf'const {const_name}\s*=\s*(\[[\s\S]*?\]|\{{[\s\S]*?\}});', content)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def parse_amount_to_usd(s):
    if not s or not isinstance(s, str):
        return 0
    s = s.replace("$", "").replace(",", "").replace("+", "").strip().upper()
    m = re.match(r'(\d+(?:\.\d+)?)\s*([TBMK]?)', s)
    if not m:
        return 0
    num = float(m.group(1))
    unit = m.group(2)
    mult = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}.get(unit, 1)
    return num * mult


def within_days(date_str, days):
    if not date_str:
        return False
    try:
        # Accept YYYY-MM, YYYY-MM-DD, ISO
        d = date_str[:10]
        if len(d) < 10:
            d = d + "-01"
        parsed = datetime.strptime(d, "%Y-%m-%d")
        return (datetime.now() - parsed).days <= days
    except Exception:
        return False


_PUBLIC_COMPANIES_CACHE = None

def _public_companies():
    """Load set of public company names from stocks_auto.js — these should
    NEVER appear in 'biggest deals' because they're already public."""
    global _PUBLIC_COMPANIES_CACHE
    if _PUBLIC_COMPANIES_CACHE is not None:
        return _PUBLIC_COMPANIES_CACHE
    stocks_path = DATA_DIR / "stocks_auto.js"
    names = set()
    if stocks_path.exists():
        content = stocks_path.read_text()
        for m in re.finditer(r'"company":\s*"([^"]+)"', content):
            names.add(m.group(1).strip().lower())
        for m in re.finditer(r'"ticker":\s*"([A-Z0-9.]+)"', content):
            names.add(m.group(1).strip().lower())
    # Always add well-known public companies that might not be in stocks_auto.js
    names.update({
        "palantir", "palantir technologies", "pltr",
        "nvidia", "nvda", "tesla", "tsla", "amd",
        "rocket lab", "rklb", "planet labs", "pl",
        "oklo", "ionq", "rigetti computing", "rgti",
        "joby aviation", "joby", "archer aviation", "achr",
        "rivian", "rivn", "ast spacemobile", "asts",
        "intuitive machines", "lunr", "recursion pharmaceuticals", "rxrx",
        "tempus ai", "tem", "aurora innovation", "aur",
        "astera labs", "alab", "quantumscape", "qs",
        "nuscale power", "smr", "nano nuclear energy", "nne",
        "solid power", "sldp", "vertical aerospace", "evtl",
        "c3.ai", "d-wave quantum", "qbts", "satellogic", "satl",
    })
    _PUBLIC_COMPANIES_CACHE = names
    return names


def _is_real_funding(company, headline, round_type, amount_raw):
    """Validate this is actually a funding round for the company — not a
    partnership, contract, market-cap mention, or misattributed headline.

    When headline exists: strict checks (company in title + funding verb + no reject signals).
    When no headline: only cap outlier amounts.
    """
    # Sanity cap — reject absurd amounts ($50B+) that are likely misparses
    # (very few real rounds exceed this; Anthropic $300B etc are noted exceptions
    # but usually paired with market/valuation not actual round)
    if amount_raw > 50e9:
        return False

    if not headline:
        # No headline to validate against — trust upstream (deals_auto)
        return True

    if not company:
        return False

    c = company.strip().lower()
    h = headline.lower()

    # Company must appear in headline — the source of truth for "who did this"
    first_word = c.split()[0] if c.split() else c
    if c not in h and (not first_word or len(first_word) < 4 or first_word not in h):
        return False

    # Reject partnership/contract/acquisition headlines
    reject = [
        "partnership", "partners with", "joins forces",
        "wins contract", "awarded", "contract win",
        "acquires", "acquisition of", "to acquire",
        "announces partnership",
    ]
    if any(r in h for r in reject):
        return False

    # Require a funding verb in the headline
    funding_verbs = [
        "raises", "raised", "secures", "secured",
        "closes", "closed", "lands", "landed",
        "bags", "scores", "nets",
        "series ", "seed round", "funding round",
        "valuation of", "valued at",
    ]
    if not any(v in h for v in funding_verbs):
        return False

    return True


def biggest_deals(days=30, limit=10):
    deals = load_json_safe("deals_auto.json") or []
    feed = load_json_safe("funding_feed_auto.json") or []
    public = _public_companies()

    merged = []
    for d in feed:
        company = (d.get("company") or "").strip()
        if company.lower() in public:
            continue  # skip public companies
        amount = d.get("amount", "")
        amount_raw = parse_amount_to_usd(amount)
        # Validate the deal is real
        if not _is_real_funding(company, d.get("headline", ""), d.get("round", ""), amount_raw):
            continue
        merged.append({
            "company": company,
            "amount": amount,
            "amount_raw": amount_raw,
            "round": d.get("round", ""),
            "date": d.get("date", ""),
            "source": d.get("source", ""),
            "url": d.get("url", ""),
            "headline": d.get("headline", ""),
            "investors": d.get("investors", []),
        })

    for d in deals:
        company = (d.get("company") or "").strip()
        if company.lower() in public:
            continue  # skip public companies
        # Avoid duplicating by (company, date)
        key = (company, d.get("date", ""))
        if any((m["company"], m["date"]) == key for m in merged):
            continue
        amount = d.get("amount", "")
        amount_raw = parse_amount_to_usd(amount)
        # Sanity caps — no validation on deals_auto since no headline
        if amount_raw > 50e9 or amount_raw <= 0:
            continue
        merged.append({
            "company": company,
            "amount": amount,
            "amount_raw": amount_raw,
            "round": d.get("round", ""),
            "date": d.get("date", ""),
            "source": "Crunchbase",
            "url": "",
            "headline": "",
            "investors": [d.get("investor", "")] if d.get("investor") else [],
        })

    # Filter by recency + sort by deal size desc
    recent = [m for m in merged if within_days(m["date"], days) and m["amount_raw"] > 0]
    recent.sort(key=lambda x: x["amount_raw"], reverse=True)
    return recent[:limit]


def top_news(limit=10):
    signals = load_js_const("news_signals_auto.js", "COMPANY_SIGNALS_AUTO") or []
    # Prefer items with links
    trimmed = []
    for s in signals[:30]:
        trimmed.append({
            "company": s.get("company", ""),
            "headline": s.get("headline", s.get("title", "")),
            "source": s.get("source", ""),
            "time": s.get("time", s.get("date", "")),
            "url": s.get("link", s.get("url", "")),
            "impact": s.get("impact", ""),
        })
    return trimmed[:limit]


def gov_highlights(limit=8):
    """Biggest government contracts in last 7 days."""
    raw = load_json_safe("sam_contracts_aggregated.json") or []
    items = []
    for c in raw[:200]:
        amt_str = c.get("amount", "") or c.get("awardAmount", "")
        amt_raw = parse_amount_to_usd(str(amt_str))
        if amt_raw <= 0:
            continue
        date = c.get("date", c.get("awardDate", ""))
        if not within_days(str(date)[:10], 14):
            continue
        items.append({
            "company": c.get("company", c.get("awardee", "")),
            "amount": amt_str,
            "amount_raw": amt_raw,
            "agency": c.get("agency", ""),
            "description": c.get("description", c.get("title", "")),
            "date": date,
            "url": c.get("url", "https://sam.gov"),
        })
    items.sort(key=lambda x: x["amount_raw"], reverse=True)
    return items[:limit]


def market_movers(limit=8):
    """Biggest public company price moves (up or down) today."""
    stocks = load_js_const("stocks_auto.js", "STOCK_PRICES") or {}
    movers = []
    for ticker, data in stocks.items():
        if not isinstance(data, dict):
            continue
        try:
            pct = float(data.get("changePercent", 0))
        except (ValueError, TypeError):
            continue
        if abs(pct) < 1.5:
            continue
        movers.append({
            "ticker": ticker,
            "company": data.get("company", ""),
            "price": data.get("price", 0),
            "changePercent": pct,
            "change": data.get("change", 0),
        })
    movers.sort(key=lambda x: abs(x["changePercent"]), reverse=True)
    return movers[:limit]


def regulatory_highlights(limit=6):
    """Recent FDA actions + federal register frontier-tech entries."""
    items = []
    # FDA actions
    fda = load_json_safe("fda_actions_raw.json") or []
    for f in fda[:20]:
        if not within_days(f.get("date", f.get("actionDate", ""))[:10], 14):
            continue
        items.append({
            "kind": "FDA",
            "company": f.get("company", f.get("sponsor", "")),
            "title": f.get("action", f.get("title", ""))[:140],
            "date": f.get("date", f.get("actionDate", "")),
            "url": f.get("url", "https://www.fda.gov"),
        })
    # Federal register
    fr = load_js_const("federal_register_auto.js", "FEDERAL_REGISTER_AUTO") or []
    for r in fr[:20]:
        if not within_days(r.get("date", "")[:10], 14):
            continue
        items.append({
            "kind": "Federal Register",
            "company": r.get("company", ""),
            "title": r.get("title", "")[:140],
            "date": r.get("date", ""),
            "url": r.get("url", "https://www.federalregister.gov"),
        })
    return items[:limit]


def patents_recent(limit=6):
    """Recent patent grants from patents_aggregated.json."""
    raw = load_json_safe("patents_aggregated.json")
    if not raw or not isinstance(raw, list):
        return []
    items = []
    for p in raw[:30]:
        if not isinstance(p, dict):
            continue
        if not within_days(str(p.get("grantDate", p.get("date", "")))[:10], 30):
            continue
        items.append({
            "company": p.get("company", p.get("assignee", "")),
            "title": p.get("title", "")[:140],
            "date": p.get("grantDate", p.get("date", "")),
            "url": p.get("url", ""),
        })
    return items[:limit]


def main():
    print("=" * 60)
    print("Daily Frontier Tech Digest Generator")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # AUTHORITATIVE-ONLY digest — no RSS-parsed funding deals or text-matched news
    # (previous versions included Palantir $30B, SiFive-as-Cerebras, etc. — all wrong)
    digest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "dateDisplay": datetime.now().strftime("%A, %B %d, %Y"),
        "sections": {
            "govActivity": gov_highlights(),          # SAM.gov (authoritative)
            "marketMovers": market_movers(),          # Yahoo Finance (authoritative)
            "regulatory": regulatory_highlights(),    # FDA openFDA + Federal Register (authoritative)
            "patents": patents_recent(),              # USPTO (authoritative)
        },
    }

    # Stats
    digest["stats"] = {
        "contractCount": len(digest["sections"]["govActivity"]),
        "moverCount": len(digest["sections"]["marketMovers"]),
        "regCount": len(digest["sections"]["regulatory"]),
        "patentCount": len(digest["sections"]["patents"]),
    }
    # Top mover (used in hero stats)
    if digest["sections"]["marketMovers"]:
        tm = digest["sections"]["marketMovers"][0]
        digest["stats"]["topMover"] = f"{tm['ticker']} {tm['changePercent']:+.1f}%"
    else:
        digest["stats"]["topMover"] = "—"

    out_path = DATA_DIR / "daily_digest.json"
    with open(out_path, "w") as f:
        json.dump(digest, f, indent=2)

    print(f"Gov Contracts:       {digest['stats']['contractCount']}")
    print(f"Market Movers:       {digest['stats']['moverCount']}")
    print(f"Regulatory:          {digest['stats']['regCount']}")
    print(f"Recent Patents:      {digest['stats']['patentCount']}")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
