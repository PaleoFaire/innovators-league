# Company Facts Verification Report

**Generated:** 2026-08-26T05:41:13+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 33 companies  

**New Claude extractions this run:** 33  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 25 | 76% |
| 🔧 Changes proposed | 8 | 24% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (8 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### 1X Technologies

- **`location`:** `Palo Alto, CA` → `Palo Alto, California, USA`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)
- **`totalRaised`:** `$1.1B` → `$123.5M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)

  **Notes:** Company was founded as Halodi Robotics in 2014 and rebranded to 1X Technologies in 2022. Series A2 funding of $23.5M raised in March 2023; Series B funding of $100M raised in January 2024. Total verified raised is $123.5M ($23.5M + $100M). Source [0] and [1] describe a completely different company (wire and cable distributor founded in 2015, located in Sheridan, WY) and should not be used for this robotics company profile.

### Agility Robotics

- **`fundingStage`:** `Series E` → `Pre-IPO`  
  Sources: [company_website](https://agilityrobotics.com)

  **Notes:** Company announced merger with Churchill Capital Corp XI to go public (source 0, June 24, 2026). Company rebranded as 'Agility' on March 5, 2026 (source 2). Database entry lists Series E stage and $400M+ raised, but these figures could not be verified from provided sources.

### Matter

- **`website`:** `*(empty)*` → `https://matter.com`  
  Sources: [company_website](https://matter.com)
- **`investors`:** `[]` → `['Lowercarbon Capital', 'Bezos Expeditions', 'Mark Cuban', '`  
  Sources: [company_about](https://matter.com/team)

  **Notes:** Database entry lists founders (Adi Prasad, Charly Mwangi, Aish Varadhan, Aditya Ranjan) and location (Sunnyvale, CA) but these cannot be verified in provided sources. CEO listed as Vishnu Sridhar in source [1]. Founded year 2025 and Seed stage from database cannot be verified in sources. Sources [2] and [3] are not relevant to this company.

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is publicly listed on NASDAQ under ticker NNE. Sources confirm three reactor designs (KRONOS MMR, ZEUS, LOKI) in development. Source [2] appears to be about a different company (Valar Atomics) and is not relevant. Founder name 'Jay Jiang Yu' from database entry is not mentioned in provided sources. Founded year 2022, total raised $600M+, valuation $808M, and acquisition of ODIN to Cambridge AtomWorks from database entry could not be verified from sources provided.

### Pacific Fusion

- **`founder`:** `Eric Lander, Will Regan` → `Will Regan, Keith LeChien, Eric Lander, Carrie von Muench, L`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Pacific_Fusion)
- **`location`:** `Fremont, CA` → `Fremont, California, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Pacific_Fusion)

  **Notes:** Wikipedia lists five co-founders (Will Regan, Keith LeChien, Eric Lander, Carrie von Muench, Leland Ellison), while database entry lists only Eric Lander and Will Regan. Series A funding of $900M raised in 2024, led by General Catalyst. Eric Lander is founding CEO. In September 2025, company selected Mesa del Sol in Albuquerque, New Mexico for $1 billion research and manufacturing facility. In December 2025, opened first build center in Los Lunas, New Mexico.

### Proteus Space

- **`founder`:** `David Kervin (CEO, 20+ yrs govt contract bid/win/execution, ` → `David Kervin, Andrew Shapiro`  
  Sources: [company_about](https://proteus-space.com/about-us)

  **Notes:** Database entry references founders David Kervin and Andrew Shapiro with detailed backgrounds, but these names are not explicitly mentioned in provided sources as founders. Sources only confirm company founded 2021 in Los Angeles. Current stage, total raised, valuation, and investor list from database entry cannot be verified from provided sources.

### SpaceX

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** SpaceX completed IPO on June 12, 2026, raising $86 billion (largest IPO in history per source). Wikipedia source indicates Elon Musk owns 42% equity and controls 85% voting power (note: database entry states 82% voting control, but Wikipedia states 85%). Valuation field set to null as sources do not provide current valuation figure; database entry claims $1.65T but this is not supported by provided sources.

### Starcloud

- **`location`:** `Redmond, Washington` → `Redmond, Washington, US`  
  Sources: [company_website](https://www.starcloud.com) · [wikipedia](https://en.wikipedia.org/wiki/Starcloud)
- **`fundingStage`:** `Seed` → `Series A`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starcloud)

  **Notes:** Company was originally founded as 'Lumen Orbit' in January 2024 in El Segundo, California, and rebranded to Starcloud in March 2025 following a legal challenge from Lumen Technologies. Wikipedia source indicates the company became the fastest unicorn in Y Combinator history at 17 months post-program completion. Series A funding round announced March 30, 2026.

---

## ✅ Cleared (25 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- AnySignal
- Apptronik
- Astera Labs
- Aurora Innovation
- Base Power
- Commonwealth Fusion Systems
- Destinus
- Deterrence
- Einride
- Hadrian
- Harbinger
- Humanoid
- Neura Robotics
- Oklo
- Orbital Composites
- Parallel Systems
- Photonic Inc
- Radiant
- Rebellions
- Sage Geosystems
- Together AI
- Valar Atomics
- Waymo
- WeaveGrid


---

*Generated by `scripts/generate_verification_report.py` on 2026-08-26T05:41:13+00:00*