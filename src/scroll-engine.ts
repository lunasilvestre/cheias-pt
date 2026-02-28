/**
 * cheias.pt — Scroll engine
 *
 * Uses scrollama for scroll-driven chapter transitions.
 * Manages chapter enter/leave lifecycle and temporal playback.
 */

import scrollama from 'scrollama';
import { gsap } from 'gsap';
import type { Map as MLMap, FilterSpecification } from 'maplibre-gl';
import { BitmapLayer, ScatterplotLayer } from '@deck.gl/layers';
import type { Layer } from '@deck.gl/core';
import type { Chapter, ResolvedChapter, RasterManifest, TemporalConfig } from './types';
import { loadRasterManifest, loadDischargeTimeseries, loadJSON, loadCOG } from './data-loader';
import { ensureLayer, setLayerOpacity, updateSourceData, updateImageSource } from './layer-manager';
import { setDeckOverlayLayers } from './map-setup';
import { compositeUV, createWindParticles, updateWeatherFrame, weatherLayersToArray } from './weather-layers';
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
let ch2SstPlayer: TemporalPlayer | null = null;
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

  // 1. SST temporal animation — 10 weekly COGs at 0.5fps
  try {
    const firstSst = await loadCOG('data/cog/sst/2025-12-01.tif');
    ch2SstBounds = firstSst.bounds;
  } catch (err) {
    console.warn('[scroll-engine] Failed to read SST bounds:', err);
  }

  const sstUrls: string[] = [];
  const sstDates: string[] = [];
  {
    const sstStart = new Date('2025-12-01');
    for (let i = 0; i < 66; i += 7) {
      const d = new Date(sstStart);
      d.setDate(d.getDate() + i);
      const dateStr = d.toISOString().slice(0, 10);
      sstUrls.push(`data/cog/sst/${dateStr}.tif`);
      sstDates.push(dateStr);
    }
  }

  ch2SstPlayer = new TemporalPlayer('chapter-2-sst', {
    id: 'ch2-sst',
    frameType: 'cog',
    mode: 'autoplay',
    fps: 0.5,
    loop: true,
    urls: sstUrls,
    dates: sstDates,
    paletteId: 'sst-diverging',
  });

  ch2SstPlayer.onImage((bitmap) => {
    ch2SstBitmap = bitmap;
    rebuildCh2DeckLayers();
  });

  // Await SST load so frames are ready before timeline starts
  await ch2SstPlayer.load().catch(err => {
    console.warn('[scroll-engine] SST loading failed:', err);
  });

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

  // Start loading IVT frames in background (77 COGs)
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

  if (ch2SstPlayer) {
    ch2SstPlayer.destroy();
    ch2SstPlayer = null;
  }

  if (ch2IvtPlayer) {
    ch2IvtPlayer.destroy();
    ch2IvtPlayer = null;
  }

  // Bitmaps are owned by their TemporalPlayers, released by destroy()
  ch2SstBitmap = null;
  ch2IvtCurrentBitmap = null;

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

  // 0s: SST player starts + fade in 0→0.8 (1.5s)
  ch2Timeline.to(sstProxy, {
    opacity: 0.8,
    duration: 1.5,
    ease: 'power2.out',
    onStart: () => {
      if (ch2SstPlayer) ch2SstPlayer.play();
    },
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

// ── Ch.4 Three Storms — sub-chapter state machine ──

type Ch4Sub = 'kristin' | 'respite' | 'leonardo' | 'marta';

// Sub-chapter state
let ch4ActiveSub: Ch4Sub | null = null;
let ch4SubTimeline: gsap.core.Timeline | null = null;
let ch4SubVersion = 0; // Abort token for async sub-chapter entries
let ch4SatellitePlayer: TemporalPlayer | null = null;

// Lazy synoptic animation state (replaces TemporalPlayer for weather-layers)
let ch4SynopticTimestamps: string[] = [];
let ch4SynopticIndex = 0;
let ch4SynopticRafId: number | null = null;
let ch4SynopticLastTime = 0;
let ch4SynopticPlaying = false;
let ch4SynopticStormName: string | undefined;
const CH4_SYNOPTIC_FPS = 8;
let ch4DeckLayers: Layer[] = [];
let ch4Loading = false;
let ch4Loaded = false;
let ch4DischargeData: Array<{ basin: string; dates: string[]; values: (number | null)[] }> | null = null;

// GSAP opacity proxies
let ch4SynopticOpacity = 0;
let ch4PrecipOpacity = 0;
let ch4SatelliteOpacity = 0;
let ch4WarningOpacity = 0;
let ch4LightningOpacity = 0;

// Precipitation manifest cache
let ch4PrecipFrames: { date: string; url: string }[] | null = null;

// Lightning GeoJSON cache
let ch4LightningFeatures: GeoJSON.Feature[] | null = null;

// Current synoptic bitmap + bounds for deck.gl rendering
let ch4SynopticLayers: Layer[] = [];
let ch4SatelliteBitmap: ImageBitmap | null = null;
let ch4SatelliteBounds: [number, number, number, number] | null = null;

/** Update the date label with hour for synoptic timestamps like 2026-01-28T12 */
function updateDateTimeLabel(timestamp: string): void {
  const el = document.getElementById('temporal-date-label');
  if (!el) return;

  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];

  // Handle YYYY-MM-DDTHH format
  const match = timestamp.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2})/);
  if (match) {
    const day = parseInt(match[3], 10);
    const month = months[parseInt(match[2], 10) - 1];
    const year = match[1];
    const hour = match[4];
    el.textContent = `${day} de ${month} ${year} · ${hour}:00 UTC`;
    return;
  }

  // Fallback to date-only
  updateDateLabel(timestamp);
}

/** Lazy synoptic animation — loads one frame at a time via updateWeatherFrame */
function startSynopticLoop(timestamps: string[], stormName?: string): void {
  ch4SynopticTimestamps = timestamps;
  ch4SynopticIndex = 0;
  ch4SynopticStormName = stormName;
  ch4SynopticPlaying = true;
  ch4SynopticLastTime = performance.now();
  synopticTick(ch4SynopticLastTime);
}

function stopSynopticLoop(): void {
  ch4SynopticPlaying = false;
  if (ch4SynopticRafId !== null) {
    cancelAnimationFrame(ch4SynopticRafId);
    ch4SynopticRafId = null;
  }
  ch4SynopticTimestamps = [];
  ch4SynopticIndex = 0;
  ch4SynopticStormName = undefined;
}

let ch4SynopticLoading = false; // guard against overlapping frame loads

function synopticTick(now: number): void {
  if (!ch4SynopticPlaying) return;

  const interval = 1000 / CH4_SYNOPTIC_FPS;
  if (now - ch4SynopticLastTime >= interval && !ch4SynopticLoading) {
    ch4SynopticLastTime = now;
    const count = ch4SynopticTimestamps.length;
    if (count === 0) return;

    ch4SynopticIndex = (ch4SynopticIndex + 1) % count;
    const ts = ch4SynopticTimestamps[ch4SynopticIndex];

    // Update date label and synced layers
    updateDateTimeLabel(ts);
    const dayDate = timestampToDate(ts);
    updatePrecipFrame(dayDate);
    updateIPMAWarnings(dayDate, ch4SynopticStormName);

    // Load this single frame lazily (3 COGs: MSLP + wind-u + wind-v)
    ch4SynopticLoading = true;
    updateWeatherFrame(ts, 'data/cog').then(set => {
      if (!ch4SynopticPlaying) return; // stale
      ch4SynopticLayers = weatherLayersToArray(set);
      scheduleCh4DeckRebuild();
      ch4SynopticLoading = false;
    }).catch(err => {
      console.warn('[scroll-engine] Synoptic frame load failed:', ts, err);
      ch4SynopticLoading = false;
    });
  }

  ch4SynopticRafId = requestAnimationFrame(synopticTick);
}

/** Throttle Ch.4 deck.gl rebuilds to once per animation frame */
let ch4DeckDirty = false;

function scheduleCh4DeckRebuild(): void {
  if (ch4DeckDirty) return;
  ch4DeckDirty = true;
  requestAnimationFrame(() => {
    ch4DeckDirty = false;
    rebuildCh4DeckLayers();
  });
}

/** Rebuild Ch.4 deck.gl layers from current state */
function rebuildCh4DeckLayers(): void {
  const layers: Layer[] = [];

  // Synoptic weather layers (isobars, particles, H/L, barbs)
  if (ch4SynopticOpacity > 0 && ch4SynopticLayers.length > 0) {
    layers.push(...ch4SynopticLayers);
  }

  // Satellite IR bitmap
  if (ch4SatelliteOpacity > 0 && ch4SatelliteBitmap && ch4SatelliteBounds) {
    layers.push(new BitmapLayer({
      id: 'ch4-satellite-ir',
      image: ch4SatelliteBitmap,
      bounds: ch4SatelliteBounds,
      opacity: ch4SatelliteOpacity,
    }));
  }

  // Lightning scatterplot
  if (ch4LightningOpacity > 0 && ch4LightningFeatures) {
    layers.push(new ScatterplotLayer({
      id: 'ch4-lightning',
      data: ch4LightningFeatures,
      getPosition: (d: GeoJSON.Feature) => (d.geometry as GeoJSON.Point).coordinates as [number, number],
      getRadius: 4000,
      getFillColor: [255, 255, 200, 220],
      getLineColor: [255, 255, 100, 255],
      lineWidthMinPixels: 1,
      stroked: true,
      opacity: ch4LightningOpacity,
      radiusMinPixels: 2,
      radiusMaxPixels: 6,
    }));
  }

  ch4DeckLayers = layers;
  setDeckOverlayLayers(layers);
}

/** Get the nearest daily precipitation date for a given hourly timestamp */
function timestampToDate(timestamp: string): string {
  const match = timestamp.match(/^(\d{4}-\d{2}-\d{2})/);
  return match ? match[1] : timestamp;
}

/** Update IPMA warning choropleth filter to match current date */
function updateIPMAWarnings(dateStr: string, stormName?: string): void {
  if (!map) return;
  const layer = map.getLayer('ipma-warnings');
  if (!layer) return;

  // Filter by date (and optionally storm)
  const dateFilter: FilterSpecification = ['==', ['get', 'date'], dateStr];
  if (stormName) {
    const stormFilter: FilterSpecification = ['==', ['get', 'storm'], stormName];
    map.setFilter('ipma-warnings', ['all', dateFilter, stormFilter]);
  } else {
    map.setFilter('ipma-warnings', dateFilter);
  }
}

/** Update precipitation raster to nearest matching frame */
function updatePrecipFrame(dateStr: string): void {
  if (!map || !ch4PrecipFrames) return;
  // Find exact match or most recent preceding frame
  let best: { date: string; url: string } | undefined;
  for (const f of ch4PrecipFrames) {
    if (f.date === dateStr) { best = f; break; }
    if (f.date <= dateStr) best = f;
  }
  if (best) {
    updateImageSource(map, 'precipitation-raster', `data/${best.url}`);
  }
}

/** Generate hourly timestamps for a date range (inclusive) */
function generateHourlyTimestamps(startDate: string, endDate: string): string[] {
  const timestamps: string[] = [];
  const start = new Date(startDate + 'T00:00:00Z');
  const end = new Date(endDate + 'T23:00:00Z');

  for (let d = new Date(start); d <= end; d.setUTCHours(d.getUTCHours() + 1)) {
    const y = d.getUTCFullYear();
    const m = String(d.getUTCMonth() + 1).padStart(2, '0');
    const day = String(d.getUTCDate()).padStart(2, '0');
    const h = String(d.getUTCHours()).padStart(2, '0');
    timestamps.push(`${y}-${m}-${day}T${h}`);
  }

  return timestamps;
}

/** Generate hourly satellite IR filenames (YYYY-MM-DDTHH-00.tif) */
function generateSatelliteTimestamps(startDate: string, endDate: string): string[] {
  const timestamps: string[] = [];
  const start = new Date(startDate + 'T00:00:00Z');
  const end = new Date(endDate + 'T23:00:00Z');

  for (let d = new Date(start); d <= end; d.setUTCHours(d.getUTCHours() + 1)) {
    const y = d.getUTCFullYear();
    const m = String(d.getUTCMonth() + 1).padStart(2, '0');
    const day = String(d.getUTCDate()).padStart(2, '0');
    const h = String(d.getUTCHours()).padStart(2, '0');
    timestamps.push(`${y}-${m}-${day}T${h}-00`);
  }

  return timestamps;
}

/** Clean up current sub-chapter state */
function cleanupCh4Sub(): void {
  if (ch4SubTimeline) {
    ch4SubTimeline.kill();
    ch4SubTimeline = null;
  }

  // Stop lazy synoptic animation
  stopSynopticLoop();

  if (ch4SatellitePlayer) {
    ch4SatellitePlayer.destroy();
    ch4SatellitePlayer = null;
  }

  ch4SynopticLayers = [];
  if (ch4SatelliteBitmap) {
    ch4SatelliteBitmap.close();
  }
  ch4SatelliteBitmap = null;
  ch4SatelliteBounds = null;
  ch4SynopticOpacity = 0;
  ch4PrecipOpacity = 0;
  ch4SatelliteOpacity = 0;
  ch4WarningOpacity = 0;
  ch4LightningOpacity = 0;
  setDeckOverlayLayers([]);

  // Hide annotation
  const ann = document.getElementById('ch4-annotation');
  if (ann) { ann.classList.remove('visible'); ann.textContent = ''; }

  // Hide sparklines
  const spark = document.getElementById('ch4-sparklines');
  if (spark) { spark.classList.remove('visible'); spark.innerHTML = ''; }

  // Reset MapLibre layer opacities
  if (map) {
    setLayerOpacity(map, 'ipma-warnings', 0);
    setLayerOpacity(map, 'frontal-boundaries', 0);
    setLayerOpacity(map, 'precipitation-raster', 0);
    // Clear IPMA filter
    if (map.getLayer('ipma-warnings')) {
      map.setFilter('ipma-warnings', ['==', ['get', 'date'], '']);
    }
    // Clear frontal boundaries filter
    if (map.getLayer('frontal-boundaries')) {
      map.setFilter('frontal-boundaries', null);
    }
  }
}

/** Determine which sub-chapter based on scroll progress */
function progressToSub(progress: number): Ch4Sub {
  if (progress < 0.3) return 'kristin';
  if (progress < 0.45) return 'respite';
  if (progress < 0.7) return 'leonardo';
  return 'marta';
}

/** Handle sub-chapter transitions based on scroll progress */
function handleChapter4SubChapter(progress: number): void {
  const targetSub = progressToSub(progress);

  if (targetSub !== ch4ActiveSub) {
    cleanupCh4Sub();
    ch4ActiveSub = targetSub;
    ch4SubVersion++;
    const version = ch4SubVersion;

    const enter = async () => {
      switch (targetSub) {
        case 'kristin': await enterKristin(version); break;
        case 'respite': await enterRespite(version); break;
        case 'leonardo': await enterLeonardo(version); break;
        case 'marta': await enterMarta(version); break;
      }
    };
    enter().catch(err => console.warn('[scroll-engine] Sub-chapter entry failed:', err));
  }
}

// ── Sub-chapter: Kristin ──

async function enterKristin(version: number): Promise<void> {
  if (!map) return;

  // Camera: Atlantic view centered on Portugal
  map.easeTo({ center: [-10, 40], zoom: 5.5, pitch: 25, bearing: 0, duration: 2000 });

  // Build Kristin hourly timestamps: Jan 26 00Z → Jan 30 23Z
  const timestamps = generateHourlyTimestamps('2026-01-26', '2026-01-30');

  // Load satellite IR for Kristin (Jan 27-28, 48 frames, for crossfade)
  const satTimestamps = generateSatelliteTimestamps('2026-01-27', '2026-01-28');
  const satUrls = satTimestamps.map(ts => `data/cog/satellite-ir/${ts}.tif`);

  ch4SatellitePlayer = new TemporalPlayer('ch4-satellite', {
    id: 'ch4-satellite',
    frameType: 'cog',
    mode: 'autoplay',
    fps: 4,
    loop: true,
    urls: satUrls,
    dates: satTimestamps,
    paletteId: 'satellite-ir',
  });

  ch4SatellitePlayer.onImage((bitmap) => {
    ch4SatelliteBitmap = bitmap;
    scheduleCh4DeckRebuild();
  });

  // Get satellite bounds from first COG
  try {
    const firstSat = await loadCOG(satUrls[0]);
    if (version !== ch4SubVersion) return; // stale — user scrolled away
    ch4SatelliteBounds = firstSat.bounds;
  } catch (err) {
    console.warn('[scroll-engine] Failed to read satellite IR bounds:', err);
  }

  if (version !== ch4SubVersion) return; // stale — user scrolled away

  // Ensure MapLibre layers
  ensureLayer(map, 'ipma-warnings');
  ensureLayer(map, 'frontal-boundaries');
  ensureLayer(map, 'precipitation-raster');

  // Filter frontal boundaries to Kristin
  if (map.getLayer('frontal-boundaries')) {
    map.setFilter('frontal-boundaries', ['==', ['get', 'storm'], 'Kristin']);
  }

  // Load lightning data
  if (!ch4LightningFeatures) {
    try {
      const geojson = await loadJSON<GeoJSON.FeatureCollection>('data/lightning/lightning-kristin.geojson');
      if (version !== ch4SubVersion) return;
      ch4LightningFeatures = geojson.features;
    } catch (err) {
      console.warn('[scroll-engine] Failed to load lightning data:', err);
    }
  }

  if (version !== ch4SubVersion) return;
  showDateLabel();

  // Load satellite IR frames in background
  ch4SatellitePlayer.load().catch(err => {
    console.warn('[scroll-engine] Satellite IR loading failed:', err);
  });

  // Build GSAP choreography timeline (synoptic loop starts via onStart)
  buildKristinTimeline(timestamps);
}

function buildKristinTimeline(timestamps: string[]): void {
  const synProxy = { opacity: 0 };
  const precipProxy = { opacity: 0 };
  const warningProxy = { opacity: 0 };
  const satProxy = { opacity: 0 };
  const lightningProxy = { opacity: 0 };
  const frontalProxy = { opacity: 0 };

  ch4SubTimeline = gsap.timeline();

  // 0s: Synoptic player starts, isobars/particles fade in (1.5s)
  ch4SubTimeline.to(synProxy, {
    opacity: 0.9,
    duration: 1.5,
    ease: 'power2.out',
    onStart: () => { startSynopticLoop(timestamps, 'Kristin'); },
    onUpdate: () => {
      ch4SynopticOpacity = synProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 0);

  // 1s: Precipitation PNG crossfade in (1.5s)
  ch4SubTimeline.to(precipProxy, {
    opacity: 0.5,
    duration: 1.5,
    ease: 'power2.out',
    onUpdate: () => {
      ch4PrecipOpacity = precipProxy.opacity;
      if (map) setLayerOpacity(map, 'precipitation-raster', ch4PrecipOpacity);
    },
  }, 1);

  // 2.5s: IPMA warnings fade in (1s)
  ch4SubTimeline.to(warningProxy, {
    opacity: 0.12,
    duration: 1,
    ease: 'power2.out',
    onUpdate: () => {
      ch4WarningOpacity = warningProxy.opacity;
      if (map) setLayerOpacity(map, 'ipma-warnings', ch4WarningOpacity);
    },
  }, 2.5);

  // 4s: Frontal boundaries fade in (1s)
  ch4SubTimeline.to(frontalProxy, {
    opacity: 0.8,
    duration: 1,
    ease: 'power2.out',
    onUpdate: () => {
      if (map) setLayerOpacity(map, 'frontal-boundaries', frontalProxy.opacity);
    },
  }, 4);

  // 5.5s: Annotation "CICLOGENESE EXPLOSIVA" (show for 3s)
  ch4SubTimeline.call(() => {
    const ann = document.getElementById('ch4-annotation');
    if (ann) {
      ann.textContent = 'CICLOGENESE EXPLOSIVA';
      ann.classList.add('visible');
    }
  }, undefined, 5.5);
  ch4SubTimeline.call(() => {
    const ann = document.getElementById('ch4-annotation');
    if (ann) ann.classList.remove('visible');
  }, undefined, 8.5);

  // 8s: Satellite IR crossfade IN, synoptic fades OUT (2s)
  ch4SubTimeline.to(satProxy, {
    opacity: 0.9,
    duration: 2,
    ease: 'power2.inOut',
    onStart: () => { if (ch4SatellitePlayer) ch4SatellitePlayer.play(); },
    onUpdate: () => {
      ch4SatelliteOpacity = satProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 8);
  ch4SubTimeline.to(synProxy, {
    opacity: 0,
    duration: 2,
    ease: 'power2.inOut',
    onUpdate: () => {
      ch4SynopticOpacity = synProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 8);

  // 14s: Lightning flashes (ScatterplotLayer)
  ch4SubTimeline.to(lightningProxy, {
    opacity: 0.8,
    duration: 1,
    ease: 'power2.out',
    onUpdate: () => {
      ch4LightningOpacity = lightningProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 14);

  // 18s: Synoptic returns, satellite fades (2s)
  ch4SubTimeline.to(synProxy, {
    opacity: 0.9,
    duration: 2,
    ease: 'power2.inOut',
    onUpdate: () => {
      ch4SynopticOpacity = synProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 18);
  ch4SubTimeline.to(satProxy, {
    opacity: 0,
    duration: 2,
    ease: 'power2.inOut',
    onUpdate: () => {
      ch4SatelliteOpacity = satProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 18);

  // 18s: Lightning fades
  ch4SubTimeline.to(lightningProxy, {
    opacity: 0,
    duration: 1.5,
    ease: 'power2.in',
    onUpdate: () => {
      ch4LightningOpacity = lightningProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 18);
}

// ── Sub-chapter: Respite ──

async function enterRespite(version: number): Promise<void> {
  if (!map) return;

  // Camera: tighter on Portugal
  map.easeTo({ center: [-8.5, 39.5], zoom: 7, pitch: 20, bearing: 0, duration: 2000 });

  // Freeze on Jan 31 — show static MSLP frame
  try {
    const weatherSet = await updateWeatherFrame('2026-01-31T12', 'data/cog');
    if (version !== ch4SubVersion) return;
    ch4SynopticLayers = weatherLayersToArray(weatherSet);
    ch4SynopticOpacity = 0.5;
    scheduleCh4DeckRebuild();
  } catch (err) {
    console.warn('[scroll-engine] Failed to load respite synoptic frame:', err);
  }

  if (version !== ch4SubVersion) return;

  // Set precipitation to Jan 31
  ensureLayer(map, 'precipitation-raster');
  updatePrecipFrame('2026-01-31');
  setLayerOpacity(map, 'precipitation-raster', 0.3);

  showDateLabel();
  updateDateTimeLabel('2026-01-31T12');

  // Annotation
  const ann = document.getElementById('ch4-annotation');
  if (ann) {
    ann.textContent = 'O pior já passou? Não.';
    ann.classList.add('visible');
  }

  // Discharge sparklines
  await renderCh4Sparklines(version);
}

async function renderCh4Sparklines(version: number): Promise<void> {
  const container = document.getElementById('ch4-sparklines');
  if (!container) return;

  if (!ch4DischargeData) {
    try {
      const data = await loadDischargeTimeseries();
      if (version !== ch4SubVersion) return;
      ch4DischargeData = data.stations.map(s => ({
        basin: s.basin,
        dates: s.timeseries.map(t => t.date),
        values: s.timeseries.map(t => t.discharge),
      }));
    } catch (err) {
      console.warn('[scroll-engine] Failed to load discharge data:', err);
      return;
    }
  }

  if (!ch4DischargeData || version !== ch4SubVersion) return;
  container.innerHTML = '';

  const Plot = await import('@observablehq/plot');

  // Show top 5 rivers by peak discharge
  const sorted = [...ch4DischargeData].sort((a, b) => {
    const peakA = Math.max(...(a.values.filter(v => v !== null) as number[]));
    const peakB = Math.max(...(b.values.filter(v => v !== null) as number[]));
    return peakB - peakA;
  }).slice(0, 5);

  for (const river of sorted) {
    const wrapper = document.createElement('div');
    wrapper.className = 'sparkline-item';

    const label = document.createElement('span');
    label.className = 'sparkline-label';
    label.textContent = river.basin;
    wrapper.appendChild(label);

    const plotData = river.dates
      .map((d, i) => ({ date: new Date(d), value: river.values[i] }))
      .filter(d => d.value !== null) as Array<{ date: Date; value: number }>;

    const chart = Plot.plot({
      width: 160,
      height: 36,
      axis: null,
      margin: 0,
      marginLeft: 0,
      marginRight: 0,
      marginTop: 2,
      marginBottom: 2,
      style: { background: 'transparent' },
      marks: [
        Plot.line(plotData, {
          x: 'date',
          y: 'value',
          stroke: '#3498db',
          strokeWidth: 1.5,
        }),
        // Mark Jan 28 (Kristin peak)
        Plot.ruleX([new Date('2026-01-28')], {
          stroke: '#ff6464',
          strokeWidth: 1,
          strokeDasharray: '3,2',
          strokeOpacity: 0.6,
        }),
      ],
    });

    wrapper.appendChild(chart);
    container.appendChild(wrapper);
  }

  container.classList.add('visible');
}

// ── Sub-chapter: Leonardo ──

async function enterLeonardo(version: number): Promise<void> {
  if (!map) return;

  // Camera: Atlantic view
  map.easeTo({ center: [-10, 40], zoom: 5.5, pitch: 25, bearing: 0, duration: 2000 });

  // Leonardo timestamps: Feb 4 00Z → Feb 8 23Z
  const timestamps = generateHourlyTimestamps('2026-02-04', '2026-02-08');

  // Satellite IR for Leonardo (Feb 4-8, 97 frames)
  const satTimestamps = generateSatelliteTimestamps('2026-02-04', '2026-02-08');
  const satUrls = satTimestamps.map(ts => `data/cog/satellite-ir/${ts}.tif`);

  ch4SatellitePlayer = new TemporalPlayer('ch4-satellite-leo', {
    id: 'ch4-satellite-leo',
    frameType: 'cog',
    mode: 'autoplay',
    fps: 4,
    loop: true,
    urls: satUrls,
    dates: satTimestamps,
    paletteId: 'satellite-ir',
  });

  ch4SatellitePlayer.onImage((bitmap) => {
    ch4SatelliteBitmap = bitmap;
    scheduleCh4DeckRebuild();
  });

  try {
    const firstSat = await loadCOG(satUrls[0]);
    if (version !== ch4SubVersion) return;
    ch4SatelliteBounds = firstSat.bounds;
  } catch (err) {
    console.warn('[scroll-engine] Failed to read Leonardo satellite bounds:', err);
  }

  if (version !== ch4SubVersion) return;

  // Ensure MapLibre layers
  ensureLayer(map, 'ipma-warnings');
  ensureLayer(map, 'frontal-boundaries');
  ensureLayer(map, 'precipitation-raster');

  // Filter frontal boundaries to Leonardo (warm front)
  if (map.getLayer('frontal-boundaries')) {
    map.setFilter('frontal-boundaries', ['==', ['get', 'storm'], 'Leonardo']);
  }

  showDateLabel();

  ch4SatellitePlayer.load().catch(err => {
    console.warn('[scroll-engine] Leonardo satellite loading failed:', err);
  });

  // Build GSAP choreography timeline (synoptic loop starts via onStart)
  buildLeonardoTimeline(timestamps);
}

function buildLeonardoTimeline(timestamps: string[]): void {
  const synProxy = { opacity: 0 };
  const precipProxy = { opacity: 0 };
  const warningProxy = { opacity: 0 };
  const satProxy = { opacity: 0 };
  const frontalProxy = { opacity: 0 };

  ch4SubTimeline = gsap.timeline();

  // 0s: Synoptic starts, fade in (1.5s)
  ch4SubTimeline.to(synProxy, {
    opacity: 0.9,
    duration: 1.5,
    ease: 'power2.out',
    onStart: () => { startSynopticLoop(timestamps, 'Leonardo'); },
    onUpdate: () => {
      ch4SynopticOpacity = synProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 0);

  // 1s: Precipitation fade in (1.5s)
  ch4SubTimeline.to(precipProxy, {
    opacity: 0.5,
    duration: 1.5,
    ease: 'power2.out',
    onUpdate: () => {
      ch4PrecipOpacity = precipProxy.opacity;
      if (map) setLayerOpacity(map, 'precipitation-raster', ch4PrecipOpacity);
    },
  }, 1);

  // 2.5s: IPMA warnings escalate to red (1s)
  ch4SubTimeline.to(warningProxy, {
    opacity: 0.15,
    duration: 1,
    ease: 'power2.out',
    onUpdate: () => {
      ch4WarningOpacity = warningProxy.opacity;
      if (map) setLayerOpacity(map, 'ipma-warnings', ch4WarningOpacity);
    },
  }, 2.5);

  // 4s: Warm front line fades in (1s)
  ch4SubTimeline.to(frontalProxy, {
    opacity: 0.8,
    duration: 1,
    ease: 'power2.out',
    onUpdate: () => {
      if (map) setLayerOpacity(map, 'frontal-boundaries', frontalProxy.opacity);
    },
  }, 4);

  // 6s: Camera push to Portugal
  ch4SubTimeline.call(() => {
    map?.easeTo({ center: [-9, 40], zoom: 7, duration: 4000, essential: true });
  }, undefined, 6);

  // 9s: Satellite IR crossfade IN, synoptic fades (2s)
  ch4SubTimeline.to(satProxy, {
    opacity: 0.9,
    duration: 2,
    ease: 'power2.inOut',
    onStart: () => { if (ch4SatellitePlayer) ch4SatellitePlayer.play(); },
    onUpdate: () => {
      ch4SatelliteOpacity = satProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 9);
  ch4SubTimeline.to(synProxy, {
    opacity: 0,
    duration: 2,
    ease: 'power2.inOut',
    onUpdate: () => {
      ch4SynopticOpacity = synProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 9);

  // 15s: Satellite fades, synoptic returns (2s)
  ch4SubTimeline.to(synProxy, {
    opacity: 0.9,
    duration: 2,
    ease: 'power2.inOut',
    onUpdate: () => {
      ch4SynopticOpacity = synProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 15);
  ch4SubTimeline.to(satProxy, {
    opacity: 0,
    duration: 2,
    ease: 'power2.inOut',
    onUpdate: () => {
      ch4SatelliteOpacity = satProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 15);
}

// ── Sub-chapter: Marta ──

async function enterMarta(version: number): Promise<void> {
  if (!map) return;

  // Camera: tight on Portugal
  map.easeTo({ center: [-9, 39.5], zoom: 7.5, pitch: 30, bearing: 0, duration: 2000 });

  // Marta timestamps: Feb 9 00Z → Feb 12 23Z
  const timestamps = generateHourlyTimestamps('2026-02-09', '2026-02-12');

  // Satellite IR for Marta (Feb 9-12, 73 frames)
  const satTimestamps = generateSatelliteTimestamps('2026-02-09', '2026-02-12');
  const satUrls = satTimestamps.map(ts => `data/cog/satellite-ir/${ts}.tif`);

  ch4SatellitePlayer = new TemporalPlayer('ch4-satellite-marta', {
    id: 'ch4-satellite-marta',
    frameType: 'cog',
    mode: 'autoplay',
    fps: 4,
    loop: true,
    urls: satUrls,
    dates: satTimestamps,
    paletteId: 'satellite-ir',
  });

  ch4SatellitePlayer.onImage((bitmap) => {
    ch4SatelliteBitmap = bitmap;
    scheduleCh4DeckRebuild();
  });

  try {
    const firstSat = await loadCOG(satUrls[0]);
    if (version !== ch4SubVersion) return;
    ch4SatelliteBounds = firstSat.bounds;
  } catch (err) {
    console.warn('[scroll-engine] Failed to read Marta satellite bounds:', err);
  }

  if (version !== ch4SubVersion) return;

  // Ensure MapLibre layers
  ensureLayer(map, 'ipma-warnings');
  ensureLayer(map, 'frontal-boundaries');
  ensureLayer(map, 'precipitation-raster');

  // Filter frontal boundaries to Marta (cold front)
  if (map.getLayer('frontal-boundaries')) {
    map.setFilter('frontal-boundaries', ['==', ['get', 'storm'], 'Marta']);
  }

  showDateLabel();

  ch4SatellitePlayer.load().catch(err => {
    console.warn('[scroll-engine] Marta satellite loading failed:', err);
  });

  // Build GSAP choreography timeline (synoptic loop starts via onStart)
  buildMartaTimeline(timestamps);
}

function buildMartaTimeline(timestamps: string[]): void {
  const synProxy = { opacity: 0 };
  const precipProxy = { opacity: 0 };
  const warningProxy = { opacity: 0 };
  const satProxy = { opacity: 0 };
  const frontalProxy = { opacity: 0 };

  ch4SubTimeline = gsap.timeline();

  // 0s: Synoptic starts, all layers fade in simultaneously for maximum impact
  ch4SubTimeline.to(synProxy, {
    opacity: 0.9,
    duration: 1.5,
    ease: 'power2.out',
    onStart: () => { startSynopticLoop(timestamps, 'Marta'); },
    onUpdate: () => {
      ch4SynopticOpacity = synProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 0);

  // 0.5s: Precipitation immediately (full composite)
  ch4SubTimeline.to(precipProxy, {
    opacity: 0.5,
    duration: 1.5,
    ease: 'power2.out',
    onUpdate: () => {
      ch4PrecipOpacity = precipProxy.opacity;
      if (map) setLayerOpacity(map, 'precipitation-raster', ch4PrecipOpacity);
    },
  }, 0.5);

  // 1s: IPMA warnings — all red
  ch4SubTimeline.to(warningProxy, {
    opacity: 0.15,
    duration: 1,
    ease: 'power2.out',
    onUpdate: () => {
      ch4WarningOpacity = warningProxy.opacity;
      if (map) setLayerOpacity(map, 'ipma-warnings', ch4WarningOpacity);
    },
  }, 1);

  // 2s: Cold front line
  ch4SubTimeline.to(frontalProxy, {
    opacity: 0.8,
    duration: 1,
    ease: 'power2.out',
    onUpdate: () => {
      if (map) setLayerOpacity(map, 'frontal-boundaries', frontalProxy.opacity);
    },
  }, 2);

  // 6s: Satellite IR crossfade (2s)
  ch4SubTimeline.to(satProxy, {
    opacity: 0.9,
    duration: 2,
    ease: 'power2.inOut',
    onStart: () => { if (ch4SatellitePlayer) ch4SatellitePlayer.play(); },
    onUpdate: () => {
      ch4SatelliteOpacity = satProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 6);
  ch4SubTimeline.to(synProxy, {
    opacity: 0.2,
    duration: 2,
    ease: 'power2.inOut',
    onUpdate: () => {
      ch4SynopticOpacity = synProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 6);

  // 12s: Return to full synoptic composite (2s)
  ch4SubTimeline.to(synProxy, {
    opacity: 0.9,
    duration: 2,
    ease: 'power2.inOut',
    onUpdate: () => {
      ch4SynopticOpacity = synProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 12);
  ch4SubTimeline.to(satProxy, {
    opacity: 0,
    duration: 2,
    ease: 'power2.inOut',
    onUpdate: () => {
      ch4SatelliteOpacity = satProxy.opacity;
      scheduleCh4DeckRebuild();
    },
  }, 12);
}

// ── Ch.4 master entry/exit ──

export async function enterChapter4(): Promise<void> {
  if (!map || ch4Loading) return;
  ch4Loading = true;

  // Clean up previous state
  cleanupCh4Sub();
  ch4ActiveSub = null;

  // Pre-load precipitation manifest
  if (!ch4PrecipFrames) {
    try {
      const manifest = await loadRasterManifest();
      ch4PrecipFrames = manifest.precipitation.frames;
    } catch (err) {
      console.warn('[scroll-engine] Failed to load precip manifest:', err);
    }
  }

  // Ensure layers are registered
  ensureLayer(map, 'ipma-warnings');
  ensureLayer(map, 'frontal-boundaries');
  ensureLayer(map, 'precipitation-raster');

  ch4Loaded = true;
  ch4Loading = false;

  // Start with Kristin (first sub-chapter)
  ch4ActiveSub = 'kristin';
  ch4SubVersion++;
  enterKristin(ch4SubVersion).catch(err => {
    console.warn('[scroll-engine] Initial Kristin entry failed:', err);
  });
}

export function leaveChapter4(): void {
  cleanupCh4Sub();
  ch4ActiveSub = null;
  ch4Loaded = false;
  ch4Loading = false;
  hideDateLabel();
}

export async function enterChapter5(): Promise<void> {
  if (!map) return;
  if (ch4Loaded) leaveChapter4();

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

      // Ch.4 sub-chapter state machine
      if (chapterId === 'chapter-4' && ch4Loaded) {
        handleChapter4SubChapter(response.progress);
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
