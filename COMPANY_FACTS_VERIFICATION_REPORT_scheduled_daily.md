# Company Facts Verification Report

**Generated:** 2026-08-21T05:40:14+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 44 companies  

**New Claude extractions this run:** 44  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 35 | 80% |
| 🔧 Changes proposed | 9 | 20% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (9 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Cerebras

- **`location`:** `Sunnyvale, CA` → `Sunnyvale, California, US`  
  Sources: [company_website](https://cerebras.ai) · [company_about](https://cerebras.ai/company) · [wikipedia](https://en.wikipedia.org/wiki/Cerebras)

  **Notes:** Company is publicly traded on Nasdaq under ticker CBRS. Sources do not provide specific IPO date, total amount raised, or current valuation, so these fields cannot be verified despite being mentioned in the database entry.

### Muon Space

- **`totalRaised`:** `$188M` → `$250M`  
  Sources: [news (SpaceNews)](https://spacenews.com/muon-space-raises-250-million-to-ramp-up-satellite-production/)

  **Notes:** Wikipedia source [2] references $35M raised by July 2023, but more recent source [3] (SpaceNews) reports $250M total raised. Used most recent figure per instruction to prefer most recent and specific data. Source [3] headline states the $250M figure but full article text not provided. Founded year 2021 confirmed in multiple sources. Company has two facilities in Silicon Valley: Mountain View (18,000 sq ft payload facility) and San Jose (130,000 sq ft headquarters and production facility per source [1]).

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is publicly traded on NASDAQ under ticker NNE. Sources do not contain founder information, founding year, total raised, valuation, or investor details. Source [2] appears to be about a different company (Valar Atomics) and was not used. Database entry claims about ODIN sale to Cambridge AtomWorks and specific founding year/valuation could not be verified from provided sources.

### Portal Space Systems

- **`location`:** `Bothell, WA` → `Bothell, Washington`  
  Sources: [company_about](https://portalsystems.space/about) · [wikipedia](https://en.wikipedia.org/wiki/Portal_Space_Systems)

  **Notes:** Wikipedia source [2] lists Ian Vorbach as COO rather than President and CRO as shown on company website. Total raised of $62.85M cannot be verified from sources; source [1] states 'Over $20M in VC Funding to Date' and source [2] mentions $3M (April 2024), $17.5M seed round (2025), and $45M STRATFI (December 2025) which sum to $65.5M, plus $350K Washington State grant. Database entry claims $70M+ total but this cannot be verified. Current stage shown as 'Series A' based on source [0] press release title mentioning Series A, though source [2] describes funding as seed round and STRATFI rather than traditional Series A.

### PsiQuantum

- **`location`:** `Palo Alto, CA` → `Palo Alto, California, USA`  
  Sources: [company_about](https://psiquantum.com/about) · [wikipedia](https://en.wikipedia.org/wiki/PsiQuantum)

  **Notes:** Series E funding of $1B raised in 2025 according to Wikipedia. Database entry claims September 2025 Series E with $7B valuation and specific investors (BlackRock, NVIDIA, Temasek), but these details are not found in provided sources. Company has facilities in Palo Alto CA, Milpitas CA, Daresbury UK, Malta NY, Chicago IL, and Queensland Australia.

### SpaceX

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** IPO occurred June 12, 2026, raising $86B (largest IPO in history per source). Wikipedia shows Elon Musk controls 85% voting power via super-voting stock (database entry stated 82%). Database entry claims $1.65T valuation and 'Preparing for IPO' but source confirms IPO already completed as of June 2026. Database claims 165 Falcon 9 launches in 2025 and 81% of mass launched to orbit - not verifiable in provided sources. Database claims 9M+ Starlink customers - not verifiable in provided sources.

### Starcloud

- **`location`:** `Redmond, WA` → `Redmond, Washington`  
  Sources: [company_website](https://www.starcloud.com) · [wikipedia](https://en.wikipedia.org/wiki/Starcloud)
- **`fundingStage`:** `Seed` → `Series A`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starcloud)

  **Notes:** Originally founded as 'Lumen Orbit' in January 2024 in El Segundo, California; rebranded to Starcloud in March 2025 after legal challenge from Lumen Technologies. Wikipedia source [2] states Series A was announced on March 30, 2026, led by Benchmark and EQT Ventures. Company achieved unicorn status 17 months after completing Y Combinator program. Starcloud-1 launched November 2025; Starcloud-2 planned for late 2026.

### Together AI

- **`fundingStage`:** `Series G` → `Series C`  
  Sources: [company_website](https://www.together.ai) · [company_about](https://www.together.ai/about)

  **Notes:** Series C announced on website but no funding amount, valuation, or investor details provided in sources. Sources [2] and [3] are about robotaxis and Tesla/SpaceX, not Together AI, so they were not used. Founded year and location could not be verified from provided sources.

### Zettascale

- **`location`:** `San Francisco, CA` → `San Francisco, CA, USA`  
  Sources: [company_website](https://zscc.ai)

  **Notes:** Source [0] announces 'our new name, Zettascale' indicating a rebrand, consistent with database note about rebrand/pivot of Exa Laborato. Source [1] is not relevant to Zettascale. No specific founder names, founding year, stage, or funding amount could be verified from provided sources despite database entry containing these details.

---

## ✅ Cleared (35 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- AnySignal
- Astera Labs
- Aurora Innovation
- Base Power
- Castelion
- Deterrence
- Divergent
- Einride
- Firefly Aerospace
- Firestorm Labs
- Galvanick
- Hadrian
- Harbinger
- Helsing
- Humanoid
- ICON
- Machina Labs
- Oklo
- Orbital Composites
- Palantir
- Parallel Systems
- Pivotal
- Proteus Space
- Quaise Energy
- Radiant
- Revel
- Rivian
- Rocket Lab
- Sage Geosystems
- *...and 5 more*


---

*Generated by `scripts/generate_verification_report.py` on 2026-08-21T05:40:14+00:00*