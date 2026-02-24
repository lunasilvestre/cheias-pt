# cheias.pt — Design & Development Plan

## Context

You are a geo-product studio combining Vizzuality's design storytelling, Development Seed's spatial data engineering, and modern AI agent orchestration. You have been hired to turn cheias.pt from a working prototype into a professional citizen-facing flood intelligence platform for Portugal.

**Current situation (February 2026):** Portugal experienced ~2 months of sustained rainfall causing widespread flooding, calamity declarations, and casualties. The immediate danger has now passed — waters are subsiding. cheias.pt has a working proto-MVP that monitors flood preconditions (soil moisture + forecast precipitation + river discharge) across 11 stations. The platform works technically but feels like a GIS tool, not a citizen product.

**This timing is strategic.** The receding flood gives us:
1. A real event with real data to validate the Precondition Index against
2. A news archive to build a compelling retrospective story
3. Public attention still warm but shifting from crisis to "what happened and why"
4. Time to build properly before the next event cycle

## Your task

Produce a **Design & Development Document** for cheias.pt structured as professional workstreams. This is the planning artifact that guides all subsequent implementation.

## Inputs to read first

### Current codebase (scan structure, read key files):
```
~/Documents/dev/cheias-pt/
```

## Elena's Four Questions (answer these first)

Before any design decisions, complete the structured exercise from the skill:

1. **Who is the user?** Define 3-4 personas for cheias.pt. Be specific to Portugal.
2. **What are they looking for?** Map each persona to their primary question and time budget.
3. **What is the most essential information?** What answers the primary question in 5 seconds?
4. **How do we make the non-essential available without overwhelming?** Define the disclosure sequence per persona.

## Workstreams

Structure the document around these workstreams, each with: objective, key questions to answer, deliverables, dependencies, and rough sequencing.

### WS1: Forensics & Index Validation
**Objective:** Determine if the Precondition Index would have correctly predicted the flooding events of Dec 2025–Feb 2026, or if it would have generated false alarms / missed events.

Key tasks:
- Gather historical data for the flood period: Open-Meteo soil moisture + precipitation, GloFAS discharge forecasts, IPMA warnings issued
- Collect news reports of actual flooding events (locations, dates, severity) as ground truth
- Run the current index formula against historical data for each of the 11 monitored stations
- Compare index alerts vs. actual events: hits, misses, false alarms
- Identify where the index needs calibration (thresholds, weighting, soil layer selection)
- Document findings as a validation report

**Design question:** How do we present this validation transparently on the site? (Methodology trust signal — "tested against the 2025-26 floods")

### WS2: Retrospective Story — "Two Months of Rain"
**Objective:** Create a data-driven narrative of the Dec 2025–Feb 2026 flood period that demonstrates cheias.pt's value proposition.

This is a scrollytelling piece that combines:
- Soil moisture accumulation over the 2-month period (the "filling up" before the floods)
- Precipitation data showing the sustained rainfall pattern
- River discharge responses (which basins peaked when)
- IPMA warnings timeline
- News reports of flooding, evacuations, casualties — matched to the data timeline
- The "climax moment" (Elena's term): when preconditions peaked and floods hit

**Design question:** This is the Soils Revealed / Half-Earth storytelling pattern. How do we apply the Delight → Curiosity → Exploration → Digestion sequence? The user should arrive curious, explore the timeline, and leave understanding WHY Portugal flooded — not just THAT it flooded.

**Data question:** What temporal resolution do we need? Hourly? Daily? What spatial resolution — district, basin, municipality?

### WS3: Data Architecture & Serving
**Objective:** Design the data pipeline that supports both real-time monitoring AND historical exploration.

Key decisions needed:
- **eoAPI vs. alternatives:** Should we stand up an eoAPI instance for serving STAC + COG layers (Copernicus GFM flood maps, soil moisture rasters)? Or is this over-engineering for MVP — could a simpler tile serving approach work?
- **Time series storage:** The retrospective story needs temporal data at multiple scales. Where does this live? PostGIS? Simple JSON files on S3? Cloud-optimized formats?
- **Granularity:** Current prototype uses point-level API calls to Open-Meteo. The story needs spatial coverage. Options: pre-compute a grid, use Open-Meteo's gridded endpoints, serve Copernicus NetCDF/GRIB as COG.
- **Real-time vs. historical:** Same pipeline or separate? Real-time needs freshness; historical needs completeness.

**DevSeed lens:** What would a cloud-native geospatial architecture look like here? STAC catalog for imagery, vector tiles for boundaries, time series API for station data? Or is that premature?

### WS4: UX/UI Design System
**Objective:** Define the visual language, interaction patterns, and component library for cheias.pt.

Apply the geo-storytelling skill to define:
- **Color system:** Risk encoding (sequential for precondition index), categorical (data source types), base palette (dark theme with functional rationale)
- **Typography:** What carries authority for a Portuguese civic platform?
- **Component inventory:** Glassmorphism sidebar, bottom sheet, risk gauge, sparkline charts, data freshness badges, methodology disclosure, IPMA warning cards
- **Map design:** Basemap selection (familiar terrain first), layer hierarchy (which layers are always visible, which appear on interaction), zoom-level behavior
- **Self-orienting views:** How does each view orient a cold arrival?
- **State confirmation:** Micro-interactions for every user action
- **Spatial orientation anchor:** Mini-map showing viewport within Portugal

**The "alive feeling":** What makes cheias.pt feel like a living system, not a static dashboard? Animations, transitions, data pulse indicators, temporal scrubbing?

### WS5: Site Architecture & Modes
**Objective:** Define the site's information architecture and how different content modes coexist.

Proposed structure (validate and refine):
- **/ (home):** Mode 1 Glance — full-screen map, color-coded risk, current status. "What's the situation right now?"
- **/story/chuvas-2025:** Mode 2 Storytelling — the retrospective scrollytelling piece (WS2)
- **/explore:** Mode 2 Exploration — independent data layers, user builds their own view
- **/about or /como-funciona:** Mode 3 Understanding — methodology, validation results (WS1), data sources
- **/agent (future):** Mode 3 Conversational — AI-powered Q&A about flood risk

**Design question:** How do these modes link? Can the home map lead into the story? Can the story surface the explorer? Apply circular journey principle.

### WS6: Agent & AI Integration
**Objective:** Define how Claude tool-use adds value beyond what the map alone provides.

Not for MVP implementation, but for architecture:
- What questions would citizens ask that the map can't answer? ("Is my street at risk?" "Should I worry about next week's forecast?" "What happened in my município?")
- What tools does the agent need? (query precondition index, fetch IPMA warnings, look up historical events, explain methodology)
- How does the agent relate to the visual modes? (Agent as Mode 3, or agent as companion across all modes?)

## Output format

Write the design document as a markdown file at:
```
~/Documents/dev/cheias-pt/docs/design-document.md
```

Structure it with:
1. **Vision statement** (2-3 sentences — what cheias.pt IS)
2. **Elena's Four Questions** (answered)
3. **Workstreams** (WS1-WS6 as described above, each with objective, approach, deliverables, dependencies, open questions)
4. **Sequencing** (what can be parallelized, what blocks what, suggested sprint structure)
5. **Technical decisions log** (key architectural choices that need to be made, with options and tradeoffs)
6. **References** (link to skill, research files, blog posts that inform decisions)

## Constraints

- Use Portuguese for user-facing copy examples (headlines, labels, status text).
- Don't write code. This is a planning document.
- Think like a studio that has done 15+ environmental platforms (Vizzuality's track record) combined with a team that builds cloud-native geospatial infrastructure (DevSeed's strength). Where do those two perspectives diverge or complement?
- The retrospective story (WS2) is the flagship deliverable — it's what gets shared, what journalists link to, what demonstrates the platform's value. Prioritize accordingly.
- Keep total document under 3000 words. Dense, not padded.
