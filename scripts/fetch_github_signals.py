#!/usr/bin/env python3
"""
GitHub Signals Fetcher
======================
Tracks GitHub organization-level activity for frontier tech companies with
public repos. Produces a structured "activity score" for each company based on
repos, stars, contributors, recent commits, and releases.

Uses the public GitHub API. Works without an API token but is rate-limited to
60 requests/hour. If GITHUB_TOKEN env var is set, the limit bumps to 5000/hr.

Strategy per company:
    1. Search GitHub orgs/users by company name
    2. Pick the best-matching org
    3. Fetch org details, repos, commit activity

Input:
    scripts/company_master_list.js  — canonical company list

Output:
    data/github_signals_auto.json       — structured signals per company
    data/github_signals_status.json     — fetch status metadata
    data/github_signals_etag_cache.json — ETag cache for conditional requests

Run standalone:
    python3 scripts/fetch_github_signals.py

Environment:
    GITHUB_TOKEN   (optional) — personal access token for higher rate limit
    GITHUB_SIGNALS_LIMIT (optional, default 120) — max companies per run
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# ─────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("github_signals")

# ─────────────────────────────────────────────────────────────────
# Paths and constants
# ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
MASTER_LIST_PATH = SCRIPT_DIR / "company_master_list.js"
ETAG_CACHE_PATH = DATA_DIR / "github_signals_etag_cache.json"

GITHUB_API = "https://api.github.com"
USER_AGENT = "InnovatorsLeague-GitHubSignals/1.0"
REQUEST_TIMEOUT = 20
DEFAULT_MAX_COMPANIES = int(os.environ.get("GITHUB_SIGNALS_LIMIT", "120"))

# Built-in known org overrides (company name -> github org slug).
# Fast path that skips the search step entirely.
KNOWN_ORG_OVERRIDES = {
    "OpenAI": "openai",
    "Anthropic": "anthropics",
    "Hugging Face": "huggingface",
    "LangChain": "langchain-ai",
    "LlamaIndex": "run-llama",
    "Scale AI": "scaleapi",
    "Palantir": "palantir",
    "HashiCorp": "hashicorp",
    "Pulumi": "pulumi",
    "Databricks": "databricks",
    "dbt Labs": "dbt-labs",
    "DeepMind": "deepmind",
    "Meta AI": "facebookresearch",
    "NVIDIA Isaac": "nvidia-isaac",
    "IBM Quantum": "Qiskit",
    "Google Quantum AI": "quantumlib",
    "Rigetti Computing": "rigetti",
    "Xanadu": "XanaduAI",
    "Physical Intelligence": "Physical-Intelligence",
    "Cognition": "cognitionlabs",
    "Stability AI": "Stability-AI",
    "Mistral": "mistralai",
    "Together AI": "togethercomputer",
    "Cohere": "cohere-ai",
    "Weights & Biases": "wandb",
    "Tesla": "teslamotors",
    "Neuralink": "neuralink",
    "SpaceX": "spacex",
    "Nvidia": "NVIDIA",
}


# ─────────────────────────────────────────────────────────────────
# GitHub session + rate limiting
# ─────────────────────────────────────────────────────────────────
class GitHubSession:
    """Wraps requests.Session with auth, retries, ETag cache, rate-limit handling."""

    def __init__(self):
        self.session = requests.Session()
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
            logger.info("Using authenticated GitHub API (5000 req/hr limit)")
        else:
            logger.info("Using anonymous GitHub API (60 req/hr limit)")
        self.session.headers.update(headers)
        self.etag_cache = self._load_etag_cache()
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

    def _load_etag_cache(self):
        if ETAG_CACHE_PATH.exists():
            try:
                with open(ETAG_CACHE_PATH) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_etag_cache(self):
        DATA_DIR.mkdir(exist_ok=True)
        try:
            with open(ETAG_CACHE_PATH, "w") as f:
                json.dump(self.etag_cache, f, indent=2)
        except Exception as e:
            logger.warning("Could not save ETag cache: %s", e)

    def _update_rate_limit(self, resp):
        rem = resp.headers.get("X-RateLimit-Remaining")
        rst = resp.headers.get("X-RateLimit-Reset")
        if rem is not None:
            self.rate_limit_remaining = int(rem)
        if rst is not None:
            self.rate_limit_reset = int(rst)

    def get(self, path, params=None, use_etag=True):
        """
        GET a GitHub API path. Returns (data, status_code).
        On 304 (cache hit), returns cached data. On error, returns (None, status).
        """
        if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 1:
            now = int(time.time())
            wait = max(0, (self.rate_limit_reset or 0) - now)
            if wait > 0 and wait <= 60:
                logger.info("  rate limit nearly exhausted, sleeping %ds", wait)
                time.sleep(wait + 1)
            else:
                logger.warning("  rate limit exhausted (remaining=%s, reset in %ds) — aborting",
                               self.rate_limit_remaining, wait)
                return None, 429

        url = f"{GITHUB_API}{path}"
        headers = {}
        cache_entry = self.etag_cache.get(url) if use_etag else None
        if cache_entry and cache_entry.get("etag"):
            headers["If-None-Match"] = cache_entry["etag"]

        for attempt in range(1, 4):
            try:
                resp = self.session.get(
                    url, params=params, headers=headers, timeout=REQUEST_TIMEOUT
                )
                self._update_rate_limit(resp)

                if resp.status_code == 304 and cache_entry:
                    return cache_entry.get("data"), 304

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except ValueError:
                        return None, resp.status_code
                    etag = resp.headers.get("ETag")
                    if use_etag and etag:
                        self.etag_cache[url] = {"etag": etag, "data": data}
                    return data, 200

                if resp.status_code == 404:
                    return None, 404

                if resp.status_code == 403 and "rate limit" in resp.text.lower():
                    reset = resp.headers.get("X-RateLimit-Reset")
                    if reset:
                        self.rate_limit_reset = int(reset)
                        self.rate_limit_remaining = 0
                    logger.warning("  rate limited (403) — stopping")
                    return None, 403

                # Other errors: brief backoff + retry
                logger.warning("  HTTP %s for %s (attempt %d/3)", resp.status_code, path, attempt)
                time.sleep(2 * attempt)

            except requests.exceptions.RequestException as e:
                logger.warning("  request error (attempt %d/3): %s", attempt, e)
                time.sleep(2 * attempt)

        return None, -1


# ─────────────────────────────────────────────────────────────────
# Master company list loader
# ─────────────────────────────────────────────────────────────────
def load_master_companies():
    """Load company list from the JS master file."""
    if not MASTER_LIST_PATH.exists():
        logger.warning("company_master_list.js not found")
        return []
    content = MASTER_LIST_PATH.read_text()
    companies = []
    pattern = r'\{\s*name:\s*"([^"]+)"'
    for match in re.finditer(pattern, content):
        name = match.group(1)
        companies.append({"name": name})
    logger.info("Loaded %d companies from master list", len(companies))
    return companies


# ─────────────────────────────────────────────────────────────────
# GitHub data fetching
# ─────────────────────────────────────────────────────────────────
def slugify_company(name):
    """Turn a company name into plausible org slug candidates."""
    base = re.sub(r"[^A-Za-z0-9 ]", "", name).strip()
    parts = base.split()
    if not parts:
        return []
    candidates = [
        base.lower().replace(" ", ""),
        base.lower().replace(" ", "-"),
        "".join(p.lower() for p in parts),
        parts[0].lower(),
    ]
    # Dedupe while preserving order
    seen = set()
    out = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def find_org_for_company(gh, company_name):
    """
    Try to find a GitHub organization for a company.
    Returns org slug or None.
    """
    # 1) known override
    if company_name in KNOWN_ORG_OVERRIDES:
        return KNOWN_ORG_OVERRIDES[company_name]

    # 2) try direct lookup on candidate slugs
    for candidate in slugify_company(company_name):
        data, status = gh.get(f"/orgs/{candidate}", use_etag=False)
        if status == 200 and data and data.get("login"):
            return data["login"]

    return None


def fetch_org_repos(gh, org_slug, max_repos=30):
    """Fetch public repos for an org, sorted by stars."""
    repos, status = gh.get(
        f"/orgs/{org_slug}/repos",
        params={"per_page": 100, "sort": "updated", "type": "public"},
    )
    if status == 304:
        # etag unchanged — return cached data
        return repos or [], True
    if status not in (200,) or not repos:
        return [], False
    repos.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    return repos[:max_repos], False


def fetch_latest_release(gh, owner, repo_name):
    """Fetch the latest release for a repo. Returns date string or None."""
    data, status = gh.get(f"/repos/{owner}/{repo_name}/releases/latest")
    if status == 200 and data and data.get("published_at"):
        return data["published_at"][:10]
    return None


def fetch_contributor_count(gh, owner, repo_name):
    """Fetch contributor count (approx)."""
    data, status = gh.get(
        f"/repos/{owner}/{repo_name}/contributors",
        params={"per_page": 100, "anon": "true"},
    )
    if status == 200 and isinstance(data, list):
        return len(data)
    return 0


def count_recent_commits(gh, owner, repo_name, days=30):
    """Count commits in the last `days` days (capped at 100)."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    data, status = gh.get(
        f"/repos/{owner}/{repo_name}/commits",
        params={"since": since, "per_page": 100},
    )
    if status == 200 and isinstance(data, list):
        return len(data)
    return 0


def score_activity(signal):
    """Compute a 0-100 activity score from a signal dict."""
    stars = signal.get("total_stars", 0)
    commits = signal.get("commits_30d", 0)
    contribs = signal.get("contributors", 0)
    repos = signal.get("total_repos", 0)
    last_release = signal.get("last_release")

    score = 0
    # Star power (log-scale, up to 40 pts)
    if stars > 0:
        import math
        score += min(40, int(math.log10(stars + 1) * 10))
    # Commit velocity (up to 25 pts)
    score += min(25, commits // 4)
    # Contributor depth (up to 15 pts)
    score += min(15, contribs // 10)
    # Repo breadth (up to 10 pts)
    score += min(10, repos)
    # Recent release (up to 10 pts)
    if last_release:
        try:
            rel_date = datetime.strptime(last_release, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_ago = (datetime.now(timezone.utc) - rel_date).days
            if days_ago <= 30:
                score += 10
            elif days_ago <= 90:
                score += 5
        except Exception:
            pass
    return min(100, score)


def build_company_signal(gh, company_name):
    """Assemble a signal record for one company. Returns dict or None."""
    org = find_org_for_company(gh, company_name)
    if not org:
        return None

    # Fetch repos (sorted by stars)
    repos, _ = fetch_org_repos(gh, org)
    if not repos:
        return None

    total_repos = len(repos)
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)

    # Aggregate languages across top-10 repos (top 5 languages by frequency)
    lang_counts = {}
    for r in repos[:10]:
        lang = r.get("language")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    languages = [
        lang for lang, _ in sorted(lang_counts.items(), key=lambda x: -x[1])
    ][:5]

    # Top repo details
    top_repo = repos[0]
    top_repo_full = top_repo.get("full_name", f"{org}/{top_repo.get('name', '')}")
    top_repo_stars = top_repo.get("stargazers_count", 0)

    # Deeper stats only on the top repo (to conserve rate limit)
    contributors = fetch_contributor_count(gh, org, top_repo.get("name", ""))
    commits_30d = count_recent_commits(gh, org, top_repo.get("name", ""))
    last_release = fetch_latest_release(gh, org, top_repo.get("name", ""))

    signal = {
        "company": company_name,
        "github_org": org,
        "total_repos": total_repos,
        "total_stars": total_stars,
        "contributors": contributors,
        "commits_30d": commits_30d,
        "last_release": last_release,
        "top_repo": top_repo_full,
        "top_repo_stars": top_repo_stars,
        "languages": languages,
        "activity_score": 0,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    signal["activity_score"] = score_activity(signal)
    return signal


# ─────────────────────────────────────────────────────────────────
# File I/O
# ─────────────────────────────────────────────────────────────────
def save_json(data, filename):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %s (%d bytes)", path, path.stat().st_size)


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 60)
    logger.info("GitHub Signals Fetcher")
    logger.info("=" * 60)

    companies = load_master_companies()
    if not companies:
        logger.error("No companies loaded — aborting")
        save_json({
            "script": "fetch_github_signals.py",
            "ok": False,
            "error": "master list missing",
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }, "github_signals_status.json")
        save_json([], "github_signals_auto.json")
        return

    gh = GitHubSession()
    started_at = datetime.now(timezone.utc).isoformat()

    # Cap the number of companies processed per run to stay within rate limit
    limit = DEFAULT_MAX_COMPANIES
    to_process = companies[:limit]
    logger.info("Processing %d/%d companies (rate-limit cap = %d)",
                len(to_process), len(companies), limit)

    signals = []
    skipped = 0
    errors = 0

    for i, company in enumerate(to_process, 1):
        name = company["name"]
        logger.info("[%d/%d] %s", i, len(to_process), name)
        try:
            signal = build_company_signal(gh, name)
            if signal:
                signals.append(signal)
                logger.info("  -> org=%s stars=%d repos=%d score=%d",
                            signal["github_org"], signal["total_stars"],
                            signal["total_repos"], signal["activity_score"])
            else:
                skipped += 1
        except Exception as e:
            errors += 1
            logger.warning("  error processing %s: %s", name, e)

        # Stop early if rate limit is gone
        if gh.rate_limit_remaining is not None and gh.rate_limit_remaining <= 1:
            logger.warning("Rate limit exhausted after %d companies — stopping", i)
            break

    # Sort by activity score descending
    signals.sort(key=lambda s: s.get("activity_score", 0), reverse=True)

    # Save outputs + ETag cache
    save_json(signals, "github_signals_auto.json")
    gh.save_etag_cache()

    status = {
        "script": "fetch_github_signals.py",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "companies_checked": i if to_process else 0,
        "companies_with_signal": len(signals),
        "skipped_no_org": skipped,
        "errors": errors,
        "rate_limit_remaining": gh.rate_limit_remaining,
        "ok": True,
    }
    save_json(status, "github_signals_status.json")

    if signals:
        logger.info("\nTop 10 by activity score:")
        for s in signals[:10]:
            logger.info("  %-25s  score=%-3d  stars=%-7d  org=%s",
                        s["company"][:25], s["activity_score"],
                        s["total_stars"], s["github_org"])
    logger.info("=" * 60)
    logger.info("Done. %d signals, %d skipped, %d errors",
                len(signals), skipped, errors)
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        save_json({
            "script": "fetch_github_signals.py",
            "ok": False,
            "fatal_error": str(e),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }, "github_signals_status.json")
        raise
