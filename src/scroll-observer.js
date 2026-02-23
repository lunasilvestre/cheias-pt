/**
 * cheias.pt — Scroll observer
 *
 * Uses IntersectionObserver to detect which chapter is currently
 * in the viewport and triggers camera + layer transitions.
 * Also provides continuous scroll-progress tracking for animated chapters.
 */

let observer = null;
let activeChapterId = null;
let lastTriggerTime = 0;

const DEBOUNCE_MS = 300;

// Scroll-progress tracking for animated chapters
let progressListenerActive = false;
const progressCallbacks = new Map(); // chapterId -> callback(progress)

/**
 * Initialize the scroll observer on all chapter sections.
 * @param {Object[]} chapters - Array of chapter config objects
 * @param {Function} onChapterEnter - Callback when a chapter enters: (chapterId, chapterConfig) => void
 */
export function initScrollObserver(chapters, onChapterEnter) {
  const chapterMap = new Map();
  for (const ch of chapters) {
    chapterMap.set(ch.id, ch);
    // Also map substeps for chapter 6
    if (ch.substeps) {
      for (const sub of ch.substeps) {
        chapterMap.set(sub.id, { ...ch, ...sub, isSubstep: true, parentLayers: ch.layers });
      }
    }
  }

  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;

        const chapterId = entry.target.dataset.chapter;
        if (!chapterId || chapterId === activeChapterId) continue;

        const now = Date.now();
        if (now - lastTriggerTime < DEBOUNCE_MS) continue;

        lastTriggerTime = now;
        activeChapterId = chapterId;

        const config = chapterMap.get(chapterId);
        if (config) {
          onChapterEnter(chapterId, config);
        }

        updateActiveState(chapterId);
      }
    },
    {
      root: null,
      threshold: 0.5,
    }
  );

  // Observe all chapter sections
  const sections = document.querySelectorAll('[data-chapter]');
  for (const section of sections) {
    observer.observe(section);
  }

  // Start the scroll-progress listener (runs always, cheap when no callbacks registered)
  startProgressListener();
}

/**
 * Get the currently active chapter ID.
 * @returns {string|null}
 */
export function getActiveChapter() {
  return activeChapterId;
}

/**
 * Clean up the observer.
 */
export function destroyScrollObserver() {
  if (observer) {
    observer.disconnect();
    observer = null;
  }
  activeChapterId = null;
}

/**
 * Update visual active state on chapter elements.
 */
function updateActiveState(chapterId) {
  const sections = document.querySelectorAll('[data-chapter]');
  for (const section of sections) {
    if (section.dataset.chapter === chapterId) {
      section.classList.add('chapter--active');
    } else {
      section.classList.remove('chapter--active');
    }
  }
}

/**
 * Register a scroll-progress callback for a chapter.
 * The callback receives a value from 0 to 1 as the user scrolls through.
 * @param {string} chapterId
 * @param {Function} callback - (progress: number) => void
 */
export function onChapterProgress(chapterId, callback) {
  progressCallbacks.set(chapterId, callback);
}

/**
 * Remove a scroll-progress callback for a chapter.
 * @param {string} chapterId
 */
export function offChapterProgress(chapterId) {
  progressCallbacks.delete(chapterId);
}

/**
 * Start the scroll event listener for continuous progress tracking.
 */
function startProgressListener() {
  if (progressListenerActive) return;
  progressListenerActive = true;

  let ticking = false;
  window.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      ticking = false;
      if (!activeChapterId || !progressCallbacks.has(activeChapterId)) return;

      const section = document.querySelector(`[data-chapter="${activeChapterId}"]`);
      if (!section) return;

      const rect = section.getBoundingClientRect();
      const sectionHeight = rect.height;
      if (sectionHeight <= 0) return;

      // progress: 0 when top of section hits top of viewport,
      // 1 when bottom of section reaches top of viewport
      const progress = Math.max(0, Math.min(1, -rect.top / sectionHeight));
      progressCallbacks.get(activeChapterId)(progress);
    });
  }, { passive: true });
}
