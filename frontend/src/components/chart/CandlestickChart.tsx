// frontend/src/components/chart/CandlestickChart.tsx
// Thin orchestrator: composes the chart hooks (instance, candle data,
// wave overlay, pattern markers, price lines) and renders the HUD/legend.
// All heavy chart logic lives in the dedicated hook modules.

import React, { useEffect, useRef, useState } from 'react';
import { CandleData } from '../../stores/useMarketStore';
import { ChartLayerVisibility, PatternMarker } from '../../pages/trading/types';
import { formatPrice, normalizeTimestamp, getCategoryColor } from './chartUtils';
import { HoveredCandleInfo } from './chartUtils';
import { useChartInstance } from './useChartInstance';
import { useCandleData } from './useCandleData';
import { useWaveOverlay, resolveActivePattern } from './useWaveOverlay';
import { usePatternMarkers } from './usePatternMarkers';
import { usePriceLines } from './usePriceLines';

interface CandlestickChartProps {
  candles: CandleData[];
  symbol: string;
  timeframe?: string;
  showOrderLines?: boolean;
  layers: ChartLayerVisibility;
  patterns?: PatternMarker[];
  levels?: {
    order_block_demand?: number;
    order_block_supply?: number;
    fvg_imbalance?: number;
    support_level?: number;
    resistance_level?: number;
  };
  tradeSetup?: {
    entry_price?: number;
    stop_loss?: number;
    take_profit_1?: number;
    take_profit_2?: number;
  };
  entryPrice?: number;
  stopLoss?: number;
  takeProfit1?: number;
  takeProfit2?: number;
  focusTimestamp?: number | null;
  selectedPatternId?: string | null;
  selectedPattern?: PatternMarker | null;
  onSelectPattern?: (pattern: PatternMarker | null) => void;
  isFullscreen?: boolean;
  onLoadMoreHistory?: (earliestTimestamp: number) => Promise<boolean | void>;
  onChartClick?: (timestamp: number) => void;
}

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  candles,
  symbol,
  timeframe,
  entryPrice,
  stopLoss,
  takeProfit1,
  takeProfit2,
  showOrderLines = true,
  isFullscreen = false,
  patterns = [],
  layers = { tradeSetup: true, regularFlat: true, expandedFlat: true, runningFlat: true, contractFlat: true, complexFlat: true, flags: true, smcLevels: true, srLevels: true, filterChochBos: false, filterVolume: false, filterRsi: false, filterTrend: false },
  levels,
  tradeSetup,
  focusTimestamp,
  selectedPatternId,
  selectedPattern,
  onSelectPattern,
  onLoadMoreHistory,
  onChartClick,
}) => {
  const [hoveredInfo, setHoveredInfo] = useState<HoveredCandleInfo | null>(null);
  const [localSelectedId, setLocalSelectedId] = useState<string | null>(null);
  const [isAutoScroll, setIsAutoScroll] = useState<boolean>(false);

  // Ref-stable accessors for the once-mounted chart subscriptions
  const candlesRef = useRef(candles);
  candlesRef.current = candles;
  const patternsRef = useRef(patterns);
  patternsRef.current = patterns;

  const handlePatternClick = (pattern: PatternMarker | null) => {
    if (!pattern) {
      setLocalSelectedId(null);
      onSelectPattern?.(null);
      return;
    }
    setLocalSelectedId((prev) => (prev === pattern.id ? null : pattern.id));
    onSelectPattern?.(pattern);
  };

  const { containerRef, chartRef, seriesRef } = useChartInstance({
    symbol,
    isFullscreen,
    getCandles: () => candlesRef.current,
    getPatterns: () => patternsRef.current,
    onPatternClick: handlePatternClick,
    onHover: setHoveredInfo,
    onLoadMoreHistory,
    onChartClick,
  });

  useCandleData({ candles, symbol, timeframe, isFullscreen, chartRef, seriesRef });

  const activePattern = resolveActivePattern(
    patterns, selectedPatternId, selectedPattern, localSelectedId,
  );

  useWaveOverlay({
    candles, patterns, selectedPatternId, selectedPattern, localSelectedId,
    layers, chartRef,
  });

  usePatternMarkers({
    candles, patterns, selectedPatternId, selectedPattern, localSelectedId,
    focusTimestamp, layers, seriesRef,
  });

  usePriceLines({
    candles, showOrderLines, entryPrice, stopLoss, takeProfit1, takeProfit2,
    tradeSetup, activePattern, levels, layers, seriesRef,
  });

  // Reset local selection on symbol change
  useEffect(() => {
    setLocalSelectedId(null);
  }, [symbol]);

  // Scroll the viewport ONLY when focusTimestamp actually changes (user clicked pattern)
  const prevFocusRef = useRef<number | null | undefined>(undefined);
  useEffect(() => {
    if (!focusTimestamp || !chartRef.current || candles.length === 0) return;
    if (prevFocusRef.current === focusTimestamp) return;
    prevFocusRef.current = focusTimestamp;

    const target = normalizeTimestamp(focusTimestamp);
    if (!target) return;
    const chart = chartRef.current;
    const raf = requestAnimationFrame(() => {
      const times = candlesRef.current.map((c) => c.time);
      let idx = times.findIndex((t) => t >= target);
      if (idx < 0) idx = times.length - 1;
      chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, idx - 40), to: idx + 40 });
    });
    return () => cancelAnimationFrame(raf);
  }, [focusTimestamp, chartRef]);

  return (
    <div className="relative w-full h-full min-h-[460px] rounded-lg overflow-hidden bg-[#090d16] group">
      {/* On-Chart Active Pattern HUD Header Badge */}
      {activePattern && (
        <div className="absolute top-3 left-3 z-20 flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-slate-950/85 backdrop-blur-md border border-white/10 shadow-2xl animate-fade-in pointer-events-none">
          <div
            className="w-2.5 h-2.5 rounded-full animate-pulse"
            style={{ backgroundColor: getCategoryColor(activePattern) }}
          />
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white font-sans">
                {activePattern.name || activePattern.text}
              </span>
              <span
                className="text-[10px] px-1.5 py-0.5 rounded font-mono font-bold"
                style={{
                  backgroundColor: `${getCategoryColor(activePattern)}20`,
                  color: getCategoryColor(activePattern),
                  border: `1px solid ${getCategoryColor(activePattern)}40`,
                }}
              >
                {activePattern.direction === 'bullish' ? 'صعودی ↗' : 'نزولی ↘'}
              </span>
              {(activePattern as any).is_developing ? (
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-sans">
                  محدوده شکار ورود (PRZ) موج C 🎯
                </span>
              ) : activePattern.points && activePattern.points.length >= 5 ? (
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-sans">
                  ساختار ۵ نقطه‌ای رانینگ فلت (0-1-A-B-C) ⚡
                </span>
              ) : null}
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              {(activePattern as any).is_developing
                ? `قیمت کنونی: ${formatPrice(activePattern.price)} | محدوده شکار PRZ`
                : activePattern.points && activePattern.points.length >= 5
                ? `ورود [نقطه C]: ${formatPrice(activePattern.price)} | تارگت [موج B]: ${formatPrice(activePattern.trade_setup?.take_profit_1)}`
                : `قیمت: ${formatPrice(activePattern.price)}`}
            </span>
          </div>
        </div>
      )}

      {/* Shamsi + Gregorian Dual Date & OHLC Legend Overlay */}
      {hoveredInfo && (
        <div className="absolute top-3 right-3 z-20 pointer-events-none flex items-center gap-3 px-3 py-1.5 rounded-xl bg-slate-950/85 backdrop-blur-md border border-white/10 text-xs font-mono shadow-xl animate-fade-in">
          <span className="text-cyan-400 font-bold">{hoveredInfo.timeStr}</span>
          <div className="flex items-center gap-2 text-slate-300">
            <span>O: <b className="text-white">{formatPrice(hoveredInfo.open)}</b></span>
            <span>H: <b className="text-emerald-400">{formatPrice(hoveredInfo.high)}</b></span>
            <span>L: <b className="text-rose-400">{formatPrice(hoveredInfo.low)}</b></span>
            <span>C: <b className={hoveredInfo.isUp ? 'text-emerald-400' : 'text-rose-400'}>{formatPrice(hoveredInfo.close)}</b></span>
          </div>
        </div>
      )}

      {/* Floating Chart Navigation & Auto-Scroll Lock Controls */}
      <div className="absolute bottom-4 left-4 z-20 flex items-center gap-1.5 px-2 py-1 rounded-xl bg-slate-950/90 backdrop-blur-md border border-white/10 shadow-2xl opacity-80 hover:opacity-100 transition-opacity">
        <button
          type="button"
          onClick={() => {
            setIsAutoScroll(!isAutoScroll);
            if (!isAutoScroll) {
              chartRef.current?.timeScale().scrollToRealTime();
            }
          }}
          className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg transition-all ${isAutoScroll
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-[0_0_10px_rgba(6,182,212,0.2)]'
              : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
            }`}
          title={isAutoScroll ? 'اسکرول خودکار فعال است (همیشه به آخرین کندل می‌چسبد)' : 'اسکرول خودکار خاموش است (می‌توانید آزادانه در تاریخچه چارت حرکت کنید)'}
        >
          <span>{isAutoScroll ? '🔒 قفل به کندل زنده' : '🔓 اسکرول آزاد'}</span>
        </button>

        <button
          type="button"
          onClick={() => chartRef.current?.timeScale().scrollToRealTime()}
          className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-cyan-300 hover:bg-white/10 rounded-lg transition-all"
          title="پرش فوری به آخرین کندل"
        >
          <span>⏭️ انتها</span>
        </button>

        <button
          type="button"
          onClick={() => chartRef.current?.timeScale().fitContent()}
          className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-amber-300 hover:bg-white/10 rounded-lg transition-all"
          title="تنظیم خودکار تمام کندل‌ها در صفحه"
        >
          <span>🔄 تناسب</span>
        </button>
      </div>

      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
};
