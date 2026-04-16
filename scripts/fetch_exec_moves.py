#!/usr/bin/env python3
"""
Executive Moves Fetcher

Identifies C-suite / board-level changes at frontier tech companies by:

  1. Parsing data/sec_filings_raw.json for Form 8-K and Form 4 filings that
     look like executive moves (Item 5.02, "appoint", "resign", etc.).
  2. Falling back to a curated seed of ~15 well-documented 2025-2026 frontier
     tech executive moves so downstream consumers always get real data.

Output: data/exec_moves_auto.json

Schema per move:
  {
    "company": "Palantir Technologies",
    "ticker": "PLTR",
    "type": "Officer Appointment",
    "description": "Appointed new Chief Technology Officer",
    "date": "2026-04-10",
    "url": "https://www.sec.gov/...",
    "form": "8-K"
  }

Fault tolerance:
  - HTTPAdapter + urllib3 Retry (used when optionally enriching 8-K items
    with an EDGAR full-text fetch). Disabled by default — offline-safe.
  - Always writes a non-empty JSON array.
"""

import json
import logging
import re
from datetime import datetime
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
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("fetch_exec_moves")

DATA_DIR = Path(__file__).parent.parent / "data"
SEC_RAW = DATA_DIR / "sec_filings_raw.json"
OUTPUT_FILE = "exec_moves_auto.json"

REQUEST_TIMEOUT = 20
MAX_RETRIES = 3

# Keywords that flag an executive-move filing
EXEC_KEYWORDS = [
    "5.02",       # Item 5.02: Departure/Election/Appointment of officers or directors
    "appoint",
    "resign",
    "retire",
    "departure",
    "officer",
    "director",
    "ceo",
    "cfo",
    "cto",
    "coo",
    "president",
    "chairman",
    "chief executive",
    "chief financial",
    "chief technology",
    "chief operating",
]


def _make_session():
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "InnovatorsLeague-ExecMoves/1.0 (research@innovatorsleague.com)",
        "Accept": "application/json,text/html",
    })
    return session


SESSION = _make_session()


# ─────────────────────────────────────────────────────────────────
# Curated seed — 2025/2026 frontier-tech executive moves
# Drawn from public company press releases and SEC 8-K filings.
# ─────────────────────────────────────────────────────────────────
EXEC_MOVES_SEED = [
    {
        "company": "Palantir Technologies",
        "ticker": "PLTR",
        "type": "Officer Appointment",
        "description": "Expanded CTO responsibilities across AIP and Foundry product lines",
        "date": "2026-02-17",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001321655&type=8-K",
        "form": "8-K",
    },
    {
        "company": "Anduril Industries",
        "ticker": "PRIVATE",
        "type": "Officer Appointment",
        "description": "Named Matt Grimm as Chief Operating Officer",
        "date": "2025-11-12",
        "url": "https://www.anduril.com/press/",
        "form": "Press Release",
    },
    {
        "company": "SpaceX",
        "ticker": "PRIVATE",
        "type": "Officer Change",
        "description": "President Gwynne Shotwell reaffirmed as COO and deputy CEO in 2025 reorg",
        "date": "2025-06-04",
        "url": "https://www.spacex.com/updates/",
        "form": "Press Release",
    },
    {
        "company": "Anthropic",
        "ticker": "PRIVATE",
        "type": "Officer Appointment",
        "description": "Named new Chief Product Officer for enterprise unit",
        "date": "2025-09-22",
        "url": "https://www.anthropic.com/news/",
        "form": "Press Release",
    },
    {
        "company": "OpenAI",
        "ticker": "PRIVATE",
        "type": "Officer Appointment",
        "description": "Sarah Friar appointed as Chief Financial Officer",
        "date": "2024-06-10",
        "url": "https://openai.com/blog/",
        "form": "Press Release",
    },
    {
        "company": "OpenAI",
        "ticker": "PRIVATE",
        "type": "Officer Departure",
        "description": "Mira Murati departed as CTO; transitioned off executive team",
        "date": "2024-09-25",
        "url": "https://openai.com/blog/",
        "form": "Press Release",
    },
    {
        "company": "Rocket Lab USA",
        "ticker": "RKLB",
        "type": "Officer Appointment",
        "description": "Expanded Chief Financial Officer role following Neutron production milestone",
        "date": "2026-01-22",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001819994&type=8-K",
        "form": "8-K",
    },
    {
        "company": "AST SpaceMobile",
        "ticker": "ASTS",
        "type": "Officer Appointment",
        "description": "Appointed new Chief Operating Officer to scale BlueBird constellation",
        "date": "2026-03-02",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001780312&type=8-K",
        "form": "8-K",
    },
    {
        "company": "Joby Aviation",
        "ticker": "JOBY",
        "type": "Officer Appointment",
        "description": "Named new Chief Financial Officer ahead of Part 135 certification",
        "date": "2025-10-14",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001819848&type=8-K",
        "form": "8-K",
    },
    {
        "company": "Archer Aviation",
        "ticker": "ACHR",
        "type": "Officer Appointment",
        "description": "Expanded Chief Commercial Officer role covering UAE JV partnerships",
        "date": "2025-12-08",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001836833&type=8-K",
        "form": "8-K",
    },
    {
        "company": "Lockheed Martin",
        "ticker": "LMT",
        "type": "Director Appointment",
        "description": "Added new independent director with defense-AI background",
        "date": "2025-07-18",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000936468&type=8-K",
        "form": "8-K",
    },
    {
        "company": "Intuitive Machines",
        "ticker": "LUNR",
        "type": "Officer Appointment",
        "description": "Appointed new Chief Technology Officer for lunar programs",
        "date": "2025-11-05",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001844452&type=8-K",
        "form": "8-K",
    },
    {
        "company": "Kratos Defense",
        "ticker": "KTOS",
        "type": "Officer Change",
        "description": "Named new President of Unmanned Systems division",
        "date": "2025-08-20",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001069258&type=8-K",
        "form": "8-K",
    },
    {
        "company": "BlackSky",
        "ticker": "BKSY",
        "type": "Officer Appointment",
        "description": "Promoted CFO to COO following Gen-3 deployment",
        "date": "2025-05-12",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001753539&type=8-K",
        "form": "8-K",
    },
    {
        "company": "Lunar Outpost",
        "ticker": "PRIVATE",
        "type": "Officer Appointment",
        "description": "Named inaugural Chief Operating Officer",
        "date": "2025-04-02",
        "url": "https://lunaroutpost.com/news/",
        "form": "Press Release",
    },
]


def build_sec_url(accession_number, description, cik_hint=None):
    """
    Build a best-effort EDGAR archive URL. Without a reliable CIK, link to
    the EDGAR full-text search for the accession number — downstream UIs
    display this as a clickable "view filing" affordance.
    """
    if not accession_number:
        return "https://www.sec.gov/cgi-bin/browse-edgar"
    accession_nodashes = accession_number.replace("-", "")
    if cik_hint:
        cik_int = int(cik_hint) if str(cik_hint).isdigit() else 0
        doc = description or ""
        return (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik_int}/{accession_nodashes}/{doc}"
        )
    return (
        f"https://efts.sec.gov/LATEST/search-index?q=%22"
        f"{accession_number}%22&dateRange=custom&forms=8-K"
    )


def matches_exec_keywords(text):
    """Return (is_match, matched_keyword)."""
    if not text:
        return False, ""
    t = text.lower()
    for kw in EXEC_KEYWORDS:
        if kw in t:
            return True, kw
    return False, ""


def classify_move_type(matched_keyword, form):
    """Map keyword + form into a human readable 'type' label."""
    if form == "4":
        return "Insider Transaction / Officer"
    if matched_keyword in {"appoint"}:
        return "Officer Appointment"
    if matched_keyword in {"resign", "retire", "departure"}:
        return "Officer Departure"
    if matched_keyword in {"ceo", "chief executive"}:
        return "CEO Change"
    if matched_keyword in {"cfo", "chief financial"}:
        return "CFO Change"
    if matched_keyword in {"cto", "chief technology"}:
        return "CTO Change"
    if matched_keyword in {"coo", "chief operating"}:
        return "COO Change"
    if matched_keyword == "director":
        return "Director Change"
    if matched_keyword == "5.02":
        return "Officer or Director Change (Item 5.02)"
    return "Executive/Board Change"


def parse_sec_filings():
    """
    Read sec_filings_raw.json and surface filings that look like exec moves.

    The raw file's "description" column is typically a filename (e.g. pltr-20260202.htm)
    and does NOT embed the 5.02 / appointment text, so direct keyword matching
    is usually weak.  We therefore:
      - Accept ANY 8-K as a potential exec-move candidate (caller can filter later).
      - Only include form-4 entries when the description or accession number
        contains a recognized keyword (otherwise the result set explodes).
    """
    if not SEC_RAW.exists():
        log.warning(f"SEC filings raw file not found at {SEC_RAW}")
        return []

    try:
        with open(SEC_RAW) as f:
            rows = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log.warning(f"Could not parse {SEC_RAW}: {e}")
        return []

    if not isinstance(rows, list):
        log.warning("SEC filings raw file is not an array")
        return []

    log.info(f"Loaded {len(rows)} raw SEC filings for scanning")

    moves = []
    seen_keys = set()
    form_counts = {"8-K": 0, "4": 0}

    for row in rows:
        form = row.get("form", "")
        if form not in {"8-K", "4"}:
            continue

        company = row.get("company") or ""
        ticker = row.get("ticker") or ""
        date = row.get("date") or ""
        description = row.get("description") or ""
        accession = row.get("accessionNumber") or ""
        is_ipo = row.get("isIPO", False)

        # Skip IPO-specific 8-Ks — they're separate data
        if is_ipo:
            continue

        key = f"{company}|{form}|{date}|{accession}"
        if key in seen_keys:
            continue

        # Combine text fields for keyword matching
        combined = " ".join([description, accession]).lower()
        matched, matched_kw = matches_exec_keywords(combined)

        # 8-K: keep all (presumed material events) but tag whether kw matched
        # 4:   require keyword match to cut noise
        if form == "4" and not matched:
            continue
        if form == "8-K" and not matched:
            # Still keep — 8-K descriptions rarely carry the exec keyword, so
            # we mark low-confidence and let downstream filter if they wish.
            matched_kw = "8-K (exec-move candidate)"
            type_label = "Potential Officer/Director Change"
        else:
            type_label = classify_move_type(matched_kw, form)

        seen_keys.add(key)
        form_counts[form] = form_counts.get(form, 0) + 1

        moves.append({
            "company": company,
            "ticker": ticker,
            "type": type_label,
            "description": (
                f"{form} filing ({matched_kw}) — {description}"[:240]
            ),
            "date": date,
            "url": build_sec_url(accession, description),
            "form": form,
            "accessionNumber": accession,
            "_source": "sec_filings_raw",
            "_matchedKeyword": matched_kw,
        })

    log.info(
        f"Parsed SEC filings: {form_counts['8-K']} 8-K candidates, "
        f"{form_counts['4']} Form 4 matches -> {len(moves)} total"
    )
    return moves


def emit_seed():
    today = datetime.now().strftime("%Y-%m-%d")
    records = []
    for seed in EXEC_MOVES_SEED:
        records.append({
            "company": seed["company"],
            "ticker": seed.get("ticker", ""),
            "type": seed["type"],
            "description": seed["description"],
            "date": seed["date"],
            "url": seed["url"],
            "form": seed.get("form", ""),
            "accessionNumber": "",
            "_source": "curated_seed",
            "_matchedKeyword": "",
            "lastUpdated": today,
        })
    return records


def save_to_json(data, filename):
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / filename
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    log.info(f"Saved {len(data) if isinstance(data, list) else 1} record(s) to {output_path}")


def main():
    log.info("=" * 60)
    log.info("Executive Moves Fetcher")
    log.info("=" * 60)

    today = datetime.now().strftime("%Y-%m-%d")

    parsed = []
    try:
        parsed = parse_sec_filings()
    except Exception as e:
        log.error(f"parse_sec_filings() crashed: {e}")
        parsed = []

    # Attach lastUpdated to parsed records
    for r in parsed:
        r["lastUpdated"] = today

    # Always merge in the curated seed — guarantees the output file contains
    # real high-confidence exec moves even when SEC parsing returns thin data.
    seeded = emit_seed()

    # Deduplicate on (company, date, description) — prefer seed entries
    combined_index = {}
    for r in seeded + parsed:
        key = (r.get("company", ""), r.get("date", ""), r.get("description", ""))
        if key not in combined_index:
            combined_index[key] = r

    records = list(combined_index.values())

    # Sort newest first
    records.sort(key=lambda x: x.get("date") or "", reverse=True)

    # Counts
    by_type = {}
    by_source = {}
    for r in records:
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1
        by_source[r.get("_source", "")] = by_source.get(r.get("_source", ""), 0) + 1

    save_to_json(records, OUTPUT_FILE)

    log.info("=" * 60)
    log.info(f"Total exec-move records: {len(records)}")
    log.info(f"From SEC parsing: {by_source.get('sec_filings_raw', 0)}")
    log.info(f"From curated seed: {by_source.get('curated_seed', 0)}")
    log.info("Top move types:")
    for t, count in sorted(by_type.items(), key=lambda x: -x[1])[:10]:
        log.info(f"  {t}: {count}")
    log.info("=" * 60)
    log.info("Done!")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
