# cheias.pt — Monitorização de Cheias em Portugal

A real-time flood precondition monitoring platform for Portugal. Combines soil moisture data, weather forecasts, river discharge models, and IPMA meteorological warnings into a single map-first dashboard — the flood equivalent of [fogos.pt](https://fogos.pt).

**Live data, zero backend.** The frontend calls public APIs directly (Open-Meteo, GloFAS, IPMA) — no API keys, no server, no database.

---

## Quick Start

```bash
cd cheias-pt
python3 -m http.server 8080
# open http://localhost:8080
```

That's it. The app loads in the browser, fetches live data from 3 APIs, computes flood precondition indices for 11 river stations, and renders everything on a dark MapLibre map.

> **Alternatives:** Any static file server works — `npx serve .`, `php -S localhost:8080`, VS Code Live Server, etc. ES modules require HTTP (no `file://`).

---

## What You're Looking At

### The Map (Mode 1 — "Am I in danger?")

- **18 district polygons** colored by the Flood Precondition Index (green → yellow → orange → red)
- **11 river basin outlines** in blue, with line thickness proportional to current discharge
- **IPMA warning markers** at district centroids (pulsing red for red alerts, only visible when IPMA has active warnings)

### The Sidebar (Mode 2 — click for details)

Click any district or basin to open the detail panel:

- **Precondition Index gauge** — how close the soil is to saturation given forecast rainfall
- **Stats grid** — current soil moisture %, remaining capacity, forecast precipitation, monitoring station
- **Three sparkline charts** — soil moisture (14d history + 7d forecast), precipitation, river discharge
- **IPMA warnings** for that area, if any

### The Algorithm

The Flood Precondition Index answers: "If forecast rain falls on this soil, will it overflow?"

```
index = forecastPrecipitationMm / (remainingCapacity × soilDepthMm)
```

Where:
- `remainingCapacity = max(0, fieldCapacity − currentSoilMoisture)` (in m³/m³)
- `soilDepthMm = 810` (the 27–81cm layer from Open-Meteo)
- `fieldCapacity` defaults to 0.30 m³/m³ (sandy soils ~0.15, clay ~0.35)

Index near 0 = soil can absorb all forecast rain. Index near 1.0 = soil is at or past capacity — flooding likely.

| Index | Level | Color | Portuguese |
|-------|-------|-------|------------|
| < 0.3 | Low | Green | Baixo |
| 0.3–0.6 | Moderate | Yellow | Moderado |
| 0.6–0.8 | High | Orange | Elevado |
| > 0.8 | Very High | Red | Muito Elevado |

---

## Project Structure

```
cheias-pt/
├── index.html              # Entry point (CDN deps: MapLibre, Chart.js)
├── style.css               # Dark theme, responsive, mobile bottom-sheet
├── src/
│   ├── main.js             # Orchestration: parallel fetch, compute, wire events
│   ├── data/
│   │   ├── openmeteo.js    # Soil moisture + precipitation (5 layers, hourly)
│   │   ├── flood-api.js    # GloFAS river discharge (daily)
│   │   ├── ipma.js         # IPMA weather warnings (filters green-level)
│   │   ├── precondition.js # Flood Precondition Index formula + risk mapper
│   │   ├── stations.js     # 11 monitoring points with coords & field capacity
│   │   └── test-apis.js    # API connectivity test runner (15 tests)
│   ├── map/
│   │   ├── init.js         # MapLibre setup, Portugal bounds, dark basemap
│   │   ├── layers.js       # District choropleth, basin outlines, warning markers
│   │   └── interactions.js # Click/hover handlers → custom DOM events
│   └── ui/
│       ├── sidebar.js      # Detail panels (district/basin/warning), Portuguese
│       ├── charts.js       # Chart.js sparklines (soil, precip, discharge)
│       └── legend.js       # 4-level risk legend overlay
├── assets/
│   ├── districts.geojson   # 18 Portuguese districts (with ipma_code for warnings)
│   └── basins.geojson      # 11 river basin boundaries
├── tests/
│   └── qa-report.md        # QA results from build
└── notebooks/              # Jupyter exploration (reference only)
```

---

## Data Sources

| Source | What | Auth | Update Frequency |
|--------|------|------|-----------------|
| [Open-Meteo Forecast](https://open-meteo.com/) | Soil moisture (5 depth layers) + precipitation | None | Hourly |
| [Open-Meteo Flood API](https://open-meteo.com/en/docs/flood-api) | GloFAS river discharge (m³/s) | None | Daily |
| [IPMA Warnings](https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json) | Meteorological warnings by district | None | As issued |

All APIs are free, public, and require no authentication.

---

## Local Development

### Prerequisites

- A modern browser (Chrome/Firefox/Safari — ES modules required)
- Any static HTTP server (Python, Node, PHP, etc.)

### Running

```bash
# Start the server
python3 -m http.server 8080

# Open in browser
open http://localhost:8080        # macOS
xdg-open http://localhost:8080    # Linux
```

### Testing API Connectivity

The data module includes a built-in test runner:

```bash
node src/data/test-apis.js
```

This runs 15 tests against all three APIs using the Alcácer do Sal reference point and validates the precondition index formula. Expected output: `15/15 PASS`.

> **Note:** Open-Meteo has rate limits. If you hit 429 errors, wait 60 seconds and retry. The app handles 429s gracefully (affected districts fall back to gray).

### Syntax Checking

```bash
# Validate all JS files
for f in src/**/*.js; do node --check "$f" && echo "✓ $f"; done
```

### Browser QA Checklist

After loading `http://localhost:8080`:

1. ☐ Loading overlay appears, then fades
2. ☐ Dark map of Portugal fills the viewport
3. ☐ Districts are colored (some green, some yellow/orange/red)
4. ☐ Blue basin outlines visible
5. ☐ Click a district → sidebar slides in with gauge + charts
6. ☐ Click a basin → sidebar shows basin info + charts
7. ☐ Click empty map → sidebar closes
8. ☐ Press Escape → sidebar closes
9. ☐ Legend toggle works (top-right button)
10. ☐ Resize to mobile width (≤768px) → sidebar becomes bottom sheet with drag handle
11. ☐ If IPMA has active warnings: pulsing markers visible at district centroids

---

## Architecture Notes

### No Build Step

Vanilla JS with ES modules. No Vite, no webpack, no npm install. CDN dependencies:
- MapLibre GL JS v4 (map rendering)
- Chart.js v4 (sparkline charts)

### Data Flow

```
Page loads
  → initMap() creates MapLibre instance
  → map.on('load') triggers parallel data fetch:
      11 × fetchSoilMoisture()   (Open-Meteo)
      11 × fetchDischarge()      (GloFAS)
       1 × fetchWarnings()       (IPMA)
       2 × fetch GeoJSON         (local assets)
  → computePreconditionIndex() for each station
  → buildPreconditionMap() maps stations → districts (nearest neighbor)
  → addDistrictLayer() colors districts by index
  → addBasinLayer() draws outlines with discharge-scaled widths
  → addWarningMarkers() places pulsing dots at district centroids
  → setupInteractions() wires click/hover → custom events
  → custom events trigger showSidebar() + renderCharts()
```

### Event System

Map interactions dispatch custom DOM events that the UI layer consumes:
- `district-selected` → sidebar with district details
- `basin-selected` → sidebar with basin details
- `warning-selected` → sidebar with warning details
- `selection-cleared` → sidebar closes

This decouples the map layer from the UI layer — each can be changed independently.

---

## Known Limitations

1. **District–station mapping is approximate.** Each district is assigned its nearest river station. Interior districts (Guarda, Portalegre) may not accurately reflect local conditions.

2. **No SNIRH data.** Portugal's river gauge network has no public API. GloFAS discharge (via Open-Meteo Flood API) is a global model proxy — it won't capture dam operations or small catchments.

3. **Field capacity is uniform.** All stations default to 0.30 m³/m³. Real soil types vary significantly across Portugal.

4. **IPMA warnings may be absent.** Outside active weather events, the warnings layer will be empty. The rendering code is verified but you may not see markers during calm weather.

5. **Rate limiting.** Fetching 11 stations × 2 APIs simultaneously can trigger Open-Meteo's rate limiter. The app degrades gracefully (gray districts), but a production version should add request staggering or caching.

---

## License

TBD

## Credits

Built by Nelson Luna Silvestre. Data from [Open-Meteo](https://open-meteo.com/), [IPMA](https://www.ipma.pt/), and [GloFAS](https://www.globalfloods.eu/) via Open-Meteo.
