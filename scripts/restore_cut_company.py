#!/usr/bin/env python3
"""Put a company that was cut from the database back in.

    python3 scripts/restore_cut_company.py "Grain Weevil"          # restore it
    python3 scripts/restore_cut_company.py "Grain Weevil" --dry    # show what would change
    python3 scripts/restore_cut_company.py --list                  # what is in the archive

Cut records are kept in data/cut_companies_archive.json (first used for the 7 Oct 2026
high-bar audit). Restoring re-inserts the record exactly as it was at the end of COMPANIES
in data.js, puts back its line in scripts/company_master_list.js (the news and jobs
matcher) and its subsector pin in scripts/assign_subsectors.py, and lifts it from the
curated watcher's EXCLUDE set so the watchers see it again. Scores, graphs and the other
derived files rebuild on their next scheduled runs. Refresh the record's facts before
committing: it is restored as it stood on its cut date.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "data" / "cut_companies_archive.json"
DATA_JS = ROOT / "data.js"
MASTER = ROOT / "scripts" / "company_master_list.js"
SUBSECTORS = ROOT / "scripts" / "assign_subsectors.py"
WATCHER = ROOT / "scripts" / "fetch_curated_lists.py"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    archive = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    entries = archive["companies"]
    if "--list" in sys.argv or not args:
        for e in entries:
            flag = f"  (restored {e['restoredDate']})" if e.get("restoredDate") else ""
            print(f"{e['cutDate']}  {e['name']}{flag}")
        return 0 if entries else 1

    name = args[0]
    entry = next((e for e in entries if e["name"].lower() == name.lower()), None)
    if entry is None:
        close = [e["name"] for e in entries if name.lower() in e["name"].lower()]
        print(f"'{name}' is not in the archive." + (f" Did you mean: {', '.join(close)}?" if close else ""))
        return 1

    data = DATA_JS.read_text(encoding="utf-8")
    start = data.index("const COMPANIES = [")
    if re.search(r'^\s*name:\s*"' + re.escape(entry["name"]) + r'",', data[start:data.index("\n];", start)], re.M):
        print(f"{entry['name']} is already in COMPANIES; nothing to do.")
        return 1

    # 1. data.js: append the archived record at the end of COMPANIES
    end = data.index("\n];", start)
    head = data[:end].rstrip()
    sep = "" if head.endswith(",") else ","
    data = head + sep + "\n  " + entry["js"].strip() + ",\n" + data[end + 1:]

    # 2. news/jobs matcher line
    master = MASTER.read_text(encoding="utf-8")
    if entry.get("masterListLine") and entry["masterListLine"].strip() not in master:
        close_at = master.index("\n];", master.index("const MASTER_COMPANY_LIST = ["))
        master = master[:close_at] + "\n" + entry["masterListLine"] + master[close_at:]

    # 3. subsector pin
    subs = SUBSECTORS.read_text(encoding="utf-8")
    if entry.get("subsectorOverride") and entry["subsectorOverride"] not in subs:
        k = subs.index("OVERRIDES = {")
        k2 = subs.index("\n}", k)
        subs = subs[:k2] + "\n    " + entry["subsectorOverride"] + subs[k2:]

    # 4. lift it from the curated watcher's EXCLUDE set
    watcher = WATCHER.read_text(encoding="utf-8")
    i = watcher.index("EXCLUDE = {")
    j = watcher.index("\n}", i)
    block = re.sub(r'"' + re.escape(entry["excludeKey"]) + r'",\s?', "", watcher[i:j], count=1)
    watcher = watcher[:i] + block + watcher[j:]

    entry["restoredDate"] = date.today().isoformat()
    if dry:
        print(f"Would restore {entry['name']} (cut {entry['cutDate']}): {entry['reason']}")
        return 0
    DATA_JS.write_text(data, encoding="utf-8")
    MASTER.write_text(master, encoding="utf-8")
    SUBSECTORS.write_text(subs, encoding="utf-8")
    WATCHER.write_text(watcher, encoding="utf-8")
    ARCHIVE.write_text(json.dumps(archive, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Restored {entry['name']} (cut {entry['cutDate']}). Update its facts, then run "
          "python3 scripts/validate_data_quality.py before committing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
