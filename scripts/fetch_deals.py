#!/usr/bin/env python3
"""
Deal Flow Fetcher for The Innovators League
Extracts funding round data from RSS news and Crunchbase News.
Merges with existing DEAL_TRACKER to keep historical data.

Sources:
  - news_raw.json (from aggregate_news.js — funding-type articles)
  - Crunchbase News RSS (funding announcements)
  - TechCrunch funding tag RSS

Free APIs only — no paid Crunchbase/PitchBook keys needed.
"""

import json
import re
import sys
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"
NAME_COLLISIONS_PATH = DATA_DIR / "name_collisions.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))

# A feed deal is never created for a company data.js records as listed,
# acquired or dead: "SpaceX raises" in Oct 2026 was a Satlyt round, and a
# listed company's raises are offerings this feed cannot parse.
INACTIVE_STATUSES = {"ipo", "acquired", "dead"}
# A round with no stage label that is under this share of the company's
# recorded totalRaised is almost always another company or a misparse
# ("Hadrian raises $40M" was the Dutch security firm, not the $1.7B factory).
MAGNITUDE_FLOOR = 0.05

# RSS feeds specifically for funding news
FUNDING_FEEDS = [
    # Original feeds
    ("Crunchbase News", "https://news.crunchbase.com/feed/"),
    ("TechCrunch Startups", "https://techcrunch.com/category/startups/feed/"),
    # Expanded coverage — Tier 1 pipeline addition
    ("TechCrunch Venture", "https://techcrunch.com/category/venture/feed/"),
    ("Business Wire Funding", "https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeGVpRWQ=="),
    ("GlobeNewswire Funding", "https://www.globenewswire.com/RssFeed/subjectcode/24-Funding%20Announcements/feedTitle/GlobeNewswire%20-%20Funding%20Announcements"),
    ("PR Newswire Funding", "https://www.prnewswire.com/rss/financial-announcements-venture-capital-rss.xml"),
    ("VentureBeat Deals", "https://venturebeat.com/category/business/deals/feed/"),
]

# Company aliases — dynamically loaded from master company list
COMPANY_ALIASES = {}

# Filled by init_matcher(). data.js records (name -> status/totalRaised), the
# squashed-name indexes used to prefer a longer company, and the hand-kept
# collision list in data/name_collisions.json.
DB_COMPANIES = {}
_DB_BY_KEY = {}
_ALIAS_BY_KEY = {}
CONTEXT_GUARDS = {}
DIFFERENT = {}
# Deals the guards dropped this run, printed by main() so a wrong skip can be seen.
SKIPPED = []


def _squash(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def _money_millions(text):
    """'$1.7B+' -> 1700.0, '~$110-111M' -> 110.0, '€30M' -> 30.0; None when no figure.

    Currencies are not converted: the magnitude guard is a 5% test, and a
    euro-for-dollar slip moves it by a few points at most.
    """
    m = re.search(r'[$€£]\s?(\d+(?:[.,]\d+)*)\s*(?:[-–]\s*\d+(?:\.\d+)?\s*)?'
                  r'(K|M|B|bn|mm|thousand|million|billion)\b', text or '', re.I)
    if not m:
        return None
    try:
        num = float(m.group(1).replace(',', ''))
    except ValueError:
        return None
    unit = m.group(2).lower()
    if unit in ('b', 'bn', 'billion'):
        return num * 1000
    if unit in ('k', 'thousand'):
        return num / 1000
    return num


def load_db_companies(path=DATA_JS_PATH):
    """name -> {status, raised, raised_m} for every COMPANIES record in data.js.

    Uses the data-quality gate's pure-Python parser, so the daily sync needs
    no Node step. Any failure returns {} and the status and magnitude guards
    stand down for the run instead of failing the sync.
    """
    try:
        from validate_data_quality import company_objects, gv
        out = {}
        for o in company_objects(Path(path).read_text()):
            name = gv(o, "name")
            if not name:
                continue
            raised = gv(o, "totalRaised") or ""
            out[name] = {"status": (gv(o, "status") or "").lower(), "raised": raised,
                         "raised_m": _money_millions(raised)}
        return out
    except Exception as e:                                   # noqa: BLE001
        print(f"  WARNING: could not read COMPANIES from data.js ({type(e).__name__}: {e}); "
              "status and magnitude guards are off this run")
        return {}


def load_name_collisions(path=NAME_COLLISIONS_PATH):
    """(context guards, different companies) from data/name_collisions.json.

    context guards:      DB name -> (compiled not_if regex, note)
    different companies: squashed name -> {name, not: squashed DB names, note}
    A missing or unreadable file disables the guard rather than the feed.
    """
    try:
        raw = json.loads(Path(path).read_text())
    except FileNotFoundError:
        return {}, {}
    except (OSError, ValueError) as e:
        print(f"  WARNING: {path} unreadable ({e}); name-collision guard is off this run")
        return {}, {}
    guards = {}
    for company, g in (raw.get("context_guards") or {}).items():
        if not isinstance(g, dict) or not g.get("not_if"):
            continue
        try:
            guards[company] = (re.compile(g["not_if"], re.I), g.get("note", ""))
        except re.error as e:
            print(f"  WARNING: bad not_if pattern for {company}: {e}")
    different = {}
    for e in raw.get("different_companies") or []:
        nots = e.get("not") or []
        nots = [nots] if isinstance(nots, str) else nots
        if e.get("name") and nots:
            entry = different.setdefault(_squash(e["name"]),
                                         {"name": e["name"], "not": set(), "note": e.get("note", "")})
            entry["not"].update(_squash(n) for n in nots)
    return guards, different


def init_matcher(data_js=DATA_JS_PATH, collisions=NAME_COLLISIONS_PATH):
    """Load everything match_company() and the deal guards read."""
    global COMPANY_ALIASES, DB_COMPANIES, _DB_BY_KEY, _ALIAS_BY_KEY, CONTEXT_GUARDS, DIFFERENT
    COMPANY_ALIASES = load_company_aliases()
    DB_COMPANIES = load_db_companies(data_js)
    _DB_BY_KEY = {_squash(n): n for n in DB_COMPANIES}
    _ALIAS_BY_KEY = {_squash(a): c for a, c in COMPANY_ALIASES.items()}
    CONTEXT_GUARDS, DIFFERENT = load_name_collisions(collisions)


def _db_record(company):
    """data.js record for a matched company, tolerating spelling variants."""
    return DB_COMPANIES.get(company) or DB_COMPANIES.get(_DB_BY_KEY.get(_squash(company), ""))


def load_company_aliases():
    """Load company aliases from master company list (534 companies)."""
    master_path = Path(__file__).parent / "company_master_list.js"
    if not master_path.exists():
        print("  WARNING: company_master_list.js not found")
        return {}

    content = master_path.read_text()
    aliases = {}

    # Common English words that shouldn't match as company names in funding headlines
    GENERIC_WORDS = {
        'aging', 'allies', 'arctic', 'array', 'atomic', 'audio', 'beacon',
        'carbon', 'charge', 'condor', 'desert', 'energy', 'fabric', 'falcon',
        'forge', 'fusion', 'garden', 'ghost', 'global', 'harbor', 'ignite',
        'impact', 'launch', 'matter', 'merge', 'neural', 'ocean', 'orbit',
        'radar', 'radiant', 'rocket', 'scout', 'shield', 'signal', 'solar',
        'space', 'spark', 'target', 'terra', 'tower', 'vapor', 'vertex',
        'blimps', 'agtech', 'quantum', 'robotics',
        'autonomous drones', 'laser communications', 'space laser',
        'optical inter-satellite link', 'road runner',
    }

    for match in re.finditer(
        r'name:\s*"([^"]+)".*?aliases:\s*\[([^\]]*)\]',
        content, re.DOTALL
    ):
        name = match.group(1)
        alias_str = match.group(2)
        # Always add the full canonical name (lowercase)
        aliases[name.lower()] = name
        # Add each alias with filtering
        for alias_match in re.finditer(r'"([^"]+)"', alias_str):
            alias = alias_match.group(1).lower()
            # Skip short aliases and generic words
            if len(alias) < 5:
                continue
            if alias in GENERIC_WORDS:
                continue
            # Single-word aliases under 8 chars are risky — require them to be proper nouns
            # (i.e., the original alias starts with uppercase and is a single word)
            orig = alias_match.group(1)
            if ' ' not in alias and len(alias) < 8 and not orig[0].isupper():
                continue
            # The master list also carries product names and topic phrases
            # ("shipbuilding" -> Saronic, "tunneling" -> The Boring Company,
            # "autonomous defense" -> Mara). Fine for news tagging, wrong for
            # crediting a funding round: "a shipbuilding startup raises $600M"
            # is not Saronic. Only spellings of the company's own name pass.
            if not _is_name_alias(alias, name):
                continue
            aliases[alias] = name

    return aliases


# Corporate suffixes that may follow a company's core name in a headline.
_CORP_SUFFIX = {
    'inc', 'corp', 'corporation', 'co', 'company', 'technologies', 'technology', 'tech',
    'labs', 'lab', 'industries', 'systems', 'space', 'aerospace', 'robotics', 'ai', 'energy',
    'bio', 'biosciences', 'therapeutics', 'defense', 'dynamics', 'computing', 'power',
    'group', 'holdings', 'ltd', 'limited', 'gmbh', 'sa', 'ag', 'plc', 'llc', 'hq',
}


def _core_name(name):
    words = re.sub(r'[^a-z0-9 ]', ' ', name.lower()).split()
    if words and words[0] == 'the':
        words = words[1:]
    while len(words) > 1 and words[-1] in _CORP_SUFFIX:
        words.pop()
    return ''.join(words)


def _is_name_alias(alias, canonical):
    """True if `alias` is a spelling of the company's own name, not a product or topic."""
    squash = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
    return squash(alias) == squash(canonical) or _core_name(alias) == _core_name(canonical)


# Patterns for extracting company names from unknown funding headlines
DISCOVERY_PATTERNS = [
    r'^([A-Z][A-Za-z0-9\s&.\'-]+?)\s+(?:raises?|secures?|closes?|lands?|gets?|nabs?|bags?)\s',
    r'^([A-Z][A-Za-z0-9\s&.\'-]+?),?\s+(?:a |an |the )?(?:\w+ )?startup,?\s+(?:raises?|secures?)',
    r'(?:startup|company)\s+([A-Z][A-Za-z0-9\s&.\'-]+?)\s+(?:raises?|secures?|closes?)\s',
]


def extract_unknown_company(title):
    """Try to extract a company name from a funding headline for unknown companies."""
    for pattern in DISCOVERY_PATTERNS:
        match = re.search(pattern, title)
        if match:
            name = match.group(1).strip().rstrip(',')
            # Filter out generic words that aren't company names
            skip_words = {'this', 'the', 'a', 'an', 'new', 'report', 'how', 'why',
                          'what', 'when', 'where', 'analysis', 'exclusive', 'breaking'}
            if name.lower() in skip_words or len(name) < 3 or len(name) > 50:
                continue
            return name
    return None

# Investor name normalization
INVESTOR_ALIASES = {
    "a16z": "a16z",
    "andreessen horowitz": "a16z",
    "founders fund": "Founders Fund",
    "sequoia": "Sequoia",
    "lux capital": "Lux Capital",
    "8vc": "8VC",
    "khosla": "Khosla Ventures",
    "general catalyst": "General Catalyst",
    "accel": "Accel",
    "benchmark": "Benchmark",
    "greylock": "Greylock",
    "tiger global": "Tiger Global",
    "coatue": "Coatue",
    "softbank": "SoftBank",
    "general atlantic": "General Atlantic",
    "thrive": "Thrive Capital",
    "lightspeed": "Lightspeed Venture Partners",
    # Expanded investor list
    "insight partners": "Insight Partners",
    "kleiner perkins": "Kleiner Perkins",
    "nea": "NEA",
    "new enterprise associates": "NEA",
    "bessemer": "Bessemer Venture Partners",
    "ivp": "IVP",
    "spark capital": "Spark Capital",
    "index ventures": "Index Ventures",
    "gv": "GV (Google Ventures)",
    "google ventures": "GV (Google Ventures)",
    "eclipse ventures": "Eclipse Ventures",
    "valor equity": "Valor Equity Partners",
    "capitalg": "CapitalG",
    "felicis": "Felicis Ventures",
    "norwest": "Norwest Venture Partners",
}


def fetch_rss(url, source_name):
    """Fetch and parse an RSS or Atom feed."""
    headers = {
        "User-Agent": "InnovatorsLeague-Bot/1.0 (https://innovatorsleague.com)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        items = []

        # Standard RSS <item> elements
        for item in root.iter("item"):
            title = item.findtext("title", "").strip()
            desc = item.findtext("description", "").strip()
            desc = re.sub(r'<[^>]+>', '', desc)[:500]
            pub_date = item.findtext("pubDate", "")
            link = item.findtext("link", "").strip()

            items.append({
                "title": title,
                "description": desc,
                "pubDate": pub_date,
                "link": link,
                "source": source_name
            })

        # Atom <entry> elements (GlobeNewswire, some Business Wire feeds)
        if not items:
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('.//atom:entry', ns) or root.findall('.//entry')
            for entry in entries:
                title = (entry.findtext('atom:title', '', ns) or entry.findtext('title', '')).strip()
                desc = (entry.findtext('atom:summary', '', ns) or entry.findtext('summary', '')).strip()
                desc = re.sub(r'<[^>]+>', '', desc)[:500]
                pub_date = (entry.findtext('atom:published', '', ns) or
                           entry.findtext('atom:updated', '', ns) or
                           entry.findtext('published', '') or
                           entry.findtext('updated', ''))
                link_el = entry.find('atom:link', ns) or entry.find('link')
                link = link_el.get('href', '') if link_el is not None else ''

                items.append({
                    "title": title,
                    "description": desc,
                    "pubDate": pub_date,
                    "link": link,
                    "source": source_name
                })

        return items
    except Exception as e:
        print(f"  Error fetching {source_name}: {e}")
        return []


# Words that mean a nearby dollar figure is NOT the size of this round.
# "targeting the $12 billion drilling market" is a TAM; "valued at $2.5B" is a
# valuation; "a $40B defense budget" is an appropriation. Each of these used to
# be recorded as money the company raised.
_NOT_A_ROUND = re.compile(
    r"\b(market|tam|industry|sector|opportunit|budget|appropriat|programme?|"
    r"contract|backlog|revenue|sales|valuation|valued|post-money|pre-money|"
    r"worth|cap|capitalization|deficit|economy|spending|forecast|projected|"
    r"expected to reach|by 20\d\d)\b", re.I)

# What may sit between the two ends of a range of figures.
_RANGE_GAP = re.compile(r"^\s*(?:-|–|—|to|or|and)\s*$", re.I)

# Words immediately around a figure that mean it IS the round.
_IS_A_ROUND = re.compile(
    r"\b(rais(?:e|es|ed|ing)|secur(?:e|es|ed|ing)|clos(?:e|es|ed|ing)|"
    r"land(?:s|ed)?|bag(?:s|ged)?|nab(?:s|bed)?|round|financing|investment|"
    r"funding|led by|oversubscribed|commitment)\b", re.I)


def parse_funding_amount(text):
    """Extract the size of THIS round from an article.

    The old version tried the billions pattern first across the whole string
    and returned the first hit. So "Durin raises $12 million to automate
    drilling, targeting the $12 billion drilling market" returned $12B — the
    market size, not the round — and Durin appeared on the site having raised
    twelve billion dollars. 139 of 346 deals in the feed were denominated in
    billions because of this, including "Cognition $40B Series A" and
    "Amca $510B IPO".

    Now every candidate figure is scored on the words around it: a figure
    sitting next to "raises" or "led by" is the round; one sitting next to
    "market", "valuation" or "budget" is disqualified outright. Ties break
    toward the EARLIEST qualifying figure, because the round is what a funding
    story leads with. Nothing is returned when no figure qualifies — a missing
    amount is recoverable, a fabricated one is not.
    """
    if not text:
        return None

    candidates = []
    figures = list(re.finditer(
            r'\$\s?(\d+(?:[.,]\d+)?)\s*(billion|million|bn|mm|[BbMm])\b'
            r'|\$\s?(\d{1,3}(?:,\d{3}){2,})\b', text))
    for i, m in enumerate(figures):
        if m.group(1):
            num = float(m.group(1).replace(',', ''))
            unit = m.group(2).lower()
            millions = num * (1000 if unit in ("billion", "bn", "b") else 1)
        else:
            millions = float(m.group(3).replace(',', '')) / 1e6

        # Disqualifiers bind TIGHTLY — a market size is named right next to its
        # figure ("$12 billion drilling market"). A wide window here would let
        # the market at the end of the sentence veto the round at the start,
        # which is the same sentence-level confusion in the other direction.
        # For the same reason the window stops at a neighbouring figure: in
        # "raises $250M Series C at $2.5B valuation" the valuation belongs to
        # the $2.5B, and until Oct 2026 it vetoed the round too, so the most
        # common shape of funding headline produced no deal. A range
        # ("the $5B-$10B market") still shares its words.
        lo, hi = max(0, m.start() - 45), m.end() + 32
        if i + 1 < len(figures) and figures[i + 1].start() < hi \
                and not _RANGE_GAP.match(text[m.end():figures[i + 1].start()]):
            hi = figures[i + 1].start()
        if i > 0 and figures[i - 1].end() > lo \
                and not _RANGE_GAP.match(text[figures[i - 1].end():m.start()]):
            lo = figures[i - 1].end()
        near = text[lo:hi]
        if _NOT_A_ROUND.search(near):
            continue
        # Qualifiers may sit further off — "raises" can lead a sentence that
        # names the figure several clauses later.
        wide = text[max(0, m.start() - 120): m.end() + 90]
        if not _IS_A_ROUND.search(wide):
            continue
        candidates.append((m.start(), millions))

    if not candidates:
        return None
    _, millions = min(candidates, key=lambda c: c[0])

    # A private round above $15B does not exist outside OpenAI/Anthropic scale,
    # and those are already tracked by hand. Treat it as a misparse we failed
    # to catch rather than a discovery.
    if millions > 15000 or millions <= 0:
        return None
    if millions >= 1000:
        b = millions / 1000
        return f"${b:.1f}B" if b != int(b) else f"${int(b)}B"
    return f"${int(millions)}M" if millions == int(millions) else f"${millions}M"


def parse_round_type(text):
    """Extract funding round type.

    The old patterns produced 61 rows claiming Series E through Series N for
    seed-stage companies. Two causes, both plain regex slips:

      "closed a series of funding rounds"  ->  Series O   ("series o|f")
      "in a round led by NEA"              ->  Series A   (any single letter
                                                           before "round")

    So the letter now has to stand alone as a word, be a plausible round
    letter, and not be the "of" in "a series of". Real seed-to-growth ladders
    run A-J; anything past J in a private frontier company is a misparse, not
    a discovery.
    """
    text_lower = (text or "").lower()
    patterns = [
        (r'\bpre-seed\b', lambda m: "Pre-Seed"),
        (r'\bseed\s+(?:round|funding|financing)\b', lambda m: "Seed"),
        # A standalone letter A-J, optionally "Series B-2". "series of" cannot
        # match because "of" is two letters and \b forbids a partial word.
        (r'\bseries\s+([a-j])(?:-(\d))?\b',
         lambda m: f"Series {m.group(1).upper()}" + (f"-{m.group(2)}" if m.group(2) else "")),
        (r'\bipo\b', lambda m: "IPO"),
        (r'\bspac\b', lambda m: "SPAC"),
        (r'\bdebt\s+(?:round|financing|facility)\b', lambda m: "Debt"),
        (r'\bgrant\b', lambda m: "Grant"),
    ]

    for pattern, formatter in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return formatter(match)

    if any(w in text_lower for w in ('funding', 'raise', 'round', 'investment')):
        return "Funding Round"
    return None


# Funding verbs: the company a headline is ABOUT is named before the first one.
_FUNDING_VERB = re.compile(
    r"\b(?:raises?|raised|raising|secures?|secured|lands?|landed|closes?|closed|bags?|bagged"
    r"|nabs?|nabbed|nets?|netted|pockets?|banks?|gets?|scores?|snags?|grabs?|attracts?|receives?|picks up|hauls? in"
    r"|announces?|completes?|wins?|draws?|pulls in|rakes in)\b", re.I)
# A name in these positions is context, not the subject: "ex-Palantir founders
# raise $22M", "Palantir-backed X raises", "a rival to Anduril raises".
#
# Names in a list share their marker: "former Google and SpaceX product
# manager", "ex-Google, SpaceX engineers", "SpaceX and Google alumni". Satlyt's
# $8M round was credited to SpaceX in Oct 2026 through exactly that gap. The
# list words must be capitalised (case-sensitive inside the otherwise
# case-insensitive patterns), so "from scratch, Neros raises" is not a list.
_PROPER = r"(?-i:[A-Z0-9][\w.&'’-]*)(?:\s+(?-i:[A-Z0-9][\w.&'’-]*))*"
_JOIN = r"(?:\s+(?:and|or|&)\s+|\s*&\s*|\s*/\s*)"
# A comma joins a list only after the people markers ("ex-Google, SpaceX");
# after "by"/"from" it ends the phrase: "Backed by Founders Fund, Neros raises".
_JOIN_COMMA = rf"(?:\s*,\s*(?:and\s+|or\s+)?|{_JOIN})"
_NOT_SUBJECT_BEFORE = re.compile(
    rf"(?:(?:\bex-|\bformer\s+|\balumni\s+of\s+|\bveterans?\s+of\s+)(?:{_PROPER}{_JOIN_COMMA})*"
    r"|(?:\blike\s+|\brival(?:s)?\s+(?:to\s+)?|\bvs\.?\s+|\bversus\s+|\bfrom\s+|\bby\s+|\bwith\s+"
    rf"|\bbacked\s+by\s+|\bout\s+of\s+|\bthe\s+next\s+)(?:{_PROPER}{_JOIN})*)$", re.I)
# People and offshoots of a company: "SpaceX engineers raise $10M" is not a SpaceX round.
_CONTEXT_NOUN = (r"(?:alum(?:ni|nus|na|s)?|veterans?|engineers?|founders?|co-?founders?|execs?"
                 r"|executives?|employees?|researchers?|scientists?|staffers?|insiders?"
                 r"|spinouts?|spin-?offs?|rivals?|competitors?)")
_NOT_SUBJECT_AFTER = re.compile(
    rf"^(?:-?{_JOIN}{_PROPER})*"
    r"(?:-?(?:backed|founded|alum(?:ni)?|veterans?|spinout|spin-?off|style|like|rival)\b"
    rf"|\s+{_CONTEXT_NOUN}\b"
    r"|['’]s\s+(?:former|ex-|rival|competitor|alum|founder|co-?founder))", re.I)

# The capitalised words that continue a name: "Monumental" + " Labs".
_NEXT_PROPER = re.compile(r"\s+[A-Z0-9][\w'’.&-]*")
# alias -> compiled word-boundary pattern, filled on first use.
_ALIAS_RX = {}


def _inside_aside(title, start, end, limit):
    """True when a name sits in a parenthetical or appositive before the verb.

    "Satlyt, founded by a former Google and SpaceX product manager, raises $8M"
    names SpaceX only to describe Satlyt. A name right after a comma is still a
    subject ("After a record year, Neros, the drone maker, raises"), so the
    appositive needs words between its opening comma and the name.
    """
    before, between = title[:start], title[end:limit]
    if before.rfind('(') > before.rfind(')') and ')' in between:
        return True
    c = before.rfind(',')
    return c >= 0 and re.search(r'\w', before[c + 1:]) is not None and ',' in between


def _full_name(title, start, end, limit):
    """The matched name plus the capitalised words after it, up to the verb."""
    while True:
        w = _NEXT_PROPER.match(title, end)
        if not w or w.end() > limit:
            return re.sub(r"['’]s?$", "", title[start:end])
        end = w.end()


def match_company(title, context="", rejected=None):
    """Return the tracked company a funding HEADLINE is about, or None.

    This used to be a bare substring test over headline + summary, taking the
    longest alias found anywhere. That credited rounds to whichever tracked
    company was merely mentioned, or whose name hid inside an ordinary word:
    "invention" -> Vention, "discover" -> Cover, "Kamara" -> Mara, "no matter"
    -> Matter, "ex-Palantir founders raise $22M" -> a Palantir Series A. By
    Oct 2026 most of the 231-deal feed was misattributed this way.

    Now the name must (1) sit in the headline on word boundaries, (2) come
    before the funding verb, since the subject leads, (3) not be framed as
    context ("ex-", "-backed", "rival to"), and (4) if it is a single word,
    appear capitalised, so the common noun never matches. The earliest
    qualifying name wins. A missed deal is recoverable; a misattributed one
    ends up on a company profile as fact.

    Oct 2026 additions, after two bad deals reached DEAL_TRACKER:
      - a name inside an appositive or parenthesis, or in a list after a
        context marker ("former Google and SpaceX product manager"), is
        context: Satlyt's $8M round had been credited to SpaceX;
      - the full proper noun decides between companies. If the name plus the
        capitalised words after it is exactly another data.js company or
        alias, that company wins ("Monumental Labs" is not Monumental); if it
        is a known different company in data/name_collisions.json, the match
        is dropped ("Navier AI" is not Navier);
      - context_guards in that file veto a company when the headline or its
        summary (`context`) gives it away: the Hadrian that "raises $40M to
        tackle AI-driven cyber threats" is the Dutch security firm.
    `rejected`, when a list, collects (company, reason) for matches the
    collision file vetoed, so the caller can log them.
    """
    if not title:
        return None
    verb = _FUNDING_VERB.search(title)
    limit = verb.start() if verb else len(title)
    best = None
    for alias, canonical in COMPANY_ALIASES.items():
        # Compiled once: 1,200+ patterns overflow re's own cache, which made
        # every headline cost ~170 ms of recompiling.
        rx = _ALIAS_RX.get(alias)
        if rx is None:
            rx = _ALIAS_RX[alias] = re.compile(
                rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])", re.I)
        for m in rx.finditer(title):
            if m.start() >= limit:
                break
            if ' ' not in alias and not title[m.start()].isupper():
                continue
            if _NOT_SUBJECT_BEFORE.search(title[:m.start()]) or _NOT_SUBJECT_AFTER.search(title[m.end():]):
                continue
            # A clause break between the name and the verb means the verb has
            # another subject: "Matter of time: Foo raises $14M".
            if re.search(r'[:|;]|\s[–—-]\s', title[m.end():limit]):
                continue
            if _inside_aside(title, m.start(), m.end(), limit):
                continue
            full = _squash(_full_name(title, m.start(), m.end(), limit))
            target = canonical
            other = _DB_BY_KEY.get(full) or _ALIAS_BY_KEY.get(full)
            if other and _squash(other) != _squash(canonical):
                target = other                   # the longer (or exact) company named
            else:
                # A one-word name followed by another capitalised word is part
                # of a longer proper noun ("Mara Kamara"), unless that word is
                # a corporate suffix ("Saronic Technologies").
                nxt = re.match(r"\s+([A-Z][\w'’.-]*)", title[m.end():])
                if ' ' not in alias and nxt and nxt.group(1).lower().strip('.') not in _CORP_SUFFIX:
                    continue
            diff = DIFFERENT.get(full)
            if diff and _squash(target) in diff["not"]:
                if rejected is not None:
                    rejected.append((target, f"'{diff['name']}' is a different company: {diff['note']}"))
                continue
            guard = CONTEXT_GUARDS.get(target)
            if guard and guard[0].search(f"{title} {context or ''}"):
                if rejected is not None:
                    rejected.append((target, f"context guard: {guard[1]}"))
                continue
            key = (m.start(), -len(alias))
            if best is None or key < best[0]:
                best = (key, target)
            break
    return best[1] if best else None


def match_investors(text):
    """Try to extract investor names from text.

    This used to be a naked substring test, so every short firm alias matched
    inside ordinary words: "nearly" and "beneath" both contain "nea", and
    "linear accelerator" contains both "nea" and "accel". NEA was consequently
    attached to a large share of the deal feed, including deals it had nothing
    to do with. Aliases now have to match on word boundaries.
    """
    text_lower = (text or "").lower()
    found = []
    for alias, canonical in INVESTOR_ALIASES.items():
        if re.search(rf"(?<![a-z0-9]){re.escape(alias.lower())}(?![a-z0-9])",
                     text_lower):
            if canonical not in found:
                found.append(canonical)
    return found


def is_funding_article(title, description):
    """Check if an article is about a funding round."""
    text = f"{title} {description}".lower()
    funding_keywords = [
        'raises', 'raised', 'funding', 'series', 'round',
        'valuation', 'venture', 'investment', 'seed round',
        'capital raise', 'financing'
    ]
    return any(kw in text for kw in funding_keywords)


_LISTED = re.compile(
    r"\b(pric(?:e|es|ed|ing)\s+(?:its\s+|an\s+|the\s+)?(?:ipo|shares|offering)"
    r"|debut(?:s|ed)?|beg(?:an|ins) trading|start(?:s|ed) trading|(?:is|was|now) listed"
    r"|went public|goes public|complet(?:e|es|ed) (?:its |an |the )?(?:ipo|listing|merger)"
    r"|clos(?:e|es|ed) (?:its |an |the )?(?:ipo|merger))\b", re.I)


def _skip(reason, company, headline):
    """Record a deal a guard dropped (printed by main) and return None."""
    SKIPPED.append({"company": company, "reason": reason, "headline": (headline or "")[:120]})
    return None


def extract_deal_from_article(article):
    """Try to extract a deal from a news article."""
    title = article.get("title", "")
    desc = article.get("description", "")
    full_text = f"{title} {desc}"

    # The headline itself must be a funding story. "Is Neko Health's body scan
    # worth it?" and "Peak XV ups Surge seed ceiling to $5M" mention money in
    # the summary but announce no round by the company named.
    if not _FUNDING_VERB.search(title):
        return None
    rejected = []
    company = match_company(title, desc, rejected)
    if not company:
        for name, why in rejected:
            _skip(why, name, title)
        return None

    amount = parse_funding_amount(full_text)
    if not amount:
        return None

    round_type = parse_round_type(full_text) or "Funding Round"
    # An IPO or SPAC "round" needs listing language. "Rebellions ... $3.4B IPO"
    # was a planned offering, not a listing, and a private company carrying an
    # IPO round fails the data-quality gate: Daily Data Sync failed 26-29 Sep
    # 2026 on exactly that. A pre-IPO private round is kept as "Pre-IPO".
    if round_type in ("IPO", "SPAC") and not _LISTED.search(full_text):
        if re.search(r'\bpre-?ipo\b', full_text, re.I):
            round_type = "Pre-IPO"
        else:
            return None

    # Guards that need the company's data.js record (none for companies the
    # master list tracks but data.js does not).
    rec = _db_record(company)
    if rec and rec["status"] in INACTIVE_STATUSES:
        return _skip(f"data.js status is '{rec['status']}'", company, title)
    if round_type == "Funding Round" and rec and rec.get("raised_m"):
        amt = _money_millions(amount)
        if amt is not None and amt < MAGNITUDE_FLOOR * rec["raised_m"]:
            return _skip(f"unlabelled {amount} round is under {MAGNITUDE_FLOOR:.0%} of recorded "
                         f"totalRaised {rec['raised']}", company, title)
    investors = match_investors(full_text)

    # Parse date
    pub_date = article.get("pubDate", "")
    try:
        dt = datetime.strptime(pub_date[:25].strip(), "%a, %d %b %Y %H:%M:%S")
        date_str = dt.strftime("%Y-%m")
    except Exception:
        date_str = datetime.now().strftime("%Y-%m")

    return {
        "company": company,
        "amount": amount,
        "round": round_type,
        "date": date_str,
        "investors": investors,
        "source": article.get("source", ""),
        "headline": title[:120],
    }


def load_existing_deals():
    """Load existing deals from data.js DEAL_TRACKER const."""
    if not DATA_JS_PATH.exists():
        return []

    with open(DATA_JS_PATH, 'r') as f:
        content = f.read()

    # Extract DEAL_TRACKER array
    match = re.search(r'const DEAL_TRACKER = \[([\s\S]*?)\];', content)
    if not match:
        return []

    # Parse the JS array into Python (simplified parser)
    deals = []
    block = match.group(1)
    obj_pattern = re.finditer(r'\{([^}]+)\}', block)

    for obj_match in obj_pattern:
        obj_str = obj_match.group(1)
        deal = {}
        for field in ['company', 'investor', 'amount', 'round', 'date', 'valuation', 'leadOrParticipant', 'headline']:
            field_match = re.search(rf'{field}:\s*"([^"]*)"', obj_str)
            if field_match:
                deal[field] = field_match.group(1)
        if deal.get('company'):
            deals.append(deal)

    return deals


def deduplicate_deals(existing, new_deals):
    """Merge new deals with existing, avoiding duplicates."""
    # Create a set of existing deal keys
    existing_keys = set()
    for d in existing:
        key = f"{d.get('company', '')}|{d.get('amount', '')}|{d.get('round', '')}|{d.get('date', '')}"
        existing_keys.add(key.lower())

    merged = list(existing)
    added = 0

    for deal in new_deals:
        key = f"{deal['company']}|{deal['amount']}|{deal['round']}|{deal['date']}"
        if key.lower() not in existing_keys:
            # Convert to DEAL_TRACKER format (one entry per investor)
            if deal['investors']:
                for i, investor in enumerate(deal['investors']):
                    entry = {
                        "company": deal["company"],
                        "investor": investor,
                        "amount": deal["amount"],
                        "round": deal["round"],
                        "date": deal["date"],
                        "valuation": "",
                        "leadOrParticipant": "lead" if i == 0 else "participant",
                        # Kept so a bad attribution can be traced to its source.
                        "headline": deal.get("headline", ""),
                    }
                    merged.append(entry)
                    added += 1
            else:
                entry = {
                    "company": deal["company"],
                    "investor": "Undisclosed",
                    "amount": deal["amount"],
                    "round": deal["round"],
                    "date": deal["date"],
                    "valuation": "",
                    "leadOrParticipant": "lead",
                    "headline": deal.get("headline", ""),
                }
                merged.append(entry)
                added += 1

            existing_keys.add(key.lower())

    return merged, added


def save_deals_json(deals):
    """Save merged deals to JSON for merge_data.py to consume."""
    output_path = DATA_DIR / "deals_auto.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(deals, f, indent=2)

    print(f"Saved {len(deals)} deals to {output_path}")


def save_discovered_companies(articles):
    """Extract and save unknown companies from funding articles for manual review."""
    discoveries = []
    seen_names = set()

    for article in articles:
        title = article.get("title", "")
        desc = article.get("description", "")
        full_text = f"{title} {desc}"

        # Skip if we can match a known company
        if match_company(full_text):
            continue

        # Must have a funding amount to be interesting
        amount = parse_funding_amount(full_text)
        if not amount:
            continue

        # Try to extract the company name from the headline
        company_name = extract_unknown_company(title)
        if not company_name or company_name.lower() in seen_names:
            continue

        seen_names.add(company_name.lower())

        # Parse date
        pub_date = article.get("pubDate", "")
        try:
            dt = datetime.strptime(pub_date[:25].strip(), "%a, %d %b %Y %H:%M:%S")
            date_str = dt.strftime("%Y-%m")
        except Exception:
            date_str = datetime.now().strftime("%Y-%m")

        discoveries.append({
            "name": company_name,
            "amount": amount,
            "round": parse_round_type(full_text) or "Funding Round",
            "investors": match_investors(full_text),
            "source": article.get("source", ""),
            "date": date_str,
            "headline": title[:150],
            "discoveredAt": datetime.now().strftime("%Y-%m-%d"),
        })

    if not discoveries:
        print("No new unknown companies discovered")
        return

    # Load existing discoveries and merge (keep most recent per company)
    discovery_path = DATA_DIR / "discovered_companies.json"
    existing = []
    if discovery_path.exists():
        try:
            with open(discovery_path) as f:
                existing = json.load(f)
        except Exception:
            existing = []

    existing_names = {d["name"].lower() for d in existing}
    for d in discoveries:
        if d["name"].lower() not in existing_names:
            existing.append(d)
            existing_names.add(d["name"].lower())

    # Sort by discovery date, keep most recent 50
    existing.sort(key=lambda d: d.get("discoveredAt", ""), reverse=True)
    existing = existing[:50]

    with open(discovery_path, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"Discovered {len(discoveries)} unknown companies (total queue: {len(existing)})")
    for d in discoveries[:5]:
        print(f"  NEW: {d['name']} — {d['amount']} {d['round']} ({d['source']})")


def main():
    print("=" * 60)
    print("Deal Flow Fetcher for The Innovators League")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Company aliases from the master list; status/totalRaised from data.js;
    # the hand-kept collision list from data/name_collisions.json.
    init_matcher()
    print(f"Loaded {len(COMPANY_ALIASES)} company aliases from master list, "
          f"{len(DB_COMPANIES)} data.js records for the status/size guards, "
          f"{len(CONTEXT_GUARDS)} context guards, {len(DIFFERENT)} known name collisions")

    all_articles = []

    # 1. Load articles from news_raw.json (already fetched by aggregate_news.js)
    news_raw_path = DATA_DIR / "news_raw.json"
    if news_raw_path.exists():
        with open(news_raw_path) as f:
            news_articles = json.load(f)
        funding_articles = [a for a in news_articles if a.get("type") == "funding"]
        all_articles.extend(funding_articles)
        print(f"Found {len(funding_articles)} funding articles from news_raw.json")
    else:
        print("news_raw.json not found — skipping")

    # 2. Fetch funding-specific RSS feeds
    for feed_name, feed_url in FUNDING_FEEDS:
        print(f"Fetching: {feed_name}...")
        articles = fetch_rss(feed_url, feed_name)
        funding = [a for a in articles if is_funding_article(a.get("title", ""), a.get("description", ""))]
        all_articles.extend(funding)
        print(f"  Found {len(funding)} funding articles out of {len(articles)} total")

    # Deduplicate articles by URL (same article appears in multiple feeds)
    seen_urls = set()
    deduplicated = []
    for article in all_articles:
        url = article.get("link", "") or article.get("url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        deduplicated.append(article)
    print(f"\nTotal funding articles to process: {len(deduplicated)} ({len(all_articles) - len(deduplicated)} duplicates removed)")
    all_articles = deduplicated

    # 3. Extract deals from articles
    new_deals = []
    for article in all_articles:
        deal = extract_deal_from_article(article)
        if deal:
            new_deals.append(deal)

    print(f"Extracted {len(new_deals)} deals from articles")
    if SKIPPED:
        seen_skips = {(s["company"], s["headline"]): s for s in SKIPPED}
        print(f"Dropped {len(seen_skips)} deals at the attribution guards:")
        for s in list(seen_skips.values())[:40]:
            print(f"  SKIP {s['company']}: {s['reason']} — \"{s['headline']}\"")

    # 4. Discovery pipeline — log unknown companies for manual review
    print("\nRunning discovery pipeline...")
    save_discovered_companies(all_articles)

    # 5. Load existing deals and merge
    existing = load_existing_deals()
    print(f"\nExisting deals in DEAL_TRACKER: {len(existing)}")

    merged, added = deduplicate_deals(existing, new_deals)
    print(f"New deals added: {added}")
    print(f"Total deals after merge: {len(merged)}")

    # 6. Sort by date (most recent first)
    merged.sort(key=lambda d: d.get("date", ""), reverse=True)

    # 7. Save
    save_deals_json(merged)

    # Summary
    if new_deals:
        print("\nNew Deals Found:")
        for d in new_deals[:10]:
            investors_str = ", ".join(d["investors"]) if d["investors"] else "Undisclosed"
            print(f"  {d['company']}: {d['amount']} {d['round']} ({d['date']}) — {investors_str}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
