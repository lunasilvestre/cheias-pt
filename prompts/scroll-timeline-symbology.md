# Scroll Timeline & Symbology Specification — cheias.pt v2

**Date:** 2026-02-26
**Status:** DRAFT — for review and approval
**Supersedes:** Phase 1 data-layers prompt (which was engineering without design)
**Inputs:** creative-direction-plan-v2.md, creative-direction-plan.md (v1 chapter detail),
MOTION-ANALYSIS.md, data-catalogue.md, effect-audit.md, refactor-nwp-planetary-computer.md,
current data inventory on disk

---

## 0. Architectural Principle: Scroll ≠ Timeline

The v0 prototype and all previous phase prompts assumed **scroll position drives temporal
playback** — i.e., as the user scrolls, the date advances. This creates two problems:

1. **GPU choking.** Loading a new COG per scroll pixel buries the GPU. Even with
   pre-rendered PNGs, the crossfade-on-scroll pattern creates jank when the user scrolls
   fast through a 77-frame sequence.

2. **Narrative pacing is lost.** A storm's 48-hour drama compressed into "however fast the
   user scrolls" means the viewer can blow past the climax in 200ms. The WeatherWatcher14
   video doesn't scrub — it PLAYS.

**The correct architecture:**

```
SCROLL controls NAVIGATION between chapters (camera, basemap, text, static layers).
CHAPTERS own TEMPORAL PLAYERS that start/play/stop/loop on chapter entry.
```

Concretely:
- Scrollama fires `onStepEnter(chapter)`.
- Chapter entry handler:
  1. Transitions camera (flyTo/easeTo)
  2. Swaps basemap style if needed
  3. Loads static layers (vectors, single-frame rasters)
  4. **Pre-loads temporal frame sequence** (COG URLs or PNG URLs into memory)
  5. When load is complete + camera transition ends: **starts the chapter's temporal player**
- The temporal player runs independently at its own frame rate (2-8 fps depending on chapter).
- When scrolling past a chapter, `onStepExit` stops the temporal player and fades layers out.
- Some chapters have NO temporal player (static layers only).
- Some chapters have a LOOPING temporal player (wind particles loop indefinitely).

**Sub-chapters within a chapter** advance on scroll. A chapter might have 3-4 scroll steps
that change which temporal sequence is playing, which annotation is visible, or which camera
framing is active — but they don't scrub the temporal player.

**Exception: Chapter 3 (soil moisture)** is the ONE chapter where scroll genuinely controls
time, because it's telling the story of slow accumulation over 77 days. The frame rate here
is ~3 days per scroll step (25 steps for 77 days). This works because soil moisture
changes slowly — no jank at 3-day resolution.

---

## 1. Basemap Strategy

The basemap is NOT an afterthought. It changes per chapter to support the visual hierarchy.

| Chapter | Basemap | Rationale |
|---------|---------|-----------|
| Ch.0 (Hook) | **Ultra-dark ocean** — #060e14 ocean, #0a1520 land, no labels, no borders. Faint coastline only. | Maximum drama. Map is almost invisible. |
| Ch.1 (Flash-forward) | **Dark with Portuguese labels** — same dark scheme + Portuguese labels at low opacity. | Context without clutter. |
| Ch.2 (Atlantic/Globe) | **Dark ocean, no land detail** — globe projection, ocean #0a212e, land silhouette only. | Planetary scale. Land is irrelevant. |
| Ch.3 (Soil) | **Muted terrain** — subtle hillshade, no labels, land in muted greens/grays. | Ground-focused. Need to see topography through the data. |
| Ch.4 (Storms) | **Dark synoptic** — very dark, minimal coastlines, national borders as faint lines. | Maximum contrast for weather data. Dark canvas for luminous particles. |
| Ch.5 (Rivers) | **Terrain + hydrography** — hillshade + river network visible through basemap. Portuguese labels. | The story is about water flowing through terrain. |
| Ch.6 (Consequences) | **Aerial/satellite hybrid** — satellite imagery beneath flood extent. Light labels. | Intimacy. The viewer needs to see the ground — fields, towns, roads. |
| Ch.7 (Full picture) | **Dark national overview** — same as Ch.4 but at national scale. | Readability for composite. |
| Ch.8-9 | **Standard dark** — Portuguese labels, moderate detail. | Exploration-ready. |

**Implementation:** Multiple MapLibre style JSONs or a single style with per-chapter
`setLayoutProperty` / `setFilter` calls to show/hide label layers, change land/water
colors, toggle hillshade.

---

## 2. Complete Scroll Timeline

Each chapter below specifies: scroll position, camera, basemap, layers visible, temporal
player state, text panel content, and transitions. Scroll positions are notional (0.0-1.0
within each chapter's scroll height).

---

### CHAPTER 0: THE HOOK — "O Inverno Que Transbordou os Rios"

**Duration:** ~10 seconds of scroll (100vh). Slow. Let the title breathe.

| Scroll | Camera | Layers | Temporal | Text/UI |
|--------|--------|--------|----------|---------|
| 0.0 | `[-15, 35]` z3 p0 b0, globe | None. Black ocean. | — | Hero serif title fades in: *"O Inverno Que Transbordou os Rios"* centered, white, 45px Georgia. |
| 0.3 | Same | Flood extent PMTiles at **3% opacity** — single ghost pulse. Fill #1a5276, no stroke. | — | Subtitle: *"Como três tempestades expuseram a fragilidade de Portugal"* fades in below. |
| 0.5 | Slow zoom to z3.5 (2s easeTo) | Ghost pulse fades to 0%. Back to empty ocean. | — | Number ticker: **226,764 hectares** animates up. |
| 0.8 | Continue zoom toward z4 | — | — | Byline and scroll indicator arrow fade in. |
| 1.0 → Ch.1 | Begin flyTo toward Portugal | — | — | Title fades out. |

**Symbology:**
- Flood extent ghost pulse: `fill-color: #1a5276`, `fill-opacity: 0 → 0.03 → 0` over 2s (GSAP)
- No stroke on ghost pulse (too noisy at this zoom)
- Background: pure dark ocean, #060e14

---

### CHAPTER 1: THE FLASH-FORWARD — "7 de Fevereiro de 2026"

**Duration:** ~12 seconds (120vh). The "before we explain, look at this" moment.

| Scroll | Camera | Layers | Temporal | Text/UI |
|--------|--------|--------|----------|---------|
| 0.0 | `[-8.5, 39.5]` z6.5 p15 b5. flyTo 3s from Ch.0. | Basemap transition to dark+labels. | — | Title: *"7 de Fevereiro de 2026"* |
| 0.2 | Stable | **Flood extent PMTiles** fades in. Fill #2471a3 at 50% opacity, stroke #1a5276 0.5px. | — | — |
| 0.4 | Stable | Full opacity (70%). | — | Text: *"O satélite Sentinel-1 capturou esta imagem..."* |
| 0.6 | Stable | — | — | Statistics appear: *"11 mortes. 69 municípios em calamidade."* |
| 0.8 | Stable | Flood extent starts fading (70% → 20%) | — | *"Para perceber como chegámos aqui, precisamos de voltar ao princípio."* |
| 1.0 → Ch.2 | Begin transition to globe | Flood fades to 0% | — | Text fades. Camera begins pulling out to Atlantic. |

**Symbology:**
- Flood extent: `fill-color: #2471a3`, `fill-opacity: 0.7`, `stroke: #1a5276`, `stroke-width: 0.5`
- Use `combined.pmtiles` source (15,253 features)
- No temporal animation — single static view

---

### CHAPTER 2: THE ATLANTIC ENGINE — "A Energia do Atlântico"

**Duration:** ~25 seconds (250vh). Two beats: SST anomaly, then atmospheric river.

| Scroll | Camera | Layers | Temporal | Text/UI |
|--------|--------|--------|----------|---------|
| 0.0 | `[-25, 35]` z2.8 p0 b0, **globe projection**. flyTo 2.5s. | Basemap: dark ocean, globe. | — | Title: *"A Energia do Atlântico"* |
| 0.1 | Stable globe | **SST anomaly raster** fades in. | — | — |
| 0.2 | Stable | SST at full opacity (80%). | — | Text: *"O inverno trouxe uma energia incomum..."* |
| 0.3 | Slight rotation (bearing 0→5 over 3s) | SST + **storm track arcs** appear. 3 ArcLayer great circles from mid-Atlantic to Iberia. Named labels (Kristin, Leonardo, Marta). | — | — |
| 0.5 | Stable | **IVT scalar field** fades in over SST. Purple/white band showing atmospheric river corridor. ERA5 daily at 0.5° for seasonal context. | **IVT temporal player starts.** 77 daily frames. 2 fps. Loop. | Text: *"...humidade que viajou milhares de quilómetros..."* |
| 0.6 | Stable | IVT + **wind particles** (low density, ~2000). Particles flow along the AR corridor, showing transport direction. White trails on dark ocean. | Particles animate continuously (GPU loop, no frame loading). IVT frames advance behind them. | — |
| 0.8 | Begin slow camera push toward Portugal (easeTo z3.5 over 4s) | IVT intensifies as date approaches January. Particles visibly accelerate in the AR core. | IVT player continues. | *"Três tempestades nomeadas em duas semanas."* |
| 0.9 | Camera push continues | SST fading. IVT crossfade from ERA5 0.5° → **ECMWF HRES 0.1°** (if available for this date range). 10× more detail in the AR structure. | Temporal player switches source. | — |
| 1.0 → Ch.3 | Transition from globe → mercator. Camera continues pushing to Portugal. | Storm arcs and IVT fade. Wind particles dissolve. | Players stop. | Text fades. |

**Symbology:**
- SST anomaly: diverging `blue (#2166ac) → white → red (#b2182b)`, domain [-2°C, +2°C]. `raster-opacity: 0.8`.
- Storm track arcs: `ArcLayer`, `getSourceColor: [255, 100, 100, 180]`, `getTargetColor: [255, 200, 100, 180]`, `getWidth: 2.5`, `greatCircle: true`. White label per storm.
- IVT field: sequential `transparent → #4a1486 (purple) → #807dba → #bcbddc → white`. Domain [0, 800 kg/m/s]. `raster-opacity: 0.7`.
- Wind particles: `ParticleLayer`, `numParticles: 2000`, `color: [255, 255, 255, 160]`, `width: 1.5`, `maxAge: 80`. Low density for Atlantic scale.

**Data temporal resolution:** IVT at daily is adequate here — we're showing the SEASONAL pattern, not a storm's hourly evolution. The "river builds over weeks" narrative works at daily cadence.

**Data needed:**
- `data/cog/sst/*.tif` (66 daily, READY)
- `data/cog/ivt/*.tif` (77 daily at 0.5°, READY)
- `data/cog/ecmwf-hres/*_ivt.tif` (17 at 0.1°, Jan 25-Feb 10, READY)
- `data/qgis/storm-tracks.geojson` (READY)
- Wind U/V COGs for particle source (any single timestep for ambient flow, READY)

---

### CHAPTER 3: THE SPONGE FILLS — "O Solo Encharca"

**Duration:** ~35 seconds (350vh). The SLOWEST chapter. Each scroll step = ~3 days.

**THIS IS THE ONE CHAPTER WHERE SCROLL = TIME.** 77 soil moisture frames mapped to scroll
progress. This works because SM changes slowly — no GPU choking at ~3 days per step.

| Scroll | Camera | Layers | Temporal | Text/UI |
|--------|--------|--------|----------|---------|
| 0.0 | `[-8.3, 39.8]` z7 p20 b-5. easeTo 2s. **Mercator.** | Basemap: muted terrain with hillshade. | SM animation: frame 1 (Dec 1). | Title: *"O Solo Encharca"* |
| 0.05-0.3 | Stable | **Soil moisture raster** at 80% opacity. Scroll drives frames 1→23 (Dec 1 → Dec 23). | SM advances with scroll. ~3 days per step. | Date counter in corner: "1 Dezembro" → "23 Dezembro". Basin sparklines appear in side panel. |
| 0.3 | Stable | SM shows first green/blue patches in the north. | Frame ~23 | *"Semanas de chuva persistente..."* |
| 0.3-0.5 | Stable | SM deepens. Blue spreads south. | Frames 23→38 (Dec 23 → Jan 7) | Date continues advancing. Sparkline for Minho-Lima reaches 0.49 → annotation pulse. |
| 0.5 | Stable | **Wildfire burn scars** fade in at 15% opacity beneath SM. Amber/orange fill. Subtle foreshadowing — the viewer may not consciously notice. | Frame ~38 | *Soft annotation: "Cicatrizes dos incêndios de 2024"* if visible. |
| 0.5-0.7 | Stable | SM now deep blue across northern and central Portugal. | Frames 38→53 (Jan 7 → Jan 22) | *"O solo já não tinha para onde mandar a água."* |
| 0.7 | Stable | Percentile overlay pulses briefly: "**Percentil 98**" annotation. | Frame ~53 (Jan 22) | *"Mais húmido que 98% de todos os dias desde 1991."* |
| 0.7-0.9 | Stable | SM saturated everywhere. Near-uniform deep blue. | Frames 53→65 (Jan 22 → Jan 28) | Text shifts to foreshadowing: *"E foi quando Kristin chegou."* |
| 0.9-1.0 | Camera begins pulling back (z7 → z6). SM fades 80% → 30%. | **Precipitation layer** fades in beneath SM at 40% opacity. The viewer sees the first rain arriving OVER the saturated ground. | SM stops advancing. Precip shows Jan 27-28 (static, two heaviest days). | Transition text: *"O que veio a seguir..."* |
| 1.0 → Ch.4 | Camera continues pulling back to synoptic scale. | SM fades out. Precipitation fades out. | — | — |

**Symbology:**
- Soil moisture: brown-to-blue sequential. `#8B6914 → #B8860B → #7A9A6E → #4A90A4 → #2E86AB → #1B4965`. Domain [0.1, 0.5 m³/m³]. Already rendered as 77 PNGs (700×1060, READY).
- Wildfire burn scars: `fill-color: #c0631a`, `fill-opacity: 0.15`, `stroke: #8b4513`, `stroke-opacity: 0.3`, `stroke-width: 0.5`. Source: `data/qgis/EFFIS-burn-scars.pmtiles`.
- Basin sparklines: Observable Plot in HTML side panel. Simple line chart, ~150×40px per basin.
- Date counter: HTML overlay, 14px Inter, top-right corner.

**Scroll-time mapping for SM:**
```
scrollProgress 0.0 → frame 0  (2025-12-01)
scrollProgress 0.5 → frame 38 (2026-01-07)
scrollProgress 0.9 → frame 65 (2026-01-28)
scrollProgress 1.0 → frame 70 (2026-02-02) — but we've started transitioning
```
Use `Math.floor(scrollProgress * 0.9 * 76)` to map scroll → frame index.
Load PNGs, not COGs. The 77 SM PNGs are 11MB total — preload all on chapter approach.

**Data needed:**
- `data/raster-frames/soil-moisture/*.png` (77, READY)
- `data/qgis/EFFIS-burn-scars.pmtiles` (READY, check path)
- `data/frontend/discharge-timeseries.json` (for sparklines, READY)
- Precipitation PNGs for the Jan 27-28 crossfade (READY but need re-render — see data gaps below)

**NEW DATA NEEDED: Soil moisture percentile COGs.** Without percentiles, "98th percentile"
is an unsourced claim. Need ERA5-Land soil moisture climatology (1991-2020 monthly means)
to compute daily percentile. This is a derived product — see §4.

---

### CHAPTER 4: THREE STORMS IN TWO WEEKS — "Três Tempestades em Duas Semanas"

**Duration:** ~30 seconds (300vh). The FASTEST chapter. 4 sub-chapters with different
temporal players and camera framings. The CLIMAX of the narrative.

**Architecture:** 4 scroll-triggered sub-chapters (4a-4d). Each sub-chapter has its own
temporal player that starts on entry. The scroll moves between sub-chapters; the temporal
player runs independently within each.

#### Sub-chapter 4a: KRISTIN — "Kristin"
**Scroll 0.0-0.3**

| Scroll | Camera | Layers | Temporal | Text/UI |
|--------|--------|--------|----------|---------|
| 0.0 | `[-10, 40]` z5.5 p25 b10. flyTo 2s. | Basemap: dark synoptic. | — | Title: *"Kristin"* with date "28 Janeiro 2026" |
| 0.05 | Stable | **MSLP isobars** appear (WeatherLayers GL ContourLayer). White 1.5px, 4hPa interval. **H/L markers** (HighLowLayer). | **Synoptic temporal player starts.** MSLP + wind COGs. Jan 26 00Z → Jan 30 00Z. Hourly. **8 fps** (12 seconds for 96 hours). | — |
| 0.08 | Stable | **Wind particles** activate (ParticleLayer). 5000 particles, white/cyan trails, speed-colored. | Particles flow through the evolving wind field. Data source updates with temporal player. | *"Possivelmente a tempestade mais forte desde que há registos."* |
| 0.12 | Stable | **Precipitation field** fades in beneath particles. Blue wash, gaussian-blurred. Daily resolution (4 frames for 4 days). | Precip crossfades at matching timestamps. | — |
| 0.15 | Stable | **IPMA warnings** district choropleth fades in. Yellow → orange during Kristin peak. | Warnings advance in sync with temporal player date. | — |
| 0.18 | Camera push toward `[-9, 40]` z7 p30. | **Satellite IR** crossfades in, replacing precip field. Inverted grayscale — bright comma cloud. | **Satellite temporal player takes over.** 48 hourly IR frames. 4 fps. Shows cloud spinning. | *"CICLOGENESE EXPLOSIVA"* annotation appears near cloud comma head. |
| 0.22 | Stable | Satellite + wind particles composite. Particles flow OVER the cloud imagery. | Satellite player continues. "STING JET" annotation appears near dry slot. | — |
| 0.25 | Stable | **Lightning flashes** — yellow ScatterplotLayer stars, 262 points. Appear in bursts timed to frontal passage. | Lightning flashes timed to satellite frames. | — |
| 0.28 | Camera pulls back to z6. | Satellite fading. Synoptic (isobars + particles) returns. Storm passing. Isobars widening (filling). | Temporal player reaching Jan 29-30. System moving NE. | *"Kristin passou. Mas os rios mal tinham começado a baixar."* |

**Symbology (4a):**
- MSLP isobars: `ContourLayer`, `interval: 400` (4hPa), `width: 1.5`, `color: [255, 255, 255, 220]`
- H/L markers: `HighLowLayer`, `radius: 500000`. L=red text, H=blue text, ~18px font.
- Wind particles: `ParticleLayer`, `numParticles: 5000`, `maxAge: 100`, `speedFactor: 0.5`, `width: 2`, `color: [255, 255, 255, 200]`. Speed-based color: calm=green, moderate=yellow, strong=magenta/white.
- Precipitation: Blue raster wash. `transparent → #b3d9e8 → #6baed6 → #3182bd → #08519c`. Alpha ∝ intensity. Gaussian blur σ=3.
- Satellite IR: Inverted grayscale. DN 0-255 mapped to white (cold cloud) → black (warm surface). Contrast stretch on 80-255 range.
- Lightning: `ScatterplotLayer`, `getRadius: 3000`, `getFillColor: [255, 255, 0, 200]`, flicker animation (opacity 0→1→0 over 300ms).
- IPMA warnings: District polygons, `fill-color` interpolated yellow `#ffd700` → orange `#ff8c00` → red `#dc143c` based on warning level.
- Annotations: White text, 16px Inter Bold, slight text-shadow. Positioned via `map.project()` at geographic coordinates.

**Temporal player spec (Kristin):**
- Source: MSLP + wind-u + wind-v COGs at hourly for Jan 26-30 (96 frames)
- Frame rate: 8 fps → 12 seconds for the full storm passage
- Satellite: separate player, 48 frames at 4 fps → 12 seconds for Jan 27-28
- Pre-load strategy: load all 96 MSLP COGs + 48 IR COGs on chapter approach (~30MB total). This is the heaviest load. Start preloading when user enters Ch.3.

#### Sub-chapter 4b: THE RESPITE — "A pausa que não foi"
**Scroll 0.3-0.45**

| Scroll | Camera | Layers | Temporal | Text/UI |
|--------|--------|--------|----------|---------|
| 0.30 | `[-8.5, 39.5]` z7 p20 b0. easeTo 1.5s. | Synoptic view calms. Isobars spread. Warnings drop to yellow. | **Temporal player pauses** at Jan 31. Static synoptic frame. | *"A pausa que não foi"* |
| 0.35 | Stable | **Discharge sparklines** appear in side panel showing rivers STILL RISING even though rain has stopped. Lag effect. | — (static) | *"Antes que os rios baixassem de Kristin..."* |
| 0.40 | Stable | IPMA warnings briefly green (no alerts). But discharge lines haven't peaked yet. | — | *"...Leonardo já se formava no Atlântico."* |

**Symbology (4b):**
- Synoptic view: Same layers as 4a but frozen at Jan 31 00Z. Calm pattern.
- Discharge sparklines: Observable Plot, 200×60px, red threshold line at Q90.

#### Sub-chapter 4c: LEONARDO — "Leonardo"
**Scroll 0.45-0.70**

| Scroll | Camera | Layers | Temporal | Text/UI |
|--------|--------|--------|----------|---------|
| 0.45 | `[-10, 40]` z5.5 p25 b-5. flyTo 2s. | Return to synoptic scale. | **Synoptic player restarts.** Feb 4 00Z → Feb 8 00Z. 6-hourly (16 frames). 4 fps. | *"Leonardo"* with date "5 Fevereiro 2026" |
| 0.50 | Stable | Isobars tightening. New low forming SW of Iberia. Wind particles accelerating. | Player advances. | *"...despejando o equivalente a três dias de chuva em 24 horas."* |
| 0.55 | Camera push to Portugal z7. | **Precipitation field** dominant. Blues intensifying. | — | IPMA warnings escalating: orange → **RED**. |
| 0.60 | Stable | Wind particles + precip composite. Rain bands sweeping SW→NE. | Player reaching Feb 6-7 peak. | — |
| 0.65 | Stable | Satellite IR for Leonardo (IF available — depends on Meteosat fetch). | Switch to satellite player if available. | *"CICLOGENESE EXPLOSIVA"* — second occurrence for impact. |

**Temporal player spec (Leonardo):**
- Source: MSLP + wind COGs at 6-hourly for Feb 4-8 (16 frames)
- Frame rate: 4 fps → 4 seconds for the storm
- **TEMPORAL DENSITY GAP:** Only 6-hourly for Leonardo vs hourly for Kristin. This makes
  Leonardo's animation visibly choppier. See §4 for resolution.

#### Sub-chapter 4d: MARTA — "Marta"
**Scroll 0.70-0.90**

| Scroll | Camera | Layers | Temporal | Text/UI |
|--------|--------|--------|----------|---------|
| 0.70 | `[-8, 39]` z8 p30 b5. easeTo 1.5s. **Basin scale.** | Tighter view on central Portugal. | **Synoptic player:** Feb 9 00Z → Feb 12 00Z. 6-hourly. 4 fps. | *"Marta"* with date "10 Fevereiro 2026" |
| 0.75 | Stable | All layers composited: isobars + particles + precipitation + IPMA warnings (all red). The map is SATURATED with data — deliberate overload. | Player advances. | *"Na zona de Grazalema, mais de 500mm num único dia."* |
| 0.80 | Stable | **Frontal boundary** visible (FrontLayer or MapLibre line). Cold front sweeping through. Blue triangles. | — | — |
| 0.85 | Camera pulling back to z6 | Layers beginning to fade. Storm passing. | Player reaching Feb 12. | *"Em duas semanas, Portugal recebeu chuva suficiente para um ano inteiro."* |
| 0.90-1.0 | Transition toward river basins | All storm layers fade. | All players stop. | Transition to Ch.5. |

**Symbology (4d):**
- Same as 4a/4c but at tighter scale (z8). Denser particles, wider isobars (more pixels per contour).
- Frontal boundary: `LineLayer`, cold front blue `#4169e1`, 2px, with triangle markers every 50km along line direction. Warm front red `#dc143c` with semicircle markers. Source: `data/qgis/frontal-boundaries.geojson`.

**Full layer stack for Ch.4 climax (when all active simultaneously):**
```
Bottom → Top:
1. Dark synoptic basemap
2. Precipitation field (blue wash, 50% opacity, gaussian blur)
3. MSLP isobars (ContourLayer, white 1.5px)
4. H/L pressure labels (HighLowLayer)
5. Frontal boundaries (FrontLayer or LineLayer, blue/red)
6. IPMA warning choropleth (district fill, 30% opacity)
7. Wind particles (ParticleLayer, 5000 particles, white/colored trails)
8. Lightning flashes (ScatterplotLayer, yellow, timed bursts)
9. Satellite IR (when active — replaces precipitation, 100% opacity)
10. Annotations (HTML overlay — storm names, meteorological labels)
```

**Visual hierarchy rule:** MAX 6 layers visible simultaneously. When satellite IR is active,
precipitation and IPMA warnings fade out. When synoptic is active, satellite fades.
Particles are always on top. The viewer should never feel "data vomit."

---

### CHAPTER 5: THE RIVERS RESPOND — "Os Rios Respondem"

**Duration:** ~25 seconds (250vh). Medium-slow. Sequential focus on 4 rivers.

| Scroll | Camera | Layers | Temporal | Text/UI |
|--------|--------|--------|----------|---------|
| 0.0 | `[-8.4, 39.6]` z7 p35 b-10. flyTo 2s. | Basemap: terrain + hydrography. **Enable MapLibre terrain** with exaggeration 1.5. | — | Title: *"Os Rios Respondem"* |
| 0.1 | Stable | **River network** from GeoJSON. Blue lines, width 1-3px by Strahler order. **Discharge station markers** — circles sized by current discharge. | **Discharge temporal player starts.** Daily. Dec 1 → Feb 15. 3 fps. Markers grow as discharge rises. | — |
| 0.2 | `[-8.4, 39.4]` z8 (Tejo focus) | Tejo river highlighted. Other rivers dim. **Discharge sparkline** for Tejo in side panel. Red threshold line. | Player continues. Tejo station marker PULSES when it crosses Q90. | *"O Tejo atingiu o nível mais alto em quase 30 anos."* |
| 0.35 | `[-8.43, 40.21]` z8 (Mondego focus) | Mondego highlighted. | — | *"Em Coimbra, o dique do Mondego cedeu."* |
| 0.50 | `[-8.8, 38.5]` z8 (Sado focus) | Sado highlighted. | — | *"O Sado voltou a valores de 1989."* |
| 0.65 | `[-7.5, 38.0]` z7.5 (Guadiana focus) | Guadiana highlighted. Its marker is HUGE — 11.5× amplification. | — | *"O Guadiana multiplicou o caudal por 11.5."* |
| 0.80 | Pull back to `[-8, 39]` z7. All rivers visible. | **3D columns** appear at discharge stations. Height = peak discharge / baseline. Color = red if >5× amplification. | Player loops on peak dates (Feb 6-8). Columns at max height. | *"Todos os grandes rios portugueses excederam os limiares."* |
| 1.0 → Ch.6 | Camera begins descent toward Salvaterra. Terrain intensifies. | Columns fade. River width returns to normal. | Player stops. | — |

**Symbology:**
- Rivers: `line-color: #2980b9`, `line-width: ["interpolate", ["linear"], ["get", "strahler"], 1, 0.5, 6, 3]`
- Discharge stations: `ScatterplotLayer`, `getRadius: d => Math.max(3000, d.discharge_ratio * 2000)`. Color: blue (#2980b9) if normal, orange (#f39c12) if elevated, red (#e74c3c) if extreme.
- 3D columns: `ColumnLayer`, `radius: 4000`, `getElevation: d => d.peak_ratio * 5000`, `getFillColor: d => d.peak_ratio > 5 ? [231, 76, 60, 200] : [52, 152, 219, 200]`, `extruded: true`.
- Sparklines: Observable Plot in side panel. X = date, Y = m³/s. Red horizontal line at Q90 threshold.
- Terrain: MapLibre `raster-dem` source, `exaggeration: 1.5`.

**Data needed:**
- `data/frontend/discharge-timeseries.json` (READY)
- `data/qgis/discharge-stations.geojson` (READY)
- `data/qgis/rivers-portugal.geojson` (READY)
- `data/qgis/basins-portugal.geojson` (READY)
- MapLibre terrain tiles (public DEM)

---

### CHAPTER 6: THE HUMAN COST — "O Custo Humano"

**Duration:** ~30 seconds (300vh). 4 sub-chapters. Intimate camera work.

#### 6a: ALCÁCER DO SAL
**Scroll 0.0-0.25**

| Scroll | Camera | Layers | Temporal | Text/UI |
|--------|--------|--------|----------|---------|
| 0.0 | `[-8.52, 38.37]` z12 p40 b15. flyTo 2.5s. | Basemap: aerial/satellite. **Terrain on** (exaggeration 1.2). | — | *"Alcácer do Sal"* |
| 0.1 | Stable | **Flood extent** (EMSR864 relevant AOI) fades in. Blue fill 60% over terrain/satellite. | — | *"A água do Sado subiu dois metros no centro da vila."* |
| 0.2 | Stable | **Consequence markers** drop in. Icon by type: death=red pin, evacuation=orange, infrastructure=purple. | — | Individual impact descriptions. |

#### 6b: COIMBRA
**Scroll 0.25-0.50**

| Scroll | Camera | Layers | Text |
|--------|--------|--------|------|
| 0.25 | `[-8.43, 40.21]` z11 p35 b-10. flyTo 2.5s. | EMSR861 (Kristin) extent in lighter blue. EMSR864 (Leonardo) in darker blue. OVERLAP visible. | *"Coimbra: duas cheias em dez dias."* |
| 0.35 | Stable | Both extents visible. The overlap tells the story — flooded, dried, flooded AGAIN. | *"3.000 pessoas evacuadas numa noite."* |

#### 6c: SALVATERRA DE MAGOS — The Temporal Triptych
**Scroll 0.50-0.80**

| Scroll | Camera | Layers | Temporal | Text/UI |
|--------|--------|--------|----------|---------|
| 0.50 | `[-8.85, 39.07]` z10 p35 b5. flyTo 2s. | Basemap: satellite/aerial for Tejo floodplain context. | — | *"Salvaterra de Magos"* |
| 0.55 | Stable | **Salvaterra temporal triptych.** Date 1: Feb 6. Blue fill from `salvaterra_temporal.pmtiles`, filtered to date 1. | Static — date 1 only. | *"6 de Fevereiro: 31.000 hectares."* |
| 0.60 | Stable | Date 2 ADDED (not replacing). Feb 7 extent in slightly darker blue. Growth visible. | — | *"7 de Fevereiro: 42.000 hectares. +35% em 24 horas."* |
| 0.65 | Stable | Date 3 ADDED. Feb 8. Deepest blue. Maximum extent. | — | *"8 de Fevereiro: 49.000 hectares. +58% em 48 horas."* |
| 0.70 | Stable | **Flood depth COG** overlaid on extent. Blue→red colormap (0m → 7m+). Shows WHERE the water is deepest. River channel = dark red. | — | *"Até 9.6 metros de profundidade nos leitos."* |
| 0.75 | Stable | **Sentinel-2 before/after** (IF acquired). Split-screen comparison using `maplibre-gl-compare`. Before: green fields. After: blue water. | — | *"O que o satélite viu."* |

**Symbology (6c):**
- Temporal triptych: Three shades of blue, additively layered:
  - Date 1: `fill-color: #a6cee3`, `fill-opacity: 0.5`
  - Date 2: `fill-color: #2171b5`, `fill-opacity: 0.5`
  - Date 3: `fill-color: #08306b`, `fill-opacity: 0.5`
  - Overlap creates darker blues — the darker the area, the longer it was flooded.
- Flood depth: `transparent → #deebf7 → #9ecae1 → #4292c6 → #2171b5 → #084594 → #8b0000`. Domain [0, 7m]. `raster-opacity: 0.7`.
- Before/after: `maplibre-gl-compare` widget, vertical slider. Full-bleed satellite imagery.

#### 6d: THE COUNT
**Scroll 0.80-1.0**

| Scroll | Camera | Layers | Text |
|--------|--------|--------|------|
| 0.80 | Pull back to `[-8, 39]` z7 p25 b0. | **All 42 consequence markers** visible nationally. | *"O resultado: 11 mortes."* |
| 0.90 | Stable | Markers clustered by type with count labels. | Statistics: evacuations, infrastructure, agricultural losses. |

---

### CHAPTER 7: THE FULL PICTURE — "A Cadeia Causal"

**Duration:** ~20 seconds (200vh). Slow reveal. The synthesis.

| Scroll | Camera | Layers | Text/UI |
|--------|--------|--------|---------|
| 0.0 | `[-8.2, 39.5]` z6.5 p15 b0. flyTo 2s. | Basemap: dark national overview. | *"A Cadeia Causal"* |
| 0.2 | Stable | Layer 1: **Basins** colored by precondition score (risk composite). | *"Solo saturado."* |
| 0.35 | Stable | Layer 2: **Precipitation accumulation** (total Jan-Feb) as raster. | *"Chuva intensa."* |
| 0.5 | Stable | Layer 3: **Flood extent** (full national, blue). | *"Rios que ultrapassaram os limites."* |
| 0.65 | Stable | Layer 4: **Consequence markers** (all 42). | *"11 mortes. 69 municípios em calamidade."* |
| 0.8 | Stable | **THE REVEAL: Wildfire burn scars** fade in. Amber/orange. The spatial correlation with flooding is immediately visible. | *"E por baixo de tudo, os incêndios do verão anterior que tinham arrancado a vegetação que segurava as encostas."* |
| 0.9 | Stable | Full composite visible. | *"Cada peça sozinha era gerível. Juntas, criaram uma catástrofe."* |

**Symbology (Ch.7 THE REVEAL):**
- Wildfire burn scars: `fill-color: #c0631a`, `fill-opacity: 0.6`, `stroke: #8b4513`, `stroke-width: 1`. Source: EFFIS PMTiles.
- This is the intellectually original moment. The amber burn scars overlapping with blue flood extent creates a visual that communicates "fire → flood" without needing to explain the hydrology. The COLORS tell the story.
- **Max 3 layers at full opacity.** Use progressive build: each new layer fades to 50% the previous one. Final state: basins 20%, precip 30%, flood 50%, consequences 80%, burn scars 60%.

---

### CHAPTERS 8-9: THE ANALYSIS + EXPLORATION

**Ch.8 (scroll 0.0-1.0):** Policy analysis text with basin risk map. Static. No temporal player.

**Ch.9 (scroll 0.0):** Enable map interaction. Layer toggles, geolocation, click-to-explore.
This is the exploration mode reward for completing the narrative.

---

## 3. Data Gaps & Derived Products

### Critical Temporal Density Gap

| Data | Kristin (Jan 26-30) | Leonardo (Feb 4-8) | Marta (Feb 9-12) | Impact |
|------|--------------------|--------------------|-------------------|--------|
| MSLP | **HOURLY** (120 frames) | 6-hourly (16 frames) | 6-hourly (12 frames) | Leonardo/Marta animate at 1/6th the smoothness of Kristin |
| Wind U/V | **HOURLY** (120 frames) | 6-hourly (16 frames) | 6-hourly (12 frames) | Same. Particle flow looks choppy. |
| Satellite IR | **HOURLY** (48 frames) | **NONE** | **NONE** | Leonardo/Marta have no cloud imagery at all |
| Precipitation | Daily (4 frames) | Daily (4 frames) | Daily (3 frames) | Inadequate for all storms — can't show rain bands sweeping |
| IVT | Daily (5 frames) | Daily (4 frames) | Daily (3 frames) | Can't show AR pulsing for any storm |

**Resolution: Fetch hourly ERA5 for Leonardo/Marta periods.** The existing fetch pipeline
already produced hourly data for Jan 26-30. Re-run for Feb 4-12. This gives Leonardo and
Marta the same temporal density as Kristin.

**Resolution: Fetch hourly ERA5 precipitation.** Daily is fine for Ch.3 (slow buildup) but
inadequate for Ch.4 (storm animation). Need hourly precip for the 3 storm windows. This
shows rain bands sweeping across in the temporal player.

**Resolution: Extended Meteosat for Leonardo/Marta.** Already identified. Without this,
Ch.4 sub-chapters 4c and 4d have no satellite view — a significant narrative gap.

**Resolution: IVT temporal density.** For Ch.2, daily is fine (seasonal pattern). For Ch.4,
need at least 6-hourly IVT to show the AR pulsing. ERA5 pressure-level data can provide
this — compute IVT from u/v/q at multiple levels.

### Derived Products That Add Analytical Value

These are the intermediary files that demonstrate geospatial mastery:

**1. Accumulated Precipitation Anomaly (% of 30-year mean)**
- Input: Daily precip COGs + ERA5 1991-2020 monthly climatology (fetch from CDS)
- Output: 77 daily COGs showing departure from normal (100% = normal, 400% = 4× normal)
- Colormap: white (100%) → yellow (200%) → orange (300%) → red (400%+)
- Chapter: Ch.3 alternative/overlay to absolute precipitation
- Impact: "400% of normal" is more powerful than "30mm"

**2. Soil Moisture Percentile (vs 1991-2020 distribution)**
- Input: Daily SM COGs + ERA5-Land SM climatology (monthly distribution)
- Output: 77 daily COGs showing percentile rank (0-100th)
- Colormap: green (0-50th) → yellow (50-75th) → orange (75-95th) → red (95-100th)
- Chapter: Ch.3 annotation/overlay
- Impact: "98th percentile" becomes a verifiable claim, not an assertion

**3. Storm Track LineStrings with Pressure Annotations**
- Input: MSLP COGs (hourly for Kristin, 6-hourly for others)
- Output: GeoJSON FeatureCollection with 3 LineStrings, each vertex has min_pressure property
- Processing: Find MSLP minimum position per timestep, connect into path
- Chapter: Ch.2 storm arcs (replaces hand-drawn tracks) + Ch.4 annotation
- Impact: Standard hurricane-track format. Universally understood.

**4. NDWI Difference for Sentinel-2 Before/After**
- Input: Sentinel-2 before + after scenes (B03 Green, B08 NIR)
- Output: NDWI difference COG + styled PNG
- Processing: NDWI = (Green - NIR) / (Green + NIR), compute for both dates, subtract
- Chapter: Ch.6c overlay (the science version of before/after)
- Impact: A portfolio piece within a portfolio piece. Shows spectral index expertise.

**5. Precipitation Accumulation (running 7-day sum)**
- Input: Daily precip COGs
- Output: 71 COGs showing rolling 7-day accumulated precipitation
- Colormap: white → blue → dark blue → purple (0 → 200mm)
- Chapter: Ch.4 alternative to daily rate — shows the CUMULATIVE impact
- Impact: "150mm in 7 days" integrates the multi-storm narrative better than daily snapshots

---

## 4. Review: Creative Direction Plan v2 — Completeness Assessment

### What's Strong and Should Be Kept

1. **The 7-chapter narrative arc** — proven structure, emotionally paced, each chapter earns its right to exist.
2. **WeatherLayers GL integration** — correctly identifies ParticleLayer, ContourLayer, GridLayer, HighLowLayer as replacing custom implementations. This is the right call.
3. **IVT as scalar field, not TripsLayer** — correct. The atmospheric river IS a broad flux structure, not a single path.
4. **Globe projection for Ch.2** — MapLibre v5 globe is the right tool. Planetary scale demands it.
5. **The wildfire reveal in Ch.7** — the intellectual original. Keep it exactly as specified.
6. **Vanilla TypeScript** — right decision for a scrollytelling piece. No React overhead.

### What's Missing or Underdeveloped

1. **No scroll timeline.** The plan specifies chapter camera positions and layer names but never describes WHEN layers appear WITHIN a chapter, how temporal players work, or what the viewer sees at scroll position 0.4 in Chapter 3. This document fills that gap.

2. **No basemap strategy.** The plan mentions `#0a212e` background but never addresses per-chapter basemap changes, label language (Portuguese!), or visual hierarchy between data and base.

3. **No temporal player architecture.** The plan assumes scroll = time, which creates the GPU choking problem Nelson identified. The correct pattern (scroll navigates, chapters own temporal players) isn't described anywhere.

4. **No derived products.** The plan lists raw data (COGs) but not analytical products (anomalies, percentiles, accumulations). The science lives in the derivatives, not the raw data.

5. **Chapter 4 sub-chapter choreography is vague.** The plan says "4a-4d" but doesn't specify which layers are on/off per sub-chapter, when satellite replaces synoptic, or how the visual hierarchy prevents data overload.

6. **The "hourly for Kristin, 6-hourly for others" asymmetry isn't flagged.** This creates a visible quality difference between the three storms' animations.

7. **No colormap specification.** Each layer's colormap is hand-waved ("blues", "inverted grayscale"). The exact color stops, domain ranges, and opacity curves aren't defined — and these ARE the cartographic design.

8. **Temperature field beneath isobars.** Listed as Phase 3 but it's actually essential for the synoptic view in Ch.4. Without it, the warm/cold front visualization is missing the most recognizable feature from the WeatherWatcher14 video (the red/blue temperature field UNDER the isobars). Should be Phase 2.

9. **Planetary Computer NWP decision isn't integrated.** The `refactor-nwp-planetary-computer.md` proposes replacing the ERA5 pipeline with Met Office Global 10km from Microsoft Planetary Computer. This is a better STAC showcase BUT it's a lateral move — the existing ERA5 data works, and replacing it adds risk without narrative benefit. The right use of Planetary Computer is as a COMPLEMENTARY source: keep ERA5 as the reanalysis ground truth, add Met Office for the STAC demo, and compare them in a notebook. Don't replace a working pipeline.

### What Should Change

1. **Add temperature field to Phase 2** (currently Phase 3).
2. **Add hourly ERA5 fetch for Leonardo/Marta** to data pipeline.
3. **Add derived products** (anomalies, percentiles, storm tracks) to data pipeline.
4. **Replace the Phase 1/2 boundary** with a design-first approach: Phase 1 = data + derived products + basemap design. Phase 2 = rendering + temporal players + scroll choreography.
5. **Add explicit pre-load strategy** for COG-heavy chapters (Ch.4 needs ~30MB preloaded).

---

## 5. Review: Planetary Computer NWP Refactor

The `refactor-nwp-planetary-computer.md` proposes a sound technical approach:
- `pystac-client` + `planetary-computer` for STAC-based discovery
- Met Office Global Deterministic 10km from Microsoft Planetary Computer
- 0.09° resolution (comparable to ECMWF HRES 0.1°)
- Near-surface variables: MSLP, 10m wind u/v, gusts, precip, temp
- Pressure-level collection for jet stream visualization
- No auth needed for data access (signed URLs via `planetary-computer` package)

**Assessment:**

The technology choice is sound for a portfolio demonstration of STAC skills. However:

1. **Don't replace ERA5. Add alongside it.** ERA5 is reanalysis (best estimate of what
   happened). Met Office is forecast (what the model predicted). Both are valuable.
   ERA5 is the ground truth for the narrative. Met Office demonstrates the STAC pipeline.

2. **The comparison notebook is the real value.** ERA5 vs Met Office for Kristin peak is a
   legitimate scientific analysis that shows you understand the difference between reanalysis
   and forecast data. This is DevSeed-level meteorological literacy.

3. **Met Office pressure-level data (250 hPa wind) is the genuine missing piece.** ERA5
   doesn't easily give us jet stream visualization at the quality level of the
   WeatherWatcher14 video. Met Office pressure-level collection could fill this gap for
   Ch.2 (globe view with jet stream).

4. **The `-mo` suffix naming convention is correct.** Keep both datasets parallel.

**Recommendation:** Execute the Planetary Computer refactor as a Phase 1 task, but scope
it to: (a) fetch Met Office data for the Kristin comparison, (b) fetch 250 hPa wind for
jet stream visualization, (c) build the comparison notebook. Don't re-process all storm
periods — that's duplicating effort.

---

## 6. Revised Phase Structure

Based on this scroll timeline, the creative direction review, and the data gaps analysis:

### Phase 1: Data Foundation + Derived Products + Design Decisions
*The science and the taste. No rendering code.*

**Track A: Missing Hourly Data**
- Fetch ERA5 hourly MSLP + wind U/V for Leonardo period (Feb 4-8)
- Fetch ERA5 hourly MSLP + wind U/V for Marta period (Feb 9-12)
- Fetch ERA5 hourly precipitation for all 3 storm windows
- Fetch extended Meteosat IR for Leonardo + Marta
- Fetch Sentinel-2 before/after via Earth Search STAC

**Track B: Derived Analytical Products**
- Compute automated storm track LineStrings from MSLP minima
- Compute accumulated precipitation anomaly (requires climatology fetch from CDS)
- Compute soil moisture percentile (requires ERA5-Land climatology)
- Compute running 7-day precipitation accumulation
- Extract flood depth COGs from CEMS
- Draw frontal boundary GeoJSONs (manual meteorological analysis)
- Compute NDWI difference from Sentinel-2 (after acquisition)

**Track C: Cartographic Design**
- Design per-chapter basemap styles (test in MapTiler/Maputnik)
- Define complete colormap palette (all layers, all chapters) — perceptually uniform, colorblind-safe
- Test colormaps against basemaps in QGIS before any code
- Decide on Portuguese label set and typography
- Create visual hierarchy mockups for Ch.4 layer stacking
- OPTIONAL: Planetary Computer Met Office comparison notebook

### Phase 2: Rendering + Temporal Players + Scroll Choreography
*The engineering, guided by Phase 1 design decisions.*

**Track A: Core Rendering Pipeline**
- COG → geotiff.js → colormap → BitmapLayer pipeline (precipitation, SM, SST, IVT, depth)
- WeatherLayers GL integration (ParticleLayer, ContourLayer, GridLayer, HighLowLayer)
- PNG frame crossfade system (soil moisture, satellite IR)
- PMTiles vector source integration (flood extent, burn scars)

**Track B: Temporal Player System**
- Chapter-local temporal player (start/play/stop/loop per chapter)
- Frame preloading on chapter approach (COGs or PNGs into memory)
- Dual-buffer crossfade for raster temporal animation
- Particle system tied to temporal player (wind field updates per frame)

**Track C: Scroll Choreography**
- Scrollama chapter enter/exit → camera + basemap + layer orchestration
- Sub-chapter transitions within Ch.4 and Ch.6
- GSAP text reveals, number tickers, annotation timing
- Per-chapter layer visibility rules (the "max 6 layers" constraint)
- Ch.3 scroll-driven SM animation (the one exception to "scroll ≠ time")
- Observable Plot sparklines in side panels (discharge, SM)

### Phase 3: Polish + Stretch Goals
- Entry animation (globe rotation → Portugal descent → title)
- maplibre-gl-compare before/after slider (Ch.6)
- Temperature field beneath isobars (Ch.4)
- 3D flood depth (Ch.6c)
- Satellite annotations ("EXPLOSIVE CYCLOGENESIS", "STING JET")
- Responsive layout + mobile
- Performance tuning + pre-fetch optimization
- Accessibility (ARIA, keyboard, reduced-motion)
- Free exploration mode (Ch.9)

---

## 7. Reference Prompts for Agent Sessions

When starting any implementation session:

```
Working on cheias.pt v2. Before doing anything, read:
1. CLAUDE.md — project rules
2. prompts/scroll-timeline-symbology.md — THE design spec (this document)
3. prompts/creative-direction-plan-v2.md — architectural decisions

Key principles:
- Scroll navigates between chapters. Chapters own temporal players.
- Temporal players start/play/stop/loop on chapter entry — NOT scrubbed by scroll.
- Exception: Ch.3 soil moisture IS scroll-driven (slow variable, works fine).
- Pre-load temporal frames on chapter approach. Don't load on demand.
- Max 6 layers visible simultaneously. Visual hierarchy > data density.
- Colormaps, basemap styles, and layer opacity are specified in the scroll timeline.
- WeatherLayers GL handles particles, isobars, wind barbs, H/L markers.
- All derived products (anomalies, percentiles, tracks) are in data/cog/ or data/qgis/.

Current task: [PHASE.TASK — DESCRIPTION]
```
