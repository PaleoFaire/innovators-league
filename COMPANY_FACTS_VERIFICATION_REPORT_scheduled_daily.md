# Company Facts Verification Report

**Generated:** 2026-05-08T07:19:03+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 39 companies  

**New Claude extractions this run:** 38  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 24 | 62% |
| 🔧 Changes proposed | 15 | 38% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (15 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Alpha School

- **`location`:** `Austin, TX` → `Austin, Texas, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Alpha_School)
- **`fundingStage`:** `Private (self-funded)` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Alpha_School)

  **Notes:** Wikipedia source (source 2) lists 13 campuses as of April 2026 across Arizona, California, Florida, New York, Texas, and Virginia. Wikipedia notes that tuition ranges from $10,000 to $75,000 per year. Joe Liemandt is listed as principal in Wikipedia. Source 3 (TechCrunch article) is about OpenAI and does not contain information about Alpha School. The database entry mentions a '$1B Liemandt commitment' but this cannot be verified in the provided sources as funding raised.

### Anysphere

- **`totalRaised`:** `$3.3B+` → `$3.2B+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Anysphere)

  **Notes:** Total raised calculated from verified funding rounds: $8M seed (Oct 2023) + $60M Series A + $900M Series C (June 2025) + $2.3B Series D (Nov 2025) = $3.268B. Wikipedia also references April 2026 xAI deal discussion but that is outside the current date context. Co-founder Arvid Lunnemark departed in October 2025 to found Integrous Research.

### Astranis

- **`location`:** `San Francisco, California` → `San Francisco, California, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Astranis)

  **Notes:** Founded October 20, 2015. Company is part of Y Combinator Winter 2016 cohort. First MicroGEO satellite (Arcturus) launched April 30, 2023. As of the website copyright year (2026), company appears to have 5 satellites on orbit. Source [3] mentions $450M in equity and debt financing but date and stage context unclear, so not included in total_raised field. Valuation of $3.5B from database entry could not be verified in provided sources.

### Blue Origin

- **`location`:** `Kent, WA` → `Kent, Washington, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Blue_Origin)

  **Notes:** Leadership change in September 2023: Dave Limp appointed as CEO to succeed Bob Smith. New Glenn achieved first successful orbital launch on January 16, 2025. Company paused New Shepard tourism launches in January 2026 to focus on Artemis lunar landing efforts.

### Fervo Energy

- **`fundingStage`:** `IPO` → `Pre-IPO`  
  Sources: [company_website](https://fervoenergy.com)

  **Notes:** Source [0] indicates IPO filing announced April 17, 2026 and IPO launch announced May 4, 2026, making current status Pre-IPO rather than Public. Most recent funding: $462M Series E in November 2025 (source [2]).

### Groq

- **`location`:** `Mountain View, CA` → `Mountain View, California, US`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Groq)
- **`fundingStage`:** `Series E` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Groq)

  **Notes:** In December 2025, Nvidia agreed to license Groq's AI inference technology for approximately US$20 billion in a non-exclusive licensing deal; Groq founder Jonathan Ross and president Sunny Madra would join Nvidia as part of the agreement, but Groq stated it would continue to operate as an independent company. Most recent funding was $750 million raised in September 2025 (mentioned in source 0), but this is newer than the $2.8B Series D valuation from August 2024.

### Hugging Face

- **`location`:** `Manhattan, NY` → `Manhattan, New York City`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Hugging_Face)

  **Notes:** Wikipedia source indicates 250 employees as of 2025. Company acquired Pollen Robotics in April 2025. Source [0] shows 2M+ models and 500k+ datasets available on platform (current counts differ from database entry's 500K+ models and 100K+ datasets). No Series stage information found in sources. No total_raised or valuation figures found in provided sources.

### OpenAI

- **`founder`:** `Sam Altman, Greg Brockman, Ilya Sutskever` → `Elon Musk, Sam Altman, Ilya Sutskever, Greg Brockman, Trevor`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/OpenAI)

  **Notes:** In October 2025, OpenAI conducted a $6.6 billion share sale valuing the company at $500 billion (source 2). The company transitioned to a for-profit capped entity in 2019 and underwent a 2025 restructuring converting the subsidiary into a public benefit corporation (source 2). Wikipedia lists 11 founders; database entry listed 3.

### Palantir

- **`location`:** `Miami, FL` → `Miami, Florida, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Palantir)
- **`fundingStage`:** `Series A` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Palantir)

  **Notes:** Company is publicly traded on Nasdaq (PLTR). Wikipedia source is dated May 6, 2026 (23 years after founding on May 6, 2003). Current database entry lists location as Miami, FL (verified), but stage as 'Series A' which is contradicted by public company status in source. Valuation and total_raised fields cannot be verified from provided sources as specific current figures are not stated.

### Percepto

- **`location`:** `Modi'in, Israel` → `Israel`  
  Sources: [company_about](https://percepto.co/about)

  **Notes:** Source [1] explicitly names all four co-founders with their titles and background. Source [1] states company was 'co-founding Percepto in 2014.' Location identified as Israel based on team presence in company description and founder backgrounds (Ben-Gurion University, Israeli Air Force). No specific funding stage, total raised amount, valuation, or investor information found in provided sources.

### Quantum Motion

- **`fundingStage`:** `Series A` → `Series C`  
  Sources: [news (Tech.eu)](https://tech.eu/2026/05/07/uk-quantum-outfit-quantum-motion-run-on-silicon-chips-raises-160m/) · [news (Sifted)](https://sifted.eu/articles/quantum-motion-series-c/)
- **`totalRaised`:** `$60M+` → `$160M`  
  Sources: [news (Tech.eu)](https://tech.eu/2026/05/07/uk-quantum-outfit-quantum-motion-run-on-silicon-chips-raises-160m/) · [news (Sifted)](https://sifted.eu/articles/quantum-motion-series-c/)

  **Notes:** Database entry listed Series A stage and $60M+ raised; sources confirm Series C with $160M raised. Founders John Morton (Founder, CTO) and Simon Benjamin (Founder, CSO) verified from company about page.

### Rocket Lab

- **`location`:** `Long Beach, CA` → `Long Beach, California, USA`  
  Sources: [company_about](https://www.rocketlabcorp.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Rocket_Lab)

  **Notes:** Founded in Auckland, New Zealand in June 2006; moved to United States in 2013 and established headquarters in Huntington Beach, California before relocating to Long Beach in 2020. Company went public on Nasdaq in August 2021 via SPAC merger. Electron is described as 'second most frequently launched U.S. rocket' (source 1). Wikipedia reports over 75 completed missions as of January 2026. Multiple acquisitions completed: Sinclair Interplanetary (2020), Advanced Solutions Inc and Planetary Systems Corporation (2021), SolAero (2022), Geost (2025), and Mynaric AG (2026).

### SpaceX

- **`fundingStage`:** `Series G` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Wikipedia indicates SpaceX is expected to have an IPO in 2026. Database entry claims 'Series G' stage, but source [1] describes SpaceX as 'private' with no mention of funding rounds. Database entry valuation ($800B) is supported by source [1] which states '2025 offer to buy internal shares valued SpaceX at $800 billion.' Database entry claims $10B+ raised but this cannot be verified from sources; SEC Form D [5] shows only a single $9.7M filing from 2026. Founded date March 14, 2002 per source [1], though database lists only 2002.

### Starcloud

- **`location`:** `Redmond, WA` → `Redmond, Washington, USA`  
  Sources: [company_website](https://www.starcloud.com) · [wikipedia](https://en.wikipedia.org/wiki/Starcloud)
- **`fundingStage`:** `SPAC` → `Series A`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starcloud)

  **Notes:** Company was originally founded as 'Lumen Orbit' in El Segundo, California in January 2024, then relocated to Redmond, Washington in February 2024, and rebranded to 'Starcloud' in March 2025 following a legal challenge from Lumen Technologies. Became fastest unicorn in Y Combinator history, reaching $1.1B valuation 17 months after completing the program. Series A announced March 30, 2026.

### Thinking Machines Lab

- **`location`:** `San Francisco, CA` → `San Francisco, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Thinking_Machines_Lab)

  **Notes:** Wikipedia confirms founding in February 2025. Barret Zoph and Luke Metz departed in January 2026 to return to OpenAI. In March 2026, announced strategic partnership with Nvidia involving deployment of one gigawatt of Vera Rubin computing capacity.

---

## ✅ Cleared (24 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Andromeda Surgical
- Anthropic
- Astera Labs
- Daylight Computer
- Deterrence
- Durin
- Dust
- Galvanick
- Gecko Robotics
- HEO
- Hidden Level
- ICON
- Karman Industries
- Kyutai
- Ouster
- Photonic Inc
- Pivotal
- QuantWare
- Rebellions
- Rivian
- Solugen
- True Anomaly
- ideaForge
- xAI


---

*Generated by `scripts/generate_verification_report.py` on 2026-05-08T07:19:03+00:00*