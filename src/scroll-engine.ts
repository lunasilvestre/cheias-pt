/**
 * cheias.pt — Scroll engine
 *
 * Uses scrollama for scroll-driven chapter transitions.
 * Manages chapter enter/leave lifecycle and temporal playback.
 */

import scrollama from 'scrollama';
import { gsap } from 'gsap';
import type { Map as MLMap } from 'maplibre-gl';
import { BitmapLayer } from '@deck.gl/layers';
import type { Layer } from '@deck.gl/core';
import type { Chapter, ResolvedChapter, RasterManifest, TemporalConfig } from './types';
import { loadRasterManifest, loadDischargeTimeseries, loadJSON, loadCOG, applyColormap, rasterToImageBitmap } from './data-loader';
import { ensureLayer, setLayerOpacity, updateSourceData, updateImageSource } from './layer-manager';
import { setDeckOverlayLayers } from './map-setup';
import { compositeUV, createWindParticles } from './weather-layers';
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

// Ch.1 GSAP timeline choreography
let ch1Timeline: gsap.core.Timeline | null = null;

export function enterChapter1(): void {
  if (!map) return;
  ensureLayer(map, 'sentinel1-flood-extent');

  const proxy = { opacity: 0 };
  ch1Timeline = gsap.timeline();
  ch1Timeline.to(proxy, {
    opacity: 0.7,
    duration: 2,
    ease: 'power2.out',
    onUpdate: () => {
      if (map) setLayerOpacity(map, 'sentinel1-flood-extent', proxy.opacity);
    },
  });
}

export function leaveChapter1(): void {
  if (ch1Timeline) {
    ch1Timeline.kill();
    ch1Timeline = null;
  }
  if (!map) return;

  const proxy = { opacity: 0.7 };
  gsap.to(proxy, {
    opacity: 0,
    duration: 1,
    ease: 'power2.in',
    onUpdate: () => {
      if (map) setLayerOpacity(map, 'sentinel1-flood-extent', proxy.opacity);
    },
  });
}

// ── Ch.2 Atlantic Engine ──

let ch2Timeline: gsap.core.Timeline | null = null;
let ch2IvtPlayer: TemporalPlayer | null = null;
let ch2WindLayer: Layer | null = null;
let ch2SstBitmap: ImageBitmap | null = null;
let ch2SstBounds: [number, number, number, number] | null = null;
let ch2IvtBounds: [number, number, number, number] | null = null;
let ch2IvtCurrentBitmap: ImageBitmap | null = null;
let ch2Loaded = false;
let ch2Loading = false;
let ch2SstOpacity = 0;
let ch2IvtOpacity = 0;
let ch2WindVisible = false;

/** Rebuild the deck.gl layer array from current Ch.2 state and push to overlay. */
function rebuildCh2DeckLayers(): void {
  const layers: Layer[] = [];

  if (ch2SstBitmap && ch2SstBounds) {
    layers.push(new BitmapLayer({
      id: 'ch2-sst',
      image: ch2SstBitmap,
      bounds: ch2SstBounds,
      opacity: ch2SstOpacity,
    }));
  }

  if (ch2IvtCurrentBitmap && ch2IvtBounds) {
    layers.push(new BitmapLayer({
      id: 'ch2-ivt',
      image: ch2IvtCurrentBitmap,
      bounds: ch2IvtBounds,
      opacity: ch2IvtOpacity,
    }));
  }

  if (ch2WindLayer && ch2WindVisible) {
    layers.push(ch2WindLayer);
  }

  setDeckOverlayLayers(layers);
}

export async function enterChapter2(): Promise<void> {
  if (!map || ch2Loading) return;
  ch2Loading = true;

  // Clean up any leftover state
  leaveChapter2();
  ch2Loading = true; // re-set after leaveChapter2 clears it

  // Ensure MapLibre storm track layers are registered
  ensureLayer(map, 'storm-tracks');
  ensureLayer(map, 'storm-track-labels');

  // 1. Load SST COG (single representative mid-January frame)
  try {
    const sstRaster = await loadCOG('data/cog/sst/2026-01-15.tif');
    const sstImageData = applyColormap(sstRaster, 'sst-diverging');
    ch2SstBitmap = await rasterToImageBitmap(sstImageData);
    ch2SstBounds = sstRaster.bounds;
    rebuildCh2DeckLayers();
  } catch (err) {
    console.warn('[scroll-engine] Failed to load SST COG:', err);
  }

  // 2. Get IVT bounds from first COG, then create TemporalPlayer
  try {
    const firstIvt = await loadCOG('data/cog/ivt/2025-12-01.tif');
    ch2IvtBounds = firstIvt.bounds;
  } catch (err) {
    console.warn('[scroll-engine] Failed to read IVT bounds:', err);
    ch2IvtBounds = ch2SstBounds; // fallback
  }

  // Build IVT frame URLs (77 daily COGs Dec 1 → Feb 15)
  const ivtUrls: string[] = [];
  const ivtDates: string[] = [];
  const startDate = new Date('2025-12-01');
  for (let i = 0; i < 77; i++) {
    const d = new Date(startDate);
    d.setDate(d.getDate() + i);
    const dateStr = d.toISOString().slice(0, 10);
    ivtUrls.push(`data/cog/ivt/${dateStr}.tif`);
    ivtDates.push(dateStr);
  }

  ch2IvtPlayer = new TemporalPlayer('chapter-2-ivt', {
    id: 'ch2-ivt',
    frameType: 'cog',
    mode: 'autoplay',
    fps: 2,
    loop: true,
    urls: ivtUrls,
    dates: ivtDates,
    paletteId: 'ivt-sequential',
  });

  ch2IvtPlayer.onImage((bitmap) => {
    ch2IvtCurrentBitmap = bitmap;
    rebuildCh2DeckLayers();
  });

  ch2IvtPlayer.onFrame((_idx, date) => {
    if (date) updateDateLabel(date);
  });

  // Start loading IVT frames in background (78 COGs)
  ch2IvtPlayer.load().catch(err => {
    console.warn('[scroll-engine] IVT loading failed:', err);
  });

  // 3. Load wind particle field (Kristin peak, static)
  try {
    const [windU, windV] = await Promise.all([
      loadCOG('data/cog/wind-u/2026-01-28T12.tif'),
      loadCOG('data/cog/wind-v/2026-01-28T12.tif'),
    ]);
    const windData = compositeUV(windU, windV);
    ch2WindLayer = createWindParticles(windData, windU.bounds, 'ch2-wind');
  } catch (err) {
    console.warn('[scroll-engine] Failed to load wind COGs:', err);
  }

  ch2Loaded = true;
  ch2Loading = false;
  showDateLabel();
  buildChapter2Timeline();
}

export function leaveChapter2(): void {
  if (ch2Timeline) {
    ch2Timeline.kill();
    ch2Timeline = null;
  }

  if (ch2IvtPlayer) {
    ch2IvtPlayer.destroy();
    ch2IvtPlayer = null;
  }

  // Release ImageBitmap GPU resources
  if (ch2SstBitmap) {
    ch2SstBitmap.close();
    ch2SstBitmap = null;
  }
  ch2IvtCurrentBitmap = null; // owned by TemporalPlayer, closed by its destroy()

  ch2WindLayer = null;
  ch2SstBounds = null;
  ch2IvtBounds = null;
  ch2SstOpacity = 0;
  ch2IvtOpacity = 0;
  ch2WindVisible = false;
  ch2Loaded = false;
  ch2Loading = false;
  setDeckOverlayLayers([]);

  if (map) {
    setLayerOpacity(map, 'storm-tracks', 0);
    setLayerOpacity(map, 'storm-track-labels', 0);
  }

  hideDateLabel();
}

/** Build the Ch.2 GSAP timeline that choreographs all layer reveals. */
function buildChapter2Timeline(): void {
  if (!map) return;

  ch2Timeline = gsap.timeline();
  const sstProxy = { opacity: 0 };
  const stormProxy = { opacity: 0 };
  const bearingProxy = { value: 0 };
  const ivtProxy = { opacity: 0 };
  const windProxy = { opacity: 0 };

  // 0s: SST fade in 0→0.8 (1.5s)
  ch2Timeline.to(sstProxy, {
    opacity: 0.8,
    duration: 1.5,
    ease: 'power2.out',
    onUpdate: () => {
      ch2SstOpacity = sstProxy.opacity;
      rebuildCh2DeckLayers();
    },
  }, 0);

  // +0.5s: Storm tracks fade in 0→0.9 (1s)
  ch2Timeline.to(stormProxy, {
    opacity: 0.9,
    duration: 1,
    ease: 'power2.out',
    onUpdate: () => {
      if (map) {
        setLayerOpacity(map, 'storm-tracks', stormProxy.opacity);
        setLayerOpacity(map, 'storm-track-labels', stormProxy.opacity);
      }
    },
  }, 0.5);

  // +1s: Globe bearing rotation 0→5 (2s)
  ch2Timeline.to(bearingProxy, {
    value: 5,
    duration: 2,
    ease: 'power2.out',
    onUpdate: () => {
      map?.easeTo({ bearing: bearingProxy.value, duration: 0 });
    },
  }, 1);

  // +2s: IVT player starts, opacity 0→0.7 (1s)
  ch2Timeline.to(ivtProxy, {
    opacity: 0.7,
    duration: 1,
    ease: 'power2.out',
    onStart: () => {
      if (ch2IvtPlayer) ch2IvtPlayer.play();
    },
    onUpdate: () => {
      ch2IvtOpacity = ivtProxy.opacity;
      rebuildCh2DeckLayers();
    },
  }, 2);

  // +3s: Wind particles visible, opacity 0→1 (1s)
  ch2Timeline.to(windProxy, {
    opacity: 1,
    duration: 1,
    ease: 'power2.out',
    onStart: () => {
      ch2WindVisible = true;
    },
    onUpdate: () => {
      rebuildCh2DeckLayers();
    },
  }, 3);

  // +6s: Camera push toward Portugal (4s)
  ch2Timeline.call(() => {
    map?.easeTo({
      center: [-15, 38],
      zoom: 3.5,
      duration: 4000,
      essential: true,
    });
  }, undefined, 6);
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
