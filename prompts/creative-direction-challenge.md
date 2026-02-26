# Creative Direction: Challenge Round

## Context for This Chat

We've been through two rounds of creative direction for cheias.pt — a flood geo-narrative
for Portugal targeting Development Seed as portfolio piece, benchmarked against Vizzuality's
work. The agent research is solid. The creative direction plan (v1) has good storytelling
bones but anchored too conservatively on architecture and technology choices.

This chat picks up where the last left off. Don't re-run research. Challenge and evolve.

## Read These Files (in order)

### The plan to challenge
1. `prompts/creative-direction-plan.md` — 523 lines. Read it all. Sections 2-4 (story arc,
   effects, untapped data) are strong. Section 6 (architecture) is the weak link.

### Agent research (completed, reusable)
2. `prompts/creative-reports/library-compatibility.md`
3. `prompts/creative-reports/data-catalogue.md`
4. `prompts/creative-reports/effect-audit.md`

### Design references
5. `data/design-vision.md` — narrative architecture + visual identity (constraint-free extract)
6. `data/video-analysis/MOTION-ANALYSIS.md` — 6 visual effects spec
7. `~/.vaults/root/2nd-Brain/Projects/vizzuality-methodology/` — ALL 8 files (quality bar)
8. `deckgl-dynamic-mapping-examples.md` — library palette

### What exists in the repo
9. `deckgl-prototype.html` — deck.gl spike (technical exploration, not a product)
10. `src/` + `index.html` — v0 scrollytelling (~1,800 lines vanilla JS, flat, no dynamic effects)
11. `CLAUDE.md` — slim project context

## What Went Wrong (Specific Decisions to Challenge)

### 1. "No npm, no bundler" for v0

The plan proposes CDN-loading scrollama + GSAP + ScrollTrigger + d3-contour + Observable
Plot + geotiff.js + deck.gl UMD + MapLibre — all via `<script>` tags and `esm.sh` imports.
This is already 7+ external dependencies with version pinning managed by... nothing. One
CDN outage or version conflict breaks the whole thing.

Meanwhile, `npm create vite@latest` takes 30 seconds and gives: dependency management,
tree-shaking, hot reload, TypeScript if wanted, and — critically — unlocks every npm
package that needs a bundler. Including deck.gl-raster (DevSeed's own GPU COG renderer).

**Challenge this.** Is there any real reason NOT to start with Vite? The "static deploy"
requirement is met by `vite build` → dist/ → any static host. What does CDN-only buy
that Vite doesn't, other than familiarity with the old approach?

Look at what Vizzuality, DevSeed, The Pudding, and NYT Graphics actually use. Check
their GitHub repos. They don't ship CDN script-tag apps.

### 2. "Keep custom code" for wind particles

The plan says keep the hand-rolled particle advection system (CPU-based, PathLayer trails,
bilinear interpolation) because deck.gl-particle is deprecated and WeatherLayers GL needs
a license.

But with a bundler, the landscape changes. What about:
- deck.gl-particle v1.1.0 itself — deprecated but functional. With Vite, the deck.gl v8/v9
  compatibility issue might be resolvable via aliasing or a thin adapter
- WeatherLayers GL's open-source core (MPL-2.0 licensed parts)
- mapbox-gl-wind or derivatives adapted for MapLibre
- The PNG wind texture pattern from deck.gl-particle's README — could be implemented as a
  custom deck.gl layer without importing the deprecated package
- WebGL wind rendering approaches (the pattern, not the package)

The question isn't "which package do we npm install" — it's "what's the most visually
impressive wind rendering achievable in 2 days with existing libraries?"

### 3. No 3D visualization anywhere

Vizzuality's methodology includes 3D as a key capability (Half-Earth globe, terrain
exaggeration, 3D building occlusion in urban scenes). The plan is entirely 2D.

For a flood narrative, 3D opportunities include:
- **Globe view** for Chapter 2 (Atlantic scale) — MapLibre v5 globe projection or deck.gl
  GlobeView. The atmospheric river wrapping around the Earth is more dramatic in 3D.
- **Terrain exaggeration** — MapLibre terrain with exaggerated hillshade shows WHY water
  flows where it does. River valleys become visible. Flood plains are obvious.
- **deck.gl ColumnLayer** for discharge stations — 3D columns rising as river levels rise.
  Physical metaphor: water RISING.
- **Pitch and bearing** in camera transitions — the plan mentions pitch 15-45 in chapter
  cameras but doesn't exploit this for 3D terrain interaction.
- **3D flood depth** — if terrain + flood extent exist, the difference IS flood depth.
  Exaggerated 3D flood surface over terrain would be visceral.

**Challenge: what 3D elements would most improve the storytelling, and what do they require?**
MapLibre v5 globe + terrain are built-in. deck.gl v9 supports globe view natively.
No special libraries needed — just enabling what's already available.

### 4. Synoptic composite "deferred to Phase 3"

The plan punts Effect 5 (synoptic charts + radar) entirely. But elements of it are achievable:
- Dynamic MSLP contours (already planned via d3-contour) ARE synoptic chart elements
- Frontal boundaries could be 3-4 hand-drawn GeoJSON LineStrings with styled symbology
- The plan already suggests combining Effects 1+2+3 creates a "synoptic-like" experience

The question is: with d3-contour isobars + wind particles + precipitation sweep + satellite,
are we actually 80% of the way to a synoptic composite already? What's the minimal addition
that gets us to "meteorologist-recognizable"?

### 5. TripsLayer for atmospheric river — but how?

The plan's most creative idea is using deck.gl TripsLayer for the atmospheric river (Ch. 2).
But it doesn't explain the data pipeline. TripsLayer needs waypoints with timestamps:
```
[{ path: [[lon1,lat1],[lon2,lat2],...], timestamps: [t1,t2,...] }]
```

How do you get from IVT COGs (a scalar field of moisture flux magnitude) to animated
waypoints that trace the river's path? This is a non-trivial data transformation:
- Trace the IVT maximum ridge across timesteps?
- Generate synthetic particle tracks through the IVT field?
- Use flowmap.gl instead (designed for flow visualization)?

**Challenge: is TripsLayer actually the right tool, or is there something better?**

### 6. The v0 src/ — evolve or scrap?

The existing `src/` has 1,800 lines of vanilla JS with chapter configs, scroll observer,
layer manager, MapLibre setup. The plan says "graduate to multi-file CDN" which is basically
the same architecture with CDN scripts added.

If we're recommending Vite, does the v0 code port cleanly? Or is it simpler to scaffold
fresh with Vite + the narrative structure from the design vision, pulling in only the pieces
worth keeping (chapter text, camera positions, data loader patterns)?

## What I Want From This Chat

Produce `prompts/creative-direction-plan-v2.md` that:

1. **Makes the architecture decision.** Vite or not. Framework or vanilla. Justify it by
   looking at what the target companies (DevSeed, Vizzuality) actually ship.

2. **Resolves the wind particle question.** Best visual result achievable with existing
   libraries + bundler. Don't default to "keep custom code" without exhausting alternatives.

3. **Adds 3D where it serves the story.** Globe for Ch.2, terrain for Ch.5/6, columns for
   discharge, pitch exploitation throughout. What's the minimum 3D that satisfies
   Vizzuality's quality bar?

4. **Clarifies the TripsLayer/flowmap.gl question** for the atmospheric river. What's the
   data pipeline? Is TripsLayer the right choice or is there something more natural?

5. **Closes the synoptic gap** — what minimal additions to the already-planned effects
   create a meteorologist-recognizable composite?

6. **Keeps everything else from v1 that works.** The story arc (sections 2-4) is strong.
   The chapter-by-chapter design is good. The untapped data priorities are correct. The
   wildfire reveal is the gem. Don't redesign what's already well-designed — challenge
   what was too conservative.

7. **Updates the implementation phases** to reflect the architectural and technology changes.

## Constraints (same as before)

- Open source only, but any open source. Build steps welcome.
- The audience is Development Seed engineers.
- The visual bar is Vizzuality's published work (including their 3D capabilities).
- Don't pre-filter ideas by difficulty.
- Infrastructure exists: titiler at titiler.cheias.pt, R2 for COGs, PMTiles ready.
- Portuguese narrative text is good — keep it.
