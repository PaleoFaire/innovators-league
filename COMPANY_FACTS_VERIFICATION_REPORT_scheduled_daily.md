# Company Facts Verification Report

**Generated:** 2026-06-05T09:35:23+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 42 companies  

**New Claude extractions this run:** 42  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 30 | 71% |
| 🔧 Changes proposed | 12 | 29% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (12 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### AMP Robotics

- **`location`:** `Louisville, CO` → `Colorado`  
  Sources: [company_about](https://amprobotics.com/about)

  **Notes:** Source [2] (Electrek article about Waymo batteries) is not relevant to AMP Robotics and was not used. Database entry lists founder as 'Matanya Horowitz' and founded year as '2014', but these cannot be verified from provided sources. Database lists Series C stage and $180M+ raised, but these cannot be verified from provided sources. About page mentions 'hundreds of systems installed across three continents' but no specific founding year or funding stage information found in sources.

### AstroForge

- **`location`:** `Huntington Beach, CA` → `Huntington Beach, California, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/AstroForge)

  **Notes:** Wikipedia source [2] mentions $13 million in seed funding but database entry shows $53M total raised. Wikipedia also references a $40 million raise in August 2024 (source [2] footnote 9), which would total approximately $53M. Company headquarters also listed as 'Seal Beach' on source [0], but Wikipedia and database confirm Huntington Beach, California. Odin spacecraft launched February 27, 2025 and was declared lost on March 6, 2025. DeepSpace-2 planned for Q4 2026 launch.

### Atom Computing

- **`totalRaised`:** `$100M+` → `$60M`  
  Sources: [company_about](https://atom-computing.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Atom_Computing)

  **Notes:** Series B funding of $60M closed in January 2022 per source [1]. Rob Hays is identified as CEO & President in source [1], though Ben Bloom is listed as Founder & CEO. Microsoft partnership announced late 2024 with logical qubits demonstrated. Source [3] URL provided but content not fully visible in extraction.

### Cape

- **`founder`:** `John Doyle, Gavin Uhma` → `John Doyle`  
  Sources: [company_about](https://www.cape.co/about)

  **Notes:** Source [2] (Wikipedia) is about the clothing item 'cape' and is not relevant. Source [3] (Defense One) is about Blue Origin and is not relevant. Founded year 2022 in database entry but not verified in provided sources. Series C stage and $195M total raised from database entry could not be verified in provided sources. Second co-founder 'Gavin Uhma' from database entry could not be verified in provided sources. Only John Doyle explicitly named as founder/CEO in sources [0, 1]. A* Capital and Fifth Down Capital, FDVC, Karman Ventures, Point72, XYZ listed visually in source [1] but not explicitly named as investors in text.

### Endurosat

- **`founder`:** `Raycho Raychev, Stanimir Gantchev` → `Raycho Raychev`  
  Sources: [company_about](https://endurosat.com/about)

  **Notes:** Source [1] confirms Raycho Raychev as Founder & CEO; only one founder explicitly named in sources. Source [2] mentions Series C fundraising but does not provide current stage confirmation or total amount raised. Founded year confirmed as 2015 from timeline in source [1] ('Company founded in an attic apartment'). Location inferred as Sofia, Bulgaria based on company operations but not explicitly stated in provided sources.

### Fervo Energy

- **`totalRaised`:** `$1.89B IPO` → `$1.5B+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fervo_Energy)

  **Notes:** Wikipedia source (index 0) lists company as 'Private' as of the article date, contradicting the database entry's claim of a May 2026 IPO. The IPO sources (indices 1-2) are headlines only with no accessible content to verify IPO details. Most recent verifiable funding is $462 million Series E in November 2025 led by B Capital. Cape Station expected to come online by 2026.

### Form Energy

- **`location`:** `Somerville, MA` → `Somerville, MA, US`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Form_Energy)

  **Notes:** Source [1] (TechCrunch article about Waymo batteries) does not contain relevant information about Form Energy and was not used. Wikipedia source provides comprehensive verified information but does not specify current funding stage or latest valuation.

### Helion

- **`investors`:** `[]` → `['Sam Altman']`  
  Sources: [news (TechCrunch)](https://techcrunch.com/2026/06/04/helion-the-sam-altman-backed-fusion-startup-raises-465m-to-build-a-power-plant-for-microsoft/)

  **Notes:** Only one source provided (TechCrunch article). Article confirms $465M fundraise (differs from database entry of $425M Series F) and 2028 Microsoft power plant delivery commitment. Cannot verify other fields (founders, location, founded_year, total_raised, valuation, stage) without additional sources. Sam Altman identified as backer/investor.

### Impulse Space

- **`fundingStage`:** `SPAC` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Impulse_Space)

  **Notes:** Recent $500M Series D funding announced in June 2026 (source [3] and [4]) brings total raised to approximately $1.525B, but valuation not explicitly stated in sources. Company has completed three LEO Express missions (launched 2023, 2025, 2025) per source [1].

### PsiQuantum

- **`location`:** `Palo Alto, CA` → `Palo Alto, California, US`  
  Sources: [company_about](https://psiquantum.com/about) · [wikipedia](https://en.wikipedia.org/wiki/PsiQuantum)
- **`totalRaised`:** `$1.6B+` → `$1.415B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/PsiQuantum)

  **Notes:** March 2025: raised $750M at $6B valuation (source 2). May 2026: signed $100M Letter of Intent with U.S. Department of Commerce (source 0). Facilities include HQ in Palo Alto CA, operations in Milpitas CA, Daresbury UK, Malta NY (GlobalFoundries), Chicago IL (IQMP), Queensland Australia (Moreton Bay Central and Brisbane Test & Validation Lab) (source 1). Australian Commonwealth and Queensland governments invested A$940 million in 2024 (source 2). Total raised calculation: $665M (July 2021) + $750M (March 2025) = $1.415B

### SpaceX

- **`fundingStage`:** `Series G` → `Pre-IPO`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Source [1] Wikipedia states 'SpaceX is not publicly traded but is expected to have an initial public offering (IPO) in 2026.' Source [3] indicates upcoming IPO plans to raise at least $75 billion at valuation exceeding $1.75 trillion, but this is future-oriented and not yet verified as current status. The database entry claims IPO at $1.5T valuation, but source [1] cites $800B valuation from 2025 share offer and source [3] projects $1.75T+ in IPO filing.

### Vast

- **`location`:** `Los Angeles, CA` → `Long Beach, CA`  
  Sources: [company_website](https://www.vastspace.com)

  **Notes:** Haven Demo launched November 2025 on Bandwagon-4 rideshare and was deorbited in February 2026. Haven-1 launch date specified as 2027 on website (not May 2026 as in database entry). Max Haot is CEO; Launcher was acquired by Vast. No specific founding year, total funding amount, valuation, or investor names could be verified from sources.

---

## ✅ Cleared (30 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- AST SpaceMobile
- Asimov
- Astera Labs
- Axiom Space
- Blue Origin
- Crusoe Energy
- Deterrence
- EnerVenue
- HEO
- Humanoid
- ICON
- Mach Industries
- Mara
- Muon Space
- Oxford Quantum Circuits
- Palantir
- Percepto
- Photonic Inc
- Pivotal
- Profluent
- Rebellions
- Rivian
- Solid Power
- Standard Nuclear
- Starcloud
- Substrate
- Waymo
- X-Energy
- Zettascale
- ideaForge


---

*Generated by `scripts/generate_verification_report.py` on 2026-06-05T09:35:23+00:00*