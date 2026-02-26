# Library Compatibility & Architecture Report

**Purpose:** Comprehensive capability matrix for every visualization library relevant to cheias.pt, a weather/flood scrollytelling geo-narrative.

**Context:** Current prototype is `deckgl-prototype.html` -- a single-file MapLibre v4 + deck.gl v9 spike that renders COGs from Cloudflare R2 using geotiff.js, with wind particles, satellite IR, MSLP fields, soil moisture, precipitation, and animated wind barbs. All loaded via CDN `<script>` tags, no bundler.

---

## 1. Capability Matrix

### 1A. deck.gl Ecosystem

| Library | What it Renders | Integration Path | deck.gl v9 | MapLibre v4 | Data Format | Maturity | Notes |
|---------|----------------|-----------------|------------|-------------|-------------|----------|-------|
| **deck.gl core** (BitmapLayer, PathLayer, ScatterplotLayer, GeoJsonLayer, IconLayer, ArcLayer, ColumnLayer) | Raster overlays, vector paths, points, polygons, icons, arcs, 3D columns | CDN: `unpkg.com/deck.gl@^9.0.0/dist.min.js` | Native | Interleaved or overlay via `MapboxOverlay` | GeoJSON, typed arrays, JS objects | 20k+ stars, weekly releases, OpenJS Foundation | Already in use in prototype. CDN bundle ~400KB gzipped. All core layers available in standalone bundle. |
| **deck.gl HeatmapLayer** | GPU-aggregated heatmap from point data | CDN: `unpkg.com/@deck.gl/aggregation-layers@^9.0.0/dist.min.js` | Native | Yes (via overlay) | Array of `{position, weight}` objects | Stable, part of core | Good for precipitation point grids. GPU-based so performant. Limited on iOS Safari (partial WebGL). Needs separate aggregation-layers CDN import. |
| **deck.gl ContourLayer** | Iso-lines and iso-bands from point data | Same CDN as HeatmapLayer | Native | Yes (via overlay) | Array of `{position, weight}` + threshold config | Stable, part of core | Could generate contour lines from gridded data, but designed for point aggregation, NOT for pre-gridded raster data. For MSLP isobars from COG, d3-contour is better. |
| **deck.gl TripsLayer** | Animated paths with timestamp-based playback and fade trails | CDN: `unpkg.com/@deck.gl/geo-layers@^9.0.0/dist.min.js` | Native | Yes (via overlay) | Array of waypoints with `{coordinates: [lng, lat], timestamp}`. Timestamps must survive `Math.fround()` (32-bit float). | Stable, well-documented | Potential for atmospheric river animation or flood progression paths. Requires converting time-series data into waypoint format. `currentTime`, `trailLength`, `fadeTrail` props control animation. |
| **deck.gl-particle** (WeatherLayers) | Animated wind particle streamlines from U/V vector fields | npm only (`npm i deck.gl-particle`). **ARCHIVED** Mar 2025. | Was built for deck.gl 8.x. v9 compat uncertain. | Via deck.gl overlay | PNG textures with U in R channel, V in G channel. Requires encoding step from raw wind data. | **ARCHIVED.** 1.1.0, last published 3 years ago. 200+ stars. | The open-source particle layer is dead. Functionality absorbed into WeatherLayers GL (commercial). The prototype already implements a custom wind particle system that is more flexible. |
| **WeatherLayers GL** | Wind particles, temperature rasters, contours, precipitation, pressure, cloud, ocean currents | npm only (`npm i weatherlayers-gl`). No CDN bundle. Requires bundler. | deck.gl 9.2: v2025.11.0+, deck.gl 9.1: v2025.1.0-2025.8.0, deck.gl 9.0: v2024.x | Via deck.gl overlay | GeoTIFF (via geotiff.js >= 3.0.0), custom data sources | 131 stars, actively maintained (Nov 2025 last update). Dual-licensed: MPL-2.0 OR proprietary. | **Most complete weather viz solution** but introduces bundler dependency and commercial licensing ambiguity. The MPL-2.0 option allows open-source use but requires sharing modifications. Not CDN-loadable -- breaks our single-file pattern. |
| **flowmap.gl** | Animated flow lines between geographic locations (origin-destination) | npm only. Monorepo with multiple packages. | Built on deck.gl, FOSDEM 2026 presentation shows active development. Likely v9 compat. | Via deck.gl overlay | `locations: [{id, lat, lon}]` + `flows: [{origin, dest, count}]` | 128 stars (visgl/flowmap.gl), Apache-2.0, active (2024 release v8.0.2) | Could visualize moisture transport between Atlantic moisture source and Portuguese catchments. Data format is origin-destination pairs with magnitude -- would need to synthesize this from IVT data. Not CDN-loadable. |
| **deck.gl-raster** (Development Seed) | GPU-accelerated COG/GeoTIFF rendering with colormaps, reprojection, tiling | npm only. Monorepo with 6 packages. | Works with deck.gl TileLayer (v9 compat likely, latest release Feb 2026) | Via deck.gl overlay | Cloud-Optimized GeoTIFF directly. No preprocessing needed. | 141 stars, **actively maintained** (Feb 2026 release). Development Seed's own project. | **The most relevant raster library for this project.** Replaces our manual geotiff.js + canvas pipeline with proper GPU rendering, automatic overview selection, and tiling. Renders 1.3GB COGs client-side. BUT: npm-only, requires bundler. This is the strongest argument for graduating from single-file HTML. |
| **nebula.gl / editable-layers** | Geometry editing overlays (draw, edit, extrude) | npm only | Migrated to `@deck.gl-community/editable-layers` v9 (Apr 2024) | Via deck.gl overlay | GeoJSON for editing | Original nebula.gl unmaintained. Community fork active. | **Not relevant** for scrollytelling. This is for interactive editing, not narrative visualization. Skip. |

### 1B. MapLibre Ecosystem

| Library | What it Renders | Integration Path | deck.gl v9 | MapLibre v4 | Data Format | Maturity | Notes |
|---------|----------------|-----------------|------------|-------------|-------------|----------|-------|
| **MapLibre GL JS v4** | Vector tiles, raster tiles, GeoJSON, image sources, terrain, 3D buildings, globe (v5) | CDN: `unpkg.com/maplibre-gl@^4.0.0/dist/maplibre-gl.js` | Full integration (interleaved, overlaid, reverse-controlled) | Native | MVT, PMTiles, GeoJSON, raster tiles, image URLs | 7.5k+ stars, foundation-backed, very active | Already in use. v4 is stable. v5 adds globe view (interesting for Ch.2 Atlantic scale but not essential). `flyTo`/`easeTo` camera transitions are excellent and already used. |
| **maplibre-contour** | Contour lines from raster DEM tiles | CDN: `unpkg.com/maplibre-contour` (ES module) | N/A (MapLibre native layer) | Native plugin | Raster-DEM tiles (Mapbox terrain-rgb or Terrarium encoding) | 350+ stars, maintained by onthegomap | Designed for elevation contours from DEM, NOT for arbitrary gridded data like pressure. Uses marching squares internally (same as d3-contour). Cannot consume our MSLP COGs directly -- it expects DEM tile sources. **Not useful for isobars.** Could be useful for terrain contours as visual context. |
| **maplibre-gl-compare** | Before/after slider between two map instances | CDN: `@maplibre/maplibre-gl-compare` on npm, also CDN-loadable | N/A (MapLibre plugin) | Native plugin | Two MapLibre map instances | Official MapLibre plugin, maintained | **Directly useful** for Chapter 6 (human cost) satellite before/after comparison. Vertical or horizontal slider. Supports mouse-following mode. Simple API. |
| **maplibre-gl-particle** (Oseenix) | Wind particle streamlines as MapLibre custom layer | GitHub only (no npm) | N/A (MapLibre custom layer) | Fork of windgl for MapLibre | PNG textures (U in R, V in G channel) + JSON metadata | **1 star. Not maintained. Known bugs.** Author states "not production ready." | Skip. Our existing custom particle implementation in the prototype is more capable and maintained by us. |
| **MapLibre custom layers** | Anything via raw WebGL | Built into MapLibre via `CustomLayerInterface` | Can coexist with deck.gl overlay | Native API | Whatever the custom WebGL code expects | Stable API | Escape hatch for anything MapLibre + deck.gl can't do natively. Used by windgl implementations. Our prototype's wind particle system effectively IS a custom layer (rendered via deck.gl overlay). |

### 1C. D3 / Observable Ecosystem

| Library | What it Renders | Integration Path | deck.gl v9 | MapLibre v4 | Data Format | Maturity | Notes |
|---------|----------------|-----------------|------------|-------------|-------------|----------|-------|
| **d3-contour** | Contour polygons (iso-lines) from gridded data via marching squares | CDN: `unpkg.com/d3-contour@4` or ESM `import` | Outputs GeoJSON -- can feed into deck.gl GeoJsonLayer | Outputs GeoJSON -- can add as MapLibre source | Flat array of values (n x m grid), specify size [n, m] and thresholds | Core D3 module, v4.0.0, stable | **The right tool for MSLP isobars.** Load COG with geotiff.js -> extract band as flat array -> feed to d3.contours().size([w,h]).thresholds([960,964,...,1040]) -> get GeoJSON MultiPolygons. Observable has a working example: "GeoTIFF Contours" notebook. Lightweight (~10KB). |
| **d3-geo** | Map projections, path rendering, great circle arcs | CDN: `unpkg.com/d3-geo@3` | Can generate GeoJSON paths for deck.gl | Can generate GeoJSON for MapLibre sources | GeoJSON geometries, projection functions | Core D3 module, rock-solid | Useful for atmospheric river track visualization (great circle arcs from Atlantic to Iberia). `d3.geoGreatArc()` generates interpolated points along geodesic paths. Could feed results to deck.gl ArcLayer or PathLayer. |
| **Observable Plot** | SVG/Canvas charts: bar, line, area, dot, cell, sparklines | CDN: `cdn.jsdelivr.net/npm/@observablehq/plot@0.6` | N/A (separate SVG/Canvas charts) | N/A (overlaid as HTML elements) | Arrays of JS objects, column-oriented | Active development by Observable team. Well-documented. | **Perfect for discharge sparklines** in sidebar panels. Lightweight inline charts. Can create sparklines with `Plot.lineY(data, {x: "date", y: "discharge"})`. Good for the Chapter 5 river discharge mini-charts and Chapter 9 exploration mode. |
| **d3-force** | Force-directed layouts, particle simulations | CDN: `unpkg.com/d3-force@3` | N/A | N/A | Node/link objects | Core D3 module | **Not useful** for this project. Force-directed layouts don't apply to geographic particle systems. Our wind particles use advection through a vector field, which is physics-based, not force-graph-based. |

### 1D. Scrollytelling Frameworks

| Library | What it Does | Integration Path | Dependencies | Data Format | Maturity | Notes |
|---------|-------------|-----------------|-------------|-------------|----------|-------|
| **scrollama** | IntersectionObserver-based scroll position detection. Fires events when elements enter/exit viewport. Sticky graphic pattern. | CDN: `cdn.jsdelivr.net/npm/scrollama@3` or `cdnjs.cloudflare.com/ajax/libs/scrollama/3.2.0/scrollama.min.js` | **Zero dependencies.** Vanilla JS. | HTML step elements | 5.8k stars, v3.2.0, created by Russell Goldenberg (The Pudding). Well-documented. | **Best fit for this project.** Lightweight, CDN-loadable, vanilla JS, no build tools. Designed exactly for the sticky-map + scrolling-text pattern. The Pudding uses it in production. Supports step enter/exit events and progress (0-100%). Can trigger MapLibre `flyTo()` + layer opacity changes on step events. |
| **GSAP ScrollTrigger** | Scroll-linked animation engine. Scrubbing, pinning, progress-based animation, timeline orchestration. | CDN: `cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js` (+ gsap core) | GSAP core (~30KB gzipped) | Animation timelines, DOM elements | 20.6k stars, 630k weekly npm downloads. **Now 100% free** (including all plugins) after Webflow acquisition. | **Powerful but heavier.** Best for complex multi-property animations (parallax, morphing, scrub-linked opacity). Overkill for simple step triggers but excellent for polish effects like: scroll-linked basemap tint change, smooth opacity interpolation between chapters, timeline scrubbing. Can complement scrollama rather than replace it. |
| **Mapbox Storytelling** | Config-driven scroll-map template. Chapter definitions with camera positions, layer visibility, text alignment. | npm or clone from GitHub. Originally Mapbox GL JS, Vizzuality forked for layer-manager integration. | Mapbox GL JS (proprietary) | Chapter config objects (JS) | Official Mapbox template, widely used | **Not directly usable** -- requires Mapbox GL JS (not MapLibre). But the chapter config format is the exact pattern we should adopt. Vizzuality's `layers-storytelling` extends it with external layer support. The config schema is well-proven. |
| **Svelte + SvelteKit** | Component framework with reactive scroll handling. The Pudding's stack. | npm, requires build tools (Vite internally) | Node.js, bundler | Svelte components | 80k+ stars, v5 stable, active | **The Pudding's production stack.** Excellent for scrollytelling with `svelte-scroller` component. But adopting Svelte means: framework migration, build tooling, component architecture. High quality ceiling but high switching cost. Relevant if/when cheias.pt graduates to a full app. |
| **Intersection Observer (native)** | Browser API for detecting element visibility. | Built into all modern browsers. Zero library needed. | None | DOM elements | Web platform standard | **Already sufficient** for basic scroll triggers. scrollama is a thin wrapper around this. For a vanilla JS project, using native IntersectionObserver directly is viable and eliminates the scrollama dependency entirely. The current prototype doesn't use scroll, but when it does, IntersectionObserver is the foundation. |

### 1E. Weather-Specific Libraries

| Library | What it Renders | Integration Path | Map Library Compat | Data Format | Maturity | Notes |
|---------|----------------|-----------------|-------------------|-------------|----------|-------|
| **webgl-wind** (Mapbox) | GPU wind particles (up to 1M at 60fps) | GitHub clone, no npm | Originally Mapbox GL, can be adapted | PNG textures (U=R, V=G) in plate carree | ~2.6k stars, Mapbox official, but **unmaintained** since ~2019 | The original reference implementation for GPU wind particles. Excellent algorithm (particle advection + ping-pong framebuffers for trail rendering). Our prototype's wind system is derived from this approach. The code is educational but not drop-in usable with MapLibre v4. |
| **windgl** (AstroSat) | Wind particles as Mapbox custom layer, up to 1M at 60fps | GitHub clone, forks exist for MapLibre | Originally Mapbox GL. MapLibre forks exist (windgl-js by illogicz/lunaseasolutions) | PNG textures (U=R, V=G) + JSON metadata (min/max ranges) | **Unmaintained.** Author left AstroSat. Known bugs. | Better architecture than webgl-wind (custom layer integration) but abandoned. The MapLibre forks are community-maintained with varying quality. Our custom implementation in the prototype is more reliable. |
| **leaflet-velocity** | Wind/ocean current arrows and particles for Leaflet | npm, Leaflet plugin | Leaflet only (not MapLibre or deck.gl) | JSON with header (nx, ny, dx, dy) + data array | ~700 stars, Leaflet ecosystem | **Not compatible.** Leaflet-only. Would need complete rewrite for MapLibre/deck.gl. Skip. |
| **weather-maps** (fbrosda) | MapLibre custom layers for weather visualization (wind particles, weather fronts) | GitHub clone | MapLibre GL JS | Various | Small project, experimental | Interesting reference for custom weather layers in MapLibre but not production-ready. |

### 1F. Animation / Rendering Libraries

| Library | What it Does | Integration Path | Relevance | Maturity | Notes |
|---------|-------------|-----------------|-----------|----------|-------|
| **GSAP** (GreenSock) | Timeline-based DOM/SVG/Canvas animation. Tweens, sequences, easing. | CDN: `cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js` | **High.** Layer crossfades, panel reveals, number counters, timeline scrubbing. | 20.6k stars, industry standard, **now 100% free.** | The premiere animation library. All plugins now free (ScrollTrigger, SplitText, MorphSVG, DrawSVG). Ideal for: animating chapter text reveals, smooth opacity transitions on layer toggles, number ticker animations for statistics, coordinated multi-element animations. CDN-loadable, no build tools needed. |
| **anime.js** | Lightweight DOM/SVG/CSS animation | CDN available | **Low.** GSAP does everything anime.js does, with better performance and more plugins. | 50k+ stars but less actively maintained than GSAP | Skip. GSAP is strictly superior for this project's needs, and now has the same price (free). |
| **Lottie / lottie-web** | Pre-rendered After Effects animations as JSON | CDN: `cdnjs.cloudflare.com/ajax/libs/bodymovin/5.13.0/lottie.min.js` | **Niche.** Could be used for editorial illustrations (storm icons, water drop animations, loading states). | 30k+ stars (airbnb/lottie-web) | Not useful for data visualization. Useful for editorial design elements IF someone creates After Effects animations. Adds ~250KB. Low priority. |
| **Three.js** | Full 3D WebGL/WebGPU rendering engine | CDN or npm | **Overkill.** deck.gl + MapLibre handle all 2D map + data viz needs. Three.js would only matter for: 3D terrain flythrough, volumetric cloud rendering, or dramatic 3D effects. None of these are in the design document. | 102k+ stars, extremely active | Skip for v0. If future versions want 3D terrain or atmospheric cross-sections, revisit. Adding Three.js alongside deck.gl creates WebGL context conflicts and doubles bundle size. |
| **regl** | Functional WebGL abstraction (low-level) | CDN: `unpkg.com/regl` (~21KB gzipped) | **Low.** Only relevant if writing custom WebGL shaders. deck.gl uses luma.gl (not regl) internally. | 5.1k stars, stable but low activity | Our wind particle system could be rewritten in regl for better performance, but the current approach (deck.gl BitmapLayer + JS advection) works. Only reach for regl if we need >50k particles at 60fps. |

---

## 2. Scrollytelling Framework Comparison

### The Decision

For cheias.pt v0, **scrollama** is the right choice, optionally complemented by **GSAP** for polish animations.

### Reasoning

| Criterion | scrollama | GSAP ScrollTrigger | Svelte | Native IntersectionObserver |
|-----------|----------|-------------------|--------|---------------------------|
| CDN-loadable (no build tools) | Yes | Yes | No | Yes (browser API) |
| Vanilla JS (no framework) | Yes | Yes | No (Svelte framework) | Yes |
| Scroll position detection | Core feature | Core feature | Via component | Manual implementation |
| Sticky graphic pattern | Built-in | Via `pin: true` | Manual | Manual |
| Step progress (0-100%) | Built-in | Via `scrub` | Manual | Manual |
| Animation orchestration | No (just events) | Full timeline engine | Reactive transitions | No |
| Learning curve | Low (5 methods) | Medium (rich API) | High (new framework) | Low (1 API) |
| Bundle size | ~3KB | ~30KB (core + ScrollTrigger) | N/A (build-time) | 0KB |
| Used by | The Pudding, NYT | Many studios | The Pudding (newer work) | Everyone (underlying API) |

### Recommended Pattern

```
scrollama (step detection) + GSAP (animation polish) + MapLibre flyTo (camera)
```

scrollama fires events when chapter steps enter/exit the viewport. On each event:
1. MapLibre `flyTo()` handles camera transitions (already excellent, no library needed)
2. Layer opacity changes via MapLibre `setPaintProperty()` or deck.gl prop updates
3. GSAP handles UI animations: text panel reveals, number tickers, basemap tint shifts
4. GSAP ScrollTrigger (optionally) provides scroll-scrubbed progress for smooth effects between chapters

This combination is CDN-loadable, vanilla JS, and matches the design document's architecture spec exactly.

### What Vizzuality Uses

Vizzuality's `layers-storytelling` framework is built on the **Mapbox Storytelling template** with their Layer Manager integration. It uses:
- Chapter config objects (declarative camera + layer definitions)
- IntersectionObserver for scroll detection
- Mapbox GL JS `flyTo()` for camera transitions

The chapter config format from Vizzuality is the **exact pattern** cheias.pt should adopt -- it's proven across multiple production platforms. The difference is that we use MapLibre instead of Mapbox GL JS, which is a drop-in replacement for the camera and layer APIs.

### What The Pudding Uses

The Pudding has evolved from scrollama (which Russell Goldenberg created) to **Svelte + SvelteKit** with custom scroll components. Their `svelte-starter` template includes pre-built scrollytelling components. This represents the highest quality ceiling for scrollytelling but requires adopting the Svelte framework and build tools.

### What NYT/WaPo Use

Major newsrooms use custom internal tools. NYT has proprietary scroll-animation frameworks. The common denominator is IntersectionObserver + custom animation code. No single framework dominates.

---

## 3. Data Format Bridge

### Our Data Inventory

| Data Type | Files | Format | Size | Current Consumer |
|-----------|-------|--------|------|-----------------|
| Wind U/V | 409 pairs | COG (GeoTIFF) on R2 | ~50KB each | geotiff.js -> canvas -> deck.gl BitmapLayer |
| MSLP | 409 files | COG on R2 | ~30KB each | geotiff.js -> canvas -> deck.gl BitmapLayer |
| Satellite IR | 49 files | COG on R2 | ~200KB each | geotiff.js -> canvas -> deck.gl BitmapLayer |
| Soil moisture | 77 daily | COG on R2 | ~30KB each | geotiff.js -> canvas -> deck.gl BitmapLayer |
| Precipitation | 77 daily | COG on R2 + 77 PNGs | ~30KB / ~50KB each | COG or pre-rendered PNGs |
| Flood extent | 1 file | PMTiles | ~2MB | MapLibre vector source |
| Basins | 1 file | GeoJSON | ~500KB | MapLibre GeoJSON source |
| Districts | 1 file | GeoJSON | ~200KB | MapLibre GeoJSON source |
| Discharge | 8 JSON files | Frontend JSON | ~50KB each | Custom JS charting |
| Soil moisture grid | 1 JSON file | Frontend JSON | ~200KB | Custom JS rendering |
| Precip frames | 1 JSON file | Frontend JSON (342 pts x 77 days) | ~300KB | Custom JS rendering |
| Lightning | 1 file | GeoJSON / PMTiles | ~50KB | MapLibre source |
| MSLP contours | 1 file | GeoJSON (single timestep) | ~100KB | MapLibre line layer |
| Wind barbs | 1 file | GeoJSON (single timestep) | ~500KB | deck.gl custom rendering |

### Conversion Requirements Per Library

#### Wind Particles (Effect 1)

**Current approach (working):** geotiff.js reads U/V COGs -> JS extracts grid -> custom particle advection loop -> deck.gl PathLayer renders trails.

**deck.gl-particle approach (dead):** Would need COG -> PNG texture conversion (encode U in R channel, V in G channel, with min/max metadata). The library is archived. Skip.

**WeatherLayers GL approach:** Accepts GeoTIFF directly (geotiff.js >= 3.0.0). No conversion needed. But requires npm + bundler.

**deck.gl-raster approach:** Could render wind speed magnitude as colored raster directly from COG. For particles, still need custom code.

**Verdict:** Keep custom implementation. It works, it's flexible, and avoids dependencies.

#### MSLP Isobars (Effect 3)

**Current approach:** Single-timestep GeoJSON contours loaded from file.

**d3-contour approach (recommended):**
```
COG (MSLP) -> geotiff.js readRasters() -> flat Float32Array
-> d3.contours().size([width, height]).thresholds([960, 964, ..., 1040])
-> GeoJSON MultiPolygon features
-> Reproject from pixel coords to geographic coords using COG bbox
-> Add as MapLibre GeoJSON source (line layer)
```
This pipeline can run client-side for each timestep on scrub. Performance: ~10ms per contour generation on a 200x200 grid. Observable has a working "GeoTIFF Contours" example.

**Conversion needed:** The d3-contour output is in pixel coordinates. Must transform to geographic coordinates using the COG bounding box: `lng = bbox[0] + (pixelX / width) * (bbox[2] - bbox[0])`. This is a simple affine transform.

#### Precipitation Sweep (Effect 2)

**Current approach:** Pre-rendered PNG frames for each day (77 frames in `data/raster-frames/precipitation/`). Also available as COG on R2.

**No conversion needed.** Two paths available:
1. **PNG frames:** Load as MapLibre image source, crossfade between frames (simplest)
2. **COG:** Render with geotiff.js + colormap each timestep (current pipeline)

Both work. PNG frames are simpler for the scrollytelling crossfade pattern.

#### Satellite Cloud Motion (Effect 4)

**Current approach:** 49 IR COGs rendered via geotiff.js pipeline.

**deck.gl-raster approach (ideal):** Would handle COG tiling, overview selection, and colormapping automatically. But requires npm.

**No conversion needed.** Current geotiff.js pipeline works. For scrollytelling, pre-render to PNG frames (49 images) for simpler crossfade animation.

#### Atmospheric River Tracks (Chapter 2)

**TripsLayer approach:**
```
IVT data (lat, lon, magnitude, timestamp) -> Convert to waypoint format:
[{
  waypoints: [
    {coordinates: [-30, 25], timestamp: t0},
    {coordinates: [-20, 30], timestamp: t1},
    ...
    {coordinates: [-9, 39], timestamp: tN}
  ]
}]
```
Timestamps must survive `Math.fround()` -- use relative seconds from epoch start, not raw unix milliseconds.

**d3-geo great circle approach:**
```
d3.geoGreatArc()({source: [-30, 25], target: [-9, 39]})
-> Array of interpolated [lng, lat] points along geodesic
-> Feed to deck.gl PathLayer or ArcLayer
```
Simpler than TripsLayer if animation isn't needed. For a static atmospheric river track, this is sufficient.

**flowmap.gl approach:**
```
locations: [
  {id: 'atlantic_source', lat: 25, lon: -30},
  {id: 'portugal_target', lat: 39, lon: -9}
]
flows: [
  {origin: 'atlantic_source', dest: 'portugal_target', count: 800}  // IVT magnitude
]
```
Visually compelling but conceptually wrong -- IVT is a continuous field, not origin-destination pairs. Skip.

#### Discharge Data (Chapter 5)

**Observable Plot approach (sidebar sparklines):**
```javascript
Plot.lineY(tejoData, {x: "date", y: "discharge", stroke: "#e74c3c"}).plot({
  width: 300, height: 60, marginLeft: 30, axis: null
})
```
Clean, CDN-loadable, designed for exactly this use case.

**deck.gl PathLayer approach (map rivers with thickness):**
```
basins.geojson river features -> width = discharge_value / max_discharge * 8
-> deck.gl PathLayer with getWidth accessor
```
Animate width over time as discharge increases during storm events.

---

## 4. Architecture Implications

### The Central Question: Does the creative vision require graduating from single-file HTML?

**Answer: Not for v0. Yes for v1.**

### What Works in Single-File (v0)

The current prototype demonstrates that a production-quality scrollytelling piece CAN be built with CDN-loaded libraries:

```html
<!-- All CDN-loadable, zero build tools -->
<script src="https://unpkg.com/maplibre-gl@^4.0.0/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/deck.gl@^9.0.0/dist.min.js"></script>
<script src="https://unpkg.com/@deck.gl/geo-layers@^9.0.0/dist.min.js"></script>
<script src="https://unpkg.com/@deck.gl/aggregation-layers@^9.0.0/dist.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/scrollama@3/build/scrollama.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
<script type="module">
  import { fromUrl } from 'https://esm.sh/geotiff@2.1.3';
  import * as d3Contour from 'https://esm.sh/d3-contour@4';
  import * as Plot from 'https://esm.sh/@observablehq/plot@0.6';
</script>
```

Total CDN payload: ~600KB gzipped. Reasonable for a scrollytelling piece.

This CDN stack covers:
- Map rendering (MapLibre)
- Data layer rendering (deck.gl)
- COG loading (geotiff.js via ESM)
- MSLP isobar generation (d3-contour)
- Scroll detection (scrollama)
- UI animation (GSAP)
- Discharge sparklines (Observable Plot)
- Wind particles (custom code, already built)
- Temporal animation (custom code, already built)

### What Requires Build Tools (v1)

Two libraries would significantly improve quality but require npm + bundler:

1. **deck.gl-raster** (Development Seed): Replaces our manual COG -> canvas -> BitmapLayer pipeline with proper GPU-accelerated rendering, automatic COG tiling, overview selection, and colormap application. This is the #1 quality improvement available.

2. **WeatherLayers GL**: Provides production-grade weather visualization layers that exceed what we can hand-build. But the licensing is ambiguous and it's a heavy dependency.

### Minimal Build Setup (When the Time Comes)

Based on what Development Seed and The Pudding use:

**Vite** is the answer. Reasons:
- Development Seed's deck.gl-raster uses standard ES modules (Vite-friendly)
- The Pudding uses SvelteKit (which uses Vite internally)
- Vite requires near-zero config for a vanilla JS/TS project
- `vite build` produces optimized ES module bundles
- Dev server with HMR for iteration speed

```
# Minimal Vite setup
npm create vite@latest cheias-pt -- --template vanilla
npm install maplibre-gl deck.gl @deck.gl/geo-layers
npm install @developmentseed/deck.gl-raster  # when ready
npm install scrollama gsap d3-contour @observablehq/plot geotiff
```

### Development Seed's Stack

From their GitHub organization (677 repos):
- **Backend:** Python (FastAPI, titiler, eoAPI, pgSTAC)
- **Frontend:** TypeScript, deck.gl, MapLibre
- **Key project:** deck.gl-raster (GPU COG rendering) -- their newest frontend library
- **Key project:** stac-map (TypeScript, MapLibre + deck.gl-raster)
- **No strong framework opinion visible** -- they use vanilla TS and deck.gl, not React/Next.js

### Vizzuality's Stack

From their GitHub (450 repos) and methodology analysis:
- **Frontend:** React 17+, Redux/Redux Toolkit, Next.js, TypeScript
- **Mapping:** ArcGIS JS (Half-Earth), MapLibre + deck.gl (landgriffon, GFW)
- **Build:** Vite (newer projects), webpack (older)
- **Animation:** CSS transitions, custom requestAnimationFrame loops
- **Scrollytelling:** Mapbox Storytelling template fork (layers-storytelling)

### Recommendation

**v0 (now):** Single-file HTML with CDN dependencies. Proves the concept. Deployable to GitHub Pages. Matches design document spec. Graduate the prototype into a multi-file structure (index.html + src/*.js + style.css) for code organization, but keep CDN loading.

**v1 (after creative direction):** Vite + npm. Unlock deck.gl-raster for proper COG rendering. Keep the same MapLibre + deck.gl + scrollama architecture. The transition is mechanical, not architectural.

---

## 5. Surprising Combinations

### TripsLayer for Atmospheric Rivers

deck.gl's TripsLayer is designed for vehicle trips but can animate ANY timestamped path. An atmospheric river is a path of moisture from the tropics to mid-latitudes -- it has a geographic trajectory and a temporal progression.

**How it would work:**
- Generate waypoints along the IVT maxima at each timestep (from ERA5 IVT COGs)
- Each waypoint: `{coordinates: [lng, lat], timestamp: hours_since_start}`
- `trailLength` = 24 (hours) creates a 24-hour trailing ribbon
- `fadeTrail: true` makes older positions transparent
- Color by IVT magnitude (250-800+ kg/m/s)

The result: an animated ribbon flowing from the Atlantic to Portugal, visually showing the moisture highway. This is the most compelling way to visualize Chapter 2 (The Atlantic Engine) and would be a portfolio-defining visual.

### d3-contour + MapLibre for Dynamic Isobars

d3-contour generates GeoJSON polygons from gridded data. Combined with our COG pipeline, this creates real-time isobar generation:

```
User scrubs timeline -> load MSLP COG for timestep -> geotiff.js extracts grid
-> d3.contours() generates isobar GeoJSON -> MapLibre setData() updates lines
```

The isobars smoothly evolve as the user scrubs through time. This replicates the Windy.com effect (Effect 3) with open-source tools and our existing data.

### HeatmapLayer for Soil Moisture Saturation Narrative

Instead of rendering soil moisture as colored grid cells, use deck.gl HeatmapLayer:
- Higher saturation = higher weight = brighter, wider heatmap glow
- As scroll progresses through Chapter 3, increase weights over time
- The ground literally "fills with light" as soil saturates

This is more emotionally impactful than colored squares -- it evokes the water metaphor from the design document.

### Observable Plot Inline in Scroll Panels

Embed small Observable Plot charts directly in the glassmorphism scroll panels:
- Chapter 3: Soil moisture timeline showing saturation rise
- Chapter 5: Discharge hydrograph for the river being discussed
- Chapter 7: Precondition index sparkline showing the cascade

These inline charts ground the map data in quantitative context without requiring the user to leave the narrative. The charts can be scroll-triggered (appear when the chapter panel enters).

### BitmapLayer Crossfade for Temporal Animation

The prototype already implements A/B buffer crossfade for COG layers. This same pattern, applied to precipitation PNG frames, creates the Windy.com-style temporal sweep (Effect 2):

- Buffer A displays frame N at opacity 1.0
- Buffer B loads frame N+1 in background
- On advance: animate A opacity 1.0 -> 0.0, B opacity 0.0 -> 1.0 over 300ms
- Swap: B becomes A, load next frame into new B

This is already in the prototype code (the `rasterBuf` dual-buffer system). It just needs to be wired to the scroll/timeline system.

### deck.gl ArcLayer for Storm Track Visualization

The prototype already uses ArcLayer for "storm arcs." A creative extension: use ArcLayer to show the causal chain in Chapter 7 (The Full Picture):

- Arc from Atlantic moisture source to Portugal (blue: moisture transport)
- Arc from rainfall area to river catchment (cyan: runoff)
- Arc from dam to downstream community (red: flood propagation)

Height and color encode the magnitude. The arcs create a visual "network of causality" over the map.

---

## 6. Recommendations

### Per-Effect Library Picks

| Visual Effect | Primary Library | Secondary | Data Pipeline | Build Required? |
|---------------|----------------|-----------|---------------|----------------|
| **Wind particles** (Effect 1) | Custom code (already built) | -- | geotiff.js -> U/V grid -> JS advection -> deck.gl PathLayer | No |
| **Precipitation sweep** (Effect 2) | MapLibre image source crossfade | deck.gl BitmapLayer dual-buffer | Pre-rendered PNGs or COG -> canvas | No |
| **MSLP isobars** (Effect 3) | d3-contour + MapLibre line layer | geotiff.js for COG loading | COG -> flat array -> d3.contours() -> GeoJSON -> MapLibre | No |
| **Satellite cloud motion** (Effect 4) | MapLibre image source crossfade | deck.gl BitmapLayer | IR COGs -> pre-render to PNG frames | No |
| **Synoptic chart composite** (Effect 5) | d3-contour (isobars) + custom icons (wind barbs) + MapLibre raster (precip) | deck.gl IconLayer for barbs | Multi-layer composite, most complex | No |
| **Layer transitions** (Effect 6) | GSAP for UI, MapLibre for map | scrollama for triggers | N/A | No |
| **Scrollytelling** | scrollama (step detection) | GSAP ScrollTrigger (polish) | Chapter config objects | No |
| **Camera transitions** | MapLibre `flyTo()` / `easeTo()` | -- | Chapter camera definitions | No |
| **Discharge sparklines** | Observable Plot | -- | Frontend JSON -> Plot.lineY() | No |
| **Before/after satellite** | maplibre-gl-compare | -- | Two map instances with different imagery | No |
| **Atmospheric river animation** | deck.gl TripsLayer | d3-geo (great circle generation) | IVT data -> waypoint conversion | No (TripsLayer in CDN geo-layers bundle) |

### Top 5 Libraries to Add (Priority Order)

1. **scrollama** -- The foundation for the scroll-driven narrative. ~3KB. CDN-loadable. Required.
2. **GSAP + ScrollTrigger** -- Animation polish for chapter transitions, text reveals, and layer crossfades. ~30KB total. CDN-loadable. Now free. High impact on perceived quality.
3. **d3-contour** -- Generates MSLP isobars from COG data client-side. ~10KB. CDN-loadable via ESM. Unlocks Effect 3 (isobar animation) which is central to the synoptic weather narrative.
4. **Observable Plot** -- Inline sparkline charts for discharge, soil moisture, and precondition index. ~50KB. CDN-loadable. Adds quantitative depth to the narrative panels.
5. **maplibre-gl-compare** -- Before/after satellite slider for Chapter 6 (human cost). ~5KB. CDN-loadable. High emotional impact with minimal implementation effort.

### Libraries to Skip

- **WeatherLayers GL**: Too heavy a dependency, licensing ambiguity, requires bundler. Our custom code does 80% of what it offers.
- **deck.gl-particle**: Archived. Dead project. Our custom implementation is better.
- **flowmap.gl**: Conceptually wrong fit for moisture transport (not origin-destination data).
- **nebula.gl / editable-layers**: Not relevant for scrollytelling.
- **leaflet-velocity**: Wrong ecosystem (Leaflet, not MapLibre).
- **anime.js**: GSAP is strictly superior and now free.
- **Three.js**: Overkill. No 3D requirements in the design document.
- **Lottie**: Only useful if someone creates After Effects animations. Low priority.
- **maplibre-contour**: For DEM elevation only, not arbitrary gridded data.
- **maplibre-gl-particle** (Oseenix): 1 star, unmaintained, known bugs.

### Library to Adopt Later (v1)

- **deck.gl-raster** (Development Seed): The #1 quality upgrade. Proper GPU COG rendering replaces our manual pipeline. Requires Vite + npm but the payoff is significant: automatic tiling, overview selection, colormap application, and reprojection. This is what Development Seed uses internally -- adopting it signals technical alignment.

---

## 7. Summary: The v0 Stack

```
MapLibre GL JS v4 ................. Map rendering, camera, vector layers
deck.gl v9 (CDN bundle) .......... BitmapLayer, PathLayer, ArcLayer, TripsLayer, etc.
geotiff.js (ESM) .................. COG loading and decoding
scrollama (CDN) ................... Scroll-driven chapter detection
GSAP + ScrollTrigger (CDN) ....... Animation polish, layer crossfades
d3-contour (ESM) .................. MSLP isobar generation from gridded data
Observable Plot (ESM) ............. Inline sparkline charts
maplibre-gl-compare (CDN) ........ Before/after satellite slider
Custom wind particle system ....... Already implemented in prototype

Total additional payload: ~100KB gzipped (scrollama + GSAP + d3-contour + Plot)
Build tools required: None
Deployment target: Static files (GitHub Pages / Netlify / Vercel)
```

This stack implements all 6 visual effects from the motion analysis, all 9 chapters from the design document, and meets the Vizzuality quality bar for environmental data storytelling -- without requiring a single npm install or build step.
