# cheias.pt Data Catalogue — Complete Inventory & Storytelling Assessment

**Date:** 2026-02-26
**Author:** Data Cartographer Agent
**Total data footprint:** 2.9 GB across 7,447 files
**Temporal backbone:** 2025-12-01 to 2026-02-15 (77 days)

---

## 1. Data Inventory Table

### 1A. Cloud Optimized GeoTIFFs (COGs) — 722 MB

The core raster archive. All COGs are EPSG:4326, synced to Cloudflare R2, and served via titiler.

| Dataset | Path | Format | Size | Count | Variable | Temporal Res | Spatial Res | Coverage | Chapter | Status |
|---------|------|--------|------|-------|----------|-------------|-------------|----------|---------|--------|
| MSLP (ERA5) | `data/cog/mslp/` | COG | 31 MB | 408 | Mean sea level pressure (Pa) | 6-hourly | 0.25deg | Dec 1 - Feb 15 | Ch.4 | On R2, in QGIS prototype |
| Wind U (ERA5) | `data/cog/wind-u/` | COG | 34 MB | 408 | 10m U-wind (m/s) | 6-hourly | 0.25deg | Dec 1 - Feb 15 | Ch.4 | On R2, needed for particle viz |
| Wind V (ERA5) | `data/cog/wind-v/` | COG | 35 MB | 408 | 10m V-wind (m/s) | 6-hourly | 0.25deg | Dec 1 - Feb 15 | Ch.4 | On R2, needed for particle viz |
| Wind Gust (ERA5) | `data/cog/wind-gust/` | COG | 34 MB | 408 | 10m gust (m/s) | 6-hourly | 0.25deg | Dec 1 - Feb 15 | Ch.4 | On R2, in QGIS prototype |
| Satellite IR (Meteosat) | `data/cog/satellite-ir/` | COG | 101 MB | 48 | IR 10.8um (DN 0-255) | Hourly | ~3 km | Jan 27-28 only | Ch.4 | On R2, in QGIS prototype |
| Satellite VIS (Meteosat) | `data/cog/satellite-vis/` | COG | 135 MB | 48 | Visible (DN 0-255) | Hourly | ~1 km | Jan 27-28 only | Ch.4 | On R2, daytime only ~10h |
| Precipitation (ERA5) | `data/cog/precipitation/` | COG | 8.4 MB | 78 | Daily precip (mm) | Daily | 0.25deg | Dec 1 - Feb 15 | Ch.4 | On R2, raster frames exist |
| Soil Moisture (ERA5-Land) | `data/cog/soil-moisture/` | COG | 8.4 MB | 77 | Vol. soil water (m3/m3) | Daily | 0.25deg | Dec 1 - Feb 15 | Ch.3 | On R2, raster frames exist |
| SST Anomaly (ERA5) | `data/cog/sst/` | COG | 6.9 MB | 66 | SST anomaly (degC) | Daily | 0.25deg | Dec 1 - Feb 4 | Ch.2 | On R2, in QGIS prototype |
| IVT (ERA5) | `data/cog/ivt/` | COG | 1.3 MB | 77 | Integ. vapor transport (kg/m/s) | Daily | 0.5deg | Dec 1 - Feb 15 | Ch.2 | On R2, low res (51x29 px) |
| Precondition Index | `data/cog/precondition/` | COG | 8.3 MB | 77 | Composite flood index | Daily | 0.25deg | Dec 1 - Feb 15 | Ch.7/8 | On R2, range 0-111 (not 0-1) |
| ECMWF HRES | `data/cog/ecmwf-hres/` | COG | 3 MB (COGs) | 85 | IVT, MSLP, wind u/v/speed | Daily (12Z) | 0.1deg | Jan 25 - Feb 10 | Ch.2/4 | Raw, higher res than ERA5 |
| ECMWF HRES GRIB | `data/cog/ecmwf-hres/grib/` | GRIB2 | 320 MB | ~85 | Source GRIB files | — | — | — | — | Raw cache, not for frontend |
| Wind Gust ICON | `data/cog/wind-gust-icon/` | — | 0 | 0 | — | — | — | — | — | EMPTY (never fetched) |
| ARPEGE | `data/cog/arpege/` | — | 0 | 0 | — | — | — | — | — | EMPTY (never fetched) |

**Total COG files: ~1,780 usable COGs + 85 GRIB source files**

### 1B. Flood Extent Data (Copernicus EMS) — 1.8 GB

| Dataset | Path | Format | Size | Features | Area (ha) | Coverage | Chapter | Status |
|---------|------|--------|------|----------|-----------|----------|---------|--------|
| EMSR861 GeoJSON | `data/flood-extent/emsr861.geojson` | GeoJSON | 2.3 MB | 506 | 7,723 | Coimbra (Storm Kristin) | Ch.6 | Ready |
| EMSR864 GeoJSON | `data/flood-extent/emsr864.geojson` | GeoJSON | 120 MB | 14,747 | 219,041 | 13 AOIs nationwide (Leonardo/Marta) | Ch.6 | Ready |
| Combined GeoJSON | `data/flood-extent/combined.geojson` | GeoJSON | 122 MB | 15,253 | 226,764 | All flood extent | Ch.1/6/7 | Ready |
| Combined PMTiles | `data/flood-extent/combined.pmtiles` | PMTiles | 17 MB | 15,253 | — | All flood extent | Ch.1/6/7 | In prototype |
| EMSR861 PMTiles | `data/flood-extent/emsr861.pmtiles` | PMTiles | 460 KB | 506 | — | Coimbra | Ch.6 | Ready |
| EMSR864 PMTiles | `data/flood-extent/emsr864.pmtiles` | PMTiles | 17 MB | 14,747 | — | 13 AOIs | Ch.6 | Ready |
| Salvaterra Temporal PMTiles | `data/flood-extent/salvaterra_temporal.pmtiles` | PMTiles | 6.4 MB | 4,234 | — | Salvaterra 3-date animation | Ch.6 | Ready |
| Salvaterra Feb 6 | `data/flood-extent/salvaterra_2026-02-06.geojson` | GeoJSON | 26 MB | 2,389 | 31,164 | Tejo floodplain | Ch.6 | Ready |
| Salvaterra Feb 7 | `data/flood-extent/salvaterra_2026-02-07.geojson` | GeoJSON | 5.2 MB | 1,112 | 42,673 | Tejo floodplain | Ch.6 | Ready |
| Salvaterra Feb 8 | `data/flood-extent/salvaterra_2026-02-08.geojson` | GeoJSON | 8.5 MB | 733 | 49,164 | Tejo floodplain | Ch.6 | Ready |
| Combined Parquet | `data/flood-extent/combined.parquet` | Parquet | 23 MB | 15,253 | — | All | — | Archive format |
| Raw CEMS ZIPs | `data/flood-extent/EMSR*/` | SHP+TIFF | ~1.5 GB | — | — | 35+ deliverables | — | Raw source, not for frontend |

**Also in raw form:** Flood depth rasters (.tif), modelled event polygons, maximum flood extents -- available in each EMSR*/directory but not yet extracted.

### 1C. Vector Datasets (QGIS-derived) — 35 MB

| Dataset | Path | Format | Size | Features | Description | Chapter | Status |
|---------|------|--------|------|----------|-------------|---------|--------|
| Wind Barbs (Kristin) | `data/qgis/wind-barbs-kristin.geojson` | GeoJSON | 1.4 MB | 6,419 | U+V derived arrows, Beaufort scale | Ch.4 | Single timestep only |
| MSLP Contours v2 | `data/qgis/mslp-contours-v2.geojson` | GeoJSON | 147 KB | 28 | Isobar lines at 400 Pa interval | Ch.4 | Single timestep (Jan 28 06Z) |
| MSLP L/H Markers | `data/qgis/mslp-lh-markers.geojson` | GeoJSON | 1 KB | 7 | Low/High pressure centers | Ch.4 | Single timestep |
| IVT Peak Storm | `data/qgis/ivt-peak-storm.geojson` | GeoJSON | 794 KB | 1,102 | IVT values at storm peak | Ch.2 | Ready |
| IPMA Warnings Timeline | `data/qgis/ipma-warnings-timeline.geojson` | GeoJSON | 649 KB | varies | Warning polygons with dates | Ch.4 | Reconstructed from Open-Meteo proxy |
| Precondition Basins | `data/qgis/precondition-basins.geojson` | GeoJSON | 68 KB | 11 | Basin-level precondition scores | Ch.7/8 | Ready |
| Precondition Peak Basins | `data/qgis/precondition-peak-basins.geojson` | GeoJSON | 66 KB | — | Basins at peak precondition | Ch.7 | Ready |
| Precondition Peak Points | `data/qgis/precondition-peak-points.geojson` | GeoJSON | 42 KB | 256 | Grid points at peak | Ch.7 | Ready |
| Soil Moisture Peak Points | `data/qgis/soil-moisture-peak-points.geojson` | GeoJSON | 37 KB | 256 | SM values at peak (Jan 31) | Ch.3 | Ready |
| Discharge Stations | `data/qgis/discharge-stations.geojson` | GeoJSON | 3.6 KB | 11 | GloFAS gauge locations | Ch.5 | Ready |
| Rivers Portugal | `data/qgis/rivers-portugal.geojson` | GeoJSON | 416 KB | 264 | Major river network | Ch.5 | Ready |
| Lightning (Kristin) | `data/qgis/lightning-kristin.geojson` | GeoJSON | 60 KB | 262 | MTG Lightning Imager flashes | Ch.4 | Ready, also PMTiles |
| Lightning PMTiles | `data/lightning/lightning-kristin.pmtiles` | PMTiles | 202 KB | 262 | Lightning for web delivery | Ch.4 | Ready |
| Wildfires 2024 | `data/qgis/wildfires-2024.geojson` | GeoJSON | 3.8 MB | varies | Burn scar perimeters | Ch.3/7 | Ready |
| Wildfires 2025 | `data/qgis/wildfires-2025.geojson` | GeoJSON | 5.4 MB | varies | Burn scar perimeters | Ch.3/7 | Ready |
| Wildfires Combined PMTiles | `data/qgis/wildfires-combined.pmtiles` | PMTiles | 3.9 MB | varies | Combined 2024+2025 burn scars | Ch.7 | Ready |
| Storm Tracks | `data/qgis/storm-tracks.geojson` | GeoJSON | 1.1 KB | 3 | Kristin/Leonardo/Marta paths | Ch.4 | Schematic (manual coords) |

### 1D. Frontend JSON (pre-processed for scroll narrative) — 3.0 MB

| Dataset | Path | Format | Size | Description | Chapter | Status |
|---------|------|--------|------|-------------|---------|--------|
| Discharge Timeseries | `data/frontend/discharge-timeseries.json` | JSON | 53 KB | 8 rivers daily discharge + anomaly | Ch.5 | In prototype |
| IPMA Warnings | `data/frontend/ipma-warnings.json` | JSON | 14 KB | 18 districts x 21 days x 3 warning types | Ch.4 | In prototype |
| IVT Peak Storm | `data/frontend/ivt-peak-storm.json` | JSON | 39 KB | IVT grid at storm peak | Ch.2 | In prototype |
| Precip Frames | `data/frontend/precip-frames.json` | JSON | 986 KB | 342 pts x 77 days temporal grid | Ch.4 | In prototype |
| Precip Storm Totals | `data/frontend/precip-storm-totals.json` | JSON | 14 KB | Accumulated precip per point | Ch.4 | In prototype |
| Precondition Basins | `data/frontend/precondition-basins.json` | JSON | 687 B | Basin-level scores | Ch.7/8 | In prototype |
| Precondition Frames | `data/frontend/precondition-frames.json` | JSON | 1.2 MB | Temporal precondition grid | Ch.7 | In prototype |
| Precondition Peak | `data/frontend/precondition-peak.json` | JSON | 15 KB | Peak precondition values | Ch.7 | In prototype |
| Soil Moisture Frames | `data/frontend/soil-moisture-frames.json` | JSON | 763 KB | 74 pts x 77 days temporal grid | Ch.3 | In prototype |
| Raster Manifest | `data/frontend/raster-manifest.json` | JSON | 17 KB | Frame URLs for PNG animation | Ch.3/4 | In prototype |

### 1E. Raster Frames (pre-rendered PNGs for animation) — 14 MB

| Dataset | Path | Format | Size | Count | Description | Chapter | Status |
|---------|------|--------|------|-------|-------------|---------|--------|
| Soil Moisture PNGs | `data/raster-frames/soil-moisture/` | PNG | 11 MB | 77 | Daily SM maps, transparent bg | Ch.3 | Ready for crossfade animation |
| Precipitation PNGs | `data/raster-frames/precipitation/` | PNG | 2.5 MB | 77 | Daily precip maps, transparent bg | Ch.4 | Ready for crossfade animation |

### 1F. Raw Temporal Data (Parquet/JSON source) — 97 MB

| Dataset | Path | Format | Size | Description | Chapter | Status |
|---------|------|--------|------|-------------|---------|--------|
| Discharge (Parquet) | `data/temporal/discharge/discharge.parquet` | Parquet | 32 KB | 8 rivers daily discharge | Ch.5 | Processed to frontend JSON |
| Soil Moisture (Parquet) | `data/temporal/moisture/soil_moisture.parquet` | Parquet | 230 KB | 74-point grid x 72 days | Ch.3 | Processed to frontend JSON |
| Precipitation (Parquet) | `data/temporal/precipitation/precipitation.parquet` | Parquet | 342 KB | 330-point grid x 74 days | Ch.4 | Processed to frontend JSON |
| Precondition (Parquet) | `data/temporal/precondition/precondition.parquet` | Parquet | 1.2 MB | Composite index temporal | Ch.7/8 | Processed to frontend JSON |
| IVT (Parquet) | `data/temporal/ivt/ivt.parquet` | Parquet | 699 KB | IVT temporal data | Ch.2 | Processed to COGs + JSON |
| SST Anomaly (NetCDF) | `data/temporal/sst/sst_anomaly.nc` | NetCDF | 10 MB | Atlantic SST anomaly field | Ch.2 | Processed to daily TIFs |
| SST Daily TIFs | `data/temporal/sst/daily/` | GeoTIFF | — | 62 | Daily SST anomaly maps | Ch.2 | Source for COG generation |
| ERA5 NetCDF cache | `data/temporal/era5/_nc_cache/` | NetCDF | 81 MB | 6 | Raw ERA5 downloads | — | Source cache |

### 1G. Point-source Data (JSON)

| Dataset | Path | Format | Size | Description | Chapter | Status |
|---------|------|--------|------|-------------|---------|--------|
| Soil Moisture Grid Points | `data/soil-moisture/grid-points.json` | JSON | 5 KB | 74 lat/lon pairs | Ch.3 | Ready |
| Soil Moisture Timeseries | `data/soil-moisture/timeseries.json` | JSON | 134 KB | Daily SM per point | Ch.3 | Ready |
| SM Basin Averages | `data/soil-moisture/basin-averages.json` | JSON | 16 KB | Per-basin SM average | Ch.3 | Ready |
| Precip Daily Grid | `data/precipitation/daily-grid.json` | JSON | 249 KB | Daily precip per point | Ch.4 | Ready |
| Precip Accumulation | `data/precipitation/accumulation-jan25-feb07.json` | JSON | 31 KB | Storm total per point | Ch.4 | Ready |
| Precip Basin Averages | `data/precipitation/basin-averages.json` | JSON | 14 KB | Per-basin precip totals | Ch.4 | Ready |
| Discharge per river (8) | `data/discharge/*.json` | JSON | 76 KB | 8 individual river files + summary | Ch.5 | Ready |

### 1H. Consequence & Impact Data

| Dataset | Path | Format | Size | Features | Description | Chapter | Status |
|---------|------|--------|------|----------|-------------|---------|--------|
| Consequence Events | `data/consequences/events.geojson` | GeoJSON | 53 KB | 42 | Geocoded impacts: 10 deaths, 9 infrastructure, 7 evacuations, 4 river records, 2 levee/dam, 2 landslides, etc. | Ch.6 | In prototype |

### 1I. Static Images

| Dataset | Path | Format | Size | Description | Chapter | Status |
|---------|------|--------|------|-------------|---------|--------|
| Sentinel-1 Tejo flood | `data/static-images/sentinel1-tejo-feb07.jpg` | JPEG | 1.3 MB | ESA composite Feb 7 vs Dec 27 | Ch.1 | Needs georeferencing |
| GPM Precipitation map | `data/static-images/gpm-precipitation-iberia-feb01-07.jpg` | JPEG | 504 KB | NASA/JAXA GPM accumulation | Ch.4 | Static image overlay |
| ATTRIBUTION.md | `data/static-images/ATTRIBUTION.md` | — | 1 KB | Source/license for images | — | Ready |

### 1J. Geographic Assets

| Dataset | Path | Format | Size | Features | Description | Chapter | Status |
|---------|------|--------|------|----------|-------------|---------|--------|
| Catchment Basins | `assets/basins.geojson` | GeoJSON | 65 KB | 11 | Primary spatial unit (river, name_pt, type) | All | In prototype |
| Districts | `assets/districts.geojson` | GeoJSON | 27 KB | 18 | Administrative (district, ipma_code) | Ch.4 | In prototype |
| OG Image | `assets/og-image.png` | PNG | 197 KB | — | Social sharing card | — | Ready |

### 1K. QGIS Project & Renders

| Dataset | Path | Format | Size | Description | Status |
|---------|------|--------|------|-------------|--------|
| QML Styles (18) | `data/qgis/styles/*.qml` | QML | 328 KB | QGIS symbology for all layers | Reference for web translation |
| WX Audit Renders (25) | `data/qgis/renders/wx-audit/` | PNG | 9.4 MB | Layer-by-layer visual QA | Reference |
| WX Prototype Renders (17) | `data/qgis/renders/wx2-*` | PNG | 4.8 MB | Earlier prototyping renders | Reference |
| QGIS Project README | `data/qgis/README.md` | — | 12 KB | Full layer inventory | Documentation |

### 1L. Other

| Dataset | Path | Format | Size | Description | Status |
|---------|------|--------|------|-------------|--------|
| Radar test image | `data/radar/test_ipma_radar.jpg` | JPEG | 67 KB | Sample IPMA radar composite | Proof of concept |
| Radar status report | `data/radar/RADAR-STATUS-REPORT.md` | — | 5 KB | Investigation results | Documentation |
| Video analysis frames | `data/video-analysis/frames/` | PNG | 269 MB | 509 frames from WeatherWatcher14 | Creative reference |
| Video motion analysis | `data/video-analysis/MOTION-ANALYSIS.md` | — | 15 KB | 6 visual effects breakdown | Creative direction input |
| API response cache | `data/cache/` | JSON | 9.5 MB | 2,404 cached API responses | Reproducibility |

---

## 2. Chapter-by-Chapter Data Mapping

### Chapter 2: The Planetary Scale (Atlantic Engine)

**Narrative purpose:** Establish that the crisis originated far from Portugal -- warm Atlantic SSTs fed atmospheric rivers carrying extreme moisture toward Iberia.

**Available data:**
- SST anomaly COGs: 66 daily maps (Dec 1 - Feb 4), 0.25deg, 6.9 MB. Shows warm Atlantic anomaly.
- SST anomaly NetCDF: 10 MB source file for full Atlantic domain.
- IVT COGs: 77 daily maps, but LOW resolution (0.5deg = 51x29 px). Atmospheric river signal present but visually coarse.
- ECMWF HRES IVT: 17 files at 0.1deg resolution (Jan 25 - Feb 10). MUCH better resolution for atmospheric river visualization. Peak IVT: 1,153 kg/m/s (confirms atmospheric river).
- IVT peak storm GeoJSON: 1,102 points at peak values. Ready for point-based viz.
- Storm tracks GeoJSON: 3 schematic LineStrings for Kristin/Leonardo/Marta paths. Hand-drawn, needs verification.

**What's missing:**
- SST COGs stop at Feb 4 (11 days before end of crisis). Gap for Leonardo/Marta period.
- IVT ERA5 COGs are too coarse (0.5deg) for dramatic visualization. The ECMWF HRES IVT at 0.1deg is much better but only covers the storm window.
- No jet stream / upper-level wind data. 250 hPa winds would show the jet stream configuration driving the storm train.
- No storm track data from official sources (IPMA/AEMET storm tracking). Current paths are schematic.

**What would make this chapter sing:**
- Animated IVT field showing the "moisture highway" from subtropics to Iberia. Use the ECMWF HRES 0.1deg IVT data for the storm window, ERA5 0.5deg for context.
- SST anomaly map as background layer with warm colors in the subtropical Atlantic.
- Wind particle animation on the Atlantic scale showing the jet stream configuration.
- Animated storm tracks with named labels moving along their paths.

**Assessment: 6/10 data readiness.** SST and IVT exist but need format optimization. The IVT resolution gap is the main concern -- the ERA5 version is too pixelated for a dramatic wide-angle Atlantic view, but the ECMWF HRES version only covers the storm window. The story is there in the data, but visual impact requires careful composition.

---

### Chapter 3: The Setup (Soil Saturation)

**Narrative purpose:** Show 8 weeks of progressive soil saturation -- the invisible precondition that made the storms catastrophic.

**Available data:**
- Soil moisture COGs: 77 daily maps, 0.25deg, 8.4 MB. Full Dec-Feb coverage.
- Soil moisture PNG frames: 77 pre-rendered transparent PNGs, 11 MB. READY for MapLibre image source crossfade.
- Soil moisture JSON timeseries: 74 points x 77 days. READY for point-based animation.
- Soil moisture basin averages: Per-basin daily values. Perfect for basin-level sparklines.
- Soil moisture peak points GeoJSON: 256 points at saturation peak (Jan 31).
- Precondition basins: Basin polygons with composite scores.
- Wildfires 2024 + 2025: Burn scar perimeters (9.2 MB GeoJSON, 3.9 MB PMTiles). Shows stripped vegetation that increased runoff.

**What's missing:**
- Nothing critical. This is the strongest chapter data-wise.
- Could improve with higher-resolution soil moisture (ERA5-Land is 0.1deg vs the 0.25deg grid used).

**What would make this chapter sing:**
- Scroll-controlled PNG frame animation showing the ground going from brown/dry to deep blue/saturated over 8 weeks. The raster frames are READY for this.
- Basin-level sparklines in the text panel showing each basin's saturation curve.
- Wildfire scars as a subtle overlay during or after the saturation animation -- "the ground was already wounded."
- Single dramatic number: saturation went from 0.13 to 0.90 (83% of dynamic range consumed before the first storm).

**Assessment: 9/10 data readiness.** All data exists, pre-processed, validated. The 77-frame PNG animation sequence is the most deployment-ready dataset in the project.

---

### Chapter 4: The Storms Arrive (Meteorological Drama)

**Narrative purpose:** Show three storms hammering Portugal in rapid succession. Maximize the drama of wind, rain, pressure drops, satellite imagery, and escalating IPMA warnings.

**Available data:**
- MSLP COGs: 408 files at 6-hourly resolution, 31 MB. Full storm evolution.
- MSLP contours GeoJSON: 28 isobars at Jan 28 06Z. SINGLE timestep only.
- MSLP L/H markers: 7 pressure centers. SINGLE timestep only.
- Wind U/V COGs: 408+408 files, 69 MB combined. Source for wind particle animation.
- Wind gust COGs: 408 files, 34 MB. Peak: 38.3 m/s over Portugal.
- Wind barbs GeoJSON: 6,419 arrows. SINGLE timestep only.
- Satellite IR COGs: 48 hourly frames, 101 MB. Storm Kristin comma cloud visible. Jan 27-28.
- Satellite VIS COGs: 48 hourly frames, 135 MB. Daytime only (~10 usable hours). Jan 27-28.
- Precipitation COGs: 78 daily maps. Storm window mean 230mm, max 567mm.
- Precipitation PNG frames: 77 pre-rendered. READY.
- IPMA warnings JSON: 18 districts x 21 days x 3 warning types (precipitation, wind, coastal agitation). Reconstructed from Open-Meteo proxy.
- Lightning GeoJSON: 262 flashes for Storm Kristin. Peak 56 flashes at 18 UTC Jan 27.
- Lightning PMTiles: 202 KB web-ready. Yellow star + glow styling defined.
- Storm tracks GeoJSON: 3 schematic paths.
- ECMWF HRES COGs: 85 files (MSLP, wind u/v, speed, IVT) at 0.1deg. Higher resolution than ERA5.
- Static GPM precipitation image: NASA/JAXA accumulation Feb 1-7.

**What's missing:**
- **Temporal MSLP contours:** Only have contours for ONE timestep. Need to generate from all 408 MSLP COGs to animate isobar evolution (the "breathing cyclone" effect from the WeatherWatcher video). This is a **scripting task**, not a data acquisition task.
- **Temporal wind barbs:** Same gap -- only ONE timestep of computed wind barbs. Need to batch-generate from the 408 U/V COG pairs.
- **Radar data:** No actual ground-based radar. GPM IMERG (11km, 30-min, NASA Earthdata auth required) would be the best substitute. Open-Meteo hourly precip (25km) is available now as fallback.
- **Satellite coverage beyond Jan 27-28:** Only 48 hours of Meteosat imagery. Missing Leonardo (Feb 5-7) and Marta (Feb 10-11) storm imagery.
- **VIS satellite for nighttime:** VIS is dark for ~14h/day. Only ~10 daytime frames usable per day.
- **Temperature field:** No 2m or 850hPa temperature data for warm/cold front visualization.

**What would make this chapter sing:**
- Animated MSLP isobar evolution showing the deep low approaching and passing -- requires batch contour generation from the 408 MSLP COGs.
- Wind particle animation using the 816 U/V COGs -- the "wow factor" visualization from the WeatherWatcher video.
- Satellite IR timelapse of the Storm Kristin comma cloud -- 48 hourly COGs ready to animate.
- IPMA warning escalation map: districts flashing yellow->orange->red as storms hit.
- Lightning overlay during the frontal passage -- 262 flashes clustering around the cold front.
- Precipitation sweep showing the rainfall accumulation building day by day.

**Assessment: 7/10 data readiness.** Massive raw data exists, but key derived products (temporal contours, temporal wind barbs, wind particle textures) need processing. The satellite imagery covers only Kristin, not Leonardo/Marta. Wind particle visualization is the highest-impact item but requires WebGL implementation.

---

### Chapter 5: The Rivers Respond (Discharge)

**Narrative purpose:** Show rivers swelling past flood thresholds as saturated ground funnels all rainfall directly into waterways.

**Available data:**
- Discharge per river JSON: 8 rivers (Tejo, Mondego, Sado, Douro, Guadiana, Minho, Vouga, Lis). Daily values + anomaly.
- Discharge summary: Peak amplification factors (Guadiana 11.5x, Tejo 6.6x, Mondego 6.0x).
- Discharge frontend JSON: Pre-processed for sparkline rendering. In prototype.
- Discharge stations GeoJSON: 11 gauge locations as point features.
- Rivers Portugal GeoJSON: 264 line segments for the river network.
- Basins GeoJSON: 11 catchment polygons with attributes.

**What's missing:**
- **Sub-daily discharge data:** GloFAS provides daily values only. Hourly data would show the surge dynamics more dramatically.
- **Flood stage thresholds:** No official "flood stage" values for Portuguese rivers. Would need to derive from GloFAS return period analysis or SNIRH (which has no API).
- **Dam discharge data:** GloFAS models naturalized flows (ignores dams). Douro/Guadiana have major dams that regulate actual river flow. Real dam releases are not in the data.

**What would make this chapter sing:**
- Animated river lines that "swell" in thickness as discharge increases -- using the rivers GeoJSON with data-driven line width from discharge timeseries.
- Sparkline charts in the text panel showing each river's hydrograph climbing.
- Station markers pulsing at peak discharge, sized by amplification factor.
- Basin polygons colored by precondition index as context.
- Sequential reveal: Kristin peaks (Jan 28-29) -> Leonardo peaks (Feb 5-7) -> Marta peaks (Feb 10-12). The narrative that "before the rivers dropped, the next storm hit" is visible in the data.

**Assessment: 8/10 data readiness.** Data is validated and pre-processed. The main gap is the lack of flood stage thresholds (hard to show "crossing the danger line" without them). The daily temporal resolution is adequate for the narrative but not for dramatic surge visualization.

---

### Chapter 6: The Consequences (Human Cost)

**Narrative purpose:** Transition from data to people. Show where the water went and what it destroyed.

**Available data:**
- Consequence events GeoJSON: 42 geocoded impacts with rich metadata (type, date, storm, descriptions in PT/EN, sources, image URLs, district, municipality, severity). Includes 10 deaths, 9 infrastructure damages, 7 evacuations, 4 river records, 2 levee/dam failures, 2 landslides.
- CEMS flood extent: 15,253 polygons across 14 AOIs, 226,764 ha total. PMTiles ready for web.
- Salvaterra temporal: 3-date progressive inundation (31,164 ha -> 42,673 ha -> 49,164 ha). PMTiles with date attribute for animation.
- CEMS flood depth rasters: Available in each EMSR*/directory but not extracted. Could show water depth in meters.
- Sentinel-1 composite image: Static JPEG, 1.3 MB. Needs georeferencing for map overlay.
- CEMS summary maps: PDFs in each EMSR*/Maps/ directory.

**What's missing:**
- **Post-flood satellite imagery (before/after):** No Sentinel-2 true color imagery for before/after comparison. This is the standard "aftermath" visual in disaster storytelling. Available from Copernicus Data Space (free, STAC) but needs acquisition.
- **Geocoded photos:** The consequence events have `image_url` fields pointing to news agency CDN URLs, but these are external links (may break). No local photo archive.
- **Landslide-specific data:** Only 2 landslide events in the consequence GeoJSON. The fire-flood interaction (summer 2025 burn scars -> winter 2026 landslides) deserves more spatial detail.
- **Road closure polylines:** Only 2 closure events as points. The actual closed road segments (A1 collapse, EN roads) would be more visually impactful as lines.
- **Evacuation zones:** No polygons for evacuation areas. Only point markers.

**What would make this chapter sing:**
- Salvaterra temporal animation: flood extent growing 58% over 2 days, rendered as expanding blue polygons over satellite imagery.
- Before/after satellite swipe (Sentinel-2) for Coimbra or Salvaterra.
- Consequence markers appearing as the user scrolls through sub-sections (Alcacer do Sal, Coimbra, A1).
- Each marker expandable with the event description and source photo.
- Flood depth overlay at Salvaterra (the raster TIFs exist in the raw data but are not extracted).

**Assessment: 7/10 data readiness.** The flood extent data is excellent (226,764 ha mapped, temporal evolution at Salvaterra). Consequence markers are good but could be richer. The main gap is Sentinel-2 before/after imagery, which would add enormous emotional impact.

---

### Chapter 7: The Full Picture (Climax)

**Narrative purpose:** Pull back to national scale and overlay ALL consequences on ALL causes. The moment where causality becomes visible in a single frame.

**Available data:**
- ALL precondition data (soil, precip, discharge) -> composite index at peak
- ALL flood extent polygons (15,253 features)
- ALL consequence markers (42 events)
- Wildfire burn scars (2024+2025) in PMTiles for fire-flood interaction
- Basin and district boundaries for context

**What's missing:**
- Nothing critical that isn't already missing from earlier chapters.
- **Pre-computed composite frame:** A "money shot" rendering showing all causal layers simultaneously at optimal opacity. This is a styling/composition challenge, not a data gap.

**What would make this chapter sing:**
- Careful opacity management: max 3 layers at full visibility simultaneously.
- Wildfire scars as the "surprise reveal" -- the hidden connection between summer fires and winter floods.
- A single framing sentence: "Each piece alone was manageable. Together, they created a catastrophe."

**Assessment: 8/10 data readiness.** This chapter composites existing data. The challenge is visual composition, not data acquisition.

---

## 3. External Data Opportunities

### High Value, Easy Acquisition

| Dataset | Source | Auth | Format | Effort | Chapter | Impact |
|---------|--------|------|--------|--------|---------|--------|
| Sentinel-2 before/after | Copernicus Data Space | Free STAC, no auth for tiles | COG via STAC | Easy script | Ch.6 | HIGH - emotional anchor |
| Met Office Global 10km (STAC) | Microsoft Planetary Computer | No auth | NetCDF on S3 | Medium script | Ch.4 | MEDIUM - higher quality NWP, demonstrates STAC patterns |
| GPM IMERG precipitation | NASA Earthdata | Free registration | HDF5/OPeNDAP | Easy script | Ch.4 | MEDIUM - sub-daily storm progression |
| Open-Meteo hourly precip | Open-Meteo | None | JSON API | Easy script | Ch.4 | LOW-MED - hourly storm animation fallback |
| Additional Meteosat imagery (Leonardo/Marta) | EUMETSAT | eumdac (existing creds) | Native | Medium script | Ch.4 | HIGH - extends satellite from Kristin-only to all 3 storms |

### Moderate Value, Needs Processing

| Dataset | Source | Auth | Format | Effort | Chapter | Impact |
|---------|--------|------|--------|--------|---------|--------|
| ERA5 850hPa temperature | CDS or Open-Meteo | CDS needs auth; Open-Meteo free | NetCDF/JSON | Medium script + COG generation | Ch.4 | MEDIUM - warm/cold front visualization |
| ERA5 250hPa winds | CDS or Planetary Computer | Varies | NetCDF | Medium-High | Ch.2 | MEDIUM - jet stream visualization |
| CEMS flood depth extraction | Already downloaded | N/A | GeoTIFF | Easy processing | Ch.6 | MEDIUM - water depth at Salvaterra |
| CEMS maximum flood extent | Already downloaded | N/A | SHP | Easy processing | Ch.6 | LOW - combined max extent per AOI |
| ICNF detailed burn areas | ICNF / EFFIS | May need request | SHP | Medium | Ch.7 | LOW-MED - already have EFFIS data |

### High Value, Complex Pipeline

| Dataset | Source | Auth | Format | Effort | Chapter | Impact |
|---------|--------|------|--------|--------|---------|--------|
| OPERA radar composites | EUMETNET | Institutional only | HDF5 | BLOCKED | Ch.4 | Would be HIGH but inaccessible |
| SNIRH river level observations | SNIRH/APA | No API | Manual scrape | HIGH effort | Ch.5 | HIGH - real observed river levels (not modelled) |
| IPMA actual historical warnings | IPMA | No archive API | Manual reconstruction | Already done (proxy) | Ch.4 | MEDIUM - proxy exists but approximates |

### Low Priority / Nice-to-Have

| Dataset | Source | Auth | Format | Effort | Chapter | Impact |
|---------|--------|------|--------|--------|---------|--------|
| NOAA OISST (higher quality SST) | NOAA | None | NetCDF | Easy script | Ch.2 | LOW - ERA5 SST already exists |
| Copernicus GFM real-time flood maps | Copernicus Global Flood Monitoring | Free | GeoTIFF | Medium | Ch.6 | LOW - CEMS is more authoritative |
| DEM / hillshade for terrain context | SRTM / Copernicus DEM | Free | COG | Easy | All | LOW - aesthetic, not narrative |

---

## 4. Format Conversion Pipeline

### Priority 1 (High impact, enables key visualizations)

| Task | Input | Output | Estimated Effort | Enables |
|------|-------|--------|-----------------|---------|
| **Generate temporal MSLP contours** | 408 MSLP COGs | 408 GeoJSON contour files (one per timestep) | 2h script (gdal_contour loop) | MSLP isobar animation (Effect 3) |
| **Generate temporal wind barbs** | 408+408 wind U/V COGs | 408 GeoJSON point files with speed/direction | 2h script | Synoptic animation (Effect 5) |
| **Generate temporal L/H markers** | 408 MSLP COGs | 408 GeoJSON point files | 1h script (scipy local minima) | Pressure center tracking |
| **Satellite IR to PNG frames** | 48 IR COGs | 48 PNG frames with inverted grayscale colormap | 1h script (rasterio + PIL) | Satellite cloud motion animation (Effect 4) |
| **IVT to higher-resolution vis** | ECMWF HRES IVT COGs (0.1deg) | Merged with ERA5 IVT timeline | 2h script | Atmospheric river animation at readable resolution |

### Priority 2 (Moderate impact, processing required)

| Task | Input | Output | Estimated Effort | Enables |
|------|-------|--------|-----------------|---------|
| **Wind U/V to particle textures** | Wind U/V COGs | PNG texture pairs per timestep for deck.gl-wind | 3h script + testing | Wind particle animation (Effect 1, highest wow-factor) |
| **Flood depth extraction** | Raw CEMS SHP `floodDepthA` layers | GeoJSON or raster of water depths at Salvaterra | 1h script (geopandas) | Water depth visualization in Ch.6 |
| **Satellite VIS to PNG frames** | 48 VIS COGs | Filtered daytime PNGs (~20 usable) | 30min script | Daytime cloud motion animation |
| **Georef Sentinel-1 composite** | sentinel1-tejo-feb07.jpg + .aux.xml | GeoTIFF or positioned image source | 30min manual (QGIS georeferencer) | Map overlay in Ch.1 |
| **MSLP field to temperature-style frames** | MSLP COGs | Color-mapped PNG frames (blue-red diverging) | 1h script | MSLP field background for synoptic animation |

### Priority 3 (Nice-to-have, polish)

| Task | Input | Output | Estimated Effort | Enables |
|------|-------|--------|-----------------|---------|
| **Pre-compute isobar labels** | MSLP contour GeoJSONs | Labeled point features per contour | 2h script | On-map isobar labels |
| **Optimize wildfire PMTiles** | Wildfires GeoJSON | Simplified PMTiles at narrative-relevant zoom | 30min tippecanoe | Faster wildfire overlay loading |
| **Consequence markers to PMTiles** | events.geojson (42 features) | PMTiles for web delivery | 10min tippecanoe | Marginal perf gain (already small) |
| **Precondition PNG frames** | 77 precondition COGs | Pre-rendered PNGs (like soil-moisture) | 1h script | Direct crossfade animation (avoids titiler) |

---

## 5. Data Gaps and Blockers

### Critical Gaps (impact narrative quality)

1. **No Sentinel-2 before/after imagery.** The design document calls for satellite before/after comparison in Ch.6, and the ESA Sentinel-1 composite (Ch.1 hook) is only a static JPEG without proper georeferencing. Acquiring actual Sentinel-2 scenes from Copernicus Data Space would provide: (a) the high-impact before/after swipe for Salvaterra/Coimbra, (b) a properly georeferenced flood composite for Ch.1. **Fetch difficulty: Easy -- free STAC API, no auth for processing API tiles.**

2. **Satellite imagery limited to Storm Kristin only.** The Meteosat COGs (96 files) cover only Jan 27-28. Storms Leonardo (Feb 5-7) and Marta (Feb 10-11) have NO satellite imagery at all. This means Ch.4 can show cloud motion only for the first storm, creating an imbalanced narrative. **Fetch difficulty: Medium -- existing eumdac pipeline in `scripts/fetch_eumetsat.py` can be re-run for the Leonardo/Marta dates.**

3. **Temporal MSLP contours do not exist.** The 408 MSLP COGs are raw rasters. Only a single timestep has been converted to isobar contour lines. The animated synoptic chart -- the "breathing cyclone" -- is one of the highest-impact visuals but requires batch processing. **Fix: Pure processing task, no external fetch needed.**

4. **IVT resolution mismatch.** The daily IVT COGs at 0.5deg (51x29 pixels) are too coarse for the Atlantic-scale view in Ch.2. The ECMWF HRES IVT at 0.1deg is much better but only covers Jan 25 - Feb 10. No IVT data before Jan 25 at high resolution. **Potential fix: Open-Meteo pressure-level archive to compute real IVT at 0.25deg for the full Dec-Feb period.**

### Moderate Gaps

5. **No sub-daily precipitation.** Current data is daily aggregates. Radar-like hourly or half-hourly precipitation would dramatically improve Ch.4's storm arrival visualization. GPM IMERG (free NASA registration) or Open-Meteo hourly grid would fill this. **Fetch difficulty: Easy (Open-Meteo) or Easy+auth (GPM IMERG).**

6. **IPMA warnings are proxied, not actual.** The warning timeline was reconstructed from Open-Meteo precipitation data using threshold estimates, not from actual IPMA warning records. The thresholds may not exactly match IPMA's criteria. Acceptable for narrative but not formally verified beyond news cross-checking.

7. **No flood stage thresholds for rivers.** GloFAS discharge is in absolute m3/s, but without "flood stage" reference lines, the audience cannot see when rivers cross danger thresholds. SNIRH has these values but has no API. **Potential fix: Derive approximate thresholds from GloFAS return period analysis.**

### Minor Gaps

8. **SST COGs end at Feb 4.** Missing 11 days of the crisis. The SST anomaly field changes slowly, so this is not narrative-critical, but completeness would be better.

9. **VIS satellite is half-dark.** Of 48 VIS COGs, only ~20 have meaningful daytime content (Portuguese winter daylight ~8am-6pm UTC). The nighttime files are essentially blank.

10. **No temperature field.** No 2m or 850hPa temperature data for visualizing warm/cold fronts in Ch.4. Would enhance the synoptic meteorology narrative but is not essential.

---

## 6. Storytelling Gems

### Gem 1: The Salvaterra Temporal Triptych

Three SAR satellite passes over Salvaterra de Magos (Tejo basin) showing flood extent on Feb 6, 7, and 8. The flood area grew from **31,164 ha to 49,164 ha -- a 58% expansion in 48 hours.** This is the single most powerful temporal dataset in the project: you can literally watch an area the size of a small country flood in real-time. The PMTiles are ready (`salvaterra_temporal.pmtiles`), the per-date GeoJSONs exist, and the `source_date` attribute enables filter-based animation.

**Storytelling use:** Progressive flood reveal in Ch.6. Start with the Feb 6 extent, scroll forward to Feb 7 (37% growth), then Feb 8 (49,164 ha). Overlay on satellite imagery for maximum emotional impact.

### Gem 2: Lightning as Storm Fingerprint

262 lightning flashes from the MTG Lightning Imager during Storm Kristin, peaking at 56 flashes at 18 UTC on Jan 27 -- the exact moment of frontal passage over central Portugal. Lightning clusters along the cold front line, providing a vivid visual marker for where the most violent convection occurred.

**Storytelling use:** Flash the lightning points during the satellite IR animation, timed to the frontal passage. The sudden burst of yellow stars on a dark satellite backdrop is visually electric.

### Gem 3: The Wildfire-Flood Connection (Unexploited)

Summer 2025 burn scars (5.4 MB GeoJSON, PMTiles ready) cover huge areas of central and northern Portugal. These stripped vegetation removes the natural sponge that holds hillslopes together. When Kristin/Leonardo/Marta hit those slopes, the result was landslides and accelerated runoff. **This dataset is fully acquired (2024+2025 fire perimeters from EFFIS) and converted to PMTiles but has NOT been used in the narrative at all.**

**Storytelling use:** Ch.7 reveal -- overlay burn scars on the flood extent map. The spatial correlation between 2025 fire areas and 2026 flood/landslide severity is the "hidden cause" that elevates the story from "flood map" to "territorial risk analysis." This is the insight that makes cheias.pt intellectually original, not just visually impressive.

### Gem 4: The 21-Day Warning Escalation

The IPMA warnings data (18 districts x 21 days) shows a remarkable escalation pattern: green -> yellow -> orange -> red across the country, with **two distinct waves** (Kristin Jan 28-29, Leonardo Feb 5-7) and a brief respite between them. The warning data includes three types (precipitation, wind, coastal agitation), meaning you can show different hazards activating at different times.

**Storytelling use:** Animated choropleth map of Portugal with districts flashing warning colors. The two-wave pattern -- green respite -- then second surge to red is a powerful visual rhythm. Show alongside the precipitation animation for cause-and-effect.

### Gem 5: The ECMWF HRES IVT at 0.1deg

While the ERA5 IVT is too coarse for dramatic visualization (0.5deg = ~50km pixels), the ECMWF HRES IVT data at 0.1deg (~10km) shows the atmospheric river structure in remarkable detail: moisture plumes extending from the subtropical Atlantic to Iberia, with peak values of **1,153 kg/m/s** -- a physically significant atmospheric river by any definition (>250 kg/m/s = AR threshold).

**Storytelling use:** This is the "smoking gun" for Ch.2. An atmospheric river visualization at readable resolution, showing the moisture highway from the tropics to Portugal. The 0.1deg resolution means individual moisture filaments are visible.

### Gem 6: The Coimbra Dual-Storm Fingerprint

Coimbra has flood extent data from BOTH storm activations: EMSR861 (Kristin, 7,723 ha) and EMSR864 (Leonardo, 10,766 ha growing to 11,813 ha). This means you can show the same city flooded twice in 10 days, with the second flood LARGER than the first. This dual-impact pattern is documented nowhere else in such spatial detail.

**Storytelling use:** Coimbra sub-section in Ch.6. First flood (7,723 ha) -> recovery attempt -> second, larger flood (11,813 ha). The "before the rivers dropped, the next storm hit" narrative becomes physically visible.

### Gem 7: The Full CEMS Coverage Arc

EMSR864 covers 13 Portuguese AOIs from **Minho (north) to Mertola/Guadiana (south)**, spanning the full geographic extent of the crisis. The spatial pattern -- densest flooding in the central Tejo basin, secondary clusters in Aveiro, Coimbra, and the Sado -- maps directly onto the precipitation gradient (NW heaviest) and soil moisture pattern (central/south most saturated). This nationwide coverage at sub-hectare resolution (10m SAR) is an extraordinary dataset for a single event narrative.

**Storytelling use:** National overview in Ch.7 showing all 226,764 ha of mapped flooding. The geographic pattern of flooding correlates with the causal chain established in earlier chapters.

### Gem 8: The Precondition Signal Two Weeks Early

The precondition peak data shows that on **Jan 25** -- three days before Storm Kristin -- the Minho-Lima basin was already at 0.49 on the precondition index. By Feb 5, the peak fraction of orange/red points was at its highest. The data literally shows the disaster building two weeks before the consequences materialized.

**Storytelling use:** Ch.8's thesis: "O que os dados ja sabiam." This is the bridge between retrospective analysis and future prediction. The precondition index showed elevated risk before the first death.

---

## 7. Summary: Data Readiness by Chapter

| Chapter | Data Readiness | Primary Gap | Key Action |
|---------|---------------|-------------|------------|
| Ch.2 (Atlantic) | 6/10 | IVT resolution, no jet stream | Use ECMWF HRES IVT (0.1deg), compute IVT from Open-Meteo pressure levels |
| Ch.3 (Soil) | 9/10 | None critical | Deploy existing PNG animation |
| Ch.4 (Storms) | 7/10 | Temporal contours, wind particles, satellite for Leonardo/Marta | Batch process MSLP contours, extend Meteosat fetch |
| Ch.5 (Rivers) | 8/10 | No flood stage thresholds | Derive from GloFAS return periods |
| Ch.6 (Consequences) | 7/10 | No Sentinel-2 before/after | Fetch from Copernicus Data Space (easy) |
| Ch.7 (Full Picture) | 8/10 | None (composites earlier data) | Wildfire overlay integration |

**Overall project data readiness: 7.5/10**

The data foundation is strong. The remaining gaps are either processing tasks (generating temporal contours from existing COGs) or straightforward external fetches (Sentinel-2, extended Meteosat). No dataset is truly blocked except OPERA radar (institutional barrier). The biggest untapped narrative potential lies in the wildfire-flood connection (data exists, not used) and the Salvaterra temporal triptych (data ready, needs animation implementation).
