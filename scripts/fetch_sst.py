"""Dataset 1: SST Anomaly from NOAA OISST v2.1
Downloads NetCDF files first, then processes to COG.
"""
import xarray as xr
import rioxarray
import numpy as np
import requests
from pathlib import Path
from datetime import datetime, timedelta
import time
import tempfile

sst_dir = Path("data/temporal/sst/daily")
sst_dir.mkdir(parents=True, exist_ok=True)
nc_cache = Path("data/temporal/sst/_nc_cache")
nc_cache.mkdir(parents=True, exist_ok=True)

bbox = {"lon_min": -60, "lon_max": 5, "lat_min": 20, "lat_max": 60}

# Generate all dates
start = datetime(2025, 12, 1)
end = datetime(2026, 2, 15)
dates = []
current = start
while current <= end:
    dates.append(current.strftime("%Y%m%d"))
    current += timedelta(days=1)

print(f"Fetching {len(dates)} days of SST anomaly...", flush=True)

for date_str in dates:
    cog_path = sst_dir / f"sst_anom_{date_str}.tif"
    if cog_path.exists():
        print(f"  {date_str}: exists, skipping", flush=True)
        continue

    yyyymm = date_str[:6]
    url = f"https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/{yyyymm}/oisst-avhrr-v02r01.{date_str}.nc"

    # Download to local file first, then open with xarray
    nc_path = nc_cache / f"oisst-{date_str}.nc"

    if not nc_path.exists():
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            nc_path.write_bytes(resp.content)
        except Exception as e:
            print(f"  {date_str}: DOWNLOAD FAILED ({e})", flush=True)
            continue

    try:
        ds = xr.open_dataset(nc_path)
        anom = ds["anom"].squeeze()

        # Convert 0-360 to -180/180 longitude
        anom = anom.assign_coords(lon=(((anom.lon + 180) % 360) - 180))
        anom = anom.sortby("lon")

        # Clip to North Atlantic
        anom_clip = anom.sel(
            lon=slice(bbox["lon_min"], bbox["lon_max"]),
            lat=slice(bbox["lat_min"], bbox["lat_max"])
        )
        # If lat is descending, flip the slice
        if len(anom_clip.lat) == 0:
            anom_clip = anom.sel(
                lon=slice(bbox["lon_min"], bbox["lon_max"]),
                lat=slice(bbox["lat_max"], bbox["lat_min"])
            )

        anom_clip = anom_clip.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
        anom_clip = anom_clip.rio.write_crs("EPSG:4326")
        anom_clip.rio.to_raster(str(cog_path), driver="COG", dtype="float32")

        ds.close()
        print(f"  {date_str}: OK ({float(anom_clip.min()):.1f} to {float(anom_clip.max()):.1f} °C)", flush=True)
    except Exception as e:
        print(f"  {date_str}: PROCESS FAILED ({e})", flush=True)
        if nc_path.exists():
            nc_path.unlink()  # Remove corrupt download
        continue

    time.sleep(0.5)

# Clean up nc cache
import shutil
shutil.rmtree(nc_cache, ignore_errors=True)

# Combine into single NetCDF
print("\nCombining into single NetCDF...", flush=True)
tifs = sorted(sst_dir.glob("sst_anom_*.tif"))
arrays = []
for tif in tifs:
    da = rioxarray.open_rasterio(tif).squeeze()
    date_str = tif.stem.split("_")[-1]
    da = da.assign_coords(time=datetime.strptime(date_str, "%Y%m%d"))
    arrays.append(da)

if arrays:
    combined = xr.concat(arrays, dim="time")
    combined.to_netcdf("data/temporal/sst/sst_anomaly.nc")
    print(f"Combined: {len(arrays)} days, shape {combined.shape}", flush=True)
else:
    print("ERROR: No SST files to combine!", flush=True)
