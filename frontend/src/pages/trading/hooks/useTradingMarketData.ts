import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useMarketStore } from '../../../stores/useMarketStore';
import { SymbolMeta, CriteriaResult, DetectorConfig } from '../types';

interface UseTradingMarketDataProps {
  selectedExchange: 'wallex' | 'nobitex' | 'faraz';
  detectorConfig: DetectorConfig;
}

export const useTradingMarketData = ({
  selectedExchange,
  detectorConfig,
}: UseTradingMarketDataProps) => {
  const {
    activeSymbol,
    setActiveSymbol,
    activeTimeframe,
    setCandles,
  } = useMarketStore();

  const [symbolsList, setSymbolsList] = useState<SymbolMeta[]>([]);
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);
  const [focusTimestamp, setFocusTimestamp] = useState<number | null>(null);

  const [analysis, setAnalysis] = useState<CriteriaResult>({
    passed: false,
    score: 0,
    max_score: 8,
    rsi: 50.0,
    atr: 0.0,
    criteria: {
      structure_4h: false,
      location_valid: false,
      pattern_1h: false,
      momentum_15m: false,
      rsi_confirmed: false,
      volume_confirmed: false,
      rr_valid: false,
      stop_loss_valid: false,
    },
    detected_patterns: [],
  });

  // 1. Fetch live symbols whenever exchange changes
  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        const res = await axios.get('/api/market/symbols', {
          params: { exchange: selectedExchange },
        });
        if (res.data && res.data.length > 0) {
          setSymbolsList(res.data);
          const exists = res.data.some(
            (s: SymbolMeta) => s.symbol.toUpperCase() === activeSymbol.toUpperCase()
          );
          if (!exists) {
            setActiveSymbol(res.data[0].symbol);
          }
        }
      } catch {
        // Fallback
      }
    };
    fetchSymbols();
  }, [selectedExchange]);

  const currentKey = `${activeSymbol}_${activeTimeframe}_${selectedExchange}`;
  const prevKeyRef = useRef(currentKey);

  // 2. Fetch live candles & analysis whenever symbol, timeframe, or exchange changes
  useEffect(() => {
    const isKeyChanged = prevKeyRef.current !== currentKey;
    if (isKeyChanged) {
      prevKeyRef.current = currentKey;
    }

    const fetchMarketData = async () => {
      try {
        const candleRes = await axios.get('/api/market/candles', {
          params: {
            symbol: activeSymbol,
            timeframe: activeTimeframe,
            exchange: selectedExchange,
            limit: 1500,
          },
        });
        if (candleRes.data && candleRes.data.length > 0) {
          const incoming = candleRes.data;
          const currentStoreCandles = useMarketStore.getState().candles;

          if (isKeyChanged || currentStoreCandles.length === 0) {
            setCandles(incoming);
          } else {
            const map = new Map<number, any>();
            for (const c of currentStoreCandles) {
              map.set(c.time, c);
            }
            for (const c of incoming) {
              map.set(c.time, c);
            }
            const merged = Array.from(map.values()).sort((a, b) => a.time - b.time);
            setCandles(merged);
          }
          const latestClose = incoming[incoming.length - 1].close;
          setCurrentPrice(latestClose);
        }

        const analysisRes = await axios.get(`/api/market/analysis/${activeSymbol}`, {
          params: {
            timeframe: activeTimeframe,
            exchange: selectedExchange,
            min_impulse_atr: detectorConfig.min_impulse_atr,
            flag_max_retrace: detectorConfig.flag_max_retrace,
            flat_max_retrace: detectorConfig.flat_max_retrace,
            wave_b_min_retrace: detectorConfig.wave_b_min_retrace,
            min_risk_reward: detectorConfig.min_risk_reward,
          },
        });
        if (analysisRes.data) {
          setAnalysis(analysisRes.data);
          if (analysisRes.data.current_price > 0 && currentPrice === 0) {
            setCurrentPrice(analysisRes.data.current_price);
          }
          const wavePats = (analysisRes.data.detected_patterns || []).filter(
            (p: any) => p.category === 'flat' || p.category === 'flag' || p.category === 'wedge'
          );
          if (wavePats.length > 0) {
            setFocusTimestamp((prev) => (prev !== null ? prev : wavePats[wavePats.length - 1].time));
          }
        }
      } catch {
        // Fallback
      }
    };

    fetchMarketData();
    const interval = setInterval(fetchMarketData, 10000);
    return () => clearInterval(interval);
  }, [activeSymbol, activeTimeframe, selectedExchange, detectorConfig]);

  // 3. WebSocket Streaming
  useEffect(() => {
    let ws: WebSocket | null = null;
    let pingTimer: any = null;
    let reconnectTimer: any = null;
    let isMounted = true;

    const connectWs = () => {
      if (!isMounted) return;
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname || '127.0.0.1';
        ws = new WebSocket(`${protocol}//${host}:8000/ws`);

        ws.onopen = () => {
          if (!isMounted) {
            ws?.close();
            return;
          }
          setIsWsConnected(true);
          pingTimer = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send('ping');
            }
          }, 15000);
        };

        ws.onmessage = (event) => {
          if (event.data === 'pong') return;
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'tick' && data.price > 0) {
              const currentActive = useMarketStore.getState().activeSymbol;
              if (data.symbol?.toUpperCase() === currentActive.toUpperCase()) {
                setCurrentPrice(data.price);
                const currentCandles = useMarketStore.getState().candles;
                if (currentCandles && currentCandles.length > 0) {
                  const updated = [...currentCandles];
                  const last = { ...updated[updated.length - 1] };
                  last.close = data.price;
                  if (data.price > last.high) last.high = data.price;
                  if (data.price < last.low) last.low = data.price;
                  updated[updated.length - 1] = last;
                  useMarketStore.getState().setCandles(updated);
                }
              }
            }
          } catch {
            // Non-JSON message
          }
        };

        ws.onclose = () => {
          setIsWsConnected(false);
          clearInterval(pingTimer);
          if (isMounted) {
            reconnectTimer = setTimeout(connectWs, 3000);
          }
        };

        ws.onerror = () => {
          setIsWsConnected(false);
        };
      } catch {
        setIsWsConnected(false);
      }
    };

    connectWs();
    return () => {
      isMounted = false;
      clearInterval(pingTimer);
      clearTimeout(reconnectTimer);
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
    };
  }, []);

  // 4. On-Scroll History Loader
  const handleLoadMoreHistory = async (earliestTime: number): Promise<boolean> => {
    try {
      setIsLoadingMore(true);
      const res = await axios.get('/api/market/candles', {
        params: {
          symbol: activeSymbol,
          timeframe: activeTimeframe,
          exchange: selectedExchange,
          limit: 1500,
          to_ts: earliestTime - 1,
        },
      });
      if (res.data && Array.isArray(res.data) && res.data.length > 0) {
        const currentStoreCandles = useMarketStore.getState().candles;
        const map = new Map<number, any>();
        for (const c of res.data) {
          map.set(c.time, c);
        }
        for (const c of currentStoreCandles) {
          map.set(c.time, c);
        }
        const merged = Array.from(map.values()).sort((a, b) => a.time - b.time);
        setCandles(merged);
        return true;
      }
      return false;
    } catch {
      return false;
    } finally {
      setIsLoadingMore(false);
    }
  };

  return {
    symbolsList,
    currentPrice,
    setCurrentPrice,
    isWsConnected,
    isLoadingMore,
    analysis,
    focusTimestamp,
    setFocusTimestamp,
    handleLoadMoreHistory,
  };
};
