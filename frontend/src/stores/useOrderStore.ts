import { create } from 'zustand';
import axios from 'axios';

export interface PositionItem {
  id: string;
  symbol: string;
  exchange: string;
  direction: 'LONG' | 'SHORT';
  entry_price: number;
  entry_time: string;
  initial_size: number;
  remaining_size: number;
  current_stop: number;
  trailing_active: boolean;
  realized_pnl: number;
  unrealized_pnl: number;
}

export interface TradeHistoryItem {
  id: string;
  symbol: string;
  exchange: string;
  direction: 'LONG' | 'SHORT';
  entry_price: number;
  exit_price: number;
  pnl: number;
  pnl_percent: number;
  risk_reward_actual: number;
  entry_reason: string;
  exit_reason: string;
  time: string;
}

interface OrderState {
  balance: number;
  availableBalance: number;
  tmnBalance: number;
  dailyPnL: number;
  winRate: number;
  profitFactor: number;
  maxDrawdown: number;
  currentDrawdown: number;
  positions: PositionItem[];
  tradeHistory: TradeHistoryItem[];
  isLoadingBalance: boolean;
  isLoadingPositions: boolean;
  isLoadingHistory: boolean;

  setPositions: (positions: PositionItem[]) => void;
  setTradeHistory: (history: TradeHistoryItem[]) => void;

  fetchBalance: () => Promise<void>;
  fetchPositions: () => Promise<void>;
  fetchTradeHistory: () => Promise<void>;
  handleWsMessage: (msg: any) => void;
}

export const useOrderStore = create<OrderState>((set) => ({
  balance: 0,
  availableBalance: 0,
  tmnBalance: 0,
  dailyPnL: 0,
  winRate: 0,
  profitFactor: 0,
  maxDrawdown: 0,
  currentDrawdown: 0,
  positions: [],
  tradeHistory: [],
  isLoadingBalance: false,
  isLoadingPositions: false,
  isLoadingHistory: false,

  setPositions: (positions) => set({ positions }),
  setTradeHistory: (tradeHistory) => set({ tradeHistory }),

  fetchBalance: async () => {
    set({ isLoadingBalance: true });
    try {
      const res = await axios.get('/api/orders/balance');
      if (res.data) {
        set({
          balance: res.data.total_balance_usdt || 0,
          availableBalance: res.data.available_balance_usdt || 0,
          tmnBalance: res.data.tmn_balance || 0,
          dailyPnL: res.data.daily_pnl || 0,
          winRate: res.data.win_rate || 0,
          profitFactor: res.data.profit_factor || 0,
          currentDrawdown: res.data.current_drawdown || 0,
        });
      }
    } catch (e) {
      console.error('Failed to fetch real balance', e);
    } finally {
      set({ isLoadingBalance: false });
    }
  },

  fetchPositions: async () => {
    set({ isLoadingPositions: true });
    try {
      const res = await axios.get('/api/orders/positions');
      if (Array.isArray(res.data)) {
        set({ positions: res.data });
      }
    } catch (e) {
      console.error('Failed to fetch active positions', e);
    } finally {
      set({ isLoadingPositions: false });
    }
  },

  fetchTradeHistory: async () => {
    set({ isLoadingHistory: true });
    try {
      const res = await axios.get('/api/orders/history');
      if (Array.isArray(res.data)) {
        set({ tradeHistory: res.data });
      }
    } catch (e) {
      console.error('Failed to fetch trade history', e);
    } finally {
      set({ isLoadingHistory: false });
    }
  },

  handleWsMessage: (data: any) => {
    if (!data) return;
    if (data.type === 'position_update' && Array.isArray(data.positions)) {
      set({ positions: data.positions });
    } else if (data.type === 'balance_update') {
      set({
        balance: data.total_balance_usdt || 0,
        availableBalance: data.available_balance_usdt || 0,
      });
    }
  },
}));
