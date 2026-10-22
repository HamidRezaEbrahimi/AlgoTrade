// frontend/src/components/chart/usePatternMarkers.ts
// Builds and applies chart markers: detailed 6-point breakdown for the
// active pattern, historical wave pattern pins, and candlestick pattern
// pins. Every marker time is normalized to integer seconds and validated
// against existing candle times (lightweight-charts silently drops
// markers whose time does not match a candle — a key cause of the
// "patterns not drawn" bug).

import { useEffect, useRef } from 'react';
import { ISeriesApi, SeriesMarker, Time } from 'lightweight-charts';
import { CandleData } from '../../stores/useMarketStore';
import { ChartLayerVisibility, PatternMarker } from '../../pages/trading/types';
import { normalizeTimestamp } from './chartUtils';
import { resolveActivePattern } from './useWaveOverlay';

interface UsePatternMarkersParams {
  candles: CandleData[];
  patterns: PatternMarker[];
  selectedPatternId?: string | null;
  selectedPattern?: PatternMarker | null;
  localSelectedId: string | null;
  focusTimestamp?: number | null;
  layers: ChartLayerVisibility;
  seriesRef: React.MutableRefObject<ISeriesApi<'Candlestick'> | null>;
}

export const usePatternMarkers = (params: UsePatternMarkersParams): void => {
  const {
    candles,
    patterns,
    selectedPatternId,
    selectedPattern,
    localSelectedId,
    focusTimestamp,
    layers,
    seriesRef,
  } = params;

  const localSelectedIdRef = useRef(localSelectedId);
  localSelectedIdRef.current = localSelectedId;

  useEffect(() => {
    if (!seriesRef.current) return;

    const filteredPatterns = (patterns || []).filter((p: PatternMarker) => {
      if (layers.runningFlat === false && !p.id?.startsWith('developing_prz')) return false;
      return true;
    });

    if (filteredPatterns.length === 0 || candles.length === 0) {
      seriesRef.current.setMarkers([]);
      return;
    }

    const candleTimes = candles.map((c: CandleData) => c.time);
    const candleTimeSet = new Set(candleTimes);
    const allMarkers: SeriesMarker<Time>[] = [];

    const snapToCandle = (rawTime: number | null | undefined): number | null => {
      const t = normalizeTimestamp(rawTime);
      if (!t || candleTimes.length === 0) return null;
      if (candleTimeSet.has(t)) return t;
      let closest = candleTimes[0];
      let minDiff = Math.abs(candleTimes[0] - t);
      for (let i = 1; i < candleTimes.length; i++) {
        const diff = Math.abs(candleTimes[i] - t);
        if (diff < minDiff) {
          minDiff = diff;
          closest = candleTimes[i];
        }
      }
      return closest;
    };

    const wavePatterns = filteredPatterns;
    const activePattern = resolveActivePattern(
      patterns || [], selectedPatternId, selectedPattern, localSelectedIdRef.current,
    );

    // 1. Detailed Elliott Wave Breakdown (0, 1, A, B, C) for confirmed patterns
    const confirmedToRender = activePattern ? [activePattern] : wavePatterns.filter((p) => !(p as any).is_developing);
    confirmedToRender.forEach((pat) => {
      if (!pat.points || pat.points.length === 0) return;
      const pts = pat.points;
      const isBull = pat.direction === 'bullish';

      pts.forEach((pt: any) => {
        const t = snapToCandle(pt.time);
        if (!t) return;

        const label = String(pt.label || '');
        const isEntry = label === 'C';
        const isLowPivot = isBull
          ? (label === '0' || label === 'A' || label === 'C')
          : (label === '1' || label === 'B');
        const position: any = isLowPivot ? 'belowBar' : 'aboveBar';

        // Dedicated Elliott Wave Colors from AlefTrade Visualizer:
        // P0 & P1 (Impulse): Blue #3b82f6
        // Wave A & B (Flat Correction): Amber #f59e0b
        // Wave C (Trigger / Reversal): Emerald #10b981 (Bull) / Rose #ef4444 (Bear)
        // Invalidated: Slate Gray #64748b | Target Hit: Emerald #10b981
        const isDev = Boolean((pat as any).is_developing);
        const isInv = Boolean((pat as any).is_invalidated || (pat as any).lifecycle_status === 'INVALIDATED');
        const isHit = Boolean((pat as any).is_target_hit || (pat as any).lifecycle_status === 'TARGET_HIT');

        let ptColor = '#3b82f6';
        if (label === 'A' || label === 'B') ptColor = '#f59e0b';
        if (label === 'C') ptColor = isBull ? '#10b981' : '#ef4444';

        if (isInv) {
          ptColor = '#64748b';
        } else if (isHit && label === 'C') {
          ptColor = '#10b981';
        }

        let cText = isDev ? `C (ورود لایو PRZ: ${pt.price})` : `C (ورود: ${pt.price})`;
        if (isInv && isEntry) {
          cText = `C (✕ باطل شد: نقض تراز P0)`;
        } else if (isHit && isEntry) {
          cText = `C (🎯 تارگت اول محقق شد)`;
        }

        allMarkers.push({
          time: t as Time,
          position,
          color: ptColor,
          shape: isInv && isEntry ? 'square' : (isEntry ? (isBull ? 'arrowUp' : 'arrowDown') : 'circle'),
          text: isEntry ? cText : label,
        });
      });
    });

    // 2. Developing Wave PRZ Markers for non-active patterns (0, 1, A, B and PRZ Zone Pin)
    wavePatterns.forEach((p: PatternMarker) => {
      if (!(p as any).is_developing) return;
      if (activePattern && activePattern.id === p.id) return; // Already rendered with full detail in activePattern

      const isBull = p.direction === 'bullish';

      // Render P0, P1, A, B if available
      if (p.points && p.points.length > 0) {
        p.points.forEach((pt: any) => {
          const t = snapToCandle(pt.time);
          if (!t) return;
          const label = String(pt.label || '');
          const isLowPivot = isBull ? (label === '0' || label === 'A') : (label === '1' || label === 'B');
          const position: any = isLowPivot ? 'belowBar' : 'aboveBar';
          const ptColor = (label === 'A' || label === 'B') ? '#f59e0b' : '#3b82f6';

          allMarkers.push({
            time: t as Time,
            position,
            color: ptColor,
            shape: 'circle',
            text: label,
          });
        });
      }

      // Render PRZ Zone Marker
      const t = snapToCandle(p.time);
      if (t) {
        allMarkers.push({
          time: t as Time,
          position: isBull ? 'belowBar' : 'aboveBar',
          color: '#f59e0b',
          shape: 'square',
          text: `🎯 شکار در PRZ (${(p as any).stage || 'موج C'})`,
        });
      }
    });

    const sortedMarkers = allMarkers.sort((a, b) => (a.time as number) - (b.time as number));
    seriesRef.current.setMarkers(sortedMarkers);
  }, [
    patterns, focusTimestamp, selectedPatternId, localSelectedId, selectedPattern,
    layers.runningFlat,
    candles, seriesRef,
  ]);
};
