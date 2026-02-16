#!/usr/bin/env python3
"""
Federal Register API Fetcher
Tracks regulatory changes affecting defense, space, nuclear, and tech sectors.
Uses the free Federal Register API - no key required.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

# Agencies to track
TRACKED_AGENCIES = [
    "Department of Defense",
    "Department of Energy",
    "Nuclear Regulatory Commission",
    "National Aeronautics and Space Administration",
    "Federal Aviation Administration",
    "Food and Drug Administration",
    "Department of Commerce",
    "National Science Foundation",
    "Defense Advanced Research Projects Agency",
]

# Keywords for our sectors
SECTOR_KEYWORDS = {
    "defense": ["defense", "military", "munitions", "export control", "ITAR", "EAR", "national security", "CFIUS", "defense contractor"],
    "space": ["space", "satellite", "launch", "orbital", "rocket", "commercial space", "space debris", "spectrum"],
    "nuclear": ["nuclear", "reactor", "NRC", "uranium", "enrichment", "HALEU", "atomic", "radiation", "fusion"],
    "drones": ["unmanned", "UAS", "drone", "autonomous", "BVLOS", "remote pilot", "airspace"],
    "ai": ["artificial intelligence", "machine learning", "AI", "algorithm", "autonomous system"],
    "biotech": ["gene therapy", "CRISPR", "cell therapy", "biologic", "clinical trial", "FDA approval"],
    "quantum": ["quantum", "encryption", "cryptography"],
}

FEDERAL_REGISTER_API = "https://www.federalregister.gov/api/v1"

def fetch_recent_documents(agency=None, keyword=None, days=30, per_page=50):
    """Fetch recent Federal Register documents."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    url = f"{FEDERAL_REGISTER_API}/documents.json"
    params = {
        "per_page": per_page,
        "order": "newest",
        "conditions[publication_date][gte]": cutoff,
    }

    if agency:
        params["conditions[agencies][]"] = agency
    if keyword:
        params["conditions[term]"] = keyword

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code != 200:
            return []

        data = response.json()
        documents = data.get("results", [])

        results = []
        for doc in documents:
            results.append({
                "document_number": doc.get("document_number", ""),
                "title": doc.get("title", ""),
                "type": doc.get("type", ""),
                "abstract": (doc.get("abstract", "") or "")[:500],
                "publication_date": doc.get("publication_date", ""),
                "agencies": [a.get("name", "") for a in doc.get("agencies", [])],
                "html_url": doc.get("html_url", ""),
                "pdf_url": doc.get("pdf_url", ""),
                "action": doc.get("action", ""),
                "dates": doc.get("dates", ""),
                "significant": doc.get("significant", False),
            })

        return results

    except Exception as e:
        print(f"  Error: {e}")
        return []

def fetch_all_documents():
    """Fetch documents for all tracked agencies and keywords."""
    all_docs = []
    seen_ids = set()

    # Fetch by agency
    for agency in TRACKED_AGENCIES[:5]:  # Limit to avoid too many requests
        print(f"Fetching from: {agency}")
        docs = fetch_recent_documents(agency=agency, days=30, per_page=20)

        new_docs = [d for d in docs if d["document_number"] not in seen_ids]
        for d in new_docs:
            seen_ids.add(d["document_number"])

        if new_docs:
            print(f"  Found {len(new_docs)} unique documents")
            all_docs.extend(new_docs)
        else:
            print(f"  No new documents")

        time.sleep(0.5)

    # Fetch by keyword
    all_keywords = []
    for keywords in SECTOR_KEYWORDS.values():
        all_keywords.extend(keywords[:2])  # Take first 2 from each sector

    for keyword in list(set(all_keywords))[:8]:
        print(f"Fetching keyword: {keyword}")
        docs = fetch_recent_documents(keyword=keyword, days=30, per_page=15)

        new_docs = [d for d in docs if d["document_number"] not in seen_ids]
        for d in new_docs:
            seen_ids.add(d["document_number"])

        if new_docs:
            print(f"  Found {len(new_docs)} unique documents")
            all_docs.extend(new_docs)

        time.sleep(0.5)

    return all_docs

def categorize_by_sector(documents):
    """Categorize documents by sector."""
    for doc in documents:
        text = (doc.get("title", "") + " " + doc.get("abstract", "")).lower()

        doc["sectors"] = []
        for sector, keywords in SECTOR_KEYWORDS.items():
            if any(kw.lower() in text for kw in keywords):
                doc["sectors"].append(sector)

    return documents

def filter_significant(documents):
    """Filter to significant/impactful documents."""
    # Significant types
    significant_types = ["Rule", "Proposed Rule", "Notice"]

    return [d for d in documents
            if d.get("significant")
            or d.get("type") in significant_types
            or d.get("sectors")]

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(documents):
    """Generate JavaScript code snippet for FEDERAL_REGISTER."""
    # Sort by publication date descending
    documents.sort(key=lambda x: x.get("publication_date", ""), reverse=True)

    js_output = "// Auto-updated Federal Register documents\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const FEDERAL_REGISTER = [\n"

    for d in documents[:30]:
        title = d.get("title", "").replace('"', '\\"').replace('\n', ' ')[:80]
        agencies = ", ".join(d.get("agencies", [])[:2])
        sectors = ", ".join(d.get("sectors", []))

        js_output += f'  {{ docNum: "{d["document_number"]}", title: "{title}", '
        js_output += f'type: "{d["type"]}", date: "{d["publication_date"]}", '
        js_output += f'agencies: "{agencies}", sectors: "{sectors}", '
        js_output += f'significant: {"true" if d["significant"] else "false"} }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "federal_register_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("Federal Register Regulatory Tracker")
    print("=" * 60)
    print(f"Tracking {len(TRACKED_AGENCIES)} agencies")
    print(f"Tracking {len(SECTOR_KEYWORDS)} sectors")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all documents
    documents = fetch_all_documents()
    print(f"\nTotal unique documents found: {len(documents)}")

    # Categorize by sector
    categorized = categorize_by_sector(documents)

    # Filter significant
    significant = filter_significant(categorized)
    print(f"Significant/sector-relevant: {len(significant)}")

    # Save data
    save_to_json(documents, "federal_register_raw.json")
    save_to_json(significant, "federal_register_filtered.json")

    # Generate JS snippet
    generate_js_snippet(significant)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary by type
    if documents:
        print("\nDocuments by type:")
        type_counts = {}
        for d in documents:
            dtype = d.get("type", "Unknown")
            type_counts[dtype] = type_counts.get(dtype, 0) + 1
        for dtype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {dtype}: {count}")

        print("\nRecent significant documents:")
        for d in sorted(significant, key=lambda x: -x.get("significant", False))[:5]:
            print(f"  [{d['type']}] {d['title'][:60]}...")

if __name__ == "__main__":
    main()
