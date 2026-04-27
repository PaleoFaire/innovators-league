#!/usr/bin/env python3
"""
Public Multiples + Comparable Engine builder.

Reads `data/stocks_raw.json` (produced by fetch_stocks.py) and emits
`data/public_multiples_auto.json` — sector-grouped public market multiples
with median / 25th-pctile / 75th-pctile benchmarks suitable for the
Comparable Engine UI.

Source of truth: Yahoo Finance (every multiple is computed by Yahoo or
derived directly from Yahoo-reported revenue + market cap). No estimation,
no inferred figures.
"""

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOCKS_PATH = ROOT / "data" / "stocks_raw.json"
OUT_PATH = ROOT / "data" / "public_multiples_auto.json"

# Sector mapping mirrors fetch_stocks.py for consistency
SECTOR_MAP = {
    "PLTR": "ai", "RKLB": "space", "JOBY": "evtol", "ACHR": "evtol",
    "PL": "space", "LUNR": "space", "ASTS": "space", "SATL": "space",
    "LLAP": "space", "OKLO": "nuclear", "QS": "battery",
    "IONQ": "quantum", "RGTI": "quantum", "QBTS": "quantum",
    "RXRX": "biotech", "TEM": "biotech", "RIVN": "ev",
    "ALAB": "chips", "NVDA": "chips", "AMD": "chips", "TSLA": "ev",
    "AUR": "autonomy", "DOBT": "space", "FREY": "battery", "LNZA": "climate",
    "NNE": "nuclear", "SMR": "nuclear", "SLDP": "battery", "EVTL": "evtol",
    "ASTR": "space", "ASRHF": "space", "DRSHF": "defense",
    "ONT.L": "biotech", "277810.KQ": "robotics",
    "IDEAFORGE.NS": "defense", "9348.T": "space",
}

SECTOR_LABELS = {
    "ai": "AI & Compute", "space": "Space & Aerospace", "evtol": "Advanced Air Mobility",
    "nuclear": "Nuclear Energy", "battery": "Energy Storage", "quantum": "Quantum Computing",
    "biotech": "Biotech & Health", "ev": "Electric Vehicles", "chips": "Semiconductors",
    "autonomy": "Autonomous Driving", "climate": "Climate & Bio-Manufacturing",
    "robotics": "Robotics", "defense": "Defense & Dual-use",
}


def percentile(values, q):
    """q in [0, 100]. Returns None if values is empty."""
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (q / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def fmt_dollar(n):
    if n is None:
        return None
    if n >= 1e12:
        return f"${n/1e12:.2f}T"
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.1f}M"
    return f"${n:,.0f}"


def main():
    if not STOCKS_PATH.exists():
        print(f"❌ {STOCKS_PATH} not found. Run fetch_stocks.py first.")
        return 1

    with open(STOCKS_PATH) as f:
        stocks = json.load(f)

    rows = []
    by_sector = {}

    for ticker, s in stocks.items():
        sector = SECTOR_MAP.get(ticker, "other")
        row = {
            "ticker": ticker,
            "company": s.get("company"),
            "sector": sector,
            "sectorLabel": SECTOR_LABELS.get(sector, sector.title()),
            "price": s.get("price"),
            "marketCap": s.get("marketCap"),
            "marketCapRaw": s.get("marketCapRaw"),
            "trailingPE": s.get("trailingPE"),
            "forwardPE": s.get("forwardPE"),
            "priceToSalesTTM": s.get("priceToSalesTTM"),
            "enterpriseToRevenue": s.get("enterpriseToRevenue"),
            "enterpriseToEbitda": s.get("enterpriseToEbitda"),
            "revenueTTM": s.get("revenueTTM"),
            "revenueTTMFormatted": fmt_dollar(s.get("revenueTTM")),
            "revenueGrowthYoY": s.get("revenueGrowthYoY"),
            "grossMarginsTTM": s.get("grossMarginsTTM"),
            "operatingMarginsTTM": s.get("operatingMarginsTTM"),
            "ebitdaTTM": s.get("ebitdaTTM"),
            "lastUpdated": s.get("lastUpdated"),
            "yahooUrl": f"https://finance.yahoo.com/quote/{ticker}",
            "secUrl": (
                f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}"
                if "." not in ticker and len(ticker) <= 5
                else None
            ),
        }
        rows.append(row)
        by_sector.setdefault(sector, []).append(row)

    # Sector benchmarks: median, 25th, 75th of P/S and EV/Revenue
    sector_stats = []
    for sector, sector_rows in by_sector.items():
        ps_vals = [r["priceToSalesTTM"] for r in sector_rows if isinstance(r.get("priceToSalesTTM"), (int, float))]
        evr_vals = [r["enterpriseToRevenue"] for r in sector_rows if isinstance(r.get("enterpriseToRevenue"), (int, float))]
        eve_vals = [r["enterpriseToEbitda"] for r in sector_rows if isinstance(r.get("enterpriseToEbitda"), (int, float))]
        pe_vals = [r["trailingPE"] for r in sector_rows if isinstance(r.get("trailingPE"), (int, float))]
        gr_vals = [r["revenueGrowthYoY"] for r in sector_rows if isinstance(r.get("revenueGrowthYoY"), (int, float))]
        gm_vals = [r["grossMarginsTTM"] for r in sector_rows if isinstance(r.get("grossMarginsTTM"), (int, float))]

        sector_stats.append({
            "sector": sector,
            "sectorLabel": SECTOR_LABELS.get(sector, sector.title()),
            "n": len(sector_rows),
            "tickers": [r["ticker"] for r in sector_rows],
            "priceToSales": {
                "median": percentile(ps_vals, 50),
                "p25": percentile(ps_vals, 25),
                "p75": percentile(ps_vals, 75),
                "n": len(ps_vals),
            },
            "evRevenue": {
                "median": percentile(evr_vals, 50),
                "p25": percentile(evr_vals, 25),
                "p75": percentile(evr_vals, 75),
                "n": len(evr_vals),
            },
            "evEbitda": {
                "median": percentile(eve_vals, 50),
                "p25": percentile(eve_vals, 25),
                "p75": percentile(eve_vals, 75),
                "n": len(eve_vals),
            },
            "trailingPE": {
                "median": percentile(pe_vals, 50),
                "p25": percentile(pe_vals, 25),
                "p75": percentile(pe_vals, 75),
                "n": len(pe_vals),
            },
            "revenueGrowth": {
                "median": percentile(gr_vals, 50),
                "n": len(gr_vals),
            },
            "grossMargin": {
                "median": percentile(gm_vals, 50),
                "n": len(gm_vals),
            },
        })

    sector_stats.sort(key=lambda x: x["sectorLabel"])

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Yahoo Finance · live quoteSummary modules (summaryDetail, defaultKeyStatistics, financialData)",
        "disclaimer": (
            "Public market multiples sourced live from Yahoo Finance. "
            "Comparable Engine applies sector-median multiples to user-supplied "
            "private revenue figures. ROS does NOT estimate private-company "
            "revenue — those inputs must be supplied. All public values are "
            "verifiable on the linked Yahoo Finance ticker page."
        ),
        "tickerCount": len(rows),
        "sectorCount": len(sector_stats),
        "tickers": rows,
        "sectors": sector_stats,
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    # Also emit a JS-wrapped copy so HTML pages can load via <script> tag
    # (avoids needing a fetch for synchronous use in Intel Brief generation)
    js_path = OUT_PATH.with_suffix(".js")
    js_payload = (
        f"// Auto-generated from {OUT_PATH.name}\n"
        f"// Last updated: {out['generatedAt']}\n"
        f"const PUBLIC_MULTIPLES_AUTO = {json.dumps(out, indent=2)};\n"
        f"if (typeof window !== 'undefined') window.PUBLIC_MULTIPLES_AUTO = PUBLIC_MULTIPLES_AUTO;\n"
    )
    js_path.write_text(js_payload)
    print(f"✅ Wrote {OUT_PATH.relative_to(ROOT)} — {len(rows)} tickers, {len(sector_stats)} sectors")
    print(f"✅ Wrote {js_path.relative_to(ROOT)} (script-tag loadable)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
