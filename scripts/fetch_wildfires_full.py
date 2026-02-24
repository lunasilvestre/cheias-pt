#!/usr/bin/env python3
"""
Fetch full-resolution wildfire burned area polygons from EFFIS WFS.

Downloads ms:modis.ba.poly features for Portugal, filters to 2024-2025
fires >= 30 ha, and saves as full-resolution GeoJSON (no simplification).

Output:
  data/qgis/wildfires-2024.geojson
  data/qgis/wildfires-2025.geojson
  /tmp/wildfires-combined-full.geojson (for tippecanoe input)
"""

import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# --- Configuration ---
WFS_BASE = "https://maps.effis.emergency.copernicus.eu/effis"
TYPENAME = "ms:modis.ba.poly"
BBOX = "36.9,-9.6,42.2,-6.1,EPSG:4326"
PAGE_SIZE = 5000
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "qgis"
TMP_COMBINED = Path("/tmp/wildfires-combined-full.geojson")

# Years to include
TARGET_YEARS = {2024, 2025}
MIN_AREA_HA = 30


def build_url(start_index: int) -> str:
    """Build WFS GetFeature URL with pagination."""
    params = {
        "SERVICE": "WFS",
        "REQUEST": "GetFeature",
        "VERSION": "2.0.0",
        "TYPENAMES": TYPENAME,
        "OUTPUTFORMAT": "application/json; subtype=geojson",
        "BBOX": BBOX,
        "SRSNAME": "EPSG:4326",
        "COUNT": str(PAGE_SIZE),
        "STARTINDEX": str(start_index),
    }
    return WFS_BASE + "?" + urllib.parse.urlencode(params)


def fetch_page(start_index: int, attempt: int = 0) -> dict:
    """Fetch one page of WFS results with retry."""
    url = build_url(start_index)
    print(f"  Fetching STARTINDEX={start_index} ...", end=" ", flush=True)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "cheias-pt/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        n = len(data.get("features", []))
        print(f"got {n} features")
        return data
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        if attempt < 3:
            wait = 5 * (attempt + 1)
            print(f"error ({e}), retrying in {wait}s ...")
            time.sleep(wait)
            return fetch_page(start_index, attempt + 1)
        raise


def extract_fire_year(props: dict) -> int | None:
    """Extract fire year from EFFIS properties."""
    # Try FIREDATE first (format: YYYY/MM/DD or YYYY-MM-DD)
    firedate = props.get("FIREDATE") or props.get("firedate") or ""
    if firedate and len(firedate) >= 4:
        try:
            return int(firedate[:4])
        except ValueError:
            pass

    # Try YEAR field
    year = props.get("YEAR") or props.get("year")
    if year is not None:
        try:
            return int(year)
        except (ValueError, TypeError):
            pass

    # Try ID field (sometimes encodes year)
    return None


def extract_area_ha(props: dict) -> float:
    """Extract area in hectares from EFFIS properties."""
    for key in ("AREA_HA", "area_ha", "Area_HA", "AREAHA"):
        val = props.get(key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
    return 0.0


def normalize_properties(props: dict, fire_year: int, area_ha: float) -> dict:
    """Build clean output properties matching our schema."""
    firedate = props.get("FIREDATE") or props.get("firedate") or ""
    # Normalize date separator
    fire_date = firedate.replace("/", "-") if firedate else ""

    return {
        "fire_year": fire_year,
        "fire_date": fire_date,
        "area_ha": round(area_ha, 1),
        "country": (props.get("COUNTRY") or props.get("country") or "").strip(),
        "province": (props.get("PROVINCE") or props.get("province") or "").strip(),
        "commune": (props.get("COMMUNE") or props.get("commune") or "").strip(),
        "broadleaf_pct": _float(props, "BROADLEAV") or _float(props, "broadleaf_pct"),
        "conifer_pct": _float(props, "CONIFER") or _float(props, "conifer_pct"),
        "mixed_pct": _float(props, "MIXED") or _float(props, "mixed_pct"),
        "sclerophyll_pct": _float(props, "SCLEROPH") or _float(props, "sclerophyll_pct"),
        "agriculture_pct": _float(props, "AGRICULTU") or _float(props, "agriculture_pct"),
        "effis_id": str(props.get("ID") or props.get("id") or props.get("effis_id") or ""),
    }


def _float(d: dict, key: str) -> float:
    """Safely extract float from dict."""
    v = d.get(key)
    if v is None:
        return 0.0
    try:
        return round(float(v), 6)
    except (ValueError, TypeError):
        return 0.0


def main():
    print("=== EFFIS Wildfire Full-Resolution Fetch ===")
    print(f"Target: Portugal, years {sorted(TARGET_YEARS)}, area >= {MIN_AREA_HA} ha")
    print()

    # --- Fetch all pages ---
    all_raw_features = []
    start_index = 0

    while True:
        page = fetch_page(start_index)
        features = page.get("features", [])
        all_raw_features.extend(features)

        if len(features) < PAGE_SIZE:
            break
        start_index += PAGE_SIZE
        time.sleep(1)  # Be polite to the WFS

    print(f"\nTotal raw features from WFS: {len(all_raw_features)}")

    # --- Filter and normalize ---
    by_year: dict[int, list] = {y: [] for y in TARGET_YEARS}

    for feat in all_raw_features:
        props = feat.get("properties", {})

        # Country filter
        country = (props.get("COUNTRY") or props.get("country") or "").strip().upper()
        if country != "PT":
            continue

        # Year filter
        fire_year = extract_fire_year(props)
        if fire_year not in TARGET_YEARS:
            continue

        # Area filter
        area_ha = extract_area_ha(props)
        if area_ha < MIN_AREA_HA:
            continue

        # Normalize and keep
        clean_props = normalize_properties(props, fire_year, area_ha)
        clean_feat = {
            "type": "Feature",
            "geometry": feat["geometry"],
            "properties": clean_props,
        }
        by_year[fire_year].append(clean_feat)

    # --- Summary ---
    total_features = sum(len(v) for v in by_year.values())
    print(f"\nFiltered features: {total_features}")
    for year in sorted(TARGET_YEARS):
        feats = by_year[year]
        total_ha = sum(f["properties"]["area_ha"] for f in feats)
        print(f"  {year}: {len(feats):,} fires, {total_ha:,.0f} ha")

    if total_features == 0:
        print("ERROR: No features matched filters. Check WFS response.")
        sys.exit(1)

    # --- Save per-year GeoJSON ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for year in sorted(TARGET_YEARS):
        feats = by_year[year]
        geojson = {"type": "FeatureCollection", "features": feats}
        out_path = OUTPUT_DIR / f"wildfires-{year}.geojson"
        with open(out_path, "w") as f:
            json.dump(geojson, f)
        size_mb = out_path.stat().st_size / 1024 / 1024
        print(f"\nSaved {out_path} ({size_mb:.1f} MB, {len(feats)} features)")

    # --- Save combined for tippecanoe ---
    combined_feats = []
    for year in sorted(TARGET_YEARS):
        combined_feats.extend(by_year[year])

    combined_geojson = {"type": "FeatureCollection", "features": combined_feats}
    with open(TMP_COMBINED, "w") as f:
        json.dump(combined_geojson, f)
    size_mb = TMP_COMBINED.stat().st_size / 1024 / 1024
    print(f"\nSaved {TMP_COMBINED} ({size_mb:.1f} MB, {len(combined_feats)} features)")

    # --- Coordinate complexity report ---
    print("\n=== Geometry Complexity ===")
    for year in sorted(TARGET_YEARS):
        total_coords = 0
        for feat in by_year[year]:
            geom = feat["geometry"]
            if geom["type"] == "MultiPolygon":
                total_coords += sum(
                    len(ring) for poly in geom["coordinates"] for ring in poly
                )
            elif geom["type"] == "Polygon":
                total_coords += sum(len(ring) for ring in geom["coordinates"])
        print(f"  {year}: {total_coords:,} coordinate pairs")

    print("\nDone.")


if __name__ == "__main__":
    main()
