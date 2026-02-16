#!/usr/bin/env python3
"""
arXiv Research Papers Fetcher
Tracks cutting-edge research in AI, robotics, physics, and quantum computing.
Uses the free arXiv API - no key required.
"""

import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
import time
import urllib.parse

# Research categories to track
ARXIV_CATEGORIES = {
    "cs.AI": "Artificial Intelligence",
    "cs.RO": "Robotics",
    "cs.LG": "Machine Learning",
    "cs.CV": "Computer Vision",
    "cs.CL": "Natural Language Processing",
    "quant-ph": "Quantum Physics",
    "physics.app-ph": "Applied Physics",
    "nucl-th": "Nuclear Theory",
    "astro-ph": "Astrophysics",
    "eess.SY": "Systems and Control",
}

# Keywords for defense/space/energy tech
SECTOR_KEYWORDS = {
    "defense": ["autonomous vehicle", "drone", "uav", "swarm", "missile", "radar", "lidar", "sensor fusion", "target detection", "electronic warfare"],
    "space": ["satellite", "spacecraft", "orbital", "rocket", "propulsion", "lunar", "mars", "asteroid", "space debris", "cubesat"],
    "nuclear": ["nuclear reactor", "fission", "fusion", "tokamak", "stellarator", "plasma", "neutron", "radioactive", "uranium", "thorium"],
    "robotics": ["humanoid", "manipulation", "locomotion", "grasping", "reinforcement learning", "imitation learning", "robot control", "actuator"],
    "quantum": ["qubit", "quantum computer", "quantum algorithm", "quantum error", "quantum entanglement", "quantum sensing", "quantum network"],
    "ai": ["large language model", "transformer", "foundation model", "neural network", "deep learning", "generative ai", "diffusion model"],
}

ARXIV_API_BASE = "http://export.arxiv.org/api/query"

def fetch_category_papers(category, max_results=50):
    """Fetch recent papers from an arXiv category."""
    params = {
        "search_query": f"cat:{category}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    url = f"{ARXIV_API_BASE}?{urllib.parse.urlencode(params)}"

    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"  Error: {response.status_code}")
            return []

        # Parse XML response
        root = ET.fromstring(response.content)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        papers = []
        for entry in root.findall("atom:entry", ns):
            paper = {
                "id": entry.find("atom:id", ns).text.split("/")[-1] if entry.find("atom:id", ns) is not None else "",
                "title": entry.find("atom:title", ns).text.strip().replace("\n", " ") if entry.find("atom:title", ns) is not None else "",
                "summary": (entry.find("atom:summary", ns).text or "").strip().replace("\n", " ")[:500] if entry.find("atom:summary", ns) is not None else "",
                "published": entry.find("atom:published", ns).text[:10] if entry.find("atom:published", ns) is not None else "",
                "updated": entry.find("atom:updated", ns).text[:10] if entry.find("atom:updated", ns) is not None else "",
                "category": category,
                "categoryName": ARXIV_CATEGORIES.get(category, category),
                "authors": [],
                "links": [],
            }

            # Get authors
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns)
                if name is not None:
                    paper["authors"].append(name.text)

            # Get links
            for link in entry.findall("atom:link", ns):
                if link.get("type") == "application/pdf":
                    paper["pdf"] = link.get("href")

            papers.append(paper)

        return papers

    except Exception as e:
        print(f"  Error: {e}")
        return []

def categorize_by_sector(papers):
    """Categorize papers by sector based on keywords."""
    for paper in papers:
        text = (paper.get("title", "") + " " + paper.get("summary", "")).lower()

        paper["sectors"] = []
        for sector, keywords in SECTOR_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                paper["sectors"].append(sector)

    return papers

def fetch_all_papers():
    """Fetch papers from all tracked categories."""
    all_papers = []

    for category, name in ARXIV_CATEGORIES.items():
        print(f"Fetching papers from: {name} ({category})")
        papers = fetch_category_papers(category, max_results=30)
        print(f"  Found {len(papers)} papers")
        all_papers.extend(papers)
        time.sleep(3)  # arXiv requests 3 second delay between requests

    return all_papers

def filter_recent_papers(papers, days=30):
    """Filter to papers from the last N days."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [p for p in papers if p.get("published", "") >= cutoff]

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(papers):
    """Generate JavaScript code snippet for ARXIV_PAPERS."""
    # Sort by published date descending
    papers.sort(key=lambda x: x.get("published", ""), reverse=True)

    # Filter to papers with sector relevance
    sector_papers = [p for p in papers if p.get("sectors")]

    js_output = "// Auto-updated arXiv research papers\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const ARXIV_PAPERS = [\n"

    for p in sector_papers[:40]:
        title = p.get("title", "").replace('"', '\\"')[:100]
        authors = ", ".join(p.get("authors", [])[:3])
        if len(p.get("authors", [])) > 3:
            authors += " et al."
        sectors = ", ".join(p.get("sectors", []))

        js_output += f'  {{ id: "{p["id"]}", title: "{title}", '
        js_output += f'category: "{p["categoryName"]}", published: "{p["published"]}", '
        js_output += f'sectors: "{sectors}", authors: "{authors}" }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "arxiv_papers_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("arXiv Research Papers Fetcher")
    print("=" * 60)
    print(f"Tracking {len(ARXIV_CATEGORIES)} research categories")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all papers
    papers = fetch_all_papers()
    print(f"\nTotal papers fetched: {len(papers)}")

    # Filter to recent
    recent = filter_recent_papers(papers, days=30)
    print(f"Papers in last 30 days: {len(recent)}")

    # Categorize by sector
    categorized = categorize_by_sector(recent)
    sector_relevant = [p for p in categorized if p.get("sectors")]
    print(f"Sector-relevant papers: {len(sector_relevant)}")

    # Save data
    save_to_json(papers, "arxiv_papers_raw.json")
    save_to_json(sector_relevant, "arxiv_papers_filtered.json")

    # Generate JS snippet
    generate_js_snippet(categorized)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary by sector
    if sector_relevant:
        print("\nPapers by sector:")
        sector_counts = {}
        for p in sector_relevant:
            for s in p.get("sectors", []):
                sector_counts[s] = sector_counts.get(s, 0) + 1
        for sector, count in sorted(sector_counts.items(), key=lambda x: -x[1]):
            print(f"  {sector}: {count} papers")

if __name__ == "__main__":
    main()
