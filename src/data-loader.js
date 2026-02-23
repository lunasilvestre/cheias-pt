/**
 * cheias.pt — Data loader
 *
 * Fetches and caches frontend JSON files.
 * All data is pre-processed; no runtime API calls.
 */

const cache = {};

export async function loadJSON(url) {
  if (cache[url]) return cache[url];
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to load ${url}: ${resp.status}`);
  const data = await resp.json();
  cache[url] = data;
  return data;
}

export const loadSoilMoistureFrames = () => loadJSON('data/frontend/soil-moisture-frames.json');
export const loadPrecipStormTotals = () => loadJSON('data/frontend/precip-storm-totals.json');
export const loadPrecipFrames = () => loadJSON('data/frontend/precip-frames.json');
export const loadDischargeTimeseries = () => loadJSON('data/frontend/discharge-timeseries.json');
export const loadPreconditionFrames = () => loadJSON('data/frontend/precondition-frames.json');
export const loadPreconditionPeak = () => loadJSON('data/frontend/precondition-peak.json');
export const loadRasterManifest = () => loadJSON('data/frontend/raster-manifest.json');
