# Motion Analysis — WeatherWatcher14 Storm Kristin Video

**Source:** https://youtu.be/MypYdH8vPHQ
**Channel:** @WeatherWatcher14
**Duration:** 7:07 (427s)
**Content:** European storm analysis covering Storm Kristin hitting Portugal (Jan 28, 2026)
**Extracted:** 2026-02-24

## Video Structure Overview

| Time | Content | Animation? |
|------|---------|------------|
| 0:00–0:04 | Windy.com precipitation sweep (flat map) | YES |
| 0:04–0:10 | Windy.com jet stream / wind particles (globe) | YES |
| 0:10–0:28 | Title cards (Francis, Oriana, storm names) | No |
| 0:28–0:36 | MSLP isobar + temperature field animation | YES |
| 0:36–0:48 | Title card (Kristin) + transitions | No |
| 0:48–0:55 | "EXPLOSIVE CYCLOGENESIS" wind streamlines | YES |
| 0:55–1:08 | Satellite VIS/IR + "STING JET" side-by-side | Partial (zoom/pan) |
| 1:08–1:20 | Precipitation radar over Portugal | YES (brief) |
| 1:20–2:10 | Social media posts, IPMA data, storm footage | No |
| 2:10–2:30 | Damage infographic + storm track diagram | No (static graphic) |
| 2:30–2:50 | WXCharts precipitation + wind gust maps | No (static maps) |
| 3:00–3:10 | Chapter 2 title (globe + jet stream) | YES (brief) |
| 3:10–3:30 | Synoptic chart time-stepping (DWD-style) | YES |
| 3:30–4:20 | European radar composite time-lapse | YES (longest) |
| 4:20–4:32 | Precipitation forecast animation | YES |
| 4:30–4:40 | Wind particles (globe view, reprise) | YES |
| 4:40–5:00 | MSLP isobar evolution | YES |
| 5:00–7:07 | User-submitted winter photos + end card | No |

---

## Effect 1: Jet Stream / Wind Particle Visualization

- **Timestamp:** 0:04–0:10 (reprise at 4:30–4:40)
- **Platform:** Windy.com (jet stream / wind layer)
- **Contact sheet:** `contact-wind-particles.png`
- **Frames:** `wind-particles_0015.png` through `wind-particles_0030.png`

### Motion Description
- **What moves:** Continuous particle streamlines showing upper-level wind flow. NOT discrete dots — these are elongated streaks/ribbons that flow along wind trajectories. The jet stream appears as a thick band of intense color.
- **Speed/tempo:** Fast-moving particles (~2-4 px/frame at 30fps). The jet stream core particles move fastest; peripheral flow slower. Creates a clear velocity gradient.
- **Direction:** Primarily W→E across the Atlantic, with large-scale curvature around low pressure systems. Visible cyclonic (counterclockwise) rotation around lows.
- **Easing:** Continuous, smooth. No step function — particles flow endlessly. New particles spawn at edges as old ones exit.

### Visual Properties
- **Color ramp:** Multi-variable — purple/magenta = highest wind speed, green = moderate, yellow = low wind, cyan/blue = calm. The mapping creates a psychedelic swirl effect where the jet stream is a vivid purple-white ribbon cutting through green/yellow background.
- **Opacity/blending:** Particles are semi-transparent, overlaid on a subtle terrain basemap. The color field BEHIND the particles also shows a smooth gradient (the underlying wind speed field), so particles add texture to an already-colored background.
- **Trail/fade effect:** YES — each particle leaves a short comet-like trail (~10-20px long). Trails fade with distance. This is critical to the visual — without trails, individual particles would be invisible. The trail length encodes speed (longer = faster).
- **Density:** Very high — hundreds of particles simultaneously visible. Denser in high-speed regions (jet stream core), sparser in calm areas. The density variation itself communicates the flow structure.
- **Globe projection:** Uses orthographic globe view, adding depth. Jet stream appears to wrap around the Earth.

### Replication Approach for deck.gl/MapLibre
- **Suggested layer type:** Custom WebGL particle system OR deck.gl `TripsLayer` adapted for wind. The closest off-the-shelf options:
  1. **mapbox-gl-wind** / **wind-layer** plugins — render particle streamlines from U/V wind fields
  2. **deck.gl ParticleLayer** (experimental) — GPU-based particle advection
  3. **Custom approach:** Advect particles through interpolated U/V field, render with `LineLayer` using trail opacity gradient
- **Data format needed:** Wind U/V components on a regular grid (COG or JSON grid). Particles are computed client-side by advecting through the field.
- **Key parameters to tune:**
  - Particle count: 5,000-20,000 for full-screen density
  - Trail length: 8-15 frames of history
  - Speed multiplier: Adjust to match visual tempo
  - Color mapping: Wind speed → color ramp (0–60 m/s → green→yellow→purple)
  - Particle spawn rate: Replace ~5% of particles per frame
  - Fade: Exponential decay on trail opacity
- **Available cheias-pt data:**
  - Wind U/V COGs: `data/cog/wind-u/*.tif` and `data/cog/wind-v/*.tif` (409 files each, 6-hourly, ERA5 0.25°)
  - Wind barbs GeoJSON: `data/qgis/wind-barbs-kristin.geojson` (6,419 points — static snapshot, not for animation)
  - Could derive wind speed field from U/V for color mapping

---

## Effect 2: Precipitation Temporal Sweep

- **Timestamp:** 0:00–0:04 (Windy flat map) + 4:20–4:32 (forecast bands)
- **Platform:** Windy.com (rain/thunder layer)
- **Contact sheet:** `contact-precip-sweep-windy.png` + last frames of `contact-synoptic-radar.png`
- **Frames:** `wind-particles_0003.png`–`wind-particles_0013.png` (opening), `synoptic-radar_0148.png` + `precip-forecast_0010.png`–`precip-forecast_0020.png` (Chapter 2)

### Motion Description
- **What moves:** Rain fields — semi-transparent colored areas representing precipitation intensity. The precipitation "blobs" advect W→E, growing, splitting, and dissipating as they cross the map.
- **Speed/tempo:** Medium speed — rain bands traverse the screen in ~3-5 seconds. The movement tracks the frontal system's progression. Time bar at bottom reads "Tomorrow 05:50" → "Tomorrow 21:50", so ~16 hours elapse in ~4 seconds.
- **Direction:** Primarily W→E / SW→NE, following the frontal conveyor belt from the Atlantic into Europe. Secondary motion: bands elongate N-S along the cold front.
- **Easing:** Smooth interpolation between timesteps. No visible frame-stepping — Windy blends between model output times.

### Visual Properties
- **Color ramp:** Light blue/white = light rain, darker blue = moderate, cyan/teal = heavy, NO pink/red in this view (those appear in radar, not forecast). The color ramp is deliberately muted — soft watercolor washes rather than hard-edged polygons.
- **Opacity/blending:** ~50-60% opacity over the basemap. Terrain and coastlines remain visible underneath. Rain fields have soft, gaussian-blurred edges — NO hard boundaries.
- **Trail/fade effect:** Rain areas fade in/out smoothly. Leading edge of rain band brightens gradually; trailing edge dissipates. Creates a "rolling curtain" impression.
- **Density:** Varies — dense bands along frontal boundaries, sparse scattered convection elsewhere.
- **Second view (4:20-4:32):** Precipitation forecast with a green color ramp (10→300mm scale). Shows accumulated precipitation as flowing stream patterns from Atlantic → Europe. More saturated and intense than the real-time view. Green bands follow atmospheric river pathways.

### Replication Approach for deck.gl/MapLibre
- **Suggested layer type:** MapLibre `image` source with frame animation (raster-based). Simplest and most effective for pre-rendered data.
  1. **Raster frame animation:** Load daily PNG rasters, crossfade between frames using opacity transitions on two alternating image layers
  2. **Alternative:** `HeatmapLayer` if point-based data, with animated radius and intensity
- **Data format needed:** Pre-rendered PNG/WebP frames with transparent background, one per timestep. OR GeoJSON point grid with precipitation values for heatmap approach.
- **Key parameters to tune:**
  - Crossfade duration: 300-500ms between frames for smooth blending
  - Opacity: 0.5-0.7 over basemap
  - Frame rate: ~2-4 frames/second for temporal sweep
  - Color ramp: White→Light blue→Blue (or Green ramp for accumulation view)
- **Available cheias-pt data:**
  - Precipitation PNGs: `data/raster-frames/precipitation/*.png` (77 daily frames) — READY for direct use
  - Precipitation frontend JSON: `data/frontend/precip-frames.json` (342 pts × 77 days) — for point-based approach
  - Precip storm totals: `data/frontend/precip-storm-totals.json` — for static accumulation view

---

## Effect 3: MSLP Isobar Animation

- **Timestamp:** 0:28–0:36 (first appearance), 4:40–5:00 (reprise/evolution)
- **Platform:** Windy.com (pressure + temperature overlay)
- **Contact sheet:** `contact-mslp-animation.png` + `contact-precip-mslp-evolution.png` (frames 80-120)
- **Frames:** `mslp-animation_0001.png`–`mslp-animation_0015.png`, `precip-forecast_0080.png`–`precip-forecast_0120.png`

### Motion Description
- **What moves:** Two distinct layers move simultaneously:
  1. **Isobar contour lines:** Concentric pressure lines shift position as the low pressure system drifts NE. Lines smoothly interpolate — no visible redrawing/flickering.
  2. **Temperature color field:** Red (warm) and blue (cold) regions sweep with the frontal boundary. The warm/cold boundary is the most visible motion element.
- **Speed/tempo:** Slow, majestic evolution. The low pressure center moves ~100px over 8 seconds. Unhurried — communicates the large spatial scale. Each visible frame advance covers ~3-6 hours of model time.
- **Direction:** Low pressure center drifts NE (from mid-Atlantic toward Iceland/UK). Warm sector wraps around the low. Cold air pushes southward behind the cold front.
- **Easing:** Very smooth continuous interpolation. Windy.com interpolates between model timesteps, creating fluid motion. No stepped jumps.

### Visual Properties
- **Color ramp:** Dual-purpose:
  - **Temperature field:** Deep red/salmon = warm (subtropical air), deep blue/navy = cold (polar air), white = boundary. Smooth gradient, NO discrete bands.
  - **Isobars:** White/cream contour lines, ~4hPa spacing. Lines maintain consistent stroke width regardless of gradient. L/H markers at pressure centers.
- **Opacity/blending:** Temperature field is ~70-80% opacity. Isobars drawn on top at full opacity. Basemap (coastlines, land boundaries) faintly visible through temperature layer.
- **Trail/fade effect:** None on contours — they simply translate. The temperature field smoothly morphs (color interpolation between frames).
- **Depth perception:** The concentric isobars around the low create a "bullseye" that naturally draws the eye. The tight gradient near the low → spread isobars further out creates an implied 3D depression.
- **Key visual detail (4:40-5:00):** The deep blue low pressure trough elongates and shifts. Multiple timesteps show the system evolving: isobars tighten (deepening), then spread (filling). The warm/cold boundary rotates around the low.

### Replication Approach for deck.gl/MapLibre
- **Suggested layer type:** Multi-layer composite:
  1. **Temperature field:** MapLibre raster image source — pre-rendered color-mapped temperature frames, crossfaded between timesteps
  2. **Isobars:** MapLibre `line` layer from GeoJSON contours. Animate by swapping GeoJSON per timestep, with interpolation on line coordinates.
  3. **L/H markers:** MapLibre `symbol` layer, animate position with `setData()` per timestep
- **Data format needed:**
  - Temperature: Raster frames (PNG/WebP) with color-mapped temperature, one per timestep
  - Isobars: GeoJSON LineString features per timestep, with `pressure_hpa` property
  - Markers: GeoJSON Point features with `type` (L/H), `pressure_hpa` per timestep
- **Key parameters to tune:**
  - Isobar stroke: 1.5-2px, white/cream, ~4hPa interval
  - Temperature opacity: 0.7
  - Crossfade: 500-800ms between frames (slower than precipitation — emphasizes scale)
  - Label placement: L/H labels should follow the pressure center smoothly
- **Available cheias-pt data:**
  - MSLP contours: `data/qgis/mslp-contours-v2.geojson` (28 isobars — SINGLE timestep only, needs temporal expansion)
  - MSLP L/H markers: `data/qgis/mslp-lh-markers.geojson` (7 centers — SINGLE timestep)
  - ERA5 MSLP COGs: `data/cog/mslp/*.tif` (409 files, 6-hourly) — source for generating temporal contours
  - **Gap:** No pre-rendered temperature field rasters. Would need to generate from ERA5 2m temperature or 850hPa temperature COGs.

---

## Effect 4: Satellite Cloud Motion

- **Timestamp:** 0:48–1:12
- **Platform:** Windy.com (wind streamlines) + satellite imagery (EUMETSAT/Zoom Earth)
- **Contact sheet:** `contact-satellite-motion.png`
- **Frames:** `satellite-motion_0001.png`–`satellite-motion_0072.png`

### Motion Description
- **Sub-segment A (0:48-0:55): Wind streamlines + "EXPLOSIVE CYCLOGENESIS" label**
  - Animated wind streamlines (thin white/blue lines) flowing in tight cyclonic rotation west of Portugal
  - Vortex pattern clearly visible — counterclockwise swirl with convergence
  - Streamlines move continuously, ~3-5px/frame, creating a hypnotic spiral effect
  - Background is a blue-tinted Windy.com basemap with terrain

- **Sub-segment B (0:55-1:08): Satellite side-by-side**
  - Left panel: Wide Atlantic satellite view (VIS/true color) showing full storm structure — comma cloud, dry slot, warm front cloud shield
  - Right panel: Zoomed Portugal satellite view showing cloud bands wrapping around the country
  - Motion: Slow zoom/pan on both panels. Cloud structure appears to evolve slightly between frames (temporal progression in the satellite imagery)
  - The "STING JET" label points to the dry intrusion / clear slot in the cloud structure
  - The dry slot is the critical visual feature — a dark (cloud-free) band cutting into the comma cloud head

- **Sub-segment C (1:08-1:12): Transition to radar**
  - Cut to precipitation radar view over Portugal — blue/cyan/pink blobs of radar reflectivity

### Visual Properties
- **Wind streamlines:** Thin (1-2px) white/light blue lines on dark blue background. Lines follow wind field, with tail-end fading to transparent. Similar to wind particles but as connected lines rather than discrete dots.
- **Satellite imagery:** True-color or enhanced IR. Dark ocean background, white clouds. Side-by-side layout with thin divider.
- **Color in radar view:** Blue = light rain, cyan = moderate, pink/magenta = intense convection.
- **The "comma cloud" structure:** The entire storm is visible as a comma-shaped cloud mass — head (N), tail (S extending SW). This is THE iconic visual of an extratropical cyclone.

### Replication Approach for deck.gl/MapLibre
- **Suggested layer type:**
  1. **Wind streamlines:** Same approach as Effect 1 but zoomed to Iberian scale. Lower particle count, tighter vortex visualization.
  2. **Satellite animation:** MapLibre `raster` source pointing to temporal satellite COGs. Crossfade between hourly frames.
  3. **Side-by-side:** Two MapLibre map instances synced with `syncMaps()` or CSS grid layout
- **Data format needed:** Satellite COGs (already have these), wind U/V for streamlines
- **Key parameters to tune:**
  - Streamline density: Lower than jet stream view (~2,000 particles)
  - Streamline color: White on dark blue
  - Satellite opacity: Full (1.0) — these are the primary visual
  - Temporal cadence: 1 frame per hour for satellite
- **Available cheias-pt data:**
  - Satellite IR COGs: `data/cog/satellite-ir/*.tif` (49 hourly) — READY
  - Wind U/V COGs: `data/cog/wind-u/*.tif`, `data/cog/wind-v/*.tif` — for streamlines
  - **Gap:** No VIS satellite COGs (only IR). True-color would require Sentinel-3 OLCI or EUMETSAT HRV.

---

## Effect 5: Synoptic Chart + Radar Time-Lapse

- **Timestamp:** 3:10–3:30 (synoptic charts) + 3:30–4:20 (radar composite)
- **Platform:** DWD/UKMO-style synoptic analysis + European radar composite (Meteologix or similar)
- **Contact sheet:** `contact-synoptic-radar.png`
- **Frames:** `synoptic-radar_0001.png`–`synoptic-radar_0148.png`

### Motion Description

**Synoptic chart (3:10-3:30):**
- **What moves:** MSLP isobars (black contour lines), frontal boundaries (blue cold fronts with triangles, red warm fronts with semicircles), H/L pressure centers, precipitation type symbols
- **Speed/tempo:** Discrete time-stepping — jumps between analysis times (typically 6 or 12 hour intervals). NOT smooth interpolation. Each frame is a distinct synoptic analysis chart.
- **Direction:** Weather systems progress W→E across Europe. Cold fronts sweep through, followed by clearance.
- **Easing:** Step function — snap from one analysis to the next. This is traditional meteorological visualization (hand-analyzed charts).

**Radar composite (3:30-4:20):**
- **What moves:** Radar reflectivity blobs (green/blue/purple/pink) sweep across Europe. Multiple rain bands visible simultaneously. This is the longest continuous animation (~50 seconds).
- **Speed/tempo:** Fast time-stepping — covers multiple days in 50 seconds. Rain bands cross the full European domain in ~10-15 seconds of playback. Approximately 1 frame per 30-60 minutes of real time.
- **Direction:** Dominant W→E advection, but individual cells show N-S elongation along fronts. Cyclonic curvature visible in rain band arcs.
- **Easing:** Frame-stepping (not interpolated), but fast enough to appear pseudo-smooth.
- **Overlay elements:** Wind barbs (static per frame), MSLP isobars (white lines), satellite imagery (background), "Current Radar" label, metdesk watermark. Very information-dense.

### Visual Properties
- **Synoptic chart:**
  - Black isobars on light background, ~4hPa spacing
  - Blue cold fronts (triangles pointing direction of travel), red warm fronts (semicircles)
  - Green/blue precipitation shading behind fronts
  - Classical meteorological cartography — NOT pretty, but extremely information-rich
- **Radar composite:**
  - Green = light rain, yellow = moderate, red/pink = heavy, purple = extreme
  - Semi-transparent radar reflectivity over satellite background
  - White MSLP isobars overlaid
  - Wind barbs: standard meteorological notation (staff + flags)
  - Layout includes sidebar text ("WANT TO SUBMIT A WEATHER PHOTO?")
  - "Current Radar" label with satellite inset in top-right corner

### Replication Approach for deck.gl/MapLibre
- **Suggested layer type:** This is the most complex composite:
  1. **Radar reflectivity:** Raster frame animation (MapLibre image source, same as precip)
  2. **MSLP isobars:** GeoJSON line layer per timestep
  3. **Wind barbs:** Custom symbol/icon layer — render barb glyphs from wind speed/direction
  4. **Frontal boundaries:** GeoJSON LineString with custom dash pattern (triangles for cold, semicircles for warm) — mapbox expression or custom sprites
- **Data format needed:**
  - Radar: Pre-rendered raster frames (we don't have actual radar data — GPM IMERG would be the fallback)
  - MSLP: Temporal GeoJSON contours (generate from ERA5 COGs)
  - Wind barbs: GeoJSON points with `speed_kts` and `direction_deg` properties
  - Fronts: Would need manual analysis or automated front detection (complex)
- **Key parameters to tune:**
  - Frame rate: 2-4 fps for radar time-lapse
  - Radar opacity: 0.6-0.7
  - Isobar stroke: 1px white
  - Wind barb size: Scale with zoom level
- **Available cheias-pt data:**
  - ERA5 MSLP COGs: `data/cog/mslp/*.tif` (409 files) — for contour generation
  - Wind barbs GeoJSON: `data/qgis/wind-barbs-kristin.geojson` (6,419 points — single timestep)
  - Wind U/V COGs: For generating temporal wind barbs
  - Precipitation PNGs: `data/raster-frames/precipitation/*.png` (77 daily) — coarser substitute for radar
  - **Gap:** No actual radar data. GPM IMERG (if acquired) would be closest. No automated frontal analysis.

---

## Effect 6: Layer Transitions and Timeline Interaction

- **Timestamp:** Throughout (0:04, 0:28, 0:48, 3:00, 4:20, 4:30, 4:40)
- **Platform:** Windy.com (primary), video editing (secondary)

### Motion Description
- **Layer switches in Windy.com:** The presenter changes between data overlays (precipitation → jet stream → MSLP → wind streamlines). Each switch:
  - Current layer fades out (~300ms)
  - New layer fades in (~300ms)
  - Basemap remains constant throughout
  - No "pop" or instant swap — always a crossfade
- **Camera transitions:** Smooth pan/zoom between scales (globe → continental → national). Approximately 1-2 second duration per camera move. Deceleration at the end (ease-out).
- **Timeline scrubber:** Visible at bottom of Windy.com views:
  - Thin horizontal bar showing time range
  - Current time indicator (vertical line or playhead)
  - Time advances left→right during animation
  - Labels show date/time at regular intervals
  - Play/pause button (|| icon visible in frames)
- **Video editing transitions:** Hard cuts between platforms (Windy → WXCharts → satellite). Title cards use fade-to-black / fade-from-black (~500ms each way).

### Visual Properties
- **Crossfade blend:** Both old and new layers visible simultaneously during transition. At 50% blend, the composite looks intentional — layers overlay rather than flash.
- **Camera easing:** Smooth ease-out (starts fast, decelerates). flyTo()-style animation similar to MapLibre's built-in camera transitions.
- **Timeline bar:** Dark background, white/light text, ~40px tall, anchored to bottom of map viewport.

### Replication Approach for deck.gl/MapLibre
- **Layer transitions:** MapLibre `setPaintProperty()` to animate opacity:
  ```js
  // Crossfade: old layer 1.0→0.0, new layer 0.0→1.0 over 500ms
  map.setPaintProperty('old-layer', 'raster-opacity', 0);
  map.setPaintProperty('new-layer', 'raster-opacity', 1);
  ```
  Use CSS `transition` on layer opacity, or `requestAnimationFrame` loop for fine control.
- **Camera:** MapLibre `flyTo()` with `duration: 2000, essential: true` matches the video's camera moves.
- **Timeline:** Custom HTML element over map canvas. Already implemented in `temporal-player.js` for cheias-pt.
- **Key parameters:**
  - Layer crossfade: 300-500ms
  - Camera transition: 1500-2500ms with ease-out
  - Timeline height: 40-60px

---

## Priority Ranking for cheias-pt Implementation

Based on visual impact, data availability, and implementation complexity:

### Tier 1: Implement Now (data ready, high impact)
1. **Precipitation temporal sweep** (Effect 2) — 77 PNG frames already exist. Crossfade animation is simplest to implement. Direct MapLibre image source swap.
2. **MSLP isobar animation** (Effect 3) — Single-timestep contours exist. Need to generate temporal series from ERA5 COGs (scripting task, not acquisition).
3. **Layer transitions** (Effect 6) — Already partially implemented. Add crossfade to chapter transitions.

### Tier 2: Implement Next (data exists, moderate complexity)
4. **Satellite cloud motion** (Effect 4) — 49 IR COGs ready. Need to serve via Titiler or convert to PNG frames. Very high narrative value (comma cloud structure).
5. **Wind particle streamlines** (Effect 1) — 409 U/V COG pairs exist. Need custom WebGL particle system or wind-layer plugin. Highest "wow factor" but most complex.

### Tier 3: Future (data gaps or high complexity)
6. **Synoptic chart + radar composite** (Effect 5) — Would require generating temporal MSLP contours + wind barbs per timestep from ERA5 data. No radar data available. Highest information density but most complex multi-layer composite.

---

## File Inventory

### Contact Sheets
- `contact-wind-particles.png` — Jet stream particle flow (7 frames, 0:04-0:10)
- `contact-precip-sweep-windy.png` — Windy precipitation sweep (6 frames, 0:00-0:04)
- `contact-mslp-animation.png` — MSLP isobar evolution (6 frames, 0:28-0:36)
- `contact-satellite-motion.png` — Satellite + wind streamlines (7 frames, 0:48-1:12)
- `contact-synoptic-radar.png` — Synoptic charts + radar time-lapse (7 frames, 3:10-4:32)
- `contact-precip-mslp-evolution.png` — Precip forecast + MSLP evolution (7 frames, 4:20-5:00)

### Frame Extracts
- `frames/overview_*.png` — 43 frames, one every 10 seconds
- `frames/wind-particles_*.png` — 30 frames at 3fps (0:00-0:10)
- `frames/mslp-animation_*.png` — 42 frames at 3fps (0:28-0:42)
- `frames/satellite-motion_*.png` — 72 frames at 3fps (0:48-1:12)
- `frames/precip-sweep_*.png` — 42 frames at 3fps (1:18-1:32, mostly storm footage)
- `frames/synoptic-radar_*.png` — 148 frames at 2fps (3:08-4:22)
- `frames/precip-forecast_*.png` — 132 frames at 3fps (4:18-5:02)
