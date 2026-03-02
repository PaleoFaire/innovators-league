#!/usr/bin/env python3
"""
Product Hunt Launch Tracker for The Innovators League
Tracks when tracked companies launch new products on Product Hunt.
Uses Product Hunt GraphQL API (free developer token required).

API: https://api.producthunt.com/v2/api/graphql
Requires PRODUCTHUNT_API_TOKEN (register at api.producthunt.com/v2/oauth/applications).
"""

import json
import os
import re
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PH_API_URL = "https://api.producthunt.com/v2/api/graphql"
PH_TOKEN = os.environ.get("PRODUCTHUNT_API_TOKEN", "")

# GraphQL query for recent posts
POSTS_QUERY = """
query($cursor: String) {
  posts(first: 50, after: $cursor, order: NEWEST) {
    edges {
      node {
        id
        name
        tagline
        description
        url
        votesCount
        commentsCount
        createdAt
        website
        makers {
          name
        }
        topics {
          edges {
            node {
              name
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


def load_company_aliases():
    """Load company aliases from master company list."""
    master_path = Path(__file__).parent / "company_master_list.js"
    if not master_path.exists():
        print("  WARNING: company_master_list.js not found")
        return {}

    content = master_path.read_text()
    aliases = {}

    # Generic words to skip
    generic_words = {
        'search', 'serverless', 'automation', 'sales', 'productivity',
        'clean energy', 'renewable', 'hardware', 'video', 'research',
        'foundation models', 'computer vision', 'nuclear', 'satellite',
        'quantum computing', 'logistics', 'delivery', 'safety',
    }

    pattern = r'\{\s*name:\s*"([^"]+)",\s*aliases:\s*\[([^\]]*)\]'
    for match in re.finditer(pattern, content):
        name = match.group(1)
        alias_str = match.group(2)

        # Add canonical name
        aliases[name.lower()] = name

        # Add aliases (only specific enough ones)
        for alias_match in re.finditer(r'"([^"]+)"', alias_str):
            alias = alias_match.group(1)
            if len(alias) >= 5 and alias.lower() not in generic_words:
                aliases[alias.lower()] = name

    return aliases


def match_company(text, company_aliases):
    """Match text against known company names/aliases."""
    text_lower = text.lower()
    for alias, canonical_name in company_aliases.items():
        if len(alias) >= 8 and alias in text_lower:
            return canonical_name
        elif len(alias) >= 5:
            # Require word boundary for shorter aliases
            if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                return canonical_name
    return None


def fetch_posts(token, cursor=None):
    """Fetch a page of recent Product Hunt posts."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    variables = {}
    if cursor:
        variables["cursor"] = cursor

    payload = {
        "query": POSTS_QUERY,
        "variables": variables,
    }

    try:
        resp = requests.post(PH_API_URL, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if "errors" in data:
            print(f"  GraphQL errors: {data['errors']}")
            return [], None, False

        posts_data = data.get("data", {}).get("posts", {})
        edges = posts_data.get("edges", [])
        page_info = posts_data.get("pageInfo", {})

        posts = [edge["node"] for edge in edges]
        next_cursor = page_info.get("endCursor")
        has_next = page_info.get("hasNextPage", False)

        return posts, next_cursor, has_next

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching posts: {e}")
        return [], None, False


def main():
    print("=" * 60)
    print("Product Hunt Launch Tracker")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not PH_TOKEN:
        print("WARNING: PRODUCTHUNT_API_TOKEN not set. Generating empty output files.")
        with open(DATA_DIR / "product_launches_raw.json", "w") as f:
            json.dump([], f)
        js_path = DATA_DIR / "product_launches_auto.js"
        with open(js_path, "w") as f:
            f.write(f"// Product Hunt launch data — API token not configured\n")
            f.write(f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("const PRODUCT_LAUNCHES_AUTO = [];\n")
        print("Empty output files created.")
        return

    print(f"API Token: {'*' * 8}...{PH_TOKEN[-4:]}")
    print("=" * 60)

    # Load company aliases
    company_aliases = load_company_aliases()
    print(f"Loaded {len(company_aliases)} company aliases")

    # Fetch recent posts (last 14 days, up to 200)
    all_posts = []
    cursor = None
    cutoff = datetime.now() - timedelta(days=14)
    pages = 0
    max_pages = 4  # 50 per page * 4 = 200 posts max

    print("\nFetching recent Product Hunt posts...")
    while pages < max_pages:
        posts, next_cursor, has_next = fetch_posts(PH_TOKEN, cursor)
        if not posts:
            break

        # Filter by date
        for post in posts:
            created = post.get("createdAt", "")
            try:
                post_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if post_date.replace(tzinfo=None) < cutoff:
                    has_next = False
                    break
            except (ValueError, AttributeError):
                pass
            all_posts.append(post)

        pages += 1
        print(f"  Page {pages}: {len(posts)} posts (total: {len(all_posts)})")

        if not has_next or not next_cursor:
            break
        cursor = next_cursor
        time.sleep(0.5)

    print(f"\nTotal posts fetched: {len(all_posts)}")

    # Match posts against tracked companies
    matched_launches = []
    for post in all_posts:
        name = post.get("name", "")
        tagline = post.get("tagline", "")
        description = post.get("description", "")[:500]
        website = post.get("website", "")
        makers = [m.get("name", "") for m in post.get("makers", [])]
        makers_text = " ".join(makers)

        # Try matching against all text fields
        search_text = f"{name} {tagline} {description} {website} {makers_text}"
        matched_company = match_company(search_text, company_aliases)

        if matched_company:
            topics = [
                t["node"]["name"]
                for t in post.get("topics", {}).get("edges", [])
            ]

            matched_launches.append({
                "company": matched_company,
                "product": name,
                "tagline": tagline,
                "votes": post.get("votesCount", 0),
                "comments": post.get("commentsCount", 0),
                "launchDate": post.get("createdAt", "")[:10],
                "url": post.get("url", ""),
                "topics": topics[:5],
                "makers": makers[:3],
                "source": "producthunt",
            })

    # Sort by votes descending
    matched_launches.sort(key=lambda x: x["votes"], reverse=True)

    print(f"Matched launches from tracked companies: {len(matched_launches)}")

    # Save raw data
    raw_path = DATA_DIR / "product_launches_raw.json"
    with open(raw_path, "w") as f:
        json.dump(matched_launches, f, indent=2)
    print(f"Saved raw data to {raw_path}")

    # Generate JS snippet
    js_lines = [
        "// Auto-generated Product Hunt launch data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"// Matched {len(matched_launches)} launches from tracked companies",
        "const PRODUCT_LAUNCHES_AUTO = [",
    ]

    for launch in matched_launches[:30]:  # Top 30
        tagline = launch["tagline"].replace('"', '\\"').replace('\n', ' ')
        topics_str = json.dumps(launch["topics"])
        makers_str = json.dumps(launch["makers"])
        js_lines.append("  {")
        js_lines.append(f'    company: "{launch["company"]}",')
        js_lines.append(f'    product: "{launch["product"]}",')
        js_lines.append(f'    tagline: "{tagline}",')
        js_lines.append(f'    votes: {launch["votes"]},')
        js_lines.append(f'    comments: {launch["comments"]},')
        js_lines.append(f'    launchDate: "{launch["launchDate"]}",')
        js_lines.append(f'    url: "{launch["url"]}",')
        js_lines.append(f'    topics: {topics_str},')
        js_lines.append(f'    makers: {makers_str},')
        js_lines.append(f'    source: "producthunt",')
        js_lines.append("  },")

    js_lines.append("];")

    js_path = DATA_DIR / "product_launches_auto.js"
    with open(js_path, "w") as f:
        f.write("\n".join(js_lines))
    print(f"Saved JS to {js_path}")

    if matched_launches:
        print(f"\nMatched Product Hunt Launches:")
        for launch in matched_launches[:10]:
            print(f"  {launch['company']:25s} | {launch['product']:30s} | {launch['votes']} votes | {launch['launchDate']}")

    print("=" * 60)


if __name__ == "__main__":
    main()
