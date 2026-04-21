#!/usr/bin/env python3
"""
Extract M&A / acquisition comparables from press releases + SEC filings +
RSS news feeds. Produces data/ma_comps_auto.json.

A "comp" here = an acquisition, a SPAC merger, or a strategic-stake deal
where we can capture target, acquirer, EV, sector, and date.

Part of Round 7l.
"""

import json
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_PATH = DATA_DIR / "ma_comps_auto.json"


def safe_json(name):
    p = DATA_DIR / name
    if not p.exists(): return []
    try:
        return json.load(open(p))
    except Exception:
        return []


# Phrases that indicate an M&A-type or strategic-stake event
MA_TRIGGERS = [
    r"to acquire",
    r"acquires?",
    r"acquisition of",
    r"has agreed to purchase",
    r"merger with",
    r"spac merger",
    r"take private",
    r"taken private",
    r"bought by",
    r"to buy",
    r"strategic stake",
    r"takeover",
    r"tender offer",
    r"agrees to acquire",
    r"definitive agreement",
    r"takes \$\d+[mb]",     # "takes $5B from Amazon"
    r"invests? \$\d+[mb]",  # "Nvidia invests $2B in"
    r"stake in",
    r"controlling stake",
    r"majority stake",
]

# Sector keyword hints
SECTORS = {
    "Space & Aerospace":       ["space", "satellite", "launch", "rocket", "orbit"],
    "Defense & Security":      ["defense", "military", "drone", "battlefield", "missile"],
    "Nuclear Energy":          ["nuclear", "reactor", "smr", "fusion"],
    "AI & Software":           ["ai ", "artificial intelligence", "machine learning", "llm"],
    "Chips & Semiconductors":  ["chip", "semiconductor", "silicon", "foundry"],
    "Biotech & Health":        ["biotech", "pharma", "drug", "therapeut", "clinical"],
    "Drones & Autonomous":     ["drone", "uas", "autonomous", "robotaxi"],
    "Robotics & Manufacturing":["robot", "humanoid", "manufact", "additive"],
    "Climate & Energy":        ["battery", "energy", "grid", "solar", "fusion"],
    "Quantum Computing":       ["quantum"],
}


def classify_sector(text):
    t = text.lower()
    for sec, kws in SECTORS.items():
        if any(k in t for k in kws): return sec
    return "Other"


def parse_dollar(text):
    """Find the largest $X amount mentioned."""
    t = text.replace(",", "")
    m = re.findall(r"\$(\d+\.?\d*)\s*(billion|bn|b|million|mn|m)\b", t, re.IGNORECASE)
    best = 0.0
    for num, unit in m:
        try: v = float(num)
        except ValueError: continue
        u = unit.lower()[0]
        if u == "b": v *= 1000
        best = max(best, v)
    if best == 0: return ""
    if best >= 1000: return f"${best/1000:.1f}B"
    return f"${best:.0f}M"


def extract_target_acquirer(text):
    """Try simple regex extraction in several shapes. Best-effort only.
    Shape 1: '<acquirer> acquires <target>'  (acquirer first)
    Shape 2: '<acquirer> invests $X in <target>'  (strategic stake)
    Shape 3: '<target> takes $X from <acquirer>'  (strategic stake, reversed)
    Shape 4: '<target> acquired by <acquirer>'  (passive)
    """
    # Company name token: capital letter start, then up to 40 chars that
    # stop before common sentence connectors ("and", "or", "for", "in",
    # "from"...) which otherwise get swept into the match.
    name_rx = r"([A-Z][A-Za-z0-9&'.\-]+(?:\s+[A-Z][A-Za-z0-9&'.\-]+){0,4})"
    patterns = [
        # Shape 1: acquirer-first
        (name_rx + r"\s+(?:to acquire|acquires|is acquiring|has acquired|will acquire|agrees to acquire)\s+" + name_rx, "acq_first"),
        (name_rx + r"\s+(?:buys|to buy|has bought)\s+" + name_rx, "acq_first"),
        # Shape 2: strategic investment, acquirer first
        (name_rx + r"\s+invests?\s+\$[\d.]+\s*[mb]?\w*\s+in\s+" + name_rx, "acq_first"),
        (name_rx + r"\s+leads?\s+\$[\d.]+\s*[mb]?\w*\s+(?:investment in|stake in)\s+" + name_rx, "acq_first"),
        # Shape 3: target-first strategic stake ("X takes $Y from Z")
        (name_rx + r"\s+takes\s+\$[\d.]+\s*[mb]?\w*\s+from\s+" + name_rx, "tgt_first"),
        # Shape 4: passive acquisition ("X acquired by Y")
        (name_rx + r"\s+(?:acquired by|bought by|merged into)\s+" + name_rx, "tgt_first"),
    ]
    for p, shape in patterns:
        m = re.search(p, text)
        if m:
            a = m.group(1).strip().rstrip(".,")
            b = m.group(2).strip().rstrip(".,")
            if not (2 < len(a) <= 40 and 2 < len(b) <= 40):
                continue
            if shape == "acq_first":
                return b, a  # (target, acquirer)
            else:
                return a, b  # (target, acquirer)
    return None, None


def main():
    press = safe_json("press_releases_filtered.json")
    news = safe_json("news_raw.json")
    sec = safe_json("sec_filings_recent.json")

    all_items = []
    for p in press:
        all_items.append({
            "title": p.get("title", ""),
            "text": p.get("title", "") + " " + (p.get("description") or ""),
            "date": p.get("date") or p.get("pubDate", ""),
            "url": p.get("link", ""),
            "src": "press",
        })
    for n in news:
        all_items.append({
            "title": n.get("title", ""),
            "text": n.get("title", "") + " " + (n.get("description") or ""),
            "date": n.get("pubDate", ""),
            "url": n.get("link", ""),
            "src": "news",
        })
    for s in sec:
        title = s.get("title") or s.get("form") or ""
        text = title + " " + (s.get("description") or "")
        all_items.append({
            "title": title,
            "text": text,
            "date": s.get("filedDate") or s.get("date", ""),
            "url": s.get("url", ""),
            "src": "sec",
        })

    print(f"  Scanning {len(all_items)} items for M&A triggers")

    comps = []
    seen = set()
    for it in all_items:
        t = it["text"]
        # Must mention at least one trigger
        if not any(re.search(trg, t, re.IGNORECASE) for trg in MA_TRIGGERS):
            continue
        tgt, acq = extract_target_acquirer(t)
        if not (tgt and acq):
            continue
        key = (tgt.lower(), acq.lower())
        if key in seen: continue
        seen.add(key)
        ev = parse_dollar(t)
        sector = classify_sector(t)
        # Extract year from date field. Accepts ISO ("2026-04-20"), RFC822
        # ("Mon, 20 Apr 2026 14:33 GMT") and bare year strings.
        raw_date = it["date"] or ""
        ym = re.search(r"\b(20\d{2})\b", raw_date)
        year = ym.group(1) if ym else ""

        comps.append({
            "target": tgt,
            "acquirer": acq,
            "sector": sector,
            "year": year,
            "ev": ev or "Undisclosed",
            "notes": it["title"][:160],
            "source": it["src"],
            "url": it["url"],
            "type": "Announced",
        })
        if len(comps) >= 40:
            break

    # Emit
    OUT_PATH.write_text(json.dumps(comps, indent=2))
    print(f"  Extracted {len(comps)} M&A comps → {OUT_PATH}")


if __name__ == "__main__":
    main()
