# cheias.pt — QGIS Symbology Prototyping

## Mission

Load all cheias.pt raster and vector data into QGIS and build symbology that matches the WeatherWatcher14 video screenshots. The goal is Windy/WXCharts-quality visualizations rendered in QGIS, then exportable as style definitions (QML) for translation to MapLibre/titiler colormaps.

Reference screenshots are in the Obsidian vault:
`~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/16-weather-video-data-sources.md`

The images are accessible via symlink: `assets/cheias-pt/research/youtube/Screenshot_*.png`

## Data Locations

### Existing COGs (77-day series, Dec 2025 – Feb 2026)
```
data/cog/soil-moisture/   # 86 files, 342 grid pts, 0.25° spacing
data/cog/precipitation/   # 89 files, daily accumulation mm
data/cog/sst/             # 67 files, North Atlantic SST anomaly °C
data/cog/ivt/             # 77 files, integrated vapour transport
data/cog/precondition/    # 77 files, flood precondition index (0-1)
```

### New COGs (from NWP acquisition sprint — may not all be available yet)
```
data/cog/mslp/            # Mean sea level pressure (Pa)
data/cog/wind-u/          # 10m U-component wind (m/s)
data/cog/wind-v/          # 10m V-component wind (m/s)
data/cog/wind-gust/       # 10m instantaneous wind gust (m/s)
data/cog/satellite-vis/   # Meteosat visible channel
data/cog/satellite-ir/    # Meteosat IR 10.8μm
data/cog/wind-gust-icon/  # ICON-EU peak gust (if available)
```

### Vector Data
```
data/qgis/discharge-stations.geojson     # 11 river gauge stations
data/qgis/rivers-portugal.geojson        # River network
data/qgis/precondition-basins.geojson    # Basin polygons with precondition
data/qgis/wildfires-combined.pmtiles     # 2024-2025 burn scars
data/qgis/ipma-warnings-timeline.geojson # Warning history
data/qgis/lightning-kristin.geojson      # Lightning (if acquired)
data/flood-extent/combined.pmtiles       # CEMS flood polygons
assets/basins.geojson                    # 11 basins
assets/districts.geojson                 # 18 districts
```

### QGIS Project
Existing: `cheias-scrollytelling.qgz` in project root

## Symbology Targets

Build these layer styles, matching the video screenshots as closely as possible:

### 1. Precipitation Color Ramp (Windy style)
**Reference:** Screenshot_20260219-220341.png (Atlantic scale), Screenshot_20260219-220857.png (Portugal zoom)
- Load: `data/cog/precipitation/2026-01-28.tif` (Storm Kristin peak day)
- Ramp: transparent (0mm) → white (1-5mm) → light blue (5-15mm) → blue (15-30mm) → violet (30-60mm) → pink/magenta (60-100mm) → deep magenta (100+mm)
- Render type: singleband pseudocolor
- Blending: multiply or normal on dark basemap
- Save as: `data/qgis/styles/precipitation-windy.qml`

### 2. MSLP Isobar Contours
**Reference:** Screenshot_20260219-220620.png (Windy MSLP), Screenshot_20260219-221701.png (WXCharts ECMWF)
- Load: `data/cog/mslp/2026-01-28T06.tif` (or nearest available timestep)
- Generate contour lines at 4 hPa intervals using QGIS Processing: `gdal:contour`
- Style contour lines: thin white or light gray, 0.5px, with hPa labels at intervals
- L/H markers: identify local minima/maxima from the pressure field, add point markers with bold "L" (blue) and "H" (red) text labels
- Background: pressure field as color fill (blue=low, red/warm=high) at low opacity
- Save as: `data/qgis/styles/mslp-contours.qml`

### 3. Wind Gust Map (WXCharts ICON-EU style)
**Reference:** Screenshot_20260219-221724.png (vivid purple→green→orange→red, 0-157+ km/h)
- Load: `data/cog/wind-gust/2026-01-28T06.tif` (or wind-gust-icon if available)
- Convert m/s to km/h in expression: `@1 * 3.6`
- Ramp: purple (0-30 km/h) → green (30-60) → yellow (60-90) → orange (90-120) → red (120-157+)
- Render type: singleband pseudocolor
- Save as: `data/qgis/styles/wind-gust-wxcharts.qml`

### 4. Wind Barbs (ARPEGE/Beaufort style)
**Reference:** Screenshot_20260219-221714.png (Beaufort-colored barbs over Iberia)
- Load: `data/cog/wind-u/` + `data/cog/wind-v/`
- Compute wind speed: `sqrt(u² + v²)` and wind direction: `atan2(-u, -v)`
- Subsample to ~50km grid (don't render barbs at every pixel)
- Style: QGIS wind barb marker (built-in), sized by knots, colored by Beaufort scale:
  - 0-5 m/s: light blue
  - 5-10 m/s: green
  - 10-15 m/s: yellow
  - 15-20 m/s: orange
  - 20-30 m/s: red
  - 30+  m/s: dark red/magenta
- Save as: `data/qgis/styles/wind-barbs-beaufort.qml`

### 5. IPMA Radar Composite
**Reference:** Screenshot_20260219-220921.png (cyan→green→yellow on white background)
- Load: `data/radar/` (if available from acquisition sprint)
- Ramp: classic radar — cyan (light) → green (moderate) → yellow (heavy) → red (very heavy)
- This is the standard meteorological precipitation radar colormap
- Save as: `data/qgis/styles/radar-ipma.qml`

### 6. Satellite Imagery (Meteosat)
**Reference:** Screenshot_20260219-220644.png (Storm Kristin comma cloud)
- Load: `data/cog/satellite-vis/` or `satellite-ir/` (if available)
- VIS channel: grayscale or natural color enhancement
- IR channel: inverted grayscale (cold cloud tops = white, warm surface = dark)
- For IR, enhance contrast to highlight the storm's comma head and sting jet tail
- Save as: `data/qgis/styles/satellite-vis.qml`, `satellite-ir.qml`

### 7. Soil Moisture (existing — validate)
- Load: `data/cog/soil-moisture/2026-01-27.tif` (day before Kristin)
- Current ramp should show saturation levels. Compare with scrollytelling rendering.
- Brown (dry, 0.15) → yellow (0.25) → green (0.35) → blue (0.45) → dark blue (saturated, 0.55+)

### 8. Flood Extent (existing — validate)
- Load: `data/flood-extent/combined.pmtiles`
- Semi-transparent blue fill with darker outline
- Compare with scrollytelling rendering

### 9. Lightning Overlay (if available)
- Load: `data/qgis/lightning-kristin.geojson`
- Point markers: yellow lightning bolt icon, small (4-6px)
- Add glow/halo effect for visibility on dark basemap

### 10. IVT / Atmospheric Rivers
- Load: `data/cog/ivt/2026-01-28.tif`
- Ramp: transparent (low) → light green → yellow → orange → red (high IVT)
- This visualizes the atmospheric river feeding moisture to the storm

## Process

1. Open the existing project: `cheias-scrollytelling.qgz`
2. Add each layer, starting with Storm Kristin peak day (Jan 28) as the reference timestep
3. Build symbology for each layer, comparing with the reference screenshots
4. Group layers in the layer panel: `NWP`, `Satellite`, `Radar`, `Hydro`, `Vectors`
5. Export each style as QML to `data/qgis/styles/`
6. Render a map image for each major layer combination for review
7. Save the project

## Style Export Convention

Each QML file in `data/qgis/styles/` should be self-contained and reusable. Name format: `{variable}-{style-variant}.qml`. These will be translated to:
- titiler colormap parameters (for server-side rendering)
- MapLibre `raster-color` expressions (for client-side rendering)
- CSS gradient definitions (for legends)

## Key Visual Notes from the Video

- Dark basemap is essential — all these layers are designed for dark backgrounds
- Windy uses a slight transparency/blend on precipitation to show basemap through
- WXCharts uses opaque fills with isobar lines drawn on top
- The video's impact comes from ANIMATION (time scrubbing). Static QGIS renders will look less dramatic — that's expected. Focus on getting the color ramps right.
- Wind barbs and isobars are the layers that make a synoptic chart look "professional" — prioritize these for visual impact
