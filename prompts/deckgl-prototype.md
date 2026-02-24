# deck.gl Atmospheric Visualization Prototype

## Context

You are working on cheias.pt, a Portuguese flood monitoring scrollytelling platform.
The project uses MapLibre GL JS with vanilla JavaScript. We need to integrate deck.gl
for atmospheric visualization layers that will appear in the scrollytelling narrative.

Read `prompts/deckgl-prototype-spec.md` for the full technical specification.
Read `data/qgis/README.md` to understand all available data assets and their formats.

## Task

Build a standalone prototype page `deckgl-prototype.html` in the project root that
demonstrates deck.gl integration with MapLibre using our existing QGIS-derived data.

### Phase 1: Setup & Base Map

1. Create `deckgl-prototype.html` — single self-contained HTML file
2. Load MapLibre GL JS from CDN (same version as index.html: 4.7.1)
3. Load deck.gl from CDN: `https://unpkg.com/deck.gl@9/dist.min.js`
4. Initialize MapLibre with CARTO Dark Matter basemap, centered on [-20, 38], zoom 4
5. Create a `MapboxOverlay` from deck.gl and add it to the map
6. Add a layer toggle panel (top-right) and two preset buttons ("Ch2: Atlântico", "Ch5: Rios")

### Phase 2: Chapter 2 Layers (Atlantic Energy)

Load data from `data/qgis/` directory. All files are GeoJSON.

**P0 layers (must work):**

a) **IVT Heatmap** — Load `data/qgis/ivt-peak-storm.geojson` (1,102 points).
   Use deck.gl `HeatmapLayer` with IVT value as weight.
   Color ramp: transparent → green → yellow → orange → red.
   This should show the atmospheric river corridor from Atlantic to Iberia.

b) **MSLP Contour Lines** — Load `data/qgis/mslp-contours-v2.geojson` (28 isobar lines).
   Render as a native MapLibre `line` layer (not deck.gl — contour lines are simpler in MapLibre).
   Style: white lines, 0.8px, opacity 0.6. Label with hPa values from the `hPa` property.

c) **MSLP L/H Markers** — Load `data/qgis/mslp-lh-markers.geojson` (7 points).
   Render as MapLibre `symbol` layer. "L" in bold blue, "H" in bold red, with pressure value below.

d) **Storm Track Arcs** — Create a small inline GeoJSON or data array with 3 storm tracks:
   - Kristin: source [-28, 38] → target [-8.5, 39.5] (Jan 28-29)
   - Leonardo: source [-25, 35] → target [-8.3, 38.5] (Feb 6-7)
   - Marta: source [-22, 33] → target [-7.5, 37.5] (Feb 10-11)
   Use deck.gl `ArcLayer` with `greatCircle: true`. Blue source → red target colors.
   Width 3-4px. Label each arc with storm name.

**P1 layers (nice to have):**

e) **Lightning** — Load `data/qgis/lightning-kristin.geojson` (262 points).
   deck.gl `ScatterplotLayer`, yellow dots, small radius.

f) **Wind Barbs** — Load `data/qgis/wind-barbs-kristin.geojson` (6,419 points).
   This is complex — if time permits, render as rotated triangles using `ScatterplotLayer`
   with data-driven angle from the `direction` property. Otherwise skip for now.

### Phase 3: Chapter 5 Layers (Rivers Respond)

**P0 layers:**

g) **Rivers** — Load `data/qgis/rivers-portugal.geojson` (264 line segments).
   Use deck.gl `PathLayer` or native MapLibre `line` layer. Blue color (#50a0f0), 2px width.

h) **Discharge Stations** — Load `data/qgis/discharge-stations.geojson` (11 points).
   deck.gl `ScatterplotLayer`. Size each circle by a discharge property if available,
   otherwise uniform cyan dots. Label with station name.

### Phase 4: Preset Views & Toggles

- "Ch2: Atlântico" button: fly to center [-20, 35], zoom 3.5, show IVT + MSLP + arcs + lightning
- "Ch5: Rios" button: fly to center [-8.4, 39.6], zoom 7.5, show rivers + discharge
- Each layer has a checkbox toggle in the panel
- Toggling updates the `MapboxOverlay` layers array via `overlay.setProps()`

### Phase 5: SST Background (if time permits)

The file `renders/ch2-sst-atlantic.png` is a pre-rendered SST anomaly image.
Add it as a MapLibre image source with approximate bounds (check the raster-manifest.json
for bounds reference, but SST covers a wider Atlantic area roughly [-45, 25, 5, 55]).
Show behind the IVT heatmap for Chapter 2 preset.

## Important Notes

- Load data files with `fetch('data/qgis/filename.geojson')` — relative paths work
  because the prototype is served from the project root
- Use `npx serve .` or `python3 -m http.server 8080` to serve the page
- The deck.gl CDN bundle exposes everything under `globalThis.deck` namespace
  (e.g., `deck.HeatmapLayer`, `deck.MapboxOverlay`, `deck.ArcLayer`)
- MapLibre native layers (MSLP contours, L/H markers) go through `map.addSource()` +
  `map.addLayer()` as normal — only the atmospheric/animated layers use deck.gl
- Dark basemap: `https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json`
- Keep the page simple — no build tools, no npm imports, just CDN + vanilla JS
- DO NOT modify any existing project files. This is a standalone prototype.
- Test with: `cd ~/Documents/dev/cheias-pt && python3 -m http.server 8080`
  then open `http://localhost:8080/deckgl-prototype.html`

## Definition of Done

- [ ] IVT heatmap shows atmospheric river corridor across Atlantic
- [ ] MSLP contour lines with hPa labels visible
- [ ] L/H pressure center markers displayed
- [ ] 3 storm track arcs visible (Kristin, Leonardo, Marta)
- [ ] Rivers visible on Portugal zoom
- [ ] Layer toggles work for each layer
- [ ] Ch2/Ch5 preset buttons fly to correct views and toggle correct layers
- [ ] No console errors, no WebGL context conflicts
- [ ] Page loads in <3 seconds on localhost
