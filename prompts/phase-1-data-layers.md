# Phase 1: Data Layers — Cloud-Native Rendering + Missing Imagery

## Mission

Wire the scroll narrative to live data. Phase 0 built the scroll engine with empty chapters.
Phase 1 makes data appear on the map — COGs rendered client-side with dynamic colormaps,
Sentinel-2 imagery fetched via STAC, missing satellite coverage acquired, and flood depth
extracted from raw CEMS archives.

**The portfolio signal:** A DevSeed engineer reviewing cheias.pt should see COGs loaded from
R2 with client-side colormapping, STAC-based data discovery, and dynamic rendering — not
pre-rendered PNGs from Python scripts. The cloud-native pipeline IS the demonstration of skill.

## What Changed From the v2 Plan's Phase 1

The v2 plan prescribed 6 tasks, half of which were Python batch-rendering PNGs from COGs.
That was v0 thinking carried forward. With Vite + deck.gl + WeatherLayers GL now working
(proven in Phase 0), we render COGs client-side. This eliminates Tasks 1.1 and 1.2 as
written and replaces them with client-side rendering integration.

| v2 Plan Task | Verdict | Replacement |
|-------------|---------|-------------|
| 1.1 Pre-render precip PNGs (blues + blur) | **ELIMINATED** | Client-side COG colormap in `layer-manager.ts` |
| 1.2 Pre-render satellite IR PNGs | **ELIMINATED** | Client-side COG rendering with inverted grayscale LUT |
| 1.3 Fetch extended Meteosat | **KEPT** — data doesn't exist yet | Same |
| 1.4 Fetch Sentinel-2 before/after | **KEPT + UPGRADED** — STAC showcase | Proper STAC search pipeline |
| 1.5 Draw frontal boundary GeoJSONs | **KEPT** — domain expertise | Same |
| 1.6 Extract flood depth rasters | **KEPT + UPGRADED** — COG output | COG with overviews, not raw TIF |

The new tasks 1.1–1.3 build the client-side rendering pipeline that replaces batch PNG
generation. This is where the geospatial mastery lives.

## Architecture Constraints (non-negotiable)

From `CLAUDE.md` — plus Phase 1 specifics:

- **All scripts run in the project venv.** `source .venv/bin/activate`. NEVER `--break-system-packages`.
- **Frontend code changes are IN SCOPE for this phase.** Phase 1 now includes wiring data
  to the map. Changes to `src/data-loader.ts`, `src/layer-manager.ts`, `src/map-setup.ts`,
  and `src/chapters.ts` are expected. Changes to scroll logic or animations are NOT (Phase 2).
- **COGs on R2 are the rendering source.** Client loads COGs directly via HTTP range requests.
  No titiler for scroll-driven layers. titiler.cheias.pt remains available for Sentinel-2
  tile serving if needed.
- **Commit the script, not the data.** Fetched imagery (Meteosat, Sentinel-2) is gitignored.
  Processing scripts are committed.
- **Branch:** `v2/phase-1` off `main`. Merge after all acceptance criteria pass.

## Existing Infrastructure

| File | Relevance |
|------|-----------|
| `src/data-loader.ts` | Currently a skeleton. Will become the COG loading + colormap pipeline. |
| `src/layer-manager.ts` | Currently handles basic layer visibility. Will manage deck.gl BitmapLayer rendering from decoded COGs. |
| `src/chapters.ts` | Chapter configs with camera positions. Will get `layers` arrays specifying which data to load per chapter. |
| `src/types.ts` | Shared interfaces. Will get `RasterFrame`, `LayerConfig`, `ChapterData` types. |
| `scripts/rerender-pngs.py` | Existing COG→PNG renderer. **Reference only** — we're replacing this pattern with client-side rendering. Keep the colormaps as design reference. |
| `scripts/fetch_eumetsat.py` | Meteosat fetch pipeline. Used directly in Task 1.5. |
| `data/cog/` | All existing COGs on R2. These become the rendering source. |
| `data/raster-frames/soil-moisture/*.png` | 77 PNGs at 9/10 readiness. **Keep as-is.** SM crossfade animation may stay PNG-based (proven pattern, low risk). |
| `data/frontend/raster-manifest.json` | Frame URLs for existing PNG animation. Will be extended for COG-based rendering. |

## Tasks and Acceptance Criteria

---

### Task 1.1: COG → BitmapLayer Rendering Pipeline

**The core skill demonstration.** Build the client-side pipeline that loads a COG from R2,
decodes it with geotiff.js, applies a colormap, and renders it as a deck.gl BitmapLayer.
This replaces all Python PNG pre-rendering with a single TypeScript module.

**Do:**

In `src/data-loader.ts`:

1. **`loadCOG(url: string): Promise<DecodedRaster>`** — Fetch a COG from R2 via geotiff.js.
   Use HTTP range requests (geotiff.js does this automatically for COGs). Return the raw
   Float32Array + dimensions + bounds + nodata value.

2. **`applyColormap(raster: DecodedRaster, config: ColormapConfig): ImageData`** — Apply a
   colormap to decoded raster data. Colormaps defined as lookup tables:
   - `precipitation-blues`: transparent→pale blue→sky blue→deep blue→near-black blue. Alpha proportional to value.
   - `satellite-ir-enhanced`: inverted grayscale with contrast stretch (cold clouds=white, warm surface=dark).
   - `soil-moisture-browns`: existing brown→blue colormap from `rerender-pngs.py` (ported to TS).
   - `sst-diverging`: blue-white-red for SST anomaly.
   - `ivt-moisture`: transparent→blue→purple→white for integrated vapor transport.
   - `mslp-pressure`: blue-white-red diverging for mean sea level pressure.

3. **`rasterToImageBitmap(imageData: ImageData): Promise<ImageBitmap>`** — Convert to ImageBitmap
   for deck.gl BitmapLayer consumption.

In `src/layer-manager.ts`:

4. **`createRasterLayer(id: string, imageBitmap: ImageBitmap, bounds: BBox): BitmapLayer`** —
   Create a deck.gl BitmapLayer positioned at the COG's geographic bounds. Opacity
   controllable for crossfade.

5. **Dual-buffer crossfade** for temporal animation: maintain two BitmapLayers (A/B). On
   frame advance, load next COG into inactive buffer, crossfade opacity. Same pattern as
   the v0 prototype's `rasterBuf` but now with COGs instead of PNGs.

**The gaussian blur question:** For precipitation, apply `sigma=3` gaussian blur to the
decoded Float32Array BEFORE colormapping. This is a simple 2D convolution on ~200×300
pixels — trivial in JS/TS. Use a separable gaussian kernel:
```typescript
function gaussianBlur(data: Float32Array, width: number, height: number, sigma: number): Float32Array
```
This keeps the "soft watercolor" aesthetic without pre-rendering PNGs.

**Do NOT:**
- Use WeatherLayers GL for this task — that's Task 1.2
- Wire to scroll events — that's Phase 2
- Change the scroll engine or chapter transitions

**Files changed:**
- `src/data-loader.ts` — complete rewrite (COG loading, colormap application, blur)
- `src/layer-manager.ts` — add BitmapLayer creation and crossfade
- `src/types.ts` — add `DecodedRaster`, `ColormapConfig`, `BBox` interfaces

**Acceptance criteria:**
- [ ] In the browser console, `loadCOG('https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/precipitation/2026-01-28.tif')` returns decoded raster data
- [ ] Precipitation COG renders as BitmapLayer with blue colormap (not yellow/red)
- [ ] Precipitation rendering shows soft blurred edges (gaussian blur applied)
- [ ] Light rain areas are more transparent than heavy rain areas (alpha ∝ value)
- [ ] Satellite IR COG (`data/cog/satellite-ir/20260127T18-00.tif`) renders with inverted grayscale — bright white comma cloud visible
- [ ] SST anomaly COG renders with blue-white-red diverging colormap
- [ ] Two raster layers can crossfade (A fades out while B fades in, 300ms)
- [ ] `npm run build` passes with zero TypeScript errors
- [ ] No `python`, no `PIL`, no `matplotlib` involved in the rendering path

**Commit:** `phase-1.1: client-side COG rendering pipeline with dynamic colormaps`

---

### Task 1.2: WeatherLayers GL Integration — Particles + Contours from COGs

**The wow-factor task.** Wire WeatherLayers GL layers to existing wind U/V and MSLP COGs
on R2. This single integration replaces what v1 estimated as 5+ days of custom code:
wind particle system, MSLP contour generation, wind barb rendering, H/L pressure tracking.

**Do:**

Create `src/weather-layers.ts`:

1. **Install and configure WeatherLayers GL:**
   ```typescript
   import { ParticleLayer, ContourLayer, GridLayer, HighLowLayer } from 'weatherlayers-gl';
   ```
   Pin to the deck.gl 9.2 compatible version. Check `weatherlayers-gl` changelog for
   exact version range.

2. **Wind particles from U/V COGs:**
   ```typescript
   const windParticles = new ParticleLayer({
     id: 'wind-particles',
     image: windGeoTiff,        // geotiff.js decoded from R2 COG
     imageType: 'VECTOR',
     numParticles: 5000,
     maxAge: 100,
     speedFactor: 0.5,
     width: 2,
     color: [255, 255, 255, 200],
     animate: true,
   });
   ```
   Load wind U/V COG pair for a single timestep (e.g., Jan 28 06Z — Kristin peak).
   Verify particles flow correctly through the wind field.

3. **MSLP isobars from MSLP COG:**
   ```typescript
   const isobars = new ContourLayer({
     id: 'mslp-isobars',
     image: mslpGeoTiff,
     imageType: 'SCALAR',
     interval: 400,             // 4 hPa in Pa
     width: 1.5,
     color: [255, 255, 255, 220],
   });
   ```
   Load MSLP COG for same timestep. Verify isobars appear at correct pressure values.

4. **H/L pressure labels:**
   ```typescript
   const pressureCenters = new HighLowLayer({
     id: 'pressure-hl',
     image: mslpGeoTiff,
     imageType: 'SCALAR',
     radius: 500000,
   });
   ```

5. **Wind barbs (GridLayer):**
   ```typescript
   const windBarbs = new GridLayer({
     id: 'wind-barbs',
     image: windGeoTiff,
     imageType: 'VECTOR',
     style: 'WIND_BARB',
     density: 32,
     color: [255, 255, 255, 180],
   });
   ```

6. **Wire all layers to the deck.gl MapboxOverlay** that Phase 0 already initialized.

**The test:** Load a single timestep (Jan 28 06Z) and visually verify:
- Wind particles streaming through the cyclone
- MSLP isobars forming concentric rings around the low
- H/L markers at pressure extrema
- Wind barbs showing proper meteorological notation

This is the synoptic chart that the effect audit said was "furthest from implementation."
WeatherLayers GL collapses it to 4 layer declarations.

**Do NOT:**
- Animate across timesteps (Phase 2)
- Wire to scroll events (Phase 2)
- Build a custom particle system (WeatherLayers GL replaces it)
- Generate contour GeoJSON with d3-contour (WeatherLayers GL replaces it)

**Files changed:**
- `src/weather-layers.ts` — new module
- `src/map-setup.ts` — import and register WeatherLayers GL layers on MapboxOverlay
- `package.json` — verify `weatherlayers-gl` version pinning

**Acceptance criteria:**
- [ ] Wind particles visibly flow through the wind field at Jan 28 06Z
- [ ] Particles show comet-tail trail effect (built-in to ParticleLayer)
- [ ] MSLP isobars render as white concentric lines around the low pressure center
- [ ] Isobar values are physically plausible (960-1030 hPa range for Kristin)
- [ ] H/L markers appear — "L" near the cyclone center, "H" over the Azores high
- [ ] Wind barbs show proper meteorological notation (flags, not just arrows)
- [ ] All 4 layers render simultaneously without WebGL errors
- [ ] Particle animation runs at 30+ fps on a mid-range GPU
- [ ] `npm run build` passes with zero TypeScript errors

**Commit:** `phase-1.2: WeatherLayers GL integration — particles, isobars, H/L, wind barbs`

---

### Task 1.3: Chapter-Data Wiring — First Visible Layers

**Make the scroll narrative show data.** Phase 0's chapters trigger camera moves but display
no data layers. This task wires the first visible layers to chapter enter/exit events,
proving the full pipeline: scroll → chapter config → data load → layer render.

**Do:**

In `src/chapters.ts`, add `layers` configuration to at least 4 chapters:

1. **Ch.1 (Hook):** Flood extent from `combined.pmtiles` — dark blue fill at 30% opacity
   pulsing to visible on scroll entry. PMTiles loaded via MapLibre vector source (already
   supported). This is the "ghost flood pulse" from the creative direction.

2. **Ch.3 (Soil Saturation):** Soil moisture raster — either from existing PNGs
   (crossfade per scroll step) OR from COG via the new Task 1.1 pipeline. Use whichever
   is more performant. The 77-frame sequence driven by `onStepProgress(0→1)`.

3. **Ch.4 (Storms):** Wind particles + MSLP isobars from Task 1.2, loaded for a single
   timestep (Kristin peak). Static for now — temporal scrubbing comes in Phase 2.

4. **Ch.5 (Rivers):** Discharge stations from `data/qgis/discharge-stations.geojson` as
   deck.gl ScatterplotLayer, rivers from `data/qgis/rivers-portugal.geojson` as MapLibre
   line layer. Static markers, no animation yet.

In `src/scroll-engine.ts`, wire `onStepEnter` to call `layer-manager.ts` functions that
show/hide the appropriate layers per chapter. Use opacity transitions (GSAP or
requestAnimationFrame) for smooth enter/exit.

**Do NOT:**
- Build the complete layer stack for every chapter (Phase 2)
- Implement temporal animation across timesteps (Phase 2)
- Add WeatherLayers GL FrontLayer (Phase 2 — needs Task 1.7 GeoJSON first)
- Add 3D columns, terrain, or globe projection (Phase 2)
- Modify Portuguese narrative text

**Files changed:**
- `src/chapters.ts` — add `layers` config arrays to 4+ chapters
- `src/scroll-engine.ts` — wire `onStepEnter`/`onStepExit` to layer visibility
- `src/layer-manager.ts` — add show/hide/crossfade functions per layer type
- `src/map-setup.ts` — add PMTiles source for flood extent, GeoJSON sources

**Acceptance criteria:**
- [ ] Scrolling to Ch.1 shows flood extent polygons fading in over the dark basemap
- [ ] Scrolling to Ch.3 shows soil moisture raster (blue/brown hues over Portugal)
- [ ] Scrolling to Ch.4 shows wind particles + isobars (synoptic view)
- [ ] Scrolling to Ch.5 shows river network + discharge station markers
- [ ] Scrolling AWAY from a chapter fades its layers out (opacity → 0)
- [ ] No layers visible between chapters (clean transitions)
- [ ] Camera transitions still work as Phase 0 established
- [ ] No jank during scroll — layer loads don't block the main thread
- [ ] `npm run build` passes with zero TypeScript errors

**Commit:** `phase-1.3: wire first data layers to scroll chapters`

---

### Task 1.4: Sentinel-2 Before/After via STAC

**The STAC showcase.** Fetch Sentinel-2 imagery through proper cloud-native patterns —
STAC catalog search, scene selection, COG access. This demonstrates the exact workflow
DevSeed builds tools for (eoAPI, stac-map, Earth Search).

**Do:**

Create `scripts/fetch_sentinel2_stac.py`:

1. **Search Earth Search STAC** (`https://earth-search.aws.element84.com/v1`):
   ```python
   from pystac_client import Client

   catalog = Client.open("https://earth-search.aws.element84.com/v1")
   search = catalog.search(
       collections=["sentinel-2-l2a"],
       bbox=[-9.16, 38.65, -8.05, 39.48],  # Salvaterra extent
       datetime="2026-01-01/2026-01-25",     # Before storms
       query={"eo:cloud_cover": {"lt": 15}},
       sortby=[{"field": "eo:cloud_cover", "direction": "asc"}],
       max_items=5,
   )
   ```
   This is the DevSeed-native STAC endpoint (Element 84, AWS). Demonstrate proper
   `pystac_client` usage — not raw HTTP requests.

2. **Select optimal scenes** — before (clearest Jan 2026) and after (closest to Feb 7-8
   flood peak, cloud cover < 30%).

3. **Access COGs directly from S3** — Sentinel-2 on Earth Search is already COG.
   Read bands B04 (Red), B03 (Green), B02 (Blue) using rasterio with `GDAL_DISABLE_READDIR_ON_OPEN=EMPTY`
   and `AWS_NO_SIGN_REQUEST=YES` for unsigned access. Clip to Salvaterra bbox.

4. **Output as Cloud-Optimized GeoTIFF** with internal tiling + overviews:
   ```python
   # Write with rasterio COG profile
   profile.update(driver='GTiff', tiled=True, compress='deflate',
                  blockxsize=256, blockysize=256)
   # Build overviews
   ds.build_overviews([2, 4, 8, 16], Resampling.average)
   ds.update_tags(ns='rio_overview', resampling='average')
   ```

5. **Generate STAC-format metadata** for each scene (not a custom JSON manifest):
   ```python
   # Output a mini STAC item for each scene
   {
     "type": "Feature",
     "stac_version": "1.0.0",
     "id": "salvaterra-before-20260115",
     "properties": {
       "datetime": "2026-01-15T11:06:23Z",
       "eo:cloud_cover": 4.2,
       "sentinel:product_id": "...",
       "processing:software": {"cheias.pt": "2.0.0"}
     },
     "assets": {
       "visual": {"href": "data/sentinel-2/salvaterra-before-20260115.tif", "type": "image/tiff; application=geotiff; profile=cloud-optimized"}
     }
   }
   ```

6. **JPEG preview** for quick QA.

**Output:**
- `data/sentinel-2/` directory (new)
- 2 COGs (before + after) with overviews
- 2 STAC Item JSONs
- 2 JPEG previews
- `data/sentinel-2/README.md` documenting the STAC search parameters and scene selection

**Files changed:**
- `scripts/fetch_sentinel2_stac.py` — new script

**Acceptance criteria:**
- [ ] Script uses `pystac_client` for STAC search (not raw HTTP)
- [ ] Earth Search STAC endpoint is the data source (DevSeed-aligned)
- [ ] Before scene: COG exists, RGB, EPSG:4326, date Jan 2026, cloud cover < 15%
- [ ] After scene: COG exists, RGB, EPSG:4326, date Feb 2026, cloud cover < 30%
- [ ] Both COGs are Cloud-Optimized (internal tiles 256×256, overviews, deflate compression)
- [ ] STAC Item JSON follows 1.0.0 spec for each scene
- [ ] `gdalinfo` on each COG shows `LAYOUT=COG` in metadata
- [ ] JPEG previews show visible difference — after scene has blue/dark flood water where before had fields
- [ ] `.gitignore` covers `data/sentinel-2/*.tif`, `*.jpg`

**Commit:** `phase-1.4: fetch Sentinel-2 before/after via Earth Search STAC`

---

### Task 1.5: Fetch Extended Meteosat Imagery (Leonardo + Marta)

**Problem:** Satellite IR COGs cover only Storm Kristin (Jan 27-28, 49 COGs). Storms
Leonardo (Feb 5-7) and Marta (Feb 10-11) have no satellite imagery. Chapter 4 needs all
three storms.

**Do:**

Run `scripts/fetch_eumetsat.py` with extended date ranges:
```bash
source .venv/bin/activate

# Leonardo approach + landfall
python scripts/fetch_eumetsat.py --start 2026-02-04T00 --end 2026-02-08T00 --interval 1

# Marta approach + landfall
python scripts/fetch_eumetsat.py --start 2026-02-09T00 --end 2026-02-12T00 --interval 1
```

If the script needs modifications (hardcoded dates, collection changes), update it.
If EUMETSAT credentials have expired, document the failure and move on — this task has
a graceful degradation path (Kristin-only satellite in the narrative).

After fetching, verify new COGs render correctly through the Task 1.1 pipeline
(client-side inverted grayscale colormap).

**Output:**
- ~96 additional COGs in `data/cog/satellite-ir/`

**Files changed:**
- `scripts/fetch_eumetsat.py` — modified if needed

**Acceptance criteria:**
- [ ] `data/cog/satellite-ir/` contains COGs for Feb 4-8 AND Feb 9-12 (or documented failure)
- [ ] New COGs are valid GeoTIFF (`rasterio.open()` succeeds)
- [ ] New COGs render through the Task 1.1 pipeline with inverted grayscale colormap
- [ ] Visual: Leonardo storm (Feb 5-6) shows cyclone structure
- [ ] Visual: Marta storm (Feb 10-11) shows cyclone structure
- [ ] If fetch failed: `data/cog/satellite-ir/FETCH-STATUS.md` documents what happened

**Commit:** `phase-1.5: fetch extended Meteosat IR for Leonardo and Marta storms`

---

### Task 1.6: Extract Flood Depth COGs from CEMS Salvaterra

**Problem:** CEMS rapid mapping for the Tejo/Salvaterra area (EMSR864 AOI03) contains
`floodDepthA` rasters with modelled water depth 0-9.6m. They're buried in deliverable
archives. Need extraction + conversion to proper COGs for client-side rendering.

**Current state confirmed:**
```
EMSR864_AOI03_DEL_MONIT01_v2  →  depth 0-7.8m, 659K valid pixels
EMSR864_AOI03_DEL_MONIT02_v1  →  depth 0-9.3m, 688K valid pixels
EMSR864_AOI03_DEL_PRODUCT_v1  →  depth 0-9.6m, 596K valid pixels
```
All EPSG:4326, float32, nodata=-9999.

**Do:**

Create `scripts/extract_flood_depth.py`:

1. **Extract the 3 monitoring-date depth TIFs** and convert to proper Cloud-Optimized
   GeoTIFF with internal tiling + overviews:
   ```python
   # Read source, write COG
   with rasterio.open(src_path) as src:
       profile = src.profile.copy()
       profile.update(driver='GTiff', tiled=True, compress='deflate',
                      blockxsize=256, blockysize=256)
       # ... write + build overviews
   ```

2. **Clip to Salvaterra temporal extent** (bbox from `salvaterra_2026-02-06.geojson`).

3. **Output with metadata:**
   - `data/flood-depth/salvaterra-depth-monit01.tif` (COG, float32, depths in meters)
   - `data/flood-depth/salvaterra-depth-monit02.tif`
   - `data/flood-depth/salvaterra-depth-product.tif`
   - `data/flood-depth/manifest.json` with per-file statistics and CEMS attribution

4. **Define a depth colormap** in the manifest that the client-side renderer (Task 1.1) can use:
   ```json
   "colormap": "flood-depth",
   "domain": [0, 7],
   "colors": ["#deebf7", "#9ecae1", "#4292c6", "#2171b5", "#084594", "#8b0000"]
   ```

**Output:**
- `data/flood-depth/` directory (new)
- 3 COGs + `manifest.json`

**Files changed:**
- `scripts/extract_flood_depth.py` — new script

**Acceptance criteria:**
- [ ] 3 COGs in `data/flood-depth/`, each valid Cloud-Optimized GeoTIFF
- [ ] `gdalinfo` shows `LAYOUT=COG`, float32 dtype, EPSG:4326
- [ ] Max depth values are physically plausible (1-10m)
- [ ] COGs render through the Task 1.1 pipeline with the depth colormap
- [ ] `manifest.json` documents each file with max/mean depth, flooded area, and CEMS attribution
- [ ] `.gitignore` covers `data/flood-depth/*.tif`

**Commit:** `phase-1.6: extract flood depth COGs from CEMS Salvaterra deliverables`

---

### Task 1.7: Frontal Boundary GeoJSONs

**Problem:** WeatherLayers GL `FrontLayer` (Phase 2) needs GeoJSON LineString input for
frontal positions. These require meteorological judgment — can't be automated.

**Do:**

Create `scripts/analyze_frontal_positions.py` that loads ECMWF HRES COGs at 0.1° and
prints diagnostic information (MSLP min/max, wind direction at key transects) to guide
manual front placement.

Create `data/qgis/frontal-boundaries.geojson` with 4 LineString features:

| Front | Storm | Timestep | Type |
|-------|-------|----------|------|
| Kristin trailing cold front (approaching) | Kristin | 2026-01-28T00Z | cold |
| Kristin trailing cold front (passed) | Kristin | 2026-01-28T12Z | cold |
| Leonardo warm front (advancing) | Leonardo | 2026-02-05T12Z | warm |
| Marta trailing cold front | Marta | 2026-02-10T06Z | cold |

Each feature: `front_type`, `storm`, `datetime`, `label` (Portuguese).

**This GeoJSON is a small hand-curated analytical product** (<10KB). Commit it to git
(like `storm-tracks.geojson`).

**Files changed:**
- `scripts/analyze_frontal_positions.py` — new diagnostic script
- `data/qgis/frontal-boundaries.geojson` — new (committed, not gitignored)

**Acceptance criteria:**
- [ ] Valid GeoJSON with 4 LineString features
- [ ] Each feature has `front_type`, `storm`, `datetime`, `label` properties
- [ ] Cold fronts trail SW→NE from low center (meteorologically plausible)
- [ ] Warm fronts extend ahead of warm sector
- [ ] `analyze_frontal_positions.py` prints MSLP/wind diagnostics for guidance
- [ ] LineStrings span the narrative domain (-15°W to 0°E, 34°N to 46°N)

**Commit:** `phase-1.7: frontal boundary GeoJSONs for 3 storms`

---

## What NOT to Do

- Do NOT pre-render precipitation PNGs with Python — colormaps are applied client-side
- Do NOT pre-render satellite IR PNGs with Python — same, client-side
- Do NOT generate temporal MSLP contour GeoJSONs — WeatherLayers GL ContourLayer
- Do NOT generate temporal wind barbs GeoJSONs — WeatherLayers GL GridLayer
- Do NOT generate temporal L/H marker positions — WeatherLayers GL HighLowLayer
- Do NOT convert IVT to TripsLayer waypoints — scalar field rendering in Phase 2
- Do NOT push data to R2 — after Phase 2 validates
- Do NOT modify soil-moisture PNGs (9/10 readiness)
- Do NOT build temporal scroll animation (Phase 2)
- Do NOT add globe projection, terrain, or 3D columns (Phase 2)
- Do NOT add the maplibre-gl-compare before/after slider (Phase 3)
- Do NOT refactor Portuguese narrative text

## Verification Commands

```bash
cd /home/nls/Documents/dev/cheias-pt

echo "=== Build ==="
npm run build && echo "BUILD OK" || echo "BUILD FAILED"

echo "=== Task 1.1: COG Rendering ==="
# Manual browser test: open dev server, check console for COG load success
npm run dev  # then verify in browser

echo "=== Task 1.2: WeatherLayers GL ==="
# Manual browser test: verify wind particles + isobars render

echo "=== Task 1.3: Chapter Wiring ==="
# Manual scroll test: scroll through all chapters, verify layer visibility

echo "=== Task 1.4: Sentinel-2 ==="
source .venv/bin/activate
ls data/sentinel-2/*.tif 2>/dev/null | wc -l  # expect 2
python3 -c "
import rasterio
for f in ['data/sentinel-2/salvaterra-before-*.tif', 'data/sentinel-2/salvaterra-after-*.tif']:
    import glob
    for path in glob.glob(f):
        with rasterio.open(path) as ds:
            print(f'{path}: {ds.width}x{ds.height}, CRS={ds.crs}, bands={ds.count}')
"

echo "=== Task 1.5: Extended Meteosat ==="
ls data/cog/satellite-ir/*.tif | wc -l  # expect 145+

echo "=== Task 1.6: Flood Depth ==="
ls data/flood-depth/*.tif 2>/dev/null | wc -l  # expect 3
python3 -c "
import json; m=json.load(open('data/flood-depth/manifest.json'))
for d in m['depths']:
    print(f'{d[\"monitoring\"]}: max={d[\"max_depth_m\"]}m, area={d[\"flooded_area_ha\"]}ha')
"

echo "=== Task 1.7: Frontal Boundaries ==="
python3 -c "
import json
gj = json.load(open('data/qgis/frontal-boundaries.geojson'))
for f in gj['features']:
    p = f['properties']
    print(f'{p[\"storm\"]} {p[\"front_type\"]} @ {p[\"datetime\"]}')
"
```

## Files to Read First (in order)

1. `src/data-loader.ts` — understand current skeleton (Task 1.1 rewrites this)
2. `src/layer-manager.ts` — understand current layer management (Tasks 1.1-1.3 extend this)
3. `src/chapters.ts` — understand chapter configs you're wiring data into (Task 1.3)
4. `deckgl-prototype.html` — extract the COG→BitmapLayer pattern (lines ~400-500) as reference
5. `scripts/rerender-pngs.py` — colormap definitions to PORT to TypeScript (Task 1.1)
6. `scripts/fetch_eumetsat.py` — Meteosat fetch pipeline (Task 1.5)
7. `prompts/creative-direction-plan-v2.md` §3 — WeatherLayers GL integration spec (Task 1.2)

---

## Context Anchors for Multi-Session Agents

### Lead Context Prompt (paste at session start)

```
I'm working on cheias.pt Phase 1 — data layers. Before doing anything:

1. Read `CLAUDE.md` for project rules (git, venv, architecture)
2. Read `prompts/phase-1-data-layers.md` for the task I'm working on
3. Read `prompts/creative-direction-plan-v2.md` §3 (Effect Resolution)

Key Phase 1 principles:
- COGs are rendered CLIENT-SIDE with dynamic colormaps. No Python PNG pre-rendering.
- WeatherLayers GL handles particles, isobars, wind barbs, H/L markers from COGs.
- STAC-based data access patterns (Earth Search for Sentinel-2).
- All COG outputs must be Cloud-Optimized (internal tiling, overviews, deflate).
- Frontend code changes ARE in scope (src/data-loader.ts, src/layer-manager.ts).
- Temporal scroll animation is NOT in scope (Phase 2).

Current task: [TASK NUMBER AND NAME]
```

### Per-Task Quick Reference

| Task | Type | Key Input | Key Output | Core Skill Demonstrated |
|------|------|-----------|------------|------------------------|
| 1.1 | Frontend | COGs on R2 | `src/data-loader.ts` + `src/layer-manager.ts` | Cloud-native COG rendering, dynamic colormaps |
| 1.2 | Frontend | Wind/MSLP COGs on R2 | `src/weather-layers.ts` | WeatherLayers GL, synoptic chart composition |
| 1.3 | Frontend | Tasks 1.1 + 1.2 outputs | `src/chapters.ts` layer wiring | Scroll-driven data narrative |
| 1.4 | Script | Earth Search STAC | `data/sentinel-2/` COGs + STAC Items | STAC search, pystac_client, COG access |
| 1.5 | Script | EUMETSAT Data Store | `data/cog/satellite-ir/` new COGs | External imagery acquisition |
| 1.6 | Script | Raw CEMS deliverables | `data/flood-depth/` COGs | Data engineering, COG conversion |
| 1.7 | Manual + Script | ECMWF HRES 0.1° COGs | `data/qgis/frontal-boundaries.geojson` | Meteorological domain expertise |

### What NOT to Search For / Suggest

If an agent suggests:
- Pre-rendering PNGs with Python → **NO.** Client-side rendering. Read Task 1.1.
- Using d3-contour for isobars → **NO.** WeatherLayers GL ContourLayer. Read Task 1.2.
- Building a custom particle system → **NO.** WeatherLayers GL ParticleLayer. Read Task 1.2.
- Generating temporal contour/barb/H-L GeoJSONs → **NO.** All client-side. Read v2 plan §3.
- Modifying scroll engine or chapter transitions → **NO.** Phase 2.
- Adding React components → **NO.** Vanilla TypeScript. Read v2 plan §1.

Redirect to `prompts/creative-direction-plan-v2.md` §3 where these decisions have evidence.
