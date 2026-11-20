#!/usr/bin/env python3
"""
Tests for scripts/build_geo_places.py, the builder of data/geo/us_places.json.

    python3 -m unittest scripts/tests/test_geo_places.py
    python3 scripts/tests/test_geo_places.py

Offline, standard library only. The Census Gazetteer parser is exercised on
small files written here in the Gazetteer's own layout (tab-separated, the
legal description on the end of the place name, a trailing space after the
last header), because the real files are not in the repo. The last class
checks the file that IS in the repo.
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_geo_places as G  # noqa: E402
import enrich_jobs as E       # noqa: E402

PLACE_HEADER = "USPS\tGEOID\tANSICODE\tNAME\tLSAD\tFUNCSTAT\tALAND\tAWATER\tALAND_SQMI\tAWATER_SQMI\tINTPTLAT\tINTPTLONG                                                                                                              \n"
PLACE_ROWS = [
    "CA\t0616532\t02410239\tCosta Mesa city\t25\tA\t40600000\t70000\t15.7\t0.0\t33.6659\t-117.9123\n",
    "CA\t0665042\t02411779\tSan Buenaventura (Ventura) city\t25\tA\t56000000\t27000000\t21.7\t10.5\t34.2678\t-119.2542\n",
    "IN\t1836003\t02395423\tIndianapolis city (balance)\t00\tF\t936000000\t17000000\t361.6\t6.6\t39.7771\t-86.1458\n",
    "TN\t4752006\t02405092\tNashville-Davidson metropolitan government (balance)\t00\tF\t1232000000\t56000000\t475.8\t21.6\t36.1718\t-86.7850\n",
    "HI\t1571550\t02630783\tUrban Honolulu CDP\t57\tS\t156000000\t20000000\t60.5\t7.9\t21.3259\t-157.8453\n",
    "ID\t1608830\t02409876\tBoise City city\t25\tA\t217000000\t2400000\t84.0\t0.9\t43.6007\t-116.2312\n",
    # the same name twice in one state: the one with more land is kept
    "PA\t4211111\t01111111\tCenterville borough\t21\tA\t1000000\t0\t0.4\t0.0\t40.0000\t-80.0000\n",
    "PA\t4222222\t02222222\tCenterville borough\t21\tA\t9000000\t0\t3.5\t0.0\t41.7400\t-79.7600\n",
    # swapped coordinates must not get through
    "TX\t4899999\t09999999\tNowhere town\t43\tA\t1000\t0\t0.0\t0.0\t-97.7431\t30.2672\n",
]
ZCTA_HEADER = "GEOID\tALAND\tAWATER\tALAND_SQMI\tAWATER_SQMI\tINTPTLAT\tINTPTLONG                                             \n"
ZCTA_ROWS = [
    "92626\t30000000\t0\t11.6\t0.0\t33.6784\t-117.9085\n",
    "92627\t20000000\t0\t7.7\t0.0\t33.6480\t-117.9197\n",
    "00601\t166000000\t800000\t64.3\t0.3\t18.1806\t-66.7499\n",
    "99723\t10000000\t0\t3.9\t0.0\t71.2577\t-156.7944\n",
    "9262\t1\t0\t0\t0\t33.0\t-117.0\n",          # not five digits: ignored
]


def write_census(folder, zipped=False):
    folder = Path(folder)
    places, zcta = PLACE_HEADER + "".join(PLACE_ROWS), ZCTA_HEADER + "".join(ZCTA_ROWS)
    if zipped:
        with zipfile.ZipFile(folder / "2024_Gaz_place_national.zip", "w") as z:
            z.writestr("2024_Gaz_place_national.txt", places)
        with zipfile.ZipFile(folder / "2024_Gaz_zcta_national.zip", "w") as z:
            z.writestr("2024_Gaz_zcta_national.txt", zcta)
    else:
        (folder / "2024_Gaz_place_national.txt").write_text(places, encoding="utf-8")
        (folder / "2024_Gaz_zcta_national.txt").write_text(zcta, encoding="utf-8")


def town(payload, name, state):
    for row in payload["places"]:
        if row[0] == name and payload["states"][row[1]] == state:
            return row
    return None


class CensusNames(unittest.TestCase):
    def test_legal_description_is_dropped(self):
        for raw, want in [
            ("Costa Mesa city", "Costa Mesa"),
            ("Indianapolis city (balance)", "Indianapolis"),
            ("Nashville-Davidson metropolitan government (balance)", "Nashville-Davidson"),
            ("Urban Honolulu CDP", "Urban Honolulu"),
            ("Boise City city", "Boise City"),
            ("Juneau city and borough", "Juneau"),
            ("Anchorage municipality", "Anchorage"),
            ("Princeton borough", "Princeton"),
            ("Carson City", "Carson City"),          # no description to drop
        ]:
            self.assertEqual(G.clean_census_name(raw), want, raw)


class CensusBuild(unittest.TestCase):
    def build(self, zipped=False, repo=None):
        with tempfile.TemporaryDirectory() as tmp:
            write_census(tmp, zipped)
            return G.build(tmp, repo=repo or {})

    def test_places_and_zips_are_read(self):
        p = self.build()
        self.assertEqual(p["source"], "census")
        self.assertEqual(p["counts"]["zips"], 4)
        self.assertEqual(town(p, "Costa Mesa", "CA")[2:], [33.666, -117.912])
        self.assertIsNone(town(p, "Nowhere", "TX"), "swapped coordinates were accepted")
        self.assertEqual(town(p, "Centerville", "PA")[2:], [41.74, -79.76], "the larger of two same-named places wins")
        self.assertEqual(len([r for r in p["places"] if r[0] == "Centerville"]), 1)

    def test_zip_file_gives_the_same_result(self):
        zipped, plain = self.build(zipped=True), self.build(zipped=False)
        self.assertEqual(zipped["builtFrom"], ["2024_Gaz_place_national.zip", "2024_Gaz_zcta_national.zip"])
        zipped["builtFrom"] = plain["builtFrom"]
        self.assertEqual(G.render(zipped), G.render(plain))

    def test_other_spellings(self):
        p = self.build()
        places = p["places"]
        self.assertEqual(places[p["aliases"]["ventura|CA"]][0], "San Buenaventura")
        self.assertEqual(places[p["aliases"]["honolulu|HI"]][0], "Urban Honolulu")
        self.assertEqual(places[p["aliases"]["nashville|TN"]][0], "Nashville-Davidson")
        self.assertEqual(places[p["aliases"]["boise|ID"]][0], "Boise City")
        self.assertNotIn("nyc|", p["aliases"], "an alias must not point at a town the file lacks")

    def test_zip_packing_round_trip(self):
        p = self.build()
        self.assertEqual(sorted(p["zips"]), ["006", "926", "997"])
        self.assertEqual(len(p["zips"]["926"]), 16, "eight characters per ZIP code")
        self.assertEqual(G.unpack_zip(p["zips"], "92626"), (33.68, -117.91))
        self.assertEqual(G.unpack_zip(p["zips"], "92627"), (33.65, -117.92))
        self.assertEqual(G.unpack_zip(p["zips"], "00601"), (18.18, -66.75))
        self.assertEqual(G.unpack_zip(p["zips"], "99723"), (71.26, -156.79))
        self.assertIsNone(G.unpack_zip(p["zips"], "92628"))
        self.assertIsNone(G.unpack_zip(p["zips"], "10001"))

    def test_repo_towns_the_census_lacks_are_kept(self):
        repo = {E.place_key("Starbase", "TX"): ("Starbase", "TX", 25.9972, -97.1561),
                E.place_key("Costa Mesa", "CA"): ("Costa Mesa", "CA", 1.0, 1.0)}
        p = self.build(repo=repo)
        self.assertEqual(town(p, "Starbase", "TX")[2:], [25.997, -97.156])
        self.assertIn("repo data for 1 towns the Census file lacks", p["builtFrom"])
        self.assertEqual(town(p, "Costa Mesa", "CA")[2:], [33.666, -117.912], "the Census point wins over the repo's")

    def test_hub_falls_back_to_the_approximate_centre(self):
        p = self.build()
        hubs = {h[0]: h for h in p["hubs"]}
        self.assertEqual(list(hubs), list(E.HUB_ANCHORS))
        self.assertEqual(hubs["sf"][2:], [37.77, -122.42, 1], "no San Francisco in the fixture: approximate, and flagged")
        self.assertEqual(hubs["sf"][1], E.METROS["sf"])

    def test_newest_year_is_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_census(tmp)
            (Path(tmp) / "2023_Gaz_place_national.txt").write_text(PLACE_HEADER, encoding="utf-8")
            places, zcta = G.find_census_files(tmp)
            self.assertEqual((places.name, zcta.name), ("2024_Gaz_place_national.txt", "2024_Gaz_zcta_national.txt"))
        self.assertEqual(G.find_census_files("/nonexistent/folder"), (None, None))


class RepoFallback(unittest.TestCase):
    def repo(self, js_records, cache=None, curated=None):
        with tempfile.TemporaryDirectory() as tmp:
            js = Path(tmp) / "data.js"
            js.write_text("const COMPANIES = [\n" + ",\n".join(js_records) + "\n];\n", encoding="utf-8")
            cp = Path(tmp) / "geocode_cache.json"
            cp.write_text(json.dumps(cache or {}), encoding="utf-8")
            left_out = []
            return G.repo_places(js, cp, curated or {}, left_out), left_out

    @staticmethod
    def company(name, location, lat, lng, country="United States"):
        return '  { name: "%s", location: "%s", country: "%s", lat: %s, lng: %s }' % (name, location, country, lat, lng)

    def test_median_shrugs_off_one_bad_geocode(self):
        towns, _ = self.repo(
            [self.company("A", "Alameda, CA", 37.7652, -122.2416), self.company("B", "Alameda, CA", 37.7660, -122.2400),
             self.company("C", "Alameda, CA", 37.7652, -122.2416)],
            cache={"D|Alameda, CA|CA": {"lat": 37.609, "lng": -121.8991, "query": "Alameda, CA"},      # the county, not the town
                   "E|Alameda, CA|CA": {"lat": 37.7652, "lng": -122.2416, "query": "E Alameda, CA"}})
        self.assertEqual(towns["alameda|CA"], ("Alameda", "CA", 37.7652, -122.2416))

    def test_curated_point_wins(self):
        towns, _ = self.repo([self.company("A", "San Mateo, CA", 37.50, -122.33)], curated={"san mateo, ca": (37.563, -122.3255)})
        self.assertEqual(towns["san mateo|CA"], ("San Mateo", "CA", 37.563, -122.3255))

    def test_a_copied_point_is_left_out_not_guessed(self):
        towns, left_out = self.repo(
            [self.company("A", "Atlanta, GA", 33.749, -84.388), self.company("B", "Atlanta, GA", 33.749, -84.388),
             self.company("C", "Norcross, GA", 33.749, -84.388)])
        self.assertIn("atlanta|GA", towns)
        self.assertNotIn("norcross|GA", towns)
        self.assertEqual([(n, s) for n, s, _ in left_out], [("Norcross", "GA")])

    def test_two_single_points_that_coincide_both_go(self):
        towns, left_out = self.repo([self.company("A", "Kearny, NJ", 40.677, -74.29), self.company("B", "Kenilworth, NJ", 40.677, -74.287)])
        self.assertEqual(towns, {})
        self.assertEqual(sorted(n for n, _, _ in left_out), ["Kearny", "Kenilworth"])

    def test_foreign_and_broken_rows_are_ignored(self):
        towns, _ = self.repo([self.company("A", "Munich, Germany", 48.1, 11.6, "Germany"),
                              self.company("B", "Austin, TX", 0, 0), self.company("C", "Somewhere", 30.0, -97.0)])
        self.assertEqual(towns, {})

    def test_not_trusted_list_is_applied(self):
        towns, left_out = self.repo([self.company("A", "San Bernardino, CA", 34.825, -116.083)])
        self.assertEqual(towns, {})
        self.assertEqual(left_out[0][:2], ("San Bernardino", "CA"))


class DowngradeGuard(unittest.TestCase):
    def run_main(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return G.main(list(args))

    def test_a_repo_build_does_not_replace_a_census_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, empty, out = Path(tmp) / "src", Path(tmp) / "empty", Path(tmp) / "us_places.json"
            src.mkdir()
            empty.mkdir()
            write_census(src)
            self.assertEqual(self.run_main("--src", str(src), "--out", str(out)), 0)
            census = out.read_text(encoding="utf-8")
            self.assertIn('"source":"census"', census)
            self.assertEqual(self.run_main("--src", str(src), "--out", str(out), "--check"), 0)
            # the Census files have gone missing: refuse, and leave the file alone
            self.assertEqual(self.run_main("--src", str(empty), "--out", str(out)), 1)
            self.assertEqual(out.read_text(encoding="utf-8"), census)
            self.assertEqual(self.run_main("--src", str(empty), "--out", str(out), "--check"), 1)
            self.assertEqual(self.run_main("--src", str(empty), "--out", str(out), "--allow-fallback"), 0)
            self.assertIn('"source":"repo"', out.read_text(encoding="utf-8"))


class Rendering(unittest.TestCase):
    def test_render_is_valid_json_and_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_census(tmp)
            payload = G.build(tmp, repo={})
        text = G.render(payload)
        self.assertEqual(json.loads(text), json.loads(json.dumps(payload)))
        self.assertEqual(text, G.render(payload))
        self.assertTrue(text.endswith("}\n"))

    def test_base36_bounds(self):
        self.assertEqual(G.b36(0, 3), "000")
        self.assertEqual(G.b36(36 ** 3 - 1, 3), "zzz")
        with self.assertRaises(ValueError):
            G.b36(36 ** 3, 3)


class FileInTheRepo(unittest.TestCase):
    """data/geo/us_places.json as committed."""

    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "data" / "geo" / "us_places.json"
        cls.payload = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_schema(self):
        p = self.payload
        self.assertEqual(p["schema"], G.SCHEMA)
        self.assertIn(p["source"], ("repo", "census"))
        self.assertEqual(p["counts"]["places"], len(p["places"]))
        self.assertEqual(p["counts"]["hubs"], len(p["hubs"]))
        self.assertEqual(p["counts"]["zips"], sum(len(v) // 8 for v in p["zips"].values()))
        if p["source"] == "repo":
            self.assertEqual(p["zips"], {}, "the fallback has no ZIP data and must not pretend to")

    def test_every_point_is_in_the_united_states(self):
        for name, state_index, lat, lng in self.payload["places"]:
            self.assertTrue(G.plausible_us_point(lat, lng), name)
            self.assertIn(self.payload["states"][state_index], E.US_STATE_CODES, name)

    def test_sorted_and_unique(self):
        p = self.payload
        keys = [E.place_key(r[0], p["states"][r[1]]) for r in p["places"]]
        self.assertEqual(len(keys), len(set(keys)))
        order = [(p["states"][r[1]], E.norm_place(r[0]), r[0]) for r in p["places"]]
        self.assertEqual(order, sorted(order))

    def test_hubs_are_the_metro_rules_hubs(self):
        hubs = self.payload["hubs"]
        self.assertEqual([h[0] for h in hubs], [c for c in E.METRO_RULES])
        for code, label, lat, lng, approx in hubs:
            self.assertEqual(label, E.METROS[code])
            self.assertTrue(G.plausible_us_point(lat, lng), code)
            near = G.APPROX_HUB_CENTRES[code]
            self.assertLess(E.haversine_miles(lat, lng, near[0], near[1]), 5, "%s hub is far from its main town" % code)

    def test_aliases_point_at_real_rows(self):
        p = self.payload
        for key, i in p["aliases"].items():
            self.assertTrue(0 <= i < len(p["places"]), key)
        nyc = p["places"][p["aliases"]["nyc|"]]
        self.assertEqual((nyc[0], p["states"][nyc[1]]), ("New York", "NY"))

    def test_no_two_towns_share_a_point(self):
        rows = self.payload["places"]
        if self.payload["source"] != "repo":
            self.skipTest("only the repo fallback is checked for copied points")
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                self.assertGreater(E.haversine_miles(a[2], a[3], b[2], b[3]), G.SAME_POINT_MILES, "%s / %s" % (a[0], b[0]))

    def test_rebuild_reminder(self):
        # Not a pass/fail check: the fallback file is built from data.js, which gains companies
        # every week, so an older file is expected. The skip message is the reminder to rebuild.
        if self.path.read_text(encoding="utf-8") != G.render(G.build()):
            self.skipTest("data/geo/us_places.json is older than the data it is built from: "
                          "run python3 scripts/build_geo_places.py")


if __name__ == "__main__":
    unittest.main(verbosity=1)
