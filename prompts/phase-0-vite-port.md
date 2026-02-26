# Phase 0: Vite Scaffold + Scroll Engine Port

## Mission

Port cheias.pt v0 (1,773 lines across 10 vanilla JS modules + `index.html`) into a Vite + vanilla TypeScript project. Replace the custom scroll observer with scrollama + GSAP. Upgrade MapLibre v4 → v5. The result is the same scrollable narrative — same chapters, same camera positions, same layer configs — running on a modern build stack.

**This is a port, not a redesign.** No new effects. No new chapters. No new data loading. The creative direction plan at `prompts/creative-direction-plan-v2.md` defines the full vision — Phase 0 only builds the foundation.

## Architecture Constraints (non-negotiable)

These come from the v2 plan's challenge findings. Do not deviate:

- **Vite + vanilla TypeScript.** No React, no Svelte, no framework. TypeScript modules with direct MapLibre/deck.gl calls. The target audience (Development Seed, Vizzuality) ships React — but cheias.pt is a single-page scroll narrative with no user accounts, no forms, no component reuse. React would add 45KB overhead and a virtual DOM layer between us and MapLibre for zero benefit.
- **MapLibre GL JS v5** (not v4). Globe projection must be available for Phase 2 (Ch.2 atmospheric river). Don't use globe yet — just ensure v5 is installed and the map initializes correctly on mercator.
- **deck.gl v9 via npm** (not CDN/UMD). Install `deck.gl`, `@deck.gl/geo-layers`, `@deck.gl/aggregation-layers`. Don't use deck.gl layers yet — just ensure `MapboxOverlay` integration with MapLibre v5 works (render a single empty overlay to verify).
- **scrollama** replaces the custom `IntersectionObserver` in `scroll-observer.js`. Use the sticky graphic pattern: fixed map, scrolling text panels.
- **GSAP + ScrollTrigger** for animation polish. Wire to scrollama step events for text reveal animations and number tickers. Basic wiring only — fancy animations come in Phase 2.
- **geotiff.js** stays as the COG loader. Port `data-loader.js` as-is.
- **WeatherLayers GL, d3-contour, Observable Plot** — install via npm but do NOT integrate yet. They're Phase 2 dependencies. Having them in `package.json` is enough.

## Existing Code Inventory

Read these files before writing any code:

| v0 File | Lines | What It Does | Port Target |
|---------|-------|-------------|-------------|
| `src/story-config.js` | ~300 | Chapter definitions: id, title, text, camera, layers, legend, callbacks | `src/chapters.ts` — add TypeScript interfaces, keep all chapter data verbatim |
| `src/scroll-observer.js` | ~120 | Custom IntersectionObserver triggering chapter transitions | `src/scroll-engine.ts` — REPLACE with scrollama. This is the biggest change. |
| `src/map-controller.js` | ~200 | MapLibre init, flyTo, setLayoutProperty, setPaintProperty | `src/map-setup.ts` — upgrade MapLibre v4→v5 API. Check for breaking changes. |
| `src/layer-manager.js` | ~250 | Layer creation, opacity transitions, crossfade, source management | `src/layer-manager.ts` — port directly. Don't add WeatherLayers GL yet. |
| `src/chapter-wiring.js` | ~150 | Connects chapters to map actions | Merge into `src/scroll-engine.ts` — scrollama callbacks replace this |
| `src/data-loader.js` | ~200 | COG loading via geotiff.js, JSON fetching, image preloading | `src/data-loader.ts` — port directly |
| `src/temporal-player.js` | ~180 | Timeline UI for temporal animation | Merge into `src/scroll-engine.ts` — scroll-driven instead of timeline UI |
| `src/exploration-mode.js` | ~100 | Ch.9 free exploration unlock | `src/exploration-mode.ts` — port directly |
| `src/main.js` | ~120 | Entry point, orchestration | `src/main.ts` — update imports, wire scrollama |
| `src/utils.js` | ~50 | Small helpers | Inline into relevant modules or `src/types.ts` |
| `index.html` | ~400 | Chapter divs, hero title, control panel | Port to project root `index.html` with Vite script tag |

Also read:
- `deckgl-prototype.html` — deck.gl spike. Extract the `MapboxOverlay` integration pattern for `map-setup.ts`. Don't port the full prototype.
- `prompts/creative-direction-plan-v2.md` §1 "Project Structure" — target directory layout.

## Tasks and Acceptance Criteria

### Task 0.1: Scaffold Vite Project

**Do:**
```bash
npm create vite@latest cheias-pt-v2 -- --template vanilla-ts
cd cheias-pt-v2
npm install maplibre-gl@^5 deck.gl @deck.gl/geo-layers @deck.gl/aggregation-layers
npm install weatherlayers-gl geotiff
npm install scrollama gsap d3-contour d3-geo @observablehq/plot
npm install @maplibre/maplibre-gl-compare
```

**Create the directory structure:**
```
cheias-pt-v2/
  index.html
  vite.config.ts
  tsconfig.json
  package.json
  src/
    main.ts
    chapters.ts
    scroll-engine.ts
    map-setup.ts
    layer-manager.ts
    data-loader.ts
    exploration-mode.ts
    types.ts
  css/
    style.css
  public/
    assets/
```

**Symlink or copy data directories** from the existing project so `data/`, `assets/` are accessible.

**Acceptance criteria:**
- [ ] `npm run dev` starts Vite dev server with no errors
- [ ] `npm run build` produces `dist/` with no TypeScript errors
- [ ] Browser shows an empty page at localhost (no content yet)

---

### Task 0.2: Port v0 Modules to TypeScript

Port each module from `src/*.js` → `src/*.ts` following the mapping table above.

**Rules:**
- Add TypeScript interfaces for chapter configs, layer configs, camera positions. Put shared types in `types.ts`.
- Keep ALL chapter data verbatim from `story-config.js` — titles, Portuguese text, camera coordinates, layer arrays. Do not edit, translate, reformat, or "improve" the content.
- Where v0 uses `document.getElementById` or DOM manipulation, keep it. This is vanilla TS, not React.
- Where v0 references MapLibre API, update to v5 syntax if needed (check MapLibre v4→v5 migration guide).
- `chapter-wiring.js` and `temporal-player.js` merge into `scroll-engine.ts` — their logic is absorbed by scrollama callbacks.
- `utils.js` — inline small helpers into the modules that use them. If anything is shared, put it in `types.ts`.

**Acceptance criteria:**
- [ ] `tsc --noEmit` passes with zero errors (strict mode)
- [ ] Every chapter from `story-config.js` exists in `chapters.ts` with identical data
- [ ] All imports resolve (no circular dependencies)
- [ ] `npm run dev` shows the map with the basemap loading

---

### Task 0.3: MapLibre v4 → v5 Upgrade

**Do:**
- Check the MapLibre v5 changelog for breaking changes vs v4.
- Update `map-setup.ts` for any API changes.
- Verify `new maplibregl.Map()` initializes correctly with v5.
- Add `projection: 'mercator'` explicitly (default, but making it explicit prepares for Phase 2's globe switch).
- Integrate deck.gl v9 via `MapboxOverlay` — render an empty overlay to verify the integration works. Pattern from `deckgl-prototype.html`:

```typescript
import { MapboxOverlay } from '@deck.gl/mapbox';

const deckOverlay = new MapboxOverlay({ layers: [] });
map.addControl(deckOverlay);
```

**Acceptance criteria:**
- [ ] Map renders with MapLibre v5 (check `maplibregl.version` in console)
- [ ] deck.gl MapboxOverlay is attached (no console errors)
- [ ] Camera flyTo works between chapters
- [ ] No WebGL errors in console

---

### Task 0.4: Replace Scroll Observer with scrollama

**Do:**
- Remove the custom `IntersectionObserver` logic from v0.
- Install and wire scrollama with the sticky graphic pattern:
  - `.scroll-container` wraps everything
  - `.sticky-graphic` contains the fixed map
  - `.scroll-text` contains the chapter step divs
- Each chapter div gets a `data-step` attribute matching the chapter id.
- scrollama's `onStepEnter` triggers the camera transition + layer changes from `chapters.ts`.
- scrollama's `onStepProgress` passes normalized progress (0→1) for scroll-driven animations.

**Do NOT:**
- Add scroll-driven animation logic beyond basic wiring. Phase 2 adds the actual effects.
- Change the chapter order or structure.

**Acceptance criteria:**
- [ ] Scrolling through the page triggers chapter transitions (camera moves, basemap visible)
- [ ] Each chapter's `onStepEnter` fires exactly once per scroll direction
- [ ] `onStepProgress` reports 0.0 → 1.0 as the user scrolls through each step
- [ ] Scroll position is correct on page reload (scrollama handles this)
- [ ] No double-firing of transitions

---

### Task 0.5: Add GSAP + ScrollTrigger

**Do:**
- Wire GSAP to scrollama step events for basic text reveal animations:
  - Chapter titles fade in from below (translateY + opacity)
  - Chapter text paragraphs stagger in
  - Number values (discharge, area, etc.) count up from 0 to target
- Register ScrollTrigger plugin.

**Do NOT:**
- Add complex timeline animations. This is foundation wiring only.
- Animate map layers with GSAP (that's the scroll-engine's job via MapLibre/deck.gl APIs).

**Acceptance criteria:**
- [ ] Chapter titles animate on scroll entry
- [ ] Text paragraphs stagger in (not all at once)
- [ ] At least one numeric counter animates (e.g., "11 mortes" counting up)
- [ ] Animations respect `prefers-reduced-motion` (skip to final state)

---

### Task 0.6: Basemap Aesthetics

**Do:**
- Background color: `#0a212e` (dark oceanic, from design vision)
- Map container fills viewport (100vw × 100vh fixed position)
- Text panels: semi-transparent dark background with glassmorphism blur (`backdrop-filter: blur(12px)`)
- Typography: serif font for chapter titles (system serif stack or load a web font), sans-serif for body text
- Text color: off-white `#e8e8e8`, accent color for highlights
- Scrollbar: thin, subtle, doesn't break the dark aesthetic

**Acceptance criteria:**
- [ ] Page background is dark (#0a212e or similar)
- [ ] Text panels have glass-like translucent background over the map
- [ ] Typography uses serif for titles, sans-serif for body
- [ ] No default browser chrome (white backgrounds, system scrollbars) leaking through

---

### Task 0.7: Integration Verification

This is the final checkpoint. Verify the complete scroll narrative works end to end.

**Acceptance criteria — ALL must pass:**
- [ ] `npm run dev` starts with zero console errors
- [ ] `npm run build` succeeds with zero TypeScript errors
- [ ] Scrolling from top to bottom visits every chapter in order
- [ ] Each chapter triggers its camera transition (flyTo with correct center/zoom/pitch/bearing)
- [ ] Chapter text animates in on entry
- [ ] The map is visible behind translucent text panels at all times
- [ ] MapLibre v5 is confirmed (log `maplibregl.version`)
- [ ] deck.gl MapboxOverlay is attached (log confirmation)
- [ ] No layer rendering yet is fine — layers come in Phase 2
- [ ] Page loads in <3 seconds on localhost
- [ ] Works in Chrome and Firefox

## What NOT to Do

- Do NOT add WeatherLayers GL integration (Phase 2)
- Do NOT render wind particles, isobars, or any effects (Phase 2)
- Do NOT load COG data or render raster layers (Phase 2)
- Do NOT implement the globe projection (Phase 2, Ch.2)
- Do NOT add terrain or 3D columns (Phase 2, Ch.5-6)
- Do NOT add the before/after satellite slider (Phase 3)
- Do NOT add responsive/mobile layout (Phase 3)
- Do NOT refactor chapter content or Portuguese text
- Do NOT "improve" the v0 code beyond what's needed for TypeScript + Vite + scrollama

## Verification Command

After completing all tasks, run:
```bash
npm run build && echo "BUILD OK" || echo "BUILD FAILED"
npx tsc --noEmit && echo "TYPES OK" || echo "TYPE ERRORS"
```

Both must print OK.

## Files to Read First (in order)

1. `src/story-config.js` — understand the chapter structure you're preserving
2. `src/scroll-observer.js` — understand what scrollama replaces
3. `src/map-controller.js` — understand the MapLibre integration you're upgrading
4. `src/main.js` — understand the orchestration flow
5. `deckgl-prototype.html` — extract the MapboxOverlay pattern (lines ~50-80)
6. `index.html` — understand the HTML structure being ported
