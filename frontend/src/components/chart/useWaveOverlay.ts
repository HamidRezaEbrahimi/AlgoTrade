// frontend/src/components/chart/useWaveOverlay.ts
// Renders unified wave lines (P0→P1→P2→P3→P4→P5) for ALL visible patterns.
// Timestamps are normalized to integer seconds and snapped to valid candle times.

import { useEffect, useRef } from 'react';
import { IChartApi, ISeriesApi } from 'lightweight-charts';
import { CandleData } from '../../stores/useMarketStore';
import { ChartLayerVisibility, PatternMarker } from '../../pages/trading/types';
import { normalizeTimestamp } from './chartUtils';

interface UseWaveOverlayParams {
  candles: CandleData[];
  patterns: PatternMarker[];
  selectedPatternId?: string | null;
  selectedPattern?: PatternMarker | null;
  localSelectedId: string | null;
  layers: ChartLayerVisibility;
  chartRef: React.MutableRefObject<IChartApi | null>;
}

export const resolveActivePattern = (
  patterns: PatternMarker[],
  selectedPatternId?: string | null,
  selectedPattern?: PatternMarker | null,
  localSelectedId: string | null = null,
): PatternMarker | null => {
  const effSelectedId = selectedPatternId || localSelectedId;
  if (selectedPattern) return selectedPattern;
  if (effSelectedId) {
    const found = patterns.find((p) => p.id === effSelectedId);
    if (found) return found;
  }
  // 1. Prioritize active live PRZ reversal opportunity (non-invalidated)
  const livePrz = patterns.filter(
    (p) => Boolean((p as any).is_developing) && (p as any).trade_setup?.is_live_entry && !(p as any).is_invalidated,
  );
  if (livePrz.length > 0) return livePrz[livePrz.length - 1];

  // 2. Confirmed completed wave patterns that are ACTIVE
  const activeConfirmed = patterns.filter(
    (p) => !Boolean((p as any).is_developing) && p.points && p.points.length >= 4 && (p as any).lifecycle_status === 'ACTIVE' && !(p as any).is_invalidated,
  );
  if (activeConfirmed.length > 0) return activeConfirmed[activeConfirmed.length - 1];

  // 3. Other confirmed wave patterns (TARGET_HIT or non-invalidated)
  const confirmed = patterns.filter(
    (p) => !Boolean((p as any).is_developing) && p.points && p.points.length >= 4 && !(p as any).is_invalidated,
  );
  if (confirmed.length > 0) return confirmed[confirmed.length - 1];

  // 4. Developing wave pattern in formation (at least P0, P1, A)
  const developing = patterns.filter(
    (p) => Boolean((p as any).is_developing) && p.points && p.points.length >= 3 && !(p as any).is_invalidated,
  );
  if (developing.length > 0) return developing[developing.length - 1];

  return patterns.length > 0 ? patterns[patterns.length - 1] : null;
};

export const useWaveOverlay = (params: UseWaveOverlayParams): void => {
  const {
    candles,
    patterns,
    selectedPatternId,
    selectedPattern,
    localSelectedId,
    layers,
    chartRef,
  } = params;

  // We maintain an array of dynamically created LineSeries
  const lineSeriesRefs = useRef<ISeriesApi<'Line'>[]>([]);

  useEffect(() => {
    if (!chartRef.current || candles.length === 0) return;
    const chart = chartRef.current;

    // 1. Clear all existing line series from the chart
    lineSeriesRefs.current.forEach((series) => {
      try {
        chart.removeSeries(series);
      } catch (e) {
        // Ignore if already removed
      }
    });
    lineSeriesRefs.current = [];

    const activePattern = resolveActivePattern(
      patterns, selectedPatternId, selectedPattern, localSelectedId,
    );

    // Filter patterns that should be visible on the chart based on layers
    const visiblePatterns = (patterns || []).filter((p) => {
      if (layers.runningFlat === false && p.type === 'running_flat') return false;
      return true;
    });

    const candleTimes = candles.map((c) => c.time);
    const candleTimeSet = new Set(candleTimes);

    const hexToRgba = (hex: string, alpha: number) => {
      if (!hex.startsWith('#') || hex.length !== 7) return hex;
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    };

    // 2. Render each visible pattern as its own LineSeries
    visiblePatterns.forEach((targetPattern) => {
      if (targetPattern && targetPattern.points && targetPattern.points.length >= 3) {
        const pts = targetPattern.points;
        const isBull = targetPattern.direction === 'bullish';
        const isDev = Boolean((targetPattern as any).is_developing);
        const isInv = Boolean((targetPattern as any).is_invalidated || (targetPattern as any).lifecycle_status === 'INVALIDATED');
        const isHit = Boolean((targetPattern as any).is_target_hit || (targetPattern as any).lifecycle_status === 'TARGET_HIT');
        const lineColor = targetPattern.pattern_color || (isInv ? '#64748b' : (isHit ? '#10b981' : (isDev ? '#f59e0b' : (isBull ? '#3b82f6' : '#ef4444'))));
        const isActive = activePattern && activePattern.id === targetPattern.id;

        const newSeries = chart.addLineSeries({
          color: isActive ? lineColor : hexToRgba(lineColor, isInv ? 0.35 : 0.45),
          lineWidth: isInv ? 1 : (isActive ? 3 : 2),
          lineStyle: isInv ? 3 : (isDev ? 2 : 0), // LargeDashed for invalidated, Dashed for dev, Solid for confirmed
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: true,
        });

        // Snap points to valid candle timestamps
        const rawLineData = pts.map((pt: any) => {
          let t = normalizeTimestamp(pt.time);
          if (!candleTimeSet.has(t) && candleTimes.length > 0) {
            let closest = candleTimes[0];
            let minDiff = Math.abs(candleTimes[0] - t);
            for (let i = 1; i < candleTimes.length; i++) {
              const diff = Math.abs(candleTimes[i] - t);
              if (diff < minDiff) {
                minDiff = diff;
                closest = candleTimes[i];
              }
            }
            t = closest;
          }
          return {
            time: t,
            value: Number(pt.price),
          };
        });

        rawLineData.sort((a: { time: number; value: number }, b: { time: number; value: number }) => a.time - b.time);

        // Ensure strictly increasing times (Lightweight Charts requirement)
        const uniqueLineData = rawLineData.filter(
          (d: { time: number; value: number }, i: number) => d.time > 0 && (i === 0 || d.time > rawLineData[i - 1].time),
        );

        newSeries.setData(uniqueLineData as any);
        lineSeriesRefs.current.push(newSeries);
      }
    });

    // Cleanup function when component unmounts or dependencies change
    return () => {
      lineSeriesRefs.current.forEach((series) => {
        try {
          chart.removeSeries(series);
        } catch (e) {}
      });
      lineSeriesRefs.current = [];
    };
  }, [
    selectedPatternId,
    selectedPattern,
    localSelectedId,
    layers.runningFlat,
    patterns,
    candles,
    chartRef,
  ]);
};
