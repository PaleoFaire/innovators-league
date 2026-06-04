# Company Facts Verification Report

**Generated:** 2026-06-04T09:45:54+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 32 companies  

**New Claude extractions this run:** 32  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 23 | 72% |
| 🔧 Changes proposed | 9 | 28% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (9 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### AST SpaceMobile

- **`location`:** `Midland, TX` → `Midland, Texas, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/AST_SpaceMobile)

  **Notes:** Founded as AST & Science LLC in May 2017; became AST SpaceMobile via SPAC merger in April 2021 and began trading on Nasdaq. Wikipedia lists website as ast-science.com while company website header shows astspacemobile.com; both are verified in sources.

### Atom Computing

- **`location`:** `Berkeley, CA` → `Berkeley, California`  
  Sources: [company_website](https://atom-computing.com) · [company_about](https://atom-computing.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Atom_Computing)

  **Notes:** Wikipedia entry mentions Rob Hayes served as CEO in 2021, but company website identifies Ben Bloom as Founder & CEO and Rob Hays as CEO & President with different spelling. The database entry references a 2025 sale of Magne system to QuNorth, but this is not verified in provided sources. Company website shows press release dated May 21, 2026 regarding $100M Letter of Intent with U.S. Department of Commerce, and June 3, 2026 announcements about quantum error correction, indicating sources are from future dates relative to Wikipedia's last update.

### Fervo Energy

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [company_website](https://fervoenergy.com)
- **`totalRaised`:** `$1.5B+` → `$1.89B`  
  Sources: [company_website](https://fervoenergy.com)

  **Notes:** Company went public on May 17, 2026 (per source 0 newsroom articles dated May 17, 2026). Wikipedia source [2] lists company type as 'Private' but this predates the IPO announcement in source [0]. IPO raised $1.89B according to source [0] headline. Series E funding of $462M mentioned in source [2] from November 2025, but total_raised figure of $1.89B from IPO is more recent.

### Impulse Space

- **`totalRaised`:** `$1.025B` → `$1.525B`  
  Sources: [company_about](https://impulsespace.com/about) · [news (SpaceNews)](https://spacenews.com/impulse-space-raises-500-million/)

  **Notes:** Source [1] shows funding progression: $30M seed (2022), $45M Series A (2023), $150M Series B (2024), $300M Series C (2025), and $500M Series D (2026). Total verified: $1.025B + $500M = $1.525B. Current stage cannot be verified from sources (database entry lists 'SPAC' but this is not confirmed in sources). Valuation not stated in sources.

### Mach Industries

- **`totalRaised`:** `$100M+` → `$300M`  
  Sources: [news (The Robot Report)](https://www.therobotreport.com/autonomous-defense-manufacturer-mach-industries-raises-300m/)

  **Notes:** Valuation of $1.8B cited in TechCrunch article linked on company website (source 0). Most recent funding round of $300M from source 2. Database entry lists founder 'Ethan Thornton' but this is not explicitly stated in provided sources as founder/co-founder. Founded year 2023 in database cannot be verified from sources. Location 'Huntington Beach, CA' cannot be verified from sources.

### Mara

- **`location`:** `San Francisco, CA` → `Hallandale Beach, Florida`  
  Sources: [company_website](https://mara.com)
- **`fundingStage`:** `Seed` → `Public`  
  Sources: [company_website](https://mara.com)
- **`website`:** `*(empty)*` → `https://mara.com`  
  Sources: [company_website](https://mara.com)

  **Notes:** Database entry describes 'Mara' as autonomous robotic defense systems company, but sources [0] and [1] describe MARA Holdings Inc. as a digital energy/AI infrastructure company operating data centers and power systems (NASDAQ: MARA, publicly traded). Source [2] references Mach Industries (different company), not MARA. No founder 'Daniel Kofman' mentioned in sources. No founded year 2024 found. Database entry appears to describe a different company entirely.

### SpaceX

- **`fundingStage`:** `Series G` → `Pre-IPO`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Wikipedia states SpaceX 'is expected to have an initial public offering (IPO) in 2026' and notes 'a 2025 offer to buy internal shares valued SpaceX at $800 billion.' Source [2] references a planned IPO raising at least $75B with valuation over $1.75T, but this appears to be speculative/projected and conflicts with the verified $800B valuation from actual internal share offers cited in Wikipedia. Total_raised field set to null because sources do not provide a specific cumulative fundraising amount.

### Starcloud

- **`location`:** `Redmond, WA` → `Redmond, Washington, USA`  
  Sources: [company_website](https://www.starcloud.com) · [wikipedia](https://en.wikipedia.org/wiki/Starcloud)
- **`fundingStage`:** `SPAC` → `Series A`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starcloud)

  **Notes:** Originally founded as Lumen Orbit in January 2024 in El Segundo, California; rebranded to Starcloud in March 2025 following legal challenge from Lumen Technologies. Became fastest unicorn in Y Combinator history at 17 months after completing program (March 2026). Series A funding announced March 30, 2026.

### Varda Space Industries

- **`fundingStage`:** `Series C` → `Series B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Varda_Space_Industries)

  **Notes:** Wikipedia indicates Series B funding of $90M announced in April 2024. Database entry claims Series C with $187M, but this cannot be verified in provided sources. Latest verifiable funding round from sources is Series B ($90M in April 2024).

---

## ✅ Cleared (23 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Astera Labs
- Axiom Space
- Blue Origin
- Crusoe Energy
- Deterrence
- Endurosat
- HEO
- Humanoid
- Muon Space
- Oxford Quantum Circuits
- Palantir
- Percepto
- Photonic Inc
- Pivotal
- Quantum-Systems
- Rebellions
- Rivian
- Space Forge
- Standard Nuclear
- Vast
- Waymo
- X-Energy
- ideaForge


---

*Generated by `scripts/generate_verification_report.py` on 2026-06-04T09:45:54+00:00*