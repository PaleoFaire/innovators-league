#!/usr/bin/env python3
"""
Reddit Discussion Trends
========================
Polls the public JSON API for a curated set of subreddits and filters
top posts for mentions of tracked frontier-tech companies. No auth
required — we use reddit.com/r/{sub}/top.json with a polite user
agent to avoid 429s.

Output:
    data/reddit_mentions_auto.json
    data/reddit_mentions_status.json

Run standalone:
    python3 scripts/fetch_reddit.py
"""

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover
    from urllib3.util import Retry  # type: ignore


# ─────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("reddit")


# ─────────────────────────────────────────────────────────────────
# Paths and config
# ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
MASTER_LIST_PATH = SCRIPT_DIR / "company_master_list.js"

SUBREDDITS = [
    "investing",
    "SpaceXLounge",
    "Futurology",
    "nuclear",
    "robotics",
    "geopolitics",
    "stocks",
]

TIME_WINDOW = "week"  # hour, day, week, month, year, all
POST_LIMIT = 50
REQUEST_TIMEOUT = 20


def _make_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=2.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    # Non-default UA avoids reddit's anonymous-UA throttling
    session.headers.update({
        "User-Agent": "ROS-Innovators-League/1.0",
        "Accept": "application/json",
    })
    return session


SESSION = _make_session()


# ─────────────────────────────────────────────────────────────────
# Master company list
# ─────────────────────────────────────────────────────────────────
def load_master_companies():
    if not MASTER_LIST_PATH.exists():
        logger.warning("company_master_list.js not found")
        return []
    content = MASTER_LIST_PATH.read_text()
    companies = []
    pattern = r'\{\s*name:\s*"([^"]+)",\s*aliases:\s*\[([^\]]*)\]'
    for match in re.finditer(pattern, content):
        name = match.group(1)
        aliases_raw = match.group(2)
        aliases = [a.strip().strip('"') for a in aliases_raw.split(",") if a.strip()]
        companies.append({"name": name, "aliases": aliases})
    logger.info("Loaded %d companies from master list", len(companies))
    return companies


MASTER_COMPANIES = load_master_companies()

GENERIC_ALIAS_STOPWORDS = {
    "aging", "allies", "arctic", "array", "atomic", "audio", "beacon",
    "carbon", "charge", "condor", "desert", "energy", "fabric", "falcon",
    "forge", "fusion", "garden", "ghost", "global", "harbor", "ignite",
    "impact", "launch", "matter", "merge", "neural", "ocean", "orbit",
    "radar", "radiant", "rocket", "scout", "shield", "signal", "solar",
    "space", "spark", "target", "terra", "tower", "vapor", "vertex",
}


def find_matching_companies(text):
    if not text or not MASTER_COMPANIES:
        return []
    text_lower = text.lower()
    matched = []
    seen = set()
    for company in MASTER_COMPANIES:
        name = company["name"]
        if name in seen:
            continue
        name_lower = name.lower()
        if len(name_lower) >= 6:
            if name_lower in text_lower:
                matched.append(name)
                seen.add(name)
                continue
        else:
            if re.search(r"\b" + re.escape(name_lower) + r"\b", text_lower):
                matched.append(name)
                seen.add(name)
                continue
        for alias in company["aliases"]:
            alias_lower = alias.lower()
            if len(alias_lower) < 5 or alias_lower in GENERIC_ALIAS_STOPWORDS:
                continue
            if alias_lower in text_lower:
                matched.append(name)
                seen.add(name)
                break
    return matched


# ─────────────────────────────────────────────────────────────────
# Reddit JSON fetcher
# ─────────────────────────────────────────────────────────────────
def fetch_subreddit_top(sub, t=TIME_WINDOW, limit=POST_LIMIT):
    url = f"https://www.reddit.com/r/{sub}/top.json?t={t}&limit={limit}"
    try:
        resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return [], f"HTTP {resp.status_code}"
        payload = resp.json()
    except requests.exceptions.RequestException as e:
        return [], str(e)
    except ValueError as e:
        return [], f"json error: {e}"

    posts = []
    for child in payload.get("data", {}).get("children", []):
        data = child.get("data", {}) or {}
        posts.append({
            "id": data.get("id"),
            "title": data.get("title", ""),
            "selftext": (data.get("selftext", "") or "")[:1500],
            "url": f"https://reddit.com{data.get('permalink', '')}",
            "score": data.get("score", 0) or 0,
            "comments": data.get("num_comments", 0) or 0,
            "created_utc": data.get("created_utc", 0) or 0,
            "subreddit": data.get("subreddit", sub),
            "author": data.get("author", ""),
        })
    return posts, None


# ─────────────────────────────────────────────────────────────────
# File I/O
# ─────────────────────────────────────────────────────────────────
def save_json(data, filename):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %s (%d bytes)", path, path.stat().st_size)


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 60)
    logger.info("Reddit Discussion Trends")
    logger.info("=" * 60)
    logger.info("Subreddits: %s", ", ".join(SUBREDDITS))

    started_at = datetime.now(timezone.utc).isoformat()
    sub_status = []
    all_posts = []

    for sub in SUBREDDITS:
        logger.info("Fetching r/%s ...", sub)
        posts, err = fetch_subreddit_top(sub)
        sub_status.append({
            "subreddit": sub,
            "posts_fetched": len(posts),
            "error": err,
        })
        logger.info("  -> %d posts", len(posts))
        all_posts.extend(posts)
        # Reddit is firm about ~1 req/sec for anonymous JSON
        time.sleep(1.5)

    logger.info("Total posts fetched: %d", len(all_posts))

    # Filter to posts that mention a tracked company
    mentions = []
    for p in all_posts:
        combined = f"{p['title']} {p['selftext']}"
        matches = find_matching_companies(combined)
        if not matches:
            continue
        dt = datetime.fromtimestamp(p["created_utc"], tz=timezone.utc) \
            if p["created_utc"] else None
        date_str = dt.strftime("%Y-%m-%d") if dt else ""
        for company in matches:
            mentions.append({
                "company": company,
                "subreddit": p["subreddit"],
                "title": p["title"][:250],
                "url": p["url"],
                "score": p["score"],
                "comments": p["comments"],
                "date": date_str,
                "author": p["author"],
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

    # Sort newest first, then highest score
    mentions.sort(key=lambda m: (m.get("date", ""), m.get("score", 0)),
                  reverse=True)

    logger.info("Relevant mentions: %d", len(mentions))
    save_json(mentions, "reddit_mentions_auto.json")

    status = {
        "script": "fetch_reddit.py",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "subreddits": sub_status,
        "total_posts": len(all_posts),
        "total_mentions": len(mentions),
        "ok": any(s["posts_fetched"] > 0 for s in sub_status),
    }
    save_json(status, "reddit_mentions_status.json")

    if mentions:
        logger.info("\nMost-mentioned companies:")
        counts = {}
        for m in mentions:
            counts[m["company"]] = counts.get(m["company"], 0) + 1
        for c, n in sorted(counts.items(), key=lambda x: -x[1])[:10]:
            logger.info("  %-25s %d", c[:25], n)
        logger.info("\nTop scoring mentions:")
        for m in sorted(mentions, key=lambda x: -x.get("score", 0))[:5]:
            logger.info("  [%4d] r/%-15s %s",
                        m["score"], m["subreddit"][:15],
                        m["title"][:80])

    logger.info("=" * 60)
    logger.info("Done.")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        save_json({
            "script": "fetch_reddit.py",
            "ok": False,
            "fatal_error": str(e),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }, "reddit_mentions_status.json")
        raise
