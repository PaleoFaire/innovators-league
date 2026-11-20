#!/usr/bin/env python3
"""
Tests for the jobs board's family layer in scripts/enrich_jobs.py: plain role
types, places for "search near home", the no-degree signal, and the employer
card.

    python3 -m unittest scripts/tests/test_jobs_family.py
    python3 scripts/tests/test_jobs_family.py

Offline, standard library only; nothing is written to data/. The cases in
jobs_family_cases.json are shared with test_jobs_family.js so the page and
the pipeline cannot drift apart on place names, distances or ZIP decoding.
"""

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_geo_places as G  # noqa: E402
import enrich_jobs as E       # noqa: E402

CASES = json.loads((Path(__file__).resolve().parent / "jobs_family_cases.json").read_text(encoding="utf-8"))


def types_of(title):
    family = E.role_family(title)
    level = E.job_level(title)
    return E.role_types(title, family, level)


class PlainRoleTypes(unittest.TestCase):
    CASES = [
        # hands-on: a trade in the title
        ("Welder", ["hands"]),
        ("CNC Machinist (2nd Shift)", ["hands"]),
        ("Machine Operator", ["hands"]),
        ("Electrician", ["hands"]),
        ("Quality Inspector", ["hands"]),
        ("Warehouse Associate", ["hands"]),
        ("Field Service Technician", ["hands"]),
        ("Avionics Technician", ["hands"]),
        ("Production Supervisor", ["hands"]),
        ("Production Coordinator, Core Tech", ["hands"]),
        # ... unless the title says engineer, manager or principal
        ("Sr. Welding Engineer", ["engineering"]),
        ("Manufacturing Engineer II", ["engineering"]),
        ("Manager, Starship Build", ["business"]),
        ("Senior Principal Technologist – Memory", ["engineering"]),
        # a bare "tech" is not a trade
        ("Tech Lead Manager, Backend", ["engineering"]),
        ("American Tech Fellowship", []),
        # engineering
        ("GNC Engineer II", ["engineering"]),
        ("Test Engineer", ["engineering"]),
        ("Avionics Engineer (All Levels)", ["engineering"]),
        ("Senior RF Front-End Design Engineer", ["engineering"]),
        ("Senior Supplier Development Engineer", ["engineering"]),
        ("Forward Deployed Engineer", ["engineering"]),
        ("Engineering Manager, Avionics", ["engineering"]),
        ("Chief Engineer", ["engineering"]),
        ("Analytical Chemist", ["engineering"]),
        ("Engineer", ["engineering"]),
        # software, data and IT
        ("Software Engineer, Propulsion Simulation", ["software"]),
        ("Staff Software Engineer, Driver Validation", ["software"]),
        ("Data Scientist", ["software"]),
        ("IT Helpdesk Technician", ["software"]),
        # business and operations
        ("Account Executive", ["business"]),
        ("Sales Engineer", ["business"]),
        ("Senior Technical Recruiter - Hardware Engineering", ["business"]),
        ("Technical Program Manager", ["business"]),
        ("Trade Analyst", ["business"]),
        ("EHS Manager", ["business"]),
        ("Deployment Strategist", ["business"]),
        # internships and first jobs cut across the kinds of work
        ("Apprentice Welder", ["hands", "early"]),
        ("Assembly Technician, New Grad", ["hands", "early"]),
        ("Mechanical Engineering Intern", ["engineering", "early"]),
        ("Nuclear Engineer (New Grad)", ["engineering", "early"]),
        ("Flight Software Engineer I", ["software", "early"]),
        ("Supply Chain Intern (Summer 2027)", ["business", "early"]),
        ("Junior Accountant", ["business", "early"]),
        # nothing to sort
        ("General Application", []),
    ]

    def test_titles(self):
        for title, want in self.CASES:
            self.assertEqual(types_of(title), want, title)

    def test_at_most_one_kind_of_work(self):
        kinds = {"hands", "engineering", "software", "business"}
        for title, _ in self.CASES:
            self.assertLessEqual(len(kinds & set(types_of(title))), 1, title)

    def test_mask_bits(self):
        bits = list(E.ROLE_TYPE_BITS.values())
        self.assertEqual(bits, [1, 2, 4, 8, 16])
        self.assertEqual(list(E.ROLE_TYPE_BITS), list(E.ROLE_TYPES))
        self.assertNotIn(E.ENTRY_LEVEL_BIT, bits)
        self.assertEqual(E.role_type_mask(["hands", "early"], "intern"), 1 | 16, "an apprentice is early but not a regular entry-level job")
        self.assertEqual(E.role_type_mask(["hands", "early"], "junior"), 1 | 16 | E.ENTRY_LEVEL_BIT)
        self.assertEqual(E.role_type_mask(["engineering"], "senior"), 2)
        self.assertEqual(E.role_type_mask([], "mid"), 0)

    def test_every_family_has_a_rule(self):
        for family in E.FAMILIES:
            if family in ("general", "other"):
                self.assertNotIn(family, E.WORK_TYPE_BY_FAMILY)
            else:
                self.assertIn(E.WORK_TYPE_BY_FAMILY.get(family), ("hands", "engineering", "software", "business"), family)
        self.assertTrue(set(E.EARLY_LEVELS) <= set(E.LEVELS))
        self.assertTrue(set(E.ENTRY_LEVELS) <= set(E.EARLY_LEVELS))

    def test_labels_are_plain(self):
        self.assertEqual([label for label, _ in E.ROLE_TYPES.values()],
                         ["Hands-on", "Engineering", "Software", "Business and operations", "Internships and first jobs"])
        for label, about in E.ROLE_TYPES.values():
            self.assertTrue(about.endswith("."), label)
            self.assertLess(len(about), 110, label)


class PlaceNames(unittest.TestCase):
    def test_norm_place(self):
        for raw, want in CASES["normPlace"]:
            self.assertEqual(E.norm_place(raw), want, raw)

    def test_state_code(self):
        for raw, want in CASES["stateCode"]:
            self.assertEqual(E.state_code(raw), want, raw)

    def test_distance(self):
        for case in CASES["distanceMiles"]:
            got = E.haversine_miles(case["from"][0], case["from"][1], case["to"][0], case["to"][1])
            self.assertAlmostEqual(got, case["miles"], places=2, msg=case["why"])

    def test_zip_fixture_is_what_the_builder_packs(self):
        for code, want in CASES["zips"]["lookups"]:
            got = G.unpack_zip(CASES["zips"]["packed"], code)
            self.assertEqual(list(got) if got else None, want, code)

    def test_hub_tables_cover_the_hub_rules(self):
        self.assertEqual(list(E.HUB_ANCHORS), list(E.METRO_RULES))
        self.assertEqual(sorted(E.METRO_STATES), sorted(E.METRO_RULES))
        for town, state in E.HUB_ANCHORS.values():
            self.assertIn(state, E.US_STATE_CODES, town)


def small_geo():
    """A places file with a handful of towns, built the way the real one is."""
    towns = [("Costa Mesa", "CA", 33.664, -117.903), ("Hawthorne", "CA", 33.916, -118.352), ("San Francisco", "CA", 37.775, -122.419),
             ("San Jose", "CA", 37.338, -121.886), ("Sunnyvale", "CA", 37.369, -122.036), ("Oakland", "CA", 37.804, -122.271),
             ("Ontario", "CA", 34.063, -117.651), ("Los Angeles", "CA", 34.052, -118.244), ("Washington", "DC", 38.895, -77.037),
             ("Cambridge", "MA", 42.373, -71.110), ("New York", "NY", 40.713, -74.006), ("Portland", "OR", 45.515, -122.678),
             ("Salem", "OR", 44.943, -123.035), ("Pittsburgh", "PA", 40.441, -79.996), ("Austin", "TX", 30.267, -97.743),
             ("Dallas", "TX", 32.777, -96.797), ("Paris", "TX", 33.661, -95.556), ("Seattle", "WA", 47.606, -122.332),
             ("Vancouver", "WA", 45.626, -122.675), ("Chicago", "IL", 41.878, -87.630), ("St. Louis", "MO", 38.627, -90.199)]
    repo = {E.place_key(n, s): (n, s, lat, lng) for n, s, lat, lng in towns}
    with tempfile.TemporaryDirectory() as empty:
        return E.GeoPlaces(json.loads(G.render(G.build(empty, repo=repo))))


class JobPlaces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geo = small_geo()

    def places(self, location, hq=None, metros=None):
        metros = E.job_metros(location, False) if metros is None else metros
        out = []
        for i, approx in E.job_places(location, metros, hq, self.geo):
            name, state = self.geo.rows[i][0], self.geo.rows[i][1]
            out.append("%s, %s%s" % (name, state, "~" if approx else ""))
        return out

    def test_town_and_state(self):
        for location, want in [
            ("Hawthorne, CA", ["Hawthorne, CA"]),
            ("Costa Mesa, California, United States", ["Costa Mesa, CA"]),
            ("San Francisco, CA - US", ["San Francisco, CA"]),
            ("Hybrid (Oakland, California, US)", ["Oakland, CA"]),
            ("US - Austin, TX", ["Austin, TX"]),
            ("Hybrid: New York, NY", ["New York, NY"]),
            ("Washington, D.C.", ["Washington, DC"]),
            ("Washington, District of Columbia, United States", ["Washington, DC"]),
            ("New York, New York, United States", ["New York, NY"]),
            ("Saint Louis, Missouri", ["St. Louis, MO"]),
            ("Austin TX", ["Austin, TX"]),
            ("Ontario, CA", ["Ontario, CA"]),
            ("Paris, TX", ["Paris, TX"]),
            ("Vancouver, WA", ["Vancouver, WA"]),
        ]:
            self.assertEqual(self.places(location), want, location)

    def test_several_places(self):
        for location, want in [
            ("San Francisco, CA | New York City, NY", ["San Francisco, CA", "New York, NY"]),
            ("Seattle, WA; Austin, TX", ["Seattle, WA", "Austin, TX"]),
            ("Remote, US, Chicago, IL, USA, Austin, TX, USA", ["Chicago, IL", "Austin, TX"]),
            # Oregon's code is not the word "or"; an upper-case OR between places is
            ("Salem, OR, or Pittsburgh, PA", ["Salem, OR", "Pittsburgh, PA"]),
            ("Portland, OR", ["Portland, OR"]),
            ("San Francisco, Bay Area OR Pittsburgh, PA OR Austin, TX", ["San Francisco, CA", "Pittsburgh, PA", "Austin, TX"]),
        ]:
            self.assertEqual(self.places(location), want, location)

    def test_areas_are_marked_approximate(self):
        for location, want in [
            ("Greater Seattle Area", ["Seattle, WA~"]),
            ("Bay Area", ["San Francisco, CA~"]),
            ("San Francisco Bay Area", ["San Francisco, CA~"]),
            ("Los Angeles - Greater Area", ["Los Angeles, CA~"]),
            ("Washington, DC Metro Area", ["Washington, DC~"]),
            ("Dallas-Fort Worth, Texas, USA", ["Dallas, TX~"]),
        ]:
            self.assertEqual(self.places(location), want, location)

    def test_bare_names_need_something_to_settle_the_state(self):
        self.assertEqual(self.places("Sunnyvale"), ["Sunnyvale, CA"], "the Bay Area hub rule matched, so it is California")
        self.assertEqual(self.places("Sunnyvale", metros=[]), [], "no hub, no state: no guess")
        self.assertEqual(self.places("New York"), ["New York, NY"])
        self.assertEqual(self.places("NYC"), ["New York, NY"])
        self.assertEqual(self.places("Chicago"), ["Chicago, IL"], "BARE_CITY_STATE")
        self.assertEqual(self.places("Cambridge (Hybrid)"), [], "Massachusetts or England?")
        self.assertEqual(self.places("Cambridge (Hybrid)", hq=("Cambridge", "MA")), ["Cambridge, MA"], "the company's own home town")
        self.assertEqual(self.places("Portland"), [], "Oregon or Maine?")
        self.assertEqual(self.places("Salem"), [])

    def test_abroad_is_never_placed_in_the_united_states(self):
        for location in ["Paris", "Paris, France", "London, UK", "Toronto, Ontario, CA", "Vancouver, British Columbia, Canada",
                         "Cambridge, United Kingdom", "San Jose, Costa Rica", "Sydney, New South Wales, Australia",
                         "Burnaby, British Columbia, CA", "Munich, Bavaria, Germany"]:
            self.assertEqual(self.places(location), [], location)

    def test_no_town_named(self):
        for location in ["Remote", "United States", "US Remote", "Remote - TX", "California", "Texas", "Orange County", "", "TBD"]:
            self.assertEqual(self.places(location), [], location)

    def test_unknown_town_is_not_guessed(self):
        self.assertEqual(self.places("Weirton, WV"), [])
        self.assertEqual(self.places("Santa Ana, California, United States"), [])

    def test_unspecified_location_uses_the_company_home(self):
        self.assertEqual(self.places("HQ", hq=("Costa Mesa", "CA")), ["Costa Mesa, CA"])
        self.assertEqual(self.places("", hq=("Costa Mesa", "CA")), ["Costa Mesa, CA"])
        self.assertEqual(self.places("HQ", hq=None), [])
        self.assertEqual(self.places("HQ", hq=("Nowhere", "ZZ")), [])

    def test_town_wins_over_area_and_the_list_is_capped(self):
        self.assertEqual(self.places("Seattle, WA; Greater Seattle Area"), ["Seattle, WA"])
        many = "; ".join("%s, %s" % (r[0], r[1]) for r in self.geo.rows)
        self.assertEqual(len(self.places(many)), E.PLACES_PER_POSTING)

    def test_missing_places_file_means_no_places(self):
        empty = E.load_geo_places("/nonexistent/us_places.json")
        self.assertEqual(empty.rows, [])
        self.assertEqual(E.job_places("Hawthorne, CA", ["la"], None, empty), [])

    def test_repo_file_loads(self):
        geo = E.load_geo_places()
        self.assertGreater(len(geo.rows), 100)
        i = geo.find("Costa Mesa", "CA")
        self.assertIsNotNone(i)
        self.assertLess(E.haversine_miles(geo.rows[i][2], geo.rows[i][3], 33.66, -117.91), 5)


class NoDegreeSignal(unittest.TestCase):
    YES = [
        "Basic qualifications: High school diploma or equivalency certificate. 1+ years of experience with hand tools.",
        "Education: High School Diploma/GED required. Associate's degree or trade certification preferred.",
        "No degree required. We care about what you can build.",
        "A college degree is not required for this role.",
        "We do not require a degree; show us your work.",
        "This role doesn't require a college degree.",
        "Bachelor’s degree preferred but not required.",
        "GED or equivalent and a valid driver's license.",
        "High school diploma and 4+ years of professional experience, or a bachelor's degree in an engineering discipline.",
    ]
    NO = [
        "",
        "Bachelor's degree in mechanical engineering required.",
        "Requires a bachelor's degree in an engineering discipline and 5+ years of experience.",
        "BS in Electrical Engineering is required; MS preferred.",
        "Bachelor's degree or equivalent practical experience.",              # too loose to call "no degree"
        "High school diploma required for Technician I. A bachelor's degree in engineering is required for Engineer I.",
        "Must have a Master's degree in a STEM field. No exceptions.",
        "We mentor local high school students every summer.",
        "PhD required. A degree of autonomy is not required at first.",
        "Six degrees of freedom robot arm experience.",
    ]

    def test_yes(self):
        for text in self.YES:
            self.assertTrue(E.no_degree_likely(text), text)

    def test_no(self):
        for text in self.NO:
            self.assertFalse(E.no_degree_likely(text), text)

    def test_signal_flag_and_cache_rule(self):
        self.assertEqual(E._signal_flags("High school diploma or GED required.") & 4, 4)
        self.assertEqual(E._signal_flags("Must hold an active TS/SCI clearance. U.S. citizen. High school diploma."), 1 | 2 | 4)
        self.assertEqual(E._signal_flags("Bachelor's degree required."), 0)
        # a board cached before the rule existed is read again; one read under it is not
        self.assertTrue(E.board_needs_fetch({"ids": "abc", "n": 3}, "abc"))
        self.assertFalse(E.board_needs_fetch({"ids": "abc", "n": 3, "sig": E.SIGNAL_RULES_VERSION}, "abc"))
        self.assertTrue(E.board_needs_fetch({"ids": "abc", "n": 3, "sig": E.SIGNAL_RULES_VERSION}, "changed"))
        self.assertTrue(E.board_needs_fetch(None, "abc"))

    def test_extraction_writes_the_flag(self):
        board = {"jobs": [{"id": 1, "content": "<p>High school diploma or GED.</p>", "updated_at": "2026-11-01"},
                          {"id": 2, "content": "<p>Bachelor&#39;s degree in physics required.</p>", "updated_at": "2026-11-01"}]}
        rows = E.extract_board_signals("gh", "acme", board, date(2026, 11, 20))
        self.assertEqual(rows["gh-acme-1"][0] & 4, 4)
        self.assertEqual(rows["gh-acme-2"][0] & 4, 0)


class EmployerCard(unittest.TestCase):
    def test_one_line(self):
        for text, want in [
            ("The Bot Company is building a household robot to automate chores. Per Reuters, it is not a humanoid.",
             "The Bot Company is building a household robot to automate chores."),
            ("Crystal-sulfur cathode lithium batteries targeting 3x energy density — €25M+ raised.",
             "Crystal-sulfur cathode lithium batteries targeting 3x energy density."),
            ("End-to-end additive manufacturing for automotive, aerospace and defense. $290M Series E at $2.3B valuation (Sep 2025).",
             "End-to-end additive manufacturing for automotive, aerospace and defense."),
            ("Industrial robots and Agile ONE humanoid (launched November 2025) — DLR spinout, unicorn valuation.",
             "Industrial robots and Agile ONE humanoid (launched November 2025)."),
            ("Builds parts for U.S. Navy ships. Founded in 2020.", "Builds parts for U.S. Navy ships."),
            # nothing plain to say: the card shows the field alone
            ("The defining space company of the generation. 165 launches in 2025.", ""),
            ("World's most mature autonomous delivery system.", ""),
            ("Leading AI company for geothermal discovery. Uses a proprietary platform.", ""),
            ("Emerged from stealth with $250M raised and launched the Matter Compiler.", ""),
            ("", ""),
        ]:
            self.assertEqual(E.one_line(text), want, text)

    def test_one_line_is_cut_at_a_word(self):
        text = "Builds " + " ".join(["actuators"] * 40) + "."
        got = E.one_line(text)
        self.assertLessEqual(len(got), E.ABOUT_MAX + 1)
        self.assertTrue(got.endswith("actuators…"), got)

    def test_no_claim_survives(self):
        db, _, _ = E.load_database()
        for name, rec in db.items():
            line = E.one_line(rec["description"])
            self.assertIsNone(E.SKIP_WORDING.search(line), "%s: %s" % (name, line))
            self.assertLessEqual(len(line), E.ABOUT_MAX + 1, name)

    def test_backers(self):
        got = E.clean_backers(["Sequoia Capital (Andrew Reed)", "Accel (co-led Series B)", "Undisclosed", "accel", "", "SV Angel",
                               "8VC", "Lux Capital", "Founders Fund"])
        self.assertEqual(got, (["Sequoia Capital", "Accel", "SV Angel", "8VC", "Lux Capital"], 6))
        self.assertEqual(E.clean_backers([]), ([], 0))
        self.assertEqual(E.clean_backers(["Undisclosed"]), ([], 0))
        # the site's publisher is never shown as a backer
        self.assertEqual(E.clean_backers(["Rational Optimist Society", "The Innovators League", "DCVC"]), (["DCVC"], 1))

    def test_no_card_names_the_publisher(self):
        db, _, tracker = E.load_database()
        names = [n for rec in db.values() for n in E.clean_backers(rec["investors"], shown=999)[0]]
        names += [n for t in tracker for n in E.clean_backers(t["leads"], shown=999)[0]]
        self.assertGreater(len(names), 1000)
        for n in names:
            self.assertIsNone(E.SITE_OWN_NAMES.search(n), n)

    SNAPS = [
        (date(2026, 7, 31), {"Acme": 40, "Gone": 9}),
        (date(2026, 8, 31), {"Acme": 50, "Flat": 12, "Moved": 30, "Held": 25}),
        (date(2026, 9, 30), {"Acme": 55, "Flat": 12, "New": 5, "Moved": 2, "Held": 26}),
        (date(2026, 11, 16), {"Acme": 80, "Flat": 12, "New": 9, "Moved": 2, "Held": 60}),
    ]
    HELD = {"Held": ["2026-10"]}

    def trend(self, company, today=date(2026, 11, 20)):
        return E.postings_trend(self.SNAPS, self.HELD, company, today)

    def test_trend_picks_the_count_nearest_90_days_back(self):
        t = self.trend("Acme")
        self.assertEqual((t["now"], t["nowDate"], t["then"], t["thenDate"]), (80, "2026-11-16", 50, "2026-08-31"))
        self.assertFalse(t["boardChanged"])
        self.assertEqual(t["since"], "2026-07-31")
        self.assertEqual(self.trend("Flat")["then"], 12)

    def test_trend_says_so_when_there_is_nothing_to_compare(self):
        t = self.trend("New")                 # first counted 47 days before the newest count: too recent
        self.assertEqual((t["now"], t["then"], t["thenDate"], t["since"]), (9, None, None, "2026-09-30"))
        self.assertIsNone(self.trend("Gone"), "not in the newest count")
        self.assertIsNone(self.trend("Never heard of it"))

    def test_a_changed_job_board_is_not_a_trend(self):
        self.assertTrue(self.trend("Moved")["boardChanged"], "30 postings to 2 is a changed board, as in calc_pulse.py")
        self.assertTrue(self.trend("Held")["boardChanged"], "the Pulse held it out in October")

    def test_stale_or_future_counts_are_not_now(self):
        self.assertIsNone(self.trend("Acme", today=date(2027, 2, 1)), "the newest count is too old to stand for now")
        t = self.trend("Acme", today=date(2026, 10, 5))        # the November count does not exist yet
        self.assertEqual((t["now"], t["nowDate"]), (55, "2026-09-30"))
        self.assertEqual((t["then"], t["thenDate"]), (40, "2026-07-31"))

    def test_compact_card(self):
        self.assertEqual(E.compact_card(None), 0)
        card = {"about": "Builds things.", "field": "Launch", "founded": 2017, "hq": "Costa Mesa, CA", "ticker": "",
                "lastRound": {"round": "Series C", "amount": "$375M", "month": "2026-11"}, "backers": ["A", "B"], "backersTotal": 7,
                "postings": {"now": 80, "nowDate": "2026-11-16", "then": 50, "thenDate": "2026-08-31", "since": "2026-07-31", "boardChanged": False}}
        row = E.compact_card(card)
        self.assertEqual(len(row), len(E.CARD_FIELDS))
        self.assertEqual(row, ["Builds things.", "Launch", 2017, "Costa Mesa, CA", "", ["Series C", "$375M", "2026-11"], ["A", "B"], 7,
                               [80, "2026-11-16", 50, "2026-08-31", 0]])
        card["lastRound"] = None
        card["postings"] = {"now": 9, "nowDate": "2026-11-16", "then": None, "thenDate": None, "since": "2026-09-30", "boardChanged": False}
        row = E.compact_card(card)
        self.assertEqual((row[5], row[8]), (0, [9, "2026-11-16", -1, "2026-09-30", 0]))
        card["postings"] = None
        self.assertEqual(E.compact_card(card)[8], 0)

    def test_list_field(self):
        rec = '{ name: "X", investors: ["Sequoia Capital (Andrew Reed)", "O\'Shaughnessy Ventures", \'Bay [Area] Fund\'], tags: ["a"] }'
        self.assertEqual(E._list_field(rec, "investors"), ["Sequoia Capital (Andrew Reed)", "O'Shaughnessy Ventures", "Bay [Area] Fund"])
        self.assertEqual(E._list_field(rec, "missing"), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
