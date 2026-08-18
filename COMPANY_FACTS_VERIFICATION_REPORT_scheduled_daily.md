# Company Facts Verification Report

**Generated:** 2026-08-18T05:38:38+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 50 companies  

**New Claude extractions this run:** 50  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 41 | 82% |
| 🔧 Changes proposed | 9 | 18% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (9 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Blue Origin

- **`fundingStage`:** `SPAC` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Blue_Origin)

  **Notes:** Database entry lists stage as 'SPAC' but Wikipedia clearly identifies company as 'Private'. Database entry cites 'Coatue Management' and 'Jeff Bezos' as investors but Wikipedia only mentions Jeff Bezos as owner/founder with no investor information provided in sources. Total raised ($10B+) and valuation listed in database entry could not be verified from provided sources.

### Groq

- **`location`:** `Mountain View, CA` → `Mountain View, California, US`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Groq)
- **`fundingStage`:** `Series C` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Groq)
- **`totalRaised`:** `$3B` → `$3.54B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Groq) · [news (TechCrunch)](https://techcrunch.com/2026/08/17/groq-raises-350m-to-fuel-its-pivot-from-ai-chips-to-neocloud/)
- **`website`:** `*(empty)*` → `https://groq.com`  
  Sources: [company_website](https://groq.com) · [company_about](https://groq.com/about)
- **`investors`:** `[]` → `['BlackRock Private Equity Partners', 'Tiger Global Manageme`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Groq) · [news (TechCrunch)](https://techcrunch.com/2026/08/17/groq-raises-350m-to-fuel-its-pivot-from-ai-chips-to-neocloud/)

  **Notes:** Wikipedia (source 2) lists Jonathan Ross as current CEO as of the article date, but source 1 (company about page) indicates Adam Winter became CEO in 2026. Wikipedia also mentions a December 2025 agreement with Nvidia reportedly valued at ~$20B for licensing and executive transfers, with Groq stating it would continue as independent. Source 3 (TechCrunch, dated 2026-08-17) reports $350M raise at $3.5B valuation during pivot from chips to neocloud. Total raised represents: $640M Series D (Aug 2024) + $650M May 2026 + $350M Aug 2026 + earlier rounds, approximately $3.54B combined.

### Muon Space

- **`location`:** `Mountain View, California` → `Silicon Valley, California`  
  Sources: [company_about](https://muonspace.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Muon_Space)

  **Notes:** Wikipedia source [2] states approximately $35 million raised by July 2023, but more recent funding information is not verifiable from provided sources. Current stage cannot be verified from sources. Database entry lists $188M total raised and Series B stage, but these specific figures are not found in provided sources.

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is publicly listed on NASDAQ under ticker NNE. Sources [0] and [1] are the same company website content. Source [2] (Canary Media article about Valar Atomics) is not relevant to NANO Nuclear Energy and was not used. Founders not explicitly named in provided sources. Founded year not specified in sources. Total raised, valuation, and investor names not found in sources.

### Planet Labs

- **`location`:** `San Francisco, CA` → `San Francisco, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Planet_Labs)

  **Notes:** Company formerly known as Cosmogia, Inc. and Planet Labs, Inc. Completed SPAC merger with DMY Technology Group Inc IV on December 7, 2021, becoming publicly traded on NYSE under ticker PLN on December 8, 2021. Registered as public benefit corporation (PBC). Valuation of $2.8B refers to the merger deal announced in July 2021.

### Satellogic

- **`location`:** `Wilmington, DE` → `Delaware, USA`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Satellogic)

  **Notes:** Company redomiciled to Delaware in 2025 and is listed on Nasdaq under ticker SATL. Went public in January 2022 via SPAC merger with CF Acquisition Corp. V. As of September 2025, has launched more than 50 ÑuSat satellites.

### SpaceX

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** SpaceX completed initial public offering on June 12, 2026, raising $86 billion (largest IPO in history per source). Wikipedia source indicates Elon Musk controls 85% of voting power; database entry states 82%. Nvidia disclosed $21B stake per Ars Technica source [1]. No current valuation figure found in sources; database entry claims $1.65T.

### Terrahaptix

- **`fundingStage`:** `Series A` → `Seed`  
  Sources: [news (TechCrunch)](https://techcrunch.com/2026/08/17/terra-industries-closes-52m-seed-round-to-build-defense-infrastructure-for-the-global-south/)
- **`totalRaised`:** `$34M` → `$52M`  
  Sources: [news (TechCrunch)](https://techcrunch.com/2026/08/17/terra-industries-closes-52m-seed-round-to-build-defense-infrastructure-for-the-global-south/)

  **Notes:** Company operates under the name 'Terra Industries' (not 'Terrahaptix' as in database entry). Source [1] states seed round extended to $52M with additional $18M. No founder names, founding year, valuation, or specific investor names could be verified from provided sources. Database entry lists different stage (Series A) and total_raised ($34M) than sources.

### Zipline

- **`location`:** `South San Francisco, CA` → `South San Francisco, California`  
  Sources: [company_about](https://zipline.com/about)
- **`founded`:** `2014` → `2016`  
  Sources: [company_about](https://zipline.com/about)

  **Notes:** Source [1] states 'Giving more time to local communities since 2016' which differs from database entry of 2014. Source [2] is Wikipedia article about zip-line (recreational equipment), not the company Zipline. Source [3] is a TechCrunch article title but content was not provided to verify claims. Founder names could not be verified from provided sources. Series stage, total_raised, valuation, and specific investor list could not be verified from provided sources.

---

## ✅ Cleared (41 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- Apptronik
- Astera Labs
- Astranis
- Aurora Innovation
- Base Power
- Cape
- Deterrence
- Dragonfly Aerospace
- Einride
- FlyBy Robotics
- Galvanick
- HEO
- Harbinger
- Helsing
- Humanoid
- ICEYE
- Icarus
- Intuitive Machines
- Isembard
- Neros
- Neura Robotics
- Oklo
- Palantir
- Parallel Systems
- Persona AI
- Photonic Inc
- Pixxel
- Quaise Energy
- Quantum-Systems
- *...and 11 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-08-18T05:38:38+00:00*