# Full Platform Review — The Innovators League
**April 17, 2026** · Multi-dimensional audit + enhancement plan

Five parallel audits were run: functional health, data pipeline status, UX/UI, per-feature enhancement, net-new feature ideation. This document is the synthesis with a prioritized action plan at the end.

---

## Executive Summary

**The good:** All 26 pages return HTTP 200. All JS parses cleanly (zero syntax errors). The site has 6 uniquely differentiated features no competitor offers (Spinout Radar, Launch Manifest, Clinical Trials Radar, NRC Licensing, Gov Grant Flow, Defense Prime Supply Chain). Core data pipelines (SEC EDGAR, SAM.gov, USPTO patents, Yahoo Finance, arXiv, NIH, NSF, NASA, clinical trials, federal register) are running and producing fresh data daily.

**The bad:** Four still-broken `dealflow.html` references (one user-facing, three inside `app.js`) produce 404s on click. Five data pipelines are effectively dead (jobs 59d stale, FDA 59d, insider transactions 56d, IPO pipeline 53d, GitHub releases 46d). Two "active" pipelines produce fake-looking data (Twitter: all 100 records are placeholders; LinkedIn headcount: all 564 are seed). The `merge_all_data` step in the main comprehensive sync has been silently failing since April 15 — which is also why the `data_health*.json` dashboards haven't refreshed. Anthropic API key is set but the account has $0 credit, blocking both the earnings LLM extraction and the funding RSS extraction.

**The strategic:** Beyond the baseline fixes, we identified **23 net-new feature ideas** that would materially widen the moat. Top 3 by ROI × effort: Primary-Source Changelog Engine (3 weeks, locks in analyst workflows), First-Customer Tracker (alpha-grade signal nobody else has), Slack Frontier Bot (intercepts where VCs actually talk).

---

## 🚨 Launch Blockers (fix before enterprise demos)

### Functional blockers

| # | File / location | Issue | Fix |
|---|---|---|---|
| 1 | `valuations.html:253` | "Deal Flow Signals & Pipeline" cross-link points to archived `dealflow.html` → 404 | Replace with link to `transformation.html` or remove the cross-link card |
| 2 | `app.js:1470` | "Deal Flow" button inside the company modal (global, fires from every company card on every page) → 404 | Remove the button; replace with "Tear Sheet" or "View on Investor Screener" (link to dealflow archive removed) |
| 3 | `app.js:1689` | Cmd-K command-bar search entry for "Deal Flow" → 404 | Remove entry |
| 4 | `app.js:1957` | `G → D` keyboard shortcut routes to Deal Flow → 404 | Remove handler (line 1924 also advertises the chord in the help overlay) |
| 5 | `index.html:90` | Section-nav dot tooltip still says `title="Portfolio & War Room"` | Change to `title="Portfolio"` |

### Data pipeline blockers

| # | Pipeline | Status | Fix |
|---|---|---|---|
| 6 | **Jobs feed** — `jobs_raw.json`, `jobs_auto.js` | **59 days stale** (last 2026-02-17). Site claims "updated every 6h" on jobs.html | Either (a) add a visible "Last updated Feb 17" badge, or (b) debug `fetch_jobs.py` (stocks side works, so not an env/secret issue) |
| 7 | **Anthropic LLM extraction** — earnings signals + funding feed | $0 credit → every API call returns 400 → `funding_feed_auto.json` is empty `[]`; earnings extraction returns 22 seed-only | Add credits at [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing) |
| 8 | **Apify cap exhausted** — `twitter_signals_auto.json` | All 100 records are placeholders. 20 HTTP 403 "Monthly usage hard limit exceeded". Site displays fake-looking signals. | Top up Apify account, or hide Twitter signals on the UI until restored |
| 9 | **`merge_all_data` failing silently** | `data_health*.json` frozen at 2026-04-15 because the tail "commit health summary" step fails | Debug workflow step or remove if unneeded |

### Trust blockers (enterprise-visible)

| # | Issue | Where | Fix |
|---|---|---|---|
| 10 | Auth modal "Terms of Service" + "Privacy Policy" are plain text, not links | Global | Make them `<a>` tags to `/terms.html` + `/privacy.html`. Legal compliance red flag for any enterprise procurement review |
| 11 | No Pricing entry in global nav | All 26 pages | Pricing is buried at bottom of homepage. Add "Pricing" to nav or add a right-side `Join Pro` button next to Sign In |
| 12 | No site-wide footer on `company.html` | Company profile pages | Copy the premium footer block from `index.html` — company.html is the highest-traffic page type |
| 13 | "50,000+ investors and founders" claim appears on 23 pages unsubstantiated | Global | If it's the ROS Substack reach, scope it to "50,000+ Substack subscribers" |
| 14 | `visualizations.html:78` shows literal text `"— loading..."` before JS runs | Hero subtitle | Remove the dangling `— loading...` from initial HTML |

---

## ⚠️ Warnings (should-fix — non-blocking but degrade experience)

### Stale / degraded data pipelines (not total failures, but not current)

| File | Last updated | Severity | Cause |
|---|---|---|---|
| `fda_actions_raw.json` | 59d stale | 🟡 High | Orphaned — not in any workflow |
| `insider_transactions_raw.json` | 56d stale | 🟡 High | Orphaned — not in any workflow |
| `ipo_pipeline_auto.json` | 53d stale | 🟡 Med | Orphaned — not in any workflow |
| `github_releases_raw.json` | 46d stale | 🟡 Med | Orphaned — not in any workflow |
| `product_launches_raw.json` (ProductHunt) | 4d stale | 🟡 Low | `weekly-extended-sync.yml` last run failed |
| `linkedin_headcount_auto.json` | All 564 seed | 🟡 Med | `apify_enabled: false` hard-coded in script |
| `secondary_market_auto.json` | Mostly seed | 🟡 Low | Forge + EquityZen scrapers returning 404 |
| `conference_presence_auto.json` | Mostly seed | 🟡 Low | 6/9 conference URLs rolled to 2027 |
| `congress_bills_auto.json` vs `.js` | JS fresh, JSON 57d stale | 🟡 Med | Dangerous — JS wrapper updates but content is stale |
| `sbir_topics_auto.json` vs `.js` | Same pattern | 🟡 Med | Same as above |
| `sbir_awards_raw.json` | Placeholder only | 🟡 High | 3 SBIR endpoints all failing (the 31 awards in `*_auto.json` are from curated seed only) |
| `diffbot_enrichment_raw.json` | `uninitialized` | 🟡 Low | Script reset itself and never repopulated |

### JS warnings

- `data/sbir_awards_auto.js` is `const SBIR_AWARDS_AUTO = [];` (empty) while `data/sbir_awards_auto.json` has 31 records — the JS-generation step is using a different/empty source. Any UI reading `SBIR_AWARDS_AUTO` shows an empty state even though data exists.
- `data/news_signals_auto.js` contains 20 signals but only 2 are `impact: "high"`. The ticker filters to HIGH-only, so only 2 items auto-scroll — visually thin. Either relax the filter to HIGH+MEDIUM or surface "quiet day" messaging.

### Copy / UX / Nav

- "Updated every 6 hours" claim on jobs.html contradicts 59-day-stale data (trust killer).
- Transformation subpage nav includes "Transformation" twice (top-level active link + in Database dropdown). Intentional hub-breadcrumb, but visually duplicate.
- `alerts.html` uses `.alerts-hero` class instead of shared `.hero` — visually inconsistent with siblings.
- Emoji used heavily across sections (`📊 💼 🧬 👑 🔥`). For enterprise buyers, replace with monochrome SVGs. One afternoon of work; biggest polish-per-hour investment.
- Action bar on company profile has 7 buttons; collapse to 4 (Save, Share ▾, Compare, Download Tear Sheet). "Share Profile" + "Share on X" are redundant. "Intel Brief" vs "Download Tear Sheet" is confusing.
- Hardcoded time windows everywhere: hiring chart months ("Aug", "Sep", …, "Jan") at `company-profile.js:423`; Sector Momentum says "Q1 funding" but should roll to "Last 90 days".

### Mobile issues

- Only 21 `@media` rules in a 376 KB stylesheet. Many layouts will break below 375px.
- `.nav-search` is hidden on mobile but not replaced with an alternative → global search unreachable on mobile.
- Jobs page has 8 filter tags + 4 dropdowns + search — will overflow horizontally below 640px.
- Tables (valuations, investors, captable, earnings-signals) have no `overflow-x: auto` wrapper → likely break viewport on mobile.
- Touch targets (`.filter-tag`, `.alert-filter`) have no explicit `min-height: 44px`.

---

## ✅ Verified Working (high-confidence list)

- **HTTP 200 on all 26 pages** (live site)
- **All JS parses cleanly** (tree-sitter ES2022, zero syntax errors)
- **All internal links + anchors + script/stylesheet refs resolve** (zero 404s apart from the 4 `dealflow.html` cases flagged above)
- **Nav consistency:** every page has Intelligence · Insights · Frontier Daily · Database dropdown · More dropdown (Company profile now matches after the fix)
- **Footer:** no `dealflow.html` references in any footer
- **Authoritative pipelines:** SEC EDGAR (1,049 filings), SAM.gov (123 contracts), USPTO (37 companies, weekly refresh), Yahoo Finance (stocks live), arXiv (300 papers), NIH Reporter (626 grants), NSF (135 awards), ARPA-E (300 projects), NASA TechPort (150 projects), federalregister.gov (87 rules), clinicaltrials.gov (297 trials)
- **Flagship features working:** Sector Explorer drilldown, Company Profile with PDF Tear Sheet, Patents velocity leaderboard, Launches manifest, Earnings Signals grid, all 4 Industry Transformation pages, Frontier Daily digest with Stephen's Take callout
- **All 152 valuation benchmarks** with source attribution
- **22 verified earnings signals** (all with real source URLs to Motley Fool/Benzinga transcripts)
- **37 companies in patent velocity leaderboard** with 8Q sparklines
- **50 upcoming launches** tracked
- **285 executive moves** parsed from SEC EDGAR
- **43 university spinouts**

---

## 🔧 Data Pipeline Scorecard

### 🟢 Healthy (fresh + real — safe to feature)
SEC filings, SAM.gov, USPTO patents, Yahoo stocks, arXiv, NIH Reporter, NSF Awards, ARPA-E, NASA TechPort, federal register, clinical trials, gov contracts, earnings transcripts (31 records), news signals (20), press releases (40 raw/23 filtered), HN buzz (53), trade data (20), federal grants (347 aggregated), deals (148), executive moves (285), federal register monitor (87), spinouts (43), launches (50), NRC licensing (15), prime supply chain (9), revenue intel (56), growth signals (78), innovator scores (805), predictive scores (4 models), demand signals (44), patent velocity (37), valuation benchmarks (152), headcount estimates (87), sector momentum (16), GitHub signals (37), podcast mentions (315), discovered companies (13), DOE programs (12), funding tracker (86).

### 🟡 Degraded (working but partial)
- `funding_feed_auto.json` — `[]` empty despite 129 RSS items pulled; extraction layer broken (Anthropic $0 credit)
- `twitter_signals_auto.json` — 100 records, all placeholders (Apify cap hit)
- `linkedin_headcount_auto.json` — 564 seed-only records
- `secondary_market_auto.json` — mostly seed (3/4 sources 404)
- `conference_presence_auto.json` — mostly seed (stale conference URLs)
- `sbir_awards_auto.json` — 31 seed-only records (APIs all failing)
- `diffbot_enrichment_raw.json` — 180B stub, `uninitialized`

### 🔴 Broken / dead
- `jobs_auto.js` / `jobs_raw.json` — 59 days stale
- `fda_actions_raw.json` — 59 days stale (orphaned)
- `insider_transactions_raw.json` — 56 days stale (orphaned)
- `sbir_topics_auto.json` — JSON 57 days stale while JS refreshes
- `congress_bills_auto.json` — JSON 57 days stale while JS refreshes
- `ipo_pipeline_auto.json` — 53 days stale (orphaned)
- `github_releases_raw.json` — 46 days stale (orphaned)

### ⚙️ Workflow health (from file mtimes + in-repo health snapshots)
| Workflow | Status | Last successful run |
|---|---|---|
| `hourly-news-sync.yml` | 🟢 Healthy | 2026-04-16 15:51 UTC |
| `daily-data-sync.yml` | 🟢 Healthy | 2026-04-16 12:51 |
| `jobs-stocks-sync.yml` | 🟡 Degraded | Stocks fresh, Jobs 59d stale |
| `comprehensive-data-sync.yml` | 🟡 Degraded | 24/25 steps succeed; `merge_all_data` failing in CI |
| `weekly-patent-sync.yml` | 🟢 Healthy | 2026-04-15 |
| `weekly-extended-sync.yml` | 🟡 Degraded | ProductHunt 4d stale |
| `weekly-brief.yml` | 🟢 Healthy | 2026-04-15 |

### 💰 API keys (from workflow env refs)
| Secret | Status | Used by |
|---|---|---|
| `ANTHROPIC_API_KEY` | 🔴 Set but $0 credit | `extract_earnings_signals.py`, `fetch_funding_rss.py` |
| `APIFY_TOKEN` | 🔴 Monthly cap exhausted | `fetch_twitter_signals.py`, `fetch_linkedin_headcount.py` |
| `EARNINGS_API_KEY` | 🟢 Working | `fetch_earnings_transcripts.py` |
| `PATENTSVIEW_API_KEY` | 🟢 Working | `fetch_patents.py` |
| `GITHUB_TOKEN` | 🟢 Working | `fetch_github_signals.py`, commits |
| `SAM_API_KEY` | 🟢 Working | `fetch_sam_contracts.py` |
| `CENSUS_API_KEY` | 🟢 Working | `fetch_census_trade.py` |
| `EIA_API_KEY` | 🟢 Working | `fetch_doe_energy.py` |
| `DATA_GOV_API_KEY` | 🟢 Working | multiple |
| `CONGRESS_API_KEY` | 🟡 Suspect | `fetch_congress_bills.py` (JSON stale) |
| `PRODUCTHUNT_API_TOKEN` | 🟡 Suspect | `fetch_product_hunt.py` (4d stale) |
| `DIFFBOT_API_TOKEN` | 🟡 Unknown | `fetch_diffbot_enrichment.py` (output empty) |

---

## 🎨 UX/UI Improvements (prioritized)

### Quick wins (one afternoon each)
1. Replace emoji in chrome (section headers, hero CTAs, pricing tier icons) with monochrome SVGs — single biggest polish-per-hour investment
2. Add site-wide footer to `company.html` (copy block from `index.html:1044+`)
3. Restore full footer on `earnings-signals.html`, `launches.html`, `patents.html`
4. Add a visible "Last updated: Feb 17" badge to jobs.html hero (turns trust liability into recency signal)
5. Add "Pricing" to global nav primary links or as right-side CTA
6. Make auth modal Terms / Privacy actual `<a>` links
7. De-dupe the IL30 "Nominate a Company" button
8. Remove the literal `— loading...` from `visualizations.html:78`
9. Swap hardcoded months in hiring chart (`company-profile.js:423`) with rolling 12-month window
10. Add sticky mobile CSS for `.section-nav` (hide below 900px or collapse to bottom FAB)

### Strategic UX upgrades
- **Redesigned homepage hero for enterprise buyers** — credibility strip (logo wall if exists) + "institutional intelligence platform for frontier tech" headline + 3 concrete deliverables + dual CTA (Request Demo + Browse Database)
- **Company profile tear-sheet restructure** — Bloomberg/Capital IQ use **tabs** (Overview · Traction · Competition · Intelligence · Markets · People) instead of endless vertical scroll. Sticky header: `Company · Stage · Sector · Frontier Index`
- **Pricing page as its own route** — spin `/pricing.html` out of the homepage with comparison table + FAQ + named customer quotes
- **Data room trust page** — `/methodology.html` lists every data source with cadence, coverage stats, team bios, audit PDF. Link from every footer.
- **Mobile nav rework** — keep search accessible below nav bar on mobile, collapse Intelligence/Insights/Frontier Daily into mega-menu, fixed bottom CTA bar
- **Freshness-as-feature** — every data page shows prominent "Last updated" badge; add a `/status` page showing source-by-source pipeline health

---

## 📈 Feature Enhancements (top picks per feature)

The per-feature review produced **200+ specific upgrade recommendations** across the 14 major features. Highlights below — full list in the expandable details section.

### Highest-leverage enhancements (<1 week each)

- **Company Database** — Active-filter chip tray (applied filters as removable chips above results) + numeric range sliders for Total Raised / Valuation / Headcount / Founded Year
- **News Ticker** — Make headlines clickable + show source chip + pause-on-hover + fallback to show MEDIUM when no HIGH items exist
- **Innovation Map** — Swap markers for MarkerClusterGroup (Leaflet addon already loaded on another page); add heatmap toggle
- **IL30 Showcase** — Expose YoY movement arrows on grid cards (data already in `yoyChange`); hover-tooltip "Why ranked #N"
- **Frontier Index** — Sort by individual dimension (not just composite); "Biggest Movers This Week" banner
- **Sector Momentum** — Expand row on click → 5-factor breakdown; 3-month sparkline per sector
- **Company Profile** — Pinned recent-signal strip below hero ("Last 7 days: +$50M Series D · 1 patent · 12 hires"); replace hiring chart hardcoded months with rolling window; reduce 7-button action bar to 4
- **Sector Explorer** — Sortable table view alongside grid; sector-vs-sector comparison mode
- **Valuations** — "Overvalued / Undervalued" toggle pre-applies `initOverUnder` as quick filter; percentile rank per row
- **Patents** — Forward-citation count as quality metric; CPC-code filtering; inventor-network cross-link
- **Earnings Signals** — "Mention streak" badge ("3Q in a row"); sentiment tagging (partner/threat); click → 200-word context before/after
- **Frontier Daily** — Archive by date (`/brief?date=...`); email subscription (biggest growth lever)
- **Gov Radar** — Top sticky "What's new since your last visit" strip; cross-section global sector filter; contract deadline countdown cards
- **Talent** — Company talent-density composite score; "Bleeding vs hiring" net-flow indicator per company

### Higher-effort strategic enhancements (1-3 weeks each)

- Primary-Source Changelog Engine — version-history diff view for every entity (see net-new feature #1 below)
- Saved searches with delta alerts ("12 new companies since you last ran this search")
- Cross-filtering across all Insights visualizations (click country → all charts update)
- Compare up to 3 companies with overlaid radar chart (reuse existing `renderRadarChart`)
- Portfolio Builder weighted positions + scenario comparison matrix
- Transformation pages: interactive stack clicks → layer detail; capital flow as Sankey

---

## 🚀 Net-New Feature Ideas (23 concepts, top 10 ranked)

Full ideation covered 12 strategic dimensions. Top 10 by ROI × effort:

| Rank | Idea | Effort | Monetization |
|---|---|---|---|
| **1** | **Primary-Source Changelog Engine** — "Git for the real world" — every entity has a timestamped diff view of what changed in SEC/USPTO/SAM.gov/NRC | 3-4w | Pro + Team |
| **2** | **First-Customer Tracker** — feed of companies winning their first marquee customer (first DoD, first airline, first utility, first hospital) | 2-3w | Pro + Enterprise |
| **3** | **Earnings Call Mention Auto-Extractor** — extension of existing earnings pipeline; flag when Fortune 500 CEOs name private frontier cos | 2-3w | Pro + Team |
| **4** | **Slack/Teams Frontier Bot** — paste URL/name, get tear sheet card. Intercepts VC Slack conversations in the moment | 2w | Team + Enterprise |
| **5** | **Frontier 100 Power List** — semi-annual authoritative ranking with transparent methodology. Brand-defining | 4w/issue | Free (SEO) + sponsored |
| **6** | **Regulatory Calendar Master Timeline** — unified FDA/NRC/FAA/FCC/DoD calendar per tracked company | 3-4w | Pro + Team + Enterprise |
| **7** | **Sovereign-Capital Flow Index** — track Mubadala/ADIO/PIF/Temasek/GIC/NBIM commitments into frontier tech. Uniquely differentiated via ADIO/SAVI | 5-6w | Enterprise + Ecosystem |
| **8** | **Export-Import Customs Data Layer** — US Census Trade / Import Genius filtered for frontier hardware (SMR components, cryo equipment, lithography). Hedge-fund gold | 4-5w | Enterprise |
| **9** | **Founder-Investor Handshake Graph** — shortest warm-path from any founder to any VC partner, built from SEC filings + 13G/13D + proxy statements | 4-5w | Pro + Team + Enterprise |
| **10** | **Anonymous Frontier Founder Benchmarks** — verified-founder submissions create sector-specific operating metric benchmarks (Carta for frontier operating metrics) | 4-5w | Free to contributors, paid to viewers |

### Second tier (genuinely valuable, slower payoff)
- Ask-an-Analyst AI mode (vertical-specific personas, retrieval-augmented, refuses ungrounded queries)
- TRL Graduation Tracker (systematic mapping of every company to TRL 1-9)
- DoD Budget PE Code Tracker (drills one level below the bill-level tracker)
- Deal Notebooks (Notion-style memos with live source-linked chips — Excel plugin equivalent for prose)
- Frontier Tech Secondaries Board (Forge/EquityZen/Hiive aggregated with frontier filter)

### Deferred (high value but legal/data/entity-resolution complexity)
- Co-Investment Opportunity Board (needs securities counsel + accredited-investor gating)
- Scientific Co-Authorship Graph → commercial translation (entity resolution is hard)
- ITAR/EAR Export License Tracker (FOIA-heavy, redaction-bound)
- LP Capital Flow Map (scattered across 10+ disclosure regimes)
- NOTAM / Spectrum License / NOTMAR Map (high noise-to-signal)

---

## 🎯 Prioritized Action Plan

### This week (launch-critical)

1. **Fix the 5 `dealflow.html` references** — 2 hours, prevents 404s on customer click-through
2. **Remove "War Room" tooltip** from `index.html:90` — 1 minute
3. **Fund the Anthropic API** ($20-50) — unlocks earnings + funding LLM extraction
4. **Pause the Apify Twitter signals output** in the UI until billing resolved, or hide it — customers will notice placeholder data
5. **Add a visible "Last updated: Feb 17" badge** to jobs.html hero — turns trust problem into transparency
6. **Make auth modal T&P actual links** — legal compliance
7. **Add Pricing to global nav** — enterprise discovery path
8. **Add site-wide footer to `company.html`** — highest-traffic page needs bottom nav
9. **Debug `merge_all_data` CI step** — unfreezes the data-health dashboard (customers will look at this)

### Next 2-4 weeks (polish + workflow hardening)

10. Replace emoji in chrome with SVG icons — tone shift from "startup" to "enterprise"
11. Rolling 12-month hiring chart (remove hardcoded months)
12. Investigate 4 orphaned pipelines (jobs, fda_actions, insider_transactions, ipo_pipeline, github_releases) — either add them back to a workflow or retire their frontend references
13. Fix `sbir_awards_auto.js` / `congress_bills_auto.js` / `sbir_topics_auto.js` JS-vs-JSON drift
14. Build the mobile-responsive CSS pass (add `overflow-x:auto` to all tables, collapse section-nav below 900px, make jobs filter bar scroll)
15. Ship saved-search delta alerts ("12 new companies since last run")
16. Ship Company Database active-filter chip tray + numeric range sliders
17. Ship Innovation Map clustering via `leaflet.markercluster`
18. Ship "Biggest Movers This Week" banner on Frontier Index
19. Build `/methodology.html` data-room page + link from every footer

### 30-60 days (net-new moat features)

20. **Build the Primary-Source Changelog Engine** (Idea #1) — highest-ROI net-new feature because it repackages data already owned
21. **Build the First-Customer Tracker** (Idea #2) — alpha-grade signal, 2-3 weeks using existing pipelines
22. **Ship the Slack Frontier Bot** (Idea #4) — trivial extension once tear-sheet API exists
23. **Publish the first "Frontier 100" Power List** (Idea #5) — brand-compounding, 4-week project

### 60-180 days (strategic bets)

24. **Sovereign-Capital Flow Index** (Idea #7) — plug into ADIO/SAVI relationship for a six-figure Ecosystem Platform contract
25. **Export-Import Customs Layer** (Idea #8) — opens hedge-fund customer segment
26. **Founder-Investor Handshake Graph** (Idea #9) — deepens existing network graph
27. **Tear-sheet tab restructure** — Bloomberg-style tabs on company profile
28. **Thematic Primer Library** (from the existing Blueprint) — 10 primers in 5 months = new ACV tier

### Ongoing (discipline items)

- Every new data source must have primary-source attribution on every rendered datapoint
- Every new table gets CSV export
- Every new pipeline gets a `_status.json` health artifact that writes to the data-health dashboard
- Every page gets a "Last updated" badge
- No curated-seed data ships to production without a visible "ROS research" label

---

## Closing

**Summary:** The platform is in good functional shape. The gap to enterprise-grade is ~5 launch-blocker fixes + ~2 weeks of polish + $50 of Anthropic credits. Beyond that, the competitive blueprint and the 23 net-new ideas above give a clear 12-month roadmap to a moat nobody else in the market can build.

**Biggest strategic insight from the review:** Every competitor (PitchBook, CB Insights, Preqin, Bloomberg, Dealroom, Crunchbase, Capital IQ) is an inch deep across 11M generic companies. Our 1,000 frontier-tech companies are covered a mile deep with authoritative sources. That structural asymmetry is the moat; every feature on the roadmap should either deepen that coverage or convert it into subscriber / LP / SWF value.

---

**Review generated by:** 5 parallel audit agents (functional, data-pipeline, UX/UI, feature-enhancement, net-new-ideation) + synthesis
**Commit reference:** `4b4b169` (as of audit start; fixes forthcoming)
**Next review suggested:** After shipping the Week-1 action items
