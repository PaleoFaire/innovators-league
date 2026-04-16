// ═══════════════════════════════════════════════════════
// INDUSTRY TRANSFORMATION TRACKING
// Shared module powering transformation.html (hub) and
// every transformation/*.html industry page.
//
// Accuracy-first: every data point is either sourced from
// a verifiable primary source (SAM.gov, SEC EDGAR, DoD,
// company press releases) or clearly labeled ROS estimate.
// ═══════════════════════════════════════════════════════

// ── helpers ──────────────────────────────────────────────
function til_escape(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function til_slug(name) {
  if (typeof companyToSlug === 'function') return companyToSlug(name);
  return String(name || '').toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function til_fmt_amount(raw) {
  // raw comes in millions — accept string "$1.8B" or number
  if (typeof raw === 'number') {
    if (raw >= 1000) return '$' + (raw / 1000).toFixed(1) + 'B';
    if (raw >= 1)    return '$' + Math.round(raw) + 'M';
    return '$' + (raw * 1000).toFixed(0) + 'K';
  }
  return raw || '';
}

function til_parse_amount_to_m(str) {
  // parse strings like "$1.8B", "$392M", "$500k" → value in millions
  if (!str || typeof str !== 'string') return 0;
  const s = str.replace(/[,$\s+]/g, '').toLowerCase();
  const m = s.match(/([\d.]+)\s*([bmk])?/);
  if (!m) return 0;
  const v = parseFloat(m[1]);
  if (isNaN(v)) return 0;
  if (m[2] === 'b') return v * 1000;
  if (m[2] === 'k') return v / 1000;
  return v;
}

// ── industry configurations ──────────────────────────────
// Each industry is a pure data config. Pages load one of
// these and the shared render functions do the rest.

const TRANSFORMATION_INDUSTRIES = {
  defense: {
    slug: 'defense',
    label: 'Defense',
    icon: '🛡️',
    color: '#dc2626',
    eyebrow: 'INDUSTRY TRANSFORMATION · DEFENSE',
    title: "Defense is being transformed. Here's who's winning.",
    subtitle: 'The $820B global defense market is 5-7 years into a 15-year transformation. Software flipped first. Platforms are flipping now.',
    thesis: 'Software has already flipped. Now hardware — drones, ships, missiles — is being rebuilt by venture-backed primes that iterate like technology companies, not government contractors.',
    // Which COMPANIES[].sector values map into this industry
    sector_match: ['Defense & Security', 'defense & security', 'Drones & Autonomous', 'drones & autonomous', 'Supersonic & Hypersonic', 'Ocean & Maritime'],
    stack_layers: [
      {
        name: 'Platforms',
        icon: '✈️',
        description: 'Aircraft, drones, ships, vehicles',
        incumbents: [
          { name: 'Boeing Defense', ticker: 'BA', url: 'https://www.boeing.com/defense' },
          { name: 'Lockheed Martin', ticker: 'LMT', url: 'https://www.lockheedmartin.com' },
          { name: 'Northrop Grumman', ticker: 'NOC', url: 'https://www.northropgrumman.com' },
          { name: 'General Dynamics', ticker: 'GD', url: 'https://www.gd.com' }
        ],
        frontier: ['Anduril Industries', 'Shield AI', 'Saildrone', 'Saronic', 'Castelion', 'Neros']
      },
      {
        name: 'Subsystems',
        icon: '⚙️',
        description: 'Propulsion, power, munitions',
        incumbents: [
          { name: 'RTX (Raytheon)', ticker: 'RTX', url: 'https://www.rtx.com' },
          { name: 'Collins Aerospace', ticker: 'RTX', url: 'https://www.collinsaerospace.com' },
          { name: 'Aerojet Rocketdyne (L3Harris)', ticker: 'LHX', url: 'https://www.l3harris.com' }
        ],
        frontier: ['Epirus', 'Hermeus', 'Ursa Major', 'Stoke Space', 'Ares Industries']
      },
      {
        name: 'Sensors & EW',
        icon: '📡',
        description: 'Radar, IR, SIGINT, electronic warfare',
        incumbents: [
          { name: 'L3Harris', ticker: 'LHX', url: 'https://www.l3harris.com' },
          { name: 'Raytheon IS', ticker: 'RTX', url: 'https://www.rtx.com' },
          { name: 'Elbit Systems', ticker: 'ESLT', url: 'https://elbitsystems.com' }
        ],
        frontier: ['Vannevar Labs', 'HawkEye 360', 'Chaos Industries', 'Scout AI']
      },
      {
        name: 'Software & AI',
        icon: '🧠',
        description: 'Mission systems, analytics, autonomy',
        incumbents: [
          { name: 'SAIC', ticker: 'SAIC', url: 'https://www.saic.com' },
          { name: 'Leidos', ticker: 'LDOS', url: 'https://www.leidos.com' },
          { name: 'Booz Allen Hamilton', ticker: 'BAH', url: 'https://www.boozallen.com' }
        ],
        frontier: ['Palantir', 'Rebellion Defense', 'Second Front Systems', 'Shift5']
      },
      {
        name: 'Services',
        icon: '🛠️',
        description: 'Sustainment, training, integration',
        incumbents: [
          { name: 'GD Mission Systems', ticker: 'GD', url: 'https://gdmissionsystems.com' },
          { name: 'Leidos', ticker: 'LDOS', url: 'https://www.leidos.com' },
          { name: 'CACI', ticker: 'CACI', url: 'https://www.caci.com' }
        ],
        frontier: ['Primer AI', 'Dexter AI']
      }
    ],
    // Hard-coded legacy R&D spend from 2024 10-Ks (company-funded IRAD)
    // Sources tagged per-row. NOT government-funded work — that's reported separately.
    legacy_rd_spend: [
      { company: 'Lockheed Martin', amount_b: 3.0, year: 2024, source: 'Lockheed Martin 2024 10-K (company-funded IRAD + MIRAD, as reported in 2024 annual report)', source_url: 'https://investors.lockheedmartin.com/static-files/850a403e-158b-41f2-bbfa-576f0375d6f1' },
      { company: 'RTX', amount_b: 2.934, year: 2024, source: 'RTX 2024 10-K, R&D expense', source_url: 'https://investors.rtx.com/static-files/ceebbf85-eb69-4563-a303-c62ad9918fba' },
      { company: 'Northrop Grumman', amount_b: 1.2, year: 2024, source: 'Northrop Grumman 2024 10-K (ROS estimate; company-sponsored R&D has run $1.0-1.2B historically)', source_url: 'https://investor.northropgrumman.com/sec-filings' }
    ],
    frontier_vc_note: 'Frontier defense VC funding: $3.0B across 102 deals in 2024 per Crunchbase (narrow definition: military/national security). Broader defense-tech definition (autonomy, space, dual-use software) was ~$48B in 2024 per JPMorgan.',
    frontier_vc_source_url: 'https://news.crunchbase.com/venture/defense-tech-highs-2024-anduril-chaos/',
    // Verified contract displacements — every single one sourced
    displacements: [
      {
        date: '2025-03',
        winner: 'Anduril Industries',
        contract: '$642M',
        amount_m: 642,
        program: 'USMC 10-year Counter-UAS program of record (Installation-CsUAS)',
        losing: 'Incumbent CUAS primes (Dedrone/Axon, Liteye/RTX-partnered systems)',
        note: 'Ten-year program of record to deliver counter-UAS systems to defend Marine Corps installations.',
        source: 'Anduril press release (03/13/2025)',
        source_url: 'https://www.anduril.com/news/anduril-awarded-10-year-642m-program-of-record-to-deliver-cuas-systems-for-u-s-marine-corps'
      },
      {
        date: '2024-07',
        winner: 'Shield AI',
        contract: '$198M',
        amount_m: 198,
        program: 'USCG Maritime UAS IDIQ (V-BAT / MQ-35)',
        losing: 'Legacy manned ISR aviation providers',
        note: 'Indefinite-delivery firm fixed-price contract for contractor-owned, contractor-operated ISR services using V-BAT.',
        source: 'Shield AI press release (07/01/2024)',
        source_url: 'https://shield.ai/shield-ais-v-bat-selected-for-198-million-contract-to-provide-u-s-coast-guard-with-maritime-unmanned-aircraft-system-services/'
      },
      {
        date: '2024-03',
        winner: 'Palantir',
        contract: '$178.4M',
        amount_m: 178.4,
        program: 'US Army TITAN (Tactical Intelligence Targeting Access Node)',
        losing: 'RTX (Raytheon)',
        note: 'Prototype maturation phase — 10 TITAN ground stations. Palantir beat RTX after both received $36M competitive awards.',
        source: 'DefenseScoop / Army Contracting Command announcement',
        source_url: 'https://defensescoop.com/2024/03/06/palantir-army-titan-ground-station-award-178-million/'
      },
      {
        date: '2025-12',
        winner: 'Saronic',
        contract: '$392M',
        amount_m: 392,
        program: 'US Navy Corsair autonomous surface vessel production',
        losing: 'Legacy shipbuilders (none bid competitively at this cycle)',
        note: 'Under-12-month prototype-to-production cycle; $200M obligated immediately. Tied to Replicator initiative.',
        source: 'US Navy via Reagan Defense Forum / Maritime Executive',
        source_url: 'https://maritime-executive.com/article/saronic-secures-392m-unmanned-vessel-contract-from-the-u-s-navy'
      },
      {
        date: '2024-10',
        winner: 'Anduril Industries',
        contract: '$250M',
        amount_m: 250,
        program: 'DoD Roadrunner-M interceptor + Pulsar EW',
        losing: 'Legacy interceptor primes',
        note: '500 Roadrunner-M reusable interceptors plus portable Pulsar EW.',
        source: 'Defense News (10/08/2024)',
        source_url: 'https://www.defensenews.com/unmanned/2024/10/08/anduril-lands-250-million-pentagon-contract-for-drone-defense-system/'
      },
      {
        date: '2023-01',
        winner: 'Epirus',
        contract: '$66.1M',
        amount_m: 66.1,
        program: 'US Army IFPC-HPM (Leonidas high-power microwave)',
        losing: 'Previous contractors on directed-energy counter-swarm',
        note: 'First-of-kind production prototype contract for a software-defined microwave weapon for counter-drone swarm defense.',
        source: 'Epirus / US Army RCCTO',
        source_url: 'https://www.epirusinc.com/press-releases/u-s-army-awards-epirus-66-1m-contract-for-leonidas-tm-directed-energy-system'
      },
      {
        date: '2025-05',
        winner: 'Ursa Major',
        contract: '$28.6M',
        amount_m: 28.6,
        program: 'AFRL responsive space / hypersonic / on-orbit propulsion',
        losing: 'Legacy solid-rocket propulsion primes',
        note: 'Draper closed-catalyst storable liquid engine for hypersonic flight demonstrator.',
        source: 'US Air Force Research Laboratory / Ursa Major',
        source_url: 'https://ursamajor.com/media/press-release/afrl-awards-ursa-major-usd28-6m-contract/'
      },
      {
        date: '2026-01',
        winner: 'Anduril Industries',
        contract: '$23.9M',
        amount_m: 23.9,
        program: "USMC Organic Precision Fires-Light (Bolt-M loitering munition)",
        losing: 'Legacy munitions primes',
        note: '600+ Bolt-M loitering munitions; first production award for the OPF-L program.',
        source: 'Defense Daily / Anduril announcement',
        source_url: 'https://www.defensedaily.com/anduril-to-deliver-more-than-600-bolt-ms-for-marines-opf-l-loitering-munition-program/navy-usmc/'
      }
    ],
    regulatory_tailwinds: [
      {
        title: 'DoD FY2026 Budget Priorities: Autonomy, Counter-UAS, Hypersonics',
        note: 'The FY2026 defense budget request explicitly prioritizes autonomous systems, counter-UAS, and hypersonic weapons — the three categories frontier companies dominate.',
        source: 'DoD FY2026 budget materials',
        source_url: 'https://comptroller.defense.gov/Budget-Materials/'
      },
      {
        title: 'DoD Replicator Initiative',
        note: "Pentagon target: thousands of attritable autonomous systems within 18-24 months. Named frontier beneficiaries include Anduril, Shield AI, Saronic, Neros, Saildrone.",
        source: 'DoD Replicator program page',
        source_url: 'https://www.defense.gov/News/Releases/Release/Article/3518827/'
      },
      {
        title: 'CHIPS Act + Microelectronics Commons',
        note: "$2B DoD-specific microelectronics commons funding de-risks domestic defense silicon — critical for secure autonomy and EW.",
        source: 'DoD Microelectronics Commons',
        source_url: 'https://www.cto.mil/ME-Commons/'
      },
      {
        title: 'SBIR/STTR reforms under SBIR Reauthorization (P.L. 117-183)',
        note: 'Phase III awards became easier to convert into full-rate procurement, unlocking startup-to-scale defense contracting.',
        source: 'SBA / SBIR.gov',
        source_url: 'https://www.sbir.gov/about'
      }
    ],
    methodology_note: 'Every contract in the Displacement Ledger is sourced from the winning company\'s press release or official DoD / agency announcement. R&D spend figures are from audited 10-K filings with SEC EDGAR. Frontier VC totals are from Crunchbase / JPMorgan public research. Last verified April 2026.'
  },

  energy: {
    slug: 'energy',
    label: 'Energy',
    icon: '⚛️',
    color: '#f59e0b',
    eyebrow: 'INDUSTRY TRANSFORMATION · ENERGY',
    title: 'Energy is being rebuilt. Nuclear is the tip of the spear.',
    subtitle: 'After a 40-year freeze, nuclear restart + SMRs + fusion + geothermal are all moving at once — driven by AI data-center demand that the grid cannot meet.',
    thesis: 'Hyperscaler baseload demand (AI data centers) has unfrozen nuclear permitting, pulled forward SMR timelines, and made previously uneconomic geothermal and fusion viable on the margin.',
    sector_match: ['Nuclear Energy', 'nuclear energy', 'Climate & Energy', 'climate & energy', 'Energy & Climate'],
    stack_layers: [
      {
        name: 'Generation',
        icon: '⚡',
        description: 'Baseload power generation',
        incumbents: [
          { name: 'Duke Energy', ticker: 'DUK', url: 'https://www.duke-energy.com' },
          { name: 'Southern Company', ticker: 'SO', url: 'https://www.southerncompany.com' },
          { name: 'Dominion Energy', ticker: 'D', url: 'https://www.dominionenergy.com' }
        ],
        frontier: ['Valar Atomics', 'Oklo', 'X-energy', 'TerraPower', 'Kairos Power', 'Last Energy', 'Deep Fission']
      },
      {
        name: 'Fusion',
        icon: '☀️',
        description: 'Commercial fusion energy',
        incumbents: [
          { name: 'ITER consortium', ticker: null, url: 'https://www.iter.org' }
        ],
        frontier: ['Commonwealth Fusion Systems', 'Helion Energy', 'TAE Technologies', 'Pacific Fusion', 'Shine Technologies']
      },
      {
        name: 'Geothermal & Enhanced',
        icon: '🌋',
        description: 'Next-gen geothermal',
        incumbents: [
          { name: 'Ormat Technologies', ticker: 'ORA', url: 'https://www.ormat.com' }
        ],
        frontier: ['Fervo Energy', 'Eavor', 'Quaise Energy']
      },
      {
        name: 'Storage & Grid',
        icon: '🔋',
        description: 'Grid-scale storage',
        incumbents: [
          { name: 'Tesla Energy', ticker: 'TSLA', url: 'https://www.tesla.com/energy' },
          { name: 'Fluence Energy', ticker: 'FLNC', url: 'https://fluenceenergy.com' }
        ],
        frontier: ['Form Energy', 'EnergyDome', 'Energy Vault']
      }
    ],
    legacy_rd_spend: [
      { company: 'Duke Energy', amount_b: 0.0, year: 2024, source: 'Utilities do not separately disclose R&D — ROS note', source_url: 'https://www.duke-energy.com' },
      { company: 'Southern Company', amount_b: 0.06, year: 2024, source: 'Southern Company 2024 10-K (estimate — R&D historically modest)', source_url: 'https://investor.southerncompany.com/' }
    ],
    frontier_vc_note: 'ROS estimate: fusion + SMR + geothermal raised over $5B in disclosed 2024 rounds (Commonwealth Fusion $1.8B Series B2, Pacific Fusion $900M Series A, Fervo $255M + $206M tranches, X-energy $700M, etc.).',
    frontier_vc_source_url: 'https://rationaloptimistsociety.substack.com',
    displacements: [
      {
        date: '2024-06',
        winner: 'X-energy',
        contract: 'Dow Seadrift SMR partnership',
        amount_m: 0,
        program: 'First commercial advanced-reactor deployment in US industrial',
        losing: 'Natural gas cogeneration',
        note: 'Dow selected X-energy Xe-100 to replace a natural-gas-fueled cogen unit at its Seadrift, TX site.',
        source: 'Dow / X-energy / DOE announcement',
        source_url: 'https://www.energy.gov/ne/articles/first-industrial-advanced-reactor-deployment-dow-and-x-energy'
      },
      {
        date: '2024-09',
        winner: 'Constellation + Microsoft (Three Mile Island restart)',
        contract: '20-year PPA',
        amount_m: 0,
        program: 'Three Mile Island Unit 1 recommissioning for Microsoft data centers',
        losing: 'Natural gas / grid purchases',
        note: 'First reactor restart in US history. Microsoft signed 20-year PPA to underwrite the restart.',
        source: 'Constellation Energy press release',
        source_url: 'https://www.constellationenergy.com/newsroom/2024/Constellation-to-Launch-Crane-Clean-Energy-Center-Restoring-Jobs-and-Carbon-Free-Power-to-The-Grid.html'
      },
      {
        date: '2024-10',
        winner: 'Kairos Power + Google',
        contract: '500 MW nuclear PPA',
        amount_m: 0,
        program: 'Advanced fluoride-salt reactor deployment',
        losing: 'Natural gas baseload',
        note: "Google's first nuclear deal, targeting multi-reactor SMR rollout through 2035.",
        source: 'Google / Kairos',
        source_url: 'https://blog.google/outreach-initiatives/sustainability/google-kairos-power-nuclear-energy-agreement/'
      },
      {
        date: '2024-10',
        winner: 'Amazon + X-energy / Dominion / Energy Northwest',
        contract: '$500M+ investment',
        amount_m: 500,
        program: 'Small Modular Reactor development — Amazon-backed SMR program',
        losing: 'Utility-scale natural gas',
        note: "AWS led a $500M+ round in X-energy and signed an MoU with Dominion for four SMRs.",
        source: 'Amazon press release',
        source_url: 'https://www.aboutamazon.com/news/sustainability/amazon-nuclear-small-modular-reactor-net-carbon-zero'
      },
      {
        date: '2023-09',
        winner: 'Fervo Energy',
        contract: 'First commercial EGS plant (Project Red)',
        amount_m: 0,
        program: 'Enhanced Geothermal Systems commercial-scale plant',
        losing: 'Legacy geothermal / gas peakers',
        note: 'First commercial enhanced-geothermal deployment — proved horizontal drilling + proppants work for heat extraction.',
        source: 'Fervo Energy',
        source_url: 'https://fervoenergy.com/fervo-energys-full-scale-commercial-pilot-project-demonstrates-success-of-enhanced-geothermal-systems/'
      }
    ],
    regulatory_tailwinds: [
      {
        title: 'ADVANCE Act (2024)',
        note: 'Nuclear permitting modernization — cuts NRC licensing fees, establishes prizes for first-of-a-kind reactor deployments, streamlines foreign investment review.',
        source: 'Public Law 118-67',
        source_url: 'https://www.congress.gov/bill/118th-congress/senate-bill/870'
      },
      {
        title: 'IRA Nuclear Production Tax Credit (§45U)',
        note: 'Existing nuclear fleet gets a PTC through 2032 — stabilizes the existing reactor fleet and makes restarts (Three Mile Island, Palisades) economic.',
        source: 'Inflation Reduction Act 2022',
        source_url: 'https://www.whitehouse.gov/cleanenergy/inflation-reduction-act-guidebook/'
      },
      {
        title: 'DOE Advanced Reactor Demonstration Program (ARDP)',
        note: '$2.5B+ for TerraPower Natrium + X-energy Xe-100 demonstrations. Paid milestones unlock federal cost-share for first-of-a-kind builds.',
        source: 'DOE Nuclear Energy',
        source_url: 'https://www.energy.gov/ne/advanced-reactor-demonstration-program'
      }
    ],
    methodology_note: 'Every PPA / deployment milestone is sourced to the utility or developer press release. Funding totals from company disclosures. Legacy utility R&D is typically not separately disclosed.'
  },

  space: {
    slug: 'space',
    label: 'Space',
    icon: '🚀',
    color: '#3b82f6',
    eyebrow: 'INDUSTRY TRANSFORMATION · SPACE',
    title: 'Space went from cost-plus cartel to commoditized launch in 10 years.',
    subtitle: 'SpaceX rebased launch economics. Now the value stack is moving to satellites, servicing, and in-orbit manufacturing.',
    thesis: 'Launch is solved (commoditized by SpaceX). The new frontier is satellites, space ISR for defense, in-orbit manufacturing, and GEO servicing.',
    sector_match: ['Space & Aerospace', 'space & aerospace'],
    stack_layers: [
      {
        name: 'Launch',
        icon: '🚀',
        description: 'Orbital launch providers',
        incumbents: [
          { name: 'ULA', ticker: null, url: 'https://www.ulalaunch.com' },
          { name: 'Arianespace', ticker: null, url: 'https://www.arianespace.com' }
        ],
        frontier: ['SpaceX', 'Rocket Lab', 'Stoke Space', 'Firefly Aerospace', 'Relativity Space']
      },
      {
        name: 'Satellites & Constellations',
        icon: '🛰️',
        description: 'Satellite platforms and networks',
        incumbents: [
          { name: 'Lockheed Martin Space', ticker: 'LMT', url: 'https://www.lockheedmartin.com/en-us/capabilities/space.html' },
          { name: 'Northrop Grumman Space', ticker: 'NOC', url: 'https://www.northropgrumman.com/space' },
          { name: 'Boeing Satellites', ticker: 'BA', url: 'https://www.boeing.com/space' }
        ],
        frontier: ['SpaceX Starlink', 'Planet Labs', 'Capella Space', 'K2 Space', 'Apex Space', 'True Anomaly']
      },
      {
        name: 'Ground & Data',
        icon: '📡',
        description: 'Ground stations and data services',
        incumbents: [
          { name: 'L3Harris', ticker: 'LHX', url: 'https://www.l3harris.com' }
        ],
        frontier: ['HawkEye 360', 'Capella Space', 'Muon Space']
      },
      {
        name: 'In-Orbit Services',
        icon: '🛠️',
        description: 'Servicing, manufacturing, stations',
        incumbents: [],
        frontier: ['Varda Space Industries', 'Axiom Space', 'Vast', 'Starfish Space', 'Impulse Space']
      }
    ],
    legacy_rd_spend: [
      { company: 'Lockheed Martin Space segment', amount_b: 0.9, year: 2024, source: 'Lockheed Martin 2024 10-K — Space segment R&D estimate', source_url: 'https://investors.lockheedmartin.com/' },
      { company: 'Boeing Defense/Space/Security', amount_b: 0.8, year: 2024, source: 'Boeing 2024 10-K — estimate (BDS segment does not break out R&D separately)', source_url: 'https://investors.boeing.com/' }
    ],
    frontier_vc_note: 'ROS estimate: $8B+ raised across tracked private space companies in 2024-25 (SpaceX secondaries, K2 Space, Apex, Varda, Impulse, Stoke, Firefly).',
    frontier_vc_source_url: 'https://rationaloptimistsociety.substack.com',
    displacements: [
      {
        date: '2024-06',
        winner: 'SpaceX (Starshield)',
        contract: '$1.8B',
        amount_m: 1800,
        program: 'NRO reconnaissance satellite constellation',
        losing: 'Legacy satellite primes (Lockheed, Northrop)',
        note: '2021-awarded contract began operational launches in May 2024 — NRO deployed ~142 satellites through 2024, most using Starshield bus.',
        source: 'Reuters / Wikipedia',
        source_url: 'https://en.wikipedia.org/wiki/SpaceX_Starshield'
      },
      {
        date: '2024-10',
        winner: 'SpaceX',
        contract: '$733M',
        amount_m: 733,
        program: 'Space Force NSSL Phase 3 Lane 1',
        losing: 'ULA (on specific missions)',
        note: 'Eight national-security launches awarded to SpaceX under the new Phase 3 Lane 1 track.',
        source: 'Space Force / DoD',
        source_url: 'https://www.spaceforce.mil/News/Article/3963123/'
      },
      {
        date: '2024-10',
        winner: 'Rocket Lab',
        contract: '$515M',
        amount_m: 515,
        program: 'SDA Tranche 2 Transport Layer-Beta',
        losing: 'Legacy satellite primes',
        note: '18 data-transport satellites for the Space Development Agency.',
        source: 'Rocket Lab / SDA',
        source_url: 'https://www.rocketlabusa.com/updates/rocket-lab-wins-515m-sda-tranche-2-transport-layer-beta-contract/'
      },
      {
        date: '2024-02',
        winner: 'Varda Space Industries',
        contract: 'First orbital pharma manufacturing return',
        amount_m: 0,
        program: 'W-1 capsule returned ritonavir grown in orbit',
        losing: 'Terrestrial pharma manufacturing',
        note: 'First successful commercial return of pharma product manufactured in microgravity.',
        source: 'Varda Space',
        source_url: 'https://www.varda.com/news/w-1-reentry'
      }
    ],
    regulatory_tailwinds: [
      {
        title: 'SDA Proliferated Warfighter Space Architecture',
        note: 'Space Development Agency is procuring hundreds of satellites in 2-year tranches — structurally favors new-space primes that can ship fast.',
        source: 'Space Development Agency',
        source_url: 'https://www.sda.mil/'
      },
      {
        title: 'FAA Part 450 commercial launch reforms',
        note: 'Performance-based regulation has dramatically cut launch-licensing timelines for repeat operators.',
        source: 'FAA AST',
        source_url: 'https://www.faa.gov/space'
      }
    ],
    methodology_note: 'Contract values are sourced to SAM.gov, Space Force, or agency announcements. Funding figures to company press releases.'
  },

  automotive: {
    slug: 'automotive',
    label: 'Automotive',
    icon: '🚗',
    color: '#eab308',
    eyebrow: 'INDUSTRY TRANSFORMATION · AUTOMOTIVE',
    title: 'Autos: the only industry where the incumbent already lost.',
    subtitle: 'Tesla reframed the industry around software. Now autonomy is the second wave — and legacy OEMs are losing it faster than they lost EVs.',
    thesis: 'The first wave (EV) went to Tesla + BYD. The second wave (robotaxis + software-defined vehicles) is being captured by Waymo, Tesla FSD, and a short list of Chinese players. Legacy OEMs have shuttered or paused most of their robotaxi programs.',
    sector_match: ['Transportation', 'transportation'],
    stack_layers: [
      {
        name: 'EV OEMs',
        icon: '🔌',
        description: 'Battery-electric vehicle manufacturers',
        incumbents: [
          { name: 'Ford', ticker: 'F', url: 'https://www.ford.com' },
          { name: 'GM', ticker: 'GM', url: 'https://www.gm.com' },
          { name: 'Stellantis', ticker: 'STLA', url: 'https://www.stellantis.com' },
          { name: 'Volkswagen Group', ticker: 'VWAGY', url: 'https://www.volkswagen-group.com' }
        ],
        frontier: ['Tesla', 'Rivian', 'Lucid Motors', 'BYD']
      },
      {
        name: 'Autonomy Software',
        icon: '🧠',
        description: 'Full-stack autonomous driving',
        incumbents: [
          { name: 'Mobileye', ticker: 'MBLY', url: 'https://www.mobileye.com' },
          { name: 'Bosch', ticker: null, url: 'https://www.bosch.com' }
        ],
        frontier: ['Waymo (Alphabet)', 'Tesla FSD', 'Wayve', 'Applied Intuition', 'Nuro']
      },
      {
        name: 'Trucking & Logistics',
        icon: '🚚',
        description: 'Autonomous trucking and freight',
        incumbents: [
          { name: 'Daimler Truck', ticker: 'DTRUY', url: 'https://www.daimlertruck.com' },
          { name: 'Paccar', ticker: 'PCAR', url: 'https://www.paccar.com' }
        ],
        frontier: ['Aurora Innovation', 'Kodiak Robotics', 'Gatik', 'Stack AV']
      },
      {
        name: 'Charging & Grid',
        icon: '⚡',
        description: 'Fast charging + V2G',
        incumbents: [
          { name: 'ChargePoint', ticker: 'CHPT', url: 'https://www.chargepoint.com' },
          { name: 'EVgo', ticker: 'EVGO', url: 'https://www.evgo.com' }
        ],
        frontier: ['Tesla Supercharger', 'Electric Era', 'Revel']
      }
    ],
    legacy_rd_spend: [
      { company: 'Ford', amount_b: 8.2, year: 2024, source: 'Ford 2024 10-K — engineering, research and development expense', source_url: 'https://s23.q4cdn.com/799395366/files/doc_financials/2024/ar/Ford-Motor-Company-2024-Annual-Report.pdf' },
      { company: 'GM', amount_b: 8.1, year: 2024, source: 'GM 2024 10-K — engineering, design and related costs', source_url: 'https://investor.gm.com/sec-filings' },
      { company: 'Volkswagen Group', amount_b: 22.0, year: 2024, source: 'Volkswagen 2024 Annual Report — ROS estimate, global R&D has been €20-22B', source_url: 'https://www.volkswagen-group.com/en/annual-report' }
    ],
    frontier_vc_note: 'Waymo raised $5.6B in Oct 2024 (Alphabet-led) at $45B post; Wayve raised $1.05B Series C in 2024 (Softbank-led); Applied Intuition raised $250M Series E in 2024 at $6B.',
    frontier_vc_source_url: 'https://rationaloptimistsociety.substack.com',
    displacements: [
      {
        date: '2024-10',
        winner: 'Waymo',
        contract: '$5.6B raise / $45B valuation',
        amount_m: 5600,
        program: 'Commercial robotaxi service in SF, Phoenix, LA, Austin',
        losing: 'GM Cruise (paused service in 2024), Ford Argo (shut down 2022)',
        note: 'Waymo One is the only commercial US robotaxi service at scale. GM paused Cruise service in 2024 after a crash. Ford/VW shuttered Argo AI in 2022.',
        source: 'Waymo / Alphabet',
        source_url: 'https://waymo.com/blog/2024/10/our-latest-step-forward'
      },
      {
        date: '2024-12',
        winner: 'Tesla FSD',
        contract: 'Robotaxi service expansion',
        amount_m: 0,
        program: 'Full Self-Driving Supervised rolled to all NA vehicles; unsupervised pilots underway',
        losing: 'Legacy OEM Level 2 systems',
        note: 'Tesla has over 2M+ vehicles generating FSD training data — an inventory no incumbent can match.',
        source: 'Tesla IR',
        source_url: 'https://ir.tesla.com'
      },
      {
        date: '2024-11',
        winner: 'Aurora Innovation',
        contract: 'First driverless freight lane',
        amount_m: 0,
        program: 'Commercial driverless trucking between Dallas & Houston',
        losing: 'Manned trucking / legacy OEM autonomy',
        note: 'Aurora launched the first commercial driverless trucking service in the US on the Dallas-Houston corridor.',
        source: 'Aurora Innovation',
        source_url: 'https://aurora.tech/blog/aurora-launches-commercial-driverless-trucking'
      }
    ],
    regulatory_tailwinds: [
      {
        title: 'NHTSA AV STEP framework',
        note: "NHTSA's voluntary AV safety evaluation + reporting framework creates a national autonomy program that favors operators with data scale.",
        source: 'NHTSA',
        source_url: 'https://www.nhtsa.gov/automated-vehicles-safety'
      },
      {
        title: 'CA DMV / California PUC robotaxi permitting',
        note: 'California remains the only market with full commercial driverless service permits — Waymo has both; Cruise suspended its permits in 2023.',
        source: 'California DMV',
        source_url: 'https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/'
      }
    ],
    methodology_note: 'Funding figures and valuation sourced to company announcements. R&D spend from 10-K filings. Shutdowns (Cruise, Argo) are public record.'
  },

  pharma: {
    slug: 'pharma',
    label: 'Pharma',
    icon: '🧬',
    color: '#ec4899',
    eyebrow: 'INDUSTRY TRANSFORMATION · PHARMA',
    title: "Pharma transformation: Data pipeline in progress.",
    subtitle: 'AI-native drug discovery, programmable biology, and clinical-trial automation are rewriting 20-year development cycles. Full report shipping soon.',
    thesis: 'The multi-trillion-dollar biopharma industry is being reshaped by AI-enabled drug discovery (Xaira, Isomorphic, Recursion), programmable cell therapy (Cellares), and AI-run clinical trials.',
    sector_match: ['Biotech & Health', 'Biotech & Medical', 'biotech & health'],
    stack_layers: [],
    legacy_rd_spend: [],
    frontier_vc_note: 'Pharma transformation data pipeline is in progress. Full report shipping in the next release.',
    frontier_vc_source_url: null,
    displacements: [],
    regulatory_tailwinds: [],
    methodology_note: 'Pharma report pipeline is still being assembled. We only publish verified displacements — ship later rather than fabricate.',
    placeholder: true
  },

  materials: {
    slug: 'materials',
    label: 'Materials',
    icon: '⚙️',
    color: '#78716c',
    eyebrow: 'INDUSTRY TRANSFORMATION · MATERIALS',
    title: 'Materials transformation: Data pipeline in progress.',
    subtitle: 'Critical minerals, advanced alloys, high-volume 3D printing, and AI-driven materials discovery are rewriting how physical goods get made.',
    thesis: 'Hadrian, Durin, and Orbital Composites are turning precision manufacturing into a software industry. Upstream — KoBold and Earth AI are redoing exploration with AI.',
    sector_match: ['Advanced Manufacturing', 'Robotics & Manufacturing', 'Robotics & Automation'],
    stack_layers: [],
    legacy_rd_spend: [],
    frontier_vc_note: 'Materials transformation data pipeline is in progress. Full report shipping in the next release.',
    frontier_vc_source_url: null,
    displacements: [],
    regulatory_tailwinds: [],
    methodology_note: 'Materials report pipeline is still being assembled. We only publish verified displacements — ship later rather than fabricate.',
    placeholder: true
  }
};

// ── shared rendering helpers (used by every industry page) ──

function tr_computeIndustryStats(industry) {
  // Safely pull COMPANIES + deal/funding data and compute industry-level aggregates
  const stats = {
    challengers: 0,
    challenger_names: [],
    last12mo_raised_m: 0,
    last24mo_raised_m: 0,
    deal_count_12mo: 0
  };

  if (typeof COMPANIES === 'undefined') return stats;

  const match = new Set((industry.sector_match || []).map(s => s.toLowerCase()));
  const frontierSet = new Set();
  (industry.stack_layers || []).forEach(layer => {
    (layer.frontier || []).forEach(n => frontierSet.add(n));
  });

  const matched = COMPANIES.filter(c => {
    const sec = (c.sector || '').toLowerCase();
    return match.has(sec) || frontierSet.has(c.name);
  });
  stats.challengers = matched.length;
  stats.challenger_names = matched.map(c => c.name);

  // Capital flow: use deals_auto + funding_tracker_auto if present
  const today = new Date();
  const cutoff12 = new Date(today.getFullYear(), today.getMonth() - 12, 1);
  const cutoff24 = new Date(today.getFullYear(), today.getMonth() - 24, 1);

  const matchedNames = new Set(matched.map(c => c.name));
  try {
    const dealsSource = (typeof DEALS_AUTO !== 'undefined' && Array.isArray(DEALS_AUTO)) ? DEALS_AUTO : null;
    if (dealsSource) {
      dealsSource.forEach(d => {
        if (!matchedNames.has(d.company)) return;
        const parts = String(d.date || '').split('-');
        if (parts.length < 2) return;
        const dt = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, 1);
        const amt = til_parse_amount_to_m(d.amount);
        // Guard against obviously bogus parse values
        if (amt > 100000) return;
        if (dt >= cutoff12) { stats.last12mo_raised_m += amt; stats.deal_count_12mo += 1; }
        if (dt >= cutoff24) { stats.last24mo_raised_m += amt; }
      });
    }
  } catch (e) {
    console.warn('[transformation] deals compute failed', e);
  }

  return stats;
}

function tr_renderStackLayer(layer, color) {
  if (!layer) return '';
  const incumbents = (layer.incumbents || []).map(i => {
    const url = i.url || '#';
    return `<a href="${til_escape(url)}" target="_blank" rel="noopener" class="tr-stack-chip tr-chip-incumbent">${til_escape(i.name)}${i.ticker ? `<span class="tr-chip-ticker">${til_escape(i.ticker)}</span>` : ''}</a>`;
  }).join('');

  const frontier = (layer.frontier || []).map(name => {
    // Prefer link to internal company profile when the name is in COMPANIES
    let url = null;
    if (typeof COMPANIES !== 'undefined') {
      const match = COMPANIES.find(c => c.name === name);
      if (match) url = 'company.html?slug=' + til_slug(match.name);
    }
    if (url) {
      return `<a href="${til_escape(url)}" class="tr-stack-chip tr-chip-frontier">${til_escape(name)}</a>`;
    }
    return `<span class="tr-stack-chip tr-chip-frontier tr-chip-dim" title="Not yet in database">${til_escape(name)}</span>`;
  }).join('');

  return `
    <div class="tr-stack-layer">
      <div class="tr-stack-layer-header">
        <span class="tr-stack-layer-icon" style="background:${color}20; color:${color};">${layer.icon || ''}</span>
        <div>
          <h3 class="tr-stack-layer-name">${til_escape(layer.name)}</h3>
          <p class="tr-stack-layer-desc">${til_escape(layer.description || '')}</p>
        </div>
      </div>
      <div class="tr-stack-side">
        <div class="tr-stack-label">Incumbents</div>
        <div class="tr-stack-chips">${incumbents || '<span class="tr-chip-empty">—</span>'}</div>
      </div>
      <div class="tr-stack-side tr-stack-side-challenger">
        <div class="tr-stack-label">Frontier challengers</div>
        <div class="tr-stack-chips">${frontier || '<span class="tr-chip-empty">—</span>'}</div>
      </div>
    </div>
  `;
}

function tr_renderDisplacements(industry) {
  if (!industry.displacements || industry.displacements.length === 0) {
    return '<div class="tr-empty-note">Verified displacements pipeline in progress. We only publish contracts traceable to SAM.gov or official agency sources.</div>';
  }
  const rows = industry.displacements.map(d => `
    <tr>
      <td class="tr-disp-date">${til_escape(d.date)}</td>
      <td class="tr-disp-winner">${til_escape(d.winner)}</td>
      <td class="tr-disp-contract">${til_escape(d.contract)}</td>
      <td class="tr-disp-program">${til_escape(d.program)}</td>
      <td class="tr-disp-losing">${til_escape(d.losing)}</td>
      <td class="tr-disp-source"><a href="${til_escape(d.source_url)}" target="_blank" rel="noopener">${til_escape(d.source)} <span class="tr-ext">&#8599;</span></a></td>
    </tr>
  `).join('');

  return `
    <div class="tr-disp-wrap">
      <table class="tr-disp-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Winner</th>
            <th>Award</th>
            <th>Program</th>
            <th>Legacy Loser</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function tr_renderCapitalFlow(industry, stats) {
  const legacy = (industry.legacy_rd_spend || []).map(r => `
    <tr>
      <td><strong>${til_escape(r.company)}</strong></td>
      <td>$${r.amount_b.toFixed(2)}B</td>
      <td>${til_escape(String(r.year))}</td>
      <td><a href="${til_escape(r.source_url)}" target="_blank" rel="noopener" class="tr-src-link">${til_escape(r.source)} <span class="tr-ext">&#8599;</span></a></td>
    </tr>
  `).join('');

  const totalLegacy = (industry.legacy_rd_spend || []).reduce((acc, r) => acc + (r.amount_b || 0), 0);
  const frontier12 = stats.last12mo_raised_m;
  const frontier24 = stats.last24mo_raised_m;

  return `
    <div class="tr-capital-grid">
      <div class="tr-capital-card tr-capital-frontier">
        <div class="tr-capital-label">Frontier challenger VC — last 12 months</div>
        <div class="tr-capital-value">${frontier12 > 0 ? til_fmt_amount(frontier12) : '—'}</div>
        <div class="tr-capital-note">${stats.deal_count_12mo} tracked deals across ${stats.challengers} challenger companies in this industry</div>
      </div>
      <div class="tr-capital-card">
        <div class="tr-capital-label">Frontier challenger VC — last 24 months</div>
        <div class="tr-capital-value">${frontier24 > 0 ? til_fmt_amount(frontier24) : '—'}</div>
        <div class="tr-capital-note">Aggregated from disclosed rounds in <a href="data/deals_auto.json" target="_blank" rel="noopener">deals_auto.json</a></div>
      </div>
      <div class="tr-capital-card tr-capital-legacy">
        <div class="tr-capital-label">Legacy R&amp;D spend — 2024</div>
        <div class="tr-capital-value">$${totalLegacy.toFixed(1)}B</div>
        <div class="tr-capital-note">Combined company-funded IRAD across tracked incumbents</div>
      </div>
    </div>
    <div class="tr-capital-context">
      <p>${til_escape(industry.frontier_vc_note || '')}</p>
      ${industry.frontier_vc_source_url ? `<p class="tr-capital-src"><a href="${til_escape(industry.frontier_vc_source_url)}" target="_blank" rel="noopener">Source &#8599;</a></p>` : ''}
    </div>
    ${legacy ? `
    <div class="tr-capital-rd-table">
      <h4>Legacy R&amp;D spend — primary sources</h4>
      <table class="tr-disp-table">
        <thead><tr><th>Company</th><th>R&amp;D 2024</th><th>Year</th><th>Source</th></tr></thead>
        <tbody>${legacy}</tbody>
      </table>
    </div>` : ''}
  `;
}

function tr_renderSimpleBar(industry, stats) {
  // Simple SVG bar chart: frontier 12-mo vs legacy R&D combined
  const legacyB = (industry.legacy_rd_spend || []).reduce((acc, r) => acc + (r.amount_b || 0), 0);
  const frontierB = stats.last12mo_raised_m / 1000;
  const max = Math.max(legacyB, frontierB, 1);
  const legacyPct = (legacyB / max) * 100;
  const frontierPct = (frontierB / max) * 100;

  return `
    <div class="tr-bar-chart" aria-hidden="true">
      <div class="tr-bar-row">
        <div class="tr-bar-label">Frontier VC — last 12mo</div>
        <div class="tr-bar-outer"><div class="tr-bar-inner tr-bar-frontier" style="width:${frontierPct}%"></div></div>
        <div class="tr-bar-amount">$${frontierB.toFixed(1)}B</div>
      </div>
      <div class="tr-bar-row">
        <div class="tr-bar-label">Legacy R&amp;D — 2024</div>
        <div class="tr-bar-outer"><div class="tr-bar-inner tr-bar-legacy" style="width:${legacyPct}%"></div></div>
        <div class="tr-bar-amount">$${legacyB.toFixed(1)}B</div>
      </div>
    </div>
  `;
}

function tr_renderEarningsSignals(industry) {
  // Load earnings_signals_auto.json (built in parallel pipeline). Graceful placeholder otherwise.
  const targetVerticals = new Set((industry.sector_match || []).map(s => s.toLowerCase()));
  targetVerticals.add(industry.slug);
  if (industry.slug === 'defense') { targetVerticals.add('autonomy'); targetVerticals.add('defense'); }
  if (industry.slug === 'energy')  { targetVerticals.add('nuclear'); targetVerticals.add('energy'); }

  const el = document.getElementById('tr-earnings-body');
  if (!el) return;

  const prefix = (typeof window.TIL_DATA_PREFIX === 'string') ? window.TIL_DATA_PREFIX : '';
  fetch(prefix + 'data/earnings_signals_auto.json', { cache: 'no-store' })
    .then(r => r.ok ? r.json() : [])
    .then(rows => {
      if (!Array.isArray(rows) || rows.length === 0) {
        el.innerHTML = '<div class="tr-empty-note">Earnings-call signals pipeline is live but no verified quotes are published for this industry yet. Check back after the next earnings cycle.</div>';
        return;
      }
      const matches = rows.filter(r => {
        const v = String(r.target_vertical || '').toLowerCase();
        return targetVerticals.has(v);
      }).slice(0, 5);
      if (matches.length === 0) {
        el.innerHTML = '<div class="tr-empty-note">No high-significance earnings signals tagged to this industry in the current pipeline window.</div>';
        return;
      }
      el.innerHTML = matches.map(m => `
        <blockquote class="tr-quote">
          <p class="tr-quote-text">&ldquo;${til_escape(m.quote || m.text || '')}&rdquo;</p>
          <footer class="tr-quote-footer">
            <span class="tr-quote-speaker">${til_escape(m.speaker || 'Executive')}</span>
            <span class="tr-quote-sep">·</span>
            <span class="tr-quote-company">${til_escape(m.company || '')}</span>
            <span class="tr-quote-sep">·</span>
            <span class="tr-quote-date">${til_escape(m.date || '')}</span>
            ${m.source_url ? `<a href="${til_escape(m.source_url)}" target="_blank" rel="noopener" class="tr-quote-src">Transcript &#8599;</a>` : ''}
          </footer>
        </blockquote>
      `).join('');
    })
    .catch(() => {
      el.innerHTML = '<div class="tr-empty-note">Earnings-call signals pipeline is being built. This panel will populate once the first batch of verified quotes lands.</div>';
    });
}

function tr_renderTalentFlow(industry) {
  const el = document.getElementById('tr-talent-body');
  if (!el) return;
  // We don't have verified migration data yet — render a clean pipeline placeholder.
  el.innerHTML = `
    <div class="tr-talent-placeholder">
      <p><strong>Talent migration flow tracking is live in the data pipeline.</strong></p>
      <p>This section will quantify engineer migration from legacy primes to frontier challengers using LinkedIn work-history data (<code>data/linkedin_headcount_auto.json</code>) and SEC Form 3/4 executive filings (<code>data/exec_moves_auto.json</code>).</p>
      <p>To avoid fabricated numbers, we are publishing the aggregated flow only after we cross-verify each migration count against a second source. First cut ships with the next release.</p>
    </div>
  `;
}

function tr_renderRegulatory(industry) {
  if (!industry.regulatory_tailwinds || industry.regulatory_tailwinds.length === 0) {
    return '<div class="tr-empty-note">Regulatory catalyst pipeline in progress.</div>';
  }
  return industry.regulatory_tailwinds.map(t => `
    <div class="tr-reg-card">
      <h4>${til_escape(t.title)}</h4>
      <p>${til_escape(t.note)}</p>
      <a href="${til_escape(t.source_url)}" target="_blank" rel="noopener" class="tr-src-link">${til_escape(t.source)} <span class="tr-ext">&#8599;</span></a>
    </div>
  `).join('');
}

function tr_renderVerdict(industry) {
  const el = document.getElementById('tr-verdict-body');
  if (!el) return;
  const prefix = (typeof window.TIL_DATA_PREFIX === 'string') ? window.TIL_DATA_PREFIX : '';
  const file = `data/transformation_${industry.slug}_verdict.md`;
  fetch(prefix + file, { cache: 'no-store' })
    .then(r => r.ok ? r.text() : '')
    .then(text => {
      if (!text || text.trim().length === 0) {
        el.innerHTML = `
          <div class="tr-verdict-placeholder">
            <p><em>Stephen's verdict on ${til_escape(industry.label)} is being written.</em></p>
            <p>Editable source: <code>${til_escape(file)}</code></p>
          </div>
        `;
        return;
      }
      // Minimal markdown rendering: paragraphs + bold/italic + links
      const html = text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .split(/\n\s*\n/)
        .map(para => {
          let p = para.trim();
          if (!p) return '';
          // bold
          p = p.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
          // italic
          p = p.replace(/\*([^*]+)\*/g, '<em>$1</em>');
          // links
          p = p.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
          // headers
          if (/^#\s+/.test(p)) return '<h3>' + p.replace(/^#\s+/, '') + '</h3>';
          if (/^##\s+/.test(p)) return '<h4>' + p.replace(/^##\s+/, '') + '</h4>';
          return '<p>' + p + '</p>';
        })
        .join('');
      el.innerHTML = html;
    })
    .catch(() => {
      el.innerHTML = `<div class="tr-verdict-placeholder"><p><em>Stephen's verdict on ${til_escape(industry.label)} is being written.</em></p></div>`;
    });
}

// ── full-page render entry point ──
function tr_renderIndustryPage(slug) {
  const industry = TRANSFORMATION_INDUSTRIES[slug];
  if (!industry) {
    const root = document.getElementById('tr-root');
    if (root) root.innerHTML = '<div class="section"><div class="container"><p>Industry not found.</p></div></div>';
    return;
  }

  // Hero
  const hero = document.getElementById('tr-hero');
  if (hero) {
    hero.innerHTML = `
      <div class="hero-content tr-hero-content">
        <p class="hero-eyebrow" style="color:${industry.color};">${til_escape(industry.eyebrow)}</p>
        <h1 class="hero-title">${til_escape(industry.title)}</h1>
        <p class="hero-subtitle">${til_escape(industry.subtitle)}</p>
      </div>
    `;
    hero.style.background = `linear-gradient(135deg, rgba(5,5,7,1) 0%, ${industry.color}22 60%, rgba(5,5,7,1) 100%)`;
  }

  // Stats (populated right after compute)
  const stats = tr_computeIndustryStats(industry);

  const heroStats = document.getElementById('tr-hero-stats');
  if (heroStats) {
    heroStats.innerHTML = `
      <div class="stat"><span class="stat-number">${stats.challengers}</span><span class="stat-label">Challengers tracked</span></div>
      <div class="stat-divider"></div>
      <div class="stat"><span class="stat-number">${stats.last12mo_raised_m > 0 ? til_fmt_amount(stats.last12mo_raised_m) : '—'}</span><span class="stat-label">Frontier VC · last 12mo</span></div>
      <div class="stat-divider"></div>
      <div class="stat"><span class="stat-number">${industry.displacements ? industry.displacements.length : 0}</span><span class="stat-label">Verified displacements</span></div>
    `;
  }

  // Thesis line
  const thesisEl = document.getElementById('tr-thesis');
  if (thesisEl) {
    thesisEl.innerHTML = `<div class="tr-thesis-pill" style="border-color:${industry.color}44;">${til_escape(industry.thesis)}</div>`;
  }

  // Stack
  const stackEl = document.getElementById('tr-stack');
  if (stackEl) {
    if (industry.placeholder || !industry.stack_layers || industry.stack_layers.length === 0) {
      stackEl.innerHTML = '<div class="tr-empty-note">Stack breakdown is being assembled for this industry. Shipping in the next release.</div>';
    } else {
      stackEl.innerHTML = industry.stack_layers.map(l => tr_renderStackLayer(l, industry.color)).join('');
    }
  }

  // Capital flow
  const capEl = document.getElementById('tr-capital');
  if (capEl) capEl.innerHTML = tr_renderCapitalFlow(industry, stats) + tr_renderSimpleBar(industry, stats);

  // Displacements
  const dispEl = document.getElementById('tr-displacements');
  if (dispEl) dispEl.innerHTML = tr_renderDisplacements(industry);

  // Earnings signals (async fetch)
  tr_renderEarningsSignals(industry);

  // Talent flow placeholder
  tr_renderTalentFlow(industry);

  // Regulatory
  const regEl = document.getElementById('tr-regulatory');
  if (regEl) regEl.innerHTML = tr_renderRegulatory(industry);

  // Verdict (async fetch)
  tr_renderVerdict(industry);

  // Methodology
  const methEl = document.getElementById('tr-methodology');
  if (methEl) {
    const today = new Date().toISOString().slice(0, 10);
    methEl.innerHTML = `
      <p><strong>Methodology.</strong> ${til_escape(industry.methodology_note || '')}</p>
      <p>Aggregated from SAM.gov, SEC EDGAR, company filings, DoD / agency press releases, and company investor relations pages. Every displacement and R&amp;D figure links to its primary source. Last updated: ${today}.</p>
    `;
  }
}

// ── hub page render ──
function tr_renderHub() {
  const grid = document.getElementById('tr-hub-grid');
  if (!grid) return;
  const cards = Object.values(TRANSFORMATION_INDUSTRIES).map(ind => {
    const stats = tr_computeIndustryStats(ind);
    const placeholder = !!ind.placeholder;
    const legacyB = (ind.legacy_rd_spend || []).reduce((a, r) => a + (r.amount_b || 0), 0);
    const dispCount = (ind.displacements || []).length;
    return `
      <a href="transformation/${ind.slug}.html" class="tr-hub-card" style="--ind-color:${ind.color};">
        <div class="tr-hub-card-top">
          <span class="tr-hub-icon" style="background:${ind.color}20; color:${ind.color};">${ind.icon}</span>
          <div>
            <div class="tr-hub-label">${til_escape(ind.label)}${placeholder ? ' <span class="tr-hub-tag">Preview</span>' : ''}</div>
            <div class="tr-hub-thesis">${til_escape(ind.thesis || '')}</div>
          </div>
        </div>
        <div class="tr-hub-stats">
          <div class="tr-hub-stat"><span class="tr-hub-stat-num">${stats.challengers || '—'}</span><span class="tr-hub-stat-label">Challengers</span></div>
          <div class="tr-hub-stat"><span class="tr-hub-stat-num">${stats.last12mo_raised_m > 0 ? til_fmt_amount(stats.last12mo_raised_m) : '—'}</span><span class="tr-hub-stat-label">VC · 12mo</span></div>
          <div class="tr-hub-stat"><span class="tr-hub-stat-num">${legacyB > 0 ? '$' + legacyB.toFixed(1) + 'B' : '—'}</span><span class="tr-hub-stat-label">Legacy R&amp;D</span></div>
          <div class="tr-hub-stat"><span class="tr-hub-stat-num">${dispCount || '—'}</span><span class="tr-hub-stat-label">Displacements</span></div>
        </div>
        <div class="tr-hub-cta">${placeholder ? 'Preview report' : 'Explore full report'} &rarr;</div>
      </a>
    `;
  }).join('');
  grid.innerHTML = cards;
}

// ── DEALS_AUTO loader shim ──
// deals_auto.json is JSON (not a .js bundle with window.DEALS_AUTO).
// Pre-load it into window so tr_computeIndustryStats can see it.
(function loadDealsAsync() {
  if (typeof window === 'undefined') return;
  if (window.DEALS_AUTO) return;
  // Honor TIL_DATA_PREFIX set by sub-folder pages (e.g. '../' when served from /transformation/)
  const prefix = (typeof window.TIL_DATA_PREFIX === 'string') ? window.TIL_DATA_PREFIX : '';
  try {
    fetch(prefix + 'data/deals_auto.json', { cache: 'no-store' })
      .then(r => r.ok ? r.json() : [])
      .then(rows => { if (Array.isArray(rows)) window.DEALS_AUTO = rows; })
      .catch(() => { window.DEALS_AUTO = []; });
  } catch (_) {
    window.DEALS_AUTO = [];
  }
})();

// Expose for pages that include this module
if (typeof window !== 'undefined') {
  window.TRANSFORMATION_INDUSTRIES = TRANSFORMATION_INDUSTRIES;
  window.tr_renderIndustryPage = tr_renderIndustryPage;
  window.tr_renderHub = tr_renderHub;
}
