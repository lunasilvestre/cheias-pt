"""Fix existing SST TIFs (÷100), fetch missing Feb dates, output COGs to data/cog/sst/"""
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import requests
import xarray as xr
import rioxarray
import time
import sys

ROOT = Path("/home/nls/Documents/dev/cheias-pt")
SST_DAILY = ROOT / "data/temporal/sst/daily"
COG_OUT = ROOT / "data/cog/sst"
NC_CACHE = ROOT / "data/temporal/sst/_nc_cache"
COG_OUT.mkdir(parents=True, exist_ok=True)
NC_CACHE.mkdir(parents=True, exist_ok=True)

BBOX = {"lon_min": -60, "lon_max": 5, "lat_min": 20, "lat_max": 60}
NODATA = -999.0

# --- Dates ---
start = datetime(2025, 12, 1)
end = datetime(2026, 2, 15)
all_dates = []
cur = start
while cur <= end:
    all_dates.append(cur)
    cur += timedelta(days=1)

print(f"Target: {len(all_dates)} days ({start.date()} to {end.date()})")


def write_cog(data, profile, out_path):
    """Write a Float32 COG with overviews."""
    profile.update(
        driver="GTiff",
        dtype="float32",
        compress="lzw",
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )
    # Remove COG-specific keys that conflict with GTiff driver
    for key in ["OVERVIEW_RESAMPLING", "COMPRESS", "BLOCKXSIZE", "BLOCKYSIZE"]:
        profile.pop(key, None)

    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(data.astype(np.float32), 1)
        dst.build_overviews([2, 4, 8], Resampling.average)
        dst.update_tags(ns="rio_overview", resampling="average")


# --- Task 1 + 3: Fix existing TIFs and output as COGs ---
print("\n=== Task 1+3: Fix existing TIFs (÷100) → COGs ===")
existing = sorted(SST_DAILY.glob("sst_anom_*.tif"))
fixed_count = 0
for tif in existing:
    date_str = tif.stem.split("_")[-1]
    iso_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    cog_path = COG_OUT / f"{iso_date}.tif"

    if cog_path.exists():
        print(f"  {iso_date}: COG exists, skipping")
        continue

    with rasterio.open(tif) as src:
        data = src.read(1)
        nodata_val = src.nodata if src.nodata is not None else NODATA
        mask = np.isclose(data, nodata_val) | np.isnan(data)
        corrected = np.where(mask, NODATA, data / 100.0)

        profile = src.profile.copy()
        profile["nodata"] = NODATA

    write_cog(corrected, profile, cog_path)
    fixed_count += 1

    # Quick stats
    valid = corrected[~np.isclose(corrected, NODATA)]
    print(f"  {iso_date}: fixed → {valid.min():.2f} to {valid.max():.2f} °C")

print(f"Fixed {fixed_count} TIFs")

# --- Task 2: Fetch missing Feb 1-15 ---
print("\n=== Task 2: Fetch missing Feb dates ===")
fetch_count = 0
fetch_failed = []

for dt in all_dates:
    date_str = dt.strftime("%Y%m%d")
    iso_date = dt.strftime("%Y-%m-%d")
    cog_path = COG_OUT / f"{iso_date}.tif"

    if cog_path.exists():
        continue

    # Need to fetch from NOAA
    yyyymm = date_str[:6]
    url = f"https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/{yyyymm}/oisst-avhrr-v02r01.{date_str}.nc"

    nc_path = NC_CACHE / f"oisst-{date_str}.nc"

    if not nc_path.exists():
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            nc_path.write_bytes(resp.content)
        except Exception as e:
            print(f"  {iso_date}: DOWNLOAD FAILED ({e})")
            fetch_failed.append(iso_date)
            continue

    try:
        ds = xr.open_dataset(nc_path)
        anom = ds["anom"].squeeze()

        # Convert 0-360 → -180/180
        anom = anom.assign_coords(lon=(((anom.lon + 180) % 360) - 180))
        anom = anom.sortby("lon")

        # Clip to North Atlantic
        anom_clip = anom.sel(
            lon=slice(BBOX["lon_min"], BBOX["lon_max"]),
            lat=slice(BBOX["lat_min"], BBOX["lat_max"]),
        )
        if len(anom_clip.lat) == 0:
            anom_clip = anom.sel(
                lon=slice(BBOX["lon_min"], BBOX["lon_max"]),
                lat=slice(BBOX["lat_max"], BBOX["lat_min"]),
            )

        anom_clip = anom_clip.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
        anom_clip = anom_clip.rio.write_crs("EPSG:4326")

        # Get the data as numpy — values from xarray should be properly decoded
        data_arr = anom_clip.values.astype(np.float32)

        # Check if values look like they need ÷100
        valid_vals = data_arr[~np.isnan(data_arr)]
        if len(valid_vals) > 0 and (valid_vals.max() > 50 or valid_vals.min() < -50):
            print(f"  {iso_date}: raw range {valid_vals.min():.0f}–{valid_vals.max():.0f}, applying ÷100")
            mask = np.isnan(data_arr)
            data_arr = np.where(mask, NODATA, data_arr / 100.0)
        else:
            mask = np.isnan(data_arr)
            data_arr = np.where(mask, NODATA, data_arr)

        # Build profile from xarray spatial info
        transform = from_bounds(
            float(anom_clip.lon.min()),
            float(anom_clip.lat.min()),
            float(anom_clip.lon.max()),
            float(anom_clip.lat.max()),
            data_arr.shape[1],
            data_arr.shape[0],
        )
        profile = {
            "driver": "GTiff",
            "dtype": "float32",
            "width": data_arr.shape[1],
            "height": data_arr.shape[0],
            "count": 1,
            "crs": "EPSG:4326",
            "transform": transform,
            "nodata": NODATA,
        }

        write_cog(data_arr, profile, cog_path)
        ds.close()

        valid = data_arr[~np.isclose(data_arr, NODATA)]
        print(f"  {iso_date}: fetched → {valid.min():.2f} to {valid.max():.2f} °C")
        fetch_count += 1
        time.sleep(0.5)

    except Exception as e:
        print(f"  {iso_date}: PROCESS FAILED ({e})")
        fetch_failed.append(iso_date)
        if nc_path.exists():
            nc_path.unlink()
        continue

print(f"Fetched {fetch_count} new dates")
if fetch_failed:
    print(f"Failed dates: {', '.join(fetch_failed)}")

# --- Summary ---
print("\n=== Summary ===")
cogs = sorted(COG_OUT.glob("*.tif"))
# Filter out .aux.xml noise
cogs = [c for c in cogs if c.suffix == ".tif" and not c.name.endswith(".aux.xml")]
print(f"Total COGs: {len(cogs)}")
if cogs:
    print(f"Date range: {cogs[0].stem} to {cogs[-1].stem}")

    # Spot-check 3 files
    for path in [cogs[0], cogs[len(cogs) // 2], cogs[-1]]:
        with rasterio.open(path) as src:
            data = src.read(1)
            valid = data[~np.isclose(data, NODATA)]
            print(f"  {path.name}: {valid.min():.2f} to {valid.max():.2f} °C (mean {valid.mean():.2f})")

# Clean nc cache
import shutil
shutil.rmtree(NC_CACHE, ignore_errors=True)
print("\nDone.")
