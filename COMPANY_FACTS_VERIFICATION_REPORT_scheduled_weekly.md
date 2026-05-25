# Company Facts Verification Report

**Generated:** 2026-05-25T11:11:44+00:00  

**Cohort:** `data/cohort_companies_weekly.json`  

**Cohort size:** 89 companies  

**New Claude extractions this run:** 53  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 71 | 80% |
| 🔧 Changes proposed | 4 | 4% |
| ❓ Unverifiable | 14 | 16% |

---

## 🔧 Proposed Changes (4 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### ADASI

- **`website`:** `*(empty)*` → `https://adasi.ai`  
  Sources: [company_website](https://adasi.ai)

  **Notes:** Source [0] describes a Japanese marketing/advertising platform (AI Image Generator, ad management tool) with Google Ads and Facebook Ads integration. This does NOT match the database entry describing ADASI as a UAE national UAV manufacturer. The source appears to be a different company entirely with the same or similar name. No information about UAVs, EDGE Group, Abu Dhabi, or military/defense applications found in provided sources. Cannot verify database entry claims.

### Electra

- **`location`:** `Boulder, CO` → `Brooklyn, NY`  
  Sources: [company_about](https://electra.com/about-us)
- **`website`:** `*(empty)*` → `https://electra.com`  
  Sources: [company_website](https://electra.com)

  **Notes:** Sources provided describe two different companies named 'Electra': (1) Electra Research Inc., a kitchen appliance company that manufactures 120V induction stoves with integrated battery backup, located in Brooklyn, NY (sources 0-1); (2) Greek mythology character Electra (source 2). The database entry references an iron ore refining company using electrochemistry, which does not match either source. No information found about founders Sandeep Nijhawan or Quoc Pham, Series B funding, $299M raised, or iron/steel decarbonization technology in provided sources. Only verifiable facts from sources 0-1 are location (Brooklyn, NY per source 1: 'Electra Research Inc. 35 Meadow St. Ste 313 Brooklyn, NY 11206') and website (https://electra.com).

### Fairmat

- **`founder`:** `Benjamin Saada` → `Matteo Tesser, Matteo Carradori`  
  Sources: [company_about](https://fairmat.com/about)
- **`location`:** `Paris, France` → `Verona, Italy`  
  Sources: [company_website](https://fairmat.com)
- **`founded`:** `2020` → `2008`  
  Sources: [company_about](https://fairmat.com/about)
- **`website`:** `*(empty)*` → `https://fairmat.com`  
  Sources: [company_website](https://fairmat.com) · [company_about](https://fairmat.com/about)

  **Notes:** The database entry appears to describe a different company (carbon fiber composite recycling with AI robotics). The sources provided describe Fairmat as a regulatory technology (reg-tech) company founded in 2008 specializing in financial software and compliance solutions, not a robotics/recycling company. The founder 'Benjamin Saada' from the database entry is not mentioned in any sources. Location is identified as Verona based on a March 2026 news item, though the company's primary website and operations appear Italy-focused. No information found in sources regarding funding, valuation, or current stage.

### Figure AI

- **`location`:** `San Jose, CA` → `San Jose, California, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Figure_AI)

  **Notes:** Company initially raised $70M in May 2023 (source 2). In February 2024, secured $675M at $2.6B valuation from consortium including Bezos, Microsoft, Nvidia, Intel, Amazon, and OpenAI (source 2). Announced partnership with OpenAI which ended after one year (source 2). In September 2025, exceeded $1B in Series C funding, raising valuation to $39B (source 2). Figure 02 deployed commercially for industrial use starting August 2024 (source 2). Figure 03 introduced October 2025 for home applications (source 2).

---

## ❓ Unverifiable (14 companies)

Couldn't fetch authoritative sources. Per Stephen's rule, we leave these as-is rather than guess. May want to flag for manual research or removal from DB.

- **44.01** — *no public sources accessible*
- **AAVantgarde Bio** — *no public sources accessible*
- **ARC Clean Technology** — *no public sources accessible*
- **Aestus Industries** — *no public sources accessible*
- **Atomic AI** — *no public sources accessible*
- **Cambridge Aerospace** — *no public sources accessible*
- **Creotech Instruments** — *no public sources accessible*
- **DIRAC** — *no public sources accessible*
- **Dendra Systems** — *no public sources accessible*
- **Digantara** — *no public sources accessible*
- **Distalmotion** — *no public sources accessible*
- **Emelody** — *no public sources accessible*
- **Ephos** — *no public sources accessible*
- **Finwave Semiconductor** — *no public sources accessible*

---

## ✅ Cleared (71 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- 1X Technologies
- ABL Bio
- AIR
- ARX Robotics
- Aeon Industrial
- Aerospacelab
- Aeva Technologies
- Agile Robots
- AiDash
- AlixLabs
- Allen Control Systems
- Amber Bio
- Anduril Industries
- Apis Cor
- Applied Intuition
- Archer Materials
- Ares Industries
- Ark Robotics
- Asimov
- Astranis
- Axelera AI
- Axelspace
- Ayar Labs
- BRINC Drones
- Basecamp Research
- Baykar
- Bedrock Robotics
- Bethlehem Steel Corp
- Blackshark.ai
- Blykalla
- *...and 41 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-05-25T11:11:44+00:00*