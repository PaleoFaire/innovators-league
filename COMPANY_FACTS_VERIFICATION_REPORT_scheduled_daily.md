# Company Facts Verification Report

**Generated:** 2026-05-19T08:59:34+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 24 companies  

**New Claude extractions this run:** 23  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 15 | 62% |
| 🔧 Changes proposed | 9 | 38% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (9 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### AST SpaceMobile

- **`location`:** `Midland, Texas, USA` → `Midland, Texas, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/AST_SpaceMobile)

  **Notes:** Founded as AST & Science LLC in May 2017; became publicly traded via SPAC merger in April 2021 on Nasdaq under ticker ASTS. Website listed as ast-science.com on Wikipedia, though company website header shows astspacemobile.com.

### Astrolab

- **`location`:** `Hawthorne, CA` → `Hawthorne, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Astrolab)

  **Notes:** Source [0] (company website) describes a different business (consulting/AI services) and does not match the aerospace company. Source [1] (Wikipedia) is the authoritative source for Astrolab aerospace. Company officially registered as 'Venturi Astrolab Inc.' per Wikipedia. Selected by NASA for Lunar Terrain Vehicle Services (LTVS) program in 2024 to support Artemis missions.

### Dust

- **`totalRaised`:** `$70M+` → `$60M+`  
  Sources: [news (Tech.eu)](https://tech.eu/2026/05/18/dust-raises-40m-series-b-to-build-the-multiplayer-operating-system-for-enterprise-ai/)
- **`investors`:** `[]` → `['Abstract', 'Sequoia', 'Snowflake', 'Datadog']`  
  Sources: [news (Tech.eu)](https://tech.eu/2026/05/18/dust-raises-40m-series-b-to-build-the-multiplayer-operating-system-for-enterprise-ai/)

  **Notes:** Source [0] is Wikipedia article about dust particles, not the company. Source [1] is about Stainless (different company), not Dust. Database entry claims $70M+ raised and founders Gabriel Hubert and Stanislas Polu, but these cannot be verified in provided sources. Series B amount verified as $40M with total raised over $60M.

### Fervo Energy

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [company_website](https://fervoenergy.com)

  **Notes:** Company went public on May 17, 2026 (per website newsroom). Wikipedia shows company status as 'Private' but website confirms IPO with article titled 'A Start-Up Aiming to Make Geothermal Energy Mainstream Goes Public' dated May 17, 2026 and 'Fervo Energy raises $1.89B in IPO: CEO on the company's Nasdaq debut'. Total funding exceeds $1.89B IPO as additional $462M Series E received November 2025 per Wikipedia.

### Nuro

- **`fundingStage`:** `Series G` → `Series E`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Nuro)

  **Notes:** Company pivoted from autonomous delivery vehicles to licensing business model in September 2024. Series E funding closed in August 2025 at $203M valuation of $6B. Partnership with Uber and Lucid Motors announced July 2025 for robotaxi deployment of 20,000+ vehicles.

### OpenAI

- **`founder`:** `Sam Altman, Greg Brockman, Ilya Sutskever` → `Elon Musk, Sam Altman, Ilya Sutskever, Greg Brockman, Trevor`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/OpenAI)

  **Notes:** Valuation updated to $500B based on October 2025 share sale (source 1). Founded as nonprofit in 2015; transitioned to capped for-profit in 2019; restructured in 2025 into for-profit public benefit corporation. Source 0 appears to be a placeholder/error page. Sources 2-4 relate to Musk lawsuit verdict but do not provide new company facts.

### SpaceX

- **`fundingStage`:** `Series G` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Source [1] indicates SpaceX is expected to have an IPO in 2026 and notes a 2025 offer to buy internal shares valued SpaceX at $800 billion. Current database entry claims 'Series G' stage and '$10B+' total raised, but these cannot be verified from provided sources. Database claims about 165 Falcon 9 launches in 2025, 81% of mass to orbit, 9M+ Starlink customers, and $1.5T valuation cannot be verified from provided sources.

### Tomorrow.io

- **`location`:** `Boston, MA` → `Boston, Massachusetts`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Tomorrow.io)
- **`totalRaised`:** `$200M+` → `$210M`  
  Sources: [news (SpaceNews)](https://spacenews.com/tomorrow-io-adds-35-million-to-deepsky-funding-round/)

  **Notes:** Company was formerly known as ClimaCell and rebranded to Tomorrow.io in March 2021. First satellite (Tomorrow-R1) launched April 15, 2023. Latest funding round of $210M includes $175M announced for DeepSky constellation plus additional $35M.

### X-Energy

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [company_website](https://x-energy.com)

  **Notes:** Source [0] confirms IPO announcement on Apr 15, 2026 and pricing announcement on Apr 23, 2026. Database entry claims cannot be verified from provided sources: founder name, location, founding year, total_raised, valuation, and specific details about Amazon funding, Pentagon/Air Force contracts, and UK deployment were not found in sources provided.

---

## ✅ Cleared (15 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Anthropic
- Atmo
- Cerebras
- Cohere
- Destinus
- Deterrence
- Galvanick
- Hidden Level
- IonQ
- Pivotal
- Quantinuum
- Rivian
- Standard Nuclear
- Waymo
- xAI


---

*Generated by `scripts/generate_verification_report.py` on 2026-05-19T08:59:34+00:00*