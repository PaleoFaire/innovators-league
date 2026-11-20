#!/usr/bin/env python3
"""
The Build-Out, Live (working name: Lagebild): one sourced line per public build-out event.
─────────────────────────────────────────────────────────────────────────
Reads only data this repo already collects and turns each public sign that a tracked US
company is building into one plain line with its source.

The method, in the order the code applies it:
  1. Collect   primary sources only: SEC filings, federal award records, company newsrooms,
               public job boards. Second-hand feeds are read so they can be counted and
               rejected, never published.
  2. Drop      forecasts, estimates, schedules and data checks are not events. Roll-ups are
               not read as events; their single rows are.
  3. Fields    company, type, amount (USD or null), place, date, agency or programme, source.
               What the source data does not hold stays empty. Nothing is guessed.
  4. Place     town-level only. Coordinates are rounded to one decimal place (about 11 km).
               When the source names no place the event sits at the company's headquarters
               town and says so.
  5. Line      one sentence per event from a fixed template. Each line is parsed back and
               checked against the fields; a mismatch rejects the event.
  6. Score     type points + dollar points (log scale) + first-of-kind points. Published,
               never tuned per event.
  7. Publish   only with a primary-source link held in repo data. Everything else is counted
               in data/lagebild/rejected.json with the reason. Follow-ups (same company, same
               type, within 30 days) are threaded onto the first event.

Never published: negative or distress signals about a named company, investor names, and
anything from the files this script refuses to open (see FORBIDDEN_INPUT_MARKERS).

Outputs
  data/lagebild/events.json        every published event, full record with provenance
  data/lagebild/rejected.json      counts and reasons by type and by source (no names)
  data/lagebild/README-METHOD.md   the method, written from the constants below
  data/lagebild_auto.js            const LAGEBILD = {...}; the last 90 days, for lagebild.html

Standard library only. No network. Deterministic for a given --today.

Usage
  python3 scripts/build_lagebild.py                          # as of today (UTC)
  python3 scripts/build_lagebild.py --today 2026-11-20       # reproducible build
  python3 scripts/build_lagebild.py --include-job-signals    # publish the job-board signals
  python3 scripts/build_lagebild.py --list-rejects no_source_url   # local debugging only
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, localcontext
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent

# ─── the published constants ─────────────────────────────────────────────
# Changing any of these is a method change: bump METHOD_VERSION.
METHOD_VERSION = "1.0"
WINDOWS = (7, 30, 90)            # the time windows the page offers, in days
PAYLOAD_DAYS = 90                # the page file holds this many days
THREAD_DAYS = 30                 # a follow-up joins the first event within this many days
COORD_DECIMALS = 1               # one decimal place of latitude/longitude is about 11 km
EARLIEST_DAY = date(1990, 1, 1)  # anything dated earlier is treated as a data error
US_COUNTRY_VALUES = frozenset({"United States", "USA", "US", "United States of America"})

DOLLAR_FLOOR_USD = 100_000       # dollar points start above this amount
POINTS_PER_TENFOLD = 10          # points for every tenfold step above the floor
DOLLAR_CAP_POINTS = 50           # reached at $10B
FIRST_POINTS = 10                # first event of its type for the company
FIRST_RECORD_DAYS = 365          # ...only where the record of that type is at least this deep
SURGE_MAX_RATIO = 3              # open roles more than tripling in four weeks = a feed change
TURN_MIN_POINTS = 15             # a production turn is a rise of at least this many points

# Event types, in display order. "points" is the type score. "first" says whether the
# first-of-kind points can apply. "stream" groups types by the kind of source.
TYPES = OrderedDict([
    ("round",           {"label": "Funding round",             "points": 20, "stream": "newsroom", "first": False}),
    ("debt",            {"label": "Debt financing",            "points": 20, "stream": "newsroom", "first": False}),
    ("form_d",          {"label": "SEC Form D",                "points": 10, "stream": "filings",  "first": False}),
    ("ipo_filing",      {"label": "IPO filing",                "points": 35, "stream": "filings",  "first": True}),
    ("contract",        {"label": "Federal contract",          "points": 20, "stream": "awards",   "first": True}),
    ("grant",           {"label": "Federal grant",             "points": 15, "stream": "awards",   "first": True}),
    ("new_location",    {"label": "New location",              "points": 45, "stream": "jobs",     "first": True}),
    ("first_mfg_role",  {"label": "First manufacturing role",  "points": 45, "stream": "jobs",     "first": True}),
    ("senior_mfg_role", {"label": "Senior manufacturing role", "points": 35, "stream": "jobs",     "first": True}),
    ("production_turn", {"label": "Shift to production roles", "points": 35, "stream": "jobs",     "first": True}),
    ("hiring_surge",    {"label": "Rise in open roles",        "points": 25, "stream": "jobs",     "first": True}),
])

# Rows that are read and counted but can never become an event.
OTHER_KINDS = OrderedDict([
    ("ipo_estimate",     "IPO pipeline estimate"),
    ("launch",           "Scheduled launch"),
    ("hiring_pullback",  "Hiring pullback"),
    ("board_check",      "Job-board data check"),
    ("job_signal_other", "Unrecognised job-board signal"),
])

# Rejection reasons, in the order used to pick one primary reason per rejected row.
REASONS = OrderedDict([
    ("negative_signal",         "Negative or distress signal about a named company. Never published."),
    ("not_an_event",            "A forecast, estimate, schedule or data check, not something that happened."),
    ("company_not_in_database", "The company name does not match a record in data.js."),
    ("outside_us",              "The company is not headquartered in the United States."),
    ("no_source_url",           "The repo data holds no link to a primary source for the event."),
    ("source_not_primary",      "The link is not a secure link to a primary source: the company's own site, a filing or an award record."),
    ("date_missing",            "No date in the source data."),
    ("date_not_a_day",          "The date has no day (a month or a year only)."),
    ("date_future",             "The date is after the build date."),
    ("date_implausible",        "The date is not a real date, is before 1990, or is before the company was founded."),
    ("date_unreliable",         "Several different announcements carry one identical timestamp."),
    ("fields_not_confirmed",    "The source does not state a completed event with these fields."),
    ("fields_implausible",      "The numbers look like a change in the data feed, not a real change."),
    ("line_mismatch",           "The written line did not match the fields when checked."),
])
PRECEDENCE = list(REASONS)

# ─── inputs: an allow-list. Nothing else is ever opened. ─────────────────
INPUTS = OrderedDict([
    ("companies",        "data.js"),
    ("announcements",    "data/company_announcements_auto.json"),
    ("deals",            "data/deals_auto.json"),
    ("funding_tracker",  "data/funding_tracker_auto.json"),
    ("form_d",           "data/form_d_filings_auto.json"),
    ("form_d_daily",     "data/form_d_daily_auto.json"),
    ("sec_filings",      "data/sec_filings_raw.json"),
    ("ipo_pipeline",     "data/ipo_pipeline_auto.json"),
    ("contracts",        "data/gov_contracts_raw.json"),
    ("contracts_rollup", "data/gov_contracts_aggregated.json"),
    ("award_links",      "data/sbir_awards_auto.json"),
    ("nsf",              "data/nsf_awards_raw.json"),
    ("launches",         "data/launch_manifest_auto.json"),
    ("job_signals",      "data/pulse/signals"),
    ("jobs",             "data/jobs_raw.json"),
    ("job_boards",       "data/pulse/job_boards.json"),
    ("geocode",          "data/geocode_cache.json"),
])
# Fund, brief and private files are never inputs. The guard below refuses them even if a
# later edit adds one to INPUTS by mistake.
FORBIDDEN_INPUT_MARKERS = ("ros_fund", "action_brief", "data/private", "/private/")

OUT_DIR = "data/lagebild"
OUT_EVENTS = OUT_DIR + "/events.json"
OUT_REJECTED = OUT_DIR + "/rejected.json"
OUT_METHOD = OUT_DIR + "/README-METHOD.md"
OUT_PAGE = "data/lagebild_auto.js"

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

PRESS_WIRES = ("businesswire.com", "prnewswire.com", "globenewswire.com")
# Hosts many unrelated sites share. A link there is never "the company's own site" just
# because the company's site lives under the same parent.
SHARED_HOSTS = frozenset({
    "github.io", "substack.com", "medium.com", "notion.site", "wordpress.com", "webflow.io",
    "wixsite.com", "squarespace.com", "framer.website", "framer.app", "carrd.co", "linkedin.com",
    "x.com", "twitter.com", "youtube.com",
})
SOURCE_NAMES = {
    "newsroom": "Company newsroom",
    "wire": "Company press release",
    "sec": "SEC EDGAR",
    "usaspending": "USAspending.gov",
    "award": "Federal award record",
    "job_board": "Company job board",
    "careers": "Company careers page",
}
# Words that praise. Lines are built from fixed templates, so this is a tripwire for a
# future template edit, not a filter on source text.
PRAISE_WORDS = frozenset({
    "leading", "innovative", "revolutionary", "breakthrough", "game-changing", "cutting-edge",
    "massive", "huge", "impressive", "exciting", "world-class", "best", "premier", "landmark",
    "historic", "record", "stunning", "remarkable", "pioneering", "disruptive", "unicorn",
    "major", "significant", "strong", "robust", "transformative",
})


# ═══ small helpers ═══════════════════════════════════════════════════════

def read_input(root: Path, rel: str):
    """Open one allow-listed input. Returns the parsed JSON, or None if the file is absent."""
    low = rel.lower()
    if any(marker in low for marker in FORBIDDEN_INPUT_MARKERS):
        raise PermissionError(f"refusing to read {rel}: fund, brief and private files are never inputs")
    if rel not in INPUTS.values() and not any(rel.startswith(v + "/") for v in INPUTS.values()):
        raise PermissionError(f"refusing to read {rel}: not on the input allow-list")
    path = root / rel
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clean_text(value) -> str:
    """Decode HTML entities and collapse whitespace."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", html.unescape(html.unescape(str(value)))).strip()


def stable_id(prefix: str, key: str) -> str:
    return prefix + "-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]


def to_whole_dollars(value):
    """A number of US dollars as an int, or None. Accepts ints, floats and digit strings."""
    if value is None or isinstance(value, bool):
        return None
    try:
        d = Decimal(str(value).replace(",", "").strip())
    except Exception:  # noqa: BLE001 - any unparseable value simply is not a number
        return None
    if not d.is_finite():
        return None
    return int(d.quantize(Decimal(1), rounding=ROUND_HALF_UP))


# ─── dates ───────────────────────────────────────────────────────────────
_ISO_DAY = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:$|[T ])")
_US_DAY = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
_COARSE = re.compile(r"^(?:\d{4}|\d{4}-\d{2}|Q[1-4] \d{4}|\d{4}-Q[1-4])$")


def parse_day(raw):
    """(date, None) for a real calendar day, else (None, reason code)."""
    if raw is None:
        return None, "date_missing"
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return None, "date_not_a_day"
    s = str(raw).strip()
    if not s:
        return None, "date_missing"
    m = _ISO_DAY.match(s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))), None
        except ValueError:
            return None, "date_implausible"
    if _COARSE.match(s):
        return None, "date_not_a_day"
    m = _US_DAY.match(s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(1)), int(m.group(2))), None
        except ValueError:
            return None, "date_implausible"
    if re.search(r"[A-Za-z]{3}", s) and re.search(r"\d{4}", s):
        try:
            return parsedate_to_datetime(s).date(), None
        except (TypeError, ValueError, IndexError):
            return None, "date_implausible"
    return None, "date_implausible"


def check_day(day: date, today: date, founded=None):
    """None if the day is usable, else a reason code."""
    if day > today:
        return "date_future"
    if day < EARLIEST_DAY:
        return "date_implausible"
    try:
        if founded and day.year < int(founded) - 1:
            return "date_implausible"
    except (TypeError, ValueError):
        pass
    return None


# ─── money ───────────────────────────────────────────────────────────────
_UNITS = {
    "": 1, "k": 10 ** 3, "thousand": 10 ** 3, "m": 10 ** 6, "mn": 10 ** 6, "mm": 10 ** 6,
    "million": 10 ** 6, "b": 10 ** 9, "bn": 10 ** 9, "billion": 10 ** 9, "t": 10 ** 12,
    "tn": 10 ** 12, "trillion": 10 ** 12,
}
_AMOUNT = re.compile(
    r"(?P<pre>US\$|USD\s?\$?|CAD\s?\$?|CA\$|C\$|AUD\s?\$?|AU\$|A\$|NZ\$|S\$|HK\$|\$|€|£|¥|₹|₩)\s?"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?:\s?(?P<unit>trillion|billion|million|thousand|bn|mn|tn|mm|[bmkt])(?![a-z]))?"
    r"(?P<plus>\+)?"
    r"(?:\s(?P<post>USD|CAD|AUD|EUR|GBP|NZD|SGD|HKD|CHF|SEK|NOK|DKK|JPY|INR|KRW)\b)?",
    re.I,
)
_QUALIFIER = re.compile(r"(?:more than|over|up to|nearly|almost|approximately|approx\.?|about|around|at least|~)\s*$", re.I)
_VALUATION_AFTER = re.compile(r"^\s*(?:(?:post|pre)-money\s+)?valuation\b", re.I)
_VALUATION_BEFORE = re.compile(r"(?:valuation of|valuation above|valuation over|valued at|valuing (?:it|the company) at)\s*$", re.I)


def find_amounts(text: str):
    """Every money figure in a headline: value, whether it is USD, exact, and a valuation."""
    out = []
    for m in _AMOUNT.finditer(text):
        number = Decimal(m.group("num").replace(",", ""))
        value = int((number * _UNITS[(m.group("unit") or "").lower()]).quantize(Decimal(1), rounding=ROUND_HALF_UP))
        pre = re.sub(r"\s", "", m.group("pre").upper())
        post = (m.group("post") or "").upper()
        before = text[max(0, m.start() - 28):m.start()]
        after = text[m.end():m.end() + 28]
        out.append({
            "value": value,
            "usd": pre in ("$", "US$", "USD", "USD$") and post in ("", "USD"),
            "exact": not m.group("plus") and not _QUALIFIER.search(before),
            "valuation": bool(_VALUATION_AFTER.match(after) or _VALUATION_BEFORE.search(before)),
            "start": m.start(),
            "end": m.end(),
        })
    return out


def parse_money_field(value):
    """A collector's money string such as "$240M" as whole US dollars, or None."""
    found = find_amounts(clean_text(value))
    if len(found) == 1 and found[0]["usd"] and found[0]["exact"]:
        return found[0]["value"]
    return None


def fmt_usd(amount) -> str:
    """Dollars to three significant figures: $640, $45.2K, $14.9M, $1B, $3.55B."""
    d = Decimal(int(amount))
    for power, suffix in ((12, "T"), (9, "B"), (6, "M"), (3, "K")):
        size = Decimal(10) ** power
        if d >= size:
            q = d / size
            step = Decimal("1") if q >= 100 else Decimal("0.1") if q >= 10 else Decimal("0.01")
            q = q.quantize(step, rounding=ROUND_HALF_UP)
            if q >= 1000 and suffix != "T":      # 999.6K rounds up into the next unit
                return fmt_usd(int(q * size))
            text = format(q, "f")
            if "." in text:
                text = text.rstrip("0").rstrip(".")
            return "$" + text + suffix
    return "$" + str(int(d))


def article_for(phrase: str) -> str:
    """"a" or "an" for a phrase that starts with a money figure or a word."""
    m = re.match(r"\$(\d+)", phrase)
    if m:
        whole = m.group(1)
        return "an" if whole[0] == "8" or whole in ("11", "18") else "a"
    return "an" if phrase[:1].lower() in "aeiou" else "a"


def fmt_number(value) -> str:
    """A count or percentage as written in a line: 33, 100, 46.2."""
    d = Decimal(str(value))
    if d == d.to_integral_value():
        return str(int(d))
    return format(d.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP), "f")


# ─── hosts ───────────────────────────────────────────────────────────────
def host_of(url) -> str:
    if not url:
        return ""
    text = str(url).strip()
    host = (urlsplit(text if "://" in text else "https://" + text).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def same_site(link_host: str, site_host: str) -> bool:
    if not link_host or not site_host or "." not in link_host or "." not in site_host:
        return False
    if link_host in SHARED_HOSTS or site_host in SHARED_HOSTS:
        return False
    return link_host == site_host or link_host.endswith("." + site_host) or site_host.endswith("." + link_host)


def is_wire(host: str) -> bool:
    return any(host == w or host.endswith("." + w) for w in PRESS_WIRES)


# ═══ data.js: a reader for the COMPANIES literal ═════════════════════════

class JSLiteralError(ValueError):
    pass


_JS_TOKEN = re.compile(
    r"""(?P<ws>\s+)
      | (?P<lc>//[^\n]*)
      | (?P<bc>/\*.*?\*/)
      | (?P<str>"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')
      | (?P<num>[-+]?(?:0[xX][0-9a-fA-F]+|(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?))
      | (?P<id>[A-Za-z_$][A-Za-z0-9_$]*)
      | (?P<punc>[{}\[\],:])
    """,
    re.X | re.S,
)
_JS_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "0": "\0", "\n": ""}
_JS_WORDS = {"true": True, "false": False, "null": None, "undefined": None}


def _js_string(token: str) -> str:
    body = token[1:-1]
    if "\\" not in body:
        return body
    out, i, n = [], 0, len(body)
    while i < n:
        ch = body[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        esc = body[i + 1]
        if esc == "u":
            if body[i + 2] == "{":
                end = body.index("}", i)
                out.append(chr(int(body[i + 3:end], 16)))
                i = end + 1
            else:
                out.append(chr(int(body[i + 2:i + 6], 16)))
                i += 6
        elif esc == "x":
            out.append(chr(int(body[i + 2:i + 4], 16)))
            i += 4
        else:
            out.append(_JS_ESCAPES.get(esc, esc))
            i += 2
    text = "".join(out)
    if any(0xD800 <= ord(c) <= 0xDFFF for c in text):      # join surrogate pairs
        text = text.encode("utf-16", "surrogatepass").decode("utf-16", "replace")
    return text


def parse_js_literal(text: str, pos: int = 0):
    """Parse one JS array or object literal (data only) starting at text[pos].

    Handles unquoted keys, single and double quotes, comments and trailing commas. Anything
    that is not plain data (an identifier used as a value, a call, a template string) raises
    JSLiteralError: the build stops rather than guess.
    """
    n = len(text)

    def next_token(p):
        while p < n:
            m = _JS_TOKEN.match(text, p)
            if not m:
                raise JSLiteralError(f"unexpected character {text[p]!r} at offset {p}")
            p = m.end()
            if m.lastgroup not in ("ws", "lc", "bc"):
                return m.lastgroup, m.group(m.lastgroup), p
        raise JSLiteralError("unexpected end of input")

    def value(p):
        kind, tok, p = next_token(p)
        if kind == "str":
            return _js_string(tok), p
        if kind == "num":
            if tok.lower().startswith(("0x", "+0x", "-0x")):
                return int(tok, 16), p
            return (float(tok) if re.search(r"[.eE]", tok) else int(tok)), p
        if kind == "id":
            if tok in _JS_WORDS:
                return _JS_WORDS[tok], p
            raise JSLiteralError(f"identifier {tok!r} used as a value at offset {p}")
        if tok == "[":
            items = []
            while True:
                kind2, tok2, p2 = next_token(p)
                if tok2 == "]" and kind2 == "punc":
                    return items, p2
                item, p = value(p)
                items.append(item)
                kind2, tok2, p2 = next_token(p)
                if kind2 == "punc" and tok2 == ",":
                    p = p2
                elif kind2 == "punc" and tok2 == "]":
                    return items, p2
                else:
                    raise JSLiteralError(f"expected , or ] at offset {p}")
        if tok == "{":
            obj = {}
            while True:
                kind2, tok2, p2 = next_token(p)
                if kind2 == "punc" and tok2 == "}":
                    return obj, p2
                if kind2 == "str":
                    key = _js_string(tok2)
                elif kind2 in ("id", "num"):
                    key = tok2
                else:
                    raise JSLiteralError(f"expected a key at offset {p}")
                kind3, tok3, p3 = next_token(p2)
                if not (kind3 == "punc" and tok3 == ":"):
                    raise JSLiteralError(f"expected : after key {key!r} at offset {p2}")
                obj[key], p = value(p3)
                kind2, tok2, p2 = next_token(p)
                if kind2 == "punc" and tok2 == ",":
                    p = p2
                elif kind2 == "punc" and tok2 == "}":
                    return obj, p2
                else:
                    raise JSLiteralError(f"expected , or }} at offset {p}")
        raise JSLiteralError(f"unexpected token {tok!r} at offset {p}")

    return value(pos)


def load_companies(root: Path):
    """The COMPANIES array from data.js, as a list of dicts with only the fields used here."""
    rel = INPUTS["companies"]
    path = root / rel
    if not path.is_file():
        raise FileNotFoundError(f"{rel} not found under {root}")
    text = path.read_text(encoding="utf-8")
    m = re.search(r"\bconst\s+COMPANIES\s*=\s*\[", text)
    if not m:
        raise JSLiteralError("const COMPANIES = [ not found in data.js")
    records, _ = parse_js_literal(text, m.end() - 1)
    out = []
    for r in records:
        if not isinstance(r, dict) or not isinstance(r.get("name"), str) or not r["name"].strip():
            continue
        former = r.get("formerNames")
        out.append({
            "name": r["name"].strip(),
            "status": r.get("status") or "",
            "sector": r.get("sector") or "",
            "location": clean_text(r.get("location")),
            "country": clean_text(r.get("country")),
            "state": r.get("state") if isinstance(r.get("state"), str) else "",
            "lat": r.get("lat") if isinstance(r.get("lat"), (int, float)) and not isinstance(r.get("lat"), bool) else None,
            "lng": r.get("lng") if isinstance(r.get("lng"), (int, float)) and not isinstance(r.get("lng"), bool) else None,
            "founded": r.get("founded") if isinstance(r.get("founded"), int) and not isinstance(r.get("founded"), bool) else None,
            "website": r.get("website") if isinstance(r.get("website"), str) else "",
            "former": [f.strip() for f in former if isinstance(f, str) and f.strip()] if isinstance(former, list) else [],
        })
    return out


class CompanyIndex:
    """Exact matching only: the name, the name ignoring case, or a recorded former name."""

    def __init__(self, records):
        self.records = {}
        for r in records:
            self.records.setdefault(r["name"], r)
        lower = defaultdict(set)
        for name in self.records:
            lower[name.lower()].add(name)
        self._lower = {k: next(iter(v)) for k, v in lower.items() if len(v) == 1}
        former = defaultdict(set)
        for name, r in self.records.items():
            for f in r["former"]:
                former[f.lower()].add(name)
        self._former = {k: next(iter(v)) for k, v in former.items() if len(v) == 1 and k not in lower}

    def match(self, raw):
        if not isinstance(raw, str):
            return None
        name = raw.strip()
        if name in self.records:
            return self.records[name]
        key = name.lower()
        hit = self._lower.get(key) or self._former.get(key)
        return self.records[hit] if hit else None


def is_us(company) -> bool:
    return company["country"] in US_COUNTRY_VALUES


def company_state(company):
    st = (company.get("state") or "").strip().upper()
    if st in US_STATES:
        return st
    m = re.search(r",\s*([A-Z]{2})\s*$", company.get("location") or "")
    return m.group(1) if m and m.group(1) in US_STATES else None


# ─── places ──────────────────────────────────────────────────────────────
def town_key(name) -> str:
    return re.sub(r"\s+", " ", str(name or "")).strip().lower()


def round_coord(x):
    quantum = Decimal(1).scaleb(-COORD_DECIMALS)
    return float(Decimal(str(x)).quantize(quantum, rounding=ROUND_HALF_UP))


def _lower_median(values):
    values = sorted(values)
    return values[(len(values) - 1) // 2]


def build_towns(companies, geocode):
    """town name -> one rounded point. A town is never mapped more finely than COORD_DECIMALS."""
    points, labels = defaultdict(list), {}
    for c in companies:
        if c["location"] and c["lat"] is not None and c["lng"] is not None:
            key = town_key(c["location"])
            points[key].append((c["lat"], c["lng"]))
            labels.setdefault(key, c["location"])
    extra = defaultdict(list)
    if isinstance(geocode, dict):
        for k in sorted(geocode):
            v = geocode[k]
            parts = k.split("|")
            if len(parts) >= 2 and isinstance(v, dict):
                lat, lng = v.get("lat"), v.get("lng")
                if isinstance(lat, (int, float)) and isinstance(lng, (int, float)) and not isinstance(lat, bool) and not isinstance(lng, bool):
                    key = town_key(parts[1])
                    if key and key not in points:
                        extra[key].append((lat, lng))
                        labels.setdefault(key, clean_text(parts[1]))
    towns = {}
    for source in (points, extra):
        for key in sorted(source):
            pts = source[key]
            towns[key] = {
                "name": labels[key],
                "lat": round_coord(_lower_median(p[0] for p in pts)),
                "lng": round_coord(_lower_median(p[1] for p in pts)),
            }
    return towns


# ═══ reading a funding headline ══════════════════════════════════════════
# A round is only taken from a headline that itself states a completed raise by the company.
_RAISED = re.compile(r"\b(?:raises|raised)\b", re.I)
_CLOSED = re.compile(r"\b(?:closes|closed|secures|secured|completes|completed|lands|landed|announces|announced|announcing)\b", re.I)
_NOUN_AFTER = re.compile(
    r"^\s*(?:(?:in|of|a|an|new|oversubscribed|growth|equity|debt|venture|strategic|additional)\s+){0,3}"
    r"(?:series\s+[a-k]\b|pre-?seed\b|seed\b|funding\b|financing\b|round\b)", re.I)
_LABEL_AFTER = re.compile(r"^\s*(?:series\s+[a-k]\b|pre-?seed\b|seed\b)", re.I)
_NOT_A_ROUND = re.compile(
    r"\b(?:grants?|awards?|awarded|contracts?|non-dilutive|acquires?|acquired|acquiring|acquisition|"
    r"merger|merges?|spac|ipo|tender offer|prize|"
    r"invests?|invested|investing|investment in|backs|leads|co-leads)\b", re.I)
_SEED_AFTER = re.compile(r"\b(?:pre-?seed|seed)\s+(?:round|funding|financing)\b", re.I)
_NOT_YET = re.compile(
    r"\b(?:to raise|will raise|plans? to|planning to|aims? to|seeks?|seeking|in talks|reportedly|rumou?red|"
    r"expects? to|expected to|could|may raise|looking to|targets?|targeting|eyes|eyeing|considering|weighs|weighing)\b", re.I)
_DEBT = re.compile(r"\b(?:debt|credit facility|term loan|loan|convertible notes?)\b", re.I)
_SERIES = re.compile(r"\bSeries\s+([A-K])(?:[\s-]?([1-9]))?(?![A-Za-z0-9])", re.I)
# The company must be the grammatical subject: its name, then at most two corporate
# words ("Energy", "Labs"), then the verb. "Helsing backer Plural raises" is not Helsing.
_VERB_NEXT = r"(?:raises|raised|closes|closed|secures|secured|completes|completed|lands|landed|announces|announced|achieves|reaches)"
_CORPORATE_WORD = (
    r"(?:inc|corp|corporation|co|company|llc|ltd|labs?|technologies|technology|tech|systems|industries|energy|"
    r"space|aerospace|robotics|ai|bio|sciences|computing|power|defense|defence|dynamics|motors|metals|materials|"
    r"semiconductors?|quantum|nuclear|fusion)")


def _words(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def round_label(title: str):
    labels = set()
    for m in _SERIES.finditer(title):
        labels.add("Series " + m.group(1).upper() + ("-" + m.group(2) if m.group(2) else ""))
    low = title.lower()
    if re.search(r"\bpre-?seed\b", low):
        labels.add("pre-seed round")
    elif re.search(r"\bseed\b", low):
        labels.add("seed round")
    if re.search(r"\bgrowth (?:financing|round|equity)\b", low):
        labels.add("growth round")
    return labels.pop() if len(labels) == 1 else None


def subject_is_company(title: str, company: str) -> bool:
    """True when the headline is in the first person, or names the company right before the verb."""
    words = _words(title)
    if re.match(r"^(?:we|we ve|we have|our|announcing our)\b", words):
        return True
    name = _words(company)
    names = [name] if name else []
    first = name.split(" ")[0] if name else ""
    if len(first) >= 4 and first != name:
        names.append(first)
    for cand in names:
        if words.startswith("announcing " + cand + " "):
            return True
        pattern = r"(?:^| )" + re.escape(cand) + r"(?: " + _CORPORATE_WORD + r"){0,2} " + _VERB_NEXT + r"(?: |$)"
        if re.search(pattern, words):
            return True
    return False


def read_headline(title: str, company: str):
    """(fields, None) when the headline states a completed raise by the company, else (None, why)."""
    title = clean_text(title)
    if not title:
        return None, "no headline in the source data"
    if _NOT_A_ROUND.search(title):
        return None, "headline is about an award, a deal, a listing or an investment made, not a round raised"
    if _NOT_YET.search(title):
        return None, "headline describes a plan or a report, not a completed round"
    amounts = find_amounts(title)
    raised = [a for a in amounts if not a["valuation"]]
    valued = [a for a in amounts if a["valuation"]]
    label = round_label(title)
    stated = False
    if _RAISED.search(title) and (raised or label):
        stated = True
    elif raised and _CLOSED.search(title) and any(
            _NOUN_AFTER.match(title[a["end"]:]) or _SERIES.search(title[a["end"]:]) or _SEED_AFTER.search(title[a["end"]:])
            for a in raised):
        stated = True
    elif raised and any(_LABEL_AFTER.match(title[a["end"]:]) for a in raised):
        stated = True
    if not stated:
        return None, "headline does not state a completed funding round"
    if not subject_is_company(title, company):
        return None, "headline does not name the company as the one raising"
    if len({(a["value"], a["usd"]) for a in raised}) > 1:
        return None, "headline carries more than one amount"
    amount = None
    if raised and raised[0]["usd"] and all(a["exact"] for a in raised):
        amount = raised[0]["value"]
    valuation = None
    if len({a["value"] for a in valued}) == 1 and valued[0]["usd"] and valued[0]["exact"]:
        valuation = valued[0]["value"]
    kind = "debt" if _DEBT.search(title) else "round"
    return {
        "kind": kind,
        "amount_usd": amount,
        "round_label": None if kind == "debt" else label,
        "valuation_usd": None if kind == "debt" else valuation,
        "amount_in_headline": bool(raised),
    }, None


# ═══ candidates ══════════════════════════════════════════════════════════

def new_candidate(kind, file, ref, company_raw, date_raw):
    return {
        "type": kind, "file": file, "ref": ref, "company_raw": company_raw, "date_raw": date_raw,
        "amount_usd": None, "agency": None, "program": None,
        "url": None, "url_rule": None, "also": [], "source_name": None,
        "detail": {}, "place_hint": None, "raw": {}, "key": None, "rank": (0,),
        "reasons": [], "note": None, "status": None,
        "company": None, "day": None, "place": None, "line": None,
    }


def add_reason(cand, code, note=None):
    if code not in cand["reasons"]:
        cand["reasons"].append(code)
    if note and not cand["note"]:
        cand["note"] = note


def collect_newsroom(doc, file):
    out = []
    results = doc.get("results") if isinstance(doc, dict) else None
    for ri, r in enumerate(results or []):
        if not isinstance(r, dict):
            continue
        company = r.get("company")
        hits = [(hi, h) for hi, h in enumerate(r.get("hits") or []) if isinstance(h, dict)]
        # One identical timestamp, with a time of day, on different announcements is the
        # feed's build time, not the day the news was published.
        titles_by_stamp = defaultdict(set)
        for _, h in hits:
            stamp = clean_text(h.get("date"))
            clock = re.search(r"\b(\d{2}):(\d{2}):(\d{2})\b", stamp)
            if stamp and clock and clock.group(0) != "00:00:00":
                titles_by_stamp[stamp].add(clean_text(h.get("title")))
        for hi, h in hits:
            title = clean_text(h.get("title"))
            stamp = clean_text(h.get("date"))
            link = clean_text(h.get("link"))
            c = new_candidate("round", file, f"results[{ri}].hits[{hi}]", company, stamp)
            c["raw"] = {"title": title, "date": stamp, "link": link,
                        "amount": clean_text(h.get("amount")), "round": clean_text(h.get("round")),
                        "valuation": clean_text(h.get("valuation"))}
            c["url"], c["url_rule"], c["site"] = (link or None), "newsroom", r.get("website") or ""
            c["key"] = f"newsroom|{company}|{link}|{title}"
            fields, why = read_headline(title, company if isinstance(company, str) else "")
            if fields is None:
                add_reason(c, "fields_not_confirmed", why)
            else:
                collector = parse_money_field(h.get("amount"))
                if fields["amount_usd"] is not None and collector is not None and collector != fields["amount_usd"]:
                    add_reason(c, "fields_not_confirmed", "the collector and the headline disagree on the amount")
                c["type"] = fields["kind"]
                c["amount_usd"] = fields["amount_usd"]
                c["detail"] = {"round_label": fields["round_label"], "valuation_usd": fields["valuation_usd"]}
                c["dedupe"] = (fields["kind"], fields["amount_usd"], fields["amount_in_headline"])
                c["rank"] = (-sum(v is not None for v in c["detail"].values()),)
            if len(titles_by_stamp.get(stamp, ())) > 1:
                add_reason(c, "date_unreliable")
            out.append(c)
    return out


def collect_deals(doc, file):
    """The deals feed is built from trade press. It is read so its rows can be counted."""
    out = []
    for i, r in enumerate(doc if isinstance(doc, list) else []):
        if not isinstance(r, dict):
            continue
        c = new_candidate("round", file, f"[{i}]", r.get("company"), r.get("date"))
        c["url"] = clean_text(r.get("source_url") or r.get("url")) or None
        c["url_rule"], c["site"] = "newsroom", ""
        c["key"] = f"deal|{i}"
        fields, why = read_headline(clean_text(r.get("headline")), r.get("company") if isinstance(r.get("company"), str) else "")
        if fields is None:
            add_reason(c, "fields_not_confirmed", why)
        else:
            c["type"] = fields["kind"]
            c["amount_usd"] = fields["amount_usd"]
            c["detail"] = {"round_label": fields["round_label"], "valuation_usd": fields["valuation_usd"]}
            c["dedupe"] = (fields["kind"], fields["amount_usd"], fields["amount_in_headline"])
        out.append(c)
    return out


def collect_form_d(docs):
    """SEC Form D filings matched to a company by CIK. The same filing in two files is one event."""
    rows = []
    for file, doc in docs:
        for i, r in enumerate((doc.get("filings") if isinstance(doc, dict) else None) or []):
            if isinstance(r, dict):
                rows.append((file, i, r))
    groups = OrderedDict()
    for file, i, r in rows:
        accession = clean_text(r.get("accession"))
        key = accession or f"{r.get('company')}|{r.get('filed_date')}|{r.get('form')}|{file}|{i}"
        groups.setdefault(key, []).append((file, i, r))
    out = []
    for key, members in groups.items():
        # Prefer the link to the filing document over a link to the filer's list of filings.
        members = sorted(members, key=lambda m: (0 if "/Archives/edgar/data/" in str(m[2].get("filing_url")) else 1, m[0], m[1]))
        for n, (file, i, r) in enumerate(members):
            form = clean_text(r.get("form")).upper()
            c = new_candidate("form_d", file, f"filings[{i}]", r.get("company"), r.get("filed_date"))
            c["key"] = "formd|" + key
            c["url"], c["url_rule"], c["source_name"] = clean_text(r.get("filing_url")) or None, "sec", SOURCE_NAMES["sec"]
            sold = to_whole_dollars(r.get("amount_sold"))
            offering = to_whole_dollars(r.get("offering_amount"))
            c["amount_usd"] = sold if sold and sold > 0 else None
            c["detail"] = {
                "form": form,
                "offering_usd": offering if offering and offering > 0 else None,
                "securities": clean_text(r.get("securities_type")) or None,
            }
            c["raw"] = {k: r.get(k) for k in ("issuer_name", "form", "filed_date", "accession", "offering_amount",
                                              "amount_sold", "securities_type", "match_method")}
            if form not in ("D", "D/A"):
                add_reason(c, "not_an_event", "not a Form D")
            if clean_text(r.get("match_method")) != "cik":
                add_reason(c, "fields_not_confirmed", "the issuer was matched by name, not by its SEC number")
            if n > 0:
                c["status"] = "merged"
            out.append(c)
    return out


IPO_FORMS = ("S-1", "S-1/A", "F-1", "F-1/A")


def collect_ipo_filings(doc, file):
    """Only registration statements count. Returns (candidates, rows skipped)."""
    out, skipped = [], 0
    for i, r in enumerate(doc if isinstance(doc, list) else []):
        if not isinstance(r, dict):
            continue
        form = clean_text(r.get("form")).upper()
        if form not in IPO_FORMS:
            skipped += 1
            continue
        c = new_candidate("ipo_filing", file, f"[{i}]", r.get("company"), r.get("date"))
        c["key"] = "ipo|" + (clean_text(r.get("accessionNumber")) or f"{r.get('company')}|{r.get('date')}|{form}")
        c["url"] = clean_text(r.get("filing_url") or r.get("url")) or None
        c["url_rule"], c["source_name"] = "sec", SOURCE_NAMES["sec"]
        c["detail"] = {"form": form}
        c["raw"] = {k: r.get(k) for k in ("form", "date", "accessionNumber")}
        out.append(c)
    return out, skipped


def collect_ipo_pipeline(doc, file):
    out = []
    for i, r in enumerate(doc if isinstance(doc, list) else []):
        if isinstance(r, dict):
            c = new_candidate("ipo_estimate", file, f"[{i}]", r.get("company"), r.get("estimatedDate"))
            c["key"] = f"ipo-estimate|{i}"
            add_reason(c, "not_an_event", "a likelihood, an estimated date and an estimated valuation")
            out.append(c)
    return out


def collect_launches(doc, file):
    out = []
    for i, r in enumerate(doc if isinstance(doc, list) else []):
        if isinstance(r, dict):
            c = new_candidate("launch", file, f"[{i}]", r.get("trackedCompany"), r.get("date"))
            c["key"] = f"launch|{i}"
            add_reason(c, "not_an_event", "a launch that was scheduled when the list was fetched; the data does not say it flew")
            out.append(c)
    return out


def award_link_index(doc):
    """USAspending award id -> permalink, from the one repo file that stores permalinks."""
    links = defaultdict(set)
    for r in doc if isinstance(doc, list) else []:
        if not isinstance(r, dict):
            continue
        url = clean_text(r.get("url"))
        m = re.match(r"^https://www\.usaspending\.gov/award/CONT_AWD_([A-Za-z0-9]+)_", url)
        if m:
            links[m.group(1).upper()].add(url)
    return {k: next(iter(v)) for k, v in links.items() if len(v) == 1}


def collect_contracts(doc, file, index: CompanyIndex, links):
    rows = [(i, r) for i, r in enumerate(doc if isinstance(doc, list) else []) if isinstance(r, dict)]
    groups = OrderedDict()
    for i, r in rows:
        award = clean_text(r.get("awardId"))
        groups.setdefault(award or f"row-{i}", []).append((i, r))
    out = []
    for award, members in groups.items():
        # One award fetched under two spellings of the vendor is one event. Keep the row
        # whose spelling is a record in data.js.
        members = sorted(members, key=lambda m: (0 if index.match(m[1].get("company")) else 1, m[0]))
        for n, (i, r) in enumerate(members):
            c = new_candidate("contract", file, f"[{i}]", r.get("company"), r.get("startDate"))
            c["key"] = "contract|" + award
            url = clean_text(r.get("url") or r.get("award_url")) or links.get(award.upper())
            c["url"], c["url_rule"], c["source_name"] = url or None, "gov", SOURCE_NAMES["usaspending"]
            amount = to_whole_dollars(r.get("amount"))
            if amount is not None and amount < 0:
                add_reason(c, "negative_signal", "money taken back from an award")
            c["amount_usd"] = amount if amount and amount > 0 else None
            agency = clean_text(r.get("agency")) or None
            sub = clean_text(r.get("subAgency")) or None
            c["agency"] = agency
            c["detail"] = {"sub_agency": sub if sub and sub != agency else None}
            c["raw"] = {k: r.get(k) for k in ("awardId", "recipientName", "amount", "agency", "subAgency", "startDate")}
            if n > 0:
                c["status"] = "merged"
            out.append(c)
    return out


def collect_grants(doc, file):
    out = []
    for i, r in enumerate(doc if isinstance(doc, list) else []):
        if not isinstance(r, dict):
            continue
        c = new_candidate("grant", file, f"[{i}]", r.get("awardee"), r.get("date"))
        c["key"] = "nsf|" + (clean_text(r.get("id")) or str(i))
        c["url"], c["url_rule"], c["source_name"] = clean_text(r.get("url")) or None, "gov", SOURCE_NAMES["award"]
        amount = to_whole_dollars(r.get("amount"))
        c["amount_usd"] = amount if amount and amount > 0 else None
        c["agency"] = "National Science Foundation"
        city, state = clean_text(r.get("city")), clean_text(r.get("state")).upper()
        if city and state in US_STATES:
            c["place_hint"] = {"town": f"{city.title()}, {state}", "state": state}
        c["raw"] = {k: r.get(k) for k in ("id", "awardee", "amount", "date", "city", "state")}
        out.append(c)
    return out


# ─── job-board signals ───────────────────────────────────────────────────
JOB_SIGNAL_TYPES = {
    "new_location": "new_location",
    "first_manufacturing_hire": "first_mfg_role",
    "senior_manufacturing_hire": "senior_mfg_role",
    "production_turn": "production_turn",
    "hiring_surge": "hiring_surge",
}
BOARD_RULES = (
    (re.compile(r"^(?:job-boards|boards)(?:\.eu)?\.greenhouse\.io$"), re.compile(r"^/([^/]+)/jobs/[^/]+/?$"), "https://{host}/{slug}"),
    (re.compile(r"^jobs\.ashbyhq\.com$"), re.compile(r"^/([^/]+)/[^/]+/?$"), "https://{host}/{slug}"),
    (re.compile(r"^jobs(?:\.eu)?\.lever\.co$"), re.compile(r"^/([^/]+)/[^/]+/?$"), "https://{host}/{slug}"),
    (re.compile(r"^ats\.rippling\.com$"), re.compile(r"^/([^/]+)/jobs/[^/]+/?$"), "https://{host}/{slug}/jobs"),
)


def is_board_host(host: str) -> bool:
    return any(rule[0].match(host) for rule in BOARD_RULES)


def board_index(urls):
    """The job board all of a company's posting links sit under, or None.

    Returns (index url, slug). The index is the parent path of every posting link held in
    data/jobs_raw.json, and only for the hosted boards whose index address is that parent.
    """
    found = set()
    for u in urls:
        p = urlsplit(str(u))
        host = (p.hostname or "").lower()
        if p.scheme != "https":
            return None
        for host_re, path_re, template in BOARD_RULES:
            if host_re.match(host):
                m = path_re.match(p.path)
                if not m:
                    return None
                found.add((template.format(host=host, slug=m.group(1)), m.group(1)))
                break
        else:
            return None
    return next(iter(found)) if len(found) == 1 else None


def _int(value):
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _num(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def collect_job_signals(weeks, file_dir, board_urls, registry):
    """weeks: [(file name, parsed weekly file)]. Only the five build-out signals can become events."""
    out = []
    for fname, doc in weeks:
        if not isinstance(doc, dict):
            continue
        generated, week = doc.get("generated"), clean_text(doc.get("week"))
        for i, s in enumerate(doc.get("signals") or []):
            if not isinstance(s, dict):
                continue
            kind, company = s.get("type"), s.get("company")
            file = f"{file_dir}/{fname}"
            if kind == "hiring_pullback":
                c = new_candidate("hiring_pullback", file, f"signals[{i}]", company, generated)
                add_reason(c, "negative_signal")
            elif kind == "board_check":
                c = new_candidate("board_check", file, f"signals[{i}]", company, generated)
                add_reason(c, "not_an_event", "a check on the job-board feed itself")
            elif kind in JOB_SIGNAL_TYPES:
                c = new_candidate(JOB_SIGNAL_TYPES[kind], file, f"signals[{i}]", company, generated)
                _fill_job_signal(c, s.get("evidence") if isinstance(s.get("evidence"), dict) else {})
                _fill_job_source(c, company, board_urls, registry)
            else:
                # Default deny: a signal type this script does not know is never published.
                c = new_candidate("job_signal_other", file, f"signals[{i}]", company, generated)
                add_reason(c, "not_an_event", "a signal type this method does not publish")
            c["key"] = f"job|{company}|{kind}|{week}|{c['detail'].get('state', '')}"
            out.append(c)
    return out


def _fill_job_signal(c, ev):
    kind = c["type"]
    c["raw"] = dict(ev)
    if kind == "hiring_surge":
        before, now, pct = _int(ev.get("roles_4w_ago")), _int(ev.get("roles_now")), _num(ev.get("change_pct"))
        c["detail"] = {"roles_before": before, "roles_now": now, "change_pct": pct}
        if before is None or now is None or pct is None or before <= 0 or now <= before:
            add_reason(c, "fields_not_confirmed", "the counts are missing or do not show a rise")
        elif abs(100 * (now - before) / before - pct) > 0.051:
            add_reason(c, "fields_not_confirmed", "the percentage does not follow from the counts")
        elif now > SURGE_MAX_RATIO * before:
            add_reason(c, "fields_implausible", "open roles more than tripled in four weeks")
    elif kind == "production_turn":
        was, now, roles = _num(ev.get("atoms_share_12w_ago_pct")), _num(ev.get("atoms_share_now_pct")), _int(ev.get("roles_now"))
        c["detail"] = {"share_before_pct": was, "share_now_pct": now, "roles_now": roles}
        if was is None or now is None or roles is None or not (0 <= was <= 100 and 0 <= now <= 100) or roles <= 0:
            add_reason(c, "fields_not_confirmed", "the shares or the role count are missing")
        elif now - was < TURN_MIN_POINTS - 0.051:
            add_reason(c, "fields_not_confirmed", "the shares do not show the rise the signal needs")
        elif was == 0:
            add_reason(c, "fields_implausible", "a starting share of zero usually means an incomplete earlier snapshot")
    elif kind == "first_mfg_role":
        mfg, roles = _int(ev.get("manufacturing_roles_now")), _int(ev.get("roles_now"))
        c["detail"] = {"mfg_roles_now": mfg, "roles_now": roles}
        if mfg is None or roles is None or mfg < 1 or roles < mfg:
            add_reason(c, "fields_not_confirmed", "the role counts are missing or inconsistent")
    elif kind == "senior_mfg_role":
        senior = _int(ev.get("senior_roles_now"))
        c["detail"] = {"senior_roles_now": senior}
        if senior is None or senior < 1:
            add_reason(c, "fields_not_confirmed", "the role count is missing")
    elif kind == "new_location":
        state, there = clean_text(ev.get("state")).upper(), _int(ev.get("postings_there"))
        c["detail"] = {"state": state, "postings_there": there}
        if state not in US_STATES or there is None or there < 1:
            add_reason(c, "fields_not_confirmed", "the state or the posting count is missing")
        else:
            cities = [clean_text(x) for x in (ev.get("cities") or []) if isinstance(x, str) and clean_text(x)]
            town = cities[0] if len(cities) == 1 and cities[0].endswith(", " + state) else None
            if town and town_key(town.rsplit(",", 1)[0]) == town_key(US_STATES[state]):
                town = None                      # "Ohio, OH" is a state, not a town
            c["place_hint"] = {"town": town, "state": state}


def _fill_job_source(c, company, board_urls, registry):
    """The link for a job-board signal: the board itself, else the company's own careers page."""
    urls = board_urls.get(company) or []
    reg = registry.get(company) or {}
    found = board_index(urls) if urls else None
    if found and clean_text(reg.get("slug")).lower() == found[1].lower():
        c["url"], c["url_rule"], c["source_name"] = found[0], "jobs", SOURCE_NAMES["job_board"]
        return
    m = re.match(r"^careers-page (https://\S+)$", clean_text(reg.get("evidence")))
    if m:
        c["url"], c["url_rule"], c["source_name"] = m.group(1), "careers", SOURCE_NAMES["careers"]
        return
    c["url"], c["url_rule"] = None, "jobs"


# ═══ lines: fixed templates, then an independent check against the fields ═

def render_line(ev) -> str:
    kind, name, d, amount = ev["type"], ev["company"], ev["detail"], ev["amount_usd"]
    if kind == "round":
        label, valuation = d.get("round_label"), d.get("valuation_usd")
        if amount is not None and label:
            text = f"{name} raised {article_for(fmt_usd(amount))} {fmt_usd(amount)} {label}"
        elif amount is not None:
            text = f"{name} raised {fmt_usd(amount)}"
        elif label:
            text = f"{name} raised {article_for(label)} {label}"
        else:
            text = f"{name} raised a funding round"
        if valuation is not None:
            text += f" at {article_for(fmt_usd(valuation))} {fmt_usd(valuation)} valuation"
        return text + "."
    if kind == "debt":
        if amount is not None:
            return f"{name} announced {fmt_usd(amount)} in debt financing."
        return f"{name} announced a debt financing."
    if kind == "form_d":
        head = f"{name} filed {'an amended Form D' if d.get('form') == 'D/A' else 'a Form D'} with the SEC"
        offering = d.get("offering_usd")
        debt = d.get("securities") == "Debt"
        if amount is not None and offering is not None:
            return f"{head} reporting {fmt_usd(amount)} sold of {article_for(fmt_usd(offering))} {fmt_usd(offering)}{' debt' if debt else ''} offering."
        if amount is not None:
            return f"{head} reporting {fmt_usd(amount)} sold{' in a debt offering' if debt else ''}."
        if offering is not None:
            return f"{head} for {article_for(fmt_usd(offering))} {fmt_usd(offering)}{' debt' if debt else ''} offering, with no sales reported yet."
        return head + "."
    if kind == "ipo_filing":
        form = d.get("form") or ""
        if form.endswith("/A"):
            return f"{name} filed an amended Form {form[:-2]} registration statement with the SEC."
        return f"{name} filed a Form {form} registration statement with the SEC."
    if kind == "contract":
        agency, sub = ev.get("agency"), d.get("sub_agency")
        size = f"{article_for(fmt_usd(amount))} {fmt_usd(amount)} contract" if amount is not None else "a contract"
        if not agency:
            return f"{name} was awarded {size} by a federal agency."
        return f"{name} was awarded {size} by the {agency}{' (' + sub + ')' if sub else ''}."
    if kind == "grant":
        size = f"{article_for(fmt_usd(amount))} {fmt_usd(amount)} grant" if amount is not None else "a grant"
        return f"{name} received {size} from the {ev['agency']}."
    if kind == "new_location":
        return (f"{name} listed {fmt_number(d['postings_there'])} open roles in {US_STATES[d['state']]}, "
                "a state where it had listed none in the prior twelve weeks.")
    if kind == "first_mfg_role":
        many = d["mfg_roles_now"] > 1
        return (f"{name} listed its first manufacturing role{'s' if many else ''} in at least four weeks "
                f"({fmt_number(d['mfg_roles_now'])} of {fmt_number(d['roles_now'])} open roles).")
    if kind == "senior_mfg_role":
        if d["senior_roles_now"] > 1:
            return f"{name} added a senior manufacturing, plant or facilities role and now lists {fmt_number(d['senior_roles_now'])}."
        return f"{name} listed a senior manufacturing, plant or facilities role."
    if kind == "production_turn":
        return (f"{name} shifted its open roles toward manufacturing and hardware, from "
                f"{fmt_number(d['share_before_pct'])}% to {fmt_number(d['share_now_pct'])}% of openings in twelve weeks "
                f"({fmt_number(d['roles_now'])} open roles).")
    if kind == "hiring_surge":
        return (f"{name} increased its open roles from {fmt_number(d['roles_before'])} to {fmt_number(d['roles_now'])} "
                f"in four weeks, a rise of {fmt_number(d['change_pct'])}%.")
    raise ValueError(f"no template for type {kind!r}")


_MONEY = r"\$\d+(?:\.\d+)?[KMBT]?"
_LABEL = r"Series [A-K](?:-[1-9])?|seed round|pre-seed round|growth round"
_COUNT = r"\d+(?:\.\d+)?"
_GRAMMAR = {
    "round": re.compile(
        r"^raised (?:(?P<art>an?) (?P<amount>" + _MONEY + r") (?P<label>" + _LABEL + r")"
        r"|(?P<amount2>" + _MONEY + r")"
        r"|(?P<art3>an?) (?P<label3>" + _LABEL + r")"
        r"|(?P<plain>a funding round))"
        r"(?: at (?P<vart>an?) (?P<valuation>" + _MONEY + r") valuation)?\.$"),
    "debt": re.compile(r"^announced (?:(?P<amount>" + _MONEY + r") in debt financing|(?P<plain>a debt financing))\.$"),
    "form_d": re.compile(
        r"^filed (?P<form>a Form D|an amended Form D) with the SEC"
        r"(?: reporting (?P<amount>" + _MONEY + r") sold(?: of (?P<art>an?) (?P<offering>" + _MONEY + r")(?P<debt> debt)? offering|(?P<debt2> in a debt offering))?"
        r"| for (?P<art2>an?) (?P<offering2>" + _MONEY + r")(?P<debt3> debt)? offering, with no sales reported yet)?\.$"),
    "ipo_filing": re.compile(r"^filed (?P<amended>a|an amended) Form (?P<form>[SF]-1) registration statement with the SEC\.$"),
    "contract": re.compile(
        r"^was awarded (?:(?P<art>an?) (?P<amount>" + _MONEY + r") contract|(?P<plain>a contract)) by "
        r"(?:the (?P<agency>[^()]+?)(?: \((?P<sub>[^()]+)\))?|(?P<unnamed>a federal agency))\.$"),
    "grant": re.compile(
        r"^received (?:(?P<art>an?) (?P<amount>" + _MONEY + r") grant|(?P<plain>a grant)) from the (?P<agency>[^()]+)\.$"),
    "new_location": re.compile(
        r"^listed (?P<there>" + _COUNT + r") open roles in (?P<state>[A-Z][A-Za-z ]+), "
        r"a state where it had listed none in the prior twelve weeks\.$"),
    "first_mfg_role": re.compile(
        r"^listed its first manufacturing (?P<noun>roles?) in at least four weeks "
        r"\((?P<mfg>" + _COUNT + r") of (?P<roles>" + _COUNT + r") open roles\)\.$"),
    "senior_mfg_role": re.compile(
        r"^(?:listed a senior manufacturing, plant or facilities role"
        r"|added a senior manufacturing, plant or facilities role and now lists (?P<senior>" + _COUNT + r"))\.$"),
    "production_turn": re.compile(
        r"^shifted its open roles toward manufacturing and hardware, from (?P<was>" + _COUNT + r")% to "
        r"(?P<now>" + _COUNT + r")% of openings in twelve weeks \((?P<roles>" + _COUNT + r") open roles\)\.$"),
    "hiring_surge": re.compile(
        r"^increased its open roles from (?P<before>" + _COUNT + r") to (?P<now>" + _COUNT + r") "
        r"in four weeks, a rise of (?P<pct>" + _COUNT + r")%\.$"),
}


def verify_line(ev):
    """Parse the line back and compare every part with the fields. Returns a list of problems."""
    line, name, kind = ev.get("line"), ev.get("company"), ev.get("type")
    if not isinstance(line, str) or not line:
        return ["no line"]
    if kind not in _GRAMMAR:
        return [f"no grammar for type {kind!r}"]
    if not isinstance(name, str) or not line.startswith(name + " "):
        return ["the line does not start with the company name"]
    rest = line[len(name) + 1:]
    problems = []
    if "  " in line or line != line.strip():
        problems.append("stray whitespace")
    if re.search(r"\b(?:None|null|undefined|nan|NaN)\b|[{}<>]", rest):
        problems.append("an empty field leaked into the line")
    praise = sorted(set(re.findall(r"[a-z][a-z-]+", rest.lower())) & PRAISE_WORDS)
    if praise:
        problems.append("praise word in the line: " + ", ".join(praise))
    m = _GRAMMAR[kind].match(rest)
    if not m:
        return problems + ["the line does not fit the template for its type"]
    g = m.groupdict()
    d, amount = ev.get("detail") or {}, ev.get("amount_usd")

    def same(what, got, want):
        if got != want:
            problems.append(f"{what}: line says {got!r}, fields say {want!r}")

    def money(v):
        return fmt_usd(v) if v is not None else None

    def article(art, token):
        if token is not None:
            same("article", art, article_for(token))

    if kind == "round":
        got_amount = g["amount"] or g["amount2"]
        got_label = g["label"] or g["label3"]
        same("amount", got_amount, money(amount))
        same("round", got_label, d.get("round_label"))
        same("valuation", g["valuation"], money(d.get("valuation_usd")))
        article(g["art"], g["amount"])
        article(g["art3"], g["label3"])
        article(g["vart"], g["valuation"])
        if g["plain"] and (amount is not None or d.get("round_label")):
            problems.append("the line leaves out a field the event has")
    elif kind == "debt":
        same("amount", g["amount"], money(amount))
    elif kind == "form_d":
        same("form", g["form"], "an amended Form D" if d.get("form") == "D/A" else "a Form D")
        same("amount sold", g["amount"], money(amount))
        got_offering = g["offering"] or g["offering2"]
        same("offering", got_offering, money(d.get("offering_usd")))
        article(g["art"], g["offering"])
        article(g["art2"], g["offering2"])
        said_debt = bool(g["debt"] or g["debt2"] or g["debt3"])
        if amount is not None or d.get("offering_usd") is not None:
            same("debt", said_debt, d.get("securities") == "Debt")
    elif kind == "ipo_filing":
        form = d.get("form") or ""
        same("form", g["form"] + ("/A" if g["amended"] == "an amended" else ""), form)
    elif kind == "contract":
        same("amount", g["amount"], money(amount))
        same("agency", g["agency"], ev.get("agency") or None)
        same("sub-agency", g["sub"], d.get("sub_agency") if ev.get("agency") else None)
        article(g["art"], g["amount"])
    elif kind == "grant":
        same("amount", g["amount"], money(amount))
        same("agency", g["agency"], ev.get("agency"))
        article(g["art"], g["amount"])
    elif kind == "new_location":
        same("postings", g["there"], fmt_number(d.get("postings_there")))
        same("state", g["state"], US_STATES.get(d.get("state")))
    elif kind == "first_mfg_role":
        same("manufacturing roles", g["mfg"], fmt_number(d.get("mfg_roles_now")))
        same("open roles", g["roles"], fmt_number(d.get("roles_now")))
        same("plural", g["noun"], "roles" if (d.get("mfg_roles_now") or 0) > 1 else "role")
    elif kind == "senior_mfg_role":
        senior = d.get("senior_roles_now")
        same("senior roles", g["senior"], fmt_number(senior) if senior and senior > 1 else None)
    elif kind == "production_turn":
        same("share before", g["was"], fmt_number(d.get("share_before_pct")))
        same("share now", g["now"], fmt_number(d.get("share_now_pct")))
        same("open roles", g["roles"], fmt_number(d.get("roles_now")))
    elif kind == "hiring_surge":
        same("roles before", g["before"], fmt_number(d.get("roles_before")))
        same("roles now", g["now"], fmt_number(d.get("roles_now")))
        same("change", g["pct"], fmt_number(d.get("change_pct")))
    return problems


# ═══ score ═══════════════════════════════════════════════════════════════

def dollar_points(amount) -> Decimal:
    """POINTS_PER_TENFOLD for every tenfold step above the floor, capped. Decimal, so the
    result is the same on every machine."""
    if amount is None or amount <= DOLLAR_FLOOR_USD:
        return Decimal("0.0")
    with localcontext() as ctx:
        ctx.prec = 28
        points = (Decimal(int(amount)) / Decimal(DOLLAR_FLOOR_USD)).log10() * POINTS_PER_TENFOLD
    return min(points, Decimal(DOLLAR_CAP_POINTS)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def score_parts(kind, amount, first):
    return {
        "type": TYPES[kind]["points"],
        "dollars": float(dollar_points(amount)),
        "first": FIRST_POINTS if first else 0,
    }


def score_total(parts) -> float:
    total = Decimal(parts["type"]) + Decimal(str(parts["dollars"])) + Decimal(parts["first"])
    return float(total.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


# ═══ the pipeline ════════════════════════════════════════════════════════

def check_url(cand, company):
    url = cand.get("url")
    if not url:
        return "no_source_url"
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or not host or re.search(r"\s", url):
        return "source_not_primary"
    bare = host[4:] if host.startswith("www.") else host
    rule = cand.get("url_rule")
    if company is None and rule in ("newsroom", "careers"):
        return None                 # whose site it is cannot be judged without the company record
    sites = [host_of(company.get("website")), host_of(cand.get("site"))] if company else []
    own = any(same_site(bare, s) for s in sites if s)
    if rule == "sec":
        ok = bare == "sec.gov" or bare.endswith(".sec.gov")
    elif rule == "gov":
        ok = bare.endswith(".gov")
    elif rule == "newsroom":
        ok = own or is_wire(bare)
        if ok:
            cand["source_name"] = SOURCE_NAMES["newsroom"] if own else SOURCE_NAMES["wire"]
    elif rule == "jobs":
        ok = is_board_host(host)
    elif rule == "careers":
        ok = own
    else:
        ok = False
    return None if ok else "source_not_primary"


def place_for(cand, company, towns):
    hint = cand.get("place_hint")
    if hint:
        town = hint.get("town")
        known = towns.get(town_key(town)) if town else None
        if known:
            return {"name": known["name"], "state": hint.get("state"), "lat": known["lat"], "lng": known["lng"], "basis": "source"}
        name = town or US_STATES.get(hint.get("state")) or None
        return {"name": name, "state": hint.get("state"), "lat": None, "lng": None, "basis": "source"}
    known = towns.get(town_key(company["location"])) if company["location"] else None
    return {
        "name": company["location"] or None,
        "state": company_state(company),
        "lat": known["lat"] if known else None,
        "lng": known["lng"] if known else None,
        "basis": "hq",
    }


def primary_reason(reasons):
    return min(reasons, key=PRECEDENCE.index)


def evaluate(cands, index: CompanyIndex, towns, today: date, include_job_signals: bool):
    """Run every check on every candidate and set its status."""
    for c in cands:
        company = index.match(c["company_raw"])
        if company is None:
            add_reason(c, "company_not_in_database")
        else:
            c["company"] = company["name"]
            c["co"] = company
            if not is_us(company):
                add_reason(c, "outside_us")
        if c["type"] in TYPES:
            why = check_url(c, company)
            if why:
                add_reason(c, why)
        day, why = parse_day(c["date_raw"])
        if day is not None:
            why = check_day(day, today, company.get("founded") if company else None)
        if why and c["type"] in TYPES:
            add_reason(c, why)
        if day is not None:
            c["day"] = day

    # The same announcement posted twice by a company (same day, same amount) is one event.
    clean = [c for c in cands if c["status"] is None and not c["reasons"] and c["type"] in ("round", "debt") and c.get("dedupe")]
    groups = defaultdict(list)
    for c in clean:
        groups[(c["company"], c["day"], c["dedupe"])].append(c)
    for members in groups.values():
        labels = {m["detail"].get("round_label") for m in members} - {None}
        valuations = {m["detail"].get("valuation_usd") for m in members} - {None}
        if len(members) < 2 or len(labels) > 1 or len(valuations) > 1:
            continue
        members.sort(key=lambda m: (m["rank"], m["url"]))
        head = members[0]
        for other in members[1:]:
            other["status"] = "merged"
            if other["url"] != head["url"] and other["url"] not in head["also"]:
                head["also"].append(other["url"])
            head.setdefault("merged_refs", []).append(other)

    for c in cands:
        if c["status"] == "merged":
            continue
        if not c["reasons"]:
            c["place"] = place_for(c, c["co"], towns)
            try:
                c["line"] = render_line(c)
                problems = verify_line(c)
            except (KeyError, TypeError, ValueError) as exc:
                problems = [f"template failed: {exc}"]
            if problems:
                add_reason(c, "line_mismatch", "; ".join(problems))
        if c["reasons"]:
            c["status"] = "rejected"
        elif TYPES[c["type"]]["stream"] == "jobs" and not include_job_signals:
            c["status"] = "held"
        else:
            c["status"] = "published"
    return cands


LINK_ONLY = frozenset({"no_source_url", "source_not_primary"})


def mark_firsts(cands):
    """first_of_kind: the earliest event of its type for the company in this site's record.

    The record is every dated row for a tracked company of that type, including rows that
    cannot be published only because they have no link. A first is claimed only where the
    record of that type starts at least FIRST_RECORD_DAYS before the event.
    """
    history = defaultdict(list)
    for c in cands:
        if c["type"] in TYPES and c["status"] != "merged" and c["company"] and c["day"] and set(c["reasons"]) <= LINK_ONLY:
            history[c["type"]].append(c)
    for kind, rows in history.items():
        record_start = min(r["day"] for r in rows)
        earliest = {}
        for r in sorted(rows, key=lambda r: (r["day"], r["key"] or "")):
            earliest.setdefault(r["company"], r)
        for r in rows:
            r["first"] = bool(
                TYPES[kind]["first"]
                and earliest[r["company"]] is r
                and (r["day"] - record_start).days >= FIRST_RECORD_DAYS
            )


def thread_events(events):
    """Follow-ups (same company, same type, within THREAD_DAYS of the first event) join its thread."""
    by_pair = defaultdict(list)
    for e in events:
        by_pair[(e["company"], e["type"])].append(e)
    for members in by_pair.values():
        members.sort(key=lambda e: (e["date"], e["id"]))
        root = None
        for e in members:
            if root is None or (date.fromisoformat(e["date"]) - date.fromisoformat(root["date"])).days > THREAD_DAYS:
                root = e
                root["thread"] = {"root": root["id"], "position": 0, "size": 1}
            else:
                root["thread"]["size"] += 1
                e["thread"] = {"root": root["id"], "position": root["thread"]["size"] - 1, "size": None}
        for e in members:
            if e["thread"]["size"] is None:
                e["thread"]["size"] = next(m for m in members if m["id"] == e["thread"]["root"])["thread"]["size"]


def to_event(c, today: date):
    parts = score_parts(c["type"], c["amount_usd"], c.get("first", False))
    provenance = [{"file": c["file"], "ref": c["ref"], "fields": c["raw"]}]
    for other in c.get("merged_refs", []):
        provenance.append({"file": other["file"], "ref": other["ref"], "fields": other["raw"]})
    return {
        "id": stable_id(c["type"], c["key"]),
        "type": c["type"],
        "company": c["company"],
        "sector": c["co"]["sector"] or None,
        "date": c["day"].isoformat(),
        "age_days": (today - c["day"]).days,
        "amount_usd": c["amount_usd"],
        "agency": c["agency"],
        "program": c["program"],
        "place": c["place"],
        "source": {"name": c["source_name"], "url": c["url"], "also": sorted(c["also"])},
        "detail": c["detail"],
        "line": c["line"],
        "first_of_kind": bool(c.get("first", False)),
        "score": score_total(parts),
        "score_parts": parts,
        "provenance": provenance,
    }


def rank_key(e):
    return (-e["score"], -date.fromisoformat(e["date"]).toordinal(), e["company"].lower(), e["id"])


def build(root: Path, today: date, include_job_signals: bool = False):
    """Read the inputs under root and return everything the four output files need."""
    root = Path(root)
    companies = load_companies(root)
    index = CompanyIndex(companies)
    towns = build_towns(companies, read_input(root, INPUTS["geocode"]))

    sources, cands = [], []

    def note_source(key, role, rows, note=None, skipped=0):
        sources.append({"file": INPUTS[key], "role": role, "rows": rows, "rows_not_read_as_events": skipped, "note": note})

    def rows_of(doc, field=None):
        if field and isinstance(doc, dict):
            doc = doc.get(field)
        return len(doc) if isinstance(doc, list) else 0

    doc = read_input(root, INPUTS["announcements"])
    found = collect_newsroom(doc, INPUTS["announcements"])
    cands += found
    note_source("announcements", "events", len(found), "Funding announcements found on company newsrooms. One row per hit.")

    doc = read_input(root, INPUTS["deals"])
    found = collect_deals(doc, INPUTS["deals"])
    cands += found
    note_source("deals", "events", len(found), "Rounds taken from trade press. Read so the rows can be counted; the feed has no link field.")

    doc = read_input(root, INPUTS["funding_tracker"])
    n = rows_of(doc)
    note_source("funding_tracker", "roll-up", n, "One summary row per company, built from the deals feed. The single rounds are read from the deals feed.", skipped=n)

    docs = [(INPUTS[k], read_input(root, INPUTS[k])) for k in ("form_d_daily", "form_d")]
    found = collect_form_d(docs)
    cands += found
    for k in ("form_d", "form_d_daily"):
        note_source(k, "events", sum(1 for c in found if c["file"] == INPUTS[k]), "SEC Form D filings matched to a company by its SEC number.")

    doc = read_input(root, INPUTS["sec_filings"])
    found, skipped = collect_ipo_filings(doc, INPUTS["sec_filings"])
    cands += found
    note_source("sec_filings", "events", len(found) + skipped,
                "Only registration statements (" + ", ".join(IPO_FORMS) + ") are read as events. Ownership forms and periodic reports are not.",
                skipped=skipped)

    doc = read_input(root, INPUTS["ipo_pipeline"])
    found = collect_ipo_pipeline(doc, INPUTS["ipo_pipeline"])
    cands += found
    note_source("ipo_pipeline", "events", len(found), "Likelihoods and estimated dates. Never an event.")

    links = award_link_index(read_input(root, INPUTS["award_links"]))
    note_source("award_links", "link lookup", len(links), "USAspending permalinks keyed by award id. Used only to give a contract its link.", skipped=len(links))

    doc = read_input(root, INPUTS["contracts"])
    found = collect_contracts(doc, INPUTS["contracts"], index, links)
    cands += found
    note_source("contracts", "events", len(found), "Federal contract awards from USAspending. The fetcher stores no link to the award.")

    doc = read_input(root, INPUTS["contracts_rollup"])
    n = rows_of(doc)
    note_source("contracts_rollup", "roll-up", n, "One summary row per company. The single awards are read from gov_contracts_raw.json.", skipped=n)

    doc = read_input(root, INPUTS["nsf"])
    found = collect_grants(doc, INPUTS["nsf"])
    cands += found
    note_source("nsf", "events", len(found), "National Science Foundation awards. Published only when the awardee is a company in data.js.")

    doc = read_input(root, INPUTS["launches"])
    found = collect_launches(doc, INPUTS["launches"])
    cands += found
    note_source("launches", "events", len(found), "A list of upcoming launches. A scheduled launch is not an event.")

    signals_dir = root / INPUTS["job_signals"]
    weeks = []
    if signals_dir.is_dir():
        for path in sorted(signals_dir.glob("*.json")):
            weeks.append((path.name, read_input(root, f"{INPUTS['job_signals']}/{path.name}")))
    wanted = set()
    for _, wdoc in weeks:
        for s in (wdoc.get("signals") if isinstance(wdoc, dict) else None) or []:
            if isinstance(s, dict) and s.get("type") in JOB_SIGNAL_TYPES and isinstance(s.get("company"), str):
                wanted.add(s["company"])
    board_urls = defaultdict(list)
    jobs = read_input(root, INPUTS["jobs"]) if wanted else None
    for j in jobs if isinstance(jobs, list) else []:
        if isinstance(j, dict) and j.get("company") in wanted and isinstance(j.get("url"), str):
            board_urls[j["company"]].append(j["url"])
    registry_doc = read_input(root, INPUTS["job_boards"]) if wanted else None
    registry = {r["company"]: r for r in (registry_doc if isinstance(registry_doc, list) else []) if isinstance(r, dict) and isinstance(r.get("company"), str)}
    found = collect_job_signals(weeks, INPUTS["job_signals"], board_urls, registry)
    cands += found
    note_source("job_signals", "events", len(found), "Weekly signals computed from public job boards. Only the five build-out signals can become events.")
    note_source("jobs", "link lookup", sum(len(v) for v in board_urls.values()), "Job posting links. Used only to find the address of a company's job board.", skipped=sum(len(v) for v in board_urls.values()))
    note_source("job_boards", "link lookup", len(registry), "The register of each company's verified job board.", skipped=len(registry))

    evaluate(cands, index, towns, today, include_job_signals)
    mark_firsts(cands)

    events = [to_event(c, today) for c in cands if c["status"] == "published"]
    thread_events(events)
    events.sort(key=rank_key)

    return {
        "today": today,
        "include_job_signals": include_job_signals,
        "candidates": cands,
        "events": events,
        "sources": sources,
        "companies_total": len(index.records),
    }


# ═══ outputs ═════════════════════════════════════════════════════════════

def window_counts(events):
    return {str(w): sum(1 for e in events if 0 <= e["age_days"] <= w) for w in WINDOWS}


def tally(cands):
    """Counts for rejected.json. Names never appear here."""
    def blank():
        return {"rows": 0, "published": 0, "held": 0, "merged_duplicates": 0, "rejected": 0,
                "primary_reason": Counter(), "any_reason": Counter()}
    by_type, by_file = defaultdict(blank), defaultdict(blank)
    for c in cands:
        for bucket in (by_type[c["type"]], by_file[c["file"]]):
            bucket["rows"] += 1
            if c["status"] == "merged":
                bucket["merged_duplicates"] += 1
            elif c["status"] == "published":
                bucket["published"] += 1
            elif c["status"] == "held":
                bucket["held"] += 1
            else:
                bucket["rejected"] += 1
                bucket["primary_reason"][primary_reason(c["reasons"])] += 1
                for r in c["reasons"]:
                    bucket["any_reason"][r] += 1
    return by_type, by_file


def _ordered_reasons(counter):
    return OrderedDict((r, counter[r]) for r in PRECEDENCE if counter.get(r))


def awaiting_link(cands, today: date):
    """Events that passed every check except the link, by type and window."""
    out = OrderedDict()
    for kind in TYPES:
        rows = [c for c in cands if c["type"] == kind and c["status"] == "rejected" and c["reasons"] == ["no_source_url"] and c["day"]]
        if rows:
            ages = [(today - c["day"]).days for c in rows]
            out[kind] = OrderedDict([(str(w), sum(1 for a in ages if 0 <= a <= w)) for w in WINDOWS] + [("all", len(rows))])
    return out


def rejected_report(result):
    cands, today = result["candidates"], result["today"]
    by_type, by_file = tally(cands)
    labels = {k: v["label"] for k, v in TYPES.items()}
    labels.update(OTHER_KINDS)

    def bucket(b):
        return OrderedDict([
            ("rows", b["rows"]), ("published", b["published"]), ("held", b["held"]),
            ("merged_duplicates", b["merged_duplicates"]), ("rejected", b["rejected"]),
            ("primary_reason", _ordered_reasons(b["primary_reason"])),
            ("any_reason", _ordered_reasons(b["any_reason"])),
        ])

    types = OrderedDict()
    for kind in list(TYPES) + list(OTHER_KINDS):
        if kind in by_type:
            entry = OrderedDict([("label", labels[kind])])
            entry.update(bucket(by_type[kind]))
            types[kind] = entry
    files = []
    for s in result["sources"]:
        entry = OrderedDict([("file", s["file"]), ("role", s["role"]), ("note", s["note"]),
                             ("rows_in_file", s["rows"]), ("rows_not_read_as_events", s["rows_not_read_as_events"])])
        matched = [k for k in by_file if k == s["file"] or k.startswith(s["file"] + "/")]
        if matched:
            merged = {"rows": 0, "published": 0, "held": 0, "merged_duplicates": 0, "rejected": 0,
                      "primary_reason": Counter(), "any_reason": Counter()}
            for k in matched:
                for field in ("rows", "published", "held", "merged_duplicates", "rejected"):
                    merged[field] += by_file[k][field]
                merged["primary_reason"].update(by_file[k]["primary_reason"])
                merged["any_reason"].update(by_file[k]["any_reason"])
            entry.update(bucket(merged))
        files.append(entry)
    totals = Counter(c["status"] for c in cands)
    return OrderedDict([
        ("as_of", today.isoformat()),
        ("method_version", METHOD_VERSION),
        ("note", "Counts only. No company is named in this file."),
        ("job_board_signals", "published" if result["include_job_signals"] else "held: switched off until the owner turns them on"),
        ("totals", OrderedDict([
            ("rows_read_as_events", len(cands)),
            ("published", totals.get("published", 0)),
            ("held", totals.get("held", 0)),
            ("merged_duplicates", totals.get("merged", 0)),
            ("rejected", totals.get("rejected", 0)),
        ])),
        ("reasons", REASONS),
        ("by_type", types),
        ("by_source", files),
        ("passed_every_check_except_the_link", awaiting_link(cands, today)),
    ])


def events_report(result):
    events, today = result["events"], result["today"]
    ordered = sorted(events, key=lambda e: (-date.fromisoformat(e["date"]).toordinal(), -e["score"], e["company"].lower(), e["id"]))
    return OrderedDict([
        ("as_of", today.isoformat()),
        ("method_version", METHOD_VERSION),
        ("counts", OrderedDict([
            ("published", len(events)),
            ("by_window_days", window_counts(events)),
            ("by_type", OrderedDict((k, sum(1 for e in events if e["type"] == k)) for k in TYPES if any(e["type"] == k for e in events))),
        ])),
        ("events", ordered),
    ])


def page_payload(result):
    events, today, cands = result["events"], result["today"], result["candidates"]
    by_id = {e["id"]: e for e in events}
    rows = []
    for e in events:
        if not 0 <= e["age_days"] <= PAYLOAD_DAYS:
            continue
        row = OrderedDict([
            ("id", e["id"]), ("type", e["type"]), ("company", e["company"]), ("sector", e["sector"]),
            ("date", e["date"]), ("amount", e["amount_usd"]), ("line", e["line"]),
            ("url", e["source"]["url"]), ("source", e["source"]["name"]), ("also", e["source"]["also"]),
            ("agency", e["agency"]), ("program", e["program"]),
            ("place", e["place"]["name"]), ("state", e["place"]["state"]),
            ("lat", e["place"]["lat"]), ("lng", e["place"]["lng"]), ("basis", e["place"]["basis"]),
            ("score", e["score"]),
            ("parts", [e["score_parts"]["type"], e["score_parts"]["dollars"], e["score_parts"]["first"]]),
            ("first", e["first_of_kind"]),
            ("thread", e["thread"]["root"]),
        ])
        if e["thread"]["root"] != e["id"]:
            root = by_id[e["thread"]["root"]]
            row["follows"] = OrderedDict([("date", root["date"]), ("line", root["line"]), ("url", root["source"]["url"])])
        rows.append(row)
    held = [k for k, v in TYPES.items() if v["stream"] == "jobs"] if not result["include_job_signals"] else []
    return OrderedDict([
        ("as_of", today.isoformat()),
        ("method_version", METHOD_VERSION),
        ("payload_days", PAYLOAD_DAYS),
        ("windows", list(WINDOWS)),
        ("thread_days", THREAD_DAYS),
        ("coord_decimals", COORD_DECIMALS),
        ("companies_tracked", result["companies_total"]),
        ("types", OrderedDict((k, OrderedDict([("label", v["label"]), ("points", v["points"]), ("first", v["first"])])) for k, v in TYPES.items())),
        ("scoring", OrderedDict([
            ("dollar_floor_usd", DOLLAR_FLOOR_USD), ("points_per_tenfold", POINTS_PER_TENFOLD),
            ("dollar_cap_points", DOLLAR_CAP_POINTS), ("first_points", FIRST_POINTS),
            ("first_record_days", FIRST_RECORD_DAYS),
        ])),
        ("held_types", held),
        ("awaiting_link", OrderedDict(
            (k, OrderedDict((w, n) for w, n in v.items() if w != "all"))
            for k, v in awaiting_link(cands, today).items()
            if k not in held and any(n for w, n in v.items() if w != "all"))),
        ("events", rows),
    ])


def method_text() -> str:
    type_rows = "\n".join(
        f"| {v['label']} | `{k}` | {v['points']} | {'yes' if v['first'] else 'no'} |" for k, v in TYPES.items())
    reason_rows = "\n".join(f"| `{k}` | {v} |" for k, v in REASONS.items())
    examples = ", ".join(
        f"{fmt_usd(a)} = {format(dollar_points(a), 'f')}" for a in (100_000, 1_000_000, 10_000_000, 100_000_000, 1_000_000_000, 10_000_000_000))
    return f"""# The Build-Out, Live: method v{METHOD_VERSION}

This file is written by `scripts/build_lagebild.py` from the constants in that script. Edit the script, not this file.

One page that turns each public sign that a tracked US company is building into one line with its source. Version 1 uses only data this repo already collects. Nothing is written by a language model and nothing is fetched at build time.

## The seven steps

1. **Collect from primary sources only.** SEC filings, federal award records, company newsrooms and public job boards. Feeds built from trade press are read so their rows can be counted and rejected. They are never published.
2. **Drop what is not an event.** A forecast, a likelihood, an estimate, a schedule or a data check is not an event. A summary row per company is not read as an event; the single rows behind it are.
3. **Fixed fields.** Company, event type, amount in US dollars (or empty), place, date, agency or programme where relevant, source. What the source data does not hold stays empty. Nothing is guessed. An amount in another currency is left empty, not converted.
4. **Place.** Town level only. Coordinates are rounded to {COORD_DECIMALS} decimal place (about 11 km), so a point marks a town, never a building. When the source names no place, the event sits at the company's headquarters town and is labelled "HQ town". A place the repo cannot locate is listed but not mapped.
5. **One line per event.** A fixed template per event type fills in the fields. The finished line is then parsed back and every part is compared with the fields. Any mismatch rejects the event.
6. **Score.** Built only from the fields. See below.
7. **Publish with the source linked.** An event with no link to a primary source in repo data is rejected and counted in `rejected.json` with the reason. A follow-up (same company, same event type, within {THREAD_DAYS} days of the first event) is threaded onto the first event.

## Who is in scope

A company must match a record in `data.js` by its exact name, its name ignoring case, or a recorded former name. There is no fuzzy matching. The company must be headquartered in the United States.

## Event types

| Type | Key | Type points | Can earn first-of-kind points |
|---|---|---|---|
{type_rows}

What each type means:

- **Funding round, debt financing.** A dated post on the company's own newsroom, or its own release on a press wire, whose headline states a completed raise by the company. The amount, round and valuation are taken from the headline, and the amount must agree with the newsroom collector's figure. A headline about a plan, an acquisition, a grant or a contract is not read as a round.
- **SEC Form D.** A filing matched to the company by its SEC number. The amount is the amount sold.
- **IPO filing.** A Form S-1 or F-1 registration statement. A pipeline estimate is not an event.
- **Federal contract.** One award from USAspending. The date is the award's start date as USAspending reports it.
- **Federal grant.** One National Science Foundation award to a tracked company.
- **Job-board signals.** Computed each week from public job boards (the weekly files in `data/pulse/signals/`): a new location (at least two postings in a state where the company listed none in the prior twelve weeks), a first manufacturing role (after at least four weeks without one), a senior manufacturing, plant or facilities role, a shift to production roles (the share of manufacturing and hardware titles up at least {TURN_MIN_POINTS} points in twelve weeks), and a rise in open roles (up at least 30% in four weeks). The date is the day the signal was recorded. Two guards: a rise of more than {SURGE_MAX_RATIO - 1}00% in four weeks, or a shift that starts from a share of zero, is treated as a change in the feed and rejected. These signals are held out of the public files until the build is run with `--include-job-signals`.

Never published: hiring pullbacks or any other negative or distress signal about a named company; investor names; anything from fund, brief or private files (the script refuses to open them).

## How this is ranked

`score = type points + dollar points + first-of-kind points`

- **Type points.** The table above. Types that carry a dollar figure start lower and earn most of their score from the dollars. Types that never carry a dollar figure start higher, in order of how directly they show building.
- **Dollar points.** `{POINTS_PER_TENFOLD} x log10(amount / {fmt_usd(DOLLAR_FLOOR_USD)})`, never below 0 and never above {DOLLAR_CAP_POINTS}, rounded to one decimal place. So {examples}. An event with no dollar figure gets 0.
- **First-of-kind points.** {FIRST_POINTS} points when the event is the earliest of its type for that company in this site's record, and only where the record of that type starts at least {FIRST_RECORD_DAYS} days before the event. The record includes rows that cannot be published only because they lack a link. These points are not given to funding rounds, debt financings or Form D filings, because this site's history of rounds is incomplete and a "first" claim could be wrong.
- **Order.** Higher score first. Ties: the newer event first, then the company name.

The formula is the same for every event. It is never tuned for one event.

## The counters on the page

All four cover the last 7 days up to the build date.

- **Funding rounds.** The number of funding-round threads.
- **Raised.** For each of those threads, the largest amount stated in the thread, added up. Debt financings and Form D filings are listed in the feed but not added, because a filing or a second post can repeat an announced round.
- **Federal contracts.** The number of contract events.
- **New locations and first manufacturing roles.** The number of those two job-board events.

## Why an event is rejected

Every rejected row is counted under one primary reason (the first that applies, in this order) and under every reason that applies.

| Reason | Meaning |
|---|---|
{reason_rows}

## Known gaps in the source data

- `data/deals_auto.json` has no link field and its dates have no day. Every row is rejected. To publish them, the collector needs to store the address of the company's own announcement (or the SEC filing) and the full date.
- `data/gov_contracts_raw.json` has no link field. USAspending returns a `generated_internal_id` for each award. Storing `https://www.usaspending.gov/award/<generated_internal_id>` as `url`, the way `scripts/fetch_sbir_awards.py` already does, would let these awards through.
- `data/sec_filings_raw.json` holds accession numbers but no filing address.
- `data/launch_manifest_auto.json` is a list of upcoming launches. A list of completed launches with the operator's own link would be needed.

## Files

- `events.json`: every published event, with the fields, the line, the score and its parts, the thread, and where each field came from.
- `rejected.json`: counts by type, by source file and by reason. No company is named.
- `../lagebild_auto.js`: the last {PAYLOAD_DAYS} days for the page.

## Run it

```
python3 scripts/build_lagebild.py --today 2026-11-20
python3 -m unittest scripts/tests/test_lagebild.py
```

The same `--today` and the same inputs give byte-identical files.
"""


def dump(obj) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False) + "\n"


def render_outputs(result):
    """file path (relative to the repo root) -> text."""
    payload = page_payload(result)
    page = (
        "// Auto-generated by scripts/build_lagebild.py. Do not edit by hand.\n"
        "// The Build-Out, Live: one sourced line per public build-out event, last "
        f"{PAYLOAD_DAYS} days.\n"
        f"// As of {result['today'].isoformat()}. Method: data/lagebild/README-METHOD.md\n"
        f"const LAGEBILD = {json.dumps(payload, indent=1, ensure_ascii=False)};\n"
    )
    return OrderedDict([
        (OUT_EVENTS, dump(events_report(result))),
        (OUT_REJECTED, dump(rejected_report(result))),
        (OUT_METHOD, method_text()),
        (OUT_PAGE, page),
    ])


def write_outputs(root: Path, outputs):
    for rel, text in outputs.items():
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)


def print_summary(result, out=None):
    out = out or sys.stdout
    events, cands = result["events"], result["candidates"]
    totals = Counter(c["status"] for c in cands)
    print(f"as of {result['today'].isoformat()} | companies in data.js: {result['companies_total']}", file=out)
    print(f"rows read as events: {len(cands)} | published: {totals.get('published', 0)} | held: {totals.get('held', 0)} "
          f"| merged duplicates: {totals.get('merged', 0)} | rejected: {totals.get('rejected', 0)}", file=out)
    counts = window_counts(events)
    print("published by window: " + ", ".join(f"{w} days: {counts[str(w)]}" for w in WINDOWS), file=out)
    by_type, _ = tally(cands)
    labels = {k: v["label"] for k, v in TYPES.items()}
    labels.update(OTHER_KINDS)
    for kind in list(TYPES) + list(OTHER_KINDS):
        if kind not in by_type:
            continue
        b = by_type[kind]
        in_windows = ", ".join(f"{w}d {sum(1 for e in events if e['type'] == kind and 0 <= e['age_days'] <= w)}" for w in WINDOWS)
        why = ", ".join(f"{r} {n}" for r, n in _ordered_reasons(b["primary_reason"]).items())
        print(f"  {labels[kind]:<30} rows {b['rows']:>5} | published {b['published']:>4} ({in_windows}) | held {b['held']:>3} "
              f"| merged {b['merged_duplicates']:>4} | rejected {b['rejected']:>5}{' : ' + why if why else ''}", file=out)


def list_rejects(result, reason, out=None):
    """Local debugging: the rows rejected for one reason. Negative signals are never listed."""
    out = out or sys.stdout
    if reason == "negative_signal":
        print("negative signals are never listed", file=out)
        return
    for c in result["candidates"]:
        if c["status"] == "rejected" and reason in c["reasons"] and "negative_signal" not in c["reasons"]:
            print(f"{c['type']} | {c['company_raw']} | {c['date_raw']} | {c['file']} {c['ref']}"
                  f"{' | ' + c['note'] if c['note'] else ''}", file=out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build the data files for lagebild.html.")
    ap.add_argument("--today", help="build date, YYYY-MM-DD (default: today, UTC)")
    ap.add_argument("--root", default=str(ROOT), help="repo root (default: the repo this script is in)")
    ap.add_argument("--include-job-signals", action="store_true",
                    help="publish the job-board signals (held by default; an owner decision)")
    ap.add_argument("--list-rejects", metavar="REASON", choices=[r for r in REASONS if r != "negative_signal"],
                    help="print the rows rejected for one reason, then exit without writing")
    args = ap.parse_args(argv)
    try:
        today = date.fromisoformat(args.today) if args.today else datetime.now(timezone.utc).date()
    except ValueError:
        ap.error("--today must be YYYY-MM-DD")
    result = build(Path(args.root), today, include_job_signals=args.include_job_signals)
    if args.list_rejects:
        list_rejects(result, args.list_rejects)
        return 0
    outputs = render_outputs(result)
    write_outputs(Path(args.root), outputs)
    print_summary(result)
    for rel, text in outputs.items():
        print(f"wrote {rel} ({len(text.encode('utf-8')):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
