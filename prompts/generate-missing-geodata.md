# Task: Generate Missing Geographic Layers for cheias.pt QGIS Project

## Context

The QGIS project `cheias-scrollytelling.qgz` has 135 layers organized by scrollytelling chapter. Several datasets exist as non-geographic formats (JSON key-value stores, parquet without geometry) that need to become proper GeoJSON/GeoPackage files. We also need river polylines that don't exist yet.

**Rules:**
- Output all new vector layers as GeoJSON into `data/qgis/` (create the directory)
- Output all new raster layers as Cloud-Optimized GeoTIFF (COG) into `data/cog/` under appropriate subdirectories
- Upload ALL new COGs to R2 using: `rclone copy <local_path> r2:cheias-cog/<remote_path> --progress`
- CRS must be EPSG:4326 for all outputs
- Install any needed Python packages (`pip install pyarrow geopandas shapely --user`)
- Do NOT modify or delete any existing files

## R2 Bucket

- Remote: `r2:cheias-cog`
- Public URL pattern: `https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/{path}`
- Current contents: `cog/soil-moisture/*.tif` (77 files) + `cog/precipitation/*.tif` (77 files)
- Titiler endpoint: `https://titiler.cheias.pt/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png?url={encoded_r2_url}&colormap_name={cmap}&rescale={min},{max}`

## Datasets to Generate

### 1. Precondition Index — Basin GeoJSON (Ch7, Ch8)

**Source:** `data/frontend/precondition-basins.json` + `assets/basins.geojson`

The JSON has this structure:
```json
{
  "peak": {"date": "2026-02-05", "basins": {"Mondego": 0.91, "Tejo": 0.752, ...}},
  "pre_storm": {"date": "2026-01-25", "basins": {"Mondego": 0.288, "Tejo": 0.15, ...}}
}
```

**Action:** Join both `peak` and `pre_storm` values to basins.geojson by matching the `name` property. Output a single file with properties: `name`, `precondition_peak`, `precondition_peak_date`, `precondition_pre_storm`, `precondition_pre_storm_date`, `precondition_delta` (peak minus pre_storm).

**Output:** `data/qgis/precondition-basins.geojson`

### 2. Precondition Index — Point Grid Peak (Ch7, Ch8)

**Source:** `data/frontend/precondition-peak.json`

Structure: `{"date": "2026-02-05", "points": [{"lat": 36.75, "lon": -6.5, "index": 26.595, "risk_class": "red"}, ...]}`

256 points with lat, lon, index value, and risk_class (green/yellow/orange/red).

**Action:** Convert to GeoJSON point features with properties: `index`, `risk_class`, `date`.

**Output:** `data/qgis/precondition-peak-points.geojson`

### 3. Precondition Index — Temporal Point Grid COGs (Ch8)

**Source:** `data/frontend/precondition-frames.json`

Structure: array of 77 frames, each `{"date": "2025-12-01", "points": [{"lat", "lon", "index", "risk_class"}, ...]}`.

The point grid is regular (0.25° spacing). These should become raster COGs showing the precondition index evolving over time, same as the existing soil-moisture and precipitation COGs.

**Action:** For each of the 77 frames, interpolate the point grid to a raster covering Portugal (bounds: -9.75, 36.75, -6.0, 42.25) at 0.25° resolution. Save as COG with the same naming convention as existing COGs.

**Output:** `data/cog/precondition/{date}.tif` (77 files)
**Upload:** `rclone copy data/cog/precondition/ r2:cheias-cog/cog/precondition/ --progress`

### 4. IVT Peak Storm — Point GeoJSON (Ch2)

**Source:** `data/frontend/ivt-peak-storm.json`

Structure: `{"date": "2026-02-10", "points": [{"lat": 25.0, "lon": -45.0, "ivt": 22.2}, ...]}` — 1,102 points across the Atlantic.

**Action:** Convert to GeoJSON point features. These represent integrated vapor transport intensity on the peak storm date — the atmospheric river feeding moisture to Portugal.

**Output:** `data/qgis/ivt-peak-storm.geojson`

### 5. IVT Peak Storm — COG (Ch2)

**Source:** Same `ivt-peak-storm.json`

The IVT grid covers the Atlantic (approx 25°N–55°N, -45°W–5°E). Interpolate to a raster COG for use with titiler.

**Action:** Grid the 1,102 IVT points to a regular raster (0.25° or 0.5° resolution), save as COG.

**Output:** `data/cog/ivt/ivt-peak-2026-02-10.tif`
**Upload:** `rclone copy data/cog/ivt/ r2:cheias-cog/cog/ivt/ --progress`

### 6. Discharge Stations — Point GeoJSON with Timeseries Summary (Ch5)

**Source:** `data/frontend/discharge-timeseries.json`

Structure:
```json
{"stations": [
  {"name": "Tejo - Santarém", "basin": "Tejo", "lat": 39.24, "lon": -8.68,
   "timeseries": [{"date": "2025-12-01", "discharge": 245.3, "anomaly": 0.8}, ...]}
]}
```

11 stations, each with 77 daily values.

**Action:** Create GeoJSON points for the 11 stations. Properties should include: `name`, `basin`, `discharge_max` (peak value), `discharge_max_date`, `anomaly_max`, `discharge_mean`, `discharge_feb06` (Leonardo peak), `discharge_jan29` (Kristin peak). This gives QGIS something to style/label without the full timeseries.

**Output:** `data/qgis/discharge-stations.geojson`

### 7. Portuguese River Polylines (Ch5, Ch6a-c)

**Source:** Natural Earth 10m rivers+lake_centerlines, filtered to Portugal. Download from: `https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.zip`

If Natural Earth rivers are too coarse for the Portuguese basins, alternatively use the OpenStreetMap water features extract from Geofabrik: `https://download.geofabrik.de/europe/portugal-latest-free.shp.zip` (waterways layer).

**Action:**
1. Download Natural Earth 10m rivers
2. Clip to Portugal bounding box (-9.6, 36.9, -6.1, 42.2)
3. Filter to keep only the named rivers relevant to the narrative: Tejo, Douro, Mondego, Sado, Guadiana, Minho, Zêzere, Vouga, Lis (match on `name` field, case-insensitive, also try Portuguese variants: "Tagus" → "Tejo", "Duero" → "Douro")
4. If Natural Earth doesn't have enough of these rivers (it often only has major ones), fall back to Geofabrik Portugal waterways and filter to `waterway=river` with matching names

**Output:** `data/qgis/rivers-portugal.geojson`

### 8. Storm Precipitation Accumulation COGs (Ch4)

**Source:** `data/frontend/precip-storm-totals.json`

Structure: `{"points": [{"lat": 36.75, "lon": -9.75, "total_mm": 79.1}, ...]}` — 342 points with total precipitation accumulation across all storms.

**Action:** Interpolate to a raster COG covering Portugal. This is the "total damage" precipitation map — how much rain fell in total during the crisis period.

**Output:** `data/cog/precipitation/storm-total.tif`
**Upload:** `rclone copy data/cog/precipitation/storm-total.tif r2:cheias-cog/cog/precipitation/storm-total.tif --progress`

### 9. Soil Moisture Frames — Temporal Point GeoJSON (Ch3, for QGIS inspection)

**Source:** `data/frontend/soil-moisture-frames.json`

Structure: 77 frames, each `{"date": "...", "points": [{"lat", "lon", "value"}, ...]}`.

We already have COGs for these (the 77 soil-moisture/*.tif files). But for QGIS point-level inspection, generate a single GeoJSON with ALL points from the peak frame (Jan 31).

**Action:** Extract the frame for `2026-01-31`, convert to GeoJSON points with `value` and `date` properties.

**Output:** `data/qgis/soil-moisture-peak-points.geojson`

## Verification Steps

After generating all files, run these checks:

1. **File existence:** Confirm all 9 outputs exist and have non-zero size
2. **GeoJSON validity:** `ogrinfo -al <file> | head -20` for each GeoJSON
3. **COG validity:** `gdalinfo <file> | head -20` for each new COG — confirm "LAYOUT=COG" in metadata
4. **R2 upload verification:** `rclone ls r2:cheias-cog/cog/precondition/ | wc -l` should be 77; `rclone ls r2:cheias-cog/cog/ivt/` should show the IVT COG; check storm-total.tif is uploaded
5. **Titiler test:** `curl -s "https://titiler.cheias.pt/cog/info?url=https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/precondition/2026-01-31.tif"` should return valid bounds

## Summary of Expected Outputs

| # | File | Type | Layers |
|---|------|------|--------|
| 1 | `data/qgis/precondition-basins.geojson` | Polygon | 11 basins with precondition scores |
| 2 | `data/qgis/precondition-peak-points.geojson` | Point | 256 points with risk index |
| 3 | `data/cog/precondition/*.tif` (77) | COG | Daily precondition rasters → R2 |
| 4 | `data/qgis/ivt-peak-storm.geojson` | Point | 1,102 Atlantic IVT points |
| 5 | `data/cog/ivt/ivt-peak-2026-02-10.tif` | COG | IVT raster → R2 |
| 6 | `data/qgis/discharge-stations.geojson` | Point | 11 river gauge stations |
| 7 | `data/qgis/rivers-portugal.geojson` | Line | Portuguese river network |
| 8 | `data/cog/precipitation/storm-total.tif` | COG | Total storm precip → R2 |
| 9 | `data/qgis/soil-moisture-peak-points.geojson` | Point | SM peak frame as points |

Working directory: `~/Documents/dev/cheias-pt/`
