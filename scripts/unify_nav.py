#!/usr/bin/env python3
"""
Unify navigation across every HTML page on the site.

v2 (15 Oct 2026, homepage-ia-prototype): navigation by INTENT, six top-level
items and no nested dropdowns:

  Companies | What's New | Sectors & Theses | Capital | Calendar | Jobs

Each item (except Jobs, a single page) opens a one-column landing panel on
click that lists its tools with a one-line description and a live count
(filled by nav.js from in-page data or data/nav_counts.json). The panel
markup is generated from NAV_GROUPS below, so adding a tool is one line.

This script replaces the existing `<nav class="nav">…</nav>` block (plus the
nav.js include that follows it) on every .html file with the canonical nav,
marks the current page (aria-current="page" on the link, .is-active on its
group) and injects `<script src="nav.js" defer>` after the nav.

Usage:
  python scripts/unify_nav.py [--dry-run]
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NAV_JS_VERSION = "20261015"

# ─── THE INTENT MAP ───────────────────────────────────────────────────────
# (href, nav-id, name, one-line description, count key, count label)
# count key = a field in data/nav_counts.json / an in-page global (see nav.js).
NAV_GROUPS = [
    {
        "id": "companies", "label": "Companies",
        "items": [
            ("companies.html", "companies", "Company database",
             "Search and filter every tracked company. Grid, market map, CSV export.", "companies", "companies"),
            ("companies.html#discovery-hub", "discovery-hub", "Innovation map",
             "Every company on a world map, coloured by sector.", "countries", "countries"),
            ("compare.html", "compare", "Compare companies",
             "Side by side on funding, stage, signals and customers.", None, None),
            ("customers.html", "customers", "Customers",
             "Who buys from the companies we track: government and commercial.", None, None),
        ],
        "foot": '<a href="lab.html">Research lab</a> &mdash; the Frontier Index, network graph, '
                'portfolio builder and ten more quantitative tools.',
    },
    {
        "id": "new", "label": "What&rsquo;s New",
        "items": [
            ("wire.html", "wire", "The Wire",
             "Every change across the database, newest first: rounds, filings, contracts, launches.", "wire_events_week", "this week"),
            ("rounds.html", "rounds", "Raised",
             "Funding rounds read from company newsrooms, before the trade press.", "rounds_30d", "in 30 days"),
            ("radar.html", "radar", "Radar",
             "SEC Form D filings matched to tracked companies: size and subscription progress.", "radar_30d", "filings, 30 days"),
            ("changes.html", "changes", "This week&rsquo;s changes",
             "The weekly changelog: companies added, status, funding and valuation moves.", "changelog_added", "added"),
            ("brief.html", "brief", "Frontier Daily",
             "Today&rsquo;s most important news and activity in one brief.", None, None),
        ],
    },
    {
        "id": "sectors", "label": "Sectors &amp; Theses",
        "items": [
            ("sectors.html", "sectors", "All sectors",
             "Every sector mapped: momentum, top companies and theses.", "sectors", "sectors"),
            ("defense.html", "defense", "Defense",
             "Autonomy, counter-drone, hypersonics, EW: rebuilding the Western industrial base.", None, None),
            ("nuclear.html", "nuclear", "Nuclear",
             "SMRs, microreactors, fusion and advanced fuels.", None, None),
            ("space.html", "space", "Space",
             "Launch, satellites, in-space manufacturing and propulsion.", None, None),
            ("reindustrialize.html", "reindustrialize", "Reindustrialize",
             "The companies rebuilding America&rsquo;s industrial base.", None, None),
            ("il30.html", "il30", "Innovators League 30",
             "The 30 most important innovative companies of 2026, handpicked by ROS.", "il30", "companies"),
        ],
        "foot": '<a href="lab.html#thesis-collision">Who else is building this?</a> &mdash; 76 thesis clusters in the Research lab.',
    },
    {
        "id": "capital", "label": "Capital", "right": True,
        "items": [
            ("investors.html", "investors", "Investors",
             "Directory of every firm tracked: theses, portfolios, co-investment.", "investors", "investors"),
            ("investor-intelligence.html", "investor-intelligence", "Investor intelligence",
             "Pattern recognition across the VC universe: momentum, specialists, pedigree.", None, None),
            ("investor-hub.html", "investor-hub", "Investor hub",
             "Active raises, funding pulse and the co-investor network.", None, None),
            ("valuations.html", "valuations", "Valuations",
             "Valuation benchmarks, revenue multiples and IPO readiness.", None, None),
            ("captable.html", "captable", "Cap tables",
             "Ownership, dilution and investor stakes.", None, None),
            ("baskets.html", "baskets", "Public baskets",
             "Public-market baskets for every private thesis.", None, None),
            ("exitwatch.html", "exitwatch", "Exit Watch",
             "First SEC Form D filings by new entities, matched to founders we already track.", None, None),
            ("govradar.html", "govradar", "Gov contracts &amp; demand",
             "Federal spending, agency demand signals and contract opportunities.", None, None),
        ],
    },
    {
        "id": "calendar", "label": "Calendar", "right": True,
        "items": [
            ("catalysts.html", "catalysts", "Catalyst calendar",
             "Every dated event that could move a valuation: FDA, FAA, NRC, earnings, conferences.", "catalysts_upcoming", "ahead"),
            ("calendar.html", "calendar", "Industry events",
             "Conferences, industry events and site visits worth the trip.", None, None),
            ("launches.html", "launches", "Space launches",
             "Upcoming launches and the frontier-tech payloads on them.", None, None),
            ("earnings-signals.html", "earnings-signals", "Earnings signals",
             "Frontier-tech quotes from public-company earnings calls, tagged by vertical.", None, None),
            ("regulatory.html", "regulatory", "Regulatory",
             "FDA, NRC, FAA and DOE pathways and milestones.", None, None),
        ],
    },
]

# Single-page intents rendered as a plain link (no panel).
NAV_DIRECT = [
    ("jobs.html", "jobs", "Jobs"),
]

# Pages that are not panel items but belong to an intent (for highlighting).
PAGE_GROUP_FALLBACK = {
    "company": "companies",
    "investor-firm": "capital",
}

CHEVRON = ('<svg width="10" height="6" viewBox="0 0 10 6" fill="none" stroke="currentColor" '
           'stroke-width="1.5" aria-hidden="true"><path d="M1 1l4 4 4-4"/></svg>')
SEARCH_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
               '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>')


def render_nav(page_id):
    """Build the canonical nav for `page_id` (filename stem) with the current
    page marked."""
    active_group = PAGE_GROUP_FALLBACK.get(page_id)
    for g in NAV_GROUPS:
        for href, nid, *_ in g["items"]:
            if href.split("#")[0].split("?")[0] == f"{page_id}.html":
                active_group = g["id"]
    out = []
    out.append('    <!-- Navigation — intent-based IA v2 (auto-generated by scripts/unify_nav.py; edit NAV_GROUPS there) -->')
    out.append('    <nav class="nav nav-v2" aria-label="Primary">')
    out.append('        <div class="nav-brand">')
    out.append('            <a href="index.html" style="display:flex;align-items:center;gap:8px;text-decoration:none;">')
    out.append('                <div class="nav-logo">ROS</div>')
    out.append('                <span class="nav-title">INNOVATORS LEAGUE</span>')
    out.append('            </a>')
    out.append('        </div>')
    out.append('        <div class="nav-links" id="nav-links">')
    for g in NAV_GROUPS:
        cls = "nav-group" + (" nav-group--right" if g.get("right") else "") + (" is-active" if g["id"] == active_group else "")
        out.append(f'            <div class="{cls}" data-nav-group="{g["id"]}">')
        out.append(f'                <button type="button" class="nav-group-btn" aria-expanded="false" '
                   f'aria-controls="nav-panel-{g["id"]}">{g["label"]} {CHEVRON}</button>')
        out.append(f'                <div class="nav-panel" id="nav-panel-{g["id"]}" hidden>')
        out.append(f'                    <div class="nav-panel-head">{g["label"]}</div>')
        for href, nid, name, desc, ckey, clabel in g["items"]:
            is_cur = href.split("#")[0].split("?")[0] == f"{page_id}.html" and "#" not in href
            cur = ' aria-current="page"' if is_cur else ""
            out.append(f'                    <a class="nav-panel-item" href="{href}" data-nav-id="{nid}"{cur}>')
            out.append(f'                        <span class="nav-panel-name">{name}</span>')
            out.append(f'                        <span class="nav-panel-desc">{desc}</span>')
            if ckey:
                out.append(f'                        <span class="nav-panel-count" data-count="{ckey}" data-count-label="{clabel}"></span>')
            out.append('                    </a>')
        if g.get("foot"):
            out.append(f'                    <div class="nav-panel-foot">{g["foot"]}</div>')
        out.append('                </div>')
        out.append('            </div>')
    for href, nid, label in NAV_DIRECT:
        cur = ' aria-current="page"' if href == f"{page_id}.html" else ""
        out.append(f'            <a href="{href}" class="nav-link" data-nav-id="{nid}"{cur}>{label}</a>')
    out.append('            <div class="nav-drawer-auth">')
    out.append('                <button type="button" class="nav-sign-in-btn" onclick="TILAuth.showAuthModal()">Sign in</button>')
    out.append('                <a href="https://www.rationaloptimistsociety.com" target="_blank" rel="noopener" class="nav-cta">Join ROS</a>')
    out.append('            </div>')
    out.append('        </div>')
    out.append('        <div class="nav-right">')
    out.append(f'            <a class="nav-search-btn" href="companies.html#search" data-nav-id="search" aria-label="Search companies">{SEARCH_ICON}<span>Search</span></a>')
    out.append('            <div class="nav-auth" id="nav-auth">')
    out.append('                <button class="nav-sign-in-btn" onclick="TILAuth.showAuthModal()">Sign in</button>')
    out.append('                <a href="https://www.rationaloptimistsociety.com" target="_blank" rel="noopener" class="nav-cta">Join ROS</a>')
    out.append('            </div>')
    out.append('            <div class="nav-user" id="nav-user" style="display:none;">')
    out.append('                <span class="nav-user-email" id="nav-user-email"></span>')
    out.append('                <button class="nav-signout-btn" onclick="TILAuth.signOut()">Sign out</button>')
    out.append('            </div>')
    out.append('            <button class="mobile-menu-btn" aria-label="Menu" aria-expanded="false" aria-controls="nav-links"><span></span><span></span><span></span></button>')
    out.append('        </div>')
    out.append('    </nav>')
    out.append(f'    <script src="nav.js?v={NAV_JS_VERSION}" defer></script>')
    return "\n".join(out)


# Pages to skip (not user-facing)
SKIP_FILES = {
    "styleguide.html",      # internal preview, has minimal page-specific layout
    "terms.html",           # legal, may have different layout
    "privacy.html",         # legal, may have different layout
}

# Match the existing <nav class="nav">…</nav> block (also handles modifier
# classes like "nav nav-minimal" used by company.html, and the v2 "nav nav-v2"),
# an optional preceding HTML comment labelling the nav, and the nav.js include
# injected after it, so re-runs replace the whole thing.
NAV_RE = re.compile(
    r'(?:[ \t]*<!--[^\n]*nav[^\n]*-->\s*\n)?'   # optional preceding comment
    r'[ \t]*<nav class="nav(?:\s+[^"]*)?"[^>]*>[\s\S]*?</nav>'
    r'(?:\s*<script src="nav\.js[^"]*"[^>]*></script>)?',
    re.IGNORECASE,
)


def page_id_from_filename(path):
    """Map foo.html → 'foo' (used as data-nav-id)."""
    return path.stem


def update_file(path, dry_run=False):
    """Replace the nav block in `path` with the unified version, preserving
    any modifier classes (e.g. .nav-minimal on company.html)."""
    src = path.read_text(encoding="utf-8")

    page_id = page_id_from_filename(path)
    new_nav = render_nav(page_id)

    m = NAV_RE.search(src)
    if not m:
        return ("skip", "no nav block found")

    old_block = m.group(0)
    nav_class_m = re.search(r'<nav class="(nav(?:\s+[^"]*)?)"', old_block)
    if nav_class_m:
        extras = [c for c in nav_class_m.group(1).split()[1:] if c != "nav-v2"]
        if extras:
            new_nav = new_nav.replace('<nav class="nav nav-v2"', f'<nav class="nav nav-v2 {" ".join(extras)}"', 1)

    new_src = src[:m.start()] + new_nav + src[m.end():]
    if new_src == src:
        return ("noop", "already unified")

    if dry_run:
        return ("preview", f"would replace {len(old_block)}B with {len(new_nav)}B")

    path.write_text(new_src, encoding="utf-8")
    return ("ok", f"replaced {len(old_block)}B → {len(new_nav)}B")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("=" * 64)
    print("Nav unification (intent-based IA v2)")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY'}")
    print("=" * 64)

    html_files = sorted([
        p for p in ROOT.glob("*.html")
        if p.name not in SKIP_FILES
    ])

    summary = {"ok": 0, "noop": 0, "skip": 0, "preview": 0}

    for p in html_files:
        status, msg = update_file(p, dry_run=args.dry_run)
        summary[status] = summary.get(status, 0) + 1
        sym = {"ok": "✓", "noop": "·", "skip": "⏭", "preview": "→"}.get(status, "?")
        print(f"  {sym} {p.name:<35} {msg}")

    print()
    print(f"Summary: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
