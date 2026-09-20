#!/usr/bin/env python3
"""
VC Portfolio Page Scraper for ROS Startup Database
Scrapes portfolio/companies pages from tracked VC firm websites to detect
new portfolio additions. Compares against existing portfolioCompanies in
data.js and outputs newly discovered companies.

Runs weekly via GitHub Actions. Free — no paid APIs needed.
"""

import json
import re
import requests
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"

# Known portfolio page URLs for each VC firm.
# 30+ frontier-tech-focused firms — when one of them adds a company we
# don't have, that's a high-conviction signal for the discovery pipeline.
VC_PORTFOLIO_URLS = {
    # ─── Tier 1: elite frontier-tech generalists ───
    "a16z": ["https://a16z.com/portfolio/"],
    "Founders Fund": ["https://foundersfund.com/portfolio/"],
    "Khosla": ["https://khoslaventures.com/portfolio/"],
    "Sequoia": ["https://sequoiacap.com/companies/"],
    "Lux": ["https://luxcapital.com/portfolio/"],
    "8VC": ["https://8vc.com/portfolio/"],
    "GC": ["https://generalcatalyst.com/portfolio/"],
    "Bessemer": ["https://www.bvp.com/portfolio/companies"],
    "Greylock": ["https://greylock.com/portfolio/"],
    "Index Ventures": ["https://www.indexventures.com/companies/"],
    "Spark Capital": ["https://www.sparkcapital.com/companies"],

    # ─── Tier 2: deeptech / hardtech specialists ───
    "DCVC": ["https://dcvc.com/portfolio/"],
    "Eclipse": ["https://eclipse.vc/portfolio/"],
    "Playground Global": ["https://playground.global/portfolio/"],
    "AV": ["https://av.vc/portfolio/"],            # Anduril Ventures
    "Pillar VC": ["https://www.pillar.vc/companies"],
    "Atomic": ["https://www.atomic.vc/companies"],

    # ─── Tier 3: defense / dual-use / security ───
    "Shield Capital": ["https://shieldcap.com/portfolio/"],
    "In-Q-Tel": ["https://www.iqt.org/portfolio/"],   # CIA's VC arm
    "Decisive Point": ["https://decisivepoint.com/portfolio"],
    "Cantos": ["https://cantos.vc/portfolio/"],
    "Razor's Edge": ["https://www.razorsedge.vc/portfolio/"],
    "Silent Ventures": ["https://silentvc.com/"],   # 33/45 portfolio overlap with the DB
    "Reservoir": ["https://reservoir.co/"],        # ag-robotics incubator + pre-seed fund

    # ─── Tier 4: climate / energy / hard-physics ───
    "Lower Carbon": ["https://lowercarbon.com/companies/"],     # Backs Panthalassa
    "Gigascale Capital": ["https://gigascale.com/portfolio/"],  # Backs Panthalassa

    # ─── Tier 5: emerging / boutique ───
    "Harpoon": ["https://harpoon.vc/portfolio/"],
    "Bedrock": ["https://bedrockcap.com/portfolio/"],

    # ─── Tier 6: the specialist seed funds that back this universe ───
    #
    # Added Sep 2026 after a manual scan. The lesson of that scan: the
    # generalists are the wrong place to look. Point72's page returned 128
    # companies, 111 of them not in our database and nearly all fintech —
    # correctly absent, and pure noise to wade through. Bessemer, Greylock,
    # Index and Spark have the same problem, which is why the discovery
    # queue kept surfacing OpenAI, Cohere and Anysphere.
    #
    # The funds worth scanning are the ones whose portfolio we ALREADY
    # mostly own, because that overlap is evidence their taste matches this
    # universe. Silent Ventures was 36 of 47 already tracked — a 77% hit
    # rate — and the 11 remaining produced Furientis, Supply Energetics,
    # Sandtable, Fulcrum Autonomy and North Vector Dynamics in one pass.
    #
    # These are ranked by how much of the database each already backs,
    # counted from the investors field rather than guessed at.
    "Prime Movers Lab": ["https://www.primemoverslab.com/portfolio"],
    "Riot Ventures": ["https://riot.vc/portfolio", "https://riotvc.com/portfolio"],
    "Point72 Ventures": ["https://p72.vc/ventures/portfolio/"],
    "Congruent Ventures": ["https://www.congruentvc.com/portfolio"],
    "Breakthrough Energy": ["https://www.breakthroughenergy.org/investments/"],
    "Valor Equity": ["https://valorep.com/portfolio/"],
    "NVentures": ["https://www.nvidia.com/en-us/ventures/"],
    "Washington Harbour": ["https://washingtonharbour.com/portfolio/"],
    "Initialized": ["https://initialized.com/companies"],
    "Draper Associates": ["https://draper.vc/companies"],
    "Interlagos": ["https://www.interlagos.com/"],
    "Pax Ventures": ["https://www.pax.vc/"],
    "Caffeinated Capital": ["https://caffeinatedcapital.com/"],
    "TenOneTen": ["https://www.tenoneten.net/portfolio"],
    "Wave Function": ["https://www.wavefunction.vc/"],
    "Also Capital": ["https://also.capital/"],
    "Marque Ventures": ["https://www.marque.vc/"],
    "8090 Industries": ["https://8090industries.com/"],
    "Seraphim Space": ["https://seraphim.vc/portfolio"],
    "America's Frontier Fund": ["https://www.americasfrontierfund.org/portfolio"],
}

# Portfolio pages name their CO-INVESTORS as well as their companies, and a
# naive scrape cannot tell the two apart. The Sep 2026 scan pulled "Dauntless"
# (a VC firm) and "Erebor Bank" off Silent Ventures' page as if they were
# holdings. Anything matching this is a fund, not a portfolio company.
INVESTOR_NAME_RE = re.compile(
    r"\b(ventures?|capital|partners|fund|funds|vc|equity|holdings|"
    r"investments?|accelerator|angels?|syndicate|lp|llp)\b$", re.I
)

# Names too generic to act on without a human look. A portfolio tile reading
# "Edge" or "Flux" is as likely to be a heading as a company — the Sep scan
# surfaced "Founder Tier", which is a section label on a VC's own page.
GENERIC_TILE = {
    "portfolio", "companies", "team", "about", "news", "contact", "founders",
    "founder tier", "investments", "our companies", "all", "more", "next",
    "previous", "close", "menu", "search", "edge", "flux", "core", "labs",
    "ventures", "capital", "partners", "seed", "series a", "growth", "index",
}


def _norm_fund(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


_KNOWN_FUNDS: set[str] = set()


def load_known_funds() -> set[str]:
    """Every fund name the database already knows, from VC_FIRMS and from the
    investors field on all companies.

    A suffix rule cannot do this job on its own. "8090 Industries" and
    "Prime Movers Lab" are funds while "Ares Industries" and "Foundry Lab"
    are companies, and no pattern separates them — but we hold roughly three
    thousand investor names, and anything on that list is a fund by
    definition. Cheap, exact, and it improves every time an investor is
    recorded on a company.
    """
    global _KNOWN_FUNDS
    if _KNOWN_FUNDS:
        return _KNOWN_FUNDS
    funds = set(VC_PORTFOLIO_URLS)
    try:
        text = (DATA_DIR.parent / "data.js").read_text(encoding="utf-8",
                                                       errors="replace")
        for block in re.findall(r"investors:\s*\[(.*?)\]", text, re.S):
            for m in re.findall(r'"((?:[^"\\]|\\.)*)"', block):
                funds.add(m)
        for m in re.findall(r'name:\s*"([^"]+)"[^}]*?\baum:', text, re.S):
            funds.add(m)
    except Exception as e:                       # never let this kill a run
        print(f"  (could not load fund names from data.js: {e})")
    _KNOWN_FUNDS = {_norm_fund(f) for f in funds if len(f) > 2}
    return _KNOWN_FUNDS


def looks_like_investor(name: str) -> bool:
    """True when a scraped tile is a fund rather than a portfolio company."""
    n = (name or "").strip()
    if not n:
        return True
    if n.lower() in GENERIC_TILE:
        return True
    if INVESTOR_NAME_RE.search(n):
        return True
    if _norm_fund(n) in load_known_funds():
        return True
    return False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def load_existing_portfolios():
    """Load existing portfolioCompanies from data.js for each VC."""
    if not DATA_JS_PATH.exists():
        return {}

    content = DATA_JS_PATH.read_text()
    portfolios = {}

    # Find each VC entry and extract its portfolioCompanies
    for short_name in VC_PORTFOLIO_URLS.keys():
        pattern = rf'shortName:\s*"{re.escape(short_name)}"'
        match = re.search(pattern, content)
        if not match:
            continue

        # Look for portfolioCompanies array after this match
        after = content[match.start():match.start() + 3000]
        portfolio_match = re.search(r'portfolioCompanies:\s*\[([^\]]*)\]', after)
        if portfolio_match:
            companies = re.findall(r'"([^"]+)"', portfolio_match.group(1))
            portfolios[short_name] = set(companies)

    return portfolios


def load_tracked_companies():
    """Load all company names tracked in the database."""
    if not DATA_JS_PATH.exists():
        return set()

    content = DATA_JS_PATH.read_text()
    # Match company names from the COMPANIES array
    names = set(re.findall(r'name:\s*"([^"]+)"', content[:500000]))
    return names


def scrape_portfolio_page(url):
    """
    Scrape a VC portfolio page and extract company names.
    Uses simple HTML parsing to find company names in common patterns.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
    except requests.RequestException as e:
        print(f"  Failed to fetch {url}: {e}")
        return []

    company_names = set()

    # Strategy 1: Look for company names in common HTML patterns
    # Many VC sites use structured markup for portfolio companies

    # Pattern: <h2>, <h3>, <h4> tags with company names
    for tag in ['h2', 'h3', 'h4', 'h5']:
        for match in re.finditer(
            rf'<{tag}[^>]*>\s*([^<]+?)\s*</{tag}>',
            html, re.IGNORECASE
        ):
            name = match.group(1).strip()
            # Filter: reasonable company name length
            if 2 < len(name) < 60 and not name.startswith('<'):
                company_names.add(name)

    # Pattern: alt text on images (logos)
    for match in re.finditer(r'alt="([^"]+)"', html, re.IGNORECASE):
        name = match.group(1).strip()
        # Filter for likely company names (not generic alt text)
        if (2 < len(name) < 50
            and 'logo' not in name.lower()
            and 'icon' not in name.lower()
            and 'image' not in name.lower()
            and 'photo' not in name.lower()
            and 'banner' not in name.lower()):
            company_names.add(name)

    # Pattern: data attributes commonly used for company names
    for match in re.finditer(
        r'data-(?:company|name|title)="([^"]+)"',
        html, re.IGNORECASE
    ):
        name = match.group(1).strip()
        if 2 < len(name) < 60:
            company_names.add(name)

    # Pattern: aria-label on links/cards
    for match in re.finditer(
        r'aria-label="([^"]+)"',
        html, re.IGNORECASE
    ):
        name = match.group(1).strip()
        if 2 < len(name) < 50:
            company_names.add(name)

    # Pattern: JSON-LD structured data
    for match in re.finditer(
        r'"name"\s*:\s*"([^"]+)"',
        html
    ):
        name = match.group(1).strip()
        if 2 < len(name) < 60:
            company_names.add(name)

    return list(company_names)


def match_to_tracked(scraped_names, tracked_companies):
    """
    Match scraped company names to tracked companies in the database.
    Uses fuzzy matching to handle slight name variations.
    """
    matches = set()
    tracked_lower = {name.lower(): name for name in tracked_companies}

    for scraped in scraped_names:
        scraped_lower = scraped.lower().strip()

        # Exact match
        if scraped_lower in tracked_lower:
            matches.add(tracked_lower[scraped_lower])
            continue

        # Match without common suffixes
        for suffix in [' inc', ' inc.', ' corp', ' corp.', ' llc', ' ltd',
                       ' co', ' co.', ' technologies', ' technology']:
            cleaned = scraped_lower.rstrip('.').removesuffix(suffix)
            if cleaned in tracked_lower:
                matches.add(tracked_lower[cleaned])
                break

        # Check if any tracked company name is contained in the scraped name
        for tracked_lower_name, tracked_original in tracked_lower.items():
            if len(tracked_lower_name) >= 5:
                if tracked_lower_name in scraped_lower or scraped_lower in tracked_lower_name:
                    matches.add(tracked_original)

    return matches


def main():
    print("=" * 60)
    print("VC Portfolio Page Scraper")
    print(f"Run time: {datetime.now().isoformat()}")
    print("=" * 60)

    # Load existing data
    existing_portfolios = load_existing_portfolios()
    tracked_companies = load_tracked_companies()

    print(f"\nLoaded {len(existing_portfolios)} VC portfolios from data.js")
    print(f"Tracking {len(tracked_companies)} companies in database")

    all_changes = []
    total_new = 0
    # Names a fund holds that we do NOT track. This is the discovery output,
    # and until Sep 2026 the script threw it away: it only ever asked which
    # KNOWN companies a fund holds, so it could enrich a VC record but could
    # never find a company. Every one of the 247 companies added in the 60
    # days to September came from a human doing this scan by hand.
    candidates = []

    for vc_short, urls in VC_PORTFOLIO_URLS.items():
        existing = existing_portfolios.get(vc_short, set())
        print(f"\n--- {vc_short} (currently {len(existing)} companies) ---")

        all_scraped = set()
        for url in urls:
            print(f"  Scraping: {url}")
            scraped = scrape_portfolio_page(url)
            print(f"    Found {len(scraped)} raw names")
            all_scraped.update(scraped)

        # Match scraped names to tracked companies
        matched = match_to_tracked(all_scraped, tracked_companies)
        print(f"  Matched to {len(matched)} tracked companies")

        # ── the discovery half ──────────────────────────────────────────
        # Anything scraped that matched nothing is a candidate, once the
        # co-investor names and generic page furniture are stripped out.
        #
        # Overlap is the quality signal. A fund whose portfolio we already
        # mostly hold has taste that matches this universe, so its unknowns
        # are worth reading; a fund we barely overlap with is either off-
        # thesis or badly scraped, and its unknowns are noise either way.
        # Silent Ventures scored 77% and yielded five real companies in one
        # pass. Point72 scored 9% and yielded 111 fintech names.
        unmatched = sorted(
            n for n in all_scraped
            if n not in matched and not looks_like_investor(n)
            and 2 < len(n) < 46
        )
        overlap = len(matched) / len(all_scraped) if all_scraped else 0.0
        if unmatched:
            print(f"  {len(unmatched)} not in database "
                  f"(portfolio overlap {overlap:.0%})")
            for n in unmatched[:12]:
                print(f"      · {n}")
            if len(unmatched) > 12:
                print(f"      … and {len(unmatched) - 12} more")
        for n in unmatched:
            candidates.append({
                "name": n,
                "vc": vc_short,
                "vc_overlap": round(overlap, 3),
                "portfolio_size": len(all_scraped),
                "detected_date": datetime.now().strftime("%Y-%m-%d"),
            })

        # Find new additions (in scraped but not in existing portfolio)
        new_companies = matched - existing
        if new_companies:
            print(f"  NEW: {', '.join(sorted(new_companies))}")
            total_new += len(new_companies)

            for company in sorted(new_companies):
                all_changes.append({
                    "vc": vc_short,
                    "company": company,
                    "source": "portfolio_page",
                    "detected_date": datetime.now().strftime("%Y-%m-%d"),
                })
        else:
            print("  No new companies detected")

    # Save results
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / "vc_portfolio_changes.json"

    # Load existing changes and append (keep history)
    existing_changes = []
    if output_path.exists():
        try:
            existing_changes = json.loads(output_path.read_text())
        except json.JSONDecodeError:
            existing_changes = []

    # Deduplicate: don't add if same vc+company already recorded this week
    existing_keys = {(c["vc"], c["company"]) for c in existing_changes
                     if c.get("detected_date", "") >= (datetime.now().strftime("%Y-%m"))}

    new_changes = [c for c in all_changes
                   if (c["vc"], c["company"]) not in existing_keys]

    if new_changes:
        combined = existing_changes + new_changes
        # Keep last 90 days of history
        cutoff = datetime.now().strftime("%Y-%m-%d")
        combined = [c for c in combined
                    if c.get("detected_date", "2020-01-01") >= "2025-12-01"]
        output_path.write_text(json.dumps(combined, indent=2))

    # ── write the discovery candidates ──────────────────────────────────
    # Ranked by the overlap of the fund that holds them, so the reviewer
    # reads the high-taste funds first and never has to wade through a
    # generalist's fintech book to reach them.
    cand_path = DATA_DIR / "vc_portfolio_candidates.json"
    candidates.sort(key=lambda c: (-c["vc_overlap"], c["vc"], c["name"].lower()))
    by_fund = {}
    for c in candidates:
        by_fund.setdefault(c["vc"], []).append(c["name"])
    cand_path.write_text(json.dumps({
        "generated_at": datetime.now().isoformat(),
        "note": ("Portfolio names held by tracked frontier funds that are not "
                 "in COMPANIES. Ranked by that fund's portfolio overlap with "
                 "the database: high overlap means the fund's taste matches "
                 "this universe, so its unknowns are worth reading. These are "
                 "leads, not verified companies — each still needs a founder, "
                 "a location and a round before it earns a record."),
        "funds_scanned": len(VC_PORTFOLIO_URLS),
        "total_candidates": len(candidates),
        "high_overlap_candidates": sum(1 for c in candidates if c["vc_overlap"] >= 0.4),
        "by_fund": by_fund,
        "candidates": candidates,
    }, indent=2))

    print(f"\n{'=' * 60}")
    print(f"Total new portfolio additions detected: {total_new}")
    print(f"Changes saved to: {output_path}")
    print(f"\nDISCOVERY: {len(candidates)} names not in the database, "
          f"{sum(1 for c in candidates if c['vc_overlap'] >= 0.4)} of them from "
          f"funds with >=40% overlap")
    print(f"Candidates saved to: {cand_path}")
    top = [c for c in candidates if c["vc_overlap"] >= 0.4][:15]
    if top:
        print("\nread these first:")
        for c in top:
            print(f"  [{c['vc_overlap']:.0%} {c['vc']:<20}] {c['name']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
