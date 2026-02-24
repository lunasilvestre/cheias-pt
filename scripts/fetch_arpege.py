#!/usr/bin/env python3
"""Fetch ARPEGE synoptic fields via Open-Meteo Historical Forecast API.

Météo-France ARPEGE data retention:
  - Official API (portail-api.meteofrance.fr): 14 days only
  - AWS S3 bucket (mf-nwp-models): real-time feed, no archive
  - Open-Meteo historical-forecast-api: archives model output indefinitely

This script uses Open-Meteo as the only viable source for historical ARPEGE
data. It fetches MSLP + 10m wind on a 0.5° grid over the North Atlantic +
Iberia, then converts to Cloud-Optimized GeoTIFFs.

Model: meteofrance_arpege_europe (0.1° native, served at request resolution)
  - Runs: 00, 06, 12, 18 UTC
  - Forecast range: 0-102h

Domain: 36N-60N, 60W-5E (matches ERA5 synoptic domain)
Temporal:
  - 6-hourly (00,06,12,18 UTC) for full range
  - Hourly for Jan 26-30 storm period
Output: data/cog/arpege/{mslp,wind-u,wind-v}/YYYY-MM-DDTHH.tif
"""

import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import requests

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
COG_DIR = DATA_DIR / "cog" / "arpege"

# Domain (matches ERA5 synoptic extent)
LAT_MIN, LAT_MAX = 36.0, 60.0
LON_MIN, LON_MAX = -60.0, 5.0
GRID_STEP = 0.5  # degrees

# Build grid
lats = np.arange(LAT_MIN, LAT_MAX + 0.01, GRID_STEP)
lons = np.arange(LON_MIN, LON_MAX + 0.01, GRID_STEP)
n_lats, n_lons = len(lats), len(lons)

# Temporal config
START_DATE = "2025-12-01"
END_DATE = "2026-02-15"
STORM_START = datetime(2026, 1, 26)
STORM_END = datetime(2026, 1, 30)

# API config
API_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
MODEL = "meteofrance_arpege_europe"
VARIABLES = "pressure_msl,wind_speed_10m,wind_direction_10m"
BATCH_SIZE = 50  # points per request (API limit ~50 locations)
RATE_LIMIT_PAUSE = 1.0  # seconds between batches

CHECKPOINT_FILE = COG_DIR / "_checkpoint.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("arpege")


def ensure_dirs():
    for subdir in ["mslp", "wind-u", "wind-v"]:
        (COG_DIR / subdir).mkdir(parents=True, exist_ok=True)


def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        return json.loads(CHECKPOINT_FILE.read_text())
    return {"completed_batches": []}


def save_checkpoint(state):
    CHECKPOINT_FILE.write_text(json.dumps(state, indent=2))


def build_grid_batches():
    """Split lat/lon grid into batches of BATCH_SIZE points."""
    points = []
    for lat in lats:
        for lon in lons:
            points.append((float(lat), float(lon)))

    batches = []
    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]
        batches.append(batch)
    return batches


def fetch_batch(batch, batch_idx, retries=3):
    """Fetch hourly data for a batch of points."""
    lat_str = ",".join(f"{p[0]:.2f}" for p in batch)
    lon_str = ",".join(f"{p[1]:.2f}" for p in batch)

    params = {
        "latitude": lat_str,
        "longitude": lon_str,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": VARIABLES,
        "models": MODEL,
        "timeformat": "unixtime",
    }

    for attempt in range(retries):
        try:
            r = requests.get(API_URL, params=params, timeout=120)
            if r.status_code == 429:
                wait = 30 * (attempt + 1)
                log.warning(f"Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            log.warning(f"Batch {batch_idx} attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
    return None


def decompose_wind(speed, direction_deg):
    """Convert wind speed + direction to U/V components.

    Meteorological convention: direction is where wind comes FROM.
    U = -speed * sin(dir), V = -speed * cos(dir)
    """
    dir_rad = np.deg2rad(direction_deg)
    u = -speed * np.sin(dir_rad)
    v = -speed * np.cos(dir_rad)
    return u, v


def write_cog(data_2d, lats_out, lons_out, path):
    """Write a 2D array as a Cloud-Optimized GeoTIFF."""
    try:
        import rioxarray  # noqa: F401
        import xarray as xr
    except ImportError:
        log.error("rioxarray required for COG output: pip install rioxarray")
        sys.exit(1)

    # data_2d shape: (n_lats, n_lons), lats descending for north-up
    da = xr.DataArray(
        data_2d[::-1],  # flip to north-up
        dims=["y", "x"],
        coords={
            "y": lats_out[::-1],
            "x": lons_out,
        },
    )
    da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")
    da = da.rio.set_crs("EPSG:4326")
    da.rio.to_raster(
        str(path),
        driver="COG",
        compress="DEFLATE",
        dtype="float32",
    )


def select_hours(timestamp_utc):
    """Return True if this hour should be output (6-hourly or storm hourly)."""
    dt = datetime.utcfromtimestamp(timestamp_utc)
    # Storm period: all hours
    if STORM_START <= dt <= STORM_END + timedelta(hours=23):
        return True
    # Otherwise: 6-hourly
    return dt.hour in (0, 6, 12, 18)


def main():
    ensure_dirs()
    state = load_checkpoint()
    batches = build_grid_batches()
    total_points = n_lats * n_lons

    log.info(f"ARPEGE fetch: {total_points} points ({n_lats}x{n_lons}), "
             f"{len(batches)} batches of {BATCH_SIZE}")
    log.info(f"Domain: {LAT_MIN}-{LAT_MAX}N, {LON_MIN}-{LON_MAX}E @ {GRID_STEP}°")
    log.info(f"Period: {START_DATE} to {END_DATE}")
    log.info(f"Model: {MODEL}")

    # Storage: {unix_timestamp: {var: 2D array}}
    # We accumulate all batches into grids, then write COGs
    # First pass: determine time axis from first batch
    log.info("Fetching first batch to determine time axis...")
    test_data = fetch_batch(batches[0], 0)
    if test_data is None:
        log.error("Failed to fetch test batch")
        sys.exit(1)

    # Handle single vs multi-location response
    if isinstance(test_data, list):
        times = test_data[0]["hourly"]["time"]
    else:
        times = test_data["hourly"]["time"]

    n_times = len(times)
    selected_times = [t for t in times if select_hours(t)]
    log.info(f"Time steps: {n_times} total, {len(selected_times)} selected "
             f"(6-hourly + storm hourly)")

    # Initialize grids: {timestamp: {var: np.zeros(n_lats, n_lons)}}
    grids = {}
    for t in selected_times:
        grids[t] = {
            "mslp": np.full((n_lats, n_lons), np.nan, dtype=np.float32),
            "wind_u": np.full((n_lats, n_lons), np.nan, dtype=np.float32),
            "wind_v": np.full((n_lats, n_lons), np.nan, dtype=np.float32),
        }

    # Fetch all batches
    completed = set(state.get("completed_batches", []))
    for batch_idx, batch in enumerate(batches):
        if batch_idx in completed:
            log.info(f"Batch {batch_idx + 1}/{len(batches)} — cached")
            continue

        log.info(f"Batch {batch_idx + 1}/{len(batches)} "
                 f"({len(batch)} points)...")
        data = fetch_batch(batch, batch_idx)
        if data is None:
            log.error(f"Failed batch {batch_idx}, stopping")
            save_checkpoint(state)
            sys.exit(1)

        # Normalize to list of location responses
        if not isinstance(data, list):
            data = [data]

        for loc_idx, loc_data in enumerate(data):
            pt_lat, pt_lon = batch[loc_idx]
            # Find grid indices
            lat_idx = int(round((pt_lat - LAT_MIN) / GRID_STEP))
            lon_idx = int(round((pt_lon - LON_MIN) / GRID_STEP))

            if lat_idx < 0 or lat_idx >= n_lats or lon_idx < 0 or lon_idx >= n_lons:
                continue

            hourly = loc_data.get("hourly", {})
            loc_times = hourly.get("time", [])
            mslp_vals = hourly.get("pressure_msl", [])
            wspd_vals = hourly.get("wind_speed_10m", [])
            wdir_vals = hourly.get("wind_direction_10m", [])

            for i, t in enumerate(loc_times):
                if t not in grids:
                    continue
                if i < len(mslp_vals) and mslp_vals[i] is not None:
                    grids[t]["mslp"][lat_idx, lon_idx] = mslp_vals[i]
                if (i < len(wspd_vals) and wspd_vals[i] is not None
                        and i < len(wdir_vals) and wdir_vals[i] is not None):
                    u, v = decompose_wind(wspd_vals[i], wdir_vals[i])
                    grids[t]["wind_u"][lat_idx, lon_idx] = u
                    grids[t]["wind_v"][lat_idx, lon_idx] = v

        completed.add(batch_idx)
        state["completed_batches"] = sorted(completed)
        save_checkpoint(state)

        if batch_idx < len(batches) - 1:
            time.sleep(RATE_LIMIT_PAUSE)

    # Write COGs
    log.info(f"Writing {len(selected_times)} timesteps as COGs...")
    written = 0
    for t in sorted(selected_times):
        dt = datetime.utcfromtimestamp(t)
        ts_str = dt.strftime("%Y-%m-%dT%H")

        for var_name, subdir in [("mslp", "mslp"), ("wind_u", "wind-u"),
                                  ("wind_v", "wind-v")]:
            out_path = COG_DIR / subdir / f"{ts_str}.tif"
            if out_path.exists():
                continue
            grid = grids[t][var_name]
            valid = np.count_nonzero(~np.isnan(grid))
            if valid < 10:
                log.warning(f"Skipping {var_name} @ {ts_str}: only {valid} valid")
                continue
            write_cog(grid, lats, lons, out_path)
            written += 1

    log.info(f"Done. Wrote {written} COGs to {COG_DIR}")

    # Summary
    for subdir in ["mslp", "wind-u", "wind-v"]:
        n_files = len(list((COG_DIR / subdir).glob("*.tif")))
        log.info(f"  {subdir}: {n_files} files")


if __name__ == "__main__":
    main()
