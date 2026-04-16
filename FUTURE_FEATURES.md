# Future World-Class Features — The Trust Tier

Every idea here is modeled on what already works: **Map, Company Database, Talent, Gov Radar**. The pattern: pull hard-to-find data from an **authoritative source**, surface it in a way investors can't get elsewhere, link every data point back to the primary source so users can verify.

Rule for adding anything: if the primary source isn't a government API or a company's own official data endpoint, don't build it.

---

## Tier 1 — Authoritative, High-Signal, Low-Effort

### 1. SEC Form 4 Insider Activity Tracker
**Source:** SEC EDGAR Form 4 filings (free API)
**What it shows:** Every insider buy/sell at frontier tech public companies (PLTR, RKLB, OKLO, IONQ, etc.) with trend analysis — is the CEO buying or selling? What's the pattern?
**Why it matters:** Insiders know more than outsiders. Net selling before an earnings miss is a leading indicator. Net buying when stock is beaten down is bullish.
**Existing data:** `data/sec_filings_auto.js` already exists but Form 4 isn't surfaced separately.
**Dashboard page:** `insiders.html` — ranked by net insider flow last 30/90/180 days.

### 2. Clinical Trials Radar (Biotech)
**Source:** ClinicalTrials.gov API (free, authoritative — NIH)
**What it shows:** Active clinical trials at tracked biotech companies (Recursion, Tempus, etc.) with phase, enrollment, primary completion date, sponsor.
**Why it matters:** Trial milestones move stock prices. Knowing when Phase 3 readout is due is alpha.
**Existing data:** `data/clinical_trials_active.json` already populated (!) — just not surfaced.
**Dashboard page:** Add a "Trial Calendar" section to `regulatory.html` sorted by upcoming readout dates.

### 3. USPTO Patent Velocity Leaderboard
**Source:** USPTO PatentsView API (free)
**What it shows:** Patent applications filed per company per quarter (leading indicator vs grants, which lag 18-24 months). Rank by velocity change.
**Why it matters:** Rising patent velocity = accelerating R&D = future moat. Decreasing velocity = complacency.
**Existing data:** `data/patent_intel_auto.js` is currently empty — populate with USPTO application data.
**Dashboard page:** Add to existing `#patent-intel` homepage section.

### 4. DoD SBIR/STTR Pipeline Tracker
**Source:** SBIR.gov API (free, federal)
**What it shows:** Which frontier tech cos have won Phase I/II/III SBIR awards. Phase III is leading indicator of prime contracts.
**Why it matters:** SBIR winners often become DoD prime vendors 2-3 years later. This catches them early.
**Existing data:** `data/sbir_awards_auto.js` likely exists. Verify + surface.
**Dashboard page:** New section on `govradar.html` — "SBIR Pipeline" ranked by Phase III potential.

### 5. FAA Type Certification Tracker (eVTOL / Supersonic / Drones)
**Source:** FAA Type Certification public data + press releases filed with FAA
**What it shows:** Certification progress for Joby, Archer, Boom, Hermeus, drone companies. Which stage of cert (G-1, TIA, production)?
**Why it matters:** FAA cert = regulatory moat. Getting closer to approval = stock catalyst.
**Existing data:** `data/faa_certification_auto.json` already exists.
**Dashboard page:** Strengthen the FAA section on `regulatory.html`.

### 6. NRC Advanced Reactor Licensing Tracker (SMR / Fusion)
**Source:** NRC.gov public licensing database
**What it shows:** Application status for Oklo, NuScale, TerraPower, Nano Nuclear, and others. Design certification, combined license, operating license stages.
**Why it matters:** Nuclear licensing is multi-year and binary — passing a milestone is a major catalyst.
**Existing data:** Need to add `fetch_nrc.py` script.
**Dashboard page:** `regulatory.html` NRC section.

---

## Tier 2 — Authoritative, Unique-to-Frontier-Tech

### 7. Defense Prime Supply Chain Map
**Source:** SAM.gov (already used) + FPDS subcontractor filings + press releases
**What it shows:** Visual graph of which frontier tech companies are in L3Harris, Raytheon, Lockheed Martin, Northrop Grumman, Boeing, General Dynamics supply chains.
**Why it matters:** A company selling to primes is durable revenue. Graph lets you see concentration risk and primes' R&D priorities.
**Existing data:** SAM.gov + subcontractor data; needs aggregation script.
**Dashboard page:** New `prime-chains.html` or section on `govradar.html`.

### 8. openFDA Regulatory Milestones Dashboard
**Source:** openFDA API (free, FDA)
**What it shows:** For biotech/med-device cos: IND filings, Fast Track designations, Breakthrough designations, PDUFA dates, approvals, rejections.
**Why it matters:** FDA actions are binary value events. Investors pay premium for visibility.
**Existing data:** `data/fda_actions_raw.json` exists.
**Dashboard page:** Add "PDUFA Calendar" to `regulatory.html` with upcoming dates.

### 9. NSF/NIH/DOE Research Grant Flow
**Source:** NIH Reporter API + NSF Award Search API + OSTI.gov (all federal, free)
**What it shows:** Federal research $ flowing into frontier tech companies and the universities that spawn them. Leading indicator 3-5 years out.
**Why it matters:** Most frontier tech is born in university labs funded by federal grants. Tracking grant flow shows where the next generation is being built.
**Existing data:** Partial — ARPA-E done, NIH/NSF need scripts.
**Dashboard page:** New section on `research.html`.

### 10. Space Launch Manifest Tracker
**Source:** FAA commercial space ops database + launch provider manifests (SpaceX, RocketLab, ULA, Blue Origin)
**What it shows:** Which private companies have payloads on upcoming launches. First-flight customers. Rideshare programs.
**Why it matters:** Launch = validation milestone. A new space co getting on a SpaceX rideshare is a credibility signal.
**Existing data:** None yet — needs `fetch_launches.py`.
**Dashboard page:** New `launches.html` or section on index.

---

## Tier 3 — Authoritative, High-Value-Add

### 11. Congressional Testimony & Hearing Tracker
**Source:** Congress.gov API (free, federal) + C-SPAN archives
**What it shows:** When frontier tech founders testify to Congress (AI Safety, space, defense, energy). Signal of policy influence.
**Why it matters:** Founders who testify often shape regulations that benefit them. Tracking who testifies = tracking who shapes the future.
**Existing data:** `data/congress_bills_auto.js` exists but hearings aren't tracked.
**Dashboard page:** Add to `regulatory.html` or `govradar.html` as "Congressional Testimony".

### 12. CFIUS / Export Control Watchlist
**Source:** BIS Entity List (Commerce Dept, free) + FIRRMA filings + Treasury sanctions
**What it shows:** Which frontier tech companies face export controls, CFIUS review, or sanctions impact. Chinese investor exposure.
**Why it matters:** Export controls can kill a revenue stream overnight. Knowing which cos face risk = alpha.
**Existing data:** None — needs BIS scraper.
**Dashboard page:** New section on `govradar.html` as "Geopolitical Risk".

### 13. University Spinout Radar
**Source:** AUTM (Association of University Technology Managers) data + university TTO filings + state registry
**What it shows:** New startups spun out of Stanford, MIT, Caltech, UW, CMU frontier labs in the last 12 months. Pre-seed discovery.
**Why it matters:** Every major frontier tech company started as a university spinout. Catching them at day zero is the ultimate deal flow.
**Existing data:** Partial — `discovered_companies.json` exists.
**Dashboard page:** New section under Talent or dedicated `spinouts.html`.

### 14. Federal Budget Bills Tracker (Frontier-Tech-Relevant)
**Source:** Congress.gov API + appropriations bill text
**What it shows:** Which federal R&D line items affect frontier tech. CHIPS Act disbursements, DOE loan guarantees, DoD R&D earmarks, etc.
**Why it matters:** Federal $ flowing into a sector = tailwind for companies in it. Budget process is public but opaque; making it searchable is valuable.
**Existing data:** `data/congress_bills_auto.js` — needs richer tagging.
**Dashboard page:** Strengthen the "Budget Signals" section on `govradar.html`.

### 15. Executive Hiring Tracker (via LinkedIn + SEC Form 8-K)
**Source:** SEC 8-K filings (Form 5.02 executive appointments) + public LinkedIn (official API or scraper)
**What it shows:** When frontier tech companies hire senior execs from top competitors. Palantir CEO to SpaceX? NASA engineer to Oklo? These moves predict strategy shifts.
**Why it matters:** C-suite moves are leading indicators of strategy changes. Public companies must file 8-K; private cos show on LinkedIn.
**Existing data:** Partial — `sec_filings_auto.js` has 8-Ks but not parsed for exec moves.
**Dashboard page:** New section on `jobs.html` under Talent Intelligence.

---

## Implementation Priority

**Build order (ROI × effort):**

1. Clinical Trials Radar — data already exists, just surface it on `regulatory.html` (1 day)
2. FAA Type Certification Tracker — data exists, needs UI (1 day)
3. SEC Form 4 Insider Activity — API is free, need new fetch script (2 days)
4. USPTO Patent Velocity — fix empty pipeline first (2-3 days)
5. SBIR/STTR Pipeline — data probably exists, verify + surface (1-2 days)
6. PDUFA Calendar (FDA actions) — data exists, needs UI (1 day)
7. Defense Prime Supply Chain — new aggregation logic (5-7 days)
8. Executive Hiring Tracker — SEC 8-K parsing + LinkedIn (5 days)
9. University Spinout Radar — data partially exists (3-5 days)
10. NSF/NIH Grant Flow — need new scripts (3-4 days)
11. NRC Reactor Licensing — need NRC scraper (2-3 days)
12. Space Launch Manifest — need FAA integration (3-4 days)
13. Congressional Testimony — API integration (2 days)
14. CFIUS/Export Control — new scraper for BIS (3-5 days)
15. Federal Budget Tracker — improve existing data (3-4 days)

---

## Rules for Future Features

**✅ DO:**
- Link every data point to its primary source (SEC filing URL, SAM.gov notice ID, USPTO patent number, etc.)
- Show "last updated" timestamp per record
- Include a "Source:" badge on every rendered item
- Cap data freshness age — stale data should be flagged

**❌ DON'T:**
- Build features that require RSS text matching or company-name string extraction
- Build "predictive scores" or heuristic rankings unless validated externally
- Pull data that can't be traced back to a single authoritative endpoint
- Show speculation as fact — label it "analyst view" or hide it

---

## Current Trust Tier (as of Round 5)

### Verified Primary Sources (keep featuring)
- Company Database (SECTORS, manual curation + Crunchbase reference) → Map
- Stock Prices (Yahoo Finance API) → Company cards + War Room
- SAM.gov Contracts (federal) → Gov Radar + War Room
- SEC EDGAR Filings (federal) → Gov Radar
- USPTO Patents (federal) → Patent section
- Greenhouse/Lever/Ashby Jobs (direct company APIs) → Talent
- ClinicalTrials.gov → Regulatory page
- ARPA-E / NIH / DOE grants (federal) → Research
- Revenue Intel — SEC 10-K/10-Q only (not reported estimates)

### Removed in Round 5 (unreliable)
- Capital Intelligence / Recent Funding Rounds (RSS-parsed amounts)
- Intelligence Hub Alerts (RSS-matched news)
- Predictive Analytics (arbitrary heuristics)
- War Room "Biggest Deals" (RSS-parsed amounts)
- Deal Flow / Investor Screener page (heuristic scoring)
