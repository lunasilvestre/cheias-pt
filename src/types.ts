/**
 * cheias.pt — Shared TypeScript interfaces
 */

export interface ChapterCamera {
  center: [number, number];
  zoom: number;
  pitch: number;
  bearing: number;
}

export interface ChapterAnimation {
  type: 'flyTo' | 'easeTo';
  duration: number;
}

export interface ChapterLayer {
  id: string;
  opacity: number;
  type: string;
}

export interface LegendItem {
  title: string;
  color: string;
  type: 'fill' | 'circle' | 'line';
}

export interface CTAButton {
  label: string;
  action: string;
}

export interface ChapterSubstep {
  id: string;
  title: string;
  text: string;
  alignment: 'left' | 'right' | 'fully';
  camera: ChapterCamera;
  animation: ChapterAnimation;
}

export interface Chapter {
  id: string;
  title: string;
  subtitle: string | null;
  text: string | null;
  alignment: 'left' | 'right' | 'fully';
  camera: ChapterCamera;
  animation: ChapterAnimation;
  layers: ChapterLayer[];
  legend: LegendItem[];
  source: string | null;
  onEnter: string | null;
  onLeave: string | null;
  byline?: string;
  substeps?: ChapterSubstep[];
  cta?: CTAButton[];
}

/** Resolved chapter config passed to callbacks (includes substep merged data) */
export interface ResolvedChapter extends Chapter {
  isSubstep?: boolean;
  parentLayers?: ChapterLayer[];
}

export interface RasterFrame {
  date: string;
  url: string;
}

export interface RasterManifest {
  soil_moisture: { frames: RasterFrame[] };
  precipitation: { frames: RasterFrame[] };
}

export interface DischargeStation {
  name: string;
  basin: string;
  lat: number;
  lon: number;
  timeseries: Array<{
    date: string;
    discharge: number;
    discharge_ratio: number;
  }>;
}

export interface DischargeData {
  stations: DischargeStation[];
}

/** Layer definition for the layer manager */
export interface LayerDef {
  type: string;
  source?: Record<string, unknown>;
  sourceRef?: string;
  'source-layer'?: string;
  paint: Record<string, unknown>;
  layout?: Record<string, unknown>;
  filter?: unknown[];
  stub?: boolean;
  imageSource?: boolean;
  bounds?: [number, number, number, number];
  initialUrl?: string;
  tileSource?: boolean;
  tiles?: string[];
  tileSize?: number;
  attribution?: string;
}

/**
 * Format a number with Portuguese locale.
 */
export function formatNumber(n: number, decimals = 0): string {
  return new Intl.NumberFormat('pt-PT', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(n);
}
