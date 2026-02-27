# Basemap Decisions — Per-Chapter Mood Design

**Date:** 2026-02-27
**Calibrated against:** IMPACT-GAUGE.md findings (deep navy > charcoal, high saturation, bold contours)
**Screenshots:** `data/basemap/screenshots/` (6 renders)

---

## Design Principle

The impact gauge revealed our biggest gap: data floating on a black void vs. the reference's
data-rich, colorful backgrounds. The basemap strategy addresses this by ensuring EVERY chapter
has intentional background color and appropriate overlay density.

**Key rule from impact gauge:** NEVER use pure black (#000000) or charcoal (#1a1a2e).
All backgrounds use navy-tinted darks (#060e14 to #1a2a3a range) that feel atmospheric.

---

## Mood 1: Ultra-dark Ocean (Ch.0-1 — Hook + Flash-forward)

**Screenshot:** `ch0-ch1-ultra-dark.png`
**Background:** #060e14 (deep navy, almost black but with blue warmth)
**Basemap:** CARTO Dark Matter at 12% opacity — faint coastlines, barely-visible labels
**Data overlay:** CEMS flood extent in #2471a3 at ~55% fill opacity

**Rationale:** Maximum drama for the opening. The viewer enters a near-void and the flood
extent appears as the sole visual element — a ghostly blue shape that suggests the scale
of disaster before any explanation. The 12% basemap gives just enough geographic context
(Iberian coastline, Spain labels) without distracting from the flood data.

**Impact gauge check:** Background navy-tinted ✓. No charcoal. Flood blue pops against dark ✓.

**Phase 2 implementation:** `setLayoutProperty` to hide all CARTO label layers. Use MapLibre
`background-color: #060e14` as CSS, not tile-based. Flood extent loads from PMTiles.

---

## Mood 2: Dark Ocean Globe (Ch.2 — Atlantic Engine)

**Screenshot:** `ch2-dark-ocean.png`
**Background:** #0a212e (deep teal-navy — "ocean at night" feel)
**Basemap:** CARTO Dark Matter at 18% — land silhouette only
**Data overlay:** SST anomaly (diverging red-blue) fills the Atlantic

**Rationale:** This chapter explains the Atlantic energy that fueled the storms. The SST
anomaly FILLS the ocean — warm oranges dominate, showing the anomalous heat reservoir.
Land is just a dark silhouette for geographic reference. The spec calls for globe projection
which adds depth (Phase 2 MapLibre feature).

**Impact gauge check:** Background matches reference ocean tone ✓. SST creates the "rich
color field" that the reference achieves with wind speed ✓. Land silhouette correct ✓.

**Phase 2 implementation:** MapLibre globe projection. SST raster as image source with
crossfade temporal player. Storm track arcs as deck.gl ArcLayer. Wind particles animate
over SST field.

---

## Mood 3: Muted Terrain (Ch.3 — The Sponge Fills)

**Screenshot:** `ch3-muted-terrain.png`
**Background:** #1a2a3a (blue-gray, lighter than other moods)
**Basemap:** CARTO Dark Matter at 35% — moderate label/feature visibility
**Data overlay:** Soil moisture (blues sequential) over Portugal

**Rationale:** This is the unique chapter that needs to show the GROUND. Soil moisture
builds over 77 days — the viewer needs to see Portugal's topography through the data to
understand where water accumulates and why certain basins saturated first.

**Known gap:** CARTO Dark Matter doesn't provide hillshade or terrain relief. For the full
"muted terrain" mood, Phase 2 needs MapLibre terrain-v2 tiles with hillshade layer at low
opacity, tinted in muted greens/grays. The current render approximates this with higher
basemap opacity.

**Soil moisture colormap note:** The current blues are data-correct (high saturation = wet)
but the spec's `soil-moisture-browns` colormap (#8B6914 → #4A7C59 → #1B4965) would be
more thematically appropriate — earth tones for a soil chapter. Test in Part 2.

**Phase 2 implementation:** MapLibre `mapbox-terrain-v2` or MapTiler terrain tiles with
`raster-dem` source for hillshade. Soil moisture as temporal raster (3 days/scroll step).
Basemap green tint via `fill-color` on land polygons.

---

## Mood 4: Dark Synoptic (Ch.4 — Three Storms)

**Screenshot:** `ch4-dark-synoptic.png`
**Background:** #080c10 (near-black with navy tint)
**Basemap:** CARTO Dark Matter at 10% — faintest coastlines
**Data overlay:** MSLP field (blue gradient) + contours (white) + precipitation + L/H markers

**Rationale:** This is THE visual challenge — the chapter that must match broadcast weather
quality. The near-black canvas gives maximum contrast for luminous data layers: white isobar
contours creating "bullseye" depth around lows, blue precipitation wash, and (at runtime)
particle effects for wind.

**Impact gauge check:** Background correctly near-black with navy tint ✓. Contours visible
but need to be thicker (Part 2 fix) △. Precipitation uses old colormap (Part 2 fix) △.
Missing temperature color field (data gap flagged in impact gauge) △.

**Critical Part 2 fixes needed:**
1. Contour stroke: 0.8px gray → 1.5px white
2. Precipitation colormap: hot pink/magenta → sequential blues
3. L/H markers: larger, bolder
4. Future: temperature field beneath MSLP (needs ERA5 2m temp COGs)

**Phase 2 implementation:** Multiple MapLibre layers with strict ordering:
basemap → temperature field (future) → MSLP field → precipitation → contours → L/H markers.
WeatherLayers GL for particles and barbs.

---

## Mood 5: Terrain + Hydro (Ch.5 — When the Rivers Answered)

**Screenshot:** `ch5-terrain-hydro.png`
**Background:** #1a2a3a (blue-gray, same as Ch.3)
**Basemap:** CARTO Dark Matter at 45% — full Portuguese labels, geographic context
**Data overlay:** River network (264 segments) + 11 discharge stations + catchment basins

**Rationale:** The story shifts from atmosphere to ground. The viewer needs to see TERRAIN —
where rivers flow, where basins collect water, where monitoring stations sit. Higher basemap
opacity (45%) brings Portuguese place names and terrain features into view, anchoring the
hydrological data to recognizable geography.

**Impact gauge check:** Appropriate for chapter purpose — this mood prioritizes geographic
context over atmospheric drama ✓. Basin outlines clearly visible ✓. Station markers
(bright blue dots) stand out against the basemap ✓.

**Phase 2 implementation:** MapLibre terrain tiles with hillshade. River network as vector
source with width encoding Strahler order. Discharge stations as circles with animated radius
encoding flow magnitude. Portuguese labels from CARTO basemap at 45% or custom label layer.

---

## Mood 6: Aerial Hybrid (Ch.6 — What the Water Left Behind)

**Screenshot:** `ch6-aerial-hybrid.png`
**Background:** Esri World Imagery at 100% — full satellite view
**Basemap:** Satellite imagery (no dark tiles)
**Data overlay:** CEMS flood extent + depth over Salvaterra de Magos

**Rationale:** Intimacy. After 5 chapters of abstract weather data, the viewer zooms into
the real landscape — agricultural fields, towns, roads, the Tejo meanders. Flood data
overlaid on satellite imagery creates the "this really happened HERE" emotional impact.

**Colormap note:** Current CEMS categorized styling (purple extent, orange depth) needs
replacement with the spec's blue gradient (Part 2). Over satellite imagery, semi-transparent
blues (#2471a3 fill) will suggest water without hiding the terrain underneath.

**Phase 2 implementation:** Esri satellite tiles or Sentinel-2 true-color composites as
basemap. Flood extent from PMTiles. Flood depth from COG via titiler with blue gradient.
Light white labels (place names) at low opacity for geographic context.

---

## Summary: 6-Mood Darkness Gradient

| Mood | Hex | Relative darkness | Purpose |
|------|-----|-------------------|---------|
| Ch.4 Dark synoptic | #080c10 | Darkest | Maximum data contrast |
| Ch.0-1 Ultra-dark | #060e14 | Very dark | Dramatic opening |
| Ch.2 Dark ocean | #0a212e | Dark teal | Ocean atmosphere |
| Ch.3 Muted terrain | #1a2a3a | Medium-dark | See the ground |
| Ch.5 Terrain hydro | #1a2a3a | Medium-dark | Geographic context |
| Ch.6 Aerial | satellite | Full imagery | Real-world intimacy |

The progression tells the story: from abstract darkness (hook) → ocean (cause) →
ground (buildup) → atmospheric drama (crisis) → terrain (impact) → satellite (aftermath).
