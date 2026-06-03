# Company Facts Verification Report

**Generated:** 2026-06-03T10:46:53+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 37 companies  

**New Claude extractions this run:** 37  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 21 | 57% |
| 🔧 Changes proposed | 16 | 43% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (16 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Astera Labs

- **`location`:** `San Jose, CA` → `San Jose, California, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Astera_Labs)

  **Notes:** Company went public on Nasdaq (ticker: ALAB) in March 2024. Wikipedia source indicates initial founding location was Santa Clara, California in 2017, with headquarters later relocated to San Jose in June 2025. Sources 3 and 4 are unrelated news articles and were not used for verification.

### Axiom Space

- **`location`:** `Houston, TX` → `Houston, Texas, United States`  
  Sources: [company_about](https://axiomspace.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Axiom_Space)
- **`fundingStage`:** `Series C` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Axiom_Space)

  **Notes:** Source [0] announces $350M financing secured February 12, 2026. Source [2] reports December 2025 definitive agreement for $100M equity investment from 4iG Group in two tranches through March 2026. Valuation not found in sources. Michael Suffredini served as CEO and President until 2024; Jonathan W. Cirtain is current CEO as of source [1].

### Blue Origin

- **`location`:** `Kent, WA` → `Kent, Washington, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Blue_Origin)

  **Notes:** Database entry lists total_raised as $10B+ and valuation as $30B+, but these figures are not mentioned in provided sources. CEO is Dave Limp (as of September 2023). Company paused New Shepard tourism launches in January 2026 to focus on Artemis lunar landing efforts. New Glenn experienced catastrophic explosion on May 28, 2026 during static fire test.

### Deterrence

- **`founder`:** `Dhruva Rajendra, Henry Olgers` → `Dhruva Rajendra, Brian Jones, Henry Olgers`  
  Sources: [company_about](https://deterrence.com/about)
- **`founded`:** `2023` → `2024`  
  Sources: [company_about](https://deterrence.com/about)

  **Notes:** Database entry listed founded year as 2023, but source [1] explicitly states company was 'Founded' in 2024. Source [1] identifies three founders (Dhruva Rajendra, Brian Jones, Henry Olgers); database entry listed only two (Dhruva Rajendra, Henry Olgers) and omitted Brian Jones. Location (Fremont, CA) and funding details from database entry could not be verified in provided sources. Sources [2] and [3] are about nuclear deterrence policy, not this company.

### Fervo Energy

- **`location`:** `Houston, TX` → `Houston, Texas, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fervo_Energy)
- **`totalRaised`:** `$1.89B` → `$1.5B+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fervo_Energy)

  **Notes:** Wikipedia lists company as Private, contradicting database entry stating IPO stage. Sources [1] and [2] reference IPO but provide no detail in provided excerpts. Most recent funding was Series E ($462M) in November 2025 led by B Capital. Database entry claims $1.89B total raised; Wikipedia states 'over $1.5 billion in equity, debt and grant funding' as of the Series E announcement.

### Focused Energy

- **`totalRaised`:** `$80M+` → `$240M`  
  Sources: [news (TechCrunch)](https://techcrunch.com/2026/06/02/focused-energy-raises-whopping-240m-series-a-for-laser-powered-fusion-tech/)

  **Notes:** Only one source provided; insufficient to verify founders, location, founded_year, investors, website, or description. The $240M figure from source [0] contradicts the database entry of '$80M+'. Source [0] headline explicitly states '$240M Series A'.

### Impulse Space

- **`location`:** `Redondo Beach, CA` → `Redondo Beach, California, United States`  
  Sources: [company_about](https://impulsespace.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Impulse_Space)
- **`fundingStage`:** `Series C` → `Series D`  
  Sources: [company_about](https://impulsespace.com/about)
- **`totalRaised`:** `$525M` → `$1.025B`  
  Sources: [company_about](https://impulsespace.com/about) · [news (SpaceNews)](https://spacenews.com/impulse-space-raises-500-million/)

  **Notes:** Series D funding of $500M was raised in June 2026 (per source [1] press release dated JUN 3 2026). Total raised calculation: $30M seed (2022) + $45M Series A (2023) + $150M Series B (2024) + $300M Series C (2025) + $500M Series D (2026) = $1.025B. Database entry listed $300M Series C as most recent but sources indicate Series D occurred in 2026.

### Observable Space

- **`totalRaised`:** `$20M+` → `$90M`  
  Sources: [news (SpaceNews)](https://spacenews.com/observable-space-raises-90-million-and-wins-space-force-contract-for-optical-systems/)

  **Notes:** Only one source provided. Unable to verify: founders (Dan Roelker, Rick Hedrick), location (Los Angeles, CA), founded year (2025), current stage (Series A), or investors. Database entry claims $20M+ but source states $90M raised—using verified figure from source.

### Oxford Quantum Circuits

- **`fundingStage`:** `Series B` → `Series C`  
  Sources: [company_website](https://oxfordquantumcircuits.com) · [news (Sifted)](https://sifted.eu/articles/oxford-quantum-circuits-series-c/)
- **`totalRaised`:** `$100M+` → `$350M`  
  Sources: [news (Sifted)](https://sifted.eu/articles/oxford-quantum-circuits-series-c/)

  **Notes:** Source [2] mentions £260M funding round (approximately $330M USD equivalent), but source [3] (more recent, Sifted) reports $350M Series C, which is preferred as most specific and recent. Database entry mentioned Ilana Wisby stepping down as CEO in May 2024 and Gerald Mullally as interim CEO, but these details cannot be verified from provided sources.

### Palantir

- **`location`:** `Miami, FL` → `Miami, Florida, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Palantir)

  **Notes:** Source [1], [2], and [3] are about unrelated companies (Vast, Impulse Space) and contain no information about Palantir. Only source [0] (Wikipedia) provides verified information about Palantir. Total raised amount and current valuation cannot be verified from provided sources.

### Rivian

- **`location`:** `Irvine, CA` → `Irvine, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Rivian)

  **Notes:** Wikipedia states company was 'founded in Rockledge, Florida in 2009' but is now 'based in Irvine, California.' Founded as Mainstream Motors, renamed to Avera Automotive, then Rivian Automotive in 2011. Current database entry lists Irvine as location; Wikipedia confirms this is current headquarters. IPO occurred November 10, 2021 at $78.00 per share, valued at $66.5 billion initially. Ford reduced stake from 12% to approximately 1.6% by end of 2022.

### Skeleton Technologies

- **`founder`:** `Taavi Madiberk` → `Oliver Ahlberg, Taavi Madiberk, Jaan Leis, Anti Perkson`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Skeleton_Technologies)

  **Notes:** Sources 0 and 1 are domain sale pages for skeletontechnologies.com and do not contain company information. All verified information extracted from Wikipedia source [2]. The most recent financing mentioned in Wikipedia is 108 million euros raised in 2023 from Siemens, Marubeni, and CBMM, but this is described as part of scale-up rather than a defined funding round stage.

### Space Forge

- **`location`:** `Cardiff, UK` → `Cardiff, United Kingdom`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Space_Forge)

  **Notes:** Series A funding of £22.6 million announced in July 2024 per Wikipedia. ForgeStar-0 failed to achieve orbit on 9 January 2023; ForgeStar-1 successfully launched 27 June 2025.

### SpaceX

- **`location`:** `Starbase, TX` → `Starbase, Texas, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)
- **`fundingStage`:** `Series G` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Source 0 is a domain sales page and provides no company information. Source 1 (Wikipedia) states SpaceX 'is expected to have an initial public offering (IPO) in 2026' and was 'valued SpaceX at $800 billion' based on a 2025 share offer. Current database entry lists 'Series G' stage and '$10B+' raised, but sources do not specify funding stage or total capital raised with sufficient detail to verify these claims.

### Varda Space Industries

- **`location`:** `El Segundo, CA` → `El Segundo, California, United States`  
  Sources: [company_website](https://varda.com) · [company_about](https://varda.com/company) · [wikipedia](https://en.wikipedia.org/wiki/Varda_Space_Industries)
- **`fundingStage`:** `Series C` → `Series B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Varda_Space_Industries)

  **Notes:** Wikipedia indicates Series B funding of $90M announced in April 2024. Database entry lists $187M Series C, but this is not verified in provided sources. Most recent verified funding is $90M Series B from April 2024 per source [2].

### Waymo

- **`location`:** `Mountain View, CA` → `Mountain View, California`  
  Sources: [company_about](https://waymo.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Waymo)

  **Notes:** Wikipedia states Waymo was founded December 13, 2016 as an independent company (spun out from Google/Alphabet); traces origins to Stanford Racing Team (2004-2007) and Google Self-Driving Car Project (January 17, 2009). In February 2026, raised $16B at $126B valuation. As of March 2026, provides 500,000 paid rides per week with 200 million fully autonomous miles logged. The database entry claims 200K+ paid rides per week, but Wikipedia source states 500,000 paid rides per week as of March 2026.

---

## ✅ Cleared (21 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- AnySignal
- Crusoe Energy
- Divergent
- Durin
- Endurosat
- HEO
- Hadrian
- Humanoid
- Machina Labs
- Matic Robotics
- Orbital Composites
- Percepto
- Pivotal
- Quantum-Systems
- Rebellions
- Solid Power
- Standard Nuclear
- True Anomaly
- Vast
- X-Energy
- ideaForge


---

*Generated by `scripts/generate_verification_report.py` on 2026-06-03T10:46:53+00:00*