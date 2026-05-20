# Company Facts Verification Report

**Generated:** 2026-05-20T08:54:53+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 29 companies  

**New Claude extractions this run:** 28  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 19 | 66% |
| 🔧 Changes proposed | 10 | 34% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (10 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Colossal Biosciences

- **`location`:** `Dallas, TX` → `Dallas, Texas`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Colossal_Biosciences)

  **Notes:** Database entry valuation of $1.5B is outdated. Wikipedia confirms Series C funding of $200M in January 2025 brought valuation to $10.2B, making it Texas' first decacorn. Total raised of $435M confirmed as of January 2025. Company also acquired ViaGen Pets in November 2025 and launched Colossal Australia through TIGRR Lab acquisition in August 2025.

### Dust

- **`totalRaised`:** `$70M+` → `$40M`  
  Sources: [news (Sifted)](https://sifted.eu/articles/dust-series-b-40m/)
- **`investors`:** `[]` → `['Sequoia']`  
  Sources: [news (Sifted)](https://sifted.eu/articles/dust-series-b-40m/)

  **Notes:** Source 3 (Sifted) headline confirms Series B of $40M backed by Sequoia. Database entry claimed '$70M+' total raised, but only $40M Series B is verified in sources. Sources 0, 1, 2 do not contain information about Dust company; source 0 is Wikipedia article about dust particles, sources 1-2 are about other companies (Dunia Innovations, Mach Industries).

### Fervo Energy

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [company_website](https://fervoenergy.com)

  **Notes:** Company went public on May 17, 2026 (Nasdaq debut) raising $1.89B in IPO proceeds per source 0. Wikipedia source 2 indicates company status as 'Private' but this appears to predate the May 2026 IPO announcement found in source 0. Most recent Series E funding of $462M in November 2025 mentioned in source 2.

### Fractile

- **`location`:** `London, UK` → `Bristol, UK`  
  Sources: [company_about](https://fractile.com/about)

  **Notes:** Source 2 (Wikipedia) is a redirect to 'Quantile' statistical concept and is not relevant to the company. Location identified as Bristol from team page; sources also mention London office but Bristol is listed first as primary location.

### Gecko Robotics

- **`founder`:** `Jake Loosararian` → `Jake Loosararian, Troy Demmer`  
  Sources: [company_about](https://geckorobotics.com/about-us)
- **`fundingStage`:** `Series C` → `Series D`  
  Sources: [company_about](https://geckorobotics.com/about-us)
- **`totalRaised`:** `$120M+` → `$125M`  
  Sources: [company_about](https://geckorobotics.com/about-us)

  **Notes:** Most recent funding round is Series D in June 2025 for $125M at $1.25B valuation. Company operates internationally with offices in Houston, Boston, New York City, Washington DC, and Abu Dhabi.

### Nuro

- **`fundingStage`:** `Series G` → `Series E`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Nuro)

  **Notes:** Company pivoted from autonomous delivery vehicle manufacturing to licensing its Level 4 autonomy technology (Nuro Driver) in September 2024. Series E round opened in April 2025 at $106M and closed in August 2025 with additional $97M funding, totaling $203M at $6B valuation.

### OpenAI

- **`founder`:** `Sam Altman, Greg Brockman, Ilya Sutskever` → `Elon Musk, Sam Altman, Ilya Sutskever, Greg Brockman, Trevor`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/OpenAI)

  **Notes:** Wikipedia indicates OpenAI was founded as a nonprofit in December 2015, with a for-profit subsidiary created in 2019. A 2025 restructuring converted the subsidiary into a PBC 26% owned by the nonprofit. October 2025 share sale valued company at $500 billion. Microsoft investment cited as 'over $13 billion' historically; Wikipedia notes Microsoft owns 27% post-restructuring.

### Shield AI

- **`location`:** `San Diego, CA` → `San Diego, California, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Shield_AI)

  **Notes:** Gary Steele became CEO on March 12, 2025, replacing Ryan Tseng who became Chief Strategic Officer. Wikipedia source indicates Series G funding of $1.5B announced in March 2026 at $12.7B post-money valuation (most recent and specific valuation available).

### SpaceX

- **`fundingStage`:** `Series G` → `Pre-IPO`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Source [0] is a domain-for-sale page and provides no company information. Source [2] is a news article about xAI and IPO concerns, not a primary source for company facts. Wikipedia source [1] states SpaceX is expected to have an IPO in 2026 and was valued at $800 billion in a 2025 share offer. Founded date confirmed as March 14, 2002 in El Segundo, California, with headquarters now at Starbase, Texas.

### X-Energy

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [company_website](https://x-energy.com)

  **Notes:** Source [0] confirms IPO announcement (Apr 15, 2026) and pricing announcement (Apr 23, 2026). Database entry claims about Amazon funding ($500M), Pentagon/Air Force contracts, UK deployment, founder name (Kam Ghaffarian), founding year (2009), total_raised ($1.1B+), and valuation ($2B+) could not be verified from provided sources.

---

## ✅ Cleared (19 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Anthropic
- Cerebras
- Cohere
- Destinus
- Deterrence
- Galvanick
- H Company
- Hidden Level
- IonQ
- Karman Industries
- Mach Industries
- Pivotal
- Quantinuum
- Rivian
- Solugen
- Space Forge
- Standard Nuclear
- Waymo
- xAI


---

*Generated by `scripts/generate_verification_report.py` on 2026-05-20T08:54:54+00:00*