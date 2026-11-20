#!/usr/bin/env python3
"""
Offline tests for scripts/build_lagebild.py (The Build-Out, Live).

    python3 -m unittest scripts/tests/test_lagebild.py
    python3 scripts/tests/test_lagebild.py

No network and no Node. Most tests build a small made-up repo in a temporary folder: a
data.js with six invented companies and one data file per source, each row written to hit
one rule of the method. One test at the end runs the real repo's data through the same
invariants.
"""
import io
import json
import sys
import tempfile
import unittest
from datetime import date
from unittest import mock
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_lagebild as lb  # noqa: E402

TODAY = date(2026, 11, 20)
MARKER = "SECRET-MARKER-DO-NOT-PUBLISH"

DATA_JS = r'''
// Made-up companies for the tests. Nothing here is real.
const LAST_UPDATED = "2026-11-19";
const SECTORS = { "Space & Aerospace": { color: "#fff", icon: "x" } };
const COMPANIES = [
  // a comment between entries
  {
    name: "Acme Robotics",
    status: "active",
    sector: "Robotics & Manufacturing",
    description: "Builds \"robots\" — fast. It's a test.",
    location: "Hawthorne, CA",
    country: "United States",
    state: "CA",
    lat: 33.9164,
    lng: -118.3526,
    founded: 2019,
    website: "https://www.acmerobotics.test",
    investors: ["Zed Capital", 'Quote\'s Fund'],
    keyPeople: [{ name: "Not A Company", role: "CEO" }],
    scores: { team: 9, tech: 8.5, },
  },
  { name: "Bolt Energy", status: "active", sector: "Climate & Energy", location: "Houston, TX", country: "United States", state: "TX", lat: 29.7587, lng: -95.3698, founded: 2015, website: "https://boltenergy.test/", formerNames: ["Volt Power"], },
  { name: "Northwind Fusion", status: "active", sector: "Nuclear Energy", location: "Calgary, Canada", country: "Canada", lat: 51.0447, lng: -114.0719, founded: 2018, website: "https://northwind.test" },
  { name: "Quiet Motors", status: "active", sector: "Transportation", location: "Detroit, MI", country: "United States", state: "MI", lat: 42.3314, lng: -83.0458, founded: 2020, website: "https://quietmotors.test" },
  { name: "Delta Foundry", status: "active", sector: "Robotics & Manufacturing", location: "Hawthorne, CA", country: "United States", state: "CA", lat: 33.9128, lng: -118.3426, founded: 2010, website: "https://deltafoundry.test" },
  { name: "Miami Marine", status: "active", sector: "Ocean & Maritime", location: "Miami, FL", country: "United States", state: "FL", lat: 25.7617, lng: -80.1918, founded: 2021, website: "https://miamimarine.test" }
];

const VC_FIRMS = [ { name: "Zed Capital" } ];
'''

ACME_SITE = "https://www.acmerobotics.test"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/1/000000012600000001/primary_doc.xml"


def announcements():
    return {"generated_at": "2026-11-19T16:00:00+00:00", "results": [
        {"company": "Acme Robotics", "website": ACME_SITE, "hits": [
            {"title": "Acme Robotics raises $240M Series C at a $3B valuation", "date": "Mon, 09 Nov 2026 00:00:00 GMT",
             "link": ACME_SITE + "/news/series-c", "round": "Series C", "amount": "$240M", "valuation": "$3B"},
            {"title": "We raised $240M to build more robots", "date": "Mon, 09 Nov 2026 00:00:00 GMT",
             "link": ACME_SITE + "/blog/we-raised", "round": "", "amount": "$240M", "valuation": ""},
            {"title": "Acme Robotics raises $240M, trade site says", "date": "Mon, 09 Nov 2026 10:00:00 GMT",
             "link": "https://tradepress.test/acme", "round": "", "amount": "$240M", "valuation": ""},
            {"title": "Acme Robotics to raise $500M Series D", "date": "Tue, 10 Nov 2026 00:00:00 GMT",
             "link": ACME_SITE + "/news/plan", "round": "Series D", "amount": "$500M", "valuation": ""},
            {"title": "", "date": "", "link": ACME_SITE + "/news", "round": "Series A", "amount": "$18M", "valuation": ""},
        ]},
        {"company": "Bolt Energy", "website": "https://boltenergy.test", "hits": [
            {"title": "Bolt Energy Secures $35 Million in Debt Financing", "date": "2026-10-21T00:00:00.000Z",
             "link": "https://boltenergy.test/news/debt", "round": "", "amount": "$35M", "valuation": ""},
            {"title": "Bolt Energy raises $50M Series B", "date": "Wed, 14 Oct 2026 16:59:58 GMT",
             "link": "https://boltenergy.test/news/b", "round": "Series B", "amount": "$50M", "valuation": ""},
            {"title": "Bolt Energy raises $20M seed round", "date": "Wed, 14 Oct 2026 16:59:58 GMT",
             "link": "https://boltenergy.test/news/seed", "round": "Seed", "amount": "$20M", "valuation": ""},
            {"title": "Bolt Energy raises $9M Series A", "date": "Tue, 01 Dec 2026 00:00:00 GMT",
             "link": "https://boltenergy.test/news/a", "round": "Series A", "amount": "$9M", "valuation": ""},
            {"title": "Bolt Energy raises $60M Series B", "date": "Thu, 01 Oct 2026 00:00:00 GMT",
             "link": "https://boltenergy.test/news/b2", "round": "Series B", "amount": "$16M", "valuation": ""},
        ]},
        {"company": "Northwind Fusion", "website": "https://northwind.test", "hits": [
            {"title": "Northwind Fusion raises $50M Series A", "date": "Mon, 02 Nov 2026 00:00:00 GMT",
             "link": "https://northwind.test/a", "round": "Series A", "amount": "$50M", "valuation": ""},
        ]},
        {"company": "Ghost Co", "website": "https://ghost.test", "hits": [
            {"title": "Ghost Co raises $5M", "date": "Mon, 02 Nov 2026 00:00:00 GMT",
             "link": "https://ghost.test/x", "round": "", "amount": "$5M", "valuation": ""},
        ]},
    ]}


def contracts():
    def row(company, award, amount, agency, sub, start, url=None):
        r = {"company": company, "awardId": award, "recipientName": company.upper(), "amount": amount,
             "agency": agency, "subAgency": sub, "awardType": None, "startDate": start, "endDate": "2027-12-31",
             "description": "PURCHASE OF THINGS"}
        if url:
            r["url"] = url
        return r
    link = "https://www.usaspending.gov/award/CONT_AWD_{}_7014_-NONE-_-NONE-"
    return [
        row("Acme Robotics", "A1", 362974500.0, "Department of Homeland Security", "U.S. Customs and Border Protection", "2026-11-16", link.format("A1")),
        row("Acme Robotics", "A2", 45205, "Department of the Interior", "Department of the Interior", "2026-11-18", link.format("A2")),
        row("Acme Robotics", "A0", 900000, "Department of Defense", "Department of the Army", "2025-06-01"),
        row("Acme Robotics", "A3", 0, "", "", "2026-08-25", link.format("A3")),
        row("Volt Power", "B1", 1273575, "National Aeronautics and Space Administration", "National Aeronautics and Space Administration", "2026-11-10"),
        row("Bolt Energy", "B1", 1273575, "National Aeronautics and Space Administration", "National Aeronautics and Space Administration", "2026-11-10"),
        row("Bolt Energy Inc", "B9", 5000, "Department of Energy", "Department of Energy", "2026-11-01", link.format("B9")),
        row("Bolt Energy", "B2", 700000, "Department of Energy", "Department of Energy", "2028-01-13", link.format("B2")),
        row("Bolt Energy", "B3", 5000000, "Department of Energy", "Department of Energy", "2026-09-01", link.format("B3")),
        row("Quiet Motors", "Q1", -5000, "Department of Energy", "Department of Energy", "2026-11-05", link.format("Q1")),
    ]


def signals_w44():
    return {"week": "2026-W44", "generated": "2026-11-01", "count": 12, "signals": [
        {"company": "Acme Robotics", "type": "hiring_surge", "evidence": {"roles_4w_ago": 33, "roles_now": 66, "change_pct": 100.0}},
        {"company": "Acme Robotics", "type": "new_location", "evidence": {"state": "FL", "state_name": "Florida", "postings_there": 2, "cities": ["Miami, FL"]}},
        {"company": "Acme Robotics", "type": "first_manufacturing_hire", "evidence": {"manufacturing_roles_now": 1, "roles_now": 66}},
        {"company": "Acme Robotics", "type": "senior_manufacturing_hire", "evidence": {"senior_roles_now": 2}},
        {"company": "Acme Robotics", "type": "production_turn", "evidence": {"atoms_share_now_pct": 66.7, "atoms_share_12w_ago_pct": 43.6, "roles_now": 66}},
        {"company": "Bolt Energy", "type": "hiring_surge", "evidence": {"roles_4w_ago": 10, "roles_now": 65, "change_pct": 550.0}},
        {"company": "Bolt Energy", "type": "production_turn", "evidence": {"atoms_share_now_pct": 72.9, "atoms_share_12w_ago_pct": 0.0, "roles_now": 177}},
        {"company": "Bolt Energy", "type": "new_location", "evidence": {"state": "OH", "state_name": "Ohio", "postings_there": 2, "cities": ["Ohio, OH"]}},
        {"company": "Quiet Motors", "type": "hiring_pullback", "evidence": {"roles_4w_ago": 40, "roles_now": 20, "change_pct": -50.0}},
        {"company": "Acme Robotics", "type": "board_check", "evidence": {"roles_4w_ago": 1, "roles_now": 30}},
        {"company": "Acme Robotics", "type": "runway_stress", "evidence": {"months": 3}},
        {"company": "Delta Foundry", "type": "hiring_surge", "evidence": {"roles_4w_ago": 20, "roles_now": 30, "change_pct": 50.0}},
    ]}


def signals_w45():
    return {"week": "2026-W45", "generated": "2026-11-02", "count": 1, "signals": [
        {"company": "Acme Robotics", "type": "new_location", "evidence": {"state": "MA", "state_name": "Massachusetts", "postings_there": 3, "cities": ["Worcester, MA"]}},
    ]}


def default_files():
    return {
        "data.js": DATA_JS,
        "data/company_announcements_auto.json": announcements(),
        "data/deals_auto.json": [
            {"company": "Acme Robotics", "investor": "Zed Capital", "amount": "$240M", "round": "Series C", "date": "2026-11",
             "valuation": "$3B", "leadOrParticipant": "lead", "headline": "Acme Robotics raises $240M Series C at a $3B valuation"},
        ],
        "data/funding_tracker_auto.json": [{"company": "Acme Robotics", "lastRound": "Series C", "lastRoundAmount": "$240M"}],
        "data/form_d_filings_auto.json": {"filings": [
            {"match_method": "cik", "company": "Acme Robotics", "issuer_name": "Acme Robotics Inc", "form": "D", "filed_date": "2026-10-30",
             "accession": "0000000001-26-000001", "filing_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000000001&type=D",
             "offering_amount": "20000000", "amount_sold": "14902982", "securities_type": "Equity"},
            {"match_method": "name-strict", "company": "Bolt Energy", "issuer_name": "Bolt Energy Holdings", "form": "D", "filed_date": "2026-10-29",
             "accession": "0000000002-26-000001", "filing_url": "https://www.sec.gov/Archives/edgar/data/2/x/primary_doc.xml",
             "offering_amount": "5000000", "amount_sold": "5000000", "securities_type": "Equity"},
        ]},
        "data/form_d_daily_auto.json": {"filings": [
            {"match_method": "cik", "company": "Acme Robotics", "issuer_name": "Acme Robotics Inc.", "form": "D", "filed_date": "2026-10-30",
             "accession": "0000000001-26-000001", "filing_url": ARCHIVE_URL,
             "offering_amount": "20000000", "amount_sold": "14902982", "securities_type": "Equity"},
        ]},
        "data/sec_filings_raw.json": [
            {"company": "Bolt Energy", "ticker": "", "form": "8-K", "date": "2026-11-01", "accessionNumber": "0000000002-26-000007", "isIPO": False},
            {"company": "Bolt Energy", "ticker": "", "form": "S-1", "date": "2026-11-05", "accessionNumber": "0000000002-26-000009", "isIPO": True},
            {"company": "Acme Robotics", "ticker": "", "form": "S-1", "date": "2026-11-12", "accessionNumber": "0000000001-26-000004", "isIPO": True,
             "filing_url": "https://www.sec.gov/Archives/edgar/data/1/s1.htm"},
        ],
        "data/ipo_pipeline_auto.json": [
            {"company": "Acme Robotics", "status": "IPO Candidate", "likelihood": "high", "estimatedDate": "2027", "estimatedValuation": "$15B"},
        ],
        "data/gov_contracts_raw.json": contracts(),
        "data/gov_contracts_aggregated.json": [{"company": "Acme Robotics", "totalGovValue": "$364M", "recentContracts": []}],
        "data/sbir_awards_auto.json": [
            {"company": "Bolt Energy", "url": "https://www.usaspending.gov/award/CONT_AWD_B1_8000_-NONE-_-NONE-", "year": 2088},
        ],
        "data/nsf_awards_raw.json": [
            {"id": "2610617", "awardee": "University of Somewhere", "amount": 448318, "date": "07/29/2026", "city": "BOULDER", "state": "CO"},
            {"id": "2610999", "awardee": "Delta Foundry", "amount": 500000, "date": "10/15/2026", "city": "HAWTHORNE", "state": "CA",
             "url": "https://www.nsf.gov/awardsearch/showAward?AWD_ID=2610999"},
        ],
        "data/launch_manifest_auto.json": [
            {"date": "2026-10-01", "vehicle": "Test Rocket", "payload": "Sat", "trackedCompany": "Acme Robotics", "url": "https://launches.test/1"},
        ],
        "data/pulse/signals/2026-W44.json": signals_w44(),
        "data/pulse/signals/2026-W45.json": signals_w45(),
        "data/jobs_raw.json": [
            {"company": "Acme Robotics", "title": "Welder", "url": "https://job-boards.greenhouse.io/acmerobotics/jobs/1"},
            {"company": "Acme Robotics", "title": "Engineer", "url": "https://job-boards.greenhouse.io/acmerobotics/jobs/2"},
            {"company": "Bolt Energy", "title": "Technician", "url": "https://jobs.lever.co/boltenergy/1f0e"},
            {"company": "Delta Foundry", "title": "Machinist", "url": "https://deltafoundry.test/jobs/1"},
        ],
        "data/pulse/job_boards.json": [
            {"company": "Acme Robotics", "platform": "greenhouse", "slug": "acmerobotics", "evidence": "legacy list"},
            {"company": "Bolt Energy", "platform": "lever", "slug": "boltenergy", "evidence": "careers-page https://boltenergy.test/careers"},
            {"company": "Delta Foundry", "platform": "custom", "slug": "deltafoundry", "evidence": "manual check"},
        ],
        "data/geocode_cache.json": {"Gone Co|Worcester, MA|MA": {"lat": 42.2626, "lng": -71.8023, "query": "Gone Co Worcester, MA"}},
        # Decoys. The builder must never open these.
        "data/ros_fund_scored.json": [{"company": "Acme Robotics", "note": MARKER}],
        "data/action_brief.json": {"note": MARKER},
        "data/private/notes.json": {"note": MARKER},
    }


def make_repo(folder, overrides=None):
    files = default_files()
    files.update(overrides or {})
    for rel, content in files.items():
        if content is None:
            continue
        path = Path(folder) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
    return Path(folder)


class RepoCase(unittest.TestCase):
    """Builds the made-up repo once per class."""
    include_job_signals = False
    overrides = None

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = make_repo(cls._tmp.name, cls.overrides)
        cls.result = lb.build(cls.root, TODAY, include_job_signals=cls.include_job_signals)
        cls.events = cls.result["events"]
        cls.outputs = lb.render_outputs(cls.result)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def lines(self):
        return {e["line"] for e in self.events}

    def event(self, line_start):
        found = [e for e in self.events if e["line"].startswith(line_start)]
        self.assertEqual(len(found), 1, f"expected one event starting {line_start!r}, got {[e['line'] for e in found]}")
        return found[0]

    def rejected(self, **want):
        out = []
        for c in self.result["candidates"]:
            if c["status"] == "rejected" and all(c.get(k) == v for k, v in want.items()):
                out.append(c)
        return out


# ─── formatting ──────────────────────────────────────────────────────────

class TestMoney(unittest.TestCase):
    def test_fmt_usd(self):
        cases = {
            640: "$640", 6400: "$6.4K", 45205: "$45.2K", 999_600: "$1M", 1_273_575: "$1.27M", 14_902_982: "$14.9M",
            28_554_354: "$28.6M", 249_999_984: "$250M", 362_974_500: "$363M", 1_000_000_000: "$1B",
            3_549_243_793: "$3.55B", 13_000_000_000: "$13B", 1_250_000_000_000: "$1.25T", 100_000: "$100K",
        }
        for amount, text in cases.items():
            self.assertEqual(lb.fmt_usd(amount), text, amount)

    def test_article(self):
        for phrase, art in {"$1B": "a", "$8M": "an", "$80M": "an", "$800M": "an", "$11M": "an", "$18.5M": "an",
                            "$110M": "a", "$118M": "a", "$1.2B": "a", "$85K": "an", "$240M": "a",
                            "Series A": "a", "seed round": "a"}.items():
            self.assertEqual(lb.article_for(phrase), art, phrase)

    def test_amounts_in_a_headline(self):
        a = lb.find_amounts("Shield raises $2.5 billion at a $28.8 billion valuation")
        self.assertEqual([(x["value"], x["valuation"]) for x in a], [(2_500_000_000, False), (28_800_000_000, True)])
        self.assertFalse(lb.find_amounts("Dominion raises $139M CAD Series A")[0]["usd"])
        self.assertTrue(lb.find_amounts("TEKEVER raises US$580 million")[0]["usd"])
        self.assertFalse(lb.find_amounts("raises €40M")[0]["usd"])
        self.assertFalse(lb.find_amounts("secures more than $200M")[0]["exact"])
        self.assertFalse(lb.find_amounts("backing a $300M+ round")[0]["exact"])
        self.assertEqual(lb.find_amounts("raises $1.2Bn Series D")[0]["value"], 1_200_000_000)
        self.assertEqual(lb.find_amounts("Raises $28.5 million")[0]["value"], 28_500_000)
        self.assertEqual(lb.parse_money_field("$240M"), 240_000_000)
        self.assertIsNone(lb.parse_money_field("€99M"))
        self.assertIsNone(lb.parse_money_field(""))

    def test_whole_dollars(self):
        self.assertEqual(lb.to_whole_dollars("14902982"), 14_902_982)
        self.assertEqual(lb.to_whole_dollars(249978466.39), 249_978_466)
        self.assertIsNone(lb.to_whole_dollars("Indefinite"))
        self.assertIsNone(lb.to_whole_dollars(None))


class TestDates(unittest.TestCase):
    def test_parse_day(self):
        self.assertEqual(lb.parse_day("2026-11-09"), (date(2026, 11, 9), None))
        self.assertEqual(lb.parse_day("2026-10-09T00:00:00.000Z"), (date(2026, 10, 9), None))
        self.assertEqual(lb.parse_day("Mon, 09 Nov 2026 00:00:00 GMT"), (date(2026, 11, 9), None))
        self.assertEqual(lb.parse_day("Thu, 05 Nov 2026 16:28:20 +0000"), (date(2026, 11, 5), None))
        self.assertEqual(lb.parse_day("07/29/2026"), (date(2026, 7, 29), None))
        self.assertEqual(lb.parse_day("2026-11"), (None, "date_not_a_day"))
        self.assertEqual(lb.parse_day(2088), (None, "date_not_a_day"))
        self.assertEqual(lb.parse_day("Q4 2026"), (None, "date_not_a_day"))
        self.assertEqual(lb.parse_day(""), (None, "date_missing"))
        self.assertEqual(lb.parse_day(None), (None, "date_missing"))
        self.assertEqual(lb.parse_day("2026-02-31"), (None, "date_implausible"))
        self.assertEqual(lb.parse_day("Late 2026"), (None, "date_implausible"))
        self.assertEqual(lb.parse_day("soon"), (None, "date_implausible"))

    def test_check_day(self):
        self.assertIsNone(lb.check_day(TODAY, TODAY))
        self.assertEqual(lb.check_day(date(2026, 11, 21), TODAY), "date_future")
        self.assertEqual(lb.check_day(date(1989, 12, 31), TODAY), "date_implausible")
        self.assertEqual(lb.check_day(date(2016, 12, 30), TODAY, founded=2019), "date_implausible")
        self.assertIsNone(lb.check_day(date(2018, 6, 1), TODAY, founded=2019))


class TestHeadline(unittest.TestCase):
    def read(self, title, company="Acme Robotics"):
        return lb.read_headline(title, company)

    def test_completed_rounds(self):
        f, _ = self.read("Castelion raises $1B Series C at a $13B valuation", "Castelion")
        self.assertEqual((f["kind"], f["amount_usd"], f["round_label"], f["valuation_usd"]),
                         ("round", 1_000_000_000, "Series C", 13_000_000_000))
        f, _ = self.read("Our $445M Series D")
        self.assertEqual((f["amount_usd"], f["round_label"]), (445_000_000, "Series D"))
        f, _ = self.read("We raised $80M to make hardware teams AI-ready")
        self.assertEqual((f["amount_usd"], f["round_label"], f["valuation_usd"]), (80_000_000, None, None))
        f, _ = self.read("Acme Closes $250 Million Series C to Scale")
        self.assertEqual((f["amount_usd"], f["round_label"]), (250_000_000, "Series C"))
        f, _ = self.read("Acme Robotics Secures $730 Million in Fund-Led Series D at a Valuation Above $4.5 Billion")
        self.assertEqual((f["amount_usd"], f["round_label"], f["valuation_usd"]), (730_000_000, "Series D", 4_500_000_000))
        f, _ = self.read("Acme Robotics Announces Oversubscribed $250 Million Growth Financing")
        self.assertEqual((f["amount_usd"], f["round_label"]), (250_000_000, "growth round"))
        f, _ = self.read("Acme raises an $8M seed round")
        self.assertEqual((f["amount_usd"], f["round_label"]), (8_000_000, "seed round"))
        f, _ = self.read("Acme Robotics raises $40M Series B-2")
        self.assertEqual(f["round_label"], "Series B-2")

    def test_debt(self):
        f, _ = self.read("Waymo Closes $5 Billion Debt Financing to Accelerate Business Expansion", "Waymo")
        self.assertEqual((f["kind"], f["amount_usd"], f["round_label"]), ("debt", 5_000_000_000, None))

    def test_amount_left_empty_when_not_exact_or_not_dollars(self):
        f, _ = self.read("Acme raises more than $200M Series C")
        self.assertEqual((f["amount_usd"], f["round_label"]), (None, "Series C"))
        f, _ = self.read("Acme Robotics raises $139M CAD Series A")
        self.assertEqual((f["amount_usd"], f["round_label"]), (None, "Series A"))

    def test_not_a_completed_round(self):
        for title in (
            "",
            "Acme Robotics to raise $500M Series D",
            "Acme Robotics plans to raise $500M",
            "Acme reportedly raises $11 billion",
            "Shield to acquire Echodyne in a transaction valued at $5.3 billion and raise $2.5 billion",
            "Acme Robotics Secures US$10 Million DARPA Stage B Extension",
            "Acme Robotics Receives $23 Million in Non-Dilutive Funding",
            "Acme Robotics Announces the Company's $150 Million Deposit Investment",
            "Acme Robotics Secures $10M from the Air Force",
            "Acme Robotics wins $40M Army contract and raises $10M",
            "Acme Robotics launches in Germany",
            "Why Investors Are Backing Acme Robotics' $300M+ Round",
            "Acme Robotics Announces $5M Investment in Bolt's Series B",
            "Acme Robotics leads $50M Series B in Bolt",
            "Acme raises $50M Series B, bringing total funding to $80M",
        ):
            fields, why = self.read(title)
            self.assertIsNone(fields, title)
            self.assertTrue(why, title)

    def test_company_must_be_the_subject(self):
        self.assertIsNone(self.read("Bolt raises $20M Series A")[0])
        self.assertIsNone(self.read("Helsing backer Plural raises $1.1B to fund moonshots", "Helsing")[0])
        self.assertIsNone(self.read("This platform just raised $200m in seed funding", "Lila Sciences")[0])
        self.assertIsNotNone(self.read("Robotics startup Acme raises $500m")[0])
        self.assertIsNotNone(self.read("Mazama Energy raises $135M for geothermal", "Mazama")[0])
        self.assertIsNotNone(self.read("Quantum Systems raises $1.2Bn Series D", "Quantum-Systems")[0])
        self.assertIsNotNone(self.read("Announcing Lila's $350M Series A", "Lila Sciences")[0])


# ─── templates and the line check ────────────────────────────────────────

def ev(kind, company="Acme Robotics", amount=None, agency=None, **detail):
    return {"type": kind, "company": company, "amount_usd": amount, "agency": agency, "detail": detail}


TEMPLATE_CASES = [
    (ev("round", "Castelion", 1_000_000_000, round_label="Series C", valuation_usd=13_000_000_000),
     "Castelion raised a $1B Series C at a $13B valuation."),
    (ev("round", amount=445_000_000, round_label="Series D", valuation_usd=None), "Acme Robotics raised a $445M Series D."),
    (ev("round", amount=8_000_000, round_label="seed round", valuation_usd=None), "Acme Robotics raised an $8M seed round."),
    (ev("round", amount=240_000_000, round_label=None, valuation_usd=3_000_000_000), "Acme Robotics raised $240M at a $3B valuation."),
    (ev("round", amount=80_000_000, round_label=None, valuation_usd=None), "Acme Robotics raised $80M."),
    (ev("round", amount=None, round_label="Series A", valuation_usd=None), "Acme Robotics raised a Series A."),
    (ev("round", amount=None, round_label=None, valuation_usd=None), "Acme Robotics raised a funding round."),
    (ev("round", amount=11_000_000, round_label="Series A", valuation_usd=80_000_000), "Acme Robotics raised an $11M Series A at an $80M valuation."),
    (ev("debt", amount=5_000_000_000), "Acme Robotics announced $5B in debt financing."),
    (ev("debt"), "Acme Robotics announced a debt financing."),
    (ev("form_d", amount=14_902_982, form="D", offering_usd=20_000_000, securities="Equity"),
     "Acme Robotics filed a Form D with the SEC reporting $14.9M sold of a $20M offering."),
    (ev("form_d", amount=249_999_984, form="D", offering_usd=None, securities="Equity"),
     "Acme Robotics filed a Form D with the SEC reporting $250M sold."),
    (ev("form_d", amount=3_000_000, form="D/A", offering_usd=6_000_000, securities="Debt"),
     "Acme Robotics filed an amended Form D with the SEC reporting $3M sold of a $6M debt offering."),
    (ev("form_d", amount=3_000_000, form="D", offering_usd=None, securities="Debt"),
     "Acme Robotics filed a Form D with the SEC reporting $3M sold in a debt offering."),
    (ev("form_d", amount=None, form="D", offering_usd=8_000_000, securities="Equity"),
     "Acme Robotics filed a Form D with the SEC for an $8M offering, with no sales reported yet."),
    (ev("form_d", amount=None, form="D", offering_usd=None, securities=None), "Acme Robotics filed a Form D with the SEC."),
    (ev("ipo_filing", form="S-1"), "Acme Robotics filed a Form S-1 registration statement with the SEC."),
    (ev("ipo_filing", form="F-1/A"), "Acme Robotics filed an amended Form F-1 registration statement with the SEC."),
    (ev("contract", amount=362_974_500, agency="Department of Homeland Security", sub_agency="U.S. Customs and Border Protection"),
     "Acme Robotics was awarded a $363M contract by the Department of Homeland Security (U.S. Customs and Border Protection)."),
    (ev("contract", amount=45_205, agency="Department of the Interior", sub_agency=None),
     "Acme Robotics was awarded a $45.2K contract by the Department of the Interior."),
    (ev("contract", amount=None, agency="Department of Energy", sub_agency=None), "Acme Robotics was awarded a contract by the Department of Energy."),
    (ev("contract", amount=None, agency=None, sub_agency=None), "Acme Robotics was awarded a contract by a federal agency."),
    (ev("grant", amount=448_318, agency="National Science Foundation"), "Acme Robotics received a $448K grant from the National Science Foundation."),
    (ev("grant", amount=None, agency="National Science Foundation"), "Acme Robotics received a grant from the National Science Foundation."),
    (ev("new_location", state="OH", postings_there=2),
     "Acme Robotics listed 2 open roles in Ohio, a state where it had listed none in the prior twelve weeks."),
    (ev("first_mfg_role", mfg_roles_now=1, roles_now=33),
     "Acme Robotics listed its first manufacturing role in at least four weeks (1 of 33 open roles)."),
    (ev("first_mfg_role", mfg_roles_now=3, roles_now=18),
     "Acme Robotics listed its first manufacturing roles in at least four weeks (3 of 18 open roles)."),
    (ev("senior_mfg_role", senior_roles_now=1), "Acme Robotics listed a senior manufacturing, plant or facilities role."),
    (ev("senior_mfg_role", senior_roles_now=3), "Acme Robotics added a senior manufacturing, plant or facilities role and now lists 3."),
    (ev("production_turn", share_before_pct=43.6, share_now_pct=66.7, roles_now=114),
     "Acme Robotics shifted its open roles toward manufacturing and hardware, from 43.6% to 66.7% of openings in twelve weeks (114 open roles)."),
    (ev("hiring_surge", roles_before=33, roles_now=66, change_pct=100.0),
     "Acme Robotics increased its open roles from 33 to 66 in four weeks, a rise of 100%."),
    (ev("hiring_surge", roles_before=78, roles_now=114, change_pct=46.2),
     "Acme Robotics increased its open roles from 78 to 114 in four weeks, a rise of 46.2%."),
]


class TestTemplates(unittest.TestCase):
    def test_every_template(self):
        for event, want in TEMPLATE_CASES:
            self.assertEqual(lb.render_line(event), want)

    def test_every_type_has_a_template_and_a_grammar(self):
        covered = {event["type"] for event, _ in TEMPLATE_CASES}
        self.assertEqual(covered, set(lb.TYPES))
        self.assertEqual(set(lb._GRAMMAR), set(lb.TYPES))

    def test_templates_use_no_praise_words(self):
        for event, _ in TEMPLATE_CASES:
            line = lb.render_line(event)
            rest = line[len(event["company"]):].lower()
            for word in lb.PRAISE_WORDS:
                self.assertNotRegex(rest, r"\b" + word + r"\b")

    def test_unknown_type_has_no_template(self):
        with self.assertRaises(ValueError):
            lb.render_line(ev("layoff"))


class TestLineCheck(unittest.TestCase):
    def test_rendered_lines_pass(self):
        for event, _ in TEMPLATE_CASES:
            event = dict(event, line=lb.render_line(event))
            self.assertEqual(lb.verify_line(event), [], event["line"])

    def test_a_changed_field_is_caught(self):
        changes = {
            "round": [("amount_usd", 999_000_000), ("detail.round_label", "Series D"), ("detail.valuation_usd", 5_000_000_000), ("detail.valuation_usd", None)],
            "debt": [("amount_usd", 6_000_000_000), ("amount_usd", None)],
            "form_d": [("amount_usd", 15_900_000), ("detail.offering_usd", 30_000_000), ("detail.form", "D/A"), ("detail.securities", "Debt")],
            "ipo_filing": [("detail.form", "F-1"), ("detail.form", "S-1/A")],
            "contract": [("amount_usd", 1_000), ("agency", "Department of Energy"), ("detail.sub_agency", "Department of the Army")],
            "grant": [("amount_usd", 5), ("agency", "Department of Energy")],
            "new_location": [("detail.state", "TX"), ("detail.postings_there", 5)],
            "first_mfg_role": [("detail.mfg_roles_now", 2), ("detail.roles_now", 99)],
            "senior_mfg_role": [("detail.senior_roles_now", 7)],
            "production_turn": [("detail.share_before_pct", 10.0), ("detail.share_now_pct", 99.0), ("detail.roles_now", 7)],
            "hiring_surge": [("detail.roles_before", 1), ("detail.roles_now", 999), ("detail.change_pct", 12.5)],
        }
        first = {}
        for event, _ in TEMPLATE_CASES:
            first.setdefault(event["type"], event)
        for kind, edits in changes.items():
            base = first[kind]
            line = lb.render_line(base)
            for path, value in edits:
                changed = {"type": kind, "company": base["company"], "amount_usd": base["amount_usd"],
                           "agency": base["agency"], "detail": dict(base["detail"]), "line": line}
                if path.startswith("detail."):
                    changed["detail"][path[7:]] = value
                else:
                    changed[path] = value
                self.assertTrue(lb.verify_line(changed), f"{kind}: changing {path} to {value!r} went unnoticed")

    def test_a_changed_line_is_caught(self):
        event = ev("round", "Castelion", 1_000_000_000, round_label="Series C", valuation_usd=13_000_000_000)
        good = lb.render_line(event)
        for bad in (
            good.replace("$1B", "$2B"),
            good.replace("$13B", "$31B"),
            good.replace("Series C", "Series B"),
            good.replace("a $1B", "an $1B"),
            good.replace("Castelion", "Castellon"),
            good[:-1],
            good.replace(" raised", "  raised"),
            good.replace("raised", "raised a massive"),
            good.replace(".", " and is the leading company."),
            "Castelion raised None.",
            "",
        ):
            self.assertTrue(lb.verify_line(dict(event, line=bad)), bad)

    def test_praise_and_empty_fields_are_caught(self):
        event = ev("contract", amount=5_000_000, agency="Department of Impressive Things", sub_agency=None)
        event["line"] = lb.render_line(event)
        self.assertTrue(any("praise" in p for p in lb.verify_line(event)))
        event = ev("grant", amount=5_000_000, agency=None)
        event["line"] = "Acme Robotics received a $5M grant from the None."
        self.assertTrue(lb.verify_line(event))


# ─── score ───────────────────────────────────────────────────────────────

class TestScore(unittest.TestCase):
    def test_dollar_points(self):
        cases = {None: "0.0", 0: "0.0", 99_999: "0.0", 100_000: "0.0", 1_000_000: "10.0", 10_000_000: "20.0",
                 35_000_000: "25.4", 100_000_000: "30.0", 240_000_000: "33.8", 1_000_000_000: "40.0",
                 5_000_000_000: "47.0", 10_000_000_000: "50.0", 100_000_000_000: "50.0"}
        for amount, points in cases.items():
            self.assertEqual(lb.dollar_points(amount), Decimal(points), amount)

    def test_parts_and_total(self):
        self.assertEqual(lb.score_parts("round", 240_000_000, False), {"type": 20, "dollars": 33.8, "first": 0})
        self.assertEqual(lb.score_total(lb.score_parts("round", 240_000_000, False)), 53.8)
        self.assertEqual(lb.score_total(lb.score_parts("contract", 5_000_000, True)), 47.0)
        self.assertEqual(lb.score_total(lb.score_parts("new_location", None, False)), 45.0)
        self.assertEqual(lb.score_total(lb.score_parts("form_d", 249_999_984, False)), 44.0)

    def test_only_the_fields_decide(self):
        a = lb.score_parts("contract", 1_273_575, False)
        b = lb.score_parts("contract", 1_273_575, False)
        self.assertEqual(a, b)
        self.assertGreater(lb.score_total(lb.score_parts("contract", 2_000_000, False)), lb.score_total(a))
        self.assertGreater(lb.score_total(lb.score_parts("contract", 1_273_575, True)), lb.score_total(a))

    def test_the_published_table(self):
        self.assertEqual({k: v["points"] for k, v in lb.TYPES.items()}, {
            "round": 20, "debt": 20, "form_d": 10, "ipo_filing": 35, "contract": 20, "grant": 15,
            "new_location": 45, "first_mfg_role": 45, "senior_mfg_role": 35, "production_turn": 35, "hiring_surge": 25})
        self.assertEqual((lb.DOLLAR_FLOOR_USD, lb.POINTS_PER_TENFOLD, lb.DOLLAR_CAP_POINTS, lb.FIRST_POINTS, lb.FIRST_RECORD_DAYS),
                         (100_000, 10, 50, 10, 365))
        for kind in ("round", "debt", "form_d"):
            self.assertFalse(lb.TYPES[kind]["first"])
        method = lb.method_text()
        for needle in ("10 x log10(amount / $100K)", "never above 50", "$1B = 40.0", "at least 365 days", "within 30 days"):
            self.assertIn(needle, method)


# ─── data.js ─────────────────────────────────────────────────────────────

class TestDataJs(unittest.TestCase):
    def test_literal_reader(self):
        value, end = lb.parse_js_literal("[{a: 1, 'b': \"x\\u2014y\", c: [true, null, -2.5, 0x10,], /* note */ d: {e: 'it\\'s'},}, ] // tail")
        self.assertEqual(value, [{"a": 1, "b": "x—y", "c": [True, None, -2.5, 16], "d": {"e": "it's"}}])
        with self.assertRaises(lb.JSLiteralError):
            lb.parse_js_literal("[{a: SOME_CONSTANT}]")
        with self.assertRaises(lb.JSLiteralError):
            lb.parse_js_literal("[{a: `template`}]")
        with self.assertRaises(lb.JSLiteralError):
            lb.parse_js_literal("[1, 2")

    def test_companies_and_matching(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            records = lb.load_companies(root)
        self.assertEqual([r["name"] for r in records],
                         ["Acme Robotics", "Bolt Energy", "Northwind Fusion", "Quiet Motors", "Delta Foundry", "Miami Marine"])
        index = lb.CompanyIndex(records)
        self.assertEqual(index.match("Acme Robotics")["name"], "Acme Robotics")
        self.assertEqual(index.match(" acme robotics ")["name"], "Acme Robotics")
        self.assertEqual(index.match("Volt Power")["name"], "Bolt Energy")
        for miss in ("Acme", "Acme Robotics Inc", "Bolt", "Not A Company", "Zed Capital", "", None):
            self.assertIsNone(index.match(miss), miss)


# ─── the pipeline on the made-up repo ────────────────────────────────────

EXPECTED_DEFAULT = {
    "Acme Robotics raised a $240M Series C at a $3B valuation.",
    "Bolt Energy announced $35M in debt financing.",
    "Acme Robotics filed a Form D with the SEC reporting $14.9M sold of a $20M offering.",
    "Acme Robotics filed a Form S-1 registration statement with the SEC.",
    "Acme Robotics was awarded a $363M contract by the Department of Homeland Security (U.S. Customs and Border Protection).",
    "Acme Robotics was awarded a $45.2K contract by the Department of the Interior.",
    "Acme Robotics was awarded a contract by a federal agency.",
    "Bolt Energy was awarded a $1.27M contract by the National Aeronautics and Space Administration.",
    "Bolt Energy was awarded a $5M contract by the Department of Energy.",
    "Delta Foundry received a $500K grant from the National Science Foundation.",
}
EXPECTED_JOB_SIGNALS = {
    "Acme Robotics increased its open roles from 33 to 66 in four weeks, a rise of 100%.",
    "Acme Robotics listed 2 open roles in Florida, a state where it had listed none in the prior twelve weeks.",
    "Acme Robotics listed 3 open roles in Massachusetts, a state where it had listed none in the prior twelve weeks.",
    "Acme Robotics listed its first manufacturing role in at least four weeks (1 of 66 open roles).",
    "Acme Robotics added a senior manufacturing, plant or facilities role and now lists 2.",
    "Acme Robotics shifted its open roles toward manufacturing and hardware, from 43.6% to 66.7% of openings in twelve weeks (66 open roles).",
    "Bolt Energy listed 2 open roles in Ohio, a state where it had listed none in the prior twelve weeks.",
}


class TestPipeline(RepoCase):
    def test_published_lines(self):
        self.assertEqual(self.lines(), EXPECTED_DEFAULT)

    def test_every_published_event_is_sound(self):
        names = {r["name"] for r in lb.load_companies(self.root)}
        for e in self.events:
            self.assertIn(e["company"], names)
            self.assertTrue(e["source"]["url"].startswith("https://"), e["line"])
            self.assertLessEqual(date.fromisoformat(e["date"]), TODAY)
            self.assertEqual(lb.verify_line(e), [], e["line"])
            self.assertIn(e["source"]["name"], set(lb.SOURCE_NAMES.values()))
            self.assertEqual(e["score"], lb.score_total(e["score_parts"]))
            self.assertEqual(e["score_parts"], lb.score_parts(e["type"], e["amount_usd"], e["first_of_kind"]))
            self.assertEqual(set(e), {"id", "type", "company", "sector", "date", "age_days", "amount_usd", "agency", "program",
                                      "place", "source", "detail", "line", "first_of_kind", "score", "score_parts",
                                      "provenance", "thread"})

    def test_rejection_reasons(self):
        def reasons(**want):
            found = self.rejected(**want)
            self.assertEqual(len(found), 1, f"{want}: {len(found)} rows")
            return found[0]["reasons"]
        file = "data/company_announcements_auto.json"
        self.assertEqual(reasons(file=file, ref="results[0].hits[2]"), ["source_not_primary"])
        self.assertEqual(reasons(file=file, ref="results[0].hits[3]"), ["fields_not_confirmed"])
        self.assertEqual(set(reasons(file=file, ref="results[0].hits[4]")), {"fields_not_confirmed", "date_missing"})
        self.assertEqual(reasons(file=file, ref="results[1].hits[1]"), ["date_unreliable"])
        self.assertEqual(reasons(file=file, ref="results[1].hits[2]"), ["date_unreliable"])
        self.assertEqual(reasons(file=file, ref="results[1].hits[3]"), ["date_future"])
        self.assertEqual(reasons(file=file, ref="results[1].hits[4]"), ["fields_not_confirmed"])
        self.assertEqual(reasons(file=file, ref="results[2].hits[0]"), ["outside_us"])
        self.assertEqual(reasons(file=file, ref="results[3].hits[0]"), ["company_not_in_database"])
        self.assertEqual(set(reasons(file="data/deals_auto.json")), {"no_source_url", "date_not_a_day"})
        self.assertEqual(reasons(file="data/form_d_filings_auto.json", ref="filings[1]"), ["fields_not_confirmed"])
        self.assertEqual(reasons(file="data/sec_filings_raw.json", ref="[1]"), ["no_source_url"])
        self.assertEqual(reasons(file="data/ipo_pipeline_auto.json")[0], "not_an_event")
        self.assertEqual(reasons(file="data/launch_manifest_auto.json")[0], "not_an_event")
        contracts_file = "data/gov_contracts_raw.json"
        self.assertEqual(reasons(file=contracts_file, ref="[2]"), ["no_source_url"])
        self.assertEqual(reasons(file=contracts_file, ref="[6]"), ["company_not_in_database"])
        self.assertEqual(reasons(file=contracts_file, ref="[7]"), ["date_future"])
        self.assertEqual(reasons(file=contracts_file, ref="[9]"), ["negative_signal"])
        self.assertEqual(set(reasons(file="data/nsf_awards_raw.json", ref="[0]")), {"company_not_in_database", "no_source_url"})

    def test_primary_reason_order(self):
        self.assertEqual(lb.primary_reason(["no_source_url", "outside_us"]), "outside_us")
        self.assertEqual(lb.primary_reason(["date_missing", "negative_signal", "no_source_url"]), "negative_signal")
        self.assertEqual(lb.primary_reason(["line_mismatch", "date_future"]), "date_future")

    def test_duplicates_are_one_event(self):
        e = self.event("Acme Robotics raised a $240M")
        self.assertEqual(e["source"]["url"], ACME_SITE + "/news/series-c")
        self.assertEqual(e["source"]["also"], [ACME_SITE + "/blog/we-raised"])
        self.assertEqual(len(e["provenance"]), 2)
        e = self.event("Acme Robotics filed a Form D")
        self.assertEqual(e["source"]["url"], ARCHIVE_URL)      # the filing itself, not the list of filings
        e = self.event("Bolt Energy was awarded a $1.27M contract")
        self.assertEqual(e["source"]["url"], "https://www.usaspending.gov/award/CONT_AWD_B1_8000_-NONE-_-NONE-")
        merged = [c for c in self.result["candidates"] if c["status"] == "merged"]
        self.assertEqual(len(merged), 3)

    def test_job_signals_are_held_by_default(self):
        held = [c for c in self.result["candidates"] if c["status"] == "held"]
        self.assertEqual({c["line"] for c in held}, EXPECTED_JOB_SIGNALS)
        self.assertFalse(any(lb.TYPES[e["type"]]["stream"] == "jobs" for e in self.events))
        page = json.loads(self.outputs[lb.OUT_PAGE].split("const LAGEBILD = ", 1)[1].rstrip().rstrip(";"))
        self.assertEqual(page["held_types"], [k for k, v in lb.TYPES.items() if v["stream"] == "jobs"])
        self.assertFalse(any(r["type"] in page["held_types"] for r in page["events"]))
        self.assertFalse(any(k in page["held_types"] for k in page["awaiting_link"]))
        self.assertNotIn("open roles from", self.outputs[lb.OUT_PAGE] + self.outputs[lb.OUT_EVENTS])
        self.assertIn("held", json.loads(self.outputs[lb.OUT_REJECTED])["job_board_signals"])

    def test_places_are_town_level(self):
        e = self.event("Acme Robotics raised a $240M")
        self.assertEqual(e["place"], {"name": "Hawthorne, CA", "state": "CA", "lat": 33.9, "lng": -118.4, "basis": "hq"})
        e = self.event("Delta Foundry received")
        self.assertEqual((e["place"]["name"], e["place"]["basis"], e["place"]["lat"], e["place"]["lng"]), ("Hawthorne, CA", "source", 33.9, -118.4))
        for e in self.events:
            for axis in ("lat", "lng"):
                value = e["place"][axis]
                if value is not None:
                    self.assertEqual(value, round(value, lb.COORD_DECIMALS))
        text = "".join(self.outputs.values())
        for exact in ("33.9164", "118.3526", "33.9128", "118.3426", "29.7587", "95.3698"):
            self.assertNotIn(exact, text)

    def test_threads(self):
        a1 = self.event("Acme Robotics was awarded a $363M")
        a2 = self.event("Acme Robotics was awarded a $45.2K")
        a3 = self.event("Acme Robotics was awarded a contract by a federal agency")
        self.assertEqual(a1["thread"], {"root": a1["id"], "position": 0, "size": 2})
        self.assertEqual(a2["thread"], {"root": a1["id"], "position": 1, "size": 2})
        self.assertEqual(a3["thread"], {"root": a3["id"], "position": 0, "size": 1})     # 83 days earlier: its own thread
        b1 = self.event("Bolt Energy was awarded a $1.27M")
        b3 = self.event("Bolt Energy was awarded a $5M")
        self.assertNotEqual(b1["thread"]["root"], b3["thread"]["root"])                  # 70 days apart
        page = json.loads(self.outputs[lb.OUT_PAGE].split("const LAGEBILD = ", 1)[1].rstrip().rstrip(";"))
        row = next(r for r in page["events"] if r["id"] == a2["id"])
        self.assertEqual(row["thread"], a1["id"])
        self.assertEqual(row["follows"], {"date": a1["date"], "line": a1["line"], "url": a1["source"]["url"]})

    def test_first_of_kind(self):
        firsts = {e["line"] for e in self.events if e["first_of_kind"]}
        # Bolt's September award is its earliest on record and the record of contracts goes back
        # more than a year. Acme's awards are not first: an earlier award without a link is on record.
        self.assertEqual(firsts, {"Bolt Energy was awarded a $5M contract by the Department of Energy."})
        e = self.event("Bolt Energy was awarded a $5M")
        self.assertEqual((e["score_parts"], e["score"]), ({"type": 20, "dollars": 17.0, "first": 10}, 47.0))

    def test_scores_and_order(self):
        e = self.event("Acme Robotics was awarded a $363M")
        self.assertEqual((e["score_parts"], e["score"]), ({"type": 20, "dollars": 35.6, "first": 0}, 55.6))
        e = self.event("Acme Robotics filed a Form S-1")
        self.assertEqual(e["score"], 35.0)
        scores = [e["score"] for e in self.events]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_page_file(self):
        text = self.outputs[lb.OUT_PAGE]
        self.assertTrue(text.startswith("// Auto-generated by scripts/build_lagebild.py"))
        self.assertTrue(text.endswith("};\n"))
        page = json.loads(text.split("const LAGEBILD = ", 1)[1].rstrip().rstrip(";"))
        self.assertEqual(page["as_of"], "2026-11-20")
        self.assertEqual(page["windows"], [7, 30, 90])
        self.assertEqual({r["line"] for r in page["events"]}, EXPECTED_DEFAULT)
        for r in page["events"]:
            self.assertLessEqual((TODAY - date.fromisoformat(r["date"])).days, lb.PAYLOAD_DAYS)
            self.assertTrue(r["url"].startswith("https://"))
            self.assertEqual(round(sum(r["parts"]), 1), r["score"])
        self.assertEqual(page["awaiting_link"], {"ipo_filing": {"7": 0, "30": 1, "90": 1}})
        self.assertEqual(set(page["types"]), set(lb.TYPES))

    def test_events_file_and_windows(self):
        report = json.loads(self.outputs[lb.OUT_EVENTS])
        self.assertEqual(report["counts"]["published"], 10)
        self.assertEqual(report["counts"]["by_window_days"], {"7": 2, "30": 7, "90": 10})
        self.assertEqual(report["counts"]["by_type"], {"round": 1, "debt": 1, "form_d": 1, "ipo_filing": 1, "contract": 5, "grant": 1})
        dates = [e["date"] for e in report["events"]]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_rejects_file_has_counts_and_no_names(self):
        text = self.outputs[lb.OUT_REJECTED]
        report = json.loads(text)
        for name in ("Acme", "Bolt", "Northwind", "Quiet", "Delta Foundry", "Miami Marine", "Ghost", "Zed Capital", "University"):
            self.assertNotIn(name, text)
        totals = report["totals"]
        self.assertEqual(totals["rows_read_as_events"], totals["published"] + totals["held"] + totals["merged_duplicates"] + totals["rejected"])
        self.assertEqual((totals["published"], totals["held"], totals["merged_duplicates"]), (10, 7, 3))
        self.assertEqual(report["by_type"]["hiring_pullback"]["primary_reason"], {"negative_signal": 1})
        self.assertEqual(report["by_type"]["round"]["any_reason"]["no_source_url"], 1)
        self.assertEqual(report["by_type"]["contract"]["primary_reason"],
                         {"negative_signal": 1, "company_not_in_database": 1, "no_source_url": 1, "date_future": 1})
        self.assertEqual(report["passed_every_check_except_the_link"]["contract"]["all"], 1)
        roles = {s["file"]: s["role"] for s in report["by_source"]}
        self.assertEqual(roles["data/funding_tracker_auto.json"], "roll-up")
        self.assertEqual(roles["data/gov_contracts_aggregated.json"], "roll-up")
        skipped = {s["file"]: s["rows_not_read_as_events"] for s in report["by_source"]}
        self.assertEqual(skipped["data/sec_filings_raw.json"], 1)       # the 8-K

    def test_nothing_private_or_negative_gets_out(self):
        text = "".join(self.outputs.values())
        self.assertNotIn(MARKER, text)                 # fund, brief and private files are never read
        self.assertNotIn("Quiet Motors", text)         # named only in a pullback and a clawed-back award
        self.assertNotIn("Zed Capital", text)          # investors are never listed
        self.assertNotIn("Quote's Fund", text)
        self.assertNotIn("pullback", self.outputs[lb.OUT_PAGE].lower())
        self.assertNotIn("pullback", self.outputs[lb.OUT_EVENTS].lower())

    def test_forbidden_inputs_are_refused(self):
        for rel in ("data/ros_fund_scored.json", "data/action_brief.json", "data/action_brief_state.json", "data/private/notes.json"):
            with self.assertRaises(PermissionError):
                lb.read_input(self.root, rel)
        with self.assertRaises(PermissionError):
            lb.read_input(self.root, "data/weekly_brief.json")       # not on the allow-list
        for rel in lb.INPUTS.values():
            self.assertFalse(any(marker in rel.lower() for marker in lb.FORBIDDEN_INPUT_MARKERS), rel)

    def test_listing_rejects_never_names_a_negative_signal(self):
        out = io.StringIO()
        lb.list_rejects(self.result, "negative_signal", out=out)
        self.assertNotIn("Quiet Motors", out.getvalue())
        for reason in lb.REASONS:
            out = io.StringIO()
            lb.list_rejects(self.result, reason, out=out)
            self.assertNotIn("Quiet Motors", out.getvalue(), reason)
        out = io.StringIO()
        lb.list_rejects(self.result, "no_source_url", out=out)
        self.assertIn("Acme Robotics", out.getvalue())


class TestJobSignalsSwitchedOn(RepoCase):
    include_job_signals = True

    def test_published_lines(self):
        self.assertEqual(self.lines(), EXPECTED_DEFAULT | EXPECTED_JOB_SIGNALS)
        for e in self.events:
            self.assertEqual(lb.verify_line(e), [], e["line"])

    def test_sources_are_job_boards(self):
        e = self.event("Acme Robotics increased its open roles")
        self.assertEqual((e["source"]["name"], e["source"]["url"]), ("Company job board", "https://job-boards.greenhouse.io/acmerobotics"))
        self.assertEqual(e["date"], "2026-11-01")
        e = self.event("Bolt Energy listed 2 open roles in Ohio")
        self.assertEqual(e["source"]["url"], "https://jobs.lever.co/boltenergy")

    def test_places(self):
        e = self.event("Acme Robotics listed 2 open roles in Florida")
        self.assertEqual(e["place"], {"name": "Miami, FL", "state": "FL", "lat": 25.8, "lng": -80.2, "basis": "source"})
        e = self.event("Acme Robotics listed 3 open roles in Massachusetts")        # a town known only from the geocode cache
        self.assertEqual(e["place"], {"name": "Worcester, MA", "state": "MA", "lat": 42.3, "lng": -71.8, "basis": "source"})
        e = self.event("Bolt Energy listed 2 open roles in Ohio")                   # "Ohio, OH" names no town: listed, not mapped
        self.assertEqual(e["place"], {"name": "Ohio", "state": "OH", "lat": None, "lng": None, "basis": "source"})
        e = self.event("Acme Robotics listed its first manufacturing role")
        self.assertEqual(e["place"]["basis"], "hq")

    def test_guards_and_never_published_signals(self):
        def one(company, kind):
            found = [c for c in self.result["candidates"] if c["company_raw"] == company and c["type"] == kind]
            self.assertEqual(len(found), 1)
            return found[0]
        self.assertEqual(one("Bolt Energy", "hiring_surge")["reasons"], ["fields_implausible"])
        self.assertEqual(one("Bolt Energy", "production_turn")["reasons"], ["fields_implausible"])
        self.assertEqual(one("Delta Foundry", "hiring_surge")["reasons"], ["no_source_url"])
        self.assertEqual(one("Quiet Motors", "hiring_pullback")["reasons"], ["negative_signal"])
        self.assertEqual(one("Acme Robotics", "board_check")["reasons"], ["not_an_event"])
        self.assertEqual(one("Acme Robotics", "job_signal_other")["reasons"], ["not_an_event"])     # unknown types: default deny
        text = "".join(self.outputs.values())
        self.assertNotIn("Quiet Motors", text)
        self.assertNotIn("runway", text.lower())
        self.assertEqual(json.loads(self.outputs[lb.OUT_PAGE].split("const LAGEBILD = ", 1)[1].rstrip().rstrip(";"))["held_types"], [])

    def test_no_first_claims_from_a_short_record(self):
        # The job-board record starts on 1 Nov 2026, far less than 365 days back.
        for e in self.events:
            if lb.TYPES[e["type"]]["stream"] == "jobs":
                self.assertFalse(e["first_of_kind"], e["line"])


class TestShortContractRecord(RepoCase):
    """Without the 2025 award, the record of contracts is under a year deep: no firsts at all."""
    overrides = {"data/gov_contracts_raw.json": [r for r in contracts() if r["awardId"] != "A0"]}

    def test_no_firsts(self):
        self.assertEqual([e["line"] for e in self.events if e["first_of_kind"]], [])
        self.assertEqual(self.lines(), EXPECTED_DEFAULT)


class TestMissingInputs(RepoCase):
    """A source file that is absent is an empty source, not a crash."""
    overrides = {rel: None for rel in default_files() if rel != "data.js" and "ros_fund" not in rel and "action_brief" not in rel and "private" not in rel}

    def test_builds_empty(self):
        self.assertEqual(self.events, [])
        page = json.loads(self.outputs[lb.OUT_PAGE].split("const LAGEBILD = ", 1)[1].rstrip().rstrip(";"))
        self.assertEqual(page["events"], [])
        self.assertEqual(json.loads(self.outputs[lb.OUT_REJECTED])["totals"]["rows_read_as_events"], 0)


class TestDeterminism(unittest.TestCase):
    def test_same_day_same_bytes(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for folder in (a, b):
                make_repo(folder)
            first = lb.render_outputs(lb.build(Path(a), TODAY))
            second = lb.render_outputs(lb.build(Path(b), TODAY))
            again = lb.render_outputs(lb.build(Path(a), TODAY))
        self.assertEqual(first, second)
        self.assertEqual(first, again)
        self.assertEqual(list(first), [lb.OUT_EVENTS, lb.OUT_REJECTED, lb.OUT_METHOD, lb.OUT_PAGE])

    def test_cli_writes_identical_files_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            runs = []
            for _ in range(2):
                out = io.StringIO()
                stdout, sys.stdout = sys.stdout, out
                try:
                    self.assertEqual(lb.main(["--root", tmp, "--today", "2026-11-20"]), 0)
                finally:
                    sys.stdout = stdout
                runs.append({rel: (Path(tmp) / rel).read_bytes() for rel in (lb.OUT_EVENTS, lb.OUT_REJECTED, lb.OUT_METHOD, lb.OUT_PAGE)})
            self.assertEqual(runs[0], runs[1])
            self.assertNotIn("Quiet Motors", out.getvalue())

    def test_the_build_date_moves_the_windows(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            early = lb.render_outputs(lb.build(Path(tmp), date(2026, 11, 10)))
            late = lb.render_outputs(lb.build(Path(tmp), TODAY))
        self.assertNotEqual(early[lb.OUT_PAGE], late[lb.OUT_PAGE])
        self.assertEqual(early[lb.OUT_METHOD], late[lb.OUT_METHOD])             # the method file has no dates in it
        early_events = json.loads(early[lb.OUT_EVENTS])
        self.assertEqual(early_events["as_of"], "2026-11-10")
        self.assertTrue(all(e["date"] <= "2026-11-10" for e in early_events["events"]))

    def test_the_clock_is_never_read_when_a_date_is_given(self):
        class NoClock:
            @staticmethod
            def now(*args, **kwargs):
                raise AssertionError("the build read the clock")

        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            normal = lb.render_outputs(lb.build(Path(tmp), TODAY))
            with mock.patch.object(lb, "datetime", NoClock):
                frozen = lb.render_outputs(lb.build(Path(tmp), TODAY))
        self.assertEqual(normal, frozen)
        for text in normal.values():
            self.assertNotIn("generated_at", text)


# ─── the real repo, if this test runs inside it ──────────────────────────

class TestRealRepo(unittest.TestCase):
    def test_invariants_on_live_data(self):
        root = Path(__file__).resolve().parents[2]
        if not (root / "data.js").is_file() or not (root / "data").is_dir():
            self.skipTest("not inside the site repo")
        result = lb.build(root, TODAY, include_job_signals=True)
        names = {r["name"] for r in lb.load_companies(root)}
        self.assertGreater(len(names), 1000)
        for e in result["events"]:
            self.assertIn(e["company"], names)
            self.assertEqual(lb.verify_line(e), [], e["line"])
            self.assertTrue(e["source"]["url"].startswith("https://"))
            self.assertLessEqual(date.fromisoformat(e["date"]), TODAY)
            for axis in ("lat", "lng"):
                if e["place"][axis] is not None:
                    self.assertEqual(e["place"][axis], round(e["place"][axis], lb.COORD_DECIMALS))
        for c in result["candidates"]:
            self.assertIn(c["status"], ("published", "held", "merged", "rejected"))
            if c["type"] in lb.OTHER_KINDS:
                self.assertEqual(c["status"], "rejected")
        self.assertEqual(lb.render_outputs(result), lb.render_outputs(lb.build(root, TODAY, include_job_signals=True)))


if __name__ == "__main__":
    unittest.main(verbosity=1)
