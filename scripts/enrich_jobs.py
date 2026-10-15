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

Outputs:
  data/jobs_enriched.json      full records (compact JSON)
  data/jobs_enriched.js        columnar version for the page (window.JOBS_V2)
  data/jobs_desc_signals.json  description-signal cache (written by the
                               fetch pass; also carries Greenhouse
                               first_published dates, which are earlier
                               than the updated_at the fetcher stores)

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
OUT_JSON = DATA / "jobs_enriched.json"
OUT_JS = DATA / "jobs_enriched.js"

STALE_DAYS = 90
RAISED_WINDOW_DAYS = 90
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
    ("remote", "Remote"),
    ("intl",   "International"),
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
    ("engineering", _rx(r"\bengineer|\bengineering\b|\barchitect\b|\bdevelopment\b|\bdesign\b")),
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
    m = INTL_RX.search(low)
    if m:
        found.append((m.start(), "intl"))
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
    t = html.unescape(html_text or "")
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def _signal_flags(text):
    flags = 0
    if CLEARANCE_DESC.search(text):
        flags |= 1
    if US_PERSON_DESC.search(text):
        flags |= 2
    return flags


def fetch_board_signals(kind, slug):
    """Return {job_id: [flags, first_published]} for one board, or None on failure."""
    import requests  # only needed for the fetch pass
    headers = {"User-Agent": "InnovatorsLeague-JobsBot/1.0", "Accept": "application/json"}
    if kind == "gh":
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    elif kind == "ab":
        url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
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
            out = {}
            if kind == "gh":
                for j in data.get("jobs", []):
                    fp = (j.get("first_published") or "")[:10]
                    up = (j.get("updated_at") or "")[:10]
                    out[f"gh-{slug}-{j.get('id')}"] = [_signal_flags(_plain(j.get("content", ""))), fp if fp and fp < up else ""]
            elif kind == "ab":
                for j in data.get("jobs", []):
                    text = j.get("descriptionPlain") or _plain(j.get("descriptionHtml", ""))
                    out[f"ab-{slug}-{j.get('id')}"] = [_signal_flags(text), ""]
            else:
                if not isinstance(data, list):
                    return None
                for j in data:
                    parts = [j.get("descriptionPlain") or "", j.get("additionalPlain") or ""]
                    for lst in j.get("lists", []) or []:
                        parts.append(_plain(lst.get("content", "")))
                    out[f"lv-{slug}-{j.get('id')}"] = [_signal_flags(" ".join(parts)), ""]
            return out
        if r.status_code in (404, 410):
            return {}
        time.sleep(2 * (attempt + 1))
    return None


def refresh_signal_cache(jobs, cache, force=False, limit=None, workers=8):
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
        futs = {ex.submit(fetch_board_signals, bk[0], bk[1]): (bk, key, h) for bk, key, h in todo}
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
            for jid, (flags, fp) in res.items():
                if flags or fp:
                    cache["jobs"][jid] = [flags, fp]
            cache["boards"][key] = {"ids": h, "n": len(res)}
    live_keys = {f"{bk[0]}:{bk[1]}" for bk in boards}
    for key in [k for k in cache["boards"] if k not in live_keys]:
        del cache["boards"][key]
    live_ids = {j["id"] for j in jobs}
    for jid in [k for k in cache["jobs"] if k not in live_ids]:
        del cache["jobs"][jid]
    print(f"[enrich]   fetched {ok} boards, {fail} failed, {len(cache['jobs'])} jobs with signals or earlier publish dates cached")
    return ok, fail


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
    cache = {"version": 2, "boards": {}, "jobs": {}}
    if CACHE_PATH.exists():
        try:
            loaded = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if loaded.get("version") == 2:
                cache = loaded
        except ValueError:
            pass
    cache_touched = False
    if fetch:
        try:
            refresh_signal_cache(raw, cache, force=force_fetch, limit=fetch_limit)
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
        sig = desc_signals.get(j.get("id")) or [0, ""]
        updated = parse_date(j.get("posted"))           # the ATS "last activity" date the fetcher stores
        first_pub = parse_date(sig[1]) if len(sig) > 1 and sig[1] else None
        posted = first_pub if first_pub and (not updated or first_pub < updated) else updated
        days = (today - posted).days if posted else None
        if days is not None and days < 0:
            days = 0
        upd_days = (today - updated).days if updated else None
        if upd_days is not None and upd_days < 0:
            upd_days = 0
        fam = role_family(title)
        lvl = job_level(title)
        db_rec = db.get(comp["canonical"])
        metros = job_metros(j.get("location"), j.get("remote"), db_rec["location"] if db_rec else "")
        remote = bool(j.get("remote")) or "remote" in metros
        clearance = bool(CLEARANCE_TITLE.search(title)) or bool(sig[0] & 1)
        us_person = bool(sig[0] & 2)
        trades = fam not in ROLE_FAMILY_SKIP_TRADES and bool(TRADES.search(title)) and lvl != "intern"
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
            "salaryMin": j.get("salaryMin"),
            "salaryMax": j.get("salaryMax"),
            "salaryCurrency": j.get("salaryCurrency"),
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
        })

    # deterministic order: newest first (undated last), then company, title, id
    out_jobs.sort(key=lambda x: (x["posted"] == "", x["company"].lower(), x["title"].lower(), x["id"]))
    out_jobs.sort(key=lambda x: x["posted"] or "0000", reverse=True)

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
        "lastUpdated": stats.get("lastUpdated", ""),
    }
    coverage = {
        "roleFamily": Counter(x["roleFamily"] for x in out_jobs),
        "level": Counter(x["level"] for x in out_jobs),
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
        flags = (1 if c["il30"] else 0) | (2 if c["isHardTech"] else 0) | (4 if c["inDatabase"] else 0)
        r = c["raised"] or {}
        comp_rows.append([c["name"], sectors.index(c["sector"]), stage_codes.index(c["stageGroup"]), flags,
                          r.get("amount", ""), r.get("round", ""), r.get("month", ""), c["fundingStage"], c["jobs"],
                          c["canonical"] if c["canonical"] != c["name"] else ""])
    job_rows = []
    for j in enriched["jobs"]:
        flags = ((1 if j["remote"] else 0) | (2 if j["stale"] else 0) | (4 if j["clearanceLikely"] else 0)
                 | (8 if j["usPersonLikely"] else 0) | (16 if j["trades"] else 0) | (32 if j["internSummer2027"] else 0)
                 | (64 if j["generalApplication"] else 0))
        job_rows.append([
            j["id"], comp_index[j["company"]], j["title"], j["location"], j["posted"], canonical_url(j),
            fam_codes.index(j["roleFamily"]), lvl_codes.index(j["level"]), ",".join(j["metros"]),
            j["salaryMin"] or 0, j["salaryMax"] or 0,
            currencies.index(j["salaryCurrency"]) if j["salaryCurrency"] in currencies else 0,
            flags, j["postedDaysAgo"] if j["postedDaysAgo"] is not None else -1,
            j["updatedDaysAgo"] if j["updatedDaysAgo"] is not None else -1,
        ])
    payload = OrderedDict([
        ("generated", enriched["generated"]),
        ("staleAfterDays", STALE_DAYS),
        ("raisedWindowDays", RAISED_WINDOW_DAYS),
        ("totals", enriched["totals"]),
        ("families", [[k, v] for k, v in FAMILIES.items()]),
        ("levels", [[k, v] for k, v in LEVELS.items()]),
        ("metros", [[k, v] for k, v in METROS.items()]),
        ("stages", [[k, v] for k, v in STAGE_GROUPS.items()]),
        ("sectors", sectors),
        ("currencies", currencies),
        ("companyFields", ["name", "sector", "stage", "flags", "raisedAmount", "raisedRound", "raisedMonth", "fundingStage", "jobs", "canonical"]),
        ("jobFields", ["id", "company", "title", "location", "posted", "url", "family", "level", "metros", "salaryMin", "salaryMax", "currency", "flags", "daysAgo", "updatedDaysAgo"]),
        ("companies", comp_rows),
        ("jobs", job_rows),
    ])
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    OUT_JS.write_text(
        "// Auto-generated by scripts/enrich_jobs.py — do not edit by hand.\n"
        f"// Generated {enriched['generated']} · {enriched['totals']['jobs']} jobs across {enriched['totals']['companies']} companies\n"
        "// Row layouts: see companyFields / jobFields. Company flags: 1=IL30 2=hard-tech 4=in database.\n"
        "// Job flags: 1=remote 2=stale 4=clearance 8=US person 16=trades 32=summer-2027 intern 64=general application.\n"
        "// An empty url means the ATS default, rebuilt from the id on the page.\n"
        "window.JOBS_V2 = " + body + ";\n",
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
    print("[enrich] metros: " + ", ".join(f"{k}={v}" for k, v in sorted(cov["metro"].items(), key=lambda kv: -kv[1])))
    print(f"[enrich] wrote {OUT_JSON.name} ({OUT_JSON.stat().st_size//1024} KB) and {OUT_JS.name} ({OUT_JS.stat().st_size//1024} KB)")


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
