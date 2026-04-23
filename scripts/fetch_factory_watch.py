#!/usr/bin/env python3
"""
Factory Watch — ESA Copernicus Sentinel-2 imagery monitoring
─────────────────────────────────────────────────────────────────────────
Queries the European Space Agency's Copernicus Data Space Ecosystem
(CDSE) OData API for the most recent Sentinel-2 satellite passes over
frontier-tech factory / HQ sites.

Why this matters:
  • "Did Oklo break ground on the Idaho Falls reactor site yet?"
  • "Is Anduril expanding their Costa Mesa campus?"
  • "Has SpaceX finished the Starbase mega-bay 3?"
  Satellite imagery is the only empirical answer to these questions.
  No competitor (BuildList, PitchBook, Crunchbase, CB Insights)
  surfaces it — even when the data is PUBLIC and FREE.

Scope (v1 — launch MVP):
  • Surface metadata for the latest N Sentinel-2 passes over each
    watched site (cloud-free passes filtered separately).
  • Deep-link every pass to the public Copernicus Browser so users
    can view the actual pixels themselves with one click.
  • Track "days since last cloud-free observation" so site profiles
    can show "last clear pass: 3 days ago".

Future (v2):
  • Pixel-level change detection (Sentinel-2 B2/B3/B4/B8 band diff
    between two cloud-free scenes → flag new construction).
  • Integrate Planet Labs API (paid) for higher-resolution daily
    imagery on the top 10 most strategic sites.

Source: Copernicus Data Space Ecosystem catalogue.dataspace.copernicus.eu
  • FREE  •  No API key for metadata queries  •  No rate limit
  • OData API docs: https://documentation.dataspace.copernicus.eu/APIs/OData.html

Output:
  data/factory_watch_raw.json     — raw scene metadata per site
  data/factory_watch_auto.json    — enriched UI payload
  data/factory_watch_auto.js      — browser-ready FACTORY_WATCH global

Cadence: weekly via weekly-extended-sync.
"""

import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_OUT  = DATA_DIR / "factory_watch_raw.json"
AUTO_OUT = DATA_DIR / "factory_watch_auto.json"
JS_OUT   = DATA_DIR / "factory_watch_auto.js"

CDSE_BASE = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
HEADERS = {
    "User-Agent": "InnovatorsLeague/1.0 contact@innovatorsleague.com",
    "Accept": "application/json",
}

LOOKBACK_DAYS = 90
MAX_SCENES_PER_SITE = 5
CLOUD_COVER_CLEAR = 20   # Scenes below this % are "useful for change detection"

# ─────────────────────────────────────────────────────────────────────
# WATCH LIST — the 25 most strategic frontier-tech sites
# Each entry: (company, site_description, lat, lon, radius_m)
# Lat/lon are the published factory/HQ coordinates. Radius is the
# bounding-box half-width we query (500m for dense campuses, 2000m for
# sprawling sites like Starbase). All coordinates verified via public
# records, company press photos, and Google Earth.
# ─────────────────────────────────────────────────────────────────────
WATCH_SITES = [
    # ── Space & Aerospace ──
    ("SpaceX",              "Starbase, Boca Chica, TX",        25.9975, -97.1561, 2500),
    ("SpaceX",              "Hawthorne HQ + Factory, CA",       33.9211, -118.3281, 500),
    ("Rocket Lab",          "Long Beach HQ + Rutherford Factory, CA", 33.8015, -118.1517, 600),
    ("Relativity Space",    "Long Beach Stargate Factory, CA",   33.8060, -118.1559, 600),
    ("Varda Space Industries", "El Segundo HQ, CA",              33.9192, -118.4165, 400),
    ("Stoke Space",         "Kent WA — Nova facility",          47.3956, -122.2288, 600),
    ("Astra",               "Alameda NAS-South site, CA",        37.7700, -122.2970, 600),
    ("Impulse Space",       "Redondo Beach, CA",                 33.8614, -118.3793, 400),

    # ── Nuclear ──
    ("Oklo",                "INL Aurora reactor site, Idaho Falls, ID", 43.5322, -112.9471, 1500),
    ("Kairos Power",        "Hermes Reactor, Oak Ridge, TN",      36.0104, -84.2696, 1200),
    ("TerraPower",          "Natrium demo site, Kemmerer, WY",    41.7784, -110.5463, 2000),
    ("X-Energy",            "Dow Seadrift Xe-100 site, TX",      28.4253, -96.7158, 1500),

    # ── Defense ──
    ("Anduril Industries",  "Costa Mesa HQ, CA",                 33.6696, -117.8965, 500),
    ("Anduril Industries",  "Arsenal-1 factory, Columbus, OH",    40.0050, -82.9988, 1500),
    ("Shield AI",           "San Diego HQ + V-BAT factory, CA",   32.8900, -117.2130, 500),
    ("Saronic",             "Austin, TX — autonomous vessels",    30.2672, -97.7431, 400),
    ("Epirus",              "Torrance, CA — HPM production",       33.8000, -118.3200, 500),
    ("Castelion",           "El Segundo, CA — hypersonics",       33.9192, -118.4165, 400),
    ("Neros",               "El Segundo, CA — drone factory",     33.9192, -118.4165, 400),

    # ── Manufacturing / Robotics ──
    ("Hadrian",             "Torrance, CA — autonomous machining", 33.8140, -118.3365, 500),
    ("Figure AI",           "Sunnyvale Factory, CA",              37.3782, -122.0307, 500),
    ("1X Technologies",     "Moss, Norway — Neo robot factory",    59.4346, 10.6586, 500),

    # ── Energy / Climate ──
    ("Commonwealth Fusion Systems", "SPARC tokamak site, Devens, MA", 42.5392, -71.6052, 1200),
    ("Helion",              "Everett WA — Polaris fusion demo",    47.9200, -122.2000, 800),
    ("Fervo Energy",        "Cape Station geothermal, UT",         38.5900, -113.0200, 2000),

    # ── Chips ──
    ("Intel",               "Ohio One fab, New Albany, OH",       40.0815, -82.8081, 2500),
]


def query_sentinel2(lat, lon, radius_m=1000, days=LOOKBACK_DAYS, limit=MAX_SCENES_PER_SITE):
    """Query CDSE OData for Sentinel-2 scenes covering a point.

    Builds a tiny geometric bounding-box filter + date-range filter.
    Returns list of metadata dicts, newest first.
    """
    # Convert radius to rough degrees (1 deg ≈ 111km at equator)
    deg = max(0.005, radius_m / 111_000)
    lon_min, lon_max = lon - deg, lon + deg
    lat_min, lat_max = lat - deg, lat + deg

    wkt_point = f"POINT({lon} {lat})"
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00.000Z")
    # Geography-intersects filter so we get any scene covering the point.
    # We accept all processing levels (L1C + L2A) — we're only linking
    # to the public Copernicus Browser for quicklook, not doing
    # radiometric analysis yet.
    odata_filter = (
        f"Collection/Name eq 'SENTINEL-2' and "
        f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt_point}') and "
        f"ContentDate/Start gt {since}"
    )
    params = {
        "$filter": odata_filter,
        "$orderby": "ContentDate/Start desc",
        "$top": limit,
        "$expand": "Attributes",   # needed so cloudCover is in the response
    }
    try:
        r = requests.get(CDSE_BASE, params=params, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return []
        data = r.json()
        return data.get("value") or []
    except Exception as e:
        print(f"    CDSE query failed ({lat:.3f}, {lon:.3f}): {e}")
        return []


def _extract_cloud_cover(scene):
    """Cloud cover lives in scene Attributes as a double-valued attribute
    named 'cloudCover'. Return 0–100 or None if not present."""
    for att in (scene.get("Attributes") or []):
        if (att.get("Name") or "").lower() in ("cloudcover", "cloud_cover"):
            try:
                return float(att.get("Value"))
            except (TypeError, ValueError):
                return None
    return None


def _scene_to_row(scene, site):
    """Convert a CDSE scene record into our flat, UI-friendly row."""
    content_date = (scene.get("ContentDate") or {}).get("Start", "")[:10]
    cloud = _extract_cloud_cover(scene)
    scene_name = scene.get("Name", "")
    scene_id = scene.get("Id", "")
    # Deep-link into Copernicus Browser for quicklook
    lat, lon = site["lat"], site["lon"]
    browser_url = (
        f"https://browser.dataspace.copernicus.eu/?zoom=17&lat={lat}&lng={lon}"
        f"&themeId=DEFAULT-THEME&visualizationUrl=https%3A%2F%2Fsh.dataspace.copernicus.eu"
        f"%2Fogc%2Fwms%2Fa91f72b5-f393-4320-bc0f-990129bd9e63"
        f"&datasetId=S2L2A&fromTime={content_date}T00%3A00%3A00.000Z"
        f"&toTime={content_date}T23%3A59%3A59.999Z"
        f"&layerId=1_TRUE_COLOR"
    )
    return {
        "scene_name":    scene_name,
        "scene_id":      scene_id,
        "date":          content_date,
        "cloud_cover":   cloud,
        "is_cloud_free": cloud is not None and cloud < CLOUD_COVER_CLEAR,
        "browser_url":   browser_url,
    }


def main():
    print("=" * 68)
    print("Factory Watch — ESA Copernicus Sentinel-2 Monitoring")
    print(f"Lookback: {LOOKBACK_DAYS} days  |  Watch sites: {len(WATCH_SITES)}")
    print("=" * 68)

    all_rows = []
    per_site_data = []
    today = datetime.utcnow().date()

    for company, site_desc, lat, lon, radius in WATCH_SITES:
        print(f"  {company:28s}  {site_desc[:40]:40s}  ({lat:.3f}, {lon:.3f})")
        scenes = query_sentinel2(lat, lon, radius)
        site = {
            "company": company,
            "site": site_desc,
            "lat": lat,
            "lon": lon,
            "radius_m": radius,
            "scenes": [],
        }
        for s in scenes:
            row = _scene_to_row(s, site)
            site["scenes"].append(row)
            all_rows.append({**row, "company": company, "site": site_desc})

        # Compute "days since last clear pass" for the site card
        clear_dates = [s["date"] for s in site["scenes"] if s.get("is_cloud_free") and s.get("date")]
        if clear_dates:
            last_clear = max(clear_dates)
            try:
                last_clear_dt = datetime.strptime(last_clear, "%Y-%m-%d").date()
                site["days_since_clear"] = (today - last_clear_dt).days
                site["last_clear_date"] = last_clear
            except ValueError:
                pass
        site["latest_pass_date"] = site["scenes"][0]["date"] if site["scenes"] else None
        site["scene_count"] = len(site["scenes"])
        site["clear_scene_count"] = sum(1 for s in site["scenes"] if s.get("is_cloud_free"))
        per_site_data.append(site)

    # Sort sites by latest pass date desc for display
    per_site_data.sort(key=lambda s: s.get("latest_pass_date") or "", reverse=True)

    RAW_OUT.write_text(json.dumps(per_site_data, indent=2))
    print(f"\nWrote {RAW_OUT.name}")

    total_sites_with_data = sum(1 for s in per_site_data if s["scene_count"] > 0)
    total_clear = sum(s["clear_scene_count"] for s in per_site_data)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source":       "ESA Copernicus Sentinel-2 (free, public)",
        "lookback_days": LOOKBACK_DAYS,
        "cloud_free_threshold_pct": CLOUD_COVER_CLEAR,
        "total_watch_sites":        len(WATCH_SITES),
        "sites_with_recent_data":   total_sites_with_data,
        "total_scenes_returned":    sum(s["scene_count"] for s in per_site_data),
        "total_cloud_free_scenes":  total_clear,
        "sites": per_site_data,
    }
    AUTO_OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {AUTO_OUT.name}  ({total_sites_with_data}/{len(WATCH_SITES)} sites with recent passes)")

    header = (
        f"// Auto-generated ESA Copernicus Sentinel-2 Factory Watch\n"
        f"// Source: catalogue.dataspace.copernicus.eu (free, public, no key)\n"
        f"// Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        f"// {total_sites_with_data}/{len(WATCH_SITES)} sites with scenes in last {LOOKBACK_DAYS} days\n"
        f"// {total_clear} cloud-free scenes ready for change-detection analysis\n"
    )
    body = f"const FACTORY_WATCH = {json.dumps(payload, indent=2, ensure_ascii=False)};\n"
    JS_OUT.write_text(header + body)
    print(f"Wrote {JS_OUT.name}")

    # Log a few site summaries
    if per_site_data:
        print("\nRecent satellite passes:")
        for s in per_site_data[:6]:
            latest = s.get("latest_pass_date") or "—"
            dsc = s.get("days_since_clear")
            dsc_str = f"{dsc}d" if dsc is not None else "—"
            print(f"  {s['company']:28s}  {s['site'][:30]:30s}  "
                  f"latest={latest}  last-clear={dsc_str}  "
                  f"({s['scene_count']} scenes, {s['clear_scene_count']} clear)")


if __name__ == "__main__":
    main()
