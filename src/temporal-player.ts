/**
 * cheias.pt — Generalized Temporal Player
 *
 * Two modes:
 *   - autoplay: rAF loop at configurable fps, loops automatically
 *   - scroll-driven: maps scroll progress (0-1) to frame index
 *
 * Three frame types:
 *   - png: fetch → ImageBitmap (pre-rendered frames)
 *   - cog: fetch → DecodedRaster → applyColormap → ImageBitmap
 *   - weather-layers: fetch GeoTIFF → WeatherLayers GL layer set
 */

import type { Layer } from '@deck.gl/core';
import type { TemporalConfig } from './types';
import { loadCOG, applyColormap, gaussianBlur, rasterToImageBitmap, getPalette } from './data-loader';
import { updateWeatherFrame, weatherLayersToArray } from './weather-layers';

export type FrameCallback = (index: number, date: string | null) => void;
export type LayerCallback = (layers: Layer[]) => void;

export class TemporalPlayer {
  readonly id: string;
  private config: TemporalConfig;

  // Frame state
  private frames: ImageBitmap[] = [];
  private weatherFrames: Layer[][] = [];
  private currentIndex = -1;
  private loaded = false;

  // Autoplay state
  private rafId: number | null = null;
  private lastFrameTime = 0;
  private playing = false;

  // Callbacks
  private onFrameCb: FrameCallback | null = null;
  private onLayerCb: LayerCallback | null = null;
  private onImageCb: ((bitmap: ImageBitmap, index: number) => void) | null = null;

  constructor(id: string, config: TemporalConfig) {
    this.id = id;
    this.config = config;
  }

  // ── Loading ──

  async load(): Promise<void> {
    if (this.loaded) return;

    const { frameType, urls } = this.config;

    if (frameType === 'png') {
      await this.loadPNGFrames(urls);
    } else if (frameType === 'cog') {
      await this.loadCOGFrames(urls);
    } else if (frameType === 'weather-layers') {
      await this.loadWeatherFrames(urls);
    }

    this.loaded = true;
  }

  private async loadPNGFrames(urls: string[]): Promise<void> {
    // Preload as ImageBitmaps for fast switching
    const promises = urls.map(async (url) => {
      const resp = await fetch(url);
      const blob = await resp.blob();
      return createImageBitmap(blob);
    });
    this.frames = await Promise.all(promises);
  }

  private async loadCOGFrames(urls: string[]): Promise<void> {
    const paletteId = this.config.paletteId;
    if (!paletteId) throw new Error(`COG frame type requires paletteId`);

    const paletteConfig = getPalette(paletteId);

    const promises = urls.map(async (url) => {
      const raster = await loadCOG(url);

      // Apply blur if palette specifies it
      let data = raster.data;
      if (paletteConfig?.blur_sigma) {
        data = gaussianBlur(data, raster.width, raster.height, paletteConfig.blur_sigma, raster.nodata);
      }

      const imageData = applyColormap({ ...raster, data }, paletteId);
      return rasterToImageBitmap(imageData);
    });

    this.frames = await Promise.all(promises);
  }

  private async loadWeatherFrames(timestamps: string[]): Promise<void> {
    const baseUrl = this.config.weatherBaseUrl;
    const promises = timestamps.map(async (ts) => {
      const set = await updateWeatherFrame(ts, baseUrl);
      return weatherLayersToArray(set);
    });
    this.weatherFrames = await Promise.all(promises);
  }

  // ── Playback control ──

  play(): void {
    if (this.config.mode !== 'autoplay') return;
    if (this.playing) return;
    if (!this.loaded) return;

    this.playing = true;
    this.lastFrameTime = performance.now();
    this.tick(this.lastFrameTime);
  }

  pause(): void {
    this.playing = false;
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  stop(): void {
    this.pause();
    this.currentIndex = -1;
  }

  seek(index: number): void {
    const maxIdx = this.getFrameCount() - 1;
    if (maxIdx < 0) return;
    const clamped = Math.max(0, Math.min(index, maxIdx));
    if (clamped !== this.currentIndex) {
      this.currentIndex = clamped;
      this.emitFrame();
    }
  }

  /**
   * Map scroll progress (0.0–1.0) to a frame index.
   * Used in scroll-driven mode.
   */
  setScrollProgress(progress: number): void {
    if (this.config.mode !== 'scroll-driven') return;
    const count = this.getFrameCount();
    if (count === 0) return;
    const idx = Math.min(Math.floor(progress * count), count - 1);
    if (idx !== this.currentIndex && idx >= 0) {
      this.currentIndex = idx;
      this.emitFrame();
    }
  }

  // ── Callbacks ──

  /** Called on every frame change with index and date label. */
  onFrame(cb: FrameCallback): void {
    this.onFrameCb = cb;
  }

  /** Called with deck.gl layers to render (weather-layers mode). */
  onLayers(cb: LayerCallback): void {
    this.onLayerCb = cb;
  }

  /** Called with ImageBitmap for png/cog modes. */
  onImage(cb: (bitmap: ImageBitmap, index: number) => void): void {
    this.onImageCb = cb;
  }

  // ── Cleanup ──

  destroy(): void {
    this.pause();
    this.frames = [];
    this.weatherFrames = [];
    this.currentIndex = -1;
    this.loaded = false;
    this.onFrameCb = null;
    this.onLayerCb = null;
    this.onImageCb = null;
  }

  // ── Internal ──

  private getFrameCount(): number {
    if (this.config.frameType === 'weather-layers') return this.weatherFrames.length;
    return this.frames.length;
  }

  private tick = (now: number): void => {
    if (!this.playing) return;

    const fps = this.config.fps || 2;
    const interval = 1000 / fps;

    if (now - this.lastFrameTime >= interval) {
      this.lastFrameTime = now;
      const count = this.getFrameCount();
      if (count === 0) return;

      let nextIdx = this.currentIndex + 1;
      if (nextIdx >= count) {
        if (this.config.loop !== false) {
          nextIdx = 0;
        } else {
          this.pause();
          return;
        }
      }

      this.currentIndex = nextIdx;
      this.emitFrame();
    }

    this.rafId = requestAnimationFrame(this.tick);
  };

  private emitFrame(): void {
    const idx = this.currentIndex;
    const date = this.config.dates?.[idx] ?? null;

    // Notify generic frame callback
    if (this.onFrameCb) this.onFrameCb(idx, date);

    if (this.config.frameType === 'weather-layers') {
      const layers = this.weatherFrames[idx];
      if (layers && this.onLayerCb) this.onLayerCb(layers);
    } else {
      const bitmap = this.frames[idx];
      if (bitmap && this.onImageCb) this.onImageCb(bitmap, idx);
    }
  }
}
