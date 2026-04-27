# Investor Tools Strategic Roadmap

_The 25 highest-value features ROS can ship to make Innovators League indispensable for both private and public market investors. Ranked by uniqueness × usefulness × feasibility._

_Generated April 2026. ~5,000 words._

---

## Part 1 — The vision

Bloomberg Terminal sells $25,000/year because it answers two questions faster than any alternative:

1. **"What's the smart money doing?"** (positions, flows, insider moves)
2. **"What just happened or is about to happen?"** (real-time signals, calendars, alerts)

For frontier tech investors specifically, those two questions become:

1. **"Who's invested in what — and what are they doing now?"**
2. **"Which companies are raising, when, at what price, and from whom?"**

Stephen named both of these directly. They're the right priorities because the rest of investor decision-making (sizing, pricing, exit timing, sourcing) all depends on having those two truths cold.

We already have raw material: 869 companies, ~50 named VCs in `VC_FIRMS`, Form D filings, news RSS, insider trades, public filings. **The opportunity is the synthesis layer.** Most investor tools available today are either:
- **Wide but shallow** (Crunchbase, PitchBook — every company, but identical depth and no edge)
- **Narrow but deep** (sector reports, individual analyst notes — great content, no real-time data)
- **Public-market only** (Bloomberg, FactSet — no private market signal)

There is no tool that combines **frontier-tech depth** + **real-time signal** + **public + private market unification**. That gap is ours.

---

## Part 2 — Evaluation framework

Every proposed tool below is scored on three dimensions, each 1–5:

| Dim | Test |
|---|---|
| **Uniqueness** | Could a member get this somewhere else for $0? If yes, low score. |
| **Usefulness** | Does it change a real decision (invest / pass / size / sell)? |
| **Feasibility** | Can we build it with public APIs + scraping + our existing data, in <30 days? |

Composite score = sum (max 15). Anything ≥ 12 is must-build.

I'll mark each tool with this score plus a 1-line "kill the deal" question — the single biggest reason it might fail.

---

## Part 3 — Funding Intelligence (Tier 1A)

_Direct answer to "when are companies raising money."_

### 1. Unified Funding Pulse ★★★★★ (15/15)

**What it is**: ONE chronological feed combining every funding signal we can detect — Form D, news RSS, AngelList LP updates, 8-K Item 1.01 disclosures, founder tweets, LP Substack mentions. Sortable by company, stage, sector, recency, and ROS-relevance.

**Why it matters**: Today these signals are scattered across `signals.html`, news feed, and `data/form_d_filings_auto.json`. A member checking "is anyone raising in fusion right now?" has to manually correlate. Unification = 10x faster decision.

**Data sources**:
- ✅ Already have: SEC Form D (60-day lookback), news RSS, press releases
- 🆕 Add: AngelList Pro LP newsletter scrape, Substack scan ("we just led/co-led/participated"), 8-K Item 1.01 parsing
- 🆕 Add: Twitter/X scrape of frontier-tech founder accounts (when API allows)

**Kill the deal**: Twitter/X API costs are real ($200/month for basic). AngelList ToS may block automated LP newsletter scraping. → Build with what's free first; add paid tiers as ROI proves out.

**Build plan**: New `funding-pulse.html` page + `scripts/aggregate_funding_signals.py` that merges 6 sources into a unified `data/funding_pulse_auto.json`. Filterable by sector / stage / check-size match.

---

### 2. Active Raise Calendar ★★★★★ (14/15)

**What it is**: Companies known to be raising RIGHT NOW with: target close date (estimated), round size, lead investor (rumored or confirmed), check-size match for ROS Fund. Like a wedding RSVP list for capital deployment.

**Why it matters**: Direct deal-flow tool. ROS Fund needs to know: "of the 50 companies actively raising in the next 90 days, which 5 fit our $100-250K check size and our thesis?" One screen, sorted by close date.

**Data sources**:
- ✅ Form D (filed within 15 days of first sale → still raising)
- ✅ News RSS pattern detection ("raising", "pre-empted", "term sheet")
- 🆕 Pitchbook-style estimated close dates via NLP on news headlines
- 🆕 ROS Fund check-size filter applied automatically

**Kill the deal**: Some rounds close pre-announcement, never appearing in any public source. → Acceptable; we capture the 70% that DO leak.

**Build plan**: Calendar view (week / month) of upcoming closes. Each card: company name, sector, round size, check-fit color (green = perfect for $100-250K, amber = stretch, red = too big), days-to-estimated-close.

---

### 3. Pre-Form-D Leak Detector ★★★★★ (13/15)

**What it is**: An alert that fires when a company is raising but hasn't yet filed Form D. Trigger sources: founder LinkedIn updates, LP newsletter mentions ("we co-led"), Twitter announcements, AngelList syndicate notices. Always 2-6 weeks ahead of Form D.

**Why it matters**: This is the single highest-leverage signal an investor can have. By the time Form D appears, the lead is set, terms are drafting, and there's typically only allocation left. A pre-Form-D signal is intro / pitch / SPV territory.

**Data sources**:
- 🆕 Watch ~200 LP-newsletter Substacks weekly for "we led / participated" language
- 🆕 Track ~500 frontier-tech founder Twitter handles for "thrilled to announce" patterns
- 🆕 Cross-reference with subsequent Form D filings to compute lead time

**Kill the deal**: Twitter API is the bottleneck. Substack scraping of LP newsletters is allowed (RSS available). → Start with LP newsletter scan only; expand to Twitter when API budget approved.

**Build plan**: `scripts/fetch_lp_newsletters.py` that pulls 200 RSS feeds + extracts company-mention NER. Output: `data/pre_form_d_leaks_auto.json`. Surface on Funding Pulse page as "leaked but unfiled" tier.

---

### 4. Round Cadence + Due-Date Tracker ★★★★ (12/15)

**What it is**: For every private company we track, predict when they'll raise their next round based on: last round date + size + headcount growth + Form D recency + sector burn-rate norms. Surface "due-to-raise" companies 30-90 days before they hit the market.

**Why it matters**: Cold outreach 60 days before a company is actively pitching = warm intro by the time term sheets fly. ROS Fund's competitive advantage is being early; this tool puts you 60 days earlier.

**Data sources**:
- ✅ COMPANIES has `fundingStage`, `totalRaised`, `founded`
- ✅ We have headcount estimates + LinkedIn growth from Apify
- 🆕 Sector burn-rate model (defense vs SaaS vs fusion all burn differently)
- 🆕 Bayesian prior on round cadence per stage

**Kill the deal**: Burn rate is hard to estimate without access to bank statements. → Use proxies: headcount × sector-median-comp + office lease + Form D cadence.

---

### 5. Down-Round / Flat-Round Detector ★★★★ (12/15)

**What it is**: Flag any round where reported valuation is flat or down vs prior round. Combined with insider language analysis (deception detector signals on the same companies in the same week), produces a high-confidence "trouble" badge.

**Why it matters**: Down rounds are the canary for fund returns. Most VC reports lag this by 6 months. We can surface in real time.

**Data sources**:
- ✅ COMPANIES already has `valuation` field
- ✅ Form D has offering amount (rough size)
- 🆕 Newsroom NLP for "$X valuation" mentions
- 🆕 Cross-reference with deception detector for layered signal

**Kill the deal**: Companies hide down rounds (extension rounds at "structure"). → Flag suspicious patterns: extension rounds + executive departures + ditched OKRs.

---

## Part 4 — Investor Intelligence (Tier 1B)

_Direct answer to "who's invested in what."_

### 6. Per-Investor Portfolio Deep Pages ★★★★★ (15/15)

**What it is**: For every fund in `VC_FIRMS` (~50 today, easily expandable to 200), a dedicated page showing: full portfolio, sector breakdown, stage breakdown, geographic mix, fund vintage(s), recent additions, recent exits, partner-level attribution, thesis cluster overlap with ROS, co-investors most often syndicated with.

**Why it matters**: Today our `investors.html` lists firms in a directory format. Bloomberg-tier coverage means: click on Founders Fund, see EVERY frontier-tech company they've backed mapped against the ROS database, with sector chart + recency timeline + recent activity.

**Data sources**:
- ✅ VC_FIRMS has portfolioCompanies arrays
- ✅ COMPANIES has investor data (where filled)
- 🆕 Crunchbase-style portfolio scrape for the top 100 firms
- 🆕 13F filings for funds with public positions

**Kill the deal**: Portfolio data is stale faster than we can update. → Wire to weekly auto-refresh from public investor websites + LP letters.

**Build plan**: Dynamic per-firm route: `/investors/[firm].html`. Each page is template-driven from the merged data. Auto-builds from existing VC_FIRMS array; new firms added by adding to that array.

---

### 7. Co-Investor Network Graph ★★★★★ (14/15)

**What it is**: An interactive force-directed graph (D3.js) where nodes are funds and edges are companies they've co-invested in. Click any fund to highlight its syndicates. Filter by sector. Reveals: who is Founders Fund's most common co-lead in defense? Who follows a16z American Dynamism? Who invests SOLO?

**Why it matters**: Syndicate intelligence is the under-appreciated alpha. If you want to invest alongside Founders Fund in defense, knowing they go in with Lux 70% of the time means you LP $1M into Lux to get co-invest rights. Network maps reveal these patterns.

**Data sources**:
- ✅ VC_FIRMS portfolio data
- ✅ COMPANIES investor lists
- 🆕 Crunchbase round-by-round syndicate detail

**Kill the deal**: Force-directed graphs of 200+ nodes get visually noisy. → Default to top 50 most active funds; let user expand.

---

### 8. Investor Focus Drift Detector ★★★★ (13/15)

**What it is**: Tracks how each VC firm's sector mix changes quarter-over-quarter. When Greylock pivots from B2B SaaS to defense, that's directional info worth knowing 6-12 months before everyone else does.

**Why it matters**: Funds often signal upcoming sector themes by doing 2-3 deals there before launching a "defense practice" or hiring a new partner. Detecting this drift = early-warning system for sector heat.

**Data sources**:
- ✅ VC_FIRMS portfolioCompanies + COMPANIES sector mapping
- ✅ Form D filings tagged with sector (via tracked-company match)
- 🆕 Press release scan for "we're hiring an X partner"

**Kill the deal**: Hard to detect drift with low-volume sample (some funds do 8 deals/year). → Use 3-quarter rolling average.

---

### 9. GP/LP Relationship Map ★★★★ (12/15)

**What it is**: Maps which sovereign wealth funds + family offices + endowments back which VCs. Reveals: ADIA → Lightspeed, Khazanah → Sequoia, Mubadala → multiple US funds. Critical for knowing who has dry powder + whose checks influence whose deals.

**Why it matters**: Stephen's ADIO/SAVI work is directly tied to which VCs ADIA / Mubadala back. Knowing the LP-to-GP-to-portfolio chain means knowing which calls to take.

**Data sources**:
- 🆕 ADV Form filings for SEC-registered investment advisors (public)
- 🆕 ILPA membership + commitment disclosures
- 🆕 Public LP announcements from sovereign wealth funds
- 🆕 LinkedIn scraping of fund LPAC members (legal grey area)

**Kill the deal**: Most LP relationships are confidential. Public ADV data covers ~30% of the picture. → Build with public-only first; clearly mark gaps.

---

### 10. Strategic Acquirer Matchmaker ★★★★ (11/15)

**What it is**: For any private company in our database, predict the top 5 most likely strategic acquirers. Trained on 10 years of frontier-tech M&A (Anduril buying Blue Force Technologies, Saronic buying NavalDome, etc.) plus prime contractor portfolio gaps.

**Why it matters**: Acquisition probability + likely acquirer = exit modeling. Investors can size positions based on realistic exit paths, and our content team can publish "potential acquirers of X" pieces that drive real engagement.

**Data sources**:
- ✅ Existing COMPANIES + sector + tech stack
- ✅ Public M&A database (GBS, S&P Capital IQ alternative via SEC 8-K parsing)
- 🆕 Prime contractor capability gap analysis (DoD R&D, RTX/LMT/NOC public reports)

**Kill the deal**: Probability models can mislead non-expert users. → Surface as "candidate buyers worth watching" not "predicted exit."

---

## Part 5 — Public Market Tools (Tier 2)

_For the 67 public frontier-tech names in our database (PLTR, RKLB, ASTS, ACHR, JOBY, IONQ, OKLO, etc.)._

### 11. 13F Institutional Flow Tracker ★★★★★ (14/15)

**What it is**: Quarterly diff of every institutional holder of every public frontier-tech company. Surfaces: BlackRock added $200M Palantir Q1, Tiger sold half its Anduril position (when Anduril IPOs), Citadel bought 5% of Joby. Time-series chart per stock.

**Why it matters**: 13F is public, free, and most investors don't bother running the diff. The signal is strongest for newly-public companies (the institutions building positions early are the ones with conviction).

**Data sources**:
- ✅ SEC 13F filings (free via EDGAR)
- ✅ Already collecting some via `fetch_sec_filings.py`
- 🆕 New script `fetch_13f_holdings.py` that maps holder → ticker quarterly

**Kill the deal**: 13F is filed 45 days after quarter-end (data is delayed). → Acknowledge in UI; combine with real-time insider trading for current signal.

---

### 12. 13D Active Stake Alert ★★★★ (13/15)

**What it is**: When any investor crosses 5% ownership in a public frontier-tech company, they must file 13D within 10 days. We surface these in real-time. 13G (passive) is a separate weaker signal.

**Why it matters**: 5%+ stakes are highest-conviction signals on the entire stock market. Activist takeovers, strategic accumulations, and insider buying surges all show up here first.

**Build plan**: Cron job (daily) hits SEC EDGAR for 13D/13G filings, filters to our 67 public names, alerts.

---

### 13. Insider Buy/Sell Velocity Score ★★★★★ (14/15)

**What it is**: For each public company, compute a rolling 90-day score of insider buy vs sell intensity, weighted by buyer rank (CEO buys = 5x weight; director sells = 1x). Color-coded: green = insider accumulation, red = distribution.

**Why it matters**: Insider buying is one of the few legal signals that historically predicts outperformance. We already pull Form 4 data — turning it into a digestible score is fast.

**Data sources**:
- ✅ Already have `data/insider_transactions_auto.js` from Form 4
- 🆕 New scoring algorithm + per-company velocity dashboard

---

### 14. Earnings Calendar + Deception Score Preview ★★★★ (12/15)

**What it is**: Calendar of upcoming earnings calls for our 67 public names, with the company's prior-quarter deception detector score shown alongside. Lets investors prep questions / position size before the call.

**Why it matters**: Stephen builds two products from this — an investor heads-up email and a "earnings to watch this week" newsletter section that drives engagement.

**Data sources**:
- 🆕 Earnings calendar scrape (Yahoo Finance, Seeking Alpha — both public)
- ✅ Deception detector skill already built

---

### 15. Analyst Coverage + PT Change Tracker ★★★ (11/15)

**What it is**: Tracks who covers each public frontier-tech name (number of analysts, ratings distribution, price target range). Alerts on rating changes, PT raises/cuts, initiations.

**Why it matters**: Coverage initiations often precede institutional accumulation by 60-90 days. Useful but not differentiated — most platforms have this.

**Build plan**: Public scrape of TipRanks / Seeking Alpha / Refinitiv summaries.

---

## Part 6 — Differentiated Alpha (Tier 3)

_Tools nobody else has built specifically for frontier tech._

### 16. Frontier Tech Comp Engine ★★★★★ (13/15)

**What it is**: For private frontier-tech companies, pre-built comparable-multiples for valuation: SMR (revenue / MW capacity / NRC stage), fusion (TRL / capital raised / scientific milestones), hypersonics (DoD contract value / test flight count), humanoid robotics (deployment count / cost per unit).

**Why it matters**: Public-market comps don't exist for these sectors. Investors pricing rounds need ANY framework. We build the framework, become the citation.

**Build plan**: Per-sector comp models published as part of the research section. Updated monthly as new data arrives.

---

### 17. Customer Concentration Risk Scorer ★★★★ (12/15)

**What it is**: For each frontier company, estimate revenue concentration: % from DoD vs commercial, % from top-1 customer. High concentration = lower exit multiple + binary risk.

**Data sources**:
- ✅ Existing SAM.gov contracts data per company
- 🆕 Press release NER for "customer wins"
- 🆕 Job postings analysis (account managers per customer)

---

### 18. Burn Rate Estimator from Public Signals ★★★★ (11/15)

**What it is**: Estimate burn per company from: headcount × sector-median-comp + office lease (square footage) + Form D cadence. Output: "Anduril burns ~$X/month, runway ~Y months until next raise."

**Why it matters**: Without bank statements, this is the best public approximation. Combined with round cadence model (Tool #4), produces actionable timing predictions.

---

### 19. Talent Flow Tracker ★★★★ (12/15)

**What it is**: When senior engineering / leadership talent moves between companies, that's signal. We track: ex-SpaceX → frontier-tech startup founders. Ex-OpenAI → AI startup founders. Ex-Anduril → defense startup founders.

**Why it matters**: Founder background already drives our scoring; talent flow extends it to track team formation in real time.

**Data sources**:
- 🆕 LinkedIn scraping of senior employees at top 50 source companies (Apify)
- ✅ Existing FOUNDER_DNA data we can extend

---

### 20. Geopolitical Risk Score per Company ★★★★ (12/15)

**What it is**: For each company, score: China supply chain dependency (from bill-of-lading data we already have), Taiwan exposure, sanctions/ITAR sensitivity, sovereign-fund LP composition. Output: 0-100 risk score.

**Why it matters**: Frontier tech is increasingly geopolitically loaded. Risk scoring is now table stakes for institutional investors.

**Build plan**: Composite score from: bill-of-lading risk-country %, sector × geography matrix, ITAR + EAR controlled tech indicator.

---

## Part 7 — Decision Support Tools (Tier 4)

### 21. Backtest Engine ★★★ (10/15)

"If I'd invested $X in every Defense & Security Series A 2020-2023, what's my IRR assuming sector-median exit multiples?" Live calculator that demonstrates portfolio construction alpha.

### 22. Personal Portfolio Tracker ★★★★ (12/15)

Members upload their positions (CSV or live OAuth to Carta/AngelList). Get daily change report + per-company news + risk flags. Bloomberg's "PORT" command for frontier tech.

### 23. ROS Fund Auto-Allocation Engine ★★★★ (11/15)

Given current ROS Fund portfolio + cash on hand + thesis weights, suggests: "of the 50 actively raising companies, here are the 5 highest-fit for your remaining capital this quarter." Combines #2 + #4 + your fund parameters.

### 24. Founder Reference Aggregator ★★★ (10/15)

For any founder in the database, pull every public mention: podcasts, interviews, Substack posts, conference talks. Surface as a single profile page. "Ted Feldmann's complete public footprint in 30 seconds."

### 25. Conviction Stack Ranker ★★★★ (12/15)

Members create a watchlist; we rank it daily by composite signal score (funding momentum + news + insider signals + deception flags + talent inflow). Top of stack = "most worth a call this week."

---

## Part 8 — The crown jewel feature

If you build only ONE thing in the next 12 months, it should be the **Investor Intelligence Hub** — a unified workspace combining 5 of the tools above into one Bloomberg-style screen:

1. **Top of screen**: 4 quick-stat tiles
   - Active raises this week (Tool #2)
   - Insider buys today (Tool #13)
   - Pre-Form-D leaks this week (Tool #3)
   - Your watchlist movers (Tool #25)

2. **Center pane**: The Funding Pulse feed (Tool #1) — chronological, filterable, searchable

3. **Left sidebar**: Per-investor mini-pages — pick any fund from VC_FIRMS, see their portfolio + recent activity (Tool #6)

4. **Right sidebar**: Co-investor graph (Tool #7) — visual + interactive

5. **Bottom**: 13F + insider velocity for any selected company (Tools #11 + #13)

This is the "**Bloomberg PORT for frontier tech**" — the screen every member opens at 6 AM to check what changed overnight. The single most defensible feature on the platform.

---

## Part 9 — 90 / 180 / 365-day roadmap

### Q2 2026 (next 90 days)

**Ship in this order:**

1. **Per-Investor Portfolio Pages** (Tool #6) — fastest big win; we already have data, just need the dynamic page template
2. **Unified Funding Pulse** (Tool #1) — combines existing pipelines into a new page
3. **Insider Buy/Sell Velocity Score** (Tool #13) — leverages existing Form 4 data
4. **13F Institutional Flow Tracker** (Tool #11) — new pipeline + UI on each public company
5. **Active Raise Calendar** (Tool #2) — derives from #1

**Estimated delivery**: 3 features per month × 3 months = 9 features. The 5 above plus 4 buffer items.

### Q3 2026 (months 4-6)

6. **Co-Investor Network Graph** (Tool #7) — D3-based interactive
7. **Pre-Form-D Leak Detector** (Tool #3) — LP-newsletter scraper first
8. **13D Active Stake Alert** (Tool #12) — extends 13F pipeline
9. **Investor Focus Drift Detector** (Tool #8) — analytics layer on existing data
10. **Earnings Calendar + Deception Preview** (Tool #14) — combines existing skill with new calendar

### Q4 2026 (months 7-9)

11. **Frontier Tech Comp Engine** (Tool #16) — content + data product
12. **Strategic Acquirer Matchmaker** (Tool #10)
13. **Customer Concentration Risk Scorer** (Tool #17)
14. **Round Cadence + Due-Date Tracker** (Tool #4)
15. **GP/LP Relationship Map** (Tool #9) — limited by data; build with public sources only

### Q1 2027 (months 10-12) — The Crown Jewel

16. **Investor Intelligence Hub** — the unified workspace (Part 8). Brings together 5 of the prior tools into one screen.

---

## Part 10 — Monetization

The current Strategic Roadmap (April 2026) proposed a $99 / $499 / $2,500/month tier structure. Investor tools are the **strongest justification** for the $499 / $2,500 tiers.

| Tier | Investor tools available |
|---|---|
| **Free** | Public funding feed, basic investor directory |
| **$99/mo Member** | Full Funding Pulse, Active Raise Calendar, 13F summaries, watchlist alerts |
| **$499/mo Pro** | Co-Investor Graph, Per-Investor pages, Insider Velocity, Auto-Allocation Engine, Backtest Engine |
| **$2,500/mo Institutional** | Pre-Form-D Leak Detector, GP/LP Map, Founder Reference Aggregator, Custom Skill Builder, API + Snowflake connector |

**Pricing rationale**: Pro tier replaces what a partner-track associate uses Pitchbook for ($1,200/yr seat + $5K addons). $499/mo = $5,988/yr undercuts Pitchbook for the frontier-tech subset while offering tools Pitchbook doesn't have.

Institutional tier is justified by Pre-Form-D Leak Detector alone — that signal is genuinely $2,500/month value to anyone running a fund. One actionable lead per month pays for the year.

---

## Part 11 — The bar for accuracy

Stephen specifically demanded "100% accurate." Three principles to enforce across every investor tool:

1. **Every data point links to its primary source.** Every Form D row links to the SEC filing. Every 13F row links to EDGAR. Every news headline links to the original publisher. We earn trust by being clickable-to-truth.

2. **Estimates are clearly marked.** Burn rate, valuation, cap-table reconstruction = `~` prefix or "estimated" badge. Never present an inferred number as a verified one.

3. **Stale data is degraded, not hidden.** When a 13F is 45 days old, we show "as of Q4 2025 — next update May 15." Never let a member assume currency that isn't there.

These principles already guide our pipeline_watchdog.py scoring; extend the same discipline to all new investor tools.

---

## Summary — the one-paragraph version

**Build five tools in the next 90 days: Per-Investor Portfolio Pages, Unified Funding Pulse, Insider Buy/Sell Velocity, 13F Institutional Flow Tracker, and Active Raise Calendar. They directly answer Stephen's two stated questions ("when raising / who invested in what") and use data we already have. They're worth $5,988/year to a fund associate (cheaper than Pitchbook, with edge Pitchbook doesn't have). The crown jewel — an Investor Intelligence Hub combining all five — ships in Q1 2027 and becomes the single most defensible feature on the platform.**

Pick the first 1-3 of these to start with and I'll scope each into a build-ready spec.
