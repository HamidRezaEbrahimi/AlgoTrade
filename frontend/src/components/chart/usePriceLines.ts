// frontend/src/components/chart/usePriceLines.ts
// Manages trade-setup price lines (Entry/SL/TP1/TP2), Smart Money levels
// (Order Block, FVG) and Support/Resistance lines. Lines are validated
// against the visible candle price range so stale/unrelated levels never
// distort the Y-axis.

import { useEffect, useRef, MutableRefObject } from 'react';
import { IPriceLine, ISeriesApi } from 'lightweight-charts';
import { CandleData } from '../../stores/useMarketStore';
import { ChartSmaLevels, formatPrice } from './chartUtils';

interface UsePriceLinesParams {
  candles: CandleData[];
  showOrderLines: boolean;
  entryPrice?: number;
  stopLoss?: number;
  takeProfit1?: number;
  takeProfit2?: number;
  tradeSetup?: {
    entry_price?: number;
    stop_loss?: number;
    take_profit_1?: number;
    take_profit_2?: number;
    signal?: string;
  };
  activePattern?: any;
  levels?: ChartSmaLevels;
  layers: {
    tradeSetup?: boolean;
    runningFlat?: boolean;
    smcLevels?: boolean;
    srLevels?: boolean;
  };
  seriesRef: React.MutableRefObject<ISeriesApi<'Candlestick'> | null>;
}

export const usePriceLines = (
  params: UsePriceLinesParams,
): MutableRefObject<IPriceLine[]> => {
  const {
    candles, showOrderLines, entryPrice, stopLoss, takeProfit1, takeProfit2,
    tradeSetup, activePattern, layers, seriesRef,
  } = params;

  const priceLinesRef = useRef<IPriceLine[]>([]);

  useEffect(() => {
    if (!seriesRef.current) return;
    const series = seriesRef.current;

    // Clean previous price lines
    priceLinesRef.current.forEach((line) => {
      try {
        series.removePriceLine(line);
      } catch {
        // ignore
      }
    });
    priceLinesRef.current = [];

    if (!showOrderLines || candles.length === 0) return;

    const minLow = Math.min(...candles.map((c: CandleData) => c.low));
    const maxHigh = Math.max(...candles.map((c: CandleData) => c.high));
    const span = Math.max(maxHigh - minLow, maxHigh * 0.01);

    // Filter out obsolete/unrelated price levels that would distort the Y-axis
    const isLineValid = (p?: number) => {
      if (!p || p <= 0) return false;
      const lowerLimit = minLow - Math.max(span * 1.5, minLow * 0.1);
      const upperLimit = maxHigh + Math.max(span * 1.5, maxHigh * 0.1);
      return p >= lowerLimit && p <= upperLimit;
    };

    const effEntry = entryPrice || tradeSetup?.entry_price;
    const effSL = stopLoss || tradeSetup?.stop_loss;
    const effTP1 = takeProfit1 || tradeSetup?.take_profit_1;
    const effTP2 = takeProfit2 || tradeSetup?.take_profit_2;

    const addLine = (
      price: number, color: string, lineStyle: number, title: string,
    ) => {
      priceLinesRef.current.push(
        series.createPriceLine({ price, color, lineWidth: 1, lineStyle, title }),
      );
    };

    // 1. Trade Setup Lines from AlefTrade (Only when an active BUY or SELL signal is confirmed)
    const sig = tradeSetup?.signal;
    const hasActiveSignal = sig === 'BUY' || sig === 'SELL';
    if (layers.tradeSetup && hasActiveSignal) {
      const isBuy = sig === 'BUY';
      if (isLineValid(effEntry)) addLine(effEntry!, '#eab308', 1, `ورود (${isBuy ? 'خرید' : 'فروش'}): ${formatPrice(effEntry)}`);
      if (isLineValid(effSL)) addLine(effSL!, '#ef4444', 2, `حد ضرر (SL): ${formatPrice(effSL)}`);
      if (isLineValid(effTP1)) addLine(effTP1!, '#10b981', 2, `تارگت ۱ (TP1): ${formatPrice(effTP1)}`);
      if (isLineValid(effTP2)) addLine(effTP2!, '#06b6d4', 2, `تارگت ۲ (TP2): ${formatPrice(effTP2)}`);
    }

    // 2. PRZ Zone Boundary Lines from AlefTrade
    // 2. PRZ Zone Boundary Lines from AlefTrade
    if (layers.runningFlat !== false && activePattern?.prz_zone) {
      const prz = activePattern.prz_zone;
      if (isLineValid(prz.top)) addLine(prz.top, '#f59e0b', 2, `سقف PRZ (${prz.label || '0.60-1.05'}): ${formatPrice(prz.top)}`);
      if (isLineValid(prz.bottom)) addLine(prz.bottom, '#f59e0b', 2, `کف PRZ: ${formatPrice(prz.bottom)}`);
    }
  }, [
    candles, showOrderLines, layers, entryPrice, stopLoss, takeProfit1,
    takeProfit2, tradeSetup, activePattern, seriesRef,
  ]);

  return priceLinesRef;
};
