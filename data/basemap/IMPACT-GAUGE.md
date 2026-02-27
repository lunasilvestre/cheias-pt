# Impact Gauge — Video Reference vs Current Renders

**Date:** 2026-02-27
**Method:** Side-by-side visual comparison of 6 WeatherWatcher14 contact sheets against
closest matching wx-audit renders from QGIS. Each section identifies specific gaps with
actionable color/opacity corrections.

---

## 1. Wind Particles (contact-wind-particles.png vs wx-audit/02-mslp-synoptic.png)

### Reference
Dense particle streamlines over a **vivid wind-speed color field**. The background is NOT
a dark void — it's a continuous, smooth-gradient color field encoding wind speed:
purple/magenta = jet stream core (~50+ m/s), green = moderate (~15-25 m/s),
yellow = light (~5-15 m/s), cyan/blue = calm (<5 m/s). Thousands of particle trails
flow through this field, adding texture. The overall impression is a "psychedelic swirl"
— dense, colorful, immersive. The globe/orthographic projection adds depth. Background
ocean is barely visible — the wind speed raster FILLS the view.

### Current (wx-audit/02)
MSLP pressure field (blue gradient) with thin white isobar contours. Background is
charcoal-dark (#1a1a2e to #2d2d44). No wind speed color field. No particles. The
contour lines are ~0.8px gray (#ccc) — barely visible against the blue field.
The composition is subdued, almost monochromatic blue-gray. Technically correct
atmospheric pressure data, but visually inert.

### Gap Analysis
| Attribute | Reference | Current | Fix |
|-----------|-----------|---------|-----|
| Background | Wind speed color field fills entire view | Dark charcoal void | Add wind speed raster layer beneath particles |
| Particle density | ~5,000-20,000 simultaneous | 0 (no particles in QGIS static render) | Particles are runtime-only (deck.gl); QGIS can show wind speed field |
| Color saturation | Vivid purple/green/yellow psychedelic | Muted blue-gray monotone | Wind speed raster needs high-saturation multi-hue colormap |
| Contour weight | N/A (no isobars in this view) | 0.8px gray — too thin | Increase to 1.5-2px white for synoptic views |
| Background color | Not visible (covered by data) | #1a1a2e charcoal | Target #0a1520 deep navy (visible only at edges/ocean) |

**Priority fix:** The missing wind speed color field is the single biggest gap. Without it,
particles float in a void. The reference's impact comes from particles OVER a rich color
field. For QGIS static tests, the wind speed raster with a purple-green-yellow colormap
is the proxy for what particles will add at runtime.

---

## 2. Precipitation (contact-precip-sweep-windy.png vs wx-audit/01-precipitation-windy.png)

### Reference
Soft precipitation bands in **deep blue-green-teal** sweeping across a dark blue ocean +
muted green terrain basemap. Rain areas have gaussian-blurred edges — "watercolor wash"
quality. Light rain is translucent pale blue; heavy rain is solid medium-dark blue/teal.
The basemap terrain (faint green land, dark blue ocean) is visible through lighter
precipitation. No hard grid-cell boundaries. Overall: atmospheric, soft, wet-looking.

### Current (wx-audit/01)
Precipitation over near-black (#0a0a0a) background using a **hot pink/magenta/blue**
colormap. Portugal silhouette with sharp mask edges. The colormap is physically wrong —
precipitation doesn't read as "rain" in magenta. The land mask has a hard boundary
with no feathering. NW Portugal shows vivid magenta (high precip), fading to blue in
the south.

### Updated Status (P1.B5 re-render)
The P1.B5 task re-rendered all 77 precipitation PNGs with a **sequential blues** colormap
and Gaussian blur (sigma=3). Viewing 2026-01-28 (storm peak): soft, feathered edges with
pale blue washes. The blur quality is GOOD — soft watercolor feel achieved. But the
color **intensity is too low** — even at storm peak, the render is pale/washed-out rather
than showing the vivid medium-to-deep blues of the reference. Against a dark basemap the
translucent blues will show, but need more saturation at the high end.

### Gap Analysis
| Attribute | Reference | Current (re-rendered) | Fix |
|-----------|-----------|----------------------|-----|
| Colormap hue | Blue-green-teal | Sequential blues (pale) | Correct hue family; increase saturation at high end |
| Color intensity | Solid medium blue at storm peak | Pale, washed-out | Lower the "zero" threshold so more pixels reach mid-range colors |
| Edge quality | Gaussian blur, soft watercolor | Gaussian blur sigma=3 | GOOD — matches reference quality |
| Background | Dark blue ocean + muted green land | Transparent (designed for overlay) | Needs dark synoptic basemap beneath |
| Opacity scaling | Proportional to intensity | Proportional alpha | Correct approach; needs wider dynamic range |
| Mask feathering | Soft edges blend into terrain | 0.005° erosion + 2px feather | Reasonable; verify against dark basemap |

**Priority fix:** Increase colormap saturation — the high end (#08519c) is correct but
the normalization makes most storm pixels land in the pale range. Consider:
(a) lowering the ceiling from 80mm to 50mm/day, or (b) using a power-law stretch
(gamma < 1) so moderate rainfall gets deeper blues sooner.

---

## 3. MSLP Isobars (contact-mslp-animation.png vs wx-audit/13-synoptic.png)

### Reference
**Temperature color field** (NOT pressure) as the primary raster: deep red/salmon = warm
subtropical air mass, deep blue/navy = cold polar air. Smooth continuous gradient — no
discrete bands. White isobar contour lines (~4 hPa spacing) drawn ON TOP at full opacity,
1.5-2px stroke. L/H pressure center markers. The warm/cold boundary (frontal zone) is
the most visually striking element — a sharp color transition sweeping across the map.
Background: temperature field covers entire view. Coastlines faintly visible through.

### Current (wx-audit/13)
MSLP blue gradient field + thin gray contour lines + a small pink/magenta precipitation
patch over Portugal. The "synoptic" composition layers pressure (blue field) + precipitation
(pink blob) + contours (thin gray lines). Missing entirely: the temperature field that
makes the reference so visually dramatic. The contours are ~0.8px #ccc — need to be
2x wider and white. The precipitation blob in pink/magenta competes with the MSLP blue
field rather than complementing it.

### Gap Analysis
| Attribute | Reference | Current | Fix |
|-----------|-----------|---------|-----|
| Primary raster | Temperature (red-blue diverging) | MSLP (blue sequential) | Add 2m temperature raster layer for synoptic view |
| Warm/cold contrast | Dramatic red→blue transition | Absent | Temperature field is the "money shot" — highest-impact addition |
| Contour stroke | White, 1.5-2px, full opacity | #ccc, 0.8px, 0.6 opacity | Double width, pure white, full opacity |
| Contour spacing | ~4 hPa | ~4 hPa | Correct |
| L/H markers | Clear L/H with pressure value | Present but static | Need temporal versions |
| Background | Temperature raster fills view | Charcoal dark base | Temperature raster should cover background |
| Precipitation | Not in this view (separate layer) | Pink blob over MSLP | Remove precip from synoptic view; test separately |

**Priority fix:** The temperature field is the #1 missing element. Without it, our synoptic
view is a monochromatic blue field with barely-visible contours. The reference achieves its
drama through the warm/cold color opposition. We need ERA5 2m temperature COGs — check
if available or fetchable. Alternatively, use wind direction/speed as a proxy for air mass
character (not as visually striking but better than monotone blue).

**Note:** We do NOT have ERA5 2m temperature COGs currently. This is a data gap for the
full synoptic experience. For Phase 1 cartographic design, we test with what we have (MSLP
field + contours) and flag temperature as a Phase 2 data fetch requirement.

---

## 4. Satellite IR (contact-satellite-motion.png vs wx-audit/06-satellite-ir.png)

### Reference
Two distinct visual modes:
- **Frames 1-2 ("EXPLOSIVE CYCLOGENESIS"):** Wind streamlines in blue/cyan on a dark
  navy-black background. Thin white/blue 1-2px lines showing tight cyclonic rotation.
  Hypnotic spiral pattern. Dark blue background tint (~#0a1830).
- **Frames 5-7 ("STING JET"):** High-contrast satellite IR. Bright white clouds against
  very dark ocean/surface. Classic inverted-grayscale IR look. Comma cloud structure
  clearly visible. Dramatic contrast between cloud tops and clear sky.

### Current (wx-audit/06)
**Excellent inverted-grayscale IR render.** White cloud tops, dark ocean surface, high
contrast. Cloud structure (frontal bands, comma-head edge) clearly visible. This is
actually the CLOSEST match to reference quality among all our renders. The Meteosat
IR imagery is well-processed.

### Gap Analysis
| Attribute | Reference | Current | Fix |
|-----------|-----------|---------|-----|
| IR contrast | High — white clouds, black ocean | High — very close match | GOOD. Minor: slightly increase contrast curve |
| Cloud definition | Sharp comma-cloud edges | Good structure visible | Acceptable |
| Background darkness | True black ocean | Dark gray-black ocean | Slightly darken the warm-surface end of the ramp |
| Cyclone streamlines | Wind streamlines in blue/cyan overlay | Not present | Runtime effect (deck.gl particles at cyclone scale) |
| Text annotations | "EXPLOSIVE CYCLOGENESIS", "STING JET" | Not present | Phase 2 narrative annotations |
| Side-by-side layout | Atlantic + zoomed Portugal split | Single view | Phase 2 UI feature |

**Assessment:** This is our strongest layer. The IR satellite render is 80-90% of reference
quality already. Minor adjustments: darken warm end of IR grayscale to increase cloud/ocean
contrast. The wind streamlines and annotations are runtime/UI features, not colormap issues.

---

## 5. Full Synoptic Composite (contact-synoptic-radar.png vs wx-audit/23-full-synoptic.png)

### Reference
The most complex composition: radar precipitation (green/yellow/red areas) + wind barbs
(standard meteorological notation) + isobar contours + country borders on a light terrain
basemap. The reference uses the WXCharts/DWD aesthetic — more "traditional weather chart"
than our dark-canvas aesthetic. Multiple information layers are readable simultaneously
because each uses a distinct visual channel: color (radar), line (isobars), symbol (barbs),
and base (terrain). ~5 layers visible without clutter.

### Current (wx-audit/23)
MSLP contours + wind visualization (dense orange vertical bars/barbs) + precipitation +
dark basemap. **Too cluttered.** The wind barbs are rendered as dense vertical orange bars
that dominate the composition. The precipitation (blue/magenta) competes with the MSLP
blue field. Contours are barely visible. The dark background makes everything harder to
read than the reference's light terrain base.

### Gap Analysis
| Attribute | Reference | Current | Fix |
|-----------|-----------|---------|-----|
| Layer readability | 5 layers distinct and readable | 3+ layers conflicting | Reduce barb density; use thinner, white barbs |
| Wind barbs | Standard meteorological barbs, sparse | Dense orange vertical bars | Re-style: thinner, white, every 2nd or 3rd point |
| Precipitation color | Green/yellow/red (radar palette) | Blue/magenta (wrong palette) | Use blues for our narrative (not radar green) |
| Background | Light terrain (WXCharts style) | Dark canvas | Keep dark for our aesthetic — but ensure sufficient contrast |
| Contour visibility | Clear white lines on light terrain | Lost in clutter | Must be readable: 1.5px white, on top of stack |
| Composite readability | Clean — each layer has its channel | Muddy — layers compete | Strict layer ordering: basemap → precip → MSLP field → contours → barbs/markers |

**Priority fix:** The layer stacking order is the core issue. Current render layers multiple
semi-transparent rasters that blend into mud. Fix: (1) reduce wind barb density dramatically,
(2) ensure contours are drawn ON TOP of all rasters, (3) use distinct visual channels per
layer (fill for precip, line for contours, symbol for wind, point for markers).

**Design decision:** We are NOT replicating the WXCharts light-terrain aesthetic. Our dark
canvas is a deliberate design choice for the geo-narrative. The challenge is making 3-4
layers legible on dark — which requires higher contrast and stricter separation than
light backgrounds demand.

---

## 6. Temporal Evolution (contact-precip-mslp-evolution.png vs wx-audit/28-money-synoptic.png)

### Reference
A heterogeneous contact sheet showing the full range of the video's visual vocabulary:
- Frames 1-3: Green precipitation accumulation maps (WXCharts style) — vivid green bands
  showing total rainfall over forecast periods
- Frame 4: Dark screen (transition)
- Frame 5: Dramatic psychedelic pressure/temperature field — vivid purple/orange/yellow
  swirls showing frontal zones. The MOST visually striking frame in the entire video.
- Frames 6-7: SST-like diverging fields — blue ocean, red-orange warm areas, smooth
  gradient

### Current (wx-audit/28)
Same as wx-audit/13 — MSLP contours + precipitation on dark background. Does not attempt
any of the reference's visual vocabulary. No accumulation maps, no vivid temperature
fields, no SST diverging view.

### Gap Analysis
| Attribute | Reference | Current | Fix |
|-----------|-----------|---------|-----|
| Visual variety | 3+ distinct rendering modes | 1 mode (MSLP+precip) | Each chapter needs its own visual identity |
| Accumulation maps | Vivid green bands | Not rendered | Use precip-7day COGs with green/blue ramp |
| Temperature drama | Vivid purple/orange/yellow swirls | Absent | ERA5 2m temperature (data gap flagged above) |
| SST diverging | Blue-white-red smooth gradient | Not rendered in synoptic | SST raster exists; needs diverging colormap test |
| Color intensity | Vivid, saturated, dramatic | Muted, monochromatic | Increase saturation across all colormaps |
| Overall impression | "Wow — professional weather broadcast" | "Developer demo — technically correct" | The gap is ARTISTIC, not technical |

---

## Summary: The 5 Highest-Impact Corrections

Ranked by visual impact on the final product:

### 1. Add wind speed / temperature color field beneath data layers
The reference NEVER shows data floating on a black void. There is always a smooth,
colorful raster field (wind speed OR temperature) that fills the view. This is the
single biggest gap between "developer demo" and "broadcast quality."

### 2. Increase colormap saturation across all layers
Our colormaps are too muted. The reference uses vivid, saturated colors. The precipitation
blues need more intensity at the high end. The MSLP/synoptic view needs the dramatic
red-blue temperature contrast. Even our strongest layer (satellite IR) could push
contrast higher.

### 3. Fix contour stroke weight: 0.8px gray → 1.5-2px white
The isobar contours should be a prominent visual element creating the "bullseye" depth
effect around low pressure centers. Currently they are barely visible background
decoration.

### 4. Reduce wind barb/symbol density in composite views
Dense, uniform symbols create visual noise. Thin out to every 2nd-3rd grid point, use
white/light color, and ensure they don't compete with contours or precipitation fill.

### 5. Shift background from charcoal (#1a1a2e) to deep navy (#0a1520)
Pure black or charcoal backgrounds look "techy". The reference consistently uses deep
navy/ocean tints that feel atmospheric. The spec calls for #0a1520 (ultra-dark) to
#0a212e (dark ocean) — both significantly bluer than our current charcoal.

---

## Data Gaps Identified

| Missing data | Needed for | Priority | Action |
|--------------|-----------|----------|--------|
| ERA5 2m temperature COGs | Synoptic temperature field (Ch.4) | HIGH — Phase 2 prerequisite | Fetch via CDS API |
| Wind speed raster (derived from U/V) | Background color field (Ch.2, Ch.4) | MEDIUM — computable from existing U/V | Script to compute sqrt(u²+v²) |
| VIS satellite imagery | True-color comma cloud (Ch.4) | LOW — IR is sufficient | EUMETSAT VIS already partially fetched |

---

## Baseline for Part 1

These gap findings calibrate every basemap and colormap decision in Parts 1 and 2:
- Backgrounds must be navy-tinted, not charcoal
- Colormaps must push saturation higher than first instinct
- Contours must be bold white, not timid gray
- Layer stacking must respect visual channels (fill / line / symbol / point)
- Static QGIS renders proxy for runtime particle effects — test with color fields instead
