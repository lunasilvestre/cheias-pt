# P2 Architecture Fix: GSAP Timeline Choreography

**Date:** 2026-02-27
**Status:** MUST APPLY before Session 7
**Problem:** Sessions 5-6 used scroll-progress-to-state mapping (v0 pattern). Session 7
must NOT propagate this to Ch.4's 13-layer synoptic stack.

---

## The Problem

Current `handleChapter2Progress(progress)` maps scroll position to layer states:

```typescript
// WRONG — v0 pattern
if (progress < 0.1) sst = progress / 0.1 * 0.8;
if (progress >= 0.3) storm = (progress - 0.3) / 0.1 * 0.9;
if (progress >= 0.5) ivtPlayer.play();
if (progress >= 0.6) windVisible = true;
if (progress >= 0.8) camera.push();
```

Problems:
1. Fast scroll skips reveals (SST never reaches 0.8 if you scroll past in 200ms)
2. Slow scroll makes you wait for content that's "parked" at a scroll position
3. Every scroll tick recomputes all opacity values (wasteful)
4. Breakpoint logic grows combinatorially with layer count
5. **Ch.4 with 13 layers and 4 sub-chapters would be unmaintainable in this pattern**

## The Fix

### Principle: Scroll = Chapter Selection. GSAP = Choreography.

```
scrollama onStepEnter('chapter-2') → enterChapter2() → starts GSAP timeline
  Timeline plays at designed pacing regardless of scroll speed:
    0.0s: SST fades in (1.5s ease)
    1.5s: Storm tracks appear (1s ease)
    3.0s: Globe rotates (2s)
    4.0s: IVT player starts, date label appears
    5.0s: Wind particles activate
    8.0s: Camera pushes toward Portugal

scrollama onStepExit('chapter-2') → leaveChapter2() → kills timeline + cleanup
```

### The Pattern

```typescript
// CORRECT — GSAP timeline choreography
export function enterChapter2(): void {
  if (!map) return;

  // 1. Load all data (async, show loading state)
  loadChapter2Data().then(() => {
    // 2. Build GSAP timeline — runs at DESIGNED pacing
    ch2Timeline = gsap.timeline({ paused: false });

    ch2Timeline
      .to(ch2State, { sstOpacity: 0.8, duration: 1.5, ease: 'power2.out',
        onUpdate: () => rebuildCh2DeckLayers() })
      .to(ch2State, { stormOpacity: 0.9, duration: 1, ease: 'power2.out',
        onUpdate: () => {
          setLayerOpacity(map, 'storm-tracks', ch2State.stormOpacity);
          setLayerOpacity(map, 'storm-track-labels', ch2State.stormOpacity);
        }
      }, '+=0.5')
      .to({}, { duration: 0, onComplete: () => startGlobeRotation() }, '+=1')
      .to({}, { duration: 0, onComplete: () => {
          ch2IvtPlayer?.play();
          showDateLabel();
        }
      }, '+=1')
      .to(ch2State, { windOpacity: 1, duration: 1, ease: 'power2.out',
        onUpdate: () => rebuildCh2DeckLayers() }, '+=1')
      .to({}, { duration: 0, onComplete: () => {
          map?.easeTo({ center: [-15, 38], zoom: 3.5, duration: 4000 });
        }
      }, '+=3');
  });
}

export function leaveChapter2(): void {
  // Kill timeline wherever it is — no orphaned animations
  ch2Timeline?.kill();
  ch2Timeline = null;
  ch2IvtPlayer?.destroy();
  // ... cleanup ...
}
```

### Ch.4 Sub-Chapter Pattern

For Ch.4, scroll STILL controls sub-chapter transitions (the user controls narrative
pacing). But each sub-chapter has its OWN GSAP timeline:

```typescript
// Scroll controls WHICH sub-chapter:
onStepProgress('chapter-4', progress => {
  const subChapter =
    progress < 0.3 ? 'kristin' :
    progress < 0.4 ? 'respite' :
    progress < 0.7 ? 'leonardo' : 'marta';

  if (subChapter !== activeSubChapter) {
    exitSubChapter(activeSubChapter);
    enterSubChapter(subChapter);  // ← starts GSAP timeline
    activeSubChapter = subChapter;
  }
});

// WITHIN a sub-chapter, GSAP handles choreography:
function enterKristin(): void {
  kristinTimeline = gsap.timeline();
  kristinTimeline
    .to({}, { duration: 0, onComplete: () => synopticPlayer.play() })
    .to(state, { isobarOpacity: 1, duration: 1.5 })
    .to(state, { particleOpacity: 1, duration: 1 }, '-=0.5')
    .to(state, { precipOpacity: 0.7, duration: 1.5 }, '+=0.5')
    .to(state, { warningOpacity: 0.8, duration: 1 }, '+=1')
    // ... satellite IR crossfade at designed moment ...
}
```

### What Stays Scroll-Driven

- **Ch.3 soil moisture:** Scroll = time. `setScrollProgress()` → frame index. CORRECT.
- **Ch.4 sub-chapter selection:** Scroll position determines Kristin/respite/Leonardo/Marta.
- **Ch.7 sequential layer build:** Each layer reveals at a scroll milestone because the
  BUILD SEQUENCE is the narrative (you add one layer at a time as you read).
- **Pre-loading:** Scroll progress > 0.8 → preload next chapter. CORRECT.

### What Becomes Timeline-Driven

Everything else. The REVEAL SEQUENCE within a chapter/sub-chapter is a GSAP timeline:
- Ch.0: Ghost pulse (already timeline-driven, correct)
- Ch.1: Flood extent fade-in (should be 2s timeline on enter, not scroll-mapped)
- Ch.2: SST → storms → globe → IVT → wind → camera (timeline)
- Ch.4 per sub-chapter: synoptic player start → isobars → particles → precip → warnings
- Ch.5: Rivers → stations → sparklines → 3D columns
- Ch.6 per sub-location: flood extent → depth → markers → triptych

---

## Implementation Plan

### Refactor Session (run BEFORE Session 7)

1. Refactor `handleChapter1Progress` → `enterChapter1Timeline()`
2. Refactor `handleChapter2Progress` → `enterChapter2Timeline()`
3. Keep `handleChapter3Progress` as-is (scroll = time is correct for Ch.3)
4. Add `ch7SequentialBuild(progress)` as the ONE other scroll-driven handler
   (because the build sequence IS the narrative)
5. Update `onStepProgress` to only call:
   - Ch.3 scroll-driven player
   - Ch.4 sub-chapter selection (triggers timelines)
   - Ch.7 sequential build
   - Pre-load triggers
6. Add `onStepExit` handler that kills active timelines

### Type Changes

```typescript
// Add to types.ts
interface ChapterChoreography {
  type: 'timeline' | 'scroll-driven' | 'sequential-build';
  // timeline: GSAP runs on enter, killed on exit
  // scroll-driven: progress maps to frame index (Ch.3 only)
  // sequential-build: progress maps to layer reveals (Ch.7)
}
```

---

## Why This Matters for Ch.4

The v0 scroll-progress pattern for Ch.4's 4 sub-chapters × 13 layers would produce
~200 lines of brittle breakpoint logic:

```typescript
// NIGHTMARE — don't build this
if (progress < 0.3) {
  if (progress < 0.05) isobar = progress / 0.05;
  if (progress >= 0.05 && progress < 0.1) particle = (progress - 0.05) / 0.05;
  if (progress >= 0.1 && progress < 0.15) precip = (progress - 0.1) / 0.05;
  if (progress >= 0.15 && progress < 0.18) satellite = ...;
  if (progress >= 0.18) warning = ...;
} else if (progress < 0.4) {
  // respite: freeze everything, show sparklines
} else if (progress < 0.7) {
  // Leonardo: same 5 opacity ramps, different data
  // plus frontal boundaries, different warnings...
} else {
  // Marta: tightest camera, full composite
  // 13 layers all interpolating simultaneously
}
```

With GSAP timelines, each sub-chapter is a clean, testable, designer-paced sequence.
