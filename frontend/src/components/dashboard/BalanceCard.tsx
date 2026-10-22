import React from 'react';
import { useTranslation } from 'react-i18next';
import { Wallet, TrendingUp, ShieldAlert, Award } from 'lucide-react';
import { useOrderStore } from '../../stores/useOrderStore';

export const BalanceCard: React.FC = () => {
  const { t } = useTranslation('Dashboard');
  const { balance, availableBalance, dailyPnL, winRate, profitFactor, currentDrawdown } = useOrderStore();

  return (
    <div className="dashboard-grid">
      {/* Total Balance */}
      <div className="glass-panel p-5">
        <div className="flex justify-between items-start text-slate-400 mb-2">
          <span className="text-xs font-semibold">{t('total_balance')}</span>
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
            <Wallet size={18} />
          </div>
        </div>
        <div className="text-2xl font-bold font-mono text-white numeric-ltr">
          ${balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </div>
        <div className="text-xs text-slate-400 mt-2 flex justify-between">
          <span>{t('available_balance')}:</span>
          <span className="font-mono numeric-ltr">${availableBalance.toLocaleString()}</span>
        </div>
      </div>

      {/* Today PnL */}
      <div className="glass-panel p-5">
        <div className="flex justify-between items-start text-slate-400 mb-2">
          <span className="text-xs font-semibold">{t('pnl_today')}</span>
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <TrendingUp size={18} />
          </div>
        </div>
        <div className="text-2xl font-bold font-mono text-emerald-400 numeric-ltr">
          +${dailyPnL.toFixed(2)}
        </div>
        <div className="text-xs text-emerald-400/80 mt-2 flex justify-between">
          <span>{t('pnl_percent')}:</span>
          <span className="font-mono numeric-ltr">+2.75%</span>
        </div>
      </div>

      {/* Win Rate & Profit Factor */}
      <div className="glass-panel p-5">
        <div className="flex justify-between items-start text-slate-400 mb-2">
          <span className="text-xs font-semibold">{t('win_rate')}</span>
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
            <Award size={18} />
          </div>
        </div>
        <div className="text-2xl font-bold font-mono text-white numeric-ltr">
          {winRate}%
        </div>
        <div className="text-xs text-slate-400 mt-2 flex justify-between">
          <span>{t('profit_factor')}:</span>
          <span className="font-mono numeric-ltr text-cyan-400">{profitFactor}</span>
        </div>
      </div>

      {/* Circuit Breaker & Drawdown */}
      <div className="glass-panel p-5 border-yellow-500/20">
        <div className="flex justify-between items-start text-slate-400 mb-2">
          <span className="text-xs font-semibold">{t('circuit_breaker')}</span>
          <div className="p-2 rounded-lg bg-yellow-500/10 text-yellow-400">
            <ShieldAlert size={18} />
          </div>
        </div>
        <div className="text-base font-bold text-emerald-400 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>{t('normal')}</span>
        </div>
        <div className="text-xs text-slate-400 mt-3 flex justify-between">
          <span>{t('current_drawdown')}:</span>
          <span className="font-mono numeric-ltr text-slate-200">{currentDrawdown}% (سقف: ۱۲٪)</span>
        </div>
      </div>
    </div>
  );
};
