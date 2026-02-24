#!/usr/bin/env python3
"""
Fetch ICON-EU VMAX_10M (10m peak wind gust) from DWD open data or dynamical.org archive.

Data sources:
  - DWD opendata: rolling ~12-day window of operational ICON-EU runs
    https://opendata.dwd.de/weather/nwp/icon-eu/grib/{HH}/vmax_10m/
  - dynamical.org archive on Source Co-Op: archived runs from ~Feb 10, 2026+
    https://data.source.coop/dynamical/dwd-icon-grib/icon-eu/regular-lat-lon/

ICON-EU specs:
  - Grid: 0.0625° regular lat-lon (~6.5 km), European domain
  - Forecast steps: 0-78h hourly, 81-120h 3-hourly (85 files per run)
  - File format: GRIB2, bzip2-compressed
  - Variable: VMAX_10M (maximum 10m wind gust since last step), m/s

Output:
  - COG tiles in data/cog/wind-gust-icon/{YYYY-MM-DD}T{HH}.tif
  - Clipped to Portugal + Atlantic domain (36N-44N, 12W-6W)
  - EPSG:4326, float32, m/s

Retention policy (confirmed 2026-02-22):
  - DWD purges ICON-EU files after ~12 days
  - dynamical.org archive starts 2026-02-10 (no Jan 2026 data)
  - COSMO-REA6 ends 2019-08, ICON-DREAM-EU ends 2025-08
  - Hugging Face openclimatefix/dwd-icon-eu stopped before 2026
  - Historical Jan 26-30 ICON-EU data is UNRECOVERABLE
"""

import argparse
import bz2
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import rasterio
import xarray as xr
from rasterio.transform import from_bounds
from rasterio.windows import from_bounds as window_from_bounds

try:
    import requests
except ImportError:
    sys.exit("requests required: pip install requests")

ROOT = Path(__file__).parent.parent
COG_DIR = ROOT / "data" / "cog" / "wind-gust-icon"

# Portugal + Atlantic domain for clipping
PT_WEST, PT_EAST = -12.0, -6.0
PT_SOUTH, PT_NORTH = 36.0, 44.0

# Wider domain for synoptic context (used with --wide flag)
WIDE_WEST, WIDE_EAST = -60.0, 5.0
WIDE_SOUTH, WIDE_NORTH = 36.0, 60.0

# DWD opendata base URL
DWD_BASE = "https://opendata.dwd.de/weather/nwp/icon-eu/grib"

# dynamical.org archive base URL
ARCHIVE_BASE = "https://data.source.coop/dynamical/dwd-icon-grib/icon-eu/regular-lat-lon"


def dwd_url(run_hour: int, step: int) -> str:
    """Build DWD opendata URL for a given run hour and forecast step."""
    return (
        f"{DWD_BASE}/{run_hour:02d}/vmax_10m/"
        f"icon-eu_europe_regular-lat-lon_single-level_"
        f"{{date}}{run_hour:02d}_{step:03d}_VMAX_10M.grib2.bz2"
    )


def archive_url(run_date: str, run_hour: int, step: int) -> str:
    """Build dynamical.org archive URL."""
    date_compact = run_date.replace("-", "")
    return (
        f"{ARCHIVE_BASE}/{run_date}T{run_hour:02d}/vmax_10m/"
        f"icon-eu_europe_regular-lat-lon_single-level_"
        f"{date_compact}{run_hour:02d}_{step:03d}_VMAX_10M.grib2.bz2"
    )


def download_and_decompress(url: str, timeout: int = 60) -> bytes | None:
    """Download bz2-compressed GRIB2 file and return decompressed bytes."""
    try:
        resp = requests.get(url, timeout=timeout, stream=True)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return bz2.decompress(resp.content)
    except requests.RequestException as e:
        print(f"  Download failed: {e}", file=sys.stderr)
        return None


def grib_to_cog(
    grib_bytes: bytes,
    out_path: Path,
    west: float,
    east: float,
    south: float,
    north: float,
) -> bool:
    """Convert GRIB2 bytes to a clipped COG in EPSG:4326."""
    with tempfile.NamedTemporaryFile(suffix=".grib2") as tmp:
        tmp.write(grib_bytes)
        tmp.flush()

        ds = xr.open_dataset(
            tmp.name,
            engine="cfgrib",
            backend_kwargs={"indexpath": ""},
        )

        # ICON-EU regular-lat-lon files use 'latitude' and 'longitude'
        lat_name = "latitude" if "latitude" in ds.coords else "lat"
        lon_name = "longitude" if "longitude" in ds.coords else "lon"

        # Find the data variable (usually 'gust' or '10fg' or similar)
        data_vars = list(ds.data_vars)
        if not data_vars:
            print("  No data variables found in GRIB", file=sys.stderr)
            return False
        var_name = data_vars[0]
        data = ds[var_name]

        # Clip to domain
        lats = ds[lat_name].values
        lons = ds[lon_name].values

        lat_mask = (lats >= south) & (lats <= north)
        lon_mask = (lons >= west) & (lons <= east)

        clipped = data.sel(
            {lat_name: lat_mask, lon_name: lon_mask}
        )

        clipped_lats = lats[lat_mask]
        clipped_lons = lons[lon_mask]

        # Ensure lat is descending (north to south) for raster convention
        if clipped_lats[0] < clipped_lats[-1]:
            clipped = clipped.isel({lat_name: slice(None, None, -1)})
            clipped_lats = clipped_lats[::-1]

        arr = clipped.values.astype(np.float32)
        if arr.ndim == 1:
            print("  Unexpected 1D array", file=sys.stderr)
            return False

        nrows, ncols = arr.shape
        res_lat = abs(clipped_lats[1] - clipped_lats[0]) if nrows > 1 else 0.0625
        res_lon = abs(clipped_lons[1] - clipped_lons[0]) if ncols > 1 else 0.0625

        transform = from_bounds(
            clipped_lons.min() - res_lon / 2,
            clipped_lats.min() - res_lat / 2,
            clipped_lons.max() + res_lon / 2,
            clipped_lats.max() + res_lat / 2,
            ncols,
            nrows,
        )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(
            out_path,
            "w",
            driver="GTiff",
            height=nrows,
            width=ncols,
            count=1,
            dtype="float32",
            crs="EPSG:4326",
            transform=transform,
            compress="deflate",
            tiled=True,
            blockxsize=256,
            blockysize=256,
            nodata=np.nan,
        ) as dst:
            dst.write(arr, 1)
            dst.update_tags(
                source="DWD ICON-EU",
                variable="VMAX_10M",
                units="m/s",
                description="10m peak wind gust",
            )

        ds.close()
        return True


def compute_valid_time(run_date: str, run_hour: int, step: int) -> str:
    """Compute valid time from run date/hour + forecast step."""
    base = datetime.strptime(f"{run_date} {run_hour:02d}", "%Y-%m-%d %H")
    valid = base + timedelta(hours=step)
    return valid.strftime("%Y-%m-%dT%H")


def fetch_run(
    run_date: str,
    run_hour: int,
    steps: list[int],
    source: str,
    wide: bool,
    out_dir: Path,
    dry_run: bool = False,
) -> dict:
    """Fetch one ICON-EU run, return stats."""
    west = WIDE_WEST if wide else PT_WEST
    east = WIDE_EAST if wide else PT_EAST
    south = WIDE_SOUTH if wide else PT_SOUTH
    north = WIDE_NORTH if wide else PT_NORTH

    stats = {"downloaded": 0, "skipped": 0, "failed": 0}
    date_compact = run_date.replace("-", "")

    for step in steps:
        valid_time = compute_valid_time(run_date, run_hour, step)
        out_path = out_dir / f"{valid_time}.tif"

        if out_path.exists():
            stats["skipped"] += 1
            continue

        if source == "dwd":
            url = (
                f"{DWD_BASE}/{run_hour:02d}/vmax_10m/"
                f"icon-eu_europe_regular-lat-lon_single-level_"
                f"{date_compact}{run_hour:02d}_{step:03d}_VMAX_10M.grib2.bz2"
            )
        else:
            url = archive_url(run_date, run_hour, step)

        if dry_run:
            print(f"  [dry-run] {url}")
            stats["downloaded"] += 1
            continue

        print(f"  Step {step:03d} → {valid_time} ...", end=" ", flush=True)
        grib_bytes = download_and_decompress(url)
        if grib_bytes is None:
            print("MISSING")
            stats["failed"] += 1
            continue

        ok = grib_to_cog(grib_bytes, out_path, west, east, south, north)
        if ok:
            size_kb = out_path.stat().st_size / 1024
            print(f"OK ({size_kb:.0f} KB)")
            stats["downloaded"] += 1
        else:
            print("FAILED")
            stats["failed"] += 1

    return stats


def get_icon_eu_steps(max_step: int = 120) -> list[int]:
    """Return valid ICON-EU forecast steps: hourly 0-78, 3-hourly 81-120."""
    steps = list(range(0, min(79, max_step + 1)))
    steps += list(range(81, min(121, max_step + 1), 3))
    return steps


def main():
    parser = argparse.ArgumentParser(
        description="Fetch ICON-EU VMAX_10M (10m peak wind gust) and convert to COG"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Run date (YYYY-MM-DD). For DWD source, must be within last ~12 days.",
    )
    parser.add_argument(
        "--run",
        type=int,
        default=0,
        choices=[0, 3, 6, 9, 12, 15, 18, 21],
        help="Model run hour (default: 0)",
    )
    parser.add_argument(
        "--steps",
        type=str,
        default="0-24",
        help="Forecast steps, e.g. '0-24' or '0,6,12,24' or '0-120' (default: 0-24)",
    )
    parser.add_argument(
        "--source",
        choices=["dwd", "archive", "auto"],
        default="auto",
        help="Data source: 'dwd' (opendata), 'archive' (dynamical.org), 'auto' (try both)",
    )
    parser.add_argument(
        "--wide",
        action="store_true",
        help="Use wide Atlantic domain (36N-60N, 60W-5E) instead of Portugal clip",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help=f"Output directory (default: {COG_DIR})",
    )
    parser.add_argument(
        "--daily-max",
        action="store_true",
        help="Also compute daily maximum gust from hourly steps",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print URLs without downloading",
    )
    args = parser.parse_args()

    out_dir = args.out_dir or COG_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # Parse steps
    steps_str = args.steps
    if "-" in steps_str and "," not in steps_str:
        parts = steps_str.split("-")
        all_steps = get_icon_eu_steps(int(parts[1]))
        steps = [s for s in all_steps if s >= int(parts[0])]
    elif "," in steps_str:
        steps = [int(s) for s in steps_str.split(",")]
    else:
        steps = [int(steps_str)]

    # Auto-detect source
    source = args.source
    if source == "auto":
        run_dt = datetime.strptime(args.date, "%Y-%m-%d")
        days_ago = (datetime.now() - run_dt).days
        if days_ago <= 12:
            source = "dwd"
            print(f"Auto-selected source: DWD opendata ({days_ago} days ago)")
        else:
            source = "archive"
            print(f"Auto-selected source: dynamical.org archive ({days_ago} days ago)")
            if run_dt < datetime(2026, 2, 10):
                print(
                    f"WARNING: Archive starts 2026-02-10. Data for {args.date} "
                    "is likely unavailable.",
                    file=sys.stderr,
                )

    print(f"Run: {args.date} {args.run:02d}Z | Steps: {steps[0]}-{steps[-1]} "
          f"({len(steps)} files) | Source: {source}")
    domain = "wide (Atlantic)" if args.wide else "Portugal"
    print(f"Domain: {domain} | Output: {out_dir}")
    print()

    stats = fetch_run(
        args.date,
        args.run,
        steps,
        source,
        args.wide,
        out_dir,
        dry_run=args.dry_run,
    )

    print(f"\nDone: {stats['downloaded']} downloaded, "
          f"{stats['skipped']} skipped, {stats['failed']} failed")

    # Compute daily maximum if requested
    if args.daily_max and not args.dry_run and stats["downloaded"] > 0:
        compute_daily_max(args.date, args.run, steps, out_dir)


def compute_daily_max(run_date: str, run_hour: int, steps: list[int], out_dir: Path):
    """Compute daily maximum gust from hourly step COGs."""
    from collections import defaultdict

    by_day = defaultdict(list)
    for step in steps:
        vt = compute_valid_time(run_date, run_hour, step)
        day = vt[:10]
        path = out_dir / f"{vt}.tif"
        if path.exists():
            by_day[day].append(path)

    for day, paths in sorted(by_day.items()):
        if len(paths) < 2:
            continue
        out_path = out_dir / f"{day}_daily-max.tif"
        if out_path.exists():
            continue

        print(f"  Daily max {day} ({len(paths)} files) ...", end=" ", flush=True)
        arrays = []
        meta = None
        for p in paths:
            with rasterio.open(p) as src:
                arrays.append(src.read(1))
                if meta is None:
                    meta = src.meta.copy()

        stack = np.stack(arrays)
        daily_max = np.nanmax(stack, axis=0)

        meta.update(compress="deflate")
        with rasterio.open(out_path, "w", **meta) as dst:
            dst.write(daily_max, 1)
            dst.update_tags(
                source="DWD ICON-EU",
                variable="VMAX_10M_daily_max",
                units="m/s",
                description=f"Daily maximum 10m peak wind gust {day}",
            )
        size_kb = out_path.stat().st_size / 1024
        print(f"OK ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
