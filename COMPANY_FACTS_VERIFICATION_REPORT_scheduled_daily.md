# Company Facts Verification Report

**Generated:** 2026-09-05T08:56:49+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 37 companies  

**New Claude extractions this run:** 37  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 26 | 70% |
| 🔧 Changes proposed | 11 | 30% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (11 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Astera Labs

- **`location`:** `San Jose, CA` → `San Jose, California, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Astera_Labs)

  **Notes:** Company listed on Nasdaq under ticker ALAB since March 2024. Wikipedia source lists 2025 financial metrics (revenue US$852.5M, net income US$219.1M) but these are not historical founding/raising data. Headquarters relocated to San Jose in June 2025 from previous Santa Clara location.

### Nano Nuclear Energy

- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://nanonuclearenergy.com) · [company_about](https://nanonuclearenergy.com/about)

  **Notes:** Company is publicly listed on NASDAQ under ticker NNE. Source [2] about Valar Atomics is not relevant to this company and was not used. No founder names explicitly stated as founders in provided sources. No founded year, total raised amount, valuation, or investor names could be verified from these sources.

### Palantir

- **`location`:** `Miami, FL` → `Miami, Florida, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Palantir)

  **Notes:** Wikipedia source [0] lists former headquarters in Palo Alto, California but current headquarters as Miami, Florida. Source [0] mentions trading on Nasdaq as PLTR with 2025 revenue of $4.48 billion, but no current market cap or valuation provided in sources. Source [1] is a news article about a separate business venture and does not provide company information.

### PsiQuantum

- **`location`:** `Palo Alto, CA` → `Palo Alto, California, US`  
  Sources: [company_about](https://psiquantum.com/about) · [wikipedia](https://en.wikipedia.org/wiki/PsiQuantum)

  **Notes:** Series E $1B raised in 2025 per Wikipedia source [2]. Multiple facilities globally including Palo Alto HQ, Milpitas (PsiFactory), Daresbury UK (PsiLabs), Malta NY (GlobalFoundries Fab 8), Chicago IL (IQMP), and Queensland Australia (Moreton Bay Central and Brisbane Test & Validation Lab). Government partnerships with DARPA, US Air Force, and Australian Commonwealth/Queensland governments.

### Rivian

- **`location`:** `Irvine, CA` → `Irvine, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Rivian)

  **Notes:** Wikipedia source [2] states company was founded in Rockledge, Florida in June 2009, later moved headquarters to Irvine, California. IPO occurred November 10, 2021 on Nasdaq. Company previously named Mainstream Motors and Avera Automotive. Manufacturing facility in Normal, Illinois.

### Scale AI

- **`location`:** `San Francisco, CA` → `San Francisco, California`  
  Sources: [company_about](https://scale.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Scale_AI)

  **Notes:** In June 2025, Meta Platforms acquired a 49% non-voting stake in Scale AI for $14.8 billion. Founder Alexandr Wang left to join Meta and was replaced by Jason Droege as CEO. Company remains independent. Lucy Guo was fired in 2018 but is still listed as co-founder.

### Shield AI

- **`location`:** `San Diego, CA` → `San Diego, California, U.S.`  
  Sources: [company_about](https://shield.ai/about) · [wikipedia](https://en.wikipedia.org/wiki/Shield_AI)

  **Notes:** CEO changed from Ryan Tseng to Gary Steele in March 2025; Ryan Tseng became Chief Strategic Officer. Wikipedia indicates Series G funding of $1.5B announced March 2026 at $12.7B post-money valuation. Current database entry references Gary Steele as CEO and Ryan Tseng as President; Wikipedia sources indicate Ryan Tseng became Chief Strategic Officer, not President.

### SpaceX

- **`location`:** `Starbase, TX` → `Starbase, Texas, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** IPO on June 12, 2026 on Nasdaq (SPCX) raised $86 billion per source [0]. Database entry claims $85.7B including greenshoe, but source [0] states $86 billion. Elon Musk controls 85% voting power via super-voting stock per source [0], not 82% as in database entry. Sources [1] and [2] are news articles about other topics (OpenAI partnership, Nvidia stake) and do not provide verified founding information.

### Vertical Aerospace

- **`location`:** `Bristol, UK` → `Bristol, England, UK`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Vertical_Aerospace)

  **Notes:** Company listed on NYSE under ticker EVTL following December 2021 SPAC merger with Broadstone Acquisition Corp. The $50M figure from 2024 represents a specific Mudrick Capital investment; Wikipedia notes this was accompanied by 70% shareholding. Database entry listed 'Valo' as successor to VX4, but sources reference VX4 as current primary aircraft in development.

### Waymo

- **`location`:** `Mountain View, CA` → `Mountain View, California`  
  Sources: [company_about](https://waymo.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Waymo)

  **Notes:** Wikipedia source indicates Waymo was established as an independent company in December 2016 after spinning out from Google/Alphabet. The $16B raise in February 2026 valued the company at $126B. Waymo is a subsidiary of Alphabet Inc. Co-CEOs are Tekedra Mawakana and Dmitri Dolgov (since April 2021). Operating cities include Phoenix, San Francisco, Los Angeles, Austin, Atlanta, and others; international expansion to London, UK and Tokyo, Japan noted in sources.

### Xanadu Quantum Technologies

- **`totalRaised`:** `$245M private + ~$302M de-SPAC` → `$245M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Xanadu_Quantum_Technologies)

  **Notes:** Company is publicly traded on TSX and Nasdaq under ticker XNDU. Database entry mentions ~$302M de-SPAC valuation, but this specific figure is not found in provided sources. Only the $245M in private venture capital funding is verified in source [0].

---

## ✅ Cleared (26 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- AnySignal
- Axiom Space
- Base Power
- Cape
- Cover
- Deterrence
- Forterra
- Hadrian
- Hailo
- Mammoth Biosciences
- Neko Health
- Oklo
- Orbital Composites
- Osmo
- Oxford Nanopore Technologies
- Percepto
- Photonic Inc
- QuiX Quantum
- Radiant
- Rebellions
- Sage Geosystems
- Valar Atomics
- Vast
- Wayve
- ideaForge


---

*Generated by `scripts/generate_verification_report.py` on 2026-09-05T08:56:49+00:00*