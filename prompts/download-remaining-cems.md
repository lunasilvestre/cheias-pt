# Task: Download Remaining CEMS AOIs

## Context

We have 5 AOIs downloaded (EMSR861 AOI05, EMSR864 AOI01-03). Both activations have many more:
- **EMSR861** (Storm Kristin): 27 AOIs, 72 products — we only have AOI05 (Coimbra)
- **EMSR864** (Storm Leonardo): 18 AOIs, 46 products — we have AOI01-03

The portal is at:
- https://rapidmapping.emergency.copernicus.eu/EMSR861
- https://rapidmapping.emergency.copernicus.eu/EMSR864

## What to do

1. **Scrape both activation pages** to get the full list of AOIs and their download URLs. The pattern is:
   ```
   https://rapidmapping.emergency.copernicus.eu/backend/EMSR{id}/AOI{nn}/DEL_PRODUCT/EMSR{id}_AOI{nn}_DEL_PRODUCT_v1.zip
   ```
   Also check for monitoring products (DEL_MONIT01, DEL_MONIT02, etc.) on any AOI.

2. **Filter to Portugal-only AOIs** — some AOIs in both activations cover Spain. We want Portuguese ones only. Check the locality/country in the activation page metadata.

3. **Download all Portuguese DEL_PRODUCT ZIPs** to `data/flood-extent/`. Skip AOIs we already have (AOI05 for EMSR861, AOI01-03 for EMSR864).

4. **Process identically** to the existing data — extract `observedEventA` shapefiles, convert to GeoJSON, enrich with metadata (activation, AOI, locality, source_date, sensor, product_type, storm).

5. **Rebuild the merged files:**
   - `data/flood-extent/emsr861.geojson` — ALL EMSR861 Portuguese flood polygons
   - `data/flood-extent/emsr864.geojson` — ALL EMSR864 Portuguese flood polygons
   - `data/flood-extent/combined.geojson` — both merged

6. **Rebuild PMTiles** using the same tippecanoe settings from the existing processing:
   ```bash
   tippecanoe -o combined.pmtiles -Z4 -z14 --drop-densest-as-needed --extend-zooms-if-still-dropping -l flood-extent combined.geojson
   tippecanoe -o emsr861.pmtiles -Z4 -z14 --drop-densest-as-needed --extend-zooms-if-still-dropping -l flood-extent emsr861.geojson
   tippecanoe -o emsr864.pmtiles -Z4 -z14 --drop-densest-as-needed --extend-zooms-if-still-dropping -l flood-extent emsr864.geojson
   ```

7. **Don't touch** the Salvaterra temporal files (salvaterra_2026-02-06/07/08.geojson, salvaterra_temporal.pmtiles) — those are already perfect.

8. **Update README.md** with the new AOI table and total area.

## Why now

The story has a short shelf life and the national picture for Chapter 7 benefits from full coverage. This is a ~30 minute download + processing task.
