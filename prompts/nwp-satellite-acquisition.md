# cheias.pt — NWP & Satellite Data Acquisition

## Mission

Acquire the missing meteorological data sources needed to replicate Weather Watcher–style synoptic visualizations for the cheias.pt scrollytelling. The scrollytelling covers **Dec 1, 2025 – Feb 15, 2026** (77 days). Storm Kristin peaked **Jan 28, 2026**. All data must be converted to Cloud-Optimized GeoTIFF (COG) following the existing pipeline pattern in `scripts/`.

Read `CLAUDE.md` first. The existing data pipeline uses: raw source → processing → COG in `data/cog/{variable}/YYYY-MM-DD.tif`. Follow this convention exactly.

## What Already Exists (DO NOT re-fetch)

- Soil moisture (ERA5-Land via Open-Meteo): `data/cog/soil-moisture/` — 86 COGs
- Precipitation (Open-Meteo archive): `data/cog/precipitation/` — 89 COGs
- SST anomaly (NOAA OISST): `data/cog/sst/` — 67 COGs
- IVT moisture flux: `data/cog/ivt/` — 77 COGs
- Precondition index: `data/cog/precondition/` — 77 COGs
- GloFAS discharge: `data/temporal/discharge/` — parquet
- CEMS flood extent: `data/flood-extent/` — PMTiles + GeoJSON
- IPMA warnings: `data/qgis/ipma-warnings-timeline.geojson`

## What's Missing (this is what you build)

### P0 — ECMWF / ERA5 Synoptic Fields

We need MSLP, wind, and pressure fields for synoptic chart views (isobars, wind barbs, wind streamlines). Two acquisition paths — try both, pick whichever yields data faster:

**Path A: ERA5 via CDS API** (preferred for archival completeness)
- Register at https://cds.climate.copernicus.eu (check if `~/.cdsapirc` already exists)
- Dataset: `reanalysis-era5-single-levels`
- Variables needed:
  - `mean_sea_level_pressure` — for isobar contours
  - `10m_u_component_of_wind` + `10m_v_component_of_wind` — for wind barbs and streamlines
  - `instantaneous_10m_wind_gust` — for sting jet visualization (peak gusts)
  - `total_precipitation` — instantaneous precip rate (complements Open-Meteo daily totals)
- Domain: `36°N–60°N, 60°W–5°E` (North Atlantic + Iberia, matching SST extent)
- Temporal: Hourly for Jan 26-30 2026 (storm period), 6-hourly for rest of Dec 2025-Feb 2026
- Output format: GRIB2 or NetCDF
- Processing: Extract each timestep → reproject to EPSG:4326 → COG with LZW compression

**Path B: ECMWF Open Data** (check if HRES archive still has Jan 2026 data)
- URL: https://data.ecmwf.int/forecasts/
- No auth needed, CC BY 4.0
- HRES 0.1° — higher resolution than ERA5 0.25°
- Check availability first. If Jan 28 forecasts exist, download the runs initialized Jan 26 12Z and Jan 27 00Z (the forecasts WXCharts was showing)

**Output directories:**
```
data/cog/mslp/          # YYYY-MM-DDTHH.tif (Pa, not hPa — divide by 100 for display)
data/cog/wind-u/         # YYYY-MM-DDTHH.tif (m/s)
data/cog/wind-v/         # YYYY-MM-DDTHH.tif (m/s)
data/cog/wind-gust/      # YYYY-MM-DDTHH.tif (m/s)
```

**Script:** `scripts/fetch_era5_synoptic.py`

### P1 — DWD ICON-EU Wind Gusts

ICON-EU at 0.0625° (~6.5 km) has the best resolution for sting jet wind gust visualization. The WXCharts screenshot shows `10m Peak Wind Gust Past 6h`.

- Source: `https://opendata.dwd.de/weather/nwp/icon-eu/grib/`
- **First: check if historical data for Jan 26-30 is still available.** DWD purges after ~2 weeks, so it's probably gone. If gone:
  1. Document the pipeline for future real-time ingestion
  2. Check DWD Climate Data Center (CDC) for reanalysis alternatives: `https://opendata.dwd.de/climate_environment/`
  3. If neither available, ERA5 wind gusts at 0.25° are the fallback
- Variable: `VMAX_10M` (10m peak gust, km/h)
- Processing: decompress `.grib2.bz2` → extract Portugal+Atlantic domain → COG

**Output:** `data/cog/wind-gust-icon/` (if available) or document pipeline in `scripts/fetch_icon_eu.py`

### P1 — Météo-France ARPEGE

Similar to ICON-EU — operational archives may have expired.

- Source: `https://donneespubliques.meteofrance.fr/`
- Check if Jan 2026 GRIB2 files still available
- Variables: MSLP + 10m wind (for Beaufort barb overlay comparison)
- If expired: document pipeline, fall back to ERA5

**Output:** `data/cog/arpege/` or pipeline docs only

### P1 — EUMETSAT Meteosat Satellite Imagery

Satellite imagery for Storm Kristin's approach and landfall. The Data Store has full archives — no expiry.

- Register at https://data.eumetsat.int (check for existing credentials in `~/.eumetsat/` or env vars)
- Products needed:
  - MSG Natural Colour RGB composite — Jan 27-28, 2026, every 15 min (or hourly at minimum)
  - MSG IR 10.8μm channel — same timestamps (for nighttime storm tracking)
- Processing: The tricky part is **geostationary projection** → EPSG:4326. Use `rioxarray` or `satpy` for reprojection. Crop to North Atlantic domain.
- Each frame → COG

**Output:** `data/cog/satellite-vis/` and `data/cog/satellite-ir/`
**Script:** `scripts/fetch_eumetsat.py`

### P1 — Blitzortung Lightning

Point data showing convective activity during Storm Kristin.

- Historical data options:
  1. Blitzortung Data Access Program — requires membership application
  2. LightningMaps.org archive — check if historical CSV/JSON available
  3. EUCLID via EUMETNET — professional, may require institutional access
- If direct data unavailable: check if Windy's API exposes historical lightning data
- Minimum viable: Jan 27-28 2026 lightning strikes over Iberian Peninsula
- Format: GeoJSON points with `timestamp`, `latitude`, `longitude`, `amplitude`

**Output:** `data/qgis/lightning-kristin.geojson` + `data/lightning/lightning-kristin.pmtiles`
**Script:** `scripts/fetch_lightning.py`

### P0 — IPMA Radar (hardest, most uncertain)

No public API. No historical archive. Options in priority order:

1. **OPERA/EUMETNET radar composites** — check if public access exists for historical European radar data. URL: https://www.eumetnet.eu/activities/observations-programme/current-activities/opera/
2. **RainViewer API** — commercial but has historical coverage. Check `https://www.rainviewer.com/api.html` for archived radar tiles for Jan 28
3. **Scrape IPMA current radar** for future real-time use — document the scraping pipeline + georeferencing approach (Portugal mainland bbox: ~36.9°N-42.2°N, 9.6°W-6.1°W)
4. **If none work:** Document the gap. This layer may need a partnership approach.

**Output:** Whatever can be obtained → `data/radar/` with georeferenced COGs or tiles

## Spawn Plan

Spawn 7 teammates (one per independent data source — maximum parallelism). All use **Opus**.

- **Teammate 1 — ERA5 CDS API:** Path A — acquire MSLP, 10m wind (u+v), wind gusts, and precip rate via the CDS API (`reanalysis-era5-single-levels`). Check `~/.cdsapirc` for credentials. Start with a single-day test request (Jan 28) to verify the pipeline before fetching the full 77-day range. Hourly for Jan 26-30, 6-hourly for the rest. Process GRIB2/NetCDF → EPSG:4326 COG. Use the virtual environment at `.venv/`.

- **Teammate 2 — ECMWF Open Data:** Path B — check `https://data.ecmwf.int/forecasts/` for archived HRES 0.1° data from Jan 2026. If available, download the runs initialized Jan 26 12Z and Jan 27 00Z (the forecasts WXCharts was showing). HRES is higher resolution than ERA5 — if it works, it supplements Teammate 1's output. If expired, document the pipeline for future real-time ingestion and report back immediately. Use `.venv/`.

- **Teammate 3 — DWD ICON-EU:** Investigate DWD open data archive for ICON-EU `VMAX_10M` (10m peak gust) from Jan 26-30. DWD purges after ~2 weeks so likely gone. Check DWD Climate Data Center (CDC) for reanalysis alternatives at `https://opendata.dwd.de/climate_environment/`. Write `scripts/fetch_icon_eu.py` either way — it's needed for monitoring mode. ERA5 gusts from Teammate 1 are the fallback. Use `.venv/`.

- **Teammate 4 — Météo-France ARPEGE:** Check `https://donneespubliques.meteofrance.fr/` for archived Jan 2026 GRIB2 files (MSLP + 10m wind). If expired, document the pipeline and write `scripts/fetch_arpege.py` for future use. Report availability status quickly — if dead end, wrap up and let the lead know. Use `.venv/`.

- **Teammate 5 — EUMETSAT Meteosat:** Acquire MSG Natural Colour RGB and IR 10.8μm from the EUMETSAT Data Store for Jan 27-28 (storm approach + landfall). Check for credentials in `~/.eumetsat/` or env vars. The geostationary → EPSG:4326 reprojection is the hardest challenge — use `satpy` if installed, otherwise `rioxarray`. Crop to North Atlantic domain. Each frame → COG. Use `.venv/`.

- **Teammate 6 — Blitzortung Lightning:** Investigate all lightning data paths for Jan 27-28 over Iberia: (1) Blitzortung Data Access Program, (2) LightningMaps.org archive, (3) EUCLID via EUMETNET, (4) Windy API historical data. Output GeoJSON points with `timestamp`, `lat`, `lon`, `amplitude`. Convert to PMTiles if data obtained. Use `.venv/`.

- **Teammate 7 — Radar (OPERA/RainViewer/IPMA):** Investigate all radar data access paths in priority order: (1) OPERA/EUMETNET historical composites, (2) RainViewer API archived tiles for Jan 28, (3) IPMA current radar scraping pipeline for future use. This is the most uncertain — expect dead ends. Document what works and what doesn't. Use `.venv/`.

**Coordination:**

- Teammate 2 should report ECMWF Open Data availability quickly — if available, it supplements Teammate 1's ERA5 output.
- Teammate 3 depends on Teammate 1's ERA5 wind gust results as fallback — if ICON-EU is unavailable, ERA5 gusts are the replacement.
- The lead should produce:
  1. A status report: what was acquired, what's missing, what's the fallback
  2. All fetch scripts in `scripts/`
  3. All COGs in `data/cog/` following naming conventions
  4. An updated data inventory section for `CLAUDE.md`

**File ownership (no conflicts — each teammate owns their directories):**
- Teammate 1: `data/cog/mslp/`, `data/cog/wind-u/`, `data/cog/wind-v/`, `data/cog/wind-gust/`, `scripts/fetch_era5_synoptic.py`
- Teammate 2: `data/cog/ecmwf-hres/`, `scripts/fetch_ecmwf_opendata.py`
- Teammate 3: `data/cog/wind-gust-icon/`, `scripts/fetch_icon_eu.py`
- Teammate 4: `data/cog/arpege/`, `scripts/fetch_arpege.py`
- Teammate 5: `data/cog/satellite-vis/`, `data/cog/satellite-ir/`, `scripts/fetch_eumetsat.py`
- Teammate 6: `data/lightning/`, `data/qgis/lightning-kristin.geojson`, `scripts/fetch_lightning.py`
- Teammate 7: `data/radar/`, `scripts/fetch_radar.py`
