# deck.gl Dynamic Mapping Examples Collection

Reference collection of deck.gl examples for dynamic, real-time, and animated geospatial visualization — curated for cheias.pt inspiration.

---

## 🌊 Meteorology & Weather

### WeatherLayers GL
**What:** Production-grade weather visualization layers for deck.gl — wind particles, temperature rasters, contours, precipitation, pressure, clouds, ocean currents, air quality.
**Why it matters:** The most complete weather viz solution built on deck.gl. Supports both 2D map and 3D globe views. Integrates with NOAA GFS/HRRR, ECMWF IFS/AIFS, Copernicus CAMS.
- GitHub: https://github.com/weatherlayers/weatherlayers-gl
- Demo: https://weatherlayers.com
- Data sources: NOAA, ECMWF, Météo-France, Copernicus CMEMS

### deck.gl-particle (Wind Animation)
**What:** Open-source particle simulation layer for deck.gl — animated wind flow visualization from GRIB data.
**Why it matters:** Shows how to encode u/v wind components into image textures and render animated particles. Great pattern for any vector field visualization (water flow, currents).
- GitHub: https://github.com/weatherlayers/deck.gl-particle
- Key tech: GRIB → PNG texture via GDAL, ParticleLayer with imageUnscale

### Tempo API (ECMWF Weather Maps)
**What:** Self-hosted weather API serving colorized WebP maps and GeoJSON contours from ECMWF data, with deck.gl BitmapLayer integration.
**Why it matters:** Shows the pattern of serving weather rasters as tiled images consumed by deck.gl BitmapLayer — directly applicable to flood extent visualization.
- GitHub: https://github.com/leoneljdias/tempo
- Stack: FastAPI + ECMWF OpenData + deck.gl BitmapLayer
- Integration: MapLibre, Leaflet, OpenLayers compatible

---

## 🚌 Transportation & Mobility

### MBTA Real-Time Geospatial Pipeline
**What:** End-to-end real-time transit visualization using Spark Streaming + Kafka + MongoDB Change Streams + deck.gl. Tracks Boston buses/trains in real-time with streaming analytics.
**Why it matters:** Full-stack architecture reference for real-time geospatial data pipelines. Events pushed to browser via WebSockets (no polling). Real-time analytics computed on data streams by Spark.
- GitHub: https://github.com/samerelhousseini/Geospatial-Analysis-With-Spark
- Stack: Spark Structured Streaming, Kafka, MongoDB, Node.js, React, deck.gl, React-Vis
- Data: MBTA GTFS-Realtime API

### Paris Public Transit (Reclus)
**What:** Animated visualization of all public transit in the Paris region using deck.gl TripsLayer with GTFS data.
**Why it matters:** Shows the challenge of large-scale transit animation (250MB+ of route data) and creative solutions using TripLayer + TileLayer tiling approach.
- Live demo: https://charnould.github.io/reclus/
- Discussion: https://github.com/visgl/deck.gl/discussions/6986

### All-Transit (TripLayer + TileLayer)
**What:** Animated transit visualization using deck.gl's TripLayer within a TileLayer — each tile renders moving "trail" animations.
**Why it matters:** Clever architecture for scaling animated paths to large datasets by tiling the trip data. Relevant pattern for animating river flow data across Portugal.
- GitHub: https://github.com/kylebarron/all-transit

### Singapore Bus Explorer
**What:** Real-time bus stops and routes with live arrival times for all Singapore bus services, built with deck.gl.
**Why it matters:** Production example of real-time transit data overlaid on interactive maps with per-stop detail views.
- Featured in deck.gl showcase

### Amsterdam Digital Twin
**What:** Real-time 3D visualization of live transit data (GVB buses/trams) in Amsterdam, alongside simulated company vehicles.
**Why it matters:** Combines live transit feeds with 3D models, fleet management, and real-time data via ZeroMQ.
- GitHub topics: `deck-gl`, `digital-twins`, `digital-twin-application`
- Stack: Node.js, ZeroMQ, Google Maps API, deck.gl, 3D models

### Sweden Transport Digital Twin
**What:** Open-source digital twin for transport systems in Sweden with real-time statistics and 3D vector maps.
**Why it matters:** Production-scale open-source transport simulation with Elasticsearch/Kibana for real-time analytics and self-hosted tile server.
- GitHub: https://github.com/PredictiveMovement/digital-twin

---

## 🎬 Animation & Time-Series

### deck.gl TripsLayer (Official)
**What:** The core animated path layer — renders animated trails representing vehicle trips with timestamp-based playback.
**Why it matters:** The foundational pattern for any temporal animation in deck.gl. Directly applicable to animating flood progression, river flow changes, or emergency response routes.
- Docs: https://deck.gl/docs/api-reference/geo-layers/trips-layer
- Animation guide: https://deck.gl/docs/developer-guide/animations-and-transitions
- Data format: waypoints with coordinates + timestamps
- Key props: `currentTime`, `trailLength`, `fadeTrail`

### NYC Taxi Trip Animation (Google Maps + deck.gl)
**What:** Google's official example of animated taxi trips in NYC using TripsLayer over Google Maps basemap.
**Why it matters:** Clean reference implementation of the animation loop pattern (requestAnimationFrame advancing currentTime).
- Docs: https://developers.google.com/maps/documentation/javascript/examples/deckgl-tripslayer

### Deck GL Time Frame Animations (Tutorial)
**What:** Step-by-step tutorial for creating animated visualizations of NYC Taxi data over time.
**Why it matters:** Explains the full animation lifecycle — data preparation, time windowing, playback controls.
- Article: https://ckochis.com/deck-gl-time-frame-animations

### Real-Time Path Layer Update (WebSocket Pattern)
**What:** Discussion and code for updating deck.gl PathLayer in real-time via WebSocket data feeds (5000 vehicles at 30fps).
**Why it matters:** Key patterns for live data: `dataComparator` for efficient updates, async generators for data fetching, real-time position streaming.
- Discussion: https://github.com/visgl/deck.gl/discussions/7068
- Also: https://github.com/visgl/deck.gl/issues/1542 (WebSocket integration)

---

## 🌍 Flow Maps & Migration

### flowmap.gl
**What:** Flow map drawing layer for deck.gl — visualizes movement between geographic locations with animated flow lines. Used for migration, commuting, freight, bicycle sharing, refugee flows.
**Why it matters:** Excellent for visualizing water flow patterns, drainage basins, or population displacement during floods.
- GitHub: https://github.com/visgl/flowmap.gl
- Products: FlowmapBlue (no-code), Flowmap City
- License: Apache-2.0

---

## 🗺️ deck.gl + MapLibre Integration

### Official Integration Guide
Three modes of integration:
1. **Interleaved** — deck.gl renders into MapLibre's WebGL2 context (mix deck.gl layers with MapLibre layers, 3D occlusion)
2. **Overlaid** — deck.gl in separate canvas inside MapLibre's controls container (compatible with MapLibre plugins)
3. **Reverse-controlled** — deck.gl manages MapLibre's camera (multi-view, custom input handling)

- Docs: https://deck.gl/docs/developer-guide/base-maps/using-with-maplibre
- Gallery: https://deck.gl/examples/maplibre
- MapLibre examples: https://maplibre.org/maplibre-gl-js/docs/examples/toggle-deckgl-layer/
- Interleaving demo: https://deck.gl/gallery/maplibre-overlay

### MapLibre v5 Globe View
deck.gl v9.1+ works seamlessly with MapLibre v5 globe view for all three integration modes. No additional configuration needed.

---

## 🔧 Key Layers for cheias.pt

| Layer | Use Case for Flood Monitoring |
|-------|-------------------------------|
| **TripsLayer** | Animate flood progression over time |
| **HeatmapLayer** | Precipitation intensity visualization |
| **GeoJsonLayer** | River basins, flood extent polygons, station markers |
| **BitmapLayer** | Weather radar imagery, satellite flood maps |
| **ScatterplotLayer** | Real-time sensor stations with size/color by water level |
| **ColumnLayer** | 3D columns showing water levels at gauge stations |
| **PathLayer** | River networks with flow-proportional width |
| **ContourLayer** | Flood risk contour lines from elevation data |
| **ParticleLayer** (via weatherlayers) | Animated wind/water flow patterns |
| **IconLayer** | Alert markers, IPMA warnings |

---

## 📚 Official Resources

- **Showcase:** https://deck.gl/showcase — full gallery of production projects
- **Examples repo:** https://github.com/visgl/deck.gl/tree/master/examples
- **Example data:** https://github.com/visgl/deck.gl-data
- **GitHub topics:** https://github.com/topics/deck-gl / https://github.com/topics/deckgl
- **Google Codelab:** https://developers.google.com/codelabs/maps-platform/maps-deck-gl
- **Kepler.gl:** https://kepler.gl — no-code deck.gl-powered geospatial analysis (great for prototyping)

---

## 🏗️ Architecture Patterns for Real-Time

**Pattern 1: WebSocket → deck.gl State**
```
Data Source → WebSocket → React State / Vanilla JS → deck.gl layer props update
```
- Use `dataComparator` for efficient re-renders
- Shallow comparison by default; use custom comparator for partial updates

**Pattern 2: Streaming Pipeline → API → deck.gl**
```
Sensors/API → Kafka → Spark Streaming → MongoDB → Change Streams → Node.js → WebSocket → deck.gl
```
- As demonstrated by the MBTA pipeline

**Pattern 3: Tiled Animation**
```
Pre-computed tiles (vector or raster) → TileLayer → TripsLayer per tile
```
- Scales animated data to millions of points
- As demonstrated by all-transit project

**Pattern 4: BitmapLayer for Rasters**
```
Weather/Satellite API → Tiled WebP/PNG → BitmapLayer with temporal controls
```
- As demonstrated by Tempo API
- Works well for flood extent maps from Copernicus/Sentinel
