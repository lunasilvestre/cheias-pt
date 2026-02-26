# Prompt B — Cloud-Native Rasters: COG-from-R2 + Satellite + MSLP

## Context

You are working on `deckgl-prototype.html` in the `cheias.pt` project — a flood monitoring
scrollytelling platform for Portugal. This is a **DevSeed portfolio piece** demonstrating
cloud-native geospatial skills.

**Architecture decision (from spike testing):** We load COGs directly from Cloudflare R2 using
`geotiff.js`, apply colormaps client-side via canvas, and render with deck.gl `BitmapLayer`.
No tiling service needed for rendering. This was validated in `spike-deckgl-raster.html`.

Read `deckgl-prototype.html` first to understand the current code.
Read `spike-deckgl-raster.html` for the **proven pattern** — specifically the `renderCOGToCanvas()`
function and the colormap LUT approach. Use this as reference; do not reinvent.
Read `data/video-analysis/MOTION-ANALYSIS.md` → Effects 2, 3, 4 for visual specs.

## Infrastructure

- **R2 public URL:** `https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/{layer}/{date}.tif`
- **geotiff.js:** Load via `import('https://esm.sh/geotiff@2.1.3')` (dynamic ESM import, proven in spike)
- **Rendering:** `geotiff.js` → canvas colormap → deck.gl `BitmapLayer` via `MapboxOverlay`
- **Temporal switching:** ~55ms cached, ~1s cold (proven in spike). Pre-fetch makes this smooth.

## COG Inventory on R2

| Layer | Path | Count | Temporal | Bounds |
|-------|------|-------|----------|--------|
| soil-moisture | `cog/soil-moisture/YYYY-MM-DD.tif` | 77 | Daily | [-9.6, 36.9, -6.1, 42.2] |
| precipitation | `cog/precipitation/YYYY-MM-DD.tif` | 77 | Daily | [-9.6, 36.9, -6.1, 42.2] |
| satellite-ir | `cog/satellite-ir/YYYY-MM-DDTHH-00.tif` | 49 | Hourly | Wider (check bbox) |
| mslp | `cog/mslp/YYYY-MM-DDTHH.tif` | 409 | 6-hourly | Wider Atlantic extent |
| sst | `cog/sst/YYYY-MM-DD.tif` | 77 | Daily | Atlantic extent |
| ivt | `cog/ivt/YYYY-MM-DD.tif` | 77 | Daily | Atlantic extent |
| precondition | `cog/precondition/YYYY-MM-DD.tif` | 77 | Daily | [-9.6, 36.9, -6.1, 42.2] |

## Task 1: Replace Local PNG Sources with COG-from-R2

Migrate soil moisture and precipitation from local PNG `image` sources to the COG pipeline:

1. **Add geotiff.js loader.** At the top of the script, add a lazy-load pattern:
   ```js
   let GeoTIFF = null;
   async function ensureGeoTIFF() {
     if (!GeoTIFF) {
       const mod = await import('https://esm.sh/geotiff@2.1.3');
       GeoTIFF = mod;
     }
     return GeoTIFF;
   }
   ```
   Call this during init so it starts loading immediately.

2. **Port the `renderCOGToCanvas()` function** from `spike-deckgl-raster.html`. This takes a
   COG URL, colormap function, and optional rescale range, and returns `{ canvas, bounds }`.
   Copy the function and the colormap LUT implementations (viridis, blues, IR thermal) from
   the spike file.

3. **Create a `RASTER_LAYERS` config:**
   ```js
   const R2_BASE = 'https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog';
   const RASTER_LAYERS = {
     'soil-moisture': {
       urlPattern: (date) => `${R2_BASE}/soil-moisture/${date}.tif`,
       colormap: bluesLUT,
       rescale: null, // auto-detect from data
       opacity: 0.8,
     },
     'precipitation': {
       urlPattern: (date) => `${R2_BASE}/precipitation/${date}.tif`,
       colormap: viridisLUT,
       rescale: null,
       opacity: 0.75,
     },
   };
   ```

4. **Replace the MapLibre image sources.** Remove the old `map.addSource('soil-moisture', { type: 'image' })` 
   and `map.addSource('precipitation', { type: 'image' })`. Instead, render rasters as deck.gl 
   `BitmapLayer`s. Update `buildDeckLayers()` to include raster layers alongside the existing
   ArcLayer and ScatterplotLayer.

5. **Update `setDate()`.** On date change:
   - Call `renderCOGToCanvas()` for each visible raster layer
   - Create `BitmapLayer` with the returned canvas and bounds
   - Update deck overlay via `setProps()`

6. **Pre-fetch cache.** Implement a simple LRU cache (Map with max ~10 entries) keyed by URL.
   Store the rendered `{ canvas, bounds }` result. On frame advance, also pre-fetch the NEXT
   frame into the cache. This makes play mode smooth (55ms cached switches).
   ```js
   const cogCache = new Map();
   const MAX_CACHE = 10;
   async function getCOGRendered(url, colormap, rescale) {
     if (cogCache.has(url)) return cogCache.get(url);
     const result = await renderCOGToCanvas(url, colormap, rescale);
     if (cogCache.size >= MAX_CACHE) {
       const oldest = cogCache.keys().next().value;
       cogCache.delete(oldest);
     }
     cogCache.set(url, result);
     return result;
   }
   ```

7. **Remove local PNG dependencies.** The `data/raster-frames/` directory is no longer needed
   for the prototype. All raster data comes from R2 COGs.

## Task 2: Satellite IR Layer

Add satellite infrared imagery as a new togglable animated layer:

1. **Add to layer panel:** Checkbox "Satellite IR" with dot color `#9b59b6`
2. **Add to RASTER_LAYERS config:**
   ```js
   'satellite-ir': {
     urlPattern: (date) => {
       // Satellite has hourly data for Jan 27-28 only
       // Map daily date to nearest available satellite frame
       if (date < '2026-01-27' || date > '2026-01-28') return null;
       return `${R2_BASE}/satellite-ir/${date}T12-00.tif`;
     },
     colormap: irLUT,
     rescale: null,
     opacity: 0.9,
     bounds: null, // read from COG bbox (wider than Portugal)
   },
   ```
3. **Temporal mapping:** When the main timeline is on Jan 27 or Jan 28, show the satellite frame.
   For other dates, hide the satellite layer (set opacity to 0 or skip rendering).
4. **Hour selector:** When satellite layer is active AND date is within range, show a small
   hour slider (0-23) that appears below the main timeline. This selects the hour suffix
   for the satellite URL pattern: `YYYY-MM-DDTHH-00.tif`
5. **Visual target (from MOTION-ANALYSIS):** Full opacity, dark ocean, white cloud structures.
   The comma cloud of Storm Kristin should be clearly visible. The IR thermal colormap (dark→purple→orange→white) from the spike works well.

## Task 3: MSLP Pressure Field

Add temporal MSLP as a new raster layer:

1. **Add to layer panel:** Checkbox "MSLP field" with dot color `#e67e22` (keep existing
   static MSLP contours as a separate toggle)
2. **Add to RASTER_LAYERS config:**
   ```js
   'mslp-field': {
     urlPattern: (date) => {
       // MSLP is 6-hourly: T00, T06, T12, T18
       return `${R2_BASE}/mslp/${date}T12.tif`;
     },
     colormap: mslpLUT, // new colormap: blue(low)→white(1013)→red(high)
     rescale: [98000, 104000], // Pascals
     opacity: 0.6,
     bounds: null, // wider Atlantic extent, read from COG
   },
   ```
3. **Create `mslpLUT` colormap:** Diverging blue→white→red centered around ~101300 Pa (1013 hPa).
   Blue = deep low pressure, red = high pressure, white = neutral. This matches the MOTION-ANALYSIS
   Effect 3 visual spec (temperature-like rdbu appearance).
4. **6-hourly resolution:** Add a small selector (00/06/12/18 UTC) that appears when MSLP field
   is active, similar to the satellite hour slider. Default to T12.
5. **Layering:** MSLP field renders BELOW the existing static MSLP contour lines. The contours
   provide isobar labels on top of the colored pressure field.

## Task 4: Crossfade for COG Layers

Implement smooth crossfade when switching dates (replaces the hard swap):

1. **Dual-layer technique:** For each raster type, maintain TWO BitmapLayers: `layer-a` and `layer-b`
2. **On date change:**
   - Render new COG into the INACTIVE layer
   - Animate opacity: active 0.8→0, inactive 0→0.8 over 400ms
   - Flip active flag
3. **Implementation:** Use `requestAnimationFrame` loop. Since deck.gl layers are immutable,
   rebuild the full layer array each frame with updated opacity values:
   ```js
   function animateCrossfade(layerA, layerB, duration, callback) {
     const start = performance.now();
     function frame() {
       const t = Math.min((performance.now() - start) / duration, 1);
       const eased = t * t * (3 - 2 * t); // smoothstep
       // Update layer opacities via deck setProps
       rebuildDeckLayers({ fadeProgress: eased });
       if (t < 1) requestAnimationFrame(frame);
       else callback();
     }
     requestAnimationFrame(frame);
   }
   ```
4. **During play mode:** If next frame is pre-cached, crossfade starts immediately.
   If still loading, show current frame until next is ready, then crossfade.

## Task 5: Colormap Selector

Add a UI dropdown to switch colormaps dynamically (showcases client-side rendering flexibility):

1. **Add panel** below camera presets: "Colormap" dropdown with options:
   viridis, blues, plasma, inferno, greys, thermal
2. **On change:** Re-render the current visible raster layer with the new colormap function
3. **Immediate feedback:** Since canvas re-rendering is ~10-20ms, this should be near-instant
4. **Implement additional LUTs:** plasma, inferno, greys (simple grayscale ramp)

## Task 6: Cloud-Native Attribution

Add attribution badges:

1. "Data: COG from Cloudflare R2" — small text, bottom-left
2. "Rendered with geotiff.js + deck.gl" — small text, below the first line
3. Style: 10px, `rgba(255,255,255,0.3)`, links to respective projects
4. This signals the cloud-native architecture to anyone inspecting the demo

## Constraints

- **Single HTML file** — all JS inline, external libs via CDN only
- **geotiff.js** loaded via `import('https://esm.sh/geotiff@2.1.3')` (dynamic ESM, proven)
- **deck.gl ^9.0** loaded via UMD from unpkg (existing `<script>` tag)
- **MapLibre GL ^4.0** (existing)
- **No build step** — must work with `python3 -m http.server` from project root
- **All raster data from R2** — no local `data/raster-frames/` references
- **Static GeoJSON vectors remain local** (rivers, discharge, lightning, wind barbs, storm tracks, MSLP contours)
- Preserve ALL existing functionality
- Dark glass panel aesthetic throughout

## Success Criteria

1. Open the page → geotiff.js loads from CDN, first raster renders from R2 COG
2. Scrub timeline → raster frames load and display with correct geographic placement
3. Hit play → frames crossfade smoothly (pre-cached frames at ~55ms, cold at ~1s)
4. Toggle "Satellite IR" on Jan 27 → Storm Kristin comma cloud visible
5. Toggle "MSLP field" → pressure patterns visible, evolving with date changes
6. Change colormap dropdown → immediate re-render with new colors
7. Browser DevTools Network tab shows range requests to `pub-abad2527698d4bbab82318691c9b07a1.r2.dev`
8. All existing vector layers (rivers, contours, discharge, lightning, arcs) still work
