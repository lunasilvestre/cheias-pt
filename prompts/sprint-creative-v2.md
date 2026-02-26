# Sprint Planning: cheias.pt Creative Direction v2

## Mission

Execute the creative direction plan at `prompts/creative-direction-plan-v2.md`. This is
the approved plan — read it end to end before doing anything.

## Reference Files (read in this order)

### The Plan (source of truth for this sprint)
1. `prompts/creative-direction-plan-v2.md` — approved creative direction with architecture
   decisions, phased implementation, technology choices

### Agent Research (background — consult as needed, don't re-run)
2. `prompts/creative-reports/library-compatibility.md` — library CDN/npm compatibility matrix
3. `prompts/creative-reports/data-catalogue.md` — full data inventory with storytelling notes
4. `prompts/creative-reports/effect-audit.md` — gap analysis of current prototype vs. spec

### Design References (the quality bar and story)
5. `data/design-vision.md` — narrative architecture, chapter storyboard, visual identity
6. `data/video-analysis/MOTION-ANALYSIS.md` — 6 visual effects spec from WeatherWatcher14
7. `~/.vaults/root/2nd-Brain/Projects/vizzuality-methodology/` — 8 files, Vizzuality quality bar
8. `deckgl-dynamic-mapping-examples.md` — library palette

### Existing Code (what we're building on)
9. `src/` + `index.html` — v0 scrollytelling (1,800 lines vanilla JS, chapter configs,
   scroll observer, layer manager). Port to Vite, don't rewrite from scratch.
10. `deckgl-prototype.html` — deck.gl spike. Proven patterns: geotiff.js COG pipeline,
    BitmapLayer rendering, MapboxOverlay integration, crossfade technique. Extract and port
    the useful pieces into the Vite project.
11. `spike-deckgl-raster.html` — geotiff.js + BitmapLayer spike. Reference for COG rendering.

### Infrastructure
12. `CLAUDE.md` — project context (slim version)
13. titiler at `https://titiler.cheias.pt/` — server-side COG rendering, contours, stats
14. R2 at `https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/` — all COGs served
15. PMTiles in `data/flood-extent/`, `data/lightning/`, `data/qgis/` — ready for MapLibre

### Previous Plans (historical context, superseded)
16. `prompts/creative-direction-plan.md` — v1 plan (too conservative, superseded by v2)
17. `CLAUDE-v4-scrollytelling.md` — detailed data pipeline docs (parked, useful for data details)

## Key Architecture Decisions (from v2 plan)

- **Vite from day one** — `npm create vite@latest`, vanilla TypeScript
- **MapLibre v5** — globe projection for Ch.2, terrain for Ch.5-6
- **deck.gl v9** — via npm, not UMD CDN
- **WeatherLayers GL** (MPL-2.0) — GPU particle system, contour, grid, high-low, front layers
- **scrollama + GSAP** — scroll engine + animation
- **d3-contour** — dynamic MSLP isobars from COG data
- **Observable Plot** — inline sparklines in text panels
- **geotiff.js** — COG loading from R2 (proven pipeline)

## Phase Structure (from v2 plan)

Execute phases in order. Each phase should be a focused session.

| Phase | Focus | Key Deliverables |
|-------|-------|-----------------|
| 0 | Vite scaffold + scroll engine | Project structure, scrollama chapters, camera transitions |
| 1 | Data pipelines | MSLP contours, blurred PNGs, wind textures, IVT processing |
| 2 | Core narrative effects | Wind particles, satellite, MSLP isobars, precipitation, 3D |
| 3 | Polish | Entry animation, before/after slider, responsive, accessibility |

Start with Phase 0. Read the v2 plan's Phase 0 section for specific tasks.
