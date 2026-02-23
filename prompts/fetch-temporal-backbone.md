# Task: Temporal Data Backbone — Full Crisis Window Acquisition

## Context

cheias.pt scrollytelling narrative covers the full Jan-Feb 2026 Portugal flood crisis: five storms (Harry, Ingrid/Joseph, Kristin, Leonardo, Marta) driven by a persistent NAO-negative blocking pattern. The narrative needs continuous daily data from **Dec 1, 2025 through Feb 15, 2026** (77 days) across six datasets that power six story chapters.

This is the single most important data task. Every chapter depends on this temporal backbone.

## Environment

```bash
source .venv/bin/activate
```

Install everything upfront:
```bash
pip install xarray netcdf4 rioxarray numpy pandas requests tqdm pyarrow
```

## Time Window

```python
START_DATE = "2025-12-01"
END_DATE = "2026-02-15"
```

## Output Structure

All outputs go in `data/temporal/`:
```
data/temporal/
├── sst/                    # Sea surface temperature anomaly (Chapter 2)
│   ├── daily/              # Individual daily COGs
│   └── sst_anomaly.nc      # Combined NetCDF time series
├── moisture/               # Soil moisture grid (Chapter 3, 5, 7)
│   └── soil_moisture.parquet
├── precipitation/          # Precipitation grid (Chapter 3, 4, 7)
│   └── precipitation.parquet
├── discharge/              # River discharge per basin (Chapter 4, 5)
│   └── discharge.parquet
├── ivt/                    # Integrated vapor transport (Chapter 2)
│   └── ivt.parquet
├── precondition/           # Computed precondition index (Chapter 5, 7)
│   └── precondition.parquet
└── README.md
```

---

## Dataset 1: SST Anomaly (Chapter 2 — Planetary Scale)

**Source:** NOAA OISST v2.1, 0.25° daily grid
**Area:** North Atlantic moisture corridor: 60°W–5°E, 20°N–60°N
**No auth required.**

```python
import xarray as xr
import rioxarray
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

sst_dir = Path("data/temporal/sst/daily")
sst_dir.mkdir(parents=True, exist_ok=True)

bbox = {"lon_min": -60, "lon_max": 5, "lat_min": 20, "lat_max": 60}

# Generate all dates
start = datetime(2025, 12, 1)
end = datetime(2026, 2, 15)
dates = []
current = start
while current <= end:
    dates.append(current.strftime("%Y%m%d"))
    current += timedelta(days=1)

print(f"Fetching {len(dates)} days of SST anomaly...")

for date_str in dates:
    cog_path = sst_dir / f"sst_anom_{date_str}.tif"
    if cog_path.exists():
        print(f"  {date_str}: exists, skipping")
        continue
    
    yyyymm = date_str[:6]
    url = f"https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/{yyyymm}/oisst-avhrr-v02r01.{date_str}.nc"
    
    try:
        ds = xr.open_dataset(url)
    except Exception:
        # Fallback to OpenDAP
        opendap_url = f"https://www.ncei.noaa.gov/thredds/dodsC/OisstBase/NetCDF/V2.1/AVHRR/{yyyymm}/oisst-avhrr-v02r01.{date_str}.nc"
        try:
            ds = xr.open_dataset(opendap_url)
        except Exception as e:
            print(f"  {date_str}: FAILED ({e})")
            continue
    
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
    print(f"  {date_str}: OK ({float(anom_clip.min()):.1f} to {float(anom_clip.max()):.1f} °C)")

# Also combine into a single NetCDF for easy time-series access
print("\nCombining into single NetCDF...")
tifs = sorted(sst_dir.glob("sst_anom_*.tif"))
arrays = []
times = []
for tif in tifs:
    da = rioxarray.open_rasterio(tif).squeeze()
    date_str = tif.stem.split("_")[-1]
    da = da.assign_coords(time=datetime.strptime(date_str, "%Y%m%d"))
    arrays.append(da)
    times.append(datetime.strptime(date_str, "%Y%m%d"))

if arrays:
    combined = xr.concat(arrays, dim="time")
    combined.to_netcdf("data/temporal/sst/sst_anomaly.nc")
    print(f"Combined: {len(arrays)} days, shape {combined.shape}")
```

**Rate limiting:** NOAA servers are public but be polite — add a 0.5s sleep between requests if needed.

---

## Dataset 2: Soil Moisture Grid (Chapters 3, 5, 7 — The Saturating Ground)

**Source:** Open-Meteo Historical API (ERA5-Land), ~11km (0.1°) resolution
**Variables:** `soil_moisture_0_to_7cm`, `soil_moisture_7_to_28cm`, `soil_moisture_28_to_100cm`
**No auth required.**

Define a grid across Portugal:

```python
import numpy as np
import pandas as pd
import requests
import time
from itertools import product

# Portugal bounding box with 0.25° spacing 
# (Open-Meteo snaps to nearest ERA5-Land grid point anyway)
lats = np.arange(36.75, 42.50, 0.25)  # ~23 points
lons = np.arange(-9.75, -6.00, 0.25)  # ~15 points
grid_points = list(product(lats, lons))
print(f"Grid: {len(lats)} x {len(lons)} = {len(grid_points)} points")

all_records = []

for i, (lat, lon) in enumerate(grid_points):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "2025-12-01",
        "end_date": "2026-02-15",
        "daily": "soil_moisture_0_to_7cm_mean,soil_moisture_7_to_28cm_mean,soil_moisture_28_to_100cm_mean",
        "timezone": "UTC"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        daily = data["daily"]
        for j, date in enumerate(daily["time"]):
            all_records.append({
                "date": date,
                "lat": lat,
                "lon": lon,
                "sm_0_7": daily["soil_moisture_0_to_7cm_mean"][j],
                "sm_7_28": daily["soil_moisture_7_to_28cm_mean"][j],
                "sm_28_100": daily["soil_moisture_28_to_100cm_mean"][j],
            })
        
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(grid_points)} points fetched")
    except Exception as e:
        print(f"  Point ({lat}, {lon}) failed: {e}")
    
    time.sleep(0.3)  # Be polite to Open-Meteo

df = pd.DataFrame(all_records)
df["date"] = pd.to_datetime(df["date"])

# Compute weighted root-zone average (matching notebook methodology)
df["sm_rootzone"] = (
    df["sm_0_7"] * 0.07 +
    df["sm_7_28"] * 0.21 +
    df["sm_28_100"] * 0.72
) / (0.07 + 0.21 + 0.72)

outpath = Path("data/temporal/moisture/soil_moisture.parquet")
outpath.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(outpath)
print(f"\nSaved: {outpath} ({len(df)} records, {df['date'].nunique()} days, {len(grid_points)} points)")
print(f"Root-zone moisture range: {df['sm_rootzone'].min():.3f} - {df['sm_rootzone'].max():.3f} m³/m³")
```

---

## Dataset 3: Precipitation Grid (Chapters 3, 4, 7 — Rainfall Accumulation)

**Source:** Open-Meteo Historical API
**Variables:** `precipitation_sum`, `rain_sum`

```python
# Same grid as soil moisture — can combine into one API call per point
# But separating for clarity. If you want efficiency, merge with Dataset 2.

all_records = []

for i, (lat, lon) in enumerate(grid_points):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "2025-12-01",
        "end_date": "2026-02-15",
        "daily": "precipitation_sum,rain_sum",
        "timezone": "UTC"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        daily = data["daily"]
        for j, date in enumerate(daily["time"]):
            all_records.append({
                "date": date,
                "lat": lat,
                "lon": lon,
                "precip_mm": daily["precipitation_sum"][j],
                "rain_mm": daily["rain_sum"][j],
            })
        
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(grid_points)} points fetched")
    except Exception as e:
        print(f"  Point ({lat}, {lon}) failed: {e}")
    
    time.sleep(0.3)

df = pd.DataFrame(all_records)
df["date"] = pd.to_datetime(df["date"])

# Compute rolling accumulations (key for precondition analysis)
# These need to be computed per-point
for point, grp in df.groupby(["lat", "lon"]):
    idx = grp.index
    df.loc[idx, "precip_3d"] = grp["precip_mm"].rolling(3, min_periods=1).sum()
    df.loc[idx, "precip_7d"] = grp["precip_mm"].rolling(7, min_periods=1).sum()
    df.loc[idx, "precip_14d"] = grp["precip_mm"].rolling(14, min_periods=1).sum()
    df.loc[idx, "precip_30d"] = grp["precip_mm"].rolling(30, min_periods=1).sum()

outpath = Path("data/temporal/precipitation/precipitation.parquet")
outpath.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(outpath)
print(f"\nSaved: {outpath} ({len(df)} records)")
print(f"Max daily precip: {df['precip_mm'].max():.1f} mm")
print(f"Max 7-day accumulation: {df['precip_7d'].max():.1f} mm")
```

**IMPORTANT OPTIMIZATION:** Datasets 2 and 3 query the same grid. To halve API calls, combine the variables into a single request per point:
```
daily=soil_moisture_0_to_7cm_mean,soil_moisture_7_to_28cm_mean,soil_moisture_28_to_100cm_mean,precipitation_sum,rain_sum
```
Then split into separate parquet files after. This reduces ~690 calls to ~345.

---

## Dataset 4: River Discharge (Chapters 4, 5 — Rivers Respond)

**Source:** Open-Meteo Flood API (GloFAS proxy), 5km grid
**No auth required.**

```python
# Key monitoring points — one per major basin
# Coordinates from the validated notebook + basin analysis
river_points = [
    {"name": "Tejo - Santarém", "lat": 39.24, "lon": -8.68, "basin": "Tejo"},
    {"name": "Tejo - Vila Franca de Xira", "lat": 38.95, "lon": -8.99, "basin": "Tejo"},
    {"name": "Sado - Alcácer do Sal", "lat": 38.37, "lon": -8.51, "basin": "Sado"},
    {"name": "Mondego - Coimbra", "lat": 40.21, "lon": -8.43, "basin": "Mondego"},
    {"name": "Douro - Porto", "lat": 41.14, "lon": -8.61, "basin": "Douro"},
    {"name": "Douro - Peso da Régua", "lat": 41.16, "lon": -7.79, "basin": "Douro"},
    {"name": "Guadiana - Mértola", "lat": 37.64, "lon": -7.66, "basin": "Guadiana"},
    {"name": "Minho - Valença", "lat": 42.03, "lon": -8.64, "basin": "Minho"},
    {"name": "Vouga - Aveiro", "lat": 40.64, "lon": -8.65, "basin": "Vouga"},
    {"name": "Lis - Leiria", "lat": 39.74, "lon": -8.81, "basin": "Lis"},
    {"name": "Zêzere - Tomar", "lat": 39.60, "lon": -8.41, "basin": "Zêzere"},
]

all_records = []

for point in river_points:
    url = "https://flood-api.open-meteo.com/v1/flood"
    params = {
        "latitude": point["lat"],
        "longitude": point["lon"],
        "start_date": "2025-12-01",
        "end_date": "2026-02-15",
        "daily": "river_discharge,river_discharge_median,river_discharge_max,river_discharge_min",
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        daily = data["daily"]
        for j, date in enumerate(daily["time"]):
            all_records.append({
                "date": date,
                "name": point["name"],
                "basin": point["basin"],
                "lat": point["lat"],
                "lon": point["lon"],
                "discharge": daily["river_discharge"][j],
                "discharge_median": daily["river_discharge_median"][j],
                "discharge_max": daily["river_discharge_max"][j],
                "discharge_min": daily["river_discharge_min"][j],
            })
        print(f"  {point['name']}: OK")
    except Exception as e:
        print(f"  {point['name']}: FAILED ({e})")
    
    time.sleep(0.5)

df = pd.DataFrame(all_records)
df["date"] = pd.to_datetime(df["date"])

# Compute discharge ratio (current / median) — key for flood detection
df["discharge_ratio"] = df["discharge"] / df["discharge_median"].replace(0, np.nan)

outpath = Path("data/temporal/discharge/discharge.parquet")
outpath.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(outpath)
print(f"\nSaved: {outpath}")
print(f"Peak discharge ratios:")
for name, grp in df.groupby("name"):
    peak = grp.loc[grp["discharge_ratio"].idxmax()]
    print(f"  {name}: {peak['discharge_ratio']:.1f}x median on {peak['date'].strftime('%Y-%m-%d')}")
```

---

## Dataset 5: Integrated Vapor Transport Proxy (Chapter 2 — Atmospheric River)

**Source:** Open-Meteo Historical API, pressure level variables
**Strategy:** Compute a simplified IVT from specific humidity and wind at key pressure levels (1000, 925, 850, 700 hPa). This avoids needing a CDS API account.

IVT = (1/g) × Σ(q × √(u² + v²) × Δp) integrated across pressure levels.

We compute this on a COARSER grid (0.5°) across a WIDER area (Atlantic → Iberia) since this is the continental-scale view.

```python
# Coarser grid for wider Atlantic view
ivt_lats = np.arange(25, 55, 0.5)  # 60 points
ivt_lons = np.arange(-45, 5, 0.5)  # 100 points
ivt_grid = list(product(ivt_lats, ivt_lons))
print(f"IVT grid: {len(ivt_lats)} x {len(ivt_lons)} = {len(ivt_grid)} points")
print("WARNING: This is ~6,000 API calls. Will take ~30-45 minutes with rate limiting.")

# Pressure levels for IVT integration
levels = [1000, 925, 850, 700]  # hPa
g = 9.80665  # m/s²

all_records = []

for i, (lat, lon) in enumerate(ivt_grid):
    # Request specific humidity and wind at pressure levels
    hourly_vars = []
    for lev in levels:
        hourly_vars.extend([
            f"specific_humidity_{lev}hPa",
            f"wind_speed_{lev}hPa",
        ])
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "2025-12-01",
        "end_date": "2026-02-15",
        "hourly": ",".join(hourly_vars),
        "timezone": "UTC",
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        hourly = data["hourly"]
        
        # Compute daily mean IVT
        times = pd.to_datetime(hourly["time"])
        
        # Build dataframe of all hourly values
        hdf = pd.DataFrame({"time": times})
        for lev in levels:
            hdf[f"q_{lev}"] = hourly.get(f"specific_humidity_{lev}hPa")
            hdf[f"ws_{lev}"] = hourly.get(f"wind_speed_{lev}hPa")
        
        hdf["date"] = hdf["time"].dt.date
        
        # Compute IVT at each hour, then daily mean
        # Simplified: IVT ≈ (1/g) * Σ(q * wind_speed * Δp)
        # Layer thicknesses (Pa): 1000→925=7500, 925→850=7500, 850→700=15000
        dp = {1000: 7500, 925: 7500, 850: 15000, 700: 15000}
        
        hdf["ivt"] = 0.0
        for lev in levels:
            q = hdf[f"q_{lev}"].fillna(0)
            ws = hdf[f"ws_{lev}"].fillna(0)
            hdf["ivt"] += (1/g) * q * ws * dp[lev]
        
        daily = hdf.groupby("date").agg({"ivt": "mean"}).reset_index()
        
        for _, row in daily.iterrows():
            all_records.append({
                "date": row["date"],
                "lat": lat,
                "lon": lon,
                "ivt": row["ivt"],
            })
        
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(ivt_grid)} points ({(i+1)/len(ivt_grid)*100:.0f}%)")
    except Exception as e:
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(ivt_grid)} (point ({lat},{lon}) failed: {e})")
    
    time.sleep(0.2)

df = pd.DataFrame(all_records)
df["date"] = pd.to_datetime(df["date"])

outpath = Path("data/temporal/ivt/ivt.parquet")
outpath.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(outpath)
print(f"\nSaved: {outpath} ({len(df)} records)")
print(f"IVT range: {df['ivt'].min():.0f} - {df['ivt'].max():.0f} kg/m/s")
```

**IMPORTANT NOTE:** Open-Meteo's pressure level variables may not include `specific_humidity` at all levels. If this fails, check available variables at https://open-meteo.com/en/docs/historical-weather-api and look for `relative_humidity` + `temperature` at pressure levels, from which specific humidity can be derived. Alternatively, fall back to `total_column_water_vapour` if available — it's a simpler proxy that still shows the moisture corridor.

**FALLBACK:** If the IVT computation proves too complex or too many API calls, use Open-Meteo's `et0_fao_evapotranspiration` or simply `precipitation_sum` on the wider Atlantic grid as a moisture proxy. The visual story just needs to show "moisture streaming from southwest to northeast toward Iberia."

---

## Dataset 6: Precondition Index (Chapters 5, 7 — Computed)

**Source:** Computed from Datasets 2, 3, 4
**No API calls needed — pure computation.**

```python
# Load the soil moisture and precipitation data
sm = pd.read_parquet("data/temporal/moisture/soil_moisture.parquet")
precip = pd.read_parquet("data/temporal/precipitation/precipitation.parquet")

# Merge on date + lat + lon
df = sm.merge(precip, on=["date", "lat", "lon"], how="inner")

# Porosity constant (sandy loam typical for Portuguese basins)
POROSITY = 0.42  # m³/m³
ROOT_DEPTH_MM = 1000  # 1m root zone in mm

# Compute remaining capacity
df["remaining_capacity_mm"] = (POROSITY - df["sm_rootzone"]) * ROOT_DEPTH_MM
df["remaining_capacity_mm"] = df["remaining_capacity_mm"].clip(lower=1.0)  # avoid div/0

# Three-component index (from validated notebook v2):
# 1. Forward-looking: forecast precip / remaining capacity
# 2. Antecedent: 7-day accumulated precip (already computed)  
# 3. Discharge anomaly: from river data (join by nearest basin)

# Component 1: Saturation ratio using 3-day precip as proxy for "incoming"
df["ratio_3d"] = df["precip_3d"] / df["remaining_capacity_mm"]

# Component 2: Antecedent wetness (normalized 14-day precip)
precip_14d_p90 = df["precip_14d"].quantile(0.90)
df["antecedent_score"] = (df["precip_14d"] / precip_14d_p90).clip(upper=1.0)

# Combined score (simplified — discharge component requires spatial join to basin)
df["precondition_index"] = 0.6 * df["ratio_3d"] + 0.4 * df["antecedent_score"]

# Classification
def classify(score):
    if score < 0.3: return "green"
    elif score < 0.6: return "yellow"
    elif score < 0.9: return "orange"
    else: return "red"

df["risk_class"] = df["precondition_index"].apply(classify)

outpath = Path("data/temporal/precondition/precondition.parquet")
outpath.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(outpath)
print(f"Saved: {outpath}")
print(f"\nRisk class distribution (all dates, all points):")
print(df["risk_class"].value_counts(normalize=True).round(3))
print(f"\nPeak precondition days (>50% of grid in orange/red):")
daily_risk = df.groupby("date")["risk_class"].apply(
    lambda x: (x.isin(["orange", "red"])).mean()
).reset_index(name="frac_high_risk")
peak_days = daily_risk[daily_risk["frac_high_risk"] > 0.5].sort_values("frac_high_risk", ascending=False)
print(peak_days.head(10))
```

---

## Execution Strategy

The datasets have different sizes and speeds. Run in this order:

1. **Discharge** (Dataset 4) — 11 API calls, 1 minute. Run first for instant validation.
2. **SST** (Dataset 1) — 77 HTTP requests, ~5 minutes. Parallelizable but be polite to NOAA.
3. **Soil moisture + Precipitation** (Datasets 2+3 combined) — ~345 API calls, ~10-15 minutes.
4. **Precondition index** (Dataset 6) — pure computation, 30 seconds. Run after 2+3 complete.
5. **IVT** (Dataset 5) — ~6,000 API calls, 30-45 minutes. Run last, lowest priority.

**Total estimated time: ~60 minutes of API fetching (mostly IVT).**

If IVT takes too long or hits rate limits, it's the least critical for v0 — the precipitation grid on the wider view already shows the moisture pattern for Chapter 2, and IVT can be added later from ERA5 CDS download.

## Validation

After all datasets are generated, run this sanity check:

```python
import pandas as pd
from pathlib import Path

datasets = {
    "Soil moisture": "data/temporal/moisture/soil_moisture.parquet",
    "Precipitation": "data/temporal/precipitation/precipitation.parquet",
    "Discharge": "data/temporal/discharge/discharge.parquet",
    "Precondition": "data/temporal/precondition/precondition.parquet",
}

for name, path in datasets.items():
    df = pd.read_parquet(path)
    print(f"\n{name}: {len(df)} records")
    print(f"  Dates: {df['date'].min()} → {df['date'].max()} ({df['date'].nunique()} days)")
    if 'lat' in df.columns:
        print(f"  Grid points: {df.groupby(['lat','lon']).ngroups}")
    if 'basin' in df.columns:
        print(f"  Basins: {df['basin'].unique().tolist()}")

# Check SST
import xarray as xr
sst = xr.open_dataset("data/temporal/sst/sst_anomaly.nc")
print(f"\nSST: {sst.dims}")
print(f"  Time: {sst.time.values[0]} → {sst.time.values[-1]}")

# Key validation: does the precondition index peak during the storm periods?
pc = pd.read_parquet("data/temporal/precondition/precondition.parquet")
print("\n--- VALIDATION: Precondition index should peak during storms ---")
storm_dates = {
    "Kristin": ("2026-01-27", "2026-01-30"),
    "Leonardo": ("2026-02-03", "2026-02-07"),
    "Marta": ("2026-02-08", "2026-02-10"),
}
for storm, (start, end) in storm_dates.items():
    mask = (pc["date"] >= start) & (pc["date"] <= end)
    frac_red = (pc.loc[mask, "risk_class"].isin(["orange", "red"])).mean()
    print(f"  {storm}: {frac_red:.0%} of grid in orange/red")
```

If the precondition index doesn't light up during storm periods, the thresholds or formula need recalibration — but do NOT adjust until you've inspected the raw soil moisture and precipitation values first.

## README

Generate `data/temporal/README.md` documenting all datasets, their sources, processing, and the validation results.
