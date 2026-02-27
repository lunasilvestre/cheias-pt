"""ERA5 Synoptic Fields Acquisition via CDS API

Downloads mean sea level pressure, 10m winds (u,v), and wind gust from
ERA5 reanalysis-era5-single-levels, then processes to Cloud-Optimized GeoTIFFs.

Domain: 36N-60N, 60W-5E (North Atlantic + Iberia)
Temporal:
  - Hourly for storm periods:
      Kristin:  Jan 26-30, 2026
      Leonardo: Feb 4-8, 2026
      Marta:    Feb 9-12, 2026
  - 6-hourly (00,06,12,18 UTC) for remaining days: Dec 1 2025 - Feb 15 2026

Output: data/cog/{mslp,wind-u,wind-v,wind-gust}/YYYY-MM-DDTHH.tif

Usage:
  python scripts/fetch_era5_synoptic.py test          # single test day (Jan 28)
  python scripts/fetch_era5_synoptic.py full           # full Dec 1 - Feb 15
  python scripts/fetch_era5_synoptic.py storms-only    # only storm periods (hourly)
"""
import cdsapi
import xarray as xr
import rioxarray  # noqa: F401 — registers .rio accessor
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os
import logging

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path("/home/nls/Documents/dev/cheias-pt")
NC_CACHE = BASE_DIR / "data" / "temporal" / "era5" / "_nc_cache"
COG_DIRS = {
    "mean_sea_level_pressure": BASE_DIR / "data" / "cog" / "mslp",
    "10m_u_component_of_wind": BASE_DIR / "data" / "cog" / "wind-u",
    "10m_v_component_of_wind": BASE_DIR / "data" / "cog" / "wind-v",
    "instantaneous_10m_wind_gust": BASE_DIR / "data" / "cog" / "wind-gust",
}

# CDS API variable names
VARIABLES = list(COG_DIRS.keys())

# Short names in the NetCDF/GRIB files (ERA5 convention)
SHORT_NAMES = {
    "mean_sea_level_pressure": "msl",
    "10m_u_component_of_wind": "u10",
    "10m_v_component_of_wind": "v10",
    "instantaneous_10m_wind_gust": "i10fg",
}

# Domain: North, West, South, East
AREA = [60, -60, 36, 5]

# Storm periods get hourly data (name, start, end inclusive)
STORM_PERIODS = [
    ("Kristin",  datetime(2026, 1, 26), datetime(2026, 1, 30)),
    ("Leonardo", datetime(2026, 2, 4),  datetime(2026, 2, 8)),
    ("Marta",    datetime(2026, 2, 9),  datetime(2026, 2, 12)),
]

# Full range
RANGE_START = datetime(2025, 12, 1)
RANGE_END = datetime(2026, 2, 15)

# Hours for 6-hourly vs hourly
HOURS_6H = ["00:00", "06:00", "12:00", "18:00"]
HOURS_ALL = [f"{h:02d}:00" for h in range(24)]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("era5")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def ensure_dirs():
    """Create all output directories."""
    NC_CACHE.mkdir(parents=True, exist_ok=True)
    for d in COG_DIRS.values():
        d.mkdir(parents=True, exist_ok=True)


def _is_storm_day(dt):
    """Check if a date falls within any storm period."""
    for _name, start, end in STORM_PERIODS:
        if start <= dt <= end:
            return True
    return False


def build_requests(storms_only=False):
    """Build a list of CDS API request dicts, batched by month.

    Args:
        storms_only: If True, only build requests for storm periods (hourly).

    Returns list of (label, request_dict, nc_path) tuples.
    """
    from collections import defaultdict

    month_days = defaultdict(list)  # (year, month) -> [(day, [hours])]

    if storms_only:
        # Only storm period days, all hourly
        for name, start, end in STORM_PERIODS:
            current = start
            while current <= end:
                key = (current.year, current.month)
                month_days[key].append((current.day, HOURS_ALL))
                current += timedelta(days=1)
    else:
        # Full range: hourly for storm days, 6-hourly otherwise
        current = RANGE_START
        while current <= RANGE_END:
            hours = HOURS_ALL if _is_storm_day(current) else HOURS_6H
            key = (current.year, current.month)
            month_days[key].append((current.day, hours))
            current += timedelta(days=1)

    requests = []
    for (year, month), day_hours in sorted(month_days.items()):
        # Within a month, separate hourly vs 6-hourly batches
        hourly_days = [d for d, h in day_hours if len(h) == 24]
        sixhourly_days = [d for d, h in day_hours if len(h) == 4]

        if hourly_days:
            label = f"{year}-{month:02d}_hourly"
            nc_path = NC_CACHE / f"era5_{label}.nc"
            req = {
                "product_type": ["reanalysis"],
                "variable": VARIABLES,
                "year": [str(year)],
                "month": [f"{month:02d}"],
                "day": [f"{d:02d}" for d in sorted(hourly_days)],
                "time": HOURS_ALL,
                "data_format": "netcdf",
                "download_format": "unarchived",
                "area": AREA,
            }
            requests.append((label, req, nc_path))

        if sixhourly_days:
            label = f"{year}-{month:02d}_6hourly"
            nc_path = NC_CACHE / f"era5_{label}.nc"
            req = {
                "product_type": ["reanalysis"],
                "variable": VARIABLES,
                "year": [str(year)],
                "month": [f"{month:02d}"],
                "day": [f"{d:02d}" for d in sorted(sixhourly_days)],
                "time": HOURS_6H,
                "data_format": "netcdf",
                "download_format": "unarchived",
                "area": AREA,
            }
            requests.append((label, req, nc_path))

    return requests


def cog_path_for(variable: str, time_val) -> Path:
    """Generate COG path for a variable at a specific time."""
    if hasattr(time_val, "dt"):
        ts = time_val
    else:
        ts = np.datetime64(time_val)
    dt = ts.astype("datetime64[s]").astype(datetime)
    fname = dt.strftime("%Y-%m-%dT%H") + ".tif"
    return COG_DIRS[variable] / fname


def all_cogs_exist(nc_path: Path) -> bool:
    """Quick check: if the NC file has been fully processed, skip."""
    if not nc_path.exists():
        return False
    try:
        ds = xr.open_dataset(nc_path)
        for var in VARIABLES:
            sn = SHORT_NAMES[var]
            if sn not in ds:
                ds.close()
                return False
            for t in ds.valid_time.values:
                if not cog_path_for(var, t).exists():
                    ds.close()
                    return False
        ds.close()
        return True
    except Exception:
        return False


def process_nc_to_cogs(nc_path: Path, label: str):
    """Extract each variable x timestep from a NetCDF to COG."""
    log.info("Processing %s -> COGs", nc_path.name)
    ds = xr.open_dataset(nc_path)

    # ERA5 NetCDF uses 'valid_time' for the time dimension
    time_dim = "valid_time" if "valid_time" in ds.dims else "time"

    total = 0
    skipped = 0
    for var in VARIABLES:
        sn = SHORT_NAMES[var]
        if sn not in ds:
            log.warning("  Variable %s (short: %s) not found in %s", var, sn, nc_path.name)
            continue

        da = ds[sn]

        # Ensure CRS is set (ERA5 is regular lat-lon = EPSG:4326)
        if "latitude" in da.dims and "longitude" in da.dims:
            da = da.rename({"latitude": "y", "longitude": "x"})
        da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")
        da = da.rio.write_crs("EPSG:4326")

        for t_idx in range(len(ds[time_dim])):
            t_val = ds[time_dim].values[t_idx]
            out_path = cog_path_for(var, t_val)

            if out_path.exists():
                skipped += 1
                continue

            slice_da = da.isel({time_dim: t_idx})

            # Write COG with LZW compression
            slice_da.rio.to_raster(
                str(out_path),
                driver="COG",
                compress="LZW",
                dtype="float32",
            )
            total += 1

    ds.close()
    log.info("  %s: wrote %d COGs, skipped %d existing", label, total, skipped)


def download_and_process(client, label, request, nc_path):
    """Download from CDS (if needed) and process to COGs."""
    # Check if already fully processed
    if all_cogs_exist(nc_path):
        log.info("SKIP %s: all COGs already exist", label)
        return True

    # Download if NC doesn't exist
    if not nc_path.exists():
        log.info("REQUESTING %s from CDS API...", label)
        try:
            client.retrieve(
                "reanalysis-era5-single-levels",
                request,
                str(nc_path),
            )
            log.info("  Downloaded: %s (%.1f MB)", nc_path.name, nc_path.stat().st_size / 1e6)
        except Exception as e:
            log.error("  FAILED to download %s: %s", label, e)
            return False
    else:
        log.info("NC cache hit: %s", nc_path.name)

    # Process to COGs
    try:
        process_nc_to_cogs(nc_path, label)
        return True
    except Exception as e:
        log.error("  FAILED to process %s: %s", label, e)
        return False


# ---------------------------------------------------------------------------
# Test mode: single day to verify pipeline
# ---------------------------------------------------------------------------
def run_test(client):
    """Download and process a single test day: Jan 28, 2026 (storm peak)."""
    label = "test_2026-01-28"
    nc_path = NC_CACHE / "era5_test_2026-01-28.nc"

    request = {
        "product_type": ["reanalysis"],
        "variable": VARIABLES,
        "year": ["2026"],
        "month": ["01"],
        "day": ["28"],
        "time": HOURS_ALL,  # 24 hours for testing
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": AREA,
    }

    log.info("=" * 60)
    log.info("TEST MODE: Fetching Jan 28, 2026 (all 24 hours)")
    log.info("=" * 60)

    success = download_and_process(client, label, request, nc_path)

    if success:
        # Verify outputs
        for var in VARIABLES:
            d = COG_DIRS[var]
            count = len(list(d.glob("2026-01-28T*.tif")))
            log.info("  %s: %d COGs for Jan 28", d.name, count)

    return success


# ---------------------------------------------------------------------------
# Full acquisition
# ---------------------------------------------------------------------------
def run_full(client):
    """Download and process the full temporal range."""
    requests = build_requests(storms_only=False)
    log.info("=" * 60)
    log.info("FULL MODE: %d batches to process", len(requests))
    log.info("=" * 60)

    _run_batches(client, requests)


def run_storms_only(client):
    """Download and process only the storm periods (hourly)."""
    requests = build_requests(storms_only=True)
    log.info("=" * 60)
    log.info("STORMS-ONLY MODE: %d batches to process", len(requests))
    for name, start, end in STORM_PERIODS:
        log.info("  %s: %s to %s", name, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    log.info("=" * 60)

    _run_batches(client, requests)


def _run_batches(client, requests):
    """Execute a list of CDS download+process batches."""
    results = {"ok": 0, "fail": 0}
    for label, request, nc_path in requests:
        ok = download_and_process(client, label, request, nc_path)
        results["ok" if ok else "fail"] += 1

    log.info("=" * 60)
    log.info("DONE: %d OK, %d failed", results["ok"], results["fail"])
    log.info("=" * 60)

    # Summary
    for var in VARIABLES:
        d = COG_DIRS[var]
        count = len(list(d.glob("*.tif")))
        log.info("  %s: %d total COGs", d.name, count)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ensure_dirs()
    client = cdsapi.Client()

    mode = sys.argv[1] if len(sys.argv) > 1 else "test"

    if mode == "test":
        success = run_test(client)
        sys.exit(0 if success else 1)
    elif mode == "full":
        run_full(client)
    elif mode == "storms-only":
        run_storms_only(client)
    else:
        print(f"Usage: {sys.argv[0]} [test|full|storms-only]")
        sys.exit(1)


if __name__ == "__main__":
    main()
