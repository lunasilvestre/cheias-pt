/**
 * cheias.pt — WeatherLayers GL integration
 *
 * Loads COGs into TextureData format for WeatherLayers GL layers:
 * wind particles, MSLP isobars, pressure center H/L markers, wind barbs.
 */

import {
  ParticleLayer,
  ContourLayer,
  HighLowLayer,
  GridLayer,
} from 'weatherlayers-gl';
import type { Layer } from '@deck.gl/core';
import { loadCOG } from './data-loader';
import type { DecodedRaster } from './types';

// ── TextureData type (WeatherLayers GL expects this) ──

interface TextureData {
  data: Uint8Array | Uint8ClampedArray | Float32Array;
  width: number;
  height: number;
}

type BitmapBoundingBox = [number, number, number, number];

export interface WeatherLayerSet {
  particles: ParticleLayer;
  isobars: ContourLayer;
  pressureCenters: HighLowLayer;
  windBarbs: GridLayer;
}

// ── COG → TextureData conversion ──

/**
 * Load a COG and return TextureData suitable for WeatherLayers GL.
 */
export async function loadWeatherTextureData(url: string): Promise<TextureData & { bounds: BitmapBoundingBox }> {
  const raster = await loadCOG(url);
  return {
    data: raster.data,
    width: raster.width,
    height: raster.height,
    bounds: raster.bounds,
  };
}

/**
 * Composite U and V wind component COGs into interleaved 2-channel TextureData.
 * WeatherLayers GL needs imageType: 'VECTOR' with interleaved [u0,v0,u1,v1,...] data.
 */
export function compositeUV(
  uData: { data: Float32Array; width: number; height: number },
  vData: { data: Float32Array; width: number; height: number },
): TextureData {
  const pixelCount = uData.width * uData.height;
  const interleaved = new Float32Array(pixelCount * 2);

  for (let i = 0; i < pixelCount; i++) {
    interleaved[i * 2] = uData.data[i];
    interleaved[i * 2 + 1] = vData.data[i];
  }

  return {
    data: interleaved,
    width: uData.width,
    height: uData.height,
  };
}

// ── Layer factory functions ──

const R2_BASE = 'https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog';

/**
 * Create animated wind particle trails from U/V wind data.
 */
export function createWindParticles(
  windData: TextureData,
  bounds: BitmapBoundingBox,
  id = 'wind-particles',
): ParticleLayer {
  return new ParticleLayer({
    id,
    image: windData,
    imageType: 'VECTOR',
    bounds,
    numParticles: 5000,
    maxAge: 100,
    speedFactor: 0.5,
    width: 2,
    color: [255, 255, 255, 200],
    animate: true,
    opacity: 0.8,
  });
}

/**
 * Create MSLP isobar contour lines at 4 hPa (400 Pa) intervals.
 */
export function createIsobars(
  mslpData: TextureData,
  bounds: BitmapBoundingBox,
  id = 'mslp-isobars',
): ContourLayer {
  return new ContourLayer({
    id,
    image: mslpData,
    imageType: 'SCALAR',
    bounds,
    interval: 400,       // 4 hPa in Pa
    majorInterval: 2000,  // 20 hPa major lines
    width: 1.5,
    color: [255, 255, 255, 220],
    opacity: 0.9,
  });
}

/**
 * Create H/L pressure center markers.
 */
export function createPressureCenters(
  mslpData: TextureData,
  bounds: BitmapBoundingBox,
  id = 'pressure-centers',
): HighLowLayer {
  return new HighLowLayer({
    id,
    image: mslpData,
    imageType: 'SCALAR',
    bounds,
    radius: 500000,
    unitFormat: { unit: 'hPa', scale: 0.01, decimals: 0 },
    textSize: 14,
    textColor: [255, 255, 255],
    textOutlineWidth: 2,
    textOutlineColor: [0, 0, 0],
    opacity: 1.0,
  });
}

/**
 * Create wind barb notation grid.
 */
export function createWindBarbs(
  windData: TextureData,
  bounds: BitmapBoundingBox,
  id = 'wind-barbs',
): GridLayer {
  return new GridLayer({
    id,
    image: windData,
    imageType: 'VECTOR',
    bounds,
    style: 'WIND_BARB',
    density: 32,
    iconColor: [255, 255, 255, 180],
    iconSize: 24,
    textSize: 0, // no text labels, just barbs
    opacity: 0.7,
  });
}

// ── Frame update ──

/**
 * Load all weather COGs for a timestamp and return configured layer set.
 * Expects R2 layout: {baseUrl}/mslp/{timestamp}.tif, wind-u/{timestamp}.tif, wind-v/{timestamp}.tif
 */
export async function updateWeatherFrame(
  timestamp: string,
  baseUrl = R2_BASE,
): Promise<WeatherLayerSet> {
  const [mslpTex, windUTex, windVTex] = await Promise.all([
    loadWeatherTextureData(`${baseUrl}/mslp/${timestamp}.tif`),
    loadWeatherTextureData(`${baseUrl}/wind-u/${timestamp}.tif`),
    loadWeatherTextureData(`${baseUrl}/wind-v/${timestamp}.tif`),
  ]);

  // Use MSLP bounds as the canonical extent (all should match)
  const bounds = mslpTex.bounds;

  // Composite wind U/V into interleaved vector field
  // loadWeatherTextureData always returns Float32Array from loadCOG
  const windData = compositeUV(
    { data: windUTex.data as Float32Array, width: windUTex.width, height: windUTex.height },
    { data: windVTex.data as Float32Array, width: windVTex.width, height: windVTex.height },
  );

  return {
    particles: createWindParticles(windData, bounds),
    isobars: createIsobars(mslpTex, bounds),
    pressureCenters: createPressureCenters(mslpTex, bounds),
    windBarbs: createWindBarbs(windData, bounds),
  };
}

/**
 * Flatten a WeatherLayerSet into an array of deck.gl layers.
 */
export function weatherLayersToArray(set: WeatherLayerSet): Layer[] {
  return [set.isobars, set.pressureCenters, set.particles, set.windBarbs];
}
