# Creative Direction: cheias.pt Visual Identity

You are the creative director for cheias.pt — a flood intelligence platform for Portugal
that needs to look like it was built by Vizzuality, not by a solo developer on a weekend.

Your background: 15 years in geospatial visualization. You've worked with EO data at scale.
You know what deck.gl, MapLibre, D3, flowmap.gl, and TripsLayer can do because you've
shipped products with them. You have strong opinions about map aesthetics — you call bullshit
on ugly defaults and push for "map porn" — but you're pragmatic: you ship with open source
libraries, not bespoke WebGL shaders. You never write from scratch what a library already does.

Your mandate: take the existing prototype and make it *feel* like a professional weather
intelligence product. Not by rewriting — by composing existing tools with taste.

## The Dramatic Arc — Why Any of This Matters

The motion effects in the design document are NOT an end in themselves. They exist to serve
a scrollytelling narrative — a story that builds tension across chapters, from planetary
causes to human consequences, and releases it in a climactic moment of understanding.

Here's the narrative intuition (not a rigid spec — a dramatic guideline):

**Chapter 2: The planetary scale** — An unusually energetic Atlantic season pushed moisture
from the subtropics toward Iberia. SST anomalies, atmospheric river visualization. Wide
camera, continental. The viewer should feel the *scale* of what's coming.

**Chapter 3: The setup** — Weeks of antecedent rainfall saturating Portuguese soils. Soil
moisture animation from December through January. The ground filling like a sponge. National
scale, zooming to the worst basins. Tension building: the ground can't absorb any more.

**Chapter 4: The storms arrive** — Kristin, Leonardo, Marta in sequence. Precipitation
accumulation maps. IPMA warnings escalating from yellow to orange to red. Zooming from
national to the Tejo/Sado/Mondego basins. This is where the dynamic effects hit hardest —
wind, rain, pressure, satellite — all the meteorological drama.

**Chapter 5: The rivers respond** — Discharge data showing rivers climbing past thresholds.
Water levels rising toward flood stage. Basin-level zoom. The lag between rain falling and
rivers peaking — the slow inevitability.

**Chapter 6: The consequences** — Flood extent polygons, damage markers, road closures,
evacuations. Geocoded news and photos. This is the human chapter. Close-up on Alcácer do
Sal, Coimbra, the A1 collapse. Data becomes impact.

**Chapter 7 (climax): The full picture** — Pull back to national scale showing ALL
consequences overlaid on the antecedent conditions. The causal chain visible in a single
frame: saturated soil + incoming rain + overwhelmed rivers = this. The moment where
understanding crystallizes.

The 6 visual effects from the motion analysis serve this arc: wind particles and satellite
build the meteorological drama of Chapter 4. Crossfades and temporal evolution build the
slow tension of Chapters 3 and 5. Synoptic composites give Chapter 2 its authority. Layer
transitions and camera moves carry the viewer through the zoom progression from continental
to basin to street level.

**Your job as creative director is to design the dynamic effects so they serve this
dramatic build** — not as isolated technical demos, but as storytelling instruments. Every
animation choice should answer: does this increase tension, deliver information, or release
understanding at the right moment in the arc?

Note: we may have captured richer data sources than listed here. Check the 2nd Brain project
notes at `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/12-design-document.md` for
the original design vision and data inventory — it may suggest datasets or narrative beats
that aren't yet in the prototype.

## Phase 1: Orientation (READ EVERYTHING FIRST)

Before designing anything, read:

1. `deckgl-prototype.html` — the current state of the prototype
2. `data/video-analysis/MOTION-ANALYSIS.md` — the full design document (6 visual effects, ALL of them, not just wind)
3. `deckgl-dynamic-mapping-examples.md` — your library palette
4. `prompts/refactor-nwp-planetary-computer.md` — alternative data pipeline via STAC
5. `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/12-design-document.md` — original design vision, chapter structure, data sources
6. `~/.vaults/root/2nd-Brain/Projects/vizzuality-methodology/` — **the quality bar**.
   Read all 8 files. This is how Vizzuality builds environmental data platforms:
   design philosophy (Elena's four questions, progressive disclosure), visual design
   system (dark-first, Firefly basemap, glassmorphism), scrollytelling patterns
   (chapter config, camera transitions, layer choreography), architecture patterns,
   trust & transparency, anti-patterns to avoid, and their full platform portfolio
   (Global Forest Watch, Half-Earth, etc.). This is the standard we're designing toward.
7. `CLAUDE.md` — project context (slim version — the detailed specs are parked in
   `CLAUDE-v4-scrollytelling.md` if you need data pipeline details, but don't treat
   its architecture or stack decisions as constraints)

## Phase 2: Planning (WRITE A PLAN BEFORE TOUCHING CODE)

Spawn 3 teammates:

- **Library Scout**: Investigate every library mentioned in `deckgl-dynamic-mapping-examples.md`
  plus any others relevant to weather/flood/scrollytelling visualization. For each one:
  what does it render? What's the integration path (CDN, npm, bundler required)? Does it
  work with deck.gl v9 or MapLibre v4? Check live demos. Check GitHub issues.
  Also explore: d3-contour, d3-geo, turf.js, maplibre-contour, scrollama, GSAP ScrollTrigger,
  Svelte + LayerCake, any scrollytelling frameworks used by Vizzuality/Pudding/NYT Graphics.
  If the best tools require a build step, say so — and recommend the minimal build setup
  (Vite, esbuild) that would unlock them.
  Also check: what data formats do these libraries expect? Would pre-processing our COGs
  into image textures, vector tiles, or other formats make integration trivial?
  Report: a capability matrix — what each tool does, integration path, and what data format
  it needs. Saved to `prompts/creative-reports/library-compatibility.md`.

- **Data Cartographer**: Inventory ALL data available — both in this project AND externally.
  Walk `data/`, walk `scripts/`, check what formats exist (GeoJSON, PMTiles, Parquet,
  NetCDF, GRIB, COG, JSON timeseries). For each dataset, note: what it shows, temporal
  coverage, spatial extent, format, and which chapter it serves.
  Then look BEYOND the project: what's available on Microsoft Planetary Computer (Met Office
  global model, ERA5, Sentinel), Copernicus Data Space (flood extent, satellite), Open-Meteo
  (historical weather API), STAC catalogs? If a better dataset exists externally and can
  be fetched with a script, recommend it. If pre-processing existing data into formats
  that pair better with visualization libraries (e.g., U/V wind COGs → PNG wind textures
  for deck.gl-particle, MSLP grids → pre-computed contour GeoJSONs per timestep, flood
  polygons → temporal PMTiles) would unlock capabilities, spec that pipeline.
  Pay special attention to:
  - IVT data (the atmospheric river signal — this is the story's backbone)
  - Flood extent polygons (Copernicus EMS — 15K polygons, temporal evolution at Salvaterra)
  - IPMA warnings timeline (378 warnings with escalation from yellow→orange→red)
  - Consequence events (42 real impacts — roads cut, evacuations, deaths)
  - Discharge timeseries (river levels rising to flood stage)
  - Wildfires (burned areas that increased flood vulnerability)
  - Visible satellite (we have VIS alongside IR)
  - Planetary Computer Met Office data as STAC-native alternative to ERA5
  - ECMWF HRES forecasts (86 files with IVT, MSLP, winds)
  Report: a data catalogue with storytelling potential for each dataset, including external
  sources worth fetching. Saved to `prompts/creative-reports/data-catalogue.md`.

- **Effect Auditor**: Read `MOTION-ANALYSIS.md` end to end. For each of the 6 effects, audit
  the current prototype against the spec. Don't just check if the layer exists — check if it
  *looks right*. Check visual properties: color ramps match? Opacity correct? Trail decay
  working? Crossfade smooth? Density appropriate? Camera framing right?
  Then identify the gap between current state and the design doc's visual standard.
  Report: per-effect status with specific visual deficiencies, not just "partial."

Have all three teammates share findings as they go. When the Library Scout finds something
relevant to a gap the Effect Auditor identified, they should message each other.

Each teammate should save their report before sending it to the lead:
- Library Scout → `prompts/creative-reports/library-compatibility.md`
- Data Cartographer → `prompts/creative-reports/data-catalogue.md`
- Effect Auditor → `prompts/creative-reports/effect-audit.md`

### Planning Deliverable

The lead synthesizes all three reports into a **Creative Direction Document** saved to
`prompts/creative-direction-plan.md` with:

1. **Visual Identity Statement** — what should cheias.pt feel like? Not "a flood monitoring
   tool" — what's the *aesthetic* identity? Dark meteorological authority? Windy.com fluidity?
   Vizzuality editorial storytelling? Something else? Reference specific products.

2. **The Story Arc** — Map the dramatic arc (Chapters 2-7 described above) to concrete
   visualization designs. For each chapter: what's the dominant visual? What data drives it?
   What's the camera position and zoom level? What's the emotional beat — tension building,
   release, understanding? How do the 6 motion effects serve the chapter they appear in?
   Don't just list datasets per chapter — describe the *experience* of watching each chapter
   unfold. Think about pacing: which chapters are fast and dramatic (Ch. 4), which are slow
   and inevitable (Ch. 3, 5), which are intimate and human (Ch. 6).

3. **Effect-by-Effect Creative Solutions** — for each of the 6 effects in the design doc:
   - Which library/layer ALREADY DOES THIS (not "how to code it")
   - Which dataset feeds it — existing or fetchable
   - What data format does the library expect, and do we need a pre-processing step?
   - What it should look like (reference the contact sheets and frame descriptions)
   - Which chapter in the dramatic arc does this effect serve?
   - Lateral thinking: is there a surprising way to use a library for something it
     wasn't designed for? (e.g., TripsLayer for atmospheric river moisture flow,
     flowmap.gl for moisture transport corridors, ContourLayer for dynamic isobars)
   - If the best solution requires a build step or architecture change, say so plainly

4. **Untapped Data Opportunities** — what datasets exist in the project that aren't in the
   prototype yet but would dramatically improve the story? Think about which *chapter* each
   dataset serves in the dramatic arc:
   - IVT corridor visualization — the atmospheric river IS the story (Ch. 2)
   - SST anomalies — why the Atlantic was loaded with moisture (Ch. 2)
   - Soil moisture temporal build-up — the sponge filling over weeks (Ch. 3)
   - Flood extent animation — Salvaterra temporal evolution, water rising day by day (Ch. 6)
   - IPMA warning escalation — yellow → orange → red across districts over time (Ch. 4)
   - Consequence events — pin drops where things actually broke (Ch. 6)
   - Discharge timeseries — spark lines showing rivers rising past thresholds (Ch. 5)
   - The wildfire→flood connection — burned areas overlaid with subsequent flood extent (Ch. 3/7)
   - Visible satellite alongside IR — true color shows the storm differently (Ch. 4)
   - Precondition index — NOT mandatory for this phase. Could be envisioned as a forward-
     looking warning tool in a future Chapter 8 (from hindcast to forecast). Note it as a
     possibility, don't design for it now.

5. **Prioritized Implementation Sequence** — what to build in what order for maximum
   narrative coherence. Not "quick wins first" — what serves the story arc best.
   Group into phases:
   - Phase 0: Architecture migration (if recommended — build setup, scrollytelling framework)
   - Phase 1: Data pipeline (any pre-processing, fetching, format conversion needed)
   - Phase 2: Core narrative effects (the pieces that make the story work)
   - Phase 3: Polish and delight (the details that elevate from good to Vizzuality-grade)

6. **Architecture Recommendation** — should the prototype stay as a single HTML file, or
   graduate to a proper app? Be direct. If the creative vision requires libraries that
   need a bundler, or a scrollytelling framework, or component architecture — recommend
   the stack. Consider:
   - Scrollytelling: scrollama, GSAP ScrollTrigger, Svelte + scroll events
   - Build: Vite (minimal config, fast), esbuild, or a framework (Svelte, Next.js)
   - What Vizzuality, The Pudding, NYT Graphics actually use for this kind of work
   - What DevSeed uses (check their open-source projects)
   - What unlocks the most libraries with the least migration pain
   - Data pre-processing pipelines: what should be computed offline vs. client-side?

## Phase 3: Implementation Prompts

After the plan is approved by the user (STOP and wait for approval — do NOT proceed to
implementation), write concrete Claude Code prompts for each item in the priority sequence.
Each prompt should:
- Name the specific library and CDN import
- Name the specific dataset path and format
- Reference the visual spec from MOTION-ANALYSIS.md
- Be copy-paste ready for `cat prompt.md | claude`

Save these to `prompts/creative-impl-{N}-{name}.md`.

## Constraints (few, and intentional)

- The audience is Development Seed engineers who value taste, architectural judgment,
  and cloud-native geospatial fluency
- Open source only — but ANY open source. If a library needs a build step, recommend one.
  If the single-file prototype needs to become a proper app with Vite/Svelte/Next.js to
  unlock the right tools, say so. The prototype was a spike — the creative vision
  shouldn't be shaped by spike constraints.
- Data is not frozen. If Microsoft Planetary Computer, Copernicus Data Space, Open-Meteo,
  or any other source has better data or formats that pair more naturally with visualization
  libraries, recommend fetching it. If pre-processing into intermediate formats (GeoParquet,
  PMTiles, FlatGeobuf, image textures) would unlock library capabilities, spec that pipeline.
- Don't budget this like a sprint. Budget it like a portfolio piece that needs to compete
  with Vizzuality's work. If something takes a week but transforms the product from
  "developer demo" to "editorial geospatial storytelling," it's worth it.
- Do NOT pre-filter ideas based on implementation difficulty. Report the full creative
  vision first. Engineering feasibility is a separate conversation that happens after
  the creative direction is approved — not a filter on what gets explored.
