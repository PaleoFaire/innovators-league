#!/usr/bin/env python3
"""
Pulse Intelligence — the paid layer on top of the Build-Out Pulse.
─────────────────────────────────────────────────────────────────────────
Reads the monthly snapshots and event feeds the Pulse already produces and turns them into
the things a paying reader acts on:

  1. Portfolio Pulse by fund   — every tracked VC portfolio (from the portfolio watcher) run
                                 through the same diffusion: which funds' companies are expanding.
  2. About to raise            — on-panel companies whose roles are up ≥30% over three months with
                                 no capital event on record in the last 12 months.
  3. About to build            — a senior manufacturing / plant / facilities hire this month or last,
                                 plus rising roles.
  4. Runway stress             — roles down ≥30% over three months and no capital event in 18 months.
                                 Names are for paying tiers only; the free page shows the count.
  5. The study: does hiring precede raising? — role growth in the three months before a capital
                                 event versus companies with no event. Published with its n.
  6. Pulse-to-ticker (v0)      — each bucket's diffusion beside the listed names in that bucket of the
                                 Build-Out Index. v1 replaces buckets with the Supplier Map.

Outputs: data/pulse/intel_<month>.json, data/pulse/studies/hiring_before_raise.md,
         data/pulse/portfolio_pulse_<month>.json; merged into data/pulse_auto.js as PULSE_DATA.intel.
"""
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from calc_pulse import (DATA, OUT, SNAP, load_companies, in_universe, capital_events,  # noqa: E402
                        contract_events, months_between, norm_domain, UP_PCT, UP_ABS)

INDEX_CONSTITUENTS = Path("/Users/stephenmcbride/Desktop/Claude/build-out-index/constituents.csv")
INDEX_BUCKET_MAP = {   # Index buckets → Pulse buckets (v0 exposure proxy)
    "Owners of existing capacity": "Power & Grid",
    "Turbines gensets fuel cells": "Power & Grid",
    "Grid and electrical equipment": "Power & Grid",
    "Builders and the permission trade": "Manufacturing & Materials",
    "Nuclear supply chain": "Nuclear",
    "Metals castings forgings welding": "Manufacturing & Materials",
    "Defence and space infrastructure": "Defence",
}


def load_snapshots():
    snaps = {}
    for p in sorted(SNAP.glob("*.json")):
        d = json.load(open(p))
        snaps[p.stem] = d
    return snaps


def diffusion(pairs):
    """pairs: list of (prev, now) role counts → (diffusion, up, down, n)"""
    up = down = 0
    for a, b in pairs:
        if b - a >= UP_ABS or (a and (b - a) / a >= UP_PCT):
            up += 1
        elif a - b >= UP_ABS or (a and (a - b) / a >= UP_PCT):
            down += 1
    n = len(pairs)
    return (round(50 + (up - down) / n * 50, 1) if n else None), up, down, n


def main():
    companies = load_companies()
    snaps = load_snapshots()
    months = sorted(snaps)
    cur, prev = months[-1], months[-2]
    three_back = months[-4] if len(months) >= 4 else months[0]
    cap, _ = capital_events(companies)
    con = contract_events(companies)
    roles_now, roles_prev, roles_3 = snaps[cur]["roles"], snaps[prev]["roles"], snaps[three_back]["roles"]
    senior_now, senior_prev = snaps[cur].get("senior", {}), snaps[prev].get("senior", {})
    senior_2 = snaps[months[-3]].get("senior", {}) if len(months) >= 3 else {}
    panel = [n for n in roles_now if n in roles_prev and in_universe(companies.get(n, {"private": False, "alive": False, "bucket": None}))]
    panel3 = [n for n in roles_now if n in roles_3 and n in companies and in_universe(companies[n])]

    def last_cap(n):
        past = [m for m in cap.get(n, []) if m <= cur]
        return past[-1] if past else None

    # ── 1. Portfolio Pulse by fund ──
    by_domain = {c["domain"]: n for n, c in companies.items() if c["domain"]}
    by_name = {n.lower(): n for n in companies}
    funds_out = []
    p = DATA / "vc_portfolio_snapshots.json"
    if p.exists():
        for key, fund in json.load(open(p)).get("funds", {}).items():
            matched = set()
            for h in fund.get("holdings") or []:
                if not isinstance(h, dict):
                    continue
                n = by_domain.get(norm_domain(h.get("domain") or "")) or by_name.get((h.get("name") or "").lower())
                if n and in_universe(companies[n]):
                    matched.add(n)
            on_panel = [n for n in matched if n in roles_now and n in roles_prev]
            if len(on_panel) < 5:
                continue
            d, up, down, n = diffusion([(roles_prev[x], roles_now[x]) for x in on_panel])
            mfg = sum(snaps[cur]["mfg"].get(x, 0) for x in on_panel); sw = sum(snaps[cur]["sw"].get(x, 0) for x in on_panel)
            raised_3m = sum(1 for x in matched if last_cap(x) and months_between(last_cap(x), cur) <= 2)
            funds_out.append({"fund": fund.get("name", key), "key": key, "tracked_in_lane": len(matched), "on_hiring_panel": n,
                              "diffusion": d, "up": up, "down": down,
                              "roles_now": sum(roles_now[x] for x in on_panel), "roles_prev": sum(roles_prev[x] for x in on_panel),
                              "atoms_bits": round(mfg / sw, 2) if sw else None,
                              "raised_last_3m": raised_3m, "factory_flags": sorted(x for x in on_panel if senior_now.get(x, 0) > senior_prev.get(x, 0))})
    funds_out.sort(key=lambda f: (-(f["diffusion"] or 0), -f["on_hiring_panel"]))

    # ── 2. About to raise ──
    about_to_raise = []
    for n in panel3:
        a, b = roles_3[n], roles_now[n]
        if a >= 5 and (b - a) / a >= 0.30:
            lc = last_cap(n)
            if lc is None or months_between(lc, cur) >= 12:
                about_to_raise.append({"company": n, "bucket": companies[n]["bucket"], "roles_3m_ago": a, "roles_now": b,
                                       "growth_pct": round(100 * (b - a) / a, 1), "last_capital_event": lc,
                                       "senior_mfg_hire": senior_now.get(n, 0) > 0})
    about_to_raise.sort(key=lambda x: -x["growth_pct"])

    # ── 3. About to build ──
    about_to_build = []
    for n in panel:
        flagged = senior_now.get(n, 0) > senior_prev.get(n, 0) or senior_prev.get(n, 0) > senior_2.get(n, 0)
        if flagged and roles_now[n] >= roles_prev[n]:
            about_to_build.append({"company": n, "bucket": companies[n]["bucket"], "state": companies[n].get("state", ""),
                                   "roles_prev": roles_prev[n], "roles_now": roles_now[n], "senior_roles_open": senior_now.get(n, 0),
                                   "last_capital_event": last_cap(n)})
    about_to_build.sort(key=lambda x: (-x["senior_roles_open"], -x["roles_now"]))

    # ── 4. Runway stress ──
    stress = []
    for n in panel3:
        a, b = roles_3[n], roles_now[n]
        if a >= 5 and (a - b) / a >= 0.30:
            lc = last_cap(n)
            if lc is None or months_between(lc, cur) >= 18:
                stress.append({"company": n, "bucket": companies[n]["bucket"], "roles_3m_ago": a, "roles_now": b,
                               "decline_pct": round(100 * (a - b) / a, 1), "last_capital_event": lc})
    stress.sort(key=lambda x: -x["decline_pct"])

    # ── 5. Study: does hiring precede raising? ──
    # For each month M from the 4th snapshot on: companies on the panel at M-3 and M. Raisers = capital event in M or M+1.
    raisers, others = [], []
    for i in range(3, len(months)):
        m, m3 = months[i], months[i - 3]
        r_now, r_3 = snaps[m]["roles"], snaps[m3]["roles"]
        nxt = months[i + 1] if i + 1 < len(months) else None
        for n in r_now:
            if n not in r_3 or n not in companies or not in_universe(companies[n]) or r_3[n] < 5:
                continue
            g = (r_now[n] - r_3[n]) / r_3[n]
            ev = cap.get(n, [])
            raised = (m in ev) or (nxt in ev if nxt else False)
            (raisers if raised else others).append(g)
    def summ(xs):
        return {"n": len(xs), "median_growth_pct": round(100 * statistics.median(xs), 1) if xs else None,
                "share_up_30pct": round(100 * sum(1 for x in xs if x >= 0.30) / len(xs), 1) if xs else None,
                "share_down": round(100 * sum(1 for x in xs if x < 0) / len(xs), 1) if xs else None}
    study = {"raisers": summ(raisers), "others": summ(others), "window": f"{months[0]}..{cur}",
             "definition": "Role growth over the three months to M for companies on the panel with ≥5 roles at M-3; raisers = a capital event in M or M+1."}
    (OUT / "studies").mkdir(exist_ok=True)
    with open(OUT / "studies" / "hiring_before_raise.md", "w") as f:
        f.write(f"# Does hiring precede raising? — generated {date.today().isoformat()}\n\n{study['definition']}\n\n")
        f.write("| Group | n (company-months) | Median 3-month role growth | Share up ≥30% | Share down |\n|---|---|---|---|---|\n")
        for k in ("raisers", "others"):
            s = study[k]; f.write(f"| {k} | {s['n']} | {s['median_growth_pct']}% | {s['share_up_30pct']}% | {s['share_down']}% |\n")
        f.write("\nSmall panel, seven months of history, hindsight-free (events are dated). Re-run every month; publish the failures too.\n")

    # ── 6. Pulse-to-ticker v0 ──
    exposure = []
    if INDEX_CONSTITUENTS.exists():
        buckets_latest = {r["bucket"]: r for r in csv.DictReader(open(OUT / "pulse_buckets.csv")) if r["month"] == cur}
        names_by_pulse_bucket = defaultdict(list)
        for r in csv.DictReader(open(INDEX_CONSTITUENTS)):
            if r["bucket"] == "BENCHMARK":
                continue
            names_by_pulse_bucket[INDEX_BUCKET_MAP.get(r["bucket"], "Other")].append(r["ticker"])
        for b, row in buckets_latest.items():
            exposure.append({"bucket": b, "panel": int(row["panel"]), "diffusion": row["hiring_diffusion"], "open_roles": int(row["open_roles"]),
                             "listed_names_v0": names_by_pulse_bucket.get(b, []), "sufficient": row["sufficient"] == "True"})
        exposure.sort(key=lambda x: -(float(x["diffusion"]) if x["diffusion"] else 0))

    intel = {"month": cur, "generated": date.today().isoformat(), "portfolio_pulse": funds_out, "about_to_raise": about_to_raise[:25],
             "about_to_build": about_to_build[:25], "runway_stress_count": len(stress), "runway_stress_paid": stress[:25],
             "study_hiring_before_raise": study, "pulse_to_ticker_v0": exposure}
    json.dump(intel, open(OUT / f"intel_{cur}.json", "w"), indent=1)
    json.dump({"month": cur, "funds": funds_out}, open(OUT / f"portfolio_pulse_{cur}.json", "w"), indent=1)

    # merge into pulse_auto.js / pulse_latest.json (free page gets counts and fund table; names of stressed companies stay out)
    latest = json.load(open(OUT / "pulse_latest.json"))
    latest["intel"] = {k: v for k, v in intel.items() if k != "runway_stress_paid"}
    json.dump(latest, open(OUT / "pulse_latest.json", "w"), indent=1)
    with open(DATA / "pulse_auto.js", "w") as f:
        f.write("// Auto-generated by scripts/calc_pulse.py + calc_pulse_intel.py — The Build-Out Pulse\n")
        f.write(f"// Generated: {date.today().isoformat()}\n")
        f.write("const PULSE_DATA = " + json.dumps(latest) + ";\n")

    print(f"month {cur}; panel {len(panel)}; 3-month panel {len(panel3)}")
    print("\nPortfolio Pulse by fund:")
    for fnd in funds_out:
        print(f"  {fnd['fund'][:34]:34s} tracked={fnd['tracked_in_lane']:3d} panel={fnd['on_hiring_panel']:3d} diff={fnd['diffusion']!s:>5} roles {fnd['roles_prev']:5d}→{fnd['roles_now']:5d} a/b={fnd['atoms_bits']} raised3m={fnd['raised_last_3m']} flags={len(fnd['factory_flags'])}")
    print("\nAbout to raise (top 10):", [(x["company"], x["roles_3m_ago"], x["roles_now"], x["last_capital_event"]) for x in about_to_raise[:10]])
    print("About to build (top 10):", [(x["company"], x["senior_roles_open"], x["roles_now"]) for x in about_to_build[:10]])
    print("Runway stress count:", len(stress), "| top:", [(x["company"], x["roles_3m_ago"], x["roles_now"]) for x in stress[:6]])
    print("Study:", study)
    print("Pulse-to-ticker v0:", [(e["bucket"], e["diffusion"], e["listed_names_v0"][:4]) for e in exposure])


if __name__ == "__main__":
    main()
