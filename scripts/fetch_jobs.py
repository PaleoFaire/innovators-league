#!/usr/bin/env python3
"""
Jobs Aggregator for The Innovators League
Pulls open positions from every job board in data/pulse/job_boards.json — the
registry that scripts/discover_job_boards.py maintains — through the public,
keyless ATS endpoints implemented in scripts/job_boards.py (Greenhouse, Lever,
Ashby, Workable, Rippling, BambooHR, SmartRecruiters, Workday, Recruitee,
Personio, Breezy, Pinpoint, Teamtailor, JazzHR, iCIMS).

Outputs (all consumed downstream — keep the shapes):
  data/jobs_raw.json    list of job records (id, company, title, location, department,
                        type, posted, url, remote, sector, source, salary*)
  data/jobs_stats.json  aggregate stats + a "boards" health list (one row per board:
                        company, platform, slug, status ok|empty|error, jobs) that the
                        discovery script reads to re-check boards that return nothing
  data/jobs_auto.js     const JOBS_DATA / JOBS_STATS for the legacy page

Usage:
  python3 scripts/fetch_jobs.py            # full pull
  python3 scripts/fetch_jobs.py --only "Anduril Industries,Shield AI"
  python3 scripts/fetch_jobs.py --platform workday
"""
import concurrent.futures
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import job_boards as jb  # noqa: E402

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger("fetch_jobs")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCRIPT_DIR = Path(__file__).resolve().parent
MAX_WORKERS = 12


# ─── Sector lookup from data.js ───
def load_master_companies():
    """{company name: sector} from data.js (regex — data.js is a JS file, not JSON)."""
    data_js_path = SCRIPT_DIR.parent / "data.js"
    companies = {}
    if data_js_path.exists():
        content = data_js_path.read_text(encoding="utf-8")
        for match in re.finditer(r'name:\s*"([^"]+)"[^}]*?sector:\s*"([^"]+)"', content, re.DOTALL):
            companies[match.group(1)] = match.group(2)
    return companies


COMPANY_SECTORS = load_master_companies()


# ─── Back-compat shims (older scripts import these names) ───
http_get_with_retry = jb.http_get_with_retry


def fetch_greenhouse_jobs(company_name, board_token):
    return jb.fetch_greenhouse(company_name, board_token, COMPANY_SECTORS.get(company_name, "tech")) or []


def fetch_lever_jobs(company_name, board_name):
    return jb.fetch_lever(company_name, board_name, COMPANY_SECTORS.get(company_name, "tech")) or []


def fetch_ashby_jobs(company_name, board_name):
    return jb.fetch_ashby(company_name, board_name, COMPANY_SECTORS.get(company_name, "tech")) or []


def fetch_workable_jobs(company_name, subdomain):
    return jb.fetch_workable(company_name, subdomain, COMPANY_SECTORS.get(company_name, "tech")) or []


def fetch_company_jobs(args):
    """(platform, company, slug) -> list of jobs ([] when the board is gone)."""
    platform, company_name, board_id = args
    jobs = jb.fetch_board(platform, company_name, board_id, COMPANY_SECTORS.get(company_name, "tech"))
    return jobs or []


# ─── The pull ───
def fetch_one(rec):
    """Registry record -> (rec, jobs or None, seconds)."""
    t0 = time.time()
    try:
        jobs = jb.fetch_board(rec["platform"], rec["company"], rec["slug"], COMPANY_SECTORS.get(rec["company"], "tech"))
    except Exception as e:  # noqa: BLE001 — one bad board must not sink the pull
        log.warning(f"  {rec['company']} ({rec['platform']}/{rec['slug']}): error {e}")
        jobs = None
    return rec, jobs, time.time() - t0


def fetch_all_jobs(registry):
    all_jobs, health, seen_ids = [], [], set()
    log.info("=" * 60)
    log.info(f"Fetching jobs from {len(registry)} boards ({len({r['company'] for r in registry})} companies)...")
    log.info("=" * 60)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_one, rec) for rec in registry]
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            rec, jobs, secs = fut.result()
            row = {"company": rec["company"], "platform": rec["platform"], "slug": rec["slug"]}
            if jobs is None:
                row.update(status="error", jobs=0)
                log.info(f"  [{i}/{len(registry)}] {rec['company']}: board unreachable ({rec['platform']}/{rec['slug']})")
            else:
                fresh = [j for j in jobs if j["id"] not in seen_ids]
                seen_ids.update(j["id"] for j in fresh)
                all_jobs.extend(fresh)
                row.update(status="ok" if fresh else "empty", jobs=len(fresh))
                log.info(f"  [{i}/{len(registry)}] {rec['company']}: {len(fresh)} jobs ({rec['platform']}, {secs:.1f}s)")
            health.append(row)
    health.sort(key=lambda r: (r["company"].lower(), r["platform"]))
    return all_jobs, health


def aggregate_stats(jobs, health):
    stats = {
        "totalJobs": len(jobs),
        "companiesHiring": len({job["company"] for job in jobs}),
        "boardsTotal": len(health),
        "boardsOk": sum(1 for b in health if b["status"] == "ok"),
        "boardsEmpty": sum(1 for b in health if b["status"] == "empty"),
        "boardsError": sum(1 for b in health if b["status"] == "error"),
        "byCompany": {},
        "bySector": {},
        "bySource": {},
        "byLocation": {},
        "remoteJobs": 0,
        "lastUpdated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    for job in jobs:
        stats["byCompany"][job["company"]] = stats["byCompany"].get(job["company"], 0) + 1
        sector = job.get("sector", "tech")
        stats["bySector"][sector] = stats["bySector"].get(sector, 0) + 1
        src = job.get("source", "")
        stats["bySource"][src] = stats["bySource"].get(src, 0) + 1
        location = job.get("location", "")
        city = location.split(",")[0].strip() if "," in location else location
        stats["byLocation"][city] = stats["byLocation"].get(city, 0) + 1
        if job.get("remote"):
            stats["remoteJobs"] += 1
    stats["jobsWithSalary"] = sum(1 for j in jobs if j.get("salaryMin") or j.get("salaryMax"))
    stats["boards"] = health
    return stats


def save_to_json(data, filename):
    output_path = DATA_DIR / filename
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info(f"Saved to {output_path}")


def save_status_metadata(filename, status, message):
    """Write a status metadata file instead of leaving empty arrays."""
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / filename
    metadata = {"status": status, "message": message, "timestamp": datetime.now().isoformat(), "source": "fetch_jobs.py", "data": []}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    log.warning(f"Wrote status metadata to {output_path}: {status}")


def generate_js_snippet(jobs, stats):
    jobs = sorted(jobs, key=lambda x: x.get("posted", ""), reverse=True)
    slim_stats = {k: v for k, v in stats.items() if k != "boards"}
    js_output = f"""// Auto-generated jobs data for The Innovators League
// Last updated: {stats['lastUpdated']}
// Total jobs: {stats['totalJobs']} across {stats['companiesHiring']} companies

const JOBS_DATA = {json.dumps(jobs, indent=2, ensure_ascii=False)};

const JOBS_STATS = {json.dumps(slim_stats, indent=2, ensure_ascii=False)};
"""
    output_path = DATA_DIR / "jobs_auto.js"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(js_output)
    log.info(f"Generated JS snippet at {output_path}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    only = platform = None
    if "--only" in argv:
        only = {x.strip() for x in argv[argv.index("--only") + 1].split(",")}
    if "--platform" in argv:
        platform = argv[argv.index("--platform") + 1]

    registry = jb.load_registry()
    if not registry:
        log.error(f"No boards in {jb.REGISTRY_PATH} — run scripts/discover_job_boards.py first")
        save_status_metadata("jobs_raw.json", "error", "job board registry missing or empty")
        save_status_metadata("jobs_stats.json", "error", "job board registry missing or empty")
        return
    if only:
        registry = [r for r in registry if r["company"] in only]
    if platform:
        registry = [r for r in registry if r["platform"] == platform]

    by_platform = {}
    for r in registry:
        by_platform[r["platform"]] = by_platform.get(r["platform"], 0) + 1
    log.info("=" * 60)
    log.info("Jobs Aggregator for The Innovators League")
    log.info("=" * 60)
    for p, n in sorted(by_platform.items(), key=lambda x: -x[1]):
        log.info(f"  {p:16s} {n:4d} boards")
    log.info(f"Total boards: {len(registry)} · companies: {len({r['company'] for r in registry})}")

    try:
        jobs, health = fetch_all_jobs(registry)
    except Exception as e:  # noqa: BLE001
        log.error(f"Fatal error: {e}")
        save_status_metadata("jobs_raw.json", "error", f"Fatal error during job aggregation: {e}")
        save_status_metadata("jobs_stats.json", "error", f"Fatal error during job aggregation: {e}")
        return

    if only or platform:
        # partial pull: print, don't overwrite the feed
        log.info(f"Partial pull: {len(jobs)} jobs from {len(health)} boards (not written)")
        for b in health:
            log.info(f"  {b['status']:5s} {b['jobs']:5d}  {b['company']} ({b['platform']}/{b['slug']})")
        return

    log.info(f"Total jobs fetched: {len(jobs)}")
    if not jobs:
        save_status_metadata("jobs_raw.json", "no_results", "All job board APIs returned zero results")
        save_status_metadata("jobs_stats.json", "no_results", "All job board APIs returned zero results")
        js_path = DATA_DIR / "jobs_auto.js"
        DATA_DIR.mkdir(exist_ok=True)
        with open(js_path, "w", encoding="utf-8") as f:
            f.write("// Jobs data — no results returned\n")
            f.write(f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("const JOBS_DATA = [];\n")
            f.write("const JOBS_STATS = { totalJobs: 0, companiesHiring: 0 };\n")
        return

    stats = aggregate_stats(jobs, health)
    save_to_json(jobs, "jobs_raw.json")
    save_to_json(stats, "jobs_stats.json")
    generate_js_snippet(jobs, stats)

    log.info("=" * 60)
    log.info("SUMMARY")
    log.info("=" * 60)
    log.info(f"Total Jobs: {stats['totalJobs']}")
    log.info(f"Companies Hiring: {stats['companiesHiring']}")
    log.info(f"Boards: {stats['boardsOk']} ok · {stats['boardsEmpty']} empty · {stats['boardsError']} unreachable")
    log.info(f"Remote Jobs: {stats['remoteJobs']} ({100 * stats['remoteJobs'] // max(1, len(jobs))}%)")
    log.info("By source: " + ", ".join(f"{k} {v}" for k, v in sorted(stats["bySource"].items(), key=lambda x: -x[1])))
    log.info("Top 15 companies by open positions:")
    for company, count in sorted(stats["byCompany"].items(), key=lambda x: -x[1])[:15]:
        log.info(f"  {company}: {count} jobs")


if __name__ == "__main__":
    main()
