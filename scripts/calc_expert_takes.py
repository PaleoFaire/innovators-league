#!/usr/bin/env python3
"""
Assemble EXPERT_INSIGHTS + EXPERT_TAKES from:
  1. Earnings-call-extracted signals (when available) — high-value
     incumbent quotes pointing at frontier sectors
  2. News items with strong impact scoring (high/medium)
  3. Press-release headlines from verified sources

Output: data/expert_takes_auto.json
Part of Round 7l.
"""

import json
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_PATH = DATA_DIR / "expert_takes_auto.json"


def safe_json(name):
    p = DATA_DIR / name
    if not p.exists(): return []
    try: return json.load(open(p))
    except Exception: return []


def main():
    earnings = safe_json("earnings_signals.json") or []
    news = safe_json("news_raw.json") or []
    press = safe_json("press_releases_filtered.json") or []

    takes = []
    insights = []

    # 1. From earnings signals — best quality, direct incumbent quotes
    for e in earnings:
        if not e.get("quote"): continue
        takes.append({
            "author": e.get("incumbent", "Incumbent executive"),
            "role": f"{e.get('quarter', '')} earnings call",
            "company": e.get("target_vertical", "").replace("_", " ").title() or "Frontier Tech",
            "text": e.get("quote", "")[:400],
            "date": e.get("date", ""),
            "source": "earnings_signal",
            "source_url": e.get("source_url", ""),
            "signal_type": e.get("signal_type", ""),
            "ticker": e.get("ticker", ""),
        })
        insights.append({
            "id": len(insights) + 1,
            "expert": e.get("incumbent", ""),
            "role": f"{e.get('quarter', '')} Earnings Call",
            "avatar": "📞",
            "company": e.get("incumbent", ""),
            "topic": (e.get("target_vertical", "") or "Frontier Tech").replace("_", " ").title(),
            "quote": e.get("quote", "")[:400],
            "date": e.get("date", ""),
            "source": "earnings",
        })

    # 2. From high-impact news — framed as "Industry Signal"
    high_news = [n for n in news
                 if (n.get("impact") or "").lower() == "high"
                 and (n.get("title") or "")]
    # Rank by recency
    high_news.sort(key=lambda n: n.get("pubDate", ""), reverse=True)
    for n in high_news[:20]:
        matched = (n.get("matchedCompanies") or [n.get("matchedCompany")])
        company = matched[0] if matched and matched[0] else ""
        takes.append({
            "author": n.get("source", "Industry news"),
            "role": "Industry signal",
            "company": company,
            "text": (n.get("title") or "")[:300],
            "date": n.get("pubDate", "")[:10],
            "source": "news",
            "source_url": n.get("link", ""),
            "signal_type": n.get("type", "news"),
        })

    # 3. Press releases that mention named experts / executives
    press.sort(key=lambda p: p.get("date", ""), reverse=True)
    for p in press[:30]:
        if not p.get("companies"): continue
        title = p.get("title", "")
        # Only include press items that look like executive commentary
        if not re.search(r'(said|says|stated|commented|noted|explained|announced)', title, re.I):
            continue
        takes.append({
            "author": p.get("source", "Press release"),
            "role": "Executive commentary",
            "company": (p.get("companies") or [""])[0],
            "text": title[:300],
            "date": p.get("date", ""),
            "source": "press",
            "source_url": p.get("link", ""),
        })

    takes = takes[:40]
    insights = insights[:30]

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "takes": takes,
        "insights": insights,
        "counts": {
            "from_earnings": sum(1 for t in takes if t["source"] == "earnings_signal"),
            "from_news":     sum(1 for t in takes if t["source"] == "news"),
            "from_press":    sum(1 for t in takes if t["source"] == "press"),
        },
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"  Wrote expert takes ({len(takes)} takes / {len(insights)} insights) → {OUT_PATH}")
    print(f"    Breakdown: {payload['counts']}")


if __name__ == "__main__":
    main()
