# cheias.pt v2 — Sprint Backlog

**Date:** 2026-02-26
**Design Authority:** `prompts/scroll-timeline-symbology.md`
**Architecture:** `prompts/creative-direction-plan-v2.md`
**Project Rules:** `CLAUDE.md`

---

## How This Works

Each task is scoped for a **single Claude Code agent session** (1-3 hours). Tasks have
explicit dependencies, inputs, outputs, and verification commands. An agent reads CLAUDE.md,
this file, and the referenced design spec section — then executes.

**Branch strategy:** `v2/phase-N` off `main`. One branch per phase. PR when phase complete.

**Task ID format:** `P{phase}.{track}{number}` — e.g., P1.A1 = Phase 1, Track A, Task 1.

---

## Phase 1: Data Foundation + Derived Products + Cartographic Design

**Goal:** Every dataset the scroll narrative needs exists on disk, analytically enriched,
with colormaps and basemap styles tested and documented. Zero rendering code.

**Duration:** ~1 week. Tracks A/B/C run in parallel.

### Track A: Fill Temporal Gaps

The scroll timeline (§2, Ch.4) requires hourly data for ALL three storms. Currently only
Kristin (Jan 26-30) has hourly MSLP/wind. Leonardo and Marta are 6-hourly — visibly
choppy in animation.

---

#### P1.A1 — Fetch Hourly ERA5 for Leonardo + Marta

**Why:** Ch.4 sub-chapters 4c (Leonardo) and 4d (Marta) animate at 1/6th the smoothness
of 4a (Kristin). The viewer will notice.

**Read first:** `CLAUDE.md`, `scripts/fetch_era5_synoptic.py` (existing pipeline that
produced hourly Kristin data)

**Do:**
1. Examine the existing ERA5 fetch script. It already produced hourly data for Jan 26-30.
2. Re-run (or modify) for two additional windows:
   - Leonardo: Feb 4 00Z → Feb 8 23Z (120 hours)
   - Marta: Feb 9 00Z → Feb 12 23Z (96 hours)
3. Variables: `mean_sea_level_pressure`, `u_component_of_wind_10m`, `v_component_of_wind_10m`
4. Output: hourly COGs in existing directories (`data/cog/mslp/`, `data/cog/wind-u/`, `data/cog/wind-v/`)
5. Naming: `2026-02-06T14.tif` (same pattern as existing hourly files)

**Verify:**
```bash
# Leonardo should have 24 frames/day like Kristin
ls data/cog/mslp/2026-02-06T*.tif | wc -l  # expect 24
ls data/cog/wind-u/2026-02-06T*.tif | wc -l  # expect 24
# Marta same
ls data/cog/mslp/2026-02-10T*.tif | wc -l  # expect 24
```

**Output:** ~648 new COGs (216 hours × 3 variables). Existing files untouched.

**Dependencies:** None (first task).
**Estimated effort:** 2-3 hours (mostly fetch time).
**Commit:** `P1.A1: fetch hourly ERA5 MSLP+wind for Leonardo and Marta storm periods`

---

#### P1.A2 — Fetch Hourly ERA5 Precipitation for Storm Windows

**Why:** Daily precipitation (1 frame/day) can't show rain bands sweeping in Ch.4.
Need hourly to match MSLP/wind temporal density.

**Read first:** `scripts/fetch_era5_synoptic.py`, existing hourly approach

**Do:**
1. Fetch ERA5 hourly `total_precipitation` for 3 windows:
   - Kristin: Jan 26-30
   - Leonardo: Feb 4-8
   - Marta: Feb 9-12
2. Output: `data/cog/precipitation-hourly/YYYY-MM-DDTHH.tif` (new directory)
3. Keep existing daily `data/cog/precipitation/` untouched (used for Ch.3 slow buildup)
4. Note: ERA5 precip is accumulation — may need to compute hourly rate from differences.
   Document this in a README.

**Verify:**
```bash
ls data/cog/precipitation-hourly/2026-01-28T*.tif | wc -l  # expect 24
ls data/cog/precipitation-hourly/*.tif | wc -l  # expect ~336
```

**Dependencies:** None (parallel with P1.A1).
**Commit:** `P1.A2: fetch hourly ERA5 precipitation for storm windows`

---

#### P1.A3 — Fetch Extended Meteosat IR for Leonardo + Marta

**Why:** Satellite IR exists only for Kristin (48 hourly, Jan 27-28). Ch.4 sub-chapters
4c and 4d have NO cloud imagery. The comma cloud structure is the most recognizable
feature of each storm — its absence is a visible gap.

**Read first:** `scripts/fetch_eumetsat.py` (existing pipeline with eumdac credentials)

**Do:**
1. Run existing script with extended date ranges:
   ```bash
   python scripts/fetch_eumetsat.py --start 2026-02-04T00 --end 2026-02-08T00 --interval 1
   python scripts/fetch_eumetsat.py --start 2026-02-09T00 --end 2026-02-12T00 --interval 1
   ```
2. If credentials expired or API changed, document the failure in
   `data/cog/satellite-ir/FETCH-STATUS.md` and move on. This task has graceful degradation.
3. Verify new COGs are valid GeoTIFF.

**Verify:**
```bash
ls data/cog/satellite-ir/2026-02-06T*.tif | wc -l  # expect ~24
# Or check FETCH-STATUS.md if failed
```

**Output:** ~192 additional IR COGs, or documented failure.

**Dependencies:** None.
**Commit:** `P1.A3: fetch extended Meteosat IR for Leonardo and Marta`

---

#### P1.A4 — Fetch Sentinel-2 Before/After via Earth Search STAC

**Why:** Ch.6c Salvaterra triptych needs visual before/after comparison. This script is
also the STAC portfolio showcase — the code itself is a work sample.

**Read first:** `prompts/scroll-timeline-symbology.md` §2 Ch.6c symbology.
Also read `prompts/refactor-nwp-planetary-computer.md` for STAC patterns (similar approach).

**Do:**

Create `scripts/fetch_sentinel2_stac.py`:

1. Search Earth Search STAC (`https://earth-search.aws.element84.com/v1`) using `pystac_client`:
   ```python
   from pystac_client import Client
   catalog = Client.open("https://earth-search.aws.element84.com/v1")
   search = catalog.search(
       collections=["sentinel-2-l2a"],
       bbox=[-9.16, 38.65, -8.05, 39.48],
       datetime="2026-01-01/2026-01-25",
       query={"eo:cloud_cover": {"lt": 15}},
       max_items=5,
   )
   ```
2. Select best before (Jan, cloud<15%) and after (Feb 6-20, cloud<30%) scenes.
3. Access COGs directly from S3 — use `rasterio` with `AWS_NO_SIGN_REQUEST=YES`.
4. Read B04/B03/B02, clip to bbox, write as COG with overviews.
5. Compute NDWI = (B03 - B08) / (B03 + B08) for both scenes. Write difference as COG.
6. Output STAC Item JSON (1.0.0 spec) per scene.
7. Generate JPEG previews for QA.

**Output:**
```
data/sentinel-2/
  salvaterra-before-YYYYMMDD.tif    (true-color COG)
  salvaterra-after-YYYYMMDD.tif     (true-color COG)
  salvaterra-ndwi-diff.tif          (NDWI difference COG)
  before-item.json                  (STAC Item)
  after-item.json                   (STAC Item)
  preview-before.jpg
  preview-after.jpg
  README.md                         (search parameters, scene IDs, rationale)
```

**Verify:**
```bash
python3 -c "
import rasterio
for f in ['data/sentinel-2/salvaterra-before-*.tif']:
    import glob
    for p in glob.glob(f):
        with rasterio.open(p) as ds:
            print(f'{p}: {ds.width}x{ds.height} CRS={ds.crs} bands={ds.count}')
            tags = ds.tags()
            print(f'  COG: {\"LAYOUT\" in str(tags)}')
"
```

**Dependencies:** None.
**Commit:** `P1.A4: fetch Sentinel-2 before/after via Earth Search STAC with NDWI difference`

---

#### P1.A5 — Planetary Computer Met Office Comparison (STAC Showcase)

**Why:** Demonstrates STAC fluency with a second catalog. The comparison notebook (ERA5 vs
Met Office for Kristin peak) is legitimate scientific analysis.

**Read first:** `prompts/refactor-nwp-planetary-computer.md`

**Do:**
1. Create `scripts/fetch_metoffice_stac.py` per the refactor document spec.
2. Fetch Met Office Global 10km for **Kristin peak only** (Jan 27-29). Not the full range.
3. Also fetch 250 hPa wind for jet stream visualization (Ch.2 globe view).
4. Create `notebooks/07-nwp-comparison.ipynb`: side-by-side ERA5 vs Met Office MSLP maps,
   wind gust maxima, spatial difference.
5. Output to `data/cog/mslp-mo/`, `data/cog/wind-u-mo/`, etc. (parallel directories).

**Verify:** Jan 28 MSLP minimum within 5 hPa of ERA5 (~960 hPa).

**Dependencies:** None (independent STAC showcase).
**Priority:** LOWER than A1-A4. Do this if time permits or as a standalone demo.
**Commit:** `P1.A5: Planetary Computer Met Office STAC comparison for Kristin`

---

### Track B: Derived Analytical Products

These are the intermediary files that demonstrate geospatial mastery. Raw COGs → scientific
products. See scroll timeline §3 for rationale.

---

#### P1.B1 — Compute Automated Storm Track LineStrings

**Why:** Ch.2 storm arcs and Ch.4 annotations need storm track paths. Currently hand-drawn
in `storm-tracks.geojson`. Automated extraction from MSLP minima shows analytical skill.

**Do:**

Create `scripts/extract_storm_tracks.py`:

1. For each timestep in `data/cog/mslp/`, find the grid cell with minimum MSLP within
   a search domain (Atlantic + Iberia: -40°W to 5°E, 30°N to 60°N).
2. Track the minimum across timesteps. When the minimum pressure < 990 hPa, consider it
   a named storm. Group into continuous tracks.
3. Smooth the track with a Savitzky-Golay filter (scipy) to remove 6-hourly jitter.
4. Output as GeoJSON FeatureCollection with 3 LineStrings (Kristin, Leonardo, Marta).
   Each vertex has properties: `datetime`, `min_pressure_hpa`.
5. Compare with existing hand-drawn `storm-tracks.geojson` for validation.

**Output:**
```
data/qgis/storm-tracks-auto.geojson    (automated, 3 LineStrings)
data/qgis/storm-tracks-auto.md         (method documentation)
```

**Verify:**
```bash
python3 -c "
import json
gj = json.load(open('data/qgis/storm-tracks-auto.geojson'))
for f in gj['features']:
    p = f['properties']
    coords = f['geometry']['coordinates']
    print(f'{p[\"name\"]}: {len(coords)} pts, min {p[\"min_pressure_hpa\"]} hPa')
"
```

**Dependencies:** P1.A1 (needs hourly MSLP for Leonardo/Marta to produce smooth tracks).
Can run with 6-hourly data but tracks will be coarser.
**Commit:** `P1.B1: extract automated storm tracks from MSLP minima`

---

#### P1.B2 — Extract Flood Depth COGs from CEMS

**Why:** Ch.6c Salvaterra triptych needs depth visualization. Raw CEMS TIFs exist but need
extraction, clipping, and COG conversion.

**Read first:** Scroll timeline §2 Ch.6c symbology. Flood depth colormap:
`transparent → #deebf7 → #9ecae1 → #4292c6 → #2171b5 → #084594 → #8b0000`, domain [0, 7m].

**Do:**

Create `scripts/extract_flood_depth.py`:

1. Read the 3 CEMS monitoring TIFs:
   - `data/flood-extent/EMSR864_AOI03_DEL_MONIT01_v2/floodDepthA_v2.tif` (0-7.8m)
   - `data/flood-extent/EMSR864_AOI03_DEL_MONIT02_v1/floodDepthA_v1.tif` (0-9.3m)
   - `data/flood-extent/EMSR864_AOI03_DEL_PRODUCT_v1/floodDepthA_v1.tif` (0-9.6m)
2. Clip to Salvaterra bbox.
3. Convert to Cloud-Optimized GeoTIFF (tiled, overviews, deflate).
4. Write manifest with per-file statistics and CEMS attribution.

**Output:**
```
data/flood-depth/
  salvaterra-depth-monit01.tif   (COG, float32)
  salvaterra-depth-monit02.tif   (COG, float32)
  salvaterra-depth-product.tif   (COG, float32)
  manifest.json                  (stats + colormap + attribution)
```

**Dependencies:** None.
**Commit:** `P1.B2: extract flood depth COGs from CEMS Salvaterra`

---

#### P1.B3 — Draw Frontal Boundary GeoJSONs

**Why:** Ch.4d shows frontal boundaries via WeatherLayers GL FrontLayer (or MapLibre line).
Requires meteorological judgment — can't be fully automated.

**Do:**

1. Create `scripts/analyze_frontal_positions.py` — diagnostic script that loads MSLP + wind
   COGs at key timesteps and prints gradient analysis to guide manual placement.
2. Create `data/qgis/frontal-boundaries.geojson` with 4 LineString features:

| Front | Storm | Timestep | Type |
|-------|-------|----------|------|
| Kristin trailing cold front | Kristin | 2026-01-28T00Z | cold |
| Kristin trailing cold front (passed) | Kristin | 2026-01-28T12Z | cold |
| Leonardo warm front | Leonardo | 2026-02-05T12Z | warm |
| Marta trailing cold front | Marta | 2026-02-10T06Z | cold |

3. Properties: `front_type`, `storm`, `datetime`, `label` (Portuguese).

**Output:** `data/qgis/frontal-boundaries.geojson` (committed, <10KB).

**Dependencies:** Ideally after P1.A1 (hourly data helps place fronts accurately), but
can be done with existing 6-hourly data.
**Commit:** `P1.B3: frontal boundary GeoJSONs for 3 storms`

---

#### P1.B4 — Compute Running 7-Day Precipitation Accumulation

**Why:** Ch.4 benefits from showing cumulative rainfall over multi-day storms, not just
daily rate. "150mm in 7 days" tells the multi-storm story better than daily snapshots.

**Do:**

Create `scripts/compute_precip_accumulation.py`:

1. Read 78 daily precip COGs from `data/cog/precipitation/`.
2. For each day, compute rolling 7-day sum (window centered or trailing).
3. Output 71 COGs (first 7 days have incomplete window).
4. Also compute total Dec 1 → Feb 15 accumulation as a single COG.

**Output:**
```
data/cog/precipitation-7day/    (71 COGs, rolling 7-day sum)
data/cog/precipitation-total.tif (single COG, full-period accumulation)
```

**Dependencies:** None.
**Commit:** `P1.B4: compute 7-day rolling precipitation accumulation`

---

#### P1.B5 — Re-Render Precipitation PNGs (Blues + Blur + Alpha)

**Why:** Ch.3 soil moisture animation uses the scroll-driven PNG crossfade pattern (the ONE
chapter where scroll = time). The existing precip PNGs use yellow→red Viridis. The scroll
timeline specifies blues with gaussian blur and intensity-proportional alpha.

Even though Ch.4 renders precipitation from COGs client-side, Ch.3 still needs nice PNGs
for the slow-buildup overlay that crossfades with soil moisture.

**Read first:** Scroll timeline §2 Ch.3 symbology. Precipitation colormap:
`transparent → #b3d9e8 → #6baed6 → #3182bd → #08519c`. Alpha ∝ intensity.

**Do:**

Modify `scripts/rerender-pngs.py`:

1. Add `--layer precip|soil-moisture` CLI flag (protect SM PNGs).
2. Replace PRECIP_CMAP with blues `LinearSegmentedColormap`:
   `#e8f4f8 (light) → #6baed6 (moderate) → #08519c (heavy)`
3. Apply `scipy.ndimage.gaussian_filter(data, sigma=3)` BEFORE colormapping.
4. Alpha proportional to intensity: `alpha = np.clip(80 + 175*t, 0, 255)`.
5. Overwrite `data/raster-frames/precipitation/*.png` (77 files).

**Verify:**
```bash
python3 -c "
from PIL import Image; import numpy as np
img = np.array(Image.open('data/raster-frames/precipitation/precip_frame_040.png'))
# Check blue channel dominates
print(f'R mean: {img[:,:,0].mean():.0f}, B mean: {img[:,:,2].mean():.0f}')
# Blue should be > Red for the blues colormap
"
```

**Dependencies:** None.
**Commit:** `P1.B5: re-render precipitation PNGs with blues colormap, gaussian blur, variable alpha`

---

#### P1.B6 — Soil Moisture Percentile Computation (Stretch)

**Why:** Ch.3 annotation says "Percentil 98" — this should be a verifiable claim, not an
assertion. Requires ERA5-Land soil moisture climatology (1991-2020).

**Do:**
1. Fetch ERA5-Land monthly mean soil moisture (0-28cm layer) for 1991-2020 from CDS.
   30 years × 12 months = 360 files, but monthly means are small (~2MB each).
2. For each of the 77 daily SM COGs, compute the percentile rank against the
   climatological distribution for that month.
3. Output: 77 percentile COGs in `data/cog/soil-moisture-percentile/`.

**Priority:** STRETCH — the narrative works without it (we can assert "98th percentile"
from literature). But it's a genuine analytical product.

**Dependencies:** CDS API access.
**Commit:** `P1.B6: compute soil moisture percentiles from ERA5-Land climatology`

---

### Track C: Cartographic Design

These are DESIGN tasks, not code. They produce style files, colormap documents, and QGIS
screenshots that guide Phase 2 rendering.

---

#### P1.C1 — Per-Chapter Basemap Style Design

**Why:** The scroll timeline (§1) specifies 6 distinct basemap moods. Without testing them,
Phase 2 will render beautiful data over an ugly or inappropriate basemap.

**Do:**

Use MapTiler, Maputnik, or direct MapLibre style JSON editing:

1. Create (or fork from a dark template) a MapLibre style with layer groups that can be
   toggled per chapter:
   - `labels-pt` — Portuguese place labels at 2 density levels (sparse for Ch.0-4, moderate for Ch.5-9)
   - `terrain-hillshade` — hillshade (off for Ch.0-4, on for Ch.5-6)
   - `water-style` — ocean color variants (#060e14 for Ch.0, #0a212e for Ch.2-4)
   - `land-tint` — land color (near-invisible for Ch.0, muted green for Ch.3, dark for Ch.4)
   - `borders` — national borders (faint for Ch.4 synoptic, off otherwise)
   - `roads` — off everywhere except Ch.6 (consequences need road context)
2. Export as `data/basemap/cheias-dark.json` (MapLibre style JSON).
3. Screenshot each chapter's basemap at the specified camera position.
4. Document decisions in `data/basemap/BASEMAP-DECISIONS.md`.

**Output:**
```
data/basemap/
  cheias-dark.json             (MapLibre style)
  BASEMAP-DECISIONS.md         (rationale per chapter)
  screenshots/                 (1 per chapter, named ch0-basemap.png, etc.)
```

**Dependencies:** None. This can start immediately.
**Commit:** `P1.C1: per-chapter basemap style design`

---

#### P1.C2 — Complete Colormap Palette + QGIS Verification

**Why:** The scroll timeline specifies colormaps for ~12 data layers. These need to be
tested against the basemap for contrast, tested for colorblind safety, and documented.

**Do:**

1. Create `data/colormaps/palette.json` documenting every colormap:
   ```json
   {
     "precipitation-blues": {
       "type": "sequential",
       "stops": [[0, "#e8f4f8"], [0.3, "#b3d9e8"], [0.6, "#6baed6"], [0.8, "#3182bd"], [1.0, "#08519c"]],
       "domain": [0, 80],
       "units": "mm/day",
       "alpha": "proportional",
       "chapters": ["ch3", "ch4"]
     },
     ...
   }
   ```
2. Define all colormaps from the scroll timeline:
   - `precipitation-blues` (Ch.3/4)
   - `soil-moisture-browns` (Ch.3) — already defined in SM PNGs, document it
   - `sst-diverging` (Ch.2)
   - `ivt-sequential` (Ch.2)
   - `satellite-ir-inverted` (Ch.4)
   - `flood-depth` (Ch.6c)
   - `ipma-warnings` (Ch.4)
   - `burn-scars-amber` (Ch.7)
   - `discharge-ratio` (Ch.5)
   - `precip-anomaly` (Ch.3 stretch)
   - `precip-accumulation-7day` (Ch.4)
   - `mslp-contour` (Ch.4 — just stroke color/weight)
3. Load representative COGs in QGIS, apply each colormap, overlay on the Ch.0 basemap.
4. Screenshot each layer + basemap composite.
5. Test colorblind safety (deuteranopia simulation in QGIS or online tool).

**Output:**
```
data/colormaps/
  palette.json                 (machine-readable)
  COLORMAP-DECISIONS.md        (rationale, colorblind notes)
  screenshots/                 (each layer over basemap)
```

**Dependencies:** P1.C1 (basemap needed for overlay testing).
**Commit:** `P1.C2: complete colormap palette with QGIS verification`

---

## Phase 2: Rendering + Temporal Players + Scroll Choreography

**Goal:** The scroll narrative works end-to-end. Every chapter shows data, temporal players
run, camera transitions fire, text reveals animate. Deployed and viewable.

**Duration:** ~2 weeks. Must be done sequentially (dependencies are tight).

**Branch:** `v2/phase-2` off `main` (after Phase 1 merged).

### Track A: Core Systems (Week 1)

Build the rendering and temporal infrastructure before wiring to chapters.

---

#### P2.A1 — COG Rendering Pipeline (geotiff.js → Colormap → BitmapLayer)

**Why:** The foundation for every raster layer in the narrative.

**Read first:** Scroll timeline §2 (all raster symbology), `data/colormaps/palette.json`.

**Do:**

Rewrite `src/data-loader.ts`:
1. `loadCOG(url): Promise<DecodedRaster>` — geotiff.js + HTTP range requests
2. `applyColormap(raster, config): ImageData` — lookup table from `palette.json`
3. `gaussianBlur(data, width, height, sigma): Float32Array` — separable kernel for precip
4. `rasterToImageBitmap(imageData): Promise<ImageBitmap>` — for deck.gl BitmapLayer

Extend `src/layer-manager.ts`:
5. `createRasterLayer(id, imageBitmap, bounds): BitmapLayer`
6. Dual-buffer crossfade (A/B layers with opacity transition)

**Verify:** Load a precip COG and an SST COG in the browser console. Both render with
correct colormaps on the map. Crossfade between them.

**Commit:** `P2.A1: client-side COG rendering pipeline with dynamic colormaps`

---

#### P2.A2 — WeatherLayers GL Integration

**Why:** Replaces ~5 days of custom code. Particles, isobars, wind barbs, H/L markers.

**Read first:** Scroll timeline §2 Ch.4a symbology (all WeatherLayers specs).

**Do:**

Create `src/weather-layers.ts`:
1. `ParticleLayer` — wind particles from U/V COGs
2. `ContourLayer` — MSLP isobars at 4hPa intervals
3. `HighLowLayer` — H/L markers
4. `GridLayer` — wind barbs (WIND_BARB style)

Wire to deck.gl MapboxOverlay.

**Verify:** Load Jan 28 06Z MSLP + wind COGs. All 4 layers render simultaneously.
Particles flow. Isobars form concentric rings around the Kristin low. H/L markers appear.

**Commit:** `P2.A2: WeatherLayers GL integration — particles, isobars, H/L, wind barbs`

---

#### P2.A3 — Chapter Temporal Player System

**Why:** The architectural core of "scroll ≠ timeline." Each chapter owns its player.

**Read first:** Scroll timeline §0 (architectural principle).

**Do:**

Create `src/temporal-player.ts`:

```typescript
interface TemporalPlayer {
  load(frames: FrameConfig[]): Promise<void>;  // preload all frames
  play(fps: number, loop: boolean): void;       // start playback
  pause(): void;
  stop(): void;                                  // stop + reset to frame 0
  seek(frameIndex: number): void;
  onFrame(callback: (frame: DecodedRaster, index: number, timestamp: string) => void): void;
}
```

1. Pre-loads ALL frames (COG URLs or PNG URLs) into memory on `load()`.
2. `play()` runs `requestAnimationFrame` loop at specified fps.
3. Each frame callback updates the relevant deck.gl/MapLibre layers.
4. Player instances are created per chapter, destroyed on chapter exit.
5. Handle dual-buffer crossfade between frames (no pop, smooth blend).

Extend `src/scroll-engine.ts`:
6. `onStepEnter` creates and starts the chapter's player.
7. `onStepExit` stops and destroys the player.
8. Pre-load next chapter's frames when user is 80% through current chapter.

**Verify:** Manual test — enter Ch.4, temporal player starts at 8fps, isobars animate.
Exit Ch.4, player stops. Re-enter, player restarts from frame 0.

**Commit:** `P2.A3: chapter-local temporal player with preloading and crossfade`

---

#### P2.A4 — Basemap + Globe + Terrain Integration

**Why:** Per-chapter basemap switching. Globe projection for Ch.2. Terrain for Ch.5-6.
These are the 3D high-impact views.

**Read first:** Scroll timeline §1 (basemap strategy), creative-direction-plan-v2.md §4 (3D).

**Do:**

Extend `src/map-setup.ts`:

1. **Per-chapter basemap switching:** Load `cheias-dark.json` style. On chapter enter,
   toggle layer groups (labels-pt, terrain-hillshade, water-style, etc.) via
   `setLayoutProperty` and `setPaintProperty`.

2. **Globe projection for Ch.2:**
   ```typescript
   map.setProjection('globe');  // on Ch.2 enter
   map.setProjection('mercator');  // on Ch.3 enter (smooth transition)
   ```
   MapLibre v5 handles the animated transition natively.

3. **Terrain for Ch.5-6:**
   ```typescript
   map.addSource('terrain', { type: 'raster-dem', url: terrainTileUrl });
   map.setTerrain({ source: 'terrain', exaggeration: 1.5 });  // Ch.5 enter
   map.setTerrain(null);  // Ch.7 enter (disable)
   ```

4. **3D columns for Ch.5 discharge:**
   ```typescript
   const columns = new ColumnLayer({
     id: 'discharge-columns',
     data: dischargeStations,
     getPosition: d => [d.lon, d.lat],
     getElevation: d => d.peak_ratio * 5000,
     getFillColor: d => d.peak_ratio > 5 ? [231,76,60,200] : [52,152,219,200],
     radius: 4000,
     extruded: true,
   });
   ```

**Verify:**
- Ch.2: Map shows globe. Rotating slightly.
- Ch.3 enter: Smooth globe→mercator transition.
- Ch.5: Terrain visible. 3D columns at discharge stations. Guadiana column towers (11.5×).
- Ch.6: Terrain with satellite-style basemap. Flood plains visible as depressions.

**Commit:** `P2.A4: basemap switching, globe projection, terrain, 3D discharge columns`

---

### Track B: Chapter Implementation (Week 2)

Wire each chapter per the scroll timeline spec. One task per chapter (or chapter group).

---

#### P2.B1 — Chapters 0-1: Hook + Flash-Forward

**Read first:** Scroll timeline §2 Ch.0 and Ch.1 (frame-by-frame spec).

**Do:**
- Ch.0: Hero title GSAP fade-in, ghost flood pulse (PMTiles at 3% opacity, 2s fade), number ticker.
- Ch.1: Flood extent PMTiles fade-in to 70%, statistics text, transition text.
- Both chapters: static layers only, no temporal player.

**Commit:** `P2.B1: chapters 0-1 hook and flash-forward`

---

#### P2.B2 — Chapter 2: The Atlantic Engine (Globe + SST + IVT + Particles)

**Read first:** Scroll timeline §2 Ch.2 (full spec including globe, SST, IVT, storm arcs, particles).

**Do:**
- Globe projection active.
- SST anomaly raster fade-in (diverging blue-white-red).
- Storm track ArcLayer (3 great circles, named labels).
- IVT temporal player: 77 daily frames at 2fps, loop.
- Wind particles (2000, white trails) flowing along AR corridor.
- IVT crossfade from ERA5 0.5° → ECMWF HRES 0.1° as date approaches January.
- Globe→mercator transition on exit.

**This is the first high-impact 3D chapter.** Globe + particles + arcs on the curved ocean.

**Commit:** `P2.B2: chapter 2 Atlantic engine with globe, IVT, storm arcs`

---

#### P2.B3 — Chapter 3: The Sponge Fills (Scroll-Driven SM + Wildfire Foreshadow)

**Read first:** Scroll timeline §2 Ch.3 (frame-by-frame including scroll-to-frame mapping).

**Do:**
- Scroll-driven SM PNG crossfade: `Math.floor(scrollProgress * 0.9 * 76)`.
- Preload all 77 SM PNGs on chapter approach.
- Date counter HTML overlay.
- Basin sparklines (Observable Plot).
- Wildfire burn scars at 15% opacity at scroll 0.5 (the foreshadowing).
- Percentile annotation at scroll 0.7.
- Transition: SM fades, precipitation layer fades in underneath.

**Commit:** `P2.B3: chapter 3 soil moisture scroll animation with wildfire foreshadow`

---

#### P2.B4 — Chapter 4: The Storms (Full Synoptic Composite)

**Read first:** Scroll timeline §2 Ch.4a-4d (the most detailed section).

**This is the hardest task.** 4 sub-chapters, 3 temporal players, 10-layer stack.

**Do:**
- Sub-chapter 4a (Kristin): Synoptic temporal player (hourly MSLP+wind, 8fps). Particles + isobars + H/L. Satellite IR player (48 frames, 4fps). Lightning bursts. Annotations.
- Sub-chapter 4b (respite): Static frame (Jan 31). Discharge sparklines showing lag.
- Sub-chapter 4c (Leonardo): Synoptic player (6-hourly or hourly if P1.A1 completed). IPMA warnings escalating to red.
- Sub-chapter 4d (Marta): Tighter camera. Frontal boundaries. Full layer composite.
- Layer hierarchy management: max 6 layers simultaneously. Satellite replaces synoptic view (not additive).

**Commit:** `P2.B4: chapter 4 three storms — synoptic composite with sub-chapter transitions`

---

#### P2.B5 — Chapter 5: Rivers Respond (Terrain + 3D Columns + Sparklines)

**Read first:** Scroll timeline §2 Ch.5 spec.

**Do:**
- Terrain enabled (exaggeration 1.5).
- River network GeoJSON (width by Strahler order).
- Discharge station markers (size by ratio).
- Sequential camera focus: Tejo → Mondego → Sado → Guadiana.
- Discharge temporal player (daily, Dec 1-Feb 15, 3fps).
- Observable Plot sparklines per river in side panel.
- **3D columns** at scroll 0.80 — peak discharge extruded. Guadiana towers at 11.5×.

**Commit:** `P2.B5: chapter 5 rivers with terrain, 3D columns, sparklines`

---

#### P2.B6 — Chapter 6: The Human Cost (Consequences + Salvaterra Triptych)

**Read first:** Scroll timeline §2 Ch.6a-6d spec.

**Do:**
- 4 sub-chapters with intimate camera work (z10-13, p35-45).
- Terrain + satellite basemap.
- Flood extent per AOI (EMSR861 + EMSR864 overlap in Coimbra).
- Consequence markers (typed icons).
- Salvaterra triptych: 3 additive flood extents (light→medium→dark blue).
- Flood depth COG overlay (blue→red, from P1.B2).
- Sentinel-2 before/after with maplibre-gl-compare (if P1.A4 succeeded).
- National pull-back with all 42 markers.

**Commit:** `P2.B6: chapter 6 consequences with Salvaterra triptych and flood depth`

---

#### P2.B7 — Chapter 7: The Full Picture (Wildfire Reveal)

**Read first:** Scroll timeline §2 Ch.7 spec.

**Do:**
- Sequential layer build: basins → precipitation total → flood extent → consequences → **burn scars (THE REVEAL)**.
- Amber burn scars at 60% opacity over blue flood extent.
- Progressive opacity management (each new layer reduces previous).
- The spatial correlation between fire and flood is immediately visible.

**Commit:** `P2.B7: chapter 7 wildfire reveal composite`

---

#### P2.B8 — Chapters 8-9: Analysis + Exploration

**Do:**
- Ch.8: Static basin risk map + policy text. No temporal player.
- Ch.9: Unlock map interaction. Layer toggles. Geolocation button.

**Commit:** `P2.B8: chapters 8-9 analysis and exploration mode`

---

## Phase 3: Polish + Stretch Goals

Lower priority. Each task is independent.

| ID | Task | Chapter | Effort |
|----|------|---------|--------|
| P3.1 | Entry animation (slow globe rotation → Portugal descent → title) | Ch.0 | 0.5d |
| P3.2 | Temperature field beneath isobars (red/blue thermal, 70% opacity) | Ch.4 | 1-2d |
| P3.3 | 3D flood depth (extruded water surface over terrain at Salvaterra) | Ch.6c | 1-2d |
| P3.4 | Satellite annotations ("CICLOGENESE EXPLOSIVA", "STING JET", dry slot arrow) | Ch.4a | 0.5d |
| P3.5 | Responsive layout (mobile bottom sheet, tablet) | All | 1-2d |
| P3.6 | Performance tuning (COG prefetch, lazy-load, device-adaptive particles) | All | 1d |
| P3.7 | Accessibility (ARIA, keyboard nav, `prefers-reduced-motion`) | All | 1d |
| P3.8 | Soil moisture percentile overlay (from P1.B6 data) | Ch.3 | 0.5d |
| P3.9 | Precipitation anomaly overlay (% of 30-year mean) | Ch.3/4 | 1d |
| P3.10 | Jet stream visualization (250 hPa wind from P1.A5) | Ch.2 | 1d |

---

## Dependency Graph

```
Phase 1 (parallel tracks):
  A1 (hourly Leonardo/Marta) ──→ B1 (storm tracks) ──→ [Phase 2]
  A2 (hourly precip) ─────────────────────────────────→ [Phase 2]
  A3 (extended Meteosat) ─────────────────────────────→ [Phase 2]
  A4 (Sentinel-2 STAC) ──────────────────────────────→ [Phase 2]
  A5 (Planetary Computer) ────────────────────────────→ [P3.10]
  B2 (flood depth) ───────────────────────────────────→ [Phase 2]
  B3 (frontal boundaries) ────────────────────────────→ [Phase 2]
  B4 (7-day precip accum) ────────────────────────────→ [Phase 2]
  B5 (precip PNG re-render) ──────────────────────────→ [Phase 2]
  B6 (SM percentile, stretch) ────────────────────────→ [P3.8]
  C1 (basemap design) ───→ C2 (colormap + QGIS) ────→ [Phase 2]

Phase 2 (sequential):
  A1 (COG pipeline) ──→ A2 (WeatherLayers) ──→ A3 (temporal player)
       │                                              │
       └──→ A4 (basemap+globe+terrain) ──────────────┘
                                                      │
                                                      ▼
  B1 (Ch.0-1) → B2 (Ch.2) → B3 (Ch.3) → B4 (Ch.4) → B5 (Ch.5) → B6 (Ch.6) → B7 (Ch.7) → B8 (Ch.8-9)

Phase 3 (independent tasks, any order)
```

---

## 3D Views — Where They Live

To be explicit about the high-impact 3D views that must NOT be dropped:

| View | Chapter | Task | Phase |
|------|---------|------|-------|
| **Globe projection** | Ch.2 (Atlantic engine) | P2.A4 + P2.B2 | **Phase 2** |
| **Globe → mercator transition** | Ch.2→Ch.3 | P2.A4 + P2.B2 | **Phase 2** |
| **Terrain exaggeration** (1.5×) | Ch.5 (rivers) | P2.A4 + P2.B5 | **Phase 2** |
| **Terrain + satellite basemap** | Ch.6 (consequences) | P2.A4 + P2.B6 | **Phase 2** |
| **3D discharge columns** (ColumnLayer) | Ch.5 (rivers) | P2.B5 | **Phase 2** |
| **3D flood depth** (extruded surface) | Ch.6c (Salvaterra) | P3.3 | **Phase 3** (stretch) |
| Globe slow rotation entry | Ch.0 (hook) | P3.1 | Phase 3 |

All except 3D flood depth and entry rotation are **Phase 2 core**.

---

## Agent Session Template

Paste this at the start of any Claude Code session:

```
I'm working on cheias.pt v2. Before doing anything:

1. Read `CLAUDE.md` — project rules, git workflow, venv
2. Read `prompts/sprint-backlog.md` — find my task by ID
3. Read `prompts/scroll-timeline-symbology.md` — design spec (symbology, colormaps, layer stacking)
4. Read the "Read first" files listed in my task

Key principles:
- Scroll navigates chapters. Chapters own temporal players (start/play/stop/loop).
- Pre-load frames on chapter approach. Don't load on scroll demand.
- Max 6 layers simultaneously. Visual hierarchy > data density.
- Colormaps are defined in data/colormaps/palette.json (after P1.C2).
- WeatherLayers GL: particles, isobars, wind barbs, H/L markers.
- 3D: globe (Ch.2), terrain (Ch.5-6), ColumnLayer (Ch.5). NOT optional.
- All scripts in project .venv. NEVER --break-system-packages.

Current task: [TASK ID — DESCRIPTION]
```

---

## Sprint Metrics

| Phase | Tasks | Estimated Effort | Parallelism |
|-------|-------|-----------------|-------------|
| Phase 1 | 13 tasks (A1-A5, B1-B6, C1-C2) | ~8-10 days | High (3 tracks) |
| Phase 2 | 12 tasks (A1-A4, B1-B8) | ~12-15 days | Low (sequential) |
| Phase 3 | 10 tasks | ~8-10 days | High (independent) |
| **Total** | **35 tasks** | **~28-35 days** | |

Phase 1 can run 3 agents simultaneously (one per track).
Phase 2 Track A must complete before Track B starts.
Phase 2 Track B chapters can be parallelized in pairs (B1+B2, B3+B4, B5+B6, B7+B8).
Phase 3 tasks are fully independent.
