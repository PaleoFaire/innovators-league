# Company Facts Verification Report

**Generated:** 2026-06-15T11:47:55+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 34 companies  

**New Claude extractions this run:** 34  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 24 | 71% |
| 🔧 Changes proposed | 10 | 29% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (10 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Apptronik

- **`founder`:** `Jeff Cardenas, Nick Paine` → `Jeff Cardenas`  
  Sources: [company_website](https://apptronik.com)

  **Notes:** Only Jeff Cardenas is explicitly named as founder/CEO in provided sources. Nick Paine mentioned in database entry but not verified in sources provided. Database entry claims Series A $350M and total $935M+ raised, but no funding information appears in provided sources. Source [2] title only, no content provided to verify additional details.

### Castelion

- **`fundingStage`:** `Series B` → `Series A`  
  Sources: [company_about](https://castelion.com/about)
- **`totalRaised`:** `$450M` → `$100M`  
  Sources: [company_about](https://castelion.com/about)

  **Notes:** Database entry lists Series B with $350M raise, but sources cite Series A announced January 2025 with $100M total capital raise including $70M Series A and $30M venture debt. Sources mention Blackbeard as a product (referenced in Breaking Defense article about maritime launch demonstration). No founding year explicitly stated in sources.

### Fervo Energy

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [company_website](https://fervoenergy.com)

  **Notes:** Company went public in May 2026 (confirmed by news headlines in source 0 dated May 17, 2026). Wikipedia source lists company as 'Private' but appears outdated given IPO occurred after Wikipedia article last update. Latest Series E funding of $462M in November 2025 is documented in source 2, but this predates the IPO.

### K2 Space

- **`location`:** `Torrance, CA` → `Torrance, US`  
  Sources: [company_website](https://k2space.com) · [company_about](https://k2space.com/about)
- **`fundingStage`:** `Series C` → `Series B`  
  Sources: [company_website](https://k2space.com)
- **`totalRaised`:** `$250M+` → `$110M`  
  Sources: [company_website](https://k2space.com)

  **Notes:** Website indicates $110M Series B funding announced January 15, 2025. Database entry shows conflicting total_raised ($250M+ vs $110M) and stage (Series C vs Series B); most recent source indicates Series B with $110M. Founded year not explicitly stated in sources despite database entry showing 2022. Mega Class platform specified as 20kW (not 30kW as in database entry). CEO Karan Kunjur and CTO Neel Kunjur explicitly named as co-founders.

### Mara

- **`founder`:** `Daniel Kofman (CEO; prior tactical FPV drones for DHS, first` → `Daniel Kofman, Sriram Raghu`  
  Sources: [company_about](https://mara.inc/about)

  **Notes:** Source [2] from Breaking Defense discusses Saronic and Castelion (unrelated companies) and does not contain information about Mara. Company website footer shows copyright 2026, which is a future date. Database entry claims founded 2024, pre-seed stage, and $1.6M raised, but these cannot be verified from provided sources.

### Neura Robotics

- **`fundingStage`:** `Series B` → `Series C`  
  Sources: [company_about](https://www.neura-robotics.com/about)
- **`totalRaised`:** `$123.3M` → `$1.4B`  
  Sources: [company_about](https://www.neura-robotics.com/about)

  **Notes:** Company is in Series C funding round. Sources indicate 'up to $1.4B' in Series C funding. Wikipedia mentions January 2025 Series B of €120M ($123.3M), but company website and news sources [3,4,5] reference Series C round of up to $1.4B. The most recent funding stage appears to be Series C. Database entry lists conflicting total_raised figures ($123.3M vs €281M); most recent verified amount from sources is $1.4B for Series C.

### Rocket Lab

- **`location`:** `Long Beach, CA` → `Long Beach, California, USA`  
  Sources: [company_about](https://www.rocketlabcorp.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Rocket_Lab)

  **Notes:** Company went public on Nasdaq in August 2021 via SPAC merger. Founded in Auckland, New Zealand in 2006, relocated headquarters to Huntington Beach, California in 2013, then moved to Long Beach in 2020. Has acquired six companies: Sinclair Interplanetary (2020), Advanced Solutions Inc (2021), Planetary Systems Corporation (2021), SolAero Holdings (2022), Geost LLC (2025), and Mynaric AG (2026). Database entry claims about 2025 launches (18 successful), $816M SDA contract, and market cap tripled to $37B could not be verified from provided sources.

### Saildrone

- **`founded`:** `2012` → `2009`  
  Sources: [company_about](https://saildrone.com/about)

  **Notes:** Founded year is based on the earliest operational date mentioned: 2009 when patented wing technology was developed (greenbird project). The company expanded to Europe in 2025 with Copenhagen headquarters. Richard Jenkins is identified as 'Founder & CEO' in source [1].

### SpaceX

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)
- **`investors`:** `[]` → `['Alphabet Inc.']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Wikipedia source indicates SpaceX completed IPO on June 12, 2026, valued above $2 trillion. Current database entry claims 'Preparing for IPO' which contradicts verified source showing IPO already occurred. Valuation of $800B in database entry is outdated.

### Standard Bots

- **`totalRaised`:** `$63M` → `$200M`  
  Sources: [news (The Robot Report)](https://www.therobotreport.com/standard-bots-raises-200m-expand-u-s-manufacturing-footprint/)

  **Notes:** Source [2] reports $200M raised (most recent), while source [1] mentions $63M Series B from July 2024. Source [0] references $63M figure. Location cannot be verified from sources (database entry mentions Glen Cove, NY and New York, NY but not confirmed in provided sources). Founded year 2011 cannot be verified from provided sources.

---

## ✅ Cleared (24 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- 1X Technologies
- Agility Robotics
- Andrenam
- Asylon Robotics
- Axiom Space
- Blue Origin
- Cape
- Cover
- Deterrence
- Dexterity
- FleetZero
- Harbinger
- Humanoid
- Navier
- Palantir
- Percepto
- Pivotal
- Saronic
- Standard Nuclear
- Tekever
- Vast
- Waymo
- X-Energy
- ideaForge


---

*Generated by `scripts/generate_verification_report.py` on 2026-06-15T11:47:55+00:00*