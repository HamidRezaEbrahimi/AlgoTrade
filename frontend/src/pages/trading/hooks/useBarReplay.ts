// frontend/src/pages/trading/hooks/useBarReplay.ts
// TradingView-style Bar Replay hook for step-by-step historical simulation.
// Computes dynamic zero-look-ahead pattern detection and 8-criteria scoring.

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import axios from 'axios';
import { CandleData } from '../../../stores/useMarketStore';
import { CriteriaResult, DetectorConfig } from '../types';

interface UseBarReplayProps {
  candles: CandleData[];
  symbol: string;
  timeframe: string;
  detectorConfig: DetectorConfig;
}

export interface BarReplayState {
  isReplayMode: boolean;
  isPlaying: boolean;
  replayIndex: number;
  speed: number;
  isCutting: boolean;
  visibleCandles: CandleData[];
  replayAnalysis: CriteriaResult | null;
  isAnalyzing: boolean;
  startReplay: (startIndex?: number) => void;
  exitReplay: () => void;
  togglePlay: () => void;
  stepForward: () => void;
  stepBackward: () => void;
  jumpToIndex: (index: number) => void;
  jumpToTime: (timestamp: number) => void;
  setSpeed: (speedMs: number) => void;
  setIsCutting: (cutting: boolean) => void;
}

const MIN_CANDLES_FOR_REPLAY = 30;

export const useBarReplay = ({
  candles,
  symbol,
  timeframe,
  detectorConfig,
}: UseBarReplayProps): BarReplayState => {
  const [isReplayMode, setIsReplayMode] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [replayIndex, setReplayIndex] = useState<number>(0);
  const [speed, setSpeed] = useState<number>(500); // 500ms default (1x)
  const [isCutting, setIsCutting] = useState<boolean>(false);
  const [replayAnalysis, setReplayAnalysis] = useState<CriteriaResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);

  const isPlayingRef = useRef(isPlaying);
  isPlayingRef.current = isPlaying;
  const replayIndexRef = useRef(replayIndex);
  replayIndexRef.current = replayIndex;
  const candlesRef = useRef(candles);
  candlesRef.current = candles;

  // Compute currently visible candle slice
  const visibleCandles = useMemo(() => {
    if (!isReplayMode || candles.length === 0) return candles;
    const endIdx = Math.min(Math.max(MIN_CANDLES_FOR_REPLAY, replayIndex), candles.length - 1);
    return candles.slice(0, endIdx + 1);
  }, [isReplayMode, candles, replayIndex]);

  // Request replay analysis for the current visible slice
  const fetchReplayAnalysis = useCallback(
    async (targetCandles: CandleData[]) => {
      if (targetCandles.length < MIN_CANDLES_FOR_REPLAY) return;
      setIsAnalyzing(true);
      try {
        const slice = targetCandles.slice(-300);
        const res = await axios.post('/api/market/analysis/replay', {
          symbol,
          timeframe,
          candles: slice,
          config: detectorConfig,
        });
        if (res.data && res.data.status === 'ok') {
          setReplayAnalysis(res.data);
        }
      } catch {
        // Keep previous analysis on transient network error
      } finally {
        setIsAnalyzing(false);
      }
    },
    [symbol, timeframe, detectorConfig]
  );

  // Trigger analysis when replayIndex or symbol/timeframe changes
  const prevReplayIdxRef = useRef<number>(-1);
  useEffect(() => {
    if (!isReplayMode || candles.length === 0) return;
    if (prevReplayIdxRef.current === replayIndex) return;
    prevReplayIdxRef.current = replayIndex;

    const currentSlice = candles.slice(0, replayIndex + 1);
    fetchReplayAnalysis(currentSlice);
  }, [isReplayMode, replayIndex, candles, fetchReplayAnalysis]);

  // Start Bar Replay (defaults to 30 bars before the end)
  const startReplay = useCallback(
    (startIndex?: number) => {
      if (candles.length <= MIN_CANDLES_FOR_REPLAY) return;
      const initialIdx =
        startIndex !== undefined
          ? Math.min(Math.max(MIN_CANDLES_FOR_REPLAY, startIndex), candles.length - 1)
          : Math.max(MIN_CANDLES_FOR_REPLAY, candles.length - 40);

      setReplayIndex(initialIdx);
      setIsReplayMode(true);
      setIsPlaying(false);
      setIsCutting(false);
    },
    [candles.length]
  );

  // Exit Bar Replay mode cleanly
  const exitReplay = useCallback(() => {
    setIsPlaying(false);
    setIsReplayMode(false);
    setIsCutting(false);
    setReplayAnalysis(null);
  }, []);

  // Step Forward (+1 bar)
  const stepForward = useCallback(() => {
    if (!isReplayMode) return;
    setReplayIndex((prev) => {
      const next = prev + 1;
      if (next >= candlesRef.current.length - 1) {
        setIsPlaying(false);
        return candlesRef.current.length - 1;
      }
      return next;
    });
  }, [isReplayMode]);

  // Step Backward (-1 bar)
  const stepBackward = useCallback(() => {
    if (!isReplayMode) return;
    setReplayIndex((prev) => Math.max(MIN_CANDLES_FOR_REPLAY, prev - 1));
  }, [isReplayMode]);

  // Toggle Play / Pause
  const togglePlay = useCallback(() => {
    if (!isReplayMode) {
      startReplay();
      setIsPlaying(true);
      return;
    }
    if (replayIndexRef.current >= candlesRef.current.length - 1) {
      // Loop back if at the end
      setReplayIndex(Math.max(MIN_CANDLES_FOR_REPLAY, candlesRef.current.length - 50));
    }
    setIsPlaying((prev) => !prev);
  }, [isReplayMode, startReplay]);

  // Jump to specific candle index
  const jumpToIndex = useCallback(
    (index: number) => {
      const clamped = Math.min(Math.max(MIN_CANDLES_FOR_REPLAY, index), candlesRef.current.length - 1);
      setReplayIndex(clamped);
      setIsCutting(false);
    },
    []
  );

  // Jump to specific timestamp
  const jumpToTime = useCallback(
    (timestamp: number) => {
      const all = candlesRef.current;
      if (all.length === 0) return;
      let closestIdx = 0;
      let minDiff = Infinity;
      for (let i = 0; i < all.length; i++) {
        const diff = Math.abs(all[i].time - timestamp);
        if (diff < minDiff) {
          minDiff = diff;
          closestIdx = i;
        }
      }
      jumpToIndex(closestIdx);
    },
    [jumpToIndex]
  );

  // Playing loop (Interval timer)
  useEffect(() => {
    if (!isReplayMode || !isPlaying) return;

    const interval = setInterval(() => {
      setReplayIndex((prev) => {
        const next = prev + 1;
        if (next >= candlesRef.current.length - 1) {
          setIsPlaying(false);
          return candlesRef.current.length - 1;
        }
        return next;
      });
    }, speed);

    return () => clearInterval(interval);
  }, [isReplayMode, isPlaying, speed]);

  return {
    isReplayMode,
    isPlaying,
    replayIndex,
    speed,
    isCutting,
    visibleCandles,
    replayAnalysis,
    isAnalyzing,
    startReplay,
    exitReplay,
    togglePlay,
    stepForward,
    stepBackward,
    jumpToIndex,
    jumpToTime,
    setSpeed,
    setIsCutting,
  };
};
