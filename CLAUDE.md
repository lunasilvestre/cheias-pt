# cheias.pt — The Winter That Broke the Rivers

## Environment
Always use the project virtual environment at `.venv/`. Activate with `source .venv/bin/activate` before any pip install or python3 command. NEVER use --break-system-packages.

## Mission

Build a **scroll-driven geo-narrative** about Portugal's January–February 2026 flood crisis. Not a dashboard. Not a monitoring tool. A story told through maps, satellite imagery, and hydro-meteorological data — about what happened, why it happened, and what it means.

This is a portfolio piece targeting Development Seed (Lisbon + DC) and a public service artifact for Portuguese citizens, journalists, and local officials trying to understand the crisis.

**Current context (Feb 2026):** Portugal under state of emergency. Storm cluster (Kristin → Leonardo → Marta) killed 11+, displaced thousands, collapsed the A1 motorway, burst the Mondego levee, triggered €2.5B aid package across 69 municipalities. Tejo at highest since 1997. Sado at levels unseen since 1989. CEMS rapid mapping activated (EMSR861, EMSR864).

## Current Phase: Scrollytelling (v0)

Nine-chapter scroll narrative. Static deploy — all data pre-processed, no runtime API calls, no backend.

### The Story Arc

| Chapter | Title | Scale | Key Data |
|---------|-------|-------|----------|
| 0 | Title screen | Atlantic | Dark basemap, hero title |
| 1 | The Hook (Act 1) | Portugal | Sentinel-1 flood extent, Feb 7 |
| 2 | The Atlantic Engine | Continental | SST anomalies, storm tracks |
| 3 | The Sponge Fills | National → basins | Soil moisture animation, Dec–Jan |
| 4 | Three Storms | National → basins | Precipitation accumulation, IPMA warnings |
| 5 | The Rivers Rise | Basin level | GloFAS discharge, precondition index |
| 6 | The Human Cost | Local (multi-stop) | Flood extent, consequence markers, photos |
| 7 | The Causal Chain (Climax) | National | All layers overlaid |
| 8 | What the Data Knew (Act 3) | National | Precondition index methodology |
| 9 | Explore | User's location | Free navigation, all layers toggleable |

### Technical Stack

- **MapLibre GL JS** — map rendering, camera transitions
- **Vanilla JS + ES Modules** — no build tools
- **CARTO Dark Matter** basemap — free, no auth
- **Intersection Observer API** — scroll-triggered chapter transitions
- **Pre-processed JSON/GeoJSON** — all data static, prepared by notebooks

### Design Principles

1. **Everything is a where and a when.** If it doesn't have coordinates and a timestamp, it doesn't belong on the primary interface.
2. **Catchment basins are the spatial unit**, not districts. Districts are context outlines only.
3. **The precondition thesis drives the narrative:** saturated soil + incoming rain + rising rivers = catastrophe. Each chapter reveals one link in the causal chain.
4. **Dark-first visual system** with glassmorphism panels, serif hero type, progressive layer reveals. Max 3 visible layers per chapter.
5. **Elena's emotional engagement sequence:** Delight → Curiosity → Exploration → Digestion.

## Primary Specification

**The design document is the source of truth:**
`~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/12-design-document.md`

It contains: full chapter storyboard with camera positions and layer specs, data inventory (what's available vs. what needs acquisition), visual design system, technical architecture, and scope boundaries.

**Supporting research (read if you need context, don't duplicate):**

| What | Where |
|------|-------|
| User personas & information hierarchy | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/11-elena-interview-findings.md` |
| Vizzuality methodology | `~/.vaults/root/2nd-Brain/Projects/vizzuality-methodology` |
| Flood dynamics & data sources | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/07-flood-dynamics-prediction.md` |
| Data source tier list | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/06-synthesis.md` |
| Sprint prompt (current) | `prompts/sprint-02-wire-data.md` |

**Skills (in Claude Code skills at `~/.claude/skills`):**

| Skill | Use for |
|-------|---------|
| `geo-storytelling` | Chapter config schema, camera transitions, narrative structures, scroll observer pattern |
| `civic-map-ux` | Progressive disclosure, layout, component patterns, anti-pattern checklist |
| `data-trust` | Attribution, methodology page, uncertainty patterns, institutional framing |

## Geographic Assets (READY — do not regenerate)

Both files are validated and ready in `assets/`:

| Asset | Features | Size | Key Properties |
|-------|----------|------|----------------|
| `assets/districts.geojson` | 18 | 27 KB | `district`, `ipma_code`, `idDistrito` |
| `assets/basins.geojson` | 11 | 64 KB | `river`, `name_pt`, `type`, `transboundary` |

**Critical notes:**
- District `ipma_code` maps to IPMA API's `idAreaAviso` — used for warning joins
- Basin boundaries don't align with districts — use both independently
- Districts are CONTEXT ONLY (thin outline, no fill) — never the primary data unit
- Notebook `02-geographic-assets.ipynb` has full analysis

## Data Pipeline

All raw data has been acquired and validated. Two data tiers:

### Temporal Backbone (Parquet — source of truth, needs conversion to frontend JSON)

```
data/temporal/
  moisture/soil_moisture.parquet       # 342 pts × 77 days, sm_rootzone + layers
  precipitation/precipitation.parquet  # 342 pts × 77 days, daily + rolling accum
  discharge/discharge.parquet          # 11 stations × 77 days, discharge + ratio
  precondition/precondition.parquet    # 342 pts × 77 days, index + risk_class
  ivt/ivt.parquet                      # 1,495 pts × 77 days, moisture flux proxy
  sst/sst_anomaly.nc + daily/*.tif     # 62 daily COGs, North Atlantic SST anomaly
```

Conversion scripts in `scripts/` (fetch_*.py, compute_precondition.py, validate_temporal.py).

**Sprint 02 converted these to `data/frontend/*.json` for browser consumption:**

```
data/frontend/
  soil-moisture-frames.json     # 342 pts × 77 days, circle layer animation
  precip-frames.json            # 342 pts × 77 days, precipitation animation
  precip-storm-totals.json      # Per-point storm total accumulation
  discharge-timeseries.json     # 11 stations × 77 days, discharge curves
  precondition-frames.json      # 342 pts × 77 days, precondition index
  precondition-peak.json        # Peak precondition per basin
  precondition-basins.json      # Basin-level precondition summaries
  ivt-peak-storm.json           # IVT moisture flux at storm peak
```

### CEMS Flood Extent (GeoJSON + PMTiles — web-ready)

```
data/flood-extent/
  combined.geojson          # 5,052 polygons, 135,925 ha total
  combined.pmtiles           # Web-optimized, z4-z14
  emsr861.geojson/pmtiles    # Storm Kristin (Coimbra, 7,723 ha)
  emsr864.geojson/pmtiles    # Storm Leonardo/Marta (128,202 ha)
  salvaterra_temporal.pmtiles # 3-date animation (31K→42K→49K ha)
  salvaterra_2026-02-0[6-8].geojson  # Per-date snapshots
  combined.parquet / emsr861.parquet / emsr864.parquet  # For notebooks
  README.md                  # Full documentation, per-AOI breakdown
```

PMTiles features have: `activation`, `aoi`, `locality`, `source_date`, `sensor`, `product_type`, `storm`, `area_ha`.

### Consequence Markers (GeoJSON — ready)

```
data/consequences/
  events.geojson    # 42 geocoded events, bilingual (PT/EN)
```

42 events: 10 deaths, 7 evacuations, 9 infrastructure, 4 river records, 2 levee breaches, 2 landslides, 2 power cuts, 2 rescues, 2 closures, 1 military, 1 political. Each has `type`, `date`, `storm`, `title_pt`, `description_pt`, `image_url`, `severity`, `chapter`, `municipality`, `river_basin`, `source_url`.

### Sprint 01 Validation Data (JSON — from initial notebooks, may be superseded by temporal backbone)

```
data/
  soil-moisture/     # grid-points.json, timeseries.json, basin-averages.json
  discharge/         # per-river JSON + summary.json
  precipitation/     # daily-grid.json, accumulation-jan25-feb07.json, basin-averages.json
  static-images/     # (empty — not yet acquired)
```

## Frontend Structure

```
src/
  main.js                 # Orchestration: init map, wire chapters, CTA buttons
  story-config.js         # Declarative chapter definitions (camera, layers, text, legends)
  map-controller.js       # MapLibre init + camera transitions + interaction toggle
  scroll-observer.js      # IntersectionObserver → chapter triggers + scroll progress
  layer-manager.js        # Layer add/remove/opacity per chapter, PMTiles, consequences
  chapter-wiring.js       # Data-driven chapter logic (soil moisture anim, precip, discharge)
  data-loader.js          # Fetch and cache frontend JSON data files
  temporal-player.js      # Timeline scrubber for animated chapters
  exploration-mode.js     # Free navigation + layer toggle panel after story ends
  utils.js                # Geolocation, URL state, helpers
```

## What NOT To Build

- ❌ No real-time data feeds or monitoring mode (future phase)
- ❌ No AI chat / GeoAgent
- ❌ No FastAPI backend
- ❌ No user accounts, notifications, saved locations
- ❌ No build tools (Vite, webpack) — vanilla JS with ES modules + CDN
- ❌ No district choropleth (anti-pattern — see design doc section 9)
- ❌ No news scraping or automated event detection

## Previous Versions

The project evolved through three phases. Current files are kept for reference:

| File | What it was | Status |
|------|-------------|--------|
| `CLAUDE-v1.md` | Initial exploration spec | Superseded |
| `CLAUDE-v2.md` | Dashboard refactor (Mode 1 + 2) | Superseded |
| `CLAUDE-v3.md` | Dashboard implementation spec | Superseded by scrollytelling pivot |
| `V2-REVIEW.md` | QA review of v2 dashboard | Historical reference |
