# cheias.pt — Narrative Vision & Visual Identity

Extracted from the original design document. This contains the storytelling
architecture and visual identity — NOT implementation constraints.
The full document lives at `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/12-design-document.md`.

NOTE: The data gaps listed in the original chapter storyboard (SST, IVT, CEMS flood
extent, consequence markers, IPMA warnings, etc.) have largely been resolved since it
was written. Walk `data/` for the current inventory — it's significantly richer than
what this document assumed was available.

---

# cheias.pt — Design Document

## The Winter That Broke the Rivers

A scroll-driven geo-narrative about the January–February 2026 flood crisis in Portugal. Not a monitoring dashboard. Not a data dump. A story told through maps, satellite imagery, and data — about what happened, why it happened, and what it means.

This document is the primary specification for implementation. It integrates findings from Elena's Four Questions (file 11), Vizzuality methodology research (file 10 + three Claude Code skills), and real-time crisis data from the ongoing emergency.

---

## 1. Strategic Reframing

### Why scrollytelling, not a dashboard

The original cheias.pt concept was a real-time monitoring platform (Mode 1 Glance + Mode 2 Explore). That remains the long-term vision, but the immediate opportunity is different.

Portugal is in a state of emergency. Storms Kristin, Leonardo, and Marta have killed at least 11 people, displaced thousands, collapsed the A1 motorway, burst the Mondego levee, and triggered a €2.5B aid package across 69 municipalities. The Tejo reached its highest level since 1997. The Sado hit levels unseen since 1989.

This is not a moment for a dashboard that needs live data feeds and backend uptime. This is a moment for a **retrospective narrative** — a finished, publishable artifact that tells the story of what happened and why. It works as a static deploy (no backend), it works in any weather, and it's the exact deliverable that Vizzuality and Development Seed ship for environmental organizations worldwide.

### Persona shift: from urgency to understanding

File 11 defined four personas around the question "Am I in danger right now?" The scrollytelling reframes them:

| Persona | Dashboard question (real-time) | Scrollytelling question (retrospective) |
|---------|-------------------------------|----------------------------------------|
| Cidadão afetado | "A minha zona está em risco agora?" | "O que aconteceu na minha zona? Podia ter sido previsto?" |
| Gestor proteção civil | "Onde posiciono recursos nas próximas 24h?" | "Onde é que o sistema falhou? Que sinais devíamos ter visto?" |
| Jornalista | "Qual é a história agora?" | "Qual é a história maior? Onde estão os dados que posso citar?" |
| Autarca | "O que está a acontecer no meu concelho?" | "Que evidência tenho para pedir investimento em prevenção?" |

The common thread: **curiosity about what went wrong**, not urgency about what's going wrong. This is a story about causality, not a feed of alerts.

### Portfolio positioning

For Development Seed evaluators: this piece demonstrates the same stack they build (MapLibre, STAC, COG, Sentinel imagery, cloud-native geospatial) but wrapped in the editorial storytelling quality of a Vizzuality piece. It proves Nelson can bridge the technical pipeline with the communication layer — which is exactly the gap most geo-developers can't cross.

---

## 2. Narrative Architecture

### Template selection

This story is a hybrid of two narrative templates from the geo-storytelling skill:

- **The Accumulation** — moisture and soil saturation building over weeks, invisible until the threshold breaks
- **The Journey** — following the water from Atlantic moisture source → Portuguese catchment basins → river systems → communities

The hybrid structure: a temporal accumulation that *also* moves through geographic scales, from the planetary (Gulf of Mexico/Atlantic moisture transport) to the continental (Iberian Peninsula weather systems) to the national (Portuguese river basins) to the local (Alcácer do Sal streets, Coimbra levee, A1 collapse).

### Emotional engagement sequence (Elena's framework)

| Phase | Design moment | Cheias.pt implementation |
|-------|--------------|--------------------------|
| **Delight** | First screen wonder | Dark basemap, Portugal coastline glowing. Slow camera descending from Atlantic-scale view. Serif title over ocean: "O Inverno Que Partiu os Rios." Beautiful, quiet, ominous. |
| **Curiosity** | What triggers questions? | The soil moisture map appearing under the terrain — green turning amber turning red over weeks. "Why was the ground already full before the first storm arrived?" |
| **Exploration** | Self-directed discovery | After the guided narrative, user unlocks free map exploration. Toggle between before/after satellite imagery. Click any basin to see its specific story. |
| **Digestion** | Personal relevance | The precondition index for THEIR location. "Here's what the data showed for your area. Here's what it means for next time." Geolocation-triggered personal relevance. |

### Three-act structure

**Act 1 — WHAT (1 chapter): The Hook**
One image, one number. Satellite view of the flooded Tejo valley. "In February 2026, Portugal's rivers broke." Camera at national scale, Sentinel-1 flood extent map fading in over the terrain.

**Act 2 — WHY (5–6 chapters): The Evidence**
This is where the story lives. Each chapter reveals a layer of causality:

- Chapter 2: The planetary scale — how an unusually energetic Atlantic season pushed moisture from the subtropics toward Iberia. SST anomalies, atmospheric river visualization. Wide camera, continental.
- Chapter 3: The setup — weeks of antecedent rainfall saturating Portuguese soils. Soil moisture animation from December through January. The ground filling like a sponge. National scale, zooming to the worst basins.
- Chapter 4: The storms arrive — Kristin, Leonardo, Marta in sequence. Precipitation accumulation maps. IPMA warnings escalating from yellow to orange to red. Zooming from national to the Tejo/Sado/Mondego basins.
- Chapter 5: The rivers respond — GloFAS discharge data showing rivers climbing past thresholds. The precondition index (saturated soil + heavy rain + rising discharge) going critical. Basin-level zoom.
- Chapter 6: The consequences — flood extent polygons, damage markers, landslide locations, road closures, evacuations. Geocoded news and photos. This is the human chapter. Close-up on Alcácer do Sal, Coimbra, the A1 collapse.
- Chapter 7 (climax): The full picture — pull back to national scale showing ALL consequences overlaid on the precondition conditions. The causal chain visible in a single frame: saturated soil + incoming rain + overwhelmed rivers = this. The moment where understanding crystallizes.

**Act 3 — ACTION (1–2 chapters): The Resolution**
- Chapter 8: "What this means" — return to Portugal overview. Strip back to one layer: the precondition index methodology. Explain how this combination of signals could have predicted what happened. Link to live monitoring (future phase).
- Chapter 9: Free exploration — "Explore the data yourself." Map unlocks. User can toggle layers, click basins, zoom to their area. CTA: subscribe, share, explore methodology. Transition from guided narrative to Mode 1/2 of the future platform.

### Physical metaphor

**Water depth.** Scroll = descending into water. The story begins above the surface (atmospheric, continental) and progressively sinks into the flooded landscape. Visual treatment: blue gradients deepening, transparency suggesting submersion, flow lines appearing as the narrative approaches the rivers. The basemap tint shifts from warm atmospheric tones in Act 1 to cool, watery tones by Act 2's end.

---

## 3. Chapter Storyboard

### Chapter 0: Title Screen

```
Camera: center [-15, 35], zoom 3, pitch 0, bearing 0
Duration: 150vh scroll height (extended first impression)
Layers: none (dark basemap only, Portugal coastline barely visible)
Animation: Slow flyTo from Atlantic-wide view
Content: Full-screen title overlay
  Title: "O Inverno Que Transbordou os Rios"
  Subtitle: "Como três tempestades expuseram a fragilidade de Portugal"
  Byline: "cheias.pt · Uma história contada com dados de satélite e modelos hidrológicos"
Alignment: fully (centered overlay)
```

Design notes: dark navy basemap (#0a212e), serif title (Georgia, 45px, weight 300), 2px letter spacing. The Atlantic Ocean dominates. Portugal is a small shape at the edge. This establishes the planetary scale before we descend.

### Chapter 1: The Hook (Act 1)

```
Camera: center [-8.5, 39.5], zoom 6.5, pitch 15, bearing 5
Animation: flyTo (3000ms, high arc from Atlantic)
Layers:
  - sentinel1-flood-extent: opacity 0.8 (red/magenta over terrain)
  - portugal-outline: opacity 0.3 (context)
Content:
  Title: "7 de Fevereiro de 2026"
  Text: "O satélite Sentinel-1 capturou esta imagem. O vermelho é água
         onde antes havia terra. O Tejo atingiu o nível mais alto desde 1997.
         11 pessoas morreram. 69 municípios declararam calamidade."
  Image: Sentinel-1 flood extent composite (ESA published Feb 7)
Alignment: left
Legend: [{ title: "Área inundada", color: "#e74c3c" }]
```

Design notes: This is the before/after moment. The Sentinel-1 composite from ESA (Feb 7 acquisition, Dec 27 baseline) is the visual anchor. One image, one devastating number. No explanation yet — just the fact.

### Chapter 2: The Atlantic Engine

```
Camera: center [-30, 30], zoom 3, pitch 0, bearing 0
Animation: flyTo (2500ms, pulling back to Atlantic scale)
Layers:
  - sst-anomaly: opacity 0.7 (sea surface temperature anomalies)
  - atmospheric-river-track: opacity 0.9 (animated flow lines if possible, static path if not)
Content:
  Title: "A Energia do Atlântico"
  Text: "O inverno de 2025-26 trouxe uma energia incomum ao Atlântico Norte.
         Temperaturas da superfície do mar acima da média alimentaram uma
         sequência de tempestades: Harry, Ingrid, Joseph, Kristin, Leonardo,
         Marta. Cada uma carregou mais humidade do que a anterior — humidade
         que viajou milhares de quilómetros até embater na costa portuguesa."
Alignment: right
```

Design notes: This is the largest geographic scale in the story. The viewer sees the full Atlantic, with Portugal as a small target at the end of a moisture highway. This chapter justifies *why* — the energy that drove the crisis originated far from Portugal.

**DATA GAP — SST anomaly data:** Need ERA5 or OISST sea surface temperature anomaly maps for Dec 2025–Feb 2026 Atlantic. Available from Copernicus Climate Data Store (ERA5 SST) or NOAA OISST. This is a static raster — download and convert to COG for display.

**DATA GAP — Atmospheric river tracks:** IVT (integrated vapor transport) data from ERA5 reanalysis would show the moisture pathways. Alternative: use published storm track maps from IPMA or AEMET as static image overlays if IVT processing is too complex for MVP.

### Chapter 3: The Sponge Fills

```
Camera: center [-8.3, 39.8], zoom 7, pitch 20, bearing -5
Animation: flyTo (2000ms)
Layers:
  - soil-moisture-animation: opacity 0.8 (temporal sequence, Dec 1 → Jan 31)
  - basins-outline: opacity 0.4 (catchment context)
Content:
  Title: "O Solo Encharca"
  Text: "Antes de qualquer tempestade, o solo já estava encharcado.
         Semanas de chuva persistente saturaram os primeiros 30 centímetros
         de terra — a camada que absorve a chuva e impede cheias.
         Quando Kristin chegou em Janeiro, o solo já não tinha para onde
         mandar a água. Cada gota adicional ia directamente para os rios."
Alignment: left
Legend: [
  { title: "Solo seco", color: "#f7f7f7" },
  { title: "Solo saturado", color: "#2166ac" }
]
```

Design notes: This is the key scientific insight of the entire story — the precondition thesis. Soil moisture animation shows the ground progressively filling. Use Open-Meteo historical soil moisture data (0–28cm, the storm-relevant layers) gridded across Portugal. The animation should be scroll-controlled or auto-play with a timeline scrubber.

**DATA SOURCE:** Open-Meteo Historical Weather API — soil_moisture_0_to_7cm + soil_moisture_7_to_28cm. Daily values, Dec 1 2025 – Jan 31 2026. Grid of ~50–100 points across Portugal, interpolated to a heatmap. Zero auth, JSON response.

**PROCESSING NEEDED:** Fetch daily soil moisture grid → normalize to 0–1 saturation range → generate frame per day → animate via MapLibre data-driven styling or temporal playback.

### Chapter 4: The Storms

```
Camera: center [-8.5, 39.5], zoom 7.5, pitch 25, bearing 10
Animation: easeTo (1500ms, staying in same region)
Layers:
  - precipitation-accumulation: opacity 0.8 (cumulative rainfall map, Jan 25 – Feb 7)
  - ipma-warnings-timeline: opacity 0.9 (animated warning escalation markers)
  - basins-outline: opacity 0.3
Content:
  Title: "Três Tempestades em Duas Semanas"
  Text: "Kristin atingiu a costa a 29 de Janeiro com ventos de força de
         furacão — possivelmente a tempestade mais forte desde que há
         registos. Antes que os rios baixassem, Leonardo chegou a 6 de
         Fevereiro, despejando o equivalente a três dias de chuva em 24 horas.
         Marta seguiu-se dias depois. Na zona de Grazalema, em Espanha,
         caíram mais de 500mm num único dia."
  Image: GPM precipitation accumulation map (Feb 1–7, from ESA/NASA)
Alignment: right
Legend: [
  { title: "> 250mm", color: "#e74c3c" },
  { title: "100–250mm", color: "#F7991F" },
  { title: "50–100mm", color: "#f7f7b5" },
  { title: "< 50mm", color: "#2166ac" }
]
```

Design notes: GPM precipitation accumulation map (published by ESA, showing Feb 1–7 data) as the primary visual. IPMA warnings can be shown as animated markers escalating from yellow to orange to red across districts — this uses the existing districts.geojson + ipma_code property.

**DATA SOURCE — Precipitation:** Open-Meteo Historical Weather API — precipitation_sum daily, same point grid as soil moisture. Or download the GPM accumulation raster directly from NASA/ESA.

**DATA SOURCE — IPMA warnings:** Historical warnings are NOT readily available from the IPMA API (it serves current warnings). This is a gap. Options: (a) manually reconstruct from news coverage and IPMA archives, (b) scrape Wayback Machine or IPMA social media posts for warning histories, (c) use Open-Meteo weather code data as proxy. This needs investigation.

### Chapter 5: The Rivers Rise

```
Camera: center [-8.4, 39.6], zoom 8, pitch 30, bearing -10
Animation: easeTo (1200ms)
Layers:
  - glofas-discharge: opacity 0.9 (river discharge lines, thickness = magnitude)
  - basins-fill: opacity 0.4 (basins colored by precondition index)
  - soil-moisture-snapshot: opacity 0.3 (jan 31 state, faded context)
Content:
  Title: "Os Rios Respondem"
  Text: "O Tejo. O Mondego. O Sado. Cada rio carrega a história do seu
         território — a chuva que caiu, o solo que não absorveu, as
         descargas das barragens espanholas a montante. O caudal do Tejo
         atingiu o nível mais alto em quase 30 anos. O Sado voltou a
         valores de 1989. Em Coimbra, o dique do Mondego cedeu."
Alignment: left
Legend: [
  { title: "Caudal excepcional", color: "#e74c3c", type: "line" },
  { title: "Caudal elevado", color: "#F7991F", type: "line" },
  { title: "Caudal normal", color: "#2166ac", type: "line" }
]
```

Design notes: River discharge visualized as line thickness on the basins.geojson river network. GloFAS data via Open-Meteo Flood API provides 7-day forecast + historical data. Show rivers "swelling" — thickening lines that animate as discharge increases. The precondition index (soil saturation + forecast rain + discharge anomaly) should be calculable for each basin.

**DATA SOURCE:** Open-Meteo Flood API — daily river discharge for GloFAS points in Portuguese basins. Historical data going back through the event. Zero auth.

**PROCESSING NEEDED:** Identify GloFAS grid points within each basin polygon (spatial join with basins.geojson). Fetch discharge time series. Calculate anomaly against historical mean. Render as data-driven line width.

### Chapter 6: The Human Cost

```
Camera: center [-8.52, 38.37], zoom 12, pitch 40, bearing 15
  → Then: easeTo to [-8.43, 40.21], zoom 11, pitch 35, bearing -10 (Coimbra)
  → Then: easeTo to [-8.63, 40.10], zoom 13, pitch 45, bearing 5 (A1 collapse)
Animation: Multi-stop within single chapter (triggered by sub-scroll positions)
Layers:
  - flood-extent-polygons: opacity 0.7 (CEMS EMSR861/EMSR864 delineation products)
  - consequence-markers: opacity 1.0 (geocoded events: deaths, evacuations, collapses, landslides)
  - satellite-after: opacity 0.6 (Sentinel-2 true color post-flood)
Content:
  Title: "O Custo Humano"
  Sub-sections (scroll-triggered within chapter):
    1. Alcácer do Sal: "A água do Sado subiu dois metros no centro da vila.
       Moradores descreveram uma calamidade que não viam há 30 anos."
    2. Coimbra: "O dique do Mondego cedeu em Casais. 3.000 pessoas
       evacuadas numa noite. Campos agrícolas submersos em todas as
       direcções."
    3. A1: "A principal auto-estrada do país colapsou perto de Coimbra.
       A artéria Norte-Sul de Portugal, cortada."
Alignment: alternating left/right per sub-section
```

Design notes: This is the emotional climax — the chapter where data becomes human. Multi-stop camera moves within a single scroll chapter. Geocoded consequence markers (each with coordinates + timestamp + source attribution) appear as the user scrolls through each sub-section.

**DATA GAP — Flood extent polygons (CRITICAL):** Copernicus EMS Rapid Mapping activations EMSR861 (Storm Kristin, Jan 28) and EMSR864 (Storm Leonardo, Feb 3) produced flood delineation products across 17+ Areas of Interest. These are downloadable as shapefiles/GeoTIFF from the CEMS portal. Need to download, convert to GeoJSON, and merge into a single flood extent layer.

**DATA GAP — Consequence/damage markers (CRITICAL):** This is the biggest unmapped dataset. We need geocoded points for: deaths, evacuations, infrastructure damage (A1 collapse, levee breaches), landslides, road closures, power outages. Sources: Proteção Civil (ANEPC) situation reports, Lusa news agency dispatches, municipal emergency declarations, social media geotagged posts. This requires manual curation — there is no API for this.

**DATA GAP — Landslide polygons:** Post-wildfire landscapes (summer 2025 fires stripped vegetation from central/northern Portugal) created landslide-prone slopes. The interaction between wildfire scars and flood-triggered landslides is a key part of the story. Sources: Copernicus EMS landslide delineation (may be included in EMSR864), LNEG (Laboratório Nacional de Energia e Geologia) landslide inventory if updated, or manual mapping from news/aerial imagery.

**DATA GAP — Geocoded photos and video:** Photos with location metadata from: (a) news agencies (Lusa, AFP, Getty — editorial use licensing required), (b) Proteção Civil social media posts, (c) citizen submissions (if a contribution mechanism is built), (d) municipal câmara social media. Each photo needs: coordinates, timestamp, source attribution, caption. This is a manual curation task.

### Chapter 7: The Full Picture (CLIMAX)

```
Camera: center [-8.2, 39.5], zoom 7, pitch 20, bearing 0
Animation: flyTo (2000ms, pulling back from Chapter 6 close-ups)
Layers:
  - basins-fill: opacity 0.6 (precondition index at peak, Jan 31)
  - flood-extent-polygons: opacity 0.5 (all CEMS extent data)
  - consequence-markers: opacity 0.8 (all events)
  - precipitation-accumulation: opacity 0.3 (faint background context)
Content:
  Title: "A Cadeia Causal"
  Text: "Solo saturado. Chuva intensa. Rios que ultrapassaram os limites.
         E por baixo de tudo, incêndios do verão anterior que tinham
         arrancado a vegetação que segurava as encostas.
         Cada peça sozinha era gerível. Juntas, criaram uma catástrofe."
Alignment: fully (centered, dramatic)
```

Design notes: This is the Act 2 → Act 3 boundary. The climax. All causal layers visible simultaneously — but with careful opacity management (max 3 at full visibility). The causal chain diagram overlaid on the map connects the pieces. The wildfire-flood connection is the unexpected insight that elevates this from "flood map" to "territorial risk analysis."

**DATA GAP — Wildfire scars:** Summer 2025 burn area perimeters. Source: Copernicus EMS fire products, ICNF (Instituto da Conservação da Natureza e das Florestas) burn area data, or Sentinel-2 derived burn severity maps (dNBR). Needed to show spatial correlation between 2025 burn areas and 2026 landslide/flood severity.

### Chapter 8: What We Can Learn (Act 3)

```
Camera: center [-8.3, 39.5], zoom 6.5, pitch 10, bearing 0
Animation: flyTo (1500ms, returning to near-overview)
Layers:
  - basins-fill: opacity 0.5 (precondition index methodology — clean single layer)
  - all other layers: opacity 0 (stripped back for resolution)
Content:
  Title: "O Que os Dados Já Sabiam"
  Text: "O índice de pré-condição de cheia combina três sinais: humidade
         do solo, precipitação prevista, e caudal nos rios. Duas semanas
         antes de Kristin, este índice mostrava grande parte de Portugal
         centro e sul em condições de risco elevado.
         Portugal não tem um sistema nacional de previsão de cheias.
         O SVARH observa, mas não prevê. O EFAS europeu tem capacidade
         degradada para rios portugueses regulados por barragens.
         Uma plataforma aberta, baseada em dados públicos, poderia
         ter dado mais tempo para preparar."
Alignment: left
```

Design notes: Simplification. Strip back to one layer — the precondition index — and explain how it works. This is the bridge from retrospective story to future tool. The methodology link (Mode 3) lives here.

### Chapter 9: Explore (Free Navigation)

```
Camera: user's geolocation (if granted), otherwise national zoom
Animation: map.scrollZoom.enable(), map.dragPan.enable() — liberation moment
Layers:
  - all layers available as toggles in a layer panel
Content:
  Title: "Explorar os Dados"
  Text: "Os dados por detrás desta história são públicos e abertos.
         Explore o mapa, clique nas bacias hidrográficas, veja os dados
         para a sua zona."
  CTA buttons:
    - "Ver a minha zona" (geolocation trigger)
    - "Metodologia" (link to /methodology)
    - "Partilhar" (share URL)
Alignment: fully
```

Design notes: This chapter IS the transition to Mode 1/2 of the future platform. When the user clicks "Explore the map," they're now in the same interface that will eventually be the real-time monitoring dashboard. The scroll narrative was onboarding for the platform.

---

## 5. Visual Design System

Based on civic-map-ux and geo-storytelling skill defaults, adapted for the water/flood domain.

### Color Palette

**Basemap:** Dark navy (#0a212e) — CARTO Dark Matter as base, providing functional contrast for data layers.

**Primary data ramp (precondition risk):**

| Value | Color | Meaning |
|-------|-------|---------|
| 0.0–0.2 | #2166ac (deep blue) | Low risk — soil dry, low discharge |
| 0.2–0.4 | #67a9cf (mid blue) | Moderate — soil moistening |
| 0.4–0.6 | #f7f7f7 (neutral) | Elevated — attention warranted |
| 0.6–0.8 | #ef8a62 (warm orange) | High — significant preconditions met |
| 0.8–1.0 | #b2182b (deep red) | Critical — flooding likely with additional rain |

**Flood extent:** #e74c3c at 60–80% opacity over terrain.

**Consequence markers:** Categorical by type:

| Event type | Symbol | Color |
|-----------|--------|-------|
| Death | ● | #e74c3c |
| Evacuation | ▲ | #F7991F |
| Infrastructure damage | ■ | #8e44ad |
| Landslide | ◆ | #795548 |
| Road closure | — | #e74c3c (line) |

### Typography

- **Hero/titles:** Georgia (serif), 45px, weight 300, letter-spacing 2px, #ffffff
- **Chapter titles:** Georgia, 28px, weight 300, letter-spacing 1px, #ffffff
- **Body text:** Inter (or system sans-serif), 14–15px, weight 400, line-height 1.6, #a0afb8
- **Data labels:** Inter, 11px, weight 500, #ffffff at 80% opacity
- **Source attribution:** Inter, 11px, weight 300, #607080

### Panels

Glassmorphism: `background: rgba(9, 20, 26, 0.4); backdrop-filter: blur(16px); border: 2px solid #0f2b3b; border-radius: 4px;`

Chapter text cards: max-width 420px on desktop. Full-width with bottom padding on mobile.

### Animation Defaults

- Camera transitions: 1500–2500ms, cubic-bezier(0.445, 0.05, 0.55, 0.95)
- Layer fade: 400ms
- Hover states: 300ms
- Scroll chapter trigger: IntersectionObserver at 50% threshold
- Intro screen: 150vh height
- Chapter spacing: 50vh bottom padding

---

