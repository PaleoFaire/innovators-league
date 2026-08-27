# Company Facts Verification Report

**Generated:** 2026-08-27T16:20:30+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 37 companies  

**New Claude extractions this run:** 37  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 29 | 78% |
| 🔧 Changes proposed | 8 | 22% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (8 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### 1X Technologies

- **`location`:** `Palo Alto, CA` → `Palo Alto, California, USA`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)
- **`totalRaised`:** `$1.1B` → `$123.5M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)

  **Notes:** Company was originally founded as Halodi Robotics in 2014 and rebranded to 1X Technologies in 2022. Series A2 funding of $23.5M in March 2023 led by OpenAI Startup Fund. Series B funding of $100M in January 2024 led by EQT Ventures. Total raised calculation: $23.5M + $100M = $123.5M. Wikipedia indicates main manufacturing in Hayward, California with additional operations in Moss, Norway. NEO pre-orders opened October 28, 2025 at $20,000 price point. Note: Source [0] and [1] appear to be for a different company (1X Technologies LLC, a wire and cable distributor in Sheridan, Wyoming founded in 2015) and are not relevant to the robotics company.

### Agility Robotics

- **`fundingStage`:** `Series E` → `Pre-IPO`  
  Sources: [company_website](https://agilityrobotics.com)

  **Notes:** Company announced merger with Churchill Capital Corp XI to go public (announced June 24, 2026, per source 0). Company rebranded as 'Agility' on March 5, 2026 (per source 2). Database entry lists multiple investors and $400M+ raised, but these specific figures could not be verified in provided sources.

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is publicly listed on NASDAQ under ticker NNE. Sources [0] and [1] are from company website only. Source [2] appears to be about a different company (Valar Atomics) and contains no information about NANO Nuclear Energy. Database entry claims about founder 'Jay Jiang Yu', founding year 2022, total raised $600M+, valuation $808M, and acquisition of ODIN to Cambridge AtomWorks could not be verified from provided sources.

### Proteus Space

- **`founder`:** `David Kervin (CEO, 20+ yrs govt contract bid/win/execution, ` → `David Kervin, Andrew Shapiro`  
  Sources: [company_about](https://proteus-space.com/about-us)

  **Notes:** Database entry references founders with detailed backgrounds (David Kervin as CEO with 20+ years government contract experience and military veteran status; Andrew Shapiro as CTO with 20 years at NASA JPL and involvement in Mars Perseverance Rover), but these details are not present in provided sources. Stage (Series A), total_raised ($14.4M), investors list, and valuation from database entry cannot be verified from sources provided. Source [2] is dated September 8th, 2026, which is a future date—likely a data error or placeholder.

### Q-CTRL

- **`founder`:** `Michael Biercuk` → `Michael J. Biercuk`  
  Sources: [company_about](https://q-ctrl.com/about)

  **Notes:** Founded year (2017) and location (Sydney, Australia) from database entry cannot be verified from provided sources. Source [2] is about Einride founders and is not relevant to Q-CTRL. Board of directors and advisory board members listed in source [1] but not classified as founders. No funding stage or total raised information found in provided sources.

### SpaceX

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Wikipedia source indicates IPO occurred on June 12, 2026, raising $86 billion. Source 0 lists Elon Musk with 42% equity and 82% voting control (article text shows 85% voting power via super-voting stock in one section, 82% in infobox). Alphabet Inc. listed as 4.19% equity holder. Database entry valuation of $1.65T and claim of 'preparing for IPO' are inconsistent with verified source stating IPO already occurred in June 2026.

### Starcloud

- **`fundingStage`:** `Seed` → `Series A`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starcloud)

  **Notes:** Company was originally founded as 'Lumen Orbit' in January 2024 in El Segundo, California and rebranded to Starcloud in March 2025 after a legal challenge from Lumen Technologies. Series A was announced on March 30, 2026, making it the fastest Y Combinator company to reach unicorn status (17 months after completing the program).

### Teralta

- **`location`:** `Burnaby, Canada` → `Burnaby, BC, Canada`  
  Sources: [company_about](https://teralta.com/about)

  **Notes:** Source [2] is about Motion (a robotics company) and is not relevant to Teralta. Only sources [0] and [1] contain verified information about Teralta. No co-founders beyond Simon Pickup are explicitly named as founders. Total raised ($15.8M) and valuation from database entry cannot be verified from provided sources. Current stage not disclosed in sources.

---

## ✅ Cleared (29 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- AnySignal
- Apptronik
- Astera Labs
- Aurora Innovation
- Base Power
- Bedrock Robotics
- Cognition
- Commonwealth Fusion Systems
- Destinus
- Deterrence
- Einride
- Galvanick
- Gecko Robotics
- Hadrian
- Humanoid
- Karman Industries
- Matter
- Neura Robotics
- Oklo
- Orbital Composites
- Photonic Inc
- Radiant
- Rebellions
- Sage Geosystems
- Solugen
- Together AI
- Valar Atomics
- Waymo


---

*Generated by `scripts/generate_verification_report.py` on 2026-08-27T16:20:30+00:00*