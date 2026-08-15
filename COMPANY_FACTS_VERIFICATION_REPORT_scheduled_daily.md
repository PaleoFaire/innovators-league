# Company Facts Verification Report

**Generated:** 2026-08-15T05:33:25+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 46 companies  

**New Claude extractions this run:** 46  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 37 | 80% |
| 🔧 Changes proposed | 9 | 20% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (9 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### 1X Technologies

- **`totalRaised`:** `$1.1B` → `$123.5M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)

  **Notes:** Company was originally founded as Halodi Robotics in 2014 and rebranded to 1X Technologies in 2022. Series A2 funding of $23.5M in March 2023 led by OpenAI Startup Fund. Series B funding of $100M in January 2024 led by EQT Ventures. Total raised calculation: $23.5M + $100M = $123.5M. Sources [0] and [1] are for a different company (1X Technologies LLC, a wire and cable distributor founded in 2015) and were not used. Wikipedia source [2] is the only source matching the company in the database entry.

### Agility Robotics

- **`fundingStage`:** `Series D` → `Pre-IPO`  
  Sources: [company_website](https://agilityrobotics.com)

  **Notes:** Company announced merger with Churchill Capital Corp XI to go public (announced June 24, 2026, per source 0). Wikipedia notes a rebrand to 'Agility' announced March 5, 2026 (source 2), but company website still uses 'Agility Robotics' name. Database entry lists investors and total_raised but these cannot be verified from provided sources.

### Blue Origin

- **`fundingStage`:** `SPAC` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Blue_Origin)

  **Notes:** Database entry lists stage as 'SPAC' but source [0] clearly identifies company as 'Private'. Database entry cites total_raised of '$10B+' but this cannot be verified from provided sources. No specific valuation found in sources. Coatue Management and Jeff Bezos listed as investors in database entry but cannot be verified from these sources.

### Icarus

- **`founder`:** `Henry Kwan (CEO, fmr Orbital — built spacecraft + space robo` → `Henry Kwan`  
  Sources: [company_about](https://www.icarus.one/about)
- **`location`:** `Los Angeles, CA` → `California, USA`  
  Sources: [company_about](https://www.icarus.one/about)

  **Notes:** Source [2] is Wikipedia entry for mythological Icarus, not the company. Source [3] is about Neros Technologies, not Icarus. Database entry mentions YC Fall 2025 acceptance, Y Combinator investors list partially visible in source [1] but only Paul Graham explicitly named. Current stage cannot be verified from sources provided. Total raised and valuation information not found in sources.

### Intuitive Machines

- **`location`:** `Houston, TX` → `Houston, Texas, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Intuitive_Machines)
- **`fundingStage`:** `SPAC` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Intuitive_Machines)

  **Notes:** Company went public on February 14, 2023 via SPAC merger with Inflection Point Acquisition Corp. and trades on Nasdaq under ticker LUNR. Database entry listed 'SPAC' as stage but company is now Public. Wikipedia lists revenue of $292 million (2025). Total raised amount of $305M from database entry could not be verified in sources.

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is publicly listed on NASDAQ under ticker NNE. Sources describe it as 'the first nuclear microreactor company to be listed publicly in the U.S.' Database entry mentions founders (Jay Jiang Yu) and specific financial figures ($600M+ raised, $808M valuation, $1.2B market cap) that cannot be verified from provided sources. ODIN sale to Cambridge AtomWorks mentioned in database entry is not referenced in provided sources.

### Neros

- **`location`:** `El Segundo, CA` → `El Segundo, California`  
  Sources: [company_website](https://www.neros.tech) · [wikipedia](https://en.wikipedia.org/wiki/Neros)
- **`totalRaised`:** `$371M` → `$250M`  
  Sources: [company_website](https://www.neros.tech)

  **Notes:** Wikipedia states approximately $121M raised by late 2025, but company website and The Robot Report source cite $250M Series C. Using the more recent $250M figure from official company announcement. Wikipedia also reports production rates of 2,000 drones per day as of December 2025, contrasting with database entry claim of ~1,000 monthly. US Army awarded $500M contract in July 2026 per Wikipedia (future-dated reference).

### Rhoman Aerospace

- **`founded`:** `2018` → `2015`  
  Sources: [company_about](https://www.rhoman.aero/about)

  **Notes:** Database entry listed founded year as 2018, but source [1] states 'Rhoman Aerospace began in 2015 with the filing of its first patent.' Founders Thomas Youmans and Thomas Callen are not explicitly named as founders in provided sources. Source [2] is about a different company (Neros Technologies) and is not relevant to Rhoman Aerospace.

### SpaceX

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Wikipedia source indicates SpaceX completed its initial public offering on June 12, 2026, raising $86 billion, described as the largest IPO in history. Source [1] (Defense One) does not contain relevant company information for SpaceX. Current database entry lists valuation at $1.65T and stage as 'IPO' but Wikipedia only confirms the June 2026 IPO occurred and raised $86B; current valuation cannot be verified from provided sources.

---

## ✅ Cleared (37 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- AnySignal
- Apptronik
- Astranis
- Asylon Robotics
- Aurora Innovation
- Base Power
- Cambridge Aerospace
- Cape
- Dawn Aerospace
- Deterrence
- Durin
- Einride
- FlyBy Robotics
- Galvanick
- Hadrian
- Humanoid
- Impulse Space
- Isembard
- Neura Robotics
- Oklo
- Orbital Composites
- Palantir
- Parallel Systems
- Persona AI
- Quaise Energy
- Quantum-Systems
- Radiant
- Rivian
- Rocket Lab
- *...and 7 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-08-15T05:33:25+00:00*