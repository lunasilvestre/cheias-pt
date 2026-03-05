# Phase 2: Rendering + Temporal Players + Scroll Choreography

**Date:** 2026-02-27
**Supersedes:** Sprint backlog P2.A1-P2.B8 (task definitions carry forward, execution strategy updated)
**Status:** READY FOR EXECUTION
**Prerequisites:** Phase 1 complete (P1.A ✅, P1.B ✅, P1.C ✅)

---

## Starting Point Assessment

Phase 0 from creative-direction-plan-v2 is **already done**:

| Component | Status | Lines |
|-----------|--------|-------|
| Vite + TypeScript scaffold | ✅ Builds to dist/ | — |
| MapLibre v5 + deck.gl 9.2 MapboxOverlay | ✅ Basic init | 138 (map-setup.ts) |
| Scrollama + chapter system | ✅ Working | 308 (scroll-engine.ts) |
| GSAP animations | ✅ Hero, counters, chapter enters | 157 (animations.ts) |
| Chapter configs (9 chapters, cameras, layers) | ✅ Basic | 239 (chapters.ts) |
| Layer manager (sources, paint, opacity) | ✅ 30+ layer defs | 528 (layer-manager.ts) |
| CSS dark design system | ✅ Glassmorphism panels | 666 (style.css) |
| Data loader (JSON fetch + cache) | ✅ But JSON only | 27 (data-loader.ts) |
| PMTiles (flood extent, wildfires) | ✅ Protocol registered | via layer-manager |
| Pre-rendered PNGs (SM + precip, blues) | ✅ P1.B5 | data/raster-frames/ |
| titiler endpoint for COG tiles | ✅ Running | titiler.cheias.pt |

**Total existing TypeScript:** 1,861 lines across 9 modules.

### What's Missing (the Phase 2 gap)

| Gap | Impact | Sprint task |
|-----|--------|-------------|
| **Client-side COG rendering** (geotiff.js → colormap → BitmapLayer) | Can't render SST, IVT, flood depth from COGs | P2.A1 |
| **WeatherLayers GL** (particles, isobars, wind barbs, H/L) | Ch.4 synoptic is static without this | P2.A2 |
| **General temporal player** (chapter-local, preload, crossfade) | Only Ch.3 has scroll-driven frames, rest are static | P2.A3 |
| **Basemap mood switching** per chapter | Same dark basemap everywhere | P2.A4 |
| **Globe projection** for Ch.2 | Flat Atlantic, no planetary scale | P2.A4 |
| **Terrain** for Ch.5-6 | No 3D river valleys or flood plains | P2.A4 |
| **3D ColumnLayer** for Ch.5 discharge | No extruded discharge columns | P2.A4 |
| **Sub-chapter system** (Ch.4 × 4, Ch.6 × 4) | No storm-by-storm or location-by-location progression | P2.B4, P2.B6 |
| **Detailed chapter content** | Chapters show basic layers, not the full symbology stack | P2.B1-B8 |

---

## Execution Strategy

### Why Not Agent Teams for Phase 2

Phase 1 parallelized well because agents wrote to **separate output directories** — zero
file conflicts. Phase 2 is different: every chapter touches shared files:

- `main.ts` — chapter enter/leave callbacks
- `scroll-engine.ts` — temporal player wiring
- `layer-manager.ts` — layer definitions and sources
- `chapters.ts` — chapter configs
- `types.ts` — shared interfaces

Two agents editing `layer-manager.ts` simultaneously = merge hell.

### The Pattern: Sequential Focused Sessions

Each session is a **single Claude Code run** targeting one deliverable. Sessions build on
each other. The branch is `v2/phase-2` throughout.

```
Week 1 (Core Systems):
  Session 1: P2.A1 + P2.A4-basemap  (COG pipeline + basemap switching)
  Session 2: P2.A2                   (WeatherLayers GL integration)
  Session 3: P2.A3                   (temporal player system)
  Session 4: P2.A4-3d               (globe + terrain + columns)

Week 2 (Chapters):
  Session 5:  P2.B1 + P2.B3         (Ch.0-1 hook + Ch.3 soil moisture)
  Session 6:  P2.B2                  (Ch.2 Atlantic globe)
  Session 7:  P2.B4                  (Ch.4 storms — THE MONSTER)
  Session 8:  P2.B5 + P2.B6         (Ch.5 rivers + Ch.6 consequences)
  Session 9:  P2.B7 + P2.B8         (Ch.7 reveal + Ch.8-9 exploration)

Week 3 (Integration):
  Session 10: P2.C1                  (end-to-end scroll test + polish)
```

**Sonnet for all sessions.** This is mechanical implementation from detailed specs, not
architecture design. Save Opus tokens for Phase 3 polish and creative decisions.

---

## Track A: Core Systems (Week 1)

### Session 1: P2.A1 + P2.A4-basemap — COG Pipeline + Basemap Switching

**Estimated:** 2-3 hours

**Why combined:** Both are infrastructure that every chapter needs. Neither is large
enough alone to fill a session. Basemap switching needs zero COG knowledge.

#### Part 1: COG Rendering Pipeline

**Read:** `data/colormaps/palette.json`, `prompts/scroll-timeline-symbology.md` §2

Extend `src/data-loader.ts`:

```typescript
// New functions:
loadCOG(url: string): Promise<DecodedRaster>
  // geotiff.js HTTP range request → Float32Array + width/height/bounds

applyColormap(raster: DecodedRaster, paletteId: string): ImageData
  // Lookup palette.json → build Uint8ClampedArray RGBA
  // Support: sequential, diverging, categorical
  // Handle nodata → transparent

gaussianBlur(data: Float32Array, w: number, h: number, sigma: number): Float32Array
  // Separable 1D kernel, used for precipitation

rasterToImageBitmap(imageData: ImageData): Promise<ImageBitmap>
  // For deck.gl BitmapLayer consumption
```

Extend `src/layer-manager.ts`:

```typescript
createRasterBitmapLayer(id: string, imageBitmap: ImageBitmap, bounds: Bounds): BitmapLayer
  // deck.gl BitmapLayer with given bounds

crossfadeRasters(layerA: string, layerB: string, progress: number): void
  // Dual-buffer opacity transition
```

**Verify:**
```
// In browser console after npm run dev:
import { loadCOG, applyColormap } from './data-loader'
const r = await loadCOG('https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/sst/2026-01-15.tif')
const img = applyColormap(r, 'sst-diverging')
// Should produce ImageData with blue-white-red pixels
```

#### Part 2: Basemap Mood Switching

**Read:** `data/basemap/cheias-dark.json`, `data/basemap/BASEMAP-DECISIONS.md`

Extend `src/map-setup.ts`:

```typescript
switchBasemapMood(mood: BasemapMood): void
  // Set canvas background color via map.setPaintProperty('background', 'background-color', ...)
  // Toggle label layers visibility
  // Toggle border layers visibility
  // Smooth transition (300ms CSS transition on background)
```

Extend `src/chapters.ts`:
```typescript
// Add basemapMood to each chapter config
{ id: 'chapter-0', basemapMood: 'ultra-dark', ... }
{ id: 'chapter-4', basemapMood: 'dark-synoptic', ... }
```

Wire in `src/main.ts` `onChapterEnter`:
```typescript
switchBasemapMood(config.basemapMood);
```

**Verify:** Scroll through chapters — background color changes per mood.
Canvas shifts from #060e14 (Ch.0) → #0a212e (Ch.2) → #1a2a3a (Ch.3) → #080c10 (Ch.4).

**Commit:** `P2.A1+A4a: COG rendering pipeline + per-chapter basemap mood switching`

---

### Session 2: P2.A2 — WeatherLayers GL Integration

**Estimated:** 2-3 hours

**Read:** `prompts/scroll-timeline-symbology.md` §2 Ch.4a (all WeatherLayers specs),
`prompts/creative-direction-plan-v2.md` §3 (effect resolution)

Create `src/weather-layers.ts`:

```typescript
import { ParticleLayer, ContourLayer, HighLowLayer, GridLayer } from 'weatherlayers-gl';

// 1. Wind Particles
createWindParticles(windUTiff: GeoTIFF, windVTiff: GeoTIFF): ParticleLayer
  // numParticles: 5000 (configurable)
  // maxAge: 100, speedFactor: 0.5
  // White/cyan trails, 2px width
  // GPU-accelerated trail decay (the comet-tail effect)

// 2. MSLP Isobars
createIsobars(mslpTiff: GeoTIFF): ContourLayer
  // interval: 400 (4 hPa in Pa)
  // width: 1.5px, color: white 220 alpha
  // Per Impact Gauge: thick enough to see bullseye pattern

// 3. H/L Pressure Labels
createPressureCenters(mslpTiff: GeoTIFF): HighLowLayer
  // radius: 500000m search
  // Renders L/H at extrema automatically

// 4. Wind Barbs
createWindBarbs(windUTiff: GeoTIFF, windVTiff: GeoTIFF): GridLayer
  // style: 'WIND_BARB'
  // density: 32px grid spacing
  // white, 180 alpha
  // Proper meteorological notation from COGs

// Update function for temporal frames
updateWeatherLayers(timestamp: string): Promise<void>
  // Load MSLP + wind COGs for given timestamp
  // Update all 4 layers simultaneously
```

Wire into deck.gl MapboxOverlay in `src/map-setup.ts`:
```typescript
// WeatherLayers GL layers added to deck overlay alongside existing layers
overlay.setProps({ layers: [...existingLayers, ...weatherLayers] });
```

**Critical test:** Load Jan 28 06Z (Kristin peak). All 4 layers render simultaneously.
Particles flow cyclonically. Isobars form concentric rings. H/L markers appear at
correct positions. Wind barbs show proper meteorological notation.

**Data source:** COGs from R2 via geotiff.js (same pipeline as P2.A1).
```
Wind U: https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/wind-u/2026-01-28T06.tif
Wind V: https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/wind-v/2026-01-28T06.tif
MSLP:   https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/mslp/2026-01-28T06.tif
```

**Commit:** `P2.A2: WeatherLayers GL integration — particles, isobars, H/L, wind barbs`

---

### Session 3: P2.A3 — Chapter Temporal Player System

**Estimated:** 2-3 hours

**Read:** `prompts/scroll-timeline-symbology.md` §0 (architectural principle: scroll ≠ timeline)

The current `scroll-engine.ts` has a Ch.3-specific scroll-driven frame system. This
session generalizes it to a **chapter-local temporal player** that any chapter can use.

Rewrite temporal system in `src/scroll-engine.ts` (or new `src/temporal-player.ts`):

```typescript
interface TemporalPlayer {
  id: string;
  load(frames: FrameConfig[]): Promise<void>;  // preload all frames into memory
  play(fps: number, loop: boolean): void;
  pause(): void;
  stop(): void;
  seek(frameIndex: number): void;
  setScrollDriven(enabled: boolean): void;      // Ch.3 mode: scroll position → frame
  onFrame(cb: (frame: FrameData, index: number, timestamp: string) => void): void;
  destroy(): void;
}

// Two modes:
// 1. AUTOPLAY: Chapter enters → player.play(fps, loop). Used by Ch.2 (IVT), Ch.4 (synoptic).
// 2. SCROLL-DRIVEN: Scroll progress maps to frame index. Used by Ch.3 (soil moisture).

// Frame types:
// - PNG URL: pre-rendered image → MapLibre image source
// - COG URL: fetch + colormap → deck.gl BitmapLayer (via P2.A1 pipeline)
// - WeatherLayers: fetch COGs → update WeatherLayers GL layers (via P2.A2)
```

Chapter lifecycle:
```
scrollama onStepEnter(chapter):
  1. switchBasemapMood()
  2. flyToChapter()
  3. showChapterLayers()
  4. if chapter.temporal:
       player = createTemporalPlayer(chapter.temporal)
       await player.load(chapter.temporal.frames)
       player.play(chapter.temporal.fps, chapter.temporal.loop)

scrollama onStepExit(chapter):
  1. player?.stop()
  2. player?.destroy()
  3. hideChapterLayers()

// Pre-loading: when user is 80% through current chapter, start loading next chapter's frames
scrollama onStepProgress(chapter, progress):
  if progress > 0.8:
    preloadNextChapter()
```

Extend `src/types.ts`:
```typescript
interface TemporalConfig {
  mode: 'autoplay' | 'scroll-driven';
  fps?: number;           // autoplay mode
  loop?: boolean;
  frameType: 'png' | 'cog' | 'weather-layers';
  frames: FrameConfig[];  // ordered list of frame URLs + timestamps
  paletteId?: string;     // for COG frames
}
```

Extend `src/chapters.ts` with temporal configs:
```typescript
{ id: 'chapter-2', temporal: { mode: 'autoplay', fps: 2, loop: true, frameType: 'cog', frames: ivtFrames } }
{ id: 'chapter-3', temporal: { mode: 'scroll-driven', frameType: 'png', frames: smFrames } }
{ id: 'chapter-4', temporal: { mode: 'autoplay', fps: 8, loop: true, frameType: 'weather-layers', frames: synopticFrames } }
```

**Verify:** Ch.3 scroll-driven SM still works. Ch.4 autoplay triggers (even with
placeholder frames). Player destroys cleanly on chapter exit (no orphaned rAF loops).

**Commit:** `P2.A3: generalized chapter-local temporal player with autoplay + scroll-driven modes`

---

### Session 4: P2.A4-3d — Globe + Terrain + 3D Columns

**Estimated:** 2-3 hours

**Read:** `prompts/creative-direction-plan-v2.md` §4 (3D visualization)

Extend `src/map-setup.ts`:

```typescript
// Globe
setGlobeProjection(): void
  // map.setProjection('globe')
  // Triggered on Ch.2 enter

setMercatorProjection(): void
  // map.setProjection('mercator')
  // Triggered on Ch.3 enter (smooth animated transition)

// Terrain
enableTerrain(exaggeration: number): void
  // map.addSource('terrain', { type: 'raster-dem', url: terrainTileUrl })
  // map.setTerrain({ source: 'terrain', exaggeration })
  // Triggered on Ch.5 enter

disableTerrain(): void
  // map.setTerrain(null)
  // Triggered on Ch.7 enter

// 3D Discharge Columns
createDischargeColumns(stations: DischargeStation[], timestep: string): ColumnLayer
  // getPosition: [lon, lat]
  // getElevation: peak_ratio * 5000 (Guadiana towers at 11.5×)
  // getFillColor: ratio > 5 → red, else → blue
  // radius: 4000, extruded: true
```

**Terrain tile source:** MapTiler or MapLibre demo tiles:
```typescript
const terrainUrl = 'https://demotiles.maplibre.org/terrain-tiles/tiles.json';
// Or MapTiler if key available: `https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key=...`
```

**Verify:**
1. Ch.2: Globe renders. SST visible on curved ocean. Bearing rotates slowly.
2. Ch.2→Ch.3: Smooth globe→mercator transition (MapLibre v5 native).
3. Ch.5: Terrain visible. River valleys are physical depressions.
4. Ch.5: ColumnLayer at discharge stations. Guadiana column visibly tallest.
5. Ch.7: Terrain disabled. Flat national overview.

**Commit:** `P2.A4: globe projection, terrain, 3D discharge columns`

---

## Track B: Chapter Implementation (Week 2)

### Session 5: P2.B1 + P2.B3 — Hook (Ch.0-1) + Soil Moisture (Ch.3)

**Estimated:** 3-4 hours

**Why combined:** Ch.0-1 is simple (static layers + GSAP). Ch.3 is partially implemented
(scroll-driven SM exists in scroll-engine.ts). Together they're one session.

#### Ch.0: The Hook

**Read:** Scroll timeline §2 Ch.0

- Hero title: serif font, GSAP fade-in with letter stagger (exists in animations.ts)
- Dark Atlantic, no labels, no data
- Ghost flood pulse: combined.pmtiles at 3% opacity, slow 2s fade in/out, 8s loop
- Number ticker: "11 mortes. 69 municípios." (exists in animations.ts)

#### Ch.1: Flash-Forward

**Read:** Scroll timeline §2 Ch.1

- Flood extent PMTiles fade to 70% opacity
- Statistics text appears
- Transition text: "Para perceber como chegámos aqui..."
- On exit: flood fades to 0%, camera begins pulling to globe

#### Ch.3: Soil Moisture (upgrade existing)

**Read:** Scroll timeline §2 Ch.3

Existing scroll-driven SM player works. Upgrade with:
- Basin sparklines (Observable Plot) in side panel
- Date counter overlay (exists partially)
- Wildfire burn scars fade-in at scroll 0.5 (15% opacity, amber)
- Percentile annotation at scroll 0.7
- Precipitation underlay fading in at scroll 0.8 (transition to Ch.4)

**Commit:** `P2.B1+B3: chapters 0-1 hook + chapter 3 soil moisture with sparklines and wildfire foreshadow`

---

### Session 6: P2.B2 — The Atlantic Engine (Ch.2)

**Estimated:** 3-4 hours

**Read:** Scroll timeline §2 Ch.2, creative-direction-plan-v2 §4 (globe) and §5 (atmospheric river)

**The first high-impact 3D chapter.**

- Globe projection active (from P2.A4)
- SST anomaly raster (COG → colormap → BitmapLayer, sst-diverging palette)
- Storm track ArcLayer: 3 great circles from `data/qgis/storm-tracks-auto.geojson`
  - Named labels (Kristin, Leonardo, Marta) moving along arcs
  - deck.gl ArcLayer with `greatCircle: true`
- IVT temporal player: 77 daily frames at 2fps, loop (from P2.A3)
  - COG → ivt-sequential palette → BitmapLayer
  - Purple/white band = atmospheric river
- Wind particles: 2000 white trails flowing along AR corridor (from P2.A2)
  - Lower density than Ch.4 synoptic — atmospheric texture, not full synoptic
- Scroll 0.5: IVT crossfade from ERA5 0.5° → ECMWF HRES 0.1° (if available)
- Slight globe rotation (bearing 0→5 over chapter duration)
- On exit: globe→mercator transition, IVT fades, camera descends to Portugal

**Data:**
```
SST:        data/cog/sst/2026-01-15.tif (single representative frame)
IVT:        data/cog/ivt/*.tif (77 daily COGs)
Wind U/V:   data/cog/wind-u/*.tif, data/cog/wind-v/*.tif (use 6-hourly subset)
Storm arcs: data/qgis/storm-tracks-auto.geojson
```

**Commit:** `P2.B2: chapter 2 Atlantic engine — globe, SST, IVT temporal, storm arcs, wind particles`

---

### Session 7: P2.B4 — The Storms (Ch.4) — THE MONSTER

**Estimated:** 4-6 hours (largest single session)

**Read:** Scroll timeline §2 Ch.4a-4d (the most detailed section). Read ALL of it.
Also: `data/basemap/IMPACT-GAUGE.md` (calibration targets), `data/colormaps/palette.json`

**4 sub-chapters, 3 temporal players, 13-layer stack.**

This is where WeatherLayers GL earns its keep. The session implements:

#### Sub-chapter 4a: Kristin (scroll 0.0-0.3)

- Dark synoptic basemap (#080c10)
- Camera: `[-12, 43]` z5.5 p20
- Synoptic temporal player (hourly, 8fps, loop):
  - MSLP isobars (ContourLayer, 1.5px white, 4hPa)
  - H/L markers (HighLowLayer)
  - Wind particles (ParticleLayer, 5000, white/cyan)
  - Precipitation field (blues PNGs overlaid)
- IPMA warnings choropleth: yellow→orange during Kristin
- Satellite IR crossfade: replaces synoptic view when scrolled to 0.18
  - 48 hourly frames, 4fps, inverted grayscale
- Lightning ScatterplotLayer: yellow stars, flash animation
- Storm annotations: "CICLOGENESE EXPLOSIVA" text overlay

#### Sub-chapter 4b: Respite (scroll 0.3-0.4)

- Static: Jan 31 00Z MSLP field
- Discharge sparklines showing lag (river peaks AFTER storm passes)
- Text: "O pior já passou? Não."

#### Sub-chapter 4c: Leonardo (scroll 0.4-0.7)

- Synoptic temporal player: Feb 4-8 hourly (from P1.A1)
  - Same layer stack as 4a but new data
- IPMA warnings escalate to RED
- Frontal boundary: warm front (red, triangle markers) from `frontal-boundaries.geojson`
- Satellite IR: Feb 4-8 (from P1.A3)
- Camera push to `[-9, 40]` z7

#### Sub-chapter 4d: Marta (scroll 0.7-1.0)

- Tightest camera: `[-9, 39.5]` z7.5 p30
- Synoptic player: Feb 9-12 hourly (from P1.A1)
- Frontal boundary: cold front (blue, triangle markers)
- Full 13-layer composite at climax (scroll 0.9):
  ```
  Bottom → Top:
  1. Dark basemap
  2. Precipitation field (blues PNG)
  3. MSLP isobars (ContourLayer)
  4. H/L labels (HighLowLayer)
  5. Wind barbs (GridLayer) — appear at sub-chapter peaks only
  6. Frontal boundaries (MapLibre line + markers)
  7. Wind particles (ParticleLayer)
  8. IPMA warnings choropleth
  9. Lightning (ScatterplotLayer)
  10. Annotations
  ```
- Max 6-7 layers active simultaneously (visual hierarchy management)

#### Sub-chapter system

Extend scrollama to detect sub-chapter steps within Ch.4's scroll height:
```typescript
// Ch.4 is divided into 4 sub-chapters by scroll progress:
// 0.0-0.3 = Kristin, 0.3-0.4 = respite, 0.4-0.7 = Leonardo, 0.7-1.0 = Marta
onStepProgress('chapter-4', progress => {
  if (progress < 0.3) enterSubChapter('kristin');
  else if (progress < 0.4) enterSubChapter('respite');
  else if (progress < 0.7) enterSubChapter('leonardo');
  else enterSubChapter('marta');
});
```

Each sub-chapter transition: swap temporal player, adjust camera, update warnings.

**This is the session where the Impact Gauge matters most.** The dark synoptic basemap +
isobar weight + precipitation blues + particle density must match the WeatherWatcher14
reference. If the composite looks wrong, stop and adjust before proceeding.

**Commit:** `P2.B4: chapter 4 three storms — full synoptic composite with 4 sub-chapters`

---

### Session 8: P2.B5 + P2.B6 — Rivers (Ch.5) + Consequences (Ch.6)

**Estimated:** 4-5 hours

#### Ch.5: Rivers Respond

**Read:** Scroll timeline §2 Ch.5

- Terrain enabled (exaggeration 1.5, from P2.A4)
- Basemap mood: terrain + hydro (#1a2a3a, Portuguese labels)
- River network: `rivers-portugal.geojson` (width by Strahler order)
- Discharge stations: circle markers (size by peak ratio)
- Sequential camera: Tejo → Mondego → Sado → Guadiana
- Discharge temporal player (daily, Dec 1 → Feb 15, 3fps):
  - Station circles pulse with daily discharge
  - Sparklines update in side panel (Observable Plot)
- **3D columns at scroll 0.8** (from P2.A4):
  - ColumnLayer extruded at each station
  - Height = peak discharge ratio × 5000
  - Guadiana towers at 11.5× — the visual climax of Ch.5

**Data:**
```
Rivers:     data/qgis/rivers-portugal.geojson
Stations:   data/qgis/discharge-stations.geojson
Timeseries: data/frontend/discharge-timeseries.json
```

#### Ch.6: The Human Cost (4 sub-chapters)

**Read:** Scroll timeline §2 Ch.6a-6d

- Terrain + satellite/aerial basemap
- Intimate camera work (z10-13, p35-45)

**6a: Coimbra** — Flood extent (EMSR861 + EMSR864 overlap), consequence markers, z10
**6b: Lisboa region** — Setúbal + Sintra, consequence markers, z10
**6c: Salvaterra triptych** — THE signature moment:
  - 3 temporal flood extents (light→medium→dark blue, additive)
  - Flood depth COG overlay (flood-depth palette from P1.C2)
  - Sentinel-2 before/after with maplibre-gl-compare slider
  - Text: "Em 48 horas, as águas cresceram 58%"
**6d: National pull-back** — All 42 consequence markers visible, z6.5

**Data:**
```
Flood extent:  data/flood-extent/*.pmtiles
Flood depth:   data/flood-depth/*.tif
Sentinel-2:    data/sentinel-2/*.tif
Consequences:  data/consequences/events.geojson
```

**Commit:** `P2.B5+B6: chapters 5-6 — rivers with 3D columns + consequences with Salvaterra triptych`

---

### Session 9: P2.B7 + P2.B8 — Reveal (Ch.7) + Exploration (Ch.8-9)

**Estimated:** 2-3 hours

#### Ch.7: The Full Picture (Wildfire Reveal)

**Read:** Scroll timeline §2 Ch.7

The INTELLECTUAL PUNCHLINE. Sequential layer build:

1. Scroll 0.0: Basin boundaries (thin gray)
2. Scroll 0.2: Precipitation total COG (cumulative Dec-Feb, from P1.B4)
3. Scroll 0.4: Flood extent (blue, #2471a3)
4. Scroll 0.6: Consequence markers (all 42)
5. **Scroll 0.8: Burn scars** — amber (#c0631a) at 60% opacity
   - The spatial correlation between fire scars and flood areas becomes VISIBLE
   - Text: "Os incêndios de 2024 abriram o caminho às cheias de 2026"

Each new layer reduces previous opacity (progressive dimming). The fire→flood spatial
correlation must be immediately legible without explanation — if the user needs the text
to understand it, the visualization has failed.

**Verify against:** `data/colormaps/screenshots/ch7-reveal-test.png` from P1.C2.
Blue/amber contrast must be at least as clear as the QGIS composite test.

#### Ch.8-9: Analysis + Exploration

- Ch.8: Static basin risk assessment map + policy text. No temporal player.
- Ch.9: Unlock map interaction. Layer toggles. Geolocation button. Share URL with
  viewport state. This is the "now explore for yourself" moment.

**Commit:** `P2.B7+B8: chapter 7 wildfire reveal + chapters 8-9 exploration mode`

---

## Track C: Integration (Week 3)

### Session 10: P2.C1 — End-to-End Scroll Test + Polish

**Estimated:** 3-4 hours

**This is the QA session.** Scroll through the entire narrative and fix:

1. **Transition smoothness:** Every chapter enter/exit — no jank, no pop, no orphaned layers
2. **Temporal player lifecycle:** Enter chapter → player starts. Exit → player stops.
   No orphaned requestAnimationFrame loops. No stale layers from previous chapters.
3. **Camera choreography:** flyTo/easeTo durations feel natural. No sudden jumps.
4. **Text timing:** Text panels appear/disappear in sync with data reveals.
5. **Layer hierarchy:** Max 6-7 layers simultaneously. Opacity management prevents muddy composites.
6. **Globe→mercator transition:** Ch.2→Ch.3, smooth and fast (~1s).
7. **Terrain enable/disable:** Ch.5 enter → terrain appears. Ch.7 enter → terrain gone.
8. **Performance:** Measure FPS during Ch.4 synoptic composite (the heaviest chapter).
   Target: 30fps minimum on desktop. If below, reduce particle count or defer wind barbs.

**Deliverable:** A scrollable URL where the entire narrative works. Not polished, not
responsive, not accessible — but WORKS end-to-end.

**Commit:** `P2.C1: end-to-end scroll narrative integration and transition polish`

---

## Data Serving Strategy

All data accessed at runtime via HTTP:

| Data Type | Source | Pattern |
|-----------|--------|---------|
| Pre-rendered PNGs (SM, precip) | Vite public dir (dev) / static hosting (prod) | `data/raster-frames/soil-moisture/2025-12-01.png` |
| COGs (SST, IVT, MSLP, wind) | R2 public bucket | `https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/sst/2026-01-15.tif` |
| COG tiles (large rasters) | titiler | `https://titiler.cheias.pt/cog/tiles/...?url=...` |
| PMTiles (flood extent, wildfires) | Local / R2 | `data/flood-extent/combined.pmtiles` |
| GeoJSON (vectors) | Local | `data/qgis/storm-tracks-auto.geojson` |
| JSON (timeseries, manifests) | Local | `data/frontend/discharge-timeseries.json` |

**Before starting Phase 2:** Run `./data/cog/sync.sh push` to ensure all P1 COGs are on R2.
WeatherLayers GL needs direct GeoTIFF access — verify R2 CORS allows `geotiff.js` range requests.

---

## Risk Register

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| WeatherLayers GL + deck.gl 9.2 version conflict | Medium | Pin to WL's tested deck.gl version. If blocked, fall back to d3-contour + custom particles. |
| geotiff.js CORS issues with R2 | Medium | Verify CORS before Session 1. If blocked, proxy through titiler or Vite dev server. |
| Ch.4 13-layer composite drops below 30fps | High | Progressive: disable wind barbs first, reduce particles second, fall back to PNG-only third. |
| Globe projection + deck.gl overlay bugs | Low | deck.gl 9.2 officially supports MapLibre v5 MapboxOverlay. Well-tested path. |
| Sub-chapter scroll detection jitter | Medium | Debounce sub-chapter transitions (100ms). Hysteresis zone between sub-chapters. |
| Session 7 (Ch.4) exceeds Claude Code context | Medium | Split into 2 sessions: 4a+4b first, 4c+4d second. Commit between. |

---

## Definition of Done (Phase 2 Complete)

- [ ] COG → colormap → BitmapLayer pipeline works for all palettes
- [ ] WeatherLayers GL renders particles + isobars + H/L + wind barbs from COGs
- [ ] Temporal player: autoplay (Ch.2, Ch.4) and scroll-driven (Ch.3) both work
- [ ] Basemap mood switches per chapter (6 moods verified)
- [ ] Globe projection in Ch.2, smooth transition to mercator in Ch.3
- [ ] Terrain in Ch.5-6, disabled in Ch.7
- [ ] 3D ColumnLayer at discharge stations in Ch.5
- [ ] Ch.4 synoptic composite: ≥3 layers legible simultaneously at 30fps
- [ ] Ch.6c Salvaterra triptych: 3 flood stages + depth + before/after slider
- [ ] Ch.7 wildfire reveal: blue/amber immediately distinct (matches P1.C2 test)
- [ ] Full scroll: Ch.0 → Ch.9 without errors, orphaned layers, or jank
- [ ] Deployed and viewable at a URL

---

## Git Strategy

```
main (Phase 1 merged)
  └── v2/phase-2
        ├── P2.A1+A4a commit
        ├── P2.A2 commit
        ├── P2.A3 commit
        ├── P2.A4 commit
        ├── P2.B1+B3 commit
        ├── P2.B2 commit
        ├── P2.B4 commit
        ├── P2.B5+B6 commit
        ├── P2.B7+B8 commit
        └── P2.C1 commit
        → PR to main when Definition of Done met
```
