#!/usr/bin/env python3
"""
Founder-Mafia Watcher
─────────────────────────────────────────────────────────────────────────
Finds new companies founded by alumni of the places that produce frontier
hardware founders — SpaceX above all.

Why this source is different
────────────────────────────
Every other feed we run is triggered by an EVENT: a round announced, a Form D
filed, a contract awarded. Those all fire after the company is already visible.
Provenance fires earlier, because the press writes "two SpaceX alumni are
betting on solar" the moment a company steps out of stealth — often before
there is a round to report at all.

That is not a hypothetical. Ambrosia Energy came to us via a TechCrunch piece
headlined exactly that way, and it was invisible to all four existing channels:
no wire release, no EDGAR CIK, not on the X watcher, and Wayback only reports
that "something changed".

The pattern is also enormous in our own data: 42 of 1,160 tracked companies
already trace a founder back to SpaceX, including Senra, Galadyne, Fortastra,
AndrenaM, Apex, Airship, Vital Lyfe and Varda.

How it works
────────────
1. Reads every configured news/press corpus we ALREADY fetch, plus a set of
   frontier-tech RSS feeds, so most of the input costs nothing extra.
2. Looks for provenance phrases ("ex-SpaceX", "former SpaceX engineer",
   "SpaceX veteran", "SpaceX alum", "spent six years at SpaceX", ...) sitting
   near founding or funding language.
3. Pulls the likely company name out of the surrounding sentence.
4. Drops anything already in COMPANIES — by name, by suffix-stem, and by
   shared founder, the same three-way check the curated-list watcher uses.

Output
──────
  data/founder_mafia_auto.json   hits with the sentence that triggered them
  data/founder_mafia_auto.js     window global for the frontend
  data/mafia_review_queue.json   new candidates awaiting review
  data/mafia_graph_auto.json     which tracked companies trace to which alma
                                 mater — the alumni graph, useful on its own

Never writes to data.js. Extraction from prose is inherently noisy, so every
hit carries the sentence that produced it and a human promotes it.

Usage
─────
  python3 scripts/fetch_founder_mafia.py
  python3 scripts/fetch_founder_mafia.py --mafia spacex
  python3 scripts/fetch_founder_mafia.py --no-fetch     # local corpora only
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
JSON_OUT = DATA_DIR / "founder_mafia_auto.json"
JS_OUT = DATA_DIR / "founder_mafia_auto.js"
QUEUE_OUT = DATA_DIR / "mafia_review_queue.json"
GRAPH_OUT = DATA_DIR / "mafia_graph_auto.json"

UA = "InnovatorsLeague-Bot/1.0 (+https://innovatorsleague.com; research)"
TIMEOUT = 20

# Alma maters worth watching, most productive first. SpaceX is the priority.
MAFIAS = {
    "spacex":   r"space\s?x",
    "anduril":  r"anduril",
    "palantir": r"palantir",
    "tesla":    r"tesla",
    "blueorigin": r"blue\s?origin",
    "waymo":    r"waymo",
    "applied":  r"applied\s+intuition",
}

# "ex-SpaceX", "former SpaceX engineer", "SpaceX veteran", "SpaceX alumni",
# "spent five years at SpaceX", "left SpaceX to", "SpaceX-founded"
def provenance_patterns(alma: str) -> list[re.Pattern]:
    a = alma
    return [re.compile(p, re.I) for p in (
        rf"\bex[-\s]{a}\b",
        rf"\bformer(?:ly)?\s+{a}\b",
        rf"\b{a}\s+(?:alum(?:ni|nus|na)?|veterans?|vets?)\b",
        rf"\b(?:worked|spent|led|engineer|engineers)\b[^.]{{0,60}}\bat\s+{a}\b",
        rf"\bleft\s+{a}\b",
        rf"\b{a}[-\s]alumni\b",
    )]

FOUNDING_CUE = re.compile(
    r"\b(founded|co-?founded|launch(?:ed|es|ing)|start(?:ed|s|up)|"
    r"emerg(?:ed|es|ing)\s+from\s+stealth|out\s+of\s+stealth|"
    r"rais(?:ed|es|ing)|new\s+(?:company|startup|venture))\b", re.I)

# Company-ish token: capitalised words, optionally with an &, digits or a suffix.
NAME = re.compile(r"\b([A-Z][A-Za-z0-9&.\-]*(?:\s+[A-Z][A-Za-z0-9&.\-]*){0,3})\b")

STOP = {
    "The","A","An","And","But","He","She","They","It","This","That","These","Those",
    "In","On","At","To","For","From","With","By","Of","As","Is","Was","Are","Were",
    "Mr","Ms","Dr","CEO","CTO","COO","Founder","Cofounder","Co","Series","Seed",
    "January","February","March","April","May","June","July","August","September",
    "October","November","December","Monday","Tuesday","Wednesday","Thursday",
    "Friday","Saturday","Sunday","SpaceX","Space","Anduril","Palantir","Tesla",
    "Blue","Origin","Waymo","Starlink","Starship","Falcon","Dragon","NASA","US",
    "U.S.","American","America","AI","But","When","While","After","Before","Now",
    "TechCrunch","Reuters","Bloomberg","Axios","Forbes","According","Read","More",
}

FRONTIER_RSS = [
    ("TechCrunch Startups", "https://techcrunch.com/category/startups/feed/"),
    ("TechCrunch Space",    "https://techcrunch.com/category/space/feed/"),
    ("Payload",             "https://payloadspace.com/feed/"),
    ("SpaceNews",           "https://spacenews.com/feed/"),
    ("Defense News Air",    "https://www.defensenews.com/arc/outboundfeeds/rss/category/air/?outputType=xml"),
    ("Axios Pro Rata",      "https://api.axios.com/feed/newsletter/axios-prorata"),
]

LOCAL_CORPORA = [
    "news_raw.json", "press_releases_raw.json", "deals_auto.json",
    "news_signals_auto.js", "funding_feed_auto.json", "product_launches_raw.json",
]


# ── known-company matching (same three-way check as the curated watcher) ──

SUFFIX = re.compile(r"(industries|technologies|systems|company|corporation|corp|inc|"
                    r"labs|lab|space|energy|aerospace|robotics|computer|ai)$")


def norm(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def stem(s):
    v = norm(s)
    for _ in range(3):
        w = SUFFIX.sub("", v)
        if len(w) >= 2 and w != v:
            v = w
        else:
            break
    return v


def person_set(s):
    out = set()
    for part in re.split(r"[,;/]| and ", s or ""):
        p = re.sub(r"\([^)]*\)", "", part).strip().lower()
        p = re.sub(r"\s+", " ", p)
        if len(p) > 6 and " " in p:
            out.add(p)
    return out


def load_companies():
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
          '+";globalThis.__n=COMPANIES.map(c=>({n:c.name,f:c.formerNames||[],p:c.founder||\'\','
          'd:(c.description||\'\')+\' \'+(c.techApproach||\'\')+\' \'+(c.insight||\'\')}));",s);'
          "console.log(JSON.stringify(s.__n));")
    return json.loads(subprocess.run(["node", "-e", js, str(DATA_JS)],
                                     capture_output=True, text=True, check=True).stdout)


# ── input gathering ──────────────────────────────────────────────────────

def strip_tags(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s or "", flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return " ".join(html.unescape(s).split())


def local_texts():
    out = []
    for fn in LOCAL_CORPORA:
        p = DATA_DIR / fn
        if not p.exists():
            continue
        raw = p.read_text(errors="ignore")
        out.append((fn, strip_tags(raw)))
    return out


def rss_texts():
    out = []
    for name, url in FRONTIER_RSS:
        try:
            r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA})
            if r.status_code == 200 and r.content:
                out.append((name, strip_tags(r.text)))
        except requests.RequestException:
            continue
    return out


# ── extraction ───────────────────────────────────────────────────────────

# Company names sit in one of two grammatical slots in these sentences:
#   "...founded Ambrosia Energy to build..."      -> object of the founding verb
#   "Fortitude Systems, launched by ex-SpaceX..." -> subject before it
# Scanning every capitalised phrase instead returns the founders, the investors
# and the first word of the headline, so we target the slots and score the rest.
FOUND_VERB = r"(?:founded|co-?founded|started|launched|created|built|set\s+up)"
OBJ = re.compile(rf"\b{FOUND_VERB}\s+(?:the\s+)?([A-Z][A-Za-z0-9&.\-]*(?:\s+[A-Z][A-Za-z0-9&.\-]*){{0,3}})")
SUBJ = re.compile(rf"\b([A-Z][A-Za-z0-9&.\-]*(?:\s+[A-Z][A-Za-z0-9&.\-]*){{0,3}}),?\s+(?:was\s+)?{FOUND_VERB}\s+by\b")

CORPORATE = re.compile(
    r"\b(systems?|energy|labs?|technologies|industries|space|aerospace|robotics|"
    r"dynamics|metals?|materials?|power|works|machines?|motors?|computing|"
    r"semiconductor|nuclear|defen[cs]e|corp|inc|ai)\b", re.I)
INVESTOR = re.compile(
    r"\b(capital|ventures?|partners|growth|fund|equity|management|holdings)\b", re.I)
# "and" between two Firstname Lastname pairs, or a trailing ", who" — people.
PERSONISH = re.compile(r"^[A-Z][a-z]+\s+[A-Z][a-z']+$")


def candidate_names(window: str, alma_regex: str) -> list[tuple[str, int]]:
    """Return [(name, confidence)] — 2 strong, 1 weak."""
    found: dict[str, int] = {}

    def offer(raw: str, conf: int):
        cand = (raw or "").strip(" .,-\u2014")
        if len(cand) < 3 or cand in STOP:
            return
        if re.search(alma_regex, cand, re.I):
            return
        if INVESTOR.search(cand):
            return
        words = cand.split()
        if words and words[0] in STOP:
            words = words[1:]
            cand = " ".join(words)
            if len(cand) < 3:
                return
        # A bare "Firstname Lastname" with no corporate token is probably the
        # founder, not the company — keep it only if a founding verb governs it.
        if PERSONISH.match(cand) and not CORPORATE.search(cand):
            conf = min(conf, 1)
        if CORPORATE.search(cand):
            conf += 1
        found[cand] = max(found.get(cand, 0), conf)

    for m in OBJ.finditer(window):
        offer(m.group(1), 2)
    for m in SUBJ.finditer(window):
        offer(m.group(1), 2)
    return sorted(((n, c) for n, c in found.items() if c >= 2),
                  key=lambda t: -t[1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mafia", choices=list(MAFIAS), help="one alma mater only")
    ap.add_argument("--no-fetch", action="store_true", help="local corpora only")
    args = ap.parse_args()

    rows = load_companies()
    exact = {norm(x) for r in rows for x in [r["n"], *r["f"]]}
    stems = {stem(x) for r in rows for x in [r["n"], *r["f"]]}
    people = {p: r["n"] for r in rows for p in person_set(r["p"])}

    # The alumni graph, from what we already hold — useful output on its own.
    graph = {}
    for key, rx in MAFIAS.items():
        hits = [r["n"] for r in rows if re.search(rx, r["p"] + " " + r["d"], re.I)]
        graph[key] = sorted(hits)
    GRAPH_OUT.write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(),
         "counts": {k: len(v) for k, v in graph.items()}, "companies": graph}, indent=2))
    print("alumni graph from tracked companies: "
          + ", ".join(f"{k}={len(v)}" for k, v in graph.items()))

    corpora = local_texts() + ([] if args.no_fetch else rss_texts())
    print(f"scanning {len(corpora)} corpora "
          f"({sum(len(t) for _, t in corpora):,} chars)")

    targets = {args.mafia: MAFIAS[args.mafia]} if args.mafia else MAFIAS
    seen_hits, hits = set(), []

    for source, text in corpora:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for key, rx in targets.items():
            pats = provenance_patterns(rx)
            for i, sent in enumerate(sentences):
                if not any(p.search(sent) for p in pats):
                    continue
                window = " ".join(sentences[max(0, i - 1): i + 2])
                if not FOUNDING_CUE.search(window):
                    continue
                for cand, conf in candidate_names(window, rx):
                    if norm(cand) in exact or stem(cand) in stems:
                        continue
                    k = (key, norm(cand))
                    if k in seen_hits:
                        continue
                    seen_hits.add(k)
                    hits.append({"company": cand, "mafia": key, "source": source,
                                 "confidence": conf, "evidence": window[:320]})

    generated = datetime.now(timezone.utc)
    payload = {"generated_at": generated.isoformat(),
               "corpora": [c for c, _ in corpora],
               "alumni_graph_counts": {k: len(v) for k, v in graph.items()},
               "hits": hits}
    JSON_OUT.write_text(json.dumps(payload, indent=2))
    JS_OUT.write_text(f"// Last updated: {generated.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                      f"window.FOUNDER_MAFIA_AUTO = {json.dumps(payload)};\n")

    queue = json.loads(QUEUE_OUT.read_text()) if QUEUE_OUT.exists() else []
    known = {norm(q.get("company", "")) for q in queue}
    added = 0
    for h in hits:
        if norm(h["company"]) in known:
            continue
        queue.append({**h, "detected_at": generated.isoformat(), "status": "pending"})
        known.add(norm(h["company"]))
        added += 1
    QUEUE_OUT.write_text(json.dumps(queue, indent=2))

    print(f"\n{len(hits)} provenance hits · {added} newly queued")
    for h in hits[:25]:
        print(f"  [{h['mafia']}] {h['company']}  (conf {h['confidence']}, {h['source']})")
        print(f"      {h['evidence'][:150]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
