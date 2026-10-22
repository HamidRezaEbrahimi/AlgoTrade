// frontend/src/components/chart/useCandleData.ts
// Zero-flicker candle data feeding: full setData on load/symbol change or
// history back-fill, and lightweight update() for live ticks. Also applies
// dynamic price precision based on the instrument's price magnitude.

import { useEffect, useRef } from 'react';
import { IChartApi, ISeriesApi } from 'lightweight-charts';
import { CandleData } from '../../stores/useMarketStore';
import { getPricePrecision } from './chartUtils';

interface UseCandleDataParams {
  candles: CandleData[];
  symbol: string;
  timeframe?: string;
  isFullscreen: boolean;
  chartRef: React.MutableRefObject<IChartApi | null>;
  seriesRef: React.MutableRefObject<ISeriesApi<'Candlestick'> | null>;
}

export const useCandleData = (params: UseCandleDataParams): void => {
  const { candles, symbol, timeframe = '1h', chartRef, seriesRef } = params;

  const prevSymbolRef = useRef<string>(symbol);
  const prevTimeframeRef = useRef<string>(timeframe);
  const prevCandlesCountRef = useRef<number>(0);
  const prevEarliestTimeRef = useRef<number | null>(null);

  // Zero-Flicker Candle Updates (setData on load/symbol change, update() on ticks)
  useEffect(() => {
    if (!seriesRef.current || !chartRef.current) return;

    if (candles.length === 0) {
      seriesRef.current.setData([]);
      prevCandlesCountRef.current = 0;
      prevEarliestTimeRef.current = null;
      return;
    }

    const isSymbolChange = prevSymbolRef.current !== symbol;
    const isTimeframeChange = prevTimeframeRef.current !== timeframe;
    const isInitialLoad = prevCandlesCountRef.current === 0;
    const isDecreased = candles.length < prevCandlesCountRef.current;
    const countDiff = Math.abs(candles.length - prevCandlesCountRef.current);

    if (isSymbolChange || isTimeframeChange || isInitialLoad || isDecreased || countDiff > 2) {
      const sorted = [...candles].sort((a, b) => a.time - b.time);
      const uniqueCandles: CandleData[] = [];
      const seen = new Set<number>();
      for (const c of sorted) {
        if (!seen.has(c.time)) {
          seen.add(c.time);
          uniqueCandles.push(c);
        }
      }

      const currentRange = chartRef.current.timeScale().getVisibleLogicalRange();

      const formatted = uniqueCandles.map((c) => ({
        time: c.time as any,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }));

      const samplePrice = uniqueCandles[uniqueCandles.length - 1]?.close || 1.0;
      const { precision, minMove } = getPricePrecision(samplePrice);
      seriesRef.current.applyOptions({
        priceFormat: {
          type: 'price',
          precision: precision,
          minMove: minMove,
        },
      });

      seriesRef.current.setData(formatted);
      prevCandlesCountRef.current = uniqueCandles.length;

      const total = uniqueCandles.length;
      const currentEarliestTime = uniqueCandles[0]?.time ?? 0;

      if (isSymbolChange || isTimeframeChange || isInitialLoad) {
        const barsToShow = Math.min(total, 120);
        chartRef.current.timeScale().setVisibleLogicalRange({
          from: Math.max(0, total - barsToShow),
          to: total + 6,
        });
        prevSymbolRef.current = symbol;
        prevTimeframeRef.current = timeframe;
        prevEarliestTimeRef.current = currentEarliestTime;
      } else if (currentRange) {
        const prevEarliestTime = prevEarliestTimeRef.current;
        let prependedCount = 0;
        if (prevEarliestTime !== null && currentEarliestTime < prevEarliestTime) {
          prependedCount = uniqueCandles.filter((c) => c.time < prevEarliestTime).length;
        }

        const isOutOfRange = currentRange.from >= total - 2 || currentRange.to < 0;

        if (isOutOfRange) {
          const barsToShow = Math.min(total, 120);
          chartRef.current.timeScale().setVisibleLogicalRange({
            from: Math.max(0, total - barsToShow),
            to: total + 6,
          });
        } else if (prependedCount > 0) {
          chartRef.current.timeScale().setVisibleLogicalRange({
            from: currentRange.from + prependedCount,
            to: currentRange.to + prependedCount,
          });
        } else {
          chartRef.current.timeScale().setVisibleLogicalRange(currentRange);
        }

        prevEarliestTimeRef.current = currentEarliestTime;
      }
    } else {
      const lastCandle = candles[candles.length - 1];
      if (lastCandle) {
        try {
          seriesRef.current.update({
            time: lastCandle.time as any,
            open: lastCandle.open,
            high: lastCandle.high,
            low: lastCandle.low,
            close: lastCandle.close,
          });
          prevCandlesCountRef.current = candles.length;
        } catch {
          const sorted = [...candles].sort((a, b) => a.time - b.time);
          const uniqueCandles: CandleData[] = [];
          const seen = new Set<number>();
          for (const c of sorted) {
            if (!seen.has(c.time)) {
              seen.add(c.time);
              uniqueCandles.push(c);
            }
          }
          seriesRef.current.setData(uniqueCandles as any);
          prevCandlesCountRef.current = uniqueCandles.length;
        }
      }
    }
  }, [candles, symbol, timeframe, chartRef, seriesRef]);
};
