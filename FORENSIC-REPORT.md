# FORENSIC REPORT: cheias.pt Sprint 02 Build Audit

**Date:** 2026-02-17
**Scope:** Gap analysis between design intent and shipped implementation
**Method:** Full code + data + config trace across all source files

---

## EXECUTIVE SUMMARY

The data pipeline is **100% complete** — all files exist, are valid, and cover the correct temporal/spatial ranges. The rendering pipeline is **architecturally sound** — scroll observer, camera transitions, layer manager, temporal player all function correctly. The failure is in the **last mile**: how data gets translated into meaningful visual representations on the map.

Three root causes explain every QA failure:

1. **Circle layers instead of continuous surfaces** — 342 scattered dots at 4-10px cannot convey spatial patterns
2. **Temporal animation wired for 1 of 3 temporal chapters** — Ch3 animates, Ch4 and Ch5 are static
3. **Soil moisture normalization eliminates visual dynamic range** — Dec 1 values already 0.49-1.0, making the entire animation look "uniform blue"

The data tells a powerful story. The code can deliver it. The gap is in visualization design — choosing layer types, color ramps, and temporal wiring that actually communicate the data.

---

## PHASE 1: DESIGN INTENT vs. REALITY

### Specification History

| Version | Date | Approach |
|---------|------|----------|
| CLAUDE-v1 | Feb 1 | Discovery/research only |
| CLAUDE-v2 | Feb 11 | Real-time dashboard (Mode 1+2) |
| V2-REVIEW | Feb 11 | QA of v2; recommended glassmorphism + continuous ramps |
| CLAUDE-v3 | Feb 11 | Dashboard implementation spec (3-agent team) |
| CLAUDE.md | Feb 16 | **Scrollytelling pivot** — 9-chapter geo-narrative |

The pivot from dashboard to scrollytelling changed everything. The data pipeline (built for dashboard) was repurposed for narrative, but the visualization layer was rebuilt from scratch in a single sprint.

### What Was Specified Per Chapter

| Ch | Design Intent | What Shipped | Gap |
|----|--------------|--------------|-----|
| 0 | Dark basemap, dramatic hero type | Hero text with no background treatment | No vignette/text-shadow |
| 1 | Sentinel-1 flood extent in red | Dark basemap only, no polygons | PMTiles layer not rendering |
| 2 | SST anomalies + storm tracks | Empty map + "em desenvolvimento" | Stubs (data not converted) |
| 3 | Soil moisture heatmap, Dec→Jan animation | Static uniform blue dot grid | Circle layer, bad color ramp |
| 4 | 3-storm precipitation animation (Kristin→Leonardo→Marta) | Static orange/red dot grid | No temporal wiring |
| 5 | River hydrographs + sparkline charts | Tiny dots + dark polygon overlay | Circles not charts, rivers undrawn |
| 6a-c | Flood extent + consequence markers + photos | 2-3 markers, no flood polygons | PMTiles not rendering, filtering issues |
| 7 | All layers overlaid (retrospective synthesis) | Risk index polygons + dot grid | Narrative inversion — prediction not facts |
| 8 | Precondition index proof ("data knew") | Nearly all Portugal "Risco baixo" | Wrong timestep for narrative |
| 9 | All layers toggleable, geolocation | Zero visible layers, toggles no effect | Layers never ensured for Ch9 |

---

## PHASE 2: DATA PIPELINE INVENTORY

**Verdict: Complete and valid. The break is NOT here.**

| Dataset | Files | Size | Status |
|---------|-------|------|--------|
| Flood extent (CEMS) | 5 GeoJSON + 4 PMTiles + 3 Parquet | 242 MB | Complete (15,253 polygons) |
| Consequence markers | 1 GeoJSON | 52 KB | Complete (42 events, bilingual) |
| Soil moisture frames | JSON (342 pts × 77 days) | ~3.8 MB | Complete |
| Precipitation frames | JSON (342 pts × 77 days) | ~2.1 MB | Complete but unused |
| Precip storm totals | JSON (342 pts) | ~800 KB | Complete |
| Discharge timeseries | JSON (11 stations × 77 days) | ~60 KB | Complete |
| Precondition frames | JSON (342 pts × 77 days) | ~3.5 MB | Complete but unused |
| Precondition peak | JSON (342 pts) | ~1.2 MB | Complete but unused |
| Precondition basins | JSON (11 basins × 2 snapshots) | <10 KB | Complete |
| IVT peak storm | JSON | — | Complete but unused |
| SST anomaly | NetCDF + 62 daily COGs | ~620 MB | Present, not converted to web format |
| Districts + Basins | GeoJSON | 91 KB | Complete |

**Total browser payload:** ~3 MB JSON + 17 MB PMTiles = ~20 MB (reasonable)

All temporal datasets aligned: Dec 1, 2025 → Feb 12, 2026 (77 days), daily frequency, 342-point grid at 0.25° spacing.

---

## PHASE 3: RENDERING PIPELINE TRACE

### Architecture Diagram

```
User scrolls
  → scroll-observer.js (IntersectionObserver, threshold 0.5)
    → main.js:onChapterEnter(chapterId, config)
      ├─ map-controller.js:flyToChapter()     [camera]
      ├─ layer-manager.js:showChapterLayers()  [layer visibility]
      ├─ chapter-wiring.js:enterChapter3/4/5() [data loading]
      ├─ exploration-mode.js                   [Ch9 only]
      └─ main.js:updateDynamicLegend()         [legend]

For Ch3 temporal animation:
  scroll-observer.js:onChapterProgress()
    → temporal-player.js:setProgress(0-1)
      → chapter-wiring.js callback
        → layer-manager.js:updateSourceData()
```

### Module-by-Module Status

| Module | Lines | Status | Issues |
|--------|-------|--------|--------|
| `map-controller.js` | 124 | Solid | PMTiles protocol registered correctly |
| `scroll-observer.js` | 154 | Solid | Progress tracking works, substeps handled |
| `temporal-player.js` | 49 | Solid | Clean state machine, correctly maps scroll→frame |
| `data-loader.js` | 25 | Solid | All paths correct, caching works |
| `story-config.js` | 237 | Has issues | Ch6c coords wrong, Ch7/8 layer assignments questionable |
| `layer-manager.js` | 446 | Has issues | All data layers are circles; sourceRef fragile |
| `chapter-wiring.js` | 187 | Has issues | Only Ch3 uses temporal player; Ch4 static only |
| `exploration-mode.js` | 143 | Has issues | References non-existent `precondition-fill` layer |
| `main.js` | 183 | Has issues | Ch7/Ch8 precondition assignment inverted for narrative |

---

## PHASE 4: SPECIFIC FAILURE POINTS

### Issue #1: Hero text illegible (Ch0)

**File:** `index.html` — Chapter 0 section
**Cause:** The `chapter--hero` section is the only chapter without a `.chapter__card` glassmorphism wrapper. Title/subtitle render directly over the map with no background treatment.
**Fix:** Add CSS vignette overlay (`radial-gradient`) + `text-shadow` to hero text. Do NOT add a card — preserve cinematic feel.

---

### Issue #2: Flood extent not rendering (Ch1, Ch6a-c)

**File:** `layer-manager.js:103-114`
**Cause:** The `sentinel1-flood-extent` layer is defined with PMTiles source and initial `fill-opacity: 0`. When `showChapterLayers` calls `setLayerOpacity(map, 'sentinel1-flood-extent', 0.8)`, it should make the layer visible.

The `flood-extent-polygons` layer (used in Ch6) uses `sourceRef: 'sentinel1-flood-extent'`. The `ensureLayer` function (line 173-176) recursively ensures the referenced layer's source exists before creating the referencing layer.

**Probable root cause:** The PMTiles source URL `'pmtiles://data/flood-extent/combined.pmtiles'` is a **relative URL**. If the development server doesn't serve from the project root, or if there's a base path mismatch, the PMTiles file won't load. MapLibre silently fails on tile load errors — no console error, just empty tiles.

**Verification needed:** Open browser devtools Network tab, filter for `.pmtiles`, check if the range requests return 200 or 404.

**Secondary issue:** The `sourceRef` pattern in `ensureLayer` (line 173-176) works correctly in the code — the recursive call ensures the parent source exists before adding the child layer. But if the PMTiles source itself fails to load, both `sentinel1-flood-extent` and `flood-extent-polygons` will be invisible.

---

### Issue #3: Soil moisture is static uniform blue (Ch3)

**File:** `layer-manager.js:33-47` + `data/frontend/soil-moisture-frames.json`

**Three compounding causes:**

**A. Layer type is `circle`, not `heatmap`:**
The design doc calls for "heatmap morphing from blue (dry) to red (saturated)." The implementation uses `circle` type — 342 scattered dots at 4-10px radius. At zoom 7, these are visible individually but convey no spatial continuity. Citizens cannot read scatter plots.

**B. Color ramp has no visual dynamic range:**
```javascript
// layer-manager.js:38-43
'circle-color': [
  'interpolate', ['linear'], ['get', 'value'],
  0, '#f7f7f7',    // white = dry
  0.5, '#67a9cf',  // light blue
  1.0, '#2166ac',  // dark blue = saturated
]
```
The ramp is white→blue (single-hue). The problem: Dec 1 data values are already 0.49-1.0 (normalized `sm_rootzone / 0.42`). Even "dry" December values map to light-to-dark blue. The animation from Dec→Jan appears as blue→slightly darker blue — visually indistinguishable.

**C. The temporal animation actually works — but looks static:**
`chapter-wiring.js:60-91` correctly wires `temporal-player` to `scroll-observer` progress. The `onFrame` callback updates the GeoJSON source. The date label updates. But because the color ramp shows no visual change, scrolling appears to do nothing.

**Fix needed:**
1. Switch to `heatmap` layer type (MapLibre native) or IDW interpolation
2. Use diverging color ramp (brown→white→blue or warm→cool) with breakpoints matched to actual data range
3. Normalize data to use full 0-1 range where 0 = actual minimum value, 1 = actual maximum

---

### Issue #4: Precipitation static (Ch4)

**File:** `chapter-wiring.js:106-115`

**Cause:** `enterChapter4()` loads `loadPrecipStormTotals()` — a **static** accumulation snapshot — and renders it as a single GeoJSON update. The function `loadPrecipFrames()` exists in `data-loader.js:21` but is **never imported or called** in `chapter-wiring.js`.

The temporal player is not wired for Ch4. There is no `onChapterProgress('chapter-4', ...)` call.

```javascript
// chapter-wiring.js:106-115 — the ENTIRE Ch4 implementation
export async function enterChapter4() {
  if (!map) return;
  if (ch3Initialized) leaveChapter3();
  const data = await loadPrecipStormTotals();       // STATIC totals
  const geojson = pointsToGeoJSON(data.points, 'total_mm');
  updateSourceData(map, 'precipitation-accumulation', geojson);
  // No temporal player. No scroll progress. No animation.
}
```

The `precip-frames.json` file (342 pts × 77 days, ~2.1 MB) sits in `data/frontend/` completely unused. The three-storm sequence (Kristin→Leonardo→Marta) is invisible.

**Fix needed:** Wire `precip-frames.json` through `temporal-player` with `onChapterProgress`, same pattern as Ch3.

---

### Issue #5: Rivers invisible, no hydrographs (Ch5)

**File:** `layer-manager.js:68-86` + `chapter-wiring.js:120-164`

**Three issues:**

**A. Discharge rendered as circles, not river lines:**
`glofas-discharge` is a `circle` layer with 11 station points sized by `discharge_ratio`. At zoom 8, these are small dots. Rivers are never drawn as lines — no river geometry GeoJSON exists in the frontend assets.

**B. Discharge ratio values are subtle:**
From memory: "Climatological ratios are 1.0-1.6 in wet season." The circle radius interpolation starts at ratio 1→6px, 5→14px. Most stations have ratios 1-5, so circles are 6-14px — small and similar-looking.

**C. No inline hydrograph charts:**
The discharge-timeseries.json contains full 77-day time series per station, but `enterChapter5()` only extracts peak values. The notebook-generated hydrograph plots are not integrated. The design called for "inline sparkline/hydrograph charts in cards."

---

### Issue #6: Ch6c wrong coordinates

**File:** `story-config.js:165`

```javascript
camera: { center: [-8.63, 40.10], zoom: 13, pitch: 45, bearing: 5 },
```

**Actual A1 collapse location (evt-017):** `[-8.487, 40.217]` (km 191, Soure area)
**Config points to:** `[-8.63, 40.10]` (Vila Nova de Ancos area, ~15km southwest)

**Fix:** Update to `center: [-8.487, 40.217]`.

---

### Issue #7: Consequence markers — green dot, few visible

**File:** `layer-manager.js:117-141` + `main.js:59-64`

**A. Green dot is a `rescue` event:**
```javascript
// layer-manager.js:130
'rescue', '#27ae60',  // GREEN
```
The legend (story-config.js:137-141) lists Mortes/Evacuações/Infraestrutura/Deslizamentos but NOT Rescue, Closure, Power Cut, Military, Political. Any rescue event appears as an unexplained green dot.

**Fix:** Either add all event types to legend, or consolidate minor types under "Outros."

**B. Few markers visible per substep:**
`filterConsequencesByChapter(map, chapterNum)` at `main.js:63` filters by chapter number. For substeps (6a, 6b, 6c), the regex `chapterId.match(/chapter-(\d+)/)` extracts `6`. So all substeps filter to `chapter === 6`. Only events in `events.geojson` with `"chapter": 6` will show.

**Verification needed:** Count how many events have `chapter: 6` in events.geojson. If some events relevant to Ch6 locations have other chapter values, they'll be hidden.

---

### Issue #8: Ch7 shows predictive risk instead of factual synthesis

**File:** `main.js:68-69` + `story-config.js:180-191`

Ch7 ("A Cadeia Causal") is specified as the **climax** — "all layers overlaid showing causal relationships." Its layers are:

```javascript
// story-config.js:180-184
layers: [
  { id: 'basins-fill', opacity: 0.6 },
  { id: 'flood-extent-polygons', opacity: 0.5 },
  { id: 'consequence-markers', opacity: 0.8 },
  { id: 'precipitation-accumulation', opacity: 0.3 },
],
```

Then `main.js:68-69` colors basins by **peak precondition**:
```javascript
if (chapterNum === 7) {
  colorBasinsByPrecondition(map, 'peak');
}
```

And the legend says "Risco crítico/elevado/moderado/baixo."

**The narrative inversion:** Ch7 text describes WHAT HAPPENED (retrospective facts), but the visualization shows a PREDICTIVE risk index. The basins-fill overlay (at 0.6 opacity) partially covers the flood-extent-polygons (at 0.5 opacity), creating visual noise.

**What Ch7 should show:** Flood extent + all 42 consequence markers (no filter) + basin outlines. No precondition coloring. The power is in seeing ALL the damage at once.

---

### Issue #9: Ch8 "Risco baixo" everywhere

**File:** `main.js:70-71` + `data/frontend/precondition-basins.json`

Ch8 calls `colorBasinsByPrecondition(map, 'pre_storm')`. The pre_storm snapshot (Jan 25) values are:

```
Algarve: 0.021, Guadiana: 0.015, Sado: 0.037, Tejo: 0.150
Lis: 0.222, Zêzere: 0.016, Mondego: 0.288, Vouga: 0.142
Douro: 0.152, Minho-Lima: 0.485
```

The color ramp (`layer-manager.js:401-411`):
- < 0.2 → `#2166ac` (blue = "Risco baixo")
- 0.2-0.4 → `#67a9cf`
- 0.4-0.6 → `#f7f7f7`
- 0.6-0.8 → `#ef8a62`
- 0.8-1.0 → `#b2182b` (red = "Risco crítico")

**Result:** 8 of 11 basins fall below 0.2 → all blue ("Risco baixo"). Only Lis (0.222), Mondego (0.288), and Minho-Lima (0.485) show any differentiation. The text claims "grande parte de Portugal centro e sul em condições de risco elevado" but the data shows the OPPOSITE.

**Root cause:** The pre_storm snapshot (Jan 25) genuinely shows low precondition values. The text is aspirational — it describes what the index SHOULD have shown, not what it actually did show. The "early warning" thesis is not supported at the Jan 25 date.

**Fix options:**
- Ch8 should show the PEAK precondition (Feb 5) to prove "the data knew" — the peak values DO show critical risk (Mondego 0.91, Minho-Lima 1.0, Tejo 0.75)
- OR: Ch8 should animate the precondition progression from Jan 25 → Feb 5, showing risk building
- The text needs to match whichever approach is chosen

---

### Issue #10: Explore mode non-functional (Ch9)

**File:** `story-config.js:225` + `exploration-mode.js:18-25` + `layer-manager.js`

**Multiple compounding issues:**

**A. Ch9 has empty layers array:**
```javascript
// story-config.js:225
layers: [],
```
So `showChapterLayers` fades ALL active layers to 0 and ensures NO new layers. If the user scrolled through the full story, layers exist on the map but are now invisible.

**B. `applyAllToggles` calls `setLayerOpacity` which checks `map.getLayer()`:**
If previous chapters created the layers, they still exist on the map (just at opacity 0). `applyAllToggles` should re-show them. But for dynamic layers (soil-moisture-snapshot, precipitation-accumulation, glofas-discharge), their GeoJSON sources may contain data from the last chapter that loaded them — or empty data if those chapters were skipped.

**C. `precondition-fill` does not exist:**
```javascript
// exploration-mode.js:23
'precondition': { layers: ['precondition-fill'], opacity: 0.7 },
```
`precondition-fill` is NOT in `LAYER_DEFS`. Toggling "precondition" silently fails.

**D. PMTiles layers (flood extent) silently fail if source didn't load:**
If the PMTiles URL issue (Issue #2) affects all sessions, flood extent will also be invisible in explore mode.

**E. At zoom 6 (Ch9 camera), circle layers are nearly invisible:**
11 discharge dots at 6-14px, 342 soil moisture dots at 4px, 342 precip dots at 3-16px — scattered across all of Portugal at zoom 6, they're technically visible but convey nothing.

---

## PHASE 5: PROCESS AUDIT

### How Did the Build Agents Work?

**1. Were design documents followed?**
Partially. The architecture (scroll observer, layer manager, temporal player, chapter wiring) matches the spec exactly. The chapter sequence, camera positions, text content, and module structure all follow CLAUDE.md. The deviation is in VISUALIZATION DESIGN — the spec says "heatmap morphing" but the implementation uses scatter plot circles.

**2. Gap between specified and implemented?**
The spec describes the USER EXPERIENCE ("soil saturates visually", "three storms hit in sequence", "rivers spike dramatically"). The implementation delivers the INFRASTRUCTURE ("soil moisture layer exists", "precipitation layer exists", "discharge layer exists"). The gap is between "layer exists" and "layer communicates data."

**3. Did agents validate visually?**
No evidence of visual validation. The Sprint 02 report claims "11 of 15 layers wired" — this was verified by checking that code paths exist, not that visual output was meaningful. The dev server was started (`http://localhost:3001`) but no systematic visual check was performed per chapter.

**4. Were notebook outputs referenced during frontend build?**
No. The notebooks produce matplotlib charts (hydrographs, heatmaps, scatter plots with proper color ramps) that demonstrate what the data SHOULD look like. The frontend layer definitions were written independently, using generic MapLibre circle layers without consulting the notebook visualizations.

**5. Integration test or component-level only?**
Component-level only. Each agent worked on its assigned files. The data-pipeline agent converted Parquet→JSON. The chapter-wiring agent connected JSON→layers. The polish agent styled the UI. No agent tested the END-TO-END experience of scrolling through the story and verifying that each chapter's visualization matched the narrative text.

**6. "Something renders" over "the right thing renders"?**
Yes. This is the primary process failure. The build optimized for "no console errors" and "code compiles" rather than "data communicates meaning." Every circle layer renders without errors. The PMTiles source registers. The temporal player ticks. But the visual output doesn't tell the story.

---

## PHASE 6: ROOT CAUSE ANALYSIS

### Primary Root Cause

**Circle layers cannot communicate spatial hydro-meteorological data.**

Every data chapter (Ch3, Ch4, Ch5, Ch7, Ch8) renders 342 points as MapLibre `circle` layers at 4-10px radius. At the zoom levels used (6-8), these appear as a scattered dot matrix with minimal color variation. Citizens — the target audience — cannot read scatter plots.

The design doc specified "heatmap morphing" and "continuous surfaces." MapLibre supports native `heatmap` layers. The implementation chose the simplest possible visualization (circles) and never revisited whether it communicated the data.

### Contributing Factors

| Factor | Impact | Files |
|--------|--------|-------|
| **Soil moisture normalization kills color range** | Dec values already 0.49-1.0; entire animation appears "blue" | `soil-moisture-frames.json` + `layer-manager.js:38-43` |
| **Temporal animation wired for Ch3 only** | Ch4 (precipitation) is static despite having frame data | `chapter-wiring.js:106-115` |
| **PMTiles flood extent not rendering** | Ch1, Ch6, Ch7 flood polygons invisible | Probable URL resolution issue |
| **No river line geometry** | In a flood story, rivers are never drawn | No river GeoJSON in frontend assets |
| **Ch7/Ch8 narrative-data mismatch** | Ch7 shows predictive risk, Ch8 shows low baseline | `main.js:67-74` + `precondition-basins.json` |
| **Ch6c coordinate error** | Camera 15km from actual event | `story-config.js:165` |
| **Explore mode references non-existent layer** | Precondition toggle silently fails | `exploration-mode.js:23` |
| **Legend incomplete** | 5 of 11 event types missing from legend | `story-config.js:137-141` |

### Process Failures

1. **No visual QA gate** — "layer wired" defined as "code path exists" not "data renders meaningfully"
2. **Notebook outputs not referenced** — matplotlib charts show correct visualizations; frontend ignores them
3. **No end-to-end scroll test** — agents validated per-module, never the full story experience
4. **Optimization for zero errors over communication** — clean console ≠ working visualization
5. **Sprint 02 report overstated completeness** — "11 of 15 layers wired" conflated infrastructure with function

### Data Pipeline Gaps

| Data | Exists | Loaded | Rendered | Communicates |
|------|--------|--------|----------|-------------|
| Flood extent (PMTiles) | Yes | Probable fail | No | No |
| Soil moisture frames (77 days) | Yes | Yes | As dots | No — blue-on-blue |
| Precip frames (77 days) | Yes | **Never loaded** | No | No |
| Precip storm totals (static) | Yes | Yes | As dots | Barely |
| Discharge timeseries (11 rivers) | Yes | Yes | As dots | No — too small |
| Precondition frames (77 days) | Yes | **Never loaded** | No | No |
| Precondition peak (static) | Yes | **Never loaded** | No | No |
| Precondition basins (2 snapshots) | Yes | Yes (Ch7/8) | As basin fill | Partially (values too low in Ch8) |
| Consequence markers (42 events) | Yes | Yes | As dots | Partially (filtering hides most) |
| IVT peak storm | Yes | **Never loaded** | No | No |

**5 of 10 frontend JSON files are never loaded by any code path.** The data pipeline produced 8 files; only 3 are consumed (soil-moisture-frames, precip-storm-totals, discharge-timeseries).

---

## SPECIFIC CODE FIXES NEEDED

### Critical (blocks story comprehension)

| # | File | Line(s) | What's Wrong | What It Should Be |
|---|------|---------|-------------|------------------|
| 1 | `layer-manager.js` | 33-47 | `soil-moisture-animation` is `circle` type | Change to `heatmap` or IDW interpolated fill |
| 2 | `layer-manager.js` | 38-43 | Color ramp 0→white, 1→blue (single-hue, no dynamic range) | Diverging ramp (brown/warm→white→blue) with breakpoints at 0.3, 0.5, 0.7, 0.9 |
| 3 | `layer-manager.js` | 48-66 | `precipitation-accumulation` is `circle` type | Change to `heatmap` or graduated circle with larger radius |
| 4 | `chapter-wiring.js` | 106-115 | `enterChapter4()` loads static totals only | Wire `loadPrecipFrames()` through temporal-player, same as Ch3 |
| 5 | `layer-manager.js` | 103-114 | PMTiles flood extent probably not loading | Verify URL resolution; consider absolute path or check dev server config |
| 6 | `story-config.js` | 165 | Ch6c center `[-8.63, 40.10]` | Change to `[-8.487, 40.217]` |
| 7 | `main.js` | 67-74 | Ch7 colors basins by peak precondition (predictive) | Ch7 should show flood extent + all markers (retrospective synthesis); remove precondition coloring |
| 8 | `main.js` | 70-71 | Ch8 uses `'pre_storm'` (values mostly < 0.2 = "Risco baixo") | Ch8 should use `'peak'` to show "data knew" OR animate Jan 25→Feb 5 progression |

### High (visual quality)

| # | File | Line(s) | What's Wrong | What It Should Be |
|---|------|---------|-------------|------------------|
| 9 | `story-config.js` | 137-141 | Legend only lists 4 of 11 event types | Add rescue, closure, river_record, power_cut, levee_dam or group as "Outros" |
| 10 | `exploration-mode.js` | 23 | References non-existent `precondition-fill` layer | Add `precondition-fill` to `LAYER_DEFS` or remove from toggle map |
| 11 | `story-config.js` | 225 | Ch9 `layers: []` means no layers are ensured | Add all toggleable layers to Ch9 config at opacity 0, so they're ensured before explore mode |
| 12 | `chapter-wiring.js` | — | No `enterChapter7()` or `enterChapter8()` | Add functions that load precondition data and set up appropriate layers |
| 13 | `index.html` | Ch0 section | No vignette or text-shadow on hero | Add CSS gradient overlay or text-shadow for readability |

### Medium (data utilization)

| # | File | What's Missing |
|---|------|---------------|
| 14 | No river geometry | Add river line GeoJSON (from basins.geojson rivers or OpenStreetMap extract) |
| 15 | `precondition-frames.json` unused | Wire to temporal animation for Ch8 |
| 16 | `precondition-peak.json` unused | Wire to Ch7 or Ch8 as point-level detail |
| 17 | `ivt-peak-storm.json` unused | Wire to Ch2 as atmospheric river visualization |
| 18 | Discharge timeseries unused | Render as inline sparkline charts or HTML canvas hydrographs in Ch5 card |

---

## ARCHITECTURAL RECOMMENDATIONS

### 1. Replace circle layers with heatmaps for continuous data

MapLibre supports native `heatmap` layers that interpolate point data into continuous surfaces. For 342-point grids, this produces readable spatial patterns:

```javascript
// Example: heatmap layer for soil moisture
'soil-moisture-heatmap': {
  type: 'heatmap',
  source: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
  paint: {
    'heatmap-weight': ['get', 'value'],
    'heatmap-intensity': 1,
    'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 5, 20, 9, 40],
    'heatmap-color': [
      'interpolate', ['linear'], ['heatmap-density'],
      0, 'rgba(0,0,0,0)',
      0.2, '#d73027',  // dry = warm
      0.4, '#fc8d59',
      0.6, '#fee08b',
      0.8, '#d9ef8b',
      1.0, '#1a9850',  // saturated = green/blue
    ],
    'heatmap-opacity': 0,
  },
}
```

### 2. Wire temporal animation for all temporal chapters

Three chapters need scroll-driven animation using the existing `temporal-player`:
- Ch3: soil moisture (already done)
- Ch4: precipitation (precip-frames.json ready)
- Ch8: precondition index (precondition-frames.json ready)

The pattern is proven in Ch3. Replicate it.

### 3. Fix the narrative arc for Ch7/Ch8

- **Ch7 (Cadeia Causal):** Show ALL flood extent + ALL 42 consequence markers + basin outlines. No precondition coloring. The visual argument is: "look at all the damage."
- **Ch8 (O Que os Dados Já Sabiam):** Animate precondition index from Jan 25 → Feb 5 using precondition-frames.json. The visual argument is: "the risk was building for weeks — and the data showed it."

### 4. Ensure all layers exist before exploration mode

Ch9's `layers: []` means `showChapterLayers` ensures nothing. Before entering explore mode, all toggleable layers should be ensured on the map with their data loaded:

```javascript
// In a new enterChapter9() function:
export async function enterChapter9() {
  // Ensure all exploration layers have data
  await Promise.all([
    ensureFloodExtent(),
    ensureSoilMoistureSnapshot(),
    ensurePrecipTotals(),
    ensureDischargePoints(),
    ensurePreconditionFill(),
  ]);
}
```

### 5. Add inline charts for discharge (Ch5)

The discharge timeseries data is rich — 11 rivers × 77 days with clear storm amplification signals. Rendering as circles wastes this. Options:
- HTML Canvas sparklines in the chapter card
- D3.js inline SVG hydrographs
- Mapbox-style chart popups on station click

### 6. Re-normalize soil moisture for visual range

The current normalization (sm_rootzone / 0.42) maps December values to 0.49+. For the animation to show visible change, renormalize to the actual data range:

```
visual_value = (value - dataset_min) / (dataset_max - dataset_min)
```

Where `dataset_min` = minimum across all 77 frames, `dataset_max` = maximum. This ensures Dec 1 maps to ~0 (warm/dry colors) and Feb 5 maps to ~1 (cool/saturated colors).

---

## CONCLUSION

The cheias.pt scrollytelling is not broken — it's **unfinished at the visualization layer**. The architecture is sound. The data is complete. The story arc is compelling. What remains is the hardest part of data journalism: making the data SPEAK through the map.

The Sprint 02 agents built the plumbing. Sprint 03 needs to open the taps.

**Priority order for next sprint:**
1. Fix PMTiles loading (unblocks Ch1, Ch6, Ch7, Ch9)
2. Replace circle layers with heatmaps (unblocks Ch3, Ch4, Ch5)
3. Wire temporal animation for Ch4 and Ch8
4. Fix Ch7/Ch8 narrative alignment
5. Fix Ch6c coordinates + consequence marker filtering
6. Ensure layers for exploration mode
7. Add river line geometry
8. Add inline discharge charts
