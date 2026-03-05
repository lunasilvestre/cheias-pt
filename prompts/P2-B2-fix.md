# P2.B2-fix: Chapter 2 Atlantic Engine — Fix & Verify

**Priority:** Run BEFORE Session 7.
**Branch:** `v2/phase-2` (continue)
**Read first:** `CLAUDE.md`, `prompts/P2-architecture-fix.md`

---

## Step 0: Data Validation (run BEFORE any rendering code)

```bash
# SST COG
python3 -c "
import rasterio
with rasterio.open('data/cog/sst/2026-01-15.tif') as src:
    print(f'SST bounds: {src.bounds}')
    print(f'SST shape: {src.width}x{src.height}')
    d = src.read(1)
    print(f'SST values: min={d[d != src.nodata].min():.1f}, max={d[d != src.nodata].max():.1f}')
"
# EXPECTED: bounds contain [-40, 25, 5, 60]. Values roughly -3 to +5.
# IF bounds are tiny or values are all 0 → COG is broken. Stop.

# Storm tracks GeoJSON
python3 -c "
import json
with open('data/qgis/storm-tracks-auto.geojson') as f:
    gj = json.load(f)
for feat in gj['features']:
    g = feat['geometry']
    n = feat['properties'].get('name', '?')
    c = g['coordinates']
    print(f'{n}: {g["type"]}, {len(c)} vertices, first={c[0]}, last={c[-1]}')
"
# EXPECTED: 3 features, all LineString, 20+ vertices each.
# First vertex ~[-30, 45], last ~[-8, 42]. Atlantic → Iberia.
# IF MultiPolygon or <10 vertices → data extraction failed. Stop.

# IVT COGs
python3 -c "
import rasterio, glob
files = sorted(glob.glob('data/cog/ivt/*.tif'))
print(f'IVT COGs: {len(files)} files')
with rasterio.open(files[0]) as src:
    print(f'IVT bounds: {src.bounds}')
    d = src.read(1)
    print(f'IVT values: min={d[d != src.nodata].min():.1f}, max={d[d != src.nodata].max():.1f}')
"
# EXPECTED: 50+ files. Bounds same as SST. Values 0-800 kg/m/s.
# IF max < 50 → wrong variable or wrong units. Stop.

# Wind COGs
python3 -c "
import rasterio
for var in ['wind-u', 'wind-v']:
    with rasterio.open(f'data/cog/{var}/2026-01-28T12.tif') as src:
        d = src.read(1)
        print(f'{var}: bounds={src.bounds}, range=[{d[d != src.nodata].min():.1f}, {d[d != src.nodata].max():.1f}]')
"
# EXPECTED: bounds cover Atlantic+Iberia. Values roughly -30 to +30 m/s.
```

**If ANY validation fails, fix the data before touching rendering code.**

---

## Problems to Fix

### 1. SST — static frame is visually incoherent

Current: single 2026-01-15 COG. IVT animates 77 days while SST sits frozen.

**Fix:** Either:
- **(A) Temporal SST** — load 10-15 SST COGs at weekly intervals (Dec 1, Dec 8, ..., Feb 15).
  TemporalPlayer autoplay at 0.5fps underneath IVT. Subtle but alive.
- **(B) Meaningful static** — if SST COGs are too large, use a single frame BUT verify
  it renders as recognizable ocean temperature. Blue = cold, red = warm, centered on
  Atlantic. If it renders as a blank rectangle or wrong extent, the COG is broken.

**Pick (A) if** the COG files exist at `data/cog/sst/`. List them first:
```bash
ls data/cog/sst/*.tif | head -20
```

**Pick (B) only if** fewer than 5 SST COGs exist.

**Visual verification:** Open `http://localhost:5173`. Scroll to Ch.2. Screenshot the SST
layer. It MUST show blue-white-red ocean temperature gradients across the North Atlantic.
If it shows: nothing, a tiny rectangle, all one color, or land instead of ocean — the
COG bounds or colormap are wrong. Fix before proceeding.

### 2. Storm tracks — PathLayer rendering garbage

Current: massive shapes that don't look like cyclone tracks.

**Debug steps:**
```bash
# 1. Check the actual geometry type
python3 -c "
import json
with open('data/qgis/storm-tracks-auto.geojson') as f:
    gj = json.load(f)
for feat in gj['features']:
    geom = feat['geometry']
    name = feat['properties'].get('name', '?')
    coords = geom['coordinates']
    print(f'{name}: {geom[\"type\"]}, {len(coords)} vertices, first={coords[0]}, last={coords[-1]}')
"
```

Expected: 3 LineStrings (Kristin, Leonardo, Marta), each with 20-100 vertices tracing
a path from mid-Atlantic toward Iberia.

If the geometry is wrong (MultiPolygon, FeatureCollection of Points, etc.), the
extraction script from P1.B1 produced the wrong output. Fix the GeoJSON first.

**Rendering:** Use MapLibre line layer (already registered in layer-manager.ts as
`storm-tracks`). Verify:
- Kristin: red (#ff6464), track curves from ~[-30, 45] toward [-8, 42]
- Leonardo: blue (#64b5f6), similar Atlantic→Iberia path
- Marta: gold (#ffc864), similar path

**Visual verification:** Storm tracks must look like 3 curved lines across the Atlantic,
not filled polygons or scattered points. Each line should have visible curvature showing
the cyclone's real wandering path.

### 3. GSAP timeline — verify sequence plays

Session 6.5 refactored to timeline. Verify it actually works:

1. Open dev server. Scroll to Ch.1 (ensure Ch.2 is NOT entered yet).
2. Scroll into Ch.2. Watch for this sequence:
   - 0-2s: SST fades in (blue-white-red ocean field appears)
   - 2-3s: Storm track lines appear (3 colored lines across Atlantic)
   - 3-5s: Globe rotates slightly
   - 5-6s: IVT player starts (purple/white band animates), date label appears
   - 6-7s: Wind particles activate (white flowing trails)
   - 9-13s: Camera pushes toward Portugal
3. Scroll past Ch.2 into Ch.3. Verify: all Ch.2 layers gone, no orphaned particles,
   no console errors.

If the sequence doesn't play (layers appear all at once, or nothing appears), the
GSAP timeline wiring is broken. Check `enterChapter2Timeline()` in scroll-engine.ts.

### 4. Globe projection

Ch.2 should render on a globe. Verify:
- The map shows curved Earth, not flat mercator
- SST wraps around the globe surface
- Storm tracks curve naturally on the sphere
- On exit to Ch.3: smooth globe→mercator transition (~1s)

If globe isn't working, check `setProjection('globe')` is called in the chapter enter.

---

## Implementation Order

1. Debug storm tracks GeoJSON (5 min) — confirm geometry type and coordinates
2. Fix storm track rendering if needed (15 min)
3. Verify/fix SST rendering (15 min) — confirm it shows ocean temperature
4. Verify GSAP timeline plays correctly (15 min)
5. Verify globe projection (5 min)
6. Take screenshot of Ch.2 at full reveal (all layers visible) — save to
   `data/screenshots/ch2-atlantic-verify.png`

## Visual Verification Checklist

Before committing, confirm ALL of these by looking at the browser:

- [ ] SST: blue-white-red ocean temperature gradient visible on globe
- [ ] Storm tracks: 3 colored curved lines across Atlantic (NOT filled shapes)
- [ ] IVT: purple/white band animates across Atlantic (temporal player cycling)
- [ ] Particles: white trails flowing along atmospheric river corridor
- [ ] Globe: curved Earth visible, not flat mercator
- [ ] Timeline: layers appear in designed sequence, not all at once
- [ ] Exit: scrolling to Ch.3 cleans up all Ch.2 layers, globe→mercator transition
- [ ] Console: zero errors

**If any checkbox fails, fix it before committing. `npm run build` passing is necessary
but NOT sufficient. The render must visually match the spec.**

## Commit

`P2.B2-fix: chapter 2 visual verification — SST, storm tracks, timeline sequence`

---

## Propagation Note for Future Sessions

Every subsequent session prompt (7, 8, 9, 10) must include this rule:

> **Before committing any chapter:** Open the browser, scroll to the chapter, visually
> verify each layer renders correctly. If a layer shows nothing, shows wrong colors,
> shows wrong geometry, or appears at wrong timing — fix it. `npm run build` is not
> acceptance. The browser render is acceptance.
