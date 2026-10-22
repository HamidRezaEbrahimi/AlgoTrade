import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard,
  CandlestickChart,
  Bot,
  Radar,
  ListOrdered,
  FlaskConical,
  Sparkles,
  BrainCircuit,
  Sliders,
} from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';

export const Sidebar: React.FC = () => {
  const { t } = useTranslation('Common');
  const { activePage, setActivePage } = useAppStore();

  const navItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: t('nav.dashboard') },
    { id: 'trading', icon: CandlestickChart, label: t('nav.trading') },
    { id: 'ai_copilot', icon: Bot, label: t('nav.ai_copilot') },
    { id: 'scanner', icon: Radar, label: t('nav.scanner') },
    { id: 'orders', icon: ListOrdered, label: t('nav.orders') },
    { id: 'strategy_builder', icon: Sparkles, label: t('nav.strategy_builder') },
    { id: 'ai_optimizer', icon: BrainCircuit, label: t('nav.ai_optimizer') },
    { id: 'backtest', icon: FlaskConical, label: t('nav.backtest') },
    { id: 'settings', icon: Sliders, label: t('nav.settings') },
  ];

  return (
    <aside className="w-64 border-r border-white/10 glass-panel rounded-none min-h-[calc(100vh-4rem)] p-4 flex flex-col justify-between hidden md:flex">
      <nav className="space-y-1.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setActivePage(item.id as any)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-sm shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              <Icon size={18} className={isActive ? 'text-cyan-400' : 'text-slate-400'} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-3 bg-white/[0.02] border border-white/5 rounded-lg text-xs text-slate-400 space-y-1">
        <div className="flex justify-between">
          <span>{t('status.engine_running')}</span>
          <span className="text-emerald-400 font-medium">✓</span>
        </div>
        <div className="flex justify-between">
          <span>{t('status.check_interval')}</span>
          <span className="font-mono text-cyan-400">15m</span>
        </div>
      </div>
    </aside>
  );
};
