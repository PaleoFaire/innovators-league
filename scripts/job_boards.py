#!/usr/bin/env python3
"""
job_boards.py — one source of truth for company job boards.

The registry lives in data/pulse/job_boards.json, a list of records:

    {"company": "Anduril Industries",      # exactly as data.js spells it
     "platform": "greenhouse",            # see PLATFORMS below
     "slug": "andurilindustries",         # board token (Workday: "tenant.wd5/Site")
     "verified": "2026-10-15",            # last date the board returned jobs
     "jobs_seen": 2527,                   # job count on that date
     "evidence": "careers-page https://www.anduril.com/careers",
     "added": "2026-10-15"}

scripts/fetch_jobs.py reads it to pull postings; scripts/discover_job_boards.py
adds to it after verifying a board really belongs to the company.

Platforms, their id prefixes (jobs.js reads the first two characters of a job
id as the source) and their public, keyless endpoints:

    greenhouse      gh  boards-api.greenhouse.io/v1/boards/{slug}/jobs
    lever           lv  api.lever.co/v0/postings/{slug}?mode=json   (api.eu.lever.co fallback)
    ashby           ab  api.ashbyhq.com/posting-api/job-board/{slug}
    workable        wk  apply.workable.com/api/v1/widget/accounts/{slug}
    rippling        rp  api.rippling.com/platform/api/ats/v1/board/{slug}/jobs
    bamboohr        bh  {slug}.bamboohr.com/careers/list
    smartrecruiters sr  api.smartrecruiters.com/v1/companies/{slug}/postings
    workday         wd  POST {tenant}.wdN.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
    recruitee       rc  {slug}.recruitee.com/api/offers/
    personio        pe  {slug}.jobs.personio.de/xml
    breezy          bz  {slug}.breezy.hr/json
    pinpoint        pp  {slug}.pinpointhq.com/postings.json
    teamtailor      tt  {slug}.teamtailor.com/jobs.rss
    jazzhr          jz  {slug}.applytojob.com/apply/            (HTML list)
    icims           ic  {slug}.icims.com/jobs/search?ss=1&in_iframe=1&pr=N  (HTML list)

Every fetcher returns the same record shape:
    id, company, title, location, department, type, posted (YYYY-MM-DD or ""),
    url, remote, sector, source, and salaryMin / salaryMax / salaryCurrency
    when the platform exposes pay.
"""
import json
import re
import time
import html as _html
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REGISTRY_PATH = DATA / "pulse" / "job_boards.json"
DISCOVERED_PATH = DATA / "pulse" / "job_boards_discovered.json"
STATS_PATH = DATA / "jobs_stats.json"

REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
BACKOFF_BASE = 2

API_HEADERS = {"User-Agent": "InnovatorsLeague-JobsBot/1.0 (+https://innovatorsleague.com)", "Accept": "application/json"}
HTML_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

PLATFORMS = {
    "greenhouse": "gh", "lever": "lv", "ashby": "ab", "workable": "wk", "rippling": "rp",
    "bamboohr": "bh", "smartrecruiters": "sr", "workday": "wd", "recruitee": "rc",
    "personio": "pe", "breezy": "bz", "pinpoint": "pp", "teamtailor": "tt", "jazzhr": "jz",
    "icims": "ic",
}

# Platforms the scanner recognises but nobody fetches yet (no keyless list endpoint,
# or not worth it). They are logged so the coverage report can name them.
UNSUPPORTED_PLATFORMS = ("gem", "dover", "ycombinator", "paylocity", "adp", "ukg", "homerun",
                         "jobvite", "comeet", "polymer", "wellfound", "linkedin", "successfactors",
                         "oracle", "taleo", "dayforce", "paycom", "welcometothejungle", "hibob",
                         "notion", "workstream", "freshteam", "zohorecruit", "trakstar",
                         "applicantpro", "clearcompany", "gusto", "humaans", "join")


# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────

def load_registry(path=REGISTRY_PATH):
    try:
        with open(path, encoding="utf-8") as f:
            recs = json.load(f)
    except (FileNotFoundError, ValueError):
        return []
    return [r for r in recs if r.get("company") and r.get("platform") in PLATFORMS and r.get("slug")]


def save_registry(records, path=REGISTRY_PATH):
    seen = set()
    out = []
    for r in sorted(records, key=lambda r: (r["company"].lower(), r["platform"], r["slug"])):
        key = (r["company"], r["platform"], r["slug"])
        if key in seen:
            continue
        seen.add(key)
        out.append({k: r[k] for k in ("company", "platform", "slug", "verified", "jobs_seen", "evidence", "added") if k in r})
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    return out


def registry_by_company(records=None):
    idx = {}
    for r in (records if records is not None else load_registry()):
        idx.setdefault(r["company"], []).append(r)
    return idx


def load_board_health(path=STATS_PATH):
    """{(platform, slug): {"ok": bool, "jobs": n, "http": code}} from the last fetch."""
    try:
        with open(path, encoding="utf-8") as f:
            stats = json.load(f)
    except (FileNotFoundError, ValueError):
        return {}
    out = {}
    for b in stats.get("boards", []) or []:
        out[(b.get("platform"), b.get("slug"))] = b
    return out


# ─────────────────────────────────────────────────────────────────────────────
# HTTP
# ─────────────────────────────────────────────────────────────────────────────

# Discovery flips this on: blind probes of boards that mostly do not exist get one attempt and a
# short timeout instead of three attempts with backoff (a non-existent *.recruitee.com costs 10 s otherwise).
FAST_PROBES = False


def request(method, url, timeout=REQUEST_TIMEOUT, max_retries=MAX_RETRIES, headers=None, **kw):
    """GET/POST with retries on 429/5xx and network errors. Returns a Response or None."""
    hdrs = dict(API_HEADERS if headers is None else headers)
    if FAST_PROBES:
        max_retries, timeout = 1, min(timeout, 12)
    for attempt in range(max_retries):
        try:
            resp = requests.request(method, url, timeout=timeout, headers=hdrs, allow_redirects=True, **kw)
        except requests.RequestException:
            if attempt < max_retries - 1:
                time.sleep(BACKOFF_BASE * (2 ** attempt))
                continue
            return None
        if resp.status_code == 429:
            wait = BACKOFF_BASE * (2 ** attempt)
            ra = resp.headers.get("Retry-After")
            if ra and ra.isdigit():
                wait = min(int(ra), 60)
            time.sleep(wait)
            continue
        if 500 <= resp.status_code < 600 and attempt < max_retries - 1:
            time.sleep(BACKOFF_BASE * (2 ** attempt))
            continue
        return resp
    return None


def http_get(url, **kw):
    return request("GET", url, **kw)


def http_get_with_retry(url, timeout=REQUEST_TIMEOUT, max_retries=MAX_RETRIES):
    """Back-compat name used by fetch_jobs.py."""
    return request("GET", url, timeout=timeout, max_retries=max_retries)


def _json(resp):
    if resp is None or resp.status_code != 200:
        return None
    try:
        return resp.json()
    except ValueError:
        return None


def plain_text(html_text):
    t = _html.unescape(html_text or "")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _is_remote(location):
    loc = (location or "").lower()
    return "remote" in loc or "anywhere" in loc or "distributed" in loc


def _record(platform, slug, jid, company, title, location, department, jtype, posted, url, remote, sector,
            salary_min=None, salary_max=None, salary_currency=None):
    rec = {
        "id": f"{PLATFORMS[platform]}-{slug}-{jid}",
        "company": company,
        "title": (title or "").strip(),
        "location": (location or "").strip() or "Remote",
        "department": (department or "").strip() or "General",
        "type": (jtype or "").strip() or "Full-time",
        "posted": posted or "",
        "url": url or "",
        "remote": bool(remote),
        "sector": sector,
        "source": platform,
    }
    if salary_min or salary_max:
        rec["salaryMin"] = salary_min
        rec["salaryMax"] = salary_max
        rec["salaryCurrency"] = salary_currency or "USD"
    return rec


# ─────────────────────────────────────────────────────────────────────────────
# Fetchers
# ─────────────────────────────────────────────────────────────────────────────

def fetch_greenhouse(company, slug, sector="tech"):
    data = _json(http_get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?pay_transparency=true"))
    if data is None:
        return None
    jobs = []
    for job in data.get("jobs", []):
        location = (job.get("location") or {}).get("name", "") or "Remote"
        departments = job.get("departments") or []
        department = departments[0].get("name") if departments and departments[0] else "General"
        smin = smax = scur = None
        for pr in job.get("pay_input_ranges") or []:
            mn, mx = pr.get("min_cents") or 0, pr.get("max_cents") or 0
            if mn or mx:
                smin = mn // 100 if mn else None
                smax = mx // 100 if mx else None
                scur = pr.get("currency_type") or "USD"
                break
        jobs.append(_record("greenhouse", slug, job.get("id"), company, job.get("title"), location, department,
                            "Full-time", (job.get("updated_at") or "")[:10], job.get("absolute_url"),
                            _is_remote(location), sector, smin, smax, scur))
    return jobs


def fetch_lever(company, slug, sector="tech"):
    resp = http_get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    if resp is not None and resp.status_code == 404:
        resp = http_get(f"https://api.eu.lever.co/v0/postings/{slug}?mode=json")
    data = _json(resp)
    if data is None or not isinstance(data, list):
        return None if data is None else []
    jobs = []
    for job in data:
        cats = job.get("categories") or {}
        location = cats.get("location") or "Remote"
        if cats.get("allLocations"):
            location = ", ".join(cats["allLocations"][:3])
        created = job.get("createdAt") or 0
        posted = datetime.utcfromtimestamp(created / 1000).strftime("%Y-%m-%d") if created else ""
        smin = smax = scur = None
        sr = job.get("salaryRange") or {}
        if sr.get("min") or sr.get("max"):
            smin, smax, scur = sr.get("min"), sr.get("max"), (sr.get("currency") or "USD").upper()
            iv = (sr.get("interval") or "").lower()   # Lever: per-year-salary, per-month-salary, per-hour-wage …
            factor = 2080 if "hour" in iv else 12 if "month" in iv else 52 if "week" in iv else 1
            smin = int(smin * factor) if smin else None
            smax = int(smax * factor) if smax else None
        jobs.append(_record("lever", slug, job.get("id"), company, job.get("text"), location, cats.get("team"),
                            cats.get("commitment"), posted, job.get("hostedUrl"),
                            _is_remote(location) or job.get("workplaceType") == "remote", sector, smin, smax, scur))
    return jobs


def fetch_ashby(company, slug, sector="tech"):
    data = _json(http_get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"))
    if data is None:
        return None
    jobs = []
    for job in data.get("jobs", []):
        location = job.get("location") or "Remote"
        smin = smax = scur = None
        comp = job.get("compensation") or {}
        for comp_part in comp.get("summaryComponents") or []:
            if comp_part.get("compensationType") == "Salary" and (comp_part.get("minValue") or comp_part.get("maxValue")):
                smin = int(comp_part["minValue"]) if comp_part.get("minValue") else None
                smax = int(comp_part["maxValue"]) if comp_part.get("maxValue") else None
                scur = comp_part.get("currencyCode") or "USD"
                break
        jobs.append(_record("ashby", slug, job.get("id"), company, job.get("title"), location, job.get("department"),
                            job.get("employmentType"), (job.get("publishedAt") or "")[:10], job.get("jobUrl"),
                            job.get("isRemote") or _is_remote(location), sector, smin, smax, scur))
    return jobs


def fetch_workable(company, slug, sector="tech"):
    data = _json(http_get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}"))
    if data is None:
        return None
    jobs = []
    for job in data.get("jobs", []):
        loc = job.get("location") or {}
        location = ", ".join(x for x in (loc.get("city"), loc.get("country")) if x) or "Remote"
        jobs.append(_record("workable", slug, job.get("shortcode"), company, job.get("title"), location,
                            job.get("department"), job.get("employment_type"), (job.get("published_on") or "")[:10],
                            job.get("url") or f"https://apply.workable.com/{slug}/j/{job.get('shortcode')}/",
                            job.get("remote") or _is_remote(location), sector))
    return jobs


def fetch_rippling(company, slug, sector="tech"):
    data = _json(http_get(f"https://api.rippling.com/platform/api/ats/v1/board/{slug}/jobs"))
    if data is None:
        return None
    if not isinstance(data, list):
        return []
    jobs = []
    for job in data:
        loc = (job.get("workLocation") or {}).get("label") or "Remote"
        dept = (job.get("department") or {}).get("label") or "General"
        jobs.append(_record("rippling", slug, job.get("uuid") or job.get("id"), company,
                            job.get("name") or job.get("title"), loc, dept, "Full-time", "",
                            job.get("url") or f"https://ats.rippling.com/{slug}/jobs", _is_remote(loc), sector))
    return jobs


def fetch_bamboohr(company, slug, sector="tech"):
    data = _json(http_get(f"https://{slug}.bamboohr.com/careers/list"))
    if data is None:
        return None
    jobs = []
    for job in data.get("result") or []:
        loc_d = job.get("location") or {}
        loc = ", ".join(x for x in (loc_d.get("city"), loc_d.get("state")) if x) or ("Remote" if job.get("isRemote") else "")
        jobs.append(_record("bamboohr", slug, job.get("id"), company, job.get("jobOpeningName"), loc,
                            job.get("departmentLabel"), job.get("employmentStatusLabel"), (job.get("datePosted") or "")[:10],
                            f"https://{slug}.bamboohr.com/careers/{job.get('id')}", job.get("isRemote") or _is_remote(loc), sector))
    return jobs


def fetch_smartrecruiters(company, slug, sector="tech"):
    jobs, offset, total = [], 0, None
    while True:
        data = _json(http_get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset={offset}"))
        if data is None:
            return None if not jobs else jobs
        content = data.get("content") or []
        total = data.get("totalFound", len(content)) if total is None else total
        for job in content:
            loc = job.get("location") or {}
            location = loc.get("fullLocation") or ", ".join(x for x in (loc.get("city"), loc.get("region"), (loc.get("country") or "").upper()) if x) or "Remote"
            dept = (job.get("department") or {}).get("label") or (job.get("function") or {}).get("label")
            jobs.append(_record("smartrecruiters", slug, job.get("id"), company, job.get("name"), location, dept,
                                (job.get("typeOfEmployment") or {}).get("label"), (job.get("releasedDate") or "")[:10],
                                f"https://jobs.smartrecruiters.com/{slug}/{job.get('id')}",
                                loc.get("remote") or _is_remote(location), sector))
        offset += len(content)
        if not content or offset >= total or offset >= 5000:
            break
    return jobs


_WD_REL = re.compile(r"posted\s+(today|yesterday|(\d+)\+?\s+days?\s+ago|(\d+)\+?\s+hours?\s+ago)", re.I)


def _workday_date(text, today=None):
    today = today or date.today()
    m = _WD_REL.search(text or "")
    if not m:
        return ""
    if "+" in (text or ""):
        return ""
    if m.group(1).lower() == "today" or m.group(3):
        return today.isoformat()
    if m.group(1).lower() == "yesterday":
        return (today - timedelta(days=1)).isoformat()
    return (today - timedelta(days=int(m.group(2)))).isoformat()


def workday_parts(slug):
    """'xenergy.wd5/X-energyUS' -> (tenant, 'wd5', site)."""
    host, _, site = slug.partition("/")
    tenant, _, wd = host.partition(".")
    return tenant, wd or "wd5", site or "External"


def fetch_workday(company, slug, sector="tech"):
    tenant, wd, site = workday_parts(slug)
    base = f"https://{tenant}.{wd}.myworkdayjobs.com"
    api = f"{base}/wday/cxs/{tenant}/{site}/jobs"
    jobs, offset, total = [], 0, None
    today = date.today()
    while True:
        payload = {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""}
        data = _json(request("POST", api, json=payload, headers=dict(API_HEADERS, **{"Content-Type": "application/json"})))
        if data is None:
            return None if not jobs else jobs
        postings = data.get("jobPostings") or []
        total = data.get("total", len(postings)) if total is None else total
        for job in postings:
            path = job.get("externalPath") or ""
            bullets = job.get("bulletFields") or []
            jid = (bullets[0] if bullets else "") or path.rsplit("_", 1)[-1] or path.rsplit("/", 1)[-1]
            jid = re.sub(r"[^A-Za-z0-9_.-]", "", str(jid))
            if not jid or not path:
                continue
            location = job.get("locationsText") or "Remote"
            jobs.append(_record("workday", f"{tenant}", jid, company, job.get("title"), location, "General", "Full-time",
                                _workday_date(job.get("postedOn"), today), f"{base}/{site}{path}", _is_remote(location), sector))
        offset += len(postings)
        if not postings or offset >= total or offset >= 3000:
            break
    return jobs


def recruitee_host(slug):
    """'leydenjar' -> leydenjar.recruitee.com; 'careers.dronamics.com' (a Recruitee site on the company's own domain) stays."""
    return slug if "." in slug else f"{slug}.recruitee.com"


def fetch_recruitee(company, slug, sector="tech"):
    host = recruitee_host(slug)
    data = _json(http_get(f"https://{host}/api/offers/"))
    if data is None:
        return None
    jobs = []
    for job in data.get("offers") or []:
        location = job.get("location") or ", ".join(x for x in (job.get("city"), job.get("country")) if x) or "Remote"
        jobs.append(_record("recruitee", slug, job.get("id"), company, job.get("title"), location, job.get("department"),
                            (job.get("employment_type_code") or "").replace("_", "-").title() or "Full-time",
                            (job.get("published_at") or job.get("created_at") or "")[:10],
                            job.get("careers_url") or f"https://{host}/o/{job.get('slug')}",
                            job.get("remote") or _is_remote(location), sector))
    return jobs


def fetch_personio(company, slug, sector="tech"):
    resp = http_get(f"https://{slug}.jobs.personio.de/xml", headers=HTML_HEADERS)
    host = f"{slug}.jobs.personio.de"
    if resp is None or resp.status_code != 200:
        resp = http_get(f"https://{slug}.jobs.personio.com/xml", headers=HTML_HEADERS)
        host = f"{slug}.jobs.personio.com"
    if resp is None or resp.status_code != 200:
        return None
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError:
        return None
    jobs = []
    for pos in root.iter("position"):
        g = lambda tag: (pos.findtext(tag) or "").strip()  # noqa: E731
        offices = [g("office")] + [(o.text or "").strip() for o in pos.findall("additionalOffices/office")]
        location = ", ".join(o for o in offices if o) or "Remote"
        jtype = g("schedule") or g("employmentType")
        jobs.append(_record("personio", slug, g("id"), company, g("name"), location, g("department"),
                            jtype.replace("-", " ").title() if jtype else "Full-time", g("createdAt")[:10],
                            f"https://{host}/job/{g('id')}", _is_remote(location), sector))
    return jobs


def fetch_breezy(company, slug, sector="tech"):
    data = _json(http_get(f"https://{slug}.breezy.hr/json"))
    if data is None:
        return None
    if not isinstance(data, list):
        return []
    jobs = []
    for job in data:
        loc = job.get("location") or {}
        location = loc.get("name") or ", ".join(x for x in (loc.get("city"), (loc.get("state") or {}).get("id") if isinstance(loc.get("state"), dict) else None) if x) or "Remote"
        dept = job.get("department") if isinstance(job.get("department"), str) else (job.get("department") or {}).get("name") if job.get("department") else None
        jobs.append(_record("breezy", slug, job.get("id"), company, job.get("name"), location, dept,
                            (job.get("type") or {}).get("name"), (job.get("published_date") or "")[:10],
                            job.get("url") or f"https://{slug}.breezy.hr/p/{job.get('friendly_id')}",
                            loc.get("is_remote") or _is_remote(location), sector))
    return jobs


def fetch_pinpoint(company, slug, sector="tech"):
    data = _json(http_get(f"https://{slug}.pinpointhq.com/postings.json"))
    if data is None:
        return None
    rows = data.get("data") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        return []
    jobs = []
    for job in rows:
        loc = job.get("location") or {}
        location = (loc.get("name") if isinstance(loc, dict) else loc) or "Remote"
        dept = job.get("department") or {}
        dept = dept.get("name") if isinstance(dept, dict) else dept
        jobs.append(_record("pinpoint", slug, job.get("id"), company, job.get("title"), location, dept,
                            (job.get("employment_type") or "").replace("_", "-").title(),
                            (job.get("created_at") or job.get("published_at") or "")[:10],
                            job.get("url") or f"https://{slug}.pinpointhq.com/postings/{job.get('id')}",
                            (job.get("workplace_type") == "remote") or _is_remote(location), sector))
    return jobs


def _rss_date(s):
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime((s or "").strip()[:31], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return (s or "")[:10] if re.match(r"\d{4}-\d{2}-\d{2}", s or "") else ""


def fetch_teamtailor(company, slug, sector="tech"):
    host = slug if "." in slug else f"{slug}.teamtailor.com"
    resp = http_get(f"https://{host}/jobs.rss", headers=HTML_HEADERS)
    if resp is None or resp.status_code != 200:
        return None
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError:
        return None
    jobs = []
    for item in root.iter("item"):
        def g(tag):
            el = item.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""
        link = g("link")
        m = re.search(r"/jobs/(\d+)", link)
        jid = m.group(1) if m else (re.sub(r"[^A-Za-z0-9]", "", g("guid"))[:32] or str(abs(hash(link))))
        locs, dept = [], ""
        for loc in item.iter():
            if loc.tag.rsplit("}", 1)[-1].lower() == "location":
                city = next((c.text.strip() for c in loc if c.tag.rsplit("}", 1)[-1].lower() == "city" and c.text), "")
                country = next((c.text.strip() for c in loc if c.tag.rsplit("}", 1)[-1].lower() == "country" and c.text), "")
                nm = next((c.text.strip() for c in loc if c.tag.rsplit("}", 1)[-1].lower() == "name" and c.text), "")
                locs.append(", ".join(x for x in (city or nm, country) if x))
        for el in item:
            if el.tag.rsplit("}", 1)[-1].lower() == "department" and el.text:
                dept = el.text.strip()
        location = "; ".join(l for l in dict.fromkeys(locs) if l)
        remote = (g("remoteStatus") or "").lower() in ("fully", "fully_remote", "remote") or _is_remote(location)
        jobs.append(_record("teamtailor", slug, jid, company, g("title"), location or "Remote", dept, "Full-time",
                            _rss_date(g("pubDate")), link, remote, sector))
    return jobs


_JZ_ITEM = re.compile(r'<a[^>]+href="(https?://[a-z0-9-]+\.applytojob\.com/apply/([A-Za-z0-9]+)/[^"?]+)"[^>]*>(.*?)</a>(.*?)(?=<a[^>]+href="https?://[a-z0-9-]+\.applytojob\.com/apply/|$)', re.S | re.I)


def fetch_jazzhr(company, slug, sector="tech"):
    resp = http_get(f"https://{slug}.applytojob.com/apply/", headers=HTML_HEADERS)
    if resp is None or resp.status_code != 200:
        return None
    jobs, seen = [], set()
    for url, jid, title_html, tail in _JZ_ITEM.findall(resp.text):
        if jid in seen or jid.lower() in ("jobs", "sign", "login"):
            continue
        seen.add(jid)
        title = plain_text(title_html)
        if not title:
            continue
        loc = ""
        m = re.search(r'<li[^>]*>\s*([^<]{3,80}?)\s*</li>', tail)
        if m:
            loc = plain_text(m.group(1))
        jobs.append(_record("jazzhr", slug, jid, company, title, loc or "Remote", "General", "Full-time", "",
                            url, _is_remote(loc), sector))
    return jobs


_IC_CARD = re.compile(r'<li class="iCIMS_JobCardItem">(.*?)</li>', re.S)
_IC_LINK = re.compile(r'href="(https?://[a-z0-9-]+\.icims\.com/jobs/(\d+)/([^/"]+)/job)[^"]*"', re.I)
_IC_TITLE = re.compile(r"<h3[^>]*>(.*?)</h3>", re.S)
_IC_LOC = re.compile(r"Job Locations</span>\s*<span[^>]*>\s*(.*?)\s*</span>", re.S)
_IC_CAT = re.compile(r"<dt[^>]*>\s*Category\s*</dt>\s*<dd[^>]*>\s*<span[^>]*>\s*(.*?)\s*</span>", re.S)


def fetch_icims(company, slug, sector="tech"):
    jobs, seen = [], set()
    for page in range(0, 40):
        resp = http_get(f"https://{slug}.icims.com/jobs/search?ss=1&in_iframe=1&pr={page}", headers=HTML_HEADERS)
        if resp is None or resp.status_code != 200:
            return None if not jobs and page == 0 else jobs
        new = 0
        for card in _IC_CARD.findall(resp.text):
            lm = _IC_LINK.search(card)
            if not lm:
                continue
            url, jid = lm.group(1), lm.group(2)
            if jid in seen:
                continue
            seen.add(jid)
            new += 1
            tm, lo, ca = _IC_TITLE.search(card), _IC_LOC.search(card), _IC_CAT.search(card)
            title = plain_text(tm.group(1)) if tm else ""
            location = plain_text(lo.group(1)).replace(" | ", ", ") if lo else ""
            location = re.sub(r"\b(?:US|USA)-([A-Z]{2})-([^,;|]+)", r"\2, \1", location) if location else location
            jobs.append(_record("icims", slug, jid, company, title, location or "Remote", plain_text(ca.group(1)) if ca else "General",
                                "Full-time", "", url, _is_remote(location), sector))
        if new == 0:
            break
        time.sleep(0.2)
    return jobs


FETCHERS = {
    "greenhouse": fetch_greenhouse, "lever": fetch_lever, "ashby": fetch_ashby, "workable": fetch_workable,
    "rippling": fetch_rippling, "bamboohr": fetch_bamboohr, "smartrecruiters": fetch_smartrecruiters,
    "workday": fetch_workday, "recruitee": fetch_recruitee, "personio": fetch_personio, "breezy": fetch_breezy,
    "pinpoint": fetch_pinpoint, "teamtailor": fetch_teamtailor, "jazzhr": fetch_jazzhr, "icims": fetch_icims,
}


def fetch_board(platform, company, slug, sector="tech"):
    """List of job records, [] for a live-but-empty board, None when the board is unreachable or gone."""
    fn = FETCHERS.get(platform)
    if fn is None:
        return None
    return fn(company, slug, sector)


# ─────────────────────────────────────────────────────────────────────────────
# Probing (does this board exist, and whose is it?)
# ─────────────────────────────────────────────────────────────────────────────

def _board_org(platform, slug, jobs):
    """Best-effort organisation name shown by the board itself."""
    try:
        if platform == "greenhouse":
            d = _json(http_get(f"https://boards-api.greenhouse.io/v1/boards/{slug}"))
            return (d or {}).get("name", "") or ""
        if platform == "workable":
            d = _json(http_get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}"))
            return (d or {}).get("name", "") or ""
        if platform == "smartrecruiters":
            d = _json(http_get(f"https://api.smartrecruiters.com/v1/companies/{slug}"))
            return (d or {}).get("name", "") or ""
        if platform == "breezy":
            d = _json(http_get(f"https://{slug}.breezy.hr/json"))
            if isinstance(d, list) and d:
                return ((d[0].get("company") or {}).get("name") or "")
        if platform == "recruitee":
            d = _json(http_get(f"https://{recruitee_host(slug)}/api/offers/"))
            offers = (d or {}).get("offers") or []
            if offers:
                return offers[0].get("company_name") or ""
        if platform in ("ashby", "rippling", "bamboohr", "icims", "jazzhr", "teamtailor", "pinpoint", "personio", "lever"):
            page = {
                "ashby": f"https://jobs.ashbyhq.com/{slug}",
                "rippling": f"https://ats.rippling.com/{slug}/jobs",
                "bamboohr": f"https://{slug}.bamboohr.com/careers",
                "icims": f"https://{slug}.icims.com/jobs/search?ss=1",
                "jazzhr": f"https://{slug}.applytojob.com/apply/",
                "teamtailor": f"https://{slug if '.' in slug else slug + '.teamtailor.com'}/jobs",
                "pinpoint": f"https://{slug}.pinpointhq.com/",
                "personio": f"https://{slug}.jobs.personio.de/",
                "lever": f"https://jobs.lever.co/{slug}",
            }[platform]
            r = http_get(page, headers=HTML_HEADERS, max_retries=1)
            if r is not None and r.status_code == 200:
                m = re.search(r"<title[^>]*>(.*?)</title>", r.text, re.S | re.I)
                og = re.search(r'property="og:site_name"\s+content="([^"]+)"', r.text, re.I)
                title = plain_text(m.group(1)) if m else ""
                return (og.group(1) if og else "") or title
    except Exception:  # noqa: BLE001 — probing is best effort
        pass
    return ""


def probe_board(platform, slug, want_org=True):
    """
    {"ok": bool, "exists": bool, "n": int, "org": str, "urls": [...], "titles": [...], "locations": [...], "text": str}
    exists = the board responded (even with 0 jobs); ok = exists and ≥1 job.
    """
    out = {"ok": False, "exists": False, "n": 0, "org": "", "urls": [], "titles": [], "locations": [], "text": ""}
    try:
        jobs = fetch_board(platform, "?", slug)
    except Exception:  # noqa: BLE001
        jobs = None
    if jobs is None:
        return out
    if platform == "smartrecruiters" and not jobs:
        return out  # the postings API answers 200 with totalFound 0 for unknown companies
    out["exists"] = True
    out["n"] = len(jobs)
    out["ok"] = len(jobs) > 0
    out["urls"] = [j["url"] for j in jobs[:5] if j.get("url")]
    out["titles"] = [j["title"] for j in jobs[:8]]
    out["locations"] = [j["location"] for j in jobs[:25] if j.get("location")]
    if want_org:
        out["org"] = _board_org(platform, slug, jobs)
    out["text"] = _first_posting_text(platform, slug, jobs)
    return out


def _first_posting_text(platform, slug, jobs):
    """Plain text of the first posting's description — the board's own words about the company."""
    try:
        if platform == "greenhouse" and jobs:
            jid = jobs[0]["id"].rsplit("-", 1)[-1]
            d = _json(http_get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{jid}"))
            return plain_text((d or {}).get("content", ""))[:4000]
        if platform == "lever" and jobs:
            resp = http_get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
            d = _json(resp)
            if d is None:
                d = _json(http_get(f"https://api.eu.lever.co/v0/postings/{slug}?mode=json"))
            if isinstance(d, list) and d:
                j = d[0]
                parts = [j.get("descriptionPlain") or "", j.get("additionalPlain") or ""]
                for lst in j.get("lists") or []:
                    parts.append(plain_text(lst.get("content", "")))
                return " ".join(parts)[:4000]
        if platform == "ashby" and jobs:
            d = _json(http_get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}"))
            js = (d or {}).get("jobs") or []
            if js:
                return (js[0].get("descriptionPlain") or plain_text(js[0].get("descriptionHtml", "")))[:4000]
        if platform == "workable" and jobs:
            d = _json(http_get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}"))
            return plain_text((d or {}).get("description", ""))[:4000]
        if platform == "smartrecruiters" and jobs:
            jid = jobs[0]["id"].rsplit("-", 1)[-1]
            d = _json(http_get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings/{jid}"))
            jd = (d or {}).get("jobAd", {}).get("sections", {})
            return plain_text(" ".join((jd.get(k) or {}).get("text", "") for k in ("companyDescription", "jobDescription")))[:4000]
        if platform == "recruitee" and jobs:
            d = _json(http_get(f"https://{recruitee_host(slug)}/api/offers/"))
            offers = (d or {}).get("offers") or []
            if offers:
                return plain_text(offers[0].get("description", ""))[:4000]
        if platform == "breezy" and jobs:
            jid = jobs[0]["id"].rsplit("-", 1)[-1]
            d = _json(http_get(f"https://{slug}.breezy.hr/json/{jid}"))
            return plain_text((d or {}).get("description", ""))[:4000]
        if platform == "teamtailor" and jobs:
            host = slug if "." in slug else f"{slug}.teamtailor.com"
            r = http_get(f"https://{host}/jobs.rss", headers=HTML_HEADERS)
            if r is not None and r.status_code == 200:
                m = re.search(r"<description>(.*?)</description>", r.text, re.S)
                return plain_text(_html.unescape(m.group(1)))[:4000] if m else ""
        if platform == "rippling" and jobs:
            r = http_get(jobs[0]["url"], headers=HTML_HEADERS, max_retries=1)
            if r is not None and r.status_code == 200:
                return plain_text(r.text)[:4000]
    except Exception:  # noqa: BLE001
        pass
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Names, domains and slugs
# ─────────────────────────────────────────────────────────────────────────────

GENERIC_WORDS = {
    "inc", "corp", "corporation", "co", "company", "llc", "ltd", "plc", "gmbh", "ag", "sa", "the", "and", "of",
    "labs", "lab", "ai", "technologies", "technology", "tech", "systems", "system", "energy", "space", "aerospace",
    "robotics", "robotic", "industries", "industrial", "bio", "biosciences", "bioscience", "therapeutics", "group",
    "holdings", "international", "global", "solutions", "networks", "network", "dynamics", "motors", "power",
    "materials", "quantum", "computing", "aviation", "aero", "automation", "manufacturing", "medical", "health",
    "sciences", "science", "digital", "software", "data", "capital", "ventures", "studio", "studios", "partners",
    "nuclear", "fusion", "electric", "semiconductor", "semiconductors", "photonics", "mobility", "defense", "security",
}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def domain_base(website):
    if not website:
        return ""
    host = urlparse(website if website.startswith("http") else "https://" + website).netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in ("co", "com", "org", "ac") and len(parts[-1]) == 2:
        parts = parts[:-2]  # foo.co.uk
    else:
        parts = parts[:-1]
    return ".".join(p for p in parts if p not in ("www", "web", "home")).split(".")[-1] if parts else ""


def domain_host(website):
    if not website:
        return ""
    host = urlparse(website if website.startswith("http") else "https://" + website).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def name_words(name):
    words = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower().replace("&", " and ")).split()
    return [w for w in words if w]


def distinctive_words(name):
    return [w for w in name_words(name) if len(w) >= 4 and w not in GENERIC_WORDS and not w.isdigit()]


_SLUG_SUFFIXES = ("inc", "co", "hq", "labs", "ai", "tech", "technologies", "energy", "space", "aero", "systems",
                  "robotics", "industries", "bio", "io", "app", "us", "global", "group")


def slugs_from_domain(website):
    base = domain_base(website)
    if not base:
        return []
    out = [base]
    for suf in _SLUG_SUFFIXES:
        if base.endswith(suf) and len(base) > len(suf) + 2:
            out.append(base[: -len(suf)])
    return [s for s in dict.fromkeys(out) if len(s) >= 3]


def slugs_from_name(name):
    words = name_words(name)
    if not words:
        return []
    out = ["".join(words), "-".join(words)]
    camel = "".join(w.capitalize() for w in words)
    if camel.lower() != camel:
        out.append(camel)
    core = [w for w in words if w not in ("inc", "corp", "co", "the", "llc", "ltd", "plc")]
    if core != words and core:
        out.extend(["".join(core), "-".join(core)])
    if len(core) > 1 and core[-1] in GENERIC_WORDS:
        out.extend(["".join(core[:-1]), "-".join(core[:-1])])
    return [s for s in dict.fromkeys(out) if len(s) >= 3]


# ─────────────────────────────────────────────────────────────────────────────
# Careers-page scanner
# ─────────────────────────────────────────────────────────────────────────────

JUNK_SLUGS = {
    "www", "app", "api", "jobs", "job", "careers", "career", "embed", "job_board", "en", "en-gb", "en-us", "en-ca",
    "de", "fr", "es", "it", "nl", "login", "signup", "sign-up", "help", "support", "resources", "blog", "cdn",
    "static", "assets", "images", "img", "js", "css", "v1", "v0", "boards", "board", "apply", "search", "o", "p",
    "null", "undefined", "company", "companies", "posting", "postings", "feed", "rss", "xml", "json", "widget",
    "account", "accounts", "privacy", "terms", "about", "home", "index", "info", "portal", "external", "internal",
}

_LOCALE = r"(?:[a-z]{2}(?:-[a-zA-Z]{2})?/)?"

# (platform, compiled regex). Group 1 is always the board slug.
BOARD_PATTERNS = [
    ("greenhouse", re.compile(r"boards(?:-api)?\.greenhouse\.io/v1/boards/([A-Za-z0-9_-]+)", re.I)),
    ("greenhouse", re.compile(r"boards\.greenhouse\.io/embed/job_board(?:/js)?\?(?:[^\"'\s<>]*?&(?:amp;)?)?for=([A-Za-z0-9_-]+)", re.I)),
    ("greenhouse", re.compile(r"job-boards(?:\.eu)?\.greenhouse\.io/([A-Za-z0-9_-]+)", re.I)),
    ("greenhouse", re.compile(r"boards(?:\.eu)?\.greenhouse\.io/(?!embed/)([A-Za-z0-9_-]+)", re.I)),
    ("greenhouse", re.compile(r"api\.greenhouse\.io/v1/boards/([A-Za-z0-9_-]+)", re.I)),
    ("lever", re.compile(r"jobs(?:\.eu)?\.lever\.co/([A-Za-z0-9_-]+)", re.I)),
    ("lever", re.compile(r"api(?:\.eu)?\.lever\.co/v0/postings/([A-Za-z0-9_-]+)", re.I)),
    ("ashby", re.compile(r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)", re.I)),
    ("ashby", re.compile(r"api\.ashbyhq\.com/posting-api/job-board/([A-Za-z0-9_.%-]+)", re.I)),
    ("workable", re.compile(r"apply\.workable\.com/(?:api/v1/widget/accounts/)?([A-Za-z0-9_-]+)", re.I)),
    ("workable", re.compile(r"(?<![a-z0-9.-])((?!apply|www|help|resources|careers|jobs|app|api)[a-z0-9-]+)\.workable\.com", re.I)),
    ("smartrecruiters", re.compile(r"(?:jobs|careers)\.smartrecruiters\.com/([A-Za-z0-9_-]+)", re.I)),
    ("smartrecruiters", re.compile(r"api\.smartrecruiters\.com/v1/companies/([A-Za-z0-9_-]+)", re.I)),
    ("workday", re.compile(r"https?://([a-z0-9-]+\.wd\d+)\.myworkdayjobs\.com/" + _LOCALE + r"(?!job/|wday/)([A-Za-z0-9_-]+)", re.I)),
    ("icims", re.compile(r"https?://([a-z0-9-]+)\.icims\.com", re.I)),
    ("rippling", re.compile(r"ats\.rippling\.com/" + _LOCALE + r"([A-Za-z0-9_-]+)", re.I)),
    ("rippling", re.compile(r"api\.rippling\.com/platform/api/ats/v1/board/([A-Za-z0-9_-]+)", re.I)),
    ("bamboohr", re.compile(r"https?://([a-z0-9-]+)\.bamboohr\.com", re.I)),
    ("recruitee", re.compile(r"https?://((?!www|app|api|cdn|assets|careers-analytics|d10zminp1cyta8)[a-z0-9-]+)\.recruitee\.com", re.I)),
    ("personio", re.compile(r"https?://([a-z0-9-]+)\.jobs\.personio\.(?:de|com)", re.I)),
    ("breezy", re.compile(r"https?://((?!www|app|api|cdn|assets)[a-z0-9-]+)\.breezy\.hr", re.I)),
    ("pinpoint", re.compile(r"https?://((?!www|app|api|cdn|assets)[a-z0-9-]+)\.pinpointhq\.com", re.I)),
    ("teamtailor", re.compile(r"https?://((?!www|app|api|cdn|assets|static|blog|support|help)[a-z0-9-]+)\.teamtailor\.com", re.I)),
    ("jazzhr", re.compile(r"https?://([a-z0-9-]+)\.applytojob\.com", re.I)),
    # unsupported, logged only
    ("gem", re.compile(r"jobs\.gem\.com/([A-Za-z0-9_-]+)", re.I)),
    ("dover", re.compile(r"app\.dover\.com/(?:jobs|apply)/([A-Za-z0-9_-]+)", re.I)),
    ("ycombinator", re.compile(r"workatastartup\.com/companies/([A-Za-z0-9_-]+)", re.I)),
    ("paylocity", re.compile(r"recruiting\.paylocity\.com/recruiting/jobs/(?:All|List)/([a-f0-9-]+)", re.I)),
    ("adp", re.compile(r"workforcenow\.adp\.com/[^\"'\s<>]*?cid=([a-f0-9-]+)", re.I)),
    ("ukg", re.compile(r"recruiting2?\.ultipro\.com/([A-Za-z0-9_]+)", re.I)),
    ("homerun", re.compile(r"https?://([a-z0-9-]+)\.homerun\.co", re.I)),
    ("jobvite", re.compile(r"jobs\.jobvite\.com/([A-Za-z0-9_-]+)", re.I)),
    ("comeet", re.compile(r"comeet\.com/jobs/([A-Za-z0-9_-]+)", re.I)),
    ("polymer", re.compile(r"jobs\.polymer\.co/([A-Za-z0-9_-]+)", re.I)),
    ("wellfound", re.compile(r"wellfound\.com/company/([A-Za-z0-9_-]+)", re.I)),
    ("linkedin", re.compile(r"linkedin\.com/company/([A-Za-z0-9_-]+)/jobs", re.I)),
    ("successfactors", re.compile(r"https?://([a-z0-9-]+)\.successfactors\.(?:com|eu)", re.I)),
    ("oracle", re.compile(r"https?://([a-z0-9-]+)\.(?:fa\.[a-z0-9-]+\.oraclecloud|taleo)\.(?:com|net)", re.I)),
    ("dayforce", re.compile(r"https?://([a-z0-9-]+)\.dayforcehcm\.com", re.I)),
    ("paycom", re.compile(r"paycomonline\.net/v4/ats/web\.php/jobs[^\"'\s<>]*?clientkey=([A-Za-z0-9]+)", re.I)),
    ("welcometothejungle", re.compile(r"welcometothejungle\.com/[a-z]{2}/companies/([A-Za-z0-9_-]+)", re.I)),
    ("hibob", re.compile(r"https?://([a-z0-9-]+)\.hibob\.com", re.I)),
    ("notion", re.compile(r"https?://([a-z0-9-]+)\.notion\.site/[^\"'\s<>]*(?:career|job|hiring|role)", re.I)),
    ("workstream", re.compile(r"workstream\.us/[a-z/]*?([A-Za-z0-9_-]{8,})", re.I)),
    ("freshteam", re.compile(r"https?://([a-z0-9-]+)\.freshteam\.com", re.I)),
    ("zohorecruit", re.compile(r"https?://([a-z0-9-]+)\.zohorecruit\.com", re.I)),
    ("join", re.compile(r"join\.com/companies/([A-Za-z0-9_-]+)", re.I)),
]

CAREERS_PATHS = ["/careers", "/careers/", "/jobs", "/join", "/join-us", "/company/careers", "/about/careers",
                 "/work-with-us", "/open-positions", "/en/careers", "/team", "/hiring", "/about#careers"]
_ANCHOR = re.compile(r"<a\b[^>]*?href\s*=\s*[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
_CAREER_TEXT = re.compile(r"\b(career|careers|jobs?|join (?:us|the team|our team)|we.?re hiring|hiring|open (?:roles|positions)|positions|work (?:with|for) us|opportunities|vacancies|join)\b", re.I)
_CAREER_HREF = re.compile(r"(career|jobs?|join|hiring|work-with-us|positions|vacanc|opportunit|openings|talent)", re.I)
_JSONLD_JOBPOSTING = re.compile(r"\"@type\"\s*:\s*\"JobPosting\"", re.I)
_URL_IN_TEXT = re.compile(r"https?://[^\s\"'<>()]+", re.I)


def _get_html(url, timeout=12):
    try:
        r = requests.get(url, headers=HTML_HEADERS, timeout=(6, 8) if FAST_PROBES else timeout, allow_redirects=True, stream=True)
        body = b""
        for chunk in r.iter_content(65536):
            body += chunk
            if len(body) > 3_000_000:   # a careers page is not 3 MB; stop reading
                break
        r._content = body
    except requests.RequestException:
        return None, None, None
    ctype = r.headers.get("content-type", "")
    final = re.sub(r"^(https://[^/:]+):443(/|$)", r"\1\2", r.url)
    final = re.sub(r"^(http://[^/:]+):80(/|$)", r"\1\2", final)
    if r.status_code != 200 or ("html" not in ctype and "xml" not in ctype and ctype):
        return None, final, r.status_code
    return r.text, final, r.status_code


def _clean_slug(platform, slug):
    slug = (slug or "").strip().strip("/").rstrip(".")
    if platform == "ashby":
        slug = requests.utils.unquote(slug)
    if platform == "workday":
        return slug  # 'tenant.wdN/site' assembled by the caller
    if not slug or slug.lower() in JUNK_SLUGS or len(slug) < 2:
        return ""
    if platform in ("rippling",) and re.fullmatch(r"[a-z]{2}(-[a-zA-Z]{2})?", slug):
        return ""
    return slug


def extract_boards(html_text, page_url=""):
    """[(platform, slug, how)] found in one page's HTML: links, script embeds, iframes, JSON-LD job URLs."""
    found = []
    text = _html.unescape(html_text or "")
    for platform, rx in BOARD_PATTERNS:
        for m in rx.finditer(text):
            if platform == "workday":
                tenant_host, site = m.group(1).lower(), m.group(2)
                if site.lower() in JUNK_SLUGS or re.fullmatch(r"[a-z]{2}(?:-[a-zA-Z]{2})?", site):
                    site = ""
                slug = f"{tenant_host}/{site}" if site else tenant_host
            else:
                slug = _clean_slug(platform, m.group(1))
            if not slug:
                continue
            ctx = text[max(0, m.start() - 160): m.start()].lower()
            how = "embed" if ("<script" in ctx or "<iframe" in ctx or ".js" in ctx[-40:] or "src=" in ctx[-60:]) else "link"
            if platform in UNSUPPORTED_PLATFORMS:
                how = "unsupported"
            found.append((platform, slug, how))
    if _JSONLD_JOBPOSTING.search(text):
        found.append(("jsonld", "JobPosting", "jsonld"))
    # dedupe, keeping the first 'how'
    out, seen = [], set()
    for f in found:
        if (f[0], f[1].lower()) in seen:
            continue
        seen.add((f[0], f[1].lower()))
        out.append(f)
    return out


def careers_links(html_text, base_url):
    """Nav links that look like a careers page, best first."""
    scored = []
    for href, inner in _ANCHOR.findall(html_text or ""):
        label = plain_text(inner)[:80]
        s = 0
        if _CAREER_TEXT.search(label):
            s += 2
        if _CAREER_HREF.search(href):
            s += 1
        if not s:
            continue
        url = urljoin(base_url, href.strip())
        if url.startswith("mailto:") or url.startswith("tel:") or url.startswith("javascript:"):
            continue
        scored.append((-s, url))
    out = []
    for _, url in sorted(scored):
        if url not in out:
            out.append(url)
    return out


def _scan_page(url, h, info):
    """Record what one fetched page reveals: boards (links/embeds), JSON-LD, unsupported ATS, Recruitee-hosted sites."""
    info["pages"].append(url)
    host = urlparse(url).netloc.lower()
    if host.endswith(".recruitee.com") and host.split(".")[0] not in ("www", "app", "api", "careers-analytics"):
        info["boards"].append(("recruitee", host.split(".")[0], "embed", url))
    elif host and not host.endswith("recruitee.com") and re.search(r"careers-analytics\.recruitee\.com|window\.Recruitee|data-recruitee|recruitee\.com/embed", h or ""):
        info["boards"].append(("recruitee", host, "embed", url))   # a Recruitee careers site on the company's own domain
    for platform, slug, how in extract_boards(h, url):
        if platform == "jsonld":
            info["jsonld"] = True
        elif how == "unsupported":
            info["unsupported"].append((platform, slug, url))
        else:
            info["boards"].append((platform, slug, how, url))


def scan_company_site(website, max_pages=7, pause=0.1):
    """
    Walk the company's site looking for a job board.
    Returns {"reachable": bool, "pages": [urls scanned], "careers_pages": [urls],
             "boards": [(platform, slug, how, page_url)], "jsonld": bool,
             "unsupported": [(platform, slug, page_url)], "external_careers": [urls]}
    """
    info = {"reachable": False, "pages": [], "careers_pages": [], "boards": [], "jsonld": False,
            "unsupported": [], "external_careers": []}
    if not website:
        return info
    base = website if website.startswith("http") else "https://" + website
    base = base.rstrip("/")
    html_text, final, status = _get_html(base)
    if html_text is None and base.startswith("https://"):
        html_text, final, status = _get_html("http://" + base[8:])
    if html_text is None:
        info["status"] = status
        return info
    info["reachable"] = True
    origin = f"{urlparse(final).scheme}://{urlparse(final).netloc}"
    site_host = urlparse(final).netloc.lower().replace("www.", "")
    queue = [(final, html_text)]
    seen_urls = {final.rstrip("/"), base}
    # 1. nav links from the homepage
    nav = careers_links(html_text, final)
    for u in nav[:5]:
        host = urlparse(u).netloc.lower().replace("www.", "")
        if host and host != site_host and not host.endswith("." + site_host):
            info["external_careers"].append(u)
            # an ATS host in the link itself is caught by the regexes on the homepage
            if re.search(r"greenhouse|lever|ashby|workable|smartrecruiters|workday|icims|rippling|bamboohr|recruitee|personio|breezy|pinpoint|teamtailor|applytojob", host):
                continue
            # an off-site careers page (e.g. careers.company.com or a Notion page): read it too
        if u.rstrip("/") in seen_urls:
            continue
        seen_urls.add(u.rstrip("/"))
        if len(queue) >= max_pages:
            break
        time.sleep(pause)
        h, f, _ = _get_html(u)
        if h:
            queue.append((f or u, h))
            info["careers_pages"].append(f or u)
    # 2. conventional paths when nav gave nothing
    if len(info["careers_pages"]) == 0:
        for path in CAREERS_PATHS:
            u = origin + path
            if u.rstrip("/") in seen_urls or len(queue) >= max_pages:
                continue
            seen_urls.add(u.rstrip("/"))
            time.sleep(pause)
            h, f, _ = _get_html(u)
            if h and (f or u).rstrip("/") not in {q[0].rstrip("/") for q in queue}:
                queue.append((f or u, h))
                info["careers_pages"].append(f or u)
                if len(info["careers_pages"]) >= 2:
                    break
    # 3. scan every page we collected
    for url, h in queue:
        _scan_page(url, h, info)
    # 4. a careers page that is itself a client-side app: follow one level of same-site links named like a board
    if not info["boards"] and info["careers_pages"]:
        for url, h in queue[1:]:
            for link in careers_links(h, url)[:3]:
                lh = urlparse(link).netloc.lower().replace("www.", "")
                if link.rstrip("/") in seen_urls or len(info["pages"]) >= max_pages + 2:
                    continue
                if lh != site_host and not lh.endswith("." + site_host):
                    for platform, slug, how in extract_boards(link, url):
                        if platform != "jsonld" and how != "unsupported":
                            info["boards"].append((platform, slug, "link", url))
                    continue
                seen_urls.add(link.rstrip("/"))
                time.sleep(pause)
                h2, f2, _ = _get_html(link)
                if not h2:
                    continue
                _scan_page(f2 or link, h2, info)
            if info["boards"]:
                break
    # dedupe boards
    out, seen = [], set()
    for b in info["boards"]:
        k = (b[0], b[1].lower())
        if k not in seen:
            seen.add(k)
            out.append(b)
    info["boards"] = out
    return info


# ─────────────────────────────────────────────────────────────────────────────
# Verification — does this board belong to this company?
# ─────────────────────────────────────────────────────────────────────────────

_US_STATES = {"al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id","il","in","ia","ks","ky","la","me","md","ma","mi","mn","ms","mo","mt","ne","nv","nh","nj","nm","ny","nc","nd","oh","ok","or","pa","ri","sc","sd","tn","tx","ut","vt","va","wa","wv","wi","wy","dc"}


def location_corroborates(hq, country, locations):
    """
    True when the board's postings sit where the company is — same HQ city, or (coarser) the same
    country: for a US company any posting in a US state, US metro or marked US; for others a posting
    naming the country or the HQ city. False when the board lists places and none agree. None when
    there is nothing to compare (no HQ, or only remote postings).
    """
    locs = [l.lower() for l in (locations or []) if l and not re.fullmatch(r"\s*(remote|anywhere|global|worldwide|other/remote|hybrid)\s*", l, re.I)]
    if not locs or not (hq or country):
        return None
    blob = " | ".join(locs)
    cty = (country or "").lower().strip()
    hq_l = (hq or "").lower()
    # HQ city / region tokens
    for part in re.split(r"[,/;·|]+", hq_l):
        part = part.strip()
        if len(part) >= 4 and part not in ("united states", "usa", "remote", "united kingdom") and part in blob:
            return True
    is_us = cty in ("united states", "usa", "us", "united states of america") or bool(re.search(r",\s*[a-z]{2}$", hq_l) and hq_l.rsplit(",", 1)[-1].strip() in _US_STATES)
    if is_us:
        if re.search(r"\b(united states|usa|u\.s\.|us-|remote - us|remote, us|, us\b|\bus remote)", blob):
            return True
        if re.search(r"\b(" + "|".join(_US_STATES_FULL) + r")\b", blob):
            return True
        if re.search(r"\b(" + "|".join(sorted(_US_METROS)) + r")\b", blob):
            return True
        for st in _US_STATES:
            if re.search(r"(?:,|\s|-)" + st.upper() + r"\b", " | ".join(l for l in (locations or []) if l)):
                return True
        return False
    if cty:
        aliases = {"united kingdom": ("united kingdom", "uk", "england", "scotland", "wales", "london", "cambridge", "oxford", "bristol", "manchester"),
                   "germany": ("germany", "deutschland", "berlin", "munich", "münchen", "hamburg", "frankfurt", "stuttgart", "aachen", "köln", "cologne"),
                   "france": ("france", "paris", "toulouse", "lyon", "grenoble", "bordeaux"),
                   "canada": ("canada", "toronto", "vancouver", "montreal", "montréal", "ottawa", "calgary", "waterloo"),
                   "israel": ("israel", "tel aviv", "haifa", "jerusalem"), "japan": ("japan", "tokyo", "osaka"),
                   "australia": ("australia", "sydney", "melbourne", "brisbane", "adelaide", "perth"),
                   "india": ("india", "bengaluru", "bangalore", "mumbai", "delhi", "hyderabad", "chennai", "pune"),
                   "netherlands": ("netherlands", "amsterdam", "eindhoven", "delft", "rotterdam", "the hague"),
                   "switzerland": ("switzerland", "zurich", "zürich", "lausanne", "geneva", "basel"),
                   "sweden": ("sweden", "stockholm", "gothenburg", "göteborg"), "finland": ("finland", "helsinki", "espoo", "tampere"),
                   "spain": ("spain", "madrid", "barcelona", "valencia"), "italy": ("italy", "milan", "milano", "rome", "turin"),
                   "south korea": ("korea", "seoul"), "singapore": ("singapore",), "new zealand": ("new zealand", "auckland", "wellington", "christchurch"),
                   "south africa": ("south africa", "cape town", "stellenbosch", "johannesburg"), "ireland": ("ireland", "dublin", "cork"),
                   "denmark": ("denmark", "copenhagen", "aarhus"), "norway": ("norway", "oslo"), "belgium": ("belgium", "brussels", "leuven", "antwerp"),
                   "austria": ("austria", "vienna", "wien", "graz"), "poland": ("poland", "warsaw", "krakow", "wrocław"), "portugal": ("portugal", "lisbon", "porto"),
                   "estonia": ("estonia", "tallinn"), "taiwan": ("taiwan", "taipei"), "china": ("china", "shanghai", "beijing", "shenzhen"),
                   "brazil": ("brazil", "são paulo", "sao paulo"), "mexico": ("mexico", "méxico"), "uae": ("uae", "abu dhabi", "dubai", "emirates"),
                   "united arab emirates": ("uae", "abu dhabi", "dubai", "emirates")}
        for tok in aliases.get(cty, (cty,)):
            if tok in blob:
                return True
        return False
    return None


_US_METROS = {"bay area", "silicon valley", "san francisco", "sf", "nyc", "new york", "los angeles", "la", "boston", "austin", "denver",
              "seattle", "chicago", "houston", "dallas", "atlanta", "miami", "phoenix", "washington", "d.c.", "dc", "san diego",
              "san jose", "palo alto", "mountain view", "sunnyvale", "redwood city", "oakland", "berkeley", "pittsburgh", "detroit",
              "philadelphia", "huntsville", "el segundo", "long beach", "hawthorne", "torrance", "irvine", "orange county", "boulder",
              "colorado springs", "salt lake city", "portland", "minneapolis", "raleigh", "durham", "nashville", "columbus", "cambridge, ma",
              "somerville", "waltham", "burlington", "arlington", "reston", "mclean", "tysons", "albuquerque", "tucson", "las vegas",
              "orlando", "tampa", "cape canaveral", "melbourne, fl", "greater seattle area", "greater boston", "greater los angeles",
              "greater new york", "san antonio", "kansas city", "st. louis", "indianapolis", "milwaukee", "madison", "ann arbor",
              "cleveland", "cincinnati", "charlotte", "richmond", "baltimore", "wilmington", "providence", "new haven", "hartford",
              "rochester", "buffalo", "syracuse", "albany", "jacksonville", "savannah", "charleston", "new orleans", "oklahoma city",
              "tulsa", "omaha", "des moines", "boise", "spokane", "anchorage", "honolulu", "sacramento", "fresno", "santa barbara",
              "santa clara", "fremont", "menlo park", "san mateo", "south san francisco", "brooklyn", "manhattan", "queens",
              "jersey city", "hoboken", "newark", "princeton", "stamford", "greenwich", "bethesda", "rockville", "fairfax", "alexandria",
              "ventura", "camarillo", "oxnard", "carlsbad", "san marcos", "chandler", "tempe", "mesa", "scottsdale", "gilbert"}


_US_STATES_FULL = {"alabama","alaska","arizona","arkansas","california","colorado","connecticut","delaware","florida","georgia",
                   "hawaii","idaho","illinois","indiana","iowa","kansas","kentucky","louisiana","maine","maryland","massachusetts",
                   "michigan","minnesota","mississippi","missouri","montana","nebraska","nevada","new hampshire","new jersey",
                   "new mexico","new york","north carolina","north dakota","ohio","oklahoma","oregon","pennsylvania","rhode island",
                   "south carolina","south dakota","tennessee","texas","utah","vermont","virginia","washington","west virginia",
                   "wisconsin","wyoming"}


COMMON_WORDS = {
    "icon", "atlas", "orbital", "orbit", "quantum", "sierra", "lunar", "merge", "rain", "slate", "texture", "kinetic", "vantage",
    "zeta", "dispatch", "foundry", "daylight", "dimensional", "nascent", "generalist", "genesis", "union", "ultra", "swan", "twenty",
    "cube", "air", "aurora", "beyond", "breaker", "brilliant", "bubble", "fulcrum", "phantom", "phoenix", "loyal", "amber", "pivotal",
    "humanoid", "apex", "vector", "nova", "lumen", "halo", "helios", "titan", "orion", "matrix", "fusion", "element", "ember", "forge",
    "anchor", "beacon", "bolt", "bridge", "canopy", "cardinal", "cascade", "catalyst", "cipher", "circuit", "clarity", "compass",
    "core", "crest", "delta", "drift", "echo", "edge", "epic", "equal", "ethos", "flux", "focal", "frontier", "gradient", "granite",
    "harbor", "horizon", "impulse", "index", "inertia", "kernel", "keystone", "lattice", "legend", "level", "lighthouse", "magnet",
    "marble", "meridian", "momentum", "monarch", "mosaic", "north", "nimble", "oasis", "onyx", "origin", "outpost", "paradigm",
    "parallel", "pillar", "pioneer", "prism", "pulse", "quest", "radiant", "relay", "resonance", "ridge", "ripple", "sentinel",
    "signal", "solstice", "spark", "spectrum", "summit", "synthesis", "tandem", "tangent", "tempo", "terra", "torch", "trellis",
    "trident", "unity", "vertex", "vessel", "vista", "voyage", "zenith", "menlo", "aleph", "alpha", "beta", "gamma", "omega", "sigma",
    "theta", "lambda", "kappa", "atom", "atoms", "ion", "proton", "neutron", "photon", "electron", "plasma", "carbon", "silicon",
    "copper", "iron", "steel", "gold", "silver", "mercury", "jupiter", "saturn", "mars", "venus", "pluto", "luna", "sol", "stellar",
    "solar", "polar", "arctic", "pacific", "atlantic", "ocean", "river", "lake", "mountain", "valley", "canyon", "desert", "forest",
    "oak", "pine", "cedar", "maple", "willow", "sage", "fern", "ivy", "lotus", "rose", "lily", "iris", "violet", "indigo", "scarlet",
    "crimson", "cobalt", "azure", "jade", "ruby", "pearl", "amber", "coral", "shift", "scale", "stack", "sprint", "launch", "lift",
    "rise", "ascend", "elevate", "boost", "surge", "spring", "summer", "autumn", "winter", "dawn", "dusk", "noon", "midnight", "eclipse",
    "aura", "nexus", "vortex", "quasar", "pulsar", "nebula", "comet", "meteor", "asteroid", "galaxy", "cosmos", "universe", "infinity",
    "eternal", "evolve", "adapt", "thrive", "flourish", "bloom", "harvest", "seed", "root", "branch", "leaf", "stem", "petal", "bud",
    "hive", "nest", "den", "burrow", "lair", "haven", "refuge", "sanctuary", "shelter", "shield", "armor", "sword", "arrow", "spear",
    "hammer", "anvil", "wrench", "gear", "cog", "lever", "pulley", "wheel", "axle", "engine", "motor", "turbine", "rotor", "propeller",
    "wing", "fin", "hull", "keel", "mast", "sail", "rudder", "anchor", "harbor", "port", "dock", "pier", "wharf", "jetty", "quay",
    "foundation", "generalist", "kinetic", "standard", "general", "national", "american", "united", "global", "first", "next", "new",
    "modern", "future", "advanced", "applied", "common", "public", "private", "open", "free", "true", "pure", "clear", "bright",
    "swift", "rapid", "quick", "fast", "sure", "safe", "sound", "solid", "firm", "strong", "bold", "brave", "noble", "royal", "regent",
}


def set_universe(names):
    """Tell the verifier which company names exist, so a one-word org shared by several (Atlas, Orbital…) is treated as ambiguous."""
    global _UNIVERSE_FIRST_WORDS
    cnt = {}
    for n in names or []:
        ws = name_words(n)
        first = next((w for w in ws if w not in ("the", "a", "an")), "")
        if first:
            cnt[first] = cnt.get(first, 0) + 1
    _UNIVERSE_FIRST_WORDS = cnt


_UNIVERSE_FIRST_WORDS = {}
_STOP_NAME_WORDS = {"inc", "corp", "co", "llc", "ltd", "plc", "the", "and", "of", "a", "an", "ai", "gmbh", "ag", "sa", "corporation", "company"}


def _clean_org(org):
    """'Careers at Aalyria' / 'AIM Jobs' / 'Jobs bei AURORA' -> 'aalyria' / 'aim' / 'aurora'."""
    o = (org or "").lower()
    o = re.sub(r"\b(careers?|jobs?|openings?|opportunities|positions?|join|work|hiring|at|the|with|us|our|team|bei|chez|en)\b", " ", o)
    o = re.sub(r"[|·•\-–—:]+.*$", " ", o) if re.search(r"\s[|·•–—]\s", o) else o
    return norm(o)


def verify_candidate(company, website, platform, slug, probe, own_site=False, crowded=False, hq="", country=""):
    """
    Returns (accepted, reason). `probe` is probe_board()'s dict.
    own_site: the slug came from the company's own website (link or embed).
    crowded: that page listed several boards (an aggregator, a portfolio page or an acquisition), so
             own-site alone is not enough — the board has to name the company.
    hq / country: the company's HQ from data.js. Blind-probe matches on a single word (an org called
             'Aurora' for 'Aurora Innovation') are accepted only when a posting location agrees with it.
    """
    if not probe.get("exists"):
        return False, "board not found"
    if own_site and not crowded:
        return True, "own-site" if probe.get("ok") else "own-site (empty board)"
    if not probe.get("ok"):
        return False, "empty board, no own-site evidence"
    n_name = norm(company)
    dbase = domain_base(website)
    dhost = domain_host(website)
    org_raw = probe.get("org") or ""
    org = _clean_org(org_raw)
    text = (probe.get("text") or "").lower()
    n_text = norm(text)
    blob = " ".join(probe.get("urls", []) + probe.get("titles", [])).lower() + " " + text
    words = name_words(company)
    dwords = distinctive_words(company)
    single = len(words) == 1
    first = next((w for w in words if w not in ("the", "a", "an")), "")
    geo = location_corroborates(hq, country, probe.get("locations"))

    def weak(reason):
        # a one-word match needs the board's job locations to agree with the company's HQ
        if geo is False:
            return False, reason + ", but postings are elsewhere (" + "; ".join(probe.get("locations", [])[:3]) + ")"
        return True, reason + ("" if geo is None else ", locations agree")

    extra = [w for w in words if w != first and w not in _STOP_NAME_WORDS and len(w) >= 3]
    ambiguous = _UNIVERSE_FIRST_WORDS.get(first, 0) > 1 or first in COMMON_WORDS

    def one_word_match(reason):
        """The board only confirms ONE word of the name. Demand the rest of the name, or the domain, in the posting."""
        if extra:
            missing = [w for w in extra if not re.search(r"\b" + re.escape(w.rstrip("s")) , text)]
            if not missing:
                return weak(reason + "; rest of name in posting")
            if dhost and dhost in blob:
                return weak(reason + f"; domain {dhost} in posting")
            return False, reason + f", but posting never mentions '{missing[0]}'"
        # single-word company
        if ambiguous:
            if dhost and dhost in blob:
                return weak(reason + f"; domain {dhost} in posting")
            if dbase and len(dbase) >= 4 and any(f"{dbase}.{tld}" in blob for tld in ("com", "ai", "io", "co", "tech", "energy", "space", "bio", "dev", "net", "org", "eu", "de", "fr", "uk")):
                return weak(reason + f"; domain base {dbase} in posting")
            return False, reason + ", but it is a common word and the posting never names the domain"
        return weak(reason)

    # 1. the board names the organisation
    if org:
        org_words = [w for w in name_words(re.sub(r"\b(careers?|jobs?|openings?|join|work|hiring|at|the|with|us|our|team|bei|chez)\b", " ", org_raw.lower())) if w]
        leftover = [w for w in org_words if w not in words and w not in GENERIC_WORDS and w not in _STOP_NAME_WORDS
                    and not any(w in nw or nw in w for nw in words if len(nw) >= 4)]
        if leftover and not (n_name and n_name in org):
            # the board's own name carries words that are not in the company's name: Archer Veterinary Clinic ≠ Archer Materials
            return False, f"org is '{org_raw.strip()}' (extra words: {', '.join(leftover[:3])})"
        if n_name and n_name in org and not single:
            return True, f"org '{org_raw.strip()}' matches name"
        if n_name and org == n_name:
            if single:
                return one_word_match(f"org '{org_raw.strip()}' is the name") if (len(n_name) < 5 or ambiguous) else (True, f"org '{org_raw.strip()}' is the name")
            return True, f"org '{org_raw.strip()}' is the name"
        if n_name and len(org) >= 4 and org in n_name:
            return one_word_match(f"org '{org_raw.strip()}' is part of the name")
        if dbase and len(dbase) >= 4 and dbase in org:
            remainder = org.replace(dbase, "", 1)
            if remainder and not all(any(g in remainder for g in list(GENERIC_WORDS) + words) for _ in [0]) and remainder not in GENERIC_WORDS and not any(w in remainder for w in words if len(w) >= 3):
                return False, f"org is '{org_raw.strip()}' (shares only '{dbase}')"
            if len(dbase) >= 6 and dbase not in COMMON_WORDS and not ambiguous:
                return True, f"org '{org_raw.strip()}' matches domain"
            return one_word_match(f"org '{org_raw.strip()}' matches domain")
        if dwords and len(dwords) >= 2 and all(w in org for w in dwords) and not single:
            return True, f"org '{org_raw.strip()}' has all distinctive words"
        if dwords and len(dwords) == 1 and dwords[0] in org and not single:
            return one_word_match(f"org '{org_raw.strip()}' has the distinctive word '{dwords[0]}'")
        if first and len(first) >= 3 and org == norm(first) and (norm(slug) == norm(first) or norm(slug) == dbase):
            return one_word_match(f"org '{org_raw.strip()}' is the company's first word")
        return False, f"org is '{org_raw.strip()}'"
    # 2. the posting text mentions the company's domain
    if dhost and dhost in blob:
        return True, f"domain {dhost} in posting"
    if dbase and len(dbase) >= 5 and any(f"{dbase}.{tld}" in blob for tld in ("com", "ai", "io", "co", "tech", "energy", "space", "bio", "dev", "net", "org", "eu", "de", "fr", "uk")):
        return True, f"domain base {dbase} in posting"
    if dbase and len(dbase) >= 4 and f"@{dbase}." in blob:
        return True, f"email domain {dbase} in posting"
    # 3. the posting text contains the full company name (multi-word names only — a single common word proves nothing)
    if n_name and len(n_name) >= 6 and not single and n_name in n_text:
        return True, "full name in posting"
    if dwords and len(dwords) >= 2 and all(w in text for w in dwords):
        return True, "all distinctive words in posting"
    if single and dwords:
        w = dwords[0]
        if len(w) >= 7 and re.search(r"\b" + re.escape(w) + r"\b", text):
            return one_word_match(f"coined name '{w}' in posting")
    # 4. no organisation name anywhere, but the slug IS the company's domain (isee.ai -> lever/isee)
    if dbase and len(dbase) >= 4 and norm(slug) == norm(dbase) and dbase not in GENERIC_WORDS:
        return one_word_match(f"slug equals domain '{dbase}', board names nobody else")
    return False, "no name/domain match in postings"


def today_iso():
    return date.today().isoformat()
