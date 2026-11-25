#!/usr/bin/env python3
"""
Offline tests for scripts/build_imagined.py (Who's Building It, imagined.html).

    python3 -m unittest scripts/tests/test_imagined.py
    python3 scripts/tests/test_imagined.py

No network and no Node. Most tests build a small made-up repo in a temporary folder: a data.js
with invented companies and a theme file written to hit one rule at a time. The last tests run
the real repo's theme file and data.js through the same checks.
"""
import copy
import json
import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_imagined as bi  # noqa: E402

TODAY = date(2026, 11, 25)
REPO = Path(__file__).resolve().parents[2]

DATA_JS = r'''
// Made-up companies for the tests. Nothing here is real.
const LAST_UPDATED = "2026-11-24";
const COMPANIES = [
  { name: "Acme Fusion", status: "active", sector: "Nuclear Energy", subsector: "Fusion",
    tags: ["fusion", "tokamak"], description: "Builds a \"tokamak\".", fundingStage: "Series B", totalRaised: "$1.2B" },
  { name: "Beta Plasma", status: "active", sector: "Nuclear Energy", subsector: "Fusion",
    tags: ["fusion"], description: "Plasma machines.", fundingStage: "Seed", totalRaised: "$40M" },
  { name: "Gamma Grid", status: "active", sector: "Climate & Energy", subsector: "Grid",
    tags: ["grid"], description: "Builds grid software; once looked at fusion.", techApproach: "Software", fundingStage: "Series A", totalRaised: "Undisclosed" },
  { name: "Delta Dead", status: "dead", sector: "Nuclear Energy", subsector: "Fusion",
    tags: ["fusion"], description: "Gone.", fundingStage: "Seed", totalRaised: "$5M" },
  { name: "Epsilon Rockets", status: "ipo", sector: "Space & Aerospace", subsector: "Launch",
    tags: ["launch", "reusable rocket"], description: "Rockets.", fundingStage: "Public", totalRaised: "$450K" },
  { name: "Zeta Équipe", status: "active", sector: "Space & Aerospace", subsector: "Launch",
    tags: [], description: "Small launcher.", techApproach: "Reusable launch vehicle", fundingStage: "Seed", totalRaised: "$40M" },
  // a comment between entries
];
'''


def theme(**over):
    t = {
        "id": "fusion-power",
        "title": "Fusion power",
        "imagined": "Power plants make energy by fusing atoms together.",
        "fiction": {"idea_id": "r1909", "entry": "Fusion Power", "work": "The Judas Valley", "author": "Gerald Vance", "year": 1956},
        "status": "demonstrated",
        "evidence": {"date": "2025-04-07", "publisher": "A Lab", "url": "https://lab.example.gov/shot", "fact": "A shot released more energy than the lasers delivered."},
        "gap": "No fusion machine has sold electricity.",
        "checked": "2026-11-25",
        "match": {"subsectors": ["Fusion"], "include": [], "exclude": []},
    }
    for k, v in over.items():
        if v is None:
            t.pop(k, None)
        else:
            t[k] = v
    return t


def rocket_theme(**over):
    base = theme(
        id="cheap-rides-to-orbit", title="Cheap rides to orbit", imagined="Flying to orbit becomes cheap.",
        fiction={"idea_id": "r3442", "entry": "Spaceplane", "work": "A Quantum Murder", "author": "Peter F. Hamilton", "year": 1998},
        status="built", match={"subsectors": ["Launch"]})
    base.update(over)
    return base


class Repo:
    """A throwaway repo folder with a data.js and a theme file."""

    def __init__(self, themes, data_js=DATA_JS):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "imagined").mkdir(parents=True)
        (self.root / "data.js").write_text(data_js, encoding="utf-8")
        self.write(themes)

    def write(self, themes):
        (self.root / "data" / "imagined" / "themes.json").write_text(
            json.dumps({"themes": themes}, ensure_ascii=False, indent=2), encoding="utf-8")

    def build(self):
        return bi.build(self.root, TODAY)

    def close(self):
        self.tmp.cleanup()


class TestThemeChecks(unittest.TestCase):
    def assertRefused(self, themes, fragment):
        repo = Repo(themes)
        try:
            with self.assertRaises(bi.ThemeError) as ctx:
                repo.build()
            self.assertIn(fragment, str(ctx.exception))
        finally:
            repo.close()

    def test_a_good_theme_builds(self):
        repo = Repo([theme()])
        try:
            payload, method, warnings = repo.build()
        finally:
            repo.close()
        self.assertEqual(warnings, [])
        self.assertEqual(payload["meta"]["themes"], 1)
        self.assertEqual(payload["themes"][0]["fiction"]["url"], "https://notboring.com/sci-fi-idea-bank?idea=r1909")
        self.assertIn("Not Boring", method)

    def test_unknown_status_is_refused(self):
        self.assertRefused([theme(status="almost")], "status must be one of")

    def test_status_needs_evidence(self):
        self.assertRefused([theme(evidence=None)], "needs evidence")

    def test_evidence_needs_a_date(self):
        ev = dict(theme()["evidence"], date="last spring")
        self.assertRefused([theme(evidence=ev)], "evidence.date")

    def test_evidence_must_be_https(self):
        ev = dict(theme()["evidence"], url="http://lab.example.gov/shot")
        self.assertRefused([theme(evidence=ev)], "https link")

    def test_the_idea_bank_is_never_the_evidence(self):
        for url in ("https://notboring.com/sci-fi-idea-bank?idea=r1909", "https://www.technovelgy.com/ct/x"):
            ev = dict(theme()["evidence"], url=url)
            self.assertRefused([theme(evidence=ev)], "primary source")

    def test_future_dated_evidence_is_refused(self):
        ev = dict(theme()["evidence"], date="2026-12-01")
        self.assertRefused([theme(evidence=ev)], "after 2026-11-25")

    def test_a_month_is_refused_only_when_wholly_in_the_future(self):
        ok = Repo([theme(evidence=dict(theme()["evidence"], date="2026-11"))])
        try:
            ok.build()
        finally:
            ok.close()
        self.assertRefused([theme(evidence=dict(theme()["evidence"], date="2026-12"))], "after 2026-11-25")

    def test_an_undated_page_needs_the_day_it_was_read(self):
        ev = dict(theme()["evidence"], date="undated")
        self.assertRefused([theme(evidence=ev)], "needs evidence.accessed")
        self.assertRefused([theme(evidence=dict(ev, accessed="2026-12-01"))], "after 2026-11-25")
        ok = Repo([theme(evidence=dict(ev, accessed="2026-11-20"))])
        try:
            payload, _, _ = ok.build()
        finally:
            ok.close()
        self.assertEqual(payload["themes"][0]["evidence"]["accessed"], "2026-11-20")

    def test_accessed_is_only_for_undated_pages(self):
        ev = dict(theme()["evidence"], accessed="2026-11-20")
        self.assertRefused([theme(evidence=ev)], "only for sources dated")

    def test_unknown_evidence_fields_are_refused(self):
        ev = dict(theme()["evidence"], quote="something")
        self.assertRefused([theme(evidence=ev)], "unknown evidence field")

    def test_checked_cannot_predate_the_evidence(self):
        self.assertRefused([theme(checked="2025-01-01")], "before the evidence date")

    def test_gap_line_is_required(self):
        self.assertRefused([theme(gap="  ")], "gap is missing")

    def test_length_limits(self):
        self.assertRefused([theme(gap="x" * (bi.LIMITS["gap"] + 1))], "limit")

    def test_no_em_dashes_in_public_copy(self):
        self.assertRefused([theme(imagined="Power plants — fusing atoms.")], "em dash")

    def test_idea_ids_look_like_the_idea_bank(self):
        fic = dict(theme()["fiction"], idea_id="1909")
        self.assertRefused([theme(fiction=fic)], "idea_id")

    def test_also_cannot_be_earlier_than_the_main_entry(self):
        also = [{"idea_id": "r2", "entry": "Older", "work": "Old Story", "author": "Someone", "year": 1900}]
        self.assertRefused([theme(also=also)], "earlier than the main entry")

    def test_duplicate_ids_and_titles(self):
        self.assertRefused([theme(), theme()], "used twice")
        self.assertRefused([theme(), theme(id="fusion-2")], "used twice")

    def test_unknown_fields_are_refused(self):
        self.assertRefused([theme(colour="red")], "unknown field")

    def test_bad_pattern_is_refused(self):
        self.assertRefused([theme(match={"pattern": "fusion("})], "does not compile")

    def test_match_needs_a_rule(self):
        self.assertRefused([theme(match={"include": [], "exclude": []})], "at least one")

    def test_include_and_exclude_cannot_clash(self):
        self.assertRefused([theme(match={"subsectors": ["Fusion"], "include": ["Beta Plasma"], "exclude": ["Beta Plasma"]})], "both included and excluded")

    def test_only_one_featured(self):
        self.assertRefused([theme(featured=True), rocket_theme(featured=True)], "only one theme can be featured")


class TestMatching(unittest.TestCase):
    def build(self, *themes):
        repo = Repo(list(themes))
        try:
            return repo.build()
        finally:
            repo.close()

    def names(self, payload, theme_id):
        t = next(t for t in payload["themes"] if t["id"] == theme_id)
        return [c["n"] for c in t["companies"]]

    def test_subsector_match_drops_dead_companies_and_orders_by_raised(self):
        payload, _, _ = self.build(theme())
        self.assertEqual(self.names(payload, "fusion-power"), ["Acme Fusion", "Beta Plasma"])

    def test_pattern_reads_short_fields_unless_wide(self):
        tight, _, _ = self.build(theme(match={"pattern": "fusion"}))
        self.assertNotIn("Gamma Grid", self.names(tight, "fusion-power"))      # only its description says fusion
        wide, _, _ = self.build(theme(match={"pattern": "fusion", "wide": True}))
        self.assertIn("Gamma Grid", self.names(wide, "fusion-power"))

    def test_tags_match_without_case(self):
        payload, _, _ = self.build(rocket_theme(match={"tags": ["Reusable Rocket"]}))
        self.assertEqual(self.names(payload, "cheap-rides-to-orbit"), ["Epsilon Rockets"])

    def test_include_and_exclude(self):
        payload, _, warnings = self.build(theme(match={"subsectors": ["Fusion"], "include": ["Gamma Grid"], "exclude": ["Beta Plasma"]}))
        self.assertEqual(self.names(payload, "fusion-power"), ["Acme Fusion", "Gamma Grid"])
        self.assertEqual(warnings, [])

    def test_missing_and_dead_names_warn_instead_of_guessing(self):
        _, _, warnings = self.build(theme(match={"subsectors": ["Fusion"], "include": ["Delta Dead", "Nobody Inc"], "exclude": ["Ghost Co"]}))
        self.assertTrue(any("Nobody Inc" in w for w in warnings))
        self.assertTrue(any("Ghost Co" in w for w in warnings))
        self.assertTrue(any("Delta Dead" in w and "dead" in w for w in warnings))

    def test_an_empty_theme_warns(self):
        _, _, warnings = self.build(theme(match={"pattern": "teleport"}))
        self.assertTrue(any("no company" in w for w in warnings))

    def test_public_companies_stay_in(self):
        payload, _, _ = self.build(rocket_theme())
        self.assertEqual(self.names(payload, "cheap-rides-to-orbit"), ["Zeta Équipe", "Epsilon Rockets"])

    def test_by_company_lists_every_theme_a_company_is_in(self):
        payload, _, _ = self.build(theme(), rocket_theme(match={"subsectors": ["Launch"], "include": ["Acme Fusion"]}))
        self.assertEqual(payload["by_company"]["acme-fusion"], ["fusion-power", "cheap-rides-to-orbit"])
        for slug, ids in payload["by_company"].items():
            for tid in ids:
                t = next(t for t in payload["themes"] if t["id"] == tid)
                self.assertIn(slug, [c["s"] for c in t["companies"]])

    def test_themes_are_ordered_by_story_year(self):
        payload, _, _ = self.build(rocket_theme(), theme())
        self.assertEqual([t["id"] for t in payload["themes"]], ["fusion-power", "cheap-rides-to-orbit"])

    def test_counts(self):
        payload, _, _ = self.build(theme(), rocket_theme())
        meta = payload["meta"]
        self.assertEqual(meta["companies"], 4)
        self.assertEqual(meta["by_status"], {"built": 1, "demonstrated": 1, "in_development": 0, "still_fiction": 0})
        self.assertEqual(meta["oldest_year"], 1956)
        self.assertEqual(meta["data_updated"], "2026-11-24")


class TestHelpers(unittest.TestCase):
    def test_slug_matches_utils_js(self):
        # companyToSlug() in utils.js: lower-case, drop anything but a-z 0-9 space hyphen,
        # spaces to hyphens, squeeze hyphens, trim hyphens.
        cases = {
            "Varda Space Industries": "varda-space-industries",
            "1X Technologies": "1x-technologies",
            "Zeta Équipe": "zeta-quipe",
            "X-Energy": "x-energy",
            "AT&T Labs": "att-labs",
            "  Odd -- Name  ": "odd-name",
            "The Biological Computing Co.": "the-biological-computing-co",
        }
        for name, slug in cases.items():
            self.assertEqual(bi.company_slug(name), slug, name)

    def test_raised(self):
        self.assertEqual(bi.raised_usd("$598M"), 598e6)
        self.assertEqual(bi.raised_usd("$1.2B"), 1.2e9)
        self.assertEqual(bi.raised_usd("~$56M"), 56e6)
        self.assertEqual(bi.raised_usd("$48.6M + $60M STRATFI"), 48.6e6)
        self.assertEqual(bi.raised_usd("$12,500,000"), 12.5e6)
        self.assertEqual(bi.raised_usd("Undisclosed"), 0.0)
        self.assertEqual(bi.raised_usd(""), 0.0)

    def test_parse_day(self):
        self.assertEqual(bi.parse_day("2025-04-07"), date(2025, 4, 7))
        self.assertEqual(bi.parse_day("2024-02"), date(2024, 2, 29))
        self.assertEqual(bi.parse_day("2001"), date(2001, 12, 31))
        self.assertIsNone(bi.parse_day("2025-13-01"))
        self.assertIsNone(bi.parse_day("April 2025"))


class TestOutputs(unittest.TestCase):
    def test_rebuild_gives_the_same_bytes_and_writes_nothing_new(self):
        repo = Repo([theme(), rocket_theme()])
        try:
            self.assertEqual(bi.main(["--root", str(repo.root), "--today", "2026-11-25"]), 0)
            first = (repo.root / bi.OUTPUTS["page"]).read_bytes()
            method = (repo.root / bi.OUTPUTS["method"]).read_bytes()
            self.assertEqual(bi.main(["--root", str(repo.root), "--today", "2026-11-25"]), 0)
            self.assertEqual((repo.root / bi.OUTPUTS["page"]).read_bytes(), first)
            self.assertEqual((repo.root / bi.OUTPUTS["method"]).read_bytes(), method)
            # The build date does not leak into the output: another day, same bytes.
            self.assertEqual(bi.main(["--root", str(repo.root), "--today", "2027-01-10"]), 0)
            self.assertEqual((repo.root / bi.OUTPUTS["page"]).read_bytes(), first)
        finally:
            repo.close()

    def test_page_file_is_one_const(self):
        repo = Repo([theme()])
        try:
            payload, _, _ = repo.build()
        finally:
            repo.close()
        text = bi.render_page_file(payload)
        m = re.search(r"^const IMAGINED = (\{.*\});$", text, re.M)
        self.assertIsNotNone(m)
        self.assertEqual(json.loads(m.group(1))["meta"]["themes"], 1)
        self.assertNotIn("_match", text)

    def test_a_bad_theme_file_leaves_the_old_output(self):
        repo = Repo([theme()])
        try:
            self.assertEqual(bi.main(["--root", str(repo.root), "--today", "2026-11-25"]), 0)
            before = (repo.root / bi.OUTPUTS["page"]).read_bytes()
            repo.write([theme(status="soon")])
            self.assertEqual(bi.main(["--root", str(repo.root), "--today", "2026-11-25"]), 1)
            self.assertEqual((repo.root / bi.OUTPUTS["page"]).read_bytes(), before)
        finally:
            repo.close()

    def test_strict_fails_on_warnings(self):
        repo = Repo([theme(match={"subsectors": ["Fusion"], "include": ["Nobody Inc"]})])
        try:
            self.assertEqual(bi.main(["--root", str(repo.root), "--today", "2026-11-25", "--check"]), 0)
            self.assertEqual(bi.main(["--root", str(repo.root), "--today", "2026-11-25", "--check", "--strict"]), 1)
        finally:
            repo.close()


class TestRealRepo(unittest.TestCase):
    """The checked-in theme file against today's data.js."""

    @classmethod
    def setUpClass(cls):
        cls.payload, cls.method, cls.warnings = bi.build(REPO, TODAY)
        cls.raw = json.loads((REPO / bi.INPUTS["themes"]).read_text(encoding="utf-8"))["themes"]

    def test_no_warnings(self):
        self.assertEqual(self.warnings, [])

    def test_every_theme_has_companies(self):
        for t in self.payload["themes"]:
            self.assertGreater(t["count"], 0, t["id"])

    def test_every_status_has_a_primary_dated_source(self):
        for t in self.payload["themes"]:
            ev = t["evidence"]
            self.assertTrue(ev["url"].startswith("https://"), t["id"])
            self.assertNotIn("notboring", ev["url"], t["id"])
            if ev["date"] == bi.UNDATED:
                self.assertIsNotNone(bi.parse_day(ev.get("accessed", "")), t["id"])
            else:
                self.assertIsNotNone(bi.parse_day(ev["date"]), t["id"])

    def test_one_featured_theme(self):
        self.assertEqual(sum(1 for t in self.payload["themes"] if t["featured"]), 1)

    def test_excluded_names_stay_out(self):
        for raw in self.raw:
            t = next(x for x in self.payload["themes"] if x["id"] == raw["id"])
            names = {c["n"] for c in t["companies"]}
            for name in raw["match"].get("exclude", []):
                self.assertNotIn(name, names, f"{raw['id']}: {name}")
            for name in raw["match"].get("include", []):
                self.assertIn(name, names, f"{raw['id']}: {name}")

    def test_checked_in_output_matches_the_theme_file(self):
        # Company lists move with data.js every day, so compare the parts the theme file owns.
        page = REPO / bi.OUTPUTS["page"]
        self.assertTrue(page.is_file(), "run python3 scripts/build_imagined.py")
        m = re.search(r"^const IMAGINED = (\{.*\});$", page.read_text(encoding="utf-8"), re.M)
        self.assertIsNotNone(m)
        shipped = {t["id"]: t for t in json.loads(m.group(1))["themes"]}
        for t in self.payload["themes"]:
            self.assertIn(t["id"], shipped, "data/imagined_auto.js is stale: run python3 scripts/build_imagined.py")
            for key in ("title", "imagined", "fiction", "status", "evidence", "gap", "checked"):
                self.assertEqual(shipped[t["id"]][key], t[key],
                                 f"{t['id']}.{key} is stale: run python3 scripts/build_imagined.py")


if __name__ == "__main__":
    unittest.main(verbosity=1)
