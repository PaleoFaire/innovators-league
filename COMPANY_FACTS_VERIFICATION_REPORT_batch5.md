# Company Facts Verification Report

**Generated:** 2026-04-30T05:58:22+00:00  

**Cohort:** `data/cold_email_batch5.json`  

**Cohort size:** 95 companies  

**New Claude extractions this run:** 73  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 10 | 11% |
| 🔧 Changes proposed | 63 | 66% |
| ❓ Unverifiable | 22 | 23% |

---

## 🔧 Proposed Changes (63 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Zeitview

- **`founder`:** `Daniel Burton, Eli Tamanaha` → `Dan Burton`  
  Sources: [company_about](https://zeitview.com/about)
- **`website`:** `*(empty)*` → `https://zeitview.com`  
  Sources: [company_website](https://zeitview.com) · [company_about](https://zeitview.com/about)

  **Notes:** Source [1] confirms Dan Burton is Founder and CEO. Source [1] mentions the company was previously called DroneBase ('now Zeitview'). Database entry claims 2014 founding year, Eli Tamanaha as co-founder, Series D stage, $174M raised, and 645 employees, but none of these details appear in provided sources and cannot be verified.

### Roam Robotics

- **`website`:** `*(empty)*` → `https://roamrobotics.com`  
  Sources: [company_website](https://roamrobotics.com)

  **Notes:** Source [0] is company website only. Cannot verify founders (Tim Swift, Mallory Ulaszek, Saul Griffith), location (San Francisco, CA), founded year (2012), stage (Series A), total raised ($16.4M), or investors from provided sources. Website contains product information and performance claims but no company history, founding details, or financial information.

### Orbit Fab

- **`website`:** `*(empty)*` → `https://orbitfab.com`  
  Sources: [company_website](https://orbitfab.com) · [company_about](https://orbitfab.com/about)
- **`investors`:** `[]` → `['Lockheed Martin', 'Northrop Grumman']`  
  Sources: [company_about](https://orbitfab.com/about)

  **Notes:** Source [1] states 'Secured Series A Funding' in 2023 timeline. Founder names not explicitly listed as 'founders' or 'co-founders' in provided sources, only leadership team members named. Database entry lists Daniel Faber and Jeremy Schiel as founders but this cannot be verified from provided sources. Total funding of $28.5M from database entry cannot be verified from these sources.

### Transmutex

- **`website`:** `*(empty)*` → `https://transmutex.com`  
  Sources: [company_website](https://transmutex.com)

  **Notes:** Sources do not explicitly identify founders (Servan-Schreiber, Carminati, and Revol are not named as founders in provided sources; Servan-Schreiber is listed as Chairman). No founding year, funding stage, total raised, valuation, or investor details are present in the provided sources. Database entry references cannot be used as source verification.

### Monarch Tractor

- **`founder`:** `Praveen Penmetsa, Zachary Omohundro, Carlo Mondavi` → `Praveen Penmetsa, Mark Schwager, Carlo Mondavi, Zachary Omoh`  
  Sources: [company_about](https://www.monarchtractor.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Monarch_Tractor)
- **`location`:** `Livermore, CA` → `Livermore, California, U.S.`  
  Sources: [company_about](https://www.monarchtractor.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Monarch_Tractor)
- **`totalRaised`:** `$137M` → `$240M+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Monarch_Tractor)
- **`website`:** `*(empty)*` → `https://www.monarchtractor.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Monarch_Tractor)
- **`investors`:** `[]` → `['Astanor Ventures', 'Foxconn Co-GP Fund', 'CNH Industrial',`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Monarch_Tractor)

  **Notes:** Company ceased most or all operations by early 2026 following dealership lawsuits, production shutdown in Ohio, and closure of Livermore headquarters. Wikipedia source indicates the company 'was an American agricultural technology company' (past tense) and documents significant operational challenges and decline starting in 2024.

### MightyFly

- **`founder`:** `Manal Habib, Jaganath Rao` → `Manal Habib`  
  Sources: [company_about](https://mightyfly.com/about)
- **`location`:** `Fremont, CA` → `San Francisco, CA`  
  Sources: [company_about](https://mightyfly.com/about)
- **`founded`:** `2018` → `2019`  
  Sources: [company_about](https://mightyfly.com/about)
- **`totalRaised`:** `$12M` → `$10M`  
  Sources: [company_website](https://mightyfly.com)
- **`website`:** `*(empty)*` → `https://mightyfly.com`  
  Sources: [company_website](https://mightyfly.com) · [company_about](https://mightyfly.com/about)
- **`investors`:** `[]` → `['Draper Associates', 'At One Ventures', '500 Global']`  
  Sources: [company_website](https://mightyfly.com)

  **Notes:** Founded year corrected to October 2019 per source [1] timeline. Only Manal Habib is explicitly named as founder/CEO; other leadership listed are employees. Database entry listed 2018 and $12M; sources verify October 2019 and $10M funding round. No co-founder 'Jaganath Rao' found in provided sources.

### Natilus

- **`location`:** `San Diego, CA` → `San Diego, California`  
  Sources: [company_website](https://natilus.co) · [wikipedia](https://en.wikipedia.org/wiki/Natilus)
- **`website`:** `*(empty)*` → `https://natilus.co`  
  Sources: *(no sources cited)*
- **`investors`:** `[]` → `['Tim Draper', 'Starburst Ventures', 'Seraph Group', 'Gelt V`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Natilus)

  **Notes:** Wikipedia indicates company was founded in April 2016. Sources show aircraft models KONA (cargo) and HORIZON (passenger). Company relocated from San Francisco Bay Area to San Diego in 2021. Recent developments (2025) include orders from Nolinor Aviation and SpiceJet partnership for India market. SEC Form D filing from 2026 suggests recent fundraising activity but amount cannot be verified as total raised without additional context.

### Precision AI

- **`founder`:** `Sreeram Raghavan, Matt Borzilleri` → `Sophia Ren`  
  Sources: [company_about](https://precision-ai.com/about)
- **`founded`:** `2020` → `2022`  
  Sources: [company_about](https://precision-ai.com/about)
- **`website`:** `*(empty)*` → `https://precision-ai.com`  
  Sources: [company_website](https://precision-ai.com) · [company_about](https://precision-ai.com/about)

  **Notes:** CRITICAL: Database entry references autonomous drones for weed spraying, but sources (company website and about page) describe AI platform for precision cancer treatment. This is a completely different company. Sources confirm only Sophia Ren as founder; source states 'Alongside a like-minded partner' but does not name the co-founder explicitly. No location, funding stage, total raised, or valuation information found in sources. The provided database entry appears to describe an entirely different company (agricultural AI drones).

### Material Evolution

- **`founded`:** `*(empty)*` → `2020`  
  Sources: [company_about](https://materialevolution.com/about)
- **`totalRaised`:** `$16M` → `$15M`  
  Sources: [company_about](https://materialevolution.com/about)
- **`website`:** `*(empty)*` → `https://materialevolution.com`  
  Sources: *(no sources cited)*
- **`investors`:** `[]` → `['KOMPAS VC', 'Norrsken VC', 'Playfair Capital', 'At One Ven`  
  Sources: [company_about](https://materialevolution.com/about)

  **Notes:** Series A funding of £15 million (converted to approximately $15M USD equivalent for consistency). First production facility (Mevo A1) commissioned in Wrexham, Wales in October 2024 with 120,000 tonnes annual capacity. Sources mention geopolymer achieves 85% lower embodied carbon than traditional cements.

### Manifold Bio

- **`founder`:** `Gleb Kuznetsov, Pierce Ogden` → `Gleb Kuznetsov, Pierce Ogden, Shane Lofgren, George Church`  
  Sources: [company_website](https://manifoldbio.com)
- **`website`:** `*(empty)*` → `https://manifoldbio.com`  
  Sources: [company_website](https://manifoldbio.com)
- **`investors`:** `[]` → `['Playground Global', 'Triatomic Capital', 'Section 32']`  
  Sources: [company_website](https://manifoldbio.com)

  **Notes:** Source [0] lists four co-founders: Gleb Kuznetsov (Co-Founder & CEO), Pierce Ogden (Co-Founder & CTO), Shane Lofgren (Co-Founder & Head of Portfolio Development and Strategy), and George Church (Co-Founder). Database entry only lists two founders. Founded year, current stage, total raised, and valuation cannot be verified from provided sources. Roche collaboration mentioned in news headline (November 3, 2025) but terms not detailed in source [0].

### Valinor Enterprises

- **`website`:** `*(empty)*` → `https://valinorenterprises.com`  
  Sources: [company_website](https://valinorenterprises.com)

  **Notes:** Source [0] is the company website but contains only a landing page with placeholder text ('Bald geht's los' - German for 'Coming soon') and a cookie notice. No verifiable business information, founders, funding details, or location data could be extracted from the provided source.

### Starfish Space

- **`location`:** `Tukwila, WA` → `Seattle, WA`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starfish_Space)
- **`founded`:** `*(empty)*` → `2019`  
  Sources: [company_about](https://starfishspace.com/company) · [wikipedia](https://en.wikipedia.org/wiki/Starfish_Space)
- **`totalRaised`:** `$200M+` → `$100M+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starfish_Space)
- **`website`:** `*(empty)*` → `https://starfishspace.com`  
  Sources: [company_website](https://starfishspace.com)
- **`investors`:** `[]` → `['Point72 Ventures', 'Activate Capital', 'Shield Capital', '`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Starfish_Space)

  **Notes:** Founded October 2019 by former Blue Origin engineers. Series B raised in April 2026 led by Point72 Ventures. Otter Pup 2 mission launched June 23, 2025. Successfully completed Remora mission in December 2025 demonstrating first fully autonomous rendezvous with lightweight camera system.

### Reliable Robotics

- **`location`:** `Mountain View, CA` → `Dubai, UAE`  
  Sources: [company_about](https://reliablerobotics.ai/about)
- **`founded`:** `*(empty)*` → `2018`  
  Sources: [company_website](https://reliablerobotics.ai) · [company_about](https://reliablerobotics.ai/about)
- **`website`:** `*(empty)*` → `https://reliablerobotics.ai`  
  Sources: [company_website](https://reliablerobotics.ai) · [company_about](https://reliablerobotics.ai/about)

  **Notes:** The sources provided describe a Dubai-based robotics distributor and solutions company founded in 2018, NOT the Reliable Robotics autonomous flight systems company referenced in the database entry. The database entry appears to reference a different company with the same name. No information found in these sources to verify founders (Robert Rose, Juerg Frefel), Mountain View CA location, Series C stage, or $134M funding.

### Koloma

- **`founder`:** `Tom Darrah, Pete Johnson, Paul Harraka` → `Pete Johnson, Tom Darrah`  
  Sources: [company_about](https://koloma.com/about)
- **`website`:** `*(empty)*` → `https://koloma.com`  
  Sources: [company_website](https://koloma.com) · [company_about](https://koloma.com/about)

  **Notes:** Database entry lists Paul Harraka as founder, but he is not identified as founder or co-founder in provided sources; only Pete Johnson (CEO & Founder) and Tom Darrah (CTO & Founder) are explicitly named as founders. Location Denver, CO in database entry cannot be verified from sources provided.

### TS Conductor

- **`founder`:** `Jason Huang, Rulong Chen` → `Jason Huang`  
  Sources: [company_about](https://tsconductor.com/about)
- **`founded`:** `*(empty)*` → `2016`  
  Sources: [company_website](https://tsconductor.com) · [company_about](https://tsconductor.com/about)
- **`website`:** `*(empty)*` → `https://tsconductor.com`  
  Sources: [company_website](https://tsconductor.com) · [company_about](https://tsconductor.com/about)

  **Notes:** Source [1] identifies Jason Huang as 'Co-founder & CEO' but does not name a second co-founder explicitly. The database entry lists 'Rulong Chen' as a co-founder, but this name does not appear in the provided sources. Hervé Touati is described as 'an investor in TS Conductor' and Chief Strategy Officer, not as a founder. Company is described as a 'public benefit corporation' in source [1]. Sources confirm 'thousands of miles installed since 2016' but do not specify exact founding year—2016 appears to be the year of initial deployment/commercialization. No Series B stage, total funding amount, valuation, or specific location beyond website mention is verified in sources.

### VEIR

- **`founder`:** `Tim Heidel, Steve Ashworth` → `Tim Heidel`  
  Sources: [company_about](https://veir.com/about)
- **`location`:** `Woburn, MA` → `Woburn, Massachusetts`  
  Sources: [company_about](https://veir.com/about)
- **`founded`:** `*(empty)*` → `2019`  
  Sources: [company_about](https://veir.com/about)
- **`website`:** `*(empty)*` → `https://veir.com`  
  Sources: [company_website](https://veir.com) · [company_about](https://veir.com/about)
- **`investors`:** `[]` → `["Microsoft's Climate Innovation Fund", 'National Grid Partn`  
  Sources: [company_about](https://veir.com/about)

  **Notes:** Only Tim Heidel is explicitly named as 'CEO & Co-Founder' in source [1]. No co-founder name matching 'Steve Ashworth' from database entry was found in sources. Current stage listed as 'Series B' in database entry could not be verified in provided sources. Total raised of $117M from database could not be verified in provided sources.

### HistoSonics

- **`totalRaised`:** `$250M growth + $2.25B acquisition` → `$250M`  
  Sources: [company_website](https://histosonics.com)
- **`website`:** `*(empty)*` → `https://histosonics.com`  
  Sources: [company_website](https://histosonics.com)

  **Notes:** Sources do not explicitly name founders, founded year, location, current stage, valuation, or investors. The company website references $250M Growth Financing as 'Oversubscribed' but does not mention the August 2025 acquisition by K5 Global, Bezos Expeditions, and Wellington referenced in the database entry. The copyright on the website shows 2019-2025, indicating the company existed by 2019. Histotripsy science was developed at University of Michigan per source [1].

### Precision Neuroscience

- **`founder`:** `Benjamin Rapoport, Michael Mager` → `Benjamin Rapoport, Michael Mager, Demetrios Papageorgiou, Ma`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Precision_Neuroscience)
- **`location`:** `New York, NY` → `New York City, NY`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Precision_Neuroscience)
- **`founded`:** `*(empty)*` → `2021`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Precision_Neuroscience)
- **`website`:** `*(empty)*` → `https://precisionneuro.io`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Precision_Neuroscience)
- **`investors`:** `[]` → `['Steadview Capital', 'Forepont Capital Partners', 'B Capita`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Precision_Neuroscience)

  **Notes:** FDA 510(k) clearance date in database entry states March 30, 2025, but source [0] states April 2025 and March 2025 in different sections; Wikipedia source consistently references March/April 2025 timeframe. Series C funding of $102M completed in December 2024 at $500M post-money valuation, with total funding reaching $180M as of January 2026.

### Frankenburg Technologies

- **`location`:** `Tallinn, Estonia` → `Estonia`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Frankenburg_Technologies)

  **Notes:** Wikipedia source does not name founders or provide funding details. Database entry lists founders (Taavi Madiberk, Marko Virkebau) and funding (€40M Series A) but these cannot be verified from provided Wikipedia source. Wikipedia confirms company signed agreement with PGZ in March 2026 to build anti-drone defence plant in Poland.

### Tytan Technologies

- **`founder`:** `Balazs Nagy, Batuhan Yumurtaci` → `Balazs Nagy`  
  Sources: [company_website](https://tytan-technologies.com)
- **`totalRaised`:** `€46M` → `€30M`  
  Sources: [company_website](https://tytan-technologies.com)
- **`website`:** `*(empty)*` → `https://tytan-technologies.com`  
  Sources: [company_website](https://tytan-technologies.com) · [company_about](https://tytan-technologies.com/about)

  **Notes:** Database entry lists 'Batuhan Yumurtaci' as co-founder, but sources only explicitly name 'Balazs Nagy' as 'CEO and co-founder.' Only Balazs Nagy is verifiable from provided sources. Database entry claims €46M raised; sources mention only €30M funding round. No founded year found in sources. Current stage listed as 'Series A' in database but not verified in sources. News article dated April 21, 2026.

### Aerospacelab

- **`website`:** `*(empty)*` → `https://aerospacelab.com`  
  Sources: [company_website](https://aerospacelab.com)

  **Notes:** Source [0] is company website only. No specific founder names, location, founding year, funding stage, total raised amount, valuation, or investor names could be verified from the provided source. Database entry claims cannot be verified from this source alone.

### The Exploration Company

- **`fundingStage`:** `Series A` → `Series B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/The_Exploration_Company)
- **`totalRaised`:** `€40M` → `$160M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/The_Exploration_Company)
- **`website`:** `*(empty)*` → `https://www.exploration.space`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/The_Exploration_Company)

  **Notes:** Founded July 2021. Most recent funding: $160M Series B in November 2024. Wikipedia source indicates 400 employees as of 2026. Company headquartered in Munich, Bordeaux, and Oberpfaffenhofen with offices in Italy, France, Houston, and MENA region. Sources [0] and [1] are domain sales pages for theexplorationcompany.com and contain no verifiable company information.

### HyImpulse

- **`location`:** `Neuenstadt, Germany` → `Neuenstadt am Kocher, Germany`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/HyImpulse)
- **`totalRaised`:** `€74M` → `€74,000,000`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/HyImpulse)
- **`website`:** `*(empty)*` → `https://www.hyimpulse.de/en/`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/HyImpulse)

  **Notes:** Wikipedia lists 'Total assets' of €74,000,000 (2025), not explicitly 'total raised'. SR75 successfully completed maiden flight on 3 May 2024 from Koonibba Test Range, Australia. No founder names explicitly listed in source. No current funding stage mentioned in source.

### INERATEC

- **`website`:** `*(empty)*` → `https://ineratec.com`  
  Sources: [company_website](https://ineratec.com) · [company_about](https://ineratec.com/about)

  **Notes:** Sources confirm Tim Boeltken as CEO but do not explicitly identify him as founder. Founded year (2016), location (Karlsruhe, Germany), funding stage (Series B), total_raised ($129M), and valuation cannot be verified from provided sources. Frankfurt plant and modular Fischer-Tropsch reactor details from database entry are not found in provided sources.

### Reverion

- **`website`:** `*(empty)*` → `https://reverion.com`  
  Sources: [company_website](https://reverion.com) · [company_about](https://reverion.com/about)

  **Notes:** Sources identify Reverion as a spin-out from TU München (Technical University of Munich). Website mentions 'Das Reverion Team' section but does not explicitly name founders. No financial data (funding, valuation, stage) could be verified from provided sources. Database entry lists founders and financial details that are not present in these sources.

### Isomorphic Labs

- **`location`:** `London, UK` → `London, England`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Isomorphic_Labs)
- **`fundingStage`:** `Series A` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Isomorphic_Labs)
- **`website`:** `*(empty)*` → `https://isomorphiclabs.com`  
  Sources: [company_website](https://isomorphiclabs.com) · [company_about](https://isomorphiclabs.com/about-us) · [wikipedia](https://en.wikipedia.org/wiki/Isomorphic_Labs)
- **`investors`:** `[]` → `['Thrive Capital']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Isomorphic_Labs)

  **Notes:** Company was incorporated on February 24, 2021 and announced on November 4, 2021 as a subsidiary of Alphabet Inc. Raised $600 million in its first external funding round in April 2025, led by Thrive Capital. Demis Hassabis is also founder and CEO of DeepMind. Current stage listed as 'Private' rather than 'Series A' as the $600M funding round in April 2025 was described as the company's 'first ever external funding round', suggesting it was not previously a traditional venture-backed Series A.

### SiPearl

- **`website`:** `*(empty)*` → `https://sipearl.com`  
  Sources: [company_website](https://sipearl.com)

  **Notes:** Source 0 is the company website but contains no information about founders, founding year, funding stage, total raised, valuation, or investors. The database entry lists Philippe Notton as founder, Series A stage, and €130M raised, but these cannot be verified from the provided sources.

### Riverlane

- **`founded`:** `*(empty)*` → `2016`  
  Sources: [company_about](https://riverlane.com/about)
- **`website`:** `*(empty)*` → `https://riverlane.com`  
  Sources: [company_website](https://riverlane.com)

  **Notes:** Steve Brierley is explicitly identified as CEO and Founder in source [1]. Current stage listed as Series C in database entry but no supporting evidence found in sources. Total raised of $120M+ in database entry but no supporting evidence found in sources. Sources mention offices in Cambridge, UK and Boston, US; Cambridge selected as primary location per specification rules.

### Poolside

- **`website`:** `*(empty)*` → `https://poolside.ai`  
  Sources: [company_website](https://poolside.ai)

  **Notes:** Source [0] is company website only—does not provide founder names, location, founding year, funding stage, total raised, or investor information. Database entry references Jason Warner, Eiso Kant as founders, Series B stage, $626M+ raised, and NVIDIA $1B commitment, but these cannot be verified from provided sources.

### Nomagic

- **`website`:** `*(empty)*` → `https://nomagic.com`  
  Sources: [company_website](https://nomagic.com) · [company_about](https://nomagic.com/company)

  **Notes:** The sources provided are from Dassault Systèmes' website and describe No Magic as a system design software company, NOT a robotics/warehouse automation company. This contradicts the database entry which claims it makes 'AI-powered pick-and-place robots for warehouse automation.' No information found in sources to verify founder name, location, founded year, stage, funding, or valuation.

### Nu Quantum

- **`totalRaised`:** `£8.5M+ (equity) + MoD/DSIT contracts` → `$60M`  
  Sources: [company_website](https://nu-quantum.com)
- **`website`:** `*(empty)*` → `https://nu-quantum.com`  
  Sources: [company_website](https://nu-quantum.com) · [company_about](https://nu-quantum.com/about-us)

  **Notes:** Source [0] shows Series A funding of $60M with title 'Nu Quantum Raises $60M Series A in Largest Financing Round for Quantum Computer Networking'. Source [1] confirms founding in 2018 as spinout from University of Cambridge and lists Dr. Carmen Palacios-Berraquero as Founder and CEO. Source [1] indicates offices in Cambridge, UK and Los Angeles, US but primary location is Cambridge.

### Pragmatic Semiconductor

- **`founder`:** `Scott White` → `Richard Price, Scott White`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Pragmatic_Semiconductor)
- **`location`:** `Durham, UK` → `Cambridge, England`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Pragmatic_Semiconductor)
- **`totalRaised`:** `£182M+` → `$231M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Pragmatic_Semiconductor)
- **`website`:** `*(empty)*` → `https://pragmaticsemiconductor.com`  
  Sources: [company_website](https://pragmaticsemiconductor.com)
- **`investors`:** `[]` → `['Arm', 'Cambridge Innovation Capital', 'Avery Dennison', 'B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Pragmatic_Semiconductor)

  **Notes:** David Moore appointed CEO in 2022, replacing co-founder Scott White. Series D funding of $231 million in 2023 was described as 'the largest ever European semiconductor venture funding round.' Manufacturing facility is located in County Durham; headquarters moved to Cambridge Science Park in 2015.

### Oxa

- **`location`:** `Oxford, UK` → `Oxford, England`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Oxa)
- **`totalRaised`:** `$250M+` → `$103M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Oxa)
- **`website`:** `*(empty)*` → `https://oxa.tech`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Oxa)
- **`investors`:** `[]` → `['IP Group', 'Parkwalk Advisors', 'AXA XL', 'NVentures', 'Ho`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Oxa)

  **Notes:** Company rebranded from Oxbotica to Oxa in May 2023. Most recent funding round was Series D in March 2026 for $103 million.

### Epoch Biodesign

- **`founder`:** `Jacob Nathan, Douglas Hamilton` → `Jacob Nathan`  
  Sources: [company_about](https://epochbiodesign.com/about)
- **`totalRaised`:** `$18.3M` → `$40M`  
  Sources: [company_about](https://epochbiodesign.com/about)
- **`website`:** `*(empty)*` → `https://epochbiodesign.com`  
  Sources: [company_website](https://epochbiodesign.com)
- **`investors`:** `[]` → `['Lowercarbon Capital', 'Extantia Capital', 'Mundi Ventures'`  
  Sources: [company_about](https://epochbiodesign.com/about)

  **Notes:** Only Jacob Nathan explicitly named as founder in sources; Douglas Hamilton listed in database entry but not identified as founder in provided sources. Source [1] mentions '$18.3M Series A round' but also states 'closing over $40M in funding' total, so $40M represents total raised across all rounds. Founded year not specified in sources despite database entry claiming 2019.

### MBRYONICS

- **`website`:** `*(empty)*` → `https://mbryonics.com`  
  Sources: [company_website](https://mbryonics.com)

  **Notes:** Sources provided are company website and about page only. No third-party sources available to verify founders, founding year, funding stage, total raised, valuation, or investors. Database entry lists founders (John Mackey, Ruth Mackey, David Mackey), founded year (2013), stage (Series B), and total raised (€17.5M+) but these cannot be verified from provided sources.

### Candela

- **`website`:** `*(empty)*` → `https://candela.com`  
  Sources: [company_website](https://candela.com) · [company_about](https://candela.com/about)

  **Notes:** Wikipedia source [2] is about the SI unit 'candela' (luminous intensity), not the company, and was excluded. Company website confirms P-12 ferry in commercial service in Stockholm. Sources do not provide verifiable information on funding stage, total capital raised, valuation, or named investors.

### KrattWorks

- **`website`:** `*(empty)*` → `https://krattworks.com`  
  Sources: [company_website](https://krattworks.com)

  **Notes:** Source [0] confirms company operates in Estonia with 50+ employees and has a 7-year contract worth €15M with Estonian Defense Forces. No founder names, funding information, valuation, or founding year explicitly stated in provided sources. Database entry claims 'Martin Karmin' as founder and '2018' as founding year, but these are not verified in source [0].

### DefSecIntel

- **`website`:** `*(empty)*` → `https://defsecintel.com`  
  Sources: [company_website](https://defsecintel.com)

  **Notes:** Source [0] is company website with no verifiable information about founders, founding year, funding stage, total raised, valuation, or investors. Database entry claims founder 'Jaanus Tamm', Series A stage, and 'SurveilSPIRE' product name — all present in website content (SurveilSPIRE confirmed as 'Mobile autonomous surveillance platform' in source [0]), but founder name and funding details cannot be verified from provided sources.

### SatRev

- **`website`:** `*(empty)*` → `https://satrev.space`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SatRev)

  **Notes:** Wikipedia source does not specify current funding stage, total raised, or valuation. Database entry mentions Series B stage and 1,500 satellite REC constellation plans, but these are not verified in provided sources. All STORK constellation satellites have decayed from orbit as of May 2024.

### KP Labs

- **`website`:** `*(empty)*` → `https://kplabs.space`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/KP_Labs)

  **Notes:** Sources [0] and [1] appear to describe a different company called 'Keesal Propulsion Labs' (focused on legal/business process automation), not the Polish space company KP Labs. Only source [2] (Wikipedia) provides verified information about the correct KP Labs. Database entry lists founder 'Grzegorz Kasprowicz' but this is not confirmed in provided sources. Database entry lists stage as 'Series A' but this cannot be verified in sources.

### Quandela

- **`website`:** `*(empty)*` → `https://quandela.com`  
  Sources: [company_website](https://quandela.com) · [company_about](https://quandela.com/about)

  **Notes:** Founders not explicitly named as such in provided sources. Location (Massy, France) and stage information from database entry could not be verified in sources. Current stage, total raised, valuation, and investor details not found in sources.

### Unseenlabs

- **`founder`:** `Clément Galic, Jonathan Galic` → `Benjamin Galic, Jonathan Galic, Clément Galic`  
  Sources: [company_about](https://unseenlabs.com/company)
- **`totalRaised`:** `€85M+` → `€112.5M`  
  Sources: [company_about](https://unseenlabs.com/company)
- **`website`:** `*(empty)*` → `https://unseenlabs.com`  
  Sources: [company_website](https://unseenlabs.com) · [company_about](https://unseenlabs.com/company)

  **Notes:** Database entry listed 12+ operational satellites; sources indicate 20 satellites in orbit as of the company page update, with BRO-21 launched as of April 2026. Founders clarified as three brothers (Benjamin, Jonathan, and Clément), not just two. Total raised figure updated from €85M to €112.5M per most recent company statement.

### Cailabs

- **`website`:** `*(empty)*` → `https://cailabs.com`  
  Sources: [company_website](https://cailabs.com) · [company_about](https://cailabs.com/about-us)

  **Notes:** Nicolas Treps is listed as co-founder in the database entry but appears in sources as co-inventor of MPLC technology (2010) rather than explicitly named as a founder at company establishment in 2013. Source [1] states 'In 2013, Cailabs was officially founded, with Guillaume Labroille as Chief Technology Officer and co-founder' and lists Jean-François Morizur as Co-founder & CEO, but Nicolas Treps' formal founder status is not explicitly stated in the provided sources, only his role in inventing the core technology.

### Sateliot

- **`website`:** `*(empty)*` → `https://sateliot.com`  
  Sources: [company_website](https://sateliot.com)

  **Notes:** Database entry claims Series B closed March 2025 with €70M and Series C underway, but these claims cannot be verified in provided sources. CEO Jaume Sanpera is listed in management; Marco Guadalupi listed as CTO and Gianluca Redolfi as CCO, all identified as founders in about section.

### Multiverse Computing

- **`founder`:** `Enrique Lizaso Olmos, Román Orús, Alfonso Rubio-Manzanares, ` → `Enrique Lizaso, Román Orús, Alfonso Rubio-Manzanares, Sam Mu`  
  Sources: [company_about](https://multiversecomputing.com/team) · [wikipedia](https://en.wikipedia.org/wiki/Multiverse_Computing)
- **`website`:** `*(empty)*` → `https://multiversecomputing.com`  
  Sources: [company_website](https://multiversecomputing.com) · [company_about](https://multiversecomputing.com/team) · [wikipedia](https://en.wikipedia.org/wiki/Multiverse_Computing)
- **`investors`:** `[]` → `['Bullhound Capital', 'HP Tech Ventures', 'SETT', 'Forgepoin`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Multiverse_Computing)

  **Notes:** Series B round of $215M closed in June 2025 per Wikipedia source. Company has 480 employees as of 2026. Headquarters in San Sebastián with offices in Madrid, Barcelona, Zaragoza, Paris, Munich, London, Milan, Toronto and San Francisco.

### Nearfield Instruments

- **`founder`:** `Hamed Sadeghian` → `Roland van Vliet, Hamed Sadeghian`  
  Sources: [company_about](https://nearfieldinstruments.com/about)
- **`totalRaised`:** `€135M+` → `$147.6M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Nearfield_Instruments)
- **`website`:** `*(empty)*` → `https://nearfieldinstruments.com`  
  Sources: *(no sources cited)*
- **`investors`:** `[]` → `['Invest-NL', 'Innovation Industries', 'Samsung Venture Inve`  
  Sources: [company_about](https://nearfieldinstruments.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Nearfield_Instruments)

  **Notes:** Founded in January 2016 as spin-off of TNO. Series C funding of $147.6M completed in 2024 (per Wikipedia). Company relocated to Rotterdam in July 2018 (originally founded in Delft). US subsidiary established February 2025.

### LeydenJar Technologies

- **`founder`:** `Christian Rood, Gabriël de Scheemaker` → `Christian Rood, Gabriel de Scheemaker`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/LeydenJar_Technologies)
- **`location`:** `Eindhoven, Netherlands` → `Leiden, Netherlands`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/LeydenJar_Technologies)
- **`totalRaised`:** `€50M+` → `€23M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/LeydenJar_Technologies)
- **`website`:** `*(empty)*` → `https://leyden-jar.com/`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/LeydenJar_Technologies)

  **Notes:** Company headquarters listed as Leiden, Netherlands in Wikipedia, though database entry mentions Eindhoven as location of planned production facility. Wikipedia indicates €23M investment for factory construction (expected completion 2027). No Series B stage information found in source. Database entry lists location as Eindhoven, but Wikipedia clearly states headquarters in Leiden.

### Carbyon

- **`totalRaised`:** `€25M+` → `€22.3M`  
  Sources: [company_about](https://carbyon.com/about)
- **`website`:** `*(empty)*` → `https://carbyon.com`  
  Sources: *(no sources cited)*
- **`investors`:** `[]` → `['Invest-NL', 'Brabant Development Agency', 'Innovation Indu`  
  Sources: [company_about](https://carbyon.com/about)

  **Notes:** Total raised calculated from seed round of €7M (2022) plus Series A round of €15.3M (2024). Company won $1M XPRIZE Carbon Removal Milestone Award in 2022. First outdoor demonstrator planned for 2025.

### Synspective

- **`fundingStage`:** `Series C` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Synspective)
- **`website`:** `*(empty)*` → `https://synspective.com`  
  Sources: [company_website](https://synspective.com) · [company_about](https://synspective.com/about)

  **Notes:** Wikipedia source indicates company is publicly traded (TYO: 290A). Founder name Motoyuki Arai not found in provided sources, so marked as null. Database entry mentions Series C and ~$220M raised, but Wikipedia references only a $44M Series C round in June 2024; insufficient detail to verify total_raised figure without additional sources. First satellite launched 2020 per all sources. Constellation goal of 30 satellites mentioned in company materials.

### Axelspace

- **`website`:** `*(empty)*` → `https://axelspace.com`  
  Sources: [company_website](https://axelspace.com)

  **Notes:** Founded year confirmed as August 8, 2008 from company information. Representative listed as NAKAMURA Yuya, President and CEO. Company is 100% owned by Axelspace Holdings Corporation. Current team approximately 180 professionals. Has developed and operated 11 microsatellites since establishment. Database entry claims Series D stage and Japan MoD contracts signed 2026, but these cannot be verified from provided sources.

### Tonbo Imaging

- **`location`:** `Bengaluru, India` → `Bengaluru, Karnataka, India`  
  Sources: [company_website](https://tonboimaging.com)
- **`website`:** `*(empty)*` → `https://tonboimaging.com`  
  Sources: [company_website](https://tonboimaging.com)

  **Notes:** Company registration shows CIN U74140KA2003PLC033043 and notes it was 'Formerly known as Tonbo Imaging India Private Limited.' Database entry contains information not verifiable from provided sources (founder name, founded year, stage, total raised).

### Dhruva Space

- **`founder`:** `Sanjay Nekkanti` → `Sanjay Srikanth Nekkanti`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Dhruva_Space)
- **`location`:** `Hyderabad, India` → `Hyderabad, Telangana, India`  
  Sources: [company_about](https://dhruvaspace.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Dhruva_Space)
- **`website`:** `*(empty)*` → `https://dhruvaspace.com`  
  Sources: [company_website](https://dhruvaspace.com)
- **`investors`:** `[]` → `['Mumbai Angels Network', 'Indian Angel Network (IAN) Fund',`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Dhruva_Space)

  **Notes:** Wikipedia lists founder as 'Sanjay Srikanth Nekkanti' while company website lists co-founders including Krishna Teja Penamakuru, Abhay Egoor, and Chaitanya Dora Surapureddy as COO, CTO, and CFO respectively, but Wikipedia only names Sanjay Srikanth Nekkanti as founder. Total funding amounts raised in December 2019 (₹5 crore) and October 2021 (₹22 crore) are documented but cumulative total in standard currency format cannot be verified. Company is private but no Series stage information found in sources.

### Netrasemi

- **`founder`:** `N. Jayakumar` → `Jyothis Indirabhai, Deepa Geetha, Sreejith Varma`  
  Sources: [company_about](https://netrasemi.com/about)
- **`website`:** `*(empty)*` → `https://netrasemi.com`  
  Sources: [company_website](https://netrasemi.com) · [company_about](https://netrasemi.com/about)

  **Notes:** Three co-founders identified from company About page (Jyothis Indirabhai as CEO & Co-Founder, Deepa Geetha as COO & Co-Founder, Sreejith Varma as CTO & Co-Founder). Database entry references ₹107 Cr Series A funding, N. Jayakumar as founder, Thiruvananthapuram location, and 2021 founding date, but none of these details appear in provided sources. Location cannot be verified from sources provided.

### Sarla Aviation

- **`totalRaised`:** `$10M` → `$13M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Sarla_Aviation)
- **`website`:** `*(empty)*` → `https://www.sarla-aviation.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Sarla_Aviation)
- **`investors`:** `[]` → `['Accel', 'Nikhil Kamath', 'Binny Bansal']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Sarla_Aviation)

  **Notes:** Founded October 2023. Total raised of $13M from pre-seed, seed, and Series A rounds per Wikipedia. Company named after Sarla Thakral, India's first female pilot. Half-scale demonstrator (SYLLA SYL-X1) began ground testing December 2025. Full-scale Shunya prototype unveiled January 2025.

### Hypersonix Launch Systems

- **`location`:** `Brisbane, Australia` → `Brisbane, Queensland, Australia`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Hypersonix_Launch_Systems)
- **`totalRaised`:** `$46M` → `$46M AUD`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Hypersonix_Launch_Systems)
- **`website`:** `*(empty)*` → `https://hypersonix.com.au`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Hypersonix_Launch_Systems)
- **`investors`:** `[]` → `['High Tor Capital', 'Saab', 'RKKVC', 'National Reconstructi`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Hypersonix_Launch_Systems)

  **Notes:** Founded December 2019. Series A funding raised in 2025. DART AE vehicle developed for DIU HyCAT program and UK MoD HTCDF framework. Technology includes SPARTAN scramjet engine (3D-printed, hydrogen-fuelled) and multiple vehicle platforms (DART AE, VISR, Delta Velos).

### Gilmour Space Technologies

- **`location`:** `Gold Coast, Australia` → `Yatala, Queensland, Australia`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Gilmour_Space_Technologies)
- **`website`:** `*(empty)*` → `https://www.gspace.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Gilmour_Space_Technologies)
- **`investors`:** `[]` → `['Blackbird Ventures', 'Main Sequence Ventures', 'Fine Struc`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Gilmour_Space_Technologies)

  **Notes:** Wikipedia states company was 'founded in 2012' in one location but 'founded in Australia 2013' in the Founding section; using 2013 as the explicit year in the Founding section. Current stage cannot be verified from sources. Total raised amount in AUD cannot be verified from provided sources.

### Silicon Quantum Computing

- **`totalRaised`:** `A$50.4M` → `A$83M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Silicon_Quantum_Computing)
- **`website`:** `*(empty)*` → `https://sqc.com.au`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Silicon_Quantum_Computing)
- **`investors`:** `[]` → `['Australian Federal Government', 'New South Wales Governmen`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Silicon_Quantum_Computing)

  **Notes:** Wikipedia source lists A$83M raised at incorporation from government, state government, UNSW, Telstra, and CBA. Database entry references A$50.4M Series A which is not mentioned in provided source. Database entry also references DARPA Stage B contract November 2025 which is not mentioned in provided source. Current stage cannot be verified from provided source.

### Greenroom Robotics

- **`website`:** `*(empty)*` → `https://greenroomrobotics.com`  
  Sources: [company_website](https://greenroomrobotics.com)

  **Notes:** Sources mention founders 'first met at Australian Maritime College' and company is 'Australian owned and Veteran operated' but do not explicitly name specific founders by full name. Founded year not stated in sources despite database entry showing 2019. No funding information, valuation, investors, or current stage disclosed in provided sources. Bureau Veritas granted Approval in Principle to GAMA software (Feb 2026). Lookout+ completed trial in Arnhem Marine Park (Feb 2026).

### Cortical Labs

- **`totalRaised`:** `$11M` → `$11.62M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Cortical_Labs)
- **`website`:** `*(empty)*` → `https://corticallabs.com`  
  Sources: [company_website](https://corticallabs.com) · [company_about](https://corticallabs.com/company) · [wikipedia](https://en.wikipedia.org/wiki/Cortical_Labs)
- **`investors`:** `[]` → `['Blackbird Ventures', 'January Capital', 'Horizons Ventures`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Cortical_Labs)

  **Notes:** Database entry lists 'Andy Kitchen' as founder but Wikipedia identifies him as 'Co-founder Andy Kitchen' and lists both Hon Weng Chong and Andy Kitchen as founders. Total raised calculation: June 2019 seed round of US$1.62M + April 2023 Series A round of US$10M = US$11.62M. Current stage inferred as 'Series A' based on April 2023 funding round description as 'Series A' funding in database entry, but not explicitly stated in sources.

### Qedma

- **`website`:** `*(empty)*` → `https://qedma.com`  
  Sources: [company_website](https://qedma.com)
- **`investors`:** `[]` → `['Glilot+', 'IBM', 'Korea Investment Partners']`  
  Sources: [company_website](https://qedma.com)

  **Notes:** Wikipedia source [2] is about Kedma (a youth village in Israel), not the company Qedma, and is not used for verification. Founded year not explicitly stated in sources despite database entry claiming 2020. CSO is Prof. Dorit Aharonov; CTO is Prof. Netanel Lindner.

### Majestic Labs

- **`founder`:** `Ofer Shacham, Sha Rabii, Masumi Reynders` → `Craig Cheney`  
  Sources: [company_about](https://majesticlabs.com/about)
- **`location`:** `Tel Aviv, Israel` → `Somerville, MA, USA`  
  Sources: [company_website](https://majesticlabs.com)
- **`website`:** `*(empty)*` → `https://majesticlabs.com`  
  Sources: [company_website](https://majesticlabs.com)

  **Notes:** The sources provided describe a robotics/engineering consulting firm based in Somerville, MA. This appears to be a different company than the database entry describes (which references AI server architecture, founders Ofer Shacham/Sha Rabii/Masumi Reynders, Tel Aviv location, and Series A funding). The provided sources contain no information about AI accelerators, memory interfaces, $100M+ funding, or the founders listed in the database entry.

### H2Pro

- **`founder`:** `Talia Gomez Atzmon, Hen Dotan, Avner Rothschild, Gideon Grad` → `Gideon Grader, Avner Rothschild, Hen Dotan, Talmon Marco`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/H2Pro)
- **`location`:** `Caesarea, Israel` → `Israel`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/H2Pro)
- **`website`:** `*(empty)*` → `https://www.h2pro.co`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/H2Pro)
- **`investors`:** `[]` → `['Bill Gates', 'Li Ka-shing', 'Hyundai', 'ArcelorMittal']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/H2Pro)

  **Notes:** Wikipedia source does not specify funding stage (Series B) or total amount raised ($100M+). Leadership structure updated as of 2025: Talmon Marco transitioned from Chairman & CEO to Chairman; Tzahi Rodrig became CEO. Database entry lists 'Talia Gomez Atzmon' as founder, but Wikipedia lists 'Talmon Marco' instead—this discrepancy cannot be resolved from provided sources.

### Addionics

- **`website`:** `*(empty)*` → `https://addionics.com`  
  Sources: [company_website](https://addionics.com) · [company_about](https://addionics.com/about)

  **Notes:** Source [0] and [1] are company-controlled sources only. No third-party verification sources provided. Database entry claims founders (Moshiel Biton, Farid Tariq), location (Tel Aviv, Israel), founded year (2017), stage (Series B), and total_raised ($39M+) cannot be verified from provided sources. Founder names, location, founding year, funding stage, and amounts require independent third-party sources.

---

## ❓ Unverifiable (22 companies)

Couldn't fetch authoritative sources. Per Stephen's rule, we leave these as-is rather than guess. May want to flag for manual research or removal from DB.

- **Dendra Systems** — *no public sources accessible*
- **Ambient Photonics** — *no public sources accessible*
- **Strand Therapeutics** — *no public sources accessible*
- **Lila Sciences** — *no public sources accessible*
- **44.01** — *no public sources accessible*
- **SpliceBio** — *no public sources accessible*
- **eleQtron** — *no public sources accessible*
- **Mission Zero Technologies** — *no public sources accessible*
- **C12 Quantum Electronics** — *no public sources accessible*
- **Jimmy Energy** — *no public sources accessible*
- **AAVantgarde Bio** — *no public sources accessible*
- **Nara Space Technology** — *no public sources accessible*
- **Digantara** — *no public sources accessible*
- **Sagar Defence Engineering** — *no public sources accessible*
- **Newspace Research** — *no public sources accessible*
- **GalaxEye** — *no public sources accessible*
- **Mindgrove Technologies** — *no public sources accessible*
- **Lohum Cleantech** — *no public sources accessible*
- **The ePlane Company** — *no public sources accessible*
- **SwarmFarm Robotics** — *no public sources accessible*
- **Sicona Battery Technologies** — *no public sources accessible*
- **Heven AeroTech** — *no public sources accessible*

---

## ✅ Cleared (10 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Helios
- Blackshark.ai
- Basecamp Research
- ReOrbit
- Fire Point
- Beyond Aero
- Pale Blue
- FuriosaAI
- SatSure
- SpectralX


---

*Generated by `scripts/generate_verification_report.py` on 2026-04-30T05:58:22+00:00*