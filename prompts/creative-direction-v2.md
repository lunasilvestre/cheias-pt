# Creative Direction: Synthesis (Round 2)

You are the creative director from the previous session. Your three research
teammates already delivered their reports. The creative direction plan from
round 1 was too conservative — it anchored to implementation constraints from
an earlier project phase and proposed a v0 that already exists.

This time: think bigger. Design the product you'd actually want to ship.

## Read These (in order)

### Agent research (already completed — use as inputs, don't redo)
1. `prompts/creative-reports/library-compatibility.md` — library capabilities, integration paths
2. `prompts/creative-reports/data-catalogue.md` — full data inventory
3. `prompts/creative-reports/effect-audit.md` — current prototype gaps vs. design spec

### Design references
4. `data/design-vision.md` — narrative architecture, chapter storyboard, visual identity.
   This contains the STORYTELLING vision (chapters, emotional arc, camera positions,
   Portuguese copy). Treat it as creative inspiration, not as a technical spec.
5. `data/video-analysis/MOTION-ANALYSIS.md` — 6 visual effects from WeatherWatcher14
6. `~/.vaults/root/2nd-Brain/Projects/vizzuality-methodology/` — all 8 files. This is
   the quality bar.
7. `deckgl-dynamic-mapping-examples.md` — library palette

### What already exists in the repo
8. `deckgl-prototype.html` — a deck.gl + MapLibre spike exploring dynamic raster rendering,
   wind particles, COG-from-R2, crossfades. This was a TECHNICAL EXPLORATION, not a product.
   Good things to carry forward: geotiff.js pipeline, BitmapLayer rendering, MapboxOverlay
   integration. Not a foundation to preserve — a spike to learn from.

9. `src/` directory + `index.html` — a v0 scrollytelling attempt (~1,800 lines vanilla JS).
   Chapter structure, IntersectionObserver scroll triggers, MapLibre camera transitions,
   Portuguese copy for all 9 chapters. It works but it's flat — no dynamic effects, no
   deck.gl layers, no temporal animation. Minimal visual impact. This is what "too
   conservative" looks like. The chapter TEXT and narrative structure are good; the
   implementation approach may or may not be worth building on.

### Infrastructure (capabilities, not constraints)
10. **titiler** deployed at `https://titiler.cheias.pt/` — server-side COG rendering,
    dynamic colormaps, contour generation, point queries, statistics. Useful for operations
    that are expensive or impossible client-side. Don't ignore it — but don't make everything
    depend on it either.
11. **Cloudflare R2** — COGs served at `https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/`.
    Proven fast, CORS-enabled, supports HTTP range requests for geotiff.js.
12. **PMTiles** — flood extent, lightning, wildfires available as PMTiles. MapLibre can
    consume these directly as vector tile sources (no tile server needed).

## What Went Wrong in Round 1

The plan proposed rebuilding the existing v0 scrollytelling with minor improvements and
"deferring deck.gl integration to later." This is backwards. The v0 already exists. The
dynamic effects and visual impact ARE the point — they're what separates a developer demo
from a Vizzuality-grade product. The plan also inherited the design document's "vanilla JS,
no build tools, static deploy" constraints as if they were immutable.

## What I Want This Time

A creative direction plan saved to `prompts/creative-direction-plan-v2.md` with:

1. **Architecture decision**: single HTML? vanilla JS modules? Vite + Svelte? Next.js?
   What does the creative vision require? Look at what Vizzuality, The Pudding, DevSeed,
   and NYT Graphics actually ship on. Make a recommendation and justify it. If the v0
   `src/` structure is worth evolving, say so. If it should be scrapped for a framework
   that unlocks better libraries, say that too.

2. **Story arc design**: Map chapters 0-9 from the design vision to CONCRETE visualization
   designs. For each chapter: what's the hero visual? What library renders it? What data
   feeds it? What's the camera doing? What's the emotional beat? Don't just say "soil
   moisture animation" — say which library, which layer type, what the transition between
   chapters looks like, how scroll position controls the animation.

3. **The 6 effects, placed in context**: Each of the motion analysis effects exists to
   serve a specific chapter. Map them. Then for each: which existing library or deck.gl
   layer delivers it? What data format does it need? Is there pre-processing required?

4. **Data pipeline**: What pre-processing turns our raw data (COGs, GeoJSON, Parquet,
   NetCDF) into the formats the visualization libraries expect? Be specific: "convert
   wind U/V COGs to PNG textures for deck.gl-particle" or "pre-compute MSLP contour
   GeoJSONs per timestep using d3-contour offline." What should happen at build time
   vs. client-side?

5. **Untapped data**: What's in the data catalogue that isn't in any existing prototype
   but would transform the storytelling? Map each to a chapter.

6. **Phased implementation plan**: Ordered by narrative coherence, not effort. What needs
   to exist first for the story to work, regardless of difficulty.

## Constraints (real ones)

- Open source only, but any open source. Build steps are fine.
- The audience is Development Seed engineers.
- The visual bar is Vizzuality's published work.
- Don't pre-filter ideas by difficulty. Full creative vision first.
- Infrastructure exists (titiler, R2, PMTiles). Use it where it helps.
- The Portuguese narrative text from the design vision is good — keep it.
