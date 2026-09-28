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


def load_verified(m):
    """data/pulse/verified_<month>.json: [{company, list, verified, source, note, by, on}].
    A name in the about-to-build / about-to-raise lists is printed in the external Note only if verified."""
    p = OUT / f"verified_{m}.json"
    if not p.exists():
        return {}
    out = {}
    for r in json.load(open(p)):
        out[(r.get("company"), r.get("list"))] = r
    return out


def main():
    external = "--external" in sys.argv
    D = json.load(open(OUT / "pulse_latest.json"))
    L = D["latest"]; I = D.get("intel", {}); H = D["history"]
    m = L["month"]
    ver = load_verified(m)
    def keep(lst, name):
        """External edition: verified names only; internal draft: all names, unverified ones tagged."""
        out = []
        for x in lst:
            v = ver.get((x["company"], name))
            if external:
                if v and v.get("verified"):
                    out.append(dict(x, verified_source=v.get("source", "")))
            else:
                out.append(dict(x, verification=("verified: " + v.get("source", "")) if v and v.get("verified") else ("REJECTED: " + v.get("note", "") if v and v.get("verified") is False else "UNVERIFIED")))
        return out
    I = dict(I, about_to_build=keep(I.get("about_to_build", []), "about_to_build"), about_to_raise=keep(I.get("about_to_raise", []), "about_to_raise"))
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
        lines.append("| Company | Bucket | Senior mfg roles open | Roles | Last capital event | Status |\n|---|---|---|---|---|---|")
        for x in atb:
            lines.append(f"| {x['company']} | {x['bucket']} | {x['senior_roles_open']} | {x['roles_prev']} → {x['roles_now']} | {x['last_capital_event'] or 'none on record'} | {x.get('verification') or ('verified: ' + x.get('verified_source', '')) } |")
    if atr:
        lines.append("\n**About to raise** — roles up 30%+ in three months, no round on our record in twelve:\n")
        lines.append("| Company | Bucket | Roles 3m ago → now | Growth | Last capital event | Status |\n|---|---|---|---|---|---|")
        for x in atr:
            lines.append(f"| {x['company']} | {x['bucket']} | {x['roles_3m_ago']} → {x['roles_now']} | +{fmt(x['growth_pct'])}% | {x['last_capital_event'] or 'none on record'} | {x.get('verification') or ('verified: ' + x.get('verified_source', ''))} |")
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


    # ── signals, labour, metros, primes ──
    SG = D.get("signals") or {}; LB = D.get("labour") or {}; WG = D.get("wages") or {}; MT = D.get("metros") or {}; PR = D.get("primes") or []
    if SG.get("items"):
        lines.append(f"\n## This week's signals ({SG.get('count', 0)}, week {SG.get('week', '')})\n")
        lines.append("| Signal | Company | Bucket | Evidence |\n|---|---|---|---|")
        for x in SG["items"][:20]:
            ev = " · ".join(f"{k.replace('_', ' ')} {v}" for k, v in (x.get("evidence") or {}).items() if not isinstance(v, list))
            lines.append(f"| {x['type'].replace('_', ' ')} | {x['company']} | {x['bucket']} | {ev} |")
    if LB.get("median_age_days_by_class"):
        cls = LB["median_age_days_by_class"]
        lines.append("\n## The labour bottleneck\n")
        lines.append("Median days a posting has been open, by class: " + ", ".join(f"{k} {v}" for k, v in sorted(cls.items(), key=lambda kv: -kv[1])) + f" (n={LB.get('n_postings_with_true_dates')}, platforms with true posting dates only).")
        if LB.get("hardest_to_fill_titles"):
            lines.append("\nHardest to fill: " + "; ".join(f"{t['title']} ({t['median_age_days']} days, n={t['n']})" for t in LB["hardest_to_fill_titles"][:6]) + ".")
    if WG.get("median_midpoint_by_class"):
        lines.append("\nWhat it pays (median published range midpoint): " + ", ".join(f"{k} ${v:,}" for k, v in sorted(WG["median_midpoint_by_class"].items(), key=lambda kv: -kv[1])) + f" (n={WG.get('n_postings_with_ranges')}; {WG.get('note', '')})")
    if MT.get("top"):
        lines.append("\n## Where the build-out is hiring\n")
        lines.append("Top metros by postings: " + ", ".join(f"{m['metro']} {m['postings']:,} ({m['companies']} cos)" for m in MT["top"][:10]) + ".")
        if MT.get("new_this_quarter"):
            lines.append("New this quarter on the constant set: " + ", ".join(f"{m['metro']} ({m['postings']}: {', '.join(m['companies'][:2])})" for m in MT["new_this_quarter"][:6]) + ".")
    if PR:
        lines.append("\n## Ecosystem Pulse — the primes' partner start-ups\n")
        lines.append("| Prime | Ticker | Partners on panel | Diffusion (4w) | Roles |\n|---|---|---|---|---|")
        for x in PR:
            lines.append(f"| {x['prime']} | {x['ticker']} | {x['on_panel']} of {x['partners_tracked']} | {x['diffusion_4w']} | {x['roles_4w_ago']} → {x['roles_now']} |")

    # ── what to do, by reader ──
    lines.append("\n## What to do with this, by reader\n")
    top_flag = (SG.get("items") or [{}])[0].get("company") if SG.get("items") else (atb[0]["company"] if atb else None)
    lines.append(f"**The public-market investor.** The private-cohort demand signal is strongest in {top_b['bucket'] if top_b else '—'}; the listed names in that bucket of the Build-Out Index are the exposure (Pulse-to-ticker above). Watch award breadth: at {fmt(L['contracts_diffusion_covered'])} and falling, the defence names' federal pipeline is thinner than their narrative.")
    lines.append(f"\n**The VC and the family office.** The about-to-raise table is a call list; {len(atr)} names this month, verified status in the last column. The production-turn signals ({sum(1 for x in (SG.get('items') or []) if x.get('type') == 'production_turn')} this week) are companies moving from prototype to rate — the moment the next round gets priced.")
    lines.append(f"\n**The founder.** Benchmark yourself against your bucket at benchmark.html. The hardest-to-fill roles list is where your competitors are stuck too; the wage table is what they're paying for the same title in the same state.")
    lines.append(f"\n**The vendor selling into the build-out — power, real estate, machine tools, EPC, staffing, finance.** The factory-coming flags and the new-location signals are the companies about to need you, in the metro where they'll need you. {len(flags)} flags and {sum(1 for x in (SG.get('items') or []) if x.get('type') == 'new_location')} new locations this print.")

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
    out = NOTES / (f"{m}-external.md" if external else f"{m}.md")
    out.write_text(md, encoding="utf-8")
    print(f"wrote {out} ({len(md.split())} words){' — external edition: verified names only' if external else ''}")


if __name__ == "__main__":
    main()
