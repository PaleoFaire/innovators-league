#!/usr/bin/env python3
"""
Fetch live prices + YTD/1y performance for every ticker referenced in
data/baskets.js (constituents + benchmarks). Writes data/basket_prices_auto.json.

Uses yfinance (handles Yahoo's auth/cookies). Free, no key required.

Schema:
  {
    "generatedAt": ISO-8601,
    "prices": {
      "OKLO": {
        "ticker": "OKLO",
        "name": "Oklo Inc.",
        "price": 9.45,
        "currency": "USD",
        "marketCap": 1234567890,
        "ytdReturn": 0.42,
        "y1Return": 0.85,
        "ok": true,
        "lastUpdated": ISO-8601
      },
      ...
    },
    "summary": { "total": N, "succeeded": N, "failed": N }
  }

Usage:
  python scripts/fetch_basket_prices.py
"""
import json
import re
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

# Quiet yfinance / urllib3 warnings
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASKETS_FILE = DATA / "baskets.js"
OUT = DATA / "basket_prices_auto.json"


def parse_baskets():
    """Pull every ticker from baskets.js (constituents + benchmarks)."""
    src = BASKETS_FILE.read_text(encoding="utf-8")
    tickers = set()
    for m in re.finditer(r'ticker:\s*"([^"]+)"', src):
        tickers.add(m.group(1))
    for m in re.finditer(r'benchmark:\s*"([^"]+)"', src):
        tickers.add(m.group(1))
    return sorted(tickers)


def fetch_one(ticker, yf):
    """Fetch one ticker; return dict or None."""
    try:
        t = yf.Ticker(ticker)
        # Use .fast_info first (faster than .info)
        try:
            fi = t.fast_info
            price = float(fi.last_price) if fi.last_price else None
            currency = getattr(fi, "currency", "USD")
            market_cap = getattr(fi, "market_cap", None)
        except Exception:
            info = t.info
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            currency = info.get("currency", "USD")
            market_cap = info.get("marketCap")

        if price is None:
            return None

        # 1y history for YTD + 1y returns
        hist = t.history(period="1y", auto_adjust=True)
        ytd_return = None
        y1_return = None
        if hist is not None and not hist.empty:
            closes = hist["Close"]
            if len(closes) > 0:
                # 1y return: first vs last
                first = float(closes.iloc[0])
                last  = float(closes.iloc[-1])
                import math
                if first > 0 and not math.isnan(first) and not math.isnan(last):
                    y1_return = (last / first) - 1.0

                # YTD: first close in current year vs last close
                year = datetime.now(timezone.utc).year
                ytd_data = closes[closes.index.year == year]
                if len(ytd_data) > 0:
                    ytd_first = float(ytd_data.iloc[0])
                    ytd_last  = float(ytd_data.iloc[-1])
                    if ytd_first > 0 and not math.isnan(ytd_first) and not math.isnan(ytd_last):
                        ytd_return = (ytd_last / ytd_first) - 1.0
                # Sanitize against NaN propagating to JSON (which would be invalid)
                if y1_return is not None and math.isnan(y1_return):  y1_return = None
                if ytd_return is not None and math.isnan(ytd_return): ytd_return = None

        # Try to get short company name
        try:
            name = (t.info.get("shortName") or t.info.get("longName") or ticker)[:60]
        except Exception:
            name = ticker

        return {
            "ticker": ticker,
            "name": name,
            "price": round(price, 4),
            "currency": currency,
            "marketCap": market_cap,
            "ytdReturn": round(ytd_return, 4) if ytd_return is not None else None,
            "y1Return": round(y1_return, 4) if y1_return is not None else None,
            "ok": True,
            "lastUpdated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    except Exception as e:
        return None


def main():
    try:
        import yfinance as yf
    except ImportError:
        print("ERROR: yfinance not installed. Run: pip install yfinance")
        return 1

    tickers = parse_baskets()
    print("=" * 60)
    print(f"Fetching prices for {len(tickers)} tickers (yfinance)")
    print("=" * 60)

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prices": {},
        "summary": {"total": len(tickers), "succeeded": 0, "failed": 0},
    }

    for t in tickers:
        rec = fetch_one(t, yf)
        if rec:
            out["prices"][t] = rec
            out["summary"]["succeeded"] += 1
            ytd = rec.get("ytdReturn")
            ytd_str = f"{ytd*100:+5.1f}%" if ytd is not None else "    ?"
            y1  = rec.get("y1Return")
            y1_str = f"{y1*100:+6.1f}%" if y1 is not None else "     ?"
            print(f"  ✓ {t:<8} ${rec['price']:>10.2f}  YTD {ytd_str}  1y {y1_str}")
        else:
            out["prices"][t] = {"ticker": t, "ok": False, "error": "fetch_failed"}
            out["summary"]["failed"] += 1
            print(f"  ✗ {t:<8} (no data)")

    OUT.write_text(json.dumps(out, indent=2, default=str))
    print()
    print(f"✅ Wrote {OUT.relative_to(ROOT)}")
    print(f"   Succeeded: {out['summary']['succeeded']}/{out['summary']['total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
