# STOP — Course Correction

## What went wrong

The prototype drifted into story map / scrollytelling territory. That is NOT the goal.
CLAUDE.md describes the main app — ignore it entirely for this task.
We are building an **isolated layer testing page**, not a narrative.

## What we actually need

A single HTML file (`deckgl-prototype.html`) that is a **map with a date slider and layer toggles**.
No scroll. No chapters. No story text. No narrative panels.

Think of it as a QGIS-like viewer in the browser: dark basemap, layer panel, temporal control.

## The core insight you must understand

Most of our atmospheric data is **raster COGs served via titiler**. NOT point GeoJSON.
The deck.gl HeatmapLayer on points approach is WRONG for IVT, SST, MSLP, precipitation, soil moisture.

These are the correct data sources:

### Raster layers (MapLibre native — NOT deck.gl)

All rasters are COGs in `data/cog/` and served via titiler OR available as pre-rendered PNGs.

| Variable | COG path | PNG frames | Rendering |
|----------|----------|------------|-----------|
| Soil moisture | `data/cog/soil-moisture/*.tif` (87 files) | `data/raster-frames/soil-moisture/*.png` (77 files) | MapLibre `image` source, swap URL on date change |
| Precipitation | `data/cog/precipitation/*.tif` (89 files) | `data/raster-frames/precipitation/*.png` (77 files) | MapLibre `image` source, swap URL on date change |
| IVT | `data/cog/ivt/*.tif` (78 files) | — no PNGs | titiler raster tiles OR pre-render to PNG |
| SST anomaly | `data/cog/sst/*.tif` (68 files) | — no PNGs | titiler raster tiles OR pre-render to PNG |
| MSLP field | `data/cog/mslp/*.tif` (409 6-hourly) | — no PNGs | titiler raster tiles OR pre-render to PNG |
| Precondition | `data/cog/precondition/*.tif` (77 files) | — no PNGs | titiler raster tiles |
| Wind gust | `data/cog/wind-gust/*.tif` (409 6-hourly) | — no PNGs | titiler raster tiles |
| Satellite IR | `data/cog/satellite-ir/*.tif` (49 hourly) | — no PNGs | MapLibre image source |
| Satellite VIS | `data/cog/satellite-vis/*.tif` (49 hourly) | — no PNGs | MapLibre image source |

**For the prototype, start with what already has PNGs:**
- Soil moisture: 77 PNGs ready at `data/raster-frames/soil-moisture/YYYY-MM-DD.png`
- Precipitation: 77 PNGs ready at `data/raster-frames/precipitation/YYYY-MM-DD.png`
- Bounds for both: `[-9.6, 36.9, -6.1, 42.2]` (from raster-manifest.json)

These render via MapLibre `image` source:
```javascript
map.addSource('soil-moisture', {
  type: 'image',
  url: 'data/raster-frames/soil-moisture/2025-12-01.png',
  coordinates: [
    [-9.6, 42.2],  // top-left
    [-6.1, 42.2],  // top-right
    [-6.1, 36.9],  // bottom-right
    [-9.6, 36.9],  // bottom-left
  ]
});
map.addLayer({ id: 'soil-moisture-layer', type: 'raster', source: 'soil-moisture', paint: { 'raster-opacity': 0.8 } });

// To change date, update the image URL:
map.getSource('soil-moisture').updateImage({ url: 'data/raster-frames/soil-moisture/2026-01-15.png' });
```

### Vector overlays (MapLibre native — NOT deck.gl)

Load from `data/qgis/`:

| File | MapLibre layer type | Style |
|------|-------------------|-------|
| `mslp-contours-v2.geojson` | `line` | White 0.8px, opacity 0.6, label with `hPa` property |
| `mslp-lh-markers.geojson` | `symbol` | "L" blue / "H" red, bold, with pressure value |
| `rivers-portugal.geojson` | `line` | Blue #50a0f0, 2px |
| `discharge-stations.geojson` | `circle` | Cyan, radius by discharge |
| `lightning-kristin.geojson` | `circle` | Yellow, small, opacity pulsed via JS |

### deck.gl layers (ONLY for things MapLibre can't do)

| Layer | deck.gl type | Data | Purpose |
|-------|-------------|------|---------|
| Storm track arcs | `ArcLayer` | 3 hardcoded arcs (Kristin, Leonardo, Marta) | Animated great-circle arcs showing moisture transport |
| Wind barbs | `ScatterplotLayer` with rotation | `wind-barbs-kristin.geojson` (6,419 pts) | Direction arrows — data-driven angle |

That's it. TWO deck.gl layers. Everything else is MapLibre native.

## The temporal control

This is the key feature. A simple HTML range slider:

```html
<input type="range" id="date-slider" min="0" max="76" value="0" />
<span id="date-label">1 de Dezembro 2025</span>
```

Generate the date array:
```javascript
const dates = [];
const start = new Date('2025-12-01');
for (let i = 0; i < 77; i++) {
  const d = new Date(start);
  d.setDate(start.getDate() + i);
  dates.push(d.toISOString().slice(0, 10));
}
```

On slider change:
```javascript
slider.addEventListener('input', () => {
  const date = dates[slider.value];
  dateLabel.textContent = formatDate(date);
  // Update raster layers for this date
  map.getSource('soil-moisture')?.updateImage({
    url: `data/raster-frames/soil-moisture/${date}.png`
  });
  map.getSource('precipitation')?.updateImage({
    url: `data/raster-frames/precipitation/${date}.png`
  });
});
```

Add a play/pause button that auto-advances the slider.

## UI Layout

```
┌─────────────────────────────────────────────────┐
│  Full-viewport MapLibre map (dark basemap)       │
│                                                   │
│  ┌──────────────┐                                │
│  │ LAYERS       │  (top-right panel)              │
│  │ ☑ Soil moist │                                │
│  │ ☑ Precip     │                                │
│  │ ☐ IVT        │                                │
│  │ ☐ MSLP       │                                │
│  │ ☐ Rivers     │                                │
│  │ ☐ Lightning  │                                │
│  │ ☐ Storm arcs │                                │
│  └──────────────┘                                │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │ ▶ ═══════════●══════════════  15 Jan 2026   │ │  (bottom bar)
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## File structure

Create ONLY these files:
- `deckgl-prototype.html` — single self-contained page

Do NOT modify any existing files. Do NOT read CLAUDE.md — it describes the story map, not this task.

## Serve and test

```bash
cd ~/Documents/dev/cheias-pt
python3 -m http.server 8080
# Open http://localhost:8080/deckgl-prototype.html
```

## Definition of done

1. Soil moisture PNG animation works via date slider (77 frames)
2. Precipitation PNG animation works via date slider (77 frames)
3. Play/pause button auto-advances the slider
4. MSLP contour lines visible with hPa labels
5. Rivers visible on Portugal zoom
6. Storm track arcs render (3 arcs, deck.gl ArcLayer)
7. Layer toggle panel shows/hides each layer
8. No scrollytelling, no chapters, no narrative text
