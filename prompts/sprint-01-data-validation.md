# cheias.pt — Data Validation & Scroll Scaffold Sprint

## Mission

Validate that the data tells the story before we build the story. We have a design document (`~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/12-design-document.md`) for a scrollytelling piece about Portugal's Jan–Feb 2026 flood crisis. Before building the frontend, we need to confirm the data actually shows what the narrative claims: soil saturating over weeks, rivers spiking past thresholds, precipitation accumulating to extreme levels. If the data doesn't show it, we need to know now.

Secondary goal: produce the pre-processed JSON/GeoJSON data files that the scroll frontend will consume, and scaffold the scroll infrastructure so a follow-up sprint can plug chapters in.

**Read `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/12-design-document.md` in the vault before doing anything.** It contains the full narrative architecture, chapter storyboard, data inventory, and technical architecture. Every agent needs to understand the story we're trying to tell.

Also read `CLAUDE.md` in the project root — it has the current project state and geographic asset details.

## Context

- **Project root:** `~/Documents/dev/cheias-pt/`
- **Vault:** `~/.vaults/root/2nd-Brain/Projects/cheias-pt/`
- **Existing assets:** `assets/basins.geojson` (11 catchment basins), `assets/districts.geojson` (18 districts with ipma_code)
- **Existing notebooks:** `notebooks/01-data-exploration.ipynb`, `notebooks/02-geographic-assets.ipynb`
- **Skills available:** `geo-storytelling`, `civic-map-ux`, `data-trust` (in Claude Code skills at `~/.claude/skills`)
- **Key data source:** Open-Meteo (zero auth, JSON API) for soil moisture, precipitation, river discharge
- **Event period:** Storms hit Jan 25 – Feb 12 2026. Antecedent buildup from Dec 1 2025.
- **Target rivers:** Tejo, Mondego, Sado, Douro, Lis (the five most affected)

## Spawn 4 teammates

### Agent 1: Soil Moisture Validation

**Owns:** `notebooks/03-soil-moisture-grid.ipynb` + `data/soil-moisture/`

Fetch historical soil moisture data from Open-Meteo for the Portugal flood event period. The hypothesis from the design document: weeks of persistent rain before the storms saturated the top 30cm of soil, creating the precondition for catastrophic flooding when Kristin/Leonardo/Marta arrived.

Specific tasks:
- Create a grid of ~80-100 points covering mainland Portugal (roughly 0.25° spacing within bbox [36.9, -9.6, 42.2, -6.1])
- Fetch from Open-Meteo Historical Weather API: `soil_moisture_0_to_7cm` and `soil_moisture_7_to_28cm` — daily values from Dec 1 2025 to Feb 12 2026
- For each grid point, calculate a normalized saturation index (0 = driest in period, 1 = wettest)
- Visualize the spatial pattern at 4 key dates: Dec 1 (baseline), Jan 15 (mid-buildup), Jan 28 (pre-Kristin), Feb 5 (between Leonardo and Marta)
- Validate: does the data actually show progressive saturation? Is the signal clear enough for a scrollytelling animation?
- Use basins.geojson to calculate per-basin average soil moisture timeseries — are the worst-hit basins (Tejo, Mondego, Sado) visibly more saturated?
- Output: `data/soil-moisture/grid-points.json` (point locations), `data/soil-moisture/timeseries.json` (daily values per point), `data/soil-moisture/basin-averages.json` (per basin daily averages)
- Include matplotlib/folium visualizations in the notebook to show the spatial + temporal pattern

Open-Meteo Historical Weather API docs: `https://open-meteo.com/en/docs/historical-weather-api` — use `&start_date=2025-12-01&end_date=2026-02-12` with `daily=soil_moisture_0_to_7cm,soil_moisture_7_to_28cm`.

**Success criterion:** A clear visual showing soil moisture increasing across Portugal from December through late January, with the hardest-hit basins showing the highest saturation before the storms.

### Agent 2: River Discharge Validation

**Owns:** `notebooks/04-discharge-timeseries.ipynb` + `data/discharge/`

Fetch GloFAS river discharge data via Open-Meteo Flood API for the major Portuguese rivers. The hypothesis: rivers were already running high from weeks of rain, and the storm cluster pushed them past extreme thresholds.

Specific tasks:
- Identify representative GloFAS grid points for each major river. Use the centroids or downstream points of the basins in `assets/basins.geojson`. Target rivers: Tejo, Mondego, Sado, Douro, Lis, Vouga, Guadiana. The Flood API takes lat/lon, so try multiple points per basin if needed to find ones with good data.
- Fetch from Open-Meteo Flood API (`https://flood-api.open-meteo.com/v1/flood`): `daily=river_discharge` — get both the event period (Jan 1 – Feb 12 2026) AND a reference period (same dates in 2024 or 2025, or use `river_discharge_mean` and `river_discharge_max` for climatology)
- For each river: plot the discharge timeseries showing the Jan–Feb 2026 spike against the climatological mean/max. Calculate the anomaly (how many times above average?)
- Validate: do Tejo, Mondego, Sado show exceptional discharge? Does the timing align with the storm dates (Kristin ~Jan 29, Leonardo ~Feb 5)?
- Determine a simple threshold for "exceptional" (e.g., > 2× historical mean, or > historical P90) that can serve as the visual encoding for Chapter 5
- Output: one JSON file per river (e.g., `data/discharge/tejo.json`) with daily discharge + anomaly ratio + threshold flag. Also `data/discharge/summary.json` with the GloFAS point coordinates and peak values for each river.

Open-Meteo Flood API docs: `https://open-meteo.com/en/docs/flood-api` — supports `past_days` parameter or `start_date/end_date`.

**Success criterion:** Discharge timeseries plots that clearly show the Tejo, Mondego, and Sado spiking to exceptional levels in late Jan / early Feb 2026, with visible storm-by-storm response.

### Agent 3: Precipitation Grid & Storm Validation

**Owns:** `notebooks/05-precipitation-grid.ipynb` + `data/precipitation/`

Fetch historical precipitation data from Open-Meteo to validate the storm accumulation narrative. The hypothesis: the Jan 25 – Feb 7 period deposited extreme rainfall across central/southern Portugal, with the storm cluster (Kristin, Leonardo, Marta) creating a sequence where each storm hit before the previous one's water had drained.

Specific tasks:
- Use the same ~80-100 point grid as Agent 1 (coordinate to use the same grid — or just use the same bbox and spacing)
- Fetch from Open-Meteo Historical Weather API: `precipitation_sum` daily, Dec 1 2025 – Feb 12 2026
- Calculate cumulative precipitation per point for the full period and for the storm window (Jan 25 – Feb 7)
- Visualize: (a) cumulative precip map for Jan 25 – Feb 7, (b) daily precipitation timeseries for 3–4 representative locations (Lisbon area, Leiria/Coimbra, Santarém/Tejo valley, Setúbal/Sado area)
- Validate: do the precipitation totals match the reports? (ESA reported >250mm in the Feb 1–7 window for large areas, >500mm in Grazalema Spain). Are the three storms (Kristin ~Jan 29, Leonardo ~Feb 5, Marta ~Feb 10) visible as distinct peaks?
- Calculate per-basin average precipitation using basins.geojson (same as Agent 1's approach)
- Output: `data/precipitation/daily-grid.json` (daily values per grid point), `data/precipitation/accumulation-jan25-feb07.json` (total per point for the storm window), `data/precipitation/basin-averages.json`

Also fetch `weathercode` or `weather_code` daily if available — this could help reconstruct the storm intensity timeline as a proxy for IPMA warnings (which have no historical API).

**Success criterion:** A precipitation accumulation map that clearly shows >200mm over central/southern Portugal in the storm window, with three distinct storm peaks visible in the daily timeseries.

### Agent 4: Scroll Scaffold & CEMS Investigation

**Owns:** `src/` directory (scroll infrastructure) + `notebooks/06-cems-investigation.ipynb`

Two tasks: (a) investigate what's downloadable from CEMS for the flood extent polygons, and (b) scaffold the scroll infrastructure that the other agents' data will plug into.

**Task A — CEMS Investigation:**
- Research the Copernicus EMS Rapid Mapping portal for activations EMSR861 (Storm Kristin, activated Jan 28) and EMSR864 (Storm Leonardo, activated Feb 3)
- Document: what products are available? Are delineation shapefiles downloadable without auth? What AOIs cover Portugal? What format are they in?
- Check `https://mapping.emergency.copernicus.eu/activations/EMSR861/` and `https://mapping.emergency.copernicus.eu/activations/EMSR864/`
- Also check the Copernicus Emergency Management Service open data: `https://emergency.copernicus.eu/` — is there a direct download or API?
- If shapefiles are freely downloadable, download them, convert to GeoJSON, and put in `data/flood-extent/`
- If not, document exactly what's needed (registration, request process) so Nelson can do it manually
- Output: `notebooks/06-cems-investigation.ipynb` with findings + `data/flood-extent/README.md` documenting the status

**Task B — Scroll Scaffold:**
- Read the geo-storytelling skill (in project skills or user skills) for the chapter config schema and scroll observer pattern
- Create the basic scroll infrastructure in `src/`:
  - `src/story-config.js` — chapter definitions following the design document's storyboard (Chapter 0–9). Use the exact camera positions, layer references, and text content from the design doc. Layers reference data files that may not exist yet — that's fine, the config is declarative.
  - `src/map-controller.js` — MapLibre initialization with CARTO Dark Matter basemap, camera transition functions (flyTo/easeTo wrapper with duration estimation)
  - `src/scroll-observer.js` — IntersectionObserver setup that reads chapter configs and triggers camera + layer transitions
  - `src/layer-manager.js` — functions to add/remove/set opacity on layers. Should handle GeoJSON sources, image overlays, and data-driven styling. Stub functions for layers that don't have data yet.
- Update `index.html` with the chapter HTML structure (text panels with data attributes matching story-config.js)
- Update `style.css` with the visual system from the design document: dark theme, glassmorphism panels, serif hero type, chapter spacing, responsive breakpoints
- The scaffold should WORK — loading the page should show the dark basemap, the title screen, and scrolling should trigger camera movements even if data layers aren't loaded yet. This is the skeleton that the data notebooks' output files will flesh out.

**Do NOT touch** `assets/basins.geojson` or `assets/districts.geojson` — these are validated and ready.

**Success criterion:** `index.html` loads in a browser showing the dark basemap with title screen, and scrolling triggers camera movements through the chapter sequence. Data layers are stubbed but the infrastructure is ready for them.

## Coordination Instructions

- **Agents 1, 2, 3** share the same geographic grid where possible. Agent 1 should define the grid first and share the point coordinates with Agents 2 and 3, or they should agree on a shared grid. Consistency matters — the frontend will need to render soil moisture, precipitation, and discharge for the same spatial units.
- **Agent 4** should message Agents 1–3 to understand the output JSON structure they're producing, so the layer-manager stubs match the actual data format.
- All agents should share notable findings: if Agent 2 finds that GloFAS data is patchy for the Lis river, Agent 4 needs to know so the scroll config can degrade gracefully. If Agent 3 finds the storm peaks don't align with the reported dates, everyone needs to discuss.
- **If any data source fails or shows unexpected results**, message the lead immediately. A core hypothesis not holding up is more important than completing the notebook.

## Output

The lead should synthesize findings into a brief validation report:

1. **Narrative validation:** Does the data support the story? For each chapter (soil → storms → rivers → consequences), does the data show what the design document claims? Flag any chapter where the data is weak or contradicts the narrative.
2. **Data readiness:** Which pre-processed files are ready in `data/`? Which still need work?
3. **Scroll status:** Does the scaffold work? What's plugged in, what's stubbed?
4. **Blockers:** What needs Nelson's manual intervention (CEMS downloads, consequence marker curation, photo sourcing)?
5. **Recommended next sprint:** What should the next agent team tackle?

Save the report to `notebooks/VALIDATION-REPORT.md` and also to the vault at `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/13-data-validation-report.md`.
