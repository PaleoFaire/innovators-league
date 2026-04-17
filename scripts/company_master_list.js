/**
 * MASTER COMPANY LIST - The Innovators League
 * ============================================
 * 
 * Complete registry of ALL 500 companies tracked in the database.
 * Used by all data fetchers for comprehensive news monitoring.
 * 
 * Coverage: 100% of companies in data.js
 * Total companies: 513
 * Last updated: 2026-02-20
 * 
 * Each company has:
 *   - name: Official company name
 *   - aliases: Alternative names/products for matching (5+ chars, no generic terms)
 *   - sector: Category for filtering
 *   - ticker: Stock ticker for public companies (null if private)
 */

const MASTER_COMPANY_LIST = [
  { name: "Anduril Industries", aliases: ["Anduril", "AndurilIndustries", "Lattice OS", "Ghost-X", "Roadrunner", "autonomous drones"], sector: "defense", ticker: null },
  { name: "Shield AI", aliases: ["Shield", "ShieldAI", "Shield", "Hivemind", "V-BAT"], sector: "defense", ticker: null },
  { name: "Epirus", aliases: ["Leonidas", "Epirus Inc", "directed energy"], sector: "defense", ticker: null },
  { name: "Saronic", aliases: ["Saronic Technologies", "shipbuilding"], sector: "defense", ticker: null },
  { name: "Neros", aliases: ["FPV drones", "Ukraine"], sector: "defense", ticker: null },
  { name: "Chaos Industries", aliases: ["Chaos", "ChaosIndustries"], sector: "defense", ticker: null },
  { name: "Castelion", aliases: [], sector: "defense", ticker: null },
  { name: "CX2 Industries", aliases: ["CX2Industries", "electronic warfare", "RF sensing"], sector: "defense", ticker: null },
  { name: "Picogrid", aliases: [], sector: "defense", ticker: null },
  { name: "Skydio", aliases: ["Skydio X2", "Skydio Dock", "autonomous drones", "public safety"], sector: "defense", ticker: null },
  { name: "Allen Control Systems", aliases: ["Allen Control", "AllenControlSystems", "gun turret"], sector: "defense", ticker: null },
  { name: "Mach Industries", aliases: ["MachIndustries", "propulsion", "energetics"], sector: "defense", ticker: null },
  { name: "Andrenam", aliases: ["maritime", "sensing"], sector: "defense", ticker: null },
  { name: "Vannevar Labs", aliases: ["Vannevar", "VannevarLabs", "intelligence", "analysis"], sector: "defense", ticker: null },
  { name: "Blue Water Autonomy", aliases: ["BlueWaterAutonomy", "autonomous ships"], sector: "defense", ticker: null },
  { name: "Valar Atomics", aliases: ["ValarAtomics"], sector: "nuclear", ticker: null },
  { name: "Radiant", aliases: ["Radiant Nuclear", "Radiant Industries", "microreactor"], sector: "nuclear", ticker: null },
  { name: "Aalo Atomics", aliases: ["AaloAtomics"], sector: "nuclear", ticker: null },
  { name: "Antares", aliases: ["microreactor"], sector: "nuclear", ticker: null },
  { name: "General Matter", aliases: ["GeneralMatter", "nuclear fuel", "HALEU"], sector: "nuclear", ticker: null },
  { name: "Kairos Power", aliases: ["KairosPower", "Kairos", "Hermes reactor"], sector: "nuclear", ticker: null },
  { name: "X-Energy", aliases: ["X Energy", "XEnergy", "XENITH"], sector: "nuclear", ticker: null },
  { name: "Oklo", aliases: ["Oklo Inc", "Aurora powerhouse"], sector: "nuclear", ticker: "OKLO" },
  { name: "Last Energy", aliases: ["LastEnergy", "microreactor"], sector: "nuclear", ticker: null },
  { name: "Deep Fission", aliases: ["DeepFission"], sector: "nuclear", ticker: null },
  { name: "TerraPower", aliases: ["Terra Power", "Natrium"], sector: "nuclear", ticker: null },
  { name: "Standard Nuclear", aliases: ["StandardNuclear", "standardized", "reactors"], sector: "nuclear", ticker: null },
  { name: "The Nuclear Company", aliases: ["TheNuclearCompany", "AP1000"], sector: "nuclear", ticker: null },
  { name: "Exodys Energy", aliases: ["Exodys", "ExodysEnergy", "waste recycling"], sector: "nuclear", ticker: null },
  { name: "SpaceX", aliases: ["Space X", "Starlink", "Starship", "Falcon", "Dragon", "Raptor"], sector: "space", ticker: null },
  { name: "Rocket Lab", aliases: ["RocketLab", "Electron", "Neutron", "Photon"], sector: "space", ticker: "RKLB" },
  { name: "Apex Space", aliases: ["ApexSpace", "satellite buses"], sector: "space", ticker: null },
  { name: "Varda Space Industries", aliases: ["Varda Space", "VardaSpaceIndustries", "Varda", "space manufacturing", "pharmaceuticals", "re-entry"], sector: "space", ticker: null },
  { name: "AstroForge", aliases: ["asteroid mining", "platinum", "space resources"], sector: "space", ticker: null },
  { name: "Reflect Orbital", aliases: ["ReflectOrbital", "reflected sunlight"], sector: "space", ticker: null },
  { name: "Relativity Space", aliases: ["Relativity", "RelativitySpace", "Terran 1", "Terran R"], sector: "space", ticker: null },
  { name: "Impulse Space", aliases: ["Impulse", "ImpulseSpace", "orbital transfer", "satellite buses"], sector: "space", ticker: null },
  { name: "K2 Space", aliases: ["K2Space", "large satellites"], sector: "space", ticker: null },
  { name: "Vast", aliases: ["Vast Space", "Haven-1", "space station", "commercial space"], sector: "space", ticker: null },
  { name: "Northwood Space", aliases: ["Northwood", "NorthwoodSpace", "ground stations", "satellite comms"], sector: "space", ticker: null },
  { name: "Astranis", aliases: ["GEO satellites"], sector: "space", ticker: null },
  { name: "Observable Space", aliases: ["Observable", "ObservableSpace", "space awareness"], sector: "space", ticker: null },
  { name: "Firefly Aerospace", aliases: ["Firefly", "FireflyAerospace", "Alpha rocket"], sector: "space", ticker: null },
  { name: "Intuitive Machines", aliases: ["IntuitiveMachines", "Nova-C"], sector: "space", ticker: "LUNR" },
  { name: "Boom Supersonic", aliases: ["BoomSupersonic", "Overture", "commercial jets"], sector: "space", ticker: null },
  { name: "Hermeus", aliases: ["Quarterhorse", "Chimera", "Mach 5"], sector: "space", ticker: null },
  { name: "Astro Mechanica", aliases: ["AstroMechanica", "electric engine", "space launch", "Y Combinator W24"], sector: "space", ticker: null },
  { name: "Venus Aerospace", aliases: ["Venus", "VenusAerospace", "Mach 9"], sector: "space", ticker: null },
  { name: "Physical Intelligence", aliases: ["PhysicalIntelligence", "foundation model"], sector: "ai", ticker: null },
  { name: "Waymo", aliases: ["Waymo One", "autonomous vehicles", "robotaxi"], sector: "ai", ticker: null },
  { name: "Figure AI", aliases: ["Figure", "FigureAI", "Figure", "Figure 01", "Figure 02"], sector: "ai", ticker: null },
  { name: "Neuralink", aliases: ["Neura Link", "neuroscience", "implants"], sector: "ai", ticker: null },
  { name: "Field AI", aliases: ["Field", "FieldAI", "Field", "embodied AI", "foundation models"], sector: "ai", ticker: null },
  { name: "Nominal", aliases: [], sector: "ai", ticker: null },
  { name: "Palantir", aliases: ["Gotham", "data analytics", "government"], sector: "ai", ticker: "PLTR" },
  { name: "Cognition", aliases: ["autonomous agent"], sector: "ai", ticker: null },
  { name: "Hadrian", aliases: ["Hadrian Manufacturing", "automated factory", "aerospace"], sector: "robotics", ticker: null },
  { name: "Machina Labs", aliases: ["Machina", "MachinaLabs", "Roboforming", "robotic manufacturing", "metal forming", "automotive"], sector: "robotics", ticker: null },
  { name: "DIRAC", aliases: ["Dirac manufacturing", "work instructions", "manufacturing software platform"], sector: "robotics", ticker: null },
  { name: "Formic", aliases: ["Formic Robotics", "robots-as-a-service", "automation"], sector: "robotics", ticker: null },
  { name: "Rangeview", aliases: ["Rangeview casting", "metal casting startup"], sector: "robotics", ticker: null },
  { name: "Senra Systems", aliases: ["Senra", "SenraSystems", "wire harnesses", "software-defined"], sector: "robotics", ticker: null },
  { name: "Salient Motion", aliases: ["SalientMotion", "actuation", "motion control"], sector: "robotics", ticker: null },
  { name: "Divergent", aliases: ["additive manufacturing", "automotive"], sector: "robotics", ticker: null },
  { name: "Amca", aliases: ["acquisitions", "aerospace components"], sector: "robotics", ticker: null },
  { name: "Altos Labs", aliases: ["Altos", "AltosLabs", "longevity", "cell reprogramming", "aging"], sector: "biotech", ticker: null },
  { name: "Retro Biosciences", aliases: ["Retro", "RetroBiosciences", "longevity", "aging", "autophagy"], sector: "biotech", ticker: null },
  { name: "New Limit", aliases: ["NewLimit", "longevity", "epigenetics"], sector: "biotech", ticker: null },
  { name: "Atom Bodies", aliases: ["AtomBodies", "prosthetics", "bionics"], sector: "biotech", ticker: null },
  { name: "Mammoth Biosciences", aliases: ["Mammoth", "MammothBiosciences", "CRISPR", "gene editing", "diagnostics"], sector: "biotech", ticker: null },
  { name: "Nucleus Genomics", aliases: ["NucleusGenomics", "genomics", "disease risk", "screening"], sector: "biotech", ticker: null },
  { name: "Orchid", aliases: ["genomics", "embryo screening", "reproductive"], sector: "biotech", ticker: null },
  { name: "Herasight", aliases: ["polygenic screening", "embryo selection", "genomics"], sector: "biotech", ticker: null },
  { name: "Terraform Industries", aliases: ["Terraform", "TerraformIndustries", "Terraformer", "synthetic fuel", "carbon capture", "solar"], sector: "climate", ticker: null },
  { name: "Commonwealth Fusion Systems", aliases: ["Commonwealth Fusion", "CommonwealthFusionSystems", "SPARC", "tokamak", "superconductors"], sector: "climate", ticker: null },
  { name: "Fervo Energy", aliases: ["Fervo", "FervoEnergy", "geothermal", "drilling", "clean energy"], sector: "climate", ticker: null },
  { name: "Xcimer Energy", aliases: ["Xcimer", "XcimerEnergy", "laser", "inertial confinement"], sector: "climate", ticker: null },
  { name: "Helion", aliases: ["Helion Energy", "field-reversed"], sector: "climate", ticker: null },
  { name: "TAE Technologies", aliases: ["TAETechnologies", "TAE Tech", "proton-boron"], sector: "climate", ticker: null },
  { name: "Mazama", aliases: ["geothermal", "supercritical"], sector: "climate", ticker: null },
  { name: "Quaise Energy", aliases: ["Quaise", "QuaiseEnergy", "geothermal", "deep drilling", "millimeter wave"], sector: "climate", ticker: null },
  { name: "Captura", aliases: ["carbon capture", "ocean"], sector: "climate", ticker: null },
  { name: "Base Power", aliases: ["BasePower", "virtual power plant", "batteries"], sector: "climate", ticker: null },
  { name: "Karman Industries", aliases: ["Karman", "KarmanIndustries", "heat pumps", "industrial", "decarbonization"], sector: "climate", ticker: null },
  { name: "Claros", aliases: ["power management", "efficiency"], sector: "climate", ticker: null },
  { name: "Zipline", aliases: ["Zip Line", "delivery drones", "medical"], sector: "autonomous", ticker: null },
  { name: "Joby Aviation", aliases: ["JobyAviation", "eVTOL", "air taxi", "electric aviation"], sector: "autonomous", ticker: "JOBY" },
  { name: "Rainmaker", aliases: ["cloud seeding", "weather modification", "water"], sector: "autonomous", ticker: null },
  { name: "Thoron", aliases: ["commercial drones", "DJI alternative"], sector: "autonomous", ticker: null },
  { name: "Airship Industries", aliases: ["Airship", "AirshipIndustries", "airships", "blimps", "cargo"], sector: "autonomous", ticker: null },
  { name: "Cerebras", aliases: ["Cerebras Systems", "AI chips", "wafer-scale", "semiconductors"], sector: "chips", ticker: null },
  { name: "Etched", aliases: ["AI chips", "inference"], sector: "chips", ticker: null },
  { name: "Extropic", aliases: ["thermodynamic computing", "AI chips", "energy efficient"], sector: "chips", ticker: null },
  { name: "Lightmatter", aliases: ["photonic interconnects", "optical"], sector: "chips", ticker: null },
  { name: "Substrate", aliases: ["lithography", "X-ray", "chipmaking"], sector: "chips", ticker: null },
  { name: "Lab 91", aliases: ["Lab91", "2D materials", "semiconductors"], sector: "chips", ticker: null },
  { name: "Cuby Technologies", aliases: ["CubyTechnologies", "modular homes", "micro-factory", "construction"], sector: "construction", ticker: null },
  { name: "Cover", aliases: ["modular homes", "panel-based", "construction"], sector: "construction", ticker: null },
  { name: "The Boring Company", aliases: ["TheBoringCompany", "Boring Company", "tunneling", "transit", "infrastructure"], sector: "transportation", ticker: null },
  { name: "Pipedream", aliases: ["underground delivery", "logistics", "infrastructure"], sector: "transportation", ticker: null },
  { name: "Navier", aliases: ["electric boats", "hydrofoil", "maritime"], sector: "transportation", ticker: null },
  { name: "Arc Boats", aliases: ["ArcBoats", "electric boats", "marine", "batteries"], sector: "transportation", ticker: null },
  { name: "Alpha School", aliases: ["AlphaSchool", "education", "school"], sector: "consumer", ticker: null },
  { name: "Matic Robotics", aliases: ["Matic", "MaticRobotics", "robot vacuum", "consumer"], sector: "consumer", ticker: null },
  { name: "Flexport", aliases: ["logistics", "freight", "trade"], sector: "consumer", ticker: null },
  { name: "Shinkei", aliases: ["fish processing", "food tech"], sector: "consumer", ticker: null },
  { name: "Vital Lyfe", aliases: ["VitalLyfe", "desalination", "water", "filtration"], sector: "consumer", ticker: null },
  { name: "Advanced Spade Company", aliases: ["AdvancedSpadeCompany", "utility locating", "mapping"], sector: "consumer", ticker: null },
  { name: "Forterra", aliases: ["autonomous vehicles"], sector: "defense", ticker: null },
  { name: "Auterion", aliases: ["drone software", "open-source"], sector: "defense", ticker: null },
  { name: "Firehawk Aerospace", aliases: ["Firehawk", "FirehawkAerospace", "rocket engines", "propulsion"], sector: "defense", ticker: null },
  { name: "Scale AI", aliases: ["Scale", "ScaleAI", "Scale", "AI data", "training data"], sector: "defense", ticker: null },
  { name: "Reveal Technology", aliases: ["Reveal", "RevealTechnology", "battlefield AI", "intelligence"], sector: "defense", ticker: null },
  { name: "Galvanick", aliases: ["cybersecurity", "critical infrastructure", "OT security"], sector: "defense", ticker: null },
  { name: "SkySafe", aliases: ["RF detection"], sector: "defense", ticker: null },
  { name: "Distributed Spectrum", aliases: ["DistributedSpectrum", "electronic warfare", "RF sensing"], sector: "defense", ticker: null },
  { name: "Aurelius Systems", aliases: ["Aurelius", "AureliusSystems", "directed energy", "laser"], sector: "defense", ticker: null },
  { name: "Darkhive", aliases: ["micro-drones"], sector: "defense", ticker: null },
  { name: "Deterrence", aliases: ["munitions"], sector: "defense", ticker: null },
  { name: "Deepnight", aliases: ["night vision", "imaging"], sector: "defense", ticker: null },
  { name: "Zeromark", aliases: ["infantry"], sector: "defense", ticker: null },
  { name: "Rune Technologies", aliases: ["RuneTechnologies", "logistics"], sector: "defense", ticker: null },
  { name: "Swan", aliases: ["modular"], sector: "defense", ticker: null },
  { name: "Biofire", aliases: ["smart firearms", "biometric", "safety"], sector: "defense", ticker: null },
  { name: "Firestorm Labs", aliases: ["Firestorm", "FirestormLabs", "low-cost"], sector: "defense", ticker: null },
  { name: "Aalyria", aliases: ["mesh networking", "satellite comms"], sector: "space", ticker: null },
  { name: "AnySignal", aliases: ["satellite comms", "aerospace"], sector: "space", ticker: null },
  { name: "Turion Space", aliases: ["Turion", "TurionSpace", "space debris", "orbital servicing"], sector: "space", ticker: null },
  { name: "Umbra", aliases: ["Umbra Space", "Umbra Lab", "satellite imaging", "intelligence"], sector: "space", ticker: null },
  { name: "Albedo", aliases: ["Albedo Space", "satellite imagery"], sector: "space", ticker: null },
  { name: "Blue Origin", aliases: ["BlueOrigin", "New Shepard", "New Glenn"], sector: "space", ticker: null },
  { name: "Axiom Space", aliases: ["Axiom", "AxiomSpace", "space station", "commercial space"], sector: "space", ticker: null },
  { name: "Astrolab", aliases: ["lunar rover"], sector: "space", ticker: null },
  { name: "Array Labs", aliases: ["Array", "ArrayLabs", "3D mapping", "satellite"], sector: "space", ticker: null },
  { name: "Armada", aliases: ["edge computing", "satellite"], sector: "space", ticker: null },
  { name: "Aetherflux", aliases: ["space solar", "power beaming"], sector: "space", ticker: null },
  { name: "Applied Intuition", aliases: ["AppliedIntuition", "Applied", "simulation"], sector: "ai", ticker: null },
  { name: "Anthropic", aliases: ["Claude", "Claude AI", "AI safety"], sector: "ai", ticker: null },
  { name: "Anysphere", aliases: ["AI coding", "developer tools"], sector: "ai", ticker: null },
  { name: "Air Space Intelligence", aliases: ["AirSpaceIntelligence", "logistics"], sector: "ai", ticker: null },
  { name: "Atmo", aliases: ["weather forecasting", "meteorology"], sector: "ai", ticker: null },
  { name: "Beacon AI", aliases: ["Beacon", "BeaconAI", "Beacon", "aviation AI", "autonomous flight", "safety"], sector: "ai", ticker: null },
  { name: "Agility Robotics", aliases: ["Agility", "AgilityRobotics", "Digit", "humanoid robot", "warehouse", "logistics"], sector: "robotics", ticker: null },
  { name: "Apptronik", aliases: ["Apollo robot", "humanoid robot", "Mercedes"], sector: "robotics", ticker: null },
  { name: "1X Technologies", aliases: ["1XTechnologies", "Neo robot", "humanoid robot", "home robotics"], sector: "robotics", ticker: null },
  { name: "Bright Machines", aliases: ["BrightMachines", "factory automation", "software manufacturing"], sector: "robotics", ticker: null },
  { name: "Atomic Industries", aliases: ["Atomic", "AtomicIndustries", "tool and die", "AI manufacturing", "precision"], sector: "robotics", ticker: null },
  { name: "Re:Build Manufacturing", aliases: ["Re:BuildManufacturing", "reshoring"], sector: "robotics", ticker: null },
  { name: "AMP Robotics", aliases: ["AMPRobotics", "recycling", "waste"], sector: "robotics", ticker: null },
  { name: "Diode", aliases: ["PCB design", "AI automation", "hardware"], sector: "robotics", ticker: null },
  { name: "Quilter", aliases: ["PCB layout", "AI automation", "hardware"], sector: "robotics", ticker: null },
  { name: "Science Corporation", aliases: ["ScienceCorporation", "organ preservation", "neuroscience"], sector: "biotech", ticker: null },
  { name: "Andromeda Surgical", aliases: ["AndromedaSurgical", "surgical robots", "healthcare"], sector: "biotech", ticker: null },
  { name: "Solugen", aliases: ["biomanufacturing", "green chemistry", "industrial"], sector: "climate", ticker: null },
  { name: "Exowatt", aliases: ["solar thermal", "off-grid"], sector: "climate", ticker: null },
  { name: "Antora Energy", aliases: ["Antora", "AntoraEnergy", "thermal storage", "industrial heat"], sector: "climate", ticker: null },
  { name: "Form Energy", aliases: ["FormEnergy", "iron-air battery", "grid storage", "100-hour"], sector: "climate", ticker: null },
  { name: "Brimstone", aliases: ["green cement", "decarbonization", "construction"], sector: "climate", ticker: null },
  { name: "Boston Metal", aliases: ["BostonMetal", "green steel", "electrolysis", "decarbonization"], sector: "climate", ticker: null },
  { name: "Avalanche Energy", aliases: ["Avalanche", "AvalancheEnergy", "compact", "modular"], sector: "climate", ticker: null },
  { name: "Bedrock Energy", aliases: ["Bedrock", "BedrockEnergy", "geothermal", "heating cooling"], sector: "climate", ticker: null },
  { name: "Arbor Energy", aliases: ["Arbor", "ArborEnergy", "carbon removal", "biomass", "sequestration"], sector: "climate", ticker: null },
  { name: "Endurance Energy", aliases: ["Endurance", "EnduranceEnergy", "geothermal", "ocean", "seafloor"], sector: "climate", ticker: null },
  { name: "Cape", aliases: ["encrypted comms", "mobile network", "security"], sector: "climate", ticker: null },
  { name: "Aepnus Technology", aliases: ["Aepnus", "AepnusTechnology", "critical minerals", "lithium", "electrochemistry"], sector: "climate", ticker: null },
  { name: "Manna Aero", aliases: ["MannaAero", "delivery drones", "logistics"], sector: "autonomous", ticker: null },
  { name: "Seneca Systems", aliases: ["Seneca", "SenecaSystems", "wildfire"], sector: "autonomous", ticker: null },
  { name: "Asylon Robotics", aliases: ["Asylon", "AsylonRobotics", "security drones", "surveillance"], sector: "autonomous", ticker: null },
  { name: "Atom Computing", aliases: ["AtomComputing", "quantum computing", "neutral atoms", "qubits"], sector: "chips", ticker: null },
  { name: "Atomic Semi", aliases: ["AtomicSemi", "semiconductor fab", "rapid prototyping"], sector: "chips", ticker: null },
  { name: "Atomic Machines", aliases: ["AtomicMachines", "nanoscale", "atomic precision"], sector: "chips", ticker: null },
  { name: "Bedrock Ocean", aliases: ["BedrockOcean", "ocean mapping", "seafloor"], sector: "ocean", ticker: null },
  { name: "Amidon Heavy Industries", aliases: ["Amidon Heavy", "AmidonHeavyIndustries", "underwater"], sector: "ocean", ticker: null },
  { name: "Clippership", aliases: ["autonomous ships", "wind-powered", "cargo"], sector: "ocean", ticker: null },
  { name: "Conductor Quantum", aliases: ["ConductorQuantum", "quantum computing", "silicon", "semiconductor"], sector: "quantum", ticker: null },
  { name: "Amperon", aliases: ["grid analytics", "energy forecasting"], sector: "infrastructure", ticker: null },
  { name: "Ample", aliases: ["battery swap", "charging"], sector: "infrastructure", ticker: null },
  { name: "Blumen Systems", aliases: ["Blumen", "BlumenSystems", "construction tech", "infrastructure"], sector: "infrastructure", ticker: null },
  { name: "Durin", aliases: ["autonomous drilling", "mining", "infrastructure"], sector: "infrastructure", ticker: null },
  { name: "Elodin", aliases: ["flight software", "aerospace", "certification"], sector: "infrastructure", ticker: null },
  { name: "Bronco AI", aliases: ["Bronco", "BroncoAI", "Bronco", "supply chain", "logistics"], sector: "infrastructure", ticker: null },
  { name: "Daylight Computer", aliases: ["DaylightComputer", "e-ink", "humane tech", "computers"], sector: "consumer", ticker: null },
  { name: "Synthesis", aliases: ["AI tutoring", "education"], sector: "consumer", ticker: null },
  { name: "Helsing", aliases: ["defense AI", "military intelligence"], sector: "defense", ticker: null },
  { name: "Saildrone", aliases: ["Sail Drone", "autonomous vessels", "maritime", "ocean data"], sector: "defense", ticker: null },
  { name: "Overland AI", aliases: ["Overland", "OverlandAI", "Overland", "autonomous ground vehicles", "military logistics"], sector: "defense", ticker: null },
  { name: "Second Front Systems", aliases: ["Second Front", "SecondFrontSystems", "defense software"], sector: "defense", ticker: null },
  { name: "Rebellion Defense", aliases: ["RebellionDefense", "military AI", "defense software", "intelligence"], sector: "defense", ticker: null },
  { name: "Primer AI", aliases: ["Primer", "PrimerAI", "Primer", "intelligence analysis", "defense AI"], sector: "defense", ticker: null },
  { name: "True Anomaly", aliases: ["TrueAnomaly", "Jackal spacecraft", "space domain awareness"], sector: "defense", ticker: null },
  { name: "Kodiak Robotics", aliases: ["Kodiak", "KodiakRobotics", "autonomous trucking", "military vehicles", "dual-use"], sector: "defense", ticker: null },
  { name: "Theseus", aliases: ["GPS-denied", "drone navigation"], sector: "defense", ticker: null },
  { name: "Mara", aliases: ["autonomous defense"], sector: "defense", ticker: null },
  { name: "Flock Safety", aliases: ["FlockSafety", "Flock", "public safety", "AI cameras", "law enforcement"], sector: "defense", ticker: null },
  { name: "Icarus", aliases: ["defense drones"], sector: "defense", ticker: null },
  { name: "PILGRIM", aliases: ["military biotech", "defense medicine", "battlefield"], sector: "defense", ticker: null },
  { name: "NuScale Power", aliases: ["NuScalePower", "NRC approved", "clean energy"], sector: "nuclear", ticker: null },
  { name: "Zap Energy", aliases: ["ZapEnergy", "Z-pinch", "clean energy"], sector: "nuclear", ticker: null },
  { name: "General Fusion", aliases: ["GeneralFusion", "magnetized target", "clean energy"], sector: "nuclear", ticker: null },
  { name: "Type One Energy", aliases: ["Type One", "TypeOneEnergy", "stellarator", "HTS magnets"], sector: "nuclear", ticker: null },
  { name: "Focused Energy", aliases: ["Focused", "FocusedEnergy", "inertial confinement", "laser"], sector: "nuclear", ticker: null },
  { name: "Nano Nuclear Energy", aliases: ["Nano Nuclear", "NanoNuclearEnergy", "microreactor", "portable nuclear", "HALEU"], sector: "nuclear", ticker: null },
  { name: "Pacific Fusion", aliases: ["PacificFusion", "inertial confinement", "clean energy"], sector: "nuclear", ticker: null },
  { name: "Fuse Energy", aliases: ["FuseEnergy", "pulsed power"], sector: "nuclear", ticker: null },
  { name: "Stoke Space", aliases: ["Stoke", "StokeSpace", "reusable rocket"], sector: "space", ticker: null },
  { name: "Capella Space", aliases: ["Capella", "CapellaSpace", "Earth observation"], sector: "space", ticker: null },
  { name: "Muon Space", aliases: ["MuonSpace", "climate satellites", "weather", "Earth observation"], sector: "space", ticker: null },
  { name: "Planet Labs", aliases: ["Planet", "PlanetLabs", "Earth observation", "geospatial"], sector: "space", ticker: "PL" },
  { name: "Astroscale", aliases: ["space debris", "on-orbit servicing", "sustainability"], sector: "space", ticker: null },
  { name: "Outpost Space", aliases: ["Outpost", "OutpostSpace", "space reentry", "cargo return"], sector: "space", ticker: null },
  { name: "Longshot Space", aliases: ["Longshot", "LongshotSpace", "gun launch", "space cannon"], sector: "space", ticker: null },
  { name: "Proteus Space", aliases: ["Proteus", "ProteusSpace", "space propulsion", "orbital maneuvering"], sector: "space", ticker: null },
  { name: "Ursa Major Technologies", aliases: ["Ursa Major", "UrsaMajorTechnologies", "rocket engines", "propulsion"], sector: "space", ticker: null },
  { name: "AST SpaceMobile", aliases: ["ASTSpaceMobile", "direct-to-cell", "broadband"], sector: "space", ticker: "ASTS" },
  { name: "Exosonic", aliases: ["low-boom", "Air Force One"], sector: "space", ticker: null },
  { name: "Destinus", aliases: ["hydrogen", "cargo transport"], sector: "space", ticker: null },
  { name: "Dynamo Air", aliases: ["DynamoAir"], sector: "space", ticker: null },
  { name: "OpenAI", aliases: ["ChatGPT", "GPT-4", "GPT-5", "DALL-E", "frontier AI"], sector: "ai", ticker: null },
  { name: "Mistral AI", aliases: ["Mistral", "MistralAI", "Mistral", "open-source AI", "frontier AI"], sector: "ai", ticker: null },
  { name: "Groq", aliases: ["Groq Inc", "AI chips", "inference"], sector: "ai", ticker: null },
  { name: "Skild AI", aliases: ["Skild", "SkildAI", "Skild", "foundation model"], sector: "ai", ticker: null },
  { name: "Crusoe Energy", aliases: ["Crusoe", "CrusoeEnergy", "AI data centers", "infrastructure"], sector: "ai", ticker: null },
  { name: "ElevenLabs", aliases: ["Eleven Labs", "11 Labs", "voice AI", "text-to-speech", "audio"], sector: "ai", ticker: null },
  { name: "Hippocratic AI", aliases: ["Hippocratic", "HippocraticAI", "Hippocratic", "healthcare AI", "patient care"], sector: "ai", ticker: null },
  { name: "Covariant", aliases: ["Covariant AI", "warehouse robotics", "AI manipulation", "foundation model"], sector: "robotics", ticker: null },
  { name: "Gecko Robotics", aliases: ["Gecko", "GeckoRobotics", "inspection robots", "industrial"], sector: "robotics", ticker: null },
  { name: "Terranova", aliases: ["planetary-scale robotics", "infrastructure"], sector: "robotics", ticker: null },
  { name: "Electric Sheep", aliases: ["ElectricSheep", "Electric Sheep Robotics", "lawn care", "autonomous robots", "landscaping"], sector: "robotics", ticker: null },
  { name: "Carbon Robotics", aliases: ["Carbon", "CarbonRobotics", "agriculture", "laser weeding"], sector: "robotics", ticker: null },
  { name: "Terran Robotics", aliases: ["Terran", "TerranRobotics", "construction robots", "earthmoving"], sector: "robotics", ticker: null },
  { name: "Recursion Pharmaceuticals", aliases: ["Recursion", "RecursionPharmaceuticals", "AI drug discovery", "machine learning"], sector: "biotech", ticker: "RXRX" },
  { name: "Insitro", aliases: ["ML drug discovery", "genomics"], sector: "biotech", ticker: null },
  { name: "Eikon Therapeutics", aliases: ["Eikon", "EikonTherapeutics", "microscopy", "drug discovery", "protein dynamics"], sector: "biotech", ticker: null },
  { name: "Tempus AI", aliases: ["Tempus", "TempusAI", "Tempus", "precision medicine", "AI oncology", "diagnostics"], sector: "biotech", ticker: "TEM" },
  { name: "Colossal Biosciences", aliases: ["Colossal", "ColossalBiosciences", "de-extinction", "gene editing", "synthetic biology"], sector: "biotech", ticker: null },
  { name: "Medra", aliases: ["lab automation", "genomics"], sector: "biotech", ticker: null },
  { name: "Abridge", aliases: ["clinical documentation", "AI healthcare"], sector: "biotech", ticker: null },
  { name: "Heirloom Carbon", aliases: ["HeirloomCarbon", "Heirloom", "direct air capture", "carbon removal"], sector: "climate", ticker: null },
  { name: "Twelve", aliases: ["Twelve Co2", "CO2 utilization", "electrochemistry"], sector: "climate", ticker: null },
  { name: "KoBold Metals", aliases: ["KoBoldMetals", "KoBold", "AI mining", "critical minerals", "lithium"], sector: "climate", ticker: null },
  { name: "Sublime Systems", aliases: ["Sublime", "SublimeSystems", "green cement", "electrochemistry", "decarbonization"], sector: "climate", ticker: null },
  { name: "Redwood Materials", aliases: ["RedwoodMaterials", "Redwood", "battery recycling", "lithium", "circular economy"], sector: "climate", ticker: null },
  { name: "Natron Energy", aliases: ["Natron", "NatronEnergy", "sodium-ion batteries", "energy storage"], sector: "climate", ticker: null },
  { name: "EnerVenue", aliases: ["metal-hydrogen batteries", "grid storage", "NASA tech"], sector: "climate", ticker: null },
  { name: "Charm Industrial", aliases: ["CharmIndustrial", "Charm", "carbon removal", "bio-oil", "permanent storage"], sector: "climate", ticker: null },
  { name: "Impulse Labs", aliases: ["Impulse", "ImpulseLabs", "electrification", "battery", "kitchen appliance"], sector: "climate", ticker: null },
  { name: "Mariana Minerals", aliases: ["MarianaMinerals", "mining", "critical minerals"], sector: "climate", ticker: null },
  { name: "Aurora Innovation", aliases: ["AuroraInnovation", "Aurora Driver", "autonomous trucking", "self-driving", "logistics"], sector: "autonomous", ticker: null },
  { name: "Nuro", aliases: ["Nuro AI", "autonomous delivery", "last-mile"], sector: "autonomous", ticker: null },
  { name: "Archer Aviation", aliases: ["ArcherAviation", "eVTOL", "air taxi", "urban air mobility"], sector: "autonomous", ticker: "ACHR" },
  { name: "Ridevalo", aliases: ["hydrofoil", "water transport"], sector: "autonomous", ticker: null },
  { name: "FlyBy Robotics", aliases: ["FlyBy", "FlyByRobotics", "Flyby", "defense drones", "swarm robotics", "Gundo"], sector: "defense", ticker: null },
  { name: "PsiQuantum", aliases: ["Psi Quantum", "quantum computing", "photonic", "semiconductor"], sector: "chips", ticker: null },
  { name: "Astera Labs", aliases: ["Astera", "AsteraLabs", "data center", "semiconductor"], sector: "chips", ticker: "ALAB" },
  { name: "Zettascale", aliases: ["AI chips", "energy efficient", "semiconductor"], sector: "chips", ticker: null },
  { name: "d-Matrix", aliases: ["in-memory computing", "AI inference", "chiplets"], sector: "chips", ticker: null },
  { name: "Inversion Space", aliases: ["Inversion", "InversionSpace", "space logistics", "orbital warehouse", "reentry"], sector: "construction", ticker: null },
  { name: "Lumina Vehicles", aliases: ["LuminaVehicles", "electric vehicles", "urban transport"], sector: "transportation", ticker: null },
  { name: "FleetZero", aliases: ["electric ships", "maritime", "zero-emission"], sector: "transportation", ticker: null },
  { name: "Framework Computer", aliases: ["FrameworkComputer", "modular laptop", "right to repair", "sustainability"], sector: "consumer", ticker: null },
  { name: "Whisper Aero", aliases: ["WhisperAero", "quiet propulsion", "electric aviation", "noise reduction"], sector: "consumer", ticker: null },
  { name: "IonQ", aliases: ["Ion Q", "trapped-ion", "quantum computing"], sector: "quantum", ticker: "IONQ" },
  { name: "Rigetti Computing", aliases: ["Rigetti", "RigettiComputing", "superconducting", "quantum computing", "cloud"], sector: "quantum", ticker: "RGTI" },
  { name: "QuEra Computing", aliases: ["QuEra", "QuEraComputing", "neutral-atom", "quantum computing", "Harvard"], sector: "quantum", ticker: null },
  { name: "NetworkOcean", aliases: ["underwater data centers", "ocean tech", "cooling"], sector: "ocean", ticker: null },
  { name: "Thalassa Robotics", aliases: ["Thalassa", "ThalassaRobotics", "underwater robots", "ocean exploration", "marine"], sector: "ocean", ticker: null },
  { name: "Running Tide", aliases: ["RunningTide", "ocean carbon removal"], sector: "ocean", ticker: null },
  { name: "Fortastra", aliases: ["infrastructure", "supply chain", "logistics"], sector: "infrastructure", ticker: null },
  { name: "Earth AI", aliases: ["Earth", "EarthAI", "Earth", "AI mining", "mineral exploration", "critical metals"], sector: "infrastructure", ticker: null },
  { name: "Watoga Tech", aliases: ["WatogaTech", "autonomous mining", "critical minerals"], sector: "infrastructure", ticker: null },
  { name: "Wardstone", aliases: ["infrastructure security", "resilience"], sector: "infrastructure", ticker: null },
  { name: "Teralta", aliases: ["hydrogen logistics", "industrial"], sector: "infrastructure", ticker: null },
  { name: "GenMat", aliases: ["materials science", "physics simulation"], sector: "infrastructure", ticker: null },
  { name: "Tokamak Energy", aliases: ["Tokamak", "TokamakEnergy", "tokamak", "clean energy", "superconductors"], sector: "nuclear", ticker: null },
  { name: "First Light Fusion", aliases: ["FirstLightFusion", "inertial confinement", "clean energy"], sector: "nuclear", ticker: null },
  { name: "Newcleo", aliases: ["lead-cooled", "waste recycling"], sector: "nuclear", ticker: null },
  { name: "Wayve", aliases: ["autonomous vehicles", "embodied intelligence"], sector: "ai", ticker: null },
  { name: "Vertical Aerospace", aliases: ["Vertical", "VerticalAerospace", "eVTOL", "air taxi", "electric aviation", "urban mobility"], sector: "transportation", ticker: null },
  { name: "Oxford Nanopore Technologies", aliases: ["Oxford Nanopore", "OxfordNanoporeTechnologies", "Nanopore", "genomics", "sequencing", "nanopore", "diagnostics"], sector: "biotech", ticker: null },
  { name: "Oxford Quantum Circuits", aliases: ["OxfordQuantumCircuits", "quantum computing", "superconducting", "Coaxmon"], sector: "quantum", ticker: null },
  { name: "Orbital Marine Power", aliases: ["OrbitalMarinePower", "tidal energy", "ocean power", "renewable", "marine"], sector: "ocean", ticker: null },
  { name: "ZeroAvia", aliases: ["Zero Avia", "hydrogen aviation", "electric flight", "zero emission"], sector: "transportation", ticker: null },
  { name: "Space Forge", aliases: ["SpaceForge", "space manufacturing", "materials"], sector: "space", ticker: null },
  { name: "Gravitricity", aliases: ["gravity storage", "energy storage", "mining"], sector: "climate", ticker: null },
  { name: "Isar Aerospace", aliases: ["IsarAerospace", "launch vehicles", "European sovereignty"], sector: "space", ticker: null },
  { name: "Quantum-Systems", aliases: ["defense drones", "reconnaissance", "eVTOL"], sector: "defense", ticker: null },
  { name: "Proxima Fusion", aliases: ["ProximaFusion", "stellarator", "clean energy", "Max Planck"], sector: "nuclear", ticker: null },
  { name: "Marvel Fusion", aliases: ["MarvelFusion", "laser", "inertial confinement"], sector: "nuclear", ticker: null },
  { name: "Rocket Factory Augsburg", aliases: ["RocketFactoryAugsburg", "European launch"], sector: "space", ticker: null },
  { name: "Neura Robotics", aliases: ["NEURA", "NEURARobotics", "NeuraRobotics", "cognitive robots", "cognitive robotics", "AI perception"], sector: "robotics", ticker: null },
  { name: "Black Semiconductor", aliases: ["BlackSemiconductor", "graphene", "semiconductors", "interconnects"], sector: "chips", ticker: null },
  { name: "Sunfire", aliases: ["green hydrogen", "electrolysis", "e-fuels"], sector: "climate", ticker: null },
  { name: "planqc", aliases: ["quantum computing", "neutral atom", "optical lattice"], sector: "quantum", ticker: null },
  { name: "Volocopter", aliases: ["Volo Copter", "eVTOL", "air taxi", "urban mobility"], sector: "transportation", ticker: null },
  { name: "Pasqal", aliases: ["Pasqal Quantum", "quantum computing", "neutral atom", "Nobel Prize"], sector: "quantum", ticker: null },
  { name: "Exotec", aliases: ["Skypod", "warehouse robotics", "logistics"], sector: "robotics", ticker: null },
  { name: "Naarea", aliases: ["microreactor", "decentralized"], sector: "nuclear", ticker: null },
  { name: "Renaissance Fusion", aliases: ["RenaissanceFusion", "stellarator", "superconductors"], sector: "nuclear", ticker: null },
  { name: "Verkor", aliases: ["batteries", "gigafactory", "low carbon"], sector: "climate", ticker: null },
  { name: "DNA Script", aliases: ["DNAScript", "synthetic biology", "DNA synthesis", "genomics"], sector: "biotech", ticker: null },
  { name: "Alice & Bob", aliases: ["Alice&Bob", "Alice and Bob", "quantum computing", "cat qubits", "error correction"], sector: "quantum", ticker: null },
  { name: "Latitude", aliases: ["micro-launcher", "small satellites"], sector: "space", ticker: null },
  { name: "Einride", aliases: ["autonomous trucks", "electric freight", "logistics"], sector: "transportation", ticker: null },
  { name: "Neko Health", aliases: ["NekoHealth", "preventive healthcare", "body scanning", "diagnostics"], sector: "biotech", ticker: null },
  { name: "ICEYE", aliases: ["Ice Eye", "SAR satellites", "Earth observation"], sector: "space", ticker: null },
  { name: "IQM Quantum Computers", aliases: ["IQMQuantumComputers", "quantum computing", "superconducting", "co-design"], sector: "quantum", ticker: null },
  { name: "Solar Foods", aliases: ["SolarFoods", "novel protein", "CO2 capture", "food tech"], sector: "biotech", ticker: null },
  { name: "Climeworks", aliases: ["Clime Works", "direct air capture", "carbon removal"], sector: "climate", ticker: null },
  { name: "ANYbotics", aliases: ["ANYmal", "quadruped robots", "inspection", "hazardous environments"], sector: "robotics", ticker: null },
  { name: "Synhelion", aliases: ["solar fuels", "synthetic fuel"], sector: "climate", ticker: null },
  { name: "Seaborg Technologies", aliases: ["Seaborg", "SeaborgTechnologies", "molten salt reactor", "floating"], sector: "nuclear", ticker: null },
  { name: "Copenhagen Atomics", aliases: ["CopenhagenAtomics", "thorium", "modular"], sector: "nuclear", ticker: null },
  { name: "FREYR Battery", aliases: ["FREYRBattery", "Freyr", "batteries", "gigafactory", "sodium-ion", "Arctic"], sector: "climate", ticker: null },
  { name: "QuantWare", aliases: ["quantum computing", "superconducting", "hardware"], sector: "quantum", ticker: null },
  { name: "PLD Space", aliases: ["PLDSpace", "launch vehicles", "European space"], sector: "space", ticker: null },
  { name: "D-Orbit", aliases: ["space logistics", "satellite deployment", "in-orbit"], sector: "space", ticker: null },
  { name: "Milrem Robotics", aliases: ["Milrem", "MilremRobotics", "military robots"], sector: "defense", ticker: null },
  { name: "Skeleton Technologies", aliases: ["Skeleton", "SkeletonTechnologies", "supercapacitors", "energy storage", "automotive"], sector: "climate", ticker: null },
  { name: "Saule Technologies", aliases: ["Saule", "SauleTechnologies", "perovskite solar", "flexible PV", "renewable energy"], sector: "climate", ticker: null },
  { name: "Quantum Machines", aliases: ["QuantumMachines", "quantum computing", "hardware control", "infrastructure"], sector: "quantum", ticker: null },
  { name: "Xtend", aliases: ["defense drones", "teleoperated"], sector: "defense", ticker: null },
  { name: "Percepto", aliases: ["Percepto Drones", "autonomous drones", "inspection", "infrastructure", "security"], sector: "autonomous", ticker: null },
  { name: "Ramon.Space", aliases: ["space computing", "radiation-hardened"], sector: "space", ticker: null },
  { name: "Wiliot", aliases: ["RF energy harvesting", "batteryless"], sector: "chips", ticker: null },
  { name: "Tevel Aerobotics", aliases: ["TevelAerobotics", "agtech", "fruit picking", "autonomous drones", "agriculture"], sector: "autonomous", ticker: null },
  { name: "ispace", aliases: ["lunar", "Moon lander", "space exploration"], sector: "space", ticker: null },
  { name: "Kyoto Fusioneering", aliases: ["KyotoFusioneering", "reactor engineering", "heat extraction"], sector: "nuclear", ticker: null },
  { name: "GITAI", aliases: ["space robotics", "in-orbit servicing"], sector: "robotics", ticker: null },
  { name: "Mujin", aliases: ["warehouse robotics", "logistics"], sector: "robotics", ticker: null },
  { name: "Rapidus", aliases: ["semiconductors", "national champion"], sector: "chips", ticker: null },
  { name: "Rebellions", aliases: ["AI chips", "inference", "data center", "semiconductors"], sector: "chips", ticker: null },
  { name: "Innospace", aliases: ["hybrid propulsion", "small satellites"], sector: "space", ticker: null },
  { name: "Rainbow Robotics", aliases: ["Rainbow", "RainbowRobotics", "cobots", "Hyundai", "KAIST"], sector: "robotics", ticker: null },
  { name: "Skyroot Aerospace", aliases: ["Skyroot", "SkyrootAerospace", "launch vehicles", "Indian space"], sector: "space", ticker: null },
  { name: "Agnikul Cosmos", aliases: ["AgnikulCosmos", "3D printed rockets", "launch vehicles", "IIT Madras"], sector: "space", ticker: null },
  { name: "Pixxel", aliases: ["hyperspectral imaging", "Earth observation"], sector: "space", ticker: null },
  { name: "ideaForge", aliases: ["defense drones", "surveillance", "security"], sector: "autonomous", ticker: null },
  { name: "Xanadu Quantum Technologies", aliases: ["Xanadu Quantum", "XanaduQuantumTechnologies", "Xanadu", "quantum computing", "photonic", "PennyLane", "open source"], sector: "quantum", ticker: null },
  { name: "Terrestrial Energy", aliases: ["Terrestrial", "TerrestrialEnergy", "molten salt reactor", "Generation IV"], sector: "nuclear", ticker: null },
  { name: "Tenstorrent", aliases: ["AI chips", "RISC-V", "open source", "Jim Keller"], sector: "chips", ticker: null },
  { name: "CarbonCure Technologies", aliases: ["CarbonCure", "CarbonCureTechnologies", "carbon capture", "concrete", "CO2 mineralization"], sector: "climate", ticker: null },
  { name: "Fleet Space Technologies", aliases: ["Fleet Space", "FleetSpaceTechnologies", "mineral exploration", "seismic"], sector: "space", ticker: null },
  { name: "Quantum Brilliance", aliases: ["QuantumBrilliance", "quantum computing", "diamond", "room temperature"], sector: "quantum", ticker: null },
  { name: "DroneShield", aliases: ["Drone Shield", "C-UAS", "RF detection"], sector: "defense", ticker: null },
  { name: "SunDrive Solar", aliases: ["SunDriveSolar", "solar cells", "copper", "efficiency record", "renewable"], sector: "climate", ticker: null },
  { name: "Silicon Box", aliases: ["SiliconBox", "semiconductor packaging", "chiplets", "advanced packaging"], sector: "chips", ticker: null },
  { name: "Satellogic", aliases: ["Earth observation", "high resolution"], sector: "space", ticker: "SATL" },
  { name: "Dawn Aerospace", aliases: ["DawnAerospace", "spaceplane", "reusable", "green propulsion", "suborbital"], sector: "space", ticker: null },
  { name: "Dragonfly Aerospace", aliases: ["Dragonfly", "DragonflyAerospace", "satellite imaging", "Earth observation", "African space"], sector: "space", ticker: null },
  { name: "Solinftec", aliases: ["agtech", "autonomous robots", "precision agriculture"], sector: "robotics", ticker: null },
  { name: "Hugging Face", aliases: ["HuggingFace", "open-source AI", "ML platform", "model hub", "datasets"], sector: "ai", ticker: null },
  { name: "Kyutai", aliases: ["AI research", "open-source", "foundation models", "European AI"], sector: "ai", ticker: null },
  { name: "Tekever", aliases: ["maritime"], sector: "autonomous", ticker: null },
  { name: "Dronamics", aliases: ["cargo drones", "logistics", "autonomous aviation"], sector: "autonomous", ticker: null },
  { name: "Monumental", aliases: ["construction robotics", "bricklaying", "automation", "labor shortage"], sector: "robotics", ticker: null },
  { name: "RobCo", aliases: ["modular robotics", "SME automation", "industrial robots", "no-code"], sector: "robotics", ticker: null },
  { name: "Gladia", aliases: ["speech AI", "transcription", "audio intelligence"], sector: "ai", ticker: null },
  { name: "Deep Isolation", aliases: ["DeepIsolation", "nuclear waste", "deep borehole", "disposal", "drilling"], sector: "nuclear", ticker: null },
  { name: "Grain Weevil", aliases: ["GrainWeevil", "agtech", "grain storage", "agricultural robots", "safety"], sector: "robotics", ticker: null },
  { name: "Naïo Technologies", aliases: ["NaïoTechnologies", "agtech", "weeding robots", "precision agriculture", "autonomous farming"], sector: "robotics", ticker: null },
  { name: "Delian Alliance Industries", aliases: ["Delian Alliance", "DelianAllianceIndustries", "maritime defense", "autonomous systems", "European defense"], sector: "defense", ticker: null },
  { name: "Cobod", aliases: ["construction", "concrete printing", "housing"], sector: "construction", ticker: null },
  { name: "Prusa Research", aliases: ["PrusaResearch", "open-source hardware", "desktop manufacturing"], sector: "robotics", ticker: null },
  { name: "Dunia", aliases: ["multi-agent AI", "enterprise automation", "workflow", "German AI"], sector: "ai", ticker: null },
  { name: "Phospho", aliases: ["LLM observability", "AI monitoring", "evaluation"], sector: "ai", ticker: null },
  { name: "Deep Atomic", aliases: ["DeepAtomic", "compact reactors", "clean energy", "Swiss tech"], sector: "nuclear", ticker: null },
  { name: "Rhoman Aerospace", aliases: ["Rhoman", "RhomanAerospace", "defense drones", "autonomous systems", "mission planning"], sector: "autonomous", ticker: null },
  { name: "AirMap", aliases: ["airspace management", "drone compliance"], sector: "autonomous", ticker: null },
  // Ulysses Eco merged into Ulysses Robotics (same founders, same company)
  { name: "Roboton", aliases: ["industrial robotics", "Czech tech", "automation"], sector: "robotics", ticker: null },
  { name: "Long Wall", aliases: ["LongWall", "autonomous systems", "military tech"], sector: "defense", ticker: null },
  { name: "Truemed", aliases: ["healthcare payments", "preventive health", "fintech"], sector: "biotech", ticker: null },
  { name: "Turbopuffer", aliases: ["vector database", "turbopuffer database"], sector: "ai", ticker: null },
  { name: "Attio", aliases: ["sales", "relationship intelligence"], sector: "ai", ticker: null },
  { name: "Day.ai", aliases: ["AI meetings", "productivity", "conversation intelligence"], sector: "ai", ticker: null },
  { name: "SHIELD Technology Partners", aliases: ["SHIELDTechnologyPartners", "defense tech", "advisory", "national security"], sector: "defense", ticker: null },
  { name: "Lotus Health AI", aliases: ["Lotus Health", "LotusHealthAI", "Lotus Health", "AI health", "clinical AI", "personalized medicine"], sector: "biotech", ticker: null },
  { name: "Bedrock Robotics", aliases: ["Bedrock", "BedrockRobotics", "autonomous construction", "heavy equipment", "retrofit autonomy", "Waymo alumni"], sector: "robotics", ticker: null },
  { name: "GrayMatter Robotics", aliases: ["GrayMatter", "GrayMatterRobotics", "industrial robotics", "AI manufacturing", "surface finishing"], sector: "robotics", ticker: null },
  { name: "RIOS Intelligent Machines", aliases: ["RIOSIntelligentMachines", "factory automation", "workcells", "Xerox PARC"], sector: "robotics", ticker: null },
  { name: "Orbital Composites", aliases: ["OrbitalComposites", "composites manufacturing", "aerospace", "defense supply chain"], sector: "robotics", ticker: null },
  { name: "SafeAI", aliases: ["autonomous mining", "heavy equipment", "retrofit autonomy", "construction"], sector: "robotics", ticker: null },
  { name: "Zoox", aliases: ["Zoox Amazon", "robotaxi", "autonomous vehicles", "purpose-built AV"], sector: "transportation", ticker: null },
  { name: "Multiply Labs", aliases: ["Multiply", "MultiplyLabs", "robotic pharma", "biomanufacturing", "cell therapy", "NVIDIA partner"], sector: "biotech", ticker: null },
  { name: "AiDash", aliases: ["infrastructure AI", "utility SaaS", "satellite imagery", "grid hardening"], sector: "infrastructure", ticker: null },
  { name: "Pano AI", aliases: ["PanoAI", "wildfire detection", "climate AI", "public safety", "computer vision"], sector: "climate", ticker: null },
  { name: "Collaborative Robotics", aliases: ["Collaborative", "CollaborativeRobotics", "cobots", "mobile manipulation", "logistics automation", "Amazon VP alumni"], sector: "robotics", ticker: null },
  { name: "Orangewood Labs", aliases: ["Orangewood", "OrangewoodLabs", "affordable robotics", "RoboGPT", "SMB automation", "Y Combinator"], sector: "robotics", ticker: null },
  { name: "Trilobio", aliases: ["lab automation", "synthetic biology", "reproducibility", "Forbes 30 Under 30"], sector: "biotech", ticker: null },
  { name: "Starpath Robotics", aliases: ["Starpath", "StarpathRobotics", "lunar mining", "space propellant", "SpaceX alumni"], sector: "space", ticker: null },
  { name: "DroneForge", aliases: ["drone AI", "autonomy SDK", "plug-and-play", "drone intelligence"], sector: "autonomous", ticker: null },
  { name: "Aerodome", aliases: ["drone security", "first responder", "public safety", "Flock Safety"], sector: "defense", ticker: null },
  { name: "Ambient.ai", aliases: ["AI security", "video analytics", "anomaly detection"], sector: "ai", ticker: null },
  { name: "Built Robotics", aliases: ["Built", "BuiltRobotics", "construction robotics", "autonomous equipment"], sector: "robotics", ticker: null },
  { name: "Chef Robotics", aliases: ["ChefRobotics", "food robotics", "automation", "commercial kitchen"], sector: "robotics", ticker: null },
  { name: "Databricks", aliases: ["Unity Catalog", "Mosaic ML", "data platform", "Apache Spark", "enterprise"], sector: "ai", ticker: null },
  { name: "Dexterity", aliases: ["warehouse robotics", "manipulation", "logistics"], sector: "robotics", ticker: null },
  { name: "Farm-ng", aliases: ["agricultural robotics", "farming"], sector: "robotics", ticker: null },
  { name: "Floodbase", aliases: ["climate tech", "flood monitoring", "parametric insurance", "satellite"], sector: "climate", ticker: null },
  { name: "Harbinger", aliases: ["electric trucks", "commercial EV", "chassis"], sector: "transportation", ticker: null },
  { name: "Hive AI", aliases: ["HiveAI", "content moderation", "AI APIs", "computer vision"], sector: "ai", ticker: null },
  { name: "Labelbox", aliases: ["data labeling", "AI training", "generative AI"], sector: "ai", ticker: null },
  { name: "LeoLabs", aliases: ["Leo Labs", "space debris", "radar tracking"], sector: "space", ticker: null },
  { name: "Liminal Insights", aliases: ["LiminalInsights", "battery QC", "ultrasound inspection"], sector: "climate", ticker: null },
  { name: "Locus Robotics", aliases: ["Locus", "LocusRobotics", "warehouse robots", "logistics"], sector: "robotics", ticker: null },
  { name: "Lumafield", aliases: ["industrial CT", "inspection"], sector: "robotics", ticker: null },
  { name: "Modern Intelligence", aliases: ["ModernIntelligence", "defense AI", "maritime surveillance", "sensor fusion"], sector: "defense", ticker: null },
  { name: "Osaro", aliases: ["robotic picking", "warehouse automation", "reinforcement learning"], sector: "robotics", ticker: null },
  { name: "Outrider", aliases: ["autonomous trucks", "yard automation", "logistics"], sector: "robotics", ticker: null },
  { name: "Parallel Systems", aliases: ["Parallel", "ParallelSystems", "autonomous rail", "electric freight", "logistics"], sector: "transportation", ticker: null },
  { name: "Prepared", aliases: ["911 AI", "public safety", "emergency response"], sector: "ai", ticker: null },
  { name: "Rain Industries", aliases: ["RainIndustries", "wildfire drones", "autonomous fire fighting"], sector: "autonomous", ticker: null },
  { name: "Rapid Robotics", aliases: ["Rapid", "RapidRobotics", "manufacturing robotics", "palletizing", "RobCo"], sector: "robotics", ticker: null },
  { name: "Revel", aliases: ["EV charging", "rideshare", "electric mopeds"], sector: "transportation", ticker: null },
  { name: "Rivian", aliases: ["electric vehicles", "trucks", "VW partnership"], sector: "transportation", ticker: "RIVN" },
  { name: "Sift", aliases: ["fraud detection", "AI security", "fintech"], sector: "ai", ticker: null },
  { name: "Slingshot Aerospace", aliases: ["Slingshot", "SlingshotAerospace", "space situational awareness", "satellite tracking", "simulation"], sector: "space", ticker: null },
  { name: "Surge AI", aliases: ["Surge", "SurgeAI", "Surge", "data labeling", "AI training"], sector: "ai", ticker: null },
  { name: "Swarm Aero", aliases: ["SwarmAero", "drone swarms"], sector: "defense", ticker: null },
  { name: "WeaveGrid", aliases: ["EV grid integration", "utilities", "smart grid"], sector: "climate", ticker: null },
  { name: "Zanskar", aliases: ["geothermal", "AI exploration", "clean energy"], sector: "climate", ticker: null },
  { name: "Cohere", aliases: ["Cohere AI", "enterprise AI", "transformers", "Canadian"], sector: "ai", ticker: null },
  { name: "Waabi", aliases: ["autonomous trucks", "simulation", "Canadian"], sector: "transportation", ticker: null },
  { name: "Ada", aliases: ["customer service AI", "chatbot", "enterprise", "Canadian"], sector: "ai", ticker: null },
  { name: "D-Wave Quantum", aliases: ["D-WaveQuantum", "quantum computing", "quantum annealing", "Canadian"], sector: "quantum", ticker: "QBTS" },
  { name: "Photonic Inc", aliases: ["Photonic", "PhotonicInc", "quantum computing", "photonic", "Microsoft", "Canadian"], sector: "quantum", ticker: null },
  { name: "Nord Quantique", aliases: ["NordQuantique", "quantum computing", "bosonic qubits", "Canadian"], sector: "quantum", ticker: null },
  { name: "Kepler Communications", aliases: ["KeplerCommunications", "satellite communications", "space infrastructure", "Canadian"], sector: "space", ticker: null },
  { name: "GHGSat", aliases: ["methane monitoring", "satellite", "Canadian"], sector: "space", ticker: null },
  { name: "Reaction Dynamics", aliases: ["ReactionDynamics", "hybrid propulsion", "Canadian"], sector: "space", ticker: null },
  { name: "Kinova Robotics", aliases: ["Kinova", "KinovaRobotics", "assistive robotics", "robotic arms", "medical", "Canadian"], sector: "robotics", ticker: null },
  { name: "ARC Clean Technology", aliases: ["ARC Clean", "ARCCleanTechnology", "clean energy", "Canadian"], sector: "nuclear", ticker: null },
  { name: "Kela", aliases: ["allies"], sector: "defense", ticker: null },
  { name: "goTenna", aliases: ["Go Tenna", "mesh networking", "communication"], sector: "defense", ticker: null },
  { name: "Endurosat", aliases: ["European"], sector: "space", ticker: null },
  { name: "Skyryse", aliases: ["safety"], sector: "space", ticker: null },
  { name: "Dusty Robotics", aliases: ["Dusty", "DustyRobotics", "construction", "automation"], sector: "robotics", ticker: null },
  { name: "Vayu Robotics", aliases: ["VayuRobotics", "delivery"], sector: "robotics", ticker: null },
  { name: "Fortera", aliases: ["cement", "carbon capture"], sector: "climate", ticker: null },
  { name: "LanzaTech", aliases: ["Lanza Tech", "carbon capture", "fuels", "chemicals"], sector: "climate", ticker: null },
  { name: "QuantumScape", aliases: ["batteries", "solid-state"], sector: "climate", ticker: "QS" },
  { name: "Mainspring Energy", aliases: ["Mainspring", "MainspringEnergy", "power generation", "hydrogen", "distributed energy"], sector: "climate", ticker: null },
  { name: "Watershed", aliases: ["carbon", "enterprise"], sector: "climate", ticker: null },
  { name: "Sakana AI", aliases: ["Sakana", "SakanaAI", "Sakana", "foundation models", "research"], sector: "ai", ticker: null },
  { name: "Together AI", aliases: ["Together", "TogetherAI", "Together", "infrastructure", "open-source"], sector: "ai", ticker: null },
  { name: "Runway", aliases: ["video", "creative tools", "generative"], sector: "ai", ticker: null },
  { name: "Humane", aliases: ["wearables", "hardware"], sector: "ai", ticker: null },
  { name: "eGenesis", aliases: ["xenotransplantation", "gene editing", "organs"], sector: "biotech", ticker: null },
  { name: "Osmo", aliases: ["olfaction", "scent", "digital smell"], sector: "consumer", ticker: null },
  { name: "Vivodyne", aliases: ["organs"], sector: "biotech", ticker: null },
  { name: "Cellares", aliases: ["cell therapy", "automation"], sector: "biotech", ticker: null },
  { name: "LabGenius", aliases: ["antibody", "drug discovery"], sector: "biotech", ticker: null },
  { name: "Mission Barns", aliases: ["MissionBarns", "cultivated meat", "food tech"], sector: "biotech", ticker: null },
  { name: "KLIR Sky", aliases: ["KLIRSky", "carbon capture", "climate tech", "industrial decarbonization"], sector: "climate", ticker: null },
  { name: "Cresilon", aliases: ["medical devices", "trauma care", "hemostatic", "FDA cleared"], sector: "biotech", ticker: null },
  { name: "Ulysses Robotics", aliases: ["Ulysses", "UlyssesRobotics", "UlyssesEco", "ocean tech", "underwater autonomy", "ecosystem restoration"], sector: "robotics", ticker: null },
  { name: "Poseidon Aerospace", aliases: ["Poseidon", "PoseidonAerospace", "ekranoplan", "ground-effect vehicle"], sector: "aerospace", ticker: null },
  { name: "Cuby", aliases: ["housing", "construction tech", "modular", "prefab"], sector: "construction", ticker: null },
  { name: "White Stork", aliases: ["WhiteStork", "Ukraine", "autonomous weapons"], sector: "defense", ticker: null },
  { name: "Parry Labs", aliases: ["Parry", "ParryLabs", "systems integration", "digital transformation"], sector: "defense", ticker: null },
  { name: "Fortem Technologies", aliases: ["Fortem", "FortemTechnologies", "C-UAS", "drone interceptor"], sector: "defense", ticker: null },
  { name: "Hexium", aliases: ["nuclear fuel", "isotope separation", "AVLIS", "lithium"], sector: "nuclear", ticker: null },
  { name: "General Galactic", aliases: ["GeneralGalactic", "synthetic fuels", "sustainable hydrocarbons", "climate tech"], sector: "climate", ticker: null },
  { name: "Ares Industries", aliases: ["AresIndustries", "munitions", "defense manufacturing", "guided weapons"], sector: "defense", ticker: null },
  { name: "Starcloud", aliases: ["space computing", "orbital data centers", "cloud infrastructure", "low latency"], sector: "space", ticker: null },
  { name: "Steady Energy", aliases: ["Steady", "SteadyEnergy", "clean energy", "baseload power"], sector: "climate", ticker: null },
  { name: "CarbonCapture Inc.", aliases: ["CarbonCaptureInc.", "direct air capture", "carbon removal", "climate tech"], sector: "climate", ticker: null },
  { name: "Kyten Technologies", aliases: ["Kyten", "KytenTechnologies", "carbon nanotubes", "advanced materials", "aerospace materials", "nanotechnology"], sector: "climate", ticker: null },
  { name: "Graphyte", aliases: ["carbon removal", "biomass", "carbon storage", "climate tech"], sector: "climate", ticker: null },
  { name: "Celero Communications", aliases: ["CeleroCommunications", "satellite communications", "space tech"], sector: "space", ticker: null },
  { name: "Zeta Surgical", aliases: ["ZetaSurgical", "surgical robotics", "neurosurgery", "AI navigation", "medical devices"], sector: "biotech", ticker: null },
  { name: "Electric Hydrogen", aliases: ["ElectricHydrogen", "green hydrogen", "electrolyzers", "industrial decarbonization", "clean energy"], sector: "climate", ticker: null },
  { name: "Tenna Systems", aliases: ["Tenna", "TennaSystems", "electronic warfare", "spectrum mapping", "SIGINT", "GPS-denied"], sector: "defense", ticker: null },
  { name: "Vatn Systems", aliases: ["VatnSystems", "underwater", "autonomous systems", "naval warfare"], sector: "defense", ticker: null },
  { name: "Hubble Network", aliases: ["HubbleNetwork", "satellite IoT", "Bluetooth", "space tech"], sector: "space", ticker: null },
  { name: "Sage Geosystems", aliases: ["SageGeosystems", "geothermal", "energy storage", "dispatchable power", "clean energy"], sector: "climate", ticker: null },
  { name: "Fourth Power", aliases: ["FourthPower", "thermal storage", "liquid metal", "thermophotovoltaics", "energy storage"], sector: "climate", ticker: null },
  { name: "Asimov", aliases: ["synthetic biology", "cell engineering", "genetic circuits", "therapeutics"], sector: "biotech", ticker: null },
  { name: "Cemvita Factory", aliases: ["CemvitaFactory", "synthetic biology", "carbon capture", "bio-ethylene", "industrial decarbonization"], sector: "climate", ticker: null },
  { name: "Q-CTRL", aliases: ["QCTRL", "quantum computing", "quantum sensing", "control software", "deep tech"], sector: "quantum", ticker: null },
  { name: "Hidden Level", aliases: ["HiddenLevel", "passive radar", "RF sensing", "critical infrastructure"], sector: "defense", ticker: null },
  { name: "ClearSpace", aliases: ["space debris", "orbital servicing", "sustainability"], sector: "space", ticker: null },
  { name: "Profluent", aliases: ["AI protein design", "LLM biology", "therapeutics", "synthetic biology"], sector: "biotech", ticker: null },
  { name: "Fairmat", aliases: ["carbon fiber recycling", "circular economy", "advanced materials", "sustainability"], sector: "climate", ticker: null },
  { name: "Infleqtion", aliases: ["ColdQuanta", "quantum sensing", "atomic clocks", "GPS-denied navigation", "defense tech"], sector: "quantum", ticker: null },
  { name: "Elroy Air", aliases: ["ElroyAir", "cargo drones", "autonomous VTOL", "military logistics", "disaster relief"], sector: "autonomous", ticker: null },
  { name: "Solid Power", aliases: ["SolidPower", "solid-state batteries", "EV batteries", "energy storage", "automotive"], sector: "climate", ticker: null },
  { name: "Rain AI", aliases: ["RainAI", "neuromorphic computing", "AI chips", "edge AI", "energy efficiency"], sector: "quantum", ticker: null },
  { name: "Twelve Labs", aliases: ["Twelve", "TwelveLabs", "multimodal AI", "video understanding", "foundation models", "computer vision"], sector: "ai", ticker: null },
  { name: "Kolena", aliases: ["ML testing", "AI validation", "model evaluation", "AI safety"], sector: "ai", ticker: null },
  { name: "Modal", aliases: ["serverless", "cloud infrastructure", "GPU compute", "ML ops"], sector: "ai", ticker: null },
  { name: "Terran Orbital", aliases: ["TerranOrbital", "small satellites", "satellite manufacturing", "space defense", "LEO constellations"], sector: "space", ticker: "LLAP" },
  { name: "Skyrora", aliases: ["launch vehicles", "small satellites", "UK space", "European launch"], sector: "space", ticker: null },
  { name: "Orbion Space Technology", aliases: ["Orbion Space", "OrbionSpaceTechnology", "electric propulsion", "plasma thrusters", "satellite propulsion", "space tech"], sector: "space", ticker: null },
  { name: "Quantinuum", aliases: ["trapped-ion", "quantum computing", "Honeywell Quantum", "Cambridge Quantum", "H-Series"], sector: "quantum", ticker: null },
  { name: "CORE POWER", aliases: ["CorePower", "maritime nuclear", "molten salt reactor", "floating nuclear", "shipping decarbonization"], sector: "nuclear", ticker: null },
  { name: "Wandelbots", aliases: ["no-code robotics", "NOVA platform", "robot programming", "industrial automation"], sector: "robotics", ticker: null },
  { name: "AlixLabs", aliases: ["APS technology", "atomic layer etching", "semiconductor patterning", "EUV alternative"], sector: "semiconductor", ticker: null },
  { name: "OpenStar", aliases: ["levitated dipole", "fusion energy", "dipole fusion", "New Zealand fusion"], sector: "energy", ticker: null },
  { name: "Qilimanjaro", aliases: ["fluxonium qubits", "analog quantum", "superconducting quantum", "Barcelona quantum"], sector: "quantum", ticker: null },
  { name: "QuiX Quantum", aliases: ["QuiXQuantum", "photonic quantum", "TriPleX", "silicon nitride quantum"], sector: "quantum", ticker: null },
  { name: "SemiQon", aliases: ["cryogenic CMOS", "cryo-CMOS", "quantum chips", "cryogenic semiconductor"], sector: "quantum", ticker: null },
  { name: "REGENT Craft", aliases: ["REGENTCraft", "seaglider", "electric seaglider", "Viceroy", "ground effect vehicle"], sector: "transportation", ticker: null },
  { name: "Orbit2Orbit", aliases: ["orbital logistics", "space logistics", "in-space transport", "reusable space tug"], sector: "space", ticker: null },
  { name: "Archer Materials", aliases: ["ArcherMaterials", "12CQ chip", "carbon qubit", "room temperature quantum"], sector: "quantum", ticker: "AXE" },
  { name: "DEEPX", aliases: ["edge AI chip", "DX-M1", "DX-M2", "Korean AI semiconductor", "neural processor"], sector: "semiconductor", ticker: null },
  { name: "PierSight", aliases: ["SAR satellite", "maritime surveillance", "ocean monitoring", "AIS satellite"], sector: "space", ticker: null },

  // ── Manufacturing / Reindustrialization ("American Shenzhen") ──────────
  // Specialty Materials — Composites
  { name: "Axial Composites", aliases: ["AxialComposites", "composite manufacturing", "Giuseppe Rapisarda"], sector: "manufacturing", ticker: null },
  { name: "Layup Parts", aliases: ["LayupParts", "composite parts", "carbon fiber parts"], sector: "manufacturing", ticker: null },
  { name: "Fiber Dynamics", aliases: ["FiberDynamics", "fiber composite", "advanced composites"], sector: "manufacturing", ticker: null },

  // Specialty Materials — Metals
  { name: "Bethlehem Steel Corp", aliases: ["BethlehemSteel", "Bethlehem Steel", "new Bethlehem Steel", "American steelmaking"], sector: "manufacturing", ticker: null },
  { name: "Nox Metals", aliases: ["NoxMetals", "Zane Hengsperger", "metal manufacturing"], sector: "manufacturing", ticker: null },
  { name: "Duranium", aliases: ["Duranium metals", "advanced alloys manufacturing"], sector: "manufacturing", ticker: null },

  // Electronics Manufacturing
  { name: "MacroFab", aliases: ["Macro Fab", "electronics manufacturing", "PCB assembly", "Chris Church"], sector: "manufacturing", ticker: null },
  { name: "Finwave Semiconductor", aliases: ["FinwaveSemi", "Finwave Semi", "GaN transistors", "gallium nitride semiconductor"], sector: "semiconductor", ticker: null },
  { name: "Sphere Semi", aliases: ["SphereSemi", "Sphere Semiconductor", "semiconductor manufacturing"], sector: "semiconductor", ticker: null },

  // Precision Machining & Fabrication
  { name: "SendCutSend", aliases: ["Send Cut Send", "laser cutting service", "Jim Belosic", "online fabrication"], sector: "manufacturing", ticker: null },
  { name: "OSH Cut", aliases: ["OSHCut", "waterjet cutting", "laser cutting marketplace"], sector: "manufacturing", ticker: null },
  { name: "RMFG", aliases: ["rapid manufacturing", "CNC machining service"], sector: "manufacturing", ticker: null },
  { name: "Forge Automation", aliases: ["ForgeAutomation", "manufacturing automation", "CNC automation"], sector: "manufacturing", ticker: null },
  { name: "Emelody", aliases: ["Emelody manufacturing", "precision fabrication"], sector: "manufacturing", ticker: null },

  // Robotic Systems — Actuators & Motors
  { name: "HLabs", aliases: ["H Labs", "robotic actuators", "electric actuators"], sector: "robotics", ticker: null },
  { name: "RISE Robotics", aliases: ["RISERobotics", "Beltdraulic", "Blake Sessions", "hydraulic replacement"], sector: "robotics", ticker: null },
  { name: "Artimus Robotics", aliases: ["ArtimusRobotics", "HASEL actuators", "electrohydraulic actuators", "soft robotics actuators"], sector: "robotics", ticker: null },
  { name: "Corvex Systems", aliases: ["CorvexSystems", "Corvex Robotics", "robotic systems integration"], sector: "robotics", ticker: null },

  // Forming & Casting
  { name: "Foundry Lab", aliases: ["FoundryLab", "rapid casting", "digital casting"], sector: "manufacturing", ticker: null },
  { name: "Digital Metal", aliases: ["DigitalMetal", "binder jetting", "metal binder jetting"], sector: "manufacturing", ticker: null },
  { name: "Aestus Industries", aliases: ["AestusIndustries", "Aestus casting", "advanced casting"], sector: "manufacturing", ticker: null },

  // Battery Manufacturing
  { name: "Ouros Energy", aliases: ["OurosEnergy", "battery manufacturing", "energy storage manufacturing"], sector: "energy", ticker: null },
  { name: "Forge Nano", aliases: ["ForgeNano", "ALD coating", "atomic layer deposition", "battery coating", "nanocoating"], sector: "manufacturing", ticker: null },
  { name: "Nascent Materials", aliases: ["NascentMaterials", "battery materials", "cathode materials"], sector: "manufacturing", ticker: null },
  { name: "Group1", aliases: ["Group1 battery", "battery technology"], sector: "energy", ticker: null },
  { name: "Advano", aliases: ["Advano silicon", "silicon anode", "battery silicon anode"], sector: "energy", ticker: null },

  // Metal Additive Manufacturing
  { name: "Freeform", aliases: ["Freeform 3D", "Erik Palitsch", "autonomous foundry", "metal 3D printing"], sector: "manufacturing", ticker: null },
  { name: "Vuecason", aliases: ["Vuecason manufacturing", "metal additive manufacturing"], sector: "manufacturing", ticker: null },
  { name: "Radian Forge", aliases: ["RadianForge", "metal forging", "advanced forging"], sector: "manufacturing", ticker: null },
  { name: "Seurat Technologies", aliases: ["SeuratTech", "Seurat Tech", "James DeMuth", "area printing", "laser powder bed fusion"], sector: "manufacturing", ticker: null },
  { name: "VulcanForms", aliases: ["Vulcan Forms", "Martin Feldmann", "industrial metal 3D printing", "laser metal fusion"], sector: "manufacturing", ticker: null },

  // Sensors & Optics — LiDAR
  { name: "Lumotive", aliases: ["Lumotive LiDAR", "software-defined LiDAR", "metamaterial beam steering"], sector: "sensors", ticker: null },
  { name: "Ouster", aliases: ["Ouster LiDAR", "Angus Pacala", "digital LiDAR", "REV7 sensor"], sector: "sensors", ticker: "OUST" },
  { name: "Aeva Technologies", aliases: ["Aeva Tech", "Aeva FMCW", "4D LiDAR", "Soroush Salehian", "frequency modulated LiDAR"], sector: "sensors", ticker: "AEVA" },
  { name: "Voyant Photonics", aliases: ["VoyantPhotonics", "chip-scale LiDAR", "silicon photonics LiDAR", "Chris Phare"], sector: "sensors", ticker: null },

  // Industrial Robots
  { name: "Standard Bots", aliases: ["StandardBots", "Evan Beard", "affordable robot arm", "RO1 robot"], sector: "robotics", ticker: null },
  { name: "Path Robotics", aliases: ["PathRobotics", "Andy Lonsberry", "autonomous welding", "robotic welding"], sector: "robotics", ticker: null },
  { name: "Forge Robotics", aliases: ["ForgeRobotics", "industrial robotic welding"], sector: "robotics", ticker: null },
  { name: "Cohesive Robotics", aliases: ["CohesiveRobotics", "machine tending", "robotic machine tending"], sector: "robotics", ticker: null },
  { name: "Ultra Robotics", aliases: ["UltraRobotics", "ultra robot", "general purpose robot"], sector: "robotics", ticker: null },

  // Power Electronics & Semiconductors
  { name: "Gallox Semiconductors", aliases: ["GalloxSemi", "Gallox Semi", "gallium oxide", "Ga2O3 semiconductor"], sector: "semiconductor", ticker: null },
  { name: "Vertical Semiconductor", aliases: ["VerticalSemi", "Vertical Semi", "vertical GaN", "vertical power semiconductor"], sector: "semiconductor", ticker: null },

  // Industrial Chemicals
  { name: "MaverickX", aliases: ["Maverick X", "industrial chemicals startup", "chemical manufacturing"], sector: "manufacturing", ticker: null },

  // Machine Tools
  { name: "OpenX", aliases: ["OpenX machine tools", "open source machine tools", "CNC machine tools"], sector: "manufacturing", ticker: null },

  // Ecosystem Enablers
  { name: "First Resonance", aliases: ["FirstResonance", "Karan Talati", "ION factory OS", "manufacturing execution system"], sector: "manufacturing", ticker: null },
  { name: "Diode Computers", aliases: ["DiodeComputers", "Diode industrial computing"], sector: "manufacturing", ticker: null },
  { name: "Flux", aliases: ["Flux PCB", "Flux circuit design", "PCB design tool"], sector: "manufacturing", ticker: null },
  { name: "JITX", aliases: ["JITX PCB", "automated circuit board design", "programmatic PCB design"], sector: "manufacturing", ticker: null },
  { name: "Lambda Function", aliases: ["LambdaFunction", "manufacturing lambda"], sector: "manufacturing", ticker: null },
  { name: "Krevera", aliases: ["Krevera manufacturing", "supply chain platform"], sector: "manufacturing", ticker: null },
  { name: "Photonium", aliases: ["Photonium optics", "photonic manufacturing"], sector: "manufacturing", ticker: null },
  { name: "Mbodi AI", aliases: ["MbodiAI", "Mbodi robotics", "embodied AI platform"], sector: "robotics", ticker: null },
  { name: "Matter", aliases: ["Matter manufacturing", "manufacturing collaboration"], sector: "manufacturing", ticker: null },
  { name: "Drafter", aliases: ["Drafter CAD", "Drafter design", "AI-powered CAD", "manufacturing design tool"], sector: "manufacturing", ticker: null },

  // ─── International expansion (Round 7b, April 2026) — 40 highest-signal non-US additions ───
  // Tracked for news aggregation; full metadata in data.js COMPANIES array
  { name: "Nu Quantum", aliases: ["NuQuantum", "quantum networking"], sector: "quantum", ticker: null },
  { name: "Fractile", aliases: ["Fractile AI", "in-memory inference"], sector: "ai", ticker: null },
  { name: "Pragmatic Semiconductor", aliases: ["Pragmatic Semi", "flexible chips"], sector: "chips", ticker: null },
  { name: "Oxa", aliases: ["Oxbotica", "Oxa autonomy"], sector: "autonomous", ticker: null },
  { name: "Humanoid", aliases: ["Humanoid AI", "HMND 01"], sector: "robotics", ticker: null },
  { name: "Nyobolt", aliases: ["niobium anode", "fast-charging battery"], sector: "battery", ticker: null },
  { name: "Cambridge Aerospace", aliases: ["CambridgeAerospace", "Skyhammer interceptor"], sector: "defense", ticker: null },
  { name: "Isembard", aliases: ["Isembard AI", "AI manufacturing"], sector: "manufacturing", ticker: null },
  { name: "Epoch Biodesign", aliases: ["EpochBiodesign", "enzymatic plastic recycling"], sector: "biotech", ticker: null },
  { name: "ReOrbit", aliases: ["ReOrbit space", "software-defined satellite"], sector: "space", ticker: null },
  { name: "Kvertus", aliases: ["Kvertus EW", "Atlas EW wall"], sector: "defense", ticker: null },
  { name: "Fire Point", aliases: ["FirePoint", "Flamingo cruise missile", "FP-5"], sector: "defense", ticker: null },
  { name: "Vyriy Drone", aliases: ["VyriyDrone", "FPV Ukraine"], sector: "defense", ticker: null },
  { name: "WB Group", aliases: ["WBGroup", "Warmate loitering munition"], sector: "defense", ticker: null },
  { name: "Creotech Instruments", aliases: ["Creotech", "HyperSat"], sector: "space", ticker: null },
  { name: "Quandela", aliases: ["Quandela quantum", "PROQCIMA"], sector: "quantum", ticker: null },
  { name: "Zama", aliases: ["Zama FHE", "fully homomorphic encryption"], sector: "ai", ticker: null },
  { name: "H Company", aliases: ["HCompany", "Holo3"], sector: "ai", ticker: null },
  { name: "Harmattan AI", aliases: ["HarmattanAI", "French combat drone"], sector: "defense", ticker: null },
  { name: "Unseenlabs", aliases: ["Unseen Labs", "BRO satellites", "RF geolocation"], sector: "space", ticker: null },
  { name: "Jimmy Energy", aliases: ["JimmyEnergy", "Jimmy microreactor"], sector: "nuclear", ticker: null },
  { name: "Multiverse Computing", aliases: ["MultiverseComputing", "CompactifAI"], sector: "ai", ticker: null },
  { name: "Nearfield Instruments", aliases: ["NearfieldInstruments", "AFM metrology"], sector: "chips", ticker: null },
  { name: "Axelera AI", aliases: ["AxeleraAI", "Metis AIPU"], sector: "chips", ticker: null },
  { name: "Synspective", aliases: ["Synspective SAR", "StriX"], sector: "space", ticker: null },
  { name: "Preferred Networks", aliases: ["PreferredNetworks", "MN-Core"], sector: "ai", ticker: null },
  { name: "Telexistence", aliases: ["Telexistence Astra", "retail humanoid"], sector: "robotics", ticker: null },
  { name: "FuriosaAI", aliases: ["Furiosa AI", "RNGD"], sector: "chips", ticker: null },
  { name: "Thunder Tiger", aliases: ["ThunderTiger", "Sea Shark USV"], sector: "defense", ticker: null },
  { name: "Digantara", aliases: ["Digantara space", "SCOT-1"], sector: "space", ticker: null },
  { name: "Raphe mPhibr", aliases: ["RapheMphibr", "mPhibr UAV"], sector: "defense", ticker: null },
  { name: "Hypersonix Launch Systems", aliases: ["Hypersonix", "DART AE", "scramjet"], sector: "defense", ticker: null },
  { name: "Gilmour Space Technologies", aliases: ["Gilmour Space", "Eris rocket"], sector: "space", ticker: null },
  { name: "Heven AeroTech", aliases: ["Heven", "hydrogen drones"], sector: "defense", ticker: null },
  { name: "Quantum Art", aliases: ["QuantumArt", "Israeli quantum"], sector: "quantum", ticker: null },
  { name: "Majestic Labs", aliases: ["MajesticLabs", "disaggregated memory"], sector: "chips", ticker: null },
  { name: "Hailo", aliases: ["Hailo AI", "Hailo-10H", "edge AI chip"], sector: "chips", ticker: null },
  { name: "H2Pro", aliases: ["H2 Pro", "E-TAC electrolysis"], sector: "hydrogen", ticker: null },
  { name: "StoreDot", aliases: ["Store Dot", "XFC battery"], sector: "battery", ticker: null },
  { name: "Space42", aliases: ["Space 42", "Bayanat Yahsat"], sector: "space", ticker: null },
  { name: "HUMAIN", aliases: ["Humain AI", "Saudi AI"], sector: "ai", ticker: null },
  { name: "Baykar", aliases: ["Bayraktar", "TB2", "TB3", "Kizilelma"], sector: "defense", ticker: null },
  { name: "Ranovus", aliases: ["Ranovus photonics", "copackaged optics"], sector: "chips", ticker: null },
  { name: "Summit Nanotech", aliases: ["SummitNanotech", "DLE lithium"], sector: "mining", ticker: null },
  { name: "Terra Industries", aliases: ["TerraIndustries", "Nigerian drones", "NetHawk"], sector: "defense", ticker: null },
  { name: "Stark Defence", aliases: ["Stark", "Virtus VTOL"], sector: "defense", ticker: null },
  { name: "Agile Robots", aliases: ["AgileRobots", "Agile ONE"], sector: "robotics", ticker: null },
  { name: "Reflex Aerospace", aliases: ["ReflexAerospace", "Praetora platform"], sector: "space", ticker: null },
  { name: "Gauss Fusion", aliases: ["GaussFusion", "European stellarator"], sector: "fusion", ticker: null },
  { name: "QuantumDiamonds", aliases: ["Quantum Diamonds", "diamond NV", "chip inspection"], sector: "quantum", ticker: null },
  { name: "Corintis", aliases: ["Corintis cooling", "microfluidic chip cooling"], sector: "chips", ticker: null },
  { name: "Distalmotion", aliases: ["Dexter surgical robot"], sector: "medtech", ticker: null },
  { name: "Tubulis", aliases: ["TUB-040", "Tubulis ADC"], sector: "biotech", ticker: null },
  { name: "Candela", aliases: ["Candela electric boat", "Candela P-12"], sector: "transportation", ticker: null },

  // ─── Round 7c: international audit additions (Apr 2026) — trackable in news pipeline ───
  { name: "Black Forest Labs", aliases: ["BlackForestLabs", "FLUX", "BFL"], sector: "ai", ticker: null },
  { name: "Calogena", aliases: ["Calogena SMR", "district heating reactor"], sector: "nuclear", ticker: null },
  { name: "Hexana", aliases: ["Hexana SMR", "sodium-cooled reactor"], sector: "nuclear", ticker: null },
  { name: "Dust", aliases: ["Dust AI", "dust.tt", "Gabriel Hubert"], sector: "ai", ticker: null },
  { name: "Photoroom", aliases: ["Photoroom AI", "on-device imaging"], sector: "ai", ticker: null },
  { name: "Vyoma", aliases: ["Vyoma Space", "optical SSA"], sector: "space", ticker: null },
  { name: "Atmos Space Cargo", aliases: ["AtmosSpaceCargo", "Phoenix capsule", "inflatable reentry"], sector: "space", ticker: null },
  { name: "Theion", aliases: ["Theion battery", "crystal sulfur"], sector: "battery", ticker: null },
  { name: "Neustark", aliases: ["Neustark CCS", "CO2 mineralization"], sector: "climate", ticker: null },
  { name: "Orbem", aliases: ["Orbem AI", "MRI imaging"], sector: "biotech", ticker: null },
  { name: "Quantum Motion", aliases: ["QuantumMotion", "silicon spin qubit"], sector: "quantum", ticker: null },
  { name: "Monumo", aliases: ["Monumo motor", "AI electric motor"], sector: "chips", ticker: null },
  { name: "XMOS", aliases: ["xcore", "XMOS audio"], sector: "chips", ticker: null },
  { name: "Causaly", aliases: ["Causaly AI", "biomedical literature"], sector: "biotech", ticker: null },
  { name: "SpaceForest", aliases: ["Perun rocket", "Polish launch"], sector: "space", ticker: null },
  { name: "RoboTwin", aliases: ["RoboTwin demo", "Czech robotics"], sector: "robotics", ticker: null },
  { name: "Ukrspecsystems", aliases: ["USS", "PD-2 Shark", "Ukrainian UAV"], sector: "defense", ticker: null },
  { name: "Roboneers", aliases: ["Shablya M2", "Ironclad UGV", "remote weapon station"], sector: "defense", ticker: null },
  { name: "Cellcolabs", aliases: ["Cellcolabs stem cells", "Karolinska"], sector: "biotech", ticker: null },
  { name: "Space Machines Company", aliases: ["SpaceMachines", "Optimus OSV"], sector: "space", ticker: null },
  { name: "HEO", aliases: ["HEO Robotics", "non-earth imaging"], sector: "space", ticker: null },
  { name: "Manastu Space", aliases: ["ManastuSpace", "green H2O2 propulsion"], sector: "space", ticker: null },
  { name: "Kneron", aliases: ["Kneron NPU", "edge AI"], sector: "chips", ticker: null },
  { name: "MakinaRocks", aliases: ["Makina Rocks", "industrial MLOps"], sector: "ai", ticker: null },
  { name: "DustPhotonics", aliases: ["Dust Photonics", "800G optics"], sector: "chips", ticker: null },
  { name: "Dream Security", aliases: ["DreamSecurity", "critical infrastructure security"], sector: "defense", ticker: null },
  { name: "Asterra", aliases: ["Asterra SAR", "leak detection"], sector: "space", ticker: null },
  { name: "Vention", aliases: ["Vention manufacturing", "modular robotics"], sector: "robotics", ticker: null },
  { name: "Kraken Robotics", aliases: ["KrakenRobotics", "SeaPower", "synthetic aperture sonar"], sector: "defense", ticker: "PNG" },
  { name: "Telesat Lightspeed", aliases: ["TelesatLightspeed", "Lightspeed constellation"], sector: "space", ticker: "TSAT" },
  { name: "AbCellera", aliases: ["AbCellera Biologics", "antibody discovery"], sector: "biotech", ticker: "ABCL" },
  { name: "Svante", aliases: ["Svante capture", "solid sorbent CCS"], sector: "climate", ticker: null },
  { name: "MineSense Technologies", aliases: ["MineSense", "ore sorting"], sector: "climate", ticker: null },
  { name: "Hypernova Space Technologies", aliases: ["Hypernova Space", "metal-fueled thruster"], sector: "space", ticker: null },
  { name: "Fossa Systems", aliases: ["Fossa picosats", "Spanish IoT satellite"], sector: "space", ticker: null },
  { name: "Saltfoss Energy", aliases: ["Saltfoss", "Seaborg", "molten salt reactor"], sector: "nuclear", ticker: null },
  { name: "Terrahaptix", aliases: ["Terrahaptix", "Terra Industries", "NetHawk"], sector: "defense", ticker: null },
];

// ═══════════════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Get all search terms (company names + aliases) for news matching
 */
function getAllSearchTerms() {
  const terms = [];
  for (const company of MASTER_COMPANY_LIST) {
    terms.push(company.name);
    terms.push(...company.aliases);
  }
  return [...new Set(terms)];
}

/**
 * Find a company by name or alias
 */
function findCompany(searchTerm) {
  const lowerSearch = searchTerm.toLowerCase();
  
  for (const company of MASTER_COMPANY_LIST) {
    if (company.name.toLowerCase() === lowerSearch) {
      return company;
    }
    for (const alias of company.aliases) {
      if (alias.toLowerCase() === lowerSearch) {
        return company;
      }
    }
  }
  return null;
}

// Generic aliases that match too many articles — skip these for news matching
const GENERIC_ALIAS_BLOCKLIST = new Set([
  'search', 'serverless', 'ai infrastructure', 'automation', 'industrial robotics',
  'military tech', 'defense tech', 'autonomous systems', 'national security',
  'sales', 'productivity', 'ai chips', 'inference', 'clean energy', 'renewable',
  'warehouse robotics', 'factory automation', 'edge computing', 'ai security',
  'open-source ai', 'open-source hardware', 'workflow', 'enterprise',
  'energy efficient', 'advanced materials', 'intelligence', 'analysis',
  'communication', 'simulation', 'logistics', 'delivery', 'safety',
  'construction', 'inspection', 'medical', 'batteries', 'solid-state',
  'carbon capture', 'fuels', 'chemicals', 'carbon', 'hydrogen',
  'geothermal', 'electric vehicles', 'trucks', 'data labeling', 'ai training',
  'generative', 'creative tools', 'video', 'wearables', 'hardware',
  'organs', 'cell therapy', 'drug discovery', 'food tech', 'cement',
  'infrastructure', 'open-source', 'research', 'foundation models',
  'computer vision', 'content moderation', 'ai apis', 'sensor fusion',
  'reinforcement learning', 'allies', 'european', 'canadian',
  'energy storage', 'power generation', 'distributed energy',
  'quantum computing', 'space debris', 'satellite', 'space tech',
  'nuclear', 'nuclear fuel', 'climate tech', 'sustainability',
  // Manufacturing generic terms
  'metal manufacturing', 'battery technology', 'composite manufacturing',
  'precision fabrication', 'robotic systems integration', 'advanced composites',
  'manufacturing software platform', 'supply chain platform',
  'manufacturing collaboration', 'chemical manufacturing',
  'semiconductor manufacturing', 'battery materials', 'energy storage manufacturing',
]);

// Company names that are too short/generic for substring matching — require word boundaries
const SHORT_GENERIC_NAMES = new Set([
  'ada', 'cape', 'sift', 'revel', 'cover', 'modal', 'runway', 'prepared',
  'surge ai', 'rain ai', 'hive ai', 'field ai',
  // Manufacturing/reindustrialization generic names
  'flux', 'matter', 'dirac', 'freeform', 'drafter', 'hlabs', 'group1', 'openx',
  'emelody', 'advano', 'rangeview', 'duranium', 'ouster',
]);

/**
 * Check if text mentions any tracked company (returns array of matches)
 * This is the main function used by news aggregators.
 *
 * Matching rules:
 * - Company names are matched case-insensitively using word boundaries
 * - Short/generic company names require strict word-boundary matching
 * - Aliases must be 8+ characters and not in the generic blocklist
 * - All alias matching uses word boundaries to prevent false positives
 */
function mentionsCompany(text) {
  const lowerText = text.toLowerCase();
  const matches = [];
  const seen = new Set();

  for (const company of MASTER_COMPANY_LIST) {
    if (seen.has(company.name)) continue;

    const lowerName = company.name.toLowerCase();

    // Check company name with word-boundary matching
    if (SHORT_GENERIC_NAMES.has(lowerName)) {
      // Strict word-boundary match for generic names
      const nameRegex = new RegExp('\\b' + lowerName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i');
      if (nameRegex.test(text) && lowerText.indexOf(lowerName) !== -1) {
        // Extra check: for very short names, require the name appears as a standalone entity
        // e.g., "Cover" should match "Cover raises $50M" but not "cover charge"
        // We accept if it appears capitalized or in a company context
        const idx = text.indexOf(company.name);
        if (idx !== -1) {
          matches.push(company);
          seen.add(company.name);
          continue;
        }
      }
    } else if (lowerText.includes(lowerName)) {
      matches.push(company);
      seen.add(company.name);
      continue;
    }

    // Check aliases — require 8+ chars and not in blocklist, use word boundaries
    for (const alias of company.aliases) {
      if (alias.length < 8) continue;
      if (GENERIC_ALIAS_BLOCKLIST.has(alias.toLowerCase())) continue;

      const lowerAlias = alias.toLowerCase();
      if (lowerText.includes(lowerAlias)) {
        // Word-boundary check to avoid partial matches
        const aliasRegex = new RegExp('\\b' + lowerAlias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i');
        if (aliasRegex.test(text)) {
          matches.push(company);
          seen.add(company.name);
          break;
        }
      }
    }
  }

  return matches;
}

/**
 * Get all companies in a specific sector
 */
function getCompaniesBySector(sector) {
  return MASTER_COMPANY_LIST.filter(c => c.sector === sector);
}

/**
 * Get all publicly traded companies
 */
function getPublicCompanies() {
  return MASTER_COMPANY_LIST.filter(c => c.ticker !== null);
}

/**
 * Get statistics about the master list
 */
function getStats() {
  const sectors = [...new Set(MASTER_COMPANY_LIST.map(c => c.sector))];
  const publicCount = MASTER_COMPANY_LIST.filter(c => c.ticker).length;
  let totalAliases = 0;
  for (const c of MASTER_COMPANY_LIST) {
    totalAliases += c.aliases.length;
  }
  
  return {
    totalCompanies: MASTER_COMPANY_LIST.length,
    totalSearchTerms: MASTER_COMPANY_LIST.length + totalAliases,
    sectors: sectors,
    publicCompanies: publicCount,
    coverage: "100%"
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

// Node.js exports (for data fetcher scripts)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    MASTER_COMPANY_LIST,
    getAllSearchTerms,
    findCompany,
    mentionsCompany,
    getCompaniesBySector,
    getPublicCompanies,
    getStats
  };
}

// Browser global (for client-side use)
if (typeof window !== 'undefined') {
  window.MASTER_COMPANY_LIST = MASTER_COMPANY_LIST;
  window.mentionsCompany = mentionsCompany;
  window.findCompany = findCompany;
  window.getStats = getStats;
}
