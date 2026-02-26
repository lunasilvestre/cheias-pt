/**
 * cheias.pt — Scroll engine
 *
 * Uses scrollama for scroll-driven chapter transitions.
 * Merges chapter wiring and temporal player logic.
 */

import scrollama from 'scrollama';
import type { Map as MLMap } from 'maplibre-gl';
import type { Chapter, ResolvedChapter, RasterFrame } from './types';
import { loadRasterManifest, loadDischargeTimeseries } from './data-loader';
import { ensureLayer, updateSourceData, updateImageSource } from './layer-manager';

// ── Temporal player state ──

let frames: RasterFrame[] = [];
let currentFrameIndex = -1;
let onFrameChange: ((frame: RasterFrame, idx: number) => void) | null = null;

function setFrames(frameArray: RasterFrame[]): void {
  frames = frameArray;
  currentFrameIndex = -1;
}

function setProgress(progress: number): void {
  if (frames.length === 0) return;
  const idx = Math.min(Math.floor(progress * frames.length), frames.length - 1);
  if (idx !== currentFrameIndex && idx >= 0) {
    currentFrameIndex = idx;
    if (onFrameChange) onFrameChange(frames[idx], idx);
  }
}

function onFrame(callback: (frame: RasterFrame, idx: number) => void): void {
  onFrameChange = callback;
}

function resetPlayer(): void {
  frames = [];
  currentFrameIndex = -1;
  onFrameChange = null;
}

// ── Scrollama instance ──

let scroller: scrollama.ScrollamaInstance | null = null;
let activeChapterId: string | null = null;

// ── Chapter wiring state ──

let map: MLMap | null = null;
let ch3Initialized = false;
let ch4Initialized = false;
const preloadedUrls = new Set<string>();

/**
 * Initialize the scroll engine with the map instance.
 */
export function initScrollEngine(mapInstance: MLMap): void {
  map = mapInstance;
}

// ── Image preloading ──

function preloadImages(rasterFrames: RasterFrame[]): void {
  for (const frame of rasterFrames) {
    const url = `data/${frame.url}`;
    if (preloadedUrls.has(url)) continue;
    preloadedUrls.add(url);
    const img = new Image();
    img.src = url;
  }
}

// ── Date label helpers ──

function showDateLabel(): void {
  const el = document.getElementById('temporal-date-label');
  if (el) el.classList.add('visible');
}

function hideDateLabel(): void {
  const el = document.getElementById('temporal-date-label');
  if (el) {
    el.classList.remove('visible');
    el.textContent = '';
  }
}

function updateDateLabel(dateStr: string): void {
  const el = document.getElementById('temporal-date-label');
  if (!el) return;

  if (!dateStr) {
    el.textContent = '';
    return;
  }

  const d = new Date(dateStr + 'T00:00:00');
  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];
  el.textContent = `${d.getDate()} de ${months[d.getMonth()]} ${d.getFullYear()}`;
}

// ── Chapter enter/leave handlers ──

export async function enterChapter3(): Promise<void> {
  if (!map) return;

  const manifest = await loadRasterManifest();
  const smFrames = manifest.soil_moisture.frames;

  ensureLayer(map, 'soil-moisture-raster');
  setFrames(smFrames);
  preloadImages(smFrames.slice(0, 15));

  onFrame((frame, idx) => {
    if (!map) return;
    updateImageSource(map, 'soil-moisture-raster', `data/${frame.url}`);
    updateDateLabel(frame.date);
    preloadImages(smFrames.slice(idx + 1, idx + 11));
  });

  if (smFrames.length > 0) {
    updateImageSource(map, 'soil-moisture-raster', `data/${smFrames[0].url}`);
    updateDateLabel(smFrames[0].date);
  }

  showDateLabel();
  ch3Initialized = true;
}

export function leaveChapter3(): void {
  resetPlayer();
  hideDateLabel();
  ch3Initialized = false;
}

export async function enterChapter4(): Promise<void> {
  if (!map) return;
  if (ch3Initialized) leaveChapter3();

  const manifest = await loadRasterManifest();
  const precipFrames = manifest.precipitation.frames;

  ensureLayer(map, 'precipitation-raster');
  setFrames(precipFrames);
  preloadImages(precipFrames.slice(0, 15));

  onFrame((frame, idx) => {
    if (!map) return;
    updateImageSource(map, 'precipitation-raster', `data/${frame.url}`);
    updateDateLabel(frame.date);
    preloadImages(precipFrames.slice(idx + 1, idx + 11));
  });

  if (precipFrames.length > 0) {
    updateImageSource(map, 'precipitation-raster', `data/${precipFrames[0].url}`);
    updateDateLabel(precipFrames[0].date);
  }

  showDateLabel();
  ch4Initialized = true;
}

export function leaveChapter4(): void {
  resetPlayer();
  hideDateLabel();
  ch4Initialized = false;
}

export async function enterChapter5(): Promise<void> {
  if (!map) return;
  if (ch4Initialized) leaveChapter4();

  const manifest = await loadRasterManifest();
  ensureLayer(map, 'soil-moisture-raster');
  const jan28Frame = manifest.soil_moisture.frames.find(f => f.date === '2026-01-28');
  if (jan28Frame) {
    updateImageSource(map, 'soil-moisture-raster', `data/${jan28Frame.url}`);
  }

  const data = await loadDischargeTimeseries();
  const features: GeoJSON.Feature[] = data.stations.map(station => {
    const peak = station.timeseries.reduce((best, t) =>
      t.discharge_ratio > best.discharge_ratio ? t : best
    , station.timeseries[0]);

    return {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [station.lon, station.lat] },
      properties: {
        name: station.name,
        basin: station.basin,
        discharge: peak.discharge,
        discharge_ratio: peak.discharge_ratio,
        peak_date: peak.date,
      },
    };
  });

  updateSourceData(map, 'glofas-discharge', { type: 'FeatureCollection', features });
  updateSourceData(map, 'river-labels', { type: 'FeatureCollection', features });
}

export async function enterChapter9(): Promise<void> {
  if (!map) return;
  if (ch3Initialized) leaveChapter3();
  if (ch4Initialized) leaveChapter4();

  ensureLayer(map, 'soil-moisture-tiles');
  ensureLayer(map, 'precipitation-tiles');
  ensureLayer(map, 'flood-extent-polygons');
  ensureLayer(map, 'glofas-discharge');
  ensureLayer(map, 'basins-outline');
}

// ── Active state management ──

function updateActiveState(chapterId: string): void {
  const sections = document.querySelectorAll('[data-chapter]');
  for (const section of sections) {
    if ((section as HTMLElement).dataset.chapter === chapterId) {
      section.classList.add('chapter--active');
    } else {
      section.classList.remove('chapter--active');
    }
  }
}

// ── Scrollama-based scroll observer ──

/**
 * Initialize scrollama on all chapter sections.
 */
export function initScrollObserver(
  chapters: Chapter[],
  onChapterEnter: (chapterId: string, config: ResolvedChapter) => void
): void {
  // Build chapter lookup including substeps
  const chapterMap = new Map<string, ResolvedChapter>();
  for (const ch of chapters) {
    chapterMap.set(ch.id, ch as ResolvedChapter);
    if (ch.substeps) {
      for (const sub of ch.substeps) {
        chapterMap.set(sub.id, {
          ...ch,
          ...sub,
          isSubstep: true,
          parentLayers: ch.layers,
        } as ResolvedChapter);
      }
    }
  }

  scroller = scrollama();

  scroller
    .setup({
      step: '[data-chapter]',
      offset: 0.5,
      progress: true,
    })
    .onStepEnter((response) => {
      const chapterId = response.element.dataset.chapter;
      if (!chapterId || chapterId === activeChapterId) return;

      activeChapterId = chapterId;

      const config = chapterMap.get(chapterId);
      if (config) {
        onChapterEnter(chapterId, config);
      }

      updateActiveState(chapterId);
    })
    .onStepProgress((response) => {
      const chapterId = response.element.dataset.chapter;
      if (!chapterId) return;

      // Drive temporal animation for chapters 3 and 4 via scroll progress
      if (chapterId === 'chapter-3' && ch3Initialized) {
        setProgress(response.progress);
      }
      if (chapterId === 'chapter-4' && ch4Initialized) {
        setProgress(response.progress);
      }
    });

  // Handle window resize
  window.addEventListener('resize', () => {
    scroller?.resize();
  });
}

export function getActiveChapter(): string | null {
  return activeChapterId;
}

export function destroyScrollObserver(): void {
  if (scroller) {
    scroller.destroy();
    scroller = null;
  }
  activeChapterId = null;
}
