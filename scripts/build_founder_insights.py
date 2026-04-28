#!/usr/bin/env python3
"""
Founder Insights Feed Builder.

For each company in COMPANIES, gathers public sources where the founder
appears (podcast episodes, earnings calls, news articles, newsletter
mentions) and uses Claude to extract the most important verbatim quotes
the founder has shared publicly about their company.

Output: data/founder_insights_auto.json with shape:
  {
    "Company Name": {
      "founder": "Founder Name",
      "lastUpdated": "...",
      "insights": [
        {
          "quote": "verbatim quote",
          "topic": "1-phrase what it's about",
          "source": "podcast|earnings|news|newsletter",
          "sourceName": "Core Memory" or article publisher,
          "url": "...",
          "date": "..."
        }
      ]
    }
  }

Trust contract:
  - Verbatim quotes only (or near-verbatim if news paraphrase explicitly
    attributes to the founder).
  - Every insight has a source URL.
  - Generic industry chatter is NOT included.
  - Empty result is fine — better than fabricated insights.

Design:
  - Cached by content hash (re-runs only process new sources).
  - Skips companies without enough source material (< 3 mentions total).
  - Cost: ~$0.05 per company processed.
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
OUT_PATH = DATA / "founder_insights_auto.json"
CACHE_PATH = DATA / ".founder_insights_cache.json"

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
MAX_COMPANIES_PER_RUN = int(os.environ.get("MAX_COMPANIES_PER_RUN", "200"))
MIN_SOURCES = 2  # Need at least 2 mentions to bother extracting

EXTRACTION_PROMPT = """You are an editorial researcher. Below are public sources where {founder} (founder of {company}) appears or is quoted. Extract the most important things {founder} has *personally said* in public — their genuine views about their company, technology, vision, or strategy.

STRICT RULES:
1. Only include quotes that are clearly attributable to {founder} — not other speakers, hosts, or third parties paraphrasing about the company.
2. Verbatim quotes preferred. If a news article paraphrases the founder, use the exact quoted span ("...") if one exists. If only paraphrased, mark it as "paraphrased: [...]" and only include if the attribution is unambiguous.
3. Skip: generic industry commentary, marketing-speak press release boilerplate, predictions about competitors, things said by hosts/journalists.
4. Aim for 5-10 substantive insights. If genuinely fewer exist, return fewer. Empty array is valid.
5. Every insight must have a source URL.

Output: JSON array. Each item:
{{
  "quote": "the actual words",
  "topic": "1-3 word what it's about (e.g. 'manufacturing strategy', 'AI safety', 'commercial timeline')",
  "source_type": "podcast|earnings|news|newsletter|other",
  "source_name": "Core Memory" or article publisher,
  "url": "source URL",
  "date": "YYYY-MM-DD if available, else null",
  "paraphrased": true if not verbatim, false otherwise
}}

Return ONLY the JSON array. No prose, no code fences, no commentary.

COMPANY: {company}
FOUNDER: {founder}

PUBLIC SOURCES:
{sources_text}
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


def parse_companies():
    """Extract companies from data.js with founder, ticker (for public co cross-ref)."""
    src = DATA_JS.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'const COMPANIES\s*=\s*\[', src)
    if not m: return []
    start = m.end() - 1
    depth = 0
    in_str = False
    str_q = None
    i = start
    while i < len(src):
        ch = src[i]
        nx = src[i + 1] if i + 1 < len(src) else ''
        if in_str:
            if ch == '\\': i += 2; continue
            if ch == str_q: in_str = False
        else:
            if ch in ('"', "'", '`'): in_str = True; str_q = ch
            elif ch == '[': depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    block = src[start:i + 1]
                    break
        i += 1
    else:
        return []

    companies = []
    obj_depth = 0
    obj_start = None
    in_str = False
    str_q = None
    for i, ch in enumerate(block):
        if in_str:
            if ch == '\\': continue
            if ch == str_q: in_str = False
        else:
            if ch in ('"', "'", '`'): in_str = True; str_q = ch
            elif ch == '{':
                if obj_depth == 0: obj_start = i
                obj_depth += 1
            elif ch == '}':
                obj_depth -= 1
                if obj_depth == 0 and obj_start is not None:
                    obj = block[obj_start:i + 1]
                    nm = re.search(r'name:\s*"([^"]+)"', obj)
                    fd = re.search(r'founder:\s*"([^"]+)"', obj)
                    tk = re.search(r'ticker:\s*"([^"]+)"', obj)
                    if nm:
                        companies.append({
                            "name": nm.group(1).strip(),
                            "founder": fd.group(1).strip() if fd else None,
                            "ticker": tk.group(1).strip() if tk else None,
                        })
                    obj_start = None
    return companies


def gather_sources(company_name, founder_name, ticker):
    """Aggregate all public-source items mentioning this company/founder."""
    sources = []

    # Podcast mentions (tagged by company)
    pm_path = DATA / "podcast_mentions_auto.json"
    if pm_path.exists():
        try:
            for m in json.load(open(pm_path)):
                if (m.get("company") or "").lower() == company_name.lower():
                    sources.append({
                        "type": "podcast",
                        "source_name": m.get("podcast"),
                        "title": m.get("episode_title"),
                        "url": m.get("url"),
                        "date": (m.get("episode_date") or "")[:10],
                        "text": m.get("description_excerpt") or "",
                    })
        except Exception:
            pass

    # News articles (matched company)
    nr_path = DATA / "news_raw.json"
    if nr_path.exists():
        try:
            for n in json.load(open(nr_path)):
                matches = []
                if n.get("matchedCompany"): matches.append(n["matchedCompany"])
                if n.get("matchedCompanies"): matches.extend(n["matchedCompanies"])
                if any(m and m.lower() == company_name.lower() for m in matches):
                    sources.append({
                        "type": "news",
                        "source_name": n.get("source"),
                        "title": n.get("title"),
                        "url": n.get("link"),
                        "date": (n.get("pubDate") or "")[:10],
                        "text": n.get("description") or "",
                    })
        except Exception:
            pass

    # Earnings signals (by ticker, for public cos)
    if ticker:
        es_path = DATA / "earnings_signals_auto.json"
        if es_path.exists():
            try:
                d = json.load(open(es_path))
                for s in d.get("signals", []):
                    if s.get("ticker") == ticker:
                        sources.append({
                            "type": "earnings",
                            "source_name": f"{s.get('incumbent','')} {s.get('quarter','')} earnings call",
                            "title": s.get("quote", "")[:120],
                            "url": s.get("source_url"),
                            "date": s.get("date") or s.get("quarter"),
                            "text": s.get("quote") or "",
                        })
            except Exception:
                pass

    # Newsletter signals (matched company in candidates)
    ns_path = DATA / "newsletter_signals_auto.json"
    if ns_path.exists():
        try:
            d = json.load(open(ns_path))
            for c in d.get("candidates", []):
                if (c.get("name") or "").lower() == company_name.lower():
                    for sig in c.get("signals", [])[:3]:
                        sources.append({
                            "type": "newsletter",
                            "source_name": sig.get("source"),
                            "title": sig.get("articleTitle"),
                            "url": sig.get("articleUrl"),
                            "date": (sig.get("articleDate") or "")[:10],
                            "text": sig.get("context") or "",
                        })
        except Exception:
            pass

    # Podcast scout raw episodes (search by founder name)
    if founder_name:
        ps_path = DATA / "podcast_signals_auto.json"
        if ps_path.exists():
            try:
                d = json.load(open(ps_path))
                first_name = founder_name.split(",")[0].split()[0]  # primary founder, first word
                for ep in d.get("rawEpisodes", []):
                    title = (ep.get("title") or "")
                    summary = (ep.get("summary") or "")
                    # Match if founder name appears in title or first 500 chars of summary
                    haystack = f"{title} {summary[:500]}"
                    if founder_name.split(",")[0] in haystack or (first_name and first_name in haystack and len(first_name) > 3):
                        sources.append({
                            "type": "podcast",
                            "source_name": ep.get("podcast"),
                            "title": title,
                            "url": ep.get("url"),
                            "date": (ep.get("date") or "")[:10],
                            "text": summary,
                        })
            except Exception:
                pass

    # Dedupe by URL
    seen = set()
    deduped = []
    for s in sources:
        u = s.get("url") or s.get("title", "")
        if u in seen: continue
        seen.add(u)
        deduped.append(s)

    return deduped


def format_sources_for_prompt(sources, max_chars=8000):
    """Format sources as a labeled list for Claude. Cap at max_chars."""
    parts = []
    used = 0
    for i, s in enumerate(sources, 1):
        block = (
            f"[{i}] {s.get('type', '?').upper()} — {s.get('source_name', '?')} "
            f"({s.get('date', 'date unknown')})\n"
            f"Title: {s.get('title', '?')}\n"
            f"URL: {s.get('url', '')}\n"
            f"Text: {(s.get('text') or '')[:1200]}\n\n"
        )
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "".join(parts)


def call_claude(client, prompt, model=DEFAULT_MODEL, max_retries=3):
    last_err = None
    for attempt in range(max_retries):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            text = msg.content[0].text.strip()
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.M).strip()
            try:
                data = json.loads(text)
                if isinstance(data, list): return data
                if isinstance(data, dict) and "insights" in data: return data["insights"]
                return []
            except json.JSONDecodeError:
                m = re.search(r"\[[\s\S]*\]", text)
                if m:
                    try: return json.loads(m.group(0))
                    except json.JSONDecodeError: pass
                return []
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1: time.sleep(2 ** attempt)
    print(f"    ⚠ Claude error: {last_err}")
    return []


def main():
    print("=" * 64)
    print("Founder Insights Feed Builder")
    print("=" * 64)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ ANTHROPIC_API_KEY not set — emitting empty placeholder.")
        OUT_PATH.write_text(json.dumps({
            "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "skipped": True,
            "reason": "ANTHROPIC_API_KEY not set",
            "byCompany": {},
        }, indent=2))
        return 0

    try:
        import anthropic
    except ImportError:
        print("⚠ anthropic SDK missing. pip install anthropic")
        return 1

    client = anthropic.Anthropic(api_key=api_key)
    cache = load_cache()
    print(f"  Cache entries: {len(cache)}")

    companies = parse_companies()
    print(f"  Companies in DB: {len(companies)}")

    # Filter to companies with a founder field
    with_founder = [c for c in companies if c.get("founder")]
    print(f"  With founder field: {len(with_founder)}")

    by_company = {}
    processed = 0
    extracted_total = 0
    new_calls = 0

    # Process companies in priority order — those with most source material first
    candidates = []
    for c in with_founder:
        srcs = gather_sources(c["name"], c["founder"], c.get("ticker"))
        if len(srcs) >= MIN_SOURCES:
            candidates.append((c, srcs))
    # Sort by source count desc
    candidates.sort(key=lambda x: -len(x[1]))
    print(f"  Companies with ≥{MIN_SOURCES} sources: {len(candidates)}")
    print(f"  Will process up to {MAX_COMPANIES_PER_RUN} this run")

    for c, sources in candidates[:MAX_COMPANIES_PER_RUN]:
        sources_text = format_sources_for_prompt(sources)
        prompt = EXTRACTION_PROMPT.format(
            company=c["name"],
            founder=c["founder"],
            sources_text=sources_text,
        )
        h = content_hash(prompt)
        if h in cache:
            insights = cache[h]
        else:
            print(f"  → Extract: {c['name']} ({c['founder']}) — {len(sources)} sources")
            insights = call_claude(client, prompt)
            cache[h] = insights
            new_calls += 1
            time.sleep(0.3)

        # Normalize + filter
        clean = []
        for ins in insights:
            if not isinstance(ins, dict): continue
            quote = (ins.get("quote") or "").strip()
            url = (ins.get("url") or "").strip()
            if not quote or not url: continue
            clean.append({
                "quote": quote,
                "topic": ins.get("topic") or "",
                "source_type": ins.get("source_type") or "other",
                "source_name": ins.get("source_name") or "",
                "url": url,
                "date": ins.get("date"),
                "paraphrased": bool(ins.get("paraphrased", False)),
            })

        if clean:
            by_company[c["name"]] = {
                "founder": c["founder"],
                "ticker": c.get("ticker"),
                "lastUpdated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "insights": clean,
            }
            extracted_total += len(clean)
        processed += 1

        # Persist cache periodically
        if new_calls % 20 == 0 and new_calls > 0:
            save_cache(cache)

    save_cache(cache)

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": DEFAULT_MODEL,
        "companiesProcessed": processed,
        "companiesWithInsights": len(by_company),
        "totalInsights": extracted_total,
        "newClaudeCallsThisRun": new_calls,
        "byCompany": by_company,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2, default=str))

    # Also emit JS wrapper for direct script-tag inclusion on company.html
    js_path = DATA / "founder_insights_auto.js"
    js_path.write_text(
        f"// Auto-generated from {OUT_PATH.name}\n"
        f"// Last updated: {out['generatedAt']}\n"
        f"const FOUNDER_INSIGHTS_AUTO = {json.dumps(out, indent=2, default=str)};\n"
        f"if (typeof window !== 'undefined') window.FOUNDER_INSIGHTS_AUTO = FOUNDER_INSIGHTS_AUTO;\n"
    )

    print()
    print(f"✅ Wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"   Companies processed: {processed}")
    print(f"   Companies w/ insights: {len(by_company)}")
    print(f"   Total insights: {extracted_total}")
    print(f"   New Claude calls: {new_calls}")
    if by_company:
        print()
        print("Sample (first 3 companies w/ insights):")
        for nm, data in list(by_company.items())[:3]:
            print(f"\n  {nm} — {data['founder']} ({len(data['insights'])} insights)")
            for ins in data['insights'][:2]:
                pf = "[paraphrase] " if ins.get("paraphrased") else ""
                print(f'    {pf}{ins["topic"]}: "{ins["quote"][:120]}..."')
                print(f'       → {ins.get("source_name", "?")} · {ins.get("date", "?")}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
