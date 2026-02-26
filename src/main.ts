/**
 * cheias.pt — Main orchestration
 *
 * Initializes the map, scroll observer, and layer manager.
 * Wires chapter transitions to camera and layer changes.
 */

import { chapters } from './chapters';
import { initMap, flyToChapter, getMap } from './map-setup';
import {
  initScrollObserver,
  initScrollEngine,
  enterChapter3,
  leaveChapter3,
  enterChapter4,
  leaveChapter4,
  enterChapter5,
  enterChapter9,
} from './scroll-engine';
import {
  showChapterLayers,
  initConsequencePopups,
  filterConsequencesByChapter,
  colorBasinsByPrecondition,
} from './layer-manager';
import {
  enterExplorationMode,
  exitExplorationMode,
  geolocateUser,
} from './exploration-mode';
import type { ResolvedChapter } from './types';

let previousChapterId: string | null = null;

function main(): void {
  const map = initMap('map-container');

  map.on('load', () => {
    console.log('[cheias.pt] Map loaded');

    initScrollEngine(map);
    initScrollObserver(chapters, onChapterEnter);
    initConsequencePopups(map);
    wireCTAButtons();
  });
}

/**
 * Called when a chapter section scrolls into view.
 */
function onChapterEnter(chapterId: string, config: ResolvedChapter): void {
  console.log(`[cheias.pt] Chapter: ${chapterId}`);

  if (previousChapterId === 'chapter-3' && chapterId !== 'chapter-3') {
    leaveChapter3();
  }
  if (previousChapterId === 'chapter-4' && chapterId !== 'chapter-4') {
    leaveChapter4();
  }
  previousChapterId = chapterId;

  if (config.camera && config.animation) {
    flyToChapter(config.camera, config.animation);
  }

  const layerConfig = config.isSubstep
    ? { ...config, layers: config.parentLayers || [] }
    : config;

  const mapInstance = getMap();
  const chapterNum = parseInt((chapterId.match(/chapter-(\d+)/) || [])[1], 10);

  if (mapInstance) {
    showChapterLayers(mapInstance, layerConfig);

    if (!isNaN(chapterNum)) {
      if (chapterNum === 7) {
        filterConsequencesByChapter(mapInstance, null);
      } else {
        filterConsequencesByChapter(mapInstance, chapterNum);
      }
    }

    if (chapterNum === 7) {
      colorBasinsByPrecondition(mapInstance, 'peak');
    } else if (chapterNum === 8) {
      colorBasinsByPrecondition(mapInstance, 'pre_storm');
    } else if (chapterNum !== 5) {
      colorBasinsByPrecondition(mapInstance, null);
    }
  }

  if (chapterId === 'chapter-3') enterChapter3();
  if (chapterId === 'chapter-4') enterChapter4();
  if (chapterId === 'chapter-5') enterChapter5();
  if (chapterId === 'chapter-9') enterChapter9();

  if (config.onEnter === 'enableExploration') {
    enterExplorationMode();
  } else {
    exitExplorationMode();
  }

  updateDynamicLegend(chapterId, config);
  updateProgress(chapterId);
}

/**
 * Update the scroll progress indicator.
 */
function updateProgress(chapterId: string): void {
  const indicator = document.getElementById('progress-indicator');
  if (!indicator) return;

  const match = chapterId.match(/chapter-(\d+)/);
  if (!match) return;

  const current = parseInt(match[1], 10);
  const total = chapters.length - 1;
  const progress = Math.min(current / total, 1);

  indicator.style.width = `${progress * 100}%`;
}

/**
 * Update the floating dynamic legend based on the current chapter's legend config.
 */
function updateDynamicLegend(chapterId: string, config: ResolvedChapter): void {
  const el = document.getElementById('dynamic-legend');
  if (!el) return;

  let legendItems = config.legend;
  if (config.isSubstep) {
    const parentId = chapterId.replace(/[a-z]$/, '').replace(/-$/, '');
    const parent = chapters.find(c => c.id === parentId);
    legendItems = parent ? parent.legend : [];
  }

  if (!legendItems || legendItems.length === 0) {
    el.classList.remove('visible');
    return;
  }

  let html = '';
  for (const item of legendItems) {
    const shape = item.type === 'circle'
      ? 'border-radius: 50%;'
      : 'border-radius: 2px;';
    html += `<div class="legend-item">
      <span class="legend-swatch" style="background: ${item.color}; ${shape}"></span>
      <span class="legend-label">${item.title}</span>
    </div>`;
  }

  el.innerHTML = html;
  el.classList.add('visible');
}

/**
 * Wire CTA buttons in the explore chapter.
 */
function wireCTAButtons(): void {
  document.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    const btn = target.closest('[data-action]') as HTMLElement | null;
    if (!btn) return;

    const action = btn.dataset.action;
    switch (action) {
      case 'geolocate':
        geolocateUser();
        break;
      case 'methodology':
        console.log('[cheias.pt] Methodology panel not yet implemented');
        break;
      case 'share':
        if (navigator.share) {
          navigator.share({
            title: 'cheias.pt — O Inverno Que Partiu os Rios',
            url: window.location.href,
          }).catch(() => {});
        } else {
          navigator.clipboard.writeText(window.location.href).then(() => {
            btn.textContent = 'Link copiado';
            setTimeout(() => { btn.textContent = 'Partilhar'; }, 2000);
          });
        }
        break;
    }
  });
}

main();
