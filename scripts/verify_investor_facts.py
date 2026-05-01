#!/usr/bin/env python3
"""
Investor Facts Verifier — accuracy-first, mirrors verify_company_facts.py.

For each VC firm in VC_FIRMS (or a specified cohort), gathers public sources
(firm website, Wikipedia, news mentions of the firm, Form D filings where
they're listed as a fund manager) and uses Claude to extract verified facts.
Outputs proposed changes for human review before any data.js modifications.

ACCURACY CONTRACT:
  - Only output a field value if Claude can cite a specific source phrase.
  - Empty/null is correct when sources don't support the field.
  - Worst outcome: incorrect data.

INPUTS PER FIRM:
  1. Firm website (homepage + /team + /about + /portfolio)
  2. Wikipedia
  3. Existing news mentions (from news_raw.json where the firm name appears)
  4. Form D filings where firm is fund manager (form_d_filings_auto.json)

FIELDS VERIFIED:
  - name (canonical full name)
  - shortName
  - aum (size of assets under management)
  - flagshipFund (current main fund name)
  - founded (year)
  - hq (city, state/country)
  - keyPartners (top partners — comma-separated list of full names)
  - sectorFocus (areas of investment, list)
  - thesis (1-3 sentence summary of investment thesis)
  - website (canonical URL)

NOT verified (curator-set):
  - signal, insight  → human judgment, not extracted from sources
  - portfolioCompanies → DERIVED separately by derive_investor_portfolios.py
                         from COMPANIES.investors[] (more reliable)

OUTPUT:
  data/investor_facts_verification[_suffix].json

USAGE:
  python scripts/verify_investor_facts.py [--cohort-file PATH] [--limit N] [--output-suffix S]

  --cohort-file PATH   JSON list of firm names to verify.
                       Default: all VC_FIRMS up to limit.
  --limit N            Max firms to process (cost control)
  --output-suffix S    Suffix for output files (parallel-safe)
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


def _out_paths(suffix=""):
    suf = f"_{suffix}" if suffix else ""
    return (
        DATA / f"investor_facts_verification{suf}.json",
        DATA / ".investor_facts_url_cache.json",
        DATA / ".investor_facts_extraction_cache.json",
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
MAX_PAGE_CHARS = 12000


# ────────────────────────────────────────────────────────────────────────
# VC_FIRMS PARSING (brace-aware, mirrors COMPANIES parser)


def parse_vc_firms():
    src = DATA_JS.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'const VC_FIRMS\s*=\s*\[', src)
    if not m: return []
    start = m.end() - 1
    depth = 0
    in_str = False
    str_q = None
    i = start
    block = None
    while i < len(src):
        ch = src[i]
        if in_str:
            if ch == '\\': i += 2; continue
            if ch == str_q: in_str = False
        else:
            if ch in ('"', "'", '`'):
                in_str = True
                str_q = ch
            elif ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    block = src[start:i+1]
                    break
        i += 1
    if block is None:
        return []

    firms = []
    obj_depth = 0
    obj_start = None
    in_str = False
    str_q = None
    for i, ch in enumerate(block):
        if in_str:
            if ch == '\\': continue
            if ch == str_q: in_str = False
        else:
            if ch in ('"', "'", '`'):
                in_str = True; str_q = ch
            elif ch == '{':
                if obj_depth == 0: obj_start = i
                obj_depth += 1
            elif ch == '}':
                obj_depth -= 1
                if obj_depth == 0 and obj_start is not None:
                    obj = block[obj_start:i+1]

                    def grab(field):
                        mm = re.search(rf'\b{field}\s*:\s*"((?:[^"\\]|\\.)*)"', obj)
                        return mm.group(1) if mm else None

                    def grab_int(field):
                        mm = re.search(rf'\b{field}\s*:\s*(\d+)', obj)
                        return int(mm.group(1)) if mm else None

                    def grab_arr(field):
                        mm = re.search(rf'\b{field}\s*:\s*\[((?:[^\[\]"]|"(?:[^"\\]|\\.)*")*)\]', obj)
                        if not mm: return []
                        return re.findall(r'"((?:[^"\\]|\\.)*)"', mm.group(1))

                    firms.append({
                        'name': grab('name'),
                        'shortName': grab('shortName'),
                        'aum': grab('aum'),
                        'flagshipFund': grab('flagshipFund'),
                        'founded': grab_int('founded'),
                        'hq': grab('hq'),
                        'thesis': grab('thesis'),
                        'keyPartners': grab_arr('keyPartners'),
                        'sectorFocus': grab_arr('sectorFocus'),
                        'portfolioCompanies': grab_arr('portfolioCompanies'),
                        'signal': grab('signal'),
                        'website': grab('website'),
                        'insight': grab('insight'),
                    })
                    obj_start = None
    return firms


# ────────────────────────────────────────────────────────────────────────
# WEB FETCHING (shared logic — copied from verify_company_facts.py)


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
            raw = r.read(800_000)
            html = raw.decode("utf-8", errors="replace")
    except Exception:
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


def guess_firm_urls(name, short_name=None, current_website=None):
    """Generate likely website URLs for a VC firm."""
    urls = []
    if current_website:
        urls.append(current_website if current_website.startswith("http") else f"https://{current_website}")

    candidates = []
    for n in filter(None, [name, short_name]):
        clean = re.sub(r'[^a-z0-9]', '', n.lower())
        dashed = re.sub(r'\s+', '-', n.lower())
        candidates.extend([
            f"https://{clean}.com",
            f"https://{dashed}.com",
            f"https://www.{clean}.com",
            f"https://{clean}.vc",
            f"https://{clean}.ventures",
            f"https://{clean}capital.com",
        ])

    seen = set()
    out = []
    for u in urls + candidates:
        if u not in seen:
            seen.add(u); out.append(u)
    return out[:8]


def search_wikipedia(name, url_cache):
    slug = name.replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{quote(slug)}"
    text = fetch_url(url, url_cache)
    if not text: return ""
    if len(text) < 500 or "may refer to" in text[:500].lower():
        return ""
    return text


def gather_sources(firm, url_cache):
    sources = []
    name = firm['name']
    short = firm.get('shortName')

    # Source 1: firm website
    candidate_urls = guess_firm_urls(name, short, firm.get('website'))
    site_text = ""
    site_url = None
    for url in candidate_urls:
        text = fetch_url(url, url_cache)
        if text and len(text) > 200:
            site_text = text
            site_url = url
            break
    if site_text:
        sources.append({'src': 'firm_website', 'url': site_url, 'text': site_text[:6000]})
        if site_url:
            base = site_url.rstrip('/')
            for path in ['/about', '/team', '/portfolio', '/companies', '/investments']:
                t = fetch_url(base + path, url_cache)
                if t and len(t) > 300:
                    sources.append({'src': f'firm{path}', 'url': base + path, 'text': t[:6000]})

    # Source 2: Wikipedia
    wiki = search_wikipedia(name, url_cache)
    if wiki:
        sources.append({
            'src': 'wikipedia',
            'url': f"https://en.wikipedia.org/wiki/{quote(name.replace(' ', '_'))}",
            'text': wiki[:8000]
        })
    elif short and short != name:
        wiki = search_wikipedia(short, url_cache)
        if wiki:
            sources.append({
                'src': 'wikipedia (short name)',
                'url': f"https://en.wikipedia.org/wiki/{quote(short.replace(' ', '_'))}",
                'text': wiki[:8000]
            })

    # Source 3: news mentions of the firm
    nr_path = DATA / "news_raw.json"
    if nr_path.exists():
        try:
            news_count = 0
            for n in json.load(open(nr_path)):
                title = (n.get("title") or "").lower()
                desc = (n.get("description") or "").lower()
                blob = title + " " + desc
                if name.lower() in blob or (short and short.lower() in blob):
                    sources.append({
                        'src': f'news ({n.get("source", "?")})',
                        'url': n.get('link'),
                        'text': f"{n.get('title','')}\n{n.get('description','')}"[:1500]
                    })
                    news_count += 1
                    if news_count >= 4:
                        break
        except Exception:
            pass

    # Source 4: Form D filings where firm is the fund manager
    fd_path = DATA / "form_d_filings_auto.json"
    if fd_path.exists():
        try:
            fd = json.load(open(fd_path))
            count = 0
            for f in fd.get('filings', [])[:200]:
                manager = (f.get('issuer_name', '') or '').lower()
                if name.lower() in manager or (short and short.lower() in manager):
                    sources.append({
                        'src': 'sec_form_d',
                        'url': f.get('filing_url'),
                        'text': f"Form D filing: {f.get('issuer_name','')}, "
                                f"raised {f.get('amount_sold','?')}, "
                                f"filed {f.get('filed_date','')}"
                    })
                    count += 1
                    if count >= 3: break
        except Exception:
            pass

    return sources


# ────────────────────────────────────────────────────────────────────────
# CLAUDE EXTRACTION


VERIFICATION_PROMPT = """You are a fact-checker for a frontier-tech VC firm database. Below are public sources for a single venture capital firm. Extract VERIFIED facts that you can support by citing a specific phrase or claim from these sources.

CRITICAL ACCURACY RULES:
1. Output a field value ONLY if you can find supporting evidence in the sources.
2. If sources disagree or you cannot verify, output null. DO NOT guess.
3. For each field with a value, cite the source_index (0-based).
4. Be SPECIFIC. "$5B" not "billions". "Menlo Park, CA" not "Silicon Valley".
5. For partner names: only list current senior partners explicitly named on the firm's site/Wikipedia. Don't include former partners.
6. For founded year: only include if a specific year is mentioned in sources.
7. For AUM: prefer most recent + most specific figure. Use "$XB+" or "$XM+" notation.
8. For thesis: 1-3 factual sentences describing what the firm invests in. No marketing fluff.
9. For sectorFocus: extract from explicit sector lists/focus areas on the site. Don't infer from individual investments.

Output ONLY valid JSON. No markdown. No prose. No commentary.

Schema:
{{
  "name": "verified canonical name or null",
  "short_name": "common abbreviation or null",
  "aum": "$X[B|M]+ or null",
  "flagship_fund": "current main fund name or null",
  "founded_year": 2009 (int) or null,
  "hq": "City, State/Country or null",
  "key_partners": ["full name", ...] or null,
  "sector_focus": ["Sector1", "Sector2"] or null,
  "thesis": "1-3 sentence factual investment thesis or null",
  "website": "https://... or null",
  "sources_per_field": {{
    "field_name": [list of source_index numbers]
  }},
  "notes": "anything important (rebrand, recent leadership change, fund close, etc.) or null"
}}

FIRM: {firm_name}
CURRENT DATABASE ENTRY (for reference, not source of truth):
  name: {current_name}
  shortName: {current_short_name}
  aum: {current_aum}
  flagshipFund: {current_flagship}
  founded: {current_founded}
  hq: {current_hq}
  keyPartners: {current_partners}
  sectorFocus: {current_sectors}
  thesis: {current_thesis}
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
    """Compare current VC_FIRMS fields vs verified facts."""
    if not verified: return []
    changes = []

    def add(field, current_val, verified_val, sources_key=None):
        if verified_val is None or verified_val == "" or verified_val == []:
            return
        # Compare with sane normalization
        cur_norm = (str(current_val) if current_val is not None else "").strip().lower()
        ver_norm = str(verified_val).strip().lower() if not isinstance(verified_val, list) else \
                   sorted([str(v).strip().lower() for v in verified_val])
        cur_cmp = cur_norm if not isinstance(verified_val, list) else \
                  sorted([str(v).strip().lower() for v in (current_val or [])])
        if cur_cmp != ver_norm:
            changes.append({
                'field': field,
                'current': current_val,
                'verified': verified_val,
                'sources': verified.get('sources_per_field', {}).get(sources_key or field, []),
            })

    # Map verifier output → DB field names
    add('name',         current.get('name'),         verified.get('name'),           'name')
    add('shortName',    current.get('shortName'),    verified.get('short_name'),     'short_name')
    add('aum',          current.get('aum'),          verified.get('aum'),            'aum')
    add('flagshipFund', current.get('flagshipFund'), verified.get('flagship_fund'),  'flagship_fund')
    add('founded',      current.get('founded'),      verified.get('founded_year'),   'founded_year')
    add('hq',           current.get('hq'),           verified.get('hq'),             'hq')
    add('keyPartners',  current.get('keyPartners'),  verified.get('key_partners'),   'key_partners')
    add('sectorFocus',  current.get('sectorFocus'),  verified.get('sector_focus'),   'sector_focus')
    add('thesis',       current.get('thesis'),       verified.get('thesis'),         'thesis')
    if verified.get('website') and not current.get('website'):
        changes.append({
            'field': 'website',
            'current': '',
            'verified': verified['website'],
            'sources': verified.get('sources_per_field', {}).get('website', []),
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
    if not cohort_file: return None
    p = Path(cohort_file)
    if not p.exists():
        p = DATA / cohort_file
    if not p.exists(): return None
    data = json.load(open(p))
    if isinstance(data, list):
        return [d if isinstance(d, str) else (d.get('name') or d.get('shortName')) for d in data if d]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cohort-file', default=None,
                    help='JSON file listing firm names to verify (default: all VC_FIRMS up to limit)')
    ap.add_argument('--limit', type=int, default=DEFAULT_LIMIT)
    ap.add_argument('--output-suffix', default='')
    args = ap.parse_args()

    OUT_PATH, URL_CACHE_PATH, EXTRACTION_CACHE_PATH = _out_paths(args.output_suffix)

    print("=" * 64)
    print("Investor Facts Verifier — Accuracy-first")
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

    cohort_names = load_cohort(args.cohort_file)
    all_firms = parse_vc_firms()
    by_name = {f['name']: f for f in all_firms if f.get('name')}
    by_short = {f['shortName']: f for f in all_firms if f.get('shortName')}
    print(f"  Total VC firms in DB: {len(all_firms)}")

    if cohort_names:
        targets = []
        for n in cohort_names:
            f = by_name.get(n) or by_short.get(n)
            if f and f not in targets:
                targets.append(f)
        targets = targets[:args.limit]
        print(f"  Cohort: {args.cohort_file} ({len(cohort_names)} names, {len(targets)} matched)")
    else:
        targets = all_firms[:args.limit]
        print(f"  No cohort file — processing all firms up to limit ({args.limit})")
    print(f"  Will process: {len(targets)}")

    url_cache = load_cache(URL_CACHE_PATH)
    extraction_cache = load_cache(EXTRACTION_CACHE_PATH)
    print(f"  URL cache: {len(url_cache)}, Extraction cache: {len(extraction_cache)}")

    cleared = []
    changes_proposed = []
    unverifiable = []
    new_extractions = 0

    for n, firm in enumerate(targets, 1):
        name = firm['name']
        print(f"\n  [{n}/{len(targets)}] {name}")

        sources = gather_sources(firm, url_cache)
        if not sources:
            print(f"    ⚠ No sources found — UNVERIFIABLE")
            unverifiable.append({'name': name, 'reason': 'no public sources accessible'})
            continue
        print(f"    Sources: {len(sources)} ({', '.join(s['src'] for s in sources[:5])})")

        sources_text = "\n\n".join(
            f"[{i}] {s['src']} ({s['url'] or 'no url'})\n{s['text']}"
            for i, s in enumerate(sources)
        )[:30000]
        cache_key = content_hash(name + "\n" + sources_text)

        if cache_key in extraction_cache:
            verified = extraction_cache[cache_key]
            print(f"    (cached extraction)")
        else:
            prompt = VERIFICATION_PROMPT.format(
                firm_name=name,
                current_name=firm.get('name') or '',
                current_short_name=firm.get('shortName') or '',
                current_aum=firm.get('aum') or '',
                current_flagship=firm.get('flagshipFund') or '',
                current_founded=firm.get('founded') or '',
                current_hq=firm.get('hq') or '',
                current_partners=firm.get('keyPartners') or [],
                current_sectors=firm.get('sectorFocus') or [],
                current_thesis=(firm.get('thesis') or '')[:300],
                current_website=firm.get('website') or '',
                sources_text=sources_text,
            )
            verified = call_claude(client, prompt)
            if verified:
                extraction_cache[cache_key] = verified
                new_extractions += 1
            time.sleep(0.3)

        if not verified:
            unverifiable.append({'name': name, 'reason': 'Claude extraction failed'})
            continue

        changes = diff_facts(firm, verified)
        if not changes:
            cleared.append(name)
        else:
            changes_proposed.append({
                'name': name,
                'current': {k: firm.get(k) for k in ('name', 'shortName', 'aum', 'flagshipFund',
                                                     'founded', 'hq', 'website')},
                'verified': verified,
                'changes': changes,
                'sources': [{'idx': i, 'src': s['src'], 'url': s['url']} for i, s in enumerate(sources)],
                'notes': verified.get('notes'),
            })

        if new_extractions % 5 == 0 and new_extractions > 0:
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
    print(f"   Cleared:        {len(cleared)}")
    print(f"   Changes:        {len(changes_proposed)}")
    print(f"   Unverifiable:   {len(unverifiable)}")
    print(f"   New Claude calls: {new_extractions}  (~${new_extractions * 0.05:.2f})")

    if changes_proposed:
        print(f"\n  Top 5 firms w/ proposed changes:")
        for c in changes_proposed[:5]:
            print(f"\n  📍 {c['name']}")
            for ch in c['changes'][:3]:
                cur = str(ch['current'])[:50]
                ver = str(ch['verified'])[:50]
                print(f'     {ch["field"]:<14}  was: "{cur}"  →  now: "{ver}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
