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
        if len(p.split()) >= 2 and len(p) <= 48:
            names.append(p)
    return names


def build_roster(companies: list[dict]) -> tuple[dict, dict]:
    """person_key -> record. Also returns the collision map so we can demote
    any key that resolves to more than one human."""
    roster: dict[str, dict] = {}
    seen_names: dict[str, set] = defaultdict(set)

    for c in companies:
        blob = " ".join((c["founder"], c["insight"], c["description"]))
        employers = [emp for emp, pats in PEDIGREE.items()
                     if any(re.search(p, blob, re.I) for p in pats)]

        for fname in split_founders(c["founder"]):
            k = person_key(fname)
            if not k:
                continue
            seen_names[k].add(fname.lower().strip())
            rec = roster.setdefault(k, {
                "name": fname.strip(),
                "companies": [],
                "employers": [],
                "evidence": [],
            })
            if c["name"] not in rec["companies"]:
                rec["companies"].append(c["name"])
            for e in employers:
                if e not in rec["employers"]:
                    rec["employers"].append(e)
                    rec["evidence"].append(
                        f'"{e}" pedigree recorded on {c["name"]} in our database')

    collisions = {k for k, v in seen_names.items() if len(v) > 1}
    return roster, collisions


# ─────────────────────────────── scoring ────────────────────────────────

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
    return a.issubset(b) or b.issubset(a)


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
        score += 12
        reasons.append("documented pedigree: " + ", ".join(employers[:4]))

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
    if strong and adjacent:
        confidence = "Strong lead"
    elif strong or weak:
        confidence = "Lead"
    else:
        confidence = "New formation"

    if confidence == "Strong lead" and w == 0 and amt < 250_000:
        confidence = "Lead"
        reasons.append("Industry group is 'Other' and little capital disclosed, "
                       "so the corroboration is thin")

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
              if s["confidence"] != "Known company" and s["score"] >= args.min_score]
    scored.sort(key=lambda r: (-r["score"], r.get("first_sale") or ""))

    tiers = defaultdict(int)
    for s in scored:
        tiers[s["confidence"]] += 1

    if known:
        print(f"\nsuppressed as tracked companies raising, not new formations: {len(known)}")
        for k in known[:5]:
            print(f"  {k['entity'][:46]:48} {k['reasons'][0][:60]}")

    print(f"\nabove score {args.min_score}: {len(scored)}")
    for t in ("Strong lead", "Lead", "New formation"):
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
