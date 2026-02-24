# cheias.pt — QA Aesthetic Issues

Tracking visual/UX issues identified during review.
Date: 2026-02-17

---

## Issue #1: Hero text illegible on first viewport

**Chapter:** `chapter-0` (Title Screen)
**Severity:** High — first impression
**Screenshot:** `qa-initial-load.png`

**Problem:**
- Title "O Inverno Que Partiu os Rios" has poor contrast against the map basemap
- Subtitle and byline text are nearly invisible — map labels (country names) compete directly
- No background scrim, vignette, or text-shadow to separate text from map
- The `chapter--hero` has no `.chapter__card` wrapper (unlike all other chapters), so there's no glassmorphism panel behind it

**Possible fixes (to discuss):**
1. Add a radial/linear gradient vignette overlay on the map during chapter-0 (CSS or map `fog`)
2. Add `text-shadow` to hero text elements for minimum legibility
3. Wrap hero content in a `.chapter__card` (but may look too boxy for a hero)
4. Dim/darken the basemap style during the hero chapter (reduce label opacity, darken fill)
5. Combine: subtle vignette + text-shadow for cinematic feel without a card

---

---

## Issue #2: Chapter 1 — No flood data visible

**Chapter:** `chapter-1` (The Hook — 7 de Fevereiro de 2026)
**Severity:** Critical — this is the story's opening punch
**Screenshot:** uploaded image

**Problem:**
- The card text says "O vermelho é água onde antes havia terra" but there is NO red flood extent on the map
- Map shows only the dark basemap with administrative boundaries — no satellite imagery, no CEMS flood polygons
- The floating legend (bottom-right) shows "Área inundada" but the layer isn't rendering
- Could be: data not loading, layer not toggled on for this chapter, PMTiles path wrong, or layer-manager not wiring chapter-1 to the flood-extent source

**Expected:**
- CEMS flood polygons (EMSR864) rendered in red over the Tejo valley / Ribatejo area
- Ideally a Sentinel-1 derived visual or at minimum the vector flood extent

**Investigation needed:**
- Check `story-config.js` for chapter-1 layer definitions
- Check `layer-manager.js` for flood-extent source/layer setup
- Check browser console for data loading errors (PMTiles, GeoJSON)
- Verify the data file exists in `data/` directory

---

## Issue #3: Chapter 2 — No atmospheric/SST data on map

**Chapter:** `chapter-2` (A Energia do Atlântico)
**Severity:** Medium — narrative still works via text, but map is wasted
**Screenshot:** uploaded image

**Problem:**
- Map zooms out to show the full Atlantic but displays nothing beyond the dark basemap
- No SST anomaly layer, no storm tracks, no atmospheric river visualization
- The card itself contains a dev placeholder: "Visualização de dados atmosféricos em desenvolvimento"
- The moisture arrow SVG (Atlântico → Portugal) is nice but the map does zero work

**Expected (ideal vs MVP):**
- **Ideal:** SST anomaly raster or IVT (integrated vapor transport) showing the atmospheric river
- **MVP:** At minimum, storm track lines (Harry → Kristin → Leonardo → Marta) as simple GeoJSON polylines with labels, or animated markers showing storm progression
- Even simple named-storm markers at landfall points would give the map purpose

**Note:** This may be intentionally deferred (the dev note suggests so), but it's worth flagging since the wide Atlantic zoom with an empty map feels anticlimactic after the chapter-1 close-up

---

## Issue #4: Chapter 3 — Soil moisture is static dots, not a temporal heatmap

**Chapter:** `chapter-3` (O Solo Encharca)
**Severity:** High — this chapter's entire purpose is showing temporal evolution
**Screenshot:** uploaded image

**Problem:**
- Soil moisture rendered as a uniform grid of blue circles — looks like a dot matrix, not data
- All dots appear the same size/color, no visual gradient from dry→saturated
- Date label shows "1 de Dezembro 2025" suggesting temporal animation exists, but the visual doesn't communicate change — user can't see the soil filling up
- The legend says "Solo seco" (white) vs "Solo saturado" (blue) but all dots look blue — no contrast
- We processed ~2 months of soil moisture data (Dec 2025 → Feb 2026) specifically to show the saturation building week by week. That temporal story is completely lost here.

**Expected:**
- A continuous heatmap/raster (interpolated grid or filled contours) showing soil moisture percentage across Portugal
- Temporal animation as user scrolls: early December (patchy, some dry) → January (widespread saturation) → pre-Kristin (wall of blue)
- Color ramp from white/light → dark blue that makes the "sponge filling" metaphor visceral
- The scroll-driven date progression should make the viewer feel the inevitability

**Root cause (likely):**
- Data rendered as point features (Open-Meteo grid points) rather than interpolated to a raster/heatmap
- Need either: (a) pre-processed raster tiles per timestep, or (b) MapLibre `heatmap` layer type using the grid points with `soil_moisture` as weight, or (c) `circle` layer with proper radius interpolation + color ramp based on moisture value

---

## Issue #5: Chapter 4 — Precipitation is static dot grid, needs animated heatmap

**Chapter:** `chapter-4` (Três Tempestades em Duas Semanas)
**Severity:** High — same fundamental problem as Issue #4
**Screenshot:** uploaded image

**Problem:**
- Precipitation shown as colored circles (red >250mm, orange 100-250mm, etc.) on a point grid
- Requires geospatial literacy to interpret — a citizen won't read a scattered dot matrix
- Static snapshot: the text describes THREE storms arriving in sequence (Kristin 29 Jan, Leonardo 6 Feb, Marta days later) but the map shows a single frozen moment
- No temporal animation — the "three storms in two weeks" narrative is completely lost visually
- Legend is decent (threshold-based classes) but wasted on dots instead of filled areas

**Expected:**
- Animated heatmap/raster looping through the storm sequence with timestamps
- Each storm should visually "hit" Portugal in succession so the reader feels the compound effect
- Ideally: a looping animation (or scroll-driven) showing daily/multi-day precipitation totals from ~25 Jan through ~12 Feb
- The triple-punch rhythm (Kristin → Leonardo → Marta) should be unmistakable

**Applies also to Issue #4 (Chapter 3):**
- Both chapters suffer from the same root cause: raw grid points rendered as circles instead of interpolated continuous surfaces
- Both need temporal animation (scroll-driven or auto-looping) to tell their story
- Consider a shared approach: MapLibre `heatmap` layer with timestep filtering, or pre-rendered raster frames switched on scroll position

---

## Issue #6: Chapter 5 — Rivers invisible, no hydrographs, polygon obscures data

**Chapter:** `chapter-5` (Os Rios Respondem)
**Severity:** High — the climax of the causal chain is flat
**Screenshot:** uploaded image

**Problem:**
- Discharge points are almost all light blue ("caudal normal") — the legend has red/orange/blue but the data shows no drama
- A semi-transparent polygon overlay darkens the map further, hiding even the little information the dots provide
- The three rivers named in the text (Tejo, Mondego, Sado) are NOT visually identified on the map — no river lines, no labels, no highlighting
- No hydrograph charts anywhere — the notebooks generated discharge time-series showing the spike but none are embedded in the narrative
- This chapter should be the payoff of chapters 3+4 (saturated soil + storms = river surge) but it feels like a regression in information density

**Expected:**
- River polylines for Tejo, Mondego, Sado highlighted and labeled on the map
- Embedded sparkline/hydrograph charts showing discharge over time — the spike above historical norms is the story
- Either inline in the card (small sparklines per river) or as an overlay panel
- The notebooks already produced these charts — they should be the primary visual, with the map providing spatial context rather than carrying the information alone
- Remove or reduce the dampening polygon overlay

**Broader pattern (Issues #4, #5, #6):**
- The narrative over-relies on geographic dot grids for data that is better told through charts + map context
- Soil moisture, precipitation, and discharge are all TIME-SERIES stories forced into static spatial displays
- The scrollytelling should blend: map for "where" + embedded charts for "how much / how fast"
- The notebook outputs (hydrographs, soil moisture curves, precipitation accumulation plots) exist but aren't wired into the frontend

---

## Issue #6: Chapter 5 — Rivers invisible, charts from notebooks unused

**Chapter:** `chapter-5` (Os Rios Respondem)
**Severity:** High — rivers are the subject and you can't see them
**Screenshot:** uploaded image

**Problem:**
- River lines are not drawn — the text names Tejo, Mondego, Sado but the map doesn't identify any of them
- Same dot-grid pattern (discharge points) as chapters 3-4, now almost invisible because a dark polygon overlay dampens everything
- Legend shows three classes (Caudal excepcional / elevado / normal) but the dots are tiny, uniform light-blue, and the overlay kills what little contrast existed
- The text makes dramatic claims ("nível mais alto em quase 30 anos", "valores de 1989") but there is ZERO quantitative visual evidence on screen
- **Notebooks already generated discharge hydrographs** (time-series charts showing the spike for Tejo, Sado, Mondego) but none are used in the narrative

**Expected:**
- River polylines drawn and labeled (Tejo, Mondego, Sado at minimum) — the reader needs to see WHICH rivers
- Discharge gauge stations as clickable markers at key locations (Santarém/Tejo, Coimbra/Mondego, Alcácer/Sado)
- **Inline sparkline or hydrograph charts** embedded in the card or as floating overlays showing the discharge spike over time
- The charts already exist in the notebooks — they just need to be rendered (as SVG in-card, or as small Chart.js/D3 elements)
- Remove the dampening polygon overlay or make it much more transparent

**Broader pattern (Issues #4, #5, #6):**
- Three consecutive chapters all default to the same uninformative dot-grid visualization
- The notebooks did the hard analytical work (temporal soil moisture, precipitation accumulation, discharge hydrographs) and produced charts, but none of that made it into the frontend
- The scrollytelling is currently text-driven with decorative maps, when it should be data-driven with supporting text
- **Action:** Audit notebook outputs, identify chart assets, and integrate them as inline SVGs or rendered chart components in the chapter cards

---

## Issue #7: Chapter 6a — Unexplained green dot, missing flood extent, empty impact

**Chapter:** `chapter-6a` (Alcácer do Sal) and likely `chapter-6b`, `chapter-6c`
**Severity:** High — "The Human Cost" section should be the emotional peak
**Screenshot:** uploaded image (browser)

**Problem:**
- **Green dot has no legend entry** — legend shows Mortes (red), Evacuações (orange), Infraestrutura (purple), Deslizamentos (tan) but green is unexplained. Data viz cardinal sin.
- Only 2 consequence markers (1 green, 1 orange) on screen despite text describing a 2-metre flood and worst calamity in 30 years
- **No CEMS flood extent polygons visible** — the Sado river channel is drawn but the flooded area is NOT shown, despite the card citing EMSR861/EMSR864 as data sources
- The river itself is barely distinguishable from the dark basemap — you have to squint to see it
- No supporting media: no satellite comparison, no photos, no area statistics, no damage counts
- The zoom level is right (tight on Alcácer) but the map content is almost empty

**Expected:**
- CEMS flood polygons rendered in red/semi-transparent over the Sado floodplain — this is the Salvaterra de Magos-scale data we already processed
- All consequence markers for the Alcácer area from the 42 geocoded events, not just 2
- Fix the green dot: either add it to the legend or reclassify it to an existing category
- Consider inline before/after or a flood area statistic ("X km² submerged")
- The river should be visually prominent — slightly lighter or blue-tinted to stand out from the basemap

**Applies to all 6x chapters:**
- Chapter 6a (Alcácer), 6b (Coimbra), 6c (Autoestrada) are the human cost triptych
- Each should zoom tight to the location, show flood extent, and have localized impact data
- The 42 geocoded disaster events we processed should be surfaced here

---

## Issue #8: Chapter 6b — Coimbra: same empty map, dike breach invisible

**Chapter:** `chapter-6b` (Coimbra)
**Severity:** High — dike breach + 3,000 evacuations = should be visually devastating
**Screenshot:** uploaded image

**Problem:**
- Identical to Issue #7: dramatic text ("dique cedeu em Casais", "3.000 pessoas evacuadas") over a near-empty dark map
- Only 2 markers visible: 1 red (Mortes) near Montemor-o-Velho, 1 purple (Infraestrutura) near Coimbra
- The Mondego river is invisible — you cannot even see WHERE the dike broke
- No flood extent polygons despite the Mondego floodplain being extensively mapped by CEMS
- No "Casais" label or marker showing the actual breach location
- "Campos agrícolas submersos em todas as direcções" — but the map shows zero submerged fields
- The card has no source attribution (unlike 6a which cited EMSR861/864)

**Expected:**
- Mondego river drawn and labeled
- Flood extent polygon showing the massive inundation of the Mondego valley agricultural plain
- Dike breach location marked (Casais)
- Evacuation zone indicated
- More of the 42 geocoded events should appear at this zoom
- The Mondego valley flooding was among the most visually dramatic — this chapter should show it

---

## Issue #9: Chapter 6c — Autoestrada camera points to wrong location (~15km off)

**Chapter:** `chapter-6c` (A Autoestrada)
**Severity:** Critical — the map is literally showing the wrong place
**Screenshot:** uploaded image

**Problem:**
- Chapter camera center: `[-8.63, 40.10]` (near Vila Nova de Ancos / Soure area)
- Actual A1 collapse (evt-017): `[-8.487, 40.217]` (km 191, between Coimbra Norte and Coimbra Sul)
- The map is pointed ~15km southwest of where the collapse actually happened
- No markers visible at all — the A1 infrastructure event doesn't even appear on screen
- Same broader issue: no flood extent, no A1 road highlighted, no damage visualization
- The text says "colapsou perto de Coimbra" but the map shows rural fields near Soure

**Fix:**
- Update camera center in `story-config.js` line 165 from `[-8.63, 40.10]` to `[-8.487, 40.217]`
- Ensure evt-017 marker is visible at this zoom
- Highlight the A1 road segment (could query from basemap or add as a GeoJSON line)
- Show the Mondego flood extent that caused the collapse

---

## Issue #10: Chapter 7 — "Cadeia Causal" shows risk index instead of causal synthesis

**Chapter:** `chapter-7` (A Cadeia Causal)
**Severity:** Critical — this is the narrative climax and it contradicts itself
**Screenshot:** uploaded image

**Problem:**
- The chapter is titled "The Causal Chain" and describes WHAT HAPPENED (saturated soil + intense rain + river overflow + burned slopes = catastrophe)
- But the map shows the **precondition RISK INDEX** (Risco crítico / elevado / moderado / baixo) — a forward-looking prediction concept, not a factual retrospective
- This creates a fundamental narrative mismatch: the text presents facts, the map presents forecasts
- The grid dots are back AGAIN, overlaying the risk polygons, adding visual noise with zero informational value
- No timescale indicated — risk of what? when? before which storm?
- The risk polygons themselves are unexplained: what are the boundaries? Districts? Basins? Arbitrary?
- The consequence markers (deaths, evacuations, infrastructure) are scattered on top but disconnected from the risk surface
- This was supposed to be the grand finale synthesis — "each piece alone was manageable, together they created a catastrophe" — but the visual is just layers dumped on top of each other

**Expected:**
- This chapter should be the SYNTHESIS, not a risk map
- Show the causal chain visually: soil moisture (blue) + precipitation (orange/red) + discharge (river lines) + consequence markers = the full picture layered with intention
- Or: a simple, powerful overlay of ALL flood extent polygons from both EMSR activations, with all 42 consequence markers, showing the full geographic scope of the disaster
- The precondition index belongs in Chapter 8 ("O Que os Dados Já Sabiam") where the narrative actually discusses prediction
- Remove the grid dots entirely from this chapter
- If keeping a composite view, each layer needs clear visual separation and purpose

**Structural issue:**
- Chapters 7 and 8 appear to have swapped their visual logic: Ch7 (facts) shows predictions, while Ch8 (predictions) should show predictions
- The precondition index is being deployed in the wrong narrative moment

---

## Issue #11: Chapter 8 — Precondition index contradicts its own text

**Chapter:** `chapter-8` (O Que os Dados Já Sabiam)
**Severity:** Critical — the map disproves the narrative claim
**Screenshot:** uploaded image

**Problem:**
- Text states: "Duas semanas antes de Kristin, este índice mostrava grande parte de Portugal centro e sul em condições de **risco elevado**"
- Map shows: nearly ALL of Portugal in **Risco baixo** (blue) with a sliver of grey (moderado) in the north
- Legend includes Risco crítico (red) and Risco elevado (orange) but **neither color appears anywhere on the map**
- The visualization literally disproves the text — this is worse than showing nothing; it actively undermines the platform's central thesis
- If a journalist or proteção civil manager sees this, the credibility of the entire precondition argument is destroyed

**Root cause (likely):**
- Wrong timestep displayed: may be showing the index at a low-risk date instead of "duas semanas antes de Kristin" (~mid-January 2026)
- Or: the index calculation/classification thresholds are wrong, pushing everything into the lowest category
- Or: the data is for a different variable entirely that happens to share the same legend

**Expected:**
- The precondition index 2 weeks before Kristin (~15 Jan 2026) should show central/southern Portugal in elevated/critical risk
- This is the KEY validation moment: "the data knew" only works if you SHOW it knew
- The map should have a date label ("15 de Janeiro de 2026 — 14 dias antes de Kristin")
- Ideally: temporal animation from low risk → building risk → critical risk, with a "Kristin arrives" marker
- This chapter needs to be bulletproof — it's the intellectual thesis of cheias.pt

**Note:** As flagged in Issue #10, the precondition index visual from Ch7 (which DID show red/orange risk areas) may actually belong here in Ch8. The two chapters may have their layer assignments swapped.

---

## Issue #12: Chapter 9 — Explore mode is empty, buttons broken, no data visible

**Chapter:** `chapter-9` (Explorar os Dados)
**Severity:** Critical — the interactive payoff is completely non-functional
**Screenshot:** uploaded image

**Problem:**
- Map shows bare basemap with Portugal outline — zero data layers visible despite the layer panel listing 6 layers
- "Ver a minha zona" button: not working (geolocation likely not wired)
- "Metodologia" button: not working
- "Partilhar" button: only one that works
- Layer panel (CAMADAS) appears but toggling layers has no visible effect — layers don't exist or aren't loaded
- The entire promise ("explore the data behind this story") is broken
- No basin boundaries visible despite "Bacias hidrográficas" being checked
- No flood extent despite "Área inundada" being checked

**Expected:**
- All 6 layers functional and togglable with visible data
- "Ver a minha zona" triggers geolocation + flies to user's area with local flood data
- "Metodologia" opens a methodology panel or page
- Basin click should show basin-level summary (precondition index, discharge, events)
- This is where the citizen persona gets their personal answer: "was MY area affected?"

---

## SYSTEMIC ISSUES (Summary)

After reviewing all 10 chapters, the problems are not isolated bugs — they're systemic:

### S1: Data exists but isn't rendered
- 5,052 flood polygons processed → not visible in chapters 1, 6a, 6b, 6c, 7, 9
- 42 geocoded consequence events → only 2-3 appear per chapter
- Notebook-generated charts (hydrographs, soil moisture curves) → none used
- Temporal soil moisture and precipitation data → shown as static dot grids

### S2: Grid point rendering is fundamentally wrong
- Chapters 3, 4, 5, 7 all render Open-Meteo grid points as uniform circles
- Citizens cannot interpret a scatter plot of dots — needs heatmaps or continuous surfaces
- Same dot-grid pattern repeated 4 times becomes visually monotonous

### S3: No temporal animation
- The story is about TIME (soil saturating, storms arriving, rivers rising) but nothing animates
- The temporal-player.js exists in src/ but the scroll-driven temporal progression is invisible
- Date labels appear in some chapters but the map doesn't change

### S4: Text-driven rather than data-driven
- Every chapter depends entirely on the text card for information
- The map is decorative background, not the storytelling medium
- Should be inverted: map tells the story, text provides context

### S5: Layer assignments misaligned with narrative
- Ch7 (facts) shows risk predictions; Ch8 (predictions) shows low-risk baseline
- Ch6c camera points to wrong location
- Consequence markers appear randomly rather than filtered per chapter's geographic focus

### S6: Missing visual fundamentals
- Rivers not drawn or labeled anywhere
- Unexplained colors (green dot in Ch6a)
- No inline charts despite notebook outputs
- Hero text illegible (Ch0)

---

## PRIORITY FIX ORDER

| Priority | Issues | Impact |
|----------|--------|--------|
| P0 | #11, #10 | Precondition thesis undermined — swap Ch7/Ch8 layers, fix timestep |
| P0 | #2 | Chapter 1 flood extent not rendering — first impression |
| P1 | #4, #5 | Soil moisture + precipitation → heatmap layers with temporal animation |
| P1 | #7, #8, #9 | 6x triptych: flood polygons + correct coordinates + consequence markers |
| P1 | #12 | Explore mode layers and buttons functional |
| P2 | #6 | River lines + inline hydrograph charts |
| P2 | #1 | Hero text legibility (vignette + text-shadow) |
| P3 | #3 | Atlantic chapter data (storm tracks as MVP) |

---

## SIDEBAR LAYER CONTROL PROPOSAL

Nelson raised: if the scrollytelling has flow, why not use a persistent sidebar for layer control?

**Recommendation:** Add an always-visible, collapsible sidebar (right side) that:
- Shows which layers are active for the current chapter
- Allows manual toggle during scroll (advanced users)
- Displays the current temporal position (date/timestamp) when animation is active
- Collapses to a thin icon strip during reading, expands on hover/click
- Transitions smoothly to the full explore panel in Chapter 9

This would make the layer state transparent throughout the narrative instead of hidden until the end.

---

*QA review complete — 12 issues, 6 systemic patterns identified.*

