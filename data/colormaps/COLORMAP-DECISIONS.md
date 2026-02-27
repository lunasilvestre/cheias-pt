# Colormap Decisions — 12 Layer Colormaps + 2 Composite Tests

**Date:** 2026-02-27
**Tested in:** QGIS with cheias-scrollytelling.qgz project
**Calibrated against:** IMPACT-GAUGE.md findings, WeatherWatcher14 contact sheets
**Output:** `palette.json` (machine-readable, all 12 colormaps)

---

## Testing Methodology

Each colormap tested by:
1. Loading representative COG/vector in QGIS
2. Overlaying on the approved basemap mood from Part 1
3. Comparing against video reference where available
4. Exporting screenshot to `screenshots/`

Two composite tests validate multi-layer legibility.
Deuteranopia simulation validates colorblind safety.

---

## Individual Colormap Results

### 1. precipitation-blues
**Render:** `precipitation-blues-over-dark.png`
**Current QGIS style:** Pink/magenta/blue (precipitation-windy.qml) — WRONG
**Spec target:** Sequential blues #e8f4f8 → #08519c
**Action:** Replace colormap entirely. The pre-rendered PNGs from P1.B5 already use
blues with Gaussian blur — those are the correct reference. QML style needs full rewrite
for any direct COG rendering in Phase 2.
**Adjustment:** Lower domain ceiling from 80mm to 50mm/day OR apply gamma<1 stretch
to push more pixels into visible mid-blue range. Current 80mm ceiling leaves most
storm pixels too pale.

### 2. soil-moisture-browns
**Render:** `soil-moisture-over-terrain.png`
**Current QGIS style:** Blue sequential (soil-moisture-saturation.qml)
**Spec target:** Brown → green → blue earth tones
**Action:** Current blues work but don't match the "sponge fills" narrative. Earth tones
(#8B6914 → #4A7C59 → #1B4965) would visually encode dry→moist→saturated in a way that
reads as "soil" not "water." Test both in Phase 2 and let the narrative director choose.

### 3. sst-diverging
**Render:** `sst-diverging-over-ocean.png`
**Current QGIS style:** Red-blue diverging (sst-anomaly.qml)
**Assessment:** Working well. Warm orange-red dominates the Atlantic view for Jan 2026,
clearly communicating the anomalous heat reservoir that fueled the storms. White midpoint
at 0°C. Land silhouette visible through basemap.
**No changes needed.**

### 4. ivt-sequential
**Render:** `ivt-over-ocean.png`
**Current QGIS style:** Green-red multicolor (ivt-atmospheric-river.qml)
**Assessment:** Vivid AR core visible — red band at ~40°N directly targeting Portugal.
For web rendering, consider switching to purple→white sequential to avoid green-red
issues and maintain consistency with the dark ocean basemap.
**Minor adjustment:** Remap to purple→white for web.

### 5. satellite-ir
**Render:** `satellite-ir-over-dark.png`
**Current QGIS style:** Inverted grayscale (satellite-ir.qml)
**Assessment:** OUR STRONGEST LAYER. 80-90% of broadcast reference quality. High contrast
white clouds on dark ocean. Comma cloud structure clearly visible. Frontal bands readable.
**Minor tweak only:** Darken the warm/surface end of the grayscale slightly to push
cloud/ocean contrast even higher.

### 6. flood-extent
**Render:** `flood-extent-over-dark.png`
**Styled in render:** #2471a3 fill at 55%, #1a5276 stroke
**Assessment:** Clean, effective. Blue on ultra-dark navy. River valley flooding pattern
immediately clear — Tejo, Mondego, Sado systems all visible.
**No changes needed.**

### 7. flood-depth
**Render:** `flood-depth-over-aerial.png`
**Styled in render:** Blue graduated (#deebf7 → #084594 → #8b0000)
**Assessment:** Dramatic improvement over previous purple/orange CEMS default. Light
blue shallow water, darker blue for moderate, transitioning to deep red for extreme
depths. Esri satellite base provides real-world context — fields, roads, the Tejo.
**No changes needed.** Graduated alpha (lighter = more transparent) keeps terrain visible.

### 8. ipma-warnings
**Render:** `ipma-warnings-over-dark.png`
**Styled in render:** Gold (#ffd700) district outlines, faint orange fill
**Assessment:** Warning zones visible without obscuring weather data underneath. The
faint fill + bold outline approach preserves the dark synoptic mood.
**Colorblind concern:** Red/orange warning distinction is NOT deuteranopia-safe.
Phase 2 mitigation: add pattern fills (hatching for red, solid for orange) or text
labels identifying warning level.

### 9. burn-scars
**Render:** `burn-scars-over-dark.png`
**Styled in render:** #c0631a fill at 78%, #8b4513 stroke
**Assessment:** Striking amber on dark navy. 3,147 wildfire polygons concentrated in
northern/central Portugal. Visually strong, instantly readable.
**No changes needed.**

### 10. discharge-ratio
**Render:** `discharge-over-terrain.png`
**Current style:** Blue dots for stations, with watershed basins and rivers
**Assessment:** Stations visible at 11 positions. For Phase 2, animate circle radius +
color encoding discharge magnitude (blue normal → red extreme). Current static render
shows placement, not the dynamic effect.
**Phase 2:** Animated proportional symbols.

### 11. precip-7day
**Render:** `precip-7day-over-dark.png`
**Current style:** Existing storm-total colormap (yellow-red)
**Spec target:** Sequential deep blues #f7fbff → #08306b
**Action:** Replace colormap to deep blues. Distinguish from daily precip by using
darker blue progression. The 7-day accumulation peaks at 324mm — domain [0, 350] maps
well to the 6-stop blue ramp.

### 12. mslp-contour
**Render:** `mslp-contours-over-dark.png`
**Restyled in render:** White, ~1.5px, full opacity
**Assessment:** CRITICAL IMPROVEMENT. The original 0.8px gray contours were invisible.
At 1.5px white, the bullseye depth effect around the low pressure center is clearly
visible. The concentric isobars draw the eye to the storm center. This single change
has the highest impact-per-effort ratio of any correction in this task.
**Locked in:** 1.5px white, 4hPa spacing, ~86% opacity.

---

## Composite Test Results

### Ch.4 Synoptic Stack
**Render:** `ch4-composite-test.png`
**Layers:** MSLP field + MSLP contours (white 1.5px) + precipitation + IPMA warning
zones (gold outlines) + L/H markers
**Verdict: PASS** — all layers legible simultaneously.
- White contours read clearly over blue MSLP field
- Precipitation visible over Portugal (needs blues colormap fix)
- Gold IPMA outlines visible without competing with contours (different visual channel:
  area outline vs line)
- L/H markers visible at pressure centers
**Key insight:** Layer legibility comes from using different visual channels: fill (precip),
line (contours), outline (warnings), symbol (L/H). When layers use the same channel
(e.g., two fills), they compete.

### Ch.7 Wildfire Reveal
**Render:** `ch7-reveal-test.png`
**Layers:** Flood extent (blue #2471a3) + wildfire scars (amber #c0631a)
**Verdict: PASS** — blue/amber contrast immediately distinct.
- Fires concentrate in northern/central mountains
- Floods concentrate in western river valleys
- The geographic complementarity IS the intellectual insight: the same soil that burned
  in summer couldn't absorb rain in winter
- Zero squinting required — the colors are on opposite sides of the color wheel

---

## Colorblind Simulation Results

### Method
Vienot et al. (1999) deuteranopia simulation matrix applied to both composite renders.

### Ch.4 Deuteranopia
**Render:** `ch4-composite-test-deuteranopia.png`
**Result:** PASS. White contours unaffected. Precipitation shifts to blue-yellow tones
(still visible). MSLP field readable. Gold IPMA outlines shift to olive (still visible).

### Ch.7 Deuteranopia
**Render:** `ch7-reveal-test-deuteranopia.png`
**Result:** PASS. Flood blue → purple-blue. Burn scars amber → olive-yellow.
Contrast maintained. Geographic pattern still immediately clear.

### Flagged Concern
IPMA warning Y/O/R system is NOT deuteranopia-safe (orange and red converge).
Mitigation for Phase 2: pattern fills or text labels on warning zones.

---

## Adjustments Summary

| Colormap | Status | Action for Phase 2 |
|----------|--------|-------------------|
| precipitation-blues | WRONG colormap | Full restyle: blues + lower ceiling or gamma |
| soil-moisture-browns | Acceptable blues, spec wants earth | Test both, narrative director chooses |
| sst-diverging | Good | No change |
| ivt-sequential | Good but multicolor | Remap to purple→white for web |
| satellite-ir | Excellent | Minor: darken warm end |
| flood-extent | Good | No change |
| flood-depth | Good (blue gradient) | No change |
| ipma-warnings | Functional | Add pattern fills for a11y |
| burn-scars | Excellent | No change |
| discharge-ratio | Placeholder | Phase 2: animated proportional symbols |
| precip-7day | WRONG colormap | Restyle to deep blues |
| mslp-contour | Fixed: 1.5px white | Locked in |
