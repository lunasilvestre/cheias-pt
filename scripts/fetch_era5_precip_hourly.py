"""ERA5 Hourly Precipitation Acquisition via CDS API

Downloads mean total precipitation rate (mtpr) from ERA5 reanalysis-era5-single-levels,
converts m/s to mm/hr, then writes Cloud-Optimized GeoTIFFs.

Domain: 36N-60N, 60W-5E (North Atlantic + Iberia)
Storm windows:
  - Kristin:  Jan 26-30, 2026 (120 hours)
  - Leonardo: Feb 4-8, 2026   (120 hours)
  - Marta:    Feb 9-12, 2026  (96 hours)
  Total: ~336 hourly COGs.

Output: data/cog/precipitation-hourly/YYYY-MM-DDTHH.tif
"""
import cdsapi
import xarray as xr
import rioxarray  # noqa: F401 — registers .rio accessor
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys
import logging

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path("/home/nls/Documents/dev/cheias-pt")
NC_CACHE = BASE_DIR / "data" / "temporal" / "era5" / "_nc_cache"
COG_DIR = BASE_DIR / "data" / "cog" / "precipitation-hourly"

# CDS API variable name
VARIABLE = "mean_total_precipitation_rate"
# Short name in ERA5 NetCDF (CDS returns 'avg_tprate' for this variable)
SHORT_NAME = "avg_tprate"

# Domain: North, West, South, East
AREA = [60, -60, 36, 5]

# Storm windows: (label, start_date, end_date) — end is inclusive
STORM_WINDOWS = [
    ("kristin", datetime(2026, 1, 26), datetime(2026, 1, 30)),
    ("leonardo", datetime(2026, 2, 4), datetime(2026, 2, 8)),
    ("marta", datetime(2026, 2, 9), datetime(2026, 2, 12)),
]

# All 24 hours
HOURS_ALL = [f"{h:02d}:00" for h in range(24)]

# Conversion: kg/m2/s (= mm/s) -> mm/hr (multiply by 3600)
# ERA5 mtpr units are kg m**-2 s**-1, equivalent to mm/s for water
KGM2S_TO_MMHR = 3600.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("era5-precip")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def ensure_dirs():
    """Create all output directories."""
    NC_CACHE.mkdir(parents=True, exist_ok=True)
    COG_DIR.mkdir(parents=True, exist_ok=True)


def cog_path_for(time_val) -> Path:
    """Generate COG path for a specific time."""
    ts = np.datetime64(time_val)
    dt = ts.astype("datetime64[s]").astype(datetime)
    fname = dt.strftime("%Y-%m-%dT%H") + ".tif"
    return COG_DIR / fname


def build_requests():
    """Build CDS API request dicts, one per storm window per month.

    Returns list of (label, request_dict, nc_path) tuples.
    """
    from collections import defaultdict

    requests = []

    for storm_label, start, end in STORM_WINDOWS:
        # Group days by month
        month_days = defaultdict(list)
        current = start
        while current <= end:
            key = (current.year, current.month)
            month_days[key].append(current.day)
            current += timedelta(days=1)

        for (year, month), days in sorted(month_days.items()):
            label = f"precip_{storm_label}_{year}-{month:02d}"
            nc_path = NC_CACHE / f"era5_{label}.nc"
            req = {
                "product_type": ["reanalysis"],
                "variable": [VARIABLE],
                "year": [str(year)],
                "month": [f"{month:02d}"],
                "day": [f"{d:02d}" for d in sorted(days)],
                "time": HOURS_ALL,
                "data_format": "netcdf",
                "download_format": "unarchived",
                "area": AREA,
            }
            requests.append((label, req, nc_path))

    return requests


def all_cogs_exist(nc_path: Path) -> bool:
    """Quick check: if the NC file has been fully processed, skip."""
    if not nc_path.exists():
        return False
    try:
        ds = xr.open_dataset(nc_path)
        time_dim = "valid_time" if "valid_time" in ds.dims else "time"
        if SHORT_NAME not in ds:
            ds.close()
            return False
        for t in ds[time_dim].values:
            if not cog_path_for(t).exists():
                ds.close()
                return False
        ds.close()
        return True
    except Exception:
        return False


def process_nc_to_cogs(nc_path: Path, label: str):
    """Extract each timestep from a NetCDF, convert m/s -> mm/hr, write COG."""
    log.info("Processing %s -> COGs", nc_path.name)
    ds = xr.open_dataset(nc_path)

    time_dim = "valid_time" if "valid_time" in ds.dims else "time"

    if SHORT_NAME not in ds:
        log.error("  Variable %s not found in %s. Available: %s",
                  SHORT_NAME, nc_path.name, list(ds.data_vars))
        ds.close()
        return

    da = ds[SHORT_NAME]

    # Rename dims for rioxarray
    if "latitude" in da.dims and "longitude" in da.dims:
        da = da.rename({"latitude": "y", "longitude": "x"})
    da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")
    da = da.rio.write_crs("EPSG:4326")

    total = 0
    skipped = 0
    for t_idx in range(len(ds[time_dim])):
        t_val = ds[time_dim].values[t_idx]
        out_path = cog_path_for(t_val)

        if out_path.exists():
            skipped += 1
            continue

        slice_da = da.isel({time_dim: t_idx})

        # Convert kg/m2/s -> mm/hr
        slice_da = slice_da * KGM2S_TO_MMHR

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
    if all_cogs_exist(nc_path):
        log.info("SKIP %s: all COGs already exist", label)
        return True

    if not nc_path.exists():
        log.info("REQUESTING %s from CDS API...", label)
        try:
            client.retrieve(
                "reanalysis-era5-single-levels",
                request,
                str(nc_path),
            )
            log.info("  Downloaded: %s (%.1f MB)",
                     nc_path.name, nc_path.stat().st_size / 1e6)
        except Exception as e:
            log.error("  FAILED to download %s: %s", label, e)
            return False
    else:
        log.info("NC cache hit: %s", nc_path.name)

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
    label = "precip_test_2026-01-28"
    nc_path = NC_CACHE / f"era5_{label}.nc"

    request = {
        "product_type": ["reanalysis"],
        "variable": [VARIABLE],
        "year": ["2026"],
        "month": ["01"],
        "day": ["28"],
        "time": HOURS_ALL,
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": AREA,
    }

    log.info("=" * 60)
    log.info("TEST MODE: Fetching precip for Jan 28, 2026 (24 hours)")
    log.info("=" * 60)

    success = download_and_process(client, label, request, nc_path)

    if success:
        count = len(list(COG_DIR.glob("2026-01-28T*.tif")))
        log.info("  precipitation-hourly: %d COGs for Jan 28", count)

        # Quick sanity check on values
        sample = list(COG_DIR.glob("2026-01-28T12.tif"))
        if sample:
            ds = xr.open_dataset(sample[0], engine="rasterio")
            vals = ds.band_data.values if "band_data" in ds else ds[list(ds.data_vars)[0]].values
            log.info("  Sample (Jan 28 12UTC): min=%.2f, max=%.2f, mean=%.2f mm/hr",
                     float(np.nanmin(vals)), float(np.nanmax(vals)), float(np.nanmean(vals)))
            ds.close()

    return success


# ---------------------------------------------------------------------------
# Full acquisition
# ---------------------------------------------------------------------------
def run_full(client):
    """Download and process all storm windows."""
    requests = build_requests()
    log.info("=" * 60)
    log.info("FULL MODE: %d batches to process", len(requests))
    for label, _, _ in requests:
        log.info("  - %s", label)
    log.info("=" * 60)

    results = {"ok": 0, "fail": 0}
    for label, request, nc_path in requests:
        ok = download_and_process(client, label, request, nc_path)
        results["ok" if ok else "fail"] += 1

    log.info("=" * 60)
    log.info("DONE: %d OK, %d failed", results["ok"], results["fail"])
    total_cogs = len(list(COG_DIR.glob("*.tif")))
    log.info("  precipitation-hourly: %d total COGs", total_cogs)
    log.info("=" * 60)


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
    else:
        print(f"Usage: {sys.argv[0]} [test|full]")
        sys.exit(1)


if __name__ == "__main__":
    main()
