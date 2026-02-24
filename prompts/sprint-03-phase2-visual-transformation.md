# cheias.pt — Sprint 03, Phase 2: Visual Transformation

## Mission

Replace the uninformative circle dot grids with continuous heatmap surfaces and wire temporal animation for all chapters that need it. This is the phase where the data starts SPEAKING through the map.

**Single-agent task.** Read `CLAUDE.md` for project context and `FORENSIC-REPORT.md` for the full gap analysis.

## Context: What Failed in Sprint 02

Three compounding failures explain every visual QA issue in Chapters 3-5 and 8:

1. **Circle layers instead of continuous surfaces** — 256 scattered dots at 4-10px cannot convey spatial patterns to citizens
2. **Temporal animation wired for Ch3 only** — Ch4 and Ch8 are static despite having 77-frame temporal data ready
3. **Soil moisture normalization kills dynamic range** — values range 0.303→1.000 but color ramp starts at 0, so Dec 1 already looks "mostly blue"

The data pipeline is complete. The temporal-player.js is proven (Ch3 works). The fix is in how data gets translated to visual representation.

## Data Value Ranges (verified)

### Soil Moisture (data/frontend/soil-moisture-frames.json)
- 77 frames, 256 points each, `value` property (0-1 normalized)
- Dec 1: min=0.303, max=1.000, mean=0.706
- Jan 8: min=0.514, max=1.000, mean=0.802  
- Feb 15: min=0.660, max=1.000, mean=0.927
- **Global: min=0.303, max=1.000**
- Problem: current ramp maps 0→white, 1→blue. Dec 1 mean is 0.706 — already deep blue.

### Precipitation (data/frontend/precip-frames.json)
- 77 frames, 256 points each, `value` property (mm/day)
- Dec 1: min=0, max=19.6, mean=2.5
- Jan 29 (Kristin): min=0.4, max=64.6, mean=14.6
- Feb 6 (Leonardo): min=0.8, max=59.4, mean=11.9
- Feb 11 (Marta): min=0, max=60.6, mean=15.6
- **Storm days clearly spike to 50-65mm**
- Currently uses `precip-storm-totals.json` (static) — the 77-frame `precip-frames.json` is **never loaded**

### Precondition Index (data/frontend/precondition-frames.json)
- 77 frames, 256 points, `index` property (raw value 0-60), `risk_class` property (green/yellow/orange/red)
- Dec 1: 228 green, 9 yellow, 5 orange, 14 red
- Jan 25 (pre-Kristin): 69 green, 74 yellow, 20 orange, **93 red** ← the thesis proof!
- Feb 2 (post-Kristin): 3 green, 52 yellow, 44 orange, **157 red** ← nearly all critical
- **This data PROVES the precondition thesis but is currently NEVER LOADED**

### Discharge (data/frontend/discharge-timeseries.json)
- 11 stations with full timeseries
- Peak discharge_ratio varies by station (some >5x, some ~2x)

## Changes Required

### Change 1: Soil moisture → heatmap layer (Ch3)

**File: `src/layer-manager.js`** — Replace the `soil-moisture-animation` layer definition.

Current (lines 33-47):
```javascript
'soil-moisture-animation': {
    type: 'circle',
    source: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
    paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 5, 4, 9, 10],
      'circle-color': [
        'interpolate', ['linear'], ['get', 'value'],
        0, '#f7f7f7',
        0.5, '#67a9cf',
        1.0, '#2166ac',
      ],
      'circle-opacity': 0,
      'circle-stroke-width': 0,
    },
},
```

Replace with a MapLibre `heatmap` layer:
```javascript
'soil-moisture-animation': {
    type: 'heatmap',
    source: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
    paint: {
      // Use re-normalized value as weight (see Change 2)
      'heatmap-weight': ['get', 'value'],
      'heatmap-intensity': 1,
      // Radius must create continuous coverage for 256 points at ~0.25° spacing
      // At zoom 7 (Ch3 default), 0.25° ≈ 20-25 pixels — need radius ≥ 20
      'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 5, 15, 7, 25, 9, 45],
      // Diverging ramp: warm/brown (dry) → neutral → cool/blue (saturated)
      // Design doc: "heatmap morphing from blue (dry) to red (saturated)" but
      // the actual intent is dry=visible-warm → saturated=visible-blue
      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0,    'rgba(0,0,0,0)',
        0.1,  '#a6611a',   // dry brown
        0.3,  '#dfc27d',   // tan
        0.5,  '#f5f5f5',   // neutral white
        0.7,  '#80cdc1',   // teal
        0.9,  '#018571',   // deep teal
        1.0,  '#003c30',   // saturated dark
      ],
      'heatmap-opacity': 0,
    },
},
```

**Critical note on heatmap-density:** This is NOT a direct mapping of the `value` property. It's computed from the spatial kernel density × weight. For a regular grid with uniform spacing, the density peaks should correlate with weight values, but the absolute density value depends on zoom level and radius. You may need to tune the color stops after seeing it render. The key test: at zoom 7, Dec 1 should look warm/brown (dry) and Feb 5 should look dark teal/blue (saturated). If the colors don't differentiate, adjust `heatmap-intensity` (try 0.5-2.0) or the radius.

**Also update `soil-moisture-snapshot`** (same approach, used in Ch5 as background):
```javascript
'soil-moisture-snapshot': {
    type: 'heatmap',
    source: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
    paint: {
      'heatmap-weight': ['get', 'value'],
      'heatmap-intensity': 1,
      'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 5, 15, 7, 25, 9, 45],
      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0,    'rgba(0,0,0,0)',
        0.1,  '#a6611a',
        0.3,  '#dfc27d',
        0.5,  '#f5f5f5',
        0.7,  '#80cdc1',
        0.9,  '#018571',
        1.0,  '#003c30',
      ],
      'heatmap-opacity': 0,
    },
},
```

**Update `setLayerOpacity` and `getOpacityProperty`:** The `heatmap` type uses `heatmap-opacity`. Add this to the switch statement in `getOpacityProperty()`:
```javascript
case 'heatmap': return 'heatmap-opacity';
```

### Change 2: Re-normalize soil moisture values

**File: `src/chapter-wiring.js`** — In `pointsToGeoJSON()` or in `enterChapter3()`, re-normalize the value from the raw range [0.303, 1.0] to [0, 1]:

```javascript
// Before passing to heatmap, re-normalize for visual range
const SOIL_MIN = 0.303;
const SOIL_MAX = 1.0;
const SOIL_RANGE = SOIL_MAX - SOIL_MIN;

function normalizeValue(raw) {
  return Math.max(0, Math.min(1, (raw - SOIL_MIN) / SOIL_RANGE));
}
```

Apply this when building the GeoJSON for soil moisture frames. Either modify `pointsToGeoJSON` to accept a normalization function, or do it inline in the `enterChapter3` and `enterChapter5` callbacks.

After re-normalization:
- Dec 1 min (0.303) → 0.0 (warm/dry end of ramp)
- Dec 1 mean (0.706) → 0.578 (neutral-ish)
- Feb 15 min (0.660) → 0.512 (just past neutral)
- Feb 15 max (1.0) → 1.0 (saturated end)

This creates visible progression from warm→cool as soil saturates.

### Change 3: Precipitation → heatmap layer with temporal animation (Ch4)

**File: `src/layer-manager.js`** — Replace the `precipitation-accumulation` layer:

```javascript
'precipitation-accumulation': {
    type: 'heatmap',
    source: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
    paint: {
      // Daily precip in mm — normalize to 0-1 range for heatmap weight
      // Storm days peak at ~65mm; use 50mm as the "saturated" threshold
      'heatmap-weight': [
        'interpolate', ['linear'], ['get', 'value'],
        0, 0,
        10, 0.3,
        25, 0.6,
        50, 0.9,
        65, 1.0,
      ],
      'heatmap-intensity': 1.2,
      'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 5, 15, 7, 25, 9, 45],
      // Warm ramp: transparent → yellow → orange → red → deep red
      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0,    'rgba(0,0,0,0)',
        0.15, '#ffffb2',    // light yellow
        0.3,  '#fecc5c',    // yellow
        0.5,  '#fd8d3c',    // orange
        0.7,  '#f03b20',    // red
        0.9,  '#bd0026',    // deep red
        1.0,  '#800026',    // very deep red
      ],
      'heatmap-opacity': 0,
    },
},
```

**File: `src/chapter-wiring.js`** — Wire `enterChapter4()` to use temporal animation:

Current enterChapter4 loads static totals only:
```javascript
export async function enterChapter4() {
  if (!map) return;
  if (ch3Initialized) leaveChapter3();
  const data = await loadPrecipStormTotals();
  const geojson = pointsToGeoJSON(data.points, 'total_mm');
  updateSourceData(map, 'precipitation-accumulation', geojson);
}
```

Replace with temporal animation using the same pattern as Ch3:
```javascript
let ch4Initialized = false;
let precipFrameData = null;

export async function enterChapter4() {
  if (!map) return;
  if (ch3Initialized) leaveChapter3();

  // Load the 77-frame precip data (currently never loaded!)
  precipFrameData = await loadPrecipFrames();

  setFrames(precipFrameData);
  onFrame((frame, idx) => {
    if (!map) return;
    const geojson = pointsToGeoJSON(frame.points, 'value');
    updateSourceData(map, 'precipitation-accumulation', geojson);
    updateDateLabel(frame.date);  // Reuse the Ch3 date label mechanism
  });

  // Render first frame
  const first = precipFrameData[0];
  if (first) {
    updateSourceData(map, 'precipitation-accumulation', pointsToGeoJSON(first.points, 'value'));
    updateDateLabel(first.date);
  }

  onChapterProgress('chapter-4', (progress) => {
    setProgress(progress);
  });

  ch4Initialized = true;
}

export function leaveChapter4() {
  offChapterProgress('chapter-4');
  resetPlayer();
  updateDateLabel('');
  ch4Initialized = false;
}
```

**Also add to `data-loader.js` import:** `loadPrecipFrames` is already exported from data-loader.js — just add the import in chapter-wiring.js:
```javascript
import { loadSoilMoistureFrames, loadPrecipStormTotals, loadPrecipFrames, loadDischargeTimeseries, loadPreconditionFrames } from './data-loader.js';
```

### Change 4: Date label for Ch4 (and later Ch8)

The current `updateDateLabel()` targets `#ch3-date-label`. For Ch4 and Ch8, we need a shared approach. Options:

**Option A (simplest):** Create a single floating date label element that appears for any temporal chapter. Position it in the map overlay area (not inside a specific chapter card). Update it from any chapter's temporal callback.

**Option B:** Each temporal chapter gets its own date label element in its HTML section. `updateDateLabel` takes a target element ID.

Recommend Option A — add a `<div id="temporal-date-label">` to `index.html` positioned absolutely over the map, styled with the glassmorphism look. Show/hide it based on whether a temporal chapter is active.

```html
<!-- Add near the progress bar in index.html -->
<div id="temporal-date-label" class="temporal-label"></div>
```

```css
.temporal-label {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(9, 20, 26, 0.6);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 6px 16px;
  color: #ffffff;
  font-family: Inter, system-ui, sans-serif;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.5px;
  z-index: 10;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}
.temporal-label.visible {
  opacity: 1;
}
```

Update `updateDateLabel()` in chapter-wiring.js to use this shared element instead of `#ch3-date-label`. Show it on enter, hide it on leave.

### Change 5: Discharge markers larger + river labels (Ch5)

The discharge circle markers are reasonable but too small at zoom 8. Increase the radii:

**File: `src/layer-manager.js`** — Update `glofas-discharge` paint:
```javascript
'circle-radius': [
  'interpolate', ['linear'], ['get', 'discharge_ratio'],
  1, 10,    // was 6
  5, 22,    // was 14
  10, 34,   // was 22
],
```

**Add river labels:** This is a stretch goal for this phase. If time permits, add a `symbol` layer that labels the 3 key rivers (Tejo, Mondego, Sado) using the discharge station points:

```javascript
'river-labels': {
  type: 'symbol',
  source: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
  layout: {
    'text-field': ['get', 'basin'],
    'text-size': 14,
    'text-font': ['Open Sans Regular'],
    'text-offset': [0, 1.5],
    'text-anchor': 'top',
  },
  paint: {
    'text-color': '#ffffff',
    'text-opacity': 0,
    'text-halo-color': 'rgba(10, 33, 46, 0.8)',
    'text-halo-width': 1.5,
  },
},
```

Wire it in `enterChapter5()` — populate with the same station data as `glofas-discharge`, but this layer shows text labels. Add to Ch5's layer list in story-config.js.

### Change 6: Wire main.js for Ch4 leave

**File: `src/main.js`** — Add Ch4 leave cleanup (same pattern as Ch3):

```javascript
// In onChapterEnter():
if (previousChapterId === 'chapter-3' && chapterId !== 'chapter-3') {
  leaveChapter3();
}
if (previousChapterId === 'chapter-4' && chapterId !== 'chapter-4') {
  leaveChapter4();
}
```

Import `leaveChapter4` from chapter-wiring.js.

## File Ownership

| File | Changes |
|------|---------|
| `src/layer-manager.js` | Heatmap layer defs for soil-moisture-animation, soil-moisture-snapshot, precipitation-accumulation. Add `heatmap` to getOpacityProperty. Larger discharge circles. Optional river-labels layer. |
| `src/chapter-wiring.js` | Re-normalize soil moisture values. New enterChapter4/leaveChapter4 with temporal animation. Shared updateDateLabel. Import loadPrecipFrames. |
| `src/main.js` | Add leaveChapter4 import and cleanup. |
| `index.html` | Add `<div id="temporal-date-label">` element. |
| `style.css` | Add `.temporal-label` styles. |
| `src/story-config.js` | Update Ch3/Ch4 layer type references if needed. Optional: add river-labels to Ch5. |

## What NOT to Do

- Do NOT touch PMTiles/flood extent layers (Phase 1 — done)
- Do NOT fix Ch7/Ch8 narrative alignment yet (Phase 3) — but DO leave the temporal player architecture ready for Ch8
- Do NOT fix exploration mode (Phase 3)
- Do NOT add inline sparkline charts for discharge (future polish)
- Do NOT add new npm dependencies or build tools

## Verification Checklist

After completing changes, start the dev server and scroll through:

- [ ] **Ch3 (Soil Moisture):** Continuous heatmap surface covering Portugal, NOT individual dots. Dec 1 should show warm/brown tones (dry). Scrolling through should visibly transition to teal/blue (saturated) by late January. The date label updates as you scroll.
- [ ] **Ch4 (Precipitation):** Continuous heatmap with warm ramp (yellow→orange→red). Scroll-driven animation shows storms hitting — quiet days (low precip, mostly transparent), storm days (bright red zones). The triple-storm rhythm (Kristin ~Jan 29, Leonardo ~Feb 6, Marta ~Feb 11) should be **visually unmistakable** — three separate pulses of red. Date label updates.
- [ ] **Ch5 (Discharge):** Larger visible markers. Station names/basins readable either via labels or on hover. The Tejo/Mondego/Sado should be identifiable.
- [ ] **Ch3→Ch4 transition:** Temporal player cleanly resets between chapters. No residual soil moisture colors when entering Ch4. No residual precipitation when leaving Ch4.
- [ ] **Date label:** Appears during Ch3 and Ch4, disappears on other chapters. Shows Portuguese-formatted date.
- [ ] **Performance:** Scroll through Ch3 and Ch4 without visible jank. If the 77-frame heatmap animation stutters, reduce to every-other-frame (38 frames) by filtering the data array.
- [ ] **No console errors**

## Heatmap Tuning Notes

MapLibre heatmap layers compute a kernel density surface — `heatmap-density` is NOT a direct mapping of feature values. For a regular grid (which this is — 256 points at ~0.25° spacing), the density surface should be fairly uniform, making `heatmap-weight` the dominant differentiator. But:

- If ALL points look the same color: increase `heatmap-intensity` (try 2.0-3.0) to amplify weight differences
- If the surface has visible "hot spots" at individual points: increase `heatmap-radius` to smooth the surface
- If the surface bleeds outside Portugal: this is expected at edges — the basins-outline layer provides the visual boundary
- If performance suffers: reduce radius at lower zoom levels, or add `maxzoom: 10` to the layer

**The key visual test:** show the page to someone unfamiliar with the data. Ask "what's happening?" If they can see the soil filling up (Ch3) and storms hitting (Ch4) without reading the text, the visualization works.

## Output

After completing:
1. `git add -A && git commit -m "feat: heatmap layers + temporal animation for Ch3/Ch4, larger discharge markers"`
2. Report: which heatmap-intensity / radius values you settled on after tuning
3. Note whether the triple-storm rhythm is visible in Ch4 animation
4. List any remaining issues (but don't fix — document for Phase 3)
