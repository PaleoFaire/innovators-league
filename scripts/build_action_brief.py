#!/usr/bin/env python3
"""
The Frontier Daily — change-detection digest
─────────────────────────────────────────────────────────────────────────
Turns the pipeline into something you can act on before breakfast.

The problem this solves
───────────────────────
The database is not short of data. Every night it collects Form D filings,
federal contract awards, executive changes, regulatory milestones, patent
velocity, launch manifests and first-party newsroom posts across 1,181
companies. On 2026-08-19 an audit found 13 feeds producing real records that no
page renders at all — 419 podcast mentions, 45 fund-intelligence rows, 30
company announcements — collected nightly and thrown away.

But the deeper problem is not the orphaned feeds. It is that a database
ANSWERS questions and a briefing RAISES them. Nobody opens 34 dashboards in the
morning to discover that Dexterity filed a $120M Form D on the 17th. The
pipeline knew; there was no path from knowing to Stephen.

So this does three things a dashboard cannot:

  1. DIFFS.        Only what changed since the last run. A dashboard shows you
                   the same $11.6B of SpaceX contracts every morning. A
                   briefing shows you the one that landed overnight.
  2. WEIGHTS BY RELATIONSHIP. A $40M round at a company nobody has met is
                   news. The same round at a company whose factory Stephen
                   walked through in July is a phone call he should make today.
                   That distinction cannot be derived from the data — it comes
                   from data/relationships.json.
  3. ROUTES TO A USE. Every item is tagged with where it goes: the fund, a
                   RiskHedge or ROS piece, or a podcast booking. An item that
                   routes nowhere is noise by definition and is dropped.

What it is not
──────────────
It does not summarise with an LLM, and it does not editorialise. Every line is
a fact from a primary feed plus a stated reason it matters, and every reason is
mechanical — "you visited them in July", "this is your fifth
time-to-power item this week", "the fund holds this". Judgement stays with the
reader; the machine only does retrieval, ranking and routing. That also means
it costs nothing to run and cannot hallucinate a round.

Output
──────
  data/action_brief.md     human-readable, for the morning dossier to ingest
  data/action_brief.json   structured, for anything else that wants it
  data/action_brief_state.json  fingerprints already reported (the diff memory)

NOT to be confused with data/daily_digest.json, which is a different product:
generate_daily_digest.py writes that one hourly for brief.html, in a
{sections: {marketMovers, govActivity, regulatory}} shape. This one is
relationship-weighted and routed to an action, and it deliberately reports far
less. Writing to that path would have silently broken the Frontier Daily page.

Usage
─────
  python3 scripts/build_action_brief.py --dry          # print, change nothing
  python3 scripts/build_action_brief.py --since 7      # first run / catch-up
  python3 scripts/build_action_brief.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STATE = DATA / "action_brief_state.json"
OUT_MD = DATA / "action_brief.md"
OUT_JSON = DATA / "action_brief.json"

# How much each kind of event is worth before relationship weighting.
# Form D outranks a press release because it is filed under penalty of perjury
# and lands weeks before the announcement; a GitHub star count is a curiosity.
BASE = {
    "form_d": 45, "contract": 38, "funding": 35, "regulatory": 32,
    "grant": 22, "exec": 20, "launch": 18, "announcement": 16,
    "podcast": 12, "patent": 10, "growth": 8, "github": 4,
}

# What a relationship multiplies it by.
TIER = {"portfolio": 3.2, "visited": 2.6, "covered": 1.7, "il30": 1.5, "": 1.0}

TIER_WHY = {
    "portfolio": "the fund holds this",
    "visited": "you have been on site / interviewed them",
    "covered": "you have written about them",
    "il30": "Innovators League 30",
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def load(name: str):
    for p in (DATA / f"{name}_auto.json", DATA / f"{name}.json"):
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                return None
    return None


def rows(obj, *keys):
    """Payload list out of either a bare list or a wrapper dict."""
    if isinstance(obj, list):
        return obj
    if not isinstance(obj, dict):
        return []
    for k in keys:
        if isinstance(obj.get(k), list):
            return obj[k]
    for v in obj.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    return []


def money(s) -> float:
    """Dollar figure out of '$120M', '104906666', 1.2e8 → float dollars."""
    if isinstance(s, (int, float)):
        return float(s)
    if not s:
        return 0.0
    t = str(s).replace(",", "").strip()
    m = re.match(r"\$?\s*([\d.]+)\s*([BMK])?", t, re.I)
    if not m:
        return 0.0
    try:
        n = float(m.group(1))
    except ValueError:
        return 0.0
    u = (m.group(2) or "").upper()
    return n * {"B": 1e9, "M": 1e6, "K": 1e3}.get(u, 1.0)


def fmt_money(v: float) -> str:
    if v >= 1e9:
        return f"${v/1e9:.2f}B".replace(".00B", "B")
    if v >= 1e6:
        return f"${v/1e6:.0f}M"
    if v >= 1e3:
        return f"${v/1e3:.0f}K"
    return f"${v:.0f}" if v else ""


def companies_from_data_js() -> dict:
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
          '+";globalThis.__n={c:COMPANIES.map(x=>({name:x.name,sector:x.sector||\'\','
          'location:x.location||\'\',founder:x.founder||\'\',stage:x.fundingStage||\'\','
          'raised:x.totalRaised||\'\'})),il30:(typeof INNOVATORS_LEAGUE_30!==\'undefined\'?INNOVATORS_LEAGUE_30:[])};",s);'
          'console.log(JSON.stringify(s.__n));')
    try:
        out = subprocess.run(["node", "-e", js, str(ROOT / "data.js")],
                             capture_output=True, text=True, check=True).stdout
        d = json.loads(out)
        return {"by_norm": {norm(c["name"]): c for c in d["c"]},
                "il30": {norm(n) for n in d["il30"]}}
    except Exception as e:
        print(f"  could not read data.js: {e}")
        return {"by_norm": {}, "il30": set()}


class Relationships:
    def __init__(self, il30: set):
        try:
            r = json.loads((DATA / "relationships.json").read_text())
        except Exception:
            r = {}
        self.tier = {}
        for t in ("covered", "visited", "portfolio"):     # strongest wins
            for n in r.get(t, []):
                self.tier[norm(n)] = t
        for n in il30:
            self.tier.setdefault(n, "il30")
        self.beats = {b: {norm(x) for x in names}
                      for b, names in (r.get("_beats") or {}).items()
                      if not b.startswith("_")}

    def of(self, company: str) -> str:
        return self.tier.get(norm(company), "")

    def beat(self, company: str):
        n = norm(company)
        for b, members in self.beats.items():
            if n in members:
                return b
        return None


def ev(kind, company, headline, detail="", date="", url="", value=0.0, source=""):
    return {"kind": kind, "company": company, "headline": headline, "detail": detail,
            "date": (date or "")[:10], "url": url, "value": value, "source": source}


# ── collectors ───────────────────────────────────────────────────────────
def collect(cutoff: str) -> list:
    out = []

    for r in rows(load("form_d_daily"), "filings") + rows(load("form_d_filings"), "filings"):
        if r.get("filed_date", "") < cutoff:
            continue
        amt = money(r.get("offering_amount"))
        sold = money(r.get("amount_sold"))
        bits = []
        if amt:
            bits.append(f"{fmt_money(amt)} offering")
        if sold:
            bits.append(f"{fmt_money(sold)} already sold"
                        + (" (fully subscribed)" if amt and sold >= amt * 0.99 else ""))
        out.append(ev("form_d", r.get("company", ""),
                      f"filed a Form D",
                      "; ".join(bits) or "amount not disclosed in the filing",
                      r.get("filed_date", ""), r.get("filing_url", ""),
                      max(amt, sold), "SEC EDGAR"))

    for r in rows(load("gov_contracts_aggregated")):
        for c in (r.get("recentContracts") or [])[:3]:
            if str(c.get("date", ""))[:10] < cutoff:
                continue
            v = money(c.get("amount"))
            out.append(ev("contract", r.get("company", ""),
                          f"won {fmt_money(v)} from {c.get('agency','a federal agency')}",
                          (c.get("description") or "")[:150],
                          str(c.get("date", ""))[:10], "", v, "USASpending"))

    for r in rows(load("deals")):
        if str(r.get("date", "")) < cutoff[:7]:
            continue
        v = money(r.get("amount"))
        inv = r.get("investor", "")
        det = f"{r.get('round','round')}"
        if inv and inv.lower() != "undisclosed":
            det += f", led by {inv}"
        if r.get("valuation"):
            det += f", at {r['valuation']}"
        out.append(ev("funding", r.get("company", ""), f"raised {r.get('amount','')}",
                      det, str(r.get("date", "")) + "-01", "", v, "press"))

    for r in rows(load("exec_moves")):
        if r.get("date", "") < cutoff:
            continue
        out.append(ev("exec", r.get("company", ""),
                      r.get("type", "leadership change"),
                      (r.get("description") or "")[:150],
                      r.get("date", ""), r.get("url", ""), 0, "SEC 8-K"))

    for src, label in (("faa_certification", "FAA"), ("nrc_licensing", "NRC"),
                       ("fcc_licenses", "FCC")):
        for r in rows(load(src)):
            d = str(r.get("lastUpdated") or r.get("filing_date") or "")[:10]
            if d < cutoff:
                continue
            who = r.get("company") or r.get("applicant") or ""
            what = (r.get("nextMilestone") or r.get("status") or
                    r.get("purpose") or r.get("stage") or "filing update")
            out.append(ev("regulatory", who, f"{label}: {what}",
                          r.get("design") or r.get("aircraft") or r.get("service_type") or "",
                          d, r.get("url", ""), 0, label))

    for r in rows(load("federal_grants")):
        d = str(r.get("lastUpdated") or "")[:10]
        if d < cutoff:
            continue
        v = money(r.get("amount"))
        out.append(ev("grant", r.get("company", ""),
                      f"{fmt_money(v) or 'a grant'} from {r.get('agency','')}",
                      (r.get("title") or "")[:140], d, r.get("url", ""), v, "grants.gov"))

    for r in rows(load("company_announcements")):
        d = str(r.get("checked_at") or "")[:10]
        if d < cutoff:
            continue
        for h in (r.get("hits") or [])[:2]:
            out.append(ev("announcement", r.get("company", ""),
                          (h.get("title") or "posted to its newsroom")[:110],
                          h.get("summary", "")[:150], d,
                          h.get("url") or r.get("website", ""),
                          money(h.get("amount")), "company newsroom"))

    for r in rows(load("podcast_mentions")):
        d = str(r.get("episode_date") or "")[:10]
        if d < cutoff:
            continue
        out.append(ev("podcast", r.get("company", ""),
                      f"discussed on {r.get('podcast','a podcast')}",
                      (r.get("episode_title") or "")[:130], d, r.get("url", ""), 0, "podcast RSS"))

    for r in rows(load("launch_manifest")):
        d = str(r.get("date") or "")[:10]
        if d < cutoff or not r.get("trackedCompany"):
            continue
        out.append(ev("launch", r.get("trackedCompany", ""),
                      f"payload on {r.get('vehicle','a launch')}",
                      f"{r.get('payload','')} from {r.get('pad','')}".strip(" from"),
                      d, r.get("url", ""), 0, "launch manifest"))

    for r in rows(load("patent_velocity")):
        if not r.get("qoqChangeNum") or r["qoqChangeNum"] < 40:
            continue
        out.append(ev("patent", r.get("company", ""),
                      f"patent filings up {r['qoqChangeNum']}% QoQ",
                      f"{r.get('patentCount','')} total, trend {r.get('trend','')}",
                      datetime.now(timezone.utc).strftime("%Y-%m-%d"), "", 0, "USPTO"))

    return [e for e in out if e["company"]]


# ── routing ──────────────────────────────────────────────────────────────
def route(e: dict, tier: str, beat) -> list:
    """Where does this go? An item that routes nowhere goes below the bar.

    Tightened 2026-08-20 after the first live send. The original rules let 32
    of 40 items claim MEDIA — every regulatory row and every launch, regardless
    of whether Stephen has any angle on the company. A tag that fires on 80% of
    events is not routing, it is a pass-through, and the result was a briefing
    that read like a feed. Ambient events about arm's-length companies now go
    below the bar: still counted, still marked seen, just not asking for his
    attention.
    """
    tags = []
    k, v = e["kind"], e["value"]
    related = tier in ("visited", "covered", "portfolio", "il30")

    if k in ("form_d", "funding"):
        tags.append("FUND")                       # a round is always dealflow
    if k == "contract" and v >= 5e6:
        tags.append("FUND")                       # real revenue changes the case
    if tier == "portfolio":
        tags.append("FUND")                       # anything at all, if we own it

    # A milestone is a story hook only when there is an angle: a relationship,
    # a live editorial thread, or a figure big enough to be the angle itself.
    if k in ("contract", "grant") and (v >= 2e7 or (related and v >= 5e6)):
        tags.append("MEDIA")
    if k in ("regulatory", "launch") and (related or beat):
        tags.append("MEDIA")
    if k == "form_d" and (v >= 5e7 or (related and v >= 1e7)):
        tags.append("MEDIA")
    if k == "announcement" and related:
        tags.append("MEDIA")

    if k == "exec" and (related or beat):
        tags.append("POD")                        # new operator, new booking
    if k == "podcast" and tier in ("visited", "portfolio", "il30"):
        tags.append("POD")                        # they are talking; get them on ours
    if k in ("form_d", "funding") and tier in ("visited", "portfolio"):
        tags.append("POD")                        # warm + newsworthy = easy yes

    return sorted(set(tags))


def score(e: dict, tier: str, beat) -> float:
    s = BASE.get(e["kind"], 5) * TIER.get(tier, 1.0)
    if e["value"] > 0:
        s += min(28.0, 4.6 * math.log10(max(e["value"], 1e5) / 1e5))
    if beat:
        s += 8                                    # lands on a live editorial thread
    try:
        age = (datetime.now(timezone.utc).date()
               - datetime.strptime(e["date"], "%Y-%m-%d").date()).days
        s -= min(20, max(0, age) * 1.3)           # yesterday beats last week
    except Exception:
        pass
    return round(s, 1)


def load_tracker() -> dict:
    """Last-known round per company, for computing what a new filing MEANS.

    "Dexterity filed a $120M Form D" is a fact; "$120M, five months after the
    $95M Series C we have on record" is an insight. The difference is one join
    against data the pipeline already holds, so the brief does the join instead
    of leaving it to the reader — that was the whole complaint about v1.
    """
    out = {}
    for r in rows(load("funding_tracker")):
        n = norm(r.get("company", ""))
        if n:
            out[n] = {"round": r.get("lastRound", ""),
                      "amount": money(r.get("lastRoundAmount", "")),
                      "date": str(r.get("lastRoundDate", ""))[:10]}
    return out


def months_between(a: str, b: str):
    try:
        d1 = datetime.strptime(a[:10], "%Y-%m-%d")
        d2 = datetime.strptime(b[:10], "%Y-%m-%d")
        return round(abs((d2 - d1).days) / 30.4)
    except Exception:
        return None


def build_group(events: list, tier: str, beat, db_rec: dict, tracker: dict) -> dict:
    """One company, one entry. The primary event leads; the rest fold in.

    v1 rendered every event as its own bullet, so Antares' Form D and Antares'
    newsroom post were two items a reader had to connect. The reader should
    never be the join engine.
    """
    events = sorted(events, key=lambda x: -x["score"])
    prim = events[0]
    company = prim["company"]

    # ── context: what the database already knows ────────────────────────
    ctx = []
    tr = tracker.get(norm(company)) or {}
    if prim["kind"] in ("form_d", "funding") and prim["value"] > 0 and tr.get("amount"):
        gap = months_between(tr.get("date", ""), prim["date"])
        ratio = prim["value"] / tr["amount"] if tr["amount"] else 0
        line = f"{fmt_money(tr['amount'])} {tr['round'] or 'round'} on record"
        if gap is not None and 0 < gap < 60:
            line += f" {gap} months ago"
        if 0 < ratio and abs(ratio - 1) > 0.15:
            line += f" — this is {ratio:.1f}× that"
        ctx.append(line)
    elif db_rec.get("raised"):
        stage = db_rec.get("stage") or ""
        ctx.append(f"{stage + ' · ' if stage else ''}{db_rec['raised']} raised to date")

    # ── why line: relationship + thread, no boilerplate ─────────────────
    why_bits = []
    if tier:
        why_bits.append(TIER_WHY[tier])
    if beat:
        why_bits.append(f"your {beat.replace('-', ' ')} thread")

    tags = sorted({t for e in events for t in e["tags"]})
    extra = [e for e in events[1:]]

    g = {"company": company, "tier": tier, "beat": beat, "tags": tags,
         "kind": prim["kind"], "headline": prim["headline"],
         "detail": prim["detail"], "date": prim["date"], "url": prim["url"],
         "value": prim["value"], "source": prim["source"],
         "context": " · ".join(ctx), "why": "; ".join(why_bits),
         "also": [{"headline": e["headline"], "date": e["date"], "url": e["url"],
                   "source": e["source"]} for e in extra[:3]],
         "score": prim["score"] + min(10, 5 * len(extra)),
         "momentum": len(events)}
    return g


KICKER = {  # subject-line verb per kind — short, factual, present tense
    "form_d": "raising {amt}", "funding": "raised {amt}", "contract": "won {amt}",
    "acquisition": "acquired", "grant": "won {amt}", "regulatory": "regulatory milestone",
    "exec": "leadership change", "launch": "launch", "announcement": "news",
    "stealth": "out of stealth", "podcast": "in the conversation",
    "patent": "patent surge",
}


def kicker(g: dict) -> str:
    k = KICKER.get(g["kind"], "update")
    return k.replace("{amt}", fmt_money(g["value"]) if g["value"] else "capital")


def lede_text(g: dict) -> str:
    """Two sentences, every slot filled from data. No adjectives, no LLM."""
    s1 = f"{g['company']} {g['headline']}"
    if g["detail"]:
        s1 += f" — {g['detail']}"
    s2 = []
    if g["context"]:
        s2.append(g["context"])
    if g["why"]:
        s2.append(g["why"])
    if g["momentum"] > 1:
        s2.append(f"{g['momentum']} separate signals in this window")
    # Uppercase only the first character — str.capitalize() lowercases the
    # rest, turning "Series C · $470M" into "Series c · $470m".
    cap = lambda x: x[0].upper() + x[1:] if x else x
    return s1.rstrip(".") + ". " + (". ".join(cap(x) for x in s2) + "." if s2 else "")


def fingerprint(e: dict) -> str:
    return hashlib.sha1(
        f"{e['kind']}|{norm(e['company'])}|{e['date']}|{e['headline'][:60]}".encode()
    ).hexdigest()[:16]


# ── render ───────────────────────────────────────────────────────────────
# Display budget. The first live send put 40 flat bullets in front of Stephen
# and his verdict was exactly right: "a long list of stuff that I have to comb
# through". A briefing's value is inversely related to how much of it there is,
# so the shape is now fixed regardless of how busy the week was:
#
#   THE LEDE      1 story, two sentences, the single most important thing
#   ACT ON        up to 2 more with full context
#   ON THE RADAR  up to 7, one line each
#   BELOW THE BAR one counting line for everything else
#
# Ten entries maximum, and only the top three ask for real attention. A heavy
# news week compresses; it does not sprawl.
LEDE_N, ACT_N, RADAR_N = 1, 2, 7


def radar_line(g: dict) -> str:
    bits = [g["headline"]]
    if g["value"] and fmt_money(g["value"]) not in g["headline"]:
        bits.append(fmt_money(g["value"]))
    if g["context"]:
        bits.append(g["context"])
    elif g["why"]:
        bits.append(g["why"])
    if g["momentum"] > 1:
        bits.append(f"+{g['momentum']-1} more signal{'s' if g['momentum'] > 2 else ''}")
    return " · ".join(bits)


def render_md(brief: dict) -> str:
    d = datetime.now(timezone.utc)
    L = [f"# The Action Brief — {d:%A %-d %B %Y}", ""]

    if not brief["lede"]:
        L += ["Nothing cleared the bar since the last run — the pipeline ran and "
              "found no new signal worth your attention.", "",
              f"_{brief['scanned']} events scanned._"]
        return "\n".join(L)

    lede = brief["lede"]
    L += ["## The lede", ""]
    L.append(lede_text(lede))
    if lede["url"]:
        L.append(f"[source]({lede['url']}) · " + " ".join(f"`{t}`" for t in lede["tags"]))
    L.append("")

    if brief["act_on"]:
        L += ["## Act on", ""]
        for g in brief["act_on"]:
            head = f"**{g['company']}** {g['headline']}"
            if g["url"]:
                head += f" · [source]({g['url']})"
            L.append(f"- {head}  " + " ".join(f"`{t}`" for t in g["tags"]))
            if g["detail"]:
                L.append(f"  {g['detail']}")
            sub = " · ".join(x for x in (g["context"], g["why"]) if x)
            if sub:
                L.append(f"  _{sub}_")
            for a in g["also"]:
                L.append(f"  ↳ also: {a['headline']} ({a['date']})")
            L.append("")

    if brief["radar"]:
        L += ["## On the radar", ""]
        for g in brief["radar"]:
            L.append(f"- **{g['company']}** — {radar_line(g)}")
        L.append("")

    if brief["threads"]:
        L.append("**Threads this week:** " +
                 " · ".join(f"{b.replace('-', ' ')} ×{n}" for b, n in brief["threads"]))
        L.append("")

    bb = brief["below_bar"]
    if bb:
        total = sum(bb.values())
        parts = ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in
                          sorted(bb.items(), key=lambda kv: -kv[1])[:5])
        L.append(f"_Below the bar: {total} more events logged ({parts}) — "
                 f"all in the repo, none needing you._")
        L.append("")

    L += ["---",
          f"_Generated {d:%Y-%m-%d %H:%M} UTC. Every line is a primary-source fact "
          f"joined against the Innovators League database; nothing is model-written._"]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=int, default=3, help="days of feed history to consider")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--max", type=int, default=40, help="cap on reported items")
    args = ap.parse_args()

    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.since)).strftime("%Y-%m-%d")
    db = companies_from_data_js()
    rel = Relationships(db["il30"])

    raw = collect(cutoff)
    print(f"scanned {len(raw)} events since {cutoff}")

    try:
        seen = set(json.loads(STATE.read_text()).get("seen", []))
    except Exception:
        seen = set()

    items, below_bar = [], {}
    # Within-batch as well as across runs. form_d_daily merges into
    # form_d_filings, so reading both surfaces the same filing twice with
    # different filing_url values — identical to a reader, and a briefing that
    # repeats itself is a briefing that gets skimmed.
    batch = set()
    for e in raw:
        fp = fingerprint(e)
        if fp in seen or fp in batch:
            continue
        batch.add(fp)
        # Only report companies we actually track — the feeds mention plenty
        # of others, and a briefing about a company that is not in the
        # database is a briefing the reader cannot act on.
        if norm(e["company"]) not in db["by_norm"]:
            continue
        tier = rel.of(e["company"])
        beat = rel.beat(e["company"])
        tags = route(e, tier, beat)
        e = {**e, "fp": fp, "tier": tier, "beat": beat, "tags": tags,
             "score": score(e, tier, beat)}
        if not tags:
            # Real event, no angle for Stephen. Counted, marked seen, not shown.
            below_bar[e["kind"]] = below_bar.get(e["kind"], 0) + 1
            items.append({**e, "routed": False})
            continue
        items.append({**e, "routed": True})

    # Everything that qualified is considered reported, including the unrouted
    # tail — otherwise the backlog dribbles out over the following days and a
    # fortnight-old filing surfaces as "new" on Friday.
    qualified = {i["fp"] for i in items}
    routed = [i for i in items if i["routed"]]

    # ── group: one company, one entry ───────────────────────────────────
    tracker = load_tracker()
    by_co = {}
    for e in routed:
        by_co.setdefault(norm(e["company"]), []).append(e)
    groups = [build_group(evs, evs[0]["tier"], evs[0]["beat"],
                          db["by_norm"].get(n, {}), tracker)
              for n, evs in by_co.items()]
    groups.sort(key=lambda g: -g["score"])

    shown = groups[:LEDE_N + ACT_N + RADAR_N]
    for g in groups[len(shown):]:
        below_bar[g["kind"]] = below_bar.get(g["kind"], 0) + g["momentum"]

    lede = shown[0] if shown else None
    act_on = shown[LEDE_N:LEDE_N + ACT_N]
    radar = shown[LEDE_N + ACT_N:]

    # Threads: beats with more than one company shown this run.
    beat_counts = {}
    for g in shown:
        if g["beat"]:
            beat_counts[g["beat"]] = beat_counts.get(g["beat"], 0) + 1
    threads = sorted(((b, n) for b, n in beat_counts.items() if n >= 2),
                     key=lambda x: -x[1])

    if lede:
        n_more = len(shown) - 1
        subject = (f"[IL Action Brief] {lede['company']} {kicker(lede)}"
                   + (f" · {n_more} more" if n_more else ""))
    else:
        subject = "[IL Action Brief] quiet day — nothing cleared the bar"

    brief = {"generated_at": datetime.now(timezone.utc).isoformat(),
             "scanned": len(raw), "new": len(routed), "companies": len(groups),
             "subject": subject,
             "fund": sum("FUND" in g["tags"] for g in shown),
             "media": sum("MEDIA" in g["tags"] for g in shown),
             "pod": sum("POD" in g["tags"] for g in shown),
             "lede": lede, "act_on": act_on, "radar": radar,
             "threads": threads, "below_bar": below_bar}

    md = render_md(brief)
    print("\n" + md[:2200] + ("\n…\n" if len(md) > 2200 else ""))

    if args.dry:
        print("DRY RUN — nothing written")
        return 0

    OUT_MD.write_text(md)
    OUT_JSON.write_text(json.dumps(brief, indent=2))
    # Keep the memory bounded — six months of fingerprints is ample and stops
    # the state file growing without limit.
    STATE.write_text(json.dumps(
        {"updated": datetime.now(timezone.utc).isoformat(),
         "seen": sorted(seen | qualified)[-20000:]}, indent=0))
    print(f"\nwrote {OUT_MD.name}, {OUT_JSON.name}, {STATE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
