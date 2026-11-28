#!/usr/bin/env python3
"""
Who's Building It (working name): ideas from science fiction, where each one stands today,
and the companies in this database working on it.
─────────────────────────────────────────────────────────────────────────
Reads the hand-written theme file and today's data.js. Writes one file for the page.

The method, in the order the code applies it:
  1. Themes    data/imagined/themes.json is written by hand. Each theme names one early
               appearance of the idea in fiction (an entry in Not Boring's Sci-Fi Idea Bank,
               linked, never copied), a status on a four-step ladder, one dated
               primary-source fact behind that status, and one sentence on what is still
               missing compared with the story.
  2. Check     a theme without a status, a dated source or a gap line is refused, and so is
               a source dated after today. Sources must be https and primary: the Idea Bank
               is the index of fiction, never the evidence.
  3. Match     companies are matched by each theme's rules (subsectors, tags and a pattern
               read against short fields) and then corrected by hand (include, exclude).
               Dead and acquired companies drop out. A name in include or exclude that is
               no longer in data.js is reported, never guessed.
  4. Order     within a theme by total raised, largest first, then by name.
  5. Publish   data/imagined_auto.js for imagined.html and the company pages.

Outputs
  data/imagined_auto.js            const IMAGINED = {...};
  data/imagined/README-METHOD.md   the method, written from the constants below

Standard library only. No network. The outputs depend only on the two input files, so a
rebuild with unchanged inputs gives the same bytes.

Usage
  python3 scripts/build_imagined.py                        # build
  python3 scripts/build_imagined.py --check                # validate only, write nothing
  python3 scripts/build_imagined.py --strict               # warnings fail the build too
  python3 scripts/build_imagined.py --today 2026-11-25     # the date sources are checked against
  python3 scripts/build_imagined.py --show fusion-power    # print one theme's matches
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, OrderedDict
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent

# ─── the published constants ─────────────────────────────────────────────
# Changing any of these is a method change: bump METHOD_VERSION.
METHOD_VERSION = "1.0"

# The ladder, in order. The definitions are printed on the page and in README-METHOD.md.
STATUSES = OrderedDict([
    ("built", ("Built",
               "People use it for its main purpose outside a test: paying customers, "
               "routine operations or a public service.")),
    ("demonstrated", ("Demonstrated",
                      "It has worked in a real test, but nobody uses it routinely yet.")),
    ("in_development", ("In development",
                        "Teams are building it and parts of it work, but the whole thing "
                        "has not worked yet.")),
    ("still_fiction", ("Still fiction",
                       "Nobody has shown it working, even in a test.")),
])

IDEA_BANK_URL = "https://notboring.com/sci-fi-idea-bank"
IDEA_BANK_NAME = "Not Boring's Sci-Fi Idea Bank"
FICTION_SOURCE_NOTE = ("Not Boring's Sci-Fi Idea Bank builds on Bill Christensen's Technovelgy. "
                       "We link to its entries and do not copy their text.")

# The Idea Bank and its source index are where the fiction comes from. They are never the
# evidence for what has been built.
FORBIDDEN_EVIDENCE_HOSTS = ("notboring.com", "notboring.co", "technovelgy.com")

DEAD_STATUSES = frozenset({"dead", "acquired", "defunct", "closed", "shut down"})
FICTION_YEARS = (1500, 2030)
MAX_ALSO = 2
LIMITS = {"title": 48, "imagined": 160, "fact": 240, "gap": 200, "publisher": 80}
HOUSE_STYLE_BANNED = {"—": "an em dash"}      # public copy is plain: no em dashes

INPUTS = {"themes": "data/imagined/themes.json", "companies": "data.js"}
OUTPUTS = {"page": "data/imagined_auto.js", "method": "data/imagined/README-METHOD.md"}

THEME_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IDEA_ID = re.compile(r"^[rt]\d{1,5}$")
DAY = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
MATCH_KEYS = frozenset({"subsectors", "tags", "pattern", "wide", "include", "exclude"})
THEME_KEYS = frozenset({"id", "title", "imagined", "fiction", "also", "status", "evidence",
                        "gap", "checked", "match", "featured"})
EVIDENCE_KEYS = frozenset({"date", "accessed", "publisher", "url", "fact"})
UNDATED = "undated"               # a primary page that prints no date; needs "accessed"


class ThemeError(ValueError):
    """A theme file problem. The build stops and leaves yesterday's output in place."""


# ═══ data.js: a reader for the COMPANIES literal ═════════════════════════
# The same reader as scripts/build_lagebild.py: data only, and anything that is not plain
# data stops the build rather than being guessed.

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
    """Parse one JS array or object literal (data only) starting at text[pos]."""
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


def _text(value) -> str:
    return re.sub(r"\s+", " ", value).strip() if isinstance(value, str) else ""


def load_companies(root: Path):
    """The COMPANIES array from data.js, with only the fields this page uses."""
    path = root / INPUTS["companies"]
    if not path.is_file():
        raise FileNotFoundError(f"{INPUTS['companies']} not found under {root}")
    text = path.read_text(encoding="utf-8")
    m = re.search(r"\bconst\s+COMPANIES\s*=\s*\[", text)
    if not m:
        raise JSLiteralError("const COMPANIES = [ not found in data.js")
    records, _ = parse_js_literal(text, m.end() - 1)
    out = []
    for r in records:
        if not isinstance(r, dict) or not _text(r.get("name")):
            continue
        tags = r.get("tags") if isinstance(r.get("tags"), list) else []
        out.append({
            "name": _text(r["name"]),
            "status": _text(r.get("status")).lower(),
            "sector": _text(r.get("sector")),
            "subsector": _text(r.get("subsector")),
            "tags": [_text(t) for t in tags if _text(t)],
            "techApproach": _text(r.get("techApproach")),
            "description": _text(r.get("description")),
            "fundingStage": _text(r.get("fundingStage")),
            "totalRaised": _text(r.get("totalRaised")),
        })
    updated = re.search(r"\bconst\s+LAST_UPDATED\s*=\s*[\"'](\d{4}-\d{2}-\d{2})[\"']", text)
    return out, (updated.group(1) if updated else "")


# ═══ small helpers ═══════════════════════════════════════════════════════

def company_slug(name: str) -> str:
    """The same slug as companyToSlug() in utils.js, so links land on the right profile."""
    s = (name or "").lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


_MONEY = re.compile(r"([\d][\d,]*(?:\.\d+)?)\s*([KMBT])?", re.I)
_SCALE = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}


def raised_usd(value: str) -> float:
    """'$598M' -> 598000000.0. Text without a number (Undisclosed, '') is 0."""
    if not value or "$" not in value and not re.search(r"\d\s*[KMBT]\b", value, re.I):
        return 0.0
    m = _MONEY.search(value)
    if not m:
        return 0.0
    try:
        amount = float(m.group(1).replace(",", ""))
    except ValueError:
        return 0.0
    return amount * _SCALE.get((m.group(2) or "").upper(), 1.0)


def parse_day(raw: str):
    """'2025-04-07', '2025-04' or '2025' -> the latest day the text could mean (for the
    'not after today' check) and the text itself."""
    if not isinstance(raw, str) or not DAY.match(raw):
        return None
    parts = [int(p) for p in raw.split("-")]
    try:
        if len(parts) == 3:
            return date(*parts)
        if len(parts) == 2:
            year, month = parts
            nxt = date(year + (month == 12), month % 12 + 1, 1)
            return date.fromordinal(nxt.toordinal() - 1)
        return date(parts[0], 12, 31)
    except ValueError:
        return None


def host_of(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def idea_bank_link(idea_id: str) -> str:
    return f"{IDEA_BANK_URL}?idea={idea_id}"


# ═══ checking the theme file ═════════════════════════════════════════════

def _need_text(theme_id, field, value, limit=None):
    if not isinstance(value, str) or not value.strip():
        raise ThemeError(f"{theme_id}: {field} is missing")
    if limit and len(value) > limit:
        raise ThemeError(f"{theme_id}: {field} is {len(value)} characters (limit {limit})")
    for ch, label in HOUSE_STYLE_BANNED.items():
        if ch in value:
            raise ThemeError(f"{theme_id}: {field} contains {label}")
    return value.strip()


def check_fiction(theme_id, fic, where):
    if not isinstance(fic, dict):
        raise ThemeError(f"{theme_id}: {where} must be an object")
    idea_id = fic.get("idea_id")
    if not isinstance(idea_id, str) or not IDEA_ID.match(idea_id):
        raise ThemeError(f"{theme_id}: {where}.idea_id must look like r120 or t4488")
    year = fic.get("year")
    if not isinstance(year, int) or isinstance(year, bool) or not FICTION_YEARS[0] <= year <= FICTION_YEARS[1]:
        raise ThemeError(f"{theme_id}: {where}.year must be a whole year between {FICTION_YEARS[0]} and {FICTION_YEARS[1]}")
    return OrderedDict([
        ("idea_id", idea_id),
        ("entry", _need_text(theme_id, f"{where}.entry", fic.get("entry"), 90)),
        ("work", _need_text(theme_id, f"{where}.work", fic.get("work"), 120)),
        ("author", _need_text(theme_id, f"{where}.author", fic.get("author"), 90)),
        ("year", year),
        ("url", idea_bank_link(idea_id)),
    ])


def check_theme(raw, today: date):
    if not isinstance(raw, dict):
        raise ThemeError("every theme must be an object")
    theme_id = raw.get("id")
    if not isinstance(theme_id, str) or not THEME_ID.match(theme_id):
        raise ThemeError(f"theme id {theme_id!r} must be lower-case words joined by hyphens")
    unknown = sorted(set(raw) - THEME_KEYS)
    if unknown:
        raise ThemeError(f"{theme_id}: unknown field(s) {', '.join(unknown)}")

    status = raw.get("status")
    if status not in STATUSES:
        raise ThemeError(f"{theme_id}: status must be one of {', '.join(STATUSES)}")

    ev = raw.get("evidence")
    if not isinstance(ev, dict):
        raise ThemeError(f"{theme_id}: every status needs evidence (date, publisher, url, fact)")
    unknown = sorted(set(ev) - EVIDENCE_KEYS)
    if unknown:
        raise ThemeError(f"{theme_id}: unknown evidence field(s) {', '.join(unknown)}")
    url = ev.get("url")
    if not isinstance(url, str) or not url.startswith("https://") or not host_of(url):
        raise ThemeError(f"{theme_id}: evidence.url must be an https link")
    host = host_of(url)
    if any(host == h or host.endswith("." + h) for h in FORBIDDEN_EVIDENCE_HOSTS):
        raise ThemeError(f"{theme_id}: evidence must come from a primary source, not {host}")

    accessed = None
    if ev.get("date") == UNDATED:
        # A primary page that prints no date is cited as undated, with the day it was read.
        accessed = ev.get("accessed")
        acc_day = parse_day(accessed) if isinstance(accessed, str) and len(accessed) == 10 else None
        if acc_day is None:
            raise ThemeError(f"{theme_id}: an undated source needs evidence.accessed, the YYYY-MM-DD it was read")
        if acc_day > today:
            raise ThemeError(f"{theme_id}: evidence.accessed {accessed} is after {today.isoformat()}")
        first_day = acc_day
    else:
        if "accessed" in ev:
            raise ThemeError(f"{theme_id}: evidence.accessed is only for sources dated {UNDATED!r}")
        if parse_day(ev.get("date")) is None:
            raise ThemeError(f"{theme_id}: evidence.date must be YYYY-MM-DD, YYYY-MM, YYYY or {UNDATED!r}")
        # A month or year can only be refused once it is entirely in the future.
        first_day = date(*[int(p) for p in (ev["date"] + "-01-01")[:10].split("-")[:3]])
        if first_day > today:
            raise ThemeError(f"{theme_id}: evidence is dated {ev['date']}, after {today.isoformat()}")

    checked = raw.get("checked")
    checked_day = parse_day(checked) if isinstance(checked, str) and len(checked) == 10 else None
    if checked_day is None:
        raise ThemeError(f"{theme_id}: checked must be the YYYY-MM-DD the status was last confirmed")
    if checked_day > today:
        raise ThemeError(f"{theme_id}: checked {checked} is after {today.isoformat()}")
    if checked_day < first_day:
        raise ThemeError(f"{theme_id}: checked {checked} is before the evidence date {ev['date'] if accessed is None else accessed}")

    also_raw = raw.get("also") or []
    if not isinstance(also_raw, list) or len(also_raw) > MAX_ALSO:
        raise ThemeError(f"{theme_id}: also must be a list of at most {MAX_ALSO} entries")

    fiction = check_fiction(theme_id, raw.get("fiction"), "fiction")
    also = [check_fiction(theme_id, a, f"also[{i}]") for i, a in enumerate(also_raw)]
    for a in also:
        # The headline year is the earliest appearance shown on the card.
        if a["year"] < fiction["year"]:
            raise ThemeError(f"{theme_id}: also lists {a['work']} ({a['year']}), earlier than the main entry "
                             f"({fiction['year']}); make the earliest one the main entry")
        if a["idea_id"] == fiction["idea_id"]:
            raise ThemeError(f"{theme_id}: also repeats the main entry {a['idea_id']}")

    match = raw.get("match")
    if not isinstance(match, dict):
        raise ThemeError(f"{theme_id}: match rules are missing")
    unknown = sorted(set(match) - MATCH_KEYS)
    if unknown:
        raise ThemeError(f"{theme_id}: unknown match field(s) {', '.join(unknown)}")
    for key in ("subsectors", "tags", "include", "exclude"):
        val = match.get(key, [])
        if not isinstance(val, list) or not all(isinstance(v, str) and v.strip() for v in val):
            raise ThemeError(f"{theme_id}: match.{key} must be a list of names")
    pattern = match.get("pattern")
    compiled = None
    if pattern is not None:
        if not isinstance(pattern, str) or not pattern.strip():
            raise ThemeError(f"{theme_id}: match.pattern must be a non-empty string")
        try:
            compiled = re.compile(pattern, re.I)
        except re.error as exc:
            raise ThemeError(f"{theme_id}: match.pattern does not compile ({exc})") from None
    if not (match.get("subsectors") or match.get("tags") or pattern or match.get("include")):
        raise ThemeError(f"{theme_id}: match needs at least one of subsectors, tags, pattern, include")
    clash = set(match.get("include", [])) & set(match.get("exclude", []))
    if clash:
        raise ThemeError(f"{theme_id}: {', '.join(sorted(clash))} is both included and excluded")
    featured = raw.get("featured", False)
    if not isinstance(featured, bool):
        raise ThemeError(f"{theme_id}: featured must be true or false")

    return OrderedDict([
        ("id", theme_id),
        ("title", _need_text(theme_id, "title", raw.get("title"), LIMITS["title"])),
        ("imagined", _need_text(theme_id, "imagined", raw.get("imagined"), LIMITS["imagined"])),
        ("fiction", fiction),
        ("also", also),
        ("status", status),
        ("status_label", STATUSES[status][0]),
        ("evidence", OrderedDict([("date", ev["date"])]
                                 + ([("accessed", accessed)] if accessed else [])
                                 + [
            ("publisher", _need_text(theme_id, "evidence.publisher", ev.get("publisher"), LIMITS["publisher"])),
            ("url", url),
            ("fact", _need_text(theme_id, "evidence.fact", ev.get("fact"), LIMITS["fact"])),
        ])),
        ("gap", _need_text(theme_id, "gap", raw.get("gap"), LIMITS["gap"])),
        ("checked", checked),
        ("featured", featured),
        ("_match", {
            "subsectors": [s.strip() for s in match.get("subsectors", [])],
            "tags": [t.strip().lower() for t in match.get("tags", [])],
            "pattern": compiled,
            "wide": bool(match.get("wide", False)),
            "include": [n.strip() for n in match.get("include", [])],
            "exclude": [n.strip() for n in match.get("exclude", [])],
        }),
    ])


def load_themes(root: Path, today: date):
    path = root / INPUTS["themes"]
    if not path.is_file():
        raise FileNotFoundError(f"{INPUTS['themes']} not found under {root}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ThemeError(f"{INPUTS['themes']} is not valid JSON ({exc})") from None
    raw_themes = doc.get("themes") if isinstance(doc, dict) else None
    if not isinstance(raw_themes, list) or not raw_themes:
        raise ThemeError(f"{INPUTS['themes']} must hold a non-empty themes list")
    themes, seen_ids, seen_titles = [], set(), set()
    for raw in raw_themes:
        t = check_theme(raw, today)
        if t["id"] in seen_ids:
            raise ThemeError(f"{t['id']}: the id is used twice")
        if t["title"].lower() in seen_titles:
            raise ThemeError(f"{t['id']}: the title {t['title']!r} is used twice")
        seen_ids.add(t["id"])
        seen_titles.add(t["title"].lower())
        themes.append(t)
    if sum(1 for t in themes if t["featured"]) > 1:
        raise ThemeError("only one theme can be featured")
    return themes


# ═══ matching companies ══════════════════════════════════════════════════

def company_text(company, wide: bool) -> str:
    parts = [company["name"], company["subsector"], " ; ".join(company["tags"]), company["techApproach"]]
    if wide:
        parts.append(company["description"])
    return " | ".join(p for p in parts if p)


def is_live(company) -> bool:
    return company["status"] not in DEAD_STATUSES


def match_theme(theme, companies, by_name):
    """The theme's companies (live only), plus the warnings a person should look at."""
    rules = theme["_match"]
    warnings = []
    chosen = OrderedDict()
    subsectors = set(rules["subsectors"])
    tags = set(rules["tags"])
    for c in companies:
        if not is_live(c):
            continue
        hit = (c["subsector"] in subsectors
               or any(tag.lower() in tags for tag in c["tags"])
               or (rules["pattern"] is not None and rules["pattern"].search(company_text(c, rules["wide"]))))
        if hit:
            chosen[c["name"]] = c
    for name in rules["exclude"]:
        if name not in by_name:
            warnings.append(f"{theme['id']}: exclude names {name!r}, which is not in data.js")
        chosen.pop(name, None)
    for name in rules["include"]:
        c = by_name.get(name)
        if c is None:
            warnings.append(f"{theme['id']}: include names {name!r}, which is not in data.js")
            continue
        if not is_live(c):
            warnings.append(f"{theme['id']}: include names {name!r}, whose status is {c['status']!r}")
            continue
        chosen[name] = c
    if not chosen:
        warnings.append(f"{theme['id']}: no company in the database matches")
    ordered = sorted(chosen.values(), key=lambda c: (-raised_usd(c["totalRaised"]), c["name"].lower(), c["name"]))
    return ordered, warnings


# ═══ the build ═══════════════════════════════════════════════════════════

def build(root: Path, today: date):
    """Return (payload, method_text, warnings). Raises ThemeError for a bad theme file."""
    themes = load_themes(root, today)
    companies, data_updated = load_companies(root)
    by_name = {c["name"]: c for c in companies}

    warnings = []
    out_themes = []
    by_company = OrderedDict()
    unique = set()
    for t in sorted(themes, key=lambda t: (t["fiction"]["year"], t["title"].lower())):
        matched, warn = match_theme(t, companies, by_name)
        warnings.extend(warn)
        rows = []
        for c in matched:
            slug = company_slug(c["name"])
            rows.append(OrderedDict([("n", c["name"]), ("s", slug), ("sec", c["sector"]),
                                     ("st", c["fundingStage"]), ("r", c["totalRaised"])]))
            unique.add(c["name"])
            by_company.setdefault(slug, []).append(t["id"])
        sectors = Counter(c["sector"] for c in matched if c["sector"])
        theme_out = OrderedDict((k, v) for k, v in t.items() if not k.startswith("_"))
        theme_out["sectors"] = OrderedDict(sorted(sectors.items(), key=lambda kv: (-kv[1], kv[0])))
        theme_out["count"] = len(rows)
        theme_out["companies"] = rows
        out_themes.append(theme_out)

    by_status = OrderedDict((key, sum(1 for t in out_themes if t["status"] == key)) for key in STATUSES)
    payload = OrderedDict([
        ("meta", OrderedDict([
            ("method_version", METHOD_VERSION),
            ("data_updated", data_updated),
            ("checked", max(t["checked"] for t in out_themes)),
            ("themes", len(out_themes)),
            ("companies", len(unique)),
            ("by_status", by_status),
            ("oldest_year", min(t["fiction"]["year"] for t in out_themes)),
            ("idea_bank", OrderedDict([("name", IDEA_BANK_NAME), ("url", IDEA_BANK_URL),
                                       ("note", FICTION_SOURCE_NOTE)])),
        ])),
        ("statuses", [OrderedDict([("key", k), ("label", v[0]), ("definition", v[1])])
                      for k, v in STATUSES.items()]),
        ("themes", out_themes),
        ("by_company", OrderedDict(sorted(by_company.items()))),
    ])
    return payload, method_text(payload), warnings


def render_page_file(payload) -> str:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return ("// Auto-generated by scripts/build_imagined.py from data/imagined/themes.json and data.js.\n"
            "// Do not edit by hand: change the theme file and rebuild.\n"
            f"const IMAGINED = {body};\n")


def method_text(payload) -> str:
    meta = payload["meta"]
    lines = [
        "# Who's Building It: method",
        "",
        "Generated by `scripts/build_imagined.py` from its constants. Do not edit by hand.",
        "",
        f"Method version {meta['method_version']}. {meta['themes']} ideas, "
        f"{meta['companies']} companies. Statuses last checked {meta['checked']}.",
        "",
        "## What the page shows",
        "",
        "Each idea pairs one early appearance in science fiction with where the technology "
        "stands today and the companies in this database working on it. The fiction entry is "
        f"one early appearance from {IDEA_BANK_NAME} ({IDEA_BANK_URL}), not always the first. "
        + FICTION_SOURCE_NOTE,
        "",
        "## The status ladder",
        "",
    ]
    for s in payload["statuses"]:
        lines.append(f"- **{s['label']}**: {s['definition']}")
    lines += [
        "",
        "The status judges the idea as the story describes it, anywhere in the world, not the "
        "companies listed under it. Every status carries one dated fact from a primary source "
        "(an agency, a regulator, a company's own newsroom or a peer-reviewed paper) and one "
        "sentence on what is still missing. The Idea Bank is never the evidence. A status "
        "without a dated source is refused by the build, and so is a source dated after the "
        "build date. A primary page that prints no date is cited as undated, together with "
        "the day we read it.",
        "",
        "## How companies are matched",
        "",
        "Each idea has rules in `data/imagined/themes.json`: database subsectors, tags, and a "
        "pattern read against the company name, subsector, tags and technical approach "
        "(descriptions only where a rule says `wide`). The lists were then checked by hand, "
        "with corrections kept in `include` and `exclude`. Dead and acquired companies drop "
        "out. The daily sync rebuilds the lists from that day's data.js, so new companies that "
        "fit a rule appear on their own. Names in `include` or `exclude` that leave the "
        "database are reported in the build log, never guessed.",
        "",
        "Within an idea, companies are ordered by total raised, largest first, then by name.",
        "",
        "## House style",
        "",
        f"Titles, facts and gap lines are plain sentences. Length limits: "
        + ", ".join(f"{k} {v} characters" for k, v in LIMITS.items())
        + ". No em dashes.",
        "",
        "## Rebuild",
        "",
        "```",
        "python3 scripts/build_imagined.py --check    # validate the theme file",
        "python3 scripts/build_imagined.py            # write data/imagined_auto.js",
        "python3 -m unittest scripts/tests/test_imagined.py",
        "node scripts/tests/test_imagined_page.js",
        "```",
        "",
    ]
    return "\n".join(lines)


def write_if_changed(path: Path, text: str) -> bool:
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--today", help="YYYY-MM-DD; sources dated after this are refused (default: today, UTC)")
    ap.add_argument("--check", action="store_true", help="validate only; write nothing")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--show", metavar="THEME_ID", help="print one theme's companies and stop")
    ap.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    root = Path(args.root)
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else datetime.now(timezone.utc).date()
    try:
        payload, method, warnings = build(root, today)
    except (ThemeError, JSLiteralError, FileNotFoundError) as exc:
        print(f"build_imagined: {exc}", file=sys.stderr)
        return 1

    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)

    if args.show:
        theme = next((t for t in payload["themes"] if t["id"] == args.show), None)
        if theme is None:
            print(f"no theme {args.show!r}", file=sys.stderr)
            return 1
        print(f"{theme['title']}: {theme['count']} companies")
        for c in theme["companies"]:
            print(f"  {c['n']}  [{c['sec']} | {c['st']} | {c['r']}]")
        return 0

    if warnings and args.strict:
        print(f"build_imagined: {len(warnings)} warning(s) with --strict", file=sys.stderr)
        return 1

    meta = payload["meta"]
    summary = (f"{meta['themes']} idea{'s' * (meta['themes'] != 1)}, "
               f"{meta['companies']} compan{'ies' if meta['companies'] != 1 else 'y'}, "
               + ", ".join(f"{STATUSES[k][0].lower()} {v}" for k, v in meta["by_status"].items()))
    if args.check:
        print(f"ok: {summary}")
        return 0

    changed = [rel for rel, text in ((OUTPUTS["page"], render_page_file(payload)),
                                     (OUTPUTS["method"], method))
               if write_if_changed(root / rel, text)]
    print(f"{summary}. " + (f"wrote {', '.join(changed)}" if changed else "no changes"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
