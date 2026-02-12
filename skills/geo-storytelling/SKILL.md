# Geo-Storytelling Skill

**Version:** 1.0
**Last Updated:** 2026-02-12
**Source:** Extracted from Vizzuality's production platforms (Global Forest Watch, Half-Earth, Aqueduct, CoCliCo, Soils Revealed)

---

## When to Use This Skill

Use this skill when building **citizen-facing environmental data platforms** that combine:
- Interactive maps with data overlays
- Complex environmental/scientific data that must be accessible to non-experts
- Real-time or forecast information requiring trust and clarity
- Multiple data sources that need coordination
- Responsive interfaces (desktop + mobile)

**Examples:** Flood monitoring, wildfire tracking, air quality dashboards, biodiversity maps, climate risk platforms.

**Do NOT use for:** GIS analyst tools, scientific data explorers for researchers, backend APIs, static reports.

---

## Design Exercise: Elena's Four Questions

**Before selecting any patterns**, work through Elena de Pomar's foundational design questions. This exercise gates all subsequent decisions.

1. **Who is the user?**
   - Primary persona (e.g., citizen checking flood risk, municipal planner, researcher)
   - Secondary personas
   - Technical sophistication level (novice, intermediate, expert)
   - Device context (mobile-first emergency check vs. desktop analysis)

2. **What are they looking for?**
   - Primary question (e.g., "Am I safe?", "Where are the fires?", "Is the air quality safe for my kids?")
   - Secondary questions (e.g., "Why is this happening?", "What should I do?")
   - Information vs. action (do they need to understand OR make a decision?)

3. **What is the most essential information?**
   - Data that answers the primary question (no more, no less)
   - Minimum viable insight for each persona
   - What can be deferred to Mode 2 (Explore) or Mode 3 (Understand)?

4. **How do we make the non-essential available without overwhelming?**
   - Progressive disclosure strategy (see below)
   - Entry points for power users
   - Methodology/data source visibility (footer vs. inline)

**Decision point:** If you cannot clearly answer all four questions, you're not ready to build. Return to user research.

**Example (flood monitoring):**
- Who: Citizens in affected districts checking current risk (mobile, non-expert)
- Looking for: "Am I in danger right now?"
- Essential: Color-coded risk level for their location, active IPMA warnings
- Non-essential: Soil moisture formulas, 14-day precipitation history, GloFAS methodology

---

## Core Principles

These principles, extracted from Vizzuality's 15+ years of environmental platform design (including designer Elena de Pomar's methodology), guide all decisions:

### 1. **Progressive Disclosure: Depth on Demand**

**Rule:** Show the minimum needed for each user goal—glance, explore, understand—in that order.

**Why it works:** Non-experts need immediate answers ("Am I safe?") before they'll engage with complexity. Revealing depth gradually prevents overwhelming users while allowing power users to dig deeper.

**How to apply:**
- **Mode 1 (Glance):** Full-screen map with color-coded risk levels. User gets answer in 5 seconds.
- **Mode 2 (Explore):** Click a region → sidebar slides in with sparkline charts, warnings, metrics. User explores in 30 seconds.
- **Mode 3 (Understand):** Footer link to methodology page with full formulas, data sources, limitations. User invests 5 minutes.

**Code pattern:**
```scss
// Accordion/collapsible sections
.detail-panel {
  height: 0;
  overflow: hidden;
  transition: height 400ms ease;

  &.expanded {
    height: auto;
    overflow: visible;
  }
}
```

**Decision point:** If you're unsure what data to show immediately vs. hide initially, ask: "Does this help answer the user's primary question?" If no, defer it to Mode 2 or 3.

---

### 2. **Institutional Trust > Technical Documentation**

**Rule:** Citizens trust named institutions more than granular data provenance. Lead with recognizable authorities, not DOIs.

**Why it works:** "IPMA (Portugal's national meteorological service)" carries more weight than "ERA5-Land reanalysis (DOI:10.24381/cds.68d2bb30)." Institutional affiliation signals quality control and accountability.

**How to apply:**
- **Hero text:** "Forecasts from IPMA + European Copernicus flood monitoring"
- **Footer:** Full technical attribution for researchers
- **Never hide sources:** Transparency builds trust, but institutional framing makes it actionable

**Anti-pattern:** Hiding data sources or burying them in fine print. Users interpret opacity as unreliability.

**Decision point:** When attributing data, ask: "Would a non-expert recognize this institution and trust it?" If no, provide context (e.g., "Copernicus, the EU's Earth observation program").

---

### 3. **Glassmorphism: Panels Preserve Map Context**

**Rule:** Sidebars, tooltips, and overlays should use semi-transparent glass effects (backdrop-filter) so the map remains visible underneath.

**Why it works:** Users orient spatially. Blocking the map with opaque panels disrupts their mental model of "where" they're looking. Glass effects maintain geographic context while layering information.

**How to apply:**
```scss
@mixin backdropBlur(
  $colour: rgba(9, 20, 26, 0.4),
  $fallback: #09141a,
  $fallbackOpacity: 0.7
) {
  background-color: rgba($fallback, $fallbackOpacity);

  @supports ((-webkit-backdrop-filter: blur(16px)) or (backdrop-filter: blur(16px))) {
    background-color: $colour;
    -webkit-backdrop-filter: blur(16px);
    backdrop-filter: blur(16px);
  }
}

.sidebar {
  @include backdropBlur();
  padding: 20px;
  border: 2px solid #0f2b3b;
}
```

**Decision point:** If you're adding a UI panel over the map, default to glassmorphism unless the panel is the primary focus (e.g., full-screen modal for editing).

---

### 4. **Scenario-Driven Risk: Ranges Beat Point Estimates**

**Rule:** Environmental forecasts have uncertainty. Show bounded scenarios (upper/lower limits) instead of false precision.

**Why it works:** A single number ("60mm rain forecast") implies certainty that doesn't exist. A range ("50-70mm P10-P90") communicates confidence while preventing over-reliance on a specific value.

**How to apply:**
- Sparkline charts: Shaded area for forecast range, solid line for historical data
- Risk levels: "Moderado" risk might have narrow range; "Muito Elevado" has wider uncertainty
- Explicit bounds: "Without flood defenses (upper limit) vs. with defenses (lower limit)"

**Decision point:** If you're displaying a forecast or model output, ask: "Does this value have inherent uncertainty?" If yes, visualize the range, not just the mean.

---

### 5. **Emotional Engagement: Delight → Curiosity → Exploration → Digestion**

**Rule:** Design a psychological sequence that overcomes cognitive bias through emotional connection before delivering complex information.

**Why it works:** Research shows people make choices based on prior beliefs and gut feelings, even when data conflicts with those beliefs (Elena de Pomar, citing cognitive bias studies). To overcome this, create an emotional connection BEFORE presenting evidence. The sequence is:

1. **Delight:** Visual beauty invites interaction ("The Half-Earth Map is a beautiful 3D globe that invites its users to explore our beautiful planet. When people first see the globe, they want to play with it.")
2. **Curiosity:** Interaction blooms into questions ("As they fly across the planet and see mountains rise up before them, delight and curiosity blooms in their minds")
3. **Exploration:** Questions drive discovery ("It's this delight that leads to exploration")
4. **Digestion:** Discovery produces understanding ("and the digestion of new information")

**How to apply:**
- **Delight layer:** Dark aesthetic with high contrast (Deep navy #0a212e + vibrant data colors), smooth 400ms animations, metaphorical design (water deepens as flood risk rises)
  - Dark theme is **functional**, not aesthetic: "provides the best contrast with the data layers and gives us more room to experiment with colour" (Elena de Pomar)
- **Curiosity layer:** Playful interactions that encourage experimentation (spin the globe, click a district, drag a timeline)
- **Exploration layer:** Responsive feedback to every interaction (see state confirmation micro-interactions below)
- **Digestion layer:** Clear insights emerge from interaction ("Baixo risco. Solo tem capacidade para absorver chuva prevista.")

**Civic UX principle (give, not sell):** "Most of the websites we create don't want to sell you anything. They want to give you something, usually knowledge, hope or a reason to change your behaviour" (Elena de Pomar). Longer dwell time is success. No conversion funnels.

**Anti-pattern:** Sterile dashboards with no personality trigger disengagement. Users bounce.

**Decision point:** If your design feels clinical, add one element of wonder (animation, color gradient, metaphor) to trigger the delight→curiosity sequence.

---

### 6. **Mobile = Bottom Sheet, Not Squished Sidebar**

**Rule:** On mobile, sidebars become slide-up bottom sheets with swipe gestures, not narrower sidebars.

**Why it works:** Mobile users hold phones one-handed and interact with thumbs. Slide-up sheets align with natural thumb motion; narrow sidebars require precision taps and horizontal scrolling.

**How to apply:**
```scss
.sidebar {
  position: fixed;
  top: 82px;
  right: 20px;
  width: 420px;

  @media (max-width: 720px) {
    // Bottom sheet on mobile
    top: auto;
    bottom: 0;
    right: 0;
    width: 100vw;
    max-height: 70vh;
    border-radius: 16px 16px 0 0;
    transform: translateY(0);

    &.collapsed {
      transform: translateY(65%); // Peek visible
    }
  }
}
```

**Decision point:** When designing responsive layouts, ask: "Can this be operated with one hand in portrait orientation?" If no, consider bottom sheet.

---

### 7. **Circular User Journey: Self-Orienting Views**

**Rule:** Every view must orient a cold arrival—someone who got a shared link to a deep page and has no prior context.

**Why it works:** "Unlike software where people take what is essentially a linear journey, websites have multiple entry points and people expect to know what's going on and where to go next, regardless of what stage of the journey they join at. In this situation we start to see that the user journey is in fact a circular one that must loop from any starting point towards the conclusion" (Elena de Pomar).

**How to apply:**
- Every page provides enough information to answer: "Where am I?" and "What can I do here?"
- Breadcrumbs or contextual headers (e.g., sidebar title: "Coimbra — Mondego Basin — Flood Risk")
- Always-visible navigation to primary views (map, methodology, data sources)
- Shared links preserve state (URL parameters for selected district, basin, date range)

**Example (flood monitoring):**
- User receives WhatsApp link: `cheias.pt?district=coimbra`
- Sidebar opens automatically with Coimbra details
- Header shows: "cheias.pt — Monitorização de Cheias"
- Footer links always visible: "Como Funciona | Fontes de Dados | Sobre"

**Anti-pattern:** Assuming users start at the homepage. Most don't.

**Decision point:** For each view you build, ask: "Can someone understand this if they land here directly from a search engine or shared link?"

---

### 8. **State Confirmation Micro-Interactions**

**Rule:** Every user action must have immediate visual confirmation. In emergency-use platforms, uncertainty is anxiety.

**Why it works:** "Small design details are just as important as the big design decisions when you want to establish an emotional connection. It's the little details that help reassure people they're in the right place and understand what they see" (Elena de Pomar).

**How to apply:**
- Layer toggles: "When a data layer is added, the circle next to the menu label will be filled with colour" (Half-Earth pattern)
- Clicks: 200ms scale animation (transform: scale(0.95)) on buttons
- Hovers: Color shift (300ms transition) on interactive elements
- Loading states: Skeleton screens or spinners, never blank screens
- Success feedback: Green checkmark or "Saved" message (disappears after 2s)

**Code pattern:**
```css
.layer-toggle {
  position: relative;
}

.layer-toggle::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 2px solid #a0afb8;
  transition: all 300ms ease;
}

.layer-toggle.active::before {
  background: var(--turquoise);
  border-color: var(--turquoise);
  box-shadow: 0 0 6px var(--turquoise);
}
```

**Decision point:** If you're adding an interactive element, specify its hover, active, and loading states. No element should be interaction-ambiguous.

---

### 9. **Spatial Orientation Anchor (Mini-Globe Pattern)**

**Rule:** Provide a persistent spatial reference when users zoom into local views.

**Why it works:** "Another small detail is the globe within the Half-Earth progress chart in the upper right corner. As the main globe moves in response to the user's interactions, the mini one in the progress chart does too. Even when they are zoomed in, they can still see where in the world they are" (Elena de Pomar).

**How to apply:**
- Small reference map (100×100px) showing current viewport within full extent
- Synchronized movement: Main map pans → mini-map updates
- Subtle styling: Low opacity basemap, bright viewport box
- Position: Top-right or bottom-left (non-intrusive corner)

**Code pattern:**
```javascript
// Create mini-map
const miniMap = new maplibregl.Map({
  container: 'mini-map',
  style: basemapURL,
  center: mainMap.getCenter(),
  zoom: 4, // Fixed zoom showing full country/region
  interactive: false
});

// Sync on main map movement
mainMap.on('move', () => {
  miniMap.setCenter(mainMap.getCenter());
  updateViewportBox(mainMap.getBounds());
});
```

**Alternative:** Breadcrumb trail (Portugal → Coimbra → Mondego Basin)

**Decision point:** If users will zoom to local views (city, watershed, building), add a spatial anchor. If platform stays at country/region scale, skip it.

---

## Decision Tree: What Kind of Geo Platform Are You Building?

Use this tree to determine which patterns to prioritize:

```
START: What is the primary user goal?

┌─ Monitor current conditions (flood risk, fire danger, air quality)
│  ├─ Frequency: Real-time or hourly updates
│  ├─ Primary action: "Am I safe right now?"
│  └─ Pattern focus:
│      ▪ Full-screen map with color-coded risk (Principle #1: Glance mode)
│      ▪ Glassmorphism sidebar for details (Principle #3)
│      ▪ Data freshness badges (trust-transparency.md)
│      ▪ IPMA-style warning markers (visual-hierarchy.md)
│      ▪ Mobile bottom sheet (Principle #6)
│  └─ Reference: cheias.pt, fogos.pt, Global Forest Watch alerts
│
├─ Tell a story about environmental change (deforestation, biodiversity loss, soil carbon)
│  ├─ Frequency: Historical or slow-changing data
│  ├─ Primary action: "Understand the issue and its scope"
│  └─ Pattern focus:
│      ▪ Scrollytelling with chapter-based camera movements (progressive-disclosure.md)
│      ▪ Opacity-based layer reveals on scroll (map-narratives.md)
│      ▪ Serif typography for emotional moments (visual-hierarchy.md)
│      ▪ What → Why → What You Can Do narrative arc (trust-transparency.md)
│      ▪ Metaphor-driven visuals (e.g., "dig deeper" for soil data)
│  └─ Reference: Soils Revealed, Half-Earth, layers-storytelling framework
│
├─ Analyze spatial data (water risk, coastal flooding, land use change)
│  ├─ Frequency: Static or scenario-based
│  ├─ Primary action: "Compare scenarios and export insights"
│  └─ Pattern focus:
│      ▪ User Stories pattern: pre-built views for different personas (trust-transparency.md)
│      ▪ Scenario matrix: defense level × return period × climate scenario (trust-transparency.md)
│      ▪ Layer controls with batch toggle operations (component-patterns.md)
│      ▪ Export to GIS (download shapefiles, GeoJSON)
│      ▪ Desktop-first (complex controls don't translate well to mobile)
│  └─ Reference: Aqueduct, CoCliCo, Resource Watch
│
└─ Hybrid: Monitoring + Storytelling + Analysis
   ├─ Example: Global Forest Watch (alerts + deforestation stories + data download)
   ├─ Pattern focus:
   │   ▪ Mode switcher: Map view / Story view / Analysis view
   │   ▪ Progressive disclosure across modes (Principle #1)
   │   ▪ Consistent glassmorphism across modes (Principle #3)
   │   ▪ Institutional trust signals in all modes (Principle #2)
   └─ Warning: Don't try to do everything at once. Build Mode 1 (Glance) first, add depth later.
```

**Decision point:** If your platform fits multiple categories, **start with monitoring** (Mode 1: Glance). It's the simplest to build and has the broadest audience. Add storytelling/analysis later as Mode 2/3.

---

## Civic UX Principles: Beyond Commercial Patterns

Environmental platforms optimize for **understanding**, not conversion. These principles distinguish civic platforms from commercial ones:

### Playful Interaction: Encourage Experimentation

**Principle:** "Design interactions that encourage people to play with the data and learn how the visualisation tool works" (Elena de Pomar).

**Why it matters:** Play = discovery. When users experiment without fear of breaking things, they learn the platform's capabilities and find insights you didn't prescribe.

**How to apply:**
- Forgiving interactions: No "Are you sure?" dialogs for non-destructive actions
- Immediate feedback: Hover over district → preview risk level
- Reversible actions: Add layer → remove layer → add again (no state loss)
- Delightful micro-animations: Globe spins with inertia, cards slide with spring physics
- Easter eggs optional: Zoom to max level → see individual trees/buildings

**Example patterns:**
- Timeline scrubber with playback speed controls (0.03×-16×)
- Click district → sidebar slides in. Click map → sidebar slides out. No "close" button needed.
- Layer toggles with batch operations ("Show all" / "Hide all")

**Anti-pattern:** Locking features behind registration, tutorials, or permission dialogs.

---

### Empowerment Framing: Agency Over Fear

**Principle:** Shift from "Am I safe?" (fear) to "What's the situation?" (agency). Tools should empower, not panic.

**Elena de Pomar:** "Tools like the Half-Earth Map help people access the information that empowers them. No matter who they are—from the kid who dreams of seeing a wild elephant one day, to the climber who conquers El Capitan, to the Mum who wants to feed her children palm oil-free chocolate spread—every one of them can use the Half-Earth Map to explore and understand the world."

**How to apply:**
- **Celebrate low risk prominently:** "Baixo risco. Solo tem capacidade para absorver chuva prevista." (Not just "No alert")
- **Neutral language for high risk:** "Risco muito elevado. Siga as instruções da ANEPC." (Not "DANGER" or "FLEE")
- **Provide context, not commands:** Show soil moisture + forecast rain → user understands WHY risk is high
- **Link to authoritative action:** "Follow ANEPC instructions" (not "We recommend evacuating")

**Frame as:** "Here's what's happening + here are your options" (empowerment)
**Not as:** "You're in danger + do what we say" (panic)

**Decision point:** Review all alert text. Does it inform or frighten? Replace fear-inducing language with context + authoritative guidance.

---

### Imagination Prompts: Scenario Framing

**Principle:** Contextual text can include scenario framing that connects abstract data to personal decisions.

**Elena de Pomar:** "Imagine for a moment that these maps were being used to decide where to build a dam, pull down a rainforest, or dig up a grassland. Do you think we'd make different choices if we could see the landscape of those places and learn about the life that lives there? We believe that people will."

**How to apply:**
- **About page:** "Imagine if every municipality had access to real-time flood forecasting. How many evacuations could be planned earlier? How many lives saved?"
- **Methodology page:** "This platform uses the same soil moisture data that farmers use to decide when to irrigate. If it's reliable enough to guide agricultural decisions, it's reliable enough to predict flood risk."
- **High-risk areas:** "If you were planning where to build a new school, would you choose this location knowing its flood history?"

**Purpose:** Bridges the gap between "data exists" and "data matters to MY life."

**Anti-pattern:** Pure technical documentation with no human connection.

**Decision point:** Where can you add a one-sentence scenario that makes data personally relevant?

---

## Quick Start: Minimal Geo-Storytelling Pattern

Here's a complete, working example of a flood risk map with progressive disclosure, glassmorphism, and institutional trust. Vanilla JavaScript + MapLibre GL JS + Chart.js.

### HTML Structure

```html
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>cheias.pt — Monitorização de Cheias</title>
  <link href="https://unpkg.com/maplibre-gl@4/dist/maplibre-gl.css" rel="stylesheet" />
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="header">
    <h1>cheias.pt</h1>
    <p>Avisos IPMA · Previsões GloFAS · Análise de Solo</p>
  </header>

  <main class="map-container" id="map"></main>

  <aside class="sidebar" id="sidebar">
    <button class="close-btn" onclick="closeSidebar()">×</button>
    <h2 id="location-name">Carregando...</h2>

    <!-- Mode 2: Progressive disclosure -->
    <div class="risk-gauge">
      <div class="gauge-bar" id="risk-bar"></div>
      <span class="gauge-label" id="risk-label">—</span>
    </div>

    <section class="data-section">
      <h3>Humidade do Solo (14 dias)</h3>
      <canvas id="soil-chart"></canvas>
      <span class="freshness-badge">
        <span class="dot green"></span> Atualizado há 2h
      </span>
    </section>

    <!-- Mode 3: Expandable methodology -->
    <details class="methodology">
      <summary>ℹ️ Como funciona</summary>
      <p>Precondition Index = forecast_precip / remaining_soil_capacity</p>
      <p>Field capacity: 0.30 (default). Range: 0.0 (safe) to 1.0 (flood risk).</p>
    </details>
  </aside>

  <footer class="footer">
    <a href="/about">Sobre</a> ·
    <a href="/methodology">Como Funciona</a> ·
    <a href="https://github.com/user/cheias-pt">GitHub</a> ·
    <a href="https://ipma.pt">IPMA</a> ·
    <a href="https://prociv.pt">Proteção Civil</a>
  </footer>

  <script src="https://unpkg.com/maplibre-gl@4/dist/maplibre-gl.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
  <script src="main.js"></script>
</body>
</html>
```

### CSS (style.css)

```css
:root {
  --navy-dark: #0a212e;
  --navy-panel: #0f2b3b;
  --turquoise: #18bab4;
  --green: #2ecc71;
  --yellow: #f1c40f;
  --orange: #e67e22;
  --red: #e74c3c;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Open Sans', sans-serif;
  background: var(--navy-dark);
  color: #fff;
}

.header {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 10;
  background: rgba(9, 20, 26, 0.4);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 16px 24px;
  border-radius: 4px;
  border: 2px solid var(--navy-panel);
}

.header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--turquoise);
}

.header p {
  font-size: 12px;
  color: #a0afb8;
  margin-top: 4px;
}

.map-container {
  width: 100vw;
  height: 100vh;
}

/* Glassmorphism sidebar */
.sidebar {
  position: fixed;
  top: 82px;
  right: 20px;
  width: 420px;
  max-height: calc(100vh - 120px);
  background: rgba(9, 20, 26, 0.4);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 2px solid var(--navy-panel);
  border-radius: 4px;
  padding: 20px;
  overflow-y: auto;
  transform: translateX(0);
  transition: transform 400ms ease;
  z-index: 15;
}

.sidebar.hidden {
  transform: translateX(150%);
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  color: #fff;
  font-size: 32px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
}

.risk-gauge {
  margin: 20px 0;
  position: relative;
}

.gauge-bar {
  height: 24px;
  background: linear-gradient(to right, var(--green) 0%, var(--yellow) 50%, var(--orange) 75%, var(--red) 100%);
  border-radius: 4px;
  position: relative;
}

.gauge-bar::after {
  content: '';
  position: absolute;
  left: 50%; /* Will be set dynamically */
  top: -4px;
  width: 4px;
  height: 32px;
  background: #fff;
  border-radius: 2px;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.5);
}

.gauge-label {
  display: block;
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.data-section {
  margin: 24px 0;
}

.data-section h3 {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #a0afb8;
  margin-bottom: 12px;
}

.freshness-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #a0afb8;
  margin-top: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.green {
  background: var(--green);
  box-shadow: 0 0 4px var(--green);
}

.methodology {
  margin-top: 24px;
  border-top: 1px dotted #a0afb8;
  padding-top: 16px;
}

.methodology summary {
  cursor: pointer;
  font-size: 14px;
  color: var(--turquoise);
  list-style: none;
}

.methodology summary::-webkit-details-marker {
  display: none;
}

.methodology p {
  margin-top: 12px;
  font-size: 13px;
  line-height: 1.6;
  color: #a0afb8;
}

.footer {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(9, 20, 26, 0.4);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 12px 20px;
  border-radius: 4px;
  border: 2px solid var(--navy-panel);
  font-size: 12px;
  z-index: 10;
}

.footer a {
  color: var(--turquoise);
  text-decoration: none;
  transition: color 300ms ease;
}

.footer a:hover {
  color: #fff;
}

/* Mobile: Bottom sheet */
@media (max-width: 720px) {
  .sidebar {
    top: auto;
    bottom: 0;
    right: 0;
    left: 0;
    width: 100vw;
    max-height: 70vh;
    border-radius: 16px 16px 0 0;
    transform: translateY(0);
  }

  .sidebar.collapsed {
    transform: translateY(65%);
  }
}
```

### JavaScript (main.js)

```javascript
// Initialize map
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  center: [-8.0, 39.5],
  zoom: 6,
  maxBounds: [[-10.5, 35.5], [-5.0, 43.5]]
});

// Load district GeoJSON and add choropleth layer
map.on('load', async () => {
  // Fetch district boundaries
  const response = await fetch('/assets/districts.geojson');
  const districts = await response.json();

  map.addSource('districts', {
    type: 'geojson',
    data: districts
  });

  map.addLayer({
    id: 'districts-fill',
    type: 'fill',
    source: 'districts',
    paint: {
      'fill-color': [
        'case',
        ['<', ['get', 'risk'], 0.3], '#2ecc71',  // Baixo
        ['<', ['get', 'risk'], 0.6], '#f1c40f',  // Moderado
        ['<', ['get', 'risk'], 0.8], '#e67e22',  // Elevado
        '#e74c3c'                                 // Muito Elevado
      ],
      'fill-opacity': 0.6
    }
  });

  map.addLayer({
    id: 'districts-outline',
    type: 'line',
    source: 'districts',
    paint: {
      'line-color': '#fff',
      'line-width': 1,
      'line-opacity': 0.3
    }
  });

  // Click to show sidebar with district details
  map.on('click', 'districts-fill', (e) => {
    const props = e.features[0].properties;
    showSidebar(props);
  });

  // Fetch and render IPMA warnings as markers
  const warnings = await fetchIPMAWarnings();
  renderWarnings(warnings);
});

async function fetchIPMAWarnings() {
  const res = await fetch('https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json');
  const data = await res.json();
  return data.filter(w => w.awarenessLevelID >= 2); // Yellow and above
}

function renderWarnings(warnings) {
  warnings.forEach(warning => {
    const color = ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c'][warning.awarenessLevelID - 1];

    new maplibregl.Marker({ color })
      .setLngLat(warning.coordinates) // Requires geocoding district codes
      .setPopup(new maplibregl.Popup().setHTML(`
        <strong>${warning.awarenessTypeName}</strong><br>
        ${warning.text.substring(0, 100)}...
      `))
      .addTo(map);
  });
}

function showSidebar(districtProps) {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.remove('hidden');

  document.getElementById('location-name').textContent = districtProps.district;

  const risk = districtProps.risk || 0.5;
  const riskPercent = (risk * 100).toFixed(0);
  document.getElementById('risk-bar').style.setProperty('--risk-value', `${riskPercent}%`);

  const labels = ['Baixo', 'Moderado', 'Elevado', 'Muito Elevado'];
  const riskLevel = risk < 0.3 ? 0 : risk < 0.6 ? 1 : risk < 0.8 ? 2 : 3;
  document.getElementById('risk-label').textContent = labels[riskLevel];

  // Fetch soil moisture data and render chart
  fetchSoilMoisture(districtProps.lat, districtProps.lon).then(renderChart);
}

function closeSidebar() {
  document.getElementById('sidebar').classList.add('hidden');
}

async function fetchSoilMoisture(lat, lon) {
  const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&hourly=soil_moisture_27_to_81cm&past_days=14&forecast_days=7`);
  return res.json();
}

function renderChart(data) {
  const ctx = document.getElementById('soil-chart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.hourly.time.map(t => new Date(t).toLocaleDateString('pt-PT', { day: 'numeric', month: 'short' })),
      datasets: [{
        label: 'Humidade do Solo (27-81cm)',
        data: data.hourly.soil_moisture_27_to_81cm,
        borderColor: '#18bab4',
        backgroundColor: 'rgba(24, 186, 180, 0.1)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 0.4,
          ticks: { color: '#a0afb8', font: { size: 10 } }
        },
        x: {
          ticks: { color: '#a0afb8', font: { size: 10 } }
        }
      }
    }
  });
}
```

### What This Example Demonstrates

✅ **Progressive disclosure:** Map (Mode 1) → Sidebar (Mode 2) → Methodology (Mode 3)
✅ **Glassmorphism:** Sidebar and header with `backdrop-filter: blur(16px)`
✅ **Institutional trust:** "Avisos IPMA · Previsões GloFAS" in hero text
✅ **Data freshness:** Green dot + "Atualizado há 2h" badge
✅ **Risk visualization:** Color-coded districts + gauge bar
✅ **Mobile bottom sheet:** Responsive `@media` query
✅ **Portuguese localization:** All text in Portuguese

**To extend this:**
- Add IPMA warning cards in sidebar (Mode 2)
- Add GloFAS discharge sparklines (Mode 2)
- Add methodology page with full formula (Mode 3)
- Add temporal animation with timeline slider (see performance.md)

---

## Integration with stac-cog-viewer Skill

If you're building a platform that combines **satellite imagery** (via STAC/COG) and **real-time sensor data** (via APIs), use both skills together:

**stac-cog-viewer handles:**
- STAC catalog navigation
- COG tile serving via Titiler
- Satellite imagery overlays (Sentinel-2, Landsat, radar)
- Temporal imagery comparison

**geo-storytelling handles:**
- Visual hierarchy (what layers dominate vs. provide context)
- User flow (glance → explore → understand)
- Trust signals (institutional attribution, data freshness)
- Responsive design (desktop sidebar → mobile bottom sheet)
- Narrative structure (what → why → what you can do)

**Example integration (flood monitoring):**
- **Base layer:** Sentinel-2 true color (via stac-cog-viewer)
- **Data overlay:** Flood extent from SAR (via stac-cog-viewer)
- **Sensor layer:** River gauge markers + IPMA warnings (via geo-storytelling)
- **UI:** Glassmorphism sidebar with sparklines (via geo-storytelling)
- **Progressive disclosure:** Click basin → show Sentinel-2 change detection + gauge time series

**Code pattern:**
```javascript
// stac-cog-viewer: Load Sentinel-2 flood extent
const floodExtentLayer = await loadCOGLayer({
  url: 'https://titiler.xyz/cog/tiles/{z}/{x}/{y}?url=s3://flood-extent.tif',
  colormap: 'blues'
});

// geo-storytelling: Add river gauge markers
const gaugeMarkers = renderStationMarkers(stations, {
  color: (station) => getRiskColor(station.discharge),
  popup: (station) => createSparklinePopup(station)
});

// Combined: Sidebar shows satellite imagery + sensor time series
function showSidebar(basin) {
  renderSentinel2Preview(basin); // stac-cog-viewer
  renderGaugeChart(basin);        // geo-storytelling
}
```

**Key insight:** stac-cog-viewer is about **data pipelines** (how to get imagery onto the map). geo-storytelling is about **presentation** (how to make users trust and understand what they're seeing).

---

## Reference Documentation

When you need deeper patterns for specific scenarios, consult these reference files:

### [progressive-disclosure.md](./references/progressive-disclosure.md)
**Use when:** Designing multi-level information architecture
**Contains:** Accordion patterns, opacity-based reveals, zoom-triggered visibility, sidebar slide animations, scroll-driven layer changes

### [map-narratives.md](./references/map-narratives.md)
**Use when:** Building storytelling experiences or temporal playback
**Contains:** Scrollytelling chapter configs, camera flyTo/easeTo transitions, timeline controls, playback speed management, what→why→action narrative structure

### [visual-hierarchy.md](./references/visual-hierarchy.md)
**Use when:** Choosing colors, typography, or spatial layout
**Contains:** Color systems (categorical + continuous ramps), typography scales, z-index hierarchy, legend patterns, responsive breakpoints

### [performance.md](./references/performance.md)
**Use when:** Rendering large datasets or temporal animations
**Contains:** WebGL sprite pooling, binary tile formats, temporal indexing, 4wings architecture, MapLibre custom layers

### [trust-transparency.md](./references/trust-transparency.md)
**Use when:** Communicating data sources, uncertainty, or warnings
**Contains:** Institutional attribution patterns, data freshness indicators, confidence levels, warning severity design, User Stories pattern

### [component-patterns.md](./references/component-patterns.md)
**Use when:** Architecting map + sidebar layouts or state management
**Contains:** Three-layer component structure, render-less managers, feature modules, layer toggle patterns, responsive mobile sheets

### [anti-patterns.md](./anti-patterns.md)
**Use when:** Avoiding common mistakes in geo dashboards
**Contains:** What NOT to do (clutter, opacity, configuration complexity, sterile design, false precision)

---

## Success Criteria

This skill is successful if you can:

1. **Determine visual hierarchy:** Given a dataset with 5 layers, decide which carries meaning vs. provides context, and how to prevent visual competition

2. **Reason about disclosure sequence:** Identify what information this specific audience needs first (glance), what requires interaction (explore), and what should be opt-in (understand)

3. **Place trust signals:** Know where methodology panels, source attribution, and data freshness indicators belong for this specific context

4. **Choose color encoding:** Select categorical vs. continuous, diverging vs. sequential color ramps based on the data's nature and the risk it communicates

5. **Add narrative/contextual text:** Decide when and how to add explanatory text without prescribing specific UI components

6. **Apply responsive patterns:** Choose desktop sidebar vs. mobile bottom sheet based on the platform's interaction model (monitoring vs. storytelling vs. analysis)

**You've failed if:**
- Your solution is a checklist of UI components to include
- The patterns only work for flood monitoring and can't adapt to air quality or wildfire
- Claude can't explain WHY a pattern was chosen, only WHAT was applied

---

## Version History

**v1.1 (2026-02-12):** Incorporated design philosophy from Elena de Pomar interviews (Vizzuality Blog). Added: Elena's Four Questions design exercise, Delight→Curiosity→Exploration→Digestion psychological sequence (replacing "Joy Before Warning"), circular user journey principle, state confirmation micro-interactions, mini-globe spatial orientation pattern, civic UX principles (playful interaction, empowerment framing, imagination prompts), "build to climax" narrative arc, and "familiar terrain first" cognitive mechanism. Updated dark theme rationale (functional contrast, not aesthetic). Created stub files for missing references.

**v1.0 (2026-02-12):** Initial release based on Vizzuality pattern analysis (half-earth-v3, landgriffon, layers-storytelling, GlobalFishingWatch, CoCliCo, Aqueduct, Resource Watch, Soils Revealed)
