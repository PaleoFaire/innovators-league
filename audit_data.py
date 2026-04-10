#!/usr/bin/env python3
"""Comprehensive data quality audit for data.js"""

import re
import json
import sys
from collections import Counter, defaultdict

DATA_FILE = "/Users/stephenmcbride/Desktop/Claude/innovators-league/data.js"

with open(DATA_FILE, "r") as f:
    raw = f.read()

print(f"File size: {len(raw):,} bytes")
print(f"Total lines: {raw.count(chr(10))}")

# ============================================================
# 1. ALL TOP-LEVEL CONST/VARIABLE DEFINITIONS
# ============================================================
print("\n" + "="*80)
print("1. ALL TOP-LEVEL CONST/VARIABLE DEFINITIONS")
print("="*80)

top_level = re.findall(r'^(const|let|var)\s+(\w+)\s*=\s*(.)', raw, re.MULTILINE)
for kind, name, first_char in top_level:
    dtype = {"[": "Array", "{": "Object", '"': "String", "'": "String"}.get(first_char, "Other")
    print(f"  {kind} {name} = {dtype}")
print(f"\nTotal top-level definitions: {len(top_level)}")

# ============================================================
# HELPER: Extract JS array/object using bracket matching
# ============================================================
def extract_js_value(var_name):
    """Extract the value of a const/let/var declaration by bracket-matching."""
    pattern = re.compile(rf'(?:const|let|var)\s+{re.escape(var_name)}\s*=\s*')
    m = pattern.search(raw)
    if not m:
        return None
    start = m.end()
    opener = raw[start]
    if opener == '[':
        close = ']'
    elif opener == '{':
        close = '}'
    elif opener == '"':
        end = raw.index('"', start + 1)
        return raw[start:end+1]
    else:
        # Find the semicolon
        end = raw.index(';', start)
        return raw[start:end]

    depth = 0
    i = start
    while i < len(raw):
        c = raw[i]
        if c == opener:
            depth += 1
        elif c == close:
            depth -= 1
            if depth == 0:
                return raw[start:i+1]
        elif c in ('"', "'", '`'):
            # skip string
            q = c
            i += 1
            while i < len(raw) and raw[i] != q:
                if raw[i] == '\\':
                    i += 1
                i += 1
        elif c == '/' and i+1 < len(raw) and raw[i+1] == '/':
            # skip line comment
            while i < len(raw) and raw[i] != '\n':
                i += 1
        i += 1
    return None

def js_to_json(js_str):
    """Convert JS object/array literal to JSON-parseable string."""
    if js_str is None:
        return None
    s = js_str
    # Remove single-line comments
    s = re.sub(r'//[^\n]*', '', s)
    # Remove multi-line comments
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.DOTALL)
    # Add quotes around unquoted keys: word: -> "word":
    s = re.sub(r'(?<=[{,\n])\s*(\w+)\s*:', r' "\1":', s)
    # Handle trailing commas before } or ]
    s = re.sub(r',\s*([}\]])', r'\1', s)
    # Replace single quotes with double quotes (careful)
    # First protect escaped single quotes
    s = s.replace("\\'", "___ESCAPED_SQUOTE___")
    # Replace unescaped single-quoted strings
    def replace_single_quotes(match):
        return '"' + match.group(1) + '"'
    s = re.sub(r"'([^']*)'", replace_single_quotes, s)
    s = s.replace("___ESCAPED_SQUOTE___", "'")
    # Handle JS booleans - already valid JSON
    # Handle null - already valid JSON
    # Handle undefined -> null
    s = re.sub(r'\bundefined\b', 'null', s)
    # Handle template literals (backtick strings) - simplified
    s = re.sub(r'`([^`]*)`', lambda m: '"' + m.group(1).replace('"', '\\"').replace('\n', '\\n') + '"', s)
    return s

def parse_js_array(var_name):
    """Extract and parse a JS array."""
    js = extract_js_value(var_name)
    if js is None:
        return None
    json_str = js_to_json(js)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Try to give info about what failed
        pos = e.pos if hasattr(e, 'pos') else 0
        context = json_str[max(0,pos-100):pos+100] if json_str else ""
        print(f"  [PARSE ERROR for {var_name}]: {e}")
        print(f"  Context around error: ...{context[:80]}...")
        return None

def parse_js_object(var_name):
    """Extract and parse a JS object."""
    return parse_js_array(var_name)  # same logic

# ============================================================
# 2. COMPANIES ARRAY ANALYSIS
# ============================================================
print("\n" + "="*80)
print("2. COMPANIES ARRAY ANALYSIS")
print("="*80)

companies = parse_js_array("COMPANIES")

if companies:
    print(f"\n  Total companies: {len(companies)}")

    # Key fields to check
    key_fields = ["description", "founder", "location", "lat", "lng",
                  "fundingStage", "totalRaised", "investors", "tags",
                  "scores", "thesisCluster", "techApproach"]

    print(f"\n  --- Missing Key Fields ---")
    for field in key_fields:
        missing = [c.get("name","?") for c in companies if field not in c or c[field] is None]
        if missing:
            print(f"  {field}: {len(missing)} missing")
            if len(missing) <= 10:
                for name in missing:
                    print(f"    - {name}")
            else:
                for name in missing[:5]:
                    print(f"    - {name}")
                print(f"    ... and {len(missing)-5} more")

    print(f"\n  --- Empty String Values ---")
    for field in key_fields:
        empty = [c.get("name","?") for c in companies if c.get(field) == ""]
        if empty:
            print(f"  {field}: {len(empty)} empty strings")
            for name in empty[:5]:
                print(f"    - {name}")

    print(f"\n  --- Duplicate Company Names ---")
    names = [c.get("name","?") for c in companies]
    name_counts = Counter(names)
    dupes = {k: v for k, v in name_counts.items() if v > 1}
    if dupes:
        for name, count in dupes.items():
            print(f"  '{name}' appears {count} times")
    else:
        print("  No duplicates found")

    print(f"\n  --- Sector Distribution ---")
    sectors = [c.get("sector", "MISSING") for c in companies]
    sector_counts = Counter(sectors)
    for sector, count in sorted(sector_counts.items()):
        print(f"  {sector}: {count}")
    print(f"  Total unique sectors: {len(sector_counts)}")

    # Check for sector inconsistencies
    print(f"\n  --- Sector Consistency Check ---")
    sector_lower = defaultdict(set)
    for s in sectors:
        sector_lower[s.lower().strip()].add(s)
    for lower, variants in sector_lower.items():
        if len(variants) > 1:
            print(f"  INCONSISTENCY: {variants}")
    if all(len(v) == 1 for v in sector_lower.values()):
        print("  No case/spelling inconsistencies found")

    print(f"\n  --- rosLink (newsletter article link) ---")
    has_roslink = [c for c in companies if c.get("rosLink")]
    no_roslink = [c for c in companies if not c.get("rosLink")]
    print(f"  Companies with rosLink: {len(has_roslink)}")
    print(f"  Companies without rosLink: {len(no_roslink)}")

    print(f"\n  --- Signal Distribution ---")
    signals = [c.get("signal", "MISSING") for c in companies]
    signal_counts = Counter(signals)
    for signal, count in sorted(signal_counts.items()):
        print(f"  {signal}: {count}")

    print(f"\n  --- Score Distribution ---")
    all_zero = []
    score_fields_set = set()
    for c in companies:
        scores = c.get("scores", {})
        if scores:
            score_fields_set.update(scores.keys())
            vals = list(scores.values())
            if all(v == 0 for v in vals):
                all_zero.append(c.get("name", "?"))
    print(f"  Score fields found: {score_fields_set}")
    print(f"  Companies with all-zero scores: {len(all_zero)}")
    if all_zero:
        for name in all_zero:
            print(f"    - {name}")

    # Score statistics
    for field in sorted(score_fields_set):
        vals = [c.get("scores", {}).get(field, 0) for c in companies if c.get("scores")]
        if vals:
            avg = sum(vals) / len(vals)
            print(f"  {field}: avg={avg:.1f}, min={min(vals)}, max={max(vals)}")

    # Check for companies missing scores entirely
    no_scores = [c.get("name","?") for c in companies if not c.get("scores")]
    if no_scores:
        print(f"\n  Companies with NO scores object: {len(no_scores)}")
        for n in no_scores[:10]:
            print(f"    - {n}")

    # Investors field
    print(f"\n  --- Investors Field ---")
    has_investors = [c for c in companies if c.get("investors")]
    no_investors = [c.get("name","?") for c in companies if not c.get("investors")]
    print(f"  Companies with investors: {len(has_investors)}")
    print(f"  Companies without investors: {len(no_investors)}")

    # valuation field
    print(f"\n  --- Valuation Field ---")
    has_val = [c for c in companies if c.get("valuation")]
    print(f"  Companies with valuation: {len(has_val)}")
    print(f"  Companies without valuation: {len(has_val) - len(companies)} (i.e., {len(companies) - len(has_val)} missing)")

    # thesis field
    print(f"\n  --- Thesis (bull/bear/risks) ---")
    has_thesis = [c for c in companies if c.get("thesis")]
    print(f"  Companies with thesis: {len(has_thesis)}")
    print(f"  Companies without thesis: {len(companies) - len(has_thesis)}")

    company_names_set = set(c.get("name","") for c in companies)

else:
    print("  FAILED TO PARSE COMPANIES ARRAY")
    company_names_set = set()

# ============================================================
# 3. VC_FIRMS ANALYSIS
# ============================================================
print("\n" + "="*80)
print("3. VC_FIRMS ANALYSIS")
print("="*80)

vc_firms = parse_js_array("VC_FIRMS")
if vc_firms:
    print(f"  Total VC firms: {len(vc_firms)}")

    no_portfolio = [v.get("name","?") for v in vc_firms if not v.get("portfolio")]
    print(f"  VCs without portfolio data: {len(no_portfolio)}")
    if no_portfolio:
        for n in no_portfolio:
            print(f"    - {n}")

    # Check portfolio company names vs COMPANIES
    print(f"\n  --- Portfolio Company Name Consistency ---")
    all_portfolio_names = set()
    for vc in vc_firms:
        portfolio = vc.get("portfolio", [])
        if isinstance(portfolio, list):
            for p in portfolio:
                if isinstance(p, str):
                    all_portfolio_names.add(p)
                elif isinstance(p, dict):
                    all_portfolio_names.add(p.get("name", p.get("company", "")))

    not_in_companies = all_portfolio_names - company_names_set
    if not_in_companies:
        print(f"  Portfolio names NOT in COMPANIES array: {len(not_in_companies)}")
        for n in sorted(not_in_companies):
            print(f"    - {n}")
    else:
        print("  All portfolio names match COMPANIES entries")

    in_companies = all_portfolio_names & company_names_set
    print(f"  Portfolio names matching COMPANIES: {len(in_companies)}")
else:
    print("  FAILED TO PARSE VC_FIRMS")

# ============================================================
# 4. OTHER DATA ARRAYS
# ============================================================
print("\n" + "="*80)
print("4. OTHER DATA ARRAYS ANALYSIS")
print("="*80)

other_arrays = [
    "INNOVATOR_SCORES", "PREV_WEEK_SCORES", "DEAL_TRACKER", "GOV_CONTRACTS",
    "SECTOR_MOMENTUM", "IPO_PIPELINE", "MARKET_PULSE", "FUNDING_TRACKER",
    "NEWS_TICKER", "WEEKLY_DIGEST", "TRL_RANKINGS", "PRODUCT_LAUNCHES",
    "GROWTH_SIGNALS", "HEADCOUNT_ESTIMATES", "REVENUE_INTEL", "NEWS_FEED",
    "STORY_LEADS", "EXPERT_TAKES", "FIELD_NOTES", "COMMUNITY_EVENTS",
    "GOV_DEMAND_TRACKER", "NIH_GRANTS", "ARPA_E_PROJECTS", "BUDGET_SIGNALS",
    "PATENT_INTEL", "ALT_DATA_SIGNALS", "EXPERT_INSIGHTS", "VALLEY_OF_DEATH",
    "VALLEY_OF_DEATH_STAGES", "CONTRACTOR_READINESS", "LIVE_AWARD_FEED",
    "DEAL_FLOW_SIGNALS", "MA_COMPS", "COMPANY_SIGNALS", "SLACK_CHANNELS",
    "INNOVATORS_LEAGUE_30", "INNOVATOR_50", "INNOVATOR_50_2025", "INNOVATOR_50_2024",
    "REQUEST_FOR_STARTUPS", "MOSAIC_SCORES"
]

for arr_name in other_arrays:
    data = parse_js_array(arr_name)
    if data is None:
        print(f"\n  {arr_name}: FAILED TO PARSE or NOT FOUND")
        continue

    if isinstance(data, list):
        print(f"\n  {arr_name}: {len(data)} entries (Array)")
        if len(data) > 0:
            first = data[0]
            if isinstance(first, dict):
                keys = list(first.keys())
                print(f"    Fields: {keys[:10]}{'...' if len(keys)>10 else ''}")

                # Check dates
                date_fields = [k for k in keys if 'date' in k.lower() or 'updated' in k.lower() or 'year' in k.lower()]
                if date_fields:
                    dates = set()
                    for item in data:
                        for df in date_fields:
                            v = item.get(df)
                            if v:
                                dates.add(str(v))
                    if dates:
                        sorted_dates = sorted(dates)
                        print(f"    Date range ({date_fields}): {sorted_dates[0]} to {sorted_dates[-1]}")

                # Check company references
                company_ref_fields = [k for k in keys if 'company' in k.lower() or 'name' in k.lower()]
                if company_ref_fields and company_names_set:
                    ref_names = set()
                    for item in data:
                        for cf in company_ref_fields:
                            v = item.get(cf)
                            if isinstance(v, str) and v:
                                ref_names.add(v)
                    not_found = ref_names - company_names_set
                    if not_found:
                        print(f"    References NOT in COMPANIES: {len(not_found)}")
                        for n in sorted(not_found)[:10]:
                            print(f"      - {n}")
                        if len(not_found) > 10:
                            print(f"      ... and {len(not_found)-10} more")
    elif isinstance(data, dict):
        print(f"\n  {arr_name}: Object with {len(data)} keys")
        keys = list(data.keys())
        print(f"    Keys: {keys[:15]}{'...' if len(keys)>15 else ''}")

# ============================================================
# 5. PLACEHOLDER / STALE DATA CHECK
# ============================================================
print("\n" + "="*80)
print("5. PLACEHOLDER / STALE DATA CHECK")
print("="*80)

# Search for common placeholder patterns
placeholder_patterns = [
    r'TODO', r'FIXME', r'PLACEHOLDER', r'TBD', r'XXX', r'HACK',
    r'lorem ipsum', r'test data', r'sample data', r'example\.com',
    r'foo', r'bar', r'baz', r'asdf', r'John Doe', r'Jane Doe'
]

for pattern in placeholder_patterns:
    matches = re.findall(rf'.*{pattern}.*', raw, re.IGNORECASE)
    if matches:
        print(f"\n  Pattern '{pattern}': {len(matches)} matches")
        for m in matches[:3]:
            print(f"    {m.strip()[:120]}")

# Check for 2024 dates (potentially stale)
print(f"\n  --- Date Currency Check ---")
dates_2024 = len(re.findall(r'2024-\d{2}', raw))
dates_2025 = len(re.findall(r'2025-\d{2}', raw))
dates_2026 = len(re.findall(r'2026-\d{2}', raw))
print(f"  References to 2024-XX dates: {dates_2024}")
print(f"  References to 2025-XX dates: {dates_2025}")
print(f"  References to 2026-XX dates: {dates_2026}")

# ============================================================
# 6. COMMUNITY_EVENTS DATE CHECK
# ============================================================
print("\n" + "="*80)
print("6. COMMUNITY_EVENTS DATE CHECK")
print("="*80)

events = parse_js_array("COMMUNITY_EVENTS")
if events:
    print(f"  Total events: {len(events)}")
    today = "2026-03-29"
    for evt in events:
        date = evt.get("date", "unknown")
        title = evt.get("title", evt.get("name", "?"))
        status = "FUTURE" if str(date) > today else "PAST"
        print(f"  [{status}] {date}: {title}")
else:
    print("  FAILED TO PARSE COMMUNITY_EVENTS")

# ============================================================
# 7. INNOVATOR_50 / IL30 CHECK
# ============================================================
print("\n" + "="*80)
print("7. INNOVATOR_50 / INNOVATORS_LEAGUE_30 CHECK")
print("="*80)

il30 = parse_js_array("INNOVATORS_LEAGUE_30")
if il30:
    print(f"  INNOVATORS_LEAGUE_30: {len(il30)} entries")
    if isinstance(il30[0], dict):
        print(f"    Fields: {list(il30[0].keys())[:10]}")
        # Check if names match COMPANIES
        il30_names = set()
        for item in il30:
            n = item.get("name") or item.get("company") or ""
            if n:
                il30_names.add(n)
        not_in = il30_names - company_names_set
        if not_in:
            print(f"    Names NOT in COMPANIES: {not_in}")
    elif isinstance(il30[0], str):
        il30_names = set(il30)
        not_in = il30_names - company_names_set
        if not_in:
            print(f"    Names NOT in COMPANIES: {not_in}")
        print(f"    All entries are strings")

i50 = parse_js_array("INNOVATOR_50")
if i50:
    print(f"\n  INNOVATOR_50: {len(i50)} entries")
    if isinstance(i50[0], dict):
        print(f"    Fields: {list(i50[0].keys())[:10]}")
        i50_names = set(item.get("name", item.get("company", "")) for item in i50)
        not_in = i50_names - company_names_set
        if not_in:
            print(f"    Names NOT in COMPANIES ({len(not_in)}): ")
            for n in sorted(not_in)[:15]:
                print(f"      - {n}")

i50_2025 = parse_js_array("INNOVATOR_50_2025")
if i50_2025:
    print(f"\n  INNOVATOR_50_2025: {len(i50_2025)} entries")

i50_2024 = parse_js_array("INNOVATOR_50_2024")
if i50_2024:
    print(f"\n  INNOVATOR_50_2024: {len(i50_2024)} entries")

i50_meta = parse_js_object("INNOVATOR_50_META")
if i50_meta:
    print(f"\n  INNOVATOR_50_META: {i50_meta}")

# ============================================================
# 8. ADDITIONAL CHECKS
# ============================================================
print("\n" + "="*80)
print("8. ADDITIONAL CHECKS")
print("="*80)

# Check MOSAIC_SCORES
mosaic = parse_js_object("MOSAIC_SCORES")
if mosaic and isinstance(mosaic, dict):
    print(f"\n  MOSAIC_SCORES: {len(mosaic)} companies scored")
    mosaic_names = set(mosaic.keys())
    not_in_companies = mosaic_names - company_names_set
    if not_in_companies:
        print(f"  MOSAIC companies NOT in COMPANIES: {len(not_in_companies)}")
        for n in sorted(not_in_companies)[:10]:
            print(f"    - {n}")

# Check NETWORK_GRAPH
network = parse_js_object("NETWORK_GRAPH")
if network and isinstance(network, dict):
    nodes = network.get("nodes", [])
    edges = network.get("edges", network.get("links", []))
    print(f"\n  NETWORK_GRAPH: {len(nodes)} nodes, {len(edges)} edges")

# Check PREDICTIVE_SCORES
pred = parse_js_object("PREDICTIVE_SCORES")
if pred and isinstance(pred, dict):
    print(f"\n  PREDICTIVE_SCORES: {len(pred)} companies")
    pred_names = set(pred.keys())
    not_in = pred_names - company_names_set
    if not_in:
        print(f"  PREDICTIVE companies NOT in COMPANIES: {len(not_in)}")
        for n in sorted(not_in)[:10]:
            print(f"    - {n}")

# HISTORICAL_TRACKING
hist = parse_js_object("HISTORICAL_TRACKING")
if hist and isinstance(hist, dict):
    print(f"\n  HISTORICAL_TRACKING: {len(hist)} companies tracked")

# FOUNDER_CONNECTIONS
fc = parse_js_object("FOUNDER_CONNECTIONS")
if fc and isinstance(fc, dict):
    print(f"\n  FOUNDER_CONNECTIONS: {len(fc)} companies")
    fc_names = set(fc.keys())
    not_in = fc_names - company_names_set
    if not_in:
        print(f"  FOUNDER_CONNECTIONS companies NOT in COMPANIES: {not_in}")
    met = sum(1 for v in fc.values() if isinstance(v, dict) and v.get("metFounder"))
    print(f"  Founders met: {met}/{len(fc)}")

# DATA_QUALITY self-assessment
dq = parse_js_object("DATA_QUALITY")
if dq:
    print(f"\n  DATA_QUALITY (self-assessment): {json.dumps(dq, indent=4)[:500]}")

# PLATFORM_STATS
ps = parse_js_object("PLATFORM_STATS")
if ps:
    print(f"\n  PLATFORM_STATS: {json.dumps(ps, indent=4)[:500]}")

print("\n" + "="*80)
print("AUDIT COMPLETE")
print("="*80)
