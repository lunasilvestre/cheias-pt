# P2.B4: Session 7 — The Storms (Ch.4)

**Model:** Opus
**Branch:** `v2/phase-2` (continue)
**Estimated:** 4-6 hours. Split into 7a (Kristin+respite) and 7b (Leonardo+Marta)
if context gets heavy. Commit after each half.

**Read first:**
1. `CLAUDE.md`
2. `prompts/P2-architecture-fix.md` — **the GSAP timeline pattern is MANDATORY**
3. `prompts/scroll-timeline-symbology.md` §2 Ch.4a-4d (narrative sequence, NOT scroll breakpoints)
4. `data/basemap/IMPACT-GAUGE.md` (visual calibration targets for synoptic composite)
5. `src/weather-layers.ts` (WeatherLayers GL wrappers from P2.A2)
6. `src/temporal-player.ts` (TemporalPlayer from P2.A3)
7. `src/scroll-engine.ts` (current state — Ch.0-3 wired, Ch.2 uses GSAP timeline pattern)

---

## Step 0: Data Validation (run BEFORE any code)

```bash
source .venv/bin/activate

# MSLP COGs — hourly, values in Pascals
python3 -c "
import rasterio, glob
for storm, pattern in [('Kristin', '2026-01-2[6789]'), ('Kristin', '2026-01-30'), ('Leonardo', '2026-02-0[45678]'), ('Marta', '2026-02-09'), ('Marta', '2026-02-1[012]')]:
    files = sorted(glob.glob(f'data/cog/mslp/{pattern}*.tif'))
    if files:
        print(f'{storm} ({pattern}): {len(files)} files')
with rasterio.open('data/cog/mslp/2026-01-28T06.tif') as src:
    d = src.read(1)
    import numpy as np
    valid = d[~np.isnan(d)]
    print(f'MSLP bounds: {src.bounds}')
    print(f'MSLP range: {valid.min():.0f} - {valid.max():.0f} Pa')
    print(f'MSLP grid: {src.width}x{src.height}')
"
# EXPECTED: bounds [-60, 36, 5, 60]. Values ~95000-103000 Pa.
# Kristin: ~120 hourly files. Leonardo: ~120. Marta: ~96.
# IF values < 1100 → already in hPa. IF bounds tiny → wrong file.

# Wind U/V COGs — same grid as MSLP
python3 -c "
import rasterio
for var in ['wind-u', 'wind-v']:
    with rasterio.open(f'data/cog/{var}/2026-01-28T06.tif') as src:
        d = src.read(1)
        import numpy as np
        valid = d[~np.isnan(d)]
        print(f'{var}: bounds={src.bounds}, range=[{valid.min():.1f}, {valid.max():.1f}] m/s, grid={src.width}x{src.height}')
"
# EXPECTED: same bounds as MSLP. Values roughly -40 to +40 m/s.

# Precipitation PNGs
python3 -c "
import glob
files = sorted(glob.glob('data/raster-frames/precipitation/*.png'))
print(f'Precipitation PNGs: {len(files)} files')
print(f'First: {files[0]}')
print(f'Last: {files[-1]}')
"
# EXPECTED: 78 files, daily Dec 1 → Feb 15.

# Satellite IR COGs
python3 -c "
import rasterio, glob
files = sorted(glob.glob('data/cog/satellite-ir/2026-01-27*.tif')) + sorted(glob.glob('data/cog/satellite-ir/2026-01-28*.tif'))
print(f'Kristin IR: {len(files)} files (expect ~48)')
with rasterio.open(files[0]) as src:
    d = src.read(1)
    import numpy as np
    valid = d[~np.isnan(d)]
    print(f'IR bounds: {src.bounds}, range=[{valid.min():.0f}, {valid.max():.0f}], grid={src.width}x{src.height}')
"
# EXPECTED: 48 hourly for Jan 27-28. Values 0-255 (brightness temperature/DN).

# Frontal boundaries
python3 -c "
import json
with open('data/qgis/frontal-boundaries.geojson') as f:
    gj = json.load(f)
for feat in gj['features']:
    g = feat['geometry']
    p = feat['properties']
    print(f'front_type={p.get(\"front_type\")}: {g[\"type\"]}, {len(g[\"coordinates\"])} vertices')
    print(f'  first={g[\"coordinates\"][0]}, last={g[\"coordinates\"][-1]}')
"
# EXPECTED: LineStrings. 3 cold fronts, 1 warm front. Coordinates over Iberia/Atlantic.
# IF Polygon or coords outside [-30, 30, 10, 55] → wrong data.

# IPMA warnings
python3 -c "
import json
with open('data/qgis/ipma-warnings-timeline.geojson') as f:
    gj = json.load(f)
print(f'{len(gj[\"features\"])} features')
levels = {}
for f in gj['features']:
    lvl = f['properties'].get('warning_level', '?')
    levels[lvl] = levels.get(lvl, 0) + 1
print(f'Warning levels: {levels}')
storms = {}
for f in gj['features']:
    s = f['properties'].get('storm', 'none')
    storms[s] = storms.get(s, 0) + 1
print(f'By storm: {storms}')
print(f'Properties: {list(gj[\"features\"][0][\"properties\"].keys())}')
"
# EXPECTED: 378 features. Levels: yellow, orange, red. Property: warning_level (NOT level).
# Storms: None/Kristin/Leonardo/Marta.

# Discharge timeseries (for respite sparklines)
python3 -c "
import json
with open('data/frontend/discharge-timeseries.json') as f:
    d = json.load(f)
print(f'{len(d[\"stations\"])} stations')
for s in d['stations'][:3]:
    ts = s['timeseries']
    peak = max(ts, key=lambda t: t['discharge_ratio'])
    print(f'{s[\"name\"]} ({s[\"basin\"]}): {len(ts)} days, peak ratio={peak[\"discharge_ratio\"]:.1f}x on {peak[\"date\"]}')
"
# EXPECTED: 5+ stations. Peak ratios 2-12×. Dates in Jan-Feb 2026.
```

**If ANY validation fails or shows unexpected values, STOP and report. Do not render
data you haven't verified.**

---

## Architecture: Scroll Selects Sub-Chapter, GSAP Choreographs Layers

**CRITICAL: Follow the pattern from Ch.2 (see `enterChapter2` in scroll-engine.ts).**

Scroll position ONLY determines which sub-chapter is active. Within each sub-chapter,
a GSAP timeline controls the layer reveal sequence at designed pacing.

```typescript
// Scroll controls WHICH sub-chapter:
let ch4ActiveSub: string | null = null;
let ch4SubTimeline: gsap.core.Timeline | null = null;

function handleChapter4SubChapter(progress: number): void {
  const sub =
    progress < 0.28 ? 'kristin' :   // hysteresis
    progress < 0.38 ? 'respite' :
    progress < 0.68 ? 'leonardo' : 'marta';

  if (sub !== ch4ActiveSub) {
    ch4SubTimeline?.kill();
    cleanupSubChapter(ch4ActiveSub);
    ch4ActiveSub = sub;
    ch4SubTimeline = enterSubChapter(sub); // returns GSAP timeline
  }
}

// WITHIN a sub-chapter, GSAP timeline plays at designed pacing:
function enterKristin(): gsap.core.Timeline {
  const tl = gsap.timeline();
  tl
    .add(() => kristinSynopticPlayer.play())
    .to(state, { isobarOpacity: 1, duration: 1.5 })
    .to(state, { particleOpacity: 1, duration: 1 }, '-=0.5')
    .to(state, { precipOpacity: 0.7, duration: 1.5 }, '+=0.5')
    .to(state, { warningOpacity: 0.8, duration: 1 }, '+=1')
    // ... etc
  return tl;
}
```

**Do NOT write `if (progress >= 0.05) setIsobarOpacity(1)`.** That is the v0 anti-pattern.

---

## Data Facts (from validation above)

| Data | Format | Resolution | Count | Units | Key property |
|------|--------|-----------|-------|-------|-------------|
| MSLP | COG | hourly, 261×97 grid | ~120/storm | Pascals | — |
| Wind U/V | COG | hourly, same grid | ~120/storm | m/s | — |
| Precipitation | PNG | daily | 78 total | pre-rendered blues | — |
| Satellite IR | COG | hourly | 48 (Kristin only) | DN 0-255 | — |
| Frontal boundaries | GeoJSON | — | 4 LineStrings | — | `front_type`: cold/warm |
| IPMA warnings | GeoJSON | daily per district | 378 features | — | `warning_level`: yellow/orange/red |
| Discharge | JSON | daily | 5+ stations | ratio × normal | `discharge_ratio` |

**Note:** MSLP is in Pascals. ContourLayer `interval: 400` = 4 hPa = 400 Pa. Correct.

**Note:** Satellite IR only confirmed for Kristin (Jan 27-28). Check if Leonardo/Marta
IR exists before attempting those sub-chapters:
```bash
ls data/cog/satellite-ir/2026-02-0[45678]*.tif 2>/dev/null | wc -l
ls data/cog/satellite-ir/2026-02-09*.tif data/cog/satellite-ir/2026-02-1[012]*.tif 2>/dev/null | wc -l
```
If zero → skip satellite IR for Leonardo/Marta. Use synoptic-only stack.

---

## Sub-chapter Implementation

### enterChapter4() — master entry

```typescript
export async function enterChapter4(): Promise<void> {
  // 1. Pre-load Kristin data (first sub-chapter starts immediately)
  //    Load MSLP + wind for Jan 26-30, precip PNGs for Jan 26-30
  // 2. Ensure MapLibre layers: precipitation-raster, ipma-warnings, frontal-boundaries
  // 3. Start first sub-chapter: enterKristin()
  // 4. Background: pre-load Leonardo + Marta data
}
```

### 4a: Kristin → enterKristin() GSAP timeline

Camera: `[-10, 40]` z5.5 p25

**Timeline:**
```
0s:    Synoptic temporal player starts — MSLP + wind COGs, Jan 26-30, 8fps, loop
       All 4 WeatherLayers GL layers: particles, isobars (400Pa interval),
       H/L markers, wind barbs. Data updates per temporal frame via updateWeatherFrame().
0s:    MSLP isobars fade in (1.5s)
1s:    Wind particles activate (1s)
2.5s:  Precipitation PNGs fade in underneath (1.5s) — daily crossfade synced to
       temporal player date (round to nearest day)
4s:    IPMA warnings fade in (1s) — filter by date from temporal player,
       property: warning_level, colors: yellow #ffd700, orange #ff8c00
5.5s:  Annotation: "CICLOGENESE EXPLOSIVA" (GSAP text fade)
8s:    Satellite IR crossfade IN (2s) — synoptic layers fade OUT simultaneously
       48 hourly frames at 4fps. Inverted grayscale. REPLACES synoptic, not additive.
       Max 6-7 layers at any time.
14s:   Lightning ScatterplotLayer flashes (yellow #ffd700, 300ms flicker)
18s:   Hold — synoptic returns, satellite fades, storm passing
```

### 4b: Respite → enterRespite() GSAP timeline

Camera: `[-8.5, 39.5]` z7 p20

**Timeline:**
```
0s:    Kill Kristin temporal player. Freeze on Jan 31 00Z — single static MSLP frame.
       Isobars visible but spread (high pressure filling).
0.5s:  Side panel slides in — discharge sparklines (Observable Plot, same pattern as
       Ch.3 sparklines). Show rivers STILL RISING after rain stopped.
       Data: discharge-timeseries.json. Plot: x=date, y=discharge_ratio.
       Red threshold line at ratio=1.0.
2s:    Text: "O pior já passou? Não."
```

### 4c: Leonardo → enterLeonardo() GSAP timeline

Camera: `[-10, 40]` z5.5 p25 → pushes to `[-9, 40]` z7 at ~6s

**Timeline:**
```
0s:    New synoptic temporal player: MSLP + wind, Feb 4-8 hourly, 8fps
0s:    Isobars + particles fade in (1.5s)
2.5s:  Precipitation fades in (1.5s)
4s:    IPMA warnings escalate — orange → RED (filter by date + storm='Leonardo')
6s:    Camera push to [-9, 40] z7 (3s flyTo)
6s:    Frontal boundary: warm front from frontal-boundaries.geojson
       Red line #dc143c, 2px, filter front_type='warm'
9s:    Satellite IR IF available (check file count first). Otherwise hold synoptic.
```

### 4d: Marta → enterMarta() GSAP timeline

Camera: `[-9, 39.5]` z7.5 p30 (tightest)

**Timeline:**
```
0s:    New synoptic temporal player: MSLP + wind, Feb 9-12 hourly, 8fps
0s:    Isobars + particles fade in (1.5s)
2.5s:  Precipitation fades in (1.5s)
4s:    Frontal boundary: cold front, blue #4169e1, filter front_type='cold'
5s:    IPMA warnings: ALL RED
6s:    Wind barbs appear (GridLayer, peak moments only)
8s:    Full composite visible — max 6-7 layers simultaneously:
       precipitation, isobars, H/L, particles, frontal, warnings
       (wind barbs optional — drop first if <30fps)
```

### leaveChapter4() — master cleanup

Kill active sub-chapter timeline. Destroy all temporal players. Clear all deck.gl
layers. Remove IPMA warnings, frontal boundaries. Hide annotations. Reset camera.

---

## IPMA Warning Choropleth

The IPMA data is a timeline GeoJSON — each feature is one district on one date with
a warning level. To render as a choropleth that updates with the temporal player:

```typescript
// On each temporal frame tick:
function updateIPMAWarnings(date: string): void {
  // Filter features where properties.date === date (or nearest)
  // Build district → warning_level lookup
  // Update MapLibre fill-color expression:
  //   match ['get', 'warning_level']
  //   'yellow' → '#ffd700'
  //   'orange' → '#ff8c00'
  //   'red'    → '#dc143c'
  //   '#333333' (default/green)
}
```

Need a district polygon source. Check if IPMA GeoJSON already has geometry:
```bash
python3 -c "
import json
with open('data/qgis/ipma-warnings-timeline.geojson') as f:
    gj = json.load(f)
feat = gj['features'][0]
print(f'Geometry type: {feat[\"geometry\"][\"type\"]}')
print(f'Coords sample: {str(feat[\"geometry\"][\"coordinates\"])[:200]}')
"
```

If features have Polygon geometry → use directly.
If features are Points or have no geometry → need a separate district polygons file.

---

## Performance Budget

Ch.4 is the heaviest chapter. Target: ≥30fps on desktop during composite.

**Layer shedding order if below 30fps:**
1. Wind barbs (GridLayer) — least visual impact
2. Reduce particles 5000 → 3000
3. Fall back to PNG-only precipitation (no live COG crossfade)
4. Reduce isobar update to every 2nd temporal frame

**Monitor:** Open Chrome DevTools → Performance tab during Ch.4 scroll.

---

## Visual Verification (BEFORE committing)

Open browser, scroll to Ch.4.

### Per sub-chapter checklist:

**Kristin:**
- [ ] Isobars show concentric rings around low pressure (bullseye pattern)
- [ ] Particles flow cyclonically (counterclockwise in NH) around the low
- [ ] Precipitation blues visible underneath particles
- [ ] IPMA warnings color districts yellow→orange
- [ ] Satellite IR: bright comma cloud visible when crossfade happens
- [ ] Timeline plays at designed pacing, not instantaneous

**Respite:**
- [ ] Synoptic calms — isobars spread apart
- [ ] Discharge sparklines appear in side panel, show rivers still rising
- [ ] No temporal player running (static frame)

**Leonardo:**
- [ ] New synoptic player starts with new data window
- [ ] IPMA warnings escalate to RED
- [ ] Warm front line visible (red with markers)
- [ ] Camera pushes to closer view of Portugal

**Marta:**
- [ ] Tightest camera view
- [ ] Cold front line visible (blue with markers)
- [ ] Full composite: 6-7 layers simultaneously legible
- [ ] ≥30fps during composite (check DevTools)

**Transitions:**
- [ ] Sub-chapter transitions: no flash, no orphaned layers from previous sub
- [ ] Exit Ch.4 → all storm layers gone, console clean
- [ ] Re-enter Ch.4 → starts fresh from Kristin

**Console:** Zero errors.

**If any checkbox fails, fix it. `npm run build` passing is NOT acceptance.
The browser render is acceptance.**

---

## Commit

Split if needed:
- `P2.B4a: chapter 4 Kristin + respite sub-chapters with synoptic composite`
- `P2.B4b: chapter 4 Leonardo + Marta sub-chapters, full layer stack`

Or single:
- `P2.B4: chapter 4 three storms — 4 sub-chapters with GSAP timeline choreography`
