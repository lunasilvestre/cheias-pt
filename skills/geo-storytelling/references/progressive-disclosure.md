# Progressive Disclosure Patterns

**Principle:** Reveal complexity gradually. Show the minimum needed for each user goal—glance, explore, understand—in that order.

---

## The Narrative Arc: Building to Climax

**Principle:** Progressive disclosure is not just hiding complexity—it's building a story with a climax moment.

**Elena de Pomar:** "The slow reveal that progressive disclosure provides should build into a climax where everything culminates in a life changing moment. It's the point where the data reveals to farmers which crops are most suitable for their farm's soil and climate conditions. Or it's the point where we realise that improving literacy rates among women in Ethiopia's maize producing regions would increase the impact of efforts to improve the region's resilience to climate change."

**For flood monitoring:** The climax is when a user in Coimbra sees their district at "Muito Elevado" risk, understands WHY (soil saturated + 60mm forecast rain), and knows WHAT TO DO (follow ANEPC evacuation instructions).

**Design implication:** Each mode must advance the story toward personal action. Mode 1 (threat level) → Mode 2 (evidence + context) → Mode 3 (methodology + trust). The climax is Mode 2, where understanding becomes actionable.

---

## Familiar Terrain First

**Principle:** Show recognizable geography BEFORE data layers appear. Recognition → personal connection.

**Elena de Pomar:** "It's the sight of familiar landscape features that help us connect with the data we're viewing. From the tallest mountain, to local lakes, and even individual houses, you'll see it all here."

**Why it works:** Cognitive mechanism. Users see their hometown → "this is about ME" → engagement increases. Abstract data → no emotional connection.

**How to apply:**
- Basemap loads first (terrain, streets, landmarks visible)
- Data layers fade in 300ms after basemap render
- 3D terrain optional but powerful ("mountains rise up before them")
- Local place names visible at appropriate zoom levels

**Anti-pattern:** Data-first rendering (choropleth loads, basemap blank). Users can't orient.

**Code pattern:**
```javascript
map.on('load', () => {
  // Wait for basemap to render
  setTimeout(() => {
    addDataLayer('flood-risk-choropleth', { opacity: 0 });
    fadeIn('flood-risk-choropleth', 600); // Fade in over 600ms
  }, 300);
});
```

---

## Mode 1: Glance (5 seconds)

**Goal:** Answer the primary question immediately

**Visual budget:**
- Full-screen map with recognizable terrain/basemap
- Single data layer (color-coded risk, alerts, or status) fading in
- Minimal UI chrome (logo, legend toggle)
- No text blocks

**Pattern:**
```html
<div class="map-full-screen">
  <!-- Map fills viewport -->
  <header class="logo-minimal">
    <h1>Platform Name</h1>
  </header>
  <div class="legend-overlay">
    <!-- 4-item max legend with color swatches -->
  </div>
</div>
```

**Example (flood monitoring):**
- District polygons colored green/yellow/orange/red
- IPMA warning markers (circles with awareness level color)
- That's it. No sidebar, no charts, no text.

**Anti-pattern:** Showing sidebar by default. User must orient spatially before diving into details.

---

## Mode 2: Explore (30 seconds)

**Goal:** Provide context and detail on demand

### Sidebar Slide-In Animation

**Pattern:** Click a map feature → sidebar slides from right with details

```scss
.sidebar {
  position: fixed;
  top: 82px;
  right: 20px;
  width: 420px;
  transform: translateX(0);
  transition: transform 400ms ease;
}

.sidebar.hidden {
  transform: translateX(150%);
}
```

**Trigger:** Map click, not automatic on page load

**Content hierarchy in sidebar:**
1. Location name (h2, 24px)
2. Primary metric (gauge, chart, or number)
3. Supporting sparklines (2-3 max)
4. Active warnings/alerts (if any)
5. Expandable methodology (see below)

### Accordion/Collapsible Sections

**Pattern:** Hide advanced details behind expandable sections

```scss
.detail-panel {
  height: 0;
  overflow: hidden;
  padding: 0;
  transition: height 400ms ease;
}

.detail-panel.expanded {
  height: auto;
  overflow: visible;
  padding: 20px 0;
}
```

**HTML:**
```html
<details class="methodology">
  <summary>ℹ️ Como funciona</summary>
  <p>Detailed explanation...</p>
</details>
```

**Key insight:** Use `<details>` + `<summary>` for native accessibility. Style the disclosure triangle.

### Hover Tooltips for Technical Terms

**Pattern:** Inline terms with dotted underline → tooltip on hover

```html
<span class="tooltip-term" data-tooltip="Razão entre chuva prevista e capacidade restante do solo">
  Precondition Index
</span>
```

```css
.tooltip-term {
  border-bottom: 1px dotted #a0afb8;
  cursor: help;
  position: relative;
}

.tooltip-term::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(9, 20, 26, 0.95);
  backdrop-filter: blur(16px);
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 300ms ease;
}

.tooltip-term:hover::after {
  opacity: 1;
}
```

**Anti-pattern:** Tooltips that appear on click (conflicts with mobile tap behavior). Use hover for desktop, expandable sections for mobile.

---

## Mode 3: Understand (5 minutes)

**Goal:** Provide full methodology, data sources, limitations

**Pattern:** Footer link to dedicated page (not inline)

```html
<footer>
  <a href="/about">Sobre</a> ·
  <a href="/methodology">Como Funciona</a> ·
  <a href="/data-sources">Fontes de Dados</a> ·
  <a href="https://github.com/user/platform">GitHub</a>
</footer>
```

**Methodology page structure:**
1. **Plain-language summary** (1-2 paragraphs)
2. **Visual diagram** (flowchart or formula breakdown)
3. **Technical details** (equations, thresholds, calibration)
4. **Data sources** (with DOIs, update frequencies)
5. **Limitations** (what the model does NOT account for)
6. **Contact/feedback** (link to GitHub issues or email)

**Example (Precondition Index methodology):**
```markdown
## How It Works

The Flood Precondition Index estimates how vulnerable an area is to flooding based on how saturated the soil is and how much rain is forecast.

### Formula

Precondition Index = forecast_precipitation / remaining_soil_capacity

Where:
- forecast_precipitation = Total rainfall expected in next 48 hours (mm)
- remaining_soil_capacity = (field_capacity - current_soil_moisture) × soil_depth

### Risk Levels

- < 0.3: Baixo (soil can absorb forecast rain)
- 0.3-0.6: Moderado (partial absorption)
- 0.6-0.8: Elevado (limited absorption)
- > 0.8: Muito Elevado (saturation, high runoff)

### Limitations

- Assumes uniform soil type (default field capacity: 0.30)
- Does not account for urban surfaces, topography, or dam releases
- Forecast precipitation has inherent uncertainty (show as range, not point estimate)
```

**Anti-pattern:** Putting this in the sidebar. Most users don't need it; those who do will navigate to a dedicated page.

---

## Opacity-Based Reveals

**Pattern:** Fade in secondary UI elements after map loads

```css
.secondary-ui {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 400ms ease 300ms, transform 400ms ease 300ms;
}

.secondary-ui.visible {
  opacity: 1;
  transform: translateY(0);
}
```

**JavaScript:**
```javascript
map.on('load', () => {
  setTimeout(() => {
    document.querySelector('.secondary-ui').classList.add('visible');
  }, 300);
});
```

**Use for:**
- Legend (not critical on first load)
- Attribution footer
- Tutorial hints

**Don't use for:**
- Logo/branding (always visible)
- Primary controls (zoom, geolocate)

---

## Zoom-Triggered Visibility

**Pattern:** Show different layers/details at different zoom levels

**MapLibre implementation:**
```javascript
map.addLayer({
  id: 'district-labels',
  type: 'symbol',
  source: 'districts',
  minzoom: 7,  // Only visible when zoomed in
  layout: {
    'text-field': ['get', 'name'],
    'text-size': 14
  }
});

map.addLayer({
  id: 'country-outline',
  type: 'line',
  source: 'countries',
  maxzoom: 7,  // Only visible when zoomed out
  paint: {
    'line-width': 2,
    'line-color': '#fff'
  }
});
```

**Resolution strategy (from Vizzuality):**
- Global view (z0-4): Coarse data (~110km² resolution)
- Regional view (z5-8): Medium data (~27km²)
- Local view (z9+): Fine data (1km² or station-level)

**Anti-pattern:** Showing all detail at all zoom levels. Causes visual clutter at low zoom, missing detail at high zoom.

---

## Scroll-Driven Progressive Disclosure (Storytelling)

**Pattern:** Reveal information as user scrolls (for narrative platforms)

```html
<div class="story-container">
  <section class="chapter" data-lat="40.2033" data-lon="-8.4103" data-zoom="10">
    <h2>Mondego em Alerta</h2>
    <p>Coimbra sob risco elevado de inundações...</p>
  </section>
  <section class="chapter" data-lat="38.7223" data-lon="-9.1393" data-zoom="11">
    <h2>Tejo em Vigilância</h2>
    <p>Lisboa monitoriza níveis do rio...</p>
  </section>
</div>
```

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const chapter = entry.target;
      map.flyTo({
        center: [chapter.dataset.lon, chapter.dataset.lat],
        zoom: chapter.dataset.zoom,
        pitch: 30,
        duration: 2000
      });
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('.chapter').forEach(chapter => {
  observer.observe(chapter);
});
```

**Spacing:** Each chapter needs `padding-bottom: 50vh` to create scroll trigger zone.

**Active state:**
```css
.chapter {
  opacity: 0.6;
  transition: opacity 400ms ease;
}

.chapter.active {
  opacity: 1;
}
```

---

## Summary: When to Use Each Mode

| Mode | Trigger | Duration | Content | Pattern |
|------|---------|----------|---------|---------|
| **Glance** | Page load | 5 sec | Map + color-coded data | Full-screen map, minimal UI |
| **Explore** | Map click | 30 sec | Sparklines, metrics, warnings | Sidebar slide-in, accordions |
| **Understand** | Footer link | 5 min | Methodology, sources, limits | Dedicated page, not inline |

**Decision rule:** If it doesn't answer the user's primary question, defer it to the next mode.
