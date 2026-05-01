#!/usr/bin/env python3
"""
Split data/comp_sets_auto.js (one 6.5 MB blob keyed by company) into
per-company JSON files at data/comp_sets/<slug>.json.

This way, the company profile page fetches a small file (typically
2-30 KB per company) on demand, instead of forcing every visitor to
download all 870 companies' comp data up front.

Re-runnable; safe to call after every comp_sets regeneration.

Usage:
  python scripts/chunk_comp_sets.py
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "comp_sets_auto.js"
OUT_DIR = ROOT / "data" / "comp_sets"
INDEX_FILE = OUT_DIR / "_index.json"


def slugify(name):
    """Match the slugify pattern company-profile.js / app.js use."""
    s = (name or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def main():
    if not SRC.exists():
        print(f"❌ {SRC} not found")
        return 1

    src_text = SRC.read_text(encoding="utf-8")
    # Strip comments + the const declaration to get JSON
    m = re.search(r"const\s+COMP_SETS_AUTO\s*=\s*", src_text)
    if not m:
        print("❌ Cannot find COMP_SETS_AUTO declaration")
        return 1
    json_str = src_text[m.end():].rstrip().rstrip(";")
    # Remove trailing comments after the }
    last_brace = json_str.rfind("}")
    json_str = json_str[: last_brace + 1]

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse failed: {e}")
        return 1

    by_company = data.get("byCompany", {})
    if not by_company:
        print("❌ No byCompany section")
        return 1

    print(f"  Source: {SRC.relative_to(ROOT)} ({SRC.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"  Companies: {len(by_company)}")

    # Wipe old chunks (in case companies were renamed)
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    # Common metadata at top level of each file (so the company file is self-contained)
    common = {
        "generatedAt": data.get("generatedAt"),
        "model": data.get("model"),
        "totalCompanies": data.get("totalCompanies"),
    }

    index = {}   # slug → {name, file, size}
    total_bytes = 0
    for name, payload in by_company.items():
        slug = slugify(name)
        if not slug:
            continue
        out = {**common, "company": name, "data": payload}
        out_path = OUT_DIR / f"{slug}.json"
        out_path.write_text(json.dumps(out, default=str))
        size = out_path.stat().st_size
        total_bytes += size
        index[slug] = {"name": name, "file": f"comp_sets/{slug}.json", "size": size}

    INDEX_FILE.write_text(json.dumps({
        "generatedAt": data.get("generatedAt"),
        "totalCompanies": len(index),
        "byCompany": index,
    }, indent=2))

    avg = total_bytes / max(1, len(index))
    print(f"  Wrote {len(index)} chunks → {OUT_DIR.relative_to(ROOT)}")
    print(f"  Total size: {total_bytes / 1024 / 1024:.1f} MB (avg {avg/1024:.1f} KB/company)")
    print(f"  Index:      {INDEX_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
