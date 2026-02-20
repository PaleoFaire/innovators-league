#!/usr/bin/env python3
"""
Link Checker for Innovators League
Extracts all URLs from data.js (rosLink, website fields) and checks if they're live.
Uses HEAD requests with fallback to GET, parallel execution via ThreadPoolExecutor.

Usage:
  python3 scripts/check_links.py           # Check all links
  python3 scripts/check_links.py --report  # Save JSON report to data/link_report.json
"""

import re
import json
import sys
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

DATA_JS_PATH = Path(__file__).parent.parent / "data.js"
REPORT_PATH = Path(__file__).parent.parent / "data" / "link_report.json"
TIMEOUT = 10
MAX_WORKERS = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (InnovatorsLeague LinkChecker/1.0)",
    "Accept": "text/html,application/xhtml+xml"
}


def extract_urls(filepath):
    """Extract all URLs and their associated company names from data.js."""
    with open(filepath, "r") as f:
        content = f.read()

    urls = []

    # Find rosLink URLs with associated company name
    # Pattern: name: "Company", ... rosLink: "https://..."
    entries = re.finditer(
        r'name:\s*"([^"]+)".*?rosLink:\s*"(https?://[^"]+)"',
        content, re.DOTALL
    )
    for m in entries:
        urls.append({"name": m.group(1), "url": m.group(2), "field": "rosLink"})

    # Find website URLs (mostly in VC_FIRMS)
    entries = re.finditer(
        r'name:\s*"([^"]+)".*?website:\s*"(https?://[^"]+)"',
        content, re.DOTALL
    )
    for m in entries:
        urls.append({"name": m.group(1), "url": m.group(2), "field": "website"})

    # Deduplicate by URL
    seen = set()
    unique = []
    for entry in urls:
        if entry["url"] not in seen:
            seen.add(entry["url"])
            unique.append(entry)

    return unique


def check_url(entry):
    """Check a single URL. Returns entry dict with status added."""
    url = entry["url"]
    result = {**entry, "status": "unknown", "status_code": 0, "error": ""}

    try:
        # Try HEAD first (faster)
        resp = requests.head(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code == 405:
            # Method not allowed, fall back to GET
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)

        result["status_code"] = resp.status_code
        if 200 <= resp.status_code < 400:
            result["status"] = "ok"
        elif resp.status_code == 404:
            result["status"] = "not_found"
        elif resp.status_code == 403:
            result["status"] = "forbidden"
        elif resp.status_code >= 500:
            result["status"] = "server_error"
        else:
            result["status"] = f"http_{resp.status_code}"

    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error"] = "Request timed out"
    except requests.exceptions.ConnectionError as e:
        error_str = str(e)
        if "NameResolutionError" in error_str or "getaddrinfo" in error_str:
            result["status"] = "dns_failure"
            result["error"] = "Domain does not resolve"
        else:
            result["status"] = "connection_error"
            result["error"] = error_str[:100]
    except requests.exceptions.TooManyRedirects:
        result["status"] = "too_many_redirects"
        result["error"] = "Redirect loop detected"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:100]

    return result


def main():
    save_report = "--report" in sys.argv

    print("=" * 60)
    print("Innovators League Link Checker")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Extract URLs
    urls = extract_urls(DATA_JS_PATH)
    print(f"Found {len(urls)} unique URLs to check")
    print(f"  rosLink: {sum(1 for u in urls if u['field'] == 'rosLink')}")
    print(f"  website: {sum(1 for u in urls if u['field'] == 'website')}")
    print()

    if not urls:
        print("No URLs found. Exiting.")
        return

    # Check URLs in parallel
    results = []
    print(f"Checking with {MAX_WORKERS} parallel workers...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_url, entry): entry for entry in urls}
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            if result["status"] != "ok":
                print(f"  [{i}/{len(urls)}] {result['status'].upper():15} | {result['name'][:30]:30} | {result['url'][:50]}")
            elif i % 50 == 0:
                print(f"  [{i}/{len(urls)}] Checked {i} URLs...")

    # Categorize results
    ok = [r for r in results if r["status"] == "ok"]
    broken = [r for r in results if r["status"] in ("not_found", "dns_failure")]
    errors = [r for r in results if r["status"] not in ("ok", "not_found", "dns_failure")]

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"  OK:          {len(ok)}")
    print(f"  Broken:      {len(broken)}")
    print(f"  Other:       {len(errors)}")
    print(f"  Total:       {len(results)}")

    if broken:
        print()
        print("BROKEN LINKS:")
        for r in sorted(broken, key=lambda x: x["name"]):
            print(f"  {r['name'][:35]:35} | {r['status']:12} | {r['url']}")

    if errors:
        print()
        print("ERRORS (may be temporary):")
        for r in sorted(errors, key=lambda x: x["name"]):
            err_detail = f" ({r['error'][:40]})" if r['error'] else ""
            print(f"  {r['name'][:35]:35} | {r['status']:12} | {r['url'][:50]}{err_detail}")

    # Save report
    if save_report:
        report = {
            "date": datetime.now().isoformat(),
            "total": len(results),
            "ok": len(ok),
            "broken": len(broken),
            "errors": len(errors),
            "details": sorted(results, key=lambda x: (x["status"] != "ok", x["name"]))
        }
        with open(REPORT_PATH, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to {REPORT_PATH}")

    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
