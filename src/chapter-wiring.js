/**
 * cheias.pt — Chapter wiring for Chapters 3, 4, 5, 9
 *
 * Connects data loading, temporal player, and map layers.
 * Ch3/Ch4: Pre-rendered PNG raster animation via MapLibre image sources.
 * Ch5: Frozen raster snapshot + discharge points.
 * Ch9: Ensures titiler tile layers for explore mode.
 */

import { loadRasterManifest, loadDischargeTimeseries } from './data-loader.js';
import { setFrames, setProgress, onFrame, reset as resetPlayer } from './temporal-player.js';
import { ensureLayer, updateSourceData, updateImageSource } from './layer-manager.js';
import { onChapterProgress, offChapterProgress } from './scroll-observer.js';

let map = null;
let ch3Initialized = false;
let ch4Initialized = false;

/** Track preloaded image URLs to avoid duplicate fetches */
const preloadedUrls = new Set();

/**
 * Preload PNG images into browser cache for smooth animation.
 * @param {Array<{date: string, url: string}>} frames
 */
function preloadImages(frames) {
  for (const frame of frames) {
    const url = `data/${frame.url}`;
    if (preloadedUrls.has(url)) continue;
    preloadedUrls.add(url);
    const img = new Image();
    img.src = url;
  }
}

/**
 * Initialize chapter wiring with the map instance.
 */
export function initChapterWiring(mapInstance) {
  map = mapInstance;
}

/**
 * Show/hide the shared temporal date label.
 */
function showDateLabel() {
  const el = document.getElementById('temporal-date-label');
  if (el) el.classList.add('visible');
}

function hideDateLabel() {
  const el = document.getElementById('temporal-date-label');
  if (el) {
    el.classList.remove('visible');
    el.textContent = '';
  }
}

/**
 * Update the shared temporal date label.
 */
function updateDateLabel(dateStr) {
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

/**
 * Called when Chapter 3 (soil moisture animation) becomes active.
 * Uses pre-rendered PNG frames via MapLibre image source.
 */
export async function enterChapter3() {
  if (!map) return;

  const manifest = await loadRasterManifest();
  const smFrames = manifest.soil_moisture.frames;

  ensureLayer(map, 'soil-moisture-raster');

  setFrames(smFrames);

  // Preload first batch of images
  preloadImages(smFrames.slice(0, 15));

  onFrame((frame, idx) => {
    if (!map) return;
    updateImageSource(map, 'soil-moisture-raster', `data/${frame.url}`);
    updateDateLabel(frame.date);
    // Preload ahead
    preloadImages(smFrames.slice(idx + 1, idx + 11));
  });

  // Show first frame
  if (smFrames.length > 0) {
    updateImageSource(map, 'soil-moisture-raster', `data/${smFrames[0].url}`);
    updateDateLabel(smFrames[0].date);
  }

  onChapterProgress('chapter-3', (progress) => {
    setProgress(progress);
  });

  showDateLabel();
  ch3Initialized = true;
}

/**
 * Called when leaving Chapter 3.
 */
export function leaveChapter3() {
  offChapterProgress('chapter-3');
  resetPlayer();
  hideDateLabel();
  ch3Initialized = false;
}

/**
 * Called when Chapter 4 (precipitation temporal animation) becomes active.
 * Uses pre-rendered PNG frames via MapLibre image source.
 */
export async function enterChapter4() {
  if (!map) return;

  if (ch3Initialized) leaveChapter3();

  const manifest = await loadRasterManifest();
  const precipFrames = manifest.precipitation.frames;

  ensureLayer(map, 'precipitation-raster');

  setFrames(precipFrames);

  // Preload first batch of images
  preloadImages(precipFrames.slice(0, 15));

  onFrame((frame, idx) => {
    if (!map) return;
    updateImageSource(map, 'precipitation-raster', `data/${frame.url}`);
    updateDateLabel(frame.date);
    // Preload ahead
    preloadImages(precipFrames.slice(idx + 1, idx + 11));
  });

  // Show first frame
  if (precipFrames.length > 0) {
    updateImageSource(map, 'precipitation-raster', `data/${precipFrames[0].url}`);
    updateDateLabel(precipFrames[0].date);
  }

  onChapterProgress('chapter-4', (progress) => {
    setProgress(progress);
  });

  showDateLabel();
  ch4Initialized = true;
}

/**
 * Called when leaving Chapter 4.
 */
export function leaveChapter4() {
  offChapterProgress('chapter-4');
  resetPlayer();
  hideDateLabel();
  ch4Initialized = false;
}

/**
 * Called when Chapter 5 (discharge) becomes active.
 * Shows frozen soil moisture raster at Jan 28 + discharge circles.
 */
export async function enterChapter5() {
  if (!map) return;

  if (ch4Initialized) leaveChapter4();

  // Frozen soil moisture raster at Jan 28
  const manifest = await loadRasterManifest();
  ensureLayer(map, 'soil-moisture-raster');
  const jan28Frame = manifest.soil_moisture.frames.find(f => f.date === '2026-01-28');
  if (jan28Frame) {
    updateImageSource(map, 'soil-moisture-raster', `data/${jan28Frame.url}`);
  }

  // Discharge circles + river labels
  const data = await loadDischargeTimeseries();
  const features = data.stations.map(station => {
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

/**
 * Called when Chapter 9 (explore) becomes active.
 * Ensures titiler tile layers and other explore-mode layers exist.
 */
export async function enterChapter9() {
  if (!map) return;

  // Clean up any active temporal chapters
  if (ch3Initialized) leaveChapter3();
  if (ch4Initialized) leaveChapter4();

  // Ensure titiler tile layers exist (toggled by exploration-mode.js)
  ensureLayer(map, 'soil-moisture-tiles');
  ensureLayer(map, 'precipitation-tiles');
  ensureLayer(map, 'flood-extent-polygons');
  ensureLayer(map, 'glofas-discharge');
  ensureLayer(map, 'basins-outline');
}
