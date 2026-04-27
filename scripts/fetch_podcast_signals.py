#!/usr/bin/env python3
"""
Podcast Episode Scout — the source that would have caught Panthalassa.

Pulls episode titles + descriptions from elite frontier-tech podcasts.
Each episode typically features ONE company — the title literally names it.
This is much higher signal than newsletter NER because podcast titles are
declarative ("Building floating AI data centers — Panthalassa CEO Garth
Sheldon-Coulson") vs Substack prose mentions buried in articles.

Sources (curated — focused on technical depth, not VC chat):
  - Core Memory (Ashlee Vance) — the primary source we missed
  - Acquired (Ben + David)
  - Invest Like the Best (Patrick O'Shaughnessy)
  - The Logan Bartlett Show
  - Founders Podcast (David Senra)
  - Lex Fridman
  - 20VC (Harry Stebbings)
  - American Optimist (Joe Lonsdale)
  - All-In Podcast (selected episodes)
  - The TWIST Podcast (Jason Calacanis)
  - The David Senra Founders show
  - The Information's TITV
  - Bg2 Pod (Bill Gurley + Brad Gerstner)

Strategy: pull episode titles via RSS, extract company names with NER-lite,
de-dupe against COMPANIES, output candidates to data/podcast_signals_auto.json.
"""

import json
import re
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "data.js"
OUT_PATH = ROOT / "data" / "podcast_signals_auto.json"

# Curated podcast RSS feeds — focused on technical depth + frontier tech
PODCASTS = [
    {
        "name": "Core Memory",
        "host": "Ashlee Vance",
        "url": "https://www.corememory.com/feed/podcast/320996.rss",  # Substack-hosted RSS
        "weight": 1.0,  # Highest weight — Vance's coverage is the gold standard
    },
    {
        "name": "Acquired",
        "host": "Ben Gilbert + David Rosenthal",
        "url": "https://feeds.transistor.fm/acquired",
        "weight": 0.8,
    },
    {
        "name": "Invest Like the Best",
        "host": "Patrick O'Shaughnessy",
        "url": "https://feeds.megaphone.fm/investlikethebest",
        "weight": 0.8,
    },
    {
        "name": "20VC",
        "host": "Harry Stebbings",
        "url": "https://thetwentyminutevc.libsyn.com/rss",
        "weight": 0.7,
    },
    {
        "name": "American Optimist",
        "host": "Joe Lonsdale",
        "url": "https://american-optimist.simplecast.com/podcast.rss",
        "weight": 0.85,  # Frontier-tech focused — same orbit as Stephen
    },
    {
        "name": "All-In",
        "host": "Chamath/Jason/Sacks/Friedberg",
        "url": "https://allinchamathjason.libsyn.com/rss",
        "weight": 0.5,  # Lower weight — broader topics, less frontier-specific
    },
    {
        "name": "Lex Fridman Podcast",
        "host": "Lex Fridman",
        "url": "https://lexfridman.com/feed/podcast/",
        "weight": 0.7,  # AI/robotics focus
    },
    # Removed sources with broken/changed RSS endpoints (BG2 Pod, Modern Wisdom,
    # Logan Bartlett Show, TWIST). To re-add: find current RSS via the
    # podcast's web page. Many switched providers in 2024-25.
    {
        "name": "TBPN",
        "host": "John Coogan + Jordi Hays",
        "url": "https://feeds.transistor.fm/technology-brother",
        "weight": 0.95,  # Very high signal — daily live tech show, specifically
                          # surfaces frontier-tech founders. Acquired by OpenAI 4/2026.
    },
]

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml",
}

LOOKBACK_DAYS = 60  # Podcasts release weekly; pull last 2 months


class StripTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)
    def text(self):
        return " ".join(self.parts)


def strip_html(s):
    if not s: return ""
    p = StripTags()
    try:
        p.feed(s)
    except Exception:
        return s
    return p.text()


def fetch_rss(url):
    """Fetch a podcast RSS feed."""
    try:
        req = urllib.request.Request(url, headers=HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            xml = r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  ⚠ {url}: {e}")
        return []
    try:
        xml = re.sub(r' xmlns="[^"]+"', '', xml, count=1)
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        print(f"  ⚠ {url}: parse error: {e}")
        return []
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        desc = (item.findtext("description") or "").strip()
        for child in item:
            if child.tag.endswith("encoded"):
                if child.text and len(child.text) > len(desc):
                    desc = child.text
        items.append({
            "title": title,
            "link": link,
            "pubDate": pub,
            "summary": strip_html(desc)[:1500],
        })
    return items


def is_recent(pub_date_str):
    if not pub_date_str: return False
    fmts = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
    ]
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    for fmt in fmts:
        try:
            dt = datetime.strptime(pub_date_str.strip(), fmt)
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            return dt > cutoff
        except ValueError: pass
    return True


def load_existing_companies():
    if not DATA_JS.exists(): return set()
    src = DATA_JS.read_text(encoding="utf-8", errors="replace")
    names = set()
    for m in re.finditer(r'name:\s*"([^"]+)"', src):
        n = m.group(1).strip().lower()
        names.add(n)
        # Also add no-space variant
        names.add(re.sub(r'[\s\-_\.]+', '', n))
    # Common false-positive names not to flag
    SUPPRESS = {
        "google", "amazon", "apple", "facebook", "meta", "openai",
        "anthropic", "tesla", "spacex", "neuralink", "stripe",
        "uber", "airbnb", "twitter", "x", "the", "this", "all",
        "about", "google search", "youtube", "tiktok", "instagram",
        "netflix", "spotify", "discord", "slack", "github", "linkedin",
        "cnbc", "bloomberg", "wsj", "nyt", "the new york times",
        "techcrunch", "cnn", "bbc", "fox", "reuters", "axios",
        "core memory", "acquired", "20vc", "all-in", "tbpn",
        "the logan bartlett show", "american optimist", "bg2",
        "ashlee vance", "ben gilbert", "david rosenthal", "patrick",
        "harry stebbings", "joe lonsdale", "lex fridman", "logan",
    }
    names |= SUPPRESS
    return names


# Episode title patterns: "Foo CEO Bar Baz" / "Building X — Foo CEO Bar"
# We extract the company name as a capitalized phrase, often near "CEO",
# "founder", "co-founder", em-dash, or in episode-number prefix.

# Match "EP 65 Garth Sheldon-Coulson" → person, but title also has "Panthalassa"
# Pattern: Capitalized 1-3 words before/after "CEO|founder|co-founder|builds?|building"
COMPANY_HINTS = [
    # "<Company> CEO/founder Bar"
    (r"\b([A-Z][A-Za-z0-9\-]+(?:\s+[A-Z][A-Za-z0-9\-]+){0,2})\s+(?:CEO|founder|Founder|co-founder|Co-Founder|cofounder|Co-founder)", 1),
    # "Company:  Description" / "Company —  Description" (title patterns)
    (r"^([A-Z][A-Za-z0-9\-]+(?:\s+[A-Z][A-Za-z0-9\-]+){0,2}):\s", 1),
    (r"^([A-Z][A-Za-z0-9\-]+(?:\s+[A-Z][A-Za-z0-9\-]+){0,2})\s+[—\-:]\s", 1),
    # "with <Company>'s CEO/founder" (mid-title)
    (r"with\s+([A-Z][A-Za-z0-9\-]+(?:\s+[A-Z][A-Za-z0-9\-]+){0,2})'s\s+(?:CEO|founder)", 1),
    # "Building <something> at <Company>"
    (r"\bat\s+([A-Z][A-Za-z0-9\-]+(?:\s+[A-Z][A-Za-z0-9\-]+){0,2})\b", 1),
    # "<Company> -" at episode title start (very common)
    (r"\bEP\s*\d+\s+([A-Z][A-Za-z0-9\-]+(?:\s+[A-Z][A-Za-z0-9\-]+){0,2})", 1),
]

# Frontier-tech keywords — boost score if context contains them
FRONTIER_KW = [
    "ocean", "wave", "energy", "nuclear", "fusion", "reactor",
    "quantum", "satellite", "rocket", "space", "lunar", "mars",
    "drone", "autonomous", "robot", "humanoid", "ai", "compute",
    "biotech", "gene", "crispr", "mrna", "molecular", "synthetic",
    "defense", "weapon", "missile", "hypersonic", "supersonic",
    "semiconductor", "chip", "fabless", "wafer",
    "manufacturing", "factory", "additive", "3d printing",
    "battery", "lithium", "geothermal", "carbon capture", "dac",
    "hardware", "deep tech", "deeptech", "frontier",
    "stealth", "first time", "first interview", "exclusive",
]


def extract_companies(title, summary, known):
    """Return list of (company_name, context, score)."""
    text = f"{title}\n{summary}"
    text_lower = text.lower()
    candidates = {}

    # Strong signal: title pattern matches
    for pattern, group in COMPANY_HINTS:
        for m in re.finditer(pattern, title):
            name = m.group(group).strip()
            if not is_plausible_company(name, known): continue
            candidates.setdefault(name, {"name": name, "score": 0,
                                         "matchedPattern": pattern,
                                         "context": title[:200]})
            candidates[name]["score"] += 5

    # Frontier-tech keyword density boost
    ft_kws = sum(1 for kw in FRONTIER_KW if kw in text_lower)
    if ft_kws >= 3:
        for c in candidates.values():
            c["score"] += 5
    elif ft_kws >= 1:
        for c in candidates.values():
            c["score"] += 2

    return list(candidates.values())


def is_plausible_company(name, known):
    """Filter out obvious non-companies."""
    if not name or len(name) < 3 or len(name) > 50: return False
    nl = name.lower()
    if nl in known: return False
    # Strip common prefixes/suffixes
    if nl in {"the", "this", "a", "an", "with", "about", "and", "or"}: return False
    # Single all-lowercase word? Probably not a name
    if name == name.lower(): return False
    # Person-name heuristic: contains common first names → reject
    PERSON_FIRST = {"garth", "ashlee", "ben", "david", "patrick", "harry",
                    "joe", "lex", "logan", "elon", "peter", "marc",
                    "sam", "alex", "matt", "michael", "john", "james",
                    "robert", "daniel", "andrew", "jason", "chamath",
                    "brian", "chris", "ryan", "jeff", "bill", "brad",
                    "katherine", "bobby"}
    first_word = name.split()[0].lower()
    if first_word in PERSON_FIRST: return False
    # Must look company-like (not all stopwords)
    return True


def main():
    print("=" * 64)
    print("Podcast Episode Scout · Discovery Phase 2")
    print("=" * 64)

    known = load_existing_companies()
    print(f"  Roster: {len(known)} known names")

    all_candidates = []
    sources_used = []
    for pod in PODCASTS:
        print(f"\n  → {pod['name']} ({pod['host']}): ", end="", flush=True)
        items = fetch_rss(pod["url"])
        if not items:
            print("0 items")
            continue
        recent = [it for it in items if is_recent(it.get("pubDate"))]
        print(f"{len(items)} items, {len(recent)} recent")
        sources_used.append({
            "name": pod["name"],
            "host": pod["host"],
            "url": pod["url"],
            "totalItems": len(items),
            "recentItems": len(recent),
        })
        for item in recent:
            cands = extract_companies(item["title"], item["summary"], known)
            for c in cands:
                c["score"] *= pod["weight"]
                c["source"] = pod["name"]
                c["sourceHost"] = pod["host"]
                c["episodeTitle"] = item["title"][:200]
                c["episodeUrl"] = item["link"]
                c["episodeDate"] = item["pubDate"]
                all_candidates.append(c)
        time.sleep(0.5)

    # Aggregate per company name
    by_name = {}
    for s in all_candidates:
        n = s["name"]
        if n not in by_name:
            by_name[n] = {"name": n, "score": 0, "episodes": []}
        by_name[n]["score"] += s["score"]
        by_name[n]["episodes"].append({
            "podcast": s["source"],
            "host": s["sourceHost"],
            "title": s["episodeTitle"],
            "url": s["episodeUrl"],
            "date": s["episodeDate"],
            "context": s["context"][:200],
        })

    aggregated = sorted(by_name.values(), key=lambda x: -x["score"])

    # ALSO save raw episode feed — every recent episode title + url across
    # all podcasts. Stephen can scan this manually (5 mins / week) to catch
    # signals our NER misses. This is how Panthalassa would have been caught:
    # "EP 65 Garth Sheldon-Coulson" → click → see Panthalassa in description.
    raw_episodes = []
    for pod in PODCASTS:
        items = fetch_rss(pod["url"])
        if not items: continue
        recent = [it for it in items if is_recent(it.get("pubDate"))]
        for item in recent[:20]:  # Cap per-podcast to avoid huge file
            raw_episodes.append({
                "podcast": pod["name"],
                "host": pod["host"],
                "title": item["title"][:200],
                "url": item["link"],
                "date": item["pubDate"],
                "summary": item["summary"][:400],
            })
    raw_episodes.sort(key=lambda x: x["date"], reverse=True)

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "lookbackDays": LOOKBACK_DAYS,
        "sources": sources_used,
        "totalRawSignals": len(all_candidates),
        "uniqueCandidates": len(by_name),
        "candidates": aggregated,
        "rawEpisodes": raw_episodes,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(f"\n✅ Wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"   {len(all_candidates)} raw signals → {len(by_name)} unique candidates")
    if aggregated:
        print(f"\n  Top 10 podcast-discovered candidates:")
        for c in aggregated[:10]:
            podcasts = sorted(set(e["podcast"] for e in c["episodes"]))
            print(f"    [{c['score']:>5.1f}] {c['name']:<40}  ({len(c['episodes'])}× from {', '.join(podcasts)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
