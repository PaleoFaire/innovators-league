# Company Facts Verification Report

**Generated:** 2026-05-21T08:57:35+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 27 companies  

**New Claude extractions this run:** 26  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 19 | 70% |
| 🔧 Changes proposed | 8 | 30% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (8 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Boston Metal

- **`location`:** `Woburn, MA` → `Woburn, Massachusetts`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Boston_Metal)

  **Notes:** Tadeu Carneiro joined as CEO in 2017 (not founder, but listed as 'Chairman & CEO' and key person in Wikipedia). Source [1] title mentions '$75 million funding round' but article text is incomplete; cannot verify this amount or current stage from available sources. Wikipedia states 'over $370,000,000 as of January 2024'.

### Colossal Biosciences

- **`location`:** `Dallas, Texas` → `Dallas, Texas, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Colossal_Biosciences)

  **Notes:** Wikipedia source (2) states total valuation is $10.2B as of January 2025 with $200M Series C funding, superseding the database entry of $1.5B. Total raised of $435M is confirmed by Wikipedia. Company acquired ViaGen Pets in November 2025 and established Colossal Australia in August 2025.

### Fervo Energy

- **`fundingStage`:** `IPO` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fervo_Energy)
- **`totalRaised`:** `$1.89B` → `$1.5B+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fervo_Energy)

  **Notes:** Wikipedia source indicates company is Private, not IPO. Database entry states 'IPO' stage and valuation is unverified. Wikipedia reports November 2025 Series E funding of $462M, bringing total backed funding to 'over $1.5 billion in equity, debt and grant funding.' Sources [1], [2], [3] (news URLs) are present but content not provided for verification of IPO claims.

### Nuro

- **`fundingStage`:** `Series G` → `Series E`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Nuro)

  **Notes:** Company pivoted business model in September 2024 from autonomous delivery vehicle manufacturing to licensing Nuro Driver L4 autonomy technology. August 2025 Series E funding round ($203M at $6B valuation) included Uber and Nvidia. Partnership with Uber and Lucid Motors announced July 2025 for robotaxi deployment targeting 20,000+ vehicles over six years.

### SpaceX

- **`fundingStage`:** `Series G` → `Pre-IPO`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Wikipedia source indicates SpaceX 'is expected to have an initial public offering (IPO) in 2026' and notes that 'a 2025 offer to buy internal shares valued SpaceX at $800 billion.' Founded March 14, 2002 in El Segundo, California, currently headquartered in Starbase, Texas. Company is private and not publicly traded.

### Vertical Aerospace

- **`location`:** `Bristol, UK` → `Bristol, England, UK`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Vertical_Aerospace)
- **`totalRaised`:** `$400M+` → `$50M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Vertical_Aerospace)

  **Notes:** Company went public via SPAC merger with Broadstone Acquisition Corp in December 2021, trading on NYSE under ticker EVTL. The $50M figure is from a 2024 Mudrick Capital investment; earlier SPAC valuation was $2.2B but this was not a direct capital raise. Source [1] is not relevant to company facts and was not used.

### X-Energy

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [company_website](https://x-energy.com)

  **Notes:** Source [0] confirms IPO: 'X-energy Announces Pricing of Upsized Initial Public Offering' (Apr 23, 2026) and 'X-energy Announces Launch of its Initial Public Offering' (Apr 15, 2026). Cannot verify: founder name (not stated in sources), founded year, total_raised, valuation, or specific investor names. Database entry claims about Amazon funding, Pentagon/Air Force contracts, and UK deployment cannot be verified from provided sources.

### Zoox

- **`founder`:** `*(empty)*` → `Tim Kentley-Klay, Jesse Levinson`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Zoox)
- **`location`:** `*(empty)*` → `Foster City, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Zoox)
- **`founded`:** `*(empty)*` → `2014`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Zoox)
- **`fundingStage`:** `*(empty)*` → `Acquired`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Zoox)
- **`totalRaised`:** `*(empty)*` → `$1.2B+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Zoox)

  **Notes:** Acquired by Amazon on June 26, 2020 as a wholly owned subsidiary for over $1.2 billion. Valuation of $3.2 billion was as of July 2018 according to Bloomberg. Company operates as separate legal entity with own governance structure within Amazon Devices & Services organization.

---

## ✅ Cleared (19 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Astera Labs
- Cerebras
- Crusoe Energy
- Deterrence
- Earth AI
- Einride
- Fractile
- Galvanick
- Gecko Robotics
- Hidden Level
- IonQ
- Karman Industries
- Quantinuum
- Rebellions
- Rivian
- Solugen
- Space Forge
- Standard Nuclear
- Waymo


---

*Generated by `scripts/generate_verification_report.py` on 2026-05-21T08:57:35+00:00*