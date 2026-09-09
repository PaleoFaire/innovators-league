# Company Facts Verification Report

**Generated:** 2026-09-09T09:32:21+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 41 companies  

**New Claude extractions this run:** 41  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 35 | 85% |
| 🔧 Changes proposed | 6 | 15% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (6 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### 1X Technologies

- **`location`:** `Palo Alto, CA` → `Palo Alto, California, USA`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)
- **`fundingStage`:** `Pre-Seed` → `Series B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)
- **`totalRaised`:** `$1.1B` → `$123.5M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)

  **Notes:** Company was originally founded as Halodi Robotics in 2014 and rebranded as 1X Technologies in 2022. Series A2 funding of $23.5M in March 2023 (source 2), Series B funding of $100M in January 2024 (source 2). Total raised calculation: $23.5M + $100M = $123.5M. Sources 0 and 1 refer to a different company (wire/cable distributor) also named 1X Technologies, not the robotics company.

### Agility Robotics

- **`fundingStage`:** `Series E` → `Pre-IPO`  
  Sources: [company_website](https://agilityrobotics.com)

  **Notes:** Company announced merger with Churchill Capital Corp XI to go public (June 24, 2026, per source 0). Wikipedia notes a rebrand to 'Agility' on March 5, 2026 (source 2). Founded as spinoff from Oregon State University's Dynamic Robotics Lab. 2025 revenue reported as $1.8M with $140M operating loss (source 4).

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is publicly listed on NASDAQ (NNE) as of the sources provided (dated August 2026). Database entry references founder 'Jay Jiang Yu' and valuation of $808M, but these cannot be verified from provided sources. Sources do not mention ODIN sale to Cambridge AtomWorks or previous Seed stage funding of $600M+. Source [2] about Valar Atomics is unrelated to Nano Nuclear Energy.

### Navier

- **`founded`:** `2019` → `2021`  
  Sources: [company_about](https://www.navierboat.com/about)

  **Notes:** Source [2] is Wikipedia article about Claude-Louis Navier (1785-1836), a French engineer/mathematician, not the boat company. Source [3] is about Navier-Stokes equations, not the company. Founded date verified as 'JAN '21' (January 2021) from company timeline. Location (Alameda, CA) from database entry cannot be verified in provided sources. Founder Sampriti Bhattacharyya confirmed as 'Founder & CEO' in source [1]. Stage progression documented: first customer delivery October 2024, first commercial delivery May 2025. No funding information found in sources.

### Poseidon Aerospace

- **`fundingStage`:** `Seed` → `Series A`  
  Sources: [company_website](https://www.poseidonaero.com)
- **`totalRaised`:** `$12M+` → `$60M`  
  Sources: [company_website](https://www.poseidonaero.com)

  **Notes:** Database entry describes ground-effect vehicles and ekranoplan technology, but company website describes unmanned cargo aircraft (HERON seaplane, EGRET fixed-wing). Series A funding of $60M announced September 8, 2026 per website news section. Previous $11M funding announced November 5, 2025. Founders listed in database entry (David Zagaynov, Parker Tenney, Isaac Baumstark) and location (San Francisco, CA) could not be verified from provided sources. Founded year 2024 from database could not be verified.

### Stoke Space

- **`location`:** `Kent, WA` → `Kent, Washington`  
  Sources: [company_about](https://www.stokespace.com/about-us) · [wikipedia](https://en.wikipedia.org/wiki/Stoke_Space)
- **`founded`:** `2019` → `2020`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Stoke_Space)
- **`totalRaised`:** `$860M` → `$1B+`  
  Sources: [news (TechCrunch)](https://techcrunch.com/2026/09/08/stoke-space-raises-another-billion-to-rival-spacex-at-re-flying-rockets/)

  **Notes:** Wikipedia states founded 2020, but database entry and company sources reference 2019 founding—Wikipedia is more authoritative source. Series D was extended to $860M in February 2026 per Wikipedia[2]; Series E of $1B completed per TechCrunch[3]. Most recent funding round is Series E.

---

## ✅ Cleared (35 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- AnySignal
- Apptronik
- Astera Labs
- Base Power
- Cognition
- Dawn Aerospace
- Deterrence
- Fortastra
- Galvanick
- HEO
- Hadrian
- Hailo
- Humanoid
- ICON
- Isar Aerospace
- Oklo
- Orbital Composites
- PLD Space
- Palantir
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
- *...and 5 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-09-09T09:32:21+00:00*