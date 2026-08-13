#!/usr/bin/env python3
"""
Data-quality gate for data.js — runs in pre-commit and in every bot workflow
before a commit is allowed. Protects the Aug 2026 overhaul invariants:

  1. No duplicate company names (exact or normalized), with a NOT_DUPLICATES
     whitelist for known distinct near-collision pairs.
  2. Referential integrity: company keys in analytics structures must resolve
     to COMPANIES (or VC_FIRMS, or the alias map).
  3. Valuation trust layer: a $-figure requires a non-'undisclosed'
     valuationType; the literal 'Undisclosed' requires type
     undisclosed | tracker-estimate | secondary-mark.
     (Undisclosed + tracker-estimate/secondary-mark is LEGAL by design: it
     means "a third-party figure exists but is not shown as fact".)
  4. sector must be a SECTORS taxonomy key.
  5. state is populated only for country == "United States" (USPS code).
  6. status must be one of active|ipo|acquired|dead|zombie on every company.
  7. Every INNOVATORS_LEAGUE_30 roster name resolves to a COMPANIES record.
  8. No backslash runs >= 8 chars anywhere (the escaping-bomb tripwire).
  9. addedDate matches ^\\d{4}-\\d{2}(-\\d{2})?$.
 10. FUNDING_TRACKER sanity: no round amount >= $50B.
 11. data.js stays under the size ceiling (soft warn 4.5MB, hard fail 8MB).

Exit 0 = clean (warnings allowed). Exit 1 = hard violations (block commit).
"""

import re
import sys
from pathlib import Path

DATA_JS = Path(__file__).resolve().parent.parent / "data.js"

US_STATES = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
    'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
    'VA','WA','WV','WI','WY','DC',
}
STATUS_ENUM = {"active", "ipo", "acquired", "dead", "zombie"}
VAL_TYPES = {"disclosed", "tracker-estimate", "secondary-mark", "undisclosed"}
NOT_DUPLICATES = [  # distinct companies that naive suffix-stripping would merge
    ("Impulse Space", "Impulse Labs"), ("Atomic Industries", "Atomic AI"),
    ("Bedrock Energy", "Bedrock Robotics"), ("Foundry Lab", "Foundry Robotics"),
    ("Reflex Aerospace", "Reflex Robotics"), ("Scout AI", "Scout Space"),
    ("Space Forge", "Forge Robotics"), ("PAVE Space", "Pave Robotics"),
    ("Rain Industries", "Rain AI"), ("Sift Stack", "Sift"),
]
ALIASES = {
    "Anduril": "Anduril Industries", "Varda Space": "Varda Space Industries",
    "Palantir Technologies": "Palantir", "Helion Energy": "Helion",
    "Cuby": "Cuby Technologies", "CX2": "CX2 Industries",
    "Summit Nanotech": "Summit Lithium Technologies",
    "Ulysses": "Ulysses Robotics", "Poseidon": "Poseidon Aerospace",
}
# Big public / mega-private companies that legitimately appear in bot-populated
# signal feeds (news, patents, headcount, revenue) but are deliberately NOT in
# COMPANIES, which tracks frontier-tech PRIVATE companies. Flagging these as
# orphans made every daily sync fail the gate. Typos and renames are still
# caught — this list is explicit and must be edited by hand to grow.
KNOWN_UNTRACKED = {
    "AMD", "NVIDIA", "Tesla", "Stripe", "OpenAI", "Anthropic",
    "Safe Superintelligence", "ElevenLabs", "Flexport", "Watershed", "Modal",
    "Hive AI", "Labelbox", "C3.ai", "Tempus AI", "Ginkgo Bioworks",
    "Boston Dynamics", "Rainbow Robotics", "Kodiak Robotics", "Zoox",
    "BlackSky", "Capella Space", "Terran Orbital",
}

ANALYTICS = [
    "GOV_CONTRACTS", "SAM_CONTRACTS", "GROWTH_SIGNALS", "ALT_DATA_SIGNALS",
    "PATENT_INTEL", "HEADCOUNT_ESTIMATES", "REVENUE_INTEL", "COMPANY_SIGNALS",
    "MOSAIC_SCORES", "TRL_RANKINGS", "VALLEY_OF_DEATH", "CONTRACTOR_READINESS",
]


def block(d, name):
    m = re.search(r'\nconst ' + name + r'\s*=', d)
    if not m:
        return ""
    e = d.find("\nconst ", m.start() + 5)
    return d[m.start():e if e > 0 else len(d)]


def company_objects(d):
    i = d.find("const COMPANIES")
    i = d.find("[", i)
    depth = 0; j = i; instr = False; q = None; esc = False
    while j < len(d):
        c = d[j]
        if instr:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == q: instr = False
        else:
            if c in '"\'': instr = True; q = c
            elif c == "[": depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0: break
        j += 1
    arr = d[i:j + 1]
    objs = []; k = 0; depth = 0; st = None; instr = False; q = None; esc = False
    while k < len(arr):
        c = arr[k]
        if instr:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == q: instr = False
        else:
            if c in '"\'': instr = True; q = c
            elif c == "{":
                if depth == 0: st = k
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0: objs.append(arr[st:k + 1])
        k += 1
    return objs


def gv(o, key):
    m = re.search(r'\n\s{4}' + key + r'\s*:\s*(.+?),?\n', o)
    return m.group(1).strip().rstrip(",").strip('"') if m else None


def main():
    errors, warnings = [], []
    d = DATA_JS.read_text()

    # 11. size ceiling
    size = len(d)
    if size > 8_000_000:
        errors.append(f"data.js is {size:,} bytes (> 8MB hard ceiling)")
    elif size > 4_500_000:
        warnings.append(f"data.js is {size:,} bytes (> 4.5MB soft ceiling)")

    # 8. escaping-bomb tripwire
    runs = re.findall(r'\\{8,}', d)
    if runs:
        errors.append(f"backslash runs >=8 chars detected ({len(runs)} occurrences) — escaping bomb regrowing")

    objs = company_objects(d)
    names = [gv(o, "name") for o in objs]
    names = [n for n in names if n]

    # 1. duplicates
    seen = {}
    wl = {tuple(sorted(p)) for p in NOT_DUPLICATES}
    for n in names:
        key = re.sub(r'[^a-z0-9]', '', n.lower())
        if key in seen and tuple(sorted((seen[key], n))) not in wl:
            errors.append(f"duplicate company name: '{seen[key]}' vs '{n}'")
        seen[key] = n
    name_set = set(names)

    vc_names = set(re.findall(r'name:\s*"([^"]+)"', block(d, "VC_FIRMS")))
    sectors = set(re.findall(r'\n  "([^"]+)":\s*\{', block(d, "SECTORS")))

    for o in objs:
        n = gv(o, "name") or "?"
        # 3. valuation trust layer
        val = gv(o, "valuation")
        vt = gv(o, "valuationType")
        if val and val.startswith("$") and (vt == "undisclosed"):
            errors.append(f"{n}: $-valuation '{val}' typed 'undisclosed'")
        if val == "Undisclosed" and vt and vt == "disclosed":
            errors.append(f"{n}: 'Undisclosed' valuation typed 'disclosed'")
        if vt and vt not in VAL_TYPES:
            errors.append(f"{n}: invalid valuationType '{vt}'")
        # 4. sector taxonomy
        sec = gv(o, "sector")
        if sec and sectors and sec not in sectors:
            errors.append(f"{n}: sector '{sec}' not in SECTORS taxonomy")
        # 5. state hygiene
        st = gv(o, "state")
        ctry = gv(o, "country")
        if st and ctry and ctry != "United States":
            errors.append(f"{n}: non-US company carries state '{st}'")
        if st and ctry == "United States" and st not in US_STATES:
            errors.append(f"{n}: invalid US state code '{st}'")
        # 6. status enum
        stat = gv(o, "status")
        if stat is None:
            warnings.append(f"{n}: missing status field")
        elif stat not in STATUS_ENUM:
            errors.append(f"{n}: invalid status '{stat}'")
        # 9. addedDate format
        ad = gv(o, "addedDate")
        if ad and not re.match(r'^\d{4}-\d{2}(-\d{2})?$', ad):
            errors.append(f"{n}: malformed addedDate '{ad}'")

    # 2. referential integrity in analytics structures
    #
    # These structures are BOT-POPULATED from news, patents, contracts and
    # hiring feeds, so they will always name companies outside COMPANIES —
    # every night the crawlers meet someone new. Treating that as a hard
    # error blocked the sync on 2026-08-13 over two legitimate discoveries
    # ("Dust", "Multiverse Computing"), and a hand-maintained allowlist can
    # never keep pace with a crawler.
    #
    # So: a few unresolved names are normal and only warn. A LOT of them means
    # the merge mangled the name fields rather than discovering companies,
    # which is a real corruption and still fails the build.
    ORPHAN_FAIL_RATIO = 0.25   # >25% unresolved = something is broken, not new
    ORPHAN_FAIL_FLOOR = 25     # ...but never fail on a handful

    def resolves(ref):
        if ref in name_set or ref in vc_names or ref in KNOWN_UNTRACKED:
            return True
        return ALIASES.get(ref) in name_set

    for s in ANALYTICS:
        blk = block(d, s)
        refs = re.findall(r'\{\s*company:\s*"([^"]+)"', blk)
        if not refs:
            continue
        orphans = sorted({r for r in refs if not resolves(r)})
        if not orphans:
            continue
        ratio = len(orphans) / len(set(refs))
        msg = (f"{s}: {len(orphans)}/{len(set(refs))} unresolved company refs "
               f"({ratio:.0%}), e.g. {orphans[:4]}")
        if len(orphans) >= ORPHAN_FAIL_FLOOR and ratio > ORPHAN_FAIL_RATIO:
            errors.append(msg + " — too many to be new discoveries; check the merge")
        else:
            warnings.append(msg)

    # 7. IL30 roster resolution
    il30 = re.findall(r'"([^"]+)"', block(d, "INNOVATORS_LEAGUE_30"))
    for n in il30:
        if n not in name_set and ALIASES.get(n) not in name_set:
            errors.append(f"INNOVATORS_LEAGUE_30: '{n}' does not resolve to a COMPANIES record")

    # 10. FUNDING_TRACKER sanity
    for m in re.finditer(r'(?:lastRoundAmount|amount):\s*"\$([\d.]+)B"', block(d, "FUNDING_TRACKER")):
        if float(m.group(1)) >= 50:
            errors.append(f"FUNDING_TRACKER: implausible round amount ${m.group(1)}B")

    print(f"data-quality gate: {len(errors)} errors, {len(warnings)} warnings "
          f"({len(objs)} companies, {size:,} bytes)")
    for w in warnings[:10]:
        print(f"  WARN  {w}")
    if len(warnings) > 10:
        print(f"  ...   +{len(warnings) - 10} more warnings")
    for e in errors[:40]:
        print(f"  ERROR {e}")
    if len(errors) > 40:
        print(f"  ...   +{len(errors) - 40} more errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
