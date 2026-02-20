#!/usr/bin/env python3
"""
Founder DNA Index Generator for The Innovators League
Cross-references COMPANIES, FOUNDER_MAFIAS, and INNOVATOR_SCORES
to produce quantified founder profiles for all tracked companies.

Output: data/founder_dna.js
"""

import json
import re
from datetime import datetime
from pathlib import Path

DATA_JS = Path(__file__).parent.parent / "data.js"
OUTPUT_JS = Path(__file__).parent.parent / "data" / "founder_dna.js"

# ── DNA composite weights ──
WEIGHTS = {
    "mafiaPedigree": 0.25,
    "capitalEfficiency": 0.20,
    "serialBonus": 0.15,
    "teamSizeSignal": 0.15,
    "teamPedigree": 0.25,
}

# ── Team structure classification ──
def classify_team(count):
    if count <= 1:
        return "solo"
    elif count == 2:
        return "duo"
    elif count == 3:
        return "trio"
    elif count <= 5:
        return "squad"
    else:
        return "large"

# ── Team size signal score ──
def team_size_score(count):
    """Optimal team size of 2-3 founders scores highest."""
    if count == 2:
        return 10
    elif count == 3:
        return 10
    elif count == 1:
        return 6
    elif count == 4:
        return 8
    elif count == 5:
        return 7
    else:
        return 4


# ═══════════════════════════════════════════════════════════════════════════════
# DATA EXTRACTION (regex-based, same pattern as generate_moat_profiles.py)
# ═══════════════════════════════════════════════════════════════════════════════

def parse_capital(amount_str):
    """Parse '$2.5B+' or '$550M' to numeric millions."""
    if not amount_str or not isinstance(amount_str, str):
        return 0
    cleaned = re.sub(r'[^0-9.BMKTbmkt]', '', amount_str)
    match = re.match(r'([\d.]+)\s*(T|B|M|K)?', cleaned, re.IGNORECASE)
    if not match:
        return 0
    num = float(match.group(1))
    unit = (match.group(2) or '').upper()
    if unit == 'T':
        return num * 1_000_000
    elif unit == 'B':
        return num * 1_000
    elif unit == 'M':
        return num
    elif unit == 'K':
        return num * 0.001
    return num


def parse_founders(founder_str):
    """Parse founder string into list of individual names."""
    if not founder_str or not isinstance(founder_str, str):
        return []
    # Handle " and " separators
    s = founder_str.strip()
    if not s:
        return []
    # Split by comma, then handle "and" in the last segment
    parts = [p.strip() for p in s.split(',')]
    result = []
    for part in parts:
        # Handle "X and Y" in a single segment
        if ' and ' in part and len(part.split(' and ')) == 2:
            for sub in part.split(' and '):
                sub = sub.strip()
                if sub:
                    result.append(sub)
        else:
            if part:
                result.append(part)
    return result


def extract_companies(content):
    """Extract COMPANIES array entries from data.js."""
    companies = []
    # Find COMPANIES array
    match = re.search(r'const\s+COMPANIES\s*=\s*\[', content)
    if not match:
        print("[WARN] COMPANIES array not found")
        return companies

    start = match.end()
    # Find matching closing bracket
    depth = 1
    i = start
    while i < len(content) and depth > 0:
        if content[i] == '[':
            depth += 1
        elif content[i] == ']':
            depth -= 1
        i += 1
    array_content = content[start:i - 1]

    # Extract individual company objects
    obj_pattern = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', re.DOTALL)
    for m in obj_pattern.finditer(array_content):
        obj_str = m.group()
        company = {}

        # Extract fields
        for field in ['name', 'founder', 'sector', 'totalRaised', 'valuation', 'fundingStage']:
            field_match = re.search(rf'{field}:\s*"(.*?)"', obj_str)
            if field_match:
                company[field] = field_match.group(1)

        if 'name' in company:
            companies.append(company)

    return companies


def extract_founder_mafias(content):
    """Extract FOUNDER_MAFIAS object from data.js."""
    mafias = {}
    match = re.search(r'(?:const\s+)?FOUNDER_MAFIAS\s*=\s*\{', content)
    if not match:
        print("[WARN] FOUNDER_MAFIAS not found")
        return mafias

    start = match.end()
    depth = 1
    i = start
    while i < len(content) and depth > 0:
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
        i += 1
    block = content[start:i - 1]

    # Find each mafia name
    mafia_names = re.findall(r'"([^"]+Mafia[^"]*|[^"]+Alumni[^"]*|[^"]+Deep Tech[^"]*)":\s*\{', block)

    for mname in mafia_names:
        # Find companies within this mafia
        mafia_match = re.search(rf'"{re.escape(mname)}":\s*\{{.*?companies:\s*\[(.*?)\]', block, re.DOTALL)
        if mafia_match:
            companies_block = mafia_match.group(1)
            # Extract company entries
            entries = re.findall(r'company:\s*"(.*?)".*?founders?:\s*"(.*?)"', companies_block, re.DOTALL)
            mafia_companies = []
            for comp_name, founder_info in entries:
                # Strip parenthetical role info from founder name
                clean_name = re.sub(r'\s*\(.*?\)', '', founder_info).strip()
                mafia_companies.append({
                    'company': comp_name,
                    'founder': clean_name,
                    'fullInfo': founder_info,
                })
            mafias[mname] = mafia_companies

    return mafias


def extract_innovator_scores(content):
    """Extract INNOVATOR_SCORES array for teamPedigree values."""
    scores = {}
    match = re.search(r'const\s+INNOVATOR_SCORES\s*=\s*\[', content)
    if not match:
        return scores

    start = match.end()
    depth = 1
    i = start
    while i < len(content) and depth > 0:
        if content[i] == '[':
            depth += 1
        elif content[i] == ']':
            depth -= 1
        i += 1
    block = content[start:i - 1]

    # Extract company and teamPedigree
    entries = re.findall(r'company:\s*"(.*?)".*?teamPedigree:\s*(\d+)', block, re.DOTALL)
    for comp, team in entries:
        scores[comp] = int(team)

    return scores


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("Founder DNA Index Generator")
    print("=" * 70)

    content = DATA_JS.read_text(encoding='utf-8')
    print(f"Read data.js: {len(content):,} chars")

    # ── Extract data ──
    companies = extract_companies(content)
    mafias = extract_founder_mafias(content)
    innovator_scores = extract_innovator_scores(content)

    print(f"Companies extracted: {len(companies)}")
    print(f"Founder mafias: {len(mafias)} networks")
    for mname, mcomps in mafias.items():
        print(f"  {mname}: {len(mcomps)} companies")
    print(f"Innovator scores (teamPedigree): {len(innovator_scores)} entries")

    # ── Build mafia lookup: company_name → [mafia_names] ──
    company_to_mafias = {}
    for mname, mcomps in mafias.items():
        for mc in mcomps:
            comp = mc['company']
            if comp not in company_to_mafias:
                company_to_mafias[comp] = []
            company_to_mafias[comp].append(mname)

    print(f"Companies with mafia connections: {len(company_to_mafias)}")

    # ── Build serial founder map: founder_name → [company_names] ──
    founder_to_companies = {}
    for c in companies:
        founders = parse_founders(c.get('founder', ''))
        for f in founders:
            fname = f.strip()
            if fname:
                if fname not in founder_to_companies:
                    founder_to_companies[fname] = []
                founder_to_companies[fname].append(c['name'])

    serial_founders = {f: comps for f, comps in founder_to_companies.items() if len(comps) >= 2}
    print(f"Serial founders detected: {len(serial_founders)}")
    for sf, comps in sorted(serial_founders.items(), key=lambda x: -len(x[1])):
        print(f"  {sf}: {comps}")

    # ── Compute capital per founder percentiles ──
    cap_per_founder_vals = []
    for c in companies:
        founders = parse_founders(c.get('founder', ''))
        count = max(len(founders), 1)
        capital = parse_capital(c.get('totalRaised', ''))
        if capital <= 0:
            capital = parse_capital(c.get('valuation', ''))  # fallback
        if capital > 0:
            cap_per_founder_vals.append(capital / count)

    cap_per_founder_vals.sort()
    total_cap_companies = len(cap_per_founder_vals)

    def capital_efficiency_score(cap_per_founder):
        """Convert capital per founder to 0-10 score using percentiles."""
        if cap_per_founder <= 0 or total_cap_companies == 0:
            return 3  # neutral default
        # Find percentile
        idx = 0
        for v in cap_per_founder_vals:
            if v <= cap_per_founder:
                idx += 1
        pct = (idx / total_cap_companies) * 100
        if pct >= 95:
            return 10
        elif pct >= 85:
            return 9
        elif pct >= 70:
            return 8
        elif pct >= 55:
            return 7
        elif pct >= 40:
            return 6
        elif pct >= 25:
            return 5
        elif pct >= 10:
            return 4
        else:
            return 3

    # ── Generate profiles ──
    profiles = []
    for c in companies:
        name = c['name']
        sector = c.get('sector', 'Unknown')
        founders = parse_founders(c.get('founder', ''))
        count = max(len(founders), 1)
        structure = classify_team(count)

        # Mafia pedigree
        mafia_connections = company_to_mafias.get(name, [])
        mafia_count = len(mafia_connections)
        mafia_score = min(mafia_count * 3, 10)

        # Serial founder detection for this company
        company_serial_founders = []
        for f in founders:
            if f in serial_founders:
                company_serial_founders.append(f)
        has_serial = len(company_serial_founders) > 0
        serial_score = 0
        if has_serial:
            max_companies = max(len(serial_founders.get(sf, [])) for sf in company_serial_founders)
            serial_score = min(3 + (max_companies - 2) * 2, 10)

        # Capital efficiency
        capital = parse_capital(c.get('totalRaised', ''))
        if capital <= 0:
            capital = parse_capital(c.get('valuation', ''))
        cap_per_founder = capital / count if capital > 0 else 0
        cap_eff_score = capital_efficiency_score(cap_per_founder)

        # Team size signal
        size_score = team_size_score(count)

        # Team pedigree (from INNOVATOR_SCORES if available, else infer)
        if name in innovator_scores:
            team_ped = innovator_scores[name]
        else:
            # Infer from mafia connections and team size
            inferred = 4  # baseline
            if mafia_count >= 2:
                inferred = 8
            elif mafia_count == 1:
                inferred = 6
            if has_serial:
                inferred = min(inferred + 2, 10)
            team_ped = inferred

        # Composite DNA score (0-100)
        raw = (
            mafia_score * WEIGHTS["mafiaPedigree"]
            + cap_eff_score * WEIGHTS["capitalEfficiency"]
            + serial_score * WEIGHTS["serialBonus"]
            + size_score * WEIGHTS["teamSizeSignal"]
            + team_ped * WEIGHTS["teamPedigree"]
        )
        dna_score = round(raw * 10)  # scale 0-10 weighted avg to 0-100

        profiles.append({
            "company": name,
            "founderCount": count,
            "teamStructure": structure,
            "founders": founders,
            "mafiaConnections": mafia_connections,
            "mafiaCount": mafia_count,
            "serialFounders": company_serial_founders,
            "hasSerialFounder": has_serial,
            "totalRaisedM": round(capital, 1),
            "capitalPerFounderM": round(cap_per_founder, 1),
            "scores": {
                "mafiaPedigree": mafia_score,
                "capitalEfficiency": cap_eff_score,
                "serialBonus": serial_score,
                "teamSizeSignal": size_score,
                "teamPedigree": team_ped,
            },
            "dnaScore": dna_score,
            "sector": sector,
        })

    # Sort by DNA score descending
    profiles.sort(key=lambda p: -p['dnaScore'])

    # ── Sector aggregations ──
    sector_data = {}
    for p in profiles:
        sec = p['sector']
        if sec not in sector_data:
            sector_data[sec] = {
                'companies': [],
                'founderCounts': [],
                'dnaScores': [],
                'mafiaConnected': 0,
            }
        sector_data[sec]['companies'].append(p)
        sector_data[sec]['founderCounts'].append(p['founderCount'])
        sector_data[sec]['dnaScores'].append(p['dnaScore'])
        if p['mafiaCount'] > 0:
            sector_data[sec]['mafiaConnected'] += 1

    sector_profiles = []
    for sec, sd in sector_data.items():
        count = len(sd['companies'])
        avg_fc = round(sum(sd['founderCounts']) / count, 1) if count > 0 else 0
        avg_dna = round(sum(sd['dnaScores']) / count, 1) if count > 0 else 0
        pct_mafia = round((sd['mafiaConnected'] / count) * 100) if count > 0 else 0

        # Dominant team structure
        structures = [c['teamStructure'] for c in sd['companies']]
        structure_counts = {}
        for s in structures:
            structure_counts[s] = structure_counts.get(s, 0) + 1
        dominant = max(structure_counts, key=structure_counts.get) if structure_counts else "unknown"

        # Top 3 by DNA score
        top3 = [c['company'] for c in sorted(sd['companies'], key=lambda x: -x['dnaScore'])[:3]]

        sector_profiles.append({
            "sector": sec,
            "companyCount": count,
            "avgFounderCount": avg_fc,
            "pctMafiaConnected": pct_mafia,
            "avgDnaScore": avg_dna,
            "dominantTeamStructure": dominant,
            "topDnaCompanies": top3,
        })

    sector_profiles.sort(key=lambda s: -s['avgDnaScore'])

    # ── Serial founder map ──
    serial_map = []
    for founder_name, comp_list in sorted(serial_founders.items(), key=lambda x: -len(x[1])):
        sectors = set()
        total_cap = 0
        for c in companies:
            if c['name'] in comp_list:
                sectors.add(c.get('sector', 'Unknown'))
                total_cap += parse_capital(c.get('totalRaised', ''))

        serial_map.append({
            "founder": founder_name,
            "companies": comp_list,
            "sectors": list(sectors),
            "totalCapitalRaisedM": round(total_cap, 1),
        })

    serial_map.sort(key=lambda x: (-len(x['companies']), -x['totalCapitalRaisedM']))

    # ── Summary stats ──
    print(f"\n{'=' * 70}")
    print(f"RESULTS SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total profiles: {len(profiles)}")
    print(f"Sectors: {len(sector_profiles)}")
    print(f"Serial founders: {len(serial_map)}")
    print(f"\nTop 15 by DNA Score:")
    for p in profiles[:15]:
        mafia_str = ', '.join(p['mafiaConnections']) if p['mafiaConnections'] else 'none'
        print(f"  {p['dnaScore']:3d} | {p['company']:30s} | {p['teamStructure']:6s} | mafias: {mafia_str}")

    print(f"\nTeam Structure Distribution:")
    struct_counts = {}
    for p in profiles:
        struct_counts[p['teamStructure']] = struct_counts.get(p['teamStructure'], 0) + 1
    for s in ['solo', 'duo', 'trio', 'squad', 'large']:
        c = struct_counts.get(s, 0)
        pct = round((c / len(profiles)) * 100, 1)
        print(f"  {s:6s}: {c:3d} ({pct}%)")

    # ── Write output ──
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"""// Founder DNA Index — Auto-generated {now}
// {len(profiles)} company founder profiles + {len(sector_profiles)} sector aggregations + {len(serial_map)} serial founders
// Cross-referenced from COMPANIES, FOUNDER_MAFIAS, INNOVATOR_SCORES
// DO NOT EDIT — regenerate with: python3 scripts/generate_founder_dna.py

"""

    OUTPUT_JS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write("const FOUNDER_DNA = ")
        f.write(json.dumps(profiles, indent=2))
        f.write(";\n\n")
        f.write("const FOUNDER_DNA_SECTORS = ")
        f.write(json.dumps(sector_profiles, indent=2))
        f.write(";\n\n")
        f.write("const FOUNDER_SERIAL_MAP = ")
        f.write(json.dumps(serial_map, indent=2))
        f.write(";\n")

    # ── Validate output ──
    output_content = OUTPUT_JS.read_text(encoding='utf-8')
    opens = output_content.count('{')
    closes = output_content.count('}')
    b_opens = output_content.count('[')
    b_closes = output_content.count(']')
    consts = len(re.findall(r'^const\s+', output_content, re.MULTILINE))

    print(f"\n{'=' * 70}")
    print(f"OUTPUT VALIDATION")
    print(f"{'=' * 70}")
    print(f"File: {OUTPUT_JS}")
    print(f"Size: {len(output_content):,} chars")
    print(f"Consts: {consts} (expected 3)")
    print(f"Braces: {{ = {opens}, }} = {closes}, balanced = {opens == closes}")
    print(f"Brackets: [ = {b_opens}, ] = {b_closes}, balanced = {b_opens == b_closes}")

    if opens != closes or b_opens != b_closes:
        print("[ERROR] Bracket/brace mismatch!")
        return 1

    print(f"\n✓ Successfully generated {OUTPUT_JS.name}")
    return 0


if __name__ == "__main__":
    exit(main())
