# cheias.pt — QA Diagnostic Report
## Sprint 01 Visual Review — 2026-02-17

---

## EXECUTIVE SUMMARY

The scrollytelling framework (scroll observer, chapter transitions, camera fly-to, glassmorphism cards) is functional infrastructure. However, the data visualization layer — which is the entire purpose of the platform — is either missing, broken, or misassigned in **every single chapter**. 

Extensive data processing was completed (5,052 flood polygons, 42 geocoded events, temporal soil moisture, precipitation accumulation, discharge hydrographs, precondition index) but almost none of it reaches the screen in a meaningful way.

The result is a text-driven slideshow with decorative maps, not a data-driven geo-narrative.

---

## ISSUES LOG

### Issue #1: Hero text illegible (Chapter 0)
- **Severity:** High
- Title/subtitle/byline float over map with no background treatment
- `chapter--hero` is the only section without a `.chapter__card` glassmorphism wrapper
- Map labels compete directly with text
- **Fix:** Vignette overlay + text-shadow (not a card — preserve cinematic feel)

### Issue #2: No flood data visible (Chapter 1)
- **Severity:** Critical
- Text says "O vermelho é água onde antes havia terra" but NO red flood extent on map
- Only dark basemap with administrative boundaries
- Floating legend shows "Área inundada" but layer not rendering
- **Root cause:** Data not loading, PMTiles path wrong, or layer-manager not wiring chapter-1 to flood-extent source

### Issue #3: Empty Atlantic map (Chapter 2)
- **Severity:** Medium
- Map zooms to full Atlantic but shows nothing beyond basemap
- Card contains dev placeholder: "Visualização de dados atmosféricos em desenvolvimento"
- Moisture arrow SVG works but map does zero work
- **MVP fix:** Storm track polylines with labels at minimum

### Issue #4: Soil moisture is static dot grid (Chapter 3)
- **Severity:** High
- Uniform blue circles on point grid — looks like dot matrix, not data
- No visual gradient from dry→saturated
- Date label shows "1 de Dezembro 2025" but visual doesn't change with scroll
- ~2 months of processed temporal data completely lost
- **Required:** Continuous heatmap with scroll-driven temporal animation

### Issue #5: Precipitation is static dot grid (Chapter 4)
- **Severity:** High
- Same dot-grid pattern as Ch3, now with orange/red dots
- Static snapshot — text describes THREE storms in sequence but map frozen
- Triple-punch rhythm (Kristin → Leonardo → Marta) invisible
- **Required:** Animated heatmap looping through storm sequence with timestamps

### Issue #6: Rivers invisible, notebook charts unused (Chapter 5)
- **Severity:** High
- Text names Tejo, Mondego, Sado — none drawn or labeled on map
- Same dot-grid (discharge points) dampened by dark polygon overlay
- Dramatic claims ("nível mais alto em quase 30 anos") with zero quantitative evidence
- Notebook-generated discharge hydrographs exist but not integrated
- **Required:** River lines + inline sparkline/hydrograph charts in cards

### Issue #7: Unexplained green dot, empty impact map (Chapter 6a — Alcácer)
- **Severity:** High
- Green dot has no legend entry (legend shows Mortes/Evacuações/Infraestrutura/Deslizamentos)
- Only 2 consequence markers visible
- No CEMS flood extent despite card citing EMSR861/864
- Sado river barely visible
- **Required:** Flood polygons + all local consequence markers + fix green dot

### Issue #8: Coimbra dike breach invisible (Chapter 6b)
- **Severity:** High
- "Dique cedeu em Casais", "3.000 evacuadas" over near-empty dark map
- Only 2 markers visible (1 Mortes, 1 Infraestrutura)
- Mondego river invisible, no breach location marked
- No source attribution in card
- **Required:** Mondego river + flood extent + breach location + evacuation zone

### Issue #9: Autoestrada camera at wrong location (Chapter 6c)
- **Severity:** Critical
- Camera: `[-8.63, 40.10]` (Vila Nova de Ancos/Soure area)
- Actual A1 collapse (evt-017): `[-8.487, 40.217]` (km 191)
- Map pointed ~15km southwest of collapse site
- Zero markers visible
- **Fix:** Update story-config.js camera center

### Issue #10: "Cadeia Causal" shows risk index instead of factual synthesis (Chapter 7)
- **Severity:** Critical
- Text describes WHAT HAPPENED but map shows forward-looking RISK INDEX
- Narrative mismatch: facts narrated, predictions visualized
- Grid dots overlaying risk polygons add visual noise
- Risk polygons have unexplained boundaries
- **Required:** This chapter should show ALL flood extent + ALL consequence markers as synthesis

### Issue #11: Precondition index contradicts its own text (Chapter 8)
- **Severity:** Critical
- Text: "grande parte de Portugal centro e sul em condições de risco elevado"
- Map: nearly ALL of Portugal in Risco baixo (blue)
- Red and orange risk classes don't appear anywhere on map
- Visualization literally disproves the platform's central thesis
- **Root cause:** Wrong timestep, broken classification, or layers swapped with Ch7

### Issue #12: Explore mode non-functional (Chapter 9)
- **Severity:** Critical
- Zero data layers visible despite 6 layers listed in panel
- "Ver a minha zona" — broken
- "Metodologia" — broken
- Layer toggles have no visible effect
- **Required:** All layers functional, geolocation working, basin click interaction

---

## SYSTEMIC PATTERNS

### S1: Data processed but not rendered
- 5,052 flood polygons → invisible in Ch1, Ch6a-c, Ch7, Ch9
- 42 geocoded consequence events → 2-3 appear per chapter
- Notebook charts (hydrographs, moisture curves) → zero integrated
- Temporal datasets → shown as static snapshots

### S2: Grid points rendered as uniform dots
- Ch3, Ch4, Ch5, Ch7 all use same uninformative dot-grid pattern
- Citizens cannot read scatter plots — needs continuous surfaces
- Monotonous repetition (4 chapters look identical)

### S3: No temporal animation despite temporal data
- Story is fundamentally about TIME (saturation building, storms arriving, rivers rising)
- temporal-player.js exists but scroll-driven progression invisible
- Date labels change but map doesn't

### S4: Text-driven, not data-driven
- Every chapter depends entirely on the card text
- Map is decorative backdrop, not storytelling medium
- Should be inverted: map drives narrative, text provides context

### S5: Layer assignments misaligned with narrative arc
- Ch7 (retrospective facts) shows predictive risk index
- Ch8 (predictive thesis) shows low-risk baseline
- Ch6c camera 15km from actual event
- Consequence markers not filtered per chapter's geographic scope

### S6: Missing visual fundamentals
- Rivers never drawn or labeled (in a flood story)
- Unexplained colors (green dot in Ch6a)
- No inline charts from notebooks
- Hero text illegible
- Tsunami emoji favicon (🌊) for a fluvial flood platform

---

## FUNDAMENTAL DIAGNOSIS

The scrollytelling is not presenting a **temporal sequence**. The design document establishes that the story IS the timeline:

1. Soil saturates over weeks (Dec 2025 → Jan 2026)
2. Kristin hits (29 Jan) on already-saturated ground
3. Leonardo hits (6 Feb) before rivers recover
4. Marta follows days later
5. Rivers peak, dikes break, infrastructure collapses
6. The precondition index — validated by the timeline — proves this was predictable

Without the temporal backbone, individual chapters become disconnected static views. The precondition index conclusion is meaningless without first showing the viewer the progression that makes it credible.

**The current build skipped the timeline and jumped to conclusions.**

---

## ADDITIONAL NOTE: Favicon

The tsunami wave emoji (🌊) as favicon is incorrect for a fluvial flood platform. Tsunamis are seismic; this story is about riverine/pluvial flooding. It also reads as casual/playful for a platform about a disaster that killed 11 people. Should be replaced with something appropriate — a simple water level icon, a river symbol, or just the cheias.pt wordmark.
