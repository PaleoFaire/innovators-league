#!/usr/bin/env python3
"""
Regression tests for the deal-feed attribution guards in scripts/fetch_deals.py,
which scripts/fetch_funding_rss.py also uses.

    python3 scripts/tests/test_deal_matcher.py        # plain runner, exit 1 on failure
    python3 -m pytest scripts/tests                    # also works where pytest exists

Offline. Reads the repo's own scripts/company_master_list.js, data.js and
data/name_collisions.json, so these tests check the live configuration, not a
copy of it. Two bad deals reached DEAL_TRACKER in the week of 1 Oct 2026:
Satlyt's $8M round credited to SpaceX, and the Dutch security firm Hadrian's
$40M round credited to the Torrance manufacturer. Both must stay out. The
later Oct 2026 cases came from running the matcher over 16,862 real headlines
after the master list grew to every data.js company.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fetch_deals as fd  # noqa: E402

fd.init_matcher()


def company(title, desc=""):
    return fd.match_company(title, desc)


def deal(title, desc=""):
    return fd.extract_deal_from_article({"title": title, "description": desc})


def check(got, want, what):
    assert got == want, f"{what}: got {got!r}, want {want!r}"


# ── the two bad deals ──────────────────────────────────────────────────────

def test_satlyt_round_is_not_spacex():
    t = "Satlyt, founded by a former Google and SpaceX product manager, raises $8M to run AI on satellites"
    check(company(t), None, t)
    check(deal(t), None, t)


def test_dutch_hadrian_is_not_ours():
    for t in ("Hadrian raises $40M to tackle AI-driven cyber threats",
              "Exclusive: Hadrian raises $40m as AI cyberattacks accelerate"):
        check(company(t), None, t)
        check(deal(t), None, t)
    # The summary alone can give the other Hadrian away.
    check(company("Hadrian raises $40M", "The Amsterdam pentesting startup will hire."), None,
          "Hadrian with a security summary")
    # Our Hadrian's own rounds still land, "national security" and all.
    d = deal("Hadrian raises $260M Series C to build factories for national security")
    check(d and (d["company"], d["amount"], d["round"]), ("Hadrian", "$260M", "Series C"), "real Hadrian round")


# ── attributions that must survive ────────────────────────────────────────

def test_neros_series_c_at_a_valuation():
    t = "Neros raises $250M Series C at $2.5B valuation"
    check(company(t), "Neros", t)
    d = deal(t)
    # The valuation used to veto the round figure too, so no deal was made.
    check(d and (d["company"], d["amount"], d["round"]), ("Neros", "$250M", "Series C"), t)


def test_saronic_technologies():
    t = "Saronic Technologies raises $600M"
    check(company(t), "Saronic", t)
    check((deal(t) or {}).get("company"), "Saronic", t)


def test_monumental_labs_is_its_own_record():
    t = "Monumental Labs raises $25M"
    check(company(t), "Monumental Labs", t)
    check((deal(t) or {}).get("company"), "Monumental Labs", t)
    check(company("Monumental raises $25M to build bricklaying robots"), "Monumental", "plain Monumental")


def test_navier_ai_is_not_navier():
    t = "Navier AI raises $5M"
    check(company(t), None, t)
    check(deal(t), None, t)
    check(company("Navier raises $7M for electric hydrofoil boats"), "Navier", "plain Navier")


def test_known_different_companies_never_match_ours():
    pairs = {
        "Atmos Thermal raises $4M": "Atmos Space Cargo",
        "Manifold Industries raises $6M": "Manifold Bio",
        "Edgerun raises $3M": "EdgeRunner AI",
        "Arxlight raises $9M": "xLight",
        "American Terawatt raises $30M": "TeraWatt Technology",
        "Inversion Semiconductor raises $10M": "Inversion Space",
        "Bedrock Ocean Exploration raises $10M": "Bedrock Robotics",
        "Parallel Bio raises $21M Series A": "Parallel Systems",
        "Parallel raises $100M to build web search for AI agents": "Parallel Systems",
    }
    for t, wrong in pairs.items():
        got = company(t)
        assert got != wrong, f"{t}: credited to {wrong}"
        assert (deal(t) or {}).get("company") != wrong, f"{t}: deal credited to {wrong}"


def test_bedrock_ocean_exploration_goes_to_the_ocean_company():
    # data.js holds bedrockocean.com twice since 7 Oct 2026 ("Bedrock Ocean"
    # and "Bedrock Ocean Exploration"); either record is right, Robotics is not.
    t = "Bedrock Ocean Exploration raises $10M"
    assert company(t) in ("Bedrock Ocean", "Bedrock Ocean Exploration"), company(t)


def test_exact_db_name_beats_a_master_list_alias():
    # The master list's "Twelve Labs" (video AI, not in data.js) owns the
    # alias "twelve"; the data.js company named exactly "Twelve" must win.
    check(company("Twelve raises $83M to turn CO2 into jet fuel"), "Twelve", "Twelve")
    check(company("Twelve Labs raises $50M"), "Twelve Labs", "Twelve Labs")


# ── context grammar ───────────────────────────────────────────────────────

def test_coordinated_context_markers():
    for t in ("ex-Google, SpaceX engineers raise $10M for orbital compute",
              "Former Google and SpaceX engineers raise $10M",
              "Former Google And SpaceX Engineers Raise $10M",
              "SpaceX and Google alumni raise $10M",
              "Google/SpaceX veterans raise $10M",
              "A former Meta, Google and SpaceX engineer raises $5M",
              "SpaceX engineers raise $10M for a new launch startup",
              "Startup from Founders Fund and SpaceX raises $12M"):
        check(company(t), None, t)


def test_appositive_and_parenthetical_names_are_context():
    for t in ("Satlyt, a SpaceX spinout, raises $8M",
              "Satlyt, whose CEO built Starlink at SpaceX, raises $8M",
              "Satlyt (backed by SpaceX) raises $8M",
              "Satlyt (a SpaceX supplier) raises $8M"):
        check(company(t), None, t)


def test_subjects_around_commas_still_match():
    for t in ("Neros, the Anduril rival, raises $250M Series C",
              "After a record year, Neros, the drone maker, raises $250M Series C",
              "Backed by Founders Fund, Neros raises $250M Series C",
              "Grown from scratch, Neros raises $250M Series C"):
        check(company(t), "Neros", t)


# ── data.js guards ─────────────────────────────────────────────────────────

def test_status_guard_blocks_listed_company():
    t = "SpaceX raises $2B in new funding round"
    check(company(t), "SpaceX", "match itself is fine")
    check(deal(t), None, "SpaceX is status ipo in data.js")
    assert any(s["company"] == "SpaceX" and "ipo" in s["reason"] for s in fd.SKIPPED), "skip not logged"


def test_magnitude_guard_on_unlabelled_round():
    check(deal("Hadrian raises $40M"), None, "$40M unlabelled vs $1.7B+ raised")
    assert any(s["company"] == "Hadrian" and "under 5%" in s["reason"] for s in fd.SKIPPED), "skip not logged"


def test_guards_on_fixture_record():
    saved = dict(fd.COMPANY_ALIASES), dict(fd.DB_COMPANIES), dict(fd._DB_BY_KEY)
    try:
        fd.COMPANY_ALIASES["zyxwv robotics"] = "Zyxwv Robotics"
        fd.DB_COMPANIES["Zyxwv Robotics"] = {"status": "acquired", "raised": "$500M", "raised_m": 500.0}
        fd._DB_BY_KEY["zyxwvrobotics"] = "Zyxwv Robotics"
        check(deal("Zyxwv Robotics raises $50M Series B"), None, "acquired")
        fd.DB_COMPANIES["Zyxwv Robotics"]["status"] = "dead"
        check(deal("Zyxwv Robotics raises $50M Series B"), None, "dead")
        fd.DB_COMPANIES["Zyxwv Robotics"]["status"] = "active"
        check(deal("Zyxwv Robotics raises $20M"), None, "4% of totalRaised, unlabelled")
        check((deal("Zyxwv Robotics raises $20M Series B") or {}).get("company"), "Zyxwv Robotics",
              "a labelled round is never size-checked")
        check((deal("Zyxwv Robotics raises $30M") or {}).get("company"), "Zyxwv Robotics", "6% passes")
        fd.DB_COMPANIES["Zyxwv Robotics"]["raised_m"] = None
        check((deal("Zyxwv Robotics raises $1M") or {}).get("company"), "Zyxwv Robotics",
              "undisclosed totalRaised disables the size check")
    finally:
        fd.COMPANY_ALIASES, fd.DB_COMPANIES, fd._DB_BY_KEY = saved


def test_money_parser():
    for s, want in (("$1.7B+", 1700.0), ("~$110-111M", 110.0), ("€30M", 30.0), ("$500K", 0.5),
                    ("₹9 Cr (~$9M)", 9.0), ("C$12M (~US$9M)", 12.0), ("$250M", 250.0),
                    ("Undisclosed", None), ("", None), ("IPO", None)):
        check(fd._money_millions(s), want, s)


def test_missing_inputs_disable_guards_not_the_feed():
    check(fd.load_db_companies("/nonexistent/data.js"), {}, "missing data.js")
    check(fd.load_name_collisions("/nonexistent/name_collisions.json"), ({}, {}), "missing collisions file")


# ── behaviour documented before Oct 2026 ─────────────────────────────────

def test_documented_matcher_cases():
    for t in ("ex-Palantir founders raise $22M",          # not a Palantir Series A
              "Palantir-backed Foo raises $10M",
              "A rival to Anduril raises $10M",
              "An invention startup raises $5M",          # not Vention
              "Researchers discover a way to cool chips as Foo raises $5M",   # not Cover
              "Mara Kamara's startup raises $3M",         # not Mara
              "No matter what, Foo raises $5M",           # not Matter
              "Matter of time: Foo raises $14M",
              "a shipbuilding startup raises $600M"):     # a topic alias, not Saronic
        check(company(t), None, t)
    for t in ("Is Neko Health's body scan worth it?", "Peak XV ups Surge seed ceiling to $5M"):
        check(deal(t), None, t)


def test_amount_parser():
    check(fd.parse_funding_amount("Durin raises $12 million to automate drilling, targeting the "
                                  "$12 billion drilling market"), "$12M", "market size")
    check(fd.parse_funding_amount("Neros raises $250M Series C at $2.5B valuation"), "$250M", "valuation")
    check(fd.parse_funding_amount("Foo, valued at $1B, raises $50M"), "$50M", "valuation first")
    check(fd.parse_funding_amount("Foo raises $40M at a $400M post-money valuation"), "$40M", "post-money")
    check(fd.parse_funding_amount("the $12 billion drilling market"), None, "market only")
    # Both ends of a range keep the word that disqualifies them.
    check(fd.parse_funding_amount("Foo raises funding for the $5B-$10B market"), None, "range is a market")
    check(fd.parse_funding_amount("Foo raises $20M to chase the $5B to $10B market"), "$20M", "round before range")


def test_round_and_investor_parsers():
    check(fd.parse_round_type("Foo closed a series of funding rounds"), "Funding Round", "series of")
    check(fd.parse_round_type("Foo raises $5M in a round led by NEA"), "Funding Round", "a round")
    check(fd.match_investors("nearly beneath the linear accelerator"), [], "NEA/Accel inside words")


def test_ipo_needs_listing_language():
    check(deal("Rebellions raises $3.4B in planned IPO"), None, "planned IPO")
    d = deal("Rebellions raises $250M in pre-IPO round")
    check(d and d["round"], "Pre-IPO", "pre-IPO round")


# ── Oct 2026: every data.js company in the master list ───────────────────

def test_master_list_covers_every_data_js_company():
    import sync_master_list as sm
    companies = sm.load_companies()
    _, entries = sm.parse_master(sm.MASTER.read_text(encoding="utf-8"))
    renames, new, _, _ = sm.plan(companies, entries, None, None, False)
    check((len(renames), [n for _, n, _ in new]), (0, []), "data.js companies missing from the master list")
    keys = [fd._db_key(n) for _, n, _ in entries]
    check(sorted({n for _, n, _ in entries if keys.count(fd._db_key(n)) > 1}), [], "duplicate master-list lines")
    # ...and nothing cut from the database came back with it.
    import json
    cut = {fd._squash(c["name"]) for c in json.loads(sm.ARCHIVE.read_text())["companies"]}
    back = [n for _, n, _ in entries if fd._squash(n) in cut]
    check(back, [], "cut companies in the master list")


def test_companies_added_in_the_sync_are_credited():
    for t, want in (("xLight raises $40M to build EUV lasers", "xLight"),
                    ("Arxlight raises $9M", "Arxlight"),
                    ("American Terawatt raises $52.6M to build a national HVDC network", "American Terawatt"),
                    ("Chip startup Efficient Computer raises $97 million at $650 million valuation",
                     "Efficient Computer"),
                    ("Callosum raises $100M in one of Europe's largest seed rounds", "Callosum")):
        check((deal(t) or {}).get("company"), want, t)
    # A one-word name only counts as written: "xlight" is not xLight, a bare number never matches.
    check(company("xlight raises $40M"), None, "lower-case xlight")
    check(company("Founded in 1872, Foo raises $10M"), None, "1872 is a year here")


def test_title_case_headlines():
    for t in ("Neros Raises $250M Series C At $2.5B Valuation",
              "Drone Maker Neros Raises $250M",
              "NEROS RAISES $250M SERIES C AT $2.5B VALUATION",
              "Defense-Manufacturing Startup Hadrian Raises $1.37B Series D at $7.87B Valuation"):
        assert company(t) in ("Neros", "Hadrian"), (t, company(t))
    d = deal("Neros Raises $250 Million Series C")
    check(d and (d["company"], d["amount"], d["round"]), ("Neros", "$250M", "Series C"), "'$250 Million'")
    # Title Case still keeps a longer proper noun whole.
    check(company("Mara Kamara's Startup Raises $3M"), None, "Title Case Mara Kamara")


def test_a_headline_opening_word_is_not_a_name():
    for t in ("Built for war, Foo raises $10M",
              "Built To Last: Foo Raises $10M",
              "Vast new fund raises $1B",
              "Twenty startups raise $1B"):
        check(company(t), None, t)
    for t, want in (("Built Robotics raises $64M", "Built Robotics"),
                    ("Vast raises $300M to build a space station", "Vast"),
                    ("Vast, the space-station startup, raises $300M", "Vast"),
                    ("Vast reportedly raises $300M for its space station", "Vast")):
        check(company(t), want, t)


def test_ordinary_word_names_need_a_names_position():
    for t in ("European Union raises €10B for defence",
              "Union AI raises $19M",                      # another company's suffix
              "Pacific Air raises fares",
              "Black Lives Matter foundation raised $90 million in 2020",
              "Kids’ Minds Matter raises more than $2.6 million at signature gala"):
        check(company(t), None, t)
    for t, want in (("Union raises $50M to build munitions factories", "Union"),
                    ("Korea's Rebellions raises $435M at $2.5B valuation", "Rebellions"),
                    ("U.K.-based Humanoid secures $152M in Series A funding", "Humanoid"),
                    ("Dutch Monumental raises $32m led by Khosla", "Monumental"),
                    ("Nuclear Startup Radiant Raises $300 Million for Small Reactors", "Radiant")):
        check(company(t), want, t)


def test_names_inside_other_names():
    for t in ("Material Bank raises $175 million",                         # "Bank" is not the verb
              "The Latest Hot Marketplace, Material Bank, Raises $100 Million",
              "Kestrel Land Trust raising $5 million to conserve 5,000 acres",
              "Ocius-X raises $12.5 million to bring fiber to the US",      # hyphenated
              "UpLift Raises $8M in Funding to Integrate Psychiatry",        # another brand's casing
              "Grove Collaborative raises $125M to launch new brands"):
        check(company(t), None, t)
    check(company("Collaborative Robotics Locks Up $100M, Latest Robot Startup To Raise Big"),
          "Collaborative Robotics", "'locks up' is a funding verb")


def test_scene_setting_and_roundups():
    for t in ("After Skyroot's Big Win, Indian Space Startups Bag $871 Million Funding",
              "Fractile eyes $6.5b, Rivian's spinout raises $150m, and PE blazes into fire safety"):
        check(company(t), None, t)
    check(company("Google's AI weather forecaster, Cohere's search, and Tenstorrent raises $693 million"),
          "Tenstorrent", "the last item of a list is the subject")
    check(company("How satellite connectivity startup Skylo hooked backers such as Intel, BMW and Samsung "
                  "to raise $37 million"), "Skylo", "a list inside the name's own clause")


def test_context_guards_for_namesakes():
    for t in ("Stripe-backed blockchain startup Tempo raises $500 million",   # not_if
              "Halo raises $20m in funding to grow business",               # only_if: not about wafers
              "Multiply raises a $9.5M seed to improve B2B ads",
              "Privateer Holdings raises $100 million in biggest private cannabis round ever",
              "Electra raises $115M for hybrid-electric aircraft",
              "ASI startup raises $10M for superintelligence",
              "Impulse Dynamics raises $158M to commercialize heart failure device"):
        check(company(t), None, t)
    for t, want in (("Tempo raises $40M for thermal batteries", "Tempo"),
                    ("Halo raises $20M to scale laser wafering of silicon carbide", "Halo"),
                    ("Multiply Labs Raises $20M in Series A Funding", "Multiply Labs"),   # full name
                    ("Electra raises $186M to make clean iron", "Electra"),
                    ("US startup Impulse raises $300 million to enhance in-space mobility", "Impulse Space")):
        check(company(t), want, t)


def test_former_names_and_acronyms():
    for t, want in (("Aetherflux raises $50M", "Cowboy Space Corporation"),
                    ("Air Space Intelligence raises $34M", "ASI"),
                    ("Terrahaptix raises $12M", "Terra Industries"),
                    ("H2Ok Innovations raises $12 million Series A", "Laminar")):
        check(company(t), want, t)


def test_an_alias_two_companies_list_names_neither():
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write('const MASTER_COMPANY_LIST = [\n'
                '  { name: "Zyxwv Space", aliases: ["Zyxwv"], sector: "space", ticker: null },\n'
                '  { name: "Zyxwv Labs", aliases: ["Zyxwv"], sector: "climate", ticker: null },\n'
                '  { name: "Qwert", aliases: [], sector: "space", ticker: null },\n'
                '  { name: "Qwert Robotics", aliases: ["Qwert"], sector: "robotics", ticker: null },\n'
                '];\n')
    aliases = fd.load_company_aliases(master_path=f.name)
    Path(f.name).unlink()
    assert "zyxwv" not in aliases, aliases
    check(aliases.get("qwert"), "Qwert", "a company's own name beats another's alias")


# ── fetch_funding_rss.py: the same matcher ─────────────────────────────────

def test_funding_rss_uses_the_deal_matcher():
    import fetch_funding_rss as fr

    def rss(title, desc=""):
        return fr.extract_deal({"title": title, "description": desc, "pubDate": "Tue, 07 Oct 2026 10:00:00 GMT",
                                "link": "https://example.com/a", "source": "Test"})

    # Credited by the old substring matcher to SpaceX, OpenAI and Conductor Quantum.
    check(rss("A SpaceX vet raised $65M to pull wire harnesses out of the Cold War era"), None, "SpaceX vet")
    check(rss("Satlyt, founded by a former Google and SpaceX product manager, raises $8M"), None, "Satlyt")
    d = rss("OpenAI-backed biotech firm Chai Discovery raises $130M Series B at $1.3B valuation")
    check(d and (d["company"], d["amount"], d["round"]), ("Chai Discovery", "$130M", "Series B"), "OpenAI-backed")
    d = rss("xLight Raises $40 Million Series B to Revolutionize Semiconductor Manufacturing")
    check(d and (d["company"], d["amount"]), ("xLight", "$40M"), "xLight, not Conductor Quantum")
    # Its old amount parser took the first figure: the market, not the round.
    check((rss("Durin raises $12 million to automate drilling, targeting the $12 billion drilling market")
           or {}).get("amount"), "$12M", "market size")
    check(rss("Hadrian raises $40M to tackle AI-driven cyber threats"), None, "Dutch Hadrian")
    # The output keeps the fields sync_weekly_metrics.py and the daily digest read.
    d = rss("Neros raises $250M Series C at $2.5B valuation")
    check(sorted(d), sorted(["company", "amount", "round", "investors", "date", "source", "url",
                             "headline", "fetched_at"]), "fields")
    check((d["date"], d["url"], d["source"]), ("2026-10-07", "https://example.com/a", "Test"), "date and link")


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
