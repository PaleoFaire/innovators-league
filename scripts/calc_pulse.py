#!/usr/bin/env python3
"""
The Build-Out Pulse — monthly diffusion index of the private hard-tech cohort.
─────────────────────────────────────────────────────────────────────────
Reads only data the repo already collects and turns it into one number a month.

Components (v0 — what is live today):
  hiring     open roles per company from the job-board feed (data/jobs_auto.js), month-end
             snapshots reconstructed from git history for the backfill; constant panel;
             diffusion = 50 + (share up − share down) × 50, up/down = ±10% or ±3 roles
  capital    capital events from data/deals_auto.json + Form D files; on the covered panel
             (companies with any event on record): positive = event in trailing 3 months,
             negative = no event in trailing 12 months; also an all-cohort rate per 100
  contracts  new federal awards from data/gov_contracts_aggregated.json; same rules
  milestones data/pulse/milestones.json (manual, from the Ladder) — counted when present
  footprint  data/pulse/footprint.json (manual/confirmed) — counted when present

Universe: private (no ticker), status active, sectors inside the build-out.
Outputs (data/pulse/): pulse_history.csv, pulse_buckets.csv, movers_<month>.json,
  snapshots/<month>.json, pulse_latest.json, README-METHOD.md; plus data/pulse_auto.js.

Usage:
  python3 scripts/calc_pulse.py                 # backfill from git + nowcast for the current month
  python3 scripts/calc_pulse.py --no-backfill   # current month only (uses stored snapshots)
"""
import csv
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "pulse"
SNAP = OUT / "snapshots"
OUT.mkdir(exist_ok=True)
SNAP.mkdir(exist_ok=True)

UP_PCT, UP_ABS = 0.10, 3          # published thresholds — never tune to make a month look better
WEIGHTS = {"hiring": 30, "capital": 20, "contracts": 20, "milestones": 20, "footprint": 10}
START_MONTH = "2026-04"           # first month with a clean prior snapshot

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

MFG = re.compile(r"technician|machinist|welder|weld|manufactur|production|assembl|fabricat|\bcnc\b|electrician|plant|operator|quality|supply chain|procurement|\btest\b|maintenance|facilit|logistic|tooling|composite|machining|inspector|fitter|rigger|millwright", re.I)
SW = re.compile(r"software|frontend|front-end|backend|back-end|full[- ]stack|devops|data scientist|machine learning|\bml\b|\bai\b|platform engineer|infrastructure engineer|security engineer|product manager|designer|data engineer", re.I)


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT).stdout


def load_companies():
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync("data.js","utf8")+";globalThis.__n=COMPANIES.map(c=>({name:c.name,'
          'sector:c.sector||\'\',subsector:c.subsector||\'\',status:c.status||\'\',ticker:c.ticker||\'\','
          'founded:c.founded||null,state:c.state||\'\'}));",s);console.log(JSON.stringify(s.__n));')
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
        out[c["name"]] = c
    return out


def in_universe(c):
    return c["private"] and c["alive"] and c["bucket"] is not None


# ─── hiring ──────────────────────────────────────────────────────────────

def parse_jobs_js(txt):
    i = txt.find("const JOBS_DATA = ")
    if i < 0:
        return []
    body = txt[i + len("const JOBS_DATA = "):]
    return json.JSONDecoder().raw_decode(body)[0]


def jobs_counts(jobs, companies):
    roles, mfg, sw = Counter(), Counter(), Counter()
    for j in jobs:
        n = j.get("company")
        c = companies.get(n)
        if not c or not in_universe(c):
            continue
        roles[n] += 1
        t = j.get("title", "") or ""
        if MFG.search(t):
            mfg[n] += 1
        elif SW.search(t):
            sw[n] += 1
    return roles, mfg, sw


def month_end_snapshots():
    """{'YYYY-MM': sha} — the last commit of each month that touched the jobs feed."""
    log = sh("git log --format='%H %ad' --date=short -- data/jobs_auto.js").splitlines()
    snap = {}
    for line in log:
        if not line.strip():
            continue
        sha, d = line.split()
        snap.setdefault(d[:7], sha)   # newest-first ⇒ first seen is the month's last commit
    return snap


# ─── capital & contracts ─────────────────────────────────────────────────

def capital_events(companies):
    """{company: sorted list of 'YYYY-MM' event months}"""
    ev = defaultdict(set)
    p = DATA / "deals_auto.json"
    if p.exists():
        for d in json.load(open(p)):
            n, m = d.get("company"), str(d.get("date", ""))[:7]
            if n in companies and re.match(r"\d{4}-\d{2}", m):
                ev[n].add(m)
    for f in ("form_d_filings_auto.json", "form_d_daily_auto.json"):
        p = DATA / f
        if p.exists():
            try:
                for d in json.load(open(p)).get("filings", []):
                    n, m = d.get("company"), str(d.get("filed_date", ""))[:7]
                    if n in companies and re.match(r"\d{4}-\d{2}", m):
                        ev[n].add(m)
            except Exception:
                pass
    return {k: sorted(v) for k, v in ev.items()}


def contract_events(companies):
    ev = defaultdict(set)
    p = DATA / "gov_contracts_aggregated.json"
    if p.exists():
        for r in json.load(open(p)):
            n = r.get("company")
            if n not in companies:
                continue
            for rc in r.get("recentContracts", []):
                m = str(rc.get("date", ""))[:7]
                if re.match(r"\d{4}-\d{2}", m):
                    ev[n].add(m)
    return {k: sorted(v) for k, v in ev.items()}


def manual_events(fname):
    p = OUT / fname
    if not p.exists():
        return {}
    ev = defaultdict(list)
    for r in json.load(open(p)):
        m = str(r.get("date", ""))[:7]
        if r.get("company") and re.match(r"\d{4}-\d{2}", m):
            ev[r["company"]].append((m, 1 if r.get("direction", "up") == "up" else -1))
    return ev


def months_between(a, b):
    ya, ma = map(int, a.split("-")); yb, mb = map(int, b.split("-"))
    return (yb - ya) * 12 + (mb - ma)


def event_diffusion(events, companies, month, lookback_pos=3, lookback_neg=12):
    """Diffusion on the covered panel (companies with any event on record before or in `month`)."""
    up = down = flat = 0
    for n, ms in events.items():
        c = companies.get(n)
        if not c or not in_universe(c):
            continue
        past = [m for m in ms if m <= month]
        if not past:
            continue
        last = past[-1]
        gap = months_between(last, month)
        if gap < lookback_pos:
            up += 1
        elif gap >= lookback_neg:
            down += 1
        else:
            flat += 1
    panel = up + down + flat
    diff = 50 + (up - down) / panel * 50 if panel else None
    events_3m = up
    return diff, panel, events_3m


def manual_diffusion(events, companies, month):
    up = down = 0
    for n, lst in events.items():
        c = companies.get(n)
        if not c or not in_universe(c):
            continue
        for m, dirn in lst:
            if m == month:
                up += dirn > 0
                down += dirn < 0
    n_total = sum(1 for c in companies.values() if in_universe(c))
    if up + down == 0:
        return None, 0
    return 50 + (up - down) / n_total * 50, up + down


# ─── main ────────────────────────────────────────────────────────────────

def main():
    backfill = "--no-backfill" not in sys.argv
    companies = load_companies()
    universe = [n for n, c in companies.items() if in_universe(c)]
    today = date.today().isoformat()
    cur_month = today[:7]

    # hiring snapshots
    snaps = {}
    if backfill:
        for m, sha in sorted(month_end_snapshots().items()):
            if m < "2026-02":
                continue
            jobs = parse_jobs_js(sh(f"git show {sha}:data/jobs_auto.js"))
            snaps[m] = jobs_counts(jobs, companies)
    else:
        for p in sorted(SNAP.glob("*.json")):
            d = json.load(open(p))
            snaps[p.stem] = (Counter(d["roles"]), Counter(d["mfg"]), Counter(d["sw"]))
    # nowcast: current working-tree file for the current month (overrides the month-end snapshot if later)
    jobs_now = parse_jobs_js(open(DATA / "jobs_auto.js", encoding="utf-8").read())
    snaps[cur_month] = jobs_counts(jobs_now, companies)

    cap = capital_events(companies)
    con = contract_events(companies)
    mil = manual_events("milestones.json")
    foot = manual_events("footprint.json")

    months = [m for m in sorted(snaps) if m >= START_MONTH]
    hist_rows, bucket_rows = [], []
    prev = None
    for m in sorted(snaps):
        roles, mfg, sw = snaps[m]
        # persist the snapshot
        json.dump({"month": m, "roles": roles, "mfg": mfg, "sw": sw,
                   "generated": today}, open(SNAP / f"{m}.json", "w"), indent=0)
        if prev is None or m < START_MONTH:
            prev = m
            continue
        p_roles = snaps[prev][0]
        panel = [n for n in roles if n in p_roles]
        up = down = 0
        tot_now = tot_prev = 0
        by_bucket = defaultdict(lambda: {"panel": 0, "up": 0, "down": 0, "roles": 0, "mfg": 0, "sw": 0})
        movers = []
        for n in panel:
            a, b = p_roles[n], roles[n]
            tot_prev += a; tot_now += b
            bk = companies[n]["bucket"]
            bb = by_bucket[bk]; bb["panel"] += 1; bb["roles"] += b; bb["mfg"] += mfg[n]; bb["sw"] += sw[n]
            if b - a >= UP_ABS or (a and (b - a) / a >= UP_PCT):
                up += 1; bb["up"] += 1
            elif a - b >= UP_ABS or (a and (a - b) / a >= UP_PCT):
                down += 1; bb["down"] += 1
            if a >= 5:
                movers.append({"company": n, "bucket": bk, "roles_prev": a, "roles_now": b,
                               "change": b - a, "change_pct": round(100 * (b - a) / a, 1)})
        n_panel = len(panel)
        h_diff = 50 + (up - down) / n_panel * 50 if n_panel else None
        c_diff, c_panel, c_ev = event_diffusion(cap, companies, m)
        k_diff, k_panel, k_ev = event_diffusion(con, companies, m)
        m_diff, m_n = manual_diffusion(mil, companies, m)
        f_diff, f_n = manual_diffusion(foot, companies, m)
        cap_rate = sum(1 for n in universe if any(months_between(x, m) in (0, 1, 2) for x in cap.get(n, []) if x <= m)) / len(universe) * 100
        con_rate = sum(1 for n in universe if any(months_between(x, m) in (0, 1, 2) for x in con.get(n, []) if x <= m)) / len(universe) * 100

        comps = {"hiring": h_diff, "capital": c_diff, "contracts": k_diff, "milestones": m_diff, "footprint": f_diff}
        live = {k: v for k, v in comps.items() if v is not None}
        wsum = sum(WEIGHTS[k] for k in live)
        composite = sum(WEIGHTS[k] * v for k, v in live.items()) / wsum if wsum else None

        mfg_tot = sum(mfg[n] for n in panel); sw_tot = sum(sw[n] for n in panel)
        hist_rows.append({
            "month": m, "is_nowcast": m == cur_month, "hiring_panel": n_panel, "hiring_up": up, "hiring_down": down,
            "hiring_diffusion": round(h_diff, 1) if h_diff is not None else "",
            "open_roles": tot_now, "open_roles_prev": tot_prev,
            "roles_mom_pct": round(100 * (tot_now / tot_prev - 1), 1) if tot_prev else "",
            "mfg_roles": mfg_tot, "sw_roles": sw_tot,
            "atoms_bits_ratio": round(mfg_tot / sw_tot, 2) if sw_tot else "",
            "capital_diffusion_covered": round(c_diff, 1) if c_diff is not None else "", "capital_panel": c_panel,
            "capital_events_3m": c_ev, "capital_rate_per100_3m": round(cap_rate, 2),
            "contracts_diffusion_covered": round(k_diff, 1) if k_diff is not None else "", "contracts_panel": k_panel,
            "contracts_events_3m": k_ev, "contracts_rate_per100_3m": round(con_rate, 2),
            "milestones_diffusion": round(m_diff, 1) if m_diff is not None else "", "milestone_events": m_n,
            "footprint_diffusion": round(f_diff, 1) if f_diff is not None else "", "footprint_events": f_n,
            "pulse_hiring": round(h_diff, 1) if h_diff is not None else "",
            "pulse_v0_composite": round(composite, 1) if composite is not None else "",
            "components_live": "+".join(live.keys()),
        })
        for bk, bb in sorted(by_bucket.items()):
            d = 50 + (bb["up"] - bb["down"]) / bb["panel"] * 50 if bb["panel"] else None
            bucket_rows.append({"month": m, "bucket": bk, "panel": bb["panel"], "up": bb["up"], "down": bb["down"],
                                "hiring_diffusion": round(d, 1) if d is not None else "", "open_roles": bb["roles"],
                                "mfg_roles": bb["mfg"], "sw_roles": bb["sw"],
                                "sufficient": bb["panel"] >= 20})
        movers.sort(key=lambda x: -x["change_pct"])
        json.dump({"month": m, "up": movers[:10], "down": sorted(movers, key=lambda x: x["change_pct"])[:5]},
                  open(OUT / f"movers_{m}.json", "w"), indent=1)
        prev = m

    with open(OUT / "pulse_history.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hist_rows[0].keys())); w.writeheader(); w.writerows(hist_rows)
    with open(OUT / "pulse_buckets.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(bucket_rows[0].keys())); w.writeheader(); w.writerows(bucket_rows)
    latest = hist_rows[-1]
    latest_buckets = [r for r in bucket_rows if r["month"] == latest["month"]]
    payload = {"generated": today, "universe": len(universe), "thresholds": {"up_pct": UP_PCT, "up_abs": UP_ABS},
               "weights": WEIGHTS, "latest": latest, "latest_buckets": latest_buckets, "history": hist_rows,
               "buckets": bucket_rows}
    json.dump(payload, open(OUT / "pulse_latest.json", "w"), indent=1)
    with open(DATA / "pulse_auto.js", "w") as f:
        f.write("// Auto-generated by scripts/calc_pulse.py — The Build-Out Pulse\n")
        f.write(f"// Generated: {today}\n")
        f.write("const PULSE_DATA = " + json.dumps(payload) + ";\n")

    print(f"universe: {len(universe)} private, active, in-lane companies of {len(companies)}")
    print("month     nowcast panel  up  down  hiring  roles   mom%   mfg   sw  a/b   cap_diff(n)  con_diff(n)  v0")
    for r in hist_rows:
        print(f"{r['month']}   {'*' if r['is_nowcast'] else ' '}     {r['hiring_panel']:4d} {r['hiring_up']:3d}  {r['hiring_down']:3d}   "
              f"{r['hiring_diffusion']:>5}  {r['open_roles']:5d}  {str(r['roles_mom_pct']):>5}  {r['mfg_roles']:4d} {r['sw_roles']:4d}  {str(r['atoms_bits_ratio']):>4}   "
              f"{str(r['capital_diffusion_covered']):>5}({r['capital_panel']:3d})   {str(r['contracts_diffusion_covered']):>5}({r['contracts_panel']:3d})  {r['pulse_v0_composite']}")
    print("\nlatest buckets:")
    for b in latest_buckets:
        print(f"  {b['bucket']:26s} panel={b['panel']:3d} diff={b['hiring_diffusion']!s:>5} roles={b['open_roles']:5d} {'' if b['sufficient'] else '(insufficient)'}")


if __name__ == "__main__":
    main()
