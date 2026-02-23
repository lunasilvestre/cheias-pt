# Sprint 01 — Data Validation Report

**Date:** 2026-02-15
**Sprint:** Data Validation & Scroll Scaffold
**Team:** 4 agents (soil-moisture, discharge, precipitation, scroll-scaffold)

---

## 1. Narrative Validation

**Verdict: THE DATA STRONGLY SUPPORTS THE STORY.**

The design document's causal chain — saturated soil + extreme rain + overwhelmed rivers = catastrophe — is validated by all three data sources. Every chapter has data behind it.

### Chapter 3 (The Sponge Fills) — VALIDATED

Soil moisture data from Open-Meteo (ERA5-Land) shows a dramatic, progressive saturation:

| Date | National Avg Saturation (0-1) | Narrative Moment |
|------|-------------------------------|------------------|
| Dec 1 | 0.13 | Baseline — relatively dry |
| Jan 15 | 0.58 | Mid-buildup — visibly wetting |
| Jan 28 | 0.90 | Pre-Kristin — ground nearly full |
| Feb 5 | 0.95 | Between storms — maxed out |

Dynamic range of 0.83 is excellent for scroll animation. The visual transformation from dry (yellow) to saturated (deep blue/red) across 8 weeks is unmistakable. All crisis basins (Tejo 0.92, Mondego 0.94, Sado 0.89, Douro 0.96) show the pattern.

**Signal strength: 5/5** — this is the strongest chapter data-wise.

### Chapter 4 (Three Storms) — VALIDATED

Precipitation data confirms extreme totals and three distinct storm peaks:

- **Storm window (Jan 25 – Feb 7):** Mean 230mm across 330 grid points, max 567mm
- **54% of Portugal** received >200mm; **33%** received >250mm
- Three peaks clearly visible: Kristin (Jan 27-28), Leonardo (Feb 5), Marta (Feb 10-11)
- Basin ranking: Minho-Lima (495mm) > Vouga (390mm) > Mondego (374mm) > Lis (294mm) > Douro (286mm) > Tejo (282mm)
- Full period (Dec 1 – Feb 12): mean 552mm, max 1,357mm

The NW-to-SE gradient is very clear — Atlantic-facing basins hammered, Algarve much less. This spatial pattern will make a compelling map in the scrollytelling.

**Signal strength: 5/5** — exceeds reported values, three storms unmistakable.

### Chapter 5 (The Rivers Rise) — VALIDATED

GloFAS discharge data shows massive storm amplification across all 8 rivers:

| River | Storm Amplification | Peak (m³/s) | Peak Date |
|-------|-------------------|-------------|-----------|
| Guadiana | **11.5×** | 4,549 | Feb 6 |
| Tejo | **6.6×** | 6,791 | Feb 7 |
| Mondego | **6.0×** | 1,848 | Feb 12 |
| Sado | **4.6×** | 1,985 | Feb 5 |
| Douro | **4.5×** | 4,796 | Feb 7 |

Peak timing aligns with Leonardo (Feb 5-7) for most rivers, Marta (Feb 10-12) for Mondego and Lis. The narrative that "before the rivers dropped, the next storm hit" is visible in the data — discharge stays elevated between storms.

**Methodological note:** Climatological anomaly ratios (~1.0) are misleading because Jan-Feb IS the wet season. The correct narrative metric is **within-season storm amplification** (storm period vs. pre-storm baseline), which shows 3-11× jumps.

**Signal strength: 4/5** — strong signal, but GloFAS models naturalized flows (ignores dams), so Douro/Guadiana may overstate.

### Chapter 1 (The Hook) — NEEDS MANUAL ACQUISITION

Sentinel-1 flood extent image is the visual anchor. Not API-fetchable — requires manual download (see Blockers section).

### Chapter 2 (The Atlantic Engine) — DATA GAP (acceptable)

SST anomaly and atmospheric river data not acquired (P2 priority in design doc). Can use static image overlays from published climate reports for v0. This chapter is context-setting, not data-critical.

### Chapter 6 (The Human Cost) — PARTIALLY READY

CEMS flood extent polygons are identified and freely downloadable (see below). Consequence markers need manual curation (Nelson).

### Chapter 7 (The Full Picture) — READY

All constituent layers (soil, precip, discharge, basins) are validated and available. This chapter composites existing data — no new acquisition needed.

### Chapters 8-9 — READY

Precondition index can be calculated from the three validated datasets. Explore mode is scaffolded.

---

## 2. Data Readiness

### Ready in `data/` (16 files, 556 KB total)

| Directory | Files | Size | Status |
|-----------|-------|------|--------|
| `data/soil-moisture/` | grid-points.json, timeseries.json, basin-averages.json | 160 KB | Ready |
| `data/discharge/` | 8 per-river JSON + summary.json | 76 KB | Ready |
| `data/precipitation/` | daily-grid.json, accumulation-jan25-feb07.json, basin-averages.json | 296 KB | Ready |
| `data/flood-extent/` | README.md (download instructions) | 12 KB | Needs download |
| `data/consequences/` | (empty) | — | Needs manual curation |
| `data/static-images/` | (empty) | — | Needs acquisition |

### Notebooks & Figures

| Notebook | Script | Figures |
|----------|--------|---------|
| 03-soil-moisture-grid | .py + .ipynb | 3 figures (4-date maps, basin timeseries, all basins) |
| 04-discharge-timeseries | .py | 9 figures (8 rivers + comparison) |
| 05-precipitation-grid | .py | 3 figures (accumulation maps, location timeseries, basin timeseries) |
| 06-cems-investigation | .py | — (documentation only) |

---

## 3. Scroll Scaffold Status

**Working:** The page loads, shows the dark basemap with hero title, and scrolling triggers camera transitions through all 10 chapters.

| Component | File | Status |
|-----------|------|--------|
| Chapter config | `src/story-config.js` | Complete — 10 chapters with camera, layers, text |
| Map controller | `src/map-controller.js` | Complete — CARTO Dark Matter, flyTo/easeTo |
| Scroll observer | `src/scroll-observer.js` | Complete — IntersectionObserver, debounced |
| Layer manager | `src/layer-manager.js` | Complete — all data layers stubbed |
| Exploration mode | `src/exploration-mode.js` | Complete — geolocation, nav controls |
| Orchestration | `src/main.js` | Complete |
| HTML structure | `index.html` | Complete — 13 sections (ch6 split into 3 substeps) |
| Visual system | `style.css` | Complete — glassmorphism, responsive, dark theme |

**Old v2/v3 dashboard files:** Deleted (src/data/, src/map/, src/ui/).

**What renders now:** Basemap + title screen + camera transitions + basin outlines + district outlines + chapter text cards.

**What's stubbed:** All 11 data-dependent layers (sentinel1, sst, soil-moisture-animation, precipitation-accumulation, glofas-discharge, flood-extent-polygons, consequence-markers, etc.) — these log "data not yet available" and will render once data files are wired in.

---

## 4. Blockers (Nelson's Manual Tasks)

### P0 — Story doesn't work without these

1. **Download CEMS flood extent ZIPs** (4 downloads, ~10 min)
   - Commands in `data/flood-extent/README.md`
   - Extract GeoJSON flood polygons, save as `data/flood-extent/emsr861.geojson` + `emsr864.geojson` + `combined.geojson`
   - Key: AOI03 Salvaterra de Magos = 64,198 ha flooded (Tejo basin visual anchor)

2. **Curate consequence markers** (~2-3 hours)
   - Need ~30-50 geocoded events: deaths, evacuations, A1 collapse, Mondego levee, landslides
   - Sources: Proteção Civil SitReps, Lusa dispatches, Público/Expresso
   - Output: `data/consequences/events.geojson`

### P1 — Significantly improves the story

3. **Acquire Sentinel-1 composite** for Chapter 1
   - The ESA-published Feb 7 flood extent image
   - Check ESA website or Earth Search STAC for downloadable GeoTIFF
   - Save to `data/static-images/sentinel1-tejo-feb07.png` or as COG

4. **Source photos** for Chapter 6 (human cost)
   - Proteção Civil social media (public domain)
   - Municipal câmara posts
   - Need coordinates + timestamp + attribution per photo

### P2 — Nice-to-have for v0

5. **SST anomaly map** for Chapter 2 — can use published NOAA/Copernicus map as static image overlay
6. **Storm track visualization** — can use IPMA/AEMET published maps
7. **IPMA historical warnings** — no API, would need manual reconstruction

---

## 5. Recommended Next Sprint

### Sprint 02: Wire Data → Scroll

Now that we have validated data and a working scroll scaffold, the next sprint plugs them together:

1. **Wire soil moisture animation** (Chapter 3) — load timeseries.json, render as animated circle layer with color ramp, scroll-controlled temporal playback
2. **Wire precipitation map** (Chapter 4) — load accumulation JSON, render as graduated circles or heatmap
3. **Wire discharge visualization** (Chapter 5) — load per-river JSON, render as line charts in sidebar panels or as river-width encoding on basins
4. **Wire CEMS flood extent** (Chapter 6) — load combined.geojson, render as red polygons (requires Nelson to download first)
5. **Build temporal player** — `src/temporal-player.js` for chapters with animated data (soil moisture, precipitation)
6. **Chapter 6 multi-stop** — wire consequence markers + photo overlays
7. **Precondition index calculation** — combine soil + precip + discharge into composite index for Chapters 7-8
8. **Responsive polish** — test on mobile, adjust panel sizing, reduce layers for performance

### Parallel track (Nelson)
- Download CEMS ZIPs and extract GeoJSON
- Begin consequence marker curation
- Source Sentinel-1 composite image

---

## Appendix: Grid Alignment

Soil moisture and precipitation agents used compatible grids:
- **Soil moisture:** 74 points, 0.4° spacing (ocean points filtered)
- **Precipitation:** 330 points, 0.25° spacing (denser grid)

Both cover mainland Portugal bbox [36.9, -9.6, 42.2, -6.1]. The precipitation grid is denser — for shared visualizations, the soil moisture grid should be interpolated to match, or both can be visualized independently at their native resolution (the scroll narrative shows them in different chapters).

---

*Generated by Sprint 01 validation team, 2026-02-15*
