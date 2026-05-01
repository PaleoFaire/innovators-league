#!/usr/bin/env python3
"""
Build the unified Catalyst Calendar feed.

Reads from every dated-event source we have, normalizes to a common
schema, writes a single chronological JSON. The Catalyst Calendar UI
(catalysts.html) and any future surface that needs "what's about to
happen" reads ONLY from this file.

Eliminates the "4 calendar pipelines" redundancy by making every
existing source feed the same downstream view.

UNIFIED EVENT SCHEMA:
  {
    id:           string (stable, hash of source+date+entity)
    date:         "YYYY-MM-DD"
    type:         enum: fda | faa | nrc | fcc | water | trial |
                        formd | sbir | earnings | news | conf |
                        launch | funding | factory
    importance:   enum: urgent (<3d) | high (<14d) | medium (<60d) | low
    title:        short (≤120 chars)
    description:  longer narrative (≤500 chars)
    companies:    list of company names (matched to COMPANIES if possible)
    sector:       defense | space | bio | energy | nuclear | quantum | ai | other
    source:       human-readable source name
    sourceUrl:    URL to original source
    raw:          original record (for debugging / future reuse)
  }

Output: data/catalyst_calendar.json

Usage:
  python scripts/build_unified_calendar.py
"""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "catalyst_calendar.json"


# ────────────────────────────────────────────────────────────────────────
# Helpers


def parse_date(s):
    """Best-effort date parser. Returns 'YYYY-MM-DD' or None."""
    if not s: return None
    if isinstance(s, datetime): return s.strftime("%Y-%m-%d")
    s = str(s).strip()
    if not s: return None

    # ISO with time
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(s.split("+")[0].split(".")[0].replace("Z",""), "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            pass

    # Plain date variants
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%Y-%m"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # YYYYMMDD
    if re.match(r"^\d{8}$", s):
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"

    return None


def importance_for_days_out(days_out):
    if days_out is None: return "low"
    if days_out < 0: return "low"        # past events are low priority
    if days_out <= 3: return "urgent"
    if days_out <= 14: return "high"
    if days_out <= 60: return "medium"
    return "low"


def make_id(source, date, identifier):
    raw = f"{source}|{date}|{identifier}".lower()
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def load_json(path):
    if not Path(path).exists(): return None
    try: return json.load(open(path))
    except Exception: return None


def parse_js_array(path, varname):
    """Parse a JS file with `const VARNAME = [...]` or `var VARNAME = [...]`"""
    p = Path(path)
    if not p.exists(): return None
    src = p.read_text(encoding="utf-8")
    m = re.search(rf'(?:const|var|let)\s+{varname}\s*=\s*([\[\{{])', src)
    if not m: return None
    start = m.end() - 1
    open_ch = src[start]
    close_ch = "]" if open_ch == "[" else "}"
    depth = 0
    in_str = False
    str_q = None
    for i in range(start, len(src)):
        c = src[i]
        if in_str:
            if c == "\\": continue
            if c == str_q: in_str = False
        else:
            if c in ('"', "'", "`"):
                in_str = True; str_q = c
            elif c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    block = src[start:i+1]
                    return _js_to_json(block)
    return None


def _js_to_json(block):
    """Convert a JS array/object literal to parseable JSON.

    Single-pass state-aware walker: skips `//` and `/* */` comments only
    when NOT inside a string, and converts single-quoted JS strings to
    double-quoted JSON strings without mangling apostrophes inside
    already-double-quoted strings (e.g., `"World's premier"`).
    """
    out = []
    i = 0
    n = len(block)
    while i < n:
        c = block[i]
        # Comment? (only outside strings)
        if c == '/' and i + 1 < n:
            if block[i+1] == '/':
                # Line comment — skip to next \n
                while i < n and block[i] != '\n':
                    i += 1
                continue
            if block[i+1] == '*':
                # Block comment
                i += 2
                while i + 1 < n and not (block[i] == '*' and block[i+1] == '/'):
                    i += 1
                i += 2
                continue
        # JS double-quoted string — copy verbatim, handling escapes
        if c == '"':
            out.append(c); i += 1
            while i < n:
                cc = block[i]
                if cc == '\\' and i + 1 < n:
                    out.append(cc); out.append(block[i+1]); i += 2; continue
                out.append(cc); i += 1
                if cc == '"': break
            continue
        # JS single-quoted string → double-quoted JSON
        if c == "'":
            content = []
            i += 1
            while i < n:
                cc = block[i]
                if cc == '\\' and i + 1 < n:
                    content.append(cc); content.append(block[i+1]); i += 2; continue
                if cc == "'":
                    i += 1; break
                content.append(cc); i += 1
            inner = "".join(content)
            inner = inner.replace("\\", "\\\\").replace('"', '\\"')
            out.append('"' + inner + '"')
            continue
        # Backtick template literal
        if c == "`":
            content = []
            i += 1
            while i < n:
                cc = block[i]
                if cc == "`":
                    i += 1; break
                if cc == '\n':
                    content.append("\\n"); i += 1; continue
                content.append(cc); i += 1
            inner = "".join(content)
            inner = inner.replace("\\", "\\\\").replace('"', '\\"')
            out.append('"' + inner + '"')
            continue
        out.append(c); i += 1

    s = "".join(out)
    s = re.sub(r'([{\[,]\s*)([a-zA-Z_$][\w$]*)\s*:', r'\1"\2":', s)
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


# ────────────────────────────────────────────────────────────────────────
# Sector inference


SECTOR_KEYWORDS = {
    "defense":   ["drone", "missile", "weapon", "munition", "warhead", "tactical",
                  "military", "soldier", "army", "navy", "air force", "marine",
                  "kinetic", "directed energy", "anti-drone", "counter-drone",
                  "loitering", "ucav", "uav", "uas"],
    "space":     ["satellite", "rocket", "launch", "orbit", "lunar", "mars",
                  "spacecraft", "constellation", "geo", "leo", "starlink"],
    "bio":       ["fda", "clinical", "trial", "drug", "therapy", "vaccine",
                  "phase i", "phase ii", "phase iii", "biotech", "gene",
                  "antibody", "monoclonal", "diagnostic", "510(k)", "pma"],
    "energy":    ["solar", "wind", "battery", "storage", "grid", "power"],
    "nuclear":   ["reactor", "smr", "fission", "uranium", "triso", "fuel",
                  "nrc", "fusion"],
    "quantum":   ["quantum", "qubit", "photonic", "cryogenic"],
    "ai":        ["llm", "neural", "training", "inference", "transformer",
                  "agent", "foundation model"],
}


def infer_sector(text):
    if not text: return "other"
    t = str(text).lower()
    for sector, keys in SECTOR_KEYWORDS.items():
        if any(k in t for k in keys):
            return sector
    return "other"


# ────────────────────────────────────────────────────────────────────────
# Loaders — one per source, returns list of unified events


def load_fda(today):
    d = load_json(DATA / "fda_actions_raw.json")
    if not d: return []
    events = []
    for r in d:
        date = parse_date(r.get("date"))
        if not date: continue
        co = r.get("company") or ""
        product = r.get("product") or ""
        evt_type = r.get("type") or "FDA action"
        title = f"{co} — {evt_type}"
        if product and product not in title:
            title += f": {product}"
        events.append({
            "id": make_id("fda", date, f"{co}-{r.get('k_number','')}"),
            "date": date,
            "type": "fda",
            "title": title[:120],
            "description": f"{evt_type}. Status: {r.get('status','')}. K#: {r.get('k_number','')}",
            "companies": [co] if co else [],
            "sector": "bio",
            "source": "openFDA",
            "sourceUrl": "https://api.fda.gov/",
            "raw": r,
        })
    return events


def load_clinical_trials(today):
    d = load_json(DATA / "clinical_trials_active.json")
    if not d or not isinstance(d, list): return []
    events = []
    for r in d:
        # Use completionDate as the catalyst date
        date = parse_date(r.get("completionDate") or r.get("primaryCompletionDate"))
        if not date: continue
        sponsor = r.get("sponsor") or ""
        title = f"{sponsor or 'Trial'}: {(r.get('title') or '')[:80]} (Phase {r.get('phase','?')})"
        cond = r.get("conditions") or ""
        if isinstance(cond, list): cond = ", ".join(cond[:3])
        events.append({
            "id": make_id("trial", date, r.get("nctId", "")),
            "date": date,
            "type": "trial",
            "title": title[:120],
            "description": f"Phase {r.get('phase','?')} · {r.get('status','')} · {cond[:150]}",
            "companies": [sponsor] if sponsor else [],
            "sector": "bio",
            "source": "ClinicalTrials.gov",
            "sourceUrl": f"https://clinicaltrials.gov/study/{r.get('nctId','')}",
            "raw": r,
        })
    return events


def load_faa(today):
    d = parse_js_array(DATA / "faa_certification_auto.js", "FAA_CERTIFICATION_AUTO") \
        or load_json(DATA / "faa_certification_auto.json")
    if not d: return []
    if isinstance(d, dict): d = d.get("certifications") or d.get("data") or []
    events = []
    for r in d:
        co = r.get("company") or ""
        sector_hint = (r.get("aircraft") or "") + " " + (r.get("category") or "")
        # FAA certs have a nested milestones array; emit one event per milestone
        # plus one for the nextMilestone if dated.
        for ms in (r.get("milestones") or []):
            date = parse_date(ms.get("date"))
            if not date: continue
            evt = ms.get("event") or ""
            events.append({
                "id": make_id("faa", date, f"{co}-{r.get('aircraft','')}-{evt}"),
                "date": date,
                "type": "faa",
                "title": f"{co} — FAA: {evt}"[:120],
                "description": f"{r.get('certType','')} · Aircraft: {r.get('aircraft','')} · Milestone status: {ms.get('status','')}",
                "companies": [co] if co else [],
                "sector": infer_sector(sector_hint + " " + evt),
                "source": "FAA Type Cert tracker",
                "sourceUrl": r.get("faaProject") or "https://www.faa.gov/",
                "raw": {**r, "_milestone": ms},
            })
        nm_date = parse_date(r.get("nextMilestoneDate"))
        nm_evt = r.get("nextMilestone")
        if nm_date and nm_evt and nm_evt != "N/A":
            events.append({
                "id": make_id("faa-next", nm_date, f"{co}-{nm_evt}"),
                "date": nm_date,
                "type": "faa",
                "title": f"{co} — FAA: {nm_evt} (upcoming)"[:120],
                "description": f"{r.get('certType','')} · Aircraft: {r.get('aircraft','')} · Status: {r.get('status','')}",
                "companies": [co] if co else [],
                "sector": infer_sector(sector_hint),
                "source": "FAA Type Cert tracker",
                "sourceUrl": r.get("faaProject") or "https://www.faa.gov/",
                "raw": r,
            })
    return events


def _extract_year_date(text):
    """Extract a YYYY-MM or YYYY date hint from a free-text milestone string.
    Returns YYYY-01-01 if only a year is found; YYYY-MM-01 if month+year.
    Returns None if nothing recognizable."""
    if not text: return None
    s = str(text)
    # YYYY-MM-DD anywhere
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # Month YYYY (e.g., "January 2027", "Q1 2027")
    months = "(January|February|March|April|May|June|July|August|September|October|November|December)"
    m = re.search(rf"{months}\s+(\d{{4}})", s, re.IGNORECASE)
    if m:
        mn = datetime.strptime(m.group(1)[:3], "%b").month
        return f"{m.group(2)}-{mn:02d}-01"
    # "Q[1-4] YYYY"
    m = re.search(r"Q([1-4])\s*(\d{4})", s, re.IGNORECASE)
    if m:
        q = int(m.group(1)); return f"{m.group(2)}-{(q-1)*3+1:02d}-01"
    # Bare year
    m = re.search(r"\b(20\d{2})\b", s)
    if m: return f"{m.group(1)}-06-01"   # mid-year as approximation
    return None


def load_nrc(today):
    d = load_json(DATA / "nrc_licensing_auto.json")
    if not d: return []
    events = []
    for r in d:
        # nextMilestone is free-text like "2027 Operating License Application"
        # — extract a year. Fall back to lastUpdated.
        date = parse_date(r.get("lastUpdated"))
        nm_text = r.get("nextMilestone") or ""
        nm_date = _extract_year_date(nm_text)
        co = r.get("company") or ""
        # Emit "next milestone" event if we have a date hint
        if nm_date:
            events.append({
                "id": make_id("nrc-next", nm_date, f"{co}-{r.get('docketId','')}"),
                "date": nm_date,
                "type": "nrc",
                "title": f"{co} — NRC: {nm_text[:80]}"[:120],
                "description": f"Design: {r.get('design','')} · Stage: {r.get('stage','')} · Docket: {r.get('docketId','')}",
                "companies": [co] if co else [],
                "sector": "nuclear",
                "source": "NRC Licensing tracker",
                "sourceUrl": r.get("url") or "https://www.nrc.gov/",
                "raw": r,
            })
        # Emit current-state event for "what just happened"
        if date:
            events.append({
                "id": make_id("nrc", date, f"{co}-{r.get('docketId','')}"),
                "date": date,
                "type": "nrc",
                "title": f"{co} — NRC: {r.get('design','')[:60]} ({r.get('stage','')})"[:120],
                "description": f"Status: {r.get('status','')[:200]} · Docket: {r.get('docketId','')}",
                "companies": [co] if co else [],
                "sector": "nuclear",
                "source": "NRC Licensing tracker",
                "sourceUrl": r.get("url") or "https://www.nrc.gov/",
                "raw": r,
            })
    return events


def load_fcc(today):
    d = load_json(DATA / "fcc_licenses_auto.json")
    if not d: return []
    filings = d.get("filings", []) if isinstance(d, dict) else d
    events = []
    for r in filings:
        date = parse_date(r.get("filing_date"))
        if not date: continue
        ap = r.get("applicant") or ""
        title = f"{ap} — FCC: {r.get('service_type','')} {r.get('frequency_band','')}".strip()
        events.append({
            "id": make_id("fcc", date, r.get("filing_id", "")),
            "date": date,
            "type": "fcc",
            "title": title[:120],
            "description": f"Purpose: {r.get('purpose','')} · Bureau: {r.get('bureau','')} · Location: {r.get('location','')}",
            "companies": [ap] if ap else [],
            "sector": infer_sector((r.get("service_type") or "") + " " + (r.get("purpose") or "")),
            "source": "FCC ULS",
            "sourceUrl": "https://www.fcc.gov/",
            "raw": r,
        })
    return events


def load_form_d(today):
    d = load_json(DATA / "form_d_filings_auto.json")
    if not d: return []
    filings = d.get("filings", []) if isinstance(d, dict) else d
    events = []
    for r in filings:
        date = parse_date(r.get("filed_date") or r.get("first_sale_date"))
        if not date: continue
        co = r.get("company") or r.get("issuer_name") or ""
        amount = r.get("amount_sold") or r.get("offering_amount") or "?"
        title = f"{co} — Form D: ${amount} sold"
        events.append({
            "id": make_id("formd", date, r.get("accession", "")),
            "date": date,
            "type": "formd",
            "title": title[:120],
            "description": f"Securities: {r.get('securities_type','')} · Exemption: {r.get('exemption','')} · CIK: {r.get('cik','')}",
            "companies": [co] if co else [],
            "sector": "other",
            "source": "SEC EDGAR Form D",
            "sourceUrl": r.get("filing_url") or "https://www.sec.gov/",
            "raw": r,
        })
    return events


def load_sbir(today):
    d = load_json(DATA / "sbir_topics_auto.json")
    if not d: return []
    events = []
    for r in d:
        date = parse_date(r.get("closeDate"))
        if not date: continue
        events.append({
            "id": make_id("sbir", date, r.get("id", "")),
            "date": date,
            "type": "sbir",
            "title": f"{r.get('agency','')} SBIR — {r.get('title','')}"[:120],
            "description": f"Phase: {r.get('phase','')} · Award: {r.get('award','')} · Type: {r.get('type','')}",
            "companies": [],   # not company-specific; this is opportunity flow
            "sector": infer_sector(r.get("title") or ""),
            "source": "SBIR.gov",
            "sourceUrl": "https://www.sbir.gov/",
            "raw": r,
        })
    return events


def load_earnings(today):
    d = load_json(DATA / "earnings_signals_auto.json")
    if not d: return []
    signals = d.get("signals", []) if isinstance(d, dict) else d
    events = []
    for s in signals:
        date = parse_date(s.get("date") or s.get("filing_date") or s.get("quarter"))
        if not date: continue
        co = s.get("incumbent") or s.get("company") or ""
        events.append({
            "id": make_id("earnings", date, f"{co}-{s.get('quarter','')}"),
            "date": date,
            "type": "earnings",
            "title": f"{co} — earnings signal {s.get('quarter','')}"[:120],
            "description": (s.get("quote") or s.get("implications") or "")[:300],
            "companies": [co] if co else [],
            "sector": infer_sector((co or "") + " " + (s.get("quote") or "")),
            "source": s.get("source") or "Earnings transcripts",
            "sourceUrl": s.get("source_url") or "",
            "raw": s,
        })
    return events


def load_federal_register(today):
    """Federal Register entries (regulatory notices)."""
    d = parse_js_array(DATA / "federal_register_auto.js", "FEDERAL_REGISTER")
    if not d: return []
    events = []
    for r in d:
        date = parse_date(r.get("date"))
        if not date: continue
        agencies = r.get("agencies") or ""
        # Classify by agency for better cluster mapping
        ag = agencies.lower()
        if "nuclear regulatory" in ag: ev_type, sector = "nrc", "nuclear"
        elif "aviation" in ag or "faa" in ag: ev_type, sector = "faa", "space"
        elif "energy department" in ag or "doe" in ag: ev_type, sector = "doe", "energy"
        elif "food and drug" in ag or "fda" in ag: ev_type, sector = "fda", "bio"
        elif "defense" in ag or "army" in ag: ev_type, sector = "fedreg", "defense"
        else: ev_type, sector = "fedreg", "other"
        events.append({
            "id": make_id("fedreg", date, r.get("docNum", "")),
            "date": date,
            "type": ev_type,
            "title": (r.get("title") or "Federal Register notice")[:120],
            "description": f"{agencies}{(' · Sectors: ' + r.get('sectors', '')) if r.get('sectors') else ''} · Type: {r.get('type', '')}",
            "companies": [],
            "sector": sector,
            "source": "Federal Register",
            "sourceUrl": f"https://www.federalregister.gov/d/{r.get('docNum', '')}",
            "raw": r,
        })
    return events


def load_doe_programs(today):
    """DOE program funding announcements from data/doe_programs_auto.js."""
    d = parse_js_array(DATA / "doe_programs_auto.js", "DOE_PROGRAMS")
    if not d: return []
    events = []
    for r in d:
        date = parse_date(r.get("lastUpdate"))
        if not date: continue
        program = r.get("program") or ""
        cos_str = r.get("companies") or ""
        cos = [c.strip() for c in cos_str.split(",") if c.strip()] if cos_str else []
        events.append({
            "id": make_id("doe", date, program),
            "date": date,
            "type": "doe",
            "title": f"DOE: {program}"[:120],
            "description": (
                f"{r.get('agency', 'DOE')} · "
                f"Status: {r.get('status', '')} · "
                f"Funding: ${r.get('funding', 'N/A')}B · "
                f"{(r.get('description') or '')[:200]}"
            ),
            "companies": cos,
            "sector": infer_sector(program + " " + (r.get("description") or "")),
            "source": r.get("agency") or "DOE",
            "sourceUrl": "https://www.energy.gov/",
            "raw": r,
        })
    return events


def load_calendar_events(today):
    """Industry events / conferences from FRONTIER_EVENTS in calendar.js."""
    if not (ROOT / "calendar.js").exists(): return []
    events_data = parse_js_array(ROOT / "calendar.js", "FRONTIER_EVENTS")
    if not events_data: return []
    out = []
    for r in events_data:
        date = parse_date(r.get("date") or r.get("startDate"))
        if not date: continue
        out.append({
            "id": make_id("conf", date, r.get("title") or r.get("name", "")),
            "date": date,
            "type": "conf",
            "title": (r.get("title") or r.get("name", ""))[:120],
            "description": f"{r.get('type','event')} · {r.get('location','')} · {r.get('description','')}"[:300],
            "companies": r.get("keyAttendees", []) or r.get("companies", []) or [],
            "sector": infer_sector((r.get("description") or "") + " " + (r.get("title") or "")),
            "source": "Industry calendar",
            "sourceUrl": r.get("url") or "",
            "raw": r,
        })
    return out


# ────────────────────────────────────────────────────────────────────────
# Main


LOADERS = [
    ("fda",      load_fda),
    ("trial",    load_clinical_trials),
    ("faa",      load_faa),
    ("nrc",      load_nrc),
    ("fcc",      load_fcc),
    ("fedreg",   load_federal_register),
    ("doe",      load_doe_programs),
    ("formd",    load_form_d),
    ("sbir",     load_sbir),
    ("earnings", load_earnings),
    ("conf",     load_calendar_events),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--past-days", type=int, default=30,
                    help="Include past events within N days (default 30)")
    ap.add_argument("--future-days", type=int, default=180,
                    help="Cap future events at N days out (default 180)")
    ap.add_argument("--output", default=str(OUT))
    args = ap.parse_args()

    today = datetime.now(timezone.utc).date()
    past_cutoff   = today - timedelta(days=args.past_days)
    future_cutoff = today + timedelta(days=args.future_days)

    print("=" * 64)
    print("Build Unified Catalyst Calendar")
    print("=" * 64)

    all_events = []
    by_source = {}
    for label, loader in LOADERS:
        try:
            events = loader(today)
        except Exception as e:
            print(f"  ⚠ {label}: loader failed — {e}")
            events = []
        # filter by date window
        kept = []
        for e in events:
            d = parse_date(e.get("date"))
            if not d: continue
            try:
                dt = datetime.strptime(d, "%Y-%m-%d").date()
            except ValueError:
                continue
            if dt < past_cutoff or dt > future_cutoff:
                continue
            kept.append(e)
        by_source[label] = len(kept)
        all_events.extend(kept)
        print(f"  {label:<10} {len(events):>4} loaded  →  {len(kept):>4} in window")

    # Add days_out + importance per event
    for e in all_events:
        try:
            dt = datetime.strptime(e["date"], "%Y-%m-%d").date()
            e["daysOut"] = (dt - today).days
        except (ValueError, KeyError):
            e["daysOut"] = None
        e["importance"] = importance_for_days_out(e.get("daysOut"))

    # Dedupe by id
    seen = set()
    deduped = []
    for e in all_events:
        if e["id"] in seen: continue
        seen.add(e["id"])
        deduped.append(e)
    if len(deduped) != len(all_events):
        print(f"  Deduped: {len(all_events)} → {len(deduped)}")

    # Sort: future events first (closest first), then past (most recent first)
    deduped.sort(key=lambda e: (
        0 if (e.get("daysOut") or 0) >= 0 else 1,
        abs(e.get("daysOut") or 0),
    ))

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "windowPastDays": args.past_days,
        "windowFutureDays": args.future_days,
        "todayUTC": today.isoformat(),
        "totalEvents": len(deduped),
        "bySource": by_source,
        "byType": {},
        "byImportance": {},
        "events": deduped,
    }

    # By-type and by-importance summary
    from collections import Counter
    out["byType"]       = dict(Counter(e["type"]       for e in deduped))
    out["byImportance"] = dict(Counter(e["importance"] for e in deduped))

    Path(args.output).write_text(json.dumps(out, indent=2, default=str))
    print()
    print(f"✅ Wrote {Path(args.output).relative_to(ROOT)}")
    print(f"   Total events: {len(deduped)}")
    print(f"   By type: {out['byType']}")
    print(f"   By importance: {out['byImportance']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
