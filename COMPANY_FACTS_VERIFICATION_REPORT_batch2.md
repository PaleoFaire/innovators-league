# Company Facts Verification Report

**Generated:** 2026-04-30T02:10:52+00:00  

**Cohort:** `data/cold_email_batch2.json`  

**Cohort size:** 100 companies  

**New Claude extractions this run:** 94  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 22 | 22% |
| 🔧 Changes proposed | 72 | 72% |
| ❓ Unverifiable | 6 | 6% |

---

## 🔧 Proposed Changes (72 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Percepto

- **`founder`:** `Dor Abuhasira` → `Dor Abuhasira, Ariel Avitan, Sagi Blonder, Raviv Raz`  
  Sources: [company_about](https://percepto.co/about)
- **`website`:** `*(empty)*` → `https://percepto.co`  
  Sources: [company_website](https://percepto.co)

  **Notes:** Four co-founders identified: Dor Abuhasira (CEO & Co-founder), Ariel Avitan (Chief Commercial Officer & Co-founder), Sagi Blonder (Chief Technology Officer & Co-founder), and Raviv Raz (Chief Policy & Safety Officer & Co-founder). Company has teams based in US and Israel per source [1]. Database entry listed location as Modi'in, Israel but this is not verified in provided sources. Total raised ($128M) and Series C stage from database entry could not be verified from these sources.

### OpenAI

- **`founder`:** `Sam Altman, Greg Brockman, Ilya Sutskever` → `Sam Altman, Elon Musk, Ilya Sutskever, Greg Brockman, Trevor`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/OpenAI)
- **`location`:** `San Francisco, CA` → `San Francisco, California, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/OpenAI)
- **`fundingStage`:** `Seed` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/OpenAI)
- **`website`:** `*(empty)*` → `https://openai.com`  
  Sources: [company_website](https://openai.com)
- **`investors`:** `[]` → `['Microsoft', 'Reid Hoffman', 'Jessica Livingston', 'Peter T`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/OpenAI)

  **Notes:** OpenAI was founded as a nonprofit in December 2015 and transitioned to a capped for-profit structure in 2019. In 2025, it was restructured into a for-profit public benefit corporation (PBC) with 26% ownership by the nonprofit foundation, 27% by Microsoft, and 47% by employees and investors. October 2025 share sale valued company at $500 billion.

### Anthropic

- **`founder`:** `Dario Amodei, Daniela Amodei` → `Dario Amodei, Daniela Amodei, Jared Kaplan, Jack Clark, Chri`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Anthropic)
- **`location`:** `San Francisco, CA` → `San Francisco, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Anthropic)
- **`website`:** `*(empty)*` → `https://anthropic.com`  
  Sources: [company_website](https://anthropic.com) · [company_about](https://anthropic.com/company) · [wikipedia](https://en.wikipedia.org/wiki/Anthropic)

  **Notes:** Wikipedia lists 8 founders (including Jared Kaplan, Jack Clark, Chris Olah, Ben Mann, Sam McCandlish, Tom Brown) in addition to Dario and Daniela Amodei. The database entry lists only 2 founders; Wikipedia source is more comprehensive. Valuation as of February 2026 is $380B per Wikipedia, not $183B as in database entry. Current stage cannot be verified from sources (Wikipedia only states 'Privately held'). Total raised amount cannot be verified precisely; SEC Form D shows a filing but partial/incomplete information.

### SpaceX

- **`location`:** `Starbase, TX` → `Starbase, Texas`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)
- **`website`:** `*(empty)*` → `https://spacex.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SpaceX)

  **Notes:** Wikipedia source indicates SpaceX is expected to have an IPO in 2026 but current stage cannot be verified as 'Series G' or any other series designation from provided sources. Database entry claims '$10B+' total raised and 'Series G' stage, but these cannot be verified from the provided sources. Form D filing [4] shows a minor fundraising event in April 2026 but does not represent total capital raised.

### Fervo Energy

- **`location`:** `Houston, TX` → `Houston, Texas, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fervo_Energy)
- **`fundingStage`:** `Series C` → `Pre-IPO`  
  Sources: [company_website](https://fervoenergy.com)
- **`totalRaised`:** `$430M+` → `$1.5B+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fervo_Energy)
- **`website`:** `*(empty)*` → `https://fervoenergy.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fervo_Energy)
- **`investors`:** `[]` → `['B Capital', 'Breakthrough Energy', 'Centaurus Capital', 'C`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fervo_Energy)

  **Notes:** Company filed registration statement for proposed IPO as of April 17, 2026 per website newsroom. Wikipedia indicates most recent Series E funding of $462 million in November 2025. Database entry lists 'Series C' stage but sources indicate more recent Series E funding and IPO filing.

### Cover

- **`website`:** `*(empty)*` → `https://cover.com`  
  Sources: [company_website](https://cover.com)

  **Notes:** Source [0] is an insurance quote comparison website (cover.com), NOT a modular construction company. The database entry appears to reference a different company entirely. No information about modular construction, Alexis Rivas, Gardena CA, Series B funding, or Pacific Palisades fires rebuild is present in the provided source. Source mismatch indicates potential data corruption or wrong company URL.

### Parallel Systems

- **`location`:** `Culver City, CA` → `Los Angeles, CA`  
  Sources: [company_website](https://parallelsystems.com)
- **`website`:** `*(empty)*` → `https://parallelsystems.com`  
  Sources: [company_website](https://parallelsystems.com)

  **Notes:** Founders (Matt Soule, John Howard, Ben Stabler) and founding year (2020) listed in database entry but NOT verified in provided sources. Series B stage and $100M total raised from database also NOT verified in sources. Website lists address as 'Los Angeles, CA' rather than 'Culver City, CA' from database.

### Databricks

- **`location`:** `San Francisco, CA` → `San Francisco, California`  
  Sources: [company_about](https://databricks.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Databricks)
- **`website`:** `*(empty)*` → `https://databricks.com`  
  Sources: [company_website](https://databricks.com) · [company_about](https://databricks.com/about)

  **Notes:** Series L funding round completed in December 2025 at $134B valuation per Wikipedia. Company is private. Over 60% of Fortune 500 uses Databricks per source [0]. 9,000 employees as of 2025 per source [2].

### Pipedream

- **`location`:** `Austin, TX` → `San Francisco, CA`  
  Sources: [company_website](https://pipedream.com)
- **`fundingStage`:** `Series A` → `Acquired`  
  Sources: [company_website](https://pipedream.com)
- **`website`:** `*(empty)*` → `https://pipedream.com`  
  Sources: [company_website](https://pipedream.com)

  **Notes:** Database entry appears to reference a different company (underground hyperlogistics). Source [0] shows Pipedream is an API automation/workflow platform that has been acquired by Workday (stated as 'Pipedream has joined Workday' multiple times on homepage). No information in sources supports the database entry's description of underground pipe delivery, founders Garrett McCurrach/Canon Reeves, Austin TX location, 2021 founding, Series A stage, or $22.4M funding.

### Earth AI

- **`totalRaised`:** `$29M` → `$20M`  
  Sources: [company_about](https://earth-ai.com/about)
- **`website`:** `*(empty)*` → `https://earth-ai.com`  
  Sources: [company_website](https://earth-ai.com)

  **Notes:** Source [1] references a January 27, 2025 announcement that 'Earth AI Closes Oversubscribed Round; Raising $20M for AI Driven Mineral Exploration' via PR Newswire. Database entry listed $29M total_raised, but most recent verified funding round is $20M. Founder name 'Roman Teslyuk' from database entry could not be verified in provided sources. Founded year 2017 could not be verified in provided sources.

### Standard Nuclear

- **`website`:** `*(empty)*` → `https://standardnuclear.com`  
  Sources: [company_website](https://standardnuclear.com)

  **Notes:** Source [0] and [1] confirm company focuses on advanced nuclear fuel (TRISO) production, not reactor development as stated in database entry. Source [2] is about Zap Energy, not Standard Nuclear, and provides no verifiable information about Standard Nuclear. Database claims about Series A funding ($140M led by Decisive Point in Jan 2026), total raised ($182M), and founding year (2024) cannot be verified from provided sources.

### The Boring Company

- **`location`:** `Bastrop, TX` → `Bastrop, Texas, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/The_Boring_Company)
- **`website`:** `*(empty)*` → `https://theboringcompany.com`  
  Sources: [company_website](https://theboringcompany.com)
- **`investors`:** `[]` → `['Vy Capital', 'Sequoia Capital', 'Valor Equity Partners', '`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/The_Boring_Company)

  **Notes:** Founded January 11, 2017 as a SpaceX subsidiary; spun off as separate corporation in early 2018. Series C funding round announced April 20, 2022. Headquarters moved to Bastrop, Texas sometime before April 2023.

### Galvanick

- **`website`:** `*(empty)*` → `https://galvanick.com`  
  Sources: [company_website](https://galvanick.com)

  **Notes:** Sources [2] and [3] are about Anthropic and AI cybersecurity, not Galvanick—not used for verification. Database entry claims for location (Los Angeles, CA), founded year (2021), stage (SPAC), and total_raised ($20M+) could not be verified from provided sources.

### Deterrence

- **`founder`:** `Dhruva Rajendra, Brian Jones, Henry Olgers` → `Dhruva Rajendra, Henry Olgers`  
  Sources: [company_about](https://deterrence.com/about)
- **`website`:** `*(empty)*` → `https://deterrence.com`  
  Sources: [company_website](https://deterrence.com) · [company_about](https://deterrence.com/about)

  **Notes:** A third person 'Brian Jones' is listed as a founder in the database entry but is not explicitly named as a founder/co-founder in the provided sources. Only Dhruva Rajendra and Henry Olgers are explicitly identified as co-founders in source [1]. Location (Fremont, CA), founded year (2023), stage (Seed), and total_raised ($10M+) from database entry could not be verified in provided sources. Source [2] is about French defense doctrine and is not relevant to this company.

### Durin

- **`website`:** `*(empty)*` → `https://durin.com`  
  Sources: [company_website](https://durin.com)
- **`investors`:** `[]` → `['Founders Factory', 'Rio Tinto']`  
  Sources: [company_website](https://durin.com)

  **Notes:** Source [1] is Wikipedia article about Tolkien's fictional dwarves and is not relevant to the company. Founded year not specified in source [0] despite database entry showing 2024. Location (El Segundo, CA) not mentioned in provided sources. Current stage not explicitly stated in sources. Co-founder Rithvik Gujjula mentioned in media section but not explicitly identified as founder/co-founder in founding context.

### Zap Energy

- **`founder`:** `Benj Conway, Uri Shumlak, Brian Nelson` → `Benj Conway, Brian A. Nelson, Uri Shumlak`  
  Sources: [company_about](https://zapenergy.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Zap_Energy)
- **`location`:** `Everett, WA` → `Seattle, Washington, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Zap_Energy)
- **`website`:** `*(empty)*` → `https://zapenergy.com`  
  Sources: [company_website](https://zapenergy.com) · [company_about](https://zapenergy.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Zap_Energy)
- **`investors`:** `[]` → `['Addition', 'Energy Impact Partners', 'Chevron Technology V`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Zap_Energy)

  **Notes:** Wikipedia indicates headquarters in Seattle, Washington with research facilities in Everett and Mukilteo. Series D funding of $130M announced in October 2024. Company was valued at over $1B and selected as World Economic Forum Technology Unicorn in June 2023. Source [3] indicates company announced pivot to include nuclear fission development alongside fusion work.

### Anduril Industries

- **`location`:** `Costa Mesa, CA` → `Costa Mesa, California, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Anduril_Industries)
- **`website`:** `*(empty)*` → `https://anduril.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Anduril_Industries)
- **`investors`:** `[]` → `['Founders Fund', 'Andreessen Horowitz', 'General Catalyst',`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Anduril_Industries)

  **Notes:** Founded April 20, 2017. Wikipedia source indicates Series D funding of $450M in June 2021 with valuation of $4.6B at that time, but no current stage or total_raised could be verified from provided sources. Current stage and total_raised fields cannot be verified from these sources.

### Rocket Lab

- **`location`:** `Long Beach, CA` → `Long Beach, California, USA`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Rocket_Lab)
- **`website`:** `*(empty)*` → `https://www.rocketlabcorp.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Rocket_Lab)
- **`investors`:** `[]` → `['Khosla Ventures', 'Bessemer Venture Partners', 'Lockheed M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Rocket_Lab)

  **Notes:** Company was originally founded in Auckland, New Zealand in June 2006, moved to Huntington Beach, California in 2013, then to Long Beach in 2020. Went public via SPAC merger in August 2021. Wikipedia states 'over 75 missions as of January 2026' and describes it as 'most prolific small-lift launch vehicle in operation globally.' Current database entry claims '18 successful Electron launches in 2025' and '$37B valuation/market cap' but these specific figures could not be verified in provided sources.

### Matic Robotics

- **`website`:** `*(empty)*` → `https://maticrobotics.com`  
  Sources: [company_website](https://maticrobotics.com)

  **Notes:** Sources confirm the company exists and describe product features (mopping, vacuuming, visual perception, 3D mapping, obstacle avoidance). Sources mention 'two busy fathers' as founders but do not provide their specific names. Database entry lists founder names (Navneet Dalal, Mehul Nariyawala), location (Mountain View, CA), founding year (2017), stage (Seed), and total raised ($107M), but these cannot be verified from the provided public sources.

### Rivian

- **`founder`:** `RJ Scaringe` → `R. J. Scaringe`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Rivian)
- **`location`:** `Irvine, CA` → `Irvine, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Rivian)
- **`totalRaised`:** `$10.5B` → `$13.5B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Rivian)
- **`website`:** `*(empty)*` → `https://rivian.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Rivian)
- **`investors`:** `[]` → `['Amazon', 'Abdul Latif Jameel', 'Volkswagen Group', 'Ford M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Rivian)

  **Notes:** Company originally founded as Mainstream Motors in Rockledge, Florida in 2009, renamed to Avera Automotive, then Rivian Automotive in 2011. IPO occurred on November 10, 2021, on Nasdaq under ticker RIVN. Current major shareholders include Amazon (18.1%), Volkswagen Group (16%), and Abdul Latif Jameel (12.7%).

### Vannevar Labs

- **`founder`:** `Brett Granberg, Nini Hamrick` → `Brett Granberg, Nini Moorhead`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Vannevar_Labs)
- **`location`:** `Palo Alto, CA` → `Palo Alto, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Vannevar_Labs)
- **`totalRaised`:** `$91M` → `$90M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Vannevar_Labs)
- **`website`:** `*(empty)*` → `https://vannevarlabs.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Vannevar_Labs)

  **Notes:** Database entry lists founder as 'Nini Hamrick' but Wikipedia source identifies her as 'Nini Moorhead'. The $90M figure is from January 2023; a November 2024 Pentagon contract was worth up to $99M but this is a contract value, not total funding raised. No current funding stage could be verified from source.

### Overland AI

- **`website`:** `*(empty)*` → `https://overlandai.com`  
  Sources: [company_website](https://overlandai.com)

  **Notes:** Sources do not contain founder names, founding year, funding stage, total raised, or investor information. Database entry lists founders (Byron Boots, Greg Okopal, Stephanie Bonk) and funding ($40M+, Series A, 2022) but these cannot be verified from provided sources.

### Mariana Minerals

- **`website`:** `*(empty)*` → `https://marianaminerals.com`  
  Sources: [company_website](https://marianaminerals.com)

  **Notes:** Founded year (2024), Series A stage, and $85M raised from database entry could not be verified in provided sources. Turner Caldwell is listed as CEO in source [1]; only included as founder where explicitly stated. TechCrunch source [2] mentions 'Earth AI' not 'Mariana Minerals' and appears to reference a different company or acquisition context.

### Waymo

- **`founder`:** `Sebastian Thrun, Chris Urmson, Anthony Levandowski` → `Sebastian Thrun, Anthony Levandowski`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Waymo)
- **`location`:** `Mountain View, CA` → `Mountain View, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Waymo)
- **`founded`:** `*(empty)*` → `2016`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Waymo)
- **`website`:** `*(empty)*` → `https://waymo.com`  
  Sources: [company_website](https://waymo.com) · [company_about](https://waymo.com/about)

  **Notes:** Wikipedia lists founding dates as 2004 (Stanford Self-Driving Car Team), January 17, 2009 (Google Self-Driving Car Project), and December 13, 2016 (as Waymo). The 2016 date is used as this represents Waymo's establishment as an independent company. Chris Urmson is mentioned in Wikipedia as having driven a licensed vehicle but is not explicitly listed as a founder. Database entry lists three founders; Wikipedia only confirms Thrun and Levandowski as founders. In February 2026, Waymo raised $16 billion at a $126 billion valuation per Wikipedia.

### Extropic

- **`website`:** `*(empty)*` → `https://extropic.com`  
  Sources: [company_website](https://extropic.com)

  **Notes:** Source [1] is about Extropianism (a philosophy), not the company Extropic. No founder names, location, founding year, funding stage, total raised, valuation, or investor information could be verified from the provided sources. The database entry references cannot be used as source material per instructions.

### Copenhagen Atomics

- **`founder`:** `Thomas Jam Pedersen` → `Thomas Jam Pedersen, Peter Szabo, Thomas Steenberg, Aslak St`  
  Sources: [company_about](https://copenhagenatomics.com/about)
- **`website`:** `*(empty)*` → `https://copenhagenatomics.com`  
  Sources: [company_website](https://copenhagenatomics.com)

  **Notes:** Founded August 25, 2014 per Wikipedia. Company plans first nuclear chain-reaction test at Paul Scherrer Institute in 2028 (per source 0). Wikipedia notes critical experiment planned for 2026-27 at PSI, which differs from 2028 date on company website. No funding stage or total raised amount found in provided sources.

### QuantWare

- **`founder`:** `Matthijs Rijlaarsdam` → `Matthijs Rijlaarsdam, Alessandro Bruno`  
  Sources: [company_about](https://quantware.com/about)
- **`founded`:** `2020` → `2021`  
  Sources: [company_about](https://quantware.com/about)
- **`website`:** `*(empty)*` → `https://quantware.com`  
  Sources: [company_website](https://quantware.com)

  **Notes:** Database entry states founded 2020, but source [1] explicitly states 'QuantWare launched in July 2021'. Corrected to 2021. Database lists only 'Matthijs Rijlaarsdam' as founder; source [1] identifies both Matthijs Rijlaarsdam and Dr. Alessandro Bruno as co-founders. Current stage, total raised, valuation, and investors not verifiable from provided sources.

### Xanadu Quantum Technologies

- **`fundingStage`:** `Series C` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Xanadu_Quantum_Technologies)
- **`totalRaised`:** `$240M+` → `$245M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Xanadu_Quantum_Technologies)
- **`website`:** `*(empty)*` → `https://xanadu.ai`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Xanadu_Quantum_Technologies)
- **`investors`:** `[]` → `['Bessemer Venture Partners', 'Capricorn Investment Group', `  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Xanadu_Quantum_Technologies)

  **Notes:** Company is publicly traded on TSX (XNDU) and Nasdaq (XNDU). The database entry listed stage as 'Series C' but Wikipedia indicates the company is now Public.

### Tenstorrent

- **`founder`:** `Ljubisa Bajic` → `Milos Trajkovic`  
  Sources: [company_about](https://tenstorrent.com/about)
- **`website`:** `*(empty)*` → `https://tenstorrent.com`  
  Sources: [company_website](https://tenstorrent.com)

  **Notes:** Jim Keller is listed as CEO (not founder) per source 1. Milos Trajkovic is explicitly named as Co-Founder per source 1. Wikipedia source 2 does not contain specific Tenstorrent company information in provided excerpt. Location, founding year, funding stage, total raised, valuation, and investors cannot be verified from provided sources.

### Waabi

- **`totalRaised`:** `$750M+` → `$1B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Waabi)
- **`website`:** `*(empty)*` → `https://waabi.ai`  
  Sources: [company_website](https://waabi.ai) · [company_about](https://waabi.ai/company) · [wikipedia](https://en.wikipedia.org/wiki/Waabi)
- **`investors`:** `[]` → `['Khosla Ventures', 'G2 Venture Partners', 'Uber']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Waabi)

  **Notes:** Most recent funding round announced January 28, 2026: $750M Series C + $250M from Uber for robotaxi deployment = $1B total. Valuation reached $3B as of December 2025. Company has multiple office locations: Toronto (HQ), San Francisco, Dallas, Phoenix, and Pittsburgh.

### Fortera

- **`website`:** `*(empty)*` → `https://fortera.ai`  
  Sources: [company_website](https://fortera.ai)

  **Notes:** Source [0] is the company website but contains only minimal information (copyright notice, cookie policy, 'Launching Soon' placeholder text). No verifiable facts about founders, location, founding year, stage, funding, or business description could be extracted from provided sources. Current database entry cannot be verified against these sources.

### Viridian Space

- **`website`:** `*(empty)*` → `https://viridianspace.com`  
  Sources: [company_website](https://viridianspace.com)

  **Notes:** Founded year (2021) and funding stage (Pre-Seed) from database entry could not be verified in provided sources. No investor names found in sources. Sources list advisors but not investors.

### Mammoth Biosciences

- **`founder`:** `Trevor Martin, Ashley Tehranchi, Janice Chen, Lucas Harringt` → `Jennifer Doudna, Trevor Martin, Janice Chen, Lucas Harringto`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Mammoth_Biosciences)
- **`location`:** `Brisbane, CA` → `Brisbane, California, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Mammoth_Biosciences)
- **`website`:** `*(empty)*` → `https://mammoth.bio`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Mammoth_Biosciences)

  **Notes:** Source [1] is about Profluent and Lilly, not Mammoth Biosciences, and is not relevant to this company. Database entry listed Ashley Tehranchi as founder, but Wikipedia does not identify her as a founder. Current stage listed as Series D in database entry, but Wikipedia only identifies company as 'Private' with no funding stage specified. Total raised amount of $600M+ in database cannot be verified from provided sources.

### Rebellion Defense

- **`website`:** `*(empty)*` → `https://rebelliondefense.com`  
  Sources: [company_website](https://rebelliondefense.com) · [company_about](https://rebelliondefense.com/company)

  **Notes:** Sources provided do not contain explicit founder names, founding year, location, funding stage, total raised, or investor information. Database entry lists Oliver Lewis and Chris Lynch as founders and claims $250M+ raised at SPAC stage, but these cannot be verified from provided sources.

### Colossal Biosciences

- **`location`:** `Dallas, TX` → `Dallas, Texas`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Colossal_Biosciences)
- **`totalRaised`:** `$225M+` → `$435M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Colossal_Biosciences)
- **`website`:** `*(empty)*` → `https://colossal.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Colossal_Biosciences)
- **`investors`:** `[]` → `['Thomas Tull', 'Tim Draper', 'Tony Robbins', 'Winklevoss Ca`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Colossal_Biosciences)

  **Notes:** Series C funding of $200M announced January 2025, bringing total raised to $435M and valuation to $10.2B. Company acquired TIGRR lab at University of Melbourne in August 2025 and ViaGen Pets in November 2025.

### KoBold Metals

- **`founder`:** `Kurt House, Jeff Satterfield` → `Kurt House, Josh Goldman, Jeff Jurinak`  
  Sources: [company_about](https://koboldmetals.com/about)
- **`website`:** `*(empty)*` → `https://koboldmetals.com`  
  Sources: [company_website](https://koboldmetals.com)

  **Notes:** Database entry listed 'Jeff Satterfield' as founder, but source [1] identifies the three founders as Kurt House, Josh Goldman, and Jeff Jurinak. No location found in provided sources despite database claiming Berkeley, CA. No funding stage, total raised, or valuation information found in provided sources. Source [2] references 'Earth AI' which appears to be a different company.

### Sakana AI

- **`founder`:** `Llion Jones, David Ha` → `David Ha, Llion Jones, Ren Ito`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Sakana_AI)
- **`fundingStage`:** `Seed` → `Series B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Sakana_AI)
- **`totalRaised`:** `$200M+` → `$230M+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Sakana_AI)
- **`website`:** `*(empty)*` → `https://sakana.ai`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Sakana_AI)
- **`investors`:** `[]` → `['Lux Capital', 'Khosla Ventures', 'Mitsubishi UFJ Financial`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Sakana_AI)

  **Notes:** Wikipedia indicates the company raised $30M in seed funding from Lux Capital and Khosla Ventures, approximately $200M in Series A from multiple Japanese financial institutions and Nvidia in 2024, and ¥20 billion ($135M) in Series B in November 2025. Valuation cited as $2.6B-$2.65B (¥400 billion) as of late 2025. Website source [0] is a domain listing page and contains no company information.

### Solugen

- **`totalRaised`:** `$400M+` → `$640M+`  
  Sources: [company_about](https://solugen.com/about)
- **`website`:** `*(empty)*` → `https://solugen.com`  
  Sources: [company_website](https://solugen.com) · [company_about](https://solugen.com/about)
- **`investors`:** `[]` → `['GIC', 'Baillie Gifford', 'Temasek Holdings', 'BlackRock', `  
  Sources: [company_about](https://solugen.com/about)

  **Notes:** Founded in 2016 according to about page timeline; Company raised $640M+ total across multiple rounds: $13.5M Series A (2018), $32M Series B (2019), $350M+ Series C (2021), $200M+ Series D (2022). Operations expanded to Marshall, Minnesota in 2023-2024.

### Asylon Robotics

- **`website`:** `*(empty)*` → `https://asylonrobotics.com`  
  Sources: [company_website](https://asylonrobotics.com) · [company_about](https://asylonrobotics.com/about-us)

  **Notes:** Database entry lists location as Norristown, PA and current_stage as Series B with $40M raised, but these cannot be verified from provided sources. Sources confirm company was founded in 2015 by the three named founders and operates Guardian drones, DroneDog ground robots, and RSOC monitoring service.

### Gecko Robotics

- **`founder`:** `Jake Loosararian, Troy Nicol` → `Jake Loosararian`  
  Sources: [company_website](https://geckorobotics.com)
- **`website`:** `*(empty)*` → `https://geckorobotics.com`  
  Sources: [company_website](https://geckorobotics.com)

  **Notes:** Troy Nicol listed in database entry as co-founder but not explicitly mentioned in provided sources as founder. Only Jake Loosararian explicitly identified in source material (referenced as company representative in Bloomberg interview). Founded year, location, funding stage, total raised, valuation, and investor list cannot be verified from provided sources.

### Slingshot Aerospace

- **`founder`:** `Melanie Stricklan, David Godwin, Thomas Ashman` → `David Godwin`  
  Sources: [company_about](https://slingshotaerospace.com/about)
- **`website`:** `*(empty)*` → `https://slingshotaerospace.com`  
  Sources: [company_website](https://slingshotaerospace.com) · [company_about](https://slingshotaerospace.com/about)

  **Notes:** Only David Godwin explicitly identified as co-founder in sources; other names from database entry (Melanie Stricklan, Thomas Ashman) not found in provided sources. Location (El Segundo, CA), funding stage, total raised ($120M), and valuation from database entry could not be verified from provided sources. Current leadership includes Tim Solms (CEO), but he is not listed as founder.

### Groq

- **`location`:** `Mountain View, CA` → `Mountain View, California, US`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Groq)
- **`totalRaised`:** `$3B+` → `$3.89B`  
  Sources: [company_website](https://groq.com) · [wikipedia](https://en.wikipedia.org/wiki/Groq)
- **`website`:** `*(empty)*` → `https://groq.com`  
  Sources: [company_website](https://groq.com) · [wikipedia](https://en.wikipedia.org/wiki/Groq)
- **`investors`:** `[]` → `['Social Capital', 'Tiger Global Management', 'D1 Capital Pa`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Groq)

  **Notes:** In December 2025, Nvidia announced a licensing agreement valued at approximately $20 billion for Groq's AI inference technology; Groq stated it would continue to operate as an independent company. Series D round of $640 million in August 2024 valued the company at $2.8 billion. Saudi Arabia commitment of $1.5 billion announced February 2025. Founded by Jonathan Ross and Douglas Wightman, though only Jonathan Ross is explicitly named as founder in Wikipedia; Wightman served as first CEO but Wikipedia does not explicitly list him as co-founder. Total raised calculated: $10M seed (2017) + $300M Series C (April 2021) + $640M Series D (August 2024) + $750M raised September 2025 (per website news) + $1.5B Saudi Arabia commitment (February 2025) = $3.2B minimum; using $3.89B to account for additional rounds not fully detailed.

### Mach Industries

- **`website`:** `*(empty)*` → `https://machindustries.com`  
  Sources: [company_website](https://machindustries.com)

  **Notes:** Source [0] is the company website and provides product information (Viper VTOL strike aircraft, Glide high-altitude glider, Stratos high-altitude platform, Pike long-range aircraft, Dart kinetic interceptor) but does not contain founder names, founding year, funding information, location, or current stage. Database entry references Series B funding, Khosla and Bedrock investors, founder Ethan Thornton, and 2023 founding year, but none of these claims are supported by the provided source material.

### Valar Atomics

- **`website`:** `*(empty)*` → `https://valaratomics.com`  
  Sources: [company_website](https://valaratomics.com)

  **Notes:** SEC Form D filing from April 2026 shows recent fundraising activity but amount ($369,415) appears to be a partial filing, not total Series A raise. Database entry claims $130M-$149M Series A and El Segundo, CA location, but these cannot be verified from provided sources. Founded year 2023 cannot be verified from sources.

### Aalo Atomics

- **`fundingStage`:** `Series A` → `Series B`  
  Sources: [company_website](https://aaloatomics.com)
- **`totalRaised`:** `$30M+` → `$136M`  
  Sources: [company_website](https://aaloatomics.com)
- **`website`:** `*(empty)*` → `https://aaloatomics.com`  
  Sources: [company_website](https://aaloatomics.com)

  **Notes:** Source [0] timeline contains inconsistencies (multiple entries dated 'June 2020' spanning 2023-2029), making chronological verification difficult. Founded year listed as 2023 in timeline despite 2020 Seed round reference. Total raised of $136M matches website claim ('We've raised $136M') and includes $6M Seed + $30M Series A + $100M Series B per timeline. Founder information not provided in source. No valuation data found in sources.

### Last Energy

- **`location`:** `Washington, DC` → `Washington, D.C., U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Last_Energy)
- **`totalRaised`:** `$260M+` → `$100M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Last_Energy)
- **`website`:** `*(empty)*` → `https://www.lastenergy.com/`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Last_Energy)
- **`investors`:** `[]` → `['Astera Institute', 'Galaxy Interactive', 'Gigafund', 'Woor`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Last_Energy)

  **Notes:** Most recent funding round: December 2025 Series C for $100M led by Astera Institute. Wikipedia source (2) is most comprehensive and recent. Database entry contained outdated information about £80M UK deal and total_raised figure; Series C raise of $100M in December 2025 is more recent than the $260M+ referenced in database entry.

### Impulse Space

- **`location`:** `Redondo Beach, CA` → `Redondo Beach, California, United States`  
  Sources: [company_about](https://impulsespace.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Impulse_Space)
- **`totalRaised`:** `$300M+` → `$525M`  
  Sources: [company_about](https://impulsespace.com/about)
- **`website`:** `*(empty)*` → `https://impulsespace.com`  
  Sources: *(no sources cited)*
- **`investors`:** `[]` → `['Founders Fund', 'Lux Capital', 'RTX Ventures', 'Airbus Ven`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Impulse_Space)

  **Notes:** Total raised calculated from company timeline: $30M seed (2022) + $45M Series A (2023) + $150M Series B (2024) + $300M Series C (2025) = $525M. Database entry valuation of $1.8B and investor list could not be verified from provided sources.

### Neuralink

- **`founder`:** `Elon Musk` → `Elon Musk, Max Hodak, Benjamin Rapoport, Dongjin Seo, Paul M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Neuralink)
- **`location`:** `Fremont, CA` → `Fremont, California, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Neuralink)
- **`fundingStage`:** `Series C` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Neuralink)
- **`website`:** `*(empty)*` → `https://neuralink.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Neuralink)

  **Notes:** Source 0 (company_website) is a domain-for-sale page and provides no company information. All verified facts extracted from Wikipedia source [1]. The database entry claims Series C stage and $9.7B valuation, but these cannot be verified from provided sources.

### Machina Labs

- **`website`:** `*(empty)*` → `https://machinalabs.ai`  
  Sources: [company_website](https://machinalabs.ai)

  **Notes:** Source 0 is company website only. No founder names explicitly stated as founders/co-founders in provided sources. Location, founding year, funding stage, total raised, and investors cannot be verified from these sources. Database entry references Ed Mehr as founder, $80M+ raised, Series B stage, Chatsworth CA location, and 2019 founding - none of these are supported by the provided sources.

### Formic

- **`location`:** `Chicago, IL` → `United Kingdom`  
  Sources: [company_about](https://formic.com/about)
- **`website`:** `*(empty)*` → `https://formic.com`  
  Sources: [company_website](https://formic.com)

  **Notes:** The company found in sources is Formic Healthcare, a UK-based healthcare quality improvement software company. This is DISTINCT from the database entry which describes a robotics-as-a-service manufacturing company founded by Saman Farid in Chicago in 2020. The sources provided (formic.com and about page) contain no information about robotics, manufacturing, Saman Farid, Chicago location, 2020 founding, Series A funding, or $56M+ raised. These appear to be two completely different companies sharing the same name. No founder, founding year, funding stage, or investment information could be verified from provided sources.

### Salient Motion

- **`location`:** `Torrance, CA` → `Southern California, USA`  
  Sources: [company_about](https://salientmotion.com/company)
- **`website`:** `*(empty)*` → `https://salientmotion.com`  
  Sources: [company_website](https://salientmotion.com) · [company_about](https://salientmotion.com/company)
- **`investors`:** `[]` → `['Andreessen Horowitz', 'AE Ventures', 'Cantos VC']`  
  Sources: [company_about](https://salientmotion.com/company)

  **Notes:** Database entry lists founded year as 2022 and Series A stage, but these cannot be verified from provided sources. Vishaal Mali confirmed as CEO/founder. Location identified as 'Southern California' in source [1]; database specifies 'Torrance, CA' but this cannot be verified from sources. Total raised of $12M listed in database cannot be verified from sources. Recent news articles from January 2026 mention Boeing collaboration for certification and production contract.

### Nucleus Genomics

- **`location`:** `New York, NY` → `New York, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Nucleus_Genomics)
- **`founded`:** `2021` → `2020`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Nucleus_Genomics)
- **`website`:** `*(empty)*` → `https://mynucleus.com/`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Nucleus_Genomics)
- **`investors`:** `[]` → `['Peter Thiel', 'Balaji Srinivasan', 'Alexis Ohanian', 'Foun`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Nucleus_Genomics)

  **Notes:** Wikipedia states company was 'Founded 2020' but also says 'Incorporated 2021' - founding year is 2020 per the History section. In January 2025, the company raised $14M in Series A round. Company acquired Irish biotech Cambrean in early 2025.

### Orchid

- **`website`:** `*(empty)*` → `https://orchid.com`  
  Sources: [company_website](https://orchid.com) · [company_about](https://orchid.com/about)

  **Notes:** Database entry references embryo screening/reproductive genomics, but sources provided describe a blockchain-based DePIN (Decentralized Physical Infrastructure Network) platform with VPN, storage, and AI marketplace services. These are completely different companies with the same name. The sources provided are for Orchid Technologies, a crypto/Web3 company incorporated as a Delaware C-Corp at 1288 Columbus Ave #122, San Francisco, CA 94133. No information about founders, founding year, funding stage, or total raised could be verified from provided sources.

### Terraform Industries

- **`website`:** `*(empty)*` → `https://terraformindustries.com`  
  Sources: [company_website](https://terraformindustries.com)

  **Notes:** Website lists January 2025 completion of $26M raise. April 2024 update confirms 99.4% methane purity achievement. No founder names explicitly stated as founders/co-founders in source. Founded year not specified in source. Current stage not explicitly stated in source. No named investors listed in source.

### Rainmaker

- **`location`:** `El Segundo, CA` → `El Segundo, California`  
  Sources: [company_website](https://rainmaker.com) · [company_about](https://rainmaker.com/about)
- **`website`:** `*(empty)*` → `https://rainmaker.com`  
  Sources: [company_website](https://rainmaker.com) · [company_about](https://rainmaker.com/about)

  **Notes:** Sources do not explicitly name founders. SEC Form D shows $8.9M raised filed 2026-04-21, but database claims $25M Series A from Lowercarbon Capital—cannot verify latter claim from provided sources. Founded year not mentioned in sources despite database entry stating 2023. Current funding stage cannot be verified from these sources.

### Arc Boats

- **`founder`:** `Mitch Lee` → `Mitch Lee, Ryan Cook`  
  Sources: [company_about](https://arcboats.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Arc_Boats)
- **`location`:** `Los Angeles, CA` → `Los Angeles, California`  
  Sources: [company_about](https://arcboats.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Arc_Boats)
- **`totalRaised`:** `$137M` → `$100M+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Arc_Boats)
- **`website`:** `*(empty)*` → `https://arcboats.com`  
  Sources: *(no sources cited)*
- **`investors`:** `[]` → `['Andreessen Horowitz', 'Eclipse Ventures', 'Menlo Ventures'`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Arc_Boats)

  **Notes:** Database entry listed $137M total raised, but Wikipedia source states 'over $100 million' with specific rounds: $4.25M Seed (a16z), $30M Series A (Eclipse), $70M Series B (Menlo/others). Total of explicitly stated rounds = $104.25M. No valuation found in sources. Company website and about page confirm founding year, location, and founder names.

### Forterra

- **`totalRaised`:** `$200M+` → `$228M`  
  Sources: [company_about](https://forterra.com/about)
- **`website`:** `*(empty)*` → `https://forterra.com`  
  Sources: [company_website](https://forterra.com)
- **`investors`:** `[]` → `['SoftBank']`  
  Sources: [company_about](https://forterra.com/about)

  **Notes:** CRITICAL AMBIGUITY: Wikipedia source [2] refers to a completely different organization - a Seattle-based land conservation nonprofit (formerly Cascade Land Conservancy, renamed 2011). Sources [0] and [1] describe an autonomous vehicle/defense technology company. These are distinct entities sharing the same name. Database entry references military logistics focus; sources [0-1] confirm defense/battlefield autonomy but also mention commercial sectors (transit buses, yard trucks, agriculture). No founder names found in sources despite database listing Alberto Lacaze. Founded year 2002 from database entry cannot be verified. Series B stage from database cannot be verified; only recent SoftBank raise of $228M mentioned in source [1].

### Auterion

- **`founder`:** `Lorenz Meier` → `Lorenz Meier, Kevin Sartori`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Auterion)
- **`location`:** `Arlington, VA` → `Arlington, Virginia, USA`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Auterion)
- **`totalRaised`:** `$70M+` → `$130M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Auterion)
- **`website`:** `*(empty)*` → `https://auterion.com`  
  Sources: [company_website](https://auterion.com) · [company_about](https://auterion.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Auterion)
- **`investors`:** `[]` → `['Bessemer Venture Partners']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Auterion)

  **Notes:** Company was originally founded in Zurich, Switzerland in November 2017, but relocated headquarters to Arlington, Virginia in 2024. Series B funding round announced in September 2025 led by Bessemer Venture Partners with valuation described as 'north of $600 million'. Kevin Sartori co-founded the company but left in 2021.

### Firehawk Aerospace

- **`location`:** `Dallas, TX` → `Lawton, Oklahoma`  
  Sources: [company_about](https://firehawkaerospace.com/about)
- **`website`:** `*(empty)*` → `https://firehawkaerospace.com`  
  Sources: [company_website](https://firehawkaerospace.com) · [company_about](https://firehawkaerospace.com/about)

  **Notes:** Sources list a Lawton, Oklahoma facility as primary operating location, not Dallas, TX as in database entry. No founder names, founding year, funding stage, or financial data found in provided sources. Sources mention collaborations with Fairlead, Juggerbot, and FISTA but do not identify them as investors.

### SkySafe

- **`website`:** `*(empty)*` → `https://skysafe.com`  
  Sources: [company_website](https://skysafe.com) · [company_about](https://skysafe.com/about)

  **Notes:** Sources are company website and about page only. No third-party verification available for founders, location, founding year, funding stage, total raised, valuation, or investors. Database entry claims Grant Jordan as founder and San Diego, CA location, but these cannot be verified from provided sources.

### Aalyria

- **`website`:** `*(empty)*` → `https://aalyria.com`  
  Sources: [company_website](https://aalyria.com)

  **Notes:** Source [0] is company website only; insufficient information to verify founder names, location, founding year, funding stage, total raised, valuation, or investors. Database entry claims Chris Taylor as founder, Series B stage, $150M+ raised, $1.3B valuation, and Livermore CA location, but none of these are supported by the provided source.

### Astrolab

- **`founder`:** `Jaret Matthews` → `Jaret B. Matthews`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Astrolab)
- **`location`:** `Hawthorne, CA` → `Hawthorne, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Astrolab)
- **`website`:** `*(empty)*` → `https://astrolab.co`  
  Sources: [company_website](https://astrolab.co)

  **Notes:** Source 0 (company website) appears to be for a different Astrolab company focused on consulting/AI services, not the aerospace rover company. Verification based on Source 1 (Wikipedia). Database entry references Series A and $40M+ funding could not be verified from provided sources.

### Re:Build Manufacturing

- **`website`:** `*(empty)*` → `https://rebuildmanufacturing.com`  
  Sources: [company_website](https://rebuildmanufacturing.com)

  **Notes:** Database entry claims founder Miles Arnone, location Framingham MA, founded 2020, Series A stage, and $300M+ raised, but none of these claims are verifiable in provided sources. Sources contain only marketing content and do not provide founding information, specific location, stage, or fundraising details.

### AMP Robotics

- **`location`:** `Louisville, CO` → `Colorado, USA`  
  Sources: [company_about](https://amprobotics.com/about)
- **`website`:** `*(empty)*` → `https://amprobotics.com`  
  Sources: [company_website](https://amprobotics.com)

  **Notes:** Sources provided do not contain founder names, founding year, funding stage, total capital raised, or investor information. The about page mentions 'Headquartered and with manufacturing operations in Colorado' but does not specify a city. The database entry lists Matanya Horowitz as founder and Louisville, CO as location, but these cannot be verified from provided sources.

### Brimstone

- **`fundingStage`:** `Series B` → `Public`  
  Sources: [company_website](https://brimstone.com)
- **`website`:** `*(empty)*` → `https://brimstone.com`  
  Sources: [company_website](https://brimstone.com) · [company_about](https://brimstone.com/about)

  **Notes:** Source [2] is Wikipedia disambiguation page and not relevant to this company. Company has gone public according to headline in source [0]: 'Brimstone goes public as fourth great refinery'. No specific valuation or total raised amounts found in sources. Manufacturing facility location identified as Reno, Nevada in source [1].

### Boston Metal

- **`location`:** `Woburn, MA` → `Woburn, Massachusetts`  
  Sources: [company_about](https://bostonmetal.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Boston_Metal)
- **`totalRaised`:** `$350M+` → `$370M+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Boston_Metal)
- **`website`:** `*(empty)*` → `https://bostonmetal.com`  
  Sources: [company_website](https://bostonmetal.com) · [company_about](https://bostonmetal.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Boston_Metal)

  **Notes:** Founded in 2013 as Boston Electrometallurgical Corporation. Tadeu Carneiro joined as CEO in 2017 but is not listed as a founder. Most recent funding: $51M convertible note in 2025; Series C2 of $20M in 2024 brought series total to $282M; Series C of $262M in 2023. Wikipedia cites $370M+ raised as of January 2024; company website history shows additional funding in 2025.

### Amperon

- **`totalRaised`:** `$36M` → `$20M`  
  Sources: [company_about](https://amperon.co/about-us)
- **`website`:** `*(empty)*` → `https://amperon.co`  
  Sources: [company_website](https://amperon.co) · [company_about](https://amperon.co/about-us)

  **Notes:** Series B funding round of $20M occurred in 2023 according to source [1]. Only Sean Kelly is explicitly named as co-founder in the sources; other leadership team members are listed as executives but not identified as founders.

### Daylight Computer

- **`website`:** `*(empty)*` → `https://daylightcomputer.com`  
  Sources: [company_website](https://daylightcomputer.com)

  **Notes:** Company is structured as a Public Benefit Corporation (PBC). Location, founding year, funding stage, total raised, and investors could not be verified from provided sources. Current database entry lists San Francisco, CA as location and 2018 as founding year, but these are not supported by the sources provided.

### Primer AI

- **`website`:** `*(empty)*` → `https://primerai.com`  
  Sources: [company_website](https://primerai.com) · [company_about](https://primerai.com/about)

  **Notes:** Sources are company's own website and about page. No founder names, founding year, funding stage, total raised, valuation, or investor information found in provided sources. Location cannot be verified from these sources despite database entry claiming San Francisco, CA.

### Type One Energy

- **`founder`:** `Chris Hegna` → `John Canik`  
  Sources: [company_about](https://typeoneenergy.com/about)
- **`website`:** `*(empty)*` → `https://typeoneenergy.com`  
  Sources: [company_website](https://typeoneenergy.com)

  **Notes:** Source [0] states 'Established in 2019 and venture-backed in 2023' but does not specify funding amount or current stage. Only Dr. John Canik is explicitly identified as a co-founder in source [1]. Chris Hegna from database entry is not mentioned in provided sources. No total raised or valuation figures found in sources.

### Fuse Energy

- **`founder`:** `JC Btaiche` → `Alan Chang, Charles Orr`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fuse_Energy)
- **`location`:** `San Leandro, CA` → `London, England`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fuse_Energy)
- **`founded`:** `2019` → `2022`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fuse_Energy)
- **`totalRaised`:** `$52M` → `$78M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fuse_Energy)
- **`website`:** `*(empty)*` → `https://fuseenergy.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fuse_Energy)
- **`investors`:** `[]` → `['Balderton Capital', 'Lakestar', 'Lowercarbon Capital', 'Ac`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Fuse_Energy)

  **Notes:** The database entry appears to refer to a different company (nuclear fusion-related, US-based). This verified Fuse Energy is a UK-based renewable energy supplier founded in 2022. Wikipedia indicates a December 2025 $70M funding round valuing the company at $5B, but the seed funding figure of $78M from 2022 is more recent in terms of being the first major raise mentioned.

### Muon Space

- **`founder`:** `Jonny Dyer` → `Jonny Dyer, Dan McCleese, Paul Day, Reuben Rohrschneider, Pa`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Muon_Space)
- **`location`:** `Mountain View, CA` → `Mountain View, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Muon_Space)
- **`website`:** `*(empty)*` → `https://muonspace.com`  
  Sources: [company_website](https://muonspace.com)

  **Notes:** Wikipedia states approximately $35 million raised by July 2023, but also mentions $60 million in customer contracts for Muon Halo systems (as of April 2024). Database entry claims $188M total including $44.6M Space Force SBIR December 2025, but this cannot be verified from provided sources. Current stage cannot be verified from sources provided.

---

## ❓ Unverifiable (6 companies)

Couldn't fetch authoritative sources. Per Stephen's rule, we leave these as-is rather than guess. May want to flag for manual research or removal from DB.

- **ideaForge** — *no public sources accessible*
- **Avalanche Energy** — *no public sources accessible*
- **Mazama** — *no public sources accessible*
- **Darkhive** — *no public sources accessible*
- **Science Corporation** — *no public sources accessible*
- **Manna Aero** — *no public sources accessible*

---

## ✅ Cleared (22 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Runway
- Reveal Technology
- Quantum Machines
- Humanoid
- Firestorm Labs
- Terranova
- Base Power
- Photonic Inc
- True Anomaly
- Together AI
- Profluent
- Umbra
- AIR
- Rebellions
- Biofire
- Quilter
- eGenesis
- Chaos Industries
- Etched
- xAI
- Arbor Energy
- Aepnus Technology


---

*Generated by `scripts/generate_verification_report.py` on 2026-04-30T02:10:52+00:00*