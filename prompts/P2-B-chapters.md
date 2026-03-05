## Session 6.5: Architecture Refactor — GSAP Timelines (run BEFORE Session 7)

**Estimated:** 1-2 hours

**Read:** `prompts/P2-architecture-fix.md`

Sessions 5-6 used scroll-progress-to-state mapping (v0 pattern). This MUST be fixed
before Ch.4 — the 13-layer synoptic stack is unmaintainable in a scroll-breakpoint style.

**Principle:** Scroll = chapter selection. GSAP = choreography within chapters.

### Refactor existing chapters

1. **Ch.1:** Replace `handleChapter1Progress` with `enterChapter1()` GSAP timeline:
   - On enter: flood extent fades 0→0.7 over 2s
   - On exit: flood fades to 0 over 1s
   - Delete the scroll-progress breakpoint handler entirely

2. **Ch.2:** Replace `handleChapter2Progress` with `enterChapter2Timeline()`:
   - 0s: SST fade-in (1.5s)
   - 2s: Storm tracks appear (1s)
   - 3.5s: Globe rotation (2s)
   - 5s: IVT player starts + date label
   - 6s: Wind particles fade-in (1s)
   - 9s: Camera push toward Portugal (4s)
   - Keep `enterChapter2()` for async data loading. Timeline starts AFTER load.
   - `leaveChapter2()` kills timeline wherever it is.

3. **Ch.3:** KEEP scroll-driven. This is correct — scroll = time (Dec→Feb).

4. **Update `onStepProgress`:** Remove Ch.1 and Ch.2 progress handlers. Only keep:
   - Ch.3 scroll-driven player
   - Pre-load triggers (progress > 0.8)
   - Ch.4 sub-chapter selection (for Session 7)
   - Ch.7 sequential build (for Session 9)

5. **Add `onStepExit` cleanup:** When exiting ANY chapter, kill its active timeline.

### Verify

- Ch.0: Ghost pulse unchanged (already correct)
- Ch.1: Enter → flood fades in over 2s. Exit → fades out. No scroll dependency.
- Ch.2: Enter → designed sequence plays. Exit → everything cleans up.
- Ch.3: Scroll-driven SM unchanged.
- Fast scroll through Ch.1→Ch.2→Ch.3: no broken states, no orphaned animations.

### Commit

`P2.B-fix: refactor Ch.1-2 from scroll-progress breakpoints to GSAP timeline choreography`

---

# P2 Track B: Chapter Implementation (Opus)

## Run Context

- **Model:** Opus
- **Prerequisites:** Track A complete (P2.A1-A4 all passing verification)
- **Branch:** `v2/phase-2` (same branch, continuing)

## Before Starting

Verify Track A deliverables exist and work:

```bash
# Quick smoke test — run dev server and check console
npm run dev
# In browser console:
# 1. COG pipeline
import('./data-loader').then(m => m.loadCOG('https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/sst/2026-01-15.tif').then(r => console.log('COG OK:', r.width, r.height)))
# 2. WeatherLayers GL (check import resolves)
import('weatherlayers-gl').then(m => console.log('WL OK:', Object.keys(m)))
# 3. Globe
# Scroll to Ch.2 — should show globe projection
# 4. Terrain
# Scroll to Ch.5 — should show terrain
```

If any fail, fix Track A first. Do not proceed with broken plumbing.

**Read first:**
1. `CLAUDE.md`
2. `prompts/scroll-timeline-symbology.md` §2 (ALL chapter specs, frame-by-frame)
3. `data/colormaps/palette.json`
4. `data/basemap/IMPACT-GAUGE.md` (visual calibration, especially for Ch.4)
5. `src/weather-layers.ts` (from P2.A2)
6. `src/temporal-player.ts` (from P2.A3)

---

## Session 5: P2.B1 + P2.B3 — Hook (Ch.0-1) + Soil Moisture (Ch.3)

**Estimated:** 3-4 hours

### Ch.0: The Hook

**Spec:** Scroll timeline §2 Ch.0

- Basemap: ultra-dark (#060e14 ocean, #0a1520 land). No labels, no borders.
- Hero title: serif font, GSAP fade-in with letter stagger. Already in `animations.ts`.
- Ghost flood pulse: `combined.pmtiles` at 3% opacity, 2s fade in/out, 8s loop cycle.
  ```typescript
  // In onChapterEnter('chapter-0'):
  gsap.to({}, {
    duration: 2, repeat: -1, yoyo: true,
    onUpdate: function() { setLayerOpacity(map, 'flood-extent', this.progress() * 0.03) }
  });
  ```
- Number ticker: "11 mortes. 69 municípios." Already in `animations.ts` `animateCounters`.
- Camera: `[-15, 35]` z3 p0 — wide Atlantic.

### Ch.1: Flash-Forward

**Spec:** Scroll timeline §2 Ch.1

- Camera: flyTo `[-8.5, 39.5]` z6.5 p15 (Portugal close-up)
- Flood extent PMTiles: opacity 0% → 70% over 2s on enter
- Statistics text: "11 mortes. 69 municípios em calamidade."
- Source attribution: Copernicus EMS
- Scroll 0.8: flood starts fading (70% → 20%)
- Exit: flood fades to 0%, camera begins pulling toward globe view

### Ch.3: Soil Moisture (upgrade existing)

**Spec:** Scroll timeline §2 Ch.3

Existing scroll-driven SM player in `scroll-engine.ts` works. Upgrade:

1. **Basin sparklines:** Observable Plot in a side panel div. Load
   `data/frontend/precondition-basins.json`, render 5 river basin SM timeseries.
   ```typescript
   import * as Plot from '@observablehq/plot';
   const chart = Plot.plot({
     marks: [Plot.line(data, { x: 'date', y: 'sm_mean', stroke: 'basin' })],
     width: 280, height: 120,
   });
   ```

2. **Date counter:** Update existing overlay with formatted Portuguese date as scroll
   advances through SM frames.

3. **Wildfire foreshadow at scroll 0.5:** Burn scars (`wildfires-combined.pmtiles`)
   fade in to 15% opacity. Amber (#c0631a). Subtle hint — don't explain yet.

4. **Percentile annotation at scroll 0.7:** Text overlay "Percentil 98 — solo mais
   saturado que em 98% dos invernos desde 1991".

5. **Transition at scroll 0.8-1.0:** SM fades, precipitation layer begins fading in
   underneath (teaser for Ch.4).

### Commit

`P2.B1+B3: chapters 0-1 hook + chapter 3 soil moisture with sparklines and wildfire foreshadow`

---

## Session 6: P2.B2 — The Atlantic Engine (Ch.2)

**Estimated:** 3-4 hours

**Spec:** Scroll timeline §2 Ch.2

**The first high-impact 3D chapter.** Globe + multiple animated layers on curved ocean.

### Layer Build (scroll-driven sequence)

| Scroll | Action |
|--------|--------|
| 0.0 | Globe active. Dark ocean basemap (#0a212e). Camera: `[-25, 35]` z2.8 |
| 0.1 | **SST anomaly** fades in. COG → sst-diverging palette → BitmapLayer at 80%. Blue-white-red on globe. |
| 0.2 | Text: "O inverno trouxe uma energia incomum..." |
| 0.3 | **Storm tracks** appear. PathLayer (or MapLibre line layer) rendering full multi-vertex LineStrings from `storm-tracks-auto.geojson`. Named labels at midpoints. These are real tracked paths from MSLP minima (P1.B1), NOT simplified arcs. |
| 0.4 | Slight globe rotation (bearing 0→5 over 3s) |
| 0.5 | **IVT temporal player starts.** 77 daily frames at 2fps, loop. COG → ivt-sequential palette. Purple/white band = atmospheric river. |
| 0.6 | **Wind particles** (2000, white trails) activate. Flow along AR corridor. Lower density than Ch.4. |
| 0.8 | Text: "Três tempestades em três semanas." |
| 1.0 | Exit: globe→mercator transition. IVT + particles fade. Camera descends to Portugal. |

### Storm Tracks

```typescript
// Option A: MapLibre line layer (simpler, uses GeoJSON source directly)
map.addSource('storm-tracks', { type: 'geojson', data: stormTracksGeoJSON });
map.addLayer({
  id: 'storm-tracks',
  type: 'line',
  source: 'storm-tracks',
  paint: {
    'line-color': ['match', ['get', 'name'], 'Kristin', '#ff6464', 'Leonardo', '#64b5f6', 'Marta', '#ffc864', '#ffffff'],
    'line-width': 2.5,
    'line-opacity': 0.9,
  },
});

// These are real multi-vertex LineStrings from P1.B1 MSLP minima tracking.
// Each vertex has datetime + min_pressure_hpa properties.
// Do NOT simplify to 2-point arcs — the wandering path IS the data.
```

### IVT Temporal Player

```typescript
// Using TemporalPlayer from P2.A3:
const ivtPlayer = new TemporalPlayer('ch2-ivt', {
  mode: 'autoplay',
  fps: 2,
  loop: true,
  frameType: 'cog',
  paletteId: 'ivt-sequential',
  frames: ivtFrameSpecs, // 77 daily COGs
});
```

### Data

```
SST:         data/cog/sst/2026-01-15.tif (single frame)
IVT:         data/cog/ivt/*.tif (77 daily)
Wind U/V:    data/cog/wind-u/*.tif + wind-v/*.tif (subset for particle texture)
Storm tracks: data/qgis/storm-tracks-auto.geojson
```

### Commit

`P2.B2: chapter 2 Atlantic engine — globe, SST, IVT temporal, storm arcs, wind particles`

---

## Session 7: P2.B4 — The Storms (Ch.4) — THE MONSTER

**Estimated:** 4-6 hours. Largest session. Consider splitting into 7a (Kristin+respite)
and 7b (Leonardo+Marta) if context gets thin.

**Spec:** Scroll timeline §2 Ch.4a-4d. **Read ALL sub-chapter specs.**

### Sub-chapter Architecture

Ch.4 scroll height maps to 4 sub-chapters:

```typescript
// In onStepProgress('chapter-4', progress):
if (progress < 0.3)       activateSubChapter('4a-kristin');
else if (progress < 0.4)  activateSubChapter('4b-respite');
else if (progress < 0.7)  activateSubChapter('4c-leonardo');
else                       activateSubChapter('4d-marta');
```

Each sub-chapter transition:
1. Swap/reconfigure temporal player (new frames, possibly different fps)
2. Adjust camera
3. Update IPMA warnings
4. Show/hide frontal boundaries
5. Debounce transitions (100ms) to avoid jitter at sub-chapter boundaries

### 4a: Kristin (scroll 0.0-0.3)

- Camera: `[-12, 43]` z5.5 p20
- Synoptic temporal player: hourly MSLP + wind, 8fps, loop
  - All 4 WeatherLayers GL layers active (from P2.A2)
  - `updateWeatherFrame()` per frame tick
- Precipitation blues overlay (PNG crossfade underneath particles)
- IPMA warnings: yellow→orange districts
- Scroll 0.18: Satellite IR crossfades IN, replacing synoptic view
  - 48 hourly frames, 4fps, inverted grayscale
  - IMPORTANT: satellite REPLACES synoptic, not additive (max 6-7 layers)
- Lightning: ScatterplotLayer, yellow #ffd700 stars, brief flash animation
- Annotation: "CICLOGENESE EXPLOSIVA"

### 4b: Respite (scroll 0.3-0.4)

- Static frame: Jan 31 00Z MSLP
- Temporal player paused on single frame
- Side panel: discharge sparklines showing river PEAK LAGS storm by 24-48h
- Text: "O pior já passou? Não."
- Camera holds steady

### 4c: Leonardo (scroll 0.4-0.7)

- Synoptic temporal player: Feb 4-8 hourly (from P1.A1), 8fps
- Same layer stack as 4a but new data window
- IPMA warnings escalate to RED
- Frontal boundary: warm front from `frontal-boundaries.geojson`
  - Red line, 2px, triangle markers every 50km
- Satellite IR: Feb 4-8 Meteosat (from P1.A3)
- Camera pushes to `[-9, 40]` z7

### 4d: Marta (scroll 0.7-1.0)

- Camera: `[-9, 39.5]` z7.5 p30 (tightest of the three)
- Synoptic player: Feb 9-12 hourly
- Frontal boundary: cold front (blue #4169e1, triangle markers)
- Full composite at climax (scroll 0.9):
  ```
  1. Dark basemap (#080c10)
  2. Precipitation field (blues PNGs)
  3. MSLP isobars (ContourLayer 1.5px white)
  4. H/L labels (HighLowLayer)
  5. Wind barbs (GridLayer) — peak moments only
  6. Frontal boundary (MapLibre line layer)
  7. Wind particles (ParticleLayer)
  8. IPMA warnings (choropleth)
  ```
- Max 6-7 active simultaneously. Visual hierarchy: particles on top, precipitation
  beneath, isobars as structure, warnings as context.
- On exit: all layers fade, camera pulls back

### Performance Budget

Ch.4 is the heaviest chapter. Target: 30fps on desktop. If below:
1. First: disable wind barbs (GridLayer)
2. Second: reduce particles to 3000
3. Third: fall back to PNG-only precipitation (no live COG rendering)

### Commit

`P2.B4: chapter 4 three storms — synoptic composite with 4 sub-chapters`

---

## Session 8: P2.B5 + P2.B6 — Rivers (Ch.5) + Consequences (Ch.6)

**Estimated:** 4-5 hours

### Ch.5: Rivers Respond

**Spec:** Scroll timeline §2 Ch.5

- Basemap: terrain + hydro (Portuguese labels, hillshade visible)
- Terrain enabled (exaggeration 1.5, from P2.A4)

**GSAP timeline on enter** (not scroll-driven):

```
0s:   River network appears (rivers-portugal.geojson, width by Strahler) + basin outlines
1.5s: Discharge stations fade in (circle markers, size ∝ peak ratio)
3s:   Camera: Tejo focus [-8.4, 39.4] z9 (3s flyTo)
6s:   Discharge temporal player starts (daily Dec 1→Feb 15, 3fps). Stations pulse.
9s:   Camera: Mondego [-8.4, 40.2] z9 (3s flyTo)
12s:  Camera: Sado [-8.5, 38.5] z9 (3s flyTo)
15s:  Camera: Guadiana [-7.5, 37.8] z9 (3s flyTo)
18s:  Side panel: Observable Plot sparklines per river (5 charts) slide in
22s:  3D discharge columns appear (ColumnLayer from P2.A4). Guadiana towers at 11.5×.
26s:  Camera pulls back to show all columns. Text: "O Guadiana multiplicou por 11.5"
```

Timeline runs at designed pacing. User reads text while camera tours rivers.
On chapter exit: kill timeline, destroy temporal player, cleanup.

**Data:**
```
Rivers:     data/qgis/rivers-portugal.geojson
Stations:   data/qgis/discharge-stations.geojson
Timeseries: data/frontend/discharge-timeseries.json
```

### Ch.6: The Human Cost (4 sub-chapters)

**Spec:** Scroll timeline §2 Ch.6a-6d

- Basemap: aerial hybrid (satellite imagery)
- Terrain enabled
- Intimate camera work (z10-13, p35-45)

**Same pattern as Ch.4:** Scroll selects sub-location, GSAP timeline choreographs layers.

```typescript
// Scroll controls WHICH sub-location:
function handleChapter6SubLocation(progress: number): void {
  const sub =
    progress < 0.23 ? 'coimbra' :
    progress < 0.48 ? 'lisboa' :
    progress < 0.78 ? 'salvaterra' : 'national';

  if (sub !== activeSub) {
    activeTimeline?.kill();
    cleanupSubLocation(activeSub);
    activeSub = sub;
    activeTimeline = buildSubLocationTimeline(sub);
  }
}
```

**6a: Coimbra → enterCoimbra timeline:**
- 0s: Camera flyTo `[-8.43, 40.20]` z10 p35 (3s)
- 1s: Flood extent: EMSR861 + EMSR864 overlap (two PMTiles sources) fade in (2s)
- 3s: Consequence markers appear (typed icons: death, evacuation, damage) (1.5s)

**6b: Lisboa region → enterLisboa timeline:**
- 0s: Camera flyTo `[-9.1, 38.7]` z10 p35 (3s)
- 1s: Setúbal + Sintra flood extents fade in (2s)
- 3s: Consequence markers (1.5s)

**6c: Salvaterra triptych → enterSalvaterra timeline — THE SIGNATURE MOMENT:**
- 0s: Camera flyTo `[-8.75, 39.05]` z11 p40 (3s)
- 2s: monit01 flood extent fades in (#b3d9e8, 40%) — 1.5s
- 4s: monit02 flood extent fades in (#6baed6, 50%) — 1.5s
- 6s: product flood extent fades in (#2471a3, 60%) — 1.5s
- 8s: Flood depth COG overlay fades in (flood-depth palette) — 2s
- 11s: Sentinel-2 before/after slider appears (`@maplibre/maplibre-gl-compare`)
  - Left: before (Jan 6), Right: after (Feb 20)
- 13s: Text: "Em 48 horas, as águas cresceram 58%"

**6d: National pull-back → enterNational timeline:**
- 0s: Camera flyTo `[-8.5, 39.5]` z6.5 p15 (4s)
- 2s: All 42 consequence markers visible (1.5s)
- 4s: Total statistics text

**Data:**
```
Flood extent:  data/flood-extent/emsr861.pmtiles, emsr864.pmtiles, combined.pmtiles
Flood depth:   data/flood-depth/salvaterra-depth-monit01.tif (+ monit02, product)
Sentinel-2:    data/sentinel-2/salvaterra-before-*.tif, salvaterra-after-*.tif
Consequences:  data/consequences/events.geojson
```

### Commit

`P2.B5+B6: chapters 5-6 — rivers with 3D columns + consequences with Salvaterra triptych`

---

## Session 9: P2.B7 + P2.B8 — Reveal (Ch.7) + Exploration (Ch.8-9)

**Estimated:** 2-3 hours

### Ch.7: The Full Picture (Wildfire Reveal)

**Spec:** Scroll timeline §2 Ch.7. Also: `data/colormaps/screenshots/ch7-reveal-test.png`

**THE INTELLECTUAL PUNCHLINE.** Sequential layer build.

**NOTE: Ch.7 is CORRECTLY scroll-driven.** The user controls the pace of the reveal.
Each scroll position adds one layer. The BUILD SEQUENCE IS THE NARRATIVE — the reader
accumulates evidence until the burn scars land and the correlation is undeniable.
This is NOT the same as Ch.2 where scroll was mapping to opacity breakpoints.
Here, scroll = "turn the page to see the next piece of evidence."

| Scroll | Layer added | Opacity | Previous layers |
|--------|------------|---------|-----------------|
| 0.0 | Basin boundaries (gray 0.5px) | 40% | — |
| 0.2 | Precipitation total COG (precip-7day palette) | 60% | Basins → 30% |
| 0.4 | Flood extent (blue #2471a3) | 70% | Precip → 40%, basins → 20% |
| 0.6 | Consequence markers (all 42) | 100% | Flood → 60% |
| 0.8 | **BURN SCARS** (amber #c0631a, 60%) | 60% | Flood stays 60% |
| 0.9 | Hold. Let the spatial correlation sink in. | — | — |

**The test:** If a user needs the text to understand the fire→flood connection, the
visualization has FAILED. The amber burn scars overlapping blue flood areas must be
immediately, viscerally legible.

**Verify against:** `data/colormaps/screenshots/ch7-reveal-test.png` from P1.C2.

- Camera: `[-8.5, 39.5]` z6.5 p10 (flat national overview)
- Basemap: dark (#080c10), no terrain
- Text at 0.8: "Os incêndios de 2024 abriram o caminho às cheias de 2026"

### Ch.8: Analysis

- Static basin risk assessment
- Policy text about flood + fire management
- No temporal player, no animation

### Ch.9: Exploration

- Unlock map interaction (`enableInteraction()` from map-setup.ts)
- Layer toggle panel (checkboxes for major layer groups)
- Geolocation button (MapLibre GeolocateControl)
- Share button: encode viewport state in URL hash
- Text: "Agora explore por si mesmo"

### Commit

`P2.B7+B8: chapter 7 wildfire reveal + chapters 8-9 exploration mode`

---

## Session 10: P2.C1 — End-to-End Integration + Polish

**Estimated:** 3-4 hours

**The QA session.** Scroll Ch.0 → Ch.9 continuously. Fix everything that breaks.

### Checklist

1. **Transitions:** Every chapter enter/exit — no jank, no pop, no flash of wrong basemap
2. **Temporal players:** Enter → starts. Exit → stops. No orphaned rAF loops.
3. **Camera:** flyTo durations feel natural. No sudden jumps between chapters.
4. **Text timing:** Panels appear/disappear in sync with data reveals.
5. **Layer hierarchy:** Max 6-7 layers simultaneously. No muddy composites.
6. **Globe→mercator:** Ch.2→Ch.3 smooth and fast (~1s).
7. **Terrain:** Ch.5 enter → appears. Ch.7 enter → gone.
8. **Performance:** FPS during Ch.4 composite ≥ 30fps on desktop.
9. **Console:** Zero errors. Zero warnings (except acceptable third-party noise).
10. **Memory:** No leaks across multiple chapter enter/exit cycles.

### Performance Targets

| Chapter | Target FPS | Heaviest moment |
|---------|-----------|-----------------|
| Ch.0-1 | 60 | Static layers only |
| Ch.2 | 45+ | Globe + IVT autoplay + particles |
| Ch.3 | 60 | Scroll-driven PNG swap |
| Ch.4 | 30+ | 6-7 layer synoptic composite |
| Ch.5 | 45+ | Terrain + river network + 3D columns |
| Ch.6 | 45+ | Satellite basemap + flood overlays |
| Ch.7 | 60 | Sequential static layer build |

If Ch.4 drops below 30fps:
1. Reduce particles: 5000 → 3000
2. Disable wind barbs (GridLayer)
3. Fall back to PNG precipitation (no live COG render)
4. Reduce isobar update frequency (every 2nd frame)

### Deliverable

A scrollable URL where the entire narrative works end-to-end. Not responsive, not
accessible, not production-polished — but COMPLETE and VIEWABLE.

### Commit

`P2.C1: end-to-end scroll narrative integration and polish`

---

## Track B Definition of Done

- [ ] Ch.0: Ghost flood pulse animates. Hero title renders. Number ticker works.
- [ ] Ch.1: Flood extent fades to 70%. Statistics visible. Fades on exit.
- [ ] Ch.2: Globe + SST + IVT temporal + storm arcs + wind particles. Globe→mercator on exit.
- [ ] Ch.3: Scroll-driven SM with sparklines, wildfire foreshadow at 0.5, percentile at 0.7.
- [ ] Ch.4: 4 sub-chapters. Synoptic composite. Satellite IR crossfade. IPMA escalation. ≥30fps.
- [ ] Ch.5: Terrain + rivers + discharge temporal + 3D columns at 0.8. Guadiana towers.
- [ ] Ch.6: 4 sub-locations. Salvaterra triptych. Flood depth. Before/after slider.
- [ ] Ch.7: Sequential layer build. Burn scars at 0.8. Fire→flood immediately legible.
- [ ] Ch.8-9: Static analysis + unlocked exploration mode.
- [ ] Full scroll Ch.0→Ch.9: no errors, no orphaned layers, no jank.
- [ ] `npm run build` succeeds. Deployed and viewable.

## After Track B

Phase 2 complete. PR `v2/phase-2` → `main`.
Phase 3 (polish, responsive, accessibility, stretch goals) is independent tasks.
