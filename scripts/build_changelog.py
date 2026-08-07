#!/usr/bin/env python3
"""Build "This Week in the League" — the auto-generated weekly changelog.

Compares the current data.js COMPANIES array against the version committed
~7 days ago (falling back to 14 days, then the earliest commit touching
data.js) and emits data/changelog_auto.js with a single const:

    const CHANGELOG_WEEKLY = {
      generated, windowDays, baselineSha,
      added:            [{name, sector, oneLine}],
      removed:          [names],
      statusChanges:    [{name, from, to, detail}],
      valuationChanges: [{name, from, to}],
      raisedChanges:    [{name, from, to}],
      stageChanges:     [{name, from, to}],
      il30Changes:      {in: [], out: []},
      events:           [{name, type, text, date}]
    };

Parsing uses the same string-aware brace-walk pattern as
scripts/sync_weekly_metrics.py::load_companies — never a whole-file
name regex, which would match names inside news blobs and comments.

Rendered by changes.html; refreshed daily by daily-data-sync.yml
(guarded so a failure here can never break the sync).
"""

import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "data.js"
OUT_JS = ROOT / "data" / "changelog_auto.js"

EVENT_WINDOW_DAYS = 14   # recentEvent lookback
MAX_EVENTS = 60


# ─── string-aware parsing (pattern from sync_weekly_metrics.load_companies) ───

def _find_matching(text, i, open_ch, close_ch):
    """Return index of the close_ch matching text[i] (an open_ch), skipping strings."""
    depth = 0
    in_str = False
    sc = None
    esc = False
    for k in range(i, len(text)):
        c = text[k]
        if esc:
            esc = False
            continue
        if c == "\\" and in_str:
            esc = True
            continue
        if in_str:
            if c == sc:
                in_str = False
            continue
        if c in "\"'":
            in_str = True
            sc = c
            continue
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return k
    return None


def extract_array_block(text, marker):
    """Inner text of the JS array declared as `<marker> = [...]`, or None."""
    start = text.find(marker)
    if start < 0:
        return None
    i = text.find("[", start)
    if i < 0:
        return None
    end = _find_matching(text, i, "[", "]")
    if end is None:
        return None
    return text[i + 1:end]


def split_entries(block):
    """Split an array body into top-level {...} object strings (string-aware)."""
    entries = []
    idx = 0
    n = len(block)
    while idx < n:
        while idx < n and block[idx] in " \t\n\r,":
            idx += 1
        if idx >= n:
            break
        if block[idx] != "{":
            idx += 1
            continue
        end = _find_matching(block, idx, "{", "}")
        if end is None:
            break
        entries.append(block[idx:end + 1])
        idx = end + 1
    return entries


def _unescape(s):
    return re.sub(r"\\(.)", r"\1", s)


def field_str(entry, key):
    m = re.search(r'\b' + re.escape(key) + r':\s*"((?:[^"\\]|\\.)*)"', entry)
    return _unescape(m.group(1)) if m else None


def extract_recent_event(entry):
    m = re.search(r"\brecentEvent:\s*\{", entry)
    if not m:
        return None
    i = entry.find("{", m.start())
    end = _find_matching(entry, i, "{", "}")
    if end is None:
        return None
    obj = entry[i:end + 1]
    return {
        "type": field_str(obj, "type") or "milestone",
        "text": field_str(obj, "text") or "",
        "date": field_str(obj, "date") or "",
    }


def load_companies(text):
    """name -> extracted fields for every entry in the COMPANIES array."""
    block = extract_array_block(text, "const COMPANIES = [")
    if block is None:
        return None
    companies = {}
    for e in split_entries(block):
        name = field_str(e, "name")
        if not name:
            continue
        companies[name] = {
            "sector": field_str(e, "sector") or "",
            "status": field_str(e, "status") or "",
            "valuation": field_str(e, "valuation") or "",
            "totalRaised": field_str(e, "totalRaised") or "",
            "fundingStage": field_str(e, "fundingStage") or "",
            "insight": field_str(e, "insight") or "",
            "description": field_str(e, "description") or "",
            "recentEvent": extract_recent_event(e),
        }
    return companies


def load_il30(text):
    block = extract_array_block(text, "const INNOVATORS_LEAGUE_30 = [")
    if block is None:
        return []
    return [_unescape(m.group(1))
            for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', block)]


# ─── git baseline ─────────────────────────────────────────────────────────────

def _git(*args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def find_baseline_sha():
    """Commit of data.js from ~7 days ago; fall back to 14 days, then earliest."""
    for days in (7, 14):
        out = _git("rev-list", "-1", f'--before={days} days ago', "HEAD", "--", "data.js")
        if out and out.strip():
            return out.strip(), days
    out = _git("rev-list", "--reverse", "HEAD", "--", "data.js")
    if out and out.strip():
        return out.strip().splitlines()[0], None
    return None, None


def baseline_age_days(sha):
    out = _git("log", "-1", "--format=%ct", sha)
    if not out:
        return None
    then = datetime.fromtimestamp(int(out.strip()), tz=timezone.utc)
    return max(1, round((datetime.now(timezone.utc) - then).total_seconds() / 86400))


# ─── diff helpers ─────────────────────────────────────────────────────────────

def parse_money(s):
    """'$3.8B' / '~$550M' / '$75B IPO' -> value in $M (float), else None."""
    if not s:
        return None
    m = re.search(r"\$?\s*([0-9][0-9,.]*)\s*([BbMmKk])?", s.replace("~", ""))
    if not m:
        return None
    try:
        v = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    unit = (m.group(2) or "M").upper()
    return v * {"B": 1000.0, "M": 1.0, "K": 0.001}[unit]


def _meaningful(s):
    return bool(s) and s.strip().lower() not in ("", "undisclosed", "n/a", "unknown", "tbd", "—", "-")


def changed(old, new):
    """True when the field moved between two meaningful-or-not states."""
    o = (old or "").strip()
    n = (new or "").strip()
    if o.lower() == n.lower():
        return False
    # Ignore pure formatting churn like "$550M" vs "~$550M"
    ov, nv = parse_money(o), parse_money(n)
    if ov is not None and nv is not None and abs(ov - nv) < 1e-9:
        return False
    return _meaningful(o) or _meaningful(n)


def one_line(c):
    text = c.get("insight") or c.get("description") or ""
    text = text.strip()
    if len(text) > 160:
        text = text[:157].rstrip() + "..."
    return text


def parse_event_date(s):
    """'2026-08-05' -> that day; '2026-07' -> last day of that month (so
    month-granularity events stay visible through the following weeks)."""
    if not s:
        return None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.match(r"^(\d{4})-(\d{2})$", s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if mo == 12:
            return date(y, 12, 31)
        try:
            return date(y, mo + 1, 1) - timedelta(days=1)
        except ValueError:
            return None
    return None


# ─── main ─────────────────────────────────────────────────────────────────────

def build():
    new_text = DATA_JS.read_text(encoding="utf-8")
    new_companies = load_companies(new_text)
    if new_companies is None:
        print("::warning::build_changelog: COMPANIES array not found in data.js")
        return None

    sha, _requested = find_baseline_sha()
    old_companies = {}
    old_il30 = []
    window_days = 7
    if sha:
        old_text = _git("show", f"{sha}:data.js")
        if old_text:
            old_companies = load_companies(old_text) or {}
            old_il30 = load_il30(old_text)
            window_days = baseline_age_days(sha) or 7
        else:
            print(f"::warning::build_changelog: git show {sha}:data.js failed")
            sha = None
    else:
        print("::warning::build_changelog: no git baseline for data.js; emitting empty diff")

    new_il30 = load_il30(new_text)

    added = sorted(set(new_companies) - set(old_companies)) if old_companies else []
    removed = sorted(set(old_companies) - set(new_companies)) if old_companies else []

    added_out = [{"name": n,
                  "sector": new_companies[n]["sector"],
                  "oneLine": one_line(new_companies[n])}
                 for n in added]

    status_changes, valuation_changes, raised_changes, stage_changes = [], [], [], []
    for name in sorted(set(new_companies) & set(old_companies)):
        o, n = old_companies[name], new_companies[name]
        if changed(o["status"], n["status"]):
            # Schema backfill guard: when status tracking first rolls out,
            # every company flips "" -> "active". That's noise. A flip from
            # untracked straight to ipo/acquired/dead/zombie IS news.
            backfill_noise = (not o["status"].strip()
                              and n["status"].strip().lower() == "active")
            if not backfill_noise:
                ev = n.get("recentEvent") or {}
                status_changes.append({
                    "name": name,
                    "from": o["status"],
                    "to": n["status"],
                    "detail": ev.get("text", ""),
                })
        if changed(o["valuation"], n["valuation"]):
            valuation_changes.append({"name": name, "from": o["valuation"], "to": n["valuation"]})
        if changed(o["totalRaised"], n["totalRaised"]):
            raised_changes.append({"name": name, "from": o["totalRaised"], "to": n["totalRaised"]})
        if changed(o["fundingStage"], n["fundingStage"]):
            stage_changes.append({"name": name, "from": o["fundingStage"], "to": n["fundingStage"]})

    # Biggest numbers first — the page leads with the headline moves.
    valuation_changes.sort(key=lambda c: parse_money(c["to"]) or 0, reverse=True)
    raised_changes.sort(key=lambda c: parse_money(c["to"]) or 0, reverse=True)

    il30_in = [n for n in new_il30 if n not in old_il30] if old_il30 else []
    il30_out = [n for n in old_il30 if n not in new_il30] if old_il30 else []

    cutoff = date.today() - timedelta(days=EVENT_WINDOW_DAYS)
    events = []
    for name, c in new_companies.items():
        ev = c.get("recentEvent")
        if not ev or not ev.get("text"):
            continue
        d = parse_event_date(ev.get("date", ""))
        if d is None or d < cutoff:
            continue
        events.append({"name": name, "type": ev["type"], "text": ev["text"], "date": ev["date"]})
    events.sort(key=lambda e: (e["date"], e["name"]), reverse=True)
    events = events[:MAX_EVENTS]

    return {
        "generated": date.today().isoformat(),
        "windowDays": window_days,
        "baselineSha": (sha or "")[:12],
        "companiesTracked": len(new_companies),
        "added": added_out,
        "removed": removed,
        "statusChanges": status_changes,
        "valuationChanges": valuation_changes,
        "raisedChanges": raised_changes,
        "stageChanges": stage_changes,
        "il30Changes": {"in": il30_in, "out": il30_out},
        "events": events,
    }


def main():
    changelog = build()
    if changelog is None:
        # Leave any previous changelog_auto.js in place rather than
        # clobbering it with nothing.
        sys.exit(0)

    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(changelog, indent=2, ensure_ascii=False)
    OUT_JS.write_text(
        "// Auto-generated by scripts/build_changelog.py — do not edit by hand.\n"
        "// Rendered by changes.html (This Week in the League).\n"
        f"const CHANGELOG_WEEKLY = {body};\n",
        encoding="utf-8",
    )
    print(f"build_changelog: wrote {OUT_JS.relative_to(ROOT)} "
          f"(window {changelog['windowDays']}d, baseline {changelog['baselineSha'] or 'none'}): "
          f"+{len(changelog['added'])} added, -{len(changelog['removed'])} removed, "
          f"{len(changelog['statusChanges'])} status, {len(changelog['valuationChanges'])} valuation, "
          f"{len(changelog['raisedChanges'])} raised, {len(changelog['stageChanges'])} stage, "
          f"IL30 +{len(changelog['il30Changes']['in'])}/-{len(changelog['il30Changes']['out'])}, "
          f"{len(changelog['events'])} events")


if __name__ == "__main__":
    main()
