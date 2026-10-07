#!/usr/bin/env python3
"""
VC Portfolio Watcher
─────────────────────────────────────────────────────────────────────────
Reads the portfolio pages of the funds whose taste matches this database and
reports two things every week:

  1. New holdings — a company a fund lists now that it did not list last run
     (plus the fund's own first-investment date, where it publishes one).
  2. Candidates  — holdings we do not track, ranked by how much of that fund's
     portfolio we already hold. A fund we already agree with (Cantos: 11 of
     13) is worth reading; a generalist's fintech book is not.

Why this replaces scripts/fetch_vc_portfolios.py (retired 25 Sept 2026)
──────────────────────────────────────────────────────────────────────────
That script ran green every morning for six months and never surfaced a real
new holding. Its company loader read only the first 500KB of data.js, so it
matched fund pages against 17 names (Slack channels and event titles); eight
of its 48 URLs had 404'd; the JS-rendered pages gave it navigation headings;
and its discovery output was never carried out of the CI job. The 247
companies added in the 60 days to September all came from a human scan.

What the funds actually publish
───────────────────────────────
Most of them hand the data over if you ask the right way, so each fund has an
adapter and a plain fetch beats a headless browser:

  getro       Cantos, Lux, 8VC and Khosla run Getro job boards whose company
              search API lists the whole portfolio with domains and locations
              (Oct 2026: 50, 189, 375 and 401 companies, against 13, 28, 174
              and 114 from their own pages).
  a16z_board  jobs.a16z.com server-renders 678 companies with domain and HQ;
              merged with the portfolio page's JSON (below), which alone
              carries the focus areas the American Dynamism filter needs.
  consider    Sequoia's Consider job board: ~255 companies with domains and
              offices. Fallback: its sitemap's /companies/<slug> pages, each
              read for the company's own link and matched on domain only.
  a16z        the portfolio page embeds the whole book as JSON — 859 companies
              with website, focus area and the date a16z first invested.
  wp_company  Founders Fund and Lowercarbon run WordPress with a public
              `company` post type: name, date added, website, founders.
  sanity      Eclipse's CMS is a public Sanity dataset with websiteURL,
              foundedYear, founder and a created date.
  cards_8vc   8VC's Webflow cards carry the company site in a hidden anchor.
  cards_lux   Lux's cards carry names only (28 featured); no website.
  links       Everyone else: each outbound link on the page is a holding, and
              the company's own domain is a far better key than its name.
  slugs       Harpoon, Shield, Congruent: only /portfolio/<slug> subpages.

A fund with a job-board adapter keeps its older adapter as `fallback`, used
when the board fails or returns nothing; the run records that as `partial`.
A run whose adapter differs from last run's is a baseline for that fund, so a
switch of source is not reported as a wave of new holdings.

Matching order: website domain → exact name → suffix-stripped stem → shared
founder. Names alone produced 3,372 "leads" that were mostly page furniture;
domains produced 177 confirmed holdings and 504 real leads on the same pages.
Pairs that data/name_collisions.json records as different companies never
match by name ("Navier AI" is not Navier).

Guards (same as the curated-list watcher): a fund that parses nothing, or
under half of last run's count, is treated as broken — last good data kept,
error recorded, `::error::` emitted, non-zero exit so the Action goes red.

Outputs
───────
  data/vc_portfolio_snapshots.json         per-fund holdings + site-meta cache (state)
  data/vc_portfolio_watch_auto.json / .js  this run's report per fund
  data/vc_portfolio_review_queue.json      candidates awaiting review (append-only)
  data/vc_portfolio_changes.json           confirmed holdings, for merge_data's VC_FIRMS update
  data/vc_portfolio_investor_backfill.json companies whose investors field lacks a fund
                                           that lists them (apply with apply_investor_backfill.py)

Never writes to data.js. A human promotes candidates.

Usage
─────
  python3 scripts/fetch_vc_portfolio_watcher.py
  python3 scripts/fetch_vc_portfolio_watcher.py --fund a16z
  python3 scripts/fetch_vc_portfolio_watcher.py --max-resolve 0   # no homepage fetches
  python3 scripts/fetch_vc_portfolio_watcher.py --fund Lux --dry --max-resolve 0
                                         # read and match, print counts, write nothing
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import quote, urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
SNAP_OUT = DATA_DIR / "vc_portfolio_snapshots.json"
JSON_OUT = DATA_DIR / "vc_portfolio_watch_auto.json"
JS_OUT = DATA_DIR / "vc_portfolio_watch_auto.js"
QUEUE_OUT = DATA_DIR / "vc_portfolio_review_queue.json"
CHANGES_OUT = DATA_DIR / "vc_portfolio_changes.json"
BACKFILL_OUT = DATA_DIR / "vc_portfolio_investor_backfill.json"

sys.path.insert(0, str(ROOT / "scripts"))
from fetch_curated_lists import (EXCLUDE, SOFT, different_company, load_collisions,  # noqa: E402
                                 norm, person_set, stem)

# Fund sites serve bot user-agents a challenge page or nothing at all.
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
TIMEOUT = 25
MIN_KEEP = 0.5          # under half of last run's count = the page broke, not the fund
MIN_PREV_FOR_GUARD = 12  # tiny lists swing naturally; only guard real lists
BOARD_MAX_PAGES = 120    # Getro answers 12 a page: 120 pages = 1,440 companies
SITEMAP_SECONDS = 360    # time budget for reading Sequoia's company pages in the fallback

# ── the funds ────────────────────────────────────────────────────────────
#
# `short` is the VC_FIRMS.shortName merge_data.py uses to update
# portfolioCompanies; None when the fund has no VC_FIRMS record.
# `investor` is the canonical spelling in COMPANIES.investors, `alias` how it
# appears in practice. `discover` says whether the fund's unknowns go to the
# review queue at all: generalists are read for holdings and investor
# back-fill only, because their unknowns are DoorDash and Instacart.
#
# `kind` is the primary adapter. A job-board fund keeps its older adapter as
# `fallback`; `merge` names a second source unioned in by domain. Board
# adapters read their settings from `getro` / `consider` / `board`; `urls`
# stays the fallback's page.
FUNDS = {
    # American Dynamism only: "Infra" is cloud software at a16z and "Bio + Health"
    # is mostly healthtech apps; the first run queued 161 of them. The job board
    # tags only 24 companies American Dynamism, so the portfolio JSON's focus
    # areas are merged in; a board-only holding has no AD tag and is never queued.
    "a16z": dict(name="Andreessen Horowitz", short="a16z", investor="Andreessen Horowitz",
                 alias=r"a16z|andreessen", kind="a16z_board", board="https://jobs.a16z.com/companies",
                 fallback="a16z", merge="a16z", urls=["https://a16z.com/portfolio/"],
                 discover=True, focus_allow={"American Dynamism"},
                 note="jobs.a16z.com (678 with domain and HQ) + portfolio JSON (focus areas, first-investment dates)"),
    "Founders Fund": dict(name="Founders Fund", short="Founders Fund", investor="Founders Fund",
                          alias=r"founders fund", kind="wp_company",
                          urls=["https://foundersfund.com/wp-json/wp/v2/company"], discover=True,
                          industry_block={"Consumer Internet & Media", "Analytics & Software"},
                          note="WordPress company feed with dates and founders"),
    "Lowercarbon": dict(name="Lowercarbon Capital", short="Lowercarbon", investor="Lowercarbon Capital",
                        alias=r"lowercarbon", kind="wp_company",
                        urls=["https://lowercarbon.com/wp-json/wp/v2/company"], discover=True,
                        note="WordPress company feed; HQ and founding year in the body"),
    "Eclipse": dict(name="Eclipse Ventures", short="Eclipse", investor="Eclipse Ventures",
                    alias=r"eclipse", kind="sanity",
                    urls=["https://5uq66tk5.api.sanity.io/v2023-01-01/data/query/production"],
                    discover=True, note="Public Sanity dataset: websiteURL, foundedYear, founder"),
    "8VC": dict(name="8VC", short="8VC", investor="8VC", alias=r"\b8vc\b", kind="getro",
                getro=dict(collection=1005, origin="https://jobs.8vc.com"), fallback="cards_8vc",
                urls=["https://8vc.com/companies"], discover=True,
                note="Getro job board (~375); fallback: Webflow cards with the site in a hidden anchor"),
    "Lux": dict(name="Lux Capital", short="Lux", investor="Lux Capital", alias=r"\blux\b",
                kind="getro", getro=dict(collection=103, origin="https://jobs.luxcapital.com"),
                fallback="cards_lux", urls=["https://www.luxcapital.com/companies"], discover=True,
                note="Getro job board (~189); fallback: 28 featured cards, names only"),
    "Cantos": dict(name="Cantos Ventures", short="Cantos", investor="Cantos Ventures",
                   alias=r"cantos", kind="getro", getro=dict(collection=220, origin="https://jobs.cantos.vc"),
                   fallback="links", urls=["https://cantos.vc/"], discover=True,
                   note="Getro job board (~50); fallback: homepage grid (13)"),
    "Riot": dict(name="Riot Ventures", short="Riot", investor="Riot Ventures", alias=r"riot",
                 kind="links", urls=["https://riot.vc/"], discover=True),
    "Silent": dict(name="Silent Ventures", short="Silent", investor="Silent Ventures",
                   alias=r"silent ventures", kind="links", urls=["https://silentvc.com/"],
                   discover=True, note="Squarespace; 77% overlap in the Sept 2026 hand scan"),
    "Pax Ventures": dict(name="Pax Ventures", short=None, investor="Pax Ventures", alias=r"\bpax\b",
                         kind="links", urls=["https://www.pax.vc/"], discover=True),
    "Prime Movers Lab": dict(name="Prime Movers Lab", short="Prime Movers Lab",
                             investor="Prime Movers Lab", alias=r"prime movers", kind="links",
                             urls=["https://www.primemoverslab.com/portfolio"], discover=True),
    "Playground": dict(name="Playground Global", short="Playground", investor="Playground Global",
                       alias=r"playground", kind="links",
                       urls=["https://playground.global/portfolio/"], discover=True),
    "Seraphim Space": dict(name="Seraphim Space", short=None, investor="Seraphim Space",
                           alias=r"seraphim", kind="links", urls=["https://seraphim.vc/portfolio"],
                           discover=True, note="Space-only fund; ~100 companies"),
    "Decisive Point": dict(name="Decisive Point", short=None, investor="Decisive Point",
                           alias=r"decisive point", kind="links",
                           urls=["https://decisivepoint.com/portfolio"], discover=True),
    "Gigascale": dict(name="Gigascale Capital", short=None, investor="Gigascale Capital",
                      alias=r"gigascale", kind="links", urls=["https://gigascale.com/portfolio/"],
                      discover=True),
    "IQT": dict(name="In-Q-Tel", short="IQT", investor="In-Q-Tel", alias=r"in-q-tel|\biqt\b",
                kind="links", urls=["https://www.iqt.org/portfolio/"], discover=True,
                note="Page shows the first 15 only; the rest load on click"),
    "Caffeinated": dict(name="Caffeinated Capital", short=None, investor="Caffeinated Capital",
                        alias=r"caffeinated", kind="links",
                        urls=["https://caffeinatedcapital.com/"], discover=True),
    "8090 Industries": dict(name="8090 Industries", short=None, investor="8090 Industries",
                            alias=r"8090", kind="links", urls=["https://8090industries.com/"],
                            discover=True),
    "Harpoon": dict(name="Harpoon Ventures", short="Harpoon", investor="Harpoon Ventures",
                    alias=r"harpoon", kind="slugs", urls=["https://harpoon.vc/portfolio/"],
                    discover=True, note="Subpage slugs only"),
    "Shield": dict(name="Shield Capital", short="Shield", investor="Shield Capital",
                   alias=r"shield capital", kind="slugs", urls=["https://shieldcap.com/portfolio/"],
                   discover=True, note="Subpage slugs only"),
    "Congruent": dict(name="Congruent Ventures", short=None, investor="Congruent Ventures",
                      alias=r"congruent", kind="slugs",
                      urls=["https://www.congruentvc.com/portfolio"], discover=True),
    # Generalists: read for holdings and investor back-fill, never for discovery.
    "KV": dict(name="Khosla Ventures", short="KV", investor="Khosla Ventures", alias=r"khosla",
               kind="getro", getro=dict(collection=257, origin="https://jobs.khoslaventures.com"),
               fallback="links", urls=["https://khoslaventures.com/portfolio/"], discover=False,
               note="Getro job board (~400); fallback: portfolio page links"),
    "Sequoia": dict(name="Sequoia Capital", short="Sequoia", investor="Sequoia Capital",
                    alias=r"sequoia", kind="consider",
                    consider=dict(origin="https://jobs.sequoiacap.com", board="sequoia-capital"),
                    fallback="sequoia_sitemap", urls=["https://sequoiacap.com/sitemap.xml"],
                    discover=False,
                    note="Consider job board (~255 with domains); fallback: sitemap company pages, domain-only"),
    "Valor": dict(name="Valor Equity Partners", short="Valor", investor="Valor Equity Partners",
                  alias=r"valor", kind="links", urls=["https://valorep.com/portfolio/"],
                  discover=False),
    "Spark": dict(name="Spark Capital", short=None, investor="Spark Capital", alias=r"spark capital",
                  kind="links", urls=["https://www.sparkcapital.com/companies"], discover=False),
    "Draper": dict(name="Draper Associates", short=None, investor="Draper Associates",
                   alias=r"draper", kind="links", urls=["https://draper.vc/companies"],
                   discover=False),
    "AlleyCorp": dict(name="AlleyCorp", short="AlleyCorp", investor="AlleyCorp",
                      alias=r"alley ?corp", kind="links", urls=["https://alleycorp.com/companies/"],
                      discover=False,
                      note="Kevin Ryan's NYC studio; ~140 cards (aria-label names), mostly software and healthcare"),
    # Not readable without a browser (JS-only pages), kept here so the gap is
    # on record: General Catalyst, DCVC, Breakthrough Energy, Initialized,
    # Interlagos, Point72 Ventures (TLS 1.0 only).
}

# Domains that appear on every fund page and are never a portfolio company.
SKIP_DOMAINS = (
    "twitter.com", "x.com", "linkedin.com", "facebook.com", "instagram.com", "youtube.com",
    "medium.com", "substack.com", "apple.com", "google.com", "crunchbase.com", "github.com",
    "tiktok.com", "spotify.com", "vimeo.com", "wikipedia.org", "bloomberg.com", "forbes.com",
    "techcrunch.com", "wsj.com", "nytimes.com", "ft.com", "reuters.com", "axios.com",
    "yahoo.com", "cnbc.com", "theinformation.com", "businesswire.com", "prnewswire.com",
    "globenewswire.com", "googleapis.com", "gstatic.com", "website-files.com",
    "squarespace-cdn.com", "squarespace.com", "sqspcdn.com", "googletagmanager.com",
    "typekit.net", "cloudfront.net", "hubspotusercontent-na1.net", "amazonaws.com",
    "docsend.com", "angel.co", "workable.com", "intralinks.com", "gmpg.org", "framer.com",
    "framerusercontent.com", "sanity.io", "intellimize.co", "intellimizeio.com", "plyr.io",
    "bsky.app", "threads.net", "mybrightsites.com", "av-funds.com", "a16zcrypto.com",
    "altareturn.com", "vercel.app", "dealroom.co", "pitchbook.com", "wellfound.com",
    "datacenterdynamics.com", "lever.co", "greenhouse.io", "ashbyhq.com", "mailchimp.com",
    "list-manage.com", "eepurl.com", "hsforms.com", "calendly.com", "typeform.com",
    "notion.site", "notion.so", "luma.com", "lu.ma", "eventbrite.com", "w3.org", "schema.org",
    "jquery.com", "cloudflare.com", "jsdelivr.net", "unpkg.com", "wp.com", "gravatar.com",
    "vimeocdn.com", "ytimg.com", "fbcdn.net", "licdn.com", "twimg.com", "hubspot.com",
    "hs-scripts.com", "segment.com", "mixpanel.com", "hotjar.com", "cloudinary.com",
    "carta.com", "goo.gl", "energy.gov", "fundpanel.io", "blackflag.vc", "silentcapital.vc",
    "hanoverpark.com", "playground.vc", "studiopaloalto.com", "rippling.com",
    "generation.space", "wixstatic.com", "parastorage.com", "webflow.com", "webflow.io",
)

# A candidate has to look like it makes something. Software holdings of
# hard-tech funds (Eclipse's vet-telehealth, Riot's e-commerce) fail this.
HARD = re.compile(
    r"(defen[cs]e|aerospace|\bspace\b|satellite|orbit|launch|rocket|propulsion|aircraft|"
    r"evtol|drone|\buav|maritime|\bships?\b|vessel|submarine|subsea|robot|humanoid|actuator|"
    r"manufactur|factory|foundry|machin|3d print|additive|hardware|sensor|lidar|radar|"
    r"\bchips?\b|semiconductor|photonic|laser|quantum|nuclear|fusion|fission|reactor|energy|"
    r"batter|\bgrid\b|solar|geothermal|hydrogen|\bfuel|carbon|steel|metal|mineral|mining|"
    r"material|biotech|biolog|therap|\bdrug|genom|protein|\bcells?\b|medical device|"
    r"diagnos|implant|neural|brain|construction|housing|\bhomes?\b|autonom|vehicle|truck|"
    r"electric|motor|engine|turbine|\bpower\b|microgrid|desalin|water|weapon|missile|"
    r"munition|armor|radiopharm|microscop|instrument|spectromet|refrigerat|cryogenic)", re.I)
SOFT2 = re.compile(
    r"(platform (that|for|to|enabl|connect)|\bsaas\b|marketplace|payments?\b|insurance|"
    r"fintech|e-?commerce|post-purchase|retail market|logistics platform|delivery solution|"
    r"control plane|inference cloud|benchmarks|local government|govtech|autonomous finance|"
    r"home care network|veterinari|dementia care|creative and communications studio|"
    r"transit agencies|energy management, helping|quoting|rate-ingestion)", re.I)
# Getro boards tag every company. A holding none of whose tags names a
# physical industry is software or services, whatever words its description
# happens to contain: Nylas ("power"), Vercel ("engine"), Rocketlane, Qualia
# ("home") all passed the description bar on the first Getro dry run.
HARD_TAGS = re.compile(
    r"(manufactur|industrial|aerospace|aviation|\bspace\b|satellite|defen[cs]e|robot|hardware|"
    r"semiconductor|electronic|energy|batter|nuclear|fusion|biotech|biopharma|pharma|therapeut|"
    r"medical device|life science|genetic|genomic|material|3d (?:printing|technology)|automotive|"
    r"autonomous|electric vehicle|construction|agri|mining|mineral|chemic|clean ?tech|climate|"
    r"water|transport|drone|marine|maritime|telecom|wireless|sensor|photonic|optic|quantum|laser|"
    r"neuro|diagnos|oncolog|biolog|protein|food tech|nanotech|appliances|machinery|"
    r"lab automation|instrument)", re.I)
ERROR_TITLE = re.compile(r"^(4\d\d|5\d\d)\b|forbidden|access denied|just a moment|attention required|"
                         r"not found|error", re.I)

# Anchor text that is a button, not a company.
JUNK_NAMES = {
    "learn more", "learn more ↗", "visit", "visit website", "visit the website", "website",
    "read more", "view", "overview", "open", "→", "↗", "link", "site", "more", "portfolio",
    "companies", "investors", "syndicate", "limited partners", "lp login", "login", "usa",
    "studio", "careers", "jobs", "team", "news", "contact", "about",
}


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def dom(url: str) -> str:
    """Bare registrable-ish domain: strips scheme, www and paths."""
    if not url:
        return ""
    u = url.strip()
    if "://" not in u:
        u = "https://" + u
    d = urlparse(u).netloc.lower().split(":")[0]
    return d[4:] if d.startswith("www.") else d


def skip_domain(d: str) -> bool:
    return not d or any(d == s or d.endswith("." + s) for s in SKIP_DOMAINS)


def clean_text(html: str) -> str:
    t = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", unescape(t)).strip()


def first_segment(inner_html: str) -> str:
    """The first text run inside an anchor: the name, not the tagline after it."""
    t = re.sub(r"</(?:div|p|h[1-6]|span|li|td|figcaption)>|<br\s*/?>|\n|\s{2,}", " | ",
               inner_html or "", flags=re.I)
    t = clean_text(t)
    for seg in t.split(" | "):
        seg = seg.strip(" -–—·|→↗")
        if seg:
            return seg
    return ""


def tidy_name(name: str) -> str:
    n = unescape(name or "").strip()
    n = re.sub(r"(?i)[-_ ]?(logo|cover[- ]image|image|icon)$", "", n).strip()
    n = re.sub(r"(?i)\s*(learn more|visit the website|visit website|visit|read more|overview).*$", "", n).strip()
    n = n.strip(" -–—·|→↗")
    return n


def name_from_domain(d: str) -> str:
    base = d.split(".")[0] if d else ""
    base = re.sub(r"^(get|try|use|join|hello|the)(?=[a-z])", "", base)
    return base.replace("-", " ").title() if base else ""


def looks_like_fund(name: str, blurb: str = "") -> bool:
    """A co-investor or a partner's personal site, not a portfolio company."""
    n = (name or "").lower().strip()
    if re.search(r"\b(ventures?|capital|partners|fund|funds|vc|equity|holdings|"
                 r"investments?|accelerator|angels?|syndicate)\b$", n):
        return True
    return bool(re.search(r"(?i)\b(investing in|we invest|venture (firm|capital|fund)|"
                          r"managing partner|general partner|our portfolio|we back|"
                          r"early[- ]stage (fund|investor)|family office)\b", blurb or ""))


def get(url: str, session: requests.Session | None = None, **kw) -> requests.Response:
    """GET with a polite retry: a 429 or 5xx is a busy server, not a broken fund.
    Lowercarbon's WordPress feed answered 429 on page 2 from a GitHub runner
    on the first CI run and the guard marked the fund broken."""
    for attempt, pause in enumerate((0, 4, 10, 20)):
        if pause:
            time.sleep(pause)
        r = (session or requests).get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True, **kw)
        if r.status_code in (429, 502, 503, 504) and attempt < 3:
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()                                   # pragma: no cover
    return r


def post(url: str, session: requests.Session | None = None, **kw) -> requests.Response:
    """POST with the same polite retry as get(); the job-board search APIs."""
    for attempt, pause in enumerate((0, 4, 10, 20)):
        if pause:
            time.sleep(pause)
        r = (session or requests).post(url, timeout=TIMEOUT, **kw)
        if r.status_code in (429, 502, 503, 504) and attempt < 3:
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()                                   # pragma: no cover
    return r


# ── the database ─────────────────────────────────────────────────────────

def load_db() -> dict:
    """Indexes over COMPANIES: by domain, by normalised name, by stem, by founder."""
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
          '+";globalThis.__n=COMPANIES.map(c=>({n:c.name,f:c.formerNames||[],p:c.founder||\'\','
          'w:c.website||\'\',i:c.investors||[]}));",s);'
          "console.log(JSON.stringify(s.__n));")
    rows = json.loads(subprocess.run(["node", "-e", js, str(DATA_JS)],
                                     capture_output=True, text=True, check=True).stdout)
    by_domain, by_norm, by_stem, domain_of, investors, by_label = {}, {}, {}, {}, {}, {}
    for r in rows:
        if r["w"]:
            by_domain.setdefault(dom(r["w"]), r["n"])
            domain_of[r["n"]] = dom(r["w"])
            lab = re.sub(r"[^a-z0-9]", "", dom(r["w"]).split(".")[0])
            if len(lab) >= 7:                       # aureliussystems.us == aureliussystems.com
                by_label.setdefault(lab, r["n"])
        for label in [r["n"]] + r["f"]:
            by_norm.setdefault(norm(label), r["n"])
            s = stem(label)
            if len(s) >= 6:                         # "edge", "fleet" are not identities
                by_stem.setdefault(s, r["n"])
        investors[r["n"]] = r["i"]
    return {"by_domain": by_domain, "by_norm": by_norm, "by_stem": by_stem, "by_label": by_label,
            "domain_of": domain_of, "investors": investors, "count": len(rows),
            "collisions": load_collisions()}


def same_site(a: str, b: str) -> bool:
    """Same host, a subdomain of it, or the same label under another TLD
    (aureliussystems.us and aureliussystems.com are one company)."""
    if a == b or a.endswith("." + b) or b.endswith("." + a):
        return True
    la, lb = a.split(".")[0], b.split(".")[0]
    return len(la) >= 6 and la == lb


def resolve_known(h: dict, db: dict) -> tuple[str | None, str]:
    """(database company this holding is, how) — or (None, "").

    Domain first, because it is exact. A name match is then allowed only if
    the two sides' domains do not disagree: a16z's "Phantom" (a crypto
    wallet) is not Phantom Space, and its "Pave" is not PAVE Space, however
    the suffix-stripper feels about it. Stems are used only when the fund
    gave us no domain to check against (Lux names, Harpoon slugs).

    No founder matching. The first run tagged Affirm as Palantir because
    they share a co-founder; serial founders make that rule wrong for a
    fund's whole book.
    """
    d = h.get("domain") or ""
    if d and d in db["by_domain"]:
        return db["by_domain"][d], "domain"
    lab = re.sub(r"[^a-z0-9]", "", d.split(".")[0]) if d else ""
    if len(lab) >= 7 and lab in db["by_label"]:
        return db["by_label"][lab], "domain"
    if h.get("_domain_only"):
        return None, ""                              # a slug or title proves nothing (Sequoia's /apex)
    n = h.get("name") or ""
    cand, how = db["by_norm"].get(norm(n)) if n else None, "exact-name"
    if not cand and n and not d:
        s = stem(n)
        if len(s) >= 6:
            cand, how = db["by_stem"].get(s), "stem"
    if not cand:
        return None, ""
    if different_company(n, cand, db.get("collisions") or {}):
        return None, ""                              # data/name_collisions.json: "Navier AI" is not Navier
    cd = db["domain_of"].get(cand, "")
    if d and cd and not same_site(d, cd):
        return None, ""                              # same name, different company
    if d and not cd and len(norm(n)) < 8:
        return None, ""                              # "Vinci", "Glimpse": a name that short proves nothing
    return cand, how


def possible_matches(h: dict, db: dict) -> list[str]:
    """Records this holding might be under another name or an older website:
    "Dominion" against "Dominion Dynamics", firehawkaerospace.com against a
    record at firehawkdefense.com. Shown to the reviewer, never auto-merged."""
    out = []
    n = norm(h.get("name") or "")
    label = (h.get("domain") or "").split(".")[0]
    for key, name in db["by_norm"].items():
        if len(key) >= 7 and len(n) >= 7 and (key.startswith(n) or n.startswith(key)) and key != n:
            out.append(name)
        elif len(label) >= 7 and (key == label or key.startswith(label) and len(key) - len(label) <= 12):
            out.append(name)
    if n and n in db["by_norm"]:                     # exact name, vetoed by domain
        out.append(db["by_norm"][n])
    out = [x for x in out if not different_company(h.get("name") or "", x, db.get("collisions") or {})]
    return sorted(set(out))[:3]


# ── adapters: each returns a list of holdings ────────────────────────────
# holding = {name, domain, website, first_funded, focus, blurb, founders,
#            founded, hq, source_url}

def holding(name="", website="", first_funded="", focus="", blurb="", founders="",
            founded="", hq="", source_url="") -> dict:
    return {"name": tidy_name(name), "domain": dom(website), "website": (website or "").strip(),
            "first_funded": (first_funded or "")[:10], "focus": focus or "", "blurb": (blurb or "")[:300],
            "founders": founders or "", "founded": str(founded or ""), "hq": hq or "",
            "source_url": source_url or ""}


def extract_a16z(fund: dict) -> list[dict]:
    """a16z server-renders its whole portfolio as HTML-escaped JSON inside the page."""
    txt = unescape(get(fund["urls"][0]).text)
    out, seen = [], set()
    for m in re.finditer(r'\{"id":"\d+","name":"(?:[^"\\]|\\.)*".*?"_sort_order":\d+\}', txt, re.S):
        try:
            c = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        if c.get("id") in seen:
            continue
        seen.add(c.get("id"))
        focus = c.get("focus_areas") or []
        out.append(holding(
            name=c.get("name") or c.get("post_title") or "",
            website=c.get("external_url") or c.get("url") or "",
            first_funded=c.get("initial_a16z_date_funded") or "",
            focus=", ".join(focus) if isinstance(focus, list) else str(focus),
            blurb=c.get("website_description") or c.get("overview") or "",
            founders=c.get("founders_list") or "", founded=c.get("year_founded") or "",
            source_url=c.get("permalink") or fund["urls"][0]))
        out[-1]["status"] = c.get("status") or ""
        out[-1]["_focus_set"] = set(focus) if isinstance(focus, list) else set()
    return out


NEWS_HOSTS = ("axios.com", "nytimes.com", "techcrunch.com", "bloomberg.com", "wsj.com",
              "forbes.com", "reuters.com", "ft.com", "cnbc.com", "theinformation.com",
              "businesswire.com", "prnewswire.com", "energy.gov", "innovationfrontier.org")


def extract_wp_company(fund: dict) -> list[dict]:
    """WordPress `company` post type, paginated 100 at a time."""
    base = fund["urls"][0]
    site = dom(base)
    out, page = [], 1
    while True:
        if page > 1:
            time.sleep(2)                    # WordPress rate-limits fast page turns
        try:
            r = get(f"{base}?per_page=100&page={page}&orderby=date&order=desc")
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else 0
            if code == 400:
                break                        # past the last page
            if page > 1 and out:
                # Lowercarbon's WAF blocks GitHub runners from page 2 onward even
                # after 20 s back-offs. Page 1 is the 100 newest holdings, which is
                # what the diff needs; keep it and say so rather than fail the fund.
                fund["_note"] = f"pages after {page - 1} blocked ({code}); newest {len(out)} kept"
                print(f"   partial: {fund['_note']}")
                break
            raise
        rows = r.json()
        if not rows:
            break
        for x in rows:
            title = clean_text(x.get("title", {}).get("rendered", ""))
            body_html = x.get("content", {}).get("rendered", "") or ""
            body = clean_text(body_html)
            profiles = x.get("profiles") or ""
            website = ""
            m = re.search(r'href="(https?://[^"]+)"', profiles)
            if m:
                website = m.group(1)
            if not website:
                # Lowercarbon writes "Founded: 2023 HQ: Austin, TX basepowercompany.com"
                m = re.search(r"HQ:\s*[^.]*?\b([a-z0-9-]+(?:\.[a-z0-9-]+)+)\b", body, re.I)
                if m and not skip_domain(m.group(1).lower()):
                    website = "https://" + m.group(1).lower()
            if not website:
                for u in re.findall(r'href="(https?://[^"]+)"', body_html):
                    d = dom(u)
                    if d and d != site and not skip_domain(d) and not any(d.endswith(h) for h in NEWS_HOSTS) \
                            and not u.lower().endswith(".pdf"):
                        website = u
                        break
            founders = ""
            if isinstance(x.get("founders"), list):
                founders = ", ".join(f.get("founder_name", "") for f in x["founders"] if isinstance(f, dict))
            founded = (re.search(r"Founded:\s*(\d{4})", body) or [None, ""])[1]
            hq = (re.search(r"HQ:\s*([A-Z][^.]*?,\s*[A-Z]{2})\b", body) or [None, ""])[1]
            blurb = re.sub(r"^.*?HQ:\s*[^.]*?\b[a-z0-9-]+(?:\.[a-z0-9-]+)+\s*", "", body) if "HQ:" in body else body
            out.append(holding(name=title, website=website, first_funded=x.get("date", ""),
                               focus=unescape(x.get("industry") or ""), blurb=blurb,
                               founders=founders, founded=founded, hq=hq,
                               source_url=x.get("link") or base))
        if len(rows) < 100:
            break
        page += 1
    return out


def extract_sanity(fund: dict) -> list[dict]:
    """Eclipse: public Sanity dataset, GROQ over the wire."""
    q = ('*[_type=="company"]{title, websiteURL, foundedYear, members, companyStatus, _createdAt,'
         ' "slug": slug.current, "excerpt": pt::text(excerpt)}')
    data = get(fund["urls"][0] + "?query=" + quote(q, safe="")).json().get("result", [])
    out = []
    for c in data:
        status = c.get("companyStatus") or []
        out.append(holding(name=c.get("title") or "", website=c.get("websiteURL") or "",
                           first_funded=c.get("_createdAt") or "",
                           focus=", ".join(status) if isinstance(status, list) else "",
                           blurb=c.get("excerpt") or "", founders=c.get("members") or "",
                           founded=c.get("foundedYear") or "",
                           source_url=f"https://eclipse.vc/portfolio/{c.get('slug') or ''}"))
    return out


def extract_cards_8vc(fund: dict) -> list[dict]:
    html = get(fund["urls"][0]).text
    out = []
    for card in re.split(r'(?=<div role="listitem" class="companies-collection_item)', html)[1:]:
        name = (re.search(r'<img[^>]+alt="([^"]+)"', card) or [None, ""])[1]
        if not name:
            name = (re.search(r'id="tag-([a-z0-9-]+)"', card) or [None, ""])[1].replace("-", " ").title()
        web = ""
        for u in re.findall(r'href="(https?://[^"#?]+)"', card):
            if not skip_domain(dom(u)) and dom(u) != "8vc.com":
                web = u
                break
        sub = (re.search(r'href="(/companies/[a-z0-9-]+)"', card) or [None, ""])[1]
        blurb = clean_text((re.search(r'class="card-description-text[^"]*">(.*?)</div>', card, re.S) or [None, ""])[1])
        out.append(holding(name=name, website=web, blurb=blurb,
                           source_url=("https://8vc.com" + sub) if sub else fund["urls"][0]))
    return out


def extract_cards_lux(fund: dict) -> list[dict]:
    html = get(fund["urls"][0]).text
    out = []
    for card in re.split(r'(?=<div role="listitem" class="companies_item)', html)[1:]:
        name = clean_text((re.search(r'class="company_name">([^<]+)<', card) or [None, ""])[1])
        sub = (re.search(r'href="(/companies/[a-z0-9-]+)"', card) or [None, ""])[1]
        if name:
            out.append(holding(name=name, source_url=("https://www.luxcapital.com" + sub) if sub else fund["urls"][0]))
    return out


def extract_links(fund: dict) -> list[dict]:
    """Every outbound link on the page is a holding; the anchor gives the name."""
    out, seen = [], set()
    for url in fund["urls"]:
        html = get(url).text
        fd = dom(url)
        for m in re.finditer(r'<a\b([^>]*)href="(https?://[^"#?]+)"([^>]*)>(.*?)</a>', html, re.S | re.I):
            href, attrs, inner = m.group(2), m.group(1) + m.group(3), m.group(4)
            d = dom(href)
            if not d or d == fd or d.endswith("." + fd) or skip_domain(d) or d in seen:
                continue
            name = ""
            for pat in (r'aria-label="([^"]+)"', r'\btitle="([^"]+)"'):
                mm = re.search(pat, attrs)
                if mm:
                    name = mm.group(1)
                    break
            if not name:
                alts = [a for a in re.findall(r'alt="([^"]+)"', inner)
                        if a and not re.search(r"(?i)logo|image|icon|arrow", a)]
                name = alts[0] if alts else first_segment(inner)
            name = tidy_name(name)
            if not name or name.lower() in JUNK_NAMES or name.lower().startswith(("http", "www.")) \
                    or len(name) > 60:
                name = ""                               # resolved later from the company's own site
            seen.add(d)
            out.append(holding(name=name, website=href, source_url=url))
    return out


def extract_slugs(fund: dict) -> list[dict]:
    out, seen = [], set()
    for url in fund["urls"]:
        html = get(url).text
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        for slug in re.findall(r'href="/?(?:portfolio|companies|company)/([a-z0-9-]+)/?"', html):
            if slug in seen or slug in {"page", "category", "tag"}:
                continue
            seen.add(slug)
            out.append(holding(name=slug.replace("-", " ").title(),
                               source_url=f"{base}/portfolio/{slug}"))
    return out


# ── job boards: the fund's whole portfolio with each company's own domain ──

def extract_getro(fund: dict) -> list[dict]:
    """Getro job boards (Cantos, Lux, 8VC, Khosla): the board's company search.

    The API returns 12 companies a page whatever hitsPerPage asks for, and
    wants the board's own Origin and Referer. Pages run from 0 until one comes
    back empty or adds nothing new. The fund lists itself; that entry is dropped.
    """
    g = fund["getro"]
    origin = g["origin"].rstrip("/")
    api = f"https://api.getro.com/api/v2/collections/{g['collection']}/search/companies"
    headers = {**HEADERS, "Accept": "application/json", "Content-Type": "application/json",
               "Origin": origin, "Referer": origin + "/companies"}
    own = dom(fund["urls"][0]) if fund.get("urls") else ""
    out, seen, total = [], set(), None
    for page in range(BOARD_MAX_PAGES):
        if page:
            time.sleep(0.4)
        res = post(api, headers=headers, json={"hitsPerPage": 12, "page": page}).json().get("results") or {}
        total = res.get("count", total)
        fresh = 0
        for c in res.get("companies") or []:
            key = c.get("id") or c.get("slug") or c.get("domain") or c.get("name")
            if key in seen:
                continue
            seen.add(key)
            fresh += 1
            d = dom(c.get("domain") or "")
            if d and (skip_domain(d) or (own and same_site(d, own))):
                continue
            locs = c.get("locations") or []
            tags = c.get("visible_industry_tags") or c.get("industry_tags") or []
            out.append(holding(name=c.get("name") or "", website=f"https://{d}" if d else "",
                               focus=", ".join(tags[:6]), blurb=c.get("description") or "",
                               hq=locs[0] if locs else "",
                               source_url=f"{origin}/companies/{c['slug']}" if c.get("slug") else origin))
            out[-1]["_tags"] = list(c.get("industry_tags") or tags)
        if not fresh or (total is not None and len(seen) >= total):
            break
    return out


def extract_a16z_board(fund: dict) -> list[dict]:
    """jobs.a16z.com server-renders every company on the board (678 in Oct
    2026) into its Next.js flight payload: name, domain, location, markets.
    It no longer runs on Consider; that API path now 404s."""
    url = fund["board"]
    html = get(url).text
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html)
    flight = "".join(json.loads(f'"{c}"') for c in chunks)
    i = flight.find('"companies":[')
    if i < 0:
        raise ValueError("no companies array in the board's page payload")
    arr, _ = json.JSONDecoder().raw_decode(flight, i + len('"companies":'))
    out = []
    for c in arr:
        if not isinstance(c, dict):
            continue
        markets = [m for m in (c.get("markets") or []) if isinstance(m, str)]
        h = holding(name=c.get("name") or "", website=f"https://{c['domain']}" if c.get("domain") else "",
                    focus=", ".join(markets), blurb=c.get("description") or "",
                    hq=c.get("location") or "", source_url=url)
        h["_focus_set"] = set(markets)
        out.append(h)
    return out


def extract_consider(fund: dict) -> list[dict]:
    """Consider job boards (Sequoia): a session cookie and the csrfToken from
    the board page's serverInitialData, then the board's company search, 100
    a page, paged by meta.sequence. The search fails without a `query` key."""
    c = fund["consider"]
    origin = c["origin"].rstrip("/")
    s = requests.Session()
    page = get(origin + "/companies", session=s)
    m = re.search(r'"csrfToken"\s*:\s*"([^"]+)"', page.text)
    if not m:
        raise ValueError("no csrfToken in the board's serverInitialData")
    headers = {**HEADERS, "Accept": "application/json", "Content-Type": "application/json",
               "Origin": origin, "Referer": origin + "/companies", "x-csrf-token": m.group(1)}
    out, seen, seq = [], set(), None
    for n in range(BOARD_MAX_PAGES):
        if n:
            time.sleep(0.4)
        meta = {"size": 100, **({"sequence": seq} if seq else {})}
        j = post(origin + "/api-boards/search-companies", session=s, headers=headers,
                 json={"meta": meta, "board": {"id": c["board"], "isParent": True}, "query": {}}).json()
        if j.get("errors"):
            raise ValueError(f"board search: {str(j['errors'][0].get('message', ''))[:80]}")
        comps = j.get("companies") or []
        fresh = 0
        for x in comps:
            key = x.get("id") or x.get("slug") or x.get("domain") or x.get("name")
            if key in seen:
                continue
            seen.add(key)
            fresh += 1
            slugs = (x.get("investorSlugs") or []) + (x.get("parentSlugs") or [])
            if slugs and c["board"] not in slugs:
                continue                             # on the board through another investor
            web = (x.get("website") or {}).get("url") or (f"https://{x['domain']}" if x.get("domain") else "")
            locs = x.get("officeLocations") or []
            out.append(holding(name=x.get("name") or "", website=web,
                               focus=", ".join(x.get("markets") or []), blurb=x.get("description") or "",
                               hq=locs[0] if locs else "",
                               source_url=f"{origin}/companies/{x['slug']}" if x.get("slug") else origin))
        seq = (j.get("meta") or {}).get("sequence")
        total = j.get("total")
        if not comps or not fresh or not seq or (total and len(seen) >= total):
            break
    return out


def _company_link(html: str) -> str:
    """The company's own site on a Sequoia company page: the outbound anchor
    whose text is its domain ("apexhq.ai"), else the first outbound link that
    is not social, press or Sequoia's own."""
    fallback = ""
    for m in re.finditer(r'<a\b[^>]*href="(https?://[^"#?]+)[^"]*"[^>]*>(.*?)</a>', html, re.S | re.I):
        d = dom(m.group(1))
        if not d or skip_domain(d) or d.endswith("sequoiacap.com") or any(d.endswith(x) for x in NEWS_HOSTS):
            continue
        text = clean_text(m.group(2)).lower().rstrip("/")
        text = text[4:] if text.startswith("www.") else text
        if text and (d == text or d.endswith("." + text)):
            return m.group(1)
        fallback = fallback or m.group(1)
    return fallback


def extract_sequoia_sitemap(fund: dict) -> list[dict]:
    """Sequoia fallback: sequoiacap.com/sitemap.xml lists ~430 /companies/<slug>
    pages. A slug is not an identity (/companies/apex is an AI-security firm,
    not Apex Space; observable, parallel, ethos and sunday are other companies
    too), so each page is read for the company's own link and these holdings
    match on that domain only. Reads stop at SITEMAP_SECONDS (or the fund's
    `_page_cap`, used by tests and dry runs)."""
    xml = get(fund["urls"][0]).text
    slugs = list(dict.fromkeys(re.findall(
        r"<loc>https?://(?:www\.)?sequoiacap\.com/companies/([a-z0-9][a-z0-9-]*)/?</loc>", xml)))
    if not slugs:
        raise ValueError("no /companies/ pages in the sitemap")
    cap = fund.get("_page_cap") or len(slugs)
    deadline = time.time() + SITEMAP_SECONDS
    out, read = [], 0
    for slug in slugs[:cap]:
        if time.time() > deadline:
            break
        url = f"https://sequoiacap.com/companies/{slug}"
        try:
            html = get(url).text
        except requests.RequestException:
            continue
        read += 1
        site = _company_link(html)
        if site:
            title = clean_text((re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I) or [None, ""])[1])
            name = re.split(r"\s+[|–—]\s+", title)[0].strip() if title else ""
            h = holding(name=name or slug.replace("-", " ").title(), website=site, source_url=url)
            h["_domain_only"] = True
            out.append(h)
        time.sleep(0.25)
    if read < len(slugs):
        fund["_note"] = f"sitemap fallback read {read} of {len(slugs)} company pages"
    return out


EXTRACTORS = {"a16z": extract_a16z, "wp_company": extract_wp_company, "sanity": extract_sanity,
              "cards_8vc": extract_cards_8vc, "cards_lux": extract_cards_lux,
              "links": extract_links, "slugs": extract_slugs, "getro": extract_getro,
              "a16z_board": extract_a16z_board, "consider": extract_consider,
              "sequoia_sitemap": extract_sequoia_sitemap}


def merge_holdings(primary: list[dict], extra: list[dict]) -> list[dict]:
    """Union by domain (else normalised name). The primary's fields win; empty
    ones, focus areas and exit status fill in from the second source."""
    def key(h: dict) -> str:
        return h["domain"] or ("n:" + norm(h["name"]))
    out, index = [], {}
    for h in primary:
        index.setdefault(key(h), h)
        out.append(h)
    for h in extra:
        p = index.get(key(h))
        if p is None:
            index[key(h)] = h
            out.append(h)
            continue
        for f in ("first_funded", "founders", "founded", "hq", "blurb", "status"):
            if not p.get(f) and h.get(f):
                p[f] = h[f]
        if p.get("_focus_set") is not None or h.get("_focus_set") is not None:
            p["_focus_set"] = (p.get("_focus_set") or set()) | (h.get("_focus_set") or set())
            p["focus"] = ", ".join(sorted(p["_focus_set"]))
    return out


def source_url(fund: dict, used: str) -> str:
    kind = used.split("+")[0]
    if kind == "getro":
        return fund["getro"]["origin"].rstrip("/") + "/companies"
    if kind == "consider":
        return fund["consider"]["origin"].rstrip("/") + "/companies"
    if kind == "a16z_board":
        return fund["board"]
    return fund["urls"][0]


def run_adapters(fund: dict) -> tuple[list[dict], str, str]:
    """(holdings, adapter(s) used, note). The primary adapter first; on an
    exception or an empty result, the fund's older adapter (a fallback with
    far fewer rows still trips the half-of-last-run guard, as it should);
    then any second source merged in."""
    notes, used = [], fund["kind"]
    try:
        rows = [h for h in EXTRACTORS[used](fund) if h["name"] or h["domain"]]
        if not rows:
            raise ValueError("parsed 0 holdings")
    except Exception as e:                                     # noqa: BLE001
        if not fund.get("fallback"):
            raise
        why = f"{type(e).__name__}: {e}"[:120]
        print(f"   {used} failed ({why}); falling back to {fund['fallback']}")
        notes.append(f"{used} failed ({why}); used {fund['fallback']}")
        used = fund["fallback"]
        rows = EXTRACTORS[used](fund)
    merge = fund.get("merge")
    if merge and merge != used:
        try:
            rows = merge_holdings(rows, EXTRACTORS[merge](fund))
            used = f"{used}+{merge}"
        except Exception as e:                                 # noqa: BLE001
            notes.append(f"{merge} merge failed ({type(e).__name__}); focus areas and dates missing")
    if fund.get("_note"):
        notes.append(fund.pop("_note"))
    return rows, used, "; ".join(notes)


# ── site metadata for candidates ─────────────────────────────────────────

def fetch_site_meta(url: str) -> dict:
    """<title> and description from a company's own homepage; the best name source."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        html = r.text[:400_000]
    except requests.RequestException as e:
        return {"error": type(e).__name__, "fetched": today()}
    title = clean_text((re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I) or [None, ""])[1])
    desc = ""
    for pat in (r'<meta[^>]+name="description"[^>]+content="([^"]*)"',
                r'<meta[^>]+content="([^"]*)"[^>]+name="description"',
                r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"',
                r'<meta[^>]+content="([^"]*)"[^>]+property="og:description"'):
        m = re.search(pat, html, re.I)
        if m and m.group(1).strip():
            desc = clean_text(m.group(1))
            break
    return {"title": title[:120], "description": desc[:300], "fetched": today(),
            "final_url": r.url, "status": r.status_code}


def name_from_title(title: str, d: str) -> str:
    if not title or ERROR_TITLE.search(title):
        return name_from_domain(d)
    parts = [p.strip() for p in re.split(r"\s[|–—•·:]\s|\s-\s", title or "") if p.strip()]
    parts = [p for p in parts if p.lower() not in {"home", "homepage", "welcome"} and len(p) <= 40]
    if parts:
        # the segment that shares letters with the domain wins, else the shortest
        key = re.sub(r"[^a-z0-9]", "", d.split(".")[0])
        for p in parts:
            if key and key in re.sub(r"[^a-z0-9]", "", p.lower()):
                return p
        return min(parts, key=len)
    return name_from_domain(d)


# ── main ─────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fund", choices=list(FUNDS), help="run one fund only")
    ap.add_argument("--max-resolve", type=int, default=80,
                    help="homepages to fetch for candidate names/descriptions (0 = none)")
    ap.add_argument("--resolve-seconds", type=int, default=240,
                    help="stop fetching homepages after this many seconds")
    ap.add_argument("--dry", action="store_true",
                    help="read and match as usual, print per-fund counts, write no files")
    args = ap.parse_args()
    resolve_deadline = time.time() + args.resolve_seconds

    generated = datetime.now(timezone.utc)
    db = load_db()
    print(f"database: {db['count']} companies, {len(db['by_domain'])} with a website domain")

    snap = json.loads(SNAP_OUT.read_text()) if SNAP_OUT.exists() else {"funds": {}, "site_meta": {}}
    prev_funds, site_meta = snap.get("funds", {}), snap.get("site_meta", {})
    targets = {args.fund: FUNDS[args.fund]} if args.fund else FUNDS

    report, broken, changes, backfill = {}, [], [], []
    cand_by_id: dict[str, dict] = {}
    raw_cands: list[tuple] = []
    resolve_budget = args.max_resolve

    for key, fund in targets.items():
        print(f"\n→ {key} [{fund['kind']}] {source_url(fund, fund['kind'])}", flush=True)
        prev = prev_funds.get(key) or {}
        try:
            rows, used, partial = run_adapters(fund)
        except Exception as e:                                 # noqa: BLE001
            why = f"{type(e).__name__}: {e}"[:200]
            print(f"   FAILED: {why}")
            report[key] = {**{k: v for k, v in prev.items() if k != "holdings"}, "error": why,
                           "stale_since": prev.get("stale_since", generated.isoformat())}
            broken.append(key)
            continue
        rows = [h for h in rows if h["name"] or h["domain"]]
        before = prev.get("count") or 0
        if not rows or (before >= MIN_PREV_FOR_GUARD and len(rows) < before * MIN_KEEP):
            why = f"parsed {len(rows)} holdings (last run: {before}); the page or feed has probably changed"
            print(f"   FAILED: {why}")
            report[key] = {**{k: v for k, v in prev.items() if k != "holdings"}, "error": why,
                           "stale_since": prev.get("stale_since", generated.isoformat())}
            broken.append(key)
            continue

        # identity = domain, else normalised name; diff against last run. A
        # different source from last run's (Lux's 28 cards -> its 189-company
        # job board, or a fallback week) is a new baseline, not 161 new holdings.
        prev_ids = {h.get("id") for h in prev.get("holdings", [])} if prev.get("kind") == used else set()
        if prev.get("kind") and prev.get("kind") != used:
            print(f"   source changed ({prev.get('kind')} -> {used}): this run is the new baseline")
        tracked, new_ids, unknown = 0, [], []
        for h in rows:
            h["id"] = h["domain"] or ("n:" + norm(h["name"]))
            known, how = resolve_known(h, db)
            h["known_as"] = known
            if known:
                tracked += 1
                if fund["short"]:
                    changes.append({"vc": fund["short"], "company": known, "source": h["source_url"],
                                    "detected_date": today()})
                inv = " | ".join(db["investors"].get(known, [])).lower()
                if not re.search(fund["alias"], inv):
                    backfill.append({"company": known, "add": fund["investor"], "fund": key,
                                     "matched_by": how, "evidence": h["source_url"],
                                     "first_funded": h["first_funded"]})
            else:
                unknown.append(h)
            if prev_ids and h["id"] not in prev_ids:
                new_ids.append(h["id"])
        overlap = tracked / len(rows) if rows else 0.0

        report[key] = {
            "name": fund["name"], "url": source_url(fund, used), "kind": used, "note": fund.get("note", ""),
            "partial": partial,
            "fetched_at": generated.isoformat(), "count": len(rows), "tracked": tracked,
            "overlap": round(overlap, 3), "new_this_run": len(new_ids), "baseline": not prev_ids,
            "new_names": [h["name"] or h["domain"] for h in rows if h["id"] in set(new_ids)][:40],
            "candidates": 0, "rejected_by_bar": {},
            "holdings": [{"id": h["id"], "name": h["name"], "domain": h["domain"],
                          "first_funded": h["first_funded"], "known_as": h["known_as"]} for h in rows],
        }
        for h in unknown:
            raw_cands.append((key, fund, overlap, h, h["id"] in set(new_ids)))
        print(f"   {len(rows)} holdings · {tracked} tracked ({overlap:.0%}) · "
              f"{'baseline' if not prev_ids else f'{len(new_ids)} new since last run'} · "
              f"{len(unknown)} not in database")
        time.sleep(0.3)

    # ── name and description from the company's own site, then the bar ──
    # Metadata comes first so the bar can judge domain-only holdings; the
    # budget goes to the highest-overlap funds, and the cache means a domain
    # is fetched once, ever.
    raw_cands.sort(key=lambda t: -t[2])
    for key, fund, overlap, h, is_new in raw_cands:
        d = h["domain"]
        if not d or not fund["discover"]:
            continue
        meta = site_meta.get(d)
        # A job board already gave name and description; the budget is for
        # link grids that gave neither.
        if meta is None and not (h["name"] and h["blurb"]) and resolve_budget > 0 \
                and time.time() < resolve_deadline:
            meta = fetch_site_meta(h["website"] or f"https://{d}")
            site_meta[d] = meta
            resolve_budget -= 1
            time.sleep(0.2)
        if meta and not meta.get("error"):
            # a 30+ character "name" is an anchor that ran into its tagline
            if not h["name"] or h["name"].lower() in JUNK_NAMES or h["name"].isdigit() or len(h["name"]) > 30:
                h["name"] = name_from_title(meta.get("title", ""), d)
            if not h["blurb"] and meta.get("description"):
                h["blurb"] = meta["description"]
        if not h["name"] or h["name"].isdigit():
            h["name"] = name_from_domain(d)
        if len(h["name"]) > 30 and " " in h["name"]:
            h["name"] = " ".join(h["name"].split()[:3])

    # ── second pass: a name learnt from the company's site may match after all ──
    rematched = 0
    for key, fund, overlap, h, is_new in raw_cands:
        if h.get("known_as"):
            continue
        known, how = (None, "")
        # A fund often links an old domain that now redirects to the one we
        # hold (firehawkaerospace.com -> firehawkdefense.com). The homepage
        # fetch recorded where it landed; match on that first.
        final = dom((site_meta.get(h["domain"]) or {}).get("final_url", "")) if h["domain"] else ""
        if final and final != h["domain"] and final in db["by_domain"]:
            known, how = db["by_domain"][final], "domain"
        elif h["name"]:
            known, how = resolve_known(h, db)
        if not known:
            continue
        h["known_as"] = known
        rematched += 1
        r = report[key]
        r["tracked"] += 1
        for hh in r["holdings"]:
            if hh["id"] == h["id"]:
                hh["known_as"], hh["name"] = known, h["name"]
        if fund["short"]:
            changes.append({"vc": fund["short"], "company": known, "source": h["source_url"],
                            "detected_date": today()})
        inv = " | ".join(db["investors"].get(known, [])).lower()
        if not re.search(fund["alias"], inv):
            backfill.append({"company": known, "add": fund["investor"], "fund": key, "matched_by": how,
                             "evidence": h["source_url"], "first_funded": h["first_funded"]})
    for key, r in report.items():
        if r.get("count"):
            r["overlap"] = round(r["tracked"] / r["count"], 3)
    fund_overlap = {k: r.get("overlap", 0) for k, r in report.items()}
    if rematched:
        print(f"   {rematched} more holdings matched once their sites gave a name")

    for key, fund, overlap, h, is_new in raw_cands:
        if h.get("known_as"):
            continue
        overlap = fund_overlap.get(key, overlap)
        why = ""
        if not fund["discover"]:
            why = "generalist fund: holdings only"
        elif norm(h["name"]) in EXCLUDE or norm(name_from_domain(h["domain"])) in EXCLUDE:
            why = "megacap / mega-private, deliberately untracked"
        elif looks_like_fund(h["name"], h["blurb"]):
            why = "a co-investor, not a company"
        elif fund.get("focus_allow") and h.get("_focus_set") is not None \
                and not (h["_focus_set"] & fund["focus_allow"]):
            why = f"focus outside {'/'.join(sorted(fund['focus_allow']))}"
        elif fund.get("industry_block") and h["focus"] in fund["industry_block"]:
            why = f"industry '{h['focus']}' is software or consumer"
        elif h.get("status", "").startswith("Exits"):
            why = "exited"
        elif SOFT.search(h["blurb"] or "") or SOFT2.search(h["blurb"] or ""):
            why = "software or services wearing a hard-tech label"
        elif h.get("_tags") and not HARD_TAGS.search(" | ".join(h["_tags"])):
            why = "the board's industry tags show no physical product"
        elif h["blurb"] and not HARD.search(h["blurb"]):
            why = "description shows no physical product"
        if why:
            report[key]["rejected_by_bar"][why] = report[key]["rejected_by_bar"].get(why, 0) + 1
            continue
        report[key]["candidates"] += 1
        c = cand_by_id.setdefault(h["id"], {
            "name": h["name"], "domain": h["domain"], "website": h["website"],
            "tagline": h["blurb"], "founders": h["founders"], "founded": h["founded"],
            "city": h["hq"], "funds": [], "fund_overlap": 0.0,
            "needs_check": not bool(h["blurb"]),
            "possible_match": possible_matches(h, db)})
        c["funds"].append({"fund": key, "first_funded": h["first_funded"], "focus": h["focus"],
                           "source_url": h["source_url"], "new_this_run": is_new})
        c["fund_overlap"] = max(c["fund_overlap"], round(overlap, 3))
        for f in ("name", "tagline", "founders", "founded", "city", "website"):
            src = h.get(f if f != "tagline" else "blurb")
            if not c.get(f) and src:
                c[f] = src
    for key in report:
        if "candidates" in report[key]:
            rej = report[key]["rejected_by_bar"]
            print(f"   {key}: {report[key]['candidates']} candidates"
                  + (" · rejected " + ", ".join(f"{n} {w}" for w, n in sorted(rej.items(), key=lambda kv: -kv[1])) if rej else ""))

    if args.dry:
        print("\n--dry: nothing written. Per fund:")
        for key, r in report.items():
            status = (f"FAILED: {r['error'][:70]}" if r.get("error")
                      else f"partial: {r['partial'][:90]}" if r.get("partial") else "ok")
            print(f"  {key:<16} {str(r.get('kind', '')):<22} {r.get('count', 0):>5} holdings · "
                  f"{r.get('tracked', 0):>4} tracked · {r.get('candidates', 0):>4} candidates · {status}")
        print(f"{len(cand_by_id)} candidates this run (not queued) · {len(changes)} holding matches · "
              f"{len(backfill)} investor back-fills (not written)")
        return 1 if broken else 0

    # ── write state and report ───────────────────────────────────────────
    DATA_DIR.mkdir(exist_ok=True)
    funds_state = {**prev_funds, **{k: v for k, v in report.items()}} if args.fund else report
    SNAP_OUT.write_text(json.dumps({"generated_at": generated.isoformat(), "funds": funds_state,
                                    "site_meta": site_meta}, indent=1))

    def slim(v: dict) -> dict:
        return {k: x for k, x in v.items() if k != "holdings"}
    payload = {"generated_at": generated.isoformat(), "funds": {k: slim(v) for k, v in funds_state.items()},
               "total_candidates": len(cand_by_id), "broken": broken}
    JSON_OUT.write_text(json.dumps(payload, indent=2))
    JS_OUT.write_text(f"// Last updated: {generated.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                      f"window.VC_PORTFOLIO_WATCH_AUTO = {json.dumps(payload)};\n")

    # ── the review queue (append-only; re-listing by another fund updates the entry) ──
    queue = json.loads(QUEUE_OUT.read_text()) if QUEUE_OUT.exists() else []
    by_key = {(q.get("domain") or "n:" + norm(q.get("name", ""))): q for q in queue}
    added = updated = 0
    for cid, c in cand_by_id.items():
        c["listed_by"] = len(c["funds"])
        c["since"] = min([f["first_funded"] for f in c["funds"] if f["first_funded"]] or [today()])
        if cid in by_key:
            q = by_key[cid]
            have = {f["fund"] for f in q.get("funds", [])}
            for f in c["funds"]:
                if f["fund"] not in have:
                    q.setdefault("funds", []).append(f)
                    updated += 1
            q["listed_by"] = len(q.get("funds", []))
            q["fund_overlap"] = max(q.get("fund_overlap", 0), c["fund_overlap"])
            for f in ("tagline", "founders", "founded", "city", "website"):
                if not q.get(f) and c.get(f):
                    q[f] = c[f]
            continue
        queue.append({**c, "detected_at": generated.isoformat(), "status": "pending",
                      "source_list": "vc-portfolio-watcher"})
        by_key[cid] = queue[-1]
        added += 1
    queue.sort(key=lambda q: (q.get("status") != "pending", -q.get("fund_overlap", 0),
                              -q.get("listed_by", 0), q.get("name", "").lower()))
    QUEUE_OUT.write_text(json.dumps(queue, indent=2, ensure_ascii=False))

    # ── confirmed holdings for merge_data (fresh each run, no history to pollute) ──
    seen_c, fresh = set(), []
    for ch in changes:
        k = (ch["vc"], ch["company"])
        if k not in seen_c:
            seen_c.add(k)
            fresh.append(ch)
    if not args.fund:
        CHANGES_OUT.write_text(json.dumps(fresh, indent=2))

    seen_b, bf = set(), []
    for b in backfill:
        k = (b["company"], b["add"])
        if k not in seen_b:
            seen_b.add(k)
            bf.append(b)
    BACKFILL_OUT.write_text(json.dumps({"generated_at": generated.isoformat(), "count": len(bf),
                                        "note": "COMPANIES whose investors field lacks a fund that lists "
                                                "them on its portfolio page. Domain matches are exact; "
                                                "name matches deserve a glance.",
                                        "items": bf}, indent=2))

    pending = [q for q in queue if q.get("status") == "pending"]
    print(f"\n{len(cand_by_id)} candidates this run · {added} newly queued · {updated} entries gained a fund"
          f" · {len(pending)} pending in queue · {len(fresh)} confirmed holdings · "
          f"{len(bf)} investor back-fills suggested")
    dupes = [q for q in pending if q.get("possible_match")]
    top = sorted(pending, key=lambda q: (bool(q.get("possible_match")), -q.get("fund_overlap", 0),
                                         -q.get("listed_by", 0)))[:15]
    if top:
        print("\nread these first:")
        for q in top:
            funds = ", ".join(f["fund"] for f in q["funds"])
            print(f"  [{q['fund_overlap']:.0%} {funds[:28]:<28}] {q['name'][:28]:<28} {q.get('tagline','')[:70]}")
    if dupes:
        print(f"\n{len(dupes)} may already be in the database under another name or website:")
        for q in dupes[:20]:
            print(f"  {q['name'][:28]:<28} {q['domain'][:26]:<26} ~ {', '.join(q['possible_match'])}")
    if broken:
        print(f"::error::VC portfolio watcher: source(s) broken: {', '.join(broken)} (kept last good data)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
