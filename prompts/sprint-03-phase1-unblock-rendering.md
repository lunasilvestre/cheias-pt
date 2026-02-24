# cheias.pt — Sprint 03, Phase 1: Unblock Rendering

## Mission

Fix the two issues that cascade across the most chapters: PMTiles flood extent not rendering (affects Ch1, Ch6a-c, Ch7, Ch9) and Ch6c camera pointing 15km from the actual event. This is surgical — two changes, massive impact.

**This is a single-agent task. No team needed.**

Read `CLAUDE.md` first for project context. Do NOT refactor, restructure, or "improve" anything beyond the scope below.

## Context: What Failed and Why

The Sprint 02 forensic audit (see `FORENSIC-REPORT.md`) identified that the data pipeline is 100% complete but the rendering has a critical last-mile failure. The PMTiles flood extent layer — which is the visual anchor of the entire narrative — is invisible in every chapter that uses it.

**Root cause (from forensic report):** The `sentinel1-flood-extent` layer in `src/layer-manager.js` uses a PMTiles source URL `'pmtiles://data/flood-extent/combined.pmtiles'`. This is a **relative URL**. If the dev server's base path doesn't resolve it correctly, the PMTiles range requests return 404. MapLibre **silently fails** on tile load errors — no console error, just empty tiles.

The PMTiles protocol IS registered correctly in `src/map-controller.js` (line 20-21). The PMTiles library IS loaded via CDN in `index.html`. The tippecanoe conversion used `-l flood_extent` as the layer name, which matches the `'source-layer': 'flood_extent'` in the layer definition.

## Fix 1: PMTiles Flood Extent (Critical)

### Diagnosis Steps (do these FIRST, before changing any code)

1. Start the dev server: `npx serve -l 3000 -s --no-clipboard` from the project root
2. Open `http://localhost:3000` in the browser
3. Open DevTools → Network tab → filter for `pmtiles`
4. Scroll to Chapter 1 (the chapter that should show red flood extent)
5. Check: are there range requests to `combined.pmtiles`? Do they return 200 or 404?
6. Also check the browser console for any MapLibre errors about sources or layers

### What to Check in Code

**File: `src/layer-manager.js`, lines 103-114:**
```javascript
'sentinel1-flood-extent': {
    type: 'fill',
    source: { type: 'vector', url: 'pmtiles://data/flood-extent/combined.pmtiles' },
    'source-layer': 'flood_extent',
    paint: { 'fill-color': '#e74c3c', 'fill-opacity': 0 },
},
'flood-extent-polygons': {
    type: 'fill',
    sourceRef: 'sentinel1-flood-extent',
    'source-layer': 'flood_extent',
    paint: { 'fill-color': '#e74c3c', 'fill-opacity': 0 },
},
```

The `sourceRef` pattern means `flood-extent-polygons` reuses the source from `sentinel1-flood-extent`. If the parent source fails, both layers are invisible.

### Likely Fixes (in order of probability)

**A. Relative URL resolution:** The `serve` package serves from the project root, so `data/flood-extent/combined.pmtiles` should resolve. But try an absolute path from root: `pmtiles:///data/flood-extent/combined.pmtiles` or `pmtiles://./data/flood-extent/combined.pmtiles`. If the dev server doesn't map `/data/` to the filesystem `data/` directory, that's the issue.

**B. PMTiles protocol registration timing:** The protocol must be registered BEFORE any source using it is added to the map. In `src/map-controller.js`, the registration happens in `initMap()` before the map constructor — which is correct. But verify that `ensureLayer()` isn't called before `map.on('load')` completes. The `main.js` wires layers inside `map.on('load')`, which should be safe.

**C. Source-layer name mismatch:** The PMTiles was built with `-l flood_extent`. The layer definition uses `'source-layer': 'flood_extent'`. These should match. But verify by inspecting the PMTiles metadata:
```bash
# If pmtiles CLI is available:
pmtiles show data/flood-extent/combined.pmtiles

# Or use Python:
source .venv/bin/activate
python3 -c "
import struct, json
with open('data/flood-extent/combined.pmtiles', 'rb') as f:
    f.seek(0)
    header = f.read(127)
    # Read metadata offset and length from header
    metadata_offset = struct.unpack('<Q', header[7:15])[0]
    metadata_length = struct.unpack('<Q', header[15:23])[0]
    if metadata_offset > 0 and metadata_length > 0:
        f.seek(metadata_offset)
        import gzip
        raw = f.read(metadata_length)
        try:
            data = gzip.decompress(raw)
            meta = json.loads(data)
            print(json.dumps(meta, indent=2))
        except:
            print('Could not decompress metadata')
"
```

Look for `vector_layers` in the metadata — it should list `flood_extent` as a layer name. If it's something else (e.g., `combined` or `default`), update the `'source-layer'` in `layer-manager.js` to match.

**D. File size / CORS:** The `combined.pmtiles` is ~17MB. `serve` should handle range requests correctly, but verify the `Content-Range` and `Accept-Ranges` headers in the network response. If range requests aren't supported, PMTiles won't work.

### Verification Criteria

After fixing, scroll through the story and confirm:

- [ ] **Ch1:** Red flood extent polygons visible over the Tejo valley at zoom 6.5. The "red is water where there used to be land" is actually visible.
- [ ] **Ch6a (Alcácer do Sal):** Flood polygons visible at zoom 12 around the Sado river
- [ ] **Ch6b (Coimbra):** Flood polygons visible at zoom 11 around the Mondego
- [ ] **Ch6c (A1):** Flood polygons visible at zoom 13 (after the camera fix below)
- [ ] **Ch7:** Flood polygons visible at opacity 0.5 in the national synthesis view
- [ ] **No console errors** related to PMTiles, sources, or layers

## Fix 2: Ch6c Camera Coordinates (Trivial)

**File: `src/story-config.js`**

Find the `chapter-6c` substep (inside the `chapter-6` substeps array) and change:

```javascript
// WRONG — Vila Nova de Ancos/Soure area, ~15km SW of collapse
camera: { center: [-8.63, 40.10], zoom: 13, pitch: 45, bearing: 5 },

// CORRECT — A1 collapse at km 191
camera: { center: [-8.487, 40.217], zoom: 13, pitch: 45, bearing: 5 },
```

The actual A1 motorway collapse (consequence event evt-017) is at `[-8.487, 40.217]`. The current camera points to an area ~15km southwest with no relevant infrastructure.

### Verification

- [ ] Scroll to Ch6c — camera should center on the A1 motorway area near Condeixa-a-Nova/km 191, not on rural Soure area

## What NOT to Do

- Do NOT touch soil moisture, precipitation, or discharge layers (those are Phase 2)
- Do NOT change the heatmap vs. circle layer type (Phase 2)
- Do NOT fix Ch7/Ch8 narrative alignment (Phase 3)
- Do NOT fix exploration mode (Phase 3)
- Do NOT refactor layer-manager.js architecture
- Do NOT add new dependencies or libraries
- Do NOT update any text content

## Output

After completing both fixes:
1. `git add -A && git commit -m "fix: PMTiles flood extent rendering + Ch6c camera coordinates"`
2. Report what the diagnosis revealed (was it URL resolution? source-layer name? timing?)
3. List which chapters now show flood polygons
4. Note any remaining issues you spotted during verification (but don't fix them — just document)
