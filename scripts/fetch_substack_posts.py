#!/usr/bin/env python3
"""
Fetch Substack posts from rationaloptimistsociety.substack.com RSS feed
and write data/field_notes_auto.json for ingestion into FIELD_NOTES.

Part of Round 7l — eliminates FIELD_NOTES from the STATIC-HIGH list.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT_PATH = DATA_DIR / "field_notes_auto.json"

FEED_URL = "https://rationaloptimistsociety.substack.com/feed"
MAX_POSTS = 30


def fetch_feed():
    try:
        resp = requests.get(FEED_URL, timeout=20,
                            headers={"User-Agent": "InnovatorsLeague/1.0"})
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException as e:
        print(f"  WARN: could not fetch Substack feed: {e}", file=sys.stderr)
        return None


def parse_rss(xml_text):
    """Parse Substack RSS → list of {title, link, pubDate, description}"""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  ERROR: XML parse: {e}", file=sys.stderr)
        return items
    for item in root.iter("item"):
        entry = {}
        for child in item:
            tag = child.tag.split("}")[-1]  # strip namespace
            text = (child.text or "").strip()
            if tag in ("title", "link", "pubDate", "description", "creator", "guid"):
                entry[tag] = text
        if entry.get("title"):
            items.append(entry)
    return items[:MAX_POSTS]


def classify(entry):
    """Guess the field-note type from title / content."""
    text = (entry.get("title", "") + " " + entry.get("description", "")).lower()
    if "podcast" in text or "interview" in text or "episode" in text:
        return "podcast"
    if "visit" in text or "factory" in text or "tour" in text:
        return "site-visit"
    if "call with" in text or "conversation with" in text:
        return "founder-call"
    if "flash" in text or "alert" in text or "signal" in text:
        return "flash-take"
    return "post"


def clean_html(s):
    """Strip HTML tags for a plain hook/description."""
    return re.sub(r"<[^>]+>", "", s or "").strip()[:400]


def parse_date(s):
    if not s:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        # RFC 822 Substack dates
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(s)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return s[:10]


def main():
    print(f"Fetching Substack RSS: {FEED_URL}")
    xml = fetch_feed()
    if not xml:
        # Write an empty-but-valid file so downstream doesn't break
        OUT_PATH.write_text("[]")
        print(f"  Wrote empty array to {OUT_PATH}")
        return
    entries = parse_rss(xml)
    print(f"  Parsed {len(entries)} entries")

    notes = []
    for i, e in enumerate(entries, 1):
        notes.append({
            "id": i,
            "date": parse_date(e.get("pubDate")),
            "title": e["title"][:200],
            "type": classify(e),
            "hook": clean_html(e.get("description", ""))[:280],
            "url": e.get("link", ""),
            "author": e.get("creator", "Stephen McBride"),
            "source": "Substack",
        })

    OUT_PATH.write_text(json.dumps(notes, indent=2))
    print(f"  Saved {len(notes)} field notes to {OUT_PATH}")


if __name__ == "__main__":
    main()
