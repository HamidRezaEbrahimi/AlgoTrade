import { create } from 'zustand';
import axios from 'axios';

export interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Opportunity {
  symbol: string;
  direction: 'LONG' | 'SHORT';
  total_score: number;
  is_ready_to_enter: boolean;
  current_price: number;
  stop_loss: number;
  take_profit: number;
  risk_reward: number;
  reason_fa: string;
}

interface MarketState {
  activeSymbol: string;
  activeTimeframe: string;
  supportedSymbols: string[];
  candles: CandleData[];
  opportunities: Opportunity[];
  currentPrice: number;
  isLoadingCandles: boolean;
  isLoadingOpportunities: boolean;

  setActiveSymbol: (symbol: string) => void;
  setActiveTimeframe: (tf: string) => void;
  setCandles: (candles: CandleData[]) => void;
  setOpportunities: (opps: Opportunity[]) => void;
  setCurrentPrice: (price: number) => void;

  fetchSymbols: () => Promise<void>;
  fetchCandles: (symbol?: string, timeframe?: string) => Promise<void>;
  fetchOpportunities: () => Promise<void>;
  fetchTicker: (symbol?: string) => Promise<void>;
  handleWsMessage: (msg: any) => void;
}

export const useMarketStore = create<MarketState>((set, get) => ({
  activeSymbol: 'BTCUSDT',
  activeTimeframe: '1h',
  supportedSymbols: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'USDTIRT'],
  candles: [],
  opportunities: [],
  currentPrice: 0,
  isLoadingCandles: false,
  isLoadingOpportunities: false,

  setActiveSymbol: (symbol: string) => {
    set({ activeSymbol: symbol });
    get().fetchCandles(symbol, get().activeTimeframe);
    get().fetchTicker(symbol);
  },

  setActiveTimeframe: (tf: string) => {
    set({ activeTimeframe: tf });
    get().fetchCandles(get().activeSymbol, tf);
  },

  setCandles: (candles) => set({ candles }),
  setOpportunities: (opportunities) => set({ opportunities }),
  setCurrentPrice: (price) => set({ currentPrice: price }),

  fetchSymbols: async () => {
    try {
      const res = await axios.get('/api/market/symbols');
      if (Array.isArray(res.data) && res.data.length > 0) {
        set({ supportedSymbols: res.data });
      }
    } catch (e) {
      console.error('Failed to fetch supported symbols', e);
    }
  },

  fetchCandles: async (symbol?: string, timeframe?: string) => {
    const sym = symbol || get().activeSymbol;
    const tf = timeframe || get().activeTimeframe;
    set({ isLoadingCandles: true });
    try {
      const res = await axios.get('/api/market/candles', {
        params: { symbol: sym, timeframe: tf, limit: 120 },
      });
      if (Array.isArray(res.data)) {
        set({ candles: res.data });
        if (res.data.length > 0) {
          const lastCandle = res.data[res.data.length - 1];
          set({ currentPrice: lastCandle.close });
        }
      }
    } catch (e) {
      console.error('Failed to fetch real market candles', e);
    } finally {
      set({ isLoadingCandles: false });
    }
  },

  fetchOpportunities: async () => {
    set({ isLoadingOpportunities: true });
    try {
      const res = await axios.get('/api/market/opportunities');
      if (Array.isArray(res.data)) {
        set({ opportunities: res.data });
      }
    } catch (e) {
      console.error('Failed to fetch real opportunities', e);
    } finally {
      set({ isLoadingOpportunities: false });
    }
  },

  fetchTicker: async (symbol?: string) => {
    const sym = symbol || get().activeSymbol;
    try {
      const res = await axios.get(`/api/market/ticker/${sym}`);
      if (res.data && res.data.price > 0) {
        set({ currentPrice: res.data.price });
      }
    } catch (e) {
      console.error('Failed to fetch ticker', e);
    }
  },

  handleWsMessage: (data: any) => {
    if (!data) return;

    // Real-time Tick update
    if (data.type === 'tick') {
      if (data.symbol === get().activeSymbol && data.price > 0) {
        set({ currentPrice: data.price });

        // Dynamically update last candle close/high/low in real-time
        const currentCandles = [...get().candles];
        if (currentCandles.length > 0) {
          const last = { ...currentCandles[currentCandles.length - 1] };
          last.close = data.price;
          if (data.price > last.high) last.high = data.price;
          if (data.price < last.low) last.low = data.price;
          currentCandles[currentCandles.length - 1] = last;
          set({ candles: currentCandles });
        }
      }
    }

    // Real-time Candle update
    else if (data.type === 'candle_update') {
      if (
        data.symbol === get().activeSymbol &&
        data.timeframe === get().activeTimeframe &&
        data.candle
      ) {
        const currentCandles = [...get().candles];
        const newCandle: CandleData = data.candle;
        if (currentCandles.length > 0) {
          const last = currentCandles[currentCandles.length - 1];
          if (last.time === newCandle.time) {
            currentCandles[currentCandles.length - 1] = newCandle;
          } else if (newCandle.time > last.time) {
            currentCandles.push(newCandle);
          }
          set({ candles: currentCandles });
        } else {
          set({ candles: [newCandle] });
        }
      }
    }

    // Real-time Opportunities update from scanner
    else if (data.type === 'opportunities_update') {
      if (Array.isArray(data.opportunities)) {
        set({ opportunities: data.opportunities });
      }
    }
  },
}));
