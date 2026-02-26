# Effect Audit: MOTION-ANALYSIS.md Spec vs. Prototype Implementation

**Date:** 2026-02-26
**Auditor:** Effect Auditor (creative direction planning phase)
**Spec:** `data/video-analysis/MOTION-ANALYSIS.md` (6 effects from WeatherWatcher14 Storm Kristin video)
**Prototype:** `deckgl-prototype.html` (1,360 lines, single-file MapLibre + deck.gl v9 spike)
**Quality bar:** Vizzuality methodology (8 files: design philosophy, visual system, scrollytelling, performance, trust, anti-patterns, portfolio)
**Design vision:** `discovery/12-design-document.md` (9-chapter scroll-driven geo-narrative)

---

## 1. Executive Summary

The prototype is a capable technical spike that proves the data pipeline works: COGs load from R2, temporal scrubbing advances frames, particles advect through wind fields, and layer toggles animate opacity. As an engineering proof-of-concept, it succeeds. As a visual experience, it falls substantially short of both the MOTION-ANALYSIS.md spec and the Vizzuality quality bar.

The core gap is not missing features -- most effects have *some* implementation. The gap is **visual refinement**: particle density too low by default, trail rendering lacks per-segment opacity decay, crossfade timing not calibrated to narrative pacing, color ramps not tuned to the reference video's vivid psychedelic quality, no temperature field beneath isobars, no gaussian-blurred edges on precipitation, static contours drifting from temporal rasters, wind "barbs" that are just direction arrows without meteorological notation, and zero camera choreography tied to narrative chapters. The prototype is a layer viewer with a timeline; the spec describes an atmospheric, emotionally engaging weather visualization. The distance between these two is the creative direction work that lies ahead.

Against Vizzuality's bar specifically: the prototype lacks the Delight phase entirely (no entry animation, no emotional typography, no serif hero title), the glassmorphism panels use the wrong background color and opacity, there is no scroll-driven narrative, no progressive disclosure, no institutional attribution, and the basemap background is `#0a0a0a` (pure near-black) instead of the spec's `#0a212e` (deep navy). These are not nitpicks -- they are structural deviations from the methodology that governs the project's target audience.

---

## 2. Per-Effect Audit

---

### Effect 1: Wind Particle Streamlines

#### A. Specification Summary

**Source reference:** WeatherWatcher14 0:04-0:10 (reprise 4:30-4:40), Windy.com jet stream layer.

The spec describes continuous particle streamlines (not discrete dots) flowing through upper-level wind fields. Key properties:

- **Particle count:** 5,000-20,000 for full-screen density. Denser in high-speed regions, sparser in calm areas. The density variation itself communicates flow structure.
- **Trail length:** 10-20px comet-like trails per particle. Trails fade with distance using exponential decay. "This is critical to the visual -- without trails, individual particles would be invisible."
- **Trail rendering:** Elongated streaks/ribbons, not point-like. Trail length encodes speed (longer = faster).
- **Speed multiplier:** ~2-4 px/frame at 30fps for jet stream core. Peripheral flow slower. Clear velocity gradient.
- **Color ramp:** Purple/magenta = highest wind speed, green = moderate, yellow = low, cyan/blue = calm. "Psychedelic swirl effect where the jet stream is a vivid purple-white ribbon cutting through green/yellow background."
- **Background:** Color field BEHIND particles showing smooth wind speed gradient. Particles add texture to an already-colored background.
- **Opacity/blending:** Semi-transparent, overlaid on subtle terrain basemap.
- **Spawn rate:** Replace ~5% of particles per frame.
- **Fade:** Exponential decay on trail opacity.
- **Projection:** Globe/orthographic adds depth; jet stream wraps around Earth.
- **Data:** Wind U/V COGs (409 files each, ERA5 0.25 deg).

#### B. Current Implementation Status

**Layer present:** Yes. `PathLayer` with id `'wind-particles'` (line 749).

**Particle system:**
- `windParticleCount = 2000` (line 436). Slider allows 500-10,000 (line 212: `min="500" max="10000"`).
- `MAX_TRAIL = 12` (line 529) -- stores 12 trail positions per particle.
- `MAX_AGE = 150` (line 530), `SPEED_MULT = 0.001` (line 531).
- Bilinear interpolation of U/V field via `sampleWind()` (line 551).
- Spawn: uniform random within `WIND_BOUNDS = [-35, 28, 5, 56]` (line 528).
- Despawn: age > MAX_AGE, out of bounds, speed < 0.5, or stochastic 3% after age 30 (lines 602-608).
- Animation: `requestAnimationFrame` loop at ~30fps (33ms threshold, line 615).

**Trail rendering:**
- Each particle's `trail` array rendered as a `PathLayer` path (line 752: `getPath: d => d.trail`).
- Color: `windSpeedColor(d.speed)` -- step function with 4 bands: `<8 -> [0,200,100]`, `<15 -> [255,255,100]`, `<25 -> [255,165,0]`, `>25 -> [180,0,255]` (lines 571-576).
- Opacity: Per-particle age-based fade `Math.max(0.3, 1 - d.age / MAX_AGE)` applied to alpha channel (line 755). Base alpha 180.
- Width: 1.5px, min 1px, max 2.5px (lines 758-760).

**UI controls:**
- Checkbox toggle (id `t-wp`), density slider (500-10,000), wind speed legend with gradient bar.
- Wind field loads from R2 COGs per date+hour selection.

**What is actually rendered:**
- Thin colored paths that flow through the wind field. Visually sparse at default density. Paths are uniform width regardless of speed. No background wind speed color field.

#### C. Visual Deficiency Analysis

1. **Default particle count is 2,000; spec calls for 5,000-20,000.** At default density, the visualization looks thin and unconvincing. The spec emphasizes that "hundreds of particles simultaneously visible" creates the visual impression, and that density variation communicates flow structure. At 2,000 particles across a domain spanning 40 degrees longitude and 28 degrees latitude, coverage is approximately 1.8 particles per square degree -- far too sparse.

2. **Trail opacity is per-particle (age-based), not per-trail-segment (position-based exponential decay).** The spec explicitly calls for "exponential decay on trail opacity" where each trail segment fades from head to tail. Currently, `getColor` computes a single alpha for the entire path based on `d.age / MAX_AGE`. This means a young particle's entire trail is bright, and an old particle's entire trail is dim -- rather than each trail having a bright head and a fading tail. This is the single most impactful visual gap for this effect.

3. **No background wind speed color field.** The spec describes "the color field BEHIND the particles also shows a smooth gradient (the underlying wind speed field), so particles add texture to an already-colored background." The prototype has no wind speed raster layer. The particles float over the bare dark basemap, which dramatically reduces the visual density and the "psychedelic swirl" quality.

4. **Color ramp uses step function, spec implies smooth gradient.** The 4-band step function (`[0,200,100]` -> `[255,255,100]` -> `[255,165,0]` -> `[180,0,255]`) creates discrete color bands. The spec's Windy.com reference uses a smooth, continuous color mapping. The step boundaries at 8/15/25 m/s create visible banding rather than fluid color transitions.

5. **Trail width is uniform (1.5px min/max).** The spec says "trail length encodes speed (longer = faster)" -- but width could also encode speed for a richer visual. More critically, at 1-2.5px, individual trails are barely visible against the dark basemap, especially at low zoom levels.

6. **No globe/orthographic projection.** The spec emphasizes the globe view as adding depth perception. The prototype uses standard Mercator. This is an acceptable trade-off for a flat-map prototype, but it means the "wrapping around the Earth" effect is absent.

7. **Spawn distribution is uniform random, not density-weighted.** The spec notes "denser in high-speed regions, sparser in calm areas." Uniform spawning means the jet stream core has the same initial particle density as calm areas, undermining the visual impression of flow structure.

8. **Spawn rate is not calibrated.** The spec suggests replacing ~5% of particles per frame. The prototype's stochastic despawn (3% after age 30, plus age/bounds/speed culling) is roughly in range but not precisely tuned.

#### D. Vizzuality Quality Gap

Vizzuality's Global Fishing Watch renders millions of vessel tracks with pre-computed rendering properties (worldX, worldY, radius, opacity all in Float32Arrays) at 60fps using sprite pooling. The cheias.pt wind particles use a `PathLayer` that rebuilds geometry every frame via `updateTriggers: { getPath: Date.now(), getColor: Date.now() }` -- this forces a full data re-upload to the GPU every frame. For 2,000 particles this is manageable; for 10,000+ it will degrade performance.

Vizzuality would:
- Use a WebGL custom layer or PIXI-based particle system with sprite pooling
- Pre-compute projected coordinates
- Render trails as GPU line strips with per-vertex alpha (not PathLayer with per-object alpha)
- Include an underlying heatmap layer showing wind speed field (additive blending, SCREEN mode)
- Tune particle density to look dense and immersive at first glance (Mode 1: 5 seconds)

The current implementation feels like a developer demo; Vizzuality's bar is an atmospheric, hypnotic visualization that makes people say "wow" before they understand what it shows.

#### E. Narrative Role

**Serves:** Chapter 2 (The Atlantic Engine) and Chapter 4 (The Storms) in the design document. The jet stream / atmospheric river visualization explains *why* Portugal was hit -- the moisture highway from the Atlantic. The wind particles at Iberian scale (Effect 4 sub-segment A) show the explosive cyclogenesis of Storm Kristin.

**Assessment:** The current particle system works mechanically but lacks the visual impact needed for the "Delight" phase of Elena's emotional engagement sequence. When users first see the Atlantic chapter, the wind visualization should be the "big beautiful globe" moment -- instead, it looks like scattered dots on a dark map. This is the highest-impact visual gap for narrative effectiveness.

---

### Effect 2: Precipitation Temporal Sweep

#### A. Specification Summary

**Source reference:** WeatherWatcher14 0:00-0:04 (Windy flat map) + 4:20-4:32 (forecast bands).

Rain fields as semi-transparent colored areas that advect W-to-E, growing, splitting, dissipating:

- **Color ramp (real-time view):** Light blue/white = light rain, darker blue = moderate, cyan/teal = heavy. "Deliberately muted -- soft watercolor washes rather than hard-edged polygons."
- **Color ramp (accumulation view):** Green ramp (10-300mm scale). "Green bands follow atmospheric river pathways."
- **Opacity:** 50-60% over basemap. Terrain and coastlines remain visible.
- **Edge quality:** "Soft, gaussian-blurred edges -- NO hard boundaries."
- **Trail/fade:** "Leading edge of rain band brightens gradually; trailing edge dissipates. Creates a rolling curtain impression."
- **Crossfade:** 300-500ms between frames for smooth blending.
- **Frame rate:** 2-4 frames/second for temporal sweep.
- **Data:** Pre-rendered PNG frames (77 daily) in `data/raster-frames/precipitation/*.png`, OR COGs from R2.

#### B. Current Implementation Status

**Layer present:** Yes. `RASTER_LAYERS.pr` (line 353) loads COGs from `${R2_BASE}/precipitation/${date}.tif`.

**Crossfade system:**
- A/B dual-buffer (`rasterBuf.pr`) with smoothstep easing (line 795: `t * t * (3 - 2 * t)`).
- Crossfade duration: 150ms during playback, 400ms during manual scrub (line 876: `const dur = playing ? 150 : 400`).
- `crossfadeRaster()` (line 777) animates the active buffer down and inactive buffer up simultaneously.
- `fadeInRaster()` / `fadeOutRaster()` for toggle transitions at 300ms.

**Color mapping:**
- Default colormap: Viridis (`'viridis'`). Swappable via colormap selector dropdown (line 503: `cfg.swappable: true`).
- Viridis ramp (line 308): dark purple -> blue -> green -> yellow. Not the spec's blue/white/cyan.

**Opacity:** `maxOpacity: 0.75` (line 355). Close to spec's 0.5-0.6 range but slightly higher.

**Rendering:** COG fetched -> parsed by geotiff.js -> color-mapped pixel-by-pixel -> rendered to Canvas -> displayed via deck.gl BitmapLayer. Fixed alpha per pixel: 200/255 = ~78% (line 494: `imgData.data[px + 3] = 200`).

**Play mode:** Frames advance every 200ms (line 1241), approximately 5 fps. Slightly faster than spec's 2-4 fps.

#### C. Visual Deficiency Analysis

1. **Color ramp is Viridis (purple-green-yellow), not the spec's blue/white/cyan.** Viridis is a generic scientific colormap; the spec describes a domain-appropriate precipitation palette: "light blue/white = light rain, darker blue = moderate, cyan/teal = heavy." The `bluesLUT` (line 313) is closer to the spec but is not the default -- it must be manually selected via the dropdown. The spec also describes a green accumulation ramp that does not exist in the prototype.

2. **No gaussian-blurred soft edges.** The COG rendering pipeline produces hard grid-cell boundaries. Each pixel is a discrete rectangle with sharp edges. The spec explicitly says "gaussian-blurred edges -- NO hard boundaries" and "soft watercolor washes." This is a fundamental difference in visual quality. The pre-rendered PNG frames in `data/raster-frames/precipitation/*.png` might have smoother edges (depending on how they were generated), but the prototype does not use them.

3. **Crossfade during playback is too fast (150ms) and frame rate too high (5fps).** The spec calls for 300-500ms crossfade at 2-4 fps. At 150ms crossfade and 200ms frame interval, frames barely overlap before the next one starts. This creates a flickering rather than rolling effect. The "rolling curtain impression" requires longer overlap where both frames are simultaneously visible.

4. **Fixed pixel alpha (200/255 = 78%) ignores data magnitude.** Every non-nodata pixel gets the same alpha. In the reference video, light rain areas are more transparent than heavy rain areas. The spec says "50-60% opacity over the basemap" as a baseline, with variation by intensity. The current implementation paints all precipitation pixels at the same opacity regardless of value.

5. **No "rolling curtain" leading/trailing edge effect.** The spec describes rain bands where "leading edge of rain band brightens gradually; trailing edge dissipates." This would require spatial-temporal blending -- possibly rendering two adjacent timesteps with directional opacity gradients -- which is not implemented. The current approach is a hard temporal swap with crossfade.

6. **COG loading is heavier than pre-rendered PNGs.** The 77 daily PNG frames already exist in `data/raster-frames/precipitation/*.png` and are ready for direct use. The prototype instead fetches COGs from R2, parses them with geotiff.js, and color-maps them client-side. This adds latency and computational overhead. For a fixed colormap, pre-rendered PNGs would load faster and could be pre-processed with gaussian blur.

#### D. Vizzuality Quality Gap

Vizzuality's temporal playback (Global Fishing Watch) uses pre-computed rendering properties indexed by time step for instant frame access. The cheias.pt approach fetches a new COG on each frame advance, introducing network latency into the playback loop. Even with the prefetch mechanism (line 884), there is no guarantee the next frame is ready when playback advances.

Vizzuality would:
- Pre-render all frames with proper colormap, gaussian blur, and variable-alpha encoding
- Use a tile-based or atlas approach for instant frame switching
- Calibrate crossfade to the narrative pacing (longer crossfades for storm chapters where the "rolling curtain" matters)
- Use additive blending (SCREEN mode) for precipitation over dark basemap, creating a luminous rainfall effect
- Implement intensity-proportional alpha (light rain = translucent, heavy rain = opaque)

#### E. Narrative Role

**Serves:** Chapter 3 (The Sponge Fills) -- soil moisture + precipitation animation showing progressive saturation -- and Chapter 4 (Three Storms in Two Weeks) -- precipitation accumulation maps.

**Assessment:** The precipitation sweep is the most data-ready effect (77 pre-rendered frames exist) and arguably the simplest to get right. The current implementation works mechanically but looks like a generic raster toggle rather than the atmospheric rainfall visualization the narrative needs. For the "Curiosity" phase ("Why was the ground already full?"), the user needs to see rain progressively washing over Portugal in a way that feels wet and continuous -- not a flickering grid of colored pixels.

---

### Effect 3: MSLP Isobar Animation

#### A. Specification Summary

**Source reference:** WeatherWatcher14 0:28-0:36 (first appearance), 4:40-5:00 (reprise).

Two simultaneous moving layers:

- **Isobar contour lines:** Concentric pressure lines shifting position as low drifts NE. Smooth interpolation, no flickering. White/cream, ~4hPa spacing, consistent stroke width. L/H markers at pressure centers.
- **Temperature color field:** Deep red/salmon = warm (subtropical air), deep blue/navy = cold (polar air), white = boundary. Smooth gradient, NO discrete bands. 70-80% opacity. Basemap faintly visible through.
- **Speed/tempo:** Slow, majestic. Low center moves ~100px over 8 seconds. ~3-6 hours per visible frame advance. Very smooth continuous interpolation between model timesteps.
- **Crossfade:** 500-800ms between frames (slower than precipitation).
- **Depth perception:** Concentric isobars create "bullseye" that draws the eye. Tight gradient near low, spread further out = implied 3D depression.
- **Data needed:** Temperature raster frames (not just MSLP), temporal GeoJSON contours, animated L/H markers.

#### B. Current Implementation Status

**MSLP raster field:** Yes. `RASTER_LAYERS.mslpf` (line 365) loads `${R2_BASE}/mslp/${date}T${h}.tif` per date+hour.
- Colormap: `mslpLUT` (line 321) -- diverging blue-white-red. Rescale `[98000, 104000]` Pa.
- Max opacity: 0.6.
- Hour selector: 4 buttons (00, 06, 12, 18 UTC) at line 250.

**MSLP contours:** Yes. MapLibre `line` layer `'mslp-lines'` (line 1108).
- Source: `data/qgis/mslp-contours-v2.geojson` (SINGLE timestep, 28 isobars).
- Line color: `#ccc`, width 0.8px, opacity animated to 0.6 when visible.
- Symbol labels along lines: `['concat', ['get', 'hPa'], ' hPa']` at 10px.

**L/H markers:** Yes. `'lh-labels'` (line 1130) and `'lh-pressure'` (line 1144).
- Source: `data/qgis/mslp-lh-markers.geojson` (SINGLE timestep, 7 centers).
- L = red (#e74c3c), H = blue (#3498db), 22px text.

**Temperature field:** NOT IMPLEMENTED. No temperature raster layer exists.

#### C. Visual Deficiency Analysis

1. **Contours are STATIC while raster field is TEMPORAL.** This is the most severe visual deficiency for this effect. When the user scrubs through dates, the MSLP color field changes but the contour lines remain fixed at a single timestep. The contours diverge from the underlying field, creating a dissonant and confusing visual. The spec requires contours that "shift position as the low pressure system drifts NE" with "smooth interpolation -- no visible redrawing/flickering."

2. **L/H markers are STATIC.** Same problem as contours. The markers show 7 pressure centers from one moment in time. As the raster field evolves, the L and H labels sit in positions that no longer correspond to actual pressure extremes. The spec requires markers that "follow the pressure center smoothly."

3. **No temperature field layer at all.** The spec identifies the warm/cold boundary as "the most visible motion element" -- the sweep of red (warm) and blue (cold) regions around the frontal boundary. This layer does not exist in the prototype. Only the MSLP pressure field is rendered. The temperature color field is described at 70-80% opacity with the isobars drawn on top -- a fundamentally different visual than MSLP alone.

4. **Contour stroke is too thin and wrong color.** Spec: "white/cream contour lines, ~4hPa spacing, 1.5-2px stroke." Prototype: `#ccc` at 0.8px. At 0.8px the contours are barely visible, especially against the MSLP color field. They should be 2x wider and white rather than gray.

5. **No smooth interpolation between timesteps for contours.** The spec describes "very smooth continuous interpolation" where Windy.com interpolates between model timesteps. The prototype does not interpolate contour line positions -- it would need temporal GeoJSON series with coordinate interpolation, which does not exist.

6. **MSLP raster crossfade uses 150ms (playback) / 400ms (scrub).** The spec recommends 500-800ms for MSLP specifically, emphasizing that the "slow, majestic evolution" requires longer crossfades than precipitation. The current timing treats MSLP the same as all other raster layers.

7. **Raster rescale range may clip extremes.** `[98000, 104000]` Pa = 980-1040 hPa. Storm Kristin's central pressure dropped to ~960 hPa, which would be clipped to the blue end. The rescale should extend to at least 95000 Pa to capture deep lows.

#### D. Vizzuality Quality Gap

Vizzuality's layer-manager pattern uses declarative `onChapterEnter` / `onChapterExit` opacity changes per chapter. The cheias.pt prototype has no chapter concept -- MSLP is just another toggle. There is no narrative pacing: the user sees MSLP the same way at any point in the timeline, with no choreography directing attention to the dramatic moment when the low deepens to explosive cyclogenesis.

Vizzuality would:
- Generate temporal contour GeoJSON from the 409 ERA5 MSLP COGs (a scripting task)
- Animate contour positions using coordinate interpolation or GeoJSON source swapping
- Track L/H marker positions per timestep and animate them with `setData()`
- Layer temperature beneath MSLP, with isobars drawn on top for the classic synoptic look
- Use a longer crossfade (600-800ms) with ease-out for the "majestic" tempo
- Fix contour stroke to 1.5-2px white for the bullseye depth effect

#### E. Narrative Role

**Serves:** Chapter 4 (The Storms) -- showing Kristin's explosive cyclogenesis, and the "synoptic view" that weather enthusiasts and journalists will recognize as authoritative.

**Assessment:** The static contours on a temporal field is a visual credibility problem. Anyone who understands weather maps will immediately notice that the isobars do not match the pressure field. This undermines the institutional trust that the design document and Vizzuality methodology both emphasize. Fixing the temporal contour generation is a data pipeline task (not a frontend task) and should be a high priority.

---

### Effect 4: Satellite Cloud Motion

#### A. Specification Summary

**Source reference:** WeatherWatcher14 0:48-1:12.

Three sub-segments:

- **A (0:48-0:55): Wind streamlines + "EXPLOSIVE CYCLOGENESIS" label.** Animated wind streamlines (thin 1-2px white/blue lines) in tight cyclonic rotation west of Portugal. Vortex pattern with convergence. "Hypnotic spiral effect." Blue-tinted basemap.
- **B (0:55-1:08): Satellite side-by-side.** Left: wide Atlantic satellite (VIS/true color) showing full comma cloud. Right: zoomed Portugal view. Slow zoom/pan. "STING JET" label pointing to dry slot. The dry slot (cloud-free band cutting into comma head) is the critical visual feature.
- **C (1:08-1:12): Transition to radar.** Cut to precipitation radar view.

Key visual properties:
- Wind streamlines: thin (1-2px) white/light blue on dark blue background. Connected lines, not dots. Tail fading to transparent.
- Satellite: true-color or enhanced IR. Dark ocean, white clouds.
- Comma cloud structure: THE iconic visual of an extratropical cyclone.
- Side-by-side layout with thin divider.
- Satellite temporal cadence: 1 frame per hour.
- Data: Satellite IR COGs (49 hourly) already available. Wind U/V COGs for streamlines.
- **Known gap:** No VIS satellite COGs (only IR). No side-by-side mode.

#### B. Current Implementation Status

**Satellite IR layer:** Yes. `RASTER_LAYERS.satir` (line 357).
- URL pattern: `${R2_BASE}/satellite-ir/${date}T${h}-00.tif`.
- Date guard: only Jan 27-28 (line 359).
- Colormap: `irLUT` (line 317) -- dark -> purple -> red -> orange -> yellow thermal ramp.
- Max opacity: 0.9.
- Hour selector: continuous slider 0-23 (line 245).

**Satellite crossfade:** Uses the same A/B buffer system as all raster layers. Crossfade on hour change via `rasterBuf.satir.currentUrl = null` -> `loadRasterForDate()`.

**Wind streamlines at cyclone scale:** No separate implementation. The wind particle layer (Effect 1) operates at the same scale regardless of satellite layer state. No cyclone-specific streamline rendering, no vortex visualization, no white/blue color scheme for streamlines.

**Side-by-side mode:** NOT IMPLEMENTED. No dual-panel layout, no synced maps.

**Labels (EXPLOSIVE CYCLOGENESIS, STING JET):** NOT IMPLEMENTED. No text annotations on the map.

**VIS/true-color satellite:** NOT AVAILABLE. Only IR (thermal) imagery.

#### C. Visual Deficiency Analysis

1. **IR colormap does not reveal cloud structure effectively.** The `irLUT` (dark -> purple -> red -> orange -> yellow) is a generic thermal ramp that does not maximize contrast for cloud features. Satellite IR imagery for weather analysis typically uses inverted grayscale (cold clouds = white, warm surface = dark) or enhanced IR colormaps designed to highlight cloud-top temperature bands. The current ramp makes cold cloud tops yellow and warm ocean dark, which inverts the intuitive expectation (clouds should be white/bright).

2. **No cyclone-scale wind streamline visualization.** The spec's sub-segment A describes streamlines specifically showing "tight cyclonic rotation west of Portugal" as a separate visualization from the jet-stream-scale particles. The prototype has one wind particle layer that looks the same regardless of zoom level. A cyclone-scale visualization needs: lower particle count (~2,000), white/blue color, tight vortex convergence pattern, dark blue basemap tint.

3. **No side-by-side comparison mode.** The spec describes a split-screen with Atlantic-wide and Portugal-zoomed satellite views. This is a significant visual device for showing both the macro storm structure (comma cloud) and the local impact simultaneously. It would require either two MapLibre instances or a CSS-based viewport split.

4. **No text annotations.** Labels like "EXPLOSIVE CYCLOGENESIS" and "STING JET" are critical narrative devices that anchor the visual to scientific concepts. They turn a satellite image from "weather picture" into "explained weather event." The prototype has no annotation system.

5. **Satellite only available for Jan 27-28 (48 hours).** The date guard (line 359) correctly restricts to available data, but the UI does not communicate this limitation. When the user scrubs to other dates with satellite enabled, the layer simply fades out with no explanation. This violates the data-trust principle of transparency.

6. **No comma cloud / dry slot annotation.** The comma cloud is described as "THE iconic visual of an extratropical cyclone." Without VIS imagery or at minimum an enhanced IR colormap that makes the dry slot visible, the most important meteorological structure in the satellite data is not legible to non-experts.

#### D. Vizzuality Quality Gap

Vizzuality would treat the satellite chapter as a standalone "featured map" (ref: Half-Earth featured maps that "inspire us further and remind us of what we have -- and what we stand to lose"). The satellite imagery of Storm Kristin is the visual centrepiece of the crisis -- the single most dramatic image in the entire story.

Vizzuality would:
- Use an enhanced IR colormap specifically designed for cloud-top temperature analysis (not a generic thermal ramp)
- Implement annotated markers pointing to meteorological features (comma head, dry slot, warm conveyor belt)
- Build a side-by-side view for the satellite chapter
- Add a semi-transparent wind streamline overlay in white/blue showing the cyclonic circulation
- Ensure the satellite chapter has its own camera preset that frames the storm perfectly
- Include a subtle animation even on "static" satellite: slow zoom-in to build tension

Against the Vizzuality quality bar, the current satellite implementation is a "data dump" -- a raw thermal raster with a colormap selector. It does not tell a story, explain a structure, or create emotional impact. This is Anti-Pattern #4 (Sterile Design) from the methodology.

#### E. Narrative Role

**Serves:** Chapter 4 (The Storms) -- the visual climax of the meteorological narrative. The satellite view of Kristin is meant to be the moment where "understanding crystallizes" (design document).

**Assessment:** The satellite imagery is the most emotionally powerful data in the entire project. A well-rendered satellite view of a cyclone can convey the scale and violence of a storm system in a way no graph or map can. The current implementation reduces this to a toggleable thermal raster. The gap between potential and implementation is the widest here.

---

### Effect 5: Synoptic Chart + Radar Composites

#### A. Specification Summary

**Source reference:** WeatherWatcher14 3:10-3:30 (synoptic charts) + 3:30-4:20 (radar composite, longest continuous animation ~50 seconds).

**Synoptic chart (3:10-3:30):**
- MSLP isobars (black contour lines), frontal boundaries (blue cold fronts with triangles, red warm fronts with semicircles), H/L pressure centers, precipitation type symbols.
- Discrete time-stepping (snap between analysis times, NOT smooth interpolation).
- Classical meteorological cartography: information-rich, not pretty.

**Radar composite (3:30-4:20):**
- Radar reflectivity: green = light rain, yellow = moderate, red/pink = heavy, purple = extreme.
- Semi-transparent over satellite background.
- White MSLP isobars overlaid.
- Wind barbs: standard meteorological notation (staff + flags).
- Fast time-stepping: covers multiple days in 50 seconds, ~1 frame per 30-60 min real time.
- Very information-dense multi-layer composite.

**Data needed:**
- Radar reflectivity raster frames (not available; GPM IMERG fallback).
- Temporal MSLP contour GeoJSON (generate from ERA5 COGs).
- Wind barbs with proper meteorological notation (staff + flags + pennants).
- Frontal boundaries (requires manual or automated front detection).

#### B. Current Implementation Status

**Wind barbs (dynamic):** Partially implemented. `generateWindBarbs()` (line 633) creates direction arrows from U/V field.
- Renders as `PathLayer` id `'wind-barbs'` (line 726).
- Each barb is a 2-point path: `[[lon, lat], [lon + dx, lat + dy]]` (line 654).
- Color: `windSpeedColor(d.speed)` -- same 4-band step function as particles.
- Width: 2px, min 1, max 3 (lines 734-736).
- Grid step: 1 degree (line 637).

**MSLP contours + L/H markers:** Present (see Effect 3) but static.

**Frontal boundaries:** NOT IMPLEMENTED. No cold front/warm front lines.

**Radar data:** NOT AVAILABLE. Precipitation COGs are model-based, not radar reflectivity.

**Multi-layer composite:** No composite mode exists. Layers can be toggled independently but there is no "synoptic view" preset that enables the appropriate combination.

#### C. Visual Deficiency Analysis

1. **Wind "barbs" are simple direction arrows, not meteorological barb notation.** Standard wind barbs encode speed via flags (50kt), long barbs (10kt), short barbs (5kt), and pennants on a staff aligned with wind direction. The prototype renders a line segment from origin in the wind direction -- this shows direction but not speed in the barb itself. A meteorologist would not recognize these as wind barbs. This needs a custom icon/sprite system or SVG symbol layer.

2. **No frontal boundaries at all.** Cold fronts (blue line with triangles) and warm fronts (red line with semicircles) are absent. These are the most recognizable elements of a synoptic chart. Without them, the MSLP + wind layer combination looks like an abstract pressure map, not a synoptic analysis. Generating fronts automatically from temperature gradients is complex; manual analysis for the 3-4 key timesteps would be more practical.

3. **No radar reflectivity data.** This is a known data gap (no free historical radar for Portugal). The prototype uses model precipitation as a substitute, but model data lacks the spatial detail and the classic green-yellow-red radar color scheme that the public recognizes from TV weather. GPM IMERG (identified in the spec as fallback) has not been acquired.

4. **No synoptic composite view preset.** The spec describes an information-dense multi-layer composite that would be served as a single "mode" (MSLP + wind barbs + fronts + radar reflectivity layered together). The prototype requires manually toggling each layer separately. A "Synoptic" camera/layer preset would instantly show this composite.

5. **Wind barb grid is too coarse.** 1-degree spacing across the domain produces barbs that are very sparse at Portugal zoom levels. The spec's reference video shows denser wind barb coverage. At 1-degree resolution, Portugal (~3 x 5 degrees) shows only ~15 barbs -- far too few to convey the wind field structure.

#### D. Vizzuality Quality Gap

This is the most information-dense effect and the one most likely to trigger Anti-Pattern #1 (Overwhelming Configuration) if not carefully managed. Vizzuality's approach would be progressive disclosure: show the synoptic composite as a single pre-composed view in the scrollytelling narrative (user does not toggle individual layers), then in free exploration mode allow layer-by-layer control.

Vizzuality would:
- Pre-compose the synoptic view as a chapter-specific visualization, not a DIY layer stack
- Generate proper wind barb sprites using a canvas-based symbol factory
- Use the discrete time-stepping approach (snap between 6h analysis times) to match classical synoptic chart conventions
- Include at minimum hand-drawn frontal analysis for the 3-4 key timesteps in the story

Against the quality bar, this effect is the furthest from implementation. The spec itself acknowledges it as Tier 3 (future, highest complexity). It should not block the creative direction phase but should be planned for with realistic scope.

#### E. Narrative Role

**Serves:** Could serve a meteorology-focused chapter between Chapter 2 (Atlantic Engine) and Chapter 4 (The Storms). The synoptic composite is the "expert view" that validates the story for weather professionals and journalists.

**Assessment:** This effect is aspirational for v0. The priority should be getting Effects 1-4 and 6 to Vizzuality quality first. The synoptic composite can be added as a Phase 2 enhancement or served as a static image overlay (published synoptic charts from DWD/UKMO) for v0.

---

### Effect 6: Layer Transitions and Timeline Interaction

#### A. Specification Summary

**Source reference:** Throughout the video (every layer switch and camera move).

- **Layer crossfade:** Current layer fades out (~300ms), new layer fades in (~300ms). Basemap constant. No "pop" or instant swap -- always a crossfade.
- **Camera transitions:** Smooth pan/zoom between scales (globe -> continental -> national). 1-2 seconds, ease-out deceleration. `flyTo()`-style.
- **Timeline scrubber:** Thin horizontal bar at bottom. Current time indicator. Time labels at intervals. Play/pause button.
- **Crossfade blend:** At 50% blend, composite looks intentional -- layers overlay rather than flash.
- **Camera easing:** ease-out (starts fast, decelerates).
- **Timeline bar:** Dark background, white/light text, ~40px tall, anchored to bottom.

#### B. Current Implementation Status

**Layer crossfade (rasters):**
- `fadeInRaster(key, 300)` / `fadeOutRaster(key, 300)` (lines 809/830). Linear interpolation for toggle transitions.
- `crossfadeRaster()` (line 777) for frame-to-frame transitions. Smoothstep easing `t*t*(3-2*t)`.
- Duration: 150ms (playing) / 400ms (scrub).

**Layer crossfade (MapLibre vectors):**
- `animateOpacity()` (line 900) uses `requestAnimationFrame` with linear interpolation. Duration 300ms (line 980).

**Layer crossfade (deck.gl vectors):**
- `animateDeckOpacity()` (line 919) same pattern, 300ms.

**Camera presets:**
- Three buttons: Atlantic (`[-20, 42]` z4), Iberia (`[-5, 39.5]` z5.5), Portugal (`[-8, 39.5]` z6.5).
- `flyTo({ duration: 2000, essential: true })` (line 1311).
- MapLibre's default easing (built-in ease-in-out curve).

**Timeline:**
- Bottom bar with play button, range slider, date label (lines 257-261).
- Storm markers above timeline (Kristin, Leonardo, Marta) with colored labels.
- Play/pause via button or Space key. Arrow keys for step.
- Play speed: 200ms per frame (line 1241).

**Sub-timeline:**
- Satellite IR hour slider (0-23, continuous).
- MSLP hour buttons (00, 06, 12, 18 UTC).

#### C. Visual Deficiency Analysis

1. **No scroll-driven chapter transitions.** The most critical gap for the final product. The design document specifies a 9-chapter scrollytelling narrative where camera transitions, layer opacity changes, and text reveals are all triggered by scroll position via IntersectionObserver. The prototype has NO scroll system at all -- it is a full-screen layer viewer with manual controls. This is the fundamental structural gap between "prototype" and "product."

2. **Vector layer fade uses linear easing, not smoothstep.** The raster crossfade correctly uses smoothstep `t*t*(3-2*t)`, but `animateOpacity()` (line 910) uses linear interpolation: `from + (to - from) * t`. This creates a perceptible "pop" at the start and an abrupt stop at the end. All opacity transitions should use consistent easing.

3. **Camera presets have no pitch or bearing variation.** All three presets fly to `pitch: 0, bearing: 0` (default). The design document specifies pitch values of 15-45 degrees and bearing values of -10 to +15 degrees per chapter. The flat, north-up view works for a generic map viewer but lacks the cinematic quality the narrative needs. Compare: design doc's Chapter 1 `pitch: 15, bearing: 5` vs prototype's `pitch: 0, bearing: 0`.

4. **No layer-specific camera presets.** Enabling the satellite layer should automatically fly to the satellite data extent (Jan 27-28, focused on the storm). Enabling MSLP should frame the pressure system. Currently, layer toggles have no camera effect -- the user must manually click camera presets.

5. **Timeline height is larger than spec (56px vs ~40px).** The timeline bar with padding is approximately 56px tall (`padding: 10px 20px 14px` + button 34px). The spec suggests 40-60px, so this is within range, but it occupies significant screen real estate. On mobile, this would be problematic.

6. **No timeline time labels at regular intervals.** The timeline shows a single date label on the right (`#date-label`). The spec describes "labels show date/time at regular intervals" along the bar. The storm markers above the timeline (Kristin, Leonardo, Marta) partially serve this purpose but do not show dates.

7. **No keyboard shortcut for camera presets.** The spec is silent on this, but for a layer viewer prototype, keyboard shortcuts (1/2/3 for camera presets) would improve the developer experience.

8. **Play speed is fixed.** No speed control (0.5x, 1x, 2x, 4x). Vizzuality's timeline (Global Fishing Watch) supports 0.03x to 16x speed.

#### D. Vizzuality Quality Gap

The most significant gap is the absence of scroll-driven narrative. Vizzuality's `layers-storytelling` framework defines the canonical pattern: declarative chapter config with `onChapterEnter` / `onChapterExit` layer opacity arrays, `location` objects for camera, and `alignment` for text panels. The prototype has none of this infrastructure.

Vizzuality's animation system uses:
- `$anim-standard: 400ms` for all transforms and reveals
- `$easing-custom: cubic-bezier(0.445, 0.05, 0.55, 0.95)` for all transitions
- Consistent easing across all interactions

The prototype mixes 300ms (toggle), 150ms (playback), 400ms (scrub) with linear and smoothstep easing. There is no consistent animation language.

Vizzuality would:
- Implement IntersectionObserver scroll triggers at 50% threshold
- Define camera positions per chapter (center, zoom, pitch, bearing, animation type)
- Animate layer opacity declaratively per chapter
- Use consistent 400ms easing across all transitions
- Disable map interaction during scroll-driven sections, re-enable for free exploration
- Use `flyTo` for large geographic jumps, `easeTo` for small movements
- Include a "liberation moment" when the user reaches Chapter 9 and map interaction unlocks

#### E. Narrative Role

**Serves:** THE ENTIRE NARRATIVE. Layer transitions are the connective tissue between every chapter. Without them, there is no story -- just a data viewer.

**Assessment:** This is both the most important and the most structurally absent effect. The prototype was explicitly built as a "Layer Viewer" (the page title says so), not a scrollytelling experience. The creative direction phase must transform this into a narrative engine. The transition system is the architectural backbone that everything else hangs on.

---

## 3. Priority Gaps (Ranked by Visual Impact)

| Rank | Gap | Effect | Impact | Effort |
|------|-----|--------|--------|--------|
| 1 | **No scroll-driven chapter narrative** | E6 | Foundational -- no story without it | High (architecture) |
| 2 | **Static MSLP contours on temporal field** | E3 | Credibility: isobars drift from pressure field | Medium (data pipeline) |
| 3 | **No temperature field beneath isobars** | E3 | Missing the "most visible motion element" | Medium (data + render) |
| 4 | **Per-particle trail opacity, not per-segment** | E1 | Particles lack comet-tail streaking effect | Medium (render logic) |
| 5 | **Default particle count 2K vs 5K+** | E1 | Sparse, unconvincing wind visualization | Trivial (parameter) |
| 6 | **No gaussian-blurred precip edges** | E2 | Hard grid pixels vs soft watercolor washes | Medium (pre-process) |
| 7 | **IR colormap wrong for cloud structure** | E4 | Comma cloud not legible to non-experts | Low (LUT swap) |
| 8 | **No wind speed background field** | E1 | Particles float on empty dark basemap | Medium (new layer) |
| 9 | **Wind barbs lack meteorological notation** | E5 | Weather experts won't recognize them | Medium (sprite system) |
| 10 | **No map annotations (labels, arrows)** | E4 | Key structures unnamed | Low-Medium (HTML overlay) |
| 11 | **Precip color ramp wrong (Viridis vs blue)** | E2 | Domain-inappropriate palette | Trivial (default swap) |
| 12 | **Camera presets lack pitch/bearing** | E6 | Flat view lacks cinematic quality | Trivial (parameters) |
| 13 | **No satellite side-by-side view** | E4 | Missing macro+micro storm perspective | Medium (layout) |
| 14 | **Frontal boundaries absent** | E5 | Synoptic chart incomplete | High (data + render) |
| 15 | **No playback speed control** | E6 | Fixed 5fps, no user control | Low |

---

## 4. Quick Wins (Parameter Tweaks, No New Libraries)

These can be done in a single editing session with immediate visual improvement:

1. **Raise default particle count to 5,000** (line 436: `windParticleCount = 2000` -> `5000`, line 212: `value="2000"` -> `value="5000"`).

2. **Swap precipitation default colormap to `blues`** (line 355: `defaultCmap: 'viridis'` -> `defaultCmap: 'blues'`). The `bluesLUT` already exists and is closer to the spec's blue/white/cyan palette.

3. **Add pitch and bearing to camera presets** (lines 220-222). Change Atlantic to `pitch: 10, bearing: -5`, Iberia to `pitch: 20, bearing: 5`, Portugal to `pitch: 30, bearing: -10` for a more cinematic feel.

4. **Increase MSLP contour stroke width** (line 1109: `'line-width': 0.8` -> `'line-width': 1.5`; `'line-color': '#ccc'` -> `'line-color': '#fff'`).

5. **Extend MSLP rescale range** (line 370: `rescale: [98000, 104000]` -> `rescale: [95500, 104000]`) to capture deep lows like Kristin's ~960 hPa.

6. **Slow down MSLP crossfade** by adding a per-layer duration override. Currently, `playing ? 150 : 400` applies to all layers. MSLP should use 400-600ms even during playback for the "slow, majestic" tempo.

7. **Make precipitation pixel alpha proportional to value.** In `renderBandToCanvas()` (line 494), change `imgData.data[px + 3] = 200` to `imgData.data[px + 3] = Math.round(80 + 175 * t)` (where `t` is already computed on line 489). This gives light rain ~80/255 (31%) alpha and heavy rain ~255/255 (100%) alpha, matching the spec's "soft watercolor" quality.

8. **Swap satellite IR colormap to inverted grayscale** for cloud structure visibility. Replace `irLUT` with a simple inverted ramp: cold (high values) = white, warm (low values) = dark. Or create an "enhanced IR" LUT with gray background and highlighted cold cloud-top bands.

9. **Change basemap background from `#0a0a0a` to `#0a212e`** (line 12: `body { background: #0a0a0a` -> `body { background: #0a212e`). This matches the Vizzuality/design document's deep navy specification.

10. **Fix glassmorphism panel styling** (line 21: `background: rgba(12, 12, 20, 0.88)` -> `background: rgba(9, 20, 26, 0.4)` + increase blur from 12px to 16px). Currently the panels are nearly opaque (88% alpha) -- the spec calls for 40% alpha with stronger blur.

---

## 5. Structural Gaps (Require New Code, Libraries, or Architecture)

### 5.1 Scroll-driven narrative engine (Effect 6)
- **What:** IntersectionObserver-based chapter system with declarative config
- **Why:** The prototype has zero narrative structure. Without this, cheias.pt is a map viewer, not a geo-narrative.
- **Approach:** Port the Vizzuality `layers-storytelling` pattern: chapter divs with 50vh padding, observer at 50% threshold, camera + layer opacity changes on enter/exit.
- **Effort:** 2-3 days (architecture change from layer-viewer to scrollytelling).

### 5.2 Temporal MSLP contour generation (Effect 3)
- **What:** Generate GeoJSON isobar contours for all 409 ERA5 MSLP timesteps
- **Why:** Static contours on a temporal field is visually broken
- **Approach:** Python script using `rasterio` + `matplotlib.contour` or `contourpy` to extract 4hPa-interval contours from each MSLP COG. Output: one GeoJSON per timestep, or a single file with `datetime` properties for filtering.
- **Effort:** 1 day (scripting + validation).

### 5.3 Per-segment trail opacity for wind particles (Effect 1)
- **What:** Replace per-particle age-based alpha with per-trail-position exponential decay
- **Why:** The comet-tail effect is "critical to the visual" per spec
- **Approach:** deck.gl `PathLayer` does not natively support per-vertex color variation along a path. Options: (a) switch to `LineLayer` rendering individual trail segments with computed alpha, (b) use a custom WebGL shader, (c) render each trail as multiple 2-point line segments with decreasing alpha.
- **Effort:** 1-2 days (medium complexity, may need layer type change).

### 5.4 Temperature field layer (Effect 3)
- **What:** 2m temperature or 850hPa temperature raster field beneath MSLP isobars
- **Why:** The warm/cold boundary sweep is "the most visible motion element"
- **Approach:** Generate temperature COGs from ERA5 data (similar pipeline to existing MSLP COGs). Upload to R2. Add as a new raster layer in the prototype with a red/white/blue diverging colormap.
- **Effort:** 1-2 days (data pipeline + frontend layer).

### 5.5 Pre-rendered precipitation PNG frames with gaussian blur (Effect 2)
- **What:** Apply gaussian blur to existing precipitation PNGs, serve directly instead of COGs
- **Why:** Eliminates hard grid edges, matches "soft watercolor wash" spec
- **Approach:** Python batch process with `scipy.ndimage.gaussian_filter` or PIL `GaussianBlur`. Output pre-blurred PNGs. Switch prototype to load PNG frames instead of COGs (simpler and faster).
- **Effort:** 0.5 day.

### 5.6 Wind barb sprite system (Effect 5)
- **What:** Canvas-generated wind barb sprites with proper meteorological notation
- **Why:** Current arrows don't encode speed and won't be recognized by meteorologists
- **Approach:** Canvas factory function that draws staff + flags (50kt) + long barbs (10kt) + short barbs (5kt) based on wind speed. Render as deck.gl `IconLayer` with rotation from wind direction.
- **Effort:** 1-2 days.

### 5.7 Satellite annotation system (Effect 4)
- **What:** HTML/CSS overlay for meteorological annotations (EXPLOSIVE CYCLOGENESIS, STING JET, dry slot arrow)
- **Why:** Annotations transform raw imagery into explained science
- **Approach:** Absolutely positioned HTML elements that track geographic coordinates via `map.project()`. Show/hide with chapter transitions.
- **Effort:** 0.5-1 day.

### 5.8 Wind speed background field (Effect 1)
- **What:** Color-mapped wind speed raster beneath particle streamlines
- **Why:** "Particles add texture to an already-colored background" -- without it, particles float on void
- **Approach:** Compute wind speed magnitude from U/V COGs client-side (already loaded for particles) and render as BitmapLayer with purple/green/yellow colormap at 40-50% opacity. Or pre-compute wind speed COGs server-side.
- **Effort:** 0.5-1 day.

---

## 6. Vizzuality Delta: Overall Quality Gap Assessment

### Where the prototype stands

The prototype is a **competent engineering spike**. It demonstrates:
- Cloud-native COG rendering from R2 (working)
- Temporal animation with dual-buffer crossfade (working)
- GPU-advected wind particles (working)
- Animated layer toggles (working)
- Dynamic wind field loading (working)

### Where Vizzuality's bar is

Vizzuality ships **emotionally engaging, narrative-driven, institutionally trusted geospatial experiences** for organizations like WRI, The Nature Conservancy, and the E.O. Wilson Foundation. Their quality bar includes:

1. **Emotional engagement sequence (Delight -> Curiosity -> Exploration -> Digestion):** The prototype skips Delight entirely. There is no entry animation, no hero typography, no moment of visual wonder. A Vizzuality piece would open with a slow camera descent over the dark Atlantic, serif title floating over the ocean, coastline glowing -- before any data appears.

2. **Dark-first design as functional choice:** The prototype uses `#0a0a0a` (near-black); Vizzuality uses `#0a212e` (deep navy). The difference is subtle but important: navy is "easier on eyes and richer for data overlay contrast." The `#0a0a0a` feels cold and technical; `#0a212e` feels oceanic and warm.

3. **Glassmorphism:** The prototype's panels are `rgba(12, 12, 20, 0.88)` with `blur(12px)` -- 88% opaque, nearly solid. Vizzuality's standard is `rgba(9, 20, 26, 0.4)` with `blur(16px)` -- 40% opaque, the map clearly visible through the panel. This is Anti-Pattern #5 (Opaque Panels Blocking Map).

4. **Typography:** The prototype uses system sans-serif for everything. The design document specifies Georgia serif at 45px weight 300 for hero titles, Inter for body. Vizzuality uses `ivypresto-display` serif for emotional moments and `Open Sans` for UI. The absence of any serif typography eliminates the editorial, journalistic quality the story needs.

5. **Progressive disclosure (Mode 1/2/3):** The prototype is all Mode 2 (explore) with no Mode 1 (glance) or Mode 3 (understand). A Vizzuality piece would show a single powerful map view at first glance, reveal detail on interaction, and link to methodology for depth.

6. **Institutional framing:** The prototype's attribution (line 269) says "Data: COG from Cloudflare R2" and "Rendered with geotiff.js + deck.gl" -- this is developer attribution, not institutional trust. Vizzuality would show "Data: ERA5 Reanalysis -- ECMWF" and "Satellite: EUMETSAT Meteosat-12" as primary attribution.

7. **Narrative arc (What -> Why -> Action):** The prototype has no arc. It is a flat tool. Vizzuality's scrollytelling pattern builds from hook (one devastating number) through evidence (layered data) to resolution (what you can do). The design document defines this arc across 9 chapters. The prototype implements none of it.

8. **State confirmation micro-interactions:** Elena: "Small design details are just as important." Layer toggles in the prototype have no visual confirmation beyond the checkbox state change. Vizzuality would add: filled dot color on enable, subtle pulse on first activation, loading skeleton while COG fetches, green check when loaded.

9. **Accessibility:** No ARIA labels on any interactive elements. Checkbox labels are clickable but not semantically associated with the map layers. No keyboard navigation for layer toggles. Contrast ratios on `#666` text against `#0a0a0a` background fail WCAG AA.

10. **Responsive design:** The prototype has `overflow: hidden` on body and no responsive breakpoints. It would be unusable on mobile. Vizzuality's pattern is desktop sidebar -> mobile bottom sheet with `border-radius: 16px 16px 0 0` and swipe gestures.

### Specific recommendations to close the gap

| Priority | Recommendation | Vizzuality principle |
|----------|---------------|---------------------|
| P0 | Build scrollytelling narrative engine (chapter config, IntersectionObserver, camera choreography) | Scrollytelling pattern, What->Why->Action |
| P0 | Add serif hero typography and entry animation | Delight phase, emotional engagement |
| P0 | Fix basemap background to `#0a212e`, glassmorphism to `rgba(9,20,26,0.4)` + `blur(16px)` | Dark-first design, glass panel spec |
| P0 | Replace developer attribution with institutional source names | Institutional trust > technical documentation |
| P1 | Generate temporal MSLP contours from ERA5 COGs | Data accuracy, meteorological credibility |
| P1 | Implement per-segment trail opacity for wind particles | Visual impact, "wow factor" |
| P1 | Pre-render precipitation PNGs with gaussian blur and domain-appropriate blue colormap | Soft watercolor quality, domain aesthetics |
| P1 | Create enhanced IR colormap for satellite layer | Cloud structure legibility |
| P1 | Add pitch/bearing to camera presets; create chapter-specific camera positions | Cinematic quality, narrative framing |
| P2 | Build temperature field layer beneath MSLP isobars | Synoptic completeness |
| P2 | Add map annotation system for meteorological labels | Science communication |
| P2 | Implement wind speed background raster | Visual density, psychedelic effect |
| P2 | Add satellite side-by-side comparison mode | Storm structure macro/micro view |
| P2 | Build proper wind barb sprite notation | Meteorological accuracy |
| P3 | Add speed controls to timeline playback | User agency, Vizzuality timeline pattern |
| P3 | Implement responsive layout (mobile bottom sheet) | Universal audience |
| P3 | Add ARIA labels, keyboard navigation, contrast fixes | Accessibility |

### The honest gap

The prototype is roughly at **30-40% of Vizzuality shipping quality** for the visual effects, and **0% for narrative structure**. The effects work mechanically but lack the refinement, calibration, and emotional intentionality that separate a data viewer from a geo-narrative. The creative direction phase must bridge this gap -- not by adding more features, but by transforming the existing capabilities into a choreographed, emotionally engaging story.

The good news: the hard engineering work is done. The COG pipeline works, the particle system works, the crossfade works. What remains is calibration, narrative architecture, and visual polish -- which is exactly what creative direction is for.
