# Company Facts Verification Report

**Generated:** 2026-08-29T11:35:32+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 45 companies  

**New Claude extractions this run:** 45  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 38 | 84% |
| 🔧 Changes proposed | 7 | 16% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (7 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### 1X Technologies

- **`location`:** `Palo Alto, CA` → `Palo Alto, California, USA`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)
- **`fundingStage`:** `Pre-Seed` → `Series B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)
- **`totalRaised`:** `$1.1B` → `$123.5M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/1X_Technologies)

  **Notes:** Company was originally founded as Halodi Robotics in 2014 and rebranded to 1X Technologies in 2022. Sources 0 and 1 refer to a completely different company (1X Technologies LLC, a wire and cable distributor in Wyoming, founded 2015). Wikipedia source (2) is the relevant company. Total raised calculated from Series A2 ($23.5M in March 2023) plus Series B ($100M in January 2024) = $123.5M.

### Agility Robotics

- **`fundingStage`:** `Series E` → `Pre-IPO`  
  Sources: [company_website](https://agilityrobotics.com)

  **Notes:** Company announced merger with Churchill Capital Corp XI on June 24, 2026 to go public (Source 0). Company rebranded as 'Agility' on March 5, 2026 per Wikipedia (Source 2), though primary sources still reference 'Agility Robotics' as of July 2026. Database entry lists $400M+ raised and specific investors, but these details are not verifiable in provided sources.

### Bedrock Robotics

- **`totalRaised`:** `$350M+` → `$270M`  
  Sources: [company_about](https://bedrockrobotics.com/about)

  **Notes:** Source [1] mentions '$80M' Series A (Forbes reference) and '$270M Series B' (New York Times reference). Only the Series B figure is directly cited in provided sources. Founder names are mentioned in database entry but not explicitly listed as founders in provided sources — only described as 'founding team' with Waymo background. Founded year not specified in sources despite database entry claiming 2024.

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is publicly listed on NASDAQ under ticker NNE. Database entry references founder 'Jay Jiang Yu' and various financial metrics ($600M+ raised, $808M valuation, market cap ~$1.2B June 2026) but these cannot be verified from provided sources. Database entry also references ODIN design sale to Cambridge AtomWorks, not mentioned in sources. No founder information found in sources provided.

### QuiX Quantum

- **`founder`:** `Hans van den Vlekkert, Jelmer Renema` → `Jelmer Renema`  
  Sources: [company_about](https://www.quixquantum.com/about)

  **Notes:** Database entry lists 'Hans van den Vlekkert' as co-founder, but sources only explicitly name Dr. Jelmer Renema as founder (listed as Chief Scientist in C-Team). Hans van den Vlekkert not mentioned in provided sources. Database lists Series A stage and €15M raised, but current sources do not confirm this funding stage or amount. Company has expanded to offices in Amsterdam, Ulm, and Stuttgart by 2022. Carina universal photonic quantum computer delivered to DLR (German Aerospace Center) in July 2026.

### SpaceX

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** SpaceX completed its IPO on June 12, 2026, raising $86 billion, described as the largest IPO in history. Elon Musk owns 42% equity with 85% voting control (Wikipedia states 82% voting control in one section and 85% in another; using the later more specific statement). No current valuation figure found in sources; database entry claims $1.65T but this is not verified in provided sources.

### Starcloud

- **`fundingStage`:** `Seed` → `Series A`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starcloud)

  **Notes:** Originally founded as 'Lumen Orbit' in January 2024 in El Segundo, California; rebranded to Starcloud in March 2025 following legal challenge from Lumen Technologies. Series A announced March 30, 2026, making it the fastest Y Combinator company to reach unicorn status at 17 months post-demo day.

---

## ✅ Cleared (38 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- AnySignal
- Apptronik
- Asimov
- Astera Labs
- Aurora Innovation
- Base Power
- Cape
- Carbon Robotics
- Cognition
- Destinus
- Deterrence
- Einride
- Galvanick
- Gecko Robotics
- Hadrian
- Humanoid
- Karman Industries
- Matter
- Oklo
- Orbital Composites
- Percepto
- Photonic Inc
- Pivotal
- Profluent
- Proteus Space
- PsiQuantum
- Q-CTRL
- Radiant
- Rebellions
- *...and 8 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-08-29T11:35:32+00:00*