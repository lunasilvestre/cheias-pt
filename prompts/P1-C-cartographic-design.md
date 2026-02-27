# P1.C — Cartographic Design (Claude Desktop + QGIS MCP)

## Prerequisites

- **Run in Claude Desktop** (not Claude Code) — needs QGIS MCP tools for render/iterate
- **QGIS open** with `cheias-scrollytelling.qgz` loaded before starting
- **Human-in-the-loop** — 3 STOP points for visual review

## Mission

Design the visual foundation for every chapter: basemap moods and colormaps, tested against
real data in QGIS, and calibrated against the proven visual compositions from the
WeatherWatcher14 motion analysis. Produce a palette.json that Phase 2 rendering consumes.

**Read first:**
1. `CLAUDE.md`
2. `prompts/sprint-backlog.md` (P1.C1, P1.C2)
3. `prompts/scroll-timeline-symbology.md` §1 (basemap strategy) and §2 (layer symbology)
4. `data/video-analysis/MOTION-ANALYSIS.md` — the visual quality target
5. `prompts/creative-reports/effect-audit.md` — gap analysis between spec and prototype

## Context: What Already Exists

You're not starting from zero. There are:

- **6 contact sheets** from the WeatherWatcher14 video — these are the VISUAL TARGET:
  ```
  data/video-analysis/contact-wind-particles.png      → Ch.4 particle density/color reference
  data/video-analysis/contact-precip-sweep-windy.png   → Ch.4 precipitation color reference
  data/video-analysis/contact-mslp-animation.png       → Ch.4 isobar/synoptic reference
  data/video-analysis/contact-satellite-motion.png     → Ch.4 IR cloud imagery reference
  data/video-analysis/contact-synoptic-radar.png       → Ch.4 composite layer reference
  data/video-analysis/contact-precip-mslp-evolution.png → Ch.4 temporal evolution reference
  ```
- **509 extracted video frames** in `data/video-analysis/frames/`
- **30+ wx-audit renders** in `data/qgis/renders/wx-audit/` — previous QGIS compositions
- **18 QML styles** in `data/qgis/styles/` — existing layer styling
- **All COGs on disk** — every data type has representative files

---

## Part 0: Impact Gauging (NEW — before any design work)

**Purpose:** Establish the visual bar. Before designing anything, compare what we HAVE
against the reference target so we know exactly where the gaps are.

### What to Do

1. **Load the 6 contact sheets** into QGIS as raster layers (or view them side-by-side
   in an image viewer). These are frames from a professional weather broadcast — note:
   - Background darkness level and ocean color
   - Particle density and trail opacity
   - Precipitation color ramp (the vivid blues/pinks, NOT our current yellow-red)
   - Isobar weight and spacing against the dark background
   - Satellite IR contrast (bright white clouds against dark)
   - How many layers are visible simultaneously without clutter

2. **Load the closest matching wx-audit renders** and compare side-by-side:

   | Reference (video) | Our render | Key comparison |
   |-------------------|-----------|----------------|
   | contact-wind-particles.png | wx-audit/02-mslp-synoptic.png | Particle density, background color |
   | contact-precip-sweep-windy.png | wx-audit/01-precipitation-windy.png | Precip colormap, blur quality |
   | contact-mslp-animation.png | wx-audit/13-synoptic.png | Isobar weight, H/L marker style |
   | contact-satellite-motion.png | wx-audit/06-satellite-ir.png | IR contrast, cloud definition |
   | contact-synoptic-radar.png | wx-audit/23-full-synoptic.png | Layer composite readability |

3. **For each pair, note the GAP:**
   - Is our background too light/dark? What hex value does the reference use?
   - Are our colormaps washed out compared to the reference?
   - Is our layer stacking too cluttered or too sparse?
   - What specific color/opacity adjustments would close the gap?

4. **Write `data/basemap/IMPACT-GAUGE.md`** documenting the comparison:
   ```markdown
   ## Wind Particles (contact-wind-particles.png vs wx-audit/02)
   Reference: Dark navy background (~#0a1520), particles vivid purple-white,
   density ~5000+, trail decay visible per-segment.
   Current: Background too black (#0a0a0a), particles sparse, no background
   wind field. Gap: need navy shift + density increase + wind speed raster.
   
   ## Precipitation (contact-precip-sweep-windy.png vs wx-audit/01)
   ...
   ```

5. **STOP. Present the IMPACT-GAUGE.md for review.** This calibrates everything that follows.

### Output
```
data/basemap/IMPACT-GAUGE.md    (gap analysis, ~6 comparisons)
```

---

## Part 1: Per-Chapter Basemap Styles (P1.C1)

**Start only after Part 0 is reviewed.** The impact gauge tells you what background colors
and contrast levels to target — don't guess.

### The 6 Basemap Moods

| Mood | Background | Labels | Terrain | Chapters | Reference frame |
|------|-----------|--------|---------|----------|-----------------|
| Ultra-dark ocean | #060e14 ocean, #0a1520 land | None | Off | Ch.0-1 | — (title screen) |
| Dark ocean globe | #0a212e ocean, land silhouette | None | Off | Ch.2 | contact-wind-particles (ocean tone) |
| Muted terrain | Subtle hillshade, muted greens | None | Hillshade | Ch.3 | — (unique to our narrative) |
| Dark synoptic | Near-black, faint coastlines | Minimal | Off | Ch.4 | contact-synoptic-radar (THE key reference) |
| Terrain + hydro | Hillshade, rivers visible | Portuguese | On | Ch.5 | wx-audit/29-iberia-hydro |
| Aerial hybrid | Satellite beneath flood data | Light | On | Ch.6 | — (Sentinel-2 based) |

### What to Do

1. For each mood, set up a QGIS composition:
   - Canvas background color (from impact gauge findings)
   - Coastline/border styling
   - Overlay with the chapter's PRIMARY data layer:

   | Mood | Overlay with | Zoom to |
   |------|-------------|---------|
   | Ultra-dark | Flood extent (data/flood-extent/combined.pmtiles) | Portugal |
   | Dark ocean | SST anomaly (data/cog/sst/2026-01-15.tif) | Atlantic |
   | Muted terrain | Soil moisture (data/cog/soil-moisture/2026-01-20.tif) | Portugal |
   | Dark synoptic | MSLP contours + precipitation (existing QMLs) | Iberia |
   | Terrain + hydro | Rivers + stations (data/qgis/rivers-portugal.geojson) | Portugal |
   | Aerial hybrid | Flood depth (data/flood-depth/salvaterra-depth-monit01.tif) | Salvaterra z11 |

2. **Compare each composition against the closest video reference frame.**
   Does the background match? Does the data pop against it?

3. Export 6 screenshots (~1200x800) to `data/basemap/screenshots/`.

4. Create `data/basemap/cheias-dark.json` — chapter group definitions (design document
   for Phase 2, not a working MapLibre style):
   ```json
   {
     "chapter_groups": {
       "ch0-ch1": { "ocean": "#060e14", "land": "#0a1520", "labels": false, "terrain": false },
       "ch2": { "ocean": "#0a212e", "land": "#12201a", "labels": false, "terrain": false },
       "ch3": { "ocean": "#1a2a3a", "land": "muted-green", "labels": false, "terrain": "hillshade" },
       "ch4": { "ocean": "#080c10", "land": "#0a0e12", "labels": "minimal", "terrain": false },
       "ch5": { "ocean": "#1a2a3a", "land": "terrain", "labels": "portuguese", "terrain": "hillshade" },
       "ch6": { "ocean": "satellite", "land": "satellite", "labels": "light", "terrain": true }
     }
   }
   ```

5. Write `data/basemap/BASEMAP-DECISIONS.md` — rationale per mood, referencing the
   impact gauge comparisons.

6. **STOP. Present the 6 basemap screenshots for review.**

### Output
```
data/basemap/
  cheias-dark.json
  BASEMAP-DECISIONS.md
  IMPACT-GAUGE.md              (from Part 0)
  screenshots/
    ch0-ch1-ultra-dark.png
    ch2-dark-ocean.png
    ch3-muted-terrain.png
    ch4-dark-synoptic.png
    ch5-terrain-hydro.png
    ch6-aerial-hybrid.png
```

---

## Part 2: Colormap Palette + Composite Tests (P1.C2)

**Start only after Part 1 basemaps are approved.**

### The 12 Colormaps

| ID | Layer | Spec stops | Domain | Test over mood | Video reference |
|----|-------|-----------|--------|----------------|-----------------|
| `precipitation-blues` | Precip | #e8f4f8→#6baed6→#08519c | 0-80 mm/day | Dark synoptic | contact-precip-sweep (Windy blues/pinks) |
| `soil-moisture-browns` | SM | #8B6914→#4A7C59→#1B4965 | 0.1-0.5 m³/m³ | Muted terrain | — (unique) |
| `sst-diverging` | SST | blue→white→red | -2°C to +2°C | Dark ocean | — |
| `ivt-sequential` | IVT | transparent→purple→white | 0-800 kg/m/s | Dark ocean | — |
| `satellite-ir` | IR | white (cold)→black (warm) | BT range | Dark synoptic | contact-satellite-motion |
| `flood-extent` | Flood | #2471a3 fill, #1a5276 stroke | binary | Ultra-dark | wx-audit/24-flood-extent-fixed |
| `flood-depth` | Depth | #deebf7→#4292c6→#084594→#8b0000 | 0-7m | Aerial | — |
| `ipma-warnings` | Warnings | #ffd700→#ff8c00→#dc143c | Y/O/R | Dark synoptic | — |
| `burn-scars` | Wildfire | #c0631a fill, #8b4513 stroke | binary | Ultra-dark | — |
| `discharge-ratio` | Columns | #3498db→#e74c3c | 1×-12× | Terrain | — |
| `precip-7day` | Accum | #f7fbff→#6baed6→#08306b | 0-350mm | Dark synoptic | — |
| `mslp-contour` | Isobars | white 1.5px, 4hPa | — | Dark synoptic | contact-mslp-animation |

### What to Do

1. **For each colormap:**
   - Load representative COG in QGIS
   - Apply colormap (start from spec, adjust based on impact gauge)
   - Overlay on the approved basemap mood from Part 1
   - Compare with video reference where available
   - Note any adjustments needed

2. **Export 12 screenshots** to `data/colormaps/screenshots/`

3. **Run two critical composite tests:**

   **Ch.4 Synoptic Stack** — the hardest visual challenge:
   - MSLP contours (white) + precipitation (blues) + IPMA warnings (Y/O/R)
   - Over dark synoptic basemap
   - Compare against `contact-synoptic-radar.png` — is ours as readable?
   - Are all 3 layers legible simultaneously?
   - Export: `data/colormaps/screenshots/ch4-composite-test.png`

   **Ch.7 Wildfire Reveal** — the intellectual punchline:
   - Flood extent (blue #2471a3) + burn scars (amber #c0631a)
   - Over dark national basemap
   - Is the fire→flood color contrast IMMEDIATELY legible? No squinting.
   - Export: `data/colormaps/screenshots/ch7-reveal-test.png`

4. **Colorblind check:** Run deuteranopia simulation on the Ch.4 composite and Ch.7
   reveal. Both must remain legible. Blues and ambers typically survive deuteranopia
   but verify.

5. **STOP. Present all 14 screenshots for review** (12 individual + 2 composites).

6. After approval, create `data/colormaps/palette.json`:
   ```json
   {
     "precipitation-blues": {
       "type": "sequential",
       "stops": [[0, "#e8f4f8"], [0.3, "#b3d9e8"], [0.6, "#6baed6"], [0.8, "#3182bd"], [1.0, "#08519c"]],
       "domain": [0, 80],
       "units": "mm/day",
       "alpha_mode": "proportional",
       "blur_sigma": 3,
       "chapters": ["ch3", "ch4"],
       "colorblind_safe": true,
       "reference": "contact-precip-sweep-windy.png — adjusted from Windy pinks to blues",
       "notes": "Gaussian blur sigma=3 applied before colormapping"
     }
   }
   ```

7. Write `data/colormaps/COLORMAP-DECISIONS.md` — rationale, adjustments from spec,
   colorblind results, video reference comparison notes.

### Output
```
data/colormaps/
  palette.json
  COLORMAP-DECISIONS.md
  screenshots/
    precipitation-blues-over-dark.png
    soil-moisture-over-terrain.png
    sst-diverging-over-ocean.png
    ivt-over-ocean.png
    satellite-ir-over-dark.png
    flood-extent-over-dark.png
    flood-depth-over-aerial.png
    ipma-warnings-over-dark.png
    burn-scars-over-dark.png
    discharge-over-terrain.png
    precip-7day-over-dark.png
    mslp-contours-over-dark.png
    ch4-composite-test.png
    ch7-reveal-test.png
```

---

## Session Flow

```
Part 0 (Impact Gauge)
  Load video contacts + wx-audit renders → compare → write IMPACT-GAUGE.md
  → STOP → human reviews gap analysis

Part 1 (Basemaps)
  Design 6 moods calibrated to impact gauge → render in QGIS → 6 screenshots
  → STOP → human reviews basemaps

Part 2 (Colormaps)
  Test 12 colormaps over approved basemaps → 2 composite tests → colorblind check
  → STOP → human reviews palette
  → Write palette.json + decisions doc
```

Three natural pauses. Your eye is the quality gate at each one.

## Git

Branch: `v2/phase-1`
Commits:
- `P1.C0: impact gauge — video reference vs current renders comparison`
- `P1.C1: per-chapter basemap style design with screenshots`
- `P1.C2: complete colormap palette with QGIS verification`

## Definition of Done

- [ ] `data/basemap/IMPACT-GAUGE.md` — 6 gap comparisons with specific color corrections
- [ ] 6 basemap mood screenshots calibrated against video reference
- [ ] `data/basemap/cheias-dark.json` chapter group definitions
- [ ] 12 colormap screenshots + 2 composite tests
- [ ] Ch.4 composite: 3 layers legible simultaneously
- [ ] Ch.7 reveal: blue/amber contrast immediately distinct
- [ ] Both composites pass deuteranopia check
- [ ] `data/colormaps/palette.json` (machine-readable, all 12 colormaps)
- [ ] `data/colormaps/COLORMAP-DECISIONS.md` with reference comparison notes
