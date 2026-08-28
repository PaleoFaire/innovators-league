# Company Facts Verification Report

**Generated:** 2026-08-28T17:16:53+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 42 companies  

**New Claude extractions this run:** 42  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 35 | 83% |
| 🔧 Changes proposed | 7 | 17% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (7 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### 1X Technologies

- **`location`:** `Palo Alto, CA` → `Palo Alto, California, USA`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)
- **`fundingStage`:** `Pre-Seed` → `Pre-IPO`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)
- **`totalRaised`:** `$1.1B` → `$123.5M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)

  **Notes:** Company was originally founded as Halodi Robotics in 2014 and rebranded as 1X Technologies in 2022. Wikipedia states Series A2 funding of $23.5M in March 2023 and Series B funding of $100M in January 2024, totaling $123.5M verified. Wikipedia also reports the company was seeking $1B in new funding as of September 2025, but this is not confirmed as raised. Sources 0 and 1 appear to be for a different company (1X Technologies LLC, an electrical wire and cable distributor in Wyoming, founded 2015) and are not relevant to the robotics company.

### Agility Robotics

- **`fundingStage`:** `Series E` → `Pre-IPO`  
  Sources: [company_website](https://agilityrobotics.com)

  **Notes:** Company announced merger with Churchill Capital Corp XI to go public (announced June 24, 2026). On March 5, 2026, the company announced a rebrand as 'Agility' per Wikipedia source [2], though official sources still use 'Agility Robotics' as of July 2026. Database entry lists Series E stage and $400M+ raised, but these specific figures could not be verified from provided sources.

### Carbon Robotics

- **`location`:** `Seattle, WA` → `Seattle, Washington`  
  Sources: [company_about](https://carbonrobotics.com/about)

  **Notes:** Source [1] confirms founded 2018 and headquarters in Seattle, Washington. Source [1] states 'over $100M in annual revenue' but this is revenue, not funding raised. Series C stage and $177M total raised from database entry could not be verified in provided sources. Investor list from database could not be verified in provided sources.

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is listed on NASDAQ under ticker NNE. Sources describe it as 'the first nuclear microreactor company to be listed publicly in the U.S.' Database entry references ODIN sale to Cambridge AtomWorks and market cap of ~$1.2B (June 2026), but these claims cannot be verified from provided sources. Founder name 'Jay Jiang Yu' from database entry not found in sources. Founded year 2022 and fundraising amounts from database entry cannot be verified from provided sources.

### Q-CTRL

- **`founder`:** `Michael Biercuk` → `Michael J. Biercuk`  
  Sources: [company_about](https://q-ctrl.com/about)

  **Notes:** Location (Sydney, Australia) and founded year (2017) are from database reference but NOT verified in provided sources. Current stage, total_raised, valuation, and investors cannot be verified from provided sources. Source [2] is about Einride and does not contain Q-CTRL information.

### SpaceX

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Wikipedia source indicates SpaceX completed initial public offering on June 12, 2026, raising $86 billion, which was the largest IPO in history. The current database entry lists 'IPO' as stage and valuation of $1.65T, but no source provided supports the $1.65T valuation figure or confirms 'Preparing for IPO' status. Per sources, IPO has already occurred. Valuation field set to null as no specific valuation is cited in sources.

### Starcloud

- **`fundingStage`:** `Seed` → `Series A`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starcloud)

  **Notes:** Company was originally founded as 'Lumen Orbit' in January 2024 in El Segundo, California, then rebranded to Starcloud in March 2025 following a legal challenge from Lumen Technologies. Wikipedia source indicates Series A was announced on March 30, 2026, led by Benchmark and EQT Ventures. Became fastest unicorn in Y Combinator history at 17 months post-program completion.

---

## ✅ Cleared (35 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- AnySignal
- Apptronik
- Astera Labs
- Aurora Innovation
- Base Power
- Bedrock Robotics
- Cape
- Cognition
- Destinus
- Deterrence
- Einride
- Forterra
- Galvanick
- Gecko Robotics
- Hadrian
- Humanoid
- Karman Industries
- Matter
- Neura Robotics
- Oklo
- Orbital Composites
- Percepto
- Photonic Inc
- Proteus Space
- Radiant
- Rebellions
- Sage Geosystems
- Solugen
- Teralta
- *...and 5 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-08-28T17:16:54+00:00*