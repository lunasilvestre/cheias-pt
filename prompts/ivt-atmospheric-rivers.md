
# PROMPT: Atmospheric River / IVT Daily Data — Cascade Acquisition

## Context

cheias.pt Chapter 2 ("The Atlantic Engine") needs to show three atmospheric rivers
hitting Portugal in sequence: Kristin (Jan 28-30), Leonardo (Feb 3-7), Marta (Feb 9-11).
The current IVT data is **physically meaningless** — a surface-level proxy that maxes at
63 instead of the 250+ kg/m/s threshold that defines an atmospheric river.

We need real IVT (Integrated Vapour Transport) data at daily granularity across the
North Atlantic, covering 2025-12-01 to 2026-02-15 (77 days).

## Current (broken) State

- `data/temporal/ivt/ivt.parquet` — 115,115 rows, 77 days × 1,495 points, but values are
  a surface moisture flux proxy (max 63), NOT real IVT
- `data/qgis/ivt-peak-storm.geojson` — 1,102 points, single date (Feb 10), max 47.9
- `data/cog/ivt/ivt-peak-2026-02-10.tif` — single COG on R2, same bad data
- All of this should be **replaced** with real IVT data

## Infrastructure

- **R2 bucket:** `cheias-cog` via rclone remote `r2:`
  - Upload: `rclone sync <local> r2:cheias-cog/cog/ivt/ --progress`
  - Public: `https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/ivt/{date}.tif`
- **Titiler:** `https://titiler.cheias.pt`
- **rclone** configured and working
- **Python venv:** `.venv/bin/python3` has xarray, rioxarray, rasterio, numpy, scipy, requests, geopandas
- **System python** has most libs EXCEPT pyarrow (use venv for parquet)
- **tippecanoe** installed (for PMTiles generation)
- **Project root:** `/home/nls/Documents/dev/cheias-pt`
- **No CDS API credentials** — `~/.cdsapirc` does not exist

## Acquisition Strategy: Try C → A → B

Execute in order. Stop as soon as one succeeds with sufficient data.

---

### Option C: Pre-computed AR Track Shapefiles (FASTEST)

Several institutions publish detected AR outlines/catalogs:

**Source 1: CW3E AR Detection (UCSD/Scripps)**
- Check: `https://cw3e.ucsd.edu/atmospheric-river-tracking/`
- They publish global AR shape catalogs from IVT fields
- Look for GeoJSON/Shapefile downloads of AR outlines for Jan-Feb 2026
- Also check their data portal for IVT fields

**Source 2: Atmospheric River Tracking Method Intercomparison (ARTMIP)**
- Catalog: `https://www.cgd.ucar.edu/projects/artmip/`
- May have standardized AR catalogs

**Source 3: NOAA Physical Sciences Laboratory**
- IVT composites and AR event pages
- Check `https://psl.noaa.gov/`

**Source 4: Copernicus Climate Data Store (CDS)**
- ERA5 single-level has `vertical_integral_of_eastward/northward_water_vapour_flux`
- BUT no credentials exist. Check if CDS has anonymous/open access endpoints

**Source 5: Direct IVT GeoTIFF archives**
- CIRA/RAMMB: `https://rammb-data.cira.colostate.edu/`
- Look for pre-computed IVT maps as GeoTIFF or NetCDF

**What to look for:**
- Daily IVT magnitude rasters (kg/m/s) covering North Atlantic (-60°W to 5°E, 20°N to 55°N)
- OR AR outline polygons/polylines with dates and IVT values
- Date range: at minimum Jan 25 – Feb 12, 2026; ideally Dec 1 – Feb 15

**If vector AR tracks found:** Generate PMTiles:
```bash
tippecanoe -o data/ar-tracks.pmtiles -Z2 -z10 --drop-densest-as-needed -l ar-tracks --force ar-tracks.geojson
```
Also save as `data/qgis/ar-tracks.geojson`.

**If raster IVT fields found:** Process to COGs and upload to R2 (see output format below).

**Evaluation criteria:** Option C succeeds if we get either:
(a) Daily IVT raster fields for ≥15 days covering the three storm periods, OR
(b) AR outline geometries with timestamps for ≥5 events in Jan-Feb 2026

---

### Option A: ERA5 IVT from CDS API

**Prerequisites:** Need CDS API credentials. 

1. Check if CDS allows anonymous API access for ERA5 single-level data
2. If not, check if there's a new CDS beta/open endpoint (CDS has been migrating)
3. If credentials are needed, print instructions for the user and STOP

**If access is possible:**

Request ERA5 single-level reanalysis:
- Variables: `vertical_integral_of_eastward_water_vapour_flux`, `vertical_integral_of_northward_water_vapour_flux`
- Area: 55°N, -60°W, 20°N, 5°E (N/W/S/E format for CDS)
- Dates: 2025-12-01 to 2026-02-15
- Time: 00:00, 06:00, 12:00, 18:00 (6-hourly, average to daily)
- Format: NetCDF

**Process:**
```python
import xarray as xr
import numpy as np

ds = xr.open_dataset('era5_ivt.nc')
# Compute IVT magnitude
ivt = np.sqrt(ds['p71.162']**2 + ds['p72.162']**2)  # or named variables
# Average to daily
ivt_daily = ivt.resample(time='1D').mean()
```

Then convert each daily slice to a COG (see output format below).

**Evaluation criteria:** Option A succeeds if we download and process IVT for ≥30 days.

---

### Option B: Open-Meteo Pressure-Level IVT Computation (SLOWEST, NO AUTH)

**This is the guaranteed fallback.** Open-Meteo has no auth and the data is there.

Compute proper column-integrated IVT from pressure-level data:

**API endpoint:** `https://archive-api.open-meteo.com/v1/archive`

**Variables needed at pressure levels (850, 700, 500, 300 hPa):**
```
pressure_level_850hPa: specific_humidity, u_component_of_wind, v_component_of_wind
pressure_level_700hPa: same
pressure_level_500hPa: same  
pressure_level_300hPa: same
```

**Check first** what pressure-level variables Open-Meteo actually exposes:
```bash
curl -s "https://archive-api.open-meteo.com/v1/archive?latitude=40&longitude=-10&start_date=2026-02-10&end_date=2026-02-10&hourly=specific_humidity_850hPa,u_component_of_wind_850hPa,v_component_of_wind_850hPa" | python3 -m json.tool | head -20
```

If specific_humidity is not available, use `relative_humidity` + `temperature` at each level to compute it:
```python
# Clausius-Clapeyron → saturation vapor pressure
es = 6.112 * exp(17.67 * T / (T + 243.5))  # T in °C
e = es * RH / 100
q = 0.622 * e / (p - 0.378 * e)  # specific humidity
```

**IVT computation:**
```python
# IVT = (1/g) * Σ(q * wind * dp) across pressure levels
# g = 9.81 m/s²
# dp = pressure difference between levels (in Pa)
levels = [850, 700, 500, 300]  # hPa
dp = [150, 150, 200, 200]  # hPa differences (approximate layer thickness)

ivt_east = 0
ivt_north = 0
for lev, dp_val in zip(levels, dp):
    ivt_east += q[lev] * u[lev] * (dp_val * 100) / 9.81
    ivt_north += q[lev] * v[lev] * (dp_val * 100) / 9.81
ivt_magnitude = sqrt(ivt_east**2 + ivt_north**2)
```

**Grid:** 1° resolution across the Atlantic box:
- Lats: 25°N to 53°N (29 points)
- Lons: -45°W to 4°E (50 points)  
- Total: 1,450 grid points
- At 0.2s per request = ~5 minutes

**Processing:**
1. Query each grid point for the full date range (Dec 1 – Feb 15)
2. Compute 6-hourly IVT, then daily mean IVT magnitude
3. Interpolate 1° grid to 0.25° for smooth rendering (scipy RBF or griddata)
4. Write each day as a COG

**Rate limiting:** Add 0.2s sleep between requests. Save intermediate parquet every 200 points.

---

## Output Format (applies to whichever option succeeds)

### If raster IVT data obtained:

**COGs** in `data/cog/ivt/`:
- Named: `YYYY-MM-DD.tif` (e.g., `2026-01-28.tif`)
- Format: Float32, LZW, tiled 256×256, with overviews
- EPSG:4326
- Units: kg/m/s (real IVT — atmospheric rivers show as 250-800+)
- NoData: -999

Upload ALL daily COGs to R2:
```bash
# First remove the old broken single file
rclone delete r2:cheias-cog/cog/ivt/ivt-peak-2026-02-10.tif
# Upload all new
rclone sync data/cog/ivt/ r2:cheias-cog/cog/ivt/ --progress
```

Verify via titiler (IVT uses `reds` colormap, rescale 0-500):
```bash
curl -s "https://titiler.cheias.pt/cog/info?url=https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/ivt/2026-02-10.tif"
```

### If vector AR tracks obtained:

**GeoJSON** at `data/qgis/ar-tracks.geojson`:
- Properties: `date`, `ivt_max` (peak IVT in the AR), `storm` (Kristin/Leonardo/Marta/none), `ar_id`
- Geometry: Polygon outlines of AR shapes, or LineString centerlines

**PMTiles** at `data/ar-tracks.pmtiles`:
```bash
tippecanoe -o data/ar-tracks.pmtiles -Z2 -z10 --drop-densest-as-needed -l ar-tracks --force data/qgis/ar-tracks.geojson
```

### Always generate (from whichever data source):

**IVT peak GeoJSON** (replace existing broken file):
`data/qgis/ivt-peak-storm.geojson` — grid points for the peak AR dates where IVT > 250:
```json
{
  "type": "Feature",
  "geometry": {"type": "Point", "coordinates": [-15.0, 42.0]},
  "properties": {"ivt": 350.2, "date": "2026-02-10", "storm": "Marta"}
}
```

**IVT temporal parquet** (replace existing broken file):
`data/temporal/ivt/ivt.parquet` — full daily grid with proper IVT values

## Verification Checklist

Print at the end:

```
=== IVT Data Acquisition Summary ===
Method used: [C/A/B]
Source: [description]
Date range: YYYY-MM-DD to YYYY-MM-DD (N days)
Grid: [resolution] across [extent]
IVT value range: X.X to X.X kg/m/s
Points > 250 (AR threshold): N across M days

Storm peaks detected:
  Kristin:  YYYY-MM-DD  max IVT = X.X at (lat, lon)
  Leonardo: YYYY-MM-DD  max IVT = X.X at (lat, lon)  
  Marta:    YYYY-MM-DD  max IVT = X.X at (lat, lon)

Files created:
  COGs on R2: N files at cog/ivt/
  GeoJSON: data/qgis/ivt-peak-storm.geojson (N features)
  PMTiles: data/ar-tracks.pmtiles (if vector data)
  Parquet: data/temporal/ivt/ivt.parquet (N rows)
  
Titiler verification:
  [date1]: ✓/✗ (min=X, max=X)
  [date2]: ✓/✗ (min=X, max=X)
  [date3]: ✓/✗ (min=X, max=X)
```

## Do NOT

- Keep the old broken IVT proxy data — overwrite `ivt.parquet` and `ivt-peak-storm.geojson`
- Skip the verification step
- Use the existing `scripts/fetch_ivt_proxy.py` — it produces bad data
- Touch SST data (separate task)
- Touch any other COG directories (soil-moisture, precipitation, precondition)
- Create frontend JSON or PNGs (we'll do that later)
