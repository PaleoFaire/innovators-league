# Company Facts Verification Report

**Generated:** 2026-08-10T08:30:17+00:00  

**Cohort:** `data/cohort_companies_weekly.json`  

**Cohort size:** 93 companies  

**New Claude extractions this run:** 87  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 81 | 87% |
| 🔧 Changes proposed | 7 | 8% |
| ❓ Unverifiable | 5 | 5% |

---

## 🔧 Proposed Changes (7 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### AiDash

- **`fundingStage`:** `Series C` → `Acquired`  
  Sources: [company_website](https://aidash.com)

  **Notes:** Schneider Electric announced definitive agreement to acquire AiDASH (stated on homepage as 'News Flash'). Database entry lists 185+ customers; current source states 200+ customers and earlier source states 'more than 150 customers'. No founder names, founding year, total raised, valuation, or specific location found in provided sources. Investor list from database entry could not be verified from these sources.

### Aigen

- **`founder`:** `Kenny Lee (CEO, ex-Weblife.io), Rich Wurden (CTO, ex-Tesla)` → `Kenny Lee, Richard Wurden`  
  Sources: [company_about](https://aigen.io/about)

  **Notes:** Wikipedia source [2] is irrelevant (disambiguation page for Austrian locations). Database entry references Series B stage, $23.7M raised, Redmond WA location, and multiple investors, but none of these are explicitly stated in the provided sources. Location cannot be verified from sources provided. Investor names and funding stage/amounts require additional sources for verification.

### Alif Semiconductor

- **`founder`:** `Syed Ali (CEO, ex-Cavium), Reza Kazerounian (President, ex-A` → `Syed Ali, Reza Kazerounian`  
  Sources: [company_about](https://alifsemi.com/about)

  **Notes:** Founded year not explicitly stated in sources despite database entry claiming 2019. Series C stage and $185.9M total raised from database entry could not be verified in provided sources. No valuation disclosed in sources.

### Astranis

- **`fundingStage`:** `Series D` → `Series E`  
  Sources: [company_website](https://astranis.com)
- **`totalRaised`:** `$350M+` → `$1.2B+`  
  Sources: [company_website](https://astranis.com)

  **Notes:** Founded October 20, 2015 per Wikipedia. Series E funding of $450M announced (source [0]), bringing total raised to more than $1.2B. Five GEO satellites in orbit as of source publication date (source [0]). Company headquarters at Historic Pier 70 in San Francisco, California (source [0]).

### Boom Supersonic

- **`location`:** `Denver, Colorado` → `Centennial, Colorado`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Boom_Supersonic)
- **`fundingStage`:** `Series D` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Boom_Supersonic)

  **Notes:** Wikipedia lists headquarters as Centennial, Colorado (source 2), while database entry listed Denver, Colorado. XB-1 broke sound barrier on January 28, 2025 per Wikipedia (source 2). Company also developing Superpower 42 MW natural gas turbine for AI data centers (source 2). No valuation figure found in sources.

### Cognition

- **`totalRaised`:** `$1.5B+` → `$400M+`  
  Sources: [company_about](https://cognition.com/about)

  **Notes:** Source [1] states 'We have raised over $400M' from named investors. Founder names (Scott Wu, Steven Hao, Walden Yan) are not explicitly identified as founders in provided sources, so cannot be verified. Founded year 2023 cannot be verified from sources. Current stage cannot be verified. Wikipedia source [2] is about cognition as a mental process, not the company.

### Core Automation

- **`totalRaised`:** `Targeting $500M-$1B at $4-5B+ val` → `$432.13M`  
  Sources: [sec_form_d](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0002148145&type=D&dateb=&owner=include&count=10)

  **Notes:** Database entry appears to reference a different company (frontier-tech AI lab with ex-OpenAI/Anthropic researchers). Source [0] and [1] describe Core Automation, Inc. as a traditional industrial automation/electrical engineering firm founded 2001 in Sacramento, CA. Source [2] SEC Form D shows $432.125M raised filed 2026-07-30, which does not match database description of 'targeting $500M-$1B'. These are likely two different entities with similar names.

---

## ❓ Unverifiable (5 companies)

Couldn't fetch authoritative sources. Per Stephen's rule, we leave these as-is rather than guess. May want to flag for manual research or removal from DB.

- **Cambridge Aerospace** — *no public sources accessible*
- **Cuby Technologies** — *no public sources accessible*
- **Dendra Systems** — *no public sources accessible*
- **Digantara** — *no public sources accessible*
- **Distalmotion** — *no public sources accessible*

---

## ✅ Cleared (81 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- 1X Technologies
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
- AlixLabs
- Allen Control Systems
- Alsym Energy
- Amber Bio
- American Housing Corporation
- Anduril Industries
- Apis Cor
- Applied Atomics
- Applied Intuition
- Archer Materials
- Ares Industries
- Ark Robotics
- Asimov
- Atana Elements
- Atomic AI
- Atoms
- *...and 51 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-08-10T08:30:17+00:00*