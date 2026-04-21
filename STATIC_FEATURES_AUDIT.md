# Static Features Audit — What's Live vs. What Needs Fixing

**Auditor:** Claude · **Date:** 2026-04-21 · **Scope:** all 22 HTML pages + 71 data arrays in `data.js` + 8 GitHub Actions workflows

---

## TL;DR

- **23 arrays are fully auto-updated** (news, gov contracts, SBIR awards, SEC filings, stocks, jobs, patents, Frontier Index scores, growth/predictive/sector/valuation/revenue/headcount/deal/funding, IPO pipeline, NASA/NIH/ARPA-E grants, trade data, Diffbot enrichment).
- **7 arrays are STATIC + HIGH-RISK** — they contain member-facing content that goes stale fast (Field Notes, Expert Insights, M&A Comps, Budget Signals, Fund Intelligence, Live Award Feed).
- **13 arrays are STATIC + MEDIUM-RISK** — have pipelines already written but unwired, or can be auto-derived from existing data (VC Firms, Founder Mafias, Network Graph, Product Launches, Gov Demand Tracker, Alerts, Contractor Readiness…).
- **21 arrays are intentionally static** (methodology docs, taxonomies, UI config, Stephen's personal Founder Connections).
- **1 CRITICAL CONFLICT** identified: `scripts/merge_data.py` runs every day and overwrites `INNOVATOR_SCORES` from a thinner auto-json, wiping insight-rich notes. Must be resolved. *(Fix shipped in Round 7k below.)*

---

## ✅ Live & Auto-Updated (23 arrays)

These update themselves. No action needed unless a pipeline is broken.

| Array | Cadence | Workflow | Data source |
|---|---|---|---|
| COMPANY_SIGNALS | Hourly | hourly-news-sync | `aggregate_news.js` (33 RSS feeds) |
| NEWS_FEED | Hourly | hourly-news-sync | RSS |
| NEWS_TICKER | Hourly | hourly-news-sync | RSS |
| INNOVATOR_SCORES | Daily + Sun | daily-data-sync + weekly-intelligence-sync | `calc_innovator_scores.py` + `sync_weekly_metrics.py` |
| MOSAIC_SCORES | Sun | weekly-intelligence-sync | `sync_weekly_metrics.py` |
| TRL_RANKINGS | Sun | weekly-intelligence-sync | `sync_weekly_metrics.py` |
| GROWTH_SIGNALS | Daily | daily-data-sync | `calc_growth_signals.py` |
| HEADCOUNT_ESTIMATES | Daily | daily-data-sync | `calc_headcount_estimates.py` + `fetch_jobs.py` |
| PREDICTIVE_SCORES | Daily | daily-data-sync | `calc_predictive_scores.py` |
| SECTOR_MOMENTUM | Daily | daily-data-sync | `calc_sector_momentum.py` |
| VALUATION_BENCHMARKS | Daily | daily-data-sync | `calc_valuation_benchmarks.py` |
| REVENUE_INTEL | Daily | daily-data-sync | `fetch_revenue_intel.py` |
| DEAL_TRACKER | Daily | daily-data-sync | `fetch_deals.py` + `merge_data.py` |
| FUNDING_TRACKER | Daily | daily-data-sync | `calc_funding_tracker.py` |
| IPO_PIPELINE | Daily | daily-data-sync | `fetch_ipo_pipeline.py` |
| DIFFBOT_ENRICHMENT | Daily | comprehensive-data-sync | `fetch_diffbot_enrichment.py` |
| PATENT_INTEL | Weekly Sun | weekly-patent-sync | `fetch_patents.py` |
| GOV_CONTRACTS | Daily | comprehensive-data-sync | `fetch_sam_contracts.py` + `fetch_demand_signals.py` |
| SAM_CONTRACTS | Daily | comprehensive-data-sync | `fetch_sam_contracts.py` |
| SBIR_AWARDS | Daily | comprehensive-data-sync | `fetch_sbir_awards.py` |
| NIH_GRANTS | Daily | comprehensive-data-sync | `fetch_nih_grants.py` |
| ARPA_E_PROJECTS | Daily | comprehensive-data-sync | `fetch_arpa_e_projects.py` |
| TRADE_DATA | Daily | comprehensive-data-sync | `fetch_census_trade.py` |

All company-facing news signals (`data/news_signals_auto.js`), press releases (`press_releases_auto.js`), stock prices (`stocks_auto.js`), and jobs (`jobs_auto.js`) are also refreshed by dedicated workflows.

---

## ⚠️ STATIC — HIGH RISK (7 arrays)

**These are visible to members and go stale fast without manual curation.**

### 1. FIELD_NOTES
- **What it is:** Stephen's podcast highlights, founder calls, site-visit notes. Renders on the Frontier Daily.
- **Why risky:** Members expect fresh editorial content; stale entries undermine the trust signal.
- **Fix options:**
  - **A.** Add `scripts/fetch_substack_posts.py` that pulls `rationaloptimistsociety.substack.com` RSS and creates `data/field_notes_auto.json`, then inject via `merge_data.py`.
  - **B.** Build a tiny admin-only form page that writes to a `data/field_notes_manual.json` committed via GitHub API.
- **Recommended:** Option A. RSS is trivial; Stephen posts on Substack anyway.

### 2. EXPERT_INSIGHTS + EXPERT_TAKES
- **What they are:** Curated expert takes — hand-written.
- **Fix:** Pull selected quotes from earnings-signals extraction + LinkedIn posts of named experts. Quarterly manual refresh as a fallback.
- **Recommended:** Lightweight `scripts/curate_expert_takes.py` that picks top-scoring earnings-signal quotes tagged `"expert_take": true`.

### 3. BUDGET_SIGNALS
- **What it is:** DoD/NASA budget signals per sector.
- **Why risky:** Federal budget cycle is a key tailwind indicator; updates quarterly at minimum.
- **Fix:** `scripts/calc_budget_signals.py` reads `federal_register_auto.js` + `congress_bills_auto.js`, keyword-matches for budget/appropriations items per sector, writes `data/budget_signals_auto.json`.
- **Status:** Feeds already exist (`fetch_federal_register.py`, `fetch_congress_bills.py`) — just needs a calc script + wiring.

### 4. FUND_INTELLIGENCE
- **What it is:** VC fund-level research.
- **Fix:** Wire `fetch_vc_portfolios.py` (already exists in `comprehensive-data-sync.yml`!) → new `calc_fund_intelligence.py` that aggregates per-fund metrics (portfolio company count, sector mix, check size, momentum) and emits `data/fund_intelligence_auto.json`.
- **Status:** Half-built — portfolio fetcher runs, but not consumed.

### 5. MA_COMPS
- **What it is:** M&A comparison benchmarks.
- **Fix:** Parse `press_releases_filtered.json` + `sec_filings_auto.js` + `news_raw.json` for M&A language, extract deal size + revenue multiple, emit `data/ma_comps_auto.json`.
- **Recommended:** `scripts/extract_ma_comps.py` — keyword-driven (acquired, acquisition, merger, multiple of revenue, all-stock).

### 6. LIVE_AWARD_FEED
- **What it is:** Duplicate of GOV_CONTRACTS.
- **Fix:** Delete (or point to GOV_CONTRACTS via getter). Legacy cruft.

---

## ⚠️ STATIC — MEDIUM RISK (13 arrays)

These are structural features or have pipelines already in place but unwired.

| Array | Proposed Fix | Status |
|---|---|---|
| FOUNDER_MAFIAS | Parse `founder` strings across COMPANIES, cluster by prior-company keyword (ex-SpaceX → SpaceX Mafia). | Need `calc_founder_mafias.py` |
| VC_FIRMS | Wire `fetch_vc_portfolios.py` output (already runs!) into `VC_FIRMS` via merge_data. | Half-built |
| NETWORK_GRAPH | Build edges from `competitors` + `founder` fields in COMPANIES. | Need `calc_network_graph.py` |
| ECOSYSTEM_NETWORK | Same as above. | Need script |
| PRODUCT_LAUNCHES | Wire existing `fetch_product_hunt.py` + `fetch_github_releases.py`. | Scripts exist but not wired |
| GOV_DEMAND_TRACKER | Already have `fetch_demand_signals.py`; just needs merge_data wiring. | Half-built |
| GOV_DEMAND_SUMMARY | Derive from GOV_DEMAND_TRACKER aggregation. | Need a calc step |
| CONTRACTOR_READINESS | Derive from gov contracts + headcount + clearances. | Can auto-compute |
| DEAL_FLOW_SIGNALS | Has scripts; wire into weekly sync. | Half-built |
| ALT_DATA_SIGNALS | Hook into jobs + stocks + news deltas. | Half-built |
| STORY_LEADS | Journalism lead tracker. | Keep manual (editorial choice) |
| PLATFORM_STATS | Pull from Google Analytics or Supabase if integrated. | Needs analytics integration |
| ALERTS_SYSTEM | Rules engine — can auto-trigger from live events. | Needs a processor |

---

## ✅ INTENTIONALLY STATIC (21 arrays)

These *should* be manual by design. Don't change them.

- **FOUNDER_CONNECTIONS** — Stephen's personally-met-founder tracker (the ROS moat)
- **COMMUNITY_EVENTS, SLACK_CHANNELS, COMMUNITY_TIERS** — your community setup
- **WATCHLIST_COLUMNS, SCREENER_FILTERS, AI_SEARCH_SUGGESTIONS, COMMAND_BAR_ACTIONS** — UI config
- **SECTORS, SIGNAL_TYPES, VALLEY_OF_DEATH_STAGES** — taxonomies
- **TRL_METHODOLOGY, TRL_DEFINITIONS, GROWTH_SIGNAL_METHODOLOGY, INNOVATOR_SCORE_METHODOLOGY, SECTOR_MOMENTUM_METHODOLOGY, ALT_DATA_METHODOLOGY, DATA_SOURCES** — methodology documentation
- **COMPANIES** — the 868-company universe (partially auto, but curation stays human)
- **LAST_UPDATED, PREV_WEEK_SCORES** — automatically updated metadata

---

## 🔴 CRITICAL CONFLICT — Fix in this commit

Two pipelines are currently fighting over `INNOVATOR_SCORES`:

1. **`daily-data-sync` (6am UTC daily)** → `calc_innovator_scores.py` writes `data/innovator_scores_auto.json` (thin schema) → `merge_data.py` rewrites the array in `data.js`, losing insight-rich notes
2. **`weekly-intelligence-sync` (Sun 8am UTC)** → `sync_weekly_metrics.py` writes insight-rich, delta-applied scores directly to `data.js`

Outcome: every Monday through Saturday morning, daily-sync wipes out the Sunday sync's richer notes.

**Fix shipped in this commit:** `merge_data.py` now skips the `INNOVATOR_SCORES` rewrite — the weekly sync is the single source of truth for that array. The thin auto-json still generates for back-compat consumers.

The same conflict could affect `GROWTH_SIGNALS`, `HEADCOUNT_ESTIMATES`, `DEAL_TRACKER`, `REVENUE_INTEL`, `FUNDING_TRACKER`, `VALUATION_BENCHMARKS`, `SECTOR_MOMENTUM` — but for those, the auto-json IS the intended source of truth and manual curation is minimal, so daily overwrite is correct.

---

## 📋 Suggested action plan (prioritized)

### Immediate (this commit)
1. ✅ Stop `merge_data.py` from overwriting `INNOVATOR_SCORES`.
2. ✅ Write this audit document.

### Next 1-2 weeks (new tiny scripts)
3. Build `scripts/fetch_substack_posts.py` → fixes FIELD_NOTES.
4. Wire `fetch_product_hunt.py` + `fetch_github_releases.py` → PRODUCT_LAUNCHES.
5. Wire `fetch_demand_signals.py` → GOV_DEMAND_TRACKER / GOV_DEMAND_SUMMARY.
6. Wire `fetch_vc_portfolios.py` → VC_FIRMS / FUND_INTELLIGENCE.

### Next month (new calc scripts)
7. `scripts/calc_budget_signals.py` → BUDGET_SIGNALS.
8. `scripts/calc_founder_mafias.py` → FOUNDER_MAFIAS + NETWORK_GRAPH + ECOSYSTEM_NETWORK.
9. `scripts/extract_ma_comps.py` → MA_COMPS.
10. Delete LIVE_AWARD_FEED (duplicate).

### Later (larger scope)
11. Analytics integration → PLATFORM_STATS.
12. Rules engine → ALERTS_SYSTEM.

---

**Audit generated by Claude (Round 7k) — saved to `/STATIC_FEATURES_AUDIT.md` for future reference. Run `python scripts/sync_weekly_metrics.py` anytime to regenerate the weekly digest.**
