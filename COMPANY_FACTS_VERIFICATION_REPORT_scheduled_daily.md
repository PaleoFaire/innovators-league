# Company Facts Verification Report

**Generated:** 2026-09-10T09:31:18+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 38 companies  

**New Claude extractions this run:** 38  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 31 | 82% |
| 🔧 Changes proposed | 7 | 18% |
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

  **Notes:** Company was originally founded as Halodi Robotics in 2014 and rebranded as 1X Technologies in 2022. Total raised is sum of Series A2 ($23.5M in March 2023) and Series B ($100M in January 2024) as documented in Wikipedia. Sources [0] and [1] refer to a different company also named '1X Technologies' (a wire and cable distributor founded in 2015, located in Sheridan, Wyoming) and are not relevant to this robotics company.

### Agility Robotics

- **`fundingStage`:** `Series E` → `Pre-IPO`  
  Sources: [company_website](https://agilityrobotics.com)

  **Notes:** Company announced merger with Churchill Capital Corp XI to go public (announced June 24, 2026, confidential S-4 submission July 14, 2026). Company rebranded as 'Agility' on March 5, 2026. S-4 filing (source [4]) reports $1.8M revenue in 2025 and $140M operating loss, but specific funding amounts and valuation not disclosed in provided sources.

### Monumental

- **`founder`:** `Salar al Khafaji, Sebastiaan Visser` → `Salar, Sebas`  
  Sources: [company_about](https://www.monumental.co/about)
- **`totalRaised`:** `$32M` → `$60M+`  
  Sources: [company_about](https://www.monumental.co/about)

  **Notes:** Database entry listed total_raised as $32M; source [1] states $60M+, which is more recent and specific. Founder full names are given as 'Salar' and 'Sebas' in source [1]; full surname 'al Khafaji' and 'Visser' from database entry are not explicitly confirmed in sources. Current_stage not specified in any source.

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is publicly listed on NASDAQ under ticker NNE. Sources [0] and [1] are duplicative content from company website. Source [2] is about a different company (Valar Atomics) and contains no information about NANO Nuclear Energy. Database entry references founder 'Jay Jiang Yu', ODIN sale to Cambridge AtomWorks, founded year 2022, $600M+ raised, and $808M valuation—none of which are mentioned in provided sources, so these cannot be verified.

### Relativity Space

- **`location`:** `Long Beach, CA` → `Long Beach, California, US`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Relativity_Space)

  **Notes:** Founded in 2015 per Wikipedia, but company About page states 'Since 2016' (discrepancy noted). Eric Schmidt replaced Tim Ellis as CEO in March 2025 per Wikipedia. Company has contract backlog of over $2.9 billion for Terran R as of March 2025 per Wikipedia. First Terran R launch targeting late 2026 per Wikipedia.

### Vention

- **`location`:** `Montreal, Canada` → `Montreal, Quebec, Canada`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Vention)
- **`fundingStage`:** `Series C` → `Series D`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Vention)
- **`totalRaised`:** `$95M+` → `$260M+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Vention)

  **Notes:** Series D funding ($110M USD) closed in January 2026, bringing total raised to over $260M USD. European headquarters relocating from Berlin to Munich in fall 2026. Wikipedia notes website as https://vention.io while company website uses https://vention.com/.

### WB Group

- **`founder`:** `Piotr Wojciechowski, Adam Bartosiewicz, Krzysztof Wysocki` → `Piotr Wojciechowski`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/WB_Group)

  **Notes:** Only Piotr Wojciechowski is explicitly named as a key person in Wikipedia. Adam Bartosiewicz and Krzysztof Wysocki are not mentioned in provided sources as founders. Polish Development Fund invested PLN 128 million (EUR 30 million) in 2017 for 24% stake. Current stage (Pre-IPO, etc.) cannot be verified from sources provided.

---

## ✅ Cleared (31 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- AnySignal
- Apptronik
- Astera Labs
- Base Power
- Deterrence
- Dexterity
- Fortastra
- Galvanick
- HEO
- Hadrian
- Humanoid
- ICON
- Isar Aerospace
- Oklo
- Orbital Composites
- Photonic Inc
- Pivotal
- PsiQuantum
- QuiX Quantum
- Radiant
- Rebellions
- Rivian
- Sage Geosystems
- Shield AI
- SpaceX
- Valar Atomics
- Vast
- Vertical Aerospace
- Waymo
- *...and 1 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-09-10T09:31:18+00:00*