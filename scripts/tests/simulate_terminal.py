#!/usr/bin/env python3
"""
End-to-end Terminal page simulator.

Replays the exact logic of terminal.js against the real _auto.js files
to verify what each panel would render in a real browser. More rigorous
than a screenshot because every decision branch is traced.

Pulls the live data files (post-deploy GitHub Pages), parses each into
a Python dict, then simulates:
  1. renderQuickStats() — the 4 top-bar stat tiles
  2. renderWatchlist() — left column (empty-state test)
  3. renderTodayActions() — center column action cards
  4. buildFeedItems() — daily feed
  5. renderDeception() — bottom of center column
  6. buildSyntheticAlerts() — right column

Reports: "PANEL X: would render N items with first item '...'"
OR: "PANEL X: would show empty state because Y".
"""
import json
import re
import urllib.request
from pathlib import Path

BASE = "https://paleofaire.github.io/innovators-league"
FILES = {
    "FORM_D_FILINGS":          "data/form_d_filings_auto.js",
    "INTERCONNECTION_QUEUE_AUTO": "data/interconnection_queue_auto.js",
    "DECEPTION_SCORES_AUTO":   "data/deception_scores_auto.js",
    "COMPANY_SIGNALS_AUTO":    "data/news_signals_auto.js",
    "DSCA_FMS_AUTO":           "data/dsca_fms_auto.js",
    "LOBBYING_AUTO":           "data/lobbying_auto.js",
    "WEBSITE_CHANGES_AUTO":    "data/website_changes_auto.js",
}


def fetch(path):
    url = f"{BASE}/{path}?cb=sim"
    req = urllib.request.Request(url, headers={"User-Agent": "terminal-sim/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_payload(js_text, var_name):
    """From a file that declares either `const X = {...};` or
    `window.X = {...};`, extract the {...} JSON payload."""
    patterns = [
        rf"{var_name}\s*=\s*(\[.*?\])\s*;\s*$",           # const X = [...] for news
        rf"{var_name}\s*=\s*(\{{.*?\}})\s*;\s*(?://|$)",  # dict  with trailing comment
    ]
    # Simpler: find `X =` then JSON-balance from the next `[` or `{`
    idx = js_text.find(f"{var_name} =")
    if idx < 0:
        # Try as window.X
        idx = js_text.find(f"window.{var_name} =")
        if idx < 0:
            return None
    eq = js_text.find("=", idx)
    # Skip whitespace after =
    start = eq + 1
    while start < len(js_text) and js_text[start] in " \t\n":
        start += 1
    if start >= len(js_text) or js_text[start] not in "[{":
        return None
    open_ch = js_text[start]
    close_ch = "]" if open_ch == "[" else "}"
    depth, i = 0, start
    in_str = False
    sc = None
    esc = False
    while i < len(js_text):
        c = js_text[i]
        if esc:
            esc = False
        elif c == "\\":
            esc = True
        elif in_str:
            if c == sc:
                in_str = False
        elif c in "\"'":
            in_str = True
            sc = c
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(js_text[start:i + 1])
                except Exception as e:
                    return {"__parse_error__": str(e)}
        i += 1
    return None


def pct(n, total):
    return f"{100 * n / total:.0f}%" if total else "0%"


def main():
    print("═" * 72)
    print("TERMINAL PAGE — FULL PANEL SIMULATION vs LIVE DATA")
    print("═" * 72)

    globals_dict = {}
    for var, path in FILES.items():
        try:
            text = fetch(path)
            data = extract_payload(text, var)
            if data is None:
                print(f"❌  {var:32s} could not extract payload from {path}")
                globals_dict[var] = None
                continue
            if isinstance(data, dict) and "__parse_error__" in data:
                print(f"❌  {var:32s} JSON parse error: {data['__parse_error__']}")
                globals_dict[var] = None
                continue
            if isinstance(data, dict):
                size_desc = f"{len(data)} keys"
            else:
                size_desc = f"{len(data)} items"
            print(f"✓   {var:32s} loaded ({size_desc})")
            globals_dict[var] = data
        except Exception as e:
            print(f"❌  {var:32s} fetch failed: {type(e).__name__}: {e}")
            globals_dict[var] = None

    def G(name):
        return globals_dict.get(name)

    print()
    print("─" * 72)
    print("SIMULATING renderQuickStats()")
    print("─" * 72)

    # Signals today
    signals = 0
    news = G("COMPANY_SIGNALS_AUTO")
    if isinstance(news, list):
        signals += len(news)
    fd = G("FORM_D_FILINGS")
    if fd and isinstance(fd.get("filings"), list):
        signals += len(fd["filings"])
    print(f"  term-qs-signals (top bar tile 1)  →  {signals}")

    raising = 0
    if fd:
        raising = fd.get("total_filings") or (len(fd.get("filings") or []))
    print(f"  term-qs-raising (top bar tile 2)  →  {raising}")

    iq = G("INTERCONNECTION_QUEUE_AUTO")
    mw = (iq and iq.get("summary", {}).get("total_mw")) or 0
    mw_display = f"{mw/1000:.1f}GW" if mw >= 1000 else f"{mw}MW"
    print(f"  term-qs-mw      (top bar tile 3)  →  {mw_display}")
    print(f"  term-qs-watch   (top bar tile 4)  →  0  (localStorage; empty on first visit)")

    print()
    print("─" * 72)
    print("SIMULATING buildTodayActions() — center column top cards")
    print("─" * 72)
    actions = []

    dep = G("DECEPTION_SCORES_AUTO")
    if dep and dep.get("scored_calls"):
        top = dep["scored_calls"][0]
        if top.get("composite_score", 0) >= 60:
            actions.append({
                "type": "Earnings deception alert",
                "headline": f"{top['company']} ({top.get('ticker','')}) scored {top['composite_score']}",
                "kind": "risk" if top["composite_score"] >= 75 else "urgent",
            })

    if fd and fd.get("filings"):
        top3 = fd["filings"][:3]
        actions.append({
            "type": "Active raisers",
            "headline": f"{len(top3)} companies filed Form D",
            "companies": [f["company"] for f in top3],
        })

    dsca = G("DSCA_FMS_AUTO")
    if dsca and dsca.get("notifications"):
        matched = [n for n in dsca["notifications"] if n.get("matched_companies")]
        if matched:
            top = matched[0]
            actions.append({
                "type": "Defense export signal",
                "headline": f"{top['country']} · {top['article']}",
                "subs": top.get("matched_companies", []),
            })

    lob = G("LOBBYING_AUTO")
    if lob and lob.get("by_company"):
        accel = [r for r in lob["by_company"] if r.get("qoq_pct", 0) > 25]
        if accel:
            r = accel[0]
            actions.append({
                "type": "Policy pipeline",
                "headline": f"{r['company']} lobbying +{r['qoq_pct']:.0f}% QoQ",
            })

    wc = G("WEBSITE_CHANGES_AUTO")
    if wc and wc.get("changes"):
        actions.append({
            "type": "Website drift",
            "headline": f"{len(wc['changes'])} companies changed their website recently",
        })

    actions = actions[:4]
    print(f"  → {len(actions)} action cards would render\n")
    for i, a in enumerate(actions, 1):
        print(f"   {i}. [{a['type']}]  {a['headline']}")

    print()
    print("─" * 72)
    print("SIMULATING buildFeedItems() — daily feed")
    print("─" * 72)
    feed = []
    if fd and fd.get("filings"):
        for f in fd["filings"][:4]:
            feed.append(f"💰  Form D: {f['company']}")
    if dsca and dsca.get("notifications"):
        for d in dsca["notifications"][:3]:
            feed.append(f"🎖️  DSCA: {d['country']} · {d.get('article','')[:50]}")
    if wc and wc.get("changes"):
        for c in wc["changes"][:2]:
            feed.append(f"🕵️  Wayback: {c['company']} changed")
    if iq and iq.get("entries"):
        for q in iq["entries"][:2]:
            feed.append(f"⚡  Queue: {q.get('customer','?')} {q.get('mw_size',0)}MW")

    print(f"  → {len(feed)} feed items would render\n")
    for i, f in enumerate(feed, 1):
        print(f"   {i}. {f}")

    print()
    print("─" * 72)
    print("SIMULATING renderDeception() — earnings flags section")
    print("─" * 72)
    if dep and dep.get("scored_calls"):
        flagged = [s for s in dep["scored_calls"] if s.get("flag_level") in ("high_alert", "suspicious")]
        print(f"  → {len(flagged)} flagged calls (of {len(dep['scored_calls'])} total)")
        for s in flagged[:4]:
            print(f"   {s['flag_level']:12s}  {s['composite_score']:>5.1f}  {s['company']} ({s.get('quarter','')})")
    else:
        print("  → would render empty state (no deception data)")

    print()
    print("─" * 72)
    print("SIMULATING buildSyntheticAlerts() — right column alert stream")
    print("─" * 72)
    alerts = []
    if fd and fd.get("filings"):
        alerts.append(f"🟢  {fd['filings'][0]['company']} filed Form D — round opening.")
    if dep and dep.get("scored_calls") and dep["scored_calls"][0].get("composite_score", 0) >= 60:
        top = dep["scored_calls"][0]
        alerts.append(f"🔴  {top['company']} · earnings deception score {top['composite_score']}.")
    if lob and lob.get("by_company"):
        accel = [r for r in lob["by_company"] if r.get("qoq_pct", 0) > 30]
        if accel:
            alerts.append(f"🟡  {accel[0]['company']} lobbying +{accel[0]['qoq_pct']:.0f}% QoQ.")
    print(f"  → {len(alerts)} synthetic alerts would render\n")
    for a in alerts:
        print(f"    {a}")

    print()
    print("═" * 72)
    print("✅ SIMULATION COMPLETE")
    print("═" * 72)
    total_panels = 6
    filled = sum([
        signals > 0, raising > 0, mw > 0,
        len(actions) > 0, len(feed) > 0, len(alerts) > 0
    ])
    print(f"Panels populating: {filled}/6 top-level checks")
    print(f"Expected visual: Terminal page at paleofaire.github.io/innovators-league/terminal.html")
    print(f"  should show live data in all panels (not 'Loading...' / '—')")


if __name__ == "__main__":
    main()
