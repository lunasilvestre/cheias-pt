#!/usr/bin/env python3
"""
Radar / High-Resolution Precipitation Data Fetcher

Status: PARTIALLY BLOCKED — no single free source provides actual radar
data for Portugal with historical archive access.

This script implements what IS available:
1. IPMA radar scraper (current day only — run as cron for future events)
2. Open-Meteo hourly precipitation grid (ECMWF IFS, 0.25°, available now)
3. GPM IMERG downloader (requires NASA Earthdata credentials)

Usage:
    # Scrape current IPMA radar images (set up as cron for future coverage)
    python scripts/fetch_radar.py --source ipma-current

    # Download Open-Meteo hourly precipitation grid (no auth needed)
    python scripts/fetch_radar.py --source open-meteo --start 2026-01-25 --end 2026-02-10

    # Download GPM IMERG data (requires NASA Earthdata credentials in .env)
    python scripts/fetch_radar.py --source gpm-imerg --start 2026-01-27 --end 2026-01-28
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "radar"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_ipma_current():
    """
    Scrape current IPMA radar images (~24h window, 10-min intervals).

    IPMA serves radar composites as JPEG images through their web portal.
    Each image URL contains a random 20-character token that changes every
    10 minutes, making historical access impossible without prior scraping.

    Radar stations: Coruche (central), Arouca (north), Loule (south)
    Product: Precipitation intensity (mm/h), mainland composite
    Resolution: ~1km
    """
    print("=== IPMA Radar Scraper (Current Day) ===\n")

    url = "https://www.ipma.pt/pt/otempo/obs.radar/"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    html = r.text

    # Extract image base directory
    img_dir_match = re.findall(r"globaImgDir\s*=\s*['\"]([^'\"]+)", html)
    if not img_dir_match:
        print("ERROR: Could not find globaImgDir in IPMA page")
        return

    base_url = f"https://www.ipma.pt{img_dir_match[0]}"

    # Extract file options (date/token/filename.jpg)
    options = re.findall(
        r'<option[^>]*value="([^"]+\.jpg)"[^>]*>([^<]*)</option>', html
    )

    if not options:
        print("ERROR: No radar image options found in page")
        return

    print(f"Found {len(options)} radar frames")

    # Download all frames
    out_dir = DATA_DIR / "ipma"
    out_dir.mkdir(exist_ok=True)

    downloaded = 0
    for path, timestamp_text in options:
        parts = path.split("/")
        if len(parts) != 3:
            continue

        date_str, token, filename = parts

        # Parse timestamp from text like "2026-02-22 17:00h"
        ts_clean = timestamp_text.strip().replace("h", "")

        # Output filename based on timestamp
        out_name = f"ipma_por_{date_str}_{filename[3:11]}.jpg"
        out_path = out_dir / out_name

        if out_path.exists():
            continue

        img_url = f"{base_url}{path}"
        try:
            ri = requests.get(img_url, timeout=15)
            if ri.status_code == 200 and ri.content[:2] == b"\xff\xd8":
                out_path.write_bytes(ri.content)
                downloaded += 1
            else:
                print(f"  SKIP {filename}: status={ri.status_code}")
        except Exception as e:
            print(f"  ERROR {filename}: {e}")

        time.sleep(0.1)  # Gentle rate limiting

    print(f"Downloaded {downloaded} new frames to {out_dir}/")
    print(f"Total frames on disk: {len(list(out_dir.glob('*.jpg')))}")
    print("\nNOTE: Set up as cron job to build historical archive:")
    print("  */30 * * * * cd /path/to/cheias-pt && .venv/bin/python scripts/fetch_radar.py --source ipma-current")


def fetch_open_meteo_hourly(start_date: str, end_date: str):
    """
    Download hourly precipitation from Open-Meteo (ECMWF IFS025, 0.25 deg).

    This is MODEL data, not radar observations, but:
    - No authentication needed
    - Archive available for our entire study period
    - Shows storm progression at sub-daily resolution
    - Resolution: 0.25° (~25km) — coarser than radar but adequate for narrative

    Output: GeoJSON with hourly precipitation for each grid point
    """
    print(f"=== Open-Meteo Hourly Precipitation Grid ===")
    print(f"Period: {start_date} to {end_date}\n")

    # Grid over Portugal + Atlantic approach: 36-44°N, 14°W-5°W
    lat_range = [i * 0.5 + 36.0 for i in range(17)]  # 36.0 to 44.0, 0.5° step
    lon_range = [i * 0.5 - 14.0 for i in range(19)]  # -14.0 to -5.0, 0.5° step

    print(f"Grid: {len(lat_range)} x {len(lon_range)} = {len(lat_range) * len(lon_range)} points")
    print(f"Resolution: 0.5° (~55km)")

    all_data = []
    total = len(lat_range) * len(lon_range)

    for i, lat in enumerate(lat_range):
        # Batch request (Open-Meteo supports multiple locations)
        lats_batch = [lat] * len(lon_range)
        lons_batch = lon_range

        params = {
            "latitude": ",".join(str(l) for l in lats_batch),
            "longitude": ",".join(str(l) for l in lons_batch),
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "precipitation",
            "models": "ecmwf_ifs025",
            "timezone": "UTC",
        }

        r = requests.get(
            "https://historical-forecast-api.open-meteo.com/v1/forecast",
            params=params,
            timeout=60,
        )

        if r.status_code != 200:
            print(f"  ERROR at lat={lat}: {r.status_code}")
            continue

        data = r.json()

        # Handle single vs multiple location response
        if isinstance(data, list):
            locations = data
        else:
            locations = [data]

        for j, loc_data in enumerate(locations):
            if "hourly" not in loc_data:
                continue

            lon = lons_batch[j]
            times = loc_data["hourly"]["time"]
            precip = loc_data["hourly"]["precipitation"]

            all_data.append({
                "lat": lat,
                "lon": lon,
                "times": times,
                "precipitation_mm": precip,
            })

        done = (i + 1) * len(lon_range)
        print(f"  Progress: {done}/{total} points ({100*done/total:.0f}%)")
        time.sleep(0.3)  # Rate limiting

    # Save as JSON
    out_path = DATA_DIR / f"open_meteo_hourly_{start_date}_{end_date}.json"
    with open(out_path, "w") as f:
        json.dump({
            "source": "Open-Meteo Historical Forecast API (ECMWF IFS025)",
            "resolution_deg": 0.5,
            "resolution_km": 55,
            "temporal_resolution": "hourly",
            "variable": "precipitation (mm)",
            "period": {"start": start_date, "end": end_date},
            "note": "Model data (not radar). Adequate for storm progression narrative.",
            "grid_points": len(all_data),
            "data": all_data,
        }, f)

    print(f"\nSaved to: {out_path}")
    print(f"Grid points: {len(all_data)}")

    # Also create per-hour GeoJSON frames for animation
    if all_data:
        frames_dir = DATA_DIR / "hourly_frames"
        frames_dir.mkdir(exist_ok=True)

        times = all_data[0]["times"]
        for t_idx, time_str in enumerate(times):
            features = []
            for pt in all_data:
                val = pt["precipitation_mm"][t_idx]
                if val is not None and val > 0:
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [pt["lon"], pt["lat"]],
                        },
                        "properties": {
                            "precipitation_mm": round(val, 2),
                            "time": time_str,
                        },
                    })

            geojson = {
                "type": "FeatureCollection",
                "features": features,
            }

            # File name from timestamp
            ts = time_str.replace(":", "").replace("T", "_")
            frame_path = frames_dir / f"{ts}.geojson"
            with open(frame_path, "w") as f:
                json.dump(geojson, f)

        print(f"Created {len(times)} hourly GeoJSON frames in {frames_dir}/")


def fetch_gpm_imerg(start_date: str, end_date: str):
    """
    Download GPM IMERG Late Run precipitation data.

    GPM IMERG provides global satellite-derived precipitation:
    - Resolution: 0.1° (~11km), half-hourly
    - Near-real-time archive (Late Run, ~12h delay)
    - Data format: HDF5 via OPeNDAP subsetting

    REQUIRES NASA Earthdata credentials:
    1. Register free at https://urs.earthdata.nasa.gov/users/new
    2. Authorize "NASA GESDISC DATA ARCHIVE" application
    3. Add to .env: NASA_EARTHDATA_USER=xxx, NASA_EARTHDATA_PASSWORD=xxx

    Or create ~/.netrc with:
    machine urs.earthdata.nasa.gov login <user> password <pass>
    """
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    user = os.environ.get("NASA_EARTHDATA_USER")
    password = os.environ.get("NASA_EARTHDATA_PASSWORD")

    if not user or not password:
        # Check .netrc
        netrc_path = Path.home() / ".netrc"
        if netrc_path.exists():
            content = netrc_path.read_text()
            if "urs.earthdata.nasa.gov" in content:
                print("Using credentials from ~/.netrc")
            else:
                print("ERROR: NASA Earthdata credentials not found.")
                print("Set NASA_EARTHDATA_USER and NASA_EARTHDATA_PASSWORD in .env")
                print("Or configure ~/.netrc for urs.earthdata.nasa.gov")
                print("Register free at: https://urs.earthdata.nasa.gov/users/new")
                return
        else:
            print("ERROR: NASA Earthdata credentials not found.")
            print("Set NASA_EARTHDATA_USER and NASA_EARTHDATA_PASSWORD in .env")
            print("Or configure ~/.netrc for urs.earthdata.nasa.gov")
            print("Register free at: https://urs.earthdata.nasa.gov/users/new")
            return

    print(f"=== GPM IMERG Late Run (V07B) ===")
    print(f"Period: {start_date} to {end_date}")
    print(f"Resolution: 0.1° (~11km), half-hourly\n")

    # Create authenticated session
    session = requests.Session()
    if user and password:
        session.auth = (user, password)

    # Portugal domain indices for OPeNDAP subsetting
    # lat: 36.9-42.2 N → indices 1269 to 1322
    # lon: -9.6 to -6.1 W → indices 1704 to 1739
    lat_start, lat_end = 1269, 1322
    lon_start, lon_end = 1704, 1739

    out_dir = DATA_DIR / "gpm_imerg"
    out_dir.mkdir(exist_ok=True)

    # Iterate over dates
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    while current <= end:
        doy = current.timetuple().tm_yday
        doy_str = f"{doy:03d}"
        date_str = current.strftime("%Y%m%d")

        # List files for this day
        list_url = f"https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHHL.07/{current.year}/{doy_str}/"

        print(f"\n--- {current.strftime('%Y-%m-%d')} (DOY {doy_str}) ---")

        r = session.get(list_url, timeout=30)
        if r.status_code != 200:
            print(f"  Cannot list directory: {r.status_code}")
            current += timedelta(days=1)
            continue

        # Get HDF5 files
        files = re.findall(r'(3B-HHR-L\.MS\.MRG\.3IMERG\.[^"]+\.HDF5)', r.text)
        files = sorted(set(files))

        print(f"  Files: {len(files)}")

        for fname in files:
            # Extract time from filename
            time_match = re.search(r"S(\d{6})-E(\d{6})\.(\d{4})", fname)
            if not time_match:
                continue

            start_time = time_match.group(1)  # HHMMSS

            # OPeNDAP subset URL
            opendap_url = (
                f"https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/"
                f"GPM_3IMERGHHL.07/{current.year}/{doy_str}/{fname}.nc4"
                f"?precipitation[0:0][{lon_start}:{lon_end}][{lat_start}:{lat_end}]"
                f",lat[{lat_start}:{lat_end}],lon[{lon_start}:{lon_end}]"
            )

            out_file = out_dir / f"imerg_{date_str}_{start_time}.nc4"
            if out_file.exists():
                continue

            try:
                rd = session.get(opendap_url, timeout=60)
                if rd.status_code == 200:
                    out_file.write_bytes(rd.content)
                    print(f"  Downloaded: {out_file.name} ({len(rd.content)} bytes)")
                elif rd.status_code == 401:
                    print(f"  AUTH FAILED — check credentials")
                    return
                else:
                    print(f"  {fname}: HTTP {rd.status_code}")
            except Exception as e:
                print(f"  {fname}: {e}")

            time.sleep(0.2)

        current += timedelta(days=1)

    print(f"\nDone. Files saved to: {out_dir}/")


def main():
    parser = argparse.ArgumentParser(description="Radar/precipitation data fetcher")
    parser.add_argument(
        "--source",
        choices=["ipma-current", "open-meteo", "gpm-imerg"],
        required=True,
        help="Data source to fetch",
    )
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")

    args = parser.parse_args()

    if args.source == "ipma-current":
        fetch_ipma_current()
    elif args.source == "open-meteo":
        if not args.start or not args.end:
            parser.error("--start and --end required for open-meteo")
        fetch_open_meteo_hourly(args.start, args.end)
    elif args.source == "gpm-imerg":
        if not args.start or not args.end:
            parser.error("--start and --end required for gpm-imerg")
        fetch_gpm_imerg(args.start, args.end)


if __name__ == "__main__":
    main()
