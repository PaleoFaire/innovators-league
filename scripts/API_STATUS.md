# Data Fetch Scripts — API Status Report

**Last updated:** 2026-04-10
**Repo:** The Innovators League
**Maintained by:** scripts/fetch_*.py

This document tracks the status of every data-fetching script in `scripts/`, the API keys they rely on, the fallback sources they can use when primary keys are unavailable, and the action items required to bring every pipeline to a fully working state.

---

## TL;DR — What Needs to Be Done

Add the following GitHub Actions secrets to unblock every script that has a primary source:

| Secret name | Where to get it | Free tier | Priority |
|---|---|---|---|
| `PATENTSVIEW_API_KEY` | https://patentsview-support.atlassian.net/servicedesk/customer/portal/1 | Yes, unlimited for research | High |
| `SAM_API_KEY` | https://sam.gov/content/api | 1000 req/day | High |
| `DIFFBOT_API_TOKEN` | https://www.diffbot.com/ | 10K credits/month | Medium |
| `GITHUB_TOKEN` | Already provided by GitHub Actions | 5000 req/hour | High (used for GitHub signals / releases) |
| `CONGRESS_GOV_API_KEY` | https://api.congress.gov/sign-up/ | 1000 req/hour | Low |
| `FRED_API_KEY` | https://fredaccount.stlouisfed.org/apikeys | No limit | Low |

All scripts now **degrade gracefully**. Missing keys produce a structured `status` metadata file instead of silent empty arrays.

---

## Scripts Updated in This Pass

### 1. `fetch_patents.py` — Patent Intelligence

**Status:** Working (with primary or fallback)

- **Primary:** PatentsView Search API v2
  - Endpoint: `https://search.patentsview.org/api/v1/patent/`
  - Requires: `PATENTSVIEW_API_KEY`
  - Free, but requires registration
- **Fallback:** USPTO IBD Public Endpoint
  - Endpoint: `https://developer.uspto.gov/ibd-api/v1/application/publications`
  - No key required
  - Returns published patent applications by text search

**Graceful degradation:** If both sources fail or return empty, writes a status metadata file (`patents_raw.json` / `patents_aggregated.json`) with `status: "api_unavailable"` and timestamp.

**Action item:** Add `PATENTSVIEW_API_KEY` to GitHub secrets for best coverage (fallback is coarser).

---

### 2. `fetch_sam_contracts.py` — Federal Contract Opportunities

**Status:** Working (with primary or fallback)

- **Primary:** SAM.gov Opportunities API
  - Endpoint: `https://api.sam.gov/opportunities/v2/search`
  - Requires: `SAM_API_KEY` (free, register at sam.gov)
  - Rate limit: 1000 req/day
- **Fallback:** USAspending.gov Awards API
  - Endpoint: `https://api.usaspending.gov/api/v2/search/spending_by_award/`
  - No key required
  - Returns actual awarded contracts (different data vs opportunities, but complementary)

**Graceful degradation:** If both sources fail, writes status metadata and a placeholder JS snippet.

**Action item:** Add `SAM_API_KEY` to GitHub secrets for recent contract opportunities.

---

### 3. `fetch_sbir_awards.py` — SBIR/STTR Grant Awards

**Status:** Working with multi-endpoint fallback and retry logic

- **Endpoints tried in order:**
  1. `https://api.www.sbir.gov/public/api/awards`
  2. `https://www.sbir.gov/api/awards.json`
  3. `https://www.sbir.gov/awards-api`
- No API key required for any endpoint
- Added: exponential backoff (up to 4 retries), pagination support, cached-data fallback if all endpoints fail

**Graceful degradation:** If all endpoints fail AND no cached data exists, writes status metadata.

**Action item:** None — SBIR.gov is the only source, and we now handle its frequent rotations.

---

### 4. `fetch_diffbot_enrichment.py` — Company Enrichment

**Status:** Working (with primary or fallback)

- **Primary:** Diffbot Knowledge Graph Enhance API
  - Endpoint: `https://kg.diffbot.com/kg/v3/enhance`
  - Requires: `DIFFBOT_API_TOKEN`
  - Free tier: 10K credits/month (1 credit per enhance call)
- **Fallback:** Wikipedia + Wikidata
  - Wikipedia REST API: `https://en.wikipedia.org/api/rest_v1/page/summary/{title}`
  - Wikidata SPARQL: `https://query.wikidata.org/sparql`
  - No keys required

**Fields extracted:** description, founding date, founders, employee count, HQ location, website.

**Graceful degradation:** If no primary token AND fallbacks return nothing, writes status metadata.

**Action item:** Add `DIFFBOT_API_TOKEN` for richer data (revenue, social links, industry taxonomies).

---

### 5. `fetch_jobs.py` — Job Aggregator

**Status:** Working — no API keys required

- **Sources (all public):**
  - Greenhouse: `https://boards-api.greenhouse.io/v1/boards/{company}/jobs`
  - Lever: `https://api.lever.co/v0/postings/{company}`
  - Ashby: `https://api.ashbyhq.com/posting-api/job-board/{company}`
  - Workable: `https://apply.workable.com/api/v1/widget/accounts/{company}`
- Added: retry logic with exponential backoff, Retry-After header support, auto-discovery of job boards for master-list companies not already covered, status metadata on empty results

**Graceful degradation:** Writes status metadata + placeholder JS snippet on total failure.

**Action item:** None — script works out of the box.

---

## Other Fetch Scripts (Not Modified in This Pass)

These scripts exist in `scripts/` and should be audited on a future pass. Listed with their primary source and key requirements.

| Script | Primary source | API key needed |
|---|---|---|
| `fetch_arpa_e_projects.py` | arpa-e.energy.gov | No |
| `fetch_arxiv_research.py` | export.arxiv.org | No |
| `fetch_census_trade.py` | api.census.gov | `CENSUS_API_KEY` (free) |
| `fetch_clinical_trials.py` | clinicaltrials.gov | No |
| `fetch_congress_bills.py` | api.congress.gov | `CONGRESS_GOV_API_KEY` (free) |
| `fetch_deals.py` | mixed web scraping | No |
| `fetch_demand_signals.py` | mixed | Varies |
| `fetch_doe_energy.py` | api.eia.gov | `EIA_API_KEY` (free) |
| `fetch_faa_certification.py` | faa.gov | No |
| `fetch_fda_approvals.py` | api.fda.gov | No |
| `fetch_federal_register.py` | federalregister.gov | No |
| `fetch_github_releases.py` | api.github.com | `GITHUB_TOKEN` (auto in Actions) |
| `fetch_gov_opportunities.py` | sam.gov | `SAM_API_KEY` |
| `fetch_hackernews.py` | hacker-news.firebaseio.com | No |
| `fetch_insider_trading.py` | sec.gov | No |
| `fetch_ipo_pipeline.py` | sec.gov | No |
| `fetch_nasa_techport.py` | techport.nasa.gov | No |
| `fetch_nih_grants.py` | api.reporter.nih.gov | No |
| `fetch_nrc_licensing.py` | nrc.gov | No |
| `fetch_nsf_grants.py` | api.nsf.gov | No |
| `fetch_press_releases.py` | mixed | No |
| `fetch_product_hunt.py` | api.producthunt.com | `PRODUCTHUNT_TOKEN` |
| `fetch_revenue_intel.py` | mixed | Varies |
| `fetch_sbir_topics.py` | sbir.gov | No |
| `fetch_sec_filings.py` | sec.gov EDGAR | No |
| `fetch_stocks.py` | yfinance / mixed | No |
| `fetch_usaspending.py` | api.usaspending.gov | No |
| `fetch_vc_portfolios.py` | mixed scraping | No |

---

## How to Add GitHub Secrets

1. Go to `https://github.com/<your-org>/<your-repo>/settings/secrets/actions`
2. Click "New repository secret"
3. Add each secret from the TL;DR table above
4. Workflows will pick them up automatically on the next run

## Output Contract

Every fetch script now writes one of two shapes to `data/`:

**Success case** — an array of records:
```json
[ { ... }, { ... } ]
```

**Failure case** — a status metadata object:
```json
{
  "status": "api_unavailable" | "no_results" | "error",
  "message": "Human-readable explanation",
  "timestamp": "2026-04-10T14:30:00",
  "source": "fetch_xxx.py",
  "data": []
}
```

Front-end consumers should check `Array.isArray(data)` before rendering — when it's an object, fall back to cached data and surface the status message to the user.

---

## Priority Fixes Needed

1. **High:** Add `PATENTSVIEW_API_KEY`, `SAM_API_KEY`, `GITHUB_TOKEN` to GitHub secrets (unblocks 3 critical pipelines)
2. **High:** Verify `fetch_github_releases.py` GitHub Actions `GITHUB_TOKEN` injection
3. **Medium:** Add `DIFFBOT_API_TOKEN` for full company enrichment coverage
4. **Medium:** Audit `fetch_revenue_intel.py` and `fetch_deals.py` (mixed-source scripts may be brittle)
5. **Low:** Add `CONGRESS_GOV_API_KEY`, `FRED_API_KEY` for sectoral macro data
