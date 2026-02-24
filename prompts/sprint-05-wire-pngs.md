# Sprint 05 — Wire Raster Surfaces into Scrollytelling

## What This Is

Sprint 04 generated 154 pre-rendered PNG frames (77 soil moisture + 77 precipitation) with proper color ramps, cubic interpolation, and transparent Portugal masking. COGs for both variables are deployed to R2 and served by `titiler.cheias.pt`. This sprint wires both into the scrollytelling:

- **Chapters 3, 4, 5, 7 (scroll-driven narrative):** Pre-rendered PNGs via MapLibre `image` sources — latency-critical animation needs 0ms frame swaps from browser cache
- **Chapter 9 (explore mode):** titiler dynamic tiles via MapLibre `raster` tile sources — user-controlled pan/zoom needs server-rendered tiles at any viewport

This is the single highest-impact change remaining. It transforms Ch3 and Ch4 from "uniform blue dots" and "static orange dots" into smooth, animated weather-map-quality surfaces — the visual backbone of the entire narrative. And it makes Ch9 actually functional with live raster data at any zoom level.

### Why Two Approaches (Not Just titiler)

For scroll-driven animation at 5-15 effective fps, each frame swap via titiler means ~6 tile requests → titiler reads COG from R2 → renders → returns. At 100-200ms per tile round-trip, users see tile-loading shimmer instead of smooth animation. Pre-rendered PNGs swap from browser cache in ~0ms.

For free exploration where users pan/zoom to arbitrary viewports, pre-rendered PNGs are fixed at one resolution and extent. titiler dynamically renders COG tiles at whatever zoom the user navigates to.

This hybrid (pre-rendered for narrative, dynamic for exploration) is the pattern DevSeed uses in production. It demonstrates understanding of when each approach is appropriate.

### titiler Infrastructure (Already Deployed)

```
Base URL: https://titiler.cheias.pt
COG storage: https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/

Example tile:
https://titiler.cheias.pt/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png
  ?url=https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/soil-moisture/2026-01-28.tif
  &colormap_name=blues
  &rescale=0,0.55

Variables on R2:
  cog/soil-moisture/{date}.tif   (77 files, EPSG:4326, float32, deflate)
  cog/precipitation/{date}.tif   (77 files, EPSG:4326, float32, deflate)
```

## Context You Must Read

Before writing any code, read these files to understand the current state and what went wrong:

```
FORENSIC-REPORT.md      # Full gap analysis — especially Phase 4 (specific failures) and Phase 6 (root causes)
QA-AESTHETICS.md        # Visual issues per chapter — Issues #4 and #5 are what we're fixing
QA-DIAGNOSTICS.md       # Condensed issue log — systemic patterns S1-S3 are the target
```

Then read the current source files you'll be modifying:

```
src/layer-manager.js    # LAYER_DEFS, ensureLayer(), updateSourceData()
src/chapter-wiring.js   # enterChapter3(), enterChapter4(), enterChapter5()
src/data-loader.js      # JSON fetchers + cache
src/temporal-player.js  # scroll-progress → frame-index mapper
src/story-config.js     # chapter layer assignments
src/main.js             # chapter enter/leave orchestration
src/exploration-mode.js # TOGGLE_LAYER_MAP for Ch9
```

And the raster manifest from Sprint 04:

```
data/frontend/raster-manifest.json
```

## The Technique: MapLibre Image Sources

MapLibre GL JS has an `image` source type designed for exactly this use case: georeferenced raster overlays. The API:

```javascript
// Add an image source (once, on layer setup)
map.addSource('soil-moisture-raster', {
  type: 'image',
  url: 'data/raster-frames/soil-moisture/2025-12-01.png',
  coordinates: [
    [-9.6, 42.2],   // top-left     [west, north]
    [-6.1, 42.2],   // top-right    [east, north]
    [-6.1, 36.9],   // bottom-right [east, south]
    [-9.6, 36.9],   // bottom-left  [west, south]
  ]
});

// Add a raster layer that renders the image source
map.addLayer({
  id: 'soil-moisture-raster',
  type: 'raster',
  source: 'soil-moisture-raster',
  paint: { 'raster-opacity': 0 }
});

// To animate: swap the image URL (browser cache handles repeated loads)
map.getSource('soil-moisture-raster').updateImage({
  url: 'data/raster-frames/soil-moisture/2026-01-15.png'
});
```

The `coordinates` array uses the four corners in order: top-left, top-right, bottom-right, bottom-left. The manifest's `bounds` field is `[west, south, east, north]` = `[-9.6, 36.9, -6.1, 42.2]`.

**Critical:** `updateImage()` only changes the URL. It triggers a network fetch but the browser cache will serve previously-loaded frames instantly. The coordinates stay fixed.

## What To Build

### 1. Add manifest loader to `data-loader.js`

```javascript
export const loadRasterManifest = () => loadJSON('data/frontend/raster-manifest.json');
```

### 2. Add image source layer definitions to `layer-manager.js`

Add two new entries to `LAYER_DEFS` for the narrative chapters:

```javascript
'soil-moisture-raster': {
  type: 'raster',
  imageSource: true,  // flag for special handling in ensureLayer
  bounds: [-9.6, 36.9, -6.1, 42.2],  // [west, south, east, north]
  initialUrl: 'data/raster-frames/soil-moisture/2025-12-01.png',
  paint: { 'raster-opacity': 0, 'raster-fade-duration': 0 },
},
'precipitation-raster': {
  type: 'raster',
  imageSource: true,
  bounds: [-9.6, 36.9, -6.1, 42.2],
  initialUrl: 'data/raster-frames/precipitation/2025-12-01.png',
  paint: { 'raster-opacity': 0, 'raster-fade-duration': 0 },
},
```

**Important:** Set `raster-fade-duration: 0` to prevent MapLibre's default tile-loading crossfade, which would make frame swaps look blurry.

And two entries for the titiler-backed explore mode:

```javascript
'soil-moisture-tiles': {
  type: 'raster',
  tileSource: true,  // flag for special handling in ensureLayer
  tiles: [
    'https://titiler.cheias.pt/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png'
    + '?url=https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/soil-moisture/2026-01-28.tif'
    + '&colormap_name=ylgnbu&rescale=0.05,0.50&return_mask=true'
  ],
  tileSize: 256,
  attribution: 'Soil moisture: Open-Meteo / ERA5-Land',
  paint: { 'raster-opacity': 0 },
},
'precipitation-tiles': {
  type: 'raster',
  tileSource: true,
  tiles: [
    'https://titiler.cheias.pt/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png'
    + '?url=https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/precipitation/2026-02-06.tif'
    + '&colormap_name=ylorrd&rescale=1,80&return_mask=true'
  ],
  tileSize: 256,
  attribution: 'Precipitation: Open-Meteo / ERA5',
  paint: { 'raster-opacity': 0 },
},
```

**Colormap choices:** `ylgnbu` (yellow-green-blue) for soil moisture gives the dry-to-saturated progression. `ylorrd` (yellow-orange-red) for precipitation gives the storm-intensity signal. `return_mask=true` ensures transparent pixels outside the COG data extent (no black ocean tiles).

**rescale values:** Soil moisture raw range is ~0.05-0.50 m³/m³. Precipitation range 1-80 mm/day captures the meaningful signal without washing out lighter rain.

**Default dates:** `2026-01-28.tif` (pre-Kristin saturation peak) for soil moisture, `2026-02-06.tif` (Leonardo peak day) for precipitation. These are baked into the tile URL — the user sees the most dramatic frame when they toggle the layer on.

Update `ensureLayer()` to handle both the `imageSource` and `tileSource` flags:

```javascript
// Handle pre-rendered image sources (for scroll-driven narrative chapters)
if (def.imageSource) {
  const [west, south, east, north] = def.bounds;
  if (!map.getSource(sourceId)) {
    map.addSource(sourceId, {
      type: 'image',
      url: def.initialUrl,
      coordinates: [
        [west, north],  // top-left
        [east, north],  // top-right
        [east, south],  // bottom-right
        [west, south],  // bottom-left
      ]
    });
  }
  if (!map.getLayer(layerId)) {
    map.addLayer({
      id: layerId,
      type: 'raster',
      source: sourceId,
      paint: { ...def.paint },
    });
  }
  registeredLayers.add(layerId);
  return;  // early return — skip the normal source/layer creation
}

// Handle titiler tile sources (for explore mode)
if (def.tileSource) {
  if (!map.getSource(sourceId)) {
    map.addSource(sourceId, {
      type: 'raster',
      tiles: def.tiles,
      tileSize: def.tileSize || 256,
      attribution: def.attribution || '',
    });
  }
  if (!map.getLayer(layerId)) {
    map.addLayer({
      id: layerId,
      type: 'raster',
      source: sourceId,
      paint: { ...def.paint },
    });
  }
  registeredLayers.add(layerId);
  return;
}
```

### 3. Add an `updateImageSource()` export to `layer-manager.js`

```javascript
/**
 * Update the URL of an image source (for raster frame animation).
 * @param {maplibregl.Map} map
 * @param {string} layerId
 * @param {string} url - New image URL
 */
export function updateImageSource(map, layerId, url) {
  const sourceId = `source-${layerId}`;
  const source = map.getSource(sourceId);
  if (source && typeof source.updateImage === 'function') {
    source.updateImage({ url });
  }
}
```

### 4. Rewrite `enterChapter3()` in `chapter-wiring.js`

The current Ch3 loads `soil-moisture-frames.json` (3.8 MB of GeoJSON points), converts each frame to GeoJSON, and pushes it through `updateSourceData()`. Replace this with:

```javascript
export async function enterChapter3() {
  if (!map) return;

  // Load the manifest (cached after first load)
  const manifest = await loadRasterManifest();
  const smFrames = manifest.soil_moisture.frames;

  // Ensure the raster layer exists
  ensureLayer(map, 'soil-moisture-raster');

  // Set frames for temporal player (just the frame metadata, not the heavy GeoJSON)
  setFrames(smFrames);

  // Preload first batch of images into browser cache
  preloadImages(smFrames.slice(0, 15));

  onFrame((frame, idx) => {
    if (!map) return;
    updateImageSource(map, 'soil-moisture-raster', `data/${frame.url}`);
    updateDateLabel(frame.date);
    // Preload ahead: load the next 10 frames beyond current position
    preloadImages(smFrames.slice(idx + 1, idx + 11));
  });

  // Show first frame
  if (smFrames.length > 0) {
    updateImageSource(map, 'soil-moisture-raster', `data/${smFrames[0].url}`);
    updateDateLabel(smFrames[0].date);
  }

  onChapterProgress('chapter-3', (progress) => {
    setProgress(progress);
  });

  showDateLabel();
  ch3Initialized = true;
}
```

**URL note:** The manifest URLs are relative to `data/` (e.g., `raster-frames/soil-moisture/2025-12-01.png`). Prepend `data/` when passing to `updateImageSource()`, since the frontend serves from the project root.

### 5. Rewrite `enterChapter4()` similarly

Same pattern, using `manifest.precipitation.frames` and `precipitation-raster` layer.

### 6. Add a `preloadImages()` helper to `chapter-wiring.js`

```javascript
const preloadedUrls = new Set();

function preloadImages(frames) {
  for (const frame of frames) {
    const url = `data/${frame.url}`;
    if (preloadedUrls.has(url)) continue;
    preloadedUrls.add(url);
    const img = new Image();
    img.src = url;
  }
}
```

This creates `Image()` objects that the browser fetches and caches. When MapLibre later requests the same URL via `updateImage()`, it gets a cache hit.

### 7. Update `enterChapter5()` — frozen raster snapshot

Ch5 currently shows a `soil-moisture-snapshot` heatmap layer frozen at Jan 28. Replace this with a frozen raster frame:

```javascript
// In enterChapter5(), replace the soil-moisture-snapshot GeoJSON update with:
const manifest = await loadRasterManifest();
ensureLayer(map, 'soil-moisture-raster');
const jan28Frame = manifest.soil_moisture.frames.find(f => f.date === '2026-01-28');
if (jan28Frame) {
  updateImageSource(map, 'soil-moisture-raster', `data/${jan28Frame.url}`);
}
```

Update `story-config.js` chapter-5 layers to use `soil-moisture-raster` instead of `soil-moisture-snapshot`:

```javascript
// chapter-5 layers
{ id: 'soil-moisture-raster', opacity: 0.3, type: 'raster' },
```

### 8. Update `story-config.js` layer references

Replace heatmap layer IDs with raster layer IDs in chapter configs:

| Chapter | Old layer | New layer |
|---------|-----------|-----------|
| chapter-3 | `soil-moisture-animation` (heatmap) | `soil-moisture-raster` (raster) |
| chapter-4 | `precipitation-accumulation` (heatmap) | `precipitation-raster` (raster) |
| chapter-5 | `soil-moisture-snapshot` (heatmap) | `soil-moisture-raster` (raster) |
| chapter-7 | `precipitation-accumulation` (heatmap, 0.3 opacity) | `precipitation-raster` (raster, 0.3 opacity) |

**Do NOT remove** the old heatmap layer definitions from `LAYER_DEFS` yet — they may be useful as fallback. Just stop referencing them in `story-config.js`.

### 9. Wire titiler for Chapter 9 (Explore Mode)

Update `exploration-mode.js` to use the titiler tile layers:

```javascript
const TOGGLE_LAYER_MAP = {
  'flood-extent': { layers: ['flood-extent-polygons'], opacity: 0.7 },
  'soil-moisture': { layers: ['soil-moisture-tiles'], opacity: 0.6 },
  'precipitation': { layers: ['precipitation-tiles'], opacity: 0.6 },
  'discharge': { layers: ['glofas-discharge'], opacity: 0.9 },
  'precondition': { layers: ['basins-fill'], opacity: 0.7 },  // fix: was 'precondition-fill' which doesn't exist
  'basins': { layers: ['basins-outline'], opacity: 0.4 },
};
```

Add `enterChapter9()` to `chapter-wiring.js`:

```javascript
export async function enterChapter9() {
  if (!map) return;
  // Clean up any active temporal chapters
  if (ch3Initialized) leaveChapter3();
  if (ch4Initialized) leaveChapter4();

  // Ensure titiler tile layers exist (they'll be toggled by exploration-mode.js)
  ensureLayer(map, 'soil-moisture-tiles');
  ensureLayer(map, 'precipitation-tiles');
  ensureLayer(map, 'flood-extent-polygons');
  ensureLayer(map, 'glofas-discharge');
  ensureLayer(map, 'basins-outline');
}
```

Wire it from `main.js`:

```javascript
if (chapterId === 'chapter-9') enterChapter9();
```

### 10. Wire `main.js` cleanup

Update the `onChapterEnter` function to handle leaving chapters properly. The current code already handles `leaveChapter3/4` — just ensure the new raster-based functions use the same `ch3Initialized`/`ch4Initialized` guards.

Also add the `enterChapter9()` call when reaching Ch9.

## What To Keep

- `temporal-player.js` — **no changes needed**. It's already a generic scroll-progress → frame-index mapper. The only change is that the `frames` array now contains `{date, url}` objects from the manifest instead of `{date, points}` objects from the GeoJSON.
- `scroll-observer.js` — **no changes needed**. It provides the progress tracking that feeds the temporal player.
- The old GeoJSON data files (`soil-moisture-frames.json`, `precip-frames.json`, `precip-storm-totals.json`) — **keep them**. They may be useful for explore-mode analytics later. Just stop loading them in the temporal chapters.
- The old heatmap `LAYER_DEFS` entries — **keep them** but dormant. Remove from story-config references but don't delete the definitions.

## What NOT To Do

- Do NOT modify `temporal-player.js` or `scroll-observer.js` — they're correct and generic
- Do NOT delete old data files or old layer definitions
- Do NOT change camera positions, text content, or chapter structure
- Do NOT attempt to fix PMTiles flood extent rendering (separate sprint)
- Do NOT attempt to fix Ch7/Ch8 narrative misalignment (separate sprint)
- Do NOT add any npm dependencies — this is vanilla JS with CDN MapLibre
- Do NOT change the dev server setup (`scripts/serve.sh`)
- Do NOT touch `style.css` or `index.html`
- Do NOT configure CORS or deploy anything to titiler — it's already deployed and working

## Testing Protocol

After making changes, start the dev server and verify each chapter visually:

```bash
cd /home/nls/Documents/dev/cheias-pt
bash scripts/serve.sh  # or: python3 -m http.server 3001
```

### Visual verification checklist

Open `http://localhost:3001` and scroll through the story:

1. **Ch3 (Soil Moisture):** Should show a smooth brown → teal surface covering Portugal. As you scroll, the date label should advance Dec 1 → Feb 15 and the surface should visibly darken/shift from dry-brown (December) to saturated-teal (late January). **No dots. No grid pattern. No uniform blue.**

2. **Ch4 (Precipitation):** Should show transparent-to-yellow-to-red pulses. Dry days should be nearly invisible (transparent PNG). Storm days (Jan 28-30 for Kristin, Feb 5-7 for Leonardo, Feb 10-11 for Marta) should show intense orange/red over Portugal. **Three distinct storm pulses should be visible as you scroll.**

3. **Ch5 (Rivers):** Should show the soil moisture raster frozen at Jan 28 at low opacity (0.3) behind the discharge circles and river labels. Verify the raster doesn't animate (it's a snapshot, not scroll-driven).

4. **Ch7 (Synthesis):** Should show the precipitation raster at low opacity (0.3) as background context behind flood extent and consequence markers.

5. **Ch9 (Explore):** Toggle "Humidade do solo" and "Precipitação" checkboxes. Each should show/hide **titiler-backed tile layers** that render dynamically. Zoom in to a specific river basin — tiles should load at higher resolution. Zoom out to all of Portugal — tiles should load at lower resolution. This is the titiler payoff.

### Console verification

Open browser devtools console. Look for:
- No `Failed to load` errors for PNG URLs (Ch3/Ch4)
- No `updateImage is not a function` errors
- No CORS errors on titiler tile requests (Ch9)
- Image source URLs in Network tab should show 200 responses, ~150KB each
- Titiler tile requests should show 200 responses with `image/png` content type

### Performance check

- Scroll Ch3 at moderate speed. Frames should swap smoothly without visible "loading" flicker
- Open Network tab: after scrolling through Ch3 fully, ~77 PNG requests should show, most from cache on re-scroll
- Memory: each PNG is ~150KB RGBA. 77 frames = ~12MB in browser cache — acceptable
- Ch9 titiler tiles: expect ~100-300ms per tile on first load, then cached by browser

## File Modification Summary

| File | Changes |
|------|---------|
| `src/data-loader.js` | Add `loadRasterManifest()` export |
| `src/layer-manager.js` | Add 4 raster LAYER_DEFS (2 image + 2 tile), update `ensureLayer()` for both source types, add `updateImageSource()` export |
| `src/chapter-wiring.js` | Rewrite `enterChapter3/4/5()` to use image sources, add `preloadImages()`, add `enterChapter9()` |
| `src/story-config.js` | Swap heatmap layer IDs for raster layer IDs in chapters 3, 4, 5, 7 |
| `src/main.js` | Wire `enterChapter9()` call |
| `src/exploration-mode.js` | Update TOGGLE_LAYER_MAP to use titiler tile layers, fix precondition toggle |

## Success Criteria

1. Ch3 renders a smooth continuous surface (no dots) that animates brown → teal on scroll
2. Ch4 renders transparent dry days and vivid storm pulses that animate on scroll
3. Ch5 shows a frozen soil moisture raster at low opacity
4. Ch7 shows a frozen precipitation raster at low opacity
5. Ch9 toggles show/hide **titiler-backed tile layers** that render at any zoom level
6. No console errors related to image sources, updateImage, or missing PNGs
7. Frame transitions are smooth at normal scroll speed (no visible loading delay)
8. Date label updates correctly in Ch3 and Ch4 as scroll progresses
9. Ch9 tiles load correctly when user pans/zooms to arbitrary viewports
10. All existing functionality (PMTiles, consequence markers, camera transitions) unchanged

## Architecture Diagram

```
BEFORE (Sprint 02 — broken):
  scroll-observer → temporal-player → chapter-wiring
    → loadSoilMoistureFrames() [3.8 MB JSON]
    → pointsToGeoJSON() [342 points → GeoJSON]
    → updateSourceData() [pushes to MapLibre GeoJSON source]
    → heatmap layer renders 342 dots as blurry circles

AFTER (Sprint 05 — hybrid raster architecture):

  NARRATIVE CHAPTERS (Ch3, Ch4, Ch5, Ch7):
    scroll-observer → temporal-player → chapter-wiring
      → loadRasterManifest() [1 KB JSON, cached]
      → updateImageSource() [swaps PNG URL on MapLibre image source]
      → raster layer renders pre-rendered smooth surface
      → preloadImages() [background-loads upcoming frames into browser cache]

  EXPLORE CHAPTER (Ch9):
    user pan/zoom → MapLibre tile requests
      → titiler.cheias.pt/cog/tiles/{z}/{x}/{y}.png?url={R2 COG}
      → titiler reads COG from R2, applies colormap + rescale
      → returns rendered 256×256 tile
      → raster layer renders dynamic tiles at any viewport
```

The narrative chapters use pre-rendered PNGs for 0ms frame swaps during scroll animation. The explore chapter uses titiler for dynamic server-side rendering at arbitrary zoom levels. Both source from the same underlying data (Sprint 04 COGs on R2).
