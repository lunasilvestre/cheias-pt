# cheias.pt — Cross-Browser & Platform Testing Strategy

## Quick Start

```bash
# Make serve script executable
chmod +x scripts/serve.sh

# Option A: Node (recommended — correct MIME types for ES modules)
npm run dev

# Option B: Fallback
bash scripts/serve.sh

# Open http://localhost:3000
```

## What to Test

The scroll scaffold is the critical path. Every test below assumes the page loads, the basemap renders, and scrolling triggers chapter transitions.

### Test Matrix

| # | What | Why it breaks | How to verify |
|---|------|---------------|---------------|
| 1 | **Basemap renders** | WebGL disabled, CARTO tiles blocked, MapLibre CDN down | Dark basemap visible, Portugal coastline appears |
| 2 | **Scroll → chapter transitions** | IntersectionObserver threshold, section heights | Scroll through all 10 chapters — camera moves, text cards appear/disappear |
| 3 | **Glassmorphism panels** | `backdrop-filter` unsupported (older browsers) | Chapter cards show frosted glass effect over map |
| 4 | **ES module loading** | MIME type `text/javascript` not served correctly (Python server) | No console errors about module loading, `story-config.js` imports work |
| 5 | **Mobile layout** | Chapter cards at <720px, touch scroll, bottom padding | Cards go full-width, map visible between cards, no horizontal overflow |
| 6 | **Hero title typography** | Google Fonts (Inter) load, Georgia fallback | "O Inverno Que Partiu os Rios" renders in serif, subtitle in sans |
| 7 | **Progress bar** | Progress indicator tracks scroll position | Bar at top fills as you scroll through chapters |
| 8 | **Chapter 9 exploration mode** | `scrollZoom.enable()`, `dragPan.enable()` after story ends | Pinch-zoom and drag work in final chapter, layer panel appears |
| 9 | **Layer stubs** | Console logs "data not yet available" (expected until data is wired) | No JS errors, graceful degradation |
| 10 | **Performance** | MapLibre + glassmorphism + scroll observer on mobile | Smooth scrolling at 30+ fps, no jank during camera transitions |

### Browser Targets

| Browser | Priority | Known Risks |
|---------|----------|-------------|
| Chrome Desktop (latest) | P0 | Baseline — should work |
| Firefox Desktop (latest) | P0 | `backdrop-filter` needs `-webkit-` prefix check |
| Safari Desktop (latest) | P1 | WebGL context loss on tab switch, scroll inertia differs |
| Chrome Android | P1 | Touch scroll + IntersectionObserver timing, address bar resize |
| Safari iOS | P1 | `100vh` includes address bar (use `dvh`), WebGL memory limits |
| Edge | P2 | Chromium-based, should match Chrome |

### Device Breakpoints

| Breakpoint | Viewport | What changes |
|------------|----------|--------------|
| Mobile | 375×667 (iPhone SE) | Full-width cards, reduced padding, simplified layers |
| Mobile large | 390×844 (iPhone 14) | Same layout, more breathing room |
| Tablet | 768×1024 (iPad) | Cards at max-width, map more visible |
| Desktop | 1440×900 | Full layout — side-positioned cards, basins visible alongside |

## Manual QA Checklist (5-minute run)

Do this on each browser/device combination:

```
[ ] Page loads without console errors
[ ] Basemap visible (dark navy, Portugal coastline)
[ ] Hero title "O Inverno Que Partiu os Rios" renders correctly
[ ] Scroll down → Chapter 1 camera transition fires (flyTo Portugal)
[ ] Continue scrolling through all chapters — each triggers camera move
[ ] Chapter text cards appear with glassmorphism effect
[ ] Progress bar at top tracks scroll position
[ ] Basin/district outlines appear when their chapters activate
[ ] Chapter 9 → map becomes interactive (drag, zoom)
[ ] No horizontal scroll overflow on mobile
[ ] No white flash between chapters
```

## Automated Testing with Playwright

The project has `.playwright-mcp/` — extend it for scroll regression:

```bash
# Install Playwright (if not installed)
npx playwright install

# Run tests
npx playwright test
```

### Suggested test file: `tests/scroll-smoke.spec.js`

```javascript
import { test, expect } from '@playwright/test';

const CHAPTERS = [
  'chapter-0', 'chapter-1', 'chapter-2', 'chapter-3',
  'chapter-4', 'chapter-5', 'chapter-6a', 'chapter-6b',
  'chapter-6c', 'chapter-7', 'chapter-8', 'chapter-9'
];

test.describe('Scroll narrative', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    // Wait for MapLibre to initialize
    await page.waitForFunction(() => {
      return document.querySelector('#map-container canvas') !== null;
    }, { timeout: 10000 });
  });

  test('basemap renders', async ({ page }) => {
    const canvas = page.locator('#map-container canvas');
    await expect(canvas).toBeVisible();
  });

  test('hero title visible on load', async ({ page }) => {
    const title = page.locator('.hero__title');
    await expect(title).toContainText('O Inverno Que Partiu os Rios');
  });

  test('scrolling triggers chapter transitions', async ({ page }) => {
    for (const chapter of CHAPTERS.slice(0, 5)) {
      const section = page.locator(`[data-chapter="${chapter}"]`);
      await section.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500); // Allow transition
      await expect(section).toBeVisible();
    }
  });

  test('no console errors', async ({ page }) => {
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    // Scroll through entire story
    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });
    await page.waitForTimeout(3000);
    // Filter out expected "data not yet available" messages
    const real_errors = errors.filter(e => !e.includes('data not yet available'));
    expect(real_errors).toHaveLength(0);
  });
});

test.describe('Responsive', () => {
  test('mobile layout — no horizontal overflow', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:3000');
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);
  });
});
```

### Playwright config: `playwright.config.js`

```javascript
export default {
  testDir: './tests',
  use: {
    baseURL: 'http://localhost:3000',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    { name: 'firefox', use: { browserName: 'firefox' } },
    { name: 'webkit', use: { browserName: 'webkit' } },
    { name: 'mobile-chrome', use: { browserName: 'chromium', viewport: { width: 390, height: 844 } } },
    { name: 'mobile-safari', use: { browserName: 'webkit', viewport: { width: 390, height: 844 } } },
  ],
  webServer: {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: true,
  },
};
```

## Known Issues to Watch

**`100vh` on iOS Safari:** The viewport height includes the URL bar. If hero section uses `height: 100vh`, it will be taller than visible area on first load. Fix: use `height: 100dvh` with `100vh` fallback.

**`backdrop-filter` on Firefox:** Works since Firefox 103+ but may need `-webkit-backdrop-filter` as fallback. Check `style.css` for the glassmorphism rules.

**MapLibre on low-end Android:** WebGL may struggle with many layers. The layer-manager already stubs 11 data layers — when they're wired in, test that mobile only renders 2-3 simultaneous layers max.

**Scroll jank during camera transitions:** `flyTo()` is GPU-intensive. If scroll + flyTo happens simultaneously, there may be frame drops. The scroll-observer should debounce to prevent rapid-fire transitions.
