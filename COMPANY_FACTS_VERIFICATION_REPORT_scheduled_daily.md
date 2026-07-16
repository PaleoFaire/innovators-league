# Company Facts Verification Report

**Generated:** 2026-07-16T07:56:38+00:00  

**Cohort:** `data/cohort_companies_daily.json`  

**Cohort size:** 25 companies  

**New Claude extractions this run:** 25  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 15 | 60% |
| 🔧 Changes proposed | 10 | 40% |
| ❓ Unverifiable | 0 | 0% |

---

## 🔧 Proposed Changes (10 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Humanoid

- **`location`:** `London, UK` → `London, United Kingdom`  
  Sources: [company_website](https://thehumanoid.ai)

  **Notes:** Founded year not explicitly stated in sources despite database entry claiming 2024. Total raised and investor information from database entry ($50M founder-led capital) could not be verified from provided sources. Current stage cannot be verified. Website lists offices in London (HQ), Cambridge MA, and Burnaby BC.

### ICON

- **`founder`:** `Jason Ballard, Evan Loomis, Alexander Le Roux` → `Kennan Frost`  
  Sources: [company_website](https://icon.com)

  **Notes:** The sources provided describe a company called 'Icon' that is 'The Human Admaker' - a UGC (User Generated Content) advertising service founded by Kennan Frost, not the 3D-printed homes company referenced in the database entry. The database entry appears to refer to a different company (ICON, the construction/3D printing firm). Source [2] is a Wikipedia disambiguation page listing multiple entities named 'Icon' including 'ICON, a 3D concrete printing technology company' but provides no details. Source [3] is about a European humanoid robot startup and is not relevant to either Icon company. The sources do not contain information supporting the database entry's claims about 3D-printed homes, DoD/NASA contracts, or the stated founders (Jason Ballard, Evan Loomis, Alexander Le Roux).

### Icarus

- **`founder`:** `Henry Kwan (CEO, fmr Orbital — built spacecraft + space robo` → `Henry Kwan`  
  Sources: [company_about](https://www.icarus.one/about)
- **`investors`:** `[]` → `['Paul Graham']`  
  Sources: [company_about](https://www.icarus.one/about)

  **Notes:** Wikipedia source [2] is about Greek mythology and is not relevant to this company. News sources [3] and [4] refer to 'Icarus Robotics,' a different company based in New York developing space robots, not the stratospheric aircraft company. Only sources [0] and [1] are verified as the company website and about page. Current funding stage (Seed or otherwise) cannot be verified from provided sources. Y Combinator Fall 2025 acceptance mentioned in database entry but not found in provided sources.

### Monumental

- **`fundingStage`:** `Series A` → `Series B`  
  Sources: [news (Tech.eu)](https://tech.eu/2026/07/15/monumental-secures-32m-series-b-to-accelerate-construction-automation/)
- **`totalRaised`:** `$25M` → `$32M`  
  Sources: [news (Sifted)](https://sifted.eu/articles/monumental-robots-fundraise-raises-32m-backed-by-khosla-ventures/) · [news (Tech.eu)](https://tech.eu/2026/07/15/monumental-secures-32m-series-b-to-accelerate-construction-automation/)
- **`investors`:** `[]` → `['Khosla Ventures']`  
  Sources: [news (Sifted)](https://sifted.eu/articles/monumental-robots-fundraise-raises-32m-backed-by-khosla-ventures/) · [news (Tech.eu)](https://tech.eu/2026/07/15/monumental-secures-32m-series-b-to-accelerate-construction-automation/)

  **Notes:** Database entry lists Series A with $25M raised, but sources indicate Series B with $32M raised led by Khosla Ventures. Founder names (Salar al Khafaji, Sebastiaan Visser) appear in database but are not explicitly mentioned as founders in provided sources, so excluded. Website not verified in sources. Founded year (2021) not found in provided sources.

### Neko Health

- **`fundingStage`:** `Series B` → `Series C`  
  Sources: [news (TechCrunch)](https://techcrunch.com/2026/07/15/daniel-eks-body-scanning-startup-neko-health-raises-another-700m/) · [news (Tech.eu)](https://tech.eu/2026/07/15/neko-health-raises-700m-as-demand-grows-for-preventive-health-scans/)
- **`totalRaised`:** `$326M+` → `$700M`  
  Sources: [news (TechCrunch)](https://techcrunch.com/2026/07/15/daniel-eks-body-scanning-startup-neko-health-raises-another-700m/) · [news (Tech.eu)](https://tech.eu/2026/07/15/neko-health-raises-700m-as-demand-grows-for-preventive-health-scans/)
- **`investors`:** `[]` → `['Lightspeed Venture Partners', 'O.G. Venture Partners']`  
  Sources: [news (TechCrunch)](https://techcrunch.com/2026/07/15/daniel-eks-body-scanning-startup-neko-health-raises-another-700m/) · [news (Tech.eu)](https://tech.eu/2026/07/15/neko-health-raises-700m-as-demand-grows-for-preventive-health-scans/)

  **Notes:** Database entry listed Series B stage; sources [1] and [2] from 2026 indicate Series C funding round of $700M led by Lightspeed Venture Partners. Previous valuation of $1.8B and total raised of $326M+ cannot be verified from provided sources.

### Path Robotics

- **`location`:** `Columbus, OH` → `Columbus, OH, USA`  
  Sources: [company_about](https://path-robotics.com/about)
- **`investors`:** `[]` → `['Drive Capital', 'Matter Venture Partners']`  
  Sources: [company_about](https://path-robotics.com/about)

  **Notes:** Sources explicitly name Andy Lonsberry as Co-Founder and CEO and Alex Lonsberry as Co-Founder and CTO. Founded year could not be verified from these sources despite database entry stating 2014. Current funding stage, total raised amount ($271M in database vs $300M+ claim), and valuation could not be verified from provided sources. Sources mention Navy shipyard contracts and partnerships with Saronic and LAD.

### PsiQuantum

- **`totalRaised`:** `$1.415B` → `$1B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/PsiQuantum)

  **Notes:** Series E funding of $1 billion announced in 2025 per Wikipedia source. Specific investor names and valuation could not be verified from provided sources. Wikipedia lists 500+ employees as of 2026.

### Quaise Energy

- **`founder`:** `Carlos Araque, Matt Houde` → `Carlos Araque, Matthew Houde`  
  Sources: [company_about](https://www.quaise.com/company)
- **`totalRaised`:** `$75M+` → `$134M`  
  Sources: [news (Canary Media)](https://www.canarymedia.com/articles/geothermal/quaise-energy-raises-134m) · [sec_form_d](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001813993&type=D&dateb=&owner=include&count=10)

  **Notes:** Sources do not explicitly state founding year despite database entry claiming 2018. Leadership page (source 1) confirms Carlos Araque as 'President, CEO, and a co-founder' and Matthew Houde as 'Chief of Staff and a co-founder.' Current stage and valuation not found in sources. Investor names not explicitly listed in provided sources.

### Reflect Orbital

- **`location`:** `Hawthorne, CA` → `Hawthorne, California, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Reflect_Orbital)

  **Notes:** Wikipedia states founding date as January 2021, but also mentions October 2021 in History section—sources show January 2021 as primary founding date. First satellite Eärendil-1 scheduled for mid-2026 launch. FCC granted license for first satellite on July 9, 2026 per Wikipedia. Total funding as of 2026 update: $35.2M (includes $6.5M seed round September 2024, $20M Series A May 2025, and $1.25M SBIR contract June 2025).

### SpaceX

- **`fundingStage`:** `IPO` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Wikipedia source indicates IPO occurred on June 12, 2026, raising $86B. Elon Musk owns 42% of outstanding shares and controls 85% of voting power (source notes 82% in one place, 85% in another—using 85% as stated in main text). Company has three operating divisions: Space, Connectivity (Starlink), and Artificial Intelligence (Grok, X, data centers). No valuation figure found in sources; database entry claims $1.5T IPO valuation but this is not supported by provided sources.

---

## ✅ Cleared (15 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- 1X Technologies
- Agility Robotics
- Apptronik
- Asimov
- Astera Labs
- Axiom Space
- Crusoe Energy
- Deterrence
- Durin
- Helsing
- Pivotal
- Profluent
- Vast
- Waymo
- Xtend


---

*Generated by `scripts/generate_verification_report.py` on 2026-07-16T07:56:38+00:00*