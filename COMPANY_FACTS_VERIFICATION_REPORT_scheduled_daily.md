# Company Facts Verification Report

**Generated:** 2026-08-12T06:21:49+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 45 companies  

**New Claude extractions this run:** 45  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 38 | 84% |
| 🔧 Changes proposed | 7 | 16% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (7 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Agility Robotics

- **`fundingStage`:** `Series D` → `Pre-IPO`  
  Sources: [company_website](https://agilityrobotics.com)

  **Notes:** Company announced merger with Churchill Capital Corp XI to go public (announced June 24, 2026, per source 0). Company rebranded as 'Agility' on March 5, 2026 (per source 2). Current CEO is Peggy Johnson (per source 1). Digit has commercial deployments with Amazon, Toyota, Mercado Libre, and GXO (per source 1).

### Isembard

- **`location`:** `London, UK` → `London, United Kingdom`  
  Sources: [company_website](https://isembard.com)

  **Notes:** Database entry lists Series A stage and $50M raised, but these claims cannot be verified from provided sources. Sources reference seed round of $9M (TechCrunch headline visible in source [1]) and £7m mentioned (The Telegraph headline in source [1]), but full details of either round are not provided in the source text. Founded year 2024 in database cannot be verified from sources. Team members listed in source [1] include Alexander Fitzgerald (CEO), Jack Williams, Tom Hall, Zoe Hatton, Rory Rose, and Justin Baucum, but only Alexander Fitzgerald is identified as founder/CEO.

### Joby Aviation

- **`location`:** `Santa Cruz, CA` → `Santa Cruz, California`  
  Sources: [company_about](https://jobyaviation.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Joby_Aviation)

  **Notes:** Company went public via SPAC on August 11, 2021 (NYSE: JOBY). Founded as Joby Aero on September 11, 2009. Recently announced acquisition of Resonant Sciences in August 2026 for $500M. Sources conflict on total_raised and valuation specifics, so those fields set to null. Database entry lists investors but sources do not provide comprehensive investor list with verification.

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is publicly listed on NASDAQ under ticker NNE. Sources [0] and [1] are duplicates of the same website content. Source [2] appears to be about a different company (Valar Atomics) and contains no information about NANO Nuclear Energy. Founder name 'Jay Jiang Yu' from database entry could not be verified in provided sources. Founded year, total raised, valuation, and investors could not be verified from sources provided.

### Proteus Space

- **`location`:** `Glendale, CA` → `Los Angeles, CA`  
  Sources: [news (SpaceNews)](https://spacenews.com/proteus-space-names-maj-gen-kim-crider-usaf-ret-to-board-of-directors/)

  **Notes:** Database entry references 'Glendale, CA' but source [2] (SpaceNews, dated August 11, 2026) states 'LOS ANGELES'. Database entry lists founders and investors, but these cannot be verified from provided sources. Database claims Series A stage and $14.4M raised, but no supporting evidence in sources. Source [1] mentions 'patent-pending' platform and M1 spacecraft with AFRL contract; Source [0] references MERCURY platform mentioned in database description but uses different terminology ('Protean Buses' instead).

### SpaceX

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** SpaceX completed initial public offering on June 12, 2026, raising $86 billion, which was the largest IPO in history according to source [0]. Wikipedia source indicates Elon Musk controls 85% voting power via super-voting stock (source [0] states 85%, though database entry states 82%). Valuation field marked null because source [0] does not specify a current valuation figure; the database entry claims $1.65T but this is not supported by provided sources.

### Zettascale

- **`founder`:** `Elias Almqvist (CEO; self-taught engineer, Chalmers Universi` → `Elias Almqvist, Prithvi Raj`  
  Sources: *(no sources cited)*

  **Notes:** Source [0] confirms company rebrand to Zettascale and mentions XPU chips for AI. Database entry claims Y Combinator S24 and founders Elias Almqvist and Prithvi Raj, but these details are not explicitly verified in provided sources. Source [1] is about Tesla/SpaceX Terafab and is not relevant to Zettascale. Founded year, total_raised, valuation, and specific founder details cannot be verified from sources provided.

---

## ✅ Cleared (38 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- 1X Technologies
- AbCellera
- Antares
- AnySignal
- Apptronik
- Astera Labs
- Atmo
- Atmos Space Cargo
- Base Power
- Cambridge Aerospace
- Cape
- Dawn Aerospace
- Deterrence
- Durin
- Firestorm Labs
- GrayMatter Robotics
- Hadrian
- Humanoid
- ICEYE
- ICON
- Kyoto Fusioneering
- Oklo
- Orbital Composites
- Path Robotics
- Percepto
- Photonic Inc
- PsiQuantum
- Quaise Energy
- Radiant
- Rebellions
- *...and 8 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-08-12T06:21:50+00:00*