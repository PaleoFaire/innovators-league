#!/usr/bin/env python3
"""
Curated-List Watcher
─────────────────────────────────────────────────────────────────────────
Diffs hand-curated frontier-tech directories against COMPANIES and reports
what we are missing.

Why this source class is worth more than another VC scraper
───────────────────────────────────────────────────────────
The VC-portfolio pipeline scores a company by how many funds list it, which
biases hard toward famous AI names — its top candidate on 2026-08-13 was
Anthropic, with Vayu Robotics and Celero buried underneath. A curated list is
the opposite: a human who shares our taste has already done the filtering, so
precision is high and the reviewer's time goes on real candidates.

Measured on the first run: buildlist.xyz had 728 companies, we already tracked
350 of them, and of the remainder 192 were genuinely in-scope and worth adding.
That is a far better hit rate than any automated feed we run.

How it works
────────────
Each source declares how to get a list of company names out of its page. Most
modern directories are Next.js apps that server-render their whole dataset into
the HTML, so a plain fetch beats a headless browser: no JS, no scrolling, no
pagination. `buildlist` parses the Next flight payload; add new sources by
writing a small extractor and registering it in SOURCES.

Matching uses a suffix-stripping stem so "Varda Space" resolves to
"Varda Space Industries" and "Helion Energy" to "Helion", and it honours
formerNames so a rename is not reported as a discovery.

Output
──────
  data/curated_lists_auto.json   full diff per source, with records
  data/curated_lists_auto.js     window global for the frontend
  data/curated_review_queue.json new in-scope candidates awaiting review

Never writes to data.js. A human promotes candidates.

Usage
─────
  python3 scripts/fetch_curated_lists.py
  python3 scripts/fetch_curated_lists.py --source buildlist
"""

from __future__ import annotations

import argparse
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
JSON_OUT = DATA_DIR / "curated_lists_auto.json"
JS_OUT = DATA_DIR / "curated_lists_auto.js"
QUEUE_OUT = DATA_DIR / "curated_review_queue.json"

UA = "InnovatorsLeague-Bot/1.0 (+https://innovatorsleague.com; research)"

# buildlist sector -> our SECTORS taxonomy. Anything not here is out of scope
# (AI App, AI Research, Fintech, Public Services, Education, Supply Chain).
SECTOR_MAP = {
    "Energy & Climate": "Climate & Energy", "Aerospace": "Space & Aerospace",
    "Defense": "Defense & Security", "Manufacturing": "Robotics & Manufacturing",
    "Robotics": "Robotics & Manufacturing", "Compute & Semiconductors": "Chips & Semiconductors",
    "Bio & Health": "Biotech & Health", "Agriculture": "Robotics & Manufacturing",
    "Construction & Housing": "Housing & Construction", "Transportation": "Transportation",
}

# Software and services that carry a hard-tech sector label on the source list.
SOFT = re.compile(
    r"(medicare|insurance|referral|paperwork|documentation|clinical document|"
    r"source-to-pay|marketplace|gpu cloud|serverless|ai cloud|penetration testing|"
    r"lab testing|drug trials with ai|generative ai agents|trades .*online|"
    r"energy retail|detects emerging risks|observability|telemetry platform)", re.I)

# Public megacaps and mega-private labs we deliberately do not track.
EXCLUDE = {
    "nvidia", "tesla", "coreweave", "cerebrassystems", "aurora", "nebius", "meta",
    "stripe", "openai", "anthropic", "canva", "deel", "rivian", "waymo", "palantir",
    "spacex", "blueorigin", "rocketlab", "databricks", "notion", "ramp", "brex",
    "mercury", "revolut", "epicgames", "rippling", "samsara", "whatnot", "xai",
    "huggingface", "midjourney", "perplexity", "scaleai", "cohere", "mistralai",
}

SUFFIX = re.compile(
    r"(industries|technologies|systems|company|corporation|corp|inc|labs|lab|"
    r"space|energy|aerospace|robotics|computer|ai)$")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def stem(s: str) -> str:
    """Strip corporate suffixes so 'CX2 Industries' and 'CX2' collapse together.

    The length guard is 2, not 4: at 4 this silently failed on exactly the
    short names it needed to catch — cx2industries -> cx2 (3) and 1xtechnologies
    -> 1x (2) were both rejected, so six merged duplicates kept reappearing as
    'new' on every run.
    """
    v = norm(s)
    for _ in range(3):
        w = SUFFIX.sub("", v)
        if len(w) >= 2 and w != v:
            v = w
        else:
            break
    return v


def person_set(s: str) -> set[str]:
    """Founder names from a free-text founder field, as lowercase full names."""
    out = set()
    for part in re.split(r"[,;/]| and ", s or ""):
        p = re.sub(r"\([^)]*\)", "", part).strip().lower()
        p = re.sub(r"\s+", " ", p)
        if len(p) > 6 and " " in p:      # needs a first and last name
            out.add(p)
    return out


def known_names() -> tuple[set[str], set[str], dict[str, str]]:
    """Returns (exact names, stems, founder -> company name).

    The founder index is the decisive duplicate signal. Suffix stemming alone
    cannot collapse 'Heirloom' onto 'Heirloom Carbon', 'STARK' onto
    'Stark Defence' or 'Regent' onto 'REGENT Craft' without an ever-growing
    list of suffix words — but all three share their full founder line with
    the record we already hold.
    """
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
          '+";globalThis.__n=COMPANIES.map(c=>({n:c.name,f:c.formerNames||[],p:c.founder||\'\'}));",s);'
          "console.log(JSON.stringify(s.__n));")
    rows = json.loads(subprocess.run(["node", "-e", js, str(DATA_JS)],
                                     capture_output=True, text=True, check=True).stdout)
    exact, stems, people = set(), set(), {}
    for r in rows:
        for label in [r["n"]] + r["f"]:
            exact.add(norm(label)); stems.add(stem(label))
        for p in person_set(r["p"]):
            people.setdefault(p, r["n"])
    return exact, stems, people


# ── source extractors ────────────────────────────────────────────────────

def extract_buildlist(html: str) -> list[dict]:
    """buildlist.xyz server-renders its full dataset into the Next flight payload."""
    t = html.replace('\\"', '"').replace("\\\\", "\\")
    out, seen = [], set()
    pat = re.compile(r'\{"name":"((?:[^"\\]|\\.)*)","slug":"([^"]*)"([\s\S]{0,1400}?)"status":"([^"]*)"')
    for m in pat.finditer(t):
        name, slug, body, status = m.group(1), m.group(2), m.group(3), m.group(4)
        if slug in seen:
            continue
        seen.add(slug)

        def f(k: str) -> str:
            r = re.search(r'"' + k + r'":"((?:[^"\\]|\\.)*)"', body)
            return r.group(1).replace("\\u0026", "&") if r else ""

        out.append({
            "name": name.replace("\\u0026", "&"), "status": status,
            "sector": f("sector"), "tagline": f("tagline"), "founders": f("founders"),
            "city": f("location_city"), "founded": f("founded_date"),
            "round": f("last_round"), "raised": re.sub(r"^\$\$", "$", f("total_raised")),
        })
    return out


SOURCES = {
    "buildlist": {"url": "https://buildlist.xyz", "extract": extract_buildlist,
                  "note": "Curated directory of companies building the future (Ryan & Christian)"},
}


def has_raise(c: dict) -> bool:
    r = (c.get("raised") or "").strip()
    return bool(r) and r.lower() != "undisclosed"


def in_scope(c: dict) -> tuple[bool, str]:
    """The quality bar. Returns (keep, reason_if_rejected).

    Derived from auditing the first 192 candidates by hand. Each rule below
    removed something that genuinely did not belong.
    """
    if c.get("sector") not in SECTOR_MAP:
        return False, "sector out of scope"
    if c.get("round") == "Public":
        return False, "public company"
    if norm(c["name"]) in EXCLUDE:
        return False, "megacap / mega-private, deliberately untracked"
    if SOFT.search(c.get("tagline") or ""):
        return False, "software or services wearing a hard-tech label"
    if not (c.get("founders") or "").strip():
        return False, "no named founders"

    # A frontier startup is venture-era. Founded pre-2015 with no disclosed
    # funding is the incumbent industrial base — real companies, but a 1902
    # sand-casting foundry does not belong next to Rangeview. Cut DW Clark
    # (1902), Cooper Steel (1960), Rampmaster (1968), Fiber Dynamics (1991).
    year = c.get("founded") or ""
    if year.isdigit() and int(year) < 2015 and not has_raise(c):
        return False, f"founded {year}, no disclosed funding — incumbent, not frontier"
    if not year.isdigit() and not has_raise(c):
        return False, "no founding year and no funding — no evidence"
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=list(SOURCES), help="run one source only")
    args = ap.parse_args()

    exact, stems, people = known_names()
    targets = {args.source: SOURCES[args.source]} if args.source else SOURCES
    generated = datetime.now(timezone.utc)
    report, all_new = {}, []

    for key, src in targets.items():
        print(f"→ {key}: {src['url']}", flush=True)
        try:
            r = requests.get(src["url"], timeout=30, headers={"User-Agent": UA})
            r.raise_for_status()
            rows = src["extract"](r.text)
        except Exception as e:                                    # noqa: BLE001
            print(f"   FAILED: {e}")
            report[key] = {"error": str(e), "listed": 0}
            continue

        missing = []
        for c in rows:
            if norm(c["name"]) in exact or stem(c["name"]) in stems:
                continue
            shared = person_set(c.get("founders", "")) & people.keys()
            if shared:                      # same founder = same company, renamed
                c["_dupe_of"] = people[sorted(shared)[0]]
                continue
            missing.append(c)
        candidates, rejected = [], {}
        for c in missing:
            keep, why = in_scope(c)
            (candidates if keep else rejected.setdefault(why, [])).append(c if keep else c["name"])
        for c in candidates:
            c["our_sector"] = SECTOR_MAP[c["sector"]]
            c["source_list"] = key
        report[key] = {
            "url": src["url"], "note": src["note"], "listed": len(rows),
            "already_tracked": len(rows) - len(missing),
            "missing": len(missing), "in_scope_candidates": len(candidates),
            "rejected_by_bar": {k: len(v) for k, v in rejected.items()},
            "rejected_names": rejected,
            "candidates": candidates,
        }
        all_new.extend(candidates)
        pct = (len(rows) - len(missing)) / len(rows) if rows else 0
        print(f"   {len(rows)} listed · {len(rows)-len(missing)} tracked ({pct:.0%})"
              f" · {len(candidates)} pass the bar")
        for why, names in sorted(rejected.items(), key=lambda kv: -len(kv[1])):
            print(f"      rejected {len(names):>3}: {why}")

    payload = {"generated_at": generated.isoformat(),
               "total_candidates": len(all_new), "sources": report}
    DATA_DIR.mkdir(exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2))
    JS_OUT.write_text(f"// Last updated: {generated.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                      f"window.CURATED_LISTS_AUTO = {json.dumps(payload)};\n")

    queue = json.loads(QUEUE_OUT.read_text()) if QUEUE_OUT.exists() else []
    seen = {norm(q.get("name", "")) for q in queue}
    added = 0
    for c in all_new:
        if norm(c["name"]) in seen:
            continue
        queue.append({**c, "detected_at": generated.isoformat(), "status": "pending"})
        seen.add(norm(c["name"]))
        added += 1
    QUEUE_OUT.write_text(json.dumps(queue, indent=2))

    print(f"\n{len(all_new)} in-scope candidates · {added} newly queued "
          f"· {len(queue)} total in queue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
