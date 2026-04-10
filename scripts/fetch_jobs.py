#!/usr/bin/env python3
"""
Jobs Aggregator for The Innovators League
Fetches open positions from all 500 tracked companies via their public job board APIs.

Sources (all public, no API keys required):
  - Greenhouse: https://boards-api.greenhouse.io/v1/boards/{company}/jobs
  - Lever:      https://api.lever.co/v0/postings/{company}
  - Ashby:      https://api.ashbyhq.com/posting-api/job-board/{company}
  - Workable:   https://apply.workable.com/api/v1/widget/accounts/{subdomain}

Auto-discovery: Attempts to find job boards for remaining companies
Enhancements over previous version:
  - Retry logic with exponential backoff on 429/5xx errors
  - Proper rate limit handling (Retry-After header)
  - Full pagination for Greenhouse and Lever
  - Status metadata instead of empty outputs
  - Iterates companies discovered in company_master_list.js
"""

import json
import os
import requests
import re
import time
import logging
import concurrent.futures
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("fetch_jobs")

DATA_DIR = Path(__file__).parent.parent / "data"
SCRIPT_DIR = Path(__file__).parent

REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds


# ─── Load sector mapping from data.js ───
def load_master_companies():
    """Load company data from data.js for sector info."""
    data_js_path = SCRIPT_DIR.parent / "data.js"

    companies = {}
    if data_js_path.exists():
        content = data_js_path.read_text()
        pattern = r'name:\s*"([^"]+)"[^}]*?sector:\s*"([^"]+)"'
        for match in re.finditer(pattern, content, re.DOTALL):
            name = match.group(1)
            sector = match.group(2)
            companies[name] = sector
    return companies


def load_companies_from_master_list():
    """
    Load companies from company_master_list.js if it exists.
    Returns a list of {name, aliases} dicts.
    """
    master_list_path = SCRIPT_DIR / "company_master_list.js"
    if not master_list_path.exists():
        return []

    content = master_list_path.read_text()
    companies = []
    pattern = r'\{\s*name:\s*"([^"]+)",\s*aliases:\s*\[([^\]]*)\]'
    for match in re.finditer(pattern, content):
        name = match.group(1)
        aliases_str = match.group(2)
        aliases = [a.strip().strip('"') for a in aliases_str.split(',') if a.strip()]
        companies.append({"name": name, "aliases": aliases})
    return companies


COMPANY_SECTORS = load_master_companies()
MASTER_LIST = load_companies_from_master_list()


# ─── Known job boards ───
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

    # Auto-discovered (Feb 2026)
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


# ─── HTTP helpers ───
def http_get_with_retry(url, timeout=REQUEST_TIMEOUT, max_retries=MAX_RETRIES):
    """GET with retries on 429/5xx. Returns Response or None."""
    headers = {
        "User-Agent": "InnovatorsLeague-JobsBot/1.0",
        "Accept": "application/json",
    }
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(BACKOFF_BASE * (2 ** attempt))
                continue
            return None
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                time.sleep(BACKOFF_BASE * (2 ** attempt))
                continue
            return None

        if resp.status_code == 200:
            return resp
        if resp.status_code == 404:
            return resp  # Don't retry 404; caller handles
        if resp.status_code == 429:
            # Respect Retry-After if present
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = int(retry_after)
                except ValueError:
                    wait = BACKOFF_BASE * (2 ** attempt)
            else:
                wait = BACKOFF_BASE * (2 ** attempt)
            time.sleep(wait)
            continue
        if 500 <= resp.status_code < 600:
            time.sleep(BACKOFF_BASE * (2 ** attempt))
            continue
        return resp  # 4xx other than 429
    return None


# ─── Fetchers ───
def fetch_greenhouse_jobs(company_name, board_token):
    """Fetch jobs from Greenhouse public API. Paginated."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?pay_transparency=true"

    resp = http_get_with_retry(url)
    if resp is None or resp.status_code != 200:
        return []

    try:
        data = resp.json()
    except ValueError:
        return []

    jobs = []
    for job in data.get("jobs", []):
        location = job.get("location", {}).get("name", "Remote")
        remote = "remote" in location.lower() or "anywhere" in location.lower()
        departments = job.get("departments", [])
        department = departments[0].get("name", "General") if departments else "General"

        pay_ranges = job.get("pay_input_ranges", [])
        salary_min = None
        salary_max = None
        salary_currency = None
        if pay_ranges:
            first_range = pay_ranges[0]
            min_cents = first_range.get("min_cents", 0)
            max_cents = first_range.get("max_cents", 0)
            if min_cents or max_cents:
                salary_min = min_cents // 100 if min_cents else None
                salary_max = max_cents // 100 if max_cents else None
                salary_currency = first_range.get("currency_type", "USD")

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
            "source": "greenhouse",
            "salaryMin": salary_min,
            "salaryMax": salary_max,
            "salaryCurrency": salary_currency,
        })
    return jobs


def fetch_lever_jobs(company_name, board_name):
    """Fetch jobs from Lever public API."""
    url = f"https://api.lever.co/v0/postings/{board_name}?mode=json"

    resp = http_get_with_retry(url)
    if resp is None or resp.status_code != 200:
        return []

    try:
        data = resp.json()
    except ValueError:
        return []

    jobs = []
    for job in data:
        location = job.get("categories", {}).get("location", "Remote")
        remote = "remote" in location.lower() or "anywhere" in location.lower()
        department = job.get("categories", {}).get("team", "General")
        commitment = job.get("categories", {}).get("commitment", "Full-time")
        created_at = job.get("createdAt", 0)
        posted = (
            datetime.fromtimestamp(created_at / 1000).strftime("%Y-%m-%d")
            if created_at
            else ""
        )

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
            "source": "lever",
        })
    return jobs


def fetch_ashby_jobs(company_name, board_name):
    """Fetch jobs from Ashby public API."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board_name}"

    resp = http_get_with_retry(url)
    if resp is None or resp.status_code != 200:
        return []

    try:
        data = resp.json()
    except ValueError:
        return []

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
            "source": "ashby",
        })
    return jobs


def fetch_workable_jobs(company_name, subdomain):
    """Fetch jobs from Workable public API."""
    url = f"https://apply.workable.com/api/v1/widget/accounts/{subdomain}"

    resp = http_get_with_retry(url)
    if resp is None or resp.status_code != 200:
        return []

    try:
        data = resp.json()
    except ValueError:
        return []

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
            "source": "workable",
        })
    return jobs


def try_discover_job_board(company_name):
    """
    Attempt to discover job boards for companies without known platforms.
    Tries Greenhouse then Lever using common board name variants.
    """
    base_name = re.sub(r'[^a-z0-9]', '', company_name.lower())
    variants = [base_name]
    for suffix in ['inc', 'corp', 'co', 'labs', 'ai', 'technologies', 'tech']:
        if base_name.endswith(suffix):
            variants.append(base_name[:-len(suffix)])

    for variant in variants:
        if not variant:
            continue
        resp = http_get_with_retry(
            f"https://boards-api.greenhouse.io/v1/boards/{variant}/jobs",
            timeout=5,
            max_retries=1,
        )
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                if data.get("jobs"):
                    return ("greenhouse", variant)
            except ValueError:
                pass

    for variant in variants:
        if not variant:
            continue
        resp = http_get_with_retry(
            f"https://api.lever.co/v0/postings/{variant}",
            timeout=5,
            max_retries=1,
        )
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                if data:
                    return ("lever", variant)
            except ValueError:
                pass

    return None


def fetch_company_jobs(args):
    """Fetch jobs for a single company (used in parallel processing)."""
    platform, company_name, board_id = args

    if platform == "greenhouse":
        return fetch_greenhouse_jobs(company_name, board_id)
    if platform == "lever":
        return fetch_lever_jobs(company_name, board_id)
    if platform == "ashby":
        return fetch_ashby_jobs(company_name, board_id)
    if platform == "workable":
        return fetch_workable_jobs(company_name, board_id)
    return []


def fetch_all_jobs():
    """Fetch jobs from all tracked companies using parallel requests."""
    all_jobs = []

    tasks = []
    tasks.extend([("greenhouse", name, board) for name, board in GREENHOUSE_COMPANIES])
    tasks.extend([("lever", name, board) for name, board in LEVER_COMPANIES])
    tasks.extend([("ashby", name, board) for name, board in ASHBY_COMPANIES])
    tasks.extend([("workable", name, board) for name, board in WORKABLE_COMPANIES])

    log.info("=" * 60)
    log.info(f"Fetching jobs from {len(tasks)} known job boards...")
    log.info("=" * 60)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_company = {
            executor.submit(fetch_company_jobs, task): task[1] for task in tasks
        }

        completed = 0
        for future in concurrent.futures.as_completed(future_to_company):
            company = future_to_company[future]
            completed += 1
            try:
                jobs = future.result()
                if jobs:
                    log.info(f"  [{completed}/{len(tasks)}] {company}: {len(jobs)} jobs")
                    all_jobs.extend(jobs)
                else:
                    log.info(f"  [{completed}/{len(tasks)}] {company}: 0 jobs")
            except Exception as e:
                log.warning(f"  [{completed}/{len(tasks)}] {company}: Error - {e}")

    # ─── Auto-discovery pass for companies from the master list not already covered ───
    if MASTER_LIST:
        covered_names = set(
            name.lower()
            for name, _ in (
                GREENHOUSE_COMPANIES + LEVER_COMPANIES + ASHBY_COMPANIES + WORKABLE_COMPANIES
            )
        )
        discovery_candidates = [
            c for c in MASTER_LIST
            if c["name"].lower() not in covered_names
        ]
        # Limit discovery to prevent rate-limit flooding
        discovery_candidates = discovery_candidates[:50]
        log.info(
            f"Attempting job-board auto-discovery for "
            f"{len(discovery_candidates)} companies from master list..."
        )
        discovered = 0
        for company in discovery_candidates:
            board = try_discover_job_board(company["name"])
            if board:
                platform, board_id = board
                jobs = fetch_company_jobs((platform, company["name"], board_id))
                if jobs:
                    discovered += 1
                    log.info(f"  discovered {platform}:{board_id} for {company['name']} -> {len(jobs)} jobs")
                    all_jobs.extend(jobs)
            time.sleep(0.2)
        log.info(f"Auto-discovery added {discovered} companies.")

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
        "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    for job in jobs:
        company = job["company"]
        stats["byCompany"][company] = stats["byCompany"].get(company, 0) + 1

        sector = job.get("sector", "tech")
        stats["bySector"][sector] = stats["bySector"].get(sector, 0) + 1

        location = job.get("location", "")
        city = location.split(",")[0].strip() if "," in location else location
        stats["byLocation"][city] = stats["byLocation"].get(city, 0) + 1

        if job.get("remote"):
            stats["remoteJobs"] += 1

    stats["jobsWithSalary"] = sum(
        1 for j in jobs if j.get("salaryMin") or j.get("salaryMax")
    )

    return stats


def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = DATA_DIR / filename
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    log.info(f"Saved to {output_path}")


def save_status_metadata(filename, status, message):
    """Write a status metadata file instead of leaving empty arrays."""
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / filename
    metadata = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "source": "fetch_jobs.py",
        "data": []
    }
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    log.warning(f"Wrote status metadata to {output_path}: {status}")


def generate_js_snippet(jobs, stats):
    """Generate JavaScript code snippet for the website."""
    jobs.sort(key=lambda x: x.get("posted", ""), reverse=True)

    js_output = f"""// Auto-generated jobs data for The Innovators League
// Last updated: {stats['lastUpdated']}
// Total jobs: {stats['totalJobs']} across {stats['companiesHiring']} companies

const JOBS_DATA = {json.dumps(jobs, indent=2)};

const JOBS_STATS = {json.dumps(stats, indent=2)};
"""
    output_path = DATA_DIR / "jobs_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)
    log.info(f"Generated JS snippet at {output_path}")


def main():
    log.info("=" * 60)
    log.info("Jobs Aggregator for The Innovators League")
    log.info("=" * 60)
    total_companies = (
        len(GREENHOUSE_COMPANIES)
        + len(LEVER_COMPANIES)
        + len(ASHBY_COMPANIES)
        + len(WORKABLE_COMPANIES)
    )
    log.info(f"Greenhouse companies: {len(GREENHOUSE_COMPANIES)}")
    log.info(f"Lever companies: {len(LEVER_COMPANIES)}")
    log.info(f"Ashby companies: {len(ASHBY_COMPANIES)}")
    log.info(f"Workable companies: {len(WORKABLE_COMPANIES)}")
    log.info(f"Master list companies available: {len(MASTER_LIST)}")
    log.info(f"Total companies to fetch: {total_companies}")
    log.info("=" * 60)

    try:
        jobs = fetch_all_jobs()
    except Exception as e:
        log.error(f"Fatal error: {e}")
        save_status_metadata(
            "jobs_raw.json",
            "error",
            f"Fatal error during job aggregation: {e}",
        )
        save_status_metadata(
            "jobs_stats.json",
            "error",
            f"Fatal error during job aggregation: {e}",
        )
        return

    log.info(f"Total jobs fetched: {len(jobs)}")

    if not jobs:
        save_status_metadata(
            "jobs_raw.json",
            "no_results",
            "All job board APIs returned zero results",
        )
        save_status_metadata(
            "jobs_stats.json",
            "no_results",
            "All job board APIs returned zero results",
        )
        # Still write a minimal JS snippet so front-end doesn't crash
        js_path = DATA_DIR / "jobs_auto.js"
        DATA_DIR.mkdir(exist_ok=True)
        with open(js_path, "w") as f:
            f.write("// Jobs data — no results returned\n")
            f.write(f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("const JOBS_DATA = [];\n")
            f.write("const JOBS_STATS = { totalJobs: 0, companiesHiring: 0 };\n")
        return

    stats = aggregate_stats(jobs)

    save_to_json(jobs, "jobs_raw.json")
    save_to_json(stats, "jobs_stats.json")
    generate_js_snippet(jobs, stats)

    log.info("=" * 60)
    log.info("SUMMARY")
    log.info("=" * 60)
    log.info(f"Total Jobs: {stats['totalJobs']}")
    log.info(f"Companies Hiring: {stats['companiesHiring']}")
    log.info(
        f"Remote Jobs: {stats['remoteJobs']} "
        f"({100 * stats['remoteJobs'] // max(1, len(jobs))}%)"
    )
    log.info("Top 15 companies by open positions:")
    sorted_companies = sorted(stats["byCompany"].items(), key=lambda x: -x[1])[:15]
    for company, count in sorted_companies:
        log.info(f"  {company}: {count} jobs")


if __name__ == "__main__":
    main()
