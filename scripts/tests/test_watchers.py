#!/usr/bin/env python3
"""
Offline tests for the name-collision guard, the BuildList HQ cross-check
(scripts/fetch_curated_lists.py) and the job-board adapters in
scripts/fetch_vc_portfolio_watcher.py.

    python3 scripts/tests/test_watchers.py        # plain runner, exit 1 on failure
    python3 -m pytest scripts/tests                # also works where pytest exists

No network and no Node: the adapters are fed canned API responses shaped like
the ones Getro, Consider, jobs.a16z.com and sequoiacap.com returned on
7 Oct 2026, and the database is a handful of fixture rows. The live
data/name_collisions.json is used, since that file is what is under test.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fetch_curated_lists as fc  # noqa: E402
import fetch_vc_portfolio_watcher as w  # noqa: E402

COLLISIONS = fc.load_collisions()


def check(got, want, what):
    assert got == want, f"{what}: got {got!r}, want {want!r}"


def db_row(name, website="", location="", state="", country="United States", former=(), founder=""):
    return {"n": name, "f": list(former), "p": founder, "w": website, "l": location, "s": state, "c": country}


DB = [
    db_row("Navier", "https://www.navierboat.com", "Alameda, CA", "CA"),
    db_row("Monumental", "https://www.monumental.co", "Amsterdam, Netherlands", "", "Netherlands"),
    db_row("Monumental Labs", "https://www.monumentallabs.co", "New York, NY", "NY"),
    db_row("Varda Space Industries", "https://varda.com", "El Segundo, CA", "CA"),
    db_row("Hadrian", "https://www.hadrian.co", "Torrance, CA", "CA"),
    db_row("Hermeus", "https://www.hermeus.com", "Hawthorne, CA", "CA"),
    db_row("Rivian", "https://rivian.com", "Irvine, CA", "CA"),
    db_row("Clone Robotics", "https://clonerobotics.com", "Wrocław, Poland", "", "Poland"),
    db_row("Moment Energy", "https://www.momentenergy.com", "Surrey, BC", "", "Canada"),
]


# ── collision guard in the curated-list matcher ───────────────────────────

def test_collision_file_loads_every_pair():
    for a, b in (("Monumental Labs", "Monumental"), ("Navier AI", "Navier"),
                 ("Atmos Thermal", "Atmos Space Cargo"), ("Manifold Industries", "Manifold Bio"),
                 ("Edgerun", "EdgeRunner AI"), ("Arxlight", "xLight"),
                 ("American Terawatt", "TeraWatt Technology"),
                 ("Inversion Semiconductor", "Inversion Space"),
                 ("Bedrock Ocean Exploration", "Bedrock Robotics")):
        assert fc.different_company(a, b, COLLISIONS), f"{a} / {b} not recorded"
        assert fc.different_company(b, a, COLLISIONS), f"{b} / {a} not symmetric"
    assert not fc.different_company("Varda Space", "Varda Space Industries", COLLISIONS)


def test_suffix_stem_never_merges_a_known_different_company():
    exact, stems, _ = fc.known_names([r for r in DB if r["n"] != "Monumental Labs"])
    check(fc.is_tracked("Navier AI", exact, stems, COLLISIONS), False, "Navier AI vs Navier")
    check(fc.is_tracked("Monumental Labs", exact, stems, COLLISIONS), False,
          "Monumental Labs vs Monumental (record absent)")
    check(fc.is_tracked("Varda Space", exact, stems, COLLISIONS), True, "real suffix variant")
    check(fc.is_tracked("Navier", exact, stems, COLLISIONS), True, "exact name")
    exact, stems, _ = fc.known_names(DB)
    check(fc.is_tracked("Monumental Labs", exact, stems, COLLISIONS), True, "its own record")


# ── HQ cross-check ─────────────────────────────────────────────────────────

def test_place_parser():
    check(fc._place("San Francisco, CA"), ("san francisco", "CA", "united states"), "US")
    check(fc._place("Washington, D.C."), ("washington", "DC", "united states"), "DC")
    check(fc._place("Toronto, Canada"), ("toronto", "", "canada"), "non-US")
    check(fc._place("Bristol, England, UK"), ("bristol", "", "united kingdom"), "three parts")
    check(fc._place("Luxembourg"), ("", "", "luxembourg"), "country only")
    check(fc._place("Wrocław, Poland"), ("wroclaw", "", "poland"), "diacritics")
    check(fc._place(""), ("", "", ""), "empty")


def test_hq_crosscheck():
    bl = [
        # domain match through an own-site careers link, different state
        {"name": "Hadrian Automation", "city": "Austin, TX", "metro": "Austin",
         "careers_url": "https://careers.hadrian.co/jobs"},
        # exact name, same state, different city
        {"name": "Navier", "city": "San Francisco, CA", "metro": "SF Bay Area",
         "careers_url": "https://jobs.ashbyhq.com/navier"},
        # exact name, different country
        {"name": "Clone Robotics", "city": "New York, NY", "metro": "NYC", "careers_url": ""},
        # agrees: not reported
        {"name": "Rivian", "city": "Irvine, CA", "metro": "Los Angeles",
         "careers_url": "https://careers.rivian.com"},
        # same name, but its own careers site differs from ours: vetoed
        {"name": "Monumental", "city": "Austin, TX", "metro": "Austin", "careers_url": "https://monumental.io/careers"},
        # a known different company: never compared with Navier
        {"name": "Navier AI", "city": "Boston, MA", "metro": "Boston", "careers_url": ""},
        # on the ignore list
        {"name": "Hermeus", "city": "Atlanta, GA", "metro": "Atlanta", "careers_url": ""},
        {"name": "Moment Energy", "city": "Coquitlam, Canada", "metro": "Canada", "careers_url": ""},
    ]
    r = fc.hq_crosscheck(bl, DB, COLLISIONS, "2026-10-07T00:00:00+00:00")
    got = {(i["company"], i["kind"], i["matched_by"]) for i in r["items"]}
    check(got, {("Hadrian", "state", "domain"), ("Navier", "city", "name"),
                ("Clone Robotics", "country", "name")}, "reported items")
    check(r["ignored"], ["Hermeus", "Moment Energy"], "ignore list")
    check(r["by_kind"], {"country": 1, "state": 1, "city": 1}, "by_kind")
    check(r["compared"], 4, "compared (Hadrian, Navier, Clone, Rivian)")
    check([i["kind"] for i in r["items"]], ["country", "state", "city"], "sorted by severity")


def test_hq_crosscheck_never_writes():
    before = fc.DATA_JS.stat().st_mtime_ns, fc.HQ_OUT.exists() and fc.HQ_OUT.stat().st_mtime_ns
    fc.hq_crosscheck([], DB, COLLISIONS)
    after = fc.DATA_JS.stat().st_mtime_ns, fc.HQ_OUT.exists() and fc.HQ_OUT.stat().st_mtime_ns
    check(after, before, "hq_crosscheck() is pure; only main() writes the report, never data.js")


# ── VC watcher adapters (canned responses) ───────────────────────────────

class FakeResponse:
    def __init__(self, payload=None, text=""):
        self._payload, self.text = payload, text

    def json(self):
        return self._payload


def with_fakes(get=None, post=None):
    """Swap the watcher's HTTP helpers for the duration of one call."""
    def deco(fn):
        def run():
            saved = w.get, w.post, w.time.sleep
            w.time.sleep = lambda s: None
            if get:
                w.get = get
            if post:
                w.post = post
            try:
                return fn()
            finally:
                w.get, w.post, w.time.sleep = saved
        return run
    return deco


def getro_company(i, name, domain, loc="Austin, TX, USA", tags=("Manufacturing",)):
    return {"id": i, "slug": name.lower().replace(" ", "-"), "name": name, "domain": domain,
            "description": f"{name} builds things.", "locations": [loc], "industry_tags": list(tags)}


GETRO_PAGES = [
    [getro_company(1, "Navier", "navierboat.com"), getro_company(2, "Cantos", "cantos.vc", tags=("Venture",)),
     getro_company(3, "Nylas", "nylas.com", tags=("Developer APIs", "Software"))],
    [getro_company(4, "Neptune Bio", "neptune.bio", tags=("Biotechnology",))],
    [],
]


def test_getro_adapter_pages_and_drops_the_fund_itself():
    calls = []

    def post(url, session=None, **kw):
        calls.append((url, kw["headers"]["Origin"], kw["json"]))
        page = kw["json"]["page"]
        return FakeResponse({"results": {"companies": GETRO_PAGES[page], "count": 4}})

    rows = with_fakes(post=post)(lambda: w.extract_getro(w.FUNDS["Cantos"]))()
    check(calls[0][0], "https://api.getro.com/api/v2/collections/220/search/companies", "endpoint")
    check(calls[0][1], "https://jobs.cantos.vc", "board Origin header")
    check([c[2] for c in calls], [{"hitsPerPage": 12, "page": 0}, {"hitsPerPage": 12, "page": 1}],
          "stops once count is reached")
    check([r["name"] for r in rows], ["Navier", "Nylas", "Neptune Bio"], "fund's own entry dropped")
    check((rows[0]["domain"], rows[0]["hq"]), ("navierboat.com", "Austin, TX, USA"), "domain and HQ")
    check(rows[1]["_tags"], ["Developer APIs", "Software"], "industry tags kept for the bar")
    assert not w.HARD_TAGS.search(" | ".join(rows[1]["_tags"])), "software tags pass the tag bar"
    assert w.HARD_TAGS.search(" | ".join(rows[2]["_tags"])), "biotech fails the tag bar"


def test_consider_adapter_uses_csrf_and_sequence():
    page_html = '<script>window.serverInitialData = {"csrfToken":"tok-123","board":{"id":"sequoia-capital"}};</script>'
    pages = [
        {"companies": [{"id": "SpaceX", "slug": "spacex", "name": "SpaceX", "domain": "spacex.com",
                        "website": {"url": "https://spacex.com/"}, "officeLocations": ["Hawthorne, California"],
                        "investorSlugs": ["sequoia-capital"], "markets": ["Aviation & Aerospace"]},
                       {"id": "Other", "slug": "other", "name": "Other", "domain": "other.com",
                        "investorSlugs": ["someone-else"]}],
         "total": 3, "meta": {"size": 100, "sequence": "abc"}, "errors": []},
        {"companies": [{"id": "Zipline", "slug": "zipline", "name": "Zipline", "domain": "flyzipline.com",
                        "investorSlugs": ["sequoia-capital"]}],
         "total": 3, "meta": {"size": 100, "sequence": "def"}, "errors": []},
    ]
    seen = []

    def get(url, session=None, **kw):
        return FakeResponse(text=page_html)

    def post(url, session=None, **kw):
        seen.append((kw["headers"].get("x-csrf-token"), kw["json"]))
        return FakeResponse(pages[len(seen) - 1])

    rows = with_fakes(get=get, post=post)(lambda: w.extract_consider(w.FUNDS["Sequoia"]))()
    check(seen[0][0], "tok-123", "csrf header")
    check(seen[0][1], {"meta": {"size": 100}, "board": {"id": "sequoia-capital", "isParent": True}, "query": {}},
          "first page body")
    check(seen[1][1]["meta"], {"size": 100, "sequence": "abc"}, "second page follows meta.sequence")
    check([r["name"] for r in rows], ["SpaceX", "Zipline"], "co-investor-only listing dropped")
    check((rows[0]["domain"], rows[0]["hq"]), ("spacex.com", "Hawthorne, California"), "domain and office")


def test_a16z_board_adapter_reads_the_flight_payload():
    companies = [{"id": "x1", "slug": "anduril-industries", "name": "Anduril", "domain": "anduril.com",
                  "description": "Defense technology.", "location": "Costa Mesa, United States",
                  "markets": ["AI"]},
                 {"id": "x2", "slug": "hadrian", "name": "Hadrian", "domain": "hadrian.co",
                  "description": "Factories.", "location": None, "markets": ["American Dynamism"]}]
    flight = '5:["$","div",null,{"children":["$","$L17",null,{"companies":' + json.dumps(companies) + '}]}]'
    html = f'<script>self.__next_f.push([1,{json.dumps(flight)}])</script>'
    rows = with_fakes(get=lambda url, session=None, **kw: FakeResponse(text=html))(
        lambda: w.extract_a16z_board(w.FUNDS["a16z"]))()
    check([(r["name"], r["domain"], r["hq"]) for r in rows],
          [("Anduril", "anduril.com", "Costa Mesa, United States"), ("Hadrian", "hadrian.co", "")], "rows")
    check(rows[1]["_focus_set"], {"American Dynamism"}, "markets become the focus set")


def test_merge_keeps_board_rows_and_fills_focus_from_the_portfolio_json():
    board = [w.holding(name="Anduril", website="https://anduril.com"),
             w.holding(name="Databricks", website="https://databricks.com")]
    board[0]["_focus_set"], board[1]["_focus_set"] = {"AI"}, {"Enterprise"}
    portfolio = [w.holding(name="Anduril Industries", website="https://www.anduril.com", first_funded="2017-06-01"),
                 w.holding(name="Castelion", website="https://castelion.com")]
    portfolio[0]["_focus_set"], portfolio[1]["_focus_set"] = {"American Dynamism"}, {"American Dynamism"}
    rows = w.merge_holdings(board, portfolio)
    check([r["name"] for r in rows], ["Anduril", "Databricks", "Castelion"], "union by domain")
    check(rows[0]["_focus_set"], {"AI", "American Dynamism"}, "focus areas unioned")
    check(rows[0]["first_funded"], "2017-06-01", "first-investment date filled in")


def test_fallback_runs_when_the_board_fails():
    saved = dict(w.EXTRACTORS)
    try:
        w.EXTRACTORS["getro"] = lambda fund: (_ for _ in ()).throw(ConnectionError("board down"))
        w.EXTRACTORS["cards_lux"] = lambda fund: [w.holding(name="Lux Holding")]
        rows, used, note = w.run_adapters(w.FUNDS["Lux"])
        check((len(rows), used), (1, "cards_lux"), "fell back")
        assert "getro failed" in note and "board down" in note, note
        w.EXTRACTORS["getro"] = lambda fund: []
        rows, used, note = w.run_adapters(w.FUNDS["Lux"])
        check(used, "cards_lux", "an empty board also falls back")
    finally:
        w.EXTRACTORS.clear()
        w.EXTRACTORS.update(saved)


def test_sequoia_page_link_and_domain_only_matching():
    html = ('<a href="https://sequoiacap.com/our-companies">Companies</a>'
            '<a class="framer-x" href="https://www.apexhq.ai/">apexhq.ai</a>'
            '<a aria-label="View LinkedIn profile" href="https://www.linkedin.com/company/apexhq-ai/"></a>')
    check(w._company_link(html), "https://www.apexhq.ai/", "company link")
    db = {"by_domain": {"apexspace.com": "Apex Space", "navierboat.com": "Navier"},
          "by_label": {}, "by_norm": {"apexspace": "Apex Space", "apex": "Apex Space", "navier": "Navier"},
          "by_stem": {"apex": "Apex Space", "navier": "Navier"},
          "domain_of": {"Apex Space": "apexspace.com", "Navier": "navierboat.com"},
          "investors": {}, "count": 2, "collisions": COLLISIONS}
    h = w.holding(name="Apex", website="https://www.apexhq.ai/")
    h["_domain_only"] = True
    check(w.resolve_known(h, db), (None, ""), "a slug-named page never matches by name")
    check(w.resolve_known(w.holding(name="Navier AI"), db), (None, ""), "collision file vetoes the stem")
    check(w.resolve_known(w.holding(name="Navier"), db), ("Navier", "exact-name"), "plain name still matches")
    check(w.possible_matches(w.holding(name="Navier AI"), db), [], "no 'maybe already tracked' hint either")


if __name__ == "__main__":
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}: {e}")
        except Exception as e:                                # noqa: BLE001
            failed += 1
            print(f"ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
