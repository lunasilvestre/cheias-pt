# deck.gl Atmospheric Visualization — Prototype Spec

## Goal

Build a standalone HTML page (`deckgl-prototype.html`) that proves deck.gl integration
with MapLibre GL JS using the QGIS-derived vector data. This page tests the exact
layers needed for Chapter 2 (Atlantic Energy) and Chapter 5 (Rivers) of the
cheias.pt scrollytelling, isolated from scroll logic.

## Why Standalone Page, Not Notebook

- deck.gl is browser WebGL — pydeck adds abstraction that hides real integration issues
- Must validate `MapboxOverlay` + MapLibre interop specifically
- GeoJSON files from QGIS load directly via `fetch()`
- Working JS code copies straight into `src/deck-overlay.js` in the main app
- Live reload with `npx serve` — faster iteration than Jupyter

## Data Assets (all exist in data/qgis/)

| File | Features | deck.gl Layer | Priority |
|------|----------|---------------|----------|
| `ivt-peak-storm.geojson` | 1,102 pts | `HeatmapLayer` — atmospheric river heat surface | P0 |
| `mslp-contours-v2.geojson` | 28 lines | `GeoJsonLayer` or native MapLibre line | P0 |
| `mslp-lh-markers.geojson` | 7 pts | `TextLayer` — "L"/"H" pressure labels | P0 |
| `wind-barbs-kristin.geojson` | 6,419 pts | `ScatterplotLayer` with rotation or `IconLayer` | P1 |
| `lightning-kristin.geojson` | 262 pts | `ScatterplotLayer` with pulsing animation | P1 |
| `rivers-portugal.geojson` | 264 lines | `PathLayer` or native MapLibre line | P0 |
| `discharge-stations.geojson` | 11 pts | `ScatterplotLayer` with size = discharge ratio | P0 |

### Additional raster overlays (image sources, not deck.gl)

| File | Use |
|------|-----|
| `renders/ch2-sst-atlantic.png` | MapLibre image source — SST anomaly background for Ch2 |
| `data/raster-frames/soil-moisture/*.png` | 77 PNG frames — existing image source animation |
| `data/raster-frames/precipitation/*.png` | 77 PNG frames — existing image source animation |

### Storm tracks (must generate — simple manual GeoJSON)

Create `data/qgis/storm-tracks.geojson` with approximate paths for:
- Kristin (Jan 27-29): mid-Atlantic → Portuguese coast
- Leonardo (Feb 5-7): similar track, slightly south
- Marta (Feb 9-11): wider track, hitting southern Portugal/Spain

These are simple LineStrings with `name` and `date` properties.
Use deck.gl `ArcLayer` for dramatic "moisture highway" visualization
or `PathLayer` with dashed animation.

## Architecture

```
deckgl-prototype.html
├── MapLibre GL JS (basemap + native vector layers)
├── deck.gl MapboxOverlay (atmospheric layers on top)
│   ├── IVT HeatmapLayer (atmospheric river)
│   ├── StormTrack ArcLayer (moisture transport arcs)
│   ├── Lightning ScatterplotLayer (pulsing dots)
│   ├── Wind Barbs IconLayer (directional arrows)
│   ├── Discharge ScatterplotLayer (sized by ratio)
│   └── Rivers PathLayer (flow animation)
├── Native MapLibre layers
│   ├── MSLP contour lines (line layer from GeoJSON)
│   ├── MSLP L/H markers (symbol layer)
│   └── SST anomaly (image source overlay)
└── UI Controls
    ├── Layer toggle checkboxes
    └── Chapter preset buttons (Ch2 view, Ch5 view)
```

## Key Technical Details

### deck.gl + MapLibre Integration

```javascript
import { MapboxOverlay } from '@deck.gl/mapbox';
// NOTE: MapboxOverlay works with MapLibre despite the name

const overlay = new MapboxOverlay({ interleaved: true, layers: [] });
map.addControl(overlay);

// Update layers dynamically:
overlay.setProps({ layers: [newLayer1, newLayer2] });
```

### IVT HeatmapLayer (the atmospheric river)

```javascript
new HeatmapLayer({
  id: 'ivt-heatmap',
  data: ivtData.features,
  getPosition: d => d.geometry.coordinates,
  getWeight: d => d.properties.ivt,
  radiusPixels: 60,
  intensity: 1,
  threshold: 0.05,
  colorRange: [
    [0, 128, 0, 25],    // transparent green (low IVT)
    [255, 255, 0, 100],  // yellow
    [255, 165, 0, 180],  // orange
    [255, 0, 0, 220],    // red (high IVT = atmospheric river core)
  ],
})
```

### Storm Track ArcLayer

```javascript
new ArcLayer({
  id: 'storm-arcs',
  data: stormSegments, // [{source: [-30,35], target: [-8,39], name: 'Kristin'}, ...]
  getSourcePosition: d => d.source,
  getTargetPosition: d => d.target,
  getSourceColor: [52, 152, 219, 180],  // blue (Atlantic)
  getTargetColor: [231, 76, 60, 220],    // red (Portugal impact)
  getWidth: 4,
  greatCircle: true,
})
```

### Lightning ScatterplotLayer (with animation)

```javascript
new ScatterplotLayer({
  id: 'lightning',
  data: lightningData.features,
  getPosition: d => d.geometry.coordinates,
  getRadius: 3000,
  getFillColor: [255, 255, 0, 200],
  radiusMinPixels: 2,
  radiusMaxPixels: 8,
  // Animate via periodic layer updates changing opacity/radius
})
```

### Rivers PathLayer

```javascript
new PathLayer({
  id: 'rivers',
  data: riverData.features,
  getPath: d => d.geometry.coordinates,
  getColor: [80, 160, 240, 180],
  getWidth: 2,
  widthMinPixels: 1,
  widthMaxPixels: 4,
  // getDashArray for animated flow effect
})
```

## NPM Dependencies

```bash
cd ~/Documents/dev/cheias-pt
npm install @deck.gl/core @deck.gl/layers @deck.gl/aggregation-layers @deck.gl/mapbox
```

The prototype HTML loads deck.gl from CDN for simplicity:
```html
<script src="https://unpkg.com/deck.gl@9/dist.min.js"></script>
```

For production (main app), use npm imports via the existing build pipeline.

## UI Layout

Simple dark page with:
- Full-viewport MapLibre map (CARTO Dark Matter basemap)
- Layer toggle panel (top-right, checkboxes for each layer)
- Two preset buttons: "Ch2: Atlântico" and "Ch5: Rios"
  - Ch2 preset: zoom to Atlantic [-30, 35, z3], show IVT + MSLP + storm arcs + SST
  - Ch5 preset: zoom to Portugal [-8.4, 39.6, z8], show rivers + discharge + soil moisture

## Success Criteria

1. IVT heatmap renders over the Atlantic showing the atmospheric river corridor
2. MSLP contour lines display with hPa labels
3. Storm track arcs animate from Atlantic to Portugal
4. Rivers visible and labeled on Portugal zoom
5. Discharge stations sized by ratio
6. Lightning pulses during Kristin overlay
7. All layers toggle on/off independently
8. No WebGL context conflicts between deck.gl and MapLibre
9. Smooth camera transitions between Ch2 and Ch5 presets
10. Performance acceptable (~30fps) with all P0 layers active

## Transfer to Main App

Once validated, the working code becomes `src/deck-overlay.js`:

```javascript
// src/deck-overlay.js
import { MapboxOverlay } from '@deck.gl/mapbox';
import { HeatmapLayer, ArcLayer, ScatterplotLayer, PathLayer } from '@deck.gl/layers';

export function createDeckOverlay(map) { ... }
export function setChapter2Layers(overlay, data) { ... }
export function setChapter5Layers(overlay, data) { ... }
export function clearDeckLayers(overlay) { ... }
```

Then `chapter-wiring.js` calls these on chapter enter/exit.
