# cheias.pt — v2 Review: QA, UX Modernization & Dev Session Plan

**Date:** 2026-02-11
**Status:** Proto-MVP complete, not shareable yet. Functional but feels dated.

---

## Part 1: QA Review — What's Solid, What Needs Work

### What's Working Well

The v1 build is structurally sound. 17/17 files pass, 15/15 API tests pass, all browser integration checks pass. The data pipeline is correct: soil moisture → precondition index → choropleth is computing real values (Mondego at 1.00, Sado at 0.60) that match ground truth. Event-driven architecture (custom DOM events decoupling map from UI) is clean and extensible. The code is well-organized with clear file ownership.

### Issues to Fix in v2

**P0 — Breaks the experience:**

1. **Overlapping polygon layers create visual confusion.** Districts (filled, colored) and basins (filled + outlined, blue) overlap everywhere. The blue basin outlines fight with the district colors. At a glance you can't tell what's what. This is the #1 visual problem.

2. **No context strip / status bar.** The map loads and shows colors, but there's no text anywhere on the map itself that says "what's happening right now." A person opening this during a flood crisis sees abstract colors but no situational context. Compare Windy.com: even before you interact, the active layer label and current conditions are visible.

3. **The sidebar district screenshot doesn't show a sidebar** — the Playwright test captured the same view twice (qa-initial-load.png and qa-sidebar-district.png are identical). Either the sidebar animation wasn't captured properly or there's a timing issue in the screenshot capture. Not a code bug per se, but the QA evidence is incomplete.

**P1 — Shareable but weak:**

4. **No "last updated" timestamp.** Users have no idea if data is live or stale. Every monitoring platform shows when data was last refreshed.

5. **No data loading feedback per station.** The loading overlay covers everything, then disappears. If 1 of 11 stations hits a 429, the user never knows — the district just turns gray. Should show which stations loaded successfully.

6. **Rate limiting mitigation.** 22 API calls (11 soil + 11 discharge) fire simultaneously. This works most of the time but triggers 429s under real conditions. Need request staggering (50ms delay between calls) or batch endpoints.

7. **Basin fill at 5% opacity still captures mouse events.** The basins-fill layer has `fill-opacity: 0.05` which is visually invisible but still intercepts clicks. This means clicking a district sometimes triggers a basin event instead. Layer order / click priority needs work.

8. **Chart bridge points for past→forecast transition.** The charts.js has complex logic to "bridge" the last past value to the first forecast value. In some cases the bridge logic produces gaps. The soil moisture chart shows a disconnect between observed and forecast segments.

**P2 — Polish:**

9. **Soil moisture display shows m³/m³ as percentage.** The sidebar shows `latestSoilMoisture * 100` as a percentage, but 0.25 m³/m³ is not 25% saturation — it's 25% volumetric water content. The label should clarify this or show it relative to field capacity.

10. **Mobile bottom sheet has no swipe-to-dismiss.** The CSS transition works for hide/show, but there's no touch gesture handler. Users expect to swipe down to close.

11. **Legend overlay blocks the sidebar.** Both use `position: fixed` on the right side. If legend is open and you click a district, the sidebar slides in behind the legend.

---

## Part 2: UX Modernization — From GIS Dashboard to Modern Platform

### The Core Problem

The current UI looks like what it is: a GIS analyst's tool. Colored polygons on a dark map, a sidebar with technical charts. It works, but it feels like QGIS with a dark theme — not like Windy.com, Ventusky, or a modern civic tech product.

The reference platforms that get millions of views (Windy, Ventusky, fogos.pt) share specific patterns that cheias.pt is missing:

### What Modern Geo Platforms Do Differently

**1. Single primary visual layer, not stacked polygons**

Windy and Ventusky never show two filled polygon layers at once. They show ONE continuous surface (temperature gradient, wind particles, precipitation radar) with clean boundary lines. The current cheias.pt shows district fills + basin fills + basin outlines simultaneously — that's three layers of overlapping geometry.

**Fix:** Remove the basin fill layer entirely. Show basins ONLY as thin dashed outlines (or hide them at overview zoom and show them only when zoomed in). The district choropleth should be the single dominant visual at the country scale. Basins become a detail-level feature.

**2. Continuous color ramps instead of 4-bucket classification**

The current 4-color classification (green/yellow/orange/red) creates hard boundaries between districts that look jarring. Two adjacent districts at index 0.29 and 0.31 show as green vs yellow. Modern platforms use continuous gradients.

**Fix:** Use a `['interpolate', ['linear'], ...]` expression in MapLibre to smoothly blend from green → yellow → orange → red based on the actual index value. Keep the 4-level classification for the legend and sidebar labels.

**3. Contextual information strip (the "what's happening" bar)**

Every modern monitoring platform has a context strip that tells you what you're looking at before you interact. Ventusky shows the active layer name + model + time. Fogos.pt shows active fire count. Google Flood Hub shows flood gauge count.

**Fix:** Add a floating status bar at the bottom (above mobile nav if applicable) showing: "Última atualização: 14:30 · 8 distritos em risco elevado · 3 avisos IPMA ativos". This is the "headline" that makes the map instantly meaningful.

**4. News/events integration (the "reality bridge")**

Nelson's right — the platform is disconnected from the reality people experience through media. A map showing "Muito Elevado" for Coimbra doesn't connect to "Mondego dike burst, 3600 evacuated." This is what makes the difference between a data tool and a civic platform.

**Approach for v2 (lightweight):**
- Add an "Eventos" panel (collapsible, bottom-left) that shows IPMA warning text as event cards
- IPMA warning text IS the news — it's authoritative, timestamped, and location-specific
- Format as a scrollable timeline: most recent first, color-coded by severity
- This doesn't require scraping or news APIs — the data is already being fetched

**Approach for v3 (later):**
- RSS feeds from Proteção Civil, Lusa, RTP
- Copernicus Emergency Management Service activations
- Social media integration (Twitter/X flooding reports)

**5. Algorithm transparency ("Why should I trust this?")**

Modern data products explain their methodology. The precondition index is cheias.pt's unique value prop but it's invisible to users. People see colors but don't know what drives them.

**Fix:** Add an "Info" button in the header (next to Legenda) that opens a brief methodology panel:
- "O Índice de Precondição combina 3 fatores:"
- Soil moisture icon + "Humidade do solo atual" (from Open-Meteo)
- Rain icon + "Precipitação prevista nos próximos 7 dias" (from Open-Meteo)
- Earth icon + "Capacidade de absorção do solo" (field capacity)
- "Quando o solo já está saturado e se prevê mais chuva, o risco de cheia aumenta."
- Link to the full technical explanation (future blog post / about page)

**6. Visual refinement — from GIS to product**

Specific changes:

- **Reduce district fill opacity from 0.5 to 0.25–0.35.** The current colors are too saturated and obscure the basemap. Let the dark basemap breathe through.
- **Use a subtle glow/gradient on district boundaries** instead of flat white 1px lines. Modern maps use `line-blur` and slightly wider semi-transparent lines for a softer look.
- **Add district name labels on the map.** Currently, only the basemap labels show. Adding district names at the centroid (small, white, with text-halo) makes the map navigable without clicking.
- **Animate the choropleth on load.** Instead of everything appearing at once, fade the districts in with a slight stagger. This signals "data just arrived" and feels alive.
- **Soften the sidebar.** Add a subtle backdrop-filter blur behind the sidebar (`backdrop-filter: blur(12px)`) with slightly transparent background. This is what makes modern sidebars feel like glass overlays rather than opaque walls.
- **Improve the header.** Add a subtle gradient or glass effect. The current flat `#16213e` feels dated. A `background: rgba(22, 33, 62, 0.85); backdrop-filter: blur(10px)` gives it a modern floating feel.

**7. Typography upgrade**

The current system font stack is fine for performance but generic. For a civic emergency platform:

- **Header/brand:** Consider a geometric sans like DM Sans or Outfit (Google Fonts, free) for the "cheias.pt" wordmark
- **Body:** Keep the system stack for data/numbers, but the sidebar section titles could use the brand font for cohesion

**8. Empty state / calm state design**

When there are no warnings and all indices are low, the map is just... green. There's no messaging that says "tudo normal." A calm-state message ("Sem alertas ativos. Última verificação: 14:30") should be visible.

---

## Part 3: v2 Dev Session Plan

Estimated scope: 2–3 hours with Claude Code agent team.

### Priority Order (highest impact first)

**Batch 1 — Visual cleanup (fixes the "ick")**
- [ ] Remove `basins-fill` layer, keep `basins-outline` only as dashed line
- [ ] Switch basins-outline to `line-dasharray: [4, 2]` and reduce opacity to 0.4
- [ ] Replace 4-bucket district colors with interpolated color ramp
- [ ] Reduce district fill opacity to 0.30
- [ ] Add district name labels (symbol layer at centroids)
- [ ] Add `line-blur: 1` to district outlines, change to `rgba(255,255,255,0.15)`

**Batch 2 — Context & trust (fixes "disconnected from reality")**
- [ ] Add status bar at bottom: last updated time, # districts at risk, # active warnings
- [ ] Add IPMA events timeline panel (bottom-left, collapsible, uses existing warning data)
- [ ] Add "Sobre o Índice" info panel (methodology explainer in Portuguese)

**Batch 3 — Polish**
- [ ] Glass-morphism header: `backdrop-filter: blur(10px)` + semi-transparent bg
- [ ] Glass-morphism sidebar: `backdrop-filter: blur(12px)` + `rgba(26,26,46,0.85)` bg
- [ ] Stagger district fade-in animation on load
- [ ] Fix chart bridge point gaps (simplify the past→forecast transition logic)
- [ ] Add "Última atualização" timestamp to sidebar
- [ ] Request staggering: 50ms delay between Open-Meteo calls
- [ ] Fix z-index conflict between legend and sidebar

### Agent Team Structure for v2

Same 3-agent structure as v1, but tighter scope:

- **Agent 1 (Map):** Batches 1 — layer changes, color ramp, labels, animations
- **Agent 2 (UI):** Batches 2+3 — status bar, events panel, info panel, glass effects, header
- **Agent 3 (Data):** Request staggering, timestamp tracking, chart bridge fix

### CLAUDE.md Additions for v2

```markdown
## v2 Changes

### Map Layer Hierarchy (bottom to top)
1. Basemap (dark-matter)
2. districts-fill (interpolated color, opacity 0.30)
3. districts-outline (soft white, line-blur: 1)
4. districts-outline-hover
5. basins-outline (dashed, blue, opacity 0.4) — NO basins-fill
6. basins-outline-hover
7. district-labels (symbol, white text with dark halo)
8. warnings-pulse
9. warnings-circle
10. warnings-label

### Color Ramp Expression
```javascript
['interpolate', ['linear'], ['get', '_preconditionIndex'],
  0.0, '#2ecc71',
  0.3, '#f1c40f',
  0.6, '#e67e22',
  0.8, '#e74c3c'
]
```

### Status Bar
Fixed bottom bar, z-index 150, glass bg.
Content: "Atualizado às HH:MM · N distritos em risco · N avisos IPMA"
```

---

## Part 4: Reference Platforms & Design Patterns

### Tier 1 — Aspirational UX (what "modern" looks like)

**Windy.com** — The gold standard for weather map UX. Key patterns:
- Single dominant layer with particle animations (wind, rain, temperature)
- Layer selector as compact bottom toolbar, not sidebar
- Point-of-interest details appear as floating cards, not full sidebars
- Time scrubber at the bottom for forecast animation
- Everything feels alive — particles move, colors shift

**Ventusky** — Windy's main competitor, slightly more data-oriented:
- Continuous color gradients (never bucket classification)
- Model comparison toggle (GFS vs ICON vs GEM)
- Clean typography (custom sans-serif, high contrast on dark)
- Forecast charts appear inline when tapping a point
- 3D globe option for dramatic presentation

**Google Flood Hub** — Academic/research tone but clean:
- Very muted base map, flood data as the only color
- Gauge-style icons on the map itself (not just colors)
- Side panel with forecast charts + historical context
- "Inundation probability" as a subtle raster overlay

### Tier 2 — Portuguese civic tech (cultural context)

**fogos.pt** — What cheias.pt is modeled after:
- Strengths: radical simplicity, immediate comprehension, trust built over years
- Weaknesses: visually dated (2016-era Mapbox), no analysis, no prediction
- Key lesson: people don't care about your tech — they care about seeing their town on the map

**incendios.pt** (Flipside/DevSeed) — Historical fire data explorer:
- Clean statistical presentation by region
- Downloadable data (CSV)
- Less about real-time, more about understanding patterns

### What This Means for cheias.pt v2

The gap between fogos.pt (functional but dated) and Windy (beautiful but technically overwhelming) is exactly where cheias.pt should sit:

- **fogos.pt simplicity** — map-first, immediate comprehension, Portuguese
- **Windy visual quality** — continuous gradients, glass effects, alive feeling
- **Google Flood Hub trust** — methodology transparency, data sourcing visible
- **Unique value** — precondition analysis (not just observation), IPMA integration, Portuguese context

The platform should feel like it was designed by someone who understands both emergency management AND modern product design. Not a GIS tool with a dark theme. Not a startup MVP with placeholder UX. A considered, purposeful civic technology product.
