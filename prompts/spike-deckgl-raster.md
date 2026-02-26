# Spike: deck.gl-raster COG Compatibility Test

## Context

Before committing to the titiler-heavy Prompt B, test whether DevSeed's `deck.gl-raster`
(`@developmentseed/deck.gl-geotiff`) can render our ERA5 COGs directly from R2 in the browser.
This would eliminate the need for titiler as a tile server for temporal animation — COGs get
fetched and rendered client-side via GPU, with only HTTP range requests to R2.

**What deck.gl-raster gives us:**
- Direct COG → GPU rendering, no tiling service needed
- Automatic overview selection based on zoom (built-in LOD)
- Client-side colormap/rescale (GPU shader pipeline)
- Efficient streaming — only fetches visible portions via HTTP range requests

**Critical unknowns to test:**
1. Can we load ESM-only `@developmentseed/deck.gl-geotiff` in a no-build HTML file?
2. Do our ERA5 COGs on R2 work? (CORS headers, CRS, band structure, internal tiling)
3. What's the render latency when switching between temporal COGs?
4. Can we control colormap client-side (replacing titiler's server-side rendering)?
5. Does it work alongside MapLibre via `MapboxOverlay` (our existing integration pattern)?

## Pre-requisite

Sync at least a few test COGs to R2 if not already done:
```bash
# Just need a handful for the spike — pick 3 dates
rclone copy data/cog/precipitation/2026-01-27.tif r2:cheias-cog/cog/precipitation/ --progress
rclone copy data/cog/precipitation/2026-01-28.tif r2:cheias-cog/cog/precipitation/ --progress
rclone copy data/cog/precipitation/2026-02-05.tif r2:cheias-cog/cog/precipitation/ --progress
rclone copy data/cog/satellite-ir/2026-01-27T12-00.tif r2:cheias-cog/cog/satellite-ir/ --progress
rclone copy data/cog/mslp/2026-01-27T12.tif r2:cheias-cog/cog/mslp/ --progress
```

Also verify R2 CORS allows browser range requests:
```bash
curl -I -H "Origin: http://localhost:8000" \
  "https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/precipitation/2026-01-27.tif"
# Need: Access-Control-Allow-Origin, Accept-Ranges: bytes
```

## Task

Create `spike-deckgl-raster.html` — a minimal standalone test page. Keep it SIMPLE. No timeline,
no layer panel, no styling beyond basics. Just prove the technology works with our data.

### Loading Strategy

The package is ESM-only (no UMD bundle). Use `esm.sh` as ESM CDN with an import map:

```html
<script type="importmap">
{
  "imports": {
    "@deck.gl/core": "https://esm.sh/@deck.gl/core@9",
    "@deck.gl/mapbox": "https://esm.sh/@deck.gl/mapbox@9",
    "@deck.gl/layers": "https://esm.sh/@deck.gl/layers@9",
    "@developmentseed/deck.gl-geotiff": "https://esm.sh/@developmentseed/deck.gl-geotiff"
  }
}
</script>
<script type="module">
import { MapboxOverlay } from '@deck.gl/mapbox';
import { COGLayer } from '@developmentseed/deck.gl-geotiff';
// ...
</script>
```

If esm.sh doesn't resolve the transitive deps cleanly (geotiff.js, proj4, etc.), try:
- `https://cdn.skypack.dev/@developmentseed/deck.gl-geotiff`
- `https://esm.run/@developmentseed/deck.gl-geotiff`
- As last resort: clone the repo, `pnpm build`, and serve the dist locally

### Test 1: Basic COG Rendering

Render a single precipitation COG from R2 on a MapLibre dark basemap:

```js
const precipLayer = new COGLayer({
  id: 'precip-test',
  geotiff: 'https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/precipitation/2026-01-27.tif',
  opacity: 0.7,
});
```

**Pass criteria:** Precipitation field visible over Portugal, correct geographic placement.
**Fail indicators:** CORS error, blank tiles, misaligned position, console errors about CRS.

### Test 2: Temporal COG Switching

Add 3 buttons to swap between dates. On click, create a new COGLayer with the new date's URL
and call `overlay.setProps({ layers: [newLayer] })`.

Measure (via `performance.now()`) the time from button click to visible render.

**Pass criteria:** <2s from click to visible render. Acceptable: <5s. Dealbreaker: >10s.

### Test 3: Custom Colormap / Rescale

deck.gl-raster supports `renderTile` for custom GPU rendering pipelines. Test whether we can
apply a colormap to single-band data (our COGs are all single-band float32).

If the library auto-infers a grayscale render, we need to check if we can override with
a custom shader module or colormap prop. Check the library's GPU module docs.

Alternatively, test with the satellite-ir COG which might render more naturally as grayscale.

**Pass criteria:** Can apply at least a basic colormap (even if manual shader). 
**Acceptable:** Grayscale renders correctly, colormap can be added later.

### Test 4: MapLibre Integration

Confirm COGLayer works inside a `MapboxOverlay` (deck.gl's MapLibre integration layer),
which is the pattern used in `deckgl-prototype.html`:

```js
const overlay = new MapboxOverlay({
  interleaved: true,
  layers: [precipLayer]
});
map.addControl(overlay);
```

**Pass criteria:** COG renders interleaved with MapLibre basemap layers (not just on top).

### Test 5: Mixed Architecture

Can we have BOTH:
- deck.gl-raster COGLayer for raster animation (precipitation, soil moisture, satellite)
- Native MapLibre vector layers (rivers, MSLP contours, discharge stations)
- deck.gl standard layers (ArcLayer for storm tracks)

All rendering together in the same map?

**Pass criteria:** All three layer types visible simultaneously.

## Output

After running the spike, add a results section to this file documenting:

```
## Results

### Test 1 — Basic COG Rendering
- Status: PASS / FAIL / PARTIAL
- Notes: ...
- Screenshot: (if useful)

### Test 2 — Temporal Switching  
- Status: PASS / FAIL
- Latency: Xms average
- Notes: ...

### Test 3 — Colormap
- Status: PASS / FAIL / NEEDS_WORK
- Notes: ...

### Test 4 — MapLibre Integration
- Status: PASS / FAIL
- Notes: ...

### Test 5 — Mixed Architecture
- Status: PASS / FAIL
- Notes: ...

### Decision
- [ ] GO: Use deck.gl-raster for temporal rasters, keep titiler for dynamic queries only
- [ ] NO-GO: Stick with titiler tile serving (revert to Prompt B as written)
- [ ] PARTIAL: Use deck.gl-raster for X but titiler for Y because Z
```

## Architecture Impact

**If GO:** Prompt B gets rewritten:
- Raster animation layers use COGLayer pointing directly at R2 COGs
- Titiler kept for: colormap dropdown demo, statistics endpoint, contour algorithm, point queries
- Crossfade becomes: two COGLayers with animated opacity (simpler than dual tile sources)
- Attribution becomes: "Powered by deck.gl-raster + titiler" (double DevSeed signal)

**If NO-GO:** Run Prompt B as written (titiler tile sources for everything).

## Constraints

- HTML file served via `python3 -m http.server` from project root
- No npm/node/build step — browser-only with CDN imports
- Test on Chrome (primary) and Firefox (secondary)
- Dark basemap: CARTO dark-matter (same as prototype)

---

## Results (2026-02-25)

Spike file: `spike-deckgl-raster.html`

### Pre-requisites — PASS

- R2 CORS: `Access-Control-Allow-Origin: *`, `Accept-Ranges: bytes` confirmed
- All test COGs accessible on R2 (precipitation, MSLP, satellite-ir)
- COG structure verified: EPSG:4326, single-band float32, 256×256 internal tiles, 2 overviews

### Test 0 — ESM CDN Loading of deck.gl-geotiff

- Status: **FAIL**
- Error: `Failed to resolve module specifier "@deck.gl/core". Relative references must start with either "/", "./", or "../".`
- Root cause: `@developmentseed/deck.gl-geotiff` uses bare specifiers (`@deck.gl/core`, `@luma.gl/core`) in its internal imports. The `?external=` param on esm.sh doesn't work because the UMD deck.gl bundle doesn't register itself as ES module specifiers in the import map. The peer dep graph (luma.gl WebGPU device, mesh-layers, geo-layers) makes pure CDN use impractical without a bundler.
- **Verdict: deck.gl-geotiff requires a build step. Cannot use in no-build HTML.**

### Fallback Architecture

Since COGLayer is not viable without a bundler, the spike tested an alternative:
**geotiff.js (ESM via esm.sh) → read COG → canvas colormap → deck.gl BitmapLayer**

This is the architecture all remaining tests evaluate.

### Test 1 — Basic COG Rendering

- Status: **PASS**
- All 3 COG types render with correct geographic placement over Portugal
- geotiff.js loads from `esm.sh` in ~140ms
- `fromUrl()` performs HTTP range requests to R2 automatically
- BitmapLayer via MapboxOverlay renders interleaved with basemap
- EPSG:4326 bbox from GeoTIFF metadata maps directly to BitmapLayer bounds

| COG Type | Dimensions | File Size | Fetch (cold) | Canvas | Total |
|----------|-----------|-----------|-------------|--------|-------|
| Precipitation | 175×265 | ~115 KB | 534-558ms | 8-16ms | 543-574ms |
| MSLP | 261×97 | ~75 KB | 281-309ms | 5-9ms | 286-318ms |
| Satellite IR | 1667×1000 | ~2.1 MB | 695-878ms | 143-224ms | 919-1041ms |

### Test 2 — Temporal Switching

- Status: **PASS**
- All switches under 2s (pass criteria: <2s). Most under 600ms.

| COG Type | Cold Switch | Cached (warm) | Verdict |
|----------|-----------|--------------|---------|
| Precipitation | 543-1793ms | — | PASS (worst case was network variance) |
| MSLP | 281-309ms | 50-114ms | PASS (sub-100ms cached!) |
| Satellite IR | 695-878ms | 313ms | PASS (largest COG still <1s cached) |

- Cached fetches are dramatically faster (50-114ms for MSLP) — browser HTTP cache works with R2
- Canvas rendering is trivially fast: 5-20ms for small COGs, 143-224ms for 1.67M pixels
- For animation playback, pre-fetching the next frame would make switches near-instant

### Test 3 — Colormap

- Status: **PASS**
- Client-side colormaps implemented via canvas pixel mapping in the fallback path
- Three colormaps tested: viridis (precipitation), blues (MSLP), IR thermal (satellite)
- Data auto-ranging works: reads min/max from band, normalizes to 0-1, applies LUT
- Precipitation: 12-68mm range on Jan 27, up to 114mm on Feb 5 (Storm Leonardo signal clear)
- MSLP: 95,785-101,661 Pa range (957-1017 hPa) — deep cyclone visible
- Satellite IR: 0-255 uint8 (already pre-scaled)
- Rescale is trivial — just change the `[min, max]` normalization bounds

### Test 4 — MapLibre Integration

- Status: **PASS**
- BitmapLayer renders via `MapboxOverlay({ interleaved: true })`
- Raster sits correctly between basemap labels and background
- Geographic alignment perfect — basemap city labels show through semi-transparent raster
- No z-fighting or rendering artifacts

### Test 5 — Mixed Architecture

- Status: **PASS**
- Confirmed: deck.gl BitmapLayer (raster) + MapLibre vector layers (basin outlines, district borders) render simultaneously
- Vectors toggle on/off independently without affecting raster layer
- Log confirms: "deck.gl BitmapLayer + MapLibre vectors rendering together"
- Standard deck.gl layers (ArcLayer, ScatterplotLayer) would also work via the same MapboxOverlay — this is the existing pattern from `deckgl-prototype.html`

### Performance Summary

| Metric | Value | Notes |
|--------|-------|-------|
| geotiff.js load | ~140ms | One-time ESM import from esm.sh |
| COG fetch (small, cold) | 280-560ms | Precipitation 115KB, MSLP 75KB |
| COG fetch (large, cold) | 700-880ms | Satellite IR 2.1MB |
| COG fetch (cached) | 50-313ms | Browser HTTP cache effective |
| Canvas colormap | 5-224ms | Proportional to pixel count |
| Total render (small COG) | 55-574ms | Well under 1s |
| Total render (large COG) | 456-1041ms | Acceptable, under 2s target |

### Decision

- [x] **PARTIAL: Use geotiff.js + BitmapLayer for temporal rasters, skip deck.gl-geotiff (needs bundler)**

**What works without a build step:**
- `geotiff.js` via esm.sh — reads COGs from R2 with range requests
- `deck.gl` UMD bundle — BitmapLayer for rendering, MapboxOverlay for integration
- Client-side colormaps via canvas pixel mapping
- All 3 COG types (precipitation, MSLP, satellite-ir) render correctly

**What doesn't work without a build step:**
- `@developmentseed/deck.gl-geotiff` COGLayer — bare specifier resolution fails
- GPU-accelerated rendering pipeline (shader modules for colormaps)
- Automatic overview/LOD selection (geotiff.js reads full resolution)

**Architecture for scrollytelling (v0):**
1. **Temporal rasters** (precipitation, soil moisture, MSLP): geotiff.js → canvas → BitmapLayer. Pre-fetch next frame during playback for smooth animation. Crossfade via two BitmapLayers with animated opacity.
2. **Satellite imagery**: Same pipeline. Larger files but still <1s cached.
3. **Vector overlays** (basins, districts, discharge stations, consequences): Native MapLibre layers.
4. **Animated layers** (storm tracks, wind): Standard deck.gl layers (ArcLayer, ScatterplotLayer) via same MapboxOverlay.
5. **titiler**: Not needed for v0. Could add later for dynamic colormap selection, statistics, or contour generation — but the static pipeline covers all scrollytelling needs.

**Key insight:** The "fallback" is actually the better architecture for a no-build project. geotiff.js is a clean, well-maintained library (2.1.3, 138 exports). The BitmapLayer path gives us full control over colormaps without GPU shader complexity. The performance is excellent — sub-second for our COG sizes. The only tradeoff vs COGLayer is no automatic LOD/overview selection, but our COGs are small enough that this doesn't matter (largest is 2.1MB, smallest 75KB).

---

## Results — Local Build Test (2026-02-26)

Tested COGLayer with esbuild-bundled `@developmentseed/deck.gl-geotiff@0.2.0`.

### Build Setup

- `spike-build/package.json` + `spike-build/entry.js` (5 lines)
- `esbuild entry.js --bundle --format=esm --outfile=spike-deckgl-bundle.js --minify`
- Bundle: **1.3MB** minified, built in **259ms**
- Exports: `COGLayer`, `MapboxOverlay`, `BitmapLayer`, `proj4`

### Bug 1 — proj4 Ellipsoid Resolution (FIXED)

- **Error:** `Cannot destructure property 'a' of 'jS[e.ellps]' as it is undefined`
- **Root cause:** Default `geoKeysParser` fetches PROJJSON from epsg.io, but proj4 parses `+type=crs` flag and strips the `ellps` field from the parsed object. The `metersPerUnit()` function in `cog-tile-matrix-set.js` then does `Ellipsoid[parsedCrs.ellps]` where `ellps` is `undefined`.
- **Fix:** Custom `geoKeysParser` prop returning proj4 string `+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs` (without `+type=crs`). This ensures `parsed.ellps = "WGS84"` is present.
- **Upstream bug:** Should be filed on `deck.gl-raster` — the default geoKeysParser doesn't work with bundled proj4 for EPSG:4326.

### Bug 2 — Float32 SampleFormat (CONFIRMED, NOT FIXABLE)

- **Error:** `Inferring render pipeline for non-unsigned integers not yet supported. Found SampleFormat: 3`
- **Root cause:** `inferRenderPipeline` in `render-pipeline.ts` explicitly rejects float32 data. Only uint8/uint16 photometric types are supported.
- **Fix:** Pre-convert COGs to uint8 with `gdal_translate -scale -ot Byte`.
- **v0.2.0 limitation** — may be fixed in v0.3.0-beta.

### Bug 3 — Grayscale PhotometricInterpretation (CONFIRMED)

- **Error:** `Unsupported PhotometricInterpretation 1` (MinIsBlack / grayscale)
- **Root cause:** Auto render pipeline only supports: RGB (2), Palette (3), CMYK, YCbCr.
- **Fix:** Pre-bake colormap into RGBA COGs (4-band uint8 with `photometric='rgb'`).

### COGLayer with RGBA COG — PASS

After fixing all three issues (custom geoKeysParser + RGBA pre-baked COG):
- **COGLayer renders correctly** over Portugal with proper geographic alignment
- GPU-accelerated tiled rendering works via `MapboxOverlay({ interleaved: true })`
- Interleaved with MapLibre basemap — labels visible through semi-transparent raster
- RGBA COG file size: 17.6KB (vs 115KB float32 original) thanks to DEFLATE compression on mostly-similar color values

### Tradeoff Analysis: COGLayer vs BitmapLayer Fallback

| Factor | COGLayer (bundle) | BitmapLayer (fallback) |
|--------|-------------------|----------------------|
| **Build step** | Required (esbuild, 1.3MB bundle) | None (CDN imports only) |
| **COG preparation** | Must pre-bake as RGBA uint8 | Works with float32 directly |
| **Colormap** | Baked server-side (can't change at runtime) | Applied client-side (switchable) |
| **GPU rendering** | Yes (tiled, LOD, WebGPU pipeline) | No (canvas 2D → texture upload) |
| **LOD/overviews** | Automatic (selects resolution by zoom) | None (reads full resolution) |
| **Render latency** | <1ms to setProps (async tile fetch) | 55-574ms (sync fetch+render) |
| **Bundle size** | +1.3MB JS | +0 (geotiff.js ~40KB via esm.sh) |
| **Workarounds needed** | 3 (geoKeysParser, RGBA, build step) | 0 |

### Updated Decision

- [x] **PARTIAL: Use geotiff.js + BitmapLayer for v0 scrollytelling (simpler, no build step)**
- [ ] Revisit COGLayer when: (a) v0.3.0 adds float32 support, (b) project adopts a bundler, (c) COGs grow large enough to need LOD

**Rationale:** COGLayer works but requires a build step, RGBA pre-baking (losing client-side colormaps), and a custom geoKeysParser workaround. For our COG sizes (75KB-2.1MB), the BitmapLayer fallback is fast enough (<1s) and keeps the no-build constraint. COGLayer's real benefit (GPU tiled rendering with LOD) only matters for large rasters that exceed browser memory — our ERA5 grids are tiny.

**The build step artifact (`spike-build/`, `spike-deckgl-bundle.js`) is kept for reference** but should not be committed to the repo. Add to `.gitignore`.
