# Strategic Roadmap — Bloomberg Intelligence for Frontier Tech

_Thorough research memo · April 2026 · ~5,000 words_
_Inspired by the hedge-fund-skill pattern: unique data + AI = irreplaceable tooling_

---

## Part 1 — The vision, made concrete

Bloomberg Terminal isn't valuable because it has data. It's valuable because it has **data + interpretation + the social contract of every serious user being on it**. The Terminal is a $25K/user/year product and it stays that way because:

1. **Unique data** — 500+ third-party providers wired in, plus Bloomberg's own proprietary feeds (dealer inventories, the FX fix, earnings call transcripts seconds after they end).
2. **Interpretation on top** — Bloomberg Intelligence (BI) runs 200+ analysts who layer "what does this mean" across 2,000 companies and 135 industries.
3. **The chat** — IB / MSG / CHAT is where every hedge fund analyst, trader, and banker does business. You can't not be on it.
4. **Proprietary scoring** — BICS classifications, Bloomberg Composite Ratings, ESG scores — embedded in every workflow.

**Bloomberg's own "next frontier" is private markets.** They said this out loud. They haven't built it yet for frontier tech specifically. That's the opening.

"Bloomberg Intelligence for frontier tech" doesn't mean "cover 2,000 companies." It means **cover the 868 companies you already track, but make every single one of them actionable in a way nothing else in the world is.**

The test: a member should be able to open the site at 6 AM and within 20 minutes have a concrete decision to make — a company to invest in, a founder to call, a patent to track, a government contract to bid for alongside, a supply-chain risk in their portfolio.

That test fails today. The data is there. The interpretation layer is thin. The decision tools are largely absent.

---

## Part 2 — The evaluation framework

Every new feature I propose is scored on **three dimensions**:

| Dimension | What it means | Why it matters |
|---|---|---|
| **Uniqueness** | Is this data nobody else has for frontier tech? | Bloomberg charges $25K/yr because you can't get the data elsewhere. |
| **Usefulness** | Does a member make a better decision because of it? | Interesting ≠ useful. Useful = drives action. |
| **Feasibility** | Can you build it with public APIs + scraping + AI, no paid partners? | $0 marginal cost = durable moat, because members can't just "go get it themselves." |

I'll tag each proposal below with a 1–5 on each.

Two additional notes:

- **The hedge fund pattern** (books → Claude skill → alpha) is not a feature category — it's an **orthogonal execution model**. Every single data source below gets 10× more valuable when you layer a Claude skill on top of it. I'll mark the highest-leverage skill opportunities explicitly.

- **The data-source landscape is moving**. Things that were paid APIs in 2020 are often free or cheaply scrapable in 2026. Recheck annually.

---

## Part 3 — Tier 1: Unique Raw Data Pipelines

The core question: **what is the frontier-tech equivalent of Bloomberg's dealer-inventory data?** It's not one thing — it's eight things. Each of these is publicly obtainable, but nobody is actively cross-referencing them against a 868-company frontier-tech universe. That cross-reference IS the product.

### 3.1. FERC / State PUC Power Interconnection Queues ★★★★★

**Uniqueness 5/5 · Usefulness 5/5 · Feasibility 5/5**

FERC ordered PJM (the largest grid operator in the US) on Dec 18, 2025 to create new colocation rules. **170,000 MW of new generation requests have hit PJM's queue since 2023** — each one has a named customer. The queue is public. The exact size, location, and counterparty of every mega-data-center build is sitting in a CSV that almost nobody in VC reads.

**The insight it unlocks:** You can see every CoreWeave, xAI, Anthropic, OpenAI, Meta, Amazon, Microsoft data-center buildout 6–18 months before the press release. You can see which of your tracked nuclear SMR companies (Oklo, NuScale, X-energy, TerraPower) are being named as preferred supply.

**How to get it:** Good news — **Interconnection.fyi already aggregates all seven US RTOs** (PJM, MISO, ERCOT, CAISO, SPP, NYISO, ISO-NE) into a free daily feed. You don't need to scrape FERC directly. Pair with **CPUC Locate Documents** and **Texas PUCT Interchange** for state-level dockets — Texas SB 6 (2025) now forces every >75 MW interconnection through formal PUCT docket filings, making large-load detection trivial.

**Claude-skill layer:** Train a skill on FERC regulatory language + data-center site selection patterns. Feed it the queue. Output: "These 8 queue entries match patterns of hyperscaler data-center builds. These 3 are the interesting ones because they're within 50 miles of a fiber hub with spare capacity." That's alpha.

**Member use case:** "Alert me 5 days after any ISO queue filing >200 MW within 50 miles of a tracked nuclear SMR company."

### 3.2. US Customs Bill of Lading (ImportYeti / scrape) ★★★★★

**Uniqueness 5/5 · Usefulness 4/5 · Feasibility 4/5**

Every ocean shipment into a US port has a bill of lading filed with CBP. Under FOIA, **this data is free**. Panjiva and ImportGenius charge $5K–50K/year to organize it. ImportYeti offers a free tier. TradeInt has 8B+ shipment records.

**The insight it unlocks:** For hardware companies — every humanoid robot startup, every rocket company, every chip company — you can see their actual component suppliers, their shipment cadence, their inventory ramp. Anduril increased shipments 12× in 18 months? That's in the data before the earnings call.

**Concrete examples of what this reveals:**
- Which drone companies are sourcing from Chinese suppliers (compliance risk)
- Which battery companies are ramping cell imports ahead of public product launches
- Which fusion companies are importing rare superconductor materials — leading indicator of build-phase advancement
- When a humanoid company's import volume triples (go find their Series B before the deck leaks)

**How to get it:** Start with ImportYeti free tier; move to paid ImportGenius ($199/mo starter) or direct CBP FOIA if usage justifies. **One engineer, two weeks, $200/mo.**

**Claude-skill layer:** Combine bill-of-lading data with company descriptions. "Which of our 868 companies look like they just crossed from prototype to manufacturing based on the cumulative import weight in the last 90 days?" Answer-engine: rank order and push to members as a "Manufacturing Readiness Index."

**Member use case:** "Show me companies whose imports grew >5× year-over-year and rank by sector heat."

### 3.3. FCC ULS + Experimental Radio Service ★★★★

**Uniqueness 4/5 · Usefulness 4/5 · Feasibility 5/5**

Every experimental radio license in the US — for satellite downlinks, drone C2 links, autonomous vehicle radars, quantum sensors — is filed with the FCC. **Public, free, API-accessible** via FCC ULS (Universal Licensing System) and ELS (Experimental Licensing System).

**The insight:** Which satellite company just filed for a new ground-station frequency? Which drone startup just filed for a unique spectrum allocation for mesh networking? These filings typically precede product launches by 6–12 months.

**How to get it:** FCC provides bulk-download weekly files + a search UI. Scrape is trivial.

**Claude-skill layer:** Match applicant names and FRNs to your company list. Surface non-obvious cross-connections — e.g., "NewCo, which claims to be in defense comms, just filed a satellite downlink license at 28 GHz — they're not a defense company, they're a nascent space company."

### 3.4. H-1B LCA + PERM Filings ★★★★

**Uniqueness 3/5 · Usefulness 5/5 · Feasibility 5/5**

Every H-1B petition requires a Labor Condition Application (LCA) filed with DOL. **Every LCA is public** — salary, job title, SOC code, employer, work city. 4.8M records indexed via h1bdata.info (free).

**The insight:** What specialized talent is a company actually hiring for, at what price, in what city?
- "Oklo just filed 12 LCAs for nuclear fuel engineers in Idaho Falls — they're staffing the fuel fab"
- "Anduril is filing LCAs for ML engineers at $450K — they're scaling, and they're paying aggressively"
- "Scale AI LCAs dropped 60% QoQ — something is happening"

**How to get it:** DOL FLAG performance data is downloadable quarterly. Free.

**Claude-skill layer:** For each tracked company, rolling 90-day view of: (a) number of LCAs filed, (b) median salary percentile vs sector, (c) concentration of SOC codes. Change detection on these three = strategy-pivot signal.

**Member use case:** "Companies where LCA filings accelerated 2× in last quarter AND median salary is above 90th percentile for the sector." That list is a who's-who of companies winning the talent war.

### 3.5. FAA ADS-B + NOTAMs + Test Flight Data ★★★★

**Uniqueness 4/5 · Usefulness 4/5 · Feasibility 4/5**

Every aerospace startup with a real test program flies real aircraft. Every one of those flights shows up in:
- ADS-B (aircraft position data) — free via adsb.lol, adsbexchange.com
- FAA NOTAMs — official flight operation notices, free
- FAA aircraft registry — who owns what tail number

**The insight:** When a stealth hypersonics startup quietly stands up a test program in Mojave, the FAA NOTAMs prove it before any press release. Same for VTOL / drone companies doing endurance testing.

**How to get it:** ADS-B exchange has a public API. NOTAMs are FAA's open-data. Aircraft registry CSV download.

**Claude-skill layer:** Cross-reference tail numbers → LLC ownership (via state business registries) → tracked companies. Surface "Company X's test aircraft flew 47 hours in March, up 3× QoQ." That's ground-truth development velocity.

### 3.6. DSCA FMS Notifications ★★★★

**Uniqueness 4/5 · Usefulness 4/5 · Feasibility 5/5**

Every major US arms sale to a foreign government triggers a DSCA Congressional notification — **publicly posted on dsca.mil** during the statutory 15 or 30-day window. Thresholds: $14M major equipment / $50M articles / $200M construction. This is where defense tech winners show up as subcontractors on multi-hundred-million-dollar foreign sales.

**The insight:** Which private defense tech company is on the prime's subcontract list for the $4B Saudi GCC air defense deal? That list is leaked weeks later in trade press, but is hinted at in the initial DSCA notification. Also signals **geographic demand** — UAE, Taiwan, Japan, Saudi — which is directly relevant for Stephen's ADIO / SAVI pipeline work.

**How to get it:** Free and scrape-friendly — dsca.mil/Press-Media/Major-Arms-Sales publishes 30-day notifications as plain-text press releases. State.gov/arms-sales-congressional-notifications duplicates.

**Claude-skill layer:** Train a skill on DSCA notification patterns + every past FMS-to-subcontractor attribution in trade press → extract "who are the implicit subcontractors likely involved." Surface matched tracked companies.

**IMPORTANT CORRECTION:** ITAR / DSP-5 export licenses themselves are **NOT publicly available** (DDTC holds them as proprietary/classified under ITAR § 126.10; FOIA denied). Only DSCA FMS notifications + Section 655 country-level aggregates are public. Update the initial list to remove DSP-5 as a pipeline candidate — it looks attractive but the data doesn't exist.

### 3.7. University Tech Transfer Office Licensing Deals ★★★★

**Uniqueness 5/5 · Usefulness 4/5 · Feasibility 3/5**

Every Stanford / MIT / Caltech / UW / CMU / Georgia Tech spinout starts as a licensing deal from their Tech Transfer Office (TTO). TTOs publish press releases for ~30% of deals; the rest show up 1–3 years later as AUTM statistics.

**The insight:** The pre-Series-A pipeline for frontier tech. Founders who haven't raised yet. 18 months before they show up on everyone's radar.

**How to get it:** Scrape 20–30 TTO press-release pages (Stanford OTL, MIT TLO, Caltech OTT, UW CoMotion, CMU CTTEC, UC TT, etc.). ~$0 cost, weekly scrape.

**Claude-skill layer:** Match TTO licensees to new Delaware incorporations (state filings are public) → discover stealth-mode companies before their LinkedIn exists.

### 3.8. State Business Registration Filings (DE, NV, CA, TX, WY) ★★★

**Uniqueness 3/5 · Usefulness 3/5 · Feasibility 4/5**

Every US startup is either a Delaware C-corp or a state LLC. State corporate filings are public and searchable in most states. New entity formations in "frontier tech adjacent" NAICS codes are a leading indicator.

**How to get it:** OpenCorporates has a free tier + paid API. Most states have individual search UIs. Scrape + aggregate.

### 3.9. Lobbying Disclosures (Senate LDA-1) ★★★

**Uniqueness 3/5 · Usefulness 4/5 · Feasibility 5/5**

Every lobbyist hired in DC has to file a Senate Lobbying Disclosure form quarterly. **Public, free, machine-readable via OpenSecrets API.** Shows which companies are spending what on which issues.

**The insight:** When a frontier tech company starts paying $200K/quarter to lobbyists on "spectrum allocation" or "export controls" or "procurement reform" — that's a real signal of what they're fighting for. Anduril's lobbying spend doubled in 12 months before their DoD wins accelerated.

**Claude-skill layer:** For each company, rolling view of: lobbying spend trend, specific issues, lobbyists retained (and those lobbyists' other clients). Network graph of which companies are hiring the same lobbyists on the same issues.

### 3.10. Federal Register Regulatory Comments ★★★

**Uniqueness 4/5 · Usefulness 3/5 · Feasibility 5/5**

Every proposed federal rule has a comment period. Company comments are public on regulations.gov. When a frontier company comments on a proposed rule — especially when they're quoted in the final rulemaking — that's influence.

**How to get it:** Regulations.gov API (free, API key, 50 req/min) + Federal Register REST API. Combine with lobbying data (3.9) for the full "policy surface" per company.

### 3.11. Wayback Machine + Common Crawl Change Detection ★★★★★

**Uniqueness 5/5 · Usefulness 5/5 · Feasibility 5/5**

This one came out of my research and it's a gem. Every frontier-tech company's website is archived weekly by the Wayback Machine. The CDX API returns up to 10K snapshots per URL with content hashes. For $0 you can **diff every company's homepage, team page, product page, and customer logo wall across time**.

**The insights it unlocks:**
- **Quiet exec departures** — when the "Our Team" page stops listing someone, that's earlier than any announcement.
- **Stealth pivots** — when a hydrogen company's homepage replaces "green H2" with "sustainable aviation fuel," they pivoted. Before the press release.
- **Customer logo wall adds and drops** — a new "As seen in / Trusted by" logo is a customer win signal.
- **Pricing page changes** — a SaaS company moving from transparent to "contact us" pricing usually = enterprise pivot.
- **Job page volume** — spike in listings = scaling; drop to zero = something is wrong.

**How to get it:** Wayback CDX API (free). For bulk text analytics, Common Crawl monthly dumps on S3 (pay only egress, ~$50–200/month).

**Claude-skill layer:** For each company, a weekly "diff digest" that reads the content changes and writes a one-paragraph summary: "Axibo AI: removed co-founder from team page; added Toyota logo; job count dropped from 27 to 9." That summary, done for all 868 companies weekly, is intelligence no one else has.

### 3.12. YouTube Auto-Captions (demo days, launches, GTC) ★★★★★

**Uniqueness 5/5 · Usefulness 5/5 · Feasibility 5/5**

Missed this in my initial list. **Every** NVIDIA GTC keynote, Tesla AI Day, SpaceX launch webcast, Figure AI / 1X / Boston Dynamics demo, Anduril demo, AWS re:Invent talk is auto-captioned by YouTube within 24 hours. The `youtube-transcript-api` Python library extracts them with no auth.

**The insight:** When Jensen says "we're partnering with [Company]" from the GTC stage, or Tesla shows a supplier logo in the background of an Optimus demo, or SpaceX's launch commentator names a payload customer — that's material non-public-structured information. It's in the video but nowhere structured.

**How to get it:** Free. Pipe ~500 corporate + frontier-tech YouTube channels → youtube-transcript-api → NER against your 868-company list → daily alert.

**Claude-skill layer:** Auto-generated weekly "What was said out loud about your portfolio" briefing, with video timestamps for any mentions.

---

## Part 4 — Tier 2: AI Interpretive Layers (The Hedge Fund Pattern)

The hedge fund example you cited is the most important idea in this memo. Here's why:

**The pattern is: "Books in, Claude skill out."** Take domain expertise that's written down — whether in PDFs, academic papers, old government reports, founder letters, even behavioral psychology texts — and turn it into an autonomous analyst that reads public data and produces interpretation no human analyst has time to write.

For frontier tech, the books-in layer is different from equities. The hedge-fund analogue for us:

### 4.1. The Earnings Call Deception Detector (direct hedge fund pattern) ★★★★★

**Uniqueness 4/5 · Usefulness 5/5 · Feasibility 5/5**

The 67 public frontier-tech companies in your database (Palantir, AST, Archer, Joby, IonQ, Rocket Lab, Symbotic, etc.) have quarterly earnings calls. Transcripts are free via SEC / Seeking Alpha. The hedge fund's CIA-negotiation-psychology pattern applies **1:1**.

**The skill**: Feed it the CIA interrogation classics + Cialdini + behavioral finance research on CEO deception (Larcker & Zakolyukina 2010 is the seminal paper). Run it against every transcript. Output: confidence score, hedging-language detection, topics-avoided analysis.

**Member use case:** "Before I increase my Palantir position, show me the deception flags in Karp's last 4 earnings calls." Or: "This quarter, rank all public frontier tech CEOs by language-confidence decline."

**Why this is irreplaceable:** Public markets have Sentieo, Aiera, AlphaSense. None are tuned to frontier tech. None have books-in customization.

### 4.2. The Hype vs Substance Scorer ★★★★★

**Uniqueness 5/5 · Usefulness 5/5 · Feasibility 5/5**

Train a skill on the history of frontier tech hype cycles — Theranos, Nikola, Quibi, Magic Leap, WeWork — and contrast with actual delivery stories (SpaceX, Palantir, Nvidia). Books-in: every SEC enforcement action against a hype-to-bust company, plus every successful category-defining technical paper.

Feed it the current press releases, product demos, and earnings calls of the 868 companies. Output: hype-substance ratio per company, per quarter.

**Member use case:** "The 10 companies whose hype-substance ratio deteriorated most in Q1 2026." Then: "Of those, which have raised a down round or filed a Form D at a cut valuation in the last 60 days?" That intersection = pre-WeWork signals.

### 4.3. The Founder Psychology Match ★★★★

**Uniqueness 4/5 · Usefulness 4/5 · Feasibility 4/5**

Books-in: Paul Graham's essays, Jason Calacanis's founder archetype frameworks, Reid Hoffman's Blitzscaling lectures, Peter Thiel's Zero to One. Add: every biographical interview of a Y Combinator Top 100 founder.

Output: for any founder in your database, a narrative of "this founder pattern-matches to [archetype], which historically is [good/bad] for [stage]."

**Member use case:** Before you cold-email Ted Feldmann at Durin, the skill writes you a two-paragraph "here's what drives this founder, here's what they'll respond to" brief. Based on every public interview, every tweet, every podcast they've been on. You can't buy that anywhere today.

### 4.4. The Government Contract Winner Predictor ★★★★

**Uniqueness 5/5 · Usefulness 5/5 · Feasibility 4/5**

Books-in: DoD 5000 series, the FAR, past GAO protest decisions, SAM.gov solicitation-to-award histories for the last 10 years. Add: every SBIR Phase II → Phase III successful transition documented in SBIR.gov.

Output: for any active SAM.gov solicitation, which of the 868 tracked companies is most likely to win, ranked.

**Member use case:** When the DoD publishes a $40M solicitation for "autonomous UAV swarm C2," the skill says: "Likely winners in order: Anduril (70%), Shield AI (15%), Swarm Aero (8%), FlyBy Robotics (5%), field (2%)." Based on: past awards, technical fit from patents, teaming patterns, ex-DoD hires via LCA data.

### 4.5. The Acquisition Probability Scorer ★★★

**Uniqueness 4/5 · Usefulness 4/5 · Feasibility 4/5**

Books-in: every M&A deal in frontier tech 2015–2026, with details of acquirer type, multiple paid, stage at acquisition, competitive landscape pre-deal. Feed in current company attributes. Output: probability of acquisition in next 12 months, ranked by likely acquirer.

**Member use case:** "Which 5 of my portfolio companies are most likely to be acquired by a defense prime in 2026, and by whom?" That's deal-flow gold for an LP, and exit-timing signal for a GP.

### 4.6. The Technology Readiness Level (TRL) Tracker ★★★

**Uniqueness 4/5 · Usefulness 4/5 · Feasibility 3/5**

NASA TRL 1–9 scale is the gold standard for hardware maturity. Books-in: NASA TRL definitions + DOD TRL definitions + historical data on TRL progression rates by sector.

Output: auto-estimated TRL for every company based on patents filed, papers published, demos executed, contracts won. Updated monthly.

**Member use case:** "Fusion companies by TRL, sorted by velocity of TRL improvement in the last 18 months." Answers "which of the 30 fusion companies is actually closest to commercial reality."

### 4.7. The Regulatory Capture / Headwind Detector ★★★

**Uniqueness 5/5 · Usefulness 3/5 · Feasibility 3/5**

Books-in: every congressional hearing transcript where frontier tech was discussed (AI safety, biosecurity, autonomous weapons, nuclear). Senator voting records on relevant bills. FDA / FAA / NRC adviser committees.

Output: for any sector or company, a "regulatory tailwind vs headwind" score and the specific congressional actors to watch.

**Member use case:** "Has the political environment for advanced nuclear improved or deteriorated in the last 6 months, and which senators are the swing votes?" Answers get published as your Rational Optimist Substack essay.

### 4.8. The Vaporware vs Real Product Classifier ★★★★

**Uniqueness 5/5 · Usefulness 4/5 · Feasibility 5/5**

Books-in: Every announced product in frontier tech 2015–2026 with the ground truth of whether it actually shipped, when, and at what performance. (Humanoid robot companies are the current cesspool of this.)

Feed in: current company announcements. Output: probability the announcement results in a shipping product within 18 months.

**Member use case:** Every time Figure / Unitree / Apptronik / Sanctuary announces a new humanoid capability, the skill says "this matches the pattern of [demoware / beta / commercial] based on 200 prior announcements."

---

## Part 5 — Tier 3: Decision Tools Members Use

Data + AI is not enough. Members need tools to act on it.

### 5.1. The Deal Comps Engine ★★★★★

Given any private company, generate: "Companies at the same stage in the same sector with the same founder-archetype pattern have raised [amount] from [investor type]." Derived from your own data + Crunchbase-style enrichment.

### 5.2. Warm Intro Path Finder ★★★★★

LinkedIn graph → "shortest path from you to [any founder in the database]." Requires members to connect LinkedIn (opt-in). Massive value, near-zero marginal cost.

### 5.3. The Co-Investor Finder ★★★★

"Who else invests at Series A in defense companies with ex-SpaceX founders in California?" Output: list of funds + partners. Combined with the LinkedIn graph → one-click warm intros to LPs / co-investors.

### 5.4. The Government Contract Opportunity Matcher ★★★★

For every SAM.gov solicitation, AI matches to tracked companies with >70% fit. Alert member: "Your portfolio company Galadyne is a 82% fit for this $12M Air Force liquid propulsion solicitation." Auto-draft the teaming email.

### 5.5. Custom Alert Builder (Bloomberg's BBG ALERT) ★★★★

"Alert me when Anduril files a new patent in [topic], or when a competitor of [X] raises >$50M, or when [founder] tweets the word 'humanoid'." Unlimited alerts, user-defined triggers, piped over email + SMS + webhook.

### 5.6. Thesis Validation Tool ★★★

Member writes a paragraph describing their investment thesis. The tool returns 50 companies matching + evidence citations. Then generates a one-page memo supporting / rebutting the thesis.

### 5.7. Time-to-Exit Predictor ★★★

For any company in the database, Bayesian model outputs probability distribution over: IPO, M&A, Series X, shutdown — and timeline.

### 5.8. Portfolio Health Dashboard (for LPs / GPs) ★★★★

Load your portfolio (CSV or email parser from AngelList / Carta). Dashboard shows: valuation change estimates, concentration risk, supply-chain exposure, competitive moves against your portfolio. Weekly brief PDF.

### 5.9. Backtest Mode ★★★

"If I had invested $X in every Defense & Security Series A 2020–2023, what's the IRR assuming benchmark median exits?" Shows portfolio construction alpha.

### 5.10. The Custom Skill Builder (the hedge fund model, productized) ★★★★★

**This is the crown jewel — see Part 8.** Members upload their own books / PDFs / internal thesis notes. You wrap them in a Claude skill that reads your data and produces interpretation through the member's lens.

---

## Part 6 — Tier 4: Terminal-Like Features

### 6.1. IB Chat Equivalent — members DM each other ★★★
### 6.2. Community Research Notes (karma-based) ★★★
### 6.3. Live Events Calendar — earnings, demos, launches, conferences ★★★★
### 6.4. Daily Audio / Video Briefing — AI-narrated 5-min Frontier Daily ★★★★
### 6.5. Data Export (CSV / Excel / JSON) + Read-Only API ★★★★
### 6.6. Tableau / Snowflake Connector (paid tier) ★★
### 6.7. Watchlist + Custom Scoring Weights (Member creates own Frontier Index) ★★★★
### 6.8. Members-Only Office Hours with Stephen (1hr/week live Q&A) ★★★★

---

## Part 7 — Tier 5: AI Skills Marketplace

This is the direct productization of the hedge fund pattern. Skills are monetizable artifacts.

**Your starter library of 10 public skills (free for members, premium for non-members):**

1. **Deception Detector** — earnings call linguistic analysis (see 4.1)
2. **Hype vs Substance** — per-company hype ratio (see 4.2)
3. **TRL Tracker** — technology readiness per company (see 4.6)
4. **Founder Psychology Profiler** — founder archetype brief (see 4.3)
5. **Gov Contract Winner Predictor** — solicitation-to-company matching (see 4.4)
6. **M&A Probability** — acquisition likelihood scorer (see 4.5)
7. **Regulatory Weathervane** — sector-level policy tailwind/headwind (see 4.7)
8. **Vaporware Classifier** — announcement credibility (see 4.8)
9. **Supply Chain Stress** — bill-of-lading + news deltas
10. **Founder DNA Match** — finds founders whose trajectories match a template (e.g., "pattern-match this to early-stage Palmer Luckey")

**Then: let members upload their own books.** The Member Skill Builder lets any paying member drop 50–500 pages of PDFs / markdown / notes into a UI, and ROS generates a Claude skill tuned to read your 868-company database through that domain expert's eyes.

**Why this is the crown jewel:** The hedge fund example is ONE member doing this privately. If you productize it, every member becomes a hedge fund. Your platform becomes the Bloomberg Terminal × OpenAI Assistants × Bloomberg Intelligence — a combined platform with no incumbent.

Pricing: $500–2,000/month premium tier, per-member. Current Rational Optimist Substack has the audience to fill this tier within 12 months.

---

## Part 8 — The Crown Jewel Feature

If you could only build ONE thing over the next 12 months, it should be this:

### **"The Private Market Bloomberg Terminal"** — a dedicated `/terminal` app

A single integrated workspace, log-in gated, that gives members:

1. **The company universe** — full 868-company database, deeply enriched (the current site)
2. **One personalized daily feed** — 10 cards, AI-curated from every pipeline, ordered by how much it matters to the member's thesis / portfolio / watchlist
3. **One "what do I do today" widget** — three concrete actions: "Email this founder now (Form D filed Monday)" · "Bid on this SBIR topic (your portfolio company is a 82% fit)" · "Sell this public position (earnings deception score rose 40% last quarter)"
4. **One Claude-skill sidebar** — a chat interface where the member can run any of the 10 library skills, or their own custom skill, on any company in the database, returning natural-language answers
5. **One alert stream** — custom alerts, grouped by urgency
6. **One community tab** — what other members are looking at, watching, writing about
7. **One export button** — everything on this page to CSV or API

The design principle: **every element has to drive a decision.** No "interesting charts." No "cool maps." Just: data → interpretation → action.

The business test: **a Tier-1 VC partner at Founders Fund or Lux Capital should want to pay $2K/month for access, because their associates don't need Pitchbook once they have this.**

---

## Part 9 — 90-Day, 6-Month, 12-Month Roadmap

### Next 90 Days (Q2 2026): the four decisive shippable features

Build these four things. They're the highest-leverage pieces from Tiers 1, 2, and 3.

1. **FERC / ISO Interconnection Queue Tracker.** Weekly scrape + alert system. (Pipeline 3.1 + alert 5.5)
2. **The Earnings Call Deception Detector.** Ship it for all 67 public frontier-tech companies. (Skill 4.1) Free to members as the MVP of the Skills marketplace.
3. **The Warm Intro Path Finder.** Opt-in LinkedIn connection, path-finding backend. (Tool 5.2)
4. **Custom Alert Builder.** Unlimited alerts, user-defined triggers. (Tool 5.5)

These four features are defensible, valuable on day 1, and each one supports a member upgrade path (free → paid $X/month tier).

### Months 4–6 (Q3 2026): the intelligence layer

5. **US Customs Bill of Lading pipeline** (Pipeline 3.2)
6. **H-1B LCA tracker + hiring-velocity scoring** (Pipeline 3.4)
7. **The Hype vs Substance scorer** (Skill 4.2)
8. **The Gov Contract Winner Predictor** (Skill 4.4)
9. **Members-only live events calendar + weekly live Office Hours** (Features 6.3, 6.8)

### Months 7–12 (Q4 2026 – Q1 2027): the crown jewel

10. **The Private Market Bloomberg Terminal** — all previous features unified into a single `/terminal` workspace (Part 8)
11. **The Member Skill Builder** — members upload their own books, get a custom Claude skill (Tier 5, productized)
12. **The Daily Audio Briefing** — AI-narrated 5-min Frontier Daily (Feature 6.4)
13. **Read-only API + Tableau/Snowflake connectors** (Feature 6.5, 6.6)
14. **FCC ULS / FAA ADS-B / Lobbying pipelines** (Pipelines 3.3, 3.5, 3.9)

---

## Part 10 — Monetization

Current state: everything is free, members sign up for a newsletter.

Proposed tiers:

| Tier | Price | Audience | What they get |
|---|---|---|---|
| **Free / Observer** | $0 | Anyone | Current public database + public signals + newsletter |
| **Member** | $99/mo | Serious investors + founders | Custom alerts, watchlists, warm-intro finder, daily feed, export to CSV, 3 skill runs/day |
| **Pro** | $499/mo | Active investors + fund associates | Everything + unlimited skill runs + portfolio dashboard + co-investor finder + gov contract matcher + terminal access |
| **Institutional** | $2,500/mo | Funds, family offices, corp dev, primes | Everything + API access + Snowflake connector + custom skill builder + 1-on-1 office hours with Stephen + white-label briefs |

**Base case unit economics:**

- 500 members at $99 = $50K/mo
- 100 Pros at $499 = $50K/mo
- 20 Institutional at $2,500 = $50K/mo
- **Total ARR from first 620 paying users: $1.8M/yr**

That's ~0.2% conversion of a 300K-reader newsletter. Very achievable.

**Second-order: the Skill Marketplace.**

Let members publish skills for other members. Charge 30% marketplace fee. Eventually this is the fly-wheel — ROS becomes the Schelling point where every serious frontier-tech investor ships one skill and consumes 10.

---

## The one-sentence summary

**Take the 868-company database you already have, cross-reference it against 8 unique public-data pipelines that nobody else is aggregating for frontier tech, wrap 10 Claude-skill interpretive layers around it, deliver the whole thing as a Bloomberg-style terminal that tells each member what to do today, and let them build their own custom skills on top. That is the product that doesn't exist anywhere else in the world, and it has a clear $10–30M ARR trajectory from your existing audience.**

The hedge fund example is the tell. When one fund builds one custom skill and gets alpha, that's a moat. When you let every member build their own custom skill — that's a category.

---

## Appendix — Quick Inventory of Every Pipeline (35 sources ranked)

Crown jewels (★★★★★): FERC queue, bill of lading, earnings deception detector, hype/substance, deal comps, warm intro, alert builder, custom skill builder, the `/terminal`

High-priority adds (★★★★): FCC ULS, H-1B LCA, FAA ADS-B, DSCA FMS, lobbying disclosures, university TTO, gov contract predictor, founder psychology, vaporware classifier, TRL tracker, live events, daily briefing, data export, custom watchlists

Supporting features (★★★): state business registrations, regulatory comments, acquisition predictor, regulatory capture detector, co-investor finder, thesis validator, time-to-exit predictor, portfolio dashboard, backtest mode, chat, community notes, office hours, Tableau connector

Skip / low-leverage: Glassdoor sentiment (noisy, ToS issues — only worth it for top-50 companies with managed scrapers), **ITAR/DSP-5 (NOT publicly available — scrub from list)**, Port vessel manifests (strictly inferior to bill of lading), Chinese patents (use Google Patents BigQuery free dataset instead), NOAA satellite tasking (not actually available), DARPA performer lists (you already have 80% via SAM.gov), Indian Patent Office (low signal), Discord / Slack (ToS block, legal risk)

---

## Appendix B — Detailed 25-Source Data Landscape Scan

_Compiled from a focused research pass. For each source: access method, cost, and the specific frontier-tech signal it unlocks._

### Tier 1 (add immediately, high-signal, <$500/mo total)

| # | Source | Access | Cost | Key insight |
|---|---|---|---|---|
| 1 | **FERC/ISO Interconnection Queue** | Interconnection.fyi aggregator + direct RTO CSVs | Free | Data center, SMR, fab buildouts 18–36 months before groundbreaking |
| 5 | **FCC ULS + Experimental Radio** | FCC License View API + weekly bulk dumps | Free | Earliest signal for satellite, drone, autonomous tech |
| 10 | **DSCA FMS Notifications** | dsca.mil press releases + state.gov | Free | Defense tech appearing as subs in foreign arms packages |
| 11 | **SEC 13F / 13D / 13G** | EDGAR direct + sec-api.io | Free / <$100/mo | Institutional ownership diff for the 67 public frontier-tech names |
| 12 | **H-1B LCA Filings** | DOL OFLC quarterly disclosure (dol.gov/agencies/eta/foreign-labor/performance) | Free | Real hiring signal — titles, salaries, worksites |
| 14 | **Federal Register / Regulations.gov** | Regulations.gov + Federal Register APIs | Free | Which companies are commenting on which rules |
| 15 | **Senate LDA Lobbying Disclosures** | lda.senate.gov/api (REST, rate-limited) | Free | Who's spending what on which policy issues |
| 19 | **Wayback Machine / Common Crawl** | Wayback CDX API + Common Crawl S3 | Free / ~$50/mo egress | Website change detection → exec moves, pivots, customers |
| 23 | **Podcast Transcription (20VC / All-In / BG2 / Dwarkesh)** | AssemblyAI @ $0.15–0.37/hr | ~$500–1,000/mo | Named mentions by top operators, investors, analysts |
| 24 | **YouTube Corporate Event Captions** | youtube-transcript-api + YouTube Data API | Free | GTC / Tesla AI Day / demos — supplier and customer name drops |

### Tier 2 (add selectively, ~$500–5,000/mo if all added)

| # | Source | Access | Cost | Key insight |
|---|---|---|---|---|
| 2 | **State PUC Dockets (CPUC, PUCT, CAISO)** | Per-state scrape | Free | Large-load applications before FERC queue |
| 3 | **EPA NPDES Water Permits** | EPA ECHO REST API + ICIS-NPDES bulk | Free | Fab, data center, lithium brine water draws |
| 4 | **US Customs Bill of Lading** | ImportGenius / ImportYeti free tier | $200–600/mo | Shipment-level supply chain for hardware companies |
| 9 | **University TTO Press Releases** | Scrape Stanford OTL / MIT TLO / Caltech / UC / CMU | Free | Pre-Series-A frontier tech pipeline from top labs |
| 13 | **OSHA Inspections** | enforcedata.dol.gov + osha.gov/ords | Free | Safety incidents at gigafactories / fabs / launch pads |
| 17 | **FAA ADS-B Flight Tracking** | ADS-B Exchange Enterprise API | $1–5K/mo | eVTOL test flight cadence + corporate jet M&A travel |
| 25 | **Reddit Subreddit Mentions** | Apify Reddit Scraper | $200–500/mo | Community sentiment on fusion, nuclear, AI, defense |

### Tier 3 (enterprise — only if ROI is clear)

| # | Source | Cost | When it's worth it |
|---|---|---|---|
| 18 | **Commercial Satellite (Planet / Maxar / Umbra)** | $50–250K/yr | Only for top 20 strategic sites, not full universe |
| 20 | **Glassdoor / Blind Sentiment** | $500–2K/mo | Only top 50 high-priority companies; legal risk noted |

### Sources to skip (and why)

| # | Source | Why skip |
|---|---|---|
| 6 | DARPA program lists | Redundant — SAM.gov already captures 80% of performers |
| 7 | NOAA satellite tasking | Data isn't actually public; only licensee lists are |
| 8 | **ITAR / DSP-5 export licenses** | Not publicly available; FOIA denied under ITAR §126.10 |
| 16 | Port vessel manifests | Strictly inferior to bill-of-lading (#4) which has port-of-entry |
| 21 | CNIPA direct | Use Google Patents BigQuery public dataset instead (free) |
| 22 | Indian Patent Office + ONDC | Low frontier-tech signal; ONDC is not a data feed |

### The "new information" that came out of this research

Three data sources I underweighted initially:

1. **Wayback Machine / Common Crawl** (#19) — I had it as "Common Crawl" at tier 2. It's actually tier 1 crown-jewel material because website diffs catch exec departures, pivots, customer wins, and hiring trends across all 868 companies for ~$0 marginal cost.

2. **YouTube captions** (#24) — Completely missed in my first draft. Free, massive, unique. GTC keynotes name partners who don't yet appear in structured data anywhere.

3. **Interconnection.fyi already exists** — I thought you'd have to build the ISO queue aggregator. Interconnection.fyi has already done it for free. This makes FERC queue tracking a 1-day integration, not a 4-week build.

Two I overweighted:

1. **ITAR / DSP-5** — Sounds sexy but genuinely is not public. Remove from pipeline list.

2. **Port manifests** — Redundant with the bill-of-lading feed.

---

_Next step: decide which 4 shippables for Q2 and I'll scope out each one with concrete data-model + UX + implementation plan._
