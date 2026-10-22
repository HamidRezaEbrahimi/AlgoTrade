// frontend/src/components/chart/useChartInstance.ts
// Chart instance lifecycle hook: creates the lightweight-charts instance,
// candlestick + wave line series, and wires crosshair hover, pattern click
// selection, infinite history loading and resize handling.

import { useEffect, useRef } from 'react';
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts';
import { CandleData } from '../../stores/useMarketStore';
import { formatDualDateTime, formatChartTickMark } from '../../utils/dateFormatter';
import { PatternMarker } from '../../pages/trading/types';
import { HoveredCandleInfo } from './chartUtils';

interface UseChartInstanceParams {
  /** Current symbol; resets history-pagination state on change. */
  symbol: string;
  isFullscreen: boolean;
  /** Latest candles getter (ref-stable, used by scroll listener). */
  getCandles: () => CandleData[];
  /** Latest patterns getter (ref-stable, used by click handler). */
  getPatterns: () => PatternMarker[];
  /** Called with the clicked pattern or null (deselect). */
  onPatternClick: (pattern: PatternMarker | null) => void;
  /** Crosshair hover updates for the OHLC legend. */
  onHover: (info: HoveredCandleInfo | null) => void;
  /** Load older history; return false when the start of data is reached. */
  onLoadMoreHistory?: (earliestTimestamp: number) => Promise<boolean | void>;
  /** Optional click callback with timestamp (used for Bar Replay jump/cut) */
  onChartClick?: (timestamp: number) => void;
}

export interface ChartInstanceRefs {
  containerRef: React.RefObject<HTMLDivElement>;
  chartRef: React.MutableRefObject<IChartApi | null>;
  seriesRef: React.MutableRefObject<ISeriesApi<'Candlestick'> | null>;
}

export const useChartInstance = (params: UseChartInstanceParams): ChartInstanceRefs => {
  const { isFullscreen, onPatternClick, onHover, onLoadMoreHistory, onChartClick } = params;

  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  // Ref-stable accessors so the once-mounted subscriptions always see fresh data
  const getCandlesRef = useRef(params.getCandles);
  getCandlesRef.current = params.getCandles;
  const getPatternsRef = useRef(params.getPatterns);
  getPatternsRef.current = params.getPatterns;
  const onPatternClickRef = useRef(onPatternClick);
  onPatternClickRef.current = onPatternClick;
  const onHoverRef = useRef(onHover);
  onHoverRef.current = onHover;
  const onLoadMoreHistoryRef = useRef(onLoadMoreHistory);
  onLoadMoreHistoryRef.current = onLoadMoreHistory;
  const onChartClickRef = useRef(onChartClick);
  onChartClickRef.current = onChartClick;

  const isFetchingHistoryRef = useRef<boolean>(false);
  const hasReachedEndRef = useRef<boolean>(false);
  const prevIsFullscreenRef = useRef<boolean>(isFullscreen);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight || 480,
      layout: {
        background: { color: '#090d16' },
        textColor: '#94a3b8',
        fontFamily: 'Inter, Vazirmatn, sans-serif',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.03)' },
      },
      crosshair: {
        vertLine: { color: '#06b6d4', width: 1, style: 3 },
        horzLine: { color: '#06b6d4', width: 1, style: 3 },
      },
      localization: {
        locale: 'fa-IR',
        timeFormatter: (timestamp: number) => formatDualDateTime(timestamp),
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 8,
        barSpacing: 8,
        tickMarkFormatter: (timePoint: any) => formatChartTickMark(timePoint),
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        autoScale: true,
        scaleMargins: { top: 0.08, bottom: 0.08 },
      },
    });

    const series = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    chartRef.current = chart;
    seriesRef.current = series;

    // Crosshair hover synchronization (Shamsi + Gregorian dual date & OHLC)
    chart.subscribeCrosshairMove((param) => {
      if (!param || !param.time || !param.seriesData.get(series)) {
        onHoverRef.current(null);
        return;
      }
      const data = param.seriesData.get(series) as any;
      if (data) {
        const ts = typeof param.time === 'number' ? param.time : (param.time as any)?.timestamp || 0;
        onHoverRef.current({
          timeStr: formatDualDateTime(ts),
          open: data.open,
          high: data.high,
          low: data.low,
          close: data.close,
          isUp: data.close >= data.open,
        });
      }
    });

    // Interactive Pattern Selection on Chart Click (Toggle On / Off)
    chart.subscribeClick((param) => {
      if (!param.time) {
        onPatternClickRef.current(null);
        return;
      }
      const patterns = getPatternsRef.current() || [];
      if (patterns.length === 0) {
        onPatternClickRef.current(null);
        return;
      }
      const clickTime = typeof param.time === 'number' ? param.time : (param.time as any)?.timestamp || 0;
      if (clickTime && onChartClickRef.current) {
        onChartClickRef.current(clickTime);
      }
      if (!clickTime) {
        onPatternClickRef.current(null);
        return;
      }

      // 1. Separate Wave/Chart patterns (which have points) and Candlestick patterns
      const wavePatterns = patterns.filter((p) => p.category !== 'candlestick' || (p.points && p.points.length >= 4));
      const candlePatterns = patterns.filter((p) => p.category === 'candlestick');

      // Determine dynamic timeframe interval from candle data
      const candles = getCandlesRef.current() || [];
      let tfInterval = 3600;
      if (candles.length >= 2) {
        const diff = Math.abs(candles[candles.length - 1].time - candles[candles.length - 2].time);
        if (diff > 0 && diff < 86400 * 30) {
          tfInterval = diff;
        }
      }

      // 2. PRIORITY 1: Check Wave Patterns (find closest point or entry within span)
      let found: PatternMarker | null = null;
      let minDistance = Infinity;

      for (const p of wavePatterns) {
        if (p.points && p.points.length >= 2) {
          const times = p.points.map((pt) => Number(pt.time));
          const pStart = Math.min(...times) - tfInterval * 2;
          const pEnd = Math.max(...times) + tfInterval * 2;
          if (clickTime >= pStart && clickTime <= pEnd) {
            for (const pt of p.points) {
              const d = Math.abs(Number(pt.time) - clickTime);
              if (d < minDistance) {
                minDistance = d;
                found = p;
              }
            }
          }
        }
        const dist = Math.abs(p.time - clickTime);
        if (dist <= tfInterval * 4 && dist < minDistance) {
          minDistance = dist;
          found = p;
        }
      }

      // 3. PRIORITY 2: Only if no wave pattern was clicked, check candlestick patterns
      if (!found) {
        let minCandleDist = Infinity;
        for (const p of candlePatterns) {
          const dist = Math.abs(p.time - clickTime);
          if (dist <= tfInterval * 2 && dist < minCandleDist) {
            minCandleDist = dist;
            found = p;
          }
        }
      }

      onPatternClickRef.current(found || null);
    });

    // Dynamic History Scroll Listener (Infinite History Loading)
    chart.timeScale().subscribeVisibleLogicalRangeChange((newRange) => {
      if (!newRange) return;
      if (newRange.from <= 2 && !isFetchingHistoryRef.current && !hasReachedEndRef.current) {
        const currentCandles = getCandlesRef.current();
        if (currentCandles && currentCandles.length > 0 && onLoadMoreHistoryRef.current) {
          const sorted = [...currentCandles].sort((a, b) => a.time - b.time);
          const earliestTime = sorted[0].time;
          isFetchingHistoryRef.current = true;
          onLoadMoreHistoryRef.current(earliestTime)
            .then((result: boolean | void) => {
              if (result === false) {
                hasReachedEndRef.current = true;
              }
            })
            .finally(() => {
              setTimeout(() => {
                isFetchingHistoryRef.current = false;
              }, 400);
            });
        }
      }
    });

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight || 480,
        });
      }
    };
    window.addEventListener('resize', handleResize);

    const resizeObserver = new ResizeObserver(() => {
      handleResize();
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      window.removeEventListener('resize', handleResize);
      resizeObserver.disconnect();
      if (seriesRef.current) {
        seriesRef.current = null;
      };
      chart.remove();
      chartRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reset history-pagination state on symbol change
  useEffect(() => {
    hasReachedEndRef.current = false;
  }, [params.symbol]);

  // Handle Fullscreen & Container Resizing (deferred to let layout settle)
  useEffect(() => {
    if (!containerRef.current || !chartRef.current) return;
    const timer = setTimeout(() => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight || 480,
        });
        if (prevIsFullscreenRef.current !== isFullscreen) {
          chartRef.current.timeScale().fitContent();
          prevIsFullscreenRef.current = isFullscreen;
        }
      }
    }, 50);
    return () => clearTimeout(timer);
  }, [isFullscreen]);

  return { containerRef, chartRef, seriesRef };
};
