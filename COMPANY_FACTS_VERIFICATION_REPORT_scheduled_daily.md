# Company Facts Verification Report

**Generated:** 2026-05-09T07:46:28+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 44 companies  

**New Claude extractions this run:** 43  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 36 | 82% |
| 🔧 Changes proposed | 8 | 18% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (8 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Alpha School

- **`investors`:** `[]` → `['Joe Liemandt', 'ESW Capital']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Alpha_School)

  **Notes:** Wikipedia source [2] confirms 13 campuses as of April 2026 across Arizona, California, Florida, New York, Texas, and Virginia. Tuition ranges $10,000-$75,000 per year per source [2]. Joe Liemandt identified as principal in source [2]. Database entry references '~$1B Liemandt commitment' but no specific funding amount is verified in provided sources. Founded as spinoff of Acton Academy, formerly called Emergent Academy per source [2].

### Fervo Energy

- **`fundingStage`:** `IPO` → `Pre-IPO`  
  Sources: [company_website](https://fervoenergy.com)

  **Notes:** Source [0] (company website) indicates IPO launch announced May 4, 2026, and registration statement filing announced April 17, 2026, placing company in Pre-IPO stage rather than public. Source [2] (Wikipedia) notes company received $462 million Series E funding in November 2025 led by B Capital. Database entry states 'IPO' but sources show Pre-IPO status as of filing dates in April-May 2026.

### Nuro

- **`location`:** `Mountain View, CA` → `Mountain View, California`  
  Sources: [company_about](https://nuro.ai/company) · [wikipedia](https://en.wikipedia.org/wiki/Nuro)
- **`fundingStage`:** `Series G` → `Series E`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Nuro)

  **Notes:** Company pivoted from autonomous delivery vehicles to licensing autonomous driving technology in September 2024. Most recent funding: August 2025 Series E closing with $203M at $6B valuation from Uber and Nvidia. Partnership with Uber and Lucid Motors announced July 2025 for 20,000+ robotaxis deployment over six years.

### Nyobolt

- **`location`:** `Cambridge, UK` → `Cambridge, United Kingdom`  
  Sources: [company_about](https://nyobolt.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Nyobolt)

  **Notes:** Database entry claims $150M contracted backlog and $100M+ total raised, but these specific figures are not found in provided sources. Sources mention Series A and B funding rounds and $30M recent funding (April 2025) but no total raised amount. No valuation data found in sources.

### OpenAI

- **`founder`:** `Sam Altman, Greg Brockman, Ilya Sutskever` → `Elon Musk, Sam Altman, Ilya Sutskever, Greg Brockman, Trevor`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/OpenAI)

  **Notes:** Wikipedia states that in October 2025, OpenAI conducted a $6.6 billion share sale that valued the company at $500 billion. Company transitioned to for-profit capped entity in 2019. io Products, Inc. team merged with OpenAI in July 2025 per source 0.

### Percepto

- **`location`:** `Israel` → `Israel, United States`  
  Sources: [company_about](https://percepto.co/about)

  **Notes:** Founded year 2014 confirmed via leadership biography stating 'Co-founding Percepto in 2014'. Location identified as both Israel and US based on source [1] stating 'visionary team based in the US and Israel'. No verifiable information found regarding current funding stage, total raised, valuation, or specific investor names in provided sources.

### Starcloud

- **`fundingStage`:** `SPAC` → `Series A`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starcloud)

  **Notes:** Company was originally founded as 'Lumen Orbit' in January 2024 in El Segundo, California and rebranded to Starcloud in March 2025 after a legal challenge from Lumen Technologies. Series A announced March 30, 2026, making it the fastest Y Combinator company to reach unicorn status at 17 months post-demo day.

### Waymo

- **`location`:** `Mountain View, CA` → `Mountain View, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Waymo)
- **`fundingStage`:** `Late Stage` → `Pre-IPO`  
  Sources: *(no sources cited)*

  **Notes:** Wikipedia states Waymo was founded December 13, 2016, tracing origins to Stanford Racing Team (2004) and Google Self-Driving Car Project (January 17, 2009). February 2026 funding round valued company at $126B. Wikipedia indicates 500,000 paid rides per week as of March 2026; database entry references 200K+ paid rides per week which appears outdated. Current stage marked as 'Pre-IPO' as company remains subsidiary of Alphabet with no public IPO announced.

---

## ✅ Cleared (36 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Andromeda Surgical
- Anthropic
- Anysphere
- Astera Labs
- Axiom Space
- Blue Origin
- Claros
- Daylight Computer
- Deterrence
- Durin
- Dust
- GITAI
- Galvanick
- Gecko Robotics
- Groq
- HEO
- Hidden Level
- Hugging Face
- ICON
- Karman Industries
- Kyutai
- Palantir
- Photonic Inc
- Pivotal
- QuantWare
- Quantum Motion
- Rebellions
- Rivian
- Rocket Lab
- Solugen
- *...and 6 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-05-09T07:46:28+00:00*