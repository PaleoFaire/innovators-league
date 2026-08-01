# Company Facts Verification Report

**Generated:** 2026-08-01T10:13:07+00:00  

**Cohort:** `data/cohort_companies_monthly.json`  

**Cohort size:** 95 companies  

**New Claude extractions this run:** 90  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 72 | 76% |
| 🔧 Changes proposed | 22 | 23% |
| ❓ Unverifiable | 1 | 1% |

---

## 🔧 Proposed Changes (22 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### 9 Mothers

- **`investors`:** `[]` → `['Y Combinator']`  
  Sources: [company_about](https://9mothers.com/company)

  **Notes:** Y Combinator Batch P26 indicated in source [1]. Founder names (Russell Smith, Roman Khomenko, Bogdan Pyzh) from database entry could not be verified in provided sources. Founded year 2024, stage Seed, and total_raised $4.5M from database entry could not be verified in provided sources.

### ACSL

- **`location`:** `Tokyo, Japan` → `Karlsruhe, Germany`  
  Sources: [company_website](https://acsl.ai)

  **Notes:** Database entry appears to reference a different company (ACSL Japan, industrial/defense drones). Source [0] is Advanced Cognitive Systems Lab, a German AI research organization founded in August 2025 (per positioning paper date). No information in source about founders, funding, stage, or investors. The company is described as 'privately owned, not-for-profit' and 'still in control' as of August 2025.

### AMP Robotics

- **`location`:** `Louisville, CO` → `Colorado, USA`  
  Sources: [company_about](https://amprobotics.com/about)

  **Notes:** Founded year 2014 and Series A stage from database entry could not be verified in provided sources. Total raised $180M+ and investor list from database entry could not be verified in provided sources. Matanya Horowitz confirmed as founder and board member in source [1]. Location specified as 'Headquartered and with manufacturing operations in Colorado' in source [1] but no specific city mentioned.

### ANYbotics

- **`totalRaised`:** `$150M+` → `$50M`  
  Sources: [company_about](https://www.anybotics.com/about) · [wikipedia](https://en.wikipedia.org/wiki/ANYbotics)

  **Notes:** Series B funding of $50M received in May 2023. Founded as spin-off from ETH Zurich. First sales in 2017.

### Aalo Atomics

- **`totalRaised`:** `$136M` → `$300M+`  
  Sources: [company_website](https://aaloatomics.com)

  **Notes:** Timeline on website shows $6M Seed (2023), $30M Series A (2024), and $100M Series B (2025) for total of $136M in named rounds, but website states '$300M+ raised' in company overview. Company achieved first criticality on July 4, 2026 at Idaho National Laboratory's Critical Test Reactor. Database entry lists 15 specific investors but source [0] does not name individual investors.

### Aepnus Technology

- **`location`:** `Oakland, CA` → `Oakland, CA, United States`  
  Sources: [company_website](https://www.aepnus.com) · [company_about](https://www.aepnus.com/team)

  **Notes:** Database entry lists 2021 as founding year, $10.6M total raised, and specific investor names, but these could not be verified in provided sources. Sources confirm Oakland, CA headquarters and two additional locations (Montréal, QC and Stuttgart, Germany). Lukas Hackl is explicitly titled 'Co-Founder and CEO' and Bilen Akuzum as 'Co-Founder and CTO' in source 1.

### Agnikul Cosmos

- **`location`:** `Chennai, India` → `Chennai, Tamil Nadu, India`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Agnikul_Cosmos)

  **Notes:** Valuation of $500M+ reported in March 2026 per Wikipedia. Tamil Nadu government (TIDCO) invested ₹25 crore in early 2026, marking first government equity stake in Indian space startup. Company claims ability to 3D print entire engine in 7 days as of 2026.

### AheadComputing

- **`founded`:** `*(empty)*` → `2024`  
  Sources: [company_website](https://www.aheadcomputing.com)

  **Notes:** Founded year calculated from website statement 'AheadComputing celebrates 2 years' dated July 31, 2026, indicating founding in 2024. Total raised of $51.5M appears to combine Seed1 ($21.5M mentioned April 1, 2026) and Seed2 ($30M mentioned April 1, 2026) rounds. Only investors explicitly named on sources (Eclipse Ventures via board member Greg Reichow, Jim Keller) are included; other investors from database entry could not be verified in provided sources.

### Albedo

- **`founder`:** `Topher Haddad, AyJay Lasater, Winston Tri` → `Topher Haddad, AyJay Lasater`  
  Sources: [company_website](https://albedo.com) · [company_about](https://albedo.com/company)
- **`location`:** `Broomfield, CO` → `Denver, CO`  
  Sources: [company_about](https://albedo.com/company)

  **Notes:** Wikipedia source [2] is about the physics concept of albedo (light reflectivity), not the company, and therefore was not used for verification. Sources confirm Clarity-1 satellite launched March 2025 with VLEO focus. Third co-founder 'Winston Tri' from database entry could not be verified in provided sources. Founded year (2020), Series B stage, total raised ($130M+), and investor list from database could not be verified from the provided sources.

### Alef Aeronautics

- **`location`:** `San Mateo, CA` → `San Mateo, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Alef_Aeronautics)

  **Notes:** Wikipedia source indicates company was founded April 6, 2015. Current database entry lists stage as 'Series A' and total_raised as '$30M+', but these specific values cannot be verified from provided sources. FAA Special Airworthiness Certificate approval mentioned in Wikipedia references (Daleo, FLYING Magazine, June 2023). Production of Model A Ultralight reported to have begun in December 2025.

### Alice & Bob

- **`totalRaised`:** `$104M+` → `€100M`  
  Sources: [company_website](https://alice-bob.com)

  **Notes:** Source [1] is Wikipedia article about the fictional characters 'Alice and Bob' used in cryptography, not the company. Company website [0] states 'We raised €100M' and describes pioneering 'the cat qubit, the first qubit with built-in error correction.' Founder names and founded year not explicitly stated in provided sources. Current stage not explicitly stated. Investors and valuation not found in provided sources.

### Alpha School

- **`location`:** `Austin, TX` → `Austin, Texas, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Alpha_School)

  **Notes:** Wikipedia indicates 13 campuses as of 2026 and lists Joe Liemandt as principal. The school was formerly called Emergent Academy and began as a spinoff of Acton Academy. Unbound Academy is a related charter school in Arizona using the same model. Academic growth claims rely on internal analyses of MAP assessments and have not been independently verified per Wikipedia. Governance concerns have been raised regarding interconnected for-profit vendors.

### Andrenam

- **`fundingStage`:** `Seed` → `Series A`  
  Sources: [company_website](https://andrenam.com)
- **`totalRaised`:** `$10M` → `$18M`  
  Sources: [company_website](https://andrenam.com)

  **Notes:** Database entry lists $10M Seed from First Round Capital, but source [0] dated 7.23.2026 announces $18M Series A, indicating this is most recent funding stage. Location 'Hawthorne, CA' from database entry could not be verified in provided sources. Founded year 2024 from database could not be verified in provided sources. Investor names from database entry (First Round Capital, Also Capital, Long Journey Ventures, Homebrew, Colorado School of Mines Venture Fund) could not be verified in provided sources.

### Anello Photonics

- **`founder`:** `Mario Paniccia, Mike Horton` → `Mario Paniccia`  
  Sources: [company_about](https://anellophotonics.com/company)
- **`totalRaised`:** `$50M+` → `$25M`  
  Sources: [company_website](https://anellophotonics.com)

  **Notes:** Series B-2 funding round of $25M closed in May 2026 per source [0]. Only Mario Paniccia explicitly identified as founder/CEO in source [1]; Mike Horton mentioned in database entry but not found in provided sources. Location (Santa Clara, CA) and founded year (2018) from database entry but not verified in provided sources. Additional investors and valuation not found in provided sources.

### Antora Energy

- **`location`:** `Sunnyvale, CA` → `San Jose, CA`  
  Sources: [company_website](https://antoraenergy.com)
- **`fundingStage`:** `Series B` → `Series C`  
  Sources: [company_website](https://antoraenergy.com) · [company_about](https://antoraenergy.com/company)
- **`totalRaised`:** `$150M` → `$550M`  
  Sources: [company_website](https://antoraenergy.com) · [company_about](https://antoraenergy.com/company)

  **Notes:** Series C funding of $550M represents most recent disclosed raise. Database entry listed Series B with $150M, which appears to be outdated. Location updated from Sunnyvale to San Jose based on website reference to 'San Jose, California Factory'.

### Apex Space

- **`totalRaised`:** `$518M` → `$200M`  
  Sources: [company_about](https://apexspace.com/about)

  **Notes:** Database entry lists $518M total_raised and multiple investors, but only $200M Series D is explicitly stated in sources. The $45.9M Space Force contract and 200+ satellites/year production capacity are mentioned in database but not verified in provided sources. Investor names from database entry cannot be verified from these sources.

### Arc Boats

- **`location`:** `Los Angeles, CA` → `Los Angeles, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Arc_Boats)

  **Notes:** Wikipedia article notes promotional content and is flagged as orphaned. All verified facts come from single Wikipedia source [0].

### Archer Aviation

- **`location`:** `San Jose, CA` → `San Jose, California, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Archer_Aviation)

  **Notes:** Wikipedia states company became IPO on September 20, 2021 (ticker NYSE: ACHR). Brett Adcock departed from leadership and board in 2022; Adam Goldstein is currently sole CEO and Chairman. Website listed in Wikipedia as 'archer.com' rather than 'archeraviation.com' from database entry.

### Archetype AI

- **`founder`:** `Ivan Poupyrev, Brandon Barbello, Leonardo Giusti, Jaime Lien` → `Ivan Poupyrev, Brandon Barbello, Leonardo Giusti, Jaime Lien`  
  Sources: [company_about](https://www.archetypeai.io/about)
- **`founded`:** `2024` → `2023`  
  Sources: [company_about](https://www.archetypeai.io/about)
- **`fundingStage`:** `Seed` → `Series A`  
  Sources: [company_about](https://www.archetypeai.io/about)
- **`totalRaised`:** `$13M` → `$48M`  
  Sources: [company_about](https://www.archetypeai.io/about)

  **Notes:** Founded in 2023 according to source [1] (not 2024 as in database entry). Series A of $35M announced Nov 20, 2025 per source [1], plus prior $13M seed = $48M total. Location (Palo Alto, CA) not verified in provided sources. Investor list from database entry not verified in provided sources.

### Astrolab

- **`location`:** `Hawthorne, CA` → `Hawthorne, California, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Astrolab)

  **Notes:** Official trade name is Venturi Astrolab Inc. Source [0] (company website at astrolab.co) appears to be a consulting/AI services firm and does not match the aerospace company described in Wikipedia. Source [1] (Wikipedia) is the authoritative source for this aerospace company. The database entry references a lunar rover (FLEX) selected for NASA Artemis, which is verified in Wikipedia. No funding information found in sources.

### Atana Elements

- **`founder`:** `Tom Wilson (CEO, Stanford GSB + Royal School of Mines, ex-He` → `Tom Wilson`  
  Sources: [company_about](https://atanaelements.com/about)

  **Notes:** Tom Wilson explicitly identified as 'Chief Executive Officer & Founder' in source [1]. Sources mention he was 'an early hire to Lilac Solutions' executive team in 2019' but do not state when Atana Elements was founded. No funding stage, total raised, valuation, or specific investor names are mentioned in provided sources. Location not specified in sources despite website being accessible.

### Atom Computing

- **`totalRaised`:** `$60M` → `$300M+`  
  Sources: [company_website](https://atom-computing.com)

  **Notes:** Most recent funding announcement from June 16, 2026 indicates $300M+ raised (source 0). Database entry lists Series B from January 2022 ($60M), but more recent funding appears to supersede this stage classification. Microsoft partnership announced late 2024 with logical qubits demonstrated. No valuation figure found in sources.

---

## ❓ Unverifiable (1 companies)

Couldn't fetch authoritative sources. Per Stephen's rule, we leave these as-is rather than guess. May want to flag for manual research or removal from DB.

- **Addionics** — *no public sources accessible*

---

## ✅ Cleared (72 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- 1872
- 1X Technologies
- 44.01
- AAVantgarde Bio
- ABL Bio
- ADASI
- AIM Intelligent Machines
- AIR
- AQT
- ARC Clean Technology
- ARX Robotics
- AST SpaceMobile
- Aalyria
- AbCellera
- Abridge
- Aclarity
- Adarga
- Aeon Industrial
- Aerospacelab
- Aestus Industries
- Aeva Technologies
- Agile Robots
- Agility Robotics
- AiDash
- Airship Industries
- Akash Systems
- Albacore
- AlixLabs
- Allen Control Systems
- Alpine Eagle
- *...and 42 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-08-01T10:13:07+00:00*