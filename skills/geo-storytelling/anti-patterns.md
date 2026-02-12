# Anti-Patterns: What NOT To Do in Geo Dashboards

**Purpose:** Learn from common mistakes in environmental data platforms

---

## 1. ❌ Overwhelming Users with Configuration

**Symptom:** Multi-tab interfaces, dropdown menus with 20+ parameters, forms requiring training

**Why it fails:** Sustainability data platforms report 60% of users describe their experience as "patchwork of software applications" requiring expert knowledge

**Example failures:**
- Platforms that assume users want to become software experts
- Configuration systems that require reading documentation before use
- Parameter dropdowns with technical jargon (no tooltips, no defaults)

**Fix:**
✅ Single-screen interface with sensible defaults
✅ Pre-computed risk levels, not "calculate your own index"
✅ Click to reveal details, don't force configuration

**Reference:** fogos.pt works because anyone can open it and understand in 30 seconds

---

## 2. ❌ Hiding Data Sources or Burying Attribution

**Symptom:** No visible source citations, buried in fine print, or completely absent

**Why it fails:** Users interpret opacity as unreliability. If you don't say where data comes from, they assume you're hiding something.

**Example failures:**
- Flood maps with no mention of forecast model
- Risk scores with no explanation of calculation
- "Proprietary algorithm" with zero transparency

**Fix:**
✅ Name institutional sources prominently: "IPMA + Copernicus GloFAS"
✅ Footer links to full methodology
✅ Data freshness badges: "Updated 2h ago"

**Reference:** Resource Watch leads with "Curated by WRI experts" for institutional trust

---

## 3. ❌ False Precision (Single Number for Uncertain Forecasts)

**Symptom:** "60mm rain forecast" with no range, confidence interval, or uncertainty

**Why it fails:** Forecasts have inherent uncertainty. Showing a single value implies certainty that doesn't exist, leading to over-reliance or distrust when wrong.

**Example failures:**
- Flood maps showing binary flood/no-flood with no depth gradation
- Point estimates for 7-day precipitation forecasts
- Risk scores (0.88) with 4 decimal places

**Fix:**
✅ Show ranges: "50-70mm (P10-P90)"
✅ Graduated severity: "Low / Moderate / High / Very High"
✅ Explicit bounds: "Upper limit (no defenses) vs. lower limit (with defenses)"

**Reference:** CoCliCo provides upper/lower bounds explicitly; GFW shows confidence levels

---

## 4. ❌ Sterile, Clinical Design (Breaking the Delight → Curiosity Sequence)

**Symptom:** Government-portal beige, no animation, no personality, feels like a spreadsheet

**Why it fails:** Research shows people make choices based on prior beliefs and gut feelings, even when data conflicts. To overcome this cognitive bias, you need emotional connection BEFORE presenting evidence. Sterile interfaces skip the **Delight → Curiosity → Exploration → Digestion** sequence and go straight to digestion. Result: users bounce without engaging.

**Example failures:**
- All-white backgrounds with black text (no contrast for data layers)
- No transitions or animations (no delight)
- Generic sans-serif with no typographic hierarchy (no personality)
- No metaphor or visual symbolism (no curiosity trigger)
- Fear-first framing ("DANGER") instead of empowerment ("Here's the situation")

**Fix:**
✅ **Delight:** Dark aesthetic (Deep navy #0a212e) chosen for functional contrast, not just aesthetics
✅ **Curiosity:** Playful interactions (spin globe, slide timeline, toggle layers freely)
✅ **Exploration:** Smooth 400ms animations, metaphorical design (water deepens as flood risk rises)
✅ **Digestion:** Empowerment framing—celebrate LOW risk prominently, frame HIGH risk with context + authoritative guidance

**Reference:** Half-Earth 3D globe (delight), fogos.pt dark theme, Soils Revealed "dig deeper" metaphor

---

## 5. ❌ Opaque Panels Blocking Map Context

**Symptom:** Solid-color sidebars that completely obscure the map underneath

**Why it fails:** Users orient spatially. Blocking the map disrupts their mental model of "where" they're looking at.

**Example failures:**
- White sidebar with 100% opacity covering 30% of map
- Modal dialogs with solid backgrounds
- Tooltips with no transparency

**Fix:**
✅ Glassmorphism: `backdrop-filter: blur(16px)` + `rgba(9, 20, 26, 0.4)`
✅ Sidebars preserve map visibility underneath
✅ Panels feel layered, not blocking

**Reference:** All Vizzuality platforms use glass effects for panels over maps

---

## 6. ❌ No Mobile Strategy (Squished Sidebar on Phone)

**Symptom:** Desktop sidebar just gets narrower on mobile, requires horizontal scrolling

**Why it fails:** Mobile users hold phones one-handed. Narrow sidebars require precision taps. Horizontal scrolling is painful.

**Example failures:**
- 420px sidebar → 280px on mobile (too narrow)
- Charts with horizontal scroll
- Map controls in top-right corner (unreachable for left-handed users)

**Fix:**
✅ Desktop: 420px sidebar, right-aligned
✅ Mobile: Full-width bottom sheet, slides up from bottom
✅ Collapsed state: 65% translateY (peek visible)
✅ Swipe gestures for dismiss

**Reference:** half-earth-v3 bottom sheet with framer-motion swipe

---

## 7. ❌ Duplicate Official Functions

**Symptom:** Platform tries to replace emergency services with custom advice

**Why it fails:** You're not the authority. IPMA issues warnings. ANEPC manages emergencies. Your role is visualization + context.

**Example failures:**
- Custom evacuation instructions (liability risk)
- "We predict..." when official forecast exists
- Competing with government emergency apps

**Fix:**
✅ Show official warnings verbatim (IPMA text)
✅ Link to authoritative sources: prociv.pt, ipma.pt
✅ "Follow ANEPC instructions" not "We recommend..."

**Reference:** GFW shows forest alerts but links to official land management agencies for action

---

## 8. ❌ Data Tables Instead of Visualizations

**Symptom:** Raw JSON, CSV exports, or HTML tables as primary interface

**Why it fails:** Non-experts can't parse tables. Trends invisible. Cognitive load too high.

**Example failures:**
- Station data as 50-row table
- Forecast precipitation as hourly table
- River discharge as CSV link

**Fix:**
✅ Sparkline charts (14-day history + 7-day forecast)
✅ Gauges for current state (risk level 0.0-1.0)
✅ Color-coded maps (choropleth for risk levels)
✅ Table as secondary view (download link for power users)

**Reference:** GFW shows "72.5 Mha lost" (single number) before offering dataset download

---

## 9. ❌ No Data Freshness Indicators

**Symptom:** No "last updated" timestamp, no indication when next update arrives

**Why it fails:** During emergencies, users need to know if data is current. Stale data presented as fresh erodes trust.

**Example failures:**
- Forecast shown with no validity period
- API failure = app shows cached data with no warning
- "Real-time" data actually 6 hours old

**Fix:**
✅ Freshness badges: "Updated 2h ago" with green/yellow/red dot
✅ Forecast validity: "Valid until 2026-02-19 18:00"
✅ Stale data warning: "Using 6h cached data (API unavailable)"

**Reference:** Gap identified in Vizzuality platforms—opportunity for cheias.pt to lead

---

## 10. ❌ Polygon Overlap Confusion

**Symptom:** Multiple overlapping polygon layers (districts + basins + flood zones) with no visual hierarchy

**Why it fails:** User can't tell which boundary matters. All polygons compete for attention.

**Example failures:**
- District boundaries + river basin boundaries + flood zones all visible at once
- Same line weight for all boundaries
- No color differentiation between layer types

**Fix:**
✅ Districts: Fill color (risk choropleth) + thin outline
✅ Basins: Thick outline only, no fill (context layer)
✅ Flood zones: Hatched pattern or dashed outline (warning layer)
✅ Z-index: Data layer on top, context below

**Reference:** landgriffon uses `beforeId` to control layer order explicitly

---

## 11. ❌ Ignoring Accessibility

**Symptom:** Color-only encoding (red/green for danger/safe), no keyboard navigation, tiny text

**Why it fails:** 8% of men have color vision deficiency. Screen readers can't read maps. Small text unusable on mobile.

**Example failures:**
- Red = danger, green = safe (colorblind users can't distinguish)
- No ARIA labels on map features
- 10px font size (unreadable on phones)

**Fix:**
✅ Color + pattern: Red = danger + diagonal lines, green = safe + dots
✅ ARIA labels: `aria-label="Coimbra district: Very high flood risk"`
✅ Minimum 12px font size
✅ Keyboard navigation: Tab through districts, Enter to open sidebar

**Reference:** GFW includes screen-reader support and keyboard navigation

---

## 12. ❌ Auto-Playing Temporal Animations

**Symptom:** Map starts animating forecast timeline automatically on page load

**Why it fails:** User loses control. Can't orient themselves. Feels chaotic.

**Example failures:**
- Timeline playback starts immediately
- No pause button
- No way to jump to specific time
- Animation too fast to comprehend

**Fix:**
✅ Start paused on "now"
✅ Play button for user-initiated animation
✅ Speed controls (0.03×-16×)
✅ Scrubber for precise time selection

**Reference:** GFW timeline with dual-brush control (outer = loaded, inner = visible)

---

## 13. ❌ Assuming Linear User Journeys (Homepage → Page 2 → Page 3)

**Symptom:** Platform designed assuming users start at homepage and follow intended path

**Why it fails:** "Unlike software where people take what is essentially a linear journey, websites have multiple entry points and people expect to know what's going on and where to go next, regardless of what stage of the journey they join at... the user journey is in fact a circular one that must loop from any starting point towards the conclusion" (Elena de Pomar).

**Example failures:**
- Deep links break context (user lands on `/district/coimbra` with no explanation of what platform does)
- Navigation assumes prior knowledge (no breadcrumbs, no "About" link on every page)
- Shared URLs don't preserve state (someone shares a map view, recipient sees default view)
- Tutorial only on first visit (returning users who skipped it have no way to access)

**Fix:**
✅ Every page self-orients: Header shows platform name + tagline
✅ URL parameters preserve state: `/map?district=coimbra&layer=soil-moisture`
✅ Always-visible footer: "Como Funciona | Fontes de Dados | Sobre"
✅ Breadcrumbs or contextual headers: "Coimbra — Mondego Basin — Flood Risk"
✅ Tutorial accessible anytime (not just first visit)

**Reference:** Elena de Pomar's circular journey principle, Google Maps (works from any shared link)

---

## 14. ❌ No Playful Interaction (Everything Behind Gates)

**Symptom:** Features locked behind registration, tutorials, or permission dialogs; interactions feel constrained

**Why it fails:** "Design interactions that encourage people to play with the data and learn how the visualisation tool works" (Elena de Pomar). When users can't experiment freely, they don't discover the platform's capabilities. Play = learning.

**Example failures:**
- "Sign up to add layers" (exploring data should be free)
- "Are you sure?" dialogs for non-destructive actions (toggle layer off/on)
- Tutorial that must be completed before map interaction
- No hover previews (click required to see any information)
- Locked timeline playback (register to animate)

**Fix:**
✅ Forgiving interactions: No confirmation dialogs unless truly destructive
✅ Immediate feedback: Hover over district → preview risk level in tooltip
✅ Reversible actions: Add/remove layers freely, no state loss
✅ Playback controls accessible: Speed slider, scrubber, play/pause (no registration)
✅ Tutorial optional, not blocking

**Reference:** Half-Earth Map (spin globe freely), fogos.pt (click any fire, no login)

---

## Summary: The Most Common Mistake

**The #1 anti-pattern:** Assuming users want to become experts in your platform.

**Reality:** Users want answers, not training.
- Glance: "Am I safe?" (5 seconds)
- Explore: "Why is this happening?" (30 seconds)
- Understand: "How does this work?" (5 minutes, optional)

Design for the glance. Make exploration easy. Make understanding available but not required.

**If users need a manual to use your platform, you've failed.**
