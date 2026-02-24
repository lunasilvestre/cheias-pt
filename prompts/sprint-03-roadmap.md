# cheias.pt — Sprint 03 Roadmap

## Strategy: Sequential Phases with Verification Gates

Sprint 02 failed because 4 parallel agents made locally rational choices (circle layers, static snapshots) that were globally wrong. Nobody could see the browser. Nobody enforced the design spec at render time.

Sprint 03 runs **sequential focused phases**. Each phase has a mandatory browser verification step before the next begins. The QA agent isn't a separate team member — it's a gate.

---

## Phase 1: Unblock Rendering ✅ COMPLETE (2026-02-18)
**Prompt:** `prompts/sprint-03-phase1-unblock-rendering.md`
**Agent:** Single agent, no team
**Root cause:** source-layer name mismatch — PMTiles built with `flood-extent` (hyphen), code referenced `flood_extent` (underscore). MapLibre silently renders empty tiles.
**Result:** Ch1, Ch6a-c, Ch7 now show red flood extent polygons. Ch6c camera corrected. Zero console errors.

**Verification gate:** ✅ Red flood polygons visible in Ch1, Ch6a-c, Ch7.

---

## Phase 2: Visual Transformation ← CURRENT
**Prompt:** `prompts/sprint-03-phase2-visual-transformation.md`
**Agent:** Single agent
**Scope:** Replace circle layers with heatmaps, wire temporal animation for all temporal chapters, fix soil moisture normalization

### 2A: Heatmap Conversion (Ch3, Ch4)
- Replace `soil-moisture-animation` circle layer → MapLibre `heatmap` type
- Replace `precipitation-accumulation` circle layer → `heatmap` type
- Fix soil moisture color ramp: diverging warm→cool (brown dry → white neutral → blue saturated)
- Re-normalize soil moisture to actual data range (dataset_min→dataset_max, not sm/0.42)
- Forensic report says Dec 1 values already 0.49+ with current normalization — kills all dynamic range

### 2B: Temporal Wiring (Ch4, Ch8)
- Ch3 temporal animation already works (temporal-player.js proven)
- Wire Ch4: load `precip-frames.json` (currently NEVER LOADED), connect to temporal-player
- Wire Ch8: load `precondition-frames.json` (currently NEVER LOADED), animate Jan 25→Feb 5
- 5 of 10 frontend JSON files are never loaded by any code path — fix this

### 2C: Discharge Improvement (Ch5)
- Make discharge markers dramatically larger (current 6-22px is tiny at zoom 8)
- Add river line geometry (extract from basins.geojson or fetch from OpenStreetMap)
- Defer inline sparkline charts to Phase 3 or a polish sprint

### File ownership
- `src/layer-manager.js` — heatmap layer definitions (LAYER_DEFS changes)
- `src/chapter-wiring.js` — enterChapter4(), enterChapter8() functions, temporal player wiring
- `src/story-config.js` — update layer type references if needed
- `src/temporal-player.js` — no changes expected (proven pattern)

### Verification gate
- Ch3: Continuous heatmap surface (not dots), visible color change as you scroll through Dec→Jan
- Ch4: Continuous heatmap with scroll-driven storm sequence (Kristin→Leonardo→Marta rhythm)
- Ch5: Visible discharge markers, river names identifiable
- Ch8: Precondition index animation showing risk building over time

---

## Phase 3: Narrative Alignment + Polish
**Agent:** Single agent OR 2-agent team (one for narrative logic, one for exploration mode)
**Scope:** Fix the story's intellectual coherence + make exploration mode functional

### 3A: Ch7/Ch8 Narrative Swap
- **Ch7 (Cadeia Causal — retrospective facts):** Remove precondition basin coloring. Show ALL flood extent polygons + ALL 42 consequence markers + basin outlines. This is "look at all the damage."
- **Ch8 (O Que os Dados Já Sabiam — predictive thesis):** Animate precondition index from Jan 25→Feb 5 using precondition-frames.json (wired in Phase 2B). This is "the risk was building — and the data showed it."
- Fix `main.js` lines 67-74: Ch7 currently calls `colorBasinsByPrecondition(map, 'peak')` — should show flood extent + markers instead. Ch8 uses `'pre_storm'` (values too low) — should use Phase 2B's temporal animation.
- Fix `story-config.js` Ch7 legend: currently shows risk classes (Risco crítico/elevado/etc.) which belong in Ch8. Ch7 should show consequence marker types.

### 3B: Exploration Mode (Ch9)
- `src/story-config.js` Ch9 has `layers: []` — means `showChapterLayers` ensures nothing
- Add all toggleable layers to Ch9 config at opacity 0, so they're ensured before explore mode activates
- Fix `exploration-mode.js` line 23: references non-existent `precondition-fill` layer — add it to LAYER_DEFS or remove from toggle map
- Wire geolocation ("Ver a minha zona") — currently logs stub message
- Wire methodology panel — at minimum, link to a methodology section

### 3C: Consequence Marker Filtering
- Currently most chapters show only 2-3 markers due to chapter filtering
- Verify each event's `chapter` property in `data/consequences/events.geojson` is correctly assigned
- Ch6a should show Alcácer/Sado events, Ch6b Coimbra events, Ch6c A1 events
- Ch7 should show ALL 42 markers (already correct: `filterConsequencesByChapter(map, null)`)
- Fix the unexplained green dot in Ch6a (the `rescue` type maps to `#27ae60` green — add it to the legend)

### 3D: Hero Text + Visual Polish
- Add CSS vignette overlay + text-shadow to Ch0 hero (NO glassmorphism card — preserve cinematic feel)
- Replace tsunami emoji favicon with appropriate icon
- Add legend entry for `rescue` type (currently missing from Ch6 legend)

### Verification gate
- Ch7 shows flood extent + all markers (no precondition coloring)
- Ch8 shows precondition risk building over time, with central/southern Portugal reaching elevated/critical
- Ch9 layer toggles work, geolocation works
- Hero text readable against map
- A first-time visitor scrolling through the full story understands the causal chain

---

## Dependencies

```
Phase 1 ──→ Phase 2A ──→ Phase 2B ──→ Phase 3A
                │                        │
                └──→ Phase 2C            └──→ Phase 3B
                                         │
                                         └──→ Phase 3C + 3D
```

Phase 1 unblocks everything. Phase 2A (heatmaps) and 2C (discharge) can run in parallel. Phase 2B (temporal wiring) depends on 2A being correct. Phase 3 depends on Phase 2 being visually verified.

---

## Success Criteria (end of Sprint 03)

After all three phases, a first-time visitor to cheias.pt should:

1. See flood extent in red on the opening chapter (Ch1)
2. Watch soil moisture fill Portugal's soil over weeks (Ch3 temporal animation)
3. Feel three storms hit in sequence (Ch4 temporal animation)
4. See rivers swell (Ch5 markers + lines)
5. Zoom into Alcácer, Coimbra, A1 with flood polygons + consequence data (Ch6)
6. See the full scope of damage (Ch7 synthesis)
7. Understand that the data predicted it (Ch8 precondition animation)
8. Explore their own area (Ch9 functional)

The map drives the narrative. The text provides context. Not the other way around.
