# Prompt A — Smooth Foundations: Crossfades + Camera Transitions

## Context

You are working on `deckgl-prototype.html` in the `cheias.pt` project — a flood monitoring scrollytelling platform for Portugal. This is a DevSeed portfolio piece demonstrating cloud-native geospatial skills. The file is a single-file layer viewer using MapLibre GL + deck.gl.

**Current state:** The prototype has raster frame animation (soil moisture + precipitation) but uses hard `updateImage()` swaps — no crossfade. Layer toggles are instant show/hide. No camera transitions.

**Goal:** Make the existing interactions feel polished and professional. No new data sources or layers — purely UX refinement.

Read `deckgl-prototype.html` first to understand the existing code structure.
Read `data/video-analysis/MOTION-ANALYSIS.md` → Effect 6 (Layer Transitions and Timeline) for the visual spec.

## Task 1: Raster Frame Crossfade

Replace the hard `updateImage()` frame swap with smooth dual-layer crossfade:

1. For each raster type (soil-moisture, precipitation), create TWO MapLibre image sources: `-a` and `-b`
2. Add two raster layers per type, stacked (e.g., `sm-layer-a` above `sm-layer-b`)
3. Track which source is "active" per layer type (a boolean flag)
4. On frame advance in `setDate()`:
   - Load the new date's PNG into the INACTIVE source via `updateImage()`
   - Animate opacity: active layer 0.8→0, inactive layer 0→0.8 over 400ms using `requestAnimationFrame`
   - Flip the active flag
5. The crossfade must work during play mode (200ms timer). If a new frame arrives before crossfade completes, snap the current transition and start the next one.
6. Update `LAYER_MAP` and `syncVisibility()` to handle both sub-layers per type

**Visual target:** Smooth "dissolve" between frames like Windy.com (from the MOTION-ANALYSIS doc). No flash or pop.

## Task 2: Layer Toggle Crossfade

Replace instant `visibility: visible/none` with animated opacity transitions:

1. Keep all MapLibre layers permanently `visibility: 'visible'` (never toggle layout visibility)
2. Each layer type stores a target opacity (e.g., `sm: 0.8`, `mslp-lines: 0.6`, etc.)
3. When toggling OFF: animate paint opacity from target → 0 over 300ms
4. When toggling ON: animate paint opacity from 0 → target over 300ms
5. Map the paint properties per layer type:
   - Raster layers: `raster-opacity`
   - Line layers: `line-opacity`
   - Circle layers: `circle-opacity`
   - Symbol layers: `text-opacity` + `icon-opacity`
6. For deck.gl layers (arcs, wind), use the `opacity` parameter in layer props and rebuild via `updateDeck()`. Animate using `requestAnimationFrame`.
7. Create a reusable `animateOpacity(layerId, property, from, to, duration)` function to avoid duplication

## Task 3: Camera Preset Buttons

Add flyTo() camera presets below the layer panel:

1. Add a new panel `#camera` below `#layers` with 3 buttons:
   - "Atlantic" → `center: [-20, 42], zoom: 4`
   - "Iberia" → `center: [-5, 39.5], zoom: 5.5`
   - "Portugal" → `center: [-8, 39.5], zoom: 6.5`
2. Each triggers `map.flyTo({ center, zoom, duration: 2000, essential: true })`
3. Style to match existing dark glass panels: `rgba(12,12,20,0.88)`, `backdrop-filter: blur(12px)`, `border: 1px solid rgba(255,255,255,0.08)`, `border-radius: 10px`
4. Buttons styled as small pills: `background: rgba(255,255,255,0.06)`, `border: 1px solid rgba(255,255,255,0.12)`, hover brightens, font-size 11px, letter-spacing 0.5px

## Constraints

- Single HTML file, all JS inline
- MapLibre GL ^4.0 + deck.gl ^9.0 (already loaded via CDN)
- No build step — must work with `python3 -m http.server` from project root
- Preserve ALL existing functionality (layers, toggles, timeline, keyboard controls)
- Dark aesthetic: keep the existing panel style language

## Success Criteria

1. Scrub the timeline → frames dissolve smoothly (no flash between dates)
2. Hit play → continuous smooth animation without stutter
3. Toggle any layer checkbox → it fades in/out over ~300ms
4. Click "Atlantic" → camera smoothly flies to wide Atlantic view over ~2s
5. All existing keyboard shortcuts (space, arrows) still work
