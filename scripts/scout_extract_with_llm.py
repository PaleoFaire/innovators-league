#!/usr/bin/env python3
"""
LLM-based Extraction Layer — the core unlock for the headhunter scout.

Reads raw signal feeds (podcast episodes, newsletter articles, tech-media
RSS) and extracts company mentions with Claude. Way more accurate than
regex NER because the LLM:
  - Distinguishes companies from people (Garth Sheldon-Coulson the
    person vs Panthalassa the company)
  - Reads full episode descriptions, not just titles
  - Filters out well-known incumbents (Tesla, OpenAI, etc.)
  - Captures stealth signals ("emerged from stealth", "first interview")
  - Returns structured data: name, sector, founder, funding, description

Inputs:
  data/podcast_signals_auto.json   (rawEpisodes[])
  data/newsletter_signals_auto.json (raw feeds — extends to all items)

Output:
  data/scout_llm_extracted.json — structured candidates with rich metadata

Cost: ~$0.50/week at full volume (200 items × claude-haiku, $0.001/item).
Trivial. The signal lift is enormous.

Setup:
  - GitHub Actions secret: ANTHROPIC_API_KEY
  - Local: export ANTHROPIC_API_KEY=...

Resilience:
  - Caches by content hash so re-runs only process new items
  - Graceful no-op if API key absent — pipeline still works without LLM
"""

import json
import os
import re
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA_JS = ROOT / "data.js"
OUT_PATH = DATA / "scout_llm_extracted.json"
CACHE_PATH = DATA / ".scout_llm_cache.json"

# Tunable: how many items per source to process per run. With caching,
# subsequent runs only touch new items, so this caps cold-start cost.
MAX_ITEMS_PER_SOURCE = 50

# Model — claude-haiku is fast + cheap for extraction tasks.
# Override via ANTHROPIC_MODEL env var if needed.
DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")

EXTRACTION_PROMPT = """You are a frontier-tech scout for the Rational Optimist Society.

Read this {kind} and extract any companies that look like real, exciting frontier-tech startups (defense, space, nuclear, fusion, AI, robotics, quantum, biotech, climate, advanced manufacturing, semiconductors).

CRITICAL FILTERS — return [] if none apply:
- Skip well-known incumbents: Tesla, SpaceX, Anthropic, OpenAI, Google, Apple, Meta, NVIDIA, Anduril (already tracked).
- Skip VC firms (Lux Capital, Founders Fund, etc.) — only PORTFOLIO companies count.
- Skip people's names (the host, the guest, individual founders) — only the COMPANIES they run.
- Skip media organizations (Bloomberg, NYT, Substack publications).
- Skip universities and government agencies (DARPA, NASA, etc.).
- Skip generic terms ("AI", "the company", "their startup").

For each real company found, output JSON:
{{
  "name": "Company Name",
  "sector": "one of: Defense & Security, Space & Aerospace, Nuclear Energy, Fusion Energy, AI & Compute, Robotics & Manufacturing, Quantum Computing, Biotech & Health, Climate & Energy, Chips & Semiconductors, Advanced Manufacturing, Critical Minerals, Other",
  "founder": "name(s) if mentioned, else null",
  "fundingMentioned": "amount + round if any, else null",
  "stealthSignal": true if this is described as stealth/first-time-public/just-launched, else false,
  "description": "1 sentence on what they do, in your own words",
  "confidence": "high|medium|low — how confident this is a real frontier-tech startup worth tracking"
}}

Return ONLY a JSON array. No prose, no code fences, no commentary.

{kind} TITLE: {title}
{kind} TEXT:
{text}
"""


def content_hash(text):
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def load_cache():
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.load(open(CACHE_PATH))
    except Exception:
        return {}


def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, indent=2, default=str))


def load_existing_companies():
    """Names already in COMPANIES — used to filter the LLM output."""
    if not DATA_JS.exists():
        return set()
    src = DATA_JS.read_text(encoding="utf-8", errors="replace")
    names = set()
    for m in re.finditer(r'name:\s*"([^"]+)"', src):
        n = m.group(1).strip().lower()
        names.add(n)
        names.add(re.sub(r'[\s\-_\.]+', '', n))  # space-stripped variant
    return names


def call_claude(client, prompt, model=DEFAULT_MODEL, max_retries=3):
    """Call Claude via SDK; return parsed JSON list or [] on failure."""
    last_err = None
    for attempt in range(max_retries):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            text = msg.content[0].text.strip()
            # Handle if model wraps in code fences despite instructions
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.M).strip()
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "companies" in data:
                    return data["companies"]
                return []
            except json.JSONDecodeError:
                # Last-ditch: try to find a JSON array in the response
                m = re.search(r"\[[\s\S]*?\]", text)
                if m:
                    try:
                        return json.loads(m.group(0))
                    except json.JSONDecodeError:
                        pass
                return []
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    print(f"    ⚠ Claude error: {last_err}")
    return []


def gather_inputs():
    """Collect all raw items to process: podcast episodes + newsletter
    article titles+summaries that haven't been seen before."""
    inputs = []

    # Podcast episodes
    pod_path = DATA / "podcast_signals_auto.json"
    if pod_path.exists():
        pod = json.load(open(pod_path))
        for ep in pod.get("rawEpisodes", []):
            text = (ep.get("summary") or "")[:1500]  # cap input length
            inputs.append({
                "kind": "podcast_episode",
                "source": ep.get("podcast"),
                "host": ep.get("host"),
                "title": ep.get("title", ""),
                "text": text,
                "url": ep.get("url"),
                "date": ep.get("date"),
            })

    # Newsletter articles — extract from raw signals' source items
    news_path = DATA / "newsletter_signals_auto.json"
    if news_path.exists():
        news = json.load(open(news_path))
        # Newsletter signals already aggregate per company. We need to also
        # process raw articles. For now, use the candidates' embedded signal
        # context as input.
        seen_articles = set()
        for cand in news.get("candidates", []):
            for sig in cand.get("signals", []):
                article_id = sig.get("articleUrl", "")
                if article_id in seen_articles:
                    continue
                seen_articles.add(article_id)
                inputs.append({
                    "kind": "newsletter_article",
                    "source": sig.get("source"),
                    "host": "",
                    "title": sig.get("articleTitle", ""),
                    "text": (sig.get("context") or "")[:1500],
                    "url": sig.get("articleUrl"),
                    "date": sig.get("articleDate"),
                })

    return inputs


def main():
    print("=" * 64)
    print("Scout LLM Extraction · Phase 3 (the core unlock)")
    print("=" * 64)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ ANTHROPIC_API_KEY not set — skipping LLM extraction.")
        print("  (Pipeline runs without LLM but uses brittle regex NER.)")
        # Still emit an empty file so downstream tooling doesn't break
        OUT_PATH.write_text(json.dumps({
            "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model": None,
            "skipped": True,
            "reason": "ANTHROPIC_API_KEY not set",
            "candidates": [],
        }, indent=2))
        return 0

    # Lazy import — only require anthropic SDK if API key present
    try:
        import anthropic
    except ImportError:
        print("⚠ anthropic SDK not installed. Install: pip install anthropic")
        return 1

    client = anthropic.Anthropic(api_key=api_key)
    known = load_existing_companies()
    print(f"  Roster: {len(known)} known companies")

    inputs = gather_inputs()
    print(f"  Raw items to consider: {len(inputs)}")

    cache = load_cache()
    print(f"  Cached extractions:    {len(cache)}")

    # Process per source, capped, with cache
    by_source_count = {}
    candidates = []
    new_extractions = 0

    for item in inputs:
        src = item.get("source", "unknown")
        by_source_count.setdefault(src, 0)
        if by_source_count[src] >= MAX_ITEMS_PER_SOURCE:
            continue
        by_source_count[src] += 1

        h = content_hash(f"{item.get('url','')}\n{item.get('title','')}\n{item.get('text','')}")
        if h in cache:
            extracted = cache[h]
        else:
            prompt = EXTRACTION_PROMPT.format(
                kind=item["kind"],
                title=item["title"],
                text=item["text"],
            )
            print(f"  → Claude extract: [{src}] {item['title'][:60]}…")
            extracted = call_claude(client, prompt)
            cache[h] = extracted
            new_extractions += 1
            time.sleep(0.3)  # rate-limit politeness

        for company in extracted:
            if not isinstance(company, dict): continue
            name = (company.get("name") or "").strip()
            if not name: continue
            # De-dupe vs known roster
            nl = name.lower()
            if nl in known: continue
            if re.sub(r'[\s\-_\.]+', '', nl) in known: continue
            candidates.append({
                "name": name,
                "sector": company.get("sector"),
                "founder": company.get("founder"),
                "fundingMentioned": company.get("fundingMentioned"),
                "stealthSignal": bool(company.get("stealthSignal")),
                "description": company.get("description"),
                "confidence": company.get("confidence", "medium"),
                "discoveredVia": {
                    "source": src,
                    "host": item.get("host"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "date": item.get("date"),
                    "kind": item["kind"],
                },
            })

        # Persist cache periodically
        if new_extractions % 20 == 0 and new_extractions > 0:
            save_cache(cache)

    save_cache(cache)

    # Aggregate per company name (multiple sources for same co = stronger signal)
    by_name = {}
    for c in candidates:
        n = c["name"]
        if n not in by_name:
            by_name[n] = {
                "name": n,
                "discoveries": [],
                "sectors": set(),
                "founders": set(),
                "stealthSignal": False,
                "confidence": "low",
                "descriptions": [],
            }
        e = by_name[n]
        e["discoveries"].append(c["discoveredVia"])
        if c["sector"]: e["sectors"].add(c["sector"])
        if c["founder"]: e["founders"].add(c["founder"])
        if c["stealthSignal"]: e["stealthSignal"] = True
        if c["description"]: e["descriptions"].append(c["description"])
        # Pick highest confidence across mentions
        order = {"high": 3, "medium": 2, "low": 1}
        if order.get(c["confidence"], 0) > order.get(e["confidence"], 0):
            e["confidence"] = c["confidence"]

    aggregated = []
    for e in by_name.values():
        e["sources"] = sorted(set(d.get("source") for d in e["discoveries"] if d.get("source")))
        e["sourceCount"] = len(e["sources"])
        e["multiSource"] = e["sourceCount"] >= 2
        e["sectors"] = sorted(e["sectors"])
        e["founders"] = sorted(e["founders"])
        # Pick the best description (longest, but capped)
        e["description"] = max(e["descriptions"], key=len) if e["descriptions"] else None
        del e["descriptions"]
        aggregated.append(e)

    # Sort: multi-source first, then high-confidence, then stealth signal
    def rank_key(c):
        return (
            -int(c["multiSource"]),
            -{"high": 3, "medium": 2, "low": 1}.get(c["confidence"], 0),
            -int(c["stealthSignal"]),
            c["name"].lower(),
        )
    aggregated.sort(key=rank_key)

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": DEFAULT_MODEL,
        "rosterSize": len(known),
        "rawItemsConsidered": len(inputs),
        "newExtractionsThisRun": new_extractions,
        "uniqueCandidates": len(by_name),
        "candidates": aggregated,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2, default=str))

    print()
    print(f"✅ Wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"   Considered:   {len(inputs)} raw items")
    print(f"   New LLM calls: {new_extractions}")
    print(f"   Cached hits:   {len(inputs) - new_extractions}")
    print(f"   Candidates:    {len(by_name)} unique")
    print()
    if aggregated:
        print("Top 15 LLM-extracted candidates:")
        for c in aggregated[:15]:
            stealth = " 🎯STEALTH" if c["stealthSignal"] else ""
            sources = ", ".join(c["sources"][:3])
            print(f"  [{c['confidence']:>6}] {c['name']:<35} ({sources}){stealth}")
            if c.get("description"):
                print(f"          → {c['description'][:90]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
