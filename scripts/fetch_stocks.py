#!/usr/bin/env python3
"""
Stock Price Fetcher for The Innovators League
Fetches real-time stock prices for public companies in our database.
Uses Yahoo Finance (free, no API key required).

Coverage: 22 public companies with stock tickers
"""

import json
import requests
import re
from datetime import datetime
from pathlib import Path
import time

# Public companies from MASTER_COMPANY_LIST with tickers
PUBLIC_COMPANIES = [
    # Defense & Space
    ("Palantir", "PLTR"),
    ("Rocket Lab", "RKLB"),
    ("Joby Aviation", "JOBY"),
    ("Archer Aviation", "ACHR"),
    ("Planet Labs", "PL"),
    ("Intuitive Machines", "LUNR"),
    ("AST SpaceMobile", "ASTS"),
    ("Satellogic", "SATL"),
    ("Terran Orbital", "LLAP"),

    # Nuclear & Energy
    ("Oklo", "OKLO"),
    ("QuantumScape", "QS"),

    # Quantum Computing
    ("IonQ", "IONQ"),
    ("Rigetti Computing", "RGTI"),
    ("D-Wave Quantum", "QBTS"),

    # Biotech
    ("Recursion Pharmaceuticals", "RXRX"),
    ("Tempus AI", "TEM"),

    # Transportation
    ("Rivian", "RIVN"),

    # Chips & Semiconductors
    ("Astera Labs", "ALAB"),

    # Major Tech (for context/comparison)
    ("NVIDIA", "NVDA"),
    ("AMD", "AMD"),
    ("Tesla", "TSLA"),
]


def fetch_yahoo_quote(ticker):
    """Fetch stock quote from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    params = {
        "interval": "1d",
        "range": "5d"  # Get 5 days for sparkline data
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()

            result = data.get("chart", {}).get("result", [])
            if not result:
                return None

            quote = result[0]
            meta = quote.get("meta", {})
            indicators = quote.get("indicators", {}).get("quote", [{}])[0]

            # Current price
            current_price = meta.get("regularMarketPrice", 0)
            previous_close = meta.get("previousClose", meta.get("chartPreviousClose", current_price))

            # Calculate change
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0

            # Get close prices for sparkline (last 5 days)
            closes = indicators.get("close", [])
            sparkline = [c for c in closes if c is not None][-5:]

            # Market cap
            market_cap = meta.get("marketCap", 0)
            if market_cap >= 1e12:
                market_cap_str = f"${market_cap/1e12:.1f}T"
            elif market_cap >= 1e9:
                market_cap_str = f"${market_cap/1e9:.1f}B"
            elif market_cap >= 1e6:
                market_cap_str = f"${market_cap/1e6:.1f}M"
            else:
                market_cap_str = "N/A"

            return {
                "price": round(current_price, 2),
                "previousClose": round(previous_close, 2),
                "change": round(change, 2),
                "changePercent": round(change_percent, 2),
                "marketCap": market_cap_str,
                "marketCapRaw": market_cap,
                "volume": meta.get("regularMarketVolume", 0),
                "dayHigh": meta.get("regularMarketDayHigh", 0),
                "dayLow": meta.get("regularMarketDayLow", 0),
                "fiftyTwoWeekHigh": meta.get("fiftyTwoWeekHigh", 0),
                "fiftyTwoWeekLow": meta.get("fiftyTwoWeekLow", 0),
                "sparkline": sparkline,
                "currency": meta.get("currency", "USD"),
                "exchange": meta.get("exchangeName", ""),
            }
        else:
            print(f"  {ticker}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"  {ticker}: Error - {e}")
        return None


def fetch_all_stocks():
    """Fetch stock data for all public companies."""
    stocks = {}

    print(f"\n{'='*60}")
    print("Fetching stock prices...")
    print(f"{'='*60}")

    for company_name, ticker in PUBLIC_COMPANIES:
        print(f"  Fetching: {ticker} ({company_name})...")
        quote = fetch_yahoo_quote(ticker)

        if quote:
            stocks[ticker] = {
                "company": company_name,
                "ticker": ticker,
                **quote,
                "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            direction = "+" if quote["change"] >= 0 else ""
            print(f"    ${quote['price']} ({direction}{quote['changePercent']:.2f}%) - {quote['marketCap']}")
        else:
            print(f"    Failed to fetch")

        time.sleep(0.5)  # Rate limiting

    return stocks


def calculate_portfolio_stats(stocks):
    """Calculate aggregate portfolio statistics."""
    total_market_cap = sum(s.get("marketCapRaw", 0) for s in stocks.values())

    # Sector performance (manual mapping)
    sector_map = {
        "PLTR": "ai", "RKLB": "space", "JOBY": "autonomous", "ACHR": "autonomous",
        "PL": "space", "LUNR": "space", "ASTS": "space", "SATL": "space", "LLAP": "space",
        "OKLO": "nuclear", "QS": "climate",
        "IONQ": "quantum", "RGTI": "quantum", "QBTS": "quantum",
        "RXRX": "biotech", "TEM": "biotech",
        "RIVN": "transportation", "ALAB": "chips",
        "NVDA": "chips", "AMD": "chips", "TSLA": "transportation"
    }

    sector_performance = {}
    for ticker, data in stocks.items():
        sector = sector_map.get(ticker, "other")
        if sector not in sector_performance:
            sector_performance[sector] = {"gainers": 0, "losers": 0, "avg_change": 0, "count": 0}
        sector_performance[sector]["count"] += 1
        sector_performance[sector]["avg_change"] += data.get("changePercent", 0)
        if data.get("changePercent", 0) >= 0:
            sector_performance[sector]["gainers"] += 1
        else:
            sector_performance[sector]["losers"] += 1

    for sector in sector_performance:
        if sector_performance[sector]["count"] > 0:
            sector_performance[sector]["avg_change"] /= sector_performance[sector]["count"]
            sector_performance[sector]["avg_change"] = round(sector_performance[sector]["avg_change"], 2)

    # Top gainers and losers
    sorted_stocks = sorted(stocks.items(), key=lambda x: x[1].get("changePercent", 0), reverse=True)
    top_gainers = [(t, d["company"], d["changePercent"]) for t, d in sorted_stocks[:5]]
    top_losers = [(t, d["company"], d["changePercent"]) for t, d in sorted_stocks[-5:]]

    return {
        "totalMarketCap": f"${total_market_cap/1e12:.2f}T" if total_market_cap >= 1e12 else f"${total_market_cap/1e9:.1f}B",
        "companiesTracked": len(stocks),
        "sectorPerformance": sector_performance,
        "topGainers": top_gainers,
        "topLosers": top_losers,
        "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved to {output_path}")


def generate_js_snippet(stocks, stats):
    """Generate JavaScript code snippet for the website."""
    js_output = f"""// Auto-generated stock price data for The Innovators League
// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
// Companies tracked: {len(stocks)}

const STOCK_PRICES = {json.dumps(stocks, indent=2)};

const STOCK_STATS = {json.dumps(stats, indent=2)};
"""

    output_path = Path(__file__).parent.parent / "data" / "stocks_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")


def main():
    print("=" * 60)
    print("Stock Price Fetcher for The Innovators League")
    print("=" * 60)
    print(f"Public companies: {len(PUBLIC_COMPANIES)}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all stocks
    stocks = fetch_all_stocks()
    print(f"\n{'='*60}")
    print(f"Successfully fetched: {len(stocks)} stocks")
    print(f"{'='*60}")

    # Calculate portfolio stats
    stats = calculate_portfolio_stats(stocks)

    # Save data
    save_to_json(stocks, "stocks_raw.json")
    save_to_json(stats, "stocks_stats.json")

    # Generate JS snippet
    generate_js_snippet(stocks, stats)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary
    print(f"\nPortfolio Overview:")
    print(f"  Total Market Cap: {stats['totalMarketCap']}")
    print(f"  Companies: {stats['companiesTracked']}")

    print(f"\nTop Gainers:")
    for ticker, company, change in stats['topGainers']:
        print(f"  {ticker} ({company}): +{change:.2f}%")

    print(f"\nTop Losers:")
    for ticker, company, change in stats['topLosers']:
        print(f"  {ticker} ({company}): {change:.2f}%")


if __name__ == "__main__":
    main()
