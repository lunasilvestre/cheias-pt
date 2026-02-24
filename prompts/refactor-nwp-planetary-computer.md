# cheias.pt — Refactor NWP Pipeline to Planetary Computer STAC

## Mission

Replace the multi-source NWP acquisition pipeline with a single STAC-based pipeline using Microsoft Planetary Computer's Met Office Global Deterministic 10km dataset. This simplifies 4 fetch scripts into 1, eliminates auth requirements, and demonstrates cloud-native geospatial patterns aligned with Development Seed's stack.

Read `CLAUDE.md` and `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/17-planetary-computer-nwp.md` first.

## Context

The NWP agent sprint produced 4 separate fetch scripts (`fetch_era5_synoptic.py`, `fetch_ecmwf_opendata.py`, `fetch_icon_eu.py`, `fetch_arpege.py`) and 1,717 COGs across ERA5 + ECMWF HRES sources. This works but is architecturally messy — 4 different APIs, 2 auth mechanisms, mixed GRIB2/NetCDF formats.

Planetary Computer hosts the **Met Office Unified Model Global 10km** with:
- All needed near-surface variables (MSLP, 10m wind u/v, gusts, precip, temp)
- 2-year rolling archive (Jan 2026 data is available)
- STAC catalog (standard discovery)
- NetCDF on AWS S3 (no auth, no API keys)
- 0.09° resolution (~10km, comparable to ECMWF HRES 0.1°)
- Pressure-level collection available for jet stream (250 hPa) visualization

**Reference:** https://planetarycomputer.microsoft.com/dataset/met-office-global-deterministic-near-surface

## What to Build

### 1. `scripts/fetch_metoffice_stac.py` — Primary NWP pipeline

Using `pystac-client` and `planetary-computer` packages:

```
pip install pystac-client planetary-computer xarray netcdf4 rioxarray
```

The script should:

1. **Discover** items via STAC for the date range Dec 1, 2025 – Feb 15, 2026
2. **Download** near-surface NetCDF files for the Atlantic+Iberia domain (36°N–60°N, 60°W–5°E)
3. **Extract variables:** `mean_sea_level_pressure`, `wind_speed_of_gust`, `x_wind` (10m U), `y_wind` (10m V), `stratiform_rainfall_rate` or equivalent precipitation field
4. **Process** each timestep: subset to domain → reproject to EPSG:4326 if needed → export as COG with LZW compression
5. **Output** to the same directory structure the existing pipeline uses:
   ```
   data/cog/mslp-mo/          # YYYY-MM-DDTHH.tif
   data/cog/wind-u-mo/        # YYYY-MM-DDTHH.tif
   data/cog/wind-v-mo/        # YYYY-MM-DDTHH.tif
   data/cog/wind-gust-mo/     # YYYY-MM-DDTHH.tif
   ```
   Use `-mo` suffix to distinguish from existing ERA5 COGs (keep both for comparison).

6. **Log** statistics: min/max values per variable per timestep, total file count, domain verification

Start with a **single day test** (Jan 28, 2026 — Storm Kristin peak) before running the full range. Verify that MSLP shows ~960 hPa minimum (matching ERA5 results) and wind gusts show ~38 m/s over Portugal.

### 2. `scripts/fetch_metoffice_pressure.py` — Jet stream layer (optional, P2)

Query `met-office-global-deterministic-pressure` collection for 250 hPa wind fields. This enables the jet stream visualization from the WeatherWatcher video (Screenshot_20260219-220417.png).

### 3. Comparison notebook: `notebooks/07-nwp-comparison.ipynb`

Quick notebook comparing ERA5 vs Met Office for Storm Kristin peak (Jan 28):
- Side-by-side MSLP maps
- Wind gust maximum over Portugal
- Spatial difference maps
- Note: ERA5 is reanalysis (observed), Met Office is forecast — differences are expected and interesting

### 4. Update `CLAUDE.md` data inventory

Add the new Met Office COG directories to the data pipeline section. Note that both ERA5 and Met Office data exist, with ERA5 as reanalysis ground truth and Met Office as the STAC-native pipeline for monitoring mode.

## Important Notes

- **Keep existing ERA5 COGs** — don't delete. They're validated and the scrollytelling may already reference them.
- The QGIS symbology prototyping session is running in parallel — the QML styles being built for ERA5 data will work identically on Met Office COGs (same variables, same units, same domain).
- Variable names in Met Office NetCDF may differ from ERA5 GRIB2. Map them explicitly in the script.
- The Met Office model runs 4x daily (00Z, 06Z, 12Z, 18Z). For the scrollytelling archive, fetch the 00Z run analysis timestep (T+0) for each day — this gives the closest-to-observation snapshot.
- For the storm period (Jan 26-30), fetch all available timesteps (hourly forecast steps from nearby runs) to enable animation.

## Dependencies

```
pystac-client
planetary-computer
xarray
netcdf4
rioxarray
rio-cogeo
```

All should install cleanly in the existing `.venv/`.

## Success Criteria

- `scripts/fetch_metoffice_stac.py` runs end-to-end, producing COGs for the full date range
- Jan 28 MSLP minimum is within 5 hPa of ERA5 result (~960 hPa)
- Jan 28 wind gust maximum over Portugal is within 5 m/s of ERA5 (~38 m/s)
- Script is clean enough to serve as a portfolio code sample
- Total runtime < 30 minutes for full date range
