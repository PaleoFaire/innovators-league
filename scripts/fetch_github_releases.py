#!/usr/bin/env python3
"""
GitHub Releases Fetcher
Tracks software releases and milestones for open-source companies.
Uses the free GitHub API - no key required (but rate limited to 60/hr).
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

# Companies/projects to track on GitHub
TRACKED_REPOS = {
    # AI/ML
    "huggingface/transformers": {"company": "Hugging Face", "category": "AI"},
    "openai/openai-python": {"company": "OpenAI", "category": "AI"},
    "anthropics/anthropic-sdk-python": {"company": "Anthropic", "category": "AI"},
    "langchain-ai/langchain": {"company": "LangChain", "category": "AI"},
    "run-llama/llama_index": {"company": "LlamaIndex", "category": "AI"},

    # Robotics
    "ros2/ros2": {"company": "Open Robotics", "category": "Robotics"},
    "nvidia-isaac/isaac_ros": {"company": "NVIDIA Isaac", "category": "Robotics"},

    # Space
    "poliastro/poliastro": {"company": "Poliastro", "category": "Space"},

    # Quantum
    "Qiskit/qiskit": {"company": "IBM Quantum", "category": "Quantum"},
    "rigetti/pyquil": {"company": "Rigetti Computing", "category": "Quantum"},
    "PennyLaneAI/pennylane": {"company": "Xanadu", "category": "Quantum"},
    "quantumlib/Cirq": {"company": "Google Quantum AI", "category": "Quantum"},

    # Biotech/Science
    "deepmind/alphafold": {"company": "DeepMind", "category": "Biotech"},
    "facebookresearch/esm": {"company": "Meta AI", "category": "Biotech"},

    # Infrastructure
    "hashicorp/terraform": {"company": "HashiCorp", "category": "Infrastructure"},
    "pulumi/pulumi": {"company": "Pulumi", "category": "Infrastructure"},

    # Data/Analytics
    "apache/spark": {"company": "Databricks", "category": "Data"},
    "dbt-labs/dbt-core": {"company": "dbt Labs", "category": "Data"},

    # Security
    "palantir/osquery": {"company": "Palantir", "category": "Security"},
}

GITHUB_API_BASE = "https://api.github.com"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "InnovatorsLeague"
}

def fetch_repo_releases(repo, info, days=90):
    """Fetch recent releases for a GitHub repo."""
    url = f"{GITHUB_API_BASE}/repos/{repo}/releases"

    try:
        response = requests.get(url, headers=GITHUB_HEADERS, timeout=30)

        if response.status_code == 200:
            releases = response.json()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            recent = []
            for release in releases[:10]:
                published = release.get("published_at", "")
                if published and published >= cutoff:
                    recent.append({
                        "repo": repo,
                        "company": info["company"],
                        "category": info["category"],
                        "tag": release.get("tag_name", ""),
                        "name": release.get("name", release.get("tag_name", "")),
                        "date": published[:10] if published else "",
                        "prerelease": release.get("prerelease", False),
                        "url": release.get("html_url", ""),
                        "body": (release.get("body", "") or "")[:200],  # First 200 chars
                    })
            return recent

        elif response.status_code == 404:
            return []
        else:
            remaining = response.headers.get("X-RateLimit-Remaining", "?")
            print(f"  API error {response.status_code} (Rate limit remaining: {remaining})")
            return []

    except requests.exceptions.RequestException as e:
        print(f"  Error: {e}")
        return []

def fetch_all_releases():
    """Fetch releases for all tracked repos."""
    all_releases = []

    for repo, info in TRACKED_REPOS.items():
        print(f"Fetching releases for: {repo}")
        releases = fetch_repo_releases(repo, info)

        if releases:
            print(f"  Found {len(releases)} recent releases")
            all_releases.extend(releases)
        else:
            print(f"  No recent releases")

        # Be nice to GitHub API (60 requests/hr without auth)
        time.sleep(1)

    return all_releases

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(releases):
    """Generate JavaScript code snippet for GITHUB_RELEASES."""
    # Sort by date descending
    releases.sort(key=lambda x: x.get("date", ""), reverse=True)

    # Filter to non-prerelease
    stable = [r for r in releases if not r.get("prerelease")]

    js_output = "// Auto-updated GitHub releases\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const GITHUB_RELEASES = [\n"

    for r in stable[:25]:
        name = r.get("name", "").replace('"', '\\"').replace('\n', ' ')[:50]
        body = r.get("body", "").replace('"', '\\"').replace('\n', ' ')[:100]
        js_output += f'  {{ company: "{r["company"]}", repo: "{r["repo"]}", tag: "{r["tag"]}", '
        js_output += f'name: "{name}", date: "{r["date"]}", category: "{r["category"]}" }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "github_releases_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("GitHub Releases Fetcher")
    print("=" * 60)
    print(f"Tracking {len(TRACKED_REPOS)} repositories")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all releases
    releases = fetch_all_releases()
    print(f"\nTotal releases found: {len(releases)}")

    # Filter stable releases
    stable = [r for r in releases if not r.get("prerelease")]
    print(f"Stable releases: {len(stable)}")

    # Save data
    save_to_json(releases, "github_releases_raw.json")

    # Generate JS snippet
    generate_js_snippet(releases)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary
    if stable:
        print("\nRecent Stable Releases:")
        for r in stable[:10]:
            print(f"  {r['date']} | {r['company']:20} | {r['tag']}")

if __name__ == "__main__":
    main()
