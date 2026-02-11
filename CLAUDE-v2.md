# cheias.pt — Flood Monitoring Platform for Portugal

## Mission

Build the **fogos.pt equivalent for floods** — a citizen-facing map that any Portuguese person can open and immediately understand their flood risk. Portfolio piece targeting Development Seed (Lisbon + DC), demonstrating cloud-native geospatial frontend skills.

**Current context (Feb 2026):** Portugal is under calamity declaration (68 municipalities). Storms killed 15 people. Tejo peaked at 8,600 m³/s. This platform would be immediately useful TODAY.

## Current Phase: 1 — Mode 1 + Mode 2 (Map Dashboard)

We are building the **map dashboard**. No AI/chat agent. No backend. The frontend calls APIs directly.

### Mode 1: Glance (the "am I in danger?" view)
- Full-screen MapLibre map of Portugal
- Color-coded regions by Flood Precondition Index (green/yellow/orange/red)
- IPMA weather warnings as colored polygons
- GloFAS river discharge markers along major rivers

### Mode 2: Explore (click for details)
- Click a basin/municipality → sidebar panel slides in
- Sparkline charts: soil moisture (14d), precipitation forecast (7d), river discharge
- Precondition Index breakdown with gauges
- Active IPMA warnings for that area

## Critical: Existing Intelligence

**Read before building.** Extensive discovery research exists:

| What | Where |
|------|-------|
| Portuguese data sources | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/01-portuguese-data-sources.md` |
| Satellite & European data | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/02-satellite-european-data.md` |
| DevSeed patterns | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/03-devseed-patterns-for-floods.md` |
| GeoAgent design | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/04-geoagent-design.md` |
| Competitive landscape | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/05-competitive-landscape.md` |
| Synthesis & architecture | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/06-synthesis.md` |
| Flood dynamics & prediction | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/07-flood-dynamics-prediction.md` |
| Interface comparison | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/08-interface-comparison.md` |
| Data exploration notebook | `notebooks/01-data-exploration.ipynb` |

---

## Agent Team Structure

Use delegate mode. Spawn 4 teammates with clear file ownership.

### Teammate 1: Data Agent
**Owns:** `src/data/`

Build the API client layer and precondition index calculator:
- `src/data/openmeteo.js` — Open-Meteo client for soil moisture + precipitation
- `src/data/flood-api.js` — Open-Meteo Flood API client for GloFAS discharge
- `src/data/ipma.js` — IPMA warnings client
- `src/data/precondition.js` — Flood Precondition Index calculator
- `src/data/stations.js` — Monitoring point definitions (coordinates + metadata)

Each module must export pure async functions that return structured data. No DOM manipulation. No map references. Every function must handle fetch errors gracefully and return a consistent error shape.

**Test your own work:** After building each module, write a test script `src/data/test-apis.js` that calls every function and logs the results. Run it with `node src/data/test-apis.js` to verify all APIs respond. If an API fails, fix the client or document the failure clearly.

### Teammate 2: Map Agent
**Owns:** `src/map/`, `assets/`

Build the MapLibre map with data visualization layers:
- `src/map/init.js` — Map initialization, Portugal bounds, base style
- `src/map/layers.js` — Layer definitions: basin choropleth, warning polygons, discharge markers
- `src/map/interactions.js` — Click handlers, hover effects, popup management
- `assets/basins.geojson` — Portuguese river basin boundaries
- `assets/districts.geojson` — IPMA district/warning area boundaries

**GeoJSON Sourcing (CRITICAL — read this carefully):**

Getting real basin and district boundaries is the hardest part. Follow this priority order:

1. **CAOP (Carta Administrativa Oficial):** Check https://www.dgterritorio.gov.pt for official Portuguese administrative boundaries. Download NUTS III or district-level shapefiles and convert to GeoJSON with `ogr2ogr`.

2. **Natural Earth + simplification:** Download admin level 1 from https://www.naturalearthdata.com/downloads/10m-cultural-vectors/ — filter to Portugal, simplify with mapshaper.

3. **OpenStreetMap via Overpass:** Query Portuguese district boundaries from OSM.

4. **Fallback — generate approximate polygons:** If all above fail within 15 minutes, create a simplified GeoJSON with approximate polygon boundaries for Portugal's 18 districts and 8 major river basins. Use known coordinates of district capitals as polygon centers. This is the MINIMUM VIABLE approach — clearly comment that these are approximate and need replacement.

**DO NOT** hallucinate URLs or assume file downloads will work. If a download fails, move to the next option immediately.

**IPMA Warning Area mapping:**
The IPMA API uses area codes (AVR, BGC, CBR, etc.). You need a mapping from these codes to geographic polygons. The simplest approach: create a lookup object in `src/map/ipma-areas.js` that maps each code to a center point + approximate radius, or to district polygon IDs in your GeoJSON.

```
AVR: Aveiro, BGC: Bragança, CBR: Coimbra, CTB: Castelo Branco
EVR: Évora, FAR: Faro, GDA: Guarda, LRS: Leiria
LSB: Lisboa, PTG: Portalegre, PRT: Porto, STR: Santarém
STB: Setúbal, VCT: Viana do Castelo, VRL: Vila Real, VSE: Viseu
```

### Teammate 3: UI Agent
**Owns:** `src/ui/`, `style.css`, `index.html`

Build the page shell, sidebar, charts, and visual components:
- `index.html` — Single page app shell with MapLibre CSS/JS from CDN, dark header, map container, sidebar container
- `style.css` — Full responsive styles, dark theme, sidebar slide animation, mobile breakpoints
- `src/ui/sidebar.js` — Detail sidebar: opens on click, shows location data, charts, warnings
- `src/ui/charts.js` — Chart.js sparklines using Chart.js from CDN (soil moisture, precipitation, discharge)
- `src/ui/legend.js` — Risk level legend overlay on map
- `src/ui/loading.js` — Loading states, skeleton screens while APIs respond
- `src/main.js` — App orchestration: initializes map, loads data, wires up interactions

**Design Requirements:**
- Map-first: 100% viewport, no chrome on load
- Dark header bar: logo "cheias.pt" top-left, minimal controls top-right
- Sidebar slides from right, dismissible, contains charts
- All user-facing text in Portuguese
- Mobile-responsive: sidebar becomes bottom sheet on mobile
- Smooth transitions, animated chart drawing

**Color Palette:**
- Risk: `#2ecc71` (green/baixo) → `#f1c40f` (yellow/moderado) → `#e67e22` (orange/elevado) → `#e74c3c` (red/muito elevado)
- Water: `#3498db`
- Dark background: `#1a1a2e`
- Use these exact hex values for consistency

**CDN Dependencies (add to index.html):**
```html
<link href="https://unpkg.com/maplibre-gl@4/dist/maplibre-gl.css" rel="stylesheet" />
<script src="https://unpkg.com/maplibre-gl@4/dist/maplibre-gl.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
```

### Teammate 4: QA Agent
**Owns:** `tests/`, nothing else. Reads everything.

You are the quality gate. The user is away and cannot test manually. Your job:

**Phase 1 — API Verification (start immediately, don't wait for other agents):**
1. Run `curl` against every API endpoint to verify they respond:
   ```bash
   # Open-Meteo soil moisture
   curl -s "https://api.open-meteo.com/v1/forecast?latitude=38.3725&longitude=-8.5153&hourly=soil_moisture_27_to_81cm&past_days=1&forecast_days=1" | head -c 200

   # Open-Meteo Flood API
   curl -s "https://flood-api.open-meteo.com/v1/flood?latitude=38.3725&longitude=-8.5153&daily=river_discharge&past_days=1&forecast_days=1" | head -c 200

   # IPMA Warnings
   curl -s "https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json" | head -c 200
   ```
2. Document any API that fails or returns unexpected format in `tests/api-status.md`
3. Message the Data Agent immediately if any API is down or has changed format

**Phase 2 — Integration Check (after teammates report progress):**
1. Start a local HTTP server: `python3 -m http.server 8080` from project root
2. Use `curl http://localhost:8080/` to verify index.html loads
3. Check that all `<script>` and `<link>` tags reference files that exist
4. Verify every JS file parses without syntax errors: `node --check src/data/*.js src/map/*.js src/ui/*.js src/main.js`
5. Check GeoJSON files are valid JSON: `node -e "JSON.parse(require('fs').readFileSync('assets/basins.geojson','utf8'))"`

**Phase 3 — Smoke Test (after all agents report done):**
1. Verify file structure matches spec (all expected files exist)
2. Run the test-apis.js script the Data Agent created
3. Check for common bugs:
   - Are there `console.log` statements left in production code? (a few are OK for MVP)
   - Does index.html reference all JS modules correctly?
   - Are there hardcoded localhost URLs that should be API URLs?
   - Do CSS class names in JS match class names in CSS?
4. Write a final report in `tests/qa-report.md` with pass/fail for each check

**If you find issues:** Message the responsible agent with the specific problem. Don't fix files you don't own. Wait for them to fix and re-check.

---

## Data Sources — Tested and Confirmed

### 1. Open-Meteo (soil moisture + precipitation)
```
GET https://api.open-meteo.com/v1/forecast
  ?latitude=38.3725&longitude=-8.5153
  &hourly=soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,soil_moisture_27_to_81cm
  &hourly=precipitation
  &past_days=14&forecast_days=7
```

### 2. Open-Meteo Flood API (GloFAS discharge)
```
GET https://flood-api.open-meteo.com/v1/flood
  ?latitude=38.3725&longitude=-8.5153
  &daily=river_discharge
  &past_days=14&forecast_days=7
```

### 3. IPMA Warnings API
```
GET https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json
```
Returns warnings with: awarenessTypeName, awarenessLevelID, text, startTime, endTime, idAreaAviso.

## Precondition Index Formula

```javascript
function computePreconditionIndex(soilMoisture, forecastPrecipMm, fieldCapacity = 0.30) {
  const soilMoistureRatio = soilMoisture / fieldCapacity;
  const remainingCapacity = Math.max(0, fieldCapacity - soilMoisture);
  const soilDepthMm = 810; // 27-81cm layer depth

  if (remainingCapacity <= 0.001) return 1.0; // Saturated

  const index = Math.min(1.0, forecastPrecipMm / (remainingCapacity * soilDepthMm));
  return index;
}

// Risk thresholds:
// < 0.3: Low (green)    — Baixo
// 0.3-0.6: Moderate (yellow) — Moderado
// 0.6-0.8: High (orange) — Elevado
// > 0.8: Very High (red) — Muito Elevado
```

Use deepest soil moisture layer (27-81cm) for saturation. Surface layers fluctuate too much.

**Field capacity by soil type:**
- Sandy (Alentejo coast): ~0.15 m³/m³
- Clay (Tejo valley): ~0.35 m³/m³
- Default: ~0.30 m³/m³

## Monitoring Points

| Basin | Lat | Lon | Notes |
|-------|-----|-----|-------|
| Tejo (Santarém) | 39.4614 | -8.5193 | RED ALERT — peaked 8,600 m³/s |
| Sado (Alcácer do Sal) | 38.3725 | -8.5153 | Active flooding, primary test case |
| Mondego (Coimbra) | 40.2033 | -8.4103 | High discharge |
| Douro (Porto) | 41.1496 | -8.6109 | Elevated |
| Guadiana (Mértola) | 38.0144 | -7.8625 | Monitoring |
| Vouga (Aveiro) | 40.6405 | -8.6538 | Affected area |
| Lis (Leiria) | 39.7437 | -8.8070 | Affected area |
| Zêzere (Constância) | 39.6000 | -8.2333 | Tejo tributary |

## MapLibre Configuration

- **CDN:** MapLibre GL JS v4+ from unpkg
- **Base style:** `https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json`
- **Portugal bounds:** `[[-9.52, 36.96], [-6.19, 42.15]]`
- **Max bounds:** `[[-10.5, 35.5], [-5.0, 43.5]]` (slight padding)

## File Structure

```
cheias-pt/
├── CLAUDE.md              # This file
├── index.html             # Single page app (UI Agent)
├── style.css              # Styles (UI Agent)
├── src/
│   ├── main.js            # App orchestration (UI Agent)
│   ├── data/              # === DATA AGENT OWNS ===
│   │   ├── openmeteo.js   # Soil moisture + precipitation client
│   │   ├── flood-api.js   # GloFAS discharge client
│   │   ├── ipma.js        # IPMA warnings client
│   │   ├── precondition.js# Precondition Index calculator
│   │   ├── stations.js    # Monitoring point definitions
│   │   └── test-apis.js   # API verification script
│   ├── map/               # === MAP AGENT OWNS ===
│   │   ├── init.js        # Map setup, bounds, controls
│   │   ├── layers.js      # Choropleth, markers, warning polygons
│   │   ├── interactions.js# Click, hover, sidebar triggers
│   │   └── ipma-areas.js  # IPMA area code → geography mapping
│   └── ui/                # === UI AGENT OWNS ===
│       ├── sidebar.js     # Detail panel component
│       ├── charts.js      # Chart.js sparklines
│       ├── legend.js      # Risk level legend
│       └── loading.js     # Loading states
├── assets/                # === MAP AGENT OWNS ===
│   ├── basins.geojson     # River basin boundaries
│   └── districts.geojson  # District boundaries for IPMA overlay
├── tests/                 # === QA AGENT OWNS ===
│   ├── api-status.md      # API availability report
│   └── qa-report.md       # Final quality report
└── README.md
```

**⚠️ FILE OWNERSHIP IS STRICT.** Do not edit files outside your directory. If you need something from another agent's module, message them with the interface you need (function name, parameters, return shape).

## Interface Contracts

Agents must agree on these interfaces. Data Agent exports, Map/UI Agents consume.

```javascript
// src/data/openmeteo.js
export async function fetchSoilMoisture(lat, lon) → {
  timestamps: string[],
  layers: {
    '0_1cm': number[], '1_3cm': number[], '3_9cm': number[],
    '9_27cm': number[], '27_81cm': number[]
  },
  precipitation: number[]
}

// src/data/flood-api.js
export async function fetchDischarge(lat, lon) → {
  dates: string[],
  discharge: number[]
}

// src/data/ipma.js
export async function fetchWarnings() → [{
  type: string,
  level: 'green'|'yellow'|'orange'|'red',
  text: string,
  startTime: string,
  endTime: string,
  areaCode: string
}]

// src/data/precondition.js
export function computePreconditionIndex(soilMoisture, forecastPrecipMm, fieldCapacity?) → number
export function getRiskLevel(index) → { level: string, color: string, label: string }

// src/data/stations.js
export const STATIONS = [{ id, name, basin, lat, lon, fieldCapacity? }]
```

## What "Done" Looks Like

A person opens `index.html` served from a local HTTP server and sees:
1. ✅ Portugal map with dark basemap, centered on mainland
2. ✅ Colored markers/regions showing flood risk for each monitoring point
3. ✅ IPMA warning indicators visible on the map
4. ✅ River discharge markers with color-coded levels
5. ✅ Click any point → sidebar slides in with charts and data
6. ✅ Sidebar shows soil moisture sparkline, precip forecast, discharge trend
7. ✅ Precondition Index displayed with visual gauge
8. ✅ Works on mobile viewport (sidebar → bottom sheet)
9. ✅ QA report exists in tests/qa-report.md with all checks passing
10. ✅ All text visible to users is in Portuguese

## What NOT To Build

- ❌ No AI chat / GeoAgent (Mode 3 — later)
- ❌ No FastAPI backend
- ❌ No user accounts or saved locations
- ❌ No satellite imagery (Sentinel-2, NDWI)
- ❌ No historical analysis
- ❌ No news feed
- ❌ No notifications
- ❌ No build tools (Vite, webpack) — vanilla JS with ES modules + CDN
