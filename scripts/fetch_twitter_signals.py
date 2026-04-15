#!/usr/bin/env python3
"""
Twitter/X Signals Fetcher
=========================
Tracks the X/Twitter presence of founders of companies in the frontier tech
database. Writes `data/twitter_signals_auto.json` as an array of records:

    {
        "founder": "Palmer Luckey",
        "company": "Anduril Industries",
        "handle": "@PalmerLuckey",
        "followers": 285000,
        "recent_posts": 15,
        "topics": ["Lattice OS", "defense"],
        "fetched_at": "2026-04-15T10:05:00Z"
    }

Data source selection (first available wins):
  1. X_BEARER_TOKEN  -> official X API v2 (Basic tier, $100/mo)
  2. APIFY_TOKEN     -> Apify 'apify/twitter-scraper' (cheap pay-as-you-go)
  3. RAPIDAPI_KEY    -> RapidAPI Twitter mirrors (free tier)
  4. None            -> placeholder mode with STRUCTURED DATA: one record per
                       top founder, flagged so downstream knows the shape but
                       that fields are empty

Only the TOP 100 founders are tracked per run, scored by:
  - featured flag (+40)
  - ticker is public (+20)
  - fundingStage at Series C+ (+15)
  - valuation >= $1B (+15)
  - tbpnMentioned (+10)

This keeps API usage well inside free tiers.
"""

import json
import logging
import os
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


# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("twitter_signals")

# ─── Paths ───
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DATA_JS_PATH = SCRIPT_DIR.parent / "data.js"
MASTER_LIST_PATH = SCRIPT_DIR / "company_master_list.js"

# ─── Secrets ───
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "").strip()
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "").strip()
X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN", "").strip()

TOP_N = 100
REQUEST_TIMEOUT = 45


def _make_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=2.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "InnovatorsLeague-TwitterFetcher/2.0",
        "Accept": "application/json",
    })
    return session


SESSION = _make_session()


# ─────────────────────────────────────────────────────────────────
# Data source selection
# ─────────────────────────────────────────────────────────────────
def available_data_source():
    if X_BEARER_TOKEN:
        return "x_api_v2"
    if APIFY_TOKEN:
        return "apify"
    if RAPIDAPI_KEY:
        return "rapidapi"
    return None


# ─────────────────────────────────────────────────────────────────
# Founder loading & ranking
# ─────────────────────────────────────────────────────────────────
def _parse_data_js_founders():
    """
    Extract (company, founder, attrs) tuples from data.js.
    attrs: fundingStage, valuation, tbpnMentioned, featured, ticker.
    """
    if not DATA_JS_PATH.exists():
        return []
    content = DATA_JS_PATH.read_text()
    founders = []

    # Split data.js roughly by company blocks (each block starts with `name: "..."`)
    # Not perfectly parseable but works for the structure we have.
    block_re = re.compile(
        r'name:\s*"(?P<name>[^"]+)"(?P<body>.*?)(?=(?:\n\s*\{|\n\s*\]\s*;))',
        re.DOTALL,
    )
    def _extract(body, key, is_bool=False):
        m = re.search(rf'{key}:\s*"([^"]*)"', body)
        if m:
            return m.group(1)
        if is_bool:
            m = re.search(rf'{key}:\s*(true|false)', body)
            if m:
                return m.group(1) == "true"
        m = re.search(rf'{key}:\s*([^,\n]+)', body)
        if m:
            return m.group(1).strip()
        return None

    for m in block_re.finditer(content):
        name = m.group("name").strip()
        body = m.group("body")
        founder_raw = _extract(body, "founder")
        if not founder_raw or founder_raw.lower() in {"null", "unknown", "n/a", ""}:
            continue
        # If founder is a comma-separated list ("Palmer Luckey, Brian Schimpf, ..."),
        # use the FIRST name only — handle guessing on concatenated names yields junk.
        founder = founder_raw.split(",")[0].strip()
        # Strip titles / post-nominals like "PhD", "Dr.", etc
        founder = re.sub(r"^(Dr\.?|Prof\.?|Mr\.?|Ms\.?|Mrs\.?)\s+", "", founder, flags=re.I)
        founder = re.sub(r",?\s*(PhD|Ph\.D\.?|MD|MBA|Esq\.?)$", "", founder, flags=re.I).strip()
        if not founder:
            continue
        founders.append({
            "company": name,
            "founder": founder,
            "fundingStage": _extract(body, "fundingStage") or "",
            "valuation": _extract(body, "valuation") or "",
            "tbpnMentioned": _extract(body, "tbpnMentioned", is_bool=True) is True,
            "featured": _extract(body, "featured", is_bool=True) is True,
            "ticker": _extract(body, "ticker") or "",
        })

    # Dedup by (company, founder)
    seen = set()
    unique = []
    for f in founders:
        key = (f["company"], f["founder"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(f)
    return unique


def _parse_valuation_to_billions(val):
    if not val:
        return 0.0
    s = str(val).upper().replace("$", "").replace(",", "").strip()
    s = s.replace("+", "")
    mult = 1.0
    if "T" in s:
        mult = 1000.0
        s = s.replace("T", "")
    elif "B" in s:
        mult = 1.0
        s = s.replace("B", "")
    elif "M" in s:
        mult = 0.001
        s = s.replace("M", "")
    try:
        return float(s) * mult
    except ValueError:
        return 0.0


def _score_founder(f):
    score = 0
    if f.get("featured"):
        score += 40
    if f.get("ticker"):
        score += 20
    stage = (f.get("fundingStage") or "").lower()
    if any(st in stage for st in ("series c", "series d", "series e", "series f", "series g",
                                   "series h", "series i", "series j", "public", "ipo",
                                   "pre-ipo", "growth", "late stage")):
        score += 15
    val_b = _parse_valuation_to_billions(f.get("valuation"))
    if val_b >= 1.0:
        score += 15
    if val_b >= 10.0:
        score += 10
    if f.get("tbpnMentioned"):
        score += 10
    return score


def load_top_founders(limit=TOP_N):
    founders = _parse_data_js_founders()
    scored = [(_score_founder(f), f) for f in founders]
    scored.sort(key=lambda x: -x[0])
    top = [f for _score, f in scored[:limit]]
    logger.info("Loaded %d founders; top %d by score selected", len(founders), len(top))
    return top


# ─────────────────────────────────────────────────────────────────
# Handle guessing
# ─────────────────────────────────────────────────────────────────
def guess_handles(founder_name):
    parts = [p for p in re.split(r"\s+", founder_name.strip()) if p]
    if not parts:
        return []
    first = parts[0].lower()
    last = parts[-1].lower()
    candidates = [
        f"{first}{last}",
        f"{first}_{last}",
        f"{first[0]}{last}",
        f"{first}",
        f"{last}",
    ]
    out = []
    for c in candidates:
        handle = re.sub(r'[^a-z0-9_]', '', c)
        if handle and handle not in [h.lstrip("@") for h in out]:
            out.append(f"@{handle}")
    return out


# ─────────────────────────────────────────────────────────────────
# Real data source: Apify Twitter scraper
# ─────────────────────────────────────────────────────────────────
# Ordered list of actors to try — the first that succeeds for a given
# founder wins. apidojo/tweet-scraper is most reliable as of 2026.
APIFY_ACTORS = [
    "apidojo~tweet-scraper",       # apidojo/tweet-scraper — most reliable
    "kaitoeasyapi~twitter-x-data-tweet-scraper-pay-per-result-cheapest",
    "apify~twitter-scraper-lite",  # apify/twitter-scraper-lite — free tier
    "apify~twitter-scraper",        # legacy fallback
]

_APIFY_DIAGNOSTICS = {"last_error": None, "actor_results": {}}


def _apify_payload_for(actor, handles):
    """Return the best-known input schema for each actor."""
    handle_list = [h.lstrip("@") for h in handles[:5]]
    if actor.startswith("apidojo"):
        return {
            "twitterHandles": handle_list,
            "maxItems": 10,
            "sort": "Latest",
        }
    if actor.startswith("kaitoeasyapi"):
        return {
            "twitterHandles": handle_list,
            "maxItems": 10,
        }
    if "twitter-scraper-lite" in actor:
        return {
            "startUrls": [f"https://twitter.com/{h}" for h in handle_list],
            "maxItems": 10,
        }
    return {
        "searchTerms": [f"from:{h}" for h in handle_list],
        "maxTweets": 10,
        "maxItems": 10,
    }


def _parse_apify_items(items):
    """Extract best handle+followers+topics from a mixed-shape Apify response."""
    if not items:
        return None
    best = None
    for item in items:
        # apidojo shape vs legacy shape vs kaitoeasyapi shape
        author = (
            item.get("author")
            or item.get("user")
            or {
                "userName": item.get("userName") or item.get("username"),
                "followersCount": item.get("followersCount") or item.get("followers"),
            }
        )
        handle = (
            author.get("userName")
            or author.get("screen_name")
            or author.get("username")
            or ""
        )
        followers = int(
            author.get("followersCount")
            or author.get("followers_count")
            or author.get("followers")
            or 0
        )
        if not handle:
            continue
        if not best or followers > best["followers"]:
            best = {
                "handle": f"@{handle}",
                "followers": followers,
                "topics": [],
                "recent_posts": 0,
            }

    if not best:
        return None

    # Count posts for chosen handle and collect hashtags
    topics = set()
    chosen_handle = best["handle"].lstrip("@").lower()
    for item in items:
        author = item.get("author") or item.get("user") or {}
        handle = (
            author.get("userName")
            or author.get("screen_name")
            or author.get("username")
            or item.get("userName")
            or ""
        ).lower()
        if handle and handle == chosen_handle:
            best["recent_posts"] += 1
            for tag in item.get("hashtags", []) or []:
                if isinstance(tag, dict):
                    tag = tag.get("text") or ""
                if tag:
                    topics.add(str(tag))
            # Entities in apidojo shape
            entities = item.get("entities") or {}
            for tag in entities.get("hashtags", []) or []:
                if isinstance(tag, dict):
                    tag = tag.get("text") or tag.get("tag") or ""
                if tag:
                    topics.add(str(tag))
    best["topics"] = sorted(topics)[:5]
    return best


def fetch_via_apify(founder, handles):
    """
    Try each Apify actor in order; first one returning data wins.
    Tracks per-actor success to avoid retrying broken actors for every founder.
    """
    if not APIFY_TOKEN:
        return None

    for actor in APIFY_ACTORS:
        # Skip actors that have failed 5+ times already
        stats = _APIFY_DIAGNOSTICS["actor_results"].setdefault(
            actor, {"attempts": 0, "successes": 0, "http_errors": {}, "last_body_preview": ""}
        )
        if stats["attempts"] >= 5 and stats["successes"] == 0:
            continue

        stats["attempts"] += 1
        run_url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
        payload = _apify_payload_for(actor, handles)

        try:
            resp = SESSION.post(
                run_url,
                params={"token": APIFY_TOKEN, "timeout": 120},
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as e:
            logger.debug("Apify request error for %s via %s: %s", founder, actor, e)
            _APIFY_DIAGNOSTICS["last_error"] = f"{actor}: request error: {e}"
            continue

        if not resp.ok:
            stats["http_errors"][str(resp.status_code)] = (
                stats["http_errors"].get(str(resp.status_code), 0) + 1
            )
            body_preview = resp.text[:300] if resp.text else ""
            stats["last_body_preview"] = body_preview
            logger.info(
                "Apify actor %s returned HTTP %d for %s — body: %s",
                actor, resp.status_code, founder, body_preview[:200]
            )
            _APIFY_DIAGNOSTICS["last_error"] = (
                f"{actor}: HTTP {resp.status_code} — {body_preview[:200]}"
            )
            continue

        try:
            items = resp.json()
        except ValueError:
            _APIFY_DIAGNOSTICS["last_error"] = f"{actor}: JSON decode error"
            continue

        parsed = _parse_apify_items(items)
        if parsed:
            stats["successes"] += 1
            return parsed

    return None


def fetch_via_rapidapi(founder, handles):
    """
    Try RapidAPI Twitter mirror. Exact endpoint varies by subscription;
    we use a common shape that returns user.followers_count.
    """
    if not RAPIDAPI_KEY:
        return None
    host = "twitter-api45.p.rapidapi.com"
    for handle in handles:
        user = handle.lstrip("@")
        try:
            resp = SESSION.get(
                f"https://{host}/screenname.php",
                params={"screenname": user},
                headers={
                    "X-RapidAPI-Key": RAPIDAPI_KEY,
                    "X-RapidAPI-Host": host,
                },
                timeout=REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException:
            continue
        if not resp.ok:
            continue
        try:
            data = resp.json()
        except ValueError:
            continue
        followers = int(data.get("sub_count") or data.get("followers_count") or 0)
        if followers > 0:
            return {
                "handle": handle,
                "followers": followers,
                "topics": [],
                "recent_posts": 0,
            }
    return None


def fetch_via_x_api(founder, handles):
    """Official X API v2 user lookup by username."""
    if not X_BEARER_TOKEN:
        return None
    users_url = "https://api.twitter.com/2/users/by"
    usernames = ",".join(h.lstrip("@") for h in handles[:5])
    try:
        resp = SESSION.get(
            users_url,
            params={"usernames": usernames, "user.fields": "public_metrics"},
            headers={"Authorization": f"Bearer {X_BEARER_TOKEN}"},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.RequestException:
        return None
    if not resp.ok:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None
    users = data.get("data") or []
    if not users:
        return None
    best = None
    for u in users:
        metrics = u.get("public_metrics") or {}
        followers = int(metrics.get("followers_count") or 0)
        handle = u.get("username") or ""
        if not best or followers > best["followers"]:
            best = {
                "handle": f"@{handle}" if handle else "",
                "followers": followers,
                "topics": [],
                "recent_posts": int(metrics.get("tweet_count") or 0),
            }
    return best


def fetch_founder_signal(founder, company, source):
    handles = guess_handles(founder)
    if not handles:
        return None

    try:
        if source == "x_api_v2":
            sig = fetch_via_x_api(founder, handles)
        elif source == "apify":
            sig = fetch_via_apify(founder, handles)
        elif source == "rapidapi":
            sig = fetch_via_rapidapi(founder, handles)
        else:
            return None
    except Exception as e:
        logger.debug("Error fetching %s via %s: %s", founder, source, e)
        return None

    if not sig:
        return None
    sig["founder"] = founder
    sig["company"] = company
    sig["fetched_at"] = datetime.now(timezone.utc).isoformat()
    return sig


# ─────────────────────────────────────────────────────────────────
# File I/O
# ─────────────────────────────────────────────────────────────────
def save_json(data, filename):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %s (%d bytes)", path, path.stat().st_size)


def build_placeholder_records(founders):
    """
    No live data source — still emit a meaningful structured placeholder
    so the frontend knows WHICH founders SHOULD be tracked.
    """
    now = datetime.now(timezone.utc).isoformat()
    recs = []
    for f in founders:
        handles = guess_handles(f["founder"])
        recs.append({
            "founder": f["founder"],
            "company": f["company"],
            "handle": handles[0] if handles else "",
            "candidate_handles": handles,
            "followers": None,
            "recent_posts": None,
            "topics": [],
            "fetched_at": now,
            "placeholder": True,
            "reason": (
                "No X_BEARER_TOKEN / APIFY_TOKEN / RAPIDAPI_KEY set. "
                "This record documents that this founder IS on the "
                "tracking list; fields will populate once a credential "
                "is configured."
            ),
        })
    return recs


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 60)
    logger.info("Twitter/X Signals Fetcher")
    logger.info("=" * 60)

    started_at = datetime.now(timezone.utc).isoformat()
    source = available_data_source()

    if not source:
        logger.warning(
            "No Twitter/X data source configured. Running in PLACEHOLDER mode "
            "— but writing STRUCTURED data for top founders so the pipeline "
            "knows who SHOULD be tracked."
        )
    else:
        logger.info("Using data source: %s", source)

    top_founders = load_top_founders()

    real_signals = []
    attempted = 0
    # Use a subset when running in real mode — the Apify free tier only allows
    # a limited number of actor runs per day.
    fetch_limit = min(int(os.environ.get("TWITTER_FETCH_LIMIT", "25")), len(top_founders))

    if source:
        for i, f in enumerate(top_founders[:fetch_limit], 1):
            attempted += 1
            logger.info("[%d/%d] %s (%s)", i, fetch_limit, f["founder"], f["company"])
            try:
                sig = fetch_founder_signal(f["founder"], f["company"], source)
                if sig:
                    real_signals.append(sig)
            except Exception as e:
                logger.warning("  error: %s", e)
            time.sleep(0.5)  # mild rate-limiting between calls

    # ALWAYS fill the rest with structured placeholders — that way the
    # frontend always has a populated "tracked founders" list, even when
    # the scraping layer is having a bad day.
    real_handles = {(s.get("founder"), s.get("company")) for s in real_signals}
    placeholders = [
        p for p in build_placeholder_records(top_founders)
        if (p["founder"], p["company"]) not in real_handles
    ]
    signals = real_signals + placeholders

    save_json(signals, "twitter_signals_auto.json")

    status = {
        "script": "fetch_twitter_signals.py",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "mode": "real+placeholder" if source else "placeholder",
        "data_source": source,
        "top_founders_tracked": len(top_founders),
        "founders_attempted": attempted,
        "signals_collected": len(real_signals),
        "placeholder_records": len(placeholders),
        "apify_diagnostics": _APIFY_DIAGNOSTICS if source == "apify" else None,
        "ok": True,
        "notes": (
            "Structured placeholder — candidate handles are guessed from "
            "first+last name; populate via APIFY_TOKEN or X_BEARER_TOKEN."
        ) if not source else (
            f"Real fetching attempted for {attempted} founders; "
            f"{len(real_signals)} populated, rest are structured placeholders."
        ),
    }
    save_json(status, "twitter_signals_status.json")

    logger.info("Founders tracked: %d", len(top_founders))
    logger.info("Signals (real or placeholder): %d", len(signals))
    logger.info("Mode: %s", "real" if source else "placeholder")
    logger.info("=" * 60)
    logger.info("Done.")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        save_json({
            "script": "fetch_twitter_signals.py",
            "ok": False,
            "fatal_error": str(e),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }, "twitter_signals_status.json")
        raise
