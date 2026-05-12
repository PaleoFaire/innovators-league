# Company Facts Verification Report

**Generated:** 2026-05-12T08:28:44+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 43 companies  

**New Claude extractions this run:** 42  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 35 | 81% |
| 🔧 Changes proposed | 8 | 19% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (8 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Fervo Energy

- **`fundingStage`:** `IPO` → `Pre-IPO`  
  Sources: [company_website](https://fervoenergy.com)

  **Notes:** Company announced IPO filing on April 17, 2026 and launched IPO on May 4, 2026. Most recent funding was Series E of $462 million in November 2025 led by B Capital. Wikipedia source notes article quality concerns but founder names and founding year are consistent across sources.

### Nuro

- **`fundingStage`:** `Series G` → `Series E`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Nuro)

  **Notes:** Company pivoted from autonomous delivery vehicles to technology licensing model in September 2024. Series E funding opened April 2025 ($106M) and closed August 2025 ($203M additional at $6B valuation). Partnership with Uber and Lucid Motors to deploy 20,000+ robotaxis announced July 2025.

### OpenAI

- **`founder`:** `Sam Altman, Greg Brockman, Ilya Sutskever` → `Elon Musk, Sam Altman, Ilya Sutskever, Greg Brockman, Trevor`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/OpenAI)

  **Notes:** Wikipedia source [2] specifies October 2025 $6.6 billion share sale valuing company at $500 billion. Founded as nonprofit in December 2015; transitioned to for-profit capped entity in 2019; restructured in 2025 with nonprofit retaining 26% ownership. Sam Altman temporarily removed as CEO in November 2023 but reinstated five days later.

### Redwood Materials

- **`location`:** `Carson City, NV` → `Carson City, Nevada, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Redwood_Materials)
- **`totalRaised`:** `$1B+` → `$1.125B+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Redwood_Materials)

  **Notes:** Wikipedia states $775M Series C (2021) and $350M Series E (2025), totaling $1.125B+ in disclosed funding. Valuation of $6 billion as of October 2025 per Wikipedia. Current stage not explicitly stated in sources. Company acquired Redux (German recycler) in 2023.

### Safe Superintelligence

- **`location`:** `Palo Alto, CA / Tel Aviv, Israel` → `Palo Alto, California / Tel Aviv, Israel`  
  Sources: [company_website](https://ssi.inc) · [wikipedia](https://en.wikipedia.org/wiki/Safe_Superintelligence)

  **Notes:** Wikipedia states 50 employees as of July 2025 (source 1), contradicting database entry of ~20 employees. Valuation updated to $30B as of March 2025 (source 1). Daniel Gross left the company in July 2025 to join Meta Superintelligence Labs (source 1). No specific funding stage (Series A/B/C) is mentioned in sources.

### Space Forge

- **`location`:** `Cardiff, UK` → `Cardiff, United Kingdom`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Space_Forge)

  **Notes:** Wikipedia indicates Series A funding of £22.6 million (approximately $22.6M USD equivalent as stated in database) was announced in July 2024 combining support from NATO Innovation Fund, World Fund, and British Business Bank. ForgeStar-0 launched January 2023 but failed to achieve orbit. ForgeStar-1 successfully launched June 2025.

### SpaceX

- **`fundingStage`:** `Series G` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Wikipedia states company is headquartered at Starbase in Starbase, Texas (not El Segundo where it was first founded in 2002). Wikipedia indicates SpaceX 'is not publicly traded but is expected to have an initial public offering (IPO) in 2026.' Valuation of $800 billion comes from 'a 2025 offer to buy internal shares.' Source 5 (SEC Form D) mentions a SpaceX Investors 5 LLC raised $9,725,064 in May 2026, but this appears to be an internal secondary offering, not primary fundraising. Total raised cannot be verified from these sources.

### Starcloud

- **`fundingStage`:** `SPAC` → `Series A`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starcloud)

  **Notes:** Company was originally founded as Lumen Orbit in January 2024 in El Segundo, California and rebranded to Starcloud in March 2025 after a legal challenge from Lumen Technologies. Series A announced March 30, 2026, making it the fastest Y Combinator company to reach unicorn status at 17 months after completing the program.

---

## ✅ Cleared (35 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- AMP Robotics
- Andromeda Surgical
- Anthropic
- Anysphere
- Astera Labs
- Axiom Space
- Blue Origin
- Claros
- Deterrence
- Dexterity
- Durin
- GITAI
- Galvanick
- Groq
- HEO
- Helsing
- Hidden Level
- Hugging Face
- Kyutai
- Nyobolt
- Ouster
- Percepto
- Physical Intelligence
- Pivotal
- Quantum Motion
- Rebellions
- Rivian
- Rocket Lab
- Skild AI
- Thinking Machines Lab
- *...and 5 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-05-12T08:28:45+00:00*