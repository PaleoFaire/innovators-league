#!/usr/bin/env python3
"""
Hacker News API Fetcher
Tracks startup buzz and tech community discussions.
Uses the free Firebase Hacker News API - no key required, no rate limits.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time
import re

# Companies to track mentions
TRACKED_COMPANIES = [
    # Defense Tech
    "Anduril", "Shield AI", "Palantir", "Saronic", "Hadrian", "Epirus",
    "Skydio", "Hermeus", "Castelion", "Vannevar",

    # Space
    "SpaceX", "Starlink", "Rocket Lab", "Relativity Space", "Astra",
    "Planet Labs", "Varda Space", "Impulse Space", "Stoke Space",
    "Astranis", "Firefly Aerospace", "Blue Origin", "Sierra Space",

    # Nuclear
    "Oklo", "NuScale", "Kairos Power", "Commonwealth Fusion", "Helion",
    "TAE Technologies", "Radiant Nuclear", "TerraPower", "X-energy",

    # AI/Robotics
    "OpenAI", "Anthropic", "Figure AI", "Physical Intelligence",
    "Covariant", "Agility Robotics", "Boston Dynamics", "1X Technologies",
    "Groq", "Cerebras", "Mistral", "Cohere",

    # Quantum
    "IonQ", "Rigetti", "D-Wave", "PsiQuantum", "Atom Computing",

    # Biotech
    "Recursion", "Ginkgo Bioworks", "Mammoth Biosciences",
]

# Technology keywords to track
TECH_KEYWORDS = [
    "humanoid robot", "autonomous drone", "directed energy",
    "hypersonic", "small modular reactor", "fusion reactor",
    "quantum computer", "LLM", "foundation model",
    "SBIR", "DARPA", "defense tech", "space startup",
]

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"

def fetch_top_stories(limit=100):
    """Fetch top story IDs."""
    url = f"{HN_API_BASE}/topstories.json"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()[:limit]
    except:
        pass
    return []

def fetch_new_stories(limit=100):
    """Fetch new story IDs."""
    url = f"{HN_API_BASE}/newstories.json"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()[:limit]
    except:
        pass
    return []

def fetch_best_stories(limit=100):
    """Fetch best story IDs."""
    url = f"{HN_API_BASE}/beststories.json"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()[:limit]
    except:
        pass
    return []

def fetch_story(story_id):
    """Fetch a single story by ID."""
    url = f"{HN_API_BASE}/item/{story_id}.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def search_stories(story_ids, batch_size=50):
    """Fetch and filter stories for relevant mentions."""
    relevant_stories = []

    for i, story_id in enumerate(story_ids[:batch_size]):
        story = fetch_story(story_id)
        if not story or story.get("type") != "story":
            continue

        title = story.get("title", "")
        url = story.get("url", "")
        text = story.get("text", "") or ""

        combined_text = f"{title} {url} {text}".lower()

        # Check for company mentions
        matched_companies = []
        for company in TRACKED_COMPANIES:
            if company.lower() in combined_text:
                matched_companies.append(company)

        # Check for keyword mentions
        matched_keywords = []
        for keyword in TECH_KEYWORDS:
            if keyword.lower() in combined_text:
                matched_keywords.append(keyword)

        if matched_companies or matched_keywords:
            relevant_stories.append({
                "id": story_id,
                "title": title,
                "url": url,
                "score": story.get("score", 0),
                "comments": story.get("descendants", 0),
                "author": story.get("by", ""),
                "time": story.get("time", 0),
                "date": datetime.fromtimestamp(story.get("time", 0)).strftime("%Y-%m-%d") if story.get("time") else "",
                "companies": matched_companies,
                "keywords": matched_keywords,
                "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
            })

        # Small delay to be nice
        if i % 10 == 0:
            time.sleep(0.1)

    return relevant_stories

def fetch_all_relevant_stories():
    """Fetch relevant stories from all HN feeds."""
    all_stories = []
    seen_ids = set()

    print("Fetching top stories...")
    top_ids = fetch_top_stories(100)
    top_relevant = search_stories(top_ids)
    for s in top_relevant:
        if s["id"] not in seen_ids:
            s["source"] = "top"
            seen_ids.add(s["id"])
            all_stories.append(s)
    print(f"  Found {len(top_relevant)} relevant in top stories")

    print("Fetching best stories...")
    best_ids = fetch_best_stories(100)
    best_relevant = search_stories(best_ids)
    for s in best_relevant:
        if s["id"] not in seen_ids:
            s["source"] = "best"
            seen_ids.add(s["id"])
            all_stories.append(s)
    print(f"  Found {len([s for s in best_relevant if s['id'] not in seen_ids])} new relevant in best stories")

    print("Fetching new stories...")
    new_ids = fetch_new_stories(100)
    new_relevant = search_stories(new_ids)
    for s in new_relevant:
        if s["id"] not in seen_ids:
            s["source"] = "new"
            seen_ids.add(s["id"])
            all_stories.append(s)
    print(f"  Found {len([s for s in new_relevant if s['id'] not in seen_ids])} new relevant in new stories")

    return all_stories

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(stories):
    """Generate JavaScript code snippet for HN_BUZZ."""
    # Sort by score descending
    stories.sort(key=lambda x: x.get("score", 0), reverse=True)

    js_output = "// Auto-updated Hacker News startup buzz\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const HN_BUZZ = [\n"

    for s in stories[:30]:
        title = s.get("title", "").replace('"', '\\"').replace('\n', ' ')[:80]
        companies = ", ".join(s.get("companies", [])[:3])
        keywords = ", ".join(s.get("keywords", [])[:2])

        js_output += f'  {{ id: {s["id"]}, title: "{title}", '
        js_output += f'score: {s["score"]}, comments: {s["comments"]}, '
        js_output += f'date: "{s["date"]}", companies: "{companies}", keywords: "{keywords}", '
        js_output += f'source: "{s["source"]}" }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "hackernews_buzz_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("Hacker News Startup Buzz Tracker")
    print("=" * 60)
    print(f"Tracking {len(TRACKED_COMPANIES)} companies")
    print(f"Tracking {len(TECH_KEYWORDS)} tech keywords")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all relevant stories
    stories = fetch_all_relevant_stories()
    print(f"\nTotal relevant stories found: {len(stories)}")

    # Save data
    save_to_json(stories, "hackernews_buzz_raw.json")

    # Generate JS snippet
    generate_js_snippet(stories)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary by company mentions
    if stories:
        print("\nTop mentioned companies:")
        company_counts = {}
        for s in stories:
            for c in s.get("companies", []):
                company_counts[c] = company_counts.get(c, 0) + 1
        for company, count in sorted(company_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {company}: {count} mentions")

        print("\nTop stories:")
        for s in sorted(stories, key=lambda x: -x.get("score", 0))[:5]:
            print(f"  [{s['score']} pts] {s['title'][:60]}...")

if __name__ == "__main__":
    main()
