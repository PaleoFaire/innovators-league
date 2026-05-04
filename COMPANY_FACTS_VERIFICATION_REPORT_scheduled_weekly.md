# Company Facts Verification Report

**Generated:** 2026-05-04T09:19:50+00:00  

**Cohort:** `data/cohort_companies_weekly.json`  

**Cohort size:** 89 companies  

**New Claude extractions this run:** 52  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 67 | 75% |
| 🔧 Changes proposed | 6 | 7% |
| ❓ Unverifiable | 16 | 18% |

---

## 🔧 Proposed Changes (6 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Agile Robots

- **`website`:** `*(empty)*` → `https://agile-robots.com`  
  Sources: [company_website](https://agile-robots.com)

  **Notes:** Source [0] mentions 'a passionate team of robotics researchers from the German Aerospace Center' but does not explicitly name individual founders. News items reference acquisition of thyssenkrupp Automation Engineering (April 2026) and partnership with Google DeepMind (March 2026), but these are headlines only without detail in provided source. Current_stage, total_raised, valuation, and specific investor names cannot be verified from source [0] alone.

### AlixLabs

- **`totalRaised`:** `$14.1M EUR` → `€15M`  
  Sources: [company_website](https://www.alixlabs.com)

  **Notes:** Series A funding closed in April 2026 with €15M total (€14.1M announced November 2025, additional €0.9M from Stephen Industries in April 2026). Company was spun off from Lund University. Amin Karimi listed as Co-Founder but joined in 2021, not 2019 founding.

### Applied Intuition

- **`totalRaised`:** `$1.2B+` → `$600M+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Applied_Intuition)

  **Notes:** Series F funding ($600M) and valuation ($15B) announced June 2025 per Wikipedia source. Previous valuation was $6B in 2024. Founded January 2017. Marc Andreessen joined as board member in 2017.

### Basecamp Research

- **`website`:** `*(empty)*` → `https://basecamp-research.com`  
  Sources: [company_website](https://basecamp-research.com)

  **Notes:** Source [0] is a privacy policy page only. No factual company information (description, founders, location, funding, stage) could be verified from the provided sources. The database entry references cannot be used as source material per instructions.

### Baykar

- **`founder`:** `Selçuk Bayraktar, Haluk Bayraktar` → `Özdemir Bayraktar`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Baykar)

  **Notes:** Wikipedia lists founding year as 1984, while company website states 1986 in 'Baykar in Numbers' section. Wikipedia is more detailed and consistent. Özdemir Bayraktar (founder) died October 18, 2021. Company acquired Piaggio Aerospace on December 27, 2024. Leonardo and Baykar agreed to cooperate on UAVs on March 6, 2025. Database entry claims $1.8B 2024 exports and ~$10B valuation but these are not verifiable from provided sources.

### Electra

- **`location`:** `Boulder, CO` → `Brooklyn, NY`  
  Sources: [company_about](https://electra.com/about-us)
- **`website`:** `*(empty)*` → `https://electra.com`  
  Sources: [company_website](https://electra.com)

  **Notes:** The sources provided describe Electra as a 120V induction stove manufacturer (sources 0-1), not the iron ore refining company described in the database entry. Source 2 is about Greek mythology and irrelevant. The database entry describes a completely different company (steel/iron ore processing via electrochemistry). No verified information about founders, founding year, funding, stage, or valuation could be found in these sources for either company.

---

## ❓ Unverifiable (16 companies)

Couldn't fetch authoritative sources. Per Stephen's rule, we leave these as-is rather than guess. May want to flag for manual research or removal from DB.

- **44.01** — *no public sources accessible*
- **AAVantgarde Bio** — *no public sources accessible*
- **ARC Clean Technology** — *no public sources accessible*
- **Aestus Industries** — *no public sources accessible*
- **Ambient Photonics** — *no public sources accessible*
- **Ambient.ai** — *no public sources accessible*
- **Atomic AI** — *no public sources accessible*
- **Cambridge Aerospace** — *no public sources accessible*
- **Collaborative Robotics** — *no public sources accessible*
- **Creotech Instruments** — *no public sources accessible*
- **DIRAC** — *no public sources accessible*
- **Dendra Systems** — *no public sources accessible*
- **Digantara** — *no public sources accessible*
- **Distalmotion** — *no public sources accessible*
- **Emelody** — *no public sources accessible*
- **Ephos** — *no public sources accessible*

---

## ✅ Cleared (67 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- 1X Technologies
- ABL Bio
- ADASI
- AIR
- ARX Robotics
- Aeon Industrial
- Aerospacelab
- Aeva Technologies
- AiDash
- Allen Control Systems
- Amber Bio
- Anduril Industries
- Anthropic
- Anysphere
- Apis Cor
- Archer Materials
- Ares Industries
- Ark Robotics
- Ascend Elements
- Asimov
- Astranis
- Axelera AI
- Axelspace
- Ayar Labs
- BRINC Drones
- Bedrock Robotics
- Bethlehem Steel Corp
- Black Forest Labs
- Blackshark.ai
- Blykalla
- *...and 37 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-05-04T09:19:50+00:00*