#!/usr/bin/env python3
"""
Pulse Signals — the weekly, event-driven layer of the Build-Out Pulse, plus the exhibits nobody
else can build from this data: the labour bottleneck, the wage index, the metro map, the prime
ecosystems.
─────────────────────────────────────────────────────────────────────────
Weekly snapshots of the job-board feed are reconstructed from git (one per ISO week, last 13
weeks). Every signal is an *event* keyed on (company, type, month) so it fires once, never daily.

Signals (each carries the evidence — the counts, the titles, the locations):
  first_manufacturing_hire   first manufacturing-class posting after ≥4 weeks with none
  production_turn            atoms share of postings up ≥15 points vs 12 weeks ago (≥10 roles)
  new_location               postings in a state the company had no postings in over the prior 12 weeks
  senior_manufacturing_hire  a VP/director/plant/facilities manufacturing role newly posted
  hiring_surge               open roles +30% in 4 weeks (≥10 roles)
  hiring_pullback            open roles −30% in 4 weeks (≥10 roles), excluding board checks
  board_check                ≥20 → ≤3 (or reverse) in 4 weeks — verify the board, never print as contraction

Exhibits (monthly, from the latest snapshot):
  labour   posting age by class (true posting dates only: Lever, Ashby, Workable, BambooHR),
           the hardest-to-fill titles, age by state
  wages    Greenhouse pay-transparency ranges: median midpoint by class and state, top-paid titles
  metros   postings by city/state, and metros new this quarter
  primes   Ecosystem Pulse: each prime's partner startups (prime_supply_chain_auto.json) run through the diffusion

Outputs: data/pulse/signals/<YYYY-Www>.json, signals_latest.json, digests/<YYYY-Www>.md (the Monday email),
         labour_<m>.json, wages_<m>.json, metros_<m>.json, primes_<m>.json; merged into pulse_latest.json / pulse_auto.js.
"""
import json
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from calc_pulse import (DATA, OUT, load_companies, in_universe, capital_events, parse_jobs_js,  # noqa: E402
                        clean_jobs, parse_state, US_STATES, sh)
from pulse_taxonomy import classify, is_senior_manufacturing  # noqa: E402

SIG = OUT / "signals"; SIG.mkdir(exist_ok=True)
DIG = OUT / "digests"; DIG.mkdir(exist_ok=True)
WEEKS = 13
TRUE_DATE_SOURCES = ("lever", "ashby", "workable", "bamboohr")


def weekly_snapshots():
    """{'YYYY-Www': (sha, date)} — last commit of each ISO week touching the jobs feed, last WEEKS weeks."""
    log = sh("git log --format='%H %ad' --date=short -- data/jobs_auto.js").splitlines()
    out = {}
    for line in log:
        if not line.strip():
            continue
        sha, d = line.split()
        y, w, _ = date.fromisoformat(d).isocalendar()
        out.setdefault(f"{y}-W{w:02d}", (sha, d))
    keys = sorted(out)[-WEEKS:]
    return {k: out[k] for k in keys}


KNOWN_CITY_STATE = {
    "san francisco": "CA", "south san francisco": "CA", "los angeles": "CA", "el segundo": "CA", "torrance": "CA", "hawthorne": "CA",
    "long beach": "CA", "huntington beach": "CA", "garden grove": "CA", "gardena": "CA", "irvine": "CA", "san jose": "CA", "mountain view": "CA",
    "palo alto": "CA", "menlo park": "CA", "burlingame": "CA", "redwood city": "CA", "san diego": "CA", "oakland": "CA", "berkeley": "CA",
    "sunnyvale": "CA", "santa clara": "CA", "fremont": "CA", "hayward": "CA", "alameda": "CA", "carlsbad": "CA", "pasadena": "CA",
    "austin": "TX", "houston": "TX", "dallas": "TX", "bastrop": "TX", "starbase": "TX", "brownsville": "TX", "san antonio": "TX", "fort worth": "TX",
    "denver": "CO", "boulder": "CO", "broomfield": "CO", "colorado springs": "CO", "louisville": "CO",
    "seattle": "WA", "redmond": "WA", "kent": "WA", "bellevue": "WA", "everett": "WA",
    "new york": "NY", "new york city": "NY", "brooklyn": "NY", "boston": "MA", "cambridge": "MA", "somerville": "MA", "burlington": "MA",
    "washington": "DC", "arlington": "VA", "reston": "VA", "huntsville": "AL", "cape canaveral": "FL", "orlando": "FL", "miami": "FL",
    "phoenix": "AZ", "tempe": "AZ", "mesa": "AZ", "chandler": "AZ", "salt lake city": "UT", "provo": "UT", "reno": "NV", "sparks": "NV",
    "las vegas": "NV", "portland": "OR", "detroit": "MI", "pittsburgh": "PA", "philadelphia": "PA", "chicago": "IL", "atlanta": "GA",
    "raleigh": "NC", "durham": "NC", "charlotte": "NC", "columbus": "OH", "cleveland": "OH", "minneapolis": "MN", "st. louis": "MO",
    "kansas city": "MO", "nashville": "TN", "knoxville": "TN", "oak ridge": "TN", "albuquerque": "NM", "santa fe": "NM", "idaho falls": "ID",
    "boise": "ID", "madison": "WI", "milwaukee": "WI", "richland": "WA", "kennewick": "WA", "greenville": "SC", "charleston": "SC",
}


def city_of(location):
    if not location:
        return None
    loc = location.split("|")[0].strip()
    parts = [p.strip() for p in loc.split(",")]
    if not parts or not parts[0]:
        return None
    city = re.sub(r"\s+", " ", parts[0]).strip()
    if city.lower() in ("remote", "united states", "usa", "us", "united states of america"):
        return None
    st = parse_state(loc)
    if not st or st == "REMOTE":
        st = KNOWN_CITY_STATE.get(city.lower())
    if city.lower() == "new york city":
        city = "New York"
    return f"{city}, {st}" if st else city


def per_company(jobs, companies):
    roles, atoms, states, cities, senior, mfg = Counter(), Counter(), defaultdict(Counter), defaultdict(Counter), Counter(), Counter()
    for j in jobs:
        n = j.get("company"); c = companies.get(n)
        if not c or not in_universe(c):
            continue
        roles[n] += 1
        k = classify(j.get("title", ""))
        if k in ("manufacturing", "hardware"):
            atoms[n] += 1
        if k == "manufacturing":
            mfg[n] += 1
        if is_senior_manufacturing(j.get("title", "")):
            senior[n] += 1
        st = parse_state(j.get("location"))
        if st and st != "REMOTE":
            states[n][st] += 1
        ct = city_of(j.get("location"))
        if ct:
            cities[n][ct] += 1
    return {"roles": roles, "atoms": atoms, "mfg": mfg, "senior": senior, "states": states, "cities": cities}


def main():
    companies = load_companies()
    today = date.today().isoformat()
    cur_month = today[:7]
    cap, _ = capital_events(companies)
    weeks = weekly_snapshots()
    keys = sorted(weeks)
    snaps = {}
    for k in keys:
        sha, d = weeks[k]
        jobs = clean_jobs(parse_jobs_js(sh(f"git show {sha}:data/jobs_auto.js")), d)
        snaps[k] = per_company(jobs, companies)
    # current working tree as the latest week
    jobs_now = clean_jobs(parse_jobs_js(open(DATA / "jobs_auto.js", encoding="utf-8").read()), today)
    y, w, _ = date.today().isocalendar()
    cur_key = f"{y}-W{w:02d}"
    snaps[cur_key] = per_company(jobs_now, companies); keys = sorted(set(keys) | {cur_key})
    cur = snaps[cur_key]
    def back(n_weeks):
        idx = max(0, len(keys) - 1 - n_weeks)
        return snaps[keys[idx]]
    w4, w12 = back(4), back(12)
    prev = back(1)

    # ── signals ──
    # A signal fires once per (company, type, month). Re-running inside the same week is idempotent:
    # that week's entries are dropped and recomputed, so CI and local runs agree.
    seen_path = OUT / "signals_seen.json"
    seen_rows = [tuple(x) for x in json.load(open(seen_path))] if seen_path.exists() else []
    seen_rows = [r for r in seen_rows if len(r) == 4 and r[3] != cur_key]
    seen = {r[:3] for r in seen_rows}
    signals = []
    def emit(n, typ, evidence):
        key = (n, typ, cur_month)
        if key in seen:
            return
        seen.add(key); seen_rows.append((n, typ, cur_month, cur_key))
        signals.append({"company": n, "bucket": companies[n]["bucket"], "state": companies[n].get("state", ""),
                        "type": typ, "week": cur_key, "evidence": evidence,
                        "last_capital_event": (cap.get(n) or [None])[-1]})
    for n, r in cur["roles"].items():
        r4, r12 = w4["roles"].get(n), w12["roles"].get(n)
        # board check first
        if r4 is not None and ((r4 >= 20 and r <= 3) or (r4 <= 3 and r >= 20)):
            emit(n, "board_check", {"roles_4w_ago": r4, "roles_now": r}); continue
        if r4 is not None and r4 >= 10 and (r - r4) / r4 >= 0.30:
            emit(n, "hiring_surge", {"roles_4w_ago": r4, "roles_now": r, "change_pct": round(100 * (r - r4) / r4, 1)})
        if r4 is not None and r4 >= 10 and (r4 - r) / r4 >= 0.30:
            emit(n, "hiring_pullback", {"roles_4w_ago": r4, "roles_now": r, "change_pct": round(-100 * (r4 - r) / r4, 1)})
        # first manufacturing hire: mfg now ≥1, zero in each of the prior 4 weekly snapshots
        if cur["mfg"].get(n, 0) >= 1 and all(snaps[k]["mfg"].get(n, 0) == 0 for k in keys[-5:-1]) and all(n in snaps[k]["roles"] for k in keys[-5:-1]):
            emit(n, "first_manufacturing_hire", {"manufacturing_roles_now": cur["mfg"][n], "roles_now": r})
        # production turn
        if r >= 10 and r12:
            share_now = cur["atoms"].get(n, 0) / r; share_12 = w12["atoms"].get(n, 0) / r12
            if share_now - share_12 >= 0.15:
                emit(n, "production_turn", {"atoms_share_now_pct": round(100 * share_now, 1), "atoms_share_12w_ago_pct": round(100 * share_12, 1), "roles_now": r})
        # senior manufacturing hire
        if cur["senior"].get(n, 0) > prev["senior"].get(n, 0):
            emit(n, "senior_manufacturing_hire", {"senior_roles_now": cur["senior"][n]})
        # new location (state) — ≥2 postings there now, none in the prior 12 weekly snapshots
        prior_states = set()
        for k in keys[-13:-1]:
            prior_states |= set(snaps[k]["states"].get(n, {}).keys())
        for st, cnt in cur["states"].get(n, {}).items():
            if cnt >= 2 and prior_states and st not in prior_states:
                emit(n, "new_location", {"state": st, "state_name": US_STATES.get(st, st), "postings_there": cnt,
                                         "cities": [c for c in cur["cities"].get(n, {}) if c.endswith(", " + st)][:3]})
    json.dump(sorted(seen_rows), open(seen_path, "w"))
    sig_out = {"week": cur_key, "generated": today, "count": len(signals),
               "by_type": dict(Counter(s["type"] for s in signals)), "signals": signals}
    json.dump(sig_out, open(SIG / f"{cur_key}.json", "w"), indent=1)
    json.dump(sig_out, open(OUT / "signals_latest.json", "w"), indent=1)

    # ── labour bottleneck (true posting dates only) ──
    ages_by_class, ages_by_title, ages_by_state = defaultdict(list), defaultdict(list), defaultdict(list)
    for j in jobs_now:
        n = j.get("company"); c = companies.get(n)
        if not c or not in_universe(c) or j.get("source") not in TRUE_DATE_SOURCES or not j.get("posted"):
            continue
        try:
            age = (date.today() - date.fromisoformat(j["posted"][:10])).days
        except ValueError:
            continue
        if age < 0 or age > 365:
            continue
        k = classify(j.get("title", ""))
        t = re.sub(r"\s+", " ", re.sub(r"\b(sr\.?|senior|staff|principal|lead|jr\.?|junior|ii|iii|iv)\b", "", (j.get("title") or "").lower())).strip(" ,-–")
        ages_by_class[k].append(age); ages_by_title[t].append(age)
        st = parse_state(j.get("location"))
        if st and st != "REMOTE":
            ages_by_state[st].append(age)
    labour = {
        "month": cur_month, "n_postings_with_true_dates": sum(len(v) for v in ages_by_class.values()),
        "median_age_days_by_class": {k: int(statistics.median(v)) for k, v in ages_by_class.items() if len(v) >= 20},
        "hardest_to_fill_titles": sorted(({"title": t, "n": len(v), "median_age_days": int(statistics.median(v))} for t, v in ages_by_title.items() if len(v) >= 6),
                                         key=lambda x: -x["median_age_days"])[:20],
        "most_posted_titles": sorted(({"title": t, "n": len(v), "median_age_days": int(statistics.median(v))} for t, v in ages_by_title.items()),
                                     key=lambda x: -x["n"])[:20],
        "median_age_days_by_state": {s: int(statistics.median(v)) for s, v in sorted(ages_by_state.items(), key=lambda kv: -len(kv[1])) if len(v) >= 30},
        "note": "Ages from platforms that expose the original posting date (Lever, Ashby, Workable, BambooHR). Greenhouse exposes a refresh date and is excluded.",
    }
    json.dump(labour, open(OUT / f"labour_{cur_month}.json", "w"), indent=1)

    # ── wages (Greenhouse pay transparency) ──
    mids_by_class, mids_by_state, mids_by_title = defaultdict(list), defaultdict(list), defaultdict(list)
    for j in jobs_now:
        n = j.get("company"); c = companies.get(n)
        if not c or not in_universe(c):
            continue
        lo, hi = j.get("salaryMin"), j.get("salaryMax")
        if not (lo and hi) or (j.get("salaryCurrency") or "USD") != "USD":
            continue
        try:
            lo, hi = float(lo), float(hi)
        except (TypeError, ValueError):
            continue
        if lo < 20000 or hi > 1500000 or hi < lo:
            continue
        mid = (lo + hi) / 2
        k = classify(j.get("title", ""))
        t = re.sub(r"\s+", " ", re.sub(r"\b(sr\.?|senior|staff|principal|lead|jr\.?|junior|ii|iii|iv)\b", "", (j.get("title") or "").lower())).strip(" ,-–")
        mids_by_class[k].append(mid); mids_by_title[t].append(mid)
        st = parse_state(j.get("location"))
        if st and st != "REMOTE":
            mids_by_state[st].append(mid)
    wages = {
        "month": cur_month, "n_postings_with_ranges": sum(len(v) for v in mids_by_class.values()),
        "median_midpoint_by_class": {k: int(statistics.median(v)) for k, v in mids_by_class.items() if len(v) >= 15},
        "median_midpoint_by_state": {s: int(statistics.median(v)) for s, v in sorted(mids_by_state.items(), key=lambda kv: -len(kv[1])) if len(v) >= 25},
        "top_paid_titles": sorted(({"title": t, "n": len(v), "median_midpoint": int(statistics.median(v))} for t, v in mids_by_title.items() if len(v) >= 4),
                                  key=lambda x: -x["median_midpoint"])[:15],
        "most_common_paid_titles": sorted(({"title": t, "n": len(v), "median_midpoint": int(statistics.median(v))} for t, v in mids_by_title.items() if len(v) >= 4),
                                          key=lambda x: -x["n"])[:15],
        "note": "Greenhouse postings with a published USD range (pay-transparency states over-represented: CA, CO, NY, WA). Midpoint of the range.",
    }
    json.dump(wages, open(OUT / f"wages_{cur_month}.json", "w"), indent=1)

    # ── metros ──  ("new this quarter" is judged on the constant set of companies present 12 weeks ago,
    # so coverage growth never masquerades as expansion)
    metro_now, metro_12, metro_now_const = Counter(), Counter(), Counter()
    const_set = set(cur["cities"]) & set(w12["roles"])
    for n, cts in cur["cities"].items():
        for ct, v in cts.items():
            metro_now[ct] += v
            if n in const_set:
                metro_now_const[ct] += v
    for n, cts in w12["cities"].items():
        for ct, v in cts.items():
            metro_12[ct] += v
    companies_by_metro, const_companies_by_metro = defaultdict(set), defaultdict(set)
    for n, cts in cur["cities"].items():
        for ct in cts:
            companies_by_metro[ct].add(n)
            if n in const_set:
                const_companies_by_metro[ct].add(n)
    def is_us_metro(m):
        return bool(re.search(r", ([A-Z]{2})$", m)) and m[-2:] in US_STATES
    metros = {"month": cur_month, "constant_set_size": len(const_set),
              "top": [{"metro": m, "postings": v, "companies": len(companies_by_metro[m]), "postings_12w_ago": metro_12.get(m, 0)}
                      for m, v in metro_now.most_common() if is_us_metro(m)][:30],
              "new_this_quarter": [{"metro": m, "postings": v, "companies": sorted(const_companies_by_metro[m])[:5]}
                                   for m, v in metro_now_const.most_common() if v >= 5 and metro_12.get(m, 0) == 0 and is_us_metro(m)][:15]}
    json.dump(metros, open(OUT / f"metros_{cur_month}.json", "w"), indent=1)

    # ── prime ecosystems ──
    primes = []
    p = DATA / "prime_supply_chain_auto.json"
    if p.exists():
        for pr in json.load(open(p)):
            names = [x.get("company") for x in pr.get("portfolio", []) if x.get("company") in companies and in_universe(companies[x["company"]])]
            on_panel = [n for n in names if n in cur["roles"] and n in w4["roles"]]
            if len(on_panel) < 2:
                continue
            up = sum(1 for n in on_panel if cur["roles"][n] - w4["roles"][n] >= 3 or (w4["roles"][n] and (cur["roles"][n] - w4["roles"][n]) / w4["roles"][n] >= 0.10))
            down = sum(1 for n in on_panel if w4["roles"][n] - cur["roles"][n] >= 3 or (w4["roles"][n] and (w4["roles"][n] - cur["roles"][n]) / w4["roles"][n] >= 0.10))
            primes.append({"prime": pr.get("prime"), "ticker": pr.get("ticker"), "partners_tracked": len(names), "on_panel": len(on_panel),
                           "diffusion_4w": round(50 + (up - down) / len(on_panel) * 50, 1),
                           "roles_now": sum(cur["roles"][n] for n in on_panel), "roles_4w_ago": sum(w4["roles"][n] for n in on_panel),
                           "partners": sorted(on_panel)[:8]})
    primes.sort(key=lambda x: -x["diffusion_4w"])
    json.dump({"month": cur_month, "primes": primes}, open(OUT / f"primes_{cur_month}.json", "w"), indent=1)

    # ── Monday digest ──
    lines = [f"# Pulse Signals — week {cur_key} (generated {today})", ""]
    lines.append(f"{len(signals)} new signals this week across {len(set(s['company'] for s in signals))} companies. Signals are events derived from public job boards; each fires once. Verify before acting.\n")
    order = ["senior_manufacturing_hire", "production_turn", "first_manufacturing_hire", "new_location", "hiring_surge", "hiring_pullback", "board_check"]
    titles = {"senior_manufacturing_hire": "Factory coming — senior manufacturing / plant / facilities hires",
              "production_turn": "Production turn — atoms share of postings up 15+ points in 12 weeks",
              "first_manufacturing_hire": "First manufacturing hire",
              "new_location": "New location — postings in a state the company wasn't hiring in",
              "hiring_surge": "Hiring surge — open roles +30% in four weeks",
              "hiring_pullback": "Hiring pullback — open roles −30% in four weeks",
              "board_check": "Board checks — verify before reading as contraction"}
    for t in order:
        items = [s for s in signals if s["type"] == t]
        if not items:
            continue
        lines.append(f"## {titles[t]} ({len(items)})\n")
        for s in items[:15]:
            ev = ", ".join(f"{k} {v}" for k, v in s["evidence"].items() if not isinstance(v, list))
            lines.append(f"- **{s['company']}** ({s['bucket']}{', ' + s['state'] if s['state'] else ''}) — {ev}" + (f"; last capital event {s['last_capital_event']}" if s['last_capital_event'] else "; no capital event on record"))
        lines.append("")
    if metros["new_this_quarter"]:
        lines.append("## Metros new this quarter\n")
        for m in metros["new_this_quarter"][:8]:
            lines.append(f"- {m['metro']}: {m['postings']} postings ({', '.join(m['companies'][:3])})")
        lines.append("")
    if labour["hardest_to_fill_titles"]:
        lines.append("## Hardest-to-fill roles this month (median days open)\n")
        for t in labour["hardest_to_fill_titles"][:8]:
            lines.append(f"- {t['title']} — {t['median_age_days']} days (n={t['n']})")
        lines.append("")
    lines.append("---\n*The Build-Out Pulse · signals layer · one email a week, only when something changed. Reply within two hours during US hours for licence holders.*")
    (DIG / f"{cur_key}.md").write_text("\n".join(lines), encoding="utf-8")
    (DIG / "latest.md").write_text("\n".join(lines), encoding="utf-8")

    # ── merge into pulse_latest / pulse_auto.js ──
    latest = json.load(open(OUT / "pulse_latest.json"))
    latest["signals"] = {"week": cur_key, "count": len(signals), "by_type": sig_out["by_type"],
                         "items": [s for s in signals if s["type"] != "hiring_pullback"][:40],
                         "pullbacks_count": sum(1 for s in signals if s["type"] == "hiring_pullback")}
    latest["labour"] = labour; latest["wages"] = wages; latest["metros"] = metros; latest["primes"] = primes
    json.dump(latest, open(OUT / "pulse_latest.json", "w"), indent=1)
    with open(DATA / "pulse_auto.js", "w") as f:
        f.write("// Auto-generated by scripts/calc_pulse.py + calc_pulse_intel.py + calc_pulse_signals.py — The Build-Out Pulse\n")
        f.write(f"// Generated: {today}\n")
        f.write("const PULSE_DATA = " + json.dumps(latest) + ";\n")

    print(f"weeks: {keys[0]}..{cur_key}; signals this week: {len(signals)} {sig_out['by_type']}")
    for s in signals[:25]:
        print(f"  {s['type']:26s} {s['company']:32s} {s['evidence']}")
    print("labour:", labour["median_age_days_by_class"], "| n=", labour["n_postings_with_true_dates"])
    print("hardest to fill:", [(t["title"], t["median_age_days"], t["n"]) for t in labour["hardest_to_fill_titles"][:8]])
    print("wages by class:", wages["median_midpoint_by_class"], "| n=", wages["n_postings_with_ranges"])
    print("wages by state:", wages["median_midpoint_by_state"])
    print("top metros:", [(m["metro"], m["postings"], m["companies"]) for m in metros["top"][:12]])
    print("new metros:", [(m["metro"], m["postings"]) for m in metros["new_this_quarter"][:8]])
    print("primes:", [(p["prime"], p["on_panel"], p["diffusion_4w"], p["roles_4w_ago"], p["roles_now"]) for p in primes])


if __name__ == "__main__":
    main()
