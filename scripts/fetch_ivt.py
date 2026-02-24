#!/usr/bin/env python3
"""
Fetch real IVT from Open-Meteo Historical Forecast API — v2 with 2° grid.

Uses 2° grid spacing (375 points) to stay within API rate limits,
then interpolates to 1° for smooth COG rendering.

Grid: 2° fetch → interpolated to 1° output
  Lats: 25°N to 53°N
  Lons: -45°W to 4°E
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import requests

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

# Fetch grid (2°)
LAT_MIN, LAT_MAX = 25.0, 53.0
LON_MIN, LON_MAX = -45.0, 5.0
FETCH_STEP = 2.0

fetch_lats = np.arange(LAT_MIN, LAT_MAX + 0.1, FETCH_STEP)
fetch_lons = np.arange(LON_MIN, LON_MAX + 0.1, FETCH_STEP)
n_fetch_lats, n_fetch_lons = len(fetch_lats), len(fetch_lons)
n_fetch_points = n_fetch_lats * n_fetch_lons

# Output grid (1°)
OUT_STEP = 1.0
out_lats = np.arange(LAT_MIN, LAT_MAX + 0.1, OUT_STEP)
out_lons = np.arange(LON_MIN, LON_MAX + 0.1, OUT_STEP)
n_out_lats, n_out_lons = len(out_lats), len(out_lons)

START_DATE = "2025-12-01"
END_DATE = "2026-02-15"
API_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
MODEL = "ecmwf_ifs025"
LEVELS = [850, 700, 500]
DP_HPA = [150, 150, 200]
G = 9.81

CHECKPOINT_FILE = DATA_DIR / "temporal" / "ivt" / "ivt_v2_checkpoint.json"


def build_hourly_params():
    params = []
    for level in LEVELS:
        for var in ["wind_speed", "wind_direction", "relative_humidity", "temperature"]:
            params.append(f"{var}_{level}hPa")
    return ",".join(params)


def specific_humidity(rh_pct, temp_c, pressure_hpa):
    es = 6.112 * np.exp(17.67 * temp_c / (temp_c + 243.5))
    e = es * rh_pct / 100.0
    q = 0.622 * e / (pressure_hpa - 0.378 * e)
    return np.maximum(q, 0.0)


def compute_ivt_from_hourly(data):
    n_hours = len(data[f"wind_speed_{LEVELS[0]}hPa"])
    ivt_u = np.zeros(n_hours)
    ivt_v = np.zeros(n_hours)
    for level, dp_hpa in zip(LEVELS, DP_HPA):
        ws = np.array(data[f"wind_speed_{level}hPa"], dtype=np.float64)
        wd = np.array(data[f"wind_direction_{level}hPa"], dtype=np.float64)
        rh = np.array(data[f"relative_humidity_{level}hPa"], dtype=np.float64)
        temp = np.array(data[f"temperature_{level}hPa"], dtype=np.float64)
        mask = np.isnan(ws) | np.isnan(wd) | np.isnan(rh) | np.isnan(temp)
        ws[mask] = 0; wd[mask] = 0; rh[mask] = 0; temp[mask] = 0
        ws_ms = ws / 3.6
        wd_rad = np.deg2rad(wd)
        u = -ws_ms * np.sin(wd_rad)
        v = -ws_ms * np.cos(wd_rad)
        q = specific_humidity(rh, temp, level)
        dp_pa = dp_hpa * 100.0
        ivt_u += q * u * dp_pa / G
        ivt_v += q * v * dp_pa / G
    return np.sqrt(ivt_u**2 + ivt_v**2)


def hourly_to_daily(times, values):
    daily = {}
    for t, v in zip(times, values):
        date = t[:10]
        if date not in daily:
            daily[date] = []
        if not np.isnan(v):
            daily[date].append(v)
    return {d: float(np.mean(vs)) if vs else 0.0 for d, vs in sorted(daily.items())}


def fetch_with_retry(lat, lon, session, max_retries=5):
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": START_DATE, "end_date": END_DATE,
        "hourly": build_hourly_params(),
        "models": MODEL, "timezone": "UTC",
    }
    for attempt in range(max_retries):
        try:
            resp = session.get(API_URL, params=params, timeout=30)
            if resp.status_code == 429:
                wait = 3 * (2 ** attempt)  # 3, 6, 12, 24, 48 seconds
                print(f"    429, waiting {wait}s (attempt {attempt+1})", flush=True)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            result = resp.json()
            if "error" in result:
                raise ValueError(f"API error: {result}")
            return result
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait = 3 * (2 ** attempt)
                time.sleep(wait)
            else:
                raise
    raise ValueError(f"Max retries exceeded for ({lat}, {lon})")


def interpolate_to_1deg(fetch_grid, fetch_lats, fetch_lons, out_lats, out_lons):
    """Interpolate 2° grid to 1° using scipy RegularGridInterpolator."""
    from scipy.interpolate import RegularGridInterpolator

    interp = RegularGridInterpolator(
        (fetch_lats, fetch_lons), fetch_grid,
        method='linear', bounds_error=False, fill_value=0.0
    )
    out_lat_grid, out_lon_grid = np.meshgrid(out_lats, out_lons, indexing='ij')
    points = np.column_stack([out_lat_grid.ravel(), out_lon_grid.ravel()])
    result = interp(points).reshape(len(out_lats), len(out_lons))
    return result


def main():
    print(f"=== IVT Data Acquisition v2 (2° grid → interpolated to 1°) ===")
    print(f"Fetch grid: {n_fetch_lats} × {n_fetch_lons} = {n_fetch_points} points (2°)")
    print(f"Output grid: {n_out_lats} × {n_out_lons} = {n_out_lats*n_out_lons} points (1°)")
    print(f"Date range: {START_DATE} to {END_DATE}")
    print(f"Model: {MODEL}")
    print()

    # Prepare directories
    cog_dir = DATA_DIR / "cog" / "ivt"
    cog_dir.mkdir(parents=True, exist_ok=True)
    temporal_dir = DATA_DIR / "temporal" / "ivt"
    temporal_dir.mkdir(parents=True, exist_ok=True)
    qgis_dir = DATA_DIR / "qgis"
    qgis_dir.mkdir(parents=True, exist_ok=True)

    # Check for checkpoint
    all_daily = {}
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            all_daily = json.load(f)
        print(f"Resuming from checkpoint: {len(all_daily)} points already fetched")

    session = requests.Session()
    session.headers["User-Agent"] = "cheias-pt/1.0 (flood narrative)"

    fetched = len(all_daily)
    failed = 0
    start_time = time.time()

    for i, lat in enumerate(fetch_lats):
        for j, lon in enumerate(fetch_lons):
            key = f"{lat:.1f},{lon:.1f}"
            if key in all_daily:
                continue

            idx = i * n_fetch_lons + j
            if idx % 25 == 0:
                elapsed = time.time() - start_time
                remaining = n_fetch_points - fetched
                rate = max(fetched - len(all_daily) + 1, 1) / max(elapsed, 1)
                eta = remaining / max(rate, 0.01)
                print(f"  [{fetched+1}/{n_fetch_points}] ({lat:.0f}°N, {lon:.0f}°E) "
                      f"elapsed={elapsed:.0f}s eta={eta:.0f}s", flush=True)

            try:
                result = fetch_with_retry(lat, lon, session)
                hourly = result["hourly"]
                times = hourly["time"]
                for var_key in hourly:
                    if var_key != "time":
                        hourly[var_key] = [float(v) if v is not None else float('nan') for v in hourly[var_key]]
                ivt_mag = compute_ivt_from_hourly(hourly)
                daily = hourly_to_daily(times, ivt_mag.tolist())
                all_daily[key] = daily
                fetched += 1
            except Exception as e:
                print(f"  FAILED ({lat:.0f}, {lon:.0f}): {e}", flush=True)
                all_daily[key] = {}
                failed += 1
                fetched += 1

            # 0.5s between requests
            time.sleep(0.5)

            # Checkpoint every 100
            if fetched % 100 == 0:
                with open(CHECKPOINT_FILE, "w") as f:
                    json.dump(all_daily, f)
                print(f"  [checkpoint: {fetched} points]", flush=True)

    # Final checkpoint
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(all_daily, f)

    print(f"\nFetch complete: {fetched} points, {failed} failed, "
          f"{time.time()-start_time:.0f}s")

    # Get dates
    sample = next((v for v in all_daily.values() if v), None)
    if not sample:
        print("ERROR: No data fetched!")
        sys.exit(1)
    dates = sorted(sample.keys())
    n_days = len(dates)
    print(f"Dates: {dates[0]} to {dates[-1]} ({n_days} days)")

    # Build 2° fetch grid
    fetch_grid = np.zeros((n_days, n_fetch_lats, n_fetch_lons), dtype=np.float32)
    for i, lat in enumerate(fetch_lats):
        for j, lon in enumerate(fetch_lons):
            key = f"{lat:.1f},{lon:.1f}"
            daily = all_daily.get(key, {})
            for d, date in enumerate(dates):
                fetch_grid[d, i, j] = daily.get(date, 0.0)

    # Interpolate each day to 1°
    print(f"\n=== Interpolating 2° → 1° ===")
    ivt_grid = np.zeros((n_days, n_out_lats, n_out_lons), dtype=np.float32)
    for d in range(n_days):
        ivt_grid[d] = interpolate_to_1deg(
            fetch_grid[d], fetch_lats, fetch_lons, out_lats, out_lons
        )
    print(f"  Interpolated {n_days} days")

    # Statistics
    print(f"\n=== IVT Statistics ===")
    print(f"Range: {ivt_grid.min():.1f} to {ivt_grid.max():.1f} kg/m/s")
    print(f"Mean: {ivt_grid.mean():.1f}")
    ar_mask = ivt_grid > 250
    print(f"Points > 250 (AR threshold): {ar_mask.sum()}")

    # Storm peaks
    storm_windows = {
        "Kristin": ("2026-01-28", "2026-01-30"),
        "Leonardo": ("2026-02-03", "2026-02-07"),
        "Marta": ("2026-02-09", "2026-02-11"),
    }

    print("\nStorm peaks:")
    peak_features = []
    for storm_name, (start, end) in storm_windows.items():
        storm_dates = [d for d in dates if start <= d <= end]
        if not storm_dates:
            continue
        storm_indices = [dates.index(d) for d in storm_dates]
        storm_slice = ivt_grid[storm_indices]
        max_val = storm_slice.max()
        max_idx = np.unravel_index(storm_slice.argmax(), storm_slice.shape)
        peak_date = storm_dates[max_idx[0]]
        peak_lat = out_lats[max_idx[1]]
        peak_lon = out_lons[max_idx[2]]
        print(f"  {storm_name}: {peak_date}  max IVT = {max_val:.1f} "
              f"at ({peak_lat:.1f}°N, {peak_lon:.1f}°E)")

        # AR-threshold features
        for di, d_idx in enumerate(storm_indices):
            for li in range(n_out_lats):
                for lj in range(n_out_lons):
                    val = ivt_grid[d_idx, li, lj]
                    if val > 250:
                        peak_features.append({
                            "type": "Feature",
                            "geometry": {"type": "Point",
                                         "coordinates": [float(out_lons[lj]), float(out_lats[li])]},
                            "properties": {"ivt": round(float(val), 1),
                                           "date": storm_dates[di], "storm": storm_name}
                        })

    # === Write COGs ===
    print(f"\n=== Writing COGs ===")
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.crs import CRS

    transform = from_bounds(
        out_lons[0] - OUT_STEP / 2, out_lats[0] - OUT_STEP / 2,
        out_lons[-1] + OUT_STEP / 2, out_lats[-1] + OUT_STEP / 2,
        n_out_lons, n_out_lats,
    )

    cog_profile = {
        "driver": "GTiff", "dtype": "float32",
        "width": n_out_lons, "height": n_out_lats, "count": 1,
        "crs": CRS.from_epsg(4326), "transform": transform,
        "nodata": -999.0, "compress": "lzw",
        "tiled": True, "blockxsize": 256, "blockysize": 256,
    }

    # Remove old files first
    old_peak = cog_dir / "ivt-peak-2026-02-10.tif"
    if old_peak.exists():
        old_peak.unlink()
        print(f"  Removed old: {old_peak.name}")

    for d, date in enumerate(dates):
        data_arr = np.flipud(ivt_grid[d])
        out_path = cog_dir / f"{date}.tif"
        with rasterio.open(out_path, "w", **cog_profile) as dst:
            dst.write(data_arr, 1)
            dst.update_tags(UNITS="kg/m/s", SOURCE="Open-Meteo ECMWF IFS 0.25°")
            dst.build_overviews([2, 4, 8], rasterio.enums.Resampling.average)
            dst.update_tags(ns="rio_overview", resampling="average")
    print(f"  Written {n_days} COGs to {cog_dir}/")

    # === Write GeoJSON ===
    peak_path = qgis_dir / "ivt-peak-storm.geojson"
    with open(peak_path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": peak_features}, f)
    print(f"  Written {len(peak_features)} peak features to {peak_path}")

    # === Write Parquet ===
    print(f"\n=== Writing Parquet ===")
    import pyarrow as pa
    import pyarrow.parquet as pq

    rows_lat, rows_lon, rows_date, rows_ivt = [], [], [], []
    for i, lat in enumerate(out_lats):
        for j, lon in enumerate(out_lons):
            for d, date in enumerate(dates):
                rows_lat.append(float(lat))
                rows_lon.append(float(lon))
                rows_date.append(date)
                rows_ivt.append(float(ivt_grid[d, i, j]))

    table = pa.table({
        "latitude": pa.array(rows_lat, type=pa.float64()),
        "longitude": pa.array(rows_lon, type=pa.float64()),
        "date": pa.array(rows_date, type=pa.string()),
        "ivt": pa.array(rows_ivt, type=pa.float32()),
    })

    parquet_path = temporal_dir / "ivt.parquet"
    pq.write_table(table, parquet_path, compression="snappy")
    print(f"  Written {len(rows_lat)} rows to {parquet_path}")

    # Clean up
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

    n_still_zero = sum(1 for v in all_daily.values() if not v)

    print(f"""
=== IVT Data Acquisition Summary ===
Method used: B (Open-Meteo Historical Forecast API)
Source: ECMWF IFS 0.25° via historical-forecast-api.open-meteo.com
Date range: {dates[0]} to {dates[-1]} ({n_days} days)
Fetch grid: 2° ({n_fetch_lats}×{n_fetch_lons} = {n_fetch_points} points)
Output grid: 1° ({n_out_lats}×{n_out_lons} = {n_out_lats*n_out_lons} points, interpolated)
IVT value range: {ivt_grid.min():.1f} to {ivt_grid.max():.1f} kg/m/s
Points > 250 (AR threshold): {ar_mask.sum()} across {n_days} days
Failed fetch points: {n_still_zero}

Storm peaks detected:""")
    for storm_name, (start, end) in storm_windows.items():
        storm_dates = [d for d in dates if start <= d <= end]
        if not storm_dates:
            continue
        storm_indices = [dates.index(d) for d in storm_dates]
        storm_slice = ivt_grid[storm_indices]
        max_val = storm_slice.max()
        max_idx = np.unravel_index(storm_slice.argmax(), storm_slice.shape)
        peak_date = storm_dates[max_idx[0]]
        peak_lat = out_lats[max_idx[1]]
        peak_lon = out_lons[max_idx[2]]
        print(f"  {storm_name}: {peak_date}  max IVT = {max_val:.1f} at ({peak_lat:.1f}°N, {peak_lon:.1f}°E)")

    print(f"""
Files created:
  COGs: {n_days} files at {cog_dir}/
  GeoJSON: {peak_path} ({len(peak_features)} features)
  Parquet: {parquet_path} ({len(rows_lat)} rows)
""")


if __name__ == "__main__":
    main()
