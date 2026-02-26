# Audit: Design Doc Effects vs Prototype Implementation

**Date:** 2026-02-26
**Source spec:** `data/video-analysis/MOTION-ANALYSIS.md` (6 visual effects from WeatherWatcher14 Storm Kristin video)
**Target:** `deckgl-prototype.html` (single-file MapLibre + deck.gl flood monitoring prototype)

---

## Effect 1: Wind Particle Streamlines
**Status: ✅ Implemented**

| Checklist | Status | Evidence |
|-----------|--------|----------|
| Particle system (PathLayer with trail rendering) | ✅ | `PathLayer` id `'wind-particles'` at line 749. Trails stored as coordinate arrays (`p.trail`) rendered as paths |
| Speed→color ramp (green→yellow→orange→purple) | ✅ | `windSpeedColor()` at line 571: `<8→[0,200,100]`, `<15→[255,255,100]`, `<25→[255,165,0]`, `>25→[180,0,255]` |
| Particle spawn/despawn cycle | ✅ | `spawnParticle()` at line 578, despawn conditions at lines 602-608 (age > MAX_AGE, out of bounds, speed < 0.5, stochastic 3%) |
| 5K+ particle count | ⚠️ | Default 2,000 (line 436), slider allows up to 10,000 (line 212 `max="10000"`). Meets spec at max but not by default |

**Remaining gaps:**
- Default count is 2,000 — spec calls for 5,000-20,000. Consider raising default to 5,000.
- Trail fade is per-age (`1 - d.age / MAX_AGE` at line 755), not per-trail-segment (exponential decay). The spec asks for "exponential decay on trail opacity" per position in the trail — currently the entire path gets one alpha value.
- `MAX_TRAIL = 12` (line 529) is within spec range (8-15 frames). Good.

---

## Effect 2: Precipitation Temporal Sweep / Raster Crossfade
**Status: ✅ Implemented**

| Checklist | Status | Evidence |
|-----------|--------|----------|
| Dual-layer crossfade on frame advance | ✅ | `rasterBuf` A/B dual-buffer system (lines 407-418). `crossfadeRaster()` at line 777 uses smoothstep easing |
| Opacity animation (requestAnimationFrame) | ✅ | `crossfadeRaster()` uses `requestAnimationFrame` loop with smoothstep `t*t*(3-2*t)` at line 795 |
| Smooth during play mode | ✅ | Play mode uses shorter crossfade `dur = playing ? 150 : 400` (line 876), frames advance every 200ms (line 1241) |

**Remaining gaps:**
- The precipitation layer loads COGs from R2 (`/precipitation/{date}.tif`) rather than the pre-rendered PNG frames in `data/raster-frames/precipitation/*.png`. This works but is heavier (COG parse + colormapping per frame vs. pre-rendered PNGs).
- No gaussian-blur soft edges on rain fields — the spec mentions "soft, gaussian-blurred edges" but COG rendering produces hard grid boundaries.

---

## Effect 3: MSLP Temporal Animation
**Status: ✅ Implemented**

| Checklist | Status | Evidence |
|-----------|--------|----------|
| MSLP raster field changing with date (COG from R2) | ✅ | `RASTER_LAYERS.mslpf` at line 365 loads `${R2_BASE}/mslp/${date}T${h}.tif` per date+hour |
| Diverging colormap (blue-white-red) | ✅ | `mslpLUT` at line 321: blue→white→red diverging scheme, rescale `[98000, 104000]` Pa |
| Static contour lines still present as overlay | ✅ | MapLibre layer `'mslp-lines'` at line 1108, GeoJSON source from `mslp-contours-v2.geojson` |
| L/H markers | ✅ | `'lh-labels'` (line 1130) and `'lh-pressure'` (line 1144) from `mslp-lh-markers.geojson` |

**Remaining gaps:**
- Contours are **static** (single timestep GeoJSON) while the raster field is temporal. They diverge as you scrub time — contours show one moment, field shows another.
- L/H markers are also static — they don't track the moving pressure centers.
- No temperature field layer (spec mentions warm/cold boundary as a key visual element).
- 6-hourly sub-timeline works (hour buttons at line 1038), but no smooth interpolation between timesteps.

---

## Effect 4: Satellite Cloud Motion
**Status: ✅ Implemented**

| Checklist | Status | Evidence |
|-----------|--------|----------|
| Satellite IR layer toggle | ✅ | Checkbox `t-satir` at line 199, `vis.satir` state |
| COG loading from R2 (`satellite-ir/` path) | ✅ | `RASTER_LAYERS.satir.urlFn` at line 358: `${R2_BASE}/satellite-ir/${date}T${h}-00.tif` |
| Thermal/IR colormap | ✅ | `irLUT` at line 317: dark→purple→red→orange→yellow thermal ramp |
| Temporal variation (hourly frames for Jan 27-28) | ✅ | Date range guard `date >= '2026-01-27' && date <= '2026-01-28'` at line 359, hour-controlled |
| Hour selector when satellite active | ✅ | `satir-hours` slider (line 243), range 0-23, wired at `wireSatirHourSlider()` line 1025 |

**Remaining gaps:**
- Only IR satellite, no VIS/true-color imagery (known gap per spec — would require Sentinel-3 OLCI or EUMETSAT HRV).
- No side-by-side comparison mode (spec Sub-segment B describes dual-panel Atlantic + Portugal views).
- Crossfade between hourly frames works via the same dual-buffer system.

---

## Effect 5: Synoptic Composite (Radar + MSLP + Wind Barbs + Fronts)
**Status: ⚠️ Partial**

| Checklist | Status | Evidence |
|-----------|--------|----------|
| Wind barb symbology | ⚠️ | `generateWindBarbs()` at line 633 creates direction arrows via PathLayer (line 726), but these are simple line segments, not meteorological barb notation (staff + flags + pennants) |
| MSLP contours + L/H markers | ✅ | Present (see Effect 3 above) |
| Frontal boundary rendering | ❌ | No frontal analysis or cold/warm front lines anywhere in the code |
| Radar data layer | ❌ | No radar data. Precipitation COGs are the closest substitute but use model data, not radar reflectivity |

**Remaining gaps:**
- Wind "barbs" are really just wind direction arrows (2-point paths). True meteorological barbs encode speed via flags/pennants on a staff — would need a custom icon layer or sprite system.
- No frontal boundaries at all — this would require manual analysis or automated front detection from temperature gradients.
- No radar data available (known gap — GPM IMERG identified as fallback in spec).
- Dynamic wind barbs from U/V COGs are a good step (line 660 `loadWindFieldForCurrentDate()` + line 633 `generateWindBarbs()`), but the visual representation is minimal.

---

## Effect 6: Layer Transitions + Camera
**Status: ✅ Implemented**

| Checklist | Status | Evidence |
|-----------|--------|----------|
| Crossfade on layer toggle (opacity animation) | ✅ | Rasters: `fadeInRaster(key, 300)` / `fadeOutRaster(key, 300)` at lines 809/830. Vectors: `animateOpacity()` at line 900 and `animateDeckOpacity()` at line 919. All use `requestAnimationFrame` loops |
| flyTo camera presets | ✅ | Three presets at lines 220-223: Atlantic (`-20,42` z4), Iberia (`-5,39.5` z5.5), Portugal (`-8,39.5` z6.5) |
| Smooth 1-2s camera transitions | ✅ | `flyTo({ duration: 2000, essential: true })` at line 1311 |

**Remaining gaps:**
- Camera transitions use linear easing — spec mentions "ease-out" deceleration. MapLibre's `flyTo` does use built-in easing by default, so this is likely fine.
- No layer-specific camera presets (e.g., "zoom to satellite extent" when enabling satellite layer).

---

## Summary Table

| Effect | Status | Key Evidence |
|--------|--------|--------------|
| 1. Wind particles | ✅ Implemented | PathLayer trails, speed→color, spawn/despawn cycle, density slider (500-10K) |
| 2. Precip crossfade | ✅ Implemented | A/B dual-buffer, smoothstep crossfade, shorter dur during play mode |
| 3. MSLP temporal | ✅ Implemented | R2 COGs per date+hour, diverging blue-white-red colormap, static contours+L/H overlay |
| 4. Satellite IR | ✅ Implemented | IR COGs from R2, thermal colormap, hourly slider for Jan 27-28 |
| 5. Synoptic composite | ⚠️ Partial | Dynamic wind arrows + MSLP contours present; no true barbs, no fronts, no radar |
| 6. Layer transitions | ✅ Implemented | rAF opacity animations on all layer types, flyTo with 3 camera presets |

## Progress Since Previous Assessment

| Effect | Before | After | Delta |
|--------|--------|-------|-------|
| 1. Wind particles | ❌ Missing | ✅ Implemented | Full particle system added |
| 2. Precip crossfade | ⚠️ Hard swaps | ✅ Implemented | A/B buffer with smoothstep |
| 3. MSLP temporal | ⚠️ Static only | ✅ Implemented | Temporal raster field from R2 COGs |
| 4. Satellite IR | ❌ No layer | ✅ Implemented | IR COGs with hourly control |
| 5. Synoptic composite | ⚠️ Minimal | ⚠️ Partial | Dynamic wind arrows added |
| 6. Layer transitions | ⚠️ No crossfade | ✅ Implemented | Animated opacity + flyTo presets |

## Remaining High-Value Gaps (priority order)

1. **Temporal MSLP contours** — Static contours diverge from dynamic raster field during playback
2. **True wind barb notation** — Current arrows don't encode speed via flags/pennants
3. **Trail-segment opacity decay** — Wind particles use per-particle age, not per-segment exponential decay
4. **Default particle count** — 2,000 vs. spec's 5,000+ recommendation
5. **Frontal boundaries** — Not implemented (complex, low ROI for prototype)
