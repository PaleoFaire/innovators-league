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

Sources move. In Sept 2026 buildlist turned its homepage into a jobs board and
moved the directory to /companies, and the extractor kept "succeeding" with
zero rows for two weekly runs. A source that suddenly parses nothing, or under
half of the previous run's count, is now treated as broken: its last good data
is kept, the error is recorded, and the script exits non-zero so the Action
goes red instead of quietly reporting "0 listed".

Matching uses a suffix-stripping stem so "Varda Space" resolves to
"Varda Space Industries" and "Helion Energy" to "Helion", and it honours
formerNames so a rename is not reported as a discovery. The stem never merges
a pair that data/name_collisions.json records as different companies
("Navier AI" is not Navier, "Monumental Labs" is not Monumental).

HQ cross-check (report only)
────────────────────────────
BuildList carries each company's location_city and metro. Every run that reads
BuildList also lists the COMPANIES records whose state, country or city
disagrees with it, matched by website domain first (BuildList publishes no
website, so the domain comes from its careers link when that is on the
company's own site), then by exact name. Known-stale BuildList rows are in
HQ_IGNORE. The list is for a human to check; nothing is applied.

Output
──────
  data/curated_lists_auto.json   full diff per source, with records
  data/curated_lists_auto.js     window global for the frontend
  data/curated_review_queue.json new in-scope candidates awaiting review
  data/hq_crosscheck_auto.json   COMPANIES whose HQ disagrees with BuildList

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
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from html import unescape

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
JSON_OUT = DATA_DIR / "curated_lists_auto.json"
JS_OUT = DATA_DIR / "curated_lists_auto.js"
QUEUE_OUT = DATA_DIR / "curated_review_queue.json"
HQ_OUT = DATA_DIR / "hq_crosscheck_auto.json"
COLLISIONS = DATA_DIR / "name_collisions.json"

sys.path.insert(0, str(ROOT / "scripts"))
from validate_data_quality import US_STATES  # noqa: E402

# BuildList rows checked by hand and known to carry a stale HQ (Oct 2026).
# BuildList / data.js: Hermeus Atlanta / Hawthorne, SpaceX Hawthorne /
# Starbase, Moment Energy Coquitlam / Surrey, Katalyst Space Flagstaff /
# Broomfield. norm()-ed names; skipped instead of re-reported every week.
HQ_IGNORE = {"hermeus", "spacex", "momentenergy", "katalystspace"}

# Careers links on these hosts say nothing about the company's own domain.
JOB_HOSTS = re.compile(
    r"(?:^|\.)(?:greenhouse\.io|ashbyhq\.com|lever\.co|workable\.com|bamboohr\.com|rippling\.com|"
    r"myworkdayjobs\.com|workday\.com|smartrecruiters\.com|jobvite\.com|breezy\.hr|recruitee\.com|"
    r"teamtailor\.com|pinpointhq\.com|dover\.com|gem\.com|wellfound\.com|ycombinator\.com|"
    r"notion\.site|paylocity\.com|icims\.com|adp\.com|ultipro\.com|paycomonline\.net|paycor\.com|"
    r"recruitingbypaycor\.com|jazzhr\.com|applytojob\.com|personio\.(?:com|de)|join\.com|homerun\.co|"
    r"trinethire\.com|gusto\.com|bullhornstaffing\.com|careerplug\.com|comeet\.(?:com|co)|polymer\.co|"
    r"getro\.com|linkedin\.com|kula\.ai|deel\.com|careers-page\.com|clearcompany\.com|"
    r"applicantpro\.com|darwinbox\.in|octbr\.ai|magneto365\.com|consider\.com)$", re.I)

COUNTRY_SYNONYMS = {
    "uk": "united kingdom", "england": "united kingdom", "scotland": "united kingdom",
    "wales": "united kingdom", "great britain": "united kingdom", "usa": "united states",
    "us": "united states", "u.s.": "united states", "the netherlands": "netherlands",
    "holland": "netherlands", "korea": "south korea", "republic of korea": "south korea",
    "uae": "united arab emirates",
}
CITY_SYNONYMS = {"nyc": "new york", "new york city": "new york", "sf": "san francisco",
                 "washington dc": "washington", "washington d.c.": "washington"}

UA = "InnovatorsLeague-Bot/1.0 (+https://innovatorsleague.com; research)"

# A source that parses fewer than this share of its previous run's count is
# treated as broken (page moved or layout changed), not as companies vanishing.
MIN_KEEP = 0.5

# buildlist sector -> our SECTORS taxonomy. Anything not here is out of scope
# (AI App, AI Research, Fintech, Public Services, Education, Supply Chain).
# Source sector vocabulary -> our SECTORS taxonomy. Sources use different words
# for the same thing (buildlist "Energy & Climate", Black Flag "Energy"), so both
# vocabularies live here. Anything absent is treated as out of scope, which is how
# AI App, Fintech, Public Services, Education and Supply Chain get filtered out.
SECTOR_MAP = {
    # buildlist.xyz
    "Energy & Climate": "Climate & Energy",
    "Compute & Semiconductors": "Chips & Semiconductors",
    "Bio & Health": "Biotech & Health",
    "Agriculture": "Robotics & Manufacturing",
    "Construction & Housing": "Housing & Construction",
    # blackflag.vc
    "Cybersecurity": "Defense & Security",
    "AI": "AI & Software",
    "Software": "AI & Software",
    "Materials Science": "Robotics & Manufacturing",
    "Critical Minerals": "Robotics & Manufacturing",
    "Health / Bio": "Biotech & Health",
    "Energy": "Climate & Energy",
    # shared by both
    "Aerospace": "Space & Aerospace",
    "Defense": "Defense & Security",
    "Robotics": "Robotics & Manufacturing",
    "Manufacturing": "Robotics & Manufacturing",
    "Transportation": "Transportation",
}

# Software and services that carry a hard-tech sector label on the source list.
SOFT = re.compile(
    r"(medicare|insurance|referral|paperwork|documentation|clinical document|"
    r"source-to-pay|marketplace|gpu cloud|serverless|ai cloud|penetration testing|"
    r"lab testing|drug trials with ai|generative ai agents|trades .*online|"
    r"energy retail|detects emerging risks|observability|telemetry platform|"
    # Added after the 2026-09-22 queue review, where these slipped through as
    # hard tech: PermitFlow, SESO, Traba, Sustainment, Candid Health, Socket,
    # Infisical, Verse Medical, Mithril.
    r"permitting|labor market|labor platform|software platform connecting|"
    r"revenue cycle|claims processing|cloud gpu|gpu capacity|malware|"
    r"managing secrets|software that coordinates)", re.I)

# Public megacaps and mega-private labs we deliberately do not track.
EXCLUDE = {
    "nvidia", "tesla", "coreweave", "cerebrassystems", "aurora", "nebius", "meta",
    "stripe", "openai", "anthropic", "canva", "deel", "rivian", "waymo", "palantir",
    "spacex", "blueorigin", "rocketlab", "databricks", "notion", "ramp", "brex",
    "mercury", "revolut", "epicgames", "rippling", "samsara", "whatnot", "xai",
    "huggingface", "midjourney", "perplexity", "scaleai", "cohere", "mistralai",
    # Cut from the database 2026-09-25 (AI labs and clouds with no physical
    # product, plus one dormant company); never re-queue them.
    "blackforestlabs", "breenenergy", "cartesia", "cognition", "coreautomation", "cuspai", "flappingairplanes", "humain", "humans", "hypernovaspacetechnologies", "lambda", "poolside", "reflectionai", "togetherai", "worldlabs",
    # Cut 2026-10-01 after the full database audit (not frontier tech, unverifiable,
    # dormant, or exited); never re-queue them.
    "somos", "runpod", "sfcompute", "davidenergy", "meter", "hedral", "axion", "monaire", "wisprai", "lumenenergy", "infinitemachine", "electricair", "deepsentinel", "groundcontroldevelopment", "atmocooling", "anatar", "stackedenergy", "californiaforever", "keentechnologies", "makesunsets", "lookingglass", "olympianmotors", "wraithwatch", "flamefrontpropulsion", "corvexsystems", "stratekglobal", "edengeopower", "ephemerisnet", "sagence", "fidlabs", "atropos", "solestial", "enfabrica", "dendrasystems", "dark",
    # Cut 2026-10-07 after the high-bar audit (no funding, top fund or contracts on record);
    # never re-queue them. Restore with scripts/restore_cut_company.py.
    "becoming", "firmapower", "mithrilmining", "pathpower", "pilaenergy", "voltra", "wetstone", "determinantmaterials", "stonepower", "adastraskysupply", "airrow", "bohrsystems", "brynhildindustries", "dispatcher", "lodgesystems", "maritimeoperationsgroup", "notusautonomoussystems", "ornadyne", "rebelspace", "revere", "victustechnologies", "vight", "deepatomic", "zephyrfusion", "deepwaterexploration", "athanor", "atopile", "axialcomposites", "digichem", "drafter", "frameworkautomation", "grainweevil", "krevera", "mbodiai", "octavia", "radianforge", "robotwin", "vuecason", "xenops", "epicaerospace", "gru", "floatcargo", "sysgit", "obsidiasemiconductor", "photonium", "guardianrf", "splashindustries", "astrolight", "thespaceportcompany", "maymanaerospace", "arkrobotics", "nordicairdefence", "rmfg", "tobeenergy", "soaring", "aibot", "kytedynamics", "createme", "parityqc", "noblemachines",
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


def load_collisions(path: Path = COLLISIONS) -> dict[str, set[str]]:
    """norm(name) -> norm()-ed COMPANIES names it is known NOT to be.

    From the different_companies list in data/name_collisions.json, which the
    deal feed and the VC portfolio watcher read too. A missing or broken file
    returns {} (no guard) rather than stopping the watcher.
    """
    try:
        raw = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}
    out: dict[str, set[str]] = {}
    for e in raw.get("different_companies") or []:
        nots = e.get("not") or []
        nots = [nots] if isinstance(nots, str) else nots
        if e.get("name") and nots:
            out.setdefault(norm(e["name"]), set()).update(norm(n) for n in nots)
    return out


def different_company(a: str, b: str, collisions: dict[str, set[str]]) -> bool:
    """True when data/name_collisions.json records `a` and `b` as different companies."""
    na, nb = norm(a), norm(b)
    return nb in collisions.get(na, ()) or na in collisions.get(nb, ())


def db_rows() -> list[dict]:
    """COMPANIES from data.js (read-only): name, formerNames, founder, website,
    location, state, country."""
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
          '+";globalThis.__n=COMPANIES.map(c=>({n:c.name,f:c.formerNames||[],p:c.founder||\'\','
          'w:c.website||\'\',l:c.location||\'\',s:c.state||\'\',c:c.country||\'\'}));",s);'
          "console.log(JSON.stringify(s.__n));")
    return json.loads(subprocess.run(["node", "-e", js, str(DATA_JS)],
                                     capture_output=True, text=True, check=True).stdout)


def known_names(rows: list[dict] | None = None) -> tuple[set[str], dict[str, set[str]], dict[str, str]]:
    """Returns (exact names, stem -> COMPANIES names, founder -> company name).

    The founder index is the decisive duplicate signal. Suffix stemming alone
    cannot collapse 'Heirloom' onto 'Heirloom Carbon', 'STARK' onto
    'Stark Defence' or 'Regent' onto 'REGENT Craft' without an ever-growing
    list of suffix words — but all three share their full founder line with
    the record we already hold.
    """
    rows = db_rows() if rows is None else rows
    exact, stems, people = set(), {}, {}
    for r in rows:
        for label in [r["n"]] + r["f"]:
            exact.add(norm(label))
            stems.setdefault(stem(label), set()).add(r["n"])
        for p in person_set(r["p"]):
            people.setdefault(p, r["n"])
    return exact, stems, people


def is_tracked(name: str, exact: set[str], stems: dict[str, set[str]],
               collisions: dict[str, set[str]]) -> bool:
    """Already in COMPANIES under this exact name or formerName, or under a
    suffix-stripped stem — unless the record sharing the stem is on file as a
    different company: "Varda Space" is Varda Space Industries, but "Navier AI"
    is not Navier and "Monumental Labs" is not Monumental."""
    if norm(name) in exact:
        return True
    return any(not different_company(name, held, collisions) for held in stems.get(stem(name), ()))


# ── HQ cross-check against BuildList ─────────────────────────────────────

def _host(url: str) -> str:
    if not url:
        return ""
    u = url.strip() if "://" in url else "https://" + url.strip()
    h = urlparse(u).netloc.lower().split(":")[0]
    return h[4:] if h.startswith("www.") else h


# Letters NFKD does not decompose into a base letter plus an accent.
_UNFOLDABLE = str.maketrans({"ł": "l", "Ł": "L", "ø": "o", "Ø": "O", "đ": "d", "Đ": "D",
                             "ß": "ss", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE", "ı": "i"})


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").translate(_UNFOLDABLE)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.strip().lower())


def _place(location: str) -> tuple[str, str, str]:
    """(city, US state code or '', country) from "City, ST" or "City, [Region,] Country"."""
    parts = [p.strip() for p in (location or "").split(",") if p.strip()]
    if not parts:
        return "", "", ""
    last = parts[-1]
    code = last.replace(".", "").upper()
    if len(parts) > 1 and code in US_STATES:
        state, country = code, "united states"
    else:
        state, country = "", COUNTRY_SYNONYMS.get(_fold(last), _fold(last))
    city = _fold(parts[0]) if len(parts) > 1 else ""
    return CITY_SYNONYMS.get(city, city), state, country


def hq_crosscheck(bl_rows: list[dict], rows: list[dict], collisions: dict[str, set[str]],
                  generated: str = "") -> dict:
    """COMPANIES records whose state, country or city disagrees with BuildList.

    Domain first: BuildList publishes no website, but about a hundred of its
    careers links sit on the company's own site, and a domain is exact (only
    the host's subdomains are stripped; a same-name site under another TLD
    is not assumed to be the same company, since a false match here becomes
    a false disagreement). Then an exact name (or formerName), vetoed when
    both sides show a domain and they differ, and never across a pair that
    data/name_collisions.json separates.
    """
    by_domain, by_norm, rec = {}, {}, {}
    for r in rows:
        rec[r["n"]] = r
        d = _host(r.get("w", ""))
        if d:
            by_domain.setdefault(d, r["n"])
        for label in [r["n"]] + r["f"]:
            by_norm.setdefault(norm(label), r["n"])

    items, ignored, how_counts, compared = [], set(), {"domain": 0, "name": 0}, 0
    for b in bl_rows:
        h = _host(b.get("careers_url", ""))
        own = h if h and not JOB_HOSTS.search(h) else ""
        name, how = None, ""
        if own:
            labels = own.split(".")
            for i in range(len(labels) - 1):                  # careers.rivian.com -> rivian.com
                name = by_domain.get(".".join(labels[i:]))
                if name:
                    break
            how = "domain" if name else ""
        if not name:
            cand = by_norm.get(norm(b.get("name", "")))
            if cand and not different_company(b.get("name", ""), cand, collisions):
                cd = _host(rec[cand].get("w", ""))
                if not (own and cd and own != cd and not own.endswith("." + cd)):
                    name, how = cand, "name"
        if not name:
            continue
        if norm(name) in HQ_IGNORE or norm(b.get("name", "")) in HQ_IGNORE:
            ignored.add(name)
            continue
        r = rec[name]
        bl_city, bl_state, bl_country = _place(b.get("city", ""))
        db_city, _, _ = _place(r.get("l", ""))
        db_state = (r.get("s") or "").upper()
        db_country = COUNTRY_SYNONYMS.get(_fold(r.get("c", "")), _fold(r.get("c", "")))
        if not db_country and db_state:
            db_country = "united states"
        if not (bl_city or bl_state or bl_country) or not (db_city or db_state or db_country):
            continue                                          # nothing to compare
        compared += 1
        how_counts[how] += 1
        if bl_country and db_country and bl_country != db_country:
            kind = "country"
        elif bl_state and db_state and bl_state != db_state:
            kind = "state"
        elif bl_city and db_city and bl_city != db_city:
            kind = "city"
        else:
            continue
        items.append({
            "company": name, "buildlist_name": b.get("name", ""), "kind": kind, "matched_by": how,
            "db_location": r.get("l", ""), "db_state": r.get("s", ""), "db_country": r.get("c", ""),
            "buildlist_location": b.get("city", ""), "buildlist_metro": b.get("metro", ""),
            "evidence": b.get("careers_url", "") if how == "domain" else "",
        })
    order = {"country": 0, "state": 1, "city": 2}
    items.sort(key=lambda x: (order[x["kind"]], x["company"].lower()))
    by_kind = {k: sum(1 for x in items if x["kind"] == k) for k in order}
    return {
        "generated_at": generated, "source": "buildlist", "source_url": SOURCES["buildlist"]["url"],
        "note": ("Report only, never applied to data.js. COMPANIES records whose state, country or "
                 "city disagrees with BuildList's location_city. BuildList can be the stale side; "
                 "check the company's own site before editing data.js."),
        "compared": compared, "matched_by": how_counts, "ignored": sorted(ignored),
        "count": len(items), "by_kind": by_kind, "items": items,
    }


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

        # careers_url sits after "status" in the record; the job board is the most
        # reliable place to confirm a company's real HQ during review.
        tail = t[m.end():m.end() + 600].split("}", 1)[0]
        careers = re.search(r'"careers_url":"((?:[^"\\]|\\.)*)"', tail)

        out.append({
            "name": name.replace("\\u0026", "&"), "status": status,
            "sector": f("sector"), "tagline": f("tagline"), "founders": f("founders"),
            "city": f("location_city"), "metro": f("metro"), "founded": f("founded_date"),
            "round": f("last_round"), "raised": re.sub(r"^\$\$", "$", f("total_raised")),
            "last_round_date": f("last_round_date"),
            "careers_url": careers.group(1).replace("\\u0026", "&") if careers else "",
        })
    return out


def extract_blackflag(html: str) -> list[dict]:
    """blackflag.vc/100-2 — a Webflow page that server-renders every company.

    Each card anchors on <h3 class="company-name">, and the fields carry
    fs-cmsfilter-field attributes (hq, region, sector, founder), so this reads
    the real values rather than scraping label/value pairs by position — the
    stat labels and texts are NOT adjacent siblings, which silently produced
    empty founders on the first attempt.
    """
    def clean(s):
        return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()

    anchors = [(m.start(), clean(m.group(1)))
               for m in re.finditer(r'<h3[^>]*class="company-name"[^>]*>(.*?)</h3>', html, re.S)]
    out, seen = [], set()
    for idx, (pos, name) in enumerate(anchors):
        end = anchors[idx + 1][0] if idx + 1 < len(anchors) else pos + 14000
        seg = html[pos:end]
        if not name or name in seen:
            continue

        def field(k):
            v = re.findall(r'fs-cmsfilter-field="' + k + r'"[^>]*>(.*?)</div>', seg, re.S)
            return [clean(x) for x in v]

        desc = re.search(r'class="company-description[^"]*"[^>]*>(.*?)</div>', seg, re.S)
        if not desc:
            continue                       # stealth cards carry placeholder text
        site = re.search(r'<a href="(https?://[^"]+)"[^>]*>\s*<div>Website</div>', seg)
        yr = re.search(r'company-stat-label">Founded</div>\s*<div[^>]*class="company-stat-text"[^>]*>(.*?)</div>',
                       seg, re.S)
        seen.add(name)
        out.append({
            "name": name, "status": "active",
            "sector": (field("sector") or [""])[0],
            "tagline": clean(desc.group(1)),
            "founders": ", ".join(dict.fromkeys(field("founder"))),
            "city": (field("hq") or [""])[0],
            "founded": clean(yr.group(1)) if yr else "",
            "round": "", "raised": "",
            "website": site.group(1).rstrip("/") if site else "",
        })
    return out


SOURCES = {
    # The directory lives at /companies since Sept 2026; "/" is now a jobs board.
    "buildlist": {"url": "https://buildlist.xyz/companies", "extract": extract_buildlist,
                  "note": "Curated directory of companies building the future (Ryan & Christian)"},
    "blackflag": {"url": "https://www.blackflag.vc/100-2", "extract": extract_blackflag,
                  "note": "Black Flag VC's 100 — defense/frontier, high precision (57% already tracked)"},
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

    rows_db = db_rows()
    exact, stems, people = known_names(rows_db)
    collisions = load_collisions()
    targets = {args.source: SOURCES[args.source]} if args.source else SOURCES
    generated = datetime.now(timezone.utc)
    prev = json.loads(JSON_OUT.read_text()).get("sources", {}) if JSON_OUT.exists() else {}
    report, all_new, broken = {}, [], []
    buildlist_rows = None

    def keep_last_good(key: str, why: str) -> None:
        """Record the failure but keep the previous run's data for this source."""
        print(f"   FAILED: {why}")
        last = {k: v for k, v in (prev.get(key) or {"listed": 0}).items() if k != "error"}
        report[key] = {**last, "error": why,
                       "stale_since": last.get("stale_since", generated.isoformat())}
        broken.append(key)

    for key, src in targets.items():
        print(f"→ {key}: {src['url']}", flush=True)
        try:
            r = requests.get(src["url"], timeout=30, headers={"User-Agent": UA})
            r.raise_for_status()
            rows = src["extract"](r.text)
        except Exception as e:                                    # noqa: BLE001
            keep_last_good(key, str(e))
            continue

        before = (prev.get(key) or {}).get("listed") or 0
        if not rows or (before >= 50 and len(rows) < before * MIN_KEEP):
            keep_last_good(key, f"parsed {len(rows)} companies (last run: {before}); "
                                "the page layout or URL has probably changed")
            continue

        if key == "buildlist":
            buildlist_rows = rows
        missing = []
        for c in rows:
            if is_tracked(c["name"], exact, stems, collisions):
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

    # A single-source run must not wipe the other sources' last results.
    sources = {**prev, **report} if args.source else report
    payload = {"generated_at": generated.isoformat(),
               "total_candidates": len(all_new), "sources": sources}
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

    # Report-only HQ cross-check; kept from the last good run when BuildList
    # was not read (broken, or a --source run for another list).
    if buildlist_rows:
        hq = hq_crosscheck(buildlist_rows, rows_db, collisions, generated.isoformat())
        HQ_OUT.write_text(json.dumps(hq, indent=2, ensure_ascii=False))
        k = hq["by_kind"]
        print(f"HQ cross-check: {hq['count']} of {hq['compared']} matched companies disagree with "
              f"BuildList ({k['country']} country, {k['state']} state, {k['city']} city only; "
              f"{len(hq['ignored'])} ignored) — report only, data/{HQ_OUT.name}")
    else:
        print("HQ cross-check: skipped, BuildList was not read this run (last report kept)")
    if broken:
        # "::error::" becomes an annotation on the GitHub Actions run.
        print(f"::error::curated-list source(s) broken: {', '.join(broken)} (kept last good data)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
