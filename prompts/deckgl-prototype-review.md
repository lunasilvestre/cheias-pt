# deck.gl Prototype — Review Notes

## What was built

A standalone layer viewer (`deckgl-prototype.html`) for testing atmospheric and hydrological data layers on a dark basemap with temporal controls.

**Serve with:** `python3 -m http.server 8080` then open `http://localhost:8080/deckgl-prototype.html`

## Architecture

| Concern | Technology | Rationale |
|---------|-----------|-----------|
| Basemap + rasters | MapLibre GL JS v4 | Native `image` source for PNGs, `line`/`circle`/`symbol` for vectors |
| Storm arcs | deck.gl v9 `ArcLayer` | Great-circle arcs not possible in MapLibre natively |
| Wind barbs | deck.gl v9 `ScatterplotLayer` | Data-driven radius + color by wind speed |
| Temporal control | HTML range slider + JS | 77-frame animation (200ms/frame), play/pause, keyboard (space/arrows) |

## Data sources used

### Raster (MapLibre image sources, swap URL on date change)

| Layer | Frames | Path pattern | Bounds |
|-------|--------|-------------|--------|
| Soil moisture | 77 | `data/raster-frames/soil-moisture/YYYY-MM-DD.png` | `[-9.6, 36.9] → [-6.1, 42.2]` |
| Precipitation | 77 | `data/raster-frames/precipitation/YYYY-MM-DD.png` | same |

### Vector (MapLibre native layers from `data/qgis/`)

| Layer | File | Type | Key properties |
|-------|------|------|---------------|
| MSLP contours | `mslp-contours-v2.geojson` | `line` + `symbol` | `hPa` for labels |
| L/H markers | `mslp-lh-markers.geojson` | `symbol` | `type` (L/H), `pressure_hpa` |
| Rivers | `rivers-portugal.geojson` | `line` | `name` |
| Discharge stations | `discharge-stations.geojson` | `circle` + `symbol` | `discharge_max`, `name` |
| Lightning | `lightning-kristin.geojson` | `circle` | 262 flashes, Jan 27-28 |

### deck.gl layers

| Layer | File/Data | Notes |
|-------|-----------|-------|
| Storm arcs | 3 hardcoded arcs | Kristin [-32,34]→[-8.5,41.5], Leonardo, Marta |
| Wind barbs | `wind-barbs-kristin.geojson` | 6,419 pts, color by `speed_ms` |

## What works (verified with screenshots)

- [x] Soil moisture raster animation (Dec 1 dry → Jan 27 saturated)
- [x] Precipitation raster overlay (Jan 27 shows Kristin rainfall in NW)
- [x] Both rasters simultaneously (dual image source)
- [x] Date slider: 77 frames, "1 Dez 2025" → "15 Fev 2026"
- [x] Play/pause button + keyboard shortcuts
- [x] Storm markers on timeline (Kristin, Leonardo, Marta at correct dates)
- [x] Storm arc rendering (3 great-circle curves from Atlantic to Iberia)
- [x] Layer toggle panel (9 independent checkboxes)
- [x] MSLP contour lines with hPa labels
- [x] L/H pressure markers ("L" red, "H" blue)
- [x] Discharge station circles sized by max discharge
- [x] No scrollytelling, no chapters, no narrative text

## What needs attention

### Not yet tested in this session
- Wind barbs toggle (code exists, not screenshot-verified)
- Rivers toggle (native MapLibre line layer — had collision issues in v1, simplified in v2)
- Lightning toggle (native MapLibre circle layer)
- Play animation loop (auto-advance every 200ms)

### Missing data (noted in v2 spec, not blocking)
- IVT raster PNGs not pre-rendered (78 COGs exist at `data/cog/ivt/`)
- SST anomaly PNGs not pre-rendered (68 COGs at `data/cog/sst/`)
- MSLP field PNGs not pre-rendered (409 COGs at `data/cog/mslp/`)
- Precondition PNGs not pre-rendered (77 COGs at `data/cog/precondition/`)

To add these: render COGs to PNGs with consistent bounds, add as additional MapLibre image sources with date-slider integration.

### Design decisions to revisit
- **Storm arcs are hardcoded** — approximate start/end points, not from data
- **MSLP/L/H are static** — one snapshot, not temporal. Would need per-date GeoJSON to animate
- **Lightning is static** — 262 flashes from Kristin only. Could filter by timestamp for temporal
- **Raster bounds** are hardcoded `[-9.6, 36.9, -6.1, 42.2]` — from raster-manifest.json
- **Animation speed** is 200ms/frame — may want configurable (100ms fast, 500ms slow)

## Session history

1. Built v1 prototype with deck.gl HeatmapLayer for IVT + chapter presets (Ch2 Atlantic, Ch5 Rivers)
2. Iterated: smoothed heatmap, added Portuguese charset, storm/discharge labels, river lines
3. **Course correction**: user redirected to v2 spec — raster PNGs via MapLibre, not deck.gl HeatmapLayer
4. Rewrote from scratch as layer viewer with date slider
5. Verified: soil moisture + precipitation rasters, storm arcs, timeline, toggles
6. Pushed 4 commits to `main`
