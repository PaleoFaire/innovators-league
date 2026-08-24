# Company Facts Verification Report

**Generated:** 2026-08-24T07:54:29+00:00  

**Cohort:** `data/cohort_companies_weekly.json`  

**Cohort size:** 93 companies  

**New Claude extractions this run:** 87  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 80 | 86% |
| 🔧 Changes proposed | 8 | 9% |
| ❓ Unverifiable | 5 | 5% |

---

## 🔧 Proposed Changes (8 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### 1X Technologies

- **`location`:** `Palo Alto, CA` → `Palo Alto, California, USA`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)
- **`totalRaised`:** `$1.1B` → `$123.5M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)

  **Notes:** Company was originally founded as Halodi Robotics in 2014 and rebranded as 1X Technologies in 2022. Total raised figure represents verified funding: $23.5M Series A2 (March 2023) + $100M Series B (January 2024). Sources [0] and [1] describe a different company (wire/cable manufacturer located in Sheridan, Wyoming) that is unrelated to the robotics company described in source [2].

### Alif Semiconductor

- **`location`:** `Pleasanton, CA` → `Pleasanton, California`  
  Sources: [company_website](https://alifsemi.com) · [company_about](https://alifsemi.com/about)

  **Notes:** Sources confirm Syed Ali as CEO & Co-Founder and Reza Kazerounian as President & Co-Founder. Kleiner Perkins explicitly mentioned as lead investor. Founded year, current stage, total raised, and valuation cannot be verified from provided sources. Location confirmed as Pleasanton, California from both website and about page.

### Anduril Industries

- **`location`:** `Costa Mesa, CA` → `Costa Mesa, California, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Anduril_Industries)

  **Notes:** Wikipedia states company was incorporated April 20, 2017. Valuation of $61B as of May 2026 per Wikipedia. Website source [0] appears to be under construction and provides no verifiable content. Current stage (Series H) and total_raised ($11B+) from database entry could not be verified in provided sources.

### Applied Intuition

- **`location`:** `Sunnyvale, CA` → `Sunnyvale, California`  
  Sources: [company_about](https://appliedintuition.com/about)

  **Notes:** Founded in January 2017 by Qasar Younis and Peter Ludwig. Series F funding of $600M announced in June 2025, increasing valuation from $6B (2024) to $15B. Marc Andreessen joined as board member in 2017. Wikipedia notes Ray Dalio, Henry Kravis, Mary Meeker, Reid Hoffman, and Mustafa Suleyman as investors alongside the listed firms.

### Boom Supersonic

- **`location`:** `Centennial, CO` → `Centennial, Colorado`  
  Sources: [company_website](https://boomsupersonic.com) · [wikipedia](https://en.wikipedia.org/wiki/Boom_Supersonic)

  **Notes:** Company legally named 'Boom Technology, Inc.' but trades as 'Boom Supersonic'. XB-1 broke sound barrier on January 28, 2025, becoming first privately-funded aircraft to do so. Introduced 42MW Superpower natural gas turbine in December 2025 for AI data center power applications. Orders total 130 aircraft from United Airlines, American Airlines, and Japan Airlines.

### Built Robotics

- **`location`:** `San Francisco, CA` → `San Francisco, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Built_Robotics)

  **Notes:** Wikipedia source uses spelling 'Andrew Liang' while database entry shows 'Andrew Lian' — Wikipedia is authoritative. Company acquired Roin Technologies in 2023.

### Core Automation

- **`location`:** `California` → `California, USA`  
  Sources: [company_about](https://coreautomation.com/company)

  **Notes:** The sources describe an established industrial automation engineering firm founded in 2001, NOT the frontier-tech AI company described in the database entry. This appears to be a completely different company with the same name. The database entry references Ceres, continual learning, ex-OpenAI/Anthropic/DeepMind researchers, and AI lab automation - none of which are mentioned in these sources. No information available to verify the frontier-tech company claims.

### Dexterity

- **`location`:** `Redwood City, CA` → `Redwood City, California`  
  Sources: [company_about](https://dexterity.com/about)
- **`totalRaised`:** `$291M` → `$104.9M`  
  Sources: [sec_form_d](https://www.sec.gov/Archives/edgar/data/2137857/000213785726000002/primary_doc.xml)

  **Notes:** Database entry lists Series B stage and $291M total raised, but most recent SEC Form D filing from 2026-08-17 shows only $104.9M raised in that filing. Current stage cannot be verified from sources. Company reached 100 million autonomous actions in production as of 2025 per website.

---

## ❓ Unverifiable (5 companies)

Couldn't fetch authoritative sources. Per Stephen's rule, we leave these as-is rather than guess. May want to flag for manual research or removal from DB.

- **Cambridge Aerospace** — *no public sources accessible*
- **Cuby Technologies** — *no public sources accessible*
- **Dendra Systems** — *no public sources accessible*
- **Digantara** — *no public sources accessible*
- **Distalmotion** — *no public sources accessible*

---

## ✅ Cleared (80 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- 44.01
- AAVantgarde Bio
- ABL Bio
- ADASI
- AIR
- ARC Clean Technology
- ARX Robotics
- Aeon Industrial
- Aerospacelab
- Aestus Industries
- Aeva Technologies
- Agile Robots
- AheadComputing
- AiDash
- Aigen
- AlixLabs
- Allen Control Systems
- Alsym Energy
- Amber Bio
- Ambrosia Energy
- American Housing Corporation
- Apis Cor
- Applied Atomics
- Archer Materials
- Ares Industries
- Ark Robotics
- Asimov
- Astranis
- Atana Elements
- Atlas Motion
- *...and 50 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-08-24T07:54:29+00:00*