# Task: Process CEMS Flood Extent ZIPs → GeoJSON

## Context

We downloaded Copernicus EMS rapid mapping products for Portugal's Jan-Feb 2026 floods. These are flood delineation shapefiles from two activations:

- **EMSR861** — Storm Kristin (Jan 26+), central Portugal (Coimbra, Leiria, Médio Tejo)
- **EMSR864** — Storm Leonardo/Marta (Feb 3+), broader flooding (Tejo, Sado, multiple basins)

The ZIPs are in `data/flood-extent/`. Each ZIP contains shapefiles with flood extent polygons derived from satellite imagery (mostly Sentinel-1 SAR).

## What to do

1. **List all ZIPs** in `data/flood-extent/` and inspect their contents (unzip -l). Identify which contain shapefiles (.shp + .shx + .dbf + .prj).

2. **Extract and convert** each activation's flood delineation shapefiles to GeoJSON using ogr2ogr or geopandas. Key details:
   - Look for files with `DELINEATION` or `observed_event` in the name — these are the actual flood extent polygons (not reference maps or grading maps)
   - Each AOI (Area of Interest) has its own shapefile. Preserve the AOI identifier.
   - Reproject to EPSG:4326 (WGS84) if not already
   - Preserve all attributes (especially: area_ha, event_date, source_date, sensor, aoi_name)

3. **Merge per activation:**
   - `data/flood-extent/emsr861.geojson` — all EMSR861 flood polygons
   - `data/flood-extent/emsr864.geojson` — all EMSR864 flood polygons

4. **Create combined file:**
   - `data/flood-extent/combined.geojson` — both activations merged
   - Add a property `activation` ("EMSR861" or "EMSR864") to each feature

5. **Generate summary** — print a table:
   - Per AOI: name, activation, number of polygons, total flooded area (ha), source date, sensor used
   - Highlight the largest AOIs (likely AOI03 Salvaterra de Magos in the Tejo basin)

6. **Save a README** at `data/flood-extent/README.md` documenting:
   - Source URLs for each activation
   - Processing steps performed
   - Output files and their contents
   - Key findings (total flooded area, major AOIs)

## Dependencies

Use geopandas + fiona (should be installed). Fall back to ogr2ogr if available. Install what's needed.

## Important

- Some ZIPs may have nested folders or multiple product types (FIRST, DELINEATION, GRADING). We only want DELINEATION products.
- If there are multiple temporal observations per AOI (monitoring products), keep all of them with their dates.
- Don't simplify geometries — we need full resolution for the scrollytelling map.
