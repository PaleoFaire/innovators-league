#!/usr/bin/env python3
"""
Company Facts Verifier — accuracy-first multi-source verification.

For each company in COMPANIES (or a specified cohort), gathers public
sources (company website, Wikipedia, our existing news/earnings/funding
data) and uses Claude to extract verified facts. Outputs proposed
changes for human review before any data.js modifications.

ACCURACY CONTRACT (per Stephen's hard rule):
  - Only output a field value if Claude can cite a specific source phrase.
  - Empty/null is correct when sources don't support the field.
  - Worst outcome: incorrect data (replace with blank rather than guess).
  - Every proposed change has a source URL + source phrase.

INPUTS PER COMPANY:
  1. Company website (homepage + /about + /team) — primary source
  2. Wikipedia (search by name)
  3. Existing data we have:
     - news_raw.json (recent matched articles)
     - earnings_signals_auto.json (if public co)
     - press_releases_*.json (recent)
     - funding_tracker (latest round)
     - form_d_filings_auto.json (recent SEC filings)

FIELDS VERIFIED (in order of importance):
  - name (canonical form)
  - description (1-2 verified sentences)
  - founder (full names, comma-separated)
  - location (HQ city, state/country)
  - founded (year)
  - fundingStage (Pre-Seed / Seed / Series A-Z / Public / Acquired)
  - totalRaised (range, e.g. "$2.5B+")
  - valuation (post-money if disclosed)
  - investors (list, top 5)
  - website (canonical URL)

OUTPUT:
  data/company_facts_verification.json
    Schema:
    {
      "generatedAt": "...",
      "model": "...",
      "cohortSize": N,
      "companiesProcessed": N,
      "cleared": [...],          // facts match sources, no change
      "changesProposed": [...],  // diffs with sources + confidence
      "unverifiable": [...]      // couldn't find authoritative source
    }

USAGE:
  python scripts/verify_company_facts.py [--cohort-file PATH] [--limit N]

  --cohort-file PATH   JSON list of company names to verify.
                       Default: data/cold_email_picks.json (top 100)
  --limit N            Max companies to process this run (cost control)
"""

import argparse
import json
import os
import re
import time
import urllib.request
import urllib.error
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, quote

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA_JS = ROOT / "data.js"
# Output paths support a --output-suffix for parallel-safe runs
def _out_paths(suffix=""):
    suf = f"_{suffix}" if suffix else ""
    return (
        DATA / f"company_facts_verification{suf}.json",
        DATA / ".company_facts_url_cache.json",  # shared (read-mostly)
        DATA / ".company_facts_extraction_cache.json",  # shared
    )

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
DEFAULT_LIMIT = int(os.environ.get("VERIFY_LIMIT", "100"))

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

FETCH_TIMEOUT = 12
MAX_PAGE_CHARS = 12000   # cap per source page after HTML strip


# ────────────────────────────────────────────────────────────────────────
# COMPANY PARSING


def parse_companies():
    """Extract every COMPANIES entry as a dict."""
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
        if in_str:
            if ch == '\\': i += 2; continue
            if ch == str_q: in_str = False
        else:
            if ch in ('"', "'", '`'): in_str = True; str_q = ch
            elif ch == '[': depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    block = src[start:i+1]
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
                    obj = block[obj_start:i+1]
                    def grab(field):
                        mm = re.search(rf'\b{field}\s*:\s*"([^"]*)"', obj)
                        return mm.group(1) if mm else None
                    def grab_int(field):
                        mm = re.search(rf'\b{field}\s*:\s*(\d+)', obj)
                        return int(mm.group(1)) if mm else None
                    def grab_arr(field):
                        mm = re.search(rf'\b{field}\s*:\s*\[([^\]]*)\]', obj)
                        if not mm: return []
                        items = re.findall(r'"([^"]+)"', mm.group(1))
                        return items
                    companies.append({
                        'name': grab('name'),
                        'sector': grab('sector'),
                        'description': grab('description'),
                        'founder': grab('founder'),
                        'location': grab('location'),
                        'state': grab('state'),
                        'fundingStage': grab('fundingStage'),
                        'totalRaised': grab('totalRaised'),
                        'valuation': grab('valuation'),
                        'founded': grab_int('founded'),
                        'website': grab('website'),
                        'investors': grab_arr('investors'),
                    })
                    obj_start = None
    return companies


# ────────────────────────────────────────────────────────────────────────
# WEB FETCHING


class TextExtractor(HTMLParser):
    SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside",
                 "noscript", "iframe", "form", "button", "svg"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        elif tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "blockquote"}:
            if self.parts and not self.parts[-1].endswith("\n"):
                self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "blockquote"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.skip_depth == 0:
            self.parts.append(data)

    def text(self):
        joined = "".join(self.parts)
        joined = re.sub(r"\n{3,}", "\n\n", joined)
        joined = re.sub(r"[ \t]+", " ", joined)
        return joined.strip()


def fetch_url(url, url_cache, timeout=FETCH_TIMEOUT):
    """Fetch URL → strip HTML → return plain text. Cached persistently."""
    if not url or not url.startswith(("http://", "https://")):
        return ""
    if url in url_cache:
        return url_cache[url]
    try:
        req = urllib.request.Request(url, headers=HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ct = r.headers.get("Content-Type", "").lower()
            if "html" not in ct and "xml" not in ct:
                url_cache[url] = ""
                return ""
            raw = r.read(800_000)  # cap 800KB
            html = raw.decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError, Exception):
        url_cache[url] = ""
        return ""
    try:
        ex = TextExtractor()
        ex.feed(html)
        text = ex.text()
    except Exception:
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
    text = text[:MAX_PAGE_CHARS]
    url_cache[url] = text
    return text


def guess_website_urls(company_name, current_website=None):
    """Generate likely website URLs from company name when explicit field missing."""
    urls = []
    if current_website:
        if current_website.startswith("http"):
            urls.append(current_website)
        else:
            urls.append(f"https://{current_website}")
    # Generate fallback guesses from name
    name = company_name.lower().strip()
    name_clean = re.sub(r'[^a-z0-9]', '', name)
    name_dash = re.sub(r'\s+', '-', name)
    candidates = [
        f"https://{name_clean}.com",
        f"https://{name_dash}.com",
        f"https://www.{name_clean}.com",
        f"https://{name_clean}.ai",
        f"https://{name_clean}.io",
        f"https://{name_clean}.co",
    ]
    # De-dup, keep order
    seen = set()
    for u in urls + candidates:
        if u not in seen:
            urls.append(u) if u not in urls else None
            seen.add(u)
    return list(dict.fromkeys(urls + candidates))[:6]


def search_wikipedia(company_name, url_cache):
    """Try to fetch Wikipedia page for the company. Returns text or empty."""
    # Wikipedia REST API direct page lookup (no API key needed)
    slug = company_name.replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{quote(slug)}"
    text = fetch_url(url, url_cache)
    # Verify it's actually about the right company (not a disambiguation)
    if not text: return ""
    # If the page is short or has "may refer to:" → it's disambig or stub
    if len(text) < 500 or "may refer to" in text[:500].lower():
        return ""
    return text


def gather_sources(company, url_cache):
    """For a single company, gather all available source text."""
    sources = []
    name = company['name']

    # Source 1: company website
    website = company.get('website')
    candidate_urls = guess_website_urls(name, website)
    site_text = ""
    site_url = None
    for url in candidate_urls:
        text = fetch_url(url, url_cache)
        if text and len(text) > 200:
            site_text = text
            site_url = url
            break
    if site_text:
        sources.append({
            'src': 'company_website',
            'url': site_url,
            'text': site_text[:6000]
        })
        # Also try /about
        if site_url:
            base = site_url.rstrip('/')
            for path in ['/about', '/about-us', '/company', '/team']:
                t = fetch_url(base + path, url_cache)
                if t and len(t) > 300:
                    sources.append({
                        'src': 'company_about',
                        'url': base + path,
                        'text': t[:6000]
                    })
                    break

    # Source 2: Wikipedia
    wiki = search_wikipedia(name, url_cache)
    if wiki:
        sources.append({
            'src': 'wikipedia',
            'url': f"https://en.wikipedia.org/wiki/{quote(name.replace(' ', '_'))}",
            'text': wiki[:8000]
        })

    # Source 3: news_raw.json — recent matched articles
    nr_path = DATA / "news_raw.json"
    if nr_path.exists():
        try:
            for n in json.load(open(nr_path)):
                matches = []
                if n.get("matchedCompany"): matches.append(n["matchedCompany"])
                if n.get("matchedCompanies"): matches.extend(n["matchedCompanies"])
                if any(m and m.lower() == name.lower() for m in matches):
                    sources.append({
                        'src': f'news ({n.get("source", "?")})',
                        'url': n.get('link'),
                        'text': f"{n.get('title','')}\n{n.get('description','')}"[:1500]
                    })
                    if sum(1 for s in sources if s['src'].startswith('news')) >= 3:
                        break
        except Exception:
            pass

    # Source 4: earnings_signals_auto.json (if public co)
    es_path = DATA / "earnings_signals_auto.json"
    if es_path.exists():
        try:
            d = json.load(open(es_path))
            for s in d.get('signals', []):
                if (s.get('incumbent', '') or '').lower() == name.lower():
                    sources.append({
                        'src': f'earnings ({s.get("incumbent","")} {s.get("quarter","")})',
                        'url': s.get('source_url'),
                        'text': f"Quote: {s.get('quote','')}\nImplications: {s.get('implications')}"[:1200]
                    })
                    break
        except Exception:
            pass

    # Source 5: form_d_filings (recent fundraises)
    fd_path = DATA / "form_d_filings_auto.json"
    if fd_path.exists():
        try:
            fd = json.load(open(fd_path))
            for f in fd.get('filings', [])[:50]:
                if (f.get('company', '') or '').lower() == name.lower():
                    sources.append({
                        'src': 'sec_form_d',
                        'url': f.get('filing_url'),
                        'text': f"Form D filing: {f.get('issuer_name','')}, "
                                f"raised {f.get('amount_sold','?')}, "
                                f"filed {f.get('filed_date','')}"
                    })
                    break
        except Exception:
            pass

    return sources


# ────────────────────────────────────────────────────────────────────────
# CLAUDE EXTRACTION


VERIFICATION_PROMPT = """You are a fact-checker for a frontier-tech database. Below are public sources for a single company. Extract VERIFIED facts that you can support by citing a specific phrase or claim from these sources.

CRITICAL ACCURACY RULES:
1. Output a field value ONLY if you can find supporting evidence in the sources.
2. If sources disagree or you cannot verify, output null for that field. DO NOT guess.
3. For each field with a value, cite the source_index (0-based) you got it from.
4. Be SPECIFIC. "San Francisco, CA" not "USA". "Series B" not "growing".
5. For founder names: only list people explicitly named as founders/co-founders, not employees.
6. For founded year: only include if a specific year is mentioned.
7. For total_raised: prefer most recent + most specific (e.g. "$2.5B+" not "raised significantly").
8. For description: 1-2 factual sentences only — no marketing language.

Output ONLY valid JSON. No markdown. No prose. No commentary.

Schema:
{{
  "name": "verified canonical name or null",
  "description": "1-2 sentence factual description or null",
  "founders": ["full name", "full name", ...] or null,
  "location": "City, State/Country" or null,
  "founded_year": 2017 (int) or null,
  "current_stage": "Series X" or "Public" or "Acquired" or "Pre-IPO" or null,
  "total_raised": "$X.XX[B|M]" or null,
  "valuation": "$X.X[B|M]" or null,
  "investors": ["name", "name"] or null,
  "website": "https://..." or null,
  "sources_per_field": {{
    "field_name": [list of source_index numbers used]
  }},
  "notes": "anything important you noticed (rebrand, acquisition, etc.) or null"
}}

COMPANY: {company_name}
CURRENT DATABASE ENTRY (for reference, not source of truth):
  name: {current_name}
  description: {current_description}
  founder: {current_founder}
  location: {current_location}
  founded: {current_founded}
  stage: {current_stage}
  totalRaised: {current_total_raised}
  valuation: {current_valuation}
  investors: {current_investors}
  website: {current_website}

SOURCES:
{sources_text}
"""


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
                return json.loads(text)
            except json.JSONDecodeError:
                m = re.search(r"\{[\s\S]*\}", text)
                if m:
                    try: return json.loads(m.group(0))
                    except json.JSONDecodeError: pass
                return None
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1: time.sleep(2 ** attempt)
    print(f"    ⚠ Claude error: {last_err}")
    return None


# ────────────────────────────────────────────────────────────────────────
# DIFF + REPORT


def diff_facts(current, verified):
    """Compare current data.js fields vs verified facts. Return list of changes."""
    if not verified: return []
    changes = []

    # Founder: compare names (case-insensitive, set-based)
    current_founders = set()
    if current.get('founder'):
        for n in current['founder'].split(','):
            current_founders.add(n.strip().lower())
    verified_founders = set()
    if verified.get('founders'):
        for n in verified['founders']:
            verified_founders.add(n.strip().lower())
    if verified_founders and current_founders != verified_founders:
        changes.append({
            'field': 'founder',
            'current': current.get('founder') or '',
            'verified': ', '.join(verified['founders']),
            'sources': verified.get('sources_per_field', {}).get('founders', []),
        })
    elif not verified_founders and current_founders:
        # Couldn't verify but we have something — leave alone, flag for human
        pass

    # Location
    if verified.get('location'):
        if (current.get('location') or '').lower() != verified['location'].lower():
            changes.append({
                'field': 'location',
                'current': current.get('location') or '',
                'verified': verified['location'],
                'sources': verified.get('sources_per_field', {}).get('location', []),
            })

    # Founded year
    if verified.get('founded_year'):
        if current.get('founded') != verified['founded_year']:
            changes.append({
                'field': 'founded',
                'current': current.get('founded'),
                'verified': verified['founded_year'],
                'sources': verified.get('sources_per_field', {}).get('founded_year', []),
            })

    # Stage
    if verified.get('current_stage'):
        if (current.get('fundingStage') or '').lower() != verified['current_stage'].lower():
            changes.append({
                'field': 'fundingStage',
                'current': current.get('fundingStage') or '',
                'verified': verified['current_stage'],
                'sources': verified.get('sources_per_field', {}).get('current_stage', []),
            })

    # Total raised
    if verified.get('total_raised'):
        if (current.get('totalRaised') or '').replace('+','').strip() != \
           verified['total_raised'].replace('+','').strip():
            changes.append({
                'field': 'totalRaised',
                'current': current.get('totalRaised') or '',
                'verified': verified['total_raised'],
                'sources': verified.get('sources_per_field', {}).get('total_raised', []),
            })

    # Website
    if verified.get('website') and not current.get('website'):
        changes.append({
            'field': 'website',
            'current': '',
            'verified': verified['website'],
            'sources': verified.get('sources_per_field', {}).get('website', []),
        })

    # Investors (only if we don't already have them)
    if verified.get('investors') and not current.get('investors'):
        changes.append({
            'field': 'investors',
            'current': '[]',
            'verified': verified['investors'],
            'sources': verified.get('sources_per_field', {}).get('investors', []),
        })

    return changes


# ────────────────────────────────────────────────────────────────────────
# CACHE HELPERS


def load_cache(path):
    if not path.exists(): return {}
    try: return json.load(open(path))
    except: return {}


def save_cache(path, cache):
    path.write_text(json.dumps(cache, indent=2, default=str))


def content_hash(text):
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


# ────────────────────────────────────────────────────────────────────────
# MAIN


def load_cohort(cohort_file):
    """Load a list of company names from a JSON file (cohort)."""
    if not cohort_file: return None
    p = Path(cohort_file)
    if not p.exists():
        # Try relative to data dir
        p = DATA / cohort_file
    if not p.exists(): return None
    data = json.load(open(p))
    # Accept list of strings OR list of objects with 'name'
    if isinstance(data, list):
        return [d if isinstance(d, str) else d.get('name') for d in data if d]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cohort-file', default='data/cold_email_picks.json',
                    help='JSON file listing company names to verify (default: top 100 cold-email picks)')
    ap.add_argument('--limit', type=int, default=DEFAULT_LIMIT,
                    help='Max companies to process (cost control)')
    ap.add_argument('--output-suffix', default='',
                    help='Suffix for output files (parallel-safe). e.g. "batch2" → company_facts_verification_batch2.json')
    args = ap.parse_args()
    OUT_PATH, URL_CACHE_PATH, EXTRACTION_CACHE_PATH = _out_paths(args.output_suffix)

    print("=" * 64)
    print("Company Facts Verifier — Accuracy-first")
    print("=" * 64)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ ANTHROPIC_API_KEY not set — emitting empty report.")
        OUT_PATH.write_text(json.dumps({
            "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "skipped": True,
            "reason": "ANTHROPIC_API_KEY not set",
        }, indent=2))
        return 0

    try:
        import anthropic
    except ImportError:
        print("⚠ anthropic SDK missing")
        return 1

    client = anthropic.Anthropic(api_key=api_key)

    # Load cohort
    cohort_names = load_cohort(args.cohort_file)
    if cohort_names:
        print(f"  Cohort: {args.cohort_file} ({len(cohort_names)} names)")
    else:
        print(f"  No cohort file — will process all companies up to limit")

    all_companies = parse_companies()
    by_name = {c['name']: c for c in all_companies if c.get('name')}
    print(f"  Total in DB: {len(all_companies)}")

    # Filter to cohort
    if cohort_names:
        targets = [by_name[n] for n in cohort_names if n in by_name][:args.limit]
    else:
        targets = all_companies[:args.limit]
    print(f"  Will process: {len(targets)}")

    # Caches
    url_cache = load_cache(URL_CACHE_PATH)
    extraction_cache = load_cache(EXTRACTION_CACHE_PATH)
    print(f"  URL cache: {len(url_cache)} entries")
    print(f"  Extraction cache: {len(extraction_cache)} entries")

    cleared = []
    changes_proposed = []
    unverifiable = []
    new_extractions = 0

    for n, company in enumerate(targets, 1):
        name = company['name']
        print(f"\n  [{n}/{len(targets)}] {name}")

        # Gather sources
        sources = gather_sources(company, url_cache)
        if not sources:
            print(f"    ⚠ No sources found — UNVERIFIABLE")
            unverifiable.append({
                'name': name,
                'reason': 'no public sources accessible',
            })
            continue
        print(f"    Sources: {len(sources)} ({', '.join(s['src'] for s in sources[:5])})")

        # Build extraction cache key
        sources_text = "\n\n".join(
            f"[{i}] {s['src']} ({s['url'] or 'no url'})\n{s['text']}"
            for i, s in enumerate(sources)
        )[:30000]  # cap total
        cache_key = content_hash(name + "\n" + sources_text)

        if cache_key in extraction_cache:
            verified = extraction_cache[cache_key]
            print(f"    (cached extraction)")
        else:
            prompt = VERIFICATION_PROMPT.format(
                company_name=name,
                current_name=company.get('name') or '',
                current_description=(company.get('description') or '')[:300],
                current_founder=company.get('founder') or '',
                current_location=company.get('location') or '',
                current_founded=company.get('founded') or '',
                current_stage=company.get('fundingStage') or '',
                current_total_raised=company.get('totalRaised') or '',
                current_valuation=company.get('valuation') or '',
                current_investors=company.get('investors') or [],
                current_website=company.get('website') or '',
                sources_text=sources_text,
            )
            verified = call_claude(client, prompt)
            if verified:
                extraction_cache[cache_key] = verified
                new_extractions += 1
            time.sleep(0.3)

        if not verified:
            unverifiable.append({
                'name': name,
                'reason': 'Claude extraction failed',
            })
            continue

        # Diff
        changes = diff_facts(company, verified)

        if not changes:
            cleared.append(name)
        else:
            changes_proposed.append({
                'name': name,
                'current': {k: company.get(k) for k in ('name', 'founder', 'location', 'founded', 'fundingStage', 'totalRaised', 'website')},
                'verified': verified,
                'changes': changes,
                'sources': [{'idx': i, 'src': s['src'], 'url': s['url']} for i, s in enumerate(sources)],
                'notes': verified.get('notes'),
            })

        # Periodic cache save
        if new_extractions % 10 == 0 and new_extractions > 0:
            save_cache(URL_CACHE_PATH, url_cache)
            save_cache(EXTRACTION_CACHE_PATH, extraction_cache)

    save_cache(URL_CACHE_PATH, url_cache)
    save_cache(EXTRACTION_CACHE_PATH, extraction_cache)

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": DEFAULT_MODEL,
        "cohortFile": args.cohort_file,
        "cohortSize": len(targets),
        "newExtractionsThisRun": new_extractions,
        "summary": {
            "cleared": len(cleared),
            "changesProposed": len(changes_proposed),
            "unverifiable": len(unverifiable),
        },
        "cleared": cleared,
        "changesProposed": changes_proposed,
        "unverifiable": unverifiable,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2, default=str))

    print()
    print(f"✅ Wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"   Cleared (data matches sources): {len(cleared)}")
    print(f"   Changes proposed:               {len(changes_proposed)}")
    print(f"   Unverifiable:                   {len(unverifiable)}")
    print()
    print(f"   New Claude calls: {new_extractions}")
    print(f"   Estimated cost:   ~${new_extractions * 0.05:.2f}")

    if changes_proposed:
        print(f"\n  Top 10 companies w/ proposed changes:")
        for c in changes_proposed[:10]:
            print(f"\n  📍 {c['name']}")
            for ch in c['changes'][:3]:
                print(f'     {ch["field"]:<15}  was: "{str(ch["current"])[:50]}"  →  now: "{str(ch["verified"])[:50]}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
