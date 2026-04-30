# Company Facts Verification Report

**Generated:** 2026-04-30T07:12:32+00:00  

**Cohort:** `data/cold_email_batch8.json`  

**Cohort size:** 95 companies  

**New Claude extractions this run:** 75  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 13 | 14% |
| 🔧 Changes proposed | 62 | 65% |
| ❓ Unverifiable | 20 | 21% |

---

## 🔧 Proposed Changes (62 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Dataminr

- **`location`:** `New York, NY` → `Manhattan, New York, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Dataminr)
- **`totalRaised`:** `$1.42B` → `$485M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Dataminr)
- **`website`:** `*(empty)*` → `https://dataminr.com`  
  Sources: [company_website](https://dataminr.com) · [company_about](https://dataminr.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Dataminr)
- **`investors`:** `[]` → `['NightDragon', 'HSBC', 'Fortress Investment Group']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Dataminr)

  **Notes:** Wikipedia reports 2025 funding: $85M (March 2025), $100M (April 2025 convertible), $300M (September 2025 convertible) = $485M total for 2025. Current stage not explicitly stated in sources. Acquired WatchKeeper (July 2021), Krizo (October 2021), and announced plans to acquire ThreatConnect for $290M in October 2025.

### Alto Neuroscience

- **`founder`:** `Amit Etkin, Dan Segal, Wei Wu` → `Amit Etkin`  
  Sources: [company_about](https://altoneuroscience.com/about)
- **`website`:** `*(empty)*` → `https://altoneuroscience.com`  
  Sources: [company_website](https://altoneuroscience.com) · [company_about](https://altoneuroscience.com/about)

  **Notes:** Only Amit Etkin is explicitly named as founder in sources; Dan Segal is listed as 'Co-founder and Strategic Advisor' but sources do not clearly establish him as a co-founder at founding. Wei Wu is not mentioned in provided sources. Current stage (Public/NYSE: ANRO), total_raised ($253M), and valuation ($529M) from database entry cannot be verified from provided sources. Location (Los Altos, CA) not mentioned in sources.

### Bethlehem Steel Corp

- **`website`:** `*(empty)*` → `https://bethlehemsteelcorp.com`  
  Sources: [company_website](https://bethlehemsteelcorp.com)

  **Notes:** Source [0] is a minimal landing page with only company name and tagline ('Inspired by Bethlehem's legacy - we've decided that it's time to reinvigorate the American steel industry'). No specific facts about founding year, location, stage, funding, founders, or business description could be verified from provided sources. Database entry claims cannot be verified.

### Gravitics

- **`website`:** `*(empty)*` → `https://gravitics.com`  
  Sources: [company_website](https://gravitics.com)
- **`investors`:** `[]` → `['Tarek Waked', 'Nick Shekerdemian', 'Tim Draper', 'Ryan Kri`  
  Sources: [company_about](https://gravitics.com/team)

  **Notes:** Location (Seattle, WA) inferred from database entry but not explicitly verified in provided sources. Founded year (2021) and funding amounts ($20M, $60M STRATFI) from database entry are not supported by provided sources and therefore marked null. Sources confirm $60M STRATFI award from Space Force (March 26, 2025) but do not specify total raised or current funding stage. Colin Doughan confirmed as CEO & Board Director, not explicitly titled as founder in sources.

### Radian Aerospace

- **`founder`:** `Livingston Holder, Richard Humphrey, Jeff Feige` → `Richard Humphrey, Livingston Holder, Jeff Feige, Curtis Giff`  
  Sources: [company_about](https://radianaerospace.com/company) · [wikipedia](https://en.wikipedia.org/wiki/Radian_Aerospace)
- **`location`:** `Renton, WA` → `Seattle, Washington`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Radian_Aerospace)
- **`totalRaised`:** `$33M` → `$27.5M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Radian_Aerospace)
- **`website`:** `*(empty)*` → `https://radianaerospace.com`  
  Sources: [company_website](https://radianaerospace.com) · [company_about](https://radianaerospace.com/company) · [wikipedia](https://en.wikipedia.org/wiki/Radian_Aerospace)
- **`investors`:** `[]` → `['Fine Structure Ventures']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Radian_Aerospace)

  **Notes:** Wikipedia lists Curtis Gifford as co-founder; company website lists him as CFO and COO but does not explicitly label him as co-founder, though Wikipedia does. Wikipedia also specifies location as 'Seattle, Washington' while database entry states 'Renton, WA' — Seattle is the verified headquarters per Wikipedia.

### Velo3D

- **`website`:** `*(empty)*` → `https://velo3d.com`  
  Sources: [company_website](https://velo3d.com)

  **Notes:** Source [0] is company website only; cannot verify founder names, founding year, funding stage, total raised, or valuation from provided sources. Database entry claims Benny Buller as founder, 2014 founding, Public stage, and $300M+ raised, but none of these are supported by the single source provided.

### BotBuilt

- **`website`:** `*(empty)*` → `https://botbuilt.com`  
  Sources: [company_website](https://botbuilt.com)

  **Notes:** Source [0] is the company website but contains no information about founders, location, founding year, funding stage, total raised, or investors. The database entry references these fields but no supporting evidence was found in the provided sources.

### Ascend Elements

- **`founder`:** `Mike O'Kronley` → `Eric Gratz`  
  Sources: [company_about](https://ascendelements.com/about)
- **`website`:** `*(empty)*` → `https://ascendelements.com`  
  Sources: [company_website](https://ascendelements.com)

  **Notes:** Eric Gratz identified as Co-Founder and Chief Technical Officer in source [1]. Database entry lists 'Mike O'Kronley' as founder, but he is not identified as such in provided sources. Current CEO is Linh Austin (appointed 2025). Sources mention 'A decade of innovation' but no specific founding year stated.

### Amber Bio

- **`website`:** `*(empty)*` → `https://amberbio.com`  
  Sources: [company_website](https://amberbio.com)

  **Notes:** Source [0] appears to be a website for a mobile app for biological data analysis and visualization, not a therapeutics company. This does not match the database entry description about RNA editing therapeutics. Unable to verify any claims about Amber Bio as described in the database entry using provided sources.

### Signaloid

- **`website`:** `*(empty)*` → `https://signaloid.com`  
  Sources: [company_website](https://signaloid.com)

  **Notes:** Source [1] lists 'Phillip' as 'Founder, CEO/CTO' but does not provide full name; full name 'Phillip Stanley-Marbell' comes from database reference only and cannot be verified from provided sources. Location, founded year, stage, and funding information from database entry cannot be verified against provided sources.

### Apis Cor

- **`website`:** `*(empty)*` → `https://apiscor.com`  
  Sources: [company_website](https://apiscor.com)

  **Notes:** Source [0] is for a different company (Apiscor, Inc. - a managed IT services company based on website content). No sources provided match the database entry for Apis Cor (3D printing construction technology company). Cannot verify any facts about the 3D printing construction company from provided sources.

### Valthos

- **`website`:** `*(empty)*` → `https://valthos.com`  
  Sources: [company_website](https://valthos.com)
- **`investors`:** `[]` → `['OpenAI', 'Lux Capital', 'Founders Fund']`  
  Sources: [company_website](https://valthos.com)

  **Notes:** Source [0] mentions founding team members come from Palantir, DeepMind, the Broad Institute, and the Arc Institute, but does not explicitly name individuals as founders. Database entry lists 'Kathleen McMahon' and 'Tess van Stekelenburg' as founders, but these names do not appear in provided sources. Founded year, stage, and total raised from database entry cannot be verified from sources provided.

### Freenome

- **`founder`:** `Gabriel Otte` → `Riley Ennis`  
  Sources: [company_about](https://freenome.com/about)
- **`founded`:** `*(empty)*` → `2014`  
  Sources: [company_about](https://freenome.com/about)
- **`website`:** `*(empty)*` → `https://freenome.com`  
  Sources: [company_website](https://freenome.com)

  **Notes:** Only Riley Ennis is explicitly named as Co-Founder in sources. Gabriel Otte from database entry is not mentioned in provided sources. Location (South San Francisco, CA), public status, total_raised ($1.3B+), and valuation ($2.6B) from current database entry cannot be verified from these sources. Board members and leadership listed but not identified as founders.

### SandboxAQ

- **`founded`:** `*(empty)*` → `2022`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SandboxAQ)
- **`totalRaised`:** `$800M+` → `$500M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SandboxAQ)
- **`website`:** `*(empty)*` → `https://sandboxaq.com`  
  Sources: [company_website](https://sandboxaq.com) · [company_about](https://sandboxaq.com/about-us)
- **`investors`:** `[]` → `['Eric Schmidt', 'Breyer Capital', 'T. Rowe Price', 'TIME Ve`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/SandboxAQ)

  **Notes:** Founded as spinout from Alphabet in March 2022. Wikipedia confirms $500M raised as of February 2023. Wikipedia also notes December 2024 report of commercialization difficulties. Eric Schmidt listed as Chairman of Board (source 1), not investor per se, but mentioned as initial investor in source 2.

### Open Cosmos

- **`founder`:** `Rafel Jordà Siquier` → `Rafel Jorda Siquier, Jordi Barrera Ars, Aleix Megias Homar`  
  Sources: [company_about](https://open-cosmos.com/about)
- **`location`:** `Harwell, UK` → `Harwell, United Kingdom`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Open_Cosmos)
- **`totalRaised`:** `$63M` → `$50M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Open_Cosmos)
- **`website`:** `*(empty)*` → `https://www.open-cosmos.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Open_Cosmos)
- **`investors`:** `[]` → `['ETF Partners', 'Trill Impact', 'A&G', 'Accenture Ventures'`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Open_Cosmos)

  **Notes:** Founded by Rafel Jorda Siquier in 2015. Co-founders Jordi Barrera Ars (CTO) and Aleix Megias Homar (COO) explicitly identified in source [1]. In September 2023, raised $50M from ETF Partners, Trill Impact, A&G and Accenture Ventures (source [2]). In July 2025, acquired Portuguese start-up Connected (source [2]). Database entry reference to 'Atlantic Constellation for Spain' is not verified in sources; Wikipedia mentions 'UK Atlantic Constellation Pathfinder' and 'Greek government constellation' but not a Spain constellation.

### Fractile

- **`totalRaised`:** `$15M+ (raising $200M)` → `$15M`  
  Sources: [company_website](https://fractile.com)
- **`website`:** `*(empty)*` → `https://fractile.com`  
  Sources: [company_website](https://fractile.com)

  **Notes:** Source [2] (Wikipedia) is about the statistical concept of 'quantiles', not the company Fractile, and is therefore not relevant. Founded year cannot be verified from sources; database entry lists 2022 but no source confirms this. Valuation cannot be verified; database entry notes '~$1B (rumored)' but sources do not contain this claim. Investors list is empty as no specific investor names are mentioned in sources. Company has offices in both Bristol and London per source [1].

### Magdrive

- **`location`:** `Harwell, UK` → `Harwell, Oxfordshire, United Kingdom`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Magdrive)
- **`totalRaised`:** `$12.5M equity (~$22M including public grants)` → `$22.5M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Magdrive)
- **`website`:** `*(empty)*` → `https://magdrive.space`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Magdrive)
- **`investors`:** `[]` → `['Redalpine', 'Founders Fund', 'Balerion Space Ventures', 'A`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Magdrive)

  **Notes:** Wikipedia source indicates total raised of $22.5M as of early 2025 (including public funding from UK Government, UK Space Agency, and European Space Agency), which differs slightly from database entry of $12.5M equity + ~$22M total. Most recent verifiable figure is $22.5M total from February 2025 seed round announcement.

### Arondite

- **`website`:** `*(empty)*` → `https://arondite.com`  
  Sources: [company_website](https://arondite.com)

  **Notes:** Founded year 2024 and Seed stage from database entry could not be verified in provided sources. No funding information found in sources. Will Blyth listed as CO-FOUNDER & CEO; Rob Underhill listed as CO-FOUNDER & CTO in source [0].

### Nordic Air Defence

- **`website`:** `*(empty)*` → `https://nordicairdefence.com`  
  Sources: [company_website](https://nordicairdefence.com)

  **Notes:** Founder name 'Karl Rosander' from database entry could not be verified in provided sources. Founded year 2023, seed stage, and funding details from database entry could not be verified in provided sources. Product name 'Kreuger 100' confirmed; described as patent-pending and made in Sweden.

### Kvertus

- **`founder`:** `Yaroslav Filimonov` → `Yaroslav Filimonov, Andrii Znaichenko`  
  Sources: [company_about](https://kvertus.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Kvertus)
- **`founded`:** `2014` → `2017`  
  Sources: [company_about](https://kvertus.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Kvertus)
- **`website`:** `*(empty)*` → `https://kvertus.com`  
  Sources: [company_website](https://kvertus.com) · [company_about](https://kvertus.com/about)

  **Notes:** Company has two headquarters: Kyiv HQ and London HQ as of source publication. Database entry lists founded year as 2014, but sources [1] and [2] both confirm 2017 as founding year. Database entry mentions Yaroslav Filimonov as sole founder, but sources [1] and [2] identify both Yaroslav Filimonov and Andrii Znaichenko as co-founders.

### Vyriy Drone

- **`website`:** `*(empty)*` → `https://vyriydrone.com`  
  Sources: [company_website](https://vyriydrone.com)

  **Notes:** Source [0] is the company website but contains only minimal information (header/footer, cookie notice, 'Launching Soon' placeholders). No verifiable facts about description, founders, location, founding year, funding, stage, or valuation could be extracted from provided sources.

### Skyeton

- **`website`:** `*(empty)*` → `https://skyeton.com`  
  Sources: [company_website](https://skyeton.com)

  **Notes:** Founded 2006; company claims '20-year legacy' as of 2026. Production plant opening in Slovakia confirmed for 2024. No founder names explicitly identified in sources. Roman Knyazhenko mentioned in database entry but not verified in provided sources.

### Ark Robotics

- **`website`:** `*(empty)*` → `https://ark-robotics.com`  
  Sources: [company_website](https://ark-robotics.com)

  **Notes:** Founder name 'Achi Takagama' from database entry could not be verified in source. Founded year 2024 and seed stage from database entry could not be verified in source. Source [0] mentions live demonstration at DALO Expo Denmark 2025 and control range of 2,000 kilometres, but does not specify founding year, stage, or funding information. No founder names explicitly listed as founders/co-founders in source.

### WB Group

- **`founded`:** `2007` → `1997`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/WB_Group)
- **`website`:** `*(empty)*` → `https://www.wbgroup.pl/en/`  
  Sources: [company_website](https://wbgroup.com) · [wikipedia](https://en.wikipedia.org/wiki/WB_Group)
- **`investors`:** `[]` → `['Polish Development Fund']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/WB_Group)

  **Notes:** Wikipedia lists founded year as 1997, not 2007 as in database entry. Key person listed as Piotr Wojciechowski but not explicitly named as founder in Wikipedia (only in Key people section). Polish Development Fund invested PLN 128 million (EUR 30 million or USD 34 million) in 2017 for 24% of shares. No IPO or Pre-IPO status verified in sources. Current stage cannot be verified.

### Astrolight

- **`website`:** `*(empty)*` → `https://astrolight.com`  
  Sources: [company_website](https://astrolight.com)

  **Notes:** Source [0] is the company website and confirms products (ATLAS-2, optical ground stations, POLARIS) but does not contain founder names, founding year, funding stage, or investment details. Database entry mentions NATO DIANA selection and €2.8M raised, but these claims are not present in provided sources and therefore cannot be verified.

### H Company

- **`founder`:** `Charles Kantor, Laurent Sifre, Karl Tuyls, Julien Perolat, D` → `Laurent Sifre, Charles Kantor, Daan Wiestra, Karl Tuyls, Jul`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/H_Company)
- **`founded`:** `2024` → `2023`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/H_Company)
- **`website`:** `*(empty)*` → `https://hcompany.ai`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/H_Company)
- **`investors`:** `[]` → `['Eric Schmidt', 'Amazon', 'Accel', 'Bpifrance', 'UiPath', '`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/H_Company)

  **Notes:** Sources 0 and 1 refer to 'Hahn & Company', a Korea-based private equity firm founded in 2010, which is a different company. Wikipedia source [2] confirms H Company is a French AI startup founded in 2023. Database entry listed founded year as 2024, but Wikipedia clearly states 2023. Charles Kantor stepped down as CEO in June 2025 and was replaced by Gautier Cloix.

### FlexAI

- **`website`:** `*(empty)*` → `https://flexai.io`  
  Sources: [company_website](https://flexai.io)

  **Notes:** Source [0] describes a company called FlexAI focused on smart manufacturing, AI, and computer vision solutions for production automation. This contradicts the database entry which describes FlexAI as an AI compute orchestration platform for GPU training. These appear to be different companies with the same name. No facts from the provided source can verify the database entry (founders, location, founding year, funding amount, or stage). Source [0] alone cannot establish which FlexAI is correct.

### DiamFab

- **`website`:** `*(empty)*` → `https://diamfab.com`  
  Sources: [company_website](https://diamfab.com)

  **Notes:** Source [0] is company website only; cannot verify founders, location, founding year, stage, funding, or investors from provided sources. Database entry lists founders (Khaled Driche, Gauthier Chicot), location (Grenoble, France), founded 2019, Seed stage, €8.7M raised, but none of these are supported by the single source provided.

### Kreios Space

- **`founder`:** `Fermín Navarro` → `Adrián Senar, Jan Mataró, Francisco Boira, Adria Barceló, Ma`  
  Sources: [company_about](https://kreiosspace.com/about)
- **`location`:** `Vigo, Spain` → `Nigrán, Spain`  
  Sources: [company_website](https://kreiosspace.com)
- **`totalRaised`:** `$9M (NATO Innovation Fund)` → `€8M`  
  Sources: [company_website](https://kreiosspace.com)
- **`website`:** `*(empty)*` → `https://kreiosspace.com`  
  Sources: [company_website](https://kreiosspace.com)
- **`investors`:** `[]` → `['SpaceQuest Ventures']`  
  Sources: [company_website](https://kreiosspace.com)

  **Notes:** Most recent funding round announced September 18, 2025: €8M Seed financing. Prior Pre-Seed round of €2.3M closed July 24, 2024. Database entry listed €9M from NATO Innovation Fund, but sources only confirm €8M Seed (Sept 2025) and €2.3M Pre-Seed (July 2024). Location specified as Rúa Montes da Barxa 10, Nave 8, Parque Empresarial de Porto do Molle 36350 Nigrán, Spain.

### Argotec

- **`website`:** `*(empty)*` → `https://www.argotecgroup.com/`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Argotec)

  **Notes:** Wikipedia source (index 2) describes Argotec as an aerospace company producing microsatellites. Website sources (indices 0-1) describe a different company (Argotec, a Mativ brand) focused on engineered polymer films. These appear to be two different companies with the same name. Database entry references aerospace/satellites (matching Wikipedia), so verification is based on Wikipedia source. The 'seven satellites for Italy's IRIDE constellation launched in 2025' could not be verified from provided sources - Wikipedia only mentions a contract signed in December 2022 for 'first batch of 10 satellites for IRIDE' with no launch confirmation.

### iQPS

- **`fundingStage`:** `Public (Tokyo)` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/iQPS)
- **`website`:** `*(empty)*` → `https://i-qps.net`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/iQPS)

  **Notes:** Wikipedia categories indicate company is listed on Tokyo Stock Exchange, confirming public status. The database entry mentions 'Japan MoD constellation award' but this specific claim is not verified in the provided source.

### Preferred Networks

- **`totalRaised`:** `JPY 24B+ (~$160M)` → `¥16.88B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Preferred_Networks)
- **`website`:** `*(empty)*` → `https://www.preferred.jp`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Preferred_Networks)
- **`investors`:** `[]` → `['Toyota', 'FANUC', 'NTT', 'Panasonic', 'NVIDIA', 'Intel', '`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Preferred_Networks)

  **Notes:** Founded March 26, 2014 as spinoff from Preferred Infrastructure (established March 2006). As of July 2019, total raised was ¥16.88B with valuation of ¥3,516,745,800. Company is private/unlisted. Developed MN-Core accelerator and MN-3 supercomputer; discontinued Chainer development in December 2019.

### Terra Drone

- **`website`:** `*(empty)*` → `https://terradrone.ai`  
  Sources: [company_website](https://terradrone.ai)

  **Notes:** Source [0] is a company website with minimal content (launching soon placeholder). No verifiable facts about founders, location, founding year, funding, stage, or business description could be extracted from provided sources. Database entry claims cannot be verified against these sources.

### ACSL

- **`location`:** `Tokyo, Japan` → `Karlsruhe, Germany`  
  Sources: [company_website](https://acsl.ai)
- **`website`:** `*(empty)*` → `https://acsl.ai`  
  Sources: [company_website](https://acsl.ai)

  **Notes:** Database entry appears to reference a different ACSL company (Japanese drone manufacturer). The verified source is an AI research organization in Germany with no connection to industrial/defense drones or Japanese Air Self-Defense Force contracts. Managing Director listed as Dr.-Ing. Christian Gilcher, but not explicitly named as founder.

### Neuromeka

- **`founder`:** `Dongwhan Park` → `Park Jong-hun`  
  Sources: [company_about](https://neuromeka.com/about)
- **`website`:** `*(empty)*` → `https://neuromeka.com`  
  Sources: [company_website](https://neuromeka.com) · [company_about](https://neuromeka.com/about)

  **Notes:** Founder name verified as Park Jong-hun (박 종 훈) from company about page showing him as CEO and founder (창업 대표이사) since 2013. Database entry references KOSDAQ listing and K-Humanoid Alliance membership but these could not be verified from provided sources. Total raised amount of $36.5M from database entry could not be verified from sources.

### Thunder Tiger

- **`location`:** `Taichung, Taiwan` → `Xitun, Taichung, Taiwan`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Thunder_Tiger)
- **`fundingStage`:** `Growth` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Thunder_Tiger)
- **`website`:** `*(empty)*` → `https://www.thundertiger.com`  
  Sources: [company_website](https://www.thundertiger.com) · [wikipedia](https://en.wikipedia.org/wiki/Thunder_Tiger)

  **Notes:** Listed on Taiwan Stock Exchange (TPE: 8033). Company operates multiple divisions: TTRobotix (UAV/ROV), TTBio (dental equipment), TT Solutions (RC vehicles). Database entry claims Gene Su as founder/CEO and $22M expansion—neither verified in sources provided. No information found on current CEO or recent fundraising.

### ABL Bio

- **`website`:** `*(empty)*` → `https://ablbio.com`  
  Sources: [company_website](https://ablbio.com)

  **Notes:** Website is in Korean and provides limited verifiable facts. No specific founder names, founding year, location details, funding amounts, or stage information could be confirmed from the website content provided. Timeline on website shows 2025 partnerships with GSK (April) and Lilly (November) but specific deal terms cannot be verified from this source alone.

### Bellatrix Aerospace

- **`founder`:** `Rohan Ganapathy, Yashas Karanam` → `Rohan M Ganapathy, Yashas Karanam`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Bellatrix_Aerospace)
- **`location`:** `Bengaluru, India` → `Bengaluru, Karnataka, India`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Bellatrix_Aerospace)
- **`totalRaised`:** `$20M+` → `$8M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Bellatrix_Aerospace)
- **`website`:** `*(empty)*` → `https://bellatrixaerospace.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Bellatrix_Aerospace)

  **Notes:** Wikipedia cites $8M Series A funding in June 2022. Database entry references $20M pre-Series B in March 2025, which cannot be verified in provided sources. RUDRA successfully tested in space on POEM-4 on January 2, 2025 per Wikipedia. Company pivoted from launch vehicles to propulsion systems in February 2022.

### Southern Launch

- **`location`:** `Adelaide, Australia` → `Adelaide, South Australia, Australia`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Southern_Launch)
- **`website`:** `*(empty)*` → `https://www.southernlaunch.space`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Southern_Launch)

  **Notes:** Wikipedia source does not contain information about Varda Space re-entry vehicle recoveries, contracted reentries through 2028, current funding stage, total raised, valuation, or named investors. Company operates two launch sites: Koonibba Test Range (sub-orbital) and Whalers Way (orbital). As of 2023, operated Australia's only rocket facilities approved by the Australian Space Agency for launches to space.

### StoreDot

- **`founder`:** `Doron Myersdorf` → `Doron Myersdorf, Simon Litsyn, Gil Rosenman`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/StoreDot)
- **`website`:** `*(empty)*` → `https://store-dot.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/StoreDot)
- **`investors`:** `[]` → `['BP', 'Daimler', 'Samsung', 'TDK', 'Vingroup', 'Ola Electri`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/StoreDot)

  **Notes:** Wikipedia source indicates no commercial products have been released as of February 2026. Company has subsidiary MolecuLED (display technology spin-off). Database entry lists '$206.5M' raised and 'Series E' stage, but these cannot be verified from provided sources.

### Arbe Robotics

- **`founder`:** `Kobi Marenko, Noam Arkind` → `Kobi Marenko, Noam Arkind, Oz Fixman`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Arbe_Robotics)
- **`fundingStage`:** `Public (ARBE)` → `Public`  
  Sources: [company_about](https://arberobotics.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Arbe_Robotics)
- **`totalRaised`:** `IPO` → `$118M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Arbe_Robotics)
- **`website`:** `*(empty)*` → `https://arberobotics.com`  
  Sources: *(no sources cited)*
- **`investors`:** `[]` → `['O.G. Tech', 'OurCrowd', 'Special Situations Funds', 'More `  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Arbe_Robotics)

  **Notes:** Founded November 4, 2015. Became publicly traded on October 6, 2021 through SPAC merger with Industrial Technology Acquisitions, Inc., raising approximately $118M in gross proceeds. Trades on NASDAQ (ARBE) and Tel Aviv Stock Exchange (ARBE). Third founder Oz Fixman listed as former COO in Wikipedia source.

### Space42

- **`website`:** `*(empty)*` → `https://space42.ai`  
  Sources: [company_website](https://space42.ai) · [company_about](https://space42.ai/about-us)

  **Notes:** Sources do not explicitly state founding year, merger details, current stage, or funding amounts. Database entry references 2024 founding and $695.5M ECA financing July 2025, but these are not supported by provided sources. Leadership team listed includes Managing Director Karim Michel Sabbagh and CEO Hasan Al Hosani, but neither are explicitly identified as founders.

### Baykar

- **`founder`:** `Selçuk Bayraktar, Haluk Bayraktar` → `Özdemir Bayraktar`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Baykar)
- **`website`:** `*(empty)*` → `https://www.baykartech.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Baykar)

  **Notes:** Wikipedia lists Özdemir Bayraktar as founder (1984). Selçuk and Haluk Bayraktar are listed as Key people (CTO and GM respectively) but not explicitly named as co-founders in sources provided. Piaggio Aerospace acquisition announced December 27, 2024 per Wikipedia [1]. Leonardo cooperation agreement announced March 6, 2025 per Wikipedia [1]. Revenue listed as $2 billion (2023) in Wikipedia [1]. Valuation and total_raised cannot be verified from provided sources.

### Fergani Space

- **`website`:** `*(empty)*` → `https://ferganispace.com`  
  Sources: [company_website](https://ferganispace.com)

  **Notes:** Source [0] provides minimal information. Founder name (Selçuk Bayraktar) from database entry cannot be verified from provided sources. Current stage, total raised, valuation, and investor information not found in sources. Website content does not specify founders explicitly.

### Ranovus

- **`website`:** `*(empty)*` → `https://ranovus.com`  
  Sources: [company_website](https://ranovus.com) · [company_about](https://ranovus.com/about)

  **Notes:** Founders not explicitly named in provided sources. Founded year (2012) and funding details ($236M, Series D+, $36M SIF grant Aug 2025) from database entry could not be verified against provided sources. Nvidia partnership mentioned in database entry not found in provided sources.

### Canada Rocket Company

- **`totalRaised`:** `$14.7M` → `$6.2M`  
  Sources: [company_website](https://canadarocketcompany.com)
- **`website`:** `*(empty)*` → `https://canadarocketcompany.com`  
  Sources: [company_website](https://canadarocketcompany.com)
- **`investors`:** `[]` → `['BDC', 'Garage Capital']`  
  Sources: [company_website](https://canadarocketcompany.com)

  **Notes:** Database entry claims $14.7M total raised, but source [0] only cites $6.2M seed round from January 16, 2026. No mention of IDEaS defense grant found in sources. Company emerged from stealth January 20, 2026. Hugh Kolias listed as CEO, David Tenny as CTO (not explicitly labeled as founders in source, but listed as key team members).

### Stratek Global

- **`location`:** `Pretoria, South Africa` → `South Africa`  
  Sources: [company_website](https://stratekglobal.com)
- **`website`:** `*(empty)*` → `https://stratekglobal.com`  
  Sources: [company_website](https://stratekglobal.com)

  **Notes:** Company uses branding 'Next Gen Nuclear' (NGN) on website. Website references co-founder Dr. Kelvin Kemm's role in South Africa's nuclear research program. Technical specs verified: 35 MW electric output, 100 MW thermal output, 750°C outlet temperature, 60+ year lifespan. No founding year, funding amount, valuation, or current stage information found in provided sources.

### Alpine Eagle

- **`website`:** `*(empty)*` → `https://alpineeagle.com`  
  Sources: [company_website](https://alpineeagle.com) · [company_about](https://alpineeagle.com/about)

  **Notes:** First systems delivered to Bundeswehr for operational trials in 2024. Deployed with Ukrainian Armed Forces in combat environments in 2025 Q2. Teams based in Munich, London, and Karlsruhe as of 2025 Q1.

### Kipu Quantum

- **`website`:** `*(empty)*` → `https://kipu-quantum.com`  
  Sources: [company_website](https://kipu-quantum.com)

  **Notes:** Sources mention '40,000+ users' and '50+ countries' (source 1), and '405 Organizations' and '1,843 Users' across '20+ Backends' and '26 Countries' (source 0). No founders explicitly named in sources as co-founders. Database entry lists founders (Enrique Solano, Daniel Volz, Tobias Grab) and founding year (2021) but these cannot be verified from provided sources. No funding, valuation, or stage information found in sources.

### Mimic Robotics

- **`totalRaised`:** `$20M+ (including $16M seed)` → `$16M`  
  Sources: [company_website](https://mimicrobotics.com)
- **`website`:** `*(empty)*` → `https://mimicrobotics.com`  
  Sources: [company_website](https://mimicrobotics.com)
- **`investors`:** `[]` → `['Elaia', 'SpeedInvest']`  
  Sources: [company_website](https://mimicrobotics.com)

  **Notes:** Founded by team with ETH Zurich research background. $16M seed round led by Elaia and SpeedInvest announced in 2025. Database entry claiming 'Series B 2025' and 'founded 2024' cannot be verified from sources; sources only confirm $16M seed funding in 2025.

### XMOS

- **`founder`:** `David May` → `Ali Dixon, James Foster, Noel Hurley, David May, Hitesh Meht`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/XMOS)
- **`location`:** `Bristol, UK` → `Bristol, United Kingdom`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/XMOS)
- **`website`:** `*(empty)*` → `https://www.xmos.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/XMOS)
- **`investors`:** `[]` → `['Amadeus Capital Partners', 'DFJ Esprit', 'Foundation Capit`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/XMOS)

  **Notes:** Company type listed as Private. In July 2017, acquired SETEM, a company specializing in audio algorithms for source separation. In December 2023, signed joint development agreement with Sonical for Headphone 3.0 technology. Current CEO & President is Mark Lippett. Database entry claims £200M+ raised, but Wikipedia sources only cite specific amounts totaling less: $16M (2007), $26.2M (2014), $15M (2017), $19M (2019).

### Hexana

- **`founder`:** `Gabriel Lévy` → `Sylvain Nizou, Paul Gauthé`  
  Sources: [company_about](https://hexana.com/team)
- **`website`:** `*(empty)*` → `https://hexana.com`  
  Sources: [company_website](https://hexana.com)

  **Notes:** Database entry mentions €21M seed funding and Groupe M investment (July 2025), but these details cannot be verified from provided sources. Co-founder Paul Gauthé participated in ASTRID project at CEA before co-founding HEXANA in 2023.

### Ukrspecsystems

- **`founder`:** `Yuri Pashchenko` → `Kostyuk Vyacheslav Nikolaevich`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Ukrspecsystems)
- **`website`:** `*(empty)*` → `https://ukrspecsystems.com`  
  Sources: [company_website](https://ukrspecsystems.com) · [wikipedia](https://en.wikipedia.org/wiki/Ukrspecsystems)

  **Notes:** Wikipedia lists founder as 'Kostyuk Vyacheslav Nikolaevich', not 'Yuri Pashchenko' as in database entry. Company type is LLC per Wikipedia. Products include PD-2 (200 km range, 8 hr flight time, 55 kg MTOW), Shark (60 km range, 4 hr flight time, 12 kg MTOW), and Mini Shark (30 km range, 2 hr flight time, 5 kg MTOW). Wikipedia notes first production plant planned for London, February 2026.

### Roboneers

- **`founder`:** `Anton Skrypnyk` → `Anton Skrypnyk, Oleksiy Skrypnyk`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Roboneers)
- **`location`:** `Kyiv, Ukraine` → `Lviv, Ukraine`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Roboneers)
- **`founded`:** `2015` → `2017`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Roboneers)
- **`totalRaised`:** `MoD contracts` → `$2,000,000+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Roboneers)
- **`website`:** `*(empty)*` → `https://roboneers.com`  
  Sources: [company_website](https://roboneers.com) · [wikipedia](https://en.wikipedia.org/wiki/Roboneers)
- **`investors`:** `[]` → `['Oleksiy Skrypnyk']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Roboneers)

  **Notes:** Wikipedia identifies headquarters as Lviv, Ukraine (not Kyiv as in database entry). Company originated from volunteer groups in 2014, formally organized as Roboneers project under Global Dynamics in 2017. Anton Skrypnyk became head in 2022. Products include ShaBlya turret, Ironclad UGV, Rys, and Camel platforms. Oleksiy Skrypnyk invested at least $2 million as main investor.

### Kraken Robotics

- **`location`:** `St. John's, Canada` → `Mount Pearl, Newfoundland and Labrador, Canada`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Kraken_Robotics)
- **`fundingStage`:** `Public (TSX-V)` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Kraken_Robotics)
- **`website`:** `*(empty)*` → `https://krakenrobotics.com`  
  Sources: [company_website](https://krakenrobotics.com) · [wikipedia](https://en.wikipedia.org/wiki/Kraken_Robotics)

  **Notes:** Company was originally founded as 'Kraken Sonar Systems Inc.' in 2012 and changed its name to 'Kraken Robotics Inc.' in 2017. Karl Kenny, the founder, passed away on February 13, 2025 according to source 2. Company is traded on TSX-V under symbol PNG and OTCQB under symbol KRKNF. Revenue was CA$91.3 million in 2024. Completed acquisition of 3D at Depth in 2025 and closed $402.5 million public offering of subscription receipts in March 2026.

### Telesat Lightspeed

- **`location`:** `Ottawa, Canada` → `Ottawa, Ontario, Canada`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Telesat_Lightspeed)
- **`founded`:** `2021` → `1969`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Telesat_Lightspeed)
- **`fundingStage`:** `Growth` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Telesat_Lightspeed)
- **`website`:** `*(empty)*` → `https://telesat.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Telesat_Lightspeed)

  **Notes:** Wikipedia article is about Telesat Corporation (founded 1969, public company traded NASDAQ: TSAT, TSX: TSAT), not specifically 'Telesat Lightspeed' which is the name of their LEO constellation project announced in 2016. Database entry appears to conflate the Lightspeed project with the parent company. No founders explicitly named in sources. No C$2.1B Government of Canada financing mentioned in provided sources. Daniel S. Goldberg confirmed as CEO.

### AbCellera

- **`founder`:** `Carl Hansen` → `Carl Hansen, Véronique Lecault, Kevin Heyries, Daniel Da Cos`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/AbCellera)
- **`location`:** `Vancouver, Canada` → `Vancouver, British Columbia, Canada`  
  Sources: [company_about](https://abcellera.com/about) · [wikipedia](https://en.wikipedia.org/wiki/AbCellera)
- **`fundingStage`:** `Public (NASDAQ)` → `Public`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/AbCellera)
- **`website`:** `*(empty)*` → `https://abcellera.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/AbCellera)

  **Notes:** Company is traded on Nasdaq under ticker ABCL. In 2023, shifted focus from partnerships to advancing internal pipeline. 596 employees as of 2024. Revenue of $38 million in 2023, net loss of US $163 million in 2024.

### Thinking Machines Lab

- **`founder`:** `Mira Murati, John Schulman, Barrett Zoph, Lilian Weng` → `Mira Murati, John Schulman, Barret Zoph, Lilian Weng`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Thinking_Machines_Lab)
- **`location`:** `San Francisco, CA` → `San Francisco, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Thinking_Machines_Lab)
- **`website`:** `*(empty)*` → `https://thinkingmachines.ai`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Thinking_Machines_Lab)
- **`investors`:** `[]` → `['Andreessen Horowitz', 'Nvidia', 'AMD', 'Cisco', 'Jane Stre`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Thinking_Machines_Lab)

  **Notes:** Wikipedia source lists Barret Zoph and John Schulman as founding team members. Barret Zoph and Luke Metz departed in January 2026 to return to OpenAI. The company is structured as a public benefit corporation. Mira Murati holds a weighted voting structure granting her majority decision-making capability.

### Red 6

- **`website`:** `*(empty)*` → `https://red6.com`  
  Sources: [company_website](https://red6.com)

  **Notes:** Source [0] is the company website (red6.com) but the provided content is unreadable/corrupted—only the domain and search engine navigation elements are visible. No factual company information could be extracted from this source. Cannot verify any claims from the database entry (founder name, location, founding year, stage, funding amounts, or description) without readable source material.

### Stratolaunch

- **`founder`:** `Paul Allen (now Cerberus-owned)` → `Paul Allen, Burt Rutan`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Stratolaunch)
- **`location`:** `Mojave, CA` → `Mojave, California, U.S.`  
  Sources: [company_about](https://stratolaunch.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Stratolaunch)
- **`website`:** `*(empty)*` → `https://stratolaunch.com`  
  Sources: [company_website](https://stratolaunch.com) · [company_about](https://stratolaunch.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Stratolaunch)
- **`investors`:** `[]` → `['Cerberus Capital Management']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Stratolaunch)

  **Notes:** Company was founded in 2011 by Paul Allen and Burt Rutan. Acquired by Cerberus Capital Management in 2019. Currently led by CEO Zachary Krevor (since March 2022). Wikipedia notes 360+ employees as of December 2023.

### Reflex Robotics

- **`location`:** `New York, NY` → `Brooklyn, NY`  
  Sources: [company_website](https://reflexrobotics.com)
- **`website`:** `*(empty)*` → `https://reflexrobotics.com`  
  Sources: [company_website](https://reflexrobotics.com)

  **Notes:** Database entry references $7M Khosla-led funding, founders Ravi Gondhalekar and Ben Kaplan, 2022 founding year, and Seed stage — none of these could be verified from the provided source (company website only). Website lists team experience from Boston Dynamics, Tesla, Oculus, and ASML but does not explicitly name founders or provide funding/valuation details.

### Pivotal

- **`founder`:** `Marcus Leng` → `Melinda French Gates`  
  Sources: [company_about](https://www.pivotal.com/about)
- **`website`:** `*(empty)*` → `https://www.pivotal.com`  
  Sources: [company_website](https://www.pivotal.com)

  **Notes:** The sources provided are for Pivotal, a philanthropic organization founded by Melinda French Gates focused on women's social progress—NOT the eVTOL aircraft manufacturer referenced in the database entry. These are two completely different companies with the same name. The database entry appears to refer to a different company (personal eVTOL manufacturer, Larry Page-backed, Marcus Leng founder) which is not present in these sources.

---

## ❓ Unverifiable (20 companies)

Couldn't fetch authoritative sources. Per Stephen's rule, we leave these as-is rather than guess. May want to flag for manual research or removal from DB.

- **Improbable Defence** — *no public sources accessible*
- **HIMERA** — *no public sources accessible*
- **Creotech Instruments** — *no public sources accessible*
- **Comand AI** — *no public sources accessible*
- **Bone AI** — *no public sources accessible*
- **Innoviz Technologies** — *no public sources accessible*
- **HUMAIN** — *no public sources accessible*
- **Nano One Materials** — *no public sources accessible*
- **Axibo AI** — *no public sources accessible*
- **CubeSpace** — *no public sources accessible*
- **QuantumDiamonds** — *no public sources accessible*
- **Distalmotion** — *no public sources accessible*
- **SpaceForest** — *no public sources accessible*
- **MineSense Technologies** — *no public sources accessible*
- **Credo Semiconductor** — *no public sources accessible*
- **Polar Semiconductor** — *no public sources accessible*
- **Scout AI** — *no public sources accessible*
- **Hyfix** — *no public sources accessible*
- **Persona AI** — *no public sources accessible*
- **Sunday Robotics** — *no public sources accessible*

---

## ✅ Cleared (13 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- WEKA
- Stegra
- Primoco UAV
- Quobly
- Stellaria
- Ephos
- Contec
- Q-Factor
- ADASI
- Akaer
- RoboTwin
- Svante
- Scout Space


---

*Generated by `scripts/generate_verification_report.py` on 2026-04-30T07:12:32+00:00*