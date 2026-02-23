# cheias.pt — Sprint 02: Wire Data → Scroll

## Mission

Connect the validated temporal backbone data and CEMS flood extent polygons to the scroll scaffold. When this sprint is done, scrolling through the narrative should show real data: soil moisture filling, precipitation falling, rivers spiking, and flood polygons appearing. The page should be publishable.

**Read `CLAUDE.md` and `discovery/12-design-document.md` in the vault before doing anything.** They contain the full narrative architecture, visual design system, and technical constraints.

## Current State

**What exists and works:**
- Scroll scaffold: `index.html` + 7 JS modules in `src/` — 10 chapters with camera transitions, glassmorphism panels, progress bar. Scrolling triggers `flyTo`/`easeTo` moves between chapters.
- `src/layer-manager.js` has 11 stubbed layers (marked `stub: true`) that log "data not yet available". These need to be replaced with real layer definitions.
- `src/story-config.js` declares each chapter's camera position, layer list, legend, and text. The layer IDs are already correct — the layer-manager just needs to implement them.
- Geographic assets: `assets/basins.geojson` (11 basins) and `assets/districts.geojson` (18 districts) — ready, validated.

**Temporal backbone (all in Parquet, need conversion to frontend JSON):**

| File | Records | Grid | Fields |
|------|---------|------|--------|
| `data/temporal/moisture/soil_moisture.parquet` | 26,334 | 342 pts × 77 days | date, lat, lon, sm_0_7, sm_7_28, sm_28_100, sm_rootzone |
| `data/temporal/precipitation/precipitation.parquet` | 26,334 | 342 pts × 77 days | date, lat, lon, precip_mm, rain_mm, precip_3d/7d/14d/30d |
| `data/temporal/discharge/discharge.parquet` | 847 | 11 stations × 77 days | date, name, basin, lat, lon, discharge, discharge_median/max/min, discharge_ratio |
| `data/temporal/precondition/precondition.parquet` | 26,334 | 342 pts × 77 days | date, lat, lon, remaining_capacity_mm, ratio_3d, antecedent_score, precondition_index, risk_class |
| `data/temporal/ivt/ivt.parquet` | 115,115 | 1,495 pts × 77 days | date, lat, lon, ivt |
| `data/temporal/sst/sst_anomaly.nc` | NetCDF | 160×260 × 62 days | SST anomaly (°C), North Atlantic |

**CEMS flood extent (already web-optimized):**

| File | Contents | Format |
|------|----------|--------|
| `data/flood-extent/combined.pmtiles` | All 5,052 flood polygons (135,925 ha) | PMTiles, z4-z14 |
| `data/flood-extent/emsr861.pmtiles` | Storm Kristin (Coimbra, 7,723 ha) | PMTiles |
| `data/flood-extent/emsr864.pmtiles` | Storm Leonardo/Marta (128,202 ha) | PMTiles |
| `data/flood-extent/salvaterra_temporal.pmtiles` | 3-date Salvaterra animation (31K→42K→49K ha) | PMTiles, z6-z14 |
| `data/flood-extent/salvaterra_2026-02-0[6-8].geojson` | Per-date GeoJSON snapshots | GeoJSON |

Each PMTiles feature has properties: `activation`, `aoi`, `locality`, `source_date`, `sensor`, `product_type`, `storm`, `area_ha`.

## Technical Constraints

- **Vanilla JS + ES modules** — no build tools (no Vite, webpack, Rollup). Import via `<script type="module">` and CDN.
- **No backend** — everything is `fetch()` against static files served from the project root.
- **MapLibre GL JS 4.7.1** — already loaded via CDN in `index.html`.
- **PMTiles** — need to add the PMTiles JS protocol library via CDN. Use `pmtiles` npm package via CDN (`https://unpkg.com/pmtiles@4.1.0/dist/pmtiles.js` or similar). Register the protocol before adding PMTiles sources.
- **Max 3 visible layers per chapter** (design doc rule) — the layer-manager handles this via opacity transitions.
- **Mobile performance** — the scroll + map + glassmorphism is already GPU-intensive. Keep layer rendering efficient. Prefer circle layers over heatmaps for the point grids. Use PMTiles (not raw GeoJSON) for the flood extent polygons.
- **Dark theme** — all data visualizations must work against the CARTO Dark Matter basemap (#0a212e).

## Spawn 4 teammates:

### Teammate 1: Data Pipeline — Parquet → Frontend JSON

Convert the temporal backbone Parquet files into frontend-consumable JSON that the browser can `fetch()` and render with MapLibre. All outputs go in `data/frontend/`.

**Soil moisture** (Chapter 3 animation):
- Read `data/temporal/moisture/soil_moisture.parquet`
- Output `data/frontend/soil-moisture-frames.json` — an array of 77 daily frames, each containing `{date, points: [{lat, lon, value}]}` where `value` is `sm_rootzone` normalized to 0–1 (divide by porosity 0.42, cap at 1.0)
- This should be a single JSON file the frontend loads once and indexes by frame number
- Keep file size manageable: round lat/lon to 2 decimals, value to 3 decimals

**Precipitation** (Chapter 4):
- Read `data/temporal/precipitation/precipitation.parquet`
- Output `data/frontend/precip-storm-totals.json` — per-point accumulated precipitation for the storm window (Jan 25 – Feb 7), as `{points: [{lat, lon, total_mm}]}`
- Also output `data/frontend/precip-frames.json` — daily frames (same structure as soil moisture) for optional animation, using `precip_mm` field

**Discharge** (Chapter 5):
- Read `data/temporal/discharge/discharge.parquet`
- Output `data/frontend/discharge-timeseries.json` — per-station timeseries: `{stations: [{name, basin, lat, lon, timeseries: [{date, discharge, discharge_ratio}]}]}`
- This is small enough to be one file

**Precondition index** (Chapters 7-8):
- Read `data/temporal/precondition/precondition.parquet`
- Output `data/frontend/precondition-frames.json` — daily frames with `{date, points: [{lat, lon, index, risk_class}]}`
- Also output `data/frontend/precondition-peak.json` — single snapshot at peak risk (the date with highest fraction of orange/red points), for the static view in Chapter 8

**IVT** (Chapter 2, lower priority):
- Read `data/temporal/ivt/ivt.parquet`
- Output `data/frontend/ivt-peak-storm.json` — a single snapshot of IVT values during Kristin's peak (around Jan 28-29), showing the moisture corridor from Atlantic to Iberia. Use the wider 1,495-point grid. Just one frame, as this chapter is context-setting.

Write a Python script `scripts/parquet_to_frontend_json.py` that does all conversions. It should:
- Activate `.venv` or use the project virtual environment
- Read all Parquet files
- Write all JSON outputs
- Print a summary table of output files and sizes
- Be idempotent (safe to re-run)

**Success criterion:** `data/frontend/` contains all JSON files, each loadable by the browser. Total size under 5 MB for all JSON combined.

**Message teammates 2 and 3** with the exact JSON structure you've output so they know what to `fetch()`.

---

### Teammate 2: Wire Chapters 3, 4, 5 — The Data Chapters

Replace the stubbed layer definitions in `src/layer-manager.js` for the three core data chapters and build the scroll-controlled temporal animation system.

**Chapter 3 — Soil Moisture Animation (`soil-moisture-animation`):**
- Load `data/frontend/soil-moisture-frames.json` on page load (or lazy-load when Chapter 2 enters view)
- Render as a **MapLibre circle layer** — 342 circles positioned at grid points
- Color ramp: dry (#f7f7f7 / white) → saturated (#2166ac / deep blue). Use `circle-color` with interpolation on the value property.
- Circle radius: 8px at zoom 7 (scale with zoom using `circle-radius` interpolation)
- **Scroll-controlled animation:** As the user scrolls through Chapter 3 (which has ~100vh of scroll height), advance through the 77 daily frames. Map scroll position within the chapter to frame index. Use `map.getSource('source-soil-moisture-animation').setData()` to update the GeoJSON on each frame change.
- Build a date label overlay that shows the current date (e.g., "1 Dez 2025" → "15 Fev 2026") as the animation progresses. Position it in the chapter card area or as a floating label on the map.

**Chapter 4 — Precipitation Accumulation (`precipitation-accumulation`):**
- Load `data/frontend/precip-storm-totals.json`
- Render as **graduated circles** — size proportional to total_mm, color from the legend in story-config (yellow < 100mm, orange 100-250mm, red > 250mm)
- This can be a static layer (no animation needed for v0) — just the storm-window totals
- Alternatively, if time allows, animate day-by-day accumulation using `precip-frames.json`

**Chapter 5 — Discharge Visualization (`glofas-discharge`):**
- Load `data/frontend/discharge-timeseries.json`
- Render 11 station markers on the map as **circles with proportional radius** based on current discharge_ratio
- Color: blue (#2166ac) for normal (ratio < 2), orange (#F7991F) for elevated (2-5), red (#e74c3c) for exceptional (>5)
- On click/hover, show a small popup or tooltip with station name, basin, peak discharge, and peak date
- For Chapter 5, show the peak-storm values (highlight the worst moment)

**Soil moisture snapshot layer (`soil-moisture-snapshot`):**
- Used in Chapter 5 as background context (opacity 0.3)
- Render the same soil moisture circle grid but frozen at a single date (Jan 28, pre-Kristin)
- Can reuse the same source with a fixed frame

**Temporal player system:**
- Create `src/temporal-player.js` — a module that manages scroll-to-frame mapping for animated chapters
- API: `setFrames(frames)`, `setProgress(0-1)` → updates the current frame, `getCurrentDate()` → returns the displayed date
- The scroll-observer should call `setProgress()` based on how far through a chapter section the user has scrolled
- This is the shared infrastructure for Chapter 3 (soil moisture) and potentially Chapter 4 (precipitation)

**Important integration details:**
- In `layer-manager.js`, change each wired layer from `{ stub: true }` to a real layer definition
- The `ensureLayer()` function needs to handle the new source types (GeoJSON data from fetched JSON, not static files)
- Add a data loading module (`src/data-loader.js`) that fetches all JSON files and caches them. Other modules import from this.
- Don't break the existing camera transitions, progress bar, or glassmorphism panels

**Success criterion:** Scrolling through Chapters 3-5 shows real data from the temporal backbone. Soil moisture animates. Precipitation renders as graduated circles. Discharge stations show proportional markers. No console errors.

---

### Teammate 3: Wire Chapters 1, 6, 7, 8 — Flood Extent + Precondition

Wire the CEMS flood extent PMTiles and the precondition index into the remaining data-dependent chapters.

**PMTiles Setup:**
- Add the PMTiles library to `index.html` via CDN: `<script src="https://unpkg.com/pmtiles@4.1.0/dist/pmtiles.js"></script>`
- Register the PMTiles protocol in `src/map-controller.js` (or a new `src/pmtiles-setup.js`) BEFORE the map loads:
  ```js
  const protocol = new pmtiles.Protocol();
  maplibregl.addProtocol("pmtiles", protocol.tile);
  ```
- This must happen before any PMTiles source is added to the map

**Chapter 1 — Flood Extent Hook (`sentinel1-flood-extent`):**
- Load `data/flood-extent/combined.pmtiles` as a vector source
- Render as a fill layer with color #e74c3c at opacity 0.8
- This gives the "red over terrain" visual anchor described in the design doc
- Layer name in the PMTiles is whatever tippecanoe assigned — inspect the PMTiles to find it (likely the default layer name)

**Chapter 6 — Human Cost (`flood-extent-polygons` + Salvaterra animation):**
- Use the same combined.pmtiles source for the base flood extent
- For the Salvaterra temporal sequence (the 3-date growth animation):
  - Load `data/flood-extent/salvaterra_temporal.pmtiles`
  - Filter by `source_date` property to show progressive inundation as user scrolls through Chapter 6a (Alcácer do Sal substep)
  - Or use the three individual GeoJSON files (`salvaterra_2026-02-06.geojson`, etc.) and swap them as the user scrolls
  - The visual: flood area growing from 31K ha → 42K ha → 49K ha, a devastating expansion
- For the Coimbra substep (6b): the same combined.pmtiles filtered to `activation === 'EMSR861'` (Coimbra AOI)
- Consequence markers (`consequence-markers`): **already curated** at `data/consequences/events.geojson` — 42 geocoded events (10 deaths, 7 evacuations, 9 infrastructure, 4 river records, 2 levee breaches, 2 landslides, etc.). Each feature has `type`, `date`, `storm`, `title_pt`, `description_pt`, `image_url`, `severity`, `chapter`, `municipality`, and `river_basin`. Wire as a circle/symbol layer with categorical styling by event type (see design doc color scheme: death=#e74c3c, evacuation=#F7991F, infrastructure=#8e44ad, landslide=#795548). On click, show a popup with the Portuguese title, description, date, and source link. The `chapter` property indicates which scroll chapter each marker should appear in (mostly 6, some in 1, 4, 7, 8).

**Chapter 7 — Causal Chain (composite view):**
- Load `data/frontend/precondition-peak.json` (from Teammate 1)
- Color the basins by peak precondition index: use `basins-fill` layer with data-driven `fill-color` mapping each basin to its peak risk level
- To do this: compute per-basin average precondition index from the point grid (spatial average of all grid points within each basin). This could be done in the data pipeline (Teammate 1) or at runtime by checking which points fall within basin bounding boxes.
- Overlay flood-extent-polygons at reduced opacity (0.5) — reuse the PMTiles source
- This is the "everything at once" chapter — careful opacity management

**Chapter 8 — What Data Knew:**
- Use basins-fill colored by precondition index at a pre-storm date (e.g., Jan 25, before Kristin)
- This shows that the index was already elevated BEFORE the first storm — the predictive power
- Load `data/frontend/precondition-frames.json`, pick the Jan 25 frame, compute per-basin averages
- Simple: basins go from blue (low risk) through orange to red (high risk) using the design doc color ramp:
  - 0.0-0.2: #2166ac, 0.2-0.4: #67a9cf, 0.4-0.6: #f7f7f7, 0.6-0.8: #ef8a62, 0.8-1.0: #b2182b

**Success criterion:** Chapter 1 shows red flood extent polygons over Portugal. Chapter 6 shows flood polygons zooming to specific locations, with Salvaterra temporal growth visible. Chapter 7 shows colored basins + flood polygons. Chapter 8 shows pre-storm risk coloring on basins.

---

### Teammate 4: Visual Polish + Performance + Responsive

Once Teammates 2 and 3 have wired the data layers, do a complete visual and performance pass.

**Legend system:**
- `story-config.js` already has legend items per chapter, but they're currently just rendered as colored swatches in the HTML
- Make the legends dynamic — update them when a chapter enters view. Each chapter should show only its own legend items.
- For animated chapters (soil moisture), add the current date to the legend area

**Chapter 2 fallback:**
- SST and IVT are lower priority for v0. If Teammate 1 produced `ivt-peak-storm.json`, render it as a low-opacity point grid showing moisture flux values across the Atlantic.
- If it's too complex, use a **static image overlay** approach: create a simple color-coded narrative card explaining the Atlantic moisture source, with text and a stylized arrow graphic (CSS/SVG) rather than a data layer. The camera still zooms to Atlantic scale.
- Mark the SST and atmospheric-river-track layers as "v1" and leave clean stubs

**Explore mode (Chapter 9):**
- `src/exploration-mode.js` already exists — verify it works with all the new layers
- In exploration mode, add a simple **layer toggle panel** that lets users show/hide: flood extent, soil moisture (peak), precipitation (totals), discharge stations, precondition index, basin outlines
- Use the glassmorphism panel style from the existing chapter cards

**Performance:**
- Test that scrolling through all 10 chapters is smooth on a simulated mobile viewport (390×844)
- The soil moisture animation (342 circles × 77 frames) is the heaviest thing — if it jitters, reduce to every-other-day frames (39 frames) or reduce circle count by filtering to every-other grid point on mobile
- PMTiles should be efficient — if the combined.pmtiles causes slow rendering at zoom 7 (national view), add `minzoom`/`maxzoom` to the layer definition
- Ensure no memory leaks from repeated `setData()` calls in the temporal animation

**Responsive check:**
- Verify all data layers render correctly at 375px width
- Chapter text cards should not overlap data visualizations — if circles or polygons are behind the card, that's fine (by design), but labels/tooltips should not be clipped
- Touch scroll through the entire narrative — no stuck states, no jank

**OG image:**
- Take a screenshot of the Chapter 1 view (flood extent over Portugal, dark basemap, hero text) at 1200×630px resolution
- Save as `assets/og-image.png`
- Verify the `<meta property="og:image">` tag in `index.html` points to it

**Cleanup:**
- Remove any old v2/v3 files if they still exist
- Ensure the data directory structure in CLAUDE.md matches reality
- Update CLAUDE.md with the new data/frontend/ directory and any new src/ modules

**Success criterion:** The full narrative scrolls smoothly from title screen to exploration mode. All data chapters show real data. Legends update per chapter. Mobile works. An outsider visiting cheias.pt for the first time would understand the story and be impressed by the data visualization.

---

## Coordination Instructions

- **Teammate 1 runs first** — Teammates 2 and 3 depend on the JSON files. Teammate 1 should message them with the exact output file paths and JSON structure as soon as conversion is done.
- **Teammates 2 and 3 can start in parallel** on the PMTiles layers and layer-manager refactoring while waiting for Teammate 1's JSON files. Teammate 3's PMTiles work (flood extent) is independent of the Parquet conversion.
- **Teammate 4 runs last** — needs all data layers wired before the polish pass. But can start on the legend system, Chapter 2 fallback, and responsive checks early.
- **File ownership:** Teammate 1 owns `scripts/` and `data/frontend/`. Teammate 2 owns `src/temporal-player.js` and `src/data-loader.js` (new files). Teammate 3 owns PMTiles integration. Both 2 and 3 edit `src/layer-manager.js` — **coordinate which layers each one handles to avoid conflicts.** Teammate 2: soil-moisture-animation, precipitation-accumulation, glofas-discharge, soil-moisture-snapshot. Teammate 3: sentinel1-flood-extent, flood-extent-polygons, consequence-markers, basins-fill (precondition coloring). Teammate 4 edits `style.css`, `index.html`, exploration-mode, and does the final cleanup.
- If anyone discovers that the data doesn't render well (wrong scale, bad colors, circles too small), message the team immediately. Iterate on the visual encoding rather than shipping something ugly.

## Output

The lead should verify the final state by:
1. Running `bash scripts/serve.sh` and scrolling through the entire narrative
2. Checking that each chapter shows its expected data visualization
3. Verifying no console errors (all data layers should be wired — no remaining stubs)
4. Testing at mobile viewport width
5. Writing a brief sprint report to `notebooks/SPRINT-02-REPORT.md` documenting: what's wired, what's still stubbed, visual quality assessment, and recommended next steps
