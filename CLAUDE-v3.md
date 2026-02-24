# cheias.pt — Flood Monitoring Platform for Portugal

## Mission

Build the **fogos.pt equivalent for floods** — a citizen-facing map that any Portuguese person can open and immediately understand their flood risk. Portfolio piece targeting Development Seed (Lisbon + DC).

**Current context (Feb 11, 2026):** Portugal under calamity declaration (69 municipalities). Four-week storm train: Kristin → Leonardo → Marta → atmospheric river. Today a Mondego dike burst at Casais, A1 cut, 3,600 evacuated in Coimbra. Tejo special flood plan at RED. All major rivers at capacity. €2.5B aid package. This platform is needed NOW.

## Current Phase: Mode 1 + Mode 2 (Map Dashboard)

No AI chat. No backend. Frontend calls APIs directly.

### Mode 1: Glance ("am I in danger?")
- Full-screen MapLibre map of Portugal
- District polygons colored by Flood Precondition Index (green/yellow/orange/red)
- IPMA weather warnings as prominent markers with severity color and full text
- River basin outlines with discharge indicators

### Mode 2: Explore (click for details)
- Click a district or basin → sidebar slides in from right
- Sparkline charts: soil moisture (14d), precipitation forecast (7d), river discharge
- Precondition Index breakdown: soil moisture %, remaining capacity, forecast rain
- Active IPMA warnings for that area with full text, severity, and time range

## What NOT To Build

- ❌ No historical time slider (sparklines give 14-day context)
- ❌ No news feed or news scraping
- ❌ No AI chat / GeoAgent
- ❌ No FastAPI backend
- ❌ No user accounts, saved locations, notifications
- ❌ No satellite imagery (Sentinel-2, NDWI)
- ❌ No build tools (Vite, webpack) — vanilla JS with ES modules + CDN

---

## Geographic Assets (READY — do not regenerate)

Both files are validated and ready in `assets/`:

| Asset | Features | Size | Key Properties |
|-------|----------|------|----------------|
| `assets/districts.geojson` | 18 | 27 KB | `district`, `ipma_code`, `idDistrito` |
| `assets/basins.geojson` | 11 | 64 KB | `river`, `name_pt`, `type`, `transboundary` |

**Critical integration notes:**
- District `ipma_code` maps directly to IPMA API's `idAreaAviso` — use this to join warnings to polygons
- Basin boundaries don't align with districts — use both layers independently, don't try to merge
- Point-in-polygon lookup: any lat/lon can be routed to its district + basin
- GloFAS has data for major basins but may miss smaller coastal ones — degrade gracefully
- Notebook `02-geographic-assets.ipynb` has full analysis

## Existing Intelligence

Discovery research in vault — read if you need context, don't duplicate:

| What | Where |
|------|-------|
| Portuguese data sources | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/01-portuguese-data-sources.md` |
| Flood dynamics & prediction | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/07-flood-dynamics-prediction.md` |
| Interface comparison | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/08-interface-comparison.md` |
| Data exploration | `notebooks/01-data-exploration.ipynb` |
| Geographic asset analysis | `notebooks/02-geographic-assets.ipynb` |

---

## Agent Team Structure

Use delegate mode (Shift+Tab). Spawn **3 teammates** with strict file ownership.

### Teammate 1: Data Agent
**Owns:** `src/data/`

Build API clients and precondition index calculator:
- `src/data/openmeteo.js` — soil moisture + precipitation (past 14d + forecast 7d)
- `src/data/flood-api.js` — GloFAS discharge via Open-Meteo Flood API
- `src/data/ipma.js` — IPMA warnings, normalize to consistent shape
- `src/data/precondition.js` — Flood Precondition Index calculator + risk level mapper
- `src/data/stations.js` — monitoring point definitions with coordinates and field capacity

Each module exports pure async functions. No DOM, no map references. Handle fetch errors gracefully — return `{ error: string }` on failure, never throw.

After building, create `src/data/test-apis.js` that calls every function for the Alcácer do Sal test point and logs results. Run it with `node src/data/test-apis.js` and fix issues before reporting done.

### Teammate 2: Map Agent
**Owns:** `src/map/`

Build MapLibre map with data visualization layers:
- `src/map/init.js` — map setup, Portugal bounds, dark basemap, navigation controls
- `src/map/layers.js` — district choropleth (colored by precondition index), basin outlines, discharge markers, IPMA warning markers
- `src/map/interactions.js` — click handlers for districts/basins → emit events for sidebar

**GeoJSON is ready.** Load `assets/districts.geojson` and `assets/basins.geojson` directly. The district features have `ipma_code` that matches IPMA API's `idAreaAviso` — use this to color warning areas.

**IPMA warnings rendering:** Show as prominent circle markers at district centroids. Color by awareness level. On hover: show warning type + short text. On click: open sidebar with full details. These ARE the "news balloons" — IPMA warning text is rich and authoritative.

### Teammate 3: UI Agent
**Owns:** `src/ui/`, `style.css`, `index.html`, `src/main.js`

Build page shell, sidebar, charts, orchestration:
- `index.html` — single page: dark header with "cheias.pt" logo, map container, sidebar container
- `style.css` — dark theme, sidebar slide animation, mobile bottom-sheet, responsive
- `src/ui/sidebar.js` — detail panel: location info, charts, warnings, precondition gauge
- `src/ui/charts.js` — Chart.js sparklines (soil moisture, precipitation, discharge)
- `src/ui/legend.js` — risk level legend overlay on map
- `src/main.js` — orchestration: init map, load all data in parallel, compute indices, wire interactions

**All user-facing text in Portuguese.** This is for Portuguese citizens during an emergency.

**CDN Dependencies (index.html):**
```html
<link href="https://unpkg.com/maplibre-gl@4/dist/maplibre-gl.css" rel="stylesheet" />
<script src="https://unpkg.com/maplibre-gl@4/dist/maplibre-gl.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
```

### Lead Agent Responsibilities

After all 3 teammates report done:
1. Run `node --check` on every JS file to catch syntax errors
2. Verify all files in the spec exist
3. Start `python3 -m http.server 8080` and verify index.html loads
4. Check that GeoJSON files load (valid JSON, correct paths)
5. Run `src/data/test-apis.js` to verify API connectivity
6. Write `tests/qa-report.md` with pass/fail for each check
7. Fix any integration issues (e.g. mismatched import paths, missing functions)

---

## Data Sources

### 1. Open-Meteo (soil moisture + precipitation)
```
GET https://api.open-meteo.com/v1/forecast
  ?latitude={lat}&longitude={lon}
  &hourly=soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,soil_moisture_27_to_81cm,precipitation
  &past_days=14&forecast_days=7
```

### 2. Open-Meteo Flood API (GloFAS discharge)
```
GET https://flood-api.open-meteo.com/v1/flood
  ?latitude={lat}&longitude={lon}
  &daily=river_discharge
  &past_days=14&forecast_days=7
```

### 3. IPMA Warnings
```
GET https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json
```
Returns: `awarenessTypeName`, `awarenessLevelID`, `text`, `startTime`, `endTime`, `idAreaAviso`

`idAreaAviso` maps to `ipma_code` in `assets/districts.geojson`.

Awareness levels: green (1) / yellow (2) / orange (3) / red (4).

## Precondition Index Formula

```javascript
function computePreconditionIndex(soilMoisture, forecastPrecipMm, fieldCapacity = 0.30) {
  const remainingCapacity = Math.max(0, fieldCapacity - soilMoisture);
  const soilDepthMm = 810; // 27-81cm layer
  if (remainingCapacity <= 0.001) return 1.0;
  return Math.min(1.0, forecastPrecipMm / (remainingCapacity * soilDepthMm));
}
// < 0.3: Baixo (green #2ecc71)
// 0.3-0.6: Moderado (yellow #f1c40f)
// 0.6-0.8: Elevado (orange #e67e22)
// > 0.8: Muito Elevado (red #e74c3c)
```

Use deepest soil layer (27-81cm). Field capacity: sandy 0.15, clay 0.35, default 0.30.

## Monitoring Points

| Basin | Lat | Lon | Notes |
|-------|-----|-----|-------|
| Tejo (Santarém) | 39.4614 | -8.5193 | RED ALERT |
| Sado (Alcácer do Sal) | 38.3725 | -8.5153 | Primary test case |
| Mondego (Coimbra) | 40.2033 | -8.4103 | Dike burst today |
| Douro (Porto) | 41.1496 | -8.6109 | Burst banks |
| Guadiana (Mértola) | 38.0144 | -7.8625 | Monitoring |
| Vouga (Aveiro) | 40.6405 | -8.6538 | Affected |
| Lis (Leiria) | 39.7437 | -8.8070 | Storm Kristin damage |
| Zêzere (Constância) | 39.6000 | -8.2333 | Tejo tributary |
| Sorraia (Coruche) | 38.9572 | -8.5297 | Tejo tributary, significant risk |
| Lima (Viana) | 41.6939 | -8.8300 | North |
| Cávado (Braga) | 41.5240 | -8.4270 | North |

## MapLibre Configuration

- **Base style:** `https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json`
- **Portugal bounds:** `[[-9.52, 36.96], [-6.19, 42.15]]`
- **Max bounds:** `[[-10.5, 35.5], [-5.0, 43.5]]`

## Interface Contracts

Data Agent exports, Map/UI Agents consume:

```javascript
// src/data/openmeteo.js
export async function fetchSoilMoisture(lat, lon)
// → { timestamps, layers: { '27_81cm': number[], ... }, precipitation: number[] }
// → { error: string } on failure

// src/data/flood-api.js
export async function fetchDischarge(lat, lon)
// → { dates, discharge: number[] }

// src/data/ipma.js
export async function fetchWarnings()
// → [{ type, level: 'green'|'yellow'|'orange'|'red', levelId: number, text, startTime, endTime, areaCode }]

// src/data/precondition.js
export function computePreconditionIndex(soilMoisture, forecastPrecipMm, fieldCapacity?) → number
export function getRiskLevel(index) → { level, color, label, labelPt }

// src/data/stations.js
export const STATIONS = [{ id, name, namePt, basin, lat, lon, fieldCapacity? }]
```

## File Structure

```
cheias-pt/
├── CLAUDE.md
├── index.html             # UI Agent
├── style.css              # UI Agent
├── src/
│   ├── main.js            # UI Agent — orchestration
│   ├── data/              # DATA AGENT OWNS
│   │   ├── openmeteo.js
│   │   ├── flood-api.js
│   │   ├── ipma.js
│   │   ├── precondition.js
│   │   ├── stations.js
│   │   └── test-apis.js
│   ├── map/               # MAP AGENT OWNS
│   │   ├── init.js
│   │   ├── layers.js
│   │   └── interactions.js
│   └── ui/                # UI AGENT OWNS
│       ├── sidebar.js
│       ├── charts.js
│       └── legend.js
├── assets/                # READY — do not modify
│   ├── basins.geojson
│   └── districts.geojson
├── tests/
│   └── qa-report.md       # Lead writes this
└── notebooks/             # Reference only
    ├── 01-data-exploration.ipynb
    └── 02-geographic-assets.ipynb
```

**⚠️ FILE OWNERSHIP IS STRICT.** Do not edit files outside your directory.

## Color Palette

- Risk: `#2ecc71` (baixo) → `#f1c40f` (moderado) → `#e67e22` (elevado) → `#e74c3c` (muito elevado)
- Water: `#3498db`
- Dark bg: `#1a1a2e`
- Header: `#16213e`

## Design Requirements

- Map-first: 100% viewport
- Dark header: "cheias.pt" top-left, legend toggle top-right
- Sidebar: slides from right, dismissible, Portuguese text
- Mobile: sidebar becomes bottom sheet
- IPMA warnings: prominent markers at district centroids, color by severity, hover shows type, click opens sidebar
- Smooth transitions on all interactive elements

## What "Done" Looks Like

A person in Coimbra opens cheias.pt on their phone right now and sees:
1. ✅ Dark map of Portugal with districts colored by flood risk
2. ✅ Mondego basin outlined, showing elevated risk
3. ✅ IPMA orange/red warning markers visible across northern/central districts
4. ✅ Click their district → sidebar shows soil moisture near saturation, 60mm forecast rain, precondition index 0.85+
5. ✅ Sparkline charts showing the 4-week rainfall accumulation
6. ✅ All text in Portuguese
7. ✅ Works on mobile
