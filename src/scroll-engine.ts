/**
 * cheias.pt — Scroll engine
 *
 * Uses scrollama for scroll-driven chapter transitions.
 * Manages chapter enter/leave lifecycle and temporal playback.
 */

import scrollama from 'scrollama';
import { gsap } from 'gsap';
import type { Map as MLMap } from 'maplibre-gl';
import type { Chapter, ResolvedChapter, RasterManifest, TemporalConfig } from './types';
import { loadRasterManifest, loadDischargeTimeseries, loadJSON } from './data-loader';
import { ensureLayer, setLayerOpacity, updateSourceData, updateImageSource } from './layer-manager';
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

// Ch.0 ghost flood pulse state
let ghostPulseTween: gsap.core.Tween | null = null;

export function enterChapter0(): void {
  if (!map) return;
  ensureLayer(map, 'ghost-flood-pulse');
  const pulse = { opacity: 0 };
  ghostPulseTween = gsap.to(pulse, {
    opacity: 0.03,
    duration: 2,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
    repeatDelay: 2,
    onUpdate: () => {
      if (map) setLayerOpacity(map, 'ghost-flood-pulse', pulse.opacity);
    },
  });
}

export function leaveChapter0(): void {
  if (ghostPulseTween) {
    ghostPulseTween.kill();
    ghostPulseTween = null;
  }
  if (map) setLayerOpacity(map, 'ghost-flood-pulse', 0);
}

// Ch.1 scroll-driven opacity (driven from onStepProgress)
function handleChapter1Progress(progress: number): void {
  if (!map) return;
  let opacity: number;
  if (progress < 0.2) {
    opacity = 0;
  } else if (progress < 0.4) {
    opacity = ((progress - 0.2) / 0.2) * 0.7;
  } else if (progress < 0.8) {
    opacity = 0.7;
  } else {
    opacity = 0.7 * (1 - (progress - 0.8) / 0.2);
  }
  setLayerOpacity(map, 'sentinel1-flood-extent', opacity);
}

// Ch.3 sparkline + wildfire + percentile + precipitation state
let ch3SparklineData: Array<{ basin: string; dates: string[]; values: (number | null)[] }> | null = null;

function handleChapter3Progress(progress: number): void {
  if (!map) return;

  // Wildfire foreshadow at 0.5
  const burnOpacity = progress >= 0.5 ? 0.15 : 0;
  setLayerOpacity(map, 'wildfires-burn-scars', burnOpacity);

  // Percentile annotation at 0.7
  const percentileEl = document.getElementById('ch3-percentile');
  if (percentileEl) {
    if (progress >= 0.7 && progress < 0.85) {
      percentileEl.classList.add('visible');
    } else {
      percentileEl.classList.remove('visible');
    }
  }

  // Precipitation transition at 0.8-1.0
  if (progress >= 0.8) {
    ensureLayer(map, 'precipitation-raster');
    const transitionProgress = (progress - 0.8) / 0.2;
    setLayerOpacity(map, 'soil-moisture-raster', 0.8 - transitionProgress * 0.5);
    setLayerOpacity(map, 'precipitation-raster', transitionProgress * 0.4);
  } else {
    setLayerOpacity(map, 'precipitation-raster', 0);
  }
}

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

  // Wire frame updates to MapLibre image source + in-card date label
  player.onFrame((idx, date) => {
    if (!map) return;
    const frame = smFrames[idx];
    if (frame) {
      updateImageSource(map, 'soil-moisture-raster', `data/${frame.url}`);
    }
    if (date) {
      updateDateLabel(date);
      const cardDate = document.getElementById('ch3-date-label');
      if (cardDate) cardDate.textContent = formatDateLabelPT(date);
    }
  });

  // Set initial frame
  if (smFrames.length > 0) {
    updateImageSource(map, 'soil-moisture-raster', `data/${smFrames[0].url}`);
    updateDateLabel(smFrames[0].date);
  }

  showDateLabel();

  // Ensure wildfire layer is registered for foreshadow
  ensureLayer(map, 'wildfires-burn-scars');

  // Load and render sparklines
  renderSparklines();

  // Set precipitation to Jan 27-28 frame for crossfade transition
  ensureLayer(map, 'precipitation-raster');
  const precipFrames = manifest.precipitation.frames;
  const jan28Precip = precipFrames.find(f => f.date === '2026-01-28') || precipFrames[precipFrames.length - 1];
  if (jan28Precip) {
    updateImageSource(map, 'precipitation-raster', `data/${jan28Precip.url}`);
  }
}

export function leaveChapter3(): void {
  destroyPlayer('chapter-3');
  hideDateLabel();
  if (map) {
    setLayerOpacity(map, 'wildfires-burn-scars', 0);
    setLayerOpacity(map, 'precipitation-raster', 0);
  }
  // Clear sparkline container
  const container = document.getElementById('ch3-sparklines');
  if (container) container.innerHTML = '';
  // Hide percentile annotation
  const percentileEl = document.getElementById('ch3-percentile');
  if (percentileEl) percentileEl.classList.remove('visible');
}

// ── Sparkline rendering ──

async function renderSparklines(): Promise<void> {
  const container = document.getElementById('ch3-sparklines');
  if (!container) return;

  if (!ch3SparklineData) {
    try {
      ch3SparklineData = await loadJSON<typeof ch3SparklineData>('data/frontend/sm-basin-timeseries.json');
    } catch (err) {
      console.warn('[scroll-engine] Failed to load sparkline data:', err);
      return;
    }
  }

  if (!ch3SparklineData) return;
  container.innerHTML = '';

  const Plot = await import('@observablehq/plot');

  for (const basin of ch3SparklineData) {
    const wrapper = document.createElement('div');
    wrapper.className = 'sparkline-item';

    const label = document.createElement('span');
    label.className = 'sparkline-label';
    label.textContent = basin.basin;
    wrapper.appendChild(label);

    const plotData = basin.dates
      .map((d, i) => ({ date: new Date(d), value: basin.values[i] }))
      .filter(d => d.value !== null) as Array<{ date: Date; value: number }>;

    const chart = Plot.plot({
      width: 200,
      height: 48,
      axis: null,
      margin: 0,
      marginLeft: 0,
      marginRight: 0,
      marginTop: 4,
      marginBottom: 4,
      style: { background: 'transparent' },
      y: { domain: [0.4, 1] },
      marks: [
        Plot.line(plotData, {
          x: 'date',
          y: 'value',
          stroke: '#3498db',
          strokeWidth: 1.5,
        }),
      ],
    });

    wrapper.appendChild(chart);
    container.appendChild(wrapper);
  }
}

function formatDateLabelPT(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];
  return `${d.getDate()} de ${months[d.getMonth()]} ${d.getFullYear()}`;
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

      // Ch.1 scroll-driven flood opacity
      if (chapterId === 'chapter-1') {
        handleChapter1Progress(response.progress);
      }

      // Ch.3 wildfire foreshadow + percentile + precipitation transition
      if (chapterId === 'chapter-3') {
        handleChapter3Progress(response.progress);
      }

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
