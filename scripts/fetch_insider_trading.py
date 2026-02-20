#!/usr/bin/env python3
"""
SEC Form 4 Insider Trading Fetcher
Tracks executive stock transactions for public companies.
Uses the free SEC EDGAR API - no key required.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time
import xml.etree.ElementTree as ET
import re

# Public companies to track with their CIK numbers
TRACKED_TICKERS = {
    # Defense
    "PLTR": {"name": "Palantir Technologies", "cik": "0001321655"},

    # Space
    "RKLB": {"name": "Rocket Lab", "cik": "0001819994"},
    "ASTS": {"name": "AST SpaceMobile", "cik": "0001780312"},
    "PL": {"name": "Planet Labs", "cik": "0001836935"},
    "LUNR": {"name": "Intuitive Machines", "cik": "0001881487"},

    # Nuclear & Energy
    "SMR": {"name": "NuScale Power", "cik": "0001822966"},
    "OKLO": {"name": "Oklo", "cik": "0001849056"},
    "LEU": {"name": "Centrus Energy", "cik": "0001065059"},

    # Quantum
    "IONQ": {"name": "IonQ", "cik": "0001820302"},
    "RGTI": {"name": "Rigetti Computing", "cik": "0001838359"},

    # eVTOL
    "ACHR": {"name": "Archer Aviation", "cik": "0001824502"},
    "JOBY": {"name": "Joby Aviation", "cik": "0001819974"},

    # Biotech
    "RXRX": {"name": "Recursion Pharmaceuticals", "cik": "0001601830"},
    "DNA": {"name": "Ginkgo Bioworks", "cik": "0001830214"},
}

SEC_API_BASE = "https://data.sec.gov"
SEC_HEADERS = {
    "User-Agent": "InnovatorsLeague contact@innovatorsleague.com",
    "Accept": "application/json"
}


def fetch_with_retry(url, headers, max_retries=3, timeout=30):
    """Fetch URL with retry logic and exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 429:
                wait = (2 ** attempt) * 5
                print(f"  Rate limited (429), waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"  Request failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    print(f"  All {max_retries} attempts failed for {url}")
    return None

def fetch_form4_filings(cik, ticker, company_name, days=90):
    """Fetch Form 4 filings for a company."""
    cik_padded = cik.lstrip("0").zfill(10)
    url = f"{SEC_API_BASE}/submissions/CIK{cik_padded}.json"

    response = fetch_with_retry(url, SEC_HEADERS)
    if response is None:
        return []

    data = response.json()

    filings = []
    recent_filings = data.get("filings", {}).get("recent", {})

    if not recent_filings:
        return []

    forms = recent_filings.get("form", [])
    dates = recent_filings.get("filingDate", [])
    accession_numbers = recent_filings.get("accessionNumber", [])
    primary_docs = recent_filings.get("primaryDocument", [])

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    for i in range(min(len(forms), 100)):
        if forms[i] == "4" and dates[i] >= cutoff:
            filings.append({
                "ticker": ticker,
                "company": company_name,
                "form": "4",
                "date": dates[i],
                "accession": accession_numbers[i] if i < len(accession_numbers) else "",
                "document": primary_docs[i] if i < len(primary_docs) else "",
            })

    return filings

def parse_form4_xml(cik, accession, document=""):
    """Parse a Form 4 XML filing to extract transaction details."""
    cik_padded = cik.lstrip("0").zfill(10)
    accession_clean = accession.replace("-", "")

    # Build the URL - use www.sec.gov (not data.sec.gov) for XML filings
    # Strip XSL transform prefix (e.g., "xslF345X05/wk-form4.xml" -> "wk-form4.xml")
    # Use CIK without leading zeros for www.sec.gov paths
    cik_trimmed = cik.lstrip("0")
    sec_www = "https://www.sec.gov"

    if document:
        doc_name = document.split("/")[-1] if "/" in document else document
        url = f"{sec_www}/Archives/edgar/data/{cik_trimmed}/{accession_clean}/{doc_name}"
    else:
        url = f"{sec_www}/Archives/edgar/data/{cik_trimmed}/{accession_clean}/primary_doc.xml"

    try:
        xml_headers = {**SEC_HEADERS, "Accept": "application/xml"}
        response = fetch_with_retry(url, xml_headers)
        if response is None or response.status_code != 200:
            # Try alternate URL patterns
            alt_urls = [
                f"{sec_www}/Archives/edgar/data/{cik_trimmed}/{accession_clean}/primary_doc.xml",
                f"{SEC_API_BASE}/Archives/edgar/data/{cik_padded}/{accession_clean}/primary_doc.xml",
            ]
            for alt_url in alt_urls:
                if alt_url == url:
                    continue
                response = fetch_with_retry(alt_url, SEC_HEADERS)
                if response is not None and response.status_code == 200:
                    break
            else:
                return None

        # Parse XML - strip namespaces to handle various Form 4 formats
        content = response.content
        # Remove XML namespace declarations that cause parsing issues
        content_str = content.decode('utf-8', errors='replace')
        content_str = re.sub(r'\sxmlns[^"]*"[^"]*"', '', content_str)
        content_str = re.sub(r'\sxmlns=[^"]*"[^"]*"', '', content_str)

        root = ET.fromstring(content_str.encode('utf-8'))

        # Extract reporting owner - use tag local name matching
        owner_name = ""
        officer_title = ""

        def local_tag(tag):
            """Get local tag name without namespace."""
            return tag.split('}')[-1] if '}' in tag else tag

        for elem in root.iter():
            tag = local_tag(elem.tag)
            if tag == 'rptOwnerName':
                owner_name = elem.text or ""
            elif tag == 'officerTitle':
                officer_title = elem.text or ""

        # Extract transactions
        transactions = []
        for elem in root.iter():
            tag = local_tag(elem.tag)
            if tag in ('nonDerivativeTransaction', 'derivativeTransaction'):
                tx = {
                    "owner": owner_name,
                    "title": officer_title,
                    "type": "",
                    "shares": 0,
                    "price": 0,
                }
                # Walk all descendants of the transaction element
                for child in elem.iter():
                    child_tag = local_tag(child.tag)
                    if child_tag == 'transactionCode':
                        code = child.text or ""
                        tx["type"] = {
                            "P": "Purchase",
                            "S": "Sale",
                            "A": "Grant",
                            "D": "Disposition",
                            "M": "Exercise",
                            "G": "Gift",
                            "F": "Tax Withholding",
                        }.get(code, code)
                    elif child_tag == 'transactionShares':
                        for val in child.iter():
                            if local_tag(val.tag) == 'value' and val.text:
                                try:
                                    tx["shares"] = int(float(val.text))
                                except (ValueError, TypeError):
                                    pass
                    elif child_tag == 'transactionPricePerShare':
                        for val in child.iter():
                            if local_tag(val.tag) == 'value' and val.text:
                                try:
                                    tx["price"] = float(val.text)
                                except (ValueError, TypeError):
                                    pass
                if tx["type"]:
                    transactions.append(tx)

        return transactions

    except Exception as e:
        print(f"    XML parse error: {e}")
        return None

def fetch_all_insider_transactions():
    """Fetch insider transactions for all tracked companies."""
    all_transactions = []

    for ticker, info in TRACKED_TICKERS.items():
        print(f"Fetching Form 4 filings for: {ticker} ({info['name']})")
        filings = fetch_form4_filings(info["cik"], ticker, info["name"])

        if filings:
            print(f"  Found {len(filings)} Form 4 filings")

            parsed_count = 0
            failed_count = 0
            for filing in filings[:5]:  # Parse top 5 most recent
                transactions = parse_form4_xml(info["cik"], filing["accession"], filing.get("document", ""))
                if transactions:
                    parsed_count += 1
                    for tx in transactions:
                        all_transactions.append({
                            "ticker": ticker,
                            "company": info["name"],
                            "date": filing["date"],
                            "insider": tx.get("owner", "Unknown"),
                            "title": tx.get("title", ""),
                            "transaction_type": tx.get("type", "Unknown"),
                            "shares": tx.get("shares", 0),
                            "price": tx.get("price", 0),
                            "value": tx.get("shares", 0) * tx.get("price", 0),
                        })
                else:
                    failed_count += 1
                time.sleep(0.2)  # Rate limit
            print(f"  Parsed {parsed_count}/{parsed_count + failed_count} filings successfully")
        else:
            print(f"  No recent Form 4 filings")

        time.sleep(0.2)

    return all_transactions

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(transactions):
    """Generate JavaScript code snippet for INSIDER_TRANSACTIONS."""
    # Sort by date descending and filter significant transactions
    transactions.sort(key=lambda x: x.get("date", ""), reverse=True)

    # Filter to purchases and sales over $10k
    significant = [t for t in transactions if t.get("transaction_type") in ["Purchase", "Sale"] and t.get("value", 0) > 10000]

    js_output = "// Auto-updated SEC Form 4 insider transactions\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const INSIDER_TRANSACTIONS = [\n"

    for t in significant[:30]:
        insider = t.get("insider", "").replace('"', '\\"')
        title = t.get("title", "").replace('"', '\\"')
        js_output += f'  {{ ticker: "{t["ticker"]}", company: "{t["company"]}", date: "{t["date"]}", '
        js_output += f'insider: "{insider}", title: "{title}", type: "{t["transaction_type"]}", '
        js_output += f'shares: {t["shares"]}, price: {t["price"]:.2f}, value: {t["value"]:.0f} }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "insider_transactions_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("SEC Form 4 Insider Trading Fetcher")
    print("=" * 60)
    print(f"Tracking {len(TRACKED_TICKERS)} public companies")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all transactions
    transactions = fetch_all_insider_transactions()
    print(f"\nTotal insider transactions found: {len(transactions)}")

    # Filter significant
    significant = [t for t in transactions if t.get("value", 0) > 10000]
    print(f"Significant transactions (>$10k): {len(significant)}")

    # Save data
    save_to_json(transactions, "insider_transactions_raw.json")

    # Generate JS snippet
    generate_js_snippet(transactions)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary
    if significant:
        print("\nRecent Significant Transactions:")
        for t in significant[:10]:
            print(f"  {t['date']} | {t['ticker']:5} | {t['transaction_type']:8} | ${t['value']:,.0f} | {t['insider'][:30]}")

if __name__ == "__main__":
    main()
