#!/usr/bin/env python3
"""
fetch_lightning.py — Fetch lightning flash data from EUMETSAT MTG Lightning Imager (LI)

The MTG Lightning Imager (LI) on Meteosat-12 (MTG-I1) is the first operational
geostationary lightning sensor covering Europe. Pre-operational Level 2 data
has been available since July 8, 2024.

Collection: EO:EUM:DAT:0691 (MTG-I LI Level 2 — Lightning Flash)
Temporal resolution: 10-minute chunks
Format: NetCDF4 (CHK-BODY = flash data with lat/lon/time/radiance/duration)
Coverage: Full disk (Europe, Africa, South America visible from 0° longitude)
Spatial resolution: ~4.5 km at sub-satellite point

Requirements:
- EUMETSAT credentials (free registration at https://eoportal.eumetsat.int)
- Set EUMETSAT_CONSUMER_KEY and EUMETSAT_CONSUMER_SECRET in .env or as env vars

Usage:
    python scripts/fetch_lightning.py                    # Download & convert to GeoJSON
    python scripts/fetch_lightning.py --start 2026-01-27 --end 2026-01-29
    python scripts/fetch_lightning.py --list-only        # Just list available products
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import netCDF4 as nc
import numpy as np
import requests

# --- Configuration ---
COLLECTION_ID = "EO:EUM:DAT:0691"  # LFL = Lightning Flash Level 2
SEARCH_API = "https://api.eumetsat.int/data/search-products/1.0.0/os"
TOKEN_URL = "https://api.eumetsat.int/token"

# Iberian Peninsula bounding box for spatial filtering
BBOX_WEST = -12.0
BBOX_EAST = 5.0
BBOX_SOUTH = 35.0
BBOX_NORTH = 45.0

OUT_DIR = Path(__file__).parent.parent / "data" / "lightning"
QGIS_DIR = Path(__file__).parent.parent / "data" / "qgis"


def get_credentials():
    """Load EUMETSAT credentials from env vars or .env file."""
    key = os.environ.get("EUMETSAT_CONSUMER_KEY") or os.environ.get("EUMETSAT_KEY")
    secret = os.environ.get("EUMETSAT_CONSUMER_SECRET") or os.environ.get("EUMETSAT_SECRET")
    if key and secret:
        return key, secret

    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        creds = {}
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                creds[k.strip()] = v.strip()
        key = creds.get("EUMETSAT_CONSUMER_KEY") or creds.get("EUMETSAT_KEY")
        secret = creds.get("EUMETSAT_CONSUMER_SECRET") or creds.get("EUMETSAT_SECRET")
        if key and secret:
            return key, secret

    return None, None


def get_access_token(key, secret):
    """Get EUMETSAT OAuth2 access token."""
    r = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(key, secret),
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def search_products(start, end):
    """Search for MTG-LI LFL products in the given time range.

    Queries in 6-hour chunks to avoid the EUMETSAT search API's pagination
    issues with large time ranges (it returns duplicates across pages).
    """
    from datetime import datetime, timedelta

    dt_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
    dt_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
    chunk = timedelta(hours=6)

    seen_ids = set()
    all_products = []
    current = dt_start

    while current < dt_end:
        chunk_end = min(current + chunk, dt_end)
        r = requests.get(
            SEARCH_API,
            params={
                "pi": COLLECTION_ID,
                "format": "json",
                "dtstart": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "dtend": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "itemsPerPage": 100,
                "sort": "start,time,1",
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

        for feat in data["features"]:
            pid = feat["properties"]["identifier"]
            if pid not in seen_ids:
                seen_ids.add(pid)
                all_products.append(feat)

        current = chunk_end

    return all_products


def download_nc(product, token, tmpdir):
    """Download the CHK-BODY NetCDF file from a product."""
    entries = product["properties"]["links"].get("sip-entries", [])
    body_entry = None
    for entry in entries:
        if (entry.get("mediaType") == "application/x-netcdf"
                and "CHK-BODY" in entry.get("title", "")):
            body_entry = entry
            break

    if not body_entry:
        return None

    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(body_entry["href"], headers=headers, timeout=120)
    if r.status_code == 401:
        return "AUTH_EXPIRED"
    r.raise_for_status()

    nc_path = Path(tmpdir) / f"lfl_{hash(body_entry['href']) & 0xFFFFFFFF:08x}.nc"
    nc_path.write_bytes(r.content)
    return nc_path


def extract_flashes(nc_path):
    """Extract Iberian flash records from LFL NetCDF.

    LFL CHK-BODY variables (root level, dimension: 'flashes'):
      latitude       int16 (scale_factor=0.0027) degrees_north
      longitude      int16 (scale_factor=0.0027) degrees_east
      flash_time     float64 seconds since 2000-01-01 00:00:00.0
      radiance       uint16 mW.m-2.sr-1
      flash_duration uint16 ms
      number_of_groups  uint16
      number_of_events  uint16
      flash_filter_confidence uint8
    """
    ds = nc.Dataset(str(nc_path), "r")
    flashes = []

    try:
        if "flashes" not in ds.dimensions or ds.dimensions["flashes"].size == 0:
            return []

        lats = ds.variables["latitude"][:]
        lons = ds.variables["longitude"][:]

        mask = (
            (lats >= BBOX_SOUTH) & (lats <= BBOX_NORTH)
            & (lons >= BBOX_WEST) & (lons <= BBOX_EAST)
        )

        if not np.any(mask):
            return []

        times = ds.variables["flash_time"][mask]
        time_units = ds.variables["flash_time"].units
        timestamps = nc.num2date(times, time_units)

        f_lats = lats[mask]
        f_lons = lons[mask]
        f_rad = ds.variables["radiance"][mask]
        f_dur = ds.variables["flash_duration"][mask]
        f_groups = ds.variables["number_of_groups"][mask]
        f_events = ds.variables["number_of_events"][mask]

        for i in range(len(f_lats)):
            # Skip entries with masked (fill) values
            if np.ma.is_masked(f_lats[i]) or np.ma.is_masked(f_lons[i]):
                continue
            rad = int(f_rad[i]) if not np.ma.is_masked(f_rad[i]) else 0
            dur = int(f_dur[i]) if not np.ma.is_masked(f_dur[i]) else 0
            grp = int(f_groups[i]) if not np.ma.is_masked(f_groups[i]) else 0
            evt = int(f_events[i]) if not np.ma.is_masked(f_events[i]) else 0
            flashes.append({
                "lat": round(float(f_lats[i]), 4),
                "lon": round(float(f_lons[i]), 4),
                "timestamp": str(timestamps[i]),
                "radiance": rad,
                "duration_ms": dur,
                "groups": grp,
                "events": evt,
            })
    finally:
        ds.close()

    return flashes


def write_geojson(flashes, output_path):
    """Write flash records as GeoJSON FeatureCollection."""
    features = []
    for f in flashes:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [f["lon"], f["lat"]],
            },
            "properties": {
                "timestamp": f["timestamp"],
                "radiance": f["radiance"],
                "duration_ms": f["duration_ms"],
                "groups": f["groups"],
                "events": f["events"],
                "type": "flash",
            },
        })

    geojson = {
        "type": "FeatureCollection",
        "properties": {
            "source": "EUMETSAT MTG Lightning Imager (LI) Level 2 — Lightning Flash",
            "collection": COLLECTION_ID,
            "instrument": "Lightning Imager on MTG-I1 (Meteosat-12)",
            "spatial_resolution_km": 4.5,
            "temporal_resolution_min": 10,
            "license": "EUMETSAT Data Policy",
            "bbox": [BBOX_WEST, BBOX_SOUTH, BBOX_EAST, BBOX_NORTH],
        },
        "features": features,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as fp:
        json.dump(geojson, fp)

    return len(features)


def main():
    parser = argparse.ArgumentParser(description="Fetch MTG Lightning Imager flash data")
    parser.add_argument("--start", default="2026-01-27", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2026-01-29", help="End date (YYYY-MM-DD)")
    parser.add_argument("--list-only", action="store_true", help="List products without downloading")
    parser.add_argument("--output", default=None, help="Output GeoJSON path")
    args = parser.parse_args()

    start = args.start if "T" in args.start else f"{args.start}T00:00:00Z"
    end = args.end if "T" in args.end else f"{args.end}T00:00:00Z"

    print(f"Searching MTG-LI LFL products: {start} to {end}")
    products = search_products(start, end)
    print(f"Found {len(products)} products")

    if args.list_only:
        for p in products[:20]:
            props = p["properties"]
            print(f"  {props.get('date', '')}  {props.get('identifier', '')[:80]}")
        if len(products) > 20:
            print(f"  ... and {len(products) - 20} more")
        return

    key, secret = get_credentials()
    if not key or not secret:
        print("\nERROR: EUMETSAT credentials required for download.")
        print("Set EUMETSAT_CONSUMER_KEY and EUMETSAT_CONSUMER_SECRET in .env")
        print(f"Products available: {len(products)}")
        sys.exit(1)

    print("Authenticating with EUMETSAT...")
    token = get_access_token(key, secret)

    all_flashes = []
    skipped = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, product in enumerate(products):
            date_str = product["properties"].get("date", "unknown")
            nc_path = download_nc(product, token, tmpdir)

            if nc_path == "AUTH_EXPIRED":
                token = get_access_token(key, secret)
                nc_path = download_nc(product, token, tmpdir)

            if nc_path is None:
                skipped += 1
                continue

            flashes = extract_flashes(nc_path)
            all_flashes.extend(flashes)
            nc_path.unlink()

            if (i + 1) % 25 == 0 or i == len(products) - 1:
                print(f"  [{i+1}/{len(products)}] {date_str} — {len(all_flashes)} Iberian flashes so far")

    print(f"\nTotal flashes over Iberia: {len(all_flashes)}")
    if skipped:
        print(f"Skipped {skipped} products (no CHK-BODY entry)")

    if not all_flashes:
        print("No lightning detected in the Iberian region for this period.")
        return

    # Write GeoJSON
    output = Path(args.output) if args.output else OUT_DIR / "lightning-kristin.geojson"
    n = write_geojson(all_flashes, output)
    print(f"Wrote {n} features to {output}")

    qgis_output = QGIS_DIR / "lightning-kristin.geojson"
    write_geojson(all_flashes, qgis_output)
    print(f"Wrote {n} features to {qgis_output}")

    # Convert to PMTiles
    if shutil.which("tippecanoe"):
        pmtiles_path = OUT_DIR / "lightning-kristin.pmtiles"
        cmd = [
            "tippecanoe",
            "-o", str(pmtiles_path),
            "-l", "lightning",
            "-z", "14", "-Z", "4",
            "--drop-densest-as-needed",
            "--force",
            str(output),
        ]
        print("Converting to PMTiles...")
        subprocess.run(cmd, check=True)
        print(f"Wrote {pmtiles_path}")
    else:
        print("tippecanoe not found — skipping PMTiles conversion")


if __name__ == "__main__":
    main()
