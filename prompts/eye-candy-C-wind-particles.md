# Prompt C — Wind Particle Streamlines

## Context

You are working on `deckgl-prototype.html` in the `cheias.pt` project — a flood monitoring scrollytelling platform for Portugal. This is a **DevSeed portfolio piece**.

This prompt implements the highest "wow factor" effect: animated wind particle streamlines showing jet stream and cyclonic flow, inspired by Windy.com's particle visualization.

Read `deckgl-prototype.html` first (by this point it should have COG-from-R2 rendering via geotiff.js from previous prompts).
Read `spike-deckgl-raster.html` for the proven `renderCOGToCanvas()` pattern and geotiff.js loading.
Read `data/video-analysis/MOTION-ANALYSIS.md` → Effect 1 (Jet Stream / Wind Particle Visualization) for the full visual spec.

## Data Available

**Wind U/V COGs on R2:**
- `cog/wind-u/YYYY-MM-DDTHH.tif` — 409 files, 6-hourly, ERA5 0.25° resolution
- `cog/wind-v/YYYY-MM-DDTHH.tif` — 409 files, 6-hourly
- R2 base: `https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/`

**Loading pattern (proven in spike + Prompt B):**
The prototype already has `geotiff.js` loaded via `import('https://esm.sh/geotiff@2.1.3')`.
Use `fromUrl()` + `readRasters()` to load U and V components as float arrays:
```js
const tiffU = await GeoTIFF.fromUrl(`${R2_BASE}/wind-u/2026-01-27T12.tif`);
const imgU = await tiffU.getImage();
const [uBand] = await imgU.readRasters({ samples: [0] });
// Same for V. Both are 0.25° grids (~145x25 pixels covering Portugal/Atlantic)
```

**Local fallback for prototyping:**
- `data/qgis/wind-barbs-kristin.geojson` — 6,419 points with `speed_ms`, `direction_deg`, `u_ms`, `v_ms` properties (single timestep, Storm Kristin peak)

## Implementation Strategy

The wind field needs to be loaded as a grid that particles can be advected through. There are two approaches — try Approach A first, fall back to Approach B.

### Approach A: geotiff.js Wind Grid + Custom Particle System (preferred)

1. **Load U/V wind fields as grids** using the existing `geotiff.js` pipeline:
   - Fetch both U and V COGs for the current timestep from R2
   - `readRasters()` gives you float arrays + image dimensions + bounding box
   - Build a `WindField` object: `{ uData, vData, width, height, bbox }` for bilinear interpolation
2. **Particle advection** via `requestAnimationFrame`:
   - Maintain array of 2,000-5,000 particles with `[lon, lat, age, trail[]]`
   - Each frame: interpolate U/V at particle position, advect, append to trail
   - Respawn ~5% of particles per frame at random positions
3. **Render trails** with deck.gl `PathLayer` (see visual spec below)
4. **Bilinear interpolation** for smooth wind lookup:
   ```js
   function sampleWind(lon, lat, field) {
     const fx = (lon - field.bbox[0]) / (field.bbox[2] - field.bbox[0]) * field.width;
     const fy = (field.bbox[3] - lat) / (field.bbox[3] - field.bbox[1]) * field.height;
     // bilinear interpolation from fx,fy into field.uData/vData
   }
   ```

### Approach B: GeoJSON Fallback (if COG loading is too slow for animation)

1. **Load wind grid from GeoJSON:** Use `data/qgis/wind-barbs-kristin.geojson` (6,419 points
   with `u_ms`, `v_ms`) and build a spatial lookup grid via nearest-neighbor bucketing
2. **Particle system:**
   - Maintain an array of 2,000-5,000 particles, each with `[lon, lat, age, trail[]]`
   - Each animation frame:
     a. For each particle, lookup nearest wind vector from the grid (bilinear interpolation)
     b. Advect: `lon += u * dt`, `lat += v * dt` (scale appropriately for degrees)
     c. Append current position to trail (keep last 10-15 positions)
     d. Increment age. If age > maxAge or particle exits bounds, respawn at random position
   - Respawn ~5% of particles per frame at random locations within the map bounds
3. **Render trails** using deck.gl `PathLayer`:
   ```js
   new PathLayer({
     id: 'wind-particles',
     data: particles,
     getPath: d => d.trail,
     getColor: d => {
       const speed = Math.sqrt(d.u*d.u + d.v*d.v);
       // green→yellow→purple ramp
       if (speed > 25) return [180, 0, 255, 200];
       if (speed > 15) return [255, 255, 0, 160];
       return [0, 200, 100, 100];
     },
     getWidth: 1.5,
     widthMinPixels: 1,
     widthMaxPixels: 2,
     opacity: 0.8,
     jointRounded: true,
     capRounded: true,
   });
   ```
4. **Animation loop:** Run `requestAnimationFrame` independently from the timeline. Particles flow continuously. When the timeline date changes, reload the wind field for the new timestep.

## Visual Spec (from MOTION-ANALYSIS)

- **Particle count:** 5,000-20,000 (start with 2,000, let user scale via a slider)
- **Trail length:** 8-15 frames of position history per particle
- **Trail fade:** Exponential opacity decay — head of trail is bright, tail fades to transparent
- **Color ramp:** Wind speed → color:
  - 0-8 m/s: `rgb(0, 200, 100)` green (calm)
  - 8-15 m/s: `rgb(255, 255, 100)` yellow (moderate)
  - 15-25 m/s: `rgb(255, 165, 0)` orange (strong)
  - 25+ m/s: `rgb(180, 0, 255)` purple/magenta (extreme jet stream)
- **Speed encoding:** Faster wind = longer trails + faster particle movement. Creates visible velocity gradient.
- **Particle spawn:** New particles appear at random positions. Despawn when they exit map bounds or reach max age (~100-200 frames).
- **Background:** Particles should be visible against the dark basemap. Semi-transparent, with glow effect if possible (via `globalCompositeOperation: 'lighter'` or additive blending in WebGL).

## UI Elements

1. **Checkbox** "Wind particles" in layer panel (dot color: `#a855f7`)
2. **Particle density slider** (appears when wind particles enabled):
   - Range: 500 to 10,000
   - Default: 2,000
   - Label shows current count
   - Place inside the layers panel, indented below the checkbox
3. **Wind speed legend** — small color bar showing the speed→color mapping, positioned in bottom-left above the titiler badge

## Temporal Integration

- When timeline date changes, find nearest 6-hourly wind timestep (same logic as MSLP)
- Fetch new U/V COGs from R2 via `geotiff.js` (same `fromUrl()` + `readRasters()` pattern used for other rasters)
- Smoothly transition: don't reset all particles — let existing particles continue advecting under the new field. This creates a natural "transition" effect.
- For Approach A: rebuild the `WindField` object from new U/V arrays
- For Approach B: rebuild the spatial lookup grid from GeoJSON

## Constraints

- Single HTML file, all JS inline, CDN-only deps
- MapLibre GL ^4.0 + deck.gl ^9.0
- Must not block the main thread — if CPU particle advection is too heavy, reduce count or use Web Workers
- Frame rate target: 30fps minimum with particles running
- Particle rendering must sync with map pan/zoom (particles stay georeferenced)
- The existing layers, toggles, and timeline must keep working

## Success Criteria

1. Toggle "Wind particles" → particles appear and start flowing across the map
2. Particle trails show clear directional flow (W→E dominant, cyclonic rotation around lows visible)
3. Jet stream core visible as dense band of fast-moving purple/magenta particles
4. Particles respond to map pan/zoom (they're georeferenced, not screen-space)
5. Changing timeline date loads new wind field — particles smoothly transition
6. Performance: 30fps with 2,000 particles, no UI jank
7. Particle density slider works — increasing to 5,000+ still renders (maybe slower)
