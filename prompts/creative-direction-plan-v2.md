# Creative Direction Plan v2: cheias.pt

**Date:** 2026-02-26
**Status:** AWAITING APPROVAL
**Supersedes:** `prompts/creative-direction-plan.md` (v1)
**Inputs:** v1 plan + three research reports + target company stack audit + library status verification

---

## 0. What Changed From v1

v1 was architecturally conservative. This version challenges six specific decisions and
resolves them with evidence from the actual GitHub repos of Development Seed, Vizzuality,
The Pudding, and NYT Graphics. Everything else from v1 — the story arc, chapter design,
untapped data priorities, the wildfire reveal — carries forward unchanged.

| v1 Decision | v2 Resolution | Evidence |
|-------------|--------------|----------|
| CDN-only, no bundler | **Vite from day one** | Zero target companies ship CDN-only. DevSeed uses Vite. |
| Keep custom wind particles | **WeatherLayers GL (MPL-2.0)** | All 6 layers are open-source. Bundler unlocks them. |
| Entirely 2D | **MapLibre v5 globe + terrain** | Globe is stable (v5.19). Terrain is built-in. |
| TripsLayer for atmospheric river | **IVT scalar field + wind particle overlay** | TripsLayer needs waypoints; IVT is a scalar field — wrong tool. |
| Synoptic composite deferred | **WeatherLayers GL closes the gap** | ContourLayer + GridLayer + HighLowLayer + FrontLayer. |
| Evolve v0 src/ with CDN | **Port to Vite** | Module structure already matches. Mechanical migration. |

---

## 1. Architecture Decision: Vite + Vanilla TypeScript

### The Evidence

Every organization whose quality bar we're targeting uses a bundler:

| Organization | Build Tool | Framework | Mapping |
|-------------|-----------|-----------|---------|
| **Development Seed** (stac-map) | Vite 7.3 | React 19 + TypeScript | MapLibre 5.19 + deck.gl 9.2 |
| **Development Seed** (deck.gl-raster) | tsup | TypeScript | deck.gl 9.2 |
| **Vizzuality** (Half-Earth v3) | Vite 5.4 | React 17 + TypeScript | ArcGIS JS 4.30 |
| **Vizzuality** (LandGriffon) | Next.js 14 | React 18 + TypeScript | MapLibre 3.6 + deck.gl 8.8 |
| **Vizzuality** (GFW frontend) | Nx + Next.js | React 19 + TypeScript | MapLibre 3.6 + deck.gl 9.1 |
| **The Pudding** | Vite (via SvelteKit) | Svelte 5 | D3 + Mapbox |
| **NYT Graphics** | Internal (Svelte compiler) | Svelte | D3 |

deck.gl's own docs state the CDN/script-tag approach is for "prototype environments such
as Codepen, JSFiddle and Observable." It is explicitly a prototyping path.

**Shipping a CDN-only script-tag app to Development Seed engineers would signal unfamiliarity
with modern frontend tooling.** It's the equivalent of submitting a portfolio piece with
inline CSS.

### The Stack

```
Vite 7 ...................... Build tool, dev server, HMR
Vanilla TypeScript ......... No framework. Module system only.
MapLibre GL JS v5 .......... Globe projection, terrain, vector/raster tiles
deck.gl v9.2 ............... BitmapLayer, PathLayer, TripsLayer, ColumnLayer
weatherlayers-gl ........... ParticleLayer, ContourLayer, GridLayer, HighLowLayer
geotiff.js ................. COG loading and decoding
scrollama .................. Scroll step detection
GSAP + ScrollTrigger ....... Animation, timeline scrubbing
d3-contour + d3-geo ........ Isobar generation (backup), great circle paths
Observable Plot ............ Inline sparklines
maplibre-gl-compare ........ Before/after satellite slider
```

### Why Vanilla TypeScript, Not React

React is what DevSeed and Vizzuality use for platforms — dashboards with persistent state,
user auth, complex UI components. cheias.pt is a scrollytelling narrative. It has:
- No user accounts
- No form inputs
- No component reuse across pages
- No server-side rendering needs
- One page, one scroll direction

React would add ~45KB gzipped, a virtual DOM reconciliation layer between us and MapLibre,
and the need for react-map-gl to bridge the imperative map API with React's declarative
model. For a single-page scroll narrative, this is pure overhead.

TypeScript gives us type safety and IDE support without framework tax. This is the pattern
deck.gl-raster itself uses (TypeScript + tsup, no React). It's also closer to how NYT
Graphics works — compiled modules, not framework components.

### Why Not Svelte

The Pudding's SvelteKit setup is excellent for scrollytelling, and Svelte 5 is technically
superior for reactive UIs. But adopting Svelte for a portfolio piece targeting DevSeed
(React shop) means the code won't read as immediately familiar to the audience. TypeScript
modules with direct MapLibre/deck.gl calls are universally readable.

### Project Structure

```
cheias-pt/
  index.html                 # Scroll structure, chapter divs, hero title
  vite.config.ts             # Minimal config
  tsconfig.json              # Strict TypeScript
  package.json               # Dependencies
  src/
    main.ts                  # Entry point, orchestration
    chapters.ts              # Chapter config (camera, layers, text)
    scroll-engine.ts         # scrollama + GSAP initialization
    map-setup.ts             # MapLibre v5 + deck.gl initialization
    layer-manager.ts         # Layer creation, opacity, crossfade
    weather-layers.ts        # WeatherLayers GL integration
    particle-system.ts       # Wind particle config and data pipeline
    contour-engine.ts        # MSLP isobar pipeline (WL ContourLayer or d3-contour)
    atmospheric-river.ts     # IVT field rendering + wind overlay
    data-loader.ts           # COG loading, geotiff.js, JSON fetching
    charts.ts                # Observable Plot inline charts
    exploration-mode.ts      # Ch.9 free exploration
    types.ts                 # Shared TypeScript interfaces
  css/
    style.css                # Dark-first design system
  public/
    assets/                  # Static assets (og-image, fonts)
  data/                      # (existing data directories, unchanged)
```

### Migration Path From v0

The existing `src/` has 1,773 lines across 10 modules. The module boundaries already match
the Vite structure:

| v0 Module | v2 Module | Migration |
|-----------|-----------|-----------|
| `story-config.js` | `chapters.ts` | Add types, keep chapter configs |
| `scroll-observer.js` | `scroll-engine.ts` | Replace custom IntersectionObserver with scrollama |
| `map-controller.js` | `map-setup.ts` | Upgrade MapLibre v4→v5, add globe/terrain |
| `layer-manager.js` | `layer-manager.ts` | Port, add WeatherLayers GL integration |
| `chapter-wiring.js` | merged into `scroll-engine.ts` | Wire via scrollama callbacks |
| `data-loader.js` | `data-loader.ts` | Port directly |
| `temporal-player.js` | merged into `scroll-engine.ts` | Scroll-driven instead of timeline UI |
| `exploration-mode.js` | `exploration-mode.ts` | Port directly |
| `main.js` | `main.ts` | Port, update imports |
| `utils.js` | inline or `types.ts` | Minimal |

This is a 1-2 day migration, not a rewrite. The chapter text, camera positions, and layer
configurations transfer directly.

### Scaffold Command

```bash
npm create vite@latest cheias-pt-v2 -- --template vanilla-ts
cd cheias-pt-v2
npm install maplibre-gl@^5 deck.gl @deck.gl/geo-layers @deck.gl/aggregation-layers
npm install weatherlayers-gl geotiff
npm install scrollama gsap d3-contour d3-geo @observablehq/plot
npm install @maplibre/maplibre-gl-compare
```

`vite build` → `dist/` → deploy to any static host. Same deployment model as CDN-only,
with every advantage of a proper build.

---

## 2. The Story Arc (Unchanged From v1)

Sections 2-4 of the v1 plan carry forward without modification. The 7-chapter narrative
structure, the chapter-by-chapter visualization design, and the untapped data priorities
are strong as written. Specifically:

- **Ch.1: The Hook** — dark Atlantic, serif title, ghost flood pulse
- **Ch.2: The Planetary Scale** — SST + atmospheric river (now with globe + 3D, see §4)
- **Ch.3: The Sponge Fills** — scroll-driven soil moisture animation + wildfire foreshadowing
- **Ch.4: The Storms Arrive** — multi-effect meteorological drama (now with WeatherLayers GL, see §3)
- **Ch.5: The Rivers Respond** — discharge swelling + sparklines (now with 3D columns, see §4)
- **Ch.6: The Consequences** — flood extent + human cost (now with terrain, see §4)
- **Ch.7: The Full Picture** — wildfire reveal, causal chain composite

The untapped data gem (fire→flood connection, §4.4 of v1) remains the intellectually
original moment. The Salvaterra temporal triptych remains the most powerful temporal
dataset. Both unchanged.

---

## 3. Effect Resolution: WeatherLayers GL Changes Everything

### The Discovery

WeatherLayers GL is **fully open-source under MPL-2.0**. All six layer types are in the
GitHub repo (`weatherlayers/weatherlayers-gl`). The "commercial" aspect is their hosted
data cloud service, not the library. Current version: 2026.2.0. Actively maintained.

With a Vite build, we can `npm install weatherlayers-gl` and get:

| Layer | What It Does | Replaces |
|-------|-------------|----------|
| **ParticleLayer** | GPU-accelerated wind particle simulation from vector fields | Custom CPU-based advection (Effect 1) |
| **RasterLayer** | Color overlay with customizable palettes from GeoTIFF | Custom geotiff.js → canvas pipeline |
| **ContourLayer** | Iso-contour lines from scalar fields | d3-contour + manual reprojection (Effect 3) |
| **GridLayer** | Grid of values/symbols — VALUE, ARROW, WIND_BARB styles | Custom wind barb canvas factory (Effect 5) |
| **HighLowLayer** | Pressure system H/L labels tracking extrema | Manual scipy extrema detection (Effect 5) |
| **FrontLayer** | Weather front lines with proper meteorological symbology | Deferred entirely in v1 |

### Effect 1: Wind Particles — WeatherLayers GL ParticleLayer

**Before (v1):** Custom JS particle advection → deck.gl PathLayer. CPU-bound. Per-segment
trail opacity requires splitting each trail into LineLayer segments. 1-2 days of work for
per-segment decay alone. Max ~10K particles before jank.

**After (v2):** WeatherLayers GL ParticleLayer. GPU-accelerated. Accepts GeoTIFF directly
(geotiff.js >= 3.0.0). Built-in trail fade, density control, speed-based coloring, comet
tail rendering. Handles 50K+ particles at 60fps.

```typescript
import { ParticleLayer } from 'weatherlayers-gl';

const windLayer = new ParticleLayer({
  id: 'wind-particles',
  image: windGeoTiff,         // geotiff.js loaded U/V COG
  imageType: 'VECTOR',
  numParticles: 5000,
  maxAge: 100,
  speedFactor: 0.5,
  width: 2,
  color: [255, 255, 255, 200],
  animate: true,
});
```

**Data pipeline:** Unchanged. Wind U/V COGs from R2 → geotiff.js → ParticleLayer. No PNG
texture encoding needed. The library reads GeoTIFF directly.

**Visual improvement:** GPU rendering means proper per-pixel trail decay (the comet-tail
effect from the WeatherWatcher14 video). The custom CPU approach could only approximate
this with discrete path segments.

**Fallback:** If WeatherLayers GL ParticleLayer proves insufficient for our aesthetic needs
(unlikely, but possible), the custom advection code from the prototype is still portable.
It would move into `particle-system.ts` as a backup path.

**Effort saved:** 2-3 days of per-segment trail opacity work eliminated.

### Effect 3: MSLP Isobars — Two Options Now

**Option A: WeatherLayers GL ContourLayer (recommended)**

ContourLayer generates iso-contour lines directly from scalar fields. Feed it the MSLP
COG, specify thresholds at 4 hPa intervals, get animated isobars that update per frame.

```typescript
import { ContourLayer } from 'weatherlayers-gl';

const isobarLayer = new ContourLayer({
  id: 'mslp-isobars',
  image: mslpGeoTiff,
  imageType: 'SCALAR',
  interval: 400,  // 4 hPa in Pa
  width: 1.5,
  color: [255, 255, 255, 220],
});
```

Combined with HighLowLayer for tracking pressure centers:

```typescript
import { HighLowLayer } from 'weatherlayers-gl';

const pressureCenters = new HighLowLayer({
  id: 'pressure-lh',
  image: mslpGeoTiff,
  imageType: 'SCALAR',
  radius: 500000,  // search radius in meters
  // Renders L and H labels at pressure extrema
});
```

**Effort saved:** No batch contour generation script needed. No d3-contour → pixel-to-geo
reprojection. No manual L/H extrema detection. The entire MSLP pipeline collapses to
loading a COG and passing it to two layers.

**Option B: d3-contour (backup)**

If WeatherLayers GL ContourLayer's output doesn't meet the aesthetic (e.g., we need more
control over line styling), the d3-contour approach from v1 remains viable:

```
COG → geotiff.js → Float32Array → d3.contours() → GeoJSON → MapLibre line layer
```

Both options work with Vite. The d3-contour approach is more work but gives total control
over line rendering via MapLibre paint properties.

### Effect 5: Synoptic Composite — No Longer Deferred

v1 deferred the full synoptic chart to Phase 3 because wind barbs, frontal boundaries, and
H/L markers each required custom implementations. WeatherLayers GL provides all three:

| Component | v1 Plan | v2 With WeatherLayers GL |
|-----------|---------|------------------------|
| Wind barbs | Canvas sprite factory, 1-2 days | `GridLayer` with `style: 'WIND_BARB'`, works from COG |
| H/L markers | scipy extrema detection script, 0.5 day | `HighLowLayer` from same MSLP COG, zero preprocessing |
| Frontal boundaries | Manual GeoJSON, 0.5 day | `FrontLayer` with GeoJSON input (still needs manual front positions) |
| Isobars | d3-contour or pre-generation, 1 day | `ContourLayer`, zero preprocessing |

The only remaining manual work is drawing 3-4 frontal boundary GeoJSON LineStrings for the
key timesteps (Kristin peak, Leonardo peak, Marta peak). The frontal analysis itself is
meteorological judgment — no library can automate this for a specific case study.

**Result:** With Effects 1 + 2 + 3 + 5 composited in Chapter 4, the synoptic-like
experience becomes a proper **meteorologist-recognizable synoptic chart**: isobars + wind
barbs + H/L markers + frontal boundaries + precipitation field + wind particles. This
closes the gap identified in v1 with minimal additional effort.

### Effect 2: Precipitation Sweep — Unchanged

Pre-rendered blurred PNGs with MapLibre image source crossfade remains the right approach.
WeatherLayers GL RasterLayer is an alternative for the COG path but doesn't improve on
pre-processed PNGs for this specific case.

### Effect 4: Satellite Cloud Motion — Unchanged

IR COG → pre-rendered enhanced PNG frames → crossfade animation. Same as v1.

### Effect 6: Layer Transitions — Scrollama + GSAP (Unchanged)

Same architecture as v1. scrollama for step detection, GSAP for animation polish, MapLibre
flyTo for camera. The scroll engine is the narrative backbone. Priority #1.

---

## 4. 3D Visualization: Globe, Terrain, Columns

### The Opportunity

Vizzuality uses 3D as a signature capability. Half-Earth's "big beautiful 3D globe for you
to explore" is their most recognized portfolio piece. The v1 plan was entirely 2D — a
missed opportunity for a story about water flowing downhill through terrain.

### MapLibre v5 Globe — Production-Ready

MapLibre GL JS v5 shipped January 2025. Current stable: v5.19.0. The globe projection is
a core feature, not experimental. Activation:

```typescript
const map = new maplibregl.Map({
  container: 'map',
  projection: 'globe',  // ← this is all it takes
  style: darkBasemapStyle,
});
```

**deck.gl GlobeView is NOT the path.** It's still experimental in v9.2 with 0 of 5
graduation items completed: no pitch/bearing rotation, broken IconLayer, jittery panning.
Instead, deck.gl layers overlay on MapLibre v5's globe via `MapboxOverlay` — the stable,
production approach.

### Where 3D Serves the Story

#### Chapter 2: Globe View for the Atlantic Engine

The atmospheric river wrapping from the subtropics to Iberia is more dramatic on a globe.
The curvature of the moisture highway becomes physically visible.

```typescript
// Ch.2 camera: globe view of Atlantic
{
  center: [-25, 35],
  zoom: 2.8,
  pitch: 0,
  bearing: 0,
  projection: 'globe'
}
```

SST anomaly raster draped over the globe. IVT field showing the atmospheric river as a
luminous band. Wind particles flowing along the curve of the Earth. Storm track arcs as
great circles. The audience feels the planetary scale before we descend to Portugal.

**Transition to flat map:** As the user scrolls from Ch.2 → Ch.3, the map smoothly
transitions from globe to mercator projection. MapLibre v5 supports animated projection
transitions.

```typescript
map.setProjection('mercator'); // smooth transition built-in
```

#### Chapter 5: 3D Columns for River Discharge

deck.gl ColumnLayer renders 3D extruded columns at geographic positions. For discharge
stations, column height = discharge magnitude. The physical metaphor: water RISING.

```typescript
import { ColumnLayer } from '@deck.gl/layers';

const dischargeColumns = new ColumnLayer({
  id: 'discharge-columns',
  data: dischargeStations,
  getPosition: d => [d.longitude, d.latitude],
  getElevation: d => d.discharge * 10,
  getFillColor: d => d.amplification > 5
    ? [231, 76, 60, 200]   // red: extreme amplification
    : [52, 152, 219, 200], // blue: elevated
  radius: 5000,
  extruded: true,
});
```

As the scroll advances through Chapter 5, columns grow from baseline to peak. The Guadiana
at 11.5x amplification towers over the others. Combined with terrain, the columns rise
from the river valleys.

#### Chapters 5-6: Terrain Exaggeration

MapLibre terrain with hillshade exaggeration shows WHY water flows where it does. River
valleys become visible depressions. Flood plains are obviously flat and low. The Tejo
basin's vulnerability becomes physically intuitive.

```typescript
map.addSource('terrain', {
  type: 'raster-dem',
  url: 'https://demotiles.maplibre.org/terrain-tiles/tiles.json',
});
map.setTerrain({ source: 'terrain', exaggeration: 1.5 });
```

Terrain enables in Ch.5 (rivers), intensifies in Ch.6 (consequences), and provides the
surface over which flood extent polygons drape — creating implicit flood depth visualization
where terrain meets water surface.

**The Salvaterra moment (Ch.6c):** With terrain enabled and flood extent draped over it,
the viewer sees the Tejo floodplain as a physical depression filling with blue. The 58%
growth over 48 hours becomes a visceral rising tide, not just expanding polygons.

#### 3D Flood Depth (Stretch Goal)

If terrain + flood extent + CEMS depth rasters are combined, the difference IS flood depth.
An extruded 3D flood surface over terrain would show water depth in meters. Requires
extracting CEMS flood depth rasters (exist in raw data, not yet processed).

**Effort: 1-2 days.** Mark as stretch goal for Phase 3.

#### What NOT to 3D

- **Chapter 1 (Hook):** Flat. The dark Atlantic should be abstract and empty.
- **Chapter 3 (Soil Moisture):** 2D raster animation. Terrain distracts from saturation.
- **Chapter 4 (Storms):** 2D with pitch. Synoptic patterns need overhead readability.
- **Chapter 7 (Full Picture):** Flat national overview. The composite must be readable.

### Pitch and Bearing Throughout

| Chapter | Pitch | Bearing | Why |
|---------|-------|---------|-----|
| 1 (Hook) | 0 | 0 | Flat, abstract, ominous |
| 2 (Atlantic) | 0 (globe) | 0 | Planetary perspective |
| 3 (Soil) | 15 | -5 | Slight tilt, ground-focused |
| 4 (Storms) | 20-30 | varies per sub-chapter | Drama, overhead synoptic readability |
| 5 (Rivers) | 35 | -10 | Terrain visible, valleys readable |
| 6 (Consequences) | 40-50 | varies per location | Close, intimate, terrain prominent |
| 7 (Full Picture) | 10 | 0 | Pull back, readable composite |

---

## 5. Atmospheric River: Not TripsLayer

### Why TripsLayer Is Wrong

TripsLayer needs waypoints with timestamps:
```typescript
[{ path: [[lon1,lat1],[lon2,lat2],...], timestamps: [t1,t2,...] }]
```

IVT (Integrated Vapor Transport) is a **scalar field** — a 2D grid of moisture flux
magnitude at each pixel. There's no inherent "path" to trace. Converting a scalar field
to waypoints requires ridge-tracing: identifying the IVT maximum ridge line across
timesteps, handling bifurcations, ambiguous maxima, and temporal coherence. This is a
non-trivial computational geometry problem that produces fragile results.

### The Better Approach: Animated Scalar Field + Flow Overlay

**Primary visualization:** Render the IVT scalar field directly as a color-mapped raster
(WeatherLayers GL RasterLayer or deck.gl BitmapLayer). Purple/white for high IVT (>500
kg/m/s), transparent for low. The atmospheric river is visible as a luminous band flowing
from the subtropics to Iberia.

```typescript
import { RasterLayer } from 'weatherlayers-gl';

const ivtLayer = new RasterLayer({
  id: 'ivt-field',
  image: ivtGeoTiff,
  imageType: 'SCALAR',
  palette: ivtPalette,  // transparent → blue → purple → white
  domain: [0, 1200],    // kg/m/s
  opacity: 0.8,
});
```

**Secondary overlay:** Wind particles at the 850hPa level flowing THROUGH the IVT field,
showing the moisture transport direction. The particles add motion and directionality.

**Tertiary accent:** Storm track paths rendered as MapLibre line layer using full
multi-vertex LineStrings from P1.B1 MSLP minima tracking. Per-storm colors. Named labels
at line-center. ~~(Originally spec'd as deck.gl ArcLayer great circles — superseded by
real tracked data from P1.B1. See P2-B-chapters.md Session 6.)~~

```typescript
import { ArcLayer } from '@deck.gl/layers';

const stormArcs = new ArcLayer({
  id: 'storm-tracks',
  data: stormTracks,
  getSourcePosition: d => d.origin,
  getTargetPosition: d => d.destination,
  getSourceColor: [255, 100, 100, 200],
  getTargetColor: [255, 200, 100, 200],
  getWidth: 3,
  greatCircle: true,
});
```

**The composite:** On the MapLibre v5 globe, the IVT field drapes over the curved ocean.
Wind particles flow along the field showing transport direction. Storm arcs trace great
circles from mid-Atlantic to Iberia. This is more visually compelling AND more
scientifically accurate than a TripsLayer ribbon, because it shows the atmospheric river
as what it actually is — a broad, coherent moisture flux structure, not a single path.

### Data Pipeline

Use the ECMWF HRES IVT data (17 COGs at 0.1deg, Jan 25-Feb 10) for the storm window.
For broader temporal context (Dec-Feb), use ERA5 IVT at 0.5deg (77 daily COGs).

The transition:
1. Ch.2 opens with ERA5 0.5deg IVT showing the seasonal pattern (on globe)
2. Scroll into the storm window → crossfade to ECMWF HRES 0.1deg for 10x detail
3. Wind particles activate as the AR intensifies

**No TripsLayer. No ridge-tracing. No waypoint conversion.** The scalar field IS the
visualization.

---

## 6. Synoptic Composite: Minimal Additions to Close the Gap

### What Chapter 4 Already Has

- Wind particles (Effect 1) → atmospheric flow texture
- Precipitation sweep (Effect 2) → rainfall accumulation
- MSLP isobars (Effect 3) → pressure pattern
- Satellite IR timelapse (Effect 4) → cloud structure

### What's Missing for "Meteorologist-Recognizable"

Wind barbs, H/L labels, and frontal boundaries. These are the cartographic conventions
that signal professional meteorological analysis.

### The Additions (Via WeatherLayers GL)

**1. Wind barbs at selected timesteps**

GridLayer with `WIND_BARB` style renders proper meteorological notation directly from the
same wind U/V COGs already loaded for particle rendering.

```typescript
import { GridLayer } from 'weatherlayers-gl';

const windBarbs = new GridLayer({
  id: 'wind-barbs',
  image: windGeoTiff,
  imageType: 'VECTOR',
  style: 'WIND_BARB',
  density: 32,  // grid spacing in pixels
  color: [255, 255, 255, 180],
});
```

Wind barbs appear during sub-chapters 4a (Kristin peak) and 4c (Leonardo peak),
complementing the particle flow with quantitative wind data. They fade during satellite
sequences to avoid visual clutter.

**2. H/L pressure labels**

HighLowLayer auto-detects pressure extrema from the MSLP COG. No preprocessing needed.

**3. Frontal boundaries at 3-4 key timesteps**

Draw GeoJSON LineStrings for:
- Kristin cold front at Jan 28 00Z and 12Z
- Leonardo warm front at Feb 5 12Z
- Marta cold front at Feb 10 06Z

~2 hours of manual meteorological analysis.

### The Full Layer Stack for Ch.4 Climax

```
Layer stack (bottom to top):
  1. Dark basemap
  2. Temperature field raster (red warm / blue cold)   ← Phase 3
  3. Wind speed background field (purple/green/yellow)
  4. MSLP isobars (ContourLayer, white 1.5px)
  5. H/L pressure labels (HighLowLayer)
  6. Wind barbs (GridLayer, WIND_BARB style)
  7. Frontal boundaries (FrontLayer or MapLibre line)
  8. Precipitation field (blurred blue PNGs)
  9. Satellite IR (inverted grayscale, when enabled)
  10. Wind particles (ParticleLayer, atmospheric texture)
  11. Lightning flashes (ScatterplotLayer, yellow stars)
  12. IPMA warning choropleth (district fill)
  13. Map annotations ("EXPLOSIVE CYCLOGENESIS", etc.)
```

A meteorologist recognizes this as a synoptic analysis chart with dynamic elements.
The general audience gets emotional impact from swirling particles, deepening colors, and
escalating warnings. Both audiences served simultaneously.

---

## 7. Updated Implementation Phases

### Phase 0: Foundation (Week 1)

Scaffold Vite project, port existing code, establish scroll narrative.

| # | Task | Delivers | Effort |
|---|------|----------|--------|
| 0.1 | **Scaffold Vite + TypeScript project** | `npm create vite`, install deps, configure | 2 hours |
| 0.2 | **Port v0 src/ modules to TypeScript** | Type-safe versions of all 10 modules | 1-2 days |
| 0.3 | **Upgrade MapLibre v4 → v5** | Globe projection available, terrain ready | 0.5 day |
| 0.4 | **Replace custom scroll observer with scrollama** | Proper sticky graphic pattern, step progress | 0.5 day |
| 0.5 | **Add GSAP + ScrollTrigger** | Animation polish for text reveals, number tickers | 0.5 day |
| 0.6 | **Fix basemap aesthetics** | Background #0a212e, glassmorphism, serif typography | 2-3 hours |
| 0.7 | **Verify chapter scroll triggers camera + layer opacity** | End-to-end scroll narrative working | 0.5 day |

**Deliverable:** Scrollable page with chapters triggering camera moves and layer changes.
All existing layers working. Deployed via `vite build` to static host.

### Phase 1: Data Pipeline (Week 2)

| # | Task | Delivers | Effort |
|---|------|----------|--------|
| 1.1 | **Pre-render precipitation PNGs** | 77 blurred PNGs with blues colormap + alpha | 0.5 day |
| 1.2 | **Pre-render satellite IR PNGs** | 48 enhanced frames with inverted grayscale | 2-3 hours |
| 1.3 | **Fetch extended Meteosat (Leonardo/Marta)** | ~96 additional IR COGs for Feb 5-11 | 0.5 day |
| 1.4 | **Fetch Sentinel-2 before/after** | 2 true-color scenes for Salvaterra | 0.5 day |
| 1.5 | **Draw frontal boundary GeoJSONs** | 3-4 front positions at key timesteps | 2-3 hours |
| 1.6 | **Extract flood depth rasters** | Depth values from raw CEMS SHP for Salvaterra | 2-3 hours |

**Note:** Tasks from v1 Phase 1 that are now eliminated (temporal MSLP contours, wind
speed magnitude field, temporal L/H markers, TripsLayer waypoints) save ~2.5 days.
WeatherLayers GL handles them client-side from existing COGs.

### Phase 2: Core Narrative Effects (Weeks 3-4)

| # | Task | Delivers | Effort |
|---|------|----------|--------|
| 2.1 | **WeatherLayers GL integration** | ParticleLayer, ContourLayer, GridLayer, HighLowLayer wired to COG pipeline | 1-2 days |
| 2.2 | **Ch.2: Globe + atmospheric river** | MapLibre v5 globe, IVT raster field, wind particles, storm track arcs | 1-2 days |
| 2.3 | **Ch.3: Soil moisture scroll animation** | 77 PNG frames driven by scroll position, basin sparklines | 1 day |
| 2.4 | **Ch.4: Full synoptic composite** | All 13 layers composited with scroll-driven sub-chapter transitions | 2-3 days |
| 2.5 | **Ch.5: River discharge with 3D columns** | ColumnLayer + terrain + sparkline hydrographs | 1-2 days |
| 2.6 | **Ch.6: Consequences with terrain** | Flood extent over terrain, Salvaterra triptych, consequence markers | 1-2 days |
| 2.7 | **Ch.7: Wildfire reveal composite** | Burn scars in amber, all flood layers, causal chain | 0.5 day |
| 2.8 | **IPMA warning choropleth** | District-level escalation yellow→orange→red | 0.5 day |
| 2.9 | **Globe→mercator transition** | Smooth projection change between Ch.2 and Ch.3 | 0.5 day |

### Phase 3: Polish (Week 5)

| # | Task | Delivers | Effort |
|---|------|----------|--------|
| 3.1 | **Entry animation** | Slow globe rotation → Portugal approach → title fade-in | 0.5 day |
| 3.2 | **maplibre-gl-compare** | Before/after Sentinel-2 slider for Salvaterra | 0.5 day |
| 3.3 | **Temperature field** | Red/white/blue raster beneath MSLP isobars | 1-2 days |
| 3.4 | **3D flood depth (stretch)** | Extruded flood surface at Salvaterra | 1-2 days |
| 3.5 | **Satellite annotations** | "EXPLOSIVE CYCLOGENESIS", "STING JET", dry slot arrow | 0.5 day |
| 3.6 | **Responsive layout** | Mobile bottom sheet, tablet adaptation | 1-2 days |
| 3.7 | **Performance tuning** | COG pre-fetch, lazy-load chapters, device-adaptive particles | 1 day |
| 3.8 | **Free exploration mode (Ch.9)** | Unlock map interaction, layer toggles, geolocation | 1 day |
| 3.9 | **Accessibility** | ARIA labels, keyboard navigation, `prefers-reduced-motion` | 1 day |

---

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| WeatherLayers GL deck.gl version conflicts | Medium | High | Pin deck.gl to WL's tested version (9.2.6). If blocked, fall back to d3-contour + custom particles. |
| MapLibre v5 globe + deck.gl overlay bugs | Low | Medium | deck.gl 9.1+ officially supports MapLibre v5 via MapboxOverlay. Well-tested path. |
| WL ParticleLayer aesthetics insufficient | Low | Medium | Custom particle system from prototype is portable as backup. 1-2 day pivot. |
| MapLibre terrain + flood extent z-fighting | Medium | Low | Adjust polygon elevation offset. Standard technique. |
| COG loading performance on mobile | High | Medium | Reduce particle count, use pre-rendered PNGs on mobile, lazy-load chapters. |
| WL MPL-2.0 copyleft concern | Certain | Low | MPL-2.0 only requires sharing modifications to MPL-licensed files. Project code stays proprietary. Acceptable. |

---

## 9. What Was Kept From v1

Almost everything except architecture and specific library choices:

- **Visual identity statement** (§1) — dark oceanic authority, unchanged
- **Story arc** (§2) — all 7 chapters, camera positions, emotional beats
- **Effect-by-effect design** (§3) — upgraded tools, same visual targets
- **Untapped data opportunities** (§4) — all tiers, all gems, all priorities
- **Portuguese narrative text** — all chapter titles and body text

The creative vision is the same. The engineering plan is upgraded.

---

## 10. Effort Comparison: v1 vs v2

| Phase | v1 Estimate | v2 Estimate | Savings |
|-------|------------|------------|---------|
| Phase 0 (Foundation) | 5-6 days | 4-5 days | ~1 day |
| Phase 1 (Data Pipeline) | 4-5 days | 2-3 days | ~2 days |
| Phase 2 (Core Effects) | 10-12 days | 8-10 days | ~2 days |
| Phase 3 (Polish) | 7-8 days | 7-8 days | Even |
| **Total** | **~27 days** | **~22 days** | **~5 days faster** |

Savings from WeatherLayers GL handling isobar generation, wind barb rendering, H/L
tracking, and particle simulation — all planned as custom code in v1.

---

## What Happens Next

**This plan is awaiting your approval.** Once approved, the first implementation prompt
will scaffold the Vite project and port the existing v0 modules to TypeScript.
