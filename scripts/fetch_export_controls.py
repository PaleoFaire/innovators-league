#!/usr/bin/env python3
"""
Export Controls / Entity List Watch
─────────────────────────────────────────────────────────────────────────
Monitors three US government restricted-party lists that, when they
touch a frontier-tech company, constitute MATERIAL events:

  1. BIS Entity List          — Department of Commerce export-control list
  2. BIS Denied Persons List  — companies barred from US exports
  3. OFAC SDN List            — Treasury specially designated nationals
  4. OFAC Consolidated List   — all non-SDN OFAC restrictions

The value prop:
  • These lists move **weekly**. When a company (or its supplier) hits
    one, gov contracts pause, exports freeze, investors panic.
  • No competitor (BuildList, CB Insights, PitchBook, Crunchbase)
    systematically tracks this. It's pure defense / national-security
    intelligence — exactly our audience.
  • Even a "zero matches this week" result is information — it confirms
    the tracked universe is clear.

Data sources (all FREE US government feeds):
  • https://data.trade.gov/downloadable_consolidated_screening_list
    A single consolidated CSV/JSON that combines BIS Entity List,
    BIS Denied Persons, OFAC SDN, OFAC Consolidated, State Department
    AECA Debarred List, and Nonproliferation Sanctions. One request,
    six lists.

We also diff against the prior run to flag ADDITIONS — new-this-week
entities are the truly material signal.

Output:
  data/export_controls_raw.json        — full consolidated list
  data/export_controls_matches.json    — matches against COMPANIES
  data/export_controls_auto.json       — UI payload: matches + diffs
  data/export_controls_auto.js         — browser global EXPORT_CONTROLS

Cadence: daily via comprehensive-data-sync.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"

RAW_OUT       = DATA_DIR / "export_controls_raw.json"
MATCH_OUT     = DATA_DIR / "export_controls_matches.json"
AUTO_OUT      = DATA_DIR / "export_controls_auto.json"
JS_OUT        = DATA_DIR / "export_controls_auto.js"
PRIOR_PATH    = DATA_DIR / "export_controls_prior.json"

TRADE_GOV_CSL = "https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.json"

HEADERS = {
    "User-Agent": "InnovatorsLeague/1.0 contact@innovatorsleague.com",
    "Accept": "application/json",
}

# Source codes as they appear in the consolidated feed — we label these
# more readably in the UI payload.
SOURCE_LABELS = {
    "Entity List (EL) - Bureau of Industry and Security": "BIS Entity List",
    "Denied Persons List (DPL) - Bureau of Industry and Security": "BIS Denied Persons",
    "Unverified List (UVL) - Bureau of Industry and Security": "BIS Unverified",
    "Military End User (MEU) List - Bureau of Industry and Security": "BIS Military End User",
    "Specially Designated Nationals (SDN) - Treasury Department": "OFAC SDN",
    "Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department":
        "OFAC Menu-Based",
    "Sectoral Sanctions Identifications List (SSI) - Treasury Department":
        "OFAC Sectoral",
    "Foreign Sanctions Evaders List (FSE) - Treasury Department":
        "OFAC Foreign Sanctions Evaders",
    "Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department":
        "OFAC CMIC (Chinese Military-Industrial)",
    "AECA Debarred List (AECA) - Department of State": "State AECA Debarred",
    "Capta List (CAP) - Treasury Department": "OFAC CAPTA",
    "ITAR Debarred (DTC) - Department of State": "State ITAR Debarred",
    "Nonproliferation Sanctions (ISN) - Department of State":
        "State Nonproliferation Sanctions",
}


def parse_companies_from_data_js():
    text = DATA_JS.read_text()
    start = text.find("const COMPANIES = [")
    if start < 0:
        return {}
    i = text.find("[", start)
    depth = 0; in_str = False; sc = None; esc = False; end = None
    for k in range(i, len(text)):
        c = text[k]
        if esc: esc = False; continue
        if c == "\\" and in_str: esc = True; continue
        if in_str:
            if c == sc: in_str = False
            continue
        if c in "\"'": in_str = True; sc = c; continue
        if c == "[": depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0: end = k; break
    block = text[i + 1:end] if end else ""
    # Pull (name, sector) tuples so the UI can tag matches by sector
    entries = {}
    for entry in re.finditer(r'\{[^{}]*?\bname:\s*"((?:[^"\\]|\\.)+)"[^{}]*?'
                             r'\bsector:\s*"((?:[^"\\]|\\.)*)"', block):
        entries[entry.group(1)] = entry.group(2)
    return entries


def fetch_consolidated_list():
    """Download the combined trade.gov screening list."""
    try:
        r = requests.get(TRADE_GOV_CSL, headers=HEADERS, timeout=60)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        print(f"  Fetched {len(results)} consolidated list entries")
        return results
    except Exception as e:
        print(f"  Consolidated list fetch failed: {e}")
        return []


# Tokens that are too common to discriminate by. "Nuclear Company"
# appears in hundreds of Russian/Chinese/Iranian entities unrelated to
# our US-tracked Nuclear Company, so matches containing ONLY these
# tokens are noise.
_STOPWORDS = {
    "the", "of", "and", "or", "a", "an", "for", "to", "by", "with",
    "new", "global", "international", "world", "national", "american",
    # Common industry words — if the match depends on these alone it's
    # almost always a false positive
    "nuclear", "space", "defense", "energy", "systems", "industries",
    "technology", "technologies", "group", "company", "corp",
    "corporation", "llc", "ltd", "inc", "co", "holdings", "partners",
    "solutions", "services", "science", "research", "enterprise",
    "enterprises", "limited", "industrial",
}


def _tokens(name):
    """Normalize and return non-stopword content tokens."""
    if not name:
        return []
    s = re.sub(r"[^a-z0-9 ]", " ", name.lower())
    s = re.sub(r"\s+", " ", s).strip()
    return [t for t in s.split() if t not in _STOPWORDS and len(t) >= 3]


def _norm(name):
    """Lowercase + strip punctuation + collapse whitespace. Keeps all
    words — don't strip corporate suffixes here; that mangles brand
    names like "Rocket Lab" down to "rocket" and destroys specificity."""
    if not name: return ""
    s = re.sub(r"[^a-z0-9 ]", " ", name.lower())
    return re.sub(r"\s+", " ", s).strip()


def _norm_no_suffix(name):
    """Exact-match helper: additional pass that strips the trailing
    corporate suffix so "Anduril Industries Inc." and "Anduril
    Industries" both normalize to the same key."""
    s = _norm(name)
    s = re.sub(r"\s+(inc|llc|corp|corporation|ltd|co|holdings|"
               r"group|partners?|lp)$", "", s)
    return s


def match_companies(entries, tracked):
    """Return list of (company_name, list-row, match_type) tuples.

    Matching rules (tight to avoid false positives — one bad hit on a
    Russian/Chinese/Iranian sanctions list destroys trust in the whole
    feature):

      1. EXACT: tracked normalized name == candidate normalized name.
      2. ALL-TOKENS: candidate contains every token of the tracked name
         (as word-bounded matches) AND the tracked name has at least 2
         tokens. "World Labs" would NOT match "World Courage" (only one
         token overlaps) but WOULD match "World Labs LLC" or "World Labs
         Holdings". Single-token company names like "Antares", "Armada",
         "Humanoid" are restricted to EXACT matches only.
      3. Tracked names shorter than 7 chars after normalization are
         restricted to EXACT match (single-word brand names are too
         likely to collide).
    """
    # Phrase = full normalized name (with "Lab" / "Labs" / etc. intact)
    # Exact key = also with corporate suffix stripped, for alias matching
    tracked_phrase = {_norm(name): name for name in tracked.keys()}
    tracked_phrase = {p: o for p, o in tracked_phrase.items() if p}

    # Second map for exact-match normalized-with-suffix-stripped → original
    tracked_exact = {}
    for orig in tracked.keys():
        for key in {_norm(orig), _norm_no_suffix(orig)}:
            if key: tracked_exact[key] = orig

    # Cache discriminating (non-stopword) tokens per tracked name — used
    # to pick a rare token for bucket indexing.
    tracked_tokens = {p: _tokens(orig) for p, orig in tracked_phrase.items()}

    # Fuzzy (phrase) match requires the original tracked name to have
    # ≥ 2 non-stopword tokens AND the full normalized phrase to be ≥ 7
    # chars. Single-token or very short names fall back to EXACT only.
    fuzzy_eligible = {p: o for p, o in tracked_phrase.items()
                      if len(tracked_tokens[p]) >= 2 and len(p) >= 7}

    # Index fuzzy-eligible names by their RAREST token (the least common
    # word is the most discriminating). Pre-compute token → candidates.
    from collections import Counter
    token_freq = Counter()
    for n in fuzzy_eligible:
        for t in tracked_tokens[n]:
            token_freq[t] += 1
    rarest_token = {}
    for n in fuzzy_eligible:
        rarest_token[n] = min(tracked_tokens[n], key=lambda t: token_freq[t])
    by_rare_token = {}
    for n, orig in fuzzy_eligible.items():
        by_rare_token.setdefault(rarest_token[n], []).append(n)

    # Sanctions-heavy country codes — tracked companies are effectively
    # never based in these, so any listed entity linked to one of these
    # regions is almost certainly a name collision rather than a real hit.
    SANCTIONED_COUNTRIES = {
        "russia", "russian federation", "china", "prc",
        "iran", "islamic republic of iran", "belarus", "cuba",
        "venezuela", "syria", "burma", "myanmar", "crimea",
        "democratic people's republic of korea", "north korea",
        "dprk", "sudan", "yemen", "zimbabwe",
    }
    # Country-specific OFAC sanctions programs — same idea via the
    # `programs` field rather than address parsing.
    SANCTIONED_PROGRAMS = {
        "RUSSIA", "UKRAINE", "VENEZUELA", "IRAN", "CUBA", "BELARUS",
        "DPRK", "NORTH KOREA", "SYRIA", "BURMA", "MYANMAR",
        "SDGT", "GLOMAG",  # broad terror/human-rights programs
    }

    def _row_is_foreign_sanctions(row):
        """Heuristic: return True if the entity is on a country-specific
        sanctions list that's clearly not a US frontier-tech target."""
        for prog in (row.get("programs") or []):
            p = (prog or "").upper()
            for flag in SANCTIONED_PROGRAMS:
                if flag in p:
                    return True
        # Address check
        for addr in (row.get("addresses") or []):
            if not isinstance(addr, dict): continue
            country = (addr.get("country") or "").strip().lower()
            if country in SANCTIONED_COUNTRIES:
                return True
        # Nationalities / citizenships
        for nat in (row.get("nationalities") or []) + (row.get("citizenships") or []):
            if (nat or "").strip().lower() in SANCTIONED_COUNTRIES:
                return True
        return False

    matches = []
    for row in entries:
        # Pre-filter: tracked companies are always Entities (never Vessels,
        # Individuals, Aircraft). Vessel hits account for most of the
        # noisy single-word-brand false positives (MARA IMO 9670999,
        # ANTARES I, etc.)
        entry_type = (row.get("type") or "").strip()
        if entry_type in {"Vessel", "Aircraft", "Individual"}:
            continue

        candidates = [row.get("name", "")]
        for alt in (row.get("alt_names") or []):
            candidates.append(alt)

        found_for_row = False
        for cand in candidates:
            cand_norm = _norm(cand)
            if not cand_norm:
                continue

            # EXACT match — highest confidence. Test both forms (with +
            # without corporate suffix) for maximum alias coverage.
            # For single-token tracked brand names (Antares, Helios,
            # Mara) we also require the listed entity NOT be on a
            # country-specific foreign-sanctions program — otherwise a
            # Russian "Antares LLC" collides with our US "Antares"
            # space company despite zero actual connection.
            cand_no_suffix = _norm_no_suffix(cand)
            exact_hit = None
            if cand_norm in tracked_exact:
                exact_hit = tracked_exact[cand_norm]
            elif cand_no_suffix in tracked_exact:
                exact_hit = tracked_exact[cand_no_suffix]
            if exact_hit:
                tracked_is_single_word = len(_tokens(exact_hit)) < 2
                if tracked_is_single_word and _row_is_foreign_sanctions(row):
                    # Almost certainly a name collision — skip.
                    continue
                matches.append((exact_hit, row, "exact"))
                found_for_row = True
                break

            # PHRASE match: the tracked normalized name must appear as
            # a contiguous word-bounded phrase in the candidate. This
            # prevents "Air Space Intelligence" matching a list entry
            # that merely CONTAINS both "air" and "intelligence" in
            # unrelated places. We still use the rare-token index to
            # avoid scanning all tracked names per candidate.
            cand_token_set = set(_tokens(cand))
            if not cand_token_set:
                continue
            checked = set()
            for tok in cand_token_set:
                for n in by_rare_token.get(tok, []):
                    if n in checked: continue
                    checked.add(n)
                    pattern = r"\b" + re.escape(n) + r"\b"
                    if re.search(pattern, cand_norm):
                        matches.append((fuzzy_eligible[n], row, "phrase"))
                        found_for_row = True
                        break
                if found_for_row:
                    break
            if found_for_row:
                break
    return matches


def build_ui_row(company, sector, row, match_type):
    source_raw = row.get("source", "")
    source_label = SOURCE_LABELS.get(source_raw, source_raw.split(" - ")[0] if " - " in source_raw else source_raw)
    return {
        "company": company,
        "sector": sector,
        "listed_name": row.get("name", ""),
        "list_source": source_label,
        "list_source_raw": source_raw,
        "list_added": row.get("date", ""),
        "country": row.get("country", ""),
        "addresses": [a.get("country", "") for a in (row.get("addresses") or []) if isinstance(a, dict)],
        "federal_register_notice": row.get("federal_register_notice", ""),
        "remarks": (row.get("remarks") or "")[:500],
        "source_url":
            "https://www.trade.gov/consolidated-screening-list" if not row.get("source_list_url") else row["source_list_url"],
        "match_type": match_type,
    }


def diff_against_prior(current_matches):
    """Compare current matches to last run; flag new additions."""
    prior = []
    if PRIOR_PATH.exists():
        try:
            prior = json.loads(PRIOR_PATH.read_text())
        except Exception:
            prior = []
    prior_keys = {(p.get("company"), p.get("listed_name"), p.get("list_source_raw"))
                  for p in prior if isinstance(p, dict)}
    new_additions = []
    for m in current_matches:
        key = (m["company"], m["listed_name"], m["list_source_raw"])
        if key not in prior_keys:
            new_additions.append(m)
    return new_additions


def main():
    print("=" * 68)
    print("Export Controls / Entity List Watch")
    print("=" * 68)

    tracked = parse_companies_from_data_js()
    print(f"Tracked companies: {len(tracked)}")

    entries = fetch_consolidated_list()
    if not entries:
        print("No data fetched — aborting without touching outputs.")
        return

    RAW_OUT.write_text(json.dumps(entries, indent=2))
    print(f"Wrote {RAW_OUT.name}  ({len(entries)} list entries)")

    raw_matches = match_companies(entries, tracked)
    ui_rows = [build_ui_row(c, tracked[c], row, mt)
               for c, row, mt in raw_matches]
    # Dedupe by (company, listed_name, source)
    seen = set(); dedup = []
    for m in ui_rows:
        key = (m["company"], m["listed_name"], m["list_source_raw"])
        if key in seen: continue
        seen.add(key)
        dedup.append(m)
    ui_rows = dedup

    MATCH_OUT.write_text(json.dumps(ui_rows, indent=2))
    print(f"Matches against tracked: {len(ui_rows)}")

    # Diff vs prior run
    new_adds = diff_against_prior(ui_rows)

    # Source breakdown for dashboard stats
    from collections import Counter
    src_counter = Counter(r["list_source"] for r in ui_rows)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source":  "Trade.gov Consolidated Screening List (BIS + OFAC + State)",
        "total_list_entries": len(entries),
        "tracked_companies":  len(tracked),
        "matches_total":      len(ui_rows),
        "new_this_run":       len(new_adds),
        "new_additions":      new_adds,
        "by_list":            dict(src_counter),
        "matches":            ui_rows,
    }

    AUTO_OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {AUTO_OUT.name}")

    # Rotate prior cache
    PRIOR_PATH.write_text(json.dumps(ui_rows, indent=2))

    # Browser bundle
    header = (
        f"// Auto-generated Export Controls / Entity List matches\n"
        f"// Source: data.trade.gov (consolidated BIS + OFAC + State)\n"
        f"// Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        f"// Total matches: {len(ui_rows)}  |  New this run: {len(new_adds)}\n"
    )
    body = f"const EXPORT_CONTROLS = {json.dumps(payload, indent=2, ensure_ascii=False)};\n"
    JS_OUT.write_text(header + body)
    print(f"Wrote {JS_OUT.name}")

    if new_adds:
        print("\n🚨 NEW ADDITIONS THIS RUN:")
        for m in new_adds:
            print(f"  {m['company']:30s} → {m['list_source']}  ({m['listed_name']})")
    if ui_rows and not new_adds:
        print("\nExisting matches (unchanged since prior run):")
        for m in ui_rows[:10]:
            print(f"  {m['company']:30s} → {m['list_source']}")


if __name__ == "__main__":
    main()
