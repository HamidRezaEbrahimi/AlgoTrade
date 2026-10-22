import { create } from 'zustand';
import i18n from '../i18n';

interface AppState {
  currentLanguage: 'fa' | 'en';
  isKillSwitchModalOpen: boolean;
  activePage:
    | 'dashboard'
    | 'trading'
    | 'ai_copilot'
    | 'scanner'
    | 'integrations'
    | 'backtest'
    | 'orders'
    | 'strategy_builder'
    | 'ai_optimizer'
    | 'settings';
  setLanguage: (lang: 'fa' | 'en') => void;
  setActivePage: (page: AppState['activePage']) => void;
  openKillSwitchModal: () => void;
  closeKillSwitchModal: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentLanguage: 'fa',
  isKillSwitchModalOpen: false,
  activePage: 'dashboard',
  setLanguage: (lang) => {
    i18n.changeLanguage(lang);
    document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
    set({ currentLanguage: lang });
  },
  setActivePage: (page) => set({ activePage: page }),
  openKillSwitchModal: () => set({ isKillSwitchModalOpen: true }),
  closeKillSwitchModal: () => set({ isKillSwitchModalOpen: false }),
}));
