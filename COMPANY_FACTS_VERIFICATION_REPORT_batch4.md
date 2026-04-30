# Company Facts Verification Report

**Generated:** 2026-04-30T05:35:34+00:00  

**Cohort:** `data/cold_email_batch4.json`  

**Cohort size:** 95 companies  

**New Claude extractions this run:** 82  


## Summary

| Category | Count | % |
|---|---|---|
| ✅ Cleared (data matches sources) | 9 | 9% |
| 🔧 Changes proposed | 73 | 77% |
| ❓ Unverifiable | 13 | 14% |

---

## 🔧 Proposed Changes (73 companies)

Review each change and reply with which ones to apply. **Source-cited diffs:**

### Palantir

- **`location`:** `Aventura, FL` → `Miami, Florida, U.S.`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Palantir)
- **`website`:** `*(empty)*` → `https://palantir.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Palantir)
- **`investors`:** `[]` → `['In-Q-Tel', 'Oakhouse Partners', 'REV']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Palantir)

  **Notes:** Wikipedia source lists headquarters as Miami, Florida (not Aventura, FL as in database entry). Company traded on Nasdaq as PLTR. Four main operating systems identified: Gotham, Foundry, Apollo, and AIP (not just three). Total raised amount not specified in sources. Current valuation not stated in sources.

### Karman Industries

- **`website`:** `*(empty)*` → `https://karmanindustries.com`  
  Sources: [company_website](https://karmanindustries.com)

  **Notes:** Source [0] is company website only. No founder names, location, founding year, funding stage, total raised, or investors could be verified from the provided source. Database entry claims do not appear in the website content provided.

### Applied Intuition

- **`location`:** `Mountain View, CA` → `Sunnyvale, California`  
  Sources: [company_about](https://appliedintuition.com/about)
- **`website`:** `*(empty)*` → `https://appliedintuition.com`  
  Sources: [company_website](https://appliedintuition.com)
- **`investors`:** `[]` → `['Andreessen Horowitz', 'Fidelity Investments', 'Lux Capital`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Applied_Intuition)

  **Notes:** Founded January 2017. Series F round of $600M announced June 2025 at $15B valuation, co-led by BlackRock-managed funds and Kleiner Perkins. Headquarters listed as both Mountain View and Sunnyvale in sources; About page specifies Sunnyvale. Database entry reference to EpiSci acquisition and Army partnerships not verified in provided sources.

### Diode

- **`website`:** `*(empty)*` → `https://diode.io`  
  Sources: [company_website](https://diode.io)

  **Notes:** Database entry references founders 'Davide Asnaghi, Lenny Khazan', location 'Brooklyn, NY', founded 2024, and Seed stage with $10M+ raised, but none of these could be verified in provided sources. Source [2] is Wikipedia article about electronic diodes (component), not the company. Company website does not contain founder names, location, founding year, or funding information in provided excerpts.

### Aurora Innovation

- **`location`:** `Pittsburgh, PA` → `Pittsburgh, Pennsylvania`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Aurora_Innovation)
- **`website`:** `*(empty)*` → `https://aurora.tech`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Aurora_Innovation)
- **`investors`:** `[]` → `['Uber']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Aurora_Innovation)

  **Notes:** Source [0] and [1] are for a Swedish healthcare company (Aurora Innovation AB/Aurora teleQ), not the autonomous vehicle company. All verified facts about the autonomous vehicle company come from Wikipedia [2]. Sterling Anderson resigned in May 2025, effective June 1, 2025.

### Astera Labs

- **`founder`:** `Jitendra Mohan, Sanjay Gajendra` → `Jitendra Mohan, Sanjay Gajendra, Casey Morrison`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Astera_Labs)
- **`location`:** `Santa Clara, CA` → `San Jose, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Astera_Labs)
- **`website`:** `*(empty)*` → `https://asteralabs.com`  
  Sources: [company_website](https://asteralabs.com) · [company_about](https://asteralabs.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Astera_Labs)
- **`investors`:** `[]` → `['Intel Capital', 'Fidelity Investments', 'Sutter Hill Ventu`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Astera_Labs)

  **Notes:** Company went public on NASDAQ under ticker ALAB in March 2024. Originally founded in Santa Clara in 2017 but relocated headquarters to San Jose in June 2025. Wikipedia lists three founders; database entry only mentioned two. IPO valuation was $5.5B as of March 2024.

### Modern Intelligence

- **`founder`:** `John Dulin, Joe Cieslik, Tristan Tager` → `John Dulin`  
  Sources: [company_about](https://modernintelligence.ai/company)
- **`website`:** `*(empty)*` → `https://modernintelligence.ai`  
  Sources: [company_website](https://modernintelligence.ai) · [company_about](https://modernintelligence.ai/company)

  **Notes:** Only John Dulin is explicitly named as CEO in company sources; Joe Cieslik and Tristan Tager from database entry are not mentioned in provided sources as founders or employees. No founding year, location, funding stage, or investment data found in these sources. Copyright notice shows 2022 but does not confirm founding year.

### Mainspring Energy

- **`website`:** `*(empty)*` → `https://mainspringenergy.com`  
  Sources: [company_website](https://mainspringenergy.com)
- **`investors`:** `[]` → `['Khosla Ventures', 'General Catalyst', 'Gates Frontier Fund`  
  Sources: [company_about](https://mainspringenergy.com/about)

  **Notes:** Founded year 2010 and location Menlo Park, CA from database entry could not be verified in provided sources. Series E stage and $400M+ total raised could not be verified in provided sources. No valuation data found in sources.

### Neros

- **`location`:** `El Segundo, CA` → `El Segundo, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Neros)
- **`totalRaised`:** `$110M+` → `$121M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Neros)
- **`website`:** `*(empty)*` → `https://www.neros.tech`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Neros)
- **`investors`:** `[]` → `['Sequoia Capital', 'Founders Fund']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Neros)

  **Notes:** Source 0 (company_website URL) returns a restaurant (Nero's Grille in Livingston, NJ) unrelated to the drone manufacturer. All verified information comes from Wikipedia (source 1). Database entry claims ~1,000 drones monthly production; Wikipedia reports 2,000 drones per day as of December 2025, which is significantly higher. U.S. Marine Corps awarded $17M contract (not reflected in database). No current_stage field verified from sources.

### Allen Control Systems

- **`founder`:** `Mike Wior, Luke Allen, Steven Simoni` → `Mike Wior, Steve Simoni, Luke Allen`  
  Sources: [company_about](https://allencontrolsystems.com/company)
- **`website`:** `*(empty)*` → `https://allencontrolsystems.com`  
  Sources: [company_website](https://allencontrolsystems.com)

  **Notes:** Database entry lists founded year as 2022, Series A stage, $42M total raised, and specific founders Mike Wior, Luke Allen, Steven Simoni, but these details could not be verified from provided sources. Website mentions $10-per-kill cost and $2M Army award in news section but sources do not contain founding year, stage, or funding details.

### Blue Water Autonomy

- **`totalRaised`:** `$64M` → `$50M`  
  Sources: [company_website](https://bluewaterautonomy.com) · [company_about](https://bluewaterautonomy.com/about)
- **`website`:** `*(empty)*` → `https://bluewaterautonomy.com`  
  Sources: [company_website](https://bluewaterautonomy.com) · [company_about](https://bluewaterautonomy.com/about)
- **`investors`:** `[]` → `['GV']`  
  Sources: [company_website](https://bluewaterautonomy.com) · [company_about](https://bluewaterautonomy.com/about)

  **Notes:** Company emerged from stealth in April 2025. Database entry claims $64M total raised, but sources verify only $50M Series A (led by GV, August 2025). Founded year listed as 2024 in database but sources do not explicitly confirm founding year—inferred from 'April 2025 launch' language and 2024 media reference. Liberty Class 190-foot autonomous ship introduced February 2026.

### The Nuclear Company

- **`website`:** `*(empty)*` → `https://thenuclearcompany.com`  
  Sources: [company_website](https://thenuclearcompany.com) · [company_about](https://thenuclearcompany.com/about)

  **Notes:** Sources provided do not contain information about founders, location, founding year, funding stage, total raised, valuation, or investors. The database entry lists founders (Jonathan Webb, Patrick Maloney, Kiran Bhatraju), location (Lexington, KY), founding year (2023), stage (Series A), and total raised ($50M+), but none of these are verifiable from the provided public sources.

### Apex Space

- **`location`:** `Playa Vista, CA` → `Los Angeles, CA`  
  Sources: [company_website](https://apexspace.com)
- **`totalRaised`:** `$400M+` → `$200M`  
  Sources: [company_about](https://apexspace.com/about)
- **`website`:** `*(empty)*` → `https://apexspace.com`  
  Sources: [company_website](https://apexspace.com) · [company_about](https://apexspace.com/about)

  **Notes:** Series D funding of $200M explicitly mentioned in source [1]. Manufacturing facility (Factory One) located in Los Angeles, CA with peak capacity of 200+ buses/year. Database entry reference to '$400M in Series C+D funding' and '$45.9M Space Force contract' could not be verified in provided sources.

### AstroForge

- **`location`:** `Seal Beach, CA` → `Huntington Beach, California`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/AstroForge)
- **`totalRaised`:** `$55M+` → `$53M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/AstroForge)
- **`website`:** `*(empty)*` → `https://www.astroforge.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/AstroForge)

  **Notes:** Wikipedia states founded January 10, 2022. Wikipedia cites $13M seed funding and $40M raised in 2024 (totaling ~$53M). Company website lists Seal Beach headquarters, but Wikipedia (more authoritative source) lists Huntington Beach, California. Odin mission launched February 27, 2025 (not February 26 as website states) and failed due to communication issues as of March 6, 2025.

### Reflect Orbital

- **`location`:** `Hawthorne, CA` → `Hawthorne, California, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Reflect_Orbital)
- **`totalRaised`:** `$20M` → `$35.2M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Reflect_Orbital)
- **`website`:** `*(empty)*` → `https://reflectorbital.com`  
  Sources: [company_website](https://reflectorbital.com) · [company_about](https://reflectorbital.com/team) · [wikipedia](https://en.wikipedia.org/wiki/Reflect_Orbital)
- **`investors`:** `[]` → `['Sequoia Capital', 'Lux Capital', 'Starship Ventures']`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Reflect_Orbital)

  **Notes:** Wikipedia states company was founded in October 2021; also mentions January 2021 founding date. Total funding as of 2026 is $35.2M comprising: $6.5M seed round (September 2024), $20M Series A (May 2025), and $1.25M SBIR Phase II contract (June 2025). First satellite Eärendil-1 planned for launch mid-2026 with SpaceX Falcon 9.

### K2 Space

- **`location`:** `Torrance, CA` → `Torrance, US`  
  Sources: [company_website](https://k2space.com) · [company_about](https://k2space.com/about)
- **`fundingStage`:** `Series C` → `Series B`  
  Sources: [company_website](https://k2space.com)
- **`totalRaised`:** `$360M+` → `$110M`  
  Sources: [company_website](https://k2space.com)
- **`website`:** `*(empty)*` → `https://k2space.com`  
  Sources: [company_website](https://k2space.com)

  **Notes:** Series B funding of $110M announced in February 2025 (source [0] references 'Bloomberg Technology: K2 Space Raises $110M Series B' dated February 13, 2025). The database entry claiming $360M+ total raised and Series C stage cannot be verified from these sources. No founded year is explicitly stated in sources.

### Northwood Space

- **`founded`:** `*(empty)*` → `2024`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Northwood_Space)
- **`totalRaised`:** `$130M+` → `$38M+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Northwood_Space)
- **`website`:** `*(empty)*` → `https://northwoodspace.io`  
  Sources: [company_website](https://northwoodspace.io)

  **Notes:** Database entry claims Series B $100M January 2026 and $49M Space Force contract, but these cannot be verified from provided sources. Wikipedia (source 2) states only $38M+ raised as of 2025. Founders are listed as spouse pair (Griffin Cleverly and Bridgit Mendler married 2019 per Wikipedia). Location in database entry (El Segundo, CA) could not be verified from sources provided.

### Nominal

- **`founder`:** `Cameron McCord, Bryce Strauss` → `Cameron McCord, Bryce Strauss, Jason Hoch`  
  Sources: [company_about](https://nominal.io/about-us)
- **`website`:** `*(empty)*` → `https://nominal.io`  
  Sources: [company_website](https://nominal.io)
- **`investors`:** `[]` → `['Sequoia', 'General Catalyst', 'Lux Capital']`  
  Sources: [company_about](https://nominal.io/about-us)

  **Notes:** Source [1] indicates a Series B-2 funding round of $80M was announced. The database entry lists $155M total raised and $1B valuation, but these figures are not supported by the provided sources. Location is not specified in sources despite database entry claiming Culver City, CA. Founded year 2022 in database entry is not verified by sources.

### Senra Systems

- **`location`:** `Torrance, CA` → `Redondo Beach, CA`  
  Sources: [company_website](https://senrasystems.com) · [company_about](https://senrasystems.com/about)
- **`website`:** `*(empty)*` → `https://senrasystems.com`  
  Sources: [company_website](https://senrasystems.com)

  **Notes:** Database entry lists location as Torrance, CA; sources specify Redondo Beach, CA facility. Sources do not contain verifiable information about founders, founding year, funding stage, total raised, valuation, or specific investor names despite database references to Series A and specific investors. Investor logos visible on website but names not extractable from provided source text.

### Amca

- **`website`:** `*(empty)*` → `https://amca.com`  
  Sources: [company_website](https://amca.com)

  **Notes:** Source [0] is company website only. No information found in sources to verify: founders (Jai Malik, Eli Giovanetti), location (El Segundo, CA), founding year (2024), stage (Series A), total raised ($76.5M), or investors (Caffeinated Capital, Founders Fund, Lux, a16z). Database entry claims require additional sources for verification.

### New Limit

- **`website`:** `*(empty)*` → `https://newlimit.com`  
  Sources: [company_website](https://newlimit.com)
- **`investors`:** `[]` → `['Kleiner Perkins', 'Dimension Capital', 'Founders Fund', 'N`  
  Sources: [company_about](https://newlimit.com/about)

  **Notes:** Sources do not explicitly name founders or confirm founding year, current stage, total raised, or valuation. Investor list includes both institutional firms and individual investors listed on the About page.

### Atom Bodies

- **`website`:** `*(empty)*` → `https://atombodies.com`  
  Sources: [company_website](https://atombodies.com) · [company_about](https://atombodies.com/company)

  **Notes:** Company website uses 'Atom' as primary name with 'Atom Bodies' as secondary identifier. No founding year, location, funding stage, total raised, valuation, or investor information found in provided sources. Database entry lists Series A stage and $2M+ raised, but these cannot be verified from given sources.

### Commonwealth Fusion Systems

- **`founder`:** `Bob Mumgaard, Dennis Whyte, Martin Greenwald, Zach Hartwig, ` → `Bob Mumgaard`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Commonwealth_Fusion_Systems)
- **`location`:** `Devens, MA` → `Devens, Massachusetts, United States`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Commonwealth_Fusion_Systems)
- **`totalRaised`:** `$3B` → `$2.863B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Commonwealth_Fusion_Systems)
- **`website`:** `*(empty)*` → `https://cfs.energy`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Commonwealth_Fusion_Systems)
- **`investors`:** `[]` → `['Eni', 'Breakthrough Energy Ventures', 'Khosla Ventures', '`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Commonwealth_Fusion_Systems)

  **Notes:** Series B funding of $1.8B raised in November 2021 (source 0). Additional Series B2 funding of $863M raised in August 2025 (source 0). Total verified raised: $115M (Series A, 2019) + $84M (Series A2, 2020) + $1.8B (Series B, 2021) + $863M (Series B2, 2025) = $2.863B. Founded in Cambridge, MA as MIT spin-off (source 0), later established campus in Devens. No co-founders explicitly named in source material; only CEO Bob Mumgaard identified by name.

### Xcimer Energy

- **`website`:** `*(empty)*` → `https://xcimerenergy.com`  
  Sources: [company_website](https://xcimerenergy.com) · [company_about](https://xcimerenergy.com/company)

  **Notes:** Database entry lists founded year as 2022, but no source provided confirms this specific year. Database lists Series A stage and $100M+ raised, but sources do not provide funding stage or total raised information. Investor logos appear on source [1] but investor names are not legible in the provided text. Manufacturing operations also located in Tucson, AZ per source [1].

### Lightmatter

- **`website`:** `*(empty)*` → `https://lightmatter.com`  
  Sources: [company_website](https://lightmatter.com)

  **Notes:** Source [0] appears to be a healthcare design/software agency website (not the optical computing company Lightmatter). The website states 'We've joined Cactus!' indicating an acquisition or rebrand. No information about the optical/photonic computing company referenced in the database entry could be verified from the provided source. The company description, founders, location, founding year, funding stage, and total raised from the database entry cannot be verified against this source.

### Substrate

- **`website`:** `*(empty)*` → `https://substrate.com`  
  Sources: [company_website](https://substrate.com)

  **Notes:** Sources provided do not explicitly name founders, specify founding year, disclose funding stage, total raised, valuation, or investor names. Database entry claims cannot be verified against provided sources.

### Cuby Technologies

- **`website`:** `*(empty)*` → `https://cubytechnologies.com`  
  Sources: [company_website](https://cubytechnologies.com)

  **Notes:** Sources provided contain only basic company information from official website. Cannot verify founder names, location, founding year, funding stage, total raised, or investor information from these sources. Database entry contains details not supported by provided sources.

### Rune Technologies

- **`website`:** `*(empty)*` → `https://runetechnologies.co`  
  Sources: [company_website](https://runetechnologies.co)

  **Notes:** Source [0] is company website but contains no readable founder names, founding year, location, funding stage, or investor information despite indicating a 'Backers and investors' section. Database entry references David Tuttle and Peter Goldsborough as founders, Arlington VA location, 2024 founding, Series A stage, and $20M+ raised, but none of these can be verified from the provided source material.

### AnySignal

- **`website`:** `*(empty)*` → `https://anysignal.com`  
  Sources: [company_website](https://anysignal.com)

  **Notes:** Source [0] is company website only. No specific founder names, location, founding year, funding stage, total raised, or investors could be verified from provided sources. Customer testimonials mention 'John' but do not explicitly identify him as a founder or provide full names.

### Albedo

- **`founder`:** `Topher Haddad, AJ Lasater` → `Topher Haddad, AyJay Lasater`  
  Sources: [company_website](https://albedo.com) · [company_about](https://albedo.com/company)
- **`location`:** `Broomfield, CO` → `Denver, CO`  
  Sources: [company_about](https://albedo.com/company)
- **`website`:** `*(empty)*` → `https://albedo.com`  
  Sources: [company_website](https://albedo.com) · [company_about](https://albedo.com/company)

  **Notes:** Wikipedia source [2] is about the physics concept of albedo (light reflectivity), not the company, and was excluded from verification. Founded year not explicitly stated in sources despite database entry claiming 2020. Funding stage and total raised not mentioned in sources. Location listed as 'Broomfield, CO' in database entry but sources consistently reference 'Denver, CO'.

### Array Labs

- **`website`:** `*(empty)*` → `https://arraylabs.com`  
  Sources: [company_website](https://arraylabs.com)

  **Notes:** Source [0] describes a web development and site maintenance company (ArrayLabs, LLC) specializing in open source software, not a satellite/radar mapping company. This appears to be a different company entirely from the database entry, which describes a space technology startup. No verification possible for any frontier-tech company facts from provided sources.

### Armada

- **`website`:** `*(empty)*` → `https://armada.ai`  
  Sources: [company_website](https://armada.ai)

  **Notes:** Wikipedia source [2] is a disambiguation page and provides no company-specific information about the Armada tech company. Sources [0] and [1] are company-controlled and do not disclose founding details, funding amounts, valuation, investors, or founding year. The database entry claims Dan Wright and Jon Runyan as founders, Series B stage, $186M raised, and 2022 founding year, but none of these can be verified from provided sources.

### Air Space Intelligence

- **`founder`:** `Phillip Buckendorf, Kris Dorosz, Lucas Kukielka` → `Lucas Kukielka`  
  Sources: [company_about](https://airspaceintelligence.com/company)
- **`website`:** `*(empty)*` → `https://airspaceintelligence.com`  
  Sources: [company_website](https://airspaceintelligence.com) · [company_about](https://airspaceintelligence.com/company)

  **Notes:** Only Lucas Kukielka is explicitly named as co-founder in source [1]. Phillip Buckendorf and Kris Dorosz from database entry are not mentioned in provided sources. Founded year 2018, Series B stage, $50M+ total raised, and Boston MA location from database entry cannot be verified from provided sources.

### Atmo

- **`website`:** `*(empty)*` → `https://atmo.ai`  
  Sources: [company_website](https://atmo.ai) · [company_about](https://atmo.ai/about)

  **Notes:** Wikipedia source [2] refers to Adobe Atmosphere, a discontinued 3D graphics software from 2001-2004, which is a different product. Only sources [0] and [1] (company website and about page) are relevant to the weather forecasting company. Founders Alex Levy and Johan Mathe could not be verified from provided sources. Founded year, funding stage, total raised, valuation, and specific investors could not be verified from provided sources.

### Beacon AI

- **`location`:** `San Francisco, CA` → `Denver, Colorado`  
  Sources: [company_about](https://beaconai.ai/about)
- **`website`:** `*(empty)*` → `https://beaconai.ai`  
  Sources: [company_website](https://beaconai.ai)

  **Notes:** The sources provided describe a completely different company than the database entry. The sources describe BeaconAI as an AI implementation consulting firm for SMBs founded by Dale Myska (based in Denver, Colorado), NOT an aviation AI copilot company founded by Matt Cox, Avinash Nair, and Andrew Musto. This appears to be a name collision between two different companies. No information about aviation, autonomous flight, pilot assistance, founding year, Series A funding, or the listed founders could be verified from these sources.

### Exowatt

- **`founder`:** `Hannan Parvizian, Jack Abraham` → `Hannan Happi, Jack Abraham`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Exowatt)
- **`location`:** `Miami, FL` → `Miami, Florida`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Exowatt)
- **`totalRaised`:** `$140M` → `$90M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Exowatt)
- **`website`:** `*(empty)*` → `https://exowatt.com`  
  Sources: [company_website](https://exowatt.com)
- **`investors`:** `[]` → `['Andreessen Horowitz', 'Atomic', 'Sam Altman', 'Felicis Ven`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Exowatt)

  **Notes:** Wikipedia source states $90M total as of April 2025 (Series A of $70M added to prior $20M Seed round). Database entry lists $140M which cannot be verified from provided sources. CEO name in Wikipedia is 'Hannan Happi' while database lists 'Hannan Parvizian' — Wikipedia is authoritative source.

### Antora Energy

- **`founder`:** `Andrew Ponec, Justin Briggs` → `Justin Briggs, Andrew Ponec, David Bierman`  
  Sources: [company_about](https://antoraenergy.com/company)
- **`founded`:** `2017` → `2018`  
  Sources: [company_about](https://antoraenergy.com/company)
- **`totalRaised`:** `$244.5M` → `$150M`  
  Sources: [company_website](https://antoraenergy.com)
- **`website`:** `*(empty)*` → `https://antoraenergy.com`  
  Sources: [company_website](https://antoraenergy.com)
- **`investors`:** `[]` → `['BlackRock', 'Temasek']`  
  Sources: [company_website](https://antoraenergy.com)

  **Notes:** Source [1] indicates David Bierman founded Marigold Power in 2017, which 'became part of Antora Energy, which he co-founded in 2018 with Andrew Ponec and Dr. Justin Briggs.' This clarifies the 2018 founding date. Database entry listed $244.5M total raised, but most recent verifiable figure from company website is $150M financing round (mentioned multiple times on homepage). No specific location beyond company website domain found in sources; database lists Sunnyvale, CA but cannot verify from these sources.

### Bedrock Energy

- **`website`:** `*(empty)*` → `https://bedrockenergy.com`  
  Sources: [company_website](https://bedrockenergy.com)

  **Notes:** Source [0] lists Joel Wish as 'Co-founder (Advisor)' but he is marked as an advisor role, not current co-founder. Only Joselyn Lai (Co-founder & CEO) and Silviu Livescu (Co-founder & CTO) are listed as active co-founders. Database entry includes location (San Francisco, CA), founded year (2022), stage (Series A), and total_raised ($15M+) but these cannot be verified from provided sources.

### Atom Computing

- **`location`:** `Berkeley, CA` → `Berkeley, California`  
  Sources: [company_website](https://atom-computing.com) · [wikipedia](https://en.wikipedia.org/wiki/Atom_Computing)
- **`totalRaised`:** `$80M+` → `$60M`  
  Sources: [company_about](https://atom-computing.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Atom_Computing)
- **`website`:** `*(empty)*` → `https://atom-computing.com`  
  Sources: [company_website](https://atom-computing.com)
- **`investors`:** `[]` → `['Innovation Endeavors', 'Venrock', 'Third Point Ventures', `  
  Sources: [company_about](https://atom-computing.com/about)

  **Notes:** Series B funding of $60M closed in January 2022 (source 1, 2). Microsoft partnership announced in late 2024 for logical qubits system. Wikipedia cites a commercial operations facility in Boulder, Colorado opened in 2022. Current CEO listed as Rob Hays in source 1, distinct from founder Ben Bloom.

### Atomic Machines

- **`website`:** `*(empty)*` → `https://atomicmachines.com`  
  Sources: [company_website](https://atomicmachines.com)

  **Notes:** Source [0] is the company website but contains minimal verifiable information. Founder names, location, founding year, funding stage, total raised, and investors from the database entry cannot be verified against the provided sources and are therefore set to null per accuracy rules.

### Bedrock Ocean

- **`website`:** `*(empty)*` → `https://bedrockocean.com`  
  Sources: [company_website](https://bedrockocean.com)

  **Notes:** Source [0] is company website but contains no founder names, location, founding year, funding stage, or investor information. Database entry fields for founders (Anthony DiMare, Charles Chiau), location (Brooklyn, NY), founding year (2019), stage (Series A), and total_raised ($63M) cannot be verified from provided sources.

### Kodiak Robotics

- **`founder`:** `Don Burnette, Paz Eshel` → `Don Burnette`  
  Sources: [company_about](https://kodiakrobotics.com/company)
- **`website`:** `*(empty)*` → `https://kodiakrobotics.com`  
  Sources: [company_website](https://kodiakrobotics.com) · [company_about](https://kodiakrobotics.com/company)

  **Notes:** Company website indicates founding in April 2018. Only Don Burnette is explicitly named as founder in the sources provided; Paz Eshel is not mentioned in these sources. Sources do not contain information about funding stage, total raised, valuation, or named investors. The company operates in trucking, defense, and industrial sectors as stated in source [0].

### Pacific Fusion

- **`website`:** `*(empty)*` → `https://pacificfusion.com`  
  Sources: [company_website](https://pacificfusion.com)

  **Notes:** Source [0] is company website only. No founder names, location, founding year, funding stage, amount raised, valuation, or investor names are explicitly stated in the provided source. Database entry references Eric Lander and Will Regan as founders, $900M Series A, and Fremont CA location, but these cannot be verified from the single source provided.

### Stoke Space

- **`location`:** `Kent, WA` → `Kent, Washington`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Stoke_Space)
- **`fundingStage`:** `Series B` → `Series D`  
  Sources: [company_website](https://stokespace.com) · [company_about](https://stokespace.com/about)
- **`totalRaised`:** `$175M+` → `$860M`  
  Sources: [company_website](https://stokespace.com) · [company_about](https://stokespace.com/about)
- **`website`:** `*(empty)*` → `https://www.stokespace.com/`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Stoke_Space)
- **`investors`:** `[]` → `["Thomas Tull's US Innovative Technology Fund (USIT)", 'Indu`  
  Sources: [company_website](https://stokespace.com) · [company_about](https://stokespace.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Stoke_Space)

  **Notes:** Founded year discrepancy: company website and Wikipedia article state 2019, but Wikipedia info box states 2020. Sources [0] and [1] quote 'When Tom Feldman and I founded Stoke in 2019', supporting 2019. Most recent funding announcement (February 10, 2026) states Series D extension to $860 million total, superseding earlier $510 million October 2025 announcement.

### Mistral AI

- **`fundingStage`:** `Series C` → `Private`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Mistral_AI)
- **`totalRaised`:** `$3B+` → `$14B`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Mistral_AI)
- **`website`:** `*(empty)*` → `https://mistralai.com`  
  Sources: [company_website](https://mistralai.com) · [company_about](https://mistralai.com/about)
- **`investors`:** `[]` → `['Lightspeed Venture Partners', 'Eric Schmidt', 'Xavier Niel`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Mistral_AI)

  **Notes:** Wikipedia indicates €2 billion investment in September 2025 with €12 billion valuation (approximately $14 billion USD). Additional $1.5 billion from ASML reported. March 2026 funding of $830 million for datacenter expansion mentioned in Wikipedia but represents most recent activity.

### ElevenLabs

- **`founder`:** `Piotr Dabkowski, Mati Staniszewski` → `Piotr Dąbkowski, Mati Staniszewski`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/ElevenLabs)
- **`location`:** `New York, NY` → `London`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/ElevenLabs)
- **`fundingStage`:** `Series C` → `Series D`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/ElevenLabs)
- **`totalRaised`:** `$200M+` → `$500M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/ElevenLabs)
- **`website`:** `*(empty)*` → `https://elevenlabs.io`  
  Sources: [company_website](https://elevenlabs.io)
- **`investors`:** `[]` → `['Andreessen Horowitz', 'Sequoia Capital', 'ICONIQ Growth', `  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/ElevenLabs)

  **Notes:** Headquarters listed as London in Wikipedia (source 2), differing from database entry of New York, NY. Most recent funding round: $500M Series D at $11B valuation announced February 4, 2026 (source 2).

### Sublime Systems

- **`website`:** `*(empty)*` → `https://sublimesystems.com`  
  Sources: [company_website](https://sublimesystems.com)

  **Notes:** Source [0] is a company website with minimal content (only navigation elements and copyright visible). No verifiable information about description, founders, location, funding stage, total raised, valuation, or investors could be extracted from provided sources. Database entry contains claims that cannot be verified against source material.

### Inversion Space

- **`totalRaised`:** `$54M + $71M SpaceWERX` → `$44M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Inversion_Space)
- **`website`:** `*(empty)*` → `https://inversionspace.com`  
  Sources: [company_website](https://inversionspace.com) · [company_about](https://inversionspace.com/company)

  **Notes:** Wikipedia notes $44M Series A funding in 2024 (source 2), while company website states $44M raised total (source 1). Company also received $71M STRATFI award from Air Force Research Laboratory and SpaceWERX in September 2024 (source 2), which is separate from equity funding. First spacecraft Ray completed orbital flight in May 2025 without reentry. Arc reentry vehicle unveiled October 2025.

### FleetZero

- **`website`:** `*(empty)*` → `https://fleetzero.com`  
  Sources: [company_website](https://fleetzero.com)
- **`investors`:** `[]` → `['Maersk Growth', 'Breakthrough Energy', 'Obvious Ventures']`  
  Sources: [company_website](https://fleetzero.com)

  **Notes:** Website states Series A funding from named investors occurred in 2026. Source material does not explicitly name founders, so founders field set to null despite database entry listing Steven Henderson and Mike Carter. Total raised amount of $43M from database entry cannot be verified from provided sources.

### Whisper Aero

- **`website`:** `*(empty)*` → `https://whisperaero.com`  
  Sources: [company_website](https://whisperaero.com)

  **Notes:** Database entry lists 'Series A' stage and '$40M+' raised, but these cannot be verified from provided sources. Sources indicate company emerged from stealth in June 2023 and received $1.2M appropriation from Tennessee General Assembly for Flight Test Center in 2024, plus U.S. Air Force STRATFI and OECIF funding mentioned for 2025 aircraft program, but total funding amount not specified.

### Tokamak Energy

- **`location`:** `Oxford, UK` → `Oxford, United Kingdom`  
  Sources: [company_about](https://tokamakenergy.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Tokamak_Energy)
- **`website`:** `*(empty)*` → `https://tokamakenergy.com`  
  Sources: [company_website](https://tokamakenergy.com)
- **`investors`:** `[]` → `['LRG Capital Group', 'East X Ventures', 'Lingotto Investmen`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Tokamak_Energy)

  **Notes:** Source [1] states total raised is $335 million ($275M from private investors and $60M from UK and US governments). Source [2] references earlier figure of $250M as of 2022, and mentions $125M funding round in November 2024. Founders David Kingham and Mikhail Gryaznevich not explicitly named as founders in provided sources, though Gryaznevich appears as author on technical publications. Current stage (Series C) from database entry cannot be verified from sources provided.

### Oxford Quantum Circuits

- **`founder`:** `Peter Leek, Ilana Wisby` → `Peter Leek`  
  Sources: [company_about](https://oxfordquantumcircuits.com/company)
- **`website`:** `*(empty)*` → `https://oxfordquantumcircuits.com`  
  Sources: [company_website](https://oxfordquantumcircuits.com) · [company_about](https://oxfordquantumcircuits.com/company)

  **Notes:** Source [1] explicitly identifies Peter Leek as 'CSO' and founder: 'Founded in 2017 by our CSO Dr. Peter Leek'. No current stage, total raised, valuation, or investor data found in provided sources. Database entry references Ilana Wisby as co-founder and CEO change, but this information is not present in provided sources.

### Proxima Fusion

- **`totalRaised`:** `€200M` → `€145M`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Proxima_Fusion)
- **`website`:** `*(empty)*` → `https://proximafusion.com`  
  Sources: [company_website](https://proximafusion.com) · [company_about](https://proximafusion.com/about) · [wikipedia](https://en.wikipedia.org/wiki/Proxima_Fusion)
- **`investors`:** `[]` → `['Plural Platform', 'UVC Partners', 'Visionaries Club', 'Wil`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Proxima_Fusion)

  **Notes:** Founded April 2023. Series A funding: €130M announced June 2025 plus €15M extension in September 2025, totaling €145M. Previous funding rounds: €7.5M pre-seed and €20M seed. Wikipedia lists 90+ employees as of 2025. Company website describes itself as 'Europe's fastest-growing fusion company.'

### Renaissance Fusion

- **`founder`:** `Simon Belka, Francesco Volpe, Martin Kupp` → `Francesco Volpe, Martin Kupp`  
  Sources: [company_about](https://renaissancefusion.com/company)
- **`totalRaised`:** `$43M` → `$60.5M`  
  Sources: [company_about](https://renaissancefusion.com/company)
- **`website`:** `*(empty)*` → `https://renaissancefusion.com`  
  Sources: [company_website](https://renaissancefusion.com) · [company_about](https://renaissancefusion.com/company)
- **`investors`:** `[]` → `['Lowercarbon Capital', 'Bpifrance', 'Crédit Mutuel']`  
  Sources: [company_about](https://renaissancefusion.com/company)

  **Notes:** Founded July 2020. Total raised includes: 15.5M€ seed round (May 2022, Lowercarbon Capital), 10M€ grant from Bpifrance (November 2023), and 32M€ Series A1 round (December 2024, Crédit Mutuel). Converted to approximate USD equivalent of $60.5M using historical conversion rates. Opened subsidiary Renaissance Fusion Italia in Pisa, October 2025. Simon Belka not explicitly named as founder in sources.

### Hugging Face

- **`location`:** `New York, NY` → `Manhattan, New York City`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Hugging_Face)
- **`website`:** `*(empty)*` → `https://huggingface.co`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Hugging_Face)

  **Notes:** Wikipedia source describes company as 'Private' (no IPO or acquisition status confirmed). Database entry claims Series D stage and $400M raised, but these cannot be verified in provided sources. In April 2025, Hugging Face acquired Pollen Robotics, a humanoid robotics startup.

### Tekever

- **`location`:** `Lisbon, Portugal` → `Lisbon region, Portugal`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Tekever)
- **`website`:** `*(empty)*` → `https://www.tekever.com`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Tekever)

  **Notes:** Wikipedia source does not provide founder names (only states 'founded in 2001 by former students of the IST engineering school'), current funding stage, total raised, or valuation. Database entry lists founders Ricardo Mendes, Vitor Cristina, Pedro Sinogas and Series C stage with $631M+ raised, but these cannot be verified from the Wikipedia source provided.

### Monumental

- **`website`:** `*(empty)*` → `https://monumental.com`  
  Sources: [company_website](https://monumental.com) · [company_about](https://monumental.com/about)

  **Notes:** Sources provided are from Telepathy.com (a domain name registry company), not from Monumental company sources. Sources only confirm that monumental.com is listed in Telepathy's domain portfolio. No information about Monumental's business, founders, funding, or operations could be verified from these sources. The database entry claims cannot be verified against the provided sources.

### Floodbase

- **`founder`:** `Bessie Schwarz, Beth Tellman` → `Bessie Schwarz, Dr. Beth Tellman`  
  Sources: [company_about](https://floodbase.com/about)
- **`website`:** `*(empty)*` → `https://floodbase.com`  
  Sources: [company_website](https://floodbase.com) · [company_about](https://floodbase.com/about)

  **Notes:** Founded at Yale University as a Masters student project. Co-founder Dr. Beth Tellman is Chief Science Officer. Science appeared on cover of Nature in 2021. Database entry lists founded year as 2015 and stage as Series A with $17M raised, but these cannot be verified from provided sources.

### Harbinger

- **`website`:** `*(empty)*` → `https://harbinger.ai`  
  Sources: [company_website](https://harbinger.ai) · [company_about](https://harbinger.ai/about)

  **Notes:** The company referenced in the database entry (Garden Grove, CA; electric vehicle manufacturer) appears to be a different entity than the Harbinger AI described in the provided sources. The sources describe an AI research and data analytics company, not an automotive manufacturer. No founder names, founding year, funding details, or location information could be verified from the provided sources.

### Liminal Insights

- **`website`:** `*(empty)*` → `https://liminalinsights.com`  
  Sources: [company_website](https://liminalinsights.com)

  **Notes:** Source [1] states 'Founded by top technologists from Princeton University and fellows in the Activate entrepreneurial fellowship program' but does not explicitly name founders by full name. Source [1] mentions partnership with Lawrence Berkeley National Laboratory's Cyclotron Road Division. No location information found in provided sources. No specific funding stage, total raised, valuation, or investor names found in provided sources.

### Lumafield

- **`founder`:** `Eduardo Torrealba, Andreas Bastian, Kevin Cedrone, Ric Fulop` → `Eduardo Torrealba, Andreas Bastian`  
  Sources: [company_about](https://lumafield.com/about)
- **`website`:** `*(empty)*` → `https://lumafield.com`  
  Sources: [company_website](https://lumafield.com) · [company_about](https://lumafield.com/about)

  **Notes:** Database entry lists 5 founders (Eduardo Torrealba, Andreas Bastian, Kevin Cedrone, Ric Fulop, Scott Johnston), but source [1] only explicitly identifies Eduardo Torrealba as CEO and Andreas Bastian as Head of Product. Only these two can be verified as founders from provided sources. Series C stage and $142M total raised from database entry could not be verified in provided sources.

### Osaro

- **`website`:** `*(empty)*` → `https://osaro.com`  
  Sources: [company_website](https://osaro.com)

  **Notes:** Founded year cannot be verified from sources (website mentions 'over 10 years' and references to 2017-2018 technology development, but no explicit founding year stated). Series B stage, total raised amount, and investor list from database entry cannot be verified from provided sources. CEO & Co-Founder Derik Pridmore confirmed in source [1]; CTO & Co-Founder Michael Kahane confirmed in source [1].

### WeaveGrid

- **`website`:** `*(empty)*` → `https://weavegrid.com`  
  Sources: [company_website](https://weavegrid.com) · [company_about](https://weavegrid.com/about)

  **Notes:** Database entry claims founding year 2018 and Series B stage with $78M raised, but these facts cannot be verified from provided sources. Sources confirm company operates EV and grid integration programs and received strategic investments from LG Technology Ventures (September 2025) and automotive companies (Toyota Woven Capital, Hyundai Motor, Kia Corporation as of February 2025), but specific funding stage and total amount cannot be verified.

### Zanskar

- **`website`:** `*(empty)*` → `https://zanskar.com`  
  Sources: [company_website](https://zanskar.com)

  **Notes:** Source [1] is Wikipedia article about Zanskar region in Ladakh, India - NOT the company. Only source [0] (company website) contains verified information about Zanskar the geothermal energy company. Founders, location, founding year, funding stage, and total raised cannot be verified from provided sources. Database entry claims cannot be corroborated.

### Kepler Communications

- **`founder`:** `Mina Mitry, Jeffrey Osborne, Mark Michael` → `Mina Mitry, Wen Cheng Chong, Mark Michael, Jeffrey Osborne`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Kepler_Communications)
- **`location`:** `Toronto, Canada` → `Toronto, Ontario, Canada`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Kepler_Communications)
- **`totalRaised`:** `$233M` → `$200M+`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Kepler_Communications)
- **`website`:** `*(empty)*` → `https://kepler.space`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Kepler_Communications)
- **`investors`:** `[]` → `['IA Ventures', 'Costanoa Ventures', 'Canaan Partners', 'Tri`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Kepler_Communications)

  **Notes:** Wikipedia lists four founders; database entry listed only three. Series C funding round of $92M announced April 2023 brings total equity raised to 'over US$200 million' per source. Database entry mentioned optical satellites launching January 2026, ESA HydRON contract, and Canadian Arctic defense contract, but these details are not present in provided sources and cannot be verified.

### Kela

- **`website`:** `*(empty)*` → `https://kela.com`  
  Sources: [company_website](https://kela.com)

  **Notes:** Source [0] describes a fund operations and ODD automation platform for hedge funds, private credit GPs, and mid-market PE firms. This contradicts the database entry which describes a 'defense integration platform' for Israel. The company appears to be a fintech/fund operations platform (A VantedgeAI product), not a defense company. Cannot verify any of the database entry claims (founders, location, founding year, stage, or funding) from provided source. The database entry appears to refer to a different company entirely.

### Vivodyne

- **`location`:** `Philadelphia, PA` → `San Francisco, USA`  
  Sources: [company_website](https://vivodyne.com)
- **`totalRaised`:** `$78M` → `$40M+`  
  Sources: [company_website](https://vivodyne.com)
- **`website`:** `*(empty)*` → `https://vivodyne.com`  
  Sources: [company_website](https://vivodyne.com)

  **Notes:** Series A financing of $40M described as 'Another $40M in Series A Financing' on website, suggesting multiple tranches within Series A stage. Database entry lists $78M total raised; sources only verify $40M Series A announcement.

### Mission Barns

- **`website`:** `*(empty)*` → `https://missionbarns.com`  
  Sources: [company_website](https://missionbarns.com)

  **Notes:** Source [0] is company website only; does not contain founder names, founding year, funding stage, or total raised information. Database entry claims cannot be verified from provided sources.

### Defense Unicorns

- **`totalRaised`:** `$186.5M` → `$171M`  
  Sources: [company_about](https://defenseunicorns.com/about-us)
- **`website`:** `*(empty)*` → `https://defenseunicorns.com`  
  Sources: [company_website](https://defenseunicorns.com)
- **`investors`:** `[]` → `['Ansa Capital', 'Sapphire Ventures', 'Bain Capital']`  
  Sources: [company_about](https://defenseunicorns.com/about-us)

  **Notes:** Total raised calculated from Series A ($35M announced February 2024) plus Series B ($136M announced January 2026). Valuation milestone reached January 2026 with Series B close led by Bain Capital.

### Mythic

- **`founder`:** `Dave Fick, Mike Henry` → `Dave Fick, Laura Fick`  
  Sources: [company_about](https://mythic.ai/about)
- **`location`:** `Austin, TX` → `Palo Alto, CA`  
  Sources: [company_website](https://mythic.ai)
- **`totalRaised`:** `$266M` → `$125M`  
  Sources: [company_website](https://mythic.ai)
- **`website`:** `*(empty)*` → `https://mythic.ai`  
  Sources: [company_website](https://mythic.ai)
- **`investors`:** `[]` → `['DCVC', 'Atreides Management', 'Future Ventures', 'S3 Ventu`  
  Sources: [company_about](https://mythic.ai/about)

  **Notes:** Most recent funding was $125M raise in December 2025 (oversubscribed). Dr. Taner Ozcelik named CEO in June 2024. Laura Fick is identified as Co-Founder; Dave Fick is identified as Co-Founder. Founded year not explicitly stated in sources. Previous database entry listed $266M total raised, but most recent source only confirms $125M December 2025 raise—cannot verify cumulative total without additional sources.

### Electra

- **`location`:** `Boulder, CO` → `Brooklyn, NY`  
  Sources: [company_about](https://electra.com/about-us)
- **`website`:** `*(empty)*` → `https://electra.com`  
  Sources: [company_website](https://electra.com)

  **Notes:** The provided sources describe Electra as a company manufacturing 120V induction stoves with integrated battery systems, NOT a steelmaking company using electrochemistry to refine iron ore. The current database entry appears to reference a completely different company. Sources [0] and [1] are for Electra Research Inc., a kitchen appliance manufacturer located in Brooklyn, NY. Source [2] is about the Greek mythological figure Electra and is not relevant to any company. No founders, funding stage, total raised, or valuation information could be verified from these sources.

### Evozyne

- **`website`:** `*(empty)*` → `https://evozyne.com`  
  Sources: [company_website](https://evozyne.com) · [company_about](https://evozyne.com/about)

  **Notes:** Sources do not explicitly name individual founders (source [1] states 'The company was founded by Paragon Biosciences' but does not list specific founder names). No founding year, funding stage, total raised amount, valuation, or specific investor names appear in provided sources. Database entry lists founders and funding details that cannot be verified from these sources.

### Biobot Analytics

- **`location`:** `Cambridge, MA` → `Cambridge, Massachusetts`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Biobot_Analytics)
- **`website`:** `*(empty)*` → `https://biobot.io`  
  Sources: [wikipedia](https://en.wikipedia.org/wiki/Biobot_Analytics)

  **Notes:** Database entry lists Series B stage and $40M total raised, but these facts are not supported by the provided Wikipedia source. No funding information is included in the source material.

---

## ❓ Unverifiable (13 companies)

Couldn't fetch authoritative sources. Per Stephen's rule, we leave these as-is rather than guess. May want to flag for manual research or removal from DB.

- **CX2 Industries** — *no public sources accessible*
- **Observable Space** — *no public sources accessible*
- **Venus Aerospace** — *no public sources accessible*
- **Quaise Energy** — *no public sources accessible*
- **Bright Machines** — *no public sources accessible*
- **Second Front Systems** — *no public sources accessible*
- **Eikon Therapeutics** — *no public sources accessible*
- **Ambient.ai** — *no public sources accessible*
- **Strider Technologies** — *no public sources accessible*
- **Xage Security** — *no public sources accessible*
- **Positron AI** — *no public sources accessible*
- **Xsight Labs** — *no public sources accessible*
- **Glyphic Biotechnologies** — *no public sources accessible*

---

## ✅ Cleared (9 companies)

Data matches sources for these companies — **no changes needed**.

Sample (first 30):

- Antares
- Captura
- Shinkei
- Atomic Industries
- Helsing
- Twelve
- Alice & Bob
- Latitude
- Ramon.Space


---

*Generated by `scripts/generate_verification_report.py` on 2026-04-30T05:35:34+00:00*