# Company Facts Verification Report

**Generated:** 2026-09-11T09:29:08+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 35 companies  

**New Claude extractions this run:** 35  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 28 | 80% |
| 🔧 Changes proposed | 7 | 20% |
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

  **Notes:** Company was originally founded as Halodi Robotics in 2014 and rebranded as 1X Technologies in 2022. Wikipedia states Series A2 funding of $23.5M (March 2023) and Series B funding of $100M (January 2024), totaling $123.5M in verified funding rounds. Sources 0 and 1 refer to a different company (wire and cable distributor also named 1X Technologies LLC based in Wyoming) and are not relevant to this robotics company. Wikipedia is the only source providing verified information about 1X Technologies robotics company.

### Agility Robotics

- **`fundingStage`:** `Series E` → `Pre-IPO`  
  Sources: [company_website](https://agilityrobotics.com)

  **Notes:** Company announced merger with Churchill Capital Corp XI to go public (announced June 24, 2026, per source 0). Wikipedia notes a rebrand to 'Agility' announced March 5, 2026 (source 2). S-4 filing indicates $1.8M revenue in 2025 (source 4). Database entry lists investors and $400M+ raised, but these cannot be verified from provided sources.

### IQM Quantum Computers

- **`founder`:** `Jan Goetz, Mikko Möttönen, Kuan Yen Tan, Juha Vartiainen` → `Jan Goetz`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/IQM_Quantum_Computers)
- **`fundingStage`:** `Public` → `Pre-IPO`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/IQM_Quantum_Computers)

  **Notes:** Wikipedia source [2] indicates IPO announced on 23 February 2026 with initial valuation of $1.8 billion, changing status from Private to Pre-IPO. Only Jan Goetz is explicitly named as founder/CEO in Wikipedia [2]; other names in database entry (Mikko Möttönen, Kuan Yen Tan, Juha Vartiainen) are not found in these sources as founders. Source [3] is about Proxima Fusion, not IQM, and was excluded from analysis.

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is publicly listed on NASDAQ under ticker NNE. Sources claim to be 'the first nuclear microreactor company to be listed publicly in the U.S.' Founded year, founder names, total capital raised, and valuation cannot be verified from provided sources. Source [2] (Canary Media article about Valar Atomics) does not contain information about NANO Nuclear Energy and was not used.

### Proxima Fusion

- **`totalRaised`:** `€200M` → `€145M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Proxima_Fusion)

  **Notes:** Series A round: €130M in June 2025 plus €15M extension in September 2025 = €145M total. Wikipedia also mentions July 2026 investment from Alphabet Inc., but total amount not specified. Company website lists €200M total_raised in database entry, but this figure is not explicitly stated in any provided source.

### Rigetti Computing

- **`location`:** `Berkeley, CA` → `Berkeley, California, United States`  
  Sources: [company_about](https://rigetti.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Rigetti_Computing)

  **Notes:** SPAC deal closed March 2, 2022; began trading on NASDAQ under ticker RGTI. Subodh Kulkarni became President and CEO in December 2022. Valuation cited is from October 2021 SPAC announcement ($1.5B estimated); current market valuation may differ. Wikipedia source shows 2024 revenue of $10.8M and net loss of $201M.

### The Boring Company

- **`location`:** `Bastrop, TX` → `Bastrop, Texas, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/The_Boring_Company)
- **`totalRaised`:** `$908M` → `$3B`  
  Sources: [news (TechCrunch)](https://techcrunch.com/2026/09/10/the-boring-company-raises-3b-in-round-led-by-uae/)

  **Notes:** Database entry states Series G and $908M raised, but most recent verified funding is $3B Series D (source 2) and April 2022 Series C valuation of $5.675B (source 1). Headquarters moved to Bastrop, Texas before April 2023 (source 1). Database entry claims 35,000 passengers daily but sources do not provide this specific metric.

---

## ✅ Cleared (28 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- AnySignal
- Apptronik
- Base Power
- Deterrence
- Dexterity
- Fortastra
- Galvanick
- Hadrian
- Humanoid
- ICON
- Monumental
- Oklo
- Orbital Composites
- Oxford Quantum Circuits
- Pivotal
- QuantWare
- Radiant
- Rivian
- Sage Geosystems
- Shield AI
- SpaceX
- Valar Atomics
- Vast
- Vention
- Vertical Aerospace
- WB Group
- Waymo


---

*Generated by `scripts/generate_verification_report.py` on 2026-09-11T09:29:08+00:00*