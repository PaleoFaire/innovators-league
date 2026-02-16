/**
 * MASTER COMPANY LIST - The Innovators League
 *
 * Central registry of ALL tracked companies with their aliases for news monitoring.
 * This file is used by all data fetchers to ensure comprehensive tracking.
 *
 * Last updated: 2026-02-16
 * Total companies: 500+
 */

const MASTER_COMPANY_LIST = [
  // ═══════════════════════════════════════════════════════════════════
  // DEFENSE & SECURITY (~60 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Anduril Industries", aliases: ["Anduril", "Lattice OS", "Ghost-X", "Barracuda"], sector: "defense", ticker: null },
  { name: "Shield AI", aliases: ["ShieldAI", "Hivemind", "V-BAT"], sector: "defense", ticker: null },
  { name: "Palantir Technologies", aliases: ["Palantir", "PLTR", "Foundry", "Gotham", "Apollo"], sector: "defense", ticker: "PLTR" },
  { name: "Epirus", aliases: ["Epirus Inc", "Leonidas"], sector: "defense", ticker: null },
  { name: "Saronic", aliases: ["Saronic Technologies"], sector: "defense", ticker: null },
  { name: "Skydio", aliases: ["Skydio Inc", "Skydio X10"], sector: "defense", ticker: null },
  { name: "Hadrian", aliases: ["Hadrian Automation"], sector: "defense", ticker: null },
  { name: "Vannevar Labs", aliases: ["Vannevar"], sector: "defense", ticker: null },
  { name: "Rebellion Defense", aliases: ["Rebellion"], sector: "defense", ticker: null },
  { name: "Chaos Industries", aliases: ["Chaos"], sector: "defense", ticker: null },
  { name: "Castelion", aliases: ["Castelion Inc"], sector: "defense", ticker: null },
  { name: "Neros", aliases: ["Neros Technologies"], sector: "defense", ticker: null },
  { name: "CX2 Industries", aliases: ["CX2"], sector: "defense", ticker: null },
  { name: "Picogrid", aliases: [], sector: "defense", ticker: null },
  { name: "Allen Control Systems", aliases: ["Allen Control"], sector: "defense", ticker: null },
  { name: "Mach Industries", aliases: ["Mach"], sector: "defense", ticker: null },
  { name: "Andrenam", aliases: [], sector: "defense", ticker: null },
  { name: "Blue Water Autonomy", aliases: ["Blue Water"], sector: "defense", ticker: null },
  { name: "Saildrone", aliases: [], sector: "defense", ticker: null },
  { name: "AeroVironment", aliases: ["AVAV"], sector: "defense", ticker: "AVAV" },
  { name: "Kratos Defense", aliases: ["Kratos", "KTOS"], sector: "defense", ticker: "KTOS" },
  { name: "L3Harris", aliases: ["L3 Harris", "LHX"], sector: "defense", ticker: "LHX" },
  { name: "Northrop Grumman", aliases: ["Northrop", "NOC"], sector: "defense", ticker: "NOC" },
  { name: "Lockheed Martin", aliases: ["Lockheed", "LMT", "Skunk Works"], sector: "defense", ticker: "LMT" },
  { name: "General Dynamics", aliases: ["GD"], sector: "defense", ticker: "GD" },
  { name: "Raytheon", aliases: ["RTX", "Raytheon Technologies"], sector: "defense", ticker: "RTX" },
  { name: "BAE Systems", aliases: ["BAE"], sector: "defense", ticker: null },
  { name: "Scale AI", aliases: ["Scale", "Scale Donovan"], sector: "defense", ticker: null },
  { name: "Second Front Systems", aliases: ["Second Front", "Game Warden"], sector: "defense", ticker: null },
  { name: "Primer AI", aliases: ["Primer"], sector: "defense", ticker: null },
  { name: "True Anomaly", aliases: ["TrueAnomaly"], sector: "defense", ticker: null },
  { name: "Forterra", aliases: [], sector: "defense", ticker: null },
  { name: "Auterion", aliases: [], sector: "defense", ticker: null },
  { name: "Firehawk Aerospace", aliases: ["Firehawk"], sector: "defense", ticker: null },
  { name: "Reveal Technology", aliases: ["Reveal Tech", "Farsight"], sector: "defense", ticker: null },
  { name: "Galvanick", aliases: [], sector: "defense", ticker: null },
  { name: "SkySafe", aliases: [], sector: "defense", ticker: null },
  { name: "Distributed Spectrum", aliases: [], sector: "defense", ticker: null },
  { name: "Aurelius Systems", aliases: ["Aurelius"], sector: "defense", ticker: null },
  { name: "Darkhive", aliases: ["Dark Hive"], sector: "defense", ticker: null },
  { name: "Deterrence", aliases: [], sector: "defense", ticker: null },
  { name: "Deepnight", aliases: [], sector: "defense", ticker: null },
  { name: "Zeromark", aliases: [], sector: "defense", ticker: null },
  { name: "Rune Technologies", aliases: ["Rune", "TyrOS"], sector: "defense", ticker: null },
  { name: "Swan", aliases: [], sector: "defense", ticker: null },
  { name: "Biofire", aliases: ["Biofire Technologies"], sector: "defense", ticker: null },
  { name: "Firestorm Labs", aliases: ["Firestorm"], sector: "defense", ticker: null },
  { name: "Helsing", aliases: [], sector: "defense", ticker: null },
  { name: "Quantum-Systems", aliases: [], sector: "defense", ticker: null },
  { name: "Flock Safety", aliases: ["Flock"], sector: "defense", ticker: null },
  { name: "Theseus", aliases: [], sector: "defense", ticker: null },
  { name: "Icarus", aliases: [], sector: "defense", ticker: null },
  { name: "Mara", aliases: [], sector: "defense", ticker: null },
  { name: "PILGRIM", aliases: [], sector: "defense", ticker: null },
  { name: "Overland AI", aliases: [], sector: "defense", ticker: null },
  { name: "Kodiak Robotics", aliases: ["Kodiak"], sector: "defense", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // NUCLEAR & FUSION (~35 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Commonwealth Fusion Systems", aliases: ["CFS", "Commonwealth Fusion", "SPARC", "ARC"], sector: "nuclear", ticker: null },
  { name: "Helion Energy", aliases: ["Helion", "Polaris"], sector: "nuclear", ticker: null },
  { name: "TAE Technologies", aliases: ["TAE", "TAE Tech", "Tri Alpha Energy"], sector: "nuclear", ticker: null },
  { name: "Oklo", aliases: ["Oklo Inc", "OKLO", "Aurora"], sector: "nuclear", ticker: "OKLO" },
  { name: "Kairos Power", aliases: ["Kairos", "Hermes"], sector: "nuclear", ticker: null },
  { name: "TerraPower", aliases: ["Terra Power", "Natrium"], sector: "nuclear", ticker: null },
  { name: "NuScale Power", aliases: ["NuScale", "SMR", "VOYGR"], sector: "nuclear", ticker: "SMR" },
  { name: "X-Energy", aliases: ["X-energy", "Xe-100"], sector: "nuclear", ticker: null },
  { name: "Radiant Nuclear", aliases: ["Radiant", "Radiant Industries", "Kaleidos"], sector: "nuclear", ticker: null },
  { name: "Valar Atomics", aliases: ["Valar"], sector: "nuclear", ticker: null },
  { name: "Aalo Atomics", aliases: ["Aalo"], sector: "nuclear", ticker: null },
  { name: "Last Energy", aliases: [], sector: "nuclear", ticker: null },
  { name: "Deep Fission", aliases: [], sector: "nuclear", ticker: null },
  { name: "Zeno Power", aliases: ["Zeno"], sector: "nuclear", ticker: null },
  { name: "General Fusion", aliases: [], sector: "nuclear", ticker: null },
  { name: "Zap Energy", aliases: ["Zap", "Z-pinch"], sector: "nuclear", ticker: null },
  { name: "Type One Energy", aliases: ["Type One"], sector: "nuclear", ticker: null },
  { name: "Focused Energy", aliases: [], sector: "nuclear", ticker: null },
  { name: "Nano Nuclear Energy", aliases: ["Nano Nuclear", "NNE", "ZEUS", "ODIN"], sector: "nuclear", ticker: "NNE" },
  { name: "Pacific Fusion", aliases: [], sector: "nuclear", ticker: null },
  { name: "Fuse Energy", aliases: ["Fuse"], sector: "nuclear", ticker: null },
  { name: "Xcimer Energy", aliases: ["Xcimer"], sector: "nuclear", ticker: null },
  { name: "Avalanche Energy", aliases: ["Avalanche"], sector: "nuclear", ticker: null },
  { name: "Tokamak Energy", aliases: ["Tokamak"], sector: "nuclear", ticker: null },
  { name: "First Light Fusion", aliases: ["First Light"], sector: "nuclear", ticker: null },
  { name: "Newcleo", aliases: [], sector: "nuclear", ticker: null },
  { name: "Proxima Fusion", aliases: ["Proxima"], sector: "nuclear", ticker: null },
  { name: "Marvel Fusion", aliases: [], sector: "nuclear", ticker: null },
  { name: "Naarea", aliases: ["XAMR"], sector: "nuclear", ticker: null },
  { name: "Renaissance Fusion", aliases: ["Renaissance"], sector: "nuclear", ticker: null },
  { name: "Westinghouse", aliases: ["Westinghouse Electric"], sector: "nuclear", ticker: null },
  { name: "Centrus Energy", aliases: ["Centrus", "LEU"], sector: "nuclear", ticker: "LEU" },

  // ═══════════════════════════════════════════════════════════════════
  // CLIMATE & ENERGY (~40 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Fervo Energy", aliases: ["Fervo"], sector: "energy", ticker: null },
  { name: "Koloma", aliases: [], sector: "energy", ticker: null },
  { name: "Antora Energy", aliases: ["Antora"], sector: "energy", ticker: null },
  { name: "Form Energy", aliases: ["Form"], sector: "energy", ticker: null },
  { name: "Malta", aliases: ["Malta Inc"], sector: "energy", ticker: null },
  { name: "Solugen", aliases: [], sector: "energy", ticker: null },
  { name: "Terraform Industries", aliases: ["Terraform", "Terraformer"], sector: "energy", ticker: null },
  { name: "Heirloom Carbon", aliases: ["Heirloom"], sector: "energy", ticker: null },
  { name: "KoBold Metals", aliases: ["KoBold"], sector: "energy", ticker: null },
  { name: "Exowatt", aliases: [], sector: "energy", ticker: null },
  { name: "Mazama", aliases: [], sector: "energy", ticker: null },
  { name: "Quaise Energy", aliases: ["Quaise"], sector: "energy", ticker: null },
  { name: "Captura", aliases: [], sector: "energy", ticker: null },
  { name: "Base Power", aliases: [], sector: "energy", ticker: null },
  { name: "Karman Industries", aliases: ["Karman"], sector: "energy", ticker: null },
  { name: "Claros", aliases: [], sector: "energy", ticker: null },
  { name: "Brimstone", aliases: [], sector: "energy", ticker: null },
  { name: "Boston Metal", aliases: [], sector: "energy", ticker: null },
  { name: "Bedrock Energy", aliases: ["Bedrock"], sector: "energy", ticker: null },
  { name: "Arbor Energy", aliases: ["Arbor"], sector: "energy", ticker: null },
  { name: "Endurance Energy", aliases: ["Endurance"], sector: "energy", ticker: null },
  { name: "Cape", aliases: [], sector: "energy", ticker: null },
  { name: "Aepnus Technology", aliases: ["Aepnus"], sector: "energy", ticker: null },
  { name: "Twelve", aliases: [], sector: "energy", ticker: null },
  { name: "Sublime Systems", aliases: ["Sublime"], sector: "energy", ticker: null },
  { name: "Redwood Materials", aliases: ["Redwood"], sector: "energy", ticker: null },
  { name: "Natron Energy", aliases: ["Natron"], sector: "energy", ticker: null },
  { name: "EnerVenue", aliases: [], sector: "energy", ticker: null },
  { name: "Charm Industrial", aliases: ["Charm"], sector: "energy", ticker: null },
  { name: "Impulse Labs", aliases: [], sector: "energy", ticker: null },
  { name: "Mariana Minerals", aliases: ["Mariana"], sector: "energy", ticker: null },
  { name: "H2 Green Steel", aliases: ["H2GS"], sector: "energy", ticker: null },
  { name: "Climeworks", aliases: [], sector: "energy", ticker: null },
  { name: "Synhelion", aliases: [], sector: "energy", ticker: null },
  { name: "Gravitricity", aliases: [], sector: "energy", ticker: null },
  { name: "Sunfire", aliases: [], sector: "energy", ticker: null },
  { name: "Verkor", aliases: [], sector: "energy", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // SPACE & AEROSPACE (~60 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "SpaceX", aliases: ["Space X", "Starlink", "Starship", "Falcon", "Dragon", "Raptor"], sector: "space", ticker: null },
  { name: "Rocket Lab", aliases: ["RocketLab", "RKLB", "Electron", "Neutron", "Photon"], sector: "space", ticker: "RKLB" },
  { name: "Relativity Space", aliases: ["Relativity", "Terran R", "Terran 1", "Aeon"], sector: "space", ticker: null },
  { name: "Blue Origin", aliases: ["Blue origin", "New Glenn", "New Shepard", "Blue Moon"], sector: "space", ticker: null },
  { name: "Sierra Space", aliases: ["Sierra Nevada", "Dream Chaser"], sector: "space", ticker: null },
  { name: "Axiom Space", aliases: ["Axiom"], sector: "space", ticker: null },
  { name: "Vast", aliases: ["Vast Space", "Haven"], sector: "space", ticker: null },
  { name: "Planet Labs", aliases: ["Planet", "PL", "Dove", "SuperDove"], sector: "space", ticker: "PL" },
  { name: "Varda Space Industries", aliases: ["Varda Space", "Varda"], sector: "space", ticker: null },
  { name: "Impulse Space", aliases: ["Impulse"], sector: "space", ticker: null },
  { name: "Stoke Space", aliases: ["Stoke", "Nova"], sector: "space", ticker: null },
  { name: "Firefly Aerospace", aliases: ["Firefly", "Alpha", "Blue Ghost"], sector: "space", ticker: null },
  { name: "Astra Space", aliases: ["Astra", "ASTR"], sector: "space", ticker: "ASTR" },
  { name: "Astranis", aliases: ["Astranis Space", "MicroGEO"], sector: "space", ticker: null },
  { name: "Muon Space", aliases: ["Muon"], sector: "space", ticker: null },
  { name: "K2 Space", aliases: ["K2"], sector: "space", ticker: null },
  { name: "AstroForge", aliases: ["Astro Forge"], sector: "space", ticker: null },
  { name: "Astrobotic", aliases: ["Astrobotic Technology", "Peregrine", "Griffin"], sector: "space", ticker: null },
  { name: "Intuitive Machines", aliases: ["Intuitive", "LUNR", "Nova-C"], sector: "space", ticker: "LUNR" },
  { name: "Spire Global", aliases: ["Spire", "SPIR"], sector: "space", ticker: "SPIR" },
  { name: "BlackSky", aliases: ["BlackSky Technology", "BKSY"], sector: "space", ticker: "BKSY" },
  { name: "Maxar", aliases: ["Maxar Technologies"], sector: "space", ticker: null },
  { name: "Redwire", aliases: ["Redwire Corporation", "RDW"], sector: "space", ticker: "RDW" },
  { name: "Apex Space", aliases: ["Apex"], sector: "space", ticker: null },
  { name: "Northwood Space", aliases: ["Northwood"], sector: "space", ticker: null },
  { name: "Observable Space", aliases: ["Observable"], sector: "space", ticker: null },
  { name: "Albedo", aliases: ["Albedo Space"], sector: "space", ticker: null },
  { name: "Epsilon3", aliases: ["Epsilon 3"], sector: "space", ticker: null },
  { name: "Orbit Fab", aliases: ["OrbitFab"], sector: "space", ticker: null },
  { name: "Aalyria", aliases: ["Project Loon"], sector: "space", ticker: null },
  { name: "AnySignal", aliases: [], sector: "space", ticker: null },
  { name: "Turion Space", aliases: ["Turion"], sector: "space", ticker: null },
  { name: "Umbra", aliases: ["Umbra Lab"], sector: "space", ticker: null },
  { name: "Astrolab", aliases: ["FLEX"], sector: "space", ticker: null },
  { name: "Array Labs", aliases: ["Array"], sector: "space", ticker: null },
  { name: "Armada", aliases: ["Galleon"], sector: "space", ticker: null },
  { name: "Aetherflux", aliases: [], sector: "space", ticker: null },
  { name: "Capella Space", aliases: ["Capella"], sector: "space", ticker: null },
  { name: "Astroscale", aliases: [], sector: "space", ticker: null },
  { name: "Outpost Space", aliases: ["Outpost"], sector: "space", ticker: null },
  { name: "Longshot Space", aliases: ["Longshot"], sector: "space", ticker: null },
  { name: "Proteus Space", aliases: ["Proteus"], sector: "space", ticker: null },
  { name: "Ursa Major Technologies", aliases: ["Ursa Major"], sector: "space", ticker: null },
  { name: "AST SpaceMobile", aliases: ["AST", "ASTS", "BlueBird"], sector: "space", ticker: "ASTS" },
  { name: "ICEYE", aliases: [], sector: "space", ticker: null },
  { name: "Isar Aerospace", aliases: ["Isar", "Spectrum"], sector: "space", ticker: null },
  { name: "Rocket Factory Augsburg", aliases: ["RFA", "RFA One"], sector: "space", ticker: null },
  { name: "Orbex", aliases: ["Prime"], sector: "space", ticker: null },
  { name: "Space Forge", aliases: [], sector: "space", ticker: null },
  { name: "Latitude", aliases: ["Zephyr"], sector: "space", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // AEROSPACE / SUPERSONIC / AVIATION (~20 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Boom Supersonic", aliases: ["Boom", "Overture", "XB-1"], sector: "aerospace", ticker: null },
  { name: "Hermeus", aliases: ["Hermeus Corporation", "Quarterhorse", "Chimera"], sector: "aerospace", ticker: null },
  { name: "Venus Aerospace", aliases: ["Venus"], sector: "aerospace", ticker: null },
  { name: "Joby Aviation", aliases: ["Joby", "JOBY"], sector: "aerospace", ticker: "JOBY" },
  { name: "Archer Aviation", aliases: ["Archer", "ACHR", "Midnight"], sector: "aerospace", ticker: "ACHR" },
  { name: "Lilium", aliases: ["Lilium Jet", "LILM"], sector: "aerospace", ticker: "LILM" },
  { name: "Wisk Aero", aliases: ["Wisk"], sector: "aerospace", ticker: null },
  { name: "Beta Technologies", aliases: ["Beta", "ALIA"], sector: "aerospace", ticker: null },
  { name: "Zipline", aliases: ["Zipline International", "Platform 2"], sector: "aerospace", ticker: null },
  { name: "Wing", aliases: ["Wing Aviation"], sector: "aerospace", ticker: null },
  { name: "Matternet", aliases: [], sector: "aerospace", ticker: null },
  { name: "Exosonic", aliases: [], sector: "aerospace", ticker: null },
  { name: "Destinus", aliases: [], sector: "aerospace", ticker: null },
  { name: "Vertical Aerospace", aliases: ["Vertical", "VX4"], sector: "aerospace", ticker: null },
  { name: "ZeroAvia", aliases: [], sector: "aerospace", ticker: null },
  { name: "Volocopter", aliases: ["VoloCity"], sector: "aerospace", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // AI & SOFTWARE (~50 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "OpenAI", aliases: ["Open AI", "GPT-4", "GPT-5", "ChatGPT", "o1", "o3", "Sora"], sector: "ai", ticker: null },
  { name: "Anthropic", aliases: ["Claude", "Claude 3", "Claude 4", "Opus", "Sonnet"], sector: "ai", ticker: null },
  { name: "Google DeepMind", aliases: ["DeepMind", "Gemini", "Gemini Ultra"], sector: "ai", ticker: null },
  { name: "Mistral AI", aliases: ["Mistral", "Mixtral"], sector: "ai", ticker: null },
  { name: "Cohere", aliases: ["Cohere AI"], sector: "ai", ticker: null },
  { name: "AI21 Labs", aliases: ["AI21", "Jurassic"], sector: "ai", ticker: null },
  { name: "Inflection AI", aliases: ["Inflection", "Pi"], sector: "ai", ticker: null },
  { name: "Character AI", aliases: ["Character.AI", "Character"], sector: "ai", ticker: null },
  { name: "Stability AI", aliases: ["Stability", "Stable Diffusion"], sector: "ai", ticker: null },
  { name: "Midjourney", aliases: ["Mid Journey", "MJ"], sector: "ai", ticker: null },
  { name: "Runway", aliases: ["Runway ML", "Gen-2", "Gen-3"], sector: "ai", ticker: null },
  { name: "Scale AI", aliases: ["Scale", "Alexandr Wang"], sector: "ai", ticker: null },
  { name: "Hugging Face", aliases: ["HuggingFace"], sector: "ai", ticker: null },
  { name: "Databricks", aliases: ["DBRX", "Mosaic ML"], sector: "ai", ticker: null },
  { name: "Anyscale", aliases: ["Ray"], sector: "ai", ticker: null },
  { name: "Weights & Biases", aliases: ["W&B", "wandb"], sector: "ai", ticker: null },
  { name: "Perplexity AI", aliases: ["Perplexity"], sector: "ai", ticker: null },
  { name: "Adept AI", aliases: ["Adept"], sector: "ai", ticker: null },
  { name: "Imbue", aliases: ["Generally Intelligent"], sector: "ai", ticker: null },
  { name: "Glean", aliases: ["Glean AI"], sector: "ai", ticker: null },
  { name: "Harvey AI", aliases: ["Harvey"], sector: "ai", ticker: null },
  { name: "Jasper AI", aliases: ["Jasper"], sector: "ai", ticker: null },
  { name: "Covariant", aliases: ["Covariant AI", "RFM-1"], sector: "ai", ticker: null },
  { name: "Physical Intelligence", aliases: ["Physical Intelligence AI", "Pi AI"], sector: "ai", ticker: null },
  { name: "Applied Intuition", aliases: [], sector: "ai", ticker: null },
  { name: "Anysphere", aliases: ["Cursor"], sector: "ai", ticker: null },
  { name: "Skild AI", aliases: ["Skild"], sector: "ai", ticker: null },
  { name: "Crusoe Energy", aliases: ["Crusoe"], sector: "ai", ticker: null },
  { name: "ElevenLabs", aliases: ["11Labs", "Eleven Labs"], sector: "ai", ticker: null },
  { name: "Hippocratic AI", aliases: ["Hippocratic"], sector: "ai", ticker: null },
  { name: "Wayve", aliases: [], sector: "ai", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // CHIPS / SEMICONDUCTORS (~20 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Cerebras", aliases: ["Cerebras Systems", "CS-3", "Wafer Scale", "WSE"], sector: "chips", ticker: null },
  { name: "Groq", aliases: ["Groq Inc", "LPU", "GroqCloud"], sector: "chips", ticker: null },
  { name: "Etched", aliases: ["Etched AI", "Sohu"], sector: "chips", ticker: null },
  { name: "Lightmatter", aliases: ["Light Matter", "Passage"], sector: "chips", ticker: null },
  { name: "SambaNova", aliases: ["Samba Nova", "SambaNova Systems"], sector: "chips", ticker: null },
  { name: "Graphcore", aliases: ["Graph Core", "IPU"], sector: "chips", ticker: null },
  { name: "Tenstorrent", aliases: ["Ten Storrent"], sector: "chips", ticker: null },
  { name: "d-Matrix", aliases: ["dMatrix"], sector: "chips", ticker: null },
  { name: "Rain AI", aliases: ["Rain Neuromorphics"], sector: "chips", ticker: null },
  { name: "Mythic", aliases: ["Mythic AI"], sector: "chips", ticker: null },
  { name: "Extropic", aliases: ["TSU"], sector: "chips", ticker: null },
  { name: "Substrate", aliases: [], sector: "chips", ticker: null },
  { name: "Lab 91", aliases: ["Lab91", "MoS2"], sector: "chips", ticker: null },
  { name: "Atomic Semi", aliases: [], sector: "chips", ticker: null },
  { name: "PsiQuantum", aliases: ["Psi Quantum"], sector: "chips", ticker: null },
  { name: "Astera Labs", aliases: ["Astera", "ALAB"], sector: "chips", ticker: "ALAB" },
  { name: "Black Semiconductor", aliases: [], sector: "chips", ticker: null },
  { name: "NVIDIA", aliases: ["NVDA", "H100", "A100", "B200", "Blackwell"], sector: "chips", ticker: "NVDA" },
  { name: "AMD", aliases: ["Advanced Micro Devices", "MI300"], sector: "chips", ticker: "AMD" },

  // ═══════════════════════════════════════════════════════════════════
  // ROBOTICS (~30 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Figure AI", aliases: ["Figure", "Figure 01", "Figure 02"], sector: "robotics", ticker: null },
  { name: "Boston Dynamics", aliases: ["Boston Dynamics Inc", "Atlas", "Spot"], sector: "robotics", ticker: null },
  { name: "Agility Robotics", aliases: ["Agility", "Digit", "RoboFab"], sector: "robotics", ticker: null },
  { name: "Apptronik", aliases: ["Apptronik Inc", "Apollo"], sector: "robotics", ticker: null },
  { name: "1X Technologies", aliases: ["1X", "NEO", "EVE"], sector: "robotics", ticker: null },
  { name: "Sanctuary AI", aliases: ["Sanctuary", "Phoenix"], sector: "robotics", ticker: null },
  { name: "Tesla Bot", aliases: ["Optimus", "Tesla Optimus"], sector: "robotics", ticker: null },
  { name: "Collaborative Robotics", aliases: ["Cobot"], sector: "robotics", ticker: null },
  { name: "Gecko Robotics", aliases: ["Gecko"], sector: "robotics", ticker: null },
  { name: "Formic", aliases: ["Formic Technologies"], sector: "robotics", ticker: null },
  { name: "Symbotic", aliases: ["SYM"], sector: "robotics", ticker: "SYM" },
  { name: "Locus Robotics", aliases: ["Locus"], sector: "robotics", ticker: null },
  { name: "Machina Labs", aliases: ["Machina"], sector: "robotics", ticker: null },
  { name: "Sarcos Robotics", aliases: ["Sarcos"], sector: "robotics", ticker: null },
  { name: "Diligent Robotics", aliases: ["Diligent", "Moxi"], sector: "robotics", ticker: null },
  { name: "Divergent", aliases: ["DAPS", "Divergent 3D"], sector: "robotics", ticker: null },
  { name: "Amca", aliases: [], sector: "robotics", ticker: null },
  { name: "Carbon Robotics", aliases: ["LaserWeeder"], sector: "robotics", ticker: null },
  { name: "NEURA Robotics", aliases: ["NEURA"], sector: "robotics", ticker: null },
  { name: "Exotec", aliases: ["Skypod"], sector: "robotics", ticker: null },
  { name: "ANYbotics", aliases: ["ANYmal"], sector: "robotics", ticker: null },
  { name: "Re:Build Manufacturing", aliases: ["Re:Build", "Rebuild"], sector: "robotics", ticker: null },
  { name: "AMP Robotics", aliases: ["AMP"], sector: "robotics", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // QUANTUM COMPUTING (~20 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "IonQ", aliases: ["IONQ"], sector: "quantum", ticker: "IONQ" },
  { name: "Rigetti Computing", aliases: ["Rigetti", "RGTI"], sector: "quantum", ticker: "RGTI" },
  { name: "D-Wave Quantum", aliases: ["D-Wave", "QBTS", "D-Wave Systems"], sector: "quantum", ticker: "QBTS" },
  { name: "PsiQuantum", aliases: ["Psi Quantum"], sector: "quantum", ticker: null },
  { name: "Atom Computing", aliases: ["Atom"], sector: "quantum", ticker: null },
  { name: "QuEra Computing", aliases: ["QuEra"], sector: "quantum", ticker: null },
  { name: "Xanadu", aliases: ["Xanadu Quantum", "PennyLane"], sector: "quantum", ticker: null },
  { name: "Pasqal", aliases: [], sector: "quantum", ticker: null },
  { name: "IQM Quantum", aliases: ["IQM"], sector: "quantum", ticker: null },
  { name: "Alice & Bob", aliases: ["Alice and Bob"], sector: "quantum", ticker: null },
  { name: "Bleximo", aliases: [], sector: "quantum", ticker: null },
  { name: "Quantum Machines", aliases: ["QM"], sector: "quantum", ticker: null },
  { name: "Q-CTRL", aliases: ["QCTRL"], sector: "quantum", ticker: null },
  { name: "Classiq", aliases: ["Classiq Technologies"], sector: "quantum", ticker: null },
  { name: "Zapata Computing", aliases: ["Zapata AI", "Zapata"], sector: "quantum", ticker: null },
  { name: "Oxford Quantum Circuits", aliases: ["OQC", "Coaxmon"], sector: "quantum", ticker: null },
  { name: "planqc", aliases: [], sector: "quantum", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // BIOTECH & HEALTH (~50 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Recursion Pharmaceuticals", aliases: ["Recursion", "RXRX"], sector: "biotech", ticker: "RXRX" },
  { name: "Ginkgo Bioworks", aliases: ["Ginkgo", "DNA"], sector: "biotech", ticker: "DNA" },
  { name: "Tempus AI", aliases: ["Tempus", "TEM"], sector: "biotech", ticker: "TEM" },
  { name: "Neuralink", aliases: ["Neura Link"], sector: "biotech", ticker: null },
  { name: "Altos Labs", aliases: ["Altos"], sector: "biotech", ticker: null },
  { name: "Retro Biosciences", aliases: ["Retro Bio", "Retro"], sector: "biotech", ticker: null },
  { name: "NewLimit", aliases: ["New Limit"], sector: "biotech", ticker: null },
  { name: "Colossal Biosciences", aliases: ["Colossal", "Woolly Mammoth"], sector: "biotech", ticker: null },
  { name: "Mammoth Biosciences", aliases: ["Mammoth"], sector: "biotech", ticker: null },
  { name: "Synthego", aliases: [], sector: "biotech", ticker: null },
  { name: "Inscripta", aliases: [], sector: "biotech", ticker: null },
  { name: "Twist Bioscience", aliases: ["Twist", "TWST"], sector: "biotech", ticker: "TWST" },
  { name: "Beam Therapeutics", aliases: ["Beam", "BEAM"], sector: "biotech", ticker: "BEAM" },
  { name: "Prime Medicine", aliases: ["Prime"], sector: "biotech", ticker: null },
  { name: "Intellia Therapeutics", aliases: ["Intellia", "NTLA"], sector: "biotech", ticker: "NTLA" },
  { name: "Editas Medicine", aliases: ["Editas", "EDIT"], sector: "biotech", ticker: "EDIT" },
  { name: "CRISPR Therapeutics", aliases: ["CRISPR", "CRSP"], sector: "biotech", ticker: "CRSP" },
  { name: "Verve Therapeutics", aliases: ["Verve", "VERV"], sector: "biotech", ticker: "VERV" },
  { name: "Exact Sciences", aliases: ["Exact", "EXAS", "Cologuard"], sector: "biotech", ticker: "EXAS" },
  { name: "Grail", aliases: ["GRAIL Inc", "Galleri"], sector: "biotech", ticker: null },
  { name: "Guardant Health", aliases: ["Guardant", "GH"], sector: "biotech", ticker: "GH" },
  { name: "Foundation Medicine", aliases: ["FMI"], sector: "biotech", ticker: null },
  { name: "Freenome", aliases: [], sector: "biotech", ticker: null },
  { name: "Adaptive Biotechnologies", aliases: ["Adaptive", "ADPT"], sector: "biotech", ticker: "ADPT" },
  { name: "23andMe", aliases: ["23 and Me", "ME"], sector: "biotech", ticker: "ME" },
  { name: "Color Health", aliases: ["Color"], sector: "biotech", ticker: null },
  { name: "Illumina", aliases: ["ILMN"], sector: "biotech", ticker: "ILMN" },
  { name: "Moderna", aliases: ["MRNA"], sector: "biotech", ticker: "MRNA" },
  { name: "BioNTech", aliases: ["BNTX"], sector: "biotech", ticker: "BNTX" },
  { name: "Science Corporation", aliases: ["Science Corp"], sector: "biotech", ticker: null },
  { name: "Insitro", aliases: [], sector: "biotech", ticker: null },
  { name: "Eikon Therapeutics", aliases: ["Eikon"], sector: "biotech", ticker: null },
  { name: "Abridge", aliases: [], sector: "biotech", ticker: null },
  { name: "Neko Health", aliases: ["Neko"], sector: "biotech", ticker: null },
  { name: "Oxford Nanopore Technologies", aliases: ["Oxford Nanopore", "ONT"], sector: "biotech", ticker: null },
  { name: "DNA Script", aliases: [], sector: "biotech", ticker: null },
  { name: "Solar Foods", aliases: ["Solein"], sector: "biotech", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // AUTONOMOUS / TRANSPORTATION (~25 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Waymo", aliases: ["Waymo One", "Waymo Driver"], sector: "autonomy", ticker: null },
  { name: "Cruise", aliases: ["Cruise Automation", "GM Cruise"], sector: "autonomy", ticker: null },
  { name: "Zoox", aliases: ["Amazon Zoox"], sector: "autonomy", ticker: null },
  { name: "Aurora Innovation", aliases: ["Aurora", "AUR", "Aurora Driver"], sector: "autonomy", ticker: "AUR" },
  { name: "Nuro", aliases: ["Nuro AI"], sector: "autonomy", ticker: null },
  { name: "Motional", aliases: [], sector: "autonomy", ticker: null },
  { name: "May Mobility", aliases: ["May"], sector: "autonomy", ticker: null },
  { name: "Gatik", aliases: ["Gatik AI"], sector: "autonomy", ticker: null },
  { name: "TuSimple", aliases: ["Tu Simple", "TSP"], sector: "autonomy", ticker: "TSP" },
  { name: "Embark Trucks", aliases: ["Embark"], sector: "autonomy", ticker: null },
  { name: "Plus AI", aliases: ["Plus"], sector: "autonomy", ticker: null },
  { name: "Helm.ai", aliases: ["Helm AI"], sector: "autonomy", ticker: null },
  { name: "Ghost Autonomy", aliases: ["Ghost"], sector: "autonomy", ticker: null },
  { name: "The Boring Company", aliases: ["Boring Company", "TBC", "Loop"], sector: "autonomy", ticker: null },
  { name: "Pipedream", aliases: [], sector: "autonomy", ticker: null },
  { name: "Navier", aliases: [], sector: "autonomy", ticker: null },
  { name: "Arc Boats", aliases: ["Arc"], sector: "autonomy", ticker: null },
  { name: "Einride", aliases: ["T-Pod"], sector: "autonomy", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // CONSTRUCTION & MANUFACTURING (~15 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "ICON", aliases: ["ICON Technology", "ICON 3D"], sector: "construction", ticker: null },
  { name: "Mighty Buildings", aliases: ["Mighty"], sector: "construction", ticker: null },
  { name: "Apis Cor", aliases: ["ApisCor"], sector: "construction", ticker: null },
  { name: "Built Robotics", aliases: ["Built"], sector: "construction", ticker: null },
  { name: "Canvas Construction", aliases: ["Canvas"], sector: "construction", ticker: null },
  { name: "Dusty Robotics", aliases: ["Dusty"], sector: "construction", ticker: null },
  { name: "Factory OS", aliases: ["FactoryOS"], sector: "construction", ticker: null },
  { name: "Veev", aliases: ["Veev Group"], sector: "construction", ticker: null },
  { name: "Cover Technologies", aliases: ["Cover"], sector: "construction", ticker: null },
  { name: "Cuby Technologies", aliases: ["Cuby"], sector: "construction", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // FINTECH / SECURITY (~15 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Flexport", aliases: ["Flex Port"], sector: "logistics", ticker: null },
  { name: "Stripe", aliases: [], sector: "fintech", ticker: null },
  { name: "Plaid", aliases: [], sector: "fintech", ticker: null },
  { name: "Brex", aliases: [], sector: "fintech", ticker: null },
  { name: "Ramp", aliases: ["Ramp Financial"], sector: "fintech", ticker: null },
  { name: "Mercury", aliases: ["Mercury Bank"], sector: "fintech", ticker: null },
  { name: "Carta", aliases: [], sector: "fintech", ticker: null },
  { name: "Vanta", aliases: [], sector: "security", ticker: null },
  { name: "Snyk", aliases: [], sector: "security", ticker: null },
  { name: "Wiz", aliases: ["Wiz.io"], sector: "security", ticker: null },
  { name: "Orca Security", aliases: ["Orca"], sector: "security", ticker: null },
  { name: "SentinelOne", aliases: ["Sentinel One", "S"], sector: "security", ticker: "S" },
  { name: "CrowdStrike", aliases: ["Crowd Strike", "CRWD"], sector: "security", ticker: "CRWD" },

  // ═══════════════════════════════════════════════════════════════════
  // AGTECH (~10 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Rainmaker", aliases: [], sector: "agtech", ticker: null },
  { name: "Indigo Agriculture", aliases: ["Indigo Ag", "Indigo"], sector: "agtech", ticker: null },
  { name: "Farmers Business Network", aliases: ["FBN"], sector: "agtech", ticker: null },
  { name: "Plenty", aliases: ["Plenty Unlimited"], sector: "agtech", ticker: null },
  { name: "Bowery Farming", aliases: ["Bowery"], sector: "agtech", ticker: null },
  { name: "AppHarvest", aliases: ["APPH"], sector: "agtech", ticker: "APPH" },
  { name: "AeroFarms", aliases: ["Aero Farms"], sector: "agtech", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // CONSUMER TECH (~10 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Alpha School", aliases: ["AlphaSchool", "2 Hour Learning"], sector: "consumer", ticker: null },
  { name: "Matic Robotics", aliases: ["Matic"], sector: "consumer", ticker: null },
  { name: "Daylight Computer", aliases: ["Daylight"], sector: "consumer", ticker: null },
  { name: "Framework Computer", aliases: ["Framework"], sector: "consumer", ticker: null },
  { name: "Whisper Aero", aliases: ["Whisper"], sector: "consumer", ticker: null },
  { name: "Synthesis", aliases: [], sector: "consumer", ticker: null },

  // ═══════════════════════════════════════════════════════════════════
  // OCEAN & MARITIME (~10 companies)
  // ═══════════════════════════════════════════════════════════════════
  { name: "Bedrock Ocean", aliases: ["Bedrock"], sector: "ocean", ticker: null },
  { name: "Running Tide", aliases: [], sector: "ocean", ticker: null },
  { name: "Orbital Marine Power", aliases: ["Orbital Marine", "O2 tidal"], sector: "ocean", ticker: null },
  { name: "Clippership", aliases: [], sector: "ocean", ticker: null },
];

// ═══════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════

/**
 * Get all search terms for comprehensive news monitoring
 * Returns array of all company names and aliases
 */
function getAllSearchTerms() {
  const terms = new Set();
  for (const company of MASTER_COMPANY_LIST) {
    terms.add(company.name.toLowerCase());
    for (const alias of company.aliases) {
      if (alias && alias.length >= 3) { // Minimum 3 chars to avoid false positives
        terms.add(alias.toLowerCase());
      }
    }
  }
  return Array.from(terms);
}

/**
 * Find a company by name or alias
 * @param {string} searchTerm - Company name or alias to search for
 * @returns {Object|null} - Company object or null
 */
function findCompany(searchTerm) {
  const lower = searchTerm.toLowerCase();
  return MASTER_COMPANY_LIST.find(c =>
    c.name.toLowerCase() === lower ||
    c.aliases.some(a => a.toLowerCase() === lower)
  );
}

/**
 * Check if text mentions any tracked company
 * @param {string} text - Text to check for company mentions
 * @returns {Array} - Array of company objects mentioned in the text
 */
function mentionsCompany(text) {
  const lowerText = text.toLowerCase();
  const matches = [];
  const seen = new Set();

  for (const company of MASTER_COMPANY_LIST) {
    if (seen.has(company.name)) continue;

    // Check main company name
    if (lowerText.includes(company.name.toLowerCase())) {
      matches.push(company);
      seen.add(company.name);
      continue;
    }

    // Check aliases (minimum 4 chars for partial matching to avoid false positives)
    for (const alias of company.aliases) {
      if (alias.length >= 4 && lowerText.includes(alias.toLowerCase())) {
        matches.push(company);
        seen.add(company.name);
        break;
      }
    }
  }

  return matches;
}

/**
 * Get all companies in a specific sector
 * @param {string} sector - Sector to filter by
 * @returns {Array} - Array of company objects in that sector
 */
function getCompaniesBySector(sector) {
  return MASTER_COMPANY_LIST.filter(c => c.sector === sector.toLowerCase());
}

/**
 * Get all publicly traded companies (with tickers)
 * @returns {Array} - Array of company objects with stock tickers
 */
function getPublicCompanies() {
  return MASTER_COMPANY_LIST.filter(c => c.ticker !== null);
}

/**
 * Get company count stats
 * @returns {Object} - Statistics about tracked companies
 */
function getStats() {
  const stats = {
    total: MASTER_COMPANY_LIST.length,
    bySector: {},
    publicCompanies: 0,
    totalAliases: 0
  };

  for (const company of MASTER_COMPANY_LIST) {
    stats.bySector[company.sector] = (stats.bySector[company.sector] || 0) + 1;
    if (company.ticker) stats.publicCompanies++;
    stats.totalAliases += company.aliases.length;
  }

  return stats;
}

// Get all unique sectors
const SECTORS = [...new Set(MASTER_COMPANY_LIST.map(c => c.sector))];

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    MASTER_COMPANY_LIST,
    getAllSearchTerms,
    findCompany,
    mentionsCompany,
    getCompaniesBySector,
    getPublicCompanies,
    getStats,
    SECTORS
  };
}

// If run directly, output stats
if (typeof require !== 'undefined' && require.main === module) {
  const stats = getStats();
  console.log('='.repeat(60));
  console.log('MASTER COMPANY LIST STATISTICS');
  console.log('='.repeat(60));
  console.log(`Total companies: ${stats.total}`);
  console.log(`Total searchable terms: ${getAllSearchTerms().length}`);
  console.log(`Public companies (with tickers): ${stats.publicCompanies}`);
  console.log(`Total aliases: ${stats.totalAliases}`);
  console.log('\nBy sector:');

  Object.entries(stats.bySector)
    .sort((a, b) => b[1] - a[1])
    .forEach(([sector, count]) => {
      console.log(`  ${sector}: ${count}`);
    });
}
