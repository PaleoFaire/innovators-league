#!/usr/bin/env python3
"""
Exit Watch — pedigree matching and scoring
─────────────────────────────────────────────────────────────────────────
fetch_exit_watch.py finds new US entities filing their first Form D in a
frontier-adjacent industry. That is a firehose — roughly 30 a day. This
script turns it into a queue by asking one question of each filing:

    do we have documented reason to care about who is behind it?

Three matches, in descending order of certainty. Every one of them is a
claim about a named private individual, so each carries its evidence and
its confidence, and nothing is asserted that the record does not support.

  CONFIRMED   An officer on the filing is a founder already recorded in
              COMPANIES. We verified that person's pedigree when we added
              their last company. Them quietly filing a Form D for an
              entity we do NOT track is the strongest pre-company signal
              available anywhere, and it is fully documented.

  PROBABLE    An officer's name matches someone our database records with
              a named prior employer ("ex-SpaceX", "ex-Palantir"), AND the
              filing corroborates — frontier industry group, real capital,
              recent incorporation. Name alone is never enough.

  WATCH       No pedigree match. A new frontier-tech entity raising real
              money is still worth a look, but we say plainly that we know
              nothing about the people.

Name collisions are the main accuracy risk. "John Smith" matching a founder
in our database is not evidence of anything. Any person key that resolves to
more than one distinct individual, or that is built from a very common
surname with no corroboration, is demoted out of CONFIRMED.

Inputs : data/exit_watch_raw.json, data.js (COMPANIES)
Outputs: data/exit_watch_auto.json, data/exit_watch_auto.js (const EXIT_WATCH)

Usage:
    python scripts/build_exit_watch.py
    python scripts/build_exit_watch.py --min-score 40
"""

from __future__ import annotations

import argparse
import json
import urllib.request
import time
import gzip
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA_JS = ROOT / "data.js"
RAW = DATA / "exit_watch_raw.json"
OUT_JSON = DATA / "exit_watch_auto.json"
OUT_JS = DATA / "exit_watch_auto.js"

# Parent companies whose alumni we care about. The keys are display names;
# the values are the patterns that appear in our own founder/insight text.
PEDIGREE = {
    "SpaceX":        [r"ex-?SpaceX", r"SpaceX (?:alum|veteran|engineer)", r"former SpaceX"],
    "Palantir":      [r"ex-?Palantir", r"Palantir (?:alum|veteran)", r"former Palantir"],
    "OpenAI":        [r"ex-?OpenAI", r"OpenAI (?:alum|co-?founder)", r"former OpenAI"],
    "Anthropic":     [r"ex-?Anthropic", r"Anthropic alum", r"former Anthropic"],
    "Anduril":       [r"ex-?Anduril", r"Anduril (?:alum|mafia)", r"former Anduril"],
    "Tesla":         [r"ex-?Tesla", r"Tesla alum", r"former Tesla"],
    "DeepMind":      [r"ex-?DeepMind", r"DeepMind alum"],
    "Google":        [r"ex-?Google", r"Google alum"],
    "Apple":         [r"ex-?Apple", r"Apple alum", r"former Apple"],
    "NVIDIA":        [r"ex-?NVIDIA", r"ex-?Nvidia", r"NVIDIA alum"],
    "Meta":          [r"ex-?Meta\b", r"ex-?Facebook", r"Meta FAIR"],
    "Amazon/AWS":    [r"ex-?Amazon", r"ex-?AWS", r"AWS alum"],
    "Microsoft":     [r"ex-?Microsoft", r"Microsoft Research"],
    "Rocket Lab":    [r"ex-?Rocket Lab"],
    "Blue Origin":   [r"ex-?Blue Origin"],
    "NASA/JPL":      [r"ex-?NASA", r"NASA veteran", r"ex-?JPL", r"JPL alum"],
    "DARPA":         [r"ex-?DARPA", r"DARPA (?:veteran|program manager)"],
    "Stripe":        [r"ex-?Stripe", r"Stripe alum"],
    "Neuralink":     [r"ex-?Neuralink"],
    "Waymo":         [r"ex-?Waymo"],
}

# Surnames common enough that a first+last key match carries little weight on
# its own. Not exhaustive — a heuristic guard, backed by the collision check.
COMMON_SURNAMES = {
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller",
    "davis", "rodriguez", "martinez", "hernandez", "lopez", "gonzalez",
    "wilson", "anderson", "thomas", "taylor", "moore", "jackson", "martin",
    "lee", "perez", "thompson", "white", "harris", "clark", "lewis",
    "robinson", "walker", "young", "allen", "king", "wright", "scott",
    "chen", "wang", "li", "zhang", "liu", "yang", "kim", "park", "singh",
    "patel", "kumar", "nguyen", "tran",
    # Short, very high-frequency surnames. "Jason Ma" matching a founder in
    # our database is close to meaningless on its own.
    "ma", "wu", "xu", "yu", "he", "gao", "lin", "zhou", "sun", "guo", "luo",
    "shi", "cao", "deng", "feng", "peng", "tang", "wei", "xie", "zhu", "zheng",
    "cho", "choi", "jung", "kang", "shin", "yoon", "lim", "han", "oh", "seo",
    "das", "shah", "gupta", "rao", "reddy", "mehta", "desai", "iyer", "bose",
}

# Industry groups where a real frontier company plausibly self-classifies,
# split by how specific the choice is. "Other" tells us nothing.
INDUSTRY_WEIGHT = {
    "Other Technology": 14, "Computers": 14, "Technology": 14,
    "Biotechnology": 13, "Aerospace": 15, "Manufacturing": 12,
    "Other Energy": 12, "Energy": 12, "Electric Utilities": 12,
    "Chemicals": 10, "Materials": 10, "Mining": 8, "Metals": 8,
    "Health Care": 9, "Other Health Care": 9, "Pharmaceuticals": 9,
    "Telecommunications": 9, "Transportation": 8, "Construction": 6,
    "Environmental Services": 9, "Agriculture": 6, "Business Services": 4,
    "Other": 0,
}


def person_key(name: str) -> str:
    parts = [p for p in re.split(r"[^A-Za-z]+", name or "") if len(p) > 1]
    if len(parts) < 2:
        return ""
    return (parts[0] + parts[-1]).lower()


def surname(name: str) -> str:
    parts = [p for p in re.split(r"[^A-Za-z]+", name or "") if len(p) > 1]
    return parts[-1].lower() if parts else ""


# ───────────────────────── build the roster ─────────────────────────────

def load_companies() -> list[dict]:
    """Parse the COMPANIES array out of data.js. We only need a few fields,
    so a targeted regex beats trying to JSON-parse a 3MB JS literal."""
    text = DATA_JS.read_text(encoding="utf-8", errors="replace")
    start = text.find("const COMPANIES = [")
    if start < 0:
        return []
    chunk = text[start:]
    end = chunk.find("\n];")
    chunk = chunk[:end if end > 0 else 4_000_000]

    out = []
    for blk in re.findall(r"\{(.*?)\n  \}", chunk, re.S):
        def f(key):
            m = re.search(rf'\b{key}:\s*"((?:[^"\\]|\\.)*)"', blk)
            return (m.group(1).replace('\\"', '"') if m else "")
        name = f("name")
        if not name:
            continue
        out.append({
            "name": name,
            "founder": f("founder"),
            "sector": f("sector"),
            "insight": f("insight"),
            "description": f("description"),
            "website": f("website"),
        })
    return out


def split_founders(raw: str) -> list[str]:
    """Founder fields are free text: 'Palmer Luckey, Trae Stephens',
    'Dr. Jane Doe (ex-SpaceX)', 'Founded by X and Y'."""
    if not raw:
        return []
    s = re.sub(r"\((.*?)\)", " ", raw)                 # drop parentheticals
    s = re.sub(r"\b(founded by|co-?founders?|founders?|ceo|cto|dr\.?|prof\.?)\b",
               " ", s, flags=re.I)
    parts = re.split(r",| and | & |;|/|\|", s)
    names = []
    for p in parts:
        p = re.sub(r"[^A-Za-z.\-' ]", " ", p).strip()
        p = re.sub(r"\s+", " ", p)
        # "Team of former SpaceX engineers", "Former SpaceX propulsion team" and
        # friends are descriptions, not people. They must never enter the roster
        # or they will name-match nothing and clutter the evidence panel.
        if re.search(r"\b(team|engineers?|employees?|staff|group|alumni|"
                     r"veterans?|founders?|unknown|undisclosed|stealth)\b", p, re.I):
            continue
        # "Former Meta", "Former Waymo" — an employer, not a person.
        if re.match(r"^(former|ex|early|founding)\b", p, re.I):
            continue
        if len(p.split()) >= 2 and len(p) <= 48:
            names.append(p)
    return names


def load_founder_mafias() -> dict:
    """Parse the curated FOUNDER_MAFIAS object out of data.js.

    This is the single best pedigree source we own, and the first version of
    this script ignored it entirely — it only grepped COMPANIES for the literal
    string "ex-SpaceX". FOUNDER_MAFIAS is hand-curated and names people
    directly, with their role at the parent:

        "SpaceX Mafia": companies: [
            { company: "Impulse Space",
              founders: "Tom Mueller (Founding Employee, VP Propulsion)" }, ...

    Returns {mafia_label: [(company, founders_string), ...]}.
    """
    try:
        text = DATA_JS.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    i = text.find("const FOUNDER_MAFIAS")
    if i < 0:
        return {}
    chunk = text[i:i + 200_000]
    end = chunk.find("\n};")
    chunk = chunk[:end if end > 0 else len(chunk)]

    out: dict[str, list] = {}
    # Each mafia is  "Name Mafia": { ... companies: [ {...}, {...} ] }
    for m in re.finditer(r'"([^"]+?Mafia|[^"]*?(?:Alumni|Spinouts|Fellows|Combinator)[^"]*?)"\s*:\s*\{(.*?)\n  \}',
                         chunk, re.S):
        label, body = m.group(1), m.group(2)
        pairs = []
        for cm in re.finditer(r'\{\s*company:\s*"([^"]*)"\s*,\s*founders:\s*"([^"]*)"', body):
            pairs.append((cm.group(1), cm.group(2)))
        if pairs:
            out[label] = pairs
    return out


def load_mafia_clusters() -> dict:
    """founder_mafias_auto.json clusters COMPANIES by mafia heritage. Every
    founder of a clustered company inherits that pedigree — which multiplies
    the roster well beyond the handful of people named explicitly."""
    p = DATA / "founder_mafias_auto.json"
    if not p.exists():
        return {}
    try:
        rows = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    out = {}
    for r in rows if isinstance(rows, list) else []:
        label = r.get("mafia")
        if not label:
            continue
        out[label] = [c.get("company") for c in r.get("companies", []) if c.get("company")]
    return out


def tidy_mafia(label: str) -> str:
    """'SpaceX Mafia' -> 'SpaceX'."""
    return re.sub(r"\s+(Mafia|Alumni|Spinouts)$", "", label).strip()


def build_roster(companies: list[dict]) -> tuple[dict, set]:
    """person_key -> record. Also returns the collision set so we can demote
    any key that resolves to more than one human.

    Pedigree comes from three sources, best first:
      1. FOUNDER_MAFIAS — curated, names the person and their role
      2. founder_mafias_auto.json — clusters companies; founders inherit
      3. free-text "ex-SpaceX" mentions in founder/insight/description
    """
    roster: dict[str, dict] = {}
    seen_names: dict[str, set] = defaultdict(set)
    by_company = {c["name"]: c for c in companies}

    def add(fname: str, company: str, employer: str | None, evidence: str | None):
        k = person_key(fname)
        if not k:
            return
        seen_names[k].add(fname.lower().strip())
        rec = roster.setdefault(k, {
            "name": fname.strip(), "companies": [], "employers": [], "evidence": [],
        })
        if company and company not in rec["companies"]:
            rec["companies"].append(company)
        if employer and employer not in rec["employers"]:
            rec["employers"].append(employer)
            if evidence:
                rec["evidence"].append(evidence)

    # ── 1. the curated roster ────────────────────────────────────────────
    for label, pairs in load_founder_mafias().items():
        emp = tidy_mafia(label)
        for company, founders_str in pairs:
            role = ""
            rm = re.search(r"\(([^)]*)\)", founders_str)
            if rm:
                role = rm.group(1)
            for fname in split_founders(founders_str):
                add(fname, company,
                    emp,
                    f'FOUNDER_MAFIAS records {fname.strip()} at {company} as '
                    f'{emp}{" — " + role if role else ""}')

    # ── 2. clustered companies: founders inherit the pedigree ────────────
    for label, comp_names in load_mafia_clusters().items():
        emp = tidy_mafia(label)
        for cname in comp_names:
            c = by_company.get(cname)
            if not c:
                continue
            for fname in split_founders(c["founder"]):
                add(fname, cname, emp,
                    f'{cname} is clustered under {label} in our database')

    # ── 2b. patent inventor records, when the key is present ─────────────
    # build_alumni_roster.py turns granted patents into documented employment:
    # a named inventor on a patent assigned to Palantir demonstrably worked
    # there, and the patent number is the citation. This is the source that
    # takes the roster from hundreds to thousands. Absent without the key.
    ap = DATA / "alumni_roster.json"
    if ap.exists():
        try:
            blob = json.loads(ap.read_text())
        except (json.JSONDecodeError, OSError):
            blob = {}
        for k, rec in (blob.get("people") or {}).items():
            name = rec.get("name", "")
            for emp in rec.get("employers", []):
                add(name, "", emp,
                    (rec.get("evidence") or [f"patent inventor record at {emp}"])[0])

    # ── 3. free-text pedigree, and every founder we know ─────────────────
    for c in companies:
        blob = " ".join((c["founder"], c["insight"], c["description"]))
        employers = [emp for emp, pats in PEDIGREE.items()
                     if any(re.search(p, blob, re.I) for p in pats)]
        for fname in split_founders(c["founder"]):
            if not employers:
                add(fname, c["name"], None, None)
            for e in employers:
                add(fname, c["name"], e,
                    f'"{e}" pedigree recorded on {c["name"]} in our database')

    collisions = {k for k, v in seen_names.items() if len(v) > 1}
    return roster, collisions


# ─────────────────────────────── scoring ────────────────────────────────

LEGAL_SUFFIX = {"inc", "incorporated", "llc", "ltd", "limited", "corp",
                "corporation", "co", "company", "lp", "llp", "plc", "sa", "gmbh"}


def name_tokens(s: str) -> set[str]:
    """Distinctive words in a company name, legal furniture removed."""
    junk = {"inc", "llc", "corp", "corporation", "co", "company", "ltd",
            "limited", "lp", "llp", "plc", "holdings", "holding", "group",
            "technologies", "technology", "labs", "lab", "industries",
            "systems", "international", "the", "and", "of"}
    return {w for w in re.split(r"[^a-z0-9]+", (s or "").lower())
            if len(w) > 2 and w not in junk}


def is_same_company(entity: str, tracked_name: str) -> bool:
    """Is this filing simply a company we already track, raising money?

    Form D issuers use their full legal name — 'Pixxel Space Technologies,
    Inc.' — while our database holds the trading name, 'Pixxel'. Stem
    equality misses that, and the miss is expensive: it surfaces a tracked
    company's funding round as a brand-new formation, which is the single
    most embarrassing thing this tool could do. So we test containment of
    the distinctive tokens in both directions.
    """
    a, b = name_tokens(entity), name_tokens(tracked_name)
    if not a or not b:
        return False
    if a.issubset(b) or b.issubset(a):
        return True

    # Acronyms. "Amca" in our database is "Advanced Manufacturing Co of
    # America" on the filing — no shared token, but the same company. Caught
    # in testing when a $244M raise was ranked a Strong lead as a brand-new
    # formation. Build initials from the entity's own words, including the
    # legal furniture, because acronyms usually swallow it.
    SKIP = {"of", "and", "the", "for", "a", "an", "de", "at", "in", "on"}

    def initial_forms(s):
        """An acronym may or may not swallow the little words and the legal
        suffix, so generate every plausible reading and try them all.
        'Advanced Manufacturing Co of America, Inc.' yields amcoai, amcai,
        amcoa and amca — the last of which is how the company writes it."""
        words = [w for w in re.split(r"[^A-Za-z]+", (s or "")) if w]
        if not words:
            return set()
        keep = [w for w in words if w.lower() not in SKIP]
        forms = set()
        for base in (words, keep):
            if not base:
                continue
            init = "".join(w[0] for w in base).lower()
            forms.add(init)
            if base[-1].lower() in LEGAL_SUFFIX and len(base) > 1:
                forms.add(init[:-1])
        return forms

    for src, toks in ((entity, b), (tracked_name, a)):
        for form in initial_forms(src):
            for tok in toks:
                if len(tok) >= 3 and form.startswith(tok):
                    return True

    # Near-identical spellings. 'AiGent' and 'AGent Energy' differ by one
    # character; a company that respells itself between our record and its
    # filing is still the same company, and calling it a brand-new formation
    # would be the most embarrassing possible error.
    def edit1(x, y):
        """True when x and y are within one insertion, deletion or
        substitution of each other."""
        if x == y:
            return True
        if abs(len(x) - len(y)) > 1:
            return False
        if len(x) == len(y):
            return sum(1 for p, q in zip(x, y) if p != q) == 1
        if len(x) > len(y):
            x, y = y, x                       # y is now exactly one longer
        i = 0
        while i < len(x) and x[i] == y[i]:
            i += 1
        return x[i:] == y[i + 1:]

    for ta in a:
        for tb in b:
            if len(ta) >= 5 and len(tb) >= 5 and edit1(ta, tb):
                return True
    return False


# ── First-filing verification ───────────────────────────────────────────────
# The decisive test of "is this a new company", and the only one that is
# ground truth rather than inference.
#
# yearOfInc is typed by the filer and is routinely wrong — Payward, Inc.
# (Kraken, a 2011 company) declared itself incorporated in 2026 on a $354M
# raise. CIK is better, because the SEC issues it and never reissues it, but
# it is still only a proxy for a date.
#
# EDGAR's submissions API just tells us the answer: every filing the entity
# has ever made. An entity raising its third round has three Form Ds on file.
# Lone Gull Holdings, Ltd. looked like our strongest hit of the entire sweep
# — two Panthalassa co-founders, $94.1M, "incorporated 2026" — and its filing
# history reads 2022, 2024, 2026. It is a company raising a later round, not
# a founding. One HTTP request per shortlisted row settles it, so we spend it.
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{:010d}.json"


def prior_form_d_count(cik: int, this_accession: str, cache: dict) -> int | None:
    """Form Ds this entity filed *before* the one we are looking at.
    None means EDGAR could not be reached — never treat that as 'it is new'."""
    key = str(cik)
    if key in cache:
        hist = cache[key]
    else:
        try:
            req = urllib.request.Request(
                SUBMISSIONS.format(cik),
                headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            js = json.loads(raw.decode("utf-8", "replace"))
            rec = js.get("filings", {}).get("recent", {})
            hist = {
                "former_names": [f.get("name") for f in js.get("formerNames") or []],
                "filings": [
                    {"form": f, "date": d, "accession": a}
                    for f, d, a in zip(rec.get("form", []),
                                       rec.get("filingDate", []),
                                       rec.get("accessionNumber", []))
                ],
            }
            cache[key] = hist
        except Exception:
            return None
        time.sleep(0.12)

    norm = (this_accession or "").replace("-", "")
    prior = 0
    for f in hist["filings"]:
        if not str(f["form"]).startswith("D"):
            continue
        if str(f["accession"]).replace("-", "") == norm:
            continue
        prior += 1
    return prior


def verify_shortlist(rows: list[dict], cache: dict) -> tuple[list[dict], list[dict]]:
    """Split the shortlist into genuine first-time registrants and the rest."""
    keep, rejected = [], []
    for r in rows:
        cik = int(r.get("cik") or 0)
        if not cik:
            keep.append(r)
            continue
        n = prior_form_d_count(cik, r.get("accession", ""), cache)
        if n is None:
            r["reasons"] = list(r.get("reasons", [])) + [
                "EDGAR filing history could not be checked — verify by hand "
                "that this is a first raise"]
            keep.append(r)
        elif n > 0:
            r["confidence"] = "Known company"
            r["score"] = 0
            r["reasons"] = [
                f"EDGAR shows {n} earlier Form D filing"
                f"{'s' if n != 1 else ''} by this entity, so it is an existing "
                f"company raising another round, not a new formation"]
            rejected.append(r)
        else:
            r["reasons"] = list(r.get("reasons", [])) + [
                "EDGAR shows no earlier Form D from this entity — this is its "
                "first disclosed raise"]
            keep.append(r)
    return keep, rejected

UA = "Rational Optimist Society stephen@rationaloptimistsociety.com"

CIK_NEW_FLOOR = 1_900_000


def score_candidate(cand: dict, roster: dict, collisions: set,
                    sector_of: dict) -> dict:
    """Return the candidate annotated with matches, score and lead strength."""
    matches = []
    for p in cand.get("persons", []):
        k = p.get("key") or person_key(p.get("name", ""))
        if not k or k not in roster:
            continue
        r = roster[k]
        weak = k in collisions or surname(p.get("name", "")) in COMMON_SURNAMES
        matches.append({
            "person": p.get("name"),
            "roles": p.get("roles", []),
            "known_for": r["companies"][:3],
            "employers": r["employers"],
            "evidence": r["evidence"][:3],
            "name_ambiguous": weak,
        })

    # ── Has the SEC known this entity for years? Kill it here. ───────────
    # yearOfInc is typed in by the filer and is routinely wrong: Payward, Inc.
    # — Kraken, a 2011 company — filed a 2026 Form D declaring itself
    # incorporated in 2026, and sailed through the age filter on a $354M
    # raise. The CIK cannot lie in that direction. The SEC assigns it at an
    # entity's first registration and never reissues it, so a low CIK is
    # positive proof the entity predates the window no matter what the filer
    # typed. Calibrated against this corpus: entities reporting a 2023-or-
    # later incorporation sit at a median CIK near 2,090,000, with a 10th
    # percentile of 1,983,000. Below 1,900,000 the entity registered with the
    # SEC before roughly 2022.
    cik = int(cand.get("cik") or 0)
    if 0 < cik < CIK_NEW_FLOOR:
        out = dict(cand)
        out["matches"] = matches
        out["score"] = 0
        out["confidence"] = "Known company"
        out["reasons"] = [f"SEC CIK {cik:,} was issued years before this "
                          f"filing, so the entity is not a new formation "
                          f"whatever its stated year of incorporation"]
        return out

    # ── Is this just a tracked company raising? Kill it here. ────────────
    for m in matches:
        for known in m["known_for"]:
            if is_same_company(cand.get("entity", ""), known):
                out = dict(cand)
                out["matches"] = matches
                out["score"] = 0
                out["confidence"] = "Known company"
                out["reasons"] = [f"This is {known} raising capital, not a new "
                                  f"formation — already tracked in COMPANIES"]
                return out

    score = 0
    reasons = []

    strong = [m for m in matches if not m["name_ambiguous"]]
    weak = [m for m in matches if m["name_ambiguous"]]

    # Sector adjacency is the corroboration that separates a real lead from a
    # coincidence of names. A founder of a construction-robotics company
    # turning up on a telehealth filing is far more likely to be a different
    # person of the same name than a genuine pivot.
    adjacent = False
    ind = (cand.get("industry") or "").strip()
    IND_TO_SECTOR = {
        "Aerospace": {"space", "defense", "aerospace"},
        "Other Energy": {"energy", "nuclear", "climate", "power"},
        "Energy": {"energy", "nuclear", "climate", "power"},
        "Electric Utilities": {"energy", "power", "grid"},
        "Biotechnology": {"bio", "health", "medical", "life"},
        "Pharmaceuticals": {"bio", "health", "medical"},
        "Health Care": {"health", "medical", "bio"},
        "Other Health Care": {"health", "medical", "bio"},
        "Manufacturing": {"manufactur", "robot", "industrial", "materials"},
        "Materials": {"materials", "manufactur"},
        "Chemicals": {"materials", "chemical", "climate"},
        "Computers": {"semiconductor", "compute", "chip"},
        "Transportation": {"mobility", "transport", "auto"},
        # "Other Technology" and "Technology" are deliberately absent. They are
        # catch-all self-classifications covering everything from telehealth to
        # rockets, so they cannot corroborate anything. Treating them as
        # adjacency was ranking a telehealth filing as a robotics founder's
        # next company purely because both fall under "technology".
    }
    want = IND_TO_SECTOR.get(ind, set())
    if want:
        for m in matches:
            for known in m["known_for"]:
                sec = (sector_of.get(known) or "").lower()
                if any(w in sec for w in want):
                    adjacent = True
                    break

    if strong:
        who = strong[0]["person"]
        built = strong[0]["known_for"][0] if strong[0]["known_for"] else "a tracked company"
        if adjacent:
            score += 45
            reasons.append(f"An officer named {who} matches the founder of {built} "
                           f"in our database, and the sector lines up")
        else:
            score += 26
            reasons.append(f"An officer named {who} matches the founder of {built} "
                           f"in our database — but the sectors do not line up, "
                           f"so this may be a different person of the same name")
        if len(strong) > 1:
            score += 8
            reasons.append(f"{len(strong)} names on this filing match founders we track")
    elif weak:
        score += 10
        reasons.append(f"Name match on {weak[0]['person']}, but that name is common "
                       f"or ambiguous in our data — verify before acting")

    employers = sorted({e for m in matches for e in m["employers"]})
    if employers:
        # This is the entire point of the tool. A documented mafia pedigree
        # outweighs every other signal on the row.
        score += 40
        who = matches[0]["person"] if matches else "an officer"
        reasons.insert(0, f"{who} carries a documented {', '.join(employers[:3])} "
                          f"pedigree in our database")

    ind = (cand.get("industry") or "").strip()
    w = INDUSTRY_WEIGHT.get(ind, 0)
    score += w
    if w >= 12:
        reasons.append(f"self-classified as {ind}")

    amt = cand.get("amount_sold") or 0
    if amt >= 25_000_000:
        score += 18; reasons.append(f"${amt/1e6:.0f}M already sold")
    elif amt >= 5_000_000:
        score += 14; reasons.append(f"${amt/1e6:.1f}M already sold")
    elif amt >= 1_000_000:
        score += 9;  reasons.append(f"${amt/1e6:.1f}M already sold")
    elif amt > 0:
        score += 4

    yr = cand.get("year_inc")
    this_year = datetime.now(timezone.utc).year
    if yr:
        age = this_year - yr
        if age <= 0:
            score += 12; reasons.append(f"incorporated this year")
        elif age == 1:
            score += 8;  reasons.append(f"incorporated {yr}")
        elif age == 2:
            score += 4

    n_officers = len(cand.get("persons", []))
    if 2 <= n_officers <= 6:
        score += 3

    # These tiers describe how strong a LEAD is, not what is true. A name in
    # a Form D matching a name in our database is a hypothesis. The filing is
    # linked on every row so it can be checked in one click, and no row ever
    # asserts that a named private individual did anything.
    # Tiers name what the evidence actually is, because "Strong lead" told the
    # reader a score was high without telling them why. The product is
    # companies founded by people out of SpaceX, Palantir, Anduril and their
    # peers; a bare surname collision is a different and much weaker thing,
    # and the two should never sit under one label.
    pedigreed = [m for m in matches if m["employers"]]
    if pedigreed:
        confidence = ("Mafia founding" if any(not m["name_ambiguous"] for m in pedigreed)
                      else "Possible mafia founding")
    elif strong or weak:
        confidence = "Founder's next company"
    else:
        confidence = "New formation"

    if confidence == "Founder's next company" and not adjacent and not strong:
        reasons.append("Nothing beyond the name lines up — treat as a weak lead")

    out = dict(cand)
    out["matches"] = matches
    out["score"] = min(100, score)
    out["confidence"] = confidence
    out["reasons"] = reasons
    return out


# ──────────────────────────────── output ────────────────────────────────

def js_escape(s: str) -> str:
    return (str(s).replace("\\", "\\\\").replace('"', '\\"')
            .replace("\n", " ").replace("\r", " ").replace(" ", " ")
            .replace(" ", " "))


def write_js(rows: list[dict], meta: dict) -> None:
    lines = ["// Generated by scripts/build_exit_watch.py — do not edit by hand",
             f"// {meta['generated_at']}",
             "const EXIT_WATCH_META = " + json.dumps(meta) + ";",
             "const EXIT_WATCH = ["]
    for r in rows:
        lines.append("  {")
        lines.append(f'    entity: "{js_escape(r["entity"])}",')
        lines.append(f'    industry: "{js_escape(r.get("industry",""))}",')
        lines.append(f'    state: "{js_escape(r.get("state",""))}",')
        lines.append(f'    yearInc: {r.get("year_inc") or "null"},')
        lines.append(f'    amountSold: {r.get("amount_sold") if r.get("amount_sold") else "null"},')
        lines.append(f'    firstSale: "{js_escape(r.get("first_sale",""))}",')
        lines.append(f'    filed: "{js_escape(r.get("filed",""))}",')
        lines.append(f'    score: {r["score"]},')
        lines.append(f'    confidence: "{r["confidence"]}",')
        lines.append(f'    url: "{js_escape(r.get("url",""))}",')
        lines.append(f'    filingUrl: "{js_escape(r.get("filing_url",""))}",')
        lines.append("    people: " + json.dumps(
            [{"name": p.get("name"), "roles": p.get("roles", [])}
             for p in r.get("persons", [])]) + ",")
        lines.append("    matches: " + json.dumps(r.get("matches", [])) + ",")
        lines.append("    reasons: " + json.dumps(r.get("reasons", [])) + ",")
        lines.append("  },")
    lines.append("];")
    OUT_JS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-score", type=int, default=25)
    ap.add_argument("--include-unmatched", action="store_true",
                    help="also publish new formations with no pedigree match. "
                         "Off by default: they were 282 of 291 rows on the first "
                         "run and are indistinguishable from noise.")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    print("=" * 72)
    print("Exit Watch — pedigree matching and scoring")
    print("=" * 72)

    if not RAW.exists():
        print(f"missing {RAW.relative_to(ROOT)} — run fetch_exit_watch.py first")
        return 1

    raw = json.loads(RAW.read_text())
    cands = raw.get("candidates", [])
    companies = load_companies()
    roster, collisions = build_roster(companies)

    with_ped = sum(1 for r in roster.values() if r["employers"])
    print(f"companies parsed:     {len(companies)}")
    print(f"founders in roster:   {len(roster)}")
    print(f"  with a documented prior employer: {with_ped}")
    print(f"  ambiguous name keys (demoted):    {len(collisions)}")
    print(f"candidate filings:    {len(cands)}")

    sector_of = {c["name"]: c.get("sector", "") for c in companies}

    all_scored = [score_candidate(c, roster, collisions, sector_of) for c in cands]
    known = [s for s in all_scored if s["confidence"] == "Known company"]
    scored = [s for s in all_scored
              if s["confidence"] != "Known company" and s["score"] >= args.min_score
              and (args.include_unmatched or s.get("matches"))]
    scored.sort(key=lambda r: (-r["score"], r.get("first_sale") or ""))

    # Ask EDGAR whether each shortlisted entity has ever filed before. This is
    # the check that separates a founding from a Series B, and it is worth one
    # request per row precisely because the shortlist is short.
    vcache_path = DATA / ".exit_watch_history.json"
    vcache = {}
    if vcache_path.exists():
        try:
            vcache = json.loads(vcache_path.read_text())
        except Exception:
            vcache = {}
    if scored:
        print(f"\nverifying first-filing status for {len(scored)} shortlisted entities...")
        scored, repeats = verify_shortlist(scored, vcache)
        vcache_path.write_text(json.dumps(vcache), encoding="utf-8")
        if repeats:
            print(f"dropped {len(repeats)} that had filed with the SEC before:")
            for r in repeats:
                print(f"  {r['entity'][:44]:46} {r['reasons'][0][:66]}")
            known.extend(repeats)

    tiers = defaultdict(int)
    for s in scored:
        tiers[s["confidence"]] += 1

    if known:
        print(f"\nsuppressed as tracked companies raising, not new formations: {len(known)}")
        for k in known[:5]:
            print(f"  {k['entity'][:46]:48} {k['reasons'][0][:60]}")

    print(f"\nabove score {args.min_score}: {len(scored)}")
    for t in ("Mafia founding", "Possible mafia founding",
              "Founder's next company", "New formation"):
        if tiers[t]:
            print(f"  {t:14} {tiers[t]}")

    print("\ntop of the queue:")
    for s in scored[:10]:
        amt = f"${s['amount_sold']/1e6:.1f}M" if s.get("amount_sold") else "—"
        print(f"  [{s['score']:3d}] {s['confidence']:9} {s['entity'][:40]:42} "
              f"{s.get('industry','')[:18]:20} {amt:>8}")
        if s["reasons"]:
            print(f"        {s['reasons'][0][:100]}")

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": raw.get("window_days"),
        "filings_scanned": raw.get("filings_scanned"),
        "candidates_considered": len(cands),
        "published": len(scored),
        "roster_size": len(roster),
        "roster_with_pedigree": with_ped,
        "method": ("SEC Form D formations, filtered to new frontier-adjacent US "
                   "entities, matched against founders already documented in "
                   "COMPANIES. Confidence tiers reflect what the public record "
                   "supports, not what is plausible."),
    }

    if args.dry:
        print("\n--dry: nothing written")
        return 0

    OUT_JSON.write_text(json.dumps({"meta": meta, "rows": scored}, indent=2),
                        encoding="utf-8")
    write_js(scored, meta)
    print(f"\nwrote {OUT_JSON.relative_to(ROOT)} and {OUT_JS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
