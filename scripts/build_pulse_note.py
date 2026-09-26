#!/usr/bin/env python3
"""
The Pulse Note — the monthly one-pager, drafted from the numbers.
─────────────────────────────────────────────────────────────────────────
Reads data/pulse/pulse_latest.json (with the intel layer) and writes data/pulse/notes/<month>.md:
the finding first, the three lists, the fund table, Pulse-to-ticker, the study, and a Verdict Block
whose data-driven lines are filled in and whose judgement lines are marked for Stephen to sign.

The generator writes the draft; the published Note is the draft after a human has written across it.
Usage: python3 scripts/build_pulse_note.py [--month YYYY-MM]
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "pulse"
NOTES = OUT / "notes"
NOTES.mkdir(exist_ok=True)


def fmt(n, d=1):
    if n in ("", None):
        return "—"
    try:
        return f"{float(n):,.{d}f}" if d else f"{int(round(float(n))):,}"
    except Exception:
        return str(n)


def month_name(m):
    y, mo = m.split("-")
    return date(int(y), int(mo), 1).strftime("%B %Y")


def main():
    D = json.load(open(OUT / "pulse_latest.json"))
    L = D["latest"]; I = D.get("intel", {}); H = D["history"]
    m = L["month"]
    prev = H[-2] if len(H) > 1 else None
    first = H[0]
    direction = "expansion" if float(L["hiring_diffusion"]) > 50 else "contraction"
    move = ""
    if prev:
        d0, d1 = float(prev["hiring_diffusion"]), float(L["hiring_diffusion"])
        move = f", {'up' if d1 > d0 else 'down' if d1 < d0 else 'unchanged'} from {fmt(d0)} in {month_name(prev['month']).split()[0]}"
    roles_since = (int(L["open_roles"]) / int(first["open_roles"]) - 1) * 100 if first.get("open_roles") else None
    ab_first, ab_now = first.get("atoms_bits_ratio"), L.get("atoms_bits_ratio")
    buckets = sorted(D["latest_buckets"], key=lambda b: -(float(b["hiring_diffusion"]) if b["hiring_diffusion"] != "" else 0))
    top_b = buckets[0] if buckets else None
    flags = D.get("movers", {}).get("factory_flags", [])
    movers = D.get("movers", {}).get("up", [])[:3]
    atb = I.get("about_to_build", [])[:8]; atr = I.get("about_to_raise", [])[:8]
    funds = I.get("portfolio_pulse", []); study = I.get("study_hiring_before_raise", {}); expo = I.get("pulse_to_ticker_v0", [])

    lines = []
    lines.append(f"# The Pulse Note — {month_name(m)}")
    lines.append(f"\n*{'Nowcast to ' + L.get('asof', '') if L.get('is_nowcast') else 'Month-end print'}. Generated {D['generated']}. Draft: the numbers are final, the judgement lines are marked for signature.*\n")
    lines.append("## The finding\n")
    lines.append(f"**The Pulse is {fmt(L['hiring_diffusion'])} — {direction}{move}.** {L['hiring_up']} of the {L['hiring_panel']} private hard-tech companies on the constant hiring panel added roles this month; {L['hiring_down']} cut. Open roles on the panel: {fmt(L['open_roles'],0)}, {'+' if float(L['roles_mom_pct'])>=0 else ''}{fmt(L['roles_mom_pct'])}% on the month" + (f", {'+' if roles_since>=0 else ''}{fmt(roles_since,0)}% since {month_name(first['month']).split()[0]}." if roles_since is not None else "."))
    if ab_first and ab_now:
        lines.append(f"\n**Atoms are hiring faster than bits.** Manufacturing, technician and production titles are {fmt(L['mfg_roles'],0)} against {fmt(L['sw_roles'],0)} software, data and product titles — a ratio of {fmt(ab_now,2)}, from {fmt(ab_first,2)} in {month_name(first['month']).split()[0]}.")
    lines.append(f"\n**Capital breadth {fmt(L['capital_diffusion_covered'])} (n={L['capital_panel']}); award breadth {fmt(L['contracts_diffusion_covered'])} (n={L['contracts_panel']}).** {L['capital_events_3m']} companies on the covered panel raised in the last three months; {L['contracts_events_3m']} won a new federal award.")
    if top_b:
        lines.append(f"\n**Strongest bucket: {top_b['bucket']}** — diffusion {fmt(top_b['hiring_diffusion'])} on a panel of {top_b['panel']}, {fmt(top_b['open_roles'],0)} open roles{'' if top_b['sufficient'] else ' (panel under 20 — insufficient, printed anyway)'}.")
    if movers:
        lines.append("\n**Movers:** " + "; ".join(f"{x['company']} {x['roles_prev']} → {x['roles_now']} roles" for x in movers) + ".")
    if flags:
        lines.append(f"\n**Factory-coming flags ({len(flags)}):** {', '.join(flags)} — each posted a senior manufacturing, plant or facilities role this month.")

    lines.append("\n## What the signals say is about to happen\n")
    lines.append("*Signals, not verdicts. Confirm before acting.*\n")
    if atb:
        lines.append("**About to build** — a senior manufacturing hire plus rising roles:\n")
        lines.append("| Company | Bucket | Senior mfg roles open | Roles | Last capital event |\n|---|---|---|---|---|")
        for x in atb:
            lines.append(f"| {x['company']} | {x['bucket']} | {x['senior_roles_open']} | {x['roles_prev']} → {x['roles_now']} | {x['last_capital_event'] or 'none on record'} |")
    if atr:
        lines.append("\n**About to raise** — roles up 30%+ in three months, no round on our record in twelve:\n")
        lines.append("| Company | Bucket | Roles 3m ago → now | Growth | Last capital event |\n|---|---|---|---|---|")
        for x in atr:
            lines.append(f"| {x['company']} | {x['bucket']} | {x['roles_3m_ago']} → {x['roles_now']} | +{fmt(x['growth_pct'])}% | {x['last_capital_event'] or 'none on record'} |")
    lines.append(f"\n**Runway stress:** {I.get('runway_stress_count', 0)} companies (roles down 30%+ in three months, no round in eighteen). Names for Circle and Institutional only.")

    if funds:
        lines.append("\n## Portfolio Pulse — tracked VC portfolios through the same diffusion\n")
        lines.append("| Fund | In-lane tracked | On panel | Diffusion | Roles | Atoms/bits | Raised in 3m |\n|---|---|---|---|---|---|---|")
        for f in funds:
            lines.append(f"| {f['fund']} | {f['tracked_in_lane']} | {f['on_hiring_panel']} | {fmt(f['diffusion'])} | {f['roles_prev']} → {f['roles_now']} | {fmt(f['atoms_bits'],2)} | {f['raised_last_3m']} |")

    if expo:
        lines.append("\n## Pulse-to-ticker (v0, bucket level)\n")
        lines.append("| Bucket | Panel | Diffusion | Open roles | Listed names in the Build-Out Index |\n|---|---|---|---|---|")
        for e in expo:
            lines.append(f"| {e['bucket']} | {e['panel']} | {fmt(e['diffusion'])} | {fmt(e['open_roles'],0)} | {', '.join(e['listed_names_v0']) or '—'} |")

    if study:
        r, o = study.get("raisers", {}), study.get("others", {})
        lines.append("\n## Does hiring precede raising?\n")
        lines.append(f"Companies that raised in the month or the next: median three-month role growth {fmt(r.get('median_growth_pct'))}% (n={r.get('n')}) against {fmt(o.get('median_growth_pct'))}% for the rest (n={o.get('n')}); share that cut roles {fmt(r.get('share_down'))}% vs {fmt(o.get('share_down'))}%. Small n. Re-run monthly; failures published.")

    lines.append("\n## The Verdict Block\n")
    lines.append("| Line | This month |\n|---|---|")
    lines.append(f"| DO | *[Stephen signs — the expression: sleeve or name, size, entry date]* |")
    lines.append(f"| DON'T | *[Stephen signs — the avoid list with the reason]* |")
    lines.append(f"| LOOK AT | {atb[0]['company'] + ' — ' + str(atb[0]['senior_roles_open']) + ' senior manufacturing roles open, ' + str(atb[0]['roles_now']) + ' roles' if atb else '—'} |")
    lines.append(f"| UNDERVALUED | *[Stephen signs — the one thing the market misprices, one number]* |")
    lines.append(f"| WHO GETS DISRUPTED, BY WHEN | *[Stephen signs — incumbent, mechanism, listed name, date]* |")
    lines.append(f"| WHAT CHANGES OUR MIND | The Pulse below 50 for two consecutive prints; award breadth below 40 with capital breadth following |")
    lines.append(f"| CONFIDENCE | {'Low — panel under 100' if int(L['hiring_panel']) < 100 else 'Medium'}; every bucket {'insufficient' if all(not b['sufficient'] for b in buckets) else 'partly sufficient'} |")

    lines.append("\n## The scoreboard call\n")
    lines.append("*[One dated call per quarter, e.g. \"the Pulse stays above 50 through the January print.\" Logged on the public page; graded; losers left up.]*")
    lines.append(f"\n---\n*Method: constant panel; up/down = ±{int(D['thresholds']['up_pct']*100)}% or ±{D['thresholds']['up_abs']} roles; 50 = neutral. Universe {fmt(D['universe'],0)} private, active, in-lane companies. Never included: stock prices, news counts, anything a company paid for. Every founder's benchmark is free at innovatorsleague.com/benchmark.html.*")

    md = "\n".join(lines) + "\n"
    (NOTES / f"{m}.md").write_text(md, encoding="utf-8")
    print(f"wrote {NOTES / (m + '.md')} ({len(md.split())} words)")


if __name__ == "__main__":
    main()
