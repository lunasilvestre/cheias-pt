# Sprint 02 Report: Wire Data → Scroll

**Date:** 2026-02-16
**Duration:** ~25 minutes (4-agent team)
**Status:** Complete

## What Was Done

Converted the temporal backbone data (Parquet) and CEMS flood extent (PMTiles) into browser-consumable formats and wired them to the 10-chapter scroll narrative. The page now shows real data at every chapter.

### Task 1: Data Pipeline (Parquet → Frontend JSON)

Wrote `scripts/parquet_to_frontend_json.py` converting 6 Parquet files into 8 JSON files in `data/frontend/`:

| File | Size | Content |
|------|------|---------|
| soil-moisture-frames.json | 745 KB | 77 frames × 256 pts, sm_rootzone normalized 0–1 |
| precip-frames.json | 963 KB | 77 frames × 342 pts, daily precipitation |
| precip-storm-totals.json | 14 KB | 342 pts, Jan 25–Feb 7 accumulation |
| discharge-timeseries.json | 52 KB | 11 stations × 77 days |
| precondition-frames.json | 1,149 KB | 77 frames × 256 pts, precondition index |
| precondition-peak.json | 15 KB | Peak date (Feb 5) snapshot |
| precondition-basins.json | 1 KB | Per-basin averages (peak + pre-storm) |
| ivt-peak-storm.json | 38 KB | IVT moisture flux at storm peak |
| **Total** | **2,977 KB** | Under 5 MB target |

### Task 2: Chapters 3, 4, 5 (Data Chapters)

Created 3 new modules:
- `src/data-loader.js` — fetch + cache for all JSON files
- `src/temporal-player.js` — scroll-to-frame mapper (0–1 progress → frame index)
- `src/chapter-wiring.js` — chapter enter/leave logic, GeoJSON construction

Wired 4 layers in `layer-manager.js`:
- **soil-moisture-animation** (Ch3): 256 circles, scroll-controlled 77-frame animation with date label
- **precipitation-accumulation** (Ch4): 342 graduated circles (size + color by mm)
- **glofas-discharge** (Ch5): 11 station markers, sized by peak discharge ratio
- **soil-moisture-snapshot** (Ch5 background): frozen at Jan 28

Added `onChapterProgress()` / `offChapterProgress()` to `scroll-observer.js` for continuous scroll tracking with rAF throttling.

### Task 3: Chapters 1, 6, 7, 8 (Flood + Precondition)

PMTiles integration:
- Added PMTiles CDN to `index.html`
- Registered protocol in `map-controller.js`
- Discovered source-layer name: `flood_extent`

Wired 3 layers:
- **sentinel1-flood-extent** (Ch1): PMTiles fill layer, red over terrain
- **flood-extent-polygons** (Ch6): Reuses same PMTiles source via `sourceRef`
- **consequence-markers** (Ch6): 42 events, categorical circle colors by type, Portuguese popups on click

Precondition basin coloring:
- **basins-fill** (Ch7): colored by peak precondition index (Feb 5) — Minho-Lima 1.0, Mondego 0.91
- **basins-fill** (Ch8): colored by pre-storm precondition (Jan 25) — mostly blue, early warning signal

### Task 4: Visual Polish

- Dynamic legend system (floating glassmorphism panel, updates per chapter)
- Chapter 2 fallback (inline SVG moisture arrow graphic)
- Exploration mode layer toggle panel (6 toggleable layers, glassmorphism styling)
- OG meta tags (og:title, og:description, og:image, twitter:card)
- OG screenshot at `assets/og-image.png` (1200×630)
- Responsive verification at 375px
- CLAUDE.md updated with new file structure
- Exploration mode exit fix + NavigationControl lifecycle

## Architecture

```
src/
  main.js              # Orchestration: init, chapter callbacks, legend, CTA
  story-config.js      # Declarative chapter defs (camera, layers, legends)
  map-controller.js    # MapLibre + PMTiles protocol + camera transitions
  scroll-observer.js   # IntersectionObserver + continuous scroll progress
  layer-manager.js     # 15 layers (4 stubs, 11 wired), PMTiles, popups, precondition
  chapter-wiring.js    # Data-driven logic for Ch3/4/5 (temporal + GeoJSON)
  data-loader.js       # Fetch + cache frontend JSON
  temporal-player.js   # Frame animation mapped to scroll progress
  exploration-mode.js  # Free navigation + layer toggle panel
  utils.js             # Formatting helpers
```

## What's Still Stubbed (v1)

4 layers remain as stubs — all are P2 priority from the design doc:

| Layer | Chapter | Why |
|-------|---------|-----|
| `sst-anomaly` | Ch2 | SST raster processing too complex for v0; SVG fallback in place |
| `atmospheric-river-track` | Ch2 | IVT data available but visualization deferred |
| `ipma-warnings-timeline` | Ch4 | No historical warning API; manual reconstruction needed |
| `satellite-after` | Ch6 | Sentinel-2 true-color imagery not yet acquired |

## Visual Quality Assessment

**Strong:**
- Soil moisture animation (Ch3) is the highlight — scroll-driven, 77 frames, smooth
- Flood extent polygons (Ch1, Ch6) are dramatic on dark basemap
- Consequence marker popups with Portuguese text feel polished
- Basin precondition coloring (Ch7 peak vs Ch8 pre-storm) tells the predictive story well
- Dynamic legends update cleanly per chapter

**Needs Iteration:**
- GloFAS discharge ratios (1.0–1.6) are climatological, not storm amplification — circles are similar sizes. Consider using absolute discharge values for sizing instead.
- Salvaterra temporal animation (3-date flood growth) not yet implemented in Ch6a — left as enhancement
- Chapter 2 uses SVG placeholder instead of real atmospheric data

## Recommended Next Steps

1. **Salvaterra temporal animation** — show flood growth from 31K→42K→49K ha across 3 dates in Ch6a
2. **Discharge visualization improvement** — use absolute discharge values or within-storm ratios for better visual differentiation
3. **Satellite imagery** — acquire Sentinel-2 true-color composites for Ch6 before/after comparison
4. **IPMA warning reconstruction** — manually curate warning timeline for Ch4
5. **Performance testing** — load test on actual mobile devices (not just viewport simulation)
6. **Static deploy** — deploy to cheias.pt (GitHub Pages or Vercel)
