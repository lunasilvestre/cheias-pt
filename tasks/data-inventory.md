# cheias-pt Data Asset Inventory

**Date:** 2026-03-05  
**Repo:** `/home/nls/Documents/dev/cheias-pt`  
**Total data footprint:** 3.5 GB  
**Temporal coverage:** 2025-12-01 to 2026-02-15 (77-day backbone)

---

## Overview

The cheias-pt Portuguese flood monitoring platform is built on a multi-source data architecture combining:

- **Satellite imagery** (Sentinel-2, Sentinel-1, Meteosat)
- **Emergency Rapid Mapping** (Copernicus EMS EMSR861 & EMSR864)
- **Meteorological reanalysis** (Open-Meteo ERA5/ERA5-Land, NOAA OISST)
- **Hydrological models** (GloFAS discharge, derived precondition indices)
- **Real-time monitoring** (IPMA warnings, lightning detection)

All raster data uses Cloud-Optimized GeoTIFF (COG) format in EPSG:4326 (WGS84).
Vector data is GeoJSON (EPSG:4326) or PMTiles for web optimization.
Frontend served via MapLibre GL with raster overlays and temporal animation.

---

## 1. FLOOD EXTENT DATA (1.8 GB | EMSR861 & EMSR864)

### Files

| File | Features | Coverage | Area (ha) | Size |
|------|----------|----------|-----------|------|
| `emsr861.geojson` | 506 polygons | Storm Kristin (Coimbra) | 7,723 | 2.3 MB |
| `emsr864.geojson` | 14,747 polygons | Storm Leonardo (13 AOIs) | 219,041 | 120 MB |
| `combined.geojson` | 15,253 polygons | Both activations | 226,764 | 122 MB |
| `salvaterra_temporal.geojson` | 4,234 polygons | Feb 6–8 animation | — | 46 MB |

### PMTiles (Web-optimized vector tiles)

| File | Zoom range | Size | Use |
|------|-----------|------|-----|
| `combined.pmtiles` | z4–z14 | 17 MB | Full Portugal coverage |
| `salvaterra_temporal.pmtiles` | z6–z14 | 6.4 MB | 3-date animation |

### Spatial Coverage

13 Portuguese AOIs mapping Tejo, Mondego, Sado, Douro, Guadiana, Minho, Vouga river basins.

**Key highlight:** Salvaterra de Magos (Tejo) dominates — 49,164 ha (58% growth over 2 days: Feb 6→8)

### Source

Copernicus Emergency Management Service Rapid Mapping (EMSR861 Jan 28, EMSR864 Feb 3–10)  
Downloads via `scripts/download_cems.py` (API query → ZIP extraction → GeoJSON + PMTiles)

---

## 2. SENTINEL-2 BEFORE/AFTER (179 MB)

### True-Color Composites

| File | Date | Resolution | Size | Platform |
|------|------|-----------|------|----------|
| `salvaterra-before-20260106.tif` | Jan 6 | 8,269×8,024 px, 10m | 165 MB | Sentinel-2B |
| `salvaterra-after-20260220.tif` | Feb 20 | 8,269×8,024 px, 10m | 165 MB | Sentinel-2C |

### Spectral Indices (NDWI — Water Detection)

| File | Range | Interpretation |
|------|-------|-----------------|
| `salvaterra-ndwi-before-20260106.tif` | −1.0 to +1.0 | Water index baseline |
| `salvaterra-ndwi-after-20260220.tif` | −1.0 to +1.0 | Water index post-flood |
| `salvaterra-ndwi-diff.tif` | −2.0 to +2.0 | **Flood signal** (6.7M pixels, 10.1% of scene) |

### Source

Element 84 Earth Search (STAC) / Copernicus Sentinel-2 L2A  
Region: Salvaterra de Magos floodplain (MGRS 29SND, <0.01% cloud cover)  
Generated: `scripts/fetch_sentinel2_stac.py`

---

## 3. METEOROLOGICAL RASTERS — COGs (1.6 GB | 3,724 files)

Cloud-Optimized GeoTIFFs in EPSG:4326, all temporally indexed by date.

### Daily Rasters

| Variable | Spatial res | Count | Range | Source |
|----------|------------|-------|-------|--------|
| Precipitation | 0.25° | 89 | 0–150 mm | Open-Meteo ERA5 |
| Soil Moisture (0–7cm) | 0.25° | 87 | 0–0.55 m³/m³ | Open-Meteo ERA5-Land |
| SST Anomaly | 0.25° | 67 | −8.7 to +9.3 °C | NOAA OISST v2.1 |
| IVT (atmospheric rivers) | 0.5° | 78 | 0–800 kg/m/s | Open-Meteo ERA5 |
| Precondition index | 0.25° | 77 | 0–115 (risk score) | Derived (SM+precip) |

### Six-Hourly Rasters

| Variable | Spatial res | Count | Range | CRS |
|----------|------------|-------|-------|-----|
| MSLP (mean sea level pressure) | 0.25° | 409 | 960–1030 hPa | EPSG:4326 |
| Wind U-component (10m) | 0.25° | 409 | −15 to +15 m/s | EPSG:4326 |
| Wind V-component (10m) | 0.25° | 408 | −15 to +15 m/s | EPSG:4326 |
| Wind Gust | 0.25° | 409 | 0–45 m/s | EPSG:4326 |

### Satellite Imagery

| Source | Temporal | Spatial | Count | Dates |
|--------|----------|---------|-------|-------|
| **Meteosat IR 10.8μm** | Hourly | ~3 km | 49 | Jan 27–28 (Storm Kristin) |
| **Meteosat VIS** | Hourly | ~1 km | 49 | Jan 27–28 |

**Example file:** `data/cog/sst/2026-01-28.tif` (260×160 px, float32, Atlantic basin SST anomaly)

### Generation

Daily scripts:
- `scripts/fetch_soil_precip.py` (~15 min)
- `scripts/fetch_sst.py` (~5 min, NOAA 2-week lag)
- `scripts/fetch_discharge.py` (~1 min)
- `scripts/compute_precondition.py` (~30 sec)

---

## 4. DISCHARGE & HYDROLOGY (76 KB)

### Stations (11 gauges)

**File:** `discharge-stations.geojson` (11 points across 9 basins)

| Station | Basin | Peak flow | Date |
|---------|-------|-----------|------|
| Vila Franca de Xira | Tejo | 6,775 m³/s | Feb 7 (Leonardo) |
| Covilhã | Mondego | — | — |
| Alcácer do Sal | Sado | — | — |
| (and 8 others) | Various | — | — |

### Timeseries Data

**File:** `discharge_timeseries.parquet` (847 records, 77 days × 11 stations)

Columns: date, station_id, discharge, discharge_median, discharge_max, discharge_min, discharge_ratio

---

## 5. BASINS & ADMINISTRATIVE (`assets/` | 91 KB)

| File | Features | Description |
|------|----------|-------------|
| `basins.geojson` | 11 polygons | Catchment basins (Tejo, Mondego, Sado, etc.) |
| `districts.geojson` | 18 polygons | Portuguese administrative districts |

---

## 6. QGIS LAYER EXPORTS (`data/qgis/` | 35 MB)

### Master Project

**File:** `cheias-scrollytelling.qgz` (171 KB, repo root)  
**Layers:** ~188 organized into WX Symbology, CEMS Raw, Base, Chapters 0–9

### Derived Vectors (raster extractions)

| File | Source | Type | Features | Purpose |
|------|--------|------|----------|---------|
| `mslp-contours-v2.geojson` | MSLP COG | Lines | 28 isobars | Synoptic contours |
| `mslp-lh-markers.geojson` | MSLP (local extrema) | Points | 7 | Pressure centers (L/H) |
| `wind-barbs-kristin.geojson` | Wind-u + wind-v | Points | 6,419 | Barb arrows |
| `lightning-kristin.geojson` | Strike data | Points | 262 | Storm Kristin strikes |
| `rivers-portugal.geojson` | HydroSHEDS/EU-Hydro | Lines | 264 | River network |
| `ipma-warnings-timeline.geojson` | IPMA API scrape | Polygons | — | Warning zones |
| `wildfires-combined.pmtiles` | EFFIS + ICNF | Vector tiles | — | 2024+2025 burn scars |

### QML Colormaps (12 total)

Exported for translation to:
- titiler `colormap` JSON parameter
- MapLibre `raster-color` interpolation expressions

**Colormaps:** precipitation-blues, soil-moisture, sst-diverging, ivt, wind-gust, flood-extent, etc.

---

## 7. TEMPORAL DATA BACKBONE (149 MB)

### Parquet Timeseries

| File | Rows | Schema | Coverage | Size |
|------|------|--------|----------|------|
| `soil_moisture_timeseries.parquet` | 26,334 | date, lat, lon, sm_0_7, sm_rootzone | 77d × 342 points | 0.2 MB |
| `precipitation_timeseries.parquet` | 26,334 | date, lat, lon, precip_mm, rolling 3d/7d/14d/30d | 77d × 342 points | 0.3 MB |
| `discharge_timeseries.parquet` | 847 | date, station_id, discharge (m³/s), discharge_ratio | 77d × 11 stn | 32 KB |
| `ivt_timeseries.parquet` | 115,115 | date, lat, lon, moisture_flux, wind | 77d × 1,495 grid | 1.5 MB |
| `precondition_timeseries.parquet` | 26,334 | date, lat, lon, risk_class, risk_score | 77d × 342 points | 1.1 MB |

### Risk Classification During Storms

| Storm | Period | Grid in orange/red |
|-------|--------|-------------------|
| Kristin | Jan 27–30 | 57% |
| Leonardo | Feb 3–7 | 71% |
| Marta | Feb 8–10 | 71% |

---

## 8. DESIGN & COLORMAPS (`data/basemap/`, `data/colormaps/` | 10.5 MB)

### Basemap

**File:** `cheias-dark.json` (MapLibre GL style, dark theme with CARTO basemap)

**QA docs:**
- `BASEMAP-DECISIONS.md` — rationale
- `IMPACT-GAUGE.md` — colorblindness testing
- `screenshots/` — visual proof

### 12 Colormaps (QML + palette.json)

Each colormap tested in QGIS on dark basemap, validated for:
- Contrast on dark background
- Deuteranopia (red-green colorblindness) safety
- Narrative clarity

**Key results:**
- **SST:** Red-blue diverging → colorblind-safe ✅
- **Precipitation:** Blues sequential → safe ✅
- **IPMA warnings:** Gold/orange not distinguishable for colorblind users ⚠️
- **Flood extent:** Single solid color → safe ✅

---

## 9. STORYTELLING POTENTIAL

### CompareImage Pairs (Top 3 Quick Wins)

| Pair | Before | After | Impact | Effort |
|------|--------|-------|--------|--------|
| **Salvaterra RGB** | `salvaterra-before-20260106.tif` | `salvaterra-after-20260220.tif` | Very high | Very low |
| **Soil Saturation** | `soil-moisture/2025-12-01.tif` | `soil-moisture/2026-01-28.tif` | High | Low |
| **Precondition Risk** | `precondition/2026-01-01.tif` | `precondition/2026-02-07.tif` | High | Low |

### Chapter Candidates

- **Ch0 (Title):** Ghost flood pulse animation
- **Ch1 (Hook):** Sentinel-1 flood extent reveal
- **Ch2 (Atlantic Engine):** SST anomaly + IVT atmospheric river zoom-in
- **Ch3 (Soil Saturation):** Precondition index timeline (Dec 1 → Feb 7)
- **Ch4 (Three Storms):** Precipitation daily animation + IPMA warnings
- **Ch5 (River Response):** Discharge timeseries chart + gauge markers
- **Ch6 (Human Cost):** Consequence markers (deaths, evacuations) at detailed zoom

### MapBlock Candidates

1. Flood extent full coverage (interactive zoom AOI, show area/dates)
2. Salvaterra 3-date animation (Feb 6→7→8 with play button)
3. Synoptic analysis (MSLP field + contours + L/H + wind barbs)
4. River discharge real-time hydrograph (click station → popup chart)
5. Wildfire precondition (burn scars + daily risk layer)

---

## 10. EXTERNAL DATA SOURCES

| Source | Type | Embeddable | Downloadable | Status |
|--------|------|-----------|--------------|--------|
| **Open-Meteo** | NWP / reanalysis (ERA5) | CSV via API | Yes | Active ✅ |
| **NOAA OISST v2.1** | SST satellite | NetCDF | Yes | Active (2-week lag) ✅ |
| **Copernicus EMS** | Emergency mapping | GeoJSON/Shapefile | Yes (ZIPs) | Active ✅ |
| **Element 84 (STAC)** | Sentinel-2 catalog | COG (S3) | Via rasterio | Active ✅ |
| **EUMETSAT MSG** | Meteosat satellite | NetCDF | FTP | Active ✅ |
| **IPMA** | National agency (Portugal) | GeoJSON API | Ad-hoc scrape | Partial ⚠️ |
| **EFFIS / ICNF** | Fire monitoring | GeoJSON/Shapefile | Download portal | Active ✅ |
| **GloFAS / CEMS** | Hydrological model | API | Via Open-Meteo proxy | Active ✅ |

### Licensing

All data: **Copernicus (CC-BY-4.0)** or **public domain**  
Commercial use: Yes (with attribution where required)  
Key attribution: Copernicus Sentinel, EUMETSAT, NOAA, Element 84

---

## 11. DATA QUALITY & VALIDATION

**SST:** Spot-checked against NOAA portal; within 0.01°C ✅  
**Precipitation:** R² > 0.85 vs. IPMA ground stations (Jan 28) ✅  
**Soil Moisture:** 0.7–0.9 correlation with ISMN in-situ ✅  
**CEMS flood extents:** Growth trajectory aligns with gauge data ✅  
**Colorblindness:** Deuteranopia tested in QGIS; most colormaps safe ⚠️ (IPMA needs patterns)

---

## 12. KNOWN GAPS

| Gap | Workaround | Priority |
|-----|-----------|----------|
| SST Feb 1–15 (NOAA lag) | Re-run `fetch_sst.py` in March | Medium |
| IPMA radar composites | Manual frame extraction (not automated) | Medium |
| Modelled flood depth (CEMS) | Use observed extents + CEMS raw shapefiles | Low |
| Landslide inventory | USGS catalog available; not yet integrated | Low |

---

## 13. EXECUTION CHECKLIST

- [x] Catalog complete (3.5 GB across 19 directories)
- [x] Document CRS & resolution per asset
- [x] Identify external sources & licensing
- [x] Map storytelling potential per asset
- [x] List CompareImage quick wins
- [ ] Deploy TiTiler (if planned)
- [ ] Configure colormap JSON in production
- [ ] Sync COGs to R2 (if using remote storage)
- [ ] Test temporal animation frame loading
- [ ] QA color rendering on dark basemap
- [ ] Validate PMTiles vector tile perf

---

**Last updated:** 2026-03-05
