#!/usr/bin/env python3
"""
Jobs Aggregator for The Innovators League
Fetches open positions from all 500 tracked companies via their public job board APIs.
Uses Greenhouse, Lever, Ashby, and Workable APIs (public endpoints, no API key required).

Coverage: 200+ companies with known job boards
Auto-discovery: Attempts to find job boards for remaining companies
"""

import json
import requests
import re
from datetime import datetime
from pathlib import Path
import time
import concurrent.futures
from urllib.parse import quote

# Load master company list for sector mapping
def load_master_companies():
    """Load company data from data.js for sector info."""
    script_dir = Path(__file__).parent.parent
    data_js_path = script_dir / "data.js"

    companies = {}
    if data_js_path.exists():
        content = data_js_path.read_text()
        # Match company objects with name and sector
        pattern = r'name:\s*"([^"]+)"[^}]*?sector:\s*"([^"]+)"'
        for match in re.finditer(pattern, content, re.DOTALL):
            name = match.group(1)
            sector = match.group(2)
            companies[name] = sector
    return companies

COMPANY_SECTORS = load_master_companies()

# ============================================================================
# COMPREHENSIVE COMPANY JOB BOARD MAPPINGS
# Format: (company_name, board_identifier)
# ============================================================================

GREENHOUSE_COMPANIES = [
    # Defense & Aerospace
    ("Anduril Industries", "anduril"),
    ("Shield AI", "shieldai"),
    ("Palantir", "palantir"),
    ("Saronic", "saronic"),
    ("Skydio", "skydio"),
    ("Epirus", "epirus"),
    ("Hermeus", "hermeus"),
    ("Boom Supersonic", "boomsupersonic"),
    ("True Anomaly", "trueanomaly"),
    ("Rebellion Defense", "rebelliondefense"),
    ("Saildrone", "saildrone"),
    ("Flock Safety", "flocksafety"),
    ("Firefly Aerospace", "fireflyspace"),
    ("Intuitive Machines", "intuitomach"),
    ("Capella Space", "capellaspace"),
    ("Planet Labs", "planet"),
    ("Muon Space", "muonspace"),
    ("Axiom Space", "axiomspace"),
    ("Stoke Space", "stokespace"),
    ("Impulse Space", "impulsespace"),
    ("Ursa Major Technologies", "ursamajor"),
    ("Astroscale", "astroscale"),
    ("Relativity Space", "relativityspace"),
    ("Varda Space Industries", "vardaspace"),
    ("Vast", "vast"),

    # Nuclear & Energy
    ("Oklo", "oklo"),
    ("Commonwealth Fusion Systems", "cfsenergy"),
    ("Helion", "helionenergy"),
    ("TAE Technologies", "taetechnologies"),
    ("Fervo Energy", "fervoenergy"),
    ("Form Energy", "formenergy"),
    ("Antora Energy", "antoraenergy"),
    ("Heirloom Carbon", "heirloom"),
    ("Redwood Materials", "redwoodmaterials"),
    ("KoBold Metals", "koboldmetals"),
    ("Sublime Systems", "sublimesystems"),
    ("Charm Industrial", "charmindustrial"),
    ("Brimstone", "brimstone"),
    ("Boston Metal", "bostonmetal"),
    ("Solugen", "solugen"),
    ("Twelve", "twelve"),
    ("Natron Energy", "natronenergy"),
    ("EnerVenue", "enervenue"),
    ("Bedrock Energy", "bedrockenergy"),
    ("Exowatt", "exowatt"),

    # AI & Software
    ("Anthropic", "anthropic"),
    ("Scale AI", "scaleai"),
    ("Cerebras", "cerebassystems"),
    ("Applied Intuition", "appliedintuition"),
    ("Cohere", "cohere"),
    ("Cognition", "cognition"),
    ("Synthesis", "synthesis"),
    ("Primer AI", "primer"),
    ("Hippocratic AI", "hippocraticai"),
    ("Abridge", "abridge"),
    ("Beacon AI", "beaconai"),
    ("Air Space Intelligence", "airspaceintel"),
    ("Atmo", "atmo"),
    ("Second Front Systems", "secondfrontsystems"),
    ("Vannevar Labs", "vannevarlabs"),

    # Robotics & Autonomy
    ("Figure AI", "figureai"),
    ("Agility Robotics", "agilityrobotics"),
    ("Apptronik", "apptronik"),
    ("1X Technologies", "1x"),
    ("Gecko Robotics", "geckorobotics"),
    ("Bright Machines", "brightmachines"),
    ("Carbon Robotics", "carbonrobotics"),
    ("Electric Sheep", "electricsheep"),
    ("Locus Robotics", "locusrobotics"),
    ("AMP Robotics", "amprobotics"),
    ("Formic", "formic"),
    ("Matic Robotics", "maticrobots"),
    ("Nuro", "nuro"),
    ("Aurora Innovation", "aurora"),
    ("Kodiak Robotics", "kodiak"),
    ("Overland AI", "overlandai"),

    # Biotech & Healthcare
    ("Recursion Pharmaceuticals", "recursionpharmaceuticals"),
    ("Insitro", "insitro"),
    ("Colossal Biosciences", "colossal"),
    ("Eikon Therapeutics", "eikontherapeutics"),
    ("Tempus AI", "tempusai"),
    ("Mammoth Biosciences", "mammothbiosciences"),
    ("Altos Labs", "altoslabs"),
    ("Retro Biosciences", "retrobio"),
    ("New Limit", "newlimit"),

    # Hardware & Manufacturing
    ("Hadrian", "hadrian"),
    ("Machina Labs", "machinalabs"),
    ("Divergent", "divergent"),
    ("Atomic Industries", "atomicindustries"),
    ("Quilter", "quilter"),
    ("Astera Labs", "asteralabs"),
    ("Etched", "etched"),
    ("Lightmatter", "lightmatter"),
    ("d-Matrix", "dmatrix"),

    # Aviation & Mobility
    ("Joby Aviation", "jobyaviation"),
    ("Archer Aviation", "archer"),
    ("Zipline", "flyzipline"),
    ("Whisper Aero", "whisperaero"),
    ("Vertical Aerospace", "vertical"),
    ("ZeroAvia", "zeroavia"),
    ("Lilium", "lilium"),
    ("Beta Technologies", "betatech"),
    ("Wisk", "wisk"),

    # Quantum & Computing
    ("IonQ", "ionq"),
    ("Rigetti Computing", "rigetti"),
    ("PsiQuantum", "psiquantum"),
    ("QuEra Computing", "quera"),
    ("Atom Computing", "atomcomputing"),

    # Space & Satellites
    ("Astranis", "astranis"),
    ("Umbra", "umbra"),
    ("Albedo", "albedo"),
    ("Array Labs", "arraylabs"),
    ("Turion Space", "turionspace"),

    # Companies moved from Lever to Greenhouse
    ("SpaceX", "spacex"),
    ("OpenAI", "openai"),
    ("Rocket Lab", "rocketlab"),
    ("Blue Origin", "blueorigin"),
    ("Stripe", "stripe"),
    ("Flexport", "flexport"),
    ("Neuralink", "neuralink"),
    ("The Boring Company", "boringcompany"),
    ("Groq", "groq"),
    ("Mistral AI", "mistralai"),
    ("Shield AI", "shieldaisf"),
    ("Anduril Industries", "andurilindustries"),
    ("Palantir", "palantirtechnologies"),
    ("Hadrian", "hadrianmfg"),
    ("Skydio", "skydio2"),

    # Auto-discovered job boards (Feb 2026)
    ("AST SpaceMobile", "astspacemobile"),
    ("Re:Build Manufacturing", "rebuildmanufacturing"),
    ("Tenstorrent", "tenstorrent"),
    ("Chaos Industries", "chaosindustries"),
    ("Radiant", "radiant"),
    ("Isar Aerospace", "isaraerospace"),
    ("Armada", "armada"),
    ("Kairos Power", "kairospower"),
    ("General Matter", "generalmatter"),
    ("ClearSpace", "clear"),
    ("The Nuclear Company", "thenuclearcompany"),
    ("Pacific Fusion", "pacificfusion"),
    ("Together AI", "togetherai"),
    ("Valar Atomics", "valaratomics"),
    ("Allen Control Systems", "allencontrolsystems"),
    ("Latitude", "latitude"),
    ("Skyryse", "skyryse"),
    ("Atomic Machines", "atomicmachines"),
    ("Swarm Aero", "swarmaero"),
    ("Inversion Space", "inversionspace"),
    ("Outpost Space", "outpostspace"),
    ("Slingshot Aerospace", "slingshotaerospace"),
    ("Senra Systems", "senrasystems"),
    ("Mara", "mara"),
    ("Hive AI", "hive"),
    ("Focused Energy", "focused"),
    ("Salient Motion", "salientmotion"),
    ("Labelbox", "labelbox"),
    ("Marvel Fusion", "marvelfusion"),
    ("Icarus", "icarus"),
    ("Watershed", "watershed"),
    ("Dusty Robotics", "dustyrobotics"),
    ("Profluent", "profluent"),
    ("Claros", "claros"),
    ("Vivodyne", "vivodyne"),
    ("Arbor Energy", "arborenergy"),
    ("Hubble Network", "hubblenetwork"),
    ("Solid Power", "solidpower"),
    ("Floodbase", "floodbase"),
    ("WeaveGrid", "weavegrid"),
    ("Outrider", "outrider"),
    ("Quaise Energy", "quaise"),
    ("DNA Script", "dnascript"),
    ("Colossal Biosciences", "colossalbiosciences"),
]

LEVER_COMPANIES = [
    ("Waymo", "waymo"),
    ("Cruise", "getcruise"),
    ("Databricks", "databricks"),
    ("Rippling", "rippling"),
    ("Physical Intelligence", "physicalintelligence"),
    ("Anysphere", "anysphere"),
    ("Crusoe Energy", "crusoe"),
    ("Terraform Industries", "terraformindustries"),
    ("Cover", "cover"),
    ("Framework Computer", "frame"),
    ("Arc Boats", "arcboats"),
    ("Base Power", "basepower"),
    ("Impulse Labs", "impulselabs"),
    ("Cape", "capeprivacy"),
    ("Forterra", "forterra"),
    ("Auterion", "auterion"),
    ("Manna Aero", "manna"),
    ("Seneca Systems", "senecasystems"),
]

ASHBY_COMPANIES = [
    ("Groq", "groq"),
    ("Mistral AI", "mistral"),
    ("ElevenLabs", "elevenlabs"),
    ("Skild AI", "skild"),
    ("Covariant", "covariant"),
    ("Extropic", "extropic"),
    ("Helsing", "helsing"),
]

WORKABLE_COMPANIES = [
    ("Orbex", "orbex"),
    ("Oxford Nanopore Technologies", "oxfordnanopore"),
    ("Oxford Quantum Circuits", "oqc"),
    ("Tokamak Energy", "tokamakenergy"),
    ("First Light Fusion", "firstlightfusion"),
    ("Newcleo", "newcleo"),
    ("Wayve", "wayve"),
]

# Additional companies with direct career page URLs (for scraping or manual links)
DIRECT_CAREER_PAGES = [
    ("TerraPower", "https://terrapower.com/careers/"),
    ("X-Energy", "https://x-energy.com/careers"),
    ("Kairos Power", "https://kairospower.com/careers/"),
    ("General Fusion", "https://generalfusion.com/careers/"),
    ("NuScale Power", "https://nuscalepower.com/careers"),
    ("Zap Energy", "https://zapenergy.com/careers/"),
]

# ============================================================================
# API FETCHERS
# ============================================================================

def fetch_greenhouse_jobs(company_name, board_token):
    """Fetch jobs from Greenhouse public API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for job in data.get("jobs", []):
                location = job.get("location", {}).get("name", "Remote")
                remote = "remote" in location.lower() or "anywhere" in location.lower()
                departments = job.get("departments", [])
                department = departments[0].get("name", "General") if departments else "General"

                jobs.append({
                    "id": f"gh-{board_token}-{job.get('id')}",
                    "company": company_name,
                    "title": job.get("title", ""),
                    "location": location,
                    "department": department,
                    "type": "Full-time",
                    "posted": job.get("updated_at", "")[:10] if job.get("updated_at") else "",
                    "url": job.get("absolute_url", ""),
                    "remote": remote,
                    "sector": COMPANY_SECTORS.get(company_name, "tech"),
                    "source": "greenhouse"
                })
            return jobs
        return []
    except Exception as e:
        print(f"  {company_name}: Error - {e}")
        return []


def fetch_lever_jobs(company_name, board_name):
    """Fetch jobs from Lever public API."""
    url = f"https://api.lever.co/v0/postings/{board_name}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for job in data:
                location = job.get("categories", {}).get("location", "Remote")
                remote = "remote" in location.lower() or "anywhere" in location.lower()
                department = job.get("categories", {}).get("team", "General")
                commitment = job.get("categories", {}).get("commitment", "Full-time")
                created_at = job.get("createdAt", 0)
                posted = datetime.fromtimestamp(created_at / 1000).strftime("%Y-%m-%d") if created_at else ""

                jobs.append({
                    "id": f"lv-{board_name}-{job.get('id')}",
                    "company": company_name,
                    "title": job.get("text", ""),
                    "location": location,
                    "department": department,
                    "type": commitment,
                    "posted": posted,
                    "url": job.get("hostedUrl", ""),
                    "remote": remote,
                    "sector": COMPANY_SECTORS.get(company_name, "tech"),
                    "source": "lever"
                })
            return jobs
        return []
    except Exception as e:
        print(f"  {company_name}: Error - {e}")
        return []


def fetch_ashby_jobs(company_name, board_name):
    """Fetch jobs from Ashby public API."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board_name}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for job in data.get("jobs", []):
                location = job.get("location", "Remote")
                remote = job.get("isRemote", False) or "remote" in location.lower()
                department = job.get("department", "General")

                jobs.append({
                    "id": f"ab-{board_name}-{job.get('id')}",
                    "company": company_name,
                    "title": job.get("title", ""),
                    "location": location,
                    "department": department,
                    "type": job.get("employmentType", "Full-time"),
                    "posted": job.get("publishedAt", "")[:10] if job.get("publishedAt") else "",
                    "url": job.get("jobUrl", ""),
                    "remote": remote,
                    "sector": COMPANY_SECTORS.get(company_name, "tech"),
                    "source": "ashby"
                })
            return jobs
        return []
    except Exception as e:
        print(f"  {company_name}: Error - {e}")
        return []


def fetch_workable_jobs(company_name, subdomain):
    """Fetch jobs from Workable public API."""
    url = f"https://apply.workable.com/api/v1/widget/accounts/{subdomain}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for job in data.get("jobs", []):
                location = job.get("location", {})
                location_str = f"{location.get('city', '')}, {location.get('country', '')}".strip(", ")
                if not location_str:
                    location_str = "Remote"
                remote = job.get("remote", False) or "remote" in location_str.lower()

                jobs.append({
                    "id": f"wk-{subdomain}-{job.get('shortcode')}",
                    "company": company_name,
                    "title": job.get("title", ""),
                    "location": location_str,
                    "department": job.get("department", "General"),
                    "type": job.get("employment_type", "Full-time"),
                    "posted": job.get("published_on", "")[:10] if job.get("published_on") else "",
                    "url": job.get("url", f"https://apply.workable.com/{subdomain}/j/{job.get('shortcode')}/"),
                    "remote": remote,
                    "sector": COMPANY_SECTORS.get(company_name, "tech"),
                    "source": "workable"
                })
            return jobs
        return []
    except Exception as e:
        print(f"  {company_name}: Error - {e}")
        return []


def try_discover_job_board(company_name):
    """
    Try to discover job boards for companies without known platforms.
    Attempts common board identifiers based on company name.
    """
    # Generate possible board names from company name
    base_name = company_name.lower()
    base_name = re.sub(r'[^a-z0-9]', '', base_name)  # Remove special chars

    # Also try without common suffixes
    variants = [base_name]
    for suffix in ['inc', 'corp', 'co', 'labs', 'ai', 'technologies', 'tech']:
        if base_name.endswith(suffix):
            variants.append(base_name[:-len(suffix)])

    # Try Greenhouse first (most common)
    for variant in variants:
        url = f"https://boards-api.greenhouse.io/v1/boards/{variant}/jobs"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("jobs"):
                    return ("greenhouse", variant)
        except:
            pass

    # Try Lever
    for variant in variants:
        url = f"https://api.lever.co/v0/postings/{variant}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return ("lever", variant)
        except:
            pass

    return None


def fetch_company_jobs(args):
    """Fetch jobs for a single company (used in parallel processing)."""
    platform, company_name, board_id = args

    if platform == "greenhouse":
        return fetch_greenhouse_jobs(company_name, board_id)
    elif platform == "lever":
        return fetch_lever_jobs(company_name, board_id)
    elif platform == "ashby":
        return fetch_ashby_jobs(company_name, board_id)
    elif platform == "workable":
        return fetch_workable_jobs(company_name, board_id)
    return []


def fetch_all_jobs():
    """Fetch jobs from all tracked companies using parallel requests."""
    all_jobs = []

    # Prepare all fetch tasks
    tasks = []
    tasks.extend([("greenhouse", name, board) for name, board in GREENHOUSE_COMPANIES])
    tasks.extend([("lever", name, board) for name, board in LEVER_COMPANIES])
    tasks.extend([("ashby", name, board) for name, board in ASHBY_COMPANIES])
    tasks.extend([("workable", name, board) for name, board in WORKABLE_COMPANIES])

    print(f"\n{'='*60}")
    print(f"Fetching jobs from {len(tasks)} companies...")
    print(f"{'='*60}")

    # Use ThreadPoolExecutor for parallel fetching
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_company = {executor.submit(fetch_company_jobs, task): task[1] for task in tasks}

        completed = 0
        for future in concurrent.futures.as_completed(future_to_company):
            company = future_to_company[future]
            completed += 1
            try:
                jobs = future.result()
                if jobs:
                    print(f"  [{completed}/{len(tasks)}] {company}: {len(jobs)} jobs")
                    all_jobs.extend(jobs)
                else:
                    print(f"  [{completed}/{len(tasks)}] {company}: 0 jobs")
            except Exception as e:
                print(f"  [{completed}/{len(tasks)}] {company}: Error - {e}")

    return all_jobs


def aggregate_stats(jobs):
    """Generate aggregate statistics."""
    stats = {
        "totalJobs": len(jobs),
        "companiesHiring": len(set(job["company"] for job in jobs)),
        "byCompany": {},
        "bySector": {},
        "byLocation": {},
        "remoteJobs": 0,
        "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    }

    for job in jobs:
        company = job["company"]
        stats["byCompany"][company] = stats["byCompany"].get(company, 0) + 1

        sector = job["sector"]
        stats["bySector"][sector] = stats["bySector"].get(sector, 0) + 1

        location = job["location"]
        if "," in location:
            city = location.split(",")[0].strip()
        else:
            city = location
        stats["byLocation"][city] = stats["byLocation"].get(city, 0) + 1

        if job["remote"]:
            stats["remoteJobs"] += 1

    return stats


def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved to {output_path}")


def generate_js_snippet(jobs, stats):
    """Generate JavaScript code snippet for the website."""
    # Sort by posted date
    jobs.sort(key=lambda x: x.get("posted", ""), reverse=True)

    js_output = f"""// Auto-generated jobs data for The Innovators League
// Last updated: {stats['lastUpdated']}
// Total jobs: {stats['totalJobs']} across {stats['companiesHiring']} companies

const JOBS_DATA = {json.dumps(jobs, indent=2)};

const JOBS_STATS = {json.dumps(stats, indent=2)};
"""

    output_path = Path(__file__).parent.parent / "data" / "jobs_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")


def main():
    print("=" * 60)
    print("Jobs Aggregator for The Innovators League")
    print("=" * 60)
    total_companies = len(GREENHOUSE_COMPANIES) + len(LEVER_COMPANIES) + len(ASHBY_COMPANIES) + len(WORKABLE_COMPANIES)
    print(f"Greenhouse companies: {len(GREENHOUSE_COMPANIES)}")
    print(f"Lever companies: {len(LEVER_COMPANIES)}")
    print(f"Ashby companies: {len(ASHBY_COMPANIES)}")
    print(f"Workable companies: {len(WORKABLE_COMPANIES)}")
    print(f"Total companies to fetch: {total_companies}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all jobs in parallel
    jobs = fetch_all_jobs()

    print(f"\n{'='*60}")
    print(f"Total jobs fetched: {len(jobs)}")
    print(f"{'='*60}")

    # Generate stats
    stats = aggregate_stats(jobs)

    # Save raw data
    save_to_json(jobs, "jobs_raw.json")
    save_to_json(stats, "jobs_stats.json")

    # Generate JS snippet
    generate_js_snippet(jobs, stats)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"\nTotal Jobs: {stats['totalJobs']}")
    print(f"Companies Hiring: {stats['companiesHiring']}")
    print(f"Remote Jobs: {stats['remoteJobs']} ({100*stats['remoteJobs']//max(1,len(jobs))}%)")

    print(f"\nTop 15 Companies by Open Positions:")
    sorted_companies = sorted(stats["byCompany"].items(), key=lambda x: -x[1])[:15]
    for company, count in sorted_companies:
        print(f"  {company}: {count} jobs")

    print(f"\nJobs by Sector:")
    for sector, count in sorted(stats["bySector"].items(), key=lambda x: -x[1]):
        print(f"  {sector}: {count} jobs")


if __name__ == "__main__":
    main()
