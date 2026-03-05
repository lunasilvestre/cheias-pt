# P2 Track A: Core Systems (Opus)

## Run Context

- **Model:** Opus
- **Session budget:** ~2 hours
- **Branch:** `v2/phase-2` off `main`
- **Prerequisite:** Phase 1 complete (merged to main as d1088a8)

## Mission

Build the 4 rendering systems that every chapter needs. When this track completes,
a chapter can: load a COG and render it with a colormap, animate weather layers from
COGs, run a temporal player that auto-plays or scroll-drives, switch basemap mood,
show globe/terrain/3D columns.

**Read first:**
1. `CLAUDE.md`
2. `prompts/scroll-timeline-symbology.md` §0 (architecture) and §1 (basemap strategy)
3. `prompts/creative-direction-plan-v2.md` §1 (stack), §3 (WeatherLayers GL), §4 (3D), §5 (IVT)
4. `data/colormaps/palette.json` (12 colormaps, machine-readable)
5. `data/basemap/cheias-dark.json` (6 chapter basemap moods)
6. `data/basemap/IMPACT-GAUGE.md` (visual calibration targets)

**Existing code to understand before touching:**
- `src/main.ts` (202 lines) — chapter enter/leave orchestration
- `src/map-setup.ts` (138 lines) — MapLibre v5 + deck.gl MapboxOverlay init
- `src/layer-manager.ts` (528 lines) — 30+ layer definitions, sources, paint
- `src/scroll-engine.ts` (308 lines) — scrollama + Ch.3 scroll-driven frames
- `src/data-loader.ts` (27 lines) — JSON fetch + cache (needs COG extension)
- `src/chapters.ts` (239 lines) — 9 chapter configs
- `src/types.ts` (120 lines) — shared interfaces

---

## Session 1: P2.A1 — COG Rendering Pipeline

### What to Build

Extend `src/data-loader.ts` with client-side COG loading and colormapping:

```typescript
// New exports:
loadCOG(url: string): Promise<DecodedRaster>
  // geotiff.js HTTP range request → Float32Array + width + height + bounds
  // Handle nodata values (NaN, -9999, etc.)
  // Cache by URL

applyColormap(raster: DecodedRaster, paletteId: string): ImageData
  // Read palette.json at build time (import) or fetch once
  // Build Uint8ClampedArray RGBA from palette stops
  // Support types: sequential, diverging, categorical
  // Handle: domain mapping, nodata → transparent
  // Handle: alpha_mode "proportional" (precip) vs "fixed" (SST)

gaussianBlur(data: Float32Array, w: number, h: number, sigma: number): Float32Array
  // Separable 1D kernel convolution
  // Used for precipitation (blur_sigma: 3 in palette.json)
  // Apply BEFORE colormapping

rasterToImageBitmap(imageData: ImageData): Promise<ImageBitmap>
  // createImageBitmap() for deck.gl BitmapLayer
```

Extend `src/layer-manager.ts`:

```typescript
createRasterBitmapLayer(id: string, imageBitmap: ImageBitmap, bounds: Bounds): BitmapLayer
  // deck.gl BitmapLayer positioned at geographic bounds

crossfadeRasters(fromLayer: string, toLayer: string, duration: number): void
  // Dual-buffer A/B layers with opacity transition
  // Used for temporal frame advancement without pop
```

Add `src/types.ts`:

```typescript
interface DecodedRaster {
  data: Float32Array;
  width: number;
  height: number;
  bounds: [number, number, number, number]; // [west, south, east, north]
  nodata: number | null;
}

interface PaletteConfig {
  type: 'sequential' | 'diverging' | 'categorical';
  stops: [number, string][];
  domain: [number, number];
  alpha_mode?: 'proportional' | 'fixed';
  blur_sigma?: number;
}
```

### Data Sources

COGs served from R2:
```
SST:   https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/sst/2026-01-15.tif
IVT:   https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/ivt/2026-01-28.tif
MSLP:  https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/mslp/2026-01-28T06.tif
```

**CORS check first:** Before writing any code, verify R2 allows browser range requests:
```bash
curl -I -H "Origin: http://localhost:3000" \
  "https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/sst/2026-01-15.tif"
# Must see: Access-Control-Allow-Origin
# If blocked: document and use titiler proxy as fallback
```

### Verify

```typescript
// In browser console after npm run dev:
const { loadCOG, applyColormap, rasterToImageBitmap } = await import('./data-loader');
const raster = await loadCOG('https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/sst/2026-01-15.tif');
console.log(`${raster.width}x${raster.height}, bounds: ${raster.bounds}`);
const img = applyColormap(raster, 'sst-diverging');
console.log(`ImageData: ${img.width}x${img.height}, sample pixel RGBA: ${Array.from(img.data.slice(0, 4))}`);
// Should show blue-white-red pixels, not all zeros or all black
```

### Commit

`P2.A1: client-side COG rendering pipeline — geotiff.js + colormap + BitmapLayer`

---

## Session 2: P2.A2 — WeatherLayers GL Integration

### What to Build

Create `src/weather-layers.ts`:

```typescript
import { ParticleLayer, ContourLayer, HighLowLayer, GridLayer } from 'weatherlayers-gl';

// === Wind Particles ===
createWindParticles(windData: GeoTIFF): ParticleLayer
  // numParticles: 5000
  // maxAge: 100, speedFactor: 0.5
  // width: 2, color: [255, 255, 255, 200]
  // GPU-accelerated trail decay (comet-tail)
  // Impact Gauge target: density matching contact-wind-particles.png

// === MSLP Isobars ===
createIsobars(mslpData: GeoTIFF): ContourLayer
  // interval: 400 (4 hPa in Pa)
  // width: 1.5 (Impact Gauge: thick enough for bullseye pattern)
  // color: [255, 255, 255, 220]

// === H/L Pressure Labels ===
createPressureCenters(mslpData: GeoTIFF): HighLowLayer
  // radius: 500000 meters

// === Wind Barbs ===
createWindBarbs(windData: GeoTIFF): GridLayer
  // style: 'WIND_BARB'
  // density: 32 (px grid spacing)
  // color: [255, 255, 255, 180]

// === Batch Update ===
updateWeatherFrame(timestamp: string): Promise<WeatherLayerSet>
  // Load MSLP + wind-u + wind-v COGs for timestamp
  // Return all 4 layers configured with new data
  // Used by temporal player in Ch.4
```

Wire into `src/map-setup.ts`:
```typescript
// deck.gl MapboxOverlay accepts WeatherLayers GL layers alongside standard deck.gl layers
overlay.setProps({ layers: [...deckLayers, ...weatherLayers] });
```

### WeatherLayers GL API Notes

WeatherLayers GL uses GeoTIFF objects directly (geotiff.js ≥ 3.0). The pattern:
```typescript
import { fromUrl } from 'geotiff';
const tiff = await fromUrl(cogUrl);
const image = await tiff.getImage();

const particleLayer = new ParticleLayer({
  id: 'wind-particles',
  image: image,        // GeoTIFF image object, NOT decoded array
  imageType: 'VECTOR', // U/V encoded as 2-band GeoTIFF
  numParticles: 5000,
  maxAge: 100,
  speedFactor: 0.5,
  width: 2,
  color: [255, 255, 255, 200],
  animate: true,
});
```

**Important:** Check if WeatherLayers GL expects single-band or multi-band GeoTIFFs.
Our wind data is split into separate U and V files. May need to composite into a
single 2-band TIFF, or the library may accept separate U/V inputs.

If the library needs a 2-band TIFF and we have separate files, create a helper:
```typescript
compositeUV(uTiff: GeoTIFF, vTiff: GeoTIFF): Float32Array  // interleaved U,V
```

### Verify

Load Jan 28 06Z (Kristin peak). All 4 layers render simultaneously:
```
Wind U: .../cog/wind-u/2026-01-28T06.tif
Wind V: .../cog/wind-v/2026-01-28T06.tif
MSLP:   .../cog/mslp/2026-01-28T06.tif
```

- Particles flow cyclonically around the Kristin low
- Isobars form concentric rings (bullseye visible at 1.5px)
- H marker appears near Azores high, L marker near Kristin low
- Wind barbs show proper meteorological notation

### Commit

`P2.A2: WeatherLayers GL — particles, isobars, H/L markers, wind barbs from COGs`

---

## Session 3: P2.A3 — Chapter Temporal Player

### What to Build

The current `scroll-engine.ts` has a Ch.3-specific scroll-driven system. Generalize to
a reusable temporal player that any chapter can instantiate.

Create or refactor into `src/temporal-player.ts`:

```typescript
interface TemporalConfig {
  mode: 'autoplay' | 'scroll-driven';
  fps?: number;              // autoplay mode (2-8 fps depending on chapter)
  loop?: boolean;            // autoplay mode
  frameType: 'png' | 'cog' | 'weather-layers';
  frames: FrameSpec[];       // ordered by timestamp
  paletteId?: string;        // for COG frameType
}

interface FrameSpec {
  timestamp: string;         // ISO date or datetime
  urls: Record<string, string>;  // { mslp: '...', windU: '...', windV: '...' } or { png: '...' }
}

class TemporalPlayer {
  constructor(id: string, config: TemporalConfig);

  async load(): Promise<void>;
  // Preload ALL frames into memory/cache
  // For PNGs: fetch → ImageBitmap[]
  // For COGs: fetch → DecodedRaster[] (via P2.A1)
  // For weather-layers: fetch GeoTIFF objects (via P2.A2)

  play(): void;
  // requestAnimationFrame loop at config.fps
  // Calls onFrame callback per frame

  pause(): void;
  stop(): void;              // stop + reset to frame 0
  seek(index: number): void;
  setScrollProgress(progress: number): void;  // scroll-driven mode

  onFrame(cb: (frameData: FrameOutput, index: number, timestamp: string) => void): void;

  destroy(): void;
  // Cancel rAF, clear cache, remove references
  // CRITICAL: no orphaned loops after chapter exit
}
```

**Two modes:**

1. **AUTOPLAY** (Ch.2 IVT at 2fps, Ch.4 synoptic at 8fps):
   Chapter enters → `player.play()`. Chapter exits → `player.stop(); player.destroy()`.

2. **SCROLL-DRIVEN** (Ch.3 soil moisture):
   scrollama `onStepProgress` → `player.setScrollProgress(progress)`.
   Maps progress 0.0-0.9 → frame index 0-76.

**Chapter lifecycle in `src/main.ts`:**

```typescript
function onChapterEnter(chapterId: string, config: ResolvedChapter): void {
  // ... existing basemap/camera/layers ...

  if (config.temporal) {
    const player = new TemporalPlayer(chapterId, config.temporal);
    await player.load();

    if (config.temporal.mode === 'autoplay') {
      player.play();
    }

    player.onFrame((frameData, index, timestamp) => {
      // Update layers with frame data
      // Update date label
    });

    activePlayer = player;
  }
}

function onChapterExit(chapterId: string): void {
  activePlayer?.stop();
  activePlayer?.destroy();
  activePlayer = null;
}
```

**Pre-loading optimization:**
```typescript
// When user is 80% through current chapter, preload next chapter's frames
onStepProgress(chapterId, progress => {
  if (progress > 0.8 && nextChapter?.temporal) {
    preloadPlayer = new TemporalPlayer(nextChapterId, nextChapter.temporal);
    preloadPlayer.load(); // fire and forget
  }
});
```

Extend `src/chapters.ts` with temporal configs for chapters that use them:
```typescript
// Ch.2: IVT autoplay
{ id: 'chapter-2', temporal: { mode: 'autoplay', fps: 2, loop: true, frameType: 'cog', paletteId: 'ivt-sequential', frames: [...] } }

// Ch.3: SM scroll-driven (existing behavior, now generalized)
{ id: 'chapter-3', temporal: { mode: 'scroll-driven', frameType: 'png', frames: [...] } }

// Ch.4: synoptic autoplay (weather-layers)
{ id: 'chapter-4', temporal: { mode: 'autoplay', fps: 8, loop: true, frameType: 'weather-layers', frames: [...] } }
```

### Verify

1. Ch.3 scroll-driven SM still works exactly as before (regression test)
2. Create a test autoplay with 5 precip PNGs at 2fps — frames cycle, date label updates
3. Enter chapter → player starts. Exit → player stops. Re-enter → restarts from frame 0.
4. No orphaned rAF loops (check with `performance.getEntries()` or dev tools profiler)

### Commit

`P2.A3: generalized temporal player — autoplay + scroll-driven modes with preloading`

---

## Session 4: P2.A4 — Globe + Terrain + 3D Columns + Basemap Switching

### What to Build

Extend `src/map-setup.ts`:

```typescript
// === Globe ===
setProjection(proj: 'globe' | 'mercator'): void
  // map.setProjection(proj)
  // MapLibre v5 handles animated transition natively
  // Ch.2 enter → globe. Ch.3 enter → mercator.

// === Terrain ===
enableTerrain(exaggeration?: number): void
  // Default exaggeration: 1.5
  // Source: MapTiler terrain-rgb or MapLibre demo tiles
  // Ch.5 enter → enable. Ch.7 enter → disable.

disableTerrain(): void

// === Basemap Mood Switching ===
switchBasemapMood(mood: string): void
  // Read mood config from cheias-dark.json
  // Set map background color: map.setPaintProperty('background', 'background-color', mood.ocean)
  // Toggle label layer visibility
  // Toggle border layer visibility
  // Smooth transition (GSAP 300ms on background color)
```

Create discharge 3D columns in `src/layer-manager.ts`:

```typescript
import { ColumnLayer } from '@deck.gl/layers';

createDischargeColumns(stations: DischargeStation[], timestep?: string): ColumnLayer
  // getPosition: [lon, lat]
  // getElevation: peak_ratio × 5000 (Guadiana 11.5× towers over all)
  // getFillColor: ratio > 5 → [231,76,60,200] (red), else → [52,152,219,200] (blue)
  // radius: 4000, extruded: true
  // Visible in Ch.5 at scroll 0.8
```

Extend `src/chapters.ts`:

```typescript
// Add to each chapter config:
{ id: 'chapter-0', basemapMood: 'ultra-dark', ... }
{ id: 'chapter-2', basemapMood: 'dark-ocean', projection: 'globe', ... }
{ id: 'chapter-3', basemapMood: 'muted-terrain', projection: 'mercator', ... }
{ id: 'chapter-4', basemapMood: 'dark-synoptic', ... }
{ id: 'chapter-5', basemapMood: 'terrain-hydro', terrain: { exaggeration: 1.5 }, ... }
{ id: 'chapter-6', basemapMood: 'aerial-hybrid', terrain: { exaggeration: 1.5 }, ... }
{ id: 'chapter-7', basemapMood: 'dark-synoptic', terrain: false, ... }
```

Wire in `src/main.ts` `onChapterEnter`:
```typescript
switchBasemapMood(config.basemapMood);
if (config.projection) setProjection(config.projection);
if (config.terrain) enableTerrain(config.terrain.exaggeration);
else disableTerrain();
```

### Terrain Tile Source

```typescript
// Preferred: MapTiler (if key exists in .env)
const terrainUrl = `https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key=${MAPTILER_KEY}`;

// Fallback: MapLibre demo tiles (lower res, no key needed)
const terrainUrl = 'https://demotiles.maplibre.org/terrain-tiles/tiles.json';
```

### Verify

1. Scroll Ch.0→Ch.2: background shifts #060e14 → #0a212e, map switches to globe
2. Scroll Ch.2→Ch.3: smooth globe→mercator transition (~1s)
3. Scroll to Ch.5: terrain appears, river valleys visible as depressions
4. Ch.5 scroll 0.8: ColumnLayer appears. Guadiana column visibly tallest.
5. Scroll to Ch.7: terrain disabled, flat national view

### Commit

`P2.A4: globe projection, terrain, 3D columns, basemap mood switching`

---

## Track A Definition of Done

When all 4 sessions complete, verify this checklist:

- [ ] `loadCOG()` fetches any COG from R2 and returns Float32Array + bounds
- [ ] `applyColormap()` works for all 12 palettes in palette.json
- [ ] `gaussianBlur()` produces visibly smoothed output (test with precip COG)
- [ ] BitmapLayer renders a colormapped COG on the map at correct position
- [ ] WeatherLayers GL ParticleLayer shows flowing wind particles from U/V COGs
- [ ] ContourLayer shows MSLP isobars at 4hPa intervals, 1.5px white
- [ ] HighLowLayer marks H/L at correct pressure extrema positions
- [ ] GridLayer shows proper wind barb notation
- [ ] All 4 weather layers render simultaneously without conflicts
- [ ] TemporalPlayer autoplay mode cycles frames at specified fps
- [ ] TemporalPlayer scroll-driven mode maps scroll progress to frame index
- [ ] Player.destroy() leaves no orphaned rAF loops
- [ ] Pre-loading triggers at 80% scroll progress through current chapter
- [ ] Globe projection renders in Ch.2
- [ ] Globe→mercator transition is smooth (~1s)
- [ ] Terrain renders with hillshade in Ch.5
- [ ] ColumnLayer shows extruded discharge columns at station positions
- [ ] Basemap mood switches per chapter (6 moods, background colors match cheias-dark.json)
- [ ] `npm run build` succeeds with zero TypeScript errors
- [ ] Dev server (`npm run dev`) renders all systems without console errors

## After Track A

Track B (Chapter Implementation) is a separate prompt at `prompts/P2-B-chapters.md`.
It assumes all Track A deliverables exist and are working.
