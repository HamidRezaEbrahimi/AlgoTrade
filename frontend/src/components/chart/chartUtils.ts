// frontend/src/components/chart/chartUtils.ts
// Shared chart utilities: price formatting/precision, pattern colors,
// timestamp normalization (ms→s) and common chart prop types.

import { PatternMarker } from '../../pages/trading/types';

export interface ChartSmaLevels {
  order_block_demand?: number;
  order_block_supply?: number;
  fvg_imbalance?: number;
  support_level?: number;
  resistance_level?: number;
}

export interface HoveredCandleInfo {
  timeStr: string;
  open: number;
  high: number;
  low: number;
  close: number;
  isUp: boolean;
}

export const getPricePrecision = (price: number): { precision: number; minMove: number } => {
  if (price <= 0) return { precision: 2, minMove: 0.01 };
  if (price < 0.001) return { precision: 8, minMove: 0.00000001 };
  if (price < 0.1) return { precision: 6, minMove: 0.000001 };
  if (price < 10) return { precision: 5, minMove: 0.00001 }; // Forex EURUSD, GBPUSD (5 digits)
  if (price < 500) return { precision: 3, minMove: 0.001 }; // USDJPY, JPY pairs
  return { precision: 2, minMove: 0.01 }; // Gold, BTC, Stocks
};

export const formatPrice = (v?: number) => {
  if (v === undefined || v === null || v === 0) return '---';
  if (v >= 1000) return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (v < 0.001) return v.toFixed(8);
  if (v < 0.1) return v.toFixed(6);
  if (v < 10) return v.toFixed(5);
  if (v < 500) return v.toFixed(3);
  return v.toFixed(2);
};

// Unified color map: distinct colors for each pattern and direction
export const getCategoryColor = (p: PatternMarker): string => {
  if (p.pattern_color) return p.pattern_color;
  
  const isBull = p.direction === 'bullish';
  const name = (p.name_en || '').toLowerCase();
  
  // Flats
  if (name.includes('regular flat')) return isBull ? '#0ea5e9' : '#0284c7';    // Sky Blue
  if (name.includes('expanded flat')) return isBull ? '#f43f5e' : '#be123c';   // Rose
  if (name.includes('running flat')) return isBull ? '#8b5cf6' : '#6d28d9';    // Violet
  if (name.includes('contract flat')) return isBull ? '#10b981' : '#047857';   // Emerald
  if (name.includes('complex flat')) return isBull ? '#f59e0b' : '#b45309';    // Amber
  
  // Flags & Legacy
  if (p.category === 'flag') return isBull ? '#eab308' : '#a16207';            // Yellow
  if (p.category === 'wedge') return isBull ? '#3b82f6' : '#1d4ed8';           // Blue
  if (p.category === 'zigzag') return isBull ? '#06b6d4' : '#0e7490';          // Cyan

  // Fallback
  return isBull ? '#10b981' : '#ef4444';
};

/**
 * Normalize a timestamp to integer seconds (UTC).
 * Backend markers are always seconds; defensive ms→s conversion guards
 * against any upstream producer emitting milliseconds, which would make
 * lightweight-charts silently drop markers/line points (time mismatch).
 */
export const normalizeTimestamp = (ts?: number | null): number => {
  if (ts === null || ts === undefined) return 0;
  const n = Number(ts);
  if (!Number.isFinite(n) || n <= 0) return 0;
  return n > 1e12 ? Math.floor(n / 1000) : Math.floor(n);
};
