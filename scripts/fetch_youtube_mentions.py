#!/usr/bin/env python3
from __future__ import annotations
"""
YouTube Corporate Caption Mention Detector
─────────────────────────────────────────────────────────────────────────
Every NVIDIA GTC keynote, Tesla AI Day, SpaceX launch webcast, Figure AI /
1X / Boston Dynamics demo, Anduril demo, AWS re:Invent keynote, and every
top podcast (All-In, Acquired, 20VC, Dwarkesh, BG2) is auto-captioned by
YouTube within 24 hours.

This pipeline:
  1. Lists recent videos from a curated set of ~50 high-signal channels
  2. Pulls auto-generated captions via youtube-transcript-api (no auth)
  3. NER-matches against our 868-company COMPANIES list
  4. Emits per-company "heard in the wild" mention records with
     video_id + timestamp + context snippet.

Why it matters:
  When Jensen names a partner from the GTC stage, or a customer logo
  flashes in a Figure demo, that's material non-public-structured
  information. It's in the video but nowhere else organized.

Graceful degradation:
  If youtube-transcript-api is unavailable OR the curated channels list
  is empty OR the YouTube Data API key is missing (for channel listing),
  we emit a seeded recent-mentions dataset so the UI has content.

Output:
  data/youtube_mentions_auto.json
  data/youtube_mentions_auto.js

Cadence: daily via daily-data-sync workflow.
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
JSON_OUT = DATA_DIR / "youtube_mentions_auto.json"
JS_OUT = DATA_DIR / "youtube_mentions_auto.js"

USER_AGENT = (
    "InnovatorsLeague-YouTubeMentions/1.0 "
    "(+https://paleofaire.github.io/innovators-league)"
)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

# High-signal channels whose videos frequently name frontier-tech cos.
# Channel IDs (UC...) — populate these via YouTube API channel search.
CURATED_CHANNELS = {
    # Corporate keynotes / demos
    "NVIDIA":                 "UCHuiy8bXnmK5nisYHUd1J5g",
    "Tesla":                  "UC5WjFrtBdufl6CZojX3D8dQ",
    "SpaceX":                 "UCtI0Hodo5o5dUb67FeUjDeA",
    "Boston Dynamics":        "UC7vVhkEfw4nOGp8TyDk7RcQ",
    "Figure":                 "UCe10azLZtYsceTIJDkrVgnw",
    "Anduril Industries":     "UCjHFk1dFoHM5Vb5vCeRkqKw",
    "Rocket Lab":             "UCb-WW_PYYm4p4V0AuYyCv9Q",
    # Deep-tech investment commentary
    "All-In Podcast":         "UCESLZhusAkFfsNsApnjF_Cg",
    "Acquired":               "UCGU0aGGcq9rcVeaDmfP6ThA",
    "The Twenty Minute VC":   "UCGBzBkV-MinlBvHBzZawfLQ",
    "Invest Like the Best":   "UCuhnjcZHCXyvdNsOLk7Dxwg",
    "Dwarkesh Patel":         "UCUL6D6XPIcLqZUXcGcQQBaA",
    "Lex Fridman":            "UCSHZKyawb77ixDdsGog4iWA",
    "BG2 Pod":                "UC1kVHlAGpoikEUJlHENUQAg",
}

# Phrases marking the opening of a targeted company mention
STRIP_WORDS = {"the", "a", "an", "inc", "corp", "ltd", "co", "llc", "labs"}


def parse_company_names():
    """Extract tracked company names from data.js."""
    try:
        text = DATA_JS.read_text()
    except Exception:
        return []
    start = text.find("const COMPANIES = [")
    if start < 0: return []
    i = text.find("[", start)
    depth = 0; in_str = False; sc = None; esc = False; end = None
    for k in range(i, len(text)):
        c = text[k]
        if esc: esc = False; continue
        if c == "\\" and in_str: esc = True; continue
        if in_str:
            if c == sc: in_str = False
            continue
        if c in "\"'": in_str = True; sc = c; continue
        if c == "[": depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0: end = k; break
    block = text[i + 1: end]
    return re.findall(r'\bname:\s*"([^"]+)"', block)


def seeded_mentions():
    """Placeholder records were removed on 26 Nov 2026. The site never publishes
    invented data: if the live source is down, the output is empty and marked
    "unavailable"."""
    return []


def match_companies_in_text(text, company_names):
    """Return list of (company, context_window) tuples for any tracked
    company mentioned in the text. Context is the ±80-char window."""
    matches = []
    text_lc = text.lower()
    seen = set()
    for name in company_names:
        if name in seen:
            continue
        nlc = name.lower()
        if len(nlc) < 4: continue
        # Word-boundary search to avoid matching "Mara" inside "camaraderie"
        m = re.search(rf'\b{re.escape(nlc)}\b', text_lc)
        if m:
            s = max(0, m.start() - 80)
            e = min(len(text), m.end() + 80)
            ctx = text[s:e].replace("\n", " ").strip()
            matches.append({"company": name, "context": ctx})
            seen.add(name)
    return matches


def fetch_recent_videos(channel_id, max_per_channel=8):
    """List the most recent uploaded videos for a channel via YouTube
    Data API v3. Returns [{id, title, published_at, channel_id}]."""
    try:
        # Search endpoint — sort by date, filter to videos on this channel
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "key": YOUTUBE_API_KEY,
                "channelId": channel_id,
                "part": "snippet",
                "order": "date",
                "maxResults": max_per_channel,
                "type": "video",
            },
            timeout=20,
            headers={"User-Agent": USER_AGENT},
        )
        if r.status_code != 200:
            return []
        items = r.json().get("items", [])
        out = []
        for it in items:
            snip = it.get("snippet", {})
            out.append({
                "id": it.get("id", {}).get("videoId", ""),
                "title": snip.get("title", ""),
                "published_at": snip.get("publishedAt", "")[:10],
                "channel_id": channel_id,
                "channel_title": snip.get("channelTitle", ""),
            })
        return out
    except Exception as e:
        print(f"    channel {channel_id} search failed: {type(e).__name__}")
        return []


def fetch_transcript(video_id):
    """Fetch auto-generated caption text via youtube-transcript-api.
    Returns list of {start, text} or [] on failure."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        try:
            chunks = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])
        except Exception:
            # Try any available auto-generated language as fallback
            chunks = YouTubeTranscriptApi.get_transcript(video_id)
        return [{"start": c.get("start", 0), "text": c.get("text", "")} for c in chunks]
    except ImportError:
        return []
    except Exception:
        return []


def ts_to_hms(seconds):
    """Seconds → H:MM:SS or M:SS format for UI display."""
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def extract_mentions_from_transcript(
    video, transcript, company_names, tracked_lower
):
    """Scan a transcript for company mentions. Returns list of mention dicts."""
    mentions = []
    if not transcript:
        return mentions
    # Concatenate chunks with their timestamps
    # For each company, find first mention and grab surrounding context
    seen_companies = set()
    for i, chunk in enumerate(transcript):
        text_lc = chunk["text"].lower()
        for name in company_names:
            nlc = name.lower()
            if len(nlc) < 4 or nlc in seen_companies:
                continue
            # Word-boundary match to avoid false positives
            if re.search(rf'\b{re.escape(nlc)}\b', text_lc):
                # Build context from ±3 chunks
                s = max(0, i - 2)
                e = min(len(transcript), i + 3)
                context = " ".join(transcript[j]["text"] for j in range(s, e)).strip()
                # Shorten to ~180 chars with ellipses
                if len(context) > 180:
                    context = "…" + context[:180] + "…"
                mentions.append({
                    "company": name,
                    "video_id": video["id"],
                    "channel": video.get("channel_title", ""),
                    "video_title": video.get("title", ""),
                    "published_at": video.get("published_at", ""),
                    "timestamp": ts_to_hms(chunk["start"]),
                    "context": context,
                })
                seen_companies.add(nlc)
    return mentions


def live_pipeline(company_names, tracked_lower):
    """Run the real pipeline: channel → videos → captions → NER."""
    all_mentions = []
    for ch_name, ch_id in CURATED_CHANNELS.items():
        print(f"  [{ch_name}] fetching recent videos...")
        videos = fetch_recent_videos(ch_id, max_per_channel=8)
        for v in videos:
            if not v.get("id"):
                continue
            time.sleep(0.2)  # polite pacing
            transcript = fetch_transcript(v["id"])
            if not transcript:
                continue
            mentions = extract_mentions_from_transcript(
                v, transcript, company_names, tracked_lower
            )
            if mentions:
                print(f"    {v['title'][:50]}... → {len(mentions)} mentions")
            all_mentions.extend(mentions)
    # Sort newest first
    all_mentions.sort(key=lambda m: m.get("published_at", ""), reverse=True)
    return all_mentions


def main():
    DATA_DIR.mkdir(exist_ok=True)
    company_names = parse_company_names()
    tracked_lower = set(n.lower() for n in company_names)
    print(f"Parsed {len(company_names)} tracked companies")

    if not YOUTUBE_API_KEY:
        print("  YOUTUBE_API_KEY not set — emitting seeded mentions")
        mentions = seeded_mentions()
        source_status = "unavailable"
    else:
        print(f"  Live pipeline: {len(CURATED_CHANNELS)} curated channels")
        try:
            mentions = live_pipeline(company_names, tracked_lower)
            if not mentions:
                print("  Live pipeline returned 0 mentions; falling back to seeded")
                mentions = seeded_mentions()
                source_status = "seeded_fallback"
            else:
                source_status = "live"
        except Exception as e:
            print(f"  Live pipeline errored ({type(e).__name__}: {e}); falling back to seeded")
            mentions = seeded_mentions()
            source_status = "seeded_fallback"

    filtered = mentions[:60]  # cap display

    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "source_status": source_status,
        "curated_channels_count": len(CURATED_CHANNELS),
        "mentions": filtered,
        "summary": {
            "total_mentions": len(filtered),
            "unique_companies": len(set(m["company"] for m in filtered)),
        },
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2, default=str))
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    JS_OUT.write_text(
        f"// Last updated: {ts}\n"
        f"window.YOUTUBE_MENTIONS_AUTO = {json.dumps(payload, default=str)};\n"
    )
    print(f"\n✓ {len(filtered)} mentions across {payload['summary']['unique_companies']} companies")
    print(f"  → {JSON_OUT.name}, {JS_OUT.name}")


if __name__ == "__main__":
    main()
