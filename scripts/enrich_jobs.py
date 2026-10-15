#!/usr/bin/env python3
"""
Jobs enrichment for the Innovators League jobs board (v2).

Reads the raw ATS pull (data/jobs_raw.json) and derives the facets the
board filters on, because the ATS "department" field is useless (65% of
rows say "General") while the titles carry the signal.

Per job it adds:
  roleFamily            ~22 families from title keywords (manufacturing,
                        software, ml, mechanical, electrical, firmware,
                        propulsion, systems, controls, test, science,
                        supply, program, operations, fde, it, product,
                        data, sales, gna, leadership, general, other)
  level                 intern | junior | mid | senior | staff | director
  metro / metros        sf | la | tx | sea | den | dc | nyc | bos | us |
                        remote | intl  (a job can sit in several)
  sector                re-resolved from data.js (the fetcher's regex
                        mis-mapped ~2,700 rows to "tech")
  isHardTech            False for pure-software companies (AI & Software,
                        Consumer Tech sectors; Stripe, Anthropic, ...)
  postedDaysAgo, stale  posted = first-published date where the ATS gives
                        one; stale = no ATS activity (update) in 90 days
  companyRecentlyRaised a round in data/deals_auto.json or data.js
                        FUNDING_TRACKER within the last 90 days
  il30                  company is on the INNOVATORS_LEAGUE_30 list
  clearanceLikely       title, or ATS description when fetched, says an
                        active / TS-SCI / Secret clearance is required
  usPersonLikely        description says U.S. person / ITAR
  trades, internSummer2027, generalApplication   shelf flags
  salaryMin/Max/Currency, salarySource   the fetcher's structured range, else
                        the ATS compensation block (Ashby, Lever), else the
                        range written in the posting text ("posting"); hourly
                        rates are annualised at 2,080 h ("...-hourly")
  yearsExperience, levelSource   "N+ years" from the text sets the level only
                        where the title carried no level word
  applicationDeadline, closingSoon   a dated deadline in the posting (or the
                        Greenhouse field, which is never set) within 14 days
  groupId, groupSize, groupPrimary, groupLocations   per-location clones of
                        one role at one company fold into the newest posting
  newThisWeek           the role's first posting is <= 7 days old (a new
                        location added to an old role does not count)
  companySurge          company posted >= 5 more roles in the last 14 days
                        than in the 14 before, and at least 1.5x as many

Outputs:
  data/jobs_enriched.json      full records (compact JSON)
  data/jobs_enriched.js        columnar version for the page (window.JOBS_V2)
  data/jobs_company_index.js   {company: [postings, roles, newest, surge, 14d]}
                               for company pages (window.JOBS_COMPANY_INDEX)
  data/jobs_history.json       new postings per day per company (120 days),
                               the series behind the hiring-surge shelf
  data/jobs_desc_signals.json  description cache (written by the fetch pass):
                               clearance / US-person flags, Greenhouse
                               first_published, salary, deadline, years

Deterministic: same inputs + same --today -> byte-identical outputs. The
only network step (the description pass, on by default) refreshes a
per-board cache keyed on the board's job-id set, so boards without new
postings are not re-downloaded; with --no-fetch nothing touches the network.

Usage:
  python3 scripts/enrich_jobs.py                 # enrich + refresh desc cache
  python3 scripts/enrich_jobs.py --no-fetch      # offline, cache as-is
  python3 scripts/enrich_jobs.py --today 2026-10-15
"""

import argparse
import concurrent.futures
import hashlib
import html
import json
import re
import sys
import time
from collections import Counter, OrderedDict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

RAW_PATH = DATA / "jobs_raw.json"
STATS_PATH = DATA / "jobs_stats.json"
DEALS_PATH = DATA / "deals_auto.json"
DATA_JS_PATH = ROOT / "data.js"
MASTER_LIST_PATH = ROOT / "scripts" / "company_master_list.js"
CACHE_PATH = DATA / "jobs_desc_signals.json"
HISTORY_PATH = DATA / "jobs_history.json"
OUT_JSON = DATA / "jobs_enriched.json"
OUT_JS = DATA / "jobs_enriched.js"
OUT_INDEX_JS = DATA / "jobs_company_index.js"

STALE_DAYS = 90
RAISED_WINDOW_DAYS = 90
NEW_DAYS = 7                 # "new this week"
CLOSING_DAYS = 14            # "closing soon": stated application deadline within this many days
SURGE_WINDOW_DAYS = 14       # "hiring surge": postings in the last 14 days vs the 14 before
SURGE_MIN_EXTRA = 5
SURGE_RATIO = 1.5
HISTORY_KEEP_DAYS = 120
CACHE_VERSION = 3            # v3 rows: [flags, firstPublished, salaryMin, salaryMax, currency, salaryKind, deadline, years]
TODAY_FALLBACK = datetime.now(timezone.utc).date()


# ─────────────────────────────────────────────────────────────────────────────
# Taxonomies
# ─────────────────────────────────────────────────────────────────────────────

FAMILIES = OrderedDict([
    ("manufacturing", "Manufacturing & technicians"),
    ("software",      "Software"),
    ("ml",            "ML, autonomy & robotics"),
    ("mechanical",    "Mechanical, structures & thermal"),
    ("electrical",    "Electrical, RF & power"),
    ("firmware",      "Firmware, embedded & avionics"),
    ("propulsion",    "Propulsion, GNC & mission"),
    ("systems",       "Systems engineering"),
    ("controls",      "Controls & automation"),
    ("test",          "Test, quality & safety"),
    ("science",       "Science & R&D"),
    ("supply",        "Supply chain & logistics"),
    ("program",       "Program & project management"),
    ("operations",    "Operations & facilities"),
    ("fde",           "Field & forward-deployed"),
    ("it",            "IT & corporate systems"),
    ("product",       "Product & design"),
    ("data",          "Data & analytics"),
    ("sales",         "Sales, BD & marketing"),
    ("gna",           "Finance, legal, people & admin"),
    ("leadership",    "Leadership (VP+)"),
    ("general",       "General application"),
    ("other",         "Other"),
])

LEVELS = OrderedDict([
    ("intern",   "Intern"),
    ("junior",   "New grad / junior"),
    ("mid",      "Mid"),
    ("senior",   "Senior"),
    ("staff",    "Staff / principal / lead"),
    ("director", "Director+"),
])

METROS = OrderedDict([
    ("sf",     "SF Bay Area"),
    ("la",     "Los Angeles"),
    ("tx",     "Austin / Texas"),
    ("sea",    "Seattle"),
    ("den",    "Denver / Colorado"),
    ("dc",     "Washington DC"),
    ("nyc",    "New York"),
    ("bos",    "Boston"),
    ("us",     "Other US"),
    ("london", "London"),
    ("munich", "Munich / Bavaria"),
    ("paris",  "Paris"),
    ("toronto", "Toronto"),
    ("telaviv", "Tel Aviv / Israel"),
    ("intl",   "Other international"),
    ("remote", "Remote"),
])

STAGE_GROUPS = OrderedDict([
    ("seed",    "Pre-seed / Seed"),
    ("a",       "Series A"),
    ("b",       "Series B"),
    ("c",       "Series C"),
    ("d",       "Series D+ / Growth"),
    ("public",  "Public"),
    ("other",   "Undisclosed / Other"),
])

# Database sectors that mean "pure software" for the hard-tech switch.
SOFTWARE_SECTORS = {"AI & Software", "Consumer Tech"}

# Job-board companies that are not in data.js (removed, or never added):
# sector label as data.js spells it, hard-tech flag, funding stage ("" = unknown).
NON_DB_COMPANIES = {
    "Stripe":         ("AI & Software", False, "Late Stage"),
    "Anthropic":      ("AI & Software", False, "Late Stage"),
    "Flexport":       ("Infrastructure & Logistics", False, "Series E"),
    "Scale AI":       ("AI & Software", False, "Late Stage"),
    "ElevenLabs":     ("AI & Software", False, "Series C"),
    "Together AI":    ("AI & Software", False, "Series B"),
    "Runpod":         ("AI & Software", False, "Series A"),
    "SF Compute":     ("AI & Software", False, ""),
    "Wispr AI":       ("AI & Software", False, ""),
    "Axion":          ("AI & Software", False, ""),
    "Hive AI":        ("AI & Software", False, "Series D"),
    "Labelbox":       ("AI & Software", False, "Series D"),
    "Watershed":      ("AI & Software", False, "Series C"),
    "Meter":          ("AI & Software", False, "Series C"),
    "Ephemeris Net":  ("Space & Aerospace", True, ""),
    "Solestial":      ("Space & Aerospace", True, ""),
    "Wraithwatch":    ("Defense & Security", True, ""),
    "Electric Air":   ("Climate & Energy", True, ""),
    "Eden Geopower":  ("Climate & Energy", True, ""),
    "David Energy":   ("Climate & Energy", True, ""),
}

# master-list short sector codes -> data.js sector labels (fallback only)
MASTER_SECTOR_LABELS = {
    "space": "Space & Aerospace", "aerospace": "Space & Aerospace",
    "defense": "Defense & Security", "climate": "Climate & Energy",
    "energy": "Climate & Energy", "battery": "Climate & Energy",
    "hydrogen": "Climate & Energy", "fusion": "Nuclear Energy",
    "nuclear": "Nuclear Energy", "robotics": "Robotics & Manufacturing",
    "manufacturing": "Robotics & Manufacturing", "biotech": "Biotech & Health",
    "medtech": "Biotech & Health", "chips": "Chips & Semiconductors",
    "semiconductor": "Chips & Semiconductors", "sensors": "Chips & Semiconductors",
    "ai": "AI & Software", "quantum": "Quantum Computing",
    "autonomous": "Drones & Autonomous", "transportation": "Transportation",
    "construction": "Housing & Construction", "housing": "Housing & Construction",
    "ocean": "Ocean & Maritime", "infrastructure": "Infrastructure & Logistics",
    "consumer": "Consumer Tech", "mining": "Climate & Energy",
}


# ─────────────────────────────────────────────────────────────────────────────
# Title rules
# ─────────────────────────────────────────────────────────────────────────────

def _rx(pattern):
    return re.compile(pattern, re.I)


# Evaluated in order; first hit wins. Distinctive business functions first,
# then the engineering domains (specific before generic), then catch-alls.
FAMILY_RULES = [
    ("general", _rx(r"general application|general interest|general (open )?call|general (job )?application|talent (network|pool|community)|future opportunit|open application|open applications|don'?t see (a role|what)|resume submi|speculative|not seeing (a|the) role|join our talent|evergreen|express(ion of)? interest|dream job|new adventure|future teammate|interested in (an? )?(internship|future)|skillbridge|join our team|pitch your own|career day|amazing candidate|opportunistic|open role|spontaneous application")),
    ("leadership", _rx(r"\b(s?vp|evp|avp)\b|vice president|\bchief\b|\bc[a-z]{1,2}o\b|\bpresident\b|general manager|managing director|\bcountry manager|\bfounder")),
    ("fde", _rx(r"forward[- ]deployed|\bfde\b|field (engineer|service|applications?|support|technician|deployment|ops|operations|rep|tech)|deployment (engineer|strategist|lead|manager|specialist|technician|operations)|customer engineer|solutions? engineer|implementation (engineer|manager|specialist|lead)|\bfsr\b|field (electrician|installer|commissioning)|commissioning engineer|install(ation)? (manager|technician|engineer|lead)|mission (lead|strategist)\b|applications? engineer")),
    ("it", _rx(r"\bit\b|help ?desk|service desk|sysadmin|systems? administrator|desktop support|network (engineer|administrator|architect|technician|operations)|corporate (network|engineering|systems|security)|endpoint|workplace tech|client platform|saas admin|salesforce (admin|engineer|developer)|\berp\b|netsuite|\bjamf\b|\bmdm\b|identity (and|&) access|\biam\b|\bokta\b|intune|\bwindows (system|server)|linux (systems? )?administrator|security operations center|\bsoc analyst|\badministrator\b|enovia|teamcenter|\bplm (admin|specialist|engineer)|business systems")),
    ("program", _rx(r"program manager|project manager|\btpm\b|technical program|program management|project management|\bpmo\b|project engineer|program (lead|director|analyst|coordinator|engineer|specialist|associate)|project (lead|coordinator|controls|director|delivery)|\bscrum|delivery manager|engineering manager|manager, engineering|\bprogram\b|capital projects?")),
    ("supply", _rx(r"supply chain|procurement|sourcing|\bbuyer\b|logistic|\bplanner\b|\bplanning\b|inventory|material (manager|planner|coordinator|specialist|analyst|program|flow|control|handler)|materials (manager|planner|coordinator|specialist|analyst|program|management)|supplier|purchasing|warehouse|shipping|receiving|\bimport\b|\bexport\b|customs|\bfleet\b|fulfillment|\bscheduler|demand (planner|planning)|\bmrp\b|\bs&op\b|\bkitting|\bstockroom|supply (manager|lead|specialist|analyst)|global supply|order management|approvisionnement")),
    ("operations", _rx(r"production support|ops support|engineering support|facilities support|manufacturing support")),
    ("electrical", _rx(r"pcb designer|electrical designer|photonic|layout designer|\bic designer|circuit designer")),
    ("mechanical", _rx(r"cad designer|bim designer|mechanical designer|piping designer|drafter")),
    ("sales", _rx(r"account executive|\bsales\b(?! compensation)(?! tax)|business development|customer success|\bsdr\b|\bbdr\b|account manager|\bcampaign")),
    ("gna", _rx(r"financ|accountant|accounting|\bfp&a\b|treasury|\btax\b|payroll|legal|counsel|paralegal|attorney|contracts? (manager|administrator|specialist|negotiator|analyst|management)|recruit|talent (acquisition|partner|sourcer|operations|programs)|\bsourcer\b|people (ops|operations|partner|team|experience|programs|analyst|generalist)|head of people|\bhr\b|human resources|office (manager|coordinator|assistant)|executive assistant|administrative|receptionist|\badmin\b|workplace|security (officer|guard|manager|specialist|analyst|operations|lead|director)|head of security|\bguard\b|regulatory affairs|compliance|\bgrc\b|\baudit|investor relations|benefits|compensation|learning (&|and) development|controller|bookkeep|\bbilling\b|\bequity (admin|plan)|stock (admin|plan)|\bcorporate development|\bstrategy\b|\bstrategic finance|\bbusiness operations|\bbizops|\bchief of staff|\bexecutive (business|operations)|\bimmigration|\bprivacy|\brisk (manager|operations|analyst|lead)|\binsurance|\bprotective (services|intelligence)|\bphysical security|\bsafety officer|\btrade compliance|\bexport compliance|\bgovernment contracts?|\bgrants?\b|\bfellow\b|\bphilanthrop|government (relations|affairs)|public (policy|affairs)|\bpolicy\b|advocacy|external affairs|\bassistant\b|\bexpense\b|\btrainer\b|\btraining (specialist|manager|coordinator)|transaction|buchhalt|\bcredit\b|onboarding|\bfraud|\btalent\b|\benablement\b|\bpeople\b|\blawyer|\bcost management")),
    ("sales", _rx(r"\bsales\b|account (executive|manager|director|lead|strategist|specialist|management)|business development|\bbd\b|customer success|partnership|alliances|go[- ]to[- ]market|\bgtm\b|marketing|\bgrowth\b|\brevenue\b|solutions? (consultant|architect)|pre[- ]?sales|commercial|\bsdr\b|\bbdr\b|territory|\bchannel\b|customer (support|experience|service|operations|advocate|care|engineer)|communications?(?! ?(/|engineer|systems?|dsp|payload|link))|public relations|\bpr\b|\bbrand(ing)?\b|\bpartner\b|\bcontent\b|community|\bevents?\b|demand gen|evangelist|\bcapture\b|proposal|strategic (accounts?|partners)|\badvisory|\bconsultant|\bsupport (engineer|specialist|analyst)|technical (account|support)|\bcustomer|\bclient\b|\bpartner (manager|engineer|engagement)|strategist|developer (relations|education|advocate)|\bdevrel\b|\bsupport\b")),
    ("product", _rx(r"product (manager|owner|lead|designer|design|marketing|management|operations|analyst|strategist|specialist|engineer|technical)|head of product|director of product|\bproduct$|human factors|\bdesigner\b|\bux\b|\bui\b|user experience|industrial design|creative|visual design|brand design|design (lead|manager|director)|technical writer|\bdocumentation|content designer|motion design")),
    ("data", _rx(r"\bdata (engineer|scientist|analyst|science|analytics|platform|infrastructure|architect|quality|manager|operations|annotation|labeling|curator|ops)|analytics|\banalyst\b|business intelligence|\bbi\b|statistic|\binsights\b|\bgeospatial|\bgis\b")),
    ("firmware", _rx(r"firmware|embedded|avionics|flight software|\brtos\b|bare[- ]metal|microcontroller|\bfpga\b|hardware/software|hw/sw|\bboard support|device driver|\bbsp\b")),
    ("ml", _rx(r"machine learning|\bml\b|deep learning|computer vision|\bperception\b|\bautonomy\b|behavior (planning|prediction)|motion planning|\bnlp\b|\bllm|\bagents?\b|reinforcement|foundation model|neural|\bcv\b|research (scientist|engineer)|\bmts\b|member of technical staff|applied scientist|robot learning|robotics (engineer|software)|\bmlops\b|\balgorithm engineer|model (training|evaluation)|\balignment\b|interpretability|red team|\bgpu kernel|\binference\b|\bai (engineer|researcher|scientist|research|infrastructure|platform|architect|deployment|solutions?|systems?|developer|product|training|tooling)|\b(applied|generative|agentic|conversational|physical|frontier|enterprise) ai\b|\bai\b.*\b(engineer|scientist|researcher|research|architect|developer|infrastructure|platform)\b|safeguards|post-training|pre-training|\btraining\b.*\binfrastructure")),
    ("propulsion", _rx(r"propulsion|\bgnc\b|guidance|navigation|aerodynamic|\baero\b|aerothermal|flight dynamics|flight (test|operations|ops|sciences?)|mission (ops|operations|design|planning|manager|director|integration|assurance|engineer|analyst|success)|orbital|trajectory|astrodynamics|launch (operations|engineer|director|site|conductor|pad|systems?)|turbomachinery|turbopump|combustion|rocket|\bengines?\b|spacecraft operations|satellite operations|\bpilot\b|\bastronaut|range (operations|safety)|recovery operations|ordnance|energetics|warhead|interceptor|hypersonic|ballistic|\bflight (controls?|engineer)|vehicle integration|stage (integration|operations)|kinetics|thruster|\btca\b")),
    ("systems", _rx(r"systems? engineer|systems? architect|systems? integration|integration (engineer|lead|manager)|integration (&|and) test|\bsysml\b|requirements engineer|mission systems|system design|systems? design engineer|\bmbse\b|\bv&v\b|configuration (engineer|management|manager)|certification engineer|airworthiness|chief engineer|systems? development")),
    ("controls", _rx(r"controls? engineer|controls? (software|systems?|design|technician|integration)|\bplc\b|automation (engineer|technician|specialist|&|and)|controls? (&|and) automation|automation (&|and) controls|\bscada\b|instrumentation|\bi&c\b|\bi&e\b|motion control|protection (and|&) control|\bhmi\b|(?<!thermal )(?<!attitude )control systems?|\bcontrols\b")),
    ("electrical", _rx(r"design verification|physical verification|post-silicon|\brtl\b|\basic\b|rfic|mmic|\brf\b|antenna|power electronics|\bpcb\b|signal integrity|physical design|\bserdes|\bdft\b|\bdigital design|\bdevice engineer|\becad")),
    ("test", _rx(r"\btest\b|testing|quality|\bqa\b|reliability|\bsafety\b|\behs\b|\bhse\b|verification|validation|certification|calibration|compliance engineer|\bdvt\b|\bevt\b|\bpvt\b|failure analysis|\bfmea\b|radiation safety|health physic|nuclear safety|licensing engineer|quality assurance|\bqms\b|\bsqe\b|supplier quality")),
    ("manufacturing", _rx(r"manufactur|production|technician|\btech\b|machinist|welder|welding|\bcnc\b|assembl|fabricat|industrial engineer|process (engineer|technician|operator)|tooling|additive|3d print|shop floor|\boperator\b|\bshift\b|\bmfg\b|cell lead|line lead|composite|\bpaint|electrician|\bmechanic\b|coating|machining|foundry|casting|forging|stamping|\bweld\b|material handler|warehouse associate|production associate|\bplumber|pipefitter|millwright|\brigger|\bcrane|forklift|\bcarpenter|superintendent|\bdrafter|\bpcba\b|\bsmt\b|\bnde\b|\bndt\b|inspector|metrology|\bcmm\b|quality (technician|inspector|control)|\bqc\b|lab technician|technologist|build (engineer|technician)|lead technician|equipment (technician|engineer|maintenance)|maintenance (technician|engineer|mechanic|planner|supervisor)|facilities (technician|electrician|engineer)|\bhvac\b|\bdriver\b|\bcdl\b|mechaniker|mechatroniker|techniker|monteur|opérateur|operateur|technicien|schweiß|elektriker|\bfitter\b|\binstaller\b|journeyman|apprentice|tool ?maker|\bdfma?\b|\bbuild (manager|lead|supervisor|technician|operations)|starship build|\blager|\bait\b|drywall|\bhanger\b")),
    ("mechanical", _rx(r"\bmechanical\b(?!.*\belectrical)|\bstructural\b|\bstructures\b|\bthermal\b|\bfluids?\b|\bmechanisms?\b|\bcfd\b|\bthrusters?\b|prototyping engineer|design release engineer|\bplumbing engineer|\bdrilling engineer|mineral processing")),
    ("electrical", _rx(r"electrical|\bee\b|\brf\b|rfic|mmic|radio frequency|antenna|power electronics|\bpcb\b|\banalog|mixed[- ]signal|electronics?\b|photonic|optical|opto|\blaser|\basic\b|\bsoc\b|silicon|circuit|battery|\bharness|wireless|microwave|\bdsp\b|electromagnetic|power systems?|high voltage|\bmotor\b|\bmotors\b|\binverter|\bbms\b|\bcells?\b|electrochem|\bpower (engineer|conversion|supply|integrity|delivery)|signal integrity|\bphy\b|\bserdes|\brtl\b|design verification|physical design|\bdft\b|\bsta\b|\btiming\b|\bemc\b|\bemi\b|\bvlsi|\bchip|\bdie\b|\bwafer|\bfab\b|lithograph|\bepitax|\bcmos|package (design|engineer)|packaging (engineer|lead)|advanced packaging|\bsubstation|\bgrid\b|\btransformer|\bswitchgear|\bsolar\b|\bphotovolta|\bhardware\b|radiation effects|layout (designer|engineer)|clock (design|distribution)|\bcpu\b|\bgpu\b|\bsemiconductor|\bmicroelectron|\belectro-?optic|\bsensor|\bradar\b|\blidar\b|\bimaging\b|\bcamera")),
    ("mechanical", _rx(r"mechanical|\bstructur|thermal|\bfluids?\b|\bcad\b|mechanism|materials? (engineer|scientist|science)|metallurg|\bstress\b|\bloads\b|\bfea\b|optomech|(?<!physical )(?<!asic )(?<!ic )(?<!rf )(?<!pcb )(?<!digital )(?<!analog )(?<!layout )(?<!circuit )design engineer|product development engineer|\bpiping\b|\bthermo|cryogenic|heat transfer|\bvalve|fluid systems|hydraulic|pneumatic|\bgse\b|ground support equipment|\bchassis|\bsuspension|body in white|vehicle (design|engineer|dynamics)|\bweight|mass properties|\bdrivetrain|\bgearbox|\btribolog|\bcivil\b|\bplant design|\bhvac design|\bmechatronic|\bcomposites? engineer|\bmanufacturing design|\bdynamics engineer|\bvibration|\bacoustic")),
    ("science", _rx(r"scientist|chemist|physicist|biolog|\bphd\b|postdoc|research associate|\blab (manager|lead|director|head|technician|tech|scientist|operations)|laboratory|\bchemistry\b|microbiolog|geolog|geophysic|geotherm|nuclear engineer|reactor|\bfuel (cycle|engineer|fabrication)|\bplasma|\bfusion\b|neuroscien|clinical|bioinformatic|genomic|protein|\bassay|formulation|process development|immunolog|oncolog|pharmacolog|pharmacist|toxicolog|histolog|\bcell (line|culture)|\bmedical\b|\bphysician|\bnurse|psychiatr|\btherapist|\bclinician|\bveterinar|animal|drug discovery|\bomics\b|\bcomputational (biolog|chem)|\bresearch\b|\bquantum\b|cryptograph|\bphysics\b|\bmetrolog|\bexploration|\beconomist|\bresearcher|shielding|radiation (effects|engineer)|neutronic|dosimetr|antibody|\bengineering (biolog|chem)")),
    ("software", _rx(r"software|\bswe\b|full[- ]?stack|back[- ]?end|front[- ]?end|\bweb\b|devops|site reliability|\bsre\b|\bcloud\b|platform engineer|infrastructure engineer|developer|\bdevex|kubernetes|distributed systems|compiler|\bhpc\b|simulation|\bsecurity engineer|application security|product security|\bcyber|\bapi\b|\bmobile (engineer|developer)|\bios\b|android|\bplatform\b|\bbackend|\bfrontend|\bobservability|\bdatabase|\bengineer, (platform|infrastructure|core)|\bcomputing\b|\bsystems software|\bnetworking\b|\bprogrammer|c\+\+|\bpython\b|\brust\b|\bgolang\b|\bjava\b|founding engineer|bring-?up engineer|\barchitecture engineer|performance (engineer|modeling)|devsecops|\bsalesforce\b|triage")),
    ("operations", _rx(r"operations|\bops\b|facilities|\bfacility\b|construction|site (manager|lead|supervisor|director)|maintenance|\bplant\b|environmental|sustainability|real estate|janitor|custodian|cafeteria|\bchef\b|\bcook\b|\bbarista|\bestimator|\bporter\b|launch site|\brange\b|\bsite\b|\bspecialist\b|\bcoordinator\b|\bsupervisor\b|\bassociate\b|\bgeneralist\b|\bmanager\b|\blead\b|\bdirector\b|\bhead of\b")),
    # long-tail rules (evaluated after the main domains, before the bare-engineer catch-all)
    ("it",            _rx(r"\bsap\b|data ?cent(?:er|re)|\bav (?:engineer|technician|specialist|lead)|audio[- ]?visual|\bitsm\b|\bservicenow\b|\bworkday (?:analyst|admin|engineer)")),
    ("program",       _rx(r"projektleit|project ?leider|projectleider|chef de projet|jefe de proyecto|\bpm\b")),
    ("supply",        _rx(r"\blsa\b|\bils\b|almac[eé]n|\blager\b|entrep[oô]t|logisti(?:k|que|ca)|einkauf|\bachat")),
    ("gna",           _rx(r"\bhrbp\b|\bfso\b|\bitpso\b|facility security officer|assitant|investigator|trust (?:&|and) safety|comptab|contab|personalreferent|recursos humanos|ressources humaines|\bjurist|rechtsanwalt|\bpaie\b|\bnómina")),
    ("sales",         _rx(r"producer\b|filmmaker|videograph|photograph|animator|\beditor\b|copywriter|journalist|(?<!technical )(?<!tech )writer\b|market development|\bvertrieb|\bventes?\b|\bventas\b|comercial|\bkundenb|\bcommerc")),
    ("data",          _rx(r"knowledge engineer|ontology|earth observation|remote sensing|\bmetrics\b")),
    ("ml",            _rx(r"\brobot|machine intelligence|\bautonom")),
    ("systems",       _rx(r"integrator\b|design criteria|\bsystems?\b")),
    ("controls",      _rx(r"\bic&e\b|\bi, ?c ?& ?e\b|automatisierung|automatis(?:me|ation)")),
    ("electrical",    _rx(r"signal processing|signal chain|\bsi/pi\b|emulation|processor architect|cpu architect|soc architect|power distribution|ground power|[ée]lectronique|elektronik|elektrotechnik|elektro\b|\bel[eé]ctric|\bbatter")),
    ("test",          _rx(r"industrial hygien|fire protection|regulatory engineer|qualification|\byield\b|qualit[éä]t|calidad|qualidade|\binspection\b|\bsafety\b|\bsecurity\b")),
    ("manufacturing", _rx(r"panel builder|\bbuilder\b|driller|\bdrilling\b|rig hand|roustabout|fertigung|produktion|produção|producción|montage|\boperario|\boperador|\bopérat|\bsoudeur|\businage|\bfabrication\b|\bassembly\b|\bproduction\b|\bwarehouse\b")),
    ("mechanical",    _rx(r"prototyp|powertrain|materials (?:&|and) process|\bm&p\b|m[ée]canique|mechanik|maschinenbau|konstrukt|critical lift|\bmaterials?\b|\bstructures?\b|\bthermal\b|\bfluid")),
    ("science",       _rx(r"\bnuclear\b|chemical|hydrolog|geoscien|environmental scientist|histopath|patholog|\br&d\b|modell?ing engineer|analysis engineer|\bphysi|\bchemi|\bbiol|\bgeol|\blab\b|\bresearch")),
    ("software",      _rx(r"\bsw\b|\bdev\b|security architect|\barchitect\b|telco|telecom|logiciel|entwickler|desarrollador|développeur|informatique|\bsoftware\b|\bprogramm|\bcoding\b|\bplatform\b|\binfrastructure\b|\bcloud\b|\bdata\b")),
    ("fde",           _rx(r"service engineer|outcome engineer|resident engineer|\bfield\b|\bdeployment\b|\bcustomer\b")),
    ("operations",    _rx(r"opera[çc][õo]es|operaciones|\bbetrieb|\boperations?\b|\bfacilit|\bsite\b")),
    ("engineering",   _rx(r"\bengineer|\bengineering\b|\barchitect\b|\bdevelopment\b|\bdesign\b")),
]

# A software title with a strongly specific domain word belongs to that domain
# (flight software -> firmware, software engineer, perception -> ml, ...).
SOFTWARE_DOMAIN_OVERRIDES = [
    ("firmware",   _rx(r"firmware|embedded|avionics|flight software")),
    ("ml",         _rx(r"machine learning|\bml\b|perception|\bautonomy\b|computer vision|robot learning|\bllm|reinforcement|\bagents?\b|\brobotics?\b")),
    ("propulsion", _rx(r"\bgnc\b|propulsion|guidance, navigation")),
    ("controls",   _rx(r"\bcontrols? (software|engineer)")),
]
TITLE_IS_SOFTWARE = _rx(r"software|\bswe\b|full[- ]?stack|back[- ]?end|front[- ]?end|developer")

LEVEL_RULES = [
    ("intern",   _rx(r"\bintern(ship)?s?\b|\bco-?op\b|\bapprentice|\bsummer\s*(20)?2\d\b|\bspring\s*(20)?2\d\b|\bfall\s*(20)?2\d\b|\bwinter\s*(20)?2\d\b|\bstudent\b|\bwerkstudent|\bpraktik|\bstagiaire|\btrainee\b|\balternance")),
    ("director", _rx(r"\bdirector\b|\bhead of\b|\b(s?vp|evp|avp)\b|vice president|\bchief\b|\bc[a-z]{1,2}o\b|\bpresident\b|general manager|managing director|\bexecutive director|\bhead,")),
    ("staff",    _rx(r"(?<!of )(?<!technical )(?<!operations )(?<!business )\bstaff\b|\bprincipal\b|\blead\b|\bfellow\b|\bdistinguished\b|\barchitect\b|\btech lead\b|\bexpert\b|\blevel [4-9]\b|\bl[4-9]\b|(?<=[a-z] )(?:iv|v|vi)(?=\s*(?:\(|-|–|,|/|$))|\bsupervisor\b|\bsuperintendent\b|\bsenior manager|\bsr\.? manager")),
    ("senior",   _rx(r"\bsenior\b|\bsr\.?\b|\biii\b|\blevel 3\b|\bl3\b|\bexperienced\b")),
    ("junior",   _rx(r"new grad|new graduate|recent graduate|graduate engineer|graduate (program|scheme|software|mechanical|electrical|role)|\bgraduate\b|entry[- ]level|\bjunior\b|\bjr\.?\b|\bassociate (engineer|scientist|analyst|software|mechanical|electrical|technician)|\bearly career|\bearly talent|\blevel 1\b|\bl1\b|\b[a-z]+ i\b$|\bi\s*(\(|-|–|,|/)")),
]
NOT_DIRECTOR = _rx(r"assistant|coordinator|office of|to the (ceo|cto|cfo|coo|president|chief)|crew chief")

CLEARANCE_TITLE = _rx(r"clearance|ts/sci|top secret|\bsecret\b|\bcleared\b|polygraph|\bsci\b|special programs|classified")
CLEARANCE_DESC = _rx(
    r"ts/sci|top[\s-]*secret|secret\s+(?:security\s+)?clearance"
    r"|(?:active|current|existing)\s+(?:(?:dod|u\.?s\.?|us|government|doe)\s+)?(?:security\s+)?clearance"
    r"|(?:hold|holds|holding|possess|possesses|possessing|maintain|maintains|maintaining)\s+(?:an?\s+)?(?:active\s+|current\s+)?(?:(?:dod|u\.?s\.?|us|government|doe)\s+)?(?:secret\s+|top\s+secret\s+)?(?:security\s+)?clearance"
    r"|(?:security\s+)?clearance\s+(?:is\s+)?(?:required|mandatory)|requires?\s+(?:an?\s+)?(?:active\s+)?(?:(?:dod|u\.?s\.?|us|government)\s+)?(?:secret\s+)?(?:security\s+)?clearance"
    r"|clearance[- ]required|cleared\s+(?:role|position|personnel|engineer|candidates?)|\bq\s+clearance|level\s+q\b|\bsci\s+clearance|polygraph"
)
US_PERSON_DESC = _rx(r"u\.?s\.?\s+(?:citizen|person|national)|\bitar\b|export[- ]control|permanent resident|green card")

TRADES = _rx(r"\btechnician\b|\btech\b|\bwelder|\bwelding\b|\bmachinist|\bcnc\b|\bassembler|\bassembly (tech|technician|operator|associate)|\bfabricat|\belectrician|\bmechanic\b|\bmillwright|\bpipefitter|\bpainter|\bmachine operator|\boperator\b|\btoolmaker|\btool\s*(&|and)\s*die|\bcomposite tech|\binspector\b|\bplumber|\bhvac\b|\bcrane\b|\brigger|\bforklift|\bmaterial handler|\bwarehouse associate|\bproduction (associate|worker|operator|technician)|\btechnologist\b|\bcarpenter|\bdriver\b|\bcdl\b|\bsheet ?metal|\bmaintenance (technician|mechanic)|\bapprentice|\bjourneyman|\bfitter\b|\binstaller\b|mechaniker|mechatroniker|techniker|monteur|technicien|opérateur|schweiß|elektriker")
SUMMER_2027 = _rx(r"summer\s*(?:20)?27\b|2027\s*summer|summer\s*'27")

ROLE_FAMILY_SKIP_TRADES = {"sales", "gna", "leadership", "general", "it", "data", "product", "software", "ml"}


# ─────────────────────────────────────────────────────────────────────────────
# Location rules
# ─────────────────────────────────────────────────────────────────────────────

METRO_RULES = OrderedDict([
    ("sf",  _rx(r"\b(?:san francisco|sf|sfhq|sf hq|bay area|silicon valley|palo alto|mountain view|sunnyvale|menlo park|redwood city|san mateo|cupertino|santa clara|san jose|fremont|milpitas|south san francisco|oakland|berkeley|emeryville|alameda|san carlos|san leandro|burlingame|brisbane\)?, ca|millbrae|san bruno|hayward|pleasanton|livermore|sausalito|scotts valley|half moon bay|dublin, ca|dublin, california|foster city|santa cruz|san rafael|novato|petaluma|los gatos|campbell, ca|newark, ca|union city|vallejo|richmond, ca|walnut creek|san ramon|moffett|mt\.? view|south sf)\b")),
    ("la",  _rx(r"\b(?:los angeles|la|california - la|costa mesa|el segundo|irvine|long beach|torrance|pasadena|anaheim|santa monica|hawthorne|inglewood|huntington beach|fullerton|orange county|garden grove|gardena|playa vista|culver city|marina del rey|redondo beach|cypress, ca|cypress, california|carson, ca|burbank|glendale, ca|van nuys|chatsworth|camarillo|thousand oaks|santa ana|newport beach|tustin|lake forest|compton|vernon, ca|city of industry|ontario, ca\b|riverside, ca|san bernardino|victorville|mojave|palmdale|lancaster, ca|lancaster, california|san pedro|signal hill|monrovia|azusa|pomona|rancho cucamonga|corona, ca|oxnard|santa clarita|valencia, ca|valencia, california|fontana|rancho dominguez|carson, california|hawthorne, california|socal|southern california)\b")),
    ("tx",  _rx(r"\b(?:texas|tx|austin|bastrop|starbase|mcgregor|houston|dallas|san antonio|fort worth|plano|midland|brownsville|college station|lockhart|temple|belton|kermit|odessa|amarillo|killeen|waco|round rock|cedar park|georgetown, tx|el paso|lubbock|boca chica|dallas-fort worth|dfw)\b")),
    ("sea", _rx(r"\b(?:seattle|redmond|bellevue|kirkland|kent|tacoma|everett|bothell|woodinville|tukwila|renton|bellingham|olympia|wa|washington state|sunset corporate campus)\b|(?<=, )washington(?!,? ?d\.?c)(?! dc)(?!, district)")),
    ("den", _rx(r"\b(?:denver|boulder|colorado|aurora, co|broomfield|littleton|golden, co|louisville, co|longmont|berthoud|commerce city|fort collins|lakewood, co|centennial|englewood, co|co|loveland|greeley|castle rock|henderson, co|thornton|lafayette, co|arvada|westminster, co)\b(?!-)")),
    ("dc",  _rx(r"washington,? ?d\.?c\.?|washington dc|district of columbia|\b(?:dc|arlington|mclean|reston|tysons|chantilly|herndon|columbia, md|baltimore|bethesda|annapolis|rosslyn|alexandria|sterling, va|sterling, virginia|ashburn|silver spring|rockville|lanham|college park, md|chevy chase|northern va|fairfax|springfield, va|dulles|middle river|laurel, md|gaithersburg|crystal city|quantico|fort meade|leesburg|manassas|vienna, va|falls church|annandale|germantown, md|greenbelt|beltsville|frederick, md|national capital region|pentagon)\b")),
    ("nyc", _rx(r"\b(?:new york|nyc|manhattan|brooklyn|jersey city|hoboken|long island city|queens|glen cove|elizabeth, nj|newark, nj|secaucus|stamford|white plains|bronx|staten island|long island)\b")),
    ("bos", _rx(r"\b(?:boston|cambridge, ma|cambridge, massachusetts|lexington|waltham|bedford, ma|burlington, ma|massachusetts|somerville|watertown|billerica|woburn|wilmington, ma|charlestown|peabody|devens|ma|andover|lowell, ma|worcester|marlborough|natick|needham|quincy, ma|canton, ma|norwood|framingham|westford|chelmsford|bedford|burlington)\b")),
])

# Non-US hubs big enough for their own chip; everything else abroad is "Other international".
SUBMETRO_RULES = OrderedDict([
    ("london",  _rx(r"\blondon\b(?!, (?:on|ontario|ky|kentucky))|greater london|\bhounslow\b|\bcroydon\b|\bhayes, (?:uk|london)|\bstratford, london|\bshoreditch\b|\bcanary wharf\b|\bking'?s cross\b|\bwestminster, london|\bsoho, london")),
    ("munich",  _rx(r"\bmunich\b|\bmünchen\b|\bmuenchen\b|\bbavaria\b|\bbayern\b|\bparsdorf\b|\bottobrunn\b|\btaufkirchen\b|\bgilching\b|\baugsburg\b|\boberpfaffenhofen\b|\bgarching\b|\bunterschlei|\bfreising\b|\bingolstadt\b|\bnuremberg\b|\bnürnberg\b|\berlangen\b|\bregensburg\b|\blandshut\b|\bputzbrunn\b|\bgermering\b|\bweßling\b|\bwessling\b")),
    ("paris",   _rx(r"\bparis\b(?!, (?:tx|texas|tn|tennessee|il|ky))|[îi]le-de-france|\baubervilliers\b|\bbic[êe]tre\b|\bmassy\b|\bsaclay\b|\bpalaiseau\b|\bversailles\b|\bboulogne-billancourt\b|\bissy-les-moulineaux\b|\bla d[ée]fense\b|\bnanterre\b|\bmontreuil\b|\bsaint-denis\b|\bcourbevoie\b|\bvitry-sur-seine\b|\borly\b|\bcr[ée]teil\b|\bbagneux\b|\bmeudon\b|\bv[ée]lizy\b|\bgennevilliers\b|\bivry-sur-seine\b|\bpantin\b|\brueil-malmaison\b|\bsuresnes\b|\bantony\b")),
    ("toronto", _rx(r"\btoronto\b|\bgreater toronto|\bgta\b|\bmississauga\b|\bmarkham\b|\bvaughan\b|\bbrampton\b|\boakville\b|\bnorth york\b|\bscarborough, on|\betobicoke\b|\brichmond hill\b|\bburlington, on|\bhamilton, on|\bpickering, on|\bajax, on|\bwhitby, on|\boshawa\b|\bconcord, on")),
    ("telaviv", _rx(r"\btel[- ]aviv\b|\bisrael\b|\bherzliya\b|\bramat gan\b|\bpetah tikva\b|\bpetach tikva\b|\brehovot\b|\bhaifa\b|\bjerusalem\b|\bbe'?er sheva\b|\bnetanya\b|\braanana\b|\bra'anana\b|\bkfar saba\b|\bhod hasharon\b|\byokneam\b|\bcaesarea\b|\bor yehuda\b|\bholon\b|\brosh ha'?ayin\b|\bmodi'?in\b")),
])
LOCATION_SPLIT = re.compile(r"\s*(?:;|\||//|/(?!\w*\d)|\bor\b|\band\b|&|\+|·|•)\s*")

REMOTE_RX = _rx(r"\bremote\b|anywhere|work from home|\bwfh\b|distributed|worldwide")

INTL_TOKENS = [
    # UK & Ireland
    r"uk\b", r"u\.k\.", r"united kingdom", r"england", r"scotland", r"wales\b", r"london", r"bristol", r"oxford, (uk|england)", r"cambridge, (uk|england)", r"daresbury", r"manchester, uk", r"edinburgh", r"glasgow", r"reading, uk", r"harwell", r"didcot", r"stevenage", r"hounslow", r"\bgb\b", r"ireland", r"dublin(?!, ca)(?!, california)", r"cork\b", r"uk&i",
    # DACH, France, Benelux, Nordics
    r"germany", r"deutschland", r"munich", r"münchen", r"berlin", r"hamburg", r"bavaria", r"bayern", r"parsdorf", r"ottobrunn", r"aachen", r"stuttgart", r"frankfurt", r"cologne", r"köln", r"düsseldorf", r"dresden", r"heidelberg", r"karlsruhe", r"bremen", r"augsburg", r"taufkirchen", r"gilching", r"austria", r"vienna", r"switzerland", r"zurich", r"zürich", r"geneva", r"lausanne", r"basel",
    r"france", r"paris", r"toulouse", r"bordeaux", r"grenoble", r"aubervilliers", r"bourbourg", r"lyon", r"nantes", r"marseille", r"bicêtre", r"hauts-de-france", r"occitanie", r"auvergne", r"île-de-france", r"ile-de-france",
    r"netherlands", r"amsterdam", r"delft", r"eindhoven", r"rotterdam", r"the hague", r"noordwijk", r"south holland", r"utrecht", r"groningen", r"belgium", r"brussels", r"antwerp", r"luxembourg",
    r"sweden", r"stockholm", r"kiruna", r"gothenburg", r"norway", r"oslo", r"andenes", r"finland", r"espoo", r"helsinki", r"denmark", r"copenhagen", r"iceland",
    # Southern & Eastern Europe
    r"spain", r"madrid", r"barcelona", r"valencia(?!, ca)(?!, california)", r"sevilla", r"seville", r"portugal", r"lisbon", r"porto\b", r"italy", r"milan", r"rome\b", r"turin", r"torino", r"greece", r"athens", r"cyprus", r"poland", r"warsaw", r"krakow", r"wrocław", r"słubice", r"czech", r"prague", r"latvia", r"riga", r"estonia", r"tallinn", r"lithuania", r"vilnius", r"hungary", r"budapest", r"romania", r"bucharest", r"ukraine", r"kyiv", r"lviv", r"serbia", r"belgrade", r"croatia", r"slovenia", r"slovakia", r"bulgaria",
    # Middle East & Africa
    r"israel", r"tel aviv", r"haifa", r"jerusalem", r"herzliya", r"uae\b", r"u\.a\.e", r"dubai", r"abu dhabi", r"qatar", r"doha", r"saudi", r"riyadh", r"jeddah", r"bahrain", r"kuwait", r"oman\b", r"egypt", r"cairo", r"turkey", r"türkiye", r"istanbul", r"ankara", r"middle east",
    r"nigeria", r"lagos", r"abuja", r"kenya", r"nairobi", r"south africa", r"cape town", r"johannesburg", r"ghana", r"accra", r"rwanda", r"kigali", r"côte d", r"cote d", r"abidjan", r"morocco", r"ethiopia",
    # Asia-Pacific
    r"india\b", r"bengaluru", r"bangalore", r"hyderabad", r"mumbai", r"pune\b", r"chennai", r"gurgaon", r"gurugram", r"noida", r"delhi(?!, ca)(?!, california)", r"ahmedabad", r"gujarat", r"karnataka", r"telangana",
    r"japan", r"tokyo", r"osaka", r"south korea", r"korea", r"seoul", r"gyeonggi", r"taiwan", r"taipei", r"hsinchu", r"china", r"shanghai", r"shenzhen", r"beijing", r"hong kong", r"hkg", r"sheung wan", r"singapore", r"malaysia", r"kuala lumpur", r"philippines", r"manila", r"makati", r"cebu", r"davao", r"iloilo", r"vietnam", r"hanoi", r"ho chi minh", r"thailand", r"bangkok", r"indonesia", r"jakarta", r"cambodia", r"phnom penh",
    r"australia", r"sydney", r"melbourne(?!, fl)(?!, florida)", r"brisbane(?!\)?, ca)", r"perth", r"adelaide", r"canberra", r"queensland", r"new south wales", r"tasmania", r"victoria\b", r"new zealand", r"nz\b", r"auckland", r"christchurch", r"wellington", r"waikato", r"canterbury", r"mahia", r"south island", r"north island", r"morrinsville",
    # Canada
    r"canada", r"toronto", r"vancouver(?!, wa)", r"montreal", r"montréal", r"ottawa", r"calgary", r"edmonton", r"waterloo", r"kitchener", r"quebec", r"québec", r"ontario(?!, ca\b)", r"british columbia", r"alberta", r"surrey, bc", r"burnaby", r"north vancouver", r"delta, british", r"sudbury", r"saskatoon", r"nova scotia", r"bc\b", r"on, can", r"can\b",
    # Latin America
    r"mexico(?<!new mexico)", r"méxico", r"guadalajara", r"monterrey", r"ciudad de", r"cdmx", r"brazil", r"brasil", r"são paulo", r"sao paulo", r"rio de janeiro", r"mato grosso", r"argentina", r"buenos aires", r"uruguay", r"montevideo", r"chile", r"santiago", r"iquique", r"colombia", r"bogot", r"peru\b", r"lima\b", r"costa rica", r"trinidad", r"caribbean",
    # Regions
    r"europe", r"emea", r"apac", r"latam", r"asia\b", r"africa", r"international", r"eu\b",
]
INTL_RX = _rx(r"\b(?:" + "|".join(INTL_TOKENS) + r")")

US_STATE_ABBR = r"al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy"
US_STATES = r"alabama|alaska|arizona|arkansas|california|connecticut|delaware|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new mexico|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|utah|vermont|west virginia|wisconsin|wyoming|virginia|maryland|new york|massachusetts|colorado|texas|washington"
US_CITIES = (
    r"huntsville|albuquerque|tucson|phoenix|tempe|portland|salem|pittsburgh|atlanta|chicago|bolingbrook|miami|orlando|tampa|cape canaveral|jacksonville|merritt island|cocoa|memphis|nashville|research triangle|raleigh|durham|charlotte|greensboro|rock hill|ridgeville|greenville|spartanburg|idaho falls|moab|salt lake|orangeville|sparks|mccarran|carson city|reno|las vegas|san luis obispo|paso robles|philadelphia|rochester|canandaigua|youngstown|kalamazoo|wixom|detroit|ann arbor|minneapolis|omaha|st\.? louis|honolulu|wallops|norfolk|richmond|stennis|lawton|new kensington|benson|paducah|homestead|pea ridge|esparto|byron|chattanooga|knoxville|oak ridge|cleveland|columbus|cincinnati|indianapolis|milwaukee|kansas city|tulsa|boise|spokane|anchorage|birmingham|louisville|des moines|little rock|baton rouge|new orleans|albany|buffalo|syracuse|hartford|providence|north kingstown|merrimack|manchester, nh|portsmouth|wichita|fargo|sioux falls|cheyenne|billings|bozeman|durango|flagstaff|santa fe|eugene|vancouver, wa|bingen|elkhart|grand rapids|lansing|dayton|akron|toledo|erie|allentown|scranton|harrisburg|wilmington|dover|charleston|savannah|augusta|macon|mobile|pensacola|tallahassee|gainesville|daytona|fort lauderdale|west palm|sarasota|fort myers|naples|st\.? petersburg|clearwater|lakeland|melbourne, fl|melbourne, florida|palm bay|titusville|kennedy space|vandenberg|lompoc|goleta|santa barbara|san diego|carlsbad|oceanside|escondido|poway|la jolla|edwards|china lake|white sands|redstone|fort bliss|fort hood|fort bragg|dahlgren|patuxent|wright-patterson|eglin|hill afb|kirtland|los alamos|sandia|argonne|fermilab|brookhaven|batavia|wittmann|madison|avon|lowell|middletown|new haven|trenton|princeton|jersey|phillipsburg|loudon|west coast|east coast|midwest|us-based|usa-based|amer\b|nationwide|any spacex site|grand island|pacific north ?west|chi, atl"
)
US_RX = _rx(r"united states|\busa\b|\bu\.s\.a?\b|\bus\b|\bu\.s\b|america(?!n)|, (?:" + US_STATE_ABBR + r")\b|\b(?:" + US_STATES + r")\b|\b(?:" + US_CITIES + r")\b")
UNSPECIFIED = {"", "n/a", "na", "any", "tbd", "various", "multiple locations", "multiple", "customer site", "flexible", "-", "location", "field", "talent community", "mountain", "south central", "sud-oeste", "sea", "ca"}


# ─────────────────────────────────────────────────────────────────────────────
# data.js parsing (pure Python, no Node dependency)
# ─────────────────────────────────────────────────────────────────────────────

def _scan_block(src, start):
    """Return src[start:close+1] for the bracket at `start`, skipping strings and comments."""
    i, depth, in_str, esc, n = start, 0, None, False, len(src)
    while i < n:
        ch = src[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            i += 1
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if ch in "\"'`":
            in_str = ch
            i += 1
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
            if depth == 0:
                return src[start:i + 1]
        i += 1
    return None


def _extract_const_array(src, name):
    m = re.search(r"\bconst\s+" + re.escape(name) + r"\s*=\s*\[", src)
    return _scan_block(src, m.end() - 1) if m else None


def _split_records(arr):
    """Top-level `{...}` objects inside an array literal."""
    recs, depth, in_str, esc, cur, i, n = [], 0, None, False, None, 0, len(arr)
    while i < n:
        ch = arr[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            i += 1
            continue
        if ch == "/" and i + 1 < n and arr[i + 1] == "/":
            j = arr.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if ch == "/" and i + 1 < n and arr[i + 1] == "*":
            j = arr.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if ch in "\"'`":
            in_str = ch
            i += 1
            continue
        if ch in "[{":
            depth += 1
            if depth == 2 and ch == "{":
                cur = i
        elif ch in "]}":
            depth -= 1
            if depth == 1 and cur is not None:
                recs.append(arr[cur:i + 1])
                cur = None
        i += 1
    return recs


def _field(rec, key):
    m = re.search(r"(?<![\w.])" + re.escape(key) + r"\s*:\s*(?:\"((?:[^\"\\]|\\.)*)\"|'((?:[^'\\]|\\.)*)')", rec)
    if not m:
        return None
    if m.group(1) is not None:
        raw = m.group(1)
    else:
        raw = m.group(2).replace("\\'", "'").replace('"', '\\"')
    try:
        return json.loads('"' + raw + '"')
    except ValueError:
        return raw


def load_database():
    """Companies, IL30 names and funding tracker from data.js."""
    src = DATA_JS_PATH.read_text(encoding="utf-8")
    companies = {}
    arr = _extract_const_array(src, "COMPANIES") or "[]"
    for rec in _split_records(arr):
        name = _field(rec, "name")
        if not name:
            continue
        companies[name] = {
            "sector": _field(rec, "sector") or "",
            "subsector": _field(rec, "subsector") or "",
            "fundingStage": _field(rec, "fundingStage") or "",
            "status": _field(rec, "status") or "",
            "country": _field(rec, "country") or "",
            "location": _field(rec, "location") or "",
        }
    il30 = []
    arr = _extract_const_array(src, "INNOVATORS_LEAGUE_30")
    if arr:
        il30 = re.findall(r'"((?:[^"\\]|\\.)*)"', arr)
    tracker = []
    arr = _extract_const_array(src, "FUNDING_TRACKER") or "[]"
    for rec in _split_records(arr):
        tracker.append({
            "company": _field(rec, "company") or "",
            "amount": _field(rec, "lastRoundAmount") or "",
            "round": _field(rec, "lastRound") or "",
            "date": _field(rec, "lastRoundDate") or "",
        })
    return companies, il30, tracker


def load_master_aliases():
    """{alias_lower: canonical name}, {name: short sector} from the master list."""
    aliases, sectors = {}, {}
    if not MASTER_LIST_PATH.exists():
        return aliases, sectors
    src = MASTER_LIST_PATH.read_text(encoding="utf-8")
    pat = re.compile(r'\{\s*name:\s*"([^"]+)",\s*aliases:\s*\[([^\]]*)\](?:,\s*sector:\s*("([^"]*)"|null))?')
    for m in pat.finditer(src):
        name = m.group(1)
        sectors[name] = m.group(4) or ""
        aliases[name.lower()] = name
        for a in re.findall(r'"([^"]+)"', m.group(2)):
            if len(a) >= 4:
                aliases.setdefault(a.lower(), name)
    return aliases, sectors


# ─────────────────────────────────────────────────────────────────────────────
# Classification
# ─────────────────────────────────────────────────────────────────────────────

def norm_title(t):
    t = (t or "").replace(" ", " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()


def role_family(title):
    t = norm_title(title).lower()
    if not t:
        return "other"
    fam = "other"
    for code, rx in FAMILY_RULES:
        if rx.search(t):
            fam = code
            break
    if fam == "software":
        for code, rx in SOFTWARE_DOMAIN_OVERRIDES:
            if rx.search(t):
                return code
        return "software"
    if fam == "engineering":
        # a bare "Engineer" with no domain word: keep it visible under Other
        # rather than guess, unless the title itself says software
        return "software" if TITLE_IS_SOFTWARE.search(t) else "other"
    return fam


def job_level(title):
    t = norm_title(title).lower()
    for code, rx in LEVEL_RULES:
        if code == "director" and NOT_DIRECTOR.search(t):
            continue
        if rx.search(t):
            return code
    return "mid"


HQ_ONLY = _rx(r"^(?:[\w .&'-]+ )?(?:hq|headquarters|head office|office|on-?site|onsite)$")


def _location_parts(low):
    """[(offset, part)] for each place in a multi-location string; the whole string when there is one."""
    parts, pos = [], 0
    for m in LOCATION_SPLIT.finditer(low):
        if m.start() > pos:
            parts.append((pos, low[pos:m.start()]))
        pos = m.end()
    if pos < len(low):
        parts.append((pos, low[pos:]))
    return parts or [(0, low)]


def job_metros(location, remote_flag, company_location=""):
    loc = (location or "").replace("\u202f", " ").replace("\xa0", " ").strip()
    low = re.sub(r"\s+", " ", loc.lower())
    if low in UNSPECIFIED or HQ_ONLY.search(low):
        if company_location:
            fallback = job_metros(company_location, False)
            if fallback:
                return fallback + (["remote"] if remote_flag else [])
        return ["remote"] if remote_flag else []
    found = []  # (position, code)
    for code, rx in METRO_RULES.items():
        m = rx.search(low)
        if m:
            found.append((m.start(), code))
    # multi-location strings ("Austin, TX; Toronto, Ontario; Berlin") are judged part by part so a
    # named hub does not swallow the other places, and "Other international" only covers the rest
    for off, part in _location_parts(low):
        sub = [(off + m.start(), code) for code, rx in SUBMETRO_RULES.items() for m in [rx.search(part)] if m]
        found.extend(sub)
        m = INTL_RX.search(part)
        if m and not sub:
            found.append((off + m.start(), "intl"))
    m = REMOTE_RX.search(low)
    if m or remote_flag:
        found.append((m.start() if m else 9999, "remote"))
    if not any(c for _, c in found if c not in ("remote", "intl")):
        m = US_RX.search(low)
        if m:
            found.append((m.start(), "us"))
    found.sort()
    out, seen = [], set()
    for _, c in found:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def stage_group(stage, status):
    s = (stage or "").lower()
    if status == "ipo" or s.startswith("public") or s == "ipo":
        return "public"
    if "pre-seed" in s or s.startswith("seed") or "bootstrapped" in s:
        return "seed"
    if s.startswith("series a") or s == "pre-series b":
        return "a"
    if s.startswith("series b"):
        return "b"
    if s.startswith("series c"):
        return "c"
    if s.startswith("series") or s in ("growth", "late stage", "pre-ipo", "series d+"):
        return "d"
    return "other"


def parse_date(s):
    try:
        return date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


def month_mid(ym):
    """'2026-10' -> date(2026, 10, 15) so a month-level deal date can be compared to a day window."""
    m = re.match(r"^(\d{4})-(\d{2})", ym or "")
    if not m:
        return None
    return date(int(m.group(1)), int(m.group(2)), 15)


# ─────────────────────────────────────────────────────────────────────────────
# Posting-text parsers: salary, years of experience, application deadline
# ─────────────────────────────────────────────────────────────────────────────

HOURS_PER_YEAR = 2080          # pay-transparency hourly rates are annualised at 40 h x 52 wk
SAL_ANNUAL_MIN, SAL_ANNUAL_MAX = 20_000, 2_000_000
SAL_HOURLY_MIN, SAL_HOURLY_MAX = 10, 400
SAL_MONTHLY_MIN, SAL_MONTHLY_MAX = 1_500, 60_000

# salary kinds stored in the cache / enriched records
SAL_NONE, SAL_ATS, SAL_TEXT, SAL_TEXT_RATE = 0, 1, 2, 3   # 3 = annualised from an hourly/monthly rate

_CODES = r"usd|gbp|eur|cad|aud|chf|inr|sgd|nzd|jpy|sek|dkk|nok|pln|ils|krw|twd|mxn|brl|hkd|czk|huf|zar"
_SYMBOL_CUR = {"$": "USD", "£": "GBP", "€": "EUR", "₹": "INR", "₪": "ILS", "us$": "USD", "c$": "CAD", "ca$": "CAD",
               "a$": "AUD", "au$": "AUD", "nz$": "NZD", "s$": "SGD", "hk$": "HKD", "mx$": "MXN", "r$": "BRL"}


def _money(i):
    return (r"(?:(?P<pre%d>us\$|ca\$|au\$|nz\$|hk\$|mx\$|[acrs]\$|\$|£|€|₹|₪|(?:%s)\s?)\s?)?"
            r"(?P<amt%d>\d{1,3}(?:[,.']\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\s?(?P<k%d>k\b)?"
            r"(?:\s?(?P<post%d>%s|€|£|\$))?") % (i, _CODES, i, i, i, _CODES)


SAL_RANGE_RX = _rx(_money(0) + r"\s*(?:-|–|—|to|and|through|up to|or)\s*" + _money(1))
SAL_SINGLE_RX = _rx(_money(0))
SAL_HOURLY_AFTER = _rx(r"^[^.$£€]{0,45}?(?:\b(?:per|an|a)\s+(?:hour|hr)\b|/\s?(?:hour|hr)\b|hourly|usd hourly)")
SAL_HOURLY_BEFORE = _rx(r"(?:hourly|per hour|/\s?(?:hour|hr)\b|hour(?:ly)?\s+(?:pay\s+|wage\s+)?(?:rate|range)|wage)[^.$£€]{0,40}$")
SAL_MONTHLY_AFTER = _rx(r"^[^.$£€]{0,30}?(?:\b(?:per|a)\s+month\b|/\s?month\b|monthly)")
SAL_MONTHLY_BEFORE = _rx(r"(?:monthly|per month|/month)[^.$£€]{0,30}$")
SAL_NEGATIVE = _rx(r"bonus|stipend|equity|stock|option|rsu|relocation|allowance|budget|fund\b|revenue|raised|valuation|funding|"
                   r"series [a-f]\b|quota|contract value|award|grant|reimburs|per diem|credit|insurance|401|deductible|premium|"
                   r"tuition|referral|commission|signing|sign-on|retention|severance|\bdeal\b|\bacv\b|\barr\b|\bmrr\b|pipeline|"
                   r"savings|\bcosts?\b|\bprice|\bfees?\b|loan|spend|worth|discount|gift|membership|subscription|voucher|"
                   r"donat|mortgage|rent\b|cash out|lump sum|one-time|one time|monthly housing|book|wellness|learning|development budget|gym")
SAL_POSITIVE = _rx(r"salary|base pay|base rate|base compensation|compensation|pay rate|pay range|pay scale|pay band|hourly rate|hourly range|"
                   r"rate of pay|per hour|/\s?hour|an hour|/\s?hr\b|per year|/\s?yr\b|per annum|annual|annually|starting (?:pay|rate|salary|wage)|"
                   r"\bwage|\bote\b|on-target|target earnings|remuneration|gehalt|salaire|salario|salário")
SAL_BASE = _rx(r"\bbase\b")
SAL_NEGATED = _rx(r"not include|excludes?|excluding|exclusive of|in addition to|does not|separate from|on top of|plus|as well as|and benefits|\+")
SAL_UNIT_AFTER = _rx(r"^\s*(?:m|mm|million|b|bn|billion|t|trillion|%|percent|years?|yrs|months?|days?|weeks?|hours?(?!\s*(?:per|a|/)))\b")


def _negative_context(before):
    """True when the words just before an amount, in the same sentence, say bonus / equity / funding and nothing negates them."""
    before = re.split(r"[.;!?]\s", before)[-1]
    return bool(SAL_NEGATIVE.search(before)) and not SAL_NEGATED.search(before)


def _to_number(amount, k_flag):
    s = amount.replace("'", "")
    if re.fullmatch(r"\d{1,3},\d{2}", s):           # "$180,00 - $230,000": a dropped zero
        s = s.replace(",", "") + "0"
    if re.fullmatch(r"\d{1,3}(?:[,.]\d{3})+(?:\.\d{1,2})?", s):
        # grouped thousands ("150,000", "36.830", "120,000.00")
        if re.fullmatch(r"\d{1,3}(?:[,.]\d{3})+", s):
            s = re.sub(r"[,.]", "", s)
        else:
            head, _, dec = s.rpartition(".")
            s = re.sub(r"[,.]", "", head) + "." + dec
    try:
        v = float(s)
    except ValueError:
        return None
    if k_flag and v < 10_000:
        v *= 1000
    return v


def _currency(*marks):
    for m in marks:
        if not m:
            continue
        m = m.strip().lower()
        if m in _SYMBOL_CUR:
            return _SYMBOL_CUR[m]
        if re.fullmatch(_CODES, m):
            return m.upper()
        if m.endswith("$"):
            return "USD"
    return ""


def _classify_amounts(lo, hi, before, after):
    """-> (kind, annual_lo, annual_hi) or None. before/after = text around the match."""
    if lo is None or hi is None:
        return None
    if lo > hi:
        lo, hi = hi, lo
    if lo <= 0:
        return None
    if hi >= SAL_ANNUAL_MIN:                               # nobody is paid $20,000 an hour
        if hi <= SAL_ANNUAL_MAX and (lo == hi or hi / lo <= 6):
            return (SAL_TEXT, round(lo), round(hi))
        return None
    hourly = bool(SAL_HOURLY_AFTER.search(after)) or bool(SAL_HOURLY_BEFORE.search(before))
    monthly = not hourly and (bool(SAL_MONTHLY_AFTER.search(after)) or bool(SAL_MONTHLY_BEFORE.search(before)))
    if hourly or (not monthly and hi <= SAL_HOURLY_MAX):
        if SAL_HOURLY_MIN <= lo <= hi <= SAL_HOURLY_MAX and (lo == hi or hi / lo <= 6):
            return (SAL_TEXT_RATE, round(lo * HOURS_PER_YEAR), round(hi * HOURS_PER_YEAR))
        return None
    if monthly and SAL_MONTHLY_MIN <= lo <= hi <= SAL_MONTHLY_MAX and (lo == hi or hi / lo <= 6):
        return (SAL_TEXT_RATE, round(lo * 12), round(hi * 12))
    return None


def parse_salary_text(text):
    """Salary range from posting prose -> (min, max, currency, kind) or None.

    Looks for '$150,000 - $200,000', '$150K–$200K', 'USD 150,000 to 200,000',
    '£70,000 - £90,000', hourly '$35 - $45 per hour' (annualised at 2,080 h,
    kind SAL_TEXT_RATE) and single amounts next to a pay keyword. Amounts that
    sit next to bonus / equity / funding / stipend words are ignored. When a
    posting lists several ranges (levels, locations) the 'base' ones win,
    then the overall min-max is taken if it is not absurdly wide.
    """
    if not text:
        return None
    cands = []   # (priority, kind, lo, hi, currency, span)
    spans = []
    for m in SAL_RANGE_RX.finditer(text):
        before = text[max(0, m.start() - 70):m.start()]
        after = text[m.end():m.end() + 60]
        cur = _currency(m.group("pre0"), m.group("post0"), m.group("pre1"), m.group("post1"))
        has_marker = bool(cur or m.group("k0") or m.group("k1"))
        if not has_marker and not SAL_POSITIVE.search(before[-60:]):
            continue
        if _negative_context(before[-45:]) and not SAL_POSITIVE.search(before[-30:]):
            continue
        if SAL_UNIT_AFTER.search(after):
            continue
        res = _classify_amounts(_to_number(m.group("amt0"), m.group("k0")), _to_number(m.group("amt1"), m.group("k1")), before, after)
        if not res:
            continue
        prio = 0 if SAL_BASE.search(before[-60:]) else (1 if SAL_POSITIVE.search(before[-90:] + " " + after[:25]) else 2)
        cands.append((prio, res[0], res[1], res[2], cur or "USD", (m.start(), m.end())))
        spans.append((m.start(), m.end()))
    for m in SAL_SINGLE_RX.finditer(text):
        if any(s <= m.start() < e for s, e in spans):
            continue
        cur = _currency(m.group("pre0"), m.group("post0"))
        if not cur and not m.group("k0"):
            continue
        before = text[max(0, m.start() - 70):m.start()]
        after = text[m.end():m.end() + 60]
        if not (SAL_POSITIVE.search(before[-60:]) or SAL_POSITIVE.search(after[:30])):
            continue
        if _negative_context(before[-45:]) or SAL_NEGATIVE.search(after[:14]):
            continue
        if SAL_UNIT_AFTER.search(after):
            continue
        v = _to_number(m.group("amt0"), m.group("k0"))
        res = _classify_amounts(v, v, before, after)
        if not res:
            continue
        prio = 0 if SAL_BASE.search(before[-60:]) else 1
        cands.append((prio, res[0], res[1], res[2], cur or "USD", (m.start(), m.end())))
    if not cands:
        return None
    best = min(c[0] for c in cands)
    pool = [c for c in cands if c[0] == best]
    if any(c[1] == SAL_TEXT for c in pool):               # prefer annual figures over rates
        pool = [c for c in pool if c[1] == SAL_TEXT]
    pool.sort(key=lambda c: c[5][0])
    first = pool[0]
    lo, hi = min(c[2] for c in pool), max(c[3] for c in pool)
    currencies = {c[4] for c in pool}
    if len(currencies) > 1 or hi > 4 * max(lo, 1):
        return (first[2], first[3], first[4], first[1])
    return (lo, hi, first[4], first[1])


YEARS_RX = _rx(r"(?<![\d.$£€/])(?<!\d-)(?<!\d–)(?P<a>\d{1,2})\s*(?:\+|plus)?\s*(?:(?:-|–|—|to|or)\s*(?P<b>\d{1,2})\s*\+?)?\s*\+?\s*(?:years?|yrs?)\b['’]?(?P<tail>.{0,70})")
YEARS_TAIL_OK = _rx(r"^\s*(?:of\s+)?(?:[\w/&,'’()+-]+\s+){0,5}?(?:experience|exp\.|expertise|background|track record|working|building|developing|"
                    r"designing|leading|managing|operating|programming|writing|selling|shipping|deploying|hands-on|work\b|in\s+(?:a|an|the)\b|"
                    r"in\s+[\w/&-]+(?:\s+[\w/&-]+)?\s+(?:roles?|positions?|environments?|settings?|engineering|development|design|"
                    r"manufacturing|operations|sales|research|industry|experience)|of\s+(?:relevant|professional|industry|hands|related|"
                    r"progressive|direct|demonstrated|proven|practical|combined|prior|work|full)|as\s+an?\b)")
YEARS_BEFORE_BAD = _rx(r"(?:founded|established|over the (?:past|last|next)|for the (?:past|last|next)|in the (?:past|last|next)|within|"
                       r"warranty|history|ha[sv]e been|next|last|past|ago|every|each|first|after|more than\s*$|lasts?|duration|period|"
                       r"term of|contract of|vest|runway|revenue|growth|age[sd]?\b|old\b|children|kids)\s*(?:\w+\s+)?$")
YEARS_TAIL_BAD = _rx(r"^\s*(?:old|of age|ago|warranty|vesting|from now|in business|in operation|in the (?:industry|market|making)|"
                     r"of (?:operation|history|growth|innovation|service|runway|funding|revenue|age|life|data)|or (?:older|younger)|"
                     r"of (?:the|our|its) (?:company|business|program))")


def parse_years_experience(text):
    """First credible 'N+ years' / 'N-M years of experience' in the text -> int (0 = none found).

    A range takes the midpoint (rounded down), so '2-5 years' reads as 3.
    """
    if not text:
        return 0
    for m in YEARS_RX.finditer(text):
        a = int(m.group("a"))
        b = int(m.group("b")) if m.group("b") else None
        if a > 30 or (b is not None and (b > 40 or b < a)):
            continue
        before = text[max(0, m.start() - 45):m.start()]
        tail = m.group("tail") or ""
        if YEARS_BEFORE_BAD.search(before) or YEARS_TAIL_BAD.search(tail):
            continue
        strong = ("+" in m.group(0)[: m.start("tail") - m.start()] or b is not None
                  or re.search(r"(?:minimum of|at least|min\.?|minimum|minimum experience:?|experience(?: level)?:|years of experience:)\s*$", before, re.I))
        if not strong and not YEARS_TAIL_OK.search(tail):
            continue
        return (a + b) // 2 if b is not None else a
    return 0


def level_from_years(years, title):
    """Years of experience -> level code, or '' when the title must keep the default.

    0-2 junior, 3-4 mid, 5-7 senior, 8+ staff; 8+ stays mid for managers,
    whose seniority the title already carries.
    """
    if not years:
        return ""
    t = (title or "").lower()
    if years <= 2:
        return "junior"
    if years <= 4:
        return "mid"
    if years <= 7:
        return "senior"
    if re.search(r"\bmanager\b|\bdirector\b|\bhead\b", t):
        return "mid"
    return "staff"


_MONTHS = r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
_MONTH_NUM = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
DATE_RX = (r"(?:(?P<mon>" + _MONTHS + r")\.?\s+(?P<day>\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(?P<year>20\d\d))?"
           r"|(?P<day2>\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(?P<mon2>" + _MONTHS + r")\.?(?:,?\s*(?P<year2>20\d\d))?"
           r"|(?P<m3>\d{1,2})/(?P<d3>\d{1,2})/(?P<y3>20\d\d|\d\d)\b"
           r"|(?P<y4>20\d\d)-(?P<m4>\d\d)-(?P<d4>\d\d)\b)"
           r"(?![\d/-])")
DEADLINE_RX = _rx(r"(?:deadline|applications?\s+(?:will\s+)?(?:be\s+)?(?:accepted|received|reviewed|considered|open|close[sd]?|closing|due)|"
                  r"(?:posting|position|role|requisition|job|opening|req)\s+(?:will\s+)?(?:(?:be\s+)?(?:open|posted|accepting|available|live)|"
                  r"close[sd]?|closing|remain\s+open|expire[sd]?|end[s]?)|apply\s+(?:by|before|no later than)|accepting\s+applications|"
                  r"expected\s+to\s+close|close[sd]?\s+on|open\s+(?:until|through)|no\s+later\s+than)"
                  r"(?P<gap>[^.;!?]{0,70}?)(?:" + DATE_RX + r")")


def _resolve_date(m, today):
    try:
        if m.group("y4"):
            return date(int(m.group("y4")), int(m.group("m4")), int(m.group("d4")))
        if m.group("m3"):
            y = int(m.group("y3"))
            y = y + 2000 if y < 100 else y
            return date(y, int(m.group("m3")), int(m.group("d3")))
        mon = (m.group("mon") or m.group("mon2"))[:3].lower()
        day = int(m.group("day") or m.group("day2"))
        yr = m.group("year") or m.group("year2")
        if yr:
            return date(int(yr), _MONTH_NUM[mon], day)
        # no year: the next occurrence, allowing a few weeks of grace for a deadline just passed
        d = date(today.year, _MONTH_NUM[mon], day)
        if (today - d).days > 45:
            d = date(today.year + 1, _MONTH_NUM[mon], day)
        return d
    except (ValueError, KeyError, TypeError):
        return None


def parse_deadline(text, today):
    """Explicit application deadline in the posting -> ISO date or ''.

    'Applications will close on December 1, 2026', 'apply by 11/30/2026',
    'accepting applications through October 31'. Sentences about tight
    project deadlines carry no date and never match; 'open until filled'
    has no date either.
    """
    if not text:
        return ""
    for m in DEADLINE_RX.finditer(text):
        gap = (m.group("gap") or "").lower()
        if re.search(r"rolling|until filled|none\b|n/a|not\s+have|no\s+deadline|project|delivery|milestone|launch|product|customer|"
                     r"start|begin|join|commence|onboard|available", gap) or re.search(r"start\s+(?:date|no later)", text[max(0, m.start() - 40):m.start()], re.I):
            continue
        d = _resolve_date(m, today)
        if not d:
            continue
        if (d - today).days < -60 or (d - today).days > 400:
            continue
        return d.isoformat()
    return ""


def ashby_compensation(job):
    """Ashby ?includeCompensation=true tiers -> (min, max, currency, kind) or None."""
    comp = job.get("compensation") or {}
    annual, rates = [], []
    for tier in comp.get("compensationTiers") or []:
        for c in tier.get("components") or []:
            if c.get("compensationType") != "Salary" or c.get("minValue") is None and c.get("maxValue") is None:
                continue
            lo = c.get("minValue") if c.get("minValue") is not None else c.get("maxValue")
            hi = c.get("maxValue") if c.get("maxValue") is not None else c.get("minValue")
            cur = (c.get("currencyCode") or "USD").upper()
            iv = (c.get("interval") or "").upper()
            if iv == "1 YEAR":
                annual.append((lo, hi, cur))
            elif iv == "1 HOUR":
                rates.append((lo * HOURS_PER_YEAR, hi * HOURS_PER_YEAR, cur))
            elif iv == "1 MONTH":
                rates.append((lo * 12, hi * 12, cur))
    pool = annual or rates
    if not pool:
        return None
    cur = pool[0][2]
    pool = [p for p in pool if p[2] == cur]
    lo, hi = min(p[0] for p in pool), max(p[1] for p in pool)
    if not (SAL_ANNUAL_MIN <= lo <= hi <= SAL_ANNUAL_MAX * 2):
        return None
    return (round(lo), round(hi), cur, SAL_ATS)


def lever_salary(job):
    """Lever salaryRange {min,max,currency,interval} -> (min, max, currency, kind) or None."""
    sr = job.get("salaryRange") or {}
    lo, hi = sr.get("min"), sr.get("max")
    if lo is None and hi is None:
        return None
    lo = lo if lo is not None else hi
    hi = hi if hi is not None else lo
    iv = (sr.get("interval") or "").lower()
    if "hour" in iv:
        lo, hi = lo * HOURS_PER_YEAR, hi * HOURS_PER_YEAR
    elif "month" in iv:
        lo, hi = lo * 12, hi * 12
    elif "week" in iv:
        lo, hi = lo * 52, hi * 52
    if not (SAL_ANNUAL_MIN <= lo <= hi <= SAL_ANNUAL_MAX * 2):
        return None
    return (round(lo), round(hi), (sr.get("currency") or "USD").upper(), SAL_ATS)


# ─────────────────────────────────────────────────────────────────────────────
# ATS description pass (clearance / US-person signals, Greenhouse first_published)
# ─────────────────────────────────────────────────────────────────────────────

def board_key(job):
    """('gh', token) etc. from a job id, so boards can be re-fetched."""
    jid = job.get("id") or ""
    src = job.get("source")
    if src == "greenhouse" and jid.startswith("gh-"):
        return ("gh", jid[3:].rsplit("-", 1)[0])
    if src == "ashby" and jid.startswith("ab-") and len(jid) > 40:
        return ("ab", jid[3:-37])
    if src == "lever" and jid.startswith("lv-") and len(jid) > 40:
        return ("lv", jid[3:-37])
    return None


def _plain(html_text):
    """HTML -> text. Greenhouse ships HTML-escaped HTML, so entities (&mdash;,
    &nbsp;) survive the first unescape; a second pass after tag-stripping
    turns them into the characters the salary and date regexes expect."""
    t = html.unescape(html_text or "")
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t).replace("\xa0", " ")
    return re.sub(r"\s+", " ", t)


def _signal_flags(text):
    flags = 0
    if CLEARANCE_DESC.search(text):
        flags |= 1
    if US_PERSON_DESC.search(text):
        flags |= 2
    return flags


def _signal_row(flags, first_published, salary, deadline, years):
    smin, smax, cur, kind = salary if salary else (0, 0, "", SAL_NONE)
    return [flags, first_published, smin, smax, cur, kind, deadline, years]


def extract_board_signals(kind, slug, data, today):
    """Pure: one board's API payload -> {job_id: signal row}. None when the payload is not a board."""
    out = {}
    if kind == "gh":
        for j in (data or {}).get("jobs", []):
            text = _plain(j.get("content", ""))
            fp = (j.get("first_published") or "")[:10]
            up = (j.get("updated_at") or "")[:10]
            deadline = (j.get("application_deadline") or "")[:10]
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", deadline):
                deadline = parse_deadline(text, today)
            out[f"gh-{slug}-{j.get('id')}"] = _signal_row(_signal_flags(text), fp if fp and fp < up else "",
                                                           parse_salary_text(text), deadline, parse_years_experience(text))
    elif kind == "ab":
        for j in (data or {}).get("jobs", []):
            text = j.get("descriptionPlain") or _plain(j.get("descriptionHtml", ""))
            out[f"ab-{slug}-{j.get('id')}"] = _signal_row(_signal_flags(text), "", ashby_compensation(j) or parse_salary_text(text),
                                                           parse_deadline(text, today), parse_years_experience(text))
    elif kind == "lv":
        if not isinstance(data, list):
            return None
        for j in data:
            parts = [j.get("descriptionPlain") or "", j.get("additionalPlain") or ""]
            for lst in j.get("lists", []) or []:
                parts.append(_plain(lst.get("content", "")))
            text = " ".join(parts)
            out[f"lv-{slug}-{j.get('id')}"] = _signal_row(_signal_flags(text), "", lever_salary(j) or parse_salary_text(text),
                                                           parse_deadline(text, today), parse_years_experience(text))
    else:
        return None
    return out


def fetch_board_signals(kind, slug, today):
    """Download one board and return {job_id: signal row}; {} for a vanished board, None on failure."""
    import requests  # only needed for the fetch pass
    headers = {"User-Agent": "InnovatorsLeague-JobsBot/1.0", "Accept": "application/json"}
    if kind == "gh":
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    elif kind == "ab":
        url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
    elif kind == "lv":
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    else:
        return None
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=60)
        except requests.RequestException:
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code == 200:
            try:
                data = r.json()
            except ValueError:
                return None
            return extract_board_signals(kind, slug, data, today)
        if r.status_code in (404, 410):
            return {}
        time.sleep(2 * (attempt + 1))
    return None


def refresh_signal_cache(jobs, cache, today, force=False, limit=None, workers=8):
    """Re-fetch boards whose job-id set changed since the cache was written."""
    boards = {}
    for j in jobs:
        bk = board_key(j)
        if bk:
            boards.setdefault(bk, []).append(j["id"])
    cache.setdefault("boards", {})
    cache.setdefault("jobs", {})
    todo = []
    for bk, ids in sorted(boards.items()):
        key = f"{bk[0]}:{bk[1]}"
        h = hashlib.sha1("\n".join(sorted(ids)).encode()).hexdigest()[:16]
        if force or cache["boards"].get(key, {}).get("ids") != h:
            todo.append((bk, key, h))
    if limit:
        todo = todo[:limit]
    print(f"[enrich] description pass: {len(boards)} boards, {len(todo)} need fetching")
    ok = fail = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fetch_board_signals, bk[0], bk[1], today): (bk, key, h) for bk, key, h in todo}
        for fut in concurrent.futures.as_completed(futs):
            bk, key, h = futs[fut]
            try:
                res = fut.result()
            except Exception as e:  # noqa: BLE001
                print(f"[enrich]   {key}: error {e}")
                res = None
            if res is None:
                fail += 1
                continue
            ok += 1
            prefix = f"{bk[0]}-{bk[1]}-"
            for jid in [k for k in cache["jobs"] if k.startswith(prefix)]:
                del cache["jobs"][jid]
            for jid, row in res.items():
                if row[0] or row[1] or row[5] or row[6] or row[7]:
                    cache["jobs"][jid] = row
            cache["boards"][key] = {"ids": h, "n": len(res)}
    live_keys = {f"{bk[0]}:{bk[1]}" for bk in boards}
    for key in [k for k in cache["boards"] if k not in live_keys]:
        del cache["boards"][key]
    live_ids = {j["id"] for j in jobs}
    for jid in [k for k in cache["jobs"] if k not in live_ids]:
        del cache["jobs"][jid]
    print(f"[enrich]   fetched {ok} boards, {fail} failed, {len(cache['jobs'])} jobs with signals, salary, deadline or publish dates cached")
    return ok, fail


# ─────────────────────────────────────────────────────────────────────────────
# Per-location clones and the posting history used for hiring surges
# ─────────────────────────────────────────────────────────────────────────────

SHIFT_SEGMENT = _rx(r"^(?:(?:\d(?:st|nd|rd|th)|first|second|third|1|2|3|4|a|b|c|d|day|days|night|nights|swing|weekend|weekends|mid|multiple|all|rotating|various|flex)\s*shifts?|"
                    r"shift\s*[a-d1-4]?|nights?|days?|weekends?|overnight|rotating|weekend days|day/night|nights & weekends|all shifts)$")
GENDER_SEGMENT = _rx(r"^\(?[mfwdhx](?:\s*/\s*[mfwdhx]){1,3}\)?$|^h/f$|^all genders$|^alle geschlechter$")
TRAILING_SEGMENT = re.compile(r"\s*(?:[-–—|:,]\s*|\()([^-–—|:,()]+)\)?\s*$")


def _is_location_segment(seg):
    low = seg.lower().strip()
    if not low or low in UNSPECIFIED or len(low) > 60:
        return False
    if REMOTE_RX.search(low) or HQ_ONLY.search(low):
        return True
    if any(rx.search(low) for rx in METRO_RULES.values()) or any(rx.search(low) for rx in SUBMETRO_RULES.values()):
        return True
    return bool(INTL_RX.search(low) or US_RX.search(low))


def group_key(title):
    """Title -> key shared by per-location / per-shift clones of the same role.

    Case, whitespace and punctuation are folded; trailing segments naming a
    place ("- Hawthorne, CA", "(Redmond)"), a shift ("- 2nd Shift") or a
    gender marker ("(m/f/d)") are stripped; team or product segments like
    "(Starlink)" or "(Summer 2027)" are kept because those are different roles.
    """
    t = norm_title(title)
    for _ in range(3):
        m = TRAILING_SEGMENT.search(t)
        if not m or m.start() == 0:
            break
        seg = m.group(1).strip()
        if _is_location_segment(seg) or SHIFT_SEGMENT.search(seg) or GENDER_SEGMENT.search(seg):
            t = t[:m.start()].rstrip()
        else:
            break
    t = re.sub(r"\((?:[mfwdhx](?:\s*/\s*[mfwdhx]){1,3})\)", " ", t, flags=re.I)
    key = re.sub(r"[^a-z0-9+#&/ ]", " ", t.lower())
    return re.sub(r"\s+", " ", key).strip()


def load_history():
    if HISTORY_PATH.exists():
        try:
            h = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
            if isinstance(h, dict) and h.get("version") == 1 and isinstance(h.get("days"), dict):
                return h
        except ValueError:
            pass
    return {"version": 1, "days": {}}


def update_history(history, out_jobs, today):
    """Fold today's live postings into the per-day, per-company count of new postings.

    A posting first published on day D is counted under D; the stored value is
    the max ever seen for (D, company), so postings that close a few days later
    still count for the day they appeared. Days older than HISTORY_KEEP_DAYS
    are dropped. Idempotent: running twice on the same input changes nothing.
    """
    days = history.setdefault("days", {})
    counts = Counter()
    for j in out_jobs:
        if j["posted"] and (today - date.fromisoformat(j["posted"])).days <= HISTORY_KEEP_DAYS:
            counts[(j["posted"], j["company"])] += 1
    for (day, company), n in counts.items():
        row = days.setdefault(day, {})
        if n > row.get(company, 0):
            row[company] = n
    cutoff = date.fromordinal(today.toordinal() - HISTORY_KEEP_DAYS).isoformat()
    for day in [d for d in days if d < cutoff]:
        del days[day]
    history["days"] = OrderedDict(sorted(days.items()))
    return history


def surge_counts(history, today):
    """{company: (postings in the last 14 days, postings in the 14 before)} from the history."""
    recent_from = date.fromordinal(today.toordinal() - SURGE_WINDOW_DAYS).isoformat()
    prior_from = date.fromordinal(today.toordinal() - 2 * SURGE_WINDOW_DAYS).isoformat()
    recent, prior = Counter(), Counter()
    for day, row in history.get("days", {}).items():
        if day > today.isoformat():
            continue
        if day > recent_from:
            for c, n in row.items():
                recent[c] += n
        elif day > prior_from:
            for c, n in row.items():
                prior[c] += n
    return {c: (recent[c], prior[c]) for c in set(recent) | set(prior)}


def is_surge(recent, prior):
    return recent - prior >= SURGE_MIN_EXTRA and recent >= SURGE_RATIO * prior


# ─────────────────────────────────────────────────────────────────────────────
# Main enrichment
# ─────────────────────────────────────────────────────────────────────────────

def enrich(today, fetch=True, force_fetch=False, fetch_limit=None):
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    if isinstance(raw, dict):  # status-metadata file written on a failed pull
        raw = raw.get("data") or []
    stats = {}
    if STATS_PATH.exists():
        try:
            stats = json.loads(STATS_PATH.read_text(encoding="utf-8"))
        except ValueError:
            stats = {}

    db, il30_names, tracker = load_database()
    aliases, master_sectors = load_master_aliases()
    il30 = set(il30_names)

    def resolve(name):
        """Job-board company name -> data.js canonical name (or the name itself)."""
        if name in db:
            return name
        canon = aliases.get((name or "").lower())
        if canon and canon in db:
            return canon
        return name

    # deals: most recent round per canonical company
    deals = {}
    try:
        for d in json.loads(DEALS_PATH.read_text(encoding="utf-8")):
            c = resolve(d.get("company", ""))
            dm = month_mid(d.get("date", ""))
            if not dm:
                continue
            cur = deals.get(c)
            if not cur or dm > cur["_d"]:
                deals[c] = {"_d": dm, "amount": d.get("amount") or "", "round": d.get("round") or "", "month": (d.get("date") or "")[:7]}
    except (FileNotFoundError, ValueError):
        pass
    for d in tracker:
        c = resolve(d["company"])
        dm = month_mid(d["date"])
        if not dm:
            continue
        cur = deals.get(c)
        if not cur or dm > cur["_d"]:
            deals[c] = {"_d": dm, "amount": d["amount"], "round": d["round"], "month": d["date"][:7]}
    raised_cutoff = date.fromordinal(today.toordinal() - RAISED_WINDOW_DAYS)

    # description-signal cache
    cache = {"version": CACHE_VERSION, "boards": {}, "jobs": {}}
    if CACHE_PATH.exists():
        try:
            loaded = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if loaded.get("version") == CACHE_VERSION:
                cache = loaded
            else:
                print(f"[enrich] description cache is v{loaded.get('version')}, want v{CACHE_VERSION}: every board will be re-fetched")
        except ValueError:
            pass
    cache_touched = False
    if fetch:
        try:
            refresh_signal_cache(raw, cache, today, force=force_fetch, limit=fetch_limit)
            cache_touched = True
        except Exception as e:  # noqa: BLE001 — never let the network break the build
            print(f"[enrich] description pass skipped: {e}")
    desc_signals = cache.get("jobs", {})

    # companies
    companies = OrderedDict()
    for j in raw:
        name = j.get("company") or ""
        if name in companies:
            companies[name]["jobs"] += 1
            continue
        canon = resolve(name)
        rec = db.get(canon)
        if rec:
            sector = rec["sector"] or "Other"
            hard = sector not in SOFTWARE_SECTORS
            stage, status, in_db = rec["fundingStage"], rec["status"], True
        elif name in NON_DB_COMPANIES:
            sector, hard, stage = NON_DB_COMPANIES[name]
            status, in_db = "", False
        else:
            sector = MASTER_SECTOR_LABELS.get(master_sectors.get(name, ""), "Other")
            hard = sector not in SOFTWARE_SECTORS and sector != "Other"
            stage, status, in_db = "", "", False
        deal = deals.get(canon)
        raised = None
        if deal and deal["_d"] >= raised_cutoff:
            raised = {"amount": deal["amount"], "round": deal["round"], "month": deal["month"]}
        companies[name] = {
            "name": name,
            "canonical": canon,
            "inDatabase": in_db,
            "sector": sector,
            "subsector": rec["subsector"] if rec else "",
            "fundingStage": stage,
            "stageGroup": stage_group(stage, status),
            "il30": canon in il30,
            "isHardTech": hard,
            "raised": raised,
            "jobs": 1,
        }

    # jobs
    out_jobs = []
    for j in raw:
        title = norm_title(j.get("title"))
        comp = companies[j.get("company") or ""]
        sig = list(desc_signals.get(j.get("id")) or [])
        sig += [0, "", 0, 0, "", SAL_NONE, "", 0][len(sig):]
        updated = parse_date(j.get("posted"))           # the ATS "last activity" date the fetcher stores
        first_pub = parse_date(sig[1]) if sig[1] else None
        posted = first_pub if first_pub and (not updated or first_pub < updated) else updated
        days = (today - posted).days if posted else None
        if days is not None and days < 0:
            days = 0
        upd_days = (today - updated).days if updated else None
        if upd_days is not None and upd_days < 0:
            upd_days = 0
        fam = role_family(title)
        lvl = job_level(title)
        level_source = "title" if lvl != "mid" else "default"
        years = int(sig[7] or 0)
        if level_source == "default" and years and fam != "general":
            from_years = level_from_years(years, title)
            if from_years:
                lvl, level_source = from_years, "description"
        db_rec = db.get(comp["canonical"])
        metros = job_metros(j.get("location"), j.get("remote"), db_rec["location"] if db_rec else "")
        remote = bool(j.get("remote")) or "remote" in metros
        clearance = bool(CLEARANCE_TITLE.search(title)) or bool(sig[0] & 1)
        us_person = bool(sig[0] & 2)
        trades = fam not in ROLE_FAMILY_SKIP_TRADES and bool(TRADES.search(title)) and lvl != "intern"
        # salary: the fetcher's structured range first, then the ATS compensation block (Ashby, Lever),
        # then the range written in the posting text. Hourly figures are annualised at 2,080 h.
        sal_min, sal_max, sal_cur, sal_source = None, None, None, ""
        rmin, rmax = j.get("salaryMin") or 0, j.get("salaryMax") or 0
        if rmax and SAL_HOURLY_MIN <= rmax <= SAL_HOURLY_MAX and rmin <= rmax:
            sal_min, sal_max, sal_cur, sal_source = (rmin or rmax) * HOURS_PER_YEAR, rmax * HOURS_PER_YEAR, j.get("salaryCurrency") or "USD", "ats-hourly"
        elif rmax >= SAL_ANNUAL_MIN or rmin >= SAL_ANNUAL_MIN:
            sal_min, sal_max, sal_cur, sal_source = rmin or None, rmax or None, j.get("salaryCurrency") or "USD", "ats"
        elif sig[5]:
            sal_min, sal_max, sal_cur = sig[2] or None, sig[3] or None, sig[4] or "USD"
            sal_source = {SAL_ATS: "ats", SAL_TEXT: "posting", SAL_TEXT_RATE: "posting-hourly"}.get(sig[5], "posting")
        deadline = sig[6] or ""
        deadline_days = (date.fromisoformat(deadline) - today).days if deadline else None
        out_jobs.append({
            "id": j.get("id"),
            "company": comp["name"],
            "title": title,
            "location": (j.get("location") or "").strip(),
            "type": j.get("type") or "",
            "posted": posted.isoformat() if posted else "",
            "updated": updated.isoformat() if updated else "",
            "url": j.get("url") or "",
            "source": j.get("source") or "",
            "remote": remote,
            "salaryMin": sal_min,
            "salaryMax": sal_max,
            "salaryCurrency": sal_cur,
            "salarySource": sal_source,
            "yearsExperience": years or None,
            "levelSource": level_source,
            "applicationDeadline": deadline,
            "closingSoon": bool(deadline_days is not None and 0 <= deadline_days <= CLOSING_DAYS),
            "sector": comp["sector"],
            "roleFamily": fam,
            "level": lvl,
            "metro": metros[0] if metros else "",
            "metros": metros,
            "isHardTech": comp["isHardTech"],
            "postedDaysAgo": days,
            "updatedDaysAgo": upd_days,
            "stale": bool(upd_days is not None and upd_days > STALE_DAYS),
            "companyRecentlyRaised": comp["raised"] is not None,
            "il30": comp["il30"],
            "clearanceLikely": clearance,
            "usPersonLikely": us_person,
            "trades": trades,
            "internSummer2027": lvl == "intern" and bool(SUMMER_2027.search(title)),
            "generalApplication": fam == "general",
            "groupKey": group_key(title),
        })

    # deterministic order: newest first (undated last), then company, title, id
    out_jobs.sort(key=lambda x: (x["posted"] == "", x["company"].lower(), x["title"].lower(), x["id"]))
    out_jobs.sort(key=lambda x: x["posted"] or "0000", reverse=True)

    # per-location clones: same company + same normalised title -> one row (the newest posting) that
    # carries the others; every posting keeps its own id and URL so the row can expand to them
    groups = OrderedDict()
    for x in out_jobs:
        groups.setdefault((x["company"], x["groupKey"]), []).append(x)
    for members in groups.values():
        members.sort(key=lambda x: (x["posted"] or "0000", bool(x["salaryMin"] or x["salaryMax"]), x["id"]), reverse=True)
        primary = members[0]
        first_posted = min((x["posted"] for x in members if x["posted"]), default="")
        for x in members:
            x["groupPrimary"] = x is primary
            x["newThisWeek"] = bool(first_posted and (today - date.fromisoformat(first_posted)).days <= NEW_DAYS)
            if x is not primary:
                x["groupId"] = primary["id"]          # clones point at their primary; primaries are their own group
        primary["groupSize"] = len(members)
        primary["groupFirstPosted"] = first_posted
        primary["groupLocations"] = sorted({m["location"] for m in members if m["location"]})
        primary["groupMetros"] = sorted({mm for m in members for mm in m["metros"]})
    for x in out_jobs:
        del x["groupKey"]

    # hiring surge: new postings per company in the last 14 days vs the 14 before, from the history file
    history = update_history(load_history(), out_jobs, today)
    surge = surge_counts(history, today)
    roles = Counter(x["company"] for x in out_jobs if x["groupPrimary"])
    for c in companies.values():
        rec, pri = surge.get(c["name"], (0, 0))
        c["recent14"], c["prior14"], c["surge"] = rec, pri, is_surge(rec, pri)
        c["roles"] = roles.get(c["name"], 0)
        c["newestPosted"] = max((x["posted"] for x in out_jobs if x["company"] == c["name"]), default="")

    totals = {
        "jobs": len(out_jobs),
        "companies": len(companies),
        "remote": sum(1 for x in out_jobs if x["remote"]),
        "withSalary": sum(1 for x in out_jobs if x["salaryMin"] or x["salaryMax"]),
        "stale": sum(1 for x in out_jobs if x["stale"]),
        "hardTech": sum(1 for x in out_jobs if x["isHardTech"]),
        "clearance": sum(1 for x in out_jobs if x["clearanceLikely"]),
        "il30": sum(1 for x in out_jobs if x["il30"]),
        "recentlyRaised": sum(1 for x in out_jobs if x["companyRecentlyRaised"]),
        "interns": sum(1 for x in out_jobs if x["level"] == "intern"),
        "summer2027": sum(1 for x in out_jobs if x["internSummer2027"]),
        "trades": sum(1 for x in out_jobs if x["trades"]),
        "descriptionSignals": sum(1 for v in desc_signals.values() if v and v[0]),
        "boardsWithDescriptions": len(cache.get("boards", {})),
        "withSalaryStructured": sum(1 for x in out_jobs if x["salarySource"] in ("ats", "ats-hourly")),
        "withSalaryFromPosting": sum(1 for x in out_jobs if x["salarySource"] in ("posting", "posting-hourly")),
        "withSalaryHourly": sum(1 for x in out_jobs if x["salarySource"] in ("ats-hourly", "posting-hourly")),
        "levelFromTitle": sum(1 for x in out_jobs if x["levelSource"] == "title"),
        "levelFromDescription": sum(1 for x in out_jobs if x["levelSource"] == "description"),
        "levelDefault": sum(1 for x in out_jobs if x["levelSource"] == "default"),
        "roles": sum(1 for x in out_jobs if x["groupPrimary"]),
        "clones": sum(1 for x in out_jobs if not x["groupPrimary"]),
        "newThisWeek": sum(1 for x in out_jobs if x["groupPrimary"] and x["newThisWeek"]),
        "withDeadline": sum(1 for x in out_jobs if x["applicationDeadline"]),
        "closingSoon": sum(1 for x in out_jobs if x["groupPrimary"] and x["closingSoon"]),
        "surgeCompanies": sum(1 for c in companies.values() if c["surge"]),
        "surgeJobs": sum(1 for x in out_jobs if x["groupPrimary"] and companies[x["company"]]["surge"]),
        "lastUpdated": stats.get("lastUpdated", ""),
    }
    coverage = {
        "roleFamily": Counter(x["roleFamily"] for x in out_jobs),
        "level": Counter(x["level"] for x in out_jobs),
        "levelSource": Counter(x["levelSource"] for x in out_jobs),
        "salarySource": Counter(x["salarySource"] or "none" for x in out_jobs),
        "metro": Counter(m for x in out_jobs for m in x["metros"]),
        "metroUnresolved": sum(1 for x in out_jobs if not x["metros"]),
        "sector": Counter(x["sector"] for x in out_jobs),
        "stage": Counter(companies[x["company"]]["stageGroup"] for x in out_jobs),
    }

    enriched = OrderedDict([
        ("generated", today.isoformat()),
        ("source", "data/jobs_raw.json"),
        ("staleAfterDays", STALE_DAYS),
        ("raisedWindowDays", RAISED_WINDOW_DAYS),
        ("newDays", NEW_DAYS),
        ("closingDays", CLOSING_DAYS),
        ("surgeWindowDays", SURGE_WINDOW_DAYS),
        ("totals", totals),
        ("families", FAMILIES),
        ("levels", LEVELS),
        ("metros", METROS),
        ("stageGroups", STAGE_GROUPS),
        ("coverage", {k: (dict(v) if isinstance(v, Counter) else v) for k, v in coverage.items()}),
        ("companies", list(companies.values())),
        ("jobs", out_jobs),
    ])
    OUT_JSON.write_text(json.dumps(enriched, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    write_compact_js(enriched)
    write_company_index(enriched)
    HISTORY_PATH.write_text(json.dumps(history, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    if cache_touched:
        cache["updated"] = today.isoformat()
        CACHE_PATH.write_text(json.dumps(cache, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    return enriched


def canonical_url(job):
    """'' when the URL is the ATS default (rebuilt on the page from the id)."""
    jid, url, src = job["id"] or "", job["url"] or "", job["source"]
    if src == "greenhouse" and jid.startswith("gh-"):
        token, _, num = jid[3:].rpartition("-")
        if url == f"https://job-boards.greenhouse.io/{token}/jobs/{num}":
            return ""
    elif src == "ashby" and jid.startswith("ab-") and len(jid) > 40:
        if url == f"https://jobs.ashbyhq.com/{jid[3:-37]}/{jid[-36:]}":
            return ""
    elif src == "lever" and jid.startswith("lv-") and len(jid) > 40:
        if url == f"https://jobs.lever.co/{jid[3:-37]}/{jid[-36:]}":
            return ""
    return url


def write_compact_js(enriched):
    fam_codes = list(FAMILIES)
    lvl_codes = list(LEVELS)
    sectors = sorted({c["sector"] for c in enriched["companies"]})
    stage_codes = list(STAGE_GROUPS)
    currencies = ["USD"] + sorted({j["salaryCurrency"] for j in enriched["jobs"] if j["salaryCurrency"] and j["salaryCurrency"] != "USD"})
    comp_index = {}
    comp_rows = []
    for c in enriched["companies"]:
        comp_index[c["name"]] = len(comp_rows)
        flags = (1 if c["il30"] else 0) | (2 if c["isHardTech"] else 0) | (4 if c["inDatabase"] else 0) | (8 if c["surge"] else 0)
        r = c["raised"] or {}
        comp_rows.append([c["name"], sectors.index(c["sector"]), stage_codes.index(c["stageGroup"]), flags,
                          r.get("amount", ""), r.get("round", ""), r.get("month", ""), c["fundingStage"], c["jobs"],
                          c["canonical"] if c["canonical"] != c["name"] else "",
                          c["recent14"], c["prior14"], c["roles"]])
    row_index = {}
    for i, j in enumerate(enriched["jobs"]):
        if j["groupPrimary"]:
            row_index[j["id"]] = i
    job_rows = []
    for j in enriched["jobs"]:
        flags = ((1 if j["remote"] else 0) | (2 if j["stale"] else 0) | (4 if j["clearanceLikely"] else 0)
                 | (8 if j["usPersonLikely"] else 0) | (16 if j["trades"] else 0) | (32 if j["internSummer2027"] else 0)
                 | (64 if j["generalApplication"] else 0)
                 | (128 if j["salarySource"] in ("posting", "posting-hourly") else 0)
                 | (256 if j["salarySource"] in ("ats-hourly", "posting-hourly") else 0)
                 | (512 if j["levelSource"] == "description" else 0))
        job_rows.append([
            j["id"], comp_index[j["company"]], j["title"], j["location"], j["posted"], canonical_url(j),
            fam_codes.index(j["roleFamily"]), lvl_codes.index(j["level"]), ",".join(j["metros"]),
            j["salaryMin"] or 0, j["salaryMax"] or 0,
            currencies.index(j["salaryCurrency"]) if j["salaryCurrency"] in currencies else 0,
            flags, j["postedDaysAgo"] if j["postedDaysAgo"] is not None else -1,
            j["updatedDaysAgo"] if j["updatedDaysAgo"] is not None else -1,
            -1 if j["groupPrimary"] else row_index[j["groupId"]],
            j["applicationDeadline"],
        ])
    payload = OrderedDict([
        ("generated", enriched["generated"]),
        ("staleAfterDays", STALE_DAYS),
        ("raisedWindowDays", RAISED_WINDOW_DAYS),
        ("newDays", NEW_DAYS),
        ("closingDays", CLOSING_DAYS),
        ("surgeWindowDays", SURGE_WINDOW_DAYS),
        ("totals", enriched["totals"]),
        ("families", [[k, v] for k, v in FAMILIES.items()]),
        ("levels", [[k, v] for k, v in LEVELS.items()]),
        ("metros", [[k, v] for k, v in METROS.items()]),
        ("stages", [[k, v] for k, v in STAGE_GROUPS.items()]),
        ("sectors", sectors),
        ("currencies", currencies),
        ("companyFields", ["name", "sector", "stage", "flags", "raisedAmount", "raisedRound", "raisedMonth", "fundingStage", "jobs", "canonical", "recent14", "prior14", "roles"]),
        ("jobFields", ["id", "company", "title", "location", "posted", "url", "family", "level", "metros", "salaryMin", "salaryMax", "currency", "flags", "daysAgo", "updatedDaysAgo", "group", "deadline"]),
        ("companies", comp_rows),
        ("jobs", job_rows),
    ])
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    OUT_JS.write_text(
        "// Auto-generated by scripts/enrich_jobs.py — do not edit by hand.\n"
        f"// Generated {enriched['generated']} · {enriched['totals']['jobs']} jobs across {enriched['totals']['companies']} companies\n"
        "// Row layouts: see companyFields / jobFields. Company flags: 1=IL30 2=hard-tech 4=in database 8=hiring surge.\n"
        "// Job flags: 1=remote 2=stale 4=clearance 8=US person 16=trades 32=summer-2027 intern 64=general application\n"
        "//   128=salary parsed from the posting text 256=salary annualised from an hourly rate (2,080 h) 512=level read from years of experience.\n"
        "// group: -1 for a role's primary row, else the index of the primary row this posting is a per-location clone of.\n"
        "// An empty url means the ATS default, rebuilt from the id on the page.\n"
        "window.JOBS_V2 = " + body + ";\n",
        encoding="utf-8",
    )


def write_company_index(enriched):
    """Small per-company index for company pages: load the 3 MB board only when a company has postings."""
    index = {}
    for c in enriched["companies"]:
        row = [c["jobs"], c["roles"], c["newestPosted"], (1 if c["surge"] else 0), c["recent14"]]
        index[c["canonical"]] = row
        if c["name"] != c["canonical"]:
            index[c["name"]] = row
    body = json.dumps(OrderedDict(sorted(index.items())), ensure_ascii=False, separators=(",", ":"))
    OUT_INDEX_JS.write_text(
        "// Auto-generated by scripts/enrich_jobs.py — do not edit by hand.\n"
        f"// Generated {enriched['generated']} · company -> [postings, distinct roles, newest posted, hiring surge, postings in last 14 days]\n"
        "window.JOBS_COMPANY_INDEX = " + body + ";\n",
        encoding="utf-8",
    )


def print_summary(enriched):
    t = enriched["totals"]
    n = max(1, t["jobs"])
    cov = enriched["coverage"]
    print(f"[enrich] {t['jobs']} jobs, {t['companies']} companies, generated {enriched['generated']}")
    print(f"[enrich] hard-tech {t['hardTech']} ({100*t['hardTech']//n}%) · stale {t['stale']} · remote {t['remote']} · salary {t['withSalary']}")
    print(f"[enrich] clearance {t['clearance']} (description signals {t['descriptionSignals']}) · il30 {t['il30']} · recently raised {t['recentlyRaised']} · interns {t['interns']} (summer 2027: {t['summer2027']}) · trades {t['trades']}")
    other = cov["roleFamily"].get("other", 0)
    print(f"[enrich] role family resolved {100*(n-other)//n}% (other={other}); metro resolved {100*(n-cov['metroUnresolved'])//n}% (unresolved={cov['metroUnresolved']})")
    print("[enrich] families: " + ", ".join(f"{k}={v}" for k, v in sorted(cov["roleFamily"].items(), key=lambda kv: -kv[1])))
    print("[enrich] levels: " + ", ".join(f"{k}={v}" for k, v in cov["level"].items()))
    print(f"[enrich] level source: title {t['levelFromTitle']} · description {t['levelFromDescription']} · default {t['levelDefault']} "
          f"(explicit {100*(t['levelFromTitle']+t['levelFromDescription'])//n}%)")
    print(f"[enrich] salary: structured {t['withSalaryStructured']} · from posting text {t['withSalaryFromPosting']} · of which hourly annualised {t['withSalaryHourly']} "
          f"· total {t['withSalary']} ({100*t['withSalary']//n}%)")
    print(f"[enrich] roles {t['roles']} (clones folded: {t['clones']}) · new this week {t['newThisWeek']} · deadlines {t['withDeadline']} (closing soon {t['closingSoon']}) "
          f"· surge companies {t['surgeCompanies']} ({t['surgeJobs']} roles)")
    print("[enrich] metros: " + ", ".join(f"{k}={v}" for k, v in sorted(cov["metro"].items(), key=lambda kv: -kv[1])))
    print(f"[enrich] wrote {OUT_JSON.name} ({OUT_JSON.stat().st_size//1024} KB), {OUT_JS.name} ({OUT_JS.stat().st_size//1024} KB), {OUT_INDEX_JS.name} ({OUT_INDEX_JS.stat().st_size//1024} KB), {HISTORY_PATH.name}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--today", help="reference date YYYY-MM-DD (default: UTC today)")
    ap.add_argument("--no-fetch", action="store_true", help="skip the ATS description pass; use the cache as-is")
    ap.add_argument("--force-fetch", action="store_true", help="re-fetch every board, ignoring the cache")
    ap.add_argument("--fetch-limit", type=int, default=None, help="debug: fetch at most N boards")
    args = ap.parse_args(argv)
    today = parse_date(args.today) if args.today else TODAY_FALLBACK
    if not today:
        print("bad --today", file=sys.stderr)
        return 2
    if not RAW_PATH.exists():
        print(f"[enrich] {RAW_PATH} missing; nothing to do", file=sys.stderr)
        return 1
    enriched = enrich(today, fetch=not args.no_fetch, force_fetch=args.force_fetch, fetch_limit=args.fetch_limit)
    print_summary(enriched)
    return 0


if __name__ == "__main__":
    sys.exit(main())
