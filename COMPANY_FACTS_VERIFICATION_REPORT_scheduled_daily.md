# Company Facts Verification Report

**Generated:** 2026-06-18T10:08:40+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 44 companies  

**New Claude extractions this run:** 44  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 33 | 75% |
| 🔧 Changes proposed | 11 | 25% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (11 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### AbCellera

- **`location`:** `Vancouver, Canada` → `Vancouver, British Columbia, Canada`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/AbCellera)

  **Notes:** Company is publicly traded on Nasdaq under ticker ABCL. In 2023, made strategic decision to shift focus from partnerships to advancing internal and co-development programs. Multiple clinical programs in development as of 2025 (ABCL635, ABCL575, ABCL688).

### Abridge

- **`founder`:** `Shiv Rao, Zack Lipton` → `Shiv Rao`  
  Sources: [company_about](https://abridge.com/about)

  **Notes:** Source [2] (Wikipedia) refers to a village in Essex, England—not the company. Only Shiv Rao explicitly named as 'CEO, Co-Founder' in source [1]; Zack Lipton from database entry is not mentioned in provided sources. Founded year, location, funding stage, total raised, valuation, and investor list could not be verified from these sources.

### AnySignal

- **`location`:** `El Segundo, CA` → `Los Angeles, CA`  
  Sources: [company_website](https://anysignal.com)

  **Notes:** Source [1] is about Dawn Aerospace, not AnySignal, and cannot be used. Database entry lists founders (John Malsbury, Ricky Medina, Jeffrey R Osborne), founded year (2022), stage (Series A), and total_raised ($34M+), but none of these are verifiable from the provided sources. Website content does not include founder names, founding year, funding stage, or investment amounts.

### Climeworks

- **`location`:** `Zurich, Switzerland` → `Zürich, Switzerland`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Climeworks)

  **Notes:** Wikipedia confirms founding in November 2009. Company operates Mammoth plant in Iceland (launched May 2024) with capacity to capture up to 36,000 tons of CO2 annually. Unicorn status achieved after April 2022 $650M funding round (per Wikipedia). Source [0] is company website with limited verifiable detail. Source [2] mentions Frontier carbon removal coalition but provides no company-specific financial data. Database entry claims Series F stage, $1B+ raised, and specific investors, but these cannot be verified from provided sources.

### Dawn Aerospace

- **`totalRaised`:** `$30M+` → `$25M`  
  Sources: [news (SpaceNews)](https://spacenews.com/dawn-aerospace-raises-25-million/)

  **Notes:** Company operates dual headquarters in Delft, Netherlands and Christchurch, New Zealand with 4 global locations. Wikipedia states $30M raised (ref 1 in Wiki citing NBR article) but SpaceNews source [3] reports $25M raised most recently. Using most recent specific figure from source [3]. Current stage unclear from sources - Wikipedia lists company as 'PrivateIndustry' (c. 2022) but no current Series funding stage explicitly stated in any source.

### Fervo Energy

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [company_website](https://fervoenergy.com)

  **Notes:** Wikipedia article (source 2) lists company as 'Private' but multiple sources (0, 2) reference IPO completion in May 2026. Wikipedia appears outdated; company website (source 0) newsroom confirms IPO with headlines dated May 17-18, 2026. Dr. Jack Norbeck identified as CTO in source 2.

### Graphyte

- **`founder`:** `Barclay Rogers` → `Bill Gates`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Graphyte)
- **`location`:** `Pine Bluff, AR` → `Pine Bluff, Arkansas`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Graphyte)
- **`totalRaised`:** `$57M` → `$30M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Graphyte)

  **Notes:** Wikipedia lists Bill Gates as founder/backer; database entry lists Barclay Rogers as founder. Wikipedia specifies $30M Series A in July 2024, contradicting database entry of $57M total raised. Database valuation of $200M could not be verified in sources. Source [2] is about Anthropic and does not contain relevant Graphyte information.

### Heirloom Carbon

- **`location`:** `Brisbane, CA` → `Central Valley, California`  
  Sources: [company_website](https://heirloomcarbon.com)

  **Notes:** Source [1] is about Anthropic, not Heirloom, and provides no verifiable information about Heirloom. Current database entry contains founder name, location (Brisbane, CA), founding year (2020), stage (Series B), and total_raised ($150M+) but none of these are supported by provided sources. Company website does not mention founder names, founding year, funding stage, or total capital raised.

### Relativity Space

- **`location`:** `Long Beach, CA` → `Long Beach, California, US`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Relativity_Space)

  **Notes:** Eric Schmidt replaced Tim Ellis as CEO in March 2025, taking a controlling interest. Company has contract backlog of over $2.9B as of March 2025. Founded year differs from database entry (2015 vs 2016); Wikipedia and database cite 2015. Database entry noted $1.6B in launch contracts; Wikipedia cites $2.9B+ in contract backlog as of March 2025 and source [1] mentions $3B+ in pre-sold launch contracts.

### SpaceX

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** IPO occurred on June 12, 2026. Wikipedia source dated as of May 2026 update. Database entry claims $1.5T valuation and IPO status, but sources only confirm $86B raised in IPO and public status; no valuation figure found in sources. Database entry lists 'IPO' as stage - corrected to 'Public' per schema requirements.

### Varda Space Industries

- **`fundingStage`:** `Series C` → `Series B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Varda_Space_Industries)

  **Notes:** Wikipedia indicates $90M Series B funding in April 2024. Database entry claims $187M Series C from Founders Fund and Khosla Ventures in 2025, but this is not verified in provided sources. Source [3] is unrelated to Varda (Jazz Pharmaceuticals/AbCellera deal) and was not used.

---

## ✅ Cleared (33 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- 1X Technologies
- Agility Robotics
- Andrenam
- Apptronik
- Arbor Energy
- Atom Bodies
- Built Robotics
- Cape
- CarbonCapture Inc.
- Charm Industrial
- Deterrence
- Dexterity
- Einride
- FleetZero
- Hadrian
- Harbinger
- Humanoid
- Mach Industries
- Mara
- Navier
- Orbital Composites
- PLD Space
- Palantir
- Percepto
- Saildrone
- Scale AI
- Standard Nuclear
- Tekever
- Tenstorrent
- Waymo
- *...and 3 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-06-18T10:08:40+00:00*