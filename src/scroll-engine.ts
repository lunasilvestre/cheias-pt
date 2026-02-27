/**
 * cheias.pt — Scroll engine
 *
 * Uses scrollama for scroll-driven chapter transitions.
 * Manages chapter enter/leave lifecycle and temporal playback.
 */

import scrollama from 'scrollama';
import type { Map as MLMap } from 'maplibre-gl';
import type { Chapter, ResolvedChapter, RasterManifest, TemporalConfig } from './types';
import { loadRasterManifest, loadDischargeTimeseries } from './data-loader';
import { ensureLayer, updateSourceData, updateImageSource } from './layer-manager';
import { TemporalPlayer } from './temporal-player';

// ── Scrollama instance ──

let scroller: scrollama.ScrollamaInstance | null = null;
let activeChapterId: string | null = null;

// ── Chapter wiring state ──

let map: MLMap | null = null;
const activePlayers = new Map<string, TemporalPlayer>();

/**
 * Initialize the scroll engine with the map instance.
 */
export function initScrollEngine(mapInstance: MLMap): void {
  map = mapInstance;
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

// ── Player management ──

function destroyPlayer(chapterId: string): void {
  const player = activePlayers.get(chapterId);
  if (player) {
    player.destroy();
    activePlayers.delete(chapterId);
  }
}

function destroyAllPlayers(): void {
  for (const [id] of activePlayers) {
    destroyPlayer(id);
  }
}

/**
 * Get the active TemporalPlayer for a chapter, if any.
 */
export function getPlayer(chapterId: string): TemporalPlayer | undefined {
  return activePlayers.get(chapterId);
}

// ── Chapter enter/leave handlers ──

export async function enterChapter3(): Promise<void> {
  if (!map) return;

  // Clean up any existing player for this chapter
  destroyPlayer('chapter-3');

  const manifest: RasterManifest = await loadRasterManifest();
  const smFrames = manifest.soil_moisture.frames;

  ensureLayer(map, 'soil-moisture-raster');

  // Build temporal config from manifest
  const config: TemporalConfig = {
    id: 'ch3-soil-moisture',
    frameType: 'png',
    mode: 'scroll-driven',
    urls: smFrames.map(f => `data/${f.url}`),
    dates: smFrames.map(f => f.date),
    layerId: 'soil-moisture-raster',
  };

  const player = new TemporalPlayer('chapter-3', config);
  activePlayers.set('chapter-3', player);

  // Wire frame updates to MapLibre image source
  player.onFrame((idx, date) => {
    if (!map) return;
    const frame = smFrames[idx];
    if (frame) {
      updateImageSource(map, 'soil-moisture-raster', `data/${frame.url}`);
    }
    if (date) updateDateLabel(date);
  });

  // Set initial frame
  if (smFrames.length > 0) {
    updateImageSource(map, 'soil-moisture-raster', `data/${smFrames[0].url}`);
    updateDateLabel(smFrames[0].date);
  }

  showDateLabel();
}

export function leaveChapter3(): void {
  destroyPlayer('chapter-3');
  hideDateLabel();
}

export async function enterChapter4(): Promise<void> {
  if (!map) return;

  // Clean up ch3 if still active
  if (activePlayers.has('chapter-3')) leaveChapter3();
  // Clean up any existing ch4 player
  destroyPlayer('chapter-4');

  const manifest: RasterManifest = await loadRasterManifest();
  const precipFrames = manifest.precipitation.frames;

  ensureLayer(map, 'precipitation-raster');

  const config: TemporalConfig = {
    id: 'ch4-precipitation',
    frameType: 'png',
    mode: 'scroll-driven',
    urls: precipFrames.map(f => `data/${f.url}`),
    dates: precipFrames.map(f => f.date),
    layerId: 'precipitation-raster',
  };

  const player = new TemporalPlayer('chapter-4', config);
  activePlayers.set('chapter-4', player);

  player.onFrame((idx, date) => {
    if (!map) return;
    const frame = precipFrames[idx];
    if (frame) {
      updateImageSource(map, 'precipitation-raster', `data/${frame.url}`);
    }
    if (date) updateDateLabel(date);
  });

  if (precipFrames.length > 0) {
    updateImageSource(map, 'precipitation-raster', `data/${precipFrames[0].url}`);
    updateDateLabel(precipFrames[0].date);
  }

  showDateLabel();
}

export function leaveChapter4(): void {
  destroyPlayer('chapter-4');
  hideDateLabel();
}

export async function enterChapter5(): Promise<void> {
  if (!map) return;
  if (activePlayers.has('chapter-4')) leaveChapter4();

  const manifest: RasterManifest = await loadRasterManifest();
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
  destroyAllPlayers();
  hideDateLabel();

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

      // Drive scroll-driven temporal players
      const player = activePlayers.get(chapterId);
      if (player) {
        player.setScrollProgress(response.progress);
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
  destroyAllPlayers();
  activeChapterId = null;
}
