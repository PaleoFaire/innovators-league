#!/usr/bin/env python3
"""
Newsletter signal fetcher for the Discovery Pipeline.

Pulls recent posts from elite frontier-tech newsletters via RSS, then
extracts candidate company names using a heuristic NER pass:
  - Capitalized phrases near keywords like "raised", "Series X", "stealth",
    "launched", "emerged from", "$XM", "$XB"
  - Cross-checked against a frontier-tech keyword filter (positive +
    negative keyword scoring)
  - Cross-checked against the existing COMPANIES roster — only NEW names
    are surfaced.

Output: data/newsletter_signals_auto.json — raw candidate mentions with
source attribution. Feeds into build_discovery_queue.py.

This is designed to be high-precision, low-recall: many real new companies
will be missed (Fine — that's what VC portfolio scrapes are for). We only
want signals strong enough to merit human review.
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
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
OUT_PATH = DATA_DIR / "newsletter_signals_auto.json"

# Curated elite frontier-tech newsletters (free RSS).
# Add/remove sources here — runs weekly so it's cheap.
SOURCES = [
    {
        "name": "Core Memory (Ashlee Vance)",
        "url": "https://www.corememory.com/feed",
        "weight": 1.0,  # Highest signal — Vance is THE deeptech voice
    },
    {
        "name": "Newcomer (Eric Newcomer)",
        "url": "https://www.newcomer.co/feed",
        "weight": 0.9,
    },
    {
        "name": "Latent Space (swyx)",
        "url": "https://www.latent.space/feed",
        "weight": 0.85,  # AI/ML focused
    },
    {
        "name": "Construction Physics (Brian Potter)",
        "url": "https://www.construction-physics.com/feed",
        "weight": 0.8,  # Hard tech / manufacturing
    },
    {
        "name": "The Generalist (Mario Gabriele)",
        "url": "https://www.generalist.com/feed",
        "weight": 0.7,
    },
    {
        "name": "Strange Loop Canon (Rohit Krishnan)",
        "url": "https://www.strangeloopcanon.com/feed",
        "weight": 0.7,
    },
    {
        "name": "Not Boring (Packy McCormick)",
        "url": "https://www.notboring.co/feed",
        "weight": 0.6,  # Broader; lower signal-to-noise
    },
    {
        "name": "Asianometry",
        "url": "https://asianometry.substack.com/feed",
        "weight": 0.7,  # Semiconductors + East Asia frontier tech
    },
    {
        "name": "Bismarck Brief (Samo Burja)",
        "url": "https://brief.bismarckanalysis.com/feed",
        "weight": 0.6,
    },
]

# Frontier-tech positive keywords (scoring +1 each)
POSITIVE_KW = {
    "defense", "dual-use", "autonomous", "drone", "swarm", "counter-drone",
    "robot", "robotic", "robotics", "humanoid", "manipulator", "manipulation",
    "satellite", "rocket", "launch", "spacecraft", "in-space", "lunar", "mars",
    "hypersonic", "supersonic", "aerospace", "propulsion", "scramjet", "ramjet",
    "nuclear", "smr", "fission", "fusion", "reactor", "tokamak", "stellarator",
    "quantum", "qubit", "photonic", "neutral atom",
    "biotech", "synthetic biology", "crispr", "gene", "mrna", "cell therapy",
    "semiconductor", "fabless", "asic", "tsmc", "wafer", "chiplet",
    "manufacturing", "foundry", "fabrication", "advanced manufacturing",
    "battery", "lithium", "solid-state", "rare earth", "critical mineral",
    "geothermal", "carbon capture", "direct air capture", "dac",
    "lidar", "radar", "sensor", "isr", "intelligence",
    "sonar", "subsea", "undersea", "maritime", "usv", "underwater",
    "ai chip", "foundation model", "embodied", "world model",
    "directed energy", "high-energy laser", "microwave",
    "additive manufacturing", "3d printing", "metal printing",
}

# Negative keywords — strong signals this is consumer/fintech/crypto/SaaS
NEGATIVE_KW = {
    "marketplace", "e-commerce", "ecommerce", "social network", "dating",
    "creator economy", "content creator", "influencer",
    "fintech", "neobank", "crypto", "nft", "token", "defi", "web3", "dao",
    "gaming", "esports", "metaverse", "vr headset",
    "food delivery", "ride-share", "rideshare", "scooter",
    "retail", "consumer goods", "beauty", "fashion", "lifestyle", "cosmetics",
    "cannabis", "real estate", "real-estate", "mortgage", "lending",
    "newsletter platform", "podcast platform", "streaming",
    "edtech", "edu-tech", "saas tools", "productivity app", "no-code",
    "subscription box", "meal kit", "meal delivery",
}

# Mainstream tech / consumer companies to suppress (these aren't "new" finds)
NOT_INTERESTING_NAMES = {
    "google", "facebook", "meta", "twitter", "x", "amazon", "apple",
    "microsoft", "openai", "anthropic", "stripe", "airbnb", "uber",
    "lyft", "netflix", "spotify", "snap", "shopify", "twilio", "salesforce",
    "instagram", "tiktok", "youtube", "linkedin", "github", "notion",
    "discord", "slack", "zoom", "the verge", "techcrunch", "wired",
    "the information", "bloomberg", "the wall street journal",
    "wall street journal", "new york times", "financial times", "economist",
    "axios", "the new york times", "wired magazine", "reuters", "ap",
    "associated press",
    "tesla", "spacex", "boring", "neuralink", "nvidia", "amd", "intel",
    "qualcomm", "broadcom", "samsung", "tsmc", "asml",
    "the substack", "substack",
}

# Fundraise-context phrases that suggest a company is being announced
TRIGGER_PHRASES = [
    "raised", "raises", "raising", "closed", "closes",
    "stealth", "emerged from stealth", "launched", "launching",
    "series a", "series b", "series c", "series d", "series e",
    "seed round", "pre-seed", "valuation", "ipo", "ipo'd",
    "spinout", "spin-out", "spun out", "founded by", "co-founded",
]

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml",
}

LOOKBACK_DAYS = 14  # Pull last 2 weeks of posts


class StripTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)
    def text(self):
        return " ".join(self.parts)


def strip_html(s):
    if not s:
        return ""
    p = StripTags()
    try:
        p.feed(s)
    except Exception:
        return s
    return p.text()


def fetch_rss(url):
    """Fetch an RSS feed; return list of {title, link, pubDate, summary}."""
    try:
        req = urllib.request.Request(url, headers=HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            xml = r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  ⚠ {url}: {e}")
        return []

    try:
        # Parse with namespace stripping
        xml = re.sub(r' xmlns="[^"]+"', '', xml, count=1)
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        print(f"  ⚠ {url}: XML parse error: {e}")
        return []

    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        # Substack puts content in description and content:encoded
        desc = (item.findtext("description") or "").strip()
        # Try content:encoded too
        for child in item:
            if child.tag.endswith("encoded"):
                if child.text and len(child.text) > len(desc):
                    desc = child.text
                break
        items.append({
            "title": title,
            "link": link,
            "pubDate": pub,
            "summary": strip_html(desc),
        })
    return items


def is_recent(pub_date_str):
    """Parse RFC 822 date and check within LOOKBACK_DAYS."""
    if not pub_date_str:
        return False
    fmts = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
    ]
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    for fmt in fmts:
        try:
            dt = datetime.strptime(pub_date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt > cutoff
        except ValueError:
            pass
    return True  # If we can't parse, default to including


def load_existing_companies():
    """Get a set of lowercase known company names from data.js."""
    if not DATA_JS.exists():
        return set()
    src = DATA_JS.read_text(encoding="utf-8", errors="replace")
    names = set()
    # Pull every name: "..." occurrence — pretty broad but bounded
    for m in re.finditer(r'name:\s*"([^"]+)"', src):
        names.add(m.group(1).strip().lower())
    # Also include common rebrands / abbreviations we want to suppress
    for n in NOT_INTERESTING_NAMES:
        names.add(n.lower())
    return names


# Regex: capture proper-noun-ish phrases (1-3 capitalized words)
# Allows ampersand, hyphens, dots (e.g. "X.AI", "Anduril Industries", "Helion")
PROPER_NOUN_RE = re.compile(
    r"\b((?:[A-Z][a-zA-Z0-9]+(?:[\.\-][A-Z][a-zA-Z0-9]+)*"
    r"(?:\s+[A-Z][a-zA-Z0-9]+){0,2}))\b"
)


STOPWORDS = {
    # Common adjectives + nouns that get capitalized at sentence start
    "humble", "kind", "noble", "great", "modern", "recent", "future", "old",
    "new", "young", "smart", "brave", "honest", "quiet", "loud", "warm",
    "cold", "open", "closed", "free", "premium", "latest", "best", "worst",
    "good", "bad", "better", "worse", "general", "special", "regular",
    "different", "common", "various", "several", "lots", "alone",
    "together", "broad", "narrow", "wide", "long", "short", "small",
    "large", "huge", "massive", "tiny", "fresh", "novel", "real", "true",
    "fake", "false", "right", "wrong", "central", "core", "key", "main",
    "primary", "essential", "critical", "vital", "important",
    # Common pronouns + articles
    "the", "this", "that", "these", "those", "and", "but", "or", "if",
    "i", "we", "you", "they", "he", "she", "it", "our", "their", "his",
    "her", "its", "us", "them", "all", "both", "each", "every", "any",
    "no", "not", "yes", "maybe", "more", "most", "many", "some", "few",
    # Days/months
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
    # Fundraising/business jargon that gets capitalized
    "series", "round", "rounds", "stage", "phase", "company", "companies",
    "startup", "startups", "founder", "founders", "investor", "investors",
    "deal", "deals", "venture", "ventures", "capital", "fund", "funds",
    "vc", "vcs", "lp", "lps", "pe", "ipo", "spac", "saas", "ai",
    "ml", "llm", "llms", "api", "apis", "saas", "b2b", "b2c",
    "other", "others", "another", "next", "last", "first", "second", "third",
    "recently", "today", "tomorrow", "yesterday", "now", "then", "soon",
    "still", "also", "again", "even", "much", "very", "just", "only",
    # Geo
    "us", "uk", "usa", "europe", "asia", "china", "russia", "india", "japan",
    "germany", "france", "italy", "spain", "brazil", "korea", "australia",
    "canada", "mexico", "africa", "north america", "south america",
    "san francisco", "los angeles", "new york", "boston", "chicago",
    "seattle", "austin", "denver", "miami", "washington dc", "washington",
    "silicon valley", "wall street", "main street", "bay area",
    "harvard", "stanford", "mit", "yale", "berkeley", "princeton", "caltech",
    "carnegie mellon", "carnegie", "oxford", "cambridge", "eth",
    # Major tech that's not "frontier"
    "google", "facebook", "meta", "twitter", "x", "amazon", "apple",
    "microsoft", "openai", "anthropic", "stripe", "airbnb", "uber",
    "lyft", "netflix", "spotify", "snap", "shopify", "twilio", "salesforce",
    "instagram", "tiktok", "youtube", "linkedin", "github", "notion",
    "discord", "slack", "zoom", "tesla", "nvidia", "amd", "intel",
    # Anthropic / OpenAI model names (commonly mentioned but not new companies)
    "claude", "claude opus", "claude sonnet", "claude haiku",
    "gpt", "gpt-3", "gpt-4", "gpt-5", "chatgpt", "dall-e", "sora",
    "gemini", "bard", "llama", "mistral", "command", "command-r", "cohere",
    "opus", "sonnet", "haiku",
    # Tools / products / generic terms
    "cursor", "copilot", "codex", "windsurf", "v0", "replit",
    "react", "vue", "angular", "node", "python", "javascript", "typescript",
    "docker", "kubernetes", "terraform", "aws", "gcp", "azure",
    # Misc proper-noun false positives
    "techcrunch", "bloomberg", "reuters", "axios", "the verge",
    "the information", "wired", "the new york times", "wall street journal",
    "financial times", "economist", "ft", "wsj", "nyt", "ap",
    "associated press", "the wall street journal",
    # Major orgs / agencies / military bodies (not startups)
    "nato", "un", "unesco", "who", "imf", "world bank", "european union",
    "european commission", "eu", "fbi", "cia", "nsa", "dod", "doj", "fcc",
    "fda", "epa", "sec", "irs", "doe", "dot", "dhs", "tsa", "usda",
    "white house", "capitol hill", "congress", "senate", "house",
    "supreme court", "pentagon", "state department", "treasury",
    "department of defense", "department of energy", "department of state",
    "u.s. air force", "us air force", "u.s. navy", "us navy", "us army",
    "u.s. army", "marine corps", "space force", "coast guard",
    # VC / investor entity names that capitalize-pattern-match
    "andreessen horowitz", "founders fund", "khosla ventures", "lux capital",
    "sequoia", "sequoia capital", "kleiner perkins", "bessemer",
    "general catalyst", "8vc", "thrive capital", "y combinator", "yc",
    "first round", "lightspeed", "accel", "benchmark", "greylock",
    "index ventures", "insight partners", "tiger global", "softbank",
    "vista", "blackstone", "kkr", "carlyle",
    # a16z thesis terms / common topics that aren't companies
    "american dynamism", "deep tech", "deeptech", "frontier tech",
    "industrial revolution", "manhattan project", "moonshot",
    "operation warp speed", "operation baltic sentry",
    # AI agents / model releases that get capitalized
    "agent lee", "agent kim", "agent foo",  # placeholder pattern
}

# Words that, if they're the LAST word in the candidate, indicate it's a VC
# firm or fund, not a startup
VC_FIRM_SUFFIXES = {
    "capital", "ventures", "partners", "fund", "funds", "vc", "investments",
    "holdings", "equity", "advisors", "management",
}


def is_vc_firm(name):
    last = name.split()[-1].lower()
    return last in VC_FIRM_SUFFIXES


def looks_like_company(name, known_names):
    """Filter out obvious non-company candidates."""
    name_lower = name.lower()
    if len(name) < 3 or len(name) > 60:
        return False
    if name_lower in known_names:
        return False
    # Skip if a known company name is a prefix (e.g. "Fervo Energy Files"
    # contains "Fervo Energy" which is already in DB)
    words = name_lower.split()
    for n in range(len(words), 0, -1):
        prefix = " ".join(words[:n])
        if prefix in known_names and len(words) > n:
            return False
    if name_lower in STOPWORDS:
        return False
    if is_vc_firm(name):
        return False
    words = name.split()
    # Filter: starts with stopword (e.g. "The Frontier", "Basically REXIS")
    first = words[0].lower()
    if first in STOPWORDS:
        return False
    # Skip if all words are stopwords
    if all(w.lower() in STOPWORDS for w in words):
        return False
    # Filter: starts with common adverb/adjective patterns that prefix nouns
    # ("Basically", "Recently", "Today", "Mostly", etc.)
    BAD_LEADERS = {
        "basically", "essentially", "actually", "literally", "really",
        "obviously", "ultimately", "eventually", "generally", "broadly",
        "specifically", "notably", "interestingly", "surprisingly",
        "ideally", "personally", "honestly", "frankly", "additionally",
        "further", "furthermore", "moreover", "however", "therefore",
        "thus", "hence", "consequently", "meanwhile", "afterwards",
    }
    if first in BAD_LEADERS:
        return False
    # Filter: 2-word names that look like "Operation X" or "Project X"
    # — usually military operations, not companies
    if len(words) >= 2 and first in {"operation", "project", "program",
                                     "mission", "task", "force", "team",
                                     "group", "department", "agency",
                                     "office", "bureau", "ministry"}:
        return False
    # Filter: names ending in common org-suffix patterns
    if words[-1].lower() in {"corporation", "corp", "incorporated", "inc",
                             "limited", "ltd", "llc", "gmbh"}:
        # These are real companies, but should already be in our DB if so
        return name_lower not in known_names
    return True


def extract_candidates(title, summary, source_weight, known_names):
    """Find candidate company mentions in a post.

    Returns list of dicts: {name, context, score}.
    """
    text = f"{title}\n{summary}"
    text_lower = text.lower()

    # Check at least one trigger phrase
    has_trigger = any(t in text_lower for t in TRIGGER_PHRASES)
    if not has_trigger:
        return []

    candidates = {}
    for match in PROPER_NOUN_RE.finditer(text):
        name = match.group(1).strip()
        if not looks_like_company(name, known_names):
            continue

        # Look at the context window around the match (200 chars)
        i = match.start()
        window = text[max(0, i - 200):min(len(text), i + 200)].lower()
        # Tighter window for trigger proximity (50 chars before/after the name)
        tight_window = text[max(0, i - 80):min(len(text), i + 80)].lower()

        # Count positive vs negative keywords in window
        pos = sum(1 for kw in POSITIVE_KW if kw in window)
        neg = sum(1 for kw in NEGATIVE_KW if kw in window)
        ft_score = pos - neg

        # Trigger proximity: in tight window only counts (must be very close)
        trigger_proximity = 0
        for t in TRIGGER_PHRASES:
            if t in tight_window:
                trigger_proximity = 1
                break

        # Stricter gate: require at least 2 frontier-tech keywords AND a tight
        # trigger proximity. Was 1 keyword + any trigger before; too noisy.
        if ft_score < 2 or trigger_proximity == 0:
            continue

        # Bonus: if the name is IMMEDIATELY before/after a fundraising verb
        # (e.g. "Foo raised", "stealth Foo"), much higher confidence
        # Look at 30-char window
        very_tight = text[max(0, i - 40):min(len(text), i + 40)].lower()
        immediate_signal = 0
        for t in ["raised", "raises", "stealth", "emerged", "launched", "spinout", "spin-out"]:
            if t in very_tight:
                immediate_signal = 1
                break

        score = (ft_score * 2 + trigger_proximity * 3 + immediate_signal * 5) * source_weight

        if name in candidates:
            candidates[name]["score"] += score
            candidates[name]["mentions"] += 1
        else:
            candidates[name] = {
                "name": name,
                "score": score,
                "frontierTechScore": ft_score,
                "context": text[max(0, i - 100):min(len(text), i + 100)],
                "mentions": 1,
            }
    return list(candidates.values())


def main():
    print("=" * 64)
    print("Newsletter Signal Fetcher · Discovery Pipeline Phase 1")
    print("=" * 64)

    known = load_existing_companies()
    print(f"  Loaded {len(known)} known company names from data.js")

    all_signals = []
    sources_used = []
    for src in SOURCES:
        print(f"\n  → {src['name']}: ", end="", flush=True)
        items = fetch_rss(src["url"])
        if not items:
            print("0 items")
            continue
        recent = [it for it in items if is_recent(it.get("pubDate"))]
        print(f"{len(items)} items, {len(recent)} recent")
        sources_used.append({
            "name": src["name"],
            "url": src["url"],
            "totalItems": len(items),
            "recentItems": len(recent),
        })

        for item in recent:
            cands = extract_candidates(
                item["title"], item["summary"],
                src["weight"], known
            )
            for c in cands:
                all_signals.append({
                    "name": c["name"],
                    "score": round(c["score"], 2),
                    "frontierTechScore": c["frontierTechScore"],
                    "mentions": c["mentions"],
                    "context": c["context"][:300],
                    "source": src["name"],
                    "sourceUrl": src["url"],
                    "articleTitle": item["title"],
                    "articleUrl": item["link"],
                    "articleDate": item["pubDate"],
                })

        time.sleep(0.5)  # Rate-limit politeness

    # De-dupe per (name, source) — keep highest score per source
    by_key = {}
    for s in all_signals:
        k = (s["name"].lower(), s["source"])
        if k not in by_key or s["score"] > by_key[k]["score"]:
            by_key[k] = s
    deduped = list(by_key.values())

    # Aggregate per company name across sources (so we can spot multi-source hits)
    by_name = {}
    for s in deduped:
        n = s["name"]
        if n not in by_name:
            by_name[n] = {
                "name": n,
                "totalScore": 0,
                "sourceCount": 0,
                "signals": [],
            }
        by_name[n]["totalScore"] += s["score"]
        by_name[n]["sourceCount"] += 1
        by_name[n]["signals"].append(s)

    aggregated = sorted(by_name.values(), key=lambda x: -x["totalScore"])

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "lookbackDays": LOOKBACK_DAYS,
        "sources": sources_used,
        "totalRawSignals": len(all_signals),
        "uniqueCandidateCount": len(by_name),
        "candidates": aggregated,
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(f"\n✅ Wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"   {out['totalRawSignals']} raw signals → {out['uniqueCandidateCount']} unique candidates")
    if aggregated:
        print(f"\n  Top 10 candidates:")
        for c in aggregated[:10]:
            sources = ", ".join(set(s["source"].split(" (")[0] for s in c["signals"]))
            print(f"    [{c['totalScore']:>6.2f}] {c['name']:<40} ({c['sourceCount']} signals — {sources})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
