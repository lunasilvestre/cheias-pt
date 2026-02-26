# Creative Direction Plan: cheias.pt

**Date:** 2026-02-26
**Status:** AWAITING APPROVAL — do not proceed to implementation until the user approves this plan.
**Inputs:** Three research reports from parallel teammates:
- `prompts/creative-reports/library-compatibility.md` (Library Scout — 474 lines)
- `prompts/creative-reports/data-catalogue.md` (Data Cartographer — 517 lines)
- `prompts/creative-reports/effect-audit.md` (Effect Auditor — 649 lines)

---

## 1. Visual Identity Statement

cheias.pt should feel like a **Windy.com forecast rendered as editorial longform** — the atmospheric
immersion and real-time data density of a professional weather platform, fused with the narrative
pacing and emotional arc of a Vizzuality scrollytelling piece.

Not a dashboard. Not a tool. Not a data explorer. A **guided experience** that opens with a dark
Atlantic ocean and a single question — *O que aconteceu?* — and over 15 minutes of scrolling,
constructs the causal chain from warm ocean anomalies to collapsed motorways, building tension
like a documentary filmmaker who also happens to read COGs from R2.

**Reference products and what we take from each:**

| Reference | What we borrow | What we reject |
|-----------|---------------|----------------|
| **Windy.com** | Particle density, color vibrancy, atmospheric immersion, the "psychedelic swirl" of wind speed colormaps | The dashboard UI, the settings-heavy exploration mode, the absence of narrative |
| **Vizzuality (GFW, Half-Earth)** | Dark-first glassmorphism, progressive disclosure (Mode 1→2→3), institutional trust framing, Elena's emotional engagement sequence (Delight→Curiosity→Exploration→Digestion), serif hero typography for editorial authority | The React/Redux complexity, the heavy framework dependency |
| **The Pudding** | Scroll-driven revelation, data journalism voice, each chapter earning the right to exist, the "one graphic, one idea" discipline | The sometimes-whimsical tone (this story has body counts) |
| **NYT Graphics (storm tracker pages)** | The annotated satellite view, the "EXPLOSIVE CYCLOGENESIS" label on an IR image, the confidence of naming meteorological structures directly on the map | Proprietary tooling |
| **fogos.pt (Joao Pina)** | Proving a solo Portuguese developer can build a civic data platform that reaches 1M views/day. The audience exists. | The utility-first aesthetic (fogos.pt is a tool; cheias.pt is a story) |

**The aesthetic identity in one sentence:**
Dark oceanic authority — deep navy (#0a212e), luminous data, serif editorial voice,
glowing particle systems, glassmorphic panels floating over satellite imagery, and the
confidence to let a single map view breathe for 10 seconds before the next piece of
information arrives.

---

## 2. The Story Arc — Chapter-by-Chapter Visualization Design

### Chapter 1: The Hook

**Camera:** Wide Atlantic, pitch 15, bearing 5, zoom 3.5. Slow zoom-in over 8 seconds.
**Dominant visual:** Dark ocean, coastline glowing faintly. Single serif title: *"O Inverno Que Partiu Os Rios"*. Below it, a devastating number — "226,764 hectares submerged."
**Emotional beat:** Delight. Visual wonder. The user doesn't know what this is yet, but it's beautiful and ominous.
**Data:** None visible yet. The map is almost empty — just the dark basemap, the coastline, maybe a faint glow where Portugal is. The flood extent polygons (15,253 features) pulse once at 5% opacity, then fade — a ghost of what's coming.
**Layers:** Basemap only. Flood extent at ghost opacity.
**Pacing:** Slow. 10-15 seconds of scroll space. Let the title breathe.

### Chapter 2: The Planetary Scale (The Atlantic Engine)

**Camera:** Atlantic wide view, center [-25, 35], zoom 4, pitch 10. Slow eastward drift.
**Dominant visual:** SST anomaly field (warm reds in subtropical Atlantic) with IVT corridor rendered as a TripsLayer animated ribbon — the "moisture highway" flowing from the subtropics to Iberia. The ribbon glows, pulses with magnitude, and carries the eye toward Portugal.
**Emotional beat:** Scale. The audience should feel the enormity of what's converging on a small country.
**Data drives it:**
- SST anomaly COGs (66 daily, 6.9 MB) as background raster — warm Atlantic in reds/oranges
- ECMWF HRES IVT at 0.1deg (17 files, Jan 25-Feb 10) for the atmospheric river corridor
- ERA5 IVT at 0.5deg (77 daily) for broader temporal context
- Storm tracks GeoJSON (3 paths) with named labels moving along their arcs
**Key effect:** TripsLayer atmospheric river — animated ribbon with trailing fade, colored by IVT magnitude (250-800+ kg/m/s). This is the signature visual of the entire piece.
**Text panel:** "In January 2026, an unusually warm Atlantic loaded the atmosphere with moisture. Three named storms would carry it to Portugal in 14 days."
**Pacing:** Medium. 20-30 seconds of scroll. Two beats: SST anomaly appears, then IVT ribbon animates.

### Chapter 3: The Setup (The Sponge Fills)

**Camera:** National scale, center [-8, 39.5], zoom 6.5, pitch 20. Static — the camera stays still while the data evolves.
**Dominant visual:** Soil moisture PNG animation — 77 pre-rendered frames showing the ground transitioning from brown/dry (December) to deep blue/saturated (late January). The scroll controls the timeline: as the user scrolls, weeks pass. The ground fills like a bathtub.
**Emotional beat:** Slow dread. The audience should feel the inevitability — *the ground can't absorb any more.*
**Data drives it:**
- 77 soil moisture PNGs (11 MB, READY) — scroll-controlled crossfade animation
- Soil moisture basin sparklines in the text panel (Observable Plot)
- Wildfire burn scars (PMTiles, 3.9 MB) — subtle overlay: "the ground was already wounded"
- Single stat: saturation 0.13 → 0.90 (83% of dynamic range consumed before first storm)
**Key effect:** Precipitation temporal sweep (Effect 2) — soft, gaussian-blurred blue washes accumulating over Portugal. Pre-rendered PNGs with blur applied in pre-processing.
**Text panel:** Small Observable Plot sparklines per basin showing saturation curves. The text names the basins reaching critical levels: *"By January 25, Minho-Lima was already at 0.49."*
**Pacing:** Slow. The slowest chapter — 30-40 seconds of scroll for 8 weeks of data. Each scroll step = ~3 days. Let the water accumulate.

### Chapter 4: The Storms Arrive (Three Storms in Two Weeks)

**Camera:** Three-stage zoom sequence:
1. Iberia scale (zoom 5.5) for Storm Kristin approach
2. Portugal scale (zoom 6.5, pitch 25) for Leonardo impact
3. Basin scale (zoom 8) for Marta's final blow
**Dominant visual:** Wind particles at full density (5,000+) with per-segment trail decay over a wind speed background field — the "psychedelic swirl" from the WeatherWatcher14 video. Satellite IR timelapse of Kristin's comma cloud. MSLP isobars evolving dynamically via d3-contour.
**Emotional beat:** Drama. Acceleration. The pacing speeds up — frames advance faster, camera pushes in, data layers pile on. This is the visceral chapter.
**Data drives it:**
- Wind U/V COGs (816 files) → particle system with per-segment trail opacity
- Wind speed background field (computed from U/V magnitude) with purple/green/yellow ramp
- MSLP COGs (408) → d3-contour-generated isobars per timestep, white 1.5px lines
- Satellite IR COGs (48 hourly, Kristin only) → enhanced IR colormap (inverted grayscale)
- IPMA warnings JSON (18 districts x 21 days) → district choropleth yellow→orange→red
- Lightning GeoJSON (262 flashes) → yellow stars appearing during frontal passage
- Precipitation PNGs (77 daily) → blue wash accumulation
**Sub-chapters (scroll-triggered):**
- 4a: *"Kristin"* — Satellite IR timelapse + wind particles + lightning + "EXPLOSIVE CYCLOGENESIS" annotation
- 4b: *"The respite that wasn't"* — Brief green in IPMA warnings, but river levels barely dropped
- 4c: *"Leonardo"* — MSLP isobars deepening + precipitation sweep + warning escalation to red
- 4d: *"Marta"* — The third blow. Basin-zoom. The map is saturated with layers now.
**Key effects:** Wind particles (E1), MSLP isobars (E3), satellite cloud motion (E4), precipitation sweep (E2), layer transitions (E6). This chapter uses more effects than any other.
**Pacing:** Fast. The fastest chapter — 20-25 seconds but with more scroll steps (each step is a sub-chapter beat). Frames advance at 3-4 fps during auto-play sections.

### Chapter 5: The Rivers Respond

**Camera:** Basin scale, sequential focus on Tejo → Mondego → Sado → Guadiana. Zoom 7-9, pitch 15.
**Dominant visual:** River lines that "swell" — width proportional to discharge ratio. Station markers pulsing at peak. Observable Plot hydrographs in the text panel showing each river climbing toward (and past) the threshold.
**Emotional beat:** Inevitability. The lag between rain and river response — the audience sees the rain stop but the rivers keep rising.
**Data drives it:**
- Discharge timeseries JSON (8 rivers) → Observable Plot sparklines in panels
- Rivers GeoJSON (264 segments) → PathLayer with data-driven width from discharge
- Discharge stations GeoJSON (11 points) → pulsing markers sized by amplification factor
- Basin polygons → subtle fill colored by precondition score
**Key effect:** River swelling animation — scroll controls time, rivers grow thicker as discharge increases. The Guadiana at 11.5x amplification should look alarming.
**Text panel:** Per-river hydrograph (Observable Plot) appearing as each river is discussed. Key stat: *"Before the rivers dropped from Kristin, Leonardo hit."*
**Pacing:** Medium-slow. The inevitability pace — each river gets its moment. 25-30 seconds.

### Chapter 6: The Consequences (The Human Cost)

**Camera:** Close-up sequence. Alcacer do Sal → Coimbra → A1 collapse → Salvaterra. Zoom 10-13, pitch 30-45.
**Dominant visual:** Flood extent polygons filling in over satellite/aerial imagery. Consequence markers dropping in as text reveals each impact. Salvaterra temporal triptych: flood extent growing 58% over 48 hours.
**Emotional beat:** Intimacy. Data becomes names, places, deaths. The camera is close. The numbers are specific. *"11 people died."*
**Data drives it:**
- Flood extent PMTiles (15,253 polygons, 226,764 ha) → fill with semi-transparent blue
- Salvaterra temporal PMTiles (3 dates: Feb 6/7/8) → progressive fill animation
- Consequence events GeoJSON (42 markers) → IconLayer with type-specific icons, expandable
- maplibre-gl-compare (before/after Sentinel-2) — if acquired from Copernicus Data Space
**Sub-chapters:**
- 6a: *"Coimbra: twice in ten days"* — EMSR861 (Kristin) + EMSR864 (Leonardo) overlaid
- 6b: *"The A1"* — Pin drop on motorway collapse
- 6c: *"Salvaterra de Magos"* — Temporal triptych: 31K → 42K → 49K hectares
- 6d: *"The count"* — All 42 consequence markers visible simultaneously
**Key effect:** Layer transitions (E6) are critical here — each sub-chapter reveals more data. Camera close-ups with pitch 30-45 for dramatic framing.
**Pacing:** Medium. Each impact gets its moment. 25-30 seconds. The tone shifts from data to human.

### Chapter 7: The Full Picture (Climax)

**Camera:** Pull back to national scale. Center [-8, 39.5], zoom 6, pitch 15, bearing 0. The widest view since Chapter 2 — the audience sees the whole country.
**Dominant visual:** ALL consequences overlaid on ALL causes. Flood extent (blue) + consequence markers (icons) + wildfire burn scars (amber — the reveal) + precondition basins (red fill). The causal chain visible in a single frame.
**Emotional beat:** Understanding. The moment where everything connects. *"Each piece alone was manageable. Together, they created a catastrophe."*
**Data drives it:**
- All flood extent polygons (national view)
- All 42 consequence markers
- Wildfire burn scars 2024+2025 (PMTiles) — THE REVEAL: summer fires created winter floods
- Precondition basins colored by composite score
- Basin boundaries for spatial structure
**Key effect:** Layer build-up — layers appear sequentially as the user scrolls, compositing into the full picture. Max 3 layers at full opacity simultaneously; others at reduced opacity.
**Pacing:** Slow reveal. 15-20 seconds. Let the full picture sink in.

---

## 3. Effect-by-Effect Creative Solutions

### Effect 1: Wind Particle Streamlines

**Library:** Custom code (already built) — keep it. The prototype's JS advection + deck.gl PathLayer approach works and avoids dead dependencies (deck.gl-particle is archived, WeatherLayers GL needs npm).

**Dataset:** Wind U/V COGs (816 files, 69 MB, on R2). Already loaded via geotiff.js with bilinear interpolation.

**Critical upgrades needed:**

| Upgrade | Description | Effort |
|---------|-------------|--------|
| Per-segment trail opacity | Split each trail into individual LineLayer segments with exponential alpha decay (head=1.0, tail→0.0). deck.gl PathLayer doesn't support per-vertex alpha natively. | 1-2 days |
| Default particle count → 5,000 | Trivial parameter change. Slider max stays at 10,000. | 10 minutes |
| Wind speed background field | Compute sqrt(u²+v²) from U/V COGs already loaded. Render as BitmapLayer beneath particles. Purple/green/yellow ramp at 40-50% opacity. | 0.5-1 day |
| Smooth color ramp | Replace 4-band step function with continuous interpolation across the purple-magenta-green-yellow spectrum. | 1 hour |
| Density-weighted spawning | Spawn more particles in high-speed regions (use wind magnitude as probability weight). | 2-3 hours |

**What it should look like:** Dense, luminous particle rivers flowing over a glowing wind speed field. The jet stream is a vivid purple-white ribbon; calm areas are sparse green dots. Each particle has a comet tail that fades exponentially. The overall effect is hypnotic and atmospheric — Windy.com quality at editorial pacing.

**Chapters served:** Ch. 2 (Atlantic scale, wide view), Ch. 4 (Iberia/Portugal scale, storm detail).

**Lateral thinking:** At Atlantic scale, combine wind particles with the TripsLayer atmospheric river ribbon. The particles provide texture; the TripsLayer provides the macro narrative ("moisture flows HERE").

### Effect 2: Precipitation Temporal Sweep

**Library:** MapLibre image source (simplest) or deck.gl BitmapLayer dual-buffer (already built).

**Dataset:** 77 pre-rendered PNGs in `data/raster-frames/precipitation/` (2.5 MB total, READY). Also 78 COGs on R2.

**Pre-processing needed:** Apply gaussian blur to the 77 PNGs (Python: `scipy.ndimage.gaussian_filter` with sigma=2-3). Also re-render with the `blues` colormap and magnitude-proportional alpha (light rain = 30% alpha, heavy rain = 100%). Output: 77 new PNGs with soft watercolor quality. ~1 hour pipeline.

**Critical upgrades:**

| Upgrade | Description | Effort |
|---------|-------------|--------|
| Switch to pre-blurred PNGs | Serve blurred PNGs directly instead of COG→canvas pipeline. Faster loading, better visual quality. | 0.5 day |
| Default colormap → blues | Change `defaultCmap: 'viridis'` → `'blues'` | 1 minute |
| Magnitude-proportional alpha | Light rain translucent, heavy rain opaque. Bake into PNG alpha channel during pre-processing. | Included in pre-processing |
| Slower crossfade (300-500ms) | Override playback crossfade from 150ms to 350ms for precipitation specifically. | 30 minutes |
| Frame rate → 3 fps | Slow from 5fps (200ms interval) to 3fps (333ms) for the "rolling curtain" impression. | 5 minutes |

**Chapters served:** Ch. 3 (accumulation over weeks, scroll-driven), Ch. 4 (storm-scale daily advance).

### Effect 3: MSLP Isobar Animation

**Library:** d3-contour (CDN, ~10KB) for generating contours + MapLibre GeoJSON line layer for rendering. d3-contour takes a flat array + grid dimensions + thresholds → outputs GeoJSON MultiPolygons.

**Dataset:** 408 MSLP COGs (31 MB, on R2). Currently rendered as color-mapped raster. Contours need to be generated.

**Two approaches for temporal contours:**

**Option A: Pre-generate (recommended for v0)**
- Python script: `rasterio` reads each COG → `contourpy` or `matplotlib.contour` generates isobars at 4 hPa intervals → output GeoJSON per timestep
- 408 files, ~5KB each = ~2 MB total
- Frontend loads the matching GeoJSON when timeline scrubs
- Effort: 1 day (script + validation)

**Option B: Client-side d3-contour (recommended for v1)**
- geotiff.js reads MSLP COG → extract band as Float32Array → d3.contours().size([w,h]).thresholds([960,964,...,1040]) → GeoJSON → reproject pixel→geo → MapLibre setData()
- ~10ms per contour generation on 200×200 grid
- Real-time contour generation on timeline scrub
- Effort: 0.5 day (once the data pipeline for d3-contour is proven)

**Additional needs:**

| Upgrade | Description | Effort |
|---------|-------------|--------|
| Temporal L/H markers | Track pressure minima/maxima across timesteps. Python script: scipy.ndimage local_extrema on each MSLP COG. | 0.5 day |
| Contour stroke → 1.5px white | Change from 0.8px #ccc to 1.5px #fff | 1 minute |
| MSLP rescale → [95500, 104000] | Capture deep lows (Kristin ~960 hPa) | 1 minute |
| Crossfade → 500-800ms | Override for MSLP specifically — "slow, majestic" tempo | 30 minutes |

**Temperature field (separate layer):**
The spec calls for a temperature color field BENEATH the isobars — deep red (warm/subtropical), deep blue (cold/polar), white at boundary. This requires:
- Fetching ERA5 2m temperature or 850hPa temperature data (Open-Meteo archive, free, ~2h script)
- Generating temperature COGs matching MSLP timesteps
- Adding a second raster layer with red/white/blue diverging colormap at 70-80% opacity
- Isobars drawn on top
- Effort: 1-2 days total

**Chapters served:** Ch. 4 (synoptic authority — this is the "weather map" that journalists and meteorologists recognize).

### Effect 4: Satellite Cloud Motion

**Library:** MapLibre image source crossfade (same dual-buffer as precipitation) or deck.gl BitmapLayer.

**Dataset:** 48 IR COGs (101 MB, on R2, Jan 27-28 only). 48 VIS COGs (135 MB, daytime only). Known gap: no Leonardo/Marta imagery.

**Critical upgrades:**

| Upgrade | Description | Effort |
|---------|-------------|--------|
| Enhanced IR colormap | Replace generic thermal ramp with inverted grayscale (cold clouds = white, warm surface = dark). Standard meteorological convention. | 1 hour (new LUT) |
| Fetch Leonardo/Marta satellite | Re-run `scripts/fetch_eumetsat.py` for Feb 5-7 and Feb 10-11 dates. Existing eumdac credentials and pipeline. | 0.5 day |
| Map annotations | HTML overlay system: "EXPLOSIVE CYCLOGENESIS", "STING JET", dry slot arrow. Positioned via map.project() at geographic coordinates. Show/hide per chapter. | 0.5-1 day |
| Pre-render to PNG frames | Convert 48 IR COGs to optimized PNGs with enhanced colormap baked in. Faster loading, no client-side color mapping needed. | 1 hour script |

**Side-by-side view (Phase 3):**
maplibre-gl-compare plugin provides a split-screen slider between two map instances. Could show Atlantic-wide + Portugal-zoomed views simultaneously. CDN-loadable, ~5KB. Effort: 0.5 day. Defer to Phase 3 (polish).

**Chapters served:** Ch. 4 sub-chapter 4a (Kristin satellite). THE visual centrepiece of the meteorological narrative.

### Effect 5: Synoptic Chart + Radar Composites

**Library:** Composite of multiple layers: d3-contour (isobars) + deck.gl IconLayer (wind barbs) + MapLibre raster (precipitation) + MapLibre line layer (fronts).

**Status:** This is the most complex effect and the furthest from implementation. The Effect Auditor correctly flags it as Tier 3. Key gaps:
- Wind barbs need proper meteorological notation (canvas sprite factory)
- Frontal boundaries need manual analysis for 3-4 key timesteps
- No radar data (GPM IMERG as fallback needs Earthdata auth)

**Recommendation:** Defer the full synoptic composite to Phase 3. For v0, the MSLP isobars (Effect 3) + wind particles (Effect 1) + precipitation sweep (Effect 2) combine to create a "synoptic-like" experience without the formal chart notation. The full synoptic chart can be added as an expert-mode overlay in the exploration chapter.

**If pursued in Phase 3:**

| Component | Approach | Effort |
|-----------|----------|--------|
| Wind barb sprites | Canvas factory: draw staff + flags (50kt), long barbs (10kt), short barbs (5kt). Render as deck.gl IconLayer with rotation. | 1-2 days |
| Frontal boundaries | Manual GeoJSON for 3-4 key timesteps (Kristin peak, Leonardo peak, Marta peak). Cold front = blue + triangles, warm front = red + semicircles. | 0.5 day manual work |
| Radar fallback (GPM IMERG) | NASA Earthdata account + script to fetch 30-min HDF5 for Jan 27-Feb 10. Convert to PNGs with green-yellow-red radar colormap. | 1-2 days |

**Chapters served:** Expert overlay in Ch. 4, or a dedicated meteorology sub-chapter.

### Effect 6: Layer Transitions & Scroll-Driven Narrative

**Library:** scrollama (CDN, ~3KB) for scroll step detection + GSAP + ScrollTrigger (CDN, ~30KB) for animation polish + MapLibre flyTo/easeTo for camera.

**This is the #1 priority.** Without it, cheias.pt is a map viewer, not a story. Everything else hangs on this.

**Architecture:**

```
Declarative chapter config (JS object array)
  → scrollama detects step enter/exit
    → MapLibre flyTo() for camera
    → MapLibre setPaintProperty() for layer opacity
    → GSAP for text panel reveals, number tickers, basemap tint
    → deck.gl updateProps for particle/path layers
```

**Chapter config format** (adapting Vizzuality's layers-storytelling pattern):

```javascript
const chapters = [
  {
    id: 'hook',
    title: 'O Inverno Que Partiu Os Rios',
    subtitle: '226,764 hectares submerged',
    alignment: 'center',
    location: { center: [-12, 40], zoom: 3.5, pitch: 15, bearing: 5 },
    transition: { type: 'flyTo', duration: 3000, easing: 'easeOutCubic' },
    onChapterEnter: [
      { layer: 'flood-extent', opacity: 0.05, duration: 2000 }
    ],
    onChapterExit: [
      { layer: 'flood-extent', opacity: 0 }
    ],
    mapInteractive: false
  },
  // ... 8 more chapters
];
```

**Implementation effort:** 2-3 days for the scroll engine. Then each chapter's layer choreography is configured declaratively.

**Transition standards** (from Vizzuality methodology):
- All opacity transitions: 400ms, `cubic-bezier(0.445, 0.05, 0.55, 0.95)`
- Camera geographic jumps: `flyTo()`, 2000ms
- Camera small movements: `easeTo()`, 1500ms
- Text panel reveals: GSAP, 600ms, stagger 50ms per element
- Number tickers: GSAP CountUp, 1200ms

**Chapters served:** ALL chapters. This IS the narrative.

---

## 4. Untapped Data Opportunities

### Tier 1: High impact, data ready, just needs integration

| Dataset | What it adds | Chapter | Status | Effort |
|---------|-------------|---------|--------|--------|
| **Wildfire burn scars (2024+2025)** | The "hidden cause" reveal — summer fires created winter floods. 9.2 MB GeoJSON + 3.9 MB PMTiles, READY. | Ch. 7 climax | Data acquired, PMTiles generated, **completely unused** | 2-3 hours integration |
| **Salvaterra temporal triptych** | 58% flood growth in 48 hours — the most powerful temporal visualization in the project. PMTiles with date filter, READY. | Ch. 6 | Data ready, needs scroll-driven reveal | 0.5 day |
| **IPMA warning escalation** | District choropleth yellow→orange→red. 18 districts × 21 days × 3 types. Frontend JSON, READY. | Ch. 4 | In prototype as data, needs scroll choreography | 0.5 day |
| **Lightning (262 flashes)** | Burst of yellow stars during frontal passage. PMTiles + GeoJSON, READY. | Ch. 4a | Data ready, needs timed reveal during satellite sequence | 2-3 hours |
| **ECMWF HRES IVT (0.1deg)** | High-resolution atmospheric river at 10x the detail of ERA5 IVT. 17 COGs, READY. | Ch. 2 | Data acquired, needs TripsLayer integration | 1 day |

### Tier 2: High impact, needs processing from existing data

| Dataset | What it adds | Chapter | Input exists | Processing needed | Effort |
|---------|-------------|---------|-------------|------------------|--------|
| **Temporal MSLP contours** | Animated isobars — the "breathing cyclone" | Ch. 4 | 408 MSLP COGs | gdal_contour or contourpy batch | 1 day |
| **Gaussian-blurred precipitation PNGs** | Soft watercolor rain washes | Ch. 3/4 | 77 existing PNGs | scipy gaussian_filter + alpha encoding | 0.5 day |
| **Satellite IR PNG frames** | Faster satellite crossfade, enhanced colormap | Ch. 4 | 48 IR COGs | rasterio + PIL with inverted grayscale | 1 hour |
| **Wind speed magnitude COGs** | Background field for wind particles | Ch. 4 | Wind U/V COGs | sqrt(u²+v²) computation | 2-3 hours |
| **Temporal L/H pressure markers** | Moving "L" and "H" labels | Ch. 4 | 408 MSLP COGs | scipy local extrema detection | 0.5 day |
| **Flood depth extraction** | Water depth in meters at Salvaterra | Ch. 6 | Raw CEMS SHP files | geopandas extraction | 1 hour |

### Tier 3: High impact, needs external fetch

| Dataset | What it adds | Chapter | Source | Auth | Effort |
|---------|-------------|---------|--------|------|--------|
| **Sentinel-2 before/after** | The aftermath — satellite true color showing flooded vs. normal | Ch. 6 | Copernicus Data Space STAC | Free, no auth for tiles | 0.5 day script |
| **Extended Meteosat (Leonardo/Marta)** | Satellite coverage for ALL three storms, not just Kristin | Ch. 4 | EUMETSAT eumdac | Existing credentials | 0.5 day (re-run existing pipeline) |
| **ERA5 temperature field** | Warm/cold front visualization beneath isobars | Ch. 4 | Open-Meteo archive | Free, no auth | 1 day |
| **Higher-resolution IVT** | Full Dec-Feb atmospheric river at 0.25deg | Ch. 2 | Open-Meteo pressure-level archive | Free, no auth | 1-2 days |

### The Storytelling Gem: Fire → Flood

The single most intellectually original dataset in the project is the wildfire-flood connection. Summer 2025 burn scars (EFFIS data, fully acquired, PMTiles ready) overlap spatially with areas that experienced the worst flooding and landslides. This is the insight that elevates cheias.pt from "flood map" to "territorial risk analysis" — the kind of cross-domain connection that a Development Seed interviewer would recognize as systems thinking.

**Implementation:** In Chapter 7, after showing all flood extent and consequences at national scale, fade in the wildfire burn scars in amber/orange. The spatial correlation is immediate and visceral. A single caption: *"Where the fire burned, the water ran faster."*

---

## 5. Prioritized Implementation Sequence

### Phase 0: Narrative Architecture (Week 1)

The scroll-driven narrative engine is the foundation everything else builds on. Without it, every visual effect is just a demo toggle.

| # | Task | Delivers | Effort |
|---|------|----------|--------|
| 0.1 | **Implement scrollama + chapter config** | Scroll-driven chapter enter/exit events. Sticky map + scrolling text panels. Declarative camera + layer opacity per chapter. | 2-3 days |
| 0.2 | **Add GSAP for text/UI animation** | Panel reveals, number tickers, basemap tint transitions. Consistent 400ms easing. | 1 day |
| 0.3 | **Create chapter HTML structure** | 9 chapter divs with text content, each 50-100vh. Hero serif title for Ch.1. | 1 day |
| 0.4 | **Fix basemap aesthetics** | Background → #0a212e. Glassmorphism → rgba(9,20,26,0.4) + blur(16px). Institutional attribution. | 2-3 hours |
| 0.5 | **Add serif hero typography** | Georgia or similar serif at 45px weight 300 for chapter titles. Inter for body. | 1-2 hours |

**Deliverable:** A scrollable page where chapters trigger camera moves and layer opacity changes. No new data layers — just the narrative skeleton wired to existing layers.

### Phase 1: Data Pipeline (Week 2)

Pre-process the data needed for the core narrative effects.

| # | Task | Delivers | Effort |
|---|------|----------|--------|
| 1.1 | **Batch generate temporal MSLP contours** | 408 GeoJSON files (or d3-contour client-side pipeline) | 1 day |
| 1.2 | **Pre-render precipitation PNGs with gaussian blur + blues colormap + alpha** | 77 improved PNGs | 0.5 day |
| 1.3 | **Pre-render satellite IR PNGs with enhanced colormap** | 48 enhanced PNG frames | 2-3 hours |
| 1.4 | **Compute wind speed magnitude field** | COGs or on-the-fly from U/V (client-side) | 2-3 hours |
| 1.5 | **Generate temporal L/H markers** | 408 point GeoJSONs with pressure center positions | 0.5 day |
| 1.6 | **Fetch extended Meteosat imagery (Leonardo/Marta)** | ~96 additional IR COGs covering Feb 5-11 | 0.5 day |
| 1.7 | **Fetch Sentinel-2 before/after for Salvaterra** | 2 true-color scenes | 0.5 day |
| 1.8 | **Prepare TripsLayer data from IVT** | Waypoint JSON for atmospheric river animation | 0.5 day |

**Deliverable:** All data pre-processed and ready for frontend integration.

### Phase 2: Core Narrative Effects (Weeks 3-4)

Build the visualization pieces that make the story work, wired to the scroll engine.

| # | Task | Delivers | Effort |
|---|------|----------|--------|
| 2.1 | **Wind particle upgrades** | Per-segment trail opacity, wind speed background field, smooth color ramp, density-weighted spawning, default 5K particles | 2-3 days |
| 2.2 | **MSLP isobar animation** | Dynamic contours from d3-contour or pre-generated GeoJSONs, temporal L/H markers, white 1.5px strokes | 1-2 days |
| 2.3 | **Satellite IR enhanced** | Inverted grayscale colormap, pre-rendered PNG crossfade, "EXPLOSIVE CYCLOGENESIS" annotation | 1 day |
| 2.4 | **Precipitation sweep refined** | Blurred PNGs, blues colormap, magnitude-proportional alpha, 350ms crossfade at 3fps | 0.5 day |
| 2.5 | **TripsLayer atmospheric river** | Animated ribbon from Atlantic to Iberia, colored by IVT magnitude, trailing fade | 1-2 days |
| 2.6 | **Soil moisture scroll animation** | 77 PNG frames driven by scroll position (not timeline), basin sparklines via Observable Plot | 1 day |
| 2.7 | **River discharge visualization** | River lines with discharge-driven width, station pulse markers, Observable Plot hydrographs in panels | 1-2 days |
| 2.8 | **Flood extent + consequences** | PMTiles flood polygons, consequence IconLayer, Salvaterra temporal reveal | 1-2 days |
| 2.9 | **IPMA warning choropleth** | District-level warning animation, yellow→orange→red escalation driven by scroll | 1 day |
| 2.10 | **Chapter 7: the wildfire reveal** | Burn scar overlay + composite of all flood layers | 0.5 day |

**Deliverable:** All chapters functional with data-driven visualizations wired to scroll.

### Phase 3: Polish and Delight (Week 5)

The details that elevate from "good" to "Vizzuality-grade."

| # | Task | Delivers | Effort |
|---|------|----------|--------|
| 3.1 | **Entry animation** | Slow camera descent over dark Atlantic, hero title fade-in, coastline glow | 0.5 day |
| 3.2 | **maplibre-gl-compare** | Before/after satellite slider for Salvaterra (Ch. 6) | 0.5 day |
| 3.3 | **Temperature field beneath isobars** | Red/white/blue raster under MSLP contours for warm/cold front visualization | 1-2 days |
| 3.4 | **Wind barb sprite system** | Canvas-generated proper meteorological notation (if pursued) | 1-2 days |
| 3.5 | **Satellite annotations** | HTML overlay for meteorological feature labels | 0.5 day |
| 3.6 | **Responsive layout** | Mobile bottom sheet, tablet adaptation | 1-2 days |
| 3.7 | **Accessibility** | ARIA labels, keyboard navigation, contrast fixes | 1 day |
| 3.8 | **Performance tuning** | Pre-fetch frames, optimize particle rendering, lazy-load chapters | 1 day |
| 3.9 | **Free exploration mode** | After completing the narrative, unlock full map interaction (Chapter 9) | 1 day |

---

## 6. Architecture Recommendation

### v0: Graduate to multi-file, keep CDN loading

The single-file HTML prototype has served its purpose as a spike. For the scrollytelling narrative, split into:

```
cheias-pt/
  index.html              # Scroll structure, chapter divs, hero title
  css/
    style.css             # Dark-first design system, glassmorphism, typography
  src/
    chapters.js           # Chapter config (camera, layers, text)
    scroll-engine.js      # scrollama + GSAP initialization
    map-setup.js          # MapLibre + deck.gl initialization
    layer-manager.js      # Layer creation, crossfade, opacity
    particle-system.js    # Wind particle advection + rendering
    contour-generator.js  # d3-contour MSLP isobar pipeline
    data-loader.js        # COG loading, geotiff.js pipeline
    charts.js             # Observable Plot inline charts
  data/
    (existing data directories)
```

**All libraries remain CDN-loaded.** No npm, no bundler, no node_modules. The `src/` files are ES modules loaded with `<script type="module">`:

```html
<script src="https://cdn.jsdelivr.net/npm/scrollama@3"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
<script type="module">
  import { initMap } from './src/map-setup.js';
  import { initScrollEngine } from './src/scroll-engine.js';
  import { chapters } from './src/chapters.js';
  // ...
</script>
```

**CDN stack (total ~100KB gzipped additional to current):**

| Library | CDN | Size (gzip) | Purpose |
|---------|-----|-------------|---------|
| scrollama | jsDelivr | ~3KB | Scroll step detection |
| GSAP + ScrollTrigger | cdnjs | ~30KB | Animation polish |
| d3-contour | esm.sh | ~10KB | MSLP isobar generation |
| Observable Plot | jsDelivr | ~50KB | Inline sparklines |
| maplibre-gl-compare | npm CDN | ~5KB | Before/after satellite slider |

**Deployment:** Static files. GitHub Pages, Netlify, or Vercel. `python -m http.server` for local dev.

### v1: Vite + npm (when needed)

Migrate to Vite when:
- **deck.gl-raster** (Development Seed's GPU COG renderer) is desired — it replaces the manual geotiff.js→canvas pipeline with proper GPU rendering, automatic tiling, and colormap application. This is the single strongest argument for build tools.
- Performance demands exceed what CDN-loaded libraries can handle
- TypeScript or a framework (Svelte) becomes attractive

The migration from multi-file CDN to Vite is mechanical, not architectural:
```bash
npm create vite@latest cheias-pt -- --template vanilla
npm install maplibre-gl deck.gl scrollama gsap d3-contour @observablehq/plot geotiff
# Move src/ files, add import statements, vite build
```

**DevSeed alignment:** Development Seed uses TypeScript + deck.gl + MapLibre. Adopting their stack (especially deck.gl-raster) signals technical fluency. But for v0, the CDN approach proves we can ship a complete narrative without framework dependencies — which is also an impressive signal.

### The honest recommendation

**Start with v0 (multi-file CDN).** The creative vision does NOT require build tools. scrollama, GSAP, d3-contour, Observable Plot, and maplibre-gl-compare are all CDN-loadable. The wind particle system is custom code. The COG pipeline is geotiff.js via ESM.

Graduate to v1 when the v0 narrative is complete and polished. The Vite migration takes half a day and unlocks deck.gl-raster for the next level of rendering quality.

---

## What Happens Next

**This plan is awaiting your approval.** Once approved, Phase 3 of the creative direction prompt asks me to write concrete implementation prompts for each task in the priority sequence — copy-paste-ready prompts with specific library imports, dataset paths, and visual specs.

The implementation sequence is designed for narrative coherence, not quick wins:
- Phase 0 builds the story engine
- Phase 1 prepares the data
- Phase 2 creates each chapter's visualization
- Phase 3 polishes to portfolio grade

Total estimated effort: ~5 weeks of focused work. The result: a geo-narrative that competes with Vizzuality's portfolio for Development Seed's attention.
