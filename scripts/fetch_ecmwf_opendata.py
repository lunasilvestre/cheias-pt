#!/usr/bin/env python3
"""
Fetch ECMWF Open Data HRES 0.25° forecasts from the AWS S3 archive.

KEY FINDING: The main ECMWF Open Data portal (data.ecmwf.int/forecasts/) only
retains the most recent ~12 forecast runs (~2-3 days). However, the AWS S3 mirror
at s3://ecmwf-forecasts (eu-central-1) maintains a FULL ARCHIVE back to Jan 2023.
This means Jan–Feb 2026 storm period data IS available.

Data source: https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/
Resolution: 0.25° global (~28 km), GRIB2 format
Cycles: 00Z, 06Z, 12Z, 18Z daily
Retention: Full archive from 2023-01-18 onwards (on AWS)

Parameters downloaded for synoptic charts:
  - msl:  Mean sea level pressure (Pa)
  - 10u:  10-metre U wind component (m/s)
  - 10v:  10-metre V wind component (m/s)
  - 10fg: Maximum 10-metre wind gust since previous post-processing (m/s)
  - tp:   Total precipitation (m, accumulated from T+0)

For IVT (Integrated Vapour Transport) computation:
  - q at 1000,925,850,700,600,500,400,300 hPa (specific humidity, kg/kg)
  - u at same levels (U wind, m/s)
  - v at same levels (V wind, m/s)

Output: Cloud-Optimized GeoTIFFs cropped to North Atlantic / Iberia region.

Usage:
  python scripts/fetch_ecmwf_opendata.py                    # Storm period (default)
  python scripts/fetch_ecmwf_opendata.py --date 20260205    # Specific date
  python scripts/fetch_ecmwf_opendata.py --latest            # Most recent forecast

Attribution: ECMWF Open Data, CC-BY-4.0 (https://www.ecmwf.int/en/forecasts/datasets/open-data)
"""

import argparse
import json
import logging
import os
import struct
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AWS_BASE = "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com"
ECMWF_BASE = "https://data.ecmwf.int/forecasts"

# Bounding box for synoptic charts: North Atlantic + Iberian Peninsula
# Generous extent for synoptic-scale features (storms, fronts)
BBOX_SYNOPTIC = {"west": -30, "east": 5, "south": 30, "north": 55}

# Tighter box for Iberia-only products
BBOX_IBERIA = {"west": -10, "east": 0, "south": 36, "north": 43}

# Surface parameters for synoptic charts
SURFACE_PARAMS = ["msl", "10u", "10v", "10fg", "tp"]

# Pressure levels for IVT computation (hPa)
IVT_LEVELS = [1000, 925, 850, 700, 600, 500, 400, 300]
IVT_PARAMS = ["q", "u", "v"]

# Storm period dates (Kristin → Leonardo → Marta, 2026)
STORM_DATES = [
    # Pre-storm context
    "20260125",
    # Storm Kristin
    "20260126", "20260127", "20260128", "20260129",
    # Inter-storm
    "20260130", "20260131", "20260201", "20260202",
    # Storm Leonardo
    "20260203", "20260204", "20260205", "20260206",
    # Storm Marta / peak
    "20260207", "20260208", "20260209", "20260210",
]

# Preferred forecast cycles (12Z gives best T+0 analysis, 00Z as fallback)
PREFERRED_CYCLES = ["12z", "00z"]

# Forecast steps to download (hours, T+0 for analysis fields)
ANALYSIS_STEPS = [0]
# For a 6-hourly sequence through a 24h period:
FORECAST_STEPS_6H = [0, 6, 12, 18, 24]

OUTPUT_DIR = Path("data/cog/ecmwf-hres")


# ---------------------------------------------------------------------------
# Index parsing + byte-range download
# ---------------------------------------------------------------------------

def fetch_index(date: str, cycle: str, step: int, source: str = "aws") -> list[dict]:
    """Fetch and parse the GRIB2 index file for a specific forecast step."""
    base = AWS_BASE if source == "aws" else ECMWF_BASE
    step_str = f"{step}h"
    # Time format: YYYYMMDDHHMMSS (e.g. 20260126120000 for 12Z)
    hour = cycle.replace("z", "").zfill(2)
    time_stamp = f"{date}{hour}0000"
    index_url = f"{base}/{date}/{cycle}/ifs/0p25/oper/{time_stamp}-{step_str}-oper-fc.index"

    resp = requests.get(index_url, timeout=30)
    if resp.status_code == 404:
        return []
    resp.raise_for_status()

    entries = []
    for line in resp.text.strip().split("\n"):
        if line:
            entries.append(json.loads(line))
    return entries


def download_fields(date: str, cycle: str, step: int, params: list[str],
                    levtype: str = "sfc", levels: list[int] | None = None,
                    source: str = "aws") -> bytes:
    """Download specific GRIB fields using byte-range requests from the index.

    Returns concatenated GRIB2 messages for the requested parameters.
    """
    entries = fetch_index(date, cycle, step, source)
    if not entries:
        return b""

    base = AWS_BASE if source == "aws" else ECMWF_BASE
    step_str = f"{step}h"
    hour = cycle.replace("z", "").zfill(2)
    time_stamp = f"{date}{hour}0000"
    grib_url = f"{base}/{date}/{cycle}/ifs/0p25/oper/{time_stamp}-{step_str}-oper-fc.grib2"

    # Filter entries matching our criteria
    ranges = []
    for entry in entries:
        if entry.get("param") not in params:
            continue
        if entry.get("levtype") != levtype:
            continue
        if levtype == "pl" and levels is not None:
            if int(entry.get("levelist", 0)) not in levels:
                continue
        offset = entry["_offset"]
        length = entry["_length"]
        ranges.append((offset, length, entry.get("param"), entry.get("levelist", "sfc")))

    if not ranges:
        log.warning(f"No matching fields for {params} levtype={levtype} in {date}/{cycle}/step={step}")
        return b""

    # Sort by offset for efficient sequential reading
    ranges.sort(key=lambda x: x[0])

    # Download each field via byte-range
    grib_data = b""
    session = requests.Session()
    for offset, length, param, level in ranges:
        range_header = f"bytes={offset}-{offset + length - 1}"
        resp = session.get(grib_url, headers={"Range": range_header}, timeout=60)
        resp.raise_for_status()
        grib_data += resp.content
        size_kb = len(resp.content) / 1024
        log.debug(f"  Downloaded {param} level={level}: {size_kb:.0f} KB")

    total_mb = len(grib_data) / (1024 * 1024)
    log.info(f"  Downloaded {len(ranges)} fields ({total_mb:.1f} MB) from {date}/{cycle}/step={step}")
    return grib_data


def save_grib(data: bytes, path: Path):
    """Save raw GRIB data to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    log.info(f"  Saved {path} ({len(data) / (1024*1024):.1f} MB)")


# ---------------------------------------------------------------------------
# GRIB → GeoTIFF conversion
# ---------------------------------------------------------------------------

def grib_to_cog(grib_path: Path, output_path: Path, bbox: dict | None = None,
                param_filter: str | None = None):
    """Convert GRIB2 file to Cloud-Optimized GeoTIFF, optionally clipping to bbox.

    Requires: rasterio, cfgrib (or gdal with GRIB driver).
    """
    try:
        import rasterio
        from rasterio.transform import from_bounds
        from rasterio.warp import calculate_default_transform, reproject, Resampling
    except ImportError:
        log.warning("rasterio not installed, attempting gdal fallback")
        _grib_to_cog_gdal(grib_path, output_path, bbox)
        return

    try:
        import cfgrib
        import xarray as xr

        ds = xr.open_dataset(grib_path, engine="cfgrib",
                             backend_kwargs={"indexpath": ""})

        if bbox:
            # cfgrib uses latitude (descending) and longitude (0-360 or -180-180)
            lons = ds.longitude.values
            if lons.max() > 180:
                # Convert 0-360 to -180-180
                ds = ds.assign_coords(longitude=(((ds.longitude + 180) % 360) - 180))
                ds = ds.sortby("longitude")

            ds = ds.sel(
                latitude=slice(bbox["north"], bbox["south"]),
                longitude=slice(bbox["west"], bbox["east"]),
            )

        # Write each variable as a separate band
        for var_name in ds.data_vars:
            var = ds[var_name]
            data = var.values
            if data.ndim == 2:
                data = data[np.newaxis, :]  # Add band dimension

                out_path = output_path.with_name(
                    output_path.stem + f"_{var_name}" + output_path.suffix
                )
                _write_cog(data, var.latitude.values, var.longitude.values, out_path)

    except Exception as e:
        log.warning(f"cfgrib failed ({e}), falling back to gdal")
        _grib_to_cog_gdal(grib_path, output_path, bbox)


def _write_cog(data: np.ndarray, lats: np.ndarray, lons: np.ndarray, path: Path):
    """Write numpy array to a Cloud-Optimized GeoTIFF."""
    import rasterio
    from rasterio.transform import from_bounds

    n_bands, height, width = data.shape
    # Assume regular grid
    west, east = float(lons.min()), float(lons.max())
    south, north = float(lats.min()), float(lats.max())
    transform = from_bounds(west, south, east, north, width, height)

    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "width": width,
        "height": height,
        "count": n_bands,
        "crs": "EPSG:4326",
        "transform": transform,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }

    with rasterio.open(path, "w", **profile) as dst:
        for i in range(n_bands):
            dst.write(data[i].astype("float32"), i + 1)

    log.info(f"  Wrote COG: {path} ({height}x{width}, {n_bands} bands)")


def _grib_to_cog_gdal(grib_path: Path, output_path: Path, bbox: dict | None = None):
    """Fallback: use GDAL CLI to convert GRIB to COG."""
    import subprocess

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "gdal_translate",
        "-of", "COG",
        "-co", "COMPRESS=DEFLATE",
        "-co", "TILING_SCHEME=GoogleMapsCompatible",
    ]
    if bbox:
        cmd += [
            "-projwin",
            str(bbox["west"]), str(bbox["north"]),
            str(bbox["east"]), str(bbox["south"]),
        ]
    cmd += [str(grib_path), str(output_path)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f"gdal_translate failed: {result.stderr}")
        raise RuntimeError(f"gdal_translate failed: {result.stderr}")
    log.info(f"  Wrote COG (GDAL): {output_path}")


# ---------------------------------------------------------------------------
# High-level fetch operations
# ---------------------------------------------------------------------------

def fetch_surface_fields(date: str, cycle: str = "12z", steps: list[int] | None = None,
                         output_dir: Path = OUTPUT_DIR, source: str = "aws") -> list[Path]:
    """Fetch surface synoptic fields (MSLP, wind, precip) for one forecast run."""
    if steps is None:
        steps = ANALYSIS_STEPS

    paths = []
    for step in steps:
        grib_data = download_fields(date, cycle, step, SURFACE_PARAMS,
                                    levtype="sfc", source=source)
        if not grib_data:
            log.warning(f"No surface data for {date}/{cycle}/step={step}")
            continue

        grib_path = output_dir / "grib" / f"{date}_{cycle}_{step:03d}h_sfc.grib2"
        save_grib(grib_data, grib_path)
        paths.append(grib_path)

    return paths


def fetch_pressure_fields(date: str, cycle: str = "12z", steps: list[int] | None = None,
                          output_dir: Path = OUTPUT_DIR, source: str = "aws") -> list[Path]:
    """Fetch pressure-level fields for IVT computation."""
    if steps is None:
        steps = ANALYSIS_STEPS

    paths = []
    for step in steps:
        grib_data = download_fields(date, cycle, step, IVT_PARAMS,
                                    levtype="pl", levels=IVT_LEVELS, source=source)
        if not grib_data:
            log.warning(f"No pressure-level data for {date}/{cycle}/step={step}")
            continue

        grib_path = output_dir / "grib" / f"{date}_{cycle}_{step:03d}h_pl.grib2"
        save_grib(grib_data, grib_path)
        paths.append(grib_path)

    return paths


def fetch_storm_period(output_dir: Path = OUTPUT_DIR, source: str = "aws",
                       surface_only: bool = False):
    """Fetch all fields for the Jan 25 – Feb 10 2026 storm period."""
    log.info(f"Fetching ECMWF HRES data for {len(STORM_DATES)} dates from {source}")
    log.info(f"Output directory: {output_dir}")

    all_paths = []

    for date in STORM_DATES:
        log.info(f"--- {date} ---")

        # Try preferred cycles in order
        for cycle in PREFERRED_CYCLES:
            sfc_paths = fetch_surface_fields(date, cycle, output_dir=output_dir, source=source)
            if sfc_paths:
                all_paths.extend(sfc_paths)
                if not surface_only:
                    pl_paths = fetch_pressure_fields(date, cycle, output_dir=output_dir,
                                                    source=source)
                    all_paths.extend(pl_paths)
                break
            else:
                log.info(f"  Cycle {cycle} not available, trying next...")
        else:
            log.warning(f"  No data available for {date}")

    log.info(f"\nDone. Downloaded {len(all_paths)} GRIB files to {output_dir}/grib/")
    return all_paths


def convert_to_cog(output_dir: Path = OUTPUT_DIR, bbox: dict | None = None):
    """Convert all downloaded GRIB files to Cloud-Optimized GeoTIFFs."""
    grib_dir = output_dir / "grib"
    if not grib_dir.exists():
        log.error(f"No GRIB directory found at {grib_dir}")
        return

    if bbox is None:
        bbox = BBOX_SYNOPTIC

    grib_files = sorted(grib_dir.glob("*.grib2"))
    log.info(f"Converting {len(grib_files)} GRIB files to COG...")

    for grib_path in grib_files:
        cog_path = output_dir / (grib_path.stem + ".tif")
        try:
            grib_to_cog(grib_path, cog_path, bbox=bbox)
        except Exception as e:
            log.error(f"Failed to convert {grib_path}: {e}")


def check_availability(date: str | None = None, source: str = "aws"):
    """Check what dates/cycles are available on the archive."""
    if date:
        # Check specific date
        for cycle in ["00z", "06z", "12z", "18z"]:
            entries = fetch_index(date, cycle, 0, source)
            if entries:
                params = set(e.get("param") for e in entries)
                log.info(f"  {date}/{cycle}: {len(entries)} fields, params: {sorted(params)}")
            else:
                log.info(f"  {date}/{cycle}: not available")
    else:
        # Check date range from AWS
        log.info("Checking AWS S3 archive for available dates...")
        resp = requests.get(
            f"{AWS_BASE}/?list-type=2&prefix=&delimiter=/&max-keys=10",
            timeout=15,
        )
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)
        ns = "{http://s3.amazonaws.com/doc/2006-03-01/}"
        prefixes = [p.text.strip("/") for p in root.findall(f".//{ns}Prefix")]
        dates = sorted([p for p in prefixes if p.isdigit()])
        if dates:
            log.info(f"  Oldest: {dates[0]}, Newest: {dates[-1]}")
            log.info(f"  Total date directories: {len(dates)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch ECMWF Open Data HRES from AWS S3 archive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", help="Command")

    # Storm period (default)
    storm_p = sub.add_parser("storm", help="Fetch full Jan 25 – Feb 10 2026 storm period")
    storm_p.add_argument("--surface-only", action="store_true",
                         help="Skip pressure-level fields (faster, no IVT)")
    storm_p.add_argument("--output", type=Path, default=OUTPUT_DIR)

    # Single date
    date_p = sub.add_parser("date", help="Fetch specific date")
    date_p.add_argument("date", help="Date in YYYYMMDD format")
    date_p.add_argument("--cycle", default="12z", choices=["00z", "06z", "12z", "18z"])
    date_p.add_argument("--steps", nargs="+", type=int, default=[0])
    date_p.add_argument("--output", type=Path, default=OUTPUT_DIR)

    # Latest
    latest_p = sub.add_parser("latest", help="Fetch most recent forecast")
    latest_p.add_argument("--output", type=Path, default=OUTPUT_DIR)

    # Check availability
    check_p = sub.add_parser("check", help="Check data availability")
    check_p.add_argument("--date", help="Specific date to check (YYYYMMDD)")

    # Convert GRIB to COG
    convert_p = sub.add_parser("convert", help="Convert downloaded GRIBs to COGs")
    convert_p.add_argument("--output", type=Path, default=OUTPUT_DIR)
    convert_p.add_argument("--bbox", choices=["synoptic", "iberia"], default="synoptic")

    args = parser.parse_args()

    if args.command is None or args.command == "storm":
        output = getattr(args, "output", OUTPUT_DIR)
        surface_only = getattr(args, "surface_only", False)
        fetch_storm_period(output_dir=output, surface_only=surface_only)

    elif args.command == "date":
        log.info(f"Fetching {args.date} {args.cycle} steps={args.steps}")
        fetch_surface_fields(args.date, args.cycle, args.steps, args.output)
        fetch_pressure_fields(args.date, args.cycle, args.steps, args.output)

    elif args.command == "latest":
        from ecmwf.opendata import Client
        client = Client()
        # Use the library to get latest, then download via our byte-range method
        log.info("Fetching latest forecast via ecmwf-opendata client...")
        today = datetime.utcnow().strftime("%Y%m%d")
        for cycle in PREFERRED_CYCLES:
            entries = fetch_index(today, cycle, 0, source="ecmwf")
            if entries:
                fetch_surface_fields(today, cycle, output_dir=args.output, source="ecmwf")
                break

    elif args.command == "check":
        check_availability(args.date)

    elif args.command == "convert":
        bbox = BBOX_SYNOPTIC if args.bbox == "synoptic" else BBOX_IBERIA
        convert_to_cog(args.output, bbox)


if __name__ == "__main__":
    main()
