#!/usr/bin/env python3
"""
The Build-Out Pulse — monthly diffusion index of the private US hard-tech cohort.  Method v1.1
─────────────────────────────────────────────────────────────────────────
Reads only data the repo already collects and turns it into one number a month.

Components:
  hiring     open roles per company from the job-board feed (data/jobs_auto.js); month-end snapshots
             reconstructed from git history for the backfill; constant panel; diffusion = 50 +
             (share up − share down) × 50, up/down = ±10% or ±3 roles; a bootstrap 90% interval on
             the diffusion; the breadth split (share up / flat / down); the atoms/bits ratio
             (manufacturing + hardware-engineering titles ÷ software titles, taxonomy v1.1); roles by
             state; the "factory coming" flag (a senior manufacturing / plant / facilities hire).
  guard      a company whose count collapses ≥85% from ≥20 roles (or jumps the reverse way from ≤3)
             is treated as a board change, not a contraction: excluded from that month's panel and
             listed in board_checks_<m>.json for a human to confirm.
  capital    one dated event per company-month merged from the deals feed, Form D, the VC portfolio
             watcher's first-funded dates and company announcements; covered panel breadth.
  contracts  new federal awards (USAspending/SAM); covered panel breadth.
  milestones data/pulse/milestones.json — confirmed Ladder rung changes (manual).
  footprint  data/pulse/footprint.json — confirmed facility events (manual).
             Unconfirmed extractions go to data/pulse/review_queue.json and never count.

Universe: private (no ticker), status active, sectors inside the build-out.
Outputs (data/pulse/): pulse_history.csv, pulse_buckets.csv, movers_<m>.json, company_scores_<m>.json,
  states_<m>.json, board_checks_<m>.json, composition_<m>.json, snapshots/<m>.json, first_prints.json,
  revisions.json, review_queue.json, validation.md, pulse_latest.json; plus data/pulse_auto.js.

Usage:
  python3 scripts/calc_pulse.py                 # backfill from git + nowcast for the current month
  python3 scripts/calc_pulse.py --no-backfill   # current month only, from stored snapshots
"""
import csv
import json
import os
import random
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from pulse_taxonomy import classify, is_senior_manufacturing, TAXONOMY_VERSION  # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "pulse"
SNAP = OUT / "snapshots"
OUT.mkdir(exist_ok=True)
SNAP.mkdir(exist_ok=True)

METHOD_VERSION = "1.1"
UP_PCT, UP_ABS = 0.10, 3          # published thresholds — never tuned to make a month look better
STALE_DAYS = 365                  # postings older than this are treated as ghosts
COLLAPSE_FROM, COLLAPSE_TO = 20, 3   # ≥20 → ≤3 (or the reverse) is a board change until confirmed
BOOTSTRAP_N = 2000
WEIGHTS = {"hiring": 30, "capital": 20, "contracts": 20, "milestones": 20, "footprint": 10}
START_MONTH = "2026-04"           # first month with a clean prior snapshot
MIN_BUCKET = 20

BUCKET_BY_SECTOR = {
    "Nuclear Energy": "Nuclear",
    "Climate & Energy": "Power & Grid",
    "Defense & Security": "Defence",
    "Space & Aerospace": "Space & Aerospace",
    "Supersonic & Hypersonic": "Space & Aerospace",
    "Chips & Semiconductors": "Chips & Quantum",
    "Quantum Computing": "Chips & Quantum",
    "Drones & Autonomous": "Autonomy & Robotics",
    "Transportation": "Autonomy & Robotics",
    "Ocean & Maritime": "Autonomy & Robotics",
    "Robotics & Manufacturing": "Manufacturing & Materials",
    "Housing & Construction": "Manufacturing & Materials",
    "Infrastructure & Logistics": "Manufacturing & Materials",
    "Biotech & Health": None,     # outside the build-out — tracked, not in the headline
    "AI & Software": None,
    "Consumer Tech": None,
}
ROBOTICS_SUBS = ("Humanoids", "Robot Foundation Models", "Industrial Automation",
                 "Warehouse & Logistics Robotics", "Food & Agriculture Robotics")
MINERALS_SUB = "Critical Minerals & Mining"

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}
STATE_BY_NAME = {v.lower(): k for k, v in US_STATES.items()}
MILESTONE_KW = re.compile(r"first (?:unit|customer|commercial|revenue|delivery|flight|launch|shipment)|criticality|went critical|achieved criticality|first light|first article|reached (?:full )?power|delivered (?:the |its )?first|production (?:begins|started|start)|commercial operation|type certificate|nrc (?:approv|permit|licen)|faa (?:approv|certif)", re.I)
FOOTPRINT_KW = re.compile(r"break(?:s|ing)? ground|groundbreaking|new (?:factory|facility|plant|headquarters|campus)|opens? (?:a |its |new )?(?:factory|facility|plant)|square[- ]f(?:oo|ee)t|sq\.? ?ft|lease[sd]?\b|expansion of|expands? (?:its )?(?:factory|facility|manufacturing)|manufacturing (?:site|facility|plant)", re.I)
CLASSES = ("manufacturing", "hardware", "software", "commercial", "other")


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT).stdout


def norm_domain(url):
    if not url:
        return ""
    host = urlparse(url if url.startswith("http") else "https://" + url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def load_companies():
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync("data.js","utf8")+";globalThis.__n=COMPANIES.map(c=>({name:c.name,'
          'sector:c.sector||\'\',subsector:c.subsector||\'\',status:c.status||\'\',ticker:c.ticker||\'\','
          'founded:c.founded||null,state:c.state||\'\',website:c.website||\'\',stage:c.fundingStage||\'\'}));",s);console.log(JSON.stringify(s.__n));')
    raw = subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd=ROOT, check=True).stdout
    out = {}
    for c in json.loads(raw):
        b = BUCKET_BY_SECTOR.get(c["sector"], "Manufacturing & Materials")
        if c["sector"] == "Robotics & Manufacturing" and c["subsector"] in ROBOTICS_SUBS:
            b = "Autonomy & Robotics"
        if c["sector"] == "Climate & Energy" and c["subsector"] == MINERALS_SUB:
            b = "Manufacturing & Materials"
        c["bucket"] = b
        c["private"] = not c["ticker"] and c["status"] not in ("ipo", "public")
        c["alive"] = c["status"] in ("active", "")
        c["domain"] = norm_domain(c["website"])
        out[c["name"]] = c
    return out


def in_universe(c):
    return c["private"] and c["alive"] and c["bucket"] is not None


# ─── hiring ──────────────────────────────────────────────────────────────

def parse_jobs_js(txt):
    i = txt.find("const JOBS_DATA = ")
    if i < 0:
        return []
    return json.JSONDecoder().raw_decode(txt[i + len("const JOBS_DATA = "):])[0]


def parse_state(location):
    if not location:
        return None
    loc = location.strip()
    m = re.search(r",\s*([A-Z]{2})\b", loc)
    if m and m.group(1) in US_STATES:
        return m.group(1)
    low = loc.lower()
    for name, abbr in STATE_BY_NAME.items():
        if re.search(r"\b" + re.escape(name) + r"\b", low):
            return abbr
    if "remote" in low:
        return "REMOTE"
    return None


def clean_jobs(jobs, asof):
    """Dedupe (company, title, location) and drop postings older than STALE_DAYS."""
    seen, out = set(), []
    cutoff = (datetime.fromisoformat(asof) - timedelta(days=STALE_DAYS)).date().isoformat()
    for j in jobs:
        key = (j.get("company"), (j.get("title") or "").strip().lower(), (j.get("location") or "").strip().lower())
        if key in seen:
            continue
        seen.add(key)
        p = j.get("posted") or ""
        if p and p < cutoff:
            continue
        out.append(j)
    return out


def jobs_counts(jobs, companies):
    roles = Counter()
    cls = {k: Counter() for k in CLASSES}
    senior = Counter()
    states = defaultdict(Counter)
    state_atoms, state_sw = Counter(), Counter()
    for j in jobs:
        n = j.get("company")
        c = companies.get(n)
        if not c or not in_universe(c):
            continue
        roles[n] += 1
        t = j.get("title", "") or ""
        k = classify(t)
        cls[k][n] += 1
        if is_senior_manufacturing(t):
            senior[n] += 1
        st = parse_state(j.get("location"))
        if st:
            states[st][n] += 1
            if k in ("manufacturing", "hardware"):
                state_atoms[st] += 1
            elif k == "software":
                state_sw[st] += 1
    return {"roles": roles, "mfg": cls["manufacturing"], "hw": cls["hardware"], "sw": cls["software"],
            "ga": cls["commercial"], "other": cls["other"], "senior": senior,
            "states": {s: dict(v) for s, v in states.items()}, "state_atoms": state_atoms, "state_sw": state_sw}


def month_end_snapshots():
    """{'YYYY-MM': (sha, date)} — the last commit of each month that touched the jobs feed."""
    log = sh("git log --format='%H %ad' --date=short -- data/jobs_auto.js").splitlines()
    snap = {}
    for line in log:
        if not line.strip():
            continue
        sha, d = line.split()
        snap.setdefault(d[:7], (sha, d))   # newest-first ⇒ first seen is the month's last commit
    return snap


def snapshot_from_file(d):
    return {"roles": Counter(d["roles"]), "mfg": Counter(d.get("mfg", {})), "hw": Counter(d.get("hw", {})),
            "sw": Counter(d.get("sw", {})), "ga": Counter(d.get("ga", {})), "other": Counter(d.get("other", {})),
            "senior": Counter(d.get("senior", {})), "states": d.get("states", {}),
            "state_atoms": Counter(d.get("state_atoms", {})), "state_sw": Counter(d.get("state_sw", {}))}


# ─── capital & contracts ─────────────────────────────────────────────────

def month_of(s):
    s = str(s or "")[:7]
    return s if re.match(r"\d{4}-\d{2}$", s) else None


def capital_events(companies):
    """{company: sorted list of 'YYYY-MM'} merged from four feeds, deduplicated by company-month."""
    ev = defaultdict(set)
    src = Counter()
    p = DATA / "deals_auto.json"
    if p.exists():
        for d in json.load(open(p)):
            n, m = d.get("company"), month_of(d.get("date"))
            if n in companies and m:
                ev[n].add(m); src["deals"] += 1
    for f in ("form_d_filings_auto.json", "form_d_daily_auto.json"):
        p = DATA / f
        if p.exists():
            try:
                for d in json.load(open(p)).get("filings", []):
                    n, m = d.get("company"), month_of(d.get("filed_date"))
                    if n in companies and m:
                        ev[n].add(m); src["form_d"] += 1
            except Exception:
                pass
    p = DATA / "vc_portfolio_snapshots.json"
    if p.exists():
        try:
            by_domain = {c["domain"]: n for n, c in companies.items() if c["domain"]}
            by_name = {n.lower(): n for n in companies}
            for fund in json.load(open(p)).get("funds", {}).values():
                for h in fund.get("holdings") or []:
                    if not isinstance(h, dict):
                        continue
                    m = month_of(h.get("first_funded") or h.get("date"))
                    if not m:
                        continue
                    n = by_domain.get(norm_domain(h.get("domain") or "")) or by_name.get((h.get("name") or "").lower())
                    if n:
                        ev[n].add(m); src["vc_first_funded"] += 1
        except Exception:
            pass
    p = DATA / "company_announcements_auto.json"
    if p.exists():
        try:
            for r in json.load(open(p)).get("results", []):
                n = r.get("company")
                for h in r.get("hits") or []:
                    if isinstance(h, dict) and (h.get("round") or h.get("amount")) and n in companies:
                        m = month_of(h.get("date"))
                        if m:
                            ev[n].add(m); src["announcements"] += 1
        except Exception:
            pass
    return {k: sorted(v) for k, v in ev.items()}, dict(src)


def contract_events(companies):
    ev = defaultdict(set)
    p = DATA / "gov_contracts_aggregated.json"
    if p.exists():
        for r in json.load(open(p)):
            n = r.get("company")
            if n not in companies:
                continue
            for rc in r.get("recentContracts", []):
                m = month_of(rc.get("date"))
                if m:
                    ev[n].add(m)
    return {k: sorted(v) for k, v in ev.items()}


def manual_events(fname):
    p = OUT / fname
    if not p.exists():
        return {}
    ev = defaultdict(list)
    for r in json.load(open(p)):
        m = month_of(r.get("date"))
        if r.get("company") and m and r.get("confirmed", True):
            ev[r["company"]].append((m, 1 if r.get("direction", "up") == "up" else -1))
    return ev


def months_between(a, b):
    ya, ma = map(int, a.split("-")); yb, mb = map(int, b.split("-"))
    return (yb - ya) * 12 + (mb - ma)


def event_diffusion(events, companies, month, lookback_pos=3, lookback_neg=12):
    up = down = flat = 0
    for n, ms in events.items():
        c = companies.get(n)
        if not c or not in_universe(c):
            continue
        past = [m for m in ms if m <= month]
        if not past:
            continue
        gap = months_between(past[-1], month)
        if gap < lookback_pos:
            up += 1
        elif gap >= lookback_neg:
            down += 1
        else:
            flat += 1
    panel = up + down + flat
    return (50 + (up - down) / panel * 50 if panel else None), panel, up


def manual_diffusion(events, companies, month, n_total):
    up = down = 0
    for n, lst in events.items():
        c = companies.get(n)
        if not c or not in_universe(c):
            continue
        for m, dirn in lst:
            if m == month:
                up += dirn > 0
                down += dirn < 0
    if up + down == 0:
        return None, 0
    return 50 + (up - down) / n_total * 50, up + down


def recency_points(events, n, month, scale):
    past = [m for m in events.get(n, []) if m <= month]
    if not past:
        return 0
    gap = months_between(past[-1], month)
    return scale if gap < 3 else (scale * 0.6 if gap < 6 else (scale * 0.2 if gap < 12 else 0))


def direction(a, b):
    if b - a >= UP_ABS or (a and (b - a) / a >= UP_PCT):
        return 1
    if a - b >= UP_ABS or (a and (a - b) / a >= UP_PCT):
        return -1
    return 0


def bootstrap_ci(dirs, n_iter=BOOTSTRAP_N, seed=20260926):
    """90% bootstrap interval on the diffusion from the list of per-company directions (+1/0/-1)."""
    if not dirs:
        return None, None
    rng = random.Random(seed)
    n = len(dirs)
    vals = []
    for _ in range(n_iter):
        s = sum(rng.choice(dirs) for _ in range(n))
        vals.append(50 + s / n * 50)
    vals.sort()
    return round(vals[int(0.05 * n_iter)], 1), round(vals[int(0.95 * n_iter) - 1], 1)


# ─── review queue: extraction that never counts until a human confirms ───

def build_review_queue(companies):
    q = []
    p = DATA / "company_announcements_auto.json"
    if p.exists():
        try:
            for r in json.load(open(p)).get("results", []):
                n = r.get("company")
                if n not in companies:
                    continue
                for h in r.get("hits") or []:
                    text = " ".join(str(h.get(k, "")) for k in ("title", "evidence")) if isinstance(h, dict) else str(h)
                    for kind, rx in (("milestone", MILESTONE_KW), ("footprint", FOOTPRINT_KW)):
                        m = rx.search(text)
                        if m:
                            q.append({"company": n, "type": kind, "keyword": m.group(0), "date": (h.get("date") if isinstance(h, dict) else "") or "",
                                      "source": (h.get("link") if isinstance(h, dict) else "") or r.get("website", ""),
                                      "snippet": text[max(0, m.start() - 120): m.end() + 120].replace("\n", " ")})
        except Exception:
            pass
    for f in ("news_raw.json", "press_releases_filtered.json"):
        p = DATA / f
        if not p.exists():
            continue
        try:
            items = json.load(open(p))
            items = items if isinstance(items, list) else next((v for v in items.values() if isinstance(v, list)), [])
            for it in items:
                names = it.get("matchedCompanies") or ([it.get("matchedCompany")] if it.get("matchedCompany") else [])
                text = f"{it.get('title', '')} {it.get('description', '')}"
                for n in names:
                    if n not in companies:
                        continue
                    for kind, rx in (("milestone", MILESTONE_KW), ("footprint", FOOTPRINT_KW)):
                        m = rx.search(text)
                        if m:
                            q.append({"company": n, "type": kind, "keyword": m.group(0), "date": str(it.get("pubDate", ""))[:10],
                                      "source": it.get("link", ""), "snippet": text[max(0, m.start() - 120): m.end() + 120]})
        except Exception:
            pass
    seen, out = set(), []
    for x in q:
        k = (x["company"], x["type"], x["source"])
        if k not in seen:
            seen.add(k); out.append(x)
    return out


# ─── main ────────────────────────────────────────────────────────────────

def main():
    backfill = "--no-backfill" not in sys.argv
    companies = load_companies()
    universe = [n for n, c in companies.items() if in_universe(c)]
    n_universe = len(universe)
    today = date.today().isoformat()
    cur_month = today[:7]

    snaps, snap_dates = {}, {}
    if backfill:
        for m, (sha, d) in sorted(month_end_snapshots().items()):
            if m < "2026-02":
                continue
            jobs = clean_jobs(parse_jobs_js(sh(f"git show {sha}:data/jobs_auto.js")), d)
            snaps[m] = jobs_counts(jobs, companies); snap_dates[m] = d
    else:
        for p in sorted(SNAP.glob("*.json")):
            d = json.load(open(p))
            snaps[p.stem] = snapshot_from_file(d); snap_dates[p.stem] = d.get("asof", "")
    jobs_now = clean_jobs(parse_jobs_js(open(DATA / "jobs_auto.js", encoding="utf-8").read()), today)
    snaps[cur_month] = jobs_counts(jobs_now, companies); snap_dates[cur_month] = today

    cap, cap_sources = capital_events(companies)
    con = contract_events(companies)
    mil = manual_events("milestones.json")
    foot = manual_events("footprint.json")
    confirmed_checks = set()
    p = OUT / "board_checks_confirmed.json"
    if p.exists():
        for r in json.load(open(p)):
            confirmed_checks.add((r.get("company"), r.get("month")))

    first_prints = json.load(open(OUT / "first_prints.json")) if (OUT / "first_prints.json").exists() else {}
    revisions = json.load(open(OUT / "revisions.json")) if (OUT / "revisions.json").exists() else []

    hist_rows, bucket_rows = [], []
    prev = None
    for m in sorted(snaps):
        s = snaps[m]
        json.dump({"month": m, "asof": snap_dates.get(m, ""), "roles": s["roles"], "mfg": s["mfg"], "hw": s["hw"], "sw": s["sw"],
                   "ga": s["ga"], "other": s["other"], "senior": s["senior"], "states": s["states"],
                   "state_atoms": s["state_atoms"], "state_sw": s["state_sw"], "generated": today,
                   "taxonomy": TAXONOMY_VERSION}, open(SNAP / f"{m}.json", "w"))
        if prev is None or m < START_MONTH:
            prev = m
            continue
        roles, p_roles = s["roles"], snaps[prev]["roles"]
        # board-change guard
        board_checks = []
        panel = []
        for n in roles:
            if n not in p_roles:
                continue
            a, b = p_roles[n], roles[n]
            if (a >= COLLAPSE_FROM and b <= COLLAPSE_TO) or (a <= COLLAPSE_TO and b >= COLLAPSE_FROM):
                if (n, m) not in confirmed_checks:
                    board_checks.append({"company": n, "month": m, "roles_prev": a, "roles_now": b,
                                         "reason": "collapse" if b < a else "jump", "status": "unconfirmed — excluded from panel"})
                    continue
            panel.append(n)
        up = down = flat = 0
        tot_now = tot_prev = 0
        dirs = []
        by_bucket = defaultdict(lambda: {"panel": 0, "up": 0, "down": 0, "roles": 0, "mfg": 0, "hw": 0, "sw": 0, "ga": 0, "senior": 0})
        movers, changes = [], {}
        for n in panel:
            a, b = p_roles[n], roles[n]
            tot_prev += a; tot_now += b
            bk = companies[n]["bucket"]
            bb = by_bucket[bk]; bb["panel"] += 1; bb["roles"] += b
            bb["mfg"] += s["mfg"][n]; bb["hw"] += s["hw"][n]; bb["sw"] += s["sw"][n]; bb["ga"] += s["ga"][n]; bb["senior"] += s["senior"][n]
            d = direction(a, b); dirs.append(d)
            if d > 0:
                up += 1; bb["up"] += 1
            elif d < 0:
                down += 1; bb["down"] += 1
            else:
                flat += 1
            changes[n] = (b - a) / a if a else (1.0 if b else 0.0)
            if a >= 5:
                movers.append({"company": n, "bucket": bk, "roles_prev": a, "roles_now": b,
                               "change": b - a, "change_pct": round(100 * (b - a) / a, 1)})
        n_panel = len(panel)
        h_diff = 50 + (up - down) / n_panel * 50 if n_panel else None
        ci_lo, ci_hi = bootstrap_ci(dirs)
        c_diff, c_panel, c_ev = event_diffusion(cap, companies, m)
        k_diff, k_panel, k_ev = event_diffusion(con, companies, m)
        m_diff, m_n = manual_diffusion(mil, companies, m, n_universe)
        f_diff, f_n = manual_diffusion(foot, companies, m, n_universe)
        cap_rate = sum(1 for n in universe if any(0 <= months_between(x, m) <= 2 for x in cap.get(n, []))) / n_universe * 100
        con_rate = sum(1 for n in universe if any(0 <= months_between(x, m) <= 2 for x in con.get(n, []))) / n_universe * 100

        comps = {"hiring": h_diff, "capital": c_diff, "contracts": k_diff, "milestones": m_diff, "footprint": f_diff}
        live = {k: v for k, v in comps.items() if v is not None}
        wsum = sum(WEIGHTS[k] for k in live)
        composite = sum(WEIGHTS[k] * v for k, v in live.items()) / wsum if wsum else None

        prev_senior = snaps[prev]["senior"]
        factory_flags = sorted([n for n in panel if s["senior"][n] > prev_senior.get(n, 0)])

        state_tot = Counter()
        for st, per in s["states"].items():
            state_tot[st] += sum(v for n, v in per.items() if n in roles)
        states_out = [{"state": st, "roles": v, "atoms": s["state_atoms"].get(st, 0), "sw": s["state_sw"].get(st, 0)}
                      for st, v in state_tot.most_common(15)]

        # composition of the panel
        comp = {"by_bucket": {b: bb["panel"] for b, bb in by_bucket.items()},
                "by_stage": dict(Counter(companies[n].get("stage") or "unknown" for n in panel).most_common()),
                "by_founded": dict(Counter(str(companies[n].get("founded") or "unknown")[:4] for n in panel).most_common(12)),
                "by_state": dict(Counter(companies[n].get("state") or "unknown" for n in panel).most_common(10))}

        ranked = sorted(changes.items(), key=lambda kv: kv[1])
        pct = {n: (i + 0.5) / len(ranked) for i, (n, _) in enumerate(ranked)} if ranked else {}
        scores = []
        for n in universe:
            sc = 40 * pct.get(n, 0.0) + recency_points(cap, n, m, 25) + recency_points(con, n, m, 20)
            sc += 15 if any(mm == m for mm, _ in mil.get(n, [])) else 0
            scores.append({"company": n, "bucket": companies[n]["bucket"], "score": round(sc, 1),
                           "roles": roles.get(n, 0), "in_hiring_panel": n in pct,
                           "last_capital": (cap.get(n) or [None])[-1], "last_contract": (con.get(n) or [None])[-1]})
        scores.sort(key=lambda x: (-x["score"], -x["roles"]))

        mfg_tot = sum(s["mfg"][n] for n in panel); hw_tot = sum(s["hw"][n] for n in panel)
        sw_tot = sum(s["sw"][n] for n in panel); ga_tot = sum(s["ga"][n] for n in panel)
        atoms = mfg_tot + hw_tot
        fp = first_prints.setdefault(m, {})
        if "hiring_diffusion" not in fp and h_diff is not None and m != cur_month:
            fp["hiring_diffusion"] = round(h_diff, 1); fp["printed"] = today; fp["method"] = METHOD_VERSION
        elif h_diff is not None and m != cur_month and abs(fp.get("hiring_diffusion", h_diff) - h_diff) > 0.05:
            key = f"{m}:{round(h_diff,1)}"
            if not any(r.get("key") == key for r in revisions):
                revisions.append({"key": key, "month": m, "first_print": fp.get("hiring_diffusion"), "revised": round(h_diff, 1),
                                  "on": today, "method": METHOD_VERSION, "reason": "feed refresh / method version"})
        row = {
            "month": m, "is_nowcast": m == cur_month, "asof": snap_dates.get(m, ""), "method": METHOD_VERSION,
            "hiring_panel": n_panel, "hiring_up": up, "hiring_flat": flat, "hiring_down": down,
            "share_up_pct": round(100 * up / n_panel, 1) if n_panel else "", "share_down_pct": round(100 * down / n_panel, 1) if n_panel else "",
            "hiring_diffusion": round(h_diff, 1) if h_diff is not None else "",
            "hiring_ci_lo": ci_lo if ci_lo is not None else "", "hiring_ci_hi": ci_hi if ci_hi is not None else "",
            "hiring_diffusion_first_print": fp.get("hiring_diffusion", ""),
            "board_checks": len(board_checks),
            "open_roles": tot_now, "open_roles_prev": tot_prev,
            "roles_mom_pct": round(100 * (tot_now / tot_prev - 1), 1) if tot_prev else "",
            "manufacturing_roles": mfg_tot, "hardware_roles": hw_tot, "software_roles": sw_tot, "commercial_roles": ga_tot,
            "mfg_roles": atoms, "sw_roles": sw_tot,
            "atoms_bits_ratio": round(atoms / sw_tot, 2) if sw_tot else "",
            "factory_flags": len(factory_flags),
            "capital_diffusion_covered": round(c_diff, 1) if c_diff is not None else "", "capital_panel": c_panel,
            "capital_events_3m": c_ev, "capital_rate_per100_3m": round(cap_rate, 2),
            "contracts_diffusion_covered": round(k_diff, 1) if k_diff is not None else "", "contracts_panel": k_panel,
            "contracts_events_3m": k_ev, "contracts_rate_per100_3m": round(con_rate, 2),
            "milestones_diffusion": round(m_diff, 1) if m_diff is not None else "", "milestone_events": m_n,
            "footprint_diffusion": round(f_diff, 1) if f_diff is not None else "", "footprint_events": f_n,
            "pulse_hiring": round(h_diff, 1) if h_diff is not None else "",
            "pulse_v0_composite": round(composite, 1) if composite is not None else "",
            "components_live": "+".join(live.keys()),
        }
        hist_rows.append(row)
        for bk, bb in sorted(by_bucket.items()):
            d = 50 + (bb["up"] - bb["down"]) / bb["panel"] * 50 if bb["panel"] else None
            at = bb["mfg"] + bb["hw"]
            bucket_rows.append({"month": m, "bucket": bk, "panel": bb["panel"], "up": bb["up"], "down": bb["down"],
                                "hiring_diffusion": round(d, 1) if d is not None else "", "open_roles": bb["roles"],
                                "mfg_roles": at, "sw_roles": bb["sw"], "manufacturing_roles": bb["mfg"], "hardware_roles": bb["hw"],
                                "commercial_roles": bb["ga"], "senior_roles": bb["senior"],
                                "atoms_bits": round(at / bb["sw"], 2) if bb["sw"] else "",
                                "sufficient": bb["panel"] >= MIN_BUCKET})
        movers.sort(key=lambda x: -x["change_pct"])
        json.dump({"month": m, "up": movers[:10], "down": sorted(movers, key=lambda x: x["change_pct"])[:5],
                   "factory_flags": factory_flags}, open(OUT / f"movers_{m}.json", "w"), indent=1)
        json.dump({"month": m, "top": scores[:50]}, open(OUT / f"company_scores_{m}.json", "w"), indent=1)
        json.dump({"month": m, "states": states_out}, open(OUT / f"states_{m}.json", "w"), indent=1)
        json.dump(board_checks, open(OUT / f"board_checks_{m}.json", "w"), indent=1)
        json.dump({"month": m, **comp}, open(OUT / f"composition_{m}.json", "w"), indent=1)
        prev = m

    json.dump(first_prints, open(OUT / "first_prints.json", "w"), indent=1)
    json.dump(revisions, open(OUT / "revisions.json", "w"), indent=1)

    dead_status = sum(1 for c in companies.values() if c["status"] in ("dead", "zombie", "acquired"))
    conf_dead = susp = checked = 0
    p = DATA / "liveness_report.json"
    if p.exists():
        lr = json.load(open(p)); checked = len(lr.get("results", []))
        for r in lr.get("results", []):
            v = r.get("verdict", "")
            if v in ("gone", "acquired_language", "parked", "not_found"):
                conf_dead += 1
            elif v in ("empty_page", "unreachable", "server_error"):
                susp += 1
    mortality = {"db_dead_or_acquired": dead_status, "liveness_checked": checked, "liveness_confirmed_dead_or_acquired": conf_dead,
                 "liveness_suspects": susp, "confirmed_rate_pct": round(100 * conf_dead / checked, 1) if checked else None}

    review = build_review_queue(companies)
    json.dump(review, open(OUT / "review_queue.json", "w"), indent=1)

    with open(OUT / "pulse_history.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hist_rows[0].keys())); w.writeheader(); w.writerows(hist_rows)
    with open(OUT / "pulse_buckets.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(bucket_rows[0].keys())); w.writeheader(); w.writerows(bucket_rows)

    latest = hist_rows[-1]
    lm = latest["month"]
    latest_buckets = [r for r in bucket_rows if r["month"] == lm]
    movers_latest = json.load(open(OUT / f"movers_{lm}.json"))
    scores_latest = json.load(open(OUT / f"company_scores_{lm}.json"))["top"][:25]
    states_latest = json.load(open(OUT / f"states_{lm}.json"))["states"]
    checks_latest = json.load(open(OUT / f"board_checks_{lm}.json"))
    comp_latest = json.load(open(OUT / f"composition_{lm}.json"))
    boards = 0
    p = OUT / "job_boards_discovered.json"
    if p.exists():
        boards = sum(1 for r in json.load(open(p)) if any(c.get("confidence") == "high" for c in r.get("candidates", [])))
    with_board = len([n for n in snaps[lm]["roles"]])
    payload = {"generated": today, "method_version": METHOD_VERSION, "taxonomy_version": TAXONOMY_VERSION,
               "universe": n_universe, "companies_total": len(companies), "companies_with_board": with_board,
               "thresholds": {"up_pct": UP_PCT, "up_abs": UP_ABS, "stale_days": STALE_DAYS, "min_bucket": MIN_BUCKET,
                              "collapse_from": COLLAPSE_FROM, "collapse_to": COLLAPSE_TO, "bootstrap_n": BOOTSTRAP_N},
               "weights": WEIGHTS, "latest": latest, "latest_buckets": latest_buckets, "history": hist_rows,
               "buckets": bucket_rows, "movers": movers_latest, "scores": scores_latest, "states": states_latest,
               "board_checks": checks_latest, "composition": comp_latest, "revisions": revisions,
               "mortality": mortality, "capital_sources": cap_sources, "review_queue_size": len(review),
               "discovered_boards_high": boards}
    json.dump(payload, open(OUT / "pulse_latest.json", "w"), indent=1)
    with open(DATA / "pulse_auto.js", "w") as f:
        f.write("// Auto-generated by scripts/calc_pulse.py — The Build-Out Pulse\n")
        f.write(f"// Generated: {today} · method v{METHOD_VERSION} · taxonomy v{TAXONOMY_VERSION}\n")
        f.write("const PULSE_DATA = " + json.dumps(payload) + ";\n")

    nuc = [r for r in bucket_rows if r["bucket"] == "Nuclear"]
    with open(OUT / "validation.md", "w") as f:
        f.write(f"# Pulse validation — generated {today} (method v{METHOD_VERSION}, taxonomy v{TAXONOMY_VERSION})\n\n")
        f.write("Known events to reproduce: Valar critical 18 Jun 2026; Antares critical at INL Jul 2026; Oklo Groves 5 Aug 2026 (public co., outside panel).\n\n")
        f.write("| month | nuclear panel | diffusion | roles | atoms | sw | senior |\n|---|---|---|---|---|---|---|\n")
        for r in nuc:
            f.write(f"| {r['month']} | {r['panel']} | {r['hiring_diffusion']} | {r['open_roles']} | {r['mfg_roles']} | {r['sw_roles']} | {r['senior_roles']} |\n")
        f.write(f"\nCapital sources merged: {cap_sources}\nMortality: {mortality}\nReview queue size: {len(review)}\nBoard checks (latest): {len(checks_latest)}\nRevisions logged: {len(revisions)}\n")

    print(f"method v{METHOD_VERSION} · taxonomy v{TAXONOMY_VERSION} · universe {n_universe} of {len(companies)} · with board this month {with_board} · capital sources {cap_sources}")
    print("month     nowcast panel  up flat down  diff   CI90        roles   mom%  mfg   hw   sw   ga  a/b  flags chk  cap(n)      con(n)     v0")
    for r in hist_rows:
        print(f"{r['month']}   {'*' if r['is_nowcast'] else ' '}     {r['hiring_panel']:4d} {r['hiring_up']:3d} {r['hiring_flat']:4d} {r['hiring_down']:4d}  {r['hiring_diffusion']:>5}  {r['hiring_ci_lo']!s:>5}–{r['hiring_ci_hi']!s:<5}  {r['open_roles']:5d}  {str(r['roles_mom_pct']):>5}  {r['manufacturing_roles']:4d} {r['hardware_roles']:4d} {r['software_roles']:4d} {r['commercial_roles']:4d}  {str(r['atoms_bits_ratio']):>4}  {r['factory_flags']:4d} {r['board_checks']:3d}  {str(r['capital_diffusion_covered']):>5}({r['capital_panel']:3d})  {str(r['contracts_diffusion_covered']):>5}({r['contracts_panel']:3d})  {r['pulse_v0_composite']}")
    print("\nlatest buckets:")
    for b in latest_buckets:
        print(f"  {b['bucket']:26s} panel={b['panel']:3d} diff={b['hiring_diffusion']!s:>5} roles={b['open_roles']:5d} a/b={b['atoms_bits']!s:>5} senior={b['senior_roles']:3d} {'' if b['sufficient'] else '(insufficient)'}")
    print("\nboard checks:", [(c["company"], c["roles_prev"], c["roles_now"]) for c in checks_latest])
    print("composition by stage:", comp_latest["by_stage"])
    print("top states:", ", ".join(f"{s['state']} {s['roles']}" for s in states_latest[:8]))
    print("factory flags:", movers_latest["factory_flags"][:12])
    print("mortality:", mortality, "| review queue:", len(review), "| discovered boards:", boards, "| revisions:", len(revisions))


if __name__ == "__main__":
    main()
