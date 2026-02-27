/**
 * cheias.pt — Data loader
 *
 * Fetches and caches frontend JSON files.
 * Loads Cloud Optimized GeoTIFFs (COGs) via geotiff.js.
 * Applies colormaps from palette.json for client-side rendering.
 */

import { fromUrl } from 'geotiff';
import type { RasterManifest, DischargeData, DecodedRaster, PaletteStop, PaletteConfig } from './types';
import paletteData from '../data/colormaps/palette.json';

// ── Caches ──

const jsonCache: Record<string, unknown> = {};
const cogCache = new Map<string, DecodedRaster>();

// ── JSON loaders ──

export async function loadJSON<T>(url: string): Promise<T> {
  if (jsonCache[url]) return jsonCache[url] as T;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to load ${url}: ${resp.status}`);
  const data = await resp.json();
  jsonCache[url] = data;
  return data as T;
}

export const loadSoilMoistureFrames = () => loadJSON('data/frontend/soil-moisture-frames.json');
export const loadPrecipStormTotals = () => loadJSON('data/frontend/precip-storm-totals.json');
export const loadPrecipFrames = () => loadJSON('data/frontend/precip-frames.json');
export const loadDischargeTimeseries = () => loadJSON<DischargeData>('data/frontend/discharge-timeseries.json');
export const loadPreconditionFrames = () => loadJSON('data/frontend/precondition-frames.json');
export const loadPreconditionPeak = () => loadJSON('data/frontend/precondition-peak.json');
export const loadRasterManifest = () => loadJSON<RasterManifest>('data/frontend/raster-manifest.json');

// ── COG loading ──

/**
 * Load a Cloud Optimized GeoTIFF from a URL.
 * Returns decoded raster data with geographic bounds.
 * Results are cached by URL.
 */
export async function loadCOG(url: string): Promise<DecodedRaster> {
  const cached = cogCache.get(url);
  if (cached) return cached;

  const tiff = await fromUrl(url);
  const image = await tiff.getImage();
  const bbox = image.getBoundingBox();
  const nodata = image.getGDALNoData();
  const width = image.getWidth();
  const height = image.getHeight();

  const rasters = await image.readRasters({ interleave: true });
  const rawData = rasters instanceof Float32Array
    ? rasters
    : new Float32Array(rasters as ArrayLike<number>);

  // Detect non-standard positive Y-resolution (south-to-north pixel order)
  // and flip to standard north-to-south for consistent BitmapLayer rendering
  const resolution = image.getResolution();
  const data = resolution[1] > 0
    ? flipRowsVertically(rawData, width, height)
    : rawData;

  const result: DecodedRaster = {
    data,
    width,
    height,
    bounds: [bbox[0], bbox[1], bbox[2], bbox[3]],
    nodata,
  };

  cogCache.set(url, result);
  return result;
}

/**
 * Flip raster rows vertically (south-to-north → north-to-south).
 */
function flipRowsVertically(data: Float32Array, width: number, height: number): Float32Array {
  const flipped = new Float32Array(data.length);
  for (let y = 0; y < height; y++) {
    const srcOffset = y * width;
    const dstOffset = (height - 1 - y) * width;
    flipped.set(data.subarray(srcOffset, srcOffset + width), dstOffset);
  }
  return flipped;
}

/**
 * Clear the COG cache (call when switching chapters to free memory).
 */
export function clearCOGCache(): void {
  cogCache.clear();
}

// ── Palette parsing ──

type RawPaletteEntry = {
  type: string;
  stops?: Array<[number, string]>;
  domain?: [number, number] | string;
  alpha_mode?: string;
  blur_sigma?: number;
};

/**
 * Parse a palette from palette.json into PaletteConfig.
 */
export function getPalette(paletteId: string): PaletteConfig | null {
  const raw = (paletteData as unknown as Record<string, RawPaletteEntry>)[paletteId];
  if (!raw || !raw.stops || !Array.isArray(raw.domain)) return null;

  const stops: PaletteStop[] = raw.stops.map(([position, hexColor]) => ({
    position,
    color: hexToRGBA(hexColor),
  }));

  return {
    type: raw.type as PaletteConfig['type'],
    stops,
    domain: raw.domain as [number, number],
    alpha_mode: raw.alpha_mode || 'fixed',
    blur_sigma: raw.blur_sigma,
  };
}

function hexToRGBA(hex: string): [number, number, number, number] {
  if (hex === 'transparent') return [0, 0, 0, 0];
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  const a = h.length === 8 ? parseInt(h.slice(6, 8), 16) : 255;
  return [r, g, b, a];
}

// ── Colormap application ──

/**
 * Apply a colormap to a decoded raster, producing an ImageData for rendering.
 * Nodata pixels become transparent.
 */
export function applyColormap(raster: DecodedRaster, paletteId: string): ImageData {
  const palette = getPalette(paletteId);
  if (!palette) throw new Error(`Unknown palette: ${paletteId}`);

  const { data, width, height, nodata } = raster;
  const { stops, domain, alpha_mode } = palette;
  const [domainMin, domainMax] = domain;
  const range = domainMax - domainMin;

  const pixels = new Uint8ClampedArray(width * height * 4);

  for (let i = 0; i < width * height; i++) {
    const value = data[i];
    const pi = i * 4;

    // Nodata → transparent
    if (nodata !== null && value === nodata) {
      continue; // already zeroed
    }
    if (isNaN(value)) {
      continue;
    }

    // Normalize value to 0-1 within domain
    const t = Math.max(0, Math.min(1, (value - domainMin) / range));

    // Interpolate between palette stops
    const [r, g, b, a] = interpolateStops(stops, t);

    // Apply alpha mode
    let alpha = a;
    if (alpha_mode === 'proportional') {
      alpha = Math.round(t * 255);
    } else if (alpha_mode.startsWith('fixed_')) {
      alpha = Math.round(parseFloat(alpha_mode.slice(6)) * 255);
    } else if (alpha_mode === 'graduated') {
      alpha = Math.round((0.6 + t * 0.3) * 255);
    }

    pixels[pi] = r;
    pixels[pi + 1] = g;
    pixels[pi + 2] = b;
    pixels[pi + 3] = alpha;
  }

  return new ImageData(pixels, width, height);
}

function interpolateStops(stops: PaletteStop[], t: number): [number, number, number, number] {
  // Find surrounding stops
  if (t <= stops[0].position) return stops[0].color;
  if (t >= stops[stops.length - 1].position) return stops[stops.length - 1].color;

  for (let i = 0; i < stops.length - 1; i++) {
    if (t >= stops[i].position && t <= stops[i + 1].position) {
      const frac = (t - stops[i].position) / (stops[i + 1].position - stops[i].position);
      const c0 = stops[i].color;
      const c1 = stops[i + 1].color;
      return [
        Math.round(c0[0] + (c1[0] - c0[0]) * frac),
        Math.round(c0[1] + (c1[1] - c0[1]) * frac),
        Math.round(c0[2] + (c1[2] - c0[2]) * frac),
        Math.round(c0[3] + (c1[3] - c0[3]) * frac),
      ];
    }
  }

  return stops[stops.length - 1].color;
}

// ── Gaussian blur ──

/**
 * Apply separable Gaussian blur to a Float32Array raster.
 * Skips nodata pixels to preserve data boundaries.
 */
export function gaussianBlur(
  data: Float32Array,
  w: number,
  h: number,
  sigma: number,
  nodata: number | null = null,
): Float32Array {
  const radius = Math.ceil(sigma * 3);
  const kernel = makeGaussianKernel(sigma, radius);

  // Horizontal pass
  const tmp = new Float32Array(data.length);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const center = data[y * w + x];
      if (nodata !== null && center === nodata) {
        tmp[y * w + x] = nodata;
        continue;
      }

      let sum = 0;
      let weightSum = 0;
      for (let k = -radius; k <= radius; k++) {
        const sx = Math.min(w - 1, Math.max(0, x + k));
        const val = data[y * w + sx];
        if (nodata !== null && val === nodata) continue;
        const weight = kernel[k + radius];
        sum += val * weight;
        weightSum += weight;
      }
      tmp[y * w + x] = weightSum > 0 ? sum / weightSum : center;
    }
  }

  // Vertical pass
  const result = new Float32Array(data.length);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const center = tmp[y * w + x];
      if (nodata !== null && center === nodata) {
        result[y * w + x] = nodata;
        continue;
      }

      let sum = 0;
      let weightSum = 0;
      for (let k = -radius; k <= radius; k++) {
        const sy = Math.min(h - 1, Math.max(0, y + k));
        const val = tmp[sy * w + x];
        if (nodata !== null && val === nodata) continue;
        const weight = kernel[k + radius];
        sum += val * weight;
        weightSum += weight;
      }
      result[y * w + x] = weightSum > 0 ? sum / weightSum : center;
    }
  }

  return result;
}

function makeGaussianKernel(sigma: number, radius: number): Float32Array {
  const size = radius * 2 + 1;
  const kernel = new Float32Array(size);
  const s2 = 2 * sigma * sigma;
  let sum = 0;
  for (let i = 0; i < size; i++) {
    const x = i - radius;
    kernel[i] = Math.exp(-(x * x) / s2);
    sum += kernel[i];
  }
  // Normalize
  for (let i = 0; i < size; i++) {
    kernel[i] /= sum;
  }
  return kernel;
}

// ── ImageBitmap conversion ──

/**
 * Convert ImageData to ImageBitmap for efficient GPU upload.
 */
export function rasterToImageBitmap(imageData: ImageData): Promise<ImageBitmap> {
  return createImageBitmap(imageData);
}
